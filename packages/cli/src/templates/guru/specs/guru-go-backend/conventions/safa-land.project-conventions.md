# Project Conventions — safa-land（Go 后端取值样例）

> 按 [project-conventions.template.md](./project-conventions.template.md) 的槽位填写。安装配置包时将本文件迁入 safa-land 仓库 `.trellis/spec/conventions/project-conventions.md`，由各阶段 writing/review Skill 在硬前置中装载。
> 通用方法真源：`.trellis/spec/guides/golden-path.md`（分层依赖律、轻框架锁定、错误处理范式、启动/关闭契约不可被本文件豁免）。
> 取值依据：2026-06-13 对 `github.com/bluehourse/safa-land` 全仓实测扫描（`go.mod`、`Makefile`、`AGENTS.md`、`.env.example`、`services/control-api/internal/*`、`db/migrations/`、`packages/contracts/`）。**取值反映现状，存量违例已在 SLOT-17 登记**；与硬规则冲突项不视为合法选择，按"触碰记债、新增阻塞"处理。

## 0. 元信息

| 字段 | 取值 |
|------|------|
| 模块名 / Go module path | safa-land / `github.com/bluehourse/safa-land` |
| 仓库路径 / Go 版本 | `safa-land`（monorepo，`go 1.17`） |
| 服务清单 | `services/control-api`（主，本文件取值的证据源）、`services/proxy-agent`、`services/proxy-rule-gate`、`services/control-worker`（占位） |
| 填写日期 / 填写人 | 2026-06-13 / guru-go-backend 配置包（实测扫描） |
| 取值依据 | 实测扫描；存量违例随扫描登记，未做团队 redline 确认 |

---

## 1. 槽位清单

> 每个槽位字段：**决策问题**（要钉死什么）· **本项目取值** · **代码证据**（≥1 条真实路径）· **生效范围**（新代码 only / 全量）· **备注**。
> 取值可以是"待定"，但待定项必须写明决策人与期限，且待定总数 ≤ 2，否则项目约定视为未就绪（硬前置不通过）。当前待定 0 项。
> **编号体系**：SLOT-NN 与 `project-conventions.template.md` / `conventions/index.md` 同一 canonical 体系（概念对齐，按编号取值）。本样例的 SLOT-12（数据库迁移）取值合并在 SLOT-02 块内叙述（见该块开头说明），其余概念各自独立成块。下方块按叙述顺序排列、不强制按编号升序，但每个 SLOT-NN 的概念与 canonical 一致。

### SLOT-01 DI 框架与装配位置
- 决策问题：依赖注入用 `wire` / `fx` 等容器，还是手工构造注入？装配 owner 落在哪个文件？
- 本项目取值：**无 DI 框架，手工构造注入**。所有 repository → service → handler 的依赖在 `app.New(cfg)` 内按层自下而上手工 `New*()` 构造并逐参数传入；`cmd/<svc>/main.go` 只做 `config.Load() → app.New() → app.Run()/app.Shutdown()`，不参与装配。新增依赖一律加到 `app.New()` 的构造链与 `NewHandler(...)` 形参表，不得在 service/handler 内部就地 `New` 出自己的依赖。
- 代码证据：`services/control-api/internal/app/app.go`（`New()` 第 37–102 行构造链）；`services/control-api/cmd/control-api/main.go`。
- 生效范围：全量。
- 备注：可升 `wire`，但属项目级架构决策，需 ADR + 升级本槽位后方可引入；实现阶段不得私自拍板（见 implementation-trace 合同 §4「未决决策」）。

