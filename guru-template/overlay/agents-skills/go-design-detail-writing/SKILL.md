---
name: go-design-detail-writing
description: 用于把 Go monorepo 后端概要设计展开为可编码合同（详细设计）。full 链按 directory_precheck + chapter_loop 执行：WX-1~WX-6 前置检查通过后，按 Go 分层写作顺序（domain→repository-data→biz→entry-api→横切）逐章/小批次（每批 1~3 章）生成 chapters/<slug>.md，每批立即自动 review 并修复闭环，层级完成后跑 checkpoint；light 链同口径展开 design.md §详细。每个设计单元按合同八问 + 章节正文骨架撰写（UNIT-<slug> 编号、签名级接口、逐行为输入/输出表、mermaid 时序、异常表、测试映射）。按当前批次命中的 doc_type 读对应 L2（entry-api / biz / repository-data，其余 pending 类型按 L1 八问展开并标注 l2_status: pending）。规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT 与 `.trellis/spec/guides/golden-path.md`。
---

# Go 后端详细设计撰写

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载详细阶段规则正文、章节骨架与完成条件；L2（`detail-type-{entry-api,biz,repository-data}.md`）承载类型差异与 Go 硬约束；golden-path（`.trellis/spec/guides/golden-path.md`）承载分层依赖律、各层迷你路径、错误处理范式、启动/关闭契约与禁止清单；本 SKILL.md 只做装载顺序、前置检查、chapter_loop 编排与输出要求，不重定义任何规则正文。冲突时 **L1 > L2 > golden-path 引用注解 > project-conventions 槽位取值 > 本文件**。
>
> 职责边界（与官方 trellis 工具区分，避免越权）：
> - 本 skill = **设计写**：承接 prd（`### BHV-NNN`）与概要承接索引产出 design 详细章正文（`chapters/<slug>.md` 或 light 链 `design.md §详细`），只做执行编排与正文落地。
> - **`trellis-brainstorm`**（官方）：在写作之前做需求/方案发散与收敛，产出概要可承接的 owner、技术决策、scope；本 skill 不发散方案、不替它拍板归属。
> - **设计审 = review evidence + detail 人工确认 Gate**（`go-design-detail-review` + `guru_gate.py record-review detail` + `guru_gate.py confirm detail`）：详细设计写完后由审核 skill 判定**能否进入编码下一阶段**（互斥三选一结论 + 两次 clean review evidence + 终端 confirm detail 收口），是阶段间的人工放行闸门。本 skill 不出放行结论，写完即转送审。
> - **`trellis-check`**（官方）：是**实现后的代码质检**（编译/vet/lint/test/合规证据），口径是「已写的代码对不对」；本 skill 是「编码前的设计合同对不对」，二者阶段不同、对象不同，互不替代。

## 目标

- 把概要的 owner 与承接索引展开为可直接编码的合同：每个设计单元（`UNIT-<slug>`）回答合同八问、正文符合 L1 §4 章节骨架、粒度满足 L1 §3.1（可直接实现 / 明确调用关系 / 完整调用链 / 粒度一致）。
- full 链按 Go 分层写作顺序逐章/小批次推进并自动审修闭环——**禁止一次性全量输出全部章节**（必然退化为大纲级薄文档）。
- 只承接概要已决定的 owner、技术决策与 scope；缺口一律回退概要，**禁止在详细阶段补造**业务规则、状态机、SQL、事务边界、provider/SDK 选型或 project-conventions「待定」槽位取值。
- 全程严守 golden-path 红线：`net/http ServeMux` 唯一框架（禁 gin/echo）、分层 `transport → service → repository → domain` 严格单向无环、sentinel + `fmt.Errorf("%w: …")` + `errors.Is()` 错误范式、`app.New/Run/Shutdown` 生命周期 + handler 接 `context`、`config.Load()` 集中配置、`internal/` 隐私、跨服务契约只走 `packages/contracts/`。

