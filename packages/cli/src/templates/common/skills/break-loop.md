# Break the Loop - Post-Implementation Failure Retrospective

Use this Skill after a user- or QA-reported post-implementation failure to explain the false green, prove the repair, and prevent recurrence. It is a retrospective helper inside the active Trellis/Guru repair continuation; it does not create a second lifecycle, own task state, classify product behavior without evidence, or authorize writes.

## Ownership And Preconditions

- `guru-bug-fast-path` or the active workflow owns repair-continuation state. The live Review/workflow contract owns the final defect route. This Skill drafts and validates retrospective evidence only.
- Before analysis, diagnosis, source edits, or test edits, the current task must preserve an append-only `runtime_acceptance_failure` row bound to the original `acceptance_id`, active task, baseline, target environment, steps, expected result, actual result, and privacy-safe evidence references.
- If that row is missing, return `PROCESS_DEFECT: runtime_failure_row_missing` with the single next action to record it. Do not reconstruct it after the repair.
- Direct root cause must be confirmed by a minimal reproduction, trace, log, or failing check before the retrospective can call the repair proven. A plausible hypothesis is not a root cause.
- Read the confirmed Requirements, Overview, Detail/packet, current implementation, prior tests/Review, and runtime evidence. Runtime evidence that contradicts an internally green packet cannot be dismissed as packet-external.

## Same-Goal Affinity

Reuse the same affinity decision as `guru-bug-fast-path`:

- `same_goal=true` only when the failure maps to the same BHV/AC or accepted user outcome and all four indicators are false: `new_product_behavior`, `permission_or_data_expansion`, `external_contract_change`, and `material_scope_change`.
- File changes, snapshot changes, a moved symptom, different error wording, or a new implementation approach do not create a new acceptance goal.
- An unbound task, baseline, or `acceptance_id` is authority-blocked until live evidence resolves it.
- If the BHV/AC differs or any change indicator is true, route `REQ_BLOCKER` or material requirement change to the affected Requirements chain. Do not relabel new product behavior as a same-goal repair.

## Five-Class Maximum Rollback

Use evidence to identify the earliest owning defect. Do not choose a class merely to obtain a shorter route.

| Defect class | Maximum rollback | Required refresh | Preserved by default |
| --- | --- | --- | --- |
| `IMPLEMENT_DEFECT` | Phase 2 implementation/check | Affected source/tests, Slice Review, Integration, and runtime receipt | Current Requirements, Overview, Detail, and independently bound sibling receipts |
| `PROCESS_DEFECT` | Current evidence/process; Phase 1 Detail only when a packet or digest-bearing plan must change | Affected mutable evidence/fixture/execution step; changed Detail and its downstream only when the plan changes | Unchanged planning and independently bound receipts |
| `DETAIL_DEFECT` | Phase 1 Detail | Affected Detail, packet/plan, Detail Review/confirmation, affected Slices, Integration, and runtime receipt | Requirements and Overview |
| `OVERVIEW_DEFECT` | Phase 1 Overview plus affected Detail | Overview Review and affected Detail/downstream evidence in order | Requirements |
| `REQ_BLOCKER` or material requirement change | Phase 1 Requirements affected Full chain | Affected Requirements through Overview, Detail, implementation, Integration, and runtime acceptance | Only evidence proven independent by current bindings |

An implementation defect never restarts Requirements, Overview, or Detail. An upstream planning defect must be repaired by its owner before downstream code is changed to conform. When findings exist in more than one class, select the earliest upstream owner and list dependent downstream refresh.

### Environment/Fixture Discriminator

Environment/fixture-only is a verification disposition, not a sixth defect class.

- A wrong or incomplete confirmed packet, digest-bearing plan, fixture contract, or declared check is `PROCESS_DEFECT`. Return to Detail only if that packet or plan must actually change.
- When packet/plan and implementation are correct and only target-environment configuration, test data, execution setup, or the runtime fixture instance is wrong, remain at the current verification step. Refresh only environment/fixture evidence and the affected runtime probe.
- Do not change product Requirements, Overview, Detail, or implementation to hide an environment-only failure. If the discriminator is unproven, request the missing evidence instead of choosing the environment route.

## Selective Evidence Refresh

Draft an exact evidence plan from the actual binding changes:

1. Compare target bytes, invariants, Requirements/Detail inputs, declared checks, policy/provider, and supervisor digest for every affected receipt.
2. Invalidate and reverify receipts with any changed binding. Refresh affected union-snapshot Integration evidence and the runtime receipt after implementation or planning bytes change.
3. Preserve a sibling receipt only when all binding components remain equal and it is independent of the affected acceptance path.
4. Treat v1 receipts, missing binding data, or unproven independence as affected. Honor any current digest/snapshot Gate that marks evidence stale; never describe stale evidence as current.

## Required Five-Field Retrospective

Every field must bind to the same `acceptance_id`, preserved failure row, and repaired baseline.

### 1. Direct Cause

Record the concrete control point that produced the failure and the evidence proving it. Categories can help organize the explanation, but a category is not the cause:

| Category | Typical signal |
| --- | --- |
| **A. Missing Spec** | Required behavior or boundary was never documented |
| **B. Cross-Layer Contract** | Data or state was lost or changed between source and user-visible sink |
| **C. Change Propagation Failure** | One owner changed while a dependent consumer remained stale |
| **D. Test Coverage Gap** | Local checks passed without exercising the failing acceptance path |
| **E. Implicit Assumption** | Behavior depended on an undocumented format, state, timing, or authority assumption |

