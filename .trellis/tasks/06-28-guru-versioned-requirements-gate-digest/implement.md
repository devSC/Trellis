# Implementation Plan: Extend requirements gate digest

> 改 `guru_gate.py` **+ `guru_supervise.py`** + 测试。codex 对抗审查后范围扩大(见 design §0)。
> planning 已经 codex opposite-provider 对抗审查(memory `codex-adversarial-review-before-delivery`)。

## 1. Plan

### Slice 1: 共享 requirements digest helper(解 blocker)

- `guru_gate.py` 抽 digest 计算到共享函数:结构化 artifact `{path,source,key}` + namespaced key + `(key,realpath)` 排序 + realpath 围栏 + `canonical_root`/`canonical_excludes` 过滤 + manifest fail-closed。
- `_requirement_package_dir(task_dir)` realpath 围栏(类比 `_package_dir`)。

### Slice 2: `guru_gate.py _gate_artifacts(requirements)` 用共享 helper

- 有 `requirement_package` 时纳入版本目录 canonical 文件(`os.walk` + sort,减 excludes);无指针保持 `prd.md` + 纯 basename。

### Slice 3: `guru_supervise.py` 改用共享 helper

- `from guru_gate import <helper>`(同 overlay/verify 目录);**替换独立 `_requirements_digest`(行 755)**,与 gate 同口径。

### Slice 4: 测试

- **集成**(supervisor+gate freshness):有指针时 supervise clean → gate `current`;改 canonical 正文 → `stale`;改 excludes 子树 → `current`;无指针 → 旧行为。
- namespace 碰撞(requirements/design `README.md` 同存)、排序稳定(枚举顺序无关)、manifest(缺失 fallback / 非法 fail-closed)、无指针回归。

### Slice 5: sync + bundled + 回归

- `node sync-guru-template.js` + 传染处理(两脚本)+ `pnpm -C packages/cli test guru`(集成 + 既有 gate 回归)。

## 2. Validation Checklist

- [ ] `git diff --check`
- [ ] `task.py validate 06-28-guru-versioned-requirements-gate-digest`
- [ ] `guru_gate` + `guru_supervise` 测试(集成 + 单元)通过
- [ ] 无指针任务 requirements digest 不变(回归)
- [ ] 端到端:改正式需求包正文 → digest 变 → confirm 失效;**supervise clean → gate `current`**(同口径,解 blocker)
- [ ] 改 overlay → sync + `git diff packages/cli/src/templates/guru` 核对(两脚本)
- [ ] 核心 confirm/review_runs/失配恢复未破坏(回归)
- [ ] 未回退 06-24/06-26/06-28 已提交改动

## 3. Risk Points

- **digest 核心 + 两脚本同口径**:共享 helper 必须严格一致(回归 + 集成测试守门)。
- **namespace 仅有指针启用**:避免改旧任务 digest(否则全 stale)。
- **manifest fail-closed 边界**:缺失 vs 非法严格区分。
- overlay 传染;改两脚本 + 测试,改动面大于档 1/2。

## 4. Rollback Plan

- 逐文件 `git checkout -- <仅本任务文件>`;**禁** 全量。
- 保护:06-24 改动、06-26/06-28 已提交内容。
- sync 大范围 bundled 改动先 `git diff` 审查,只 add 本任务。

## 5. Open Confirmation Before Implementation

- OQ-1~4 待用户拍板(OQ-2 已升级为整体决策:namespace+relpath+排序+共享 helper)。
- planning 已经 codex 对抗审查(Go-with-fixes,findings 全部纳入)。

## 6. 审查记录

- **codex(gpt-5.5)对抗审查 2026-06-28**:结论 Go-with-fixes;[blocker] `guru_supervise.py` 独立 digest + [major]×5(namespace/结构化 artifact/稳定排序/manifest fail-closed/集成测试)+ [minor]×2(字段审计/OQ-2 升级),**全部纳入 prd/design/implement**。报告:`scratchpad/codex-review-tier3.txt`。

