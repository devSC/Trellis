#!/usr/bin/env python3
"""Guru 五阶段 Gate 校验 + 追溯矩阵（结构底线检查；语义判定由 review skill 人工 Gate 负责）。

用法:
  python3 guru_gate.py auto [task_dir]            # 按 task.json status + artifact 渐进校验（worktree.yaml verify 用这个）
  python3 guru_gate.py requirements <task_dir>    # 需求 Gate：prd.md（含 BHV 编号纪律）
  python3 guru_gate.py overview <task_dir>        # 概要 Gate：design.md §概要（归属表引用 BHV）
  python3 guru_gate.py detail <task_dir>          # 详细 Gate：design.md §详细（UNIT 编号 + 承接断链拦截）+ implement.md
  python3 guru_gate.py implement <task_dir>       # 实现 Gate：implement.md trace 四节（切片挂 UNIT）
  python3 guru_gate.py trace-matrix <task_dir> [--write] [--strict]
                                                  # 追溯矩阵：BHV × owner × UNIT × 测试 × 切片 + 孤儿清单
                                                  # --write 写入 <task_dir>/trace-matrix.md；--strict 有断链时 exit 2

编号纪律:
  BHV-NNN   行为编号。prd.md 中以标题定义（如 `### BHV-001 玩家选择 Hammer`）；创建后不复用、不重排，删除留洞。
  UNIT-slug 设计单元编号。design.md §2 中以标题定义（如 `### UNIT-hammer-usecase`）；语义 slug。
  下游引用一律写裸编号（兼容未来的 [[file#BHV-001]] 双链包裹——解析按编号 token 识别）。

退出码: 0=通过/合法跳过; 2=Gate 拦截(stderr 给缺口清单)。
设计约束: 只查结构存在性与引用闭合, 不做语义判断——"判不动的规则不进脚本"。
"""

import json
import os
import re
import sys

PASS, BLOCK = 0, 2

BHV_DEF = re.compile(r"^#{2,5}\s+(BHV-\d+)\b[^\n]*$", re.M)
UNIT_DEF = re.compile(r"^#{2,5}\s+(UNIT-[a-z0-9][a-z0-9-]*)\b[^\n]*$", re.M)
BHV_REF = re.compile(r"\b(BHV-\d+)\b")
UNIT_REF = re.compile(r"\b(UNIT-[a-z0-9][a-z0-9-]*)\b")


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


def _design_sections(design: str):
    """切出概要章与详细章正文（按 § 或章节标题启发式）。"""
    m = re.search(r"(?:§\s*2|##\s*(?:§?\s*2|详细设计))", design)
    if m:
        return design[: m.start()], design[m.start():]
    return design, ""


# =========================================================================
# 追溯模型
# =========================================================================

def build_trace(task_dir: str) -> dict:
    """扫描产物构建追溯模型。返回:
    behaviors: {bhv: 短名}; units: {unit: {"behaviors":[...], "tests": bool, "owner_hint": str}};
    owners: {bhv: owner 行文本}; slices: {unit: [切片行]}; orphans: {...断链清单}
    """
    prd = read(os.path.join(task_dir, "prd.md"))
    design = read(os.path.join(task_dir, "design.md"))
    imp = read(os.path.join(task_dir, "implement.md"))
    overview, detail = _design_sections(design)

    behaviors = {}
    for m in BHV_DEF.finditer(prd):
        line = m.group(0)
        behaviors[m.group(1)] = re.sub(r"^#{2,5}\s+BHV-\d+\s*", "", line).strip() or "(未命名)"

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
    return {"behaviors": behaviors, "owners": owners, "units": units, "slices": slices, "orphans": orphans}


def render_matrix(t: dict) -> str:
    lines = ["# 追溯矩阵（机器生成，勿手编）", "",
             "| 行为 | 名称 | 归属（§1） | 承接单元（§2） | 测试映射 | 实现切片 |",
             "|------|------|-----------|---------------|---------|---------|"]
    unit_by_bhv = {}
    for u, d in t["units"].items():
        for b in d["behaviors"]:
            unit_by_bhv.setdefault(b, []).append(u)
    for b, name in sorted(t["behaviors"].items()):
        us = unit_by_bhv.get(b, [])
        tests = "✅" if us and all(t["units"][u]["tests"] for u in us) else ("⚠️" if us else "—")
        sl = "✅" if us and all(u in t["slices"] for u in us) else ("⚠️" if us else "—")
        lines.append(f"| {b} | {name} | {'✅' if b in t['owners'] else '❌'} | {', '.join(us) or '❌ 无承接'} | {tests} | {sl} |")
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