For repeated attempts, record why each failed: symptom-only repair, incomplete scope, tool limitation, stale evidence, or incorrect mental model.

### 2. Earliest Missed Gate

Name the earliest Requirement, Overview, Detail, Implementation, Test, Review, or Process Gate that should have rejected the known-wrong behavior. Cite the exact missing contract, check, or evidence decision. Do not name only the final Gate that happened to report the symptom.

### 3. False-Green Reason

Explain why the previous tests and Review stayed green. Trace the gap from their actual inputs and assertions to the user-visible failure. A generic statement such as "coverage was incomplete" is insufficient.

### 4. Falsifiable Regression

Record a deterministic check or runtime probe that exercises the accepted source-to-sink path. Include evidence that it fails on the old wrong implementation and passes on the repair. A helper-only positive assertion, a test that never reaches the old failure, or a probe that stays green on the known-wrong behavior is incomplete and routes `DETAIL_DEFECT` so the falsifiability contract and affected downstream evidence are repaired.

### 5. Prevention Disposition - Exact XOR

Choose exactly one complete branch. Never include both and never omit both.

`writeback_required` requires:

- one allowed canonical Skill/workflow/spec source owner;
- the exact recurrence path the writeback prevents;
- required source/consumer parity, if any;
- focused validation evidence; and
- confirmation that the writeback does not require a forbidden script/runtime edit.

`no_writeback_required` requires:

- an explicit reason that a new source-contract change is unnecessary;
- evidence references showing which current contract already owns the rule; and
- evidence that the new falsifiable regression or probe closes the previously uncovered path.

A TODO, an empty "no writeback needed" assertion, both branches, neither branch, or an invented unnecessary writeback returns `PROCESS_DEFECT: prevention_disposition_incomplete` and keeps the retrospective incomplete. A required writeback outside current allowed paths is a scope blocker, not write authority.

## Output Contract

Produce one evidence-backed record in this shape:

```markdown
## Bug Analysis: [short description]

- **Acceptance ID**: [original BHV/AC/invariant]
- **Failure Row**: [append-only runtime_acceptance_failure reference]
- **Task Affinity**: same_goal | material_change | unproven
- **Defect Class**: IMPLEMENT_DEFECT | PROCESS_DEFECT | DETAIL_DEFECT | OVERVIEW_DEFECT | REQ_BLOCKER
- **Maximum Rollback**: [exact phase/owner]

### 1. Direct Cause
- **Category**: [A/B/C/D/E]
- **Confirmed Cause**: [control point and causal chain]
- **Evidence**: [reproduction, trace, log, or failing check references]

### 2. Earliest Missed Gate
- **Gate**: [Requirement/Overview/Detail/Implementation/Test/Review/Process]
- **Missed Contract**: [exact contract or check]
- **Evidence**: [references]

### 3. False-Green Reason
- **Prior Inputs/Assertions**: [what was actually checked]
- **Why They Missed The Failure**: [source-to-sink gap]
- **Evidence**: [prior test/Review references]

### 4. Falsifiable Regression
- **Check Or Probe**: [exact command/test/runtime steps]
- **Known-Wrong Result**: FAIL [evidence]
- **Repaired Result**: PASS [evidence]

### 5. Prevention Disposition
- **Branch**: writeback_required | no_writeback_required
- **Owner Or Existing Contract**: [allowed owner/path]
- **Action Or No-Writeback Reason**: [exact prevention or evidence-backed reason]
- **Evidence And Validation**: [references]

### Evidence Refresh
- **Invalidate/Reverify**: [exact receipt ids and reasons]
- **Preserve**: [exact sibling receipt ids and equal bindings]
- **Integration**: [refresh requirement/result]
- **Runtime Reprobe**: [original probe and current result]

### Closure
- **Retrospective**: complete | incomplete
- **Repair Completion Eligible**: yes | no
- **Blocking Gap**: [none or one exact gap]
```

The selected prevention branch must contain its complete fields even though the compact output uses one shared shape. Do not add the unselected branch.

## Completion Boundary

- Retrospective completion requires all five fields and exactly one valid prevention branch.
- Repair completion additionally requires current affected implementation/Slice/Integration evidence and a current `runtime_acceptance_pass` from the original target-environment probe on the repaired baseline. A focused test, clean Review, `implementation_verified`, or an older runtime pass is not enough.
- Keep broader similar issues as non-blocking follow-ups unless evidence shows they affect the current acceptance path. Do not turn the retrospective into an open-ended repository audit.

## Archived Task And No-Script Boundary

- For an archived original task, do not claim in-place reopen or machine baseline inheritance. With lifecycle authorization, use a linked repair task/child that references the original `acceptance_id`, artifact digests, receipts, and new failure evidence. Follow current Gates honestly, including any Full planning they still require.
- Creating a task/child, changing task authority, updating a spec, syncing a template, committing, pushing, merging, archiving, or running finish-work requires its own current workflow authority. This retrospective does not grant it.
- Do not modify `.trellis/scripts/**`, `task.py`, `guru_gate.py`, Guru verify/hooks/apply, packaged script mirrors, Python/shell files, or CLI TypeScript runtime to implement this contract. If prevention requires such a change, stop and request a separately scoped task and explicit authorization.
- This Markdown behavior cannot provide executable reopen, automatic receipt inheritance, digest-graph invalidation, or script-level archive enforcement. State those limitations rather than promising them.

## Core Principle

The value of a repair is not only that the symptom disappears. The same accepted path must fail on the old behavior, pass on the repaired baseline, explain the prior false green, and leave one evidence-backed prevention disposition without inventing unauthorized work.
