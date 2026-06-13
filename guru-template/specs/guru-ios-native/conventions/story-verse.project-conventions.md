# Project Conventions — story-verse (iOS Native)

> 按 iOS 平台 project-conventions 模板填写。安装配置包时将本文件迁入 story-verse 仓库 `.trellis/spec/conventions/project-conventions.md`，并与 `.trellis/spec/guides/golden-path.md`、`.trellis/spec/harness/*` 协同生效。
> 取值依据：2026-06-14 对 `story-verse-mac`（macOS 原生，SwiftUI + DDD 四层）的全仓实测扫描；doc_type 与分层一律以 IOS_BRIEF 七类为权威，未照抄 flutter/Go 类型名。
> 槽位编号体系与 `project-conventions.template.md`（canonical 权威）一致：SLOT-01~SLOT-16，SLOT-16 为存量违例清单（最后一个槽位）。本样例仅列实测取到值的槽位，模板有而本仓未取值的槽位（如 SLOT-15 构建自动化）属「未取值」不列。
> 本文件只钉**项目约定槽位**（与 golden-path 通用硬规则互补）；通用硬规则（FactoryKit DI / Repository 模式 / enum Error 分层 / WCDBSwift / ObservableObject+@Published / private extension）见 golden-path.md，不在此重复定义，只在槽位取值与硬规则冲突时显式标注豁免。

## 0. 元信息

| 字段 | 取值 |
|------|------|
| App 名称 / Bundle | StoryVerse（macOS 原生应用，`platform :macos, '10.15.3'`） |
| 仓库路径 | `story-verse-mac/StoryVerse/StoryVerse/`（源码根；外层 `StoryVerse/` 为 Xcode workspace 容器） |
| 架构 | DDD 四层 Domain → App → Infrastructure → UI；SwiftUI 主体；FactoryKit `@Injected` DI；Repository 模式（接口 Domain / 实现 Infrastructure）；AppCoordinator 导航；WCDBSwift 持久化 |
| 填写日期 / 填写人 | 2026-06-14 / client_agent iOS 配置包（实测扫描） |
| 取值依据 | 实测扫描 + 规范文档 `StoryVerse/docs/PROJECT_STRUCTURE.md`、`StoryVerse/docs/Swift_代码组织规范.md`；存量违例为代码实测，待团队 redline 确认 |
| doc_type 权威 | viewmodel / usecase / repository / domain-model / view / coordinator / external（七类，全程唯一，禁改名增减） |

> 文档与实测的偏差登记（重要）：`PROJECT_STRUCTURE.md` 第 46-49 行写「ViewModels 用 `@Observable`，no ObservableObject」，但全仓 ViewModel（10 个 `*ViewModel` 类，截至 2026-06-14 实测）一律 `class XxxViewModel: ObservableObject` + `@Published`，ViewModel 侧零 `@Observable` 宏（见 SLOT-01）。**以实测为准**：ViewModel = `ObservableObject` + `@Published`，该文档段落属过期描述（aspirational），不作为归属基准。注：`@Observable` 宏全仓仅 1 处，落在 `Core/Utilities/ObservableEnvironment.swift`（Repository 自动观察的环境管理器单例，非 ViewModel），与 ViewModel 形态取值无关。

## 1. 槽位清单