## doc_type 全集与 L2 装载矩阵（详细阶段承接索引取值）

> 概要承接索引 `chapter_target → detail_doc_type` 的 doc_type 取下表之一。**只对当前批次命中的 doc_type 读对应 L2**，不为后续章节预加载无关类型。

| detail_doc_type | owner 层 / 覆盖对象 | L2 文件 | L2 状态 |
|-----------------|--------------------|---------|---------|
| `entry-api` | transport — `internal/transport/http` handler 入口：路由/`ServeMux`、请求解析、JSON 编解码、状态码映射、`context` 透传 | `.trellis/spec/harness/detail/detail-type-entry-api.md` | **v1** |
| `biz` | service — `internal/service` 业务规则/状态机/编排、入参校验、sentinel error 定义与 `%w` 包装、事务边界决策 | `.trellis/spec/harness/detail/detail-type-biz.md` | **v1** |
| `repository-data` | repository — `internal/repository` 数据访问合同、原生 SQL/驱动、行映射、`ErrNotFound` 转换；含 `domain`/Data 字段级落盘语义承接 | `.trellis/spec/harness/detail/detail-type-repository-data.md` | **v1** |
| `domain` | domain — `internal/domain` 业务实体、值对象、参数结构体（`CreateUserParams` 等）、序列化 tag | 无（pending） | pending |
| `config` | — `internal/config` env 装载、默认值、env 前缀（按服务区分，如 `<SVC>_*`）、校验；secret 引用边界 | 无（pending） | pending |
| `external` | — 外部 provider / 第三方 API / SDK client / outbound 集成契约、credential strategy、调用模式、限流/SLA | 无（pending） | pending |
| `runtime` | — `internal/app` + `cmd/<svc>/main.go` 装配（`New/Run/Shutdown`）、信号处理、连接池参数、线上注入/短期凭证、部署契约 | 无（pending） | pending |

- 命中 **pending** 类型（`domain`/`config`/`external`/`runtime`）：按 L1 合同八问展开，正文头部标注 `l2_status: pending`；**full 链**须显式 `L2豁免：<doc_type> 理由：…`（见 WX-6），否则停止、提示先补 L2 或写豁免；light 链按 L1 八问展开并标注 `l2_status: pending` 即可。
- doc_type 取值与 L1 §2 / `harness/index.md` 七类同步维护；本文件不另行枚举类型差异规则。

## 最小输入与自动补全

输入参数均可省略，省略时按默认推进：

- `chapter_target`：本轮只写一个概要承接索引目标；必须属于 `chapter_target → detail_doc_type` 目标集合。
- `chapter_batch`：本轮写多个明确列出的目标（≤3 章）；必须全部属于目标集合，且批次足够小，能只装载命中的 L2 与上下文。
- `partial_scope`（`chapter_subscope` / `behavior_subset`）：仅在已指定 `chapter_target` / `chapter_batch` 后，收窄当前 canonical 目标内部的本轮覆盖项（多 route/method 子集、多 entity 子集、runtime 单元子集等）；**只收窄不扩展**，未覆盖项必须显式回填 `not_covered_items[]`，并记 `canonical_publish_status=not_applicable_by_partial_scope`。
- 默认（全部省略）：进入自动逐章模式——按 §执行流程的推荐写作顺序生成 `chapter_sequence`，取下一个未通过或受影响后失效的目标作为当前批次；不得一次性输出全部目标正文。

需求证据只从概要已显式引用的锚点（`source_anchor` / 场景 id / 第 6 章承接索引来源锚点）读取最小片段；**不直接拿需求自然语言改变** `chapter_target` / `detail_doc_type` / owner / 技术决策 / scope。概要已指向的显式结构化合同（`structured_contract_source_refs` / `field_schema_source_refs`）必须作为当前类型的正式承接输入；第 4 章 Scenario/Flow 只能作为场景证据，不能单独形成 owner/scope/trigger。

## 装载顺序（硬前置，任一失败即终止）

