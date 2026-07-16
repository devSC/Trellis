#!/usr/bin/env python3
"""Observe guarded starts and report direct official bypasses truthfully."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def _fsync_parent(path: Path) -> None:
    try:
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    try:
        with open(tmp, "xb") as fh:
            fh.write((json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        _fsync_parent(path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    _fsync_parent(path)


def main() -> int:
    task_json_text = os.environ.get("TASK_JSON_PATH", "")
    task_json = Path(task_json_text) if task_json_text else None
    if task_json is None or not task_json.is_file():
        sys.stderr.write("[guru-after-start] TASK_JSON_PATH missing; capability unavailable\n")
        return 0
    task_dir = task_json.parent
    evidence_path = task_dir / "start-violations.jsonl"
    attempt_id = os.environ.get("GURU_START_ATTEMPT_ID", "").strip()
    attempt_path_text = os.environ.get("GURU_START_ATTEMPT_PATH", "").strip()
    wrapper_identity = os.environ.get("GURU_START_WRAPPER_IDENTITY", "").strip()
    if not attempt_id:
        _append_jsonl(evidence_path, {
            "schema_version": 1,
            "created_at": _now(),
            "capability": "advisory",
            "event": "direct_official_start_without_guard_attempt",
            "message": "detected only; no previous lifecycle state is guessed or restored",
        })
        sys.stderr.write("[guru-after-start] direct official start detected; advisory evidence recorded\n")
        return 0
    expected_path = (task_dir / "start-attempts" / f"{attempt_id}.json").resolve()
    attempt_path = Path(attempt_path_text).resolve() if attempt_path_text else expected_path
    if attempt_path != expected_path or not attempt_path.is_file():
        _append_jsonl(evidence_path, {
            "schema_version": 1,
            "created_at": _now(),
            "capability": "advisory",
            "event": "invalid_guard_attempt_path",
            "attempt_id": attempt_id,
        })
        return 0
    attempt = _read_json(attempt_path)
    valid = (
        attempt.get("schema_version") == 1
        and attempt.get("attempt_id") == attempt_id
        and attempt.get("state") == "prepared"
        and attempt.get("task_json_path") == str(task_json.resolve())
        and attempt.get("wrapper_pid_identity") == wrapper_identity
        and bool(wrapper_identity)
        and isinstance(attempt.get("pre_snapshot"), dict)
    )
    if not valid:
        _append_jsonl(evidence_path, {
            "schema_version": 1,
            "created_at": _now(),
            "capability": "advisory",
            "event": "invalid_guard_attempt",
            "attempt_id": attempt_id,
        })
        sys.stderr.write("[guru-after-start] invalid guarded attempt; wrapper must compensate\n")
        return 0
    binding = attempt["pre_snapshot"].get("binding")
    attempt["hook_outcome"] = {
        "status": "observed",
        "observed_at": _now(),
        "capability": "compensated",
        "binding_digest": _digest(binding),
        "task_status": _read_json(task_json).get("status"),
    }
    _write_json_atomic(attempt_path, attempt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
