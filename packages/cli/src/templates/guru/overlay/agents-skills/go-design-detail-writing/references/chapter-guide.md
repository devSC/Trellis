# Go 后端详细设计分章写作指南（references）

> 编排层产物：只补充逐类写法细则、章节模板与示例，不替代 L1/L2/golden-path。规则正文与完成条件以
> `.trellis/spec/harness/detail/detail-structure-single-source.md`（L1）、`detail-type-{entry-api,biz,repository-data}.md`（L2）、
> `.trellis/spec/guides/golden-path.md`（通用方法真源）为准。冲突时 **L1 > L2 > golden-path 引用注解 > project-conventions 槽位取值 > 本文件**。
> 本文件只回答「拿到一个 `chapter_target` 后，按它的 `detail_doc_type` 怎么把骨架填满到可编码粒度」。

## 1. 规范装载矩阵（按当前批次命中装载，不全量装）

只对当前批次命中的 doc_type 装载对应 L2 与 golden-path 迷你路径，不为后续章节预加载无关类型正文。

| detail_doc_type | owner 层 / 落点 | L2 文件 | 额外必读（golden-path） |
|-----------------|-----------------|---------|------------------------|
| `entry-api` | transport — `internal/transport/http` | `detail-type-entry-api.md`（v1） | §6 Transport 迷你路径、§2.1 分层依赖律、§2.3 错误→状态码映射 |
| `biz` | service — `internal/service/*_service.go` | `detail-type-biz.md`（v1） | §4 Service 迷你路径、§2.2 构造注入/最小接口、§2.3 sentinel+`%w`+`errors.Is` |
| `repository-data` | repository — `internal/repository`、`db/migrations/` | `detail-type-repository-data.md`（v1） | §5 Repository 迷你路径、§8 DB Migration 迷你路径、§2.3 `sql.ErrNoRows`→`ErrNotFound` |
| `domain` | domain — `internal/domain/*.go` | 无（pending，按 L1 八问） | §3 Domain 迷你路径 + `L2豁免` 声明 |
| `config` | — `internal/config/config.go` | 无（pending，按 L1 八问） | §2.5 配置范式 + `L2豁免` 声明 |
| `external` | — `transport/<svc>client/`、`packages/contracts/` | 无（pending，按 L1 八问） | §7 Contracts 迷你路径 + `L2豁免` 声明 |
| `runtime` | — `internal/app/app.go`、`cmd/<svc>/main.go` | 无（pending，按 L1 八问） | §2.6 App 生命周期律 + `L2豁免` 声明 |

- pending 类型（`domain`/`config`/`external`/`runtime`）：按 L1 §3 合同八问展开，文档头标注 `l2_status: pending`；**full 链** design-main 须有 `L2豁免：<doc_type> 理由：…`（无豁免则 gate 拦截，先补 L2 或写豁免）。
- 装载完 L2 后，正文规则疑义回 L1，引用写结构化字段 `rule_ref=<规范文件路径#章节锚点>`，不在本指南或正文重定义规则。

## 2. 章节正文模板（L1 §4 骨架的操作版）

新章节从此模板起稿（full 链=`chapters/<slug>.md`，文件名与概要承接索引一致；light 链=`design.md §详细` 内一章，可压缩小节层级）。模板是表达形式，**L1 §3 合同八问是完成条件**，二者必须同时满足。

````markdown
# <chapter_target> 详细设计

> doc_type：biz ｜ l2_status：v1 ｜ 承接索引：design-main.md 第 6 章 <chapter_target>
> entry_kind：<http_endpoint / cli_command / scheduled_job / message_consumer>（仅 entry-api 必填）
> 归属回指：归属判定表第 <行> 行（owner=service）
> 返回：[design-main](../design-main.md)

## 1. 单元职责
`UserService` 是用户业务规则与 `user.status` 终态推进的唯一写 owner，封装创建/更新/状态流转/月度套餐
（month_plan）的校验、重叠判定与跨域同步编排。位于 service 层，向下依赖 `userStore`（repository 接口，
`dep_kind=repo`）与下层 `RouteSyncService`/`ConfigSyncService`（`dep_kind=infra`，单向）；被 `transport/http`
的用户 handler 调用（反向不依赖任何 transport 组件）。

## 2. 行为定义
### 2.1 行为清单（每行为一行：行为名 + 简述 + 承接 BHV-NNN）
- Create — 创建用户：字段校验 + 关联账户必须 active + 创建后同步路由（BHV-101）｜详见 §4.1
- CreateMonthPlan — 新增月度套餐：区间合法 + 同用户不重叠（BHV-103）｜详见 §4.2