### SLOT-02 ORM / 数据访问与迁移组织
> 本块覆盖 canonical 两个槽位：数据访问写法 = SLOT-02；迁移工具/目录/命名/版本 = SLOT-12（取值合并在此叙述，编号交叉引用 SLOT-12）。
- 决策问题：用 ORM（`ent`/`gorm`）、查询生成器（`sqlc`）还是原生 SQL？迁移文件命名、组织与事务包裹方式（迁移侧见 SLOT-12）？
- 本项目取值：**原生 SQL + `database/sql` + `github.com/lib/pq` + PostgreSQL**，无 ORM、无代码生成。SQL 直接写在 `repository` 层的 `QueryContext`/`QueryRowContext`/`ExecContext` 调用里，行映射经手写 `scanXxx()` helper。迁移（SLOT-12）落在 `db/migrations/`，命名 `NNNN_<slug>.up.sql` + `NNNN_<slug>.down.sql` **成对、四位顺序号递增**（当前到 `0013`）；每个迁移用 `BEGIN; ... COMMIT;` 包裹；`updated_at` 统一靠 `set_updated_at()` 触发器维护；枚举值用 PostgreSQL `CHECK (col IN (...))` 约束兜底。
- 代码证据：`services/control-api/internal/repository/user_repository.go`（原生 SQL + `scanUser`）；`db/migrations/0001_initial_schema.up.sql`（`set_updated_at()` + `CHECK` 约束）；`db/migrations/0013_user_month_plans.down.sql`（成对 down + 事务包裹）；`db/README.md`（迁移约定）。
- 生效范围：全量。
- 备注：可升 `sqlc`/`ent`，需 ADR；通用硬规则要求**迁移可 up/down、新增列给 DEFAULT 或 scan 兜底、版本号递增**，不可被本槽位豁免。

### SLOT-15 接口定义位置与命名（DIP 策略）
- 决策问题：依赖抽象用消费方本地 interface（DIP）还是被依赖方导出 interface？接口命名风格？
- 本项目取值：**消费方本地小接口**，命名为业务化的 `xxxStore` / 内嵌 interface（如 `userStore`、transport 内的 `initEnvService`），定义在消费它的文件顶部，按需声明最小方法集；不加 `I` 前缀，不集中放 `interfaces.go`。**注意：此约定仅 `UserService.userStore` 与 transport 的 `initEnvService` 落实，其余 service 直接持有具体 `*repository.XxxRepository`**（见 SLOT-17 第 4 条）。新代码一律走本地接口抽象。
- 代码证据：`services/control-api/internal/service/user_service.go`（`userStore` interface 第 14–26 行）；`services/control-api/internal/transport/http/router.go`（`initEnvService` interface 第 45–49 行）。
- 生效范围：新代码（存量具体类型依赖见 SLOT-17 第 4 条）。
- 备注：通用硬规则——分层依赖律为单向 `handler → service → repository → domain`，接口抽象是消除反向/越层导入的手段，不可用其它手段强行打通。

### SLOT-13 错误处理：sentinel 归属与包装/收口
- 决策问题：sentinel error 定义在哪一层（service / repository）？跨层用 `%w` 包装还是裸返回？handler 用 `errors.Is` 在哪一层映射 HTTP 状态码？
- 本项目取值：**service 级 sentinel + handler `errors.Is` 收口**为目标范式：service 暴露包级 sentinel（`service.ErrValidation`、`service.ErrInitEnv*` 一组），业务校验失败用 `fmt.Errorf("%w: ...", ErrValidation)` 链式包装；handler 用 `errors.Is(err, service.ErrXxx)` 分类映射 HTTP 状态码（`ErrValidation`→400，登录场景→401，唯一冲突→409，兜底→500），错误响应体用 `jsonResponse{"error": ...}`。**现状偏差：not-found 的 canonical sentinel 是 `repository.ErrNotFound`（非 service 级），且被 transport 直接 `errors.Is` 引用**（见 SLOT-17 第 1 条）。新代码必须在 service 层定义/转译 sentinel，handler 只 `errors.Is` service 包的 sentinel，不得新引 `repository.ErrNotFound`。
- 代码证据：`services/control-api/internal/service/errors.go`（`ErrValidation`）；`services/control-api/internal/service/initenv_service.go`（`ErrInitEnv*` 第 30–35 行）；`services/control-api/internal/service/user_service.go`（`fmt.Errorf("%w: ...", ErrValidation)` 第 59 行）；`services/control-api/internal/transport/http/router.go`（`errors.Is(err, service.ErrValidation)` 第 201/289/319 行）；`services/control-api/internal/repository/errors.go`（存量 `repository.ErrNotFound`）。
- 生效范围：新代码走 service 级 sentinel；存量 `repository.ErrNotFound` 路径触碰记债。
- 与 golden-path 的差距：**未对齐**。golden-path 规定 not-found 的 canonical sentinel 在 service 级（§2.3 「sentinel 归属」、概要 SSOT §1 硬规则「service 层定义 sentinel」），safa-land 现状是 not-found sentinel 落在 `repository.ErrNotFound`，且 transport 层绕过 service 直接 `errors.Is(err, repository.ErrNotFound)`（`router.go` 第 396/417/529/625/923/1512/1533 行，import 在第 21 行）。差距已登记于 SLOT-17 第 1 条，按"触碰记债、新增阻塞"处理，新代码不得新引 `repository.ErrNotFound` 到 handler。注意：错误**翻译**（repository 把 `sql.ErrNoRows` 转成 `ErrNotFound`）是 golden-path 硬规则、已对齐；本槽位决策的是**包装风格**（裸 sentinel vs `%w` 包装）——safa-land 选裸 sentinel（`return nil, ErrNotFound`，见 SLOT-17 第 5 条），属 golden-path §2.3 允许的项目级风格选择，非硬规则违例。
- 备注：通用硬规则——**禁止 `_ = err` 吞错、禁止 `fmt.Errorf("...: " + err.Error())` 丢 `%w`、错误响应不得回 `err.Error()` 泄露内部细节**，本槽位不豁免这些。

