# 黄金路径：Go 后端开发（通用方法 SSOT · v1）

> **双向拆分版**：本文只包含**类别级方法**（任何 Go HTTP 后端服务怎么做对）与**团队栈级 canonical**（Guru 团队 Go 技术栈统一约定）。**项目级取值一律不出现在本文**——凡标注 `[SLOT-xx]` 处，取值见目标仓库的 `project-conventions.md`（模板：`.trellis/spec/conventions/project-conventions.template.md`）。
> 脚手架模板、`golangci-lint` 规则集、各 agent 适配层**全部从本文派生**，两端都指向本文，不各写一份。改约定先改这里。
> 装载路径：本文安装后位于 `.trellis/spec/guides/golden-path.md`；配套 harness 三件套位于 `.trellis/spec/harness/*`（概要/详细/实现 skill + references）。
> 实测基准仓库：safa-land `services/control-api`（Go monorepo，net/http + 原生 SQL + PostgreSQL）。本文所有代码块均与该仓库当前实现对齐。

核心思想：**一个需求 = 它真正碰到的那几层的 canonical 迷你路径之组合。** 一个完整的 REST endpoint 只是"transport + 下层"的全栈组合；非 transport 需求就是"只跑下层"。

行为单元写 `BHV-NNN`（prd 标题）；设计单元写 `UNIT-<slug>`（详细设计标题）；下游引用一律写裸编号 token（如 `BHV-012`、`UNIT-user-create`）。

---

## 1. 入口决策树：这个需求碰哪几层？

```
需求进来
 ├─ 要对外暴露/改一个 HTTP endpoint?      → 跑 §6 Transport + 它需要的下层
 ├─ 只改业务规则/校验/编排/跨域同步?       → 只跑 §4 Service
 ├─ 只改持久化/SQL/数据读写?              → 只跑 §5 Repository
 ├─ 只改数据形状/JSON 合约/入参出参结构?    → 只跑 §3 Domain（再被上下层消费）
 ├─ 只加/改跨服务契约（agent 也要读的结构）?  → 只跑 §7 Contracts（packages/contracts/）
 └─ 只改一张表/加列/加约束?               → 只跑 §8 DB Migration（再回灌 §5 SQL）
跑完任意层都要过 §9 代码生成（如有）+ §10 自检（go build / go vet / go test / golangci-lint）。
启停/信号/优雅关闭归 §2.6 的 app 生命周期律，新增 endpoint 不碰它，只在 app.New() 里加一行 wiring。
```

---

## 2. canonical 总则（跨层，所有迷你路径都遵守）

### 2.1 分层依赖律（最重要）
依赖方向**只能从上往下**，严禁反向或同层横跳：
```
cmd/<svc>/main.go        （进程入口：装配信号 + 调 app）
        ↓ 只依赖
internal/app             （生命周期编排：New / Run / Shutdown，是唯一允许 import 所有层的装配层）
        ↓ 装配
internal/transport/http  （Handler：解析请求、调 service、写响应；不写业务规则）
        ↓ 只依赖
internal/service         （业务规则 / 校验 / 编排 / 跨域同步；不碰 SQL，不碰 http.Request/ResponseWriter）
        ↓ 只依赖
internal/repository      （数据访问：SQL、扫描、sentinel ErrNotFound；不写业务规则）
        ↓ 只依赖
internal/domain          （纯数据结构 + JSON tag：实体 / 入参 Params / 出参；零依赖、可被任何层 import）
```
**硬禁止（lint 查 import 方向，不可豁免）**：
- ❌ `repository` import `service` 或 `transport`（反向依赖）。
- ❌ `transport` 直接 import `repository` 跑 SQL（跳过 service）——例外：transport 可 import `repository` **仅为 `errors.Is(err, repository.ErrNotFound)` 这一类哨兵判定**（见 §2.3，实测 router.go 即如此用）。
- ❌ `service` 引用 `net/http`、`http.Request`、`http.ResponseWriter`（业务层不得感知传输协议）。
- ❌ `domain` import 本服务任何其它 internal 包（domain 必须是依赖图的叶子）。
- ❌ 跨服务 `import` 另一个服务的 `internal/`（Go `internal/` 编译期隐私，跨服务共享只能走 `packages/contracts/`，见 §7）。
- ❌ 任意两个 internal 包之间形成 import 环。

**框架律（团队栈级 canonical，不可豁免）**：路由层一律 `net/http` 的 `http.ServeMux`，**禁止引入 gin / echo / fiber / chi 等重型或第三方路由框架**。保持标准库可移植、零运行时魔法。

