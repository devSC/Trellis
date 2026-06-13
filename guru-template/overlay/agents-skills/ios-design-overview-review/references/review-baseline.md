# iOS 概要审核取证矩阵与严重度判级（references）

> 编排层产物：只承载逐章 / 逐类取证操作与判级细则。规则正文与完成条件以 L1
> `.trellis/spec/harness/overview/overview-structure-single-source.md` 为权威；承接索引合法性回指详细 L1
> `.trellis/spec/harness/detail/detail-structure-single-source.md` 与已出 3 类 L2（`detail-type-{viewmodel,usecase,repository}.md`）；
> 分层依赖律基准回指 `.trellis/spec/guides/golden-path.md`。冲突时 **L1 > L2 > 本文件 > SKILL.md**。
> doc_type 七类名一律以 L1 / 详细 L1 为准：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`。
> 禁自创 `transport-handler` / `service` / `controller` / `datasource` / `dao` / `page-entry` 等其它平台类型名（flutter/Go 类型名不适用 iOS）。

## 1. 取证准备

- 建立编号索引：`rg -n "BHV-|UC-|TD-|UNIT-" <主文档>` 固化行为 / 用例 / 决策 / 单元清单；`rg -n "^###? " <主文档>` 固化章节锚点。
- 引用证据用「章节 + 表格行 / 裸编号」定位（如 `§3 归属表 BHV-012 行`、`§5 时序图策略表 UC-02 行`、`§6 技术决策 TD-03`），不引用模糊位置。
- 七类 doc_type 命中扫描：`rg -n "viewmodel|usecase|repository|domain-model|view|coordinator|external" <主文档>` 与归属表 owner 对照；同时 `rg -ni "transport-handler|datasource|page-entry|controller|service|dao|db-dao|api-network" <主文档>` 扫自创类型名（命中即 P1，见 §5）。
- full 链同时取证：README.md 是否承载事实正文（承载即 P2，应只做导航 / 索引）；任务内 `design.md` 是否仍承载主定义（承载即 P2 双主定义）。light 链只取证任务内 `design.md` §1。
- secret 扫描：`rg -ni "api_key|access_key_id|secret_access_key|secret_key|\\btoken\\b|password|私钥|-----BEGIN" <主文档> <fixtures>`；命中真实值即 P1（见 §6 第 6 章取证）。
- 装载顺序与 EX 前置判定见 SKILL.md「装载顺序与 EX 前置判定」；任一前置失败 → 前置阻断输出（见 review-output.md 分支一），不进入本文逐章矩阵。

## 2. 逐章取证矩阵（对照 L1 §2 必含章节）

按链型取轨道：full 链 = `design-main.md` 第 1~9 章；light 链承载于任务内 `design.md` §1（第 5 章可简化为一句话架构 + 页面流文字描述，第 9 章可简化为 Gate 前自查；第 1~4 / 6 / 7 / 8 章不可省，归属表七类不可因单文件而省略，见 L1 §2b）。

| 章 | 应覆盖（L1 锚点） | 取证操作 | 缺口判级 |
|----|------------------|---------|---------|
| 1 设计约束与输入 | P0/P1 核心能力逐条带需求锚点；技术栈约束（DDD 四层 / SwiftUI / FactoryKit / WCDBSwift）；显式假设三字段（依据 / 影响范围 / 验证时点）；project-conventions 槽位快照（C1~C10） | 对照需求核心能力清单做差集；抽查需求锚点可定位；C1~C10 槽位取值是否落项或显式 pending（L1 §1-P3/P3a/P3b） | 缺章 P1；P0/P1 漏承接 P1（G1）；需求锚点缺失 P2；槽位未落项或与约定冲突 P2（影响归属 / 合规升 P1） |
| 2 行为集合 | §3 四类来源枚举（用户操作 / 系统反应 / 失败路径 / 生命周期）+ `### BHV-NNN <短名>` + GWT 三段 + 状态 / 数据标注 + §3.1 粒度 | 逐条核对 GWT（Given/When/Then）与「哪个 ViewModel 的哪个 `@Published`」「哪个 domain-model / 哪个 Repository」标注；抽样 ≥1/3 行为做 §3.1 四条粒度判定 | 无失败路径类行为（网络失败 / 权限拒绝 / WCDBSwift 损坏等）P1；粗粒度行为（如「处理创作」）P1；GWT 缺段或缺状态 / 数据标注 P2；行为从 SwiftUI View 名 / 组件名倒推（违 §3）→ 文档级重构（P1） |
| 3 归属判定表 | §4 唯一 owner（七类 doc_type）+ 三问实质 + 分层依赖律 + 写作顺序依赖闭合 + 命名规范 §4.1 | 逐行：owner ∈ 七类且归正确层？三问是否有实质内容（非「同上」）？一个状态是否仅一个写 owner？依赖方向是否符合 Domain→App→Infrastructure→UI（运行期调用）单向？ | 分层依赖律违例 P1（阻断，见 §5）；行为无 owner / owner 非七类 P1；多写 owner（同一状态多写 owner）P1；三问空洞（「同上」）P2；名词先行 / 含混 Manager/Helper 后缀 P2 |
| 4 页面流与路由 | §2.5③ 路由（`NavigationDestination` 枚举值）/ 入参出参 / deep link / 失败 / 取消 / 权限拒绝去向；导航必经 AppCoordinator；非 UI 需求标 N/A 及依据 | 路由名与归属表 coordinator owner 抽查；失败 / 取消 / 权限拒绝去向逐页核对；扫 View 间直连导航（`NavigationLink` 跨 feature 硬跳） | 整章缺失（UI 需求）P1；View 间直连导航绕过 coordinator P1（分层依赖律，见 §5）；缺失败 / 取消去向 P2；非 UI 需求缺 N/A 依据 P2 |
| 5 架构总览（人审视图，full 链必含成节） | §2.5 六件套 | 见 §3 专项 | 见 §3（缺件 P1 / G6） |
| 6 技术决策承接清单 | §2.6 `technology_decision_handoff[]` 字段合同 + `compliance_basis` + 凭证策略 | 逐条字段齐全性；涉权限 / 采集 / 三方域名 / PII 的条目有 `compliance_basis`；secret value 扫描（见 §1）；未选定决策是否被下游引用 | 字段缺（未被引用）P2；缺 `compliance_basis`（涉权限 / 采集 / PII）P1（G3）；真实 secret value 落盘 P1；未选定决策被下游引用 P1（G8） |
| 7 详细设计承接索引 | §2.7 owner 全覆盖 + `detail_doc_type` ∈ 七类 + full 链逐文件 + `l2_status` 标注 + pending 四类 L2 豁免计划 | 归属表 owner 集合 vs 索引覆盖集合差集；`detail_doc_type` 是否全为七类（无自创）；full 链每条有 `chapters/<slug>.md`；pending 四类是否 `l2_status: pending` + 按详细 L1 八问展开的豁免计划；已出 3 类是否能回指对应 L2 | owner 未覆盖 P1（G4）；`detail_doc_type` 非七类 / 自创类型 P1；pending 四类缺 `l2_status` 标注或缺豁免计划 P1（G9）；已出 3 类指向的 detail-type-*.md 口径与归属表 doc_type 不一致 P2 |
| 8 未决问题 | 风险等级（P1/P2/P3）+ 阻塞 G 项；未选定决策不私自拍板 | 高风险项是否存在未关闭；是否把「未选定」决策写成已选定 | 高风险未关闭 P1（G5）；把未选定写成已选定 P1（越界，L1 §5） |
| 9 架构就绪自检（full 链必含成节） | G1~G9 逐项自评（满足 / 缺口 + 闭合计划） | 自检结论与本次审核结论交叉核对；存在未闭合 G 项是否仍送审 | 自检缺章（full）P1；自检与实情不符（自评满足但实际违例）P1 |