### 2.2 接口定义（Go 签名级，禁止超过签名级的实现体）
```go
type UserService interface {
    Create(ctx context.Context, params domain.CreateUserParams) (*domain.User, error)
    CreateMonthPlan(ctx context.Context, userID int64, params domain.CreateUserMonthPlanParams) (*domain.UserMonthPlan, error)
}
```

## 3. 核心数据结构
### 3.1 数据结构（domain struct 在 domain 类承接；biz 只引用，不重定义）
入参引用 `domain.CreateUserParams` / `domain.CreateUserMonthPlanParams`（owner=domain 类，见对应章），biz 不重定义实体。

### 3.2 错误类型表（sentinel error）
| 错误名（var ErrXxx） | 定义层 | 语义 | 包装方式（%w 链） | 上抛/收口位置 |
|----------------------|--------|------|-------------------|---------------|
| `service.ErrValidation` | service | 入参/业务规则校验失败（业务可恢复） | `fmt.Errorf("%w: <字段> ...", ErrValidation)` | biz 内返回；handler `errors.Is`→400 |
| `repository.ErrNotFound` | repository | 关联实体不存在（透传） | 下层已翻译，biz 按业务语义透传或吞 | biz 透传；handler `errors.Is`→404 |

## 4. 逐行为设计（每个行为一小节）
### 4.1 Create
- 函数签名：`func (s *UserService) Create(ctx context.Context, params domain.CreateUserParams) (*domain.User, error)`
- 简述：承接 BHV-101——校验字段、要求关联应用账户为 active、写库、创建后同步路由策略。
- 输入参数表：
  | 参数 | 类型 | 取值域/约束 | 必填 |
  |------|------|-------------|------|
  | ctx | context.Context | 承载请求级 timeout/cancel | 是 |
  | params.DisplayName | string | TrimSpace 后非空 | 是 |
  | params.ProxyUsername | string | TrimSpace 后非空 | 是 |
  | params.ApplicationAccountID | *int64 | nil 跳过；非 nil 必须 > 0 且账户 active | 否 |
- 输出表：
  | 返回值 | 类型 | 语义 |
  |--------|------|------|
  | user | *domain.User | 创建成功的用户实体 |
  | err | error | `ErrValidation` / 下层错误（`%w` 链上抛） |
- 执行流程：
  ```mermaid
  sequenceDiagram
      participant H as UserHandler
      participant S as UserService
      participant AA as ApplicationAccountRepository
      participant R as userStore(repo)
      participant RS as RouteSyncService
      H->>S: 1. Create(ctx, params)
      S->>S: 2. 校验 ApplicationAccountID>0 与字段非空
      S->>AA: 3. GetByID(ctx, *applicationAccountID)（非 nil 时）
      AA-->>S: 4. account / err
      S->>R: 5. Create(ctx, params)
      R-->>S: 6. *domain.User / err
      S->>RS: 7. SyncUser(ctx, user.ID)
      RS-->>S: 8. err（失败则上抛）
      S-->>H: 9. *domain.User / error
  ```
- 流程详述（与图中编号一一对应，满足 L1 §3.1 粒度）：
  1. handler 透传 `ctx := r.Context()`，进入 `Create(ctx, params)`。
  2. `params.ApplicationAccountID != nil && *params.ApplicationAccountID <= 0` → `fmt.Errorf("%w: application_account_id must be > 0", ErrValidation)`，终止。
  3-4. `requireActiveApplicationAccount(ctx, params.ApplicationAccountID)`：非 nil 时 `applicationAccounts.GetByID(ctx, id)`，`account.Status != "active"` → `%w ErrValidation`。
  5. `validateUserFields(...)` 通过后调 `repo.Create(ctx, params)`（repository 已把 `sql.ErrNoRows` 翻成 `ErrNotFound`，唯一约束冲突由 handler 用 `isUniqueViolation` 映射 409）。
  6. 写库失败 → 直接透传错误（`%w` 链由下层保留）。
  7-8. 成功后 `routeSync.SyncUser(ctx, user.ID)`；同步失败上抛，调用方据此告警/回滚。
  9. 全部成功返回 `user, nil`。