### 2.2 构造注入 + 接口按需收窄（DI 策略）
- **无 DI 框架**（当前栈）：依赖通过**构造函数显式传入**，集中在 `app.New()` 一次性 `NewXxxRepository(db)` → `NewXxxService(repo, ...)` → `NewHandler(...)` 串起来。是否引入 `wire` 由 `[SLOT-01]` 决定，未引入前不得手写全局单例/`init()` 隐式装配。
- **接口只在消费方按需声明、按需收窄**（Go 惯例 "accept interfaces, return structs"）：
  - 构造函数**返回具体类型**（`*UserService`、`*UserRepository`），不返回接口。
  - service 需要 repository 时，**在 service 包内声明它真正用到的那几个方法的最小接口**（实测 `user_service.go` 的 `userStore` 接口），而不是在 repository 包导出一个大接口。这让单测可注入 fake，且依赖面最小。
- ❌ 禁止：包级可变全局变量持有依赖；`init()` 里建数据库连接；service/repository 里 `os.Getenv` 现取配置（配置只从 `config.Config` 经构造注入，见 §2.5）。

### 2.3 错误处理（sentinel + 包装 + errors.Is，团队栈级 canonical）
分三类，各层职责钉死：
- **哨兵错误（sentinel）**：跨层需要被识别的错误，定义为包级 `var Err... = errors.New("<pkg>: <msg>")`。实测两枚：`repository.ErrNotFound`（`repository/errors.go`）、`service.ErrValidation`（`service/errors.go`）；多枚同族哨兵用 `var ( ... )` 块集中（实测 `initenv_service.go` 的 `ErrInitEnv*`）。命名前缀必须是包名（`repository:` / `service:` / `initenv:`），便于日志溯源。
- **包装（wrap）**：附加上下文一律 `fmt.Errorf("%w: ...", ErrXxx, ...)`，保留可追溯链。校验失败的标准写法：`fmt.Errorf("%w: display_name is required", ErrValidation)`。
- **判定（match）**：上层一律 `errors.Is(err, repository.ErrNotFound)` / `errors.Is(err, service.ErrValidation)` 区分语义；判定 PostgreSQL 约束错误用 `errors.As(err, &pqErr)` 取 `pqErr.Code`（实测 `isUniqueViolation`=23505、`isExclusionViolation`=23P01、`isReferenceOrConstraintError`=23503/23514/22P02）。
- **repository 层**：把 `sql.ErrNoRows` 翻译成 `ErrNotFound`（`if errors.Is(err, sql.ErrNoRows) { return nil, ErrNotFound }`——此处 `return nil, ErrNotFound` 裸 sentinel 与 `return nil, fmt.Errorf("%w: …", ErrNotFound)` 包装两种写法皆可接受，取值见下条与 `[SLOT-13]`）；写操作用 `ensureRowsAffected(result)` 把"0 行受影响"也归为 `ErrNotFound`。**不向上抛 `sql.ErrNoRows` 裸错误**。
- **错误翻译强制；包装风格（裸 sentinel vs `%w` 包装）= `[SLOT-13]` 决策**：repository 必须把 `sql.ErrNoRows` 翻译成 `ErrNotFound`——这是硬规则、不可协商（上层只认 sentinel，不得感知 `database/sql` 的裸错误）。但 repository 返回的是**裸 sentinel**（`return nil, ErrNotFound`，当前 safa-land 现状）还是 **`%w` 包装**（`fmt.Errorf("%w: user %d", ErrNotFound, id)`）——属项目级风格选择，由 `[SLOT-13]`（错误处理风格）钉死，本文不强制其一。两种写法 `errors.Is(err, ErrNotFound)` 都判定为真，差异只在是否保留底层上下文链。
- **transport 层（唯一翻 HTTP 状态码的地方）**：用 `errors.Is/As` 把领域错误映射成状态码：`ErrValidation`→400、`ErrNotFound`→404、唯一冲突→409、外键/约束→400、其余→500（`writeInternalError`）。集中在 `handleMutationError(w, err, notFoundMessage)` 复用。
- ❌ 禁止：吞错误（`_ = svc.Do()` 丢弃可恢复错误）；用 `errors.New(fmt.Sprintf(...))` 代替 `fmt.Errorf("%w", ...)` 丢失链；在 service 层写 `http.Error` 或返回状态码。

