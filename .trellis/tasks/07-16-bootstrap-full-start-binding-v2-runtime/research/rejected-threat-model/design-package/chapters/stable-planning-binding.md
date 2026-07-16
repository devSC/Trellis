# Stable Planning Binding And Dispatch

### UNIT-stable-planning-binding

## 1. 单元职责

Own A2 construction, canonical serialization, task-level planning dispatch and external-receipt-based in-progress dispatch. It承接行为 BHV-002 and BHV-009.

## 2. 行为定义

- BHV-002: A2 is stable across confirmation and changes for every stable subject drift.
- BHV-009: algorithm selection is explicit, authoritative and non-downgradable.

### 2.1 Invariants

- `INV-FSB-001`: downstream confirmation, receipt, E[i], registry and lifecycle state never enter A2.
- `INV-FSB-002`: artifact, contract, policy, decision, review or expected-inventory drift changes A2.
- `INV-FSB-003`: planning uses task contract; in-progress uses signed activation/legacy registration; absence never selects legacy.

## 3. 核心数据结构

```text
StablePlanningArtifactV2 {
  domain, schema_version, repository_namespace, task_id, task_ref,
  route, policy_version, start_binding_version,
  selection_generation, scope_fingerprint,
  gate_contract_digest, requirements_digest, detail_digest,
  decision_inventory_digest, expected_slice_inventory_digest,
  review_policy_digest, review_evidence_digest
}

DispatchEvidence {
  lifecycle, task_contract_projection,
  external_activation_or_legacy_registration_receipt
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

## 4. 逐行为设计

A2 reuses current Gate artifact and policy collectors. No downstream parser may reconstruct omitted inputs.

Planning Full v2 requires policy v2, task-level binding v2 and a signed external `binding_adopted` registry head created before A2/risk. Every planning/start dispatch queries it. Planning policy v2 without discriminator/adoption is migration-required. Legacy Full v1 requires policy v1, no V2 marker and no V2 adoption record. Lite and Micro/Small require their own routes and reject Full artifacts.

In-progress V2 requires an external signed activation receipt plus matching local snapshot. Pre-upgrade legacy requires an audited external legacy registration. No record, total task-marker deletion or disagreement blocks.

The bootstrap child itself always selects legacy Full v1 and is never upgraded in place. During planning, `BootstrapRuntimeLockV1` and `BootstrapRuntimeAnchorSubjectV1` are created. Before requirements confirmation, a passphrase/hardware-protected user key signs the subject; root-owned allowed-signers policy plus the single-assignment subject/signature live outside the workspace. Every SDK implement/check dispatch first verifies `BootstrapRuntimeAnchorReceiptV1`, then compares its signed values with task-local requirements/confirmation/lock/contract, base commit/tree and live installed runtime. It continues through that pre-repair installed runtime, so the modified source dispatcher is not loaded during SDK-U2/U3/U4. No task-writable value can redefine the original.

After all SDK slice checks and independent implementation review, the repaired source may issue `AuditedLegacyContinuationReceiptV1` from the verified bootstrap anchor plus original v1 requirements/detail/start evidence through the external signer/registry. Registration derives repository/task/requirements/lock/base/runtime values from the external receipt, not current task files. The receipt permits final source-runtime verification/check-commit only. It rejects implement, new slice, official start and any V2 evidence, and is required before the repaired source handles this in-progress child.

## 5. 状态 / 边界管理

失败如何收口:

| Error | Condition | Outcome |
| --- | --- | --- |
| `StableArtifactUnavailable` | required stable input absent/invalid | block before risk |
| `StableArtifactStale` | recomputed A2 differs | block |
| `BindingMigrationRequired` | planning v2 policy lacks discriminator | block |
| `BindingAdoptionMismatch` | local contract and external adoption disagree | block |
| `ActivationProvenanceUnknown` | in-progress external registration absent | block |
| `DispatchEvidenceMismatch` | task/registry evidence differs | block |
| `BootstrapRuntimeDrift` | SDK worker runtime differs from pinned v1 lock | block |
| `BootstrapRuntimeAnchorMismatch` | confirmed PRD literal, lock, contract projection, base tree or live runtime differs | block |
| `BootstrapAnchorUntrusted` | signature/key/audience/time/root ownership/registry mismatch | block |
| `LegacyContinuationScopeInvalid` | registration is early or grants implement/new slice/V2 | block |

## 6. 数据合同

Inputs come only from current canonical collectors, provider-asserted repository namespace and external registration verifier. Downstream risk/receipt/envelope fields may agree with dispatch but cannot select it.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| before/after confirmation | A2 byte-identical |
| stable input drift | A2 changes |
| remove all task-local V2 markers | external registry still selects V2 and blocks |
| roll back V2 planning contract after adoption | external adoption still blocks legacy |
| no audited legacy registration | provenance-unknown block |
| SDK-U2/U3/U4 resolve modified source runtime | bootstrap runtime drift block |
| coherent lock/contract/runtime rewrite after confirmation | confirmed PRD anchor mismatch block |
| coherent task-local confirmation/PRD/lock/runtime rewrite | external signed anchor mismatch block |
| agent-usable key, wrong SSH namespace/principal or non-root-writable trust/receipt | bootstrap anchor rejected |
| post-slice registration grants more than verify/check-commit | registration block |
| Full v1/V2/Lite/Micro matrix | explicit owned result |

## 8. 不得补造清单

- 不得从 risk or envelope evidence选择 binding version。
- 不得从 task-local marker absence 推断 legacy。
- 不得放回 confirmation-dependent A2 inputs。
- 不得给 bootstrap child 增加 V2 discriminator。
