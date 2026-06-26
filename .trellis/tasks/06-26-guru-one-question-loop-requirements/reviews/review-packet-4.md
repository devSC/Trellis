# Compact Review Packet - Round 4


## .trellis/tasks/06-26-guru-one-question-loop-requirements/prd.md
```text
# 修复 Guru full 链 one-question loop 需求确认缺口

## Goal

修复 Guru full 链需求阶段绕过 Trellis brainstorm one-question loop 的流程缺口，使高风险产品 / 范围 / 合规 / 验收决策默认一次只问一个问题，并要求每次用户回答后再回写需求包或 `prd.md`。

## Background

当前 Trellis 原版 `trellis-brainstorm` 明确要求：

- 一次只问一个问题。
- 每次用户回答后再更新 `prd.md`。
- 仓库能回答的问题先查证，不向用户重复确认。

但 Guru full 链在需求阶段引入 `requirement-writing` / `requirement-review`，并将 `trellis-brainstorm` 定位为前置探索。现有 Guru workflow / requirement standard 允许将用户确认问题压缩为 `1~4` 个关键问题，`guru_gate.py requirements` 又只检查 `Brainstorm Evidence` 字段形状，导致 agent 可以批量写完需求包，再一次性列出多个 OQ，用户体验上表现为“没有经过 brainstorm 后逐项确认”。

本任务要让 Guru full 链继承 Trellis brainstorm 的 one-question loop，并让 Gate / review / continue 规则阻止“补字段”冒充真实确认。

## Scope

In scope:

- Guru workflow 模板中的 full 链需求阶段规则。
- Planning breadcrumb / workflow-state 中高频注入的 one-question loop 提示。
- `requirement-doc-standard` 对用户确认、`confirmation_status`、open questions 的约束。
- `requirement-review` 对 one-question evidence 的审核规则。
- `guru_gate.py requirements` 对 `Brainstorm Evidence` / 用户确认证据的最低结构检查。
- `trellis-continue` 在 planning 阶段遇到 high-risk OQ 时的恢复规则。
- 对应单测 / fixture / 文档验证。

Out of scope:

- 取消 Guru full 链 `requirement-writing` / `requirement-review`。
- 改变 overview/detail 双 clean review 与 detail confirm 机制。
- 强制所有低风险事实都问用户；仓库、代码、文档能回答的问题仍由 agent 自行取证。
- 对已经进入 `in_progress` 的历史任务做强制回滚。

## Definitions

- **one-question loop**: 每轮只向用户提出一个最高优先级的产品 / 范围 / 风险问题，附推荐答案和取舍说明；用户回答后，agent 先回写对应 artifact，再继续下一个问题。
- **high-risk open question**: 会改变上线范围、P0/P1 核心能力、验收口径、合规风险、对外 API / 数据合同、付费 / 权益 / 账号 / 内容安全策略的问题。
- **batch listing**: 用户要求“一次性列出问题清单”时，agent 可以列出多个问题，但这些问题未逐项回答前不得写成 confirmed。
- **confirmed decision evidence**: 能追踪到用户确认的证据。本任务确认的最低硬要求是 `user_quote` 或 `confirmed_ref` 二选一；完整 `Question loop log` 先作为推荐结构。

## Requirements

### REQ-001 planning breadcrumb 必须显式暴露 one-question loop

`planning` / `planning-inline` 的 workflow-state breadcrumb 必须直接写明：

- high-risk product / scope / risk decisions 默认使用 one-question loop。
- 每轮只问一个最高优先级问题。
- 每次用户回答后再更新 `prd.md` / requirements。
- Guru full 链中 `requirement-writing` 只能生成草稿，不能绕过用户逐项确认。

### REQ-002 Guru full 链必须区分草稿生成和用户确认

当任务为 `guru_chain=full`，`requirement-writing` 可以生成正式需求包草稿，但需要用户拍板的决策只能保持为：

- `confirmation_status=ai_drafted`
- `confirmation_status=evidence_ready`
- `open_questions` 中的待确认项

只有用户明确回答后，才能写成：

- `confirmation_status=user_confirmed`
- `confirmation_status=user_confirmed_with_edits`

### REQ-003 high-risk open questions 默认一次只问一个

当需求包或 `prd.md` 中存在多个 high-risk open questions，agent 下一步必须选择一个最高优先级问题询问用户。

每个问题必须包含：

- 决策点。
- 为什么影响需求 / 设计 / 上线。
- 推荐答案。
- 选择不同答案的取舍。

如果用户明确要求批量确认，agent 可以一次列出 2~4 个问题，但必须逐项记录用户回答；没有逐项回答的问题仍为 open。用户明确要求的判定仅限用户当前消息包含“批量确认”“一次性确认”“这几个都按推荐处理”等能覆盖多个问题的表述，不能由 agent 从“继续”“好”等短回复推断。

### REQ-004 Brainstorm Evidence 必须可追踪到用户确认

`prd.md` 的 `Brainstorm Evidence` 不得只作为字段补丁。对于 `Product decisions confirmed`，必须能追踪到用户确认来源。本次修复以 `user_quote` 或 `confirmed_ref` 二选一作为最低硬性结构；完整 `Question loop log` 作为推荐结构，不在本次 P1 中对所有 high-risk decisions 强制要求。

推荐格式：

```md
Brainstorm Evidence section:

