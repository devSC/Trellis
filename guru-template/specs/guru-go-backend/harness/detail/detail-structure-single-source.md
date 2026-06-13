# Go 后端详细设计 — 单一来源规范（L1）

> 跨类型唯一权威。L2 类型文件只承载类型差异，不得与本文冲突；writing/review 只做编排与判定。
> 上游硬输入：概要设计的归属判定表 + `chapter_target → detail_doc_type` 承接索引 + `technology_decision_handoff[]`。
> 层级契约：本文（L1）承载规则正文与完成条件；writing/review skill 的 `references/` 只承载编排细则、模板与示例；冲突时 L1 > L2 > references > SKILL.md。
> 平台基线：本文是 Go monorepo（`services/<svc>/internal/{app,config,transport,service,repository,domain,auth}` + `cmd/<svc>/main.go`）的详细设计权威；通用方法真源见 `.trellis/spec/guides/golden-path.md`，流程骨架见 `.trellis/spec/harness/*`。

## 0. 与 backend 九类的关系（裁剪说明）

本规范以后端九类 `detail_doc_type`（Entry/API、Entry/CLI、Entry/Background Trigger、Biz、Utility、Data、Config、External、Runtime）为来源，按 Go monorepo 实测形态裁剪为 **七类**：

| backend 九类 | Go 七类 | 裁剪理由 |
|--------------|---------|---------|
| Entry / API Behavior + Entry / CLI Behavior + Entry / Background Trigger Behavior | `entry-api` | Go 服务以 `net/http` ServeMux HTTP endpoint 为主入口；CLI 子命令（`cmd/<svc>` 的 flag 解析）、定时任务、消息消费均归 `entry-api` 的 `entry_kind` 子类（见 §2.1），不再拆成三个独立类型——它们共用 `transport` 层薄入口 + 单向调 `service` 的同一合同骨架。 |
| Biz / Behavior | `biz` | 对应 `internal/service/*_service.go`，是厚业务核心与状态/能力 owner。 |
| —（新增） | `repository-data` | Go 把数据访问合同（`internal/repository`）与 canonical 表/迁移（`db/migrations/`）合并为一类：合同 + DDL + 字段字典在同一文档闭合，因为 Go 原生 SQL 栈下 Repo 接口与表结构强耦合。 |
| —（新增聚焦） | `domain` | `internal/domain/*.go` 是 Go 分层依赖律唯一允许被跨层导入的包：实体、值对象、sentinel errors、领域不变量。独立成类以锁定"无副作用、无 I/O、可被任意层导入"的边界。 |
| Config / Runtime Contract | `config` | 对应 `internal/config/config.go` + `config.Load()` + env 前缀；运行配置与 secret 引用一等合同。 |
| External / Integration Contract | `external` | 外部系统/第三方 API/对象存储/模型服务的集成合同。 |
| Runtime / Deployment Contract | `runtime` | 进程拓扑、`app.New/Run/Shutdown` 生命周期、信号处理、健康检查、发布回滚边界。 |
| Utility / Technical Capability | （并入 `domain` 的纯函数 + `external` 的技术封装） | Go 轻量栈下业务无关纯函数留在被调用包内，不单独立类；跨服务复用的技术能力走 `packages/contracts/`，按 `external` 或 `domain` 合同承接。 |

七类清单与覆盖对象见 §2。Go 平台的硬规则（golden-path 锁定，不可豁免）贯穿全文，集中声明见 §6.0。

## 1. 装载与硬前置

执行写作或审核前依次确认，任一失败即终止并输出前置缺口：

