# View Guidelines

> 本项目 SwiftUI view 的真实约定：view 拆分、主题修饰器、禁裸色值。

---

## View Composition

<!-- View 如何拆分（子 View / `@ViewBuilder` / 计算属性）？单个 View 的复杂度边界在哪？何时拆出独立文件？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Theme Modifiers

<!-- 主题如何应用（自定义 `ViewModifier` / 扩展 / 环境值）？标准的间距、字体、圆角修饰器有哪些、从哪里取？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## No Hardcoded Colors

<!-- 为什么禁裸色值（`Color(red:...)` / `.red`）？颜色必须从哪里取（设计 token / Asset / 主题）？ -->

```swift
// WRONG:
// .foregroundColor(Color(red: 0.2, green: 0.4, blue: 0.9))

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## State Binding

<!-- View 如何绑定 ViewModel 状态（`@StateObject`/`@ObservedObject`/`@Binding`）？三态如何在 view 里分支渲染？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- View 上反复踩过的坑（业务逻辑进 body、裸色值/魔法数、过大 body、误用 state 包装器等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
