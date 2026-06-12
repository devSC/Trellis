#!/usr/bin/env python3
"""Guru 五阶段 Gate 校验 + 追溯矩阵（结构底线检查；语义判定由 review skill 人工 Gate 负责）。

用法:
  python3 guru_gate.py auto [task_dir]            # 按 task.json status + artifact 渐进校验（worktree.yaml verify 用这个）
  python3 guru_gate.py requirements <task_dir>    # 需求 Gate：prd.md（含 BHV 编号纪律）
  python3 guru_gate.py overview <task_dir>        # 概要 Gate：light=design.md §概要；full=设计包 design-main.md（结构+归属+索引）
  python3 guru_gate.py detail <task_dir>          # 详细 Gate：light=design.md §详细；full=chapters/*.md（章节闭合+pending L2 拦截）+ implement.md
  python3 guru_gate.py implement <task_dir>       # 实现 Gate：implement.md trace 四节（切片挂 UNIT）
  python3 guru_gate.py trace-matrix <task_dir> [--write] [--strict]
                                                  # 追溯矩阵：BHV × owner × UNIT × 测试 × 切片 + 孤儿清单
                                                  # --write 写入 <task_dir>/trace-matrix.md；--strict 有断链时 exit 2
  python3 guru_gate.py confirm [gate] [task_dir] [--via-agent]
                                                  # 人工确认 Gate（gate 省略=批量确认全部待确认阶段，逐个 y/n）
                                                  # strict 模式（默认）：仅限用户本人在交互式终端运行，agent 代跑被拒
                                                  # soft 模式（config guru.gate_mode: soft）：用户对话确认后 agent 以 --via-agent 代跑（记录留痕标注）
  python3 guru_gate.py status [task_dir]          # 查看三道人工 Gate 的确认状态与下一步
  python3 guru_gate.py check [task_dir]           # before_start 钩子用：复跑结构 Gate + 三道人工确认 + 确认快照比对，任一不满足 exit 2
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

import json
import os
import re
import sys

PASS, BLOCK = 0, 2

BHV_DEF = re.compile(r"^#{2,5}\s+(BHV-\d+)\b[^\n]*$", re.M)
UNIT_DEF = re.compile(r"^#{2,5}\s+(UNIT-[a-z0-9][a-z0-9-]*)\b[^\n]*$", re.M)
BHV_REF = re.compile(r"\b(BHV-\d+)\b")
UNIT_REF = re.compile(r"\b(UNIT-[a-z0-9][a-z0-9-]*)\b")

# 双轨制（完整五阶段链=目录级设计包；轻量链=单文件 design.md）
# V1_L2 / NINE_TYPES 与 detail-structure-single-source.md §2 同步维护。
V1_L2 = {"controller", "usecase", "repository-datasource"}
NINE_TYPES = V1_L2 | {"page-entry", "service", "db-dao", "api-network",
                      "config-l10n", "external-platform"}
DOC_TYPE_REF = re.compile(r"(?:detail_)?doc_type\s*[=:：]\s*`?([a-z][a-z-]*)`?")
CHAPTER_FILE_REF = re.compile(r"chapters/([A-Za-z0-9_][A-Za-z0-9_.-]*\.md)")
L2_EXEMPT_LINE = re.compile(r"L2豁免[^\n]*")


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


def _package_dir(task_dir: str):
    """full 链设计包路径（task.json design_package，相对 repo root）。

    拒绝 `..` 穿越与绝对路径（防止 gate 误读仓库外文件给出误导结论）；
    测试夹具可设 GURU_GATE_ALLOW_ABS=1 放行绝对路径。未声明/非法返回 None。
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
    repo_root = os.path.realpath(os.getcwd())
    real = os.path.realpath(norm)
    try:
        if os.path.commonpath([repo_root, real]) != repo_root:
            return None
    except ValueError:
        return None
    return norm


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


