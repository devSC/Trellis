#!/usr/bin/env python3
"""Idempotently add Guru supervision defaults to .trellis/config.yaml."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


VALID_PLATFORMS = {"flutter", "go", "ios", "h5"}
HIGH_RISK_REVIEW_PROVIDER_POLICY_PATH = (
    "guru",
    "supervision",
    "high_risk_review_provider_policy",
)
DEFAULTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("codex", "dispatch_mode"), "sub-agent"),
    (("channel", "worker_guard", "idle_timeout"), "10m"),
    (("channel", "worker_guard", "max_live_workers"), "4"),
    (("guru", "supervision", "provider"), "codex"),
    (("guru", "supervision", "implement_timeout"), "45m"),
    (("guru", "supervision", "check_timeout"), "30m"),
    (("guru", "supervision", "warn_before"), "5m"),
    (("guru", "supervision", "adversarial_enabled"), "true"),
    (("guru", "supervision", "adversarial_claude_model"), "claude-sonnet-4-6"),
    (("guru", "supervision", "adversarial_codex_model"), "gpt-5.4"),
    (("guru", "supervision", "adversarial_codex_reasoning_effort"), "high"),
    (("guru", "supervision", "high_risk_review_provider_policy"), "current"),
)
LEGACY_DEFAULTS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ("guru", "supervision", "adversarial_claude_model"),
        ("claude-sonnet-4.8", "claude-sonnet-4.6"),
    ),
)
BOOLEAN_TRUE = {"1", "true", "yes", "on"}
BOOLEAN_FALSE = {"0", "false", "no", "off"}

KEY_RE = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z0-9_-]+)\s*:\s*(?P<value>.*)$")


class ConfigPatchError(RuntimeError):
    """Raised when config.yaml has a shape this patcher cannot merge safely."""


@dataclass(frozen=True)
class ParsedKey:
    index: int
    indent: int
    key: str
    raw_value: str


@dataclass(frozen=True)
class PatchResult:
    changed: bool
    actions: list[str]
    warnings: list[str]


def _parse_key_line(index: int, line: str) -> ParsedKey | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = KEY_RE.match(line)
    if match is None:
        return None
    return ParsedKey(
        index=index,
        indent=len(match.group("indent")),
        key=match.group("key"),
        raw_value=match.group("value"),
    )


def _has_scalar_value(raw_value: str) -> bool:
    value = raw_value.strip()
    return bool(value) and not value.startswith("#")


def _scalar_value(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("#"):
        return ""
    for marker in (" #", "\t#"):
        idx = value.find(marker)
        if idx >= 0:
            value = value[:idx].rstrip()
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        value = value[1:-1]
    return value


def _legacy_default_values(path: tuple[str, ...]) -> tuple[str, ...]:
    for legacy_path, values in LEGACY_DEFAULTS:
        if legacy_path == path:
            return values
    return ()


def _config_bool_string(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in BOOLEAN_TRUE:
        return "true"
    if normalized in BOOLEAN_FALSE:
        return "false"
    raise ConfigPatchError("adversarial-enabled must be true or false")


def _find_key(lines: Sequence[str], path: tuple[str, ...]) -> ParsedKey | None:
    stack: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        parsed = _parse_key_line(index, line)
        if parsed is None:
            continue
        while stack and parsed.indent <= stack[-1][0]:
            stack.pop()
        current_path = tuple(key for _, key in stack) + (parsed.key,)
        if current_path == path:
            return parsed
        if not _has_scalar_value(parsed.raw_value):
            stack.append((parsed.indent, parsed.key))
    return None


def _section_end(lines: Sequence[str], section: ParsedKey) -> int:
    for index in range(section.index + 1, len(lines)):
        parsed = _parse_key_line(index, lines[index])
        if parsed is not None and parsed.indent <= section.indent:
            return index
    return len(lines)


def _append_top_level(lines: list[str], line: str) -> None:
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(line)


def _ensure_mapping(
    lines: list[str],
    path: tuple[str, ...],
    actions: list[str],
) -> ParsedKey:
    existing = _find_key(lines, path)
    if existing is not None:
        if _has_scalar_value(existing.raw_value):
            dotted = ".".join(path)
            raise ConfigPatchError(
                f"{dotted} is a scalar; cannot merge child defaults safely"
            )
        return existing

    key = path[-1]
    if len(path) == 1:
        _append_top_level(lines, f"{key}:")
        actions.append(f"created {'.'.join(path)}")
        created = _find_key(lines, path)
        if created is None:
            raise ConfigPatchError(f"failed to create {'.'.join(path)}")
        return created

    parent = _ensure_mapping(lines, path[:-1], actions)
    indent = parent.indent + 2
    insert_at = _section_end(lines, parent)
    lines.insert(insert_at, f"{' ' * indent}{key}:")
    actions.append(f"created {'.'.join(path)}")
    created = _find_key(lines, path)
    if created is None:
        raise ConfigPatchError(f"failed to create {'.'.join(path)}")
    return created


def _ensure_scalar(
    lines: list[str],
    path: tuple[str, ...],
    value: str,
    actions: list[str],
    warnings: list[str],
    *,
    warn_if_different: bool = False,
) -> None:
    existing = _find_key(lines, path)
    dotted = ".".join(path)
    if existing is not None:
        current = _scalar_value(existing.raw_value)
        if current:
            if current in _legacy_default_values(path):
                lines[existing.index] = f"{' ' * existing.indent}{path[-1]}: {value}"
                actions.append(
                    f"updated {dotted}={value} from legacy default {current}"
                )
                return
            actions.append(f"preserved {dotted}={current}")
            if warn_if_different and current != value:
                warnings.append(f"{dotted} already {current}; did not overwrite {value}")
            return
        lines[existing.index] = f"{' ' * existing.indent}{path[-1]}: {value}"
        actions.append(f"set {dotted}={value}")
        return

    if len(path) == 1:
        _append_top_level(lines, f"{path[-1]}: {value}")
    else:
        parent = _ensure_mapping(lines, path[:-1], actions)
        indent = parent.indent + 2
        insert_at = _section_end(lines, parent)
        lines.insert(insert_at, f"{' ' * indent}{path[-1]}: {value}")
    actions.append(f"set {dotted}={value}")


def _set_scalar(
    lines: list[str],
    path: tuple[str, ...],
    value: str,
    actions: list[str],
) -> None:
    existing = _find_key(lines, path)
    dotted = ".".join(path)
    if existing is not None:
        lines[existing.index] = f"{' ' * existing.indent}{path[-1]}: {value}"
        actions.append(f"set {dotted}={value}")
        return

    if len(path) == 1:
        _append_top_level(lines, f"{path[-1]}: {value}")
    else:
        parent = _ensure_mapping(lines, path[:-1], actions)
        indent = parent.indent + 2
        insert_at = _section_end(lines, parent)
        lines.insert(insert_at, f"{' ' * indent}{path[-1]}: {value}")
    actions.append(f"set {dotted}={value}")


def patch_config_text(
    text: str,
    platform: str,
    adversarial_enabled: str | None = None,
) -> tuple[str, PatchResult]:
    if platform not in VALID_PLATFORMS:
        allowed = "|".join(sorted(VALID_PLATFORMS))
        raise ConfigPatchError(f"unknown platform {platform!r}; expected {allowed}")

    lines = text.splitlines()
    actions: list[str] = []
    warnings: list[str] = []

    for path, value in DEFAULTS:
        if (
            path == HIGH_RISK_REVIEW_PROVIDER_POLICY_PATH
            and _find_key(lines, path) is not None
        ):
            actions.append(f"preserved explicit {'.'.join(path)}")
            continue
        _ensure_scalar(lines, path, value, actions, warnings)

    _ensure_scalar(
        lines,
        ("guru", "platform"),
        platform,
        actions,
        warnings,
        warn_if_different=True,
    )
    if adversarial_enabled is not None:
        _set_scalar(
            lines,
            ("guru", "supervision", "adversarial_enabled"),
            _config_bool_string(adversarial_enabled),
            actions,
        )

    patched = "\n".join(lines).rstrip() + "\n"
    return patched, PatchResult(changed=patched != text, actions=actions, warnings=warnings)


def ensure_supervision_defaults(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    config_path = (
        Path(args.config).expanduser().resolve()
        if args.config
        else root / ".trellis" / "config.yaml"
    )
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    patched, result = patch_config_text(
        original,
        args.platform,
        args.adversarial_enabled,
    )

    for action in result.actions:
        print(f"  {action}")
    for warning in result.warnings:
        print(f"  warning: {warning}", file=sys.stderr)

    if args.dry_run:
        print(
            "  dry-run: config would change"
            if result.changed
            else "  dry-run: config already has supervision defaults"
        )
        return 0

    if result.changed:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(patched, encoding="utf-8")
        print(f"  patched: {config_path.relative_to(root)}")
    else:
        print("  config already has supervision defaults")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ensure = sub.add_parser(
        "ensure-supervision-defaults",
        help="fill missing Guru supervision defaults",
    )
    ensure.add_argument("--root", default=".", help="Trellis project root")
    ensure.add_argument("--config", help="explicit config.yaml path")
    ensure.add_argument(
        "--platform",
        required=True,
        choices=sorted(VALID_PLATFORMS),
        help="Guru platform for guru.platform when missing",
    )
    ensure.add_argument(
        "--adversarial-enabled",
        choices=sorted(BOOLEAN_TRUE | BOOLEAN_FALSE),
        help="override guru.supervision.adversarial_enabled",
    )
    ensure.add_argument("--dry-run", action="store_true")
    ensure.set_defaults(func=ensure_supervision_defaults)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigPatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
