---
name: ios-design-detail-writing
description: 用于把 Guru iOS 原生（SwiftUI + DDD 四层 + FactoryKit DI + WCDBSwift）概要设计展开为可编码合同（详细设计）。full 链按 directory_precheck + chapter_loop 执行：WX-1~WX-6 前置检查通过后，按 iOS 自底向上写作顺序 domain-model→repository→usecase→viewmodel→view（横切 coordinator/external 随宿主层）逐章/小批次（每批 1~3 章）生成 chapters/<slug>.md，每批立即自动 review 并修复闭环，层级完成后跑 checkpoint。doc_type 严格用 IOS_BRIEF 钉死的七类（viewmodel / usecase / repository / domain-model / view / coordinator / external），命中已提供 L2（viewmodel/usecase/repository）读对应 L2，其余四类（domain-model/view/coordinator/external）按 L1 合同八问展开并标 l2_status: pending。每个设计单元按合同八问 + 章节正文骨架撰写（UNIT 编号、签名级接口、逐行为输入输出表、mermaid 时序、enum Error 表、测试映射）。规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT；本文件只做装载顺序、前置检查、chapter_loop 编排与输出要求。
---

# Guru iOS 原生详细设计撰写

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载规则正文、合同八问与完成条件；L2（`detail-type-viewmodel.md` / `detail-type-usecase.md` / `detail-type-repository.md`）承载已落盘类型的差异规则；`references/` 只承载逐类写法细则、模板与示例；本 SKILL.md 只做装载顺序、WX 前置检查、chapter_loop 编排与输出要求，不重定义规范正文。冲突时 `L1 > L2 > references > 本文件`。
> 平台事实唯一来源是本任务注入的 **IOS_BRIEF**：DDD 四层 `Domain → App → Infrastructure → UI`（Domain 零依赖）、SwiftUI 主 + RxSwift 遗留、FactoryKit DI（`@Injected`）、Repository 模式（接口在 Domain、实现在 Infrastructure）、`enum Error` per domain、`AppCoordinator` 导航、WCDBSwift 持久化、`ViewModel = ObservableObject + @Published`。doc_type、分层、owner 一律以 IOS_BRIEF 为权威，**禁止照抄 flutter（controller/page/datasource）或 Go（API/Biz/Utility/Data）的类型名**。

## 目标

- 把概要的 owner 与第 7 节详细设计承接索引展开为可直接编码的 iOS 合同：每个设计单元（`UNIT-<slug>`）回答合同八问，正文符合章节骨架合同（L1 §4），粒度满足 L1 §3.1（可直接实现 / 明确调用关系 / 完整调用链 / 粒度一致）。
- full 链按 iOS 写作顺序逐章/小批次推进并自动审修闭环——**禁止一轮全量输出全部章节**（必然退化为大纲级薄文档）。
- 只承接概要已决定的 owner、技术决策与 scope；缺口一律回退概要，**禁止在详细阶段补造** provider/SDK/持久化模型/导航拓扑/错误分层。
- 强制锁定 iOS golden-path（见下「iOS 硬规则」），凡违反分层依赖律或 golden-path 的归属，直接判 fail 回退概要，不在详细阶段就地纠偏。

## iOS doc_type 权威七类（全程唯一，禁止改名 / 增减 / 换数）

| doc_type | 含义 | owner 层 | L2 状态 |
| --- | --- | --- | --- |
| `domain-model` | Domain 实体 / 值对象 / `enum` / `enum Error` / 不变量（零依赖、可被任意层导入） | Domain | pending（按 L1 八问展开 + L2豁免） |
| `repository` | Domain `IXxxRepository` 接口 **＋** Infrastructure 实现（合并为一类） | Domain（接口）/ Infrastructure（实现） | full（`detail-type-repository.md`） |
| `usecase` | Domain 业务编排（零 UI 依赖） | Domain | full（`detail-type-usecase.md`） |
| `viewmodel` | UI 层 `ObservableObject` + `@Published` 状态容器 | UI | full（`detail-type-viewmodel.md`） |
| `view` | UI 层 SwiftUI View（只展示 + 输入，无业务） | UI | pending（按 L1 八问展开 + L2豁免） |
| `coordinator` | App 层 `AppCoordinator` 导航 + FactoryKit DI 装配 | App | pending（按 L1 八问展开 + L2豁免） |
| `external` | Infrastructure 外部集成（网络 / SDK / WCDBSwift 持久化 / 第三方） | Infrastructure | pending（按 L1 八问展开 + L2豁免） |

