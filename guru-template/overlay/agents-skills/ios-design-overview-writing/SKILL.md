---
name: ios-design-overview-writing
description: 用于撰写 Guru iOS 原生平台（典型形态：SwiftUI 主 + RxSwift 遗留，DDD 四层 Domain → App → Infrastructure → UI，Domain 零依赖，FactoryKit @Injected DI，Repository 模式，enum Error per domain，AppCoordinator 导航，WCDBSwift 持久化，ViewModel = ObservableObject + @Published）概要设计文档。按"判轨与设计包骨架、技术栈与约束确认（project-conventions C1~C5）、行为枚举（BHV-NNN 编号，按用户操作/系统反应/失败路径/生命周期四类）、四层 owner 归属判定（三问 + 分层依赖律自检，落 UI/App/Domain/Infrastructure 四层 + 七类 doc_type）、架构总览人审视图（一句话架构/分层架构图/页面流图/核心 UC 表/UC 承接表/时序图策略表）、technology_decision_handoff 技术决策承接清单（含 credential strategy）、详细设计承接索引（doc_type 七分类 viewmodel/usecase/repository/domain-model/view/coordinator/external，逐 UNIT 落 chapters/<slug>.md）、架构就绪自检 G1~G8"的顺序推进；把概要写到"详细设计可直接展开而不需要重新决定边界"，但不进入可编码合同层（Swift 方法签名/@Published 字段全集/enum Error 全集与 case/FactoryKit Container 注册项/WCDBSwift 表结构/SDK 初始化参数/secret value 禁写）。规则唯一来源是 .trellis/spec/harness/overview/ 的 L1 SSOT 与 .trellis/spec/guides/golden-path.md；本 skill 只编排写作动作，不复写规范正文。
---

# Guru iOS 概要设计撰写

> 层级契约：L1（`.trellis/spec/harness/overview/overview-structure-single-source.md`）承载章节合同、归属方法与 Gate 完成条件；`golden-path.md` 承载分层依赖律与硬红线（golden-path 锁定项）；`project-conventions.md` 承载项目槽位取值；本 SKILL.md 只做装载顺序、边界、执行规则、阶段流程与输出要求；`references/` 只承载分章写法细则、模板与示例。冲突时 golden-path 硬红线 > L1 章节合同 > project-conventions 槽位 > references > 本文件。

## 目标

- 输出可评审、可追踪、可指导详细设计的 Guru iOS 原生概要设计文档；每个关键章节同时落出生成动作（正向写什么）、约束边界（不写什么 / 不适用什么）与可验证信号（怎么判定写对了）。
- 以行为驱动组织概要：先枚举行为空间（`BHV-NNN` 编号），再判定唯一 owner 归属（三问理由），ViewModel/UseCase/Repository/View 等单元只在行为归属后形成——禁止「先有 `HomeViewModel` 再倒推它做什么」的名词先行。
- iOS 行为以「用户操作 / 系统反应 / 失败路径 / 生命周期」为枚举单位；归属 owner 一律落在四层之一：`UI`（SwiftUI View + ViewModel 状态容器）、`App`（AppCoordinator 导航 + FactoryKit DI 装配）、`Domain`（UseCase 业务编排 + Repository 接口 + 实体/值对象/enum Error）、`Infrastructure`（Repository 实现 + 网络/SDK/WCDBSwift 持久化/第三方集成）。
- 在落 owner 前先做能力泛化抽象：识别下层承接对象是在形成稳定业务编排（`usecase`）、数据访问合同（`repository` 接口在 Domain / 实现在 Infrastructure）、可被任意层导入的实体或值对象或 `enum Error`（`domain-model`，零依赖）、UI 状态容器（`viewmodel`）、纯展示 + 输入入口（`view`）、导航 + DI 装配一等合同（`coordinator`）、外部既有边界（`external`：网络 / SDK / WCDBSwift / 三方），还是只把同一业务能力换名下传（不抽象）。
- 先完成「架构总览（人审视图）」再进入索引细化：一句话架构、分层架构图、页面流图、核心 UC 表、UC 承接表、时序图策略表是架构就绪门禁（L1 §2.5），不是可选的可读性优化。分层架构图箭头方向必须符合分层依赖律（`Domain → App → Infrastructure → UI` 单向无环，`Domain` 零依赖）。
- 把概要写到详细设计可直接展开：承接索引为每个 owner 提供 `chapter_target` 来源锚点（full 链逐条落到 `chapters/<slug>.md` 文件名），并标注 `detail_doc_type`（七分类）与 `l2_status`。
- 守住概要深度边界（L1 §5）：只闭合边界、语义、链路、取舍、索引；**不写** Swift 方法签名、`@Published` 字段全集、`enum Error` 全集与每个 `case`、FactoryKit `Container` 注册条目、WCDBSwift 表结构 / `ColumnCodable`、SDK 初始化 / 调用参数、网络请求体字段、secret value——这些可编码合同由详细设计承接，概要只说明「由哪个 `chapters/<slug>.md`（哪类 doc_type）展开」。
- 命中外部 provider / 对象存储 / 云服务 / 三方 SDK / 推送 / IAP 选定等架构显著技术选择时进入 `technology_decision_handoff[]`（含 credential strategy：不保存 secret value，只写 `api_key_keychain_ref` / Info.plist 注入 / 默认凭证来源 / Keychain 引用）。
- 在进入详细设计前完成架构就绪收敛（L1 §6 G1~G8）。

