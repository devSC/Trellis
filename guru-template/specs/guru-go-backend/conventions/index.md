# conventions/ 索引（Guru Go 后端）

> 项目约定槽位的入口。本文件只做导航与边界声明，**不承载任何槽位取值正文**；取值正文只许落在 `project-conventions.md`。
> 适用平台：Guru 多平台 Harness 的 Go monorepo 后端（服务形态 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}` + `cmd/<svc>/main.go` 单一入口）。

## 1. 三类文件的职责分工（导航）

本目录用三类文件把"方法/团队栈级 canonical"与"项目级取值"彻底分离。三者不可互相替代：

| 文件 | 职责 | 状态 |
|------|------|------|
| [project-conventions.template.md](./project-conventions.template.md) | **槽位定义**：配置包给出的空槽位模板（每个槽位的决策问题、生效范围、与硬规则的边界）。是"要钉死哪些项"的唯一定义来源；不含任何具体取值。 | 配置包内固定，随 `trellis update` 演进 |
| `project-conventions.md` | **本项目取值的唯一权威**：按模板逐槽位填写本仓库的真实取值 + 代码证据 + 生效范围，含校验清单 C1~C6 与 SLOT-17 存量违例清单。所有 writing/review skill 与 Gate 的硬前置**只认此文件**。 | 缺失时按模板/样例建立并填写；init 后由模板复制填写 |
| [safa-land.project-conventions.md](./safa-land.project-conventions.md) | **样例取值**：safa-land Go monorepo 实测扫描的填写样例（control-api 等服务）。仅供参考对照填写深度，**不直接生效、不参与任何校验**。 | 只读参考 |

规则：硬前置与 Gate 只装载 `project-conventions.md`；模板与样例文件均不参与校验。修改任何槽位取值属于服务级架构决策，须 ADR 记录后方可生效。

## 2. 装载路径（安装后）

writing/review skill 与 Gate 在硬前置中按下列**安装后路径**装载（不要引用 guru-template 开发期路径）：

- 项目约定取值：`.trellis/spec/harness/conventions/project-conventions.md`（本目录安装落位；缺失即停，先完成项目约定）。
- 通用方法 SSOT（分层依赖律、各层迷你路径、禁止清单、门禁映射）：`.trellis/spec/guides/golden-path.md`。
- 五阶段方法 SSOT（概要/详细/实现合同）：`.trellis/spec/harness/index.md` 及其下 `overview/`、`detail/`、`implementation/`。

装载顺序（每个任务开工前）：先读 `project-conventions.md` 过 C1~C6 → 读 `golden-path.md` 锁硬规则 → 按当前阶段读对应 harness SSOT，并把所读文件登记进任务 `implement.jsonl` / `check.jsonl`（带 reason）。

## 3. Go 平台硬规则回顾（golden-path 锁定，槽位不可豁免）

下列规则属团队栈级 canonical，**任何槽位取值不得与之冲突**（C4 校验该约束）。完整正文见 `golden-path.md`，此处只回顾以便填表时对照：

- **框架轻量**：HTTP 入口一律 `net/http` 的 `ServeMux`；禁用 gin/echo/fiber 等重型 Web 框架（中间件用标准 `http.Handler` 装饰链表达）。
- **分层依赖律（严格单向、无环）**：`transport(handler) → service → repository → domain`。除 `domain` 可被各层共享外，禁止跨 `internal/` 包反向或横向导入；`service` 不得 import `transport`，`repository` 不得 import `service`。
- **错误处理三件套**：每个服务级包定义 sentinel errors（`var ErrXxx = errors.New(...)`）；跨层传播用 `fmt.Errorf("%w: ...", ErrXxx)` 链式包装；判定一律 `errors.Is()` / `errors.As()`，禁止字符串比对错误信息。
- **启动/关闭生命周期**：`main()` 只接信号（`signal.NotifyContext`）→ `app.New(cfg)` → `app.Run(ctx)` → `app.Shutdown(ctx)`；每个 Handler 接收 `context.Context` 并尊重 `ctx.Done()` / timeout。
- **配置集中**：环境变量 + 默认值，统一在 `config.Load()` 装配；env 前缀按服务隔离（如 `CONTROL_API_*`），禁止在业务代码里散读 `os.Getenv`。
- **包可见性约定**：服务私有代码进 `internal/`（编译期隔离）；跨服务共享契约进 `packages/contracts/`，且只放纯数据契约（不放业务逻辑）。

这些规则在槽位里只能"具体化落点"（如选哪个 DB 驱动、用 slog 还是标准 log），**不能反转方向或绕过**。

## 4. Go 平台槽位地图（定义在 template，取值在 project-conventions）

下表是 Go 后端槽位的导航视图（决策问题 + 谁消费），帮助填表人定位；**完整决策问题与边界以 template 为准，本项目取值以 project-conventions.md 为准**。槽位允许按服务调整（同一 monorepo 内不同服务可有不同取值，但单个服务内新代码必须唯一）。

| 槽位 | 决策问题（要钉死什么） | 谁消费 |
|------|------------------------|--------|
| SLOT-01 DI 框架 | 手工构造（当前 safa-land 无 DI 框架，`app.New()` 内手工 wire）还是引入 `google/wire`？注入边界在 `app` 层。 | runtime、implementation-review |
| SLOT-02 ORM / 数据访问层 | ORM/查询层：原生 `database/sql` + `lib/pq` + PostgreSQL（当前）还是 `ent` / `sqlc`？查询写法与行映射方式（迁移工具与 `db/migrations/` 组织见 SLOT-12）。 | repository-data、repository 合同 |
| SLOT-03 日志方案 | 标准 `log`（当前）还是 `slog` / `zap`？logger 注入路径、结构化字段约定、请求链路 ID 传递。 | implementation-writing、implementation-review |
| SLOT-04 测试框架 | 标准 `testing`（当前）还是 `testify` / `ginkgo`？表驱动测试约定、mock 生成方式、集成测试是否连真实 DB。 | detail 合同测试映射、implement Gate |
| SLOT-05 API 风格 | REST + JSON（当前 `net/http` 手写 JSON 编解码）还是 gRPC？路由注册位置（`transport/http/router.go`）、版本前缀、统一错误体形态。 | entry-api、overview 承接索引 |
| SLOT-06 DB 驱动 / 连接形态 | 驱动包（`lib/pq` / `pgx`）、连接池参数、`*sql.DB` 注入位置、驱动 import 落点（仅 repository/app）。 | config.Load 取值、repository 合同 |
| SLOT-07 lint / 静态检查 | `golangci-lint` 配置文件路径与启用的 linters 集合、`go vet` / `gofmt` 在 Makefile 的目标名、CI 触发。 | implement Gate 证据节 |
| SLOT-08 配置加载 | `config.Load()` 文件路径、env 前缀（如 `CONTROL_API_*`）、默认值来源、必填项校验失败行为（fail-fast）。 | config 合同、启动序列检查 |
| SLOT-09 文档生成 | OpenAPI/Swagger 是否启用（当前无）、契约文档来源（手写 / 注解生成 / `packages/contracts/`）。 | overview 承接索引、API 契约 review |
| SLOT-10 会话 / 鉴权 | 当前自实现：HMAC-SHA256 签名 cookie + bcrypt 口令哈希，落在 `internal/auth`。是否迁移到标准库/第三方？签名密钥来源、cookie 属性。 | entry-api、合规红线 review |
| SLOT-11 包组织 / 分层目录 | 服务内部包划分（标准分层 vs 按领域聚合）、跨服务共享代码落点（`packages/contracts/` 的命名与版本策略，如 `proxy_node_config.go`）。 | overview 归属、跨服务依赖 review |
| SLOT-12 数据库迁移 | 迁移工具（`golang-migrate` / `goose` / `ent`）、`db/migrations/` 目录与 `NNNN_*.up.sql`/`.down.sql` 命名、版本号规则、触发时机。 | repository-data、db-migration 合同、迁移检查 hooks |
| SLOT-13 错误处理风格 | 服务级 sentinel errors 声明在哪个包（domain 还是 service）、跨层 `%w` 包装/裸 sentinel 风格、HTTP 状态码映射表落点（transport 层 errors→status）。 | detail 失败收口、implementation-review |
| SLOT-14 启动 / 关闭与超时 | `main()` 控信号 → `app.New/Run/Shutdown` 生命周期的超时数值、shutdown 宽限期、超时值是否来自 config。 | runtime、启动序列检查、implementation-review |
| SLOT-15 接口抽象 / DIP 策略 | 层间依赖抽象：消费方本地最小接口（`xxxStore`）、被依赖方导出大接口，还是 service 直接持具体类型？接口命名风格。 | biz/repository 详细合同、implementation-review |
| SLOT-16 可穷举字段（枚举）表达 | status/role/protocol/mode 等用 Go `iota`/具名常量枚举还是裸 `string`？非法值收口层（service `switch` / DB `CHECK`）。 | entry-api/domain 详细合同、枚举 owner review |
| SLOT-17 存量违例清单（tech-debt 登记） | 已知存量架构违例逐条登记（违例描述 + 文件路径 + 关联槽位/硬规则），供 review 的存量豁免判定使用。 | 所有 review 的存量豁免判定 |

> 待定槽位规则：取值可为"待定"，但必须写明决策人与期限，且待定总数 ≤ 2，否则项目约定视为未就绪（硬前置 C2 不通过）。

## 5. 校验清单（writing/review 硬前置使用，对应 project-conventions §2）

装载 `project-conventions.md` 的 skill 必须先执行以下校验，任一不通过即终止并提示修复：

- **C1** 元信息齐全（服务/模块名、`go.mod` module path、仓库路径、填写日期/填写人四字段）。
- **C2** SLOT-01 ~ SLOT-17 全部存在；"待定"槽位 ≤ 2 且均写明决策人与期限。
- **C3** 每个已填槽位至少 1 条代码证据路径（路径须真实存在于仓库，如 `services/control-api/internal/transport/http/router.go`）。
- **C4** 取值不得与第 3 节硬规则冲突（分层依赖律方向、轻量框架、错误三件套、启动序列、`internal/` 隔离、契约入 `packages/contracts/`——均不可被槽位豁免）。
- **C5** SLOT-17 存量违例清单存在（可为空，但必须显式声明"无"）。
- **C6** 同一 monorepo 内若多服务取值不同，须在 §0 元信息标注"取值粒度=按服务"并逐服务给证据；否则默认取值对全 monorepo 生效。

## 6. 与 Gate 的兼容关系（guru_gate.py 结构检查口径）

本目录只产"项目约定"，不直接产五阶段产物；但它定义的取值会被下游五阶段产物引用，因此填写时须保证结构兼容 `guru_gate.py` 的结构底线：

- **需求 Gate（五要素）**：prd.md 需含行为编号（`### BHV-NNN <短名>`）、Given/When/Then 行为规格、P0/P1 优先级、失败路径、验收场景、未决问题六项。约定层的产出（如 SLOT-10 鉴权口径）会成为某些 BHV 的前置条件，但**约定文件本身不写 BHV**。
- **概要 Gate（归属表 + 承接索引）**：概要产物的行为→owner 归属表逐条引用 BHV 编号 + 三问理由（为什么属于它/不属于别人/是否需独立存在），并给"承接索引"（`chapter_target → doc_type`）。Go 的 `doc_type` 取值集合见 harness（如 `transport` / `service` / `repository` / `domain` / `app` / `config` / `auth` / `api-network` / `db-migration`）。
- **详细 Gate（合同八问）**：每个设计单元以 `### UNIT-<slug>` 标题定义，合同须显式覆盖：承接行为、输入/输出/错误、读写状态、依赖（遵守分层律）、失败收口（错误如何 `%w` 包装与 `errors.Is` 判定）、事件/后置、测试映射（哪些测试）、不得补造声明。约定槽位以裸编号 token 形式被引用（如"错误转换位置遵循 SLOT-13"）。
- **实现 Gate（trace 四节）**：implement.md 须含计划（切片挂 `UNIT-<slug>`）、执行（改动文件 + 代码生成记录，如跑 `sqlc generate` 按 SLOT-02）、证据（`go vet` / `golangci-lint` / `go test` 命令与结果，按 SLOT-07 / SLOT-04）、阻塞与偏差（触碰的 SLOT-17 条目编号 + 处置）四节。