### SLOT-03 日志方案
- 决策问题：用标准 `log`、`log/slog`、`zap` 还是项目日志门面？结构化字段与 trace id 约定？
- 本项目取值：**标准库 `log`**，仅在 `main()` 入口用 `log.Fatalf` / `log.Printf` 记录启动、信号、关闭；service/repository/transport 层当前不打日志。无结构化字段、无 trace id 透传。
- 代码证据：`services/control-api/cmd/control-api/main.go`（`log.Fatalf`/`log.Printf` 第 17/37 行）；`services/proxy-agent/internal/reporter/stdout.go`（`import "log"`）。
- 生效范围：全量。
- 与 golden-path 的差距：**已对齐**（栈选型层面）。golden-path 把日志列为 `[SLOT-03]` 槽位，default 即标准 `log`、未切换前用标准库（§2.5「是否切到 `slog`/`zap` 由对应 `[SLOT-xx]` 决定；未切换前用标准库」），safa-land 现状正是此 default，未越槽位、无硬规则违例。**残留缺口**仅在可观测性维度：handler 兜底 500 分支无 trace id（见下条备注），属 SLOT-17 第 7 条登记的观测性缺口，不是 golden-path 分层/错误硬规则的偏差。
- 备注：可升 `log/slog`（结构化 + 注入 `*slog.Logger`）；升级前 handler 兜底 500 分支当前**无法记录** trace id（entry-api 合同要求兜底 500 记 correlation/trace id），此缺口在 SLOT-17 第 7 条登记。

