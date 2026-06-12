---
name: client-design-overview-writing
description: 用于撰写 Flutter 客户端概要设计文档。按"判轨与设计包骨架、技术栈与约束确认、行为枚举（BHV 编号）、owner 归属判定（三问）、页面流与路由、架构总览人审视图（一句话架构/分层架构图/页面流图/核心 UC 表/UC 承接表/时序图策略表）、技术决策承接清单、详细设计承接索引（逐文件）、架构就绪自检 G1~G8"的顺序推进；把概要写到"详细设计可直接展开而不需要重新决定边界"，但不进入可编码合同层（字段级合同/方法签名/SDK 参数禁写）。规则唯一来源是 `.trellis/spec/harness/overview/` 的 L1 SSOT；本 skill 只编排写作动作，不复写规范正文。
---

# 客户端概要设计撰写

> 层级契约：L1（`.trellis/spec/harness/overview/overview-structure-single-source.md`）承载规则正文与完成条件；本 SKILL.md 只做装载顺序、执行规则、阶段流程与输出要求；`references/` 只承载分章写法细则、模板与示例。冲突时 L1 > references > 本文件。

## 目标

- 输出可评审、可追踪、可指导详细设计的客户端概要设计文档；每个关键章节同时落出生成动作、约束边界与可验证信号。
- 以行为驱动组织概要：先枚举行为空间（BHV 编号），再判定唯一 owner 归属（三问理由），组件只在行为归属后形成——禁止名词先行。
- 先完成「架构总览（人审视图）」再进入索引细化：一句话架构、分层架构图、页面流图、核心 UC 表、UC 承接表、时序图策略表是架构就绪门禁（L1 §2.5），不是可选的可读性优化。
- 把概要写到详细设计可直接展开：承接索引为每个 owner 提供 chapter_target 来源锚点（full 链逐条落到 `chapters/<slug>.md` 文件名）。
- 守住概要深度边界（L1 §5）：只闭合边界、语义、链路、取舍、索引；不写字段级合同、方法签名、SDK 参数、DDL、secret value。
- 在进入详细设计前完成架构就绪收敛（L1 §6 G1~G8）。

## 最小输入与自动补全

- 接受需求产物路径（prd.md / 正式需求包）、设计目标、已有草稿或 design_package 路径。
- 优先读取需求核心能力清单（P0/P1）；不可定位时仍可产出概要草稿并记录显式假设，但不得凭空生成 P0/P1，不得宣称可进入详细设计。
- 信息不足时收敛到最小可写范围，**不擅自补齐高风险业务规则**；未决问题显式列出并向用户提问（一次 1~4 个关键问题）。
- 有历史设计版本时，优先复用命名、章节和术语约定（先 `rg` 检索既有 BHV/UC/组件名）。

## 执行模式（按需切换）

- **一次性交付模式（默认）**：按分阶段流程内部连续推进，一次性完成全稿或本轮目标；信息不足用显式假设，不因等待确认而阻塞。
- **共创式迭代模式**：仅当用户明确要求逐阶段确认或只看某一阶段时启用；一次只产出当前阶段内容。
- 模式必须在输出中显式标注。

## 装载顺序（硬前置，任一失败即终止）

1. 读 L1 `.trellis/spec/harness/overview/overview-structure-single-source.md`；不可用 → 终止并提示先安装 guru spec 模板（trellis init -t guru-flutter-client）。
2. 读通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律是归属判定基准）。
3. 读 `.trellis/spec/conventions/project-conventions.md` 并执行校验清单 C1~C5；不可读或校验不过 → 终止并提示先填写项目约定。
4. 判轨：读 task.json `guru_chain`（L1 §2 轨道判定）；full 链确认/声明 `design_package`。
5. 定位需求产物；缺失走 L1 §1-P4 显式假设路径。
6. 需要分章写法细则与模板时读 `references/chapter-guide.md`；需要成稿样例时读 `references/examples/design-main-minimal.md`。

## 执行规则

