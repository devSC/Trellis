# Go 实现阶段标准包（L1 · go-guru / golden-path 锁定）

> 本文件是 `guru-go-backend` Harness 的实现阶段 **L1 标准 SSOT**，由代码编写与实现审核**同源引用**。
> 目标平台：Go monorepo · `net/http ServeMux` · 分层 `handler → service → repository → domain` · 原生 SQL · 手写 DI。
> grounded 在 `safa-land/services/control-api` 真实写法；适配 `backend-implementation-go-guru-standard`。
> 实现阶段只**承接**已审核通过的详细设计，不重新设计业务行为、owner、依赖边界、错误语义、事务语义、配置项或运行合同。
>
> 装载（安装后路径）：
> - 通用方法真源：`.trellis/spec/guides/golden-path.md`（模块形态、分层依赖律、错误处理范式、启动/关闭契约、入口决策树、禁止清单）。
> - 流程骨架与本标准包：`.trellis/spec/harness/implementation/implementation-go-guru-standard.md`（本文件）。
> - 项目槽位取值：`.trellis/spec/conventions/project-conventions.md`（DI 框架 / ORM / 日志 / 测试框架 / API 风格 / DB 驱动 / lint / 文档生成 / 会话鉴权）。
> - trace 合同：`.trellis/spec/harness/implementation/implementation-trace-contract.md`。

---

## 0. 本标准包定位与边界

适用：
- Go 后端实现阶段的可编码合同定义、代码编写执行依据、实现审核依据。
- 从已审核详细设计单元（`UNIT-<slug>`）到 Go 代码的承接、`implement.md` trace 主文档、实现 Gate 判定、存量豁免口径。

不适用：
- 详细设计正文生成、需求 / 概要 / 详细设计审核（各有对应阶段 SSOT）。
- golden-path 与 project-conventions 槽位本体的重定义——本文件只引用，不复制其规则正文。

中立性约束：
- 本标准包**不执行**代码修改，也**不输出**审核 Findings。它定义"代码编写"与"实现审核"共同遵守的合同与判定口径。
- golden-path 的硬规则（`net/http`、分层依赖律、错误处理范式、启动 / 关闭契约）在本文件中是**锁定前提（不可豁免）**；project-conventions 的槽位（DI / ORM / 日志 / 测试 / API 风格等）是**可按服务调整的取值**，实现时读 `project-conventions.md` 当前值，不在本文件硬编码。

### 0.1 Active packet 与验证路由

- Full/high active worker 必须消费 current packet 与 `implement.md` 已确认的 minimum commit-stable planning audit；它们是不可变 dispatch input。
- Full/high ordinary 只写 packet `target_paths`，只运行 packet `deterministic_checks` 与 planning audit focused checks；不得按 UNIT、layer、`doc_type`、component、symbol 或 hunk 重新切片或转移 ownership。
- Workspace-wide Go build/vet/lint/full regression 只由唯一 Integration 执行；Integration 实际写范围限 exact `integration_owned_paths`。
- Small、Micro、Lite、non-Full 与 v1 保留本标准原有验证合同。下文的 workspace 命令均按此路由解释，不得覆盖 Full/high ordinary 的 packet 边界。

---

## 1. golden-path 锁定前提（不可豁免）

下列规则来自 `.trellis/spec/guides/golden-path.md`，是 Go 后端的 golden-path 锁定项。实现阶段**任何切片**都不得违反，也不得在 `implement.md` 用"存量豁免"绕过；触碰即 Gate `fail`。

### LOCK-1 框架轻量

- HTTP 入口只用标准库 `net/http` + `http.ServeMux`；**禁用** gin / echo / fiber / chi 等重型或第三方路由框架。
- 路由注册集中在 `transport/http` 的 `Handler.Routes()` 一处，返回 `http.Handler`。
- 好例子（safa-land `transport/http/router.go`）：

  ```go
  func (h *Handler) Routes() http.Handler {
      mux := http.NewServeMux()
      mux.HandleFunc("/healthz", h.handleHealthz)
      mux.HandleFunc("/api/v1/users", h.requireAdmin(h.handleUsers))
      mux.HandleFunc("/api/v1/users/", h.requireAdmin(h.handleUserByID))
      return mux
  }
  ```

- 坏例子：`r := gin.Default(); r.GET("/users", ...)`——引入重型框架，触碰 LOCK-1，Gate `fail`。

### LOCK-2 分层依赖律（严格单向、无循环）