## 7. 执行(改动文件 + trace)

### 改动文件

- `guru-template/overlay/verify/guru_gate.py`(+314)
  - 新增 `_requirement_package_dir(task_dir)`:严格照抄 `_package_dir` 围栏(normpath、`GURU_GATE_ALLOW_ABS` 逃生口、拒绝 abs/`..`、realpath commonpath 围栏)。
  - 新增 manifest fail-closed 解析:`RequirementManifestError` + `_parse_inline_list` + `_requirement_manifest(pkg)`(缺失→默认 `canonical_root='.'`/`excludes=[snapshots,changes]`;非法→抛错)+ `_requirement_manifest_problem(task_dir)`。stdlib 小解析,只支持 §15.2 两键的 inline/block list,无 yaml 依赖。
  - 新增 `_requirement_package_files(pkg)`:`os.walk` + `dirs.sort()`/`files.sort()` + 按 `canonical_excludes` 顶层剪枝,返回 `(relpath, abspath)`。
  - 新增 `_namespaced_key(...)`:namespace OFF→纯 basename(向后兼容);ON→`<source>:<relpath>`。
  - **重写** `_gate_artifacts`:返回结构化 `[{path, source, key}]`(source∈task/design/requirements);namespace 仅在该任务有 `requirement_package` 时启用;requirements 段把正式需求包 canonical 文件并入(累积:overview/detail 同样含)。
  - **重写** `_gate_digest`:按 `(key, realpath)` 全量排序;入哈希用 `key`(替换 basename)。namespace OFF 时 `key==basename`,digest 与改动前逐字节一致。
  - 新增公开 `requirements_digest(task_dir)`(供 supervise import)。
  - manifest fail-closed 接入读/写路径:`check_requirements`(先于 digest 取材阻断)、`cmd_status`、`digest` 子命令、`_record_review`、`cmd_confirm`、`_record_grill` 各加一处守卫,非法 manifest 不再 traceback。
- `guru-template/overlay/verify/guru_supervise.py`(+/-25)
  - 顶部 `sys.path.insert(0, <script dir>)` + `from guru_gate import requirements_digest as _guru_gate_requirements_digest`。
  - **替换** 独立 `_requirements_digest`(原行 755)为薄 wrapper 委托共享 helper;移除因此孤立的 `import hashlib`。
- `guru-template/overlay/verify/tests/run_tests.sh`(+173):新增档3夹具(见 §4),175 passed/0 failed。
- `packages/cli/test/guru/guru-bundled.test.ts`(+227):新增 `describe("guru requirements digest versioned package (source overlay)")` 集成块(driver=SOURCE overlay,bundled 未同步时也能验证);新增 `import crypto`。

### 设计落实确认(逐条对照 brief)

1. 共享 helper 解 blocker:`requirements_digest` 单一来源,supervise 委托 → 两脚本字节一致(已端到端验证)。✅
2. 结构化 artifact + namespace key:`{path,source,key}`,`task:`/`design:`/`requirements:`;namespace 仅有指针启用,无指针纯 basename(digest 不变)。✅
3. `_requirement_package_dir` 围栏照抄 `_package_dir`。✅
4. manifest fail-closed:缺失 fallback / 非法阻断 + 修复提示;stdlib 解析无 yaml。✅
5. 稳定排序:`(key, realpath)` + `os.walk` dirs/files.sort() + excludes 剪枝。✅

### 偏离 / 存疑(显式)

- **namespace 作用域**:design §2.3 强调“namespace 仅在有 `requirement_package` 时启用”。实现把该开关按任务粒度统一应用到该任务**全部 gate**(requirements/overview/detail),而非仅 requirements gate。理由:(a) 同一任务 digest scheme 一致;(b) requirements README 与 design README 的潜在 key 碰撞由 `source:` 前缀消解;(c) 有指针任务必为新任务,改其 overview/detail digest 无回归;(d) 无指针任务全部 gate 保持纯 basename,digest 逐字节不变(最高优先级)。此为对 design 的细化,不改变任何对外行为或 SSOT。
- **manifest 守卫接入点**:design 只点名“`guru_gate.py requirements` 阻断”。为避免非法 manifest 在 status/digest/record-review/confirm/grill 等也调用 `_gate_digest` 的读/写路径 traceback,在这些入口各加同口径 fail-closed 守卫(返回 BLOCK + 同一修复提示)。属健壮性补强,不放宽任何放行条件。

