# Project Conventions 模板（Go 后端项目约定槽位）

> **这是什么**：配置包定义的"项目约定槽位"模板（Go 后端 Harness 专用）。配置包的 SSOT 只锁方法与团队栈级 canonical（即 golden-path 硬规则），**项目级取值永不进配置包**——每个服务/服务集仓库按本模板填一份取值文件（建议路径：目标仓库 `.trellis/spec/conventions/project-conventions.md`），由各阶段 writing/review Skill 在硬前置中装载（装载源：`.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md`）。
> **填写规则**：复制本模板 → 删除说明文字 → 逐槽位填写。每个取值必须给**代码证据**（仓库内真实路径）；没有证据的取值视为未填。
> **变更规则**：修改任何槽位取值属于服务级架构决策，需要 ADR 记录后方可生效；跨服务统一取值的变更需经全 monorepo owner 评审。
> **与硬规则的关系**：golden-path 硬规则（见 `.trellis/spec/guides/golden-path.md`）锁死的不可豁免约束 **不在本模板槽位内**——槽位只钉"可按服务调整"的项目级选择。任何槽位取值与硬规则冲突即非法（见 C4）。

---

## 0. 元信息（必填）

| 字段 | 取值 |
|------|------|
| 服务名 / module path | `<svc>` / `<go_module_path>` |
| monorepo 仓库路径 / 服务子路径 | `<repo>` / `services/<svc>/` |
| Go 版本（go.mod `go` 指令） | `<go_version>` |
| 填写日期 / 填写人 | `<date>` / `<who>` |
| 取值依据 | 实测扫描 / 团队决策（附 ADR 链接） |

> 说明：本模板假定 Go monorepo 形态——服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，入口在 `cmd/<svc>/main.go`，跨服务契约在 `packages/contracts/`。若服务集内多个服务取值不一致，本文件按**单服务**填写；同一 monorepo 内多服务各填一份，元信息区分 `<svc>`。

---

## 1. 槽位清单（全部必填）

> 每个槽位字段：**决策问题**（要钉死什么）· **本项目取值** · **代码证据**（≥1 条真实路径）· **生效范围**（新代码 only / 全量）· **备注**。
> 取值可以是"待定"，但待定项必须写明决策人与期限，且待定总数 ≤ 2，否则项目约定视为未就绪（硬前置不通过）。
> 每个槽位末尾以引用形式给出 safa-land control-api 的**实测基线取值**，作为填写参照（不是强制取值）。

### SLOT-01 DI 框架
- 决策问题：依赖装配方式钉死为哪一种——手工构造（在 `app.New()` 内显式 new 并注入）还是编译期 DI（`google/wire`）？是否允许运行期反射型容器（如 `uber/dig`、`fx`）？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/app/app.go` 的构造序列；若引入 wire，给 `wire.go` / `wire_gen.go` 路径）
- 生效范围：
- 备注：禁止运行期反射型容器是建议默认（与"轻量、可读启动序列"一致），但本槽位允许项目选择 wire。若选 wire，构造仍须收敛在 `app` 包，不得在 `transport`/`service` 内自取依赖。
- safa-land 实测基线：**手工构造**，无 DI 框架；`app.New()` 顺序构造 config → repository → service → handler 并逐层注入。可演进为 `google/wire`。

### SLOT-02 ORM / 数据访问层
- 决策问题：repository 层访问 DB 的方式钉死为哪一种——原生 SQL（`database/sql` + 驱动）、`sqlc`（SQL 编译为 Go）、`ent`（schema-as-code ORM），还是其它？是否允许 query builder（如 `squirrel`）？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/repository/user_repository.go`；若用 sqlc 给 `sqlc.yaml` 与生成目录；若用 ent 给 `ent/schema/` 目录）
- 生效范围：
- 备注：无论选哪种，**repository 是唯一持有 DB 句柄的层**（service 不得直接 import 驱动或拿 `*sql.DB`）是硬规则边界，不可由本槽位豁免。本槽位只钉"用什么写查询"。
- safa-land 实测基线：**原生 SQL**（`database/sql` + `lib/pq`，PostgreSQL），手写 `db.QueryRowContext` / `db.ExecContext`。可演进为 `ent` 或 `sqlc`。