## 与官方 trellis 工具的职责边界（务必先读，避免越权）

本 skill 是「设计**写**」——承接 `prd.md` 产出，生成概要 design 章（行为归属 + 架构总览 + 承接索引）。它与下列两个独立环节职责不重叠、不互相替代：

- **vs `trellis-brainstorm`（需求/构思阶段）**：brainstorm 负责把模糊意图收敛成 `prd.md` 的 `BHV-NNN` 行为规格、P0/P1 核心能力、失败路径与验收场景。本 skill **消费** prd，不生成 prd，不补造业务规则——prd 缺失或核心能力不可定位时只能产草稿并记显式假设，不得凭空生成 P0/P1。需求侧合法声明「无 P0/P1」时记录依据，不补造核心能力主线。
- **vs 设计**审**（review evidence Gate）**：写完后由配套的 `ios-design-overview-review` skill 做 clean-context review，并用 `record-review overview` 写入当前 digest 的 clean/findings 证据；两个不同 `run_id` 的 clean review 后才可进入下一阶段（详细设计）。判的是四层归属是否正确、是否违反分层依赖律（`Domain` 是否真零依赖、`View` 是否直连持久化/直接导航）、架构视图是否就绪、承接索引是否覆盖全部 owner 且七类 doc_type 取值合法。
- **vs `trellis-check`（代码质检）**：`trellis-check`（对应实现 / 审核 Gate）查的是**代码层**质量——`xcodebuild` / SwiftLint / `xcodebuild test`（XCTest 或迁移后的 Quick/Nimble）证据、secret 合规、存量违例豁免。本 skill 不产 Swift 代码、不跑构建测试，概要阶段不输出任何编译 / 测试证据。
- 一句话定位：**brainstorm 定「做什么」→ 本 skill 概要定「分给哪层、边界在哪、谁承接展开」→ overview review evidence 判「能否进详细」→ 详细写「可编码合同」→ trellis-check 判「代码达标」**。本 skill 只占第二格，越界即停。

## 最小输入与自动补全

- 接受需求产物路径（`prd.md` / 正式需求包）、设计目标、feature 边界（落在哪个 `UI/Features/<Feature>/` + 对应 `Domain` 子能力）、已有草稿或 `design_package` 路径。
- 优先读取需求核心能力清单（P0/P1）与失败路径章节；不可定位时仍可产出概要草稿并记录显式假设，但**不得凭空生成 P0/P1**，不得宣称可进入详细设计。
- 信息不足时收敛到最小可写范围，**不擅自补齐高风险业务规则**；未决问题显式列出并向用户提问（一次 1~4 个关键问题）。
- 有历史设计版本时，优先复用命名、章节和术语约定（先 `rg` 检索既有 `BHV-NNN` / `UC` / `UNIT-<slug>` / View / ViewModel / UseCase / Repository 名）。

