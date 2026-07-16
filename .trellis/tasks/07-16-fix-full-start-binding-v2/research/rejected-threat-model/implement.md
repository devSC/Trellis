# Full Start Binding V2 Implementation Plan

## 1. 执行边界 (Execution Boundary)

This task is the design/integration parent and remains `planning`; it is never an implementation or `task.py start` target. Runtime check-start, Start Guard and before-start hook must hard-block its role. Task topology approval did not authorize child start or production edits.

The approved legacy Full v1/high bootstrap child now exists and is planning. Only that child uses Trellis sub-agents after its own requirements/detail confirmations, reviews and separate start approval. The main session owns parent artifacts, user decisions, child/task-map coordination, spec changes, integration, commit scope and final lifecycle actions.

The task changes Guru Custom runtime only. It must not modify Trellis Core, the original dirty checkout, the target Himora business code or unrelated reinstall artifacts.

## 2. Preconditions

- [ ] Re-read current task/branch/worktree status and prove the parent remains planning and the one linked child is the user-approved bootstrap child.
- [ ] Re-run exact intake for the parent and verify `gate-contract.json` declares `task_role=design_parent`, `start_this_parent_task=false` and the target V2 contract.
- [ ] Verify the linked child is `full_chain/high`, `guru-risk-contract-v1`, has no V2 marker, includes generated-only package mirror scope and has no premature production edits.
- [ ] Prove the child can use the satisfiable legacy order: requirements confirmation -> overview/detail reviews -> detail confirmation -> SDK unit risk/guard binding -> guarded start.
- [ ] Before child requirements confirmation, verify the runtime lock/literal/projection, generate canonical bootstrap anchor subject, obtain a protected user signature and install root-owned allowed-signers plus single-assignment subject/signature outside the workspace.
- [ ] Before every SDK implement/check dispatch, verify the external receipt signature/root ownership/current subject first, then run installed-v1 `check-implementation` and compare task-local projections plus live runtime to values taken from the signed subject.
- [ ] Prohibit applying or installing repaired source into the active child worktree until SDK-U1..SDK-U4 implementation/check and independent implementation review are complete.
- [ ] Verify the reviewed SDK unit inventory is explicit and unchanged before child risk generation.
- [ ] Read `guru-overlay-gates.md`, cross-layer guide, Python/script/test conventions and current Full Start design history.
- [ ] Reproduce the current digest loop from the source branch in a temporary fixture.
- [ ] Record current focused baselines: delivery-policy tests, start-guard tests, shell verify suite, apply test and mirror sync status.
- [ ] Validate the child `verification/mirror-baseline.json` against the live 38-drift check and keep sync/install blocked until the named owner zero-drift artifact exists and its reviewed commit is merged.

## 2.1 Slice To Unit Trace

| Slice | Primary UNIT | BHV scope | Result boundary |
| --- | --- | --- | --- |
| SDK-U1 | UNIT-stable-planning-binding | BHV-001, BHV-008 | A2 versioned and confirmation-independent |
| SDK-U2 | UNIT-full-confirmation-authority | BHV-002, BHV-003, BHV-004 | validated risk set + one canonical Full authority |
| SDK-U3 | UNIT-guarded-slice-activation | BHV-005, BHV-006, BHV-007 | same-batch start and later-slice membership |
| SDK-U4 | UNIT-binding-regression-release | BHV-008, BHV-009, BHV-010 | real lifecycle, compatibility and source/mirror/install proof |

Invariant ownership is fixed: SDK-U1 owns `INV-FSB-001..003`, SDK-U2 owns `INV-FSB-004..007`, SDK-U3 owns `INV-FSB-008..010`, and SDK-U4 owns `INV-FSB-011..012`.

## 3. Mandatory Impact Analysis

Before editing each production symbol, run repo-pinned GitNexus upstream impact and record the result:

```bash
node .gitnexus/run.cjs impact \
  --repo "$PWD" \
  --uid 'Function:guru-template/overlay/hooks/guru_task.py:_gate_digest' \
  --direction upstream --depth 4 --include-tests

node .gitnexus/run.cjs impact \
  --repo "$PWD" \
  --uid 'Function:guru-template/overlay/verify/guru_gate.py:_full_confirmation_batch_inputs' \
  --direction upstream --depth 4 --include-tests
```