def _index_doc_types(main: str) -> set:
    """提取承接索引引用的 doc_type：兼容 `doc_type=X` 行内形式与表格行形式
    （表格行无 doc_type= 前缀，按九类 token 出现在索引上下文行识别）。"""
    hits = {t for t in DOC_TYPE_REF.findall(main) if t in NINE_TYPES}
    for line in main.splitlines():
        if "L2豁免" in line:
            continue
        if "chapters/" in line or "chapter_target" in line:
            for t in NINE_TYPES:
                if re.search(rf"\b{re.escape(t)}\b", line):
                    hits.add(t)
    return hits


def _check_pending_l2(task_dir: str) -> list:
    """pending L2 拦截：承接索引命中非 v1 doc_type 时必须在 design-main 显式 `L2豁免：<doc_type> 理由：…`。"""
    pkg = _package_dir(task_dir)
    if not pkg:
        return []
    main = read(os.path.join(pkg, "design-main.md"))
    hit = {t for t in _index_doc_types(main) if t not in V1_L2}
    exempted = set()
    for line in L2_EXEMPT_LINE.findall(main):
        # 豁免对象只从「理由」之前的声明段取词（且限九类 token）——
        # 理由文本里出现的类型词（如 "this service layer..."）不构成豁免
        head = line.split("理由", 1)[0]
        exempted.update(t for t in re.findall(r"[a-z][a-z-]*", head) if t in NINE_TYPES)
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
        if os.path.isdir(arg):
            return arg
        named = os.path.join(".trellis", "tasks", arg)  # 裸任务名
        return named if os.path.isdir(named) else None
    # before_start 钩子注入 TASK_JSON_PATH（最可靠：指向正要 start 的任务）
    tj = os.environ.get("TASK_JSON_PATH", "")
    if tj and os.path.isfile(tj):
        return os.path.dirname(tj)
    import subprocess
    try:
        out = subprocess.run(["python3", ".trellis/scripts/task.py", "current"],
                             capture_output=True, text=True, timeout=15).stdout.strip()
        m = re.search(r"(\.trellis/tasks/\S+)", out)
        if m and os.path.isdir(m.group(1)):
            return m.group(1)
    except Exception:
        pass
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
# 人工 Gate（confirm / status / check）
# =========================================================================
# 设计：阶段跃迁（需求→概要→详细→实现）必须由用户本人确认。confirm 强制 TTY +
# 交互输入，agent 经工具管道运行必然无 TTY 而被拒；确认落盘 task.json 的
# guru_gates 键；task.py start 经 before_start 钩子跑 check，缺确认即中止。

HUMAN_GATES = ("requirements", "overview", "detail")
GATE_LABEL = {"requirements": "需求", "overview": "概要设计", "detail": "详细设计"}
GATES_KEY = "guru_gates"


def _gate_artifacts(task_dir: str, gate: str) -> list:
    """各阶段人工确认所覆盖的产物文件（确认快照的取材范围）。

    快照是**累积的**：下游阶段包含上游产物——上游（如 prd）改动后即使只重确认上游，
    下游确认也会失配并要求重新确认（下游评审基于的上游语义已变）。
    """
    full = task_chain(task_dir) == "full"
    pkg = _package_dir(task_dir)
    req_files = [os.path.join(task_dir, "prd.md")]
    if gate == "requirements":
        return req_files
    if full and pkg:
        # README 属包骨架（导航/追踪矩阵入口），同样纳入确认快照
        ov_files = req_files + [os.path.join(pkg, "README.md"), os.path.join(pkg, "design-main.md")]
    else:
        ov_files = req_files + [os.path.join(task_dir, "design.md")]
    if gate == "overview":
        return ov_files
    # detail：全链累积
    if full and pkg:
        dt_files = [os.path.join(pkg, "chapters", n) for n in _chapter_files(pkg)]
    else:
        dt_files = []  # light 链 design.md 已在 ov_files 中
    dt_files.append(os.path.join(task_dir, "implement.md"))
    seen, ordered = set(), []
    for p in ov_files + dt_files:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


