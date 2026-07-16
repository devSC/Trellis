# Bootstrap Full Start Binding V2 Runtime Implementation Plan

## 1. 执行边界 (Execution Boundary)

The parent remains planning forever. This child is the implementation target, but remains planning until its own legacy Full v1 requirements/detail confirmations and double-clean reviews are current and the user separately approves child start.

No production runtime, spec, package mirror or test file may be edited before child activation. The current user quote authorized child creation/planning only.

## 2. Preconditions

- [ ] Verify parent status is planning and child is linked as its only bootstrap implementation child.
- [ ] Verify child contract is `full_chain/high`, `guru-risk-contract-v1`, scope-bounded and contains no V2 marker.
- [ ] Verify child scope includes generated-only `packages/cli/src/templates/guru/overlay`, has no artificial file-count cap, and prohibits hand edits/unrelated mirror drift.
- [ ] Pin the current reviewed parent requirements/design baseline before child final confirmation.
- [ ] Complete child requirements, overview and detail Gates under legacy ordering.
- [ ] Generate SDK unit risk/guard evidence only after legacy detail confirmation, so current Start Guard digest is satisfiable.
- [ ] Before requirements confirmation, verify `verification/bootstrap-runtime-lock.json` hashes to child PRD literal `62074a1fef9e68d758a57dbebb26a4bd9058839d529c89d77a42e0eff21397a7` and the matching gate-contract projection.
- [ ] Generate canonical `BootstrapRuntimeAnchorSubjectV1` with current child requirements digest, then have the user sign it interactively with a new passphrase/hardware-protected OpenSSH key. Reject the current unencrypted agent-usable `~/.ssh/id_rsa`.
- [ ] Require the user to install the allowed-signers policy and single-assignment subject/signature receipt root-owned/read-only at the contract paths; verify signature, root ownership/mode, audience, time, event/nonce and exact subject before requirements confirmation.
- [ ] Obtain separate explicit child start approval; do not reuse parent topology approval.
- [ ] Re-read specs and current source/tests before every production slice.
- [ ] Before every SDK implement/check worker, verify the root-owned signed bootstrap receipt and take expected values from its subject, then run installed-v1 `check-implementation` and compare requirements/PRD/lock/contract/base/runtime projections. Never apply/install repaired source into this active worktree before all SDK slice checks and implementation review complete.
- [ ] Record baseline focused/full tests, apply test and existing mirror drift.
- [ ] Validate `verification/mirror-baseline.json` against the live 38-drift check and keep sync/install blocked until the named owner zero-drift artifact exists and its reviewed commit is merged.

Required `bootstrap-worker-preflight` before every SDK implement/check dispatch:

```bash
ssh-keygen -Y verify \
  -f /etc/trellis-guru/bootstrap-allowed-signers \
  -I devSC \
  -n trellis-guru-bootstrap-v1 \
  -s /var/db/trellis-guru/bootstrap-anchors/github.com_devSC_Trellis/bootstrap-full-start-binding-v2-runtime/subject.json.sig \
  < /var/db/trellis-guru/bootstrap-anchors/github.com_devSC_Trellis/bootstrap-full-start-binding-v2-runtime/subject.json
stat -f '%Su:%Sg:%Lp' \
  /etc/trellis-guru/bootstrap-allowed-signers \
  /var/db/trellis-guru/bootstrap-anchors/github.com_devSC_Trellis/bootstrap-full-start-binding-v2-runtime/subject.json \
  /var/db/trellis-guru/bootstrap-anchors/github.com_devSC_Trellis/bootstrap-full-start-binding-v2-runtime/subject.json.sig
python3 .trellis/scripts/guru/guru_gate.py check-implementation \
  .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime
shasum -a 256 \
  .trellis/tasks/07-16-bootstrap-full-start-binding-v2-runtime/verification/bootstrap-runtime-lock.json
git rev-parse HEAD
git rev-parse HEAD:.trellis/scripts/guru
git diff --exit-code HEAD -- .trellis/scripts/guru
git status --short -- .trellis/scripts/guru
```