1. 读 L1：`.trellis/spec/harness/detail/detail-structure-single-source.md`；不可用 → 终止并提示先安装 guru-go-backend spec 模板。
2. 读 golden-path：`.trellis/spec/guides/golden-path.md`（分层依赖律 / 各层迷你路径 / 错误处理范式 / 启动关闭契约 / 禁止清单），确认本批不触碰锁定红线。
3. 读项目约定：`.trellis/spec/conventions/project-conventions.md`，并通过其内置校验清单 **C1~C5**（元信息五字段、SLOT-01~17 齐全且待定 ≤2、每个已填槽位 ≥1 条代码证据、取值不与硬规则冲突、SLOT-17 存量违例清单存在）；任一不过 → 停止，先定槽位。
4. 定位概要主定义（full=`design_package/design-main.md` 第 6 章承接索引；light=`design.md §概要`），建立 `chapter_target → detail_doc_type（→ 目标文件名）` 目标集合。
5. **只对当前批次命中的 doc_type** 读对应 L2（`detail-type-entry-api` / `detail-type-biz` / `detail-type-repository-data`）；命中 pending 类型按 L1 §3 八问展开并标注 `l2_status: pending`（full 链须 `L2豁免` 声明，见 WX-6）。
6. 需要逐类写法细则、章节模板或时序图示例时再读 `references/chapter-guide.md` / `references/examples/`；该文件只提供编排提示，不替代 L1/L2/golden-path。

## WX 前置检查（directory_precheck，full 链；任一失败 → 停止并输出缺口与概要修订动作）

- **WX-1 输入键完整**：task.json 含 `guru_chain` 与（full 链）`design_package`；缺失 → 执行级错误，提示补判轨。
- **WX-2 路径边界**：`design_package` 目录存在且 `chapters/` 已存在；目标文件名均落在 `chapters/` 内（词法检查，**不自动创建缺失目录**——缺 `chapters/` 属概要骨架缺口）。
- **WX-3 承接索引**：design-main 第 6 章承接索引存在、非空，可建立完整非空的 `chapter_target → detail_doc_type` 映射（每条有 doc_type 与目标文件名）；缺失/为空 → **硬阻断，回退概要**。
- **WX-4 概要 review evidence 已达标**：`python3 .trellis/scripts/guru/guru_gate.py status` 显示 overview 当前 digest 已有两个不同 `run_id` 的 clean review；未达标 → 停止，提示先运行概要 review 并用 `record-review overview` 留痕。
- **WX-5 项目约定就绪**：`project-conventions.md` 的 C1~C5 已通过且本批引用的 `SLOT-NN` 槽位均非「待定」（命中待定槽位会改变本批合同取值时 → 停止，先定槽位；不在详细阶段拍板未选定槽位如 ORM/鉴权/驱动）。
- **WX-6 承接源状态**：本批引用的 `technology_decision_handoff[]` 条目均为「选定」（未选定 → 回退概要，禁止详细拍板）；命中 `external` 类型时，provider/external owner、SDK/client、调用模式、runtime profile、credential strategy、异步生命周期、成本/限流/SLA 驱动来源必须均来自概要已落盘的技术决策，缺一即回退概要、禁止本地补造；本批命中 pending L2 的 doc_type 均有 `L2豁免：<doc_type> 理由：…` 声明（无豁免 → 停止，提示先补 L2 或写豁免）。

light 链执行 WX-3/WX-4/WX-5/WX-6 的等价检查（索引在 `design.md §概要`；产物写 `design.md §详细`）。

## 执行流程（chapter_loop）

