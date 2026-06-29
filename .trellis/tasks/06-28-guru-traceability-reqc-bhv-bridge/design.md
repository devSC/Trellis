# Design: Bridge REQ-UC and BHV for versioned traceability

> 改 `guru_gate.py`(trace-matrix + 新 `trace-aggregate`)+ BHV 编号契约(4 平台同步)。
> 已据 codex 审查(§0)+ 用户拍板 3 合同决策返工。

## 0. codex 对抗审查 + 合同决策(2026-06-29)

codex Needs-rework(9 findings,完整报告 `scratchpad/codex-review-bridge2.txt`);用户拍板 3 合同决策:

- **决策 1(finding 1)**:`traceability.md` **加 `manifest.canonical_excludes`,不触发 requirements digest**(保持档 1「永不硬 Gate 审计参考」)。→ B。
- **决策 2(finding 6)**:BHV↔REQ-UC **多对多 + 行展开** `(REQ-UC, BHV, UNIT, Source Task)`。
- **决策 3(finding 7)**:**命名消歧** —— `REQ-UC`(需求源场景)vs `UC-<序号>`(overview 核心用例),两独立编号体系。

其余 findings(2 跨模板 / 3 strict / 4 表结构 / 5 反查 / 8 CLI / 9 测试)在下文落实。

## 1. Approach

BHV 标题带 `[REQ-UC-XXX]`(多对多承接);新子命令 `trace-aggregate <version-dir>` 聚合多 task 行展开到版本级 traceability 生成区;traceability 加 `canonical_excludes`(不触发 digest);改 BHV 编号契约(4 平台同步)。向后兼容(旧 prd 不断链)。

## 2. 改动设计

### 2.1 BHV 承接 REQ-UC(命名消歧 + 多对多,findings 6/7)

- BHV 标题:`### BHV-001 [REQ-UC-005, REQ-UC-007] <描述>`(多对多)。
- **命名消歧(决策 3)**:`REQ-UC` = requirements source use case(需求包场景,single-source §6);`UC-<序号>` = overview core use case(架构,overview §3.2)。**两独立编号体系**;BHV 标题承接 `REQ-UC`;overview §3.2 继续做 `BHV↔UC-<序号>` 人审(不动)。
- `guru_gate.py`:BHV 标题提取 `[REQ-UC-XXX]`(支持多个);基数多对多。

### 2.2 trace-matrix `REQ-UC` 列(行展开,决策 2)

- `build_trace` 收集 BHV→`[REQ-UC]`;`render_matrix` 加 `REQ-UC` 列,多 REQ-UC **行展开** `(REQ-UC, BHV, UNIT, Source Task)`(不塞同 cell)。
- task 级旧输出兼容(REQ-UC 列增量,无承接则空,回归锁定)。

### 2.3 `trace-aggregate` 子命令 + 反查策略(findings 5/8)

- **新子命令** `trace-aggregate <version-dir> [--include-completed]`(finding 8,**不复用** `trace-matrix <task_dir>` 解析,parser 明确分支)。
- **反查(finding 5 + codex 第三轮 finding 2)**:复用 `_requirement_package_dir(task_dir, repo_root)` 归一;**扫描根**:默认仅 `.trellis/tasks/<task>/task.json`(排除 `archive/`);`--include-completed` **同时扫 `.trellis/tasks/archive/<YYYY-MM>/<task>/task.json`**(仓库归档是月份分层,非一层 glob 能覆盖)+ 兼容旧 task.json status 缺失/`completed`/`archived`。非法指针**只在候选匹配该 version 时** fail,其余 `skipped`;**skipped summary 分类**:无 requirement_package / 别版本 / 非法指针 / 归档未 include / 历史 schema 缺字段。
- 收集 `(REQ-UC, BHV, UNIT, Source Task)` 行展开,按 REQ-UC 汇总写入版本目录 traceability 生成区。

### 2.4 生成 vs 手维护(单表回填,findings 1/4)