- v1 已提供的 L2（与 flutter `controller/usecase/repository-datasource` 三类一一对应、但用 iOS 类型名）：`detail-type-viewmodel.md`（对应 controller）、`detail-type-usecase.md`、`detail-type-repository.md`（对应 repository-datasource，且 iOS 把接口+实现合并）。
- 其余四类 `domain-model / view / coordinator / external` 为 **pending**：按 L1 §3 合同八问展开，正文头部标 `l2_status: pending`；full 链命中 pending 类型必须在 WX-6 取得 `L2豁免：<doc_type> 理由：…` 声明，否则停止。
- **禁止自创** `transport-handler / service / controller / page / datasource / handler` 之类不在七类内的 doc_type 名；概要索引若出现非七类名，属概要骨架缺口，回退概要修订。

## 分层依赖律（归属硬基准，违反直接 fail）

- **Domain 零依赖**：`domain-model` / `usecase` / `repository` 接口不得 `import` UI / App / Infrastructure / SwiftUI / FactoryKit / WCDBSwift / 任何网络或第三方 SDK；只允许 `Foundation` 与 Domain 自身类型。
- **依赖方向单向**：`Domain → App → Infrastructure → UI`；上游不得反向引用下游。`usecase` 只依赖 Domain（`domain-model` + `IXxxRepository` 接口），不依赖 Infrastructure 具体实现。
- **禁 View 间直接导航**：View 跳转一律经 `coordinator`（`AppCoordinator`）；详细设计若出现 View 直接 `push/present` 另一 View，判 fail。
- **禁 View 直接访问持久化**：View 不得直接读写 WCDBSwift / `repository`；只能调 `viewmodel`，由 `viewmodel` 调 `usecase`，`usecase` 调 `repository` 接口，实现侧落 Infrastructure。
- **repository 跨层归属**：接口（`IXxxRepository`）的 owner 是 Domain，实现（`XxxRepository`）的 owner 是 Infrastructure；同一 `repository` UNIT 必须同时落清接口合同与实现合同，并标注两个 owner 层。

## iOS 硬规则（golden-path 锁定，违反即 fail）

1. **FactoryKit `@Injected` DI**：依赖注入一律走 `@Injected(\.xxx)` + `Container` 扩展（`Container+Domain/UseCases/ViewModels/Coordinators/Infrastructure`）；**禁手动初始化**依赖（禁 `XxxUseCase()` 直接 new 注入对象）；`coordinator` 类负责 DI 装配 owner。
2. **Repository 模式强制**：接口在 Domain（`protocol IXxxRepository`），实现在 Infrastructure（`final class XxxRepository: IXxxRepository`）；`usecase` 只持有接口类型。
3. **`enum Error` 分层定义**：每个 domain 用独立 `enum XxxError: Error`（示例如 `StoryError` / `VoiceConfigurationError` / `ExportTaskManagerError` / `PersistenceError`），需要测试断言时实现 `Equatable`；错误必须分层归属（Domain 错误 owner=Domain，持久化/外部错误 owner=Infrastructure），不得在 UI 层首次发明错误类型。
4. **WCDBSwift 持久化**：本地持久化一律 WCDBSwift（示例 `Infrastructure/Persistence/DatabaseManager.swift` + `Persistence/Repositories/*`）；**禁 CoreData / SwiftData**；持久化模型落 `external` 或 `repository` 实现侧，不污染 `domain-model`。
5. **`ViewModel = ObservableObject + @Published`**：`viewmodel` 必须是 `class … : ObservableObject`，对外状态用 `@Published`，依赖用 `@Injected`，异步用 `Task` + `async/await`，状态写回 `@MainActor`/`MainActor.run`。
6. **private 方法在 `private extension`**：内部辅助方法收敛到 `private extension <Type>`，正文骨架的「内部方法」小节按此组织。
7. **UI 框架收敛**：SwiftUI 主 + RxSwift 遗留，新设计一律 **纯 SwiftUI**（RxSwift 仅作为既存改造说明，不作为新单元目标）。

## 项目约定槽位（project-conventions，取值一律从 `.trellis/spec/conventions/project-conventions.md` 读，不在本文件写死）

