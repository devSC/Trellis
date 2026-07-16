# Deferred Hardening Boundary

### UNIT-deferred-hardening-boundary

## 1. 单元职责

Own BHV-002 scope separation.

## 2. 行为定义

Rejected external trust/launch design is historical research only.

### 2.1 Invariants

- `INV-UMB-002`: deferred hardening never blocks current source repair.

## 3. 核心数据结构

```text
DeferredScope { topics[], prerequisite_for_current_source=false }
```

## 4. 逐行为设计

Preserve old drafts under research and create a later task only when scheduled.

## 5. 状态 / 边界管理

失败收口:

New findings reopen current planning only if they violate the original hash
cycle or Gate-strength invariants.

## 6. 数据合同

No production contract is introduced.

## 7. 测试映射

Current source diff contains none of the deferred mechanisms.

## 8. 不得补造清单

No signer, root launcher, external registry, or malicious-agent protocol.
