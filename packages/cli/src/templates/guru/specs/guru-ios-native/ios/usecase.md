# UseCase

> 本项目 UseCase 的真实写法：Domain 层编排、零 UI 依赖、单一业务动作。

---

## Responsibility & Granularity

<!-- 一个 UseCase 承担什么职责？粒度如何（一个动作一个 UseCase vs 聚合多动作）？何时该新建 UseCase 而非塞进 ViewModel？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Interface Shape

<!-- UseCase 的标准签名长什么样（protocol + struct/class、`callAsFunction` / `execute(...)`、入参出参类型）？是否统一 `async throws`？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Zero UI Dependency

<!-- 如何保证 UseCase 不依赖 UI（不 import SwiftUI/UIKit、不引用 ViewModel）？依赖只能指向哪一层？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Orchestration & Composition

<!-- UseCase 如何编排多个 Repository / 子 UseCase？事务性、顺序/并发、错误传播如何处理？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- UseCase 上反复踩过的坑（贫血直传 Repository、混入 UI 状态、跨层引用 Infrastructure 具体类型等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
