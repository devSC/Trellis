---
name: guru-bug-fast-path
description: "Use during Trellis/Guru Bug repair when the user explicitly invokes guru-bug-fast-path, a post-implementation runtime failure is bound to the same acceptance goal, the same goal records two implementation or semantic failures, or an additional semantic reviewer not required by the active Gate is about to run for the same snapshot. Preserve the runtime failure before repair, route the earliest owning defect to the maximum necessary rollback, refresh only affected evidence, require a complete retrospective and runtime reprobe, then complete with current evidence or stop with one blocker. Do not use for a first ordinary pre-acceptance failure, mandatory Gate reviewers, or a standalone retrospective without an active repair."
---

# Guru Bug Fast Path

Stop repair-review-retry loops without weakening the active workflow.
## Guardrails
- This is a behavioral guardrail, not a Gate or runtime controller. It acts only when control returns at a step boundary; never interrupt a running worker or supervisor.
- The live task route and its Requirements, Detail, Review, Receipt, Commit, and Integration Gates remain authoritative.
- Preserve user changes. Activation alone never commits, pushes, merges, archives, installs Guru, runs `finish-work`, automatically runs `trellis-break-loop`, updates Specs, creates a task, or changes task authority. A post-implementation runtime failure still requires the equivalent retrospective contract below before repair completion.
- Never change tests, verifiers, reviewer conclusions, scoring, provider policy, or runtime code to obtain a pass.
## Activation
- Explicit invocation activates immediately at the next step boundary.
- A current post-implementation `runtime_acceptance_failure` bound to an active task and the same acceptance goal activates repair continuation immediately. This is distinct from a first ordinary implementation, test, or Review failure before runtime acceptance.
- Increment `same_goal_failures` only for an implementation failure or blocking semantic Review failure against the unchanged goal, including a mandatory Gate Review blocker. Provider, malformed-output, requirement, and authority failures use their own routes.
- Auto-activate when `same_goal_failures=2/2`. A code snapshot or allowed write-scope change does not reset it; only a user-confirmed change to the acceptance target, or `complete`, ends the count.
- Before `activation_reason=redundant_review`, prove the reviewer is additional and not required by the active Gate. Mandatory Gate reviewers never trigger redundant-review activation or consume the additional-review budget, but their blocking semantic outcomes still increment `same_goal_failures`.
- This Markdown pilot observes only evidence available when control returns. Seed all applicable counters from receipts, logs, Review records, or visible conversation history; never invent a missing attempt or claim to interrupt an in-flight supervisor.
- Do not activate for the first ordinary pre-acceptance failure.

## Failure-First Continuation Intake
1. Before diagnosis, source edits, test edits, or repair Review, append the reported result as `runtime_acceptance_failure` through the current task's authorized append-only `verification-evidence.jsonl` path. Bind it to the original `acceptance_id`, active task, current baseline, target environment, steps, expected result, actual result, and privacy-safe evidence references. Preserve earlier pending, pass, and failure rows; never summarize the failure only after the repair.
2. If the failure row cannot be written through an authorized current workflow, set `status=evidence_required`, `phase=blocked`, `code_writes_allowed=false`, `blocking_issue=runtime_failure_row_missing`, and one `next_action` that records it. Do not diagnose or repair first.
3. Freeze the original BHV/AC and user-visible outcome. `task_affinity=same_goal` only when `same_bhv_or_ac=true` and all four indicators are false: `new_product_behavior`, `permission_or_data_expansion`, `external_contract_change`, and `material_scope_change`. A changed file, code snapshot, symptom location, error text, or implementation approach does not change goal affinity.
4. If the task, baseline, or `acceptance_id` cannot be bound to live evidence, use the existing `authority_blocked` route. If affinity fails or any change indicator is true, classify the boundary as `REQ_BLOCKER` or material requirement change and return to the affected Requirements chain; do not disguise it as repair continuation.
5. Continue in place only for an active same-goal task. For an archived task, use the linked-repair boundary below rather than representing the historical task as active.

