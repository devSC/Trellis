# Directory Structure

> 本项目 `lib/` 下页面 / widget / 路由 / 注入的真实组织方式。

---

## Top-Level Layout

<!--
- `lib/` 下的一级目录是怎么划分的？（如 `pages/`、`widgets/`、`router/`、`di/`、`models/`）
- 哪些目录属于 UI / 表现层，哪些只是被本层引用？
- 一个新页面应该落在哪个目录、命名怎么定？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Page Organization

<!--
- 单个页面是「一个文件」还是「一个文件夹」（page + widgets + controller）？
- 页面文件内部的组织顺序约定（State / build / 私有 widget 方法）是什么？
- 页面级私有 widget 放在哪里，何时上升为共享 widget？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Shared Widgets

<!--
- 可复用 widget 放在哪个目录？按什么维度分子目录（原子组件 / 业务组件）？
- 一个 widget 从「页面私有」晋升到「共享」的判定标准是什么？
- 命名约定（前缀 / 后缀 / 文件名风格）是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (放错目录 / 命名不符约定的反例，bootstrap 从真实项目补)

// CORRECT:
// (符合本项目目录与命名约定的正例，bootstrap 从真实项目补)
```

---

## Routing & Injection Wiring

<!--
- 路由表 / 路由配置文件在 `lib/` 下的真实位置是哪里？
- 依赖注入（DI）的注册入口在哪个文件？UI 层如何取用？
- 页面与其 controller / provider 的接线在哪里完成？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Where Things Go (Cheat Sheet)

<!--
- 新增「页面 / 共享 widget / 路由 / 注入」分别落在哪个目录，一表说清。
- 哪些目录是「不要往里塞 UI 代码」的禁区？
- 与 `service/`、`shared/` 层的目录边界在哪里？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
