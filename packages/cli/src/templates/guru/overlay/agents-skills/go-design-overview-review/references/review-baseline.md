# Go 后端概要审核取证矩阵与严重度判级（references）

> 编排层产物：只承载取证操作与判级细则。规则正文与完成条件（G1~G8）以 L1
> `.trellis/spec/harness/overview/overview-structure-single-source.md` 为唯一来源；分层依赖律与 net/http
> 锁定项以 `.trellis/spec/guides/golden-path.md` 为基准。冲突时 L1 > golden-path > 本文件。
> 本文逐项检查必须能回指 L1 章节号（§1~§8、G1~G8）；不复写规范正文，只规定怎么取证、判到几级。

## 1. 取证准备

- 建立编号索引：`rg -n "BHV-[0-9]+|UC-[0-9]+|TECH-[0-9]+|UNIT-[a-z-]+" <主文档>` 固化行为/用例/技术决策/单元编号清单。
- 建立章节锚点：`rg -n "^#{1,3} " <主文档>` 固化第 1~7 章（及第 8/9/10/11 等附加节）位置。
- 引用证据一律用「章节 + 表格行 / 裸编号」定位（如 `§3 归属表 BHV-021 行`、`§5 ⑤ UC-003`、`§6 TECH-002`），不引用模糊位置。
- full 链额外取证：
  - README.md 是否承载事实正文（承载即 P2，README 只能做导航/索引/版本矩阵——L1 §2a）。
  - 任务内 `design.md` 是否仍承载主定义（承载即 P2 双主定义；full 链 design.md 应退为指针+摘要——L1 §2a）。
- doc_type 取值锁定：第 7 章承接索引只能用 Go 七类 `entry-api / biz / repository-data / domain / config / external / runtime`（L1 §6.1）；出现 flutter/backend 的类型名（如 Entry/API、Biz IC、Utility、Data、Page、State、Widget）即 P1（doc_type 非法）。
- 机检前置：人工取证前确认 `python3 .trellis/scripts/guru/guru_gate.py overview <task_dir>` 已过（结构性缺口由机检定位，人审聚焦语义与归属）；机检未过走前置阻断输出。

## 2. 逐章取证矩阵（按 L1 §2「必含章节」十一条）