### SLOT-08 配置加载与 env 前缀
- 决策问题：配置集中在哪个函数加载？env 前缀如何按服务区分？必填项与默认值策略？
- 本项目取值：**集中 `config.Load() (Config, error)`**，每服务一个 `internal/config` 包；env 前缀按服务区分——control-api 用 `CONTROL_API_*`、proxy-agent 用 `PROXY_AGENT_*`/`GOST_*`；读取经 `getEnv`/`mustDuration`/`mustInt`/`mustBool` helper（有默认值的用 `getEnv(key, fallback)`，格式非法即 `panic`）；强制必填项（如 `DATABASE_URL`）缺失时 `Load()` 返回 error 由 `main()` `log.Fatalf`。handler/service **不读环境变量**，配置经构造注入。
- 代码证据：`services/control-api/internal/config/config.go`（`Load()` + helper 第 40–126 行）；`.env.example`（`CONTROL_API_*` / `PROXY_AGENT_*` / `GOST_*` 前缀清单）。
- 生效范围：全量。
- 与 golden-path 的差距：**已对齐且更严**（deliberate project convention，非误读）。golden-path 的硬规则只显式禁 **service/repository** 读 env（§2.2「service/repository 里 `os.Getenv` 现取配置」、§11、§12 门禁「禁 service 内 `os.Getenv`」均只点名 service/repository；§6 transport 禁止清单不含读 env），handler 读 env 在 golden-path 正文未被明确点名。safa-land 选择**更严口径**——handler 也不读 env，全仓 `os.Getenv` 仅出现在 `internal/config/config.go`（第 43/62/68/79/87/101/115 行），service/repository/transport 三层均无 env 读取，配置一律经 `config.Load()` 构造注入。这是项目主动收紧、与 golden-path 同向且更强的 deliberate convention，不是对 golden-path 的误解，故不登记为 SLOT-17 违例。
- 备注：通用硬规则——handler 不调用 `config.Load()`、不读 env，所需配置构造注入，本槽位不豁免。

### SLOT-10 会话 / 鉴权实现
- 决策问题：管理端会话用什么机制？密码哈希用什么？token 形态与校验方式？
- 本项目取值：**自实现 HMAC-SHA256 签名 cookie + bcrypt**。会话由 `auth.SessionManager` 管理：payload `adminUserID|expiresUnix`，`hmac.New(sha256.New, secret)` 签名，`base64.RawURLEncoding` 编码为 cookie 值；校验用 `hmac.Equal` 常量时间比对 + 过期检查；cookie `HttpOnly` + `SameSite=Lax` + `Secure` 由 `CONTROL_API_SESSION_SECURE` 控制。管理员密码用 `golang.org/x/crypto/bcrypt` 的 `CompareHashAndPassword`。会话密钥/cookie 名/TTL 经 `CONTROL_API_SESSION_*` env 注入。
- 代码证据：`services/control-api/internal/auth/session_manager.go`（HMAC 签名/校验全流程）；`services/control-api/internal/service/admin_auth_service.go`（`bcrypt.CompareHashAndPassword` 第 45 行）；`.env.example`（`CONTROL_API_SESSION_SECRET/COOKIE/TTL/SECURE`）。
- 生效范围：全量。
- 备注：自实现签名 cookie 为现状选择；引入第三方会话/JWT 库属架构决策，需 ADR + 升级本槽位。

### SLOT-05 API 风格与路由注册
- 决策问题：对外用 REST JSON、gRPC 还是混合？路由如何注册？版本号怎么传？
- 本项目取值：**REST JSON over `net/http` `ServeMux`**。路由集中在 `Handler.Routes()` 内 `mux.HandleFunc("/api/v1/...", ...)` 注册，前缀 `/api/v1/`，鉴权端点经 `h.requireAdmin(...)` 包裹；集合 vs 单资源用 trailing slash 区分（`/api/v1/users` vs `/api/v1/users/`）；响应统一 `jsonResponse{"data": ...}` / `{"error": ...}`；handler 形态为 `func(h *Handler) handleXxx(w http.ResponseWriter, r *http.Request)`，内部 `switch r.Method` 分发。版本号写死在路径段（`v1`），无动态版本协商。
- 代码证据：`services/control-api/internal/transport/http/router.go`（`Routes()` ServeMux 注册第 93–126 行；`handleDomainBlacklistRules` 的 `switch r.Method` 第 128 行起）；`packages/contracts/proxy_node_config.go`（跨服务 JSON 契约）。
- 生效范围：全量。
- 备注：通用硬规则——**禁用 gin/echo/fiber 等重型框架**（已实测无引入），handler 接收并透传 `r.Context()` 到 service，本槽位不豁免。可升 gRPC，需 ADR。

