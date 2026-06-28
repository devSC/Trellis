# Go 后端概要设计 — 单一来源规范（L1）

> 本文件是 Go 后端服务概要设计阶段的唯一权威规则（SSOT）。writing/review skill 只做编排与判定，不得复写本文规则正文。
> 上游硬输入：需求阶段产物（核心能力清单 P0/P1/P2 + 行为规格 + 显式结构化合同来源锚点）。
> 横向依赖：通用方法 SSOT `.trellis/spec/guides/golden-path.md`（Go 分层依赖律 + golden-path 锁定项）+ 目标仓库 `project-conventions.md`（项目槽位）。
> 层级契约：本文（L1）承载规则正文与完成条件；writing/review skill 的 `references/` 只承载编排细则、模板与示例；冲突时 L1 > L2 > references > SKILL.md。
> 方法论来源：本文将中立的 `backend-design-overview-doc-standard` 方法（行为驱动分层归属、能力泛化、技术决策承接、人类可审核架构视图、详细设计承接索引、架构就绪收敛）适配到 Go monorepo 分层（transport/service/repository/domain），并锁定 net/http golden-path 硬规则。

## 1. 装载与硬前置（WX/EX 共用）

执行写作或审核前必须依次确认，任一失败即终止并输出前置缺口：

- P1 本文件可读。
- P2 通用 golden-path 可读（`.trellis/spec/guides/golden-path.md`）——Go 分层依赖律与 net/http 锁定项是归属判定与硬规则校验的基准。
- P3 目标仓库 `project-conventions.md` 可读，且通过其内置校验清单（DI 框架、ORM/DB 驱动、日志、测试框架、API 风格、lint、文档生成、会话/鉴权等槽位已声明取值或显式标注沿用当前默认）。
- P4 需求产物可定位，核心能力清单存在 `P0/P1`（或需求阶段已合法声明 `exception_type=no_p0_p1`）。若需求产物缺失或未达概要准入条件：仍可产出概要草稿，但必须记录**显式假设**（依据、影响范围、验证时点），且 `Capability-to-Architecture Mapping` 标记为 `未建立：需求核心能力输入未满足`，不得宣称"可进入详细设计"。`ai_drafted` 不可作为概要准入状态。
- P5 判轨完成：task.json `guru_chain` 已确定（full/light）；full 链另须确认 `design_package` 路径已声明或将在阶段 0 声明。`guru_gate.py` 按链型自动切换检查口径。

硬规则装载（golden-path 锁定，不可豁免，概要必须按此约束归属与索引，违反即 review P1）：

- 框架轻量：transport 层只用标准库 `net/http` + `ServeMux`，禁用 gin/echo 等重型 web 框架。
- 分层依赖律：`transport(handler) → service → repository → domain`，严格单向、无循环；除 `internal/domain` 外不得跨 `internal/` 子包导入；`service/repository/domain` 不得 import `internal/transport`。
- 错误处理：service 层定义 sentinel errors（如 `ErrValidation`）；跨层用 `fmt.Errorf("%w: ...")` 链式包装；调用方用 `errors.Is()` 判定，不得用字符串匹配。
- 启动/关闭：`cmd/<svc>/main.go` 控信号 → `app.New(cfg)` → `app.Run()` → `app.Shutdown(ctx)`；Handler 接收 `context.Context` 支持 timeout。
- 配置：环境变量 + 默认值，集中 `config.Load()`；env 前缀区分服务（如 `CONTROL_API_*`）。
- 包私有约定：服务私有实现放 `services/<svc>/internal/`；跨服务契约放 `packages/contracts/`。

## 2. 产物合同（按链型分轨）

**轨道判定**：task.json `guru_chain`（`guru_after_create` 创建时默认 `full`）。涉及核心能力主线、外部依赖（数据库/MQ/对象存储/三方 provider/LLM）、跨服务契约、鉴权/数据采集等高架构显著度的需求走**目录级设计包**；轻量链（小迭代分流且获用户同意后显式降级）走任务内单文件 `design.md`。

### 2a. full 链：目录级设计包

- 位置：目标仓库 `docs/designs/versions/vx.y.z/`（版本化，推荐）或 `docs/designs/<feature>/`（非版本化，按需），并写入 task.json `design_package` 字段（相对 repo root）。目录策略二选一必须在 `design-main.md` 显式声明并记录依据（迭代频率、是否并行维护多版本、审计/回溯要求）；未明确时默认版本化并以显式假设标注。
- 多服务边界策略：单服务集中式；多服务自治发布时按服务拆分子目录（对应 monorepo `services/<svc>/`），并保留上层 README 跨服务导航。
- 骨架（概要阶段建立，gate 查存在性）：
  - `README.md` — 仅导航/索引/版本矩阵/追踪入口，不承载事实正文，不得作为详细设计执行基线的权威定义位置。
  - `design-main.md` — 概要主定义，必含本节「必含章节」全部条目。
  - `chapters/` — 详细设计逐章承载区（文件本体在详细阶段产出），命名 `<序号>-<层次名>-<模块名>-design.md`。