- P1 本文件可读；涉及类型的 L2 文件可读（v1 仅 `biz` / `repository-data` / `entry-api` 提供 L2；其余类型按本文 §3 合同八问展开并在文档头标注 `l2_status: pending`，full 链另须满足 §2 的 pending L2 豁免合同）。
- P2 通用方法真源 `.trellis/spec/guides/golden-path.md` 可读（分层依赖律、错误处理范式、启动/关闭契约是详细设计的硬基准）。
- P3 目标仓库 `.trellis/spec/conventions/project-conventions.md` 可读且校验通过（DI 框架 / ORM / 日志 / 测试框架 / API 风格 / DB 驱动 / lint / 文档生成 / 会话鉴权槽位均已取值，无空槽、无与 golden-path 冲突项）。
- P4 概要主定义可定位（full 链=`design_package/design-main.md`；light 链=`design.md` 第 1 节），且承接索引存在、可建立完整非空的 `chapter_target → detail_doc_type` 目标集合。**索引缺失 / 为空 / 任一条目映射不完整 → 回退概要阶段，禁止在详细阶段补造归属。**
- P5 概要 Gate 已过且人工确认已落盘（`guru_gate.py status` 可查 overview 确认）；未确认不得开始详细写作。

任一前置失败时，writing 停止并输出"前置缺口 + 概要修订动作"；review 只输出前置缺口，不产出 findings 与放行结论。

## 2. 七类 detail_doc_type

| doc_type | 覆盖对象 | 落点（internal 包） | L2 状态 |
|----------|---------|---------------------|---------|
| `entry-api` | 薄入口：HTTP endpoint（ServeMux 路由注册 + handler）、CLI 子命令、定时/消息触发；req/resp 解码编码、参数校验、鉴权中间件挂载、context/timeout 透传、调用 service 行为、错误→HTTP 状态码映射 | `transport/http/`、`cmd/<svc>/`、`transport/<consumer>/` | **v1 提供** |
| `biz` | 厚业务核心：业务行为、状态 owner、核心能力（P0/P1）展开、业务规则、事务边界、失败收口、领域事件发射；调 repository 与 domain | `service/*_service.go` | **v1 提供** |
| `repository-data` | 数据访问合同 + canonical 数据定义：Repo 接口（查询意图/过滤/排序稳定性/分页/事务）、表 DDL、字段字典、索引/约束、版本迁移、`lib/pq`/PostgreSQL 访问点、错误转换（`sql.ErrNoRows` → domain sentinel） | `repository/*_repository.go`、`db/migrations/` | **v1 提供** |
| `domain` | 领域实体与不变量：struct/值对象、枚举、sentinel errors（`var ErrXxx = errors.New(...)`）、纯函数业务规则、构造校验；**无 I/O、无副作用、可被任意 internal 包导入** | `domain/*.go` | pending |
| `config` | 运行配置一等合同：配置键、env 变量名 + 前缀（如 `CONTROL_API_*`）、默认值、`config.Load()` 装载、校验规则、secret 引用（不落明文）、reload/启动失败行为、消费方引用 | `config/config.go` | pending |
| `external` | 外部集成合同：第三方 API / 对象存储 / 模型服务 / Webhook 回调的协议、请求/响应/错误、鉴权边界、SLA/限流、超时重试、本系统 adapter 消费边界；跨服务契约落 `packages/contracts/` | `transport/<svc>client/`、`packages/contracts/` | pending |
| `runtime` | 运行部署合同：进程/服务拓扑、`main()→app.New()→app.Run()→app.Shutdown()` 生命周期、信号处理（SIGINT/SIGTERM）、context 超时控制、健康检查、启动顺序、发布/回滚边界、环境矩阵 | `app/app.go`、`cmd/<svc>/main.go` | pending |

**承载形态按链型分轨**（轨道判定见概要 SSOT）：

- **full 链（目录级设计包）**：每个 `chapter_target` 独立一个 `design_package/chapters/<slug>.md` 文件（文件名与概要承接索引一致，gate 检查双向闭合）。执行采用 **directory_precheck + chapter_loop**（合同见 §5）：先确认 design-main.md 承接索引存在且非空（缺失/为空 → 回退概要，禁止详细补造），再**逐章或小批次**生成正文——禁止一次性全量输出全部章节（全量输出必然退化为大纲级薄文档）。
- **light 链（单文件）**：合并为任务内 `design.md` 第 2 节单文档多章节，每章仍须独立满足对应合同。

