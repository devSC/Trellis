# Guru review governance problem report and solution

## Goal

产出一份可执行的问题报告与治理方案，解释 Guru 系 review 为什么没有在 Himora V2 grouped-media 迁移中提前挡住跨层语义缺陷，并给出不强依赖 OCR 的修复路径。方案必须经过 Claude 独立审查，并按审查意见反复修订，直到不存在 blocker / should-fix 级问题。

2026-06-30 范围变更：在 `session-019f171a-root-cause-repair-plan.md` 已审查到无 blocker / should-fix 后，本任务继续落地 Guru/Trellis 流程根因修复。修复目标是防止 `019f171a-091d-7572-85ab-34b1d475b2e5` 暴露的三类违规再次发生：planning 任务直接实现/提交、Brainstorm Evidence 只有结构无真实 one-question 证据、`guru_gate.py check` 被误读为实现/提交放行。

## Requirements

- 报告必须区分“Guru review 完全失效”和“Guru review 在错误阶段 / 错误粒度 / 缺少可判定合同下漏检”。
- 报告必须基于当前 Guru 模板代码与 Himora 事故证据，不只做抽象流程建议。
- 方案必须明确 OCR 不是硬依赖；Claude / manual / Codex / OCR 都只能作为 semantic review provider，硬 Gate 应来自 deterministic checks、slice scope、invariant matrix 和 review record。
- 方案必须提出可落地的配置 / workflow / skill / runtime 修改点，并说明优先级、验收方式和风险。
- 必须记录每轮 Claude 审查输入、输出摘要、finding 处置和最终 clean 结论。
- 新增实现必须把 start / implementation / commit 三段生命周期 gate 分离，`guru_gate.py check` 只能兼容为 start 前置，不得继续被当成实现/提交放行。
- 新增实现必须让未 `task.py start` 的 planning 任务无法直接进入 `guru_supervise.py implement/check/implement-check`，也无法在有 active Guru task 时直接 `git commit` 交付代码。
- 新增实现必须强化 `Brainstorm Evidence`：高风险决策要么有 `Question Loop Log`，要么有 `Question Policy: evidence_only` 的覆盖理由；原始 bug 描述不得被当作当前轮用户确认。
- 新增实现必须强化人工确认记录的作用域：requirements/detail 的确认只允许推进到下一规划 gate 或 `task.py start`，不能隐式授权实现或提交。
- 新增实现必须同步 `guru-template` 源模板和 `packages/cli/src/templates/guru` 打包镜像，避免安装到目标项目后行为漂移。
- 2026-06-30 追加：需求文档在 `confirm requirements` 前必须先调用对应 requirements review skill / supervisor，直到当前 digest 无 medium+ 问题并记录 `review_result=clean/requirements-ready`；missing/deferred/blocked/stale 不能让用户确认。
- 2026-06-30 追加：概要设计与详细设计在 write/repair 后必须先调用各自 review skill / supervisor；overview 当前 digest 双 clean（含 adversarial）后才能进 detail，detail 当前 digest 双 clean（含 adversarial）后才能请求用户确认。

## Acceptance Criteria

- [x] `problem-report-and-solution.md` 包含问题报告、根因、影响、修复方案、实施计划、验收标准和风险矩阵。
- [x] `claude-review-brief.md` 明确要求 Claude 按 blocker / should-fix / nice-to-have 分类审查，不允许空泛意见。
- [x] `review-rounds.md` 记录每轮 Claude 审查结果和修订动作。
- [x] 至少完成一轮 Claude 审查；如 Claude 返回 blocker / should-fix，必须修订后继续下一轮。
- [x] 最终 Claude 审查结论为无 blocker / should-fix；若只剩 nice-to-have，必须在报告中标为后续项或明确拒绝理由。
- [x] 第一阶段不修改产品代码；只修改任务报告与必要的方案文档。
- [x] `session-019f171a-root-cause-repair-plan.md` 已回答 019f171a 是否符合当前规范、为何未逐问确认、为何 review 后直接实现、是否正确触发 brainstorm。
- [x] `design.md` 定义 lifecycle gate、commit hook、brainstorm evidence、current-turn confirmation、supervise guard、review record 写入和模板同步的技术方案。
- [x] `implement.md` 定义可执行顺序、风险文件、验证命令、回归夹具和回退点。
- [x] 修复后，未运行 `task.py start` 的 Guru full-chain planning task 即使 planning gate 全绿，也不能直接 `git commit`。
- [x] 修复后，`guru_supervise.py implement/check/implement-check` 在 task status 非 `in_progress` 时 fail-closed，不启动 worker。
- [x] 修复后，只有结构化标签但没有 `Question Loop Log` / `Question Policy` 的 `Brainstorm Evidence` 不得通过 requirements gate。
- [x] 修复后，`guru_gate.py status/check-start` 输出必须明确 `START_READY` 只允许下一步 `task.py start`，不能出现可被理解为实现/提交放行的文案。
- [x] 修复后，Guru overlay apply 在 Claude Code 与 Codex 项目中都能安装并注册 `block-unstarted-commit`；Codex 用户级 hooks/trust 未开启时必须有明确提示，且 `guru_gate.py check-commit` 仍可手动复跑。
- [x] 修复后，源模板与 CLI 打包镜像通过 mirror 一致性检查。
- [x] `confirm requirements` 在缺少 clean/current requirements adversarial review、review blocked/deferred 或 digest stale 时返回阻断，不再只是警告。
- [x] `check-start` 在缺少 clean/current requirements adversarial review、review blocked/deferred 或 digest stale 时返回阻断，即使 requirements/detail 确认与 overview/detail review 已齐。
- [x] `guru_supervise.py --adversarial requirements` 遇到 `REQ_BLOCKER`、缺 verdict、worker skip/deferred 时返回非 0，同时保留 `requirements_review` 状态证据；只有 `review_result=clean/requirements-ready` 返回成功。
- [x] 四端 workflow/spec 明确 overview/detail write/repair 后必须先完成各自 review，才能进入下一阶段或请求 detail confirm。

