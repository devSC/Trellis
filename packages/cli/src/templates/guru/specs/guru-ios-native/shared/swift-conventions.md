# Swift Conventions

> 本项目 Swift 语言级的实际约定与惯用法。

---

## Language Features

<!-- 本项目实际用到哪些 Swift 语言特性（struct vs class、enum 关联值、protocol-oriented、property wrapper、result builder、泛型约束）？哪些约定俗成、哪些避免使用？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Access Control & private extension

<!-- 可见性如何组织？`private` 方法是否一律放进 `private extension`（平台硬约定）？`internal`/`fileprivate`/`public` 的使用边界是什么？协议与实现如何分文件？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Optionals & Error Handling

<!-- 可选值的解包约定是什么？何时允许强解包 `!`、`try!`、`as!`，何时必须用 `guard let`/`if let`/`??`/早返回？错误如何 `throws` 与归一到领域 `enum Error`？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Concurrency

<!-- async/await、Task、actor、`@MainActor`、GCD 的写法约定是什么？如何处理取消、线程切换与 RxSwift 遗留的并发边界？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- Swift 语言层面团队踩过的坑有哪些（retain cycle、值/引用语义混淆、隐式 `self` 捕获、可选链误用等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
