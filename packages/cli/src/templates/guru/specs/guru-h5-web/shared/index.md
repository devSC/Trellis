# Shared / Cross-layer Guidelines

> 跨层通用约定（TypeScript 语言级、命名、git）。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的跨层硬规则与约定（不分 H5 七类 doc_type，对所有层通用）。方法学（TS strict、server-first、分层依赖律、route 段约定）见 `../guides/golden-path.md` 与 `../harness/`；项目级槽位取值见 `../conventions/`。本目录只写「这个项目实际的语言级 / 命名 / 协作约定怎么落」，供 sub-agent 匹配本项目风格。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [TS Conventions](./ts-conventions.md) | TypeScript 语言级约定（strict、类型建模、async、import） | To fill |
| [Naming Conventions](./naming-conventions.md) | 文件/类型/成员/常量命名规律 | To fill |
| [Git Conventions](./git-conventions.md) | 分支/提交/PR 约定 | To fill |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals).
2. Include **code examples** from your codebase (real file paths).
3. List **forbidden patterns** (WRONG/CORRECT) and why.
4. Add **common mistakes** your team has made.

填写时遵循 `../guides/golden-path.md` 的 TS strict、分层依赖律与 server-first 硬规则，不复写其正文，只引用。

---

**Language**: 正文中文与既有 spec 一致；代码示例保留原样。
