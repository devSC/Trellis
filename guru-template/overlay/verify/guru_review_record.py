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
import os

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
NON_REQUIRED_PROVIDERS = {"manual", "ocr_optional"}
OCR_VALUES = {"optional", "disabled"}

_INVARIANT_REQUIRED_FIELDS = (
    "invariant_id", "rule", "source", "owner",
    "positive_case", "negative_case", "route_if_missing",
)


class ReviewRecordError(Exception):
    """packet schema / review record schema 非法。调用方(guru_supervise)据此记 PACKET_INVALID 等
    supervisor_failure 并 fail-closed(exit 2,不启 worker)。"""


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
    required=true ∧ provider∈{manual,ocr_optional} → ReviewRecordError(R5-F1:第一版 required 只 channel-spawnable)。"""
    if obj is None:
        return {"required": True, "provider": "opposite", "ocr": "optional"}
    if not isinstance(obj, dict):
        raise ReviewRecordError("semantic_review_provider 必须是对象")
    required = obj.get("required", True)
    provider = obj.get("provider", "opposite")
    ocr = obj.get("ocr", "optional")
    if not isinstance(required, bool):
        raise ReviewRecordError("semantic_review_provider.required 必须是 bool")
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
    ds = pkt.get("dirty_state")
    if ds is None:
        pkt["dirty_state"] = {"unrelated": []}
    elif not isinstance(ds, dict) or not isinstance(ds.get("unrelated", []), list):
        raise ReviewRecordError("slice packet dirty_state.unrelated 必须是数组")
    if not isinstance(pkt.get("deterministic_checks", []), list):
        raise ReviewRecordError("slice packet deterministic_checks 必须是数组")
    return pkt


def _reviews_path(task_dir: str) -> str:
    return os.path.join(task_dir, "review-records", "implementation-reviews.jsonl")


# review record jsonl 字段全集(append_record 写;R3-F2 review_target / R5-F2 deterministic_results /
# R5-F3 message+candidates / R7-F2 supplemental+required_satisfied 均在内)。
_RECORD_FIELDS = (
    "run_id", "slice_id", "review_target", "target_paths", "review_provider",
    "route_class", "review_result", "deterministic_checks", "dirty_scope", "invariant_coverage",
    "deterministic_results", "channel", "worker", "timestamp", "supervisor_failure", "repairable",
    "message", "candidates", "supplemental", "required_satisfied",
)


def append_record(task_dir: str, record: dict) -> None:
    """**唯一 writer**:校验 record 关键枚举后追加 review-records/implementation-reviews.jsonl。
    调用方永远经 normalize_review_record / preflight_failure_record → append_record,绝不拒绝后手写
    (BHV-005;malformed/scope/packet failure 都经此入 jsonl)。"""
    if not isinstance(record, dict):
        raise ReviewRecordError("review record 必须是 dict")
    if record.get("review_result") not in REVIEW_RESULT:
        raise ReviewRecordError(f"review_result 非法:{record.get('review_result')!r}")
    if record.get("route_class", "none") not in ROUTE_CLASS:
        raise ReviewRecordError(f"route_class 非法:{record.get('route_class')!r}")
    if record.get("supervisor_failure", "none") not in SUPERVISOR_FAILURE:
        raise ReviewRecordError(f"supervisor_failure 非法:{record.get('supervisor_failure')!r}")
    os.makedirs(os.path.dirname(_reviews_path(task_dir)), exist_ok=True)
    line = json.dumps(
        {k: record[k] for k in _RECORD_FIELDS if k in record},
        ensure_ascii=False, sort_keys=True,
    )
    with open(_reviews_path(task_dir), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def preflight_failure_record(kind: str, run_id: str, unit_id: str = None, candidates=None) -> dict:
    """supervisor-only 硬停 canonical record(R2-F1+F6/R5):**route_class=none**(非 PROCESS_DEFECT——
    它在 REPAIRABLE_IMPLEMENT_ROUTES 里会被误进 repair loop)、repairable=false。
    kind ∈ {PACKET_MISSING,PACKET_INVALID,PACKET_AMBIGUOUS,SCOPE_INVALID}。
    字段策略(R5-F6):有 unit_id → slice_id=unit_id / review_target=slice:<unit>;
    无 → slice_id=None / review_target=slice:unknown;多 packet(PACKET_AMBIGUOUS)候选入 message+candidates。"""
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
        rec["candidates"] = list(candidates)
        rec["message"] = "candidates: " + ", ".join(candidates)
    return rec