### SLOT-01 UI 框架基线 / ViewModel 形态（SwiftUI 主 + RxSwift 遗留 → 纯 SwiftUI；ObservableObject + @Published）
- 本项目取值（UI 框架）：新代码**纯 SwiftUI**（`View` + `ObservableObject` ViewModel + `@Published`）。RxSwift/RxCocoa 虽在 `Podfile` 声明（`pod 'RxSwift' / 'RxCocoa' / 'RxGesture' / 'Moya/RxSwift'`），但 Swift 源码实际仅 1 处 `import RxSwift`（`Core/Extensions/StringExtension.swift`），属遗留依赖，不在业务层使用。响应式诉求统一走 **Combine**（17 文件 `import Combine`）+ SwiftUI `@Published`。
- 本项目取值（ViewModel 形态）：ViewModel = `class XxxViewModel: ObservableObject` + `@Published` 状态字段，依赖经 `@Injected(\.xxxUseCase)`（FactoryKit）注入，**禁手动 init 构造依赖**。异步加载用 `Task { ... await MainActor.run { ... } }` 回主线程更新 `@Published`。view 侧用 `@InjectedObject(\.xxxViewModel)` 持有。`@Observable` 宏（Observation 框架）在 ViewModel 层**未启用**（10 个 ViewModel 全为 `ObservableObject`，截至 2026-06-14 实测）；全仓 `@Observable` 仅 1 处（`Core/Utilities/ObservableEnvironment.swift`，Repository 自动观察的环境单例，非 ViewModel），不作为 ViewModel 形态先例。
- 生效范围：新代码。**禁止**在 view/viewmodel 新引入 RxSwift；新增异步流用 Combine `Publisher` 或 Swift Concurrency `AsyncStream`。此处钉死「ObservableObject 而非 @Observable」的项目取值，覆盖 `PROJECT_STRUCTURE.md` 过期描述。
- 代码证据：`UI/Features/Home/ViewModels/HomeViewModel.swift`（`class HomeViewModel: ObservableObject` + 5 个 `@Injected`：4 个 `\.xxxUseCase` + 1 个 `\.fileSystem` + `@Published`）；`UI/Features/Home/Views/HomeView.swift`（纯 SwiftUI）；遗留 `Core/Extensions/StringExtension.swift`（唯一 `import RxSwift`）；`StoryVerse/Podfile`（Rx pods 声明）；全仓 18 个 `class X: ObservableObject`（其中 10 个为 `*ViewModel`，余 8 个为 `AppCoordinator`/`ThemeManager`/`ToastManager`/`DynamicLayoutManager`/`RootViewState`/`VoicePlayer`/`VoiceRecorder`/`StoryAudioPlayer`）；`@Injected`/`@InjectedObject` 合计 73 处（67 `@Injected` + 6 `@InjectedObject`，全部落在 UI 层 21 个文件）；ViewModel 侧 0 处 `@Observable`（全仓 `@Observable` 仅 `ObservableEnvironment.swift` 1 处，非 ViewModel）。
- 好例：viewmodel 用 `@Published var recentStories: [Story] = []`，view 通过 `@InjectedObject(\.homeViewModel)` 观察；`@Injected(\.storyManageUseCase) var storyManageUseCase`。
- 坏例：(1) view 内 `Observable<T>.create { ... }.subscribe(...)`（引入 Rx 数据流）→ 阻塞；(2) ViewModel 用 `@Observable` 宏（与现有 10 个 `ObservableObject` ViewModel 不一致，割裂）；(3) `init(useCase: ...)` 手动注入而非 `@Injected`；(4) 见 SLOT-16 #5——`catch {}` 空吞错误，状态机无错误分支。
- 不适用：`StringExtension.swift` 既有遗留 Rx 扩展可保留维护，但禁扩散到其它文件；极简纯展示组件可不建 ViewModel，状态用 `@State`。
- Gate：view/viewmodel 文件出现 `import RxSwift|RxCocoa|RxRelay` 且非 SLOT-16 登记的遗留文件 → fail（新增违例）；viewmodel 非 `ObservableObject` / 依赖手动 init / 空 `catch {}` 吞业务错误 → fail。

### SLOT-04 enum Error 分层定义
- 本项目取值：错误按领域/层各自定义 `enum Error`，**禁全局通用 Error 桶**。Domain 错误置 `Domain/Errors/`（`StoryError` / `ExportTaskManagerError` / `VoiceConfigurationError`，均 `enum X: Error, Equatable` + 关联值携带原因 `case validationFailed(reason: String)`）；Infrastructure 错误就近定义（如 `Infrastructure/Models/TTS/TTSError.swift`、`AIModelDownloaderService` 内 `case downloadCancelledByRequest(taskId:)`、JSON 修复 `JSONRepairError`、持久化 `PersistenceError`）。手动实现 `Equatable` 以便 XCTest 断言。
- 生效范围：全量（与 golden-path 硬规则一致）。
- 代码证据：`Domain/Errors/StoryError.swift`（`enum StoryError: Error, Equatable` + 5 case + 手写 `==`）；`Domain/Errors/ExportTaskManagerError.swift`、`VoiceConfigurationError.swift`；`Infrastructure/Models/TTS/TTSError.swift`；`Domain/Repositories/IStoryRepository.swift` 内 `enum PersistenceError: Error, Equatable`。
- 好例：`enum StoryError: Error, Equatable { case validationFailed(reason: String) }`，usecase `throw StoryError.validationFailed(reason:)`。
- 坏例：跨域复用某个不相关 enum 的 case；或抛 `NSError`/裸 `String` 当错误。
- 不适用：第三方 SDK 抛出的错误在 external/Infrastructure 边界转译为本层 enum 后上抛。
- Gate：新错误未定义为分层 `enum X: Error`（关联值携带 reason）/ 跨层复用错误类型 → fail。