## 执行模式（按需切换）

- **一次性交付模式（默认）**：按分阶段流程内部连续推进，一次性完成全稿或本轮目标；信息不足用显式假设，不因等待确认而阻塞。
- **共创式迭代模式**：仅当用户明确要求逐阶段确认或只看某一阶段时启用；一次只产出当前阶段内容。
- 模式必须在输出中显式标注。

## 装载顺序（硬前置，任一失败即终止）

1. 读 L1 概要 SSOT `.trellis/spec/harness/overview/overview-structure-single-source.md`；不可用 → 终止并提示先安装 guru spec 模板（`trellis init -t guru-ios-native`）。
2. 读通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律 `Domain → App → Infrastructure → UI` 单向无环、`Domain` 零依赖、FactoryKit `@Injected` DI 禁手动初始化、Repository 模式强制、`enum Error` 分层定义、WCDBSwift 持久化禁 CoreData/SwiftData、ViewModel = `ObservableObject` + `@Published`、private 方法在 `private extension`——这是 owner 归属判定与红线自检的基准）。
3. 读 `.trellis/spec/conventions/project-conventions.md` 并执行校验清单 C1~C5；任一不过（UI 框架 / 网络层 / 日志 / JSON 修复策略 / 测试框架 / i18n / 主题 / feature 模块结构 / mock 生成 / 构建自动化等槽位缺失或与硬规则冲突）→ 终止并提示先填写项目约定。取值一律引用槽位（`SLOT-NN` 裸 token），不在概要另定。
4. 判轨：读 task.json `guru_chain`（`guru_after_create` 默认 `full`）。full=完整五阶段链（新 feature 模块、新导航流、新 Domain 子能力、持久化结构变更、三方 SDK 接入等高风险需求）→ 走目录级设计包；light=同 feature 内小迭代且获用户同意降级 → 任务内单文件 `design.md`。full 链确认 / 声明 task.json `design_package`（相对 repo root，如 `docs/design/<feature>/`）。
5. 详细阶段承接索引需要 doc_type 与 L2 状态时读详细 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；需要类型差异锚点时读已出三类 L2 `.trellis/spec/harness/detail/detail-type-{viewmodel,usecase,repository}.md`（对应 flutter controller/usecase/repository-datasource 三类一一对应）；其余四类 `domain-model / view / coordinator / external` 为 pending，按 L1 合同八问展开并标注 `l2_status: pending` + `L2豁免：<doc_type> 理由：…`（full 链须 L2 豁免声明，否则详细 Gate 拦截）。
6. 定位需求产物（`prd.md` / 正式需求包）；缺失走 L1 显式假设路径。
7. 需要分章写法细则与模板时读 `references/chapter-guide.md`；需要成稿样例时读 `references/examples/design-main-minimal.md`。

## 边界约束（概要只闭合，不展开）

- **只写概要，不写详细实现**：概要闭合「边界 / 语义 / 链路 / 取舍 / 索引」五件事；可编码合同（下列项）全部交给详细设计，概要只写「由哪个 `chapters/<slug>.md`（哪类 doc_type）承接」。
  - 禁写：Swift 方法签名（`func loadStories() async throws -> [Story]` 级）、`@Published` 字段全集与初值、`enum XxxError` 全集与每个 `case` 文案、FactoryKit `Container` 注册条目（`Container.shared.xxxRepository`）、`@Injected` 注入点逐个清单、WCDBSwift 表结构 / `ColumnCodable` / 索引、`DatabaseManager` 建表语句、网络请求 URL / Header / Body 字段、SDK 初始化 / 调用参数、超时 / 重试数值、Keychain / secret value。
  - 可写（概要应写）：行为空间与 GWT 语义、行为 → 四层 owner 归属与三问理由、分层依赖边（架构图箭头，`Domain` 零依赖）、关键取舍 / ADR、技术决策承接清单（决策点 + owner 层 + 详细落点 + credential strategy）、页面流与路由意图（走 `coordinator`，不直接 View → View）、UC 承接链、`chapter_target → detail_doc_type` 索引。
