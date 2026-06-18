# 概要审核输出合同（references）

> 输出分支、字段与顺序以本文件为唯一主定义；与其他说明冲突时以本文件为准（规则正文仍以 L1 为准）。

## 分支一：前置阻断输出（EX-1~EX-4 任一失败）

只输出以下三段，不展开逐章审核：

```markdown
## 概要审核：前置阻断

**前置缺口**（逐条：EX 编号 / 缺口 / 证据）
- EX-2：design_package 缺 chapters/ 目录（ls 取证）

**修复动作**（逐条最小动作，含回退指向）
- 建立 chapters/ 空目录并重跑 guru_gate.py overview

**结论**：前置未通过，不进入逐章审核；修复后重新送审。
```

需求准入失败时，修复动作必须写"回退需求阶段"而非概要侧补救。

## 分支二：全量门禁输出（前置通过）

按以下顺序与字段输出：

### 1. 架构视图检查摘要（放最前——评审者先看图）

```markdown
| 件 | 状态 | 备注 |
|----|------|------|
| 一句话架构 | ✅/❌ | |
| 分层架构图 | ✅/❌ | 节点×N，方向合规/违例位置 |
| 页面流图 | ✅/❌/N-A | |
| 核心 UC 表 | ✅/❌ | UC×N |
| UC 承接表 | ✅/❌ | 断链清单 |
| 时序图策略表 | ✅/❌ | 独立×N/合并×N/豁免×N；占位残留清单 |
```

### 2. Findings（按严重度分组，每条五字段）

```markdown
**P1-1** ｜ location：§3 归属表 BHV-021 行 ｜ problem：识别重试规则归给 Controller，违反分层依赖律
｜ evidence：归属表原文"重试由 controller 定时发起" ｜ suggestion：owner 改 RecognitionUseCase，controller 仅订阅状态
｜ 受影响 G 项：G2
```

同一根因多处表现合并为一条，列全部 location。

### 3. 结构概况（一段话）

链型、主定义位置、BHV/UC/索引条目计数、整体形态评价（≤4 句）。

### 4. G1~G8 状态表

```markdown
| G 项 | 状态 | 证据/阻塞 finding |
|------|------|------------------|
| G1 行为覆盖 | pass / fail | |
| ...G8 | | |
```

light 链 G6~G8 标注 `N/A(light)` 并说明简化口径已满足（L1 §2b）。

### 5. 三选一结论（互斥）

- `可进入详细设计`
- `带明确假设可进入`：逐条列假设、依据、验证时点
- `不可进入`：列阻塞 P1 清单 + 修订形态建议（局部修订 / 文档级重构，按 L1 §8）

### 6. Review Evidence 收口指引（结论为可进入/带假设可进入时必须输出）

```markdown
记录本次 clean review（使用新的 run_id）：
python3 .trellis/scripts/guru/guru_gate.py record-review overview <task_dir> --result clean --max-severity low --reviewer clean-context --run-id <fresh-run-id> --evidence "<本次概要审核证据摘要>"

当前 digest 下两个不同 run_id 的 clean review 后，overview 自动通过；不要运行 confirm overview。
```

## 复审闭环

按 findings 修订后复审：只复查受影响章节与其跨章一致性项，输出"复审范围 + 原 finding 关闭状态 + 新增 finding（若有）+ 更新后的 G 状态表与结论"；不重复输出未受影响章节的全量取证。