### SLOT-08 网络层（URLSession / Moya）
- 本项目取值：**本应用为本地优先（on-device）应用，无常规 REST 后端层**。实测 `URLSession` 直接使用 0 处、无 `Infrastructure/Network/` 目录、无 `MoyaProvider`/`TargetType` 业务调用、无 `import Alamofire`。外部 I/O 由 `external` doc_type 承担，形态为：(1) Hugging Face 模型下载（`Infrastructure/Services/AIModelDownloader/AIModelDownloaderService.swift`，Swift Concurrency `async/await` + `Task` + 进度 `DownloadTaskProgress`）；(2) Firebase（Messaging / RemoteConfig / Crashlytics / Auth / DynamicLinks，见 `Podfile` `firebase_pods`）；(3) 端侧 LLM/TTS 适配器（`Infrastructure/Adapters/OnDeviceLLMAdapter.swift`、`TTS/F5TTSAdapter.swift`）。`Moya/RxSwift` 在 `Podfile` 声明，但 Swift 业务代码 `import Moya` **0 处**（截至 2026-06-14 实测）；仅余两类无害痕迹：`Core/Utilities/CodableExtension/` 下 3 个文件保留 `// Moya-Cuddle` 模板头注释，`App/DependencyInjection/Container+Infrastructure.swift` 第 273 行有一行被注释掉的 `// self { MoyaNetworkClient() }` 注册。
- 生效范围：全量。新增任何远端/SDK/下载集成一律归 `external`（Infrastructure 层），**禁止** view/viewmodel/usecase 直接发网络请求；usecase 经 Domain 接口（如 `IAIModelDownloaderService` 风格协议）调用，实现落 Infrastructure。
- 代码证据：`Infrastructure/Services/AIModelDownloader/AIModelDownloaderService.swift`（`func downloadModel(from huggingFaceRepoId:...) async throws -> UUID`）；`StoryVerse/Podfile`（`firebase_pods` / `pod 'Moya/RxSwift'`）；全仓 `grep URLSession` = 0。
- 好例：新远端能力 → Domain 定 `IXxxProvider` 接口 → Infrastructure `XxxProvider` 实现（`external`）→ Container 注册 → usecase `@Injected` 调用。
- 坏例：viewmodel 内 `URLSession.shared.dataTask(...)` 或 view 直连 Firebase RemoteConfig 读取业务配置。
- 不适用：纯端侧推理（LLM/TTS）无网络，仍归 `external`（外部 SDK 集成语义）。
- Gate：view/viewmodel/usecase 出现 `URLSession|MoyaProvider|Alamofire|URLRequest` → fail；远端逻辑未经 Domain 接口收口 → fail。

### SLOT-09 日志（SwiftyBeaver → OSLog）
- 本项目取值：当前底座为 **SwiftyBeaver**——`Infrastructure/Services/Logger.swift` 定义 `protocol ILogger` + `LogType` 枚举（emoji 前缀 debug/info/notice/warning/critical/error/network）+ `Loggerable` 协议（强制注入 logger）；调用点用 `Logger.d(...)` / `Logger.e(...)` 静态门面。**统一收口规则**：所有日志走 `ILogger` 协议（依赖注入）或 `Logger` 静态门面，禁止裸 `print` / 散落 `os_log`。OSLog 为迁移目标，新代码可选 OSLog 但须封进 `ILogger` 实现，不得绕过门面。
- 生效范围：全量。
- 代码证据：`Infrastructure/Services/Logger.swift`（`protocol ILogger` / `enum LogType` / `protocol Loggerable`）；调用样本 `Infrastructure/Services/AIModelDownloader/AIModelDownloaderService.swift`（`Logger.d("download ... start task")`）。
- 好例：组件实现 `Loggerable`，构造注入 `logger: any ILogger`，调用 `logger.error(...)`。
- 坏例：见 SLOT-16 #3——`Infrastructure/Persistence/Repositories/StoryRepository.swift` 顶部私自 `extension Logger { static func e(_:) { os_log(...) } }` 直连 `os_log`，绕过 SwiftyBeaver 底座（日志双轨）。
- 不适用：`#if DEBUG` 临时排错 print 可短期存在，提交前清理。
- Gate：新代码出现裸 `print(`（非测试）或自建 `os_log` 包装绕过 `ILogger` → fail。