### 验证结果(命令 + 结论)

- `python3 -m py_compile guru_gate.py guru_supervise.py` → OK。
- `python3 guru_supervise.py --help` → import 解析成功(real-script 语义)。
- 共享单一来源:`guru_supervise._requirements_digest == guru_gate.requirements_digest == _gate_digest('requirements')`(无指针)→ PASS。
- 向后兼容:无指针 requirements/overview/detail digest == 历史 basename 公式 → PASS。
- requirement_package:canonical 文件入 digest(namespaced)、snapshots/changes 排除、改 canonical 正文→digest 变、改 excludes 子树→不变 → 全 PASS。
- namespace 碰撞:`design:README.md` + `requirements:README.md` 各自独立、overview digest 确定不崩溃 → PASS。
- 稳定排序:不同创建顺序→同 digest → PASS。
- manifest:缺失 fallback / 自定义 root+excludes 生效 / 非法(excludes 非列表、canonical_root 列表、未闭合 inline)→ requirements gate 阻断 + digest/status 同口径阻断 → 全 PASS。
- 端到端集成(real source 脚本 + fake trellis 发 clean verdict):**supervise 记录 digest == gate 当前 digest**;改 canonical→diverge(stale);改 excludes 子树→不变 → 全 PASS(解 blocker 核心)。
- `bash tests/run_tests.sh` → **175 通过 / 0 失败**(原 157 + 新 18);无 `__pycache__`/`.pyc` 残留。
- `task.py validate 06-28-guru-versioned-requirements-gate-digest` → All validations passed。
- TS:`tsc --noEmit` 单测文件(node types + NodeNext)→ exit=0,我新增代码 0 错误。

### 未完成 / 交主会话

