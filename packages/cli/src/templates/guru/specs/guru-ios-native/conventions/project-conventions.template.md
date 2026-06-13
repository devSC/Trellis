# Project Conventions 模板（iOS 原生项目约定槽位）

> **这是什么**：配置包定义的「项目约定槽位」模板，面向 **Guru iOS 原生平台**（DDD 四层 Domain → App → Infrastructure → UI + SwiftUI + FactoryKit DI + WCDBSwift）。配置包的 SSOT 只锁**方法与团队栈级 canonical**，**项目级取值永不进配置包**——每个 App 仓库按本模板填一份取值文件（建议路径：目标仓库 `.trellis/spec/conventions/project-conventions.md`），由各阶段 writing/review Skill 在硬前置中装载（装载路径见各 Skill 的 `.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md`）。
> **填写规则**：复制本模板 → 删除说明文字 → 逐槽位填写。每个取值必须给**代码证据**（仓库内真实路径）；没有证据的取值视为未填。
> **变更规则**：修改任何槽位取值属于项目级架构决策，需要 ADR 记录后方可生效。
> **doc_type 权威**：本平台详细设计 doc_type 全程唯一七类，不得改名/增减/换数：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`。任何槽位、证据、违例登记引用 doc_type 一律用裸 token，禁止自创 `transport-handler` / `service` / `controller` 之类（后者属 flutter/Go 平台，不得照抄）。

---

## 0. 元信息（必填）

| 字段 | 取值 |
|------|------|
| App 名称 / Bundle Identifier | `<app_name>` / `<bundle_id>` |
| 仓库路径 / 主 target 名 | `<repo>` / `<target>` |
| 最低部署版本 / Swift 版本 | `<min_os>` / `<swift_version>` |
| 填写日期 / 填写人 | `<date>` / `<who>` |
| 取值依据 | 实测扫描 / 团队决策（附 ADR 链接） |

> 元信息示例（story-verse-mac 实测，仅供形态参考，**禁止照抄到目标仓库**）：target=`StoryVerse`、DDD 四层根目录 `StoryVerse/{Domain,App,Infrastructure,UI}/`、DI 入口 `StoryVerse/App/DependencyInjection/Container*.swift`。

---

## 1. 槽位清单（全部必填）

> 每个槽位字段固定五段：**决策问题**（要钉死什么）· **本项目取值** · **代码证据**（≥1 条真实路径）· **生效范围**（新代码 only / 全量）· **备注**（含通用硬规则边界、好坏例子、迁移目标）。
> 取值可以是「待定」，但待定项必须写明**决策人与期限**，且待定总数 ≤ 2，否则项目约定视为未就绪（硬前置 C2 不通过）。
> 迁移类取值（如 `SwiftUI 主 + RxSwift 遗留 → 纯 SwiftUI`）必须写「现状 / 目标 / 新代码取哪个」三段，新代码一律取**目标值**，遗留值只用于解释存量。

### SLOT-01 UI 框架基线
- 决策问题：新增 `view` / `viewmodel` 用纯 SwiftUI，还是允许 RxSwift / UIKit 桥接？遗留 RxSwift 谱系的边界在哪？
- 本项目取值：现状＝SwiftUI 主 + RxSwift 遗留；目标＝纯 SwiftUI（`@Published` 单向数据流）；**新代码取目标值，禁止在新 `view`/`viewmodel` 中引入 RxSwift / `Observable` / `DisposeBag`**。RxSwift 仅允许出现在已登记的存量文件中（见 SLOT-16）。
- 代码证据：`StoryVerse/UI/Features/Home/Views/HomeView.swift`（纯 SwiftUI View）、`StoryVerse/UI/Features/Home/ViewModels/HomeViewModel.swift`（`class HomeViewModel: ObservableObject` + `@Published`）。
- 生效范围：新代码 only（遗留 RxSwift 走 SLOT-16 记债，不阻塞触碰式改动）。
- 备注：**`viewmodel` 必须是 `ObservableObject` + `@Published`、`view` 只展示+输入无业务**是通用硬规则（不可槽位豁免，违反直接 fail）。好例：ViewModel 暴露 `@Published var recentStories: [Story]`，View 用 `@StateObject`/`@ObservedObject` 绑定。坏例：在 SwiftUI View 内 `BehaviorRelay` 订阅、或在 ViewModel 内 `import RxSwift`。

### SLOT-02 DDD 四层目录分界与归属
- 决策问题：新增的 `domain-model` / `usecase` / `repository`（接口+实现） / `viewmodel` / `view` / `coordinator` / `external` 各落哪个物理目录？四层（Domain/App/Infrastructure/UI）根路径是什么？
- 本项目取值：按 doc_type → owner 层 → 物理目录一一映射，**不得跨层混放**：
  - `domain-model`（owner=Domain）→ `<target>/Domain/{Entities,ValueObjects,Enums,Errors}/`
  - `repository` 接口（owner=Domain）→ `<target>/Domain/Repositories/`（`IXxxRepository.swift`）；`repository` 实现（owner=Infrastructure）→ `<target>/Infrastructure/Persistence/Repositories/`（`XxxRepository.swift`）
  - `usecase`（owner=Domain）→ `<target>/App/UseCases/` 或 `<target>/Domain/Services/`（业务编排，零 UI 依赖）
  - `viewmodel`（owner=UI）→ `<target>/UI/Features/<Feature>/ViewModels/`
  - `view`（owner=UI）→ `<target>/UI/Features/<Feature>/Views/`
  - `coordinator`（owner=App）→ `<target>/App/Coordinators/` + DI 装配 `<target>/App/DependencyInjection/`
  - `external`（owner=Infrastructure）→ `<target>/Infrastructure/{Adapters,Services,Persistence}/`
- 代码证据：`StoryVerse/Domain/Repositories/IStoryRepository.swift`、`StoryVerse/Infrastructure/Persistence/Repositories/StoryRepository.swift`、`StoryVerse/App/Coordinators/AppCoordinator.swift`、`StoryVerse/UI/Features/Home/{ViewModels,Views}/`、`StoryVerse/Infrastructure/Adapters/OnDeviceLLMAdapter.swift`。
- 生效范围：全量（hooks 按此路径前缀拦截目录违例）。
- 备注：**分层依赖律是归属硬基准（违反直接 fail）**：Domain 零依赖；依赖方向 `Domain → App → Infrastructure → UI` 单向。坏例：`domain-model` 文件 `import SwiftUI` 或 `import WCDBSwift`（Domain 被框架/持久化污染）。

### SLOT-03 接口与命名约定（协议前缀 / 实现后缀）
- 决策问题：协议（接口）用 `IXxx` 前缀还是 `XxxProtocol` 后缀？实现类如何命名？接口与实现是否分文件？
- 本项目取值：协议默认 `IXxx` 前缀（如 `IStoryRepository` / `IFileSystem` / `ILogger`），历史遗留允许 `XxxProtocol`（如 `AudioStorageServiceProtocol`、`Coordinating`）但新代码统一用 `IXxx`；实现类去掉 `I` 前缀（`IStoryRepository` → `StoryRepository`）；**接口与实现必须分文件**。
- 代码证据：`StoryVerse/Domain/Repositories/IStoryRepository.swift` ↔ `StoryVerse/Infrastructure/Persistence/Repositories/StoryRepository.swift`；`StoryVerse/Infrastructure/Adapters/IAudioMergingTool.swift` ↔ `AVFoundationAudioMerger.swift`。
- 生效范围：新代码 only（命名统一）；分文件＝全量硬规则。
- 备注：**接口与实现分文件**是通用硬规则（不可豁免）；本槽位只钉前缀风格。`repository` doc_type 合并「接口在 Domain + 实现在 Infrastructure」一类，详细设计须同时给出两个文件路径。

### SLOT-04 错误类型与收口位置（enum Error 分层）
- 决策问题：每个领域错误是否用独立 `enum XxxError: Error`？底层异常（WCDB / 网络 / SDK）在哪一层转换为领域 `enum Error`？
- 本项目取值：**每领域一个 `enum XxxError: Error`，定义在 `Domain/Errors/`**；Infrastructure 实现（`repository`/`external`）捕获底层异常（WCDB 错误、URLSession 错误、SDK 错误）并转换为对应 `domain-model` 的 `enum Error` 后上抛；`usecase` 只消费领域错误，不感知底层异常类型；`viewmodel` 在 `do/catch` 中将领域错误映射为 UI 文案/Toast。
- 代码证据：`StoryVerse/Domain/Errors/StoryError.swift`（`enum StoryError: Error, Equatable`）、`StoryVerse/Domain/Errors/ExportTaskManagerError.swift`、`StoryVerse/Domain/Errors/VoiceConfigurationError.swift`。
- 生效范围：全量。
- 备注：**Infrastructure 层不得把底层异常静默吞掉**（必须转领域错误后上抛或显式记债）是通用硬规则。好例：`StoryError.chapterNotFound(id:)` 带可读关联值。坏例：`repository` 实现里 `catch { return [] }` 把 DB 失败伪装成空结果。

### SLOT-05 FactoryKit DI 注册规范
- 决策问题：依赖注册写在哪些 `Container+*.swift`？用 `@Injected` 还是 `@LazyInjected`？是否禁止手动 `init` 拼装依赖？单例用 `.singleton` 还是默认 graph 作用域？
- 本项目取值：**强制 FactoryKit `@Injected(\.xxx)`，禁止在 `view`/`viewmodel`/`usecase`/`repository` 内手动 `new` 依赖**；注册按层拆分到 `Container+Domain.swift` / `Container+Infrastructure.swift` / `Container+UseCases.swift` / `Container+ViewModels.swift` / `Container+Coordinators.swift`；跨实例共享的服务/仓库用 `.singleton`；`@MainActor` 的 `viewmodel` 工厂闭包标 `@MainActor`。
- 代码证据：`StoryVerse/App/DependencyInjection/Container+ViewModels.swift`（`var homeViewModel: Factory<HomeViewModel> { self { @MainActor in HomeViewModel() } }`）、`Container+Infrastructure.swift`（`var fileSystem: Factory<IFileSystem> { self { LocalFileSystemAdapter() }.singleton }`）、`HomeViewModel.swift`（`@Injected(\.storyManageUseCase) var storyManageUseCase`）。
- 生效范围：全量。
- 备注：**FactoryKit `@Injected` DI（禁手动初始化）是 golden-path 锁定硬规则**。坏例：`viewmodel` 的 `init` 里 `self.repo = StoryRepository(databaseManager: DatabaseManager.shared)`（绕过 DI + 直连单例）。好例：依赖通过 `@Injected` 声明，工厂在 `Container+*.swift` 装配。

### SLOT-06 持久化方案（WCDBSwift）
- 决策问题：DB 管理类路径、单例/注入方式、建表与迁移（schema migration）的组织、版本号字段？是否绝对禁止 CoreData/SwiftData？
- 本项目取值：**WCDBSwift 唯一持久化方案，禁止 CoreData / SwiftData**；DB 管理走 `DatabaseManaging` 协议 + `DatabaseManager`（默认 `static shared`，DI 通过 `databaseManager: Factory<DatabaseManaging>.singleton` 注入测试可替换路径）；持久化实体（带 `WCDBSwift` 标注）放 `Infrastructure/Persistence/{Entities,Models}/`，与 `domain-model` 解耦（实体 ↔ 领域模型用映射）；迁移按表升级、新增列给默认值兜底。
- 代码证据：`StoryVerse/Infrastructure/Persistence/DatabaseManager.swift`（`class DatabaseManager: DatabaseManaging` + `import WCDBSwift` + `let database: Database`）、`StoryVerse/Infrastructure/Persistence/DatabaseManaging.swift`、`Container+Infrastructure.swift` 的 `databaseManager` 工厂。
- 生效范围：全量。
- 备注：**`view` 禁止直接访问持久化（必须走 `repository`）**、**WCDBSwift 强制**是通用硬规则。坏例：`view`/`viewmodel` 内 `import WCDBSwift` 或调用 `DatabaseManager.shared.database`。好例：UI → `viewmodel` → `usecase` → `IXxxRepository` → WCDB。

### SLOT-07 导航与 Coordinator
- 决策问题：页面跳转走 `AppCoordinator` 还是 View 间直接 `NavigationLink`？目的地如何枚举？导航动作如何注入到 ViewModel？
- 本项目取值：**所有跨页面导航走 `coordinator`（`AppCoordinator`），禁止 View 间直接导航**；目的地集中在 `AppCoordinator.NavigationDestination` 枚举；`AppCoordinator` 是 `ObservableObject`，导航状态用 `@Published var activeDestination`；导航动作通过 FactoryKit 以闭包工厂（`Factory<() -> Void>` / `Factory<(String) -> Void>`）注入给 ViewModel/View，避免 View 直接持有 Coordinator 全量能力。
- 代码证据：`StoryVerse/App/Coordinators/AppCoordinator.swift`（`enum NavigationDestination` + `navigateToStoryDetail(storyId:)`）、`StoryVerse/App/DependencyInjection/Container+Coordinators.swift`（`var navigateToStoryDetail: Factory<(String) -> Void>`）。
- 生效范围：全量。
- 备注：**禁 View 间直接导航（走 coordinator）**是通用硬规则。坏例：故事卡片 View 内 `NavigationLink(destination: StoryDetailView(...))` 硬跳。好例：View 调用注入的 `navigateToStoryDetail(story.id)` 闭包。

### SLOT-08 网络层
- 决策问题：HTTP 客户端用 `URLSession` 还是 `Moya`/`Alamofire`？API 定义放哪？请求/响应模型与 `domain-model` 的边界？
- 本项目取值：**待定**（决策人：`<iOS Tech Lead>`；期限：`<首个联网 external 落地前>`）。现状：仓库无网络实现，仅 `Container+Infrastructure.swift` 内 `// var networkClient: Factory<NetworkClientProtocol> { self { MoyaNetworkClient() } }` 占位注释。倾向：首个联网 `external` 落地时二选一钉死，网络客户端注册为 `Container` 工厂、请求经 `external` 封装后只向上暴露领域模型 / `enum Error`。
- 代码证据：`StoryVerse/App/DependencyInjection/Container+Infrastructure.swift` 第 269–275 行「网络服务」占位注释（现状证据）。
- 生效范围：新代码 only（待定，落地后转全量）。
- 备注：网络属 `external` doc_type，归属 Infrastructure 层。**`external` 不得静默吞异常**（与 SLOT-04 一致）。本槽位计入「待定总数 ≤ 2」。