1. **建立写作顺序**（Go 分层，依赖 `transport → service → repository → domain`，**写作自底向上**）——按 L1 §5.2 把目标集合排序：
   - ① `domain`（实体/值对象/参数结构体——下层共享类型的主语义先稳定）；
   - ② `repository-data`（数据访问合同 + 字段级落盘语义，承接 domain 实体）；
   - ③ `biz`（service 业务规则/状态机/编排，承接 repository 接口与 domain 类型）；同一 feature 的 service 与其直接 repository 同批优先；
   - ④ `entry-api`（transport handler，把外部 HTTP 输入映射到已稳定的 service 行为）；
   - ⑤ 横切（`config` / `external` / `runtime`，按支撑合同关系处理；无序时先写一等支撑合同再写运行/部署契约）。
   - owner 层只能是 `transport / service / repository / domain` 四者之一；**禁止跨层、保持单向、无循环**——发现归属错误回退概要修订，不就地改。
2. **确定当前批次**：按输入参数或自动取下一批（1~3 章）；批次必须属于第 6 章承接索引目标集合，并**只加载当前批次命中的 L2、概要锚点、已完成章节锚点摘要、概要已指向的最小需求反向校验证据与必要示例**。
3. **逐章生成正文**：按 L1 §4 章节骨架合同撰写目标文件 `chapters/<slug>.md`；每个 `### UNIT-<slug>`（kebab-case，体现服务+层角色，如 `UNIT-user-service`/`UNIT-user-repository`/`UNIT-users-handler`）按合同八问作答，L2 命中时叠加类型差异规则。每个设计单元正文落地以下骨架（细则与样例见 `references/chapter-guide.md`）：
   - **承接哪些行为**：逐条引用存在于 prd 的裸 `BHV-NNN`（`entry-api` 逐 `route + method` 各绑一个行为；`biz` 每行为映射 `<Domain>Service` 一个公开方法）；无承接或幽灵引用被 Gate 断链拦截。
   - **签名级接口**：Go 方法/函数签名（biz/repository 首参恒 `ctx context.Context`、返回值末位恒 `error`；entry-api handler 形态 `func(w http.ResponseWriter, r *http.Request)` 并把 `r.Context()` 透传 service）；domain 给结构体定义 + 序列化 tag。**不写超过签名级的实现代码/伪代码**。
   - **逐行为输入/输出表**：entry-api 输入按 `path/query/header/body/context` 五类来源**分列**逐字段（路径/Go 类型/必填/来源/入口校验/映射目标）；biz 输入/输出各给参数表（参数/类型/取值域·约束/必填）；可穷举字段用 Go 具名枚举（`iota`/字符串常量）+ 显式 JSON 序列化口径，禁裸魔法值。
   - **mermaid 时序**：每个核心行为给一张 `sequenceDiagram`，画出 handler→service→repository→（domain/external）的完整调用链与关键状态/结果节点。
   - **异常表**：逐行对应一条失败路径——entry-api 给「入口校验失败 / service sentinel error / 兜底未知错误」三态到 HTTP 状态码 + 错误响应体映射；biz 给每个 sentinel error（`var ErrXxx = errors.New(...)`）的业务可恢复/系统不可恢复区分与 `%w` 包装/转换位置（`[SLOT-13]`）；repository 给 `ErrNotFound` 等转换点。
   - **测试映射**：每条行为成功 + 全部失败路径各一条 unit test 行，逐行挂 `BHV-NNN`/`UNIT-<slug>`（entry-api 用 `httptest`+mock service；biz mock repository/下层 service；repository 走集成测试口径）；写不出测试点的行为视为粒度不达标，回第 3 步。
   - **读写状态 + 依赖正反面 + 失败收口 + 后置事件 + 不得补造**：按八问其余各问就地作答（写 owner 与概要一致；依赖正反面都写防越层，`direct_dependencies[]` 形成 `依赖 → NewXxx 构造入参 → 字段赋值 → usage_refs` 闭环，Utility 纯函数调用不入依赖清单；事务边界三选一给结论）。暂无法回答的问题写入「未决问题」而非留空或编造。
   - go-guru profile 命中时，Repo 生成 / `PropertyFilter`/`PageRequest`/`WithTx` / ProviderSet/Wire / proto 生成等框架细节正文只放 `framework_reference_ref` 回指知识库，不展开生成方法表。
