#!/usr/bin/env python3
"""Guru 五阶段 Gate 校验 + 追溯矩阵（结构底线检查；语义判定由 review loop 负责）。

Gate 确认模型 SSOT：.trellis/spec/harness/gate/gate-confirmation-model.md

用法:
  python3 guru_gate.py auto [task_dir]            # 按 task.json status + artifact 渐进校验（worktree.yaml verify 用这个）
  python3 guru_gate.py requirements <task_dir>    # 需求 Gate：prd.md（含 BHV 编号纪律）
  python3 guru_gate.py overview <task_dir>        # Full/legacy artifact Gate；lite_task 不调用
  python3 guru_gate.py detail <task_dir>          # Full/legacy artifact Gate；lite_task 不调用
  python3 guru_gate.py implement <task_dir>       # 实现 Gate：implement.md trace 四节（切片挂 UNIT）
  python3 guru_gate.py trace-matrix <task_dir> [--write] [--strict] [--require-req-uc]
                                                  # 追溯矩阵：BHV × REQ-UC × owner × UNIT × 测试 × 切片 + 孤儿清单
                                                  # --write 写入 <task_dir>/trace-matrix.md；--strict 有断链时 exit 2
                                                  # --require-req-uc 强制 BHV 标题须带 [REQ-UC-XXX]（亦读 task.json require_req_uc）
  python3 guru_gate.py trace-aggregate <version_dir> [--include-completed]
                                                  # 版本级聚合：反查指向该需求包版本目录的 task → 行展开
                                                  # 写 <version_dir>/traceability.md 生成区（§15.4 单表，回填手维护列）
                                                  # 默认仅扫 .trellis/tasks/<task>；--include-completed 加扫 archive/<YYYY-MM>/<task>
                                                  # fail-closed：traceability 不在 manifest canonical_excludes 时拒写（避免触发 requirements digest）
  python3 guru_gate.py confirm [requirements|detail] [task_dir] [--via-agent]
                                                  # route-aware 人工确认：Lite 只确认 requirements 一次；Full v2 一次批量确认 requirements + risk + 不可逆设计
                                                  # Full v2 使用省略 gate 的 confirm（confirm detail 仅兼容）；legacy 才保留 requirements/detail 分阶段确认
                                                  # strict 模式（默认）：仅限用户本人在交互式终端运行，agent 代跑被拒
                                                  # soft 模式（config guru.gate_mode: soft）：用户对话确认后 agent 以 --via-agent 代跑（记录留痕标注）
  python3 guru_gate.py record-review <overview|detail> <task_dir> --result clean|findings --max-severity none|low|medium|high|critical --reviewer clean-context --run-id <id> --evidence <text> [--finding-class <class>] [--deletion-audit <summary>]
                                                  # 记录概要/详细设计 review 证据；当前产物 digest 下需两个不同 run-id 的 clean 记录，默认至少一条 reviewer 含 adversarial
  python3 guru_gate.py grill-done <gate> [task_dir] [--via-agent] --user-quote "<用户确认原话>"
                                                  # 兼容旧流程：记录 design-grill 已完成（不再作为新 gate 放行条件）
  python3 guru_gate.py grill-skip <gate> [task_dir] [--via-agent] --user-quote "<跳过理由>"
                                                  # 兼容旧流程：仅 low-risk 非 full 的 overview/detail 可跳过（留原因）
  python3 guru_gate.py status [task_dir]          # 查看需求确认、概要/详细 review 证据、详细确认状态与下一步
  python3 guru_gate.py check-start [task_dir]     # before_start 钩子用：只证明 START_READY（下一步仅 task.py start）
  python3 guru_gate.py check [task_dir]           # 兼容别名：等同 check-start，不代表实现/提交放行
  python3 guru_gate.py check-implementation [task_dir]
                                                  # Full 实现/检查 Worker 前置；Lite 不需要 Worker（该命令只保留兼容只读校验）
  python3 guru_gate.py check-commit [task_dir]    # route-aware 提交前置：Lite 校验标准任务/当前确认/in_progress/合同 scope；Full 另需 implementation review clean
                                    [--slice <id>] [--aggregate --slice <id> ...]
                                                  # Full/high exact slice Gate；aggregate 仅 all-missing bootstrap
  python3 guru_gate.py record-slice-commit <task_dir> [--aggregate] --slice <id> [--slice <id> ...] --review-run-id <id>
                                                  # 主会话 work commit 后的官方 append-only receipt producer
  python3 guru_gate.py commit-plan [task_dir] [--write]
                                                  # 输出提交计划 JSON；--write 同步写 task-local commit-plan.json mutable evidence
  python3 guru_gate.py intake [task_dir] --description "<需求>" [--path <path> ...] [--commit-requested] [--write-contract]
                                                  # 收到任务时风险分流；可将 micro/lite/full 合同写入任务目录
  python3 guru_gate.py init-contract <task_dir> --route <route> --risk <risk> [--allowed-path <path> ...] [--max-files <n>]
                                                  # 用 guru_contract.default_contract + validator 写 gate-contract.json
  python3 guru_gate.py record-degradation <task_dir> --gate <gate> --reason <reason> --command <cmd> --check <name:status[:evidence]> ...
                                                  # 追加 task-local gate-degradations.jsonl；写入前按合同验证
  python3 guru_gate.py slice-plan <task_dir>      # 只读输出 full-chain slice packet 执行计划 JSON
  python3 guru_gate.py digest <gate> [task_dir]   # 输出该阶段产物的确认快照摘要（排查快照失配用）

编号纪律:
  BHV-NNN   行为编号。prd.md 中以标题定义（如 `### BHV-001 玩家选择 Hammer`）；创建后不复用、不重排，删除留洞。
  UNIT-slug 设计单元编号。design.md §2 中以标题定义（如 `### UNIT-hammer-usecase`）；语义 slug。
  下游引用一律写裸编号（兼容未来的 [[file#BHV-001]] 双链包裹——解析按编号 token 识别）。

Route 与兼容产物:
  `gate-contract.json.route` 是执行权威；禁止用 task.json `guru_chain` 推导 lite_task。
  full  完整五阶段链：目录级设计包（task.json `design_package` 指向，含 README.md/design-main.md/chapters/）。
  light 仅是存量单文件 design.md §1/§2 的兼容产物形态，不等于 lite_task。

退出码: 0=通过/合法跳过; 2=Gate 拦截(stderr 给缺口清单)。
设计约束: 只查结构存在性与引用闭合, 不做语义判断——"判不动的规则不进脚本"。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys

# 共享风险 helper（单一来源，防两份风险逻辑漂移）：guru_gate 作脚本运行时其目录已在 sys.path[0]，
# 被 guru_supervise import 时其目录也已加入——此处显式补一遍兜底奇怪调用形态。guru_risk **不 import
# guru_gate**（防循环）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guru_risk  # noqa: E402
import guru_contract  # noqa: E402
import guru_delivery_policy  # noqa: E402
import guru_review_record  # noqa: E402

PASS, BLOCK = 0, 2

# 不用 \b 词边界：Python 的 \b 把 CJK 视作 word 字符，"执行BHV-001"/"UNIT-x执行" 等
# 中文相邻编号会因边界失配被漏掉，导致 trace 误判孤儿（假拦/假通过）。
# DEF 靠行首标题(^#{2,5}\s+)锚定；REF 直匹配编号本体。slug 首字符限 [a-z]（语义 slug 字母起头）。
BHV_DEF = re.compile(r"^#{2,5}\s+(BHV-\d+)[^\n]*$", re.M)
UNIT_DEF = re.compile(r"^#{2,5}\s+(UNIT-[a-z][a-z0-9-]*)[^\n]*$", re.M)
BHV_REF = re.compile(r"(BHV-\d+)")
UNIT_REF = re.compile(r"(UNIT-[a-z][a-z0-9-]*)")
# 需求场景承接（REQ-UC = 需求源 use case；与 overview 的 UC-<序号> 是两套独立编号，命名消歧）
REQ_UC_REF = re.compile(r"(REQ-UC-\d+)")

# 双轨制（完整五阶段链=目录级设计包；轻量链=单文件 design.md）
# doc_type 分类【运行时】从已装的 detail-structure-single-source.md §2 表解析（见 _doc_type_taxonomy），
# 使 gate 自适应平台（flutter/go/ios/h5 的 doc_type 类目各异）。下列 fallback 是 flutter 基线，仅在
# SSOT 缺失/解析空时使用（向后兼容测试夹具与上游 CLI 装的项目）。
_FALLBACK_V1 = {"controller", "usecase", "repository-datasource"}
_FALLBACK_NINE = _FALLBACK_V1 | {"page-entry", "service", "db-dao", "api-network",
                                 "config-l10n", "external-platform"}
_TAXONOMY_CACHE = {}
DOC_TYPE_REF = re.compile(r"(?:detail_)?doc_type\s*[=:：]\s*`?([a-z][a-z0-9-]*)`?")
CHAPTER_FILE_REF = re.compile(r"chapters/([A-Za-z0-9_][A-Za-z0-9_.-]*\.md)")
L2_EXEMPT_LINE = re.compile(r"L2豁免[^\n]*")

DETAIL_SECTION_PATTERNS = [
    ("单元职责", r"单元职责"),
    ("行为定义", r"行为定义"),
    ("核心数据结构", r"核心数据结构"),
    ("逐行为设计", r"逐行为设计"),
    ("状态/边界", r"状态管理|状态与事务|状态\s*/\s*边界管理|状态\s*/\s*边界"),
    ("类型专属章节", r"Widget\s*设计|View\s*设计|导航设计|数据合同|路由\s*/\s*渲染\s*/\s*SEO"),
    ("测试映射", r"测试映射"),
    ("不得补造清单", r"不得补造清单|不得补造"),
]

DETAIL_CONTRACT_PATTERNS = [
    ("行为定义/清单", r"行为清单|行为定义|承接.{0,8}行为"),
    ("失败收口", r"失败.{0,8}收口|失败如何|错误类型表|异常表|错误映射"),
    ("测试映射", r"测试映射|哪些测试"),
    ("不得补造声明", r"不得.{0,8}补造|不在此补造|不决定|不拥有"),
]

BRAINSTORM_EVIDENCE_LABELS = [
    ("Skill loaded", ("skill loaded",)),
    ("Repository evidence inspected", ("repository evidence inspected",)),
    ("Domain/terminology triggers", ("domain/terminology triggers", "domain grill triggers")),
    ("Current code vs user intent conflicts", ("current code vs user intent conflicts",)),
    ("Product decisions confirmed", ("product decisions confirmed",)),
    ("Open product/scope/risk questions", ("open product/scope/risk questions",)),
]
BRAINSTORM_PLACEHOLDERS = {
    "",
    "pending",
    "tbd",
    "todo",
    "待定",
    "未填写",
    "未确认",
}
BRAINSTORM_NEGATIVE_PREFIXES = (
    "none",
    "not triggered",
    "no open questions",
    "无",
    "没有",
    "不触发",
)
BRAINSTORM_RECOVERY = "load trellis-brainstorm, complete Domain Grill / one-question loop, then update prd.md"
CONFIRMATION_HINT_RE = re.compile(r"\b(?:user_quote|confirmed_ref)\b\s*[:=：]", re.I)
CURRENT_TURN_CONFIRMATION_RE = re.compile(r"\bcurrent[-_ ]turn[-_ ]confirmation\b\s*[:=：]", re.I)
CONFIRMED_STATUS_RE = re.compile(r"(?<!`)\bconfirmation_status\s*[:=：]\s*user_confirmed(?:_with_edits)?\b", re.I)
EVIDENCE_READY_STATUS_RE = re.compile(r"(?<!`)\bconfirmation_status\s*[:=：]\s*evidence_ready\b", re.I)
OQ_ID_RE = re.compile(r"\bOQ-\d+\b", re.I)
DECISION_ID_RE = re.compile(r"\b(?:DEC|REQ|BHV)-\d+\b", re.I)
NEXT_ACTION_RE = re.compile(r"\b(?:next_question|next_action)\b|下一[个步]|下一问|one-question loop|保持\s*open", re.I)
QUESTION_LOOP_REQUIRED_HEADERS = {
    "oq_id",
    "asked_at",
    "question",
    "recommended_answer",
    "tradeoff",
    "user_quote",
    "resolved_decision",
    "artifact_update",
}


def _logical_blocks(section: str) -> list:
    blocks = []
    current = []
    for raw_line in section.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            if current:
                current.append(line)
            continue
        starts_item = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line)
        is_nested = re.match(r"^\s{2,}(?:[-*+]|\d+[.)])\s+", line)
        if starts_item and not is_nested and current:
            blocks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return [b for b in blocks if b]


def _unfenced_lines(text: str) -> list:
    lines = []
    in_fence = False
    for raw_line in text.splitlines():
        if re.match(r"^\s*```", raw_line):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(raw_line)
    return lines


def _section_between_labels(section: str, label: str) -> str:
    aliases = []
    for known_label, known_aliases in BRAINSTORM_EVIDENCE_LABELS:
        if known_label == label:
            aliases = list(known_aliases)
            break
    if not aliases:
        aliases = [label.lower()]
    start = None
    lines = section.splitlines()
    for i, raw_line in enumerate(lines):
        line = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", raw_line).strip().lower()
        if any(line.startswith(alias) for alias in aliases):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    other_aliases = []
    for other_label, known_aliases in BRAINSTORM_EVIDENCE_LABELS:
        if other_label != label:
            other_aliases.extend(known_aliases)
    other_aliases.append("question loop log")
    for j in range(start + 1, len(lines)):
        candidate = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", lines[j]).strip().lower()
        if any(candidate.startswith(alias) for alias in other_aliases):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def _question_policy(section: str) -> str:
    match = re.search(
        r"(?im)^\s*(?:[-*+]\s+)?question_policy\s*[:=：]\s*([^\s`|,;]+)\s*$",
        section,
    )
    return match.group(1).lower() if match else ""


def _question_policy_block(section: str) -> str:
    match = re.search(r"(?im)^#{3,6}\s+Question Policy\s*$", section)
    if not match:
        return ""
    rest = section[match.end():]
    next_heading = re.search(r"(?m)^#{2,6}\s+", rest)
    return rest[: next_heading.start()].strip() if next_heading else rest.strip()


def _question_loop_headers(section: str) -> set:
    match = re.search(r"(?im)^#{3,6}\s+Question Loop Log\s*$", section)
    if not match:
        return set()
    for raw_line in section[match.end():].splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if not stripped.startswith("|"):
            if stripped.startswith("#"):
                break
            continue
        if _is_table_separator(stripped):
            continue
        return {cell.strip().lower().strip("`") for cell in _split_table_cells(stripped)}
    return set()


def _question_loop_is_structured(section: str) -> bool:
    headers = _question_loop_headers(section)
    return QUESTION_LOOP_REQUIRED_HEADERS.issubset(headers)


def _is_negative_evidence_value(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in BRAINSTORM_PLACEHOLDERS or normalized.startswith(BRAINSTORM_NEGATIVE_PREFIXES)


def _positive_decision_blocks(product_block: str, value) -> list:
    if value is None:
        return []
    has_child_decision = bool(re.search(r"\bDEC-\d+\b", product_block, re.I) or re.search(r"\bconfirmed\b|确认|拍板|决定", product_block, re.I))
    if _is_negative_evidence_value(value) and not has_child_decision:
        return []
    blocks = _logical_blocks(product_block)
    decision_blocks = [
        block for block in blocks
        if re.search(r"\bDEC-\d+\b", block, re.I) or re.search(r"\bconfirmed\b|确认|拍板|决定", block, re.I)
    ]
    if decision_blocks:
        return decision_blocks
    return [product_block] if product_block.strip() else [value]


def _split_table_cells(line: str) -> list:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$", line))


def _table_rows_with_status(prd: str, status_re) -> list:
    rows = []
    header_cells = []
    for line in _unfenced_lines(prd):
        stripped = line.strip()
        if not stripped.startswith("|"):
            header_cells = []
            continue
        if _is_table_separator(stripped):
            continue
        cells = _split_table_cells(stripped)
        if not header_cells:
            header_cells = cells
            continue
        context = "\n".join((" | ".join(header_cells), stripped))
        if not (
            status_re.search(stripped) or (
                re.search(r"\bconfirmation_status\b|\bstatus\b|确认状态", " | ".join(header_cells), re.I)
                and status_re.search(context)
            )
        ):
            continue
        evidence = []
        for index, name in enumerate(header_cells):
            normalized = name.strip().lower().strip("`")
            if normalized in {"user_quote", "confirmed_ref"} and index < len(cells) and cells[index].strip():
                evidence.append(f"{normalized}: {cells[index].strip()}")
        rows.append("\n".join([context, *evidence]))
    return rows


def _confirmation_blocks(prd: str) -> list:
    blocks = [
        block for block in _logical_blocks(prd)
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", block) and CONFIRMED_STATUS_RE.search(block)
    ]
    blocks.extend(_table_rows_with_status(prd, re.compile(r"\buser_confirmed(?:_with_edits)?\b", re.I)))
    return blocks


def _evidence_ready_blocks(prd: str) -> list:
    blocks = [
        block for block in _logical_blocks(prd)
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", block) and EVIDENCE_READY_STATUS_RE.search(block)
    ]
    blocks.extend(_table_rows_with_status(prd, re.compile(r"\bevidence_ready\b", re.I)))
    return blocks


def _user_quote_values(block: str) -> set:
    values = set()
    for match in re.finditer(r"\buser_quote\b\s*[:=：]\s*([\"“]?)(.+?)\1\s*$", block, re.I | re.M):
        values.add(match.group(2).strip())
    return values


def _stale_confirmation_upgrade_detected(prd: str) -> bool:
    evidence_blocks = _evidence_ready_blocks(prd)
    confirmed_blocks = _confirmation_blocks(prd)
    if any(CONFIRMED_STATUS_RE.search(block) for block in evidence_blocks):
        return True
    evidence_quotes = set()
    for block in evidence_blocks:
        evidence_quotes.update(_user_quote_values(block))
    if not evidence_quotes:
        return False
    for block in confirmed_blocks:
        if _user_quote_values(block) & evidence_quotes:
            return True
    return False


def _has_batch_confirmation_marker(text: str) -> bool:
    return bool(re.search(r"批量确认|一次性确认|这几个都按推荐|batch confirmation|covered_oq|covered_decision|covered_refs", text, re.I))


def _batch_confirmation_problems(prd: str) -> list:
    problems = []
    blocks = _confirmation_blocks(prd)
    if not _has_batch_confirmation_marker(prd):
        quote_counts = {}
        for block in blocks:
            match = re.search(r"\buser_quote\b\s*[:=：]\s*([\"“]?)(.+?)\1\s*$", block, re.I | re.M)
            if match:
                quote = match.group(2).strip()
                if quote in {"好", "继续", "按推荐", "ok", "OK"} or re.search(r"批量确认|一次性确认", quote):
                    quote_counts[quote] = quote_counts.get(quote, 0) + 1
        if not any(count > 1 for count in quote_counts.values()):
            return problems
    for block in blocks:
        if not _has_batch_confirmation_marker(block) and not re.search(r"\buser_quote\b\s*[:=：]\s*[\"“]?(?:好|继续|按推荐|ok|OK|.*批量确认.*|.*一次性确认.*)", block):
            continue
        if not (OQ_ID_RE.search(block) or re.search(r"covered_(?:oq|decision|refs)", block, re.I)):
            problems.append(
                "Batch confirmation missing covered OQ/decision id on a confirmed decision; "
                "vague batch acknowledgement must fall back to one `next_question`"
            )
    return problems


def fail(gate: str, problems: list) -> int:
    sys.stderr.write(f"[guru-gate:{gate}] 未通过，缺口：\n")
    for p in problems:
        sys.stderr.write(f"  - {p}\n")
    sys.stderr.write("修复后重试；语义级判定请走对应 review loop 并用 record-review 留痕。\n")
    return BLOCK


def ok(gate: str, note: str = "") -> int:
    print(f"[guru-gate:{gate}] 通过{(' — ' + note) if note else ''}")
    return PASS


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _brainstorm_section(prd: str) -> str:
    match = re.search(r"(?im)^##\s+Brainstorm Evidence\s*$", prd)
    if not match:
        return ""
    rest = prd[match.end():]
    next_heading = re.search(r"(?m)^##\s+", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _brainstorm_line_value(section: str, aliases: tuple) -> str | None:
    for raw_line in section.splitlines():
        line = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", raw_line).strip()
        lower = line.lower()
        for alias in aliases:
            if lower.startswith(alias):
                return line[len(alias):].lstrip(" \t:-—").strip()
    return None


def _negative_evidence_has_reason(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered.startswith(BRAINSTORM_NEGATIVE_PREFIXES):
        return True
    return bool(re.search(r"(?:--?|—|:|：|because|due to|因为|理由|原因)\s*\S+", value))


def _brainstorm_evidence_problems(prd: str) -> list:
    section = _brainstorm_section(prd)
    if not section.strip():
        return ["Brainstorm Evidence missing: add `## Brainstorm Evidence` to prd.md"]

    problems = []
    for label, aliases in BRAINSTORM_EVIDENCE_LABELS:
        value = _brainstorm_line_value(section, aliases)
        if value is None:
            problems.append(f"Brainstorm Evidence missing: {label}")
            continue
        block = _section_between_labels(section, label)
        has_child_content = bool(re.search(r"(?m)^\s{2,}(?:[-*+]|\d+[.)])\s+\S+", block))
        normalized = value.strip().lower()
        if normalized in BRAINSTORM_PLACEHOLDERS and not has_child_content:
            problems.append(f"Brainstorm Evidence pending: {label}")
        elif not _negative_evidence_has_reason(value):
            problems.append(f"Brainstorm Evidence needs reason: {label}")

    product_value = _brainstorm_line_value(section, ("product decisions confirmed",))
    product_block = _section_between_labels(section, "Product decisions confirmed")
    positive_decision_blocks = _positive_decision_blocks(product_block, product_value)
    policy_block = _question_policy_block(section)
    policy = _question_policy(policy_block) if policy_block else ""
    has_structured_loop = _question_loop_is_structured(section)
    if positive_decision_blocks and not has_structured_loop and not policy:
        problems.append(
            "Brainstorm Evidence confirmed decisions need `Question Loop Log` "
            "or `question_policy: evidence_only|mixed`"
        )
    if policy == "evidence_only":
        if CONFIRMED_STATUS_RE.search(section) or CURRENT_TURN_CONFIRMATION_RE.search(section):
            problems.append(
                "`question_policy: evidence_only` cannot produce `user_confirmed*` "
                "or `current-turn-confirmation`; keep decisions as evidence_ready"
            )
        if re.search(r"\buser_quote\b\s*[:=：]", product_block, re.I):
            problems.append(
                "`question_policy: evidence_only` cannot use original/source quotes "
                "as `user_quote`; use `source_quote` or `confirmed_ref` instead"
            )
    elif policy == "mixed":
        if not re.search(r"证据已回答|evidence[-_ ]answered|evidence answered", policy_block, re.I):
            problems.append("`question_policy: mixed` must list which questions were answered by evidence")
        if not re.search(r"用户已确认|user[-_ ]confirmed|current[-_ ]turn", policy_block, re.I):
            problems.append("`question_policy: mixed` must list which questions were confirmed by the user in this turn")
    elif policy and policy not in {"evidence_only", "mixed"}:
        problems.append("Question Policy question_policy must be `evidence_only` or `mixed`")
    if re.search(r"(?im)^#{3,6}\s+Question Loop Log\s*$", section) and not has_structured_loop:
        problems.append(
            "Question Loop Log must include columns: "
            + ", ".join(sorted(QUESTION_LOOP_REQUIRED_HEADERS))
        )
    evidence_hint_re = (
        re.compile(r"\b(?:source_quote|confirmed_ref)\b\s*[:=：]", re.I)
        if policy == "evidence_only"
        else CONFIRMATION_HINT_RE
    )
    for block in positive_decision_blocks:
        if not evidence_hint_re.search(block):
            expected_hint = (
                "`source_quote` or `confirmed_ref`"
                if policy == "evidence_only"
                else "`user_quote` or `confirmed_ref`"
            )
            problems.append(
                "Brainstorm Evidence Product decisions confirmed needs "
                f"{expected_hint} on the same decision or direct child block"
            )

    oq_block = _section_between_labels(section, "Open product/scope/risk questions")
    oq_count = len(set(m.group(0).upper() for m in OQ_ID_RE.finditer(oq_block)))
    if oq_count >= 2 and not NEXT_ACTION_RE.search(oq_block):
        problems.append(
            "Brainstorm Evidence has multiple OQ entries; declare exactly one "
            "`next_question` / `next_action` and keep the other OQs open"
        )

    for block in _confirmation_blocks(prd):
        if not CONFIRMATION_HINT_RE.search(block):
            problems.append(
                "`confirmation_status=user_confirmed*` needs `user_quote` or "
                "`confirmed_ref` in the same decision item or direct child block"
            )

    if _stale_confirmation_upgrade_detected(prd) and not CURRENT_TURN_CONFIRMATION_RE.search(prd):
        problems.append(
            "`confirmation_status=evidence_ready` cannot be silently upgraded to "
            "`user_confirmed*`; record `current-turn-confirmation` for the specific decision"
        )

    problems.extend(_batch_confirmation_problems(prd))
    return problems


def _brainstorm_status_mark(task_dir: str) -> str:
    problems = _brainstorm_evidence_problems(read(os.path.join(task_dir, "prd.md")))
    if not problems:
        return "✅ present"
    summary = "; ".join(problems[:3])
    if len(problems) > 3:
        summary += f"; +{len(problems) - 3} more"
    return f"⬜ missing: {summary}"


def _design_sections(design: str):
    """切出概要章与详细章正文（按行首 §2/详细设计标题锚定）。

    分割点必须是行首标题（^#{1,6}）：§2 要求行首（不命中正文里的 `详见 §2` 行内交叉引用），
    「详细设计」用负向前瞻排除「详细设计承接索引」子节标题——否则结构合规的 light design.md
    会被误切（承接索引/三问理由漏进详细段），导致 overview/auto 假拦截。
    """
    m = re.search(r"(?m)^#{1,6}\s*(?:§\s*2(?![0-9])|详细设计(?!承接))", design)
    if m:
        return design[: m.start()], design[m.start():]
    return design, ""


def _task_json_of(task_dir: str) -> dict:
    """读路径宽容解析：非法/非对象根一律回 {}（写路径 cmd_confirm 另有严格守卫）。"""
    try:
        data = json.loads(read(os.path.join(task_dir, "task.json")) or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def task_chain(task_dir: str) -> str:
    """判轨：task.json guru_chain（full|light）优先；缺省时按 design_package 存在性推断。

    guru_after_create 钩子在创建时默认写入 full；light 必须显式声明（经
    client-small-iteration-dev 分流并获用户同意）。两者皆缺按 light 走单文件
    检查（兼容存量任务），但 full 链缺 design_package 会被 Gate 显式拦截。
    """
    data = _task_json_of(task_dir)
    chain = data.get("guru_chain")
    if chain in ("full", "light"):
        return chain
    return "full" if data.get("design_package") else "light"


def _package_dir(task_dir: str, repo_root: str = None):
    """full 链设计包路径（task.json design_package，相对 repo root）。

    拒绝 `..` 穿越与绝对路径（防止 gate 误读仓库外文件给出误导结论）；
    测试夹具可设 GURU_GATE_ALLOW_ABS=1 放行绝对路径。未声明/非法返回 None。

    repo_root（解 cwd≠repo-root 注入 bug，对齐 _requirement_package_dir）：design_package 是
    「相对 repo root」字段。gate 命令 cwd==repo_root，故 **repo_root=None 时按 cwd 解析、返相对**
    （历史行为逐字节不变，8 个 gate 调用方零影响）；`guru_supervise --root` 可在 cwd≠root 下运行，
    必须显式传 repo_root，否则 design 包会按进程 cwd 解析成空包/错包。**传 repo_root 时围栏与返回都
    锚定它、返回绝对路径**，使后续 join/读取与 cwd 无关（digest 只哈希 key+内容，不哈希该路径串）。
    """
    pkg = _task_json_of(task_dir).get("design_package")
    if not isinstance(pkg, str) or not pkg.strip():
        return None
    norm = os.path.normpath(pkg.strip())
    if os.environ.get("GURU_GATE_ALLOW_ABS") == "1":  # 测试夹具逃生口
        return norm
    if os.path.isabs(norm):
        return None
    if norm == ".." or norm.startswith("..%s" % os.sep) or norm.startswith("../"):
        return None
    # realpath 围栏：词法合法但经符号链接逃逸出仓库的路径同样拒绝
    root = os.path.realpath(repo_root) if repo_root else os.path.realpath(os.getcwd())
    real = os.path.realpath(os.path.join(root, norm)) if repo_root else os.path.realpath(norm)
    try:
        if os.path.commonpath([root, real]) != root:
            return None
    except ValueError:
        return None
    return os.path.join(root, norm) if repo_root else norm


def _requirement_package_dir(task_dir: str, repo_root: str = None):
    """正式需求包版本目录（task.json requirement_package，相对 repo root）。

    指向版本化需求包的版本目录（如 docs/requirements/versions/v1.0.0），是 Guru-owned
    顶层字段（类比 design_package）。围栏逻辑与 _package_dir 一致：拒绝 `..` 穿越与
    绝对路径，realpath commonpath 围栏挡符号链接逃逸；测试夹具可设 GURU_GATE_ALLOW_ABS=1
    放行绝对路径。未声明/非法返回 None（= 现状：requirements digest 只含 prd.md）。

    repo_root（解 codex blocker）：requirement_package 是「相对 repo root」字段。gate 自身命令
    cwd 即 repo root，故默认 repo_root=os.getcwd()。但 guru_supervise --root <repo> 可在 cwd≠root
    下运行——它必须显式传 config.root，否则按 cwd 解析会把 docs/... 当成 <cwd>/docs/...（空包/错包），
    与 gate 从 repo root 算的 digest 分叉、review 立刻 stale。返回**绝对**路径（join repo_root），
    使后续枚举/读取与 cwd 无关，supervise 与 gate 字节同口径。**仅校验指针合法性，不校验目录存在**
    （存在性 / canonical_root 围栏是 fail-closed 关注点，见 _requirement_package_problem）。
    """
    pkg = _task_json_of(task_dir).get("requirement_package")
    if not isinstance(pkg, str) or not pkg.strip():
        return None
    base = os.path.realpath(repo_root) if repo_root else os.path.realpath(os.getcwd())
    norm = os.path.normpath(pkg.strip())
    if os.environ.get("GURU_GATE_ALLOW_ABS") == "1":  # 测试夹具逃生口
        return norm if os.path.isabs(norm) else os.path.normpath(os.path.join(base, norm))
    if os.path.isabs(norm):
        return None
    if norm == ".." or norm.startswith("..%s" % os.sep) or norm.startswith("../"):
        return None
    real = os.path.realpath(os.path.join(base, norm))
    try:
        if os.path.commonpath([base, real]) != base:
            return None
    except ValueError:
        return None
    return os.path.normpath(os.path.join(base, norm))


class RequirementManifestError(ValueError):
    """manifest.yaml 存在但解析失败/字段类型非法（fail-closed，不静默 fallback）。"""


_MANIFEST_DEFAULT_ROOT = "."
_MANIFEST_DEFAULT_EXCLUDES = ("snapshots", "changes")


def _parse_inline_list(value: str):
    """解析 `[a, b, c]` 内联列表（stdlib，无 yaml 依赖）。返回字符串列表或抛错。"""
    inner = value.strip()[1:-1].strip()
    if not inner:
        return []
    items = []
    for raw in inner.split(","):
        token = raw.strip()
        if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
            token = token[1:-1]
        if not token:
            raise RequirementManifestError("canonical_excludes 含空条目")
        items.append(token)
    return items


def _consume_block_list(raw_lines, start: int, strict_dash: bool = True):
    """从 start 起消费缩进块列表 `- item` 行，返回 (items, next_index)。

    strict_dash=True（canonical_excludes）：缩进非 `- ` 行抛错（fail-closed）。
    strict_dash=False（非目标键）：只为吞掉缩进子项使顶层解析继续，不校验内容、不存储。
    遇非缩进行 / EOF 停止。
    """
    items = []
    i = start
    while i < len(raw_lines):
        sub = raw_lines[i]
        if not sub.strip() or sub.strip().startswith("#"):
            i += 1
            continue
        if sub[:1] not in (" ", "\t"):
            break
        item_m = re.match(r"^\s*-\s*(.*)$", sub)
        if not item_m:
            if strict_dash:
                raise RequirementManifestError(
                    "canonical_excludes 块列表行必须以 `- ` 开头"
                )
            i += 1
            continue
        if strict_dash:
            token = item_m.group(1).strip()
            if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
                token = token[1:-1]
            if not token:
                raise RequirementManifestError("canonical_excludes 含空条目")
            items.append(token)
        i += 1
    return items, i


def _requirement_manifest(pkg: str):
    """读取版本目录 manifest.yaml 的 canonical_root / canonical_excludes（fail-closed）。

    缺失 → 返回默认 (".", ["snapshots", "changes"])。
    存在但解析失败 / 字段类型非法 → 抛 RequirementManifestError（由 requirements Gate 阻断）。
    仅支持 §15.2 需要的两键：canonical_root（标量）与 canonical_excludes（内联或块列表）。
    无 Python yaml 依赖（仓库无 import yaml）。
    """
    manifest_path = os.path.join(pkg, "manifest.yaml")
    if not os.path.isfile(manifest_path):
        return _MANIFEST_DEFAULT_ROOT, list(_MANIFEST_DEFAULT_EXCLUDES)
    try:
        with open(manifest_path, encoding="utf-8") as f:
            raw_lines = f.read().splitlines()
    except OSError as exc:
        raise RequirementManifestError(f"manifest.yaml 无法读取：{exc}")

    canonical_root = None
    excludes = None
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        stripped = line.strip()
        i += 1
        if not stripped or stripped.startswith("#"):
            continue
        # fail-closed（解 codex major #4）：顶层缩进行只能是块列表子项，应在键的内层循环被消费；
        # 走到这里说明是孤立缩进行（无属主键 / 块列表已结束后的残留），按非法语法阻断。
        if line[:1] in (" ", "\t"):
            raise RequirementManifestError(
                f"manifest.yaml 含无属主的缩进行（疑似列表项缺失上级键）：{stripped}"
            )
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if not m:
            # fail-closed：顶层非空非注释行无法按 `key: value` 解析（无冒号 / `=` / typo bareword）→
            # 不再静默 fallback，否则配置错误会被默默吞掉走默认 canonical_root/excludes。
            raise RequirementManifestError(
                f"manifest.yaml 顶层行无法按 `key: value` 解析（不支持的语法）：{stripped}"
            )
        key, value = m.group(1), m.group(2)
        # 去行尾注释（仅处理 ` #`，不破坏值内 `#`）
        for marker in (" #", "\t#"):
            idx = value.find(marker)
            if idx >= 0:
                value = value[:idx].rstrip()
        value = value.strip()
        if key == "canonical_root":
            if value == "" or value.startswith("[") or value.startswith("{") or value.startswith("-"):
                raise RequirementManifestError("canonical_root 必须是非空标量字符串")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            canonical_root = value
        elif key == "canonical_excludes":
            if value.startswith("["):
                if not value.endswith("]"):
                    raise RequirementManifestError("canonical_excludes 内联列表未闭合")
                excludes = _parse_inline_list(value)
            elif value == "":
                excludes = _consume_block_list(raw_lines, i)
                # _consume_block_list 不推进 i 自身——返回 (items, next_i)
                excludes, i = excludes
            else:
                raise RequirementManifestError(
                    "canonical_excludes 必须是内联列表 [..] 或块列表"
                )
        elif value == "":
            # 非目标键的块列表（如 supersedes:\n  - v0.9.0）：消费其缩进子项使顶层解析不被孤立缩进行
            # 误判为非法（但不存储，§15.2 只取 canonical_root/canonical_excludes 两键）。
            _items, i = _consume_block_list(raw_lines, i, strict_dash=False)
    if canonical_root is None:
        canonical_root = _MANIFEST_DEFAULT_ROOT
    if excludes is None:
        excludes = list(_MANIFEST_DEFAULT_EXCLUDES)
    if not isinstance(canonical_root, str) or not canonical_root.strip():
        raise RequirementManifestError("canonical_root 必须是非空字符串")
    if not all(isinstance(x, str) and x.strip() for x in excludes):
        raise RequirementManifestError("canonical_excludes 必须是非空字符串列表")
    return canonical_root.strip(), excludes


def _canonical_root_dir(pkg: str) -> str:
    """解析并围栏 canonical_root（相对 pkg），返回绝对路径或抛 RequirementManifestError。

    canonical_root 默认 '.'（= pkg）。fail-closed（解 codex major #2）：
    - 拒绝绝对路径与 `..` 穿越（防 `canonical_root: ../../..` 把包外目录纳入 digest）；
    - realpath commonpath 围栏，确保 canonical root 落在 pkg 内（挡符号链接逃逸）；
    - canonical root 目录不存在 → 抛错（不空枚举：空 hash 会伪装成「有包但只 prd.md」）。
    """
    canonical_rel, _excludes = _requirement_manifest(pkg)
    rel_norm = os.path.normpath(canonical_rel)
    if os.path.isabs(rel_norm) or rel_norm == ".." \
            or rel_norm.startswith("..%s" % os.sep) or rel_norm.startswith("../"):
        raise RequirementManifestError(
            f"canonical_root 不得为绝对路径或穿越包外：{canonical_rel}"
        )
    canonical_root = os.path.normpath(os.path.join(pkg, rel_norm))
    pkg_real = os.path.realpath(pkg)
    root_real = os.path.realpath(canonical_root)
    try:
        if os.path.commonpath([pkg_real, root_real]) != pkg_real:
            raise RequirementManifestError(
                f"canonical_root 经 realpath 逃逸出版本目录：{canonical_rel}"
            )
    except ValueError:
        raise RequirementManifestError(f"canonical_root 非法：{canonical_rel}")
    if not os.path.isdir(canonical_root):
        raise RequirementManifestError(
            f"canonical_root 目录不存在：{canonical_root}（fail-closed，不空枚举）"
        )
    return canonical_root


def _requirement_package_files(pkg: str):
    """枚举版本目录 canonical 文件（os.walk + sort + excludes 剪枝），返回 (relpath, abspath)。

    relpath 相对版本目录根（pkg），用于 namespaced key。excludes 相对 canonical_root，
    按顶层子目录/文件名剪枝（默认 snapshots/changes）。dirs.sort()/files.sort() 保证
    同一文件集合不因枚举顺序产生不同 digest。manifest 非法 / canonical_root 越界或缺失
    时向上抛 RequirementManifestError（fail-closed）。
    """
    _canonical_rel, excludes = _requirement_manifest(pkg)
    canonical_root = _canonical_root_dir(pkg)
    exclude_set = set(excludes)
    out = []
    for dirpath, dirnames, filenames in os.walk(canonical_root):
        rel_from_canonical = os.path.relpath(dirpath, canonical_root)
        # 顶层 canonical 子目录按 excludes 剪枝（snapshots/changes 整树不进 digest）
        if rel_from_canonical == ".":
            dirnames[:] = [d for d in dirnames if d not in exclude_set]
        dirnames.sort()
        filenames.sort()
        for name in filenames:
            abspath = os.path.join(dirpath, name)
            rel_from_canonical_file = os.path.relpath(abspath, canonical_root)
            top = rel_from_canonical_file.split(os.sep, 1)[0]
            if top in exclude_set:
                continue
            relpath = os.path.relpath(abspath, pkg)
            out.append((relpath.replace(os.sep, "/"), abspath))
    return out


def _chapter_files(pkg: str) -> list:
    chap_dir = os.path.join(pkg, "chapters")
    if not os.path.isdir(chap_dir):
        return []
    return sorted(n for n in os.listdir(chap_dir) if n.endswith(".md"))


def _artifact_sources(task_dir: str) -> dict:
    """按链型解析四类产物正文。full：overview=design-main.md，detail=chapters/*.md 拼接。"""
    prd = read(os.path.join(task_dir, "prd.md"))
    imp = read(os.path.join(task_dir, "implement.md"))
    if task_chain(task_dir) == "full":
        pkg = _package_dir(task_dir)
        overview = read(os.path.join(pkg, "design-main.md")) if pkg else ""
        detail = ""
        if pkg:
            parts = [read(os.path.join(pkg, "chapters", n)) for n in _chapter_files(pkg)]
            detail = "\n\n".join(p for p in parts if p)
        return {"prd": prd, "overview": overview, "detail": detail, "imp": imp}
    design = read(os.path.join(task_dir, "design.md"))
    overview, detail = _design_sections(design)
    return {"prd": prd, "overview": overview, "detail": detail, "imp": imp}


def _has_detail_heading(text: str, pattern: str) -> bool:
    return bool(re.search(rf"(?m)^#{{1,6}}\s*(?:\d+(?:\.\d+)?[.)、]?\s*)?(?:{pattern})", text))


def detail_chapter_blocks(task_dir: str) -> list:
    """返回当前 detail gate 作用域内的章节块。full 逐文件；light 按 §2 整体检查。"""
    if task_chain(task_dir) == "full":
        pkg = _package_dir(task_dir)
        if not pkg:
            return []
        blocks = []
        for name in _chapter_files(pkg):
            text = read(os.path.join(pkg, "chapters", name))
            if text:
                blocks.append((f"chapters/{name}", text))
        return blocks
    design = read(os.path.join(task_dir, "design.md"))
    _overview, detail = _design_sections(design)
    return [("design.md §2 详细设计", detail)] if detail else []


def analyze_detail_chapter_skeleton(name: str, text: str) -> list:
    problems = []
    if not text.strip():
        return [f"{name} 为空"]
    if not UNIT_DEF.search(text):
        problems.append(f"{name} 缺设计单元编号：单元须以 `### UNIT-<slug>` 标题定义")
    if not BHV_REF.search(text):
        problems.append(f"{name} 缺 BHV-NNN 承接引用")
    for label, pattern in DETAIL_SECTION_PATTERNS:
        if not _has_detail_heading(text, pattern):
            problems.append(f"{name} 缺 L1 章节：{label}")
    for label, pattern in DETAIL_CONTRACT_PATTERNS:
        if not re.search(pattern, text):
            problems.append(f"{name} 缺合同标记：{label}")
    return problems


# =========================================================================
# 追溯模型
# =========================================================================

def build_trace(task_dir: str) -> dict:
    """扫描产物构建追溯模型。返回:
    behaviors: {bhv: 短名}; units: {unit: {"behaviors":[...], "tests": bool, "owner_hint": str}};
    owners: {bhv: owner 行文本}; slices: {unit: [切片行]}; orphans: {...断链清单}
    """
    src = _artifact_sources(task_dir)
    prd, overview, detail, imp = src["prd"], src["overview"], src["detail"], src["imp"]

    behaviors = {}
    req_ucs = {}  # {bhv: [REQ-UC-XXX, ...]}：BHV 标题 [..] 承接的需求场景（多对多）
    for m in BHV_DEF.finditer(prd):
        line = m.group(0)
        bhv = m.group(1)
        # BHV 标题形如 `### BHV-001 [REQ-UC-005, REQ-UC-007] <描述>`：先抽 [..] 内的 REQ-UC
        bracket = re.search(r"\[([^\]]*REQ-UC[^\]]*)\]", line)
        req_ucs[bhv] = REQ_UC_REF.findall(bracket.group(1)) if bracket else []
        # 短名：去掉 `#### BHV-001 ` 前缀，再去掉紧随的 `[REQ-UC..]` 承接段
        name = re.sub(r"^#{2,5}\s+BHV-\d+\s*", "", line)
        name = re.sub(r"^\[[^\]]*REQ-UC[^\]]*\]\s*", "", name).strip()
        behaviors[bhv] = name or "(未命名)"

    # §1 归属：含 BHV 引用的行视为归属行
    owners = {}
    for line in overview.splitlines():
        for b in BHV_REF.findall(line):
            owners.setdefault(b, line.strip()[:120])

    # §2 设计单元：按 UNIT 标题切块
    units = {}
    defs = list(UNIT_DEF.finditer(detail))
    for i, m in enumerate(defs):
        body = detail[m.end(): defs[i + 1].start() if i + 1 < len(defs) else len(detail)]
        units[m.group(1)] = {
            "behaviors": sorted(set(BHV_REF.findall(body))),
            "tests": bool(re.search(r"测试映射|哪些测试", body)),
        }

    # 实现切片：implement.md 中含 UNIT 引用的行
    slices = {}
    for line in imp.splitlines():
        for u in UNIT_REF.findall(line):
            slices.setdefault(u, []).append(line.strip()[:120])

    covered = {b for u in units.values() for b in u["behaviors"]}
    orphans = {
        "bhv_no_unit": sorted(set(behaviors) - covered),                      # 行为无单元承接
        "unit_ghost_bhv": sorted({b for u in units.values() for b in u["behaviors"]} - set(behaviors)),  # 幽灵引用
        "unit_no_test": sorted(u for u, d in units.items() if not d["tests"]),
        "unit_no_slice": sorted(set(units) - set(slices)) if imp else [],
        "slice_ghost_unit": sorted(set(slices) - set(units)),
    }
    return {"behaviors": behaviors, "req_ucs": req_ucs, "owners": owners, "units": units, "slices": slices, "orphans": orphans}


def render_matrix(t: dict) -> str:
    lines = ["# 追溯矩阵（机器生成，勿手编）", "",
             "| 行为 | 名称 | 需求场景（REQ-UC） | 归属（§1） | 承接单元（§2） | 测试映射 | 实现切片 |",
             "|------|------|------|-----------|---------------|---------|---------|"]
    unit_by_bhv = {}
    for u, d in t["units"].items():
        for b in d["behaviors"]:
            unit_by_bhv.setdefault(b, []).append(u)
    for b, name in sorted(t["behaviors"].items()):
        us = unit_by_bhv.get(b, [])
        tests = "✅" if us and all(t["units"][u]["tests"] for u in us) else ("⚠️" if us else "—")
        sl = "✅" if us and all(u in t["slices"] for u in us) else ("⚠️" if us else "—")
        owner = '✅' if b in t['owners'] else '❌'
        unit_cell = ', '.join(us) or '❌ 无承接'
        # 多对多行展开：一 BHV 多 REQ-UC → 每 REQ-UC 一行；无承接 → 一行 REQ-UC 空（旧 prd 不断链）
        ucs = t.get("req_ucs", {}).get(b, [])
        if ucs:
            for uc in ucs:
                lines.append(f"| {b} | {name} | {uc} | {owner} | {unit_cell} | {tests} | {sl} |")
        else:
            lines.append(f"| {b} | {name} | — | {owner} | {unit_cell} | {tests} | {sl} |")
    o = t["orphans"]
    lines += ["", "## 孤儿/断链清单"]
    label = [("bhv_no_unit", "行为无设计单元承接"), ("unit_ghost_bhv", "单元引用了不存在的行为（幽灵 BHV）"),
             ("unit_no_test", "单元缺测试映射"), ("unit_no_slice", "单元无实现切片引用"),
             ("slice_ghost_unit", "切片引用了不存在的单元")]
    any_o = False
    for k, lab in label:
        if o[k]:
            any_o = True
            lines.append(f"- **{lab}**：{', '.join(o[k])}")
    if not any_o:
        lines.append("- 无（承接链闭合）")
    return "\n".join(lines) + "\n"


def cmd_trace_matrix(task_dir: str, write: bool, strict: bool, require_req_uc: bool = False) -> int:
    t = build_trace(task_dir)
    if not t["behaviors"] and not t["units"]:
        print("[guru-gate:trace-matrix] 未发现 BHV/UNIT 编号（产物尚未按编号纪律撰写）")
        return BLOCK if strict else PASS
    out = render_matrix(t)
    print(out)
    if write:
        p = os.path.join(task_dir, "trace-matrix.md")
        open(p, "w", encoding="utf-8").write(out)
        print(f"[guru-gate:trace-matrix] 已写入 {p}")
    broken = t["orphans"]["bhv_no_unit"] or t["orphans"]["unit_ghost_bhv"] or t["orphans"]["slice_ghost_unit"]
    if strict and broken:
        return fail("trace-matrix", ["存在断链（见上方孤儿清单）"])
    # --require-req-uc（finding 3，不复用 --strict 的断链判定）：强制态下 BHV 缺 REQ-UC 承接即 BLOCK。
    # 触发合同见 main() 的 trace-matrix 分支：① CLI --require-req-uc 显式强制（即使旧 task）；
    # ② task.json require_req_uc==true；③ 无则旧 task 默认 false。
    if require_req_uc:
        missing = sorted(b for b in t["behaviors"] if not t.get("req_ucs", {}).get(b))
        if missing:
            return fail("trace-matrix", [
                "--require-req-uc：以下 BHV 缺 [REQ-UC-XXX] 需求场景承接（标题须形如 "
                f"`### BHV-001 [REQ-UC-005] <描述>`）：{', '.join(missing)}"
            ])
    return PASS


# =========================================================================
# 版本级追溯聚合（trace-aggregate）：跨 task 反查 → 单表回填 → fail-closed
# =========================================================================

# 版本级 traceability 生成区标记（HTML 注释，对 --aggregate 幂等；包裹整个生成表）。
_TRACE_GEN_START = "<!-- trace-matrix:generated:start -->"
_TRACE_GEN_END = "<!-- trace-matrix:generated:end -->"
# §15.4 单表表头（REQ-UC | Source Task | Design Unit | BHV | Code Entry | Test Evidence | Status）
_TRACE_AGG_HEADER = (
    "| REQ-UC | Source Task | Design Unit | BHV | Code Entry | Test Evidence | Status |"
)
_TRACE_AGG_SEP = "|--------|-------------|-------------|-----|-----------|---------------|--------|"
# 回填 key = (REQ-UC, UNIT)；这三列由人维护，aggregate 不覆盖、只按 key 搬运。
_TRACE_MANUAL_COLS = ("code_entry", "test_evidence", "status")


def _aggregate_rows_for_task(task_dir: str, source_task: str) -> list:
    """单 task 的行展开：(REQ-UC, BHV, UNIT, Source Task)。

    复用 build_trace：req_ucs={bhv:[REQ-UC...]}、units[u]["behaviors"]=该单元承接的 BHV。
    一个 BHV 可对多 REQ-UC（行展开），可被多 UNIT 承接（每 UNIT 一行）；
    BHV 无 REQ-UC → REQ-UC 列空（"—"）；BHV 无 UNIT 承接 → UNIT 列空（"—"，标 orphan 由状态列体现）。
    """
    t = build_trace(task_dir)
    unit_by_bhv = {}
    for u, d in t["units"].items():
        for b in d["behaviors"]:
            unit_by_bhv.setdefault(b, []).append(u)
    rows = []
    for bhv in sorted(t["behaviors"]):
        ucs = t.get("req_ucs", {}).get(bhv) or [""]  # "" = 无 REQ-UC 承接
        units = sorted(unit_by_bhv.get(bhv, [])) or [""]  # "" = 无 UNIT 承接
        for uc in ucs:
            for unit in units:
                rows.append({
                    "req_uc": uc,
                    "source_task": source_task,
                    "unit": unit,
                    "bhv": bhv,
                })
    return rows


def _split_md_row(line: str):
    """拆 markdown 表行 `| a | b | ... |` → [a, b, ...]（去首尾空 cell 与两端空白）。"""
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _parse_existing_manual(text: str) -> dict:
    """从既有 traceability.md 生成区解析人维护列，返回 {(REQ-UC, UNIT): {code_entry,test_evidence,status}}。

    只读生成区内、表头之后的数据行；按列名定位 Code Entry/Test Evidence/Status（容忍列序微调）。
    key 用 (REQ-UC, UNIT)：UNIT 改名/删除时该 key 不再出现 → 调用方标 orphan/stale 保留旧证据。
    解析失败/无生成区/无表 → 返回 {}（首次 aggregate 无可回填）。
    """
    if not text:
        return {}
    start = text.find(_TRACE_GEN_START)
    end = text.find(_TRACE_GEN_END)
    if start < 0 or end < 0 or end < start:
        return {}
    block = text[start + len(_TRACE_GEN_START): end]
    lines = [ln for ln in block.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return {}
    header = [h.lower() for h in _split_md_row(lines[0])]

    def col_idx(*names):
        for n in names:
            if n in header:
                return header.index(n)
        return None
    i_uc = col_idx("req-uc", "req_uc")
    i_unit = col_idx("design unit", "design_unit", "unit")
    i_code = col_idx("code entry", "code_entry")
    i_test = col_idx("test evidence", "test_evidence")
    i_status = col_idx("status")
    if i_uc is None or i_unit is None:
        return {}

    # 解析必须是 _render_aggregate_table 的逆：render 把空值 cell 渲染成占位符 "—"，故读回时
    # 须把 "—" 归一回空串。否则 (a) 空 REQ-UC 行的 parsed key 变 ("—", unit) 与 live key ("", unit)
    # 失配，活跃单元被误判 orphan；(b) 空 code/test 读成 "—"（truthy）使 orphan 空证据过滤失效，
    # 给当前单元造出假「已移除」孤儿行（破坏幂等 + 误导审计）。
    def uncell(v):
        return "" if v == "—" else v

    manual = {}
    for ln in lines[2:]:  # 跳表头 + 分隔行
        cells = _split_md_row(ln)
        if len(cells) <= max(i for i in (i_uc, i_unit, i_code, i_test, i_status) if i is not None):
            continue
        uc = uncell(cells[i_uc])
        unit = uncell(cells[i_unit])
        manual[(uc, unit)] = {
            "code_entry": uncell(cells[i_code]) if i_code is not None else "",
            "test_evidence": uncell(cells[i_test]) if i_test is not None else "",
            "status": uncell(cells[i_status]) if i_status is not None else "",
        }
    return manual


def _render_aggregate_table(rows: list, existing_manual: dict) -> str:
    """渲染版本级 traceability 单表（生成区内容，不含标记本身）。

    人维护三列按 (REQ-UC, UNIT) key 从 existing_manual 回填；不再出现的旧 key 末尾追加为 orphan 行
    （UNIT 列原值 + status 标 `stale (UNIT 已移除)`），保证手维护证据不丢。幂等：相同 rows + 相同
    existing_manual 二次渲染逐字节一致（rows 排序确定 + orphan 按 key 排序）。
    """
    # 规格化空值占位
    def cell(v):
        return v if v else "—"
    live_keys = set()
    body = []
    # rows 已由 _aggregate_rows_for_task 内部 sorted，跨 task 合并后再统一排序确保确定性
    for r in sorted(rows, key=lambda x: (x["req_uc"], x["source_task"], x["unit"], x["bhv"])):
        key = (r["req_uc"], r["unit"])
        live_keys.add(key)
        m = existing_manual.get(key, {})
        code = m.get("code_entry", "")
        test = m.get("test_evidence", "")
        status = m.get("status", "") or "missing"  # 派生行默认 missing（待人补证据）
        body.append(
            f"| {cell(r['req_uc'])} | {cell(r['source_task'])} | {cell(r['unit'])} | "
            f"{cell(r['bhv'])} | {cell(code)} | {cell(test)} | {status} |"
        )
    # 不再出现的旧 (REQ-UC, UNIT)：保留人维护证据，标 orphan/stale（不丢）
    orphan_keys = sorted(set(existing_manual) - live_keys)
    for uc, unit in orphan_keys:
        m = existing_manual[(uc, unit)]
        # 仅保留确曾有人维护证据的 orphan（全空的派生残留无须保留）
        if not (m.get("code_entry") or m.get("test_evidence")
                or (m.get("status") and m["status"] not in ("missing", "—", ""))):
            continue
        prev = m.get("status", "")
        marker = "orphan" if "orphan" not in prev.lower() else prev
        status = f"{marker} (BHV/UNIT 已移除，保留旧证据)" if "已移除" not in prev else prev
        body.append(
            f"| {cell(uc)} | — | {cell(unit)} | — | "
            f"{cell(m.get('code_entry', ''))} | {cell(m.get('test_evidence', ''))} | {status} |"
        )
    return "\n".join([_TRACE_AGG_HEADER, _TRACE_AGG_SEP, *body])


def _write_traceability(version_dir: str, table: str) -> str:
    """把生成表写入 <version_dir>/traceability.md 的生成区（其余手写正文保留）。

    既有文件有生成区标记 → 只替换标记之间内容（保留区外手写导语/说明）。
    无标记 / 文件不存在 → 创建/追加：文件首部保留既有手写内容，末尾插入带标记的生成区。
    返回写入路径。
    """
    path = os.path.join(version_dir, "traceability.md")
    block = f"{_TRACE_GEN_START}\n{table}\n{_TRACE_GEN_END}\n"
    old = read(path)
    if old and _TRACE_GEN_START in old and _TRACE_GEN_END in old:
        s = old.find(_TRACE_GEN_START)
        e = old.find(_TRACE_GEN_END) + len(_TRACE_GEN_END)
        # 保留生成区尾随换行风格：替换 [start, end] 区段
        new = old[:s] + block.rstrip("\n") + old[e:]
        # 确保文件以单换行结尾
        if not new.endswith("\n"):
            new += "\n"
    elif old:
        sep = "" if old.endswith("\n") else "\n"
        new = old + sep + "\n" + block
    else:
        header = (
            "# Traceability（版本级审计参考，single-source §15.4）\n\n"
            "> `REQ-UC | Source Task | UNIT | BHV` 派生列由 `guru_gate.py trace-aggregate` 生成；\n"
            "> `Code Entry | Test Evidence | Status` 人维护（aggregate 按 (REQ-UC, UNIT) key 回填保留）。\n\n"
        )
        new = header + block
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return path


def _excludes_has_traceability(version_dir: str) -> bool:
    """目标 version_dir 的 effective canonical_excludes 是否含顶层 `traceability`。

    复用 _requirement_manifest（manifest 缺失/字段缺失回退 _MANIFEST_DEFAULT_EXCLUDES=
    (snapshots, changes)，**不含 traceability**）。manifest 解析失败抛 RequirementManifestError
    由调用方转 fail-closed 拒写。
    """
    _root, excludes = _requirement_manifest(version_dir)
    return "traceability" in excludes


def _collect_aggregate_candidates(repo_root: str, include_completed: bool):
    """枚举候选 task.json 路径。返回 [(task_dir, source_task, is_archived), ...]。

    默认仅 `.trellis/tasks/<task>/task.json`（排除 archive/）；include_completed 加扫
    `.trellis/tasks/archive/<YYYY-MM>/<task>/task.json`（归档是月份分层，非一层 glob）。
    source_task = task 目录名（archive 项保留月份前缀消歧，如 `archive/2026-06/<task>`）。
    """
    import glob
    candidates = []
    tasks_root = os.path.join(repo_root, ".trellis", "tasks")
    for tjp in sorted(glob.glob(os.path.join(tasks_root, "*", "task.json"))):
        task_dir = os.path.dirname(tjp)
        name = os.path.basename(task_dir)
        if name == "archive":  # archive 是目录，*/task.json 不会命中它，但稳妥起见跳过
            continue
        candidates.append((task_dir, name, False))
    if include_completed:
        for tjp in sorted(glob.glob(os.path.join(tasks_root, "archive", "*", "*", "task.json"))):
            task_dir = os.path.dirname(tjp)
            month = os.path.basename(os.path.dirname(task_dir))
            name = os.path.basename(task_dir)
            candidates.append((task_dir, f"archive/{month}/{name}", True))
    return candidates


