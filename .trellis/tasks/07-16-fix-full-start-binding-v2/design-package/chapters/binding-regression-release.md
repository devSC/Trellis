# Umbrella Integration Boundary

### UNIT-umbrella-integration

## 1. 单元职责

Track child source proof and the separate mirror release blocker.
It supports BHV-001 and BHV-002.

## 2. 行为定义

Source repair/tests proceed first; mirror sync/install/canary wait for the
38-drift owner.

### 2.1 Invariants

- `INV-UMB-004`: mirror drift is not a source implementation blocker.

## 3. 核心数据结构

```text
IntegrationState { source_tests, mirror_drift_count, release_allowed }
```

## 4. 逐行为设计

The parent consumes child results but does not execute them.

## 5. 状态 / 边界管理

失败收口:

Green source tests with unresolved mirror drift produce source-ready,
release-blocked status.

## 6. 数据合同

Child test output and mirror check output remain separate evidence.

## 7. 测试映射

Child source suites green; `sync:guru:check` may remain exit 1 with 38 drifts.

## 8. 不得补造清单

No direct sync or hand-edited mirror.
