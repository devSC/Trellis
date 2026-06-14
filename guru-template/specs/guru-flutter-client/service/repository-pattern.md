# Repository Pattern

> 本项目 repository 接口/实现与 datasource 边界的真实约定。

---

## Overview

<!--
- repository 在本项目中承担什么职责？接口与实现分别放在哪一层？
- 命名/目录约定是什么（如接口在 `domain/repository/`、实现在 `data/repository/`）？
- repository 是否聚合多个 datasource？聚合粒度如何划分？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Interface & Implementation

<!--
- 接口（抽象）与实现（具体）如何分离？谁依赖谁？
- 实现类的命名与放置约定是什么（如 `XxxRepositoryImpl`）？
- 入参/出参用领域实体还是 DTO？转换发生在哪里？
-->

```dart
// WRONG: <在此放本项目实际禁止的 repository 接口/实现写法>

// CORRECT: <在此放本项目实际推荐的 repository 接口/实现写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Datasource Boundaries

<!--
- 远程 datasource 与本地 datasource 如何划分？各自职责边界？
- repository 如何在远程/本地之间做缓存或回退策略？
- datasource 是否允许被 repository 以外的层直接调用？
-->

```dart
// WRONG: <在此放本项目实际禁止的 datasource 越界调用>

// CORRECT: <在此放本项目实际推荐的 datasource 边界写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## DTO / Entity Mapping

<!--
- DTO ↔ 领域实体 的映射放在哪里（mapper / extension / fromJson）？
- 哪些字段做了重命名/默认值/空值处理？约定是什么？
- 映射失败如何处理？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在 repository 上踩过的坑（如把 DTO 直接泄漏到 domain、datasource 边界被绕过等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