def cmd_trace_aggregate(version_dir: str, include_completed: bool, repo_root: str = None) -> int:
    """版本级聚合：反查指向 version_dir 的 task → 行展开 → 单表回填写 traceability.md。

    finding 5/8（反查 + 独立子命令）+ 决策 1（fail-closed，不触发 digest）。
    流程：① fail-closed 前置（effective excludes 须含 traceability，否则拒写）；
    ② 反查候选 task.json（默认非 archive；--include-completed 加扫月份归档树）；
    ③ realpath 比对 _requirement_package_dir == version_dir；④ build_trace 行展开聚合；
    ⑤ 解析既有手维护列回填 → 写生成区。
    """
    base = os.path.realpath(repo_root) if repo_root else os.path.realpath(os.getcwd())
    version_real = os.path.realpath(version_dir)
    if not os.path.isdir(version_dir):
        sys.stderr.write(f"[guru-gate:trace-aggregate] version 目录不存在：{version_dir}\n")
        return BLOCK

    # ① fail-closed 前置（决策 1，codex blocker）：写 traceability 前必须确认它在 canonical_excludes，
    # 否则写入会进 requirements digest → review stale。_MANIFEST_DEFAULT_EXCLUDES 不含 traceability，
    # 故 manifest 缺失/未配置时此处拒写（不静默触发 digest，不改代码默认）。
    try:
        if not _excludes_has_traceability(version_dir):
            sys.stderr.write(
                "[guru-gate:trace-aggregate] 拒写（fail-closed）：traceability.md 不在 "
                "canonical_excludes，写它会进 requirements digest 并使 review stale。\n"
                f"  请先在 {os.path.join(version_dir, 'manifest.yaml')} 的 canonical_excludes "
                "加 `traceability`（如 `canonical_excludes: [snapshots, changes, traceability]`），再重跑。\n"
            )
            return BLOCK
    except RequirementManifestError as exc:
        sys.stderr.write(
            f"[guru-gate:trace-aggregate] manifest.yaml 非法（{os.path.join(version_dir, 'manifest.yaml')}）：{exc}\n"
        )
        return BLOCK

    # ② + ③ 反查：候选 task.json，realpath 比对 requirement_package == version_dir
    matched = []  # [(task_dir, source_task)]
    skipped = {
        "no_requirement_package": [],  # 无 requirement_package 字段
        "other_version": [],           # 指向别的版本目录
        "illegal_pointer": [],         # 指针非法（候选匹配范围内才记，见下）
        "archived_not_included": [],   # 归档但未 --include-completed（仅在默认扫到提示时用）
        "history_schema": [],          # 历史 schema 缺字段（task.json 解析为空/无 requirement_package 视为此类的子集）
    }
    for task_dir, source_task, _is_archived in _collect_aggregate_candidates(base, include_completed):
        data = _task_json_of(task_dir)
        if not data:
            skipped["history_schema"].append(source_task)
            continue
        field = data.get("requirement_package")
        if not isinstance(field, str) or not field.strip():
            skipped["no_requirement_package"].append(source_task)
            continue
        pkg = _requirement_package_dir(task_dir, base)
        if pkg is None:
            # 指针非法：只在它本可能指向本 version 时才算 fail 相关，否则记 skipped（design §2.3：
            # 非法指针只在候选匹配该 version 时 fail，其余 skipped）。这里无法 realpath 比对（已 None），
            # 统一记 illegal_pointer skipped，不中断聚合。
            skipped["illegal_pointer"].append(f"{source_task}（{field.strip()}）")
            continue
        if os.path.realpath(pkg) == version_real:
            matched.append((task_dir, source_task))
        else:
            skipped["other_version"].append(source_task)

    # 默认模式下提示「归档里还有匹配本版本的 task，--include-completed 可纳入」（design §2.3 分类）：
    # 只 realpath 比对计数，不读产物、不入表，避免误以为聚合已覆盖归档历史。
    if not include_completed:
        for task_dir, source_task, _is_archived in _collect_aggregate_candidates(base, True):
            if not _is_archived:
                continue
            data = _task_json_of(task_dir)
            field = data.get("requirement_package") if data else None
            if not isinstance(field, str) or not field.strip():
                continue
            pkg = _requirement_package_dir(task_dir, base)
            if pkg is not None and os.path.realpath(pkg) == version_real:
                skipped["archived_not_included"].append(source_task)

    # ④ 行展开聚合
    all_rows = []
    for task_dir, source_task in matched:
        all_rows.extend(_aggregate_rows_for_task(task_dir, source_task))

    # ⑤ 回填 + 写生成区
    path = os.path.join(version_dir, "traceability.md")
    existing_manual = _parse_existing_manual(read(path))
    table = _render_aggregate_table(all_rows, existing_manual)
    written = _write_traceability(version_dir, table)

    print(f"[guru-gate:trace-aggregate] 已写入 {written}")
    print(f"  匹配 task：{len(matched)}（{', '.join(s for _, s in matched) or '无'}）")
    print(f"  行展开：{len(all_rows)} 行")
    print("  跳过分类：")
    for k, label in (
        ("no_requirement_package", "无 requirement_package 字段"),
        ("other_version", "指向别版本"),
        ("illegal_pointer", "指针非法"),
        ("archived_not_included", "归档未 --include-completed"),
        ("history_schema", "历史 schema 缺字段"),
    ):
        items = skipped[k]
        if items:
            print(f"    - {label}：{len(items)}（{', '.join(items)}）")
    return PASS


# =========================================================================
# 五阶段 Gate
# =========================================================================

def _requirement_package_problem(task_dir: str, repo_root: str = None) -> str:
    """requirement_package fail-closed 检查。返回缺口描述（空=合法或无包）。

    fail-closed 边界（解 codex blocker + major #2）：
    - 无 requirement_package 字段 → 返回空（= 现状，digest 只含 prd.md）。
    - 字段存在但指针非法（绝对路径 / `..` 穿越 / realpath 逃逸出 repo root）→ 阻断（不静默忽略）。
    - 指向的版本目录不存在 → 阻断（不空枚举伪装成「有包但只 prd.md」）。
    - manifest 解析失败 / 字段类型非法 / canonical_root 越界或缺失 → 阻断 + 修复提示。
    repo_root：requirement_package 相对 repo root；gate 命令 cwd==root（默认 None→cwd），
    supervise 显式传 config.root，使两脚本同口径（不因 cwd 分叉给出空包/错包）。
    """
    field = _task_json_of(task_dir).get("requirement_package")
    if not isinstance(field, str) or not field.strip():
        return ""
    req_pkg = _requirement_package_dir(task_dir, repo_root)
    if req_pkg is None:
        return (
            f"requirement_package 指针非法：{field.strip()}"
            "（必须是 repo root 相对路径，不得为绝对路径或 `..` 穿越 / 符号链接逃逸出仓库）"
        )
    if not os.path.isdir(req_pkg):
        return (
            f"requirement_package 版本目录不存在：{req_pkg}"
            "（fail-closed：有指针就必须纳入正式需求包；修正路径或移除字段回退 prd.md-only）"
        )
    try:
        _requirement_manifest(req_pkg)
        _canonical_root_dir(req_pkg)  # 触发 canonical_root 围栏/存在性 fail-closed
    except RequirementManifestError as exc:
        return (
            f"requirement_package manifest 非法（{os.path.join(req_pkg, 'manifest.yaml')}）：{exc}"
            "（修正 canonical_root/canonical_excludes 字段，或删除 manifest.yaml 回退默认 "
            f"canonical_root='.'、excludes={list(_MANIFEST_DEFAULT_EXCLUDES)}）"
        )
    return ""


def _task_requires_brainstorm_evidence(task_dir: str) -> bool:
    route = _contract_route_for_review_policy(task_dir)
    if route != guru_contract.ROUTE_LITE_TASK:
        return True
    contract, error = guru_contract.load_contract(task_dir)
    if error or not isinstance(contract, dict):
        return True
    execution_policy = contract.get("execution_policy")
    required = (
        execution_policy.get("brainstorm_required")
        if isinstance(execution_policy, dict)
        else None
    )
    return required if isinstance(required, bool) else True


def check_requirements(task_dir: str) -> int:
    """需求 Gate：行为规格(BHV 编号标题) / P0 P1 / 失败路径 / 验收 / 未决问题。"""
    prd = read(os.path.join(task_dir, "prd.md"))
    problems = []
    if not prd:
        return fail("requirements", ["prd.md 不存在或为空"])
    manifest_problem = _requirement_package_problem(task_dir)
    if manifest_problem:
        # manifest fail-closed：先于 digest 取材阻断，避免非法 manifest 导致 digest 计算抛错
        return fail("requirements", [manifest_problem])
    if not BHV_DEF.search(prd):
        problems.append("缺行为编号：行为须以 `### BHV-NNN <短名>` 标题定义（编号纪律）")
    if not (re.search(r"\bGiven\b", prd) and re.search(r"\bWhen\b", prd) and re.search(r"\bThen\b", prd)):
        problems.append("缺行为规格：未找到 Given/When/Then 三段式（至少一组）")
    # 不用 \bP0\b：Python \b 把 CJK 当 word 字符，"优先级P0" 会失配（同文件头部反 \b 纪律）。
    # 守卫用显式 ASCII-word 类（含数字/下划线）两侧对称：放过 CJK 紧贴，挡掉 step_P0/3P0/P0Beta 假阳性。
    if not re.search(r"(?<![A-Za-z0-9_])P[01](?![A-Za-z0-9_])", prd):
        problems.append("缺核心能力清单：未找到 P0/P1 优先级标记")
    if not re.search(r"失败路径|失败场景|异常路径|failure", prd, re.I):
        problems.append("缺失败路径章节")
    if not re.search(r"验收|acceptance", prd, re.I):
        problems.append("缺验收场景/标准章节")
    if not re.search(r"未决|open question|待确认", prd, re.I):
        problems.append("缺未决问题章节（无未决也须显式声明）")
    if _task_requires_brainstorm_evidence(task_dir):
        brainstorm_problems = _brainstorm_evidence_problems(prd)
        if brainstorm_problems:
            problems.extend(brainstorm_problems)
            problems.append(f"恢复步骤：{BRAINSTORM_RECOVERY}")
    return fail("requirements", problems) if problems else ok("requirements")


def _check_package_skeleton(task_dir: str) -> list:
    """full 链设计包结构检查。返回缺口清单（空=通过）。"""
    pkg = _package_dir(task_dir)
    if not pkg:
        return ["full 链必须在 task.json 声明 design_package（目录级设计包路径，如 docs/design/<feature>）"]
    problems = []
    if not os.path.isdir(pkg):
        return [f"design_package 目录不存在：{pkg}"]
    if not read(os.path.join(pkg, "README.md")):
        problems.append(f"缺 {pkg}/README.md（导航与追踪矩阵入口）")
    if not read(os.path.join(pkg, "design-main.md")):
        problems.append(f"缺 {pkg}/design-main.md（概要主定义）")
    if not os.path.isdir(os.path.join(pkg, "chapters")):
        problems.append(f"缺 {pkg}/chapters/ 目录（详细设计逐章承载区）")
    return problems


def _check_chapter_closure(task_dir: str) -> list:
    """承接索引 ↔ chapters/ 文件闭合：索引引用的文件必须存在；chapters/ 不得有未被索引的孤儿。"""
    pkg = _package_dir(task_dir)
    if not pkg:
        return []
    main = read(os.path.join(pkg, "design-main.md"))
    referenced = set(CHAPTER_FILE_REF.findall(main))
    existing = set(_chapter_files(pkg))
    problems = []
    missing = sorted(referenced - existing)
    orphan = sorted(existing - referenced)
    if missing:
        problems.append(f"承接索引引用的章节文件不存在：{', '.join(missing)}")
    if orphan:
        problems.append(f"chapters/ 存在未被承接索引引用的孤儿文件：{', '.join(orphan)}")
    return problems


def _doc_type_taxonomy():
    """运行时从已装 SSOT 解析 doc_type 分类，返回 (all_types, v1_types)。

    定位 .trellis/spec/harness/detail/detail-structure-single-source.md（相对 cwd=项目根，与
    _package_dir 同约定）的 doc_type 表：表格行最后一列为 L2 状态（pending / 含 v1）时，取行内第一个
    反引号 token 为 doc_type；含 v1 → 已建成 L2（不需豁免）。这样 go/ios/h5 的 domain/route/
    coordinator… 也能被 pending-L2 Gate 正确拦截，而非只认 flutter 硬编码类目。SSOT 缺失/解析空 →
    fallback flutter 基线。结果按 cwd 缓存（同一进程多次调用不重复解析）。
    """
    key = os.path.realpath(os.getcwd())
    if key in _TAXONOMY_CACHE:
        return _TAXONOMY_CACHE[key]
    text = read(os.path.join(".trellis", "spec", "harness", "detail",
                             "detail-structure-single-source.md"))
    allt, v1 = set(), set()
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2 or not re.search(r"pending|v1", cells[-1]):
            continue
        m = re.search(r"`([a-z][a-z0-9-]*)`", s)   # 行内第一个反引号 token = doc_type（兼容 doc_type 在第 1/2 列）
        if not m:
            continue
        allt.add(m.group(1))
        if "v1" in cells[-1]:
            v1.add(m.group(1))
    result = (allt, v1) if allt else (set(_FALLBACK_NINE), set(_FALLBACK_V1))
    _TAXONOMY_CACHE[key] = result
    return result


def _index_doc_types(main: str) -> set:
    """提取承接索引引用的 doc_type：兼容 `doc_type=X` 行内形式与表格行形式
    （表格行无 doc_type= 前缀，按当前平台 doc_type token 出现在索引上下文行识别）。"""
    nine, _ = _doc_type_taxonomy()
    hits = {t for t in DOC_TYPE_REF.findall(main) if t in nine}
    for line in main.splitlines():
        if "L2豁免" in line:
            continue
        if "chapters/" in line or "chapter_target" in line:
            for t in nine:
                if re.search(rf"\b{re.escape(t)}\b", line):
                    hits.add(t)
    return hits


def _check_pending_l2(task_dir: str) -> list:
    """pending L2 拦截：承接索引命中非 v1 doc_type 时必须在 design-main 显式 `L2豁免：<doc_type> 理由：…`。"""
    pkg = _package_dir(task_dir)
    if not pkg:
        return []
    nine, v1 = _doc_type_taxonomy()
    main = read(os.path.join(pkg, "design-main.md"))
    hit = {t for t in _index_doc_types(main) if t not in v1}
    exempted = set()
    for line in L2_EXEMPT_LINE.findall(main):
        # 豁免对象只从「理由」之前的声明段取词（且限当前平台 doc_type token）——
        # 理由文本里出现的类型词（如 "this service layer..."）不构成豁免
        head = line.split("理由", 1)[0]
        exempted.update(t for t in re.findall(r"[a-z][a-z0-9-]*", head) if t in nine)
    not_exempted = sorted(t for t in hit if t not in exempted)
    if not_exempted:
        return [f"承接索引命中 pending L2 类型且无显式豁免：{', '.join(not_exempted)}"
                "（在 design-main.md 写 `L2豁免：<doc_type> 理由：…`，或等对应 L2 建成）"]
    return []


def check_overview(task_dir: str) -> int:
    """概要 Gate：归属表（引用 BHV 编号）+ 三问理由 + 承接索引。full 链另查设计包结构与章节闭合。"""
    full = task_chain(task_dir) == "full"
    problems = []
    if full:
        problems += _check_package_skeleton(task_dir)
        if problems:
            return fail("overview", problems)
    src = _artifact_sources(task_dir)
    overview = src["overview"]
    if not overview:
        return fail("overview", ["design-main.md 为空（概要主定义未开始）" if full
                                 else "design.md 不存在或为空（概要设计未开始）"])
    if not full and not re.search(r"概要设计|§\s*1", overview):
        problems.append("缺概要设计章（§1）标题")
    if not re.search(r"owner|归属", overview):
        problems.append("缺行为→owner 归属表")
    if not BHV_REF.search(overview):
        problems.append("归属表未引用 BHV 编号（追溯断点：归属必须按行为编号逐条）")
    if not re.search(r"为什么属于|归属理由|三问", overview):
        problems.append("归属表缺三问理由（为什么属于它/不属于别人/是否需独立存在）")
    if not re.search(r"承接索引|doc_type", overview):
        problems.append("缺详细设计承接索引（chapter_target → doc_type）")
    if full:
        if not re.search(r"架构就绪|就绪自检", overview):
            problems.append("缺架构就绪自检节（G1~G8 自评，见 overview L1 §6）")
        if not CHAPTER_FILE_REF.search(overview):
            problems.append("承接索引未引用 chapters/<file>.md 章节文件（包模式索引必须落到文件；文件本体在详细阶段产出）")
        if "```mermaid" not in overview:
            problems.append("缺架构图/页面流图（design-main 须含 mermaid 图，见 overview L1 §2.5）")
        if "sequenceDiagram" not in overview and "时序图策略" not in overview:
            problems.append("缺时序图或时序图策略表（见 overview L1 §2.5 ⑥）")
    return fail("overview", problems) if problems else ok("overview")


