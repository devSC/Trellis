# Stable Planning Binding

### UNIT-stable-planning-binding

## 1. 单元职责

This unit owns `StablePlanningArtifactV2` (`A2`), domain separation, canonical serialization and version dispatch. It承接行为 BHV-001 and BHV-008. It does not own user confirmation, worker launch or lifecycle status.

## 2. 行为定义

行为清单:

- BHV-001: A2 is byte-identical before and after Full confirmation.
- BHV-008: Full v2, legacy Full v1, Lite and Micro select explicit compatible algorithms.

### 2.1 Invariants

- `INV-FSB-001`: A2 is byte-identical before and after writing any confirmation, attestation, envelope or lifecycle evidence.
- `INV-FSB-002`: every planning input that can change the authorized implementation subject, including the reviewed expected-slice inventory, changes A2.
- `INV-FSB-003`: task-level version dispatch is selected before downstream evidence is read and never silently downgrades.

## 3. 核心数据结构

```text
StablePlanningArtifactV2 {
  kind, schema_version, repository_namespace, task_id, route, guru_chain,
  policy_version, start_binding_version, selection_generation, scope_fingerprint,
  require_req_uc, gate_contract_digest,
  requirements_artifact_digest, detail_artifact_digest,
  decision_inventory_digest, expected_slice_inventory_digest,
  review_policy_snapshot_digest,
  review_evidence_digest
}
BootstrapRuntimeLockV1 {
  schema_version, task_id, task_ref, route, risk, policy_version,
  base_commit, installed_runtime_root, installed_runtime_git_tree,
  tracked_file_count, capture_worktree_state, anchor_metadata
}
BootstrapRuntimeAnchorSubjectV1 {
  domain, schema_version, repository_namespace, audience,
  principal_id, provider_id, key_id, event_id, nonce,
  issued_at, not_before, expires_at,
  task_id, task_ref, requirements_artifact_digest,
  runtime_lock_sha256, base_commit, installed_runtime_git_tree
}
BootstrapRuntimeAnchorReceiptV1 {
  subject, detached_signature, signature_namespace,
  allowed_signers_policy_digest, external_registry_record_digest
}
AuditedLegacyContinuationReceiptV1 {
  repository_namespace, task_id, legacy_policy_version,
  bootstrap_runtime_anchor_receipt_digest,
  requirements_confirmation_artifact_digest,
  original_start_evidence_digest,
  completed_slice_check_inventory_digest,
  allowed_actions[], issued_at, provider_id, key_id, signature
}
```

Canonical JSON uses sorted keys and explicit domain/version fields. The digest never reads requirements/detail confirmation records.

## 4. 逐行为设计

For BHV-001, compute A2 before risk generation and recompute after confirmation; equality is mandatory. The expected-slice inventory comes from the reviewed `gate-contract.json` projection of `implement.md`, not from enumerating current risk files. Requirements/detail content or expected-slice changes still alter their direct stable inputs.

For BHV-008, planning dispatch first hard-blocks design-parent roles, then reads the task-level `gate-contract.json.start_binding.version` before any risk evidence. Creating or migrating a V2 contract atomically appends an externally signed monotonic `binding_adopted` record before A2/risk generation. Every planning and start dispatch queries that registry head. V2 packets must agree but cannot select the algorithm. `version=2` plus compatible Full/high policy requires V2 adoption and the complete V2 contract; missing evidence blocks. A planning task on `guru-risk-contract-v2` without the discriminator/adoption record is migration-required. Legacy Full v1 requires `guru-risk-contract-v1`, no V2 marker and no V2 adoption record. Lite and Micro/Small require their owned route with no Full artifacts.

In-progress dispatch never infers legacy from absence. It queries the externally configured monotonic activation registry by stable task identity. A signed V2 activation receipt requires a byte-matching local `activation_contract_snapshot.version=2`; a signed audited legacy-registration receipt selects legacy-only compatibility and forbids new slices/V2 authorization. No registry record, removed task markers, or any registry/task disagreement blocks.