- 方向固定：`transport(handler) → service → repository → domain`。
- `domain` 是最底层纯类型，可被任意层导入；除 `domain` 外，**不得跨 `internal/` 包反向或横向导入**（service 不导入 transport；repository 不导入 service）。
- handler 只做协议适配、输入解析、上下文提取、调用 service、错误转 HTTP 状态码、响应收口；**不直接访问 DB / SQL / 外部连接**。
- service 持有业务规则、校验、事务编排、跨 repository 协调；**不读 HTTP header / query / cookie**，只接收已解析的参数。
- repository 只做 SQL 读写与行扫描，返回 `domain` 类型或 sentinel error；**不含业务判定**。
- 好例子（safa-land `app/app.go` 装配链）：`handler := httptransport.NewHandler(db, service.NewUserService(userRepo, ...), ...)`——上层构造函数只接收下层真实实例。
- 坏例子：`repository` 包 `import ".../internal/service"`——反向依赖，触碰 LOCK-2，Gate `fail`。

### LOCK-3 错误处理范式

- 每层定义服务级 sentinel error，并用 `fmt.Errorf("%w: ...", SentinelErr)` 链式包装；上层用 `errors.Is()` 判定语义后转 HTTP 状态码。
- repository 把 `sql.ErrNoRows` 收敛为本层 sentinel（`repository.ErrNotFound`）；service 用 `service.ErrValidation` 表达校验失败。
- 好例子（safa-land）：
  - `repository/errors.go`：`var ErrNotFound = errors.New("repository: not found")`
  - `service/errors.go`：`var ErrValidation = errors.New("service: validation failed")`
  - service 包装：`return nil, fmt.Errorf("%w: display_name is required", ErrValidation)`
  - repository 收敛：`if errors.Is(err, sql.ErrNoRows) { return nil, ErrNotFound }`
  - handler 判定：

    ```go
    switch {
    case errors.Is(err, service.ErrValidation):
        writeJSON(w, http.StatusBadRequest, jsonResponse{"error": err.Error()})
    case errors.Is(err, repository.ErrNotFound):
        writeJSON(w, http.StatusNotFound, jsonResponse{"error": "user not found"})
    default:
        writeInternalError(w, err)
    }
    ```

- 坏例子：service 直接 `return errors.New("bad")` 裸字符串，handler 用 `err.Error() == "bad"` 字符串比较——触碰 LOCK-3，Gate `fail`。

### LOCK-4 启动 / 关闭契约

- `cmd/<svc>/main.go` 是单一入口，只控信号 → `app.New(cfg)` → `app.Run()` → `app.Shutdown(ctx)`。
- `app.New()` 完成全部依赖装配（DB 连接、repository、service、handler、`http.Server`）；`Run()` 启动监听；`Shutdown(ctx)` 在 timeout context 内优雅关闭 server 并释放 DB。
- 所有 handler / service / repository 方法第一参数为 `ctx context.Context`，支持 timeout / cancel 传播。
- 好例子（safa-land `app/app.go`）：`func (a *App) Shutdown(ctx context.Context) error { serverErr := a.server.Shutdown(ctx); dbErr := a.db.Close(); ... }`。
- 坏例子：`main.go` 里散落 `go server.ListenAndServe()` 且无信号处理、无 `Shutdown`——触碰 LOCK-4，Gate `fail`。

### LOCK-5 配置集中

- 环境变量 + 默认值，集中在 `config.Load()`；env 前缀按服务区分（如 `CONTROL_API_*`）。
- 业务层（service / repository / transport）**不直接读 `os.Getenv`**；只消费 `config.Config` 字段。
- 好例子（safa-land `config/config.go`）：`HTTPAddr: getEnv("CONTROL_API_ADDR", ":8080")`、`DBMaxOpenConns: mustInt("CONTROL_API_DB_MAX_OPEN_CONNS", 10)`、缺必填项时 `Load()` 返回 error（`if cfg.DatabaseURL == "" { return Config{}, fmt.Errorf("DATABASE_URL is required") }`）。
- 坏例子：在 `service/user_service.go` 里 `timeout, _ := time.ParseDuration(os.Getenv("X"))`——绕过 config.Load，触碰 LOCK-5，Gate `fail`。

### LOCK-6 包私有约定