| 章 | 应覆盖（L1 锚点） | 取证操作 | 缺口判级 |
|----|------------------|---------|---------|
| 1 设计约束与输入 | 承接 P0/P1 逐条带需求锚点；Go 技术栈约束（golden-path 锁定项 + project-conventions 槽位取值）；显式假设三字段（依据/影响范围/验证时点）；向后兼容性决策（§2.7） | 对照需求核心能力清单做差集；抽查每条能力锚点可定位；核对技术栈引用是否写实际取值（非"待定"）；核对向后兼容默认 `no` 且 yes 时有 `confirmation_ref` | 缺章 P1；P0/P1 锚点缺失 P2；技术栈槽位空置/占位 P2；向后兼容 yes 无用户确认依据 P1 |
| 2 行为集合 | §3 六类枚举（入口触发/业务动作/数据访问/技术访问/失败路径/运行生命周期）+ GWT 三段 + `### BHV-NNN` 标题 + §3.1 粒度四条 + §3.2 行为↔UC 回指 | 逐条核 GWT 三段（前置/触发/后置+状态变化+错误语义）；抽样 ≥1/3 行为做粒度四条判定；核对每条 BHV 能回指 ≥1 UC | 核心能力无失败路径类行为 P1；粗粒度（"处理用户"式）P1；入口行为无下游业务承接 P1；GWT 缺段 P2；BHV 无 UC 来源 P2（影响 G1 升 P1） |
| 3 归属判定表 | §4 唯一 owner（transport/service/repository/domain）+ 三问实质 + Go 分层依赖律 + §4.2 行为驱动归属（先候选行为后单元） | 逐行：owner 在四层内且方向合规？三问有实质内容（非"同上"/"见上"）？写 owner 唯一？是否名词先行（先 `XxxManager` 再补行为）？ | 分层依赖律违例（SQL 上浮 service、业务规则下沉 transport、repository import service）P1（阻断）；外部/前端直连下层越过 transport entry P1；net/http 锁定违反（gin/echo）P1；多写 owner P1；三问空洞 P2；名词先行反模式 P2（影响 G2 升 P1） |
| 4 入口与路由承接 | HTTP 路由（method+path）→ handler → 下游 service 行为；非 HTTP 入口标注 `entry_kind`；纯库标注 N/A 依据 | 路由 method+path 与真实 ServeMux 注册形态可对应；逐路由核失败去向（错误→HTTP 状态码映射）；后台入口有 `entry_kind` | 整章缺失（有 HTTP 入口需求）P1；缺失败去向/状态码映射 P2；后台入口无 `entry_kind` P2；transport handler 间形成运行时依赖链 P1 |
| 5 架构总览（人审视图） | §2.5 六件套 | 见 §3 专项 | 见 §3 专项 |
| 6 技术决策承接 | §2.6 `technology_decision_handoff[]` 字段合同 + credential strategy + 合规依据 | 逐条字段齐全性；`selection_status ∈ {accepted, explicit_assumption}`；`rg -i "api[_-]?key\|access[_-]?key\|secret[_-]?key\|secret_access_key\|access_key_secret\|token=" <主文档>` 扫真实 secret value | 字段缺 P2；涉权限/采集/三方域名/PII 缺 `compliance_basis` P1；出现真实 secret value P1；`.env` 当线上配置合同/secret 来源 P1；云 SDK 支持默认链却要求长期 AK/SK P1；`selection_status=needs_validation` P1（G8） |
| 7 承接索引 | owner 全覆盖 + doc_type 七类合法 + 逐文件 + pending 豁免 | 归属表 owner 集合 vs 索引覆盖集合差集；每条 doc_type ∈ 七类；full 链逐条有 `chapters/<slug>.md`；命中 `domain/config/external/runtime` 是否标 `l2_status: pending` + L2 豁免计划；存在持久化是否含 ≥1 条 `repository-data` | owner 未覆盖 P1；doc_type 非法（含他平台类型名）P1；full 链缺 `chapters/<slug>.md` 文件名 P1；pending 类型缺 `l2_status` 标注或缺 L2 豁免计划 P1；有持久化但无 `repository-data` 条目 P1 |
| 8（即 L1 第 9 条）未决问题 | 风险等级 + 阻塞 G 项 | 高风险项是否存在且未关闭/未获用户带假设确认 | 高风险未关闭且无带假设确认 P1（G5） |
| 核心能力承接矩阵 `Capability-to-Architecture Mapping`（L1 §6.2） | 逐 P0/P1 字段非空；`owner_behaviors` 落到 `biz` chapter_target；P2 走 `p2_ordinary_behavior_trace[]`；派生 `detail_wx6_readiness` | 逐 capability 核 `difficulty_focus/complexity_source/design_focus/architecture_response` 非空非"见需求"；核每个 owner 行为命中 `detail_doc_type=biz`；核 `detail_wx6_readiness` 状态 | 矩阵未建立（需求 P0/P1 存在却缺）P1；字段空/占位 P1（语义字段缺）；owner 行为只落 entry-api/repository-data/domain/config/external/runtime 支撑索引 P1；`detail_wx6_readiness=fail:*` P1（G9） |
| 架构就绪自检（L1 §2 第 11 条，full 链必含） | G1~G8 逐项自评 + 证据 | 自检结论与本次审核结论交叉核对 | full 链缺自检节 P1；自检与实情不符 P1 |
| 详细设计执行基线（L1 §6.3，落在第 1/7 章） | 五字段 + 稳定 profile ref | `stack_profile_ref`/`project_profile_ref` 为稳定引用（`builtin:...` 或 `project:<相对路径>`）；非本机绝对路径/缓存路径；`profile_assumption_status` 合法 | 五字段缺 P1（G5）；profile ref 为本机绝对路径/缓存路径 P1；只在对话确认未落 design-main.md P1 |

light 链口径（L1 §2b）：第 5 章可简化为一句话架构 + 一张分层架构图 + 核心 UC 表，系统边界图与时序图策略表在无外部依赖/无异步时标 `N/A 依据`；G6~G8 标 `N/A(light)` 并说明简化口径已满足。light 链仍必须保留归属判定表与详细设计承接索引——缺这两者即 P1。

## 3. 架构总览六件套专项取证（G6，第一取证对象）