### SLOT-03 日志方案
- 决策问题：日志库钉死为哪一种——标准库 `log`、标准库 `log/slog`（结构化）、`uber-go/zap`，还是 `rs/zerolog`？日志 handle 如何注入（全局 logger / context 携带 / 构造注入）？
- 本项目取值：
- 代码证据：（如 logger 初始化处 `services/<svc>/internal/app/app.go`，及一处业务日志调用点）
- 生效范围：
- 备注：建议演进方向为结构化日志（`slog`/`zap`）并通过构造注入而非全局单例，便于按请求附加 trace 字段。本槽位钉具体库与注入方式。脱敏与等级规则属团队栈级约定，不在本槽位。
- safa-land 实测基线：**标准库 `log`**（非结构化），全局默认 logger。可演进为 `log/slog` 或 `zap`。

### SLOT-04 测试框架
- 决策问题：单测断言/组织方式钉死为哪一种——纯标准库 `testing`、`stretchr/testify`（assert/require + suite + mock）、`onsi/ginkgo`（BDD）？mock 生成用什么（手写 / `mockgen` / `mockery`）？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/service/user_service_test.go`；若用 testify 给一处 `require.NoError`；若有 mock 给生成目录）
- 生效范围：
- 备注：测试文件与被测文件同包同目录（`xxx_test.go` 紧邻 `xxx.go`）是 Go 惯例硬约束，不由本槽位豁免。本槽位钉断言库与 mock 策略。表驱动测试为推荐默认。
- safa-land 实测基线：**标准库 `testing`** + 表驱动；mock 手写。可演进为 `testify`（assert/require/suite）或 `ginkgo`。

### SLOT-05 API 风格
- 决策问题：对外接口风格钉死为哪一种——REST over HTTP/JSON、gRPC、二者并存（写明分界，如内部 gRPC + 边缘 REST）？错误响应体的统一形态？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/transport/http/router.go`；若 gRPC 给 `.proto` 与生成目录）
- 生效范围：
- 备注：无论 REST 还是 gRPC，**handler 不直接持有 DB、只调 service**，分层依赖律不变。REST 场景下路由器必须为 `net/http` `ServeMux`（禁 gin/echo，硬规则）；gRPC 场景由 `transport/grpc` 子包承载。本槽位钉风格与统一错误体。
- safa-land 实测基线：**REST + JSON**，`net/http` `ServeMux` 路由，handler 编解码 JSON。可演进为 gRPC（新增 `transport/grpc`）。

### SLOT-06 DB 驱动 / 连接形态
- 决策问题：数据库类型与驱动钉死为哪一组——PostgreSQL `lib/pq`、PostgreSQL `jackc/pgx`（含 `pgxpool`）、MySQL `go-sql-driver/mysql`，还是其它？连接池如何配置、连接串如何来自 config？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/app/app.go` 打开连接处；驱动 import 路径；连接池 `SetMaxOpenConns` 等设置点）
- 生效范围：
- 备注：连接串、连接池参数必须来自 `config.Load()`，禁止 handler/service 持有连接配置（与 SLOT-08 配置律一致）。本槽位钉驱动选型与连接形态；驱动 import 只允许出现在 repository/app 层。
- safa-land 实测基线：**PostgreSQL + `lib/pq`**，`database/sql` 标准接口，`*sql.DB` 由 app 层持有并注入 repository。可演进为 `pgx`/`pgxpool`。

### SLOT-07 lint / 静态检查
- 决策问题：lint 工具链钉死为哪一套——`golangci-lint`（配置文件路径与启用 linters 集）、`go vet` + `staticcheck` 独立组合？lint 在何处触发（Makefile target / CI / pre-commit hook）？
- 本项目取值：
- 代码证据：（如 `.golangci.yml` / `.golangci.yaml`；`Makefile` 的 `lint` target；CI workflow 路径）
- 生效范围：
- 备注：`gofmt`/`goimports` 格式化为不可豁免基线。本槽位钉 lint 聚合器与启用的 linters；新启用某条 linter 若产生大量存量告警，相关豁免登记入 SLOT-17（存量违例清单）。
- safa-land 实测基线：**`golangci-lint`**，由 `Makefile` `lint` target 触发；启用集见 `.golangci.yml`。

### SLOT-08 配置加载
- 决策问题：配置来源与加载方式钉死为哪一种——纯环境变量 + 默认值（手写 `os.Getenv` + fallback）、`caarlos0/env`/`kelseyhightower/envconfig`（tag 解析）、`spf13/viper`（多源）？env 前缀如何区分服务？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/config/config.go` 的 `Load()`；env 前缀常量如 `CONTROL_API_*` 出现处）
- 生效范围：
- 备注：**配置集中在 `config.Load()`、其它层不读 env**是硬规则边界。env 前缀按服务区分（如 `CONTROL_API_*`）防止跨服务串扰。本槽位钉解析方式与前缀方案，不豁免"集中加载"约束。
- safa-land 实测基线：**纯环境变量 + 默认值**，手写 `os.Getenv` + fallback，集中于 `config.Load()`，前缀 `CONTROL_API_*`。可演进为 `envconfig`/`viper`。