### SLOT-10 JSON 修复策略
- 本项目取值：LLM 原始输出可能是脏 JSON，统一经 **`IJSONRepairService`** 修复——接口 `Core/Utilities/IJSONRepairService.swift`，实现 `Core/Utilities/JSONRepairService.swift`（`func repair(_ invalidJSON: String, strategy: JSONRepairStrategy) async throws -> String`，支持纯文本修复与 LLM 辅助修复两档，含 `JSONRepairConfig` / `JSONRepairError` / 可选 `JSONRepairMetrics`）。解析编排经 `Domain/Services/StoryParsingStrategy.swift`（`protocol StoryParsingStrategy` + `DefaultStoryParsingStrategy` 持有 `jsonRepairService`），usecase（`App/UseCases/LLMUseCase/LLMUseCase.swift`）调用解析策略，不在 viewmodel/view 手搓 `JSONDecoder`。
- 生效范围：全量（凡解析 LLM/外部不可信 JSON）。
- 代码证据：`Core/Utilities/IJSONRepairService.swift` + `Core/Utilities/JSONRepairService.swift`；`Domain/Services/StoryParsingStrategy.swift`（`DefaultStoryParsingStrategy` 注入 `IJSONRepairService`）；`App/UseCases/LLMUseCase/LLMUseCase.swift`。
- 好例：usecase → `StoryParsingStrategy.parse(rawLLMOutput:initialTitle:)`，内部失败时 `JSONRepairService.repair(...)` 修复后重试。
- 坏例：viewmodel 直接 `try JSONDecoder().decode(Story.self, from:)` 解析 LLM 输出（无修复，脏 JSON 即崩）。
- 不适用：本地受信资源（如随包 `System Stories.zip` 解出的结构化数据）可直接 decode。
- Gate：解析 LLM/外部 JSON 未经 `IJSONRepairService`/解析策略 → fail。结构债：`IJSONRepairService` 现居 `Core/Utilities/` 而非 `Domain/Services/`，登记于 SLOT-16 #8，新接口应入 Domain。

### SLOT-11 主题（ThemeManager 单例）
- 本项目取值：主题统一经 **`ThemeManager` 单例**——`Infrastructure/Theme/ThemeManager.swift`（`class ThemeManager: ObservableObject` + `static let shared` + `@Published private(set) var currentTheme: Theme` + `@AppStorage("theme_id")` 持久化）。颜色/字体经 `Theme` 值对象（`Infrastructure/Theme/Models/Theme.swift` / `ThemeColors.swift` / `ThemeFonts.swift`）取，view 经主题修饰器（如 `.themedBackground(\.card)`，见 `ThemeExtensions.swift` / `ThemeWrappers.swift`）消费，**禁 view 内裸 `Color`/`Font` 字面量**。
- 生效范围：新代码。
- 代码证据：`Infrastructure/Theme/ThemeManager.swift`（`static let shared` + `@Published currentTheme`）；`UI/Features/Home/Views/HomeView.swift`（`.themedBackground(\.card)`）；`Infrastructure/Theme/ThemeExtensions.swift`。
- 好例：`.themedBackground(\.card)` / `theme.colors.primary`。
- 坏例：见 SLOT-16 #4——`HomeView.swift` 中 `.background(Color.white) // 设置背景为白色` 硬编码颜色，绕过主题。
- 不适用：纯黑/透明等语义无关常量（`.clear`）可直接用。
- Gate：新 view 裸用 `Color(...)` / `Font(...)` 字面量绕过 `ThemeManager`/主题修饰器 → fail。

