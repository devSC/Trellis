# Binding Regression And Release

### UNIT-binding-regression-release

## 1. 单元职责

Own bootstrap isolation, real cross-component lifecycle regression, compatibility matrix, source/package/install consistency, disposable V2 canary and Himora handoff evidence. It承接行为 BHV-001 and BHV-010, and supports BHV-009.

## 2. 行为定义

- BHV-001: parent stays unstarted and child stays legacy for delivery.
- BHV-009: all dispatch families have explicit executable tests.
- BHV-010: chronological fixture, mirror/install and V2 canary control release.

### 2.1 Invariants

- `INV-FSB-011`: a chronological `FIX-F1/FIX-F2` fixture crosses real builders, signed receipt, check-start, guarded start and later preflight.
- `INV-FSB-012`: parent/child isolation, compatibility, source/package/install and V2 canary are all green before Himora sync.

## 3. 核心数据结构

```text
DeliveryEvidence {
  parent_status,
  child_contract_digest,
  child_activation_contract,
  bootstrap_runtime_lock_and_worker_digests,
  bootstrap_runtime_anchor_receipt,
  audited_legacy_continuation_receipt,
  stable_digest_before_after,
  signed_receipt_digest,
  risk_member_rows,
  activation_registry_receipt,
  start_attempt_state,
  later_member_result,
  source_package_install_digests,
  v2_canary_result,
  harness_runtime_manifests,
  signed_receipt_and_grant,
  signed_registry_chain_and_head,
  public_keys_and_trust_revocation_snapshot,
  durable_attempt_journal,
  selected_and_later_action_results,
  mirror_integration_proof
}
MirrorIntegrationProofV1 {
  schema_version, repository_namespace,
  baseline_manifest_digest, owner_artifact_digest, reviewed_commit,
  baseline_source_tree, baseline_package_tree,
  reviewed_child_source_delta_digest,
  expected_mapped_package_rows_digest,
  actual_package_delta_digest,
  sync_command, sync_exit, sync_output_digest,
  generated_at
}
```

## 4. 逐行为设计

Bootstrap tests assert parent status remains planning, child policy remains v1 and no V2 marker appears in child activation evidence. Before requirements confirmation, a protected user key signs the exact repository/task/requirements/lock/base/runtime subject and root-owned trust/receipt is installed outside the workspace. Every SDK worker verifies that external receipt and matches its subject against task-local confirmation/lock/contract/base tree/live runtime; repaired source cannot be applied into the active child before all slice checks. After those checks, audited legacy registration derives the bootstrap values from the same external receipt, binds the original v1 start and completed inventory, permits final source verify/check-commit only and rejects new implement/slice/V2 actions. Otherwise-valid evidence must still yield `PARENT_TASK_NOT_STARTABLE` from check-start, guard and hook without registry or official side effects.

The canonical fixture declares exactly `FIX-F1/FIX-F2`, registers V2 adoption, creates real risk, obtains a signed test-provider receipt and deterministic grant, calls real confirm/check-start/_artifact_binding/start_with_guard, proves explicit FIX-F1 implement/check authorization, and performs explicit FIX-F2 implement/check authorization preflight. Only official lifecycle side effects may use a controlled fake.

Compatibility fixtures cover legacy Full v1 two-stage confirmation, Lite requirements-only, Micro/Small no-Full-artifact, V2 migration-required, external V2 activation and audited legacy registration.

`guru_mirror_integration.py guarded-sync` verifies the reviewed owner baseline, invokes standard sync and writes `MirrorIntegrationProofV1` only for exact source-to-package delta equality. `verify-proof` recomputes live inputs and is mandatory for apply/install, canary and repaired-source check-commit; direct sync without proof is release-blocked. Disposable install and `full_start_binding_v2_canary.py` use `CANARY-SELECTED/CANARY-LATER`, external ephemeral trust/registry and persistent child evidence before parent integration and `HIM-S1/HIM-S2`.

## 5. 状态 / 边界管理

失败如何收口:

| Failure | Outcome |
| --- | --- |
| parent started or child gains V2 marker | bootstrap block |
| parent hard denial missing on any start surface | P1 regression |
| split fixture/mocked target boundary | release block |
| negative drift reaches official/worker call | P1 regression |
| compatibility path changes | compatibility block |
| unrelated mirror drift included | integration block |
| direct sync or missing/stale mirror proof | apply/install/canary/check-commit block |
| SDK worker runtime differs from pinned v1 lock | bootstrap block |
| lock/contract/runtime/worker evidence rewritten together | requirements-confirmed PRD anchor mismatch; bootstrap block |
| all task-local bootstrap evidence rewritten together | external signature/root-owned registry mismatch; bootstrap block |
| V2 canary fails | no Himora sync |

## 6. 数据合同

Evidence reports exact commands, counts, digests and task roles. Executor can recommend candidate pass only; final verifier status belongs to an independent verifier/harness or user.

## 7. 测试映射

| Suite | Coverage |
| --- | --- |
| `test_delivery_policy.py` | A2/risk/receipt/projection/dispatch |
| `test_start_guard.py` | preimage/registry/snapshot/CAS/later authorization |
| `full_start_binding_v2_canary.py` | installed adoption, self-contained signed public evidence and offline replay verification |
| `run_tests.sh` | CLI/Gate integration and historical regression |
| `guru_mirror_integration.py` tests | owner baseline, guarded sync, exact mapping, proof replay and bypass rejection |
| `apply_test.sh` | current mirror proof + source/package/installed target and canary setup |
| GitNexus detect changes | expected symbols/processes only |

## 8. 不得补造清单

- 不得启动 parent。
- 不得把 child legacy start 当 V2 pass。
- 不得 mock `START_READY`、preseed confirmation 或使用 fake risk JSON 证明目标链。
- 不得吸收 unrelated reinstall/package drift。