UI 框架（SwiftUI 主 + RxSwift 遗留 → 纯 SwiftUI）、网络层（URLSession / Moya）、日志（SwiftyBeaver → OSLog）、JSON 修复策略、测试框架（XCTest → Quick/Nimble）、i18n、主题（`ThemeManager` 单例）、feature 模块结构、mock 生成（手写 → Mockolo）、构建自动化（Fastlane）。
命名/目录/序列化取值按 project-conventions 槽位；行为命名按概要 L1 §4.1；槽位未落盘时按 WX 前置缺口回退，不在详细阶段拍板默认值。

## 与官方 Trellis skill 与 review skill 的边界（务必先读，避免越权）

本 skill 是「详细设计**写**」——承接概要 `design-main.md` 第 7 节详细设计承接索引，按 iOS 自底向上顺序逐章/小批次生成 `chapters/<slug>.md` 的合同八问正文（可编码合同）。它与下列环节职责不重叠、不互相替代：

- **vs `trellis-brainstorm`（需求/构思阶段）**：brainstorm 负责把模糊意图收敛成 `prd.md` 的 `BHV-NNN` 行为规格、P0/P1 核心能力与失败路径。本 skill **消费** prd 已定义的 `BHV-NNN` 与已被概要承接的 owner/技术决策，**不重造需求**、不补造业务规则——需求语义缺口一律记 `requirement_to_overview_gap_findings` 并回退概要，不在详细阶段新增 P0/P1 或失败路径。
- **vs `trellis-check`（代码质检）**：`trellis-check`（对应实现/审核 Gate）查的是**代码层**质量——`xcodebuild` / SwiftLint / `xcodebuild test`（XCTest 或迁移后的 Quick/Nimble）证据、secret 合规、存量违例豁免。本 skill **不做代码质检**：不产 Swift 代码（只到方法签名 / `struct`/`enum`/`protocol` 声明级），不跑构建测试，详细阶段不输出任何编译/测试证据，只写「哪些测试验证它」的测试映射合同（八问之 7）。
- **vs `ios-design-detail-review`（姊妹 skill，写侧 vs 审侧）**：本 skill 是**写侧**——生成 `chapters/<slug>.md` 合同正文并做批内自动审修闭环（自检不替代 Gate）。`ios-design-detail-review` 是**审侧**——做 Phase 1 详细 Gate 的人工判定「能否进入实现编码」，给分级 finding 与三选一结论，**审而不写**。两者共享同一组 SSOT（L1 `detail-structure-single-source.md` + v1 三类 L2 + golden-path + project-conventions），本 skill 只产正文与自检证据，最终放行结论由 review skill 出、由用户终端 confirm 收口。
- **vs `ios-implementation-guru-writing`（下游实现写，不编码）**：那一支在 Phase 2 承接已通过详细 Gate 的合同，生成 Swift 实现代码 + trace 计划合同与 mutable evidence。本 skill **不编码**——产出的是「可编码合同」而非实现体；写实现代码/伪代码超过签名级（方法体、>15 行实现）即越界（见「强制约束 4」），实现由 `ios-implementation-guru-writing` 在详细 Gate 通过后承接。
- 一句话定位：**brainstorm 定「做什么」→ 概要 writing 定「分给哪层、边界在哪、谁承接展开」→ overview review evidence 判「能否进详细」→ 本 skill（详细 writing）写「可编码合同」→ ios-design-detail-review 人工判「能否进编码」→ ios-implementation-guru-writing 写 Swift 实现 → trellis-check 判「代码达标」**。本 skill 只占「详细 writing」一格，越界即停。

## 最小输入与自动补全

- 输入参数（均可省略，省略时按默认推进）：
  - `chapter_target`：只写一个概要第 7 节索引目标；必须属于 `chapter_target → detail_doc_type` 目标集合。
  - `chapter_batch`：指定小批次（≤3 章），必须全部属于目标集合，且批次足够小，能只装载命中的 L2 与上下文。
  - `partial_scope`：仅在已指定 `chapter_target`/`chapter_batch` 后收窄当前 canonical 目标内部条目（如多 View 的子 View 集合、多实体 `domain-model` 的实体子集），写入 `covered_items[]`；**不得扩展成新目标范围**；未覆盖项必须显式回填 `not_covered_items[]`，并记 `canonical_publish_status=not_applicable_by_partial_scope`。
  - 默认（全部省略）：按「iOS 写作顺序」自动逐批推进，每次取下一个未通过或受影响失效的目标。