### 2.4 命名 / 目录约定
- 实体与入参结构在 `internal/domain/<entity>.go`：实体 `User`，入参 `CreateUserParams` / `UpdateUserParams` / `UpdateUserStatusParams`，全部带 `json` tag（见 §3）。
- repository 文件 `internal/repository/<entity>_repository.go`，类型 `<Entity>Repository`，构造 `New<Entity>Repository(db *sql.DB) *<Entity>Repository`。
- service 文件 `internal/service/<entity>_service.go`，类型 `<Entity>Service`，构造 `New<Entity>Service(...)`。
- transport handler 方法 `handle<Resource>` / `handle<Resource>ByID`，挂在唯一的 `*Handler` 上，注册集中在 `Routes()`。
- 跨服务契约在 `packages/contracts/<thing>.go`，类型前缀 `Desired*`（见 §7）。
- 环境变量前缀按服务区分，由 `[SLOT-08]` 取值（实测 `CONTROL_API_*`）。

### 2.5 配置（集中 Load + 默认值 + 构造注入）
- 全部配置集中在 `internal/config/config.go` 的 `Config` 结构 + `Load() (Config, error)`；`main()` 启动时调一次，经 `app.New(cfg)` 注入下去。
- 取值用 helper：`getEnv(key, fallback)`（字符串带默认）、`mustDuration` / `mustInt` / `mustBool`（带默认 + 解析失败 `panic`，因为是启动期不可恢复配置）。
- **必填项缺失返回 error 而非 panic**（实测 `DatabaseURL` 为空时 `return Config{}, fmt.Errorf("DATABASE_URL is required")`），交 `main()` `log.Fatalf`。
- 是否切到 `slog`/`zap`（日志）、`testify`/`ginkgo`（测试）、`ent`/`sqlc`（ORM）由对应 `[SLOT-xx]` 决定；未切换前用标准库（`log` / `testing` / 原生 `database/sql`）。

### 2.6 App 生命周期律（启动/关闭，团队栈级 canonical）
固定四步、信号在 `main`、装配在 `app`：
- `main()`：`config.Load()` → `app.New(cfg)` → goroutine 跑 `app.Run()`（`ListenAndServe`）→ `signal.Notify(SIGINT, SIGTERM)` → 收到信号或 server 出错后 `context.WithTimeout(cfg.ShutdownTimeout)` → `app.Shutdown(ctx)`。`http.ErrServerClosed` 视为正常退出，不 `Fatal`。
- `app.New(cfg)`：开 `sql.DB`、设连接池（`SetMaxOpenConns/SetMaxIdleConns/SetConnMaxLifetime`）、`db.Ping()` 失败则 `db.Close()` 并返回 error；装配所有 repo/service/handler；构造 `*http.Server` 并设 `ReadTimeout/WriteTimeout/IdleTimeout`。
- `app.Run()`：`return a.server.ListenAndServe()`。
- `app.Shutdown(ctx)`：`server.Shutdown(ctx)` + `db.Close()`，两个错误都尝试、优先返回 server 错误。
- **Handler 一律接收 `ctx context.Context`**：每个 handler 用 `r.Context()` 透传到 service/repository 的 `QueryContext/ExecContext`；需要兜底超时的 handler 自建 `context.WithTimeout`（实测 `handleHealthz` 2s）。
- ❌ 禁止：在 handler 里 `context.Background()` 替代 `r.Context()`（丢失取消/超时）；不带 timeout 的 `*http.Server`；`Shutdown` 里漏关 db。

### 2.7 文件大小指南（非硬性）
service/repository 单文件 > 600 行评审职责单一性；> 1000 行须拆分或写明理由。router.go 因 ServeMux 集中注册天然偏大，按"每资源一组 handler 方法"分段即可，不强拆。

---

## 3. Domain 迷你路径（纯数据结构）

domain 是依赖叶子：**只有 struct + json tag + 零业务方法**（校验在 service，扫描在 repository）。新增一个资源先在 `internal/domain/<entity>.go` 定形状。