def _decision_inventory_problem(task_dir: str) -> str:
    contract, contract_error = guru_contract.load_contract(task_dir)
    if contract_error:
        return f"RISK_DECISION_INVENTORY_POLICY_INVALID: {contract_error}"
    policy_problem = guru_contract.decision_inventory_policy_problem(contract)
    if policy_problem:
        return policy_problem
    if not guru_contract.decision_inventory_required(contract):
        return ""
    task_data = _task_json_of(task_dir)
    task_id = str(task_data.get("id") or task_data.get("name") or os.path.basename(os.path.normpath(task_dir)))
    try:
        artifacts = collect_gate_artifacts(task_dir, "detail", _config_root_for_task(task_dir))
        guru_contract.load_detail_decision_inventory(task_dir, task_id, artifacts)
    except (OSError, ValueError, guru_contract.ContractError) as exc:
        return str(exc)
    return ""


def check_detail(task_dir: str) -> int:
    """详细 Gate：UNIT 编号 + 合同八问标记 + implement.md + 承接断链拦截。
    full 链按 chapters/*.md 逐章承载（章节闭合 + pending L2 豁免拦截）。"""
    full = task_chain(task_dir) == "full"
    problems = []
    if full:
        problems += _check_package_skeleton(task_dir)
        if problems:
            return fail("detail", problems)
        problems += _check_chapter_closure(task_dir)
        problems += _check_pending_l2(task_dir)
    src = _artifact_sources(task_dir)
    if not full and not read(os.path.join(task_dir, "design.md")):
        return fail("detail", ["design.md 不存在"])
    detail = src["detail"]
    if not detail:
        problems.append("chapters/ 无任何章节正文（详细设计未开始）" if full else "缺详细设计章（§2）")
    else:
        for name, text in detail_chapter_blocks(task_dir):
            problems += analyze_detail_chapter_skeleton(name, text)
    if not read(os.path.join(task_dir, "implement.md")):
        problems.append("implement.md（trace §1 实现计划）不存在")
    inventory_problem = _decision_inventory_problem(task_dir)
    if inventory_problem:
        problems.append(inventory_problem)
    # 承接断链拦截（编号闭合）
    t = build_trace(task_dir)
    if t["behaviors"] or t["units"]:
        if t["orphans"]["unit_ghost_bhv"]:
            problems.append(f"单元引用幽灵行为（prd 无此编号）：{', '.join(t['orphans']['unit_ghost_bhv'])}")
        if t["orphans"]["bhv_no_unit"]:
            problems.append(f"行为无设计单元承接：{', '.join(t['orphans']['bhv_no_unit'])}（补单元或在 prd 显式降范围）")
    return fail("detail", problems) if problems else ok("detail")


def check_implement(task_dir: str) -> int:
    """实现 Gate：trace 四节齐全 + 切片挂 UNIT（项目级 analyze/test 由 worktree.yaml 其余 verify 条目执行）。"""
    imp = read(os.path.join(task_dir, "implement.md"))
    problems = []
    if not imp:
        return fail("implement", ["implement.md 不存在"])
    for label, pat in [
        ("计划节", r"计划|切片"),
        ("执行节", r"执行|改动文件"),
        ("证据节", r"证据|analyze|test"),
        ("阻塞与偏差节", r"阻塞|偏差"),
    ]:
        if not re.search(pat, imp, re.I):
            problems.append(f"trace 缺{label}")
    t = build_trace(task_dir)
    if t["units"]:
        if not UNIT_REF.search(imp):
            problems.append("实现切片未引用任何 UNIT 编号（切片必须挂设计单元）")
        if t["orphans"]["slice_ghost_unit"]:
            problems.append(f"切片引用幽灵单元：{', '.join(t['orphans']['slice_ghost_unit'])}")
    return fail("implement", problems) if problems else ok("implement")


def resolve_task_dir(arg, *, allow_unique_planning_fallback=True):
    # before_start 注入 TASK_JSON_PATH（指向正要 start 的任务）：与显式 arg 不一致时警告，
    # 避免 check 校验了 A（已确认）却给 B（正要 start、未确认）放行（F4 跨任务错配）。
    tj = os.environ.get("TASK_JSON_PATH", "")
    tj_dir = os.path.dirname(tj) if tj and os.path.isfile(tj) else None
    if arg:
        if os.path.isdir(arg):
            resolved = arg
        else:
            named = os.path.join(".trellis", "tasks", arg)  # 裸任务名
            resolved = named if os.path.isdir(named) else None
        if resolved and tj_dir and os.path.realpath(resolved) != os.path.realpath(tj_dir):
            sys.stderr.write(
                f"[guru-gate] 警告：显式 task_dir（{resolved}）与 before_start 注入的 "
                f"TASK_JSON_PATH（{tj_dir}）指向不同任务，按显式参数校验——若此调用是 "
                f"task.py start 的前置闸门，请核实校验的是否为正在激活的任务。\n")
        return resolved
    # before_start 钩子注入 TASK_JSON_PATH（最可靠：指向正要 start 的任务）
    if tj_dir:
        return tj_dir
    import subprocess
    try:
        out = subprocess.run(["python3", ".trellis/scripts/task.py", "current"],
                             capture_output=True, text=True, timeout=15).stdout.strip()
        m = re.search(r"(\.trellis/tasks/\S+)", out)
        if m and os.path.isdir(m.group(1)):
            return m.group(1)
    except Exception:
        pass
    if not allow_unique_planning_fallback:
        return None
    # 用户终端跑 confirm 时通常无会话指针：唯一 planning 任务可安全兜底
    tasks_root = os.path.join(".trellis", "tasks")
    planning = []
    if os.path.isdir(tasks_root):
        for name in sorted(os.listdir(tasks_root)):
            d = os.path.join(tasks_root, name)
            tjp = os.path.join(d, "task.json")
            if not os.path.isfile(tjp):
                continue
            try:
                data = json.loads(read(tjp) or "{}")
                if isinstance(data, dict) and data.get("status") == "planning":
                    planning.append(d)
            except json.JSONDecodeError:
                continue
    if len(planning) == 1:
        return planning[0]
    if len(planning) > 1:
        sys.stderr.write("[guru-gate] 多个 planning 任务，请显式传 task_dir：\n"
                         + "".join(f"  - {d}\n" for d in planning))
    return None


# =========================================================================
# Guru Gate（confirm / record-review / status / check）
# =========================================================================
# 设计：新流程只保留两个人工确认点：requirements 与 detail。overview/detail
# 的设计评审由 review worker 写入 task.json.guru_gates.review_runs；同一产物
# digest 下两个不同 run-id 的 clean 记录才允许自动通过。旧 design-grill 记录
# 继续可读写，但只作为兼容审计信息，不再作为 gate 放行条件。
#
# 安全边界（诚实声明，勿误用）：本机制是「诚实性辅助（integrity aid）」，不是
# 「安全边界（security boundary）」。它挡得住「无意/图省事跳过评审」（手滑），
# 挡不住「蓄意绕过」的 agent——判定材料 task.json 与 agent 同处可写信任域，
# artifact_digest 是无密钥哈希且 `digest` 子命令无门禁，故蓄意者可：(a) 自取
# digest 伪造一份自洽的 guru_gates；(b) 分配 pty 使 isatty() 误判为人；(c) 自行
# 把 gate_mode 降 soft 代跑。strict 模式只抬高绕过成本、提供流程纪律，不构成
# 密码学保证。要升级成真正的安全边界，须把确认信任根移出 agent 可写域（独立
# 进程/服务签发确认），属架构级改动，不在本脚本范围。

ALL_GATES = ("requirements", "overview", "detail")
HUMAN_GATES = ("requirements", "detail")
REVIEW_GATES = ("overview", "detail")
GATE_LABEL = {"requirements": "需求", "overview": "概要设计", "detail": "详细设计"}
GATES_KEY = "guru_gates"
REVIEW_RUNS_KEY = "review_runs"
ADVERSARIAL_SKIPS_KEY = "adversarial_skips"
REQUIREMENTS_REVIEW_KEY = "requirements_review"
REQUIRED_CLEAN_REVIEWS = 2
SEVERITY_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
FINDING_CLASSES = {
    "REQ_BLOCKER",
    "OVERVIEW_DEFECT",
    "DETAIL_DEFECT",
    "IMPLEMENT_DEFECT",
    "PROCESS_DEFECT",
}
from guru_risk import HIGH_RISK_LEVELS, LOW_RISK_LEVELS  # noqa: F401  单一来源（guru_risk）


def _namespaced_key(path: str, source: str, relpath: str, namespace: bool) -> str:
    """digest key 生成。

    namespace OFF（无 requirement_package 的任务）：纯 basename——与历史 digest 逐字节一致
    （向后兼容是最高优先级；_gate_digest 旧实现按 basename 入哈希）。
    namespace ON（有 requirement_package 的任务）：`<source>:<relpath>`——消除正式需求包与
    design_package 的 README.md 同名碰撞（task: / design: / requirements:）。
    """
    if not namespace:
        return os.path.basename(path)
    return f"{source}:{relpath}"


def _gate_artifacts(task_dir: str, gate: str, repo_root: str = None) -> list:
    """各阶段确认快照所覆盖的产物，返回结构化条目 [{path, source, key}]。

    快照是**累积的**：下游阶段包含上游产物——上游（如 prd）改动后即使只重确认上游，
    下游确认也会失配并要求重新确认（下游评审基于的上游语义已变）。

    结构化条目把来源边界（task/design/requirements）在枚举处一次定死，digest 不再反推；
    requirement_package realpath 围栏、canonical_root 解析、canonical_excludes 过滤、
    namespaced key 都集中在此。namespace 仅在该任务声明 requirement_package 时启用，
    无指针任务保持纯 basename（digest 与改动前一致）。manifest 非法时向上抛
    RequirementManifestError（由 requirements Gate fail-closed 阻断）。

    repo_root（解 codex blocker）：透传给 _requirement_package_dir，使正式需求包按 repo root
    （而非进程 cwd）解析；gate 命令默认 None→cwd，supervise 显式传 config.root。
    """
    full = task_chain(task_dir) == "full"
    pkg = _package_dir(task_dir, repo_root)
    req_pkg = _requirement_package_dir(task_dir, repo_root)
    namespace = req_pkg is not None
    entries = []

    def add(path, source, relpath):
        entries.append({
            "path": path,
            "source": source,
            "key": _namespaced_key(path, source, relpath, namespace),
        })

    # requirements：prd.md（task）+ 正式需求包 canonical 文件（requirements）
    add(os.path.join(task_dir, "prd.md"), "task", "prd.md")
    if req_pkg is not None:
        for relpath, abspath in _requirement_package_files(req_pkg):
            add(abspath, "requirements", relpath)
    if gate == "requirements":
        return entries

    # overview：累积 + 概要主定义（design）或 design.md（light）
    if full and pkg:
        # README 属包骨架（导航/追踪矩阵入口），同样纳入确认快照
        add(os.path.join(pkg, "README.md"), "design", "README.md")
        add(os.path.join(pkg, "design-main.md"), "design", "design-main.md")
    else:
        add(os.path.join(task_dir, "design.md"), "task", "design.md")
    if gate == "overview":
        return entries

    # detail：全链累积 + chapters（design）+ implement.md（task）
    if full and pkg:
        for n in _chapter_files(pkg):
            add(os.path.join(pkg, "chapters", n), "design", f"chapters/{n}")
    # light 链 design.md 已在 overview 段加入
    add(os.path.join(task_dir, "implement.md"), "task", "implement.md")
    return entries


class GateArtifactError(Exception):
    """gate-local fail-closed 错误：供 guru_supervise 注入 review SSOT 时，正式包声明却非法/缺失
    或 manifest 非法时抛出。定义在 guru_gate.py、由 supervise 捕获并包装为 GuruSupervisionError——
    guru_gate **不得**反向 import guru_supervise 的异常（防循环 import；supervise 已 module-load
    import guru_gate）。"""


def collect_gate_artifacts(task_dir: str, gate: str, repo_root: str = None) -> list:
    """guru_supervise 注入 review SSOT 的安全枚举器：复用 _gate_artifacts 的 repo-root 围栏 /
    canonical_excludes / namespacing / digest 取材边界，但对**声明却非法/缺失的正式包 fail-closed**
    （抛 GateArtifactError），不像 _gate_artifacts 那样静默回落 task-local docs。

    - requirement_package 声明却有问题（复用 _requirement_package_problem，repo_root-aware）→ 抛。
    - full 链且 design_package 声明却非法（_package_dir 返 None）或目录不存在 → 抛。
    - manifest 非法（_gate_artifacts 抛 RequirementManifestError）→ 包装为 GateArtifactError。
    light 链 / 未声明正式包 → 正常返回（含 task-local 回落，属设计内）。
    """
    prob = _requirement_package_problem(task_dir, repo_root)
    if prob:
        raise GateArtifactError(f"requirement_package fail-closed：{prob}")
    design = _task_json_of(task_dir).get("design_package")
    if task_chain(task_dir) == "full":
        # full 链声明即隐含须有正式 design 包：合法流程到 implement/check 时（collect 的唯一调用点）
        # 必已过 overview/detail gate（二者都拦 full+无 design_package），故缺失即错误态——
        # supervise 注入 SSOT 时 fail-closed，不静默回落 task-local design.md（不像 _gate_artifacts
        # 那样为 gate auto 渐进保留历史兼容）。
        if not (isinstance(design, str) and design.strip()):
            raise GateArtifactError(
                "full 链缺 design_package：正式设计包是 review SSOT 行级基线，"
                "不得回落 task-local design.md（声明 full 即须提供正式包）"
            )
        pkg = _package_dir(task_dir, repo_root)
        if pkg is None:
            raise GateArtifactError(
                f"design_package 指针非法：{design.strip()}"
                "（必须是 repo root 相对路径，不得绝对 / `..` 穿越 / 符号链接逃逸）"
            )
        if not os.path.isdir(pkg):
            raise GateArtifactError(f"design_package 目录不存在：{pkg}")
        # 包骨架核心 SSOT 文件 fail-closed：目录存在但缺 README/design-main(/detail 阶段缺 chapters)
        # 时，_gate_artifacts 仍会把这些路径列入 entries，但 supervise 的 _existing_paths 会**静默
        # 过滤**掉不存在的，导致正式 design 基线被悄悄少注入（违反「正式包是行级权威基线」）。故在此硬检。
        for skeleton in ("README.md", "design-main.md"):
            if not os.path.isfile(os.path.join(pkg, skeleton)):
                raise GateArtifactError(f"design_package 缺核心骨架文件：{skeleton}（{pkg}）")
        if gate == "detail" and not os.path.isdir(os.path.join(pkg, "chapters")):
            raise GateArtifactError(f"design_package 缺 chapters/ 目录（detail 阶段需逐章设计；{pkg}）")
    try:
        return _gate_artifacts(task_dir, gate, repo_root)
    except RequirementManifestError as exc:
        raise GateArtifactError(f"requirement manifest 非法：{exc}") from exc