## 3. 架构总览六件套专项取证（G6，第一取证对象）

评审者必须先能从六件套读懂「这个 iOS feature 长什么样、DDD 四层边界在哪、核心链路从 View 到持久化怎么走」，再进入逐章细查。

| 件 | 取证操作 | 缺口判级 |
|----|---------|---------|
| ① 一句话架构 | 是否按 L1 §2.5① 固定格式：`用户经 <入口 View/路由> 进入，由 <ViewModel> 承接 <核心行为> 状态，调 <UseCase> 编排，经 <Repository 接口> 访问数据（实现在 Infrastructure），导航由 <AppCoordinator> 收口，按需经 <external> 集成 <网络/SDK/WCDBSwift>`；组件为归属表真实名 | 缺失 P1（G6）；格式自由化 / 组件名非真实 owner P3 |
| ② 分层架构图（mermaid graph） | subgraph 表达 DDD 四层（UI=view/viewmodel；App=coordinator/DI；Domain=usecase/repository 接口/domain-model；Infrastructure=repository 实现/external）；箭头方向符合分层依赖律（运行期调用 UI→App→Domain←Infrastructure，Domain 零依赖）；图中节点逐个回查归属表 | 缺图 P1（G6）；依赖方向逆 Domain→App→Infrastructure→UI 单向（如 usecase→viewmodel、domain-model→external）P1（分层依赖律）；UI 直连 Infrastructure 持久化 P1；图含归属表外组件 / Manager·Helper·Util 无行为来源结构 P1 |
| ③ 页面流图（仅 UI 需求） | 节点=SwiftUI View（标路由 / `NavigationDestination` 枚举值），边=导航动作（标触发 BHV 编号 + 入参要点 + 经 AppCoordinator 的方法名如 `navigateToStoryDetail`）；覆盖新增 / 修改全部页面，含失败 / 取消 / 权限拒绝去向；非 UI 需求 N/A + 依据 | 缺图（UI 需求）P1（G6）；边未经 AppCoordinator / 出现 View 间直连导航 P1（分层依赖律）；缺失败 / 取消路径 P2；非 UI 需求缺 N/A 依据 P2 |
| ④ 核心 UC 表 | 列齐全（`uc_id` / `uc_title` 动词开头 / `actor_or_trigger` / `source_refs` / `goal` / `priority`）；UC 从验收场景提炼，非 BHV 一对一重排（一 UC 覆盖 2~5 BHV 为常态） | 缺表 P1（G6）；UC = 单 BHV 重排 P2；缺 `priority`（P0/P1 对应）P2 |
| ⑤ UC 承接表 | `bhv_refs` 与行为集合双向闭合（§3.2）；`owner_refs` 写归属表 `UNIT-<slug>` 且 ⊆ 归属表；`index_refs` ⊆ 第 7 章 `chapter_target` | 任一向断链（行为无 UC 来源 / UC 无行为承接 / owner_refs 不在归属表 / index_refs 不在第 7 章）P1 |
| ⑥ 时序图策略表 | 逐 UC 三选一齐备（`独立` / `合并` / `豁免`）；独立 / 合并有可定位 `sequence_section`；合并有 `merged_coverage` 覆盖清单；豁免有 `exemption_reason` + 最小行为链 | 缺表 P1（G6）；占位锚点残留 P1（G7）；豁免缺理由 P1 |

