#!/usr/bin/env python3
"""Guru review record + slice packet 的单一 schema 校验 / reader / writer
(supervisor parse-time、manual/ocr append 共用,避免一个 jsonl 两套 writer 漂移)。

设计约束:**不 import guru_gate / guru_supervise**(防循环——guru_supervise import 本模块、
guru_risk 也 import 本模块的 load_packet)。自带最小 packet/json 读取。

P1a 范围(本文件当前):packet schema(两层、非空)+ load_packet/list_packets + append_record +
preflight_failure_record。verdict 层(validate_verdict_values / normalize_review_record /
aggregate_invariant_coverage / run_deterministic_checks / parse_verdict_block)在 P1c 加。
"""
from __future__ import annotations

import json
import hashlib
import os
import select
import subprocess
import sys
import tempfile
import time

SCHEMA_VERSION = 1

REVIEW_RESULT = {"clean", "findings", "blocked"}
ROUTE_CLASS = {"none", "IMPLEMENT_DEFECT", "PROCESS_DEFECT", "DETAIL_DEFECT", "OVERVIEW_DEFECT", "REQ_BLOCKER"}
DETERMINISTIC_CHECKS = {"passed", "failed", "missing"}
DIRTY_SCOPE = {"clean", "isolated", "invalid"}
INVARIANT_COVERAGE = {"all_passed", "failed", "missing"}
SUPERVISOR_FAILURE = {
    "none", "SCOPE_INVALID", "MALFORMED_REVIEW_OUTPUT",
    "PACKET_MISSING", "PACKET_INVALID", "PACKET_AMBIGUOUS",
}

# packet.risk 参与判定的合法值;unknown/null/空/缺 → None(回落 P0);其他字符串 → PACKET_INVALID(R3-F3)。
PACKET_RISK_VALUES = {"high", "critical", "low"}
# semantic_review_provider.provider 第一版只支持 channel-spawnable(R5-F1);manual/ocr_optional 作 required → PACKET_INVALID。
REQUIRED_PROVIDER_VALUES = {"codex", "claude", "opposite"}
_CHANNEL_PROVIDERS = {"codex", "claude"}  # worker 自报 review_provider 的合法值域(真 channel-spawn;opposite 仅 packet 要求类型)
NON_REQUIRED_PROVIDERS = {"manual", "ocr_optional"}
OCR_VALUES = {"optional", "disabled"}
HIGH_RISK_REVIEW_PROVIDER_POLICIES = {"current", "opposite", "codex", "claude"}
PROVIDER_OVERRIDE_SOURCES = {"cli_same_provider", "config_policy", "staged_packet"}

_INVARIANT_REQUIRED_FIELDS = (
    "invariant_id", "rule", "source", "owner",
    "positive_case", "negative_case", "route_if_missing",
)


class ReviewRecordError(Exception):
    """packet schema / review record schema 非法。调用方(guru_supervise)据此记 PACKET_INVALID 等
    supervisor_failure 并 fail-closed(exit 2,不启 worker)。"""


def _require_str_list(val, name: str):
    """可选字符串数组校验(R1-F3/F6):None→[];必须是 list 且每元素非空 string,否则 ReviewRecordError。"""
    if val is None:
        return []
    if not isinstance(val, list) or not all(isinstance(x, str) and x.strip() for x in val):
        raise ReviewRecordError(f"slice packet {name} 必须是非空字符串数组")
    return val


def _packets_dir(task_dir: str) -> str:
    return os.path.join(task_dir, "slice-packets")


def list_packets(task_dir: str) -> list:
    """列出 task 的 slice-packets/*.json 的 unit_id(文件名去 .json);目录不存在 → []。"""
    d = _packets_dir(task_dir)
    if not os.path.isdir(d):
        return []
    return sorted(n[:-5] for n in os.listdir(d) if n.endswith(".json"))


def _normalize_packet_risk(raw):
    """high|critical|low → 该值;unknown/null/空/缺 → None(回落 P0);其他字符串 → ReviewRecordError(R3-F3)。"""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ReviewRecordError(f"packet risk 非字符串:{raw!r}")
    v = raw.strip().lower()
    if v in ("", "unknown"):
        return None
    if v in PACKET_RISK_VALUES:
        return v
    raise ReviewRecordError(f"packet risk 非法枚举:{raw!r}(仅 high|critical|low|unknown/缺)")


def _validate_semantic_review_provider(obj) -> dict:
    """present 时:required:bool / provider∈{codex,claude,opposite} / ocr∈{optional,disabled}。
    缺 → 默认 {required:true,provider:opposite,ocr:optional}。
    required=true ∧ provider∈{manual,ocr_optional} → ReviewRecordError(R5-F1:第一版 required 只 channel-spawnable)。
    Slice-backed review 将该字段作为审计元数据，实际 provider 由 supervisor 的项目 policy
    resolution context 决定；non-slice staged review 继续把该字段作为 provider contract。"""
    if obj is None:
        return {"required": True, "provider": "opposite", "ocr": "optional"}
    if not isinstance(obj, dict):
        raise ReviewRecordError("semantic_review_provider 必须是对象")
    required = obj.get("required", True)
    provider = obj.get("provider", "opposite")
    ocr = obj.get("ocr", "optional")
    if not isinstance(required, bool):
        raise ReviewRecordError("semantic_review_provider.required 必须是 bool")
    # R2-F1:provider/ocr 先做字符串类型校验,防 unhashable(list/dict)在 set membership 抛 TypeError
    # 逃逸 ReviewRecordError → packet preflight 漏判 PACKET_INVALID 而 traceback(违反 fail-closed 真闭)。
    if not isinstance(provider, str):
        raise ReviewRecordError("semantic_review_provider.provider 必须是字符串")
    if not isinstance(ocr, str):
        raise ReviewRecordError("semantic_review_provider.ocr 必须是字符串")
    if provider in NON_REQUIRED_PROVIDERS and required is True:
        raise ReviewRecordError(
            f"semantic_review_provider.provider={provider} 不能作 required(第一版仅 "
            f"{sorted(REQUIRED_PROVIDER_VALUES)};manual/ocr_optional 仅 supplemental,verify-record 路径 deferred)"
        )
    if provider not in REQUIRED_PROVIDER_VALUES and provider not in NON_REQUIRED_PROVIDERS:
        raise ReviewRecordError(f"semantic_review_provider.provider 非法:{provider!r}")
    if ocr not in OCR_VALUES:
        raise ReviewRecordError(f"semantic_review_provider.ocr 非法:{ocr!r}")
    return {"required": required, "provider": provider, "ocr": ocr}