- `internal/` 隐私约定：服务私有实现落 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`。
- 跨服务契约落 `packages/contracts/`（DTO / 同步配置等纯类型，无业务逻辑）。
- 好例子（safa-land `packages/contracts/proxy_node_config.go`）：`type DesiredNodeConfig struct { ... }`——跨服务共享的纯数据契约。
- 坏例子：把跨服务 DTO 塞进某服务 `internal/`，另一服务跨 `internal/` 导入——触碰 LOCK-6，Gate `fail`。

> 不适用场景：单文件脚本工具、一次性迁移程序、`cmd/` 下纯 CLI 助手（无 HTTP 入口、无分层需求）不强制 LOCK-1/LOCK-2 的 handler/service/repository 分层，但仍需 LOCK-3（错误包装）与 LOCK-5（配置集中），并在 `implement.md` 计划节显式声明"非分层服务"理由。

---

## 2. 可编码合同（承接判定）

实现阶段的输入是**已审核通过的详细设计单元**（`UNIT-<slug>`）。一个详细设计单元"可编码"当且仅当下列八项合同齐全且无歧义；任一缺失则该切片置 `blocked`，回退详细阶段修订（见 §7），不得在代码里临时补设计。

合同八项（对齐详细 Gate 的合同八问，逐项必须能落到 Go 代码锚点）：

| # | 合同项 | 可编码判据（落到 Go 锚点） |
|---|--------|---------------------------|
| 1 | 承接行为 | 该单元承接哪些 `BHV-NNN`；prd 无此编号即幽灵引用，`blocked` |
| 2 | 接口签名 | service / repository 方法签名（含 `ctx context.Context`、参数结构体、返回 `(*domain.X, error)`）可直接落地 |
| 3 | 字段与结构 | `domain` 类型字段、JSON tag、可空字段（指针 / `sql.Null*`）、`CreateXParams`/`UpdateXParams` 可直接定义 |
| 4 | 执行流程 | 每步骤可落到方法调用、字段赋值、分支、事务块或错误返回（不允许"执行业务逻辑"式大方法占位） |
| 5 | 失败收口 | 每类失败映射到 sentinel error（`ErrValidation` / `ErrNotFound` / 唯一约束冲突等）与 HTTP 状态码 |
| 6 | 依赖边界 | `direct_dependencies[]` 每项映射到构造函数参数 + 私有字段 + `app.New()` 装配点；无下层缺口 |
| 7 | 测试映射 | 既有验证命令落点（`go test ./...`）；或 §6 allowlist 允许的纯函数最小单测目标 |
| 8 | 不得补造声明 | 该单元未授权的字段 / 错误码 / 配置 / 事务 / 依赖，实现期不补造 |

可验证信号：
- `implement.md` 的合同追踪表中，每个 `UNIT-<slug>` 都能回指上述八项的代码锚点或 `blocked` 依据。
- 每个执行流程步骤都有预期代码落点；每个 `direct_dependencies[]` 行都能映射到构造函数参数 → 字段 → `app.New()` 装配。

约束边界：
- 不从代码、习惯或参考工程反推需求；不猜测、发明、补全详细设计未定义的契约 / 字段 / 错误码 / 配置 / 事务 / 依赖。
- 不把详细设计的行为步骤合并、改序、上移、下沉或省略，除非详细设计本身给出依据。
- 不为编译通过新增 fake、optional path、占位结果、内存 store 或硬编码依赖。

---

## 3. 实现顺序（依赖方向从下至上）

代码阶段唯一执行顺序。先实现被依赖层，再实现调用层；上层不得用 fake / 占位 / 内存 store / hardcoded 依赖绕过下层缺口。

```text
Phase 0  设计合同解析 + implement.md 计划      （不写生产代码）
Phase 1  domain：类型、Params、JSON tag、可空字段
Phase 2  repository：SQL 读写、行扫描、sentinel error 收敛、migration
Phase 3  service：业务规则、校验、事务编排、跨 repo 协调、sentinel error 包装
Phase 4  transport：handler、路由注册、输入解析、错误转 HTTP、响应收口
Phase 5  app/config/main：config.Load、app.New 装配、信号与启动/关闭
Phase 6  验证与符合性审查：go build / go vet / go test + lint + 证据回填
```

阶段共同规则：
- Phase 0 在 detail 确认前创建或更新 `implement.md` 计划合同；detail 确认后 `implement.md` 不再作为执行状态写入点。
- Phase 1~6 的切片状态、改动文件、偏差、阶段自检和恢复条件追加到 `implementation-evidence.jsonl`；验证命令和测试名级证据追加到 `verification-evidence.jsonl`。
- Phase 0 未通过不得写生产代码；Phase 1~5 只能按依赖方向推进；发现下层合同缺失，当前生产路径必须 `blocked`。

各 Phase 的产物合同与出入口条件见 §4。

---

## 4. 各 Phase 产物合同与出入口

### Phase 0 — 设计合同解析（不写生产代码）

输入：概要承接索引（`chapter_target → doc_type`）、目标详细设计单元、`golden-path.md`、`project-conventions.md`、现有代码骨架。

代码前硬门禁：
- 必须先创建或更新 `implement.md` 的计划节；小迭代可缩小范围，但不得跳过计划，也不得"先写代码再补 trace"。若 detail 已确认而计划缺失或需改变，必须回退 detail Gate，不在实现阶段静默补写。
- 完成 `UNIT-<slug> → 代码资产` 映射；识别 LOCK 锁定面与 Secret/Credential 检查面；为每个切片写明 `checkpoint` 与 `validation_commands`。

出口条件：
- 每个目标单元都有合同追踪行与资产映射行；每个执行流程步骤都有预期代码落点；无未解释的设计缺口（有则 `blocked`）。

失败判定：`chapter_target → doc_type` 映射缺失；执行流程步骤无法落到代码目标；`direct_dependencies[]` 无法形成构造闭环；缺 `implement.md` 计划节。

### Phase 1 — domain（最底层纯类型）

产物合同：
- 实体类型、`CreateXParams` / `UpdateXParams` / `UpdateXStatusParams`，JSON tag 与详细设计字段一致。
- 可空字段用指针（`*string` / `*int64` / `*int`）或 `sql.Null*`（仅在 repository 扫描层）；切勿在 domain 暴露 `sql.Null*`。
- 好例子（safa-land `domain/user.go`）：

  ```go
  type User struct {
      ID                   int64    `json:"id"`
      ExternalRef          *string  `json:"external_ref,omitempty"`
      DisplayName          string   `json:"display_name"`
      SourceIPAllowlist    []string `json:"source_ip_allowlist"`
      MaxConcurrentConnections *int  `json:"max_concurrent_connections,omitempty"`
  }
  ```

- 坏例子：`Status sql.NullString json:"status"`——把数据库扫描类型泄漏进 domain，破坏分层纯度。

出口条件：所有承接单元的字段、可空语义、JSON 契约落地；`go build ./internal/domain/...` 通过。

### Phase 2 — repository（SQL 读写 + 行扫描）

产物合同：
- 每个 repository 是 `struct{ db *sql.DB }` + `NewXRepository(db *sql.DB) *XRepository`（DB 驱动取值见 `project-conventions.md`，当前 `lib/pq` + PostgreSQL）。
- 方法签名：`(ctx context.Context, ...) (*domain.X, error)` / `([]domain.X, error)` / `error`。
- 读取用 `QueryContext` / `QueryRowContext`，写入用 `ExecContext`，参数化查询（`$1` 占位符），切片用 `pq.Array`。
- 行扫描走私有 `scanX` helper；`sql.ErrNoRows` 收敛为 `ErrNotFound`；写操作用 `ensureRowsAffected(result)` 校验影响行数。
- 复杂读（跨实体聚合 / JSON 组装）允许私有 helper（如 safa-land `attachMonthPlans`、`LEFT JOIN LATERAL`），但仍只产 `domain` 类型，不含业务判定。
- 好例子（safa-land `repository/user_repository.go`）：

  ```go
  func (r *UserRepository) GetByID(ctx context.Context, id int64) (*domain.User, error) {
      row := r.db.QueryRowContext(ctx, `SELECT ... FROM users WHERE users.id = $1`, id)
      user, err := scanUser(row)
      if err != nil {
          if errors.Is(err, sql.ErrNoRows) { return nil, ErrNotFound }
          return nil, err
      }
      return &user, nil
  }
  ```

- 坏例子：repository 方法里 `if user.Status != "active" { return ErrForbidden }`——业务判定下沉到 repo，触碰 LOCK-2。

出口条件：每个承接单元的读写路径落地；`ErrNotFound` 收敛正确；migration 落 `db/migrations/`；`go build ./internal/repository/...` 通过。

失败判定：repository 含业务状态机；repository 读 HTTP/env；用内存 map 代替 SQL；裸 `sql.ErrNoRows` 透出未收敛。

### Phase 3 — service（业务规则 + 校验 + 编排）

产物合同：
- service 是 `struct` 持有 repository / 其他 service 私有字段 + `NewXService(...)` 构造函数；依赖通过构造函数注入（手写 DI，见 `project-conventions.md`，当前无 wire）。
- 依赖可用接口收窄（safa-land `userStore interface`）以表达"只用到的 repository 方法"，便于演进；接口定义在消费方 service 包内。
- 业务校验用 `fmt.Errorf("%w: <原因>", ErrValidation)`；状态枚举校验、唯一性前置、跨实体一致性（如月计划不重叠）落在 service 方法或私有 `validateX` helper。
- 执行流程每步骤可定位：校验 → repo 调用 → 联动同步（如 `routeSync.SyncUser` / `configSync.TouchNodesForUser`）→ 返回。
- 好例子（safa-land `service/user_service.go` `Create`）：先 `requireActiveApplicationAccount` → `validateUserFields` → `repo.Create` → `routeSync.SyncUser`，每步独立可读。
- 坏例子：一个 `func Create(...)` 内 200 行 `// 处理业务逻辑` 不拆步骤——触碰合同八项之 4，Gate `fail`。