Known baseline: `_full_confirmation_batch_inputs` is HIGH impact with 19 symbols and four execution processes. Stop and report if refreshed analysis is HIGH/CRITICAL or expands beyond the planned files.

## 4. 实施计划切片 SDK-U1: Stable Planning Artifact V2

Owner files:

- `guru-template/overlay/hooks/guru_task.py`
- `guru-template/overlay/verify/guru_delivery_policy.py`
- focused unit tests

Steps:

- [ ] Add a versioned/domain-separated stable planning payload and digest builder.
- [ ] Bind provider-asserted canonical repository namespace into A2 so cross-repository replay changes the stable identity.
- [ ] Reuse current requirements/detail artifact collectors and canonical policy/decision helpers; do not create a second parser.
- [ ] Exclude all requirements/detail confirmation records and downstream evidence from A2.
- [ ] Bind the reviewed expected-slice inventory digest into A2 before risk generation.
- [ ] Select Binding V2 only from task-level `gate-contract.json.start_binding.version`; downstream evidence may agree but cannot select or downgrade it.
- [ ] Register signed external `binding_adopted` state atomically with V2 contract creation/migration, before A2/risk generation; query it at every planning/start dispatch.
- [ ] Add one shared `PARENT_TASK_NOT_STARTABLE` denial consumed by check-start, Start Guard and before-start hook.
- [ ] Add explicit V2 risk binding field/schema; isolate legacy v1 verification and block migration-required v2-policy planning tasks.
- [ ] Make Start Guard compare selected risk A2 with recomputed A2.
- [ ] Keep complete task/session pre/post snapshots and legacy lifecycle CAS intact.
- [ ] Keep the repaired source dispatcher out of all SDK worker paths; a confirmed lock-anchor/runtime mismatch must block rather than switch runtime or infer legacy.
- [ ] Add exact unit tests proving confirm-independent digest stability and contract/review/artifact invalidation.

Rollback point: revert SDK-U1 as one source/test unit; no schema output may ship without its version dispatcher.

## 5. 实施计划切片 SDK-U2: Canonical Risk Set And Full Authorization

Owner files:

- `guru-template/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/guru_delivery_policy.py`
- `guru-template/overlay/hooks/guru_task.py`
- focused unit tests

Steps:

- [ ] Add one `validate_current_risk_packet_set()` shared by confirm, check-start and Start Guard.
- [ ] Load the A2-bound expected-slice inventory independently from observed risk files and require exact expected/observed ID equality.
- [ ] Validate JSON shape, canonical names, matching slice packet, task/route/policy/scope/A2, decisions and invariants before hashing.
- [ ] Build deterministic risk member rows and risk set digest.
- [ ] Add canonical `ConfirmationSubjectV2` with provider-asserted repository namespace and audience exactly `trellis-guru-full-start-v2:<repository_namespace>`, plus issuer/event/nonce/principal/time/task/route/policy/binding/selection/A2/artifact/inventory/member/scope/action/mode fields.
- [ ] Include actor/confirmed-at/via/turn-ref/user-quote digest and canonical per-slice action rows: selected `guarded_start`, selected `implement`, selected `check`, and later `implement`/`check`.
- [ ] Add one signed-receipt provider/verifier interface for configured terminal signer, signed platform user-turn receipt, or signed external attestation; raw TTY, bearer tokens and unverified agent text remain non-authoritative metadata.
- [ ] Keep trust configuration/signing keys outside task-writable artifacts and inject an isolated signer/verifier in tests.
- [ ] Add versioned canonical `guru_gates.full_confirmation` projection with receipt/domain/task/policy/selection/A2 bindings.
- [ ] Build the closed `AuthorizationGrantCoreV2` only from independently known immutable fields; exclude grant/authorization/batch/projection derived values and replay-time `verified_at`.
- [ ] Compute grant digest first, then derive authorization digest, batch id/digest and byte-identical canonical/compatibility projection bytes in an acyclic order.
- [ ] Keep requirements/detail compatibility projections but validate every shared authority field.
- [ ] Reject partial, missing, divergent, replayed or mixed-version records.
- [ ] Preserve strict TTY as the required acquisition channel where configured, but require its signer to issue a replay-verifiable receipt; allow soft/via-agent only with a trusted platform receipt.
- [ ] Enforce audience, exact subject, signature, validity window, revocation, single-use event/nonce and byte-identical idempotent retry.
- [ ] Add tamper tests where all mutable files and caller-provided SHA values are recomputed.

