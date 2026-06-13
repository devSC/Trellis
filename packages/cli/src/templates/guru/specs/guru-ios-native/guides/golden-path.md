# 黄金路径：iOS 原生客户端开发（通用方法 SSOT · v1）

> **类别级 + 团队栈级 canonical**：本文只包含**类别级方法**（任何 iOS 原生 DDD 客户端怎么做对）与**团队栈级 canonical**（story-verse-mac 实测固化的 Swift 统一约定）。**项目级取值一律不出现在本文**——凡标注 `[SLOT-xx]` 处，取值见目标仓库的 `.trellis/spec/conventions/project-conventions.md`（入口 `../conventions/index.md`）。
> 脚手架模板、SwiftLint/SwiftFormat 规则、各 agent 适配层**全部从本文派生**，不各写一份；改约定先改这里。
> 平台基线（DDD 四层 Domain → App → Infrastructure → UI，Domain 零依赖；SwiftUI 主 + RxSwift 遗留；FactoryKit DI；Repository 模式；WCDBSwift 持久化）。证据基准见 story-verse-mac：`docs/PROJECT_STRUCTURE.md`、`docs/Swift_代码组织规范.md`、`StoryVerse/App/{DependencyInjection,Coordinators}/`、`StoryVerse/Infrastructure/Persistence/`、`StoryVerse/Domain/Errors/`、`StoryVerse/UI/Features/Home/`、`StoryVerseTests/`。

核心思想：**一个需求 = 它真正碰到的那几个 doc_type 的 canonical 迷你路径之组合。** 整页 feature 只是"view + viewmodel + 下层"的全栈组合；非 UI 需求就是"只跑下层"（usecase / repository / domain-model / external）。

**doc_type 七类（权威分层口径，全程唯一，禁止改名/增减/换数；下游引用一律裸 token）**：
`viewmodel`（UI 层 ObservableObject+@Published 状态容器）· `usecase`（Domain 业务编排，零 UI 依赖）· `repository`（Domain `IXxxRepository` 接口 + Infrastructure 实现，合并一类）· `domain-model`（Domain 实体/值对象/`enum Error`/不变量，零依赖）· `view`（UI 层 SwiftUI View，只展示+输入）· `coordinator`（App 层 `AppCoordinator` 导航 + FactoryKit DI 装配）· `external`（Infrastructure 外部集成：网络/SDK/WCDBSwift 持久化/第三方）。
禁止自创 `service` / `transport-handler` / `datasource` 之类 token：领域服务归 `usecase` 或并入 `repository`/`external` 的实现侧，按归属层落位，绝不新增第八类。

---

## 1. 入口决策树：这个需求碰哪几个 doc_type？

```
需求进来
 ├─ 要给用户看的新界面/新交互?      → 跑 §7 view + §6 viewmodel + 它需要的下层
 ├─ 只改 UI 状态/事件编排(无新业务)?  → 只跑 §6 viewmodel
 ├─ 只改业务规则/跨仓储编排?         → 只跑 §5 usecase（零 UI 依赖）
 ├─ 只改数据访问合约/持久化读写?      → 只跑 §4 repository（接口在 Domain，实现在 Infrastructure）
 ├─ 只动核心实体/值对象/错误枚举?     → 只跑 §3 domain-model（零依赖、最先写）
 ├─ 只接网络/SDK/三方/新建表?         → 只跑 §8 external，再交给 §4 repository 消费
 └─ 只加/改导航跳转或 DI 装配?        → 只跑 §9 coordinator
跑完任意 doc_type 都要过 §10 自检（SwiftLint + build/test）。
```

写作顺序（自底向上，硬约定）：`domain-model → repository → usecase → viewmodel → view`，`coordinator` / `external` 作为横切随用随写。理由：上层只能依赖已存在的下层接口，先有合同才能注入。

---

## 2. canonical 总则（跨 doc_type，所有迷你路径都遵守）

### 2.1 分层依赖律（最重要，归属硬基准，违反直接 fail）
依赖方向**只能 Domain → App → Infrastructure → UI 单向**，严禁反向或同层横跳：

```
UI(view + viewmodel)
        ↓ 只依赖
App(coordinator + usecase 编排入口)
        ↓ 只依赖
Domain(usecase 业务编排 / repository 接口 / domain-model)   ← Domain 零依赖，可被任意层 import
        ↑ 实现侧
Infrastructure(repository 实现 / external：WCDBSwift / 网络 / SDK)
```

