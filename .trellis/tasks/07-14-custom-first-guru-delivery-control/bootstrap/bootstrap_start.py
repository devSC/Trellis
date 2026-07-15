#!/usr/bin/env python3
"""Audited one-shot start for this task's delivery-control bootstrap only."""

from __future__ import annotations

import argparse
import ast
import base64
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK = Path(".trellis/tasks/07-14-custom-first-guru-delivery-control")
TASK_ID, SLICE = "custom-first-guru-delivery-control", "delivery-control"
SOURCE = TASK / "bootstrap/bootstrap_start.py"
EVIDENCE, LOCK = "bootstrap-exception.jsonl", ".bootstrap-exception.lock"
SHA = re.compile(r"^[0-9a-f]{64}$")
SAFE_CHANNEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
BOOTSTRAP_REVIEW_AUTHORIZATION = {
    "kind": "codex_same_provider_user_directive_v1",
    "user_directive": "关闭调用claude",
    "provider": "codex",
    "review_mode": "check_only",
    "independence_claim": "none",
    "trusted_review_envelope_eligible": False,
}
FIXED_CAPABILITY_CHECKS = (
    "python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_delivery_policy.py'",
    "python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_start_guard.py'",
)
EXPECTED_ATTEMPT_CAPABILITY = {
    "entry_scope": "guarded_entry",
    "guarded_lifecycle_bindings": "enforced",
    "guarded_structural_bindings": "enforced",
    "confirmation_identity_provenance": "unavailable_fail_closed",
    "unresolved_required_high_risk": "blocked",
    "direct_official_bypass": "advisory",
}
BOOTSTRAP_DIRTY_EXCEPTION = {
    str(TASK / "bootstrap/bootstrap_start.py"),
    str(TASK / "bootstrap/tests/test_bootstrap_start.py"),
}
IMPLEMENTATION_REVIEW_EXCEPTION = str(TASK / "review-records/implementation-reviews.jsonl")
POSTCHECK_DIRTY_EXCEPTION = BOOTSTRAP_DIRTY_EXCEPTION | {str(TASK / EVIDENCE), IMPLEMENTATION_REVIEW_EXCEPTION}
OFFICIAL_BASELINE = {
    "authority": "comparison_only_not_execution_authority",
    "package": "@mindfoldhq/trellis",
    "version": "0.6.7",
    "npm_integrity": "sha512-W67K3DvKGk2W/cFGWM3ev2HvMY9DzWc2sWegv7l+iBiY//Vf9lplQT9dy7jD7j4+MwHDLFIYSM7nZjFcGqgrrg==",
    "tarball_sha256": "98e3c22bedf2f201d0370bd40e7baeb5c0e8b323f1f768abde433f3fb227cfaf",
}


class Fail(RuntimeError):
    pass


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str:
    regular(path)
    return digest(path.read_bytes())