The orchestrator first requires a valid SSH signature from the root-owned allowed-signers policy and `root:wheel` ownership with no group/other/user write bit on the policy, subject and signature. It takes expected repository/task/requirements/lock/base/runtime values only from that subject. It then requires, respectively: `IMPLEMENTATION_READY`, lock SHA-256 `62074a1fef9e68d758a57dbebb26a4bd9058839d529c89d77a42e0eff21397a7`, base commit `54f3f407d4143577f40f38845ea9f6d55f3253d9`, runtime tree `0d25fca9474b17b0bc1d6db4301f932352cf395a`, an empty tracked diff and empty short status including untracked files. Any mismatch means no worker launch.

## 2.1 实施计划切片 To Unit Trace

| Slice | UNIT | BHV | Result |
| --- | --- | --- | --- |
| SDK-U1 | UNIT-stable-planning-binding | BHV-002, BHV-009 | stable A2 + authoritative dispatch |
| SDK-U2 | UNIT-full-confirmation-authority | BHV-003, BHV-004, BHV-005 | exact risk set + signed receipt/projections |
| SDK-U3 | UNIT-guarded-slice-activation | BHV-006, BHV-007, BHV-008 | preimage + registry/snapshot + CAS |
| SDK-U4 | UNIT-binding-regression-release | BHV-001, BHV-009, BHV-010 | bootstrap/compatibility/lifecycle/release proof |

## 3. Mandatory Impact Analysis

Before editing every production symbol, run repo-pinned upstream impact. Known `_full_confirmation_batch_inputs` baseline is HIGH with 19 impacted symbols and four processes; warn and stop if refreshed risk expands beyond approved files.

Required first targets:

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

## 4. SDK-U1 Stable Binding And Dispatch

- [ ] Add domain-separated `StablePlanningArtifactV2` and canonical digest.
- [ ] Bind provider-asserted canonical repository namespace into A2.
- [ ] Bind artifact, policy, decision, expected-inventory and review facts.
- [ ] Exclude confirmation, receipt, E[i], registry and lifecycle state.
- [ ] Select planning algorithm only from task contract.
- [ ] Register signed external `binding_adopted` state atomically with V2 contract creation/migration and query it before A2/risk and every start dispatch.
- [ ] Select in-progress algorithm only from signed external V2 activation or audited legacy registration.
- [ ] Preserve child legacy contract and block any in-place child upgrade.
- [ ] Keep modified source dispatcher out of SDK-U2/U3/U4 worker paths; runtime-lock drift blocks without inferring or minting legacy provenance.
- [ ] Add stability, drift, migration and total-marker-deletion tests.

Rollback: SDK-U1 ships as one source/test unit or is fully reverted.

## 5. SDK-U2 Exact Risk Set And Signed Authorization

- [ ] Add one shared `validate_current_risk_packet_set()`.
- [ ] Require exact expected/observed ids and validate every packet/slice/policy/decision invariant.
- [ ] Define canonical `ConfirmationSubjectV2` with provider-asserted repository namespace and audience exactly `trellis-guru-full-start-v2:<repository_namespace>`.
- [ ] Sign actor/time/via/turn/quote digest and exact action rows: selected `guarded_start`, selected `implement`, selected `check`, and later `implement`/`check`.
- [ ] Add signed terminal, signed platform user-turn and signed external-attestation provider adapters behind one verifier.
- [ ] Keep signing keys, trust lookup and revocation outside task artifacts.
- [ ] Verify signature, audience, exact subject, time, revocation and event/nonce uniqueness.
- [ ] Make identical retry byte-identical; changed subject requires a new receipt.
- [ ] Build the closed `AuthorizationGrantCoreV2` only from independently known immutable fields; exclude grant/authorization/batch/projection derived values and replay-time `verified_at`.
- [ ] Compute grant digest first, then derive authorization digest, batch id/digest and byte-identical canonical/compatibility projections in an acyclic order.
- [ ] Write canonical and compatibility projections atomically.
- [ ] Add malformed set, receipt and projection tamper tests with all mutable digests recomputed.

Rollback: no receipt/projection schema ships partially.