出口条件：`BZ05` 类执行流程每步骤定位到代码；事务 / 幂等 / 错误语义与设计一致；`go build ./internal/service/...` 与既有 service 单测通过。

失败判定：service 读 HTTP/cookie/flag；用 fake repo 绕过下层缺口；校验语义弱化；大方法吞步骤。

### Phase 4 — transport（handler + 路由 + 协议适配）

产物合同：
- `Handler` 持有各 service 私有字段 + `NewHandler(...)` 构造函数；`Routes()` 集中注册路由（LOCK-1）。
- 集合路由（`/api/v1/users`）与 by-ID 路由（`/api/v1/users/`）分开注册；by-ID 用 `parseIDParam` 解析路径尾段；按 `r.Method` `switch` 分发，未命中 `methodNotAllowed`。
- 输入解析用 `decodeJSON(r, &req)`；错误转状态码集中走 `errors.Is` 判定（LOCK-3）；响应统一 `writeJSON(w, status, jsonResponse{"data": x})` 或 `{"error": msg}`。
- 鉴权 / 会话中间件包装 handler（safa-land `h.requireAdmin(h.handleUsers)`）；会话实现取值见 `project-conventions.md`（当前 HMAC-SHA256 签名 cookie + bcrypt，自实现）。
- 好例子（safa-land `router.go` `handleUserByID`）：路径解析 → `switch r.Method` → 每分支 `decodeJSON` + service 调用 + `errors.Is` 错误收口。
- 坏例子：handler 内 `db.QueryContext(...)` 直查 DB——触碰 LOCK-2，Gate `fail`。