## State
Carry this block across turns and compactions:
```text
[FAST-PATH-STATE]
goal=<one acceptance target>
acceptance_id=<original BHV/AC/invariant id>
original_user_outcome=<frozen accepted result>
task_affinity=same_goal|material_change|unproven
runtime_failure_ref=<append-only evidence row ref or missing>
status=active|requirements_blocked|root_cause_blocked|evidence_required|repair_blocked|review_output_blocked|external_blocked|authority_blocked|complete
phase=freeze|diagnose|requirements_repair|repair|review|blocked|complete
route_class=requirement|root_cause|implementation|malformed_review|external|authority
defect_class=unclassified|IMPLEMENT_DEFECT|PROCESS_DEFECT|DETAIL_DEFECT|OVERVIEW_DEFECT|REQ_BLOCKER
maximum_rollback=<current verification step|Phase 2 implementation/check|Phase 1 Detail|Phase 1 Overview plus affected Detail|Phase 1 Requirements affected chain>
environment_fixture_disposition=not_applicable|process_contract_defect|environment_fixture_only
evidence_refresh_plan=<exact invalidate, preserve, reverify, Integration, and runtime ids with reasons>
activation_reason=explicit|runtime_acceptance_failure|repeated_failure|redundant_review
snapshot=<current digest or precise diff description>
reviewed_snapshot=<snapshot covered by the latest semantic Review or none>
allowed_paths=<bounded write scope>
forbidden_paths=<forbidden scope>
code_writes_allowed=false|diagnostics_only|repair
same_goal_failures=0/2
last_failure_class=<none|implementation|semantic>
blocker_id=<stable id derived from blocker_fingerprint>
blocker_fingerprint=<violated invariant|root-cause family|affected surface>
blocker_generation=1/2
resolved_blockers=<none or ordered blocker ids with resolution evidence>
pending_blockers=<ordered non-active implementation blockers with fingerprint, severity, Gate order, reviewed snapshot, and evidence>
deferred_implementation_findings=<ordered untouched mixed-Review evidence awaiting requirement/authority resolution>
repair_slices=1/2
root_cause_status=unknown|hypothesis|confirmed
root_cause=<confirmed cause or unknown>
root_cause_evidence=<reproduction, logs, trace, or failing test>
evidence_epoch=1/2
diagnostic_actions=0/2
repair_attempts_for_blocker=0/1
mandatory_review_runs=<live Gate evidence; not budgeted by this Skill>
additional_review_cycles=0/1
malformed_review_retries=0/1
provider_attempts=0/2
requirement_confirmation_rounds=0/1
full_regression_runs=0/1
retrospective_state=missing|incomplete|complete
prevention_disposition=missing|writeback_required|no_writeback_required
user_extra_attempts=0/1
user_extra_kind=<none|diagnostic|repair_cycle|review|provider>
scope_expansions=0
blocking_issue=<one active blocker or exact generation-limit reason>
follow_ups=<non-blocking findings only>
next_action=<one bounded action>
```
## Blocker Identity And Generations
1. Seed `blocker_generation=1/2` when the first current blocker is identified. Derive `blocker_id` from a normalized `blocker_fingerprint` containing the violated invariant, root-cause family, and affected surface; record the evidence used for each component.
2. Default to the same blocker. Findings with the same violated invariant and root-cause family are the same blocker even when they move or propagate to another affected surface. A changed line number, severity wording, snapshot, symptom restatement, Review phrasing, or expanded `allowed_paths` does not create a new identity. Missing or ambiguous identity evidence also stays on the current generation.
3. Advance from generation 1 to 2 only when current evidence proves the previous blocker resolved, proves a materially different violated invariant or materially different root-cause family for the new blocker within the unchanged goal and scope, and proves the new finding is not propagation or restatement of the prior blocker. Record affected surface in `blocker_fingerprint`, but affected-surface difference alone is never sufficient for a new generation. Append the prior id, fingerprint, resolved snapshot, and resolution evidence to `resolved_blockers`; never erase its diagnosis, repair, or Review history.
4. On that one allowed transition, reset only blocker-local fields: `root_cause_status`, `root_cause`, `root_cause_evidence`, `evidence_epoch=1/2`, `diagnostic_actions=0/2`, and `repair_attempts_for_blocker=0/1`. Preserve `same_goal_failures`, `repair_slices`, all mandatory/additional/malformed Review evidence and counters, `provider_attempts`, `requirement_confirmation_rounds`, `full_regression_runs`, `user_extra_attempts`, `user_extra_kind`, `scope_expansions`, prior snapshots, and all valid evidence.
5. If the same blocker persists after its bounded repair, end as `repair_blocked`; never relabel it as a new generation or stack another patch. If two independent blockers are already recorded and a third appears, fail closed as `repair_blocked` with `blocking_issue=blocker_generation_limit_exhausted: two independent blockers already consumed for unchanged goal/scope`.
6. `repair_slices` describes independently owned execution slices already proved by the active plan. It neither grants repair attempts nor counts blocker generations; changing it never resets or advances blocker state.
7. Migrate legacy state conservatively. When `blocker_id`, `blocker_fingerprint`, or `blocker_generation` is absent, seed generation 1 from the unchanged goal/scope plus the legacy `root_cause` and `blocking_issue`, and retain the original state as migration evidence. Map legacy `code_repair_attempts=0/1` to `repair_attempts_for_blocker=0/1`; map `code_repair_attempts=1/1` to `repair_attempts_for_blocker=1/1`, leaving no base repair for that blocker and never inferring resolution. Preserve an already-consumed `user_extra_attempts=1/1` and its `user_extra_kind` exactly; migration and generation transition never reset them. Ambiguity means the same generation, `resolved_blockers` stays empty unless current evidence proves resolution, and `pending_blockers` is populated only from visible blocking evidence.
8. After requirement and authority routing has completed, normalize every implementation blocking finding from one Review to a fingerprint and merge same-identity findings into one row while preserving all evidence. Select one active blocker deterministically by descending severity, then live Gate order, then strongest current evidence, then stable Review order. Store every other implementation blocker in ordered `pending_blockers`; never place a blocking finding in `follow_ups`.
9. A queued row may be promoted, classified as independent, or counted against the generation budget only when its semantic evidence is current: its row-level reviewed snapshot must match `reviewed_snapshot`, and that Review must cover the current `snapshot` and live Gate requirements. Stale, unreviewed, or Gate-inapplicable queue evidence cannot advance state; set `status=evidence_required`, `phase=blocked`, `code_writes_allowed=false`, `blocking_issue=pending_blocker_current_semantic_evidence_required`, and one `next_action` that obtains current semantic evidence for that row. Preserve the row and consume no implementation generation, diagnosis, or repair budget.
10. Only after every queued implementation identity has current semantic evidence, compare the independent identities in `pending_blockers` with the remaining generation budget. If the queue exceeds the remaining budget, fail closed as `repair_blocked` with `blocking_issue=blocker_generation_limit_exhausted: pending independent blockers exceed remaining generation budget`, and preserve the complete ordered queue and its evidence.
11. After the active blocker resolves, re-normalize the first current pending row against the just-resolved active identity before any promotion. If it is the same identity and its current evidence is already covered by the resolution snapshot and does not contradict that resolution, merge the evidence into the resolved record and remove the queue row without consuming a generation. Newer current evidence that affirmatively confirms resolution follows the same merge path. If current or newer evidence contradicts the resolution, merge that evidence back into the active blocker, remove only the duplicate queue row after the evidence transfer, and end as `repair_blocked` with `blocking_issue=same_blocker_persists_or_reopened`; never open generation 2. Newer evidence that neither confirms nor contradicts resolution remains `evidence_required`. Never silently discard a queued row or its evidence.
12. Promote a current, materially independent pending row only through the identity and generation rules above, and remove it from `pending_blockers` only when it becomes active. Generation 2 may make its one bounded repair only when `repair_attempts_for_blocker=0/1`; success appends its resolution exactly once and may complete only with an empty queue, while failure ends as `repair_blocked`. Any blocker remaining or appearing after generation 2 resolves is a third blocker: preserve it in `pending_blockers` and fail closed with the generation-limit reason instead of opening generation 3.
## Freeze And Route
1. Freeze the goal, snapshot, blocker identity, paths, counters, and still-valid evidence. Keep `repair_slices=1/2` by default; set 2/2 only when the active plan already proves independent ownership.
2. Read-only verify worktree, active task, task status, staged target, digest, and current Gate requirements. On disagreement, set `authority_blocked`; only explicit user confirmation may select or rebind the correct task and resume.
3. Select one primary `route_class` and one bounded `next_action`; ask at most one highest-value user question at a time. Adjacent findings never replace the primary route.
4. Increment the relevant bounded counter before every diagnostic action, repair write, additional Review dispatch, regression, confirmation, or provider attempt. Unknown, timed-out, or interrupted outcomes still consume it. Record mandatory Review runs from current Gate evidence without treating them as a bounded counter. Never decrement a counter; reset only the blocker-local fields on the evidence-proven generation transition defined above.
5. When `allowed_paths` expands for the same acceptance target, increment `scope_expansions`, preserve the blocker identity, generation, all failure/diagnostic/repair/Review counters, and the current fast-path status, refresh `snapshot`, and route the added scope through the applicable requirement, diagnosis, or authority check before another write. Scope expansion never creates a new goal or Review budget, and it never creates a new blocker.
6. For any terminal non-complete status, set `phase=blocked`, `code_writes_allowed=false`, `blocking_issue`, and one `next_action`, except `requirements_blocked`, which stays in `requirements_repair` with product-code writes locked.
## Diagnose Before Repair
- While root cause is unknown or hypothetical, set `phase=diagnose` and `code_writes_allowed=diagnostics_only`; production repair is forbidden. Confirmation requires evidence explaining the symptom, failing path, and why the repair point controls the failure.
- Allow at most two diagnostic actions in an evidence epoch: first obtain missing evidence, then confirm or refute one hypothesis.
- Self-authored instrumentation, a code digest change, repeated observation of the same data, or rephrasing a hypothesis never resets `diagnostic_actions`.
- Increment `evidence_epoch` only once, after genuinely new independent evidence arrives, such as user or production reproduction data or new runtime output produced by approved instrumentation. Then set `status=active`, `phase=diagnose`, clear the resolved evidence blocker, and reset only `diagnostic_actions`; epoch 2 is final.
- Diagnostics must be minimal, reversible, privacy-safe, behavior-neutral, and within `allowed_paths`. New scope, deployment, production data, user reproduction, or access ends as `evidence_required` with exact collection steps.
- If epoch 2 exhausts its actions without confirmation, end as `root_cause_blocked`; never make a plausible-looking repair. Only explicit `user_extra_attempts=1/1` with `user_extra_kind=diagnostic` may add one final action for the current blocker.

