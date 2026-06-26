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
- Batch confirmation: allowed only when the current user turn explicitly confirms each item or explicitly covers the listed OQ / decision ids.
- Unanswered items remain `open_questions`.
- Vague acknowledgements such as `继续`, `好`, or `按推荐` without clear OQ / decision coverage are not batch confirmation; fall back to one `next_question`.

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

Define `evidence_ready` as evidence-complete but not user-confirmed. It can support drafting and review, but it cannot be promoted to `user_confirmed*` during `continue` unless the current user turn confirms the specific decision. A historical `user_quote` or existing `user_confirmed*` record is valid audit evidence for the decision it already confirmed, but it is not current-turn approval for new state transitions, OQ deletion, overview/detail, or `task.py start`.

### 5. Gate Structure Checks

Enhance `_brainstorm_evidence_problems` and requirements checks:

- Positive `Product decisions confirmed` means the value is not a negative value (`none`, `无`, `没有`, `not triggered`, etc.) and contains at least one `DEC-` item or natural-language confirmed decision.
- Positive `Product decisions confirmed` requires `user_quote` or `confirmed_ref` in the same decision item or adjacent indented block.
- Multiple OQ means two or more `OQ-` entries in `Open product/scope/risk questions`.
- Multiple OQ requires a single `next_question` / `next_action`; all other OQ entries must remain open.
- If `prd` contains `confirmation_status=user_confirmed*`, require `user_quote` or `confirmed_ref` in the same decision item or its direct indented child block.
- If an `evidence_ready` decision is upgraded to `user_confirmed*`, require current-turn confirmation evidence rather than accepting the prior evidence-ready record.
- Batch confirmation requires each confirmed decision to record the covered OQ / decision id; vague batch language must fail or route back to one `next_question`.
- If a full `Question loop log` is absent but minimum confirmation hints exist, pass the structural gate and leave review-level guidance to prefer the richer format.

This remains a structural gate. Semantic judgment stays in `requirement-review`.

### 6. Continue Boundary

Update `trellis-continue` guidance:

- `continue` can do reversible evidence work.
- If high-risk OQ or `ai_drafted` P0/P1 remains, next step is one question.
- Existing historical confirmation evidence cannot be reused as current-turn approval for a new state transition or to bypass remaining high-risk OQ.
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
- F-008: removed orphan `confirmed_by` from hard evidence requirements.
- F-009: added `evidence_ready` definition and aligned `REQ-006` with BHV-007.
- F-010: defined how one batch user quote may cover multiple decisions.
- F-011: added detail-design blocking to `REQ-006`.
- F-012: added explicit manual review checklist for Markdown skill behavior.
- F-013: replaced vague "nearby" with same decision item or direct child block.
- F-014: defined current-turn confirmation and blocked stale confirmation reuse during `continue`.
- F-015: tightened batch confirmation to require explicit OQ / decision id coverage and vague-batch fallback to one question.
- F-016: added gate/test requirements for `evidence_ready` not being silently upgraded and for `user_confirmed*` without confirmation evidence.
