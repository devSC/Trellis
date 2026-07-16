# Binding Regression And Release

### UNIT-binding-regression-release

## 1. 单元职责

This unit owns the real cross-component lifecycle regression, drift matrix, compatibility verification, source/mirror/install consistency and final target replay. It承接行为 BHV-008, BHV-009 and BHV-010.

## 2. 行为定义

行为清单:

- BHV-008: legacy Full v1 and Lite remain explicit and green.
- BHV-009: one real `FIX-F1/FIX-F2` fixture proves the canonical lifecycle independently from the bootstrap child's four SDK unit slices.
- BHV-010: source, package mirror and installed target match reviewed output.

### 2.1 Invariants

- `INV-FSB-011`: at least one chronological fixture with its own exact expected `FIX-F1/FIX-F2` inventory crosses real risk builder, trusted receipt confirmation, check-start, guarded start and later-slice preflight boundaries without preseeded success state.
- `INV-FSB-012`: Full v2, legacy Full v1, Lite, Micro/Small, source mirror and installed target must each pass their owned compatibility/release checks before synchronization to Himora.

## 3. 核心数据结构

```text
LifecycleEvidence {
  stable_digest_before_confirm,
  stable_digest_after_confirm,
  bootstrap_runtime_lock_and_worker_digests,
  bootstrap_runtime_anchor_receipt,
  audited_legacy_continuation_receipt,
  expected_slice_inventory_digest,
  authorization_provenance_digest,
  confirmation_batch_digest,
  activation_registry_receipt_digest,
  activation_contract_preimage_digest,
  risk_member_rows,
  selected_start_attempt_state,
  later_slice_membership_result,
  source_mirror_install_digests,
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

The test fixture constructs state through production builders in chronological order and never preloads a final confirmation state.

## 4. 逐行为设计

For BHV-008, dedicated fixtures execute legacy Full requirements/detail confirmation, Lite requirements-only confirmation and Micro/Small no-Full-artifact dispatch, plus migration-required, external activation/legacy registration, total task-marker deletion and no-downgrade cases.

For BHV-009, the isolated fixture contract declares expected `FIX-F1/FIX-F2`, builds exact matching risk before confirmation, verifies a signed test-provider receipt and deterministic grant, runs real confirm/check-start/_artifact_binding/start_with_guard, proves explicit FIX-F1 implement/check authorization, and then performs full FIX-F2 implement/check authorization preflight. The linked legacy bootstrap child implements SDK-U1..SDK-U4. After installation, the replayable `full_start_binding_v2_canary.py` harness uses `CANARY-SELECTED/CANARY-LATER` and persists `verification/v2-canary.json` before `HIM-S1/HIM-S2`.

For BHV-010, `guru_mirror_integration.py guarded-sync` verifies the reviewed zero-drift baseline before invoking standard sync and writes `MirrorIntegrationProofV1` only when the actual package delta exactly equals the canonical mapping of the reviewed child source delta. `verify-proof` recomputes live facts; apply/install, V2 canary and repaired-source check-commit all require it. Direct sync cannot create release evidence. The bootstrap child also proves every SDK worker verified the root-owned signed runtime anchor and creates its check/commit-only audited legacy receipt only after all slice checks.

## 5. 状态 / 边界管理

Verifier status stays pending until every focused/full test and mirror/install check is current. Test failures do not authorize modifying the verifier or weakening assertions.

错误映射:

| Failure | Outcome |
| --- | --- |
| canonical happy path unreachable | release block |
| negative drift reaches official/worker call | P1 security regression |
| untrusted provenance or expected/observed mismatch passes | P1 authorization regression |
| parent is started through broken V2 or child lacks separate approval | bootstrap release block |
| check-start/guard/hook accepts design parent | P1 bootstrap regression |
| all task-local V2 markers deleted and legacy path selected | P1 downgrade regression |
| legacy/Lite path changes unexpectedly | compatibility block |
| Micro/Small inherits any Full artifact | compatibility block |
| mirror contains unrelated baseline drift | integration block |
| direct sync or missing/stale mirror integration proof | apply/install/canary/check-commit block |
| bootstrap worker loads repaired source before all SDK checks | bootstrap release block |
| lock, contract projection, runtime and worker evidence are coherently rewritten | confirmed requirements/PRD lock anchor mismatch; bootstrap block |
| task-local PRD/confirmation/lock/runtime rewritten with no trusted signature | external anchor receipt mismatch; bootstrap block |

## 6. 数据合同

Tests may fake the official lifecycle side effect but must call real risk builder, real confirmation writer, real check-start, real artifact binding and real after-start observation contract. Evidence reports exact commands/counts/digests.

## 7. 测试映射

| Suite | Coverage |
| --- | --- |
| `test_delivery_policy.py` | schema, expected/observed risk set, provenance, confirmation subject, compatibility |
| `test_start_guard.py` | parent hard deny, canonical lifecycle, adoption/activation registry, later actions, replay, CAS and compensation |
| `full_start_binding_v2_canary.py` | installed runtime, exact canary members, self-contained public evidence and offline replay verification |
| `run_tests.sh` | CLI/Gate integration and historical regression |
| `guru_mirror_integration.py` tests | owner artifact, guarded sync, exact mapping, proof replay and bypass rejection |
| `apply_test.sh` | current mirror proof + source/package/installed target |
| GitNexus detect changes | expected symbols/processes only |

## 8. 不得补造清单

- 不得用伪 risk JSON、preconfirmed fixture 或 unconditional `START_READY`证明目标链。
- 不得改测试/评分逻辑制造通过。
- 不决定产品行为或 schema compatibility；只验证已批准合同。
- 不得将 design parent 直接启动，或把 bootstrap child 的 legacy authorization 伪称为 V2 canary evidence。
- 不吸收 unrelated reinstall 或 package mirror drift。
