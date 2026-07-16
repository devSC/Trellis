# Binding Regression And Release

### UNIT-binding-regression-release

## 1. 单元职责

Own the chronological regression, compatibility checks, and mirror release
boundary under BHV-004.

## 2. 行为定义

One fixture crosses real risk construction, Full batch recording,
`check-start`, and guarded binding/start in chronological order.

### 2.1 Invariants

- `INV-FSB-008`: the target regression cannot preseed post-confirmation state.
- `INV-FSB-009`: only the official lifecycle side effect may be controlled.
- `INV-FSB-010`: mirror drift blocks release only, not source repair/tests.

## 3. 核心数据结构

```text
ChronologicalRegressionEvidence {
  stable_digest_before_confirm,
  risk_packet_digest,
  confirmation_batch_digest,
  confirmation_projection_digest,
  check_start_result,
  guarded_binding_result,
  stable_digest_after_confirm
}
```

## 4. 逐行为设计

The test starts without requirements/detail confirmation records, computes the
v2 stable digest, builds real risk evidence, records the real Full batch,
asserts `check-start`, then runs real Start Guard binding/lifecycle code. Drift
cases are applied only after the valid path is proven.

The negative matrix mutates every existing confirmation projection field and
requires `check-start` to reject the stale projection while the stable v2 digest
remains unchanged.

## 5. 状态 / 边界管理

失败收口:

Any mocked risk builder, preseeded Full batch, unconditional `START_READY`, or
directly fabricated binding invalidates the regression.

## 6. 数据合同

The evidence is test output, not a new production artifact.

## 7. 测试映射

| Suite | Coverage |
| --- | --- |
| `test_delivery_policy.py` | Full batch freshness and compatibility |
| `test_start_guard.py` | stable digest, selected binding, lifecycle CAS |
| `run_tests.sh` | CLI/Gate historical regression |
| `sync:guru:check` | release-only 38-drift status |

## 8. 不得补造清单

- Do not gate source tests on mirror zero-drift.
- Do not install or run canary while mirror drift remains.
- Do not add deferred threat-model mechanisms.
