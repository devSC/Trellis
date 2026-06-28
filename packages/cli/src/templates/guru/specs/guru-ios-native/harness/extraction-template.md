# 复盘萃取模板（九段结构）— iOS 原生（Swift / DDD 四层）适配

> Phase 3.3（spec 回写）由 `trellis-update-spec` 按本模板执行。
> 原则：**不沉淀本次需求事实，只沉淀"这类 iOS 任务如何被做好"**；一次性内容（某个 ViewModel 的具体 `@Published` 字段、某条 WCDBSwift 建表语句、某次崩溃的具体调用栈值）不进 spec。
> 即使结论是"无可沉淀"，也要走完判定并在任务 journal 记一句原因（写明对照了判定清单哪几条、为何不达标）。
> 语言政策：正文中文优先；英文仅限代码标识符、命令、路径、框架/库名（SwiftUI、RxSwift、FactoryKit、`@Injected`、WCDBSwift、`ObservableObject`、`@Published`、URLSession、Moya、OSLog、Mockolo、Fastlane、XCTest、Quick/Nimble…）、协议字段、缩写、原文引用。

## 适用范围与边界（先读这一段）

本模板服务于 iOS 原生客户端（Swift，DDD 四层 `Domain → App → Infrastructure → UI`，SwiftUI 主 + RxSwift 遗留，FactoryKit `@Injected` 注入，Repository 模式，WCDBSwift 持久化，`AppCoordinator` 导航）的复盘萃取。它回答两个问题：

1. 这次复盘里，有没有"换一个相似 iOS 需求还能复用的方法 / 坑 / 约定"？
2. 如果有，按什么结构写、写到哪个文件、怎么让 Gate 检查得到。

它**不**回答："这次需求的事实是什么"——那留在任务产物（`prd.md` / `design-main.md` / `chapters/*.md` / `implement.md` / `check.md`）里，不进 spec。