def _validate_invariant(inv, idx: int) -> None:
    if not isinstance(inv, dict):
        raise ReviewRecordError(f"invariants[{idx}] 必须是对象")
    for f in _INVARIANT_REQUIRED_FIELDS:
        val = inv.get(f)
        if not isinstance(val, str) or not val.strip():
            raise ReviewRecordError(f"invariants[{idx}] 缺必填非空字段 {f}")
    te = inv.get("test_evidence", [])
    if te is not None and not isinstance(te, list):
        raise ReviewRecordError(f"invariants[{idx}].test_evidence 必须是数组")


def load_packet(task_dir: str, unit_id: str) -> dict:
    """读 <task_dir>/slice-packets/<unit_id>.json 并校验 schema(两层、非空)。
    缺失 / 非 JSON / 未知 schema_version / 缺必填 / 空 target_paths / 空 invariants / 非法枚举 →
    ReviewRecordError(调用方记 PACKET_MISSING/PACKET_INVALID,fail-closed)。
    返回规范化 dict(risk 已规范化、semantic_review_provider 补默认、dirty_state 补默认)。"""
    path = os.path.join(_packets_dir(task_dir), f"{unit_id}.json")
    if not os.path.isfile(path):
        raise ReviewRecordError(f"slice packet 不存在:{path}")
    try:
        with open(path, encoding="utf-8") as fh:
            pkt = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ReviewRecordError(f"slice packet 非法 JSON:{path}:{exc}") from exc
    if not isinstance(pkt, dict):
        raise ReviewRecordError(f"slice packet 根节点必须是对象:{path}")
    if pkt.get("schema_version") != SCHEMA_VERSION:
        raise ReviewRecordError(
            f"slice packet schema_version 须为 {SCHEMA_VERSION}:{pkt.get('schema_version')!r}"
        )
    for f in ("slice_id", "owner_unit", "target_kind"):
        if not isinstance(pkt.get(f), str) or not pkt.get(f).strip():
            raise ReviewRecordError(f"slice packet 缺必填非空字段 {f}")
    # R9-F1:target_paths 非空字符串数组(防 scope gate 失边界)
    tp = pkt.get("target_paths")
    if not isinstance(tp, list) or not tp or not all(isinstance(p, str) and p.strip() for p in tp):
        raise ReviewRecordError("slice packet target_paths 必须是非空字符串数组")
    # R9-F1:invariants 非空对象数组(防 invariants:[] 绕过 invariant gating)
    invs = pkt.get("invariants")
    if not isinstance(invs, list) or not invs:
        raise ReviewRecordError("slice packet invariants 必须是非空对象数组")
    for i, inv in enumerate(invs):
        _validate_invariant(inv, i)
    pkt = dict(pkt)
    pkt["risk"] = _normalize_packet_risk(pkt.get("risk"))  # 非法枚举在此 raise
    pkt["semantic_review_provider"] = _validate_semantic_review_provider(pkt.get("semantic_review_provider"))
    _require_str_list(pkt.get("risk_reasons"), "risk_reasons")  # R1-F6:非字符串数组 → PACKET_INVALID
    _require_str_list(pkt.get("deterministic_checks"), "deterministic_checks")  # R1-F3:元素须非空 string(防 run 时 traceback)
    ds = pkt.get("dirty_state")
    if ds is None:
        pkt["dirty_state"] = {"unrelated": []}
    elif not isinstance(ds, dict):
        raise ReviewRecordError("slice packet dirty_state 必须是对象")
    else:
        _require_str_list(ds.get("unrelated"), "dirty_state.unrelated")  # R1-F6
    return pkt


def _reviews_path(task_dir: str) -> str:
    return os.path.join(task_dir, "review-records", "implementation-reviews.jsonl")


# review record jsonl 字段全集(append_record 写;R3-F2 review_target / R5-F2 deterministic_results /
# R5-F3 message+candidates / R7-F2 supplemental+required_satisfied 均在内)。
_RECORD_FIELDS = (
    "run_id", "slice_id", "review_target", "target_paths", "review_provider",
    "route_class", "review_result", "deterministic_checks", "dirty_scope", "invariant_coverage",
    "deterministic_results", "channel", "worker", "timestamp", "supervisor_failure", "repairable",
    "message", "candidates", "supplemental", "required_satisfied", "reviewed_target_digest",
    "provider_override_source", "same_provider_user_quote", "high_risk_review_provider_policy",
    "check_provider", "implement_provider", "review_target_kind",
)


def _clean_target_paths(target_paths) -> list:
    if not isinstance(target_paths, list):
        raise ReviewRecordError("target_paths 必须是数组")
    cleaned = []
    for raw in target_paths:
        if not isinstance(raw, str) or not raw.strip():
            raise ReviewRecordError("target_paths 必须是非空字符串数组")
        path = raw.strip().replace("\\", "/")
        if (
            not path
            or "\0" in path
            or path.startswith("/")
            or (len(path) >= 2 and path[1] == ":")
        ):
            raise ReviewRecordError(f"target path 越界或非法:{raw!r}")
        while path.startswith("./"):
            path = path[2:]
        if (
            not path
            or path.startswith("../")
            or "/../" in f"/{path}/"
            or path.startswith(":")
        ):
            raise ReviewRecordError(f"target path 越界或非法:{raw!r}")
        path = path.strip("/")
        if not path:
            raise ReviewRecordError(f"target path 越界或非法:{raw!r}")
        cleaned.append(path)
    return sorted(set(cleaned))


