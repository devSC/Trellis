# L2 类型规范：biz（业务流程 / service 层）

> 从属于 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；本文件只写 biz 类型相对通用骨架的差异规则与 Go 硬约束，不复述合同八问的完整定义。
> golden-path 对应：`.trellis/spec/guides/golden-path.md` §2.1 分层依赖律、§3 Domain（service）迷你路径、§2.5 边界与禁止清单、错误处理范式（sentinel + `%w` 包装 + `errors.Is`）。
> 层级契约：冲突时 L1 > 本文（L2）> golden-path 引用注解 > project-conventions 槽位取值。
> 装载后路径：通用方法真源在 `.trellis/spec/guides/golden-path.md`，流程骨架在 `.trellis/spec/harness/*`，项目槽位取值在 `.trellis/spec/conventions/project-conventions.md`。

## 适用对象

业务规则与业务状态的 owner，落在 `services/<svc>/internal/service/`。一个 biz 单元 = 一个 `<Domain>Service` 接口及其实现，封装"为完成某业务目标所需的规则判定、状态转移、事务/一致性收口与下层编排"。

**适用**：

- 业务规则封装（校验、判定、计算、聚合、终态推进）。
- 业务状态读写与终态收口（谁是某状态的唯一写 owner）。
- 跨 repository / 下层 service / outbound 的业务编排。
- 事务/一致性边界的业务决策（决定边界，不等于在 biz 里写 SQL/驱动）。

**不适用（命中即归错层，回退概要重判归属）**：

- 用户入口协议解析（HTTP 路由、请求解码、状态码映射、cookie 读写）→ 归 `transport/http` handler（entry-api-behavior 类型）。
- 数据访问实现（建表、SQL、`lib/pq` 调用、行→结构体映射、缓存介质）→ 归 `repository` 类型。
- 业务无关的纯函数技术能力（HMAC-SHA256 计算、bcrypt 哈希、token 编解码、时间/随机数封装）→ 归 Utility；biz 只调用，不重复封装，且 Utility 调用不进 `direct_dependencies[]`。
- 实体表结构、DDL、索引、protobuf Entity 主定义 → 归 `domain` / Data 类型。

## 合同八问的类型特化

> 编号纪律：承接行为引用 prd 标题里的裸 `BHV-NNN` token；设计单元以 `### UNIT-<slug>` 定义（kebab-case），下游测试与实现切片只引用 `UNIT-<slug>` 与 `BHV-NNN` 裸 token。

1. **承接哪些行为**：逐条引用 `BHV-NNN`（必须存在于 prd，否则 gate 断链拦截）。每条业务行为映射到 `<Domain>Service` 接口上一个公开方法。biz 是业务厚层，承接"业务规则 + 状态变化"类行为；纯展示/纯入口协议行为不在此承接。承接 P0/P1 核心能力时，必须把概要的 `难点焦点 / 复杂度来源 / 设计焦点 / 展开粒度 / 架构响应` 拆成可直接编码的步骤，不得只写"处理 XX 能力"。

2. **输入 / 输出 / 错误结果**：
   - **接口全集逐方法签名级**列出 Go 方法签名（方法名 / 参数类型 / 返回类型），首参数恒为 `ctx context.Context`，返回值末位恒为 `error`（`func (s *userService) Register(ctx context.Context, in RegisterInput) (*User, error)`）。输入/输出各给参数表（参数 / 类型 / 取值域·约束 / 必填）。
   - **错误 = 服务级 sentinel errors 全集**：每个公开方法可能返回的 `var ErrXxx = errors.New("...")` 逐条列出，并区分"业务可恢复（调用方可据 `errors.Is` 分支处置）"与"系统不可恢复（链式包装上抛）"。错误必须可被 handler 用 `errors.Is(err, service.ErrXxx)` 判定后映射协议层语义；biz 自身不决定 HTTP 状态码。

