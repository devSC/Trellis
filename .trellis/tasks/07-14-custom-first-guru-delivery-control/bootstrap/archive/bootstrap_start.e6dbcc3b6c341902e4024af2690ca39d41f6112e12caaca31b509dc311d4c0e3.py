#!/usr/bin/env python3
"""Audited one-shot start for this task's delivery-control bootstrap only."""

from __future__ import annotations

import argparse
import ast
import base64
import contextlib
import fcntl
import hashlib
import json
import os
import re
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
        "supervisor": root / ".trellis/scripts/guru/guru_supervise.py"}
    for key in ("task_json", "contract", "packet", "task_py", "gate", "supervisor"): regular(result[key])  # type: ignore[arg-type]
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
            ".trellis/scripts/guru/guru_supervise.py"]
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


def bind_chain(p: dict[str, Path | str], items: list[tuple[dict[str, Any], bytes, str]]) -> None:
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
        items = chain(p["log"]); bind_chain(p, items)  # type: ignore[arg-type]
        return {"state": items[-1][0]["event"], "events": len(items),
                "event_sha256": [x[2] for x in items],
                "outcome": items[-1][0]["payload"].get("outcome")}


def burn(p: dict[str, Path | str], evidence_path: Path) -> dict[str, Any]:
    with locked(p["lock"]):  # type: ignore[arg-type]
        items = chain(p["log"]); bind_chain(p, items)  # type: ignore[arg-type]
        if items[-1][0]["event"] == "burned": raise Fail("bootstrap already burned")
        if items[-1][0]["event"] not in ("consumed", "retry_consumed") or items[-1][0]["payload"].get("outcome") != "verified":
            raise Fail("verified consumed event required")
        evidence = load(evidence_path if evidence_path.is_absolute() else p["root"] / evidence_path)  # type: ignore[operator]
        expected = {"task_id": TASK_ID, "selected_slice_id": SLICE, "source_sha256": p["source_sha"],
            "wrapper_entry_capability": "enforced_guarded_entry_only", "direct_official_capability": "advisory"}
        if any(evidence.get(k) != v for k, v in expected.items()) or evidence.get("after_start_capability") not in ("compensated", "advisory", "unavailable"):
            raise Fail("burn evidence identity/capability mismatch")
        for key in ("verified_delivery_control_target_digest", "deterministic_check_summary_digest", "implementation_review_record_digest", "wrapper_capability_test_digest"):
            if not SHA.fullmatch(str(evidence.get(key, ""))): raise Fail(f"invalid burn digest: {key}")
        payload = {"task_id": TASK_ID, "slice": SLICE, "source_sha256": p["source_sha"],
            "state": "burned", "consumed_sha256": items[-1][2], "evidence": evidence,
            "evidence_sha256": digest(canon(evidence)), "future_policy": "reject_all_reuse"}
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
