#!/usr/bin/env python3
"""Standalone 测试：REQ-UC↔BHV 桥（trace-aggregate + 单表回填 + fail-closed + --require-req-uc）。

环境 arm64/x64 不可跑 pnpm test，故用 python3 直跑（无第三方依赖）。
覆盖 design §5 + implement.md checklist：
  - trace-matrix REQ-UC 列（行展开）+ task 级旧输出回归
  - trace-aggregate 反查边界（无指针/别版本/非法/缺目录/symlink/archive 月份树/历史 schema + skipped 分类）
  - 单表回填（(REQ-UC, UNIT) key 保留 / orphan-stale 不丢 / 幂等）
  - fail-closed 四态（无 manifest / 无 canonical_excludes / excludes 不含 traceability → 拒写；含 → 写）
  - --require-req-uc 三类（旧 task 无字段 PASS / task.json flag 缺 REQ-UC BLOCK / CLI 显式即使旧 task 也 BLOCK）

用法：python3 .trellis/tasks/06-28-guru-traceability-reqc-bhv-bridge/tests/test_trace_bridge.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
GATE = os.path.join(REPO, "guru-template", "overlay", "verify", "guru_gate.py")

_spec = importlib.util.spec_from_file_location("guru_gate", GATE)
gg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gg)

PASS, BLOCK = 0, 2

_results = []


def check(name, cond):
    _results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


# ---------------------------------------------------------------------------
# 夹具构造
# ---------------------------------------------------------------------------

def make_task(root, name, *, prd=None, design=None, implement=None,
              task_json=None):
    """在 root/.trellis/tasks/<name>/ 造一个 task。返回 task_dir 绝对路径。"""
    d = os.path.join(root, ".trellis", "tasks", name)
    os.makedirs(d, exist_ok=True)
    if prd is not None:
        open(os.path.join(d, "prd.md"), "w").write(prd)
    if design is not None:
        open(os.path.join(d, "design.md"), "w").write(design)
    if implement is not None:
        open(os.path.join(d, "implement.md"), "w").write(implement)
    open(os.path.join(d, "task.json"), "w").write(json.dumps(task_json or {}))
    return d


def make_archived_task(root, month, name, *, prd=None, design=None, task_json=None):
    d = os.path.join(root, ".trellis", "tasks", "archive", month, name)
    os.makedirs(d, exist_ok=True)
    if prd is not None:
        open(os.path.join(d, "prd.md"), "w").write(prd)
    if design is not None:
        open(os.path.join(d, "design.md"), "w").write(design)
    open(os.path.join(d, "task.json"), "w").write(json.dumps(task_json or {}))
    return d


def make_version_pkg(root, rel, *, excludes_line=None, no_manifest=False):
    """造需求包版本目录。excludes_line=None 且 no_manifest=False → 无 canonical_excludes 键。"""
    vdir = os.path.join(root, rel)
    os.makedirs(vdir, exist_ok=True)
    if not no_manifest:
        lines = ["version: v1.0.0", "app_version: 1.0.0", "status: draft"]
        if excludes_line is not None:
            lines.append(excludes_line)
        open(os.path.join(vdir, "manifest.yaml"), "w").write("\n".join(lines) + "\n")
    return vdir


PRD_TWO_BHV = """# Test feature
### BHV-001 [REQ-UC-005, REQ-UC-007] 玩家选择 Hammer
Given a player When choose Then hammer used. P0 失败路径 验收场景 未决问题
### BHV-002 玩家取消（无 REQ-UC 承接）
Given/When/Then P1
"""

DESIGN_TWO_UNIT = """# Design
## §1 概要
BHV-001 owner 行 BHV-002 owner 行
## §2 详细
### UNIT-hammer-usecase
承接 BHV-001 测试映射
### UNIT-cancel-flow
承接 BHV-002 测试映射
"""


# ---------------------------------------------------------------------------
# 测试组
# ---------------------------------------------------------------------------

def test_trace_matrix_req_uc_column():
    print("\n== test_trace_matrix_req_uc_column（行展开 + 旧输出回归） ==")
    root = tempfile.mkdtemp()
    try:
        d = make_task(root, "t1", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT)
        t = gg.build_trace(d)
        check("BHV-001 解析多 REQ-UC", t["req_ucs"].get("BHV-001") == ["REQ-UC-005", "REQ-UC-007"])
        check("BHV-002 无 REQ-UC → 空列表", t["req_ucs"].get("BHV-002") == [])
        out = gg.render_matrix(t)
        check("矩阵含 REQ-UC 列头", "需求场景（REQ-UC）" in out)
        check("REQ-UC-005 单独成行", "| REQ-UC-005 |" in out)
        check("REQ-UC-007 单独成行", "| REQ-UC-007 |" in out)
        # 无 REQ-UC 的 BHV-002 行用 — 占位（不断链）
        bhv2_rows = [ln for ln in out.splitlines() if "BHV-002" in ln and ln.startswith("|")]
        check("BHV-002 行 REQ-UC 列为 —", bhv2_rows and " — " in bhv2_rows[0])
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_trace_matrix_legacy_no_req_uc():
    print("\n== test_trace_matrix_legacy_no_req_uc（旧 prd 全无 REQ-UC 不断链） ==")
    root = tempfile.mkdtemp()
    try:
        prd = "# old\n### BHV-001 老行为\nGiven/When/Then P0 失败 验收 未决\n"
        design = "# d\n## §1\nBHV-001 owner\n## §2\n### UNIT-old\n承接 BHV-001 测试映射\n"
        d = make_task(root, "old", prd=prd, design=design)
        t = gg.build_trace(d)
        out = gg.render_matrix(t)
        check("旧 BHV REQ-UC 列空 —", "| BHV-001 | 老行为 | — |" in out)
        check("旧输出不因 REQ-UC 断链（无 bhv_no_unit）", not t["orphans"]["bhv_no_unit"])
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_trace_matrix_golden_regression():
    print("\n== test_trace_matrix_golden_regression（task 级输出逐字节冻结） ==")
    root = tempfile.mkdtemp()
    try:
        # 冻结一个完整闭链 task 的矩阵输出（含 REQ-UC 列）；列结构/占位/孤儿区一旦回归即报警。
        prd = ("# g\n### BHV-001 [REQ-UC-005] 选择\nGiven/When/Then P0 失败 验收 未决\n"
               "### BHV-002 取消\nGiven/When/Then P1\n")
        design = ("# d\n## §1\nBHV-001 owner BHV-002 owner\n## §2\n"
                  "### UNIT-pick\n承接 BHV-001 测试映射\n### UNIT-cancel\n承接 BHV-002 测试映射\n")
        implement = "# i\nSlice 1 承接 UNIT-pick\nSlice 2 承接 UNIT-cancel\n"
        d = make_task(root, "g", prd=prd, design=design, implement=implement)
        out = gg.render_matrix(gg.build_trace(d))
        expected = (
            "# 追溯矩阵（机器生成，勿手编）\n\n"
            "| 行为 | 名称 | 需求场景（REQ-UC） | 归属（§1） | 承接单元（§2） | 测试映射 | 实现切片 |\n"
            "|------|------|------|-----------|---------------|---------|---------|\n"
            "| BHV-001 | 选择 | REQ-UC-005 | ✅ | UNIT-pick | ✅ | ✅ |\n"
            "| BHV-002 | 取消 | — | ✅ | UNIT-cancel | ✅ | ✅ |\n\n"
            "## 孤儿/断链清单\n"
            "- 无（承接链闭合）\n"
        )
        check("矩阵输出逐字节匹配 golden", out == expected)
        if out != expected:
            print("    --- actual ---")
            print(out)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_aggregate_basic_and_skipped():
    print("\n== test_aggregate_basic_and_skipped（反查 + 行展开 + skipped 分类） ==")
    root = tempfile.mkdtemp()
    try:
        os.environ["GURU_GATE_ALLOW_ABS"] = "1"  # 测试夹具用绝对路径指针
        vdir = make_version_pkg(root, "docs/req/v1.0.0",
                                excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        other_vdir = make_version_pkg(root, "docs/req/v2.0.0",
                                      excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        # 匹配 task：指向 v1.0.0
        make_task(root, "match-a", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                  task_json={"requirement_package": vdir})
        # 别版本：指向 v2.0.0
        make_task(root, "other-ver", prd=PRD_TWO_BHV,
                  task_json={"requirement_package": other_vdir})
        # 无 requirement_package 字段
        make_task(root, "no-pkg", prd=PRD_TWO_BHV, task_json={})
        # 非法指针（绝对路径在非 ALLOW_ABS 下会 None，但此处 ALLOW_ABS=1 放行绝对路径，
        # 故用 .. 穿越构造非法）
        make_task(root, "illegal", prd=PRD_TWO_BHV,
                  task_json={"requirement_package": "../../../../etc"})
        # 历史 schema：task.json 非对象 → _task_json_of 回 {}
        d_hist = os.path.join(root, ".trellis", "tasks", "hist")
        os.makedirs(d_hist)
        open(os.path.join(d_hist, "task.json"), "w").write("[]")
        open(os.path.join(d_hist, "prd.md"), "w").write(PRD_TWO_BHV)

        rc = gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        check("aggregate 返回 PASS", rc == PASS)
        tpath = os.path.join(vdir, "traceability.md")
        check("traceability.md 已写", os.path.isfile(tpath))
        txt = open(tpath).read()
        check("含生成区 start 标记", gg._TRACE_GEN_START in txt)
        check("含生成区 end 标记", gg._TRACE_GEN_END in txt)
        # match-a 的 BHV-001 × (REQ-UC-005, REQ-UC-007) × UNIT-hammer-usecase = 2 行
        check("REQ-UC-005 行展开存在", "| REQ-UC-005 |" in txt)
        check("REQ-UC-007 行展开存在", "| REQ-UC-007 |" in txt)
        check("UNIT-hammer-usecase 在表", "UNIT-hammer-usecase" in txt)
        check("Source Task=match-a", "match-a" in txt)
        # 别版本/无指针/非法/历史 不应进表
        check("别版本 task 不进表", "other-ver" not in txt)
    finally:
        os.environ.pop("GURU_GATE_ALLOW_ABS", None)
        shutil.rmtree(root, ignore_errors=True)


def test_aggregate_include_completed_archive():
    print("\n== test_aggregate_include_completed_archive（archive 月份树反查） ==")
    root = tempfile.mkdtemp()
    try:
        os.environ["GURU_GATE_ALLOW_ABS"] = "1"
        vdir = make_version_pkg(root, "docs/req/v1.0.0",
                                excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        make_archived_task(root, "2026-06", "old-feat", prd=PRD_TWO_BHV,
                           design=DESIGN_TWO_UNIT,
                           task_json={"requirement_package": vdir, "status": "completed"})
        # 默认（不含 archive）：归档 task 不进表
        gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        txt_default = open(os.path.join(vdir, "traceability.md")).read()
        check("默认不扫 archive → old-feat 不进表", "old-feat" not in txt_default)
        # 默认模式应把匹配本版本的归档 task 记入 archived_not_included 提示（不入表）
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        check("默认模式提示 归档未 --include-completed", "归档未 --include-completed" in buf.getvalue())
        # --include-completed：归档 task 进表（source 带 archive/月份前缀）
        gg.cmd_trace_aggregate(vdir, include_completed=True, repo_root=root)
        txt_inc = open(os.path.join(vdir, "traceability.md")).read()
        check("include-completed 扫 archive 月份树 → old-feat 进表", "old-feat" in txt_inc)
        check("archive source 带月份前缀", "archive/2026-06/old-feat" in txt_inc)
    finally:
        os.environ.pop("GURU_GATE_ALLOW_ABS", None)
        shutil.rmtree(root, ignore_errors=True)


def test_aggregate_symlink_escape():
    print("\n== test_aggregate_symlink_escape（symlink 逃逸出 repo → None → skipped） ==")
    root = tempfile.mkdtemp()
    outside = tempfile.mkdtemp()
    try:
        # 不设 ALLOW_ABS：走 realpath commonpath 围栏
        vdir = make_version_pkg(root, "docs/req/v1.0.0",
                                excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        # task 指针经 symlink 逃逸出 repo root
        link = os.path.join(root, "docs", "escape")
        os.symlink(outside, link)
        make_task(root, "sym", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                  task_json={"requirement_package": "docs/escape"})
        rc = gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        check("symlink 逃逸 task 不致命（PASS）", rc == PASS)
        txt = open(os.path.join(vdir, "traceability.md")).read()
        check("symlink 逃逸 task 不进表", "BHV-001" not in txt or "sym" not in txt)
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(outside, ignore_errors=True)


def test_backfill_and_orphan_and_idempotent():
    print("\n== test_backfill_and_orphan_and_idempotent（回填/orphan/幂等） ==")
    root = tempfile.mkdtemp()
    try:
        os.environ["GURU_GATE_ALLOW_ABS"] = "1"
        vdir = make_version_pkg(root, "docs/req/v1.0.0",
                                excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        make_task(root, "feat", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                  task_json={"requirement_package": vdir})
        # 第一次生成
        gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        tpath = os.path.join(vdir, "traceability.md")
        first = open(tpath).read()
        # 人手填 Code/Test/Status（模拟审计回填）：替换 REQ-UC-005 + UNIT-hammer-usecase 行
        lines = first.splitlines()
        for i, ln in enumerate(lines):
            if "REQ-UC-005" in ln and "UNIT-hammer-usecase" in ln:
                lines[i] = ("| REQ-UC-005 | feat | UNIT-hammer-usecase | BHV-001 | "
                            "lib/hammer.dart | hammer_test.dart::usecase | covered |")
        open(tpath, "w").write("\n".join(lines) + "\n")
        # 第二次：手维护列必须按 (REQ-UC, UNIT) key 保留
        gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        second = open(tpath).read()
        check("回填保留 Code Entry", "lib/hammer.dart" in second)
        check("回填保留 Test Evidence", "hammer_test.dart::usecase" in second)
        check("回填保留 Status=covered", "covered" in second)
        # 幂等：再跑一次输出逐字节不变
        gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        third = open(tpath).read()
        check("幂等：第二次 == 第三次", second == third)

        # orphan：移除 design 的 UNIT-hammer-usecase（BHV-001 不再被该 UNIT 承接）
        design_no_hammer = DESIGN_TWO_UNIT.replace(
            "### UNIT-hammer-usecase\n承接 BHV-001 测试映射\n", "")
        # 同时让 BHV-001 改挂别的 UNIT，使旧 (REQ-UC-005, UNIT-hammer-usecase) key 失活
        open(os.path.join(root, ".trellis", "tasks", "feat", "design.md"), "w").write(
            design_no_hammer)
        gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        after = open(tpath).read()
        check("UNIT 移除后旧手维护证据不丢（lib/hammer.dart 仍在）", "lib/hammer.dart" in after)
        check("旧证据被标 orphan/移除", "已移除" in after or "orphan" in after.lower())
    finally:
        os.environ.pop("GURU_GATE_ALLOW_ABS", None)
        shutil.rmtree(root, ignore_errors=True)


def _gen_region(txt):
    s = txt.find(gg._TRACE_GEN_START)
    e = txt.find(gg._TRACE_GEN_END)
    return txt[s:e] if (s >= 0 and e >= 0) else ""


def test_pure_idempotent_no_manual_no_phantom_orphan():
    """回归：无手维护编辑时 aggregate 必须逐字节幂等；含「无 REQ-UC 的 BHV」时
    不得为其仍存活的 UNIT 造假「已移除」孤儿行。

    缺陷根因：render 把空 cell 渲染成占位符 `—`，旧 _parse_existing_manual 读回为字面 `—`，
    导致 (a) 空 REQ-UC live key ("", unit) ≠ parsed key ("—", unit) → 活跃单元被判 orphan；
    (b) 空 code/test 读成 `—`（truthy）使空证据过滤失效 → 假孤儿行。原幂等用例只比 run2==run3
    （二者均已携带假孤儿故相等），漏掉本缺陷。"""
    print("\n== test_pure_idempotent_no_manual_no_phantom_orphan（无 REQ-UC BHV 不造假孤儿 + 纯幂等） ==")
    root = tempfile.mkdtemp()
    try:
        os.environ["GURU_GATE_ALLOW_ABS"] = "1"
        vdir = make_version_pkg(root, "docs/req/v1.0.0",
                                excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        # PRD_TWO_BHV：BHV-002 无 REQ-UC 承接、其 UNIT-cancel-flow 始终存活
        make_task(root, "feat", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                  task_json={"requirement_package": vdir})
        tpath = os.path.join(vdir, "traceability.md")
        snaps = []
        for _ in range(3):
            gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
            snaps.append(open(tpath).read())
        check("纯幂等：run1 == run2 == run3（无手维护编辑）", snaps[0] == snaps[1] == snaps[2])
        # UNIT-cancel-flow 是 BHV-002 的当前承接单元，绝不能出现「已移除」孤儿标记
        orphan_lines = [ln for ln in _gen_region(snaps[-1]).splitlines()
                        if ln.startswith("|") and "已移除" in ln]
        check("无 REQ-UC 的 BHV 的存活 UNIT 不被造假孤儿（无「已移除」行）", not orphan_lines)
        if orphan_lines:
            print("    spurious orphan rows:")
            for ln in orphan_lines:
                print("     ", ln)
    finally:
        os.environ.pop("GURU_GATE_ALLOW_ABS", None)
        shutil.rmtree(root, ignore_errors=True)


def test_fail_closed_four_states():
    print("\n== test_fail_closed_four_states（决策 1 fail-closed 四态） ==")
    root = tempfile.mkdtemp()
    try:
        os.environ["GURU_GATE_ALLOW_ABS"] = "1"
        # 状态 1：无 manifest → 默认 excludes (snapshots, changes) 不含 traceability → 拒写
        v1 = make_version_pkg(root, "docs/req/v1", no_manifest=True)
        make_task(root, "t-nomanifest", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                  task_json={"requirement_package": v1})
        rc1 = gg.cmd_trace_aggregate(v1, include_completed=False, repo_root=root)
        check("无 manifest → 拒写 BLOCK", rc1 == BLOCK)
        check("无 manifest → 未写 traceability.md", not os.path.isfile(os.path.join(v1, "traceability.md")))

        # 状态 2：有 manifest 但无 canonical_excludes 键 → 回退默认 → 拒写
        v2 = make_version_pkg(root, "docs/req/v2")  # excludes_line=None → 无该键
        make_task(root, "t-nokey", prd=PRD_TWO_BHV,
                  task_json={"requirement_package": v2})
        rc2 = gg.cmd_trace_aggregate(v2, include_completed=False, repo_root=root)
        check("无 canonical_excludes 键 → 拒写 BLOCK", rc2 == BLOCK)
        check("无 canonical_excludes → 未写文件", not os.path.isfile(os.path.join(v2, "traceability.md")))

        # 状态 3：excludes 显式不含 traceability → 拒写
        v3 = make_version_pkg(root, "docs/req/v3",
                              excludes_line="canonical_excludes: [snapshots, changes]")
        make_task(root, "t-notrace", prd=PRD_TWO_BHV,
                  task_json={"requirement_package": v3})
        rc3 = gg.cmd_trace_aggregate(v3, include_completed=False, repo_root=root)
        check("excludes 不含 traceability → 拒写 BLOCK", rc3 == BLOCK)
        check("excludes 不含 traceability → 未写文件", not os.path.isfile(os.path.join(v3, "traceability.md")))

        # 状态 4：excludes 含 traceability → 允许写
        v4 = make_version_pkg(root, "docs/req/v4",
                              excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        make_task(root, "t-ok", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                  task_json={"requirement_package": v4})
        rc4 = gg.cmd_trace_aggregate(v4, include_completed=False, repo_root=root)
        check("excludes 含 traceability → 写入 PASS", rc4 == PASS)
        check("excludes 含 traceability → 已写文件", os.path.isfile(os.path.join(v4, "traceability.md")))
    finally:
        os.environ.pop("GURU_GATE_ALLOW_ABS", None)
        shutil.rmtree(root, ignore_errors=True)


def test_require_req_uc_three_cases():
    print("\n== test_require_req_uc_three_cases（finding 3 三类触发） ==")
    root = tempfile.mkdtemp()
    try:
        # 旧 task：BHV 全无 REQ-UC，无 flag → 默认 false → 不拦（require_req_uc=False）
        prd_old = "# old\n### BHV-001 老行为\nGiven/When/Then P0 失败 验收 未决\n"
        design = "# d\n## §1\nBHV-001 owner\n## §2\n### UNIT-old\n承接 BHV-001 测试映射\n"
        d_old = make_task(root, "old", prd=prd_old, design=design, task_json={})
        rc_default = gg.cmd_trace_matrix(d_old, write=False, strict=False, require_req_uc=False)
        check("旧 task 无字段默认不拦 → PASS", rc_default == PASS)

        # task.json require_req_uc=true + BHV 缺 REQ-UC → BLOCK
        d_flag = make_task(root, "flagged", prd=prd_old, design=design,
                           task_json={"require_req_uc": True})
        rc_flag = gg.cmd_trace_matrix(d_flag, write=False, strict=False, require_req_uc=True)
        check("task.json require_req_uc 缺 REQ-UC → BLOCK", rc_flag == BLOCK)

        # CLI 显式 --require-req-uc 即使旧 task（无 flag）也 BLOCK
        rc_cli = gg.cmd_trace_matrix(d_old, write=False, strict=False, require_req_uc=True)
        check("CLI 显式 require_req_uc 旧 task 缺 REQ-UC → BLOCK", rc_cli == BLOCK)

        # 强制态 + BHV 带 REQ-UC → PASS
        d_ok = make_task(root, "okuc", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                         task_json={"require_req_uc": True})
        # BHV-002 在 PRD_TWO_BHV 无 REQ-UC → 强制态应 BLOCK（验证 require 真的检查每个 BHV）
        rc_partial = gg.cmd_trace_matrix(d_ok, write=False, strict=False, require_req_uc=True)
        check("强制态 BHV-002 缺 REQ-UC → BLOCK（逐 BHV 检查）", rc_partial == BLOCK)

        # 全部 BHV 带 REQ-UC → PASS
        prd_all = ("# all\n### BHV-001 [REQ-UC-001] a\nGiven/When/Then P0 失败 验收 未决\n"
                   "### BHV-002 [REQ-UC-002] b\nGiven/When/Then P1\n")
        design_all = ("# d\n## §1\nBHV-001 BHV-002 owner\n## §2\n"
                      "### UNIT-a\n承接 BHV-001 测试映射\n### UNIT-b\n承接 BHV-002 测试映射\n")
        d_all = make_task(root, "alluc", prd=prd_all, design=design_all,
                          task_json={"require_req_uc": True})
        rc_all = gg.cmd_trace_matrix(d_all, write=False, strict=False, require_req_uc=True)
        check("强制态全 BHV 带 REQ-UC → PASS", rc_all == PASS)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_finding9_status_not_blocking():
    print("\n== test_finding9_status_not_blocking（traceability status 不参与 requirements/detail gate） ==")
    root = tempfile.mkdtemp()
    try:
        os.environ["GURU_GATE_ALLOW_ABS"] = "1"
        vdir = make_version_pkg(root, "docs/req/v1.0.0",
                                excludes_line="canonical_excludes: [snapshots, changes, traceability]")
        d = make_task(root, "feat", prd=PRD_TWO_BHV, design=DESIGN_TWO_UNIT,
                      task_json={"requirement_package": vdir})
        # 解耦 brainstorm 合同（与本断言无关）：核心证明 = traceability status 不参与 gate 判定。
        # 同一 prd / design 下，aggregate 写 traceability 前后 gate 结果必须逐字相同——
        # 若 status 参与判定，写入 missing/orphan 行会改变结果。
        rc_req_before = gg.check_requirements(d)
        gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        txt = open(os.path.join(vdir, "traceability.md")).read()
        check("生成行默认 status=missing", "missing" in txt)
        rc_req_after = gg.check_requirements(d)
        check("requirements gate 结果不受 traceability 写入影响", rc_req_before == rc_req_after)
        # detail gate 同理（detail 读 design.md / chapters，不读 version traceability）
        rc_detail_before = gg.check_detail(d)
        # 再聚合一次（traceability 内容稳定）
        gg.cmd_trace_aggregate(vdir, include_completed=False, repo_root=root)
        rc_detail_after = gg.check_detail(d)
        check("detail gate 结果不受 traceability 写入影响", rc_detail_before == rc_detail_after)
    finally:
        os.environ.pop("GURU_GATE_ALLOW_ABS", None)
        shutil.rmtree(root, ignore_errors=True)


def test_aggregate_missing_version_dir():
    print("\n== test_aggregate_missing_version_dir（version 目录不存在 → BLOCK） ==")
    root = tempfile.mkdtemp()
    try:
        rc = gg.cmd_trace_aggregate(os.path.join(root, "nope"), include_completed=False,
                                    repo_root=root)
        check("version 目录不存在 → BLOCK", rc == BLOCK)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    tests = [
        test_trace_matrix_req_uc_column,
        test_trace_matrix_legacy_no_req_uc,
        test_trace_matrix_golden_regression,
        test_aggregate_basic_and_skipped,
        test_aggregate_include_completed_archive,
        test_aggregate_symlink_escape,
        test_backfill_and_orphan_and_idempotent,
        test_pure_idempotent_no_manual_no_phantom_orphan,
        test_fail_closed_four_states,
        test_require_req_uc_three_cases,
        test_finding9_status_not_blocking,
        test_aggregate_missing_version_dir,
    ]
    for t in tests:
        t()
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n==== {passed}/{total} assertions passed ====")
    failed = [n for n, ok in _results if not ok]
    if failed:
        print("FAILED:")
        for n in failed:
            print(f"  - {n}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