## Five-Class Maximum Rollback
After the failure is preserved and a minimal reproduction confirms the controlling point, compare the current Requirements, Overview, Detail/packet, implementation, and process evidence. Select the earliest owning defect from exactly these five product/process classes. The route is evidence-derived; never infer a cause from the desired rollback.

| Defect class | Maximum rollback | Required refresh | Preserved by default |
| --- | --- | --- | --- |
| `IMPLEMENT_DEFECT` | Phase 2 implementation/check | Affected source/tests, Slice Review, Integration, and runtime receipt | Current Requirements, Overview, Detail, and independently bound sibling receipts |
| `PROCESS_DEFECT` | Current evidence/process; Phase 1 Detail only when a packet or digest-bearing plan must change | Affected mutable evidence/fixture/execution step; changed Detail and its downstream only when the plan changes | Unchanged planning and independently bound receipts |
| `DETAIL_DEFECT` | Phase 1 Detail | Affected Detail, packet/plan, Detail Review/confirmation, affected Slices, Integration, and runtime receipt | Requirements and Overview |
| `OVERVIEW_DEFECT` | Phase 1 Overview plus affected Detail | Overview Review and affected Detail/downstream evidence in order | Requirements |
| `REQ_BLOCKER` or material requirement change | Phase 1 Requirements affected Full chain | Affected Requirements through Overview, Detail, implementation, Integration, and runtime acceptance | Only evidence proven independent by current bindings |