```go
package domain

import "time"

// 实体：对外 JSON 形状。可空字段用指针 + omitempty。
type User struct {
	ID                       int64           `json:"id"`
	ExternalRef              *string         `json:"external_ref,omitempty"`
	ApplicationAccountID     *int64          `json:"application_account_id,omitempty"`
	DisplayName              string          `json:"display_name"`
	ProxyUsername            string          `json:"proxy_username"`
	Status                   string          `json:"status"`
	SourceIPAllowlist        []string        `json:"source_ip_allowlist"`
	MaxConcurrentConnections *int            `json:"max_concurrent_connections,omitempty"`
	MonthPlan                []UserMonthPlan `json:"month_plan"`
	CreatedAt                time.Time       `json:"created_at"`
	UpdatedAt                time.Time       `json:"updated_at"`
}

// 入参：Create / Update / UpdateStatus 各一个独立结构。
// 创建必填字段用值类型；可选字段用指针（区分"未传"与"传零值"）。
type CreateUserParams struct {
	ExternalRef              *string  `json:"external_ref,omitempty"`
	DisplayName              string   `json:"display_name"`
	ProxyUsername            string   `json:"proxy_username"`
	SourceIPAllowlist        []string `json:"source_ip_allowlist,omitempty"`
	MaxConcurrentConnections *int     `json:"max_concurrent_connections,omitempty"`
}

type UpdateUserStatusParams struct {
	Status string `json:"status"`
}
```

约束：
- ✅ 可空字段用 `*T` + `,omitempty`；必传字段用值类型。
- ✅ "未传"与"传零值"必须可区分时（如 PATCH 部分更新）一律用 `*T`（实测 `UpdateUserMonthPlanParams.StartsAt *time.Time`）。
- ❌ domain 里不写 `Validate()`（校验属 service）、不写 `Scan()`（扫描属 repository）、不 import 其它 internal 包。
- ❌ 不在 domain 里放 `db:` ORM tag（当前栈用原生 SQL 手动扫描，无 ORM tag；切 `ent`/`sqlc` 由 `[SLOT-02]` 决定）。

## 4. Service 迷你路径（业务规则 / 校验 / 编排）

service 拿 domain 入参，跑校验与编排，调 repository，做跨域同步。**只认 `context.Context`，绝不认 `http.*`。**

```go
package service

import (
	"context"
	"fmt"
	"strings"

	"github.com/<org>/<repo>/services/<svc>/internal/domain"
)

// 在 service 包内声明它真正用到的最小接口（accept interfaces）。
// 单测可注入 fake；生产注入 *repository.UserRepository（结构体实现了这些方法）。
type userStore interface {
	GetByID(ctx context.Context, id int64) (*domain.User, error)
	Create(ctx context.Context, params domain.CreateUserParams) (*domain.User, error)
	UpdateStatus(ctx context.Context, id int64, status string) (*domain.User, error)
	Delete(ctx context.Context, id int64) error
}

type UserService struct {
	repo       userStore
	configSync *ConfigSyncService // 单向依赖同层 service：允许，构造注入，不得成环
}

func NewUserService(repo userStore, configSync *ConfigSyncService) *UserService {
	return &UserService{repo: repo, configSync: configSync}
}

func (s *UserService) Create(ctx context.Context, params domain.CreateUserParams) (*domain.User, error) {
	// 1) 校验：失败一律 %w 包装 ErrValidation
	params.DisplayName = strings.TrimSpace(params.DisplayName)
	if params.DisplayName == "" {
		return nil, fmt.Errorf("%w: display_name is required", ErrValidation)
	}
	// 2) 写库（repository 已把 sql.ErrNoRows 翻成 ErrNotFound，这里直接透传）
	user, err := s.repo.Create(ctx, params)
	if err != nil {
		return nil, err
	}
	// 3) 编排副作用：跨域同步失败要上抛，调用方据此回滚/告警
	if err := s.configSync.TouchNodesForUser(ctx, user.ID); err != nil {
		return nil, err
	}
	return user, nil
}
```

约束：
- ✅ 校验失败 = `fmt.Errorf("%w: ...", ErrValidation)`；`ctx` 一路透传。
- ✅ 枚举校验用 `switch` + default 报错（实测 status `switch params.Status { case "active","disabled","suspended": default: ...ErrValidation }`）。
- ✅ service → service **单向**依赖允许（构造注入具体类型，如 `*ConfigSyncService`、`*RouteSyncService`）；出现互相调用倾向时抽更高层编排 service 或把共享逻辑下沉 repository。
- ❌ 不 import `net/http`；不返回 HTTP 状态码；不直接拼 SQL；不读环境变量（配置经构造注入）。

**Service vs Repository 职责边界**：业务规则、跨实体校验、副作用编排在 service；纯数据存取、SQL、行扫描在 repository。repository 不认 `ErrValidation`，service 不写 SQL。

## 5. Repository 迷你路径（数据访问 / SQL）

repository 持 `*sql.DB`，用 `Context` 版 API，手动扫描到 domain，翻译哨兵错误。