口径说明：`usecase` 落 `App/UseCases/`（编排），其依赖的 `repository` 接口与 `domain-model` 在 `Domain/`；`Domain` 自身不 import App/Infrastructure/UI 任何符号（实测 `Domain/Repositories/IStoryRepository.swift` 只 `import Foundation`）。

**硬禁止（review + lint 查 import 方向）**：
- ❌ `Domain` 层 import `App` / `Infrastructure` / `UI`（破坏 Domain 零依赖）。
- ❌ `view` 间直接导航（`NavigationLink` 硬跳到另一个 feature 的 View）——必须走 `coordinator`（`AppCoordinator` 改 `@Published activeDestination`）。
- ❌ `view` 直接访问持久化（`Database` / `WCDBSwift` / repository 实现类）——必须走 `repository` 接口，且经 `viewmodel`/`usecase`。
- ❌ `viewmodel` 直接 import repository 实现类或 `WCDBSwift`（只能注入 `IXxxRepository` 或 `usecase` 协议）。
- ❌ `repository` 实现绕过 `external`/`DatabaseManager` 直接散写 SQL 字面量到业务方法里。

### 2.2 接口与实现分离（通用硬规则，不可豁免）
`usecase` / `repository` / 领域服务 / `external` 适配器一律**协议（接口）与实现分两个文件**：
- 接口：`Domain/` 下 `IXxx`（实测 `IStoryRepository`、`IStoryManagementUseCase`、`IVoiceProfileRepository`），`I` 前缀强制。
- 实现：`usecase` 实现落 `App/UseCases/<Feature>/XxxUseCase.swift`；`repository` 实现落 `Infrastructure/Persistence/Repositories/XxxRepository.swift`（实测 `StoryRepository`、`VoiceProfileRepository`）；`external` 适配器落 `Infrastructure/Adapters` 或 `Infrastructure/Services`。
- 命名后缀按 §2.4。`view` / `viewmodel` 不强制接口分离（SwiftUI View 是 struct，ViewModel 直接是 class）。

### 2.3 DI 唯一策略：FactoryKit `@Injected`（团队栈级 canonical）
- **唯一容器**：`extension Container`，每个依赖一个 `Factory<T>` 计算属性；实现按职责拆进 `Container+UseCases.swift` / `Container+Infrastructure.swift` / `Container+ViewModels.swift` / `Container+Coordinators.swift` / `Container+Domain.swift`（实测目录 `App/DependencyInjection/`）。
- **注册形态**（实测 `Container+UseCases.swift`）：
  ```swift
  var storyManageUseCase: Factory<IStoryManagementUseCase> {
      self {
          StoryManagementUseCase(
              storyRepository: self.storyRepository(),          // ✅ 用 Factory 取子依赖
              systemStoriesInitializer: self.systemStoriesInitializer()
          )
      }
      .singleton                                                 // 有状态/重对象用 .singleton
  }
  ```
  接口型协议注册用 `Factory<any IXxxRepository>`（存在 associatedtype 时用 `any`，实测 `var storyRepository: Factory<any IStoryRepository>`）。
- **消费形态**：`viewmodel`/`usecase` 用 `@Injected(\.xxx)`；`view` 注入 ViewModel 用 `@InjectedObject(\.homeViewModel)`，注入 ObservableObject 协调器用 `@InjectedObject(\.appCoordinator)`，注入导航闭包/普通服务用 `@Injected(\.navigateToSetting)`（实测 `HomeView.swift` / `HomeViewModel.swift`）。
- **禁止**：业务类里手动 `new`（`XxxUseCase(...)` 直接构造）；`view` 的 `body` 里 `init` ViewModel；用全局单例（`Xxx.shared`）顶替可注入依赖。例外：`ThemeManager.shared` / `ToastManager.shared` / `Logger` 这类纯横切工具单例（项目既有约定，不视为可注入业务依赖）。
- **`@MainActor` Factory**：UI 相关 ViewModel 的 Factory 须 `@MainActor`（实测 `var homeViewModel: Factory<HomeViewModel>` 标 `@MainActor`）。