`sequenceDiagram` 细查（每张抽查，G7）：

- 参与者必须用真实 owner 名（`view` / `viewmodel` / `usecase` / `repository` / `coordinator` / `external` / `domain-model`），覆盖 `View → ViewModel → UseCase → Repository(接口) → Infrastructure(repository 实现 / external) → 返回 / 状态推进` 链路（按实际裁剪），导航穿插 `AppCoordinator`。
- 禁止出现的边（命中即分层依赖律违例 P1）：`view` 直连 `repository` 实现 / WCDBSwift / `external`；`view` 间直连导航绕过 `coordinator`；`viewmodel` 直连 `external` / 持有 WCDBSwift 句柄；`usecase` 反向调 `viewmodel`。
- 图中步骤编号与图下文字详述一一对应；失败分支有表达（`alt` 块或独立图，对应 §3 失败路径行为）。编号 / 详述不对应记 P2；方向违例记 P1。

## 4. 跨章一致性取证（规则 7 的四组双向核对）

1. **架构图组件 ⊆ 归属表 owner 集合**：图中节点逐个回查归属表；多出（「图比表大」=补造）→ P1；图中出现 Manager/Helper/Util 等无行为来源结构 → P1。
2. **系统边界图外部依赖 ↔ `external` owner**：图中网络 / WCDBSwift / SDK / 推送 / 端侧·远程 LLM 等外部依赖必须在归属表有 `external` owner；互查差集 → P2（影响 G6 / G3 时升 P1）。
3. **UC 承接表 `bhv_refs` ↔ BHV-NNN 行为集合**：双向闭合；行为无 UC 来源 / UC 无行为承接 → P1。
4. **页面流图边 ↔ `coordinator` 导航行为**：页面流图每条导航边必须对应归属表 coordinator owner 的导航方法；`index_refs`/`owner_refs` ↔ 第 7 章 `chapter_target` 断链 → P1；技术决策 `detail_expansion_targets` 指向不存在的第 7 章索引条目 → P2。