**pending L2 拦截（full 链）**：承接索引命中 L2 状态为 pending 的 doc_type（`domain`/`config`/`external`/`runtime`）时，必须在 design-main.md 显式声明 `L2豁免：<doc_type> 理由：…`（说明按 L1 合同八问展开的风险与补齐计划），否则 gate 拦截；首选做法是先补齐对应 L2 再进详细设计。

### 2.1 entry-api 的 entry_kind 子类（强制标注）

`entry-api` 文档头必须标注 `entry_kind`，决定契约主定义形态与依赖闭合口径：

| `entry_kind` | 触发形态 | 契约主定义 | 落点 |
|--------------|---------|-----------|------|
| `http_endpoint` | `net/http` ServeMux 路由（如 `mux.HandleFunc("POST /api/users", h.Create)`） | req/resp JSON struct + HTTP 方法/路径/状态码 | `transport/http/router.go` + handler |
| `cli_command` | `cmd/<svc>/main.go` 的 flag / 子命令解析 | flag 参数表 + 退出码语义 | `cmd/<svc>/` |
| `scheduled_job` | 定时任务（`time.Ticker` / cron-like 调度） | schedule 表达式 + 任务触发契约 | `transport/<job>/` 或 `app` 调度注册 |
| `message_consumer` | 消息队列/流消费 | topic/key/payload schema + ACK/RETRY 策略 | `transport/<consumer>/` |

约束：HTTP/gRPC callback、Webhook callback、外部系统回调入口归 `entry_kind=http_endpoint`（仍是本系统对外暴露的入口），不归 `external`；`external` 只承载本系统**出站**调用外部系统的合同。

## 3. 合同八问（所有 doc_type 通用骨架）

**编号纪律**：每个设计单元以 `### UNIT-<slug>` 标题定义（语义 kebab-case，如 `### UNIT-user-create-handler`）；测试与实现切片对单元的引用一律写 `UNIT-<slug>` 编号 token。行为承接一律写 `BHV-NNN` 编号 token（prd 标题），下游引用写裸编号 token（不加路径、不加引号包装）。

每个设计单元必须回答以下八问，缺一不可（括号内为可验证信号——审核按此取证）：

1. **承接哪些行为**：逐条引用 `BHV-NNN` 编号（必须存在于 prd——幽灵引用与无承接行为均被 gate 断链拦截）。同时回指概要归属判定表对应行（owner 必须一致）。
2. **输入 / 输出 / 错误结果**：Go 类型签名级——入参 struct/字段类型/取值域、返回值/error、错误枚举（sentinel error 名）。输入/输出各有参数表；错误有错误类型表（见 §4 表合同）。
3. **读取 / 写入哪些状态**：明确读写分离；写 owner 必须与概要归属一致（可回指归属表行）。数据库写入只能由 `repository-data` 持有，`biz` 声明写意图但不直接持有 SQL。
4. **调用哪些依赖，不调用哪些依赖**：正反两面都写（防止越层）。依赖必须出现在概要架构图/归属表中，且**严格遵守分层依赖律**（§6.0）：`entry-api → biz → repository-data → domain` 单向；反向调用、跨层调用、循环依赖均为 §6 红线。"不调用"必须显式列出（如 handler 不直接调 repository、biz 不直接写 SQL、domain 不导入任何 internal 兄弟包）。
5. **失败如何收口**：每条失败路径的处置（sentinel error 包装 / 重试 / 降级 / 上抛 / HTTP 状态码映射）。错误转换遵循 Go 错误范式（§6.0）：服务级 sentinel errors + `fmt.Errorf("%w: ...")` 链式包装 + `errors.Is()` 检查。异常表逐行可对应一条失败路径 BHV 或八问 1 的行为分支，并标注转换位置（哪一层 wrap、哪一层 `errors.Is` 判定、哪一层映射 HTTP 码）。
6. **产生哪些事件 / 后置结果**：领域事件发射、日志埋点、副作用（逐条写明消费方）。
7. **哪些测试验证它**：映射到测试分层（unit / integration / e2e；测试框架取值见 project-conventions 槽位），逐行为给测试点（成功 + 全部失败路径）。
8. **哪些内容不得在此补造**：显式列出本单元不拥有的决策（如 handler "不决定业务规则——属 biz"；biz "不决定表结构与索引——属 repository-data"；domain "不决定配置默认值——属 config"）。

