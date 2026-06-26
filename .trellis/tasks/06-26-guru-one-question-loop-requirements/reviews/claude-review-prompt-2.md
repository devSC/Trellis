Review the following packet for the Trellis task `06-26-guru-one-question-loop-requirements`.

Goal: adversarially review until no requirement issues remain. Focus on whether the task fully specifies the fix for the Guru full-chain one-question-loop gap. Treat vague, untestable, internally inconsistent, or under-scoped requirements as blockers. Do not suggest implementation code; review the requirement and adjustment plan quality.

# Review Packet: guru-one-question-loop-requirements


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
- **confirmed decision evidence**: 能追踪到用户确认的证据，如用户原话、确认时间、确认引用、会话 turn 或显式 `confirmed_ref`。本任务确认的最低硬要求是 `user_quote` / `confirmed_ref`；完整 `Question loop log` 先作为推荐结构。

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

如果用户明确要求批量确认，agent 可以一次列出 2~4 个问题，但必须逐项记录用户回答；没有逐项回答的问题仍为 open。

### REQ-004 Brainstorm Evidence 必须可追踪到用户确认

`prd.md` 的 `Brainstorm Evidence` 不得只作为字段补丁。对于 `Product decisions confirmed`，必须能追踪到用户确认来源。本次修复以 `user_quote` / `confirmed_ref` 作为最低硬性结构；完整 `Question loop log` 作为推荐结构，不在本次 P1 中对所有 high-risk decisions 强制要求。

推荐格式：

```md
## Brainstorm Evidence

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

### REQ-006 `继续` 不得越过 one-question planning boundary

当用户在 planning 阶段输入 `继续`，且当前任务存在 high-risk open questions 或 P0/P1 `confirmation_status=ai_drafted` 时：

- 可以继续做证据收集、结构整理、review。
- 不得批量替用户完成确认。
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

## Acceptance Criteria

- [ ] Guru workflow 中 `1~4 个` 的默认口径被调整为“默认 1 个，用户显式要求时才允许批量列出 2~4 个”。
- [ ] Planning breadcrumb 明确写入 one-question loop，高频注入上下文可见。
- [ ] `requirement-doc-standard` 明确 `requirement-writing` 只能草拟，不能替用户拍板。
- [ ] `requirement-review` 能把缺少 one-question evidence 的 P0/P1 决策判为 blocker 或 process defect。
- [ ] `guru_gate.py requirements` 对 `Product decisions confirmed`、`Open product/scope/risk questions`、`user_confirmed*` 做最低结构检查。
- [ ] `trellis-continue` 在 planning + high-risk OQ 时恢复到 one-question loop。
- [ ] 新增或更新测试覆盖缺失确认证据、多个 OQ 无 next question、`user_confirmed` 无确认引用、用户显式批量确认等场景。
- [ ] 不影响既有 overview/detail clean review 与 detail confirm Gate。
- [ ] 不触碰无关脏改。

## Brainstorm Evidence

- Skill loaded: trellis-brainstorm requirement exploration loaded for this task; current artifact is the Phase 1.1 PRD draft.
- Repository evidence inspected: `.agents/skills/trellis-brainstorm/SKILL.md`, `.trellis/workflow.md`, `packages/cli/src/templates/guru/workflows/guru-client.md`, `packages/cli/src/templates/guru/workflows/guru-go.md`, `guru-template/overlay/verify/guru_gate.py`, `guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`, and `guru-template/overlay/agents-skills/requirement-review/SKILL.md`.
- Domain/terminology triggers: Guru full chain uses both `trellis-brainstorm` and `requirement-writing`; the term "confirm" is overloaded between chat confirmation, `confirmation_status`, and `guru_gate.py confirm`.
- Current code vs user intent conflicts: Trellis brainstorm requires one question per message, but Guru full-chain workflow and requirement standard allow compressed `1~4` confirmation questions; `guru_gate.py` checks evidence field shape rather than the real question loop.
- Product decisions confirmed:
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

It may not produce `user_confirmed*` unless the artifact includes confirmed evidence. The confirmed P1 minimum accepted evidence is:

- `user_quote`, or
- `confirmed_ref`, or
- `confirmed_by` + `confirmed_at` + exact decision text.

### 4. Requirement Review Update

`requirement-review` should classify missing one-question evidence as:

- `REQ_BLOCKER` when the missing decision affects P0/P1, scope, acceptance, compliance, API/data contract, payment, account, or safety.
- `PROCESS_DEFECT` when `Brainstorm Evidence` has fields but no traceable question loop.

Full `Question loop log` remains recommended structure for clarity and future hardening, but it is not mandatory for all high-risk decisions in this patch.

### 5. Gate Structure Checks

Enhance `_brainstorm_evidence_problems` and requirements checks:

- If `Product decisions confirmed` is positive, require confirmation hints.
- If `Open product/scope/risk questions` contains multiple OQ entries, require `next_question` / `next_action` / `one-question loop`.
- If `prd` contains `confirmation_status=user_confirmed*`, require a nearby confirmation hint.
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

```


## .trellis/tasks/06-26-guru-one-question-loop-requirements/implement.md

```text
# Implementation Plan

## Preconditions

- Stay in `planning` until this PRD / design / implementation plan is reviewed.
- Do not edit unrelated dirty files.
- Before modifying Python or TypeScript symbols, run GitNexus impact analysis per project instruction.
- Before committing, run GitNexus `detect_changes()`.

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

6. Add tests.
   - Missing `Brainstorm Evidence` still fails.
   - Positive `Product decisions confirmed` without confirmation reference fails.
   - Multiple OQ entries without single next action fails.
   - `confirmation_status=user_confirmed*` without confirmation hint fails.
   - Explicit batch confirmation fixture passes only when each confirmed decision has evidence.
   - Missing full `Question loop log` does not fail when `user_quote` / `confirmed_ref` is present.

7. Validate.
   - Run targeted Python gate tests.
   - Run relevant CLI/template tests.
   - Run `python3 ./.trellis/scripts/task.py validate 06-26-guru-one-question-loop-requirements`.
   - Run `python3 ./.trellis/scripts/guru/guru_gate.py requirements .trellis/tasks/06-26-guru-one-question-loop-requirements` if Guru gate is available in this worktree; otherwise document absence.
   - Run `git diff --check`.

8. Final review boundary.
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
  "notes": "Planning artifacts capture the requirement and adjustment plan. OQ-001 confirmed on 2026-06-26: user_quote/confirmed_ref is the hard minimum; Question loop log is recommended, not mandatory. Implementation is not started.",
  "meta": {}
}

```


## .agents/skills/trellis-brainstorm/SKILL.md

```text
---
name: trellis-brainstorm
description: "Guides collaborative requirements discovery before implementation. Creates task directory, seeds PRD, asks high-value questions one at a time, researches technical choices, and converges on MVP scope. Use when requirements are unclear, there are multiple valid approaches, or the user describes a new feature or complex task."
---

# Trellis Brainstorm

## Non-Negotiable Interview Contract

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

## Non-Negotiable Evidence Rule

If a question can be answered by exploring the codebase, explore the codebase instead.

This is mandatory. Before asking the user a question, first check whether the answer is already available in code, tests, configs, docs, existing specs, or task history.

Do not ask the user to confirm facts that the repository can answer. Ask only for product intent, preference, scope, risk tolerance, or decisions that remain ambiguous after inspection.

## Domain Grill Subroutine

Run this subroutine before asking requirement questions when evidence shows any of the following:

- new domain terms or renamed concepts
- term conflicts with `CONTEXT.md`, `CONTEXT-MAP.md`, docs, ADRs, specs, or existing code
- overloaded or ambiguous wording
- unclear lifecycle, state, ownership, or boundary rules
- cross-context ownership ambiguity
- mismatch between current code facts and the user's requested behavior

When triggered:

1. Build a short context map from repository evidence first: code, tests, configs, docs, `.trellis/spec/`, `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`, and relevant task history.
2. Point out term conflicts directly instead of asking the user to rediscover them.
3. Recommend canonical terms for overloaded language and explain the trade-off.
4. Pressure-test boundaries with concrete scenarios, especially state transitions, ownership, failure paths, and cross-layer responsibilities.
5. When current code behavior conflicts with user intent, ask a "current code vs user intent" product decision question with a recommended answer.
6. Write confirmed long-term glossary or domain-boundary decisions to `CONTEXT.md` only when they are durable. Keep temporary task decisions in `prd.md`.
7. Propose an ADR only when the decision is hard-to-reverse, surprising-without-context, and a real trade-off.

Do not turn Domain Grill into a separate post-draft Gate. It is part of requirement discovery and feeds the requirements confirmation Gate.

---

Use this skill during Phase 1 planning to turn the user's request into clear requirements and planning artifacts.

## Preconditions

Use this skill only after task-creation consent has been given and the user is ready to enter Trellis planning.

If no task exists yet, create one:

```bash
TASK_DIR=$(python3 ./.trellis/scripts/task.py create "<short task title>" --slug <slug>)
```

Use a concise title from the user's request. Use a slug without a date prefix. `task.py create` adds the `MM-DD-` directory prefix automatically.

`task.py create` creates the default `prd.md`. Update that file with the current understanding before asking follow-up questions.

## Planning Flow

1. Capture the user's request and initial known facts in `prd.md`.
2. Inspect available evidence before asking questions:
   - code, tests, fixtures, and configs
   - README files, docs, existing specs, domain notes, `CONTEXT.md`, `CONTEXT-MAP.md`, and `docs/adr/`
   - related Trellis tasks, research files, and session history when present
3. Separate what you found into:
   - confirmed facts
   - domain terms, ownership boundaries, and current code vs user intent conflicts
   - product intent still needed from the user
   - scope or risk decisions still needed from the user
   - likely out-of-scope items
4. Ask the single highest-value remaining question.
5. Include your recommended answer with the question.
6. After each user answer, update `prd.md` before continuing.
7. For complex tasks, create or update `design.md` and `implement.md` before implementation starts.

Do not invent a project-specific product/spec hierarchy. If the repository already has product, domain, or spec docs, use them. If it does not, proceed with the evidence that exists.

## Question Rules

Ask only one question per message.

Each question must include:

- the decision needed
- why the answer matters
- your recommended answer
- the trade-off if the user chooses differently

Do not ask process questions such as whether to search, inspect files, or continue brainstorming. Do the evidence work directly. Ask the user only when the remaining issue is a product decision, preference, scope boundary, or risk tolerance choice.

## Artifact Rules

`prd.md` records requirements and acceptance:

- goal and user value
- confirmed facts
- requirements
- acceptance criteria
- out of scope
- open questions that still block planning

`design.md` records technical design for complex tasks:

- architecture and boundaries
- data flow and contracts
- compatibility and migration notes
- important trade-offs
- operational or rollback considerations

`implement.md` records execution planning for complex tasks:

- ordered implementation checklist
- validation commands
- risky files or rollback points
- follow-up checks before `task.py start`

Lightweight tasks may have only `prd.md`. Complex tasks must have `prd.md`, `design.md`, and `implement.md` before `task.py start`.

`implement.md` is not a replacement for `implement.jsonl`. Use JSONL files only for manifest-style spec and research references when the task needs them.

## Quality Bar

Before declaring planning ready:

- `prd.md` contains testable acceptance criteria.
- Repository-answerable questions have already been answered through inspection.
- Remaining open questions are genuinely about user intent or scope.
- Complex tasks have `design.md` and `implement.md`.
- The user has reviewed the final planning artifacts or explicitly approved proceeding.

Do not start implementation until the user approves or asks for implementation.

```