### SLOT-12 i18n（Localizable.strings + R.swift）
- 本项目取值：文案源 `en.lproj/Localizable.strings`（`PROJECT_STRUCTURE.md` 第 65 行：所有文案须经此文件管理）；代码引用统一经 **R.swift 生成的 `R.string.localizable.xxx()`** 强类型 key（如 `R.string.localizable.homeWelcome()`），全仓 53 处（截至 2026-06-14 实测）。注：`NSLocalizedString(` 实测 0 处、无自建 `"...".localized` 字符串扩展（仓内 `.localized` 命中均为 Swift 内建 `error.localizedDescription`，非用户文案），故本地化唯一权威机制即 `R.string.localizable.*`。新文案先入 `Localizable.strings`，再用 `R.string.localizable.<key>()` 引用，禁硬编码中英文字面量入 view。
- 生效范围：全量。
- 代码证据：`en.lproj/Localizable.strings`；`UI/Features/Home/Views/HomeView.swift`（`.navigationTitle(R.string.localizable.homeWelcome())`）。
- 好例：`Text(R.string.localizable.homeWelcome())`。
- 坏例：`Text("欢迎")` 硬编码，或 `Text("Welcome")` 英文字面量直写 view。
- 不适用：日志/调试串、enum rawValue（非用户可见）无需 i18n。
- Gate：view 出现用户可见硬编码字面量（非 R.string/NSLocalizedString）→ fail。

### SLOT-13 feature 模块结构
- 本项目取值：UI 按 **feature 切目录**，路径 `UI/Features/<Feature>/`，内部子目录 `Views/`（SwiftUI View）+ `ViewModels/`（ObservableObject）；复杂 feature 再下钻子模块（如 `Design/{Creation,Illustration,Preview,Sound}/` 各自 `Views/`+`ViewModels/`）；feature 私有模型置 `Models/`、私有组件置 `Components/`。跨 feature 复用组件入 `Shared/`，全局状态入 `UI/States/`（如 `RootViewState`）。命名：view `XxxView`、viewmodel `XxxViewModel`。
- 生效范围：新代码。
- 代码证据：实测 `UI/Features/` 下 Home / Design / Launch / Stories / Voice / MyVoices / Root / Creations / Setting / Story 共 10 feature；`UI/Features/Home/{Views,ViewModels}/`；`UI/Features/Design/Illustration/{Views,ViewModels,Character,Picture}/`。
- 好例：新 feature `Library` → `UI/Features/Library/Views/LibraryView.swift` + `UI/Features/Library/ViewModels/LibraryViewModel.swift`。
- 坏例：view 与 viewmodel 平铺在 `UI/` 根；或跨 feature 直接 import 另一 feature 的私有 View（应走 `Shared/` 或 coordinator）。
- 不适用：`Shared/Components` 复用组件不归任何单一 feature。
- Gate：新 UI 未落 `UI/Features/<Feature>/{Views,ViewModels}/` 结构 → fail；feature 间直接导航（不走 coordinator）→ fail（违反分层依赖律）。

### SLOT-14 测试约定 + mock 生成（XCTest → Quick/Nimble；手写 → Mockolo）
- 本项目取值（测试框架）：**XCTest**（36 个测试文件 `import XCTest`，截至 2026-06-14 实测，0 处 Quick/Nimble），`final class XxxTests: XCTestCase`，异步用 `func test...() async throws` + `setUp() async throws`/`tearDown()`。测试目录 `StoryVerseTests/` 按层镜像源码：`Domain/`、`UseCases/<Feature>/`、`Infrastructure/{Adapters,Services}/`、`Integration/`、`TestHelpers/`。domain-model 的 `enum Error: Equatable` 便于断言（见 SLOT-04）。Quick/Nimble 为目标方向，迁移前新测试仍 XCTest。
- 本项目取值（mock 生成）：测试 mock 当前**全手写**——`StoryVerseTests/TestHelpers/MockClasses.swift`、`StoryVerseTests/UseCases/ManageAIModels/MockAIModelDownloaderService.swift`、`MockApplicationInfoService.swift`、`MockDatabaseManager.swift` 等，命名 `Mock<协议名去 I>`。无 Mockolo（0 处 `@mockable`/Mockolo 标注）。仓库与 DB 相关测试倾向用**真实临时实例**（`EnhancedDatabaseManager(databasePath: 临时路径)` + 真实 `AIModelRepository`），仅对外部服务 mock。Mockolo 为目标方案，迁移前新 mock 仍手写、置于 `StoryVerseTests/` 对应镜像目录。
- 生效范围：全量（测试）。
- 代码证据：`StoryVerseTests/ManageAIModelsUseCaseTests.swift`（`final class ... : XCTestCase` + `setUp() async throws`，内建真实临时 DB + 手写 mock service）；目录 `StoryVerseTests/UseCases/LLMUseCase/ImagePromptsValidationTests.swift`；36 文件 `import XCTest`（截至 2026-06-14 实测）；`StoryVerseTests/TestHelpers/MockClasses.swift`；`StoryVerseTests/UseCases/ManageAIModels/MockAIModelDownloaderService.swift`。
- 好例：usecase 测试镜像入 `StoryVerseTests/UseCases/<Feature>/XxxUseCaseTests.swift`；协议 `IAIModelDownloaderService` → 手写 `MockAIModelDownloaderService` 实现，置 `StoryVerseTests/UseCases/ManageAIModels/`。
- 坏例：测试文件不镜像层级、平铺根目录；引入 Quick/Nimble 与现有 XCTest 双轨；在被测 production 代码里塞测试 stub；或 mock 文件散落 production target。
- 不适用：UI 快照/集成测试入 `StoryVerseUITests/` / `StoryVerseTests/Integration/`；DB/仓库集成测试用真实临时实例，不强制 mock。
- Gate：新测试非 XCTest（无团队 redline 批准 Quick/Nimble 迁移）/ 不镜像源码层级 → fail；mock 落入 production target / 命名非 `Mock<Name>` → fail。

