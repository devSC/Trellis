#!/usr/bin/env python3
"""Run Guru implement/check work through the official trellis channel runtime.

Usage:
    python3 guru_supervise.py [--adversarial] requirements <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] overview <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] detail <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] implement <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] check <task-dir> [--dry-run]
    python3 guru_supervise.py [--adversarial] implement-check <task-dir> [--dry-run]
    python3 guru_supervise.py status <task-dir>
    python3 guru_supervise.py kill <task-dir> --channel <name> --worker <name>
"""

from __future__ import annotations

import argparse
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
)
import guru_risk  # noqa: E402  共享风险 helper（③ 独立 check 触发判定）
import guru_review_record  # noqa: E402  P1 packet reader / 单一 writer / verdict 校验


VALID_ACTIONS = {"requirements", "overview", "detail", "implement", "check", "implement-check"}
VALID_PLATFORMS = {"flutter", "go", "ios", "h5"}

DEFAULT_PROVIDER = "codex"
DEFAULT_IMPLEMENT_TIMEOUT = "45m"
DEFAULT_CHECK_TIMEOUT = "30m"
DEFAULT_WARN_BEFORE = "5m"
DEFAULT_IMPLEMENT_CHECK_MAX_LOOPS = 3
DEFAULT_ADVERSARIAL_CLAUDE_MODEL = "claude-sonnet-4-6"
DEFAULT_ADVERSARIAL_CODEX_MODEL = "gpt-5.4"
DEFAULT_ADVERSARIAL_CODEX_REASONING_EFFORT = "high"
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