## .agents/skills/trellis-continue/SKILL.md

```text
---
name: trellis-continue
description: "Resume work on the current task. Loads the workflow Phase Index, figures out which phase/step to pick up at, then pulls the step-level detail via get_context.py --mode phase. Use when coming back to an in-progress task and you need to know what to do next."
---

# Continue Current Task

Resume work on the current task — pick up at the right phase/step in `.trellis/workflow.md`.

---

## Step 1: Load Current Context

```bash
python3 ./.trellis/scripts/get_context.py
```

Confirms: current task, git state, recent commits.

## Step 2: Load the Phase Index

```bash
python3 ./.trellis/scripts/get_context.py --mode phase
```

Shows the Phase Index (Plan / Execute / Finish) with routing + skill mapping.

## Step 3: Decide Where You Are

`get_context.py` shows the active task's `status` field. Route by `status` + artifact presence. This command replaces the user needing to remember the Trellis flow; it does not itself approve implementation.

- `status=planning` + no `prd.md` → **1.1** (load `trellis-brainstorm`)
- `status=planning` + `prd.md` only → decide whether the task is lightweight or complex. Lightweight can move to **1.4** review; complex returns to **1.1** to add `design.md` + `implement.md`.
- `status=planning` + complex artifacts complete + sub-agent jsonl not curated (only the seed `_example` row) → **1.3**
- `status=planning` + required artifacts complete + required jsonl curated or inline mode → **1.4** (ask for start review; only run `task.py start` after user confirms)
- `status=in_progress` + implementation not started → **2.1**
- `status=in_progress` + implementation done, not yet checked → **2.2**
- `status=in_progress` + check passed → **3.1**
- `status=completed` (rare; usually archived immediately) → archive flow

Phase rules (full detail in `.trellis/workflow.md`):

1. Run steps **in order** within a phase — `[required]` steps must not be skipped
2. `[once]` steps are already done if the required output exists. `prd.md` alone can be enough only for lightweight tasks; complex tasks also need `design.md` and `implement.md`.
3. You may go back to an earlier phase if discoveries require it

## Step 4: Load the Specific Step

Once you know which step to resume at:

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <X.X> --platform codex
```

Follow the loaded instructions. After each `[required]` step completes, move to the next.

---

## Reference

Full workflow and detailed phase steps live in `.trellis/workflow.md`. This command is only an entry point — the canonical guidance is there.

```


## .trellis/workflow.md

```text

# lines 180-210

[/workflow-state:no_task]

### Phase 1: Plan
- 1.0 Create task `[required · once]` (only after task-creation consent)
- 1.1 Requirement exploration `[required · repeatable]` (`prd.md`; complex tasks also need `design.md` + `implement.md`)
- 1.2 Research `[optional · repeatable]`
- 1.3 Configure context `[conditional · once]` — Claude Code, Cursor, OpenCode, Codex, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi
- 1.4 Activate task `[required · once]` (review gate, then `task.py start`; status → in_progress)
- 1.5 Completion criteria

<!-- Per-turn breadcrumb: shown throughout Phase 1 (status='planning') -->

[workflow-state:planning]
Load `trellis-brainstorm`; stay in planning.
Lightweight: `prd.md` can be enough. Complex: finish `prd.md`, `design.md`, and `implement.md`; ask for review before `task.py start`.
Multi-deliverable scope: consider a parent task plus independently verifiable child tasks; dependencies must be written in child artifacts, not implied by tree position.
Sub-agent mode: curate `implement.jsonl` and `check.jsonl` as spec/research manifests before start.
[/workflow-state:planning]

<!-- Per-turn breadcrumb: shown throughout Phase 1 when codex.dispatch_mode=inline.
     Codex-only opt-in alternate to [workflow-state:planning]. The main agent
     edits code directly in Phase 2, so jsonl curation is skipped —
     the inline workflow loads `trellis-before-dev` instead of injecting JSONL
     into a sub-agent. -->

[workflow-state:planning-inline]
Load `trellis-brainstorm`; stay in planning.
Lightweight: `prd.md` can be enough. Complex: finish `prd.md`, `design.md`, and `implement.md`; ask for review before `task.py start`.
Multi-deliverable scope: consider a parent task plus independently verifiable child tasks; dependencies must be written in child artifacts, not implied by tree position.
Inline mode: skip jsonl curation; Phase 2 reads artifacts/specs via `trellis-before-dev`.
[/workflow-state:planning-inline]

# lines 326-345


Skip when `python3 ./.trellis/scripts/task.py current --source` already points to a task.

#### 1.1 Requirement exploration `[required · repeatable]`

Load the `trellis-brainstorm` skill and explore requirements interactively with the user per the skill's guidance.

The brainstorm skill will guide you to:
- Ask one question at a time
- Prefer researching over asking the user
- Prefer offering options over open-ended questions
- Update `prd.md` immediately after each user answer
- Split large scopes into a parent task plus child tasks when the deliverables can be verified independently
- Keep `prd.md` focused on requirements and acceptance criteria
- For complex tasks, produce `design.md` and `implement.md` before implementation starts

When considering a parent/child split:
- Use a parent task when one request contains several independently verifiable deliverables.
- Parent tasks own source requirements, child-task mapping, cross-child acceptance criteria, and final integration review.
- Child tasks own actual deliverables that can be planned, implemented, checked, and archived independently.

# lines 560-635


## Phase 3: Finish

Goal: ensure code quality, capture lessons, record the work.

#### 3.1 Quality verification `[required · repeatable]`

Load the `trellis-check` skill and do a final verification:
- Spec compliance
- lint / type-check / tests
- Cross-layer consistency (when changes span layers)

If issues are found → fix → re-check, until green.

#### 3.2 Debug retrospective `[on demand]`

If this task involved repeated debugging (the same issue was fixed multiple times), load the `trellis-break-loop` skill to:
- Classify the root cause
- Explain why earlier fixes failed
- Propose prevention

The goal is to capture debugging lessons so the same class of issue doesn't recur.

#### 3.3 Spec update `[required · once]`

Load the `trellis-update-spec` skill and review whether this task produced new knowledge worth recording:
- Newly discovered patterns or conventions
- Pitfalls you hit
- New technical decisions

Update the docs under `.trellis/spec/` accordingly. Even if the conclusion is "nothing to update", walk through the judgment.

#### 3.4 Commit changes `[required · once]`

The AI drives a batched commit of this task's code changes so `/finish-work` can run cleanly afterwards. Goal: produce work commits FIRST, then bookkeeping (archive + journal) commits land after — never interleaved.

**Step-by-step**:

1. **Inspect dirty state**:
   ```bash
   git status --porcelain
   ```
   Snapshot every dirty path. If the working tree is clean, skip to 3.5.

2. **Learn commit style** from recent history (so drafted messages blend in):
   ```bash
   git log --oneline -5
   ```
   Note the prefix convention (`feat:` / `fix:` / `chore:` / `docs:` ...), language (中文/English), and length style.