### SLOT-09 文档生成
- 决策问题：API 文档生成方式钉死为哪一种——无（仅手写 README）、`swaggo/swag`（注释生成 Swagger/OpenAPI）、手写 OpenAPI YAML + 校验、由 proto 生成（gRPC 场景）？文档产物落在哪、谁负责更新？
- 本项目取值：
- 代码证据：（如 `docs/` 目录、`swagger.json`/`openapi.yaml`、`swag init` 在 Makefile 的 target；若当前无则填"无"并写计划）
- 生效范围：
- 备注：文档生成属可选演进项，当前为"无"是合法取值，但须显式声明并写明引入计划（决策人 + 期限），否则视为待定槽位计入 C2 上限。本槽位钉生成器与产物位置。
- safa-land 实测基线：**无**（仅 `AGENTS.md` + README 描述接口）。可演进为 `swaggo/swag`（注释驱动 Swagger）或手写 OpenAPI。

### SLOT-10 会话 / 鉴权
- 决策问题：鉴权方案钉死为哪一种——自实现签名 cookie（HMAC-SHA256）+ 密码哈希（`bcrypt`）、JWT（`golang-jwt`）、第三方 session 库、OAuth/OIDC 接入？鉴权在哪一层施加（middleware in `transport` / `auth` 包）？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/auth/` 下签名/校验实现；middleware 注册处 `transport/http/router.go`；密码哈希调用点）
- 生效范围：
- 备注：鉴权逻辑收敛在 `internal/auth` 包并通过 `transport` middleware 注入，**service/repository/domain 不感知 cookie/header**。密钥来自 `config`（与 SLOT-08 一致），禁止硬编码密钥/盐。本槽位钉鉴权机制与施加层。
- safa-land 实测基线：**自实现 HMAC-SHA256 签名 cookie + `bcrypt` 密码哈希**，`internal/auth` 实现签发/校验，`transport` middleware 拦截。可演进为 JWT 或 OIDC。

### SLOT-11 包组织 / 分层目录
- 决策问题：服务内部包划分钉死为哪种形态——`internal/{app,config,transport,service,repository,domain,auth}` 标准分层、按领域聚合（`internal/<feature>/{handler,service,repo}`）、二者混合？跨服务共享代码进哪个目录？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/` 实际子目录树；`packages/contracts/` 下跨服务契约文件；`cmd/<svc>/main.go`）
- 生效范围：
- 备注：**分层依赖律 `handler(transport) → service → repository → domain` 严格单向无循环、除 domain 外不跨 internal 包互相导入、`internal/` 隐私边界、跨服务契约只走 `packages/contracts/`**——均为硬规则，不由本槽位豁免。本槽位钉子包是否按领域再切分及共享代码落点。
- safa-land 实测基线：**标准分层** `internal/{app,config,transport,service,repository,domain,auth}`，入口 `cmd/<svc>/main.go`，跨服务契约 `packages/contracts/proxy_node_config.go`。

### SLOT-12 数据库迁移
- 决策问题：schema 迁移工具与组织钉死为哪一种——`golang-migrate/migrate`（`NNNN_*.up.sql`/`*.down.sql` 成对）、`pressly/goose`、`ent` 内置 migrate、手工 SQL 脚本？迁移文件目录、命名、版本号规则、是否自动随启动执行？
- 本项目取值：
- 代码证据：（如 `db/migrations/` 目录及迁移文件命名样例；迁移触发处——Makefile target / CI / app 启动）
- 生效范围：
- 备注：迁移必须**版本号单调递增、成对 up/down（或工具等价物）、不修改已应用的历史迁移**（改 schema 一律追加新版本）。生产迁移与服务启动解耦为推荐默认（避免多实例并发自动迁移）。本槽位钉工具、目录与触发时机。
- safa-land 实测基线：**SQL 迁移文件**置于 `db/migrations/`，版本号前缀递增、up/down 成对（`golang-migrate` 风格）。可演进为 `goose` 或 `ent` migrate。