### 2.4 命名 / 目录约定（实测 `PROJECT_STRUCTURE.md` §命名约定）
- 实体：`EntityName`（`Story`、`Chapter`）；值对象：`ValueObjectName`；错误：`<Domain>Error`（`StoryError`、`VoiceConfigurationError`、`ExportTaskManagerError`）。
- 仓储接口 `IEntityNameRepository`，实现 `EntityNameRepository`；用例接口 `IXxxUseCase`，实现 `XxxUseCase`（个别遗留实现带 `Impl` 后缀如 `ManageExportTasksUseCaseImpl`，新代码统一无 `Impl`，按 `[SLOT-feature-structure]`）。
- 视图 `XxxView`，视图模型 `XxxViewModel`；feature 目录结构 `UI/Features/<Feature>/{Views,ViewModels}/`（实测 `UI/Features/Home/Views/HomeView.swift` + `ViewModels/HomeViewModel.swift`），具体 feature 模块切分按 `[SLOT-feature-structure]`。
- 协调器 `AppCoordinator`（单一全局协调器，导航目的地用其内嵌 `enum NavigationDestination`）。

### 2.5 错误：每域一个 `enum Error`（团队栈级 canonical）
- 每个领域/用例定义独立 `enum XxxError: Error`（实测 `Domain/Errors/StoryError.swift`、`StoryManagement/StoryManagementError.swift`、持久化侧 `PersistenceError`）。
- 需要在测试里比较的错误实现 `Equatable`（实测 `StoryError`/`PersistenceError` 手写 `static func ==`）。
- 分层定界：`domain-model`/`usecase` 抛领域错误（`StoryError`/`StoryManagementError`）；`repository` 实现/`external` 抛 `PersistenceError` 或域内错误，**不得把 `WCDBSwift` 原始错误裸抛到 UI**——在 repository 边界转换为 `PersistenceError.underlyingError` 或具体 case。

### 2.6 访问级别组织（实测 `Swift_代码组织规范.md`，硬规则）
- 所有 `private` 方法/属性必须放进 `private extension`，不得与 `public`/`internal` 成员混合声明。
- 每个 `private extension` 带 `MARK` 注释并按功能分组（`// MARK: - Private Methods - Validation` / `- Data Processing` / `- Retry Logic` 等）。
- 主体类内只放：`// MARK: - Dependencies` / `- Initialization` / `- Public Methods` / `- Protocol Conformance`。例外：极简类（1~2 个 private 方法）、协议扩展、测试类、自动生成代码可放宽。

### 2.7 持久化：WCDBSwift（团队栈级 canonical，禁 CoreData/SwiftData）
- 唯一持久化栈 `WCDBSwift`，经 `DatabaseManager`/`EnhancedDatabaseManager` 取 `Database` 实例（实测 `Infrastructure/Persistence/DatabaseManager.swift`）。
- `repository` 实现注入 `DatabaseManager`（DI 提供 `enhancedDatabaseManager` Factory），不在 ViewModel/View 里直接持有 `Database`。
- 表/列定义集中在 `Persistence/Entities` 或 `Models` 的 WCDB 表对象里，迁移逻辑集中，不散落到业务方法。

---

## 3. domain-model 迷你路径（Domain 实体/值对象/enum Error/不变量）

**正向生成动作**：在 `Domain/Entities` / `Domain/ValueObjects` / `Domain/Errors` 新增类型，只 `import Foundation`，零外部依赖；不变量在初始化或工厂方法里校验失败抛域错误。

```swift
// Domain/Errors/StoryError.swift —— 每域一个 enum Error，可比较的实现 Equatable
enum StoryError: Error, Equatable {
    case validationFailed(reason: String)
    case chapterNotFound(id: String)
    // ...
}

// Domain/Entities/Story.swift —— 实体只承载状态 + 不变量，不 import App/Infra/UI
struct Story: Identifiable, Equatable {
    let id: String
    var title: String
    var updatedAt: Date
    // 不变量：title 非空由工厂/用例校验，违反抛 StoryError.validationFailed
}
```

- **边界**：domain-model 不持有 repository/usecase 引用，不做 IO，不引 SwiftUI/WCDBSwift。
- **产物合同**：类型签名 + 字段语义 + 不变量清单 + 关联 `enum Error` 的每个 case 触发条件。
- **可验证信号**：`Domain/` 下文件 `grep import` 只出现 `Foundation`（及少量纯值类型库）；无 `import SwiftUI` / `import WCDBSwift` / `import FactoryKit`。
- **好例子**：`StorySummary` 值对象（`Identifiable, Codable, Equatable`，纯数据）。**坏例子**：在实体里塞 `func save()` 直接写库（应在 repository）。
- **不适用**：纯 UI 展示态（属于 viewmodel 的 `@Published`）、跨表查询条件以外的编排（属 usecase）。
- **Gate 判定**：违反 Domain 零依赖 → 概要 Gate 归属 fail。

