# State Management

> 本项目实际的状态方案与 controller 生命周期约定。

---

## State Patterns

<!--
- 本项目用的状态方案是什么（Provider / Riverpod / GetX / Bloc / setState）？
- UI 层「本地 UI 状态」和「业务 / 共享状态」分别用哪种承载？
- 状态对象与 widget 的绑定方式是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (用错状态层级 / 把业务状态塞进 setState 的反例)

// CORRECT:
// (符合本项目状态方案的正例)
```

---

## When to Use Which

<!--
- 何时用 setState，何时上升到 controller / provider？
- 跨页面共享状态用哪种，页面内瞬态用哪种？
- 选型判定有没有一句话规则？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Controller Lifecycle

<!--
- controller 在哪里创建、哪里注入、哪里释放（dispose）？
- 与页面生命周期（initState / dispose）如何对齐？
- 监听器 / 订阅 / 定时器如何保证被取消？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (漏 dispose / 订阅泄漏的反例，bootstrap 从真实项目补)

// CORRECT:
// (正确创建与释放 controller 的正例)
```

---

## Rebuild Scope

<!--
- 如何把 rebuild 收敛到最小子树（Consumer / Selector / 局部监听）？
- 哪些写法会导致整页重建？
- 性能敏感页面有什么额外约定？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!--
- 本项目状态管理最常见的错误有哪些（泄漏 / 越权改状态 / 重建过大）？
- 哪些是 review 反复打回的？
- 每条对应正确做法是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
