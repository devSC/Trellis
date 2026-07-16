# Parent Non-Start

### UNIT-parent-non-start

## 1. 单元职责

Keep the umbrella parent in planning under BHV-001.

## 2. 行为定义

The parent is not an implementation target.

### 2.1 Invariants

- `INV-UMB-003`: parent status remains planning.

## 3. 核心数据结构

```text
ParentRole { task_role=design_parent, start_this_parent_task=false }
```

## 4. 逐行为设计

Operator and task contract both route implementation to the child.

## 5. 状态 / 边界管理

失败收口:

Any parent start attempt blocks.

## 6. 数据合同

Existing parent role fields remain sufficient.

## 7. 测试映射

Read parent status before child activation.

## 8. 不得补造清单

No parent risk/start artifacts.