### SLOT-16 存量违例清单（tech-debt 登记）
> 清单内为已知存量，可暂存维护；**清单外的同类问题一律按「新增违例」阻塞（fail）**。
1. **Domain 层非零依赖（最严重，违反归属硬基准）**：截至 2026-06-14 实测，Domain 层共 4 个文件含非 `Foundation` import——`Domain/Adapters/IImageFromPromptProvider.swift`（`import SwiftUI` + `import AppKit`）；`Domain/Services/Files/ILocalImageStorageService.swift`（`import AppKit`）；`Domain/Services/IExportTaskManager.swift`（`import Combine`）；`Domain/Services/ExportTaskManager.swift`（`import Combine`）。Domain 应零依赖（只 `import Foundation`），现引入 UI/系统/响应式框架 → 污染领域纯度。新 Domain 文件**禁止** `import SwiftUI|AppKit|Combine|WCDBSwift|FactoryKit`。
2. **领域服务接口与实现同层混放，且实现违反 Domain 零依赖（实现应迁 Infrastructure）**：`Domain/Services/ExportTaskManager.swift` 是一个完整的具体实现——`final class ExportTaskManager: IExportTaskManager`，构造依赖 `IExportTaskRepository`/`IStoryRepository`/`IExportAdapterFactory`/`PriorityTaskQueueImpl`/`ILogger`，内含 `actor InternalState` 线程安全状态机与 `import Combine`（截至 2026-06-14 实测）；接口 `Domain/Services/IExportTaskManager.swift` 与之同层并放于 Domain。按 Repository 模式与 §2 分层归属基准，接口（`IExportTaskManager`）应留 Domain、具体实现（`ExportTaskManager`）应迁 `Infrastructure/Services/`（Domain 仅保留接口与 `Domain/Errors/ExportTaskManagerError.swift`），以同时满足「接口与实现分离」与「Domain 零依赖（去掉 `import Combine`）」两条硬基准。新增同类服务一律「接口 Domain / 实现 Infrastructure」。
3. **日志双轨**：`Infrastructure/Persistence/Repositories/StoryRepository.swift` 顶部自建 `extension Logger { static func e(_:) { os_log(...) } }` 直连 `os_log`，绕过 SwiftyBeaver `ILogger` 底座（与 SLOT-09 冲突）。
4. **主题硬编码绕过**：`UI/Features/Home/Views/HomeView.swift` 出现 `.background(Color.white) // 设置背景为白色`，绕过 `ThemeManager`（与 SLOT-11 冲突）。
5. **ViewModel 空吞错误**：`UI/Features/Home/ViewModels/HomeViewModel.swift` 的 `loadStorys()` 内 `catch { }` 为真正空块（仅空行），吞业务错误且无错误状态机 / 无日志（与 SLOT-01 ViewModel 形态 + SLOT-04 冲突）；截至 2026-06-14 实测，UI 层空 `catch {}` 共 2 处、全仓共 16 处（含 Infrastructure/Core 等非 UI 层），新代码禁再新增空 catch。
6. **View 越层直连 Repository（违反分层依赖律）**：`UI/Features/Home/Views/HomeView.swift` 同时 `@Injected(\.storyRepository) private var storyRepository` 并 `.autoObserve(storyRepository, ...)`，View 直接持有并订阅 repository，绕过 viewmodel/usecase（应由 viewmodel 持有 repository 订阅，view 只观察 viewmodel）。
7. **持久化双管理器并存**：`Infrastructure/Persistence/DatabaseManager.swift`（旧单例 `static let shared`，DB 名 `storyverse.db`）与 `Infrastructure/Persistence/EnhancedDatabaseManager.swift`（线程安全增强版，DI 注入仓库实际使用）共存；新仓库一律注入 `EnhancedDatabaseManager`，`DatabaseManager` 为遗留。
8. **JSON 修复接口错层**：`IJSONRepairService` 居 `Core/Utilities/` 而非 `Domain/Services/`（与 DDD 接口归属不符，见 SLOT-10）。
9. **RxSwift/Moya 遗留依赖**：`Podfile` 声明 RxSwift/RxCocoa/RxGesture/Moya，但 Swift 业务代码近乎不用（截至 2026-06-14 实测：`import RxSwift` 仅 1 处于 `Core/Extensions/StringExtension.swift`，`import RxCocoa|RxRelay|RxGesture` 0 处，`import Moya` **0 处**）。⚠️ 此前登记「1 处 Moya import 于 `DesignIllustrationCharacterView.swift`」系误判（张冠李戴）：该 view 仅含 `import SwiftUI/SwiftUIIntrospect/UniformTypeIdentifiers`，文中 `dropTargetType`/`enum DropTargetType` 是本地拖拽枚举，与 Moya 的 `TargetType` 无关，现予更正。Moya 真实残痕只有 `Core/Utilities/CodableExtension/` 下 3 个文件的 `// Moya-Cuddle` 模板头注释与 `Container+Infrastructure.swift` 第 273 行被注释掉的 `// self { MoyaNetworkClient() }`（均非编译期依赖）。新代码禁扩散（见 SLOT-01/SLOT-08）。
- 生效范围：全量。