出口条件：`AP06` 类入口行为每步骤有代码落点；handler 不直连 DB/外部连接；`go build ./internal/transport/...` 与既有 router 单测通过。

失败判定：handler 直访 repository/DB/cache/outbound；承载业务状态机；用统一 mapper/validator 文件替代逐行为步骤。

### Phase 5 — app / config / main（装配与运行）

产物合同：
- `config.Load()` 集中环境变量 + 默认值（LOCK-5），缺必填项返回 error。
- `app.New(cfg)` 完成 DB 连接（`sql.Open` + 连接池参数 + `Ping`）、各 repository / service / handler 装配、`http.Server` 构造；返回 `*App`。
- `main.go` 控信号 → `app.New` → `app.Run` → `app.Shutdown(ctx)`（LOCK-4），`Shutdown` 在 timeout context 内关 server + 释放 DB。
- 好例子（safa-land `app/app.go`）：`app.New` 内逐个 `repository.NewXRepository(db)` → `service.NewXService(...)` → `httptransport.NewHandler(...)` → `&http.Server{...}`。
- 坏例子：`main.go` 手工 `new` 全部业务对象、跳过 `app.New` 装配层——破坏单一装配入口。

出口条件：最小启动验证通过（或因凭据/基础设施缺失明确 `blocked`）；无手工散落装配；Full/high ordinary 的 packet focused build 通过，Integration 或 non-Full/v1 的 `go build ./...` 通过。

失败判定：业务对象在 `main.go` 散装；启动无信号 / 无优雅关闭；config 被业务层绕过。

### Phase 6 — 验证与符合性审查

见 §5（实现 Gate）。

---

## 5. 实现 Gate（go build / vet / test + lint + 证据）

实现 Gate 是"证据感，不是做完感"。Full/high ordinary 运行 packet-declared deterministic/focused checks；Integration 运行一次下表 workspace 命令。Small、Micro、Lite、non-Full 与 v1 继续按下表既有命令。命令与结果追加到 `verification-evidence.jsonl`；implementation review verdict 进入 `review-records/implementation-reviews.jsonl`。

