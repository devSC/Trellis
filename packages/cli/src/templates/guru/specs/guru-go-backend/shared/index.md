# Shared / Cross-layer Guidelines

> 跨层通用约定（Go 语言级、命名、git）。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的跨层硬规则与约定（不跨某一层、对所有 `internal/` 包通用的部分）。方法学（分层依赖律、错误三件套、启动序列、各层迷你路径）见 `../harness/` 与 `../guides/golden-path.md`，本目录只写「这个 Go 后端项目实际怎么做」，供 sub-agent 匹配本项目风格。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Go Conventions](./go-conventions.md) | Go 语言级约定与包可见性（`internal/` 隐私、context 传递、并发与 receiver 风格） | To fill |
| [Naming Conventions](./naming-conventions.md) | 包/文件/类型/接口/常量的命名规律 | To fill |
| [Git Conventions](./git-conventions.md) | 分支/提交/PR 约定 | To fill |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals).
2. Include **code examples** from your codebase (real file paths).
3. List **forbidden patterns** (WRONG/CORRECT) and why.
4. Add **common mistakes** your team has made.

填写时遵循 `../guides/golden-path.md` 的分层依赖律与 `../harness/` 的 doc_type 口径，不复写其正文，只引用。

---

**Language**: 正文中文与既有 spec 一致；代码示例保留原样。