- 任务内 `design.md` 退为指针+摘要：链接 design_package，不承载主定义。
- 承接索引每条必须落到章节文件：`chapter_target → detail_doc_type → chapters/<slug>.md`；gate 在详细 Gate 检查索引↔文件双向闭合（引用缺文件、孤儿章节均拦截）。

### 2b. light 链：单文件

概要主定义承载于任务内 `design.md` **§1 概要设计**，必含「必含章节」第 1~9 条（第 5 条架构总览可简化：保留一句话架构 + 一张分层架构图 + 核心 UC 表，系统边界图与时序图策略表在无外部依赖/无异步时可标 `N/A 依据`；第 11 条架构就绪自检可简化为 Gate 前自查，不强制成节）。light 链仍必须保留分层依赖律归属表与详细设计承接索引。

### 必含章节（两轨共用语义）

1. **设计约束与输入**：承接的需求核心能力（逐条引用 P0/P1 编号）、Go 技术栈约束（golden-path 锁定项 + project-conventions 槽位取值）、显式假设清单、向后兼容性决策（见 §2.7）。
2. **行为集合**：行为枚举结果（见 §3）。
3. **归属判定表**：行为 → owner 层（transport/service/repository/domain）→ 归属理由三问（见 §4）。**这是概要的核心产物。**
4. **入口与路由承接**：HTTP 路由（method+path）→ handler → 下游 service 行为的承接关系；非 HTTP 入口（后台 worker/定时任务/消息消费）显式标注其 `entry_kind`；纯库/纯计算服务显式标注 N/A 依据。
5. **架构总览（人审视图）**（full 链必含成节，合同见 §2.5）：一句话架构 + 分层架构图 + 系统边界图 + 核心 UC 表 + UC 承接表 + 时序图策略表。
6. **技术决策承接清单** `technology_decision_handoff[]`：DB 引擎/驱动选型、ORM 槽位、MQ/缓存/对象存储/搜索引入、三方 provider/LLM 调用、跨服务契约协议、游标分页等架构显著决策（合同见 §2.6）。
7. **共享能力归属判定**（按需）：被多个 service 复用且业务无关的技术访问能力是否抽为 Utility（Go 中表现为 `internal/<tech>` 纯函数包或 `packages/` 共享包），判定证据见 §4.3。
8. **详细设计承接索引**：`chapter_target → detail_doc_type` 映射（detail_doc_type 取值见 §6.1 七类）。归属判定表中每个 owner 必须被至少一个索引条目覆盖；full 链每条另附 `chapters/<slug>.md` 目标文件。含详细设计执行基线五字段（见 §6.3）。
9. **未决问题**：显式列出，标注风险等级。
10. **核心能力到架构承接矩阵** `Capability-to-Architecture Mapping`（见 §6.2，可作为第 3 与第 4 之间子节）：逐 P0/P1 能力承接到架构响应、owner 行为、详细索引；P2 走 `p2_ordinary_behavior_trace[]`。
11. **架构就绪自检**（full 链必含成节）：对照 §6 G1~Gn 逐项自评（满足/缺口+闭合计划）；存在未闭合 G 项不得送审概要 Gate。

### 2.5 架构总览（人审视图）合同

架构总览是概要的人类可审核入口——评审者不读全文也能从这一节判断"这个服务长什么样、对不对"。full 链六件套缺一不可：

**① 一句话架构**。固定格式：

> 外部调用方经 `<API Endpoint / 后台触发入口>` 进入 `<svc>`，由 `transport` handler 归一化请求后分发给 `<核心 Service 行为>`，按需经 `<Repository>` 访问 `<PostgreSQL / 外部依赖>`，以 domain 结构与 sentinel error 语义收口为 HTTP 响应或状态推进。

**② 分层架构图**（mermaid graph）。要求：

- 用 subgraph 表达 Go 分层（transport / service / repository / domain / 横切如 config·auth）；层内列出本设计涉及的真实组件名（`UserHandler`、`UserService`、`UserRepository`、`domain.User` 等）。
- 箭头只表达依赖方向，且必须符合 Go 分层依赖律（`transport → service → repository → domain`；domain 被依赖不依赖任何上层；config/auth 横切被依赖不依赖业务）。
- 图中出现的组件必须与归属判定表的 owner 一一对应；图中不得出现归属表之外的组件，也不得出现违反单向依赖律的箭头（如 `repository → service`）。

**③ 系统边界图**（mermaid graph，与分层架构图是两个不同产物，不得互替）。要求：

- 表达系统内外边界：外部调用方/前端/上游服务、当前 `<svc>` 边界、Entry（API/后台触发）、service/repository、PostgreSQL/对象存储/MQ、跨服务契约方（`packages/contracts`）、外部 provider/三方 API、运行/发布边界。
- 数据/权限出入边界标注方向与用途（请求进入、会话鉴权门禁、状态写入 DB、外部查询、回调/事件）。
- 外部系统不得画成本服务内部组件；其协议/鉴权/SLA 需详细展开时承接到 `external`。

