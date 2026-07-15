# Requirement Main Definition

## 1. Goal And Scope

Deliver a Custom-first Guru delivery system that uses official Workflow/Spec/Config customization plus a reversible project-local overlay, keeps Trellis Core unchanged during the functional phase, and measurably improves delivery speed, risk timing, autonomous closure, repeated-task cost, cross-artifact consistency and Gate-caused rework across all supported intents.

In scope: all-intent route/risk policy, bounded confirmation, finite execution, exact and semantic-delta evidence reuse, deterministic consistency checks, Gate-value metrics, reversible install lifecycle, minimal historical-session replay and official Template cutover readiness.

Out of scope: new Trellis Core APIs, immediate deletion of existing SDK Guru bundling, a new Marketplace engine, ExtensionManager/WAL infrastructure, trusted-reviewer identity infrastructure, generic replay platforms, six independent slice lifecycles, bootstrap burn/reuse, hostile local-bundle security, production deployment, provider billing internals, or treating Agent-authored evidence as a security authorization.

## 2. Core Capabilities

| Capability | Priority | Source scenarios | Completion signal |
| --- | --- | --- | --- |
| CAP-001 Risk-proportional delivery | P0 | REQ-UC-001, REQ-UC-002, REQ-UC-003 | Each intent resolves an execution route, bounded artifacts and a terminal condition |
| CAP-002 Evidence convergence | P0 | REQ-UC-005, REQ-UC-006 | Unchanged input reuses evidence; real dependency changes invalidate the affected evidence without review ping-pong |
| CAP-003 Official reversible distribution | P0 | REQ-UC-007 | Official Custom install plus managed apply/verify/unapply restores owned pre-state and preserves unrelated user work |
| CAP-004 Cost compounding | P1 | REQ-UC-004 | Comparable warm run uses no more than 70% of each declared cold-run proxy, subject to the small-baseline floor |
| CAP-005 Cross-artifact consistency | P1 | REQ-UC-005 | Requirement, design, module/symbol and test evidence trace is complete |

## 3. Requirement Scenarios

### REQ-UC-001 Route a bounded low-risk delivery

- Actor/trigger: user submits an implementation, review, research, debug, docs, config or ops request with no unresolved high-risk signal.
- Given: intent, affected paths and current repository facts are available.
- When: intake evaluates risk and resolves an execution route.
- Then: only the selected intent/route artifact set is required, and execution reaches its first route-specific value signal within budget.
- Negative invariant: a non-implementation intent must not be measured by “first code”; it uses first verified evidence or first accepted artifact instead.
- Extracted behavior: BHV-001.

### REQ-UC-002 Expose high risk before execution

- Actor/trigger: intake or scope reclassification detects high-risk workflow/Gate/runtime, data, privacy, security, migration or cross-layer impact.
- Given: current scope fingerprint and policy version are available.
- When: execution is requested or scope expands.
- Then: route is Full, a current risk packet exists, and unresolved critical/high decisions require a bounded confirmation attestation before worker launch.
- Negative invariant: a user preference or stale confirmation must not authorize a lower route or implementation start.
- Extracted behavior: BHV-002.

### REQ-UC-003 Close work autonomously after bounded confirmation

- Actor/trigger: current scope and irreversible decisions are confirmed through a trusted channel.
- Given: artifact digests and confirmation attestation remain current.
- When: the selected workflow continues.
- Then: the Agent completes the bounded plan without asking the same decision again, stopping only on terminal success, new irreversible risk, scope expansion or budget failure.
- Negative invariant: a budget must terminate work, never bypass a required Gate.
- Extracted behavior: BHV-003.

### REQ-UC-004 Reuse verified task-family knowledge

- Actor/trigger: a comparable task family has prior verified decisions, evidence and validation commands.
- Given: reuse candidates match policy, repository and artifact digests.
- When: a new task changes only a bounded delta.
- Then: unchanged knowledge is reused and the warm-run cost proxies meet the declared <=70% rule.
- Negative invariant: no family match must not trigger an unbounded history scan.
- Extracted behavior: BHV-004.

### REQ-UC-005 Preserve requirement/design/code/test consistency

- Actor/trigger: a change affects route, API, schema, state, boundary, ownership or testing contracts.
- Given: project-current design SSOT and task-local delta design are discoverable.
- When: final verification runs.
- Then: REQ-UC/BHV, UNIT, module/symbol and test command/result mappings are complete and no source/template/installed drift remains unexplained.
- Negative invariant: `no-doc-impact` must not override a higher-priority contract-impact signal.
- Extracted behavior: BHV-005.

### REQ-UC-006 Reuse valid Gate evidence and terminate non-progress

- Actor/trigger: a Gate/review is evaluated again for the same or changed artifact set.
- Given: canonical artifact manifests, digests, honest provider/context provenance and finding fingerprints exist.
- When: the Gate computes current validity.
- Then: same semantic input reuses valid evidence; true dependency changes invalidate downstream evidence; repeated findings without new semantic evidence stop as STALLED.
- Negative invariant: prose-only finding wording or run-id changes must not create false independence or progress; same-provider Codex review is recorded honestly and is never promoted to independent-review proof.
- Extracted behavior: BHV-006.

### REQ-UC-007 Install, upgrade and remove Guru without ownership loss