- 异常处理表：
  | 异常情况 | 处置（wrap/重试/降级/上抛） | errors.Is 判定位置 | 错误转换位置（哪层） |
  |----------|------------------------------|--------------------|----------------------|
  | 字段为空/非法 | 返回 `%w ErrValidation`，无副作用 | handler→400 | biz（本单元） |
  | 关联账户非 active | 返回 `%w ErrValidation` | handler→400 | biz（本单元） |
  | 写库唯一冲突 | 透传 pq 错误 | handler `isUniqueViolation`→409 | repository |
  | 路由同步失败 | 上抛（系统不可恢复） | handler→500 | 下层 service |

## 5. 状态与事务（biz 类必含）
- 状态 owner：`user.status` 终态推进（active/disabled/suspended）的唯一写 owner = `UserService`（回指归属表第 <行> 行）；
  禁止其它 service 写同一状态（双写=P1，回概要重判）。
- 事务边界（三选一给结论）：`Create` 为单条写 + 创建后跨域同步（路由策略写库 + 触达节点）→ **本地数据库事务不覆盖跨域同步**；
  采用「写用户成功后异步/顺序触发同步，同步失败上抛由调用方收口」语义，不把「写库 + 多表同步」硬塞进一个本地事务。

## 6. 数据合同（repository-data 类必含；biz 写 N/A）
N/A（biz 不持有 SQL/表结构；存储介质与索引归 repository-data 类，见对应章）。

## 7. 测试映射
| BHV/行为 | 测试层 | 测试点（成功 + 全部失败路径逐条） |
|----------|--------|------------------------------------|
| BHV-101 成功 | unit | mock repo Create 成功 + RouteSync 成功 → 返回 user |
| BHV-101 字段空 | unit | DisplayName 空 → `errors.Is(err, ErrValidation)` |
| BHV-101 账户非 active | unit | mock 账户 status!=active → `errors.Is(err, ErrValidation)` |
| BHV-103 区间非法 | unit | starts_at==ends_at → `errors.Is(err, ErrValidation)` |
| BHV-103 重叠 | unit | 同用户已有重叠套餐 → `errors.Is(err, ErrValidation)` |

## 8. 不得补造清单
- 不决定 HTTP 状态码/响应体 JSON 形态与错误文案（属 entry-api handler）。
- 不决定存储介质/索引/缓存策略/SQL（属 repository-data）。
- 不决定配置项默认值与 env 前缀（属 config）。
- 不重复封装业务无关技术能力（如 bcrypt/HMAC 算法，调既有 Utility，且不入 `direct_dependencies[]`）。
````

## 3. 七类写作步骤（3.1~3.7）

每类共同骨架同上模板；以下只列类型要点与易错点（规则正文回各类 L2 / golden-path）。

### 3.1 biz（v1，按 `detail-type-biz.md`）
- **先行为后接口**：从承接的 `BHV-NNN` 推导 `<Domain>Service` 公开方法清单，再写 interface 签名（首参恒 `ctx context.Context`，末位恒 `error`）。
- **状态写 owner 是一等公民**：§5 必须声明本 biz 拥有写权的业务状态清单（唯一写 owner），同一状态出现在两个 service 合同里=P1，回概要重判归属。
- **错误 = sentinel 全集**：每个公开方法可能返回的 `var ErrXxx` 逐条列出，区分「业务可恢复（handler 据 `errors.Is` 分支）」与「系统不可恢复（`%w` 链式上抛）」。biz 自身不决定 HTTP 状态码。
- **依赖正反面 + 闭环**：允许 `<Entity>Repository`（`dep_kind=repo`）、单向下层 `<Other>Service`（`dep_kind=infra`，无环无双向）、基础设施边界（`dep_kind=infra`）、外部边界（`dep_kind=outbound`）；Utility 纯函数直接调用、**不入 `direct_dependencies[]`**。每条依赖回到 `direct_dependencies -> NewXxx 构造入参 -> 字段赋值 -> usage_refs` 闭环。禁止 `net/http` 物件、`*sql.DB`/`lib/pq`/原生 SQL 进 biz。
- **事务边界三分法**：每个写行为在 `无显式事务 / 本地数据库事务 / 一致性模式` 三选一给结论；禁止把单条写、只读校验、审计/metric/cache 副作用机械写成显式事务，禁止把 `DB + MQ/API` 塞进一个本地事务。
- 易错点：把"提供 XX 业务能力"当方法清单（无签名/无 ctx/无 error）；handler 物件入 biz；字符串比较错误代替 `errors.Is`；biz 内直连 DB。

