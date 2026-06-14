# Harness — Go 后端五阶段方法 SSOT 入口

> 本文是 Go monorepo 后端（safa-land 形态：`net/http` + 严格分层 + 原生 SQL）五阶段方法的唯一权威入口。
> 阶段子 SSOT 承载规则正文，本文只做编排、装载顺序、Gate 口径与编号纪律的统一索引；冲突时以阶段子 SSOT 为准、本文为辅。
> 横向硬依赖：通用方法 `.trellis/spec/guides/golden-path.md`（分层依赖律与禁止清单）+ 目标仓库 `.trellis/spec/conventions/project-conventions.md`（项目约定槽位）。
> 项目实际按层模式见 `.trellis/spec/<layer>/`（by-layer 项目 spec，`backend/`、`shared/`，bootstrap 填实）；本 harness 只承载方法学，不写项目实例。

## Pre-Development Checklist（每个任务开始前）

执行任何阶段写作/编码前，依次确认；任一未过即停止，先补前置再开工：

- [ ] 读 `.trellis/spec/conventions/project-conventions.md` 并通过其内置校验清单 C1~C5（DI/ORM/日志/测试框架/API 风格/DB 驱动/lint/文档生成/会话鉴权等槽位缺失或未填 → 停止，先定槽位）。
- [ ] 读 `.trellis/spec/guides/golden-path.md`：确认本任务不触碰锁定红线（`net/http ServeMux` 唯一框架、分层单向依赖、sentinel + `%w` + `errors.Is`、`app.New/Run/Shutdown` 生命周期、`config.Load()` 集中配置、`internal/` 隐私约定、`packages/contracts/` 放跨服务契约）。
- [ ] 确定服务边界：本任务落在哪个 `services/<svc>/`，复用还是新建 `internal/{app,config,transport,service,repository,domain,auth}` 包；跨服务数据结构是否需进 `packages/contracts/`。
- [ ] 按本任务所处阶段读对应阶段 SSOT（下表「装载」列），并把所读文件登记进任务的 `implement.jsonl` / `check.jsonl`（带 reason，便于追溯读了哪条规则）。
- [ ] 判轨：读 task.json `guru_chain`（`guru_after_create` 创建默认 `full`）。full=完整五阶段链（新服务、新协议端点、鉴权/会话、迁移、跨服务契约变更等高风险需求），走目录级设计包；light=轻量链（同包内小迭代且获用户同意降级），产物为任务内单文件。
- [ ] 产物语言：中文优先。正文一律中文，英文仅限代码标识符、命令、路径、协议字段（如 `application_account_id`）、框架/库名（`net/http`、`lib/pq`）、缩写（HMAC-SHA256）与原文引用。

## 阶段 → SSOT 映射

**双轨制**：下表「产物」列写作 `full / light`。full 链需求走正式需求包、设计走目录级设计包（task.json `design_package` 字段，相对 repo root，如 `docs/design/<feature>/`）；light 链产物收敛为任务内单文件 `design.md`。`guru_gate.py` 按链型自动切换检查口径。

| 阶段 | 产物（full / light） | 装载 |
|------|------|------|
| 需求 | 正式需求包（requirement-writing 撰写 + requirement-review 门禁）+ `prd.md` 行为规格抽取 / 仅 `prd.md` | guru-ai-guides `requirement-writing`、`requirement-review` skill 及其标准包 `requirement-doc-standard`（**硬前置：未安装即停**）；jsonl 引用安装路径 |
| 概要设计 | `design_package/design-main.md` / `design.md` §概要 | [overview/overview-structure-single-source.md](./overview/overview-structure-single-source.md)（行为枚举 → 分层归属判定 → 承接索引 → 架构总览人审视图） |
| 详细设计 | `design_package/chapters/*.md`（逐章）/ `design.md` §详细 | [detail/detail-structure-single-source.md](./detail/detail-structure-single-source.md) + 涉及类型的 [detail-type-entry-api](./detail/detail-type-entry-api.md) / [detail-type-biz](./detail/detail-type-biz.md) / [detail-type-repository-data](./detail/detail-type-repository-data.md)（其余类型 doc_type 为 pending：full 链须显式 `L2豁免` 或先补 L2，light 链按 L1 合同八问展开并标注 `l2_status: pending`） |
| 实现 | 代码 + `implement.md`（trace） | golden-path + [implementation/implementation-trace-contract.md](./implementation/implementation-trace-contract.md) |
| 审核/复盘 | findings + spec 回写 | 各阶段 SSOT 审核基线章节 + [extraction-template.md](./extraction-template.md) |

