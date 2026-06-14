# Guru Go Backend — Spec 库

> 本 spec 库由 guru-template 安装（`trellis init -t guru-go-backend -r <registry>`），落位 `.trellis/spec/`（PROTECTED：`trellis update` 永不覆盖项目侧已改文件）。
> 平台形态：Go monorepo（safa-land 实测）——服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，`cmd/<svc>/main.go` 单一入口，跨服务契约在 `packages/contracts/`。
> 知识源头唯一真源原则：本库只「装载」规则，writing / review skill 与 Gate 不复写规则正文；冲突时以阶段子 SSOT 为准、本导航为辅。

本 README 是 guru-go-backend spec 包的导航入口，回答四个问题：目录里有什么（目录树）、每个 harness 文件管什么（文件职责）、它们如何在五阶段 workflow 中被装载（阶段关系）、哪些线一旦越过就直接 fail（硬规则速览 + Gate 判定）。本文件**只导航、不承载规则正文**——任何具体规则正文以被指向的 SSOT 为准。

## 目录树

安装后落位 `.trellis/spec/`，结构如下（标注 v1 已提供 / 规划中 / init 生成）：

```
.trellis/spec/
├── README.md                                  本导航（你正在读的文件）
├── guides/
│   ├── index.md                               guides 导航（只导航不承载正文）
│   └── golden-path.md                         通用方法 SSOT：分层依赖律 + 各层迷你路径 + 禁止清单 + 门禁映射 [规划中]
├── conventions/
│   ├── index.md                               槽位地图 + 校验清单 C1~C6 + Gate 兼容口径
│   ├── project-conventions.template.md        槽位定义模板（SLOT-01~17，只定义不取值；SLOT-17=存量违例恒为最后槽）
│   ├── safa-land.project-conventions.md       样例取值（safa-land 实测，只读参考、不参与校验）[规划中]
│   └── project-conventions.md                 本项目取值唯一权威（硬前置只认此文件）[init 后由模板填写]
├── harness/
│   ├── index.md                               五阶段方法 SSOT 入口：编排 + 装载顺序 + 编号纪律 + 五道 Gate
│   ├── extraction-template.md                  复盘/萃取九段模板（沉淀「这类任务怎么做好」）
│   ├── overview/
│   │   └── overview-structure-single-source.md 概要设计 SSOT：行为枚举→归属判定→承接索引→架构视图 [规划中]
│   ├── detail/
│   │   ├── detail-structure-single-source.md   详细设计 L1 SSOT：合同八问骨架 + doc_type 七类 [规划中]
│   │   ├── detail-type-entry-api.md            L2：entry-api（internal/transport/http handler 入口行为）
│   │   ├── detail-type-biz.md                  L2：biz（internal/service 业务核心层）
│   │   └── detail-type-repository-data.md      L2：repository-data（internal/repository 数据访问合同 + db/migrations）
│   └── implementation/
│       └── implementation-trace-contract.md    实现 trace 合同：必含四节 + 证据感
├── backend/                                    by-layer 项目 spec — backend 层（transport/service/repository/domain 分层）：项目实际模式（bootstrap 从真实项目填实）
│   ├── index.md                               本层导航入口（链到本层真实存在的 topic 文件）
│   ├── directory-structure.md                  `services/*/internal` 真实分层目录组织：项目实际模式（bootstrap 从真实项目填实）
│   ├── api-design.md                           transport 层 entry-api：net/http 路由 / JSON 编解码 / 错误码映射：项目实际模式（bootstrap 从真实项目填实）
│   ├── service-patterns.md                     service 层 biz：编排与依赖注入边界：项目实际模式（bootstrap 从真实项目填实）
│   ├── repository-data.md                      repository 层：数据访问与 db 迁移：项目实际模式（bootstrap 从真实项目填实）
│   ├── domain-model.md                         domain 层：模型与 sentinel error 归属：项目实际模式（bootstrap 从真实项目填实）
│   ├── config-runtime.md                       config / 启动关闭序列：项目实际模式（bootstrap 从真实项目填实）
│   ├── error-handling.md                       错误翻译与包装风格：项目实际模式（bootstrap 从真实项目填实）
│   ├── logging.md                              logger 注入与结构化字段：项目实际模式（bootstrap 从真实项目填实）
│   └── quality.md                              go build/vet/test/golangci-lint 门禁：项目实际模式（bootstrap 从真实项目填实）
└── shared/                                     by-layer 项目 spec — shared 层（跨层）：项目实际模式（bootstrap 从真实项目填实）
    ├── index.md                               本层导航入口（链到本层真实存在的 topic 文件）
    ├── go-conventions.md                       Go 语言级约定与包可见性：项目实际模式（bootstrap 从真实项目填实）
    ├── naming-conventions.md                   包/文件/类型/接口/常量命名规律：项目实际模式（bootstrap 从真实项目填实）
    └── git-conventions.md                      分支/提交/PR 约定：项目实际模式（bootstrap 从真实项目填实）
```

> 标注「规划中」的文件被 `harness/index.md` 与各子 SSOT 引用，是当前迭代的待落盘项；在它们落盘前，对应阶段以 index.md 的对应章节为临时权威。标注「init 后填写」的 `project-conventions.md` 是本仓库取值的唯一权威，缺失即硬前置不通过。

## 各 harness 文件职责

| 文件 | 职责（管什么） | 何时读 | 承载的合同/检查 |
|------|----------------|--------|-----------------|
| `harness/index.md` | 五阶段方法的唯一权威入口：阶段→SSOT 映射、装载顺序、`doc_type` 七类取值表、编号纪律（BHV/UNIT）、五道 Gate 不进条件 | 任何阶段开工前**必读** | 编排与索引；与子 SSOT 冲突时以子 SSOT 为准 |
| `guides/golden-path.md` | 通用方法 SSOT：模块形态、分层依赖律、各层迷你路径、错误处理三件套、启动/关闭契约、入口决策树、禁止清单、门禁映射 | 写任何代码前**必读** | 六条锁定红线的正文（不可豁免） |
| `conventions/project-conventions.md` | 本项目槽位取值的唯一权威：SLOT-01~17 取值 + 代码证据 + 生效范围 + C1~C6 校验 + SLOT-17 存量违例清单 | 所有阶段硬前置（C1~C6 任一不过即停） | 项目级取值；writing/review/Gate 只认此文件 |
| `conventions/project-conventions.template.md` | 槽位定义模板：每个 SLOT 的决策问题、生效范围、与硬规则的边界，不含取值 | 填写 `project-conventions.md` 时对照 | 槽位定义来源（随 update 演进） |
| `harness/overview/overview-structure-single-source.md` | 概要设计 SSOT：行为枚举→分层归属判定（owner + 三问理由）→详细设计承接索引（`chapter_target → doc_type`）→架构总览人审视图 | 进概要阶段前 | 概要 Gate 的归属表 + 承接索引判定基线 |
| `harness/detail/detail-structure-single-source.md` | 详细设计 L1 SSOT：合同八问完整骨架、`doc_type` 七类与其证据锚点、L2 层级契约（L1 > L2 > golden-path > conventions） | 进详细阶段前 | 详细 Gate 的合同八问判定基线 |
| `harness/detail/detail-type-entry-api.md` | L2 类型规范（doc_type `entry-api`）：`internal/transport/http` handler 入口的合同八问特化——逐 route+method 行为、五类输入来源分列、错误响应三态收口、无状态适配层约束 | 详细阶段命中 entry-api 单元时 | 合同八问的 entry-api 特化；冲突以 L1 为准 |
| `harness/detail/detail-type-biz.md` | L2 类型规范（doc_type `biz`）：`internal/service` 业务流程的合同八问特化——方法签名级输入输出、sentinel error 全集、业务状态唯一写 owner、依赖正反面（service 调 repository 不反向） | 详细阶段命中 biz 单元时 | 合同八问的 biz 特化；冲突以 L1 为准 |
| `harness/detail/detail-type-repository-data.md` | L2 类型规范（doc_type `repository-data`）：`internal/repository` 数据访问合同 + `db/migrations` canonical 表/迁移的合同八问特化 | 详细阶段命中 repository-data 单元时 | 合同八问的 repository-data 特化；冲突以 L1 为准 |
| `harness/implementation/implementation-trace-contract.md` | 实现 trace 合同：必含四节（计划/执行/证据/阻塞偏差）、自下而上执行顺序、切片挂 `UNIT-<slug>`、证据节须有可复跑命令与测试名 | 进实现阶段前 | 实现 Gate 的 trace 四节判定基线 |
| `harness/extraction-template.md` | 复盘/萃取九段模板：只沉淀「这类任务如何被做好」（可复用方法），不沉淀本次需求事实 | 审核/复盘阶段 | 萃取产物结构基线 |

`*/index.md` 三个导航文件（`harness/index.md`、`guides/index.md`、`conventions/index.md`）只做目录导航与边界声明，不承载规则正文——避免双真源漂移。

## by-layer 项目 spec（项目实例层）

`backend/` 与 `shared/` 是**按层组织的项目实例 spec**——记录「本项目实际怎么写」，而非通用方法或团队栈级红线。本平台 by-layer 分两层：`backend/`（Go 服务层，按 transport/service/repository/domain 分层）与 `shared/`（跨层：Go 语言级约定、命名、git，对所有 `internal/` 包通用）。它与 harness、conventions 的边界如下：

- **harness（方法学 / HOW）**：承载五阶段方法、合同八问、doc_type 七类、编号纪律与五道 Gate 口径——「这类任务怎么做好」的可复用方法，与具体项目无关。
- **conventions（钉死的 SLOT 决策 / Gate 硬前置）**：`project-conventions.md` 是 SLOT-01~17 槽位取值的唯一权威，逐条钉死（选哪个 DB 驱动、用 slog 还是标准 `log` 等），C1~C6 校验，是所有阶段的硬前置（任一不过即停）。
- **by-layer（开放式按层模式 / 项目风格匹配）**：不是钉死的槽位、不是 Gate 硬前置，而是**开放式的按层模式文档**——记录每层真实的目录结构、命名规律、WRONG·CORRECT 代码示例与团队踩过的坑，供 sub-agent 写作/实现前匹配本项目既有风格。

要点纪律：

- **document reality 非理想**：by-layer 由 `00-bootstrap-guidelines` 任务扫真实项目代码填实（记录实际约定与真实文件路径的代码示例），未填实前各 topic 文件标 `To fill`；写的是「这个项目实际怎么做」，不是「应该怎么做」。
- **不复写、只引用**：分层依赖律、错误三件套、doc_type 口径等正文在 `guides/golden-path.md` 与 `harness/`，by-layer 只引用不复写——避免双真源漂移。
- **各层 index.md 是导航入口**：`backend/index.md`、`shared/index.md` 只做本层导航与边界声明，链到本层**真实存在**的 topic 文件（如 backend 层链到 `directory-structure.md` / `api-design.md` / `service-patterns.md` / `repository-data.md` / `domain-model.md` / `config-runtime.md` / `error-handling.md` / `logging.md` / `quality.md`；shared 层链到 `go-conventions.md` / `naming-conventions.md` / `git-conventions.md`），不承载规则正文。

## 与五阶段 workflow 的关系

guru-go-backend workflow 的每个阶段从本库装载规则。**双轨制**：task.json `guru_chain` 判轨（`guru_after_create` 创建默认 `full`）。full = 完整五阶段链（新服务、新协议端点、鉴权/会话、DB 迁移、跨服务契约变更等高风险需求），走目录级设计包（task.json `design_package`，相对 repo root）；light = 轻量链（同包内小迭代且获用户同意降级），产物收敛为任务内单文件。下表产物列写作 `full / light`。

```
需求(prd.md)              ← guru-ai-guides requirement-writing / requirement-review + requirement-doc-standard（硬前置：未安装即停）
概要(design-main / §概要)  ← .trellis/spec/harness/overview/overview-structure-single-source.md
详细(chapters/* / §详细)   ← .trellis/spec/harness/detail/detail-structure-single-source.md
                            + 命中类型的 detail-type-entry-api.md / detail-type-biz.md / detail-type-repository-data.md（其余四类 doc_type pending：
                              full 链须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2；light 链按 L1 合同八问展开并标注 l2_status: pending）
实现(代码 + implement.md)  ← .trellis/spec/guides/golden-path.md + .trellis/spec/harness/implementation/implementation-trace-contract.md
审核/复盘(findings + 回写) ← 各阶段 SSOT 审核基线章节 + .trellis/spec/harness/extraction-template.md
```

**每个任务开工前的统一前置**（`harness/index.md` Pre-Development Checklist，任一未过即停）：

1. 读 `.trellis/spec/conventions/project-conventions.md` 并过校验清单 C1~C6（DI / ORM / 日志 / 测试框架 / API 风格 / DB 驱动 / lint / 文档生成 / 会话鉴权等槽位缺失或未填 → 停止）。
2. 读 `.trellis/spec/guides/golden-path.md`，确认本任务不触碰六条锁定红线。
3. 确定服务边界：本任务落在哪个 `services/<svc>/`，复用还是新建 `internal/{app,config,transport,service,repository,domain,auth}` 包；跨服务数据结构是否需进 `packages/contracts/`。
4. 按当前阶段读对应阶段 SSOT，并把所读文件登记进任务的 `implement.jsonl` / `check.jsonl`（带 reason，便于追溯读了哪条规则）。
5. 产物语言中文优先（英文仅限代码标识符、命令、路径、协议字段如 `application_account_id`、框架/库名如 `net/http`/`lib/pq`、缩写如 HMAC-SHA256、原文引用）。

**编号纪律（贯穿全链，机器追溯按编号 token 闭合）**：

- 行为 `BHV-NNN`：需求阶段 `prd.md` 以 `### BHV-NNN <短名>` 标题定义；NNN 为数字，创建后不复用、不重排，删除留洞。Go 后端行为以「协议端点 / 编排步骤 / 数据访问 / 失败收口」为枚举单位。
- 设计单元 `UNIT-<slug>`：详细设计阶段以 `### UNIT-<slug>` 标题定义；slug 为语义 kebab-case，体现服务+层角色（`UNIT-user-service`、`UNIT-user-repository`、`UNIT-users-handler`、`UNIT-session-manager`）。
- 下游引用一律写**裸编号 token**：归属判定表逐行以 `BHV-NNN` 开头；详细单元「承接哪些行为」逐条写 `BHV-NNN`；`implement.md` 实现切片逐条挂 `UNIT-<slug>`。
- 断链即拦截：单元引用 prd 不存在的 `BHV-NNN`（幽灵行为）、行为无任何单元承接、切片引用不存在的 `UNIT-<slug>`（幽灵单元）——均被 Gate 拦截。`guru_gate.py trace-matrix <task_dir> --write` 生成追溯矩阵并落盘 `<task_dir>/trace-matrix.md`，`--strict` 在有断链时 exit 2。

## 硬规则速览（任何阶段不可豁免）

下列六条属团队栈级 canonical（golden-path 锁定红线），任何 SLOT 槽位取值不得与之冲突（C4 校验该约束）。完整正文见 `guides/golden-path.md`，本节只速览以便对照：

- **框架轻量**：HTTP 入口一律 `net/http` 的 `ServeMux`；禁用 gin / echo / fiber 等重型 Web 框架（中间件用标准 `http.Handler` 装饰链表达）。
- **分层依赖律（严格单向、无环）**：`transport(handler) → service → repository → domain`。除 `domain` 可被各层共享外，禁止跨 `internal/` 包反向或横向导入；`service` 不得 import `transport`，`repository` 不得 import `service`。
- **错误处理三件套**：每个服务级包定义 sentinel errors（`var ErrXxx = errors.New(...)`）；跨层传播用 `fmt.Errorf("%w: ...", ErrXxx)` 链式包装；判定一律 `errors.Is()` / `errors.As()`，禁止字符串比对错误信息。
- **启动/关闭生命周期**：`main()` 只接信号（`signal.NotifyContext`）→ `app.New(cfg)` → `app.Run(ctx)` → `app.Shutdown(ctx)`；每个 Handler 接收 `context.Context` 并尊重 `ctx.Done()` / timeout。
- **配置集中**：环境变量 + 默认值统一在 `config.Load()` 装配；env 前缀按服务隔离（如 `CONTROL_API_*`），禁止业务代码里散读 `os.Getenv`。
- **包可见性约定**：服务私有代码进 `internal/`（编译期隔离）；跨服务共享契约进 `packages/contracts/`，且只放纯数据契约（不放业务逻辑）。

这些规则在 SLOT 槽位里只能「具体化落点」（选哪个 DB 驱动、用 slog 还是标准 `log`），**不能反转方向或绕过**。

**好 / 坏例子（红线落地基线）**：

- ✅ 好：`internal/service/user_service.go` 定义 `func (s *userService) Register(ctx context.Context, in RegisterInput) (*User, error)`，对 repository 返回的 `sql.ErrNoRows` 转换的 `domain.ErrUserNotFound` 用 `fmt.Errorf("%w: load user", domain.ErrUserNotFound)` 上抛，handler 用 `errors.Is(err, domain.ErrUserNotFound)` 映射 404。
- ❌ 坏：handler 直接 `db.QueryRow(...)` 拼 SQL（绕过 service/repository，违反分层依赖律）；或 repository 返回 `*http.Response` / 写 HTTP 状态码（反向依赖 transport 关注点，C4 直接拦截）；或 `if err.Error() == "user not found"` 字符串比对（违反错误三件套）。

**不适用场景（本库不解决的问题）**：不写五阶段产物正文（BHV/UNIT、归属表、合同、trace 在任务目录或设计包内产出）；不复写硬规则正文（正文在 golden-path）；不替代 ADR（槽位取值变更走 ADR）；不裁决跨平台差异（Flutter / iOS / Android 各有自己的 `guru-<platform>/`）。

## Gate 判定（五道，对齐 `guru_gate.py`）

每道 Gate 的结构判定由 `guru_gate.py <gate> <task_dir>` 执行；以下为各 Gate 的不进条件（命中即阻塞），与脚本同口径。完整判定项见 `harness/index.md` §Quality Check。

| Gate | 命令 | 不进条件（命中即 fail） |
|------|------|--------------------------|
| 需求 | `guru_gate.py requirements` | `prd.md` 缺五要素任一：行为编号 `### BHV-NNN`、`Given/When/Then` 行为规格、`P0`/`P1` 优先级、失败路径章节、验收场景章节、未决问题章节（无未决也须显式声明「无未决」） |
| 概要 | `guru_gate.py overview` | 缺行为→owner 归属表 / 归属表未引用 `BHV-NNN` / 缺三问理由（为什么属于它·不属于别人·需独立存在）/ 缺承接索引（`doc_type`）/ 归属违反分层依赖律；full 链另查设计包骨架、架构就绪自检 G1~G8、mermaid 架构图、时序图 |
| 详细 | `guru_gate.py detail` | 缺 `### UNIT-<slug>` 标题 / 合同八问四个机检标记缺任一（承接行为·失败收口·测试映射·不得补造声明）/ `implement.md` 不存在 / 承接断链；full 链另查章节闭合与 pending L2 拦截（命中非 v1 doc_type 须 `L2豁免：<doc_type> 理由：…`） |
| 实现 | `guru_gate.py implement` | `implement.md` 不存在 / trace 四节缺任一（计划·执行·证据·阻塞偏差）/ 切片未挂 `UNIT-<slug>` / 切片引用幽灵单元 / 项目级证据缺失（`go build ./...`、`go vet ./...`、`golangci-lint run`、`go test ./...` 须到测试名级别；secret 只写环境变量名引用，不落真实 key） |
| 审核/复盘 | 人工 + 存量豁免判定 | SLOT-17 存量违例清单内记债不阻塞；清单外新增违例阻塞（新代码绕过 service 让 handler 直连 DB、新增 gin/echo 依赖、新写 secret 字面量、单元跟随名词而非行为）；结构性缺陷只能回上游修，禁止下游补造 |

**结构兼容底线**（让 `guru_gate.py` 结构检查通过的最小骨架）：需求五要素齐全；概要含归属表（逐行 `BHV-NNN` + 三问理由）+ 承接索引（`chapter_target → doc_type`）；详细每单元含合同八问（承接行为 / 输入输出错误 / 读写状态 / 依赖正反面 / 失败收口 / 事件后置 / 测试映射 / 不得补造）；实现 trace 含四节且证据节有可复跑命令与测试名。

---

**装载路径提醒**：本库安装后落在 `.trellis/spec/`——通用方法真源 `.trellis/spec/guides/golden-path.md`，五阶段骨架 `.trellis/spec/harness/*`，项目槽位取值 `.trellis/spec/conventions/project-conventions.md`。writing / review skill 与 Gate 一律按安装后路径装载，不要引用 guru-template 开发期路径。