### 3.2 entry-api（v1，按 `detail-type-entry-api.md`）
- 文档头**必标 `entry_kind`**（`http_endpoint`/`cli_command`/`scheduled_job`/`message_consumer`），决定契约主定义形态；外部回调/Webhook 入口归 `entry_kind=http_endpoint`，不归 external。
- **逐 route+method 各绑一个 `BHV-NNN`**，行为清单表含列 `BHV 编号 | route + method | handler 方法名 | 目标 service 方法 | 概要场景 id`；禁止「一个 handler 文件=一个行为」压缩多个真实 route。
- **输入五类来源分列**：`path / query / header / body / context` 逐字段给（字段路径/Go 类型/必填/来源/入口校验/空值策略/映射目标 service 入参）；`ctx context.Context` 必为透传载体（`svc.DoX(r.Context(), ...)`），禁止 `context.Background()` 顶替。
- **错误三态收口**：每行为给「入口校验失败 / service sentinel error / 兜底未知错误」三类到 HTTP 状态码 + 错误响应体的映射表；service sentinel 用 `errors.Is(err, service.ErrXxx)` 分类，未命中统一 500 + 记日志（含 trace id），不向客户端泄露内部细节。
- handler 无状态：只读请求入参与 ctx 中鉴权产物，不写任何业务状态。可穷举字段用 Go `iota`/字符串常量 + 显式 JSON 序列化口径，禁裸魔法值。
- 易错点：handler 直连 repository/DB（越层 P1）；吞 sentinel error（`_ = err`）；`err.Error()` 直接回客户端；handler 内做业务判定。

### 3.3 repository-data（v1，按 `detail-type-repository-data.md`）
- 合同从 domain 实体出发：Repo 接口（查询意图/过滤/排序稳定性/分页/事务）、表 DDL（签名级，不写迁移脚本正文）、字段字典、索引/约束、`sql.ErrNoRows` → domain/`repository.ErrNotFound` 转换点逐查询写明。
- 用 `Context` 版 API（`QueryContext`/`QueryRowContext`/`ExecContext`），`$1,$2` 参数化（永不字符串拼接 SQL），`rows` 必 `defer Close()` + 查 `rows.Err()`，写操作 0 行受影响也归 `ErrNotFound`。
- repository 不写业务校验、不返回 `ErrValidation`、不感知 HTTP。go-guru profile 命中时框架细节只放 `framework_reference_ref`。
- 易错点：裸抛 `sql.ErrNoRows`；忽略 `RowsAffected`；在 repository 写业务判定。

### 3.4 domain（pending，L1 八问 + `L2豁免`）
- 只给 struct/值对象/枚举/sentinel errors（`var ErrXxx = errors.New(...)`）定义 + JSON tag；可空字段 `*T` + `,omitempty`，必传值类型，需区分「未传/传零值」一律 `*T`。
- domain 是依赖叶子：**不写 `Validate()`（属 service）、不写 `Scan()`（属 repository）、不 import 任何 internal 兄弟包、无 I/O、无副作用**。
- 当前栈无 ORM tag（原生 SQL 手动扫描）；切 `ent`/`sqlc` 由 `[SLOT-02]` 决定，未切前不加 `db:` tag。
- 八问之 8 必列「不拥有校验/扫描/配置默认值」。

### 3.5 config（pending，L1 八问 + `L2豁免`）
- 配置项表（key / env 变量名 + 前缀如 `<SVC>_*` / 类型 / 默认值 / 来源 / 校验规则 / 消费方）；集中 `config.Load() (Config, error)`，`main()` 调一次经 `app.New(cfg)` 注入。
- 必填项缺失返回 error（交 `main()` `log.Fatalf`），可恢复默认用 `getEnv(key, fallback)`，启动期不可恢复配置解析失败 `panic`（`mustDuration`/`mustInt`/`mustBool`）。
- secret 只写 env 变量名/`credential_ref` 引用，**正文/yaml/测试 fixture 均不得出现明文 key/AK/SK/token/私钥**（出现即 P1）；业务规则默认值仍归 `biz`/`domain`，不在 config 拍板。

### 3.6 external（pending，L1 八问 + `L2豁免`）
- 逐外部系统：协议、请求/响应/错误 schema、鉴权边界、SLA/限流、超时重试、本系统 adapter 消费边界；只承载本系统**出站**调用外部系统的合同（入站回调归 entry-api）。
- 跨服务契约只落 `packages/contracts/`（`Desired*` 前缀，零行为零业务依赖），不在 `internal/` 私自定义跨服务 schema。
- WX-6 硬前置：provider/external owner、SDK/client、调用模式、runtime profile、credential strategy、异步生命周期、成本/限流/SLA 驱动来源必须均来自概要已落盘技术决策；缺一即回退概要、禁止本地补造。
- credential 只写引用方式，secret value 出现即 P1。