def regular(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise Fail(f"required file unavailable: {path}: {exc}") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise Fail(f"not a non-symlink regular file: {path}")


def directory(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise Fail(f"required directory unavailable: {path}: {exc}") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise Fail(f"not a non-symlink directory: {path}")


def load(path: Path) -> dict[str, Any]:
    regular(path)
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Fail(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise Fail(f"JSON root is not an object: {path}")
    return value


def fsync_parent(path: Path) -> None:
    fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextlib.contextmanager
def locked(path: Path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def frame(seq: int, event: str, payload: dict[str, Any], previous: str | None) -> bytes:
    body = {
        "schema_version": 1, "sequence": seq, "event": event,
        "event_id": str(uuid.uuid4()),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "previous_event_sha256": previous,
        "payload_sha256": digest(canon(payload)), "payload": payload,
    }
    return canon(body) + b"\n"


def chain(path: Path) -> list[tuple[dict[str, Any], bytes, str]]:
    regular(path)
    raw = path.read_bytes()
    if not raw or not raw.endswith(b"\n"):
        raise Fail("torn bootstrap chain")
    prior, result = None, []
    lines = raw.splitlines(keepends=True)
    if len(lines) > 5:
        raise Fail("reused bootstrap chain")
    for index, line in enumerate(lines):
        try:
            item = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise Fail("corrupt bootstrap chain") from exc
        if not isinstance(item, dict) or item.get("schema_version") != 1 or not item.get("event_id") or canon(item) + b"\n" != line:
            raise Fail("non-canonical bootstrap frame")
        payload = item.get("payload")
        if item.get("sequence") != index + 1 or item.get("previous_event_sha256") != prior:
            raise Fail("corrupt/misordered bootstrap link")
        if not isinstance(payload, dict) or item.get("payload_sha256") != digest(canon(payload)):
            raise Fail("corrupt bootstrap payload")
        event = item.get("event")
        if index == 0 and event != "prepared":
            raise Fail("corrupt/misordered bootstrap link")
        if index > 0:
            previous = result[-1][0]
            previous_event, previous_payload = previous.get("event"), previous.get("payload", {})
            allowed = {
                "prepared": {"consumed"},
                "retry_prepared": {"retry_consumed"},
            }.get(str(previous_event), set())
            if previous_event in ("consumed", "retry_consumed"):
                if previous_payload.get("outcome") == "verified":
                    allowed = {"burned"}
                elif previous_event == "consumed" and previous_payload.get("outcome") == "failed_compensated":
                    allowed = {"retry_prepared"}
                else:
                    allowed = set()
            if event not in allowed:
                raise Fail("corrupt/misordered bootstrap link")
        prior = digest(line)
        result.append((item, line, prior))
    return result


def create(path: Path, line: bytes) -> None:
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise Fail("bootstrap already used") from exc
    with os.fdopen(fd, "wb") as stream:
        stream.write(line); stream.flush(); os.fsync(stream.fileno())
    fsync_parent(path)


def append(path: Path, event: str, payload: dict[str, Any]) -> str:
    current = chain(path)
    last_event = current[-1][0]["event"]
    last_payload = current[-1][0]["payload"]
    valid = (
        (event == "consumed" and last_event == "prepared")
        or (event == "retry_prepared" and last_event == "consumed" and last_payload.get("outcome") == "failed_compensated")
        or (event == "retry_consumed" and last_event == "retry_prepared")
        or (event == "burned" and last_event in ("consumed", "retry_consumed") and last_payload.get("outcome") == "verified")
    )
    if not valid:
        raise Fail(f"invalid state for {event}")
    line = frame(len(current) + 1, event, payload, current[-1][2])
    fd = os.open(path, os.O_WRONLY | os.O_APPEND)
    with os.fdopen(fd, "ab") as stream:
        stream.write(line); stream.flush(); os.fsync(stream.fileno())
    fsync_parent(path)
    return digest(line)


def snap(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False, "sha256": None, "content_base64": None, "mode": None, "json": None}
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return {"path": str(path), "exists": False, "sha256": None, "content_base64": None, "mode": None, "json": None}
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise Fail(f"unsafe lifecycle file: {path}")
    content = path.read_bytes()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise Fail(f"corrupt lifecycle JSON: {path}") from exc
    if not isinstance(parsed, dict):
        raise Fail(f"lifecycle JSON root is not object: {path}")
    return {"path": str(path), "exists": True, "sha256": digest(content),
            "content_base64": base64.b64encode(content).decode(),
            "mode": stat.S_IMODE(mode), "json": parsed}


def current_run(snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot["path"] is None: return {"state": "no_session_identity", "value": None}
    if not snapshot["exists"]: return {"state": "session_file_absent", "value": None}
    if "current_run" not in snapshot["json"]: return {"state": "absent", "value": None}
    value = snapshot["json"]["current_run"]
    return {"state": "null" if value is None else "value", "value": value}


def command(root: Path, *args: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    actual_env = os.environ.copy(); actual_env.update(env or {})
    result = subprocess.run(args, cwd=root, env=actual_env, text=True,
                            capture_output=True, encoding="utf-8", errors="replace")
    return {"argv": list(args), "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def must(result: dict[str, Any], label: str) -> dict[str, Any]:
    if result["returncode"]:
        raise Fail(f"{label} failed rc={result['returncode']}: {result['stderr'].strip()}")
    return result


def context_key() -> str | None:
    raw = os.environ.get("TRELLIS_CONTEXT_ID") or os.environ.get("CODEX_THREAD_ID")
    if not raw: return None
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", raw.strip()).strip("._-")[:160]
    return safe if os.environ.get("TRELLIS_CONTEXT_ID") else f"codex_{safe}"


def paths(task_arg: str, slice_id: str, source_sha: str) -> dict[str, Path | str]:
    root = Path.cwd().resolve()
    while root != root.parent and not (root / ".trellis").is_dir(): root = root.parent
    exact = root / TASK
    supplied = Path(task_arg); supplied = supplied if supplied.is_absolute() else root / supplied
    if supplied.resolve() != exact.resolve() or slice_id != SLICE:
        raise Fail("wrong task or slice")
    source = root / SOURCE
    if not SHA.fullmatch(source_sha) or file_hash(source) != source_sha:
        raise Fail("reviewed source SHA-256 mismatch")
    result: dict[str, Path | str] = {"root": root, "task": exact, "source_sha": source_sha,
        "log": exact / EVIDENCE, "lock": exact / LOCK, "task_json": exact / "task.json",
        "contract": exact / "gate-contract.json", "packet": exact / "slice-packets/delivery-control.json",
        "task_py": root / ".trellis/scripts/task.py", "gate": root / ".trellis/scripts/guru/guru_gate.py",
        "supervisor": root / ".trellis/scripts/guru/guru_supervise.py",
        "template_supervisor": root / "guru-template/overlay/verify/guru_supervise.py",
        "wrapper": root / "guru-template/overlay/hooks/guru_task.py",
        "after_start": root / "guru-template/overlay/hooks/guru_after_start.py",
        "contract_module": root / "guru-template/overlay/verify/guru_contract.py",
        "template_gate": root / "guru-template/overlay/verify/guru_gate.py",
        "review_record": root / "guru-template/overlay/verify/guru_review_record.py"}
    for key in ("task_json", "contract", "packet", "task_py", "gate", "supervisor", "template_supervisor", "wrapper", "after_start", "contract_module", "template_gate", "review_record"):
        regular(result[key])  # type: ignore[arg-type]
    return result


def dependency_hashes(p: dict[str, Path | str]) -> dict[str, str]:
    root = p["root"]
    rels = [".trellis/scripts/task.py", ".trellis/scripts/common/__init__.py",
            ".trellis/scripts/common/active_task.py", ".trellis/scripts/common/io.py",
            ".trellis/scripts/common/log.py", ".trellis/scripts/common/paths.py",
            ".trellis/scripts/common/task_utils.py", ".trellis/scripts/common/config.py",
            ".trellis/scripts/common/tasks.py", ".trellis/scripts/common/types.py",
            ".trellis/scripts/common/task_store.py", ".trellis/scripts/common/task_context.py",
            ".trellis/scripts/common/git.py", ".trellis/scripts/common/safe_commit.py",
            ".trellis/config.yaml", ".trellis/scripts/guru/guru_gate.py",
            ".trellis/scripts/guru/guru_supervise.py",
            "guru-template/overlay/verify/guru_supervise.py",
            "guru-template/overlay/hooks/guru_task.py",
            "guru-template/overlay/hooks/guru_after_start.py",
            "guru-template/overlay/verify/guru_contract.py",
            "guru-template/overlay/verify/guru_gate.py",
            "guru-template/overlay/verify/guru_review_record.py"]
    return {rel: file_hash(root / rel) for rel in rels}  # type: ignore[operator]


def dirty_exception_allowed(root: Path, dirty: set[str], *, include_runtime_evidence: bool) -> bool:
    allowed = POSTCHECK_DIRTY_EXCEPTION if include_runtime_evidence else BOOTSTRAP_DIRTY_EXCEPTION
    if not dirty or not dirty <= allowed:
        return False
    if IMPLEMENTATION_REVIEW_EXCEPTION not in dirty:
        return True
    review_path = root / IMPLEMENTATION_REVIEW_EXCEPTION
    regular(review_path)
    lines = [line for line in review_path.read_text().splitlines() if line.strip()]
    if not lines:
        return False
    for line in lines:
        try:
            item = json.loads(line)
        except (UnicodeError, json.JSONDecodeError):
            return False
        if not (
            isinstance(item, dict)
            and item.get("review_target") == f"slice:{SLICE}"
            and item.get("slice_id") == SLICE
            and item.get("review_result") == "blocked"
            and item.get("supervisor_failure") == "SCOPE_INVALID"
            and item.get("target_paths") == []
        ):
            return False
    return True


def preflight(p: dict[str, Path | str]) -> dict[str, Any]:
    task_data, contract, packet = load(p["task_json"]), load(p["contract"]), load(p["packet"])  # type: ignore[arg-type]
    if (task_data.get("id"), task_data.get("status")) != (TASK_ID, "planning"):
        raise Fail("exact task must be planning")
    if (contract.get("route"), contract.get("risk")) != ("full_chain", "high"):
        raise Fail("contract route/risk mismatch")
    if (packet.get("slice_id"), packet.get("risk"), packet.get("depends_on")) != (SLICE, "high", []):
        raise Fail("packet identity/risk/dependency mismatch")
    root, gate = p["root"], str(p["gate"])
    plan_cmd = must(command(root, sys.executable, gate, "slice-plan", str(TASK)), "slice-plan")  # type: ignore[arg-type]
    try: plan = json.loads(plan_cmd["stdout"])
    except json.JSONDecodeError as exc: raise Fail("slice-plan JSON invalid") from exc
    selected = [x for x in plan.get("slices", []) if x.get("slice_id") == SLICE]
    blockers = set(plan.get("blocking_reasons", [])) - {"PACKET_AMBIGUOUS_WITHOUT_SLICE"}
    for item in plan.get("slices", []):
        dirty = set(item.get("dirty_out_of_scope") or [])
        if dirty_exception_allowed(root, dirty, include_runtime_evidence=True):
            blockers.discard(f"SCOPE_INVALID:{item.get('slice_id')}")
            item["parallel_blockers"] = [x for x in item.get("parallel_blockers", []) if x != "SCOPE_INVALID"]
            item["bootstrap_dirty_exception"] = sorted(dirty)
    if blockers or len(selected) != 1 or selected[0].get("depends_on") != [] or selected[0].get("parallel_blockers"):
        raise Fail(f"delivery-control not eligible: {sorted(blockers)}")
    start_cmd = must(command(root, sys.executable, gate, "check-start", str(TASK)), "check-start")  # type: ignore[arg-type]
    digests, digest_cmds = {}, []
    for name in ("requirements", "overview", "detail"):
        result = must(command(root, sys.executable, gate, "digest", name, str(TASK)), f"digest {name}")  # type: ignore[arg-type]
        value = result["stdout"].strip()
        if not SHA.fullmatch(value): raise Fail(f"invalid {name} digest")
        digests[name] = value; digest_cmds.append(result)
    task_data = load(p["task_json"])  # type: ignore[arg-type]
    gates = task_data.get("guru_gates", {})
    confirmations, reviews = {}, {}
    for name in ("requirements", "detail"):
        record = gates.get(name)
        if not isinstance(record, dict) or record.get("artifact_digest") != digests[name] or not record.get("confirmed_by") or record.get("mode") == "soft" or record.get("via") == "agent":
            raise Fail(f"{name} strict confirmation missing/stale")
        confirmations[name] = {"record": record, "canonical_sha256": digest(canon(record)),
            "strict_tty_observation": "check-start accepted a v1 record without soft/agent markers",
            "tty_device_ref": "unavailable_in_v1"}
    for name in ("overview", "detail"):
        runs = [x for x in gates.get("review_runs", {}).get(name, []) if isinstance(x, dict) and x.get("artifact_digest") == digests[name]]
        clean = [x for x in runs[-2:] if x.get("result") == "clean" and x.get("max_severity") in ("none", "low") and x.get("run_id") and "clean-context" in str(x.get("reviewer", "")).lower()]
        if len(clean) != 2 or len({x["run_id"] for x in clean}) != 2 or (name == "detail" and any(not x.get("deletion_audit") for x in clean)):
            raise Fail(f"{name} current double-clean/deletion audit missing")
        reviews[name] = {"current_runs": runs, "canonical_sha256": digest(canon(runs))}
    return {"artifact_digests": digests, "confirmations": confirmations, "reviews": reviews,
        "contract_sha256": file_hash(p["contract"]), "packet_sha256": file_hash(p["packet"]),  # type: ignore[arg-type]
        "commands": {"slice_plan": plan_cmd, "check_start": start_cmd, "digests": digest_cmds}}


def restore(pre: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    if pre["path"] is None: return {"status": "not_applicable"}
    path = Path(pre["path"]); now = snap(path)
    if (now["exists"], now["sha256"]) != (observed["exists"], observed["sha256"]):
        return {"status": "manual_recovery_required", "path": str(path)}
    if not pre["exists"]:
        if now["exists"]: path.unlink(); fsync_parent(path)
        return {"status": "restored_absent", "path": str(path)}
    content = base64.b64decode(pre["content_base64"])
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.restore.", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream: stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.chmod(tmp, pre["mode"]); os.replace(tmp, path); fsync_parent(path)
    finally:
        with contextlib.suppress(FileNotFoundError): tmp.unlink()
    return {"status": "restored_exact_preimage", "path": str(path), "sha256": pre["sha256"]}


def verified_consumed_source(
    p: dict[str, Path | str],
    items: list[tuple[dict[str, Any], bytes, str]],
) -> dict[str, str]:
    verified_index = next((
        index for index in range(len(items) - 1, -1, -1)
        if items[index][0].get("event") in ("consumed", "retry_consumed")
        and items[index][0].get("payload", {}).get("outcome") == "verified"
    ), None)
    if verified_index is None or verified_index == 0:
        raise Fail("verified consumed source is missing")
    consumed = items[verified_index][0]["payload"]
    prepared = items[verified_index - 1][0]["payload"]
    source_sha = consumed.get("source_sha256")
    if not isinstance(source_sha, str) or source_sha != prepared.get("source_sha256") or not SHA.fullmatch(source_sha):
        raise Fail("verified consumed source binding mismatch")
    if source_sha == p["source_sha"]:
        source_path = p["root"] / SOURCE  # type: ignore[operator]
        storage = "current_verifier"
    else:
        source_path = p["task"] / "bootstrap/archive" / f"bootstrap_start.{source_sha}.py"  # type: ignore[operator]
        storage = "immutable_task_archive"
    if file_hash(source_path) != source_sha:
        raise Fail("historical verified-consumed source bytes are missing or stale")
    return {
        "event_sha256": items[verified_index][2],
        "source_sha256": source_sha,
        "storage": storage,
        "path": source_path.resolve().relative_to(p["root"]).as_posix(),  # type: ignore[union-attr,arg-type]
    }


def bind_chain(
    p: dict[str, Path | str],
    items: list[tuple[dict[str, Any], bytes, str]],
) -> dict[str, str] | None:
    current_source = p["source_sha"]
    for index, (item, _, _) in enumerate(items):
        payload, event = item["payload"], item["event"]
        if payload.get("task_id") != TASK_ID or payload.get("slice") != SLICE:
            raise Fail("chain task/slice/source binding mismatch")
        if event in ("prepared", "retry_prepared") and payload.get("source_sha256") == current_source and payload.get("dependency_hashes") != dependency_hashes(p):
            raise Fail("local lifecycle dependency changed")
        if event in ("consumed", "retry_consumed"):
            prepared = items[index - 1][0]["payload"]
            if payload.get("source_sha256") != prepared.get("source_sha256"):
                raise Fail("chain task/slice/source binding mismatch")
        if event == "burned" and payload.get("source_sha256") != current_source:
            raise Fail("chain task/slice/source binding mismatch")
    if any(
        item[0].get("event") in ("consumed", "retry_consumed")
        and item[0].get("payload", {}).get("outcome") == "verified"
        for item in items
    ):
        return verified_consumed_source(p, items)
    return None


def compensation_is_clean(payload: dict[str, Any]) -> bool:
    if payload.get("outcome") != "failed_compensated":
        return False
    compensation = payload.get("compensation")
    if not isinstance(compensation, dict):
        return False
    accepted = {"restored_exact_preimage", "restored_absent", "not_applicable"}
    return all(isinstance(v, dict) and v.get("status") in accepted for v in compensation.values())


def bootstrap_scope_only(root: Path, result: dict[str, Any]) -> bool:
    if result.get("returncode") == 0:
        return True
    if result.get("returncode") != 2 or "scope invalid" not in str(result.get("stderr", "")):
        return False
    match = re.search(r"out-of-scope dirty paths: (\[[^\n]+\])", str(result.get("stderr", "")))
    if not match:
        return False
    try:
        dirty = set(ast.literal_eval(match.group(1)))
    except (SyntaxError, ValueError):
        return False
    return dirty_exception_allowed(root, dirty, include_runtime_evidence=True)


def run(p: dict[str, Path | str]) -> dict[str, Any]:
    with locked(p["lock"]):  # type: ignore[arg-type]
        prior_failed = None
        if Path(p["log"]).exists():  # type: ignore[arg-type]
            existing = chain(p["log"])  # type: ignore[arg-type]
            prior_failed = existing[-1]
            if existing[-1][0]["event"] != "consumed" or not compensation_is_clean(existing[-1][0]["payload"]):
                raise Fail("bootstrap run cannot be reused")
        facts = preflight(p); key = context_key()
        session_path = p["root"] / ".trellis/.runtime/sessions" / f"{key}.json" if key else None  # type: ignore[operator]
        task_pre, session_pre = snap(p["task_json"]), snap(session_path)  # type: ignore[arg-type]
        event_name = "retry_prepared" if prior_failed else "prepared"
        invocation = {"command": "run", "task": str(TASK), "slice": SLICE,
                      "source_sha256": p["source_sha"], "retry_after": prior_failed[2] if prior_failed else None}
        prepared = {"task_id": TASK_ID, "slice": SLICE, "source_sha256": p["source_sha"],
            "state": event_name, "reason": "one-shot self-hosting before the v2 wrapper exists",
            **facts, "dependency_hashes": dependency_hashes(p),
            "source": {"path": str(SOURCE), "actual_sha256": file_hash(p["root"] / SOURCE),
                       "reviewed_sha256": p["source_sha"], "invocation": invocation,
                       "invocation_sha256": digest(canon(invocation))},
            "official_067": OFFICIAL_BASELINE,
            "hook_capability": {"after_start": "non_blocking_not_hard_enforcement", "direct_bypass": "not_prevented"},
            "task_json_preimage": task_pre, "session_preimage": session_pre,
            "session_current_run_preimage": current_run(session_pre), "context_key": key}
        if prior_failed:
            prepared["retry_after_event_sha256"] = prior_failed[2]
            prepared_digest = append(p["log"], event_name, prepared)  # type: ignore[arg-type]
        else:
            first = frame(1, event_name, prepared, None); create(p["log"], first)  # type: ignore[arg-type]
            prepared_digest = digest(first)
        env = {"TRELLIS_CONTEXT_ID": key} if key else {}
        official = command(p["root"], sys.executable, str(p["task_py"]), "start", str(TASK), env=env)  # type: ignore[arg-type]
        task_post, session_post = snap(p["task_json"]), snap(session_path)  # type: ignore[arg-type]
        problems = []
        expected = dict(task_pre["json"]); expected["status"] = "in_progress"
        if official["returncode"] or task_post["json"] != expected: problems.append("official start failed or task postimage invalid")
        if key:
            expected_run = session_pre["json"].get("current_run") if session_pre["exists"] and "current_run" in session_pre["json"] else None
            if not session_post["exists"] or session_post["json"].get("current_task") != str(TASK) or session_post["json"].get("current_run") != expected_run:
                problems.append("session postimage/current_run invalid")
            elif session_pre["exists"] and any(session_post["json"].get(k) != v for k, v in session_pre["json"].items() if k not in ("platform", "last_seen_at", "current_task", "current_run")):
                problems.append("session postimage changed an unrelated preimage field")
        check = dry = None
        if not problems:
            check = command(p["root"], sys.executable, str(p["gate"]), "check-implementation", str(TASK), env=env)  # type: ignore[arg-type]
            dry = command(p["root"], sys.executable, str(p["supervisor"]), "implement-check", str(TASK), "--slice", SLICE, "--dry-run", env=env)  # type: ignore[arg-type]
            if check["returncode"] or not bootstrap_scope_only(p["root"], dry): problems.append("postcheck failed")  # type: ignore[arg-type]
            if (snap(p["task_json"])["sha256"], snap(session_path)["sha256"]) != (task_post["sha256"], session_post["sha256"]):  # type: ignore[arg-type]
                problems.append("postcheck mutated lifecycle state")
        if problems:
            compensation = {"task_json": restore(task_pre, task_post), "session": restore(session_pre, session_post)}
            outcome = "manual_recovery_required" if any(x["status"] == "manual_recovery_required" for x in compensation.values()) else "failed_compensated"
        else: compensation, outcome = {"status": "not_required"}, "verified"
        consumed = {"task_id": TASK_ID, "slice": SLICE, "source_sha256": p["source_sha"],
            "state": "retry_consumed" if prior_failed else "consumed", "prepared_sha256": prepared_digest, "outcome": outcome,
            "problems": problems, "official": official, "check_implementation": check,
            "delivery_control_dry_run": dry, "task_observed": task_post,
            "session_observed": session_post, "compensation": compensation}
        append(p["log"], "retry_consumed" if prior_failed else "consumed", consumed)  # type: ignore[arg-type]
        if problems: raise Fail(f"bootstrap consumed with outcome={outcome}: {problems}")
        return consumed


def read_status(p: dict[str, Path | str]) -> dict[str, Any]:
    with locked(p["lock"]):  # type: ignore[arg-type]
        if not Path(p["log"]).exists(): return {"state": "absent", "events": 0}
        items = chain(p["log"]); historical_source = bind_chain(p, items)  # type: ignore[arg-type]
        return {"state": items[-1][0]["event"], "events": len(items),
                "event_sha256": [x[2] for x in items],
                "outcome": items[-1][0]["payload"].get("outcome"),
                "historical_verified_consumed_source": historical_source,
                "current_verifier_source": {"path": str(SOURCE), "sha256": p["source_sha"]}}


def load_module(path: Path, label: str):
    regular(path)
    name = f"bootstrap_{label}_{digest(str(path.resolve()).encode())[:16]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Fail(f"cannot load {label}: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules[name] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        raise Fail(f"cannot load {label}: {exc}") from exc
    return module


def current_detail_evidence(p: dict[str, Path | str]) -> dict[str, Any]:
    root, task = p["root"], p["task"]
    detail_check = must(command(root, sys.executable, str(p["gate"]), "detail", str(TASK)), "detail Gate")  # type: ignore[arg-type]
    implementation_check = must(
        command(root, sys.executable, str(p["gate"]), "check-implementation", str(TASK)),
        "check-implementation",
    )  # type: ignore[arg-type]
    digest_check = must(
        command(root, sys.executable, str(p["gate"]), "digest", "detail", str(TASK)),
        "detail digest",
    )  # type: ignore[arg-type]
    detail_digest = digest_check["stdout"].strip()
    if not SHA.fullmatch(detail_digest):
        raise Fail("live Detail digest is invalid")
    task_data = load(p["task_json"])  # type: ignore[arg-type]
    gates = task_data.get("guru_gates")
    detail = gates.get("detail") if isinstance(gates, dict) else None
    if not (
        isinstance(detail, dict)
        and detail.get("artifact_digest") == detail_digest
        and detail.get("confirmed_by")
        and detail.get("confirmed_at")
        and detail.get("mode") != "soft"
        and detail.get("via") != "agent"
    ):
        raise Fail("current strict Detail confirmation is missing or stale")
    review_runs = gates.get("review_runs") if isinstance(gates, dict) else None
    all_detail_runs = review_runs.get("detail") if isinstance(review_runs, dict) else None
    current_runs = [
        row for row in (all_detail_runs if isinstance(all_detail_runs, list) else [])
        if isinstance(row, dict) and row.get("artifact_digest") == detail_digest
    ]
    latest = current_runs[-2:]
    if not (
        len(latest) == 2
        and len({row.get("run_id") for row in latest}) == 2
        and all(
            row.get("run_id")
            and "clean-context" in str(row.get("reviewer", "")).lower()
            and row.get("result") == "clean"
            and row.get("max_severity") in ("none", "low")
            and row.get("deletion_audit")
            for row in latest
        )
    ):
        raise Fail("current Detail double-clean/deletion audit is missing")
    return {
        "artifact_digest": detail_digest,
        "confirmation_sha256": digest(canon(detail)),
        "review_run_ids": [row["run_id"] for row in latest],
        "review_runs_sha256": digest(canon(latest)),
        "commands": {
            "detail": detail_check,
            "check_implementation": implementation_check,
            "digest": digest_check,
        },
        "task_status": task_data.get("status"),
        "task_path": Path(task).resolve().relative_to(Path(root).resolve()).as_posix(),
    }


def current_artifact_binding(p: dict[str, Path | str]) -> tuple[dict[str, Any], dict[str, Any]]:
    root, task = Path(p["root"]), Path(p["task"])
    packet_path = Path(p["packet"])
    risk_path = task / "risk-packets" / f"{SLICE}.json"
    envelope_path = task / "execution-envelopes" / f"{SLICE}.json"
    for path in (risk_path, envelope_path):
        regular(path)
    task_data, packet = load(Path(p["task_json"])), load(packet_path)
    risk, envelope = load(risk_path), load(envelope_path)
    wrapper = load_module(Path(p["wrapper"]), "guru_task")
    gate_digest = wrapper._gate_digest(task_data, task)
    request = wrapper.StartRequest(
        task_dir=task,
        selected_slice_id=SLICE,
        official_task_py=Path(p["task_py"]),
        expected_gate_digest=gate_digest,
        expected_slice_packet_digest=file_hash(packet_path),
        expected_risk_packet_digest=file_hash(risk_path),
        expected_envelope_digest=file_hash(envelope_path),
        expected_attestation_digest=envelope.get("confirmation_attestation_digest"),
    )
    try:
        binding = wrapper._artifact_binding(request, root)
    except Exception as exc:
        raise Fail(f"live risk/envelope/inventory binding failed: {exc}") from exc
    return binding, {
        "gate_digest": binding["gate_digest"],
        "slice_packet_digest": binding["slice_packet_digest"],
        "risk_packet_digest": binding["risk_packet_digest"],
        "execution_envelope_digest": binding["envelope_digest"],
        "decision_universe_digest": risk.get("decision_universe_digest"),
        "decision_set_digest": risk.get("decision_set_digest"),
        "decision_count": len(risk.get("decision_items", [])) if isinstance(risk.get("decision_items"), list) else None,
        "confirmation_required": risk.get("confirmation_required"),
        "packet_invariant_ids": [
            row.get("invariant_id") for row in packet.get("invariants", []) if isinstance(row, dict)
        ],
        "wrapper_source_sha256": file_hash(Path(p["wrapper"])),
    }


def channel_project_key(root: Path) -> str:
    slashed = re.sub(r"[\\/_]", "-", str(root.resolve()))
    return re.sub(r"[^A-Za-z0-9.-]", "-", slashed)


def jsonl_objects(path: Path, label: str) -> list[dict[str, Any]]:
    regular(path)
    rows = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise Fail(f"{label} JSONL is invalid at line {line_number}") from exc
        if not isinstance(row, dict):
            raise Fail(f"{label} JSONL row {line_number} is not an object")
        rows.append(row)
    if not rows:
        raise Fail(f"{label} JSONL is empty")
    return rows


def codex_control_plane_capture(
    p: dict[str, Path | str],
    record: dict[str, Any],
    packet: dict[str, Any],
    target_digest: str,
    review_module: Any,
) -> dict[str, Any]:
    root, task = Path(p["root"]).resolve(), Path(p["task"]).resolve()
    channel, worker = record.get("channel"), record.get("worker")
    run_id = record.get("run_id")
    if not (
        isinstance(channel, str)
        and SAFE_CHANNEL_NAME.fullmatch(channel)
        and isinstance(worker, str)
        and SAFE_CHANNEL_NAME.fullmatch(worker)
        and isinstance(run_id, str)
        and run_id.strip()
    ):
        raise Fail("bootstrap Codex review channel/worker identity is invalid")
    run_slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", run_id.strip().lower()).strip("-")[:40].strip("-") or "task"
    task_slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", task.name.strip().lower()).strip("-")[:70].strip("-") or "task"
    expected_channel = f"guru-{task_slug}-check-{run_slug}"
    expected_worker = f"check-codex-{run_slug}"
    if channel != expected_channel or worker != expected_worker:
        raise Fail("bootstrap Codex review channel/worker does not match the official run id")

    if "TRELLIS_CHANNEL_ROOT" in os.environ:
        raise Fail("bootstrap burn rejects redirected Trellis channel storage")
    channel_root = (Path.home() / ".trellis/channels").resolve()
    channel_dir = channel_root / channel_project_key(root) / channel
    directory(channel_root)
    directory(channel_dir.parent)
    directory(channel_dir)

    events_path = channel_dir / "events.jsonl"
    log_path = channel_dir / f"{worker}.log"
    thread_path = channel_dir / f"{worker}.thread-id"
    session_path = channel_dir / f"{worker}.session-id"
    for artifact in (events_path, log_path, thread_path, session_path):
        regular(artifact)

    thread_id = thread_path.read_text(encoding="utf-8").strip()
    session_id = session_path.read_text(encoding="utf-8").strip()
    try:
        parsed_thread_id = str(uuid.UUID(thread_id))
    except (ValueError, AttributeError) as exc:
        raise Fail("bootstrap Codex review thread id is invalid") from exc
    if thread_id != parsed_thread_id or session_id != thread_id:
        raise Fail("bootstrap Codex review thread/session binding is invalid")

    metadata_rows, initialize_rows, thread_started_rows, completed_rows = [], [], [], []
    for raw in log_path.read_text(encoding="utf-8", errors="strict").splitlines():
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        result = row.get("result")
        if row.get("id") == 2 and isinstance(result, dict) and isinstance(result.get("thread"), dict):
            metadata_rows.append(result)
        if row.get("id") == 1 and isinstance(result, dict) and isinstance(result.get("userAgent"), str):
            initialize_rows.append(result)
        if row.get("method") == "thread/started" and isinstance(row.get("params"), dict):
            thread_started_rows.append(row["params"])
        if row.get("method") == "turn/completed":
            completed_rows.append(row)
    if not (
        len(metadata_rows) == 1
        and len(initialize_rows) == 1
        and len(thread_started_rows) == 1
        and len(completed_rows) == 1
    ):
        raise Fail("bootstrap Codex raw control-plane capture is incomplete or multi-turn")

    metadata, initialized = metadata_rows[0], initialize_rows[0]
    thread = metadata["thread"]
    expected_cwd = str(root)
    thread_path_raw = thread.get("path")
    if not isinstance(thread_path_raw, str) or not thread_path_raw.strip():
        raise Fail("bootstrap Codex session path is missing")
    codex_home = (Path.home() / ".codex").resolve()
    session_root = (codex_home / "sessions").resolve()
    session_path = Path(thread_path_raw).expanduser().resolve()
    try:
        session_path.relative_to(session_root)
    except ValueError as exc:
        raise Fail("bootstrap Codex session is outside the official session store") from exc
    regular(session_path)
    session_meta_rows = []
    for line_number, raw in enumerate(session_path.read_text(encoding="utf-8", errors="strict").splitlines(), 1):
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise Fail(f"bootstrap Codex session JSONL is invalid at line {line_number}") from exc
        if isinstance(row, dict) and row.get("type") == "session_meta" and isinstance(row.get("payload"), dict):
            session_meta_rows.append(row["payload"])
    if len(session_meta_rows) != 1:
        raise Fail("bootstrap Codex session metadata is missing or duplicated")
    session_meta = session_meta_rows[0]
    thread_started = thread_started_rows[0].get("thread")
    completed = completed_rows[0].get("params")
    instruction_sources = metadata.get("instructionSources")
    regular(root / "AGENTS.md")
    if not (
        thread.get("id") == thread_id
        and thread.get("sessionId") == session_id
        and thread.get("parentThreadId") is None
        and thread.get("forkedFromId") is None
        and thread.get("ephemeral") is False
        and thread.get("cwd") == expected_cwd
        and metadata.get("cwd") == expected_cwd
        and isinstance(metadata.get("model"), str)
        and metadata["model"].strip()
        and isinstance(metadata.get("modelProvider"), str)
        and metadata["modelProvider"].strip()
        and thread.get("modelProvider") == metadata.get("modelProvider")
        and isinstance(thread.get("cliVersion"), str)
        and thread["cliVersion"].strip()
        and isinstance(initialized.get("userAgent"), str)
        and initialized["userAgent"].startswith(f"trellis-channel/{thread['cliVersion']} ")
        and "(trellis-channel;" in initialized["userAgent"]
        and Path(str(initialized.get("codexHome", ""))).expanduser().resolve() == codex_home
        and initialized.get("platformFamily") == "unix"
        and thread.get("source") == "vscode"
        and metadata.get("runtimeWorkspaceRoots") == [expected_cwd]
        and isinstance(instruction_sources, list)
        and str(root / "AGENTS.md") in instruction_sources
        and metadata.get("approvalPolicy") == "never"
        and isinstance(thread_started, dict)
        and thread_started.get("id") == thread_id
        and thread_started.get("sessionId") == session_id
        and thread_started.get("cwd") == expected_cwd
        and isinstance(completed, dict)
        and completed.get("threadId") == thread_id
        and isinstance(completed.get("turn"), dict)
        and completed["turn"].get("status") == "completed"
        and session_meta.get("id") == thread_id
        and session_meta.get("session_id") == session_id
        and session_meta.get("cwd") == expected_cwd
        and session_meta.get("originator") == "trellis-channel"
        and session_meta.get("cli_version") == thread.get("cliVersion")
        and session_meta.get("source") == thread.get("source")
        and session_meta.get("model_provider") == metadata.get("modelProvider")
    ):
        raise Fail("bootstrap Codex thread/start metadata binding is invalid")

    events = jsonl_objects(events_path, "bootstrap Codex channel events")
    sequences = [row.get("seq") for row in events]
    if not all(isinstance(seq, int) and seq > 0 for seq in sequences) or sequences != sorted(set(sequences)):
        raise Fail("bootstrap Codex channel event sequence is invalid")
    creates = [row for row in events if row.get("kind") == "create"]
    spawned = [row for row in events if row.get("kind") == "spawned"]
    prompts = [
        row for row in events
        if row.get("kind") == "message" and row.get("by") == "main"
    ]
    started = [
        row for row in events
        if row.get("kind") == "turn_started"
    ]
    worker_messages = [
        row for row in events
        if row.get("kind") == "message" and row.get("by") == worker
    ]
    done = [row for row in events if row.get("kind") == "done"]
    finished = [
        row for row in events
        if row.get("kind") == "turn_finished"
    ]
    terminal_failures = [row for row in events if row.get("kind") in {"error", "killed"}]
    file_changes = [
        row for row in events
        if row.get("kind") == "progress"
        and row.get("by") == worker
        and isinstance(row.get("detail"), dict)
        and row["detail"].get("kind") == "file_change"
    ]
    expected_injected_files = {
        (task / "prd.md").resolve(),
        (task / "design.md").resolve(),
        (task / "implement.md").resolve(),
        Path(p["packet"]).resolve(),
    }
    raw_files, raw_manifests = spawned[0].get("files") if len(spawned) == 1 else None, spawned[0].get("manifests") if len(spawned) == 1 else None
    if not (
        isinstance(raw_files, list)
        and all(isinstance(item, str) and item.strip() for item in raw_files)
        and isinstance(raw_manifests, list)
        and all(isinstance(item, str) and item.strip() for item in raw_manifests)
    ):
        raise Fail("bootstrap Codex spawned artifact manifest is invalid")
    injected_files = {
        (Path(item) if Path(item).is_absolute() else root / item).resolve()
        for item in raw_files
    }
    injected_manifests = {
        (Path(item) if Path(item).is_absolute() else root / item).resolve()
        for item in raw_manifests
    }
    if not (
        len(creates) == 1
        and creates[0].get("by") == "main"
        and creates[0].get("cwd") == expected_cwd
        and Path(str(creates[0].get("task", ""))).resolve() == task
        and creates[0].get("scope") == "project"
        and creates[0].get("type") == "chat"
        and creates[0].get("origin") == "cli"
        and creates[0].get("description") == f"Guru implementation-review {task.name}"
        and len(spawned) == 1
        and spawned[0].get("by") == "main"
        and spawned[0].get("as") == worker
        and spawned[0].get("provider") == "codex"
        and spawned[0].get("agent") == "check"
        and spawned[0].get("inboxPolicy") == "explicitOnly"
        and isinstance(spawned[0].get("pid"), int)
        and spawned[0]["pid"] > 0
        and expected_injected_files <= injected_files
        and (task / "check.jsonl").resolve() in injected_manifests
        and len(prompts) == 1
        and prompts[0].get("to") == worker
        and prompts[0].get("origin") == "cli"
        and len(started) == 1
        and started[0].get("by") == worker
        and started[0].get("worker") == worker
        and worker_messages
        and len(done) == 1
        and done[0].get("by") == worker
        and len(finished) == 1
        and finished[0].get("by") == worker
        and finished[0].get("worker") == worker
        and finished[0].get("outcome") == "done"
        and not terminal_failures
        and not file_changes
    ):
        raise Fail("bootstrap Codex channel is not one clean check-only turn")
    prompt_seq, started_seq = prompts[0]["seq"], started[0]["seq"]
    done_seq, finished_seq = done[0]["seq"], finished[0]["seq"]
    final_message = max(worker_messages, key=lambda row: row["seq"])
    final_message_seq = final_message["seq"]
    if not (
        creates[0]["seq"] < spawned[0]["seq"] < prompt_seq < started_seq
        and all(started_seq < row["seq"] <= final_message_seq for row in worker_messages)
        and final_message_seq < done_seq < finished_seq
        and started[0].get("inputSeq") == prompt_seq
        and started[0].get("turnId") == f"msg:{prompt_seq}"
        and finished[0].get("inputSeq") == prompt_seq
        and finished[0].get("turnId") == f"msg:{prompt_seq}"
    ):
        raise Fail("bootstrap Codex channel event causality is invalid")
    prompt = prompts[0].get("text")
    final_text = final_message.get("text")
    required_prompt_facts = (
        f"Active task: {task}",
        f"review_target=slice:{SLICE}",
        "target_digest_source=index",
        f"reviewed_target_digest={target_digest}",
    )
    if not isinstance(prompt, str):
        raise Fail("bootstrap Codex check-only invocation binding is incomplete")
    prompt_lines = prompt.splitlines()
    if (
        any(prompt_lines.count(fact) != 1 for fact in required_prompt_facts)
        or prompt.count("Implementation-review check-only required evidence path.") != 1
        or "Do not implement or edit files" not in prompt
    ):
        raise Fail("bootstrap Codex check-only invocation binding is incomplete")
    contract_lines = [
        line.removeprefix("review_invocation_contract=")
        for line in prompt_lines
        if line.startswith("review_invocation_contract=")
    ]
    if len(contract_lines) != 1:
        raise Fail("bootstrap Codex invocation contract is missing or duplicated")
    try:
        invocation_contract = json.loads(contract_lines[0])
    except json.JSONDecodeError as exc:
        raise Fail("bootstrap Codex invocation contract is invalid") from exc
    results = record.get("deterministic_results")
    target_paths = packet.get("target_paths")
    expected_invocation_contract = {
        "schema_version": 1,
        "action": "implementation-review",
        "review_mode": "check_only",
        "run_id": run_id,
        "channel": channel,
        "worker": worker,
        "supervisor_source": "guru-template/overlay/verify/guru_supervise.py",
        "supervisor_source_sha256": file_hash(Path(p["template_supervisor"])),
        "slice_id": SLICE,
        "review_target": f"slice:{SLICE}",
        "digest_source": "index",
        "reviewed_target_digest": target_digest,
        "target_paths_sha256": digest(canon(target_paths)),
        "deterministic_status": "passed",
        "deterministic_results_sha256": digest(canon(results)),
        "implement_provider": "codex",
        "review_provider": "codex",
        "check_provider": "codex",
        "provider_override_source": "cli_same_provider",
        "same_provider_user_quote": BOOTSTRAP_REVIEW_AUTHORIZATION["user_directive"],
        "same_provider": True,
        "staged": True,
    }
    if invocation_contract != expected_invocation_contract:
        raise Fail("bootstrap Codex invocation contract does not match the official review")
    if not isinstance(final_text, str) or not final_text.strip():
        raise Fail("bootstrap Codex final worker verdict is missing")
    verdict_keys = (
        "review_result", "route_class", "review_target", "review_provider",
        "deterministic_checks", "dirty_scope", "invariant_coverage",
    )
    final_lines = [line.strip() for line in final_text.splitlines()]
    if any(sum(line.startswith(f"{key}=") for line in final_lines) != 1 for key in verdict_keys):
        raise Fail("bootstrap Codex final worker verdict is duplicated or incomplete")
    verdict = review_module.parse_verdict_block(final_text)
    try:
        normalized, failure = review_module.normalize_review_record(verdict, {
            "mode": "supervisor",
            "packet": packet,
            "implement_provider": "codex",
            "supervisor_deterministic_status": "passed",
            "deterministic_results": results,
            "run_id": run_id,
            "slice_id": SLICE,
            "review_target": f"slice:{SLICE}",
            "target_paths": target_paths,
            "channel": channel,
            "worker": worker,
            "check_provider": "codex",
            "provider_override_source": "cli_same_provider",
            "same_provider_user_quote": BOOTSTRAP_REVIEW_AUTHORIZATION["user_directive"],
            "high_risk_review_provider_policy": "codex",
            "review_target_kind": "slice",
            "reviewed_target_digest": target_digest,
        })
    except Exception as exc:
        raise Fail(f"bootstrap Codex final verdict normalization failed: {exc}") from exc
    if failure is not None:
        raise Fail(f"bootstrap Codex final worker verdict is not clean: {failure}")
    normalized["message"] = (
        "same-provider implementation-review authorized by user quote: "
        + BOOTSTRAP_REVIEW_AUTHORIZATION["user_directive"]
    )
    if canon(normalized) != canon(record):
        raise Fail("bootstrap Codex final worker verdict does not match the review record")

    return {
        "capture_kind": "codex_channel_control_plane_audit_v2",
        "identity_claim": "lineage_only_not_reviewer_or_context_identity",
        "independence_claim": "none",
        "trusted_review_envelope_eligible": False,
        "channel": channel,
        "worker": worker,
        "thread_id": thread_id,
        "session_id": session_id,
        "model": metadata["model"],
        "model_provider": metadata["modelProvider"],
        "cli_version": thread["cliVersion"],
        "user_agent": initialized["userAgent"],
        "cwd": expected_cwd,
        "channel_store_ref": f"{channel_project_key(root)}/{channel}",
        "codex_session_ref": session_path.relative_to(codex_home).as_posix(),
        "codex_session_sha256": file_hash(session_path),
        "raw_control_plane_sha256": file_hash(log_path),
        "channel_events_sha256": file_hash(events_path),
        "event_sequence_sha256": digest(canon(events)),
        "invocation_contract_sha256": digest(canon(invocation_contract)),
        "final_message_seq": final_message_seq,
        "final_message_sha256": digest(final_text.encode("utf-8")),
        "verdict_fields_sha256": digest(canon(verdict)),
        "normalized_record_sha256": digest(canon(normalized)),
        "spawn_seq": spawned[0]["seq"],
        "prompt_seq": prompts[0]["seq"],
        "terminal_seq": finished[0]["seq"],
    }


def implementation_review_evidence(
    p: dict[str, Path | str],
    run_id: str,
    authorization: dict[str, Any],
) -> dict[str, Any]:
    task, root = Path(p["task"]), Path(p["root"])
    packet = load(Path(p["packet"]))
    review_path = task / "review-records/implementation-reviews.jsonl"
    regular(review_path)
    records = []
    for raw in review_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise Fail("implementation review JSONL is invalid") from exc
        if isinstance(record, dict) and record.get("run_id") == run_id:
            records.append(record)
    if len(records) != 1:
        raise Fail("implementation review run id is missing or duplicated")
    record = records[0]
    target_paths = packet.get("target_paths")
    expected = {
        "slice_id": SLICE,
        "review_target": f"slice:{SLICE}",
        "review_result": "clean",
        "route_class": "none",
        "deterministic_checks": "passed",
        "invariant_coverage": "all_passed",
        "supervisor_failure": "none",
        "required_satisfied": True,
        "target_paths": target_paths,
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise Fail("implementation review is not a current required clean slice review")
    if record.get("supplemental") is True:
        raise Fail("supplemental implementation review cannot satisfy required review")
    if record.get("dirty_scope") not in ("clean", "isolated"):
        raise Fail("implementation review dirty scope is not isolated")
    providers = (record.get("implement_provider"), record.get("review_provider"), record.get("check_provider"))
    expected_message = "same-provider implementation-review authorized by user quote: " + authorization["user_directive"]
    if not (
        authorization == BOOTSTRAP_REVIEW_AUTHORIZATION
        and providers == ("codex", "codex", "codex")
        and record.get("provider_override_source") == "cli_same_provider"
        and record.get("same_provider_user_quote") == authorization["user_directive"]
        and record.get("high_risk_review_provider_policy") == "codex"
        and record.get("review_target_kind") == "slice"
        and record.get("message") == expected_message
    ):
        raise Fail("implementation review does not match the exact Codex bootstrap authorization")
    checks = packet.get("deterministic_checks")
    results = record.get("deterministic_results")
    if not isinstance(checks, list) or not isinstance(results, list) or len(results) != len(checks):
        raise Fail("implementation review deterministic check set is incomplete")
    for declared, result in zip(checks, results):
        if not (
            isinstance(result, dict)
            and result.get("command") == declared
            and result.get("exit_code") == 0
            and result.get("timed_out") is False
        ):
            raise Fail("implementation review deterministic check result is stale or failed")
    review_module = load_module(Path(p["review_record"]), "guru_review_record")
    try:
        index_target_digest = review_module.target_snapshot_digest(str(root), target_paths, "index")
        worktree_target_digest = review_module.target_snapshot_digest(str(root), target_paths, "worktree")
    except Exception as exc:
        raise Fail(f"cannot recompute implementation review target digest: {exc}") from exc
    target_digest = record.get("reviewed_target_digest")
    if not (
        isinstance(target_digest, str)
        and SHA.fullmatch(target_digest)
        and target_digest == index_target_digest == worktree_target_digest
    ):
        raise Fail("implementation review target digest is stale")
    control_plane_capture = codex_control_plane_capture(
        p, record, packet, target_digest, review_module
    )
    return {
        "run_id": run_id,
        "record_sha256": digest(canon(record)),
        "reviewed_target_digest": target_digest,
        "index_target_digest": index_target_digest,
        "worktree_target_digest": worktree_target_digest,
        "deterministic_results_sha256": digest(canon(results)),
        "target_paths_sha256": digest(canon(target_paths)),
        "providers": {
            "implement": providers[0], "review": providers[1], "check": providers[2],
        },
        "bootstrap_review_authorization": authorization,
        "control_plane_capture": control_plane_capture,
    }


def run_capability_probe(
    p: dict[str, Path | str],
    binding: dict[str, Any],
) -> dict[str, Any]:
    root, live_task = Path(p["root"]), Path(p["task"])
    focused_results = []
    for declared in FIXED_CAPABILITY_CHECKS:
        result = command(root, "/bin/sh", "-lc", declared)
        count = re.search(r"Ran\s+([1-9][0-9]*)\s+tests?", result["stdout"] + result["stderr"])
        if result["returncode"] != 0 or count is None:
            raise Fail(f"live wrapper capability check failed: {declared}")
        result["declared_command"] = declared
        result["test_count"] = int(count.group(1))
        focused_results.append(result)
    with tempfile.TemporaryDirectory(prefix="guru-bootstrap-capability-") as tmp:
        probe_root = Path(tmp)
        (probe_root / ".git").mkdir()
        shutil.copytree(root / ".trellis/scripts", probe_root / ".trellis/scripts")
        shutil.copytree(root / "guru-template/overlay/hooks", probe_root / "guru-template/overlay/hooks")
        shutil.copytree(root / "guru-template/overlay/verify", probe_root / "guru-template/overlay/verify")
        probe_task = probe_root / TASK
        shutil.copytree(live_task, probe_task)
        for transient in (probe_task / ".guru-start.lock", probe_task / "start-attempts"):
            if transient.is_dir():
                shutil.rmtree(transient)
            elif transient.exists():
                transient.unlink()
        task_data = load(probe_task / "task.json")
        task_data["status"] = "planning"
        (probe_task / "task.json").write_text(
            json.dumps(task_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        config = probe_root / ".trellis/config.yaml"
        config.write_text(
            "hooks:\n"
            "  after_start:\n"
            f"    - \"python3 {Path(p['after_start']).resolve()}\"\n",
            encoding="utf-8",
        )
        args = [
            sys.executable, str(Path(p["wrapper"])), "start", str(probe_task),
            "--slice", SLICE,
            "--official-task-py", str(probe_root / ".trellis/scripts/task.py"),
            "--gate-digest", binding["gate_digest"],
            "--slice-packet-digest", binding["slice_packet_digest"],
            "--risk-packet-digest", binding["risk_packet_digest"],
            "--envelope-digest", binding["envelope_digest"],
        ]
        if binding.get("attestation_digest"):
            args.extend(["--attestation-digest", binding["attestation_digest"]])
        probe = command(probe_root, *args, env={
            "TRELLIS_CONTEXT_ID": "", "CODEX_THREAD_ID": "", "CODEX_SESSION_ID": "",
        })
        if probe["returncode"] != 0:
            raise Fail(f"isolated guarded-start capability probe failed: {probe['stderr'].strip()}")
        attempts = list((probe_task / "start-attempts").glob("*.json"))
        if len(attempts) != 1:
            raise Fail("isolated guarded-start capability probe did not create one StartAttempt")
        attempt_path = attempts[0]
        attempt = load(attempt_path)
        hook = attempt.get("hook_outcome")
        if not (
            attempt.get("task_id") == TASK_ID
            and attempt.get("selected_slice_id") == SLICE
            and attempt.get("state") == "verified"
            and attempt.get("capability") == EXPECTED_ATTEMPT_CAPABILITY
            and isinstance(attempt.get("pre_snapshot"), dict)
            and attempt["pre_snapshot"].get("binding") == binding
            and isinstance(hook, dict)
            and hook.get("status") == "observed"
        ):
            raise Fail("isolated guarded-start StartAttempt/capability evidence is invalid")
        return {
            "probe_kind": "isolated_live_guarded_start",
            "wrapper_source_sha256": file_hash(Path(p["wrapper"])),
            "after_start_source_sha256": file_hash(Path(p["after_start"])),
            "focused_check_results": focused_results,
            "focused_check_results_sha256": digest(canon(focused_results)),
            "start_attempt_file_sha256": file_hash(attempt_path),
            "start_attempt": attempt,
            "probe_command": probe,
        }


def verify_burn_manifest(evidence: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    expected = {
        "schema_version": 3,
        "task_id": TASK_ID,
        "selected_slice_id": SLICE,
        "wrapper_entry_capability": "enforced_guarded_entry_only",
        "after_start_capability": "compensated",
        "direct_official_capability": "advisory",
        "decision_inventory_scope": "selected_slice_only",
        "later_slice_authority": "supervisor_fail_closed",
    }
    if set(evidence) != set(expected) | {"implementation_review_run_id", "bootstrap_review_authorization"}:
        raise Fail("burn evidence schema is not exact v3")
    if any(evidence.get(key) != value for key, value in expected.items()):
        raise Fail("burn evidence identity/capability/scope mismatch")
    run_id = evidence.get("implementation_review_run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise Fail("burn evidence implementation review id is missing")
    authorization = evidence.get("bootstrap_review_authorization")
    if authorization != BOOTSTRAP_REVIEW_AUTHORIZATION:
        raise Fail("burn evidence bootstrap review authorization is invalid")
    return run_id, dict(authorization)


def burn(p: dict[str, Path | str], evidence_path: Path) -> dict[str, Any]:
    with locked(p["lock"]):  # type: ignore[arg-type]
        items = chain(p["log"]); historical_source = bind_chain(p, items)  # type: ignore[arg-type]
        if items[-1][0]["event"] == "burned": raise Fail("bootstrap already burned")
        if items[-1][0]["event"] not in ("consumed", "retry_consumed") or items[-1][0]["payload"].get("outcome") != "verified":
            raise Fail("verified consumed event required")
        evidence = load(evidence_path if evidence_path.is_absolute() else p["root"] / evidence_path)  # type: ignore[operator]
        review_run_id, review_authorization = verify_burn_manifest(evidence)
        detail = current_detail_evidence(p)
        if detail.get("task_status") != "in_progress":
            raise Fail("bootstrap burn requires task status in_progress")
        binding, artifacts = current_artifact_binding(p)
        if detail["artifact_digest"] != load(Path(p["task"]) / "risk-packets" / f"{SLICE}.json").get("detail_artifact_digest"):
            raise Fail("risk packet is not bound to the live confirmed Detail digest")
        review = implementation_review_evidence(p, review_run_id, review_authorization)
        capability = run_capability_probe(p, binding)
        final_detail = current_detail_evidence(p)
        final_binding, final_artifacts = current_artifact_binding(p)
        final_review = implementation_review_evidence(p, review_run_id, review_authorization)
        final_items = chain(p["log"])  # type: ignore[arg-type]
        final_historical_source = bind_chain(p, final_items)
        if (
            file_hash(Path(p["root"]) / SOURCE) != p["source_sha"]
            or final_items != items
            or final_historical_source != historical_source
            or final_detail != detail
            or final_binding != binding
            or final_artifacts != artifacts
            or final_review != review
        ):
            raise Fail("burn inputs changed during final verification")
        current_source = {"path": str(SOURCE), "sha256": p["source_sha"]}
        payload = {"task_id": TASK_ID, "slice": SLICE, "source_sha256": p["source_sha"],
            "state": "burned", "consumed_sha256": items[-1][2], "evidence": evidence,
            "evidence_sha256": digest(canon(evidence)),
            "historical_verified_consumed_source": historical_source,
            "current_verifier_source": current_source,
            "verified_delivery_control": {
                "detail": detail,
                "artifacts": artifacts,
                "implementation_review": review,
                "capability_probe": capability,
            },
            "verified_delivery_control_sha256": digest(canon({
                "detail": detail,
                "artifacts": artifacts,
                "implementation_review": review,
                "capability_probe": capability,
            })),
            "future_slice_authority": "supervisor_fail_closed",
            "future_policy": "reject_all_reuse"}
        append(p["log"], "burned", payload)  # type: ignore[arg-type]
        return payload


def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "status", "burn"):
        cmd = sub.add_parser(name); cmd.add_argument("task"); cmd.add_argument("--slice", required=True); cmd.add_argument("--source-sha256", required=True)
        if name == "burn": cmd.add_argument("--evidence", required=True)
    args = parser.parse_args()
    try:
        p = paths(args.task, args.slice, args.source_sha256)
        result = run(p) if args.command == "run" else burn(p, Path(args.evidence)) if args.command == "burn" else read_status(p)
    except Fail as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr); return 2
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