def cmd_trace_matrix(task_dir: str, write: bool, strict: bool) -> int:
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
    return PASS


# =========================================================================
# 五阶段 Gate
# =========================================================================

def check_requirements(task_dir: str) -> int:
    """需求 Gate：行为规格(BHV 编号标题) / P0 P1 / 失败路径 / 验收 / 未决问题。"""
    prd = read(os.path.join(task_dir, "prd.md"))
    problems = []
    if not prd:
        return fail("requirements", ["prd.md 不存在或为空"])
    if not BHV_DEF.search(prd):
        problems.append("缺行为编号：行为须以 `### BHV-NNN <短名>` 标题定义（编号纪律）")
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


def check_overview(task_dir: str) -> int:
    """概要 Gate：归属表（引用 BHV 编号）+ 三问理由 + 承接索引。"""
    design = read(os.path.join(task_dir, "design.md"))
    problems = []
    if not design:
        return fail("overview", ["design.md 不存在或为空（概要设计未开始）"])
    overview, _ = _design_sections(design)
    if not re.search(r"概要设计|§\s*1", overview):
        problems.append("缺概要设计章（§1）标题")
    if not re.search(r"owner|归属", overview):
        problems.append("缺行为→owner 归属表")
    if not BHV_REF.search(overview):
        problems.append("归属表未引用 BHV 编号（追溯断点：归属必须按行为编号逐条）")
    if not re.search(r"为什么属于|归属理由|三问", overview):
        problems.append("归属表缺三问理由（为什么属于它/不属于别人/是否需独立存在）")
    if not re.search(r"承接索引|doc_type", overview):
        problems.append("缺详细设计承接索引（chapter_target → doc_type）")
    return fail("overview", problems) if problems else ok("overview")


def check_detail(task_dir: str) -> int:
    """详细 Gate：UNIT 编号 + 合同八问标记 + implement.md + 承接断链拦截。"""
    design = read(os.path.join(task_dir, "design.md"))
    problems = []
    if not design:
        return fail("detail", ["design.md 不存在"])
    _, detail = _design_sections(design)
    if not detail:
        problems.append("缺详细设计章（§2）")
    else:
        if not UNIT_DEF.search(detail):
            problems.append("缺设计单元编号：单元须以 `### UNIT-<slug>` 标题定义（编号纪律）")
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


def resolve_task_dir(arg):
    if arg:
        return arg if os.path.isdir(arg) else None
    import subprocess
    try:
        out = subprocess.run(["python3", ".trellis/scripts/task.py", "current"],
                             capture_output=True, text=True, timeout=15).stdout.strip()
        m = re.search(r"(\.trellis/tasks/\S+)", out)
        if m and os.path.isdir(m.group(1)):
            return m.group(1)
    except Exception:
        pass
    return None


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
        if read(os.path.join(task_dir, "design.md")):
            rc = check_overview(task_dir)
            if rc != PASS:
                return rc
            _, detail = _design_sections(read(os.path.join(task_dir, "design.md")))
            if detail or read(os.path.join(task_dir, "implement.md")):
                return check_detail(task_dir)
        return ok("auto", f"planning 渐进校验到当前 artifact（{task_dir}）")
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
    rest = [a for a in sys.argv[2:] if not a.startswith("--")]
    flags = {a for a in sys.argv[2:] if a.startswith("--")}
    arg = rest[0] if rest else None
    table = {
        "requirements": check_requirements,
        "overview": check_overview,
        "detail": check_detail,
        "implement": check_implement,
    }
    if cmd == "auto":
        return auto(arg)
    if cmd == "trace-matrix":
        if not arg or not os.path.isdir(arg):
            sys.stderr.write("[guru-gate:trace-matrix] 需要有效 task_dir 参数\n")
            return BLOCK
        return cmd_trace_matrix(arg, "--write" in flags, "--strict" in flags)
    if cmd in table:
        if not arg or not os.path.isdir(arg):
            sys.stderr.write(f"[guru-gate:{cmd}] 需要有效 task_dir 参数\n")
            return BLOCK
        return table[cmd](arg)
    sys.stderr.write(f"未知子命令: {cmd}\n{__doc__}")
    return BLOCK


if __name__ == "__main__":
    sys.exit(main())
