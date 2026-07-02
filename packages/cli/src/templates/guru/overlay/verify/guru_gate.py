#!/usr/bin/env python3
"""Guru 五阶段 Gate 校验 + 追溯矩阵（结构底线检查；语义判定由 review loop 负责）。

Gate 确认模型 SSOT：.trellis/spec/harness/gate/gate-confirmation-model.md

用法:
  python3 guru_gate.py auto [task_dir]            # 按 task.json status + artifact 渐进校验（worktree.yaml verify 用这个）
  python3 guru_gate.py requirements <task_dir>    # 需求 Gate：prd.md（含 BHV 编号纪律）
  python3 guru_gate.py overview <task_dir>        # 概要 Gate：light=design.md §概要；full=设计包 design-main.md（结构+归属+索引）
  python3 guru_gate.py detail <task_dir>          # 详细 Gate：light=design.md §详细；full=chapters/*.md（章节闭合+pending L2 拦截）+ implement.md
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
                                                  # 人工确认 Gate（需求确认 + 详细设计 review 双 clean 后确认）
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
                                                  # 实现/检查 worker 前置：START_READY + task.json.status == in_progress
  python3 guru_gate.py check-commit [task_dir]    # 提交前置：check-implementation + staged scope + implementation review clean
  python3 guru_gate.py digest <gate> [task_dir]   # 输出该阶段产物的确认快照摘要（排查快照失配用）

编号纪律:
  BHV-NNN   行为编号。prd.md 中以标题定义（如 `### BHV-001 玩家选择 Hammer`）；创建后不复用、不重排，删除留洞。
  UNIT-slug 设计单元编号。design.md §2 中以标题定义（如 `### UNIT-hammer-usecase`）；语义 slug。
  下游引用一律写裸编号（兼容未来的 [[file#BHV-001]] 双链包裹——解析按编号 token 识别）。

双轨制:
  task.json `guru_chain: full|light` 判轨（after_create 默认 full；light 须经分流+用户同意显式声明）。
  full  完整五阶段链：目录级设计包（task.json `design_package` 指向，含 README.md/design-main.md/chapters/）。
  light 轻量链：单文件 design.md §1/§2（存量兼容：两字段皆缺按 light 检查）。

退出码: 0=通过/合法跳过; 2=Gate 拦截(stderr 给缺口清单)。
设计约束: 只查结构存在性与引用闭合, 不做语义判断——"判不动的规则不进脚本"。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# 共享风险 helper（单一来源，防两份风险逻辑漂移）：guru_gate 作脚本运行时其目录已在 sys.path[0]，
# 被 guru_supervise import 时其目录也已加入——此处显式补一遍兜底奇怪调用形态。guru_risk **不 import
# guru_gate**（防循环）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guru_risk  # noqa: E402
import guru_contract  # noqa: E402
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
    cfg = read(os.path.join(_config_root_for_task(task_dir), ".trellis", "config.yaml"))
    if not cfg:
        return ""
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
            return _config_scalar(raw_value)
        if not _config_has_scalar(raw_value):
            stack.append((indent, key))
    return ""


def _config_bool(path: tuple[str, ...], default: bool, task_dir: str = None) -> bool:
    value = _config_value(path, task_dir).strip().lower()
    if not value:
        return default
    return value not in {"0", "false", "no", "off"}


def _adversarial_enabled(task_dir: str = None) -> bool:
    return _config_bool(("guru", "supervision", "adversarial_enabled"), True, task_dir)


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
    adversarial_required = _adversarial_enabled(task_dir)
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
        return f"review ✅ clean x{state['clean_count']} ({ids}; adversarial disabled by config)"
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
        else "（adversarial_enabled=false 时不要求 adversarial reviewer）"
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


def _record_confirm(task_dir: str, gate: str, via: str, user_quote=None) -> int:
    """写入单个 Gate 的确认记录（严格 JSON 守卫 + 原子写）。via ∈ tty|agent。"""
    data = _task_data_for_write(task_dir, "confirm")
    if data is None:
        return BLOCK
    gates = data.setdefault(GATES_KEY, {})
    previous = gates.get(gate)
    record = {
        "confirmed_by": _developer_name(),
        "confirmed_at": _now_iso(),
        "confirmation_scope": "requirements_gate_only" if gate == "requirements" else "detail_gate_only",
        "allowed_next_action": "overview_design" if gate == "requirements" else "task_start",
        "prompt_summary": (
            "Requirements confirmation allows overview/detail planning only"
            if gate == "requirements"
            else "Detail confirmation allows task.py start only"
        ),
        # 确认快照：check 时比对，产物在确认后被修改 → 要求重新确认
        "artifact_digest": _gate_digest(task_dir, gate),
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
    for g in HUMAN_GATES:
        s = states.get(g)
        ok_record = (isinstance(s, dict) and s.get("confirmed_by")
                     and s.get("artifact_digest") == _gate_digest(task_dir, g))
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
    # manifest fail-closed：确认快照 digest 累积 requirements 产物（含正式需求包），非法 manifest 先拦
    manifest_problem = _requirement_package_problem(task_dir)
    if manifest_problem:
        sys.stderr.write(f"[guru-gate:confirm] {manifest_problem}\n")
        return BLOCK
    allowed, interactive, mode = _authorize_gate_write("confirm", via_agent, user_quote)
    if not allowed:
        return BLOCK
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
    adversarial_required = _adversarial_enabled(task_dir)
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
    adversarial_required = _adversarial_enabled(task_dir)
    if not review:
        if not adversarial_required:
            return "✅ disabled by config — adversarial requirements review not required"
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
    if not _adversarial_enabled(task_dir):
        sys.stderr.write(
            f"[guru-gate:{action}] 拦截：requirements review 记录存在当前阻断问题；"
            f"{problem}。\n"
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
    print(f"  Brainstorm Evidence — {_brainstorm_status_mark(task_dir)}")
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
            else "（adversarial_enabled=false，不要求 adversarial reviewer）"
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


def cmd_check_start(task_dir_arg, channel: str = "check-start") -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        # check 是阻断闸门：定位不到任务即拒绝（与"任一不满足 exit 2"的合同一致）。
        # before_start 注入 TASK_JSON_PATH、hook 透传命令参数，正常路径都可定位。
        sys.stderr.write(f"[guru-gate:{channel}] 无法定位任务目录，请显式传 task_dir 或确保 TASK_JSON_PATH 已注入\n")
        return BLOCK
    # 结构 Gate 复跑：防止"确认后再改产物"带病 start（确认只代表确认时点的状态）
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
    status = _task_status(task_dir)
    if status != "in_progress":
        sys.stderr.write(
            f"[guru-gate:check-implementation] 拦截：task.json.status={status!r}，"
            "实现/检查 worker 只能在 task.py start 后运行。\n"
        )
        if status == "planning":
            sys.stderr.write(
                f"当前只达到 START_READY；下一步运行：python3 .trellis/scripts/task.py start {task_dir}\n"
            )
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


def _implementation_review_problem(record, staged_paths: list, task_dir: str, root: str) -> str:
    if not isinstance(record, dict):
        return "implementation review record missing"
    verdict_problem = guru_review_record.validate_verdict_values(record)
    if verdict_problem:
        return "latest implementation review is malformed or incomplete; rerun implement-check for a complete clean verdict"
    if str(record.get("review_result", "")).strip().lower() != "clean":
        return f"latest implementation review is not clean: review_result={record.get('review_result')!r}"
    if str(record.get("route_class", "none")).strip() not in {"", "none"}:
        return f"latest implementation review route_class is not none: {record.get('route_class')!r}"
    if str(record.get("supervisor_failure", "none")).strip() not in {"", "none"}:
        return f"latest implementation review has supervisor_failure={record.get('supervisor_failure')!r}"
    if record.get("required_satisfied") is not True:
        return "latest implementation review did not satisfy required semantic provider"
    for key, bad_values in (
        ("deterministic_checks", {"failed", "missing"}),
        ("dirty_scope", {"invalid"}),
        ("invariant_coverage", {"failed", "missing"}),
    ):
        value = str(record.get(key, "")).strip().lower()
        if value in bad_values:
            return f"latest implementation review has {key}={value}"
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
        return "staged changes contain only task/workspace artifacts; this is not a Guru implementation commit"
    if not isinstance(target_paths, list) or not target_paths:
        return "latest implementation review has no target_paths; cannot prove staged scope belongs to reviewed slice"
    out_of_scope = [path for path in code_paths if not _path_in_targets(path, target_paths)]
    if out_of_scope:
        return "staged paths outside latest reviewed target_paths: " + ", ".join(out_of_scope[:5])
    reviewed_digest = record.get("reviewed_target_digest")
    if not isinstance(reviewed_digest, str) or not reviewed_digest.strip():
        return "latest implementation review has no reviewed_target_digest; rerun implement-check before commit"
    try:
        staged_digest = guru_review_record.target_snapshot_digest(root, target_paths, "index")
    except guru_review_record.ReviewRecordError as exc:
        return f"cannot compute staged target digest: {exc}"
    if staged_digest != reviewed_digest:
        return "staged target content differs from latest clean implementation review; rerun implement-check"
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
    code_paths = [
        path for path in staged_paths
        if not guru_contract.is_task_artifact_path(path, task_dir, root)
    ]
    high_path_signals = set(guru_contract.high_risk_path_signals(code_paths))
    if guru_risk.has_cross_layer_or_storage(code_paths):
        high_path_signals.add("cross-layer/storage path signal")
    if high_path_signals:
        return "micro_task staged paths contain high-risk signals: " + ", ".join(sorted(high_path_signals)[:5])
    return ""


def _cmd_check_micro_commit(task_dir: str, contract: dict, staged_paths: list, root: str) -> int:
    problem = _micro_commit_contract_problem(contract, staged_paths, task_dir, root)
    if problem:
        sys.stderr.write(f"[guru-gate:check-commit] 拦截：{problem}\n")
        sys.stderr.write(
            "下一步：收窄 staged scope / 补齐 gate-degradations.jsonl 的补偿检查，"
            "或将任务升级为 lite/full 后重跑对应 review。\n"
        )
        return BLOCK
    print(f"[guru-gate:check-commit] COMMIT_READY: micro_task contract allows scoped low-risk commit（{task_dir}）")
    return PASS


def _direct_low_risk_commit_problem(staged_paths: list, root: str) -> str:
    artifact_paths = [path for path in staged_paths if guru_contract.is_task_artifact_path(path, "", root)]
    if artifact_paths:
        return "direct low-risk commit cannot include task/workspace artifacts: " + ", ".join(artifact_paths[:5])
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


def cmd_check_commit(task_dir_arg) -> int:
    root = _repo_root()
    staged_paths, staged_error = _git_staged_paths(root)
    if staged_error:
        sys.stderr.write(f"[guru-gate:check-commit] {staged_error}\n")
        return BLOCK
    if not staged_paths:
        sys.stderr.write("[guru-gate:check-commit] 拦截：没有 staged changes\n")
        return BLOCK
    task_dir = resolve_task_dir(task_dir_arg, allow_unique_planning_fallback=False)
    if not task_dir:
        if task_dir_arg:
            sys.stderr.write("[guru-gate:check-commit] 无法定位任务目录，请检查显式 task_dir\n")
            return BLOCK
        return _cmd_check_direct_low_risk_commit(staged_paths, root)
    contract, contract_error = guru_contract.load_contract(task_dir)
    if contract_error:
        sys.stderr.write(f"[guru-gate:check-commit] 拦截：{contract_error}\n")
        return BLOCK
    route = guru_contract.contract_route(contract)
    if route == guru_contract.ROUTE_MICRO_TASK:
        return _cmd_check_micro_commit(task_dir, contract, staged_paths, root)

    if cmd_check_implementation(task_dir) != PASS:
        sys.stderr.write("[guru-gate:check-commit] 提交被拒：实现期 gate 未通过。\n")
        return BLOCK
    review_path = os.path.join(task_dir, "review-records", "implementation-reviews.jsonl")
    latest_record, read_error = _latest_jsonl_record(review_path)
    if read_error:
        sys.stderr.write(f"[guru-gate:check-commit] {read_error}\n")
        return BLOCK
    problem = _implementation_review_problem(latest_record, staged_paths, task_dir, root)
    if problem:
        sys.stderr.write(f"[guru-gate:check-commit] 拦截：{problem}\n")
        sys.stderr.write(
            "下一步：运行 guru_supervise.py implement-check 产出 clean implementation review record，"
            "并只 stage 已审查 target_paths 内的实现文件。\n"
        )
        return BLOCK
    if contract:
        contract_problem = _contract_validation_problem(contract, staged_paths, task_dir, root)
        if contract_problem:
            sys.stderr.write(f"[guru-gate:check-commit] 拦截：{contract_problem}\n")
            sys.stderr.write("下一步：修正 gate-contract.json / gate-degradations.jsonl 后重跑 check-commit。\n")
            return BLOCK
    print(f"[guru-gate:check-commit] COMMIT_READY: staged scope matches latest clean implementation review（{task_dir}）")
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
    rest = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
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
    if cmd == "check-commit":
        return cmd_check_commit(arg)
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
