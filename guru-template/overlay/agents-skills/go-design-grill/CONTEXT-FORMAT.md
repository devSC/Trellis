# CONTEXT.md 格式（Go 后端术语表）

`CONTEXT.md` 是仓库的**领域术语表**——只定义概念、关系与歧义裁定，**零实现细节**（实现归 design / golden-path / project-conventions）。拷问中磨出新术语或裁定一处歧义时即回写本文件。

## 结构

```md
# {Context 名}

{一两句：这个 context 是什么、为何存在。}

## Language

**User**：
平台为之分配代理凭据的代理用户（proxy user），对应 `users` 表。
_避免_：账号、客户、buyer

**ApplicationAccount**：
归集若干 User 的应用账号（计费/归属上级），对应 `application_accounts` 表。
_避免_：账号、租户

**ProxyNode**：
被控制面服务渲染期望态、由数据面 agent 消费拉取的代理节点。
_避免_：服务器、机器、实例

## Relationships

- 一个 **ApplicationAccount** 拥有零到多个 **User**
- 一个 **User** 的变更会触发其相关 **ProxyNode** 的期望态（DesiredNodeConfig）重算
- **DesiredNodeConfig** 由控制面服务生成、数据面 agent 消费（跨服务契约，单向）

## Example dialogue

> **开发：**"管理员创建一个 **User** 时，要不要立刻把它下发到 **ProxyNode**？"
> **领域专家：**"不立刻下发——创建只触发期望态重算（`ConfigSyncService.TouchNodesForUser`），数据面 agent 下一轮按自己的节奏拉 **DesiredNodeConfig**。"

## Flagged ambiguities

- "账号"曾同时指 **User** 与 **ApplicationAccount**——裁定：二者是不同表、不同概念，术语表分别固定，prd/design 不得混用。
- "同步"曾同时指 service 内部的期望态重算（`ConfigSyncService`）与数据面 agent 的契约拉取——裁定：前者写 service 编排副作用，后者写跨服务契约消费，分别归属。
```

## 规则

- **要有主见。** 同一概念有多个词时，挑最好的一个，其余列为"避免"的别名。
- **显式标注冲突。** 术语被歧义使用时，在 "Flagged ambiguities" 点名并给出清晰裁定（如上面 `User` vs `ApplicationAccount`）。
- **定义保持紧凑。** 一句话为限。定义它**是什么**，不写它**怎么做**（怎么做归 design/golden-path）。
- **展示关系。** 用加粗术语名表达关系与基数（一对多、单向触发、跨服务消费方向）。
- **只收本项目领域专有的术语。** 通用编程概念（context 超时、sentinel error、连接池、`errors.Is`、HTTP 状态码、JSON tag 等）**不进术语表**，即使项目大量使用——它们是平台方法（golden-path）或语言惯例，不是领域语言。加一个词前先问：这是本 context 独有的概念，还是通用编程/Go 概念？只有前者进表。
- **按子标题分组。** 出现自然簇（如"用户域 / 节点域 / 计费域"）时用子标题分组；若全部术语属同一内聚区域，扁平列表即可。
- **写一段示例对话。** 开发与领域专家的对话，演示术语如何自然交互、厘清相邻概念的边界（如 User 创建 → 期望态重算 → 节点拉取的链路）。

## 单 context vs 多 context 仓库

**单 context（多数仓库）：** 仓库根一个 `CONTEXT.md`。

**多 context（如 monorepo 多服务）：** 仓库根放一份 `CONTEXT-MAP.md`，列出各 context 落在哪个 `services/<svc>/`、彼此如何关联：

```md
# Context Map

## Contexts

- [Control](./services/<control-svc>/CONTEXT.md) — 管理面：User/ApplicationAccount 主数据、鉴权会话、渲染节点期望态
- [Proxy](./services/<proxy-svc>/CONTEXT.md) — 数据面：消费 DesiredNodeConfig，落地代理监听与路由

## Relationships

- **Control → Proxy**：Control 渲染 `packages/contracts/DesiredNodeConfig`；Proxy 拉取并落地（单向，跨服务契约）
- **Control ↔ Proxy**：共享类型 `DesiredNodeConfig` 及其嵌套结构，owner 在 `packages/contracts/`，Proxy 不反向写 Control 的 `internal/`
```

本 skill 推断采用哪种结构：

- 存在 `CONTEXT-MAP.md` → 读它定位各 context。
- 只有仓库根 `CONTEXT.md` → 单 context。
- 两者都无 → 首个术语裁定时按本格式惰性创建仓库根 `CONTEXT.md`。

多 context 时，推断当前拷问主题归属哪个服务的 context；不清楚则问用户（不擅自把 Control 的术语写进 Proxy 的表）。
