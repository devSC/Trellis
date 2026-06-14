# Usecase Pattern

> 本项目 usecase 的真实编排写法与依赖边界。

---

## Overview

<!--
- usecase 在本项目中承担什么职责？是否每个业务动作一个 usecase？
- usecase 与 repository / 表现层的边界在哪里？
- 命名/目录约定是什么（如 `XxxUsecase`、放在 `domain/usecase/`）？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Orchestration Patterns

<!--
- usecase 如何编排多个 repository / 多个 datasource 的调用？
- 是否允许 usecase 调用其他 usecase？组合方式是什么？
- 入参/出参形态（实体 vs DTO vs 原始类型）的约定是什么？
-->

```dart
// WRONG: <在此放本项目实际禁止的 usecase 编排写法>

// CORRECT: <在此放本项目实际推荐的 usecase 编排写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Dependency Boundaries

<!--
- usecase 允许依赖哪些层？是否禁止直接依赖 datasource / Dio / 本地库？
- 依赖如何注入（构造注入 vs 容器获取）？见 dependency-injection.md。
- 哪些依赖是被禁止跨过 repository 直接触达的？
-->

```dart
// WRONG: <在此放本项目实际禁止的依赖跨层写法>

// CORRECT: <在此放本项目实际推荐的依赖注入写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Error & Result Handling

<!--
- usecase 是否捕获/转换错误，还是原样上抛由上层收口？见 error-handling.md。
- 成功/失败结果如何返回（Either / Result / 异常 / 可空）？
- 业务校验失败与系统错误如何区分？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在 usecase 编排上踩过的坑（如把网络细节泄漏到 usecase、usecase 互相循环依赖等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