### SLOT-11 包组织 / 分层目录与跨服务契约位置
- 决策问题：服务内部包如何分层划分？跨服务请求/响应/事件 schema 放哪个包？谁是 owner？
- 本项目取值：**`packages/contracts/`**（package `contracts`）。control-api 渲染、proxy-agent 消费的 `DesiredNodeConfig` 及其嵌套结构（`DesiredEntryListener`/`DesiredRoutePolicy`/`DesiredUpstream*` 等）集中在此，用纯 struct + JSON tag 定义；`internal/` 内不私自定义跨服务 schema。`packages/sdk/`、`packages/shared/` 为占位（仅 README）。
- 代码证据：`packages/contracts/proxy_node_config.go`；`packages/contracts/README.md`。
- 生效范围：全量。
- 备注：通用硬规则——`internal/` 为服务私有边界，跨服务类型必经 `packages/contracts/`；契约变更须排在所有消费方之前（见 implementation-trace 合同 §1 执行顺序）。

### SLOT-16 可穷举字段（枚举）表达
- 决策问题：status/role/protocol/mode 等可穷举概念用 Go `iota`/具名常量枚举，还是裸 `string`？非法值如何收口？
- 本项目取值：**目标为 Go 具名枚举（`iota` 常量或字符串常量）+ 显式 JSON 序列化口径 + 非法值错误收口**；**现状偏差：契约与 domain 里 `NodeStatus`/`NodeRole`/`ProxyProtocol`/`Mode`/`RoutingMode` 等可穷举字段均为裸 `string`**，合法集合仅靠 DB `CHECK` 约束与 service 层校验兜底，Go 类型层面未建枚举（见 SLOT-17 第 6 条）。新增可穷举字段必须建 Go 枚举类型，不得新增裸 `string` 魔法值字段。
- 代码证据：`packages/contracts/proxy_node_config.go`（`NodeStatus string` 第 11 行、`ProxyProtocol string` 第 32 行等裸 string）；`db/migrations/0001_initial_schema.up.sql`（`role TEXT ... CHECK (role IN (...))` 作为现状兜底）。
- 生效范围：新代码建枚举；存量裸 string 字段触碰记债。
- 备注：通用硬规则——可穷举概念禁裸魔法值，owner 按语义归属（业务枚举回指 service，运行/网关枚举回指 runtime/config）。

### SLOT-04 测试框架与组织
- 决策问题：用标准 `testing` 还是 `testify`/`ginkgo`？mock 用生成器还是手写 fake？测试目录是否镜像、是否 white-box？handler 怎么测？
- 本项目取值：**标准库 `testing`，无 testify/ginkgo/gomock**。mock 一律**手写 fake**（实现被测接口的 struct，字段塞返回值/错误）；测试**与被测代码同包**（white-box，`*_test.go` 与源码同目录，非镜像 `test/` 树）；handler 测试用 `net/http/httptest`（`NewRequest` + `ResponseRecorder`）驱动 + 手写 fake service；表驱动 + `t.Run` 子测试命名。仓库根 `test/` 仅放部署/运维 shell 脚本测试，不是 Go 单测目录。
- 代码证据：`services/control-api/internal/service/user_month_plan_service_test.go`（手写 fake + 同包）；`services/control-api/internal/transport/http/router_initenv_test.go`（`httptest` + `fakeInitEnvHandlerService`）；`services/control-api/internal/config/config_test.go`。
- 生效范围：全量。
- 备注：可升 testify；implementation-trace 要求测试名级别证据（`--- PASS: TestX/sub`），与本槽位 `t.Run` 子测试命名一致。

### SLOT-07 lint / 格式化 / 静态检查
- 决策问题：lint 工具链是什么？配置文件在哪？CI 强制哪些检查？
- 本项目取值：标准工具链 `gofmt` + `go vet`；**约定 lint 工具为 `golangci-lint`，但仓库内当前无 `.golangci.yml`/`.golangci.yaml` 配置文件**（见 SLOT-17 第 7 条）。`Makefile` 仅含 `help`/`init`/`tree` 三个导航 target，未封装 `build`/`test`/`lint`。CI 配置在 `.github/`（未纳入本次取值证据深读）。
- 代码证据：`Makefile`（无 lint/test target）；仓库根**无** `.golangci.*`（实测 glob 无匹配）；`go.mod`（`go 1.17`）。
- 生效范围：全量。
- 备注：implementation-trace G3 要求 `go vet` + `golangci-lint run` 通过或豁免记债；在落地 `.golangci.yml` 前，`golangci-lint` 证据项按"工具未配置"处理并指向本槽位与 SLOT-17 第 7 条。

