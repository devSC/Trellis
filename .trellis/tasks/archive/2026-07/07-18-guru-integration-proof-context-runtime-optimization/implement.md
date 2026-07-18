# Guru Integration Proof Context Runtime Optimization Implementation Plan

## Planning Boundary

This file is an execution plan only. No implementation starts until the parent
requirements and design are reviewed, the user approves the complete planning
package, the Full/high contract and packets are current, and `task.py start` is
run through the official Gate.

The parent task owns no production path. The four child directories are
planning, allocation, and rollback records only: the parent task and its four
slice packets remain the sole lifecycle authority. Do not run `task.py start`
against a child directory. After final parent approval, start only the parent,
publish the serial baseline receipt, then dispatch the two Wave 1 packets from
isolated worktrees at the same baseline commit.

## 计划与切片 (Slice Planning Audit)

| Slice | Owner unit | Covered units | Mutable ownership | Depends on | Parallel wave | Independent commit and rollback |
| --- | --- | --- | --- | --- | --- | --- |
| SL-BASELINE-PARITY | UNIT-baseline-parity | UNIT-baseline-parity | three canonical runtime files plus canonical lifecycle test | none | Wave 0, serial | restores canonical authority without changing package behavior; revert before descendants |
| SL-PROOF-SUPERVISOR | UNIT-proof-supervisor | UNIT-proof-supervisor | canonical supervisor plus focused proof-context test | SL-BASELINE-PARITY | Wave 1 with verdict evidence | reversible proof projection, admission, budgets, and orchestration |
| SL-VERDICT-EVIDENCE | UNIT-verdict-evidence | UNIT-verdict-evidence | canonical review-record plus focused retry test | SL-BASELINE-PARITY | Wave 1 with proof supervisor | reversible retry identity/evidence/normalization contract |
| SL-INTEGRATION | UNIT-integration-proof | UNIT-integration-proof | bounded canonical Shell test plus seven exact package peers | SL-PROOF-SUPERVISOR, SL-VERDICT-EVIDENCE | Wave 2, serial | generated parity and combined proof; revert first |

Wave 1 mutable overlap is zero. Both Wave 1 slices consume the frozen API in
`design.md` and have no implementation dependency on each other. Wave 0
intentionally evolves the two later runtime files first to absorb pre-existing
canonical drift; its current receipt is the frozen baseline dependency rather
than a claim of same-wave independence.

Shared package generation, compatibility checks, receipt-currentness checks,
and the final full lifecycle regression belong only to SL-INTEGRATION. Formal
staged review, commit, and receipt publication are serial in the control
worktree even when Wave 1 implementation runs concurrently.

After the baseline receipt is current, create one isolated worktree for each
Wave 1 packet at the same baseline commit. Each worker consumes its exact parent
packet plus the corresponding child context, writes only its owned paths, runs
only packet-focused checks, and returns an owned-path patch plus focused
evidence. Workers do not stage, commit, publish receipts, write task evidence,
or re-plan ownership. The control worktree applies those patches and serially
publishes the formal reviews, commits, and receipts.

### Exact Integration Write Scope

- `guru-template/overlay/tests/integration_proof_runtime_test.sh`
- `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_review_record.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/tests/test_slice_commit_lifecycle.py`
- `packages/cli/src/templates/guru/overlay/verify/tests/test_integration_proof_context.py`
- `packages/cli/src/templates/guru/overlay/verify/tests/test_integration_verdict_retry.py`
- `packages/cli/src/templates/guru/overlay/tests/integration_proof_runtime_test.sh`

Integration review coverage is the 14-path union in `SL-INTEGRATION.json`;
coverage does not authorize rewriting the six ordinary canonical paths.

## Critical/High Decision Inventory

