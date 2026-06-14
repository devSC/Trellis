# Flutter UI / Presentation Layer Guidelines

> 本项目 UI / 表现层的真实约定与模式。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的 Flutter UI 层模式（widget 写法、状态方案、路由、序列化、踩坑）。
方法学（分层依赖律、doc_type 七类、五阶段 Gate）见 `../harness/` 与 `../guides/golden-path.md`，本目录只写「这个项目实际怎么做」，供 sub-agent 匹配本项目风格。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | `lib/` 下页面/widget/路由/注入的真实组织 | To fill |
| [Widget Guidelines](./widget-guidelines.md) | const 构造、widget 拆分、build 边界 | To fill |
| [State Management](./state-management.md) | 实际状态方案与 controller 生命周期 | To fill |
| [Navigation](./navigation.md) | 路由注册位置与跳转约定 | To fill |
| [Type Safety](./type-safety.md) | 序列化与空安全约定 | To fill |
| [Pitfalls](./pitfalls.md) | 本项目踩过的 UI 层坑 | To fill |
| [Quality](./quality.md) | analyze/format/lint 命令与门禁 | To fill |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals).
2. Include **code examples** from your codebase (real file paths).
3. List **forbidden patterns** (WRONG/CORRECT) and why.
4. Add **common mistakes** your team has made.

填写时遵循 `../guides/golden-path.md` 的分层依赖律与 `../harness/` 的 doc_type 七类口径，不复写其正文，只引用。

---

**Language**: 正文中文与既有 spec 一致；代码示例保留原样。