def _gate_digest(task_dir: str, gate: str) -> str:
    """确认快照摘要：按文件名（basename）排序后串接内容做 sha256。
    只掺入 basename 不掺入完整路径——confirm（用户终端相对路径）与
    check（before_start 注入绝对路径）的调用形态不同，完整路径会导致假失配。"""
    import hashlib
    h = hashlib.sha256()
    for p in sorted(_gate_artifacts(task_dir, gate), key=os.path.basename):
        h.update(os.path.basename(p).encode("utf-8"))
        h.update(b"\0")
        h.update(read(p).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def _developer_name() -> str:
    for line in read(os.path.join(".trellis", ".developer")).splitlines():
        if line.startswith("name="):
            return line[len("name="):].strip()
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


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
    cfg = read(os.path.join(".trellis", "config.yaml"))
    # 只认顶层 guru: 块内的 gate_mode（防止其他配置节的同名键误开 soft）
    guru = re.search(r"(?ms)^guru\s*:\s*\n(?P<body>(?:^[ \t]+[^\n]*\n?)*)", cfg)
    if guru:
        m = re.search(r"(?m)^[ \t]+gate_mode\s*:\s*(soft|strict)\b", guru.group("body"))
        if m:
            return m.group(1)
    return "strict"


def _record_confirm(task_dir: str, gate: str, via: str, user_quote=None) -> int:
    """写入单个 Gate 的确认记录（严格 JSON 守卫 + 原子写）。via ∈ tty|agent。"""
    from datetime import datetime
    # confirm 是写路径：task.json 内容非法时拒绝写入（_task_json_of 的宽容 {} 会冲掉原有元数据）
    raw = read(os.path.join(task_dir, "task.json"))
    if raw.strip():
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"[guru-gate:confirm] task.json 格式非法，拒绝写入确认：{e}\n")
            return BLOCK
        if not isinstance(data, dict):
            sys.stderr.write("[guru-gate:confirm] task.json 根节点必须是对象，拒绝写入确认\n")
            return BLOCK
    else:
        data = {}
    gates = data.setdefault(GATES_KEY, {})
    record = {
        "confirmed_by": _developer_name(),
        "confirmed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        # 确认快照：check 时比对，产物在确认后被修改 → 要求重新确认
        "artifact_digest": _gate_digest(task_dir, gate),
    }
    if via == "agent":
        record["mode"] = "soft"
        record["via"] = "agent"  # 留痕：对话确认、agent 代跑（非 TTY 人手证明）
        if user_quote:
            record["user_quote"] = user_quote[:500]  # 用户确认原话（审计：伪造须编造用户言论）
    gates[gate] = record
    tj_path = os.path.join(task_dir, "task.json")
    # 原子写：中断不留半截 task.json（与 guru_after_create 同一模式）
    tmp_path = f"{tj_path}.tmp.{os.getpid()}"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, tj_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    suffix = "（soft：对话确认，agent 代跑）" if via == "agent" else ""
    print(f"[guru-gate:confirm] ✅ {GATE_LABEL[gate]} Gate 已由 {record['confirmed_by']} 确认{suffix}（已写入 {tj_path}）")
    return PASS