<!-- GURU:RISK_DECISION_INVENTORY:START -->
```json
{
  "schema_version": 1,
  "task_id": "guru-integration-proof-context-runtime-optimization",
  "scope": {
    "selected_slice_id": "SL-BASELINE-PARITY",
    "official_start_authority": "selected_slice_only",
    "later_slice_authority": "supervisor_fail_closed"
  },
  "slices": {
    "SL-BASELINE-PARITY": [
      {
        "decision_id": "DEC-BASELINE-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Restore canonical authority in a separate serial prerequisite by copying current package runtime bytes before feature work.",
        "alternatives": [
          "Modify package runtime only and retain canonical drift.",
          "Mix historical parity and feature changes in one commit."
        ],
        "impact": "Prevents later template synchronization from overwriting the optimization and gives historical drift an independent review and rollback boundary.",
        "irreversible": false,
        "invariant_ids": [
          "INV-RT-001",
          "INV-RT-002"
        ],
        "required": true,
        "resolution": {
          "choice": "Use the independent RT-BASELINE-PARITY prerequisite.",
          "evidence": "User confirmed OQ-001 on 2026-07-18; PRD DEC-001 records the decision."
        },
        "source_refs": [
          {
            "artifact_key": "baseline-parity.md",
            "anchor": "GURU-DECISION:DEC-BASELINE-001"
          }
        ]
      }
    ],
    "SL-PROOF-SUPERVISOR": [
      {
        "decision_id": "DEC-BUDGET-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Hard-block an eligible Integration prompt before provider dispatch when either final serialized budget is exceeded.",
        "alternatives": [
          "Warn and continue with an over-budget proof prompt.",
          "Fallback to the current full-context reviewer."
        ],
        "impact": "Makes the performance contract deterministic and prevents projection regressions from recreating the observed high-token review.",
        "irreversible": false,
        "invariant_ids": [
          "INV-RT-005"
        ],
        "required": true,
        "resolution": {
          "choice": "Enforce both limits before channel or provider creation with no fallback.",
          "evidence": "User confirmed OQ-002 on 2026-07-18; PRD DEC-002 records the decision."
        },
        "source_refs": [
          {
            "artifact_key": "proof-supervisor.md",
            "anchor": "GURU-DECISION:DEC-BUDGET-001"
          }
        ]
      },
      {
        "decision_id": "DEC-SCOPE-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Enable proof projection only for Full/high schema-v2 Integration in the first release.",
        "alternatives": [
          "Change every v2 ordinary review in the same task.",
          "Change all routes and review schemas at once."
        ],
        "impact": "Confines the runtime and compatibility blast radius to the measured Integration bottleneck.",
        "irreversible": false,
        "invariant_ids": [
          "INV-RT-003"
        ],
        "required": true,
        "resolution": {
          "choice": "Keep ordinary v2 and every lower/legacy route unchanged.",
          "evidence": "User confirmed OQ-003 on 2026-07-18; PRD DEC-003 records the decision."
        },
        "source_refs": [
          {
            "artifact_key": "proof-supervisor.md",
            "anchor": "GURU-DECISION:DEC-SCOPE-001"
          }
        ]
      },
      {
        "decision_id": "DEC-TOKEN-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Estimate tokens as ceil of complete UTF-8 prompt bytes divided by three without adding a tokenizer dependency.",
        "alternatives": [
          "Add a provider-specific tokenizer dependency.",
          "Measure only selected context fragments."
        ],
        "impact": "Keeps admission offline, reproducible, provider-independent, and conservative.",
        "irreversible": false,
        "invariant_ids": [
          "INV-RT-005"
        ],
        "required": true,
        "resolution": {
          "choice": "Enforce 98304 bytes and 25000 estimated tokens using the bytes/3 formula.",
          "evidence": "User confirmed OQ-006 on 2026-07-18; PRD DEC-006 records the decision."
        },
        "source_refs": [
          {
            "artifact_key": "proof-supervisor.md",
            "anchor": "GURU-DECISION:DEC-TOKEN-001"
          }
        ]
      }
    ],
    "SL-VERDICT-EVIDENCE": [
      {
        "decision_id": "DEC-RETRY-AUDIT-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Persist raw semantic output and retry identity in a separate append-only evidence stream and publish only the final official verdict.",
        "alternatives": [
          "Write an intermediate official blocked row before retry.",
          "Discard malformed raw semantic output."
        ],
        "impact": "Preserves a complete audit chain without creating recoverable official false failures or receipt churn.",
        "irreversible": false,
        "invariant_ids": [
          "INV-RT-007"
        ],
        "required": true,
        "resolution": {
          "choice": "Separate immutable retry evidence from the single final official row.",
          "evidence": "User confirmed OQ-004 on 2026-07-18; PRD DEC-004 records the decision."
        },
        "source_refs": [
          {
            "artifact_key": "verdict-evidence.md",
            "anchor": "GURU-DECISION:DEC-RETRY-AUDIT-001"
          }
        ]
      },
      {
        "decision_id": "DEC-RETRY-LIMIT-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Allow at most one serialization-only provider retry for each unchanged RetryIdentity.",
        "alternatives": [
          "Retry formatting until a valid envelope appears.",
          "Never retry a recoverable envelope error."
        ],
        "impact": "Places a hard upper bound on formatting repair calls while retaining one recovery opportunity.",
        "irreversible": false,
        "invariant_ids": [
          "INV-RT-007",
          "INV-RT-008"
        ],
        "required": true,
        "resolution": {
          "choice": "One formatting attempt, then one final blocked row and stop.",
          "evidence": "User confirmed OQ-005 on 2026-07-18; PRD DEC-005 records the decision."
        },
        "source_refs": [
          {
            "artifact_key": "verdict-evidence.md",
            "anchor": "GURU-DECISION:DEC-RETRY-LIMIT-001"
          }
        ]
      }
    ],
    "SL-INTEGRATION": []
  }
}
```
<!-- GURU:RISK_DECISION_INVENTORY:END -->