## 4. repository 迷你路径（Domain 接口 + Infrastructure 实现，合并一类）

**正向生成动作**：①在 `Domain/Repositories/IXxxRepository.swift` 定义协议（`async throws`，抛 `PersistenceError`）；②在 `Infrastructure/Persistence/Repositories/XxxRepository.swift` 实现，注入 `DatabaseManager`；③在 `Container+UseCases.swift`/`Container+Infrastructure.swift` 注册 Factory。

```swift
// 接口（Domain 侧，只 import Foundation）
protocol IStoryRepository: IObservableRepository {
    func save(story: Story) async throws            // 抛 PersistenceError
    func findById(id: String) async throws -> Story?
    func findAll() async throws -> [Story]
    func delete(id: String) async throws
}

// 实现（Infrastructure 侧）
final class StoryRepository: IStoryRepository {
    private let databaseManager: EnhancedDatabaseManager   // ✅ 经 WCDBSwift，不在 VM/View 出现
    init(databaseManager: EnhancedDatabaseManager) { self.databaseManager = databaseManager }
    // WCDBSwift 原始错误在此边界转换为 PersistenceError，绝不裸抛到上层
}
```

- **边界**：接口零依赖于实现；实现是唯一碰 `Database` 的地方；不写业务编排（编排归 usecase）。
- **产物合同**：协议方法签名 + 抛错类型 + 一致性语义（如 `save` 的 upsert 语义、`findAll` 是否含子聚合）。
- **可验证信号**：`viewmodel`/`view` 文件里 `grep` 不到 repository 实现类名与 `WCDBSwift`；只见 `IXxxRepository`。
- **好例子**：`StoryRepository` 实现 + DI `Factory<any IStoryRepository>`。**坏例子**：ViewModel 里 `StoryRepository(databaseManager: ...)` 手动 new（违 §2.3）。
- **不适用**：纯内存态、跨域转换（用 usecase）；只读常量配置（用 `external`/Resource）。
- **Gate 判定**：接口与实现混一文件 / 实现落错目录 / view 直连 → 详细或实现 Gate fail。

## 5. usecase 迷你路径（Domain 业务编排，零 UI 依赖）

**正向生成动作**：①`App/UseCases/<Feature>/IXxxUseCase.swift` 定协议；②同目录 `XxxUseCase.swift` 实现，构造注入 `repository`/其他 `usecase`/`external` 适配器；③`App/UseCases/<Feature>/XxxError.swift` 定域错误；④`Container+UseCases.swift` 注册 `.singleton` Factory。

```swift
protocol IStoryManagementUseCase {
    func fetchAllFullStories() async throws -> [Story]    // 抛 StoryManagementError
    func deleteStory(storyId: String) async throws
}

final class StoryManagementUseCase: IStoryManagementUseCase {
    // MARK: - Dependencies
    private let storyRepository: any IStoryRepository       // ✅ 注入接口，不依赖实现
    private let systemStoriesInitializer: ISystemStoriesInitializer
    // MARK: - Initialization
    init(storyRepository: any IStoryRepository, systemStoriesInitializer: ISystemStoriesInitializer) { ... }
    // MARK: - Public Methods
    func fetchAllFullStories() async throws -> [Story] { try await retryFetch() }
}
// MARK: - Private Methods - Retry Logic
private extension StoryManagementUseCase { func retryFetch() async throws -> [Story] { ... } }   // §2.6
```

- **usecase → usecase 单向依赖：允许**（活例 `AppInitializationService` 协调 `voiceProfileUseCase` + `storyManageUseCase`）。约束：必须单向、构造注入接口、禁环形/双向；协调超 2 个 usecase 或出现互调倾向时抽更高层编排 usecase 或把共享逻辑下沉到 repository。
- **边界**：零 UI 依赖（不 import SwiftUI / 不持 `@Published`）；不直接碰 `Database`（走 repository）；私有方法进 `private extension`（§2.6）。
- **产物合同**：协议方法签名 + 抛 `XxxError` 的每个 case + 编排步骤（调哪些 repository/usecase，顺序与失败回滚）。
- **可验证信号**：usecase 文件 `grep` 无 `import SwiftUI`、无 `@Published`、无 repository 实现类名。
- **好例子**：`LLMUseCase` 注入 `aiModelRepository`+`onDeviceLLMAdapter`+`storyRepository`+`jsonRepairService`，retry/解析分组进 `private extension`。**坏例子**：usecase 里 `import SwiftUI` 或返回 `View`。
- **不适用**：纯数据读写（repository）、纯 UI 状态（viewmodel）。
- **Gate 判定**：usecase 环形依赖 / 触碰 UI 层 → 概要+详细 Gate fail。

