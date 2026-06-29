#!/usr/bin/env python3
"""Guru 共享风险判定 helper（guru_gate / guru_supervise 单一来源，避免两份风险逻辑漂移）。

设计约束：**不 import guru_gate / guru_supervise**（防循环 import——guru_gate._risk_level 兼容代理
它、guru_supervise 也 import 它）。自带最小 task.json 读取，不依赖兄弟模块。
"""
from __future__ import annotations

import json
import os
import subprocess

# 与 guru_gate 历史口径字节一致（_risk_level 现兼容代理本模块）。
HIGH_RISK_LEVELS = {"high", "critical", "p0"}
LOW_RISK_LEVELS = {"low", "minor", "trivial"}

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
        if level in LOW_RISK_LEVELS:
            has_low = True
    return "low" if has_low else "unknown"


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


def implement_check_independent_required(task_dir: str, platform: str, repo_root: str):
    """P0 ③ 触发判定：返回 (required: bool, reason: str)。

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
    # level == "low"、无跨层信号、扫描成功
    if has_valid_approved_low(task_dir):
        return (False, "reviewer-approved true-low")
    return (True, "bare low without valid approval (not true-low)")