### 3.7 runtime（pending，L1 八问 + `L2豁免`）
- 展开 `main()→app.New()→app.Run()→app.Shutdown()` 生命周期、信号处理（SIGINT/SIGTERM）、连接池参数（`SetMaxOpenConns`/`SetMaxIdleConns`/`SetConnMaxLifetime`）、`*http.Server` timeout（Read/Write/Idle）、`db.Ping()` 失败收口、健康检查、发布/回滚边界。
- `http.ErrServerClosed` 视为正常退出（不 `Fatal`）；`Shutdown` 不漏关 db；handler 接 `r.Context()` 在 entry-api 证明，runtime 只负责根 ctx 与生命周期。
- 不写部署脚本、Dockerfile、CI 流水线、云控制台步骤、运维 Runbook 正文（属运维阶段）。

## 4. 批次收敛与 checkpoint 操作细则

- **写作顺序**（Go 分层自底向上，依赖 `transport → service → repository → domain`）：① domain → ② repository-data → ③ biz（同 feature 的 service 与其直接 repository 同批优先）→ ④ entry-api → ⑤ 横切（config/external/runtime）。owner 层只能是 `transport/service/repository/domain` 四者之一；归属错误回退概要，不就地改。
- **批内自动 review 检查单**（逐项打钩后才置 `chapter_status`，不等用户）：
  1. 模板节齐全（§2 模板 1~8，含 N/A 声明）；八问四机检标记齐全（承接行为/失败收口/测试映射/不得补造）。
  2. 八问逐 UNIT 可回指（L1 §3 括号内可验证信号）。
  3. 粒度抽查：任选一个行为，按 L1 §3.1 四条（可直接实现/明确调用关系/完整调用链/粒度一致）逐条判。
  4. 依赖出现在概要架构图/归属表中，且分层方向单向无环（§6.0 分层依赖律）。
  5. 错误范式：sentinel + `fmt.Errorf("%w: ...")` + `errors.Is`，无裸字符串错误/自定义错误码体系。
  6. L2 命中时逐条核对类型差异规则；技术决策只承接概要已确认输入。
- **层级 checkpoint**（L1 §5.4）操作：列出该层全部 UNIT → 跑对应核对项 → 失效项标注到章节 → 回批次修复。上一层级 checkpoint 通过前不开始下一层批次。
  - domain 层：实体/sentinel 唯一定义、无 I/O、无 internal 兄弟包导入；被引用实体均已定义。
  - repository-data 层：domain 实体均有表/Repo 合同；`sql.ErrNoRows`→sentinel 转换点一致；SQL 只在 repository。
  - biz 层：UNIT↔BHV 承接闭合；状态写 owner 唯一；service 间依赖单向无环；事务三分法有结论。
  - entry-api 层：handler 只调稳定 biz 行为、不直触 repository/SQL；context 透传；错误三态收口齐全。
- **受影响章节复查**：本批修改触及已完成章节引用时，复查该引用闭合；已通过章节被改动则通过状态失效，重新进入当前小批次写审修闭环。
- **修复闭环上限**：同一 finding 修 2 轮仍不收敛 → 按强制约束 11 升级用户，不得带病置 `passed`。

## 5. 禁止事项（写作期红线速查）

1. 一轮全量生成全部章节（每批 ≤3 章并完成批内审修后才进下一批）。
2. 越过签名级写实现代码/伪代码（方法签名、struct/type/interface 定义为上限；不写函数体、完整 SQL、迁移脚本正文、`wire.Build` 细节）。
3. 补造概要外结构、改 owner、拍板 `technology_decision_handoff[]` 未选定的决策或 project-conventions「待定」槽位。
4. 把"见概要"当八问答案（每问就地作答，可引用但须有本地结论；暂不能答写入「未决问题」而非留空或编造）。
5. 跳过失败路径的测试映射（每行为成功 + 全部失败路径各一条 unit test 行）。
6. 违反 golden-path 红线：引入 gin/echo 等重型框架替代 `net/http` ServeMux；反向/跨层/循环依赖；非 sentinel 错误体系；缺生命周期；明文 secret。
7. strict 模式代跑 `guru_gate.py confirm`（agent 不得代跑）；soft 模式未获用户本轮对话明确确认即代跑。
