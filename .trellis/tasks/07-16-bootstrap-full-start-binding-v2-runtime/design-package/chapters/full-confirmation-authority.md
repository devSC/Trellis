# Full Confirmation Freshness

### UNIT-full-confirmation-authority

## 1. 单元职责

Own current Full batch recomputation and BHV-002.

## 2. 行为定义

The current one-batch model remains authoritative. Requirements, detail, and
the complete sorted risk-packet byte set are recomputed at confirmation and
`check-start`.

### 2.1 Invariants

- `INV-FSB-004`: confirmation records share one current batch id/digest.
- `INV-FSB-005`: any requirements/detail/risk-set byte drift blocks.
- `INV-FSB-005A`: both confirmation records are exact canonical peers and every
  existing metadata field is covered by one self-verifying projection digest.

## 3. 核心数据结构

```text
FullConfirmationBatchInputs {
  requirements_digest,
  detail_artifact_digest,
  risk_packet_set_digest,
  confirmation_batch_digest
}
FullConfirmationProjectionV2 {
  schema_version,
  confirmed_by, confirmed_at,
  confirmation_scope, allowed_next_action, prompt_summary,
  confirmation_batch_id, confirmation_batch_digest,
  requirements_digest, detail_artifact_digest, risk_packet_set_digest,
  mode?, via?, turn_ref?, user_quote?
}
```

## 4. 逐行为设计

Keep `_full_confirmation_batch_inputs()`,
`_record_full_confirmation_batch()`, and
`_full_confirmation_batch_problem()` as the independent dynamic Gate. The
writer stores `confirmation_projection_digest = H(domain || canonical
FullConfirmationProjectionV2)`. The validator rejects unknown/missing fields,
requirements/detail projection divergence, invalid TTY/agent optional-field
combinations, constant/current-input mismatch, or projection-digest mismatch.
The cycle repair must not move these fields back into the stable digest.

## 5. 状态 / 边界管理

失败收口:

Missing risk directory, empty set, empty packet, changed filename/content, or
changed requirements/detail artifact blocks before `START_READY`. Any
confirmation metadata mutation or requirements/detail projection divergence
also blocks.

## 6. 数据合同

Risk rows stay sorted by filename and bind exact file bytes. Existing
requirements/detail compatibility records remain unchanged.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| one valid Full batch | current |
| risk packet changed/added/removed | stale |
| requirements changed | stale |
| detail changed | stale |
| actor/time/scope/action/prompt/batch/input metadata changed | stale |
| mode/via/turn/user quote changed or records diverge | stale |
| projection digest removed/recomputed incorrectly | stale |

## 8. 不得补造清单

- No signed receipt redesign.
- No new provider schema.
- No second confirmation batch.