- Skill loaded: trellis-brainstorm loaded during Phase 1.1.
- Repository evidence inspected: ...
- Domain/terminology triggers: ...
- Current code vs user intent conflicts: ...
- Product decisions confirmed:
  - DEC-001: <decision summary>
    - user_quote: "<用户原话>"
    - confirmed_at: <date/session/turn if available>
    - affected_refs: <requirement-main.md#... / prd.md#...>
- Open product/scope/risk questions:
  - OQ-001: <question>
    - risk: <why high risk>
    - next_action: ask user one question
- Question loop log:
  - QL-001:
    - question: <asked question>
    - recommended_answer: <recommendation>
    - user_answer: "<用户原话>"
    - updated_refs: <files/sections updated>
```

### REQ-005 requirements Gate 不允许字段补齐冒充 brainstorm 完成

`guru_gate.py requirements` 必须至少识别以下结构性风险：

- `Product decisions confirmed` 有正向结论，但缺 `user_quote` / `confirmed_at` / `confirmed_by` / `confirmed_ref` / `用户确认` 等确认引用。
- `Open product/scope/risk questions` 中有多个 OQ，但缺 `next_question` / `next_action` / `one-question loop` 指向。
- `confirmation_status=user_confirmed*` 附近缺用户确认依据。
- `Brainstorm Evidence` 只有摘要，没有用户确认引用。完整逐问记录缺失时不单独阻断，但应提示使用推荐的 `Question loop log` 格式补强。

结构化判定规则：

- `Product decisions confirmed` 为 positive 的定义：该字段不是 `none` / `无` / `没有` / `not triggered` 等 negative value，且包含至少一个 `DEC-` 条目或自然语言确认结论。
- positive `Product decisions confirmed` 必须在同一条决策或相邻缩进块中包含 `user_quote` 或 `confirmed_ref`。
- 多个 OQ 的定义：`Open product/scope/risk questions` 中出现两个或以上 `OQ-` 条目。
- 多个 OQ 必须明确一个 `next_question` / `next_action`，并声明其他 OQ 保持 open。

### REQ-006 `继续` 不得越过 one-question planning boundary

当用户在 planning 阶段输入 `继续`，且当前任务存在 high-risk open questions 或 P0/P1 `confirmation_status=ai_drafted` 时：

- 可以继续做证据收集、结构整理、review。
- 不得批量替用户完成确认。
- 不得把 `confirmation_status` 从 `ai_drafted` / `evidence_ready` 改为 `user_confirmed*`。
- 不得把 high-risk OQ 从 open 移除，除非本轮用户回答包含该问题的确认。
- 下一步必须问一个最高优先级问题。
- 不得进入概要设计或 `task.py start`。

## Behavior Specs

### BHV-001 Planning Breadcrumb Injection

Given 当前任务状态为 `planning`
When Trellis hook 注入 workflow-state breadcrumb
Then breadcrumb 必须包含 one-question loop、Guru full 链草稿限制、用户回答后再回写 artifact 的规则。

### BHV-002 Requirement Drafting

Given 任务为 `guru_chain=full`
When agent 使用 `requirement-writing` 生成 requirements package
Then high-risk 决策必须保留为 `ai_drafted` / `evidence_ready` / `open_questions`，直到用户明确确认。

### BHV-003 Single Next Question

Given 存在多个 high-risk OQ
When agent 继续 planning
Then agent 只能问一个最高优先级问题，并提供推荐答案与取舍。

### BHV-004 Confirmed Decision Evidence

Given `Brainstorm Evidence` 包含 `Product decisions confirmed`
When requirements Gate 或 requirement-review 检查该 section
Then 每个 confirmed decision 必须有用户确认引用，否则不得视为完成。

### BHV-005 Continue Boundary

Given 用户输入 `继续`
When 当前 planning task 仍有 high-risk OQ
Then agent 停在 one-question loop，不能批量推进到概要 / 详细 / start。

### BHV-006 Batch Confirmation Exception

Given 用户当前消息明确要求批量确认多个问题
When agent 一次列出 2~4 个问题
Then 每个被标记 confirmed 的问题必须有独立 `user_quote` 或 `confirmed_ref`；未被用户逐项覆盖的问题必须保留为 open，并指明唯一 `next_question`。

### BHV-007 Evidence Work During Continue

Given 用户输入 `继续` 且仍存在 high-risk OQ
When agent 做证据收集、结构整理或 review
Then agent 可以补充 evidence / risk / source refs，但不能改变 `confirmation_status` 为 `user_confirmed*`，也不能删除 high-risk OQ，除非本轮用户明确回答该问题。

## Failure Paths

- FP-001: If an agent attempts to mark a high-risk decision `user_confirmed*` without `user_quote` or `confirmed_ref`, `guru_gate.py requirements` must fail and point back to one-question loop recovery.
- FP-002: If multiple OQ entries exist without a single `next_question` / `next_action`, `guru_gate.py requirements` must fail and require the next one-question loop prompt.
- FP-003: If `continue` is invoked while high-risk OQ remains, the workflow must allow evidence enrichment but block overview/detail/start and block confirmation-status promotion.
- FP-004: If overlay and bundled templates drift after Guru overlay edits, validation must fail before reporting the task ready.

## Acceptance Criteria

- [ ] Guru workflow 中 `1~4 个` 的默认口径被调整为“默认 1 个，用户显式要求时才允许批量列出 2~4 个”。
- [ ] Planning breadcrumb 明确写入 one-question loop，高频注入上下文可见。
- [ ] `requirement-doc-standard` 明确 `requirement-writing` 只能草拟，不能替用户拍板。
- [ ] `requirement-review` 能把缺少 one-question evidence 的 P0/P1 决策判为 blocker 或 process defect。
- [ ] `guru_gate.py requirements` 对 `Product decisions confirmed`、`Open product/scope/risk questions`、`user_confirmed*` 做最低结构检查。
- [ ] `trellis-continue` 在 planning + high-risk OQ 时恢复到 one-question loop。
- [ ] 新增或更新测试覆盖缺失确认证据、多个 OQ 无 next question、`user_confirmed` 无确认引用、用户显式批量确认等场景。
- [ ] 现有 overview/detail clean review 与 detail confirm Gate 回归测试通过；若没有单独测试，至少运行 Guru gate 现有测试套件并确认 requirements 变更没有破坏 overview/detail/detail-confirm 相关 fixture。
- [ ] 不触碰无关脏改。

## Brainstorm Evidence

- Skill loaded: trellis-brainstorm requirement exploration loaded for this task; current artifact is the Phase 1.1 PRD draft.
- Repository evidence inspected: `.agents/skills/trellis-brainstorm/SKILL.md`, `.trellis/workflow.md`, `packages/cli/src/templates/guru/workflows/guru-client.md`, `packages/cli/src/templates/guru/workflows/guru-go.md`, `guru-template/overlay/verify/guru_gate.py`, `guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`, and `guru-template/overlay/agents-skills/requirement-review/SKILL.md`.
- Domain/terminology triggers: Guru full chain uses both `trellis-brainstorm` and `requirement-writing`; the term "confirm" is overloaded between chat confirmation, `confirmation_status`, and `guru_gate.py confirm`.
- Current code vs user intent conflicts: Trellis brainstorm requires one question per message, but Guru full-chain workflow and requirement standard allow compressed `1~4` confirmation questions; `guru_gate.py` checks evidence field shape rather than the real question loop.
- Product decisions confirmed: DEC-001 user_quote="确"; DEC-002 user_quote="好"; confirmed_ref=prd.md Brainstorm Evidence DEC-001/DEC-002.
  Confirmed decision detail:
  - DEC-001: Create a Trellis planning task for the Guru full-chain one-question loop fix.
    - user_quote: "确"
    - confirmed_at: 2026-06-26
    - affected_refs: `.trellis/tasks/06-26-guru-one-question-loop-requirements/`
  - DEC-002: For this P1 patch, require `user_quote` / `confirmed_ref` as the hard minimum and keep full `Question loop log` recommended rather than mandatory.
    - user_quote: "好"
    - confirmed_at: 2026-06-26
    - affected_refs: `REQ-004`, `REQ-005`, `design.md`
- Open product/scope/risk questions: none -- because the only planning decision needed before implementation scope drafting, OQ-001, is confirmed as DEC-002.
- Question loop log:
  - QL-001:
    - question: Should `Question loop log` be mandatory for all high-risk decisions, or should `user_quote` / `confirmed_ref` be the hard minimum for this patch?
    - recommended_answer: Use `user_quote` / `confirmed_ref` as the hard minimum in P1; keep full `Question loop log` recommended.
    - user_answer: "好"
    - updated_refs: `prd.md`, `design.md`, `implement.md`

## Notes

- This task is planning-only until PRD / design / implement artifacts are reviewed.
- Existing unrelated dirty files must remain untouched.

```