- `traceability.md` 用 **§15.4 单表**:`REQ-UC | Source Task | Design Unit(UNIT) | BHV | Code Entry | Test Evidence | Status`(不拆两表)。
- `trace-aggregate` 生成/更新 `REQ-UC|Source Task|UNIT|BHV` 派生列;`Code Entry|Test|Status` 按 `(REQ-UC, UNIT)` **稳定 key 回填**(保留手维护,绝不丢);BHV 新增/删除时旧证据标 `orphan`/`stale` 而非丢弃。
- 生成区标记(`<!-- trace-matrix:generated:start/end -->`)包裹整表;回填逻辑保证幂等。
- **决策 1(已据 codex 第三轮纠正)**:`traceability.md` 加 `manifest.canonical_excludes` → aggregate 写它**不触发** requirements digest。
- **⚠️ 撤回前一轮自核对错误**:`canonical_excludes` **有硬编码默认** `_MANIFEST_DEFAULT_EXCLUDES=(snapshots, changes)`(guru_gate.py:528);manifest 缺失 / 字段缺失 / 仍是 `[snapshots, changes]` 时回退默认(line 584/652),**默认不含 traceability** → 此时 aggregate 写 traceability 仍进 digest,违反 REQ-004。
- **故 `trace-aggregate` 须 fail-closed 前置(方案 A)**:写入前检查目标 version-dir 的 **effective excludes 必须含顶层 `traceability`**,否则**拒写 + 提示先更新 manifest**(不静默写入并声称 digest 不变)。**不改代码默认**(保持旧目录向后兼容;改 `_MANIFEST_DEFAULT_EXCLUDES` 会变旧目录默认口径,不取)。
- 须改:single-source §15.2 manifest 示例 `canonical_excludes: [snapshots, changes, traceability]` + 新目录模板 + 档 1 versioned-package §10。

### 2.5 `--require-req-uc` 模式(finding 3)

- 新模式(**不复用** `--strict`)。**触发合同(codex 第三轮 finding 3,拍死)**:① `trace-matrix --require-req-uc` 是**显式 CLI 强制**模式(即使旧 task 也 BLOCK);② 新模板生成的 task.json 带 `require_req_uc: true` capability;③ `trace-matrix <task_dir>` 默认读 task flag,**无 flag 的旧 task 默认 false → PASS**。BHV 缺 REQ-UC 在强制态 BLOCK。

### 2.6 跨模板同步矩阵(finding 2,blocker)

改 BHV 编号契约**必须同步全部**(否则跨模板漂移):

1. `requirement-doc-standard/single-source.md` §6(BHV 承接 REQ-UC 规则)+ §15.2(excludes 加 traceability)+ §15.4(单表 + 生成/手维护)。
2. **4 平台** `overview-structure-single-source.md`(flutter/go/h5/ios:BHV 承接 REQ-UC + UC 消歧说明)。
3. **4 平台** `harness/index.md`(编号纪律)。
4. **4 平台** workflow(flutter/go/h5/ios:BHV 口径)。
5. harness `versioned-requirements-package.md`(档 1 导读:traceability excludes + 生成区)。
6. CLI bundled + guru-template mirrored(`sync:guru`)。

## 3. 与档 3 gate digest 交互(决策 1 = B + codex 第三轮 fail-closed 前置)

- `canonical_excludes` 有硬编码默认 `(snapshots, changes)`(guru_gate.py:528),**不含 traceability**。`trace-aggregate` **写前 fail-closed 检查**目标目录 effective excludes 含顶层 `traceability`,满足才写(此时不触发 digest),否则拒写提示更新 manifest。
- 验证:① manifest excludes 含 traceability → aggregate 前后 `digest requirements` **不变**;② 无 manifest / 无 canonical_excludes / excludes 不含 traceability → aggregate **拒写**(不静默改 digest)。

## 4. 向后兼容

- 旧 prd(BHV 无 REQ-UC):trace-matrix `REQ-UC` 列空、不断链(`--require-req-uc` 关);task 级 `trace-matrix <task_dir>` 输出与改动前一致(回归)。
- `trace-aggregate` 新子命令,不影响 `trace-matrix <task_dir>`。
- 旧 `traceability.md` 无生成区标记:首次 aggregate 插入生成区,不丢既有手维护内容。