### Go 后端的 doc_type 七类（详细阶段承接索引取值）

详细设计承接索引 `chapter_target → detail_doc_type` 的 doc_type 取下表之一；L2 状态标注当前是否已提供类型差异文件（pending 类型须 `L2豁免` 或先补 L2）：

| doc_type | 覆盖对象（Go monorepo 形态） | 证据锚点 | L2 状态 |
|----------|------------------------------|----------|---------|
| `entry-api` | `internal/transport/http` handler 入口：路由注册、`ServeMux` 模式、请求解析、JSON 编解码、状态码映射、`context` 超时透传；CLI 子命令/定时任务/消息消费归其 entry_kind 子类 | `transport/http/router.go` | **v1 提供** |
| `biz` | `internal/service` 业务核心与状态/能力 owner：业务编排、入参校验、sentinel error 定义与 `%w` 包装、跨 repository 协调 | `service/user_service.go`、`service/errors.go` | **v1 提供** |
| `repository-data` | `internal/repository` 数据访问合同（原生 SQL `lib/pq`、行映射、`ErrNotFound` 转换）+ `db/migrations` canonical 表/迁移（`NNNN_*.up.sql` / `.down.sql` 表定义、索引、版本迁移） | `repository/user_repository.go`、`repository/errors.go`、`db/migrations/0001_initial_schema.up.sql` | **v1 提供** |
| `domain` | `internal/domain` 实体/值对象/sentinel errors/不变量、参数结构体（`CreateUserParams` 等）、序列化 tag（唯一允许被跨层导入） | `domain/user.go` | pending |
| `config` | `internal/config` + `config.Load` + env 前缀（`CONTROL_API_*`）+ secret 引用：环境变量装载、默认值、校验；鉴权会话合同 auth 亦在此或 `biz` | `config/config.go`、`auth/session_manager.go` | pending |
| `external` | 外部系统/第三方 API/对象存储/模型服务集成合同；跨服务技术封装 contracts（`packages/contracts/` 跨服务契约结构体如 `DesiredNodeConfig`、JSON 字段冻结）归此或 `domain` | `packages/contracts/proxy_node_config.go` | pending |
| `runtime` | 进程拓扑 + `app.New`/`Run`/`Shutdown` 生命周期 + 信号 + 健康检查 + 发布回滚：`internal/app` 装配、依赖注入接线、连接池参数（`app-lifecycle` 归此） | `app/app.go`、`cmd/<svc>/main.go` | pending |

> doc_type 与 detail-structure-single-source.md §2 同步维护。`guru_gate.py` 用七类 token 识别承接索引命中的类型，命中 pending 类型且无 `L2豁免：<doc_type> 理由：…` 即拦截详细 Gate。

## 编号纪律（BHV / UNIT）

机器追溯（`guru_gate.py trace-matrix`）按编号 token 闭合 行为 × 归属 × 单元 × 测试 × 切片。编号规则为硬约束：

- **行为：`BHV-NNN`**。需求阶段 `prd.md` 中以 `### BHV-NNN <短名>` 标题定义（NNN 为数字；创建后不复用、不重排，删除留洞）。Go 后端行为以「协议端点 / 编排步骤 / 数据访问 / 失败收口」为枚举单位，例：
  - ✅ `### BHV-012 创建代理用户` — Given 管理员已登录会话有效 When `POST /api/users` 携带 `display_name`/`proxy_username` Then service 校验入参→repository 落库→触发 config 同步→返回 201 与用户实体；校验失败返回 400 并携带 `ErrValidation` 文案。
  - ❌ `### BHV-012 处理用户` — Given 有请求 When 调用 Then 完成。（无前置、无协议、无失败路径、无状态变化）