### SLOT-13 错误处理风格（项目级补充）
- 决策问题：sentinel error 的声明位置与命名钉死为何种约定——按服务层声明（`var ErrUserNotFound = errors.New(...)` 在 `service`/`domain`）、按包集中 `errors.go`？跨层包装时 `fmt.Errorf("%w: ...")` 的 message 前缀规范？面向 HTTP/gRPC 的错误码映射在哪一层做？
- 本项目取值：
- 代码证据：（如 `services/<svc>/internal/service/user_service.go` 的 sentinel 声明与 `%w` 包装点；`transport` 层 `errors.Is()` → HTTP status 映射处）
- 生效范围：
- 备注：**sentinel errors + `fmt.Errorf("%w: ...")` 链式包装 + `errors.Is()` 检查**是硬规则的错误处理骨架，不可豁免；禁用 `panic` 作控制流、禁裸字符串比较错误。本槽位只钉 sentinel 声明位置、message 前缀规范、错误→状态码映射层。
- safa-land 实测基线：服务级 sentinel error 声明于各 service 包顶部，跨层用 `fmt.Errorf("%w: ...")` 包装，`transport` 层用 `errors.Is()` 映射 HTTP status。

### SLOT-14 启动 / 关闭与超时
- 决策问题：进程生命周期钉死为何种形态——`main()` 监听信号（`SIGINT`/`SIGTERM`）→ `app.New()` → `app.Run()` → `app.Shutdown(ctx)` 的优雅关闭序列；HTTP server 读写超时、shutdown 超时取值；handler 是否一律接收 `context.Context` 并尊重 deadline？
- 本项目取值：
- 代码证据：（如 `cmd/<svc>/main.go` 信号处理；`services/<svc>/internal/app/app.go` 的 `Run`/`Shutdown`；server 超时设置点）
- 生效范围：
- 备注：**`main()` 控信号 → `New/Run/Shutdown` 生命周期、handler 接收 context 支持 timeout、优雅关闭**是硬规则，不可豁免。本槽位只钉具体超时数值与 shutdown 宽限期，以及超时值是否来自 config。
- safa-land 实测基线：`main()` 捕获信号 → `app.New()` → `app.Run()` → `app.Shutdown(ctx)`；HTTP server 设置读写超时，handler 透传 `context.Context`。

### SLOT-15 接口抽象 / DIP 策略
- 决策问题：层间依赖抽象钉死为哪一种——消费方本地声明最小接口（DIP，"accept interfaces, return structs"，在 service 包内按需声明 `xxxStore` 这类只含真正用到方法的小接口）、被依赖方导出大接口（在 repository 包导出 `UserStore`），还是 service 直接持有具体 `*repository.XxxRepository`？接口命名风格（业务化 `xxxStore` / `I` 前缀 / 集中 `interfaces.go`）？
- 本项目取值：
- 代码证据：（如 service 包内本地接口声明 `services/<svc>/internal/service/user_service.go` 的 `userStore`；构造函数返回具体类型的写法）
- 生效范围：
- 备注：**构造注入 + "accept interfaces, return structs"**（构造函数返回具体类型、消费方按需收窄接口）是团队栈级 canonical（见 golden-path §2.2），不可由本槽位反转为"返回接口/包级全局单例"。本槽位只钉接口声明位置（消费方本地 vs 被依赖方导出）、命名风格、是否允许 service 持有具体类型。
- safa-land 实测基线：**消费方本地小接口**，命名业务化 `xxxStore`（实测仅 `UserService.userStore` 与 transport 的 `initEnvService` 落实），其余 service 仍直接持有具体 `*repository.XxxRepository`（存量见 SLOT-17）。可逐步把各 service 收敛到本地接口抽象。