## 2. doc_type 与分层归属基准（钉死，违反直接 fail）

| doc_type | owner 层 | 实测落点 | 关键证据 |
|----------|---------|---------|---------|
| `domain-model` | Domain | `Domain/{Entities,ValueObjects,Enums,Errors}/` | `Domain/Entities/Story.swift`、`Domain/Errors/StoryError.swift` |
| `repository`（接口+实现合并一类） | Domain（`IXxxRepository` 接口）+ Infrastructure（实现） | 接口 `Domain/Repositories/IStoryRepository.swift`；实现 `Infrastructure/Persistence/Repositories/StoryRepository.swift` | `final class StoryRepository: ObservableRepository<Story, StoryObject>, IStoryRepository` |
| `usecase` | Domain（业务编排，零 UI 依赖） | `App/UseCases/<Feature>/` | `App/UseCases/LLMUseCase/LLMUseCase.swift`（`class LLMUseCase: ILLMUseCase`） |
| `viewmodel` | UI | `UI/Features/<Feature>/ViewModels/` | `UI/Features/Home/ViewModels/HomeViewModel.swift` |
| `view` | UI | `UI/Features/<Feature>/Views/` | `UI/Features/Home/Views/HomeView.swift` |
| `coordinator`（导航 + FactoryKit DI 装配） | App | `App/Coordinators/`、`App/DependencyInjection/Container+*.swift` | `App/Coordinators/AppCoordinator.swift`、`App/DependencyInjection/Container+Coordinators.swift` |
| `external`（网络/SDK/WCDBSwift 持久化/第三方） | Infrastructure | `Infrastructure/{Services,Adapters,Persistence}/` | `Infrastructure/Services/AIModelDownloader/AIModelDownloaderService.swift`、`Infrastructure/Persistence/DatabaseManager.swift` |

