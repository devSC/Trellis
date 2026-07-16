# Guarded Slice Activation

### UNIT-guarded-slice-activation

## 1. 单元职责

This unit owns selected-slice activation binding, attestation/envelope batch linkage, guarded lifecycle CAS and later-slice membership. It承接行为 BHV-005, BHV-006 and BHV-007.

## 2. 行为定义

行为清单:

- BHV-005: attestation and envelope bind the same authorization/member.
- BHV-006: guarded start preserves pre-lock, lock, final pre-call and post-call CAS.
- BHV-007: every later slice proves membership before worker launch.

### 2.1 Invariants

- `INV-FSB-008`: attestation and envelope bind the same current authorization, expected member set and selected member.
- `INV-FSB-009`: pre-lock, lock-internal, final pre-official-start and post-return CAS checks remain mandatory; no precondition failure invokes official start.
- `INV-FSB-010`: every later worker revalidates full authorization and its own expected-member binding immediately before launch.

## 3. 核心数据结构

```text
SliceAuthorizationProjectionV2 {
  repository_namespace, task_id, slice_id, action,
  authorized_action_row_digest, selected_risk_digest,
  confirmation_batch_id, confirmation_batch_digest,
  authorization_digest, risk_member_set_digest,
  scope_fingerprint, decision_set_digest
}

ActivationContractPreimageV2 {
  repository_namespace, task_id, task_ref, version, route_policy_digest,
  stable_planning_digest, authorization_digest,
  expected_slice_inventory_digest, risk_member_set_digest,
  selection_generation, authorized_slice_actions_digest
}

ActivationBindingV2 {
  stable_planning_digest, slice_packet_digest, risk_packet_digest,
  envelope_digest, attestation_digest, authorization_digest,
  activation_contract_preimage_digest,
  action, authorized_action_row_digest
}

ActivationRegistryRecordV2 {
  domain, schema_version, repository_namespace, task_id, task_ref,
  binding_version, contract_or_preimage_digest,
  attempt_id, state, sequence, predecessor_digest,
  canonical_payload_digest, issued_at,
  provider_id, key_id, signature
}
```

## 4. 逐行为设计

For BHV-005, attestation and envelope agree with canonical authorization, provider-asserted repository namespace, current risk member and precomputable activation preimage. Each E[i] includes exactly one canonical `{slice_id, action}` row and digest. Preflight matches the requested `guarded_start`, `implement` or `check` operation to that row; whole-set binding alone is insufficient.

For BHV-006, Start Guard performs current checks before lock, inside lock, immediately before official invocation and after official return. The activation preimage is computed after C2/U2 and includes the digest of canonical per-slice actions. V2 adoption already created the first external record before risk. Under the start lock, provider compare-and-swap appends `activation_prepared` against the current head and preimage digest. A successful start persists the exact preimage snapshot and appends `activation_finalized`; failures append terminal `failed`, `compensated` or `manual_recovery_required`. Every signed record carries sequence and predecessor digest, so a replayed prior state cannot become current.

The local attempt journal is durably written as `prepared`, `official_call_started`, `official_returned` and `verified`. `reconcile-start` is a no-official-call recovery operation:

| Registry head / durable local truth | Reconciliation |
| --- | --- |
| prepared + no call-started + unchanged planning snapshots | append `aborted_pre_call`; fresh attempt may later proceed |
| prepared + returned/exact in-progress postcondition | append `activation_finalized` |
| prepared + known post-call divergence | run bounded compensation once; append compensated/manual terminal result |
| prepared + call-started but outcome ambiguous | `manual_recovery_required`; never re-invoke |
| finalized | verified terminal; no second start |

Only aborted-pre-call, failed or compensated heads may lead to a new attempt, and only while task is planning with current fresh evidence.

For BHV-007, E[selected,guarded_start] is created just in time before check-start; selected implement/check and each later implement/check E[i,action] are created or refreshed just in time before their worker. Issuance is deterministic from current C2/U2, the same activation preimage and exact authorized action row; it is not an all-members atomic write. Immediately before worker launch, preflight revalidates receipt/C2/U2 freshness, the requested action row, selection generation, external activation receipt, exact local snapshot, expected inventory, E[i,action]/attestation, slice packet and risk digest. `task.status=in_progress` is only a lifecycle prerequisite and never an authorization shortcut.

## 5. 状态 / 边界管理

Lifecycle states remain planning -> guarded official start -> in_progress, with durable attempt states prepared -> official_returned -> verified or compensated/manual_recovery_required.

异常表:

| Error | Condition | 收口 |
| --- | --- | --- |
| `AuthorizationBatchMismatch` | attestation/envelope/canonical differ | no official/worker call |
| `AuthorizationProvenanceStale` | trusted event/projection no longer verifies | no official/worker call |
| `SliceMembershipMissing` | later slice not in confirmed set | no worker launch |
| `SliceInventoryMismatch` | current expected/observed set differs from C2 | no worker launch |
| `ActivationSnapshotMismatch` | V2 marker exists but snapshot is missing/stale | no legacy fallback or worker call |
| `ActivationRegistryMismatch` | external adoption/prepared/final chain differs or is absent | no official/worker call |
| `ActivationRegistryReplay` | sequence/predecessor/head mismatch | no official/worker call |
| `ActivationReconciliationAmbiguous` | prepared head and call outcome unprovable | manual recovery; no re-invocation |
| `LifecycleCASMismatch` | artifact/task/session drift | block or compensate |
| `OfficialStartFailed` | postcondition/hook/check failure | exact compensation/manual recovery |

## 6. 数据合同

The unit consumes canonical A2/risk/authorization/provenance projections and owns no independent parser or provenance adapter. It owns the precomputable activation preimage and external registry reservation/finalization CAS. Full `task.json` and session file images remain lifecycle CAS inputs even though dynamic confirmation is excluded from A2.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| same-batch selected member | guarded start verified |
| selected implement/check action rows | primary worker authorized |
| attestation A/envelope B after rehash | block |
| untrusted/stale provenance or unauthorized slice action | no official/worker call |
| final pre-call mutation | official start not called |
| post-start unexpected mutation | compensate/manual recovery |
| any expected member added/changed/deleted after confirm | later preflight block |
| later member current but C2/U2/requested action row stale | later preflight block |
| V2 activation snapshot removed after start | mixed-state block |
| crash in each prepared/call-started/returned window | deterministic reconcile result |
| all task-local V2 markers removed but registry says V2 | registry-selected V2 mismatch block |
| no external V2 or audited legacy registration | provenance-unknown block |

## 8. 不得补造清单

- 不得把 Start Guard lock描述为约束所有其他 writers。
- 不得依赖 caller-provided SHA 代替语义校验。
- 不得让 E[i] 绑定尚未生成的 snapshot；只能绑定 precomputable preimage。
- 不得以 task-local marker absence 推断 legacy。
- 不决定 risk set contents或用户 confirmation subject。
- 不验证 provenance string；只消费 full-confirmation owner 的 trusted verifier result。
- 不允许 task `in_progress` 自动授权未确认的 later slice。