### SLOT-09 日志（SwiftyBeaver → OSLog）
- 决策问题：日志门面用什么？目标迁移到哪个后端？`view`/`viewmodel`/`usecase`/`repository` 各层是否统一经 `ILogger`？是否禁止裸 `print`？
- 本项目取值：现状＝自研 `Logger` 封装 `SwiftyBeaver`（协议 `ILogger`）；目标＝后端切换为 `OSLog`（门面 `ILogger` 不变，仅替换实现）；**新代码统一经 `ILogger`（DI 注入 `makeLogger(for:)` 或静态 `Logger.d`），禁止裸 `print` 进生产路径**。日志需脱敏（不打印用户内容/密钥）。
- 代码证据：`StoryVerse/Infrastructure/Services/Logger.swift`（`import SwiftyBeaver` + `protocol ILogger`）、`Container+Infrastructure.swift`（`var logger: Factory<any ILogger>` + `func makeLogger(for:)`）。
- 生效范围：新代码 only（门面统一）；后端迁移为全量目标。
- 备注：坏例：`viewmodel` 内 `print("error \(error)")`。好例：`Logger.d("onTapStoryDelete failed: \(error)")` 或注入 `logger.error(...)`。

### SLOT-10 JSON 解析与修复策略
- 决策问题：JSON 解析用 `Codable` 还是手写？AI/LLM 输出等不可信 JSON 是否过修复管线？修复在哪一层、配置如何注入？
- 本项目取值：结构化数据统一 `Codable`；**来自 LLM/外部的不可信 JSON 必须经 `IJSONRepairService` 修复后再解析**，修复服务与配置（`JSONRepairConfig`）经 FactoryKit 注入，归属 `external`（Infrastructure）；修复失败上抛领域错误，禁止把半截 JSON 当成功结果。
- 代码证据：`StoryVerse/App/DependencyInjection/Container+Infrastructure.swift`（`var jsonRepairService: Factory<IJSONRepairService>` + `var jsonRepairConfig: Factory<JSONRepairConfig>`）、`StoryVerseTests/StoryParsingStrategyTests.swift`、`StoryVerseTests/StoryParsingErrorTests.swift`。
- 生效范围：全量（涉及 LLM/外部 JSON 的路径）。
- 备注：解析失败处理与 SLOT-04 错误收口一致（转领域错误上抛）。坏例：`try? JSONDecoder().decode(...)` 静默吞错。

