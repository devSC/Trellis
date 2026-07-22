# Break the Loop - Post-Implementation Failure Retrospective

Use this Skill after a user- or QA-reported post-implementation failure to explain the false green, prove the repair, and prevent recurrence. It is a retrospective helper inside the active Trellis/Guru repair continuation; it does not create a second lifecycle, own task state, classify product behavior without evidence, or authorize writes.

## Ownership And Preconditions

- `guru-bug-fast-path`/workflow owns continuation, Review/workflow owns final routing, `ClosureSpec` owns currentness and durable reconciliation. This helper drafts/validates retrospective evidence only.
- Before any analysis or edit, preserve `runtime_acceptance_failure` with original `acceptance_id`, active task/current baseline, environment, steps, expected/actual, and privacy-safe refs. If missing, return `PROCESS_DEFECT: runtime_failure_row_missing` and only its recording action.
- The append stales prior resolution. Before affinity/classification/repair, require fresh CH-01 `AcceptanceResolution` selecting that failure with both open lists empty; missing/stale/projected/blocked means process correction only.
- Confirm root cause by reproduction/trace/log/failing check, not hypothesis. Compare current Requirements, Overview, Detail/packet, implementation, prior tests/Review, and runtime evidence; packet-local green cannot dismiss runtime contradiction.

## Canonical Evidence Input And Ownership

Consume the same complete CH-01 object used by Review/Workflow/Finish/repair: `baseline_binding`, ledger+reconciliation snapshot refs, both open lists, row results, selected+blocking refs, task result, blocking IDs, and `next_probe`. Never project it, select a row, reconcile/mutate storage, or authorize a probe. `ClosureSpec` owns full replay/currentness/transitions/correlation/probe; this helper returns only `FailureRetrospectiveDraft`, while `guru-bug-fast-path` owns the validated, durably bound final record.

## Same-Goal Affinity

Reuse fast-path affinity: `same_goal=true` only for the same BHV/AC/outcome with `new_product_behavior`, `permission_or_data_expansion`, `external_contract_change`, and `material_scope_change` all false. File/snapshot/symptom/wording/approach changes do not change the goal. Unbound task/baseline/ID is authority-blocked; different behavior or any true indicator routes `REQ_BLOCKER`/material change to Requirements.

## Five-Class Maximum Rollback

Choose the earliest evidence-proven owner, never the shortest desired route.

| Defect class | Maximum rollback | Required refresh | Preserved by default |
| --- | --- | --- | --- |
| `IMPLEMENT_DEFECT` | Phase 2 implementation/check | Affected source/tests, Slice Review, Integration, and runtime receipt | Current Requirements, Overview, Detail, and independently bound sibling receipts |
| `PROCESS_DEFECT` | Current evidence/process; Phase 1 Detail only when a packet or digest-bearing plan must change | Affected mutable evidence/fixture/execution step; changed Detail and its downstream only when the plan changes | Unchanged planning and independently bound receipts |
| `DETAIL_DEFECT` | Phase 1 Detail | Affected Detail, packet/plan, Detail Review/confirmation, affected Slices, Integration, and runtime receipt | Requirements and Overview |
| `OVERVIEW_DEFECT` | Phase 1 Overview plus affected Detail | Overview Review and affected Detail/downstream evidence in order | Requirements |
| `REQ_BLOCKER` or material requirement change | Phase 1 Requirements affected Full chain | Affected Requirements through Overview, Detail, implementation, Integration, and runtime acceptance | Only evidence proven independent by current bindings |

Implementation defects never restart planning; upstream defects are repaired by their owner first. Multiple classes use the earliest owner plus dependent refresh.

### Environment/Fixture Discriminator

Environment/fixture-only is not a sixth class. Wrong packet/plan/fixture contract/check is `PROCESS_DEFECT`, returning to Detail only if that artifact changes. If plan+implementation are correct and only target setup/data/fixture instance is wrong, stay at verification and refresh that evidence/probe without product changes. Unproven means request evidence.

## Selective Evidence Refresh

Draft an exact evidence plan from the actual binding changes:

1. Compare target bytes, invariants, Requirements/Detail inputs, declared checks, policy/provider, and supervisor digest for every affected receipt.
2. Invalidate and reverify receipts with any changed binding. Refresh affected union-snapshot Integration evidence and the runtime receipt after implementation or planning bytes change.
3. Preserve a sibling receipt only when all binding components remain equal and it is independent of the affected acceptance path.
4. Treat v1 receipts, missing binding data, or unproven independence as affected. Honor any current digest/snapshot Gate that marks evidence stale; never describe stale evidence as current.