## 6. viewmodel 迷你路径（UI 层 ObservableObject + @Published）

**正向生成动作**：①`UI/Features/<Feature>/ViewModels/XxxViewModel.swift` 建 `class XxxViewModel: ObservableObject`；②`@Published` 暴露 UI 状态；③`@Injected(\.xxxUseCase)` 注入用例/仓储接口；④异步操作放 `Task` + `await MainActor.run` 回主线程改 `@Published`；⑤UI 相关 Factory 在 `Container+ViewModels.swift` 标 `@MainActor` 注册。

```swift
final class HomeViewModel: ObservableObject {
    @Published var recentStories: [Story] = []                 // ✅ UI 状态
    @Injected(\.storyManageUseCase) var storyManageUseCase     // ✅ 注入 usecase 协议
    @Injected(\.exportStoryUseCase) var exportStoryUseCase
    func loadStorys() {
        Task {
            do {
                let storys = try await storyManageUseCase.fetchAllFullStories()
                await MainActor.run { recentStories = storys.sorted { $0.updatedAt > $1.updatedAt } }
            } catch { Logger.d("loadStorys failed: \(error)") }   // 不把 throws 漏到 View
        }
    }
}
```

- **边界**：不直接碰 `Database`/repository 实现/网络 SDK（只经注入的 usecase 或 `IXxxRepository`）；不返回 `View`；导航不在此硬跳，调注入的导航闭包/coordinator。
- **产物合同**：`@Published` 字段清单（每个的初值与含义）+ 公开方法（事件入口如 `onViewAppear`/`onTapXxx`）+ 注入依赖清单 + 错误如何降级为 UI 态。
- **可验证信号**：是 `ObservableObject` 且有 `@Published`；依赖全是 `@Injected`，无手动 new；`grep` 无 repository 实现类名/`WCDBSwift`。
- **好例子**：`HomeViewModel` 全 `@Injected`，异步回主线程改 `@Published`。**坏例子**：`@Published` 直接存 `Database` 查询结果对象 / ViewModel 里 `StoryRepository(...)`。
- **不适用**：纯展示无状态片段（用 `view` 的子 View / `Shared/Components`）、跨页业务编排（usecase）。
- **Gate 判定**：ViewModel 直连持久化或 import 实现类 → 详细/实现 Gate fail。

## 7. view 迷你路径（UI 层 SwiftUI View，只展示+输入）

**正向生成动作**：①`UI/Features/<Feature>/Views/XxxView.swift` 建 `struct XxxView: View`；②`@InjectedObject(\.xxxViewModel)` 注入 ViewModel；③导航/主题/Toast 等通过注入的闭包或 `@EnvironmentObject` 获取；④`body` 只组装 UI 与转发用户输入到 ViewModel 方法。

```swift
struct HomeView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    @InjectedObject(\.homeViewModel) private var viewModel          // ✅ 注入 VM
    @InjectedObject(\.appCoordinator) private var coordinator        // ✅ 经 coordinator 导航
    @Injected(\.navigateToSetting) private var navigateToSetting     // ✅ 注入导航闭包
    var body: some View {
        NavigationStack {
            ScrollView { /* createStorySection / recentStoriesSection ... */ }
                .navigationTitle(R.string.localizable.homeWelcome())  // i18n 经本地化，不硬编码文案
                .toolbar { ToolbarItem { NavigationSettingButton { navigateToSetting() } } }
        }
        .onAppear { viewModel.onViewAppera() }                        // 输入转发给 VM
    }
}
```

