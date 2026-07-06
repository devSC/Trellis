# implementation-trace 合同

> `implement.md` / implementation-trace 是 detail Gate 的 digest-bearing planning contract。detail 确认后的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`。
> 建议路径：目标仓库 `docs/design/<feature>/implementation-trace.md`。若必须修改已确认 trace，必须回退 detail Gate 并重新 review/confirm。

## 必含四节

### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 任务切片 | 每片：承接的设计单元编号（`UNIT-<slug>`，幽灵引用被 gate 拦截）+ doc_type / **`target_paths` 文件范围摘要** / 完成信号 / 验证方式。**每片小到可独立 review**。**P1 high-risk slice 额外必填**：`slice_packet` 路径 + `invariant_ids` + `negative_case` 摘要（机器内容以 packet 为准；`UNIT-<slug>` 同时作 trace unit / packet 文件名 / `--slice` 参数）。 |
| 执行顺序 | 按依赖排序（通常自下而上：data → domain → presentation），人工选择从最小任务开始。 |
| 风险点 | 预判的高风险改动（迁移、共享状态、平台差异），逐条写验证手段。 |

### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个任务切片完成时记录下列字段：
- 实际改动文件清单（相对路径）。
- 与计划的偏差（改了计划外文件 / 没改计划内文件 → 必须写原因）。
- 代码生成执行记录（跑了哪个脚本，按 `[SLOT-08]`）。

### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

| 类型 | 要求 |
|------|------|
| 静态检查 | `flutter analyze` / `dart run custom_lint` 的执行结果（通过/失败+处理）。 |
| 测试 | 每个切片对应的测试命令 + 结果（测试名级别，不只写"通过"）；新增测试清单。**P1：测试按 invariant 归档**（不只按文件/命令）——每条 high-risk invariant 至少一个正/负测试作为其 `invariant_evidence`。 |
| 未验证项 | 无法本地验证的（真机表现、双端差异）→ 显式列出 + 留给哪个环节（Manual QA / 真机池）。 |

### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- 上游缺陷：详细设计合同错/漏（**含 invariant 缺失**）→ 记录后**回退详细阶段修订**，不就地改设计、不在实现 worker 内补造 invariant（`implementation-evidence.jsonl` 留回退记录）。
- 存量违例触碰：列出触碰的 SLOT-15 条目编号 + 处置（绕行/顺手修复/记债）。
- 未决决策：实现中冒出的新决策点 → 不私自拍板，记录并升级给人工 Gate。

## 反模式

- ❌ trace 在 PR 前一次性补写（失去过程证据意义）。
- ❌ mutable evidence 只写"全部通过"（无命令、无测试名）。
- ❌ 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