**编号纪律**：行为用 `BHV-NNN`（prd 标题定义，不复用不重排，删除留洞）；设计单元用 `UNIT-<slug>`（详细设计标题定义，语义 slug）；下游引用一律写裸编号 token。约定文件引用槽位时同样写裸 token（`SLOT-NN`），不加链接包裹以便机器解析。

## 7. 好 / 坏例子（填写质量基线）

填 `project-conventions.md` 时按下列基线把握取值的"可验证性"：

- ✅ 好（SLOT-02 数据访问）：「原生 `database/sql` + `lib/pq`，PostgreSQL；query 方法集中在 `services/control-api/internal/repository/user_repository.go`，迁移 SQL 在 `db/migrations/NNNN_*.up.sql` / `.down.sql` 成对；连接由 `app.New()` 注入，repository 只持有 `*sql.DB`。证据：`db/migrations/`、`user_repository.go:NN`。」——取值具体、有落点、有证据、不与硬规则冲突。
- ❌ 坏：「用 PostgreSQL 做存储」——无驱动、无迁移组织、无证据路径，C3 不通过；且未说明 repository 是否直连 SQL，留下分层律盲区。
- ✅ 好（SLOT-13 错误处理风格）：「sentinel errors 定义在 `internal/domain`（如 `ErrUserNotFound`）；`service` 层 `fmt.Errorf("%w: load user", ErrUserNotFound)` 包装；`transport/http` 层有 `errors→httpStatus` 映射表（`ErrUserNotFound→404`、`ErrInvalidCredential→401`）。证据：`domain/user.go`、`transport/http/router.go`。」
- ❌ 坏（C4 冲突）：「为省事在 `repository` 层直接写 HTTP 状态码并返回 `*http.Response`」——repository 反向依赖 transport 关注点，违反分层依赖律，C4 直接拦截，不得作为合法取值登记。

## 8. 不适用场景（本目录不解决的问题）

- **不写五阶段产物**：BHV/UNIT、概要归属表、详细合同、implement trace 一律在任务目录或设计包内产出，不在 conventions/。
- **不复写硬规则正文**：分层依赖律、错误三件套、启动序列等正文在 `golden-path.md`；本目录只回顾与对照，避免双真源漂移。
- **不替代 ADR**：槽位取值变更的决策记录走 ADR；conventions/ 只承载"当前生效取值 + 证据"，不承载决策推导过程。
- **不裁决跨平台差异**：Flutter / iOS / Android 等其它平台的约定各自有 `guru-<platform>/conventions/`，本目录只管 Go 后端。
- **不做语义评审**："取值是否合理"由对应 review skill 的人工 Gate 判定；本目录的校验（C1~C6）只查结构存在性与硬规则不冲突，"判不动的规则不进校验"。