def _pending_gates(task_dir: str) -> list:
    """按阶段顺序列出待确认 Gate（未确认 / 缺快照 / 快照失配）。"""
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
        sys.stderr.write(f"[guru-gate:confirm] 未知 gate: {gate_arg}（可选: {', '.join(HUMAN_GATES)}；省略=批量确认全部待确认 Gate）\n")
        return BLOCK
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:confirm] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    mode = _gate_mode()
    if not interactive and not (mode == "soft" and via_agent):
        sys.stderr.write(
            f"[guru-gate:confirm] 拒绝：strict 模式下人工 Gate 确认必须由用户本人在交互式终端执行（当前无 TTY）。\n"
            f"agent 不得代为确认。请提示用户在自己的终端运行：\n"
            f"  python3 .trellis/scripts/guru/guru_gate.py confirm\n"
            f"（项目可在 .trellis/config.yaml 设 guru.gate_mode: soft 改为对话确认后 agent --via-agent 代跑）\n"
        )
        return BLOCK
    if not interactive and not (user_quote and user_quote.strip()):
        # soft 代跑的审计底线：必须留用户确认原话，否则留痕失去意义
        sys.stderr.write(
            "[guru-gate:confirm] soft 模式 agent 代跑必须带 --user-quote \"<用户确认原话>\" 记录审计留痕\n"
        )
        return BLOCK
    targets = [gate_arg] if gate_arg else _pending_gates(task_dir)
    if not targets:
        print(f"[guru-gate:confirm] 三道人工 Gate 均已确认且快照一致（{task_dir}），无需操作")
        return PASS
    print(f"任务：{task_dir}（gate_mode={mode}）")
    checkers = {"requirements": check_requirements, "overview": check_overview, "detail": check_detail}
    for g in targets:
        # 结构 Gate 未过时确认无意义，先拦下（批量模式停在首个未过阶段）
        if checkers[g](task_dir) != PASS:
            sys.stderr.write(f"[guru-gate:confirm] {GATE_LABEL[g]}结构 Gate 未过，先修复缺口再确认；本次到此为止。\n")
            return BLOCK
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


def _gate_states(task_dir: str) -> dict:
    gates = _task_json_of(task_dir).get(GATES_KEY)
    return gates if isinstance(gates, dict) else {}


def cmd_status(task_dir_arg) -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:status] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    states = _gate_states(task_dir)
    print(f"任务：{task_dir}")
    pending = []
    for g in HUMAN_GATES:
        s = states.get(g)
        if isinstance(s, dict) and s.get("confirmed_by"):
            # 与 check 同口径呈现快照状态——避免 status 报绿而 check 拦截的不一致
            recorded = s.get("artifact_digest")
            if not recorded:
                pending.append(g)
                print(f"  ⚠️ {GATE_LABEL[g]} Gate — 缺确认快照，请重新确认")
            elif recorded != _gate_digest(task_dir, g):
                pending.append(g)
                print(f"  ⚠️ {GATE_LABEL[g]} Gate — 确认快照失配（产物已改动），请重新确认")
            else:
                soft_mark = "（soft：对话确认，agent 代跑）" if s.get("via") == "agent" else ""
                print(f"  ✅ {GATE_LABEL[g]} Gate — {s['confirmed_by']} @ {s.get('confirmed_at', '?')}{soft_mark}")
        else:
            pending.append(g)
            print(f"  ⬜ {GATE_LABEL[g]} Gate — 未确认")
    if pending:
        print(f"下一步：完成 {GATE_LABEL[pending[0]]} 阶段 review 后，由用户本人在终端运行：")
        print(f"  python3 .trellis/scripts/guru/guru_gate.py confirm {pending[0]} {task_dir}")
    else:
        print("三道人工 Gate 已全部确认，可 task.py start 进入实现。")
    return PASS


