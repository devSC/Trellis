# Coordinator & Navigation

> 本项目导航的真实约定：`AppCoordinator` 路由注册位置与跳转约定。

---

## AppCoordinator Responsibility

<!-- AppCoordinator 承担什么职责、定义在哪个文件？它如何持有导航状态（`NavigationPath` / 自定义栈）？谁创建它？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Route Registration

<!-- 路由如何定义与注册（`enum Route`、目的地工厂）？新增一个页面要改哪几处？路由放在哪一层？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Navigation API

<!-- 页面间如何跳转（push/present/dismiss）？ViewModel 触发导航的标准方式是什么（不直接 import SwiftUI）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Deep Link & Back Stack

<!-- 深链/外部入口如何映射到路由？返回栈、根重置、tab 切换如何处理？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 导航上反复踩过的坑（View 里硬编码跳转、ViewModel 直引 SwiftUI 导航、栈状态不一致等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