- A correct Requirement/Overview/Detail with code, tests, or verification that deviates from it is `IMPLEMENT_DEFECT`; do not restart Requirements, Overview, or Detail.
- Current target-environment runtime evidence can disprove an internally green packet or planning assumption. Do not dismiss it as packet-external and do not let the reviewer invent product semantics: route the earliest owning artifact above.
- When several classes have evidence, use the earliest upstream owner and list its downstream refresh. When root cause is still hypothetical, remain in diagnosis instead of selecting a convenient class.

### Environment/Fixture Discriminator
Environment/fixture-only is a verification disposition, not a sixth defect class.

- If the confirmed packet, digest-bearing plan, fixture contract, or declared check is itself wrong or incomplete, classify `PROCESS_DEFECT`. Return to Detail only when the packet or digest-bearing plan must actually change.
- If the packet/plan and implementation are correct and only target-environment configuration, test data, execution setup, or the runtime fixture instance is wrong, remain at the current verification step. Refresh only the environment/fixture evidence and affected runtime probe; do not rewrite Requirements, Overview, Detail, or implementation to hide the environment failure.
- If the discriminator cannot be proven, stop as `evidence_required`; uncertainty is not permission to use the environment-only route.

## Selective Evidence Refresh
1. Build `evidence_refresh_plan` from exact binding changes: target bytes, invariants, Requirements/Detail inputs, declared checks, policy/provider, and supervisor digest.
2. Invalidate and reverify each receipt whose binding changed. Always refresh the affected union-snapshot Integration evidence and runtime receipt after changed implementation or planning bytes.
3. Preserve a sibling receipt only when every binding component remains equal and it has no dependency on the affected acceptance path. A v1 receipt, a receipt without sufficient binding data, or independence that cannot be proven is affected and must be reverified.
4. Never invalidate all siblings merely because one acceptance row failed, and never reuse a receipt after a relevant binding changed. If an existing digest/snapshot Gate reports evidence stale, refresh it honestly; do not mark or describe it as current by hand.