**④ 核心 UC 表**。从需求验收场景提炼可观测用例，列定义：

| 列 | 含义 |
|----|------|
| `uc_id` | UC-<序号>，创建后不复用不重排 |
| `uc_title` | 业务视角一句话（动词开头） |
| `actor_or_trigger` | 外部调用方 / 系统事件 / 定时调度 / 生命周期 |
| `source_refs` | 需求来源锚点（prd 章节或 BHV 编号） |
| `business_goal` | 可验证的完成态 |
| `priority_or_core_capability_refs` | 对应核心能力 P0/P1 |

**⑤ UC 承接表**。逐 UC 回答"谁实现它"，列定义：

| 列 | 含义 |
|----|------|
| `uc_id` | 对应④ |
| `api_or_background_entry_refs` | 涉及的 HTTP 路由 / 后台触发入口（含 method+path 或 consumer/job 名） |
| `bhv_refs` | 承接的 BHV 编号（必须存在于 prd） |
| `owner_refs` | 归属表中的 owner（Handler/Service/Repository/domain 行为单元） |
| `data_external_runtime_refs` | 涉及的 DB 实体 / 外部依赖 / 运行边界 |
| `index_refs` | 第 8 节承接索引的 chapter_target |

**⑥ 时序图策略表**。逐 UC 声明时序图交付策略，列定义：

| 列 | 含义 |
|----|------|
| `uc_id` | 对应④ |
| `strategy` | `独立` / `合并` / `豁免` 三选一 |
| `sequence_section` | 可定位的 `sequenceDiagram` 所在小节锚点（独立/合并必填） |
| `merged_coverage` | 合并图覆盖的 uc_id 清单（合并时必填） |
| `exemption_reason` | 豁免理由 + 最小行为链（豁免时必填） |

**时序图回填硬约束**：送审概要 Gate 前，非豁免 UC 必须有可定位的真实 `sequenceDiagram`（mermaid），覆盖 `外部调用方 → API Entry/后台触发 → Service → Repository → PostgreSQL/外部依赖 → 返回/状态推进`（按实际链路裁剪），异常/事务边界/异步/重试在图或紧邻说明中表达，步骤编号与文字详述一一对应。外部调用方在图中只能进入显式 Entry，不得直连 service/repository/外部依赖。早期写作可用计划锚点占位，占位状态下不得宣称可送审。

### 2.6 技术决策承接清单合同

`technology_decision_handoff[]` 是所有架构显著技术选择进入详细设计的唯一承接清单。逐条字段，缺一即该条不完整：

| 字段 | 要求 |
|------|------|
| `decision_id` | TECH-<序号> |
| `trigger_source` | `capability` / `technical_difficulty` / `architecture_driver` / `p2_ordinary_behavior` |
| `decision_point` | 决策点（如"持久化引擎选型"、"会话鉴权方案"、"列表是否引入游标"、"<svc> 模型 provider 选型"） |
| `candidates` | 候选清单（≥1；只有一个候选时说明为何无备选） |
| `selected` | 选定项，或显式 `未选定`（未选定项禁止详细/实现阶段私自拍板） |
| `selection_status` | `accepted` / `explicit_assumption`；最终概要不得停留在 `needs_validation` |
| `rationale` | 选择理由（回指架构驱动/约束，不得反向用选型倒推驱动）；必含备选、选定、原因、主要代价/限制 |
| `selected_stack_boundary` | 选定的引擎/库/中间件/provider/model/协议边界 |
| `runtime_component_boundary` | 该选择在 Go 内的归属：落到哪个 repository/service/transport/纯函数包，构造与依赖方向 |
| `contract_boundary` | 调用方载荷、读写契约或跨服务契约的 owner 与结果校验责任；不适用写 N/A 与理由 |
| `resilience_boundary` | 超时、重试/退避、context 取消、不可重试错误归一与失败收口的概要语义 |
| `credential_strategy_boundary` | 命中外部 provider/LLM/对象存储/云服务时必填：只写 `api_key_env_name`/`credential_ref`/默认凭证链/运行平台身份注入；secret value 永不落文档 |
| `detail_expansion_targets` | 交给详细设计展开的字段/合同（指向第 8 节索引条目 `detail_doc_type + chapter_target`） |
| `compliance_basis` | 涉鉴权/数据采集/三方域名/PII 时必填：最小权限与用途可解释依据；否则写 N/A |

不保存任何 secret value；密钥/凭证只写引用方式（环境变量名 `CONTROL_API_*`、配置引用、运行平台注入）。`config.Load()` 的默认值不得是真实凭证；`.env` 仅本地注入，不是线上配置合同或 secret 来源。出现真实 key/AK/SK/token 即审核 P1。

### 2.7 向后兼容性决策（强制，默认不成立）

