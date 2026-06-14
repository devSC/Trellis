# ViewModel

> 本项目 ViewModel 的真实写法：`ObservableObject` + `@Published` 三态（loading / loaded / error）约定。

---

## State Modeling

<!-- 三态如何建模？是单个 enum `ViewState`（idle/loading/loaded/error）还是多个 `@Published` 布尔/可选字段？哪种是本项目标准？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## ObservableObject & @Published

<!-- ViewModel 如何声明（`final class ... : ObservableObject`）？哪些属性标 `@Published`、哪些不标？是否统一标 `@MainActor`？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Dependencies & Initialization

<!-- ViewModel 依赖（UseCase / Repository）如何注入（init 参数 vs `@Injected`）？View 如何持有 ViewModel（`@StateObject` vs `@ObservedObject`）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Async & Threading

<!-- 异步加载如何触发与回写状态？`Task`/`async let` 用法、错误如何落到 error 态、主线程更新如何保证？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- ViewModel 上反复踩过的坑（业务逻辑写进 View、网络层细节泄漏进 ViewModel、状态竞态、retain cycle 等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