## .trellis/tasks/06-26-guru-one-question-loop-requirements/design.md
```text
# 调整方案：Guru full 链 one-question loop 恢复

## Summary

当前缺口横跨三层：

1. **Workflow / breadcrumb**: 原版 Trellis step detail 有 one-question loop，但 per-turn breadcrumb 太弱，Guru full 链模板也没有把该规则作为高频约束。
2. **Requirement writing / review**: Guru full 链把正式需求写作交给 `requirement-writing`，并允许 `1~4` 个确认问题，导致批量草稿容易被误当成确认流程。
3. **Gate enforcement**: `guru_gate.py requirements` 只检查 `Brainstorm Evidence` 字段是否存在，不能识别“字段补齐但没有逐问确认”的情况。

调整方案是在不取消 Guru full 链的前提下，把 one-question loop 明确下沉到 workflow、standard、review、gate、continue 五个入口。

## Affected Files

Workflow / templates:

- `.trellis/workflow.md`
- `packages/cli/src/templates/trellis/workflow.md`
- `packages/cli/src/templates/guru/workflows/guru-client.md`
- `packages/cli/src/templates/guru/workflows/guru-go.md`
- 其他 `packages/cli/src/templates/guru/workflows/guru-*.md` 如存在同类 `1~4` 文案

Skills / standards:

- `.agents/skills/trellis-continue/SKILL.md`
- `packages/cli/src/templates/codex/skills/continue/SKILL.md` 或 common continue 模板
- `guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`
- `packages/cli/src/templates/guru/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`
- `guru-template/overlay/agents-skills/requirement-review/SKILL.md`
- `packages/cli/src/templates/guru/overlay/agents-skills/requirement-review/SKILL.md`

Gate / tests:

- `guru-template/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/tests/`
- `packages/cli` tests that snapshot or validate generated Guru templates

## Design

### 1. Breadcrumb Hardening

Add one-question loop text directly to planning breadcrumb blocks. This matters because hook-injected workflow-state is the most likely instruction the agent sees on every turn.

Target behavior:

```md
High-risk product/scope/risk decisions use one-question loop: ask exactly one highest-value question, include recommended answer + trade-off, wait for user answer, then update prd/requirements before asking the next.
For Guru full chain, requirement-writing may draft evidence, but it must not mark decisions user_confirmed or collapse multiple high-risk OQs into one confirmation unless the user explicitly asks for batch confirmation.
```

### 2. Guru Full Chain Rule Change

Replace the `1~4` default with a strict default:

- Default: one highest-priority question per message.
- Batch listing: allowed only when user asks for a complete list.
- Batch confirmation: allowed only when user explicitly confirms each item or gives an unambiguous answer covering all listed items.
- Unanswered items remain `open_questions`.

### 3. Requirement Standard Update

Clarify that `requirement-writing` may produce:

- `ai_drafted`
- `evidence_ready`

It may not produce `user_confirmed*` unless the artifact includes confirmed evidence. The confirmed P1 minimum accepted evidence is exactly one of:

- `user_quote`, or
- `confirmed_ref`.

### 4. Requirement Review Update

`requirement-review` should classify missing one-question evidence as:

- `REQ_BLOCKER` when the missing decision affects P0/P1, scope, acceptance, compliance, API/data contract, payment, account, or safety.
- `PROCESS_DEFECT` when `Brainstorm Evidence` has fields but no traceable question loop.

Full `Question loop log` remains recommended structure for clarity and future hardening, but it is not mandatory for all high-risk decisions in this patch.

### 5. Gate Structure Checks

Enhance `_brainstorm_evidence_problems` and requirements checks:

- Positive `Product decisions confirmed` means the value is not a negative value (`none`, `无`, `没有`, `not triggered`, etc.) and contains at least one `DEC-` item or natural-language confirmed decision.
- Positive `Product decisions confirmed` requires `user_quote` or `confirmed_ref` in the same decision item or adjacent indented block.
- Multiple OQ means two or more `OQ-` entries in `Open product/scope/risk questions`.
- Multiple OQ requires a single `next_question` / `next_action`; all other OQ entries must remain open.
- If `prd` contains `confirmation_status=user_confirmed*`, require a nearby `user_quote` or `confirmed_ref`.
- If a full `Question loop log` is absent but minimum confirmation hints exist, pass the structural gate and leave review-level guidance to prefer the richer format.

This remains a structural gate. Semantic judgment stays in `requirement-review`.

### 6. Continue Boundary

Update `trellis-continue` guidance:

- `continue` can do reversible evidence work.
- If high-risk OQ or `ai_drafted` P0/P1 remains, next step is one question.
- It must not move to overview/detail/start.

## Compatibility

- Existing tasks can keep legacy evidence until they re-enter requirements planning.
- For old tasks lacking question-loop details, Gate should provide recovery guidance rather than silently treating the task as confirmed.
- `Question loop log` starts recommended, not globally mandatory. `user_quote` / `confirmed_ref` is the hard minimum for this P1.

## Risks

- Too strict Gate parsing could block legacy tasks with valid human confirmation written in older formats.
- Too loose parsing will preserve the current loophole.
- The implementation must keep local `.trellis/workflow.md` and generated templates aligned; otherwise this worktree passes while new projects still regress.

## Recommended First Decision

OQ-001 is confirmed: do not make `Question loop log` mandatory in this P1. Make `user_quote` / `confirmed_ref` the minimum hard requirement, and introduce `Question loop log` as recommended structure. This reduces migration friction while still preventing field-only Brainstorm Evidence.

## Claude Adversarial Review Fixes

Review 3 produced `review_result=findings route_class=PROCESS_DEFECT max_severity=high`. Repairs made in this plan:

- F-001: aligned PRD and design on the hard minimum: `user_quote` or `confirmed_ref` only.
- F-002: implementation plan now includes `sync:guru` / template sync verification.
- F-003: PRD now has BHV-006 for batch confirmation exception.
- F-004: gate design defines positive decisions and multiple OQ operationally.
- F-005: PRD now forbids `confirmation_status=user_confirmed*` changes or high-risk OQ removal during `continue` evidence work without current-turn user confirmation.
- F-006: acceptance now requires Guru gate regression coverage for overview/detail/detail-confirm.
- F-007: implementation plan treats unavailable gate verification as blocker.

```