### SLOT-14 启动 / 关闭契约
- 决策问题：`main()` 如何控信号？`app` 的生命周期方法签名？关闭如何传 timeout、释放哪些资源？
- 本项目取值：**`main()` 控信号 → `app.New(cfg)` → `app.Run()` → `app.Shutdown(ctx)`**。`App` 持有 `*http.Server` 与 `*sql.DB`；`Run()` = `server.ListenAndServe()`；`main()` 用 `signal.Notify(SIGINT, SIGTERM)` + `select` 同时监听信号与 `serverErrCh`，收到信号后 `context.WithTimeout(ctx, cfg.ShutdownTimeout)` 调 `Shutdown(ctx)`；`Shutdown()` 先 `server.Shutdown(ctx)` 再 `db.Close()`，聚合返回首个非空错误；`http.ErrServerClosed` 视为正常退出。`http.Server` 的 Read/Write/Idle timeout 由 config 注入。
- 代码证据：`services/control-api/internal/app/app.go`（`New/Run/Shutdown` 第 22–129 行）；`services/control-api/cmd/control-api/main.go`（信号 + `select` + timeout shutdown 第 27–51 行）。
- 生效范围：全量。
- 备注：通用硬规则——handler 必须接收并透传 `r.Context()` 承载请求级 timeout/cancel，禁止 `context.Background()` 顶替请求上下文；启动/关闭编排归 doc_type=`runtime-deployment`。

### SLOT-09 文档生成（API doc）
- 决策问题：是否用 Swagger/OpenAPI 自动生成 API 文档？源在哪、生成命令是什么？
- 本项目取值：**无 API 文档自动生成**（无 Swagger/OpenAPI/swaggo 注解、无生成脚本，实测 grep 无匹配）。API 现状靠 `db/README.md`、`packages/contracts/README.md` 与 `docs/` 下手写文档描述；路由清单的唯一真源是 `Routes()` 注册表。
- 代码证据：仓库内**无** swagger/openapi 注解或 spec 文件（实测 grep 无匹配）；`docs/`（手写文档目录）；`packages/contracts/README.md`。
- 生效范围：全量。
- 备注：引入 OpenAPI 生成属架构决策，需 ADR；在引入前，跨服务契约的 SSOT 是 `packages/contracts/` 的 Go struct，而非任何生成文档。