- **边界**：无业务逻辑（不调 repository/usecase 之外的 IO）；不直接 `import WCDBSwift`；不在 View 间硬 `NavigationLink` 跳到别 feature（走 coordinator）；文案走本地化（`Localizable.strings` / `R.string.localizable`），不硬编码用户可见字符串。
- **产物合同**：View 输入（构造参数/环境对象）+ 绑定的 ViewModel + 用户输入事件 → 转发的 VM 方法映射 + 导航触发点（调哪个 coordinator 动作）。
- **可验证信号**：是 `struct: View`；依赖经 `@InjectedObject`/`@Injected`/`@EnvironmentObject`；`grep` 无 repository/usecase 实现类、无 `WCDBSwift`。
- **好例子**：`HomeView` 经 `@InjectedObject` 取 VM + coordinator，导航走注入闭包。**坏例子**：View 里 `Task { try await storyRepository.findAll() }`（业务漏进 View）。
- **不适用**：可复用无 feature 归属的控件（落 `Shared/Components`）。
- **Gate 判定**：view 间直接导航 / view 直连持久化 → 概要+实现 Gate fail（§2.1 硬禁止）。

## 8. external 迷你路径（Infrastructure 外部集成：网络/SDK/WCDBSwift/三方）

**正向生成动作**：①在 `Domain` 定适配器协议 `IXxxAdapter`（让 Domain 零依赖于具体 SDK）；②在 `Infrastructure/Adapters` 或 `Infrastructure/Services` 实现，封装 SDK/网络/WCDBSwift 细节；③`Container+Infrastructure.swift` 注册 Factory；④原始错误转为域错误/`PersistenceError`。

```swift
// Domain 侧协议（零 SDK 依赖）
protocol IOnDeviceLLMAdapter { func run(prompt: String) async throws -> String }
// Infrastructure 实现（独占 SDK/IO 细节）
final class OnDeviceLLMAdapter: IOnDeviceLLMAdapter {
    private let fileSystem: IFileSystem
    init(fileSystem: IFileSystem) { self.fileSystem = fileSystem }
}
```

**新建一张表（WCDBSwift）**：①表/列定义集中到 `Persistence/Entities` 的 WCDB 表对象（`Codable`+`TableCodable`），不散落 repository；②建表/迁移逻辑集中在 `DatabaseManager`/`EnhancedDatabaseManager`，迁移按版本推进、新列给默认值或 `fromMap` 兜底；③供 repository 实现消费，绝不让 ViewModel/View 直接拿 `Database`。

- **七类收敛口径（external 不拆分）**：iOS **不**像 flutter 九类那样把外部集成拆成 `external-platform` / `api-network` / `db-dao` 三类，而是**统一为 `external` 一类**——网络（URLSession/Moya）、三方 SDK、WCDBSwift 持久化引擎的**实现**全部归本类（Infrastructure 层）；对应的**接口**（`IXxxAdapter` / `IXxxRepository` / 表对象映射的对外协议）归 `domain-model`（实体/值对象/`enum Error`）与 `repository` 接口同层（Domain 层，零依赖）。换言之"接口在 Domain、实现归 external"，不为网络/DB/SDK 单列第八/九类 doc_type。
- **边界**：external 只做"对接外部 + 翻译错误/数据格式"；不做业务编排（usecase）、不做 UI（view）。网络层框架（URLSession/Moya）、日志后端（OSLog/SwiftyBeaver）、JSON 修复策略、mock 生成（手写/Mockolo）等取值按对应 `[SLOT-network]`/`[SLOT-logging]`/`[SLOT-json-repair]`/`[SLOT-mock]`。
- **产物合同**：适配器协议签名 + 封装的 SDK/接口 + 错误翻译表（SDK error → 域/持久化 error）+ 线程语义。
- **可验证信号**：SDK/`WCDBSwift` import 只出现在 `Infrastructure/`；Domain/UI `grep` 不到这些 import。
- **好例子**：`OnDeviceLLMAdapter`、`F5TTSAdapter`、`StoryRepository`（持久化 external 实现）。**坏例子**：在 usecase 里 `import WCDBSwift` 或在 ViewModel 里直连 Moya。
- **不适用**：纯本地计算（usecase/domain-model）。
- **Gate 判定**：SDK 细节泄漏到 Domain/UI、原始错误裸抛到 UI → 详细/实现 Gate fail。

## 9. coordinator 迷你路径（App 层导航 + FactoryKit DI 装配）

**正向生成动作**：①导航目的地加进 `AppCoordinator.NavigationDestination` enum；②`AppCoordinator` 加 `navigateToXxx()` 改 `@Published activeDestination`（实测 `App/Coordinators/AppCoordinator.swift`）；③在 `Container+Coordinators.swift` 把导航动作暴露为 `Factory<() -> Void>` / `Factory<(String) -> Void>` 供 view 注入。

