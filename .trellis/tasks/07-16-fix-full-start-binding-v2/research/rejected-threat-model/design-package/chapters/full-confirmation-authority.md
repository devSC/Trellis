# Full Confirmation Authority

### UNIT-full-confirmation-authority

## 1. 单元职责

This unit owns semantic risk member validation, deterministic set membership, `FullConfirmationAuthorizationV2` and requirements/detail compatibility projections. It承接行为 BHV-002, BHV-003 and BHV-004. It does not execute task lifecycle or workers.

## 2. 行为定义

行为清单:

- BHV-002: every risk member is semantically current before hashing.
- BHV-003: one canonical authorization binds requirements/detail/A2 and all members.
- BHV-004: any authority/projection tamper blocks even while A2 stays stable.

### 2.1 Invariants

- `INV-FSB-004`: canonical observed risk member IDs equal the independently reviewed expected-slice IDs exactly.
- `INV-FSB-005`: confirm, check-start, Start Guard and later-slice preflight consume the same validator result and cannot reinterpret packet bytes independently.
- `INV-FSB-006`: no canonical authorization projection is current without one accepted, verified external user-authorization event.
- `INV-FSB-007`: the canonical projection and requirements/detail compatibility projections are atomically consistent; any security-field divergence blocks.

## 3. 核心数据结构

```text
ExpectedSliceInventoryV2 {kind, schema_version, task_id, source_digest, slice_ids[]}
RiskMemberSetV2 {kind, schema_version, task_id, A2, expected_inventory_digest, members[]}
RiskMember {slice_id, canonical_name, risk_packet_digest}
AuthorizationProvenanceV2 {
  receipt_version, provider_type, provider_id, key_or_token_id,
  event_id, nonce, subject_digest, receipt_digest, signature
}
ConfirmationSubjectV2 {
  domain, schema_version, repository_namespace, audience, issuer_provider_id,
  event_id, nonce, principal_id, confirmed_actor_id,
  confirmed_at, issued_at, not_before, expires_at,
  task_id, task_ref, route, policy_version, start_binding_version,
  selection_generation, A2,
  requirements_digest, detail_digest,
  expected_slice_inventory_digest,
  ordered_risk_member_rows, risk_member_set_digest,
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
FullConfirmationAuthorityV2 {
  grant_digest, batch_id, batch_digest, authorization_digest,
  task/policy/selection identity, A2,
  requirements_digest, detail_digest, risk_member_set,
  authorization_provenance,
  actor/time/scope/authorized_slice_actions/mode/via/turn_ref/user_quote
}
```

## 4. 逐行为设计

For BHV-002, `validate_current_risk_packet_set()` first loads the A2-bound `ExpectedSliceInventoryV2`, then parses each file, rejects symlinks and validates filename, task/slice, matching slice packet, A2, policy/scope, decisions and invariants. Canonical observed slice IDs must equal expected slice IDs exactly; missing, unexpected, duplicate and orphan members block before hashing.

For BHV-003, confirm builds canonical `ConfirmationSubjectV2`. Provider-asserted repository namespace is bound into A2 and subject, and audience must equal `trellis-guru-full-start-v2:<repository_namespace>`. The selected slice receives separate `guarded_start`, `implement` and `check` rows; later slices receive `implement` and `check`. It obtains a one-time receipt and verifies it before deriving `AuthorizationGrantCoreV2`. Accepted providers are a signed platform user-turn adapter, configured terminal signer or signed external attestation. Trust/key lookup and revocation state are outside task-writable artifacts.

For BHV-004, the grant core field list above is closed and contains only independently known immutable base fields. It excludes `grant_digest`, `authorization_digest`, `batch_id`, `batch_digest`, every projection digest and replay-time verification observations. Grant digest is computed once; authorization digest, batch id/digest and projection digests derive afterward in an acyclic order. Canonical and compatibility projection bytes are pure deterministic derivations. Replay verification appends non-authoritative observations without changing projection bytes.

## 5. 状态 / 边界管理

The canonical projection transitions from absent to current; any upstream, provenance or projection mutation makes it stale. The provider/registry maps one event id and nonce to exactly one subject digest and byte-identical batch/projection. Cross-task, cross-selection, expired/revoked or changed-subject reuse blocks.

失败如何收口:

| Error | Condition | Outcome |
| --- | --- | --- |
| `RiskMemberInvalid` | malformed/orphan/mismatch | confirm/check-start block |
| `RiskInventoryMismatch` | observed IDs do not exactly equal expected IDs | block before set hash |
| `RiskSetStale` | member add/delete/rename/change | authorization stale |
| `AuthorizationProvenanceUntrusted` | no replay-verifiable receipt | remain planning/block |
| `AuthorizationReceiptMismatch` | provider/key/audience/subject/signature mismatch | block |
| `AuthorizationReceiptExpiredOrRevoked` | invalid time window or external revocation | block |
| `AuthorizationReceiptReused` | event/nonce maps to another subject or batch | block |
| `AuthorizationGrantMismatch` | grant/batch/projection derivation differs | block |
| `ConfirmationProjectionMismatch` | canonical/projection divergence | block |
| `ConfirmationReplay` | task/version/selection mismatch | block |

## 6. 数据合同

The validator is the only decoder for risk packet JSON across confirm, check-start, Start Guard and later-slice preflight. Callers consume the expected inventory plus canonical member rows; they不得补造 filenames, slice ids or decision membership. The provenance verifier is the only adapter allowed to convert a configured terminal signer, trusted platform user-turn provider or signed external attestation into `AuthorizationProvenanceV2`. Provider trust configuration and signing keys live outside task-writable artifacts; tests inject an isolated test provider.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| malformed/empty/non-object extra risk | confirm block |
| filename/slice/task/policy/A2 mismatch | confirm and check-start block |
| missing/unexpected member vs reviewed inventory | confirm and check-start block |
| deterministic creation order | identical set digest |
| raw TTY or unverified agent quote/turn-ref | no authorization written |
| receipt signature/audience/time/revocation/subject divergence | live validation block |
| same receipt requests second non-identical batch | idempotent replay block |
| actor/time/via/turn/quote/action tamper | signed subject/grant block |
| authority field subTest tamper | live validation block |
| all expected members in one batch | one canonical member set |

## 8. 不得补造清单

- 不得只哈希非空文件而跳过语义校验。
- 不得从 observed member set 反推 expected inventory。
- 不得让 requirements/detail 两份记录成为并列权威。
- 不得把 raw TTY、canonical projection、provider-name string、agent quote、turn ref 或 actor 字符串本身当作授权信任根。
- 不决定 official task start、session pointer 或 compensation。
- 不把旧 quote 自动升级为 V2 authorization。
