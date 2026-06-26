Trellis SessionStart 上下文已加载。

---

## 对抗性需求审查结论

### F-001【高】REQ-004 与 design.md §3 定义不一致

**位置**: `prd.md REQ-004` vs `design.md Section 3`

PRD 明确"最低硬性结构"是 `user_quote` **或** `confirmed_ref`（二选一）。design.md Section 3 添加第三选项："`confirmed_by` + `confirmed_at` + exact decision text"。implement.md Step 6 的测试矩阵没有覆盖该第三选项。

若实施者按 design.md 写 gate，则标准比 PRD 宽松（三条路均可通过），未来 `confirmed_by+confirmed_at` 无 quote 的情形能过关。若按 PRD 写，第三选项测试缺失。**两份文件互相矛盾，实施前必须选定一个权威来源并同步另一方。**

---

### F-002【高】implement.md 缺少 `sync:guru` 步骤

**位置**: `implement.md Steps 1-8`

项目 memory (`guru-template-bundled-dual-source.md`) 明确：修改 `guru-template/overlay/` 后必须运行 `sync:guru` 将变更同步到 bundled CLI 模板，否则 CLI 发布旧态分叉。implement.md Steps 3/5 均涉及 `guru-template/overlay/` 路径，但整个执行计划无 sync 步骤。漏掉 sync 会导致本 worktree 测试通过但 `packages/cli` 生成产物未更新，与 design.md Compatibility 节的目标直接矛盾。

---

### F-003【中】REQ-003 批量例外无对应 BHV 规格

**位置**: `prd.md REQ-003` vs `BHV-001~005`

REQ-003 引入了批量例外："用户明确要求批量确认，agent 可以一次列出 2~4 个问题，但必须逐项记录用户回答；没有逐项回答的问题仍为 open。" 五条 BHV 规格仅覆盖"单问"场景（BHV-003）。**批量流程缺乏可测试的行为规格**——包括：什么算"用户明确要求"、agent 如何记录逐项回答、gate 如何区分批量已答和批量未答。这个例外是当前 `1~4` 漏洞的保留形式，没有 BHV 就无法验收。

---

### F-004【中】gate 设计中"positive"语义不可解析

**位置**: `design.md §5 Gate Structure Checks`

> "If `Product decisions confirmed` is positive, require confirmation hints."

Markdown 自由文本中"positive"无操作定义：是指该节非空、包含正向词（"confirmed"/"yes"）、或含有 bulleted 条目？gate 是结构性检查，缺乏精确的判断规则会让实现者自行猜测，导致两种极端：全过（太松）或大量误报（太紧）。

---

### F-005【中】REQ-006 "证据收集" 边界未闭合

**位置**: `prd.md REQ-006`

REQ-006 允许 `继续` 做"证据收集、结构整理、review"，但未定义这些操作是否可以写回 `prd.md` / requirements 包。若 agent 借"结构整理"把 `ai_drafted` 条目重组后写入文件，即构成绕过 one-question loop 的路径。缺少一条明确约束："证据收集期间不得修改 `confirmation_status`"，或者一条对应 BHV 规格。

---

### F-006【中】验收标准 "不影响既有 Gate" 不可测

**位置**: `prd.md Acceptance Criteria` 最后两条

"不影响既有 overview/detail clean review 与 detail confirm Gate" 没有关联任何回归测试用例、fixture 或 snapshot 检查。当前 AC 是一句意图声明，无法在 Phase 3 验证。需要补充：引用现有测试路径，或在 implement.md Step 6 中加一条"运行现有 Gate 回归套件并通过"。

---

### F-007【低】Step 7 gate 验证设为条件可选

**位置**: `implement.md Step 7`

> "Run `guru_gate.py requirements` if Guru gate is available in this worktree; otherwise document absence."

本任务的主交付物之一是增强 gate 检查。如果 gate 脚本本身不可用，则核心验收标准（REQ-005, BHV-004）无法在 worktree 内自验证。"document absence"不是可接受的出口条件；应先在 Step 0/Preconditions 确认 gate 可运行，或在 Step 7 将不可用情况定义为阻断项而非文档化跳过。

---

## 汇总

| 编号 | 严重度 | 类型 | 一句话 |
|------|--------|------|--------|
| F-001 | 高 | 内部不一致 | PRD REQ-004 与 design §3 对最低证据要求有分歧 |
| F-002 | 高 | 流程缺陷 | implement.md 缺 sync:guru，guru-template 变更不会同步到 CLI |
| F-003 | 中 | 规格缺口 | 批量例外无 BHV 规格，不可验收 |
| F-004 | 中 | 不可测 | gate "positive" 无操作定义 |
| F-005 | 中 | 边界模糊 | REQ-006 证据收集范围未限制 confirmation_status 写回 |
| F-006 | 中 | 不可测 | 现有 Gate 回归无测试路径 |
| F-007 | 低 | 流程缺陷 | gate 验证步骤设为可选，主交付物不可自验 |

---

`review_result=findings route_class=PROCESS_DEFECT max_severity=high`