```swift
// App/Coordinators/AppCoordinator.swift
class AppCoordinator: ObservableObject, Coordinating {
    @Published var activeDestination: NavigationDestination?
    enum NavigationDestination: Equatable { case storyCreation, storyDetail, setting, myVoices }
    func navigateToSetting() { activeDestination = .setting }
}
// Container+Coordinators.swift —— 导航动作以闭包 Factory 暴露
var navigateToSetting: Factory<() -> Void> {
    self { [weak coordinator = self.appCoordinator()] in { coordinator?.navigateToSetting() } }
}
```

- **边界**：coordinator 只管"去哪"（改导航态/装配依赖），不写业务（usecase）、不写持久化（repository）、不直接渲染（view）。DI 装配（Factory 计算属性）是 coordinator 类的横切职责，集中在 `App/DependencyInjection/`。
- **产物合同**：新增 `NavigationDestination` case + `navigateToXxx` 方法 + 对应 Factory 闭包 + view 侧消费点（哪个 View 注入哪个导航闭包）。
- **可验证信号**：feature 间跳转全部经 `AppCoordinator`；`grep` 跨 feature 的 `NavigationLink(destination: OtherFeatureView())` 应为 0。
- **好例子**：`HomeView` 注入 `navigateToSetting` 闭包，点击调用改 `activeDestination`。**坏例子**：View A 里直接 `NavigationLink` 到 View B 的页面。
- **不适用**：feature 内部局部状态切换（用本地 `@State`/ViewModel）。
- **Gate 判定**：view 间硬导航 / DI 用手动 new 替代 Factory → 概要+实现 Gate fail。

## 10. 自检（跑完任意 doc_type 都要过）

```bash
# 构建自动化按 [SLOT-build]（Fastlane 等）；本地最小自检：
swiftlint                              # 代码组织/import 方向/命名（按 [SLOT-lint] 规则集）
xcodebuild build -scheme StoryVerse    # 编译通过
xcodebuild test -scheme StoryVerse     # 测试框架按 [SLOT-test]（XCTest → Quick/Nimble）
```
自检产物登记进任务 `implement.jsonl` / `check.jsonl`（带 reason），作为实现 Gate 证据。

---

## 11. 禁止清单（汇总，门禁拦）

**通用硬禁止（任何项目不可豁免）**：
- ❌ `Domain` 层 import `App`/`Infrastructure`/`UI`（破坏 Domain 零依赖，§2.1）。
- ❌ `view` 间直接导航（绕过 coordinator，§2.1/§9）。
- ❌ `view`/`viewmodel` 直接访问持久化或 import repository 实现/`WCDBSwift`（§2.1/§6/§7）。
- ❌ 接口与实现混在一个文件（`usecase`/`repository`/`external`，§2.2）。
- ❌ 业务依赖手动 `new` / `view` 的 `body` 里 init ViewModel（绕过 FactoryKit `@Injected`，§2.3）。
- ❌ `usecase` 环形/双向依赖、`usecase` import SwiftUI/持 `@Published`（§2.1/§5）。
- ❌ 不用 `enum XxxError`（每域错误枚举）或把 `WCDBSwift` 原始错误裸抛到 UI（§2.5）。
- ❌ `private` 方法与 `public`/`internal` 混合声明、未进 `private extension`（§2.6）。
- ❌ 用 CoreData/SwiftData 替代 WCDBSwift（§2.7）。
- ❌ `view` 硬编码用户可见文案（不走本地化，§7）。
- ❌ 自创第八类 doc_type / 用 `service`/`transport-handler`/`datasource` 当 token（§开篇）。

**按项目约定执行的禁止（取值见 project-conventions）**：
- ❌ 违反 `[SLOT-ui-framework]`（如该项目定纯 SwiftUI 则新代码不得引入 RxSwift）。
- ❌ 网络层不走 `[SLOT-network]` 选定栈、日志不走 `[SLOT-logging]`、JSON 修复不走 `[SLOT-json-repair]`。
- ❌ feature 落在 `[SLOT-feature-structure]` 之外的目录、repository 实现落在 `Infrastructure/Persistence/Repositories/` 之外。
- ❌ 主题硬编码颜色/尺寸而不经 `[SLOT-theme]`（`ThemeManager`）、mock 不按 `[SLOT-mock]`、测试不用 `[SLOT-test]` 框架。