**doc_type 七类（全程唯一，禁改名 / 增减 / 换数；禁自创 `transport-handler` / `service` 之类他平台命名）**：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`。owner 层映射：UI(`view` / `viewmodel`) · App(`coordinator`) · Domain(`usecase` / `repository` 接口 / `domain-model`) · Infrastructure(`repository` 实现 / `external`)。L2 现状：`viewmodel` / `usecase` / `repository` 三类已提供 L2 文件（`detail-type-viewmodel.md` / `detail-type-usecase.md` / `detail-type-repository.md`）；`domain-model` / `view` / `coordinator` / `external` 为 `l2_status: pending`——full 链须显式 `L2豁免` 或先补 L2，light 链按 L1 合同八问展开并标 `l2_status: pending`。

---

## 萃取产物结构（九段，缺一不可）

按以下结构产出 / 更新 `.trellis/spec/` 下的方法文件（新方法建新文件；既有方法的增量直接改对应 SSOT / L2 并在文件头记一行修订）。每段都有 iOS 的实质要求，不得留空或写占位符。

### 1. 名称

kebab-case 方法名，体现"一类 iOS 任务"而非组件名。动词或动名词开头优先。

- 好：`viewmodel-published-state-isolation`（ViewModel 用 `@Published` 收口可观察状态、私有方法落 `private extension` 的展开方法）、`repository-interface-domain-impl-infra`（接口归 Domain、实现归 Infrastructure 的 Repository 拆分方法）、`domain-error-enum-per-domain`（每个领域定义独立 `enum Error` 并向上映射的方法）、`coordinator-driven-navigation`（View 间跳转一律经 `AppCoordinator` 的导航装配方法）、`factory-injected-assembly`（`@Injected` 装配、禁手动 `init` 的依赖装配方法）。
- 坏：`home-viewmodel`（这是组件名，不是方法）、`fix-story-list-crash`（这是一次性事实，不是方法）、`swift-best-practice`（粒度太粗，无法判定与展开）。

### 2. 适用场景

描述什么样的**一类** iOS 任务会用到它，给出可识别的触发信号（需求形态 / 代码层位 / 复用频率）。

- 必须能让下一个执行者一眼判断"我这次的任务算不算这一类"。
- 层位锚点要写明：是 `view` / `viewmodel`（UI）、`coordinator`（App）、`usecase` / `repository` 接口 / `domain-model`（Domain）、`repository` 实现 / `external`（Infrastructure）哪一类或哪几类的横切。
- 例：「凡是新增一个特性页且 UI 需展示加载 / 成功 / 失败三态、并把业务编排下沉 UseCase 的任务，都用 `viewmodel-published-state-isolation`；触发信号 = 出现新的 `UI/Features/<Feature>/*ViewModel.swift` + 该状态由用户操作或异步结果驱动。」

### 3. 输入

执行该方法需要什么前置物，逐项列：

- **上游产物**：本任务所处阶段的上游产出（需求包 / `prd.md` 行为规格、概要 `design-main.md` 归属判定表、详细 `chapters/*.md` 合同八问）。
- **约定槽位**：从 `.trellis/spec/conventions/project-conventions.md` 读到的取值——UI 框架（SwiftUI 主 + RxSwift 遗留 → 纯 SwiftUI）、网络层（URLSession / Moya）、日志（SwiftyBeaver → OSLog）、JSON 修复策略、测试框架（XCTest → Quick/Nimble）、i18n、主题（`ThemeManager` 单例）、feature 模块结构、mock 生成（手写 → Mockolo）、构建自动化（Fastlane）。**方法正文里凡涉及这些取值的地方一律写槽位引用，不写死某项目的具体选型。**
- **代码现状**：需要先看的证据文件（如 `StoryVerse/App/DependencyInjection/Container+UseCases.swift`、`App/Coordinators/AppCoordinator.swift`、`Domain/Repositories/IStoryRepository.swift`、`Infrastructure/Persistence/Repositories/StoryRepository.swift`、`Domain/Errors/StoryError.swift`、`UI/Features/Home/ViewModels/HomeViewModel.swift`、`Infrastructure/Persistence/DatabaseManager.swift`、`StoryVerseTests/`、`docs/PROJECT_STRUCTURE.md`、`docs/Swift_代码组织规范.md`、`Podfile`）。
- **横向依赖**：通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律 = 归属 / 调用判定的基准）。

### 4. 正向生成动作

步骤顺序，动词开头，覆盖「识别 → 判定 → 展开 → 自检」四拍。每步要可执行、可验证，落到 iOS 的真实层位。写作顺序自底向上：`domain-model` → `repository` → `usecase` → `viewmodel` → `view` + `coordinator` / `external` 横切。

模板（按实际方法替换具体动作，保留四拍）：

1. **识别**：从上游行为规格 / 归属表定位本方法该作用的 doc_type（`view` / `viewmodel` / `usecase` / `repository` / `domain-model` / `coordinator` / `external`），列出本次涉及的 `BHV-NNN` 与 `UNIT-<slug>`；按自底向上顺序排展开次序。
2. **判定**：按分层依赖律确认依赖方向 `Domain → App → Infrastructure → UI` 单向无环；确认 `Domain` 零依赖（不导入任何上层 / 框架）；确认 View 之间不直接跳转（走 `coordinator`）、View 不直接访问持久化（走 `repository`）；按 `project-conventions.md` 槽位确认选型取值。
3. **展开**：按该方法的产物合同（第 6 段）生成代码骨架 / 合同字段——Repository 接口（`IXxxRepository`）写在 `Domain`、实现写在 `Infrastructure`；UseCase 在 `Domain` 编排且零 UI 依赖；ViewModel 为 `ObservableObject` + `@Published`，私有方法落 `private extension`；依赖一律 `@Injected`（禁手动初始化）；错误用分层 `enum Error`（每域一个）并定义向上映射；持久化用 WCDBSwift（禁 CoreData / SwiftData）。
4. **自检**：跑 `xcodebuild build`（或 Fastlane 槽位脚本）与目标测试（按测试框架槽位 XCTest / Quick·Nimble）；核对未越层、`Domain` 零依赖、无 View 间直接导航、无 View 直访持久化、依赖均经 `@Injected`、`enum Error` 映射闭合、`@Published` 状态收口、mock 按生成槽位（手写 → Mockolo）。

### 5. 边界约束

显式写"不做什么、不替谁决策、不进入哪个阶段的领地"。iOS 高频边界：

- 不在 `view` 写业务规则（View 只做展示 + 输入，状态来自 `viewmodel` 的 `@Published`，业务编排在 `usecase`）。
- 不让 `viewmodel` / `usecase` 直接访问 WCDBSwift 或网络（数据访问归 `repository`，外部集成归 `external`）。
- 不让 `domain-model` / `usecase` / `repository` 接口反向依赖上层或 UI 框架（`Domain` 零依赖硬基准；`import SwiftUI` 出现在 Domain 即 fail）。
- 不让 View 之间直接 `NavigationLink`/`present` 互跳（导航归 `coordinator`，golden-path 硬锁定）。
- 不手动 `init` 拼装依赖替代 `@Injected`（FactoryKit DI 强制，不可豁免）。
- 不引入 CoreData / SwiftData 替代 WCDBSwift；不为求快在 ViewModel 里直接 `URLSession`/Moya 调网络。
- 不在方法里替项目拍板 `project-conventions.md` 的槽位选型（如直接规定"用 Moya"/"用 Quick"）——只写"按网络层槽位"/"按测试框架槽位"。
- 不把一次性事实（具体字段名、具体表结构、具体路由参数、具体崩溃栈）写进方法正文。
- 不自创或借用他平台 doc_type 名（`controller` / `transport-handler` / `service` / `biz` 等一律禁用）。
- 不越阶段：方法是"怎么做对"的元规则，不重新决定需求 scope，也不在此展开某个单元的字段级合同（那属详细设计阶段产物）。

### 6. 输出产物合同

该方法产出的东西必须包含的结构（章节 / 字段 / 表 / 代码骨架形态）。按方法落到的阶段，对齐对应阶段 Gate 的结构合同：

- **若方法影响需求阶段产出** → 产物须含行为五要素：行为（`BHV-NNN` 标题）/ 前置条件 / 状态变化 / 失败路径 / 验收场景。
- **若方法影响概要阶段产出** → 产物须含归属判定表（行为 → owner 层 → 三问理由）+ 详细设计承接索引（`chapter_target → detail_doc_type`），owner 取 UI / App / Domain / Infrastructure，`detail_doc_type` 取七类之一，且每个 owner 被至少一个索引条目覆盖。
- **若方法影响详细阶段产出** → 产物须满足合同八问（承接哪些 `BHV` / 输入·输出·错误 / 读写哪些状态（含 `@Published`）/ 调用与不调用哪些依赖（含 `@Injected` 的协议）/ 失败如何收口（哪个 `enum Error`、向上如何映射）/ 产生哪些事件后置（导航 / 通知 / 持久化副作用）/ 哪些测试验证 / 哪些不得补造），单元以 `UNIT-<slug>` 标题定义；`l2_status` 标注 `full` 或 `pending`。
- **若方法影响实现阶段产出** → 产物须落实现 trace 四节：计划（切片承接 `UNIT`、自底向上执行顺序、风险点）/ 执行（实际改动文件、与计划偏差、代码生成记录）/ 证据（`xcodebuild build` 或 Fastlane 脚本、测试命令与测试名级结果、未验证项）/ 阻塞与偏差（上游缺陷回退、存量违例处置、未决决策升级）。
- **Swift 代码骨架合同**（涉及代码生成的方法必含）：接口 / 实现的 doc_type 归属（接口在 `Domain`、实现在 `Infrastructure`）；依赖是否经 `@Injected`（禁手动 `init`）；错误是否走分层 `enum Error` 并定义向上映射；ViewModel 是否 `ObservableObject` + `@Published`、私有方法是否在 `private extension`；持久化是否 WCDBSwift；`Domain` 是否零依赖。

### 7. 可验证信号

人或脚本如何判断达标，逐条对应 Gate / `guru_gate.py` 可检查点或可执行命令：

- **机器可查（命令）**：`xcodebuild build`（或 Fastlane 槽位脚本）通过；目标测试命令（按测试框架槽位 XCTest / Quick·Nimble）逐测试名通过；`Domain` target 不链接 UI 框架。
- **机器可查（结构 Gate）**：`guru_gate.py trace-matrix <task_dir> --write` 生成的 行为×需求场景（REQ-UC）×归属×单元×测试×切片 矩阵无断链；`BHV-NNN` / `UNIT-<slug>` 引用不存在幽灵编号；承接索引↔章节文件双向闭合（full 链）；`detail_doc_type` 仅取七类名。
- **分层可查**：import 方向 `Domain → App → Infrastructure → UI` 单向无环；`Domain` 文件无 `import SwiftUI`/`import RxSwift`/`import WCDBSwift`/任何上层 import（零依赖）；无 View 间直接导航（跳转引用集中在 `coordinator`）；无 View 直接引用 `DatabaseManager` / WCDBSwift（数据访问经 `repository`）。
- **DI 可查**：依赖通过 `@Injected` 取得，无业务对象手动 `init` 拼装（搜不到绕过 `Container` 的实例化）。
- **错误链可查**：对外失败路径命中分层 `enum Error` 的具体 case，且上层（usecase → viewmodel → view）有显式映射，不靠字符串匹配。
- 每个信号必须可由人复核或脚本判定，不能写"代码质量好"这类不可验证表述。

### 8. 好例子 / 坏例子

各至少一个，来自本次真实复盘（脱敏业务细节，保留结构与层位）。例子要能说明"按方法做"与"没按方法做"的可见差异。

- ✅ **好例子（Repository 接口归 Domain、实现归 Infrastructure）**：`Domain/Repositories/IStoryRepository.swift` 定义协议（仅引用 `domain-model`，零框架依赖）；`Infrastructure/Persistence/Repositories/StoryRepository.swift` 实现协议、内部用 WCDBSwift 读写；`Container+Infrastructure.swift` 把实现注册到协议，调用方 `@Injected(\.storyRepository)` 拿协议。接口语义归 `Domain`、持久化细节封在 `Infrastructure`、装配在 `coordinator`/`Container`，依赖方向单向，符合归属。
- ❌ **坏例子**：在 `HomeViewModel` 里直接 `let db = DatabaseManager.shared` 并写 WCDBSwift 查询。ViewModel 越层直访持久化，业务与存储耦合、无法 mock、违反"View/ViewModel 不直访持久化"，重构即崩。
- ✅ **好例子（分层 enum Error 向上映射）**：`Domain/Errors/StoryError.swift` 定义 `enum StoryError: Error { case notFound, decodeFailed }`；`usecase` 捕获 repository 抛出的 `StoryError` 并按需转译；`viewmodel` 把错误映射成 `@Published` 的用户可读状态供 `view` 展示。错误语义在各层有明确 owner，映射链显式可测。
- ❌ **坏例子**：repository 抛 `NSError(domain:"", code:-1)`、ViewModel 用 `error.localizedDescription` 直接渲染。错误无领域语义、无法按 case 分支、UI 文案与底层耦合，换实现即断。
- ✅ **好例子（@Injected 装配 + ViewModel @Published）**：`HomeViewModel: ObservableObject`，`@Published var state`，依赖 `@Injected(\.exportStoryUseCase) var exportStoryUseCase`，私有辅助方法集中在 `private extension HomeViewModel`；`Container+ViewModels.swift` 注册该 ViewModel。装配走 FactoryKit、状态收口 `@Published`、私有方法分区清晰。
- ❌ **坏例子**：`HomeViewModel` 在 `init` 里 `self.useCase = ExportStoryUseCase(repo: StoryRepository(db: DatabaseManager.shared))` 手动拼装整条依赖链。绕过 DI、测试时无法替换、违反 `@Injected` 硬规则。

### 9. 不适用场景

显式列出别用它的情况，避免方法被误套：

- 一次性事实（这个 ViewModel 的具体字段、这条 WCDBSwift 建表语句、这次崩溃的具体栈）→ 留任务产物，不进 spec。
- 仅本项目的选型取值（"本项目网络层用 Moya 不用裸 URLSession"、"测试用 Quick/Nimble 不用 XCTest"）→ 进 `conventions/project-conventions.md` 槽位，不进通用方法。
- 与既有 SSOT / golden-path 冲突且属"换口径"性质 → 不直接新写一份，走第二节判定清单的修订形态判定。
- 粒度过粗无法判定 / 展开（"写好 SwiftUI 代码"）→ 不沉淀，拆细或不写。
- 仅风格偏好且无生成顺序与判定方法（命名口吻、缩进、注释语气）→ 进对应 L2 备注或 lint / 规范槽位，不单列方法。
- RxSwift 遗留代码的临时绕过技巧（目标是迁移到纯 SwiftUI）→ 不沉淀为方法，记入迁移债清单。

---

## 判定清单（萃取前自问）

逐项打勾才进入九段撰写；任一为"否"按括号内分流处置，并在 journal 记一句。

- [ ] 它适用于一类重复的 iOS 任务，而不是本次需求？（否 → 不沉淀，事实留任务产物）
- [ ] 它规定了生成顺序与判定方法（识别→判定→展开→自检可落地到七类 doc_type 与四层）？（否 → 可能只是模板 / 风格，写进对应 L2 备注或规范槽位即可）
- [ ] 换一个相似 iOS 需求（另一个 feature、另一个 ViewModel / Repository）还能复用？（否 → 不沉淀）
- [ ] 与既有 SSOT / golden-path 冲突？（是 → 走修订形态判定：局部修订 vs 文档级重构，禁止并行两套口径）
- [ ] 属于项目级取值差异（UI 框架 / 网络层 / 日志 / JSON 修复 / 测试框架 / i18n / 主题 / feature 结构 / mock 生成 / 构建自动化槽位）？（是 → 进 `conventions/project-conventions.md` 槽位，不进通用方法，并按需补 ADR）
- [ ] 它是否触碰分层依赖律 / `Domain` 零依赖 / `@Injected` DI / Repository 模式 / 分层 `enum Error` / WCDBSwift / `ObservableObject`+`@Published` 硬规则？（是 → 校验是否仍单向无环、Domain 零依赖、未绕 DI、未直访持久化、未换持久化引擎；硬规则不可被方法豁免）

---

## 回写位置路由（iOS 适配）

装载后（安装路径）的回写目标。开发期模板路径 `guru-template/` 不在此出现。

| 萃取物类型 | 写到 |
|-----------|------|
| 新的一类 iOS 任务方法 | `.trellis/spec/harness/<阶段域>/` 新文件（阶段域取 `overview` / `detail` / `implementation` 之一）+ 在 `.trellis/spec/harness/index.md` 登记 |
| 既有方法的修正 / 新增反例（落到某 doc_type） | 对应 SSOT / L2 文件就地修订（`.trellis/spec/harness/detail/detail-type-viewmodel.md` / `detail-type-usecase.md` / `detail-type-repository.md`，或 pending 四类补 L2 时新建对应文件），文件头记一行修订日期与原因 |
| 通用方法本身的规则增删（分层律、`Domain` 零依赖、`@Injected` DI、Repository 模式、分层 `enum Error`、WCDBSwift、导航经 coordinator） | `.trellis/spec/guides/golden-path.md` 就地修订（改约定先改这里，并按需补 ADR） |
| 生产坑（一次根因，多次可踩，如 ViewModel retain cycle、`@Published` 主线程更新缺失、WCDBSwift 迁移漏写、Domain 误 import 框架） | `.trellis/spec/guides/`（或迁入 big-question 域后归位） |
| 项目取值变化（槽位选型从 A 换 B，如 SwiftyBeaver → OSLog、手写 mock → Mockolo） | `.trellis/spec/conventions/project-conventions.md` 槽位（需 ADR 记录） |
| 存量违例修复（如残留 RxSwift、残留手动 init、残留 CoreData） | 从存量豁免清单（SLOT-16 / 项目存量清单）移除并注明日期 |

### 回写后必做

1. 在 `.trellis/spec/harness/index.md` 的「阶段 → SSOT 映射」表确认新文件被引用（新方法文件未登记即为孤儿，Gate 不识别）。
2. 若改动触碰分层律 / `Domain` 零依赖 / DI 强制 / Repository 模式 / 分层 `enum Error` / 持久化引擎 / 导航归 coordinator → 在仓库 `docs/adr/` 追加或更新 ADR，并在被改文件头回指 ADR 编号；规范类同步 `docs/Swift_代码组织规范.md`。
3. 编号纪律：行为引用写裸 `BHV-NNN` token，设计单元引用写裸 `UNIT-<slug>` token；新方法文件内若引用具体行为 / 单元，一律用编号 token，便于 `guru_gate.py trace-matrix` 追溯；doc_type 一律用七类钉死名，不得换名。
