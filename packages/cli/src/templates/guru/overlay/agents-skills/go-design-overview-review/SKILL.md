---
name: go-design-overview-review
description: 用于审核 Go 后端概要设计文档，判定能否进入详细设计。先做 EX 前置判定（判轨/包骨架/需求准入/项目约定 C1~C5/机器 Gate），再按取证矩阵逐章审核：行为覆盖与粒度（BHV-NNN）、owner 归属与分层依赖律（transport→service→repository→domain 单向无循环）、架构总览人审视图六件套、Use Case 时序图策略闭合、技术决策承接（technology_decision_handoff）与合规凭证策略、共享能力归属判定、七类 doc_type 承接索引完整性与 L2 豁免、跨章边连线一致性；先证据后结论，输出分级 findings（严重度/证据/最小修订）与互斥结论（前置失败 vs 通过），并以用户终端 confirm 作为 Gate 收口。规则唯一来源是 `.trellis/spec/harness/overview/` 的 L1 SSOT。
---

# Go 后端概要设计审核

> 层级契约：L1（`.trellis/spec/harness/overview/overview-structure-single-source.md`）承载规则正文与 G1~G8 完成条件；本 SKILL.md 只做前置判定、执行规则与审核流程；`references/review-baseline.md` 承载逐章取证矩阵与严重度判级，`references/review-output.md` 承载输出字段合同。冲突时 L1 > references > 本文件。

## 目标

- 审核 Go 后端概要设计是否达到进入详细设计阶段的架构就绪口径（L1 §6 G1~G8）。
- 只评审概要阶段质量，不扩展到需求方向、详细设计实现或代码评审。
- 基于文档证据输出问题清单与最小修订方案：每条 finding 给「严重度 + 证据锚点 + 最小修订」，先证据后结论。
- 架构总览（人审视图）是第一取证对象：评审者必须先能从六件套读懂「这个 Go 服务长什么样、边界在哪、核心链路怎么走」，再进入逐章细查。
- 验证概要是否把分层归属（transport / service / repository / domain）落到唯一 owner，且依赖方向单向、无循环、无跨层、无外部直连下层。
- 验证概要技术决策承接（`technology_decision_handoff[]`）是否覆盖触发项（DB/缓存/消息/外部 provider/LLM/对象存储/云服务），并对涉权限、数据采集、三方域名、PII、凭证的项落出 `compliance_basis` 与凭证策略（只声明默认凭证链/env/ref/profile/平台身份注入，不写 secret value）。
- 验证第 7 章承接索引是否覆盖归属表全部 owner，并对 Go 七类 `doc_type`（`entry-api` / `biz` / `repository-data` / `domain` / `config` / `external` / `runtime`）给出来源锚点与逐文件落点；命中尚无 L2 的类型（`domain` / `config` / `external` / `runtime`）时是否标注 `l2_status: pending` 并给出按 L1 八问展开的 L2 豁免计划。

## 最小输入与自动补全

- 接受 task 目录、design_package 路径或单个 design-main.md / design.md 路径。
- 仅用于概要全稿完成后的门禁审核，不用于写作过程中的中间态审核。
- 候选文档不唯一时：能从 task.json `design_package` 或 README 唯一推断主文档则说明识别结果后继续；否则暂停向用户确认审核目标。
- 若需求阶段「核心能力定义」可定位，必须读取并作为审核输入；不可定位时只有当概要已按 L1 §1-P4 记录显式假设才继续，否则走前置阻断。

## 装载路径（安装后固定锚点）

- golden-path（通用方法 SSOT，分层依赖律基准）：`.trellis/spec/guides/golden-path.md`
- 概要 L1（本审核规则唯一来源）：`.trellis/spec/harness/overview/overview-structure-single-source.md`
- 详细 L1（七类 doc_type 八问基线，校验承接索引合法性）：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- 详细 L2（已出 3 类，校验 `entry-api` / `biz` / `repository-data` 承接深度）：`.trellis/spec/harness/detail/detail-type-{entry-api,biz,repository-data}.md`
- 项目约定（执行前校验 C1~C5）：`.trellis/spec/conventions/project-conventions.md`

## 装载顺序与 EX 前置判定（任一失败 → 前置阻断输出，停止逐章审核）

