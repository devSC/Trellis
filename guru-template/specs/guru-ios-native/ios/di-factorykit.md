# DI / FactoryKit

> 本项目依赖注入的真实规范：FactoryKit `@Injected` 注册与解析约定。

---

## Container & Registration

<!-- 依赖在哪里注册（`Container` 扩展、注册文件位置）？每个依赖的工厂写法长什么样？注册按层如何组织？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## @Injected Resolution

<!-- 消费方如何解析依赖（`@Injected(\.xxx)`）？哪些类型适合 `@Injected`、哪些走 init 注入？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Scope & Lifetime

<!-- 依赖的作用域如何设定（`.singleton` / `.cached` / `.unique`）？默认作用域是什么、为什么？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Test Overrides

<!-- 测试里如何替换实现（register mock / `Container.shared`）？测试隔离如何保证不污染其它用例？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- DI 上反复踩过的坑（漏注册导致运行时崩、作用域选错、循环依赖、跨层注入具体类型等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