### SLOT-11 主题（ThemeManager 单例）
- 决策问题：主题/颜色/字号如何获取？是否允许在 `view` 硬编码颜色与尺寸字面量？主题入口是单例还是注入？
- 本项目取值：**主题统一经 `ThemeManager.shared`（`ObservableObject` 单例）取色与样式，`view` 禁止硬编码颜色/尺寸魔法数**（颜色走 `currentTheme.colors.*`，间距/字号走主题或布局管理器）；动态布局走 `DynamicLayoutManager`。
- 代码证据：`StoryVerse/Infrastructure/Theme/ThemeManager.swift`（`class ThemeManager: ObservableObject` + `static let shared`）、`StoryVerse/Infrastructure/Layout/DynamicLayoutManager.swift`、`HomeViewModel.swift`（`themeManager.currentTheme.colors.primary`）。
- 生效范围：新代码 only（硬编码颜色清理走 SLOT-16）。
- 备注：**`view` 禁止硬编码尺寸/颜色字面量**是通用硬规则。好例：`.foregroundStyle(ThemeManager.shared.currentTheme.colors.primary)`。坏例：`.padding(16)` / `Color(hex: "#FF0000")` 散落在 View。

### SLOT-12 i18n / 本地化
- 决策问题：本地化用 `.strings` + `NSLocalizedString` 还是 `String Catalog`(.xcstrings) / SwiftGen？源语言文件路径与代码引用入口？是否禁止 UI 裸字符串？
- 本项目取值：现状＝`Localizable.strings`（源语言 `en.lproj/Localizable.strings`）；**`view` 文案禁止裸字符串，统一经本地化 key**；新增 key 追加到源语言 `.strings`，目标语言增量翻译。（如团队切 `.xcstrings`/SwiftGen 需 ADR + 更新本槽位与证据。）
- 代码证据：`StoryVerse/en.lproj/Localizable.strings`。
- 生效范围：新代码 only（裸字符串清理走 SLOT-16）。
- 备注：坏例：`Text("删除故事")` 写死中文。好例：`Text(NSLocalizedString("story.delete", comment: ""))` 或封装的本地化访问器。