1. 读 L1 主 SSOT；不可用 → 终止并提示先安装 guru spec 模板（`trellis init -t guru-go-backend`）。
2. 读 `references/review-baseline.md`（取证矩阵）与 `references/review-output.md`（输出合同）。
3. 读 golden-path（分层依赖律）与详细 L1 / 已出 3 类 L2（校验承接索引时回指）。
4. 读 `project-conventions.md` 并执行 C1~C5 校验（Go 版本/模块路径、分层目录约定、DB/迁移工具、网络与序列化栈、可观测性基线）；不可读或校验不过 → 前置阻断。
5. **EX-1 判轨**：task.json `guru_chain` 可判定；full 链 `design_package` 已声明。
6. **EX-2 包骨架（full 链）**：design_package 目录、README.md、design-main.md、chapters/ 齐全；light 链 design.md §1 存在。
7. **EX-3 需求准入**：需求产物可定位且有 P0/P1 核心能力；不可定位时只有当概要已按 L1 §1-P4 记录显式假设才继续，否则前置阻断（`Capability-to-Architecture Mapping` 只能判为「未建立」）。
8. **EX-4 机器 Gate**：`python3 .trellis/scripts/guru/guru_gate.py overview <task_dir>` 通过（结构性缺口先由机检定位，人工审核聚焦语义与归属）。

## 执行规则

1. 共享规范一律以 L1 为准；本 skill 与 references 不重复维护规范正文，逐项检查必须能回指 L1 章节号（承接索引合法性回指详细 L1 / 已出 3 类 L2）。
2. 先证据后结论：每条 finding 带章节锚点或明确缺失对象；引用正文优先给小节/表格行/裸编号定位。
3. 架构就绪判定统一按 L1 §6 G1~G8 执行；G 项缺失即 P1，并在 finding 中标注受影响 G 项；不得用概括性「基本满足」替代逐项证据。
4. 分层依赖律违例（归属方向错、依赖出现循环、跨层调用、图中箭头逆向、外部/前端直连 service/repository/domain 越过 transport entry）→ P1，**不得给出通过性结论**；问题描述写明「外部调用方不能直接调用 service/repository/domain，必须经 transport entry」。
5. 写作顺序与归属自洽是必查项：概要应体现自底向上写作（① domain → ② repository-data → ③ biz(service) → ④ entry-api(transport) → ⑤ 横切 config/external/runtime）形成的依赖闭合；上层引用的下层 owner 必须在归属表中存在且方向正确——断链或反向记 P1。
6. 图表与正文一致性必查：架构图组件 ⊆ 归属表；系统边界图外部依赖 ↔ external/runtime owner；UC 承接表 `bhv_refs` ↔ BHV-NNN 双向闭合——任一向断链记 P1/P2（判级见 review-baseline）。
7. 时序图策略闭合（G7）：非豁免 UC 无可定位 `sequenceDiagram`、合并图缺覆盖清单、豁免缺理由、占位锚点残留 → P1；时序图参与者必须用真实 owner 名（transport/service/repository/domain/external），不得出现外部直连下层的边。
8. 行为粒度按 L1 §3.1 判定：BHV-NNN 须为可独立承接的行为（含失败路径与生命周期），「处理订单」式粗粒度行为 → P1（不可直接展开详细设计）。
9. 技术决策承接按 L1 §2.6 字段合同逐条核查 `technology_decision_handoff[]`：DB/缓存/消息/外部 provider/LLM/对象存储/云服务等触发项必须有承接目标与 `detail_*_target`；涉权限/采集/三方域名/PII 缺 `compliance_basis` → P1；正文/示例/fixture 出现真实 `api_key` / `access_key_id` / `secret_access_key` / `access_key_secret` / `secret_key` / `token` 等 secret value，或把 `.env` 当线上配置合同 / secret 来源 → P1；云 SDK 支持默认凭证链却要求长期 AK/SK → P1。
10. 共享能力归属判定：按 L1 共享能力条款区分 Utility 纯函数技术能力、下层 service 公用单元、普通 service unit 与横切 config/external/runtime；同域业务步骤误下传、技术能力被误归类为业务 owner、缺归属边集合 → P2 起步（影响 G2/G5 时升 P1）。
11. 承接索引核查（G4）：覆盖归属表全部 owner；`doc_type` 取值只用 Go 七类（`entry-api` / `biz` / `repository-data` / `domain` / `config` / `external` / `runtime`）；full 链逐条有 `chapters/<slug>.md` 文件名；命中 `domain` / `config` / `external` / `runtime`（尚无 L2）须标注 `l2_status: pending` + 按详细 L1 八问展开的 L2 豁免计划，缺标注或缺计划 → P1；已出 3 类（`entry-api` / `biz` / `repository-data`）须能回指对应 L2 承接深度。
12. 编号纪律核查：行为用 `BHV-NNN`（prd 标题来源），设计单元引用用 `UNIT-<slug>`（详细标题来源），正文引用须为裸编号；编号缺失/重号/跨层混用 → P2。
13. 命名按 L1 §4.1 抽查：组件=定语+名词+层后缀（如 `OrderService` / `OrderRepository`）；含混 Manager/Helper 后缀或名词先行结构 → P2。
14. 概要越界（出现方法签名/字段级合同/SDK 参数/DDL/具体 SQL，L1 §5）→ P2 起步，并给最小回收方案（移入承接索引的 `detail_expansion_targets`）。
15. 若概要出现 LLM/agent/prompt 驱动调用：按 L1 LLM 承接条款核查逐次逻辑调用承接、`prompt_owner`、运行期上下文来源、上下文获取/编排行为锚点、prompt 组装 owner、`detail_prompt_target`，及 provider/model/SDK/invocation mode/config/external/runtime/凭证策略对应的 `technology_decision_handoff[]` 目标；缺口归入 G8。
16. 发现需求层缺陷（行为缺失/矛盾/范围漂移）→ 结论标注「回退需求阶段」，不建议在概要补造业务规则。
17. 审核不重写设计：只给证据、影响与最小修订方案，不代写正文；修订形态按 L1 §8 区分局部修订 vs 文档级重构——结构/归属/合同缺陷不得建议用局部补写保留错误模型。
18. 概要文档无存量豁免：新文档必须全量符合 L1（存量豁免仅适用于实现阶段代码）。