向后兼容是架构级决策，默认 `no`，必须由用户显式确认。仅当 `<svc>` 对外提供公开 API/SDK 给旧第三方使用方，或作为 App 服务端需兼容旧版本客户端时，`backward_compatibility_required=yes`。内部 service/repository/domain、`packages/contracts` 跨服务契约默认只描述当前正确契约，不为兼容保留内部历史版本、version 字段或多版本 adapter。最小字段：`backward_compatibility_required` / `confirmation_ref` / `compatibility_scope` / `external_consumer_refs` / `protected_contract_refs` / `compatibility_owner_index_refs`（通常指向 `entry-api`）/ `internal_contract_policy`。未确认时概要可继续草稿，但不得宣称具备进入详细设计条件。

## 3. 行为枚举方法（生成动作）

从需求行为规格出发，按以下顺序枚举行为空间，**禁止从名词/组件出发**（不得先写 `UserManager` 再补行为）：

1. 入口触发（HTTP 请求到达某 method+path、CLI 命令、定时任务触发、消息消费、事件回调）。
2. 业务动作（校验、准入判定、状态流转、计数/限额、结算、跨实体一致性、终态收口）。
3. 数据访问（查询、写入、事务、迁移合同、跨 service 复用的仓储访问）。
4. 技术访问（外部 provider/对象存储/缓存调用、内容摘要、URL 生成等业务无关访问）。
5. 失败路径（校验失败、记录不存在、并发冲突、外部依赖超时、context 取消、鉴权拒绝）。
6. 运行/生命周期（启动 `app.New`、信号触发 `app.Shutdown`、context timeout、连接池耗尽）。

每条行为：`Given <前置> When <触发> Then <后置 + 状态变化 + 错误语义>`，并标注涉及的 domain 实体与持久化状态。

### 3.1 粒度标准（四条，写作与审核共用）

1. **可直接实现**：行为描述具体到详细设计可以直接展开为方法合同（含 ctx、入参语义、出参/error 语义），不需要再分解业务语义。
2. **明确触发与归属**：每条行为能指出触发者（入口/业务/数据/技术/生命周期）与候选 owner 层（transport/service/repository/domain）。
3. **完整链路**：从入口行为出发能追踪到全部下游行为（含失败路径与 sentinel error 归一），无断链。
4. **粒度一致**：同一文档内所有行为的描述粒度一致；出现"处理用户"这类粗粒度行为即不达标。

正反例：

- ✅ `BHV-012 创建用户渠道`：Given application_account_id 已提供 When POST /api/v1/users（已通过 requireAdmin）Then service 校验字段（失败返回 `%w: ErrValidation`）→ 校验关联应用账号处于 active（失败 `ErrValidation`）→ repository 在事务中插入 users 行 → 返回 domain.User；记录不存在时 repository 返回 `ErrNotFound` 由 service 转 404 语义。
- ❌ `BHV-012 处理用户`：Given 用户要操作 When 调用接口 Then 完成。（无前置细节、无失败路径、无错误语义、无状态变化）

### 3.2 行为 ↔ UC 回指

每条 BHV 必须能回指至少一个核心 UC（§2.5 ④）；UC 承接表（⑤）的 `bhv_refs` 与行为集合做双向核对，出现"行为无 UC 来源"或"UC 无行为承接"均为审核缺口。入口行为（transport）必须能追踪到至少一个业务行为（service），禁止"入口即业务终点"且无业务语义归属。

### 3.3 编号纪律

每条行为以 `### BHV-NNN <短名>` 标题定义（NNN 数字；创建后不复用、不重排，删除留洞）。归属表、详细设计单元、测试与实现切片对行为的引用一律写 `BHV-NNN` 裸编号 token——这是机器追溯的依据（`guru_gate.py trace-matrix` 据此生成 行为×需求场景×归属×单元×测试×切片 矩阵，断链被 Gate 拦截）。归属判定表逐行以 BHV 编号开头。详细设计单元以 `UNIT-<slug>` 命名（如 `UNIT-user-service`、`UNIT-user-repository`），下游引用写裸编号/裸 slug token。

### 3.4 行为 ↔ REQ-UC 承接（需求源回指 + 命名消歧）

full 链存在正式需求包（版本化组织见需求包标准 single-source §15）时，BHV 标题可在短名前以 `[REQ-UC-XXX]`（可多个，多对多）显式承接需求源场景，形如 `### BHV-001 [REQ-UC-005, REQ-UC-007] 创建订单`。`trace-matrix` 解析该承接生成「需求场景（REQ-UC）」列（行展开），版本级 `trace-aggregate` 据此把多 task 聚合进 `traceability.md`。需求包标准 `--require-req-uc`（或 task.json `require_req_uc:true`）可强制 BHV 必须带 REQ-UC；旧 prd（BHV 无 REQ-UC）默认不拦、列空、不断链。