```go
package repository

import (
	"context"
	"database/sql"
	"errors"

	"github.com/<org>/<repo>/services/<svc>/internal/domain"
)

type UserRepository struct {
	db *sql.DB
}

func NewUserRepository(db *sql.DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) GetByID(ctx context.Context, id int64) (*domain.User, error) {
	row := r.db.QueryRowContext(ctx, `
		SELECT id, display_name, proxy_username, status, created_at, updated_at
		FROM users
		WHERE id = $1
	`, id)

	var user domain.User
	if err := row.Scan(&user.ID, &user.DisplayName, &user.ProxyUsername, &user.Status, &user.CreatedAt, &user.UpdatedAt); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			// ✅ 翻译哨兵（硬规则），不向上抛 sql.ErrNoRows。
			// 裸 sentinel（下行）与 fmt.Errorf("%w: user %d", ErrNotFound, id) 包装两种皆可接受 = [SLOT-13] 决策；errors.Is 都判定为真。
			return nil, ErrNotFound
		}
		return nil, err
	}
	return &user, nil
}

func (r *UserRepository) Delete(ctx context.Context, id int64) error {
	result, err := r.db.ExecContext(ctx, `DELETE FROM users WHERE id = $1`, id)
	if err != nil {
		return err
	}
	return ensureRowsAffected(result) // ✅ 0 行 = ErrNotFound
}
```

约束：
- ✅ 一律 `QueryContext` / `QueryRowContext` / `ExecContext`（带 ctx）；`rows` 必 `defer rows.Close()`，循环后查 `rows.Err()`。
- ✅ 参数化查询用 `$1,$2...`（PostgreSQL 占位符），**永不字符串拼接 SQL**（注入风险）。
- ✅ 数组入参用 `pq.Array(...)`（实测 `WHERE user_id = ANY($1)`）；可空列用 `sql.NullString/NullInt64/NullTime` 扫描后经 `nullableString` 等 helper 转 `*T`。
- ✅ 扫描复用：多处用同一行形状时抽 `scanXxx(scanner)` + `type xxxScanner interface{ Scan(...) error }`（实测 `scanUser`，`*sql.Row` 与 `*sql.Rows` 都满足）。
- ❌ 不在 repository 写业务校验、不返回 `ErrValidation`、不感知 HTTP。
- ❌ 不裸抛 `sql.ErrNoRows`、不忽略 `ExecContext` 的 `RowsAffected`。

helper 收口在 `internal/repository/helpers.go`：`ensureRowsAffected`、`nullableString/nullableInt/nullableInt64/nullableFloat64/nullTimePtr`、`decodeStringArray`。新 repository 复用，不各写一份。

## 6. Transport 迷你路径（HTTP endpoint，= 全栈 feature 的顶层）

唯一 `*Handler` 持所有 service；`Routes()` 集中注册 `http.ServeMux`；handler 解析→调 service→映射错误→写 JSON。

**注册（`Routes()`，集中在 router.go）**：集合用裸路径 `"/api/v1/users"`，带 ID/子路径用尾斜杠前缀 `"/api/v1/users/"`，鉴权资源包 `h.requireAdmin(...)`：
```go
func (h *Handler) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", h.handleHealthz)
	mux.HandleFunc("/api/v1/users", h.requireAdmin(h.handleUsers))
	mux.HandleFunc("/api/v1/users/", h.requireAdmin(h.handleUserByID))
	return mux
}
```

**集合 handler（按 method 分支，每分支自负解码/调用/错误映射）**：
```go
func (h *Handler) handleUsers(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		users, err := h.users.List(r.Context())
		if err != nil {
			writeInternalError(w, err)
			return
		}
		writeJSON(w, http.StatusOK, jsonResponse{"data": users})
	case http.MethodPost:
		var req domain.CreateUserParams
		if err := decodeJSON(r, &req); err != nil { // 严格解码：DisallowUnknownFields + 单对象
			writeJSON(w, http.StatusBadRequest, jsonResponse{"error": err.Error()})
			return
		}
		user, err := h.users.Create(r.Context(), req)
		if err != nil {
			switch { // ✅ 错误→状态码映射唯一发生在 transport
			case errors.Is(err, service.ErrValidation):
				writeJSON(w, http.StatusBadRequest, jsonResponse{"error": err.Error()})
			case isUniqueViolation(err):
				writeJSON(w, http.StatusConflict, jsonResponse{"error": err.Error()})
			default:
				writeInternalError(w, err)
			}
			return
		}
		writeJSON(w, http.StatusCreated, jsonResponse{"data": user})
	default:
		methodNotAllowed(w, r.Method, http.MethodGet, http.MethodPost) // 设 Allow 头 + 405
	}
}
```