## .trellis/tasks/06-26-guru-one-question-loop-requirements/implement.md
```text
# Implementation Plan

## Preconditions

- Stay in `planning` until this PRD / design / implementation plan is reviewed.
- Do not edit unrelated dirty files.
- Before modifying Python or TypeScript symbols, run GitNexus impact analysis per project instruction.
- Before committing, run GitNexus `detect_changes()`.
- `guru_gate.py` must be runnable from this worktree before gate changes are considered verifiable. If neither `.trellis/scripts/guru/guru_gate.py` nor `guru-template/overlay/verify/guru_gate.py` can run the relevant tests, stop as blocked instead of documenting absence as acceptable.

## Steps

1. Update workflow wording.
   - Edit `.trellis/workflow.md` planning breadcrumb and Phase 1.1 detail.
   - Edit `packages/cli/src/templates/trellis/workflow.md` to keep generated output aligned.

2. Update Guru workflow templates.
   - Edit `packages/cli/src/templates/guru/workflows/guru-client.md`.
   - Edit `packages/cli/src/templates/guru/workflows/guru-go.md`.
   - Search all Guru workflow templates for `1~4` / `一次问用户` / `trellis-brainstorm 仅作前置探索` and align wording.

3. Update requirement standard and review skill.
   - Edit `guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`.
   - Edit matching `packages/cli/src/templates/guru/overlay/...` file.
   - Edit `guru-template/overlay/agents-skills/requirement-review/SKILL.md`.
   - Edit matching template file.

4. Update continue recovery guidance.
   - Edit `.agents/skills/trellis-continue/SKILL.md`.
   - Edit generated template source for Codex/common continue skill.
   - Ensure planning + high-risk OQ routes to one-question loop.

5. Update Guru gate.
   - Run GitNexus impact analysis for functions to edit in `guru_gate.py`.
   - Enhance Brainstorm Evidence parsing and confirmation hint checks.
   - Mirror changes in template and overlay copies.

6. Sync Guru overlay and bundled templates.
   - Run the project-approved `sync:guru` flow if available.
   - If no `sync:guru` command exists in this worktree, manually verify every edited `guru-template/overlay/...` file has the matching `packages/cli/src/templates/guru/overlay/...` update, and document the command absence.
   - Treat unsynced overlay/template drift as blocking.

7. Add tests.
   - Missing `Brainstorm Evidence` still fails.
   - Positive `Product decisions confirmed` without confirmation reference fails.
   - Multiple OQ entries without single next action fails.
   - `confirmation_status=user_confirmed*` without confirmation hint fails.
   - Explicit batch confirmation fixture passes only when each confirmed decision has evidence.
   - Missing full `Question loop log` does not fail when `user_quote` / `confirmed_ref` is present.
   - Existing overview/detail/detail-confirm Guru gate fixtures still pass, proving requirements changes did not regress later Gate behavior.

8. Validate.
   - Run targeted Python gate tests.
   - Run relevant CLI/template tests.
   - Run `python3 ./.trellis/scripts/task.py validate 06-26-guru-one-question-loop-requirements`.
   - Run Guru requirements gate through the available path (`.trellis/scripts/guru/guru_gate.py` or `guru-template/overlay/verify/guru_gate.py`); unavailable gate execution is blocking, not skippable.
   - Run `git diff --check`.

9. Final review boundary.
   - Present changed files and validation results.
   - Do not start implementation task or commit until user confirms.

## Confirmed Decisions

1. DEC-002: `Question loop log` is recommended, not mandatory, for this P1 patch. The hard minimum is `user_quote` / `confirmed_ref`.
   - User confirmation: "好" on 2026-06-26.

```