### 5.1 路由解析后的必跑验证命令

| 类型 | 命令 | 通过判据 |
|------|------|---------|
| Full/high ordinary | packet `deterministic_checks` + planning audit focused checks | 全部通过；不得扩成 workspace-wide 命令 |
| Integration / non-Full / v1 编译 | `go build ./...` | 退出码 0，无编译错误 |
| Integration / non-Full / v1 静态检查 | `go vet ./...` | 退出码 0，无可疑构造告警 |
| Integration / non-Full / v1 测试 | `go test ./...`（或 `project-conventions.md` 指定的等价命令） | 退出码 0；记录受影响包的测试名 |
| Integration / non-Full / v1 lint | `golangci-lint run`（lint 取值见 `project-conventions.md`） | 退出码 0，无新增告警 |
| Integration / non-Full / v1 启动验证 | 最小真实启动 / 调用（`/healthz` 探活、关键 endpoint 冒烟） | 返回预期状态码与响应结构 |
| Integration / non-Full / v1 Secret 残留 | 检查 `config.go` / yaml / fixture / 代码 / `implement.md` / mutable evidence 无明文 secret | 仅出现 env var name / 引用，无真实 key/AK/SK/token |

`verification-evidence.jsonl` 要求：
- 每个切片对应"命令 + 结果"；测试写到测试名级别（如 `ok internal/service 0.3s` + 具体 `Test_UserService_Create_...`）。
- 无法本地验证项（真机表现、外部依赖联调）显式列出，标注留给哪个环节（Manual QA / 远程冒烟机，safa-land 见 `AGENTS.md` `safa-test`）。

### 5.2 Gate 结构判定（guru_gate.py 结构底线）

实现 Gate 结构检查（`guru_gate.py implement`）要求 `implement.md` 计划合同与 mutable evidence 齐全，且**切片挂 UNIT**：

- 计划节（含"计划"或"切片"）
- 执行节（含"执行"或"改动文件"）
- `verification-evidence.jsonl`（含"证据"或 analyze/test）
- 阻塞与偏差节（含"阻塞"或"偏差"）
- 若存在 `UNIT-<slug>`，trace 中必须出现 `UNIT-` 引用（裸编号 token，兼容未来双链包裹）。

下游引用一律写**裸编号 token**：行为写 `BHV-001`，单元写 `UNIT-user-service`；不重排、不复用、删除留洞。

### 5.3 Gate 语义判定（实现审核口径）

`pass` / `fail` / `blocked` 三态，语义判定由实现审核（人工 Gate）逐条核：

- `pass`：先按当前 route 解析验证闭合条件，再检查共同条件。Full/high ordinary 只要求 singular current packet 为 `verified`，且 current packet/audit 选中的 focused checks 成功，不等待或检查 sibling packets；Integration 要求完整依赖 packet set 均有 current receipt，并完成 Integration-selected checks；non-Full/v1 保留原合同，所有计划设计单元 slices 为 `verified` 或明确 `skipped_with_reason`、无悬空 `in_progress`、无被当成完成交付的未验证 `implemented`，且 legacy checks 通过。三路都必须满足 LOCK-1~6、合同八项无偏离，并在当前 route 要求时通过 Secret 检查。
- `fail`：存在合同未实现 / 实现偏离；无 plan 先行证据却已写生产代码；计划已 `blocked` 但代码绕过继续；`implemented` 未验证却交付为完成；触碰任一 LOCK 锁定项；明文 secret 写入配置/代码/fixture；fake / 占位 / 内存 store 生产路径；新增测试超出 §6 allowlist；测试补写业务语义。
- `blocked`：详细设计缺失 / 冲突 / 需确认且已按 §7 记录并回退，未写临时代码绕过；或环境 / 凭据 / 基础设施缺失导致验证无法继续，保留恢复条件。