## 5. 分层依赖律违例形态（命中即 P1，不得给通过性结论）

按 L1 §4 硬约束 + golden-path §2.1 / §11 逐形态对照（归属硬基准，命中即 fail）：

- **Domain 非零依赖**：`usecase` / `repository` 接口 / `domain-model` 出现对 App / Infrastructure / UI 的依赖（如 `usecase` `import SwiftUI`、`domain-model` 内嵌 WCDBSwift `TableCodable` 持久化逻辑、`usecase` 直接 `import WCDBSwift`）。
- **依赖方向逆单向**：违反运行期调用方向 UI→App→Domain←Infrastructure（如 `usecase` 反向 import `viewmodel`、`domain-model` import `external`）；或出现循环依赖 / 跨层直连。
- **View 间直接导航**：`view` 之间 `push`/`present`/`NavigationLink` 跨页跳转而未经 `coordinator`。问题描述写明「View 间不能直接导航，必须经 AppCoordinator」。
- **View 直连持久化**：`view` 直接访问 WCDBSwift / `repository` 实现 / `external`。问题描述写明「View 不能直接访问持久化，必须经 repository（且经 viewmodel→usecase）」。
- **ViewModel 越层**：`viewmodel` 直接 import `external` / `repository` 实现类 / 直接持有 WCDBSwift 句柄（必须经 `usecase` → `repository` 接口）。

golden-path 硬规则违例（锁定项，命中即 P1）：

- DI 非 FactoryKit `@Injected`（手动 `init` 注入依赖、`view` 的 `body` 里 init ViewModel、单例硬编码顶替可注入依赖）。例外：`ThemeManager.shared` / `ToastManager.shared` / `Logger` 等纯横切工具单例（项目既有约定）。
- Repository 模式缺失（`usecase`/`viewmodel` 直接拼 SQL / 网络，未经 `IXxxRepository` 接口；接口与实现混在一个文件）。
- 错误非 `enum Error` 分层定义（裸 `NSError` / 字符串错误穿层；持久化原始 WCDBSwift 错误裸抛到 UI，未在 repository 边界转 `PersistenceError`）。
- 持久化非 WCDBSwift（出现 CoreData / SwiftData 选型即 P1，违反全局钉死约定 + L1 §1-P3b）。
- `viewmodel` 非 `ObservableObject + @Published`；自创第八类 doc_type / 用七类之外的 token。