- **分层依赖律是归属硬基准（golden-path 锁定，不可豁免，违反直接 fail）**：
  - `Domain` 零依赖——`UseCase` / `IXxxRepository` 接口 / 实体 / 值对象 / `enum Error` 不 import `App`、`Infrastructure`、`UI`、也不 import 网络 / SDK / WCDBSwift；把网络调用、WCDBSwift 写入、SwiftUI 类型塞进 Domain 即归属错误，必须回退重判。
  - 依赖方向 `Domain → App → Infrastructure → UI` 单向无环；`Repository` 接口在 `Domain`、实现在 `Infrastructure`，UI/App 只依赖接口（依赖倒置），不直接 import 实现。
  - 禁 View 间直接导航——View → View 直接 push/present 即违例，必须走 `coordinator`（`AppCoordinator`）。
  - 禁 View 直接访问持久化——View / ViewModel 直接 import `DatabaseManager` 或 WCDBSwift 即违例，必须走 `repository` 接口。
- **外部触发边界**：架构图与 sequenceDiagram 中外部触发（用户手势 / 系统生命周期回调 / 推送）只能进入 `UI`（View 输入）或 `App`（生命周期 / 深链入口），**不能**让外部直接调用 `UseCase` / `Repository` 实现 / `external`；发现直连先补显式入口（View 或 Coordinator）。
- **纯函数技术能力不是层、不是依赖对象**：业务无关纯函数（格式化、日期 / 随机数封装、纯算法）是可随时调用的纯函数集合，概要只标「纯函数技术能力 + 调用方使用锚点」，不写成 owner 行为、不进 ViewModel/UseCase 的运行时依赖边、不作为 FactoryKit 装配对象；业务判定（「该故事是否可发布」「会话是否过期」）留在 `usecase`，纯算法直接调用。
- **横切一等合同单独承接**：`coordinator`（导航 + FactoryKit DI 装配）、`external`（网络 / SDK / WCDBSwift 持久化 / 第三方出站合同）不混入 UI/Domain 行为归属，作为独立 doc_type 在承接索引落项；命中外部 provider / 存储 / 云服务 / 三方 SDK 时必须带 credential strategy。
- **修订纪律**：按 L1 先判定局部修订 vs 文档级重构；发现需求缺陷回退需求阶段（brainstorm），不在概要补造业务规则；发现归属错回退归属判定章重判，不在下游补救。

## 执行规则

1. 共享规范（章节合同、图表合同、归属方法、Gate 完成条件）一律以 L1 为准，硬红线以 golden-path 为准；本 skill 与 references 不重复维护规范正文。
2. 默认一次性交付模式：按阶段内部推进，不要求用户逐阶段确认；只在出现高风险未决项时暂停提问（一次 1~4 个）。
3. 显式假设必须标注依据、影响范围、验证时点，并落盘到 `design-main.md`（或 light 链 `design.md` §概要）对应章节——不允许只在会话输出里口头声明。
4. 阶段 0 必须完成判轨落盘：full 链建立设计包骨架（`README.md` + `design-main.md` + `chapters/` 空目录）并把包路径写入 task.json `design_package`；任务内 `design.md` 只写指针 + 摘要。light 链直接写 `design.md` §概要。
5. 阶段 0 必须确认技术栈基线并明确 feature 边界：本任务落在哪个 `UI/Features/<Feature>/`，复用还是新建对应 `Domain` 子能力（UseCase / Repository 接口 / 实体）与 `Infrastructure` 实现；取值（UI 框架 SwiftUI 主 + RxSwift 遗留→纯 SwiftUI、网络层、日志、测试框架、i18n、主题 `ThemeManager`、mock 生成、构建自动化等）一律引用 project-conventions 槽位 `SLOT-NN`，不在概要另定。
6. 行为枚举（阶段 2）按 iOS 四类顺序（**用户操作 → 系统反应 → 失败路径 → 生命周期**），逐条 Given/When/Then + `### BHV-NNN <短名>` 编号标题（`BHV-NNN` 取 prd 标题口径）；每条满足 L1 粒度标准（有前置、有触发、有状态变化、有失败路径）；禁止从 View / ViewModel / UseCase 名出发。`BHV-NNN` 创建后不复用、不重排，删除留洞，下游裸 token 引用。
   - ✅ `### BHV-012 加载故事列表` — Given 用户已登录且进入首页 When `HomeView` `onAppear` 触发 Then ViewModel 调 UseCase 拉取 → Repository 命中 WCDBSwift 缓存 → 更新 `@Published stories`；缓存空时 Repository 实现走网络 → 写回；网络失败抛 `enum Error` → ViewModel 置错误态展示重试。
   - ❌ `### BHV-012 处理首页` — Given 有页面 When 打开 Then 显示数据。（无前置、无触发源、无失败路径、无状态变化）
