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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote, urlparse


VALID_ACTIONS = {"requirements", "overview", "detail", "implement", "check", "implement-check"}
VALID_PLATFORMS = {"flutter", "go", "ios", "h5"}

DEFAULT_PROVIDER = "codex"
DEFAULT_IMPLEMENT_TIMEOUT = "45m"
DEFAULT_CHECK_TIMEOUT = "30m"
DEFAULT_WARN_BEFORE = "5m"
DEFAULT_IMPLEMENT_CHECK_MAX_LOOPS = 3

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
    implement_timeout: str
    check_timeout: str
    warn_before: str
    idle_timeout: str | None
    max_live_workers: str | None
    trellis_bin: str


@dataclass(frozen=True)
class RunPlan:
    action: str
    task_dir: Path
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
    )


def build_run_plan(
    action: str,
    task_dir: Path,
    config: SupervisionConfig,
    run_id: str,
    extra_brief: str = "",
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


def _execute_plan(plan: RunPlan, config: SupervisionConfig) -> tuple[int, str | None, str]:
    for command in (plan.create_cmd, plan.spawn_cmd):
        result = _run(command, cwd=config.root)
        if result.returncode != 0:
            return result.returncode, None, ""

    result = _run(plan.send_cmd, cwd=config.root, stdin=plan.brief)
    if result.returncode != 0:
        return result.returncode, None, ""

    wait = _run(plan.wait_cmd, cwd=config.root)
    terminal = _terminal_status(wait.stdout)
    messages = _run(plan.messages_cmd, cwd=config.root)
    if wait.returncode != 0:
        return wait.returncode, terminal, messages.stdout
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

    rc, _terminal, _messages = _execute_plan(plan, config)
    return rc


def run_implement_check(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).expanduser().resolve()
    root = _resolve_root(args.root, task_dir)
    config = _load_config(
        root,
        platform=args.platform,
        provider=args.provider,
        adversarial=args.adversarial,
        trellis_bin=args.trellis_bin,
    )
    base_run_id = args.run_id or _default_run_id()

    if args.dry_run:
        implement_plan = build_run_plan(
            "implement",
            task_dir,
            config,
            f"{base_run_id}-implement-1",
            "Implement-check loop step 1/2: apply implementation fixes from the previous check context when present.",
        )
        check_plan = build_run_plan(
            "check",
            task_dir,
            config,
            f"{base_run_id}-check-1",
            "Implement-check loop step 2/2: emit review_result=clean/final-verification-ready with route_class=none, or route_class=<defect>.",
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
            extra,
        )
        rc, _terminal, _messages = _execute_plan(implement_plan, config)
        if rc != 0:
            return rc

        check_plan = build_run_plan(
            "check",
            task_dir,
            config,
            f"{base_run_id}-check-{iteration}",
            "Emit exactly one route_class and review_result for implement-check routing.",
        )
        rc, _terminal, messages = _execute_plan(check_plan, config)
        if rc != 0:
            return rc

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