**命名消歧（强制）**：`REQ-UC-XXX` 是**需求源场景**（requirement source use case，主定义在需求包标准 single-source §6），与本文 §2.5/§3.2 的 `UC-<序号>`（概要设计**架构核心用例**，`uc_id`）是**两套独立编号**，不混用同一字段。`source_refs`/`bhv_refs` 仍指 overview 内的 `UC-<序号>` 与 BHV；BHV 标题的 `[REQ-UC-XXX]` 指需求源。§3.2 的 `BHV ↔ UC-<序号>` 人审映射不因本规则改写。

## 4. 归属判定方法（核心规则）

对每条行为/每个状态，按 Go 分层依赖律判定**唯一 owner**（owner 层只取 transport/service/repository/domain 四层，外部依赖与配置作为被依赖边界标注，不作为业务 owner）：

| 行为/状态类型 | 归属层 | 判定理由模板 |
|--------------|--------|-------------|
| 协议适配、路由分发、请求/响应序列化、鉴权门禁接入、ctx 注入、入口错误→HTTP 状态码转换 | transport（Handler，`net/http` ServeMux） | 薄入口层，只做协议与归一化，不拥有业务规则 |
| 业务规则、校验、准入/状态流转、不变式、跨实体协作、sentinel error 定义、终态收口 | service（`<Domain>Service`） | 业务语义与状态语义 owner，持有 `ErrValidation` 等 sentinel |
| 数据访问、SQL/查询、事务边界、错误转换（如 `ErrNotFound`）、跨 service 复用的仓储访问 | repository（`<Domain>Repository`，必经 DB driver） | 数据一致性 owner，唯一接触持久化 |
| 实体结构、值对象、入参/出参 DTO（Params）、纯领域不变式 | domain（`domain.<Entity>` / `<Entity>Params`） | 被各层依赖的纯数据契约，不依赖任何上层、无副作用 |
| 业务无关共享技术访问（对象存储、provider/model 调用、摘要、URL 生成） | Utility 纯函数包（`internal/<tech>` 或 `packages/`，不进 owner 四层主线） | 离开业务域仍成立，业务判定仍回指 service；不参与 DI 主链路 |
| 配置键、env 前缀、默认值、密钥引用 | Config 边界（`config.Load`，横切） | 集中配置合同，被各层读取，不写业务规则 |
| 跨服务契约 message/字段 | `packages/contracts` 契约边界 | 跨服务协议 owner，独立版本化 |
| 外部系统/三方 API/MQ/PostgreSQL 实例 | 依赖边界（Outbound Dependency） | 外部依赖收口，被 repository/Utility 访问，不作为业务 owner |

归属判定表每行必须回答三问：**为什么属于它？为什么不属于别人？为什么需要（或不需要）独立存在？**

硬约束：
- 归属方向不得违反 Go 分层依赖律（如把 SQL 访问归给 service、把业务规则归给 transport、让 repository import service）——违反即 review 直接 fail。
- 一个状态只能有一个写 owner（通常是 service 编排 + repository 落库）；其他层只能读/调用。
- 不得在概要阶段发明 `Manager`/`Helper`/`Util`/`Handler`(非 transport)/`Processor` 等无行为来源的结构（名词先行反模式）。Utility 只能作为纯函数技术能力，不得写成 service 的 direct dependency 组件或 DI/wire 目标（当前项目无 DI 框架，project-conventions 可声明引入 wire）。
- transport handler 之间不得形成运行时依赖链；入口复用只能通过共享中间件（如 `requireAdmin`）、`packages/contracts` 或下游 service 行为间接表达。
- 单行为候选默认可疑：若某候选只有一个行为却被提为独立 service/repository/Utility，必须给出独立边界证据（外部协议、独立事务边界、独立技术资源、跨 service 复用、不独立会让父行为黑盒）；否则回收为父行为的内部步骤。

### 4.1 命名规范（组件与行为）

- **组件名**：定语 + 层角色后缀，体现领域 + 层。层后缀使用本表既有约定：transport 用 `<Domain>Handler`（或单一 `Handler` + 方法 `handle<X>`）；service 用 `<Domain>Service`；repository 用 `<Domain>Repository`；domain 用 `<Entity>` / `<Entity>Params`；Utility 用 `<Tech>` 纯函数包。禁止 `Manager`/`Helper`/`Engine` 等含混后缀。
- **方法/行为名**：动词或动词+宾语，不重复组件名（`UserRepository` 的查询方法命名 `List`/`GetByID`，不是 `ListUser`）。取数动词区分语义：`List`（取多个）/`GetByID`（取必然存在的，缺失返回 `ErrNotFound`）/`Find`/`Fetch`（取可能不存在的）。
- **sentinel error 名**：service 用 `Err<Reason>`（如 `ErrValidation`），repository 用 `Err<Reason>`（如 `ErrNotFound`）；跨层用 `fmt.Errorf("%w: <上下文>")` 包装，调用方 `errors.Is()` 判定。
- **包/目录与序列化风格**：以 `project-conventions.md` 槽位为准（DB 驱动、ORM、日志、API 风格等），本节不覆盖项目级取值。`internal/` 私有、`packages/contracts/` 跨服务契约的约定不可豁免。