| 件 | 取证操作 | 缺口判级 |
|----|---------|---------|
| ① 一句话架构 | 是否按 L1 §2.5 固定格式（外部调用方经 Entry 进入 svc → transport handler 归一化 → 核心 Service 行为 → 按需 Repository 访问 PostgreSQL/外部依赖 → domain 结构与 sentinel error 收口）；组件为真实名（如 `UserHandler`/`ClientIPLocationService`） | 缺失 P1（G6）；格式自由化但语义完整 P3；组件名非真实/泛化（`XxxManager`）P2 |
| ② 分层架构图 | mermaid graph 存在；subgraph 表达 transport/service/repository/domain（+ 横切 config·auth）；箭头方向全部 `transport → service → repository → domain`（domain 被依赖不依赖任何上层；config/auth 横切被依赖）；图中节点逐个回查归属表 | 缺图 P1（G6）；逆向箭头（如 `repository → service`）P1（分层律）；图含归属表外组件 P1（"图比表大"=补造）；外部/前端节点直连 service/repository P1 |
| ③ 系统边界图 | mermaid graph，与分层架构图是两个不同产物不得互替；表达系统内外边界（外部调用方/前端/上游、当前 svc 边界、Entry、service/repository、PostgreSQL/对象存储/MQ、`packages/contracts`、外部 provider/三方 API、运行/发布边界）；数据/权限出入边界标方向与用途 | 缺图 P1（G6）；与分层架构图互替（只有一张图充当两者）P1；外部系统被画成本服务内部组件 P2；其协议/鉴权需详述但无 `external` 承接 P2 |
| ④ 核心 UC 表 | 列齐全（`uc_id / uc_title / actor_or_trigger / source_refs / business_goal / priority_or_core_capability_refs`）；UC 从验收场景提炼（一 UC 覆盖多 BHV 为常态，非 1:1 重排 BHV） | 缺表 P1（G6）；UC=单 BHV 重排 P2；`source_refs` 缺需求锚点 P2 |
| ⑤ UC 承接表 | 列齐全（`uc_id / api_or_background_entry_refs / bhv_refs / owner_refs / data_external_runtime_refs / index_refs`）；`bhv_refs` 与行为集合双向闭合；`owner_refs ⊆ 归属表`；`index_refs ⊆ 第 7 章 chapter_target` | 任一向断链 P1（G6）；`owner_refs` 含归属表外 owner P1；`index_refs` 指向不存在条目 P1 |
| ⑥ 时序图策略表 | 列齐全（`uc_id / strategy / sequence_section / merged_coverage / exemption_reason`）；策略 `独立/合并/豁免` 三选一；独立/合并有 `sequence_section` 且可定位；合并有 `merged_coverage` 清单；豁免有理由 + 最小行为链 | 缺表 P1（G6）；占位锚点残留 P1（G7）；非豁免 UC 无可定位 `sequenceDiagram` P1（G7）；合并缺覆盖清单 P1；豁免缺理由/最小行为链 P1 |

`sequenceDiagram` 细查（G7，每张抽查——L1 §2.5 时序图回填硬约束）：

- 参与者必须用真实 owner 名（`外部调用方 / UserHandler / UserService / UserRepository / domain.User / 外部 provider`），不得出现外部调用方直连 service/repository/外部依赖的边。
- 调用链覆盖 `外部调用方 → API Entry/后台触发 → Service → Repository → PostgreSQL/外部依赖 → 返回/状态推进`（按实际链路裁剪），回包用虚线。
- 异常/事务边界/异步/重试在图（`alt`/`opt` 块或独立图）或紧邻说明中表达；context 取消/超时收口有体现。
- 步骤编号与图下文字详述一一对应。
- 判级：方向违例（外部直连下层、反向箭头）P1（分层律）；参与者非真实名 P2；缺失败分支表达 P2；编号与详述不对应 P2。

## 4. 七类 doc_type 承接索引取证矩阵（G4，第 7 章逐条）

第 7 章每个索引项必须且只能声明 1 个 `detail_doc_type`，可追踪到 `chapters/<slug>.md`（full 链），来源可回指（第 2/3/4 章），职责边界与禁写边界明确。逐类取证：