## Brainstorm Evidence

- Skill loaded: 已加载 `full-cycle-plan-repair`、`plan-reviewer`、`trellis-channel`，本任务定位为方案闭环与跨代理审查，不进入产品代码实现。
- Repository evidence inspected: 已检查 `guru_gate.py`、`guru_supervise.py`、`guru_review_record.py`、`block-unconfirmed-start.sh`、`config.hooks.yaml`、`requirement-writing/review`、`implementation-trace-contract`、Guru workflow、Himora 019f171a 会话日志、目标 task/prd/task.json 与当前 dirty worktree。
- Domain/terminology triggers: 触发。关键词包括 Guru review、semantic review provider、OCR hard dependency、slice review packet、invariant matrix、deterministic checks、dirty diff hygiene、route_class。
- Current code vs user intent conflicts: 当前 Guru runtime 已有 start 前置 gate 和实现期 review record 基座，但 `check` 只拦 `task.py start`，不拦未 start 直接实现/提交；Brainstorm Evidence 检查主要验证结构，不能证明真实 one-question loop；`guru_supervise.py` 的 implement/check 禁止提交是 prompt 约束，不是 lifecycle 硬闸。
- Product decisions confirmed: 用户先要求输出本地根因修复方案并审查到无问题；方案完成后，用户确认“好”，同意复用本任务继续补齐规划产物并在 review gate 后进入实现。
- Open product/scope/risk questions: 无阻断问题。本任务当前包含治理方案和 Guru runtime/template 根因修复落地；不修改 Himora 产品代码，也不评价 `b841e5dd` 业务修复正确性。

### Question Loop Log

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-019F-001 | 2026-06-30 | 是否允许复用已有 `06-28-guru-review-governance-report` 任务，基于根因方案补齐规划产物，待 `task.py start` 后进入代码实现？ | 复用已有任务，先修订 PRD/design/implement，再过 gate；不直接改代码。 | 另开任务边界更干净，但会让同一治理问题的证据和实现计划分散；直接改代码会再次违反当前 Trellis 规范。 | 好 | DEC-019F-001 复用本任务继续规划并准备实现 | prd.md / design.md / implement.md |
| OQ-019F-002 | 2026-06-30 | requirements / overview / detail 的 write 与 confirm 边界是否要收紧为“先 review 到无 medium+ 问题，再允许确认或进入下一阶段”？ | 收紧为硬规则：requirements confirm 前必须 clean/current requirements review；overview/detail write 后必须完成各自 review，detail clean 后才可请求确认。 | 会增加流程耗时，但消除“写完即确认”“deferred 当 clean”“需求 review 只警告”的事故路径。 | 好，需求文档在确认之前需要先调用对应的review skill直至无中等问题后才能让我确认，概要设计，详细设计 write 之后也要先各自调用review，确保无问题后再让我确认 | DEC-019F-002 收紧 requirements / overview / detail review-before-confirm 边界 | prd.md / design.md / implement.md |

### Question Policy

question_policy: mixed

证据已回答的问题：事故事实、当前代码落点、流程根因、模板镜像同步边界均可由仓库文件和会话日志回答，不再询问用户。

用户已确认的问题：是否复用当前治理任务继续进入规划与后续实现，由 `OQ-019F-001` 当前轮回答确认；是否收紧 requirements / overview / detail review-before-confirm 边界，由 `OQ-019F-002` 当前轮回答确认。

## Notes

- 审查闭环最终按用户更严格口径收敛：Claude Round 16 结论为 `review_result=clean`、`max_severity=none`，无 blocker、无 should-fix、无 nice-to-have。
- `session-019f171a-root-cause-repair-plan.md` 是本轮根因修复方案 SSOT；`design.md` / `implement.md` 只承接其已审查结论并转成可执行实现计划。