Rollback point: SDK-U2 cannot partially ship. If canonical authority/projections are not atomic and compatible, revert SDK-U2 and keep the task blocked.

## 6. 实施计划切片 SDK-U3: Attestation, Envelope And Later-Slice Membership

Owner files:

- `guru-template/overlay/verify/guru_delivery_policy.py`
- `guru-template/overlay/hooks/guru_task.py`
- `guru-template/overlay/verify/guru_supervise.py`
- focused unit tests

Steps:

- [ ] Extend/upgrade attestation and envelope to bind confirmation batch id/digest, authorization digest, risk set digest and selected risk digest.
- [ ] Define `ActivationContractPreimageV2` after C2/U2; bind E[i] to its digest rather than a future snapshot.
- [ ] Replace scalar allowed action with a canonical action-set digest; each E[i,action] carries one exact `{slice_id, action}` row and `authorized_action_row_digest`, not only the whole-set digest.
- [ ] Issue separate selected `guarded_start`, `implement` and `check` projections, and separate later `implement`/`check` projections.
- [ ] Validate selected risk membership before official start.
- [ ] Add a final stable + authorization CAS immediately before official subprocess invocation.
- [ ] Preserve post-start revalidation, exact status-only postcondition and compensation/manual recovery.
- [ ] Add an external monotonic adoption/activation registry record with domain/schema/repository/task namespace, sequence, predecessor, payload digest, state, attempt, time, provider/key and signature.
- [ ] Enforce provider head CAS for `binding_adopted -> activation_prepared -> activation_finalized|failed|compensated|manual_recovery_required`.
- [ ] Persist the local attempt journal as `prepared -> official_call_started -> official_returned -> verified` around the official call.
- [ ] Implement no-official-call `reconcile-start` for prepared crash windows: `aborted_pre_call`, exact finalize, one bounded compensation terminal result, or `manual_recovery_required`; never retry an ambiguous call-started attempt.
- [ ] Require signed audited legacy registration for pre-upgrade in-progress tasks; absence never selects legacy.
- [ ] Create E[selected,guarded_start] just in time before check-start and selected/later E[i,action] just in time before each implement/check worker preflight from the same preimage.
- [ ] Extend later-slice implement/check preflight to require `slice_id` membership in current Full authorization.
- [ ] Revalidate provenance, C2/U2 freshness, the requested action row, selection generation, expected inventory and E[i,action] immediately before every selected/later worker launch.
- [ ] Block any expected member added/changed/deleted/renamed after confirmation.
- [ ] Add cross-task, cross-batch, cross-selection and selected-slice replay tests.

Rollback point: if later-slice membership cannot be proven without changing Trellis Core, stop and return to design rather than weakening the contract.

## 7. 实施计划切片 SDK-U4: Canonical Lifecycle Regression And Compatibility

Owner files:

- `guru-template/overlay/verify/tests/test_start_guard.py`
- `guru-template/overlay/verify/tests/test_delivery_policy.py`
- `guru-template/overlay/verify/tests/run_tests.sh`
- `guru-template/overlay/verify/guru_mirror_integration.py`
- `guru-template/overlay/tests/apply_test.sh`

Required isolated two-member regression happy path:

```text
valid Full v2/high docs + review evidence + fixture contract expecting FIX-F1/FIX-F2
-> generate FIX-F1/FIX-F2 slice packets
-> production builder generates FIX-F1/FIX-F2 risk packets before confirmation
-> observed risk IDs equal the independently reviewed expected IDs
-> one replay-verifiable test-provider receipt writes the canonical authorization projection
-> attestation/envelope bind the same batch
-> real cmd_check_start returns PASS
-> real _artifact_binding accepts FIX-F1
-> start_with_guard reaches official fake start and verified attempt
-> FIX-F1 implement/check preflight proves its separate selected action rows
-> FIX-F2 implement/check preflight proves full authorization
```

Required negative matrix:

