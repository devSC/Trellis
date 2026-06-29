# Guru review governance problem report and solution

## Goal

产出一份可执行的问题报告与治理方案，解释 Guru 系 review 为什么没有在 Himora V2 grouped-media 迁移中提前挡住跨层语义缺陷，并给出不强依赖 OCR 的修复路径。方案必须经过 Claude 独立审查，并按审查意见反复修订，直到不存在 blocker / should-fix 级问题。

## Requirements

- 报告必须区分“Guru review 完全失效”和“Guru review 在错误阶段 / 错误粒度 / 缺少可判定合同下漏检”。
- 报告必须基于当前 Guru 模板代码与 Himora 事故证据，不只做抽象流程建议。
- 方案必须明确 OCR 不是硬依赖；Claude / manual / Codex / OCR 都只能作为 semantic review provider，硬 Gate 应来自 deterministic checks、slice scope、invariant matrix 和 review record。
- 方案必须提出可落地的配置 / workflow / skill / runtime 修改点，并说明优先级、验收方式和风险。
- 必须记录每轮 Claude 审查输入、输出摘要、finding 处置和最终 clean 结论。

## Acceptance Criteria

- [x] `problem-report-and-solution.md` 包含问题报告、根因、影响、修复方案、实施计划、验收标准和风险矩阵。
- [x] `claude-review-brief.md` 明确要求 Claude 按 blocker / should-fix / nice-to-have 分类审查，不允许空泛意见。
- [x] `review-rounds.md` 记录每轮 Claude 审查结果和修订动作。
- [x] 至少完成一轮 Claude 审查；如 Claude 返回 blocker / should-fix，必须修订后继续下一轮。
- [x] 最终 Claude 审查结论为无 blocker / should-fix；若只剩 nice-to-have，必须在报告中标为后续项或明确拒绝理由。
- [x] 本任务不修改产品代码；只修改任务报告与必要的方案文档。

## Brainstorm Evidence

- Skill loaded: 已加载 `full-cycle-plan-repair`、`plan-reviewer`、`trellis-channel`，本任务定位为方案闭环与跨代理审查，不进入产品代码实现。
- Repository evidence inspected: 已检查 `guru_gate.py`、`guru_supervise.py`、`flutter-implementation-guru-review`、`implementation-trace-contract`、Guru workflow、Himora 事故记忆摘要与当前 dirty worktree。
- Domain/terminology triggers: 触发。关键词包括 Guru review、semantic review provider、OCR hard dependency、slice review packet、invariant matrix、deterministic checks、dirty diff hygiene、route_class。
- Current code vs user intent conflicts: 当前 Guru runtime 对实现期 review 的输入仍是宽泛 current diff，且 implementation check 没有和 OCR policy / invariant matrix / dirty scope gate 绑定；用户明确不希望强依赖 OCR。
- Product decisions confirmed: 用户要求输出问题报告和解决方案，并调用 Claude 反复审查到无问题。
- Open product/scope/risk questions: 无阻断问题。本任务只产出治理方案，不直接修改 Guru runtime；后续若要落地代码 patch，再进入单独实现任务。

## Notes

- 审查闭环最终按用户更严格口径收敛：Claude Round 16 结论为 `review_result=clean`、`max_severity=none`，无 blocker、无 should-fix、无 nice-to-have。
