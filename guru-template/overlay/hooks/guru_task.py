#!/usr/bin/env python3
"""Core-free guarded wrapper around the checkout-local Trellis task start."""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERIFY_DIR = Path(__file__).resolve().parents[1] / "verify"
sys.path.insert(0, str(VERIFY_DIR))
import guru_contract  # noqa: E402

PASS = 0
BLOCK = 2
HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
LIVE_RUN_STATES = {"planned", "starting", "running", "cancelling", "cleanup_required"}
DECISION_INVENTORY_START = guru_contract.DECISION_INVENTORY_START
DECISION_INVENTORY_END = guru_contract.DECISION_INVENTORY_END


@dataclass(frozen=True)
class StartRequest:
    task_dir: Path
    selected_slice_id: str
    official_task_py: Path
    expected_gate_digest: str
    expected_slice_packet_digest: str
    expected_risk_packet_digest: str
    expected_envelope_digest: str
    expected_attestation_digest: str | None = None
    expected_task_status: str = "planning"
    expected_context_key: str | None = None
    expected_active_task: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _fsync_parent(path: Path) -> None:
    try:
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    try:
        with open(tmp, "xb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        _fsync_parent(path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _write_json_atomic(path: Path, payload: dict) -> None:
    _write_bytes_atomic(path, (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _write_json_exclusive(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        raw = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_parent(path)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_root(task_dir: Path) -> Path:
    current = task_dir.resolve()
    for parent in (current, *current.parents):
        if (parent / ".trellis").is_dir() and (parent / ".git").exists():
            return parent
    raise RuntimeError("cannot find repo root")


def _task_ref(task_dir: Path, root: Path) -> str:
    try:
        return task_dir.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("task directory escapes repository") from exc


def _context_key(request: StartRequest, root: Path) -> str | None:
    resolver_path = request.official_task_py.resolve().parent / "common" / "active_task.py"
    if not resolver_path.is_file():
        raise ValueError("CapabilityInsufficient: checkout-local active_task resolver missing")
    module_name = f"guru_official_active_task_{hashlib.sha256(str(resolver_path).encode()).hexdigest()[:16]}"
    spec = importlib.util.spec_from_file_location(module_name, resolver_path)
    if spec is None or spec.loader is None:
        raise ValueError("CapabilityInsufficient: cannot load checkout-local active_task resolver")
    module = importlib.util.module_from_spec(spec)
    previous_argv = sys.argv
    try:
        sys.argv = [str(request.official_task_py), "start", str(request.task_dir)]
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        resolved = module.resolve_context_key()
    finally:
        sys.argv = previous_argv
        sys.modules.pop(module_name, None)
    if request.expected_context_key is not None and resolved != request.expected_context_key:
        raise ValueError(
            f"LifecycleCASMismatch: expected context key {request.expected_context_key!r}, "
            f"official resolver selected {resolved!r}"
        )
    return resolved


def _session_path(root: Path, context_key: str | None) -> Path | None:
    if not context_key:
        return None
    base = (root / ".trellis" / ".runtime" / "sessions").resolve()
    candidate = (base / f"{context_key}.json").resolve()
    if candidate.parent != base:
        raise ValueError("LifecycleCASMismatch: official context key escapes session directory")
    return candidate


def _file_image(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {"exists": False, "sha256": None, "bytes_b64": None}
    raw = path.read_bytes()
    return {
        "exists": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes_b64": base64.b64encode(raw).decode("ascii"),
    }


def _gate_digest(task_data: dict, task_dir: Path) -> str:
    contract = task_dir / "gate-contract.json"
    if not contract.is_file():
        raise ValueError("StartNotReady: gate-contract.json missing")
    return _digest({
        "guru_chain": task_data.get("guru_chain"),
        "require_req_uc": task_data.get("require_req_uc"),
        "guru_gates": {
            key: (task_data.get("guru_gates") or {}).get(key)
            for key in ("requirements", "detail", "review_runs")
        },
        "gate_contract_sha256": _sha256_file(contract),
    })


def _canonical_decision_universe(raw_items: Any, invariant_ids: list[str]) -> tuple[dict, ...]:
    try:
        return guru_contract.canonical_decision_universe(raw_items, invariant_ids)
    except guru_contract.ContractError as exc:
        raise ValueError(f"RiskPacketStale: {exc}") from exc


def _detail_gate_artifacts(task_dir: Path) -> list:
    gate_path = VERIFY_DIR / "guru_gate.py"
    module_name = f"guru_detail_gate_{hashlib.sha256(str(gate_path).encode()).hexdigest()[:16]}"
    spec = importlib.util.spec_from_file_location(module_name, gate_path)
    if spec is None or spec.loader is None:
        raise ValueError("CapabilityUnavailable: cannot load Guru detail artifact collector")
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.collect_gate_artifacts(str(task_dir), "detail", str(_repo_root(task_dir)))
    finally:
        sys.modules.pop(module_name, None)


def _detail_decision_universe(
    task_dir: Path,
    task_id: str,
    slice_id: str,
    invariant_ids: list[str],
) -> tuple[dict, ...]:
    try:
        loaded = guru_contract.load_detail_decision_inventory(
            str(task_dir),
            task_id,
            _detail_gate_artifacts(task_dir),
            expected_slice_id=slice_id,
        )
    except guru_contract.ContractError as exc:
        raise ValueError(f"RiskPacketStale: {exc}") from exc
    universe = loaded["decision_universe"]
    if {
        invariant
        for item in universe
        for invariant in item.get("invariant_ids", [])
    } - set(invariant_ids):
        raise ValueError("RiskPacketStale: selected slice invariant binding changed")
    return universe


def _artifact_binding(request: StartRequest, root: Path) -> dict:
    task_data = _read_json(request.task_dir / "task.json")
    task_id = str(task_data.get("id") or task_data.get("name") or request.task_dir.name)
    packet_path = request.task_dir / "slice-packets" / f"{request.selected_slice_id}.json"
    risk_path = request.task_dir / "risk-packets" / f"{request.selected_slice_id}.json"
    envelope_path = request.task_dir / "execution-envelopes" / f"{request.selected_slice_id}.json"
    for path in (packet_path, risk_path, envelope_path):
        if not path.is_file():
            raise ValueError(f"StartNotReady: required artifact missing: {path.name}")
    actual = {
        "gate_digest": _gate_digest(task_data, request.task_dir),
        "slice_packet_digest": _sha256_file(packet_path),
        "risk_packet_digest": _sha256_file(risk_path),
        "envelope_digest": _sha256_file(envelope_path),
    }
    expected = {
        "gate_digest": request.expected_gate_digest,
        "slice_packet_digest": request.expected_slice_packet_digest,
        "risk_packet_digest": request.expected_risk_packet_digest,
        "envelope_digest": request.expected_envelope_digest,
    }
    if any(not HEX_DIGEST.fullmatch(value or "") for value in expected.values()):
        raise ValueError("StartNotReady: every expected binding must be a sha256 digest")
    if actual != expected:
        raise ValueError("LifecycleCASMismatch: gate/slice/risk/envelope binding changed")
    packet = _read_json(packet_path)
    risk = _read_json(risk_path)
    envelope = _read_json(envelope_path)
    packet_invariants = sorted(str(row.get("invariant_id")) for row in packet.get("invariants", []) if isinstance(row, dict) and row.get("invariant_id"))
    if packet.get("slice_id") != request.selected_slice_id:
        raise ValueError("StartNotReady: selected slice id mismatch")
    if risk.get("schema_version") != 1 or risk.get("task_id") != task_id or risk.get("slice_id") != request.selected_slice_id:
        raise ValueError("RiskPacketStale: task/slice binding mismatch")
    if risk.get("route") != "full_chain" or risk.get("slice_packet_digest") != actual["slice_packet_digest"]:
        raise ValueError("RiskPacketStale: route or slice digest mismatch")
    gates = task_data.get("guru_gates") if isinstance(task_data.get("guru_gates"), dict) else {}
    detail = gates.get("detail") if isinstance(gates.get("detail"), dict) else {}
    detail_artifact_digest = detail.get("artifact_digest")
    if (
        risk.get("artifact_digest") != actual["gate_digest"]
        or risk.get("detail_artifact_digest") != detail_artifact_digest
        or not HEX_DIGEST.fullmatch(str(detail_artifact_digest or ""))
        or risk.get("invariant_ids") != packet_invariants
    ):
        raise ValueError("RiskPacketStale: current Gate/invariant binding mismatch")
    if envelope.get("schema_version") != 1 or envelope.get("task_id") != task_id or envelope.get("slice_id") != request.selected_slice_id:
        raise ValueError("StartNotReady: execution envelope task/slice mismatch")
    for field, value in {
        "slice_packet_digest": actual["slice_packet_digest"],
        "risk_packet_digest": actual["risk_packet_digest"],
        "scope_fingerprint": risk.get("scope_fingerprint"),
        "policy_snapshot_digest": risk.get("policy_snapshot_digest"),
    }.items():
        if envelope.get(field) != value:
            raise ValueError(f"StartNotReady: execution envelope {field} mismatch")
    decision_universe = _detail_decision_universe(
        request.task_dir,
        task_id,
        request.selected_slice_id,
        packet_invariants,
    )
    if risk.get("decision_universe_digest") != _digest(decision_universe):
        raise ValueError("RiskPacketStale: decision universe disagrees with confirmed detail")
    decision_items = [item for item in decision_universe if item["status"] == "unresolved"]
    if risk.get("decision_items") != decision_items:
        raise ValueError("RiskPacketStale: blocking decision set is not the confirmed detail closure")
    if risk.get("decision_set_digest") != _digest(decision_items):
        raise ValueError("RiskPacketStale: decision_set_digest mismatch")
    confirmation_required = risk.get("risk") == "high"
    if risk.get("confirmation_required") is not confirmation_required:
        raise ValueError("RiskPacketStale: high-risk confirmation requirement changed")
    if envelope.get("confirmation_required") is not confirmation_required:
        raise ValueError("ConfirmationStale: execution envelope confirmation requirement changed")
    if not confirmation_required:
        if request.expected_attestation_digest or envelope.get("confirmation_attestation_digest"):
            raise ValueError("ConfirmationStale: unexpected confirmation evidence")
        return {**actual, "attestation_digest": None, "task_id": task_id}

    attestation_path = request.task_dir / "confirmation-attestations" / f"{request.selected_slice_id}.json"
    if not attestation_path.is_file():
        raise ValueError("ConfirmationMissing: high-risk user confirmation evidence is required")
    attestation_digest = _sha256_file(attestation_path)
    if (
        not HEX_DIGEST.fullmatch(str(request.expected_attestation_digest or ""))
        or request.expected_attestation_digest != attestation_digest
        or envelope.get("confirmation_attestation_digest") != attestation_digest
    ):
        raise ValueError("ConfirmationStale: confirmation evidence digest mismatch")
    attestation = _read_json(attestation_path)
    expected_decision_ids = sorted(str(item["decision_id"]) for item in decision_items)
    if (
        attestation.get("schema_version") != 1
        or attestation.get("task_id") != task_id
        or attestation.get("slice_id") != request.selected_slice_id
        or attestation.get("risk_packet_digest") != actual["risk_packet_digest"]
        or attestation.get("scope_fingerprint") != risk.get("scope_fingerprint")
        or attestation.get("decision_set_digest") != risk.get("decision_set_digest")
        or attestation.get("decision_ids") != expected_decision_ids
        or attestation.get("outcome") != "confirmed"
        or attestation.get("confirmation_batch") != 1
        or attestation.get("provider") != "codex"
        or not str(attestation.get("user_quote") or "").strip()
    ):
        raise ValueError("ConfirmationStale: high-risk confirmation evidence is incomplete")
    return {**actual, "attestation_digest": attestation_digest, "task_id": task_id}


def _snapshot(request: StartRequest, root: Path, binding: dict) -> dict:
    task_path = request.task_dir / "task.json"
    task_data = _read_json(task_path)
    context_key = _context_key(request, root)
    session_path = _session_path(root, context_key)
    session_data = _read_json(session_path) if session_path and session_path.is_file() else {}
    return {
        "task_status": task_data.get("status"),
        "task_data": task_data,
        "task_file": _file_image(task_path),
        "context_key": context_key,
        "session_path": str(session_path) if session_path else None,
        "session_file": _file_image(session_path),
        "active_task_pointer": session_data.get("current_task"),
        "current_run_present": "current_run" in session_data,
        "current_run": session_data.get("current_run"),
        "binding": binding,
    }


def _run_gate(request: StartRequest, root: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable or "python3", str(root / ".trellis/scripts/guru/guru_gate.py"), "check-start", str(request.task_dir)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, _digest({"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr})


def _validate_preconditions(request: StartRequest, root: Path) -> tuple[list[str], dict | None, dict | None]:
    problems: list[str] = []
    task_json = request.task_dir / "task.json"
    if not task_json.is_file():
        return ["task.json missing"], None, None
    injected = os.environ.get("TASK_JSON_PATH")
    if injected and Path(injected).resolve() != task_json.resolve():
        problems.append("TASK_JSON_PATH points to a different task")
    try:
        binding = _artifact_binding(request, root)
        snapshot = _snapshot(request, root, binding)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return problems + [str(exc)], None, None
    if snapshot["task_status"] != request.expected_task_status:
        problems.append(f"task status must be {request.expected_task_status}, got {snapshot['task_status']}")
    if request.expected_active_task != snapshot["active_task_pointer"]:
        problems.append("LifecycleCASMismatch: active task pointer differs from request")
    current_run = snapshot.get("current_run")
    if current_run not in (None, ""):
        problems.append("SupervisorRunConflict: session current_run is already owned")
    supervisor_state = request.task_dir / "supervisor" / "current-run.json"
    if supervisor_state.is_file():
        state = _read_json(supervisor_state).get("state")
        if state in LIVE_RUN_STATES:
            problems.append(f"SupervisorRunConflict: current run state is {state}")
    packet = _read_json(request.task_dir / "slice-packets" / f"{request.selected_slice_id}.json")
    for dependency in packet.get("depends_on", []):
        completion = request.task_dir / "slice-completions" / f"{dependency}.json"
        if not completion.is_file() or _read_json(completion).get("status") != "verified":
            problems.append(f"StartNotReady: slice dependency is not verified: {dependency}")
    gate_ok, gate_run_digest = _run_gate(request, root)
    snapshot["gate_run_digest"] = gate_run_digest
    if not gate_ok:
        problems.append("check-start failed")
    return problems, binding, snapshot


class _StartLock:
    def __init__(self, task_dir: Path) -> None:
        self.path = task_dir / ".guru-start.lock"
        self.token = uuid.uuid4().hex
        self.owner_bytes = b""

    def __enter__(self) -> "_StartLock":
        payload = {
            "schema_version": 1,
            "pid": os.getpid(),
            "owner_identity": f"pid:{os.getpid()}:token:{self.token}",
            "token": self.token,
            "acquired_at": _now(),
            "recovery": "fail_closed; remove only after proving owner dead and associated attempt terminal",
        }
        self.owner_bytes = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, self.owner_bytes)
            os.fsync(fd)
        finally:
            os.close(fd)
        _fsync_parent(self.path)
        return self

    def assert_owned(self) -> None:
        try:
            current = self.path.read_bytes()
        except OSError as exc:
            raise ValueError("StartLockConflict: lock disappeared while guarded start was active") from exc
        if current != self.owner_bytes:
            raise ValueError("StartLockConflict: lock ownership token changed")

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        try:
            if self.path.read_bytes() == self.owner_bytes:
                self.path.unlink()
                _fsync_parent(self.path)
        except OSError:
            return


def _prepare_attempt(request: StartRequest, root: Path, pre_snapshot: dict) -> tuple[str, Path, str]:
    attempt_id = uuid.uuid4().hex
    wrapper_identity = f"pid:{os.getpid()}:nonce:{uuid.uuid4().hex}"
    attempt_path = request.task_dir / "start-attempts" / f"{attempt_id}.json"
    payload = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "task_id": pre_snapshot["binding"]["task_id"],
        "task_json_path": str((request.task_dir / "task.json").resolve()),
        "selected_slice_id": request.selected_slice_id,
        "wrapper_pid_identity": wrapper_identity,
        "created_at": _now(),
        "state": "prepared",
        "pre_snapshot": pre_snapshot,
        "expected_post_status": "in_progress",
        "expected_post_pointer": _task_ref(request.task_dir, root) if pre_snapshot["context_key"] else pre_snapshot["active_task_pointer"],
        "capability": {
            "entry_scope": "guarded_entry",
            "guarded_lifecycle_bindings": "enforced",
            "guarded_structural_bindings": "enforced",
            "confirmation_identity_provenance": "not_claimed",
            "high_risk_confirmation_evidence": "digest_bound_single_batch",
            "unresolved_required_high_risk": "blocked_without_current_confirmation",
            "direct_official_bypass": "advisory",
        },
    }
    _write_json_exclusive(attempt_path, payload)
    return attempt_id, attempt_path, wrapper_identity


def _mark_attempt(path: Path, state: str, extra: dict | None = None) -> None:
    data = _read_json(path)
    if data.get("state") in {"verified", "compensated", "manual_recovery_required"} and data.get("state") != state:
        raise ValueError("attempt terminal state conflict")
    data["state"] = state
    data["updated_at"] = _now()
    if extra:
        data.update(extra)
    _write_json_atomic(path, data)


def _expected_post_is_exact(pre: dict, post: dict, root: Path, task_dir: Path) -> list[str]:
    problems: list[str] = []
    expected_task = dict(pre["task_data"])
    expected_task["status"] = "in_progress"
    if post["task_data"] != expected_task:
        problems.append("OfficialStartFailed: task postcondition changed fields other than status")
    if pre["context_key"]:
        if post["active_task_pointer"] != _task_ref(task_dir, root):
            problems.append("OfficialStartFailed: session pointer postcondition mismatch")
        expected_run = pre["current_run"] if pre["current_run_present"] else None
        if not post["current_run_present"] or post["current_run"] != expected_run:
            problems.append("OfficialStartFailed: current_run ownership changed")
    elif post["session_file"] != pre["session_file"]:
        problems.append("OfficialStartFailed: no-session start changed a session file")
    return problems


def _restore_preimages(attempt: dict, observed: dict) -> tuple[bool, list[str]]:
    pre = attempt["pre_snapshot"]
    task_path = Path(attempt["task_json_path"])
    session_path = Path(pre["session_path"]) if pre.get("session_path") else None
    conflicts: list[str] = []
    if _file_image(task_path)["sha256"] != observed["task_file"]["sha256"]:
        conflicts.append("task.json CAS conflict")
    if session_path is not None and _file_image(session_path)["sha256"] != observed["session_file"]["sha256"]:
        conflicts.append("session file CAS conflict")
    if conflicts:
        return False, conflicts
    _write_bytes_atomic(task_path, base64.b64decode(pre["task_file"]["bytes_b64"]))
    if session_path is not None:
        if pre["session_file"]["exists"]:
            _write_bytes_atomic(session_path, base64.b64decode(pre["session_file"]["bytes_b64"]))
        else:
            try:
                session_path.unlink()
                _fsync_parent(session_path)
            except FileNotFoundError:
                pass
    return True, []


def _post_official_failure(
    request: StartRequest,
    root: Path,
    attempt_path: Path,
    pre_snapshot: dict,
    reason: str,
    observed: dict | None = None,
) -> int:
    failures = [reason]
    if observed is None:
        try:
            observed = _snapshot(request, root, pre_snapshot["binding"])
        except Exception as exc:  # lifecycle may itself be malformed after official mutation
            failures.append(f"post lifecycle snapshot unavailable: {exc}")
    restored = False
    conflicts: list[str] = []
    if observed is not None:
        try:
            attempt = _read_json(attempt_path) if attempt_path.is_file() else {
                "pre_snapshot": pre_snapshot,
                "task_json_path": str((request.task_dir / "task.json").resolve()),
            }
            restored, conflicts = _restore_preimages(attempt, observed)
        except Exception as exc:
            conflicts.append(f"compensation failed: {exc}")
    else:
        conflicts.append("manual recovery required: observed lifecycle is unknown")
    terminal = "compensated" if restored else "manual_recovery_required"
    try:
        _mark_attempt(attempt_path, terminal, {
            "post_failures": failures,
            "compensation_conflicts": conflicts,
            "official_post_snapshot": observed,
        })
    except Exception as exc:
        sidecar = attempt_path.with_suffix(".manual-recovery.json")
        try:
            _write_json_exclusive(sidecar, {
                "schema_version": 1,
                "state": "manual_recovery_required",
                "attempt_path": str(attempt_path),
                "reason": str(exc),
                "post_failures": failures,
                "compensation_conflicts": conflicts,
            })
        except Exception:
            pass
        failures.append(f"attempt terminalization failed: {exc}")
    sys.stderr.write("[guru-task:start] blocked after official start: " + "; ".join(failures + conflicts) + "\n")
    return BLOCK


def start_with_guard(request: StartRequest) -> int:
    root = _repo_root(request.task_dir)
    problems, _binding, pre = _validate_preconditions(request, root)
    if problems or pre is None:
        for problem in problems:
            sys.stderr.write(f"[guru-task:start] blocked: {problem}\n")
        return BLOCK
    try:
        with _StartLock(request.task_dir) as start_lock:
            locked_problems, _locked_binding, locked_pre = _validate_preconditions(request, root)
            if locked_problems or locked_pre != pre:
                sys.stderr.write("[guru-task:start] blocked: LifecycleCASMismatch after start lock\n")
                return BLOCK
            start_lock.assert_owned()
            attempt_id, attempt_path, wrapper_identity = _prepare_attempt(request, root, locked_pre)
            env = dict(os.environ)
            env.update({
                "GURU_START_ATTEMPT_ID": attempt_id,
                "GURU_START_ATTEMPT_PATH": str(attempt_path.resolve()),
                "GURU_START_WRAPPER_IDENTITY": wrapper_identity,
            })
            official_begun = False
            post: dict | None = None
            try:
                start_lock.assert_owned()
                official_begun = True
                result = subprocess.run(
                    [sys.executable or "python3", str(request.official_task_py), "start", str(request.task_dir)],
                    cwd=root,
                    env=env,
                    text=True,
                    capture_output=True,
                )
                start_lock.assert_owned()
                post_binding = _artifact_binding(request, root)
                post = _snapshot(request, root, post_binding)
                _mark_attempt(attempt_path, "official_returned", {"official_returncode": result.returncode, "official_post_snapshot": post})
                gate_ok, post_gate_digest = _run_gate(request, root)
                post_problems = _expected_post_is_exact(locked_pre, post, root, request.task_dir)
                attempt = _read_json(attempt_path)
                hook = attempt.get("hook_outcome") if isinstance(attempt.get("hook_outcome"), dict) else {}
                if hook.get("status") != "observed" or hook.get("binding_digest") != _digest(locked_pre["binding"]):
                    post_problems.append("OfficialStartFailed: after_start hook outcome not observed")
                if result.returncode != 0:
                    post_problems.append(f"OfficialStartFailed: official return code {result.returncode}")
                if not gate_ok or post_binding != locked_pre["binding"]:
                    post_problems.append("OfficialStartFailed: post-start Gate/binding recheck failed")
                if post_problems:
                    return _post_official_failure(
                        request, root, attempt_path, locked_pre, "; ".join(post_problems), post
                    )
                start_lock.assert_owned()
                _mark_attempt(attempt_path, "verified", {"post_gate_run_digest": post_gate_digest})
                if result.stdout:
                    sys.stdout.write(result.stdout)
                return PASS
            except Exception as exc:
                if official_begun:
                    return _post_official_failure(request, root, attempt_path, locked_pre, str(exc), post)
                raise
    except FileExistsError:
        sys.stderr.write(
            "[guru-task:start] blocked: StartLockConflict; fail closed and remove only after "
            "proving the recorded owner dead and its attempt terminal\n"
        )
        return BLOCK
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"[guru-task:start] blocked: {exc}\n")
        return BLOCK


def compensate_after_start(attempt_id: str, task_dir: Path) -> dict:
    path = task_dir / "start-attempts" / f"{attempt_id}.json"
    if not path.is_file():
        return {"ok": False, "state": "manual_recovery_required", "reason": "attempt missing"}
    attempt = _read_json(path)
    observed = attempt.get("official_post_snapshot")
    if not isinstance(observed, dict):
        return {"ok": False, "state": "manual_recovery_required", "reason": "official post snapshot missing"}
    restored, conflicts = _restore_preimages(attempt, observed)
    state = "compensated" if restored else "manual_recovery_required"
    _mark_attempt(path, state, {"compensation_conflicts": conflicts})
    return {"ok": restored, "state": state, "conflicts": conflicts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guru guarded task wrapper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    start = sub.add_parser("start")
    start.add_argument("task_dir")
    start.add_argument("--slice", required=True, dest="slice_id")
    start.add_argument("--official-task-py", default=".trellis/scripts/task.py")
    start.add_argument("--gate-digest", required=True)
    start.add_argument("--slice-packet-digest", required=True)
    start.add_argument("--risk-packet-digest", required=True)
    start.add_argument("--envelope-digest", required=True)
    start.add_argument("--attestation-digest", default=None)
    start.add_argument("--context-key", default=None)
    start.add_argument("--expected-active-task", default=None)
    args = parser.parse_args(argv)
    request = StartRequest(
        task_dir=Path(args.task_dir),
        selected_slice_id=args.slice_id,
        official_task_py=Path(args.official_task_py),
        expected_gate_digest=args.gate_digest,
        expected_slice_packet_digest=args.slice_packet_digest,
        expected_risk_packet_digest=args.risk_packet_digest,
        expected_envelope_digest=args.envelope_digest,
        expected_attestation_digest=args.attestation_digest,
        expected_context_key=args.context_key,
        expected_active_task=args.expected_active_task,
    )
    return start_with_guard(request)


if __name__ == "__main__":
    sys.exit(main())