- **设计单元：`UNIT-<slug>`**。详细设计阶段以 `### UNIT-<slug>` 标题定义（slug 为语义 kebab-case，体现服务+层角色），例：`UNIT-user-service`、`UNIT-user-repository`、`UNIT-users-handler`、`UNIT-session-manager`。
- **下游引用一律写裸编号 token**：归属判定表逐行以 `BHV-NNN` 开头；详细设计单元的「承接哪些行为」逐条写 `BHV-NNN`；`implement.md` 的实现切片逐条挂 `UNIT-<slug>`。
- **断链即拦截**：单元引用了 prd 不存在的 `BHV-NNN`（幽灵行为）、行为无任何单元承接、切片引用了不存在的 `UNIT-<slug>`（幽灵单元）——均被 Gate 拦截，进不了下一阶段。`guru_gate.py trace-matrix <task_dir> --write` 生成追溯矩阵并落盘 `<task_dir>/trace-matrix.md`；`--strict` 在有断链时 exit 2。

## Quality Check（五道 Gate，对齐 guru_gate.py）

每道 Gate 的结构判定由 `guru_gate.py <gate> <task_dir>` 执行；以下为各 Gate 的不进条件（命中即阻塞），与脚本同口径：

### Gate 1 — 需求（`guru_gate.py requirements`）

`prd.md` 缺以下五要素任一即不进概要：

- 缺行为编号：行为未以 `### BHV-NNN <短名>` 标题定义。
- 缺行为规格：未出现 `Given/When/Then` 三段式（至少一组）。
- 缺核心能力清单：未出现 `P0`/`P1` 优先级标记。
- 缺失败路径章节（失败路径 / 失败场景 / 异常路径 / failure 任一关键词缺失）。
- 缺验收场景/标准章节（验收 / acceptance）。
- 缺未决问题章节（未决 / open question / 待确认）——无未决也须显式声明「无未决」。

### Gate 2 — 概要设计（`guru_gate.py overview`）

行为无唯一 owner+三问理由、归属违反分层依赖律、承接索引缺失 → 不进详细。脚本判定项：

- 缺行为→owner 归属表（`owner` / `归属` 关键词缺失）。
- 归属表未引用 `BHV-NNN` 编号（归属必须按行为编号逐行展开）。
- 归属表缺三问理由（`为什么属于` / `归属理由` / `三问`：为什么属于它 / 为什么不属于别人 / 为什么需独立存在）。
- 缺详细设计承接索引（`承接索引` / `doc_type`）。
- **full 链另查**：设计包骨架（`README.md` / `design-main.md` / `chapters/` 目录缺一即拦）、缺架构就绪自检节（G1~G8 自评）、承接索引未落到 `chapters/<file>.md`、缺 mermaid 架构图、缺时序图或时序图策略表。
- 归属判定示例（Go 分层依赖律）：路由注册/请求解析/JSON 编解码/状态码 → `entry-api`；业务编排/入参校验/sentinel error → `biz`；SQL/行映射/`ErrNotFound` 转换 → `repository-data`；实体/参数结构体 → `domain`；签名 cookie/bcrypt → `config`（或 `biz`）；跨服务结构体 → `external`（或 `domain`）。把数据访问归给 handler、或让 repository 反向 import service 即违反单向依赖律，直接 fail。

### Gate 3 — 详细设计（`guru_gate.py detail`）

合同八问缺项、追溯不到概要 owner、无测试映射、涉权限无合规依据 → 不进实现。脚本判定项：