3. **读取 / 写入哪些状态**：明确读写分离。列出本 biz 拥有写权的业务状态清单（**唯一写 owner**：同一业务状态出现在两个 service 的合同里 = P1，回概要重判归属）。状态的物理存储介质属 repository 合同——biz 只声明"我是 `user.status` 终态推进的唯一 owner"，不声明它落在哪张表/哪个缓存。对调用方只读暴露的状态经返回值/查询方法给出。

4. **调用哪些依赖，不调用哪些依赖**（正反两面都写，防越层）：
   - **允许调用**：注入的 `<Entity>Repository` 接口（`dep_kind=repo`）；**下层** `<OtherDomain>Service` 接口（`dep_kind=infra`/biz，**严格单向、构造注入接口、无环无双向**——见类型硬规则）；基础设施边界（缓存/消息/审计接口，`dep_kind=infra`）；外部既有边界（`dep_kind=outbound`）；概要已抽取的 Utility 纯函数（直接调用，不入依赖清单）。
   - **禁止调用**：`transport/http` handler 或任何 entry 组件（反向依赖）；除 `domain` 外其它服务的 `internal/` 包（违反 internal 隐私约定）；`net/http` 的 `Request`/`ResponseWriter`/`http.Error`（协议物件不得进 biz）；具体 `*sql.DB`、`lib/pq`、原生 SQL（数据访问实现属 repository）；重型 Web 框架（gin/echo 等，golden-path 锁定禁用）。
   - 每条 `direct_dependencies[]` 条目必须能回到概要架构图/归属表的边，并形成 `direct_dependencies -> NewXxx 构造入参 -> 字段赋值 -> usage_refs` 闭环。

5. **失败如何收口**：每个公开方法逐条失败路径给处置语义（返回业务 sentinel / 链式包装系统错误上抛 / 降级 / 重试），并标错误转换位置（`[SLOT-13]`：下层错误在进入 biz 时若改变业务语义则在此转换，否则用 `fmt.Errorf("%w: ...", err)` 保链上抛）。异常表逐行必须对应一条失败路径 `BHV` 或八问 1 的行为分支。写状态/可重放行为必须给幂等键、作用域、重复调用语义与冲突收口；纯校验/纯计算行为可写"幂等 = 无 / 事务 = 无 / 副作用 = 无"，但必须显式说明。

6. **产生哪些事件 / 后置结果**：状态终态推进、审计/metric 副作用、消息发布、跨 service 通知，逐条写明触发时机与消费方。`什么操作成功后哪些后置结果必然发生`要可定位（如"`Register` 成功后必然写入审计事件 `user.registered`，消费方：审计 service"）。

7. **哪些测试验证它**：biz 是测试密度最高的层。业务规则与状态转移 = unit test（mock repository / 下层 service 接口，`testing` 标准库 + project-conventions 选定的断言库如 testify）；事务/一致性边界与幂等 = unit test（重复调用断言）；错误语义 = unit test（断言 `errors.Is(got, ErrXxx)`）。**每条承接行为至少 1 成功用例 + 全部失败路径各 1 用例**；逐行映射到 `BHV-NNN`/`UNIT-<slug>`。

8. **哪些内容不得在此补造**：不决定 HTTP 状态码/响应体 JSON 形态与错误文案（属 handler）；不决定存储介质/索引/缓存策略/SQL（属 repository / Data）；不决定配置项默认值与 env 前缀（属 config，biz 只消费 `config.Load()` 注入的值）；不重复封装 Utility 已提供的业务无关技术能力；不在未确认的业务规则上拍板（列入未决问题回需求/概要，不在详细阶段就地改归属）。

## 类型硬规则（Go golden-path 锁定，不可豁免）