canonical 规则：
- ✅ 路径参数用 `parseIDParam(r.URL.Path, prefix)`（解析失败 → 404，不 500）；多段子资源写专用 `parseXxxPath`。
- ✅ 请求体解码统一走 `decodeJSON(r, &req)`：`DisallowUnknownFields()` + 拒绝多 JSON 对象（防止脏字段静默通过）。
- ✅ 响应统一 `writeJSON(w, status, jsonResponse{"data": ...})` 成功 / `{"error": ...}` 失败；`jsonResponse` = `map[string]interface{}`。
- ✅ method 不匹配走 `methodNotAllowed`（设 `Allow` 头 + 405），不静默 200。
- ✅ 变更类 handler 错误映射复用 `handleMutationError(w, err, "<resource> not found")`。
- ✅ 鉴权：受保护路由包 `h.requireAdmin(next)`（HMAC-SHA256 签名 cookie 校验，由 `SessionManager.ParseCookie` 解；密码侧 bcrypt，自实现，是否切库由 `[SLOT-10]` 决定）。
- ❌ handler 里写业务校验（属 service）、拼 SQL（属 repository）、`context.Background()`（应 `r.Context()`）、忘记 `return` 导致双写响应头。

## 7. Contracts 迷你路径（跨服务契约）

跨服务（如 control-api 与 proxy-agent）共享、agent 也要读懂的结构，**不放 `internal/`（编译期隔离），放 `packages/contracts/<thing>.go`**。

```go
package contracts

import (
	"encoding/json"
	"time"
)

// Desired 前缀 = "期望态"契约：一端生成、另一端消费。字段全带 json tag，可空用指针+omitempty。
type DesiredNodeConfig struct {
	NodeID               int64                  `json:"node_id"`
	NodeName             string                 `json:"node_name"`
	DesiredConfigVersion int64                  `json:"desired_config_version"`
	Metadata             json.RawMessage        `json:"metadata"` // 不预解析的透传块用 json.RawMessage
	GeneratedAt          time.Time              `json:"generated_at"`
	EntryListeners       []DesiredEntryListener `json:"entry_listeners"`
}
```

约束：
- ✅ 契约结构零行为、零业务依赖（同 domain 的纯数据律），可被多个服务 import。
- ✅ 不预解析、原样透传的子块用 `json.RawMessage`（实测 `Metadata`）。
- ✅ 改契约即改双方合同：JSON 字段名/类型变更属破坏性变更，必须在 prd/详细设计里写明并同步消费端。
- ❌ 不把 `packages/contracts/` 当 domain 的别名乱放服务内部结构；只放真·跨边界结构。

## 8. DB Migration 迷你路径（改表 / 加列 / 加约束）

迁移文件成对放仓库根 `db/migrations/`，命名 `NNNN_<slug>.up.sql` + `NNNN_<slug>.down.sql`，序号 +1，不跳号。

```sql
-- 0013_user_month_plans.up.sql
BEGIN;
CREATE EXTENSION IF NOT EXISTS btree_gist; -- 需要扩展时 IF NOT EXISTS

CREATE TABLE user_month_plans (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT user_month_plans_range_ck CHECK (starts_at < ends_at),
  CONSTRAINT user_month_plans_no_overlap EXCLUDE USING gist (
    user_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&
  )
);
CREATE INDEX user_month_plans_user_starts_at_idx ON user_month_plans (user_id, starts_at DESC);
CREATE TRIGGER user_month_plans_set_updated_at
  BEFORE UPDATE ON user_month_plans FOR EACH ROW EXECUTE FUNCTION set_updated_at();
COMMENT ON TABLE user_month_plans IS 'Informational month-plan history for proxy users.';
COMMIT;
```
```sql
-- 0013_user_month_plans.down.sql：精确逆操作，可重入
BEGIN;
DROP TRIGGER IF EXISTS user_month_plans_set_updated_at ON user_month_plans;
DROP INDEX IF EXISTS user_month_plans_user_starts_at_idx;
DROP TABLE IF EXISTS user_month_plans;
COMMIT;
```