## Requirement Defects
- Enter this section only for the `REQ_BLOCKER`/material-change row above. Classify the requirement defect as missing, ambiguous, conflicting, changed, or misinterpreted.
- Set `status=requirements_blocked`, `phase=requirements_repair`, `route_class=requirement`, `code_writes_allowed=false`, and `next_action=requirements_repair`.
- Stop implementation and implementation Review. Do not guess product intent or modify tests to justify behavior; ask the user only when repository evidence cannot determine intent.
- Propagate confirmed changes through Requirements, Overview, Detail, implementation plan, affected Slice packets/invariants, then implementation. Invalidate only affected Slice and dependent Integration evidence; reuse everything unaffected.
- Requirement repair does not increment `repair_attempts_for_blocker`. Increment `requirement_confirmation_rounds` for one concentrated confirmation round; a second fundamental conflict requires a DCP decision.
- After the repaired requirement chain is current, set `status=active`, `root_cause_status=confirmed`, `root_cause=<requirement category>`, requirement-chain evidence, and `code_writes_allowed=repair` for one bounded implementation repair. If implementation already conforms, verify and complete without inventing a code repair.
## Repair And Verify
- With a confirmed root cause, set `phase=repair` and `code_writes_allowed=repair`, increment `repair_attempts_for_blocker` before the write, make one repair limited to the current blocker and `allowed_paths`, then run the focused reproduction or check.
- If focused evidence shows the same `blocker_fingerprint` persists, record whether it invalidates the root cause or only the implementation, downgrade `root_cause_status` when contradicted, and end as `repair_blocked`. Do not stack another patch or advance `blocker_generation`.
- If focused evidence proves the current blocker resolved, preserve it and continue only through the live Gate. Promote a queued blocker only through the ordered pending-blocker and generation rules above. A later finding can enter generation 2 only through the evidence and identity test above; a changed snapshot alone is insufficient.
- Only the user may authorize one extra named action for the current blocker. Before it, set `status=active`, the matching phase, `user_extra_attempts=1/1`, and `user_extra_kind`; never reset counters, broaden the goal, expand scope, open a normal new generation, or raise the two-generation cap. `repair_cycle` requires a still-confirmed root cause and includes one extra repair, focused verification, and any Review the live Gate currently requires; mandatory Review remains outside the additional-review budget.
- A temporary mitigation requires explicit approval and must be labeled `mitigation`, never `fixed`.
- If the active route defines an Integration owner, run `full_regression_runs=1/1` there. Otherwise follow the existing Gate that owns regression; this Skill never removes or duplicates a required check.
## Review And Failure Routing
- Mandatory Gate Review runs exactly when the live Gate requires it. Record each semantic Review digest in `reviewed_snapshot`. This Skill never skips, caps, or charges it to `additional_review_cycles`; every blocking semantic outcome still increments `same_goal_failures`.
- Route every mixed Review before implementation fingerprinting, severity ordering, or generation-budget checks. Partition requirement, authority, and implementation findings first. Requirement and authority findings never enter implementation `pending_blockers` and never consume implementation blocker generations; route them through their existing requirement or authority rules, preserve their Review evidence, and keep all implementation findings untouched in `deferred_implementation_findings`.
- While a requirement or authority finding controls the route, do not fingerprint, rank, repair, or charge the deferred implementation findings. After the controlling route resolves, require their semantic evidence to be current for the resulting snapshot and live Gate requirements, then resume implementation normalization; stale evidence follows `pending_blocker_current_semantic_evidence_required` without consuming implementation budget. Remove a deferred finding only when its complete evidence is transferred into the normalized active or pending implementation blocker state.
- After mixed-Review routing is clear, a Review with multiple implementation blockers must populate the active blocker plus `pending_blockers` under the deterministic selection rule. Do not collapse simultaneous blockers into `blocking_issue`, discard them, or relabel them as non-blocking follow-ups.
- Base budget permits one `additional_review_cycles=1/1` cycle for a changed snapshot only when the explicit user request includes that additional Review. Record that digest in `reviewed_snapshot`. `activation_reason=redundant_review` blocks the additional reviewer without dispatch. Other optional or unchanged-snapshot reviewers are blocked; only the persisted user-extra `repair_cycle` or `review` may add one additional cycle. Reclassify requirement or authority findings; route another implementation blocker through the blocker identity and generation rules instead of treating Review wording as a new blocker.
- `MALFORMED_REVIEW_OUTPUT`: inspect immutable raw output against the live Guru schema. If every required semantic field is complete, mechanically normalize only through the unique official writer identified from the live Guru help or workflow. Never change result, route, severity, findings, or invariants.
- If no unambiguous official writer exists, end as `review_output_blocked`; never hand-format. If raw semantics are incomplete, allow one new Review via `malformed_review_retries`; a second incomplete result ends as `review_output_blocked`.
- Provider, handshake, channel, capacity, or delivery failure: inspect raw errors, run one minimal preflight, then retry once. Attempt 2 failure for the digest ends as `external_blocked`; never switch provider or redo implementation. Reset `provider_attempts` only after an allowed route action creates a legitimate new digest. Verified recovery on the same digest uses the one explicit `user_extra_kind=provider`.
- Only a genuinely non-blocking adjacent or Owner/PUA finding belongs in `follow_ups`, with evidence, impact, priority, and suggested route. Normalize any blocking finding into the active/pending blocker state instead. Never implement an adjacent finding or auto-create a Task, Issue, or Spec; expand only with approval when required for current acceptance or immediate security, privacy, or data-integrity safety.

