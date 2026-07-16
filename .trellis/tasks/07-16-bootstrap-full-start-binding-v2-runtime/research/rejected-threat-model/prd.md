# Bootstrap Full Start Binding V2 Runtime

## Goal

Implement the Full Start Binding V2 runtime in the isolated SDK worktree without asking the broken Full v2 Start Guard to authorize its own repair. This child is activated only through the existing satisfiable legacy Full v1/high sequence. After installation, a disposable Full v2 canary must prove the repaired lifecycle before any Himora synchronization.

Parent task: `../07-16-fix-full-start-binding-v2`.

## Bootstrap Contract

- This child is the only implementation target; the parent remains planning and is never passed to `task.py start`.
- `gate-contract.json.policy_version` remains `guru-risk-contract-v1`.
- The child must never acquire `start_binding.version=2`, canonical V2 confirmation, V2 envelope or V2 activation-registry evidence for its own activation.
- Child activation order is legacy and forward-reachable: requirements confirmation -> overview/detail reviews -> detail confirmation -> current SDK unit risk/guard evidence -> guarded start.
- Production files remain untouched until the child has current legacy Gates and a separate explicit start approval.
- A child legacy pass proves only authorized delivery of the repair. It is not V2 correctness evidence.
- Every `SDK-U1..SDK-U4` implement/check worker uses the pre-repair installed runtime pinned by `verification/bootstrap-runtime-lock.json`; repaired source is never installed over the active child worktree mid-run.
- `bootstrap_runtime_lock_sha256`: `62074a1fef9e68d758a57dbebb26a4bd9058839d529c89d77a42e0eff21397a7`. This literal and the task-local requirements confirmation are projections only. Before risk/start, the user signs a canonical bootstrap-anchor subject with a protected external key and installs the subject/signature into the root-owned external registry; that signed receipt is the trust root.
- Canonical `BootstrapRuntimeAnchorSubjectV1` binds domain/schema, repository namespace, audience, principal, event/nonce/time window, task id/ref, requirements artifact digest, runtime-lock SHA-256, base commit and installed runtime tree. The user signs it with a passphrase-protected OpenSSH signing key whose public identity is root-owned outside the workspace; subject and signature are installed as a root-owned single-assignment receipt under `/var/db/trellis-guru/bootstrap-anchors/`.
- Every installed-v1 SDK worker dispatch verifies the external receipt signature/audience/subject and root-owned registry path first, then validates current requirements confirmation and recomputes the task-local projections and live `.trellis/scripts/guru` tree against the external subject. A changed receipt, lock, PRD, confirmation record, contract projection, base commit or runtime tree blocks before worker launch.
- Only after all four SDK slices are implemented and checked may the repaired source issue a signed audited legacy-continuation registration from the existing v1 start evidence. That registration permits final source-runtime verification/check-commit only; it cannot authorize a new slice, V2 evidence or additional implementation.

## Mirror Baseline Contract

`verification/mirror-baseline.json` binds base commit `54f3f407d4143577f40f38845ea9f6d55f3253d9`, source/package tree digests and all 38 live pre-existing drift entries. Ownership stays with `.trellis/tasks/07-14-custom-first-guru-delivery-control`, not this child.

Child source implementation/start may proceed, but package sync and install are hard-blocked until the owner publishes `.trellis/tasks/07-14-custom-first-guru-delivery-control/verification/guru-mirror-zero-drift-baseline.json` containing a reviewed commit, zero-exit sync check, tree/output digests and review run ids. After merging that exact commit, `guru_mirror_integration.py guarded-sync` is the only authorized sync entrypoint: it verifies the owner artifact, invokes the standard sync command, proves that the generated package delta exactly equals this child's reviewed `guru-template` source mapping and writes `verification/mirror-integration-proof.json`. Apply/install, V2 canary and source-runtime check-commit independently run `verify-proof`; direct sync without a current proof cannot release.

## Slice Namespaces

- Canonical SDK slice ids: `SDK-U1..SDK-U4`, mapped respectively to `UNIT-stable-planning-binding`, `UNIT-full-confirmation-authority`, `UNIT-guarded-slice-activation`, `UNIT-binding-regression-release`.
- Canonical regression members: `FIX-F1/FIX-F2`.
- Target replay members: `HIM-S1/HIM-S2`.

Unqualified `S1/S2` cannot be used as confirmation or test evidence.

## Core Capability Priorities

- **P0**: keep parent unstarted and child legacy-only through bootstrap delivery.
- **P0**: remove the confirmation-dependent A2 cycle without weakening live Gate validation.
- **P0**: require exact semantic risk membership and replay-verifiable signed authorization receipts.
- **P0**: preserve guarded start and later-worker lifecycle CAS with external monotonic activation provenance.
- **P1**: preserve legacy Full/Lite/Micro compatibility and complete source/package/install/canary evidence.

