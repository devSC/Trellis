# Full/high Start Guard Binding Cycle Implementation Plan

实施计划: four bounded SDK slices execute serially.

## 1. Execution Boundary

The parent remains an unstarted umbrella. This child is the only implementation
SSOT. Production source edits begin only after the child reaches `in_progress`.
执行范围 is limited to the contract-approved Guru source and tests.

The current task does not implement protected signers, root launchers, external
registries/receipts, or malicious workspace-agent defenses.

## 2. Preconditions

- [ ] Child contract remains `full_chain/high` and
  `guru-risk-contract-v1` for its own bootstrap activation.
- [ ] Parent remains planning and is not passed to `task.py start`.
- [ ] Requirements, Overview, Detail, and Implement structural Gates pass.
- [ ] Required current reviews and confirmations are recorded.
- [ ] User separately approves child start.
- [ ] Production edits stay within contract scope.
- [ ] The 38 mirror drifts are recorded as sync/install/canary-only blockers.

## 2.1 Slice To Unit Trace

| Slice | UNIT | BHV | Result |
| --- | --- | --- | --- |
| SDK-U1 | UNIT-stable-planning-binding | BHV-001 | versioned stable Start Guard digest |
| SDK-U2 | UNIT-full-confirmation-authority | BHV-002 | unchanged independent Full batch freshness |
| SDK-U3 | UNIT-guarded-slice-activation | BHV-003 | selected binding and lifecycle CAS preserved |
| SDK-U4 | UNIT-binding-regression-release | BHV-004 | chronological regression and compatibility proof |

## 3. Mandatory Impact Analysis

Completed before production edits:

- `_gate_digest`: LOW, 5 impacted symbols, one affected process.
- `_full_confirmation_batch_inputs`: HIGH, 19 impacted symbols, four affected
  processes.

Refresh impact if implementation expands beyond the approved functions/tests.

## 4. SDK-U1 Stable V2 Digest

- [ ] Update `guru_task._gate_digest()` with an explicit v2 branch selected
  from `gate-contract.json.policy_version`.
- [ ] V2 binds schema, task chain flags, review runs, and contract digest.
- [ ] V2 excludes requirements/detail confirmation record contents.
- [ ] Non-v2 executes the byte-compatible legacy payload.
- [ ] Add before/after confirmation and v1 compatibility tests.

Rollback: revert the v2 branch and its tests as one unit.

## 5. SDK-U2 Full Batch Freshness

- [ ] Keep `_full_confirmation_batch_inputs()` as the independent requirements,
  detail, and complete risk-byte-set recomputation.
- [ ] Define canonical `FullConfirmationProjectionV2` over all existing
  confirmation metadata and current batch inputs.
- [ ] Store one domain-separated `confirmation_projection_digest` in both
  requirements/detail records.
- [ ] Require exact allowed fields and exact peer equality except
  `artifact_digest`; validate TTY vs agent optional-field combinations.
- [ ] Keep `_full_confirmation_batch_problem()` as `check-start` freshness
  enforcement.
- [ ] Add/retain risk changed/added/removed, requirements/detail drift, and every
  confirmation metadata mutation/divergence test.
- [ ] Do not add a new provider or authorization schema.

Rollback: no production change is expected unless the chronological regression
finds a directly related missing freshness assertion.

## 6. SDK-U3 Guarded Binding

- [ ] Keep `_artifact_binding()` selected slice/risk/detail/decision checks.
- [ ] Keep high-risk attestation and envelope checks.
- [ ] Keep pre-lock, lock, final pre-call, post-return, after-start, and
  compensation behavior.
- [ ] Add only the assertions needed to prove the new stable digest composes
  with existing guarded binding.

Rollback: no lifecycle redesign is permitted.

## 7. SDK-U4 Chronological Regression

Required order:

```text
create real Full v2/high fixture without confirmation records
-> compute stable v2 digest
-> build real risk packet
-> record one real Full confirmation batch
-> assert stable digest unchanged
-> run real Full batch freshness/check-start
-> run real Start Guard artifact binding/guarded lifecycle
-> assert verified result
```

Negative cases:

- [ ] requirements artifact drift blocks `check-start`;
- [ ] detail artifact drift blocks `check-start`;
- [ ] risk packet changed/added/removed blocks `check-start`;
- [ ] confirmation actor/time/scope/action/prompt/batch/input/mode/via/turn/quote
  mutation or requirements/detail divergence blocks `check-start`;
- [ ] selected risk drift blocks guarded binding;
- [ ] attestation drift blocks guarded binding;
- [ ] envelope drift blocks guarded binding;
- [ ] legacy v1 confirmation mutation retains legacy digest behavior.

## 8. Source Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s guru-template/overlay/verify/tests -p 'test_delivery_policy.py' -v

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s guru-template/overlay/verify/tests -p 'test_start_guard.py' -v

PYTHONDONTWRITEBYTECODE=1 bash guru-template/overlay/verify/tests/run_tests.sh
git diff --check
```

## 9. Mirror Release Boundary

Source repair and source tests do not wait for mirror zero-drift.

These remain blocked while the known 38 drifts are unresolved:

- package mirror sync;
- apply/install verification;
- installed-runtime canary;
- target Himora installation.

Do not hand-edit the package mirror and do not absorb those drifts into this
source fix.

## 10. Review And Stop Conditions

- [ ] Planning reviews are current for the narrowed digest.
- [ ] Child requirements/detail confirmations are current.
- [ ] Separate child start approval is recorded.
- [ ] Focused and full source tests pass.

Stop only if a discovery directly violates a core invariant in BHV-001..BHV-004.
Do not reopen deferred threat-model planning in this task.

阻塞与偏差: record only a direct core-invariant violation or a source-test
failure; mirror drift remains a release-only deviation.
