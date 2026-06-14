# H5/Web Frontend Layer Guidelines

> 本项目 H5/Web 前端层（Next.js App Router + React + TypeScript strict）的真实约定与模式。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的前端层模式（`app/` 路由组织、server/client 组件边界、UI 组件、客户端状态、类型安全、质量门禁）。
方法学（分层依赖律、doc_type 七类、五阶段 Gate、TS strict / server-first 等硬规则）见 `../harness/` 与 `../guides/golden-path.md`，并以 `../conventions/project-conventions.md` 为项目取值唯一权威；本目录只写「这个项目实际怎么做」，供 sub-agent 匹配本项目风格，不复写硬规则正文、不重复槽位取值。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | `app/` 下路由段、组件、hooks 的真实组织 | To fill |
| [Server Components](./server-components.md) | server-component 默认形态与数据获取约定 | To fill |
| [Client Components](./client-components.md) | `'use client'` 判定与 client/server 边界 | To fill |
| [UI Components](./ui-components.md) | UI 组件库选型与 props 约定 | To fill |
| [State](./state.md) | 客户端状态方案与 owner 归属 | To fill |
| [Type Safety](./type-safety.md) | TS strict 档位与类型组织 | To fill |
| [Quality](./quality.md) | eslint / tsc / test 命令与门禁 | To fill |

---

## How to Fill These Guidelines

For each guideline file:

1. Document your project's **actual conventions** (not ideals).
2. Include **code examples** from your codebase (real file paths，如 `app/(blog)/posts/[slug]/page.tsx`、`components/`、`lib/`）。
3. List **forbidden patterns** (WRONG/CORRECT) and why。
4. Add **common mistakes** your team has made。

填写时遵循 `../guides/golden-path.md` 的分层依赖律（server-first、`'use client'` 最小化、secret 只在 server 侧、doc_type 七类）与 `../harness/` 的 doc_type 口径，不复写其正文，只引用；项目取值以 `../conventions/project-conventions.md` 为准。

---

**Language**: 正文中文与既有 spec 一致；代码示例保留原样。