## 6. 共享能力归属取证（G5，规则 11）

按 L1 共享能力条款区分四类，取证其归类与边集合：

- **Utility 纯函数技术能力**：无状态格式化 / 转换（如日期格式化、字符串裁剪）；落 UI 或独立工具，不进 Domain 业务 owner，不参与 DI 业务依赖装配。
- **下层公用 `usecase` / `repository` 单元**：被多 feature 复用的业务编排 / 数据访问合同（如 story-verse-mac `AppInitializationService` 协调多 usecase、`IStoryRepository` 被多处消费）。
- **普通业务单元**：单 feature 私有的 owner。
- **横切**：`coordinator`（导航 + FactoryKit DI 装配）/ `external`（网络 / SDK / WCDBSwift / 三方集成）。

判级：同域业务步骤误下传（普通行为被建模为独立下层单元而无独立边界证据，应收回父单元）、技术能力被误归类为业务 owner（Utility 进 Domain 业务 owner）、缺归属边集合 → P2 起步；影响 G2（归属错位）/ G5（共享能力承接缺口）时升 P1。

## 7. 承接索引与 L2 状态取证（G4 / G9，规则 12）

- **owner 覆盖**：归属表全部 owner 必须被至少一个索引条目覆盖（差集为空）。
- **doc_type 合法**：每条 `detail_doc_type` ∈ 七类裸 token；出现自创类型（`transport-handler` / `service` / `controller` / `datasource` / `dao`）→ P1。
- **逐文件（full 链）**：每条索引有 `chapters/<slug>.md` 目标文件名。
- **L2 状态分两组**（对照 L1 §2.7 钉死供给状态）：
  - 已出 3 类 **full**：`viewmodel`（`detail-type-viewmodel.md`，与 flutter `controller` 对应位）、`usecase`（`detail-type-usecase.md`，与 flutter `usecase` 对应位）、`repository`（`detail-type-repository.md`，与 flutter `repository-datasource` 合并对应位）。命中时须能回指对应 L2 八问承接深度；指向的 detail-type-*.md 口径与归属表 doc_type 不一致 → P2。
  - pending 4 类：`domain-model` / `view` / `coordinator` / `external`。命中须标注 `l2_status: pending` + 给出按详细 L1 合同八问（详细 L1 §3）展开的 L2 豁免计划。缺 `l2_status` 标注或缺豁免计划 → P1（G9）；`pending` 是 L1 §2.7 钉死的合法缺省承载状态，标注齐全时不计为缺口（不得误判为缺陷）。

## 8. 越界取证（L1 §5，规则 15）

概要只闭合「边界、语义、链路、取舍、索引」。以下在概要正文展开即越界（P2 起步，给最小回收方案——移入承接索引的 `detail_expansion_targets`）：

- Swift 方法签名 / 协议方法、字段级合同、WCDBSwift 表结构 / `TableCodable` 字段 / 迁移 DDL、具体 API 路径与 JSON schema。
- SDK 初始化 / 调用参数、FactoryKit `register` 闭包细节、LLM prompt 正文、配置项取值。
- Swift 代码 / 伪代码 / `private extension` 内部实现安排。
- 把 pending 四类的合同八问字段写成详细正文（概要只写归属与索引）。
- secret value 落盘（P1，不可只回收）；未选定决策写成已选定（P1）。

## 9. LLM / agent / prompt 承接取证（规则 16，缺口归 G8）

概要出现端侧 / 远程 LLM、agent、prompt 驱动调用时（story-verse-mac 实测 `OnDeviceLLMAdapter` / `LLMUseCase` 链路）：

