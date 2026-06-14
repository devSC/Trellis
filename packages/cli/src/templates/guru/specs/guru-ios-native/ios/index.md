# iOS UI / Presentation Layer Guidelines

> 本项目 iOS 原生（SwiftUI + MVVM + Clean Architecture）UI / 表现层的真实约定与模式。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的 iOS 层模式（目录分层、SwiftUI view 写法、ViewModel 三态、UseCase 编排、Repository 接口/实现、导航、依赖注入、错误分层、质量门禁）。
方法学（分层依赖律、doc_type 七类、五阶段 Gate）见 `../harness/` 与 `../guides/golden-path.md`，本目录只写「这个项目实际怎么做」，供 sub-agent 匹配本项目风格。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | `UI/Features/<Feature>/{Views,ViewModels}` 与四层目录的真实组织 | To fill |
| [ViewModel](./viewmodel.md) | `ObservableObject` + `@Published` 三态（loading/loaded/error）约定 | To fill |
| [UseCase](./usecase.md) | Domain 层编排、零 UI 依赖的 UseCase 写法 | To fill |
| [Repository](./repository.md) | 接口在 Domain、实现在 Infrastructure 的契约约定 | To fill |
| [View Guidelines](./view-guidelines.md) | SwiftUI view 拆分、主题修饰器、禁裸色值 | To fill |
| [Coordinator & Navigation](./coordinator-navigation.md) | `AppCoordinator` 路由注册位置与导航约定 | To fill |
| [DI / FactoryKit](./di-factorykit.md) | FactoryKit `@Injected` 注册与解析规范 | To fill |
| [Error Handling](./error-handling.md) | `enum Error` 分层与跨层转换点 | To fill |
| [Quality](./quality.md) | SwiftLint / build / test 命令与门禁 | To fill |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals).
2. Include **code examples** from your codebase (real file paths).
3. List **forbidden patterns** (WRONG/CORRECT) and why.
4. Add **common mistakes** your team has made.

填写时遵循 `../guides/golden-path.md` 的分层依赖律与 `../harness/` 的 doc_type 七类口径，不复写其正文，只引用。

---

**Language**: 正文中文与既有 spec 一致；代码示例保留原样（Swift）。