### 4.2 行为驱动归属（生成顺序）

第 4 章必须**先**列出候选行为集合（`candidate_behavior_items[]` 或等价），逐项记录 `candidate_behavior_ref / source_refs / behavior_kind（入口触发/业务动作/数据访问/技术访问/配置合同/外部合同/运行合同/父行为内部步骤）/ input_context / output_or_postcondition / owner_decision / owner_landing / decision_basis`，**再**归纳责任单元（UNIT-<slug>）与行为单元。`owner_decision` 必须先完成真实归属判定（transport/service/repository/domain/Utility/Config/contracts/Outbound Dependency/`N/A：仍属父行为步骤`），不得先写组件名再反补行为。

### 4.3 能力泛化与共享能力归属（按需，强制证据可追踪）

当某技术访问被多个 service 复用、或会改变依赖方向/详细展开目标/失败诊断边界时，按"调用意图 → 去业务词汇 → 变化隔离 → 决策归属"判定：业务动作/业务判断留 service；业务无关技术访问（对象存储、provider/model 调用、摘要、URL 生成）抽为 Utility 纯函数包并记录 `utility_scope / used_by / underlying_dependency / business_decision_owner / generalization_basis / usage_anchor_refs / detail_expansion_targets`；配置合同落 Config；跨服务协议落 `packages/contracts` → `external` 或 `config`；运行单元/进程拓扑落 `runtime`。判定证据可放在第 3 章关键取舍、第 4 章责任抽象或第 6 章索引职责边界中；审核只判断证据是否可追踪，不强制专表。Utility 不拥有业务状态、不变式或终态；若同一外部依赖被多个 service 各自封装 SDK 细节，必须抽共享 Utility 或说明不抽取理由。

## 5. 阶段边界（概要不做什么）

概要只闭合：**边界、语义、链路、取舍、索引、技术决策承接**。以下内容禁止在概要展开，发现即属越界：

- 字段级合同、方法签名、struct 字段全集、错误码全集、DDL/迁移 SQL 正文、具体 SQL 查询、API 字段级 schema（属详细设计；通过第 8 节索引承接）。
- SDK/provider 初始化/调用参数、`config.Load()` 具体配置键表、env 取值、secret value（属详细设计/实现，secret 永不落文档；选型与 credential strategy 例外，必须按 §2.6 进入 `technology_decision_handoff[]`）。
- 完整 prompt 正文/模板、运行期变量获取步骤、最终 prompt/messages 组装步骤（LLM 调用时，概要只固定逻辑调用、owner、上下文来源、prompt 详细承接目标）。
- 代码实现、伪代码、`go.mod`/Makefile/wire/ProviderSet/生成代码已存在性作为通过条件（目标 module 路径、proto 根、生成目标可作为设计落点或 `detail_stage_impact`，但不作为概要/详细 Gate 的存在性通过条件；这些产物只在实现阶段创建或回验）。
- 测试用例正文、部署脚本、流水线 YAML、运维 Runbook、监控告警表达式。
- 重新决定需求 scope 或私自拍板未决业务规则（回需求阶段）；把 `technology_decision_handoff[]` 中"未选定/needs_validation"的决策直接写成已选定。

## 6. 完成判定与 Gate

概要可进入详细设计，当且仅当（G1~G5 两轨共用；G6~Gn 仅 full 链强制）：

- G1 行为集合覆盖需求全部 P0/P1 核心能力（逐条可追溯），且每条行为满足 §3.1 粒度标准；P2 已按 §6.2 `p2_ordinary_behavior_trace[]` 普通行为承接。
- G2 归属判定表完整：每条行为有唯一 owner（transport/service/repository/domain）+ 三问理由；无 Go 分层依赖律违例（无反向 import、无业务规则下沉 transport、无 SQL 上浮 service）；net/http 锁定项无违反（无 gin/echo）。
- G3 涉及外部 provider/LLM/对象存储/云服务/鉴权/数据采集的行为，已在 `technology_decision_handoff[]` 标注选型 + credential strategy + 合规依据（最小权限、用途可解释、env/ref/默认链注入，无 secret value）。
- G4 详细设计承接索引非空，按 §6.1 七类 `detail_doc_type` 建模，且覆盖归属表全部 owner（full 链逐条落到 `chapters/<slug>.md` 文件名）；存在业务数据库持久化时必含至少一条 `repository-data`（无持久化时显式声明并标 n/a）。
- G5 未决问题中无高风险项（或已获用户确认带假设进入）；详细设计执行基线五字段（§6.3）齐全且 `stack_profile_ref/project_profile_ref` 为稳定引用（内置用 `builtin:detail-stack/go-wire-go-guru`、`builtin:detail-project/go-guru`）；向后兼容性决策（§2.7）来自用户显式确认。
- G6 架构总览六件套齐全（§2.5 ①~⑥）：一句话架构、分层架构图、系统边界图、核心 UC 表、UC 承接表、时序图策略表，且图中组件与归属表一致，外部调用方只进入显式 Entry。
- G7 时序图策略闭合：非豁免 UC 均有可定位 `sequenceDiagram`；合并图列出覆盖清单；豁免项有理由与最小行为链；无占位锚点残留。
- G8 `technology_decision_handoff[]` 逐条字段完整（§2.6），`selection_status` 均为 `accepted`/`explicit_assumption`（无 `needs_validation`），无"未选定但已被下游引用"的条目；每条 `detail_expansion_targets` 能回指第 8 节 `detail_doc_type + chapter_target`。
- G9 核心能力承接闭环（§6.2）：每个 P0/P1 经 `Capability-to-Architecture Mapping` 回指到 `owner_units + owner_behaviors`，且每个 owner 行为映射到 `detail_doc_type=biz`（Go 中即 service `UNIT-*`）的 `chapter_target`；`detail_wx6_readiness` 为合法通过状态（`pass:established_complete` 或 `pass:not_applicable_by_no_p0_p1`），任何 `fail:*` 不得输出"可进入详细设计"。

