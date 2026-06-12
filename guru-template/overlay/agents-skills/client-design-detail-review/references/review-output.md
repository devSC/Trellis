# 详细审核输出合同（references）

> 输出分支、字段与顺序以本文件为唯一主定义；与其他说明冲突时以本文件为准（规则正文仍以 L1 为准）。

## 分支一：前置缺口输出（EX-1~EX-6 任一失败）

```markdown
## 详细审核：前置阻断

**EX 缺口**（逐条：EX 编号 / 缺口 / 证据）
**修复动作**（逐条最小动作；EX-3/EX-5 类缺口必须写"回退概要"而非详细侧补造）
**结论**：前置未通过，不进入逐文档诊断。
```

## 分支二：诊断输出（前置通过）

### 1. scope 声明

`review_scope`（current_chapter / layer_checkpoint(<层>) / directory_final）+ 本次范围内目标清单 + 范围外未审清单（明示"范围外未审"，防止误读为通过）。

### 2. 逐文档概况表（current_chapter / directory_final 必含）

```markdown
| 章节 | doc_type | l2 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | findings |
|------|----------|----|----|----|----|----|----|----|----|----|----|
| recognition-usecase | usecase | v1 | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | P2×1 |
```

缺失目标文档单列：`缺失清单 + 修订方案`（不进 D 诊断）。

### 3. Findings（按严重度分组，每条五字段 + 受影响 G 项）

```markdown
**P1-1** ｜ location：chapters/scan-food-page.md §4.2 ｜ problem：页面内实现重试计数（业务规则越权）
｜ evidence：流程详述第 3 步"retryCount>=3 时禁用按钮" ｜ suggestion：规则上收 RecognitionUseCase，页面只消费状态
｜ 受影响 G 项：G2
```

薄文档命中时（review-baseline §6）：跳过逐条列举，输出薄文档证据（雷同章节对照 + 占位统计）+ 文档级重构方案。

### 4. 跨层链路状态（directory_final / layer_checkpoint 必含）

四个层边界（review-baseline §4）逐项 pass/fail + 失效位置。

### 5. 覆盖率状态（directory_final 必含）

索引↔章节差集 / UC 链路抽查结果 / 时序↔行为抽查结果。

### 6. G1~G7 状态表

```markdown
| G 项 | 状态 | 证据/阻塞 finding |
```

light 链 G6~G7 标注 `N/A(light)` 并说明单文件口径已满足。

### 7. 三选一结论（互斥）

- `可进入编码`
- `带明确假设可进入`：逐条假设、依据、验证时点
- `不可进入`：阻塞 P1 清单 + 修订形态建议（局部修订 / 文档级重构，按 L1 §9；概要缺陷标注"回退概要"）

### 8. Gate 收口指引（结论为可进入/带假设可进入时必须输出）

```markdown
请用户本人在终端运行（agent 不得代跑）：
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir>
确认落盘后方可 task.py start（before_start 钩子强制校验）。
```

## 复审闭环

按 findings 修订后复审：只复查受影响章节的 D 诊断 + 其跨层引用，输出「复审范围 / 原 finding 关闭状态 / 新增 finding / 更新后 G 状态与结论」。current_chapter 复审通过不改变目录级结论——目录级结论只能由 directory_final 产生。