### SLOT-13 Feature 模块结构
- 决策问题：UI 层一个 feature 内部如何分目录？`view` 与 `viewmodel` 是否强制分目录？feature 之间是否允许互相 import？
- 本项目取值：**每 feature 一个目录 `UI/Features/<Feature>/`，内部强制 `Views/` 与 `ViewModels/` 分子目录**；feature 私有的 UI 状态可放 `UI/States/`；feature 之间不直接互相导航/import 私有 View（共享逻辑下沉到 `usecase`/`domain-model`，导航走 `coordinator`）。
- 代码证据：`StoryVerse/UI/Features/`（`Home/{Views,ViewModels}`、`Stories`、`Story`、`Voice`、`Setting`、`Root` 等并列 feature）。
- 生效范围：新代码 only。
- 备注：与 SLOT-07 配合——跨 feature 跳转只能经 `coordinator`。坏例：`Home/Views` 直接 `import` 并 push `Story/Views/StoryDetailView`。

### SLOT-14 测试约定（XCTest → Quick/Nimble；mock 生成）
- 决策问题：测试框架用 XCTest 还是 Quick/Nimble？测试目录是否镜像源码分层？mock 用手写还是 Mockolo 生成？DB/网络如何替身？
- 本项目取值：现状＝**XCTest + 手写 mock**；目标＝可选引入 Quick/Nimble（BDD 风格）与 Mockolo（协议 mock 生成），**未落地前一律 XCTest + 手写 mock**；测试目录镜像分层（`StoryVerseTests/{Domain,UseCases,Infrastructure,Integration,TestHelpers}/`）；DB 用可注入路径的 `DatabaseManager(databasePath:)` 或 `MockDatabaseManager` 替身（受益于 SLOT-05 DI）。
- 代码证据：`StoryVerseTests/StoryRepositoryTests.swift`、`StoryVerseTests/UseCases/`、`StoryVerseTests/MockDatabaseManager.swift`、`StoryVerseTests/TestHelpers/`。
- 生效范围：新代码 only（框架/mock 工具二选一前保持现状）。
- 备注：Quick/Nimble、Mockolo 均属待定演进项；引入需 ADR。本槽位若把「框架二选一」记为待定，计入「待定总数 ≤ 2」。

