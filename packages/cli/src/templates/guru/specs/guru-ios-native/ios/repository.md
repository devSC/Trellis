# Repository

> 本项目 Repository 的真实契约：接口定义在 Domain、具体实现在 Infrastructure。

---

## Interface in Domain

<!-- Repository protocol 定义在哪一层、哪个目录？方法签名约定是什么（`async throws`、返回 Domain 模型而非 DTO）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Implementation in Infrastructure

<!-- 具体实现放在哪一层、如何命名（`...RepositoryImpl` 等）？它依赖哪些数据源（网络/本地/缓存）？如何被装配？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## DTO ↔ Domain Mapping

<!-- 网络/持久化 DTO 与 Domain 模型如何映射、映射代码放哪？解码失败如何处理？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Caching & Data Sources

<!-- 多数据源如何协调（先缓存后网络、单一可信源）？缓存失效策略是什么？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- Repository 上反复踩过的坑（Domain 引用具体实现、DTO 泄漏到上层、接口与实现错位等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
