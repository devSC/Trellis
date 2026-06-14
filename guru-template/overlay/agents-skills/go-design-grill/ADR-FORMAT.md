# ADR 格式（Go 后端架构决策记录）

ADR 落在目标仓库 `docs/adr/`，顺序编号：`0001-slug.md`、`0002-slug.md` …… slug 用短横线连接、体现决策主题（如 `0001-no-orm-raw-sql`、`0002-hmac-cookie-session`）。

`docs/adr/` 目录**惰性创建**——只在第一条 ADR 真正需要时建。

## 模板

```md
# {决策的一句话标题}

{1~3 句：上下文是什么、我们决定了什么、为什么。}
```

就这样。一条 ADR 可以只有一段。价值在于记录**做了一个决策**以及**为什么**——而不是把章节填满。正文中文优先，代码标识符/库名/路径/协议字段保留原文（如 `database/sql`、`net/http`、`packages/contracts`、`<SVC>_*`）。

## 可选章节

只在确实增加价值时加，多数 ADR 用不上：

- **Status** frontmatter（`proposed | accepted | deprecated | superseded by ADR-NNNN`）——决策会被重新审视时有用，对齐 project-conventions 槽位升级（如某 SLOT 从"当前无"升到引入某库）的状态流转。
- **Considered Options**——只在被否决的备选值得记住时（如"评估过 `ent` 与 `sqlc`，选 `sqlc` 因 X"）。
- **Consequences**——只在有不显然的下游影响要点名时（如"引入 `wire` 后，新增依赖必须改 ProviderSet，`app.New()` 手工构造链废弃"）。

## 编号

扫描 `docs/adr/` 取现存最高编号 +1，不跳号、不复用。

## 何时提议 ADR（三条全中才提）

1. **难以回头** —— 以后改主意的代价不小。
2. **缺上下文会困惑** —— 未来读者看代码会想"为什么偏要这样做？"。
3. **真实权衡的产物** —— 确实有备选项，为具体理由选了其一。

易回退就跳过（反正会被改回去）；不令人意外就没人会问为什么；没有真备选就没什么可记的（"我们做了显而易见的事"不值得记）。

## Go 后端哪些决策够格记 ADR

拷问中命中以下情形、且三条全中时，当场起草 ADR（用户确认后落盘）：

- **架构形态与分层偏离**：刻意偏离 golden-path 分层依赖律的决策及其代价（注意：分层律本身是不可豁免硬红线，"偏离"通常应回退而非记 ADR；只有经用户确认的、有边界证据的合法例外才记，如 transport 仅为 `errors.Is(err, repository.ErrNotFound)` 这一类哨兵判定而 import repository——这本身已是 SLOT-17 登记项，扩散到新代码须 ADR 背书）。
- **技术栈槽位切换（SLOT 升级，带锁定成本）**：`SLOT-01` 无 DI → 引入 `wire`；`SLOT-02` 原生 `database/sql` → `sqlc`/`ent`；`SLOT-03` 标准 `log` → `log/slog`/`zap`；`SLOT-05` REST JSON → gRPC；`SLOT-04` `testing` → `testify`/`ginkgo`。这些都"要一个季度才换得动"，必须 ADR + 升级对应槽位后才能引入，拷问/实现阶段不得私自拍板。
- **跨服务契约协议形态**：控制面服务与数据面 agent 经 `packages/contracts/DesiredNodeConfig` 同步 JSON 期望态 vs 改走事件/消息——契约协议是双方合同的锁定点。
- **数据/范围归属边界（显式的"不做"和"谁拥有"）**：如"`users` 数据由其属主服务拥有，其它服务只经 `packages/contracts` 按 ID 引用，不反向写库"；"会话密钥只经 `<SVC>_SESSION_SECRET` 注入，不入库"。显式的边界与拒绝和肯定同样有价值。
- **鉴权/会话方案**：现状自实现 HMAC-SHA256 签名 cookie + bcrypt（`internal/auth/session_manager.go`、`admin_auth_service.go`）；切换到第三方会话/JWT 库属架构决策，记 ADR + 升级 `SLOT-10`。
- **代码不可见的约束**：合规/法规导致的技术选择（如"不可采集某类用户数据"）、外部契约的 SLA（如"响应须 < 200ms 因合作方接口约束"）。
- **非显然的被否决备选**：评估过却否决、且半年后会有人再提的方案（如"评估过 chi 路由，否决，坚持 `net/http ServeMux` 保持零运行时魔法"）——记下来，免得下次再被提一遍。

不够格的（不记，照 golden-path 默认走即可）：遵循分层迷你路径新增一个常规 endpoint、复用既有 `scanXxx`/helper、按既有 env 前缀加一个配置键、沿用 `testing` 写单测。