- 逐次逻辑调用承接、`prompt_owner`、运行期上下文来源、上下文获取 / 编排行为锚点（落 `usecase`，不落 `external`）、prompt 组装 owner、`detail_prompt_target`。
- provider / model / SDK / invocation mode / config / external / 凭证策略对应的 `technology_decision_handoff[]` 目标。
- prompt 业务组装归 `usecase`，`external`（LLM adapter）只做集成边界 / 技术错误归一，不得在 adapter 内做「低置信度则降级业务规则」类业务判定。缺口 → P1（G8）；概要不得写完整 prompt 正文（越界）。

## 10. 严重度判级规则（对照 L1 §8）

- **P1（阻断，不可进入详细设计）**：G1~G9 任一缺失；分层依赖律违例（§5：Domain 非零依赖 / 方向逆 / 循环 / 跨层 / View 间直连导航 / View 直连持久化 / ViewModel 越层）；FactoryKit 以外的 DI；Repository 模式缺失；CoreData/SwiftData 出现；`enum Error` 未分层且穿层（裸抛到 UI）；非豁免 UC 时序图缺失 / 占位残留；缺 `compliance_basis`；真实 secret value 落盘；粗粒度核心行为；P0/P1 核心能力漏承接；行为无 owner / owner 非七类 / 自创 doc_type；pending 四类缺 `l2_status` 标注或缺豁免计划；owner 未被索引覆盖；未选定决策被下游引用；双主定义（README/design.md 与 design-main 两套正文）。
- **P2（应修，可带明确假设进入）**：归属三问空洞（「同上」）；命名反模式（名词先行 / 含混 Manager·Helper 后缀）；失败 / 取消去向缺失；字段不全的技术决策（未被下游引用时）；轻度越界（少量签名 / 字段合同——给回收方案）；图文局部不一致；共享能力误归类（未影响主链）；`enum Error` 未分层但未穿层；已出 3 类 L2 口径与归属表局部不一致；编号缺失 / 重号 / 跨层混用。
- **P3（建议）**：表述与术语一致性；一句话架构格式偏离模板但语义完整；其它格式偏离。
- 判级冲突时取高；同一根因的多处表现合并为一条 finding（列全部位置）。需求层缺陷（行为缺失 / 矛盾 / 范围漂移）→ 不在概要修，标注「回退需求阶段」（不进 P 级阻塞计数，但阻止「可进入」结论）。

## 11. 结论判定（三选一，互斥）

- 存在 ≥1 条 P1 → **不可进入**（列阻塞清单 + 修订形态建议，局部修订 vs 文档级重构按 L1 §9）。
- 仅 P2 且每条已有明确假设 / 修订路径，无 P1 → **带明确假设可进入**（列假设、依据、影响范围、验证时点）。
- G1~G9 全部已闭合，无 P0/P1（P3 可遗留）→ **可进入详细设计**。
- 结论为「可进入」/「带假设可进入」时必须给 Gate 收口指引（用户终端 confirm，见 SKILL.md「Gate 收口」与 review-output.md 分支二第 6 节）。

## 12. 修订形态判定（对照 L1 §9，输入到 finding 的 suggestion）

- **局部修订**（在原文档上改）：补一条行为 / 失败路径、补一行归属三问理由、补一条索引条目、补 / 改一张图、改措辞、补 `l2_status` 标注与豁免计划、回填一个时序图占位锚点、补 `compliance_basis`、把越界签名移入 `detail_expansion_targets`。
- **文档级重构**（重做对应章节，禁止用局部补丁掩盖错误模型）：归属模型错误（owner 大面积错位 / doc_type 用错层 / Domain 依赖外泄被系统性默许）；行为枚举从名词 / SwiftUI View 名 / 组件名倒推；索引与归属表系统性脱节；架构总览与正文两套口径（图中组件与归属表不一致 / 依赖方向矛盾）；自创 doc_type 贯穿全文。
- 上游缺陷（需求行为缺失 / 矛盾 / 五要素不全）→ 回退需求阶段，禁止在概要补造业务规则或拍板未决 scope。