### SLOT-15 构建自动化（Fastlane）
- 决策问题：构建/签名/发布是否用 Fastlane？lane 定义与触发方式？是否禁止 agent 自动执行发布动作？
- 本项目取值：**待定**（决策人：`<iOS Tech Lead / Release Owner>`；期限：`<首次 CI 发布前>`）。现状：仓库无 `fastlane/Fastfile`；倾向首次接入 CI 发布时引入 Fastlane（build/test/beta/release lanes）。**任何发布/签名 lane 一律人工执行，agent 禁止自动触发上架/分发动作。**
- 代码证据：`StoryVerse/StoryVerse.xcworkspace`、`StoryVerse/StoryVerse.xcodeproj`（当前构建入口为 Xcode workspace，无 Fastlane 证据）。
- 生效范围：新代码 only（待定，落地后转全量）。
- 备注：本槽位计入「待定总数 ≤ 2」。若 SLOT-08 与本槽位同时待定即已达上限，第三项待定将使硬前置 C2 不通过。

### SLOT-16 存量违例清单（tech-debt 登记）
- 决策问题：已知的存量架构违例有哪些（供 review 的存量豁免判定使用：触碰存量记债不阻塞、新增违例阻塞）？
- 本项目取值：（逐条登记，格式：`违例描述 + 文件路径 + 涉及 doc_type + 计划`；若无则显式写「无」）
  - 示例条目（story-verse-mac 实测，目标仓库须替换为自身实测结果）：RxSwift 遗留订阅散落于历史 `viewmodel`（待迁纯 SwiftUI，对应 SLOT-01）。
  - 示例条目：日志后端仍为 SwiftyBeaver，未切 OSLog（门面 `ILogger` 已统一，仅后端待迁，对应 SLOT-09）：`StoryVerse/Infrastructure/Services/Logger.swift`。
  - 示例条目：`DatabaseManager.shared` 单例在历史 `external`/`repository` 中被直接引用（新代码须经 DI，对应 SLOT-05/SLOT-06）：`StoryVerse/Infrastructure/Persistence/DatabaseManager.swift`。