## Requirements

### BHV-001 [REQ-UC-001] Legacy bootstrap remains isolated

- **Given** the current Full v2 start path is cyclic
- **When** this child is planned and activated
- **Then** its task contract remains legacy Full v1/high and contains no V2 discriminator
- **And** the parent remains unstarted and production remains unchanged until child activation
- **And** all child slice workers remain on one pinned pre-repair installed v1 runtime; no repaired source/runtime is installed into the active child before all SDK slice checks complete
- **And** the original lock SHA-256 is a literal in this requirements artifact and is therefore bound by the user's requirements confirmation before risk/start; every worker verifies that confirmed anchor rather than trusting the current lock file
- **And** the trust root is the root-owned externally signed `BootstrapRuntimeAnchorReceiptV1`; PRD literal, requirements confirmation, lock and contract field are projections that must all match its subject

### BHV-002 [REQ-UC-002] Stable planning binding removes the hash cycle

- **Given** current requirements, detail, contract, review, decision and expected-slice facts
- **When** V2 risk packets are generated before Full confirmation
- **Then** every packet binds one domain-separated A2 that is byte-identical after confirmation
- **And** A2 binds the provider-asserted canonical repository namespace
- **And** confirmation, receipt, envelope, activation and lifecycle evidence is excluded from A2

### BHV-003 [REQ-UC-003] Risk set proves exact semantic membership

- **Given** a reviewed expected-slice inventory
- **When** confirm, check-start, Start Guard or later-slice preflight reads risk packets
- **Then** one shared validator proves schema, task, filename/slice, matching slice packet, A2, scope/policy, decisions and invariants
- **And** canonical observed members equal expected members exactly

### BHV-004 [REQ-UC-004] Full authorization uses a durable signed receipt

- **Given** the current stable subject and exact risk member set
- **When** a user authorizes Full v2
- **Then** a configured external provider signs canonical `ConfirmationSubjectV2`
- **And** raw TTY, agent quote, turn reference, actor string or reusable bearer token cannot authorize
- **And** subject binds provider-asserted canonical repository namespace and audience exactly `trellis-guru-full-start-v2:<repository_namespace>`
- **And** subject includes actor/time/via/turn/quote digest and exact action rows: selected `guarded_start`, selected `implement`, selected `check`, and later `implement`/`check`
- **And** `AuthorizationGrantCoreV2` contains only independently known immutable fields, excludes grant/authorization/batch/projection derived values and replay-time `verified_at`, and is hashed before all downstream derivations
- **And** signature, audience, validity, revocation, event/nonce uniqueness and byte-identical deterministic grant/batch/projection retry are verified

### BHV-005 [REQ-UC-005] Canonical projection and compatibility records cannot diverge

- **Given** one verified authorization receipt
- **When** confirmation is recorded or checked
- **Then** one canonical projection and requirements/detail compatibility projections are written atomically
- **And** any shared security-field mismatch, stale subject or replay blocks check-start and guarded start

### BHV-006 [REQ-UC-006] Activation binding has no forward reference

- **Given** current C2/U2 and a selected member
- **When** an attestation or envelope is issued
- **Then** it binds a precomputable activation-contract preimage rather than a future task snapshot
- **And** selected and later envelopes are issued just in time from the same current authorization

### BHV-007 [REQ-UC-007] Activation provenance is externally monotonic

- **Given** selected V2 start is ready
- **When** guarded start crosses the official lifecycle boundary
- **Then** V2 contract adoption is externally registered before A2/risk, and the registry later reserves the task/preimage before official call, persists the exact local snapshot, and finalizes after success
- **And** failed or compensated attempts remain registered
- **And** deleting all task-local V2 markers cannot select legacy

### BHV-008 [REQ-UC-008] Guarded and later-slice CAS remains fail-closed

- **Given** a selected or later expected member
- **When** official start or a worker is about to launch
- **Then** receipt, authorization, risk set, envelope, activation registry/snapshot, task/session and lifecycle CAS are all current
- **And** the selected slice has separate `guarded_start`, `implement` and `check` rows/E bindings, while every later slice has separate `implement` and `check` rows/E bindings
- **And** pre-lock, lock-internal, final pre-call and post-return checks remain mandatory

### BHV-009 [REQ-UC-009] Version dispatch preserves compatibility without downgrade