- **分层依赖律单向**：`handler(transport) → service → repository → domain`，严格单向、无循环。biz 只能向下依赖 repository/下层 service/domain，**绝不**被 handler 反向依赖之外的方式调用，也不得跨服务导入除 `domain` 外的 `internal/` 包。
- **service → service 单向**：允许上层 biz 构造注入下层 biz 接口，但必须单向、无环、无双向。同一业务状态被两个 service 写 = P1；出现 A↔B 互调倾向 → 回退概要抽更高层编排 service 或把共享逻辑下沉到下层 service/repository。
- **接口与实现分离 + 依赖注入**：公开形态是接口（`type UserService interface { ... }`），实现是私有结构体（`type userService struct { repo UserRepository; ... }`）；唯一构造入口 `func NewUserService(repo UserRepository, ...) UserService`，依赖只经构造函数注入（DI 框架槽位见 project-conventions，当前无 → 手写 `New*`，可选 wire）。禁止在方法内 `new`/全局单例硬取依赖。
- **错误处理范式**：服务级 sentinel `var ErrXxx = errors.New("...")` 集中声明；包装下层错误用 `fmt.Errorf("%w: 业务上下文", err)` 保留错误链；调用方/handler 用 `errors.Is(err, ErrXxx)` 判定。禁止用字符串比较错误、禁止吞错（除非显式降级并说明）。
- **context 贯穿**：每个公开方法首参 `ctx context.Context`，支持 timeout/cancel，并透传到 repository 调用；biz 不自行 `context.Background()` 覆盖入参 ctx（后台触发场景由 entry 决定根 ctx）。
- **轻量框架约束**：biz 不感知 `net/http`/重型框架；任何协议物件（`http.Request`/`http.ResponseWriter`/status code/header/cookie）都不得出现在 biz 签名或正文。HMAC-SHA256 签名 cookie、bcrypt 等会话/鉴权技术细节中，业务判定（"该用户是否可登录""会话是否过期需续期"）留在 biz，纯算法（签名计算、哈希）调 Utility。
- **数据访问抽象**：biz 通过语义化 `<Entity>Repository` 接口访问数据，正文不出现原生 SQL/`lib/pq`/`*sql.DB`；go-guru profile 命中时框架细节只写 `framework_reference_ref`，不在正文展开 Repo 生成方法表/`PropertyFilter`/`WithTx`。
- **事务边界三分法**：每个写行为在 `无显式事务 / 本地数据库事务 / 一致性模式` 三选一给结论；禁止把单条写、只读校验、审计/metric/cache 副作用机械写成显式事务，禁止把 `DB + MQ/API` 硬塞进一个本地事务边界。
- **internal 隐私 + contracts 边界**：跨服务复用的契约放 `packages/contracts/`，biz 不导入别的服务的 `internal/`。

## 好 / 坏例子

✅ **好（方法签名级 + sentinel + 单向依赖 + 状态 owner + 测试映射）**

- 接口：`type UserService interface { Register(ctx context.Context, in RegisterInput) (*domain.User, error); Login(ctx context.Context, in LoginInput) (*domain.Session, error) }`（每个方法首 `ctx`、末 `error`，签名级完整）。
- 错误全集：`var ErrEmailTaken = errors.New("email already registered")`（业务可恢复，handler 映射 409）；`var ErrInvalidCredential = errors.New("invalid credential")`（业务可恢复，映射 401）；底层故障 `return nil, fmt.Errorf("persist user: %w", err)`（系统不可恢复，链式上抛）。
- 依赖声明："构造注入 `UserRepository`（`dep_kind=repo`）与下层 `AuditService`（`dep_kind=infra`，单向）；不注入任何其它 service 反向依赖；不导入 `net/http`；bcrypt 哈希调 `passwordutil.Hash(plain)`（Utility，不入 `direct_dependencies[]`）"。
- 状态 owner："`user.status` 终态推进（pending→active→disabled）的唯一写 owner = `UserService`"。
- 失败收口：`Register` 流程——① 调 `repo.FindByEmail(ctx, email)`，命中 → `return nil, ErrEmailTaken`（业务收口，无副作用）；② `passwordutil.Hash` 调 Utility；③ `repo.Create(ctx, u)` 失败 → `fmt.Errorf("persist user: %w", err)` 上抛；④ 成功后发布 `user.registered` 审计事件。事务边界：单条写 → `无显式事务`。
- 测试映射：`BHV-012` → unit test：成功注册（mock repo 返回 not-found + create 成功）；`errors.Is(err, ErrEmailTaken)`（mock repo 命中）；persist 失败链路（mock repo Create 返回错误，断言 `%w` 链）。

