# Implementation Plan: Bridge REQ-UC and BHV

> 改 `guru_gate.py`(trace-matrix + 新 `trace-aggregate`)+ BHV 编号契约(4 平台)。据 codex 9 findings + 3 决策返工(design §0)。
> planning(本轮返工)交付前再经 codex 对抗审查。

## 1. Plan

### Slice 1: BHV 承接 REQ-UC 解析(多对多)+ 命名消歧

- `guru_gate.py` 从 BHV 标题提取 `[REQ-UC-XXX]`(多个);文档明确 `REQ-UC` ≠ `UC-<序号>`。

### Slice 2: trace-matrix `REQ-UC` 列(行展开)

- `build_trace` 收集 BHV→[REQ-UC];`render_matrix` 行展开;**task 级旧输出逐字节回归**。

### Slice 3: `trace-aggregate` 子命令 + 反查策略

- 新子命令(parser 明确分支);反查复用 `_requirement_package_dir`;**扫描根默认 `.trellis/tasks/<task>`,`--include-completed` 加扫 `archive/<YYYY-MM>/<task>`**;skipped summary 分类;兼容历史 status。

### Slice 4: traceability 单表回填 + canonical_excludes(决策 1)

- 生成区单表回填(`(REQ-UC, UNIT)` key,orphan/stale,幂等);**`trace-aggregate` 写前 fail-closed 检查 effective excludes 含 traceability,否则拒写**(canonical_excludes 有硬编码默认 snapshots/changes、不含 traceability,guru_gate.py:528;**不改代码默认**);改 single-source §15.2 示例 + 档 1 §10。

### Slice 5: `--require-req-uc` 模式

- 新模式拦无 REQ-UC(不复用 strict);**触发合同:CLI 显式强制 + task.json `require_req_uc` flag + 旧 task 默认 false PASS**。

### Slice 6: 跨模板同步矩阵(finding 2,blocker)

- single-source §6/§15.2/§15.4 + 4 平台 overview-structure-single-source + 4 平台 harness index + 4 平台 workflow + 档 1 versioned-package 导读。逐项核对,`rg` 防漏。

### Slice 7: 测试 + sync

- 测试见 design §5;改 overlay + 4 平台 specs/workflows → `sync:guru` + 传染处理 + `test guru`。

## 2. Validation Checklist

- [ ] `git diff --check`;`task.py validate`
- [ ] BHV 解析(多 REQ-UC)/ REQ-UC 列行展开 / 命名消歧测试
- [ ] **task 级 `trace-matrix <task_dir>` 逐字节回归**(向后兼容)
- [ ] `trace-aggregate` 反查边界(无指针/别版本/非法/缺目录/symlink/**archive 月份树路径**/跨开发者 + skipped summary 分类)
- [ ] 单表回填:手维护 Code/Test/Status 按 key 保留、orphan/stale 不丢、**aggregate 幂等**
- [ ] **决策 1 fail-closed 四态**:manifest excludes 含 traceability → aggregate `digest requirements` 不变;**无 manifest / 无 canonical_excludes / excludes 不含 traceability → 拒写**
- [ ] `--require-req-uc` 触发三类:旧 task 无字段 PASS / 新 task `require_req_uc:true` 缺 REQ-UC BLOCK / 显式 CLI flag 即使旧 task 也 BLOCK
- [ ] finding 9 负例:traceability status 不阻断 gate
- [ ] **4 平台同步**:`rg` 无残留「旧 BHV 口径无 REQ-UC」
- [ ] 改 overlay → sync + `git diff packages/cli/src/templates/guru` 核对
- [ ] 未回退 06-24/06-26/06-28 已提交改动

## 3. Risk Points

- **跨模板同步范围大**(§2.6 矩阵:4 平台 ×3 类 + standard + 导读 + bundled),漏一处即漂移 → 实现后 `rg` 全量核对。
- **§15.2 默认 excludes 加 traceability**是 spec 级新基线:无真实 `versions/` 目录故无实际回归,但须标注 + 迁移说明随档 4。
- 反查性能(46 task.json)+ realpath 归一 + status 过滤。
- 单表回填 `(REQ-UC, UNIT)` key 稳定性(UNIT 改名/删 → orphan)。
- `trace-matrix` blast radius(断链拦截被详细/实现 Gate 用)→ 只增量 REQ-UC、不改既有断链口径(回归守门)。
- overlay 传染(同档 1/2/3)。

## 4. Rollback Plan

- 逐文件 `git checkout -- <仅本任务文件>`;禁全量。
- 保护:06-24 改动、06-26/06-28 已提交内容。
- sync 大范围 bundled 改动先 `git diff` 审查,只 add 本任务。

## 5. Open Confirmation Before Implementation

- 3 合同决策已拍板(design §0)。
- design §8 实现期 Open(生成区标记 / orphan 格式 / --require-req-uc 触发)待实现定 + codex 重审。
- 本轮返工后的 planning 交付前再经 codex 对抗审查(闭环确认 9 findings 修好、无新引入)。