- **Given** Full v2, legacy Full v1, Lite, Micro/Small and pre-upgrade in-progress tasks
- **When** runtime chooses an algorithm
- **Then** planning uses the task contract, in-progress uses signed V2 activation or audited legacy registration, and absence never selects legacy
- **And** unknown, mixed, migration-required or registry/task-divergent states block
- **And** this bootstrap child does not consume the repaired dispatcher during SDK slice execution; after all slice checks, source-runtime verification requires a signed audited legacy registration derived from its current v1 start evidence and grants no new implementation slice

### BHV-010 [REQ-UC-010] Real lifecycle, mirror and target evidence controls release

- **Given** unit suites can miss a cross-command lifecycle defect
- **When** implementation is considered releasable
- **Then** one chronological `FIX-F1/FIX-F2` fixture crosses the real builders, signed receipt, confirm, check-start, guarded start and later preflight
- **And** source/package/install checks and a disposable Full v2 canary are green before `HIM-S1/HIM-S2` replay
- **And** runtime hard-denies the design parent at check-start, Start Guard and before-start hook
- **And** package sync must run through guarded mirror verification, while apply/install, canary and source-runtime check-commit reject a missing, stale or non-matching mirror integration proof

## Non-Functional Requirements

- **Security**: no task-writable string is a trust root; keys, trust lookup, revocation and monotonic activation state live outside task artifacts.
- **Bootstrap trust**: the existing unencrypted `~/.ssh/id_rsa` is explicitly ineligible because the agent can use it. Bootstrap signing requires a new passphrase/hardware-protected key plus a root-owned allowed-signers file and root-owned single-assignment receipt.
- **Determinism**: every digest has domain/schema separation and canonical sorted inputs.
- **Atomicity**: canonical/projection writes and activation snapshot/registry transitions have explicit CAS and recovery.
- **Compatibility**: legacy Full v1, Lite and Micro/Small retain explicit owned tests.
- **Scope**: edit contract-allowed Guru source/tests/spec; package mirror is generated only by standard sync after unrelated drift is isolated, never hand-edited.
- **Delivery**: executor may only recommend candidate pass; independent verifier/harness or user owns final status.

## Failure Paths

- **Bootstrap boundary violation**: parent start, child V2 marker or production edit before child activation blocks delivery and returns to planning.
- **Stable binding drift**: any A2 input changes after risk generation; risk/confirm/start blocks and evidence regenerates.
- **Risk inventory invalid**: expected/observed mismatch or packet semantic failure blocks all four consumers.
- **Receipt invalid**: signer, audience, subject, time, revocation or event/nonce validation fails; no authorization is current.
- **Projection tamper**: canonical and compatibility evidence diverges; check-start and guarded start block.
- **Activation provenance drift**: external registry and local snapshot differ or disappear; official/worker calls block and legacy is never inferred.
- **Lifecycle race**: final/pre/post CAS fails; pre-call has zero official side effects, post-call uses exact compensation/manual recovery.
- **Compatibility/mirror/canary failure**: release and Himora synchronization remain blocked.
- **Bootstrap runtime drift**: any SDK worker resolves a runtime path/digest different from the pinned pre-repair v1 lock, or repaired source is installed mid-run; worker/release blocks and no implicit legacy registration is created.
- **Bootstrap lock rewrite**: task-local PRD/confirmation/lock/contract/runtime/per-worker evidence is coherently rewritten; the external signed subject, trusted key or root-owned registry record no longer matches, so worker dispatch and continuation registration block.
- **Bootstrap anchor unavailable**: protected signer, root-owned allowed-signers file or root-owned subject/signature is absent, mutable, invalid, expired or divergent; requirements confirmation/start remains operator-blocked and no worker or continuation registration may proceed.
- **Mirror proof unavailable**: direct sync, missing owner artifact, non-ancestor reviewed commit, baseline/delta mismatch or stale proof; apply/install/canary/check-commit block even if package files were generated.

## Acceptance Criteria