## 12. 门禁映射（三层各管什么）
| 规则 | 脚手架 | SwiftLint/SwiftFormat | review |
|------|:---:|:---:|:---:|
| §2.1 分层依赖律（import 方向） | | ✅ | ✅ |
| §2.2 接口/实现分离 | ✅ | ✅ | |
| §2.3 FactoryKit DI 策略 | ✅ | ✅ | ✅ |
| §2.4 命名/目录 | ✅ | ✅(读项目约定) | |
| §2.5 enum Error 分层 | | | ✅ |
| §2.6 private extension 组织 | ✅ | ✅ | ✅ |
| §2.7 WCDBSwift 唯一持久化 | ✅ | ✅(禁 CoreData/SwiftData import) | ✅ |
| §4 repository 经 DatabaseManager | ✅ | ✅ | |
| §5 usecase 零 UI 依赖 | | ✅(禁 import SwiftUI) | ✅ |
| §6/§7 viewmodel/view 不直连持久化 | ✅ | ✅ | ✅ |
| §9 view 间不直接导航 | | ✅ | ✅ |
| §7 文案走本地化 | | ✅ | hooks |

## 13. 流程承接与编号（Gate 兼容）

- **需求五要素**：行为 / 前置条件 / 状态变化 / 失败路径 / 验收场景五项齐 → 才进概要（缺任一不进）。行为以 `BHV-NNN` 为 PRD 标题编号，下游引用裸 token。
- **概要归属表 + 承接索引**：每个 `BHV-NNN` 落唯一 owner doc_type（七类之一）+ 三问理由（为何归此层、依赖谁、谁依赖它），违反 §2.1 分层依赖律或承接索引缺失 → 不进详细。owner 层映射：`view`/`viewmodel`→UI，`coordinator`→App，`usecase`/`repository` 接口/`domain-model`→Domain，`repository` 实现/`external`→Infrastructure。
- **详细合同八问**：设计单元以 `UNIT-<slug>` 为详细标题编号；八问 = ①职责边界 ②输入/依赖（注入什么）③输出/产物合同 ④抛错（哪个 `enum Error` 的哪些 case）⑤分层归属与 import 约束 ⑥可验证信号 ⑦测试映射（`[SLOT-test]` 用例）⑧不适用场景。缺项 / 追溯不到概要 owner / 无测试映射 → 不进实现。
- **实现 trace 四节**：①对照的 `UNIT-<slug>`/`BHV-NNN` ②实现文件与 DI 注册点 ③自检证据（§10 输出）④偏差与豁免（存量违例记债，清单外新增违例阻塞）。四节不全 → 不进 commit。

## 14. v1 详细设计交付状态（L2 映射）

与 flutter `controller/usecase/repository-datasource` 三类 L2 一一对应，v1 提供三份 L2 文件（落 `.trellis/spec/harness/detail/`）：
- `detail-type-viewmodel.md`（对应 flutter `detail-type-controller.md`）
- `detail-type-usecase.md`（对应 flutter `detail-type-usecase.md`）
- `detail-type-repository.md`（对应 flutter `detail-type-repository-datasource.md`，含 Domain 接口 + Infrastructure 实现合并口径）

其余四类 `domain-model` / `view` / `coordinator` / `external` 为 **pending**：full 链须显式 `L2豁免` 或先补 L2，light 链按 §13 详细合同八问展开并标注 `l2_status: pending`。

## 15. 派生关系（给 build 用）
- **脚手架模板** ← §3~§9 各 doc_type 的代码块参数化（参数 = project-conventions 槽位）；按 §1 入口决策树条件组合。
- **SwiftLint/SwiftFormat 规则** ← §2 + §11（import 方向 / `private extension` / 禁 CoreData·SwiftData import / 禁 SwiftUI 进 usecase / 命名后缀；槽位类规则运行时读目标仓库 project-conventions）。
- **配置包 Skill（概要/详细/实现三件套）** ← 全文 + 各自 references（§14 的三份 L2）；所有 agent 适配层指向本文，不各写一份。
- **hooks** ← §7 文案本地化拦截 + §11 老目录/禁用框架拦截（读 `[SLOT-feature-structure]`/`[SLOT-ui-framework]`）+ §10 自检回灌。
