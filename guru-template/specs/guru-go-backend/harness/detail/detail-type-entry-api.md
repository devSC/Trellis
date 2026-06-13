# L2 类型规范：entry-api（HTTP handler 入口行为）

> 从属于 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；本文件只写 entry-api 类型的差异规则，冲突以 L1 为准。
> golden-path 对应：`.trellis/spec/guides/golden-path.md` 的 transport(handler) 迷你路径、分层依赖律（handler → service → repository → domain）、错误处理范式（sentinel error + `%w` 包装 + `errors.Is`）、启动/关闭契约（Handler 接收 context）。

## 适用对象

`services/<svc>/internal/transport/http/` 下的 HTTP handler 入口：一组共享 route prefix 的 `net/http` handler 集合，负责把外部 HTTP 请求解析、校验、映射为 service 调用，并把 service 结果与 sentinel error 收口为 HTTP 响应。

适用：注册到 `http.ServeMux` 的 handler 函数 / handler struct 方法、入口中间件链触达的请求处理层。
不适用：
- 业务规则与状态机（归 `internal/service`，doc_type=`biz-behavior`）。
- 数据访问与 SQL（归 `internal/repository`，doc_type=`repository`）。
- 后台定时/消费触发入口（归 doc_type=`entry-background-trigger`）。
- `cmd/<svc>/main.go` 与 `internal/app` 的启动/关闭编排（归 doc_type=`runtime-deployment`）。

一个 entry-api 设计单元对应一组共享 prefix 的 handler；每个 route+method 默认对应一个入口行为 `BHV-NNN`，必须逐 route+method 展开行为、Req/Resp、参数映射与 service 调度，不得用「一个 handler 文件 = 一个行为」压缩多个真实 route。

## 合同八问的类型特化

1. **承接行为**：逐条引用 prd 的 `BHV-NNN`；每个 `route + HTTP method`（如 `POST /v1/users`）独立绑定一个入口行为。行为清单表必含列：`BHV 编号 | route + method | handler 方法名 | 目标 service 方法 | 承接的概要场景 id`。无承接行为或幽灵引用被 gate 断链拦截。

2. **输入 / 输出 / 错误**：先固定协议入口，再写编排。
   - 输入 = `path / query / header / body / context` 五类来源**分列**（禁止混写成一个泛化来源）；逐字段给：字段路径、Go 类型、必填、来源、入口校验、空值策略、映射目标 service 入参。`ctx context.Context` 必为 handler 第一形参，承载 timeout / cancel / 鉴权产物（如 actorID）。
   - 输出 = 成功响应体结构（Go struct + JSON tag）、HTTP 状态码、`Content-Type`；可穷举字段用 Go `iota` 枚举或具名常量 + 其 JSON 序列化口径，禁止裸 `int/string` 魔法值。
   - 错误 = **错误响应三态收口**：每个行为必须给「入口校验失败 / service sentinel error / 兜底未知错误」三类到 HTTP 状态码 + 错误响应体的映射表（见硬规则错误处理）。

3. **读写状态**：handler 是无状态适配层，**不持有业务状态**。只读：解析自请求的入参、`ctx` 中的鉴权产物。不写任何业务状态、不写 DB、不写缓存——所有持久化与状态变更 owner 是 service / repository，必须回指概要归属表行。

4. **依赖（正反面都写）**：
   - 可调用：注入的 service 接口（构造注入，字段为 service interface 类型）、框架基础 infra（`*slog.Logger` 或项目日志门面、validator/decoder helper、metrics）。
   - **禁止调用**：`repository` 实现、`database/sql` / `lib/pq` / DB 连接、缓存客户端、外部 HTTP 客户端、其他 transport handler、`domain` 之外的跨 `internal` 包（违反分层单向律，P1）。需要业务无关技术能力时调用概要已抽取的纯函数工具，不在 handler 内重复封装。

5. **失败收口**：每条失败路径 → 明确的 HTTP 状态码 + 错误响应体。service 上抛的 sentinel error 必须用 `errors.Is(err, service.ErrXxx)` 分类映射，**不得吞错**（不允许 `_ = err` 或裸 `return nil`）；未命中任何 sentinel 的错误统一映射 500 并记录日志（含 correlation/trace id），不向客户端泄露内部细节。

6. **事件 / 后置结果**：handler 入口自身通常无业务副作用（写 `无`）；只在响应前做接口指标 / 访问日志上报。若入口承载审计或埋点，须逐条写明事件名、触发时机、消费方；业务事件（领域事件、MQ 投递）由 service 触发，不在 handler 制造。

7. **测试映射**：每个行为映射 unit test（用 `httptest.NewRequest` + `httptest.ResponseRecorder` 驱动 handler，mock service 接口，测试框架按 project-conventions 槽位，当前 `testing`，可升 testify）。测试点必须覆盖：成功路径 + 每条入口校验失败 + 每个 service sentinel error 分支 + 兜底未知错误。不在此层测业务规则正确性（归 service 单测）、不测真实 DB（归 repository 集成测试）。

8. **不得补造**：不发明业务规则 / 状态机判定（属 service）；不决定缓存 / 持久化 / 事务边界（属 repository / service）；不定义跨服务契约 schema（属 `packages/contracts/`）；不私自拍板 project-conventions「未选定」槽位（如 ORM、鉴权实现）。