## 5. 测试

- BHV 带/不带/多 REQ-UC 解析;命名消歧(模板示例同现 `REQ-UC-005` 与 `UC-03` 不混字段)。
- trace-matrix `REQ-UC` 列;**task 级旧输出逐字节回归**。
- `trace-aggregate`:多 task 行展开;反查边界(无指针/别版本/非法路径/缺目录/symlink/archived/跨开发者 → skipped summary)。
- 单表回填:手维护 `Code/Test/Status` 按 key 保留;新增/删 BHV 标 orphan/stale 不丢旧证据;**aggregate 幂等**。
- **决策 1**:aggregate 不触发 requirements digest(traceability 在 excludes,回归 `digest requirements` 不变)。
- `--require-req-uc`:旧 PASS、新缺 BLOCK、新带多 REQ-UC PASS。
- finding 9 负例:aggregate 生成 `missing/untested/orphan` 状态,但 requirements/detail/implement gate **不因 traceability status 阻断**。
- 4 平台同步:`rg` 无残留「旧 BHV 口径而无 REQ-UC 说明」。

## 6. Bundled + sync

改 overlay(`guru_gate.py` + single-source)+ 4 平台 specs/workflows → `sync:guru`(整树)+ 传染处理 + `test guru`。**§2.6 同步矩阵逐项核对**(漏一处即漂移)。

## 7. 风险

- **跨模板同步范围大**(§2.6,4 平台 ×3 类文件 + standard + 导读 + bundled),漏一处即漂移 → 实现后 `rg` 全量核对。
- **决策 1 digest 前置(codex 第三轮纠正,见 §2.4)**:`canonical_excludes` **有**硬编码默认 `(snapshots, changes)`(guru_gate.py:528),manifest/字段缺失回退默认、**不含 traceability**。我前一轮「无全局默认/只影响新目录」的自核对**错误,已撤回**。`trace-aggregate` 必须 fail-closed 前置检查 effective excludes 含 traceability,否则拒写 —— 否则 manifest 未满足前提时写 traceability 会制造 digest/review stale。测试须覆盖四态(无 manifest / 无 canonical_excludes / excludes 不含 traceability / 含 traceability),前三必须拒写。
- 反查性能(46 task.json)+ realpath 归一 + status 过滤正确性。
- 单表回填 `(REQ-UC, UNIT)` key 稳定性(UNIT 改名/删除时的 orphan 处理)。

## 8. Open(实现 / codex 重审关注)

- 生成区标记机制对 `--aggregate` 幂等(HTML 注释 vs front-matter)。
- 单表回填的 orphan/stale 标记格式。
- ~~`--require-req-uc` 触发~~ → 已拍死(§2.5:CLI 显式强制 + task.json `require_req_uc` flag + 旧默认 false)。

## 9. 交付状态(2026-06-29)

- 实现完成并提交 `4c442d15`。Slice 1-2(主代理)+ Slice 3-7(trellis-implement)。
- **验证**:49 bridge + 10 e2e + 189 主套件 + fail-closed 独立对抗 4 + Slice1-2 验证 4,全绿。trellis-check(独立 fresh 视角)Go,并抓修 `_parse_existing_manual` 占位符往返不对称 bug(uncell fix);见 memory `test-self-confirmation-trap`。
- **codex opposite-provider 代码终审:已完成 → Go(2026-06-29)**。gateway 前 7 次阻塞(6×503 + 1×断流),第 8 次以 effort=low + 精简 prompt 赶在 cooldown 前完成。两项核对均 Go:① fail-closed 决策1(写前必经 `_excludes_has_traceability`、回退默认拒写、无绕过、`_MANIFEST_DEFAULT_EXCLUDES` 未改);② uncell 回填幂等(所有 parse cell 均过 uncell、无漏网)。**桥任务彻底闭环。**
- task 标 **completed**:实现已充分验证;codex 为额外跨 provider 保险,环境阻塞不无限卡 task。
