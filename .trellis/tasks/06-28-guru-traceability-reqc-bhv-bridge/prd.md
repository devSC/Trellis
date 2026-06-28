# Bridge REQ-UC and BHV for versioned traceability auto-linking

## Goal

让版本级 `traceability.md`(用 `REQ-UC`)与 task 级 `trace-matrix`(用 `BHV`/`UNIT`)自动连通,使版本级 traceability 的 BHV/UNIT 派生部分可由 `trace-aggregate` 生成、不再纯手维护 —— 闭合档 1 REQ-005 / 档 3 标注的「REQ-UC↔BHV 桥」前置。

## Background

- prd 的 `BHV-NNN`(`guru_gate.py BHV_DEF`)承接需求包 `REQ-UC` 场景(workflow:195),但无显式 BHV→REQ-UC 映射。
- `trace-matrix`(`build_trace`)单 task,无 `REQ-UC` 列、无多任务聚合(档 3 codex 证实)。
- 版本级 `traceability.md`(档 1 / §15.4)用 `REQ-UC`、手维护、与 trace-matrix 不连通。task→version 关联:档 3 `requirement_package` 指针。
- **codex 对抗审查(2026-06-29,Needs-rework)+ 用户 3 决策**(见 design §0):决策 1 = traceability 加 `canonical_excludes` 不触发 digest;决策 2 = BHV↔REQ-UC 多对多行展开;决策 3 = `REQ-UC`(需求源)≠ `UC-<序号>`(overview 用例)命名消歧。

## Requirements

### REQ-001: BHV 显式承接 REQ-UC(多对多 + 命名消歧)

prd 的 BHV 标题带 `[REQ-UC-XXX]`(可多个);BHV↔REQ-UC **多对多**(决策 2)。**命名消歧(决策 3)**:`REQ-UC` 是需求源场景(single-source §6),与 overview `UC-<序号>`(架构核心用例,overview §3.2)是**两套独立编号**,不混用字段。

### REQ-002: trace-matrix `REQ-UC` 列(行展开)

`trace-matrix` 解析 BHV 的 `[REQ-UC]`,矩阵增 `REQ-UC` 列,多 REQ-UC **行展开** `(REQ-UC, BHV, UNIT, Source Task)`;task 级旧输出兼容。

### REQ-003: `trace-aggregate` 子命令 + 反查策略

新子命令 `trace-aggregate <version-dir> [--include-completed]`(不复用 trace-matrix task_dir 解析)。反查 **默认扫 `.trellis/tasks/<task>/task.json`(排除 `archive/`)**,`--include-completed` **加扫 `.trellis/tasks/archive/<YYYY-MM>/<task>/task.json`**(归档是月份分层目录);realpath 归一;非法指针只在候选匹配时 fail、其余 skipped;**skipped summary 分类**(无字段/别版本/非法/归档未 include/历史 schema);兼容 status 缺失/completed/archived。

### REQ-004: traceability 单表回填 + 不触发 digest(决策 1)

`traceability.md` 用 §15.4 **单表**;`trace-aggregate` 生成 `REQ-UC|Source Task|UNIT|BHV` 派生列,`Code Entry|Test|Status` 按 `(REQ-UC, UNIT)` key **回填保留**(不丢手维护,BHV 增删标 orphan/stale)。traceability 加 `manifest.canonical_excludes` → **不触发** requirements digest。**⚠️ `canonical_excludes` 有硬编码默认 `(snapshots, changes)`**(guru_gate.py:528,不含 traceability):`trace-aggregate` 写前 **fail-closed 检查**目标目录 effective excludes 含 traceability,否则**拒写 + 提示更新 manifest**(不静默触发 digest);不改代码默认。

### REQ-005: `--require-req-uc` 模式

新模式(不复用 `--strict`)拦 BHV 缺 REQ-UC。**触发合同**:① `--require-req-uc` 显式 CLI 强制(旧 task 也 BLOCK);② 新模板 task.json 带 `require_req_uc: true`;③ 默认读 task flag,无 flag 旧 task false → PASS。

### REQ-006: 跨模板同步(finding 2,blocker)

BHV 编号契约改动须同步:single-source §6/§15.2/§15.4 + **4 平台**(flutter/go/h5/ios)的 overview/index/workflow + 档 1 导读 + CLI bundled/mirrored。漏一处即跨模板漂移。

### REQ-007: 向后兼容

旧 prd(BHV 无 REQ-UC):trace-matrix `REQ-UC` 列空、不断链;`trace-matrix <task_dir>` 输出与改动前一致;`trace-aggregate` 是新子命令不影响既有。

### REQ-008: bundled 同步 + 测试 + codex 对抗审查

改 `guru_gate.py` + spec 后 sync + 测试;planning(本轮已返工)与代码均经 codex opposite-provider 对抗审查。

## Out Of Scope

- 不改 gate digest **失效算法**(决策 1 = B:traceability 加 excludes 是配置,不改 digest 计算)。
- 不动 overview `UC-<序号>` 体系(决策 3:独立,仅命名消歧 + 文档说明)。
- 不迁移真实项目(档 4)。

## Open Questions(本轮已拍板)

- OQ-1 ✅ A(BHV 标题带 `[REQ-UC]`)。
- OQ-2 ✅ A(`trace-aggregate` 子命令)。
- OQ-3 ✅ 接受改 BHV 编号契约 + **4 平台同步**(finding 2)。
- OQ-4 ✅ → **决策 1 = B**(traceability 加 `canonical_excludes`,不触发 digest)。
- **决策 2** ✅ 多对多行展开;**决策 3** ✅ 命名消歧。
- **codex 第三轮(2026-06-29)收敛**:9 项 = 6 闭合 + 2 半闭合 + 3 未闭合,3 项已据 codex 建议修正(finding 1 fail-closed 前置 + 撤回我的 manifest-per-dir 自核对错误;finding 2 扫 archive 月份树;finding 3 触发合同拍死)。
- 实现期 Open(design §8):生成区标记机制、orphan/stale 格式。

## Brainstorm Evidence

- Repository: `guru_gate.py` `BHV_DEF`/`build_trace`/`render_matrix`/`cmd_trace_matrix`;workflow:195;single-source §6/§15.2/§15.4;4 平台 overview-structure-single-source §3.2(已有 BHV↔UC-<序号>);档 1 REQ-005、档 3 桥前置。
- codex 对抗审查 2 轮(`scratchpad/codex-review-bridge2.txt`):Needs-rework → 3 决策 + 9 findings 已纳入 design §0/§2。
- Product decisions: 3 决策(见 design §0)。
- **流程**:planning 交付前经 codex opposite-provider 对抗审查(memory `codex-adversarial-review-before-delivery`);本轮为返工后第二次审查前。