### 6.1 详细设计承接索引 `detail_doc_type`（七类，一一映射）

第 8 节每个索引项必须且只能声明 1 个 `detail_doc_type`，并可追踪到 `chapters/` 目标文档，来源可回指（第 2/3/4 章条目），职责边界与禁写边界明确。Go 详细 `detail_doc_type` 权威取值固定为下列**七类**（来源：详细设计 SSOT `detail-structure-single-source.md` §0~§2 的"backend 九类 → Go 七类"裁剪表，不可改动）：

| `detail_doc_type` | 职责边界与禁写边界 | L2 装载 |
|------|------|------|
| `entry-api` | 承接 `internal/transport/http` handler 入口行为（`net/http` ServeMux）：协议边界、参数归一、鉴权门禁接入、context/timeout 透传、下游 service 分发、入口错误→HTTP 状态码转换；CLI 子命令、定时任务、消息消费/事件触发归其 `entry_kind` 子类，共用同一薄入口骨架；不承接业务规则。 | `detail-type-entry-api.md`（v1 提供） |
| `biz` | 承接 `internal/service` 业务核心与状态/能力 owner（`<Domain>Service` 的核心行为、sentinel error、跨实体协作、终态收口、内部能力组件 `IC-*`）。**这是核心能力正文主承接方。** | `detail-type-biz.md`（v1 提供） |
| `repository-data` | 承接 `internal/repository` 数据访问合同 + `db/migrations` canonical 表/迁移（合并为一类）：Repo 读写/事务/查询意图、表结构、索引、迁移合同、错误转换、domain 实体字段语义来源；存在业务数据库持久化时必含至少一条。 | `detail-type-repository-data.md`（v1 提供） |
| `domain` | 承接 `internal/domain` 实体/值对象/sentinel errors/不变量（唯一允许被跨层导入），以及落在被调用包内的业务无关纯函数技术能力；无 I/O、无副作用。 | pending（无 L2，按 L1 合同八问展开并标 `l2_status: pending`，full 链须 L2豁免） |
| `config` | 承接运行配置合同（`internal/config` + `config.Load`、env 前缀、默认值、credential 引用策略、超时/重试 profile、feature flag、校验与失败行为；鉴权会话合同 auth 亦在此或 `biz`）；不写真实 secret。 | pending（无 L2，按 L1 合同八问展开并标 `l2_status: pending`，full 链须 L2豁免） |
| `external` | 承接外部系统/第三方 API/对象存储/模型服务/Webhook 的集成合同（协议、鉴权、请求/响应/错误、SLA/限流、超时重试、出站 adapter 消费边界），以及跨服务 `packages/contracts` 对外契约（跨服务技术封装 contracts 归此或 `domain`）。 | pending（无 L2，按 L1 合同八问展开并标 `l2_status: pending`，full 链须 L2豁免） |
| `runtime` | 承接进程拓扑 + `app.New/Run/Shutdown` 生命周期（`cmd/<svc>/main.go` 启动顺序、信号关闭、context 超时控制、健康检查、资源边界、发布/回滚、环境矩阵）；不写部署脚本与运维命令。 | pending（无 L2，按 L1 合同八问展开并标 `l2_status: pending`，full 链须 L2豁免） |

入口类型映射（强制）：`entry_kind=API Endpoint → entry-api`；`entry_kind=CLI Command → entry-api`（CLI 子类）；`entry_kind=Message Consumer / Scheduled Job / Event Trigger / Background Worker → entry-api`（后台触发子类）。各入口子类均按需引入。每个归属表 owner 必须被至少一条索引覆盖；`technology_decision_handoff[].detail_expansion_targets` 必须能回指本节索引并覆盖实际承担技术合同的目标类型。

### 6.2 核心能力到架构承接矩阵 `Capability-to-Architecture Mapping`（强制）

