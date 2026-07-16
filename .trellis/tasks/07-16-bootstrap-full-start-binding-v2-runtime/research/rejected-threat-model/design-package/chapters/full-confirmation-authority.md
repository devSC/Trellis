# Full Confirmation Authority

### UNIT-full-confirmation-authority

## 1. 单元职责

Own expected/observed risk membership, canonical `ConfirmationSubjectV2`, signed receipt verification, canonical authorization projection and requirements/detail compatibility projections. It承接行为 BHV-003, BHV-004 and BHV-005.

## 2. 行为定义

- BHV-003: one shared semantic validator proves the exact risk member set.
- BHV-004: only a durable signed receipt authorizes Full v2.
- BHV-005: canonical and compatibility projections are atomic and tamper-evident.

### 2.1 Invariants

- `INV-FSB-004`: canonical observed member ids equal independently reviewed expected ids exactly.
- `INV-FSB-005`: all four consumers use the same validator result.
- `INV-FSB-006`: no authorization is current without a replay-verifiable signed receipt for the exact subject.
- `INV-FSB-007`: canonical and compatibility projections are byte-consistent for every shared security field.

## 3. 核心数据结构

```text
ExpectedSliceInventoryV2 {
  domain, schema_version, task_id, source_digest, slice_ids[]
}

RiskMemberV2 {
  slice_id, canonical_name, slice_packet_digest,
  risk_packet_digest, A2, scope_policy_decision_digests
}

ConfirmationSubjectV2 {
  domain, schema_version, repository_namespace, audience, issuer_provider_id,
  event_id, nonce, principal_id, confirmed_actor_id,
  confirmed_at, issued_at, not_before, expires_at,
  task_id, task_ref, route, policy_version, binding_version,
  selection_generation, A2,
  requirements_digest, detail_digest,
  expected_inventory_digest, ordered_member_rows, risk_set_digest,
  scope_fingerprint, confirmation_mode, via, turn_ref,
  user_quote_digest, authorized_slice_actions[]
}

AuthorizedSliceAction {
  slice_id, action
}

AuthorizationGrantCoreV2 {
  domain, schema_version, repository_namespace,
  subject_digest, receipt_digest,
  task_id, task_ref, route, policy_version, start_binding_version,
  selection_generation, A2,
  requirements_digest, detail_digest,
  expected_slice_inventory_digest, risk_member_set_digest,
  scope_fingerprint, confirmation_mode,
  authorized_slice_actions_digest
}

AuthorizationVerificationObservationV2 {
  verifier_id, verified_at, result, revocation_head_digest
}

TrustedAuthorizationReceiptV2 {
  subject, provider_id, key_id, detached_signature, receipt_digest
}
```

## 4. 逐行为设计

`validate_current_risk_packet_set()` rejects non-objects, malformed JSON, symlinks, noncanonical names, duplicates, missing/unexpected members, task/slice mismatch, missing slice packets, A2 drift, scope/policy/decision/invariant mismatch and mixed versions. Confirm, check-start, Start Guard and later preflight consume its canonical result.

The receipt provider is configured outside task artifacts and asserts a canonical repository namespace. Audience must equal `trellis-guru-full-start-v2:<repository_namespace>`. Subject rows explicitly authorize selected `guarded_start`, selected `implement`/`check`, and later `implement`/`check`; no broad scalar action exists. Raw TTY, unsigned metadata and reusable bearer tokens cannot authorize.

Confirm and check-start verify key lookup, signature, audience, exact subject, validity window, revocation and single-use event/nonce mapping. They compute a domain-separated grant digest over the closed field list above, which contains only independently known immutable base fields. `grant_digest`, authorization/batch/projection derived values and replay-time `verified_at` observations are excluded; they are produced afterward in an acyclic order. Identical retry returns byte-identical grant/batch/projections; changed actor/time/via/turn/quote/action or any other field requires a new receipt.

## 5. 状态 / 边界管理

失败如何收口:

| Error | Condition | Outcome |
| --- | --- | --- |
| `RiskMemberInvalid` | member semantic failure | block |
| `RiskInventoryMismatch` | expected != observed | block |
| `AuthorizationReceiptInvalid` | signature/audience/subject failure | block |
| `AuthorizationReceiptExpiredOrRevoked` | time/revocation failure | block |
| `AuthorizationReceiptReused` | event/nonce maps to different output | block |
| `AuthorizationGrantMismatch` | deterministic grant/batch/projection differs | block |
| `ConfirmationProjectionMismatch` | canonical/compatibility divergence | block |

## 6. 数据合同

Persisted evidence contains canonical subject, detached signature and public provider/key identifiers only. Secret keys, reusable platform credentials and revocation authority live outside the task tree.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| malformed/missing/unexpected member | confirm/check-start block |
| wrong audience/issuer/key/signature | block |
| expired/revoked receipt | block |
| event/nonce reused for changed subject/batch | block |
| identical receipt retry | byte-identical result |
| actor/time/via/turn/quote/action tamper | signed subject/grant block |
| any projection field tamper | live validation block |

## 8. 不得补造清单

- 不得只哈希非空 risk 文件。
- 不得从 observed files 推断 expected inventory。
- 不得把 TTY、quote、provider string 或 task record 当信任根。
- 不得持久化 signing secret 或 bearer credential。