### SLOT-16 可穷举字段（枚举）表达
- 决策问题：status/role/protocol/mode 等可穷举概念钉死为哪种表达——Go `iota` 具名常量、字符串具名常量（`type NodeStatus string` + 常量集），还是裸 `string`？JSON 序列化口径与非法值如何收口（service 层 `switch`+default、DB `CHECK` 约束、二者兼有）？
- 本项目取值：
- 代码证据：（如 `packages/contracts/` 或 `internal/domain/` 的枚举类型定义；service 层枚举校验 `switch` 点；`db/migrations/` 的 `CHECK (col IN (...))`）
- 生效范围：
- 备注：**可穷举概念禁裸魔法值散落**为推荐默认；owner 按语义归属（业务枚举回指 service，运行/网关枚举回指 runtime/config）。本槽位钉枚举的 Go 类型层表达与非法值收口层。
- safa-land 实测基线：**现状裸 `string`**（`NodeStatus`/`NodeRole`/`ProxyProtocol`/`Mode`/`RoutingMode` 等），合法集合仅靠 DB `CHECK` 约束与 service 校验兜底，Go 类型层未建枚举（存量见 SLOT-17）。可演进为 Go 具名枚举类型。

### SLOT-17 存量违例清单（tech-debt 登记）
- 决策问题：已知的存量架构违例有哪些（供 review 的存量豁免判定使用：触碰存量记债不阻塞、新增违例阻塞）？
- 本项目取值：（逐条：违例描述 + 文件路径 + 关联槽位/硬规则 + 计划处置）
  - 示例格式：`[SLOT-03] internal/service/legacy_billing.go 仍用全局 log.Printf；待迁 slog（owner: <who>，期限: <date>）`
- 生效范围：全量
- 备注：本槽位是**存量豁免机制**的数据源，必须维护；清单外的违例一律按"新增"处理（阻塞）。若确无存量违例，必须显式写"无"（见 C5），不得留空。

---

## 2. 校验清单（writing/review 硬前置使用）

装载本约定文件的 Skill（来自 `.trellis/spec/harness/*`）必须先执行以下校验，任一不通过即终止并提示修复：

- [ ] **C1** 元信息五字段齐全（服务名/module path、仓库路径/服务子路径、Go 版本、填写日期/填写人、取值依据）。
- [ ] **C2** SLOT-01 ~ SLOT-17 全部存在；"待定"槽位 ≤ 2 且均写明决策人与期限（SLOT-09 取"无"亦须写明引入计划，否则计入待定上限）。
- [ ] **C3** 每个已填槽位至少 1 条代码证据路径（不校验路径内容，但路径必须存在于仓库；演进型取值如未落地可标"计划路径"并不计入已填）。
- [ ] **C4** 取值不得与 golden-path 硬规则冲突——以下不可被任何槽位豁免：net/http ServeMux（禁 gin/echo）、分层依赖律单向无循环、除 domain 外不跨 internal 包导入、sentinel errors + `%w` 包装 + `errors.Is()`、`main()` 控信号的 New/Run/Shutdown 生命周期 + handler 接收 context、config 集中 `Load()`、`internal/` 隐私边界、跨服务契约只走 `packages/contracts/`、gofmt/goimports 基线。
- [ ] **C5** SLOT-17 存量违例清单存在（可为空清单，但必须显式声明"无"）。

---

## 3. 槽位与门禁的对应关系（参考）

| 槽位 | 谁消费 |
|------|--------|
| SLOT-11 / SLOT-02 / SLOT-06 | hooks（import 边界 / 驱动落点拦截）、implementation-review（分层依赖律核查） |
| SLOT-01 / SLOT-14 | runtime（启动序列与装配合同）、implementation-review |
| SLOT-05 / SLOT-13 | entry-api（API 风格 + 错误码映射合同）、implementation-review |
| SLOT-02 / SLOT-06 / SLOT-12 | repository-data（数据访问 + 迁移合同）、implementation-writing |
| SLOT-10 | entry-api（鉴权 middleware 合同）、implementation-review |
| SLOT-03 / SLOT-04 / SLOT-07 / SLOT-08 / SLOT-09 | implementation-writing、CI gate（日志/测试/lint/配置/文档生成检查） |
| SLOT-15 / SLOT-16 | implementation-review（接口抽象/DIP 方向核查、枚举表达与非法值收口层核查） |
| SLOT-17 | 所有 review 的存量豁免判定 |

> 下游引用规范：行为引用裸 `BHV-NNN`（prd 标题）、设计单元引用裸 `UNIT-<slug>`（详细设计标题）、槽位引用裸 `SLOT-NN` token，便于 `guru_gate.py` 的结构检查（需求五要素、概要归属表 + 承接索引、详细合同八问、实现 trace 四节）跨文件追踪。
