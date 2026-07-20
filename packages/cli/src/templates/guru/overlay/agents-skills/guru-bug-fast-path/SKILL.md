---
name: guru-bug-fast-path
description: "Use during Trellis/Guru Bug repair when the user explicitly invokes guru-bug-fast-path, the same acceptance goal records two implementation or semantic failures, or an additional semantic reviewer not required by the active Gate is about to run for the same snapshot. Freeze scope, key diagnosis and repair to a stable blocker identity, allow at most two evidence-proven independent blocker generations, route requirement, malformed-review, provider, authority, and adjacent findings, then complete with current evidence or stop with one blocker. Do not use for a first ordinary failure, mandatory Gate reviewers, or post-fix retrospectives."
---

# Guru Bug Fast Path

Stop repair-review-retry loops without weakening the active workflow.
## Guardrails
- This is a behavioral guardrail, not a Gate or runtime controller. It acts only when control returns at a step boundary; never interrupt a running worker or supervisor.
- The live task route and its Requirements, Detail, Review, Receipt, Commit, and Integration Gates remain authoritative.
- Preserve user changes. Activation alone never commits, pushes, merges, archives, installs Guru, runs `finish-work` or `trellis-break-loop`, updates Specs, or changes task authority.
- Never change tests, verifiers, reviewer conclusions, scoring, provider policy, or runtime code to obtain a pass.
## Activation
- Explicit invocation activates immediately at the next step boundary.
- Increment `same_goal_failures` only for an implementation failure or blocking semantic Review failure against the unchanged goal, including a mandatory Gate Review blocker. Provider, malformed-output, requirement, and authority failures use their own routes.
- Auto-activate when `same_goal_failures=2/2`. A code snapshot or allowed write-scope change does not reset it; only a user-confirmed change to the acceptance target, or `complete`, ends the count.
- Before `activation_reason=redundant_review`, prove the reviewer is additional and not required by the active Gate. Mandatory Gate reviewers never trigger redundant-review activation or consume the additional-review budget, but their blocking semantic outcomes still increment `same_goal_failures`.
- This Markdown pilot observes only evidence available when control returns. Seed all applicable counters from receipts, logs, Review records, or visible conversation history; never invent a missing attempt or claim to interrupt an in-flight supervisor.
- Do not activate for the first ordinary failure.
## State
Carry this block across turns and compactions:
```text
[FAST-PATH-STATE]
goal=<one acceptance target>
status=active|requirements_blocked|root_cause_blocked|evidence_required|repair_blocked|review_output_blocked|external_blocked|authority_blocked|complete
phase=freeze|diagnose|requirements_repair|repair|review|blocked|complete
route_class=requirement|root_cause|implementation|malformed_review|external|authority
activation_reason=explicit|repeated_failure|redundant_review
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
## Requirement Defects
- Classify the defect as missing, ambiguous, conflicting, changed, or misinterpreted requirements.
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
## Exit Contract
Set `status=complete` and `phase=complete` only when the selected route's required action is resolved, its current evidence and digest agree, focused verification passes where applicable, all mandatory Reviews and existing Gates remain satisfied, `blocking_issue` is empty, `pending_blockers` is empty, and `deferred_implementation_findings` is empty. Append the final current blocker and its resolution evidence to `resolved_blockers` exactly once before completion. Code repair routes additionally require confirmed root cause evidence; requirement and mechanical-normalization routes do not require an invented code change.
Otherwise stop with the exact non-complete `status` and report:
```text
goal=<acceptance target>
status=<exact blocked status>
blocker=<id, fingerprint, generation, and reviewed snapshot>
root_cause_status=<status>
blocking_issue=<one blocker>
evidence=<current evidence>
attempts=<failure, Slice, blocker generation, evidence epoch, diagnostic, blocker-local repair, requirement-confirmation, mandatory-Review evidence, additional-Review, malformed, provider, regression, scope-expansion, and user-extra counts>
resolved_blockers=<ordered preserved history>
pending_blockers=<ordered preserved blocking queue>
deferred_implementation_findings=<ordered preserved mixed-Review implementation evidence>
preserved_state=<preserved code and valid evidence>
required_next=<one action that can remove the blocker>
follow_ups=<non-blocking findings>
```
