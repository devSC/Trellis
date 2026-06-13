# guides/ 索引

> guru-go-backend spec 库的通用方法入口。本文件只做导航，不承载规则正文。

| 文件 | 职责 |
|------|------|
| [golden-path.md](./golden-path.md) | Go 后端通用方法唯一真源（SSOT）：模块形态、分层依赖律、各层迷你路径、错误处理范式、启动/关闭契约、入口决策树、禁止清单 |

- **项目级取值不在本目录**：DI 框架、ORM、日志、测试框架、API 风格、DB 驱动、lint、文档生成、会话/鉴权等槽位取值一律走 [`../conventions/project-conventions.md`](../conventions/project-conventions.md)（入口见 [`../conventions/index.md`](../conventions/index.md)）。
- **五阶段流程规则不在本目录**：见 [`../harness/index.md`](../harness/index.md)。
- **安装后装载路径**：通用方法真源落在 `.trellis/spec/guides/golden-path.md`，流程骨架落在 `.trellis/spec/harness/*`。
