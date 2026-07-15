# Requirement Main Definition

## 1. Goal And Scope

Deliver a Custom-first Guru control plane that uses official Workflow/Spec Template distribution plus a reversible project-local Extension, keeps Trellis Core unchanged during the functional phase, and improves verified delivery value across implementation, review, research, debugging, documentation, configuration and operations intents.

In scope: route/risk policy, bounded confirmation, semantic Gate evidence, finite supervision, context reuse, design synchronization, official catalog distribution, reversible install lifecycle and end-to-end replay.

Out of scope: new Trellis Core APIs, immediate deletion of existing SDK Guru bundling, production deployment, controlling provider billing internals, or treating Agent-authored evidence as a security authorization.

## 2. Core Capabilities

| Capability | Priority | Source scenarios | Completion signal |
| --- | --- | --- | --- |
| CAP-001 Risk-proportional delivery | P0 | REQ-UC-001, REQ-UC-002, REQ-UC-003 | Each intent resolves an execution route, bounded artifacts and a terminal condition |
| CAP-002 Semantic convergence | P0 | REQ-UC-005, REQ-UC-006 | Unrelated changes retain evidence; true dependency changes invalidate only downstream evidence |
| CAP-003 Official reversible distribution | P0 | REQ-UC-007 | Official resolver install plus Extension apply/verify/unapply restores pre-state |
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
- Given: canonical artifact manifests, digests, identity evidence and finding fingerprints exist.
- When: the Gate computes current validity.
- Then: same semantic input reuses valid evidence; true dependency changes invalidate downstream evidence; repeated findings without new semantic evidence stop as STALLED.
- Negative invariant: prose-only finding wording or run-id changes must not create false independence or progress.
- Extracted behavior: BHV-006.

### REQ-UC-007 Install, upgrade and remove Guru without ownership loss

- Actor/trigger: user runs plan, apply, adopt, upgrade, status, verify or unapply against an official Trellis project.
- Given: catalog source, target pre-state and durable transaction journal are available.
- When: an Extension lifecycle operation executes or recovers.
- Then: created/replaced/adopted ownership is explicit; writes are journaled before first mutation; conflicts preserve user content; successful unapply restores pre-state equivalence.
- Negative invariant: project-owned Template files or hash-mismatched user changes must not be deleted as Extension-owned files.
- Extracted behavior: BHV-007.

## 4. Failure And Recovery Requirements

- Invalid policy, manifest, risk packet, confirmation attestation or ownership state fails closed with one recovery action.
- A process crash after journal durability but before state publish recovers or rolls back idempotently on the next lifecycle operation.
- Scope expansion freezes new workers and invalidates only attestations whose scope/digest no longer matches.
- Missing telemetry is `unknown`, never zero and never counted as passing a hard benchmark.
- Unsupported platform hooks are reported as compensated/advisory/unavailable; non-blocking hooks are never called enforced.

## 5. Open Questions

No unresolved product or scope question is currently known. Planning details remain subject to Overview/Detail review; those reviews may identify a new decision, but may not silently change these approved scenarios.