### 3.1 粒度标准（四条，写作与审核共用）

1. **可直接实现**：每个行为步骤具体到开发者可直接编码，不需要再分解业务逻辑或补充判定。
2. **明确调用关系**：每步指明调用的具体行为——下层组件的方法名与参数（如 `userRepo.FindByEmail(ctx, email)`）、本单元内部函数、外部依赖的具体调用。
3. **完整调用链**：从入口行为出发可追踪到所有下级行为，构成完整调用关系（与概要时序图一致）。
4. **粒度一致**：同一文档内所有行为描述粒度一致。

正反例（Go `entry-api` 的 `Create` handler 行为执行流程）：

✅ 合格粒度——`CreateUser` handler 执行流程：
1. `r.Context()` 取请求 context，挂上 `context.WithTimeout(ctx, 5*time.Second)`；defer cancel。
2. `json.NewDecoder(r.Body).Decode(&req)`；解码失败 → 写 `400 Bad Request` + `{"error":"invalid_body"}`，流程终止。
3. 调本单元 `validateCreateReq(req)`（email 非空且格式合法、password 长度 ≥ 8）；失败 → `400` + 字段级错误，流程终止。
4. 调 `userService.Create(ctx, req.Email, req.Password)`（owner：`biz`，返回 `(*domain.User, error)`）。
5. 成功 → `201 Created` + `json.NewEncoder(w).Encode(toUserResp(user))`。
6. `errors.Is(err, domain.ErrEmailTaken)` → `409 Conflict`；`errors.Is(err, context.DeadlineExceeded)` → `504`；其余 → `log.Error` + `500`。

❌ 不合格——`CreateUser` handler：解析请求，校验参数，调用服务创建用户，返回结果。（无 context/timeout、无调用对象与参数、无失败分支、无状态码映射）

## 4. 章节正文骨架合同（chapters/<slug>.md 模板）

full 链每个章节文件按以下骨架撰写（light 链 design.md 第 2 节的每章同构，可压缩小节层级）。骨架与合同八问的映射在末表——**模板是表达形式，八问是完成条件**，二者必须同时满足。