## 执行步骤 (Execution)

The following child sections are the ordered execution plan. Each child must
stop at its declared review/commit/receipt boundary before its dependents become
eligible.

## Child 1: RT-BASELINE-PARITY

### Dependency

None. This child must commit before either runtime child starts.

### Mutable Ownership

- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/guru_review_record.py`
- `guru-template/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/tests/test_slice_commit_lifecycle.py`

### Read-Only Inputs

- the four matching package runtime/test paths
- `packages/cli/scripts/sync-guru-template.js`
- parent `prd.md` and `design.md`

### Steps

1. Reconfirm package runtime lifecycle tests are green before copying.
2. Copy the exact package bytes to the four canonical paths.
3. Prove all four pairs are byte-identical.
4. Run `py_compile` on the three canonical and three package runtime files.
5. Run the canonical and package lifecycle test entrypoints as baseline
   compatibility executions; record them as `baseline_compatibility_runs`.
6. Confirm package runtime bytes did not change in this child.
7. Run GitNexus detect-changes, formal staged review, commit, and receipt.

### Rollback

Revert this child only before runtime children start. After they start, baseline
rollback requires reverting all descendants first.

## Child 2: RT-PROOF-SUPERVISOR

### Dependency

Requires current `RT-BASELINE-PARITY` receipt.

### Mutable Ownership

- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/tests/test_integration_proof_context.py`

### Frozen Read Contract

Consumes the existing Gate receipt validators and the verdict-evidence function
signatures frozen in parent `design.md`. It may not edit Gate or review-record
runtime.

### Steps

1. Add Integration proof eligibility without changing ordinary/v1 routing.
2. Implement current ordinary receipt admission and union calculation.
3. Implement canonical/package peer projection using existing managed-root
   mapping rules.
4. Emit receipt, peer, requirements/design, deterministic, and diff proofs.
5. Serialize the complete brief and enforce the byte/token budget before plan
   execution.
6. Make the proof reviewer plan inject zero files/JSONLs and reject source
   probes for a clean verdict.
7. Orchestrate at most one formatting-only retry through the frozen
   review-record interface.
8. Add focused positive, negative, compatibility, budget, and call-count tests.
9. Run focused tests, `py_compile`, GitNexus detect-changes, formal staged
   review, commit, and receipt.

### Focused Checks

```bash
python3 -m py_compile guru-template/overlay/verify/guru_supervise.py
python3 -m unittest guru-template/overlay/verify/tests/test_integration_proof_context.py
git diff --check -- guru-template/overlay/verify/guru_supervise.py guru-template/overlay/verify/tests/test_integration_proof_context.py
```

### Rollback

Revert the supervisor and its focused test commit. Existing focused/full review
behavior remains the fallback only after the feature bytes are reverted; runtime
must never fallback while the proof feature is active.

## Child 3: RT-VERDICT-EVIDENCE

### Dependency

Requires current `RT-BASELINE-PARITY` receipt. It has no implementation
dependency on `RT-PROOF-SUPERVISOR` and may run concurrently after the frozen
function signatures are recorded in both child artifacts.

### Mutable Ownership

- `guru-template/overlay/verify/guru_review_record.py`
- `guru-template/overlay/verify/tests/test_integration_verdict_retry.py`

### Frozen Write Contract

Owns validation and append-only persistence for retry evidence. It may not edit
supervisor or Gate runtime.

### Steps

1. Define retry identity validation and domain-separated digest generation.
2. Add an append-only retry event writer/reader with atomic artifact creation.
3. Reject invalid run IDs, path escape, duplicate artifact names, overwrite,
   malformed event shape, and identity mismatch.
4. Classify retryable format failures separately from semantic findings,
   snapshot drift, provider failure, and incomplete invariant evidence.
5. Normalize a successful serialization retry through the existing official
   review schema without changing receipt schema.
6. Append exactly one final blocked row when the sole retry fails.
7. Add focused event replay, normalization, retry-limit, tamper, and legacy
   compatibility tests.