7. 归属判定（阶段 3）按 L1 判定表给每条行为唯一 owner（四层 `UI` / `App` / `Domain` / `Infrastructure`，并细化到七类 doc_type）+ 三问理由（为什么属于它 / 为什么不属于别人 / 为什么需独立存在）；对照分层依赖律自检无违例（`Domain` 零依赖 / 单向无环 / View 不直接导航 / View 不直接访问持久化）；一个 UI 状态只能有一个写 owner（同一 `@Published` 状态在两个 ViewModel 里写 = P1，回退重判）。归属表逐行以 `BHV-NNN` 开头。
   - owner 层 → doc_type 对应：`UI` → {`view`, `viewmodel`}；`App` → {`coordinator`}；`Domain` → {`usecase`, `repository`（接口侧）, `domain-model`}；`Infrastructure` → {`repository`（实现侧）, `external`}。`repository` 合并接口（Domain）+ 实现（Infrastructure）为一类。
8. 命名遵守 L1 与 golden-path：View=Feature + `View`（`HomeView`）；ViewModel=Feature + `ViewModel`（`HomeViewModel`，`ObservableObject` + `@Published`）；UseCase=动词短语 + `UseCase`（`LoadStoriesUseCase`）；Repository 接口=`I` + 领域名 + `Repository`（`IStoryRepository`），实现=领域名 + `Repository`（`StoryRepository`）；导航 owner=`AppCoordinator`。设计单元 `UNIT-<slug>` 体现 feature + 层角色（`UNIT-home-view` / `UNIT-home-viewmodel` / `UNIT-load-stories-usecase` / `UNIT-story-repository` / `UNIT-story-model` / `UNIT-app-coordinator` / `UNIT-story-api-external`）；行为=动词 / 动词 + 宾语；list/one/get/fetch 语义区分。
9. 架构总览（阶段 5）按 L1 §2.5 六件套合同产出：一句话架构 → 分层架构图（mermaid）→ 页面流图 → 核心 UC 表 → UC 承接表 → 时序图策略表；图中组件必须与归属表一一对应，不得出现归属表之外的组件；分层架构图箭头方向必须符合 `Domain → App → Infrastructure → UI` 单向无环且 `Domain` 节点零入边依赖（只被依赖、不依赖他层）。
10. 时序图策略表逐 UC 声明 独立 / 合并 / 豁免；早期可用计划锚点，**送审概要 Gate 前非豁免 UC 必须回填可定位的真实 `sequenceDiagram`**（参与者用真实组件名如 `HomeView` / `HomeViewModel` / `LoadStoriesUseCase` / `StoryRepository` / `DatabaseManager`，步骤编号与详述一一对应；外部触发从 View/Coordinator 进入，不直连 UseCase/Repository 实现）；占位残留不得宣称可送审。
11. 技术决策承接（阶段 6）按 L1 §2.6 字段合同逐条建立 `technology_decision_handoff[]`：决策点 / 选定值（或显式「未选定」）/ owner 层 / 详细落点（`chapters/<slug>.md`，通常落 `external` 或 `coordinator`）/ 关键取舍锚点（回指架构驱动章 ADR）。技术选择命中时必须先在架构驱动章形成 ADR / 关键取舍再建清单。命中外部 provider / LLM / 对象存储 / 云服务 / 三方 SDK / 推送 / IAP 时必填 credential strategy：**不保存任何 secret value**，优先 Keychain 引用 / Info.plist 注入 / 默认凭证来源，通过 `api_key_keychain_ref` / `credential_ref` / `default_credential_source` 表达；「未选定」必须显式标注，禁止让下游引用未选定决策。查询分页先判定普通分页还是连续消费语义，普通分页不触发游标决策。
12. 承接索引（阶段 7）覆盖归属表全部 owner + 全部横切一等合同；full 链每条附 `chapters/<slug>.md` 目标文件名（文件本体详细阶段产出）；`detail_doc_type` 取值只用七分类（见下表，裸 token），命中 pending L2 类型（`domain-model` / `view` / `coordinator` / `external`）时在此阶段就写明 `L2豁免：<doc_type> 理由：…`（按 L1 合同八问展开）或改走先补 L2 路径。
13. 概要禁写项（见「边界约束」）全程生效：发现自己在写 Swift 方法签名、`@Published` 字段全集、`enum Error` 全集、FactoryKit 注册条目、WCDBSwift 表结构、SDK 参数即停下，回收到「交给详细设计展开」的索引条目。
14. UC 与行为双向回指（L1 §3.2）：每条 `BHV-NNN` 回指 ≥1 个 UC；UC 承接表 `bhv_refs` 与行为集合双向核对，不留孤儿行为、不留空 UC。
15. 阶段 9 自检按 L1 §6 G1~G8 逐项输出（满足 / 缺口 + 闭合计划），full 链写成 `design-main` 的「架构就绪自检」章节；存在未闭合 G 项不得送审，不得用概括性「基本满足」替代逐项证据。其中分层律 G 项必须逐条核对四条硬红线（`Domain` 零依赖 / 单向无环 / View 不直接导航 / View 不直接访问持久化）。
16. 产物语言：辅助性正文一律中文；英文仅限代码标识符、命令、路径、框架 / 库名（`SwiftUI`、`RxSwift`、`FactoryKit`、`WCDBSwift`、`@Injected`、`@Published`、`ObservableObject`）、协议字段、缩写与原文引用。
17. 完稿后提示送审：加载 `ios-design-overview-review` 做 clean-context review；review worker 用 `guru_gate.py record-review overview <task_dir> ...` 记录证据。当前 digest 下两个不同 `run_id` 的 clean review 后 overview 自动通过并进入详细设计；不要运行 `confirm overview`，也不要做任何 overview 人工收口。