❌ **坏（命中即 P1/P2）**

- 方法清单写"提供用户相关业务能力"，无 Go 签名、无 `ctx`/`error`（违反八问 2 + context 硬规则）。
- 方法签名出现 `func (s *userService) Register(w http.ResponseWriter, r *http.Request)`（协议物件入 biz，越层到 handler 职责）。
- 错误用 `if err.Error() == "email taken"` 字符串比较，或方法直接 `http.Error(w, ..., 409)`（违反 sentinel + `errors.Is` 范式，且 biz 决定了状态码）。
- biz 内直接 `db.Query("SELECT ...")` 或导入 `lib/pq`（数据访问实现下沉失败，越层到 repository）。
- `UserService` 与 `OrderService` 互相注入并都写 `user.balance`（双向依赖 + 状态双写，回概要重划）。
- 把 bcrypt/HMAC 算法在 biz 内重新实现一遍而不调既有 Utility（重复封装业务无关技术能力）。
- 把单条 `Create` 包进 `BEGIN/COMMIT` 显式事务、或把"写库 + 发 MQ"塞进一个本地事务边界（事务边界误判）。

## 不适用场景（明确归错层处理）

| 看似 biz、实际归属 | 正确 owner 类型 | 判据 |
| --- | --- | --- |
| 请求解码 / 状态码映射 / cookie 读写 | entry-api-behavior（handler） | 触碰入口协议物件 |
| SQL / 行映射 / 缓存介质 / 索引 | repository / Data | 数据访问实现细节 |
| HMAC-SHA256 计算 / bcrypt 哈希 / token 编解码（无业务判定） | Utility | 业务无关纯函数 |
| env 前缀 / 默认值 / `config.Load()` | config-runtime-contract | 配置取值 owner |
| 表结构 / DDL / Entity protobuf 主定义 | domain / Data | 实体主语义 |

## Gate 判定（结构检查可通过的最小条件）

承接此类型的章节文件（full 链 `chapters/<slug>.md`，light 链 `design.md §2` 对应章）按 L1 §4 骨架撰写，并满足：

- **需求五要素 / 承接**：每个 `### UNIT-<slug>` 都逐条引用存在于 prd 的 `BHV-NNN`；无幽灵引用、无无承接单元（否则 G1/断链 P1）。
- **概要归属 + 承接索引**：单元出现在概要归属表与第 6 章 `chapter_target → detail_doc_type=biz` 承接索引中，双向闭合；写 owner 与概要一致。
- **合同八问完整**：上列八问逐问有实质内容（含错误 sentinel 全集、依赖正反面、失败收口逐路径、不得补造清单），缺一为 P1。
- **粒度（L1 §3.1）**：行为步骤可直接编码——指明调用的具体下层方法与参数、本单元内部判定、错误返回与状态写入点；同文档粒度一致。
- **实现 trace 四节对齐**：go-guru profile 命中时正文只放 `framework_reference_ref`，生成命令/`retrieve_trace_id`/`pack_id`/`source_uri` 延后到 `implementation-trace.md`；MCP 不可用写 `status=blocked_by_knowledge_unavailable`。
- **测试映射**：每条行为成功 + 全部失败路径各有 unit test 行，引用 `BHV-NNN`/`UNIT-<slug>`。

判级口径沿用 L1 §8：违反本文硬规则、八问缺项、追溯断链、状态双写、越层依赖 = P1（阻塞）；错误枚举不全、粒度局部不达标、事务三分法缺结论 = P2；表述建议 = P3。