## 6. SDK-U3 Activation Preimage, Registry And CAS

- [ ] Define precomputable `ActivationContractPreimageV2`.
- [ ] Bind canonical authorized-action-set digest into the preimage and one exact `{slice_id, action}` row plus `authorized_action_row_digest` into each E[i,action].
- [ ] Issue separate selected `guarded_start`, `implement` and `check` projections and separate later `implement`/`check` projections.
- [ ] Bind attestation/E[i] to preimage, authorization, risk set and member.
- [ ] Issue E[selected,guarded_start] before check-start and selected/later E[i,action] before each implement/check worker preflight.
- [ ] Add external monotonic adoption/activation records with repository/task namespace, sequence, predecessor, payload digest, state, attempt, time, provider/key and signature.
- [ ] Enforce provider-head CAS for `binding_adopted -> activation_prepared -> activation_finalized|failed|compensated|manual_recovery_required`.
- [ ] Persist exact local activation snapshot and compare it to the signed registry receipt.
- [ ] Persist the local attempt journal as `prepared -> official_call_started -> official_returned -> verified`.
- [ ] Implement no-official-call `reconcile-start` with explicit aborted-pre-call, exact-finalize, bounded-compensation and manual-recovery outcomes; never re-invoke an ambiguous call-started attempt.
- [ ] Preserve pre-lock, lock, final pre-call, post-return, after-start and compensation contracts.
- [ ] Require full later-slice receipt/authorization/member/registry/snapshot validation.
- [ ] Add total-marker deletion, registry disagreement, race and compensation tests.
- [ ] Add a shared design-parent hard denial used by check-start, Start Guard and before-start hook.

Rollback: stop if external monotonic provenance would require Trellis Core modification or task-local trust.

## 7. SDK-U4 Real Regression And Release

Canonical fixture:

```text
valid V2 fixture expecting FIX-F1/FIX-F2
-> real slice/risk builders before confirmation
-> exact expected/observed set
-> signed test-provider receipt
-> deterministic grant/batch/projections with explicit slice actions
-> real confirm
-> just-in-time E[FIX-F1]
-> real check-start
-> real _artifact_binding
-> start_with_guard with controlled official side effect
-> external registry finalized + local snapshot exact
-> FIX-F1 implement/check preflight proves separate selected action rows
-> FIX-F2 full authorization preflight
```

Negative matrix:

- [ ] Stable artifact, expected inventory, selected/unselected member drift.
- [ ] Malformed, missing, unexpected, duplicate, orphan, symlink and mixed risk evidence.
- [ ] Wrong issuer/audience/key/signature, expired/revoked receipt and event/nonce reuse.
- [ ] Actor/time/via/turn/quote/action tamper and non-identical second batch from the same receipt.
- [ ] Canonical/projection divergence and cross-task/selection replay.
- [ ] E/preimage, registry/snapshot and task/session CAS drift.
- [ ] Grant core derived-field/self-reference injection and replay-time observation mutation.
- [ ] Prepared/call-started/returned crash windows reconcile deterministically without a duplicate official call.
- [ ] All task-local V2 markers deleted while registry remains V2.
- [ ] Legacy Full v1, Lite, Micro/Small and audited legacy registration.
- [ ] Pinned pre-repair v1 runtime across all SDK workers; any mid-run source/runtime replacement blocks.
- [ ] Any ordinary lock, gate-contract projection, installed runtime or per-worker digest drift blocks against current Gate and projection checks.
- [ ] Coordinated rewrite of PRD, requirements confirmation, lock, contract, runtime and worker evidence still blocks because the protected signer/root-owned external receipt cannot be replaced.
- [ ] Post-slice audited legacy registration binds the bootstrap anchor receipt digest, original v1 start and completed check inventory, permits source verify/check-commit only and rejects implement/new-slice/V2 actions.
- [ ] Parent/child bootstrap isolation.
- [ ] Otherwise-valid parent evidence is denied by all three start surfaces with zero registry/official effects.

Tests must call real target boundaries; only official lifecycle side effects may be controlled.

## 8. Spec And Operator Contract