4. **批内自动 review（不等用户）**：对照 L1 §5.3 清单逐项核——章节骨架符合性（八问四机检标记齐全：承接行为/失败收口/测试映射/不得补造）、八问完成条件、粒度四条（L1 §3.1）、依赖与概要归属一致、分层依赖律单向无环、错误范式（sentinel + `%w` + `errors.Is`）、命中 L2 的类型差异规则、技术决策只承接概要已确认输入。
5. **修复闭环**：有 finding → 按 L1 §8/§9 判定修订形态（P1 阻塞 / P2 / P3）→ 直接修复 → 复查受影响的行为/依赖/跨章引用；规则全部有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。**不以固定次数 clean review 作为通过条件**。
6. **层级 checkpoint**：每完成一个层级跑 L1 §5.4 对应核对——
   - domain 层：实体/值对象/参数结构体主语义稳定，无被上层重定义；
   - repository-data 层：repository 接口 ↔ domain 实体 ↔ 字段级落盘语义无 gap、无重复定义、`ErrNotFound` 转换点齐全；
   - biz 层：业务行为 owner 唯一、状态唯一写 owner、capability/P0/P1 承接、对 repository/下层 service 的依赖与 Utility 静态调用锚点闭合、事务边界三分法有结论；
   - entry-api 层：Entry → Service → Repository 的完整 scenario/behavior chain，handler 接 context、错误三态收口、依赖正反面齐全。
   - 上一层级 checkpoint 通过前不开始下一层批次；失效项回到对应批次重走审修闭环。
7. **受影响章节复查**：本批修改触及已完成章节的引用时，复查该引用闭合；已通过章节被改动则其通过状态失效，重新进入当前小批次写审修闭环。
8. **输出本批成果**（见输出要求）。
9. **下一目标推荐**：给出下一批建议与剩余目标清单；全目录完成时转入完成判定（L1 §5.5）并提示送审（见强制约束 12）。

## 强制约束

**破坏性编辑保护**：任何删除、压缩、替换既有详细章节的改动，必须先列 deletion ledger（deleted_category / reason / replacement_location / removes_contract_obligation / reviewer_decision）。接口或后端事实可删除，仍有效的 L1 章节骨架、UNIT/BHV 承接、行为列表、输入输出错误合同、状态/事务 owner、失败收口、测试映射、不得补造清单必须保留、移到命名替代位置，或以 `N/A：<理由>` 显式声明；不得把行为合同压扁成 endpoint/interface 映射表。