## .trellis/tasks/06-26-guru-one-question-loop-requirements/task.json
```text
{
  "id": "guru-one-question-loop-requirements",
  "name": "guru-one-question-loop-requirements",
  "title": "修复 Guru full 链 one-question loop 需求确认缺口",
  "description": "修复 Guru full 链需求阶段绕过 Trellis brainstorm one-question loop 的流程缺口：明确 high-risk open questions 默认一次只问一个，requirement-writing 仅可生成草稿，Brainstorm Evidence 与 requirements Gate 需能追踪用户逐项确认，trellis-continue 不得越过业务拍板边界。",
  "status": "planning",
  "dev_type": null,
  "scope": null,
  "package": null,
  "priority": "P1",
  "creator": "devSC",
  "assignee": "devSC",
  "createdAt": "2026-06-26",
  "completedAt": null,
  "branch": null,
  "base_branch": "codex/guru-0.6.0-ga-worktree",
  "worktree_path": null,
  "commit": null,
  "pr_url": null,
  "subtasks": [],
  "children": [],
  "parent": null,
  "relatedFiles": [
    ".trellis/tasks/06-26-guru-one-question-loop-requirements/prd.md",
    ".trellis/tasks/06-26-guru-one-question-loop-requirements/design.md",
    ".trellis/tasks/06-26-guru-one-question-loop-requirements/implement.md",
    ".agents/skills/trellis-brainstorm/SKILL.md",
    ".agents/skills/trellis-continue/SKILL.md",
    ".trellis/workflow.md",
    "packages/cli/src/templates/trellis/workflow.md",
    "packages/cli/src/templates/guru/workflows/guru-client.md",
    "packages/cli/src/templates/guru/workflows/guru-go.md",
    "guru-template/overlay/verify/guru_gate.py",
    "guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md",
    "guru-template/overlay/agents-skills/requirement-review/SKILL.md"
  ],
  "notes": "Planning artifacts capture the requirement and adjustment plan. OQ-001 confirmed on 2026-06-26: user_quote/confirmed_ref is the hard minimum; Question loop log is recommended, not mandatory. Claude review 3 found PROCESS_DEFECT/high issues; PRD/design/implement were repaired to address F-001..F-007. Implementation is not started.",
  "meta": {}
}

```