## iOS 详细 doc_type 七分类（承接索引取值，全程唯一，禁止改名 / 增减 / 换数）

承接索引 `chapter_target → detail_doc_type` 的 doc_type 取下表之一；引用裸 token。**不得自创 `transport-handler` / `service` / `controller` 之类类型名**，也不得照抄 flutter（controller/datasource）或 Go（transport/biz）的类型名——iOS 一律以本表七类为权威。`l2_status` 标注当前是否已提供类型差异 L2 文件（pending 类型须 `L2豁免：<doc_type> 理由：…` 或先补 L2，否则详细 Gate 拦截）。

| doc_type | owner 层 / 覆盖对象 | 证据锚点（iOS 形态） | L2 状态 |
|----------|--------------------|----------------------|---------|
| `viewmodel` | `UI` — `ObservableObject` + `@Published` 状态容器，绑定 View，调用 UseCase，把 Domain 结果映射为展示态，承接错误态 / 加载态，private 方法在 `private extension` | `UI/Features/<Feature>/<Feature>ViewModel.swift` | **已出 L2**（对应 flutter controller） |
| `usecase` | `Domain` — 业务编排（零 UI 依赖），协调 Repository 接口与 domain-model，执行业务判定与不变量校验，定义 / 抛出业务 `enum Error` | `Domain/UseCases/<Verb><Noun>UseCase.swift` | **已出 L2**（对应 flutter usecase） |
| `repository` | `Domain`（接口 `IXxxRepository`）+ `Infrastructure`（实现）合并一类 — 数据访问合同；接口在 Domain 声明、实现在 Infrastructure 落网络 / WCDBSwift / 缓存策略与错误转换 | `Domain/Repositories/IStoryRepository.swift` + `Infrastructure/Repositories/StoryRepository.swift` | **已出 L2**（对应 flutter repository-datasource） |
| `domain-model` | `Domain` — 实体 / 值对象 / `enum Error` / 不变量；零依赖、可被任意层导入 | `Domain/Models/Story.swift`、`Domain/Errors/StoryError.swift` | pending（L1 合同八问 + `L2豁免`） |
| `view` | `UI` — SwiftUI `View`，只展示 + 输入，无业务，状态来自绑定的 ViewModel | `UI/Features/<Feature>/<Feature>View.swift` | pending（L1 合同八问 + `L2豁免`） |
| `coordinator` | `App` — `AppCoordinator` 导航（页面跳转 / present / deep link）+ FactoryKit DI 装配（`Container` 注册 / `@Injected` 接线）；View 间导航必经此层 | `App/Coordinators/AppCoordinator.swift`、`App/DependencyInjection/Container+*.swift` | pending（L1 合同八问 + `L2豁免`） |
| `external` | `Infrastructure` — 外部既有边界：网络（URLSession/Moya）/ 三方 SDK / WCDBSwift 持久化（`DatabaseManager`）/ 推送 / 云服务的出站合同与凭证策略 | `Infrastructure/Network/*.swift`、`Infrastructure/Persistence/DatabaseManager.swift` | pending（L1 合同八问 + `L2豁免`） |