1. 共享规范（章节合同、图表合同、归属方法、Gate 条件）一律以 L1 为准；本 skill 与 references 不重复维护规范正文。
2. 默认一次性交付模式：按阶段内部推进，不要求用户逐阶段确认；只在出现高风险未决项时暂停提问（一次 1~4 个）。
3. 显式假设必须标注依据、影响范围、验证时点，并落盘到 design-main.md（或 design.md §1）对应章节——不允许只在会话输出里口头声明。
4. 阶段 0 必须完成判轨落盘：full 链建立设计包骨架（README.md + design-main.md + chapters/ 空目录）并把包路径写入 task.json `design_package`；任务内 design.md 只写指针+摘要。light 链直接写 design.md §1。
5. 阶段 0 必须确认技术栈基线：Flutter 版本、状态管理（GetX 等）、DI、网络栈、本地存储——取值一律引用 project-conventions 槽位，不在概要另定。
6. 行为枚举（阶段 2）按 L1 §3 四类顺序（用户操作→系统反应→失败路径→生命周期），逐条 Given/When/Then + `### BHV-NNN` 编号标题；每条满足 L1 §3.1 粒度标准；禁止从名词/组件出发。
7. 归属判定（阶段 3）按 L1 §4 判定表给每条行为/状态唯一 owner + 三问理由；对照分层依赖律自检无违例；一个状态只能有一个写 owner。
8. 命名遵守 L1 §4.1：组件=定语+名词（≤2 词）+ 层后缀；行为=动词/动词+宾语；list/one/get/fetch 语义区分。
9. 架构总览（阶段 5）按 L1 §2.5 六件套合同产出；图中组件必须与归属表一一对应，不得出现归属表之外的组件；分层架构图箭头方向必须符合分层依赖律。
10. 时序图策略表逐 UC 声明 独立/合并/豁免；早期可用计划锚点，**送审概要 Gate 前非豁免 UC 必须回填可定位的真实 sequenceDiagram**（参与者用真实组件名、步骤编号与详述一一对应）；占位残留不得宣称可送审。
11. 技术决策承接（阶段 6）按 L1 §2.6 字段合同逐条建立 `technology_decision_handoff[]`；涉权限/数据采集/三方域名/PII 必填合规依据；不保存任何 secret value；"未选定"必须显式标注，禁止让下游引用未选定决策。
12. 承接索引（阶段 7）覆盖归属表全部 owner；full 链每条附 `chapters/<slug>.md` 目标文件名（文件本体详细阶段产出）；doc_type 取值只用详细 L1 §2 九分类；命中 pending L2 类型时在此阶段就写明 `L2豁免` 计划或改走先补 L2 路径。
13. 概要禁写项（L1 §5）全程生效：发现自己在写方法签名、字段合同、SDK 参数即停下回收到"交给详细设计展开"的索引条目。
14. UC 与行为双向回指（L1 §3.2）：每条 BHV 回指 ≥1 个 UC；UC 承接表 bhv_refs 与行为集合双向核对。
15. 阶段 9 自检按 L1 §6 G1~G8 逐项输出（满足/缺口+闭合计划），full 链写成 design-main 的"架构就绪自检"章节；存在未闭合 G 项不得送审，不得用概括性"基本满足"替代逐项证据。
16. 修订时按 L1 §8 先判定局部修订 vs 文档级重构；发现需求缺陷回退需求阶段，不在概要补造业务规则。
17. 产物语言：辅助性文本一律中文；代码语法元素与路由名/组件名保持英文。
18. 完稿后提示送审：加载 `client-design-overview-review` 过概要 Gate；Gate 结论"可进入"后提请**用户本人**在终端运行 `python3 .trellis/scripts/guru/guru_gate.py confirm overview <task_dir>`（agent 不得代跑）。

## 分阶段流程（writing 专属）

1. **阶段 0 判轨与骨架**：判轨落盘（规则 4）；技术栈基线确认（规则 5）；full 链建包骨架 + design.md 指针。
2. **阶段 1 README 与元信息**：full 链写 README 导航（不承载正文）+ design-main 元信息/修订历史。
3. **阶段 2 行为枚举**：第 1~2 章（设计约束与输入、行为集合）；BHV 编号 + GWT + 粒度自检。
4. **阶段 3 归属判定**：第 3 章归属判定表（owner + 三问）；分层依赖律自检。
5. **阶段 4 页面流与路由**：第 4 章（页面导航/入参出参/deep link；非 UI 标注 N/A）。
6. **阶段 5 架构总览**：第 5 章六件套（一句话架构→分层架构图→页面流图→核心 UC 表→UC 承接表→时序图策略表）；本阶段建立人审链路，时序图可先计划锚点。
7. **阶段 6 技术决策承接**：第 6 章 `technology_decision_handoff[]`。
8. **阶段 7 承接索引**：第 7 章 chapter_target → doc_type（→ chapters/<slug>.md）；回填 UC 承接表 index_refs。
9. **阶段 8 未决问题**：第 8 章显式列出 + 风险等级。
10. **阶段 9 架构就绪收敛**：回填全部时序图占位 → 第 9 章 G1~G8 自检 → 送审提示（规则 18）。

## 输出要求（writing 专属）

- 默认先给完整正文，再给结构化状态；共创式迭代模式只给当前阶段正文 + 当前阶段状态。
- 一次性交付模式默认输出下列字段：
  - `交付范围`（全稿/当前阶段）与`执行模式`
  - `链型`（full/light）与`概要主定义位置`（design-main.md / design.md §1）
  - `显式假设`（无/有：假设、依据、影响范围、验证时点）及`落盘状态`
  - `行为集合状态`（BHV 条数、粒度自检结论）
  - `归属判定状态`（覆盖行为数、分层律自检结论）
  - `架构总览状态`（六件套逐件 完整/缺失；缺失时标注影响 G6/G7）
  - `时序图承接状态`（非豁免 UC 是否全部有可定位 sequenceDiagram；占位残留清单）
  - `技术决策承接状态`（无触发/已建立/存在缺口；未选定清单）
  - `承接索引状态`（owner 覆盖率；full 链逐文件清单；pending L2 命中与豁免计划）
  - `架构就绪结论`（仅阶段 9 或全稿完成时输出 G1~G8 逐项；草稿阶段只说明不可送审原因）
  - `需用户确认项`（若有）
- 完稿输出末尾给出送审与人工确认指引（规则 18 的两条命令）。

## 参考资料

- 概要阶段中立规范（L1）：`.trellis/spec/harness/overview/overview-structure-single-source.md`
- 分章写法细则与模板：`references/chapter-guide.md`
- 最小成稿样例：`references/examples/design-main-minimal.md`
- 通用方法 SSOT：`.trellis/spec/guides/golden-path.md`；项目取值：`.trellis/spec/conventions/project-conventions.md`