## Required Repair Retrospective
Every user- or QA-reported post-implementation runtime failure requires a current `trellis-break-loop`-equivalent retrospective before this continuation can close. `trellis-break-loop` may draft the analysis, but this Skill owns the continuation state and must verify all five fields against the same `acceptance_id` and failure row:

1. `direct_cause`: the confirmed code/process cause and evidence, not the symptom.
2. `earliest_missed_gate`: the earliest Requirement, Overview, Detail, Implementation, Test, Review, or Process Gate that should have caught it.
3. `false_green_reason`: why the prior tests and Review remained green.
4. `falsifiable_regression`: the new deterministic check or runtime probe plus evidence that it fails on the old wrong behavior and passes on the repair.
5. `prevention_disposition`: exactly one complete branch:
   - `writeback_required`: an allowed Skill/workflow/spec source owner, any required consumer parity, the exact prevention change, and validation evidence; or
   - `no_writeback_required`: an explicit reason and evidence references proving the existing contract plus the new regression already covers the recurrence path.

A regression that stays green on the known-wrong implementation makes `retrospective_state=incomplete`, routes `DETAIL_DEFECT`, and blocks completion until the Detail falsifiability contract and affected downstream evidence are repaired. Both prevention branches, neither branch, an empty no-writeback claim, or an invented unnecessary writeback makes `retrospective_state=incomplete`, routes `PROCESS_DEFECT`, and blocks completion. A required writeback that exceeds current allowed paths remains blocked pending explicit scope authority; it is not permission to edit.