## 类型硬规则（golden-path 锁定，不可豁免）

- **框架轻量**：路由一律注册到 `net/http` `ServeMux`，handler 形态为 `func(w http.ResponseWriter, r *http.Request)` 或等价 struct 方法。禁用 `gin` / `echo` / `fiber` 等重型框架与其上下文对象。
- **handler 接收 context**：业务调用必须把 `r.Context()` 透传给 service 方法（`svc.DoX(ctx, ...)`），承接请求级 timeout / cancel；禁止 `context.Background()` 顶替请求上下文，禁止把 `*http.Request` 透到 service 层。
- **薄适配只触发 service**：handler 主路径只做「解析 → 入口校验 → 映射入参 → 调用一个 service 方法 → 映射结果/错误 → 写响应」。禁止在 handler 内编排多步业务流程、做业务分支判定、组合多个 repository 结果。
- **sentinel error 上抛不吞**：service 暴露包级 sentinel（`var ErrNotFound = errors.New("user not found")`），service 内用 `fmt.Errorf("%w: ...", ErrNotFound)` 链式包装；handler 用 `errors.Is` 检查并映射 HTTP 状态码。handler **不得**新造平行错误体系、不得吞掉未识别错误、不得把内部错误文案直接回给客户端。
- **分层依赖律**：导入只允许 `internal/service` 接口、`internal/domain`（共享类型）、框架/标准库 infra；不得导入 `internal/repository`、DB 驱动、其他服务的 `internal` 包。
- **配置引用**：handler 不读环境变量、不调用 `config.Load()`；所需配置（如响应超时、分页上限默认值）由构造注入或 service 持有，回指 doc_type=`config-runtime-contract`。env 前缀按服务区分（如 `CONTROL_API_*`）。
- **隐私边界**：handler 落在 `internal/`，跨服务请求/响应契约引用 `packages/contracts/`，不在 handler 内私自定义跨服务 schema。
- **可穷举字段**：请求/响应中可穷举概念用 Go 具名枚举（`iota` 常量或字符串常量）+ 显式 JSON 序列化/反序列化口径 + 非法值错误收口；owner 按语义归属（业务枚举回指 service，运行/网关枚举回指 runtime/config）。

## 无业务行为入口豁免（条件）

仅 `health` / `readiness` / 静态能力信息等**确无业务行为**的入口允许无 service 依赖。此时必须：在依赖正反面声明 `no_business_behavior_entry` 豁免与涉及的 `BHV-NNN`；行为正文仍按八问展开本地探针/技术处理链路与失败分支；枚举 owner 回指 runtime/config，不得退回魔法值，也不得为技术枚举补造业务 owner。

## 可验证信号（gate 取证锚点）

- 每个 `route + method` 都能定位独立 `BHV-NNN`、handler 方法、目标 service 方法与五类来源参数表。
- handler 签名含 `ctx context.Context`（或 `r.Context()` 透传到 service）；service 调用入参含 `ctx`。
- 错误处理表逐行对应一条失败路径；每个 service sentinel error 都有 `errors.Is` 分支与 HTTP 状态码；存在兜底 500 分支。
- 依赖正反面齐全：注入项均为 service interface / infra；反面显式列出不调用 repository/DB/缓存/其他 handler。
- 测试映射覆盖成功 + 全部失败路径，使用 `httptest` + mock service。
- 不得补造清单逐单元存在。

## 好 / 坏例子

✅ 好（`CreateUser` 行为，`POST /v1/users`）：
- 行为签名：`func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request)`；主路径 `ctx := r.Context()` → 解析并校验 body（`email` 非空且格式合法，否则 400）→ 映射 `service.CreateUserInput` → 调用 `h.userSvc.CreateUser(ctx, in)` → 成功 201 返回 `UserView`。
- 错误处理表完整：`errors.Is(err, service.ErrEmailTaken)` → 409；`errors.Is(err, service.ErrInvalidInput)` → 400；其余 → 500 + `slog.Error("create user failed", "err", err, "trace_id", tid)`，响应体只回通用文案。
- 依赖只注入 `userSvc service.UserService` 接口 + `logger *slog.Logger`；反面声明不导入 `repository`、不碰 `database/sql`。
- 枚举 `UserStatus`（`iota`：`StatusActive`/`StatusSuspended`）给 JSON 字符串序列化口径，owner 回指 `internal/service` 用户域。

❌ 坏：
- 「处理用户相关请求」一句话带过，多个 route 共享一个泛化行为，无逐 route 参数表。
- handler 直接 `db.QueryRow(...)` 或 `import ".../internal/repository"`（越层，P1）。
- 调用 service 用 `context.Background()` 而非 `r.Context()`，丢失请求 timeout（违反 handler 接收 context，P1）。
- `if err != nil { return }` 吞掉 service error 或 `_ = h.userSvc.CreateUser(...)`（吞 sentinel error，P1）；错误响应文案直接写 `err.Error()` 泄露内部细节。
- handler 内做业务判定（如「余额不足则拒绝」），把状态机搬进入口层（应归 service）。
- 在 handler 内 `gin.Context` / `c.JSON(...)`（违反框架轻量律，P1）。