```markdown
# <chapter_target> 详细设计

> doc_type：<七类之一> ｜ l2_status：v1 / pending（pending 须有 L2豁免）
> entry_kind：<http_endpoint / cli_command / scheduled_job / message_consumer>（仅 entry-api）
> 承接索引：design-main.md 第 7 节 <chapter_target> ｜ 返回：[design-main](../design-main.md)
> 归属回指：归属判定表第 <行> 行（owner=<service/repository/...>）

## 1. 单元职责
本章承载的 UNIT 清单与一句话职责；与依赖/被依赖单元的关系（调用谁的什么行为、被谁调用）。
分层位置声明：本单元位于 <transport/service/repository/domain/config/external/app> 层，依赖方向 <下游单元>。

## 2. 行为定义
### 2.1 行为清单（每行为一行：行为名 + 简述 + 承接的 BHV-NNN 编号）
### 2.2 接口定义（Go 签名级，禁止超过签名级的实现代码）
``go
type UserService interface {
    Create(ctx context.Context, email, password string) (*domain.User, error)
    GetByID(ctx context.Context, id string) (*domain.User, error)
}
``

## 3. 核心数据结构
### 3.1 数据结构（Go struct/type/enum 签名级；JSON tag 与序列化按 project-conventions 槽位）
### 3.2 错误类型表（sentinel error）
| 错误名（var ErrXxx） | 定义层 | 语义 | 包装方式（%w 链） | 上抛/收口位置 |

## 4. 逐行为设计（每个行为一小节）
### 4.x <行为名>
- 函数签名（Go，含 ctx context.Context 与 error 返回位）
- 行为简述（一句话 + 承接 BHV-NNN 编号）
- 输入参数表：| 参数 | 类型 | 取值域/约束 | 必填 |
- 输出表：| 返回值 | 类型 | 语义 |
- 执行流程（mermaid sequenceDiagram，参与者用真实组件名如 Handler/UserService/UserRepo，步骤编号）
- 流程详述（编号列表，与图中编号一一对应，满足 §3.1 粒度标准；含 context/timeout、事务边界、依赖调用）
- 异常处理表：| 异常情况 | 处置（wrap/重试/降级/上抛/HTTP 码映射） | errors.Is 判定位置 | 错误转换位置（哪层） |

## 5. 状态与事务（biz 类必含；无状态单元写 N/A）
状态字段/owner 声明 + 事务边界（哪些写操作在同一 tx，谁开启/提交/回滚）+ 一致性语义。
repository-data 类此节写表/事务传播；entry-api/domain/config/external/runtime 按各自合同。

## 6. 数据合同（repository-data 类必含）
表 DDL（签名级，不写迁移脚本正文）+ 字段字典 + 索引/约束 + Repo 查询意图表 + sql 错误→domain sentinel 转换点。

## 7. 测试映射
| BHV/行为 | 测试层（unit/integration/e2e） | 测试点（成功+失败路径逐条） |

## 8. 不得补造清单
本单元不拥有的决策逐条列出（含分层越界禁止项）。
```

**骨架 ↔ 八问映射**：

| 模板节 | 满足八问 |
|--------|---------|
| 1 单元职责 | 八问 4（依赖正反面的"谁"与分层方向） |
| 2 行为定义 | 八问 1（BHV 承接）+ 2（签名/接口） |
| 3 核心数据结构 | 八问 2（类型/sentinel error 枚举） |
| 4 逐行为设计 | 八问 2/4/5/6（流程、依赖调用、失败收口、事件） |
| 5 状态与事务 | 八问 3（读写状态与 owner、事务边界） |
| 6 数据合同 | 八问 2/3（表/字段/错误转换，repository-data） |
| 7 测试映射 | 八问 7 |
| 8 不得补造清单 | 八问 8 |

辅助性文本（描述、表格、图内标签）一律中文；代码语法元素（包名/类型名/方法名/参数名/字面量/error 名）保持英文。

## 5. chapter_loop 执行合同（full 链）

### 5.1 directory_precheck（写作/审核共用前置）

进入任何章节写作前确认：① design_package 路径合法且 `chapters/` 存在；② design-main 承接索引非空且每条有目标文件名；③ pending L2 命中项（`domain`/`config`/`external`/`runtime`）均有 `L2豁免` 声明；④ `technology_decision_handoff[]` 中被本批引用的条目状态为"选定"（含 DI 框架 / ORM / 日志 / 测试框架 / API 风格 / DB 驱动等 project-conventions 槽位取值已确认；未选定 → 回退概要，禁止详细拍板）。任一失败 → 停止，输出缺口与概要修订动作。

### 5.2 推荐写作顺序（层级，沿 Go 分层依赖律自底向上）

1. **domain 层**（`domain`）——实体、值对象、sentinel errors、领域不变量先固化（被所有层导入，必须最稳定）。
2. **data 层**（`repository-data`）——按 domain 实体展开表 DDL、Repo 合同、迁移、错误转换。
3. **biz 层**（`biz`）——业务规则与状态 owner，按 repository-data 合同与 domain 实体展开；核心能力（P0/P1）在此 owner。
4. **entry 层**（`entry-api`）——只做解码/编码/校验/鉴权到稳定 biz 行为的薄适配。
5. **横切**（`config` / `external` / `runtime`）——被各层引用的一等合同收口。

同一 feature 的 biz 及其直接 repository-data 视为同一小批次优先完成。