约束：
- ✅ up 与 down 同时提交，down 是 up 的精确逆且用 `IF EXISTS` 保证可重入。
- ✅ up/down 各包在 `BEGIN; ... COMMIT;` 单事务里（DDL 在 PostgreSQL 可事务化）。
- ✅ 主键 `BIGINT GENERATED ALWAYS AS IDENTITY`；时间列 `TIMESTAMPTZ NOT NULL DEFAULT NOW()`；外键带 `ON DELETE` 策略；约束命名 `<table>_<purpose>_ck/_idx/_no_overlap`。
- ✅ 新增 NOT NULL 列必须带 `DEFAULT` 或分两步（先加可空列回填再加约束），否则破坏既有行。
- ✅ 改表后回灌 §5：repository 的 SELECT/INSERT 列清单、`scanXxx` 字段、domain struct 字段三处同步。
- ❌ 改已合入的旧迁移文件（迁移是 append-only）；跳号；写不可逆 down（无 down 文件）；漏 COMMENT（实测对表/列加 `COMMENT ON`）。

## 9. 代码生成（当前栈：基本无；按槽位条件触发）
当前栈用原生 `database/sql`、无 DI 框架、无 OpenAPI 生成，**默认无代码生成步骤**。仅当对应槽位切换后才出现：
```
若 [SLOT-01]=wire        → wire ./...                （DI 生成）
若 [SLOT-02]=sqlc        → sqlc generate              （查询/模型生成）
若 [SLOT-09]=swagger     → swag init                  （OpenAPI 文档生成）
```
生成产物随源码提交，不进 `.gitignore`。

## 10. 自检
```bash
go build ./...          # 编译通过（含 import 方向不成环）
go vet ./...            # 静态检查
go test ./...           # 单测（当前 testing；testify/ginkgo 由 [SLOT-04] 决定）
golangci-lint run       # 团队 lint 门禁（[SLOT-07] 规则集）
gofmt -l .              # 格式（输出非空即未格式化，须为空）
```

---

## 10b. 自检产物合同（可验证信号）
- **入口决策树命中**：需求被归到 §3–§8 中明确的层，且未越层（如"只改业务规则"不应出现 SQL 改动）。
- **依赖方向干净**：`go build ./...` 通过且无 import 环；`transport` 无 SQL、`service` 无 `net/http`、`domain` 无 internal import。
- **错误链完整**：所有校验错误 `errors.Is(_, service.ErrValidation)` 为真；所有"找不到"`errors.Is(_, repository.ErrNotFound)` 为真；状态码映射只在 transport。
- **生命周期完好**：`main`→`app.New`→`app.Run`→`app.Shutdown` 四步在；handler 用 `r.Context()`。
- **迁移成对可逆**：up/down 同序号成对存在，down 含 `IF EXISTS`。

---

## 11. 禁止清单（汇总，门禁拦）

**通用硬禁止（任何 Go 后端服务不可豁免）**：
- ❌ 引入 gin/echo/fiber/chi 等替代 `net/http` ServeMux（§2.1 框架律）。
- ❌ 反向依赖：`repository`/`service` import 上层；`domain` import 任何 internal 包（§2.1）。
- ❌ `service` 引用 `net/http` / `http.Request` / `http.ResponseWriter`（§2.1/§4）。
- ❌ 跨服务 import 另一服务的 `internal/`（应走 `packages/contracts/`）（§2.1/§7）。
- ❌ internal 包之间 import 成环（§2.1）。
- ❌ 包级全局可变依赖 / `init()` 建连接 / service 内 `os.Getenv`（§2.2/§2.5）。
- ❌ `errors.New(fmt.Sprintf(...))` 代替 `fmt.Errorf("%w", ...)` 丢失链；吞错误（§2.3）。
- ❌ repository 裸抛 `sql.ErrNoRows`、忽略 `RowsAffected`、字符串拼接 SQL（§5）。
- ❌ handler 写业务校验/SQL、用 `context.Background()` 替 `r.Context()`、method 不匹配静默 200（§6）。
- ❌ `*http.Server` 无 timeout、`Shutdown` 漏关 db、`main` 把 `http.ErrServerClosed` 当致命错误（§2.6）。
- ❌ 改已合入的旧迁移、迁移跳号、写无 down 的不可逆迁移（§8）。

**按项目约定执行的禁止（取值见 project-conventions）**：
- ❌ 违反 `[SLOT-08]` 环境变量前缀（跨服务变量名串台）。
- ❌ 在未切换 `[SLOT-02]` ORM 前给 domain 加 ORM tag / 在未引 `[SLOT-01]` wire 前手写隐式装配。
- ❌ 日志绕过 `[SLOT-03]` 选定的 logger（当前 `log`，切 `slog`/`zap` 后不得混用）。

