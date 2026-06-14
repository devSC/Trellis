# Service (Domain + Data) Layer Guidelines

> 本项目领域层 + 数据层的真实约定与模式。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的 domain + data 层模式（usecase 编排、repository、网络、DI、错误收口、本地库）。
方法学见 `../harness/` 与 `../guides/golden-path.md`，本目录只写「这个项目实际怎么做」。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Usecase Pattern](./usecase-pattern.md) | usecase 编排的真实写法、依赖边界 | To fill |
| [Repository Pattern](./repository-pattern.md) | repository 接口/实现、datasource 边界 | To fill |
| [API Patterns](./api-patterns.md) | 网络层（`@RestApi`/Dio）、契约组织 | To fill |
| [Error Handling](./error-handling.md) | 错误收口位置（集中 normalizer vs 分散 try-catch） | To fill |
| [Dependency Injection](./dependency-injection.md) | DI 入口与注册约定 | To fill |
| [Local Storage](./local-storage.md) | 本地库版本字段与迁移 | To fill |
| [Logging](./logging.md) | logger 注入路径、结构化字段 | To fill |

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