| `detail_doc_type` | 承接对象（L1 §6.1） | 取证操作 | 该类专属缺口判级 |
|-------------------|--------------------|---------|------------------|
| `entry-api` | `transport/http` handler 入口行为（含 CLI/定时/消息子类，按 `entry_kind` 标注） | 索引条目能回指第 4 章某路由/后台入口；`entry_kind` 已标；条目职责只写薄入口（协议/归一/鉴权接入/分发/错误→状态码），不写业务规则 | 缺 `entry_kind`（后台/CLI 入口）P2；条目承载业务规则（应属 biz）P2（影响归属升 P1）；HTTP 入口 owner 未被任一条目覆盖 P1 |
| `biz` | `internal/service` 业务核心与状态/能力 owner（核心能力正文主承接方） | 每个 service owner 被覆盖；P0/P1 `owner_behaviors` 命中本类 `chapter_target`；条目职责写业务规则/sentinel/终态收口 | 核心能力 owner 行为未落 `biz` chapter_target P1（G9）；service owner 未被覆盖 P1 |
| `repository-data` | `internal/repository` 数据访问合同 + `db/migrations` 表/迁移（合并为一类） | 存在业务数据库持久化时必含 ≥1 条；条目职责写读写/事务/查询意图/表结构/索引/迁移/错误转换；无持久化时显式声明并标 n/a | 有持久化但无 `repository-data` 条目 P1（G4）；repository owner 未被覆盖 P1 |
| `domain` | `internal/domain` 实体/值对象/sentinel/不变量 + 被调用包内业务无关纯函数（无 I/O 无副作用） | 命中即标 `l2_status: pending` + 按详细 L1 八问展开的 L2 豁免计划；条目职责不写配置默认值/SQL | pending 缺 `l2_status` 标注 P1；pending 缺 L2 豁免计划 P1；domain 条目承载副作用/I/O P2 |
| `config` | 运行配置合同（`internal/config` + `config.Load`、env 前缀、默认值、credential 引用策略、超时/重试 profile、feature flag） | 命中即标 `l2_status: pending` + L2 豁免计划；条目只写 env/ref/默认链/运行平台身份注入，**不写真实 secret**；env 前缀区分服务（如 `<SVC>_*`） | pending 缺标注/缺计划 P1；条目出现真实 secret value P1；`.env` 当线上配置合同 P1 |
| `external` | 外部系统/三方 API/对象存储/模型服务/Webhook 出站集成合同 + 跨服务 `packages/contracts` 对外契约 | 命中即标 `l2_status: pending` + L2 豁免计划；条目写协议/鉴权/请求响应错误/SLA限流/超时重试/出站 adapter 消费边界；credential strategy 与 §2.6 一致 | pending 缺标注/缺计划 P1；外部依赖缺超时/重试收口语义 P2；把对外暴露的回调入口误归 external（应属 entry-api）P2 |
| `runtime` | 进程拓扑 + `app.New/Run/Shutdown` 生命周期（`cmd/<svc>/main.go` 启动顺序、信号关闭、context 超时、健康检查、资源边界、发布/回滚） | 命中即标 `l2_status: pending` + L2 豁免计划；条目不写部署脚本/运维命令 | pending 缺标注/缺计划 P1；runtime 条目写部署脚本/运维命令（越界）P2 |

入口类型映射（L1 §6.1 强制）：`API Endpoint / CLI Command / Message Consumer / Scheduled Job / Event Trigger / Background Worker` 全部归 `entry-api`，按 `entry_kind` 区分子类；映射错位 P2（影响归属升 P1）。已出 3 类 L2（`entry-api`/`biz`/`repository-data`）须能回指对应 L2 承接深度（`detail-type-{entry-api,biz,repository-data}.md`）；回指断裂 P2。

## 5. 跨章一致性取证（L1 §2.5/§3.2/规则 6）

逐项做双向差集核对：

1. 分层架构图组件集合 ⊆ 归属表 owner 集合（多出 → P1，"图比表大"=补造）。
2. 系统边界图外部依赖 ↔ `external`/`runtime` owner / 第 7 章承接条目（外部依赖无承接 → P2；承接指向不存在外部依赖 → P2）。
3. UC 承接表 `bhv_refs` ↔ 行为集合 BHV-NNN（双向断链 → P1）。
4. UC 承接表 `index_refs` ↔ 第 7 章 `chapter_target`（断链 → P1）。
5. `technology_decision_handoff[].detail_expansion_targets` ↔ 第 7 章 `detail_doc_type + chapter_target`（指向不存在条目 → P2；未覆盖实际承担技术合同的目标类型 → P2）。
6. `Capability-to-Architecture Mapping.detail_index_refs` ↔ 第 7 章条目（断链 → P1，G9）。
7. 时序图参与者 ↔ 归属表 owner（出现归属表外参与者或外部直连下层边 → P1）。