把需求阶段已达概要准入条件的 P0/P1 核心能力承接到架构响应，不新增顶层章节号。逐 capability 最小字段：`capability_id / capability_priority(P0|P1) / difficulty_focus / complexity_source / design_focus / design_expansion_requirement / architecture_response / scenario_refs / owner_units(UNIT-*) / owner_behaviors(BHV-*) / internal_component_refs(IC-* 或 N/A) / quality_semantics / fallback_semantics / observability_semantics / technology_decision_refs(TECH-* 或 N/A) / detail_owner_plan / detail_index_refs`。`difficulty_focus/complexity_source/design_focus/design_expansion_requirement/architecture_response` 不得为空或只写"见需求"。每个 `owner_behaviors` 必须落到 `detail_doc_type=biz`（service `UNIT-*`）的 `chapter_target`，只落到 entry-api/repository-data/domain/config/external/runtime 支撑索引不成立。

P2 不进矩阵主行，记录 `p2_ordinary_behavior_trace[]`：`capability_id / capability_priority=P2 / source_refs / ordinary_scenario_refs / owner_behavior_refs(service 普通行为) / detail_index_refs(含至少一个 biz) / handoff_mode=ordinary_behavior_trace / no_detail_expansion_reason`。P2 owner 不得落到 entry-api/repository-data/domain/config/external/runtime。不得为进矩阵临时升级 P2 优先级。

进入架构就绪收敛前必须派生 `detail_wx6_readiness`：`pass:established_complete`（所有 P0/P1 字段完整、触发增强语义完整、技术决策引用合法、每个 owner 行为命中 biz chapter_target、P2 trace 完成、技术决策承接完整、LLM 调用逐次承接）/ `pass:not_applicable_by_no_p0_p1`（需求合法声明无 P0/P1）/ `fail:<failure_state>`（如 `semantic_fields_missing`、`owner_behavior_detail_index_incomplete`、`capability_technology_decision_missing`、`technology_handoff_incomplete`、`technology_status_needs_validation`、`p2_trace_missing` 等，回指 §6.1 owner 与 §2.6 字段缺口）。任何 `fail:*` 不得输出"可进入详细设计"。

### 6.3 详细设计执行基线（强制）

`design-main.md` 必须权威承载五字段（README 只能镜像位置提示，不得作为权威定义）：`stack_profile_ref`（内置 `builtin:detail-stack/go-wire-go-guru`，项目自定义用 `project:<相对路径>`）/ `project_profile_ref`（内置 `builtin:detail-project/go-guru`）/ `profile_selection_basis`（回指用户确认/需求目标技术栈/既有实现证据；若 `explicit_assumption` 写明依据、影响范围、实现期回验时点）/ `profile_assumption_status`（`user_confirmed`/`explicit_assumption`/`existing_project_evidence` 单值）/ `detail_stage_impact`（如 Repo 命名、Service 行为、Data Canonical、wire/ProviderSet 若 project-conventions 声明引入）。引用必须稳定可解析，不得写本机绝对路径、Skill 安装路径或缓存路径；profile 只在对话确认而未落 `design-main.md` 时不得判定可进入详细设计。

## 7. 审核基线（review 专用）

- 先证据后结论：每条 finding 必须带章节锚点或明确缺失对象；引用正文时给出可定位的小节/表格行/BHV-NNN/UNIT-slug。
- 严重度：P1（违反 Go 分层依赖律/net/http 锁定项/Gate 项缺失/secret value 落文档，阻塞）；P2（归属理由不充分、索引不完整、图表与归属表不一致、技术决策字段缺失，应修）；P3（表述/一致性建议）。
- 输出互斥分支：前置（§1）失败 → 只输出前置缺口与修复动作，不展开逐章审核；前置通过 → 逐条 findings（severity/location/problem/suggestion）+ 结构概况 + "是否可进入详细设计"互斥结论。
- 存量豁免：仅适用于实现阶段代码违例，**概要文档本身无存量豁免**——新文档必须全量符合本规范。
- 逐章取证矩阵与判级细则的执行口径在 review skill 的 `references/`（编排层产物，不得与本文冲突）。

## 8. 修订形态判定

按 findings 修订前必须先判定缺陷性质（不按改动大小）：

- **局部修订**：补一条行为、补归属三问理由、补一条 `technology_decision_handoff[]` 字段、补一条承接索引、补一张图、回填 `Capability-to-Architecture Mapping` 引用、改措辞 → 在原文档上直接闭合缺口，并验证不引入新责任单元体系、并行归属规则、跨章边矛盾或详细设计越界。
- **文档级重构**：归属模型错误（owner 大面积错位、违反分层依赖律）、行为枚举从名词倒推、Utility 误归为业务 owner 或 service 误抽为 Utility、索引与归属表系统性脱节、架构总览与正文两套口径、技术决策承接模型错误、核心能力承接主线错误 → 先修正正向结构/责任边界/能力归属/技术决策承接/详细设计索引，再补齐 G1~Gn 证据，禁止用局部补丁或旁路表格掩盖错误模型。审核发现上游缺陷（需求行为缺失/矛盾）→ 回退需求阶段修订，禁止在概要补造业务规则。