- 缺设计单元编号（未以 `### UNIT-<slug>` 标题定义）。
- 合同八问的四个机检标记缺失任一：承接行为（八问之 1，`承接…行为`）、失败收口（八问之 5，`失败…收口` / `失败如何`）、测试映射（八问之 7，`测试映射` / `哪些测试`）、不得补造声明（八问之 8，`不得…补造` / `不在此补造`）。
- `implement.md`（trace §1 实现计划）不存在。
- 承接断链：单元引用幽灵 `BHV-NNN`、行为无单元承接 → 拦截。
- **full 链另查**：设计包骨架、章节闭合（承接索引 ↔ `chapters/*.md` 双向闭合，缺文件或孤儿文件均拦）、pending L2 拦截（命中非 v1 doc_type 须 `L2豁免：<doc_type> 理由：…`）。
- 八问完整骨架（写作完成条件，非仅机检标记）：① 承接哪些 `BHV-NNN`；② 输入/输出/错误结果（Go 签名级：函数签名、`domain` 结构体、错误枚举与 sentinel error 表）；③ 读写哪些状态（DB 行/会话态，写 owner 与概要一致）；④ 调用哪些依赖、不调用哪些（service 调 repository 不反向；handler 不直连 DB）；⑤ 失败如何收口（`%w` 链式包装 + `errors.Is(err, ErrValidation/ErrNotFound)` 检查 + HTTP 状态码映射，逐条失败路径对应处置）；⑥ 产生哪些事件/后置（config 同步触发、审计、副作用）；⑦ 哪些测试验证它（映射到 `internal/<pkg>/*_test.go` 的 `testing`，逐行为给成功+全部失败路径测试点）；⑧ 哪些内容不得在此补造（如 handler 不决定 SQL，service 不决定路由）。

### Gate 4 — 实现（`guru_gate.py implement`）

trace 四节不全、切片未挂 UNIT、analyze/test/lints/compliance 任一无证据 → 不进 commit。脚本判定项：

- `implement.md` 不存在。
- trace 四节缺任一：计划节（`计划` / `切片`）、执行节（`执行` / `改动文件`）、证据节（`证据` / `analyze` / `test`）、阻塞与偏差节（`阻塞` / `偏差`）。
- 实现切片未引用任何 `UNIT-<slug>` 编号（切片必须挂设计单元）。
- 切片引用幽灵单元（详细设计无此 UNIT）。
- 项目级证据（由 worktree.yaml 其余 verify 条目执行）：`go build ./...` / `go vet ./...` / `golangci-lint run` / `go test ./...`（测试名级别，不只写「全部通过」）；config/secret 合规（密钥只写环境变量名引用，不落真实 key）。

### Gate 5 — 审核/复盘

- 存量豁免判定：`SLOT-17` 清单内记债不阻塞；清单外新增违例（如新代码绕过 service 让 handler 直连 DB、新增 gin/echo 依赖、新写 secret 字面量）阻塞。
- 缺陷只能回上游修：审核发现结构性缺陷（归属错、合同越界、单元跟随名词而非行为）回到拥有该决策的阶段修订，禁止下游补造。
- 复盘只沉淀「这类任务如何被做好」，不沉淀本次需求事实；萃取按 [extraction-template.md](./extraction-template.md) 九段结构执行。

---

**统一红线（贯穿五阶段，对齐 golden-path 锁定项）**：框架只用 `net/http ServeMux`（禁 gin/echo 等重型框架）；分层 `transport → service → repository → domain` 严格单向无环（除 `domain` 外不跨 `internal` 包导入）；错误用 sentinel + `fmt.Errorf("%w: …")` + `errors.Is()`；生命周期 `main()` 控信号 → `app.New()` → `app.Run()` → `app.Shutdown()`，Handler 接 `context` 支持 timeout；配置经 `config.Load()` 集中装载（env + 默认值，前缀区分服务）；`internal/` 隐私、`packages/contracts/` 放跨服务契约。任一红线违例在对应阶段 Gate 直接 fail，不可豁免。