SKILL_BY_PLATFORM: dict[str, dict[str, list[str]]] = {
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
    match = ROUTE_RE.search(text)
    if match:
        route = match.group(1).upper()
        if route != "NONE":
            return route
    if "review_result=clean/final-verification-ready" in text:
        return "clean"
    return None


def _opposite_provider(provider: str) -> str:
    current = provider.strip().lower()
    if current == "codex":
        return "claude"
    if current == "claude":
        return "codex"
    return DEFAULT_PROVIDER


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
    slice_packet_path: Path = None,
) -> RunPlan:
    if action not in VALID_ACTIONS:
        raise GuruSupervisionError(f"unknown action {action!r}")
    if not task_dir.is_dir():
        raise GuruSupervisionError(f"task directory not found: {task_dir}")

    action_timeout = config.check_timeout if action in {"requirements", "check"} else config.implement_timeout
    run_slug = _sanitize(run_id, limit=40)
    provider_slug = _sanitize(config.provider, limit=24)
    task_slug = _sanitize(task_dir.name, limit=70)
    channel = f"guru-{task_slug}-{action}-{run_slug}"
    worker = f"{action}-{provider_slug}-{run_slug}"

    skill_rels = SKILL_BY_PLATFORM[config.platform][action]
    skill_paths = [config.root / rel for rel in skill_rels]
    artifact_candidates = [
        *skill_paths,
        task_dir / "prd.md",
        task_dir / "design.md",
        task_dir / "implement.md",
    ]
    if action == "requirements":
        artifact_candidates.extend(
            [
                task_dir / "task.json",
                *_requirements_reference_files(config.root, task_dir),
            ]
        )
    if config.platform == "flutter" and action in {"implement", "check", "implement-check"}:
        # ② 为 flutter 实现期 review 注入正式 requirement/design 包(SSOT 否决基线);
        # 声明却非法/缺失的包由 collect_review_artifacts → GuruSupervisionError 在 spawn 前 fail-closed
        artifact_candidates.extend(collect_review_artifacts(task_dir, "detail", config.root))
    if slice_packet_path is not None:  # P1c R4-F2:注入 resolved slice packet,worker 才能逐条 invariant/正确 provider
        artifact_candidates.append(slice_packet_path)
    artifact_files = _dedupe_paths(_existing_paths(artifact_candidates))
    jsonl_names = [f"{action}.jsonl"]
    if action == "implement-check":
        jsonl_names = ["implement.jsonl", "check.jsonl"]
    if action == "requirements":
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
            action,
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
            "wording nits or observations are non-blocking. Emit review_result=clean/requirements-ready "
            "only when no blocker remains. Keep temporary requirement decisions in prd.md; do not write "
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
        responsibility = "Implement according to the Guru workflow and keep implement.md evidence current."
    elif action == "implement-check":
        responsibility = (
            "Implement the planned slices, then review the current diff under Guru quality rules, self-fixing only "
            "issues in scope. Route IMPLEMENT_DEFECT, DETAIL_DEFECT, OVERVIEW_DEFECT, REQ_BLOCKER, and "
            "PROCESS_DEFECT explicitly. A single clean implementation check is MVP review evidence only when the "
            "output includes review_result=clean/final-verification-ready, reviewed diff/artifact context, and "
            "validation_summary. Do not create implementation guru_gates. Keep implement.md evidence current and "
            "stop at final validation plus hard boundary."
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


def _requirements_review_verdict(messages: str) -> tuple[str, str]:
    if REQUIREMENTS_CLEAN_MARKER in messages:
        return "clean", REQUIREMENTS_CLEAN_MARKER
    match = ROUTE_RE.search(messages)
    if match:
        route = match.group(1).upper()
        if route != "NONE":
            return "blocked", f"route_class={route}"
    return "deferred", "missing requirements review verdict"


def _record_requirements_review(
    plan: RunPlan,
    config: SupervisionConfig,
    status: str,
    reason: str,
) -> None:
    if not (config.adversarial and plan.action == "requirements"):
        return
    task_json = plan.task_dir / "task.json"
    try:
        data = json.loads(task_json.read_text(encoding="utf-8")) if task_json.exists() else {}
        if not isinstance(data, dict):
            return
        gates = data.setdefault(GATES_KEY, {})
        if not isinstance(gates, dict):
            return
        gates[REQUIREMENTS_REVIEW_KEY] = {
            "action": plan.action,
            "provider": config.provider,
            "current_provider": config.current_provider,
            "adversarial": True,
            "status": status,
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
    except Exception as exc:
        # Requirements review state is advisory visibility; do not block the main workflow.
        sys.stderr.write(f"[guru-supervise] failed to record requirements review: {exc}\n")


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
    return 0, "skipped", messages


def _execute_plan(plan: RunPlan, config: SupervisionConfig) -> tuple[int, str | None, str]:
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
        _record_requirements_review(plan, config, status, reason)
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


def run_implement_check(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
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
    base_run_id = args.run_id or _default_run_id()

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

    # ③ P0/P1：高风险触发独立(对立 provider)阻断 check;packet.risk 优先(unit_id,§4.5.8;packet 已 preflight 合法)。
    # provider 隔离 + adversarial=False → 不走 advisory rc0,check 失败 rc≠0 阻断。
    try:
        independent_required, independent_reason = guru_risk.implement_check_independent_required(
            str(task_dir), config.platform, str(root), unit_id=unit_id
        )
    except guru_review_record.ReviewRecordError as exc:  # 防御:packet 已 preflight,正常不触发
        guru_review_record.append_record(str(task_dir), guru_review_record.preflight_failure_record(
            "PACKET_INVALID", f"{base_run_id}-check-1", unit_id=unit_id))
        sys.stderr.write(f"[guru-supervise] slice packet 非法,硬停(PACKET_INVALID):{exc}\n")
        return 2

    check_config = (
        replace(config, current_provider=config.provider, provider=_opposite_provider(config.provider))
        if independent_required
        else config
    )
    if independent_required:
        sys.stderr.write(
            f"[guru-supervise] 独立实现期 review ON（{independent_reason}）："
            f"implement provider={config.provider} ≠ check provider={check_config.provider}\n"
        )

    # P1c R4-F2：有 packet 时注入到 worker（artifact --file + brief active_slice），worker 才能逐条
    # invariant、输出正确 review_target/provider。无 packet → slice_packet_path=None（P0 旧路径）。
    slice_packet_path = (task_dir / "slice-packets" / f"{unit_id}.json") if unit_id else None
    active_slice_brief = ""
    if packet is not None:
        _sp = packet.get("semantic_review_provider", {})
        active_slice_brief = (
            f"\nactive_slice={unit_id}\nslice_packet={slice_packet_path}\n"
            f"review_target=slice:{unit_id}\ntarget_paths={packet.get('target_paths')}\n"
            f"semantic_review_provider={_sp.get('provider')}(required={_sp.get('required')})\n"
            "置顶输出 7 字段 + 逐条 invariant_status.<id>=pass|fail|not_applicable"
            "（pass 必随 invariant_evidence.<id>；not_applicable 必随 invariant_reason.<id>）。\n"
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
            verdict = guru_review_record.parse_verdict_block(messages)
            record, failure = guru_review_record.normalize_review_record(verdict, {
                "mode": "supervisor", "packet": packet, "implement_provider": config.provider,
                "supervisor_deterministic_status": det_status, "deterministic_results": det_results,
                "run_id": f"{base_run_id}-check-{iteration}", "slice_id": unit_id,
                "review_target": f"slice:{unit_id}", "target_paths": packet.get("target_paths", []),
                "channel": check_plan.channel, "worker": check_plan.worker,
                "check_provider": check_config.provider,  # R1-F1:worker 自报 review_provider 须 == 实际 spawn
                "independent_required": independent_required,  # R1-F1:对立要求仅独立期强制(low-risk override 不要求)
            })
            guru_review_record.append_record(str(task_dir), record)
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
        print(f"No Guru supervision channels found for {task_dir}")
        return 0

    for item in matched:
        channel = str(item.get("name"))
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
                by = str(event.get("by") or "")
                if by:
                    workers.setdefault(by, {"provider": "-", "terminal": "running"})
                    workers[by]["terminal"] = kind
        for worker, info in sorted(workers.items()):
            print(
                f"  worker: {worker} provider={info['provider']} "
                f"terminal={info['terminal']}"
            )
            print(
                "    kill: "
                "python3 .trellis/scripts/guru/guru_supervise.py kill "
                f"{shlex.quote(str(task_dir))} --channel {shlex.quote(channel)} "
                f"--worker {shlex.quote(worker)}"
            )
        print(
            "  messages: "
            + shlex.join(
                _trellis_cmd(config, ["channel", "messages", channel, "--raw", "--last", "20"])
            )
        )
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

    status = sub.add_parser("status")
    status.add_argument("task_dir")
    status.add_argument("--dry-run", action="store_true")
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
