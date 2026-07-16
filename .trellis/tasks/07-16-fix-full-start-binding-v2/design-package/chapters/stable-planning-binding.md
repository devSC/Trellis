# Child Implementation Delegation

### UNIT-child-implementation-delegation

## 1. 单元职责

Own BHV-001 delegation to the linked child.

## 2. 行为定义

All source implementation and test evidence lives in the child.

### 2.1 Invariants

- `INV-UMB-001`: parent has no production implementation slice.

## 3. 核心数据结构

```text
ChildDelegation { parent_task, child_task, child_is_only_ssot }
```

## 4. 逐行为设计

Parent links one child and never dispatches itself.

## 5. 状态 / 边界管理

失败收口:

Any parent start or source edit is a topology error.

## 6. 数据合同

The child task id is the durable link.

## 7. 测试映射

Parent remains planning; child owns source checks.

## 8. 不得补造清单

No parent implementation.