同一根因的多处表现合并为一条 finding（列全部 location）。

## 6. 严重度判级规则（L1 §7）

- **P1（阻断，不可进入详细设计）**：
  - 违反 Go 分层依赖律（反向 import、业务规则下沉 transport、SQL 上浮 service、repository import service、依赖成环）。
  - 外部/前端直连 service/repository/domain 越过 transport entry（图/时序图/正文任一处）。
  - net/http 锁定项违反（引入 gin/echo/fiber/chi）。
  - G1~G8 任一缺失（缺章、缺图、缺六件套任一件、缺承接索引、缺核心能力承接闭环）。
  - 非豁免 UC 无可定位 `sequenceDiagram`；时序图策略表占位锚点残留。
  - 涉权限/采集/三方域名/PII 缺 `compliance_basis`；出现真实 secret value；`.env` 当线上配置合同/secret 来源；云 SDK 支持默认链却要求长期 AK/SK。
  - 粗粒度核心行为（不可直接展开详细设计）；核心能力无失败路径行为。
  - 第 7 章 doc_type 非法（含他平台类型名）；pending 类型缺 `l2_status` 标注或缺 L2 豁免计划；有持久化无 `repository-data`。
  - `Capability-to-Architecture Mapping` 应建未建 / 语义字段缺 / owner 行为未落 `biz`；`detail_wx6_readiness=fail:*`。
  - 详细设计执行基线五字段缺 / profile ref 非稳定引用；向后兼容 yes 无用户确认依据。
  - 双主定义（full 链 README/design.md 与 design-main 两套正文）。
- **P2（非阻断，可带明确假设进入）**：归属三问空洞；失败去向/状态码映射缺失；技术决策字段不全（未被下游引用时）；图文局部不一致；名词先行反模式（未影响主链）；共享能力误归类（未影响主链）；命名反模式（含混 Manager/Helper 后缀、名词先行结构）；轻度越界（少量签名/字段——给回收方案）；编号缺失/重号/跨层混用；后台入口缺 `entry_kind`。
- **P3（建议）**：表述与术语一致性；格式偏离模板但语义完整。
- 判级冲突时取高；同一根因的多处表现合并为一条 finding（列全部位置）。
- 需求层缺陷（行为缺失/矛盾/范围漂移）→ 不在概要修，结论标注「回退需求阶段」，不建议在概要补造业务规则。

## 7. 结论判定（互斥三选一，L1 §6）

- 存在任一 P1 → **不可进入详细设计**（列阻塞清单 + 修订形态建议：局部修订 vs 文档级重构，按 L1 §8）。
- 仅余 P2 且每条已有明确假设/修订路径 → **带明确假设可进入**（列假设、依据、影响范围、验证时点；P3 可遗留）。
- 无 P1/P2（P3 可遗留）→ **可进入详细设计**。
- 结论为「可进入」或「带明确假设可进入」时必须给 Gate 收口指引（用户终端 confirm，见 SKILL.md「Gate 收口」节）；确认未落盘前不得进入详细设计。

## 8. 修订形态判定（L1 §8，写进每条 finding 的 suggestion）

- **局部修订**：补一条行为、补归属三问理由、补一条 `technology_decision_handoff[]` 字段、补一条承接索引、补一张图、回填 `Capability-to-Architecture Mapping` 引用、改措辞 → 在原文档直接闭合，验证不引入新责任单元体系/并行归属规则/跨章边矛盾/详细设计越界。
- **文档级重构**：归属模型错误（owner 大面积错位、违反分层依赖律）、行为从名词倒推、Utility 误归业务 owner 或 service 误抽 Utility、索引与归属表系统性脱节、架构总览与正文两套口径、技术决策承接模型错误、核心能力承接主线错误 → 先修正正向结构/责任边界/能力归属/技术决策承接/索引，再补齐 G1~G8 证据；禁止用局部补丁或旁路表格掩盖错误模型。