- 需求证据只从概要已显式引用的锚点读取最小片段，用于理解字段语义、边界、异常语义、权限含义并反向校验概要是否已收口；**不直接拿需求自然语言改变 `chapter_target` / `detail_doc_type` / `owner` / 技术决策**。

## 装载顺序（硬前置，任一失败即终止并提示；只装当前小批次命中项，禁止预加载）

1. **读 L1 detail SSOT**：`.trellis/spec/harness/detail/detail-structure-single-source.md`（合同八问规则正文、章节骨架合同、完成判定与 Gate 口径的唯一权威）；不可用 → 终止并提示先安装 guru spec 模板。
2. **读通用方法 SSOT + 项目取值**：`.trellis/spec/guides/golden-path.md`（分层依赖律 + golden-path 五条硬红线）；`.trellis/spec/conventions/project-conventions.md`（校验上文「项目约定槽位」C1~C6 是否已落盘，取值一律引用槽位 `SLOT-NN`，不在详细阶段另定）。
3. **解析承接索引建立目标集合**：定位概要主定义（full=`design_package/design-main.md` 第 7 节详细设计承接索引；light=`design.md` §1），建立完整非空的 `chapter_target → detail_doc_type（→ 目标文件）` 目标集合；每条索引的 doc_type 必须落在 IOS 七类内（出现非七类名 → 回退概要，禁止详细补造）。
4. **确定当前小批次（按需装载的范围基准）**：按 `chapter_target` / `chapter_batch` 或「iOS 写作顺序」自动取下一批（1~3 章），批次须足够小到只装载本批命中的 L2、概要锚点与必要上下文；后续步骤的 L2/豁免/细则装载全部限定在当前批次命中的 doc_type 上。
5. **当前小批次命中 doc_type 读对应 v1 L2（仅 viewmodel/usecase/repository 三类）**：命中 `viewmodel` 读 `detail-type-viewmodel.md`（八问 3 状态机/三态 + 八问 6 `@Published` 发射强约束）、命中 `usecase` 读 `detail-type-usecase.md`（八问 1 capability owner 承接 + 八问 5 业务失败终态收口）、命中 `repository` 读 `detail-type-repository.md`（八问 2 接口/实现分离 + 八问 5 `[SLOT-error-mapping]` 错误转换点），路径均在 `.trellis/spec/harness/detail/`；命中即装、冲突时 L1 > L2。**不得为后续章节预加载未命中的 L2 类型。**
6. **pending 四类（`domain-model`/`view`/`coordinator`/`external`）按 L1 §3 八问展开并写 `l2_status: pending` 与 L2豁免**：此四类无独立 L2 文件，全程按 L1 §3 合同八问 + §4 骨架 + §3.2 类型专属要点展开（`domain-model` 强约束 2/5/8、行为类项写 `N/A：值类型无运行时行为`；`view` 强约束 2/4/6/8；`coordinator` 强约束 4/6/8 且八问 2 用导航路由表表达；`external` 强约束 2/5/8 且交付面合规依据逐条落点），章节头部标注 `l2_status: pending`。豁免承载按链型分轨：
   - **full 链**：本批命中的每个 pending doc_type 必须在 `design-main.md` 第 7 节对应承接索引项写明 `L2豁免：<doc_type> 理由：…`（说明按 L1 §3 八问展开的风险与补齐计划）；无豁免 → 停止（对齐 WX-6），提示先补对应 L2 或在概要补写豁免声明，不在详细阶段私自放行。
   - **light 链**：直接在 `design.md` 该承接索引项标 `l2_status: pending` 并就地写明豁免理由（等价 full 链的 `L2豁免：<doc_type> 理由：…`），不另起 design-main。
7. **按需读细则与示例**：需要逐类写法细则、章节模板或 mermaid 时序图示例时读 `references/chapter-guide.md` / `references/examples/`；这些只提供编排提示与表达形式，不替代 L1/L2 规则正文（冲突时 L1 > L2 > references > 本文件）。

## WX 前置检查（directory_precheck，full 链；任一硬前置失败 → 停止正文生成，输出缺口 + 概要修订动作）