逐条核查清单：
1. `implement.md` 存在且计划合同齐全，能恢复实现范围、计划状态、设计锚点；代码落点、阶段自检、验证状态、阻塞原因可由 `implement.md` 字段合同与 mutable evidence 合并恢复。
2. 每个切片挂 `UNIT-<slug>`，无幽灵引用（prd 无此 `BHV`）。
3. 代码有 plan 先行证据；计划 `blocked` 但代码继续绕过 → 不得 `pass`。
4. 合同八项每项有代码锚点或 `blocked` 依据；执行流程每步骤有落点。
5. LOCK-1~6 全部满足（框架轻量 / 分层单向 / 错误包装 / 启动关闭 / 配置集中 / 包私有）。
6. 错误 / 事务 / 幂等 / 配置 / 可观测字段未弱化。
7. 生产路径无 fake / 占位 / 硬编码结果 / 内存模拟。
8. 默认只跑既有验证命令；新增测试仅限 §6 allowlist 并回指切片与 `test_target`。
9. Secret 合同闭合：代码 / config / yaml / fixture / trace / mutable evidence 无 secret value；`.env` 未当线上合同。
10. handler 不直访 DB；service 不读 HTTP/env；repository 无业务判定。

---

## 6. 实现期测试边界

- 默认只运行既有验证命令（§5.1），**不默认新增测试用例**，不采用 TDD / RED-GREEN，不先写测试再反向收敛生产代码。
- 新增测试用例不是详细设计承接来源，也不得牵引代码结构。
- allowlist（唯一允许新增的测试）：**无状态、幂等、输入输出明确的纯函数 / 算法 / 静态技术函数**最小单元测试。例如 safa-land 中可对 `validateMonthPlanRange`、`decodeStringArray` 这类纯函数补最小单测；新增前必须已有 `implement.md` 计划或 slice packet 的 `test_target`，detail 确认后新增测试证据写入 `verification-evidence.jsonl`。
- 禁止：新增业务流程测试 / 集成测试 / e2e 测试 / repository-DB 测试 / 外部系统 mock-fake 测试来定义业务语义；为测试通过新增 fake repo/store/adapter、内存模拟、硬编码结果或放宽断言。
- 测试框架取值见 `project-conventions.md`（当前标准 `testing`，可调 testify/ginkgo）；不在本文件硬编码。
- 不适用场景：详细设计已附带独立测试计划 / 业务验收用例时，按该计划执行属于既有验证，不受 allowlist 限制；detail 确认后的执行结果登记到 `verification-evidence.jsonl`。

---

## 7. 存量豁免口径

实现阶段触碰**存量代码**时按以下口径处理；豁免只针对存量违例，**不豁免** golden-path 锁定项（LOCK-1~6）与本次新增代码。

### 7.1 豁免对象与边界

- 豁免对象：仓库内已存在、不符合当前 golden-path / 合同但在本次切片范围**外**的代码（典型：旧服务里残留的大方法、未收敛的错误、横向导入）。
- 不可豁免：LOCK-1~6 锁定项（任何代码都不可违反）；本次切片**新增 / 修改**的代码（必须符合全部合同与 LOCK）。
- 触碰即修 vs 记债：本次切片为完成目标**必须**改动到的存量违例 → 顺手修复并在 mutable evidence 记录；本次切片**不必**改动、改动会扩散影响面的存量违例 → 记债（列出位置 + 原因），不在本次扩大范围（呼应 `AGENTS.md` 外科手术式改动原则）。

### 7.2 处置记录（写入 mutable evidence）

每条触碰的存量违例记录：
- 违例位置（相对路径 + 符号）。
- 处置：`绕行` / `顺手修复` / `记债`。
- 理由：为什么本次不全量修（影响面 / 范围 / 风险）。
- 若是 LOCK 锁定项被存量违反且落在本次必经路径 → 必须修复（不可记债豁免），因为 LOCK 不可豁免。

### 7.3 Gate 交互

- 存量记债项**不阻塞**本次实现 Gate（已显式记录、不在本次范围）。
- 范围外新增违例（本次切片引入的新违例）**阻塞** Gate（`fail`）。
- 缺陷只能回上游修：审核发现结构性缺陷（归属错、合同越界）回到拥有该决策的阶段修订，禁止下游补造（呼应 Harness 总则）。

---

## 8. `implement.md`（trace）主文档合同与 mutable evidence 边界

