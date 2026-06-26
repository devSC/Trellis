Trellis SessionStart 上下文已加载，直接进入 Round 4 对抗性需求审查。

---

## Round 4 审查结果

以下为新发现的问题（F-001..F-007 已被前三轮修复，本轮不重复计分）。

---

### F-008 ｜MEDIUM｜`confirmed_by` 孤儿字段

**位置**: PRD REQ-005 第一个风险条件列表。

REQ-005 将 `confirmed_by` 列为 Gate 应检测的缺失字段之一（"缺 `user_quote` / `confirmed_at` / `confirmed_by` / `confirmed_ref` / `用户确认`"），但：

- REQ-004 推荐格式中不存在 `confirmed_by`。
- PRD 自身的 Brainstorm Evidence 示例（DEC-001、DEC-002）也不含此字段。
- Design.md Section 5 的 Gate 实现规则只提 `user_quote` 或 `confirmed_ref`。

Gate 实现者要么跳过这个检查（因为没有格式依据），要么强制要求一个任何标准都不要求填写的字段。须删除 `confirmed_by` 或在 REQ-004 推荐格式中定义它。

---

### F-009 ｜HIGH｜`evidence_ready` 未定义 + REQ-006 / BHV-007 约束范围不一致

**两个关联问题，共同造成 one-question loop 核心边界漏洞。**

**9a — `evidence_ready` 无定义**
REQ-002 和 REQ-006 均使用 `confirmation_status=evidence_ready`，但 Definitions 章节无此术语。实现者无法判断它与 `ai_drafted` 的区别是什么。

**9b — REQ-006 约束比 BHV-007 窄**
REQ-006 的触发条件是"P0/P1 `confirmation_status=ai_drafted`"，只保护 `ai_drafted` 状态；BHV-007 则禁止 `continue` 将*任何* `confirmation_status` 改为 `user_confirmed*`。

后果：若某条决策状态为 `evidence_ready`（尚无用户确认），`continue` 按 REQ-006 字面执行不会触发拦截，但 BHV-007 要求拦截。这是核心特性——"continue 不得越过业务拍板边界"——的逻辑漏洞。须将 REQ-006 触发条件扩展为 `ai_drafted` **或** `evidence_ready`，并在 Definitions 补充 `evidence_ready` 定义。

---

### F-010 ｜MEDIUM｜批量确认时 `user_quote` 归属逻辑未定义

**位置**: REQ-003 + BHV-006。

REQ-003 要求"逐项记录用户回答"；BHV-006 要求每个 confirmed 问题有"独立 `user_quote`"。但当用户发出一条批量确认消息（如"这几个都按推荐处理"），PRD 未说明：

- 该消息是否可以被复制为每个问题的 `user_quote`？
- Gate / review 应拒绝、允许，还是需要区分？

实现者和 review 者对"独立 user_quote"的解读将不一致，直接影响 FP-001 的判断。

---

### F-011 ｜MEDIUM｜REQ-006 未封堵"详细设计"入口

**位置**: REQ-006 + BHV-005。

REQ-006 禁止 `continue` "进入概要设计或 `task.py start`"，但**没有提到详细设计**。BHV-005 明确列出"概要 / 详细 / start"全部封堵。

若实现仅依据 REQ-006，`continue` 在存在未解决 high-risk OQ 时仍可合法进入详细设计阶段，绕过业务拍板边界。须在 REQ-006 中补加"详细设计"。

---

### F-012 ｜LOW｜skill 文件行为无自动化测试，AC 不可机器验证

**位置**: Acceptance Criteria + implement.md Step 7。

AC 包含两条以 skill 文件为实现载体的要求：
1. "trellis-continue 在 planning + high-risk OQ 时恢复到 one-question loop"
2. "requirement-review 能把缺少 one-question evidence 的 P0/P1 决策判为 blocker 或 process defect"

implement.md Step 7 的测试全部针对 `guru_gate.py` Python fixture，无一覆盖 skill 文件（Markdown）。这两条 AC 只能通过人工阅读验证，不能通过运行测试验证。须为 skill 文件行为明确说明验证方式（如"由 reviewer 对照 AC checklist 审阅文件内容"），或承认这是人工验收项并在 AC 中标注。

---

### F-013 ｜LOW｜Design Section 5 "nearby" 无操作定义

Design.md Section 5: "If `prd` contains `confirmation_status=user_confirmed*`, require a nearby `user_quote` or `confirmed_ref`."

"Nearby"未定义（同行？同缩进块？同 section？）。门控实现者将自行决定，导致 Gate 行为不可预测。建议改为"同一决策条目或其直接缩进子块中"。

---

## 汇总

| 编号 | 严重程度 | 核心问题 |
|------|----------|----------|
| F-008 | MEDIUM | `confirmed_by` 在 Gate 检查中但在格式规范中不存在 |
| F-009 | HIGH | `evidence_ready` 未定义；REQ-006 不封堵 `evidence_ready→user_confirmed*` 转换，BHV-007 封堵 |
| F-010 | MEDIUM | 批量单条消息如何归属为多个独立 `user_quote` 未定义 |
| F-011 | MEDIUM | REQ-006 漏掉"详细设计"，BHV-005 已封堵 |
| F-012 | LOW | skill 行为 AC 仅可人工验证，Step 7 无测试 |
| F-013 | LOW | "nearby" 操作含义未定 |

`review_result=findings route_class=REQ_BLOCKER max_severity=high`
