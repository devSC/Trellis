# Shared / Cross-layer Guidelines

> 跨层通用约定（Swift 语言级、命名、git）。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的跨层硬规则与约定（Swift 语言惯用法、文件/类型/成员命名规律、分支与提交约定）。这些约定横跨 DDD 四层，不归属任何单一 doc_type，供 sub-agent 匹配本项目风格。
方法学（分层依赖律、iOS 七类 doc_type、五阶段 Gate）见 `../harness/` 与 `../guides/golden-path.md`，本目录只写「这个项目实际怎么做」。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Swift Conventions](./swift-conventions.md) | Swift 语言级约定与惯用法（`private extension`、可选值、并发等） | To fill |
| [Naming Conventions](./naming-conventions.md) | 文件/类型/成员/常量命名规律 | To fill |
| [Git Conventions](./git-conventions.md) | 分支/提交/PR 约定 | To fill |

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
