# Stable Planning Binding

### UNIT-stable-planning-binding

## 1. 单元职责

Own the versioned Start Guard digest and BHV-001.

## 2. 行为定义

- V2 excludes requirements/detail confirmation records from the pre-confirmation
  stable digest.
- V1 keeps the existing digest payload.

### 2.1 Invariants

- `INV-FSB-001`: v2 digest bytes are identical before and after Full batch write.
- `INV-FSB-002`: review-run or gate-contract drift changes the v2 digest.
- `INV-FSB-003`: v1 confirmation-record mutation retains existing behavior.

## 3. 核心数据结构

```text
StartGuardStableBindingV2 {
  schema_version,
  guru_chain,
  require_req_uc,
  review_runs,
  gate_contract_sha256
}
```

## 4. 逐行为设计

`guru_task._gate_digest()` reads the contract policy version. V2 uses the stable
payload above. All other policies execute the unchanged legacy payload.

## 5. 状态 / 边界管理

失败收口:

Unknown/malformed contract state does not silently select v2. Existing error
handling remains fail closed.

## 6. 数据合同

The result remains a SHA-256 hex digest and keeps the existing `--gate-digest`
request field. No new artifact or provider is introduced.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| write v2 requirements/detail batch | digest unchanged |
| change v2 review run | digest changes |
| change v2 gate contract | digest changes |
| mutate v1 confirmation | legacy digest changes |

## 8. 不得补造清单

- No external trust provider.
- No root launcher.
- No external registry.
- No new migration protocol.
