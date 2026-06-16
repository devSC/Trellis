# 需求文档导航（语义SSOT最小示例）

## 文档说明

- 本文档集满足语义SSOT：`README.md` 仅做导航与追踪，不承载第一章/第二章事实正文。
- 第一章与第二章入口组织主定义在 `requirement-main.md`；第二章为入口组织结构，本示例因存在 Web 控制台而采用页面组织结构。
- 第一章主定义包含“核心能力定义”，用于在进入概要设计前完成核心能力收敛。
- 页面详细规则、API 契约（若适用）、CLI Command 契约（若适用）、非功能要求分别在独立文档主定义。

## 接口适用性声明

- API：适用。原因：本示例包含服务端可调用接口契约，用于导入简历、查询列表和更新基础信息，符合标准包 `5.1` 中“API 适用”的定义。
- CLI：适用。原因：本示例包含 `resume-tool sync --all` 命令入口，供运维或自动化任务触发全量同步，符合标准包 `5.1` 中“CLI 适用”的定义。

## 文档导航

- [主需求文档（第一章、第二章）](./requirement-main.md)
- [前端页面详细需求](./requirement-web-console.md)
- [服务端 API 需求（若适用）](./requirement-api.md)
- [CLI Command 需求（若适用）](./requirement-cli-command.md)
- [非功能需求](./requirement-non-functional.md)

说明：最小示例同时提供 API/CLI 文档用于演示编号与追踪关系，不代表“API/CLI 默认必有”；实际项目需按标准包中的“API/CLI 适用标准”判定是否启用，并在 README 中显式声明适用性。

## 章节追踪矩阵（最小示例）

| 主题 | 主定义位置 | 说明 |
| --- | --- | --- |
| 第一章：产品总述 | `requirement-main.md` | 单一来源 |
| 第二章：入口组织结构（本示例为页面组织结构） | `requirement-main.md` | 单一来源 |
| 第三章起：页面详细描述 | `requirement-web-console.md` | 单一来源 |
| 服务端 API（若适用） | `requirement-api.md` | 单一来源 |
| CLI Command（若适用） | `requirement-cli-command.md` | 单一来源 |
| 非功能需求 | `requirement-non-functional.md` | 单一来源 |

## 编号差集结果（最小示例）

编号差集判定口径引用标准包第 6 章；本示例不重复定义规则，仅展示当前文档集结果。

| 差集类型 | 本示例结果 |
| --- | --- |
| 正常不映射 | `REQ-UC-001`、`REQ-UC-002`、`REQ-UC-003` 无命令入口；`REQ-UC-004` 无接口入口 |
| 真实 `UC-接口映射豁免` | 无 |
| 缺失映射 | 无 |

## 入口分支与非功能可达性（最小示例）

本矩阵仅展示 `REQ-UC -> 页面/API/CLI -> 非功能` 的可达关系，非功能约束主定义仍在 `requirement-non-functional.md`。

| REQ-UC-ID | 页面/入口主定义 | API/CLI 意图 | 非功能约束入口 |
| --- | --- | --- | --- |
| `REQ-UC-001` | `requirement-web-console.md` 第五章 | `API-INTENT-001` | `requirement-non-functional.md` 的安全、可用性、兼容性 |
| `REQ-UC-002` | `requirement-web-console.md` 第三章 | `API-INTENT-002` | `requirement-non-functional.md` 的性能、兼容性 |
| `REQ-UC-003` | `requirement-web-console.md` 第四章 | `API-INTENT-003` | `requirement-non-functional.md` 的安全、可用性、兼容性 |
| `REQ-UC-004` | `requirement-cli-command.md` | `CLI-INTENT-001` | `requirement-non-functional.md` 的安全 |

## 文档版本

- 版本：v0.1.0
- 最后更新：2026-04-24
- 状态：示例模板