- 生效范围：全量
- 备注：本槽位是**存量豁免机制**的数据源，必须维护；清单外的违例一律按「新增」处理（review 阻塞）。触碰已登记存量做最小修复＝记债不阻塞；在已登记文件中**新增同类违例**＝阻塞。

---

## 2. 校验清单（writing/review 硬前置使用）

装载本约定文件的 Skill（writing/review，经 `.trellis/spec/harness/*` 装载、对齐 `.trellis/spec/guides/golden-path.md`）必须先执行以下校验，任一不通过即终止并提示修复：

- [ ] **C1 元信息齐全**：第 0 节五行字段（App/Bundle、仓库/target、部署/Swift 版本、日期/填写人、取值依据）全部非空。
- [ ] **C2 槽位完整 + 待定受控**：SLOT-01 ~ SLOT-16 全部存在；标「待定」的槽位 ≤ 2 且每个均写明决策人与期限（默认待定候选：SLOT-08 网络层、SLOT-15 构建自动化）。
- [ ] **C3 证据可达**：每个**已填**（非待定）槽位至少 1 条代码证据路径，且路径在目标仓库真实存在（不校验文件内容，只校验路径存在性）；待定槽位须给「现状证据」（占位注释/缺失说明亦可）。
- [ ] **C4 不与通用硬规则冲突**：取值不得违反以下不可豁免硬规则——分层依赖律（Domain 零依赖、`Domain → App → Infrastructure → UI` 单向）、接口实现分文件、`view` 禁直接导航（走 `coordinator`）、`view` 禁直接访问持久化（走 `repository`）、FactoryKit `@Injected` DI（禁手动初始化）、WCDBSwift 强制（禁 CoreData/SwiftData）、`enum Error` 分层、`viewmodel` = `ObservableObject` + `@Published`、`view` 禁硬编码尺寸/颜色、Infrastructure 不静默吞异常、private 方法置于 `private extension`、发布/同步类脚本人工执行。
- [ ] **C5 doc_type 合规**：全文件引用 doc_type 只用钉死七类（`viewmodel`/`usecase`/`repository`/`domain-model`/`view`/`coordinator`/`external`）裸 token，无自创类型名、无 flutter/Go 类型名混入。
- [ ] **C6 存量清单存在**：SLOT-16 存量违例清单存在（可为空，但必须显式声明「无」）。

