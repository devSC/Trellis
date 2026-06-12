#!/usr/bin/env python3
"""Guru 五阶段 Gate 校验（结构底线检查；语义判定由 review skill 人工 Gate 负责）。

用法:
  python3 guru_gate.py auto [task_dir]          # 按 task.json status + artifact 渐进校验（worktree.yaml verify 用这个）
  python3 guru_gate.py requirements <task_dir>  # 需求 Gate：prd.md
  python3 guru_gate.py overview <task_dir>      # 概要 Gate：design.md §概要
  python3 guru_gate.py detail <task_dir>        # 详细 Gate：design.md §详细 + implement.md
  python3 guru_gate.py implement <task_dir>     # 实现 Gate：implement.md trace 四节

退出码: 0=通过/合法跳过; 2=Gate 拦截(stderr 给缺口清单)。
设计约束: 只查结构存在性(章节/标记), 不做语义判断——"判不动的规则不进脚本"。
"""

import json
import os
import re
import sys

PASS, BLOCK = 0, 2


def fail(gate: str, problems: list) -> int:
    sys.stderr.write(f"[guru-gate:{gate}] 未通过，缺口：\n")
    for p in problems:
        sys.stderr.write(f"  - {p}\n")
    sys.stderr.write("修复后重试；语义级判定请走对应 review skill 的人工 Gate。\n")
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


def check_requirements(task_dir: str) -> int:
    """需求 Gate：行为规格 / P0 P1 / 失败路径 / 验收 / 未决问题 五要素。"""
    prd = read(os.path.join(task_dir, "prd.md"))
    problems = []
    if not prd:
        return fail("requirements", ["prd.md 不存在或为空"])
    if not (re.search(r"\bGiven\b", prd) and re.search(r"\bWhen\b", prd) and re.search(r"\bThen\b", prd)):
        problems.append("缺行为规格：未找到 Given/When/Then 三段式（至少一组）")
    if not re.search(r"\bP0\b|\bP1\b", prd):
        problems.append("缺核心能力清单：未找到 P0/P1 优先级标记")
    if not re.search(r"失败路径|失败场景|异常路径|failure", prd, re.I):
        problems.append("缺失败路径章节")
    if not re.search(r"验收|acceptance", prd, re.I):
        problems.append("缺验收场景/标准章节")
    if not re.search(r"未决|open question|待确认", prd, re.I):
        problems.append("缺未决问题章节（无未决也须显式声明）")
    return fail("requirements", problems) if problems else ok("requirements")


def _design_sections(design: str):
    """切出概要章与详细章正文（按 § 或章节标题启发式）。"""
    m = re.search(r"(?:§\s*2|##\s*(?:§?\s*2|详细设计))", design)
    if m:
        return design[: m.start()], design[m.start():]
    return design, ""


def check_overview(task_dir: str) -> int:
    """概要 Gate：归属表 + 三问理由 + 承接索引。"""
    design = read(os.path.join(task_dir, "design.md"))
    problems = []
    if not design:
        return fail("overview", ["design.md 不存在或为空（概要设计未开始）"])
    overview, _ = _design_sections(design)
    if not re.search(r"概要设计|§\s*1", overview):
        problems.append("缺概要设计章（§1）标题")
    if not re.search(r"owner|归属", overview):
        problems.append("缺行为→owner 归属表")
    if not re.search(r"为什么属于|归属理由|三问", overview):
        problems.append("归属表缺三问理由（为什么属于它/不属于别人/是否需独立存在）")
    if not re.search(r"承接索引|doc_type", overview):
        problems.append("缺详细设计承接索引（chapter_target → doc_type）")
    return fail("overview", problems) if problems else ok("overview")


def check_detail(task_dir: str) -> int:
    """详细 Gate：合同八问关键标记 + implement.md（trace §1）。"""
    design = read(os.path.join(task_dir, "design.md"))
    problems = []
    if not design:
        return fail("detail", ["design.md 不存在"])
    _, detail = _design_sections(design)
    if not detail:
        problems.append("缺详细设计章（§2）")
    else:
        for label, pat in [
            ("承接行为（八问之1）", r"承接.{0,6}行为"),
            ("失败收口（八问之5）", r"失败.{0,6}收口|失败如何"),
            ("测试映射（八问之7）", r"测试映射|哪些测试"),
            ("不得补造声明（八问之8）", r"不得.{0,6}补造|不在此补造"),
        ]:
            if not re.search(pat, detail):
                problems.append(f"详细章缺{label}")
    if not read(os.path.join(task_dir, "implement.md")):
        problems.append("implement.md（trace §1 实现计划）不存在")
    return fail("detail", problems) if problems else ok("detail")


def check_implement(task_dir: str) -> int:
    """实现 Gate：trace 四节齐全（项目级 analyze/test 命令由 worktree.yaml 其余 verify 条目执行）。"""
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
    return fail("implement", problems) if problems else ok("implement")


def resolve_task_dir(arg: str | None) -> str | None:
    if arg:
        return arg if os.path.isdir(arg) else None
    # auto 模式：尝试 task.py current
    import subprocess
    for cmd in (["python3", ".trellis/scripts/task.py", "current"],):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip()
            m = re.search(r"(\.trellis/tasks/\S+)", out)
            if m and os.path.isdir(m.group(1)):
                return m.group(1)
        except Exception:
            pass
    return None


def auto(task_dir_arg: str | None) -> int:
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
        # 渐进：按 artifact 存在性查到当前最远一步（早期阶段未到的步骤不拦）
        rc = check_requirements(task_dir)
        if rc != PASS:
            return rc
        if read(os.path.join(task_dir, "design.md")):
            rc = check_overview(task_dir)
            if rc != PASS:
                return rc
            _, detail = _design_sections(read(os.path.join(task_dir, "design.md")))
            if detail or read(os.path.join(task_dir, "implement.md")):
                return check_detail(task_dir)
        return ok("auto", f"planning 渐进校验到当前 artifact（{task_dir}）")
    # in_progress / 其他：实现 Gate
    for fn in (check_requirements, check_overview, check_detail, check_implement):
        rc = fn(task_dir)
        if rc != PASS:
            return rc
    return ok("auto", f"status={status} 全 Gate 通过")


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write(__doc__ or "")
        return BLOCK
    cmd = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    table = {
        "requirements": check_requirements,
        "overview": check_overview,
        "detail": check_detail,
        "implement": check_implement,
    }
    if cmd == "auto":
        return auto(arg)
    if cmd in table:
        if not arg or not os.path.isdir(arg):
            sys.stderr.write(f"[guru-gate:{cmd}] 需要有效 task_dir 参数\n")
            return BLOCK
        return table[cmd](arg)
    sys.stderr.write(f"未知子命令: {cmd}\n{__doc__}")
    return BLOCK


if __name__ == "__main__":
    sys.exit(main())
