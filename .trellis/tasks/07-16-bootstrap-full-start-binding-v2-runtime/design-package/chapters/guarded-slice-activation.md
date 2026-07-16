# Guarded Slice Activation

### UNIT-guarded-slice-activation

## 1. 单元职责

Own selected artifact binding and existing lifecycle CAS under BHV-003.

## 2. 行为定义

Start Guard consumes the stable v2 digest after `check-start` independently
proves current Full confirmation. Selected slice/risk/envelope/attestation and
decision checks remain unchanged.

### 2.1 Invariants

- `INV-FSB-006`: no stale selected artifact reaches official start.
- `INV-FSB-007`: lifecycle lock/snapshot/postcondition checks remain unchanged.

## 3. 核心数据结构

```text
ArtifactBinding {
  gate_digest,
  slice_packet_digest,
  risk_packet_digest,
  envelope_digest,
  attestation_digest
}
```

## 4. 逐行为设计

Only the meaning of the v2 `gate_digest` input changes. `_artifact_binding()`,
`_snapshot()`, `start_with_guard()`, and compensation retain their current
validation and state transitions.

## 5. 状态 / 边界管理

失败收口:

Selected risk/detail/invariant/decision, attestation, or envelope mismatch
blocks before any official side effect. Post-call mismatch follows the existing
compensation/manual recovery behavior.

## 6. 数据合同

The `StartRequest` CLI and digest fields remain compatible. No new external
state is read.

## 7. 测试映射

| Test | Expected |
| --- | --- |
| current stable digest and selected artifacts | binding passes |
| selected risk changed | block |
| attestation changed | block |
| envelope changed | block |
| lifecycle CAS conflict | block/compensate as before |

## 8. 不得补造清单

- No new lifecycle state.
- No external activation receipt.
- No worker authorization redesign.