## .trellis/tasks/06-26-guru-one-question-loop-requirements/reviews/claude-review-fix-log.md
```text
# Claude Requirements Review Fix Log

## Review 1

`claude-requirements-review-1.md` is invalid evidence. The prompt passed `$(cat ...)` literally, so Claude did not receive the packet.

## Review 2

`claude-requirements-review-2.md` did not complete in useful time with the large packet and was interrupted.

## Review 3

Valid review evidence:

- File: `reviews/claude-requirements-review-3.md`
- Result: `review_result=findings route_class=PROCESS_DEFECT max_severity=high`

Findings and repairs:

- F-001: PRD and design disagreed on accepted confirmation evidence. Fixed by standardizing the hard minimum to `user_quote` or `confirmed_ref`.
- F-002: Implementation plan missed `sync:guru`. Fixed by adding a sync / overlay-template drift verification step.
- F-003: Batch exception lacked behavior specs. Fixed by adding BHV-006.
- F-004: Gate "positive" semantics were undefined. Fixed by defining positive decisions and multiple OQ structurally.
- F-005: `continue` evidence work could still mutate confirmation state. Fixed by forbidding `confirmation_status=user_confirmed*` changes or high-risk OQ removal without current-turn user confirmation.
- F-006: Existing Gate non-regression was not testable. Fixed by requiring Guru gate regression coverage for overview/detail/detail-confirm fixtures.
- F-007: Guru gate validation was skippable. Fixed by making unavailable gate execution blocking.

```


## Current Verification

- `python3 guru-template/overlay/verify/guru_gate.py requirements .trellis/tasks/06-26-guru-one-question-loop-requirements` passes.
- `python3 ./.trellis/scripts/task.py validate 06-26-guru-one-question-loop-requirements` passes.
- `git diff --check -- .trellis/tasks/06-26-guru-one-question-loop-requirements` passes.

## Repository Evidence Summary

- Trellis brainstorm requires one question per message.
- Current Guru full-chain templates allow 1~4 confirmation questions and route formal requirements through requirement-writing/review.
- Current guru_gate.py checks Brainstorm Evidence structurally, so this task proposes enhanced positive decision / OQ parsing.
- Claude review 3 found F-001..F-007; the current packet includes repairs.