8. Run focused tests, `py_compile`, GitNexus detect-changes, formal staged
   review, commit, and receipt.

### Focused Checks

```bash
python3 -m py_compile guru-template/overlay/verify/guru_review_record.py
python3 -m unittest guru-template/overlay/verify/tests/test_integration_verdict_retry.py
git diff --check -- guru-template/overlay/verify/guru_review_record.py guru-template/overlay/verify/tests/test_integration_verdict_retry.py
```

### Rollback

Revert the review-record runtime and focused test commit. Append-only retry
evidence already written remains readable history and is never deleted.

## Child 4: RT-INTEGRATION-PROOF

### Dependencies

Requires current receipts for both `RT-PROOF-SUPERVISOR` and
`RT-VERDICT-EVIDENCE`. The dependency is explicit; parent/child hierarchy alone
does not authorize execution.

### Mutable Ownership

- `guru-template/overlay/tests/integration_proof_runtime_test.sh`
- exact package runtime/test peers declared by that bounded test

It must not edit either ordinary canonical runtime or focused test path.

### Steps

1. Add a bounded source/peer table for the three runtime files, existing
   lifecycle test, two new focused tests, and the bounded test itself.
2. Run bounded `--sync`; reject writes outside the declared table and reject
   deletions.
3. Run read-only byte parity.
4. Run JSONL/retry evidence tests and both focused test suites.
5. Run the existing full slice lifecycle regression exactly once after all
   feature bytes are assembled; record
   `integration_full_regression_count=1`. The earlier baseline compatibility
   executions do not increment this Integration metric.
6. Run route compatibility checks for ordinary v2, Small/Micro/Lite/non-Full,
   and v1 behavior.
7. Run a real Full/high Integration proof fixture and capture payload bytes,
   estimated/provider tokens, reviewer count, duplicate reads/probes, regression
   count, projection counts, retry count, and receipt currentness.
8. Verify no unrelated global-sync baseline path changed.
9. Run GitNexus detect-changes and `git diff --check`.
10. Stage only Integration-owned paths, run one official semantic review,
    commit locally, and record the Integration receipt.
11. Run the final no-slice Gate and stop before push, merge, archive, install,
    canary, full sync, or finish-work.

### Deterministic Checks

```bash
bash guru-template/overlay/tests/integration_proof_runtime_test.sh --sync
bash guru-template/overlay/tests/integration_proof_runtime_test.sh
python3 -m unittest guru-template/overlay/verify/tests/test_integration_proof_context.py
python3 -m unittest guru-template/overlay/verify/tests/test_integration_verdict_retry.py
python3 guru-template/overlay/verify/tests/test_slice_commit_lifecycle.py
git diff --check
```

These commands are frozen by `SL-INTEGRATION.json`; implementation may not
replace their invocation form or widen the deterministic set.

### Rollback

Revert this Integration commit first. If a cross-module contract remains
broken, revert the responsible ordinary runtime child, refresh only its receipt,
then regenerate a new Integration proof.

## 阻塞与偏差 (Blocks And Deviations)

Any dependency staleness, frozen-interface change, new mutable overlap, package
mapping change, provider-policy change, or unplanned path returns to Detail.
Ordinary focused failure returns only to its owner. Integration failures route
to the true contract owner and require a new Integration proof. No deviation may
authorize full-context fallback, extra formatting retries, full sync, or a
prohibited lifecycle action.

## Review And Commit Order

```text
baseline implement -> review -> commit -> receipt
proof supervisor implement ----+
                               +-> serial review/commit/receipt publication
verdict evidence implement -----+
Integration bounded sync -> full proof -> review -> commit -> receipt
final no-slice Gate
```

Workers may implement the two ordinary runtime children concurrently in
isolated worktrees. The control worktree alone owns staging, official review
records, commits, and receipts. The child directories never become independent
Guru lifecycle authorities; all dispatch, start, review, commit, and receipt
eligibility is evaluated from the parent task and parent packets.

## Planning Completion Checklist

- [x] Parent PRD has no open product/scope/risk question.
- [ ] Parent design and implementation plan are reviewed by the user.
- [x] Four child tasks exist and declare the dependencies above in their own
      PRD/implement artifacts.
- [ ] Baseline child packet is the only dispatchable packet before its receipt.
- [x] Ordinary child function signatures and evidence contracts are identical.
- [x] Mutable path overlap is zero for concurrently dispatchable children.
- [x] `implement.jsonl` and `check.jsonl` contain the relevant specs and research.
- [ ] Full/high contract, Overview/Detail reviews, deletion audit, and human
      confirmation are current before `task.py start`.