> doc_type 与详细 L1 §2 同步维护；命中 pending 类型且无 `L2豁免` 声明即被详细 Gate 拦截。v1 已提供 `viewmodel / usecase / repository` 三类 L2；其余四类按 L1 合同八问展开。

## iOS 四层与写作顺序（依赖向下，写作自底向上）

- **依赖方向**（运行时调用与归属判定基准，golden-path 锁定）：`Domain → App → Infrastructure → UI` 单向无环，`Domain` 零依赖；`Repository` 依赖倒置（接口在 Domain，实现在 Infrastructure，上层只依赖接口）。
- **概要写作顺序**（自底向上，先定稳定零依赖层再定上层依赖）：① `domain-model`（实体 / 值对象 / `enum Error` / 不变量边界，零依赖）→ ② `repository`（数据访问合同边界：接口语义 + 实现承接的存储 / 网络策略）→ ③ `usecase`（业务编排与状态写 owner，零 UI 依赖）→ ④ `viewmodel`（UI 状态容器，绑定 UseCase）→ ⑤ `view`（展示 + 输入入口）+ 横切 `coordinator`（导航 + DI 装配）/ `external`（外部出站合同）一等合同。
- 该顺序只约束「概要里先把哪层的边界与归属定清楚」，不等于详细设计的编码顺序，也不改变运行时依赖方向。行为枚举与归属判定仍按 `BHV-NNN` 行为逐条进行，自底向上顺序用于组织归属判定章的边界叙述与承接索引的收敛节奏。

## 分阶段流程（writing 专属）

1. **阶段 0 判轨与骨架**：判轨落盘（规则 4）；技术栈基线 + feature 边界确认（规则 5，引用 `SLOT-NN`）；full 链建包骨架 + `design.md` 指针。
2. **阶段 1 README 与元信息**：full 链写 `README.md` 导航（不承载正文）+ `design-main` 元信息 / 修订历史。
3. **阶段 2 行为枚举**：第 1~2 章（设计约束与输入、行为集合）；按用户操作 / 系统反应 / 失败路径 / 生命周期四类枚举 `BHV-NNN` + GWT + 粒度自检。
4. **阶段 3 归属判定**：第 3 章归属判定表（owner ∈ {UI, App, Domain, Infrastructure} + 细化七类 doc_type + 三问理由）；分层依赖律自检（`Domain` 零依赖 / 单向无环 / View 不直接导航 / View 不直接访问持久化 / 唯一写 owner）；按自底向上顺序（domain-model → repository → usecase → viewmodel → view + coordinator/external）收敛边界叙述。
5. **阶段 4 关键取舍与 ADR**：第 3 章续——架构驱动、关键结构策略、关键取舍 / ADR；命中技术选择（三方 SDK / 网络栈 / 持久化策略 / RxSwift→SwiftUI 迁移取舍）先形成 ADR 再为阶段 6 清单埋锚点。
6. **阶段 5 架构总览**：第 4 章六件套（一句话架构 → 分层架构图 → 页面流图 → 核心 UC 表 → UC 承接表 → 时序图策略表）；本阶段建立人审链路，时序图可先计划锚点。
7. **阶段 6 技术决策承接**：第 5 章 `technology_decision_handoff[]`（决策点 / 选定值或未选定 / owner 层 / 详细落点 / credential strategy）。
8. **阶段 7 承接索引**：第 6 章 `chapter_target → detail_doc_type`（→ `chapters/<slug>.md`）；覆盖全部 owner + 横切一等合同；逐 `UNIT-<slug>` 落项；回填 UC 承接表 `index_refs`；pending L2 命中处写 `L2豁免` 或先补 L2。
9. **阶段 8 未决问题**：第 7 章显式列出 + 风险等级；无未决也须显式声明「无未决」。
10. **阶段 9 架构就绪收敛**：回填全部时序图占位 → 第 8 章 G1~G8 自检（含分层四红线逐条核对）→ 送审提示（规则 17）。