- **bundled 同步(Slice 5)**:未执行 `node sync-guru-template.js`、未改 `packages/cli/src/templates/guru/...`(按 brief 由主会话 sync)。同步前 `guru-bundled.test.ts` line 676 的 in-sync 断言(source==bundled)与读 bundled 的既有 python smoke 会失败,属预期;同步后转绿。
- **`pnpm -C packages/cli test guru` 未在本环境跑通**:worktree 的 `node_modules` 为 arm64 安装(仅 `@rollup/rollup-darwin-arm64`)而当前为 darwin x64,叠加 pnpm store v11/v10 版本错配,rollup/vitest/tsc bin 均无法链接(npm 已知 optional-deps bug,错误信息自带 #4828 链接)。此为预存环境问题,非本改动引入;新增 TS 用例已用 `tsc` 单独类型校验通过,且其断言的 Python 行为已由上述 bash 端到端复现全 PASS。主会话在正常环境跑 `pnpm -C packages/cli test guru` 即可。

## 8. 返工(codex 代码审查 Needs-rework,2026-06-28,gpt-5.5 opposite-provider)

报告:`scratchpad/codex-review-tier3-impl.txt`。结论 Needs-rework:1 blocker + 3 major + 2 minor。逐条修复(只改 `guru_gate.py` + `guru_supervise.py` + `tests/run_tests.sh` + `guru-bundled.test.ts`,未改 bundled、未 commit)。

### 逐条修复

- **[blocker] cwd 分叉(`_requirement_package_dir` 用 `os.getcwd()`)**:`guru_supervise --root <repo>` 在 cwd≠root 下把 `docs/...` 解析成 `<cwd>/docs/...`(空包/错包),与 gate 从 repo root 算的 digest 分叉、review 立刻 stale。
  - 修:`_requirement_package_dir(task_dir, repo_root=None)` 增显式 `repo_root` 形参——按 `repo_root`(而非进程 cwd)解析 `requirement_package`,**返回绝对路径**(join repo_root + 围栏 commonpath base=repo_root),使后续枚举/读取与 cwd 无关。`repo_root` 透传链:`_gate_artifacts` / `_gate_digest` / `requirements_digest` / `_requirement_package_problem` 全部新增 `repo_root=None`(gate 自身命令 cwd==root,默认 None 保持旧行为)。`guru_supervise._requirements_digest(task_dir, repo_root)` 在记录 review digest 处传 `config.root`。
  - 回归(已加):bash `[blocker]`(in-process,cwd≠root + repo-root 相对 pkg → supervise digest == gate digest 且纳入包)+ TS `matches the gate digest when supervise runs with cwd different from --root`(真 `--root` 子进程,cwd=独立临时目录)+ 实测真脚本 e2e(`cd /elsewhere && guru_supervise --root <repo>` → recorded == gate)。

- **[major] 向后兼容 tie-break 破坏**:`_gate_digest` 把排序从 `key=basename`(稳定保留输入顺序)统一改成 `(key, realpath)`,namespace OFF 时重复 basename(`design-main.md`+`chapters/design-main.md`、`implement.md`+`chapters/implement.md`)串接顺序变 → 旧确认/review_runs stale。
  - 修:`_gate_digest` 按 namespace 分支排序——**OFF:只按 `e["key"]`(==basename),Python 稳定排序保留 `_gate_artifacts` 原始 entry 顺序,与历史 `key=os.path.basename` 逐字节一致**;ON:`(key, realpath)`(key 已全局唯一)。
  - 回归(已加):bash `[major] 无指针 overview/detail digest 与历史 basename 公式一致(含重复 basename 设计包)`,直接比对 HEAD `_gate_digest` 公式;sanity 脚本另证 light 链三 gate 全等。

- **[major] 围栏不 fail-closed**:`_requirement_package_dir` 不查目录存在;`_requirement_package_files` 对 `canonical_root` 只 normpath+join 不拒 abs/`..`、不 commonpath。`docs/missing`→空 hash;`canonical_root: ../../..`→包外入 digest。
  - 修:新增 `_canonical_root_dir(pkg)` 集中围栏(拒 abs/`..`、realpath commonpath 确保在 pkg 内、目录不存在抛错);`_requirement_package_files` 改用它(canonical_root 越界/缺失 → 抛 `RequirementManifestError`)。`_requirement_manifest_problem` 重命名为 `_requirement_package_problem` 并扩展:字段存在但指针非法 → BLOCK;版本目录不存在 → BLOCK;manifest/canonical_root 非法 → BLOCK(6 处调用点同步改名)。
  - 回归(已加):bash `[major]` missing package / canonical_root escape / canonical_root missing;TS `fails closed when the requirement package directory is missing` + `fails closed when manifest canonical_root escapes the package directory`。

- **[major] manifest fail-closed 不完整**:顶层非 `key: value` 行(无冒号/`=`/typo bareword)直接 `continue` → 静默 fallback。
  - 修:解析器顶层非空非注释行无法按 `key: value` 解析 → 抛 `RequirementManifestError`(不再 `continue`);孤立缩进行(无属主键)抛错;`canonical_root` 空值/列表/块标量一律拒;非目标键的合法块列表(如 `supersedes:\n  - v0`)经新增 `_consume_block_list(strict_dash=False)` 吞掉子项使顶层解析继续,不误判。
  - 回归(已加):bash `[major]` 无冒号 / `=` 赋值 / typo bareword / 内联未闭合 / 块列表非 dash;`[major] manifest 块列表 excludes 生效 + 非目标键块列表(supersedes)容忍`。

- **[minor] 偏离合同**:旧 implement.md 偏离理由“有指针任务必为新任务”不成立(代码不禁止老任务后补字段)。改为正确合同:**新增 `requirement_package` 是需求取材范围变化,必须使下游 cumulative digest stale**(保守且符合 Gate 模型)。namespace 仍按任务粒度应用到该任务全部 gate(OFF→纯 basename,digest 不变;ON→namespaced)。回归(已加):bash `[minor] 后补 requirement_package → requirements digest 变更(预期 stale)`。

- **[minor] 测试盲区**:TS `gateDigest` 固定 `cwd=tmpDir=fake root`、shell `GURU_GATE_ALLOW_ABS=1`+绝对路径,掩盖 cwd/root-relative 分叉。已用 codex 列的 4 类回归覆盖真实场景:cwd≠root+--root+relative pkg(bash+TS+真脚本 e2e);无指针 overview/detail byte-compat 含重复 basename;manifest block list + 各 malformed;missing package / missing canonical root / canonical_root escape。新 bash 用例用 `env -u GURU_GATE_ALLOW_ABS` 走生产围栏。

### 改动文件(返工)

- `guru-template/overlay/verify/guru_gate.py`:`_requirement_package_dir(+repo_root,返回绝对路径)`;新增 `_canonical_root_dir`、`_consume_block_list`;`_requirement_package_files` 改用 `_canonical_root_dir`;manifest 解析器 fail-closed 补全;`_requirement_manifest_problem`→`_requirement_package_problem`(+目录存在/指针合法/canonical_root 围栏,6 处调用点改名);`_gate_artifacts`/`_gate_digest`/`requirements_digest` 增 `repo_root`;`_gate_digest` 按 namespace 分支排序(OFF byte-compat)。
- `guru-template/overlay/verify/guru_supervise.py`:`_requirements_digest(+repo_root)` 委托共享 helper 传 root;记录 review digest 处传 `config.root`。
- `guru-template/overlay/verify/tests/run_tests.sh`:新增返工回归块(blocker cwd≠root / byte-compat 重复 basename / 后补指针 stale / 围栏 fail-closed×3 / manifest fail-closed×5 + block list 容忍)。
- `packages/cli/test/guru/guru-bundled.test.ts`:新增 3 个 TS 用例(cwd≠root blocker 真子进程、missing package fail-closed、canonical_root escape fail-closed)。

### 验证结果(返工)

- `python3 -m py_compile guru_gate.py guru_supervise.py` → OK;`guru_supervise.py --help` 导入成功(real-script 语义)。
- `bash tests/run_tests.sh` → **189 通过 / 0 失败**(原 175 + 返工新增 14);无 `__pycache__`/`.pyc` 残留。
- `task.py validate 06-28-...` → All validations passed。
- TS:全局 `tsc --noEmit`(NodeNext + @types/node)对 `guru-bundled.test.ts` → exit=0,0 错误(vitest 模块在 NodeNext 下也解析,新增代码无类型错)。
- 真脚本 e2e(`cd /elsewhere && guru_supervise --root <repo> --adversarial requirements`,fake trellis 发 clean):recorded review digest == gate `digest requirements`(repo root)→ **SAME**(解 blocker 核心,实测两脚本字节同口径)。
- sanity 脚本(`scratchpad/sanity.py`):byte-compat full(含重复 basename)+ light 三 gate 全等;blocker cwd≠root SAME 且纳入包;fail-closed missing/escape/missing-canonical-root + manifest no-colon/`=`/bareword/block-non-dash/inline-unclosed 全阻断;block list 合法 + supersedes 容忍 → ALL PASSED。

### 仍交主会话(返工后不变)

- **bundled 同步(Slice 5)**:仍未执行 `node sync-guru-template.js`、未改 `packages/cli/src/templates/guru/...`(按 brief 由主会话 sync)。同步前 in-sync 断言与读 bundled 的 python smoke 属预期失败,同步后转绿;新增 SOURCE-overlay TS 用例不依赖同步即可独立验证本任务改动。
- **`pnpm -C packages/cli test guru` 未在本环境跑通**:预存环境问题(arm64 node_modules on x64 + pnpm store 版本错配),非本改动引入。已用全局 `tsc` 类型校验 + bash/真脚本 e2e 等价覆盖;主会话在正常环境跑即可。