The current design parent is never dispatched. During planning, its separately approved bootstrap child computes `BootstrapRuntimeLockV1`. Before requirements confirmation, a passphrase/hardware-protected user key signs `BootstrapRuntimeAnchorSubjectV1`; the allowed-signers policy and single-assignment `BootstrapRuntimeAnchorReceiptV1` live root-owned/read-only outside the workspace. The unencrypted agent-usable SSH key is rejected. Task-local PRD/confirmation/lock/contract are projections only. Each SDK dispatch first verifies the external receipt signature, audience, time, trusted key and registry record, then compares its subject to current requirements, lock, base tree and live installed runtime. Modified source is not installed into that worktree during SDK execution.

After all SDK slice checks, the source registration command may issue `AuditedLegacyContinuationReceiptV1` from the external bootstrap anchor, original v1 confirmations/start evidence and completed check inventory. Registration derives all original bootstrap values from the verified root-owned receipt and refuses current task-local substitutes. Its closed `allowed_actions` permits final source-runtime verification/check-commit only and rejects implement, new slice, official start or V2 evidence.

## 5. 状态 / 边界管理

A2 is a pure projection and has no mutable lifecycle state. `task.status`, confirmation time, session pointer and start attempt belong to downstream CAS snapshots.

错误类型表:

| Error | Condition | 收口 |
| --- | --- | --- |
| `StableArtifactUnavailable` | required input missing/invalid | block before risk |
| `StableArtifactStale` | recomputed A2 differs | block confirm/start |
| `BindingVersionUnsupported` | unknown/mixed algorithm | fail closed |
| `BindingMigrationRequired` | planning v2-policy task lacks task-level discriminator | block and migrate/review |
| `BindingAdoptionMismatch` | contract and external adoption registry disagree | block |
| `ParentTaskNotStartable` | design parent reaches start dispatch | hard block |

## 6. 数据合同

Inputs come from current Gate artifact collectors, contract/policy helpers, provider-asserted canonical repository namespace and canonical review/decision/expected-slice projections. Consumers receive a typed payload plus digest; they不得补造 missing fields from confirmation or packet content.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| confirm before/after metamorphic test | A2 equal |
| requirements/detail/contract/review/decision drift | A2 changes |
| confirmation/timestamp/quote drift | A2 unchanged |
| task discriminator/evidence downgrade | V2 remains selected and blocks |
| task-local contract rolled back after V2 adoption | external adoption still selects V2 and blocks |
| legacy/v2/mixed/migration dispatch | explicit legacy/pass/block |
| V2 activation registry/snapshot removed or divergent | block, never legacy fallback |
| in-progress task lacks signed activation/legacy registration | provenance-unknown block |
| bootstrap worker runtime differs from pinned v1 manifest | worker/release block |
| lock/contract/runtime rewritten after requirements confirmation | requirements snapshot or confirmed lock literal mismatch; worker/registration block |
| task-local confirmation/PRD/lock/contract rewritten coherently | external anchor signature/subject/registry mismatch; worker/registration block |
| protected signer or root-owned trust/receipt unavailable | bootstrap anchor unavailable; no worker/registration |
| bootstrap legacy receipt requested before all slice checks or grants implement/new slice | registration block |
| agent-usable key, wrong SSH namespace/principal or non-root-writable trust/receipt | bootstrap anchor rejected |
| Micro/Small with any Full marker | compatibility block |

## 8. 不得补造清单

- 不得把 confirmation record、attestation、envelope 或 lifecycle timestamp 放回 A2。
- 不得复写 requirements/detail digest collector。
- 不得从 observed risk files 推断 expected slices。
- 不得让 risk/attestation/envelope evidence 选择或降级 task-level binding version。
- 不决定用户授权是否 current。
- 不拥有 Start Guard lock、worker membership 或 package sync。