## 12. 门禁映射（三层各管什么）
| 规则 | 脚手架 | golangci-lint | review |
|------|:---:|:---:|:---:|
| §2.1 分层依赖律 / 框架律 | ✅(目录骨架) | ✅(depguard import 方向/禁框架) | ✅ |
| §2.2 构造注入 / 最小接口 | ✅ | | ✅ |
| §2.3 错误处理（sentinel/wrap/Is） | | ✅(errcheck/errorlint/wrapcheck) | ✅ |
| §2.4 命名 / 目录 | ✅ | ✅(读项目约定) | |
| §2.5 配置集中 Load | ✅ | ✅(禁 service 内 os.Getenv) | ✅ |
| §2.6 app 生命周期 | ✅(main+app 骨架) | | ✅ |
| §4 service 不碰 http | | ✅(depguard) | ✅ |
| §5 repository SQL 安全 / 哨兵 | | ✅(sqlclosecheck/rowserrcheck) | ✅ |
| §6 transport 错误映射/解码 | ✅ | | ✅ |
| §7 contracts 跨服务隔离 | ✅ | ✅(internal 隐私) | ✅ |
| §8 迁移成对可逆 | ✅(模板) | | ✅ + hooks |
| §10 自检（build/vet/test/lint/fmt） | | ✅ | hooks(回灌) |

## 13. 派生关系（给 build 用）
- **脚手架模板** ← §2.6 + §3/§4/§5/§6/§7/§8 的代码块参数化（参数 = project-conventions 槽位）；按 §1 入口决策树条件组合生成对应层文件。
- **`golangci-lint` 规则集** ← §2.1（depguard：禁重型框架 + import 方向）+ §2.3（errcheck/errorlint/wrapcheck）+ §5（sqlclosecheck/rowserrcheck）+ §11（槽位类规则运行时读目标仓库 project-conventions）。
- **配置包 Skill（概要/详细/实现三件套）** ← 全文 + 各自 references；所有 agent 适配层**指向本文**，不各写一份。概要归属表把每条需求映射到 §3–§8 层与 `BHV-NNN`；详细合同回答八问；实现 trace 计划合同与 mutable evidence 回链到 `UNIT-<slug>`。
- **hooks** ← §8 迁移成对/序号校验 + §10 自检回灌（提交前跑 `go build`/`go vet`/`gofmt -l`/`golangci-lint run`）+ §11 老目录/裸 `os.Getenv` 拦截（读 `[SLOT-08]`）。

---

### 附：项目约定槽位索引（取值见 `.trellis/spec/conventions/project-conventions.md`）
- `[SLOT-01]` DI 框架：当前无（构造注入）→ 可 `wire`。
- `[SLOT-02]` ORM/数据访问：当前原生 `database/sql` + `lib/pq` + PostgreSQL → 可 `ent`/`sqlc`。
- `[SLOT-03]` 日志：当前标准 `log` → 可 `slog`/`zap`。
- `[SLOT-04]` 测试框架：当前 `testing` → 可 `testify`/`ginkgo`。
- `[SLOT-05]` API 风格：当前 REST JSON → 可 gRPC。
- `[SLOT-06]` DB 驱动/连接形态：当前 `lib/pq` + PostgreSQL → 可 `pgx`/`pgxpool`。
- `[SLOT-07]` lint 规则集：`golangci-lint`（具体启用规则）。
- `[SLOT-08]` 环境变量前缀/配置加载：按服务区分（实测 `CONTROL_API_*`）。
- `[SLOT-09]` API 文档生成：当前无 → 可 Swagger/OpenAPI（`swag`）。
- `[SLOT-10]` 会话/鉴权：当前 HMAC-SHA256 签名 cookie + bcrypt（自实现）。
- `[SLOT-11]` 包组织/分层目录：标准分层 `internal/{app,config,transport,service,repository,domain,auth}` + `packages/contracts/`。
- `[SLOT-12]` 数据库迁移：`db/migrations/` 成对 `NNNN_*.up.sql`/`.down.sql`（`golang-migrate` 风格）→ 可 `goose`/`ent`。
- `[SLOT-13]` 错误处理风格：sentinel 归属/包装（裸 sentinel vs `%w`）/状态码映射层。
- `[SLOT-14]` 启动/关闭与超时：`main` 控信号 → `app.New/Run/Shutdown`，超时数值与宽限期。
- `[SLOT-15]` 接口抽象/DIP：消费方本地最小接口（`xxxStore`）vs 被依赖方导出。
- `[SLOT-16]` 可穷举字段（枚举）表达：Go 具名枚举 vs 裸 `string`；非法值收口层。
- `[SLOT-17]` 存量违例清单（tech-debt 登记）。