- [ ] Update `.trellis/spec/cli/backend/guru-overlay-gates.md` with bootstrap, A2, expected inventory, receipt, confirmation, preimage, registry, dispatch and error contracts.
- [ ] Update operator docs only for actual command/order changes.
- [ ] Document trust-provider configuration without persisting secrets.
- [ ] Document migration-required and audited legacy registration.
- [ ] State that `START_READY` permits guarded activation only.

## 9. Source, Package And Install

- [ ] Re-read current `sync:guru:check` drift before sync.
- [ ] Require the named owner artifact with reviewed zero-drift commit/tree/output digests/review ids; merge exactly that commit before sync.
- [ ] Implement `guru-template/overlay/verify/guru_mirror_integration.py` with `guarded-sync` and `verify-proof`.
- [ ] `guarded-sync` verifies owner artifact/commit ancestry/tree/output/review ids and package baseline, invokes the standard sync command, then writes `verification/mirror-integration-proof.json` only when actual package rows/content exactly equal the canonical mapping of this child's reviewed source delta.
- [ ] Never hand-edit package mirror. Direct standard sync without a current proof is non-authoritative and cannot pass apply/install, canary or repaired-source check-commit.
- [ ] `verify-proof` recomputes live owner/source/package/command facts; task-writable proof bytes alone never authorize release.
- [ ] Run package sync check and disposable apply/install verification.
- [ ] Create a disposable Full v2 canary after install.
- [ ] Run `full_start_binding_v2_canary.py` with exact `CANARY-SELECTED/CANARY-LATER`, ephemeral external signer/registry and output `verification/v2-canary.json`.
- [ ] Persist the self-contained public receipt/grant, registry chain/head, public trust/revocation, attempt journal and action evidence; destroy every secret key.
- [ ] Run `full_start_binding_v2_canary.py --verify-evidence verification/v2-canary.json` offline after secret destruction and require PASS before cleanup.
- [ ] After all SDK slice checks and implementation review, run `register-legacy-continuation` from the verified root-owned bootstrap anchor plus original v1 start, never current task-local confirmation/lock alone. The signed receipt permits repaired-source verify/check-commit only.
- [ ] Block parent integration and Himora sync until canary passes.

## 10. Verification Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s guru-template/overlay/verify/tests -p 'test_delivery_policy.py' -v

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s guru-template/overlay/verify/tests -p 'test_start_guard.py' -v

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
  --repo "$PWD" --scope compare --base-ref codex/preserve-guru-target-wip-75887690
git status --short
git diff --name-status
git diff --cached --name-status
```

## 11. Review、阻塞与偏差 Gates

- [ ] Parent review baseline current.
- [ ] Child requirements confirmation current under strict legacy Gate.
- [ ] Child Overview clean x2.
- [ ] Child Detail clean x2 with `--deletion-audit none`; no implementation diff exists at planning review time.
- [ ] Separate child start approval recorded.
- [ ] Independent implementation review and verifier candidate recommendation current.

Stop and return to planning if:

- parent would need start;
- child acquires any V2 activation marker;
- protected bootstrap signer/root-owned trust or external anchor receipt is absent, invalid, mutable or divergent;
- any SDK worker resolves repaired source or a runtime digest different from the pinned pre-repair v1 lock before all slice checks;
- signed receipt or registry trust would be task-local;
- canonical lifecycle needs a mocked target boundary;
- Trellis Core modification is required;
- package sync absorbs unrelated drift;
- guarded sync/proof can be bypassed by apply/install, canary or repaired-source check-commit;
- refreshed HIGH/CRITICAL impact exceeds approved scope.

## 12. Final Handoff

After V2 canary success:

- [ ] Bind reviewed source/package/install digests into parent integration evidence.
- [ ] Install the exact runtime in Himora.
- [ ] Generate `HIM-S1/HIM-S2` under Binding V2.
- [ ] Present one confirmation subject/batch to the user.
- [ ] Run target check-start, guarded HIM-S1 start and HIM-S2 full authorization preflight.
- [ ] Only then resume media-progress implementation.