### 5.3 批次与自动审修闭环

- 每批 **1~3 章**；禁止一轮生成全部章节。
- 每批生成后**立即自动 review**（不等用户）：章节模板符合性（§4）、八问完成条件（§3）、粒度（§3.1）、分层依赖律一致（§6.0）、错误范式一致（§6.0）、L2 差异规则（命中 v1 类型时）。
- 有 finding → 按 §9 判定修订形态 → 直接修复 → 复查受影响的行为/依赖/跨章引用。
- 当前批所有规则均有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。
- 只有"概要源缺失 / 业务语义必须人工确认 / 技术决策（含槽位取值）未选定 / 修复无法收敛"时才中断并升级用户。

### 5.4 层级 checkpoint

每完成一个层级（§5.2 的 1~5）执行跨章核对，失效项回到对应批次重走审修闭环：

- domain 层后：实体/sentinel error 唯一定义且无 I/O、无 internal 兄弟包导入；被引用的实体均已定义。
- data 层后：domain 实体均有对应表/Repo 合同；`sql.ErrNoRows` → domain sentinel 转换点一致；事务边界声明完整；SQL 只在 repository-data。
- biz 层后：UNIT↔BHV 承接闭合；状态写 owner 唯一；service 间依赖单向无环；核心能力 owner 落在 biz 且展开到可编码粒度。
- entry 层后：handler 只调稳定 biz 行为且不直接触 repository/SQL；context/timeout 透传；错误→HTTP 码映射齐全；与概要时序图一致。
- 横切后：config 键/env 前缀/secret 引用被引用方闭合；external 协议/鉴权/超时合同闭合；runtime 生命周期（New/Run/Shutdown）与信号处理闭合；合规依据（鉴权/数据采集/三方域名）逐单元可定位。

### 5.5 完成判定输入

目录级完成 = 全部 chapter_target 的 `chapter_status=passed_by_method_evidence` + 五个层级 checkpoint 通过 + gate 章节闭合（索引↔文件双向）通过。

## 6. 分层依赖硬约束与禁止补造清单（详细阶段红线）

### 6.0 Go golden-path 硬规则（不可豁免，贯穿全类型）

详细设计正文不得违反以下 golden-path 锁定规则；违反即 §8 的 P1 阻塞：

1. **框架轻量**：入口与路由只用 `net/http` ServeMux；禁止在详细设计中引入 gin/echo 等重型框架（除非 project-conventions API 风格槽位已显式选定并经概要技术决策确认）。
2. **分层依赖律**：`handler(transport) → service → repository → domain`，严格单向、无循环；除 `domain` 外不跨 internal 兄弟包导入。`entry-api` 不直接调 `repository-data`；`biz` 不直接写 SQL；`domain` 不导入任何 internal 兄弟包、无 I/O、无副作用。
3. **错误处理范式**：服务级 sentinel errors（`var ErrXxx = errors.New(...)`）+ `fmt.Errorf("%w: ...")` 链式包装 + `errors.Is()` 检查。详细设计的错误表必须落到这三件套，不得用裸字符串错误或自定义错误码体系替代。
4. **启动/关闭契约**：`main()` 控信号 → `app.New()` → `app.Run()` → `app.Shutdown()`；handler 接收 `context.Context` 支持 timeout。`runtime` 类必须展开这条生命周期，`entry-api` 必须证明 context 透传。
5. **配置范式**：环境变量 + 默认值，集中 `config.Load()`；env 前缀区分服务（如 `CONTROL_API_*`）。`config` 类必须落到 env 变量名 + 默认值 + 前缀，业务规则默认值仍归 `biz`/`domain`。
6. **包隐私约定**：`internal/` 私有，跨服务契约放 `packages/contracts/`。`external` 的跨服务契约只落 `packages/contracts/`。
7. **命名后缀**：PascalCase 导出标识符；推荐 `XxxService`（biz 行为接口）、`XxxRepo`（数据访问）、`ErrXxx`（sentinel）；禁止把数据库表名、SQL 片段当作 biz 合同。