## 审核流程

1. **结构识别**：对照 L1 §2 产物合同（按链型取轨道），记录第 1~7 章存在性与位置；缺章记 P1。
2. **前置判定**：执行 EX-1~EX-4 与 C1~C5；任一失败走前置阻断输出，停止逐章审核。
3. **架构总览取证**（G6，第一取证对象）：六件套逐件核查——一句话架构格式、系统架构图（分层与依赖方向）、系统边界图（外部依赖与调用边界）、核心 UC 表、UC 承接表（列完整 + `bhv_refs`/`index_refs`）、时序图策略表（独立/合并/豁免三选一）。
4. **行为覆盖核查**（G1）：逐条核对 P0/P1 核心能力 → BHV-NNN 行为集合差集；抽查粒度（§3.1）与失败路径/生命周期覆盖。
5. **归属判定核查**（G2，核心）：逐行核查 owner 唯一性（transport/service/repository/domain）、三问实质性（「同上」式三问记 P2）、分层依赖律单向无循环无跨层一致性、写作顺序依赖闭合、名词先行反模式。
6. **图文一致性核查**：规则 6 的三组双向核对（架构图⊆归属表、边界图↔external/runtime、UC 承接表↔BHV）。
7. **时序闭合核查**（G7）：逐 UC 按策略表核对 `sequenceDiagram` 可定位性、参与者真实性（无外部直连下层边）、编号与详述对应。
8. **技术决策与合规核查**（G3/G8）：`technology_decision_handoff[]` 逐条字段 + `compliance_basis` + 凭证策略 + secret value 扫描；LLM 触发时按规则 15 核查承接链。
9. **共享能力归属核查**（G5）：Utility / 下层 service 公用 / 普通 unit / config/external/runtime 归类与边集合。
10. **承接索引核查**（G4）：owner 覆盖、七类 doc_type 合法、逐文件、`l2_status: pending` 标注与 L2 豁免计划、已出 3 类回指 L2。
11. **越界核查**：L1 §5 禁写项扫描（方法签名/字段合同/SDK 参数/DDL/SQL）。
12. **汇总**：G1~G8 状态表（已闭合/需修订）+ findings 分级 + 互斥结论（输出合同见 review-output.md）。

## findings 与结论口径