3. **Classify dirty files into two groups**:
   - **AI-edited this session** — files you wrote/edited via Edit/Write/Bash tool calls in this session. You know what changed and why.
   - **Unrecognized** — dirty files you did NOT touch this session (could be the user's manual edits, leftover WIP from a previous session, or unrelated work). Do NOT silently include these.

4. **Draft a commit plan**. Group AI-edited files into logical commits (1 commit per coherent change unit, not 1 commit per file). Each entry: `<commit message>` + file list. List unrecognized files separately at the bottom.

5. **Present the plan once, ask for one-shot confirmation**. Format:
   ```
   Proposed commits (in order):
     1. <message>
        - <file>
        - <file>
     2. <message>
        - <file>

   Unrecognized dirty files (NOT in any commit — confirm include/exclude):
     - <file>
     - <file>

   Reply 'ok' / '行' to execute. Reply with edits, or '我自己来' / 'manual' to abort.
   ```

6. **On confirmation**: run `git add <files>` + `git commit -m "<msg>"` for each batch in order. Do not amend. Do not push.

7. **On rejection** (user replies "不行" / "我自己来" / "manual" / any pushback on the plan): stop. Do not attempt a second plan. The user will commit by hand; you skip ahead to 3.5 once they confirm.

```


## packages/cli/src/templates/guru/workflows/guru-client.md

```text

# lines 140-205

### Active Task Routing

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `client-design-overview-writing` / `client-design-detail-writing`；Gate 判定 → 对应 `*-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → 默认运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task>`（必要时拆分 implement/check）（官方 `trellis channel`，注入 flutter implementation/review skill）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → legacy dispatch `trellis-implement` / `trellis-check`（guru 口径），prompt 以 `Active task: <path>` 开头。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- 编辑前 → `trellis-before-dev`；编辑后 → `trellis-check`（guru 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待 requirements adversarial review + 确认、overview/detail 双 clean（各含 adversarial clean）、detail 确认后的 `task.py start`。
- 阶段跃迁必须经 `guru_gate.py confirm` 人工收口（strict=用户终端；soft=用户**本轮对话明确确认**后 agent 以 `--via-agent --user-quote "<用户原话>"` 代跑）；不得以自写 review 记录或机器检查通过替代；soft 下未获用户确认即代跑属违规（记录留痕可审计）。
- 合规 STOP：任何可能违反 App Store / Google Play 政策或美国法规的不确定性 → 立即停止，输出风险点+替代方案+人类确认清单。
- 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有验证证据。
- 产物语言中文优先（英文仅限标识符/命令/路径/协议字段/专有名词/缩写/原文引用）；面向用户的提问与结论一律中文。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。
after_create 钩子默认写入 `guru_chain: full`；按 Request Triage 判定为小改且**用户同意**走轻量链时，才把 task.json 改为 `guru_chain: light` 并记录理由。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包**（项目 docs 需求目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 仅作前置探索，不替代正式需求链。
**light 链**：加载 `trellis-brainstorm` 探索需求，直接产出 `prd.md`。
两轨 `prd.md` 口径一致：必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（一次问用户 1~4 个，不私自拍板）。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：上述五要素缺一 → 留在本步修订。结构过后（`guru_gate.py requirements <task_dir>` 通过），先运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>`。review 必须先查 `prd.md`、正式需求包、task context 与 repo evidence；medium+ 需求阻断输出 `route_class=REQ_BLOCKER` 并留在 1.1 修订，需求 digest 变更后下游 overview/detail 证据需重跑；低严重度措辞 nit 不阻断；clean 输出 `review_result=clean/requirements-ready`。requirements review 不使用 review-evidence Gate、不写 review_runs、不代替人工确认；clean 后停下等待 **confirm 人工收口**（通道按 gate_mode，见 Trellis System 节）；确认落盘后方可进 1.3。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。

#### 1.3 概要设计 `[required · repeatable]`
```


## packages/cli/src/templates/guru/workflows/guru-go.md

```text

# lines 140-205

5. 三条最高禁令（轻框架锁定 / 分层单向依赖 / 无 secret 字面量）贯穿五阶段，对应 Gate 直接 fail。

### Active Task Routing

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `go-design-overview-writing` / `go-design-detail-writing`（Go 平台专属设计 skill，按 Go doc_type 七分类展开）；Gate 判定 → 对应 `*-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → 默认运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task>`（必要时拆分 implement/check）（官方 `trellis channel`，注入 Go implementation/review skill）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `go-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → legacy dispatch `trellis-implement`（按 `go-implementation-guru-writing` 口径）/ `trellis-check`（按 `go-implementation-guru-review` 口径），prompt 以 `Active task: <path>` 开头。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `go-design-*-writing/review`（按 Go doc_type 展开）。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- 编辑前 → `trellis-before-dev`（读 golden-path + project-conventions + harness SSOT）；编辑按 `go-implementation-guru-writing` 口径；编辑后 → `trellis-check`（按 `go-implementation-guru-review` 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待 requirements adversarial review + 确认、overview/detail 双 clean（各含 adversarial clean）、detail 确认后的 `task.py start`。
- 阶段跃迁必须经 `guru_gate.py confirm` 人工收口（strict=用户终端；soft=用户**本轮对话明确确认**后 agent 以 `--via-agent --user-quote "<用户原话>"` 代跑）；不得以自写 review 记录或机器检查通过替代；soft 下未获用户确认即代跑属违规（记录留痕可审计）。
- 合规 STOP：触及鉴权/会话/密钥/用户数据采集或任何法规/政策不确定性 → 立即停止，输出风险点 + 替代方案 + 人类确认清单；密钥一律走环境变量名引用，不落字面量。
- 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有 `go build`/`go vet`/`go test`/`golangci-lint` 验证证据。
- 产物语言中文优先（英文仅限标识符/命令/路径/协议字段/库名/缩写/原文引用）；面向用户的提问与结论一律中文。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。
`guru_after_create` 钩子默认写入 `guru_chain: full`；按 Request Triage 判定为同包内小改且**用户同意**走轻量链时，才把 task.json 改为 `guru_chain: light` 并记录理由。创建后先按 golden-path 入口决策树确认服务边界（落在哪个 `services/<svc>/`、复用还是新建 `internal/` 子包、是否动 `packages/contracts/`）。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包**（项目 docs 需求目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 仅作前置探索，不替代正式需求链。
**light 链**：加载 `trellis-brainstorm` 探索需求，直接产出 `prd.md`。
两轨 `prd.md` 口径一致：必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（无未决也须显式声明「无未决」；一次问用户 1~4 个，不私自拍板）。Go 行为枚举到「协议端点 / 编排步骤 / 数据访问 / 失败收口」，例：`### BHV-012 创建代理用户` — Given 管理员会话有效 When `POST /api/users` 携带 `display_name`/`proxy_username` Then service 校验入参→repository 落库→触发 config 同步→返回 201；校验失败返回 400 携带 `ErrValidation`。反例 `### BHV-012 处理用户`（无前置/无协议/无失败路径）被需求 Gate 拒。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：五要素（行为编号 `BHV-NNN`、Given/When/Then、P0/P1 清单、失败路径章节、验收场景章节、未决问题章节）缺一 → 留在本步修订。结构过后（`guru_gate.py requirements <task_dir>` 通过），先运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>`。review 必须先查 `prd.md`、正式需求包、task context 与 repo evidence；medium+ 需求阻断输出 `route_class=REQ_BLOCKER` 并留在 1.1 修订，需求 digest 变更后下游 overview/detail 证据需重跑；低严重度措辞 nit 不阻断；clean 输出 `review_result=clean/requirements-ready`。requirements review 不使用 review-evidence Gate、不写 review_runs、不代替人工确认；clean 后停下等待 **confirm 人工收口**（通道按 gate_mode，见 Trellis System 节）；确认落盘后方可进 1.3。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。Go 后端常见研究项：既有服务的 `internal/` 包结构与导入图（确认不引入反向依赖）、`packages/contracts/` 现有契约字段、`db/migrations/` 现状与迁移版本号、目标服务的 env 前缀与 `config.Load()` 现有键。
```


## guru-template/overlay/verify/guru_gate.py

```text

# lines 80-185


DETAIL_CONTRACT_PATTERNS = [
    ("行为定义/清单", r"行为清单|行为定义|承接.{0,8}行为"),
    ("失败收口", r"失败.{0,8}收口|失败如何|错误类型表|异常表|错误映射"),
    ("测试映射", r"测试映射|哪些测试"),
    ("不得补造声明", r"不得.{0,8}补造|不在此补造|不决定|不拥有"),
]

BRAINSTORM_EVIDENCE_LABELS = [
    ("Skill loaded", ("skill loaded",)),
    ("Repository evidence inspected", ("repository evidence inspected",)),
    ("Domain/terminology triggers", ("domain/terminology triggers", "domain grill triggers")),
    ("Current code vs user intent conflicts", ("current code vs user intent conflicts",)),
    ("Product decisions confirmed", ("product decisions confirmed",)),
    ("Open product/scope/risk questions", ("open product/scope/risk questions",)),
]
BRAINSTORM_PLACEHOLDERS = {
    "",
    "pending",
    "tbd",
    "todo",
    "待定",
    "未填写",
    "未确认",
}
BRAINSTORM_NEGATIVE_PREFIXES = (
    "none",
    "not triggered",
    "no open questions",
    "无",
    "没有",
    "不触发",
)
BRAINSTORM_RECOVERY = "load trellis-brainstorm, complete Domain Grill / one-question loop, then update prd.md"


def fail(gate: str, problems: list) -> int:
    sys.stderr.write(f"[guru-gate:{gate}] 未通过，缺口：\n")
    for p in problems:
        sys.stderr.write(f"  - {p}\n")
    sys.stderr.write("修复后重试；语义级判定请走对应 review loop 并用 record-review 留痕。\n")
    return BLOCK


def ok(gate: str, note: str = "") -> int:
    print(f"[guru-gate:{gate}] 通过{(' — ' + note) if note else ''}")
    return PASS


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _brainstorm_section(prd: str) -> str:
    match = re.search(r"(?im)^##\s+Brainstorm Evidence\s*$", prd)
    if not match:
        return ""
    rest = prd[match.end():]
    next_heading = re.search(r"(?m)^##\s+", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _brainstorm_line_value(section: str, aliases: tuple) -> str | None:
    for raw_line in section.splitlines():
        line = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", raw_line).strip()
        lower = line.lower()
        for alias in aliases:
            if lower.startswith(alias):
                return line[len(alias):].lstrip(" \t:-—").strip()
    return None


def _negative_evidence_has_reason(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered.startswith(BRAINSTORM_NEGATIVE_PREFIXES):
        return True
    return bool(re.search(r"(?:--?|—|:|：|because|due to|因为|理由|原因)\s*\S+", value))


def _brainstorm_evidence_problems(prd: str) -> list:
    section = _brainstorm_section(prd)
    if not section.strip():
        return ["Brainstorm Evidence missing: add `## Brainstorm Evidence` to prd.md"]

    problems = []
    for label, aliases in BRAINSTORM_EVIDENCE_LABELS:
        value = _brainstorm_line_value(section, aliases)
        if value is None:
            problems.append(f"Brainstorm Evidence missing: {label}")
            continue
        normalized = value.strip().lower()
        if normalized in BRAINSTORM_PLACEHOLDERS:
            problems.append(f"Brainstorm Evidence pending: {label}")
        elif not _negative_evidence_has_reason(value):
            problems.append(f"Brainstorm Evidence needs reason: {label}")
    return problems


def _brainstorm_status_mark(task_dir: str) -> str:
    problems = _brainstorm_evidence_problems(read(os.path.join(task_dir, "prd.md")))
    if not problems:
        return "✅ present"

# lines 410-445



# =========================================================================
# 五阶段 Gate
# =========================================================================

def check_requirements(task_dir: str) -> int:
    """需求 Gate：行为规格(BHV 编号标题) / P0 P1 / 失败路径 / 验收 / 未决问题。"""
    prd = read(os.path.join(task_dir, "prd.md"))
    problems = []
    if not prd:
        return fail("requirements", ["prd.md 不存在或为空"])
    if not BHV_DEF.search(prd):
        problems.append("缺行为编号：行为须以 `### BHV-NNN <短名>` 标题定义（编号纪律）")
    if not (re.search(r"\bGiven\b", prd) and re.search(r"\bWhen\b", prd) and re.search(r"\bThen\b", prd)):
        problems.append("缺行为规格：未找到 Given/When/Then 三段式（至少一组）")
    # 不用 \bP0\b：Python \b 把 CJK 当 word 字符，"优先级P0" 会失配（同文件头部反 \b 纪律）。
    # 守卫用显式 ASCII-word 类（含数字/下划线）两侧对称：放过 CJK 紧贴，挡掉 step_P0/3P0/P0Beta 假阳性。
    if not re.search(r"(?<![A-Za-z0-9_])P[01](?![A-Za-z0-9_])", prd):
        problems.append("缺核心能力清单：未找到 P0/P1 优先级标记")
    if not re.search(r"失败路径|失败场景|异常路径|failure", prd, re.I):
        problems.append("缺失败路径章节")
    if not re.search(r"验收|acceptance", prd, re.I):
        problems.append("缺验收场景/标准章节")
    if not re.search(r"未决|open question|待确认", prd, re.I):
        problems.append("缺未决问题章节（无未决也须显式声明）")
    brainstorm_problems = _brainstorm_evidence_problems(prd)
    if brainstorm_problems:
        problems.extend(brainstorm_problems)
        problems.append(f"恢复步骤：{BRAINSTORM_RECOVERY}")
    return fail("requirements", problems) if problems else ok("requirements")


def _check_package_skeleton(task_dir: str) -> list:
    """full 链设计包结构检查。返回缺口清单（空=通过）。"""
    pkg = _package_dir(task_dir)

# lines 1200-1250

    tj_path = _write_task_data_atomic(task_dir, data)
    state = _review_state(task_dir, gate)
    print(
        f"[guru-gate:record-review] ✅ 已记录 {GATE_LABEL[gate]} review "
        f"result={result} max_severity={max_severity} run_id={run_id} "
        f"clean={state['clean_count']}/{REQUIRED_CLEAN_REVIEWS}（{tj_path}）"
    )
    return PASS


def _record_confirm(task_dir: str, gate: str, via: str, user_quote=None) -> int:
    """写入单个 Gate 的确认记录（严格 JSON 守卫 + 原子写）。via ∈ tty|agent。"""
    data = _task_data_for_write(task_dir, "confirm")
    if data is None:
        return BLOCK
    gates = data.setdefault(GATES_KEY, {})
    previous = gates.get(gate)
    record = {
        "confirmed_by": _developer_name(),
        "confirmed_at": _now_iso(),
        # 确认快照：check 时比对，产物在确认后被修改 → 要求重新确认
        "artifact_digest": _gate_digest(task_dir, gate),
    }
    if isinstance(previous, dict) and isinstance(previous.get("grill"), dict):
        record["grill"] = previous["grill"]
    if via == "agent":
        record["mode"] = "soft"
        record["via"] = "agent"  # 留痕：对话确认、agent 代跑（非 TTY 人手证明）
        if user_quote:
            record["user_quote"] = user_quote[:500]  # 用户确认原话（审计：伪造须编造用户言论）
    gates[gate] = record
    tj_path = _write_task_data_atomic(task_dir, data)
    suffix = "（soft：对话确认，agent 代跑）" if via == "agent" else ""
    print(f"[guru-gate:confirm] ✅ {GATE_LABEL[gate]} Gate 已由 {record['confirmed_by']} 确认{suffix}（已写入 {tj_path}）")
    return PASS


def _record_grill(task_dir: str, gate: str, status: str, via: str, user_quote=None) -> int:
    """写入 design-grill 完成/跳过记录（严格 JSON 守卫 + 原子写）。via ∈ tty|agent。"""
    policy = _grill_policy(task_dir, gate)
    data = _task_data_for_write(task_dir, f"grill-{status}")
    if data is None:
        return BLOCK
    gates = data.setdefault(GATES_KEY, {})
    entry = gates.setdefault(gate, {})
    if not isinstance(entry, dict):
        entry = {}
        gates[gate] = entry
    record = {
        "status": status,
        "by": _developer_name(),

# lines 1360-1430

        sys.stderr.write(
            f"[guru-gate:{channel}] soft 模式 agent 代跑必须带 --user-quote \"<用户确认原话/理由>\" 记录审计留痕\n"
        )
        return False, interactive, mode
    return True, interactive, mode


def _pending_gates(task_dir: str) -> list:
    """按阶段顺序列出待人工确认 Gate（未确认 / 缺快照 / 快照失配）。"""
    states = _gate_states(task_dir)
    pending = []
    for g in HUMAN_GATES:
        s = states.get(g)
        ok_record = (isinstance(s, dict) and s.get("confirmed_by")
                     and s.get("artifact_digest") == _gate_digest(task_dir, g))
        if not ok_record:
            pending.append(g)
    return pending


def cmd_confirm(gate_arg, task_dir_arg, via_agent: bool = False, user_quote=None) -> int:
    if gate_arg is not None and gate_arg not in HUMAN_GATES:
        if gate_arg in REVIEW_GATES:
            sys.stderr.write(
                f"[guru-gate:confirm] {gate_arg} 不再走人工确认；请通过 record-review 累积两个当前 digest 的 clean review\n"
            )
        else:
            sys.stderr.write(f"[guru-gate:confirm] 未知 gate: {gate_arg}（可选: {', '.join(HUMAN_GATES)}；省略=批量确认全部待确认 Gate）\n")
        return BLOCK
    task_dir = resolve_task_dir(task_dir_arg)
    if not task_dir:
        sys.stderr.write("[guru-gate:confirm] 无法定位任务目录，请显式传 task_dir\n")
        return BLOCK
    allowed, interactive, mode = _authorize_gate_write("confirm", via_agent, user_quote)
    if not allowed:
        return BLOCK
    targets = [gate_arg] if gate_arg else _pending_gates(task_dir)
    if not targets:
        print(f"[guru-gate:confirm] 需求/详细两个人工 Gate 均已确认且快照一致（{task_dir}），无需操作")
        return PASS
    print(f"任务：{task_dir}（gate_mode={mode}）")
    checkers = {"requirements": check_requirements, "detail": check_detail}
    for g in targets:
        # 结构 Gate 未过时确认无意义，先拦下（批量模式停在首个未过阶段）
        if checkers[g](task_dir) != PASS:
            sys.stderr.write(f"[guru-gate:confirm] {GATE_LABEL[g]}结构 Gate 未过，先修复缺口再确认；本次到此为止。\n")
            return BLOCK
        if g == "requirements":
            _warn_requirements_review_before_confirm(task_dir)
        if g == "detail":
            for review_gate in REVIEW_GATES:
                if not _review_state(task_dir, review_gate)["ready"]:
                    return _block_review("confirm", task_dir, review_gate)
        if interactive:
            print(f"即将确认【{GATE_LABEL[g]} Gate】通过，允许进入下一阶段。")
            try:
                answer = input("确认请输入 yes/y（其他=取消）：").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer not in ("yes", "y"):
                print("已取消，本 Gate 及后续未写入确认。")
                return BLOCK
        rc = _record_confirm(task_dir, g, "tty" if interactive else "agent", user_quote=user_quote)
        if rc != PASS:
            return rc
    return PASS


def cmd_grill_done(gate_arg, task_dir_arg, via_agent: bool = False, user_quote=None) -> int:
    if gate_arg not in ALL_GATES:
        sys.stderr.write(f"[guru-gate:grill-done] 需要 gate 参数（{', '.join(ALL_GATES)}）\n")
```


## guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md

```text
# 需求文档体系（单一来源）

本文档是需求文档“语义单一来源（SSOT）”的中立主定义。写作技能与审核技能均以本文档为准。

## 1. 适用范围

- 适用于含前端（App/Web）、API-only、CLI-only 或混合入口的产品需求文档。
- 覆盖文档组织、章节承载、阶段推进、写作合同、完成口径与收敛口径。
- 若其他文档与本文档冲突，以本文档为准并在对应文档修正引用。

## 2. 推荐目录形态（非强制）

```text
requirements/
├── README.md
├── requirement-main.md
├── requirement-api.md               # 可选，API 适用时启用
├── requirement-cli-command.md       # 可选，存在 CLI 入口时启用
├── requirement-non-functional.md
├── modules/                         # 可选，按需拆分详细章节
│   └── requirement-<module>.md
├── requirement-<domain-or-ui>.md    # 可选，详细章节聚合文档
├── changes/
│   ├── change-log.md
│   └── changes/
└── assets/
```

## 3. 语义强约束（完成口径）

- 同一事实只允许一个主定义位置（SSOT）。
- 第一章与第二章入口组织主定义必须位于 `requirement-main.md`。
- 第一章主定义除产品用途、目标用户、用户核心痛点、主要功能及核心场景外，必须包含“核心能力定义”主定义。
- 第二章为入口组织结构：有 UI 时承载页面组织结构；无 UI 时承载 API/CLI 等入口组织关系或明确“不适用”。第二章只保留摘要，不承载可执行规则。
- 第三章起页面详细、API（若适用）、CLI（若适用）、非功能规则必须可追踪到唯一主定义。
- 文档形态（`modules/` 拆分或聚合文档）不作为完成硬约束。

## 4. 文档职责（主从边界）

- `README.md`：仅维护导航、索引、追踪矩阵、版本入口；不承载第一章/第二章事实正文。
- `requirement-main.md`：第一章（产品总述）与第二章（入口组织结构；有 UI 时为页面组织结构）主定义。
- `modules/requirement-<module>.md` 或等价聚合页面文档：第三章起页面详细主定义。
- `requirement-api.md`：服务端 API 契约主定义（仅在 API 适用时创建）。
- `requirement-cli-command.md`：CLI Command 契约主定义（仅在 CLI 适用时创建）。
- `requirement-non-functional.md`：非功能主定义。
- `changes/*`：版本变更记录，不承载业务规则主定义。

## 5. 章节承载与可执行规则边界

- 第一章：产品用途、目标用户、用户核心痛点、主要功能及核心场景，以及“核心能力定义”主定义（主定义在 `requirement-main.md`）。
- 第二章：入口清单、关系、编号命名、摘要级入口简述；有 UI 时包含页面清单、页面关系和摘要级页面简述（主定义在 `requirement-main.md`）。
- 第三章起：页面可执行规则（状态、校验、交互、业务逻辑）主定义在页面详细文档。
- API：接口输入输出、异常、必要步骤主定义在 `requirement-api.md`（若适用）。
- CLI：命令、参数、输出语义、退出码等主定义在 `requirement-cli-command.md`（若适用）。
- 非功能：性能、安全、可用性、兼容性主定义在 `requirement-non-functional.md`。
- API 与 CLI 入口契约相互独立：两类文档分别维护各自主定义，不得把一方文档作为另一方成立的唯一前提。

API 必要步骤判定（适用于 `requirement-api.md` 主定义）：
- `必要步骤` 仅用于“业务语义正确且可验收所必需”的动作，不用于描述可替代的技术实现过程。
- 判断是否需要 `必要步骤` 时，不按“写操作/读操作”机械区分；当不写会导致外部结果歧义、不可验证或跨团队实现分叉时，必须增加该小节。
- 若接口业务语义已能由输入、输出和异常完整表达，且不写 `必要步骤` 不会造成验收歧义或实现分叉，可不声明 `必要步骤`。

第二章禁写项（出现即越界）：
- 校验阈值与参数集合。
- 状态机与强约束流转规则。
- 守恒公式或统计口径公式。
- 错误码边界与失败补偿判定。
- “必须/不得/仅允许”等可执行约束语义。

### 5.1 API/CLI 适用标准（强制，单一来源）

本小节是 API/CLI 适用性判定的唯一主定义。写作与审核文档仅可引用，不得重复定义或改写判定口径。

- API 适用：需求存在服务端可调用接口契约（如 HTTP/gRPC/GraphQL/Webhook/内部服务接口等）需要对外或对内协作。
- API 不适用：需求不包含任何服务端可调用接口契约（例如纯本地工具或纯前端静态演示），此时不创建 `requirement-api.md`。
- CLI 适用：需求存在命令行入口契约（命令/子命令/参数/输出语义/退出码）供用户、运维或自动化任务调用。
- CLI 不适用：需求不存在命令行入口契约，此时不创建 `requirement-cli-command.md`。
- 独立性：API 与 CLI 适用性彼此独立，允许“仅 API”“仅 CLI”“两者都适用”“两者都不适用”四种状态。
- 记录要求：必须在 `README.md` 的导航或追踪矩阵中显式声明 API/CLI 的适用性；若不适用，需写明“不适用”说明。

### 5.2 核心能力定义（强制，单一来源）

本小节是需求阶段“核心能力”的唯一主定义来源，默认位于 `requirement-main.md` 第一章。表格字段名中的 `capability_*` 为稳定字段标识，正文统一称“核心能力”。

命名消歧：核心能力表中的 `priority` 表示 `capability_priority`，取值为 `P0/P1/P2`；审核发现中的 `P1/P2/P3` 表示 `finding_severity`。两者不得混用，输出时应通过字段名或上下文明确区分。

- 核心能力默认指从 `1.4` 全量场景清单及后续校正后的关键 `REQ-UC` 行为链中抽取出的系统难点问题域：它直接服务业务结果、决定主价值链成败，并会在概要设计与详细设计阶段形成主要技术难点或系统复杂点。
- 需求阶段定义核心能力的目标是识别“后续设计必须深入思考和细粒度展开的问题空间”，不是提前给出架构方案、技术选型或实现细节。
- 核心能力不是普通需求本身，也不是技术组件名；一条合格的核心能力必须同时表达业务目标、关键行为链、复杂度来源、可验证约束或失败风险，以及后续设计必须展开的问题。
- 核心能力与 `REQ-UC` 不建立对应、覆盖、映射或验收替代关系；只通过 `source_req_refs` 记录来源/归属，说明该难点从哪些场景或入口意图中被识别出来。
- 不要求每个 `REQ-UC` 都被核心能力引用；未被引用的 `REQ-UC` 只表示该场景没有上升为本轮核心难点，不表示场景缺失。
- 核心能力允许分层：`top_level` 表示直接决定主价值链的顶层核心能力；`derived` 表示从某个顶层核心能力中拆出的派生核心能力/子核心能力。
- 派生核心能力仅在子问题能独立破坏顶层核心能力的成功标准，且需要在概要设计/详细设计中单独展开状态、数据、边界、延迟、规模、一致性、降级或外部依赖时成立；不得把普通实现任务、模块拆分或组件清单写成派生核心能力。
- 鉴权、缓存、审计、监控、重试、调度、模型网关、通用模型调用封装等平台级/切面级/通用支撑项，默认只作为依赖、约束或质量/回退/可观测语义承接，不单独进入核心能力集。
- 若某项平台型事项本身就是产品对外提供的核心价值，必须先改写为业务结果导向的核心能力定义，方可进入核心能力集；不得直接以技术构件名入表。
- 完成 `1.4 主要功能及核心场景` 的全量场景清单后，应先提取阶段 0 初版核心能力候选；后续页面/API/CLI/非功能细化若新增或改变关键 `REQ-UC`，必须回写候选池与正式核心能力清单。
- 核心能力候选采用组合判定，不按单一信号入选：
  1. 必须命中主价值链关键节点或高失败成本：失败会导致主价值链中断、严重降级、不可验收或高概率返工；
  2. 必须至少命中一个系统难点信号；
  3. 必须能说清后续概要设计/详细设计需要单独展开的问题空间。
- 系统难点信号包括：
  - 动态决策：运行时需要基于上下文、规则、优先级、冲突或策略输出不同结果；
  - 状态黏着：结果必须跨请求、跨时间或跨入口保持稳定，不允许漂移；
  - 性能规模：存在明确低延迟、高并发、大连接数、大 fan-out 或高吞吐约束；
  - 外部依赖：关键路径依赖上游服务、异步数据或跨域查询，且超时/降级会改变业务结果；
  - 一致性边界：涉及版本、幂等、顺序、事务、最终一致、回滚或补偿；
  - 可诊断性：失败后必须能解释命中/未命中、分配、通知、降级或回退原因；
  - 高返工风险：若需求阶段不先识别，概要设计/详细设计会遗漏关键模型、存储、索引、协议或降级路径。
- 仅命中宽泛信号但不影响主价值链的普通接口、普通依赖调用、普通日志诊断、常规缓存或常规 CRUD，不得入选核心能力。
- 阶段 0 产物必须同时具备三部分：
  1. 全量场景清单：用于覆盖范围边界与 `REQ-UC-XXX`；
  2. 核心能力候选池与取舍记录：用于说明“为什么入选/为什么落选”；
  3. 正式核心能力清单：用于承载进入设计前需要收敛的重点/难点行为。
- 核心能力字段合同、候选池记录要求与证据收敛状态定义只在本小节维护；写作技能、审核技能、模板与示例只可引用或完整复用，不得另起一套字段集合。

候选池与取舍记录最小字段：

| 字段 | 说明 |
| --- | --- |
| `candidate_name` | 候选核心能力名称 |
| `source_req_refs` | 来源/归属场景或接口意图编号；阶段 0 初版只使用 `REQ-UC-XXX` 或“API/CLI 待判定”，API/CLI 主定义完成后再在校正时补充接口意图编号 |
| `decision` | `selected / dropped / pending` |
| `decision_rationale` | 入选、落选或暂缓的原因；必须说明该候选与主价值链/失败成本、系统难点信号、后续设计展开空间三项判定的关系 |

`decision_rationale` 不要求拆成多列，但不得只写“覆盖更多场景”“优先级较高”等泛化理由。`selected` 必须说明三项判定均成立；`dropped` 必须说明缺失哪项关键判定或为何可由普通需求承接；`pending` 必须说明当前缺少的判定证据。

正式核心能力清单最小字段：

| 字段 | 说明 |
| --- | --- |
| `capability_id` | 稳定标识，跨阶段不变 |
| `capability_name` | 核心能力名称 |
| `capability_level` | `top_level / derived` |
| `parent_capability_refs` | 派生核心能力所属的父级核心能力编号；顶层核心能力写 `无` |
| `priority` | `P0/P1/P2` |
| `business_outcome` | 该核心能力直接服务的业务结果 |
| `value_chain` | 从输入到输出的主价值链 |
| `difficulty_focus` | 需要优先确认的难点行为链环节 |
| `complexity_source` | 复杂度来源 |
| `design_focus` | 概要设计/详细设计阶段必须重点思考的系统设计问题 |
| `design_expansion_requirement` | 后续设计需展开到的粒度要求，例如状态、数据、边界、异常、一致性、性能、安全、可观测或回退 |
| `risk_if_missed` | 若需求阶段未优先识别该核心能力，会导致的返工或交付风险 |
| `success_metrics` | 成功指标，至少包含口径/时间窗/样本 |
| `failure_impact` | 失败业务后果 |
| `acceptance_bar` | 最低验收标准 |
| `validation_strategy` | 需求阶段即可执行的前置验证策略 |
| `source_req_refs` | 来源/归属编号，用于说明该核心能力来自或归属于哪些 `REQ-UC-XXX` / `API-INTENT-XXX` / `CLI-INTENT-XXX`；阶段 0 初版只使用 `REQ-UC-XXX` 或“API/CLI 待判定”，API/CLI 主定义完成后再在校正时补充接口意图编号 |
| `evidence_refs` | 需求证据、痛点证据或业务目标证据 |
| `priority_score` | 评分明细与总分 |
| `priority_rationale` | 为什么是 `P0/P1/P2` |
| `counterfactual_check` | 反证回答：若延期，该系统是否仍可定义为成功交付 |
| `confirmation_status` | `ai_drafted` / `evidence_ready` / `user_confirmed` / `user_confirmed_with_edits` |
| `open_questions` | 尚待确认的问题；无则写 `无`；若会阻断概要设计，需明确说明风险 |

优先级判定合同：

- `priority` 表示核心能力优先级（`capability_priority`），不是审核发现严重度。
- `P0`：若延期或缺失，系统不能被定义为本轮成功交付；`counterfactual_check` 应明确回答“不能”并说明主价值链如何中断。
- `P1`：若延期或缺失，系统仍可形成受限交付或演示，但主价值、真实使用、验收可信度或后续设计会出现明显降级；`counterfactual_check` 应说明可继续的前提与不可接受的损失。
- `P2`：重要但不直接决定主价值链成败，可由普通需求、约束或后续迭代承接；若它需要进入核心能力集，必须说明独立设计展开价值。
- `priority_score` 只作为优先级证据，不自动决定 `P0/P1/P2`。建议使用 `业务影响 / 系统复杂度 / 失败成本` 三项 `1~5` 分记录评分明细；项目也可替换评分维度，但必须保持同一文档内一致。
- 防膨胀约束：默认一个需求范围只应保留极少数 `P0`；若 `P0/P1` 超过 3 项，或超过已选核心能力的大多数，必须重新检查是否把普通场景、模块拆分或平台支撑项写成核心能力，并给出合并、降级或保留理由。
- 反证优先：若反证显示“延期后仍不影响本轮成功交付”，不得标为 `P0`；若缺少独立的设计展开问题空间，不得标为 `P0/P1`。

强制约束：

- 每个 `P0/P1` 核心能力必须至少标明一个来源/归属编号，优先使用触发该难点的 `REQ-UC-XXX`。
- 每个 `derived` 核心能力必须填写 `parent_capability_refs`，并说明它如何支撑或约束父级核心能力的成功标准。
- 若某个派生核心能力的优先级高于父级核心能力，应重新检查父级拆分是否合理，避免把真正的顶层难点误写成子项。
- 每个核心能力都必须给出 `evidence_refs`，不得凭空命名。
- 每个核心能力都必须给出 `priority_score`、`priority_rationale` 与 `counterfactual_check`，且优先级结论必须能被反证回答支撑。
- 每个 `P0/P1` 核心能力都必须给出 `design_focus` 与 `design_expansion_requirement`，用于承接概要设计与详细设计；该字段只描述设计问题空间和展开粒度，不写具体实现方案。
- 进入概要设计前，所有 `P0/P1` 核心能力必须完成证据收敛：字段齐全、证据可追踪、优先级理由可辩护，且不存在会改变范围或验收口径的高风险待确认问题。
- 若 `confirmation_status=evidence_ready` 且无高风险待确认问题，可带明确假设进入概要设计；若 `confirmation_status=ai_drafted` 或仍存在高风险 `open_questions`，可以继续完善需求草稿，但不得宣称“可进入概要设计”。
- 若本次范围被判定为“纯维护 / 纯工具化 / 非核心交付”，允许无 `P0`，但必须显式记录该结论与依据。

合法无 `P0/P1` 主线声明：

- 仅当完成全量场景清单、候选池与取舍记录后，所有候选核心能力均被判定为 `P2` 或 `dropped`，且本轮范围仍可由普通需求、约束或后续迭代承接时，才可声明无可承接的 `P0/P1` 核心能力主线。
- 声明位置固定在 `requirement-main.md` 第一章“核心能力定义”主定义内，不得散落到 `README.md`、审核输出或设计文档中。
- 最小字段为：`exception_type`（`no_p0` / `no_p0_p1`）、`scope_refs`、`basis`、`candidate_decision_refs`、`design_handoff`、`confirmation_status`、`open_questions`。
- `exception_type=no_p0` 只表示没有 `P0`；若仍存在 `P1`，概要设计必须继续承接 `P1`。
- 只有 `exception_type=no_p0_p1` 才允许后续概要设计将 `Capability-to-Architecture Mapping` 标记为 `N/A：需求已声明无 P0/P1 核心能力主线`。若 `confirmation_status=ai_drafted`，或 `open_questions` 中存在会改变范围/验收口径的问题，不得作为概要阶段 `N/A` 依据。

### 5.3 非功能范围豁免（强制记录口径）

非功能需求是默认检查项，但不是所有子项都必须在所有需求范围内展开。若性能、安全、可用性、兼容性或其他非功能子项在本轮需求中不适用，必须显式声明范围豁免；不得用空章节、泛化一句话或缺失文档来代替豁免。

需求文档中的非功能范围豁免至少记录：

| 字段 | 说明 |
| --- | --- |
| `waived_item` | 被豁免的非功能子项或具体约束 |
| `scope_refs` | 适用范围，可引用 `REQ-UC-XXX` / `API-INTENT-XXX` / `CLI-INTENT-XXX`，或写明“全局” |
| `waiver_reason` | 为什么本轮不展开；必须能回到业务范围、交付阶段或入口适用性 |
| `risk_statement` | 不展开该子项带来的风险口径、已接受边界或后续补齐条件 |

审核指令也可以声明单次审核的非功能范围豁免；若审核指令与需求文档冲突，`requirement-review` 以审核指令为准并在输出中记录来源。除非用户明确要求固化，单次审核指令中的豁免不自动改写为需求事实。

## 6. 场景与接口编号契约（防漂移）

为保证“需求 -> 概要设计 -> 详细设计”跨阶段追踪稳定，需求文档必须维护以下编号：

- `REQ-UC-XXX`：需求场景编号（Use Case Source ID）
  - 主来源：`requirement-main.md` 第一章核心场景 + 第二章入口组织骨架
  - 细化来源：第三章起页面详细主定义文档
- `API-INTENT-XXX`：API 业务意图编号（若适用）
  - 主来源：`requirement-api.md`
- `CLI-INTENT-XXX`：CLI 命令业务意图编号（若适用）
  - 主来源：CLI 相关需求主定义位置

编号稳定性规则：

1. 已发布编号不得因排序或重构重排。
2. 语义变化时新增编号；旧编号标记为 deprecated，不复用。
3. 任何 API（若适用）/CLI（若适用）必须回指至少一个 `REQ-UC-XXX`，不得出现无来源接口意图。
4. 若 API 或 CLI 整体不适用，只需在 `README.md` 记录不适用理由，不要求逐个 `REQ-UC-XXX` 声明豁免。
5. UI-only、纯前端展示、纯文案或不形成服务端/命令入口契约的场景，属于正常“不映射接口意图”；在追踪表中标记“无接口入口/无命令入口 + 简短原因”即可，不视为 `UC-接口映射豁免`。
6. `UC-接口映射豁免` 仅用于“按当前范围本应映射 API/CLI 意图，但本次明确不新增或不改变接口/命令契约”的例外场景。
7. 真正使用 `UC-接口映射豁免` 时，声明主体必须是对应 `REQ-UC-XXX`，并在主定义处记录豁免原因与必要影响说明；不得在 `API-INTENT-XXX` 或 `CLI-INTENT-XXX` 条目上声明“无来源豁免”。
8. 完成收敛与全稿复核时必须输出“编号差集检查结果”，并区分正常不映射、真实豁免与缺失映射。

### 6.1 入口分支追踪规则（强制，单一来源）

本小节定义 `REQ-UC` 与页面/API/CLI 的追踪关系。写作与审核文档仅可引用，不得重复定义映射基数或改写为线性链路。

- UI 场景：`REQ-UC-XXX -> 入口组织结构中的页面组织 / 页面详细 -> API-INTENT-XXX / CLI-INTENT-XXX（若需要） -> 非功能`
- API-only 场景：`REQ-UC-XXX -> API-INTENT-XXX -> 非功能`
- CLI-only 场景：`REQ-UC-XXX -> CLI-INTENT-XXX -> 非功能`
- 混合场景：允许一个 `REQ-UC-XXX` 同时分支到页面与 API/CLI；是否存在页面，取决于该场景是否包含 UI 入口，而不是默认强制要求。
- 第二章只要求覆盖本需求实际存在的入口：有 UI 时覆盖 UI 功能和 UI 场景；无 UI 时记录 API-only/CLI-only 入口组织关系并明确页面组织不适用。若某个页面涉及 `P0/P1` 核心能力，可标注相关核心能力用于提醒后续设计关注，不要求页面与核心能力建立承接或覆盖关系。
- 每个 `API-INTENT-XXX` / `CLI-INTENT-XXX` 必须回指至少一个 `REQ-UC-XXX`。
- 一个 `API-INTENT-XXX` / `CLI-INTENT-XXX` 可以回指多个 `REQ-UC-XXX`，前提是这些场景共享同一业务意图、验收边界、必要步骤与输出语义。
- 若多个场景在验收口径、必要步骤、失败语义或退出语义上存在实质差异，必须拆分为不同的 `API-INTENT-XXX` / `CLI-INTENT-XXX`。
- 完成收敛关注的是“按入口类型分支后的可达性与单一来源”，而不是机械要求 `功能 -> 页面 -> API -> CLI -> 非功能` 的单线串接。

## 7. 双时态机制

### 7.0 阶段 0：核心能力初版收敛与校正

- 初版时间位置：完成文档骨架后，在 `requirement-main.md` 第一章内先完成 `1.1`~`1.4` 的全量场景清单，再基于该清单产出候选池与正式核心能力清单。
- `1.6 场景编号与接口意图追踪` 在阶段 0 只建立 `REQ-UC-XXX` 与入口类型占位，可标记“API 待判定 / CLI 待判定 / 无接口入口 / 无命令入口”；不得在 API/CLI 主定义完成前强行生成最终 `API-INTENT-XXX` 或 `CLI-INTENT-XXX`。
- 阶段 0 默认采用 `AI 草拟 -> 用户校准 -> 用户拍板` 的写作合同：AI 可先产出 `confirmation_status=ai_drafted`；证据齐全且无高风险待确认问题时可标记为 `evidence_ready`；只有用户明确拍板后，才可写为 `user_confirmed` 或 `user_confirmed_with_edits`。
- `requirement-review` 只检查 `confirmation_status` 与 `open_questions` 是否满足进入概要设计的条件，不替代用户完成业务确认。
- 用户确认问题应压缩到 `1~4` 个关键问题。
- 阶段 0 初版至少要产出标准包 `5.2` 规定的三部分内容：全量场景清单、候选池与取舍记录、正式核心能力清单。
- 未完成阶段 0 初版收敛前，不得进入第二章及后续详细展开。
- 第二章及后续页面/API/CLI/非功能细化过程中，若新增 `REQ-UC`、改变关键行为链、发现新的系统难点或证伪已选核心能力，必须回写候选池与正式核心能力清单；这属于阶段 0 校正，不视为流程倒退。
- API/CLI 主定义完成后，必须回填 `1.6` 的最终接口意图追踪，并在完成收敛时输出正常不映射、真实豁免与缺失映射的差集结果。
- 进入概要设计前必须完成阶段 0 最终校正；`P0/P1` 核心能力证据未收敛或存在高风险待确认问题时，不得进入概要设计。

### 7.1 阶段写作时态

- 允许第二章摘要与详细文档短期并存同一业务事实。
- 约束：第二章只可保留摘要，不得承载可执行规则主定义。
- 目标：快速建立全局骨架并逐步下沉规则到主定义文档。

### 7.2 完成收敛时态

- 进入条件：整体复审、发布前、进入开发/设计前。
- 必做动作：清理重复事实，确保可执行事实只保留一个主定义位置。
- 完成口径：重复主定义清零；引用链可达；映射关系完整且一致。

### 7.3 阶段切换与轻量确认

- 阶段写作默认由 `requirement-writing` 先执行内置轻量自检，不额外调用 `$requirement-review`。
- 仅当存在高风险未决项时才暂停，并向用户提出 `1~4` 个关键问题：
  - 核心能力入选/落选难以判断；
  - API/CLI 适用性无法从现有范围直接判定；
  - 验收口径、边界条件或编号映射存在明显分叉风险；
  - 继续推进会高概率造成后续大面积返工。
- 若不存在上述高风险未决项，允许连续推进到下一阶段，不机械逐阶段等待确认。

## 8. 固定阶段流程

```text
准备步骤 -> 建立文档骨架（README + requirement-main + 子文档链接）
阶段 0 -> 完成第一章主线初版（1.1~1.5；1.6 只建立 REQ-UC 与入口类型占位）
阶段 1 -> 完成第二章入口组织结构（摘要级；有 UI 时包含页面组织结构）
阶段 2 -> 完成页面详细需求主定义（若适用）
阶段 3 -> 完成 API 主定义（若适用）
阶段 4 -> 完成 CLI Command 主定义（若适用）
阶段 5 -> 完成非功能主定义
阶段 6 -> 回填 1.6 最终接口意图追踪，执行完成收敛清理与整体复审
```

## 9. 单一来源与单向维护

- 同一事实只在一个主文档/主章节定义，其他位置仅引用。
- 通用规范仅定义规则与适用条件，不维护消费方清单。
- 消费方文档必须显式声明遵循的规范并链接到主定义。
- 任一跨文档引用变更后，必须校验引用链和版本矩阵一致性。

## 10. 写作与复核协同规则

- 阶段写作中的中间态默认执行 `requirement-writing` 内置轻量自检；仅高风险歧义时暂停做少量确认，不单独调用 `$requirement-review`。
- `$requirement-review` 仅用于需求全稿完成后的复核，不参与阶段写作中的业务确认。
- 全稿复核必须先检查“阶段 0 核心能力初版收敛与最终校正”是否完成；未完成时不得给出“可进入概要设计”结论。
- 复核若发现文档组织不满足语义 SSOT，应指出缺失或重复的主定义位置，并回到写作阶段修正。
- 审核发现严重度、Findings 输出和阻断结论由 `requirement-review` 维护；本标准包只定义需求文档应写成什么样。

## 11. 何时应从聚合文档拆分到 modules

出现以下任一情况时，应将详细章节拆分到 `modules/`（或等价多文档）：

- 文档体量过大导致评审定位困难或反复误读。
- 多人并行编辑冲突频繁，影响交付节奏。
- 变更范围隔离困难，导致版本追踪不清晰。
- 无法稳定建立“`REQ-UC -> 页面/API/CLI -> 非功能`（按入口类型分支）”追踪关系。

## 12. 产物修订形态判定

本节用于指导需求文档写作、自检和按 Findings 修订时如何选择修改形态。它只约束被写作或审核的需求文档产物，不用于指导 Skill、模板或标准包自身的维护。

修订前应先判断缺陷属于局部产物缺口，还是需求文档结构/语义模型缺陷。

### 12.1 局部修订

若现有文档组织、语义 SSOT、入口分支追踪、核心能力定义、编号契约和主从边界仍然成立，只是存在局部措辞不精确、字段遗漏、引用缺失、示例不完整、编号回指缺口、单点事实未同步或 Finding 指向的局部证据不足，应采用局部修订。

局部修订必须直接闭合缺口，并验证不会引入新的主定义位置、并行术语、重复规则、编号分支或语义漂移。

### 12.2 文档级重构

若缺陷来自需求文档自身的结构错误、主定义归属错误、语义 SSOT 分裂、跨文档合同漂移、旧语义残留、入口分支追踪模型错误、核心能力定义退化、编号契约整体不成立，或继续局部补写会保留错误模型，应进行文档级重构。

文档级重构应先修正需求文档的正向结构、主从边界、入口追踪、核心能力定义和事实主定义位置，再补齐可验证证据、引用链、编号差集结果和必要的复核输出。不得用局部补写、重复摘要或审核说明替代主定义修正。

### 12.3 判定口径

判断标准不是改动大小，而是缺陷性质：局部产物缺口用局部修订；需求文档结构、归属或合同缺陷用文档级重构。

## 13. 完成收敛清单

- 第一章与第二章入口组织主定义仅在 `requirement-main.md`。
- 第一章已包含产品用途、目标用户、用户核心痛点、主要功能及核心场景、核心能力定义，且核心能力定义与产品总述一致。
- 阶段 0 核心能力初版收敛与最终校正已完成；已同时产出全量场景清单、候选池与取舍记录、正式核心能力清单。
- `P0/P1` 核心能力均满足标准包 `5.2` 的字段合同，并具备来源/归属编号、证据、评分、反证与证据收敛状态。
- 第二章仅保留摘要与链接，不保留可执行规则。
- 页面详细/API（若适用）/CLI（若适用）/非功能规则主定义唯一且可追踪。
- 非功能需求已覆盖默认子项；若存在范围豁免，已按 `5.3` 记录子项、范围、原因与风险口径。
- `REQ-UC-XXX`、`API-INTENT-XXX`（及 `CLI-INTENT-XXX` 若适用）编号完整且稳定。
- 正常不映射、真实 `UC-接口映射豁免` 与缺失映射已在编号差集检查中区分；真实豁免已在对应 `REQ-UC-XXX` 主定义处说明原因与必要影响。
- 编号追踪可达：存在 API/CLI 入口的场景，其 `REQ-UC-XXX` 与对应 `API-INTENT-XXX` / `CLI-INTENT-XXX` 双向可达；正常不映射场景已在编号差集中说明；稳定编号可供后续概要设计与详细设计引用。
- 入口分支追踪完整：UI 场景映射到页面；非 UI 场景可直接映射到 API/CLI；无 UI 时第二章已明确页面组织不适用；相关非功能约束可达。
- 术语、状态、口径、引用链、版本矩阵一致。
- 若本轮修订来自 Findings 或自检差距，已按第 `12` 节判定采用局部修订或文档级重构，且修订后未引入新的主定义、并行规则或语义漂移。

## 14. 最小示例

- 最小示例目录：`references/examples/unique-structure-minimal/`（从本标准包目录解析）
- 用于演示语义 SSOT 与推荐目录形态，不作为业务模板强约束。

```


## guru-template/overlay/agents-skills/requirement-review/SKILL.md

```text
---
name: requirement-review
description: 用于审核含前端（App/Web）、API-only 或 CLI-only 入口的产品需求文档。该技能仅用于需求全稿完成后的门禁审核，强制单一来源收敛；文档组织采用语义 SSOT 口径（README 导航 + requirement-main 第一章和第二章入口组织主定义），并要求先判定文档组织模式与审核口径再下结论。
---

# Requirement Review

## 目标

- 审核需求文档是否达到可进入设计或开发的质量口径。
- 只评审需求质量，不扩展到产品方向、视觉设计或实现方案。
- 基于文档证据输出问题清单和修订方案建议。
- 解决“先粗后细写作”与“单一来源完成收敛”之间的时态差异，避免前后审核口径摇摆。
- 按标准包 `5.2/7.0` 检查阶段 0 核心能力初版收敛与最终校正是否完成。
- 按标准包 `5.2` 检查核心能力是否聚焦重点/难点行为、避免退化为场景重排，并能承接概要设计与详细设计。

## 最小输入与自动补全

- 接受单个需求文档路径，或包含多份需求文档的目录路径。
- 该技能仅在需求文档全稿完成后调用，不用于阶段写作过程中的中间态审核。
- 输入是目录时，先识别主文档、模块文档、API 文档（若适用）、CLI 文档（若适用）和非功能文档。
- 候选文档不唯一时，若无法从 README、版本矩阵或用户指定路径唯一确定主文档/版本根，必须先暂停确认审核目标；只有主文档与版本根可唯一推断时，才说明识别结果与假设后继续审核。
- 识别用户是否在需求文档或审核指令中声明非功能范围豁免；优先采用已声明口径，只有声明冲突或无法判定且会影响审核结论时才暂停确认。

## 执行前置判定（输出顺序仍以 references/review-output.md 为准）

### 1) 文档组织模式

- 目标口径为语义 SSOT：README 仅导航，`requirement-main.md` 承载第一章/第二章入口组织主定义。
- 第三章起详细内容可采用模块化拆分或聚合详细文档。
- 若不满足语义 SSOT（如双主定义、边界混乱、不可追踪），不给出通过性结论；仅输出前置缺口与修订方案，不展开后续逐章门禁审核。

### 2) 审核口径

口径判定规则：
- 默认且唯一口径：门禁审核（用于整体复审/发布前/进入下一阶段）。

### 3) 核心能力目标一致性

- 核心能力目标、来源/归属、`top_level / derived` 分层、设计承接与反模式统一以标准包 `5.2` 为准。
- 若核心能力清单退化为“场景重列/场景重排/功能全量打包”，不得给出通过性结论。

## 执行规则

1. 必须先读取同级标准包主定义 `../requirement-doc-standard/references/requirement-structure-single-source.md`（从本 Skill 目录解析），以中立主定义确认组织结构与完成口径；若该文件不可用，终止并提示先安装 `requirement-doc-standard`。
2. 再判定文档组织模式与审核口径，建立章节覆盖表。
3. 先用 `rg` 与 `rg --files` 建立术语和文档索引，再逐章审核。
4. 先引用证据，再下结论；优先用 `nl -ba` 固化行号。
5. 默认按基线全量检查；对按标准包 `5.3` 或审核指令声明的非功能豁免项，只检查豁免清晰度与风险声明。
6. API/CLI 适用性按标准包 `requirement-structure-single-source.md` 的“API/CLI 适用标准”判定。
7. 必须按标准包 `5.2/7.0` 核查核心能力定义是否存在，以及阶段 0 三产物、字段合同、优先级、证据状态、设计承接、`top_level / derived` 分层与反模式是否满足要求；本技能不重复维护字段级判定规则。
8. 必须核查 `confirmation_status` 与 `open_questions` 是否满足进入概要设计的条件；`P0/P1` 核心能力若仍为 `ai_drafted`，或存在会改变范围/验收口径的高风险 `open_questions`，不得判定“可进入概要设计”；`evidence_ready` 可在假设明确且无高风险待确认问题时放行。
9. 本技能只判断核心能力是否达到进入概要设计的文档条件，不替代用户完成业务确认，不得把核心能力状态写成 `user_confirmed` 或 `user_confirmed_with_edits`。
10. 核心能力反模式命中后的严重度按 `references/review-baseline.md` 的严重度规则判定，不机械把所有 P2 视为阻断项。
11. 必须核查 API/CLI 适用性判定依据是否明确（适用/不适用 + 理由）且引用标准包“API/CLI 适用标准”；缺失判定依据按 `references/review-baseline.md` 的严重度规则赋级。
12. API/CLI（若适用）必查：按标准包第 `6` 章与 `6.1` 核查入口分支追踪、业务意图回指、复用/拆分条件与差集分类；API 同时按标准包第 `5` 章检查 `必要步骤` 覆盖与契约单一来源，CLI 同时检查命令语义、参数、退出码契约及其与 API 文档的解耦关系。
13. 编号契约必查：按标准包第 `6` 章与 `6.1` 核查 `REQ-UC-XXX`、`API-INTENT-XXX`（若适用）、`CLI-INTENT-XXX`（若适用）的完整性、稳定性、入口分支追踪与差集结果。
14. 编号差集分类、真实 `UC-接口映射豁免` 的声明主体统一引用标准包第 `6` 章；缺失映射赋级按 `references/review-baseline.md` 的严重度规则处理；API/CLI 整体不适用或 UI-only 正常不映射不得按豁免缺失处理。
15. 跨文档必查：单向维护、主从一致性、版本矩阵与引用链一致性。
16. 对“重复定义”按 `references/review-baseline.md` 的严重度规则判定严重度与阻断口径。
17. “第一章/第二章是否缺失”按文档集判定，不按 README 单文件判定。
18. 阻断与放行结论按 `references/review-baseline.md` 的严重度规则输出。
19. 若存在真实 `UC-接口映射豁免` 但缺少豁免原因或必要影响说明，按 `references/review-baseline.md` 的严重度规则赋级；API/CLI 整体不适用或 UI-only 正常不映射不得按豁免缺失处理。
20. 输出 Finding 的建议或修订方案时，必须按标准包第 `12` 章区分局部产物缺口与需求文档结构/语义模型缺陷；结构、归属或合同缺陷不得建议用局部补写保留错误模型。

## 审核流程

1. 开始评审前读取 `references/review-baseline.md`。
2. 识别文档结构，记录：文档组织模式、审核口径、第一章主定义位置、第二章入口组织主定义位置、章节映射与豁免清单；若语义 SSOT 前置不满足，输出前置缺口后停止。
3. 先审核“阶段 0：核心能力初版收敛与最终校正”与第一章核心能力定义，再按产品总述、入口组织结构（有 UI 时包含页面组织结构）、页面详细描述（若适用）、服务端 API（若适用）、CLI Command（若适用）、非功能需求逐章审核。
4. 执行一致性、可测试性、适度性、实用性交叉检查。
5. 输出 findings（按 P1/P2/P3）与必要结论；仅在用户要求或复杂文档需要说明覆盖情况时输出审核矩阵。
6. 在总结中明确：是否可进入下一阶段，以及前提条件。

## 输出要求

- 输出分支、字段与顺序以 `references/review-output.md` 为唯一主定义，本文件不再重复维护第二份字段清单。
- 若语义 SSOT 前置不满足，按 `references/review-output.md` 的“前置失败输出”仅输出前置缺口与修订方案。
- 若语义 SSOT 前置通过，按 `references/review-output.md` 的“常规门禁输出”输出 Findings、必要结构概况与总结；每条 Finding 包含严重度、位置、问题、建议。
- 若模板与其他说明冲突，以 `references/review-output.md` 为准。

## 命令建议

- 用 `rg` 搜索功能名、入口名、页面名（若适用）、API/CLI 名、命令名和关键术语。
- 用 `rg --files` 建立目录型文档清单。
- 用 `nl -ba` 和 `sed -n` 抽取可引用证据。

## 参考资料

- 需求文档体系中立主定义：同级标准包 `../requirement-doc-standard/references/requirement-structure-single-source.md`（从本 Skill 目录解析）
- 审核基线与详细检查矩阵：`references/review-baseline.md`
- 输出模板与复审闭环：`references/review-output.md`
- 最小示例模板（共享）：`../requirement-doc-standard/references/examples/unique-structure-minimal/`（从本 Skill 目录解析）

```