项目约定槽位（project-conventions，可按服务调整且必须先在概要技术决策确认）：DI 框架（当前无 → 可 wire）、ORM（当前原生 SQL + `lib/pq` + PostgreSQL → 可 ent/sqlc）、日志（当前标准 `log` → 可 slog/zap）、测试框架（当前 `testing` → 可 testify/ginkgo）、API 风格（REST JSON → 可 gRPC）、DB 驱动、lint（golangci-lint）、文档生成（当前无 → 可 Swagger/OpenAPI）、会话鉴权（HMAC-SHA256 签名 cookie + bcrypt，当前自实现）。详细设计取值不得偏离已确认槽位。

### 6.1 各类型依赖边界

- `entry-api`：只能调 `biz`（`XxxService` 接口）；禁止直接调 `repository-data`、直接写 SQL、承载业务规则/业务终态。可读 `config`（启动期注入）、可调 `domain`（请求→实体转换、纯校验）。
- `biz`：调 `repository-data`（`XxxRepo` 接口）与 `domain`；禁止调 `entry-api`（反向）、禁止持有 `*sql.DB` 直接执行 SQL（数据访问归 repository-data）、禁止在 biz 内拼 HTTP 路由。可调 `external` adapter（出站）。
- `repository-data`：调底层 DB 驱动（`lib/pq`/`database/sql`）与 `domain`；禁止调 `biz`/`entry-api`、禁止承载业务规则与业务决策（只做 CRUD/查询意图 + 错误转换）。
- `domain`：纯包，禁止导入任何 internal 兄弟包、禁止 I/O、禁止持有依赖；只定义实体/值对象/sentinel/纯函数。
- `config`：被各层在启动期读取；禁止反向依赖业务包、禁止存明文 secret（只存 env 变量名/引用）。
- `external`：本系统出站调用外部系统的合同；禁止把本系统自有业务能力伪装成外部依赖；跨服务契约落 `packages/contracts/`。
- `runtime`：组合 app 生命周期与进程拓扑；禁止写部署脚本、流水线、云控制台步骤、运维 Runbook 正文。

### 6.2 禁止补造清单（红线）

- 不得新增概要归属表之外的结构（发现缺口 → 回退概要补归属，再回详细）。
- 不得变更概要已定的 owner、技术决策、scope。
- 不得把 `technology_decision_handoff[]` 中"未选定"的决策（含 DI/ORM/日志/测试/API 风格槽位）在详细阶段私自拍板。
- 不得写实现代码/伪代码超过签名级（方法签名、struct/type 定义、interface 定义为上限；不写函数体、不写完整 SQL、不写迁移脚本正文、不写 `wire.Build` 细节）。
- 命名、目录、序列化、错误范式等取值不得偏离 golden-path 与 project-conventions 槽位。
- 不得违反 §6.0 任一硬规则（重型框架、跨层/反向/循环依赖、非 sentinel 错误体系、缺生命周期、明文 secret）。

## 7. 完成判定与 Gate

详细设计可进入编码，当且仅当（G1~G5 两轨共用；G6~G7 仅 full 链强制）：

- **G1** 承接索引的每个条目都有对应详细设计单元，无遗漏；归属表全部 owner 被至少一个 UNIT 覆盖。
- **G2** 每个单元的合同八问完整；字段/接口/状态/sentinel error 可追溯到概要 owner；满足 §3.1 粒度标准；分层依赖律（§6.0）与错误范式（§6.0）在正文中可验证。
- **G3** 每条行为有测试映射（八问之 7），覆盖成功路径 + 全部失败路径（含 context 超时、sentinel error 分支）。
- **G4** 涉及鉴权 / 会话 / 数据采集 / 三方域名 / PII 的单元附合规依据（HMAC-SHA256 签名 cookie + bcrypt 等鉴权范式可定位）；无私有 API、无动态执行类设计、无明文 secret。
- **G5** 八问之 8（不得补造清单，含分层越界禁止项）逐单元存在。
- **G6** 章节闭合：索引↔chapters/ 文件双向闭合；每章符合 §4 骨架合同；pending L2 命中项（`domain`/`config`/`external`/`runtime`）豁免齐全。
- **G7** chapter_loop 证据：逐章 `chapter_status=passed_by_method_evidence`，五个层级 checkpoint 全过，无"一轮全量生成"迹象（多章雷同骨架、无单元级实质内容）。