- [ ] Requirements/detail/contract/review-policy/decision inventory drift.
- [ ] Selected and unselected risk member drift.
- [ ] Malformed, extra, orphan, filename/slice mismatch and mixed-version risk files.
- [ ] Missing/unexpected slice versus the reviewed inventory, including a self-consistent smaller observed set.
- [ ] Task-level V2 discriminator retained while V2 evidence is removed or rewritten to request legacy fallback.
- [ ] V2 contract fully rolled back before start after external adoption; planning dispatch still blocks downgrade.
- [ ] Raw TTY, unverified agent quote/turn-ref, receipt signature/token/subject replay and provenance/projection divergence.
- [ ] Actor/time/via/turn/quote/action tamper and same receipt requesting a non-identical grant/batch.
- [ ] Generic bearer token rejection, wrong audience/issuer, expired/revoked receipt, event/nonce reuse and non-identical second batch.
- [ ] Confirmation authority/projection field tamper.
- [ ] Attestation/envelope rehash and cross-batch replay.
- [ ] Slice packet drift and route downgrade with all mutable SHA values recomputed.
- [ ] Lock/CAS race, post-start failure, after-start hook failure and compensation conflict.
- [ ] Prepared, official-call-started and official-returned crash windows reconcile deterministically without invoking official start a second time.
- [ ] Grant core self-reference/derived-field injection and replay-time verifier observation mutation cannot change canonical grant/projection bytes.
- [ ] Legacy Full v1 two-stage confirmation.
- [ ] Pinned bootstrap v1 runtime across SDK-U1..SDK-U4; repaired-source dispatch before the post-slice legacy receipt blocks.
- [ ] Any ordinary lock, gate-contract projection, installed runtime or per-worker evidence drift blocks against current Gate and projection checks.
- [ ] Coordinated rewrite of every task-local confirmation/PRD/lock/contract/runtime/worker field still blocks against the protected signature and root-owned external receipt.
- [ ] Post-slice `register-legacy-continuation` binds the bootstrap anchor receipt digest, original v1 start and completed check inventory, permits source verify/check-commit only and rejects implement/new-slice/V2 actions.
- [ ] Lite one requirements confirmation and no Full artifacts.
- [ ] Micro/Small dispatch with no Full confirmation, risk, attestation, envelope or activation snapshot.
- [ ] In-progress V2 registry/snapshot current, all task-local V2 markers removed, registry/task divergence, audited legacy registration and provenance-unknown blocking.
- [ ] Design parent with otherwise-valid evidence is denied by check-start/guard/hook and never reserves registry state or invokes official start.

Tests must call real production builders and real `cmd_check_start`; only official lifecycle side effects may use a controlled fake.

## 8. Spec And Operator Contract

- [ ] Update `.trellis/spec/cli/backend/guru-overlay-gates.md` with A2/expected-inventory/R/C2/U2/E/provenance contracts, error matrix and required tests.
- [ ] Update Guru overlay README/workflow text only where public commands or operator order changes.
- [ ] Document explicit regeneration guidance for Full v2 planning tasks with v1 evidence.
- [ ] Keep docs in English per repo spec; task-local artifacts may remain Chinese.
- [ ] Record that `START_READY` authorizes only guarded activation, not implementation or commit.

## 9. Source And Mirror Integration

`guru-template/` is the authoritative edit surface. Do not hand-edit package mirror files.

- [ ] Before sync, re-read current `pnpm --filter @devsc/trellis sync:guru:check` drift.
- [ ] Rebase/merge onto the separately reviewed synced baseline produced by the reinstall task, or otherwise prove every pre-existing mirror delta is independently owned.
- [ ] Implement `guru_mirror_integration.py guarded-sync` to validate the named owner artifact/commit/tree/output/review ids, invoke standard `pnpm -C packages/cli sync:guru`, compare actual package delta to the canonical mapping of the reviewed child source delta and write `verification/mirror-integration-proof.json` only on exact equality.
- [ ] Treat direct standard sync as non-authoritative: without a current proof, apply/install, V2 canary and repaired-source check-commit must block.
- [ ] Recompute proof inputs in `verify-proof`; task-writable proof bytes alone never authorize release.
- [ ] Run `pnpm --filter @devsc/trellis sync:guru:check`.
- [ ] Run apply/install fixture verification against a disposable target.
- [ ] Run `full_start_binding_v2_canary.py` with `CANARY-SELECTED/CANARY-LATER`, an external ephemeral signer/registry and persistent child evidence output.
- [ ] Retain a self-contained public evidence bundle with full signed receipt/grant, signed registry chain/head, public trust/revocation material, attempt journal and action results; destroy secret keys.
- [ ] Re-run `full_start_binding_v2_canary.py --verify-evidence <v2-canary.json>` offline after key destruction and require PASS before cleanup.
- [ ] After all SDK slice checks and implementation review, issue the signed audited legacy-continuation receipt from the verified external bootstrap anchor and original v1 start; never trust current task-local confirmation/lock alone. Use it with repaired-source `check-commit`, which also requires the current mirror proof.
- [ ] Do not sync the fix into Himora until source, package mirror and installed target checks are green.