## Required Five-Field Retrospective

Every field must bind to the same `acceptance_id`, preserved failure row, and repaired baseline.

The canonical field names are `direct_cause`, `earliest_missed_gate`, `false_green_reason`, `falsifiable_regression`, and `prevention_disposition`. The disposition is an exact XOR of `writeback_required` and `no_writeback_required`.

| Field | Required evidence |
| --- | --- |
| `direct_cause` | Confirmed causal control point and proof, not symptom/category. Optional categories: missing spec, cross-layer loss, stale propagation, coverage gap, implicit assumption. For repeats, explain each failed attempt. |
| `earliest_missed_gate` | Earliest Requirement/Overview/Detail/Implementation/Test/Review/Process Gate plus exact missing contract/check/decision, not merely the reporting Gate. |
| `false_green_reason` | Trace actual prior inputs/assertions through the source-to-sink gap; “coverage incomplete” alone fails. |
| `falsifiable_regression` | Accepted-path deterministic check/probe with old-wrong FAIL and repaired PASS evidence. Helper-only or old-wrong green routes `DETAIL_DEFECT`. |
| `prevention_disposition` | Exactly one complete branch below. |

- `writeback_required`: allowed canonical Skill/workflow/spec owner, exact prevented recurrence, required consumer parity, focused validation, and proof no forbidden runtime/script edit is needed.
- `no_writeback_required`: explicit no-change reason, current owning-contract refs, and proof the new regression/probe closes the uncovered path.
- TODO/empty claim, both/neither branch, or invented writeback returns `PROCESS_DEFECT: prevention_disposition_incomplete`. Out-of-scope writeback is a scope blocker, never authority.

## Output Contract

Produce one evidence-backed draft, never a `FailureRetrospectiveRecord`, append acknowledgment, or probe authorization:

```markdown
## Bug Analysis: [short description]
acceptance_id: <original BHV/AC/invariant>
failure_row: <runtime_acceptance_failure ref>
affinity: same_goal | material_change | unproven
defect_class: IMPLEMENT_DEFECT | PROCESS_DEFECT | DETAIL_DEFECT | OVERVIEW_DEFECT | REQ_BLOCKER
maximum_rollback: <phase/owner>
direct_cause: <cause + proof>
earliest_missed_gate: <Gate + missed contract + refs>
false_green_reason: <prior checks + source-to-sink gap + refs>
falsifiable_regression: <check; old FAIL ref; repaired PASS ref>
prevention_disposition: <one complete branch>
evidence_refresh: <invalidate/reverify, preserve, Integration, runtime>
Draft: complete | incomplete
blocking_gap: <none or one exact gap>
```

The selected prevention branch must be complete; omit the other. `Draft: complete` means field validation only and never `retrospective_state=complete`.

## Completion Boundary

- Draft completeness is five fields plus one prevention branch; it closes no attempt. Final completion requires legal current-baseline pending row, prepared-event acknowledgment before evidence append, accepted/uniquely reconciled append ref, canonical record/ref, and full-replay acknowledgment of exact `record-bound` chain. Accepted alone, open, rejected, or ambiguous stays blocked.
- Repair completion also requires fresh complete CH-01 with empty blockers, current affected Slice/Integration evidence, and current repaired-baseline `runtime_acceptance_pass`. Workflow alone reports canonical `next_probe`; this helper never chooses/reissues it. Focused test, Review, `implementation_verified`, or old pass is insufficient.
- Keep broader similar issues as non-blocking follow-ups unless evidence shows they affect the current acceptance path. Do not turn the retrospective into an open-ended repository audit.

## Archived Task And No-Script Boundary

- Archived work uses an authorized linked repair task carrying original `acceptance_id`, digests, receipts, and new-failure ref; never claim in-place reopen/inheritance, and obey current Gates.
- Task/authority/spec/sync/Git/archive/finish actions require their own authority. Do not edit Trellis/Guru scripts, verify/hooks/apply, packaged script mirrors, Python/shell, or CLI TS; request separate scope. Markdown cannot provide executable reopen, automatic inheritance/digest invalidation, or script-level archive enforcement.

## Core Principle

The value of a repair is not only that the symptom disappears. The same accepted path must fail on the old behavior, pass on the repaired baseline, explain the prior false green, and leave one evidence-backed prevention disposition without inventing unauthorized work.
