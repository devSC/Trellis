# Go Backend / Service Layer Guidelines

> 本项目 Go backend / 服务层的真实约定与模式。由 `00-bootstrap-guidelines` 任务从真实代码填实。

---

## Overview

本目录记录**本项目实际**的 Go backend 层模式（services/*/internal 分层、entry-api 路由、biz 编排、repository 数据访问、domain 模型、config 启动、错误翻译、日志、质量门禁）。
方法学（分层依赖律、doc_type 七类、五阶段 Gate）见 `../harness/` 与 `../guides/golden-path.md`，本目录只写「这个项目实际怎么做」，供 sub-agent 匹配本项目风格。

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | `services/*/internal` 的真实分层目录组织 | To fill |
| [API Design](./api-design.md) | entry-api：net/http 路由、JSON 编解码、错误码映射 | To fill |
| [Service Patterns](./service-patterns.md) | biz：service 编排与依赖注入边界 | To fill |
| [Repository & Data](./repository-data.md) | repository 数据访问与 db 迁移 | To fill |
| [Domain Model](./domain-model.md) | domain 模型与 sentinel error 归属 | To fill |
| [Config & Runtime](./config-runtime.md) | `config.Load`、env 前缀、启动关闭序列 | To fill |
| [Error Handling](./error-handling.md) | `sql.ErrNoRows` → sentinel 翻译与包装风格 | To fill |
| [Logging](./logging.md) | logger 注入、结构化字段、请求链路 ID | To fill |
| [Quality](./quality.md) | go build/vet/test/golangci-lint 命令与门禁 | To fill |

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