- **WX-1 输入键完整**：`task.json` 含 `guru_chain` 与（full 链）`design_package`；缺失 → 执行级错误，提示补判轨。
- **WX-2 路径边界**：`design_package` 目录存在且 `chapters/` 已存在；目标文件名均落在 `chapters/` 内（词法检查）。`chapters/` 缺失属概要骨架缺口，**不自动创建目录**。
- **WX-3 承接索引**：design-main 第 7 节索引存在、非空，每条有 `doc_type`（IOS 七类之一）与目标文件名，且可建立完整非空的 `chapter_target → detail_doc_type` 映射；缺失/为空/出现非七类名 → **硬阻断，回退概要**。
- **WX-4 概要 review evidence 已达标**：`guru_gate.py status` 显示 overview 当前 digest 已有两个不同 `run_id` 的 clean review；未达标 → 停止，提示先运行概要 review 并用 `record-review overview` 留痕。
- **WX-5 概要归属与分层合法**：本批目标的 owner 必须与概要归属表一致，且符合「分层依赖律」（Domain 零依赖、方向单向、View 不直连导航/持久化、repository 接口/实现双 owner）；越界或 owner 与概要不符 → 回退概要修订，**不就地改**。
- **WX-6 承接源状态 + L2豁免**：本批引用的 `technology_decision_handoff[]` 条目均为「选定」（含网络层 URLSession/Moya、TTS/STT/图像生成等外部 provider/SDK、WCDBSwift 持久化模型、`@Injected` 注册位等；未选定 → 回退概要，禁止详细拍板）；本批命中 pending L2 的 doc_type（`domain-model/view/coordinator/external`）均有 `L2豁免：<doc_type> 理由：…` 声明（无豁免 → 停止，提示先补 L2 或写豁免）。

light 链执行 WX-3/WX-4/WX-5/WX-6 的等价检查（索引在 `design.md` §1；产物写 §2）。

## 执行流程（chapter_loop）

1. **建立写作顺序（自底向上）**：按 iOS 分层把目标集合排序——① `domain-model`（实体/值对象/enum/`enum Error`/不变量）→ ② `repository`（接口 + 实现）→ ③ `usecase`（业务编排）→ ④ `viewmodel`（状态容器）→ ⑤ `view`（SwiftUI 展示）；`coordinator`（导航+DI 装配）与 `external`（网络/SDK/WCDBSwift/第三方）为横切，随其宿主层就近排入（`coordinator` 紧跟其装配的 viewmodel/view；`external` 紧跟其支撑的 repository 实现）。同一 feature 的 `usecase` 与其直接 `repository` 同批优先；同一 feature 的 `view` 与其 `viewmodel` 同批优先。
2. **确定当前批次**：按输入参数或自动取下一批（1~3 章）；只加载当前批次命中的 L2、概要锚点、已完成章节锚点摘要、概要已指向的最小需求反向校验证据与必要示例。
3. **逐章生成正文**：按 L1 §4 章节骨架合同撰写目标文件；每个 `UNIT-<slug>` 按「合同八问」作答（命中 full L2 时叠加 viewmodel/usecase/repository 类型差异规则；pending 类型按 L1 §3 八问展开）；暂无法回答的问题写入「未决问题」，**禁止留空、禁止 TODO、禁止编造**。
4. **批内自动 review（不等用户）**：对照 L1 §5.3 清单 + 下文「批内自动 review 清单」——骨架符合性、八问完成条件、粒度四条、分层依赖律、golden-path 硬规则、L2 差异规则。
5. **修复闭环**：有 finding → 按 L1 §9 判定修订形态 → 直接修复 → 复查受影响的行为/依赖/跨章引用；当前范围所有命中规则均有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。不以固定次数 clean review 作为通过条件。
6. **层级 checkpoint**：每完成一个层级（domain-model / repository / usecase / viewmodel / view）跑下文对应核对；失效项回到对应批次重走审修闭环。
7. **受影响章节复查**：本批修改触及已完成章节的跨章引用（如 viewmodel 引用的 usecase 签名变了）时，复查该引用闭合。
8. **输出本批成果**（见输出要求）。
9. **下一目标推荐**：给出下一批建议与剩余目标清单；全目录完成时转入完成判定（L1 §5.5）并提示送审。

## 合同八问（每个 `UNIT-<slug>` 必答；这是详细设计「可编码」判定的硬基准）

