# Local Storage

> 本项目本地库版本字段与迁移的真实约定。

---

## Overview

<!--
- 本项目用什么本地存储方案（sqflite / drift / hive / isar / shared_preferences / 安全存储）？
- 各方案分别存什么数据（结构化表 / KV / 敏感数据）？
- 本地库的访问是否收口在 datasource？见 repository-pattern.md。
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Schema & Version Field

<!--
- 本地库的 schema 在哪里定义？版本号字段叫什么、存在哪里？
- 表/实体如何声明（代码生成 / 手写 DDL / 注解）？
- 主键、索引、可空字段的约定是什么？
-->

```dart
// WRONG: <在此放本项目实际禁止的 schema/版本字段写法>

// CORRECT: <在此放本项目实际推荐的 schema/版本字段写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Migration Strategy

<!--
- 版本升级时迁移逻辑写在哪里、如何触发？
- 迁移是逐版本递增还是一次性重建？破坏性迁移如何兜底？
- 迁移失败/数据损坏时的降级策略是什么？
-->

```dart
// WRONG: <在此放本项目实际禁止的迁移写法（如漏写中间版本迁移）>

// CORRECT: <在此放本项目实际推荐的迁移写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Access & Caching Boundaries

<!--
- 本地库读写如何与远程数据协同（缓存 / 离线 / 单一数据源）？
- 哪一层允许直接触达本地库？是否禁止 usecase/UI 直接读写？
- 敏感数据的加密/清除约定是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在本地存储上踩过的坑（如忘记升版本号、迁移不可逆、KV 与 DB 数据不一致等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