### 7.1 编号断链拦截口径（gate 结构检查可执行）

`guru_gate.py` 的详细阶段结构检查按以下口径拦截，writing/review 必须按此自检：

- **行为承接断链**：UNIT 的八问 1 引用的 `BHV-NNN` 必须存在于 prd——幽灵引用（prd 无此 BHV）与孤儿行为（prd 有 BHV 但无任何 UNIT 承接）均拦截。
- **索引↔文件双向闭合（full 链）**：承接索引每条 `chapter_target` 必须有对应 `chapters/<slug>.md`；每个 `chapters/<slug>.md` 必须被索引引用——引用缺文件、孤儿章节文件均拦截。
- **归属一致断链**：UNIT 回指的归属表行 owner 必须与该 UNIT 的 `detail_doc_type` 落点层一致（如 `detail_doc_type=biz` 的 UNIT 不能回指归属表中 owner=repository 的行）。
- **分层方向断链**：八问 4 声明的依赖方向违反 §6.0 分层依赖律（反向、跨层、循环）即拦截。
- **trace 四节齐全**：每个 UNIT 必须可被追溯矩阵串起——① 需求五要素（prd BHV 的触发/输入/处理/输出/异常）→ ② 概要归属表 + 第 7 节承接索引 → ③ 详细合同八问 → ④ 实现 trace（实现阶段 `implementation-trace.md` 回指本 UNIT）。任一节缺失或断链即拦截。
- **编号纪律**：行为引用必须是裸 `BHV-NNN` token，设计单元必须是 `UNIT-<slug>` 标题 token；不得写自然语言指代（如"上面那个登录行为"）替代编号 token，否则追溯矩阵无法建链，按断链拦截。

## 8. 审核基线

- 先证据后结论；finding 带文档/章节锚点（`<chapter_target> §<节> UNIT-<slug>`）。
- 严重度：
  - **P1**（阻塞）：违反 §6 红线（含 §6.0 硬规则）、八问缺项、追溯断链（§7.1）、合规缺失、章节闭合失败、分层依赖律违反。
  - **P2**（可局部补）：合同不完整但可局部补，如 sentinel error 枚举不全、错误转换位置缺标、粒度局部不达标、测试映射缺失败路径。
  - **P3**（建议）：表述建议、命名一致性、图标签中文化。
- 互斥分支：前置失败 → 只输出前置缺口；前置通过 → findings + 概况 + 三选一结论（可进入编码 / 带假设可进入 / 不可进入）。
- 详细设计文档无存量豁免（新文档全量合规）；存量豁免仅适用于实现阶段代码。

## 9. 修订形态判定

- **局部修订**：补 sentinel error 枚举、补测试映射、补一条依赖声明、补一张时序图、补一个错误转换位置、补 context/timeout 透传声明。
- **文档级重构**：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档迹象）、分层归属系统性错位（如 biz 大面积直接写 SQL、handler 大面积承载业务规则）、错误范式整体偏离 sentinel 三件套。
- 发现概要缺陷（归属错、索引漏、技术决策/槽位未选定）→ 回退概要修订，禁止在详细阶段就地改归属或私自拍板槽位。

## 10. 不适用场景

本规范不适用于：实现代码与函数体、测试用例正文、SQL 迁移脚本正文、`wire.Build` 装配代码、部署脚本/Dockerfile/CI 流水线、云平台控制台操作、运维 Runbook、监控平台配置细节。这些属于实现阶段（`implementation-trace.md` 回指本阶段 UNIT）或运维阶段产物。