def _gate_digest(task_dir: str, gate: str, repo_root: str = None) -> str:
    """确认快照摘要：排序后串接 key+内容做 sha256。

    入哈希的是 key 不是完整路径——confirm（用户终端相对路径）与 check（before_start 注入
    绝对路径）的调用形态不同，完整路径会导致假失配。

    排序口径（解 codex major #3，向后兼容是最高优先级）：
    - namespace OFF（无 requirement_package）：key==basename，**只按 basename 排序**。Python
      sorted 是稳定排序，相同 basename 时保留 _gate_artifacts 的原始 entry 顺序——与历史实现
      （`key=os.path.basename`）逐字节一致。含重复 basename 的 full 设计包（design-main.md +
      chapters/design-main.md、implement.md + chapters/implement.md）串接顺序不变，旧确认/
      review_runs 不失配。
    - namespace ON（有 requirement_package）：key 已是 `<source>:<relpath>` 全局唯一，按
      (key, realpath) 全量稳定排序；os.walk 已 dirs.sort()/files.sort()，同一文件集合不因
      枚举顺序产生不同 digest。
    """
    import hashlib
    h = hashlib.sha256()
    namespace = _requirement_package_dir(task_dir, repo_root) is not None
    artifacts = _gate_artifacts(task_dir, gate, repo_root)
    if namespace:
        entries = sorted(artifacts, key=lambda e: (e["key"], os.path.realpath(e["path"])))
    else:
        # 复刻历史排序：仅按 basename（==key），稳定排序保留原始 entry 顺序（向后兼容字节级）
        entries = sorted(artifacts, key=lambda e: e["key"])
    for entry in entries:
        h.update(entry["key"].encode("utf-8"))
        h.update(b"\0")
        h.update(read(entry["path"]).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def requirements_digest(task_dir: str, repo_root: str = None) -> str:
    """requirements digest 共享单一来源（供 guru_supervise.py import 调用）。

    与 _gate_digest(task_dir, "requirements") 完全同口径——消除 guru_supervise 历史上
    独立 _requirements_digest 实现导致的两处分叉。无 requirement_package 时只含 prd.md。

    repo_root（解 codex blocker）：requirement_package 相对 repo root。guru_supervise --root
    <repo> 可在 cwd≠root 下运行，必须传 config.root，否则按 cwd 解析正式需求包会与 gate 分叉、
    supervise 写入的 review digest 永久 stale。gate 自身命令 cwd==root，默认 None。
    """
    return _gate_digest(task_dir, "requirements", repo_root)


def requirements_confirmation_digest(task_dir: str, repo_root: str = None) -> str:
    """Bind Lite confirmation to the current PRD, route, risk, and semantic scope."""
    artifact_digest = requirements_digest(task_dir, repo_root)
    contract, error = guru_contract.load_contract(task_dir)
    if error or not isinstance(contract, dict):
        return artifact_digest
    route = guru_contract.contract_route(contract)
    if route != guru_contract.ROUTE_LITE_TASK:
        return artifact_digest
    execution_policy = contract.get("execution_policy")
    scope_fingerprint = (
        execution_policy.get("scope_fingerprint")
        if isinstance(execution_policy, dict)
        else None
    )
    payload = {
        "requirements_digest": artifact_digest,
        "route": route,
        "risk": guru_contract.contract_risk(contract),
        "scope_fingerprint": scope_fingerprint,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _risk_level(task_dir: str) -> str:
    """读取任务风险等级。缺失/不可判定按 unknown 处理，避免 light 链自动获得 skip 权限。

    实现委托 `guru_risk.task_risk_level`（单一来源；guru_supervise 也用同一 helper，防两份风险逻辑漂移）。
    """
    return guru_risk.task_risk_level(task_dir)


def _grill_policy(task_dir: str, gate: str) -> dict:
    """Return legacy design-grill audit policy for compatibility commands only."""
    chain = task_chain(task_dir)
    risk = _risk_level(task_dir)
    if gate == "requirements":
        return {
            "policy": "required",
            "guru_chain": chain,
            "risk_level": risk,
            "reason": "legacy compatibility：requirements 的旧 design-grill 记录不允许 skip",
        }
    if chain == "full":
        return {
            "policy": "required",
            "guru_chain": chain,
            "risk_level": risk,
            "reason": "legacy compatibility：guru_chain=full 的旧概要/详细 grill-skip 审计记录不适用",
        }
    if risk == "high":
        return {
            "policy": "required",
            "guru_chain": chain,
            "risk_level": risk,
            "reason": "legacy compatibility：risk_level=high 的旧概要/详细 grill-skip 审计记录不适用",
        }
    if chain == "light" and risk == "low":
        return {
            "policy": "skippable",
            "guru_chain": chain,
            "risk_level": risk,
            "reason": "legacy compatibility：guru_chain=light 且 risk_level=low，可写入旧 grill-skip 审计记录",
        }
    return {
        "policy": "required",
        "guru_chain": chain,
        "risk_level": risk,
        "reason": "legacy compatibility：risk_level 未显式标为 low，拒绝旧 grill-skip 审计记录",
    }


def _developer_name() -> str:
    for line in read(os.path.join(".trellis", ".developer")).splitlines():
        if line.startswith("name="):
            return line[len("name="):].strip()
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


def _turn_ref() -> str:
    for name in ("CODEX_SESSION_ID", "CODEX_THREAD_ID", "CLAUDE_SESSION_ID", "TRELLIS_CONTEXT_ID"):
        value = os.environ.get(name, "").strip()
        if value:
            return f"{name}={value}"
    return ""


def _parse_config_key_line(line: str):
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or ":" not in line:
        return None
    indent = len(line) - len(line.lstrip(" "))
    key, raw_value = line.strip().split(":", 1)
    key = key.strip()
    if not key:
        return None
    return indent, key, raw_value


def _config_scalar(raw_value: str) -> str:
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


def _config_has_scalar(raw_value: str) -> bool:
    return bool(_config_scalar(raw_value))


def _config_root_for_task(task_dir: str = None) -> str:
    if task_dir:
        real = os.path.realpath(task_dir)
        marker = f"{os.sep}.trellis{os.sep}tasks{os.sep}"
        idx = real.find(marker)
        if idx >= 0:
            return real[:idx]
        candidate = real if os.path.isdir(real) else os.path.dirname(real)
        while candidate and candidate != os.path.dirname(candidate):
            if os.path.isfile(os.path.join(candidate, ".trellis", "config.yaml")):
                return candidate
            candidate = os.path.dirname(candidate)
    try:
        return _repo_root()
    except Exception:
        return os.getcwd()


def _config_value(path: tuple[str, ...], task_dir: str = None) -> str:
    return _config_value_with_presence(path, task_dir)[1]


def _config_value_with_presence(
    path: tuple[str, ...],
    task_dir: str = None,
) -> tuple[bool, str]:
    cfg = read(os.path.join(_config_root_for_task(task_dir), ".trellis", "config.yaml"))
    if not cfg:
        return False, ""
    stack = []
    for line in cfg.splitlines():
        parsed = _parse_config_key_line(line)
        if parsed is None:
            continue
        indent, key, raw_value = parsed
        while stack and indent <= stack[-1][0]:
            stack.pop()
        current_path = tuple(k for _, k in stack) + (key,)
        if current_path == path:
            return True, _config_scalar(raw_value)
        if not _config_has_scalar(raw_value):
            stack.append((indent, key))
    return False, ""


def _config_bool(path: tuple[str, ...], default: bool, task_dir: str = None) -> bool:
    value = _config_value(path, task_dir).strip().lower()
    if not value:
        return default
    return value not in {"0", "false", "no", "off"}


def _adversarial_enabled(task_dir: str = None) -> bool:
    return _config_bool(("guru", "supervision", "adversarial_enabled"), True, task_dir)


def _contract_route_for_review_policy(task_dir: str = None) -> str:
    if not task_dir:
        return ""
    contract, error = guru_contract.load_contract(task_dir)
    if error or not isinstance(contract, dict):
        return ""
    route = guru_contract.contract_route(contract)
    if not route:
        return ""
    risk_problem = guru_contract.raw_risk_problem(contract.get("risk"))
    if risk_problem:
        return ""
    risk = guru_contract.contract_risk(contract)
    if risk == guru_contract.RISK_UNKNOWN:
        return ""
    validation_problems = guru_contract.validate_contract(contract)
    if route == guru_contract.ROUTE_SMALL_INLINE:
        validation_problems = [
            problem for problem in validation_problems
            if problem != "small_inline cannot be used as a commit contract; use micro_task when committing"
        ]
    if validation_problems:
        return ""
    return route


def _review_policy(task_dir: str = None) -> dict:
    route = _contract_route_for_review_policy(task_dir)
    adversarial_enabled = _adversarial_enabled(task_dir)
    requirements_required = adversarial_enabled
    review_adversarial_required = adversarial_enabled
    reason = "strict full_chain/default policy"
    if not adversarial_enabled:
        reason = "adversarial disabled by config"
    elif route in {guru_contract.ROUTE_SMALL_INLINE, guru_contract.ROUTE_MICRO_TASK}:
        requirements_required = False
        review_adversarial_required = False
        reason = f"route={route}: adversarial review not required"
    elif route == guru_contract.ROUTE_LITE_TASK:
        requirements_required = False
        review_adversarial_required = False
        reason = "route=lite_task: bounded review policy"
    return {
        "route": route or guru_contract.ROUTE_FULL_CHAIN,
        "requirements_adversarial_required": requirements_required,
        "review_adversarial_required": review_adversarial_required,
        "adversarial_enabled": adversarial_enabled,
        "reason": reason,
    }


def _requirements_adversarial_required(task_dir: str = None) -> bool:
    return bool(_review_policy(task_dir)["requirements_adversarial_required"])


def _review_adversarial_required(task_dir: str = None) -> bool:
    return bool(_review_policy(task_dir)["review_adversarial_required"])


def _gate_mode() -> str:
    """人工 Gate 通道：strict（默认，用户终端 TTY）/ soft（对话确认后 agent --via-agent 代跑）。

    优先级：GURU_GATE_MODE 环境变量 > .trellis/config.yaml 的 `guru.gate_mode` > strict。
    soft 即官方 Trellis 的对话确认模型，另保留累积快照/结构复跑/留痕标注三道兜底。
    """
    mode = os.environ.get("GURU_GATE_MODE", "").strip().lower()
    if mode == "strict":
        return mode  # env 收紧到 strict 总是允许
    if mode == "soft" and os.environ.get("GURU_GATE_ALLOW_ENV_SOFT") == "1":
        return mode  # env 放宽到 soft 仅限测试（需双开关）——生产降级必须改 config（留 git 痕迹可审计）
    config_mode = _config_value(("guru", "gate_mode")).strip().lower()
    if config_mode in {"soft", "strict"}:
        return config_mode
    return "strict"


def _task_data_for_write(task_dir: str, channel: str):
    """写路径严格读取 task.json：非法/非对象根拒绝，避免宽容读冲掉用户元数据。"""
    raw = read(os.path.join(task_dir, "task.json"))
    if raw.strip():
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"[guru-gate:{channel}] task.json 格式非法，拒绝写入：{e}\n")
            return None
        if not isinstance(data, dict):
            sys.stderr.write(f"[guru-gate:{channel}] task.json 根节点必须是对象，拒绝写入\n")
            return None
        return data
    return {}


def _write_task_data_atomic(task_dir: str, data: dict) -> str:
    """原子写 task.json：中断不留半截文件。返回写入路径。"""
    tj_path = os.path.join(task_dir, "task.json")
    tmp_path = f"{tj_path}.tmp.{os.getpid()}"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, tj_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return tj_path


def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _review_runs(task_dir: str, gate: str) -> list:
    gates = _gate_states(task_dir)
    by_gate = gates.get(REVIEW_RUNS_KEY)
    if not isinstance(by_gate, dict):
        return []
    runs = by_gate.get(gate)
    return runs if isinstance(runs, list) else []


def _severity_rank(value) -> int:
    if not isinstance(value, str):
        return -1
    return SEVERITY_ORDER.get(value.strip().lower(), -1)


def _review_run_validation_error(run: dict) -> str:
    result = str(run.get("result", "")).strip().lower()
    severity = str(run.get("max_severity", "")).strip().lower()
    rank = _severity_rank(severity)
    if result not in {"clean", "findings"}:
        return "result 必须是 clean 或 findings"
    if rank < 0:
        return "max_severity 必须是 none|low|medium|high|critical"
    if not str(run.get("run_id", "")).strip():
        return "缺 run_id"
    reviewer = str(run.get("reviewer", "")).strip()
    if not reviewer:
        return "缺 reviewer"
    if "clean-context" not in reviewer.lower():
        return "reviewer 必须包含 clean-context 标记"
    if not str(run.get("evidence", "")).strip():
        return "缺 evidence"
    if result == "clean":
        if rank > SEVERITY_ORDER["low"]:
            return "clean 记录的 max_severity 只能是 none 或 low"
        if str(run.get("finding_class", "")).strip():
            return "clean 记录不得写 finding_class"
    if result == "findings":
        if rank < SEVERITY_ORDER["medium"]:
            return "findings 记录的 max_severity 必须是 medium+"
        finding_class = str(run.get("finding_class", "")).strip().upper().replace("-", "_")
        if finding_class not in FINDING_CLASSES:
            return f"findings 记录必须带 finding_class（可选: {', '.join(sorted(FINDING_CLASSES))}）"
    return ""


def _review_run_is_clean(run: dict) -> bool:
    return (
        _review_run_validation_error(run) == ""
        and str(run.get("result", "")).strip().lower() == "clean"
        and _severity_rank(run.get("max_severity")) <= SEVERITY_ORDER["low"]
        and not str(run.get("finding_class", "")).strip()
    )


def _review_state(task_dir: str, gate: str) -> dict:
    """返回当前 digest 下的 review clean streak 状态。findings/非法记录会打断 streak。"""
    digest = _gate_digest(task_dir, gate)
    policy = _review_policy(task_dir)
    adversarial_required = bool(policy["review_adversarial_required"])
    all_runs = [run for run in _review_runs(task_dir, gate) if isinstance(run, dict)]
    current_runs = [
        run for run in all_runs
        if run.get("artifact_digest") == digest
    ]
    stale_runs = [
        run for run in all_runs
        if run.get("artifact_digest") != digest
    ]
    clean_run_ids = []
    adversarial_clean_run_ids = []
    duplicate_clean_run_ids = []
    latest_blocker = None
    for run in current_runs:
        error = _review_run_validation_error(run)
        if error:
            latest_blocker = {"run_id": run.get("run_id", "?"), "reason": error}
            clean_run_ids = []
            adversarial_clean_run_ids = []
            continue
        if _review_run_is_clean(run):
            run_id = str(run.get("run_id", "")).strip()
            if run_id not in clean_run_ids:
                clean_run_ids.append(run_id)
                reviewer = str(run.get("reviewer", "")).strip().lower()
                if "adversarial" in reviewer:
                    adversarial_clean_run_ids.append(run_id)
            else:
                duplicate_clean_run_ids.append(run_id)
            continue
        latest_blocker = run
        clean_run_ids = []
        adversarial_clean_run_ids = []
    ready = (
        len(clean_run_ids) >= REQUIRED_CLEAN_REVIEWS
        and (not adversarial_required or bool(adversarial_clean_run_ids))
    )
    return {
        "digest": digest,
        "runs": current_runs,
        "stale_run_count": len(stale_runs),
        "latest_stale_digest": stale_runs[-1].get("artifact_digest") if stale_runs else "",
        "clean_run_ids": clean_run_ids,
        "adversarial_clean_run_ids": adversarial_clean_run_ids,
        "adversarial_required": adversarial_required,
        "adversarial_policy_reason": policy["reason"],
        "review_policy_route": policy["route"],
        "has_adversarial_clean": bool(adversarial_clean_run_ids),
        "duplicate_clean_run_ids": duplicate_clean_run_ids,
        "clean_count": len(clean_run_ids),
        "ready": ready,
        "latest_blocker": latest_blocker,
    }


def _review_problem(task_dir: str, gate: str) -> str:
    state = _review_state(task_dir, gate)
    if state["ready"]:
        return ""
    if not state["runs"]:
        if state.get("stale_run_count"):
            return (
                f"review digest 失配：已有 {state['stale_run_count']} 条旧 digest 记录，"
                f"但当前产物 digest 尚无 {GATE_LABEL[gate]} review 记录"
            )
        return f"当前产物 digest 尚无 {GATE_LABEL[gate]} review 记录"
    if (
        state.get("adversarial_required", True)
        and
        state["clean_count"] >= REQUIRED_CLEAN_REVIEWS
        and not state.get("has_adversarial_clean")
    ):
        return (
            f"当前 digest 已有 {state['clean_count']}/{REQUIRED_CLEAN_REVIEWS} 个不同 run-id 的 clean review，"
            "但 clean streak 缺少 reviewer 含 adversarial 的 opposite-provider clean review"
        )
    blocker = state["latest_blocker"]
    if isinstance(blocker, dict):
        reason = blocker.get("reason")
        if reason:
            return f"最近 review 记录非法（run_id={blocker.get('run_id', '?')}）：{reason}"
        return (
            f"最近 review 仍有 medium+ findings"
            f"（run_id={blocker.get('run_id', '?')}，max_severity={blocker.get('max_severity', '?')}，"
            f"finding_class={blocker.get('finding_class', '?')}）"
        )
    duplicates = state.get("duplicate_clean_run_ids") or []
    if duplicates:
        dup_text = ", ".join(sorted(set(str(item) for item in duplicates)))
        return (
            f"重复 clean review run_id 不计入双 clean：{dup_text}；"
            f"当前 digest 只有 {state['clean_count']}/{REQUIRED_CLEAN_REVIEWS} 个不同 run-id 的 clean review"
        )
    return (
        f"当前 digest 只有 {state['clean_count']}/{REQUIRED_CLEAN_REVIEWS} 个不同 run-id 的 clean review"
    )


def _review_route_guidance(task_dir: str, gate: str) -> str:
    blocker = _review_state(task_dir, gate).get("latest_blocker")
    if not isinstance(blocker, dict):
        return ""
    finding_class = str(blocker.get("finding_class", "")).strip().upper()
    if finding_class == "REQ_BLOCKER":
        return (
            "回到需求澄清，更新 prd.md 后重新确认 requirements；"
            "下游 review evidence 会因 digest 变化失效。"
        )
    if gate == "detail" and finding_class == "OVERVIEW_DEFECT":
        return "回到概要设计修复承接/归属问题，再重新执行 detail review。"
    return ""


def _review_status_mark(task_dir: str, gate: str) -> str:
    state = _review_state(task_dir, gate)
    if state["ready"]:
        ids = ", ".join(state["clean_run_ids"][-REQUIRED_CLEAN_REVIEWS:])
        if state.get("adversarial_required", True):
            adv = ", ".join(state["adversarial_clean_run_ids"])
            return f"review ✅ clean x{state['clean_count']} ({ids}; adversarial {adv})"
        return f"review ✅ clean x{state['clean_count']} ({ids}; {state.get('adversarial_policy_reason', 'adversarial not required')})"
    problem = _review_problem(task_dir, gate)
    return f"review ⬜ {state['clean_count']}/{REQUIRED_CLEAN_REVIEWS} clean — {problem}"


def _review_deletion_audit_mark(task_dir: str, gate: str) -> str:
    if gate != "detail":
        return ""
    digest = _gate_digest(task_dir, gate)
    audits = [
        str(run.get("deletion_audit", "")).strip()
        for run in _review_runs(task_dir, gate)
        if (
            isinstance(run, dict)
            and run.get("artifact_digest") == digest
            and str(run.get("result", "")).strip().lower() == "clean"
            and str(run.get("deletion_audit", "")).strip()
        )
    ]
    if not audits:
        return " ｜ deletion-audit ⬜ missing"
    latest = audits[-1]
    if len(latest) > 120:
        latest = latest[:117] + "..."
    return f" ｜ deletion-audit ✅ {latest}"


def _block_review(channel: str, task_dir: str, gate: str) -> int:
    state = _review_state(task_dir, gate)
    route_guidance = _review_route_guidance(task_dir, gate)
    audit_hint = ' --deletion-audit "<none|删除审计摘要>"' if gate == "detail" else ""
    if route_guidance:
        sys.stderr.write(
            f"[guru-gate:{channel}] 拦截：{GATE_LABEL[gate]} review 路由上游："
            f"{_review_problem(task_dir, gate)}\n"
        )
        sys.stderr.write(f"下一步：{route_guidance}\n")
        return BLOCK
    if (
        state.get("adversarial_required", True)
        and
        state["clean_count"] >= REQUIRED_CLEAN_REVIEWS
        and not state.get("has_adversarial_clean")
    ):
        sys.stderr.write(
            f"[guru-gate:{channel}] 拦截：{GATE_LABEL[gate]} Gate 已有双 clean，"
            "但缺少 reviewer 含 adversarial 的 opposite-provider clean review。\n"
        )
        sys.stderr.write("下一步：运行对抗 clean-context review，并记录 adversarial reviewer：\n")
        sys.stderr.write(
            f"  python3 .trellis/scripts/guru/guru_supervise.py --adversarial {gate} {task_dir}\n"
        )
        sys.stderr.write(
            f"  python3 .trellis/scripts/guru/guru_gate.py record-review {gate} {task_dir} "
            "--result clean --max-severity low --reviewer clean-context-adversarial-<provider> "
            f"--run-id <id> --evidence \"<review证据>\"{audit_hint}\n"
        )
        return BLOCK
    sys.stderr.write(
        f"[guru-gate:{channel}] 拦截：{GATE_LABEL[gate]} Gate 缺少当前产物的双 clean review 证据："
        f"{_review_problem(task_dir, gate)}\n"
    )
    adversarial_clause = (
        "，且至少一次来自 opposite-provider adversarial review"
        if state.get("adversarial_required", True)
        else f"（{state.get('adversarial_policy_reason', 'adversarial not required')}）"
    )
    sys.stderr.write(
        f"由 review worker 记录两次不同 run-id 的 clean 证据{adversarial_clause}：\n"
        f"  python3 .trellis/scripts/guru/guru_gate.py record-review {gate} {task_dir} "
        f"--result clean --max-severity low --reviewer clean-context[-adversarial-<provider>] --run-id <id> --evidence \"<review证据>\"{audit_hint}\n"
    )
    return BLOCK


def _record_review(task_dir: str, gate: str, options: dict) -> int:
    if gate not in REVIEW_GATES:
        sys.stderr.write(
            f"[guru-gate:record-review] 只支持 {', '.join(REVIEW_GATES)}；requirements 只走人工确认，不记录 clean streak\n"
        )
        return BLOCK
    # overview/detail digest 累积 requirements 产物（含正式需求包）；manifest 非法时 fail-closed
    manifest_problem = _requirement_package_problem(task_dir)
    if manifest_problem:
        sys.stderr.write(f"[guru-gate:record-review] {manifest_problem}\n")
        return BLOCK
    if gate == "detail":
        inventory_problem = _decision_inventory_problem(task_dir)
        if inventory_problem:
            sys.stderr.write(
                f"[guru-gate:record-review] 拒绝写入：Detail decision inventory 未就绪：{inventory_problem}\n"
            )
            return BLOCK
    data = _task_data_for_write(task_dir, "record-review")
    if data is None:
        return BLOCK
    result = str(options.get("result") or "").strip().lower()
    max_severity = str(options.get("max_severity") or "").strip().lower()
    finding_class = str(options.get("finding_class") or "").strip().upper().replace("-", "_")
    run_id = str(options.get("run_id") or "").strip()
    reviewer = str(options.get("reviewer") or "").strip()
    evidence = str(options.get("evidence") or "").strip()
    deletion_audit = str(options.get("deletion_audit") or "").strip()
    if gate == "detail" and result == "clean" and not deletion_audit:
        sys.stderr.write("[guru-gate:record-review] 拒绝写入：detail clean review 必须带 --deletion-audit\n")
        return BLOCK
    record = {
        "run_id": run_id,
        "reviewer": reviewer,
        "recorded_at": _now_iso(),
        "artifact_digest": _gate_digest(task_dir, gate),
        "result": result,
        "max_severity": max_severity,
        "evidence": evidence[:1000],
    }
    if finding_class:
        record["finding_class"] = finding_class
    if deletion_audit:
        record["deletion_audit"] = deletion_audit[:1000]
    error = _review_run_validation_error(record)
    if error:
        sys.stderr.write(f"[guru-gate:record-review] 拒绝写入：{error}\n")
        return BLOCK
    gates = data.setdefault(GATES_KEY, {})
    if not isinstance(gates, dict):
        sys.stderr.write("[guru-gate:record-review] task.json guru_gates 必须是对象，拒绝写入\n")
        return BLOCK
    by_gate = gates.setdefault(REVIEW_RUNS_KEY, {})
    if not isinstance(by_gate, dict):
        sys.stderr.write("[guru-gate:record-review] guru_gates.review_runs 必须是对象，拒绝写入\n")
        return BLOCK
    runs = by_gate.setdefault(gate, [])
    if not isinstance(runs, list):
        sys.stderr.write(f"[guru-gate:record-review] guru_gates.review_runs.{gate} 必须是数组，拒绝写入\n")
        return BLOCK
    if any(isinstance(run, dict) and run.get("artifact_digest") == record["artifact_digest"] and run.get("run_id") == run_id for run in runs):
        sys.stderr.write(f"[guru-gate:record-review] 当前 digest 已存在 run_id={run_id} 的 {gate} review 记录\n")
        return BLOCK
    runs.append(record)
    tj_path = _write_task_data_atomic(task_dir, data)
    state = _review_state(task_dir, gate)
    print(
        f"[guru-gate:record-review] ✅ 已记录 {GATE_LABEL[gate]} review "
        f"result={result} max_severity={max_severity} run_id={run_id} "
        f"clean={state['clean_count']}/{REQUIRED_CLEAN_REVIEWS}（{tj_path}）"
    )
    return PASS


def _full_v2_confirmation_required(task_dir: str) -> bool:
    contract, error = guru_contract.load_contract(task_dir)
    return bool(
        not error
        and isinstance(contract, dict)
        and guru_contract.contract_route(contract) == guru_contract.ROUTE_FULL_CHAIN
        and contract.get("policy_version") == guru_contract.POLICY_VERSION_V2
    )


def _full_confirmation_batch_inputs(task_dir: str) -> tuple[dict | None, str]:
    risk_dir = os.path.join(task_dir, "risk-packets")
    if not os.path.isdir(risk_dir):
        return None, "Full confirmation batch requires current risk-packets/*.json before confirmation"
    risk_entries = []
    for name in sorted(os.listdir(risk_dir)):
        path = os.path.join(risk_dir, name)
        if not name.endswith(".json") or not os.path.isfile(path):
            continue
        content = read(path)
        if not content.strip():
            return None, f"Full confirmation batch risk packet is empty: {name}"
        risk_entries.append({
            "name": name,
            "digest": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        })
    if not risk_entries:
        return None, "Full confirmation batch requires at least one current risk packet"
    try:
        payload = {
            "requirements_digest": requirements_digest(task_dir),
            "detail_artifact_digest": _gate_digest(task_dir, "detail"),
            "risk_packet_set_digest": hashlib.sha256(
                json.dumps(risk_entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }
    except (GateArtifactError, RequirementManifestError, OSError, ValueError) as exc:
        return None, f"Full confirmation batch inputs unavailable: {exc}"
    payload["confirmation_batch_digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload, ""


FULL_CONFIRMATION_PROJECTION_SCHEMA_VERSION = 2
FULL_CONFIRMATION_PROJECTION_DOMAIN = b"guru-full-confirmation-projection-v2\0"
FULL_CONFIRMATION_SCOPE = "full_requirements_risk_irreversible_design_batch"
FULL_CONFIRMATION_ALLOWED_ACTION = "task_start_and_autonomous_close"
FULL_CONFIRMATION_PROMPT = (
    "One Full confirmation binds requirements, current risk packets and irreversible design"
)
FULL_CONFIRMATION_PROJECTION_FIELDS = (
    "schema_version",
    "confirmed_by",
    "confirmed_at",
    "confirmation_scope",
    "allowed_next_action",
    "prompt_summary",
    "confirmation_batch_id",
    "confirmation_batch_digest",
    "requirements_digest",
    "detail_artifact_digest",
    "risk_packet_set_digest",
)
FULL_CONFIRMATION_OPTIONAL_FIELDS = ("mode", "via", "turn_ref", "user_quote")
FULL_CONFIRMATION_RECORD_FIELDS = frozenset(
    (*FULL_CONFIRMATION_PROJECTION_FIELDS, *FULL_CONFIRMATION_OPTIONAL_FIELDS,
     "artifact_digest", "confirmation_projection_digest")
)


def _full_confirmation_projection(record: dict) -> dict:
    return {
        field: record[field]
        for field in (*FULL_CONFIRMATION_PROJECTION_FIELDS, *FULL_CONFIRMATION_OPTIONAL_FIELDS)
        if field in record
    }


def _full_confirmation_projection_digest(record: dict) -> str:
    encoded = json.dumps(
        _full_confirmation_projection(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(FULL_CONFIRMATION_PROJECTION_DOMAIN + encoded).hexdigest()


def _record_full_confirmation_batch(task_dir: str, via: str, user_quote=None) -> int:
    inputs, problem = _full_confirmation_batch_inputs(task_dir)
    if problem or not isinstance(inputs, dict):
        sys.stderr.write(f"[guru-gate:confirm] 拦截：{problem or 'Full confirmation batch inputs missing'}\n")
        return BLOCK
    data = _task_data_for_write(task_dir, "confirm")
    if data is None:
        return BLOCK
    gates = data.setdefault(GATES_KEY, {})
    batch_digest = inputs["confirmation_batch_digest"]
    batch_id = f"confirm-{batch_digest[:16]}"
    base = {
        "schema_version": FULL_CONFIRMATION_PROJECTION_SCHEMA_VERSION,
        "confirmed_by": _developer_name(),
        "confirmed_at": _now_iso(),
        "confirmation_scope": FULL_CONFIRMATION_SCOPE,
        "allowed_next_action": FULL_CONFIRMATION_ALLOWED_ACTION,
        "prompt_summary": FULL_CONFIRMATION_PROMPT,
        "confirmation_batch_id": batch_id,
        "confirmation_batch_digest": batch_digest,
        "requirements_digest": inputs["requirements_digest"],
        "detail_artifact_digest": inputs["detail_artifact_digest"],
        "risk_packet_set_digest": inputs["risk_packet_set_digest"],
    }
    turn_ref = _turn_ref()
    if turn_ref:
        base["turn_ref"] = turn_ref
    if via == "agent":
        base["mode"] = "soft"
        base["via"] = "agent"
        if user_quote:
            base["user_quote"] = user_quote[:500]
    base["confirmation_projection_digest"] = _full_confirmation_projection_digest(base)
    gates["requirements"] = {
        **base,
        "artifact_digest": inputs["requirements_digest"],
    }
    gates["detail"] = {
        **base,
        "artifact_digest": inputs["detail_artifact_digest"],
    }
    task_json_path = _write_task_data_atomic(task_dir, data)
    print(
        f"[guru-gate:confirm] Full 单批确认已写入 requirements/detail 共享 batch={batch_id}"
        f"（{task_json_path}）"
    )
    return PASS


def _full_confirmation_record_problem(record: dict, inputs: dict, artifact_digest: str) -> str:
    fields = set(record)
    unknown = sorted(fields - FULL_CONFIRMATION_RECORD_FIELDS)
    if unknown:
        return f"Full confirmation projection has unknown fields: {', '.join(unknown)}"
    required = set(FULL_CONFIRMATION_PROJECTION_FIELDS) | {
        "artifact_digest",
        "confirmation_projection_digest",
    }
    missing = sorted(required - fields)
    if missing:
        return f"Full confirmation projection missing fields: {', '.join(missing)}"
    if record.get("schema_version") != FULL_CONFIRMATION_PROJECTION_SCHEMA_VERSION:
        return "Full confirmation projection schema_version mismatch"
    for field in ("confirmed_by", "confirmed_at"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            return f"Full confirmation projection {field} must be a non-empty string"
    expected_constants = {
        "confirmation_scope": FULL_CONFIRMATION_SCOPE,
        "allowed_next_action": FULL_CONFIRMATION_ALLOWED_ACTION,
        "prompt_summary": FULL_CONFIRMATION_PROMPT,
        "confirmation_batch_id": f"confirm-{inputs['confirmation_batch_digest'][:16]}",
    }
    for field, expected in expected_constants.items():
        if record.get(field) != expected:
            if field == "confirmation_batch_id":
                return "Full confirmation batch stale: confirmation_batch_id mismatch"
            return f"Full confirmation projection {field} mismatch"
    for field in (
        "confirmation_batch_digest",
        "requirements_digest",
        "detail_artifact_digest",
        "risk_packet_set_digest",
    ):
        if record.get(field) != inputs[field]:
            return f"Full confirmation batch stale: {field} changed"
    if record.get("artifact_digest") != artifact_digest:
        return "Full confirmation batch stale: gate artifact digest changed"
    has_mode = "mode" in record
    has_via = "via" in record
    has_quote = "user_quote" in record
    if has_mode or has_via:
        if (
            record.get("mode") != "soft"
            or record.get("via") != "agent"
            or not has_quote
            or not isinstance(record.get("user_quote"), str)
            or not record["user_quote"].strip()
        ):
            return "Full confirmation projection agent optional fields are invalid"
    elif has_quote:
        return "Full confirmation projection TTY record cannot contain user_quote"
    if "turn_ref" in record and (
        not isinstance(record.get("turn_ref"), str) or not record["turn_ref"].strip()
    ):
        return "Full confirmation projection turn_ref must be a non-empty string"
    recorded_projection_digest = record.get("confirmation_projection_digest")
    if (
        not isinstance(recorded_projection_digest, str)
        or recorded_projection_digest != _full_confirmation_projection_digest(record)
    ):
        return "Full confirmation projection digest mismatch"
    return ""


def _full_confirmation_batch_problem(task_dir: str) -> str:
    inputs, problem = _full_confirmation_batch_inputs(task_dir)
    if problem or not isinstance(inputs, dict):
        return problem or "Full confirmation batch inputs missing"
    states = _gate_states(task_dir)
    requirements = states.get("requirements")
    detail = states.get("detail")
    if not all(isinstance(record, dict) and record.get("confirmed_by") for record in (requirements, detail)):
        return "Full confirmation batch missing requirements/detail records"
    requirements_peer = {
        key: value for key, value in requirements.items() if key != "artifact_digest"
    }
    detail_peer = {
        key: value for key, value in detail.items() if key != "artifact_digest"
    }
    if requirements_peer != detail_peer:
        return "Full confirmation batch requirements/detail projections diverge"
    requirements_problem = _full_confirmation_record_problem(
        requirements,
        inputs,
        inputs["requirements_digest"],
    )
    if requirements_problem:
        return requirements_problem
    detail_problem = _full_confirmation_record_problem(
        detail,
        inputs,
        inputs["detail_artifact_digest"],
    )
    if detail_problem:
        return detail_problem
    return ""


def _record_confirm(task_dir: str, gate: str, via: str, user_quote=None) -> int:
    """写入单个 Gate 的确认记录（严格 JSON 守卫 + 原子写）。via ∈ tty|agent。"""
    data = _task_data_for_write(task_dir, "confirm")
    if data is None:
        return BLOCK
    gates = data.setdefault(GATES_KEY, {})
    previous = gates.get(gate)
    route = _contract_route_for_review_policy(task_dir)
    lite_requirements = route == guru_contract.ROUTE_LITE_TASK and gate == "requirements"
    record = {
        "confirmed_by": _developer_name(),
        "confirmed_at": _now_iso(),
        "confirmation_scope": (
            "lite_prd_route_risk_scope"
            if lite_requirements
            else ("requirements_gate_only" if gate == "requirements" else "detail_gate_only")
        ),
        "allowed_next_action": (
            "task_start_and_autonomous_close"
            if lite_requirements
            else ("overview_design" if gate == "requirements" else "task_start")
        ),
        "prompt_summary": (
            "Lite confirmation binds PRD, route, risk and scope; implementation through check closes autonomously"
            if lite_requirements
            else (
                "Requirements confirmation allows overview/detail planning only"
                if gate == "requirements"
                else "Detail confirmation allows task.py start only"
            )
        ),
        # 确认快照：check 时比对，产物在确认后被修改 → 要求重新确认
        "artifact_digest": (
            requirements_confirmation_digest(task_dir)
            if lite_requirements
            else _gate_digest(task_dir, gate)
        ),
    }
    turn_ref = _turn_ref()
    if turn_ref:
        record["turn_ref"] = turn_ref
    if isinstance(previous, dict) and isinstance(previous.get("grill"), dict):
        record["grill"] = previous["grill"]
    if via == "agent":
        record["mode"] = "soft"
        record["via"] = "agent"  # 留痕：对话确认、agent 代跑（非 TTY 人手证明）
        if user_quote:
            record["user_quote"] = user_quote[:500]  # 用户确认原话（审计：伪造须编造用户言论）
    gates[gate] = record
    tj_path = _write_task_data_atomic(task_dir, data)
    suffix = "（soft：对话确认，agent 代跑）" if via == "agent" else ""
    print(f"[guru-gate:confirm] ✅ {GATE_LABEL[gate]} Gate 已由 {record['confirmed_by']} 确认{suffix}（已写入 {tj_path}）")
    return PASS


def _record_grill(task_dir: str, gate: str, status: str, via: str, user_quote=None) -> int:
    """写入 design-grill 完成/跳过记录（严格 JSON 守卫 + 原子写）。via ∈ tty|agent。"""
    manifest_problem = _requirement_package_problem(task_dir)
    if manifest_problem:
        sys.stderr.write(f"[guru-gate:grill-{status}] {manifest_problem}\n")
        return BLOCK
    policy = _grill_policy(task_dir, gate)
    data = _task_data_for_write(task_dir, f"grill-{status}")
    if data is None:
        return BLOCK
    gates = data.setdefault(GATES_KEY, {})
    entry = gates.setdefault(gate, {})
    if not isinstance(entry, dict):
        entry = {}
        gates[gate] = entry
    record = {
        "status": status,
        "by": _developer_name(),
        "at": _now_iso(),
        "policy": policy["policy"],
        "policy_reason": policy["reason"],
        "guru_chain": policy["guru_chain"],
        "risk_level": policy["risk_level"],
    }
    if status == "done":
        record["digest"] = _gate_digest(task_dir, gate)
    elif status == "skipped":
        reason = (user_quote or "").strip()
        record["reason"] = reason[:500]
        record["digest"] = _gate_digest(task_dir, gate)
    if via == "agent":
        record["mode"] = "soft"
        record["via"] = "agent"
        if user_quote:
            record["user_quote"] = user_quote[:500]
    entry["grill"] = record
    tj_path = _write_task_data_atomic(task_dir, data)
    suffix = "（soft：对话确认，agent 代跑）" if via == "agent" else ""
    if status == "done":
        print(f"[guru-gate:grill-done] ✅ {GATE_LABEL[gate]} Gate design-grill 已完成{suffix}（已写入 {tj_path}）")
    else:
        print(f"[guru-gate:grill-skip] ✅ {GATE_LABEL[gate]} Gate design-grill 已按用户理由跳过{suffix}（已写入 {tj_path}）")
    return PASS


def _grill_ok(task_dir: str, gate: str) -> bool:
    """Legacy design-grill audit state; ignored by the current Gate model."""
    state = _gate_states(task_dir).get(gate)
    grill = state.get("grill") if isinstance(state, dict) else None
    if not isinstance(grill, dict):
        return False
    if grill.get("status") == "skipped":
        if _grill_policy(task_dir, gate)["policy"] != "skippable":
            return False
        return bool((grill.get("reason") or "").strip()) and grill.get("digest") == _gate_digest(task_dir, gate)
    if grill.get("status") == "done" and grill.get("digest") == _gate_digest(task_dir, gate):
        return True
    return False


def _grill_problem(task_dir: str, gate: str) -> str:
    state = _gate_states(task_dir).get(gate)
    grill = state.get("grill") if isinstance(state, dict) else None
    policy = _grill_policy(task_dir, gate)
    if not isinstance(grill, dict):
        if policy["policy"] == "skippable":
            return "未记录旧 design-grill 完成或低风险跳过审计记录"
        return f"未记录旧 design-grill 完成审计记录（{policy['reason']}）"
    if grill.get("status") == "done":
        if not grill.get("digest"):
            return "旧 design-grill 完成记录缺 digest"
        if grill.get("digest") != _gate_digest(task_dir, gate):
            return "旧 design-grill digest 失配（产物在兼容记录后被修改）"
    if grill.get("status") == "skipped":
        if policy["policy"] != "skippable":
            return f"旧 design-grill 跳过记录不适用：当前旧审计策略为 required（{policy['reason']}）"
        if not (grill.get("reason") or "").strip():
            return "旧 design-grill 跳过记录缺理由（reason）"
        if grill.get("digest") != _gate_digest(task_dir, gate):
            return "旧 design-grill 跳过后产物被修改（digest 失配）；该兼容记录已过期"
        return ""
    return "旧 design-grill 状态非法（必须是 done 或 skipped）"


def _grill_status_mark(task_dir: str, gate: str) -> str:
    """status 呈现用：旧 design-grill 子状态，仅作兼容审计信息。"""
    state = _gate_states(task_dir).get(gate)
    grill = state.get("grill") if isinstance(state, dict) else None
    if not isinstance(grill, dict):
        return "legacy grill missing (ignored by current Gate model)"
    status = grill.get("status")
    if status in ("done", "skipped"):
        fresh = "current" if grill.get("digest") == _gate_digest(task_dir, gate) else "stale"
        return f"legacy grill present:{status}/{fresh} (ignored by current Gate model)"
    return "legacy grill invalid (ignored by current Gate model)"


def _block_grill(channel: str, task_dir: str, gate: str) -> int:
    reason = _grill_problem(task_dir, gate)
    policy = _grill_policy(task_dir, gate)
    sys.stderr.write(
        f"[guru-gate:{channel}] 拦截：旧 design-grill 兼容审计记录不满足：{reason}\n"
    )
    sys.stderr.write(
        "当前新模型不应依赖 design-grill；若你正在维护旧任务审计记录，可显式写入：\n"
    )
    sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py grill-done {gate} {task_dir}\n")
    if policy["policy"] == "skippable":
        sys.stderr.write("若本阶段确认保持 low-risk，也可记录跳过（必须留理由）：\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py grill-skip {gate} {task_dir} --user-quote \"<跳过理由>\"\n")
    else:
        sys.stderr.write(f"旧审计策略不允许 grill-skip：{policy['reason']}\n")
    return BLOCK


def _authorize_gate_write(channel: str, via_agent: bool, user_quote=None):
    """复用人工 Gate 写入守卫：strict 只认 TTY；soft 需 --via-agent + --user-quote。"""
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    mode = _gate_mode()
    if not interactive and not (mode == "soft" and via_agent):
        sys.stderr.write(
            f"[guru-gate:{channel}] 拒绝：strict 模式下人工 Gate 写入必须由用户本人在交互式终端执行（当前无 TTY）。\n"
            f"agent 不得代跑。请提示用户在自己的终端运行对应 guru_gate.py 命令。\n"
            f"（项目可在 .trellis/config.yaml 设 guru.gate_mode: soft 改为对话确认后 agent --via-agent 代跑）\n"
        )
        return False, interactive, mode
    if not interactive and not (user_quote and user_quote.strip()):
        sys.stderr.write(
            f"[guru-gate:{channel}] soft 模式 agent 代跑必须带 --user-quote \"<用户确认原话/理由>\" 记录审计留痕\n"
        )
        return False, interactive, mode
    return True, interactive, mode


def _pending_gates(task_dir: str) -> list:
    """按阶段顺序列出待人工确认 Gate（未确认 / 缺快照 / 快照失配）。"""
    states = _gate_states(task_dir)
    pending = []
    route = _contract_route_for_review_policy(task_dir)
    target_gates = ("requirements",) if route == guru_contract.ROUTE_LITE_TASK else HUMAN_GATES
    if route in {guru_contract.ROUTE_SMALL_INLINE, guru_contract.ROUTE_MICRO_TASK}:
        target_gates = ()
    if _full_v2_confirmation_required(task_dir):
        return ["detail"] if _full_confirmation_batch_problem(task_dir) else []
    for g in target_gates:
        s = states.get(g)
        current_digest = (
            requirements_confirmation_digest(task_dir)
            if route == guru_contract.ROUTE_LITE_TASK and g == "requirements"
            else _gate_digest(task_dir, g)
        )
        ok_record = (isinstance(s, dict) and s.get("confirmed_by")
                     and s.get("artifact_digest") == current_digest)
        if not ok_record:
            pending.append(g)
    return pending


def cmd_confirm(gate_arg, task_dir_arg, via_agent: bool = False, user_quote=None) -> int:
    if gate_arg is not None and gate_arg not in HUMAN_GATES:
        if gate_arg in REVIEW_GATES:
            sys.stderr.write(
                f"[guru-gate:confirm] {gate_arg} 不再走人工确认；请通过 record-review 累积两个当前 digest 的 clean review\n"
            )
        else:
            sys.stderr.write(f"[guru-gate:confirm] 未知 gate: {gate_arg}（可选: {', '.join(HUMAN_GATES)}；省略=批量确认全部待确认 Gate）\n")
        return BLOCK
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:confirm] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    route = _contract_route_for_review_policy(task_dir)
    if route == guru_contract.ROUTE_LITE_TASK and gate_arg == "detail":
        sys.stderr.write("[guru-gate:confirm] lite_task 只有一次 requirements 确认，不存在 detail 人工确认\n")
        return BLOCK
    if route in {guru_contract.ROUTE_SMALL_INLINE, guru_contract.ROUTE_MICRO_TASK}:
        print(f"[guru-gate:confirm] route={route} 不需要用户确认（{task_dir}）")
        return PASS
    if _full_v2_confirmation_required(task_dir) and gate_arg == "requirements":
        sys.stderr.write(
            "[guru-gate:confirm] Full v2 只允许一次批量确认；先完成 requirements、risk packet、"
            "Overview/Detail review，再运行不带 gate 参数的 confirm 或 confirm detail\n"
        )
        return BLOCK
    if route == guru_contract.ROUTE_LITE_TASK:
        standard_problems = _lite_standard_task_problems(task_dir)
        if standard_problems:
            return fail("confirm", standard_problems)
    # manifest fail-closed：确认快照 digest 累积 requirements 产物（含正式需求包），非法 manifest 先拦
    manifest_problem = _requirement_package_problem(task_dir)
    if manifest_problem:
        sys.stderr.write(f"[guru-gate:confirm] {manifest_problem}\n")
        return BLOCK
    allowed, interactive, mode = _authorize_gate_write("confirm", via_agent, user_quote)
    if not allowed:
        return BLOCK
    if _full_v2_confirmation_required(task_dir):
        for label, checker in (
            ("requirements", check_requirements),
            ("overview", check_overview),
            ("detail", check_detail),
        ):
            if checker(task_dir) != PASS:
                sys.stderr.write(f"[guru-gate:confirm] Full 单批确认前 {label} 结构 Gate 未通过\n")
                return BLOCK
        if _block_requirements_review("confirm", task_dir) != PASS:
            return BLOCK
        for review_gate in REVIEW_GATES:
            if not _review_state(task_dir, review_gate)["ready"]:
                return _block_review("confirm", task_dir, review_gate)
        inputs, batch_problem = _full_confirmation_batch_inputs(task_dir)
        if batch_problem or not isinstance(inputs, dict):
            sys.stderr.write(f"[guru-gate:confirm] 拦截：{batch_problem}\n")
            return BLOCK
        if interactive:
            print("即将一次确认 requirements、当前风险包和不可逆设计，确认后自动执行到 check。")
            try:
                answer = input("确认请输入 yes/y（其他=取消）：").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer not in ("yes", "y"):
                print("已取消，未写入 Full confirmation batch。")
                return BLOCK
        return _record_full_confirmation_batch(
            task_dir,
            "tty" if interactive else "agent",
            user_quote=user_quote,
        )
    targets = [gate_arg] if gate_arg else _pending_gates(task_dir)
    if not targets:
        print(f"[guru-gate:confirm] 需求/详细两个人工 Gate 均已确认且快照一致（{task_dir}），无需操作")
        return PASS
    print(f"任务：{task_dir}（gate_mode={mode}）")
    checkers = {"requirements": check_requirements, "detail": check_detail}
    for g in targets:
        # 结构 Gate 未过时确认无意义，先拦下（批量模式停在首个未过阶段）
        if checkers[g](task_dir) != PASS:
            sys.stderr.write(f"[guru-gate:confirm] {GATE_LABEL[g]}结构 Gate 未过，先修复缺口再确认；本次到此为止。\n")
            return BLOCK
        if g == "requirements":
            if _block_requirements_review("confirm", task_dir) != PASS:
                return BLOCK
        if g == "detail":
            for review_gate in REVIEW_GATES:
                if not _review_state(task_dir, review_gate)["ready"]:
                    return _block_review("confirm", task_dir, review_gate)
        if interactive:
            print(f"即将确认【{GATE_LABEL[g]} Gate】通过，允许进入下一阶段。")
            try:
                answer = input("确认请输入 yes/y（其他=取消）：").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer not in ("yes", "y"):
                print("已取消，本 Gate 及后续未写入确认。")
                return BLOCK
        rc = _record_confirm(task_dir, g, "tty" if interactive else "agent", user_quote=user_quote)
        if rc != PASS:
            return rc
    return PASS


def cmd_grill_done(gate_arg, task_dir_arg, via_agent: bool = False, user_quote=None) -> int:
    if gate_arg not in ALL_GATES:
        sys.stderr.write(f"[guru-gate:grill-done] 需要 gate 参数（{', '.join(ALL_GATES)}）\n")
        return BLOCK
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:grill-done] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    allowed, interactive, _mode = _authorize_gate_write("grill-done", via_agent, user_quote)
    if not allowed:
        return BLOCK
    return _record_grill(task_dir, gate_arg, "done", "tty" if interactive else "agent", user_quote=user_quote)


def cmd_grill_skip(gate_arg, task_dir_arg, via_agent: bool = False, user_quote=None) -> int:
    if gate_arg not in ALL_GATES:
        sys.stderr.write(f"[guru-gate:grill-skip] 需要 gate 参数（{', '.join(ALL_GATES)}）\n")
        return BLOCK
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:grill-skip] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    if not (user_quote and user_quote.strip()):
        sys.stderr.write("[guru-gate:grill-skip] 必须带 --user-quote \"<跳过理由>\" 记录用户选择跳过的原因\n")
        return BLOCK
    policy = _grill_policy(task_dir, gate_arg)
    if policy["policy"] != "skippable":
        sys.stderr.write(
            f"[guru-gate:grill-skip] 拒绝：{GATE_LABEL[gate_arg]} Gate 当前不允许跳过旧 design-grill 审计记录。"
            f"{policy['reason']}。如需维护旧记录，请显式记录兼容完成：\n"
            f"  python3 .trellis/scripts/guru/guru_gate.py grill-done {gate_arg} {task_dir}\n"
        )
        return BLOCK
    allowed, interactive, _mode = _authorize_gate_write("grill-skip", via_agent, user_quote)
    if not allowed:
        return BLOCK
    return _record_grill(task_dir, gate_arg, "skipped", "tty" if interactive else "agent", user_quote=user_quote)


def _gate_states(task_dir: str) -> dict:
    gates = _task_json_of(task_dir).get(GATES_KEY)
    return gates if isinstance(gates, dict) else {}


def _adversarial_skips(task_dir: str) -> list:
    skips = _gate_states(task_dir).get(ADVERSARIAL_SKIPS_KEY)
    return skips if isinstance(skips, list) else []


def _requirements_review(task_dir: str) -> dict:
    review = _gate_states(task_dir).get(REQUIREMENTS_REVIEW_KEY)
    return review if isinstance(review, dict) else {}


def _requirements_review_problem(task_dir: str) -> str:
    review = _requirements_review(task_dir)
    adversarial_required = _requirements_adversarial_required(task_dir)
    if not review:
        if not adversarial_required:
            return ""
        return "缺少当前需求 digest 的 opposite-provider requirements adversarial review 记录"
    recorded = review.get("artifact_digest")
    current = _gate_digest(task_dir, "requirements")
    if recorded != current:
        if not adversarial_required:
            return ""
        return "requirements adversarial review digest 失配（prd.md 已改动）"
    status = str(review.get("status", "")).strip().lower()
    if status == "clean":
        provider = str(review.get("provider", "")).strip()
        current_provider = str(review.get("current_provider", "")).strip()
        max_severity = str(review.get("max_severity", "")).strip().lower()
        if adversarial_required:
            if review.get("adversarial") is not True:
                return "requirements adversarial review 记录缺少 adversarial=true"
            if not provider or not current_provider:
                return "requirements adversarial review 记录缺少 provider/current_provider"
            if provider == current_provider:
                return "requirements adversarial review 不是 opposite-provider"
        if max_severity not in {"none", "low"}:
            return "requirements review 缺少 max_severity=none|low 证据"
        return ""
    if status == "blocked":
        reason = str(review.get("reason", "")).strip() or "requirements review blocked"
        return f"requirements adversarial review blocked：{reason}"
    if status == "deferred":
        reason = str(review.get("reason", "")).strip() or "requirements review deferred"
        if not adversarial_required and "adversarial_enabled=false" in reason:
            return ""
        return f"requirements adversarial review deferred：{reason}"
    return f"requirements adversarial review 状态非法：{status or '<missing>'}"


def _requirements_review_status_mark(task_dir: str) -> str:
    review = _requirements_review(task_dir)
    policy = _review_policy(task_dir)
    adversarial_required = bool(policy["requirements_adversarial_required"])
    if not review:
        if not adversarial_required:
            return f"✅ not required — {policy['reason']}"
        return "⬜ missing — 缺少 opposite-provider requirements adversarial review"
    status = str(review.get("status", "")).strip().lower() or "missing"
    fresh = "current" if review.get("artifact_digest") == _gate_digest(task_dir, "requirements") else "stale"
    provider = review.get("provider", "?")
    reason = str(review.get("reason", "")).strip()
    suffix = f" — {reason}" if reason else ""
    if status == "clean" and fresh == "current":
        return f"✅ clean/current ({provider}){suffix}"
    if status == "blocked" and fresh == "current":
        return f"⚠️ blocked/current ({provider}){suffix}"
    if status == "deferred" and fresh == "current":
        if not adversarial_required and "adversarial_enabled=false" in reason:
            return f"✅ deferred/current ({provider}) — adversarial disabled by config"
        return f"⚠️ deferred/current ({provider}){suffix}"
    return f"⚠️ {status}/{fresh} ({provider}){suffix}"


def _block_requirements_review(action: str, task_dir: str) -> int:
    problem = _requirements_review_problem(task_dir)
    if not problem:
        return PASS
    policy = _review_policy(task_dir)
    if not policy["adversarial_enabled"]:
        sys.stderr.write(
            f"[guru-gate:{action}] 拦截：requirements review 记录存在当前阻断问题；"
            f"{problem}。\n"
        )
        sys.stderr.write("下一步：修订需求或清理/重跑当前 digest 的 requirements review 证据后再确认。\n")
        return BLOCK
    if not policy["requirements_adversarial_required"]:
        sys.stderr.write(
            f"[guru-gate:{action}] 拦截：requirements adversarial review 按当前 route policy 可选，"
            f"但当前 requirements review 证据存在阻断问题；{problem}。\n"
        )
        sys.stderr.write("下一步：修订需求或清理/重跑当前 digest 的 requirements review 证据后再确认。\n")
        return BLOCK
    sys.stderr.write(
        f"[guru-gate:{action}] 拦截：需求确认前必须先完成 clean/current 的对抗审查证据；"
        f"{problem}。\n"
    )
    sys.stderr.write(
        "先运行 requirements review；若返回 REQ_BLOCKER/deferred/blocked，修订需求并重跑，"
        "直到输出 review_result=clean/requirements-ready：\n"
    )
    sys.stderr.write(
        f"  python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements {task_dir}\n"
    )
    return BLOCK


def cmd_status(task_dir_arg) -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:status] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    manifest_problem = _requirement_package_problem(task_dir)
    if manifest_problem:
        # manifest fail-closed：digest 取材会抛错，status 先报缺口再退出（与 requirements Gate 同口径）
        print(f"任务：{task_dir}")
        print(f"  ⚠️ requirement_package manifest — {manifest_problem}")
        print("下一步：修正 manifest.yaml 后重跑 guru_gate.py requirements / status。")
        return BLOCK
    states = _gate_states(task_dir)
    print(f"任务：{task_dir}")
    route = _contract_route_for_review_policy(task_dir)
    if route == guru_contract.ROUTE_LITE_TASK and not _task_requires_brainstorm_evidence(task_dir):
        print("  Brainstorm Evidence — not required (requirements already clear)")
    else:
        print(f"  Brainstorm Evidence — {_brainstorm_status_mark(task_dir)}")
    if route == guru_contract.ROUTE_LITE_TASK:
        standard_problems = _lite_standard_task_problems(task_dir)
        if standard_problems:
            print("  Lite standard task — invalid: " + "; ".join(standard_problems[:4]))
            return BLOCK
        confirmation_problem = _requirements_confirmation_problem(task_dir, route)
        if confirmation_problem:
            print(f"  Lite requirements confirmation — pending: {confirmation_problem}")
            print(f"下一步：python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}")
        else:
            print("  Lite requirements confirmation — current (PRD + route + risk + scope)")
            print(f"下一步：python3 .trellis/scripts/task.py start {task_dir}")
        print("  Overview/Detail reviews — not required")
        print("  Implementation Worker — not required; host continues autonomously through check")
        return PASS
    confirm_pending = []
    for g in HUMAN_GATES:
        s = states.get(g)
        if isinstance(s, dict) and s.get("confirmed_by"):
            # 与 check 同口径呈现快照状态——避免 status 报绿而 check 拦截的不一致
            recorded = s.get("artifact_digest")
            if not recorded:
                confirm_pending.append(g)
                print(f"  ⚠️ {GATE_LABEL[g]} Gate — 缺确认快照，请重新确认")
            elif recorded != _gate_digest(task_dir, g):
                confirm_pending.append(g)
                print(f"  ⚠️ {GATE_LABEL[g]} Gate — 确认快照失配（产物已改动），请重新确认")
            else:
                soft_mark = "（soft：对话确认，agent 代跑）" if s.get("via") == "agent" else ""
                scope = s.get("confirmation_scope")
                allowed = s.get("allowed_next_action")
                scope_mark = (
                    f" ｜ scope={scope} next={allowed}"
                    if scope and allowed
                    else " ｜ legacy confirmation: scope missing, not implementation/commit permission"
                )
                print(f"  ✅ {GATE_LABEL[g]} Gate — {s['confirmed_by']} @ {s.get('confirmed_at', '?')}{soft_mark}{scope_mark}")
        else:
            confirm_pending.append(g)
            print(f"  ⬜ {GATE_LABEL[g]} Gate — 未确认")

    print(f"  需求对抗 Review — {_requirements_review_status_mark(task_dir)}")

    review_pending = []
    for g in REVIEW_GATES:
        mark = _review_status_mark(task_dir, g)
        audit_mark = _review_deletion_audit_mark(task_dir, g)
        print(f"  {GATE_LABEL[g]} Review — {mark}{audit_mark} ｜ legacy {_grill_status_mark(task_dir, g)}")
        if not _review_state(task_dir, g)["ready"]:
            review_pending.append(g)

    skips = [skip for skip in _adversarial_skips(task_dir) if isinstance(skip, dict)]
    if skips:
        print("  ⚠️ 对抗审查跳过记录：")
        for skip in skips[-3:]:
            action = skip.get("action", "?")
            provider = skip.get("provider", "?")
            reason = skip.get("reason", "?")
            timestamp = skip.get("timestamp", "?")
            print(f"    - {timestamp} {action}/{provider}: {reason}")

    req_review_problem = _requirements_review_problem(task_dir)
    if req_review_problem:
        policy = _review_policy(task_dir)
        if not policy["requirements_adversarial_required"]:
            print(
                "下一步：requirements adversarial review 当前 policy 非必需，"
                "但已有 requirements review 证据存在阻断问题；先修订需求或清理/重跑该证据。"
            )
        else:
            print("下一步：先完成 requirements adversarial review，clean 后才能确认需求：")
            print(f"  python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements {task_dir}")
    elif "requirements" in confirm_pending:
        print("下一步：需求 review 已 clean/current，由用户本人在终端运行：")
        print(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}")
    elif review_pending:
        g0 = review_pending[0]
        state = _review_state(task_dir, g0)
        route_guidance = _review_route_guidance(task_dir, g0)
        if route_guidance:
            print(f"下一步：{route_guidance}")
            return PASS
        if (
            state.get("adversarial_required", True)
            and
            state["clean_count"] >= REQUIRED_CLEAN_REVIEWS
            and not state.get("has_adversarial_clean")
        ):
            audit_hint = ' --deletion-audit "<none|删除审计摘要>"' if g0 == "detail" else ""
            print(
                f"下一步：{GATE_LABEL[g0]} 已有双 clean，但缺 opposite-provider adversarial clean review；运行："
            )
            print(
                f"  python3 .trellis/scripts/guru/guru_supervise.py --adversarial {g0} {task_dir}"
            )
            print(
                f"  python3 .trellis/scripts/guru/guru_gate.py record-review {g0} {task_dir} "
                f"--result clean --max-severity low --reviewer clean-context-adversarial-<provider> --run-id <id> --evidence \"<review证据>\"{audit_hint}"
            )
            return PASS
        adv_note = (
            "（其中至少一次 adversarial）"
            if state.get("adversarial_required", True)
            else f"（{state.get('adversarial_policy_reason', 'adversarial not required')}）"
        )
        print(f"下一步：继续 {GATE_LABEL[g0]} review，当前 digest 需要两个不同 run-id 的 clean 记录{adv_note}：")
        audit_hint = ' --deletion-audit "<none|删除审计摘要>"' if g0 == "detail" else ""
        print(
            f"  python3 .trellis/scripts/guru/guru_gate.py record-review {g0} {task_dir} "
            f"--result clean --max-severity low --reviewer clean-context[-adversarial-<provider>] --run-id <id> --evidence \"<review证据>\"{audit_hint}"
        )
    elif "detail" in confirm_pending:
        print("下一步：详细设计已双 clean，由用户本人在终端运行：")
        print(f"  python3 .trellis/scripts/guru/guru_gate.py confirm detail {task_dir}")
    else:
        print("START_READY：需求确认、概要/详细双 clean review、详细确认均已完成。")
        print(f"下一步只允许：python3 .trellis/scripts/task.py start {task_dir}")
        print("注意：START_READY 不授权实现、review worker、git commit 或发布。")
    return PASS


def _lite_standard_task_problems(task_dir: str) -> list:
    problems = []
    for name in ("task.json", "prd.md", "implement.jsonl", "check.jsonl", guru_contract.CONTRACT_FILE):
        path = os.path.join(task_dir, name)
        if not os.path.isfile(path):
            problems.append(f"Lite standard task artifact missing: {name}")
    if os.path.isfile(os.path.join(task_dir, "prd.md")) and not read(os.path.join(task_dir, "prd.md")).strip():
        problems.append("Lite standard task prd.md must be non-empty")
    task_data = _task_json_of(task_dir)
    if not str(task_data.get("id") or task_data.get("name") or "").strip():
        problems.append("Lite standard task task.json must contain id or name")
    contract, error = guru_contract.load_contract(task_dir)
    if error:
        problems.append(error)
        return problems
    if not isinstance(contract, dict):
        problems.append("Lite standard task gate-contract.json missing or malformed")
        return problems
    contract_problems = guru_contract.validate_contract(contract)
    if contract_problems:
        problems.extend(f"Lite gate contract invalid: {problem}" for problem in contract_problems)
    if guru_contract.contract_route(contract) != guru_contract.ROUTE_LITE_TASK:
        problems.append("Lite standard task requires gate-contract.json route=lite_task")
    if guru_contract.contract_risk(contract) not in {guru_contract.RISK_LOW, guru_contract.RISK_MEDIUM}:
        problems.append("Lite standard task risk must be low or medium")
    execution_policy = contract.get("execution_policy")
    scope_fingerprint = (
        execution_policy.get("scope_fingerprint")
        if isinstance(execution_policy, dict)
        else None
    )
    if not re.fullmatch(r"[0-9a-f]{64}", str(scope_fingerprint or "")):
        problems.append("Lite execution_policy.scope_fingerprint must be a sha256 digest")
    generation = execution_policy.get("selection_generation") if isinstance(execution_policy, dict) else None
    if not isinstance(generation, int) or isinstance(generation, bool) or generation <= 0:
        problems.append("Lite execution_policy.selection_generation must be a positive integer")
    brainstorm_required = (
        execution_policy.get("brainstorm_required")
        if isinstance(execution_policy, dict)
        else None
    )
    if not isinstance(brainstorm_required, bool):
        problems.append("Lite execution_policy.brainstorm_required must be boolean")
    return problems


def _requirements_confirmation_problem(task_dir: str, route: str) -> str:
    state = _gate_states(task_dir).get("requirements")
    if not (isinstance(state, dict) and state.get("confirmed_by")):
        return "需求 Gate 未确认"
    current = (
        requirements_confirmation_digest(task_dir)
        if route == guru_contract.ROUTE_LITE_TASK
        else _gate_digest(task_dir, "requirements")
    )
    recorded = state.get("artifact_digest")
    if not recorded:
        return "需求 Gate 缺确认快照"
    if recorded != current:
        return "需求 Gate 确认快照失配（PRD、route、risk 或 scope 在确认后变化）"
    return ""


def cmd_check_start(task_dir_arg, channel: str = "check-start") -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        # check 是阻断闸门：定位不到任务即拒绝（与"任一不满足 exit 2"的合同一致）。
        # before_start 注入 TASK_JSON_PATH、hook 透传命令参数，正常路径都可定位。
        sys.stderr.write(f"[guru-gate:{channel}] 无法定位任务目录，请显式传 task_dir 或确保 TASK_JSON_PATH 已注入\n")
        return BLOCK
    route = _contract_route_for_review_policy(task_dir)
    if route == guru_contract.ROUTE_LITE_TASK:
        standard_problems = _lite_standard_task_problems(task_dir)
        if standard_problems:
            return fail(channel, standard_problems)
        if check_requirements(task_dir) != PASS:
            sys.stderr.write(f"[guru-gate:{channel}] 拦截：Lite requirements 结构 Gate 当前未通过。\n")
            return BLOCK
        if _block_requirements_review(channel, task_dir) != PASS:
            return BLOCK
        confirmation_problem = _requirements_confirmation_problem(task_dir, route)
        if confirmation_problem:
            sys.stderr.write(f"[guru-gate:{channel}] 拦截：{confirmation_problem}\n")
            sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}\n")
            return BLOCK
        print(
            f"[guru-gate:{channel}] START_READY: Lite 标准任务 + 当前 requirements 确认有效；"
            "跳过 Overview/Detail review 和 implementation Worker，start 后自动执行到 check。"
        )
        return PASS
    if route in {guru_contract.ROUTE_SMALL_INLINE, guru_contract.ROUTE_MICRO_TASK}:
        print(f"[guru-gate:{channel}] START_READY: route={route} 无人工确认或 Overview/Detail Gate")
        return PASS

    # Full/legacy 结构 Gate 复跑：防止"确认后再改产物"带病 start（确认只代表确认时点的状态）
    for gate, checker in (("requirements", check_requirements),
                          ("overview", check_overview),
                          ("detail", check_detail)):
        if checker(task_dir) != PASS:
            sys.stderr.write(f"[guru-gate:{channel}] 拦截：{GATE_LABEL[gate]}结构 Gate 当前未通过"
                             f"（产物在 Gate 证据后被修改？）。\n")
            if gate == "overview":
                sys.stderr.write("修复概要后重新运行 overview review loop 并写入 record-review overview；overview 不走人工确认。\n")
            elif gate == "requirements":
                sys.stderr.write("修复需求后请用户重新人工确认 requirements。\n")
            else:
                sys.stderr.write("修复详细设计后重新完成 detail 双 clean review，再请用户人工确认 detail。\n")
            return BLOCK
    states = _gate_states(task_dir)
    if _block_requirements_review(channel, task_dir) != PASS:
        return BLOCK
    if _full_v2_confirmation_required(task_dir):
        for gate in REVIEW_GATES:
            if not _review_state(task_dir, gate)["ready"]:
                return _block_review(channel, task_dir, gate)
        batch_problem = _full_confirmation_batch_problem(task_dir)
        if batch_problem:
            sys.stderr.write(f"[guru-gate:{channel}] 拦截：{batch_problem}\n")
            sys.stderr.write(
                f"  python3 .trellis/scripts/guru/guru_gate.py confirm {task_dir}\n"
            )
            return BLOCK
        print(
            f"[guru-gate:{channel}] START_READY: Full requirements + risk packet + irreversible design "
            f"共享一次 current confirmation batch（{task_dir}）。"
        )
        return PASS
    req = states.get("requirements")
    if not (isinstance(req, dict) and req.get("confirmed_by")):
        sys.stderr.write(f"[guru-gate:{channel}] 拦截：需求 Gate 未确认（任务 {task_dir}）\n")
        sys.stderr.write("由用户本人在交互式终端执行：\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}\n")
        return BLOCK
    req_digest = req.get("artifact_digest")
    if not req_digest or req_digest != _gate_digest(task_dir, "requirements"):
        reason = "缺确认快照" if not req_digest else "确认快照失配（产物在确认后被修改）"
        sys.stderr.write(f"[guru-gate:{channel}] 拦截：需求 Gate {reason}\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}\n")
        return BLOCK

    for gate in REVIEW_GATES:
        if not _review_state(task_dir, gate)["ready"]:
            return _block_review(channel, task_dir, gate)

    detail = states.get("detail")
    if not (isinstance(detail, dict) and detail.get("confirmed_by")):
        sys.stderr.write(f"[guru-gate:{channel}] 拦截：详细设计 Gate 未确认（任务 {task_dir}）\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm detail {task_dir}\n")
        return BLOCK
    detail_digest = detail.get("artifact_digest")
    if not detail_digest or detail_digest != _gate_digest(task_dir, "detail"):
        reason = "缺确认快照" if not detail_digest else "确认快照失配（产物在确认后被修改）"
        sys.stderr.write(f"[guru-gate:{channel}] 拦截：详细设计 Gate {reason}\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm detail {task_dir}\n")
        return BLOCK
    print(
        f"[guru-gate:{channel}] START_READY: 需求确认 + 概要/详细双 clean review + "
        f"详细确认均有效（{task_dir}）。下一步只允许 task.py start；"
        "不授权实现、review worker、git commit 或发布。"
    )
    return PASS


def cmd_check(task_dir_arg) -> int:
    sys.stderr.write("[guru-gate:check] deprecated alias for check-start; START_READY only.\n")
    return cmd_check_start(task_dir_arg, "check")


def _task_status(task_dir: str) -> str:
    data = _task_json_of(task_dir)
    status = data.get("status", "planning")
    return status if isinstance(status, str) and status else "planning"


def cmd_check_implementation(task_dir_arg) -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:check-implementation] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    if cmd_check_start(task_dir, "check-implementation") != PASS:
        return BLOCK
    route = _contract_route_for_review_policy(task_dir)
    status = _task_status(task_dir)
    if route in {guru_contract.ROUTE_LITE_TASK, guru_contract.ROUTE_FULL_CHAIN} and status != "in_progress":
        sys.stderr.write(
            f"[guru-gate:check-implementation] 拦截：task.json.status={status!r}，"
            "实现/检查 worker 只能在 task.py start 后运行。\n"
        )
        if status == "planning":
            sys.stderr.write(
                f"当前只达到 START_READY；下一步运行：python3 .trellis/scripts/task.py start {task_dir}\n"
            )
        return BLOCK
    if route == guru_contract.ROUTE_FULL_CHAIN:
        packet_problem = _implementation_packet_preflight_problem(task_dir)
        if packet_problem:
            sys.stderr.write(f"[guru-gate:check-implementation] 拦截：{packet_problem}\n")
            sys.stderr.write(f"下一步：python3 .trellis/scripts/guru/guru_gate.py slice-plan {task_dir}\n")
            return BLOCK
    print(f"[guru-gate:check-implementation] IMPLEMENTATION_READY: task status is in_progress（{task_dir}）")
    return PASS


def _repo_root() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return os.getcwd()


def _git_staged_paths(root: str) -> tuple[list, str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--no-renames", "-z"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"无法读取 staged changes：{exc}"
    if result.returncode != 0:
        return [], f"git diff --cached 失败：{result.stderr.strip()}"
    paths = [p for p in result.stdout.split("\0") if p]
    return paths, ""


def _task_relative_prefix(task_dir: str, root: str) -> str:
    try:
        return os.path.relpath(os.path.realpath(task_dir), os.path.realpath(root)).replace(os.sep, "/").rstrip("/") + "/"
    except ValueError:
        return ""


def _is_task_artifact_path(path: str, task_dir: str, root: str) -> bool:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if (
        normalized == ".trellis/tasks"
        or normalized.startswith(".trellis/tasks/")
        or normalized == ".trellis/workspace"
        or normalized.startswith(".trellis/workspace/")
    ):
        return True
    task_prefix = _task_relative_prefix(task_dir, root)
    if task_prefix and normalized.startswith(task_prefix):
        return True
    return False


def _latest_jsonl_record(path: str) -> tuple:
    latest = None
    if not os.path.isfile(path):
        return None, "implementation review record missing"
    try:
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    return None, f"implementation review record line {lineno} invalid JSON: {exc}"
                if isinstance(row, dict):
                    latest = row
    except OSError as exc:
        return None, f"cannot read implementation review record: {exc}"
    if latest is None:
        return None, "implementation review record empty"
    return latest, ""


def _path_in_targets(path: str, target_paths: list) -> bool:
    normalized = path.replace("\\", "/")
    for raw_target in target_paths:
        if not isinstance(raw_target, str) or not raw_target.strip():
            continue
        target = raw_target.replace("\\", "/").strip().strip("/")
        while target.startswith("./"):
            target = target[2:]
        if target == ".":
            return True
        if normalized == target or normalized.startswith(target + "/"):
            return True
    return False


def _implementation_review_record_id(record: dict, fallback: str) -> str:
    for key in ("run_id", "review_target", "slice_id"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def _implementation_review_base_problem(record, label: str) -> str:
    if not isinstance(record, dict):
        return f"{label} missing"
    verdict_problem = guru_review_record.validate_verdict_values(record)
    if verdict_problem:
        return (
            f"{label} is malformed or incomplete; run implementation-review "
            "--staged for a complete clean verdict"
        )
    if str(record.get("review_result", "")).strip().lower() != "clean":
        return f"{label} is not clean: review_result={record.get('review_result')!r}"
    if str(record.get("route_class", "none")).strip() not in {"", "none"}:
        return f"{label} route_class is not none: {record.get('route_class')!r}"
    if str(record.get("supervisor_failure", "none")).strip() not in {"", "none"}:
        return f"{label} has supervisor_failure={record.get('supervisor_failure')!r}"
    if record.get("required_satisfied") is not True:
        return f"{label} did not satisfy required semantic provider"
    for key, bad_values in (
        ("deterministic_checks", {"failed", "missing"}),
        ("dirty_scope", {"invalid"}),
        ("invariant_coverage", {"failed", "missing"}),
    ):
        value = str(record.get(key, "")).strip().lower()
        if value in bad_values:
            return f"{label} has {key}={value}"
    target_paths = record.get("target_paths")
    if not isinstance(target_paths, list) or not target_paths:
        return f"{label} has no target_paths; cannot prove staged scope belongs to reviewed slice"
    reviewed_digest = record.get("reviewed_target_digest")
    if not isinstance(reviewed_digest, str) or not reviewed_digest.strip():
        return f"{label} has no reviewed_target_digest; run implementation-review --staged before commit"
    return ""


def _implementation_review_problem(record, staged_paths: list, task_dir: str, root: str) -> str:
    problem = _implementation_review_base_problem(record, "latest implementation review")
    if problem:
        return problem
    target_paths = record.get("target_paths")
    task_artifact_paths = [
        path for path in staged_paths
        if _is_task_artifact_path(path, task_dir, root)
    ]
    if task_artifact_paths:
        return "staged task artifacts are not covered by latest implementation review: " + ", ".join(task_artifact_paths[:5])
    code_paths = [
        path for path in staged_paths
        if path not in task_artifact_paths
    ]
    if not code_paths:
        return "staged changes contain only task artifacts/workspace artifacts; this is not a Guru implementation commit"
    out_of_scope = [path for path in code_paths if not _path_in_targets(path, target_paths)]
    if out_of_scope:
        return "staged paths outside latest reviewed target_paths: " + ", ".join(out_of_scope[:5])
    reviewed_digest = record.get("reviewed_target_digest")
    try:
        staged_digest = guru_review_record.target_snapshot_digest(root, target_paths, "index")
    except guru_review_record.ReviewRecordError as exc:
        return f"cannot compute staged target digest: {exc}"
    if staged_digest != reviewed_digest:
        return "staged target content differs from latest clean implementation review; rerun implementation-review --staged"
    return ""


def _contract_validation_problem(contract: dict, staged_paths: list, task_dir: str, root: str) -> str:
    problems = guru_contract.validate_commit_contract(contract, staged_paths, task_dir, root)
    if problems:
        return "; ".join(problems[:5])
    return ""


def _micro_commit_contract_problem(contract: dict, staged_paths: list, task_dir: str, root: str) -> str:
    problem = _contract_validation_problem(contract, staged_paths, task_dir, root)
    if problem:
        return problem
    high_path_signals, _cross_layer_or_storage, _code_paths = _micro_commit_high_path_signals(
        contract,
        staged_paths,
        task_dir,
        root,
    )
    if high_path_signals:
        return "micro_task staged paths contain high-risk signals: " + ", ".join(high_path_signals[:5])
    return ""


def _micro_commit_high_path_signals(contract: dict, staged_paths: list, task_dir: str, root: str) -> tuple[list, bool, list]:
    code_paths = [
        path for path in staged_paths
        if not guru_contract.is_task_artifact_path(path, task_dir, root)
    ]
    high_path_signals = set(guru_contract.high_risk_path_signals(code_paths))
    cross_layer_or_storage = guru_risk.has_cross_layer_or_storage(code_paths)
    if cross_layer_or_storage:
        high_path_signals.add("cross-layer/storage path signal")
    return sorted(high_path_signals), cross_layer_or_storage, code_paths


def _is_test_path(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/").lower()
    base = os.path.basename(normalized)
    return (
        normalized.startswith(("test/", "tests/", "__tests__/"))
        or "/test/" in normalized
        or "/tests/" in normalized
        or base.endswith(("_test.dart", "_test.py", "_spec.rb", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"))
    )


def _split_path_layer(path: str) -> str:
    normalized = str(path or "").replace("\\", "/").lower()
    if _is_test_path(normalized):
        return "tests"
    if any(keyword in normalized for keyword in guru_risk.STORAGE_KEYWORDS):
        return "storage"
    for layer, keywords in guru_risk.LAYER_GROUPS.items():
        if any(keyword in normalized for keyword in keywords):
            return layer
    return "other"


def _path_match_tokens(path: str) -> set:
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    stem = re.sub(r"(_test|_spec|\.test|\.spec)$", "", stem)
    return {part for part in re.split(r"[^a-z0-9]+", stem) if len(part) >= 3 and part not in {"test", "spec"}}


def _path_match_stem(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    return re.sub(r"(_test|_spec|\.test|\.spec)$", "", stem)


def _paths_look_paired(code_path: str, test_path: str) -> bool:
    code_stem = _path_match_stem(code_path)
    test_stem = _path_match_stem(test_path)
    if code_stem and test_stem and (code_stem in test_stem or test_stem in code_stem):
        return True
    return len(_path_match_tokens(code_path).intersection(_path_match_tokens(test_path))) >= 2


def _paired_test_paths(layer_paths: list, test_paths: list) -> list:
    if not layer_paths or not test_paths:
        return []
    paired = []
    for test_path in test_paths:
        if any(_paths_look_paired(path, test_path) for path in layer_paths):
            paired.append(test_path)
    return paired


def _micro_commit_split_suggestions(staged_paths: list, task_dir: str, root: str) -> list:
    code_paths = [
        path for path in staged_paths
        if not guru_contract.is_task_artifact_path(path, task_dir, root)
    ]
    test_paths = [path for path in code_paths if _is_test_path(path)]
    layer_groups: dict[str, list] = {}
    for path in code_paths:
        if path in test_paths:
            continue
        layer = _split_path_layer(path)
        layer_groups.setdefault(layer, []).append(path)
    if not layer_groups and test_paths:
        layer_groups["tests"] = []
    suggestions = []
    for layer in sorted(layer_groups):
        paths = sorted(layer_groups[layer])
        paired_tests = _paired_test_paths(paths, test_paths) if layer != "tests" else sorted(test_paths)
        stage_paths = _dedupe_strings(paths + paired_tests)
        suggestions.append({
            "layer": layer,
            "paths": paths,
            "paired_tests": paired_tests,
            "stage_command": _stage_command(stage_paths)[0] if stage_paths else "",
        })
    unpaired_tests = [path for path in test_paths if not any(path in row["paired_tests"] for row in suggestions)]
    if unpaired_tests:
        suggestions.append({
            "layer": "tests",
            "paths": [],
            "paired_tests": sorted(unpaired_tests),
            "stage_command": _stage_command(sorted(unpaired_tests))[0],
        })
    return suggestions


def _write_micro_split_guidance(staged_paths: list, task_dir: str, root: str) -> None:
    suggestions = _micro_commit_split_suggestions(staged_paths, task_dir, root)
    sys.stderr.write(
        "下一步：拆分 staged scope，按 layer 分别提交并尽量带上对应 tests；"
        "cross-layer/storage high-risk signal 不能通过 gate-degradations.jsonl 降级。\n"
    )
    for suggestion in suggestions[:6]:
        layer = suggestion.get("layer") or "other"
        command = suggestion.get("stage_command") or "git add -- <paths>"
        paired_tests = suggestion.get("paired_tests") or []
        suffix = f" paired_tests={', '.join(paired_tests[:5])}" if paired_tests else ""
        sys.stderr.write(f"  - {layer}: {command}{suffix}\n")


def _cmd_check_micro_commit(task_dir: str, contract: dict, staged_paths: list, root: str) -> int:
    problem = _micro_commit_contract_problem(contract, staged_paths, task_dir, root)
    if problem:
        sys.stderr.write(f"[guru-gate:check-commit] 拦截：{problem}\n")
        high_signal_problem = problem.startswith("micro_task staged paths contain high-risk signals:")
        high_path_signals, cross_layer_or_storage, _code_paths = _micro_commit_high_path_signals(
            contract,
            staged_paths,
            task_dir,
            root,
        )
        if high_signal_problem and high_path_signals:
            if cross_layer_or_storage:
                _write_micro_split_guidance(staged_paths, task_dir, root)
            else:
                sys.stderr.write(
                    "下一步：拆分或升级为 lite/full 后重跑对应 review；"
                    "high-risk path signals 不能通过 gate-degradations.jsonl 降级。\n"
                )
        else:
            sys.stderr.write(
                "下一步：收窄 staged scope / 补齐允许的可选 gate degradation 补偿检查，"
                "或将任务升级为 lite/full 后重跑对应 review。\n"
            )
        return BLOCK
    print(f"[guru-gate:check-commit] COMMIT_READY: micro_task contract allows scoped low-risk commit（{task_dir}）")
    return PASS


def _direct_low_risk_commit_problem(staged_paths: list, root: str) -> str:
    artifact_paths = [path for path in staged_paths if guru_contract.is_task_artifact_path(path, "", root)]
    if artifact_paths:
        return "direct low-risk commit cannot include task artifacts/workspace artifacts: " + ", ".join(artifact_paths[:5])
    code_paths = [path for path in staged_paths if path not in artifact_paths]
    if not code_paths:
        return "direct low-risk commit requires staged implementation files"
    if len(code_paths) > 3:
        return f"direct low-risk commit staged file count {len(code_paths)} exceeds max_files=3"
    high_path_signals = set(guru_contract.high_risk_path_signals(code_paths))
    if guru_risk.has_cross_layer_or_storage(code_paths):
        high_path_signals.add("cross-layer/storage path signal")
    if high_path_signals:
        return "direct low-risk staged paths contain high-risk signals: " + ", ".join(sorted(high_path_signals)[:5])
    return ""


def _cmd_check_direct_low_risk_commit(staged_paths: list, root: str) -> int:
    problem = _direct_low_risk_commit_problem(staged_paths, root)
    if problem:
        sys.stderr.write(f"[guru-gate:check-commit] 拦截：{problem}\n")
        sys.stderr.write(
            "下一步：创建/切换到 micro_task 或 lite/full 任务并生成 gate-contract.json，"
            "或收窄 staged scope 后重跑 check-commit。\n"
        )
        return BLOCK
    print("[guru-gate:check-commit] COMMIT_READY: direct small_inline scoped low-risk commit")
    return PASS


def _compact_gate_output(text: str) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return "; ".join(lines[:4])


def _captured_gate_problem(cmd: str, task_dir: str, root: str) -> str:
    try:
        result = subprocess.run(
            [sys.executable or "python3", os.path.abspath(__file__), cmd, task_dir],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"{cmd} failed to run: {exc}"
    if result.returncode == PASS:
        return ""
    detail = _compact_gate_output(result.stderr) or _compact_gate_output(result.stdout)
    return detail or f"{cmd} failed with rc={result.returncode}"


def _display_task_dir(task_dir: str, root: str) -> str:
    if not task_dir:
        return ""
    try:
        rel = os.path.relpath(os.path.realpath(task_dir), os.path.realpath(root)).replace(os.sep, "/")
        if not rel.startswith("../"):
            return rel
    except ValueError:
        pass
    return task_dir


def _gate_command(command: str, task_dir: str, root: str) -> str:
    display_task = _display_task_dir(task_dir, root)
    suffix = f" {shlex.quote(display_task)}" if display_task else ""
    return f"python3 .trellis/scripts/guru/guru_gate.py {command}{suffix}"


def _implementation_review_command(task_dir: str, root: str) -> str:
    display_task = _display_task_dir(task_dir, root)
    suffix = f" {shlex.quote(display_task)}" if display_task else ""
    return f"python3 .trellis/scripts/guru/guru_supervise.py implementation-review{suffix} --staged"


def _implementation_review_slice_command(task_dir: str, root: str, slice_id: str) -> str:
    display_task = _display_task_dir(task_dir, root)
    suffix = f" {shlex.quote(display_task)}" if display_task else ""
    return (
        "python3 .trellis/scripts/guru/guru_supervise.py "
        f"implementation-review{suffix} --slice {shlex.quote(slice_id)} --staged"
    )


def _stage_command(paths: list) -> list:
    cleaned = [path for path in paths if isinstance(path, str) and path.strip()]
    if not cleaned:
        return []
    if any(path.strip().strip("/") in {"", "."} for path in cleaned):
        return []
    chunk_size = 20
    return [
        "git add -- " + " ".join(shlex.quote(path) for path in cleaned[i:i + chunk_size])
        for i in range(0, len(cleaned), chunk_size)
    ]


def _dedupe_strings(values: list) -> list:
    seen = set()
    deduped = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _new_commit_plan(staged_paths: list) -> dict:
    return {
        "schema_version": 1,
        "route": "",
        "commit_mode": "implementation",
        "task_dir": "",
        "staged_paths": staged_paths,
        "allowed_stage_paths": [],
        "forbidden_stage_paths": [],
        "can_commit_now": False,
        "split_required": False,
        "blocking_reasons": [],
        "required_commands": [],
        "optional_commands": [],
        "required_user_confirmations": [],
        "suggested_stage_commands": [],
        "split_suggestions": [],
        "review_coverage": _empty_review_coverage(),
        "stop_boundary": "before_commit",
        "contract_present": False,
        "contract_valid": None,
    }


def _empty_review_coverage() -> dict:
    return {
        "source": "review-records/implementation-reviews.jsonl",
        "records_considered": 0,
        "records_current_clean": 0,
        "covered_staged_paths": [],
        "uncovered_staged_paths": [],
        "forbidden_staged_paths": [],
        "covering_reviews": {},
        "covering_review_ids": [],
        "ignored_reviews": [],
        "ignored_covering_review_ids": [],
        "ignored_covering_staged_paths": [],
        "missing_review_commands": [],
    }


def _finish_commit_plan(plan: dict) -> dict:
    plan["allowed_stage_paths"] = _dedupe_strings(plan.get("allowed_stage_paths", []))
    plan["forbidden_stage_paths"] = _dedupe_strings(plan.get("forbidden_stage_paths", []))
    plan["blocking_reasons"] = _dedupe_strings(plan.get("blocking_reasons", []))
    plan["required_commands"] = _dedupe_strings(plan.get("required_commands", []))
    plan["optional_commands"] = _dedupe_strings(plan.get("optional_commands", []))
    plan["required_user_confirmations"] = _dedupe_strings(plan.get("required_user_confirmations", []))
    suggested = _dedupe_strings(plan.get("suggested_stage_commands", []))
    if not suggested:
        suggested = _stage_command(plan.get("allowed_stage_paths", []))
    plan["suggested_stage_commands"] = suggested
    if plan.get("split_required"):
        plan["commit_mode"] = "split_required"
    return plan


def _write_json_atomic(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def _parse_positive_int(value: str, field: str, problems: list):
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        problems.append(f"{field} must be a positive integer")
        return None
    if parsed <= 0:
        problems.append(f"{field} must be a positive integer")
        return None
    return parsed


def _parse_confidence(value: str, problems: list):
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        problems.append("confidence must be a number between 0 and 1")
        return None
    if parsed < 0 or parsed > 1:
        problems.append("confidence must be a number between 0 and 1")
        return None
    return parsed


def _contract_bool(value) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _contract_for_intake(
    assessment: dict,
    paths: list,
    *,
    created_by: str = "intake",
    selection: guru_delivery_policy.DeliverySelection | None = None,
) -> tuple[dict | None, list]:
    route = guru_contract.normalize_route(assessment.get("route"))
    risk = guru_contract.normalize_risk(assessment.get("risk"))
    problems = []
    if route == guru_contract.ROUTE_SMALL_INLINE:
        return None, ["small_inline has no commit contract; use --commit-requested to route a commit through micro_task"]
    contract = guru_contract.default_contract(route, risk, created_by=created_by)
    if selection is not None:
        contract.update(guru_delivery_policy.selection_to_contract_patch(selection))
    contract["assessment"] = {
        "confidence": assessment.get("confidence"),
        "reasons": assessment.get("reasons") if isinstance(assessment.get("reasons"), list) else [],
        "risk_flags": assessment.get("risk_flags") if isinstance(assessment.get("risk_flags"), list) else [],
        "recommended_route": guru_contract.normalize_route(
            assessment.get("recommended_contract") or guru_contract.recommended_route_for_risk(risk)
        ),
    }
    contract["route_selection"] = {
        "selected_route": route,
        "source": selection.selection_source if selection is not None else "recommended",
        "recommended_route": contract["assessment"]["recommended_route"],
        "risk_acknowledged": False,
        "user_quote": "",
        "selected_by": "user" if selection is not None and selection.selection_source == "user_override" else "system",
        "selected_at": _now_iso(),
    }
    if selection is not None:
        contract["route_selection"].update({
            "selection_generation": selection.selection_generation,
            "scope_fingerprint": selection.scope_fingerprint,
        })
    clean_paths = [str(path).strip() for path in paths if str(path).strip()]
    if clean_paths:
        contract.setdefault("scope", {})["allowed_paths"] = clean_paths
        contract.setdefault("scope", {})["max_files"] = len(clean_paths)
    if route == guru_contract.ROUTE_MICRO_TASK and risk == guru_contract.RISK_LOW:
        contract["allowed_degradations"] = [
            {"gate": "gitnexus_impact", "fallback_checks": ["rg_callers", "git_diff_check"]},
            {"gate": "gitnexus_detect_changes", "fallback_checks": ["git_diff_check"]},
        ]
    elif route == guru_contract.ROUTE_LITE_TASK and risk in {guru_contract.RISK_LOW, guru_contract.RISK_MEDIUM}:
        contract["allowed_degradations"] = [
            {"gate": "gitnexus_impact", "fallback_checks": ["rg_callers", "scoped_tests", "git_diff_check"]},
            {"gate": "gitnexus_detect_changes", "fallback_checks": ["scoped_tests", "git_diff_check"]},
        ]
    problems.extend(guru_contract.validate_contract(contract))
    return contract, problems


def _update_task_route_metadata(
    task_dir: str,
    route: str,
    risk: str,
    selection: guru_delivery_policy.DeliverySelection | None = None,
) -> None:
    path = os.path.join(task_dir, "task.json")
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return
    if not isinstance(data, dict):
        return
    if route == guru_contract.ROUTE_FULL_CHAIN:
        data["guru_chain"] = "full"
    elif route in {guru_contract.ROUTE_MICRO_TASK, guru_contract.ROUTE_LITE_TASK}:
        data["guru_chain"] = "light"
    meta = data.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["route"] = route
        meta["risk"] = risk
        if selection is not None:
            meta["recommended_route"] = selection.recommended_route
            meta["selected_route"] = selection.selected_route
            meta["selection_source"] = selection.selection_source
            meta["selection_generation"] = selection.selection_generation
            meta["scope_fingerprint"] = selection.scope_fingerprint
    data["route"] = route
    data["risk"] = risk
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def _intake_suggested_commands(assessment: dict, paths: list, task_dir: str | None, root: str) -> list:
    route = guru_contract.normalize_route(assessment.get("route"))
    risk = guru_contract.normalize_risk(assessment.get("risk"))
    if route == guru_contract.ROUTE_SMALL_INLINE:
        return [
            "inline implementation and a reversible scoped commit are allowed; "
            "rerun intake only if semantic scope, risk, coupling, or verification cost expands"
        ]
    display_task = _display_task_dir(task_dir, root) if task_dir else "<task-dir>"
    commands = []
    if not task_dir:
        if route == guru_contract.ROUTE_MICRO_TASK:
            commands.append('python3 .trellis/scripts/task.py create "<short task title>" --priority P2')
        elif route == guru_contract.ROUTE_LITE_TASK:
            commands.append('python3 .trellis/scripts/task.py create "<short task title>" --priority P2')
        else:
            commands.append('python3 .trellis/scripts/task.py create "<short task title>" --priority P1')
    path_args = " ".join(f"--allowed-path {shlex.quote(path)}" for path in paths)
    if path_args:
        path_args = " " + path_args
    max_files = len(paths) if paths and route == guru_contract.ROUTE_MICRO_TASK else None
    max_arg = f" --max-files {max_files}" if max_files else ""
    commands.append(
        f"python3 .trellis/scripts/guru/guru_gate.py init-contract {shlex.quote(display_task)} "
        f"--route {route} --risk {risk}{path_args}{max_arg}"
    )
    return commands


def cmd_intake(task_dir_arg, options: dict) -> int:
    root = _repo_root()
    task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False) if task_dir_arg else None
    if not task_dir and task_dir_arg and os.path.isdir(task_dir_arg):
        task_dir = os.path.abspath(task_dir_arg)
    previous = None
    if task_dir:
        previous, read_error = guru_contract.load_contract(task_dir)
        if read_error:
            print(json.dumps({
                "schema_version": 1,
                "blocking_reasons": [f"existing contract unreadable: {read_error}"],
                "contract_written": False,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return BLOCK
    paths = [path for path in (options.get("paths") or []) if path]
    if options.get("use_staged"):
        staged_paths, staged_error = _git_staged_paths(root)
        if staged_error:
            payload = {
                "schema_version": 1,
                "error": staged_error,
                "risk": "medium",
                "route": guru_contract.ROUTE_LITE_TASK,
                "needs_user_choice": True,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            return BLOCK
        if not paths:
            paths = staged_paths
    description = str(options.get("description") or "")
    commit_requested = bool(options.get("commit_requested"))
    requirements_clear = options.get("requirements_clear")
    coupling = str(options.get("coupling") or "unknown")
    reversible = options.get("reversible")
    verification_scope = str(options.get("verification_scope") or "unknown")
    prior_generation = options.get("prior_selection_generation")
    if isinstance(prior_generation, str) and prior_generation.strip():
        try:
            prior_generation = int(prior_generation)
        except ValueError:
            prior_generation = 0
    prior_route = options.get("prior_route")
    first_write_started = bool(options.get("first_write_started"))
    if isinstance(previous, dict):
        execution_policy = previous.get("execution_policy")
        execution_policy = execution_policy if isinstance(execution_policy, dict) else {}
        stored_route = guru_contract.contract_route(previous)
        stored_generation = execution_policy.get("selection_generation")
        transition_problems = []
        if prior_route and prior_route != stored_route:
            transition_problems.append(
                f"prior route {prior_route!r} conflicts with existing contract route {stored_route!r}"
            )
        if prior_generation is not None and prior_generation != stored_generation:
            transition_problems.append(
                "prior selection generation conflicts with existing contract generation "
                f"{stored_generation!r}"
            )
        if transition_problems:
            print(json.dumps({
                "schema_version": 1,
                "blocking_reasons": transition_problems,
                "contract_written": False,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return BLOCK
        prior_route = stored_route
        prior_generation = stored_generation
        first_write_started = first_write_started or _task_status(task_dir) in {
            "in_progress", "completed",
        }
        for evidence_name in ("implementation-evidence.jsonl", "verification-evidence.jsonl"):
            evidence_path = os.path.join(task_dir, evidence_name)
            first_write_started = first_write_started or (
                os.path.isfile(evidence_path) and os.path.getsize(evidence_path) > 0
            )
        previous_scope = previous.get("scope")
        previous_scope = previous_scope if isinstance(previous_scope, dict) else {}
        allowed_paths = previous_scope.get("allowed_paths", [])
        if isinstance(allowed_paths, list) and allowed_paths:
            try:
                first_write_started = first_write_started or bool(
                    set(allowed_paths) & guru_risk.scan_paths(root)
                )
            except guru_risk.RiskScanError:
                pass
    assessment = guru_risk.assess_intake(
        description,
        paths,
        commit_requested=commit_requested,
        requirements_clear=requirements_clear,
        coupling=coupling,
        reversible=reversible,
        verification_scope=verification_scope,
    )
    try:
        selection = guru_delivery_policy.resolve_project_delivery_selection(
            guru_delivery_policy.IntakeRequest(
                description=description,
                affected_paths=tuple(paths),
                commit_requested=commit_requested,
                preferred_route=options.get("preferred_route"),
                requirements_clear=requirements_clear,
                coupling=coupling,
                reversible=reversible,
                verification_scope=verification_scope,
                prior_route=prior_route,
                prior_selection_generation=prior_generation,
                first_write_started=first_write_started,
            ),
            root,
            capability_report=guru_delivery_policy.managed_capability_report(),
        )
    except guru_delivery_policy.DeliveryPolicyError as exc:
        payload = {
            "schema_version": 1,
            "risk": guru_contract.normalize_risk(assessment.get("risk")),
            "recommended_route": guru_contract.normalize_route(assessment.get("route")),
            "blocking_reasons": [str(exc)],
            "contract_written": False,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return BLOCK
    route = selection.selected_route
    risk = selection.risk
    assessment = dict(assessment)
    assessment["route"] = route
    assessment["risk"] = risk
    assessment["recommended_contract"] = selection.recommended_route
    payload = {
        "schema_version": 1,
        "task_dir": _display_task_dir(task_dir, root) if task_dir else "",
        "input": {
            "description": description,
            "paths": paths,
            "commit_requested": commit_requested,
            "use_staged": bool(options.get("use_staged")),
        },
        "risk": risk,
        "route": route,
        "confidence": assessment.get("confidence"),
        "reasons": assessment.get("reasons") if isinstance(assessment.get("reasons"), list) else [],
        "risk_flags": assessment.get("risk_flags") if isinstance(assessment.get("risk_flags"), list) else [],
        "needs_user_choice": bool(assessment.get("needs_user_choice")),
        "recommended_contract": assessment.get("recommended_contract"),
        "recommended_route": selection.recommended_route,
        "selected_route": selection.selected_route,
        "selection_source": selection.selection_source,
        "selection_generation": selection.selection_generation,
        "scope_fingerprint": selection.scope_fingerprint,
        "brainstorm_required": selection.brainstorm_required,
        "evidence_cache_key": selection.evidence_cache_key,
        "evidence_reused": selection.evidence_reused,
        "planning_cost_ratio_percent": selection.planning_cost_ratio_percent,
        "task_needed": route != guru_contract.ROUTE_SMALL_INLINE,
        "commit_contract_required": route != guru_contract.ROUTE_SMALL_INLINE,
        "suggested_commands": _intake_suggested_commands(assessment, paths, task_dir, root),
        "contract_written": False,
    }
    if not options.get("write_contract"):
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return PASS
    if not task_dir:
        payload["blocking_reasons"] = ["--write-contract requires a task_dir for micro_task/lite_task/full_chain routes"]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return BLOCK
    contract, problems = _contract_for_intake(
        assessment,
        paths,
        created_by="intake",
        selection=selection,
    )
    if problems or not isinstance(contract, dict):
        payload["blocking_reasons"] = problems or ["cannot build intake contract"]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return BLOCK
    try:
        guru_contract.write_contract(task_dir, contract)
        _update_task_route_metadata(task_dir, route, risk, selection)
    except OSError as exc:
        payload["blocking_reasons"] = [f"write gate-contract.json failed: {exc}"]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return BLOCK
    payload["contract_written"] = True
    payload["written_path"] = _display_task_dir(guru_contract.contract_path(task_dir), root)
    payload["old_route"] = guru_contract.contract_route(previous) if isinstance(previous, dict) else None
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return PASS


def cmd_init_contract(task_dir_arg, options: dict) -> int:
    task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False)
    if not task_dir and task_dir_arg and os.path.isdir(task_dir_arg):
        task_dir = os.path.abspath(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:init-contract] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    previous, read_error = guru_contract.load_contract(task_dir)
    if read_error:
        sys.stderr.write(f"[guru-gate:init-contract] existing contract unreadable: {read_error}\n")
        return BLOCK

    route = str(options.get("route") or "").strip()
    risk = str(options.get("risk") or "").strip()
    problems = []
    risk_problem = guru_contract.raw_risk_problem(risk)
    if risk_problem:
        problems.append(risk_problem)

    contract = guru_contract.default_contract(
        route,
        risk,
        created_by=str(options.get("created_by") or "init-contract"),
    )
    scope = contract.setdefault("scope", {})
    scope["allowed_paths"] = options.get("allowed_paths") or []
    scope["forbidden_path_patterns"] = options.get("forbidden_patterns") or []
    max_files = _parse_positive_int(options.get("max_files"), "max-files", problems)
    if max_files is not None:
        scope["max_files"] = max_files
    confidence = _parse_confidence(options.get("confidence"), problems)
    assessment = contract.setdefault("assessment", {})
    assessment["confidence"] = confidence
    assessment["reasons"] = options.get("reasons") or []
    assessment["risk_flags"] = options.get("risk_flags") or []
    recommended_route = guru_contract.normalize_route(options.get("recommended_route"))
    if not recommended_route:
        recommended_route = guru_contract.recommended_route_for_risk(risk)
    assessment["recommended_route"] = recommended_route
    selected_route = guru_contract.normalize_route(route)
    user_quote = str(options.get("user_override_quote") or "").strip()
    selected_by = str(options.get("selected_by") or "").strip() or ("user" if user_quote else "system")
    risk_acknowledged = _contract_bool(options.get("risk_acknowledged"))
    selection_source = "user_override" if user_quote or risk_acknowledged or selected_by == "user" else "recommended"
    contract["route_selection"] = {
        "selected_route": selected_route,
        "source": selection_source,
        "recommended_route": recommended_route,
        "risk_acknowledged": risk_acknowledged,
        "user_quote": user_quote,
        "selected_by": selected_by,
        "selected_at": _now_iso(),
    }

    selection = None
    if selected_route:
        allowed_paths = tuple(scope.get("allowed_paths") or [])
        if selected_route == guru_contract.ROUTE_FULL_CHAIN:
            selection_description = "change workflow gate runtime"
            requirements_clear = False
            coupling = "cross_layer"
            reversible = False
            verification_scope = "broad"
        elif selected_route == guru_contract.ROUTE_LITE_TASK:
            selection_description = "change local behavior"
            requirements_clear = False
            coupling = "unknown"
            reversible = None
            verification_scope = "unknown"
        else:
            selection_description = "change local behavior"
            requirements_clear = True
            coupling = "local"
            reversible = True
            verification_scope = "focused"
        previous_route = guru_contract.contract_route(previous) if isinstance(previous, dict) else None
        previous_execution = previous.get("execution_policy") if isinstance(previous, dict) else None
        previous_generation = (
            previous_execution.get("selection_generation")
            if isinstance(previous_execution, dict)
            else None
        )
        request_kwargs = {
            "description": selection_description,
            "affected_paths": allowed_paths,
            "requirements_clear": requirements_clear,
            "coupling": coupling,
            "reversible": reversible,
            "verification_scope": verification_scope,
            "max_files": max_files,
            "prior_route": previous_route,
            "prior_selection_generation": previous_generation,
            "first_write_started": bool(previous_route and _task_status(task_dir) == "in_progress"),
        }
        try:
            selection = guru_delivery_policy.resolve_delivery_selection(
                guru_delivery_policy.IntakeRequest(**request_kwargs),
                capability_report=guru_delivery_policy.managed_capability_report(),
            )
            if selection.selected_route != selected_route:
                selection = guru_delivery_policy.resolve_delivery_selection(
                    guru_delivery_policy.IntakeRequest(
                        **request_kwargs,
                        preferred_route=selected_route,
                    ),
                    capability_report=guru_delivery_policy.managed_capability_report(),
                )
            contract.update(guru_delivery_policy.selection_to_contract_patch(selection))
            execution_policy = contract["execution_policy"]
            execution_policy["recommended_route"] = recommended_route
            execution_policy["selection_source"] = selection_source
            contract["route_selection"].update({
                "selection_generation": execution_policy["selection_generation"],
                "scope_fingerprint": execution_policy["scope_fingerprint"],
            })
        except guru_delivery_policy.DeliveryPolicyError as exc:
            problems.append(str(exc))

    problems.extend(guru_contract.validate_contract(contract))
    if problems:
        sys.stderr.write("[guru-gate:init-contract] 拒绝写入 gate-contract.json：\n")
        for problem in problems:
            sys.stderr.write(f"  - {problem}\n")
        return BLOCK

    old_route = guru_contract.contract_route(previous) if isinstance(previous, dict) else ""
    guru_contract.write_contract(task_dir, contract)
    _update_task_route_metadata(task_dir, contract["route"], contract["risk"], selection)
    summary = {
        "schema_version": 1,
        "task_dir": _display_task_dir(task_dir, _repo_root()),
        "written_path": _display_task_dir(guru_contract.contract_path(task_dir), _repo_root()),
        "old_route": old_route or None,
        "new_route": contract["route"],
        "recommended_route": guru_contract.contract_recommended_route(contract) or None,
        "route_selection_source": contract.get("route_selection", {}).get("source"),
        "risk": contract["risk"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return PASS


def _parse_degradation_check(raw: str, problems: list) -> dict | None:
    parts = raw.split(":", 2)
    if len(parts) < 2:
        problems.append("--check must use name:status[:evidence]")
        return None
    name = parts[0].strip()
    status = parts[1].strip()
    evidence = parts[2].strip() if len(parts) > 2 else ""
    if not name or not status:
        problems.append("--check must include non-empty name and status")
        return None
    check = {"name": name, "status": status}
    if evidence:
        check["evidence"] = evidence
    return check


def _default_allowed_by(contract: dict, gate: str) -> str:
    rows = contract.get("allowed_degradations", []) if isinstance(contract, dict) else []
    if not isinstance(rows, list):
        return ""
    for idx, row in enumerate(rows):
        if isinstance(row, dict) and row.get("gate") == gate:
            return f"gate-contract.json#/allowed_degradations/{idx}"
    return ""


def cmd_record_degradation(task_dir_arg, options: dict) -> int:
    task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False) if task_dir_arg else None
    if not task_dir and task_dir_arg and os.path.isdir(task_dir_arg):
        task_dir = os.path.abspath(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:record-degradation] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    contract, read_error = guru_contract.load_contract(task_dir)
    if read_error:
        sys.stderr.write(f"[guru-gate:record-degradation] {read_error}\n")
        return BLOCK
    contract_problems = guru_contract.validate_contract(contract)
    if contract_problems:
        sys.stderr.write("[guru-gate:record-degradation] 当前 gate-contract.json 无效：\n")
        for problem in contract_problems:
            sys.stderr.write(f"  - {problem}\n")
        return BLOCK
    problems = []
    gate = str(options.get("gate") or "").strip()
    reason = str(options.get("reason") or "").strip()
    command = str(options.get("command") or "").strip()
    if not gate:
        problems.append("--gate is required")
    if not reason:
        problems.append("--reason is required")
    if not command:
        problems.append("--command is required")
    checks = []
    for raw in options.get("checks") or []:
        check = _parse_degradation_check(raw, problems)
        if check:
            checks.append(check)
    row = {
        "schema_version": guru_contract.SCHEMA_VERSION,
        "gate": gate,
        "reason": reason,
        "command": command,
        "stderr_excerpt": str(options.get("stderr_excerpt") or ""),
        "allowed_by": str(options.get("allowed_by") or _default_allowed_by(contract, gate)),
        "compensating_checks": checks,
        "created_by": str(options.get("created_by") or "agent"),
    }
    rows, degradation_error = guru_contract.read_degradations(task_dir)
    if degradation_error:
        problems.append(degradation_error)
    if not problems:
        problems.extend(guru_contract.validate_degradations(contract, rows + [row]))
    if problems:
        sys.stderr.write("[guru-gate:record-degradation] 拒绝追加 gate-degradations.jsonl：\n")
        for problem in problems:
            sys.stderr.write(f"  - {problem}\n")
        return BLOCK
    try:
        guru_contract.append_degradation(task_dir, row)
    except guru_contract.ContractError as exc:
        sys.stderr.write(f"[guru-gate:record-degradation] {exc}\n")
        return BLOCK
    summary = {
        "schema_version": 1,
        "task_dir": _display_task_dir(task_dir, _repo_root()),
        "written_path": _display_task_dir(guru_contract.degradations_path(task_dir), _repo_root()),
        "gate": gate,
        "compensating_checks": [check.get("name") for check in checks],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return PASS


def _implementation_packet_preflight_problem(task_dir: str) -> str:
    required, reason = guru_risk.full_chain_packet_required(task_dir)
    if not required:
        return ""
    packets = guru_review_record.list_packets(task_dir)
    if not packets:
        return f"PACKET_REQUIRED_BEFORE_IMPLEMENT: {reason}; create slice-packets/<unit>.json or choose/update the selected route with user override audit"
    return ""


def _dirty_scope_for_packet(root: str, packet: dict) -> tuple[str, list, str]:
    try:
        dirty = guru_risk.scan_dirty_paths(root)
    except guru_risk.RiskScanError as exc:
        return "unknown", [], f"scan failed: {exc}"
    code_dirty = [p for p in dirty if guru_risk._is_scannable(p)]
    targets = packet.get("target_paths", [])
    unrelated = set(packet.get("dirty_state", {}).get("unrelated", []))
    out_of_scope = sorted(
        p for p in code_dirty
        if p not in unrelated and not _path_in_targets(p, targets)
    )
    if out_of_scope:
        return "invalid", out_of_scope, "dirty paths outside target_paths and dirty_state.unrelated"
    return ("isolated" if code_dirty else "clean"), [], ""


def _slice_plan_dispatch_advisory(task_dir: str) -> dict:
    mode = _config_value(("codex", "dispatch_mode"), task_dir).strip().lower() or "inline"
    blockers = []
    if mode not in {"inline", "sub-agent", "channel"}:
        blockers.append(f"DISPATCH_MODE_INVALID:{mode}")
        mode = "inline"
    return {
        "configured_dispatch_mode": mode,
        "selected_backend": mode,
        "channel_is_default": mode == "channel",
        "slice_plan_read_only": True,
        "sub_agent_requires_active_task_prelude": mode == "sub-agent",
        "advisory_blockers": blockers,
    }


def _slice_plan_depends_on(packet: dict) -> tuple[list, list]:
    raw = packet.get("depends_on", [])
    if raw is None:
        return [], []
    if not isinstance(raw, list) or not all(isinstance(dep, str) and dep.strip() for dep in raw):
        return [], ["DEPENDENCY_METADATA_INVALID"]
    return list(raw), []


def _slice_plan_resource_locks(checks: list) -> list:
    locks = []
    for raw_check in checks:
        command = str(raw_check).strip().lower()
        if not command:
            continue
        if "build_runner" in command:
            locks.append("dart_build_runner")
        if "flutter " in f" {command}" or command.startswith("fvm flutter "):
            locks.append("flutter_tooling")
        if (
            " dart test" in f" {command}"
            or " dart analyze" in f" {command}"
            or command.startswith("dart run ")
        ):
            locks.append("dart_tooling")
        if any(token in f" {command} " for token in (" pnpm ", " npm ", " yarn ", " bun ")):
            locks.append("node_package_manager")
        if "gradle" in command or "gradlew" in command:
            locks.append("gradle")
        if "xcodebuild" in command:
            locks.append("xcodebuild")
    return _dedupe_strings(locks)


def _slice_plan_target_key(path: str) -> str:
    value = path.replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    value = value.strip("/")
    return value or "."


def _slice_plan_targets_overlap(left: str, right: str) -> bool:
    left_key = _slice_plan_target_key(left)
    right_key = _slice_plan_target_key(right)
    if left_key == "." or right_key == ".":
        return True
    return (
        left_key == right_key
        or left_key.startswith(f"{right_key}/")
        or right_key.startswith(f"{left_key}/")
    )


def _slice_plan_first_overlap(left_targets: list, right_targets: list) -> str:
    for left in left_targets:
        if not isinstance(left, str):
            continue
        for right in right_targets:
            if not isinstance(right, str):
                continue
            if _slice_plan_targets_overlap(left, right):
                return f"{left}<->{right}"
    return ""


def _slice_plan_target_conflicts(slices: list) -> dict:
    conflicts = {entry["slice_id"]: [] for entry in slices}
    for idx, left in enumerate(slices):
        for right in slices[idx + 1:]:
            overlap = _slice_plan_first_overlap(left.get("target_paths", []), right.get("target_paths", []))
            if not overlap:
                continue
            left_id = left["slice_id"]
            right_id = right["slice_id"]
            conflicts[left_id].append(f"TARGET_PATH_OVERLAP:{right_id}:{overlap}")
            conflicts[right_id].append(f"TARGET_PATH_OVERLAP:{left_id}:{overlap}")
    return conflicts


def _slice_plan_parallel_groups(slices: list) -> list:
    groups = []
    writer_slices = [
        entry for entry in slices
        if entry.get("parallel_safe") and entry.get("parallel_mode") == "writer"
    ]
    serial_slices = [
        entry for entry in slices
        if not entry.get("parallel_safe") or entry.get("parallel_mode") == "serial"
    ]
    if writer_slices:
        group_id = f"g{len(groups) + 1}"
        for entry in writer_slices:
            entry["parallel_group"] = group_id
        groups.append({
            "group_id": group_id,
            "mode": "writer",
            "slice_ids": [entry["slice_id"] for entry in writer_slices],
            "max_parallel": len(writer_slices),
            "blocking_reasons": [],
            "recommended_commands": [
                entry["recommended_commands"]["implement_check"]
                for entry in writer_slices
            ],
        })
    if serial_slices:
        group_id = f"g{len(groups) + 1}"
        blocking_reasons = []
        for entry in serial_slices:
            entry["parallel_group"] = group_id
            blocking_reasons.extend(entry.get("parallel_blockers", []))
        groups.append({
            "group_id": group_id,
            "mode": "serial",
            "slice_ids": [entry["slice_id"] for entry in serial_slices],
            "max_parallel": 1,
            "blocking_reasons": _dedupe_strings(blocking_reasons),
            "recommended_commands": [
                entry["recommended_commands"]["implement_check"]
                for entry in serial_slices
            ],
        })
    return groups


def _slice_plan_payload(task_dir_arg) -> dict:
    root = _repo_root()
    task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False)
    plan = {
        "schema_version": 2,
        "task_dir": _display_task_dir(task_dir, root) if task_dir else "",
        "route": "",
        "risk": "",
        "packet_required": False,
        "packet_required_reason": "",
        "slices": [],
        "parallel_groups": [],
        "dispatch_advisory": {},
        "blocking_reasons": [],
    }
    if not task_dir:
        plan["blocking_reasons"].append("TASK_DIR_NOT_FOUND")
        return plan

    route, risk, source = guru_risk.task_route_and_risk(task_dir)
    required, required_reason = guru_risk.full_chain_packet_required(task_dir)
    plan["route"] = route or guru_contract.ROUTE_FULL_CHAIN
    plan["risk"] = risk
    plan["packet_required"] = required
    plan["packet_required_reason"] = required_reason
    plan["dispatch_advisory"] = _slice_plan_dispatch_advisory(task_dir)
    packets = guru_review_record.list_packets(task_dir)
    if required and not packets:
        plan["blocking_reasons"].append("PACKET_REQUIRED_BEFORE_IMPLEMENT")
    for unit_id in packets:
        try:
            packet = guru_review_record.load_packet(task_dir, unit_id)
        except guru_review_record.ReviewRecordError as exc:
            plan["blocking_reasons"].append(f"PACKET_INVALID:{unit_id}:{exc}")
            continue
        dirty_status, out_of_scope, dirty_reason = _dirty_scope_for_packet(root, packet)
        if dirty_status == "invalid":
            plan["blocking_reasons"].append(f"SCOPE_INVALID:{unit_id}")
        provider = packet.get("semantic_review_provider", {})
        checks = packet.get("deterministic_checks", [])
        depends_on, dependency_blockers = _slice_plan_depends_on(packet)
        resource_locks = _slice_plan_resource_locks(checks if isinstance(checks, list) else [])
        display_task_dir = _display_task_dir(task_dir, root)
        implement_command = (
            f"python3 .trellis/scripts/guru/guru_supervise.py implement-check "
            f"{shlex.quote(display_task_dir)} --slice {shlex.quote(unit_id)}"
        )
        review_command = (
            f"python3 .trellis/scripts/guru/guru_supervise.py implementation-review "
            f"{shlex.quote(display_task_dir)} --slice {shlex.quote(unit_id)}"
        )
        review_staged_command = f"{review_command} --staged"
        parallel_blockers = list(dependency_blockers)
        parallel_blockers.extend(f"DEPENDS_ON:{dep}" for dep in depends_on)
        parallel_blockers.extend(f"RESOURCE_LOCK:{lock}" for lock in resource_locks)
        if dirty_status == "invalid":
            parallel_blockers.append("SCOPE_INVALID")
        plan["slices"].append({
            "slice_id": unit_id,
            "target_paths": packet.get("target_paths", []),
            "risk": packet.get("risk", "unknown"),
            "risk_reasons": packet.get("risk_reasons", []),
            "deterministic_checks": [
                check.get("command") if isinstance(check, dict) else check
                for check in checks
            ],
            "semantic_review_provider": provider if isinstance(provider, dict) else {},
            "dirty_scope": dirty_status,
            "dirty_out_of_scope": out_of_scope,
            "dirty_reason": dirty_reason,
            "depends_on": depends_on,
            "resource_locks": resource_locks,
            "parallel_safe": False,
            "parallel_mode": "serial",
            "parallel_group": "",
            "parallel_blockers": parallel_blockers,
            "recommended_command": implement_command,
            "recommended_commands": {
                "implement_check": implement_command,
                "implementation_review": review_command,
                "implementation_review_staged": review_staged_command,
            },
        })
    known_slice_ids = {entry["slice_id"] for entry in plan["slices"]}
    for entry in plan["slices"]:
        unknown_dependencies = [
            dep for dep in entry.get("depends_on", [])
            if dep not in known_slice_ids
        ]
        entry["parallel_blockers"].extend(
            f"DEPENDENCY_UNKNOWN:{dep}" for dep in unknown_dependencies
        )
    conflicts = _slice_plan_target_conflicts(plan["slices"])
    overlap_found = False
    for entry in plan["slices"]:
        entry["parallel_blockers"].extend(conflicts.get(entry["slice_id"], []))
        entry["parallel_blockers"] = _dedupe_strings(entry["parallel_blockers"])
        if any(reason.startswith("TARGET_PATH_OVERLAP:") for reason in entry["parallel_blockers"]):
            overlap_found = True
        entry["parallel_safe"] = not entry["parallel_blockers"]
        entry["parallel_mode"] = "writer" if entry["parallel_safe"] else "serial"
    plan["parallel_groups"] = _slice_plan_parallel_groups(plan["slices"])
    if len(plan["slices"]) > 1:
        plan["blocking_reasons"].append("PACKET_AMBIGUOUS_WITHOUT_SLICE")
    if overlap_found:
        plan["blocking_reasons"].append("PARALLEL_TARGET_PATH_OVERLAP")
    plan["blocking_reasons"].extend(plan["dispatch_advisory"].get("advisory_blockers", []))
    plan["source"] = source
    plan["blocking_reasons"] = _dedupe_strings(plan["blocking_reasons"])
    return plan


def cmd_slice_plan(task_dir_arg) -> int:
    print(json.dumps(_slice_plan_payload(task_dir_arg), ensure_ascii=False, indent=2, sort_keys=True))
    return PASS


def _commit_plan_split_scope(staged_paths: list, task_dir: str, root: str) -> tuple[list, list]:
    artifact_paths = [
        path for path in staged_paths
        if guru_contract.is_task_artifact_path(path, task_dir or "", root)
    ]
    code_paths = [path for path in staged_paths if path not in artifact_paths]
    return artifact_paths, code_paths


def _commit_plan_split_required(staged_paths: list, task_dir: str, root: str) -> bool:
    artifact_paths, code_paths = _commit_plan_split_scope(staged_paths, task_dir, root)
    return bool(artifact_paths and code_paths)


def _direct_commit_stage_paths(staged_paths: list, root: str) -> tuple[list, list]:
    artifact_paths = [path for path in staged_paths if guru_contract.is_task_artifact_path(path, "", root)]
    code_paths = [path for path in staged_paths if path not in artifact_paths]
    forbidden = list(artifact_paths)
    high_risk_paths = set(guru_contract.high_risk_path_signals(code_paths))
    if guru_risk.has_cross_layer_or_storage(code_paths):
        high_risk_paths.update(code_paths)
    forbidden.extend(path for path in code_paths if path in high_risk_paths)
    if len(code_paths) > 3:
        forbidden.extend(code_paths[3:])
    forbidden = _dedupe_strings(forbidden)
    allowed = [path for path in code_paths if path not in forbidden]
    return allowed, forbidden


def _micro_recovery_commands(staged_paths: list, root: str) -> list:
    allowed, _forbidden = _direct_commit_stage_paths(staged_paths, root)
    max_files = len(allowed) if allowed else len(staged_paths)
    path_args = " ".join(f"--allowed-path {shlex.quote(path)}" for path in allowed)
    if path_args:
        path_args = " " + path_args
    return [
        'python3 .trellis/scripts/task.py create "<short task title>" --priority P2',
        (
            "python3 .trellis/scripts/guru/guru_gate.py init-contract <new-task-dir> "
            f"--route micro_task --risk low{path_args} --max-files {max_files}"
        ),
        "rerun commit-plan/check-commit with the new micro_task task_dir",
    ]


def _post_implementation_recovery_reason(prefix: str = "") -> str:
    base = (
        "post-implementation intake recovery required: scoped low-risk staged changes "
        "need a micro_task gate-contract before commit; do not backfill full PRD/"
        "overview/detail gates after implementation"
    )
    return f"{prefix}: {base}" if prefix else base


def _contract_commit_stage_paths(contract: dict, staged_paths: list, task_dir: str, root: str) -> tuple[list, list]:
    scope = contract.get("scope", {}) if isinstance(contract, dict) else {}
    if not isinstance(scope, dict):
        scope = {}
    raw_allowed_scope = scope.get("allowed_paths")
    allowed_scope: list = raw_allowed_scope if isinstance(raw_allowed_scope, list) else []
    raw_forbidden_patterns = scope.get("forbidden_path_patterns")
    forbidden_patterns: list = raw_forbidden_patterns if isinstance(raw_forbidden_patterns, list) else []
    max_files = scope.get("max_files")
    artifact_paths = [path for path in staged_paths if guru_contract.is_task_artifact_path(path, task_dir, root)]
    code_paths = [path for path in staged_paths if path not in artifact_paths]
    forbidden = list(artifact_paths)
    forbidden.extend(path for path in code_paths if not guru_contract.path_in_scope(path, allowed_scope))
    for path in code_paths:
        normalized = path.replace("\\", "/").strip("/")
        if any(isinstance(pattern, str) and pattern and pattern in normalized for pattern in forbidden_patterns):
            forbidden.append(path)
    if isinstance(max_files, int) and max_files > 0 and len(staged_paths) > max_files:
        forbidden.extend(staged_paths[max_files:])
    route = guru_contract.contract_route(contract)
    if route and route != guru_contract.ROUTE_FULL_CHAIN:
        high_risk_paths = set(guru_contract.high_risk_path_signals(code_paths))
        if guru_risk.has_cross_layer_or_storage(code_paths):
            high_risk_paths.update(code_paths)
        forbidden.extend(path for path in code_paths if path in high_risk_paths)
    forbidden = _dedupe_strings(forbidden)
    allowed = [path for path in code_paths if path not in forbidden]
    return allowed, forbidden


def _review_commit_stage_paths(record, staged_paths: list, task_dir: str, root: str) -> tuple[list, list]:
    task_artifacts = [
        path for path in staged_paths
        if guru_contract.is_task_artifact_path(path, task_dir, root)
    ]
    code_paths = [path for path in staged_paths if path not in task_artifacts]
    target_paths = record.get("target_paths") if isinstance(record, dict) else None
    if not isinstance(target_paths, list) or not target_paths:
        return [], staged_paths
    forbidden = list(task_artifacts)
    forbidden.extend(path for path in code_paths if not _path_in_targets(path, target_paths))
    forbidden = _dedupe_strings(forbidden)
    allowed = [path for path in code_paths if path not in forbidden]
    return allowed, forbidden


def _implementation_review_records(path: str) -> tuple[list, str]:
    records = []
    if not os.path.isfile(path):
        return records, "implementation review record missing"
    try:
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    return [], f"implementation review record line {lineno} invalid JSON: {exc}"
                if isinstance(row, dict):
                    records.append(row)
    except OSError as exc:
        return [], f"cannot read implementation review record: {exc}"
    if not records:
        return records, "implementation review record empty"
    return records, ""


def _remember_ignored_review(coverage: dict, review_id: str, reason: str) -> None:
    ignored = coverage.setdefault("ignored_reviews", [])
    if len(ignored) < 20:
        ignored.append({"review_id": review_id, "reason": reason})


def _review_record_targets_staged_paths(record: dict, code_paths: list) -> bool:
    target_paths = record.get("target_paths") if isinstance(record, dict) else None
    if not isinstance(target_paths, list) or not target_paths:
        return False
    return any(_path_in_targets(path, target_paths) for path in code_paths)


def _remember_ignored_covering_review(coverage: dict, review_id: str) -> None:
    coverage["ignored_covering_review_ids"] = _dedupe_strings(
        coverage.get("ignored_covering_review_ids", []) + [review_id]
    )


def _remember_ignored_covering_paths(coverage: dict, record: dict, code_paths: list) -> None:
    target_paths = record.get("target_paths") if isinstance(record, dict) else None
    if not isinstance(target_paths, list) or not target_paths:
        return
    covered = [path for path in code_paths if _path_in_targets(path, target_paths)]
    coverage["ignored_covering_staged_paths"] = _dedupe_strings(
        coverage.get("ignored_covering_staged_paths", []) + covered
    )


def _packet_slice_candidates_by_path(task_dir: str, paths: list) -> dict:
    candidates = {path: [] for path in paths}
    if not paths:
        return candidates
    for unit_id in guru_review_record.list_packets(task_dir):
        try:
            packet = guru_review_record.load_packet(task_dir, unit_id)
        except guru_review_record.ReviewRecordError:
            continue
        target_paths = packet.get("target_paths", [])
        for path in paths:
            if _path_in_targets(path, target_paths):
                candidates[path].append(unit_id)
    return {
        path: sorted(set(slice_ids))
        for path, slice_ids in candidates.items()
    }


def _missing_review_commands_for_paths(task_dir: str, root: str, uncovered_paths: list) -> list:
    slice_candidates = _packet_slice_candidates_by_path(task_dir, uncovered_paths)
    slice_ids = []
    needs_staged_review = False
    for path in uncovered_paths:
        candidates = slice_candidates.get(path, [])
        if candidates:
            slice_ids.append(candidates[0])
        else:
            needs_staged_review = True
    commands = [
        _implementation_review_slice_command(task_dir, root, slice_id)
        for slice_id in sorted(set(slice_ids))
    ]
    if needs_staged_review:
        commands.append(_implementation_review_command(task_dir, root))
    return commands


def _implementation_review_coverage(review_path: str, staged_paths: list, task_dir: str, root: str) -> tuple[dict, str, bool]:
    coverage = _empty_review_coverage()
    task_artifact_paths = [
        path for path in staged_paths
        if _is_task_artifact_path(path, task_dir, root)
    ]
    code_paths = [
        path for path in staged_paths
        if path not in task_artifact_paths
    ]
    coverage["forbidden_staged_paths"] = task_artifact_paths
    if not code_paths:
        return (
            coverage,
            "staged changes contain only task artifacts/workspace artifacts; this is not a Guru implementation commit",
            False,
        )
    records, read_error = _implementation_review_records(review_path)
    coverage["uncovered_staged_paths"] = code_paths
    coverage["missing_review_commands"] = _missing_review_commands_for_paths(task_dir, root, code_paths)
    if read_error:
        return coverage, read_error, True

    covering_reviews = {path: [] for path in code_paths}
    clean_review_ids = []
    targeted_review_problem = ""
    for index, record in enumerate(records, 1):
        coverage["records_considered"] += 1
        review_id = _implementation_review_record_id(record, f"record:{index}")
        problem = _implementation_review_base_problem(record, f"implementation review {review_id}")
        if problem:
            _remember_ignored_review(coverage, review_id, problem)
            if _review_record_targets_staged_paths(record, code_paths):
                _remember_ignored_covering_review(coverage, review_id)
                _remember_ignored_covering_paths(coverage, record, code_paths)
                if not targeted_review_problem:
                    targeted_review_problem = problem
            continue
        target_paths = record.get("target_paths", [])
        reviewed_digest = record.get("reviewed_target_digest")
        try:
            staged_digest = guru_review_record.target_snapshot_digest(root, target_paths, "index")
        except guru_review_record.ReviewRecordError as exc:
            reason = f"cannot compute staged target digest: {exc}"
            _remember_ignored_review(coverage, review_id, reason)
            if _review_record_targets_staged_paths(record, code_paths):
                _remember_ignored_covering_review(coverage, review_id)
                _remember_ignored_covering_paths(coverage, record, code_paths)
                if not targeted_review_problem:
                    targeted_review_problem = reason
            continue
        if staged_digest != reviewed_digest:
            reason = (
                f"staged target content differs from implementation review {review_id}; "
                "rerun implementation-review --staged"
            )
            _remember_ignored_review(coverage, review_id, reason)
            if _review_record_targets_staged_paths(record, code_paths):
                _remember_ignored_covering_review(coverage, review_id)
                _remember_ignored_covering_paths(coverage, record, code_paths)
                if not targeted_review_problem:
                    targeted_review_problem = reason
            continue
        coverage["records_current_clean"] += 1
        clean_review_ids.append(review_id)
        for path in code_paths:
            if _path_in_targets(path, target_paths):
                covering_reviews[path].append(review_id)

    covered_paths = [
        path for path in code_paths
        if covering_reviews[path]
    ]
    uncovered_paths = [
        path for path in code_paths
        if not covering_reviews[path]
    ]
    coverage["covered_staged_paths"] = covered_paths
    coverage["uncovered_staged_paths"] = uncovered_paths
    coverage["covering_reviews"] = {
        path: _dedupe_strings(review_ids)
        for path, review_ids in covering_reviews.items()
        if review_ids
    }
    coverage["covering_review_ids"] = _dedupe_strings(clean_review_ids)
    coverage["missing_review_commands"] = _missing_review_commands_for_paths(task_dir, root, uncovered_paths)
    if uncovered_paths:
        ignored_covering_paths = set(coverage.get("ignored_covering_staged_paths", []))
        if targeted_review_problem and all(path in ignored_covering_paths for path in uncovered_paths):
            return coverage, targeted_review_problem, True
        return (
            coverage,
            "staged implementation paths lack current clean implementation review coverage: "
            + ", ".join(uncovered_paths[:5]),
            True,
        )
    return coverage, "", False


def _lite_deterministic_evidence_problem(
    task_dir: str,
    contract: dict,
    staged_paths: list,
    root: str,
) -> str:
    path = os.path.join(task_dir, "verification-evidence.jsonl")
    if not os.path.isfile(path):
        return "Lite deterministic verification evidence missing: verification-evidence.jsonl"
    latest = None
    try:
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    return f"Lite verification evidence line {lineno} invalid JSON: {exc}"
                if isinstance(row, dict) and row.get("kind") == "deterministic_final":
                    latest = row
    except OSError as exc:
        return f"cannot read Lite verification evidence: {exc}"
    if not isinstance(latest, dict):
        return "Lite verification evidence has no deterministic_final record"
    if str(latest.get("status", "")).strip().lower() != "passed":
        return "Lite latest deterministic_final evidence is not passed"

    execution_policy = contract.get("execution_policy")
    if not isinstance(execution_policy, dict):
        return "Lite contract execution_policy missing"
    if latest.get("selection_generation") != execution_policy.get("selection_generation"):
        return "Lite deterministic evidence selection_generation is stale"
    if latest.get("scope_fingerprint") != execution_policy.get("scope_fingerprint"):
        return "Lite deterministic evidence scope_fingerprint is stale"
    if str(latest.get("docs_code_test_consistency", "")).strip().lower() != "passed":
        return "Lite deterministic evidence lacks passed docs/code/tests consistency"
    if str(latest.get("spec_sync", "")).strip().lower() not in {"passed", "not_required"}:
        return "Lite deterministic evidence lacks passed/not_required Spec sync"

    code_paths = [
        path
        for path in staged_paths
        if not guru_contract.is_task_artifact_path(path, task_dir, root)
    ]
    target_paths = latest.get("target_paths")
    if not isinstance(target_paths, list) or sorted(target_paths) != sorted(code_paths):
        return "Lite deterministic evidence target_paths do not match the exact staged implementation scope"
    target_digest = latest.get("target_digest")
    if not isinstance(target_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", target_digest):
        return "Lite deterministic evidence target_digest must be sha256"
    try:
        current_digest = guru_review_record.target_snapshot_digest(root, target_paths, "index")
    except guru_review_record.ReviewRecordError as exc:
        return f"cannot compute Lite staged target digest: {exc}"
    if current_digest != target_digest:
        return "Lite deterministic evidence is stale for the exact staged target digest"
    return ""


def _git_output(root: str, args: list[str], label: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise guru_review_record.ReviewRecordError(f"{label}:{exc}") from exc
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise guru_review_record.ReviewRecordError(f"{label}:{message}")
    return result.stdout.strip()


def _slice_review_policy(task_dir: str, packet: dict, record: dict) -> dict:
    present, configured = _config_value_with_presence(
        ("guru", "supervision", "high_risk_review_provider_policy"),
        task_dir,
    )
    configured = configured.strip().lower()
    if not present:
        configured = "current"
    if configured not in guru_review_record.HIGH_RISK_REVIEW_PROVIDER_POLICIES:
        raise guru_review_record.ReviewRecordError(
            f"invalid high-risk review provider policy:{configured!r}"
        )
    source = record.get("provider_override_source")
    if packet.get("risk") in {"high", "critical"} and source == "config_policy":
        if record.get("high_risk_review_provider_policy") != configured:
            raise guru_review_record.ReviewRecordError(
                "implementation review provider policy is stale"
            )
    return {
        "packet_risk": packet.get("risk"),
        "packet_risk_reasons": packet.get("risk_reasons"),
        "packet_semantic_review_provider": packet.get("semantic_review_provider"),
        "configured_high_risk_review_provider_policy": configured,
        "provider_override_source": source,
        "same_provider_user_quote": record.get("same_provider_user_quote"),
        "review_target_kind": record.get("review_target_kind"),
        "implement_provider": record.get("implement_provider"),
        "check_provider": record.get("check_provider"),
        "review_provider": record.get("review_provider"),
    }


def _slice_component_digests(
    task_dir: str,
    packet: dict,
    record: dict,
    *,
    supervisor_digest: str | None = None,
) -> dict:
    supervisor_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "guru_supervise.py",
    )
    policy = _slice_review_policy(task_dir, packet, record)
    components = guru_review_record.review_evidence_components(
        task_dir,
        packet,
        record,
        supervisor_path=supervisor_path,
        supervisor_digest=supervisor_digest,
    )
    if not packet.get("aggregate_slice_ids"):
        components["review_policy_digest"] = guru_review_record.review_policy_digest(
            policy
        )
    return components


def _slice_contract_problem(
    task_dir: str,
    root: str,
    staged_paths: list[str],
) -> str:
    if _task_status(task_dir) != "in_progress":
        return (
            "slice commit lifecycle requires task.json.status=in_progress; "
            f"got {_task_status(task_dir)!r}"
        )
    contract, error = guru_contract.load_contract(task_dir)
    if error or not isinstance(contract, dict):
        return error or "gate contract missing"
    problems = guru_contract.validate_commit_contract(
        contract,
        staged_paths,
        task_dir,
        root,
    )
    return "; ".join(problems[:5])


def _slice_review_record(
    task_dir: str,
    slice_id: str,
    review_run_id: str | None = None,
) -> tuple[dict | None, str]:
    path = os.path.join(task_dir, "review-records", "implementation-reviews.jsonl")
    records, error = _implementation_review_records(path)
    if error:
        return None, error
    matches = [
        record
        for record in records
        if record.get("slice_id") == slice_id
        and (review_run_id is None or record.get("run_id") == review_run_id)
    ]
    if not matches:
        suffix = f" run_id={review_run_id}" if review_run_id else ""
        return None, f"official implementation review missing for slice {slice_id}{suffix}"
    return matches[-1], ""


def _receipt_review_record(
    task_dir: str,
    slice_id: str,
    review_run_id: str,
) -> tuple[dict | None, str, bool]:
    path = os.path.join(task_dir, "review-records", "implementation-reviews.jsonl")
    records, records_error = _implementation_review_records(path)
    if records_error:
        return None, records_error, False
    matches = [
        record
        for record in records
        if record.get("run_id") == review_run_id
        and record.get("supplemental") is not True
    ]
    if not matches:
        return (
            None,
            f"official implementation review missing for run_id={review_run_id}",
            False,
        )
    if len(matches) != 1:
        return (
            None,
            "implementation review run_id ownership ambiguous: "
            f"run_id={review_run_id} official_rows={len(matches)}",
            False,
        )
    review = matches[0]
    if (
        review.get("slice_id") == slice_id
        and review.get("review_target") == f"slice:{slice_id}"
    ):
        return review, "", False
    aggregate_ids = review.get("aggregate_slice_ids")
    if (
        isinstance(aggregate_ids, list)
        and slice_id in aggregate_ids
        and review.get("review_target") == "aggregate:" + ",".join(aggregate_ids)
    ):
        return review, "", True
    return (
        None,
        f"implementation review run_id={review_run_id} does not bind slice {slice_id}",
        False,
    )


def _slice_review_problem(
    task_dir: str,
    root: str,
    packet: dict,
    record: dict,
) -> str:
    slice_id = packet["slice_id"]
    problem = _implementation_review_base_problem(
        record,
        f"slice {slice_id} implementation review",
    )
    if problem:
        return problem
    if record.get("slice_id") != slice_id or record.get("review_target") != f"slice:{slice_id}":
        return f"implementation review does not bind slice {slice_id}"
    try:
        expected_targets = guru_review_record._clean_target_paths(
            packet.get("target_paths")
        )
        reviewed_targets = guru_review_record._clean_target_paths(
            record.get("target_paths")
        )
    except guru_review_record.ReviewRecordError as exc:
        return str(exc)
    if reviewed_targets != expected_targets:
        return f"slice {slice_id} implementation review target_paths differ from packet"
    try:
        current_components = _slice_component_digests(
            task_dir,
            packet,
            record,
        )
        for field, value in current_components.items():
            if record.get(field) != value:
                return (
                    f"slice {slice_id} review evidence stale: {field}"
                )
        current_evidence_key = guru_review_record.review_evidence_key(
            record.get("reviewed_target_digest"),
            current_components,
        )
        packet_schema = packet.get(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
            1,
        )
        record_schema = record.get(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
            1,
        )
        if record_schema != packet_schema:
            return (
                f"slice {slice_id} review evidence schema is "
                "stale or missing"
            )
        if record.get("evidence_key") != current_evidence_key:
            return f"slice {slice_id} review evidence_key is stale or missing"
        if (
            packet_schema
            == guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
        ):
            invariant_verdicts = (
                guru_review_record.validate_persisted_invariant_verdicts(
                    packet.get("invariants"),
                    record.get("invariant_verdicts"),
                    require_all_pass=True,
                )
            )
            if (
                guru_review_record.aggregate_invariant_coverage(
                    packet.get("invariants"),
                    invariant_verdicts,
                )
                != record.get("invariant_coverage")
            ):
                return (
                    f"slice {slice_id} invariant_coverage does not match "
                    "persisted invariant_verdicts"
                )
            if (
                record.get("invariant_verdicts_digest")
                != guru_review_record.invariant_verdicts_digest(
                    invariant_verdicts
                )
            ):
                return (
                    f"slice {slice_id} invariant_verdicts_digest "
                    "is stale or missing"
                )
            if record.get("deterministic_evidence_key") != current_evidence_key:
                return (
                    f"slice {slice_id} deterministic_evidence_key is stale "
                    "or missing"
                )
            guru_review_record.validate_review_deterministic_evidence(
                task_dir,
                record,
                current_components,
            )
        current_digest = guru_review_record.target_snapshot_digest(
            root,
            expected_targets,
            "index",
        )
    except guru_review_record.ReviewRecordError as exc:
        return f"cannot validate slice {slice_id} review evidence: {exc}"
    if current_digest != record.get("reviewed_target_digest"):
        return f"staged bytes changed after slice {slice_id} implementation review"
    return ""


def _git_is_ancestor(root: str, ancestor: str, descendant: str = "HEAD") -> bool:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise guru_review_record.ReviewRecordError(
            f"cannot verify commit ancestry:{exc}"
        ) from exc
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise guru_review_record.ReviewRecordError(
        "cannot verify commit ancestry:" + (result.stderr or result.stdout or "").strip()
    )


def _commit_parent(root: str, commit_sha: str) -> str:
    line = _git_output(
        root,
        ["rev-list", "--parents", "-n", "1", commit_sha],
        "cannot inspect commit parent",
    ).split()
    if len(line) < 2:
        raise guru_review_record.ReviewRecordError(
            "slice commit must have a first parent"
        )
    return line[1]


def _commit_changed_paths(root: str, commit_sha: str, parent_sha: str) -> list[str]:
    try:
        result = subprocess.run(
            [
                "git", "diff", "--name-only", "--no-renames", "-z",
                parent_sha, commit_sha,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise guru_review_record.ReviewRecordError(
            f"cannot inspect slice commit paths:{exc}"
        ) from exc
    if result.returncode != 0:
        raise guru_review_record.ReviewRecordError(
            "cannot inspect slice commit paths:"
            + (result.stderr or result.stdout or "").strip()
        )
    return [path for path in result.stdout.split("\0") if path]


def _receipt_by_slice(task_dir: str) -> dict[str, dict]:
    history = _receipt_history_by_slice(task_dir)
    return {
        slice_id: receipts[-1]
        for slice_id, receipts in history.items()
        if receipts
    }


class _ReceiptHistory(dict[str, list[dict]]):
    def __init__(self) -> None:
        super().__init__()
        self.batch_memberships: dict[str, list[dict]] = {}


def _receipt_history_by_slice(task_dir: str) -> _ReceiptHistory:
    history = _ReceiptHistory()
    for batch in guru_review_record.load_receipt_batches(task_dir):
        receipts = batch["receipts"]
        membership = {
            "batch_id": batch["batch_id"],
            "ordered_receipt_ids": tuple(
                receipt.get("receipt_id") for receipt in receipts
            ),
            "ordered_slice_ids": tuple(
                receipt["slice_id"] for receipt in receipts
            ),
            "ordered_review_run_ids": tuple(
                receipt["review_run_id"] for receipt in receipts
            ),
            "ordered_commit_shas": tuple(
                receipt["commit_sha"] for receipt in receipts
            ),
        }
        for receipt in receipts:
            history.setdefault(receipt["slice_id"], []).append(receipt)
            receipt_id = receipt.get("receipt_id")
            if isinstance(receipt_id, str):
                history.batch_memberships.setdefault(receipt_id, []).append(
                    membership
                )
    return history


def _aggregate_receipt_batch_problem(
    receipt_history: dict[str, list[dict]],
    receipt: dict,
    review: dict,
) -> str:
    if not isinstance(receipt_history, _ReceiptHistory):
        return "aggregate receipt history does not preserve batch membership"
    receipt_memberships = receipt_history.batch_memberships.get(
        receipt.get("receipt_id"), []
    )
    if len(receipt_memberships) != 1:
        return "aggregate receipt does not belong to exactly one atomic receipt batch"
    membership = receipt_memberships[0]
    expected_slice_ids = tuple(review.get("aggregate_slice_ids") or [])
    expected_run_id = review.get("run_id")
    ordered_receipt_ids = membership["ordered_receipt_ids"]
    if (
        membership["ordered_slice_ids"] != expected_slice_ids
        or len(set(ordered_receipt_ids)) != len(ordered_receipt_ids)
        or any(not isinstance(receipt_id, str) for receipt_id in ordered_receipt_ids)
        or any(
            run_id != expected_run_id
            for run_id in membership["ordered_review_run_ids"]
        )
        or any(
            commit_sha != receipt.get("commit_sha")
            for commit_sha in membership["ordered_commit_shas"]
        )
    ):
        return "aggregate receipt batch does not match official review"
    return ""


def _dependency_receipt_for_commit(
    root: str,
    receipt_history: dict[str, list[dict]],
    dependency: str,
    dependent_commit: str,
    *,
    require_strict_ancestor: bool,
) -> dict | None:
    for candidate in reversed(receipt_history.get(dependency, [])):
        candidate_commit = candidate.get("commit_sha")
        if not isinstance(candidate_commit, str):
            continue
        if require_strict_ancestor and candidate_commit == dependent_commit:
            continue
        try:
            if _git_is_ancestor(root, candidate_commit, dependent_commit):
                return candidate
        except guru_review_record.ReviewRecordError:
            continue
    return None


def _validate_slice_receipt(
    task_dir: str,
    root: str,
    receipt: dict,
    *,
    receipt_history: dict[str, list[dict]] | None = None,
    visiting: set[str] | None = None,
) -> str:
    historical_problem = _validate_historical_slice_receipt(
        task_dir,
        root,
        receipt,
    )
    if historical_problem:
        return historical_problem
    try:
        receipt = guru_review_record.validate_receipt(receipt)
        packet = guru_review_record.load_packet(task_dir, receipt["slice_id"])
        visiting = set() if visiting is None else set(visiting)
        if receipt["slice_id"] in visiting:
            return f"slice receipt dependency cycle:{receipt['slice_id']}"
        visiting.add(receipt["slice_id"])
        review, review_error, aggregate_review = _receipt_review_record(
            task_dir,
            receipt["slice_id"],
            receipt["review_run_id"],
        )
        if review_error or not isinstance(review, dict):
            return review_error or "official implementation review missing"
        if aggregate_review:
            aggregate_packet = guru_review_record.build_aggregate_packet(
                task_dir,
                review["aggregate_slice_ids"],
                review["reviewed_staged_paths"],
            )
            component_map = guru_review_record.aggregate_per_slice_components(
                task_dir,
                aggregate_packet,
                review,
                supervisor_path=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "guru_supervise.py",
                ),
            )
            components = component_map[receipt["slice_id"]]
            components["review_policy_digest"] = guru_review_record.review_policy_digest(
                _slice_review_policy(task_dir, packet, review)
            )
        else:
            components = _slice_component_digests(task_dir, packet, review)
        for field, value in components.items():
            if field == "supervisor_source_digest":
                continue
            if receipt.get(field) != value:
                return f"slice receipt {receipt['slice_id']} stale {field}"
        if receipt_history is None:
            receipt_history = _receipt_history_by_slice(task_dir)
        if aggregate_review:
            batch_problem = _aggregate_receipt_batch_problem(
                receipt_history,
                receipt,
                review,
            )
            if batch_problem:
                return f"slice receipt {receipt['slice_id']} invalid: {batch_problem}"
        for dependency in packet.get("depends_on") or []:
            same_aggregate_dependency = (
                aggregate_review
                and dependency in review.get("aggregate_slice_ids", [])
            )
            dependency_receipt = _dependency_receipt_for_commit(
                root,
                receipt_history,
                dependency,
                receipt["commit_sha"],
                require_strict_ancestor=not same_aggregate_dependency,
            )
            if not isinstance(dependency_receipt, dict):
                return (
                    f"slice receipt {receipt['slice_id']} dependency "
                    f"{dependency} missing from dependent commit ancestry"
                )
            if dependency_receipt.get("commit_sha") == receipt["commit_sha"]:
                dependency_review, _, dependency_is_aggregate = _receipt_review_record(
                    task_dir,
                    dependency,
                    dependency_receipt.get("review_run_id"),
                )
                if (
                    not same_aggregate_dependency
                    or not dependency_is_aggregate
                    or not isinstance(dependency_review, dict)
                    or dependency_review.get("run_id") != review.get("run_id")
                    or dependency_review.get("aggregate_slice_ids")
                    != review.get("aggregate_slice_ids")
                ):
                    return (
                        f"slice receipt {receipt['slice_id']} dependency "
                        f"{dependency} is not a valid same-commit aggregate receipt"
                    )
                receipt_memberships = receipt_history.batch_memberships.get(
                    receipt.get("receipt_id"), []
                )
                dependency_memberships = receipt_history.batch_memberships.get(
                    dependency_receipt.get("receipt_id"), []
                )
                if (
                    len(receipt_memberships) != 1
                    or len(dependency_memberships) != 1
                    or receipt_memberships[0] != dependency_memberships[0]
                ):
                    return (
                        f"slice receipt {receipt['slice_id']} dependency "
                        f"{dependency} is not in the same atomic receipt batch"
                    )
            dependency_problem = _validate_slice_receipt(
                task_dir,
                root,
                dependency_receipt,
                receipt_history=receipt_history,
                visiting=visiting,
            )
            if dependency_problem:
                return (
                    f"slice receipt {receipt['slice_id']} dependency "
                    f"{dependency} invalid: {dependency_problem}"
                )
    except (KeyError, guru_review_record.ReviewRecordError) as exc:
        return str(exc)
    return ""


def _validate_historical_slice_receipt(
    task_dir: str,
    root: str,
    receipt: dict,
) -> str:
    try:
        receipt = guru_review_record.validate_receipt(receipt)
        review, review_error, aggregate_review = _receipt_review_record(
            task_dir,
            receipt["slice_id"],
            receipt["review_run_id"],
        )
        if review_error or not isinstance(review, dict):
            return review_error or "official implementation review missing"
        problem = _implementation_review_base_problem(
            review,
            f"receipt {receipt['slice_id']} implementation review",
        )
        if problem:
            return problem
        full_commit = _git_output(
            root,
            ["rev-parse", "--verify", f"{receipt['commit_sha']}^{{commit}}"],
            "cannot resolve receipt commit",
        )
        if full_commit != receipt["commit_sha"]:
            return f"slice receipt {receipt['slice_id']} commit_sha is not canonical"
        historical_supervisor_digest = (
            guru_review_record.commit_supervisor_source_digest(
                root,
                receipt["commit_sha"],
                _runtime_repo_relative_path(root, "guru_supervise.py"),
            )
        )
        component_fields = (
            "target_paths_digest",
            "invariant_set_digest",
            "requirements_design_digest",
            "deterministic_commands_digest",
            "deterministic_results_digest",
            "review_policy_digest",
            "supervisor_source_digest",
        )
        if aggregate_review:
            aggregate_packet = guru_review_record.build_aggregate_packet(
                task_dir,
                review["aggregate_slice_ids"],
                review["reviewed_staged_paths"],
            )
            aggregate_problem = _aggregate_review_problem(
                task_dir,
                root,
                aggregate_packet,
                review,
                verify_index=False,
                supervisor_digest=historical_supervisor_digest,
            )
            if aggregate_problem:
                return aggregate_problem
            recorded_components = dict(
                review["per_slice_component_digests"][receipt["slice_id"]]
            )
            reviewed_digest = review["per_slice_target_digests"][
                receipt["slice_id"]
            ]
            expected_evidence_key = review["per_slice_evidence_keys"][
                receipt["slice_id"]
            ]
        else:
            recorded_components = {
                field: review.get(field) for field in component_fields
            }
            reviewed_digest = review.get("reviewed_target_digest")
            expected_evidence_key = guru_review_record.review_evidence_key(
                reviewed_digest,
                recorded_components,
            )
        for field, value in recorded_components.items():
            if not isinstance(value, str) or not re.fullmatch(
                r"[0-9a-f]{64}", value
            ):
                return (
                    f"receipt {receipt['slice_id']} review lacks "
                    f"official {field}"
                )
            if receipt.get(field) != value:
                return f"slice receipt {receipt['slice_id']} {field} mismatch"
        if (
            not aggregate_review
            and review.get("evidence_key") != expected_evidence_key
        ):
            return f"receipt {receipt['slice_id']} review evidence_key mismatch"
        review_schema = review.get(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
            1,
        )
        receipt_schema = receipt.get(
            guru_review_record.RECEIPT_REVIEW_EVIDENCE_SCHEMA_FIELD,
            1,
        )
        if review_schema not in (
            1,
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION,
        ):
            return (
                f"receipt {receipt['slice_id']} review "
                "review_evidence_schema_version invalid"
            )
        if receipt_schema != review_schema:
            return (
                f"receipt {receipt['slice_id']} review evidence schema "
                "mismatch"
            )
        if review_schema == guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION:
            historical_verdicts = review.get("invariant_verdicts")
            if not isinstance(historical_verdicts, dict):
                return (
                    f"receipt {receipt['slice_id']} review lacks "
                    "invariant_verdicts"
                )
            if aggregate_review:
                slice_packet = guru_review_record.load_packet(
                    task_dir,
                    receipt["slice_id"],
                )
                historical_verdicts = {
                    invariant["invariant_id"]: historical_verdicts[
                        invariant["invariant_id"]
                    ]
                    for invariant in slice_packet["invariants"]
                }
            historical_invariants = [
                {"invariant_id": invariant_id}
                for invariant_id in historical_verdicts
            ]
            guru_review_record.validate_persisted_invariant_verdicts(
                historical_invariants,
                historical_verdicts,
                require_all_pass=True,
            )
            historical_verdicts_digest = (
                guru_review_record.invariant_verdicts_digest(
                    historical_verdicts
                )
            )
            if (
                not aggregate_review
                and
                review.get("invariant_verdicts_digest")
                != historical_verdicts_digest
            ):
                return (
                    f"receipt {receipt['slice_id']} review "
                    "invariant_verdicts_digest mismatch"
                )
            if receipt.get(
                guru_review_record.RECEIPT_INVARIANT_VERDICTS_DIGEST_FIELD
            ) != historical_verdicts_digest:
                return (
                    f"receipt {receipt['slice_id']} "
                    "invariant_verdicts_digest mismatch"
                )
            if receipt.get(
                guru_review_record.RECEIPT_DETERMINISTIC_EVIDENCE_KEY_FIELD
            ) != expected_evidence_key:
                return (
                    f"receipt {receipt['slice_id']} "
                    "deterministic_evidence_key mismatch"
                )
            if (
                not aggregate_review
                and review.get("deterministic_evidence_key")
                != expected_evidence_key
            ):
                return (
                    f"receipt {receipt['slice_id']} review "
                    "deterministic_evidence_key mismatch"
                )
            if not aggregate_review:
                guru_review_record.validate_review_deterministic_evidence(
                    task_dir,
                    review,
                    recorded_components,
                )
        if receipt["reviewed_target_digest"] != reviewed_digest:
            return f"slice receipt {receipt['slice_id']} review digest mismatch"
        if not _git_is_ancestor(root, receipt["commit_sha"]):
            return (
                f"slice receipt {receipt['slice_id']} commit is not on "
                "current HEAD ancestry"
            )
        if _commit_parent(root, receipt["commit_sha"]) != receipt["parent_sha"]:
            return f"slice receipt {receipt['slice_id']} parent_sha mismatch"
        commit_time = _git_output(
            root,
            ["show", "-s", "--format=%cI", receipt["commit_sha"]],
            "cannot read receipt commit timestamp",
        )
        if commit_time != receipt["committed_at"]:
            return f"slice receipt {receipt['slice_id']} committed_at mismatch"
        historical_targets = (
            review["per_slice_target_paths"][receipt["slice_id"]]
            if aggregate_review
            else review.get("target_paths")
        )
        tree_digest = guru_review_record.commit_target_digest(
            root,
            historical_targets,
            receipt["commit_sha"],
        )
        if tree_digest != receipt["reviewed_target_digest"]:
            return (
                f"slice receipt {receipt['slice_id']} commit bytes differ "
                "from reviewed digest"
            )
        if historical_supervisor_digest != receipt["supervisor_source_digest"]:
            return f"slice receipt {receipt['slice_id']} supervisor source mismatch"
    except (KeyError, guru_review_record.ReviewRecordError) as exc:
        return str(exc)
    return ""


def _slice_dependency_problem(
    task_dir: str,
    root: str,
    packet: dict,
    *,
    dependent_commit: str = "HEAD",
    require_strict_ancestor: bool = False,
) -> str:
    depends_on = packet.get("depends_on", [])
    if depends_on is None:
        depends_on = []
    if not isinstance(depends_on, list) or not all(
        isinstance(dep, str) and dep.strip() for dep in depends_on
    ):
        return f"slice {packet['slice_id']} depends_on must be a string array"
    try:
        receipt_history = _receipt_history_by_slice(task_dir)
    except guru_review_record.ReviewRecordError as exc:
        return str(exc)
    for dependency in depends_on:
        receipt = _dependency_receipt_for_commit(
            root,
            receipt_history,
            dependency,
            dependent_commit,
            require_strict_ancestor=require_strict_ancestor,
        )
        if not isinstance(receipt, dict):
            return (
                f"slice {packet['slice_id']} dependency {dependency} "
                "has no valid commit receipt"
            )
        problem = _validate_slice_receipt(
            task_dir,
            root,
            receipt,
            receipt_history=receipt_history,
        )
        if problem:
            return (
                f"slice {packet['slice_id']} dependency {dependency} "
                f"receipt invalid: {problem}"
            )
    return ""


def _resolve_slice_packet(
    task_dir_arg,
    slice_id: str,
) -> tuple[str | None, dict | None, str]:
    task_dir = resolve_task_dir(
        task_dir_arg,
        allow_unique_planning_fallback=False,
    )
    if not task_dir:
        return None, None, "无法定位任务目录，请显式传 task_dir"
    contract, error = guru_contract.load_contract(task_dir)
    if error:
        return task_dir, None, error
    if (
        not isinstance(contract, dict)
        or guru_contract.contract_route(contract) != guru_contract.ROUTE_FULL_CHAIN
        or guru_contract.contract_risk(contract)
        not in {guru_contract.RISK_HIGH, guru_contract.RISK_UNKNOWN}
    ):
        return task_dir, None, "slice commit lifecycle only applies to Full/high-like tasks"
    try:
        packet = guru_review_record.load_packet(task_dir, slice_id)
    except guru_review_record.ReviewRecordError as exc:
        return task_dir, None, str(exc)
    if packet.get("slice_id") != slice_id:
        return task_dir, None, f"slice packet id mismatch:{packet.get('slice_id')!r}"
    return task_dir, packet, ""


def _runtime_repo_relative_path(root: str, sibling_name: str) -> str:
    runtime_path = os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), sibling_name)
    )
    root_real = os.path.realpath(root)
    if (
        runtime_path == root_real
        or not runtime_path.startswith(root_real + os.sep)
    ):
        raise guru_review_record.ReviewRecordError(
            f"runtime source is outside repository:{runtime_path}"
        )
    return guru_review_record._clean_target_paths(
        [os.path.relpath(runtime_path, root_real).replace(os.sep, "/")]
    )[0]


def cmd_check_slice_commit(task_dir_arg, slice_id: str) -> int:
    task_dir, packet, error = _resolve_slice_packet(task_dir_arg, slice_id)
    if error or not isinstance(task_dir, str) or not isinstance(packet, dict):
        sys.stderr.write(f"[guru-gate:check-commit] 拦截：{error}\n")
        return BLOCK
    root = _repo_root()
    staged_paths, staged_error = _git_staged_paths(root)
    problems = []
    if staged_error:
        problems.append(staged_error)
    if not staged_paths:
        problems.append("没有 staged changes")
    contract_problem = _slice_contract_problem(
        task_dir,
        root,
        staged_paths,
    )
    if contract_problem:
        problems.append(contract_problem)
    artifacts = [
        path for path in staged_paths
        if _is_task_artifact_path(path, task_dir, root)
    ]
    if artifacts:
        problems.append(
            "staged task artifacts/workspace artifacts must not enter slice commit: "
            + ", ".join(artifacts[:5])
        )
    out_of_scope = [
        path for path in staged_paths
        if not _path_in_targets(path, packet["target_paths"])
    ]
    if out_of_scope:
        problems.append(
            f"staged paths outside slice {slice_id} target_paths: "
            + ", ".join(out_of_scope[:5])
        )
    dependency_problem = _slice_dependency_problem(task_dir, root, packet)
    if dependency_problem:
        problems.append(dependency_problem)
    review, review_error = _slice_review_record(task_dir, slice_id)
    if review_error or not isinstance(review, dict):
        problems.append(review_error or "official implementation review missing")
    else:
        review_problem = _slice_review_problem(
            task_dir,
            root,
            packet,
            review,
        )
        if review_problem:
            problems.append(review_problem)
    if problems:
        sys.stderr.write(
            "[guru-gate:check-commit] 拦截：" + "; ".join(_dedupe_strings(problems)) + "\n"
        )
        return BLOCK
    print(
        f"[guru-gate:check-commit] SLICE_COMMIT_READY "
        f"slice={slice_id} review_run_id={review.get('run_id')}"
    )
    return PASS


def _resolve_aggregate_packet(
    task_dir_arg,
    slice_ids: list[str],
    staged_paths: list[str],
) -> tuple[str | None, dict | None, str]:
    if not slice_ids:
        return None, None, "aggregate requires at least one explicit --slice"
    task_dir, _, error = _resolve_slice_packet(task_dir_arg, slice_ids[0])
    if error or not isinstance(task_dir, str):
        return task_dir, None, error
    for slice_id in slice_ids[1:]:
        resolved_task, _, packet_error = _resolve_slice_packet(task_dir, slice_id)
        if packet_error or resolved_task != task_dir:
            return task_dir, None, packet_error or "aggregate task mismatch"
    try:
        packet = guru_review_record.build_aggregate_packet(
            task_dir,
            slice_ids,
            staged_paths,
        )
    except guru_review_record.ReviewRecordError as exc:
        return task_dir, None, str(exc)
    return task_dir, packet, ""


def _aggregate_review_record(
    task_dir: str,
    aggregate_slice_ids: list[str],
    review_run_id: str | None = None,
) -> tuple[dict | None, str]:
    path = os.path.join(task_dir, "review-records", "implementation-reviews.jsonl")
    records, error = _implementation_review_records(path)
    if error:
        return None, error
    expected_target = "aggregate:" + ",".join(aggregate_slice_ids)
    matches = [
        record
        for record in records
        if record.get("review_target") == expected_target
        and record.get("aggregate_slice_ids") == aggregate_slice_ids
        and (review_run_id is None or record.get("run_id") == review_run_id)
    ]
    if not matches:
        suffix = f" run_id={review_run_id}" if review_run_id else ""
        return None, f"official aggregate implementation review missing{suffix}"
    return matches[-1], ""


def _aggregate_receipts_problem(task_dir: str, slice_ids: list[str]) -> str:
    try:
        existing = sorted(
            {
                receipt["slice_id"]
                for receipt in guru_review_record.receipt_records(task_dir)
                if receipt.get("slice_id") in set(slice_ids)
            }
        )
    except guru_review_record.ReviewRecordError as exc:
        return str(exc)
    if existing:
        return (
            "aggregate bootstrap requires all selected receipts missing; "
            f"existing={existing}"
        )
    return ""


def _aggregate_receipt_replay_state(
    task_dir: str,
    slice_ids: list[str],
    expected_receipts: list[dict],
) -> tuple[str, str]:
    """Classify a producer retry without accepting partial or split batches."""
    try:
        expected = [
            guru_review_record.validate_receipt(receipt)
            for receipt in expected_receipts
        ]
        batches = guru_review_record.load_receipt_batches(task_dir)
    except guru_review_record.ReviewRecordError as exc:
        return "", str(exc)
    selected = set(slice_ids)
    selected_batches = []
    existing = []
    for batch in batches:
        selected_receipts = [
            receipt
            for receipt in batch["receipts"]
            if receipt.get("slice_id") in selected
        ]
        if selected_receipts:
            selected_batches.append((batch, selected_receipts))
            existing.extend(selected_receipts)
    if not existing:
        return "missing", ""
    existing_ids = {receipt["slice_id"] for receipt in existing}
    if existing_ids != selected:
        missing = sorted(selected - existing_ids)
        return (
            "",
            "aggregate receipt replay is partial; missing=" + ",".join(missing),
        )
    if len(selected_batches) != 1:
        return "", "aggregate receipt replay conflicts across receipt batches"
    batch, selected_receipts = selected_batches[0]
    if batch["receipts"] != selected_receipts or selected_receipts != expected:
        return "", "aggregate receipt replay conflicts with expected receipt batch"
    return "exists", ""


def _aggregate_review_problem(
    task_dir: str,
    root: str,
    packet: dict,
    record: dict,
    *,
    verify_index: bool,
    supervisor_digest: str | None = None,
) -> str:
    ids = packet["aggregate_slice_ids"]
    problem = _implementation_review_base_problem(
        record,
        "aggregate implementation review",
    )
    if problem:
        return problem
    if (
        record.get("slice_id") != "aggregate"
        or record.get("review_target") != "aggregate:" + ",".join(ids)
        or record.get("aggregate_slice_ids") != ids
    ):
        return "aggregate review does not bind the explicit slice set"
    expected_fields = {
        "target_paths": packet["target_paths"],
        "reviewed_staged_paths": packet["reviewed_staged_paths"],
        "per_slice_target_paths": packet["per_slice_target_paths"],
        "per_slice_requirements_design_digests": packet[
            "per_slice_requirements_design_digests"
        ],
    }
    for field, expected in expected_fields.items():
        if record.get(field) != expected:
            return f"aggregate review {field} mismatch"
    if record.get("aggregate_target_digest") != record.get("reviewed_target_digest"):
        return "aggregate_target_digest mismatch"
    try:
        components = _slice_component_digests(
            task_dir,
            packet,
            record,
            supervisor_digest=supervisor_digest,
        )
        for field, value in components.items():
            if record.get(field) != value:
                return f"aggregate review evidence stale: {field}"
        evidence_key = guru_review_record.review_evidence_key(
            record.get("reviewed_target_digest"),
            components,
        )
        if (
            record.get("evidence_key") != evidence_key
            or record.get("deterministic_evidence_key") != evidence_key
        ):
            return "aggregate review evidence_key is stale or missing"
        verdicts = guru_review_record.validate_persisted_invariant_verdicts(
            packet["invariants"],
            record.get("invariant_verdicts"),
            require_all_pass=True,
        )
        if record.get("invariant_verdicts_digest") != (
            guru_review_record.invariant_verdicts_digest(verdicts)
        ):
            return "aggregate invariant_verdicts_digest mismatch"
        guru_review_record.validate_review_deterministic_evidence(
            task_dir,
            record,
            components,
        )
        per_components = guru_review_record.aggregate_per_slice_components(
            task_dir,
            packet,
            record,
            supervisor_path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "guru_supervise.py",
            ),
            supervisor_digest=supervisor_digest,
        )
        for slice_id in ids:
            slice_packet = guru_review_record.load_packet(task_dir, slice_id)
            per_components[slice_id]["review_policy_digest"] = (
                guru_review_record.review_policy_digest(
                    _slice_review_policy(task_dir, slice_packet, record)
                )
            )
        if record.get("per_slice_component_digests") != per_components:
            return "aggregate per_slice_component_digests mismatch"
        target_digests = record.get("per_slice_target_digests")
        if not isinstance(target_digests, dict) or set(target_digests) != set(ids):
            return "aggregate per_slice_target_digests invalid"
        per_keys = {
            slice_id: guru_review_record.review_evidence_key(
                target_digests[slice_id],
                per_components[slice_id],
            )
            for slice_id in ids
        }
        if record.get("per_slice_evidence_keys") != per_keys:
            return "aggregate per_slice_evidence_keys mismatch"
        if verify_index:
            current_aggregate = guru_review_record.target_snapshot_digest(
                root,
                packet["target_paths"],
                "index",
            )
            if current_aggregate != record.get("reviewed_target_digest"):
                return "staged bytes changed after aggregate implementation review"
            for slice_id, paths in packet["per_slice_target_paths"].items():
                current_slice = guru_review_record.target_snapshot_digest(
                    root,
                    paths,
                    "index",
                )
                if current_slice != target_digests.get(slice_id):
                    return f"staged bytes changed after aggregate review for {slice_id}"
    except (KeyError, guru_review_record.ReviewRecordError) as exc:
        return f"cannot validate aggregate review evidence: {exc}"
    return ""


def cmd_check_aggregate_slice_commit(task_dir_arg, slice_ids: list[str]) -> int:
    root = _repo_root()
    staged_paths, staged_error = _git_staged_paths(root)
    task_dir, packet, error = _resolve_aggregate_packet(
        task_dir_arg,
        slice_ids,
        staged_paths,
    )
    problems = []
    if staged_error:
        problems.append(staged_error)
    if error or not isinstance(task_dir, str) or not isinstance(packet, dict):
        problems.append(error or "aggregate packet invalid")
    if not staged_paths:
        problems.append("没有 staged changes")
    if isinstance(task_dir, str):
        artifacts = [
            path
            for path in staged_paths
            if _is_task_artifact_path(path, task_dir, root)
        ]
        if artifacts:
            problems.append(
                "staged task artifacts/workspace artifacts must not enter aggregate commit: "
                + ", ".join(artifacts[:5])
            )
        contract_problem = _slice_contract_problem(
            task_dir,
            root,
            staged_paths,
        )
        if contract_problem:
            problems.append(contract_problem)
    if isinstance(task_dir, str) and isinstance(packet, dict):
        receipt_problem = _aggregate_receipts_problem(
            task_dir,
            packet["aggregate_slice_ids"],
        )
        if receipt_problem:
            problems.append(receipt_problem)
        review, review_error = _aggregate_review_record(
            task_dir,
            packet["aggregate_slice_ids"],
        )
        if review_error or not isinstance(review, dict):
            problems.append(review_error or "official aggregate review missing")
        else:
            review_problem = _aggregate_review_problem(
                task_dir,
                root,
                packet,
                review,
                verify_index=True,
            )
            if review_problem:
                problems.append(review_problem)
    else:
        review = None
    if problems:
        sys.stderr.write(
            "[guru-gate:check-commit] 拦截："
            + "; ".join(_dedupe_strings(problems))
            + "\n"
        )
        return BLOCK
    print(
        "[guru-gate:check-commit] SLICE_COMMIT_READY "
        f"aggregate={','.join(packet['aggregate_slice_ids'])} "
        f"review_run_id={review.get('run_id')}"
    )
    return PASS


def cmd_record_slice_commit(
    task_dir_arg,
    slice_id: str,
    review_run_id: str,
) -> int:
    task_dir, packet, error = _resolve_slice_packet(task_dir_arg, slice_id)
    if error or not isinstance(task_dir, str) or not isinstance(packet, dict):
        sys.stderr.write(f"[guru-gate:record-slice-commit] 拦截：{error}\n")
        return BLOCK
    root = _repo_root()
    try:
        review, review_error, aggregate_owner = _receipt_review_record(
            task_dir,
            slice_id,
            review_run_id,
        )
        if (
            review_error
            or not isinstance(review, dict)
            or aggregate_owner
        ):
            raise guru_review_record.ReviewRecordError(
                review_error
                or "review_run_id does not have unique ordinary slice ownership"
            )
        latest_review, latest_review_error = _slice_review_record(
            task_dir,
            slice_id,
        )
        if latest_review_error or not isinstance(latest_review, dict):
            raise guru_review_record.ReviewRecordError(
                latest_review_error or "latest implementation review missing"
            )
        if latest_review.get("run_id") != review_run_id:
            raise guru_review_record.ReviewRecordError(
                "record-slice-commit requires the latest slice review run_id"
            )
        problem = _slice_review_problem(task_dir, root, packet, review)
        if problem:
            raise guru_review_record.ReviewRecordError(problem)
        commit_sha = _git_output(
            root,
            ["rev-parse", "--verify", "HEAD^{commit}"],
            "cannot resolve HEAD commit",
        )
        dependency_problem = _slice_dependency_problem(
            task_dir,
            root,
            packet,
            dependent_commit=commit_sha,
            require_strict_ancestor=True,
        )
        if dependency_problem:
            raise guru_review_record.ReviewRecordError(dependency_problem)
        parent_sha = _commit_parent(root, commit_sha)
        changed_paths = _commit_changed_paths(root, commit_sha, parent_sha)
        contract_problem = _slice_contract_problem(
            task_dir,
            root,
            changed_paths,
        )
        if contract_problem:
            raise guru_review_record.ReviewRecordError(contract_problem)
        if not changed_paths:
            raise guru_review_record.ReviewRecordError(
                "HEAD commit has no changed paths"
            )
        artifacts = [
            path for path in changed_paths
            if _is_task_artifact_path(path, task_dir, root)
        ]
        if artifacts:
            raise guru_review_record.ReviewRecordError(
                "slice commit contains task/workspace artifacts: "
                + ", ".join(artifacts[:5])
            )
        out_of_scope = [
            path for path in changed_paths
            if not _path_in_targets(path, packet["target_paths"])
        ]
        if out_of_scope:
            raise guru_review_record.ReviewRecordError(
                f"slice commit contains paths outside {slice_id} target_paths: "
                + ", ".join(out_of_scope[:5])
            )
        tree_digest = guru_review_record.commit_target_digest(
            root,
            packet["target_paths"],
            commit_sha,
        )
        if tree_digest != review.get("reviewed_target_digest"):
            raise guru_review_record.ReviewRecordError(
                "HEAD commit bytes differ from reviewed staged digest"
            )
        components = _slice_component_digests(task_dir, packet, review)
        committed_supervisor_digest = (
            guru_review_record.commit_supervisor_source_digest(
                root,
                commit_sha,
                _runtime_repo_relative_path(root, "guru_supervise.py"),
            )
        )
        if components["supervisor_source_digest"] != committed_supervisor_digest:
            raise guru_review_record.ReviewRecordError(
                "supervisor source differs between reviewed worktree and slice commit"
            )
        components["supervisor_source_digest"] = committed_supervisor_digest
        committed_at = _git_output(
            root,
            ["show", "-s", "--format=%cI", commit_sha],
            "cannot read commit timestamp",
        )
        receipt = {
            "schema_version": guru_review_record.RECEIPT_SCHEMA_VERSION,
            "slice_id": slice_id,
            "commit_sha": commit_sha,
            "parent_sha": parent_sha,
            "review_run_id": review_run_id,
            "reviewed_target_digest": tree_digest,
            **components,
            "committed_at": committed_at,
        }
        if (
            review.get(guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD)
            == guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
        ):
            receipt[
                guru_review_record.RECEIPT_REVIEW_EVIDENCE_SCHEMA_FIELD
            ] = guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
            receipt[
                guru_review_record.RECEIPT_DETERMINISTIC_EVIDENCE_KEY_FIELD
            ] = review["deterministic_evidence_key"]
            receipt[
                guru_review_record.RECEIPT_INVARIANT_VERDICTS_DIGEST_FIELD
            ] = review["invariant_verdicts_digest"]
        receipt["receipt_id"] = guru_review_record.canonical_digest(
            "guru-slice-commit-receipt-v1",
            guru_review_record.receipt_digest_payload(receipt),
        )
        existing = _receipt_by_slice(task_dir).get(slice_id)
        if existing is not None:
            if existing == receipt:
                print(
                    f"[guru-gate:record-slice-commit] RECEIPT_EXISTS "
                    f"slice={slice_id} commit={commit_sha}"
                )
                return PASS
            if existing.get("commit_sha") == commit_sha:
                raise guru_review_record.ReviewRecordError(
                    f"conflicting slice receipt already exists for commit:{slice_id}"
                )
            existing_problem = _validate_historical_slice_receipt(
                task_dir,
                root,
                existing,
            )
            if existing_problem:
                raise guru_review_record.ReviewRecordError(
                    f"existing slice receipt invalid:{slice_id}:{existing_problem}"
                )
            if not _git_is_ancestor(root, existing["commit_sha"], commit_sha):
                raise guru_review_record.ReviewRecordError(
                    f"new slice receipt does not supersede prior ancestor:{slice_id}"
                )
        current_owner, owner_error, current_is_aggregate = _receipt_review_record(
            task_dir,
            slice_id,
            review_run_id,
        )
        if (
            owner_error
            or current_is_aggregate
            or current_owner != review
        ):
            raise guru_review_record.ReviewRecordError(
                owner_error
                or "slice review_run_id ownership changed before receipt append"
            )
        guru_review_record.append_receipt_batch(task_dir, [receipt])
    except guru_review_record.ReviewRecordError as exc:
        sys.stderr.write(f"[guru-gate:record-slice-commit] 拦截：{exc}\n")
        return BLOCK
    print(
        f"[guru-gate:record-slice-commit] RECEIPT_RECORDED "
        f"slice={slice_id} commit={commit_sha} review_run_id={review_run_id} "
        f"receipt_id={receipt['receipt_id']}"
    )
    return PASS


def cmd_record_aggregate_slice_commit(
    task_dir_arg,
    slice_ids: list[str],
    review_run_id: str,
) -> int:
    root = _repo_root()
    try:
        if not slice_ids:
            raise guru_review_record.ReviewRecordError(
                "aggregate requires at least one explicit --slice"
            )
        task_dir, _, error = _resolve_slice_packet(task_dir_arg, slice_ids[0])
        if error or not isinstance(task_dir, str):
            raise guru_review_record.ReviewRecordError(error or "task missing")
        ordered_packets = guru_review_record._aggregate_topological_packets(
            task_dir,
            slice_ids,
        )
        ordered_ids = [packet["slice_id"] for packet in ordered_packets]
        review, review_error, aggregate_owner = _receipt_review_record(
            task_dir,
            ordered_ids[0],
            review_run_id,
        )
        if (
            review_error
            or not isinstance(review, dict)
            or not aggregate_owner
            or review.get("aggregate_slice_ids") != ordered_ids
        ):
            raise guru_review_record.ReviewRecordError(
                review_error
                or "review_run_id does not have unique aggregate ownership"
            )
        latest, latest_error = _aggregate_review_record(task_dir, ordered_ids)
        if latest_error or not isinstance(latest, dict):
            raise guru_review_record.ReviewRecordError(
                latest_error or "latest aggregate review missing"
            )
        if latest.get("run_id") != review_run_id:
            raise guru_review_record.ReviewRecordError(
                "record-slice-commit --aggregate requires the latest aggregate review run_id"
            )
        packet = guru_review_record.build_aggregate_packet(
            task_dir,
            ordered_ids,
            review.get("reviewed_staged_paths"),
        )
        review_problem = _aggregate_review_problem(
            task_dir,
            root,
            packet,
            review,
            verify_index=False,
        )
        if review_problem:
            raise guru_review_record.ReviewRecordError(review_problem)

        commit_sha = _git_output(
            root,
            ["rev-parse", "--verify", "HEAD^{commit}"],
            "cannot resolve HEAD commit",
        )
        parent_sha = _commit_parent(root, commit_sha)
        changed_paths = _commit_changed_paths(root, commit_sha, parent_sha)
        if guru_review_record._clean_target_paths(changed_paths) != packet[
            "reviewed_staged_paths"
        ]:
            raise guru_review_record.ReviewRecordError(
                "aggregate commit changed paths differ from reviewed_staged_paths"
            )
        contract_problem = _slice_contract_problem(
            task_dir,
            root,
            changed_paths,
        )
        if contract_problem:
            raise guru_review_record.ReviewRecordError(contract_problem)
        artifacts = [
            path
            for path in changed_paths
            if _is_task_artifact_path(path, task_dir, root)
        ]
        if artifacts:
            raise guru_review_record.ReviewRecordError(
                "aggregate commit contains task/workspace artifacts: "
                + ", ".join(artifacts[:5])
            )
        aggregate_digest = guru_review_record.commit_target_digest(
            root,
            packet["target_paths"],
            commit_sha,
        )
        if aggregate_digest != review.get("reviewed_target_digest"):
            raise guru_review_record.ReviewRecordError(
                "aggregate commit bytes differ from reviewed staged digest"
            )
        committed_supervisor_digest = (
            guru_review_record.commit_supervisor_source_digest(
                root,
                commit_sha,
                _runtime_repo_relative_path(root, "guru_supervise.py"),
            )
        )
        committed_at = _git_output(
            root,
            ["show", "-s", "--format=%cI", commit_sha],
            "cannot read commit timestamp",
        )
        target_digests = review["per_slice_target_digests"]
        component_maps = review["per_slice_component_digests"]
        per_keys = review["per_slice_evidence_keys"]
        receipts = []
        for slice_packet in ordered_packets:
            slice_id = slice_packet["slice_id"]
            tree_digest = guru_review_record.commit_target_digest(
                root,
                slice_packet["target_paths"],
                commit_sha,
            )
            if tree_digest != target_digests.get(slice_id):
                raise guru_review_record.ReviewRecordError(
                    f"aggregate commit bytes differ from reviewed {slice_id} digest"
                )
            components = dict(component_maps[slice_id])
            if components.get("supervisor_source_digest") != committed_supervisor_digest:
                raise guru_review_record.ReviewRecordError(
                    f"aggregate {slice_id} supervisor source differs from commit"
                )
            slice_verdicts = {
                invariant["invariant_id"]: review["invariant_verdicts"][
                    invariant["invariant_id"]
                ]
                for invariant in slice_packet["invariants"]
            }
            slice_verdict_digest = guru_review_record.invariant_verdicts_digest(
                slice_verdicts
            )
            receipt = {
                "schema_version": guru_review_record.RECEIPT_SCHEMA_VERSION,
                "slice_id": slice_id,
                "commit_sha": commit_sha,
                "parent_sha": parent_sha,
                "review_run_id": review_run_id,
                "reviewed_target_digest": tree_digest,
                **components,
                "committed_at": committed_at,
                guru_review_record.RECEIPT_REVIEW_EVIDENCE_SCHEMA_FIELD: (
                    guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
                ),
                guru_review_record.RECEIPT_DETERMINISTIC_EVIDENCE_KEY_FIELD: (
                    per_keys[slice_id]
                ),
                guru_review_record.RECEIPT_INVARIANT_VERDICTS_DIGEST_FIELD: (
                    slice_verdict_digest
                ),
            }
            receipt["receipt_id"] = guru_review_record.canonical_digest(
                "guru-slice-commit-receipt-v1",
                guru_review_record.receipt_digest_payload(receipt),
            )
            receipts.append(receipt)
        current_owner, owner_error, current_is_aggregate = _receipt_review_record(
            task_dir,
            ordered_ids[0],
            review_run_id,
        )
        if (
            owner_error
            or not current_is_aggregate
            or current_owner != review
            or current_owner.get("aggregate_slice_ids") != ordered_ids
        ):
            raise guru_review_record.ReviewRecordError(
                owner_error
                or "aggregate review_run_id ownership changed before receipt append"
            )
        replay_state, replay_error = _aggregate_receipt_replay_state(
            task_dir,
            ordered_ids,
            receipts,
        )
        if replay_error:
            raise guru_review_record.ReviewRecordError(replay_error)
        if replay_state == "exists":
            print(
                "[guru-gate:record-slice-commit] RECEIPTS_EXIST "
                f"aggregate={','.join(ordered_ids)} commit={commit_sha} "
                f"review_run_id={review_run_id} receipts={len(receipts)}"
            )
            return PASS
        guru_review_record.append_receipt_batch(task_dir, receipts)
    except (KeyError, guru_review_record.ReviewRecordError) as exc:
        sys.stderr.write(
            f"[guru-gate:record-slice-commit] 拦截：{exc}\n"
        )
        return BLOCK
    print(
        "[guru-gate:record-slice-commit] RECEIPTS_RECORDED "
        f"aggregate={','.join(ordered_ids)} commit={commit_sha} "
        f"review_run_id={review_run_id} receipts={len(receipts)}"
    )
    return PASS


def _commit_plan_payload(task_dir_arg) -> dict:
    root = _repo_root()
    staged_paths, staged_error = _git_staged_paths(root)
    plan = _new_commit_plan(staged_paths)

    def block(reason: str) -> None:
        if reason and reason not in plan["blocking_reasons"]:
            plan["blocking_reasons"].append(reason)

    if staged_error:
        block(staged_error)
        plan["required_commands"].append("git diff --cached --name-only")
        return _finish_commit_plan(plan)
    task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False)
    if not staged_paths:
        if task_dir:
            plan["task_dir"] = _display_task_dir(task_dir, root)
            contract, contract_error = guru_contract.load_contract(task_dir)
            plan["contract_present"] = isinstance(contract, dict)
            plan["contract_valid"] = False if contract_error else (not bool(guru_contract.validate_contract(contract)) if isinstance(contract, dict) else None)
            plan["route"] = guru_contract.contract_route(contract) or guru_contract.ROUTE_FULL_CHAIN
        elif task_dir_arg:
            plan["route"] = guru_contract.ROUTE_FULL_CHAIN
        else:
            plan["route"] = "direct_small_inline"
            plan["commit_mode"] = "direct"
        block("没有 staged changes")
        plan["required_commands"].append("git add -- <paths>")
        return _finish_commit_plan(plan)

    if not task_dir:
        if task_dir_arg:
            plan["route"] = guru_contract.ROUTE_FULL_CHAIN
            plan["forbidden_stage_paths"] = staged_paths
            block("无法定位任务目录，请检查显式 task_dir")
            plan["required_commands"].append(_gate_command("check-commit", task_dir_arg, root))
            return _finish_commit_plan(plan)
        plan["route"] = "direct_small_inline"
        plan["commit_mode"] = "direct"
        plan["split_required"] = _commit_plan_split_required(staged_paths, "", root)
        allowed, forbidden = _direct_commit_stage_paths(staged_paths, root)
        plan["allowed_stage_paths"] = allowed
        plan["forbidden_stage_paths"] = forbidden
        problem = _direct_low_risk_commit_problem(staged_paths, root)
        if problem:
            block(problem)
            plan["required_commands"].append(
                "create or select a micro_task/lite_task/full_chain task, then rerun commit-plan"
            )
        else:
            plan["can_commit_now"] = True
            plan["commit_mode"] = "direct"
        plan["suggested_stage_commands"] = _stage_command(plan["allowed_stage_paths"])
        return _finish_commit_plan(plan)

    plan["task_dir"] = _display_task_dir(task_dir, root)
    plan["split_required"] = _commit_plan_split_required(staged_paths, task_dir, root)
    split_artifacts, split_code_paths = _commit_plan_split_scope(staged_paths, task_dir, root)
    contract, contract_error = guru_contract.load_contract(task_dir)
    if contract_error:
        block(contract_error)
        plan["route"] = guru_contract.ROUTE_FULL_CHAIN
        plan["forbidden_stage_paths"] = staged_paths
        plan["contract_present"] = True
        plan["contract_valid"] = False
        plan["required_commands"].append(_gate_command("check-commit", task_dir, root))
        return _finish_commit_plan(plan)
    plan["contract_present"] = isinstance(contract, dict)
    route = guru_contract.contract_route(contract) or guru_contract.ROUTE_FULL_CHAIN
    plan["route"] = route
    if isinstance(contract, dict):
        contract_problems = guru_contract.validate_commit_contract(contract, staged_paths, task_dir, root)
        plan["contract_valid"] = not bool(contract_problems)
        allowed, forbidden = _contract_commit_stage_paths(contract, staged_paths, task_dir, root)
        plan["allowed_stage_paths"] = allowed
        plan["forbidden_stage_paths"] = forbidden
    else:
        contract_problems = []
        direct_recovery_problem = _direct_low_risk_commit_problem(staged_paths, root)
        if not direct_recovery_problem and _task_status(task_dir) != "in_progress":
            plan["route"] = guru_contract.ROUTE_MICRO_TASK
            plan["commit_mode"] = "implementation"
            allowed, forbidden = _direct_commit_stage_paths(staged_paths, root)
            plan["allowed_stage_paths"] = allowed
            plan["forbidden_stage_paths"] = forbidden
            block(_post_implementation_recovery_reason("active task has no commit contract"))
            plan["required_commands"].extend(_micro_recovery_commands(staged_paths, root))
            plan["suggested_stage_commands"] = _stage_command(plan["allowed_stage_paths"])
            return _finish_commit_plan(plan)

    if split_artifacts and split_code_paths:
        plan["split_required"] = True
        if not plan["allowed_stage_paths"]:
            plan["allowed_stage_paths"] = split_code_paths
        plan["forbidden_stage_paths"] = _dedupe_strings(plan["forbidden_stage_paths"] + split_artifacts)
        block("staged task artifacts/workspace artifacts must be split from implementation commit: " + ", ".join(split_artifacts[:5]))

    if route == guru_contract.ROUTE_MICRO_TASK:
        plan["commit_mode"] = "implementation"
        micro_contract = contract if isinstance(contract, dict) else {}
        problem = _micro_commit_contract_problem(micro_contract, staged_paths, task_dir, root)
        if problem:
            block(problem)
            high_signal_problem = problem.startswith("micro_task staged paths contain high-risk signals:")
            high_path_signals, cross_layer_or_storage, _code_paths = _micro_commit_high_path_signals(
                micro_contract,
                staged_paths,
                task_dir,
                root,
            )
            if (
                high_signal_problem
                and high_path_signals
                and cross_layer_or_storage
            ):
                plan["split_required"] = True
                plan["split_suggestions"] = _micro_commit_split_suggestions(staged_paths, task_dir, root)
            plan["required_commands"].append(_gate_command("check-commit", task_dir, root))
        else:
            plan["can_commit_now"] = True
        plan["suggested_stage_commands"] = _stage_command(plan["allowed_stage_paths"])
        return _finish_commit_plan(plan)

    if route == guru_contract.ROUTE_LITE_TASK:
        plan["commit_mode"] = "implementation"
        standard_problems = _lite_standard_task_problems(task_dir)
        for problem in standard_problems:
            block(problem)
        confirmation_problem = _requirements_confirmation_problem(task_dir, route)
        if confirmation_problem:
            block(confirmation_problem)
            plan["required_user_confirmations"].append("requirements")
            plan["required_commands"].append(
                f"python3 .trellis/scripts/guru/guru_gate.py confirm requirements "
                f"{shlex.quote(_display_task_dir(task_dir, root))}"
            )
        status = _task_status(task_dir)
        if status != "in_progress":
            block(f"lite_task requires task.json.status=in_progress before commit; got {status!r}")
            if status == "planning":
                plan["required_commands"].append(
                    f"python3 .trellis/scripts/task.py start {shlex.quote(_display_task_dir(task_dir, root))}"
                )
        if contract_problems:
            block("; ".join(contract_problems[:5]))
        if (
            not standard_problems
            and not confirmation_problem
            and status == "in_progress"
            and not contract_problems
            and isinstance(contract, dict)
        ):
            evidence_problem = _lite_deterministic_evidence_problem(
                task_dir,
                contract,
                staged_paths,
                root,
            )
            if evidence_problem:
                block(evidence_problem)
                plan["required_commands"].append(
                    "run the focused checks and append a current deterministic_final record to "
                    f"{shlex.quote(_display_task_dir(task_dir, root))}/verification-evidence.jsonl"
                )
        plan["review_coverage"] = _empty_review_coverage()
        plan["review_coverage"]["source"] = "not-required-for-lite_task"
        plan["suggested_stage_commands"] = _stage_command(plan["allowed_stage_paths"])
        if plan["blocking_reasons"]:
            if not plan["required_commands"]:
                plan["required_commands"].append(_gate_command("auto", task_dir, root))
        else:
            plan["can_commit_now"] = True
        return _finish_commit_plan(plan)

    implementation_problem = _captured_gate_problem("check-implementation", task_dir, root)
    if implementation_problem:
        block(f"check-implementation failed: {implementation_problem}")
        plan["required_commands"].append(_gate_command("check-implementation", task_dir, root))

    review_path = os.path.join(task_dir, "review-records", "implementation-reviews.jsonl")
    needs_implementation_review = False
    implementation_review_problem = ""
    review_coverage, implementation_review_problem, needs_implementation_review = (
        _implementation_review_coverage(review_path, staged_paths, task_dir, root)
    )
    plan["review_coverage"] = review_coverage
    if implementation_review_problem:
        block(implementation_review_problem)
    allowed = review_coverage.get("covered_staged_paths", [])
    forbidden = (
        review_coverage.get("forbidden_staged_paths", [])
        + review_coverage.get("uncovered_staged_paths", [])
    )
    if allowed or forbidden:
        plan["allowed_stage_paths"] = allowed
        plan["forbidden_stage_paths"] = _dedupe_strings(forbidden)
    if allowed:
        plan["suggested_stage_commands"] = _stage_command(plan["allowed_stage_paths"])

    if not isinstance(contract, dict):
        direct_recovery_problem = _direct_low_risk_commit_problem(staged_paths, root)
        if direct_recovery_problem:
            block(direct_recovery_problem)
        elif (
            plan["blocking_reasons"]
            and implementation_review_problem
            and not plan["review_coverage"].get("ignored_covering_review_ids")
        ):
            plan["route"] = guru_contract.ROUTE_MICRO_TASK
            plan["allowed_stage_paths"], plan["forbidden_stage_paths"] = _direct_commit_stage_paths(staged_paths, root)
            plan["blocking_reasons"] = []
            block(_post_implementation_recovery_reason("active task has no commit contract"))
            plan["required_commands"] = _micro_recovery_commands(staged_paths, root)
            plan["review_coverage"]["missing_review_commands"] = []
            plan["suggested_stage_commands"] = _stage_command(plan["allowed_stage_paths"])
            return _finish_commit_plan(plan)

    if contract_problems:
        block("; ".join(contract_problems[:5]))
    review_commands_allowed = not contract_problems and not implementation_problem and not plan.get("split_required")
    if not review_commands_allowed:
        review_coverage["missing_review_commands"] = []
    if plan["blocking_reasons"]:
        if needs_implementation_review and review_commands_allowed:
            missing_review_commands = review_coverage.get("missing_review_commands") or [
                _implementation_review_command(task_dir, root)
            ]
            plan["required_commands"].extend(missing_review_commands)
        plan["required_commands"].append(_gate_command("check-commit", task_dir, root))
    else:
        plan["can_commit_now"] = True
    return _finish_commit_plan(plan)


def cmd_commit_plan(task_dir_arg, write: bool = False) -> int:
    plan = _commit_plan_payload(task_dir_arg)
    if write:
        task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False)
        if not task_dir:
            sys.stderr.write("[guru-gate:commit-plan] --write 需要显式可定位的 task_dir\n")
            return BLOCK
        try:
            _write_json_atomic(os.path.join(task_dir, "commit-plan.json"), plan)
        except OSError as exc:
            sys.stderr.write(f"[guru-gate:commit-plan] 写 commit-plan.json 失败：{exc}\n")
            return BLOCK
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    return PASS


def _record_lite_delivery_evidence_cache(task_dir_arg, root: str) -> tuple[str, str]:
    task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False)
    if not task_dir:
        return "", "cannot resolve Lite task for evidence cache"
    contract, read_error = guru_contract.load_contract(task_dir)
    if read_error or not isinstance(contract, dict):
        return "", read_error or "Lite contract missing for evidence cache"
    execution_policy = contract.get("execution_policy")
    if not isinstance(execution_policy, dict):
        return "", "Lite execution_policy missing for evidence cache"
    evidence_path = os.path.join(task_dir, "verification-evidence.jsonl")
    latest = None
    existing_cache_keys = set()
    try:
        with open(evidence_path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    continue
                if row.get("kind") == "deterministic_final":
                    latest = row
                if row.get("kind") == "delivery_evidence_cache" and isinstance(
                    row.get("evidence_cache_key"), str
                ):
                    existing_cache_keys.add(row["evidence_cache_key"])
    except (OSError, json.JSONDecodeError) as exc:
        return "", f"cannot read Lite evidence cache source: {exc}"
    if not isinstance(latest, dict):
        return "", "Lite deterministic_final evidence missing for evidence cache"
    target_digest = latest.get("target_digest")
    target_paths = latest.get("target_paths")
    docs_digest = guru_delivery_policy.project_docs_code_test_digest(root)
    values = {
        "policy_version": execution_policy.get("policy_version"),
        "intent": execution_policy.get("intent"),
        "execution_route": execution_policy.get("route"),
        "scope_fingerprint": execution_policy.get("scope_fingerprint"),
        "target_digest": target_digest,
        "docs_code_test_digest": docs_digest,
    }
    if not all(isinstance(value, str) and value for value in values.values()):
        return "", "Lite evidence cache binding fields are incomplete"
    if not isinstance(target_paths, list) or not target_paths:
        return "", "Lite evidence cache target_paths missing"
    cache_key = guru_delivery_policy.delivery_evidence_cache_key(**values)
    if cache_key in existing_cache_keys:
        return cache_key, ""
    record = {
        "schema_version": 1,
        "kind": "delivery_evidence_cache",
        "status": "passed",
        "outcome": "passed",
        "evidence_cache_key": cache_key,
        "policy_version": values["policy_version"],
        "intent": values["intent"],
        "route": values["execution_route"],
        "selection_generation": execution_policy.get("selection_generation"),
        "scope_fingerprint": values["scope_fingerprint"],
        "target_paths": target_paths,
        "target_digest": target_digest,
        "docs_code_test_digest": docs_digest,
    }
    try:
        with open(evidence_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError as exc:
        return "", f"cannot append Lite evidence cache: {exc}"
    return cache_key, ""


def cmd_check_commit(task_dir_arg) -> int:
    plan = _commit_plan_payload(task_dir_arg)
    if not plan.get("can_commit_now"):
        reasons = plan.get("blocking_reasons") or ["commit-plan blocked"]
        sys.stderr.write(f"[guru-gate:check-commit] 拦截：{'; '.join(reasons)}\n")
        if (
            plan.get("route") == guru_contract.ROUTE_MICRO_TASK
            and plan.get("split_required")
            and plan.get("split_suggestions")
        ):
            sys.stderr.write(
                "下一步：拆分 staged scope，按 layer 分别提交并尽量带上对应 tests；"
                "cross-layer/storage high-risk signal 不能通过 gate-degradations.jsonl 降级。\n"
            )
            for suggestion in (plan.get("split_suggestions") or [])[:6]:
                layer = suggestion.get("layer") or "other"
                command = suggestion.get("stage_command") or "git add -- <paths>"
                paired_tests = suggestion.get("paired_tests") or []
                suffix = f" paired_tests={', '.join(paired_tests[:5])}" if paired_tests else ""
                sys.stderr.write(f"  - {layer}: {command}{suffix}\n")
        for command in plan.get("required_commands") or []:
            sys.stderr.write(f"下一步：{command}\n")
        return BLOCK
    route = plan.get("route")
    task_dir = plan.get("task_dir") or task_dir_arg or ""
    if route == "direct_small_inline":
        print("[guru-gate:check-commit] COMMIT_READY: direct small_inline scoped low-risk commit")
    elif route == guru_contract.ROUTE_MICRO_TASK:
        print(f"[guru-gate:check-commit] COMMIT_READY: micro_task contract allows scoped low-risk commit（{task_dir}）")
    elif route == guru_contract.ROUTE_LITE_TASK:
        cache_key, cache_error = _record_lite_delivery_evidence_cache(task_dir_arg, _repo_root())
        if cache_error:
            sys.stderr.write(f"[guru-gate:check-commit] evidence cache warning: {cache_error}\n")
        print(
            f"[guru-gate:check-commit] COMMIT_READY: Lite standard task + current requirements confirmation "
            f"+ in_progress + scoped deterministic contract evidence（{task_dir}）；"
            "implementation Worker/review not required"
            + (f"；evidence_cache_key={cache_key}" if cache_key else "")
        )
    else:
        print(f"[guru-gate:check-commit] COMMIT_READY: staged scope has current clean implementation review coverage（{task_dir}）")
    return PASS


def auto(task_dir_arg) -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        print("[guru-gate:auto] 无活动任务，跳过（合法）")
        return PASS
    status = "planning"
    tj = read(os.path.join(task_dir, "task.json"))
    if tj:
        try:
            status = json.loads(tj).get("status", "planning")
        except json.JSONDecodeError:
            pass
    route = _contract_route_for_review_policy(task_dir)
    if route == guru_contract.ROUTE_LITE_TASK:
        if cmd_check_start(task_dir, "auto") != PASS:
            return BLOCK
        if status == "planning":
            return PASS
        if status != "in_progress":
            sys.stderr.write(
                f"[guru-gate:auto] 拦截：Lite task.json.status={status!r}；"
                "只允许 planning START_READY 或 in_progress deterministic check。\n"
            )
            return BLOCK
        return ok(
            "auto",
            "Lite 标准任务/当前确认/合同 scope 均有效；host 直接完成 deterministic check，无 implementation Worker/review",
        )
    if route in {guru_contract.ROUTE_SMALL_INLINE, guru_contract.ROUTE_MICRO_TASK}:
        return ok("auto", f"route={route} 无 Full planning Gate")
    if status in ("planning",):
        rc = check_requirements(task_dir)
        if rc != PASS:
            return rc
        if _block_requirements_review("auto", task_dir) != PASS:
            return BLOCK
        req = _gate_states(task_dir).get("requirements")
        if not (
            isinstance(req, dict)
            and req.get("confirmed_by")
            and req.get("artifact_digest") == _gate_digest(task_dir, "requirements")
        ):
            sys.stderr.write("[guru-gate:auto] 拦截：需求 Gate 未确认或确认快照失配\n")
            sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}\n")
            return BLOCK
        src = _artifact_sources(task_dir)
        full = task_chain(task_dir) == "full"
        # full 链：design_package 已声明即校验骨架（声明但损坏不得静默跳过）；
        # 未声明属概要阶段 0 待办——渐进语义下放行但显式提示，不静默。
        if src["overview"] or (full and _package_dir(task_dir)):
            rc = check_overview(task_dir)
            if rc != PASS:
                return rc
            if not _review_state(task_dir, "overview")["ready"]:
                return _block_review("auto", task_dir, "overview")
            if src["detail"] or src["imp"]:
                rc = check_detail(task_dir)
                if rc != PASS:
                    return rc
                if not _review_state(task_dir, "detail")["ready"]:
                    return _block_review("auto", task_dir, "detail")
                return PASS
        note = "；full 链尚未声明 design_package（概要阶段 0 待办）" if full and not _package_dir(task_dir) else ""
        return ok("auto", f"planning 渐进校验到当前 artifact（{task_dir}，{task_chain(task_dir)} 链{note}）")
    for fn in (check_requirements, check_overview, check_detail, check_implement):
        rc = fn(task_dir)
        if rc != PASS:
            return rc
    if _block_requirements_review("auto", task_dir) != PASS:
        return BLOCK
    req = _gate_states(task_dir).get("requirements")
    if not (
        isinstance(req, dict)
        and req.get("confirmed_by")
        and req.get("artifact_digest") == _gate_digest(task_dir, "requirements")
    ):
        sys.stderr.write("[guru-gate:auto] 拦截：需求 Gate 未确认或确认快照失配\n")
        return BLOCK
    for gate in REVIEW_GATES:
        if not _review_state(task_dir, gate)["ready"]:
            return _block_review("auto", task_dir, gate)
    return ok("auto", f"status={status} 全 Gate 通过")


def _pop_value_option(argv: list, name: str):
    if name not in argv:
        return None
    idx = argv.index(name)
    if idx + 1 >= len(argv):
        del argv[idx]
        return ""
    value = argv[idx + 1]
    del argv[idx:idx + 2]
    return value


def _pop_all_value_options(argv: list, name: str) -> list:
    values = []
    while name in argv:
        idx = argv.index(name)
        if idx + 1 >= len(argv):
            del argv[idx]
            values.append("")
            continue
        values.append(argv[idx + 1])
        del argv[idx:idx + 2]
    return values


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__ or "")
        return BLOCK
    cmd = sys.argv[1]
    argv = list(sys.argv[2:])
    # --user-quote 带值：先摘出值，避免污染位置参数
    user_quote = _pop_value_option(argv, "--user-quote")
    review_options = {
        "result": _pop_value_option(argv, "--result"),
        "max_severity": _pop_value_option(argv, "--max-severity"),
        "finding_class": _pop_value_option(argv, "--finding-class"),
        "reviewer": _pop_value_option(argv, "--reviewer"),
        "run_id": _pop_value_option(argv, "--run-id"),
        "evidence": _pop_value_option(argv, "--evidence"),
        "deletion_audit": _pop_value_option(argv, "--deletion-audit"),
    }
    init_contract_options = {
        "route": _pop_value_option(argv, "--route"),
        "risk": _pop_value_option(argv, "--risk"),
        "max_files": _pop_value_option(argv, "--max-files"),
        "confidence": _pop_value_option(argv, "--confidence"),
        "created_by": _pop_value_option(argv, "--created-by") if cmd == "init-contract" else None,
        "allowed_paths": _pop_all_value_options(argv, "--allowed-path"),
        "forbidden_patterns": _pop_all_value_options(argv, "--forbidden-pattern"),
        "reasons": _pop_all_value_options(argv, "--reason") if cmd == "init-contract" else [],
        "risk_flags": _pop_all_value_options(argv, "--risk-flag"),
        "recommended_route": _pop_value_option(argv, "--recommended-route"),
        "user_override_quote": _pop_value_option(argv, "--user-override-quote"),
        "risk_acknowledged": _pop_value_option(argv, "--risk-acknowledged"),
        "selected_by": _pop_value_option(argv, "--selected-by"),
    }
    intake_options = {
        "description": _pop_value_option(argv, "--description"),
        "paths": _pop_all_value_options(argv, "--path"),
        "preferred_route": _pop_value_option(argv, "--preferred-route"),
        "coupling": _pop_value_option(argv, "--coupling"),
        "verification_scope": _pop_value_option(argv, "--verification-scope"),
        "prior_route": _pop_value_option(argv, "--prior-route"),
        "prior_selection_generation": _pop_value_option(argv, "--prior-selection-generation"),
    }
    degradation_options = {
        "gate": _pop_value_option(argv, "--gate"),
        "reason": _pop_value_option(argv, "--reason"),
        "command": _pop_value_option(argv, "--command"),
        "stderr_excerpt": _pop_value_option(argv, "--stderr-excerpt"),
        "allowed_by": _pop_value_option(argv, "--allowed-by"),
        "created_by": _pop_value_option(argv, "--created-by"),
        "checks": _pop_all_value_options(argv, "--check"),
    }
    slice_ids = _pop_all_value_options(argv, "--slice")
    slice_id = slice_ids[0] if len(slice_ids) == 1 else None
    review_run_id = _pop_value_option(argv, "--review-run-id")
    rest = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    intake_options["commit_requested"] = "--commit-requested" in flags
    intake_options["write_contract"] = "--write-contract" in flags
    intake_options["use_staged"] = "--staged" in flags
    intake_options["requirements_clear"] = (
        True if "--requirements-clear" in flags
        else (False if "--requirements-ambiguous" in flags else None)
    )
    intake_options["reversible"] = (
        True if "--reversible" in flags
        else (False if "--irreversible" in flags else None)
    )
    intake_options["first_write_started"] = "--first-write-started" in flags
    arg = rest[0] if rest else None
    table = {
        "requirements": check_requirements,
        "overview": check_overview,
        "detail": check_detail,
        "implement": check_implement,
    }
    if cmd == "auto":
        return auto(arg)
    if cmd == "confirm":
        # confirm [gate] [task_dir] [--via-agent]：gate 省略=批量确认全部待确认 Gate
        if rest and rest[0] in ALL_GATES:
            gate_arg, dir_arg = rest[0], (rest[1] if len(rest) > 1 else None)
        else:
            gate_arg, dir_arg = None, (rest[0] if rest else None)
        return cmd_confirm(gate_arg, dir_arg, via_agent="--via-agent" in flags, user_quote=user_quote)
    if cmd == "record-review":
        if not rest or rest[0] not in REVIEW_GATES:
            sys.stderr.write(f"[guru-gate:record-review] 需要 gate 参数（{', '.join(REVIEW_GATES)}）\n")
            return BLOCK
        task_dir = resolve_task_dir(rest[1] if len(rest) > 1 else None)
        if not task_dir:
            sys.stderr.write("[guru-gate:record-review] 无法定位任务目录\n")
            return BLOCK
        return _record_review(task_dir, rest[0], review_options)
    if cmd == "grill-done":
        gate_arg, dir_arg = (rest[0] if rest else None), (rest[1] if len(rest) > 1 else None)
        return cmd_grill_done(gate_arg, dir_arg, via_agent="--via-agent" in flags, user_quote=user_quote)
    if cmd == "grill-skip":
        gate_arg, dir_arg = (rest[0] if rest else None), (rest[1] if len(rest) > 1 else None)
        return cmd_grill_skip(gate_arg, dir_arg, via_agent="--via-agent" in flags, user_quote=user_quote)
    if cmd == "digest":
        if not rest or rest[0] not in ALL_GATES:
            sys.stderr.write(f"[guru-gate:digest] 需要 gate 参数（{', '.join(ALL_GATES)}）\n")
            return BLOCK
        task_dir = resolve_task_dir(rest[1] if len(rest) > 1 else None)
        if not task_dir:
            sys.stderr.write("[guru-gate:digest] 无法定位任务目录\n")
            return BLOCK
        manifest_problem = _requirement_package_problem(task_dir)
        if manifest_problem:
            sys.stderr.write(f"[guru-gate:digest] {manifest_problem}\n")
            return BLOCK
        print(_gate_digest(task_dir, rest[0]))
        return PASS
    if cmd == "status":
        return cmd_status(arg)
    if cmd == "check-start":
        return cmd_check_start(arg)
    if cmd == "check":
        return cmd_check(arg)
    if cmd == "check-implementation":
        return cmd_check_implementation(arg)
    if cmd == "commit-plan":
        return cmd_commit_plan(arg, write="--write" in flags)
    if cmd == "intake":
        return cmd_intake(arg, intake_options)
    if cmd == "init-contract":
        return cmd_init_contract(arg, init_contract_options)
    if cmd == "record-degradation":
        return cmd_record_degradation(arg, degradation_options)
    if cmd == "slice-plan":
        return cmd_slice_plan(arg)
    if cmd == "check-commit":
        if "--aggregate" in flags:
            return cmd_check_aggregate_slice_commit(arg, slice_ids)
        if len(slice_ids) > 1:
            sys.stderr.write(
                "[guru-gate:check-commit] repeated --slice requires --aggregate\n"
            )
            return BLOCK
        if slice_id is not None:
            if not slice_id.strip():
                sys.stderr.write("[guru-gate:check-commit] --slice 需要非空值\n")
                return BLOCK
            return cmd_check_slice_commit(arg, slice_id.strip())
        return cmd_check_commit(arg)
    if cmd == "record-slice-commit":
        if "--aggregate" in flags:
            if not review_run_id or not review_run_id.strip():
                sys.stderr.write("[guru-gate:record-slice-commit] --review-run-id 是必填项\n")
                return BLOCK
            return cmd_record_aggregate_slice_commit(
                arg,
                slice_ids,
                review_run_id.strip(),
            )
        if len(slice_ids) > 1:
            sys.stderr.write(
                "[guru-gate:record-slice-commit] repeated --slice requires --aggregate\n"
            )
            return BLOCK
        if not slice_id or not slice_id.strip():
            sys.stderr.write("[guru-gate:record-slice-commit] --slice 是必填项\n")
            return BLOCK
        if not review_run_id or not review_run_id.strip():
            sys.stderr.write("[guru-gate:record-slice-commit] --review-run-id 是必填项\n")
            return BLOCK
        return cmd_record_slice_commit(
            arg,
            slice_id.strip(),
            review_run_id.strip(),
        )
    if cmd == "trace-matrix":
        if not arg or not os.path.isdir(arg):
            sys.stderr.write("[guru-gate:trace-matrix] 需要有效 task_dir 参数\n")
            return BLOCK
        # --require-req-uc 触发合同（finding 3）：① CLI 显式 --require-req-uc 强制（即使旧 task）；
        # ② 无 CLI flag 时读 task.json require_req_uc==true；③ 都无则旧 task 默认 false → 不拦。
        require_req_uc = "--require-req-uc" in flags
        if not require_req_uc:
            require_req_uc = _task_json_of(arg).get("require_req_uc") is True
        return cmd_trace_matrix(arg, "--write" in flags, "--strict" in flags, require_req_uc)
    if cmd == "trace-aggregate":
        # trace-aggregate <version-dir> [--include-completed]：不复用 trace-matrix 的 task_dir 解析
        if not arg or not os.path.isdir(arg):
            sys.stderr.write("[guru-gate:trace-aggregate] 需要有效 version 目录参数\n")
            return BLOCK
        return cmd_trace_aggregate(arg, "--include-completed" in flags)
    if cmd in table:
        if not arg or not os.path.isdir(arg):
            sys.stderr.write(f"[guru-gate:{cmd}] 需要有效 task_dir 参数\n")
            return BLOCK
        return table[cmd](arg)
    sys.stderr.write(f"未知子命令: {cmd}\n{__doc__}")
    return BLOCK


if __name__ == "__main__":
    sys.exit(main())
