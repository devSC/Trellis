# Guarded Slice Activation

### UNIT-guarded-slice-activation

## 1. 单元职责

Own activation preimage, per-slice attestation/envelope binding, external monotonic activation registry, local snapshot CAS, guarded official start and later-worker authorization. It承接行为 BHV-006, BHV-007 and BHV-008.

## 2. 行为定义

- BHV-006: E[i] binds a precomputable activation preimage.
- BHV-007: activation provenance is monotonic outside task artifacts.
- BHV-008: selected and later lifecycle boundaries remain fail-closed.

### 2.1 Invariants

- `INV-FSB-008`: attestation and E[i] bind the same current authorization, preimage and member.
- `INV-FSB-009`: pre-lock, lock-internal, final pre-call and post-return CAS remain mandatory.
- `INV-FSB-010`: every later worker revalidates receipt, authorization, registry/snapshot and member immediately before launch.

## 3. 核心数据结构

```text
ActivationContractPreimageV2 {
  repository_namespace, task_id, task_ref, version, route_policy_digest,
  A2, authorization_digest, expected_inventory_digest,
  risk_set_digest, selection_generation, authorized_slice_actions_digest
}

SliceAuthorizationProjectionV2 {
  repository_namespace, slice_id, action,
  authorized_action_row_digest, selected_risk_digest,
  batch_id, batch_digest, authorization_digest,
  risk_set_digest, activation_preimage_digest
}

ActivationRegistryReceiptV2 {
  domain, schema_version, repository_namespace,
  task_id, task_ref, binding_version,
  contract_or_preimage_digest, attempt_id, state,
  sequence, predecessor_digest, canonical_payload_digest,
  issued_at, provider_id, key_id, signature
}
```

## 4. 逐行为设计

V2 contract adoption appends the first signed registry record before A2/risk. The activation preimage binds provider-asserted repository namespace and action-set digest. Each E[i] carries one exact `{slice_id, action}` row/digest: selected `guarded_start`, selected `implement`/`check`, or later `implement`/`check`. Preflight matches the requested operation to that row; no E[i] references a future snapshot.

Under the start lock, provider head CAS appends prepared state with sequence/predecessor and returns a signed receipt. The final pre-call CAS validates the signed chain head. Successful start persists exactly the preimage as local snapshot and appends finalized state. Failed, compensated or manual-recovery states remain visible. Old signed records cannot replay over the current head.

The durable local attempt journal advances `prepared -> official_call_started -> official_returned -> verified`. A no-official-call `reconcile-start` operation maps registry/local truth as follows:

| Prepared-head truth | Reconciliation |
| --- | --- |
| no call-started and unchanged planning snapshots | append aborted-pre-call; later fresh attempt allowed |
| returned plus exact in-progress postcondition | append finalized |
| known post-call divergence | bounded compensation once, then terminal record |
| call-started with ambiguous outcome | manual-recovery-required; never re-invoke |

Only explicit aborted/failed/compensated planning states may start a new attempt.

Later preflight checks task in-progress only as a lifecycle prerequisite, then revalidates current confirmation receipt, authorization, exact risk set, member, E[i], external registry and local snapshot.

## 5. 状态 / 边界管理

失败如何收口:

| Error | Condition | Outcome |
| --- | --- | --- |
| `AuthorizationBatchMismatch` | E/attestation/C2 differ | no call |
| `ActivationPreimageMismatch` | E/local candidate differ | no call |
| `ActivationRegistryMismatch` | external receipt absent/divergent | no call |
| `ActivationRegistryReplay` | sequence/predecessor/head mismatch | no call |
| `ActivationReconciliationAmbiguous` | call outcome unprovable | manual recovery/no re-invocation |
| `ActivationSnapshotMismatch` | local snapshot absent/divergent | no worker |
| `LifecycleCASMismatch` | task/session/artifact drift | block/compensate |
| `OfficialStartFailed` | call/postcondition/hook failure | compensate/manual recovery |

## 6. 数据合同

This unit consumes the shared risk validator and confirmation receipt verifier. It owns no duplicate parser or signer. Registry provider and trust configuration are external to task-writable artifacts.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| E binds future snapshot | schema rejects |
| all task V2 markers deleted | registry-selected V2 mismatch block |
| final pre-call drift | official start not called |
| post-return drift | compensate/manual recovery |
| later member current but receipt/registry stale | worker not launched |
| later member lacks explicit implement/check action | worker not launched |
| selected member lacks implement/check action | primary worker not launched |
| crash at prepared/call-started/returned window | deterministic reconcile/no duplicate call |

## 8. 不得补造清单

- 不得把 lock描述为约束所有 writers。
- 不得从 task-local absence推断 legacy。
- 不得用 caller SHA 代替 receipt/member validation。
- 不得让 task status 自动授权 later slice。
