#!/usr/bin/env python3
"""Guru 共享风险判定 helper（guru_gate / guru_supervise 单一来源，避免两份风险逻辑漂移）。

设计约束：**不 import guru_gate / guru_supervise**（防循环 import——guru_gate._risk_level 兼容代理
它、guru_supervise 也 import 它）。自带最小 task.json 读取，不依赖兄弟模块。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 使 guru_review_record 可 import
import guru_review_record  # noqa: E402  P1 单一 packet reader（它不反向 import 本模块，无循环）
import guru_contract  # noqa: E402  gate-contract route/risk 单一 schema owner

# 与 guru_gate 历史口径字节一致（_risk_level 现兼容代理本模块）。
HIGH_RISK_LEVELS = {"high", "critical", "p0"}
MEDIUM_RISK_LEVELS = {"medium", "moderate", "normal", "p1", "p2"}
LOW_RISK_LEVELS = {"low", "minor", "trivial"}
# P1 §4.5.9：packet risk_reasons 命中任一即 high。
RISK_REASON_KEYWORDS = {
    "protocol_migration", "cross_layer", "stateful_cache_merge", "db_migration",
    "payment", "ads", "permission", "privacy",
}
HIGH_RISK_TEXT_KEYWORDS = RISK_REASON_KEYWORDS | {
    "schema", "migration", "workflow", "hook", "gate", "runtime", "auth",
    "login", "account", "security", "release", "publish", "compliance",
    "数据采集", "隐私", "权限", "支付", "广告", "门禁", "工作流", "迁移",
}
MEDIUM_RISK_TEXT_KEYWORDS = {
    "bug", "behavior", "logic", "test", "state", "controller", "usecase",
    "repository", "api", "interaction", "local behavior", "业务", "行为",
    "测试", "状态", "接口",
}
LOW_RISK_TEXT_KEYWORDS = {
    "color", "colour", "copy", "text", "label", "typo", "comment", "format",
    "spacing", "style", "icon", "文案", "颜色", "注释", "格式", "样式",
}
AMBIGUOUS_REQUIREMENTS_TEXT_KEYWORDS = {
    "unclear", "ambiguous", "unspecified", "underspecified", "under-specified",
    "not clear", "not specified", "不清楚", "不明确", "未明确", "未指定",
    "有歧义", "需求模糊", "描述模糊", "需求不清", "范围不清",
}

ROUTE_SMALL_INLINE = "small_inline"
ROUTE_MICRO_TASK = "micro_task"
ROUTE_LITE_TASK = "lite_task"
ROUTE_FULL_CHAIN = "full_chain"

# P0 ③ 无 packet 触发信号：storage 关键词（路径子串，小写匹配）。裸短词（db/bloc）用边界形式
# 避免子串误报（裸 "db" 会命中 "feedback"，裸 "bloc" 会命中 "block"）。
STORAGE_KEYWORDS = (
    "datasource", "data_source", "dao", "database",
    "/db/", "_db.", "db_", "cache", "storage", "local_data_source",
)
# 路径 → layer group（命中 ≥2 组视为跨层）。
LAYER_GROUPS = {
    "api": ("/api", "apiclient", "remote_data_source", "remotedatasource", "/remote"),
    "dto_model": ("/dto", "/models/", "/model/", "/entity", "/entities"),
    "repository": ("repositor", "/repo/"),  # repositor 覆盖 repository/repositories/..._impl
    "datasource": ("datasource", "data_source", "/dao", "database", "/db/", "cache", "storage"),
    "domain": ("usecase", "use_case", "/domain/"),
    # bloc 用边界（/bloc、_bloc、bloc/）避免误命中 "block"。
    "controller": ("controller", "/state/", "/bloc", "_bloc", "bloc/", "/provider", "viewmodel", "view_model"),
    "ui": ("/widget", "/page", "/screen", "/ui/", "/view/"),
}

# 跨层/storage 判定只看**代码改动**：排除 .trellis 任务元数据、文档、纯配置/锁文件，避免任务名或
# 文档路径（如 .trellis/tasks/cache-fix/、docs/storage.md）被误判为 storage/跨层信号而误触独立 check。
_SCAN_SKIP_PREFIXES = (".trellis/", ".git/", "docs/", "doc/")
_SCAN_SKIP_EXTS = (".md", ".txt", ".json", ".yaml", ".yml", ".lock", ".log")


class RiskScanError(Exception):
    """git 路径扫描失败（git 不可用 / 非 git worktree / porcelain 退出非零或不可解码）。
    调用方据此 fail-closed（unknown_scan_failed：禁 true-low 降级、按需启用独立 check）。"""


def _task_json(task_dir: str) -> dict:
    try:
        with open(os.path.join(task_dir, "task.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def task_risk_level(task_dir: str) -> str:
    """task.json 声明的风险等级。缺/不可判 → "unknown"（与历史 guru_gate._risk_level 同语义）。

    **任意 high 信号优先于 low**（fail-closed）：自相矛盾的 task.json——如 top-level
    `risk_level=high` 叠加 nested `guru_risk.low_risk=true`——一律从严判 high，绝不让 nested
    low 抢先 return 而吞掉 high 信号、绕过独立 check。故先收集所有 low 信号（has_low），
    任一处出现 high 立即判 high；扫完无 high 才考虑 low。
    """
    data = _task_json(task_dir)
    candidates = [data.get("risk_level"), data.get("guru_risk_level")]
    has_low = False
    for key in ("guru_risk", "risk"):
        obj = data.get(key)
        if isinstance(obj, dict):
            if obj.get("high_risk") is True:
                return "high"
            if obj.get("low_risk") is True:
                has_low = True
            candidates.extend([obj.get("risk_level"), obj.get("level")])
        elif isinstance(obj, str):
            candidates.append(obj)
    for value in candidates:
        if not isinstance(value, str):
            continue
        level = value.strip().lower().replace("_", "-")
        if level in HIGH_RISK_LEVELS:
            return "high"
        if level in MEDIUM_RISK_LEVELS:
            return "medium"
        if level in LOW_RISK_LEVELS:
            has_low = True
    return "low" if has_low else "unknown"


def task_route_and_risk(task_dir: str) -> tuple[str, str, str]:
    """Return (route, risk, source) from gate-contract first, then task metadata.

    Invalid/missing contracts intentionally fall back to task metadata so legacy
    full-chain tasks keep their strict behavior without inheriting new packet
    requirements unless they explicitly declare high/full risk.
    """
    contract, read_error = guru_contract.load_contract(task_dir)
    if isinstance(contract, dict) and not read_error:
        route = guru_contract.contract_route(contract)
        risk = guru_contract.contract_risk(contract)
        if not guru_contract.validate_contract(contract):
            return route, risk, "gate-contract.json"
        if risk == "high" and route != ROUTE_FULL_CHAIN:
            return ROUTE_FULL_CHAIN, "high", "invalid gate-contract.json"

    data = _task_json(task_dir)
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    route = str(meta.get("route") or data.get("route") or "").strip().lower().replace("-", "_")
    if route not in {ROUTE_SMALL_INLINE, ROUTE_MICRO_TASK, ROUTE_LITE_TASK, ROUTE_FULL_CHAIN}:
        chain = str(meta.get("guru_chain") or data.get("guru_chain") or "").strip().lower()
        route = ROUTE_FULL_CHAIN if chain == "full" else ""
    risk = str(meta.get("risk") or data.get("risk") or task_risk_level(task_dir)).strip().lower()
    if risk in HIGH_RISK_LEVELS:
        risk = "high"
    elif risk in MEDIUM_RISK_LEVELS:
        risk = "medium"
    elif risk in LOW_RISK_LEVELS:
        risk = "low"
    else:
        risk = "unknown"
    return route, risk, "task.json"


def full_chain_packet_required(task_dir: str) -> tuple[bool, str]:
    """High-risk full-chain tasks need an explicit slice packet before workers.

    This is intentionally narrow: unknown/missing contracts preserve legacy
    strict full-chain behavior without forcing packets onto old doc-only tasks.
    """
    route, risk, source = task_route_and_risk(task_dir)
    if route == ROUTE_FULL_CHAIN and risk == "high":
        return True, f"{source} route=full_chain risk=high"
    return False, f"{source} route={route or 'unknown'} risk={risk}"


def _keyword_flags(text: str, keywords: set) -> list:
    haystack = text.lower()
    flags = []
    for keyword in keywords:
        normalized = keyword.lower()
        if normalized.isascii():
            matched = re.search(
                rf"(?<![a-z0-9_]){re.escape(normalized)}(?![a-z0-9_])",
                haystack,
            )
        else:
            matched = normalized in haystack
        if matched:
            flags.append(keyword)
    return sorted(flags)


def _explicit_ambiguity_flags(text: str) -> list:
    """Return explicit requirement-ambiguity markers without substring traps."""
    return _keyword_flags(text, AMBIGUOUS_REQUIREMENTS_TEXT_KEYWORDS)


def path_high_risk_flags(paths) -> list:
    flags = []
    normalized = [str(p).lower().replace("\\", "/") for p in paths]
    if has_cross_layer_or_storage(normalized):
        flags.append("cross_layer_or_storage")
    for path in normalized:
        for keyword in (
            ".trellis/workflow.md", ".trellis/config.yaml", ".codex/", ".claude/",
            "hooks/", "/hooks/", "workflow", "guru_gate.py", "guru_risk.py",
            "guru_contract.py", "guru_supervise.py", "schema", "migration",
            "payment", "ads", "permission", "privacy",
        ):
            if keyword in path:
                flags.append(keyword.strip("/"))
    return sorted(set(flags))


def assess_intake(
    description: str = "",
    paths=None,
    commit_requested: bool = False,
    *,
    requirements_clear: bool | None = None,
    coupling: str | None = None,
    reversible: bool | None = None,
    verification_scope: str | None = None,
) -> dict:
    """Classify incoming Guru work into risk + route.

    This is intentionally conservative: any high-risk signal wins; unknown work
    never becomes low.  The helper is side-effect free so workflow hooks, skills,
    and tests can share the same table.
    """
    paths = list(paths or [])
    coupling = str(coupling or "unknown").strip().lower().replace("-", "_")
    verification_scope = str(verification_scope or "unknown").strip().lower().replace("-", "_")
    high_flags = _keyword_flags(description, HIGH_RISK_TEXT_KEYWORDS) + path_high_risk_flags(paths)
    medium_flags = _keyword_flags(description, MEDIUM_RISK_TEXT_KEYWORDS)
    low_flags = _keyword_flags(description, LOW_RISK_TEXT_KEYWORDS)
    ambiguity_flags = _explicit_ambiguity_flags(description)
    explicitly_ambiguous = requirements_clear is False or bool(ambiguity_flags)
    reasons = []
    if high_flags:
        return {
            "risk": "high",
            "route": ROUTE_FULL_CHAIN,
            "confidence": 0.95,
            "reasons": [f"high-risk signal: {flag}" for flag in sorted(set(high_flags))],
            "risk_flags": sorted(set(high_flags)),
            "needs_user_choice": False,
            "recommended_contract": ROUTE_FULL_CHAIN,
        }
    bounded_behavior = (
        requirements_clear is True
        and not explicitly_ambiguous
        and coupling == "local"
        and reversible is True
        and verification_scope == "focused"
        and 0 < len(paths) <= 3
    )
    if low_flags and not medium_flags and not explicitly_ambiguous and 0 < len(paths) <= 3:
        return {
            "risk": "low",
            "route": ROUTE_SMALL_INLINE,
            "confidence": 0.9,
            "reasons": [f"mechanical low-risk signal: {flag}" for flag in sorted(set(low_flags))],
            "risk_flags": sorted(set(low_flags)) + ["mechanical_change"],
            "needs_user_choice": False,
            "brainstorm_required": False,
            "recommended_contract": ROUTE_SMALL_INLINE,
        }
    if bounded_behavior:
        return {
            "risk": "low",
            "route": ROUTE_MICRO_TASK,
            "confidence": 0.9,
            "reasons": ["requirements clear; local coupling; reversible; focused verification"],
            "risk_flags": sorted(set(medium_flags)) + ["bounded_local_change"],
            "needs_user_choice": False,
            "brainstorm_required": False,
            "recommended_contract": ROUTE_MICRO_TASK,
        }
    if medium_flags or explicitly_ambiguous:
        ambiguity_reasons = []
        if explicitly_ambiguous:
            ambiguity_reasons = (
                [f"explicit requirements ambiguity: {flag}" for flag in ambiguity_flags]
                or ["requirements or acceptance criteria are not yet clear"]
            )
        return {
            "risk": "medium",
            "route": ROUTE_LITE_TASK,
            "confidence": 0.8,
            "reasons": ambiguity_reasons + [
                f"medium-risk signal: {flag}" for flag in sorted(set(medium_flags))
            ],
            "risk_flags": sorted(set(
                medium_flags + (["requirements_ambiguous"] if explicitly_ambiguous else [])
            )),
            "needs_user_choice": explicitly_ambiguous,
            "brainstorm_required": explicitly_ambiguous,
            "recommended_contract": ROUTE_LITE_TASK,
        }
    if paths:
        reasons.append("paths present but no low-risk classifier match")
    else:
        reasons.append("no concrete low-risk evidence")
    return {
        "risk": "medium",
        "route": ROUTE_LITE_TASK,
        "confidence": 0.55,
        "reasons": reasons,
        "risk_flags": ["unknown_non_low"],
        "needs_user_choice": True,
        "brainstorm_required": True,
        "recommended_contract": ROUTE_LITE_TASK,
    }


def scan_paths(repo_root: str) -> set:
    """用 `git -C <root> status --porcelain=v1 -z -uall` 收集 staged/unstaged/renamed/deleted/
    untracked 路径（新建文件常未 tracked，`git diff` 会漏）。**必须 -uall**：默认 git 把整个未跟踪
    目录折叠成单条 `lib/`，丢失 `lib/data/x_datasource.dart` 层级 → 跨层/storage 检测漏判；
    -uall 递归列出每个未跟踪文件完整路径。git 不可用/非 git/失败 → 抛 RiskScanError。"""
    try:
        proc = subprocess.run(
            ["git", "-C", repo_root, "status", "--porcelain=v1", "-z", "-uall"],
            capture_output=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RiskScanError(f"git status 不可用：{exc}") from exc
    if proc.returncode != 0:
        raise RiskScanError(
            f"git status 退出 {proc.returncode}：{proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    paths: set = set()
    # porcelain v1 -z：每条 "XY PATH"；rename/copy 额外跟一个 from-path token（无 XY 前缀）。
    for rec in proc.stdout.split(b"\0"):
        if not rec:
            continue
        if len(rec) >= 4 and rec[2:3] == b" ":
            path = rec[3:].decode("utf-8", "replace")
        else:
            path = rec.decode("utf-8", "replace")  # rename/copy 的 from-path
        if path:
            paths.add(path)
    return paths


def _is_scannable(path: str) -> bool:
    """只让代码改动参与跨层/storage 判定（排除 .trellis 元数据、文档、纯配置/锁文件）。"""
    pl = path.lower().lstrip("./")
    if any(pl.startswith(pre) or ("/" + pre) in pl for pre in _SCAN_SKIP_PREFIXES):
        return False
    return os.path.splitext(pl)[1] not in _SCAN_SKIP_EXTS


def _layer_of(path: str):
    pl = path.lower()
    for layer, kws in LAYER_GROUPS.items():
        if any(k in pl for k in kws):
            return layer
    return None


def has_cross_layer_or_storage(paths) -> bool:
    """命中 storage 关键词，或路径跨 ≥2 个 layer group → True（仅对可扫描代码路径判定）。"""
    scannable = [p for p in paths if _is_scannable(p)]
    for p in scannable:
        pl = p.lower()
        if any(k in pl for k in STORAGE_KEYWORDS):
            return True
    layers = {layer for p in scannable if (layer := _layer_of(p))}
    return len(layers) >= 2


def has_valid_approved_low(task_dir: str) -> bool:
    """合法 approved-low：task.json `guru_risk: {level: low, reviewer_approved: true,
    approved_by, approved_at, evidence}`。裸 `risk_level=low` 不算 true-low。"""
    obj = _task_json(task_dir).get("guru_risk")
    if not isinstance(obj, dict):
        return False
    if str(obj.get("level", "")).strip().lower() != "low":
        return False
    if obj.get("reviewer_approved") is not True:
        return False
    return all(
        isinstance(obj.get(k), str) and obj.get(k).strip()
        for k in ("approved_by", "approved_at", "evidence")
    )


def scan_dirty_paths(repo_root: str) -> set:
    """P1 scope preflight 的**唯一 dirty path 来源**：复用 scan_paths 的
    `git status --porcelain=v1 -z -uall`（含 untracked/rename/delete，与 P0 同口径，不重造 git diff 弱扫描）。"""
    return scan_paths(repo_root)


def slice_packet_risk(task_dir: str, unit_id):
    """P1 §4.5.8/4.5.9：读 packet risk/risk_reasons → "high" | "low" | None。
    经 guru_review_record.load_packet（单一 packet reader）；packet 非法/缺失由 load_packet 抛
    ReviewRecordError **上抛**（由 supervise preflight 捕获记 PACKET_INVALID/PACKET_MISSING，此处不吞）。
    unit_id=None（无 packet）→ None（回落 P0）。"""
    if not unit_id:
        return None
    pkt = guru_review_record.load_packet(task_dir, unit_id)  # ReviewRecordError 上抛
    risk = pkt.get("risk")  # 已规范化：high|critical|low|None
    reasons = pkt.get("risk_reasons", [])
    if risk in ("high", "critical"):
        return "high"
    if isinstance(reasons, list) and any(r in RISK_REASON_KEYWORDS for r in reasons):
        return "high"
    if risk == "low":
        return "low"
    return None


def _p0_implement_check_independent_required(task_dir: str, platform: str, repo_root: str):
    """P0 ③ 触发判定（原 L160-183 逻辑原样保留，供 unit_id=None / 无 packet risk 回落）。

    flutter 下：high | unknown | 跨层/storage 信号 → 须独立阻断 check（fail-closed）；
    git 扫描失败 → unknown_scan_failed 亦 fail-closed；仅「合法 approved-low + 无跨层信号 + 扫描成功」
    才算 true-low（不要求）。非 flutter → 不要求。
    """
    if platform != "flutter":
        return (False, "non-flutter")
    level = task_risk_level(task_dir)
    if level == "high":
        return (True, "high-risk")
    try:
        paths = scan_paths(repo_root)
    except RiskScanError as exc:
        return (True, f"unknown_scan_failed fail-closed：{exc}")
    if has_cross_layer_or_storage(paths):
        return (True, "cross-layer/storage path signal (overrides low)")
    if level == "unknown":
        return (True, "unknown-risk fail-closed")
    if level == "medium":
        return (True, "medium-risk")
    # level == "low"、无跨层信号、扫描成功
    if has_valid_approved_low(task_dir):
        return (False, "reviewer-approved true-low")
    return (True, "bare low without valid approval (not true-low)")


def implement_check_independent_required(task_dir: str, platform: str, repo_root: str, unit_id=None):
    """P1 ③ 触发判定：返回 (required: bool, reason: str)。slice_packet.risk > task（§4.5.8）。

    三分支（R3-F3/R8-F1）：packet_risk=="high" → required（先于 task）；packet_risk=="low" → **slice 级
    override 直接 (False)**（SSOT §4.5.9，不被 task/git 抬高）；packet_risk is None / unit_id=None →
    回落 _p0_（P0 task.json+git scan，字节兼容）。packet 非法/缺失经 slice_packet_risk 上抛 ReviewRecordError。
    """
    if platform == "flutter" and unit_id:
        packet_risk = slice_packet_risk(task_dir, unit_id)  # ReviewRecordError 上抛
        if packet_risk == "high":
            return (True, "slice-packet high-risk")
        if packet_risk == "low":
            return (False, "slice-packet low-risk")
        # packet_risk is None（packet 无 risk/unknown）→ 回落 P0
    return _p0_implement_check_independent_required(task_dir, platform, repo_root)