1. **职责与归属**：本 UNIT 是什么 doc_type、owner 落在哪一层（Domain/App/Infrastructure/UI；`repository` 标双 owner），承接概要哪个 `BHV-NNN` / owner 条目，对应源码目录（如 `Domain/Entities/`、`App/UseCases/<Feature>/`、`UI/Features/<Feature>/ViewModels/`）。
2. **签名级接口**：对外公开的 Swift 签名——`protocol` / `struct` / `enum` / `class` 声明，方法签名（含 `async throws`、参数/返回类型）、`@Published` 属性、`@Injected` 依赖键；上限到签名级，**不写方法体实现**。
3. **逐行为输入输出**：每个行为（方法/intent）用表格列出输入参数（名/类型/约束）、输出（类型/语义）、副作用（持久化/导航/状态变更）；`viewmodel` 行为含触发来源（View intent）与状态写回字段。
4. **调用链与依赖**：本 UNIT 调用谁、被谁调用（向上向下各一跳），列出 `@Injected` 注入的依赖键与其接口类型；必须符合分层依赖律（如 usecase 只列 Domain 依赖）。
5. **不变量与边界**：`domain-model` 的不变量（构造校验、值约束）、空集/边界/越界输入语义、并发与 `@MainActor` 边界、分页/排序稳定性（如 `StorySearchCriteria` 的 sortBy/sortOrder）。
6. **异常与 `enum Error`**：本 UNIT 抛出/转换的 `enum XxxError` 用例表（case、触发条件、面向上游的语义）；分层错误转换点（Infrastructure `PersistenceError` → Domain `XxxError` → UI 呈现）；需测试断言的实现 `Equatable`。
7. **测试映射**：每个行为映射可验证信号——成功路径 + **全部失败路径**（每个 `enum Error` case 至少一条），测试框架按 project-conventions（XCTest → Quick/Nimble），mock 按槽位（手写 → Mockolo）对接口 `IXxxRepository`/usecase 协议；写不出测试点的行为视为粒度不达标，回到流程第 3 步。
8. **不适用场景与产物合同**：明确本 UNIT 不负责什么（如 `view` 不含业务、`usecase` 不含 UI/导航、`domain-model` 不含持久化注解），列出落盘产物文件与其归属目录，跨章未闭合项留稳定引用 + 下一批修复动作。

## 章节正文骨架（L1 §4 合同，每个 chapters/<slug>.md 至少含；编号纪律见下）

- **0. 元信息头**：`doc_type`（IOS 七类之一）、`l2_status: full|pending`、`owner_layer`、承接的 `BHV-NNN`、对应源码目录、`partial_scope`（如有 covered/not_covered）。
- **1. 设计单元清单**：本章包含的 `UNIT-<slug>` 列表与一句话职责。
- **2. 签名级接口**：Swift 声明块（protocol/struct/enum/class，方法签名，`@Published`/`@Injected`），到签名级为止。
- **3. 逐行为输入输出表**：每行为一表（八问之 3）。
- **4. 调用链与依赖闭合**：依赖键表 + 一跳上下游；分层依赖律自检结论。
- **5. mermaid 时序**：关键行为的调用时序（View → ViewModel → UseCase → Repository 接口 → Infrastructure 实现 / external），含异步 `Task`/`await` 与 `@MainActor` 回写边界。
- **6. enum Error 与异常表**：error case 表 + 分层转换点。
- **7. 不变量与边界**：八问之 5。
- **8. 测试映射**：行为 × 成功/失败路径 × 测试点（八问之 7）。
- **9. 不适用场景与产物合同**：八问之 8；落盘文件清单。
- **10. 未决问题与跨章引用**：未决项（不留空）、稳定引用、下一批修复动作。

## 编号纪律

- 行为编号：`BHV-NNN`（来源于 prd 标题，详细阶段裸 token 引用，不改名）。
- 设计单元编号：`UNIT-<slug>`（详细阶段标题；slug 用 kebab-case 语义名，如 `UNIT-home-viewmodel`、`UNIT-story-repository`、`UNIT-story-error`）。
- 下游引用一律裸 token（`BHV-012`、`UNIT-story-repository`），不重复定义编号语义。

## 批内自动 review 清单（在 L1 §5.3 之上叠加 iOS 专属项）