- 每条 finding 三要素：**严重度**（P0 阻断 / P1 阻断 / P2 非阻断）、**证据**（章节锚点 + 表格行/裸编号，或明确缺失对象）、**最小修订**（局部补写还是文档级重构按 L1 §8）。
- 严重度判级：分层依赖律违例、外部直连下层、非豁免 UC 时序图缺失、缺 `compliance_basis`、出现 secret value、粗粒度核心行为、缺 `l2_status` 标注 → P1（阻断）；命名反模式、三问空洞、轻度越界、共享能力误归类（未影响主链）→ P2（非阻断）；需求层缺陷 → 不在概要修，标注「回退需求阶段」。
- 是否可进详细设计结论（三选一，互斥）：
  - **可进入详细设计**：G1~G8 全部已闭合，无 P0/P1。
  - **带明确假设可进入**：仅余已落盘的显式假设（列假设、依据、影响范围、验证时点），无 P0/P1。
  - **不可进入**：存在 ≥1 条 P0/P1，列阻塞清单与最小修订。

## 输出（互斥分支）

- **前置失败**：仅输出前置缺口与修复动作（含「回退需求 / 补判轨 / 补包骨架 / 补项目约定 / 过机器 Gate」指引）与最小结构状态，不展开逐章审核，不输出 G 项展开结论。
- **前置通过**：按 `references/review-output.md` 的字段合同输出——架构视图检查摘要 → 逐条 findings（severity / location / evidence / suggestion）→ 结构概况（链型 / 主定义位置 / 显式假设落盘状态）→ 技术决策承接预览（`technology_decision_handoff_source_preview`）→ 承接索引状态（owner 覆盖 / 七类 doc_type / `l2_status: pending` 清单）→ G1~G8 状态表 → **三选一结论** → 修订形态建议。
- 不在本文件维护输出字段清单；字段新增/删改/命名调整只改 `references/review-output.md`。

## 边界约束

- 概要文档无存量豁免：新文档必须全量符合标准包。
- 审核不重写设计：只给证据、影响与最小修订方案，不代写正文。
- 发现需求层缺陷（行为缺失/矛盾）→ 结论标注「回退需求阶段」，不建议在概要补造。
- 只审概要主定义（full = design-main.md；light = design.md §1）与第 1~7 章，不审详细设计正文，不审代码。

## 与官方 Trellis skill 及姊妹 skill 的边界

- 与官方 `trellis-brainstorm`：那是需求/构想阶段产物；本 skill 不做需求方向评判，只审概要承接需求 P0/P1 的就绪度。需求缺陷一律回退需求阶段。
- 与官方 `trellis-check`：`trellis-check` 是 Phase 2/3 的**代码质检**（实现是否符合规范）；本 skill 是 Phase 1 内的概要**人工 Gate 判定**（能否进入下一阶段），审核对象是设计文档而非代码，二者职责不重叠。
- 与 `go-design-overview-writing`（设计写）：那一支**承接 prd 产出 design 章**（按行为枚举→归属→架构总览→技术决策→承接索引推进）；本 skill 是其下游门禁，**审而不写**——只给证据、影响与最小修订，不代写正文。
- 与 `go-design-detail-review`：本 skill 的「可进入详细设计」结论是详细阶段的入口前提；详细审核是另一支 skill 的职责。

## Gate 收口（人工确认）

结论为「可进入详细设计」（或带明确假设可进入且假设已记录）时，按 config `guru.gate_mode` 完成人工收口（通道主定义见 workflow Trellis System 节）：

- **strict（默认）**：提请**用户本人**在终端运行 `python3 .trellis/scripts/guru/guru_gate.py confirm`；agent 不得代跑（无 TTY 会被拒）。
- **soft**：用户在对话中明确确认后，agent 运行 `python3 .trellis/scripts/guru/guru_gate.py confirm overview <task_dir> --via-agent --user-quote "<用户确认原话>"` 代跑（记录留痕标注 soft/agent）；未获用户本轮明确确认不得执行。

确认未落盘前不得进入详细设计。

## 参考资料

- 概要阶段中立规范（L1）：`.trellis/spec/harness/overview/overview-structure-single-source.md`
- 详细阶段基线（承接索引回指）：`.trellis/spec/harness/detail/detail-structure-single-source.md`；已出 3 类 L2：`.trellis/spec/harness/detail/detail-type-{entry-api,biz,repository-data}.md`
- 取证矩阵与严重度判级：`references/review-baseline.md`
- 输出字段合同：`references/review-output.md`
- 通用方法 SSOT：`.trellis/spec/guides/golden-path.md`；项目取值：`.trellis/spec/conventions/project-conventions.md`