- [ ] Child contract is Full/high, `guru-risk-contract-v1`, linked to the parent and contains no V2 activation marker.
- [ ] Parent remains planning and child has no production edits before legacy activation.
- [ ] `bootstrap-runtime-lock.json` proves every SDK implement/check worker used the same pre-repair installed v1 runtime; no in-place repaired-runtime install occurred before all slice checks.
- [ ] Child requirements confirmation binds the exact `bootstrap_runtime_lock_sha256` literal; worker preflight and continuation registration reject any lock/PRD/contract/runtime mismatch against that original confirmed anchor.
- [ ] Before requirements confirmation, a protected external signer creates one `BootstrapRuntimeAnchorReceiptV1`; root-owned trust/registry verification passes and its subject exactly matches requirements digest, lock SHA, base commit and installed runtime tree.
- [ ] Every worker and continuation registration treats the external signed receipt as authority and task-local confirmation/lock/contract only as matching projections.
- [ ] After all SDK slice checks, a signed audited legacy registration enables only final source-runtime verification/check-commit and cannot authorize another implementation slice or V2 evidence.
- [ ] `stable_digest_before_confirm == stable_digest_after_confirm`.
- [ ] Exact expected/observed risk membership blocks malformed, missing, unexpected, duplicate, orphan, symlink and mixed-version evidence.
- [ ] Signed receipt subject, audience, time, revocation, event/nonce and idempotency tamper tests fail closed.
- [ ] Actor/time/via/turn/quote/action fields are signed and deterministically derive one byte-identical grant/batch/projection.
- [ ] `AuthorizationGrantCoreV2` and downstream derivations are acyclic and replay-time verifier observations are non-authoritative.
- [ ] Each E binds one exact `{slice_id, action}` row/digest; selected start/implement/check and later implement/check are all exercised.
- [ ] Canonical confirmation and requirements/detail projections cannot diverge.
- [ ] E[i] binds a precomputable activation preimage and never a future snapshot.
- [ ] External activation registry prevents coordinated task-local marker deletion downgrade.
- [ ] External binding adoption exists before A2/risk and registry records form a signed sequence/predecessor CAS chain.
- [ ] Real `FIX-F1/FIX-F2` lifecycle reaches verified start and full later-member authorization.
- [ ] Legacy Full v1, Lite, Micro/Small and audited pre-upgrade compatibility tests pass.
- [ ] Focused/full Guru tests, apply/install verification, source/package sync check and GitNexus change detection pass.
- [ ] Mirror baseline manifest matches the 38 live pre-existing drifts; sync/install remain blocked until the named owner artifact proves a reviewed zero-drift commit.
- [ ] After baseline merge, generated package delta equals only this child's reviewed source mapping.
- [ ] `guru_mirror_integration.py guarded-sync` is the sole release-authorized sync path; current proof is revalidated by apply/install, V2 canary and source-runtime check-commit, and direct sync without proof remains release-blocked.
- [ ] Design parent hard denial prevents check-start/guard/hook official side effects.
- [ ] Disposable canary with `CANARY-SELECTED/CANARY-LATER` writes replayable PASS evidence before target `HIM-S1/HIM-S2` artifacts are generated.

## Out Of Scope

- Starting the parent task.
- Direct official `task.py start` that bypasses Guru guarded start.
- Treating child legacy authorization as V2 verification.
- Modifying Trellis Core or Himora business behavior.
- Absorbing unrelated reinstall work or pre-existing package mirror drift.
- Committing, pushing, merging, archiving or finish-work before separately authorized lifecycle steps.

## Open Questions

None. The user explicitly confirmed the parent/legacy-bootstrap-child/V2-canary topology in the current Codex thread. Any new trust-provider, schema, migration or scope trade-off returns here before implementation.

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`, PUA Amazon architecture discipline, GitNexus debugging/impact guidance.
- Repository evidence inspected: parent PRD/design/implement package, current `guru_task.py`, `guru_gate.py`, `guru_delivery_policy.py`, `guru_supervise.py`, focused tests, contract generator and current intake output.
- Domain/terminology triggers: parent, bootstrap child, legacy activation, V2 canary, signed confirmation receipt and monotonic activation registry are distinct contracts.
- Current code vs user intent conflicts: current V2 confirmation order and Start Guard digest are cyclic; raw TTY/task strings are not durable provenance; task-local marker absence cannot prove legacy.
- Product decisions confirmed:
  - DEC-BOOT-001: non-started parent + legacy Full v1/high bootstrap child + repaired-runtime V2 canary.
    - user_quote: "确认"
    - confirmed_ref: Codex thread 019f69a6-c923-7792-8607-7863eae0430a
  - DEC-BOOT-002: child creation/planning only; no child start or production edit is authorized by the quote above.
    - user_quote: "确认"
    - confirmed_ref: current turn scope statement
- Open product/scope/risk questions: none; reason: parent evidence and the user's explicit OQ-002 confirmation closed task topology, security scope and delivery boundaries.

### Question Loop Log

question_policy: evidence_only

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-BOOT-001 | 2026-07-16 | How can the broken V2 runtime lawfully deliver its own repair? | Non-started parent, separately gated legacy Full v1/high child, then V2 canary | Adds one child and canary but avoids direct start or false V2 authorization | "确认" | DEC-BOOT-001 | prd.md, design.md, implement.md, gate-contract.json |

## Notes

- The child is planning only.
- The next human confirmation is the child requirements baseline after reviews, not implementation start.
- Bootstrap anchor status: blocked pending user creation/use of a protected signing key and root-owned external allowed-signers/receipt. The existing unencrypted SSH key cannot satisfy this contract.