_SNAPSHOT_EXCLUDED_PREFIXES = (".trellis/tasks", ".trellis/workspace")


def _snapshot_path_excluded(path: str) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return any(
        normalized == prefix or normalized.startswith(prefix + "/")
        for prefix in _SNAPSHOT_EXCLUDED_PREFIXES
    )


def _target_contains_path(target: str, path: str) -> bool:
    normalized_target = target.rstrip("/")
    if normalized_target == ".":
        return True
    return path == normalized_target or path.startswith(normalized_target + "/")


def _git_ls_files(repo_root: str, targets: list, args: list) -> bytes:
    try:
        result = subprocess.run(
            ["git", "--literal-pathspecs", "ls-files", "-z", *args, "--", *targets],
            cwd=repo_root,
            capture_output=True,
            text=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewRecordError(f"cannot inspect git paths:{exc}") from exc
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        raise ReviewRecordError(f"git ls-files failed:{stderr}")
    return result.stdout


def _git_diff_cached_deleted(repo_root: str, targets: list) -> list:
    try:
        result = subprocess.run(
            ["git", "--literal-pathspecs", "diff", "--cached", "--name-only", "--no-renames", "--diff-filter=D", "-z", "--", *targets],
            cwd=repo_root,
            capture_output=True,
            text=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewRecordError(f"cannot inspect staged deletions:{exc}") from exc
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        raise ReviewRecordError(f"git diff --cached failed:{stderr}")
    return [
        raw.decode("utf-8", errors="surrogateescape")
        for raw in result.stdout.split(b"\0")
        if raw
    ]


def _worktree_entries(repo_root: str, targets: list) -> list:
    root_real = os.path.realpath(repo_root)
    entries = []
    paths = set()
    cached_entries = {}
    for raw in _git_ls_files(
        repo_root, targets, ["--stage", "--cached"]
    ).split(b"\0"):
        if not raw:
            continue
        try:
            meta, path_raw = raw.split(b"\t", 1)
            fields = meta.split()
            mode = fields[0].decode("ascii", errors="replace")
            oid = fields[1].decode("ascii", errors="replace")
            stage = fields[2].decode("ascii", errors="replace") if len(fields) > 2 else ""
            path = path_raw.decode("utf-8", errors="surrogateescape")
        except (IndexError, ValueError) as exc:
            raise ReviewRecordError("cannot parse git worktree index entry") from exc
        if _snapshot_path_excluded(path):
            continue
        if stage != "0":
            raise ReviewRecordError(f"unmerged worktree index entry for {path}: stage {stage}")
        paths.add(path)
        cached_entries[path] = (mode, oid)
    for deleted in _git_diff_cached_deleted(repo_root, targets):
        if not _snapshot_path_excluded(deleted):
            paths.add(deleted)
    untracked = set()
    for raw in _git_ls_files(
        repo_root, targets, ["--others", "--exclude-standard"]
    ).split(b"\0"):
        if raw:
            path = raw.decode("utf-8", errors="surrogateescape")
            if not _snapshot_path_excluded(path):
                untracked.add(path)
    for target in targets:
        if _snapshot_path_excluded(target):
            continue
        target_untracked = [
            p for p in untracked
            if _target_contains_path(target, p)
        ]
        paths.update(target_untracked)
        if target != "." and target not in paths and not any(_target_contains_path(target, p) for p in paths):
            paths.add(target)
    for target in sorted(paths):
        cached_mode, cached_oid = cached_entries.get(target, (None, None))
        if cached_mode == "160000":
            entries.append((target, _worktree_gitlink_oid(repo_root, target, cached_oid), "gitlink"))
            continue
        abs_path = os.path.join(repo_root, target)
        abs_real = os.path.realpath(abs_path)
        if not os.path.lexists(abs_path):
            entries.append((target, None, "delete"))
            continue
        if os.path.islink(abs_path):
            entries.append((target, abs_path, "symlink"))
            continue
        if abs_real != root_real and not abs_real.startswith(root_real + os.sep):
            raise ReviewRecordError(f"target path escapes repo root:{target}")
        if os.path.isfile(abs_path):
            entries.append((target, abs_path, "file"))
            continue
    return sorted(entries, key=lambda item: item[0])


def _worktree_git_mode(path: str, kind: str) -> str:
    if kind == "symlink":
        return "120000"
    try:
        st = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise ReviewRecordError(f"cannot stat target file:{path}:{exc}") from exc
    return "100755" if (st.st_mode & 0o111) else "100644"


def _index_entries(repo_root: str, targets: list) -> list:
    paths = {}
    for raw in _git_ls_files(repo_root, targets, ["--stage", "--cached"]).split(b"\0"):
        if not raw:
            continue
        try:
            meta, path_raw = raw.split(b"\t", 1)
            fields = meta.split()
            mode = fields[0].decode("ascii", errors="replace")
            oid = fields[1].decode("ascii", errors="replace")
            stage = fields[2].decode("ascii", errors="replace") if len(fields) > 2 else ""
            path = path_raw.decode("utf-8", errors="surrogateescape")
        except (IndexError, ValueError) as exc:
            raise ReviewRecordError("cannot parse git index entry") from exc
        if _snapshot_path_excluded(path):
            continue
        if stage != "0":
            raise ReviewRecordError(f"unmerged staged entry for {path}: stage {stage}")
        paths[path] = (mode, oid)
    for deleted in _git_diff_cached_deleted(repo_root, targets):
        if not _snapshot_path_excluded(deleted):
            paths[deleted] = (None, None)
    indexed = set(paths)
    for target in targets:
        if _snapshot_path_excluded(target):
            continue
        if target != "." and target not in paths and not any(_target_contains_path(target, p) for p in indexed):
            paths[target] = (None, None)
    return [(p, *paths[p]) for p in sorted(paths)]


def _hash_field(h, label: str, value) -> None:
    data = value if isinstance(value, bytes) else str(value).encode(
        "utf-8", errors="surrogateescape"
    )
    h.update(label.encode("ascii"))
    h.update(b":")
    h.update(str(len(data)).encode("ascii"))
    h.update(b"\0")
    h.update(data)
    h.update(b"\0")


def _hash_content_chunks(h, data: bytes) -> None:
    for offset in range(0, len(data), 1024 * 1024):
        _hash_field(h, "CONTENT_CHUNK", data[offset:offset + 1024 * 1024])


def _hash_file_chunks(h, path: str) -> None:
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                _hash_field(h, "CONTENT_CHUNK", chunk)
    except OSError as exc:
        raise ReviewRecordError(f"cannot read target file:{path}:{exc}") from exc


def _blob_read_timeout_seconds() -> float:
    raw = os.environ.get("GURU_REVIEW_RECORD_BLOB_TIMEOUT_SECONDS", "120")
    try:
        value = float(raw)
    except ValueError:
        value = 120.0
    return max(15.0, value)


def _hash_git_blob_chunks(h, repo_root: str, rel: str, oid: str) -> None:
    timeout_s = _blob_read_timeout_seconds()
    if os.name == "nt":
        with tempfile.TemporaryFile() as stdout_tmp, tempfile.TemporaryFile() as stderr_tmp:
            try:
                proc = subprocess.Popen(
                    ["git", "cat-file", "-p", oid],
                    cwd=repo_root,
                    stdout=stdout_tmp,
                    stderr=stderr_tmp,
                )
            except OSError as exc:
                raise ReviewRecordError(f"cannot read staged blob for {rel}:{exc}") from exc
            try:
                rc = proc.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired as exc:
                proc.kill()
                proc.wait()
                raise ReviewRecordError(f"cannot read staged blob for {rel}:timeout") from exc
            stdout_tmp.seek(0)
            for chunk in iter(lambda: stdout_tmp.read(1024 * 1024), b""):
                _hash_content_chunks(h, chunk)
            stderr_tmp.seek(0)
            stderr = stderr_tmp.read(128 * 1024 + 1)
    else:
        try:
            proc = subprocess.Popen(
                ["git", "cat-file", "-p", oid],
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            raise ReviewRecordError(f"cannot read staged blob for {rel}:{exc}") from exc
        try:
            assert proc.stdout is not None
            assert proc.stderr is not None
            if not (hasattr(proc.stdout, "fileno") and hasattr(proc.stderr, "fileno")):
                data, stderr = proc.communicate(timeout=timeout_s)
                _hash_content_chunks(h, data)
                rc = proc.returncode
                if rc != 0:
                    message = stderr.decode("utf-8", errors="replace").strip()
                    raise ReviewRecordError(f"cannot read staged blob for {rel}:{message}")
                return
            stdout_fd = proc.stdout.fileno()
            stderr_fd = proc.stderr.fileno()
            fds = {stdout_fd: "stdout", stderr_fd: "stderr"}
            stderr_chunks = []
            pending = b""
            deadline = time.monotonic() + timeout_s
            while fds:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    proc.kill()
                    proc.wait()
                    raise ReviewRecordError(f"cannot read staged blob for {rel}:timeout")
                readable, _, _ = select.select(list(fds), [], [], min(1.0, remaining))
                if not readable:
                    continue
                for fd in readable:
                    stream_name = fds[fd]
                    chunk = os.read(fd, 1024 * 1024)
                    if not chunk:
                        del fds[fd]
                        continue
                    if stream_name == "stdout":
                        pending += chunk
                        while len(pending) >= 1024 * 1024:
                            _hash_field(h, "CONTENT_CHUNK", pending[:1024 * 1024])
                            pending = pending[1024 * 1024:]
                    else:
                        stderr_chunks.append(chunk)
            if pending:
                _hash_field(h, "CONTENT_CHUNK", pending)
            try:
                rc = proc.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                proc.kill()
                proc.wait()
                raise ReviewRecordError(f"cannot read staged blob for {rel}:timeout") from exc
            stderr = b"".join(stderr_chunks)
        finally:
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()
    if rc != 0:
        message = stderr.decode("utf-8", errors="replace").strip()
        raise ReviewRecordError(f"cannot read staged blob for {rel}:{message}")


def _worktree_gitlink_oid(repo_root: str, rel: str, cached_oid: str | None) -> str:
    submodule_path = os.path.join(repo_root, rel)
    if os.path.isdir(submodule_path):
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=submodule_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ReviewRecordError(f"cannot read gitlink worktree HEAD for {rel}:{exc}") from exc
        oid = result.stdout.strip()
        if result.returncode == 0 and oid and all(ch in "0123456789abcdefABCDEF" for ch in oid):
            return oid
        message = (result.stderr or result.stdout or "").strip()
        raise ReviewRecordError(f"cannot read gitlink worktree HEAD for {rel}:{message}")
    if cached_oid:
        return cached_oid
    raise ReviewRecordError(f"cannot resolve gitlink target for {rel}")


def target_snapshot_digest(repo_root: str, target_paths: list, source: str = "worktree") -> str:
    """Return a content snapshot digest for review target paths.

    `source=worktree` captures the files the implementation reviewer inspected.
    `source=index` captures the currently staged index for commit gating. The
    digest is intentionally path+content based rather than only path based, so
    a clean review cannot be reused after modifying the same target file.
    """
    targets = _clean_target_paths(target_paths)
    if not targets:
        raise ReviewRecordError("target_paths 为空，无法计算 target snapshot digest")
    h = hashlib.sha256()
    h.update(b"guru-target-snapshot-v2\0")
    if source == "worktree":
        entries = _worktree_entries(repo_root, targets)
        for rel, full, kind in entries:
            _hash_field(h, "PATH", rel)
            if full is None:
                _hash_field(h, "STATE", "DELETE")
                continue
            if kind == "gitlink":
                _hash_field(h, "MODE", "160000")
                _hash_field(h, "TYPE", "GITLINK")
                _hash_field(h, "CONTENT", full)
                continue
            _hash_field(h, "MODE", _worktree_git_mode(full, kind))
            if kind == "symlink":
                _hash_field(h, "TYPE", "SYMLINK")
                try:
                    link_target = os.readlink(full)
                except OSError as exc:
                    raise ReviewRecordError(f"cannot read symlink target:{full}:{exc}") from exc
                _hash_field(h, "CONTENT", link_target)
                continue
            _hash_field(h, "TYPE", "FILE")
            _hash_file_chunks(h, full)
        return h.hexdigest()
    if source == "index":
        for rel, mode, oid in _index_entries(repo_root, targets):
            _hash_field(h, "PATH", rel)
            if not (mode and oid):
                _hash_field(h, "STATE", "DELETE")
                continue
            if mode not in {"100644", "100755", "120000", "160000"}:
                raise ReviewRecordError(f"unsupported staged mode for {rel}:{mode}")
            if mode == "160000":
                _hash_field(h, "MODE", mode)
                _hash_field(h, "TYPE", "GITLINK")
                _hash_field(h, "CONTENT", oid)
                continue
            _hash_field(h, "MODE", mode)
            _hash_field(h, "TYPE", "SYMLINK" if mode == "120000" else "FILE")
            if mode == "120000":
                try:
                    blob = subprocess.run(
                        ["git", "cat-file", "-p", oid],
                        cwd=repo_root,
                        capture_output=True,
                        text=False,
                        timeout=15,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise ReviewRecordError(f"cannot read staged blob for {rel}:{exc}") from exc
                if blob.returncode == 0:
                    _hash_field(h, "CONTENT", blob.stdout)
                else:
                    stderr = (blob.stderr or b"").decode("utf-8", errors="replace").strip()
                    raise ReviewRecordError(f"cannot read staged blob for {rel}:{stderr}")
            else:
                _hash_git_blob_chunks(h, repo_root, rel, oid)
        return h.hexdigest()
    raise ReviewRecordError(f"unknown target snapshot source:{source!r}")


def append_record(task_dir: str, record: dict) -> None:
    """**唯一 writer**:校验 record 关键枚举后追加 review-records/implementation-reviews.jsonl。
    调用方永远经 normalize_review_record / preflight_failure_record → append_record,绝不拒绝后手写
    (BHV-005;malformed/scope/packet failure 都经此入 jsonl)。"""
    if not isinstance(record, dict):
        raise ReviewRecordError("review record 必须是 dict")
    # R3-SF1:枚举字段先做字符串类型守卫(单一 writer/校验入口须对非法 record fail-closed,而非 traceback);
    # 防 unhashable(list/dict)在下面 set membership 抛 TypeError 逃逸 ReviewRecordError。缺失字段保留默认逻辑。
    for _k in ("review_result", "route_class", "supervisor_failure"):
        _v = record.get(_k)
        if _v is not None and not isinstance(_v, str):
            raise ReviewRecordError(f"review record {_k} 必须是字符串")
    if record.get("review_result") not in REVIEW_RESULT:
        raise ReviewRecordError(f"review_result 非法:{record.get('review_result')!r}")
    if record.get("route_class", "none") not in ROUTE_CLASS:
        raise ReviewRecordError(f"route_class 非法:{record.get('route_class')!r}")
    sf = record.get("supervisor_failure", "none")
    if sf not in SUPERVISOR_FAILURE:
        raise ReviewRecordError(f"supervisor_failure 非法:{record.get('supervisor_failure')!r}")
    # R1-F5:防绕过——supervisor_failure=none 的 record 必须是完整规范化 verdict(7 字段 + 取值一致);
    # 裸 clean(缺 gating 字段)或手写不一致直接拒,杜绝绕过 normalize_review_record 污染 jsonl。
    # canonical failure record(sf!=none,preflight/malformed)不含 worker verdict 字段,跳过此校验。
    if sf == "none":
        vc = validate_verdict_values(record)
        if vc:
            raise ReviewRecordError(
                "review record 非规范化(缺完整 verdict 字段或取值不一致);"
                "须经 normalize_review_record / preflight_failure_record 产出后再 append")
    os.makedirs(os.path.dirname(_reviews_path(task_dir)), exist_ok=True)
    line = json.dumps(
        {k: record[k] for k in _RECORD_FIELDS if k in record},
        ensure_ascii=False, sort_keys=True,
    )
    with open(_reviews_path(task_dir), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def preflight_failure_record(kind: str, run_id: str, unit_id: str | None = None, candidates=None) -> dict:
    """supervisor-only 硬停 canonical record(R2-F1+F6/R5):**route_class=none**(非 PROCESS_DEFECT——
    它在 REPAIRABLE_IMPLEMENT_ROUTES 里会被误进 repair loop)、repairable=false。
    kind ∈ {PACKET_MISSING,PACKET_INVALID,PACKET_AMBIGUOUS,SCOPE_INVALID}。
    字段策略(R5-F6):有 unit_id → slice_id=unit_id / review_target=slice:<unit>;
    无 → slice_id=None / review_target=slice:unknown;多 packet(PACKET_AMBIGUOUS)候选入 message+candidates。"""
    if not isinstance(kind, str):  # R4-SF1:public 入口字符串守卫,防 unhashable 在 set membership 抛 TypeError
        raise ReviewRecordError(f"preflight_failure_record kind 必须是字符串:{kind!r}")
    if kind not in SUPERVISOR_FAILURE or kind == "none" or kind == "MALFORMED_REVIEW_OUTPUT":
        raise ReviewRecordError(f"preflight_failure_record kind 非法:{kind!r}")
    rec = {
        "run_id": run_id,
        "slice_id": unit_id,
        "review_target": f"slice:{unit_id}" if unit_id else "slice:unknown",
        "target_paths": [],
        "review_result": "blocked",
        "route_class": "none",
        "supervisor_failure": kind,
        "repairable": False,
    }
    if candidates:
        if not isinstance(candidates, list) or not all(isinstance(c, str) and c for c in candidates):  # R5-SF3
            raise ReviewRecordError("preflight_failure_record candidates 必须是非空字符串数组")
        rec["candidates"] = list(candidates)
        rec["message"] = "candidates: " + ", ".join(candidates)
    return rec


# ============================================================================
# P1c verdict 层:取值校验 / invariant 聚合 / deterministic 执行 / 解析 / 规范化(单一入口)。
# ============================================================================

_VERDICT_FIELDS = (
    "review_result", "route_class", "review_target", "review_provider",
    "deterministic_checks", "dirty_scope", "invariant_coverage",
)
_REPAIRABLE_ROUTES = {"IMPLEMENT_DEFECT", "PROCESS_DEFECT"}  # 与 guru_supervise 同值(本模块不 import 它,防循环)


def _norm_result(v):
    return "clean" if v == "final-verification-ready" else v


def validate_verdict_values(fields) -> "str|None":
    """取值校验层①（**所有 provider 共用**）：7 字段存在性 + 枚举 + clean 三通过值一致性。
    不过 → "MALFORMED_REVIEW_OUTPUT"；通过 → None。不做 provider/deterministic/invariant 重算(那在②)。"""
    if not isinstance(fields, dict):  # R5-SF1:顶层 shape guard,非 mapping → MALFORMED 不 traceback
        return "MALFORMED_REVIEW_OUTPUT"
    f = dict(fields)
    f["review_result"] = _norm_result(f.get("review_result"))
    for k in _VERDICT_FIELDS:
        v = f.get(k)
        if not isinstance(v, str) or not v:  # R3-SF2:非空字符串守卫(防 unhashable 击穿后续 set membership 抛 TypeError)
            return "MALFORMED_REVIEW_OUTPUT"
    if f["review_result"] not in REVIEW_RESULT:
        return "MALFORMED_REVIEW_OUTPUT"
    if f["route_class"] not in ROUTE_CLASS:
        return "MALFORMED_REVIEW_OUTPUT"
    if f["deterministic_checks"] not in DETERMINISTIC_CHECKS:
        return "MALFORMED_REVIEW_OUTPUT"
    if f["dirty_scope"] not in DIRTY_SCOPE:
        return "MALFORMED_REVIEW_OUTPUT"
    if f["invariant_coverage"] not in INVARIANT_COVERAGE:
        return "MALFORMED_REVIEW_OUTPUT"
    if f["review_result"] == "clean":
        if f["route_class"] != "none":  # R1-F4:clean 必须 route_class=none
            return "MALFORMED_REVIEW_OUTPUT"
        if not (f["deterministic_checks"] == "passed"
                and f["dirty_scope"] in ("clean", "isolated")
                and f["invariant_coverage"] == "all_passed"):
            return "MALFORMED_REVIEW_OUTPUT"
    elif f["route_class"] == "none":  # R1-F4:findings/blocked 必须有真 route,否则无法安全路由
        return "MALFORMED_REVIEW_OUTPUT"
    return None


def aggregate_invariant_coverage(packet_invariants, reviewer_statuses) -> str:
    """§4.3 唯一聚合：reviewer_statuses = {invariant_id: {"status","evidence","reason"}}。
    未知 id → "MALFORMED"；任一 fail → "failed"；缺 status / pass 缺 evidence / N/A 缺 reason → "missing"；
    否则 "all_passed"。supervisor 从 packet invariants + reviewer statuses 重算,不只信 worker 字符串。"""
    # R4-SF2:public 聚合入口形状守卫,非预期类型 fail-closed "MALFORMED"(非 traceback)。真实路径
    # packet 来自 load_packet(_validate_invariant 保证非空 str)、statuses 来自 parse_verdict_block(str)。
    if not isinstance(packet_invariants, list) or not isinstance(reviewer_statuses, dict):
        return "MALFORMED"
    inv_ids = set()
    for inv in packet_invariants:
        if not isinstance(inv, dict) or not isinstance(inv.get("invariant_id"), str) or not inv["invariant_id"]:
            return "MALFORMED"
        inv_ids.add(inv["invariant_id"])
    for sid in reviewer_statuses:
        if sid not in inv_ids:
            return "MALFORMED"
    for inv in packet_invariants:
        st = reviewer_statuses.get(inv["invariant_id"])
        if not isinstance(st, dict) or not st.get("status"):
            return "missing"
        status = st["status"]
        if not isinstance(status, str):
            return "MALFORMED"
        if status == "fail":
            return "failed"
        if status == "pass":
            if not isinstance(st.get("evidence"), str) or not st["evidence"].strip():
                return "missing"
        elif status == "not_applicable":
            if not isinstance(st.get("reason"), str) or not st["reason"].strip():
                return "missing"
        else:
            return "MALFORMED"
    return "all_passed"


def run_deterministic_checks(commands, repo_root):
    """supervisor-side 执行 packet deterministic_checks[]（R3-F1/R5-F2,BHV-008）。
    返回 (status, results)：空/缺→("missing",[])；全 exit0→"passed"；任一失败/timeout/非法命令→"failed"。
    results 逐条 command/cwd/exit_code/timed_out/stdout_summary/stderr_summary/duration_ms/run_at。
    R1-F3:非字符串/空 argv 命令转 failed result(不 traceback);load_packet 已先校验,此为 defense-in-depth。"""
    import shlex
    import subprocess
    import time
    from datetime import datetime, timezone
    if not commands:
        return ("missing", [])
    if not isinstance(commands, list):  # R5-SF2:顶层非 list(非预期)→ failed,不迭代任意 iterable(如 dict key)
        return ("failed", [])
    results = []
    status = "passed"
    for cmd in commands:
        entry = {"command": cmd, "cwd": repo_root, "timed_out": False,
                 "run_at": datetime.now(timezone.utc).isoformat()}

        def _fail(msg):  # R1-F3:非法命令 → failed entry,不抛
            entry.update({"exit_code": None, "stdout_summary": "", "stderr_summary": msg, "duration_ms": 0})
            results.append(entry)

        if not isinstance(cmd, str) or not cmd.strip():
            _fail("invalid command: non-string or empty"); status = "failed"; continue
        try:
            argv = shlex.split(cmd)
        except ValueError as exc:
            _fail(f"shlex error: {exc}"); status = "failed"; continue
        if not argv:
            _fail("empty argv after shlex.split"); status = "failed"; continue
        start = time.monotonic()
        try:
            proc = subprocess.run(argv, cwd=repo_root, capture_output=True,
                                  text=True, errors="replace", timeout=600)
            entry["exit_code"] = proc.returncode
            entry["stdout_summary"] = (proc.stdout or "")[-500:]
            entry["stderr_summary"] = (proc.stderr or "")[-500:]
            if proc.returncode != 0:
                status = "failed"
        except subprocess.TimeoutExpired:
            entry["exit_code"] = None; entry["timed_out"] = True
            entry["stdout_summary"] = ""; entry["stderr_summary"] = "timeout"; status = "failed"
        except OSError as exc:
            entry["exit_code"] = None; entry["stdout_summary"] = ""
            entry["stderr_summary"] = f"exec error: {exc}"; status = "failed"
        entry["duration_ms"] = int((time.monotonic() - start) * 1000)
        results.append(entry)
    return (status, results)


def parse_verdict_block(text: str) -> dict:
    """从 worker 输出解析行级 key=value：7 字段 + per-invariant
    invariant_status.<id> / invariant_evidence.<id> / invariant_reason.<id>。
    返回 fields，per-invariant 收进 fields["_invariants"] = {id: {status,evidence,reason}}。"""
    fields = {}
    invariants = {}
    if not isinstance(text, str):  # R4-SF(穷尽):非 str 输入返回空 fields,交 validate_verdict_values 判 MALFORMED
        return fields
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("{"):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                event = None
            if isinstance(event, dict):
                event_text = event.get("text")
                if isinstance(event_text, str):
                    lines.extend(event_text.splitlines())
                    continue
        lines.append(line)
    for line in lines:
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip(); val = val.strip()
        matched = False
        for prefix, slot in (("invariant_status.", "status"),
                             ("invariant_evidence.", "evidence"),
                             ("invariant_reason.", "reason")):
            if key.startswith(prefix):
                invariants.setdefault(key[len(prefix):], {})[slot] = val
                matched = True
                break
        if not matched and key in _VERDICT_FIELDS:
            fields[key] = val
    fields["_invariants"] = invariants
    return fields


def normalize_review_record(fields, context):
    """**唯一规范化入口**（两层 R7-F2）。context:
    {mode:"supervisor"|"supplemental", packet, implement_provider, supervisor_deterministic_status,
     run_id, slice_id, review_target, target_paths, channel, worker, timestamp, deterministic_results}。
    返回 (record, failure_code)。调用方永远 normalize → append_record,绝不拒绝后手写。"""
    if not isinstance(context, dict):  # R5-SF1:顶层 shape guard,非 dict context 归一(防 .get traceback)
        context = {}
    if not isinstance(fields, dict):  # R5-SF1:非 mapping verdict 归一为空 → 走 validate 判 MALFORMED,不 traceback
        fields = {}
    mode = context.get("mode", "supervisor")
    f = dict(fields)
    statuses = f.pop("_invariants", {})
    f["review_result"] = _norm_result(f.get("review_result"))
    base = {
        "run_id": context.get("run_id"), "slice_id": context.get("slice_id"),
        "review_target": context.get("review_target") or f.get("review_target"),
        "target_paths": context.get("target_paths", []),
        "review_provider": f.get("review_provider"), "channel": context.get("channel"),
        "worker": context.get("worker"), "timestamp": context.get("timestamp"),
        "deterministic_results": context.get("deterministic_results", []),
        "provider_override_source": context.get("provider_override_source"),
        "same_provider_user_quote": context.get("same_provider_user_quote"),
        "high_risk_review_provider_policy": context.get("high_risk_review_provider_policy"),
        "check_provider": context.get("check_provider"),
        "implement_provider": context.get("implement_provider"),
        "review_target_kind": context.get("review_target_kind"),
    }
    if context.get("reviewed_target_digest"):
        base["reviewed_target_digest"] = context.get("reviewed_target_digest")

    def blocked(code):
        rec = dict(base)
        rec.update({"review_result": "blocked", "route_class": "none",
                    "deterministic_checks": f.get("deterministic_checks"),
                    "dirty_scope": f.get("dirty_scope"), "invariant_coverage": f.get("invariant_coverage"),
                    "supervisor_failure": code, "repairable": False})
        return (rec, code)

    fc = validate_verdict_values(f)  # 层①
    if fc:
        return blocked(fc)

    if mode == "supplemental":  # manual/ocr append:只过①,保留补充审计(含 clean),不消费为 required clean
        rec = dict(base)
        rec.update({"review_result": f["review_result"], "route_class": f["route_class"],
                    "deterministic_checks": f["deterministic_checks"], "dirty_scope": f["dirty_scope"],
                    "invariant_coverage": f["invariant_coverage"], "supervisor_failure": "none",
                    "repairable": False, "supplemental": True, "required_satisfied": False})
        return (rec, None)

    # R1-F2:supervisor 消费 required 时,worker 自报 review_target 必须 == 当前 resolved slice
    # （防 check 审错 slice 却被当前 packet 消费,打穿 packet-centric 绑定）。
    want_target = context.get("review_target")
    if want_target and f.get("review_target") != want_target:
        return blocked("MALFORMED_REVIEW_OUTPUT")

    pkt = context.get("packet")
    if isinstance(pkt, dict):
        semantic_metadata = pkt.get("semantic_review_provider")
        if semantic_metadata is not None and not isinstance(semantic_metadata, dict):
            return blocked("MALFORMED_REVIEW_OUTPUT")
    source = context.get("provider_override_source")
    quote = context.get("same_provider_user_quote")
    policy = context.get("high_risk_review_provider_policy")
    target_kind = context.get("review_target_kind")
    actual = f.get("review_provider")
    impl = context.get("implement_provider")
    check_provider = context.get("check_provider")
    if (
        source not in PROVIDER_OVERRIDE_SOURCES
        or policy not in HIGH_RISK_REVIEW_PROVIDER_POLICIES
        or target_kind not in {"slice", "staged"}
        or actual not in _CHANNEL_PROVIDERS
        or impl not in _CHANNEL_PROVIDERS
        or check_provider not in _CHANNEL_PROVIDERS
        or actual != check_provider
        or (quote is not None and not isinstance(quote, str))
    ):
        return blocked("MALFORMED_REVIEW_OUTPUT")
    normalized_quote = quote.strip() if isinstance(quote, str) else ""

    if source == "cli_same_provider":
        if not normalized_quote or check_provider != impl:
            return blocked("MALFORMED_REVIEW_OUTPUT")
    elif source == "config_policy":
        if normalized_quote or target_kind != "slice":
            return blocked("MALFORMED_REVIEW_OUTPUT")
        if policy == "current":
            expected_provider = impl
        elif policy == "opposite":
            expected_provider = "claude" if impl == "codex" else "codex"
        else:
            expected_provider = policy
        if check_provider != expected_provider:
            return blocked("MALFORMED_REVIEW_OUTPUT")
    else:
        if normalized_quote or not isinstance(pkt, dict):
            return blocked("MALFORMED_REVIEW_OUTPUT")
        if target_kind == "slice" and pkt.get("risk") in {"high", "critical"}:
            return blocked("MALFORMED_REVIEW_OUTPUT")
        semantic_provider = pkt.get("semantic_review_provider")
        if semantic_provider is None:
            semantic_provider = {"provider": "opposite", "required": True}
        if not isinstance(semantic_provider, dict):
            return blocked("MALFORMED_REVIEW_OUTPUT")
        packet_provider = semantic_provider.get("provider", "opposite")
        packet_required = semantic_provider.get("required", True)
        if not isinstance(packet_required, bool):
            return blocked("MALFORMED_REVIEW_OUTPUT")
        if packet_provider == "opposite":
            expected_provider = (
                "claude" if impl == "codex" else "codex"
            ) if packet_required else impl
        elif packet_provider in _CHANNEL_PROVIDERS:
            expected_provider = packet_provider
        else:
            return blocked("MALFORMED_REVIEW_OUTPUT")
        if check_provider != expected_provider:
            return blocked("MALFORMED_REVIEW_OUTPUT")

    # 层②(supervisor 消费 channel check 作 required clean)：provider gating + deterministic 双过 + 聚合重算
    if f["review_result"] == "clean":
        # R6-F1:supervisor clean 必须有有效 packet(dict + 非空 invariants list)。packet 缺失 / 非 dict /
        # 空 invariants 既会 .get 出 traceback,又会让 aggregate([],{}) 误判 all_passed → 零 invariant 核验的
        # fail-open clean;统一 blocked(绝不静默 `or {}` 回落,那会重新引入 fail-open)。
        if not isinstance(pkt, dict):
            return blocked("MALFORMED_REVIEW_OUTPUT")
        invs = pkt.get("invariants")
        if not isinstance(invs, list) or not invs:
            return blocked("MALFORMED_REVIEW_OUTPUT")
        if context.get("supervisor_deterministic_status") != "passed" or f["deterministic_checks"] != "passed":
            return blocked("MALFORMED_REVIEW_OUTPUT")
        agg = aggregate_invariant_coverage(invs, statuses)
        if agg != "all_passed":
            return blocked("MALFORMED_REVIEW_OUTPUT")

    rec = dict(base)
    rec.update({"review_result": f["review_result"], "route_class": f["route_class"],
                "deterministic_checks": f["deterministic_checks"], "dirty_scope": f["dirty_scope"],
                "invariant_coverage": f["invariant_coverage"], "supervisor_failure": "none",
                "repairable": f["review_result"] == "findings" and f["route_class"] in _REPAIRABLE_ROUTES,
                "required_satisfied": f["review_result"] == "clean"})
    return (rec, None)


# ============================================================================
# append CLI(§4.6.7):manual / ocr_optional provider 的验证型留痕（第一版 supplemental 补充审计,
# 不满足 required provider,verify-record 路径 deferred）。内部走 normalize_review_record(mode=supplemental)
# → append_record(单一 writer / 校验)。
# ============================================================================
def _append_cli(argv) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="guru_review_record.py")
    sub = p.add_subparsers(dest="command", required=True)
    ap = sub.add_parser("append")
    ap.add_argument("--task-dir", required=True)
    ap.add_argument("--packet")
    ap.add_argument("--provider", required=True)  # manual | ocr_optional
    ap.add_argument("--reviewer")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--route-class", default="none")
    ap.add_argument("--review-target", required=True)
    ap.add_argument("--deterministic-checks", required=True)
    ap.add_argument("--dirty-scope", required=True)
    ap.add_argument("--invariant-coverage", required=True)
    ap.add_argument("--evidence-file", required=True)
    args = p.parse_args(argv)
    if args.provider not in NON_REQUIRED_PROVIDERS:
        sys.stderr.write(f"append CLI 仅 supplemental provider {sorted(NON_REQUIRED_PROVIDERS)};got {args.provider}\n")
        return 2
    if args.run_id not in os.path.basename(args.evidence_file):
        sys.stderr.write("--run-id 必须与 --evidence-file 文件名中的 run_id 一致\n")
        return 2
    slice_id = args.review_target.split(":", 1)[1] if args.review_target.startswith("slice:") else None
    fields = {
        "review_result": args.result, "route_class": args.route_class, "review_target": args.review_target,
        "review_provider": args.provider, "deterministic_checks": args.deterministic_checks,
        "dirty_scope": args.dirty_scope, "invariant_coverage": args.invariant_coverage, "_invariants": {},
    }
    channel = "ocr_optional" if args.provider == "ocr_optional" else "manual"
    record, failure = normalize_review_record(fields, {
        "mode": "supplemental", "run_id": args.run_id, "slice_id": slice_id,
        "review_target": args.review_target, "channel": channel, "worker": args.reviewer or args.provider,
    })
    if failure:
        sys.stderr.write(f"append 被拒({failure}):取值不合格\n")
        return 2
    append_record(args.task_dir, record)
    sys.stderr.write(f"[guru_review_record] appended supplemental {args.provider} record(run_id={args.run_id})\n")
    return 0


if __name__ == "__main__":
    sys.exit(_append_cli(sys.argv[1:]))
