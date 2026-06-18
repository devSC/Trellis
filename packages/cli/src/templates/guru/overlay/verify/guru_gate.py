#!/usr/bin/env python3
"""Guru 五阶段 Gate 校验 + 追溯矩阵（结构底线检查；语义判定由 review loop 负责）。

Gate 确认模型 SSOT：.trellis/spec/harness/gate/gate-confirmation-model.md

用法:
  python3 guru_gate.py auto [task_dir]            # 按 task.json status + artifact 渐进校验（worktree.yaml verify 用这个）
  python3 guru_gate.py requirements <task_dir>    # 需求 Gate：prd.md（含 BHV 编号纪律）
  python3 guru_gate.py overview <task_dir>        # 概要 Gate：light=design.md §概要；full=设计包 design-main.md（结构+归属+索引）
  python3 guru_gate.py detail <task_dir>          # 详细 Gate：light=design.md §详细；full=chapters/*.md（章节闭合+pending L2 拦截）+ implement.md
  python3 guru_gate.py implement <task_dir>       # 实现 Gate：implement.md trace 四节（切片挂 UNIT）
  python3 guru_gate.py trace-matrix <task_dir> [--write] [--strict]
                                                  # 追溯矩阵：BHV × owner × UNIT × 测试 × 切片 + 孤儿清单
                                                  # --write 写入 <task_dir>/trace-matrix.md；--strict 有断链时 exit 2
  python3 guru_gate.py confirm [requirements|detail] [task_dir] [--via-agent]
                                                  # 人工确认 Gate（需求确认 + 详细设计 review 双 clean 后确认）
                                                  # strict 模式（默认）：仅限用户本人在交互式终端运行，agent 代跑被拒
                                                  # soft 模式（config guru.gate_mode: soft）：用户对话确认后 agent 以 --via-agent 代跑（记录留痕标注）
  python3 guru_gate.py record-review <overview|detail> <task_dir> --result clean|findings --max-severity none|low|medium|high|critical --reviewer clean-context --run-id <id> --evidence <text> [--finding-class <class>]
                                                  # 记录概要/详细设计 review 证据；当前产物 digest 下需两个不同 run-id 的 clean 记录
  python3 guru_gate.py grill-done <gate> [task_dir] [--via-agent] --user-quote "<用户确认原话>"
                                                  # 兼容旧流程：记录 design-grill 已完成（不再作为新 gate 放行条件）
  python3 guru_gate.py grill-skip <gate> [task_dir] [--via-agent] --user-quote "<跳过理由>"
                                                  # 兼容旧流程：仅 low-risk 非 full 的 overview/detail 可跳过（留原因）
  python3 guru_gate.py status [task_dir]          # 查看需求确认、概要/详细 review 证据、详细确认状态与下一步
  python3 guru_gate.py check [task_dir]           # before_start 钩子用：结构 Gate + review_runs 证据 + 人工确认快照，任一不满足 exit 2
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

# 不用 \b 词边界：Python 的 \b 把 CJK 视作 word 字符，"执行BHV-001"/"UNIT-x执行" 等
# 中文相邻编号会因边界失配被漏掉，导致 trace 误判孤儿（假拦/假通过）。
# DEF 靠行首标题(^#{2,5}\s+)锚定；REF 直匹配编号本体。slug 首字符限 [a-z]（语义 slug 字母起头）。
BHV_DEF = re.compile(r"^#{2,5}\s+(BHV-\d+)[^\n]*$", re.M)
UNIT_DEF = re.compile(r"^#{2,5}\s+(UNIT-[a-z][a-z0-9-]*)[^\n]*$", re.M)
BHV_REF = re.compile(r"(BHV-\d+)")
UNIT_REF = re.compile(r"(UNIT-[a-z][a-z0-9-]*)")

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
REQUIRED_CLEAN_REVIEWS = 2
SEVERITY_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
FINDING_CLASSES = {
    "REQ_BLOCKER",
    "OVERVIEW_DEFECT",
    "DETAIL_DEFECT",
    "IMPLEMENT_DEFECT",
    "PROCESS_DEFECT",
}
HIGH_RISK_LEVELS = {"high", "critical", "p0"}
LOW_RISK_LEVELS = {"low", "minor", "trivial"}


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


def _risk_level(task_dir: str) -> str:
    """读取任务风险等级。缺失/不可判定按 unknown 处理，避免 light 链自动获得 skip 权限。"""
    data = _task_json_of(task_dir)
    candidates = [
        data.get("risk_level"),
        data.get("guru_risk_level"),
    ]
    for key in ("guru_risk", "risk"):
        risk_obj = data.get(key)
        if isinstance(risk_obj, dict):
            if risk_obj.get("high_risk") is True:
                return "high"
            if risk_obj.get("low_risk") is True:
                return "low"
            candidates.extend([risk_obj.get("risk_level"), risk_obj.get("level")])
        elif isinstance(risk_obj, str):
            candidates.append(risk_obj)
    for value in candidates:
        if not isinstance(value, str):
            continue
        level = value.strip().lower().replace("_", "-")
        if level in HIGH_RISK_LEVELS:
            return "high"
        if level in LOW_RISK_LEVELS:
            return "low"
    return "unknown"


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
    duplicate_clean_run_ids = []
    latest_blocker = None
    for run in current_runs:
        error = _review_run_validation_error(run)
        if error:
            latest_blocker = {"run_id": run.get("run_id", "?"), "reason": error}
            clean_run_ids = []
            continue
        if _review_run_is_clean(run):
            run_id = str(run.get("run_id", "")).strip()
            if run_id not in clean_run_ids:
                clean_run_ids.append(run_id)
            else:
                duplicate_clean_run_ids.append(run_id)
            continue
        latest_blocker = run
        clean_run_ids = []
    ready = len(clean_run_ids) >= REQUIRED_CLEAN_REVIEWS
    return {
        "digest": digest,
        "runs": current_runs,
        "stale_run_count": len(stale_runs),
        "latest_stale_digest": stale_runs[-1].get("artifact_digest") if stale_runs else "",
        "clean_run_ids": clean_run_ids,
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
        return f"review ✅ clean x{state['clean_count']} ({ids})"
    problem = _review_problem(task_dir, gate)
    return f"review ⬜ {state['clean_count']}/{REQUIRED_CLEAN_REVIEWS} clean — {problem}"


def _block_review(channel: str, task_dir: str, gate: str) -> int:
    route_guidance = _review_route_guidance(task_dir, gate)
    if route_guidance:
        sys.stderr.write(
            f"[guru-gate:{channel}] 拦截：{GATE_LABEL[gate]} review 路由上游："
            f"{_review_problem(task_dir, gate)}\n"
        )
        sys.stderr.write(f"下一步：{route_guidance}\n")
        return BLOCK
    sys.stderr.write(
        f"[guru-gate:{channel}] 拦截：{GATE_LABEL[gate]} Gate 缺少当前产物的双 clean review 证据："
        f"{_review_problem(task_dir, gate)}\n"
    )
    sys.stderr.write(
        "由 review worker 记录两次不同 run-id 的 clean 证据：\n"
        f"  python3 .trellis/scripts/guru/guru_gate.py record-review {gate} {task_dir} "
        "--result clean --max-severity low --reviewer clean-context --run-id <id> --evidence \"<review证据>\"\n"
    )
    return BLOCK


def _record_review(task_dir: str, gate: str, options: dict) -> int:
    if gate not in REVIEW_GATES:
        sys.stderr.write(
            f"[guru-gate:record-review] 只支持 {', '.join(REVIEW_GATES)}；requirements 只走人工确认，不记录 clean streak\n"
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
        # 确认快照：check 时比对，产物在确认后被修改 → 要求重新确认
        "artifact_digest": _gate_digest(task_dir, gate),
    }
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


def cmd_status(task_dir_arg) -> int:
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:status] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    states = _gate_states(task_dir)
    print(f"任务：{task_dir}")
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
                print(f"  ✅ {GATE_LABEL[g]} Gate — {s['confirmed_by']} @ {s.get('confirmed_at', '?')}{soft_mark}")
        else:
            confirm_pending.append(g)
            print(f"  ⬜ {GATE_LABEL[g]} Gate — 未确认")

    review_pending = []
    for g in REVIEW_GATES:
        mark = _review_status_mark(task_dir, g)
        print(f"  {GATE_LABEL[g]} Review — {mark} ｜ legacy {_grill_status_mark(task_dir, g)}")
        if not _review_state(task_dir, g)["ready"]:
            review_pending.append(g)

    if "requirements" in confirm_pending:
        print("下一步：完成需求 review 后，由用户本人在终端运行：")
        print(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}")
    elif review_pending:
        g0 = review_pending[0]
        route_guidance = _review_route_guidance(task_dir, g0)
        if route_guidance:
            print(f"下一步：{route_guidance}")
            return PASS
        print(f"下一步：继续 {GATE_LABEL[g0]} review，当前 digest 需要两个不同 run-id 的 clean 记录：")
        print(
            f"  python3 .trellis/scripts/guru/guru_gate.py record-review {g0} {task_dir} "
            "--result clean --max-severity low --reviewer clean-context --run-id <id> --evidence \"<review证据>\""
        )
    elif "detail" in confirm_pending:
        print("下一步：详细设计已双 clean，由用户本人在终端运行：")
        print(f"  python3 .trellis/scripts/guru/guru_gate.py confirm detail {task_dir}")
    else:
        print("需求确认、概要/详细双 clean review、详细确认均已完成，可 task.py start 进入实现。")
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
                             f"（产物在 Gate 证据后被修改？）。\n")
            if gate == "overview":
                sys.stderr.write("修复概要后重新运行 overview review loop 并写入 record-review overview；overview 不走人工确认。\n")
            elif gate == "requirements":
                sys.stderr.write("修复需求后请用户重新人工确认 requirements。\n")
            else:
                sys.stderr.write("修复详细设计后重新完成 detail 双 clean review，再请用户人工确认 detail。\n")
            return BLOCK
    states = _gate_states(task_dir)
    req = states.get("requirements")
    if not (isinstance(req, dict) and req.get("confirmed_by")):
        sys.stderr.write(f"[guru-gate:check] 拦截：需求 Gate 未确认（任务 {task_dir}）\n")
        sys.stderr.write("由用户本人在交互式终端执行：\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}\n")
        return BLOCK
    req_digest = req.get("artifact_digest")
    if not req_digest or req_digest != _gate_digest(task_dir, "requirements"):
        reason = "缺确认快照" if not req_digest else "确认快照失配（产物在确认后被修改）"
        sys.stderr.write(f"[guru-gate:check] 拦截：需求 Gate {reason}\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm requirements {task_dir}\n")
        return BLOCK

    for gate in REVIEW_GATES:
        if not _review_state(task_dir, gate)["ready"]:
            return _block_review("check", task_dir, gate)

    detail = states.get("detail")
    if not (isinstance(detail, dict) and detail.get("confirmed_by")):
        sys.stderr.write(f"[guru-gate:check] 拦截：详细设计 Gate 未确认（任务 {task_dir}）\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm detail {task_dir}\n")
        return BLOCK
    detail_digest = detail.get("artifact_digest")
    if not detail_digest or detail_digest != _gate_digest(task_dir, "detail"):
        reason = "缺确认快照" if not detail_digest else "确认快照失配（产物在确认后被修改）"
        sys.stderr.write(f"[guru-gate:check] 拦截：详细设计 Gate {reason}\n")
        sys.stderr.write(f"  python3 .trellis/scripts/guru/guru_gate.py confirm detail {task_dir}\n")
        return BLOCK
    print(f"[guru-gate:check] 需求确认 + 概要/详细双 clean review + 详细确认均有效（{task_dir}），放行")
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