1. L3（本 skill）不重定义 L1/L2/golden-path；规则疑义回 L1，引用时给章节号并用结构化字段 `rule_ref=<规范文件路径#章节锚点>`。
2. **禁止一轮全量生成**全部章节；每批 ≤3 章并完成批内审修后才进下一批。
3. 不新增概要归属表之外的结构；不变更 owner / 技术决策 / scope；缺口回退概要（L1 §6），不在详细阶段补造业务规则、状态机、SQL、事务边界、provider/model/SDK/client/invocation_mode/runtime_profile/lifecycle/cost 或 secret 选型。
4. 不写超过签名级的代码（Go 方法/函数签名、`domain` 结构体定义为上限；禁实现体/伪实现）。
5. 命名 / 目录 / 序列化取值 / 库选型按 project-conventions 槽位（`SLOT-NN`）；行为命名按 prd 的 `BHV-NNN`；设计单元命名 `UNIT-<slug>`；下游引用一律写裸编号 token。
6. `partial_scope` 只收窄不扩展，不得解释为新的目标范围来源；未覆盖项必须显式回填 `not_covered_items[]` 并记 `canonical_publish_status=not_applicable_by_partial_scope`，不得静默丢弃或声明 canonical 目标完整通过。
7. 写 owner 必须与概要归属一致，且必为 `transport/service/repository/domain` 之一；发现归属错误或越层（如 handler 直连 DB、repository 反向 import service、状态双写）→ 回退概要修订，不就地改。
8. 每行为测试映射覆盖成功 + 全部失败路径（八问之 7）；写不出测试点的行为视为粒度不达标，回到第 3 步。
9. 涉鉴权 / secret / 外部 provider / PII / 跨服务契约的单元必须落合规依据与边界：secret 只写 `api_key_env_name`/`credential_ref` 引用，正文/yaml/测试 fixture 均不得出现真实 key/AK/SK/token/私钥/`secret_value`（出现即 P1）；跨服务结构体只走 `packages/contracts/`，不在 `internal/` 私自定义；不写制裁地区域名、私有 API、动态执行类设计。
10. 辅助文本中文优先；英文仅限代码标识符、命令、路径、协议字段、框架/库名（`net/http`、`lib/pq`）、缩写（HMAC-SHA256）与原文引用。
11. 中断升级仅限四种情形：概要源缺失 / 业务语义必须人工确认 / 技术决策（含 `external` provider/SDK）未选定或槽位待定 / 修复无法收敛（同一 finding 修 2 轮仍不收敛）；其余情况自动闭环推进，不停下等用户人工 review。
12. 全目录完成后提示送审：加载 `go-design-detail-review`（人工 Gate 判定能否进入编码，区别于 `trellis-check` 的实现后代码质检）；Gate 结论「可进入编码」后先用 `record-review detail` 留下当前 digest 的两次 clean review evidence，再按 config `guru.gate_mode` 完成 `confirm detail` 人工收口——strict 由用户本人在终端跑 `guru_gate.py confirm detail <task_dir>`（agent 不得代跑），soft 在用户对话明确确认后按 `--via-agent --user-quote` 代跑。

## Full/high 实现切片计划（与章节批次解耦）

full/high 全目录完成时，写作者必须在 `implement.md` 建立切片 planning
audit；章节写作批次不是实现切片边界。Go 的
domain→repository-data→biz→entry-api→横切写作顺序，以及
transport/service/repository/domain 的归属与单向依赖律继续生效，但不得机械
要求每个 `UNIT`、`doc_type` 或层各占一个切片。

1. 每个普通切片记录 `owner_unit`、`covered_units`、`read_paths`、
   `owned_paths`、`focused_checks`、`parallel_wave`、`resource_locks`、
   `resource_isolation`、`check_wave`、`independent_commit_value`、
   `rollback_contract`、`review_context_inputs`、`review_context_bytes` 和
   `rejected_merge_candidates`。packet 的 `owner_unit` 保持一个真实标量；
   `covered_units` 可包含多个 Design UNIT。
2. `owned_paths` 按文件级声明，同一 `parallel_wave` 的一个 mutable path
   只能有一个 ordinary slice **mutable owner**；不得以 symbol、函数、类或
   diff hunk 绕过。重叠路径须重新分配唯一 owner 或合并切片。
3. 普通切片默认 `depends_on=[]`。先在已确认 Detail 中冻结跨切片接口、
   schema、digest、错误语义和共享数据结构；只有必须读取另一切片实际输出
   bytes 时才允许非空依赖。UNIT、章节、doc_type、层级或 review 顺序都不是
   实现依赖。
4. 每个被修改的测试文件只能有一个 owner。普通切片只跑 focused checks；
   相同工具状态须以独立 worktree/cache/output 隔离，或记录同一
   `resource_locks` 并分配串行 `check_wave`；不能隔离时合并。full regression
   只交给 Integration。
5. 普通切片默认最多四个。每片必须有可独立提交的用户/合同价值和可独立执行
   的 rollback；缺任一项就拒绝该切片候选并合并。对考虑过但决定不合并的
   组合，在 `rejected_merge_candidates` 逐项写切片集合与保持分离的理由；
   超过四片时还须逐片说明独立价值和 rollback 例外理由。
