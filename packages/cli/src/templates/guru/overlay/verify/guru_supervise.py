#!/usr/bin/env python3
"""Run Guru implement/check work through the official trellis channel runtime.

Usage:
    python3 guru_supervise.py [--adversarial] requirements <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] overview <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] detail <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] implement <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] check <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] implement-check <task-dir> [--dry-run]
    python3 guru_supervise.py implement-slices <task-dir> [--dry-run] [--parallel N] [--group <id>] [--backend auto|sub-agent|channel]
    python3 guru_supervise.py implementation-review <task-dir> [--aggregate] [--slice <UNIT> ...] [--staged] [--same-provider --user-quote <quote>]
    python3 guru_supervise.py status <task-dir> [--json]
    python3 guru_supervise.py kill <task-dir> --channel <name> --worker <name>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote, urlparse

# requirements digest 共享单一来源：guru_gate.py 与本脚本同在 overlay/verify（安装后同在
# .trellis/scripts/guru/）。脚本运行时其目录已是 sys.path[0]，此处显式补一遍兜底奇怪调用形态，
# 保证 _requirements_digest 复用 guru_gate 实现而非维护第二份（消除 digest 分叉 / 永久 stale）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guru_gate import (  # noqa: E402
    requirements_digest as _guru_gate_requirements_digest,
    collect_gate_artifacts as _guru_gate_collect_artifacts,
    GateArtifactError as _GateArtifactError,
    cmd_check_implementation as _guru_gate_check_implementation,
    _is_task_artifact_path as _guru_gate_is_task_artifact_path,
)
import guru_contract  # noqa: E402  commit contract reader for staged implementation-review targets
import guru_risk  # noqa: E402  共享风险 helper（③ 独立 check 触发判定）
import guru_review_record  # noqa: E402  P1 packet reader / 单一 writer / verdict 校验


VALID_ACTIONS = {
    "requirements",
    "overview",
    "detail",
    "implement",
    "check",
    "implement-check",
    "implementation-review",
}
VALID_CONFIG_DISPATCH_MODES = {"inline", "sub-agent", "channel"}
VALID_IMPLEMENT_SLICE_BACKENDS = {"auto", "sub-agent", "channel"}
VALID_PLATFORMS = {"cli", "flutter", "go", "ios", "h5"}

DEFAULT_PROVIDER = "codex"
DEFAULT_IMPLEMENT_TIMEOUT = "45m"
DEFAULT_CHECK_TIMEOUT = "30m"
DEFAULT_WARN_BEFORE = "5m"
DEFAULT_IMPLEMENT_CHECK_MAX_LOOPS = 3
DEFAULT_ADVERSARIAL_CLAUDE_MODEL = "claude-sonnet-4-6"
DEFAULT_ADVERSARIAL_CODEX_MODEL = "gpt-5.4"
DEFAULT_ADVERSARIAL_CODEX_REASONING_EFFORT = "high"
HIGH_RISK_REVIEW_PROVIDER_POLICIES = {"current", "opposite", "codex", "claude"}
DEFAULT_HIGH_RISK_REVIEW_PROVIDER_POLICY = "current"
DETERMINISTIC_REVIEW_BRIEF_MAX_CHARS = 16000
FOCUSED_REQUIREMENTS_CONTEXT_MAX_CHARS = 32000
FOCUSED_REQUIREMENT_ITEM_MAX_CHARS = 12000
ADVERSARIAL_MODEL_ACTIONS = {"requirements", "overview", "detail"}
GATES_KEY = "guru_gates"
ADVERSARIAL_SKIPS_KEY = "adversarial_skips"
REQUIREMENTS_REVIEW_KEY = "requirements_review"
REQUIREMENTS_CLEAN_MARKER = "review_result=clean/requirements-ready"

REPAIRABLE_IMPLEMENT_ROUTES = {"IMPLEMENT_DEFECT", "PROCESS_DEFECT"}
UPSTREAM_ROUTE_TARGETS = {
    "REQ_BLOCKER": "requirements",
    "OVERVIEW_DEFECT": "overview",
    "DETAIL_DEFECT": "detail",
}
ROUTE_RE = re.compile(
    r"\broute_class\s*[:=：]\s*`?(REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|PROCESS_DEFECT|IMPLEMENT_DEFECT|none)`?",
    re.IGNORECASE,
)
REVIEW_RESULT_RE = re.compile(
    r"\breview_result\s*[:=：]\s*`?([A-Za-z0-9_/-]+)`?",
    re.IGNORECASE,
)
SEVERITY_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
MAX_SEVERITY_RE = re.compile(
    r"\bmax_severity\s*[:=：]\s*`?(none|low|medium|high|critical)`?",
    re.IGNORECASE,
)

SKILL_BY_PLATFORM: dict[str, dict[str, list[str]]] = {
    "cli": {
        "requirements": [".agents/skills/trellis-brainstorm/SKILL.md"],
        "overview": [".agents/skills/trellis-meta/SKILL.md"],
        "detail": [".agents/skills/trellis-meta/SKILL.md"],
        "implement": [".agents/skills/trellis-before-dev/SKILL.md"],
        "check": [".agents/skills/trellis-check/SKILL.md"],
        "implementation-review": [".agents/skills/trellis-check/SKILL.md"],
        "implement-check": [
            ".agents/skills/trellis-before-dev/SKILL.md",
            ".agents/skills/trellis-check/SKILL.md",
        ],
    },
    "flutter": {
        "requirements": [".agents/skills/requirement-review/SKILL.md"],
        "overview": [
            ".agents/skills/client-design-overview-writing/SKILL.md",
            ".agents/skills/client-design-overview-review/SKILL.md",
        ],
        "detail": [
            ".agents/skills/client-design-detail-writing/SKILL.md",
            ".agents/skills/client-design-detail-review/SKILL.md",
        ],
        "implement": [".agents/skills/flutter-implementation-guru-writing/SKILL.md"],
        "check": [".agents/skills/flutter-implementation-guru-review/SKILL.md"],
        "implementation-review": [".agents/skills/flutter-implementation-guru-review/SKILL.md"],
        "implement-check": [
            ".agents/skills/flutter-implementation-guru-writing/SKILL.md",
            ".agents/skills/flutter-implementation-guru-review/SKILL.md",
        ],
    },
    "go": {
        "requirements": [".agents/skills/requirement-review/SKILL.md"],
        "overview": [
            ".agents/skills/go-design-overview-writing/SKILL.md",
            ".agents/skills/go-design-overview-review/SKILL.md",
        ],
        "detail": [
            ".agents/skills/go-design-detail-writing/SKILL.md",
            ".agents/skills/go-design-detail-review/SKILL.md",
        ],
        "implement": [".agents/skills/go-implementation-guru-writing/SKILL.md"],
        "check": [".agents/skills/go-implementation-guru-review/SKILL.md"],
        "implementation-review": [".agents/skills/go-implementation-guru-review/SKILL.md"],
        "implement-check": [
            ".agents/skills/go-implementation-guru-writing/SKILL.md",
            ".agents/skills/go-implementation-guru-review/SKILL.md",
        ],
    },
    "ios": {
        "requirements": [".agents/skills/requirement-review/SKILL.md"],
        "overview": [
            ".agents/skills/ios-design-overview-writing/SKILL.md",
            ".agents/skills/ios-design-overview-review/SKILL.md",
        ],
        "detail": [
            ".agents/skills/ios-design-detail-writing/SKILL.md",
            ".agents/skills/ios-design-detail-review/SKILL.md",
        ],
        "implement": [".agents/skills/ios-implementation-guru-writing/SKILL.md"],
        "check": [".agents/skills/ios-implementation-guru-review/SKILL.md"],
        "implementation-review": [".agents/skills/ios-implementation-guru-review/SKILL.md"],
        "implement-check": [
            ".agents/skills/ios-implementation-guru-writing/SKILL.md",
            ".agents/skills/ios-implementation-guru-review/SKILL.md",
        ],
    },
    "h5": {
        "requirements": [".agents/skills/requirement-review/SKILL.md"],
        "overview": [
            ".agents/skills/h5-design-overview-writing/SKILL.md",
            ".agents/skills/h5-design-overview-review/SKILL.md",
        ],
        "detail": [
            ".agents/skills/h5-design-detail-writing/SKILL.md",
            ".agents/skills/h5-design-detail-review/SKILL.md",
        ],
        "implement": [".agents/skills/h5-implementation-guru-writing/SKILL.md"],
        "check": [".agents/skills/h5-implementation-guru-review/SKILL.md"],
        "implementation-review": [".agents/skills/h5-implementation-guru-review/SKILL.md"],
        "implement-check": [
            ".agents/skills/h5-implementation-guru-writing/SKILL.md",
            ".agents/skills/h5-implementation-guru-review/SKILL.md",
        ],
    },
}

KEY_RE = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z0-9_-]+)\s*:\s*(?P<value>.*)$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class GuruSupervisionError(RuntimeError):
    """Raised when Guru supervision cannot be configured safely."""


@dataclass(frozen=True)
class SupervisionConfig:
    root: Path
    platform: str
    current_provider: str
    provider: str
    adversarial: bool
    adversarial_enabled: bool
    implement_timeout: str
    check_timeout: str
    warn_before: str
    idle_timeout: str | None
    max_live_workers: str | None
    trellis_bin: str
    adversarial_model: str | None
    adversarial_reasoning_effort: str | None
    high_risk_review_provider_policy: str = DEFAULT_HIGH_RISK_REVIEW_PROVIDER_POLICY


@dataclass(frozen=True)
class ReviewProviderResolution:
    check_config: SupervisionConfig
    reason: str
    provider_override_source: str
    same_provider_user_quote: str | None
    review_target_kind: str


@dataclass(frozen=True)
class RunPlan:
    action: str
    task_dir: Path
    run_id: str
    channel: str
    worker: str
    create_cmd: list[str]
    spawn_cmd: list[str]
    send_cmd: list[str]
    wait_cmd: list[str]
    messages_cmd: list[str]
    brief: str
    files: list[Path]
    jsonls: list[Path]


@dataclass(frozen=True)
class ReviewTarget:
    unit_id: str | None
    review_target: str
    packet: dict
    slice_packet_path: Path | None
    digest_source: str
    active_brief: str
    reviewed_target_digest: str | None = None


def _parse_key_line(line: str) -> tuple[int, str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = KEY_RE.match(line)
    if match is None:
        return None
    return len(match.group("indent")), match.group("key"), match.group("value")


def _has_scalar(raw_value: str) -> bool:
    value = raw_value.strip()
    return bool(value) and not value.startswith("#")


def _scalar(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("#"):
        return ""
    for marker in (" #", "\t#"):
        idx = value.find(marker)
        if idx >= 0:
            value = value[:idx].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value


def _config_value(root: Path, path: tuple[str, ...]) -> str | None:
    config_path = root / ".trellis" / "config.yaml"
    if not config_path.exists():
        return None
    stack: list[tuple[int, str]] = []
    for line in config_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_key_line(line)
        if parsed is None:
            continue
        indent, key, raw_value = parsed
        while stack and indent <= stack[-1][0]:
            stack.pop()
        current_path = tuple(k for _, k in stack) + (key,)
        if current_path == path:
            value = _scalar(raw_value)
            return value or None
        if not _has_scalar(raw_value):
            stack.append((indent, key))
    return None


def _config_entry(root: Path, path: tuple[str, ...]) -> tuple[bool, str | None]:
    """Return presence separately from value so explicit empty YAML fails closed."""
    config_path = root / ".trellis" / "config.yaml"
    if not config_path.exists():
        return False, None
    stack: list[tuple[int, str]] = []
    for line in config_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_key_line(line)
        if parsed is None:
            continue
        indent, key, raw_value = parsed
        while stack and indent <= stack[-1][0]:
            stack.pop()
        current_path = tuple(k for _, k in stack) + (key,)
        if current_path == path:
            return True, _scalar(raw_value)
        if not _has_scalar(raw_value):
            stack.append((indent, key))
    return False, None


def _config_bool(root: Path, path: tuple[str, ...], default: bool) -> bool:
    value = _config_value(root, path)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".trellis").is_dir():
            return candidate
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".trellis").is_dir():
            return candidate
    raise GuruSupervisionError("could not find .trellis; pass --root")


def _resolve_root(args_root: str | None, task_dir: Path) -> Path:
    if args_root:
        root = Path(args_root).expanduser().resolve()
        if not (root / ".trellis").is_dir():
            raise GuruSupervisionError(f"{root} is not a Trellis project")
        return root
    return _find_repo_root(task_dir.resolve())


def _sanitize(value: str, *, limit: int = 80) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower()).strip("-")
    return (clean or "task")[:limit].strip("-") or "task"


def _default_run_id() -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{now}-{os.getpid()}"


def _existing_paths(paths: Sequence[Path]) -> list[Path]:
    return [path for path in paths if path.exists()]


def _dedupe_paths(paths: Sequence[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _read_json_object(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _files_from_reference(root: Path, base_dir: Path, reference: str) -> list[Path]:
    raw = reference.strip().strip("<>")
    if not raw:
        return []
    parsed = urlparse(raw)
    if parsed.scheme and parsed.scheme not in {"file"}:
        return []
    raw_path = unquote(parsed.path if parsed.scheme == "file" else raw)
    raw_path = raw_path.split("#", 1)[0].split("?", 1)[0].strip()
    if not raw_path:
        return []

    ref_path = Path(raw_path).expanduser()
    candidates = [ref_path] if ref_path.is_absolute() else [root / ref_path, base_dir / ref_path]
    files: list[Path] = []
    for candidate in candidates:
        if candidate.is_file():
            if candidate.suffix.lower() in {".md", ".markdown", ".json", ".jsonl"}:
                files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                sorted(
                    path
                    for path in candidate.rglob("*")
                    if path.is_file()
                    and path.suffix.lower() in {".md", ".markdown", ".json", ".jsonl"}
                )
            )
    return _dedupe_paths(files)


def _requirements_reference_files(root: Path, task_dir: Path) -> list[Path]:
    files: list[Path] = []
    task_json = task_dir / "task.json"
    data = _read_json_object(task_json)
    related = data.get("relatedFiles") if data else None
    if isinstance(related, list):
        for item in related:
            if isinstance(item, str):
                files.extend(_files_from_reference(root, task_dir, item))

    for markdown_path in sorted(task_dir.glob("*.md")):
        text = markdown_path.read_text(encoding="utf-8", errors="replace")
        for match in MARKDOWN_LINK_RE.finditer(text):
            files.extend(_files_from_reference(root, markdown_path.parent, match.group(1)))
    return _dedupe_paths(files)


def _trellis_cmd(config: SupervisionConfig, args: Sequence[str]) -> list[str]:
    return [config.trellis_bin, *args]


def _clip_context(text: str, *, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text


def _route_from_output(text: str) -> str | None:
    route_matches = list(ROUTE_RE.finditer(text))
    verdict_region = text
    if route_matches:
        last_route = route_matches[-1]
        route = last_route.group(1).upper()
        if route != "NONE":
            return route
        verdict_start = route_matches[-2].end() if len(route_matches) > 1 else 0
        verdict_region = text[verdict_start:]
    result_matches = list(REVIEW_RESULT_RE.finditer(verdict_region))
    if result_matches:
        result = result_matches[-1].group(1).strip().lower()
        if result in {"clean", "final-verification-ready", "clean/final-verification-ready"}:
            return "clean"
    if "review_result=clean/final-verification-ready" in verdict_region:
        return "clean"
    return None


def _opposite_provider(provider: str) -> str:
    current = provider.strip().lower()
    if current == "codex":
        return "claude"
    if current == "claude":
        return "codex"
    return DEFAULT_PROVIDER


def _packet_requires_opposite_review(packet: dict | None) -> bool:
    if not isinstance(packet, dict):
        return False
    semantic_provider = packet.get("semantic_review_provider")
    if not isinstance(semantic_provider, dict):
        return False
    return (
        semantic_provider.get("provider", "opposite") == "opposite"
        and semantic_provider.get("required", True) is True
    )


def _packet_is_high_risk(packet: dict | None) -> bool:
    if not isinstance(packet, dict):
        return False
    if packet.get("risk") in {"high", "critical"}:
        return True
    reasons = packet.get("risk_reasons")
    return isinstance(reasons, list) and any(
        isinstance(reason, str) and reason in guru_risk.RISK_REASON_KEYWORDS
        for reason in reasons
    )


def _slice_uses_high_risk_review_policy(packet: dict | None, task_dir: Path) -> bool:
    if not isinstance(packet, dict):
        return False
    if _packet_is_high_risk(packet):
        return True
    if packet.get("risk") == "low":
        return False
    return guru_risk.task_risk_level(str(task_dir)) == "high"


def _implementation_review_check_config(
    config: SupervisionConfig,
    *,
    packet: dict | None,
    independent_required: bool,
    independent_reason: str,
    high_risk_policy_applies: bool,
    review_target_kind: str,
    same_provider_user_quote: str | None = None,
) -> ReviewProviderResolution:
    if review_target_kind not in {"slice", "staged", "aggregate"}:
        raise GuruSupervisionError(
            "review_target_kind must be slice|staged|aggregate; "
            f"got {review_target_kind!r}"
        )
    if not isinstance(high_risk_policy_applies, bool):
        raise GuruSupervisionError("high_risk_policy_applies must be bool")
    if same_provider_user_quote is not None:
        quote = same_provider_user_quote.strip()
        if not quote:
            raise GuruSupervisionError(
                "cli_same_provider resolution requires a non-empty user quote"
            )
        return ReviewProviderResolution(
            check_config=config,
            reason="same-provider explicitly authorized by user",
            provider_override_source="cli_same_provider",
            same_provider_user_quote=quote,
            review_target_kind=review_target_kind,
        )

    if review_target_kind in {"slice", "aggregate"} and high_risk_policy_applies:
        policy = config.high_risk_review_provider_policy
        if policy == "current":
            check_provider = config.provider
        elif policy == "opposite":
            check_provider = _opposite_provider(config.provider)
        else:
            check_provider = policy
        return ReviewProviderResolution(
            check_config=replace(
                config,
                current_provider=config.provider,
                provider=check_provider,
            ),
            reason=f"project high-risk review provider policy={policy}",
            provider_override_source="config_policy",
            same_provider_user_quote=None,
            review_target_kind=review_target_kind,
        )

    reasons: list[str] = []
    check_provider = config.provider
    semantic_provider = (
        packet.get("semantic_review_provider")
        if isinstance(packet, dict)
        else None
    )
    packet_provider = (
        semantic_provider.get("provider", "opposite")
        if isinstance(semantic_provider, dict)
        else None
    )
    if packet_provider in {"codex", "claude"}:
        check_provider = packet_provider
        reasons.append(f"semantic_review_provider pinned to {packet_provider}")
    elif _packet_requires_opposite_review(packet):
        check_provider = _opposite_provider(config.provider)
        reasons.append("semantic_review_provider opposite(required=true)")
    elif isinstance(semantic_provider, dict) and packet_provider == "opposite":
        reasons.append("semantic_review_provider opposite(required=false)")
    elif independent_required:
        check_provider = _opposite_provider(config.provider)
        reasons.append(independent_reason)
    check_config = replace(
        config,
        current_provider=config.provider,
        provider=check_provider,
    )
    return ReviewProviderResolution(
        check_config=check_config,
        reason="; ".join(reasons) if reasons else independent_reason,
        provider_override_source="staged_packet",
        same_provider_user_quote=None,
        review_target_kind=review_target_kind,
    )


def _report_review_provider_resolution(
    config: SupervisionConfig,
    resolution: ReviewProviderResolution,
) -> None:
    sys.stderr.write(
        "[guru-supervise] implementation review provider "
        f"source={resolution.provider_override_source} "
        f"policy={config.high_risk_review_provider_policy} "
        f"target={resolution.review_target_kind} "
        f"implement={config.provider} check={resolution.check_config.provider} "
        f"reason={resolution.reason}\n"
    )


def _adversarial_model(root: Path, provider: str) -> str | None:
    if provider == "claude":
        return (
            _config_value(root, ("guru", "supervision", "adversarial_claude_model"))
            or DEFAULT_ADVERSARIAL_CLAUDE_MODEL
        )
    if provider == "codex":
        return (
            _config_value(root, ("guru", "supervision", "adversarial_codex_model"))
            or DEFAULT_ADVERSARIAL_CODEX_MODEL
        )
    return None


def _adversarial_reasoning_effort(root: Path, provider: str) -> str | None:
    if provider == "codex":
        return (
            _config_value(
                root,
                ("guru", "supervision", "adversarial_codex_reasoning_effort"),
            )
            or DEFAULT_ADVERSARIAL_CODEX_REASONING_EFFORT
        )
    return None


def _load_config(
    root: Path,
    *,
    platform: str | None,
    provider: str | None,
    adversarial: bool,
    trellis_bin: str | None,
) -> SupervisionConfig:
    policy_path = ("guru", "supervision", "high_risk_review_provider_policy")
    policy_present, raw_policy = _config_entry(root, policy_path)
    if policy_present:
        review_provider_policy = (raw_policy or "").strip().lower()
        if review_provider_policy not in HIGH_RISK_REVIEW_PROVIDER_POLICIES:
            allowed = "|".join(sorted(HIGH_RISK_REVIEW_PROVIDER_POLICIES))
            raise GuruSupervisionError(
                "guru.supervision.high_risk_review_provider_policy must be one of "
                f"{allowed}; got {raw_policy!r}"
            )
    else:
        review_provider_policy = DEFAULT_HIGH_RISK_REVIEW_PROVIDER_POLICY

    resolved_platform = platform or _config_value(root, ("guru", "platform"))
    if resolved_platform not in VALID_PLATFORMS:
        allowed = "|".join(sorted(VALID_PLATFORMS))
        raise GuruSupervisionError(
            f"cannot determine Guru platform; pass --platform {allowed} "
            "or set guru.platform in .trellis/config.yaml"
        )

    current_provider = (
        provider
        or _config_value(root, ("guru", "supervision", "provider"))
        or DEFAULT_PROVIDER
    )
    spawned_provider = _opposite_provider(current_provider) if adversarial else current_provider

    return SupervisionConfig(
        root=root,
        platform=resolved_platform,
        current_provider=current_provider,
        provider=spawned_provider,
        adversarial=adversarial,
        adversarial_enabled=_config_bool(
            root,
            ("guru", "supervision", "adversarial_enabled"),
            True,
        ),
        implement_timeout=_config_value(
            root, ("guru", "supervision", "implement_timeout")
        )
        or DEFAULT_IMPLEMENT_TIMEOUT,
        check_timeout=_config_value(root, ("guru", "supervision", "check_timeout"))
        or DEFAULT_CHECK_TIMEOUT,
        warn_before=_config_value(root, ("guru", "supervision", "warn_before"))
        or DEFAULT_WARN_BEFORE,
        idle_timeout=_config_value(root, ("channel", "worker_guard", "idle_timeout")),
        max_live_workers=_config_value(
            root, ("channel", "worker_guard", "max_live_workers")
        ),
        trellis_bin=trellis_bin or os.environ.get("TRELLIS_BIN", "trellis"),
        adversarial_model=_adversarial_model(root, spawned_provider)
        if adversarial
        else None,
        adversarial_reasoning_effort=_adversarial_reasoning_effort(root, spawned_provider)
        if adversarial
        else None,
        high_risk_review_provider_policy=review_provider_policy,
    )


def collect_review_artifacts(task_dir: Path, gate: str, repo_root: Path) -> list[Path]:
    """为 flutter implement/check review worker 注入正式 requirement/design 包文件（SSOT 否决基线）。

    复用 guru_gate.collect_gate_artifacts（repo-root 安全枚举 + 声明却非法的包 fail-closed），把
    gate-local GateArtifactError 包装为 GuruSupervisionError（spawn 前硬停，不静默回落 task-local
    docs）。只返回 design/requirements 源文件——task-local prd/design/implement 已由 build_run_plan
    单独注入，避免重复。
    """
    try:
        entries = _guru_gate_collect_artifacts(str(task_dir), gate, str(repo_root))
    except _GateArtifactError as exc:
        raise GuruSupervisionError(f"SSOT 正式包 fail-closed：{exc}") from exc
    return [Path(e["path"]) for e in entries if e.get("source") in ("design", "requirements")]


def build_run_plan(
    action: str,
    task_dir: Path,
    config: SupervisionConfig,
    run_id: str,
    extra_brief: str = "",
    slice_packet_path: Path | None = None,
    focused_review_context: dict | None = None,
) -> RunPlan:
    if action not in VALID_ACTIONS:
        raise GuruSupervisionError(f"unknown action {action!r}")
    if not task_dir.is_dir():
        raise GuruSupervisionError(f"task directory not found: {task_dir}")

    worker_action = "check" if action == "implementation-review" else action
    action_timeout = (
        config.check_timeout
        if action in {"requirements", "check", "implementation-review"}
        else config.implement_timeout
    )
    run_slug = _sanitize(run_id, limit=40)
    provider_slug = _sanitize(config.provider, limit=24)
    task_slug = _sanitize(task_dir.name, limit=70)
    channel = f"guru-{task_slug}-{worker_action}-{run_slug}"
    worker = f"{worker_action}-{provider_slug}-{run_slug}"

    skill_rels = SKILL_BY_PLATFORM[config.platform][action]
    skill_paths = [config.root / rel for rel in skill_rels]
    focused_implementation_review = (
        action == "implementation-review"
        and isinstance(focused_review_context, dict)
    )
    artifact_candidates = [*skill_paths]
    if not focused_implementation_review:
        artifact_candidates.extend(
            [
                task_dir / "prd.md",
                task_dir / "design.md",
                task_dir / "implement.md",
            ]
        )
    if action == "requirements":
        artifact_candidates.extend(
            [
                task_dir / "task.json",
                *_requirements_reference_files(config.root, task_dir),
            ]
        )
    if (
        not focused_implementation_review
        and config.platform == "flutter"
        and action in {
            "implement",
            "check",
            "implement-check",
            "implementation-review",
        }
    ):
        # ② 为 flutter 实现期 review 注入正式 requirement/design 包(SSOT 否决基线);
        # 声明却非法/缺失的包由 collect_review_artifacts → GuruSupervisionError 在 spawn 前 fail-closed
        artifact_candidates.extend(collect_review_artifacts(task_dir, "detail", config.root))
    if slice_packet_path is not None:  # P1c R4-F2:注入 resolved slice packet,worker 才能逐条 invariant/正确 provider
        artifact_candidates.append(slice_packet_path)
    artifact_files = _dedupe_paths(_existing_paths(artifact_candidates))
    jsonl_names = [f"{worker_action}.jsonl"]
    if action == "implement-check":
        jsonl_names = ["implement.jsonl", "check.jsonl"]
    if focused_implementation_review:
        jsonls = []
    elif action == "requirements":
        jsonls = _dedupe_paths(sorted(task_dir.glob("*.jsonl")))
    else:
        jsonls = _existing_paths([task_dir / name for name in jsonl_names])

    create_cmd = _trellis_cmd(
        config,
        [
            "channel",
            "create",
            channel,
            "--task",
            str(task_dir),
            "--by",
            "main",
            "--cwd",
            str(config.root),
            "--description",
            f"Guru {action} {task_dir.name}",
        ],
    )

    spawn_cmd = _trellis_cmd(
        config,
        [
            "channel",
            "spawn",
            channel,
            "--agent",
            worker_action,
            "--provider",
            config.provider,
            "--as",
            worker,
            "--cwd",
            str(config.root),
            "--timeout",
            action_timeout,
            "--warn-before",
            config.warn_before,
        ],
    )
    if config.idle_timeout:
        spawn_cmd.extend(["--idle-timeout", config.idle_timeout])
    if config.max_live_workers:
        spawn_cmd.extend(["--max-live-workers", config.max_live_workers])
    if config.adversarial and action in ADVERSARIAL_MODEL_ACTIONS:
        if config.adversarial_model:
            spawn_cmd.extend(["--model", config.adversarial_model])
        if config.adversarial_reasoning_effort:
            spawn_cmd.extend(
                ["--reasoning-effort", config.adversarial_reasoning_effort]
            )
    for file_path in artifact_files:
        spawn_cmd.extend(["--file", str(file_path)])
    for jsonl_path in jsonls:
        spawn_cmd.extend(["--jsonl", str(jsonl_path)])

    send_cmd = _trellis_cmd(
        config,
        [
            "channel",
            "send",
            channel,
            "--as",
            "main",
            "--to",
            worker,
            "--stdin",
        ],
    )
    wait_cmd = _trellis_cmd(
        config,
        [
            "channel",
            "wait",
            channel,
            "--as",
            "main",
            "--from",
            worker,
            "--kind",
            "done,error,killed",
            "--timeout",
            action_timeout,
        ],
    )
    messages_cmd = _trellis_cmd(
        config,
        [
            "channel",
            "messages",
            channel,
            "--from",
            worker,
            "--raw",
            "--last",
            "20",
        ],
    )

    skill_names = ", ".join(Path(rel).parts[-2] for rel in skill_rels)
    skill_line = f"Load the injected Guru {config.platform} skill(s): {skill_names}."
    adversarial_line = ""
    if config.adversarial and action in {"requirements", "overview", "detail"}:
        review_kind = (
            "requirements reviewer"
            if action == "requirements"
            else "clean-context reviewer"
        )
        adversarial_line = (
            f"You are the adversarial {review_kind} from the opposite provider "
            f"({config.current_provider} -> {config.provider}); challenge the current plan before "
            "allowing it to proceed."
        )
    if action == "requirements":
        review_mode = (
            "opposite-provider adversarial requirements review"
            if config.adversarial
            else "requirements review"
        )
        responsibility = (
            f"Run the {review_mode} before human requirements confirmation. Review prd.md, task.json "
            "metadata, task jsonl manifests, any formal requirements package referenced by "
            "task.json relatedFiles or task markdown links, task context, and repository evidence before "
            "asking product questions. Inspect code, tests, configs, docs, .trellis/spec/, CONTEXT.md, "
            "CONTEXT-MAP.md, and docs/adr/ when available before asking product questions. Challenge "
            "behavior, terms, scope, lifecycle, ownership, failure paths, acceptance criteria, compliance, "
            "and current-code-vs-user-intent conflicts. Emit route_class=REQ_BLOCKER for any medium/high/"
            "critical requirement blocker; route REQ_BLOCKER back to requirements repair and rerun "
            "downstream overview/detail evidence after the requirements digest changes. Low severity "
            "wording nits or observations are non-blocking. In the final verdict, emit these fields "
            "together on separate lines: route_class=none|REQ_BLOCKER, "
            "review_result=clean/requirements-ready, and max_severity=none|low|medium|high|critical. "
            "Use max_severity=none or low only when no blocker remains. Emit "
            "review_result=clean/requirements-ready only when no blocker remains. Keep temporary "
            "requirement decisions in prd.md; do not write "
            "long-term glossary/spec/ADR content unless confirmed via Domain Grill rules. Requirements "
            "has no review-evidence command or clean streak. Stop before confirm requirements."
        )
    elif action in {"overview", "detail"}:
        reviewer = "clean-context"
        review_run_id = run_id
        if config.adversarial:
            reviewer = f"clean-context-adversarial-{provider_slug}"
            review_run_id = f"{run_id}-{provider_slug}"
        deletion_audit_option = (
            ' --deletion-audit "<none|deletion audit summary>"'
            if action == "detail"
            else ""
        )
        detail_audit_line = (
            " For detail review, D9 deletion audit is mandatory: distinguish obsolete facts removed, "
            "contracts moved to a named replacement, intentional N/A with reason, and blocking contract loss."
            if action == "detail"
            else ""
        )
        responsibility = (
            f"Write or repair the {action} design artifact, run two clean review passes for the current digest, "
            f"and record each clean pass with `python3 .trellis/scripts/guru/guru_gate.py record-review {action} "
            f"{task_dir} --result clean --max-severity low --reviewer {reviewer} --run-id {review_run_id}-rN "
            f"--evidence \"<review evidence>\"{deletion_audit_option}`.{detail_audit_line} If medium+ findings remain, record findings with "
            "--finding-class REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|IMPLEMENT_DEFECT|PROCESS_DEFECT and stop."
        )
    elif action == "implement":
        responsibility = (
            "Implement according to the Guru workflow. Record mutable execution evidence in task-local "
            "evidence files; do not edit prd.md, design.md, or implement.md after detail confirmation "
            "unless intentionally returning to the detail gate."
        )
    elif action == "implement-check":
        responsibility = (
            "Implement the planned slices, then review the current diff under Guru quality rules, self-fixing only "
            "issues in scope. Route IMPLEMENT_DEFECT, DETAIL_DEFECT, OVERVIEW_DEFECT, REQ_BLOCKER, and "
            "PROCESS_DEFECT explicitly. A single clean implementation check is MVP review evidence only when the "
            "output includes review_result=clean/final-verification-ready, reviewed diff/artifact context, and "
            "validation_summary. Do not create implementation guru_gates. Record mutable execution evidence in "
            "task-local evidence files, do not mutate confirmed detail artifacts, and stop at final validation "
            "plus hard boundary."
        )
    elif action == "implementation-review":
        responsibility = (
            "Review the exact implementation target under Guru quality rules without implementing or editing files. "
            "Remain read-only: do not modify source, tests, review records, Gate code, the index, task artifacts, "
            "or Git history. "
            "Emit a complete required implementation review verdict for commit evidence and stop after one review pass."
        )
    else:
        responsibility = "Review the current diff under Guru quality rules and self-fix only mechanical issues."
    brief = "\n".join(
        [line for line in [
            f"Active task: {task_dir}",
            skill_line,
            adversarial_line,
            responsibility,
            "Do not commit, push, merge, archive, or run finish-work.",
        ] if line]
    )
    if extra_brief:
        brief = f"{brief}\n{extra_brief}"
    if focused_implementation_review:
        brief = (
            f"{brief}\nfocused_review_context="
            + json.dumps(
                focused_review_context,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )

    return RunPlan(
        action=action,
        task_dir=task_dir,
        run_id=run_id,
        channel=channel,
        worker=worker,
        create_cmd=create_cmd,
        spawn_cmd=spawn_cmd,
        send_cmd=send_cmd,
        wait_cmd=wait_cmd,
        messages_cmd=messages_cmd,
        brief=brief,
        files=artifact_files,
        jsonls=jsonls,
    )


def _print_dry_run(plan: RunPlan) -> None:
    print(f"TASK={shlex.quote(str(plan.task_dir))}")
    print(f"CHANNEL={shlex.quote(plan.channel)}")
    print(f"WORKER={shlex.quote(plan.worker)}")
    print("")
    print(shlex.join(plan.create_cmd))
    print(shlex.join(plan.spawn_cmd))
    print(f"printf '%s\\n' {shlex.quote(plan.brief)} | {shlex.join(plan.send_cmd)}")
    print(shlex.join(plan.wait_cmd))
    print(shlex.join(plan.messages_cmd))
    print("")
    if plan.files:
        print("Injected files:")
        for file_path in plan.files:
            print(f"  {file_path}")
    if plan.jsonls:
        print("Injected jsonl manifests:")
        for jsonl_path in plan.jsonls:
            print(f"  {jsonl_path}")


def _run(cmd: Sequence[str], *, cwd: Path, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(cmd),
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result


def _record_adversarial_skip(plan: RunPlan, config: SupervisionConfig, reason: str) -> None:
    task_json = plan.task_dir / "task.json"
    try:
        data = json.loads(task_json.read_text(encoding="utf-8")) if task_json.exists() else {}
        if not isinstance(data, dict):
            return
        gates = data.setdefault(GATES_KEY, {})
        if not isinstance(gates, dict):
            return
        skips = gates.setdefault(ADVERSARIAL_SKIPS_KEY, [])
        if not isinstance(skips, list):
            return
        skips.append(
            {
                "action": plan.action,
                "provider": config.provider,
                "current_provider": config.current_provider,
                "channel": plan.channel,
                "worker": plan.worker,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        task_json.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = task_json.with_name(f"{task_json.name}.tmp.{os.getpid()}")
        tmp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_path, task_json)
    except Exception as exc:
        # Skip persistence is advisory; it must never block the main workflow.
        sys.stderr.write(f"[guru-supervise] failed to record adversarial skip: {exc}\n")


def _requirements_digest(task_dir: Path, repo_root: Path | None = None) -> str:
    """requirements digest 单一来源：委托 guru_gate.requirements_digest（同 overlay/verify 目录）。

    历史上本函数是独立实现（只哈希 prd.md，不 import guru_gate），与 guru_gate._gate_digest
    并存——两者碰巧一致但只要 guru_gate 把正式需求包纳入 requirements digest 就会分叉、
    supervise 写入的 review digest 与 gate 判断的 current digest 永久 stale。现统一调用共享
    helper，保证两脚本对 requirements digest 字节一致；无 requirement_package 时仍只含 prd.md。

    repo_root（解 codex blocker）：requirement_package 是「相对 repo root」字段。本脚本支持
    `--root <repo>` 并可在 cwd≠root 下运行（gate 自身命令则 cwd==root）。必须把 config.root
    透传给共享 helper，否则正式需求包会按进程 cwd 解析成 <cwd>/docs/...（空包/错包），与 gate
    从 repo root 算的 digest 分叉、review 立刻 stale。
    """
    return _guru_gate_requirements_digest(
        str(task_dir), str(repo_root) if repo_root is not None else None
    )


def _negated_req_blocker_mention(messages: str, start: int) -> bool:
    line_start = messages.rfind("\n", 0, start) + 1
    prefix = messages[line_start:start].lower()[-120:]
    return bool(
        re.search(
            r"\b(?:no|not|without|zero)\s+"
            r"(?:(?:a|an|actual|blocking|open|remaining|unresolved|new|medium\+)\s+){0,4}$",
            prefix,
        )
        or re.search(
            r"\b(?:there\s+(?:is|are)\s+no|no\s+blocking|not\s+a|not\s+an)\s+"
            r"(?:(?:actual|blocking|open|remaining|unresolved|new|medium\+)\s+){0,4}$",
            prefix,
        )
    )


def _requirements_review_verdict(messages: str) -> tuple[str, str]:
    matches = list(ROUTE_RE.finditer(messages))
    if matches:
        route = matches[-1].group(1).upper()
        if route != "NONE":
            return "blocked", f"route_class={route}"
    verdict_start = matches[-1].start() if matches else 0
    verdict_region = messages[verdict_start:]
    route_spans = [
        (match.start(1) - verdict_start, match.end(1) - verdict_start)
        for match in matches
        if match.start() >= verdict_start
    ]
    for match in re.finditer(r"\bREQ_BLOCKER\b", verdict_region, re.IGNORECASE):
        if any(start <= match.start() and match.end() <= end for start, end in route_spans):
            continue
        if _negated_req_blocker_mention(verdict_region, match.start()):
            continue
        return "blocked", "bare REQ_BLOCKER"
    if REQUIREMENTS_CLEAN_MARKER in verdict_region:
        return "clean", REQUIREMENTS_CLEAN_MARKER
    return "deferred", "missing requirements review verdict"


def _requirements_review_max_severity(messages: str, status: str) -> str:
    matches = list(ROUTE_RE.finditer(messages))
    verdict_region = messages[matches[-1].start():] if matches else messages
    values = [
        match.group(1).lower()
        for match in MAX_SEVERITY_RE.finditer(verdict_region)
    ]
    if not values:
        return ""
    return values[-1]


def _record_requirements_review(
    plan: RunPlan,
    config: SupervisionConfig,
    status: str,
    reason: str,
    max_severity: str = "",
) -> bool:
    if not (config.adversarial and plan.action == "requirements"):
        return True
    task_json = plan.task_dir / "task.json"
    try:
        data = json.loads(task_json.read_text(encoding="utf-8")) if task_json.exists() else {}
        if not isinstance(data, dict):
            return False
        gates = data.setdefault(GATES_KEY, {})
        if not isinstance(gates, dict):
            return False
        gates[REQUIREMENTS_REVIEW_KEY] = {
            "action": plan.action,
            "provider": config.provider,
            "current_provider": config.current_provider,
            "adversarial": True,
            "status": status,
            "max_severity": max_severity,
            "artifact_digest": _requirements_digest(plan.task_dir, config.root),
            "run_id": plan.run_id,
            "channel": plan.channel,
            "worker": plan.worker,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        task_json.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = task_json.with_name(f"{task_json.name}.tmp.{os.getpid()}")
        tmp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_path, task_json)
        return True
    except Exception as exc:
        # Missing persisted evidence makes the requirements review unusable for downstream gates.
        sys.stderr.write(f"[guru-supervise] failed to record requirements review: {exc}\n")
        return False


def _skip_adversarial(
    plan: RunPlan,
    config: SupervisionConfig,
    reason: str,
    messages: str = "",
) -> tuple[int, str, str]:
    _record_adversarial_skip(plan, config, reason)
    _record_requirements_review(plan, config, "deferred", reason)
    sys.stderr.write(
        f"[guru-supervise] skipped adversarial {config.provider} review: {reason}\n"
    )
    if plan.action == "requirements":
        return 2, "skipped", messages
    return 0, "skipped", messages


def _execute_plan(plan: RunPlan, config: SupervisionConfig) -> tuple[int, str | None, str]:
    if config.provider != "codex" or config.current_provider != "codex":
        sys.stderr.write(
            "[guru-supervise] BLOCKED: V0 launch boundary is Codex-only; "
            f"current={config.current_provider!r} worker={config.provider!r}\n"
        )
        return 2, None, ""
    for command in (plan.create_cmd, plan.spawn_cmd):
        try:
            result = _run(command, cwd=config.root)
        except OSError as exc:
            if config.adversarial:
                return _skip_adversarial(
                    plan,
                    config,
                    f"{shlex.join(command)} failed: {exc}",
                )
            raise
        if result.returncode != 0:
            if config.adversarial:
                return _skip_adversarial(
                    plan,
                    config,
                    f"{shlex.join(command)} exited {result.returncode}",
                )
            return result.returncode, None, ""

    try:
        result = _run(plan.send_cmd, cwd=config.root, stdin=plan.brief)
    except OSError as exc:
        if config.adversarial:
            return _skip_adversarial(
                plan,
                config,
                f"{shlex.join(plan.send_cmd)} failed: {exc}",
            )
        raise
    if result.returncode != 0:
        if config.adversarial:
            return _skip_adversarial(
                plan,
                config,
                f"{shlex.join(plan.send_cmd)} exited {result.returncode}",
            )
        return result.returncode, None, ""

    try:
        wait = _run(plan.wait_cmd, cwd=config.root)
    except OSError as exc:
        if config.adversarial:
            return _skip_adversarial(
                plan,
                config,
                f"{shlex.join(plan.wait_cmd)} failed: {exc}",
            )
        raise
    terminal = _terminal_status(wait.stdout)
    try:
        messages = _run(plan.messages_cmd, cwd=config.root)
    except OSError as exc:
        if config.adversarial:
            return _skip_adversarial(
                plan,
                config,
                f"{shlex.join(plan.messages_cmd)} failed: {exc}",
            )
        raise
    provider_evidence = wait.stdout + "\n" + messages.stdout
    if re.search(r"\bclaude\b", provider_evidence, re.IGNORECASE):
        sys.stderr.write("[guru-supervise] BLOCKED: forbidden provider text/event detected\n")
        return 2, terminal, messages.stdout
    if wait.returncode != 0:
        if config.adversarial:
            return _skip_adversarial(
                plan,
                config,
                f"{shlex.join(plan.wait_cmd)} exited {wait.returncode}",
                messages.stdout,
            )
        return wait.returncode, terminal, messages.stdout
    if config.adversarial and terminal != "done":
        return _skip_adversarial(
            plan,
            config,
            f"worker terminal status was {terminal or 'missing'}",
            messages.stdout,
        )
    if config.adversarial and plan.action == "requirements":
        status, reason = _requirements_review_verdict(messages.stdout)
        max_severity = _requirements_review_max_severity(messages.stdout, status)
        if status == "clean":
            if not max_severity:
                status = "blocked"
                reason = "missing max_severity"
            elif SEVERITY_ORDER.get(max_severity, 99) > SEVERITY_ORDER["low"]:
                status = "blocked"
                reason = f"max_severity={max_severity}"
        recorded = _record_requirements_review(plan, config, status, reason, max_severity)
        if not recorded:
            sys.stderr.write(
                "[guru-supervise] BLOCKED: requirements adversarial review "
                "could not be persisted to task.json; downstream gates would "
                "not have clean/current evidence.\n"
            )
            return 2, terminal, messages.stdout
        if status != "clean":
            sys.stderr.write(
                "[guru-supervise] BLOCKED: requirements adversarial review is not clean "
                f"({reason}). Repair requirements and rerun until "
                f"{REQUIREMENTS_CLEAN_MARKER} with no blocking route_class.\n"
            )
            return 2, terminal, messages.stdout
    return (0 if terminal == "done" else 1), terminal, messages.stdout


def _terminal_status(output: str) -> str | None:
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("kind")
        if kind in {"done", "error", "killed"}:
            return str(kind)
    return None


def run_action(args: argparse.Namespace, action: str) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
    if action in {"implement", "check", "implement-check"}:
        if _guru_gate_check_implementation(str(task_dir)) != 0:
            print(
                "[guru-supervise] BLOCKED: implementation/check workers require "
                "task.json.status == in_progress. Run task.py start after START_READY.",
                file=sys.stderr,
            )
            return 2
    config = _load_config(
        root,
        platform=args.platform,
        provider=args.provider,
        adversarial=args.adversarial,
        trellis_bin=args.trellis_bin,
    )
    run_id = args.run_id or _default_run_id()
    plan = build_run_plan(action, task_dir, config, run_id)

    if args.dry_run:
        _print_dry_run(plan)
        return 0

    if config.adversarial and not config.adversarial_enabled:
        rc, _terminal, _messages = _skip_adversarial(
            plan,
            config,
            "disabled by guru.supervision.adversarial_enabled=false",
        )
        return rc

    rc, _terminal, _messages = _execute_plan(plan, config)
    return rc


def _resolve_slice_packet(task_dir: str, slice_arg):
    """P1b resolve:--slice 显式 / 单 packet auto-select / 多 packet 未指定→ambiguous(返回候选列表) /
    无 packet→None(回落 P0)。返回 (unit_id|None, ambiguous_candidates|None)。"""
    if slice_arg:
        return (slice_arg, None)
    packets = guru_review_record.list_packets(task_dir)
    if len(packets) == 1:
        return (packets[0], None)
    if len(packets) > 1:
        return (None, packets)
    return (None, None)


def _scope_preflight(repo_root: str, packet: dict):
    """P1b scope preflight(BHV-002):**代码** dirty(scan_dirty_paths 唯一 -z -uall 来源,经
    guru_risk._is_scannable 排除 .trellis 运行时/文档/配置噪声)须全属 packet target_paths 或
    dirty_state.unrelated;越界 → 返回 failure 描述(调用方记 SCOPE_INVALID 硬停)。scan 失败
    fail-closed(不可确认 review target)。返回 None=通过。"""
    try:
        dirty = guru_risk.scan_dirty_paths(repo_root)
    except guru_risk.RiskScanError as exc:
        return f"scan failed (fail-closed): {exc}"
    code_dirty = [p for p in dirty if guru_risk._is_scannable(p)]
    targets = set(packet.get("target_paths", []))
    unrelated = set(packet.get("dirty_state", {}).get("unrelated", []))
    out_of_scope = sorted(p for p in code_dirty if p not in targets and p not in unrelated)
    if out_of_scope:
        return f"out-of-scope dirty paths: {out_of_scope}"
    return None


def _staged_paths(repo_root: str) -> tuple[list[str], str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--no-renames", "-z"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"cannot read staged changes: {exc}"
    if result.returncode != 0:
        return [], f"git diff --cached failed: {result.stderr.strip()}"
    return [path for path in result.stdout.split("\0") if path], ""


def _unstaged_paths(repo_root: str) -> tuple[list[str], str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", "-z"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"cannot read unstaged changes: {exc}"
    if result.returncode != 0:
        return [], f"git diff failed: {result.stderr.strip()}"
    return [path for path in result.stdout.split("\0") if path], ""


def _dispatch_path_key(path: str) -> str:
    value = str(path).replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    value = value.strip("/")
    return value or "."


def _path_covered_by_targets(path: str, targets: set[str]) -> bool:
    path_key = _dispatch_path_key(path)
    for target in targets:
        target_key = _dispatch_path_key(target)
        if (
            target_key == "."
            or path_key == target_key
            or path_key.startswith(f"{target_key}/")
        ):
            return True
    return False


def _targets_overlap(left: str, right: str) -> bool:
    left_key = _dispatch_path_key(left)
    right_key = _dispatch_path_key(right)
    if left_key == "." or right_key == ".":
        return True
    return (
        left_key == right_key
        or left_key.startswith(f"{right_key}/")
        or right_key.startswith(f"{left_key}/")
    )


def _first_target_overlap(left_targets: Sequence[str], right_targets: Sequence[str]) -> str:
    for left in left_targets:
        for right in right_targets:
            if _targets_overlap(left, right):
                return f"{left}<->{right}"
    return ""


def _staged_target_drift(repo_root: str, target_paths: list) -> str:
    targets = {
        str(path).strip().strip("/")
        for path in target_paths
        if str(path).strip().strip("/")
    }
    staged_paths, staged_error = _staged_paths(repo_root)
    if staged_error:
        return f"cannot verify staged review target drift: {staged_error}"
    out_of_target = sorted(
        path for path in staged_paths if not _path_covered_by_targets(path, targets)
    )
    if out_of_target:
        return f"staged changes outside review target paths: {out_of_target}"
    unstaged_paths, unstaged_error = _unstaged_paths(repo_root)
    if unstaged_error:
        return f"cannot verify staged review target drift: {unstaged_error}"
    overlap = sorted(
        path
        for path in unstaged_paths
        if _path_covered_by_targets(path, targets)
    )
    if overlap:
        return f"unstaged changes overlap staged review target paths: {overlap}"
    return ""


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _normal_string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dedupe_strings(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _positive_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _parallel_arg(value: str) -> int:
    parsed = _positive_int(value)
    if parsed is None:
        raise argparse.ArgumentTypeError("--parallel must be a positive integer")
    return parsed


def _dispatch_mode_from_config(root: Path) -> tuple[str, str, list[str]]:
    raw = _config_value(root, ("codex", "dispatch_mode"))
    if raw is None or not raw.strip():
        return "inline", "", []
    mode = raw.strip().lower()
    if mode not in VALID_CONFIG_DISPATCH_MODES:
        return "inline", raw.strip(), [f"DISPATCH_MODE_INVALID:{raw.strip()}"]
    return mode, raw.strip(), []


def _select_dispatch_backend(root: Path, requested: str) -> dict:
    configured, raw_configured, blockers = _dispatch_mode_from_config(root)
    selected = configured if requested == "auto" else requested
    serial_reasons: list[str] = []
    if blockers and requested == "auto":
        serial_reasons.extend(blockers)
    if selected == "inline":
        serial_reasons.append("DISPATCH_MODE_INLINE_SERIAL_ONLY")
    if selected not in {"inline", "sub-agent", "channel"}:
        selected = "inline"
        serial_reasons.append(f"DISPATCH_BACKEND_INVALID:{requested}")
    return {
        "requested_backend": requested,
        "configured_dispatch_mode": configured,
        "raw_configured_dispatch_mode": raw_configured,
        "selected_backend": selected,
        "config_blockers": blockers,
        "serial_reasons": _dedupe_strings(serial_reasons),
    }


def _load_current_slice_plan(root: Path, task_dir: Path) -> tuple[dict, list[str]]:
    gate_script = Path(__file__).resolve().with_name("guru_gate.py")
    cmd = [
        "python3",
        _display_path(root, gate_script),
        "slice-plan",
        _display_path(root, task_dir),
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GuruSupervisionError(f"slice-plan failed before dispatch: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GuruSupervisionError(f"slice-plan failed before dispatch: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GuruSupervisionError(f"slice-plan returned non-JSON output: {exc}") from exc
    if not isinstance(payload, dict):
        raise GuruSupervisionError("slice-plan returned a non-object payload")
    return payload, cmd


def _slice_map(slice_plan: dict) -> dict[str, dict]:
    slices = slice_plan.get("slices", [])
    if not isinstance(slices, list):
        return {}
    mapped: dict[str, dict] = {}
    for entry in slices:
        if not isinstance(entry, dict):
            continue
        slice_id = str(entry.get("slice_id") or "").strip()
        if slice_id:
            mapped[slice_id] = entry
    return mapped


def _select_slice_group(slice_plan: dict, group_id: str | None) -> tuple[dict | None, list[str]]:
    groups = slice_plan.get("parallel_groups", [])
    if not isinstance(groups, list):
        groups = []
    valid_groups = [group for group in groups if isinstance(group, dict)]
    if group_id:
        for group in valid_groups:
            if str(group.get("group_id") or "") == group_id:
                return group, []
        return None, [f"GROUP_NOT_FOUND:{group_id}"]
    for group in valid_groups:
        if group.get("mode") == "writer" and _normal_string_list(group.get("slice_ids")):
            return group, []
    for group in valid_groups:
        if _normal_string_list(group.get("slice_ids")):
            return group, []
    return None, ["NO_PARALLEL_GROUPS"]


def _slice_dependency_blockers(slice_entry: dict) -> list[str]:
    blockers = _normal_string_list(slice_entry.get("parallel_blockers"))
    return [
        blocker for blocker in blockers
        if (
            blocker.startswith("DEPENDS_ON:")
            or blocker.startswith("DEPENDENCY_")
        )
    ]


def _slice_resource_blockers(slice_entry: dict) -> list[str]:
    locks = _normal_string_list(slice_entry.get("resource_locks"))
    return [f"RESOURCE_LOCK:{lock}" for lock in locks]


def _slice_target_paths(slice_entry: dict) -> list[str]:
    return _normal_string_list(slice_entry.get("target_paths"))


def _dispatch_action_for_group(group_mode: str) -> str:
    return "implementation-review" if group_mode == "read_only" else "implement-check"


def _recommended_command(slice_entry: dict, action: str) -> str:
    commands = slice_entry.get("recommended_commands")
    if isinstance(commands, dict):
        key = "implementation_review" if action == "implementation-review" else "implement_check"
        command = commands.get(key)
        if isinstance(command, str) and command.strip():
            return command.strip()
    command = slice_entry.get("recommended_command")
    return command.strip() if isinstance(command, str) else ""


def _supervisor_command(
    root: Path,
    task_dir: Path,
    slice_id: str,
    action: str,
    *,
    dry_run: bool,
) -> list[str]:
    script_ref = _display_path(root, Path(__file__).resolve())
    command = ["python3", script_ref, action, _display_path(root, task_dir), "--slice", slice_id]
    if dry_run:
        command.append("--dry-run")
    return command


def _sub_agent_brief(
    root: Path,
    task_dir: Path,
    slice_entry: dict,
    *,
    group_id: str,
    group_mode: str,
) -> str:
    slice_id = str(slice_entry.get("slice_id") or "").strip()
    target_paths = _slice_target_paths(slice_entry)
    agent_name = "trellis-check" if group_mode == "read_only" else "trellis-implement"
    write_rule = (
        "Read-only review slice: do not edit files."
        if group_mode == "read_only"
        else "Write only inside the allowed target_paths. If another path is required, stop and report the blocker."
    )
    targets = "\n".join(f"- {path}" for path in target_paths) if target_paths else "- <none>"
    return "\n".join([
        f"Active task: {_display_path(root, task_dir)}",
        "",
        f"You are already the `{agent_name}` sub-agent for this Guru slice. Implement directly in this workspace and do not spawn another `trellis-implement` or `trellis-check`.",
        "Do not create channels and do not call `trellis channel`; this dispatch uses the direct platform sub-agent backend.",
        f"Task slice: {slice_id}",
        f"Parallel group: {group_id}",
        f"Slice mode: {group_mode}",
        "Allowed target_paths:",
        targets,
        write_rule,
        "Preserve unrelated dirty work. Do not commit, push, merge, archive, or run finish-work.",
    ])


def _group_safety(
    group: dict | None,
    slices_by_id: dict[str, dict],
    backend: dict,
) -> tuple[list[dict], list[str], str]:
    if group is None:
        return [], ["NO_RUNNABLE_GROUP"], "blocked"

    group_mode = str(group.get("mode") or "serial").strip() or "serial"
    slice_ids = _normal_string_list(group.get("slice_ids"))
    selected_slices = [slices_by_id[slice_id] for slice_id in slice_ids if slice_id in slices_by_id]
    missing_ids = sorted(set(slice_ids) - set(slices_by_id))
    reasons = list(backend.get("serial_reasons", []))
    reasons.extend(f"SLICE_NOT_FOUND:{slice_id}" for slice_id in missing_ids)
    reasons.extend(_normal_string_list(group.get("blocking_reasons")))

    if not selected_slices:
        return [], _dedupe_strings(reasons or ["NO_RUNNABLE_SLICES"]), "blocked"
    if group_mode == "serial":
        reasons.append("SLICE_PLAN_SERIAL_GROUP")
    elif group_mode not in {"writer", "read_only"}:
        reasons.append(f"SLICE_PLAN_UNKNOWN_GROUP_MODE:{group_mode}")

    if group_mode == "writer":
        for entry in selected_slices:
            slice_id = str(entry.get("slice_id") or "").strip()
            target_paths = _slice_target_paths(entry)
            blockers = _normal_string_list(entry.get("parallel_blockers"))
            if not entry.get("parallel_safe"):
                reasons.append(f"SLICE_NOT_PARALLEL_SAFE:{slice_id}")
            if entry.get("parallel_mode") not in {"writer"}:
                reasons.append(f"SLICE_PLAN_SERIAL:{slice_id}")
            if not target_paths:
                reasons.append(f"TARGET_PATHS_MISSING:{slice_id}")
            dirty_scope = str(entry.get("dirty_scope") or "").strip()
            if dirty_scope not in {"clean", "isolated"}:
                reasons.append(f"DIRTY_SCOPE_INVALID:{slice_id}:{dirty_scope or 'unknown'}")
            if entry.get("dirty_out_of_scope"):
                reasons.append(f"SCOPE_INVALID:{slice_id}")
            reasons.extend(f"{slice_id}:{blocker}" for blocker in blockers)
            reasons.extend(f"{slice_id}:{blocker}" for blocker in _slice_dependency_blockers(entry))
            reasons.extend(f"{slice_id}:{blocker}" for blocker in _slice_resource_blockers(entry))

        for idx, left in enumerate(selected_slices):
            left_id = str(left.get("slice_id") or "").strip()
            left_targets = _slice_target_paths(left)
            for right in selected_slices[idx + 1:]:
                right_id = str(right.get("slice_id") or "").strip()
                overlap = _first_target_overlap(left_targets, _slice_target_paths(right))
                if overlap:
                    reasons.append(f"TARGET_PATH_OVERLAP:{left_id}:{right_id}:{overlap}")
    elif group_mode == "read_only":
        for entry in selected_slices:
            slice_id = str(entry.get("slice_id") or "").strip()
            if _slice_dependency_blockers(entry):
                reasons.extend(f"{slice_id}:{blocker}" for blocker in _slice_dependency_blockers(entry))

    reasons = _dedupe_strings(reasons)
    if reasons:
        return selected_slices, reasons, "serial"
    if len(selected_slices) == 1:
        return selected_slices, [], "serial"
    return selected_slices, [], "parallel"


def _effective_parallel_limit(
    selected_slices: list[dict],
    group: dict | None,
    decision: str,
    requested_parallel: int,
    backend: dict,
    root: Path,
) -> int:
    if decision != "parallel":
        return 1 if selected_slices else 0
    group_limit = _positive_int(str(group.get("max_parallel"))) if isinstance(group, dict) else None
    limit = min(requested_parallel, group_limit or requested_parallel, len(selected_slices))
    if backend.get("selected_backend") == "channel":
        channel_limit = _positive_int(_config_value(root, ("channel", "worker_guard", "max_live_workers")))
        if channel_limit is not None:
            limit = min(limit, channel_limit)
    return max(1, limit)


def _dispatch_item(
    root: Path,
    task_dir: Path,
    slice_entry: dict,
    *,
    group_id: str,
    group_mode: str,
    backend: str,
    dispatch_now: bool,
) -> dict:
    slice_id = str(slice_entry.get("slice_id") or "").strip()
    action = _dispatch_action_for_group(group_mode)
    recommended = _recommended_command(slice_entry, action)
    review_command = _recommended_command(slice_entry, "implementation-review")
    item = {
        "slice_id": slice_id,
        "mode": group_mode,
        "target_paths": _slice_target_paths(slice_entry),
        "dirty_scope": slice_entry.get("dirty_scope", ""),
        "parallel_safe": bool(slice_entry.get("parallel_safe")),
        "parallel_blockers": _normal_string_list(slice_entry.get("parallel_blockers")),
        "dispatch_now": dispatch_now,
        "recommended_command": recommended,
        "read_only_review_command": review_command,
    }
    if backend == "sub-agent":
        item["sub_agent"] = {
            "agent": "trellis-check" if group_mode == "read_only" else "trellis-implement",
            "brief": _sub_agent_brief(root, task_dir, slice_entry, group_id=group_id, group_mode=group_mode),
        }
    elif backend == "channel":
        item["channel"] = {
            "uses_existing_channel_plan_builder": True,
            "dry_run_command": shlex.join(_supervisor_command(root, task_dir, slice_id, action, dry_run=True)),
            "execute_command": shlex.join(_supervisor_command(root, task_dir, slice_id, action, dry_run=False)),
        }
    else:
        item["manual"] = {
            "reason": "inline dispatch mode is serial/manual only",
            "command": recommended,
        }
    return item


def run_implement_slices(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
    slice_plan, slice_plan_cmd = _load_current_slice_plan(root, task_dir)
    backend = _select_dispatch_backend(root, args.backend)
    group, group_errors = _select_slice_group(slice_plan, args.group)
    slices_by_id = _slice_map(slice_plan)
    selected_slices, safety_reasons, decision = _group_safety(group, slices_by_id, backend)
    if not selected_slices:
        safety_reasons.extend(_normal_string_list(slice_plan.get("blocking_reasons")))
    safety_reasons = _dedupe_strings([*group_errors, *safety_reasons])
    if safety_reasons and decision == "parallel":
        decision = "serial"
    if not selected_slices:
        decision = "blocked"

    group_id = str(group.get("group_id") or "") if isinstance(group, dict) else ""
    group_mode = str(group.get("mode") or "serial") if isinstance(group, dict) else "serial"
    parallel_limit = _effective_parallel_limit(
        selected_slices,
        group,
        decision,
        args.parallel,
        backend,
        root,
    )
    dispatch_backend = str(backend["selected_backend"])
    active_count = parallel_limit if decision == "parallel" else min(parallel_limit, len(selected_slices))
    dispatchable = decision != "blocked"
    items = [
        _dispatch_item(
            root,
            task_dir,
            entry,
            group_id=group_id,
            group_mode=group_mode,
            backend=dispatch_backend,
            dispatch_now=dispatchable and idx < active_count,
        )
        for idx, entry in enumerate(selected_slices)
    ]
    report = {
        "schema_version": 1,
        "command": "implement-slices",
        "task_dir": _display_path(root, task_dir),
        "dry_run": bool(args.dry_run),
        "slice_plan_command": shlex.join(slice_plan_cmd),
        "slice_plan_reread": True,
        "slice_plan_schema_version": slice_plan.get("schema_version"),
        "slice_plan_blocking_reasons": _normal_string_list(slice_plan.get("blocking_reasons")),
        "configured_dispatch_mode": backend["configured_dispatch_mode"],
        "raw_configured_dispatch_mode": backend["raw_configured_dispatch_mode"],
        "requested_backend": backend["requested_backend"],
        "selected_backend": dispatch_backend,
        "selected_group": group_id,
        "group_mode": group_mode,
        "decision": decision,
        "parallel_requested": args.parallel,
        "parallel_limit": parallel_limit,
        "downgrade_reasons": safety_reasons,
        "dispatch_items": items,
        "dispatch_now": [item["slice_id"] for item in items if item["dispatch_now"]],
        "deferred_slices": [item["slice_id"] for item in items if not item["dispatch_now"]],
        "read_only_fanout": [
            {
                "slice_id": item["slice_id"],
                "command": item["read_only_review_command"],
                "does_not_launch_implement_worker": True,
            }
            for item in items
            if item.get("read_only_review_command")
        ],
        "status_input": {
            "backend": dispatch_backend,
            "status_source": (
                "guru_supervise.py status --json"
                if dispatch_backend == "channel"
                else "main-session platform sub-agent results; no channel status queried"
            ),
            "status_command": (
                shlex.join(["python3", _display_path(root, Path(__file__).resolve()), "status", _display_path(root, task_dir), "--json"])
                if dispatch_backend == "channel"
                else ""
            ),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if decision == "blocked" else 0


def _review_invariant_brief(invariants: list | None) -> str:
    if not isinstance(invariants, list) or not invariants:
        return ""
    lines = ["expected_invariants:"]
    for inv in invariants:
        if not isinstance(inv, dict):
            continue
        inv_id = inv.get("invariant_id")
        if not isinstance(inv_id, str) or not inv_id.strip():
            continue
        detail = inv.get("rule") or inv.get("description") or inv.get("positive_case") or ""
        if isinstance(detail, str) and detail.strip():
            lines.append(f"- {inv_id.strip()}: {detail.strip()}")
        else:
            lines.append(f"- {inv_id.strip()}")
    if len(lines) == 1:
        return ""
    lines.append("只使用这些 invariant id 输出 invariant_status/invariant_evidence/invariant_reason；不要从其他 slice packet 借 id。")
    return "\n".join(lines) + "\n"


def _active_review_brief(
    *,
    label: str,
    review_target: str,
    target_paths: list,
    semantic_provider: dict,
    digest_source: str,
    invariants: list | None = None,
    slice_packet_path: Path | None = None,
    reviewed_target_digest: str | None = None,
) -> str:
    packet_line = f"slice_packet={slice_packet_path}\n" if slice_packet_path is not None else ""
    digest_line = (
        f"reviewed_target_digest={reviewed_target_digest}\n"
        if reviewed_target_digest is not None
        else ""
    )
    return (
        f"\nactive_review={label}\n"
        f"{packet_line}"
        f"review_target={review_target}\n"
        f"target_paths={target_paths}\n"
        f"target_digest_source={digest_source}\n"
        f"{digest_line}"
        f"semantic_review_provider={semantic_provider.get('provider')}(required={semantic_provider.get('required')})\n"
        "review_provider 必须写实际 worker provider（codex 或 claude），不要写 opposite/manual/ocr_optional。\n"
        "置顶逐行输出且不得漏写这 7 字段：review_result、route_class、review_target、review_provider、"
        "deterministic_checks、dirty_scope、invariant_coverage；不要用 target_paths/required_satisfied 替代。\n"
        f"{_review_invariant_brief(invariants)}"
        "随后输出逐条 invariant_status.<id>=pass|fail|not_applicable"
        "（pass 必随 invariant_evidence.<id>；not_applicable 必随 invariant_reason.<id>）。\n"
    )


def _slice_review_target(task_dir: Path, root: Path, unit_id: str, *, staged: bool) -> ReviewTarget:
    try:
        packet = guru_review_record.load_packet(str(task_dir), unit_id)
    except guru_review_record.ReviewRecordError as exc:
        kind = "PACKET_MISSING" if "不存在" in str(exc) else "PACKET_INVALID"
        raise GuruSupervisionError(f"{kind}:{exc}") from exc
    if not staged:
        scope_failure = _scope_preflight(str(root), packet)
        if scope_failure:
            raise GuruSupervisionError(f"SCOPE_INVALID:{scope_failure}")
    slice_packet_path = task_dir / "slice-packets" / f"{unit_id}.json"
    semantic_provider = packet.get("semantic_review_provider", {})
    digest_source = "index" if staged else "worktree"
    try:
        reviewed_target_digest = guru_review_record.target_snapshot_digest(
            str(root), packet.get("target_paths", []), digest_source
        )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(f"SCOPE_INVALID:target snapshot digest failed:{exc}") from exc
    return ReviewTarget(
        unit_id=unit_id,
        review_target=f"slice:{unit_id}",
        packet=packet,
        slice_packet_path=slice_packet_path,
        digest_source=digest_source,
        active_brief=_active_review_brief(
            label=unit_id,
            review_target=f"slice:{unit_id}",
            target_paths=packet.get("target_paths", []),
            semantic_provider=semantic_provider,
            digest_source=digest_source,
            invariants=packet.get("invariants", []),
            slice_packet_path=slice_packet_path,
            reviewed_target_digest=reviewed_target_digest,
        ),
        reviewed_target_digest=reviewed_target_digest,
    )


def _aggregate_review_target(
    task_dir: Path,
    root: Path,
    slice_ids: list[str],
) -> ReviewTarget:
    staged_paths, staged_error = _staged_paths(str(root))
    if staged_error:
        raise GuruSupervisionError(f"SCOPE_INVALID:{staged_error}")
    if not staged_paths:
        raise GuruSupervisionError("SCOPE_INVALID:no staged code paths to review")
    artifacts = [
        path
        for path in staged_paths
        if _guru_gate_is_task_artifact_path(path, str(task_dir), str(root))
    ]
    if artifacts:
        raise GuruSupervisionError(
            "SCOPE_INVALID:aggregate staged scope contains task/workspace artifacts: "
            + ", ".join(artifacts[:5])
        )
    try:
        existing = {
            receipt["slice_id"]
            for receipt in guru_review_record.receipt_records(str(task_dir))
            if receipt.get("slice_id") in set(slice_ids)
        }
        if existing:
            raise guru_review_record.ReviewRecordError(
                "aggregate bootstrap requires all selected slice receipts missing; "
                f"existing={sorted(existing)}"
            )
        packet = guru_review_record.build_aggregate_packet(
            str(task_dir),
            slice_ids,
            staged_paths,
        )
        reviewed_target_digest = guru_review_record.target_snapshot_digest(
            str(root),
            packet["target_paths"],
            "index",
        )
        packet["aggregate_target_digest"] = reviewed_target_digest
        packet["per_slice_target_digests"] = {
            slice_id: guru_review_record.target_snapshot_digest(
                str(root),
                paths,
                "index",
            )
            for slice_id, paths in packet["per_slice_target_paths"].items()
        }
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(f"PACKET_INVALID:{exc}") from exc
    aggregate_label = ",".join(packet["aggregate_slice_ids"])
    review_target = f"aggregate:{aggregate_label}"
    return ReviewTarget(
        unit_id="aggregate",
        review_target=review_target,
        packet=packet,
        slice_packet_path=None,
        digest_source="index",
        active_brief=_active_review_brief(
            label=aggregate_label,
            review_target=review_target,
            target_paths=packet["target_paths"],
            semantic_provider=packet["semantic_review_provider"],
            digest_source="index",
            invariants=packet["invariants"],
            reviewed_target_digest=reviewed_target_digest,
        ),
        reviewed_target_digest=reviewed_target_digest,
    )


def _staged_review_target(task_dir: Path, root: Path) -> ReviewTarget:
    staged_paths, staged_error = _staged_paths(str(root))
    if staged_error:
        raise GuruSupervisionError(f"SCOPE_INVALID:{staged_error}")
    if not staged_paths:
        raise GuruSupervisionError("SCOPE_INVALID:no staged code paths to review")
    contract, contract_error = guru_contract.load_contract(str(task_dir))
    if contract_error:
        raise GuruSupervisionError(f"SCOPE_INVALID:{contract_error}")
    if isinstance(contract, dict):
        problems = guru_contract.validate_commit_contract(contract, staged_paths, str(task_dir), str(root))
        if problems:
            raise GuruSupervisionError(f"SCOPE_INVALID:{'; '.join(problems[:5])}")
    code_paths = [
        path for path in staged_paths
        if not _guru_gate_is_task_artifact_path(path, str(task_dir), str(root))
    ]
    if not code_paths:
        raise GuruSupervisionError("SCOPE_INVALID:staged changes contain only task/workspace artifacts")
    packet = {
        "target_paths": code_paths,
        "deterministic_checks": ["git diff --cached --check"],
        "invariants": [
            {
                "invariant_id": "staged_scope_reviewed",
                "description": "The check worker reviewed the exact staged code paths against the task requirements, design, and implementation contract.",
            }
        ],
        "semantic_review_provider": {"provider": "opposite", "required": True},
    }
    try:
        reviewed_target_digest = guru_review_record.target_snapshot_digest(
            str(root), code_paths, "index"
        )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(f"SCOPE_INVALID:target snapshot digest failed:{exc}") from exc
    return ReviewTarget(
        unit_id="staged",
        review_target="staged:index",
        packet=packet,
        slice_packet_path=None,
        digest_source="index",
        active_brief=_active_review_brief(
            label="staged:index",
            review_target="staged:index",
            target_paths=code_paths,
            semantic_provider=packet["semantic_review_provider"],
            digest_source="index",
            invariants=packet.get("invariants", []),
            reviewed_target_digest=reviewed_target_digest,
        ),
        reviewed_target_digest=reviewed_target_digest,
    )


def _append_supervisor_review_record(
    *,
    task_dir: Path,
    root: Path,
    target: ReviewTarget,
    run_id: str,
    config: SupervisionConfig,
    resolution: ReviewProviderResolution,
    check_plan: RunPlan,
    messages: str,
    det_status: str,
    det_results: list,
    deterministic_evidence_key: str = "",
    expected_evidence_components: dict | None = None,
    platform: str | None = None,
    provider: str | None = None,
    trellis_bin: str | None = None,
    same_provider_user_quote: str | None = None,
) -> tuple[dict, str | None]:
    verdict = guru_review_record.parse_verdict_block(messages)
    try:
        current_target_digest = guru_review_record.target_snapshot_digest(
            str(root), target.packet.get("target_paths", []), target.digest_source
        )
    except guru_review_record.ReviewRecordError as exc:
        guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
            "SCOPE_INVALID", run_id, unit_id=target.unit_id))
        raise GuruSupervisionError(f"target snapshot digest failed,硬停(SCOPE_INVALID):{exc}") from exc
    reviewed_target_digest = target.reviewed_target_digest or current_target_digest
    if current_target_digest != reviewed_target_digest:
        guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
            "SCOPE_INVALID", run_id, unit_id=target.unit_id))
        raise GuruSupervisionError(
            "target snapshot changed during implementation-review,硬停(SCOPE_INVALID)"
        )
    aggregate_context = {}
    if target.review_target.startswith("aggregate:"):
        aggregate_record = _implementation_review_policy_record(config, resolution)
        aggregate_record["deterministic_results"] = det_results
        try:
            per_components = guru_review_record.aggregate_per_slice_components(
                str(task_dir),
                target.packet,
                aggregate_record,
                supervisor_path=str(Path(__file__).resolve()),
            )
            per_target_digests = target.packet["per_slice_target_digests"]
            per_keys = {
                slice_id: guru_review_record.review_evidence_key(
                    per_target_digests[slice_id],
                    per_components[slice_id],
                )
                for slice_id in target.packet["aggregate_slice_ids"]
            }
        except (KeyError, guru_review_record.ReviewRecordError) as exc:
            raise GuruSupervisionError(
                f"aggregate review component maps invalid:{exc}"
            ) from exc
        aggregate_context = {
            "aggregate_slice_ids": target.packet["aggregate_slice_ids"],
            "reviewed_staged_paths": target.packet["reviewed_staged_paths"],
            "aggregate_target_digest": target.reviewed_target_digest,
            "per_slice_target_paths": target.packet["per_slice_target_paths"],
            "per_slice_target_digests": per_target_digests,
            "per_slice_requirements_design_digests": target.packet[
                "per_slice_requirements_design_digests"
            ],
            "per_slice_component_digests": per_components,
            "per_slice_evidence_keys": per_keys,
        }
    record, failure = guru_review_record.normalize_review_record(verdict, {
        "mode": "supervisor", "packet": target.packet, "implement_provider": config.provider,
        "supervisor_deterministic_status": det_status, "deterministic_results": det_results,
        "run_id": run_id, "slice_id": target.unit_id,
        "review_target": target.review_target, "target_paths": target.packet.get("target_paths", []),
        "channel": check_plan.channel, "worker": check_plan.worker,
        "check_provider": resolution.check_config.provider,
        "provider_override_source": resolution.provider_override_source,
        "same_provider_user_quote": resolution.same_provider_user_quote,
        "high_risk_review_provider_policy": config.high_risk_review_provider_policy,
        "review_target_kind": resolution.review_target_kind,
        "reviewed_target_digest": reviewed_target_digest,
        "evidence_key": deterministic_evidence_key,
        "deterministic_evidence_key": deterministic_evidence_key,
        guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD: (
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
            if deterministic_evidence_key
            else None
        ),
        "supervisor_successful_commands": [
            result["command"]
            for result in det_results
            if result.get("exit_code") == 0
            and result.get("timed_out") is False
        ],
        **aggregate_context,
    })
    if resolution.same_provider_user_quote and failure is None:
        record["message"] = (
            "same-provider implementation-review authorized by user quote: "
            + resolution.same_provider_user_quote
        )
    if deterministic_evidence_key:
        if not isinstance(expected_evidence_components, dict):
            raise GuruSupervisionError(
                "v2 implementation review requires expected evidence "
                "components before append"
            )
        _require_current_slice_evidence(
            task_dir=task_dir,
            root=root,
            target=target,
            evidence_key=deterministic_evidence_key,
            evidence_components=expected_evidence_components,
            deterministic_results=det_results,
            platform=platform,
            provider=provider,
            trellis_bin=trellis_bin,
            same_provider_user_quote=same_provider_user_quote,
        )
    try:
        guru_review_record.append_record(str(task_dir), record)
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(
            f"cannot append current implementation review evidence:{exc}"
        ) from exc
    return record, failure


def _implementation_review_policy_record(
    config: SupervisionConfig,
    resolution: ReviewProviderResolution,
) -> dict:
    return {
        "deterministic_results": [],
        "provider_override_source": resolution.provider_override_source,
        "same_provider_user_quote": resolution.same_provider_user_quote,
        "high_risk_review_provider_policy": (
            config.high_risk_review_provider_policy
        ),
        "review_target_kind": resolution.review_target_kind,
        "implement_provider": config.provider,
        "check_provider": resolution.check_config.provider,
        "review_provider": resolution.check_config.provider,
    }


def _implementation_review_evidence_key(
    task_dir: Path,
    target: ReviewTarget,
    config: SupervisionConfig,
    resolution: ReviewProviderResolution,
) -> tuple[str, dict]:
    components = guru_review_record.review_evidence_components(
        str(task_dir),
        target.packet,
        _implementation_review_policy_record(config, resolution),
        supervisor_path=str(Path(__file__).resolve()),
    )
    return (
        guru_review_record.review_evidence_key(
            target.reviewed_target_digest,
            components,
        ),
        components,
    )


def _require_current_slice_evidence(
    *,
    task_dir: Path,
    root: Path,
    target: ReviewTarget,
    evidence_key: str,
    evidence_components: dict,
    deterministic_results: list,
    platform: str | None,
    provider: str | None,
    trellis_bin: str | None,
    same_provider_user_quote: str | None,
) -> None:
    """Fail when any semantic input changed after the initial evidence key."""
    if target.unit_id is None:
        raise GuruSupervisionError(
            "implementation review evidence lifecycle requires a slice id"
        )
    aggregate_review = target.review_target.startswith("aggregate:")
    current_target = (
        _aggregate_review_target(
            task_dir,
            root,
            target.packet.get("aggregate_slice_ids", []),
        )
        if aggregate_review
        else _slice_review_target(
            task_dir,
            root,
            target.unit_id,
            staged=target.digest_source == "index",
        )
    )
    current_config = _load_config(
        root,
        platform=platform,
        provider=provider,
        adversarial=False,
        trellis_bin=trellis_bin,
    )
    try:
        independent_required, independent_reason = (
            guru_risk.implement_check_independent_required(
                str(task_dir),
                current_config.platform,
                str(root),
                unit_id=None if aggregate_review else current_target.unit_id,
            )
        )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(
            f"implementation review evidence is no longer current:{exc}"
        ) from exc
    current_resolution = _implementation_review_check_config(
        current_config,
        packet=current_target.packet,
        independent_required=independent_required,
        independent_reason=independent_reason,
        high_risk_policy_applies=_slice_uses_high_risk_review_policy(
            current_target.packet,
            task_dir,
        ),
        review_target_kind="aggregate" if aggregate_review else "slice",
        same_provider_user_quote=same_provider_user_quote,
    )
    policy_record = _implementation_review_policy_record(
        current_config,
        current_resolution,
    )
    policy_record["deterministic_results"] = deterministic_results
    try:
        current_components = guru_review_record.review_evidence_components(
            str(task_dir),
            current_target.packet,
            policy_record,
            supervisor_path=str(Path(__file__).resolve()),
        )
        current_key = guru_review_record.review_evidence_key(
            current_target.reviewed_target_digest,
            current_components,
        )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(
            f"implementation review evidence is no longer current:{exc}"
        ) from exc
    if (
        current_key != evidence_key
        or current_components != evidence_components
    ):
        raise GuruSupervisionError(
            "implementation review semantic inputs changed after initial "
            "evidence key; rerun the slice review"
        )


def _slice_evidence_lifecycle_enabled(target: ReviewTarget) -> bool:
    return (
        (
            (
                target.review_target.startswith("slice:")
                and target.slice_packet_path is not None
            )
            or target.review_target.startswith("aggregate:")
        )
        and target.packet.get(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
            1,
        )
        == guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
    )


def _reusable_clean_review(
    task_dir: Path,
    target: ReviewTarget,
    evidence_key: str,
) -> dict | None:
    path = task_dir / "review-records" / "implementation-reviews.jsonl"
    if not path.is_file():
        return None
    latest_attempt = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise GuruSupervisionError(
            f"cannot read implementation review evidence:{exc}"
        ) from exc
    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GuruSupervisionError(
                f"implementation review evidence line {lineno} invalid JSON:{exc}"
            ) from exc
        if not isinstance(record, dict):
            raise GuruSupervisionError(
                f"implementation review evidence line {lineno} must be object"
            )
        if (
            record.get("evidence_key") == evidence_key
            and record.get("supplemental") is not True
        ):
            latest_attempt = record
    if latest_attempt is None:
        return None
    record = latest_attempt
    if (
        record.get("slice_id") != target.unit_id
        or record.get("review_target") != target.review_target
        or record.get("review_result") != "clean"
        or record.get("required_satisfied") is not True
        or record.get("supervisor_failure", "none") != "none"
        or guru_review_record.validate_verdict_values(record) is not None
        or record.get("deterministic_evidence_key") != evidence_key
    ):
        return None
    try:
        invariant_verdicts = (
            guru_review_record.validate_persisted_invariant_verdicts(
                target.packet.get("invariants"),
                record.get("invariant_verdicts"),
                require_all_pass=True,
            )
        )
        if (
            guru_review_record.aggregate_invariant_coverage(
                target.packet.get("invariants"),
                invariant_verdicts,
            )
            != record.get("invariant_coverage")
        ):
            return None
        if (
            record.get("invariant_verdicts_digest")
            != guru_review_record.invariant_verdicts_digest(
                invariant_verdicts
            )
        ):
            return None
        components = guru_review_record.review_evidence_components(
            str(task_dir),
            target.packet,
            record,
            supervisor_path=str(Path(__file__).resolve()),
        )
        current_key = guru_review_record.review_evidence_key(
            target.reviewed_target_digest,
            components,
        )
    except guru_review_record.ReviewRecordError:
        return None
    persisted_fields = (
        "target_paths_digest",
        "invariant_set_digest",
        "requirements_design_digest",
        "deterministic_commands_digest",
        "deterministic_results_digest",
        "review_policy_digest",
        "supervisor_source_digest",
    )
    if current_key != evidence_key or not all(
        record.get(field) == components[field]
        for field in persisted_fields
    ):
        return None
    try:
        deterministic = guru_review_record.load_deterministic_evidence(
            str(task_dir),
            evidence_key,
        )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(
            f"deterministic evidence referenced by clean review is invalid:{exc}"
        ) from exc
    if deterministic is None:
        return None
    if deterministic["status"] != "passed":
        raise GuruSupervisionError(
            "clean implementation review references failed deterministic evidence"
        )
    if (
        deterministic["deterministic_commands_digest"]
        != components["deterministic_commands_digest"]
        or deterministic["deterministic_results_digest"]
        != components["deterministic_results_digest"]
        or deterministic["results"] != record.get("deterministic_results")
    ):
        raise GuruSupervisionError(
            "clean implementation review deterministic cache binding mismatch"
        )
    return record


def _append_reused_clean_review(
    task_dir: Path,
    target: ReviewTarget,
    source_record: dict,
    review_run_id: str,
    evidence_key: str,
) -> dict:
    try:
        deterministic = guru_review_record.load_deterministic_evidence(
            str(task_dir),
            evidence_key,
        )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(
            f"cannot append clean reuse row from invalid deterministic evidence:{exc}"
        ) from exc
    if deterministic is None or deterministic.get("status") != "passed":
        raise GuruSupervisionError(
            "cannot append clean reuse row without current passed deterministic evidence"
        )
    reused = dict(source_record)
    reused.update(
        {
            "run_id": review_run_id,
            "slice_id": target.unit_id,
            "review_target": target.review_target,
            "target_paths": target.packet.get("target_paths", []),
            "reviewed_target_digest": target.reviewed_target_digest,
            "deterministic_results": deterministic["results"],
            "deterministic_evidence_key": evidence_key,
            "channel": "evidence-cache",
            "worker": "semantic-review-reuse",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": (
                "validated clean semantic evidence reused; "
                f"reused_from_run_id={source_record.get('run_id')}; "
                f"deterministic_evidence_key={evidence_key}; "
                "deterministic_runs=0; reviewers_spawned=0"
            ),
        }
    )
    try:
        guru_review_record.append_record(
            str(task_dir),
            guru_review_record._normalized_reuse_record(reused),
        )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(
            f"cannot append official clean reuse review row:{exc}"
        ) from exc
    return reused


def _resolve_slice_deterministic_evidence(
    task_dir: Path,
    root: Path,
    target: ReviewTarget,
    review_run_id: str,
    evidence_key: str,
    evidence_components: dict,
) -> tuple[dict | None, str, list, bool, dict]:
    def current_target_digest() -> str:
        try:
            return guru_review_record.target_snapshot_digest(
                str(root),
                target.packet.get("target_paths", []),
                target.digest_source,
            )
        except guru_review_record.ReviewRecordError as exc:
            raise GuruSupervisionError(
                f"SCOPE_INVALID:target snapshot digest failed:{exc}"
            ) from exc

    try:
        lock = guru_review_record.DeterministicEvidenceLock(
            str(task_dir),
            evidence_key,
        )
        with lock:
            if current_target_digest() != target.reviewed_target_digest:
                raise GuruSupervisionError(
                    "SCOPE_INVALID:implementation-review target changed "
                    "before deterministic evidence lookup"
                )
            clean_record = _reusable_clean_review(
                task_dir,
                target,
                evidence_key,
            )
            if clean_record is not None:
                deterministic = guru_review_record.load_deterministic_evidence(
                    str(task_dir),
                    evidence_key,
                )
                if deterministic is None:
                    raise GuruSupervisionError(
                        "clean review deterministic evidence disappeared"
                    )
                return (
                    clean_record,
                    "passed",
                    deterministic["results"],
                    True,
                    {
                        **evidence_components,
                        "deterministic_results_digest": deterministic[
                            "deterministic_results_digest"
                        ],
                    },
                )
            cached = guru_review_record.load_deterministic_evidence(
                str(task_dir),
                evidence_key,
            )
            deterministic_reused = cached is not None
            if cached is not None:
                if (
                    cached["deterministic_commands_digest"]
                    != evidence_components["deterministic_commands_digest"]
                ):
                    raise GuruSupervisionError(
                        "deterministic evidence command binding does not "
                        "match current evidence key"
                    )
                det_status = cached["status"]
                det_results = cached["results"]
            else:
                commands = guru_review_record.stable_unique_commands(
                    target.packet.get("deterministic_checks", [])
                )
                det_status, det_results = (
                    guru_review_record.run_deterministic_checks(
                        commands,
                        str(root),
                    )
                )
                if current_target_digest() != target.reviewed_target_digest:
                    raise GuruSupervisionError(
                        "SCOPE_INVALID:implementation-review target changed "
                        "during deterministic checks"
                    )
                deterministic_record = (
                    guru_review_record.deterministic_evidence_record(
                        evidence_key,
                        commands,
                        det_status,
                        det_results,
                    )
                )
                guru_review_record.append_deterministic_evidence(
                    str(task_dir),
                    deterministic_record,
                )
            if det_status == "passed":
                if current_target_digest() != target.reviewed_target_digest:
                    raise GuruSupervisionError(
                        "SCOPE_INVALID:implementation-review target changed "
                        "during deterministic checks"
                    )
            current_components = dict(evidence_components)
            current_components["deterministic_results_digest"] = (
                guru_review_record.deterministic_results_digest(det_results)
            )
            return (
                None,
                det_status,
                det_results,
                deterministic_reused,
                current_components,
            )
    except guru_review_record.ReviewRecordError as exc:
        raise GuruSupervisionError(
            f"deterministic evidence lifecycle invalid:{exc}"
        ) from exc


def _deterministic_reviewer_brief(
    evidence_key: str,
    results: list,
    *,
    reused: bool,
) -> str:
    successful_commands = [
        result["command"]
        for result in results
        if result.get("exit_code") == 0
        and result.get("timed_out") is False
    ]
    max_payload_chars = 10000
    bounded_results = []
    truncated = False
    for result in results:
        candidate = [*bounded_results, result]
        encoded = json.dumps(
            candidate,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if len(encoded) > max_payload_chars:
            truncated = True
            break
        bounded_results = candidate
    payload = {
        "evidence_key": evidence_key,
        "reused": reused,
        "results": bounded_results,
        "results_digest": guru_review_record.deterministic_results_digest(
            results
        ),
        "result_count": len(results),
        "included_result_count": len(bounded_results),
        "truncated": truncated,
    }
    included_commands = successful_commands[:len(bounded_results)]
    brief = (
        "Supervisor deterministic evidence follows. Treat these results as "
        "authoritative for this exact evidence key. Do not rerun any exact "
        "command from the packet deterministic_checks: semantic review starts "
        "only after all of them passed. You may run a distinct read-only "
        "adversarial probe; report each one as "
        "reviewer_probe_command.N=<exact command>. Any repeated successful "
        "command invalidates a clean verdict.\n"
        f"supervisor_successful_commands={json.dumps(included_commands, ensure_ascii=False)}\n"
        f"supervisor_deterministic_evidence_truncated={str(truncated).lower()}\n"
        "supervisor_deterministic_evidence="
        + json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    if len(brief) <= DETERMINISTIC_REVIEW_BRIEF_MAX_CHARS:
        return brief
    payload["results"] = []
    payload["included_result_count"] = 0
    payload["truncated"] = True
    return (
        "Supervisor deterministic evidence follows. All packet deterministic "
        "commands passed; do not rerun them. Distinct read-only probes are "
        "allowed and must be reported as reviewer_probe_command.N=<exact "
        "command>.\n"
        "supervisor_successful_commands=[]\n"
        "supervisor_deterministic_evidence_truncated=true\n"
        "supervisor_deterministic_evidence="
        + json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def _focused_requirements_design_context(
    task_dir: Path,
    manifest: list,
) -> list[dict]:
    guru_review_record.requirements_design_digest(str(task_dir), manifest)
    task_root = task_dir.resolve()
    remaining = FOCUSED_REQUIREMENTS_CONTEXT_MAX_CHARS
    selected = []
    for entry in manifest:
        rel = guru_review_record._clean_target_paths([entry["path"]])[0]
        path = (task_root / rel).resolve()
        if path != task_root and task_root not in path.parents:
            raise GuruSupervisionError(
                f"focused requirements/design path escapes task root:{rel}"
            )
        heading = entry.get("heading")
        if isinstance(heading, str) and heading.strip():
            selector = f"heading:{heading.strip()}"
            content = guru_review_record._markdown_section_bytes(
                str(path), heading.strip()
            )
        else:
            selector = "whole_file"
            try:
                content = path.read_bytes()
            except OSError as exc:
                raise GuruSupervisionError(
                    f"cannot read focused requirements/design input:{path}:{exc}"
                ) from exc
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GuruSupervisionError(
                f"focused requirements/design input is not UTF-8:{path}:{exc}"
            ) from exc
        limit = min(FOCUSED_REQUIREMENT_ITEM_MAX_CHARS, remaining)
        exact = len(text) <= limit
        if exact:
            rendered = text
        elif limit >= 64:
            head = max(32, (limit * 3) // 4)
            tail = max(16, limit - head - 24)
            rendered = text[:head] + "\n...[bounded]...\n" + text[-tail:]
        else:
            rendered = ""
        remaining = max(0, remaining - len(rendered))
        selected.append(
            {
                "path": rel,
                "selector": selector,
                "content_kind": "exact" if exact else "bounded_excerpt",
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_bytes": len(content),
                "content": rendered,
            }
        )
    return selected


def _focused_dependency_receipts(task_dir: Path, packet: dict) -> list[dict]:
    aggregate_ids = packet.get("aggregate_slice_ids")
    selected_ids = set(aggregate_ids if isinstance(aggregate_ids, list) else [])
    packets = (
        [
            guru_review_record.load_packet(str(task_dir), slice_id)
            for slice_id in aggregate_ids
        ]
        if selected_ids
        else [packet]
    )
    latest = {
        receipt["slice_id"]: receipt
        for receipt in guru_review_record.receipt_records(str(task_dir))
    }
    summary = []
    for owner in packets:
        for dependency in owner.get("depends_on") or []:
            receipt = latest.get(dependency)
            row = {
                "slice_id": owner.get("slice_id"),
                "depends_on": dependency,
            }
            if isinstance(receipt, dict):
                row.update(
                    {
                        "state": "receipt_present",
                        "commit_sha": receipt.get("commit_sha"),
                        "receipt_id": receipt.get("receipt_id"),
                        "review_run_id": receipt.get("review_run_id"),
                    }
                )
            elif dependency in selected_ids:
                row["state"] = "same_aggregate_pending"
            else:
                row["state"] = "receipt_missing"
            summary.append(row)
    return summary


def _focused_staged_diff(root: Path, target_paths: list) -> str:
    try:
        result = subprocess.run(
            [
                "git",
                "--literal-pathspecs",
                "diff",
                "--cached",
                "--binary",
                "--no-ext-diff",
                "--",
                *target_paths,
            ],
            cwd=root,
            capture_output=True,
            text=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GuruSupervisionError(
            f"cannot build focused staged diff:{exc}"
        ) from exc
    if result.returncode != 0:
        message = (result.stderr or result.stdout or b"").decode(
            "utf-8", errors="replace"
        ).strip()
        raise GuruSupervisionError(f"cannot build focused staged diff:{message}")
    return result.stdout.decode("utf-8", errors="replace")


def _focused_review_context_payload(
    task_dir: Path,
    root: Path,
    target: ReviewTarget,
    evidence_components: dict,
    deterministic_results: list,
) -> dict:
    packet_fields = (
        "schema_version",
        guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
        "slice_id",
        "aggregate_slice_ids",
        "target_paths",
        "reviewed_staged_paths",
        "risk",
        "risk_reasons",
        "depends_on",
        "requirements_design_inputs",
        "deterministic_checks",
        "semantic_review_provider",
        "invariants",
        "per_slice_target_paths",
    )
    deterministic_summary = [
        {
            "command": result.get("command"),
            "exit_code": result.get("exit_code"),
            "timed_out": result.get("timed_out"),
            "duration_ms": result.get("duration_ms"),
            "stdout_summary": str(result.get("stdout_summary", ""))[:1000],
            "stderr_summary": str(result.get("stderr_summary", ""))[:1000],
        }
        for result in deterministic_results
        if isinstance(result, dict)
    ]
    return {
        "schema_version": 1,
        "review_target": target.review_target,
        "reviewed_target_digest": target.reviewed_target_digest,
        "target_paths": target.packet.get("target_paths", []),
        "exact_staged_diff": _focused_staged_diff(
            root, target.packet.get("target_paths", [])
        ),
        "invariants": target.packet.get("invariants", []),
        "selected_requirements_design": (
            _focused_requirements_design_context(
                task_dir,
                target.packet.get("requirements_design_inputs", []),
            )
        ),
        "component_digests": evidence_components,
        "deterministic_results": deterministic_summary,
        "deterministic_results_digest": (
            guru_review_record.deterministic_results_digest(
                deterministic_results
            )
        ),
        "dependency_receipts": _focused_dependency_receipts(
            task_dir, target.packet
        ),
        "packet_manifest": {
            field: target.packet[field]
            for field in packet_fields
            if field in target.packet
        },
        "reviewer_may_run_distinct_read_only_probes": True,
    }


def _review_read_only_snapshot(root: Path) -> str:
    """Bind HEAD, index, tracked edits, and untracked bytes around the reviewer."""
    h = hashlib.sha256()
    h.update(b"guru-review-read-only-snapshot-v1\0")
    commands = (
        ["rev-parse", "--verify", "HEAD^{commit}"],
        ["ls-files", "--stage", "-z"],
        ["diff", "--binary", "--no-ext-diff"],
        [
            "for-each-ref",
            "--sort=refname",
            "--format=%(refname)%00%(objectname)%00%(objecttype)%00%(symref)",
        ],
        ["ls-files", "--others", "--exclude-standard", "-z"],
    )
    outputs = []
    for args in commands:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=root,
                capture_output=True,
                text=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GuruSupervisionError(
                f"cannot snapshot reviewer read-only boundary:{exc}"
            ) from exc
        if args[0] == "for-each-ref" and (
            result.returncode != 0 or result.stderr
        ):
            message = (result.stderr or result.stdout or b"").decode(
                "utf-8",
                errors="replace",
            ).strip()
            raise GuruSupervisionError(
                f"cannot snapshot reviewer read-only boundary:{message}"
            )
        output = result.stdout
        if args[0] == "for-each-ref":
            # Codex creates these observation refs outside the reviewer process.
            # Product/history refs remain bound by the snapshot.
            output = b"".join(
                line
                for line in output.splitlines(keepends=True)
                if not line.startswith(b"refs/codex/turn-diffs/")
            )
        if result.returncode != 0 and args == [
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
        ]:
            try:
                symbolic_head = subprocess.run(
                    ["git", "symbolic-ref", "-q", "HEAD"],
                    cwd=root,
                    capture_output=True,
                    text=False,
                    timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise GuruSupervisionError(
                    f"cannot snapshot reviewer read-only boundary:{exc}"
                ) from exc
            if symbolic_head.returncode != 0:
                message = (result.stderr or result.stdout or b"").decode(
                    "utf-8",
                    errors="replace",
                ).strip()
                raise GuruSupervisionError(
                    f"cannot snapshot reviewer read-only boundary:{message}"
                )
            head_ref = symbolic_head.stdout.strip()
            if not head_ref:
                raise GuruSupervisionError(
                    "cannot snapshot reviewer read-only boundary:empty HEAD ref"
                )
            try:
                ref_state = subprocess.run(
                    [
                        "git",
                        "show-ref",
                        "--verify",
                        "--quiet",
                        head_ref.decode("utf-8", errors="surrogateescape"),
                    ],
                    cwd=root,
                    capture_output=True,
                    text=False,
                    timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise GuruSupervisionError(
                    f"cannot snapshot reviewer read-only boundary:{exc}"
                ) from exc
            if ref_state.returncode == 1:
                try:
                    git_path = subprocess.run(
                        [
                            "git",
                            "rev-parse",
                            "--git-path",
                            head_ref.decode("utf-8", errors="surrogateescape"),
                        ],
                        cwd=root,
                        capture_output=True,
                        text=False,
                        timeout=30,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise GuruSupervisionError(
                        f"cannot snapshot reviewer read-only boundary:{exc}"
                    ) from exc
                path_lines = git_path.stdout.splitlines()
                if (
                    git_path.returncode != 0
                    or len(path_lines) != 1
                    or not path_lines[0]
                ):
                    message = (
                        git_path.stderr
                        or git_path.stdout
                        or b"cannot resolve exact HEAD ref path"
                    ).decode("utf-8", errors="replace").strip()
                    raise GuruSupervisionError(
                        f"cannot snapshot reviewer read-only boundary:{message}"
                    )
                loose_ref_path = Path(
                    path_lines[0].decode("utf-8", errors="surrogateescape")
                )
                if not loose_ref_path.is_absolute():
                    loose_ref_path = root / loose_ref_path
                if os.path.lexists(loose_ref_path):
                    raise GuruSupervisionError(
                        "cannot snapshot reviewer read-only boundary:"
                        "unresolved HEAD loose ref exists"
                    )
                output = b"unborn\0" + symbolic_head.stdout
            else:
                message = (
                    ref_state.stderr
                    or ref_state.stdout
                    or b"HEAD ref exists but does not resolve to a commit"
                ).decode("utf-8", errors="replace").strip()
                raise GuruSupervisionError(
                    f"cannot snapshot reviewer read-only boundary:{message}"
                )
        elif result.returncode == 0 and args == [
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
        ]:
            try:
                symbolic_head = subprocess.run(
                    ["git", "symbolic-ref", "-q", "HEAD"],
                    cwd=root,
                    capture_output=True,
                    text=False,
                    timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise GuruSupervisionError(
                    f"cannot snapshot reviewer read-only boundary:{exc}"
                ) from exc
            symbolic_lines = symbolic_head.stdout.splitlines()
            if (
                symbolic_head.returncode == 0
                and len(symbolic_lines) == 1
                and symbolic_lines[0]
            ):
                output = b"symbolic\0" + symbolic_lines[0] + b"\0" + result.stdout
            elif (
                symbolic_head.returncode == 1
                and not symbolic_head.stdout
                and not symbolic_head.stderr
            ):
                output = b"detached\0" + result.stdout
            else:
                message = (
                    symbolic_head.stderr
                    or symbolic_head.stdout
                    or b"cannot classify canonical HEAD identity"
                ).decode("utf-8", errors="replace").strip()
                raise GuruSupervisionError(
                    f"cannot snapshot reviewer read-only boundary:{message}"
                )
        elif result.returncode != 0:
            message = (result.stderr or result.stdout or b"").decode(
                "utf-8",
                errors="replace",
            ).strip()
            raise GuruSupervisionError(
                f"cannot snapshot reviewer read-only boundary:{message}"
            )
        outputs.append(output)
        h.update(len(output).to_bytes(8, "big"))
        h.update(output)
    for raw_path in outputs[-1].split(b"\0"):
        if not raw_path:
            continue
        rel = raw_path.decode("utf-8", errors="surrogateescape")
        path = root / rel
        h.update(len(raw_path).to_bytes(8, "big"))
        h.update(raw_path)
        try:
            if path.is_symlink():
                data = os.readlink(path).encode(
                    "utf-8",
                    errors="surrogateescape",
                )
            else:
                data = path.read_bytes()
        except OSError as exc:
            raise GuruSupervisionError(
                f"cannot snapshot untracked reviewer path {rel}:{exc}"
            ) from exc
        h.update(len(data).to_bytes(8, "big"))
        h.update(data)
    return h.hexdigest()


def _task_status(task_dir: Path) -> str:
    try:
        data = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "planning"
    status = data.get("status", "planning") if isinstance(data, dict) else "planning"
    return status if isinstance(status, str) and status else "planning"


def run_implement_check(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
    base_run_id = args.run_id or _default_run_id()
    if _task_status(task_dir) == "in_progress":
        required, reason = guru_risk.full_chain_packet_required(str(task_dir))
        if required and not guru_review_record.list_packets(str(task_dir)):
            guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
                "PACKET_REQUIRED_BEFORE_IMPLEMENT", f"{base_run_id}-check-1"))
            sys.stderr.write(
                "[guru-supervise] high-risk full_chain requires slice packet before worker launch; "
                f"硬停(PACKET_REQUIRED_BEFORE_IMPLEMENT):{reason}\n"
            )
            return 2
    if _guru_gate_check_implementation(str(task_dir)) != 0:
        print(
            "[guru-supervise] BLOCKED: implement-check requires "
            "task.json.status == in_progress. Run task.py start after START_READY.",
            file=sys.stderr,
        )
        return 2
    # implement-check 内部**强制 non-advisory 且不翻转 provider**：忽略外部全局 `--adversarial`
    # （parser 顶层 flag，对 implement-check 同样可传）。否则 _load_config(adversarial=True) 会先把
    # provider 翻成 opposite(current_provider)，使 implement 错用对立 provider；且 _execute_plan 在
    # worker 失败/terminal≠done 时走 _skip_adversarial 返 rc0，把③对立-provider check 失败降级成不
    # 阻断。强制 adversarial=False ⇒ provider=args.provider（不翻转）、check 失败 rc≠0 真阻断；
    # 独立 check 的 provider 隔离由下方 ③ 自管。
    config = _load_config(
        root,
        platform=args.platform,
        provider=args.provider,
        adversarial=False,
        trellis_bin=args.trellis_bin,
    )
    # P1b：resolve slice packet(--slice 显式 / 单 packet auto / 多 packet 未指定→PACKET_AMBIGUOUS 硬停 /
    # 无 packet→None 回落 P0)。preflight failure 全经 preflight_failure_record + append_record + exit2,
    # 绝不进 REPAIRABLE_IMPLEMENT_ROUTES、不启 implement worker(repairable=false,BHV-001/002)。
    unit_id, ambiguous = _resolve_slice_packet(str(task_dir), getattr(args, "slice", None))
    if ambiguous:
        guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
            "PACKET_AMBIGUOUS", f"{base_run_id}-check-1", candidates=ambiguous))
        sys.stderr.write(f"[guru-supervise] 多 slice packet 未用 --slice 指定:{ambiguous};硬停(PACKET_AMBIGUOUS)\n")
        return 2

    # P1b：packet preflight(unit_id 有 packet → load 确认存在合法[区分 MISSING/INVALID] + scope preflight)——
    # **先于 risk 判定**,使缺失/非法在此正确分类(risk 判定的 slice_packet_risk 会重 load,届时已合法)。
    # fail-closed,全 exit2 不进 REPAIRABLE_IMPLEMENT_ROUTES、不启 worker(BHV-001/002)。
    packet = None
    if unit_id:
        try:
            packet = guru_review_record.load_packet(str(task_dir), unit_id)
        except guru_review_record.ReviewRecordError as exc:
            kind = "PACKET_MISSING" if "不存在" in str(exc) else "PACKET_INVALID"
            guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
                kind, f"{base_run_id}-check-1", unit_id=unit_id))
            sys.stderr.write(f"[guru-supervise] slice packet {kind},硬停:{exc}\n")
            return 2
        scope_failure = _scope_preflight(str(root), packet)
        if scope_failure:
            guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
                "SCOPE_INVALID", f"{base_run_id}-check-1", unit_id=unit_id))
            sys.stderr.write(f"[guru-supervise] scope invalid,硬停(SCOPE_INVALID):{scope_failure}\n")
            return 2

    # ③ P0/P1：风险判定决定是否需要独立阻断 check；只有有效 high-risk slice 的实际
    # provider 由项目 policy 决定，其他 slice 保留 packet provider 合同。
    try:
        independent_required, independent_reason = guru_risk.implement_check_independent_required(
            str(task_dir), config.platform, str(root), unit_id=unit_id
        )
    except guru_review_record.ReviewRecordError as exc:  # 防御:packet 已 preflight,正常不触发
        guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
            "PACKET_INVALID", f"{base_run_id}-check-1", unit_id=unit_id))
        sys.stderr.write(f"[guru-supervise] slice packet 非法,硬停(PACKET_INVALID):{exc}\n")
        return 2

    resolution = _implementation_review_check_config(
        config,
        packet=packet,
        independent_required=independent_required,
        independent_reason=independent_reason,
        high_risk_policy_applies=_slice_uses_high_risk_review_policy(packet, task_dir),
        review_target_kind="slice" if packet is not None else "staged",
    )
    check_config = resolution.check_config
    _report_review_provider_resolution(config, resolution)

    # P1c R4-F2：有 packet 时注入到 worker（artifact --file + brief active_slice），worker 才能逐条
    # invariant、输出正确 review_target/provider。无 packet → slice_packet_path=None（P0 旧路径）。
    slice_packet_path = (task_dir / "slice-packets" / f"{unit_id}.json") if unit_id else None
    active_slice_brief = ""
    if packet is not None:
        slice_id = str(unit_id)
        packet_target_paths = packet.get("target_paths", [])
        if not isinstance(packet_target_paths, list):
            packet_target_paths = []
        packet_semantic_provider = packet.get("semantic_review_provider", {})
        if not isinstance(packet_semantic_provider, dict):
            packet_semantic_provider = {}
        active_slice_brief = _active_review_brief(
            label=slice_id,
            review_target=f"slice:{slice_id}",
            target_paths=packet_target_paths,
            semantic_provider=packet_semantic_provider,
            digest_source="worktree",
            invariants=packet.get("invariants", []),
            slice_packet_path=slice_packet_path,
        )

    if args.dry_run:
        implement_plan = build_run_plan(
            "implement",
            task_dir,
            config,
            f"{base_run_id}-implement-1",
            "Implement-check loop step 1/2: apply implementation fixes from the previous check context when present." + active_slice_brief,
            slice_packet_path=slice_packet_path,
        )
        check_plan = build_run_plan(
            "check",
            task_dir,
            check_config,
            f"{base_run_id}-check-1",
            "Implement-check loop step 2/2: emit review_result=clean/final-verification-ready with route_class=none, or route_class=<defect>." + active_slice_brief,
            slice_packet_path=slice_packet_path,
        )
        print("IMPLEMENT-CHECK LOOP")
        print("repeat: implement -> check -> route")
        print(
            "routes: IMPLEMENT_DEFECT/PROCESS_DEFECT repeat implement; "
            "DETAIL_DEFECT -> detail; OVERVIEW_DEFECT -> overview; REQ_BLOCKER -> requirements"
        )
        print(
            "clean: review_result=clean/final-verification-ready route_class=none; "
            "reviewed diff/artifact context; validation_summary; final validation plus hard boundary stop"
        )
        print("Do not create implementation guru_gates")
        print("")
        _print_dry_run(implement_plan)
        print("")
        _print_dry_run(check_plan)
        return 0

    review_context = ""
    for iteration in range(1, DEFAULT_IMPLEMENT_CHECK_MAX_LOOPS + 1):
        extra = (
            "Previous implementation check finding context:\n"
            + _clip_context(review_context)
            if review_context
            else ""
        )
        implement_plan = build_run_plan(
            "implement",
            task_dir,
            config,
            f"{base_run_id}-implement-{iteration}",
            extra + active_slice_brief,
            slice_packet_path=slice_packet_path,
        )
        rc, _terminal, _messages = _execute_plan(implement_plan, config)
        if rc != 0:
            return rc

        # P1c R4-F1：有 packet → 每轮 implement 成功后 supervisor 执行 deterministic_checks（绑定本轮 diff,不复用过期）
        det_status, det_results = ("missing", [])
        if packet is not None:
            det_status, det_results = guru_review_record.run_deterministic_checks(
                packet.get("deterministic_checks", []), str(root)
            )

        check_plan = build_run_plan(
            "check",
            task_dir,
            check_config,
            f"{base_run_id}-check-{iteration}",
            "Emit exactly one route_class and review_result for implement-check routing." + active_slice_brief,
            slice_packet_path=slice_packet_path,
        )
        rc, _terminal, messages = _execute_plan(check_plan, check_config)
        if rc != 0:
            return rc

        if packet is not None:
            # P1c 结构化 verdict gating（有 packet）：parse + normalize（单一入口,层①取值 + 层②provider/
            # deterministic 双过/聚合重算）+ append（单一 writer）。malformed/不通过 → 硬停 exit2。
            try:
                record, failure = _append_supervisor_review_record(
                    task_dir=task_dir,
                    root=root,
                    target=ReviewTarget(
                        unit_id=unit_id,
                        review_target=f"slice:{unit_id}",
                        packet=packet,
                        slice_packet_path=slice_packet_path,
                        digest_source="worktree",
                        active_brief=active_slice_brief,
                    ),
                    run_id=f"{base_run_id}-check-{iteration}",
                    config=config,
                    resolution=resolution,
                    check_plan=check_plan,
                    messages=messages,
                    det_status=det_status,
                    det_results=det_results,
                )
            except GuruSupervisionError as exc:
                sys.stderr.write(f"[guru-supervise] {exc}\n")
                return 2
            if failure:
                sys.stderr.write(f"[guru-supervise] check verdict {failure}; 硬停(不空转修复审查格式)\n")
                return 2
            if record["review_result"] == "clean":
                print("[guru-supervise] implement-check clean（structured verdict）; stop at hard-boundary.")
                return 0
            if record.get("repairable"):
                review_context = messages
                continue
            if record["route_class"] in UPSTREAM_ROUTE_TARGETS:
                target = UPSTREAM_ROUTE_TARGETS[record["route_class"]]
                print(f"[guru-supervise] implement-check routed upstream: {record['route_class']} -> {target}")
                return 2
            sys.stderr.write(
                f"[guru-supervise] check {record['review_result']}/{record['route_class']}; cannot route safely\n"
            )
            return 2

        # 无 packet（P0 存量流程,过渡）：旧 _route_from_output 全文解析
        route = _route_from_output(messages)
        if route == "clean":
            print("[guru-supervise] implement-check clean; stop at hard-boundary confirmation.")
            return 0
        if route in REPAIRABLE_IMPLEMENT_ROUTES:
            review_context = messages
            continue
        if route in UPSTREAM_ROUTE_TARGETS:
            target = UPSTREAM_ROUTE_TARGETS[route]
            print(f"[guru-supervise] implement-check routed upstream: {route} -> {target}")
            return 2
        sys.stderr.write(
            "[guru-supervise] check output missing route_class or "
            "review_result=clean/final-verification-ready; cannot route safely\n"
        )
        return 2

    sys.stderr.write(
        f"[guru-supervise] implement-check stopped after {DEFAULT_IMPLEMENT_CHECK_MAX_LOOPS} "
        "repair loops; continue manually with the latest check findings\n"
    )
    return 1


def run_implementation_review(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
    base_run_id = args.run_id or _default_run_id()
    if _guru_gate_check_implementation(str(task_dir)) != 0:
        print(
            "[guru-supervise] BLOCKED: implementation-review requires "
            "task.json.status == in_progress. Run task.py start after START_READY.",
            file=sys.stderr,
        )
        return 2
    same_provider_quote = ""
    if getattr(args, "same_provider", False):
        same_provider_quote = str(getattr(args, "user_quote", "") or "").strip()
        if not same_provider_quote:
            sys.stderr.write(
                "[guru-supervise] --same-provider requires --user-quote for audit; "
                "do not skip opposite-provider review without explicit user authorization.\n"
            )
            return 2
    config = _load_config(
        root,
        platform=args.platform,
        provider=args.provider,
        adversarial=False,
        trellis_bin=args.trellis_bin,
    )
    raw_slices = getattr(args, "slice", None)
    slice_ids = (
        [raw_slices]
        if isinstance(raw_slices, str) and raw_slices.strip()
        else list(raw_slices or [])
    )
    slice_ids = [str(slice_id).strip() for slice_id in slice_ids if str(slice_id).strip()]
    aggregate_mode = bool(getattr(args, "aggregate", False))
    if aggregate_mode and (not bool(args.staged) or not slice_ids):
        sys.stderr.write(
            "[guru-supervise] --aggregate requires --staged and at least one explicit --slice\n"
        )
        return 2
    if not aggregate_mode and len(slice_ids) > 1:
        sys.stderr.write(
            "[guru-supervise] repeated --slice requires --aggregate\n"
        )
        return 2
    unit_id = slice_ids[0] if slice_ids else None
    record_unit_id = unit_id
    try:
        if aggregate_mode:
            target = _aggregate_review_target(task_dir, root, slice_ids)
        elif unit_id:
            target = _slice_review_target(task_dir, root, unit_id, staged=bool(args.staged))
        elif args.staged or args.contract:
            contract, contract_error = guru_contract.load_contract(str(task_dir))
            packet_ids = guru_review_record.list_packets(str(task_dir))
            lifecycle_packets = []
            for packet_id in packet_ids:
                try:
                    packet = guru_review_record.load_packet(str(task_dir), packet_id)
                except guru_review_record.ReviewRecordError as exc:
                    raise GuruSupervisionError(f"PACKET_INVALID:{exc}") from exc
                if (
                    packet.get(guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD, 1)
                    == guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
                ):
                    lifecycle_packets.append(packet_id)
            if lifecycle_packets and (
                contract_error or not isinstance(contract, dict)
            ):
                raise GuruSupervisionError(
                    "SCOPE_INVALID:schema-v2 staged fallback requires a valid "
                    f"route contract:{contract_error or 'gate-contract.json missing'}"
                )
            full_high_lifecycle = (
                isinstance(contract, dict)
                and guru_contract.contract_route(contract)
                == guru_contract.ROUTE_FULL_CHAIN
                and guru_contract.contract_risk(contract)
                in {guru_contract.RISK_HIGH, guru_contract.RISK_UNKNOWN}
            )
            if lifecycle_packets and full_high_lifecycle:
                raise GuruSupervisionError(
                    "PACKET_AMBIGUOUS:schema-v2 staged fallback requires "
                    "--aggregate with every explicit --slice; weak synthetic "
                    "staged_scope_reviewed is not valid"
                )
            target = _staged_review_target(task_dir, root)
        else:
            resolved_unit, ambiguous = _resolve_slice_packet(str(task_dir), None)
            if ambiguous:
                guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
                    "PACKET_AMBIGUOUS", f"{base_run_id}-review-1", candidates=ambiguous))
                sys.stderr.write(f"[guru-supervise] 多 slice packet 未用 --slice 指定:{ambiguous};硬停(PACKET_AMBIGUOUS)\n")
                return 2
            if not resolved_unit:
                sys.stderr.write("[guru-supervise] implementation-review requires --staged when no slice packet exists\n")
                return 2
            target = _slice_review_target(task_dir, root, resolved_unit, staged=False)
        record_unit_id = target.unit_id
        if (
            _slice_evidence_lifecycle_enabled(target)
            and target.digest_source != "index"
        ):
            raise GuruSupervisionError(
                "SCOPE_INVALID:schema-v2 slice implementation-review "
                "requires --staged"
            )
        if target.digest_source == "index":
            drift_failure = _staged_target_drift(str(root), target.packet.get("target_paths", []))
            if drift_failure:
                raise GuruSupervisionError(f"SCOPE_INVALID:{drift_failure}")
    except GuruSupervisionError as exc:
        kind = "SCOPE_INVALID"
        if str(exc).startswith("PACKET_MISSING:"):
            kind = "PACKET_MISSING"
        elif str(exc).startswith("PACKET_INVALID:"):
            kind = "PACKET_INVALID"
        elif str(exc).startswith("PACKET_AMBIGUOUS:"):
            kind = "PACKET_AMBIGUOUS"
        guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
            kind, f"{base_run_id}-review-1", unit_id=record_unit_id))
        sys.stderr.write(f"[guru-supervise] implementation-review preflight failed({kind}):{exc}\n")
        return 2

    try:
        independent_required, independent_reason = guru_risk.implement_check_independent_required(
            str(task_dir), config.platform, str(root), unit_id=(target.unit_id if target.review_target.startswith("slice:") else None)
        )
    except guru_review_record.ReviewRecordError as exc:
        guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
            "PACKET_INVALID", f"{base_run_id}-review-1", unit_id=target.unit_id))
        sys.stderr.write(f"[guru-supervise] implementation-review target invalid,硬停(PACKET_INVALID):{exc}\n")
        return 2

    review_target_kind = (
        "aggregate"
        if target.review_target.startswith("aggregate:")
        else ("slice" if target.review_target.startswith("slice:") else "staged")
    )
    resolution = _implementation_review_check_config(
        config,
        packet=target.packet,
        independent_required=independent_required,
        independent_reason=independent_reason,
        high_risk_policy_applies=_slice_uses_high_risk_review_policy(
            target.packet, task_dir
        ),
        review_target_kind=review_target_kind,
        same_provider_user_quote=same_provider_quote or None,
    )
    check_config = resolution.check_config
    _report_review_provider_resolution(config, resolution)
    review_run_id = f"{base_run_id}-review-1"
    det_status, det_results = "not_run", []
    deterministic_reused = False
    lifecycle_enabled = _slice_evidence_lifecycle_enabled(target)
    evidence_key = ""
    evidence_components = {}
    if lifecycle_enabled:
        try:
            evidence_key, evidence_components = (
                _implementation_review_evidence_key(
                    task_dir,
                    target,
                    config,
                    resolution,
                )
            )
        except guru_review_record.ReviewRecordError as exc:
            sys.stderr.write(
                f"[guru-supervise] implementation-review evidence key invalid:{exc}\n"
            )
            return 2
    elif not args.dry_run:
        det_status, det_results = guru_review_record.run_deterministic_checks(
            target.packet.get("deterministic_checks", []),
            str(root),
        )
        try:
            current_target_digest = guru_review_record.target_snapshot_digest(
                str(root),
                target.packet.get("target_paths", []),
                target.digest_source,
            )
        except guru_review_record.ReviewRecordError as exc:
            guru_review_record.append_record(
                str(task_dir),
                guru_review_record.preflight_failure_record(
                    "SCOPE_INVALID",
                    review_run_id,
                    unit_id=target.unit_id,
                ),
            )
            sys.stderr.write(
                "[guru-supervise] implementation-review target digest "
                f"failed(SCOPE_INVALID):{exc}\n"
            )
            return 2
        if current_target_digest != target.reviewed_target_digest:
            guru_review_record.append_record(
                str(task_dir),
                guru_review_record.preflight_failure_record(
                    "SCOPE_INVALID",
                    review_run_id,
                    unit_id=target.unit_id,
                ),
            )
            sys.stderr.write(
                "[guru-supervise] implementation-review target changed during "
                "deterministic checks; 硬停(SCOPE_INVALID)\n"
            )
            return 2
    if not args.dry_run and lifecycle_enabled:
        try:
            (
                reusable_clean_record,
                det_status,
                det_results,
                deterministic_reused,
                evidence_components,
            ) = _resolve_slice_deterministic_evidence(
                task_dir,
                root,
                target,
                review_run_id,
                evidence_key,
                evidence_components,
            )
        except GuruSupervisionError as exc:
            if str(exc).startswith("SCOPE_INVALID:"):
                guru_review_record.append_record(
                    str(task_dir),
                    guru_review_record.preflight_failure_record(
                        "SCOPE_INVALID",
                        review_run_id,
                        unit_id=target.unit_id,
                    ),
                )
            sys.stderr.write(f"[guru-supervise] {exc}\n")
            return 2
        if det_status != "passed":
            sys.stderr.write(
                "[guru-supervise] deterministic checks failed; semantic "
                f"reviewer not started (evidence_key={evidence_key}, "
                f"cached={str(deterministic_reused).lower()})\n"
            )
            return 2
        try:
            _require_current_slice_evidence(
                task_dir=task_dir,
                root=root,
                target=target,
                evidence_key=evidence_key,
                evidence_components=evidence_components,
                deterministic_results=det_results,
                platform=args.platform,
                provider=args.provider,
                trellis_bin=args.trellis_bin,
                same_provider_user_quote=same_provider_quote or None,
            )
        except GuruSupervisionError as exc:
            sys.stderr.write(f"[guru-supervise] {exc}\n")
            return 2
        if reusable_clean_record is not None:
            try:
                reused_record = _append_reused_clean_review(
                    task_dir,
                    target,
                    reusable_clean_record,
                    review_run_id,
                    evidence_key,
                )
            except GuruSupervisionError as exc:
                sys.stderr.write(f"[guru-supervise] {exc}\n")
                return 2
            print(
                "[guru-supervise] implementation-review clean evidence reused "
                f"(evidence_key={evidence_key}, "
                f"run_id={reused_record.get('run_id')}); "
                "deterministic_runs=0 reviewers_spawned=0"
            )
            return 0

    run_slug = _sanitize(review_run_id, limit=40)
    expected_channel = f"guru-{_sanitize(task_dir.name, limit=70)}-check-{run_slug}"
    expected_worker = f"check-{_sanitize(check_config.provider, limit=24)}-{run_slug}"
    supervisor_source = Path(__file__).resolve()
    try:
        supervisor_source_ref = supervisor_source.relative_to(root).as_posix()
    except ValueError:
        supervisor_source_ref = str(supervisor_source)
    invocation_contract = {
        "schema_version": 1,
        "action": "implementation-review",
        "review_mode": "check_only",
        "run_id": review_run_id,
        "channel": expected_channel,
        "worker": expected_worker,
        "supervisor_source": supervisor_source_ref,
        "supervisor_source_sha256": hashlib.sha256(supervisor_source.read_bytes()).hexdigest(),
        "slice_id": target.unit_id,
        "aggregate_slice_ids": target.packet.get("aggregate_slice_ids"),
        "review_target": target.review_target,
        "digest_source": target.digest_source,
        "reviewed_target_digest": target.reviewed_target_digest,
        "target_paths_sha256": hashlib.sha256(json.dumps(
            target.packet.get("target_paths", []), sort_keys=True,
            separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")).hexdigest(),
        "deterministic_status": det_status,
        "deterministic_results_sha256": (
            guru_review_record.deterministic_results_digest(det_results)
        ),
        "deterministic_evidence_key": evidence_key or None,
        "deterministic_evidence_reused": (
            deterministic_reused if lifecycle_enabled else None
        ),
        "evidence_components": (
            evidence_components if lifecycle_enabled else None
        ),
        "implement_provider": config.provider,
        "review_provider": check_config.provider,
        "check_provider": check_config.provider,
        "provider_override_source": resolution.provider_override_source,
        "same_provider_user_quote": resolution.same_provider_user_quote,
        "same_provider": resolution.provider_override_source == "cli_same_provider",
        "staged": target.digest_source == "index",
    }
    invocation_line = "review_invocation_contract=" + json.dumps(
        invocation_contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ) + "\n"
    deterministic_brief = (
        _deterministic_reviewer_brief(
            evidence_key,
            det_results,
            reused=deterministic_reused,
        )
        if lifecycle_enabled
        else ""
    )
    focused_context = (
        _focused_review_context_payload(
            task_dir,
            root,
            target,
            evidence_components,
            det_results,
        )
        if lifecycle_enabled
        else None
    )
    check_plan = build_run_plan(
        "implementation-review",
        task_dir,
        check_config,
        review_run_id,
        "Implementation-review check-only required evidence path. Do not implement or edit files; "
        "emit exactly one route_class and review_result for required commit evidence.\n"
        + invocation_line
        + deterministic_brief
        + target.active_brief,
        slice_packet_path=target.slice_packet_path,
        focused_review_context=focused_context,
    )

    if args.dry_run:
        print("IMPLEMENTATION-REVIEW CHECK-ONLY")
        print("run: deterministic checks -> check -> append structured record")
        print("no implement worker is launched")
        print("")
        _print_dry_run(check_plan)
        return 0

    try:
        read_only_before = _review_read_only_snapshot(root)
    except GuruSupervisionError as exc:
        guru_review_record.append_record(
            str(task_dir),
            guru_review_record.preflight_failure_record(
                "SCOPE_INVALID",
                review_run_id,
                unit_id=target.unit_id,
            ),
        )
        sys.stderr.write(f"[guru-supervise] {exc}\n")
        return 2
    rc, _terminal, messages = _execute_plan(check_plan, check_config)
    try:
        read_only_after = _review_read_only_snapshot(root)
    except GuruSupervisionError as exc:
        guru_review_record.append_record(
            str(task_dir),
            guru_review_record.preflight_failure_record(
                "SCOPE_INVALID",
                review_run_id,
                unit_id=target.unit_id,
            ),
        )
        sys.stderr.write(f"[guru-supervise] {exc}\n")
        return 2
    if read_only_after != read_only_before:
        guru_review_record.append_record(
            str(task_dir),
            guru_review_record.preflight_failure_record(
                "SCOPE_INVALID",
                review_run_id,
                unit_id=target.unit_id,
            ),
        )
        sys.stderr.write(
            "[guru-supervise] implementation reviewer changed repository, "
            "index, task artifact, or Git HEAD; 硬停(SCOPE_INVALID)\n"
        )
        return 2
    if rc != 0:
        if lifecycle_enabled:
            try:
                _append_supervisor_review_record(
                    task_dir=task_dir,
                    root=root,
                    target=target,
                    run_id=review_run_id,
                    config=config,
                    resolution=resolution,
                    check_plan=check_plan,
                    messages="",
                    det_status=det_status,
                    det_results=det_results,
                    deterministic_evidence_key=evidence_key,
                    expected_evidence_components=evidence_components,
                    platform=args.platform,
                    provider=args.provider,
                    trellis_bin=args.trellis_bin,
                    same_provider_user_quote=same_provider_quote or None,
                )
            except GuruSupervisionError as exc:
                sys.stderr.write(
                    "[guru-supervise] cannot record interrupted semantic "
                    f"attempt:{exc}\n"
                )
                return 2
        return rc
    try:
        record, failure = _append_supervisor_review_record(
            task_dir=task_dir,
            root=root,
            target=target,
            run_id=review_run_id,
            config=config,
            resolution=resolution,
            check_plan=check_plan,
            messages=messages,
            det_status=det_status,
            det_results=det_results,
            deterministic_evidence_key=evidence_key,
            expected_evidence_components=evidence_components,
            platform=args.platform,
            provider=args.provider,
            trellis_bin=args.trellis_bin,
            same_provider_user_quote=same_provider_quote or None,
        )
    except GuruSupervisionError as exc:
        sys.stderr.write(f"[guru-supervise] {exc}\n")
        return 2
    if failure:
        sys.stderr.write(f"[guru-supervise] implementation-review verdict {failure}; 硬停\n")
        return 2
    if record["review_result"] == "clean":
        print("[guru-supervise] implementation-review clean（structured verdict）; commit evidence ready.")
        return 0
    if record.get("route_class") in UPSTREAM_ROUTE_TARGETS:
        target_step = UPSTREAM_ROUTE_TARGETS[record["route_class"]]
        print(f"[guru-supervise] implementation-review routed upstream: {record['route_class']} -> {target_step}")
    else:
        print(f"[guru-supervise] implementation-review not clean: {record['review_result']}/{record['route_class']}")
    return 2


def _load_channel_events(config: SupervisionConfig, channel: str) -> list[dict]:
    result = subprocess.run(
        _trellis_cmd(
            config,
            ["channel", "messages", channel, "--raw", "--last", "200"],
        ),
        cwd=config.root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return []
    events: list[dict] = []
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _terminal_worker_name(event: dict) -> str:
    worker = str(event.get("worker") or "").strip()
    if worker:
        return worker
    by = str(event.get("by") or "").strip()
    if by.startswith("supervisor:"):
        return by.split(":", 1)[1].strip()
    if by.startswith("cli:"):
        return ""
    return by


def status_action(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
    config = _load_config(
        root,
        platform=args.platform,
        provider=args.provider,
        adversarial=args.adversarial,
        trellis_bin=args.trellis_bin,
    )
    task_slug = _sanitize(task_dir.name, limit=70)
    prefix = f"guru-{task_slug}-"

    if args.dry_run:
        print(shlex.join(_trellis_cmd(config, ["channel", "list", "--all", "--json"])))
        print(f"# filter: name starts with {prefix!r} or task == {str(task_dir)!r}")
        print("# then inspect exact workers with:")
        print("trellis channel messages <channel> --raw --last 200")
        print(
            "python3 .trellis/scripts/guru/guru_supervise.py kill "
            f"{shlex.quote(str(task_dir))} --channel <channel> --worker <worker>"
        )
        return 0

    result = subprocess.run(
        _trellis_cmd(config, ["channel", "list", "--all", "--json"]),
        cwd=config.root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode
    try:
        summaries = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GuruSupervisionError(f"channel list did not return JSON: {exc}") from exc

    matched = [
        item
        for item in summaries
        if isinstance(item, dict)
        and (
            str(item.get("name", "")).startswith(prefix)
            or str(item.get("task", "")) == str(task_dir)
        )
    ]
    if not matched:
        if args.json:
            print(json.dumps({
                "schema_version": 1,
                "task_dir": str(task_dir),
                "channels": [],
                "live_workers": 0,
                "terminal_workers": 0,
                "cleanup_available": False,
                "blocking": False,
                "cleanup_command": "",
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        print(f"No Guru supervision channels found for {task_dir}")
        return 0

    json_channels = []
    live_workers = 0
    terminal_workers = 0
    cleanup_candidates = []
    for item in matched:
        channel = str(item.get("name"))
        if not args.json:
            print(f"channel: {channel}")
            print(f"  task: {item.get('task', '-')}")
            print(f"  workers: {item.get('workersAlive', 0)}/{item.get('workersTotal', 0)}")
            print(f"  last: {item.get('lastEventKind', '-')}")
        events = _load_channel_events(config, channel)
        workers: dict[str, dict[str, str]] = {}
        for event in events:
            kind = str(event.get("kind", ""))
            worker = str(event.get("as") or event.get("by") or "")
            if kind == "spawned" and worker:
                workers[worker] = {
                    "provider": str(event.get("provider", "-")),
                    "terminal": "running",
                }
            elif kind in {"done", "error", "killed"}:
                worker_name = _terminal_worker_name(event)
                if worker_name:
                    workers.setdefault(worker_name, {"provider": "-", "terminal": "running"})
                    workers[worker_name]["terminal"] = kind
        channel_workers = []
        for worker, info in sorted(workers.items()):
            terminal = info["terminal"]
            is_live = terminal == "running"
            if is_live:
                live_workers += 1
            else:
                terminal_workers += 1
                cleanup_candidates.append({"channel": channel, "worker": worker, "terminal": terminal})
            kill_command = (
                "python3 .trellis/scripts/guru/guru_supervise.py kill "
                f"{shlex.quote(str(task_dir))} --channel {shlex.quote(channel)} "
                f"--worker {shlex.quote(worker)}"
            )
            channel_workers.append({
                "worker": worker,
                "provider": info["provider"],
                "terminal": terminal,
                "live": is_live,
                "kill_command": kill_command,
            })
            if not args.json:
                print(
                    f"  worker: {worker} provider={info['provider']} "
                    f"terminal={terminal}"
                )
                print(f"    kill: {kill_command}")
        messages_command = shlex.join(
            _trellis_cmd(config, ["channel", "messages", channel, "--raw", "--last", "20"])
        )
        json_channels.append({
            "channel": channel,
            "task": item.get("task", "-"),
            "workers_alive": item.get("workersAlive", 0),
            "workers_total": item.get("workersTotal", 0),
            "last_event_kind": item.get("lastEventKind", "-"),
            "workers": channel_workers,
            "messages_command": messages_command,
        })
        if not args.json:
            print("  messages: " + messages_command)
    if args.json:
        cleanup_command = ""
        if cleanup_candidates:
            first = cleanup_candidates[0]
            cleanup_command = (
                "python3 .trellis/scripts/guru/guru_supervise.py kill "
                f"{shlex.quote(str(task_dir))} --channel {shlex.quote(first['channel'])} "
                f"--worker {shlex.quote(first['worker'])}"
            )
        print(json.dumps({
            "schema_version": 1,
            "task_dir": str(task_dir),
            "channels": json_channels,
            "live_workers": live_workers,
            "terminal_workers": terminal_workers,
            "cleanup_available": bool(cleanup_candidates),
            "blocking": live_workers > 0,
            "cleanup_command": cleanup_command,
            "cleanup_candidates": cleanup_candidates,
        }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def kill_action(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
    config = _load_config(
        root,
        platform=args.platform,
        provider=args.provider,
        adversarial=args.adversarial,
        trellis_bin=args.trellis_bin,
    )
    if not args.channel or not args.worker:
        raise GuruSupervisionError("kill requires exact --channel and --worker values")
    cmd = _trellis_cmd(
        config,
        ["channel", "kill", args.channel, "--as", args.worker],
    )
    if args.force:
        cmd.append("--force")
    if args.dry_run:
        print(shlex.join(cmd))
        return 0
    result = _run(cmd, cwd=config.root)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Trellis project root")
    parser.add_argument("--platform", choices=sorted(VALID_PLATFORMS))
    parser.add_argument("--provider")
    parser.add_argument(
        "--adversarial",
        action="store_true",
        help="Spawn the opposite provider for clean-context adversarial review",
    )
    parser.add_argument("--trellis-bin", default=os.environ.get("TRELLIS_BIN"))
    sub = parser.add_subparsers(dest="command", required=True)

    for action in ("requirements", "overview", "detail", "implement", "check"):
        p = sub.add_parser(action)
        p.add_argument("task_dir")
        p.add_argument("--run-id")
        p.add_argument("--dry-run", action="store_true")
        p.set_defaults(func=lambda args, action=action: run_action(args, action))

    implement_check = sub.add_parser("implement-check")
    implement_check.add_argument("task_dir")
    implement_check.add_argument("--run-id")
    implement_check.add_argument("--dry-run", action="store_true")
    implement_check.add_argument("--slice", help="P1 slice packet unit_id（多 packet 时必填；单 packet 可省）")
    implement_check.set_defaults(func=run_implement_check)

    implement_slices = sub.add_parser("implement-slices")
    implement_slices.add_argument("task_dir")
    implement_slices.add_argument("--dry-run", action="store_true")
    implement_slices.add_argument("--parallel", type=_parallel_arg, default=1)
    implement_slices.add_argument("--group", help="Run only one slice-plan parallel_group id")
    implement_slices.add_argument("--backend", choices=sorted(VALID_IMPLEMENT_SLICE_BACKENDS), default="auto")
    implement_slices.set_defaults(func=run_implement_slices)

    implementation_review = sub.add_parser("implementation-review")
    implementation_review.add_argument("task_dir")
    implementation_review.add_argument("--run-id")
    implementation_review.add_argument("--dry-run", action="store_true")
    implementation_review.add_argument(
        "--slice",
        action="append",
        help="Review an existing slice packet; repeat only with --aggregate",
    )
    implementation_review.add_argument(
        "--aggregate",
        action="store_true",
        help="Review one explicit all-missing slice set with one worker",
    )
    implementation_review.add_argument("--staged", action="store_true", help="Bind reviewed_target_digest to the staged index")
    implementation_review.add_argument("--contract", action="store_true", help="Derive review target from gate-contract and staged code paths")
    implementation_review.add_argument("--same-provider", action="store_true", help="Use the current provider for implementation-review when the user explicitly skips the opposite provider")
    implementation_review.add_argument("--user-quote", help="Required audit quote when --same-provider is used")
    implementation_review.set_defaults(func=run_implementation_review)

    status = sub.add_parser("status")
    status.add_argument("task_dir")
    status.add_argument("--dry-run", action="store_true")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=status_action)

    kill = sub.add_parser("kill")
    kill.add_argument("task_dir")
    kill.add_argument("--channel", required=True)
    kill.add_argument("--worker", required=True)
    kill.add_argument("--force", action="store_true")
    kill.add_argument("--dry-run", action="store_true")
    kill.set_defaults(func=kill_action)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except GuruSupervisionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