## 输出要求（writing 专属）

- 默认先给完整正文，再给结构化状态；共创式迭代模式只给当前阶段正文 + 当前阶段状态。
- 一次性交付模式默认输出下列字段：
  - `交付范围`（全稿 / 当前阶段）与 `执行模式`
  - `链型`（full/light）与 `概要主定义位置`（`design-main.md` / `design.md` §概要）
  - `feature 边界`（落在哪个 `UI/Features/<Feature>/`，复用 / 新建 Domain 子能力 + Infrastructure 实现清单）
  - `显式假设`（无 / 有：假设、依据、影响范围、验证时点）及 `落盘状态`
  - `项目约定校验状态`（C1~C5 逐项 通过 / 不过；不过即标终止原因）
  - `行为集合状态`（`BHV-NNN` 条数、四类分布、粒度自检结论）
  - `归属判定状态`（覆盖行为数、四层 owner 分布 + 七类 doc_type 分布、分层依赖律四红线自检结论、唯一写 owner 自检）
  - `架构总览状态`（六件套逐件 完整 / 缺失；缺失时标注影响 G6/G7）
  - `时序图承接状态`（非豁免 UC 是否全部有可定位 `sequenceDiagram`；占位残留清单；外部触发是否经 View/Coordinator 入口）
  - `技术决策承接状态`（无触发 / 已建立 / 存在缺口；未选定清单；命中外部 provider/SDK/云服务时 credential strategy 是否齐备）
  - `承接索引状态`（owner + 横切覆盖率；full 链逐 `UNIT-<slug>` → `chapters/<slug>.md` 清单；七类 doc_type 分布；pending L2 命中与 `L2豁免` / 补 L2 计划）
  - `架构就绪结论`（仅阶段 9 或全稿完成时输出 G1~G8 逐项 满足 / 缺口；草稿阶段只说明不可送审原因）
  - `需用户确认项`（若有）
- 完稿输出末尾给出送审与 review evidence 指引（规则 17）：加载 `ios-design-overview-review` 过概要 Gate；由 review worker 用 `record-review overview` 记录当前 digest 的 clean/findings 证据，区别于 `trellis-check` 代码质检。

## 参考资料

- 概要阶段中立规范（L1）：`.trellis/spec/harness/overview/overview-structure-single-source.md`
- 详细阶段 L1 与已出 L2：`.trellis/spec/harness/detail/detail-structure-single-source.md`、`.trellis/spec/harness/detail/detail-type-{viewmodel,usecase,repository}.md`
- 通用方法 SSOT（分层依赖律 `Domain → App → Infrastructure → UI` / 四条硬红线 / 禁止清单）：`.trellis/spec/guides/golden-path.md`
- 项目约定取值（C1~C5 硬前置：UI 框架 / 网络层 / 日志 / 测试框架 / i18n / 主题 / mock 生成 / 构建自动化等槽位）：`.trellis/spec/conventions/project-conventions.md`
- 分章写法细则与模板：`references/chapter-guide.md`
- 最小成稿样例：`references/examples/design-main-minimal.md`