`implement.md` 是 detail Gate 的 digest-bearing planning/trace contract。建议路径：目标仓库 `docs/design/<feature>/implement.md`（或服务内 `docs/implementation/<module_slug>/implement.md`）。它在 detail 确认前完成并进入 digest；detail 确认后不得作为执行证据默认写入点。实现阶段的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`。若必须修改 `implement.md`，必须回退 detail Gate 并重新 review/confirm。

### 8.1 必含四节（计划合同结构底线）

#### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 切片 | Full/high 读取已确认 planning audit 的真实 `owner_unit`、`covered_units`、文件级 `owned_paths`、完成信号与 focused checks；active worker 不重切。non-Full/v1 保留原有 UNIT / 文件范围 / 完成信号 / 验证方式合同 |
| 执行顺序 | Full/high 按 audit 的真实 `depends_on` 与 `parallel_wave`；domain → repository → service → transport → app 只约束代码依赖，不按 layer 机械生成 slices |
| 风险点 | 预判高风险改动（migration、跨服务契约、共享状态），逐条写验证手段 |

#### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个切片完成时记录：
- 实际改动文件清单（相对路径）。
- 与计划的偏差（改了计划外文件 / 没改计划内文件 → 必须写原因）。
- 代码生成 / 迁移执行记录（跑了哪个脚本 / migration）。

#### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

| 类型 | 要求 |
|------|------|
| Full/high ordinary evidence | 只记录 current packet `deterministic_checks` 与 planning audit focused checks；test / startup / Secret 仅在 packet/audit 明确声明时记录，不自行扩展命令 |
| Integration evidence | 记录完整 workspace build / vet / lint / test / startup / Secret / full regression；测试结果到测试名级别，新增测试清单限 §6 allowlist |
| non-Full/v1 evidence | 保留 legacy evidence 合同：编译、静态、lint、测试名级别结果、最小启动或 `/healthz` 冒烟、Secret 残留检查 |
| 未验证项 | 无法本地验证的（真机、外部联调）→ 显式列出 + 留给哪个环节 |

#### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- 上游缺陷：详细设计合同错 / 漏 → 记录后**回退详细阶段修订**，不就地改设计（`implementation-evidence.jsonl` 留回退记录与恢复条件）。
- 存量违例触碰：列出位置 + 处置（绕行 / 顺手修复 / 记债，见 §7）。
- 未决决策：实现中冒出的新决策点 → 不私自拍板，记录并升级给人工 Gate。

### 8.2 切片状态机

- 固定枚举：`pending` / `in_progress` / `implemented` / `verified` / `blocked` / `skipped_with_reason`。
- 一个 active worker 只推进分配给它的 current packet，不创建或转换 sibling slices；并行宽度由已确认 planning audit 的 `parallel_wave` 决定。
- `implemented` 只表示代码落地；未通过 `checkpoint` 与 `validation_commands` 的切片不得 `verified`。
- `blocked` 必须写明恢复条件与回指（详细设计回修 / 凭据 / 基础设施）。
- `skipped_with_reason` 必须说明设计范围 / 用户范围为何不需要；不得用来隐藏未实现的 required 切片。

### 8.3 反模式

- trace 在 PR 前一次性补写（失去过程证据意义）。
- mutable evidence 只写"全部通过"（无命令、无测试名）。
- 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
- 把 `implement.md` 当设计补写位置；detail 确认后又把它当执行证据写入点。

---

## 9. 反模式总表（Gate `fail`）

- `net/http` 之外引入 gin/echo/chi 等重型框架（违 LOCK-1）。
- handler / service / repository 反向或横向跨 `internal/` 导入（违 LOCK-2）。
- handler 直访 DB/cache/outbound；service 读 HTTP header/cookie/flag；repository 含业务状态机（违 LOCK-2）。
- 裸字符串 error + 字符串比较，或不收敛 `sql.ErrNoRows`（违 LOCK-3）。
- `main.go` 散装业务对象、无信号 / 无优雅关闭（违 LOCK-4）。
- 业务层直读 `os.Getenv`、绕过 `config.Load`（违 LOCK-5）。
- 跨服务 DTO 塞进某服务 `internal/` 并被跨 `internal/` 导入（违 LOCK-6）。
- 详细设计有 `AP06`/`BZ05` 步骤，但代码只写"调用下游 / 处理异常 / 执行业务逻辑"式大方法（违合同八项之 4）。
- 用内存 map / fake repo / 硬编码 adapter 替代真实 SQL repository（违承接合同）。
- 默认 TDD / 先写测试牵引实现，或新增业务流程 / 集成 / e2e / mock-fake 测试定义业务语义（违 §6）。
- 把 API key / 长期 AK/SK / token / password 写进 `config.go` / yaml / fixture / 测试 / 代码 / 日志 / `implement.md`（违 Secret 合同）。
- 用"存量豁免"绕过 LOCK 锁定项或本次新增代码的合同（违 §7）。
- trace 在 PR 前补写、mutable evidence 只写"全部通过"、切片不挂 `UNIT-<slug>`（违 §8 与实现 Gate 结构底线）。
