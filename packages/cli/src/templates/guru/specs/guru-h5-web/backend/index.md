# H5 Backend / Server Layer Guidelines

> 本项目 H5 平台 backend / server 层的真实约定与模式。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的 backend / server 层模式（route handler / API 路由约定、data-access 红线、server action 约定、server/client 错误边界）。
方法学（分层依赖律、doc_type 分类、五阶段 Gate）见 `../harness/` 与 `../guides/golden-path.md`，本目录只写「这个项目实际怎么做」，供 sub-agent 匹配本项目风格。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Route Handlers](./route-handlers.md) | route handler / API 路由约定 | To fill |
| [Data Access](./data-access.md) | data-access 层（只在 server 侧 / 私有数据红线） | To fill |
| [Server Actions](./server-actions.md) | server action 约定 | To fill |
| [Error Handling](./error-handling.md) | server / client 错误边界 | To fill |

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