### SLOT-17 存量违例清单（tech-debt 登记）
- 决策问题：已知的存量架构违例有哪些（供 review 的存量豁免判定使用：触碰存量记债不阻塞、新增违例阻塞）？
- 本项目取值：
  1. **transport 导入 repository 且直接 `errors.Is(err, repository.ErrNotFound)`** —— 违反分层依赖律（handler 不得导入 repository）与 SLOT-13（not-found sentinel 应在 service 级）。证据：`services/control-api/internal/transport/http/router.go` 第 21 行 `import ".../internal/repository"`，第 396/417/529/625/923/1512/1533 行 `errors.Is(err, repository.ErrNotFound)`。
  2. **transport 持有 `*sql.DB` 并直接 `h.db.PingContext`** —— handler 触碰 DB（healthz 探活），违反"handler 不碰 `database/sql`"。证据：`services/control-api/internal/transport/http/router.go`（`Handler.db *sql.DB` 第 26 行；`h.db.PingContext(ctx)` 第 222 行）。
  3. **transport 直接断言 `pq.Error`** —— DB 驱动细节泄漏到 transport（应在 repository 转译为 sentinel）。证据：`services/control-api/internal/transport/http/router.go`（`var pqErr *pq.Error` 第 1446/1455/1464 行）。
  4. **service 持有具体 `*repository.XxxRepository` 而非接口** —— 与 SLOT-15 的本地接口抽象约定不一致（仅 `UserService.userStore`、transport 的 `initEnvService` 用了接口）。证据：`services/control-api/internal/service/admin_auth_service.go`（`repo *repository.AdminUserRepository` 第 15 行）、`application_account_service.go`（第 14–15 行）、`port_binding_service.go`、`route_sync_service.go`、`config_sync_service.go` 等。
  5. **repository 裸返回 `ErrNotFound`，未用 `%w` 包装** —— 与 SLOT-13 的链式包装范式不一致（虽 `errors.Is` 仍可判定，但丢失底层链）。证据：`services/control-api/internal/repository/user_repository.go`（`return nil, ErrNotFound` 第 110/194/286/351 行）。
  6. **可穷举字段为裸 `string`，无 Go 枚举** —— 违反 SLOT-16/可穷举字段硬规则的 Go 类型层表达（仅靠 DB `CHECK` 兜底）。证据：`packages/contracts/proxy_node_config.go`（`NodeStatus`/`NodeRole`/`ProxyProtocol`/`Mode`/`RoutingMode` 等裸 string）；`db/migrations/0001_initial_schema.up.sql`（`CHECK (... IN ...)`）。
  7. **`golangci-lint` 为约定 lint 工具但无 `.golangci.*` 配置文件，且兜底 500 无 trace id 日志** —— 工具链与可观测性缺口。证据：仓库根无 `.golangci.*`（实测无匹配）；`services/control-api/internal/transport/http/router.go` 兜底错误分支仅 `writeJSON(... 500 ...)` 无 `log`/trace（与 SLOT-03 标准 `log`-only 现状叠加）。
- 生效范围：全量。**清单外的同类问题一律按"新增违例"阻塞。**
- 备注：本槽位是**存量豁免机制**的数据源。触碰上述条目须挂编号记债（绕行写"为何不修"，顺手修复写处置），新增同类违例直接阻塞（见 implementation-trace 合同 §4「存量违例触碰」）。

---

## 2. 校验自检（writing/review 硬前置使用）

装载本约定文件的 Skill 必须先执行以下校验，任一不通过即终止并提示修复：

- [x] C1 元信息齐全（module path / Go 版本 / 服务清单 / 填写日期）。
- [x] C2 SLOT-01 ~ SLOT-17 全部填写，待定 0 项（≤ 2 且均写明决策人与期限——本文件无待定项）。
- [x] C3 每个槽位至少 1 条真实代码证据路径（路径均存在于仓库）。
- [x] C4 取值与通用硬规则的冲突已显式标注并降级为存量违例（分层依赖律、轻框架锁定、错误链式包装/不吞错、handler 接收 context、`internal/` 隐私边界、可穷举字段禁魔法值——这些不被槽位豁免，冲突现状一律进 SLOT-17）。
- [x] C5 SLOT-17 存量违例清单已登记（7 条，非空）。

---

## 3. 槽位与门禁的对应关系（参考）

| 槽位 | 谁消费 |
|------|--------|
| SLOT-01 / SLOT-14 | runtime-deployment 详细合同、implementation-trace（装配与启动改动）、implementation-review |
| SLOT-02 / SLOT-12 / SLOT-11 | repository 详细合同、迁移检查 hooks、跨服务契约变更 review |
| SLOT-03 / SLOT-13 | service / entry-api 详细合同（合同八问之依赖与失败收口）、implementation-review |
| SLOT-07 | `verification-evidence.jsonl`（`go vet`/`golangci-lint`/日志）、implementation-review |
| SLOT-08 / SLOT-10 | config-runtime-contract、entry-api 鉴权链路、implementation-review |
| SLOT-05 / SLOT-16 | entry-api 详细合同（路由/枚举 owner）、API 风格 review |
| SLOT-04 / SLOT-15 | 各阶段测试映射校验、implementation-trace G4（测试名级别证据）、接口抽象/DIP review |
| SLOT-06 / SLOT-09 | repository 驱动落点、API 文档生成 review |
| SLOT-17 | 所有 review 的存量豁免判定（触碰记债、新增阻塞） |