- 类型骨架与第 7 节索引的 `detail_doc_type` 匹配，且为 IOS 七类之一，无自创类型名。
- 八问全部作答，无 TODO/占位/空章节；测试映射覆盖每个 `enum Error` case。
- 分层依赖律全部满足：Domain 零依赖（无 SwiftUI/FactoryKit/WCDBSwift/网络 import）、方向单向、View 不直连导航/持久化、repository 接口/实现双 owner。
- golden-path 硬规则全部满足：`@Injected` DI（无手动 new 注入对象）、Repository 模式（接口 Domain/实现 Infrastructure）、`enum Error` 分层、WCDBSwift（无 CoreData/SwiftData）、`ObservableObject + @Published`、private 方法在 `private extension`。
- 技术决策只承接概要已确认输入（网络层/外部 provider/SDK/持久化模型/`@Injected` 注册位），不在详细阶段首次发明；缺口记 `requirement_to_overview_gap_findings` 并回退概要。
- 跨章引用（viewmodel→usecase→repository 接口→实现）签名一致、无业务语义漂移；结果性产物（`*Result`/异步任务/外部 SDK 返回/持久化产物）必须闭合来源、定位、成功/失败产物与恢复边界，不止写一个泛化调用名。

## 层级 checkpoint

- **domain-model 层**：实体/值对象不变量、`enum`/`enum Error` 定义、零依赖（无任何下游 import）形成可追踪基准；被 repository/usecase 引用的类型签名稳定。
- **repository 层**：每个 `IXxxRepository` 接口都有 Infrastructure 实现合同，接口 owner=Domain / 实现 owner=Infrastructure 双标清；WCDBSwift 持久化与 `PersistenceError` 转换闭合；无 CoreData/SwiftData。
- **usecase 层**：usecase 只依赖 Domain（domain-model + 接口），`@Injected` 键齐全，业务编排无 UI/导航/持久化直连。
- **viewmodel 层**：`ObservableObject + @Published` 状态闭合，`@Injected` 依赖到 usecase，异步 `Task`/`@MainActor` 回写边界清晰；不含业务逻辑下沉缺口。
- **view 层**：SwiftUI View 只展示 + 输入 intent，导航走 `coordinator`，持久化走 viewmodel→usecase→repository；无 View 间直接导航、无直连持久化。
- 横切 `coordinator`：导航拓扑 + FactoryKit DI 装配（`Container+*` 注册）闭合，所有被装配单元的注入键有归属。
- 横切 `external`：网络/SDK/WCDBSwift/第三方集成的契约、credential 策略（只写 `credential_ref`/env name，不写真实 key）、错误转换到 `PersistenceError`/Domain Error 闭合。
- 层级 checkpoint 或最终复审若修改了已通过章节，受影响章节通过状态失效，必须重新进入当前小批次写审修闭环。

## 强制约束

**破坏性编辑保护**：任何删除、压缩、替换既有详细章节的改动，必须先列 deletion ledger（deleted_category / reason / replacement_location / removes_contract_obligation / reviewer_decision）。接口或平台事实可删除，仍有效的 L1 章节骨架、UNIT/BHV 承接、行为列表、输入输出错误合同、状态 owner、失败收口、事件/后置、测试映射、不得补造清单必须保留、移到命名替代位置，或以 `N/A：<理由>` 显式声明；不得把行为合同压扁成 endpoint/interface 映射表。