> 校验顺序：C1 → C2 → C3 → C4 → C5 → C6，前序失败即短路返回，不继续后续校验。

---

## 3. 槽位与门禁的对应关系（参考）

| 槽位 | 谁消费 | 关联 doc_type |
|------|--------|---------------|
| SLOT-01 / SLOT-13 | hooks（UI 目录/RxSwift 拦截）、`view`/`viewmodel` 详细 writing 与 review | `view` / `viewmodel` |
| SLOT-02 | hooks（PreToolUse 分层目录拦截）、implementation-review（归属判定） | 全部七类 |
| SLOT-03 | `repository`/`external` 详细 writing 与 review（接口实现分文件、命名） | `repository` / `external` / `domain-model` |
| SLOT-04 / SLOT-10 | `repository`/`usecase`/`external` 合同八问、implementation-review（错误收口） | `repository` / `usecase` / `external` / `domain-model` |
| SLOT-05 / SLOT-07 | `viewmodel`/`coordinator` 合同、implementation-review（DI/导航） | `viewmodel` / `coordinator` / `usecase` |
| SLOT-06 | `repository`/`external` 合同、implementation-review（持久化归属） | `repository` / `external` |
| SLOT-09 / SLOT-11 / SLOT-12 | hooks（裸 print/裸字符串/硬编码颜色检查）、`view`/`viewmodel` writing | `view` / `viewmodel` |
| SLOT-08 / SLOT-15 | implementation-writing（待定阻塞判定）、CI 接入评审 | `external` |
| SLOT-14 | implementation trace 四节（测试章节）、implementation-review | 全部七类 |
| SLOT-16 | 所有 review 的存量豁免判定（触碰记债不阻塞 / 新增违例阻塞） | 全部七类 |

> 编号纪律提醒：上游需求行为编号 `BHV-NNN`、详细设计单元编号 `UNIT-<slug>`、doc_type 引用裸 token；下游（implementation trace 四节、Gate 判定）一律以裸 token 回引，不得改写本文件锁定的七类 doc_type 名。