6. `review_context_inputs` 必须列出 reviewer 实际选中的精确、有序 inventory
   （packet、planning audit、target diff/owned paths、相关 frozen contracts
   与 focused evidence），每项写选择范围和该 snapshot 的 UTF-8 bytes。
   `review_context_bytes` 是各项的精确整数和，必须 `<= 262144`；禁止 wildcard、
   “相关文件”或只写未实测不等式。超限先缩减到上述最小输入，再阻断确认。
7. 普通分组稳定后创建恰好一个 Integration Slice：它依赖全部普通切片，
   packet coverage 覆盖普通 target union；`integration_owned_paths` 单独限定
   实际可写路径。Integration 只补集成字节、跨切片 invariant、full regression
   和最终 spec/sync 检查，不重写普通 owner 的核心字节。
8. Full/high planning 时，从当前 route/platform contract 解析适用的
   `go-implementation-guru-writing` 与 implementation standard，并将其作为
   只读 guidance 校验：其声明契约须消费已确认的 packet/planning audit，且
   ordinary checks 须保持 packet-focused。不得把这些 framework 文件分配给
   application slice，不得依赖固定 `slice_id`、新增 planning-audit 字段或修改
   已确认的 `implement.md`；实际 framework 维护归属与 receipt bookkeeping 由
   相应 framework maintenance task、Integration validation 或 coordinator 处理。

## 输出要求（writing 专属）

每批输出：

- `execution_mode=directory_precheck+chapter_loop`（light 链标注 `light+chapter_loop`）。
- `目标集合解析`（`target_count` 总数 / 已完成 / 本批 `chapter_target` 清单与 `detail_doc_type`；`chapter_sequence` 与 `current_chapter_scope`）。
- `WX 前置状态`（首批输出 WX-1~WX-6 逐项；后续批只报变化；含 `technology_decision_handoff` 与 pending `L2豁免` 状态）。
- `项目约定校验`（C1~C5 结论与本批引用的 `SLOT-NN`）。
- `partial_scope`（如有：`covered_items[]` / `not_covered_items[]` / `canonical_publish_status`）。
- `本批正文`（或落盘文件清单：`chapters/<slug>.md`）。
- `批内自动 review 结果`（finding 数 / 修复迭代次数 / `chapter_status`）。
- `层级 checkpoint 状态`（到达层级边界时输出）。
- `需求反向校验`（`requirement_reverse_validation_evidence` / `requirement_to_overview_gap_findings` 与对应 `overview_revision_action`）。
- `未决问题与升级项`（如有，按强制约束 11 分类）。
- `下一目标推荐`（下一批建议 + 剩余目标清单）。

全目录完成时追加：`完成判定`（L1 §5.5 三要素）+ 上述切片 planning audit +
送审与人工确认指引（强制约束 12）。

前置失败输出：`writing_stage=blocked_requires_overview_fix` + `draft_blockers` 缺口清单 + 概要修订动作 + `recommended_next_step`，不产出正文。

## 参考资料

- 详细阶段中立规范（L1）：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- 类型差异（L2，按命中装载）：
  - `.trellis/spec/harness/detail/detail-type-entry-api.md`（transport / handler，v1）
  - `.trellis/spec/harness/detail/detail-type-biz.md`（service，v1）
  - `.trellis/spec/harness/detail/detail-type-repository-data.md`（repository / data，v1）
  - pending 类型（`domain`/`config`/`external`/`runtime`）：无 L2，按 L1 八问展开 + `l2_status: pending`（full 链须 `L2豁免`）
- 概要承接源（L1）：`.trellis/spec/harness/overview/overview-structure-single-source.md`
- 通用方法 SSOT：`.trellis/spec/guides/golden-path.md`；项目取值与 C1~C5 校验：`.trellis/spec/conventions/project-conventions.md`
- 逐类写法细则、章节模板与样例：`references/chapter-guide.md`、`references/examples/`
- 阶段编排与 Gate 口径：`.trellis/spec/harness/index.md`
- 送审审核 skill（人工 Gate）：`go-design-detail-review`