1. L3 不重定义 L1/L2；规则疑义回 L1，引用时给章节号（`rule_ref=<文件#锚点>`、`rule_id=<规则ID>`）。
2. **禁止一轮全量生成**全部章节；每批 ≤3 章并完成批内审修后才进下一批。
3. 不新增概要归属表之外的结构；不变更 owner/技术决策/scope；缺口回退概要（L1 §6），不在详细阶段补造 provider/SDK/持久化模型/导航拓扑/错误类型/`@Injected` 注册位。
4. 不写超过签名级的代码（Swift 方法签名、`struct`/`enum`/`protocol` 声明、`@Published`/`@Injected` 声明为上限；不写方法体实现）。
5. 命名/目录/序列化取值按 project-conventions 槽位；行为命名按概要 L1 §4.1。
6. `partial_scope` 只收窄不扩展；未覆盖项必须显式回填 `not_covered_items[]`，记 `canonical_publish_status=not_applicable_by_partial_scope`，不得静默丢弃，不得声明 canonical 目标完整通过。
7. 状态写 owner 必须与概要归属一致且符合分层依赖律；发现归属错误/越界 → 回退概要修订，不就地改。
8. 每行为测试映射覆盖成功 + 全部失败路径（每个 `enum Error` case 至少一条，八问之 7）；写不出测试点的行为视为粒度不达标，回到执行流程第 3 步。
9. 涉权限（相册/麦克风/语音/文件访问）、数据采集、三方域名/SDK、PII 的单元必须落合规依据；不写制裁 TLD、私有 API、动态执行类设计；外部 provider/SDK/credential 只承接概要已选定项。
10. 辅助文本中文优先；标识符/命令/路径/框架名（FactoryKit/WCDBSwift/SwiftUI/RxSwift/Moya/OSLog/XCTest/Quick/Nimble/Mockolo/Fastlane）/原文引用用英文。
11. 中断升级仅限四种情形：概要源缺失 / 业务语义必须人工确认 / 技术决策未选定 / 修复无法收敛；其余情况自动闭环推进，不停下来等用户人工 review。
12. doc_type 严格用 IOS_BRIEF 钉死的七类（`viewmodel / usecase / repository / domain-model / view / coordinator / external`），不得改名/增减/换数，不得自创 `transport-handler/service/controller/page/datasource` 之类。
13. 全目录完成后提示送审：加载 `ios-design-detail-review`；Gate 结论「可进入编码」后按 gate_mode 完成 confirm 人工收口。

## Gate 兼容（贯穿三阶段的可追踪字段，详细阶段对齐）

- **需求五要素**（承接概要、详细阶段反向校验，不新增）：行为 `BHV-NNN`、触发、输入/输出、边界、异常语义；详细阶段只用于反向校验概要是否收口，不改要素。
- **概要归属表 + 承接索引**（WX-3/WX-5 前置）：第 7 节 `chapter_target → detail_doc_type → 目标文件 → owner_layer` 必须完整非空且分层合法。
- **详细合同八问**（本文件「合同八问」）：每个 `UNIT-<slug>` 八问全答，是「可编码」判定硬基准。
- **实现 trace 计划合同与 mutable evidence**（供下游实现/review 闭环对齐）：① 签名级接口 → ② 逐行为输入输出 + 调用链 → ③ enum Error 与异常表 → ④ 测试映射（成功 + 全部失败路径）；四节齐全且互相闭合，才记 `chapter_status=passed_by_method_evidence`。

## 输出要求（writing 专属）

每批输出：

- `execution_mode=directory_precheck+chapter_loop`（light 链标注 `light+chapter_loop`）
- `目标集合解析`（总数 / 已完成 / 本批 `chapter_target` 清单与 `doc_type` / owner_layer）
- `WX 前置状态`（首批输出 WX-1~WX-6 逐项；后续批只报变化）
- `partial_scope`（如有：`covered_items[]` / `not_covered_items[]` / `canonical_publish_status`）
- `本批正文`（或落盘文件清单，文件均在 `chapters/` 内）
- `批内自动 review 结果`（finding 数 / 修复迭代次数 / `chapter_status`）
- `需求反向校验证据` 与 `requirement_to_overview_gap_findings`（如有：`overview_revision_action`）
- `层级 checkpoint 状态`（到达层级边界时输出）
- `未决问题与升级项`（如有，按强制约束 11 分类）
- `下一目标推荐`（下一批建议 + 剩余目标清单）

全目录完成时追加：`完成判定`（L1 §5.5 三要素）+ 送审与人工确认指引（强制约束 13）。

前置失败输出：`writing_stage=blocked_requires_overview_fix` + `draft_blockers` 缺口清单 + `recommended_next_step` 概要修订动作，**不产出正文**。

## 参考资料

- 详细阶段中立规范（L1）：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- 类型差异（L2，已落盘三类）：`.trellis/spec/harness/detail/detail-type-viewmodel.md` / `detail-type-usecase.md` / `detail-type-repository.md`
- pending 四类（`domain-model/view/coordinator/external`）：按 L1 §3 合同八问展开，标 `l2_status: pending`，full 链须 L2豁免
- 逐类写法细则与章节模板：`references/chapter-guide.md`
- 章节成稿样例：`references/examples/`
- 通用方法 SSOT：`.trellis/spec/guides/golden-path.md`；项目取值：`.trellis/spec/conventions/project-conventions.md`