After the retrospective is complete, rerun the original runtime probe in the target environment. A focused test, clean Review, `implementation_verified`, or an older pass cannot replace a current `runtime_acceptance_pass` for the repaired baseline.

## Archived Task And No-Script Boundary
- If the original Full task is archived, do not change its status or claim in-place reopen or machine-verified baseline inheritance. With lifecycle authorization, create a linked repair task/child that references the original `acceptance_id`, artifact digests, receipt references, and new failure evidence; otherwise report that single authorization step. Obey all current Gates and state honestly when they still require Full planning.
- This Skill cannot promise zero replanning for an archived task, automatic receipt inheritance, an executable reopen command, automatic digest invalidation, or script-level archive enforcement.
- Do not modify `.trellis/scripts/**`, `task.py`, `guru_gate.py`, Guru verify/hooks/apply, packaged script mirrors, Python/shell files, or CLI TypeScript runtime to implement this continuation. If repair requires any such change, stop with `blocking_issue=forbidden_script_scope` and request a separately scoped task and explicit authorization.
- These are behavioral Markdown contracts. They do not prevent direct script invocation outside the Skill, create a new lifecycle state, or make manual evidence current. Never describe them as a fail-closed runtime Gate.

## Exit Contract
Set `status=complete` and `phase=complete` only when the selected route's required action is resolved, its current evidence and digest agree, focused verification passes where applicable, all mandatory Reviews and existing Gates remain satisfied, `blocking_issue` is empty, `pending_blockers` is empty, and `deferred_implementation_findings` is empty. A post-implementation runtime-failure route also requires `retrospective_state=complete`, exactly one valid `prevention_disposition` branch, refreshed affected Integration evidence, and a current `runtime_acceptance_pass` for the original probe and repaired baseline. Append the final current blocker and its resolution evidence to `resolved_blockers` exactly once before completion. Code repair routes additionally require confirmed root cause evidence; requirement and mechanical-normalization routes do not require an invented code change.
Otherwise stop with the exact non-complete `status` and report:
```text
goal=<acceptance target>
acceptance_id=<original id>
runtime_failure_ref=<preserved row>
status=<exact blocked status>
defect_class=<five-class route or unclassified>
maximum_rollback=<bounded phase>
blocker=<id, fingerprint, generation, and reviewed snapshot>
root_cause_status=<status>
blocking_issue=<one blocker>
evidence=<current evidence>
evidence_refresh_plan=<invalidate, preserve, reverify, Integration, and runtime ids>
retrospective=<state plus direct cause, missed Gate, false-green reason, falsifiable regression, and XOR prevention disposition>
attempts=<failure, Slice, blocker generation, evidence epoch, diagnostic, blocker-local repair, requirement-confirmation, mandatory-Review evidence, additional-Review, malformed, provider, regression, scope-expansion, and user-extra counts>
resolved_blockers=<ordered preserved history>
pending_blockers=<ordered preserved blocking queue>
deferred_implementation_findings=<ordered preserved mixed-Review implementation evidence>
preserved_state=<preserved code and valid evidence>
required_next=<one action that can remove the blocker>
follow_ups=<non-blocking findings>
```