- Actor/trigger: user runs plan, apply, adopt, upgrade, status, verify or unapply against an official Trellis project.
- Given: official Custom source, target pre-state and an external rollback bundle are available.
- When: an Extension lifecycle operation executes or recovers.
- Then: created/replaced ownership is explicit; preimage evidence exists before mutation; failed apply recovers when ownership is provable; conflicts preserve user content; successful unapply restores managed pre-state equivalence.
- Negative invariant: project-owned Template files or hash-mismatched user changes must not be deleted as Extension-owned files.
- Extracted behavior: BHV-007.

## 4. Failure And Recovery Requirements

- Invalid policy, manifest, risk packet, confirmation attestation or ownership state fails closed with one recovery action.
- A trappable apply failure or signal recovers from the external preimage when exact ownership is provable; otherwise it fails closed to one explicit manual-recovery action.
- Scope expansion freezes new workers and invalidates only attestations whose scope/digest no longer matches.
- Missing telemetry is `unknown`, never zero and never counted as passing a hard benchmark.
- Unsupported platform hooks are reported as compensated/advisory/unavailable; non-blocking hooks are never called enforced.

## 5. Outcome-first Delivery Milestones

These milestones are the execution authority for the remainder of the task. Internal module or slice count is not a completion criterion.

### M0 - Custom V0 foundation and self-use lifecycle (`completed`)

- One policy resolves `small_inline`, `micro_task`, `lite_task` and `full_chain` high-risk work.
- Lite is host-inline with zero confirmation, zero Worker and no pre-code planning-review Gate.
- High-risk work fails closed before implementation without current risk and confirmation evidence.
- Exact fingerprint/digest evidence reuse applies the declared 70% planning/token-budget proxy and invalidates on digest drift.
- The Custom overlay installs, recovers from owned partial failure, and performs managed-asset unapply while preserving unrelated user work.
- Evidence: commits `de52458f` and `52e64185`; install/recovery/unapply suite `101/0`; full Custom overlay suite `564/0`.

### M1 - Operational route proof (`candidate complete`)

- Install the committed Custom package into one disposable official Trellis target.
- Run a deterministic four-route matrix and real Lite/full-high-risk dogfood derived from sessions `019f5b42-b507-7801-96ef-50b1ed01c863` and `019f5f27-045d-7fc1-b84d-5ce21e8c8358`.
- Record `time_to_first_code`, confirmation count, Worker count, finding-to-fix cycles, full-suite count and wall time per route.
- Acceptance: Lite reaches code in five-minute class with 0 confirmations/0 Workers; full-high-risk exposes risk before code, uses at most one confirmation and then continues through deterministic check; no Claude event exists.
- Evidence: `M1_OPERATIONAL_ROUTE_PROOF.md`; Lite TTFC `18s`, confirmations `0`, Workers `0`; Full/high missing-risk `rc=2` with `start_attempts=0`; independent `2 HIGH + 1 MEDIUM` findings repaired in one batch; apply/consistency `109/0`.

### M2 - All-intent compounding and Gate value (`candidate complete`)

- Cover implementation, review-only, research/docs/config/ops and repeated-debug intents with route-specific first-value metrics and terminal conditions.
- Repeat a matching task to prove unchanged evidence reuse and <=70% controllable planning/context/token-budget proxies; change the target digest to prove invalidation.
- Prove scope expansion re-routes before further implementation, identical confirmation is not repeated, unchanged evidence is reused and Gate-caused rework remains below 10%.
- Exact provider token telemetry is reported when available; otherwise it remains `unknown` and a separately labelled controllable proxy is used without claiming actual billing reduction.
- Evidence: `M2_ALL_INTENT_COMPOUNDING_PROOF.md`; all 7 intent rows reuse exact evidence at the declared 70% proxy, both relevant digest drifts invalidate 7/7, scope expansion promotes before another write, unchanged confirmation reuses batch 1, and observed Gate-caused rework is `0/4` with an explicit small-sample warning.

### M3 - Official Custom and Template cutover readiness (`candidate complete`)

- Validate official Workflow/Spec/Config/Template resolution in a disposable target without a fork package or Core modification.
- Close the user-visible lifecycle surface: read-only plan/status/verify plus compatible apply/upgrade/unapply behavior using the existing rollback-bundle approach, not a new WAL framework.
- Produce the minimal source-to-Template cutover mapping only; add a manifest only when the official resolver requires it.
- Acceptance: source, installed assets, docs and tests match; native Trellis remains usable after unapply; Core-zero remains true.
- Evidence: `M3_CUSTOM_TEMPLATE_CUTOVER_PROOF.md`; official Trellis `0.6.7` installed all four exact spec/workflow stacks and rejected blank fallback; lifecycle `120/0`, catalog `18/0`; one Codex HIGH false-state finding was repaired in one batch; Core-zero and Codex-only remain true.

### M4 - Final consistency and task closure (`current`)

- Publish a hardened status report so V0 deferrals no longer contradict implemented recovery, managed unapply and the full suite.
- Update `REQ/BHV -> design -> code -> test` traceability with actual paths and results.
- Run checks proportional to the final diff, one final Codex check-only review, `trellis-update-spec`, final commit and readback.
- Archive/finish only with explicit lifecycle authorization; do not push.

## 6. Completion Rule

The task is complete only when M1-M4 pass. Marketplace catalog, ExtensionManager WAL, trusted reviewer identity, generic replay infrastructure, bootstrap burn and six-slice execution are explicitly non-requirements and cannot block completion.

## 7. Open Questions

No unresolved product or scope question is currently known. M1-M4 proceed without another planning-review cycle. A new review or confirmation is allowed only when execution discovers a new irreversible product choice, a real external-information gap, or expanded critical/high risk; it may not silently change these approved scenarios.