## 10. Verification Commands

Focused:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s guru-template/overlay/verify/tests -p 'test_delivery_policy.py' -v

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s guru-template/overlay/verify/tests -p 'test_start_guard.py' -v
```

Full Guru overlay:

```bash
PYTHONDONTWRITEBYTECODE=1 bash guru-template/overlay/verify/tests/run_tests.sh
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_mirror_integration.py guarded-sync \
  --task-dir .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_mirror_integration.py verify-proof \
  --task-dir .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime \
  --consumer apply_install
bash guru-template/overlay/tests/apply_test.sh
pnpm --filter @devsc/trellis sync:guru:check
git diff --check
```

Before commit:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/hooks/guru_task.py register-legacy-continuation \
  --task-dir .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime \
  --runtime-lock .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime/verification/bootstrap-runtime-lock.json
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_mirror_integration.py verify-proof \
  --task-dir .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime \
  --consumer check_commit
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_gate.py check-commit \
  .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime
node .gitnexus/run.cjs detect-changes \
  --repo "$PWD" --scope compare --base-ref main
git status --short
git diff --name-status
git diff --cached --name-status
```

No completion claim is valid unless the canonical lifecycle, full drift matrix, compatibility paths, mirror/apply checks and detect-changes output are all current.

## 11. Review Gates

- [ ] Requirements structure and semantic review current.
- [ ] Overview review: two current-digest clean runs.
- [ ] Detail review: two current-digest clean runs with `--deletion-audit none`; no implementation diff exists at planning review time.
- [ ] One Full confirmation binds current requirements, all risk members and irreversible design.
- [ ] Implementation review is check-only and independent from the implementation sub-agent.
- [ ] External/harness verifier may recommend pass; executor must not write final verifier status.

Bootstrap Gate:

- [ ] Parent review package current and user explicitly approves a separate bootstrap child.
- [ ] Linked child contract is legacy Full v1/high with no V2 marker; its own requirements/detail confirmations and reviews are current.
- [ ] Parent is never started and no child production edit occurs before child activation.
- [ ] After child implementation/install, a disposable V2 canary passes before parent integration or Himora sync.

## 12. Final Integration Back To Himora

After the SDK fix is reviewed and installed into the target project:

- [ ] Verify installed runtime file digests match the reviewed SDK output.
- [ ] Regenerate target `HIM-S1/HIM-S2` risk packets under Binding V2.
- [ ] Present exactly one Full confirmation batch to the user.
- [ ] Run target `guru_gate.py check-start`.
- [ ] Run guarded start binding for selected `HIM-S1`.
- [ ] Verify `HIM-S2` full authorization preflight before any HIM-S2 worker.
- [ ] Only then resume the media progress implementation task.

## 13. 阻塞与偏差处理 (Stop Conditions)

Stop and return to planning when:

- a new dependency creates another reverse edge into A2 or risk packets;
- the parent would need direct start, or bootstrap child scope/contract cannot remain independently authorized legacy Full v1/high;
- protected bootstrap signer/root-owned trust or external anchor receipt cannot be established before child requirements confirmation;
- any SDK worker resolves repaired source or a runtime digest different from the pinned pre-repair v1 lock before all slice checks;
- Full v2 cannot distinguish legacy/mixed evidence;
- canonical confirmation/projections cannot be written atomically;
- later-slice membership would require bypassing check-start or modifying Trellis Core;
- external receipt/activation registry trust configuration cannot be kept outside task-writable artifacts;
- package sync would absorb unrelated 38-file drift;
- guarded sync/proof is bypassed or cannot make apply/install, canary and repaired-source check-commit independently fail closed;
- any HIGH/CRITICAL impact expands outside the approved runtime/spec/test scope.