def cmd_check(task_dir_arg) -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        # check 是阻断闸门：定位不到任务即拒绝（与"任一不满足 exit 2"的合同一致）。
        # before_start 注入 TASK_JSON_PATH、hook 透传命令参数，正常路径都可定位。
        sys.stderr.write("[guru-gate:check] 无法定位任务目录，请显式传 task_dir 或确保 TASK_JSON_PATH 已注入\n")
        return BLOCK
    # 结构 Gate 复跑：防止"确认后再改产物"带病 start（确认只代表确认时点的状态）
    for gate, checker in (("requirements", check_requirements),
                          ("overview", check_overview),
                          ("detail", check_detail)):
        if checker(task_dir) != PASS:
            sys.stderr.write(f"[guru-gate:check] 拦截：{GATE_LABEL[gate]}结构 Gate 当前未通过"
                             f"（产物在确认后被修改？）。修复后请用户重新人工确认该阶段。\n")
            return BLOCK
    states = _gate_states(task_dir)
    missing = [g for g in HUMAN_GATES
               if not (isinstance(states.get(g), dict) and states[g].get("confirmed_by"))]
    if missing:
        sys.stderr.write(f"[guru-gate:check] 拦截：人工 Gate 未全部确认（任务 {task_dir}）：\n")
        for g in missing:
            sys.stderr.write(f"  ⬜ {GATE_LABEL[g]} Gate 未确认\n")
        sys.stderr.write(
            "阶段跃迁确认必须由用户本人在交互式终端执行（agent 代跑会因无 TTY 被拒）：\n"
            f"  python3 .trellis/scripts/guru/guru_gate.py confirm {missing[0]} {task_dir}\n"
        )
        return BLOCK
    # 确认快照比对：缺快照（手写/旧版确认记录）或失配（确认后产物被修改）→ 要求重新人工确认
    stale = []
    for g in HUMAN_GATES:
        recorded = states[g].get("artifact_digest")
        if not recorded:
            stale.append((g, "缺确认快照（确认必须经 guru_gate.py confirm 产生）"))
        elif recorded != _gate_digest(task_dir, g):
            stale.append((g, "确认快照失配（产物在确认后被修改）"))
    if stale:
        sys.stderr.write(f"[guru-gate:check] 拦截：确认快照校验未通过（任务 {task_dir}）：\n")
        for g, reason in stale:
            sys.stderr.write(f"  ⚠️ {GATE_LABEL[g]} Gate {reason}\n")
        sys.stderr.write(
            f"请复核改动并由用户本人重新人工确认：\n"
            f"  python3 .trellis/scripts/guru/guru_gate.py confirm {stale[0][0]} {task_dir}\n"
        )
        return BLOCK
    print(f"[guru-gate:check] 三道人工 Gate 已全部确认且快照一致（{task_dir}），放行")
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
        src = _artifact_sources(task_dir)
        full = task_chain(task_dir) == "full"
        # full 链：design_package 已声明即校验骨架（声明但损坏不得静默跳过）；
        # 未声明属概要阶段 0 待办——渐进语义下放行但显式提示，不静默。
        if src["overview"] or (full and _package_dir(task_dir)):
            rc = check_overview(task_dir)
            if rc != PASS:
                return rc
            if src["detail"] or src["imp"]:
                return check_detail(task_dir)
        note = "；full 链尚未声明 design_package（概要阶段 0 待办）" if full and not _package_dir(task_dir) else ""
        return ok("auto", f"planning 渐进校验到当前 artifact（{task_dir}，{task_chain(task_dir)} 链{note}）")
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
    argv = list(sys.argv[2:])
    # --user-quote 带值：先摘出值，避免污染位置参数
    user_quote = None
    if "--user-quote" in argv:
        qi = argv.index("--user-quote")
        if qi + 1 < len(argv):
            user_quote = argv[qi + 1]
            del argv[qi:qi + 2]
        else:
            del argv[qi]
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
        if rest and rest[0] in HUMAN_GATES:
            gate_arg, dir_arg = rest[0], (rest[1] if len(rest) > 1 else None)
        else:
            gate_arg, dir_arg = None, (rest[0] if rest else None)
        return cmd_confirm(gate_arg, dir_arg, via_agent="--via-agent" in flags, user_quote=user_quote)
    if cmd == "digest":
        if not rest or rest[0] not in HUMAN_GATES:
            sys.stderr.write(f"[guru-gate:digest] 需要 gate 参数（{', '.join(HUMAN_GATES)}）\n")
            return BLOCK
        task_dir = resolve_task_dir(rest[1] if len(rest) > 1 else None)
        if not task_dir:
            sys.stderr.write("[guru-gate:digest] 无法定位任务目录\n")
            return BLOCK
        print(_gate_digest(task_dir, rest[0]))
        return PASS
    if cmd == "status":
        return cmd_status(arg)
    if cmd == "check":
        return cmd_check(arg)
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