> 注 1：`usecase` 实测落在 `App/UseCases/`（App 层目录），但其语义/依赖契约属 Domain 编排（零 UI 依赖、只依赖 Domain 接口）；归属判定以「零 UI 依赖 + 经 Domain 接口」为准，目录位置不改判。
> 注 2：`coordinator` 双职责——`AppCoordinator`（`ObservableObject` + `@Published var activeDestination` 集中导航状态，非 `@Observable`）+ `Container+*.swift`（FactoryKit `extension Container` 装配，用默认 FactoryKit `Container`，自建 `SharedContainer` 子类已注释停用，见 `Container.swift`）。
> 注 3：分层依赖律（硬基准，违反直接 fail）：Domain 零依赖；方向 Domain→App→Infrastructure→UI 单向；禁 View 间直接导航（走 coordinator 的 `navigateToXxx` Factory 闭包）；禁 View 直接访问持久化/repository（走 viewmodel→usecase→repository）。存量违例见 SLOT-16 #1/#6。

## 3. golden-path 硬规则对照（本项目取值确认）

| 硬规则（golden-path 锁定） | 本项目取值确认 | 证据 |
|---------|---------|------|
| FactoryKit `@Injected` DI（禁手动初始化） | 确认，73 处 `@Injected`/`@InjectedObject`（67 + 6，截至 2026-06-14 实测，全部在 UI 层 21 文件；UseCase/Infrastructure 走 Container 构造注入而非属性包裹器），Container+*.swift 集中注册 | `HomeViewModel.swift`、`Container+UseCases.swift` |
| Repository 模式强制（接口 Domain / 实现 Infrastructure） | 确认 | `IStoryRepository.swift` + `StoryRepository.swift` |
| enum Error 分层定义 | 确认，Domain/Errors + 各层就近 | SLOT-04 |
| WCDBSwift 持久化（禁 CoreData/SwiftData） | 确认，16 文件 `import WCDBSwift`，0 处 CoreData/SwiftData/`@Model` | `DatabaseManager.swift`、`StoryObject.swift` |
| ViewModel `ObservableObject` + `@Published` | 确认，18 个 `ObservableObject` 类（其中 10 个 `*ViewModel`，截至 2026-06-14 实测），ViewModel 侧 0 `@Observable`（全仓 `@Observable` 仅 `ObservableEnvironment.swift` 1 处非 ViewModel） | SLOT-01 |
| private 方法在 `private extension`（含 MARK 分组） | 项目规范明文要求 | `docs/Swift_代码组织规范.md` |
| 写作顺序自底向上 | domain-model → repository → usecase → viewmodel → view + coordinator/external 横切 | IOS_BRIEF |

## 4. v1 L2 落地状态

| doc_type | L2 文件 | l2_status |
|----------|---------|-----------|
| `viewmodel` | `detail-type-viewmodel.md` | full |
| `usecase` | `detail-type-usecase.md` | full |
| `repository` | `detail-type-repository.md` | full |
| `domain-model` | —（按 L1 合同八问展开） | pending |
| `view` | —（按 L1 合同八问展开） | pending |
| `coordinator` | —（按 L1 合同八问展开） | pending |
| `external` | —（按 L1 合同八问展开） | pending |

> full 链须 L2 豁免；pending 四类在详细设计阶段按 L1 合同八问就地展开，编号纪律：行为 `BHV-NNN`（prd 标题）、设计单元 `UNIT-<slug>`（详细标题），下游引用裸 token。

## 5. 校验自检

- [x] C1 元信息齐全（含 doc_type 七类权威钉死 + 文档/实测偏差登记）
- [x] C2 本样例列出实测取值的 9 个槽位（SLOT-01 / 04 / 08 / 09 / 10 / 11 / 12 / 13 / 14，其中 SLOT-01 含 UI 框架与 ViewModel 形态两个取值、SLOT-14 含测试框架与 mock 生成两个取值），模板有而本仓未取值的 SLOT-02/03/05/06/07/15 属「未取值」未列；待定 0 项；SLOT-16 存量违例清单 9 条
- [x] C3 每个列出槽位均有真实代码证据路径（绝对落点见正文）
- [x] C4 取值与 golden-path 通用硬规则对照确认（§3），无未授权豁免；ObservableObject 取值显式覆盖 PROJECT_STRUCTURE 过期 @Observable 描述
- [x] C5 doc_type 严格用 IOS_BRIEF 七类（viewmodel/usecase/repository/domain-model/view/coordinator/external），未自创 transport-handler/service 等
- [x] C6 SLOT-16 存量违例清单存在（9 条）；分层归属基准表（§2）+ L2 落地状态（§4）齐备，装载路径用 `.trellis/spec/*`
