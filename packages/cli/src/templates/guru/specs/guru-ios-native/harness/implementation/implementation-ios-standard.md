# iOS 实现阶段标准包（L1 · guru-ios-native / golden-path 锁定）

> 本文件是 `guru-ios-native` Harness 的实现阶段 **L1 标准 SSOT**，由代码编写与实现审核**同源引用**。
> 目标平台：iOS / macOS 原生 · Swift · DDD 四层 `Domain → App → Infrastructure → UI`（Domain 零依赖）· SwiftUI 主 + RxSwift 遗留 · FactoryKit `@Injected` DI · Repository 模式 · `enum Error` per domain · WCDBSwift 持久化 · `AppCoordinator` 导航。
> grounded 在 `story-verse-mac`（`StoryVerse/StoryVerse/`）真实写法；详细设计 doc_type 与分层一律以 **IOS_BRIEF 七类**为权威，**不照抄** flutter（controller/usecase/repository-datasource）或 Go（handler/service/repository）的类型名。
> 实现阶段只**承接**已审核通过的详细设计，不重新设计业务行为、owner、依赖边界、错误语义、持久化语义、配置槽位或导航合同。
>
> 装载（安装后路径）：
> - 通用方法真源：`.trellis/spec/guides/golden-path.md`（分层依赖律、错误处理范式、DI canonical、导航契约、入口决策树、禁止清单）。
> - 流程骨架与本标准包：`.trellis/spec/harness/implementation/implementation-ios-standard.md`（本文件）。
> - 项目槽位取值：`.trellis/spec/conventions/project-conventions.md`（UI 框架 / 网络层 / 日志 / JSON 修复 / 测试框架 / i18n / 主题 / feature 模块结构 / mock 生成 / 构建自动化）。
> - trace 合同：`.trellis/spec/harness/implementation/implementation-trace-contract.md`。
> - 七类详细 doc_type：v1 已提供 L2 文件 `detail-type-viewmodel.md` / `detail-type-usecase.md` / `detail-type-repository.md`；`domain-model` / `view` / `coordinator` / `external` 四类为 `l2_status: pending`，按本文件 §2 合同八问展开，full 链须 L2 豁免。

---

## 0. 本标准包定位与边界

适用：
- iOS 原生实现阶段的可编码合同定义、代码编写执行依据、实现审核依据。
- 从已审核详细设计单元（`UNIT-<slug>`）到 Swift 代码的承接、`implement.md` trace 主文档、实现 Gate 判定、存量豁免口径。

不适用：
- 详细设计正文生成、需求 / 概要 / 详细设计审核（各有对应阶段 SSOT）。
- golden-path 与 project-conventions 槽位本体的重定义——本文件只引用，不复制其规则正文。

中立性约束：
- 本标准包**不执行**代码修改，也**不输出**审核 Findings。它定义"代码编写"与"实现审核"共同遵守的合同与判定口径。
- golden-path 的硬规则（FactoryKit DI、DDD 分层依赖律、Repository 模式、`enum Error` 分层、WCDBSwift 持久化、`ObservableObject + @Published` ViewModel、`private extension`、Coordinator 导航）在本文件中是**锁定前提（不可豁免）**；project-conventions 的槽位（UI 框架收敛 / 网络层 / 日志 / JSON 修复 / 测试框架 / i18n / 主题 / mock 生成 / 构建自动化）是**可按项目调整的取值**，实现时读 `project-conventions.md` 当前值，不在本文件硬编码。

### 0.1 Active packet 与验证路由

- Full/high active worker 必须消费 current packet 与 `implement.md` 已确认的 minimum commit-stable planning audit；它们是不可变 dispatch input。
- Full/high ordinary 只写 packet `target_paths`，只运行 packet `deterministic_checks` 与 planning audit focused checks；不得按 UNIT、layer、`doc_type`、ViewModel、UseCase、View、component、symbol 或 hunk 重新切片或转移 ownership。
- Workspace-wide `xcodebuild` / SwiftLint / full regression 只由唯一 Integration 执行；Integration 实际写范围限 exact `integration_owned_paths`。
- Small、Micro、Lite、non-Full 与 v1 保留本标准原有验证合同。下文的 workspace 命令均按此路由解释，不得覆盖 Full/high ordinary 的 packet 边界。

### 0.2 iOS 详细设计 doc_type 权威七类（全程唯一，禁止改名 / 增减 / 换数）

| doc_type | 含义 | owner 层 | 落地锚点（story-verse-mac 实测路径） |
|----------|------|----------|-------------------------------------|
| `viewmodel` | UI 层 `ObservableObject + @Published` 状态容器 | UI | `UI/Features/<Feature>/ViewModels/XxxViewModel.swift` |
| `usecase` | Domain 业务编排（零 UI 依赖） | Domain | `App/UseCases/<Feature>/XxxUseCase.swift`（接口 `IXxxUseCase`） |
| `repository` | Domain `IXxxRepository` 接口 + Infrastructure 实现（合并一类） | Domain（接口）/ Infrastructure（实现） | `Domain/Repositories/IXxxRepository.swift` + `Infrastructure/Persistence/Repositories/XxxRepository.swift` |
| `domain-model` | Domain 实体 / 值对象 / `enum Error` / 不变量（零依赖、可被任意层导入） | Domain | `Domain/Entities/`、`Domain/ValueObjects/`、`Domain/Errors/`、`Domain/Enums/` |
| `view` | UI 层 SwiftUI View（只展示 + 输入，无业务） | UI | `UI/Features/<Feature>/Views/XxxView.swift`、`Shared/Components/` |
| `coordinator` | App 层 `AppCoordinator` 导航 + FactoryKit DI 装配 | App | `App/Coordinators/AppCoordinator.swift`、`App/DependencyInjection/Container+*.swift` |
| `external` | Infrastructure 外部集成（网络 / SDK / WCDBSwift 持久化 / 第三方） | Infrastructure | `Infrastructure/Persistence/`、`Infrastructure/Services/`、`Infrastructure/Adapters/` |

> 七类名是**全程唯一硬约束**：详细设计、概要承接索引、`implement.md` 合同追踪表、Gate 判定全部只用这七个 token，不得自创 `transport-handler` / `service` / `datasource` / `controller` 之类。`usecase` 即 Domain 业务编排，不要写成 Go 的 `service`；`viewmodel` 即 UI 状态容器，不要写成 flutter 的 `controller`。

---

## 1. golden-path 锁定前提（不可豁免）

下列规则来自 `.trellis/spec/guides/golden-path.md`，是 iOS 原生的 golden-path 锁定项。实现阶段**任何切片**都不得违反，也不得在 `implement.md` 用"存量豁免"绕过；触碰即 Gate `fail`。

### LOCK-1 DDD 四层分层依赖律（严格单向、Domain 零依赖）

- 方向固定：`Domain → App → Infrastructure → UI`，单向，无循环、无反向、无横向跨层。
- `Domain` 是最底层纯类型（实体 / 值对象 / `enum Error` / `IXxxRepository` 接口 / `IXxxUseCase` 接口），**零依赖**：不 `import` SwiftUI / Combine / RxSwift / WCDBSwift / FactoryKit / UIKit / AppKit，可被任意层导入。
- `App`（`usecase` 实现 / `coordinator`）依赖 `Domain`；`Infrastructure`（`repository` 实现 / `external`）依赖 `Domain`；`UI`（`viewmodel` / `view`）依赖 `App` 与 `Domain`。
- 严禁：`View` 间直接导航（必须走 `coordinator`）；`View` 直接访问持久化（必须走 `repository`）；`usecase` 持有 `viewmodel` / `view` / SwiftUI 类型；`Domain` 接口体 `import` 任何框架。
- 好例子（story-verse-mac `Domain/Repositories/IStoryRepository.swift`）：`protocol IStoryRepository: IObservableRepository { func save(story: Story) async throws; ... }`——接口在 Domain，零框架导入。
- 好例子（`App/UseCases/StoryManagement/StoryManagementUseCase.swift`）：`usecase` 构造函数只接收 `IStoryRepository` 等 Domain 接口，零 UI 依赖。
- 坏例子：`HomeViewModel` 里 `import WCDBSwift` 直接 `database.getTable(...)` 查库——`View`/`viewmodel` 越层直访持久化，绕过 `repository`，触碰 LOCK-1，Gate `fail`。
- 坏例子：`Domain/Entities/Story.swift` 顶部 `import SwiftUI`——Domain 不再零依赖，触碰 LOCK-1，Gate `fail`。

### LOCK-2 FactoryKit `@Injected` DI（禁手动初始化业务依赖）

- 依赖装配集中在 `App/DependencyInjection/Container+*.swift`，每个依赖一个 `Factory<Type>` 闭包；跨实例共享用 `.singleton`。
- 消费方（`viewmodel` / `usecase` / `coordinator`）通过 `@Injected(\.xxx)` 注入，**禁**在业务对象内部 `XxxRepository(databaseManager: ...)` 或 `XxxUseCase(...)` 手动 `init` 拼真实依赖。
- 接口型依赖在 `Factory` 中以协议存在类型暴露（`Factory<any IXxxRepository>` / `Factory<IXxxUseCase>`），实现类只在 `Container+*` 闭包里出现一次。
- 好例子（story-verse-mac `Container+UseCases.swift`）：

  ```swift
  var storyRepository: Factory<any IStoryRepository> {
      self { StoryRepository(databaseManager: self.enhancedDatabaseManager()) }
          .singleton
  }
  var storyManageUseCase: Factory<IStoryManagementUseCase> {
      self {
          StoryManagementUseCase(
              storyRepository: self.storyRepository(),
              systemStoriesInitializer: self.systemStoriesInitializer()
          )
      }
      .singleton
  }
  ```

- 好例子（`HomeViewModel.swift`）：`@Injected(\.storyManageUseCase) var storyManageUseCase`——`viewmodel` 不手搓 use case。
- 坏例子：`HomeViewModel` 的 `init` 里 `self.useCase = StoryManagementUseCase(storyRepository: StoryRepository(databaseManager: EnhancedDatabaseManager()))`——手动初始化业务依赖链，绕过 FactoryKit，触碰 LOCK-2，Gate `fail`。
- 不适用：纯 UI 内部状态、`@State`、SwiftUI 环境对象、值类型的就地构造、`enum` / `struct` 字面量不算"业务依赖手动初始化"。

### LOCK-3 Repository 模式强制（接口在 Domain，实现在 Infrastructure）

- 数据访问只经 `repository`：`Domain/Repositories/IXxxRepository.swift` 声明接口（异步 `async throws`），`Infrastructure/Persistence/Repositories/XxxRepository.swift` 持有 WCDBSwift / 网络落地。
- `usecase` 只依赖 `IXxxRepository` 接口，不依赖具体实现；`viewmodel` 只依赖 `usecase`（或必要时 `IXxxRepository`），不直接 `import WCDBSwift`。
- repository 方法返回 Domain 实体 / 值对象，不向上层泄漏 WCDB `Table` / `TableCodable` / `WCDBExpression` 等持久化类型。
- 好例子（story-verse-mac `StoryRepository`）：`final class StoryRepository: ObservableRepository<Story, StoryObject>, IStoryRepository`——接口实现 + `entityToObject` / `objectToEntity` 在边界做转换，向上只露 `Story`。
- 坏例子：`viewmodel` / `usecase` 直接 `let table = database.getTable(named: ..., of: StoryObject.self)`——绕过 repository 接口，触碰 LOCK-3，Gate `fail`。
- 坏例子：`IStoryRepository.fetch()` 返回 `StoryObject`（WCDB 行对象）而非 `Story`——持久化类型泄漏到 Domain 接口，触碰 LOCK-3，Gate `fail`。

### LOCK-4 `enum Error` 分层定义（按 domain 收敛，禁裸字符串错误）

- 每个 domain / 持久化边界定义自己的 `enum XxxError: Error`，关联值带原因（`case validationFailed(reason: String)` / `case notFound`）；需要测试比较时实现 `Equatable`。
- 上层用 `do/catch` + `switch` 模式匹配按语义分流，不靠 `error.localizedDescription` 字符串比较判定。
- repository 把底层 WCDB / IO 错误收敛为本层 `enum`（如 `PersistenceError.notFound` / `.uniqueConstraintFailed(field:)`）；`usecase` 用领域 `enum`（如 `StoryError.validationFailed(reason:)`）表达业务失败。
- 好例子（story-verse-mac `Domain/Errors/StoryError.swift`）：`enum StoryError: Error, Equatable { case validationFailed(reason: String); case chapterNotFound(id: String); ... }`。
- 好例子（`StoryRepository.swift` 内 `PersistenceError`）：`case saveFailed(reason:)` / `case notFound` / `case uniqueConstraintFailed(field:)`——持久化错误收敛为本层 `enum`。
- 坏例子：`usecase` 里 `throw NSError(domain: "story", code: -1)` 或 `throw GenericError("bad")` 裸字符串，上层 `if error.localizedDescription == "bad"` 比较——触碰 LOCK-4，Gate `fail`。

### LOCK-5 WCDBSwift 持久化（禁 CoreData / SwiftData）

- 本地持久化只用 WCDBSwift（`Database` / `Table` / `TableCodable`），数据库生命周期集中在 `Infrastructure/Persistence/`（`DatabaseManager` / `EnhancedDatabaseManager`）。
- **禁用** CoreData（`NSManagedObject` / `NSPersistentContainer`）、SwiftData（`@Model` / `ModelContainer`）、裸 `sqlite3` C API、`UserDefaults` 当主存储。
- WCDB 表对象（`XxxObject: TableCodable`）落 `Infrastructure/Persistence/Models|Entities/`，只在 repository 实现内出现，不上浮到 Domain / App / UI。
- 好例子（story-verse-mac `DatabaseManager.swift`）：`import WCDBSwift` → `let database: Database = Database(at: dbPath)`；表对象 `StoryObject` 经 `StoryObject.from(story:)` / `object.toStory()` 双向转换。
- 坏例子：新切片 `import CoreData` 建 `NSManagedObjectModel`，或用 `@Model class Story`（SwiftData）——触碰 LOCK-5，Gate `fail`（即便 story-verse-mac 存量某处违例，新增代码不可豁免）。

### LOCK-6 ViewModel = `ObservableObject + @Published`；导航走 Coordinator

- `viewmodel` 是 `class XxxViewModel: ObservableObject`，对外可变状态用 `@Published`；异步用 `Task { ... }` + `await MainActor.run { ... }` 回主线程更新 `@Published`。
- `viewmodel` 不持有 `View`，不做导航跳转；跨页导航统一经 `coordinator`（`AppCoordinator` 的 `navigateToXxx()` 改 `@Published var activeDestination`）。
- `view` 只展示 + 收输入 + 调 `viewmodel` 方法 / `coordinator` 导航方法，无业务判定、无持久化、无网络。
- 好例子（story-verse-mac `HomeViewModel.swift`）：`class HomeViewModel: ObservableObject { @Published var recentStories: [Story] = []; ... loadStorys() { Task { ... await MainActor.run { recentStories = ... } } } }`。
- 好例子（`AppCoordinator.swift`）：`@Published var activeDestination: NavigationDestination?`，`func navigateToStoryDetail(storyId:) { activeStoryId = storyId; activeDestination = .storyDetail }`。
- 坏例子：`viewmodel` 用 `@State` / 直接 `NavigationLink` 跳转，或一个 View 里 `self.present(OtherView())` 直接打开另一个 View——绕过 coordinator，触碰 LOCK-6，Gate `fail`。

### LOCK-7 `private` 方法落 `private extension`（代码组织硬约定）

- 所有 `private` 方法落 `private extension XxxType`，按功能用 `// MARK: - Private Methods - <分组>` 分组，不与 `public`/`internal` 成员混合声明。
- `viewmodel` / `usecase` / `repository` 实现的私有 helper（校验 / 解析 / 重试 / 转换）按分组进 `private extension`。
- 好例子（story-verse-mac `Swift_代码组织规范.md` 与 `LLMUseCase`）：主体类只放 `Dependencies` / `init` / Public Methods，`generateStoryWithRetry` / `validateGenerateStoryInput` 进 `// MARK: - Private Methods - Story Generation` 的 `private extension`。
- 坏例子：`func fetchUser()`（public）后紧跟 `private func validate()` 夹在 public 方法之间——触碰 LOCK-7，Gate `fail`。
- 不适用（按 `Swift_代码组织规范.md` 例外）：只有 1~2 个 private 方法的极简类、协议扩展、测试类、自动生成代码可放宽，但需在 `implement.md` 显式声明。

> 不适用场景：纯展示性 SwiftUI Preview、一次性脚本工具、纯静态常量文件不强制 LOCK-2/LOCK-3 的 DI/Repository 链，但仍需 LOCK-1（分层方向）与 LOCK-4（错误语义，如有抛错）；并在 `implement.md` 计划节显式声明"非分层资产"理由。

---

## 2. 可编码合同（承接判定 · 合同八问）

实现阶段的输入是**已审核通过的详细设计单元**（`UNIT-<slug>`）。一个详细设计单元"可编码"当且仅当下列八项合同齐全且无歧义；任一缺失则该切片置 `blocked`，回退详细阶段修订（见 §7），不得在代码里临时补设计。

合同八项（对齐详细 Gate 的合同八问，逐项必须能落到 Swift 代码锚点；按七类 doc_type 区分锚点）：

| # | 合同项 | 可编码判据（落到 Swift 锚点，按 doc_type） |
|---|--------|---------------------------------------------|
| 1 | 承接行为 | 该单元承接哪些 `BHV-NNN`；prd 无此编号即幽灵引用，`blocked` |
| 2 | 接口签名 | `usecase`：`IXxxUseCase` 协议方法（`func execute(command:) async throws -> X`）；`repository`：`IXxxRepository` 协议方法（`async throws`）；`viewmodel`：`@Published` 状态 + Public 方法签名；`coordinator`：`navigateToXxx(...)`；可直接落地 |
| 3 | 字段与结构 | `domain-model`：实体 / 值对象字段、`Codable`、`enum`（含关联值）、不变量；`viewmodel`：`@Published` 属性类型与初值；`external`：WCDB `XxxObject` 列与 `TableCodable` 映射；可直接定义 |
| 4 | 执行流程 | 每步骤可落到方法调用、`@Published` 赋值、`switch` 分支、`Task`/`await` 块、`do/catch` 或抛错（不允许"执行业务逻辑"式大方法占位） |
| 5 | 失败收口 | 每类失败映射到分层 `enum Error`（`StoryError` / `PersistenceError` / `VoiceConfigurationError` 等）与上层 `do/catch switch` 分流（含 UI 反馈如 `ToastManager`） |
| 6 | 依赖边界 | `direct_dependencies[]` 每项映射到 `@Injected(\.xxx)` 字段 + `Container+*.swift` 的 `Factory` 装配点；无下层缺口；方向符合 LOCK-1 |
| 7 | 测试映射 | 既有验证命令落点（`xcodebuild test` / `swift test`）；或 §6 allowlist 允许的纯函数 / Codable / 解析策略最小单测目标 |
| 8 | 不得补造声明 | 该单元未授权的字段 / `enum case` / 导航目的地 / `Factory` / 依赖 / 持久化表，实现期不补造 |

可验证信号：
- `implement.md` 的合同追踪表中，每个 `UNIT-<slug>` 都能回指上述八项的代码锚点或 `blocked` 依据，并标注其 doc_type（七类之一）。
- 每个执行流程步骤都有预期代码落点；每个 `direct_dependencies[]` 行都能映射到 `@Injected` 字段 → `Container` 的 `Factory` → `.singleton`/瞬态 装配。
- pending 四类（`domain-model` / `view` / `coordinator` / `external`）无 L2 详细文件时，按本节合同八问展开即可承接；若详细设计声明 full 链（需逐字段 / 逐导航目的地展开），必须有 L2 豁免记录，否则 `blocked`。

约束边界：
- 不从代码、习惯或参考工程反推需求；不猜测、发明、补全详细设计未定义的契约 / 字段 / `enum case` / 导航目的地 / `Factory` / 持久化表。
- 不把详细设计的行为步骤合并、改序、上移、下沉或省略，除非详细设计本身给出依据。
- 不为编译通过新增 fake、`InMemoryXxxRepository`、optional path、占位结果、硬编码依赖（story-verse-mac 已存在 `InMemoryStoryRepository`，属测试 / 存量资产，不得作为本次生产路径替身）。

---

## 3. 实现顺序（依赖方向自底向上）

代码阶段唯一执行顺序。先实现被依赖层，再实现调用层；上层不得用 fake / 占位 / 内存 store / hardcoded 依赖绕过下层缺口。横切的 `coordinator`（DI 装配 + 导航）与 `external`（持久化 / SDK）随被依赖项就位时补齐。

```text
Phase 0  设计合同解析 + implement.md 计划                  （不写生产代码）
Phase 1  domain-model：实体 / 值对象 / enum Error / 不变量（Domain 零依赖）
Phase 2  repository：IXxxRepository 接口（Domain）+ Infrastructure 实现 + external 持久化/SDK
Phase 3  usecase：IXxxUseCase 接口 + App 层业务编排（零 UI 依赖）
Phase 4  viewmodel：ObservableObject + @Published 状态容器 + @Injected 注入
Phase 5  view + coordinator：SwiftUI View（只展示+输入）+ AppCoordinator 导航 + Container 装配
Phase 6  验证与符合性审查：xcodebuild build/test + SwiftLint + 证据回填
```

阶段共同规则：
- Phase 0 在 detail 确认前创建或更新 `implement.md` 计划合同；detail 确认后 `implement.md` 不再作为执行状态写入点。
- Phase 1~6 的切片状态、改动文件、偏差、阶段自检和恢复条件追加到 `implementation-evidence.jsonl`；验证命令和测试名级证据追加到 `verification-evidence.jsonl`。
- Phase 0 未通过不得写生产代码；Phase 1~5 只能按依赖方向推进；发现下层合同缺失，当前生产路径必须 `blocked`，不得用 `InMemory*` / 假数据顶上。
- `coordinator`（DI 装配片）可在每个 Phase 增量补：domain-model 无 `Factory`；repository / usecase / viewmodel 落地时同步在 `Container+*.swift` 补对应 `Factory`，避免悬空 `@Injected`。

各 Phase 的产物合同与出入口条件见 §4。

---

## 4. 各 Phase 产物合同与出入口

### Phase 0 — 设计合同解析（不写生产代码）

输入：概要承接索引（`chapter_target → doc_type`，doc_type 必属七类之一）、目标详细设计单元、`golden-path.md`、`project-conventions.md`、现有代码骨架（`StoryVerse/StoryVerse/` 四层）。

代码前硬门禁：
- 必须先创建或更新 `implement.md` 的计划节；小迭代可缩小范围，但不得跳过计划，也不得"先写代码再补 trace"。
- 完成 `UNIT-<slug> → 代码资产`（含 doc_type → 落地目录）映射；识别 LOCK 锁定面与 Secret/Credential 检查面；为每个切片写明 `checkpoint` 与 `validation_commands`。
- pending 四类若详细设计标 full 链，确认 L2 豁免记录是否存在；缺失则该切片 `blocked`。

出口条件：
- 每个目标单元都有合同追踪行与资产映射行（标 doc_type）；每个执行流程步骤都有预期代码落点；无未解释的设计缺口（有则 `blocked`）。

失败判定：`chapter_target → doc_type` 映射缺失或 doc_type 不属七类；执行流程步骤无法落到代码目标；`direct_dependencies[]` 无法形成 `@Injected → Factory` 闭环；缺 `implement.md` 计划节。

### Phase 1 — domain-model（最底层纯类型，Domain 零依赖）

产物合同：
- 实体（`struct`/`class` + `Codable`/`Identifiable`/`Equatable` 按需）、值对象、`enum`（含关联值）、不变量校验入口；落 `Domain/Entities|ValueObjects|Enums`。
- 每个 domain 的 `enum XxxError: Error` 落 `Domain/Errors/`，关联值带原因；需测试比较时实现 `Equatable`（LOCK-4）。
- 顶部**不 `import`** SwiftUI / Combine / RxSwift / WCDBSwift / FactoryKit / UIKit / AppKit（LOCK-1）。
- 好例子（story-verse-mac `Domain/Errors/StoryError.swift`）：`enum StoryError: Error, Equatable { case validationFailed(reason: String); case chapterNotFound(id: String); ... }`，仅 `import Foundation`。
- 坏例子：`Domain/Entities/Story.swift` 里 `import WCDBSwift` 直接 `: TableCodable`——把持久化类型混进 Domain 实体，触碰 LOCK-1 / LOCK-5。

出口条件：所有承接单元的字段、可空语义、`enum case`、不变量、`enum Error` 落地；`Domain/` 仅 `import Foundation`；编译通过。

失败判定：Domain 类型 `import` 框架；实体直接是 WCDB 表对象；裸字符串错误代替 `enum Error`。

### Phase 2 — repository（接口在 Domain + 实现在 Infrastructure + external）

产物合同：
- 接口 `protocol IXxxRepository`（`async throws`，返回 Domain 实体）落 `Domain/Repositories/`；实现 `final class XxxRepository: ... , IXxxRepository` 落 `Infrastructure/Persistence/Repositories/`。
- 实现持有 `EnhancedDatabaseManager` / WCDB `Table`；实体 ↔ WCDB 表对象转换在边界 helper（`XxxObject.from(entity:)` / `object.toEntity()`），向上只露 Domain 类型（LOCK-3）。
- 底层 WCDB / IO 错误收敛为本层 `enum`（`PersistenceError.notFound` / `.saveFailed(reason:)` / `.uniqueConstraintFailed(field:)`）（LOCK-4）。
- `external`（网络 / SDK / 第三方适配）落 `Infrastructure/Services|Adapters/`，同样以 Domain 接口（`IXxxAdapter` / `IXxxService`）对上，实现细节内聚。
- 私有转换 / 校验 helper 进 `private extension`（LOCK-7）。
- 好例子（story-verse-mac `StoryRepository.swift`）：`final class StoryRepository: ObservableRepository<Story, StoryObject>, IStoryRepository`，`override func entityToObject(_:) -> StoryObject` / `objectToEntity(_:) -> Story` 在边界转换。
- 坏例子：repository 方法返回 `StoryObject`，或 repository 内 `if story.status != .published { throw ForbiddenError }` 把业务判定下沉到 repo——触碰 LOCK-3。

出口条件：每个承接单元的读写路径落地；WCDB 表对象不上浮；`PersistenceError` 收敛正确；对应 `Factory<any IXxxRepository>` 在 `Container+*.swift` 注册（LOCK-2）；编译通过。

失败判定：repository 含业务状态机；用 `InMemoryXxxRepository` / 内存数组代替 WCDB；CoreData/SwiftData 落地（LOCK-5）；接口泄漏持久化类型；底层错误裸透出未收敛。

### Phase 3 — usecase（Domain 业务编排，零 UI 依赖）

产物合同：
- 接口 `protocol IXxxUseCase` + 实现 `class XxxUseCase: IXxxUseCase`，落 `App/UseCases/<Feature>/`；依赖通过构造函数接收 `IXxxRepository` / `IXxxAdapter` 等 Domain 接口。
- 业务校验、状态机、跨 repository / adapter 编排、重试落在 use case 方法或 `private extension` helper；失败抛领域 `enum Error`（`StoryError.validationFailed(reason:)`）（LOCK-4）。
- **零 UI 依赖**：不 `import` SwiftUI / 不持有 `viewmodel` / `view`；不读 UI 状态（LOCK-1）。
- 执行流程每步骤可定位：校验 → repository 调用 → adapter 联动（如 `llmAdapter.generate` / `ttsAdapter`）→ 返回 Domain 类型。
- 好例子（story-verse-mac `LLMUseCase`，`Swift_代码组织规范.md` 示例）：`generateStory` → `generateStoryWithRetry`，私有方法 `validateGenerateStoryInput` / `createStory` / `shouldRetryForError` 分组进 `private extension`，依赖 `IAIModelRepository` / `IOnDeviceLLMAdapter` / `IStoryRepository` 经构造函数注入。
- 坏例子：`func execute()` 内 200 行 `// 处理业务逻辑` 不拆步骤，或 use case `import SwiftUI` 调 `@Published`——触碰合同八项之 4 / LOCK-1。

出口条件：执行流程每步骤定位到代码；持久化 / 幂等 / 错误语义与设计一致；对应 `Factory<IXxxUseCase>` 在 `Container+UseCases.swift` 注册；编译 + 既有 use case 单测通过。

失败判定：use case `import` UI 框架 / 持有 viewmodel；用 fake repository 绕过下层缺口；校验语义弱化；大方法吞步骤；私有方法不进 `private extension`（LOCK-7）。

### Phase 4 — viewmodel（`ObservableObject + @Published` 状态容器）

产物合同：
- `class XxxViewModel: ObservableObject`，对外可变状态用 `@Published`；依赖用 `@Injected(\.xxx)`（LOCK-2），不手动 `init` 业务依赖。
- 异步交互用 `Task { do { ... } catch { ... } }`，更新 `@Published` 时 `await MainActor.run { ... }` 回主线程；失败按 `enum Error` 分流并触发 UI 反馈（`ToastManager` 等，取值见 `project-conventions.md`）。
- `viewmodel` 不持有 / 不创建 `View`，不做导航（导航交 `coordinator`）（LOCK-6）。
- 私有 helper 进 `private extension`（LOCK-7）。
- 好例子（story-verse-mac `HomeViewModel.swift`）：`@Published var recentStories: [Story]`，`@Injected(\.storyManageUseCase) var storyManageUseCase`，`loadStorys()` 内 `Task { let storys = try await storyManageUseCase.fetchAllFullStories(); await MainActor.run { recentStories = ... } }`。
- 坏例子：`viewmodel` 的 `init` 里 `StoryManagementUseCase(storyRepository: StoryRepository(...))` 手搓依赖链，或在 `@Published` 更新不回主线程——触碰 LOCK-2 / 并发约定。

出口条件：`@Published` 状态与 Public 方法签名与设计一致；依赖全部 `@Injected`；主线程更新正确；`Factory<XxxViewModel>` 在 `Container+ViewModels.swift` 注册（`@MainActor` 按需）；编译通过。

失败判定：用 `@State`/`@StateObject` 替 `@Published` 做对外状态；手动初始化业务依赖；viewmodel 内做导航 / 直访 repository-WCDB；私有方法不进 `private extension`。

### Phase 5 — view + coordinator（SwiftUI 展示 + 导航 + 装配）

产物合同（`view`）：
- `struct XxxView: View`，只展示 + 收输入 + 调 `viewmodel` 方法 / `coordinator` 导航；无业务判定、无持久化、无网络。
- 文案走 i18n（`Localizable.strings`，取值见 `project-conventions.md`），不硬编码用户可见字符串；主题走 `ThemeManager`。
- 遗留 RxSwift 视图在触碰范围内**收敛**为纯 SwiftUI（UI 框架槽位目标值），不新增 RxSwift 绑定（取值见 `project-conventions.md`）。

产物合同（`coordinator`）：
- 导航集中在 `AppCoordinator`：新增目的地进 `enum NavigationDestination`，配 `navigateToXxx(...)` 改 `@Published var activeDestination`（LOCK-6）。
- DI 装配补齐：本切片新增的 repository / usecase / viewmodel 对应 `Factory` 在 `Container+*.swift` 注册，消除悬空 `@Injected`（LOCK-2）。
- 好例子（story-verse-mac `AppCoordinator.swift`）：`enum NavigationDestination: Equatable { case storyCreation; case storyDetail; ... }`，`func navigateToStoryDetail(storyId:) { activeStoryId = storyId; activeDestination = .storyDetail }`。
- 坏例子：`View` 里 `NavigationLink(destination: OtherView())` 直接跳转、或 `view` 内 `try await repository.save(...)` 直访持久化——触碰 LOCK-6 / LOCK-3。

出口条件：入口行为每步骤有代码落点；`view` 不直访 repository/WCDB/网络；导航走 coordinator；DI 装配无悬空 `@Injected`；编译通过。

失败判定：`View` 间直接导航；`view` 承载业务 / 持久化；硬编码用户可见文案；新增 RxSwift 绑定（违 UI 框架收敛槽位）；新增 `Factory` 缺失致 `@Injected` 解析崩溃。

### Phase 6 — 验证与符合性审查

见 §5（实现 Gate）。

---

## 5. 实现 Gate（xcodebuild build/test + SwiftLint + 证据）

实现 Gate 是"证据感，不是做完感"。Full/high ordinary 运行 packet-declared deterministic/focused checks；Integration 运行一次下表 workspace 命令。Small、Micro、Lite、non-Full 与 v1 继续按下表既有命令。命令与结果追加到 `verification-evidence.jsonl`；implementation review verdict 进入 `review-records/implementation-reviews.jsonl`。

### 5.1 路由解析后的必跑验证命令

| 类型 | 命令（story-verse-mac 用 `.xcworkspace`；纯 SPM 模块用 `swift`） | 通过判据 |
|------|------------------------------------------------------------------|---------|
| Full/high ordinary | packet `deterministic_checks` + planning audit focused checks | 全部通过；不得扩成 workspace-wide 命令 |
| Integration / non-Full / v1 编译 | `xcodebuild build -workspace StoryVerse.xcworkspace -scheme StoryVerse -destination 'platform=macOS'`（或 `swift build`） | 退出码 0，无编译错误 |
| Integration / non-Full / v1 测试 | `xcodebuild test -workspace StoryVerse.xcworkspace -scheme StoryVerse -destination 'platform=macOS'`（或 `swift test`） | 退出码 0；记录受影响 target 的测试名 |
| Integration / non-Full / v1 lint | `swiftlint` | 退出码 0，无新增告警 |
| Integration / non-Full / v1 静态/告警 | 构建告警清零（`-quiet` 下无 warning 残留）；并发安全（`@MainActor` / `await MainActor.run` 路径正确） | 无新增 warning |
| Integration / non-Full / v1 启动/冒烟 | 最小真实启动 / 关键 feature 冒烟（如 Home 加载故事列表）或真机 / 模拟器手测 | 行为符合预期 |
| Integration / non-Full / v1 Secret 残留 | 检查代码 / `Info.plist` / `xcconfig` / fixture / `implement.md` / mutable evidence 无明文 secret（注意 `DatabaseManager` 的加密 key 走配置而非硬编码） | 仅出现引用 / env 名，无真实 key/token/password |

`verification-evidence.jsonl` 要求：
- 每个切片对应"命令 + 结果"；测试写到测试名级别（如 `StoryRepositoryTests.testSaveAndFetch` 通过 / `ManageAIModelsUseCaseTests.*`）。
- 无法本地验证项（真机表现、外部 SDK 联调、模型下载）显式列出，标注留给哪个环节（Manual QA / 真机 / 远程冒烟）。

### 5.2 Gate 结构判定（guru_gate.py 结构底线）

实现 Gate 结构检查（`guru_gate.py implement`）要求 `implement.md` 计划合同与 mutable evidence 齐全，且**切片挂 UNIT**：

- 计划节（含"计划"或"切片"）
- 执行节（含"执行"或"改动文件"）
- `verification-evidence.jsonl`（含"证据"或 analyze/test）
- 阻塞与偏差节（含"阻塞"或"偏差"）
- 若存在 `UNIT-<slug>`，trace 中必须出现 `UNIT-` 引用（裸编号 token，兼容未来双链包裹）。

下游引用一律写**裸编号 token**：行为写 `BHV-001`，设计单元写 `UNIT-story-management-usecase`；doc_type 写七类名之一；不重排、不复用、删除留洞。

### 5.3 Gate 语义判定（实现审核口径）

`pass` / `fail` / `blocked` 三态，语义判定由实现审核（人工 Gate）逐条核：

- `pass`：先按当前 route 解析验证闭合条件，再检查共同条件。Full/high ordinary 只要求 singular current packet 为 `verified`，且 current packet/audit 选中的 focused checks 成功，不等待或检查 sibling packets；Integration 要求完整依赖 packet set 均有 current receipt，并完成 Integration-selected checks；non-Full/v1 保留原合同，所有计划设计单元 slices 为 `verified` 或明确 `skipped_with_reason`、无悬空 `in_progress`、无被当成完成交付的未验证 `implemented`，且 legacy checks 通过。三路都必须满足 LOCK-1~7、合同八项无偏离，并在当前 route 要求时通过 Secret 检查。
- `fail`：存在合同未实现 / 实现偏离；无 plan 先行证据却已写生产代码；计划已 `blocked` 但代码绕过继续；`implemented` 未验证却交付为完成；触碰任一 LOCK 锁定项；明文 secret 写入配置/代码/fixture；fake / 占位 / `InMemory*` store 作生产路径；新增测试超出 §6 allowlist；测试补写业务语义；自创非七类 doc_type。
- `blocked`：详细设计缺失 / 冲突 / 需确认（含 pending 四类 full 链无 L2 豁免）且已按 §7 记录并回退，未写临时代码绕过；或环境 / 凭据 / 真机 / 模型缺失导致验证无法继续，保留恢复条件。

逐条核查清单：
1. `implement.md` 存在且计划合同齐全，能恢复实现范围、计划状态、设计锚点（含 doc_type）；代码落点、阶段自检、验证状态、阻塞原因可由 `implement.md` 字段合同与 mutable evidence 合并恢复。
2. 每个切片挂 `UNIT-<slug>` 并标 doc_type（七类之一），无幽灵引用（prd 无此 `BHV`）、无自创类型名。
3. 代码有 plan 先行证据；计划 `blocked` 但代码继续绕过 → 不得 `pass`。
4. 合同八项每项有代码锚点或 `blocked` 依据；执行流程每步骤有落点。
5. LOCK-1~7 全部满足（分层单向 / FactoryKit DI / Repository 模式 / `enum Error` 分层 / WCDBSwift / ViewModel+Coordinator / `private extension`）。
6. 错误 / 持久化 / 幂等 / 导航 / 并发（`@MainActor`）/ i18n 语义未弱化。
7. 生产路径无 fake / 占位 / 硬编码结果 / `InMemory*` 模拟 / CoreData / SwiftData。
8. 默认只跑既有验证命令；新增测试仅限 §6 allowlist 并回指切片与 `test_target`。
9. Secret 合同闭合：代码 / `Info.plist` / `xcconfig` / fixture / trace / mutable evidence 无 secret value。
10. `view` 不直访 repository/WCDB；`usecase` 不 `import` UI；`repository` 无业务判定 / 不泄漏 WCDB 表对象；`viewmodel` 全 `@Injected`。

---

## 6. 实现期测试边界

- 默认只运行既有验证命令（§5.1），**不默认新增测试用例**，不采用 TDD / RED-GREEN，不先写测试再反向收敛生产代码。
- 新增测试用例不是详细设计承接来源，也不得牵引代码结构。
- allowlist（唯一允许新增的测试）：**无状态、幂等、输入输出明确的纯函数 / 算法 / 静态技术函数**最小单元测试。例如 story-verse-mac 中可对 `StoryParsingStrategy` 解析纯函数、`AIModelStatus` Codable 编解码、值对象不变量校验补最小单测（对应既有 `StoryParsingStrategyTests` / `AIModelStatusCodingTests`）；新增前必须已有 `implement.md` 计划或 slice packet 的 `test_target`，detail 确认后新增测试证据写入 `verification-evidence.jsonl`。
- 禁止：新增业务流程测试 / 集成测试 / UI 测试（UITests）/ repository-WCDB 落库测试 / 外部 SDK mock-fake 测试来定义业务语义；为测试通过新增 fake repository/adapter、`InMemory*` 模拟、硬编码结果或放宽断言。
- 测试框架取值见 `project-conventions.md`（当前 XCTest，可调 Quick/Nimble）；mock 生成取值见同文件（当前手写，可调 Mockolo）；不在本文件硬编码。
- 不适用场景：详细设计已附带独立测试计划 / 业务验收用例时，按该计划执行属于既有验证，不受 allowlist 限制；detail 确认后的执行结果登记到 `verification-evidence.jsonl`。

---

## 7. 存量豁免口径

实现阶段触碰**存量代码**时按以下口径处理；豁免只针对存量违例，**不豁免** golden-path 锁定项（LOCK-1~7）与本次新增代码。

### 7.1 豁免对象与边界

- 豁免对象：仓库内已存在、不符合当前 golden-path / 合同但在本次切片范围**外**的代码（story-verse-mac 典型：`InMemoryStoryRepository` 测试替身、`DatabaseManager` 与 `EnhancedDatabaseManager` 并存、`Models`/`Common` 早期混层目录、RxSwift 遗留视图、`HomeViewModel` 里被注释掉的旧 `Factory`、`PersistenceError.underlyingError` 的简化 `Equatable`）。
- 不可豁免：LOCK-1~7 锁定项（任何代码都不可违反）；本次切片**新增 / 修改**的代码（必须符合全部合同与 LOCK）。
- 触碰即修 vs 记债：本次切片为完成目标**必须**改动到的存量违例 → 顺手修复并在 mutable evidence 记录；本次切片**不必**改动、改动会扩散影响面的存量违例 → 记债（列出位置 + 原因），不在本次扩大范围（外科手术式改动原则）。

### 7.2 处置记录（写入 mutable evidence）

每条触碰的存量违例记录：
- 违例位置（相对路径 + 符号，如 `Infrastructure/Persistence/Repositories/InMemoryStoryRepository.swift`）。
- 处置：`绕行` / `顺手修复` / `记债`。
- 理由：为什么本次不全量修（影响面 / 范围 / 风险）。
- 若是 LOCK 锁定项被存量违反且落在本次必经路径 → 必须修复（不可记债豁免），因为 LOCK 不可豁免。

### 7.3 Gate 交互

- 存量记债项**不阻塞**本次实现 Gate（已显式记录、不在本次范围）。
- 范围外新增违例（本次切片引入的新违例）**阻塞** Gate（`fail`）。
- 缺陷只能回上游修：审核发现结构性缺陷（归属错、合同越界、doc_type 错用）回到拥有该决策的阶段修订，禁止下游补造。

---

## 8. `implement.md`（trace）主文档合同与 mutable evidence 边界

`implement.md` 是 detail Gate 的 digest-bearing planning/trace contract。建议路径：目标仓库 `docs/design/<feature>/implement.md`（或 `docs/implementation/<module_slug>/implement.md`，呼应 story-verse-mac `docs/implementation/`）。它在 detail 确认前完成并进入 digest；detail 确认后不得作为执行证据默认写入点。实现阶段的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`。若必须修改 `implement.md`，必须回退 detail Gate 并重新 review/confirm。

### 8.1 必含四节（计划合同结构底线）

#### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 切片 | Full/high 读取已确认 planning audit 的真实 `owner_unit`、`covered_units`、文件级 `owned_paths`、完成信号与 focused checks；active worker 不按 UNIT / `doc_type` / ViewModel / UseCase / View 重切。non-Full/v1 保留原有计划合同 |
| 执行顺序 | Full/high 按 audit 的真实 `depends_on` 与 `parallel_wave`；iOS 自底向上顺序只约束代码依赖，不机械生成 slices |
| 风险点 | 预判高风险改动（WCDB schema 变更、跨 feature 共享 use case、`@MainActor` 并发、导航目的地新增、RxSwift→SwiftUI 收敛），逐条写验证手段 |

#### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个切片完成时记录：
- 实际改动文件清单（相对路径，标 doc_type 与所属层）。
- 与计划的偏差（改了计划外文件 / 没改计划内文件 → 必须写原因）。
- DI 装配记录（在哪个 `Container+*.swift` 加了哪个 `Factory`）、导航记录（`NavigationDestination` 是否新增 case）。

#### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

| 类型 | 要求 |
|------|------|
| Full/high ordinary evidence | 只记录 current packet `deterministic_checks` 与 planning audit focused checks；test / startup / Secret 仅在 packet/audit 明确声明时记录，不自行扩展命令 |
| Integration evidence | 记录完整 workspace build / lint / test / startup / Secret / full regression；测试结果到测试名级别，新增测试清单限 §6 allowlist |
| non-Full/v1 evidence | 保留 legacy evidence 合同：编译、lint、测试名级别结果、关键 feature 启动冒烟与 Secret 残留检查 |
| 未验证项 | 无法本地验证的（真机、外部 SDK、模型下载）→ 显式列出 + 留给哪个环节 |

#### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- 上游缺陷：详细设计合同错 / 漏（含 pending 四类 full 链无 L2 豁免）→ 记录后**回退详细阶段修订**，不就地改设计（`implementation-evidence.jsonl` 留回退记录与恢复条件）。
- 存量违例触碰：列出位置 + 处置（绕行 / 顺手修复 / 记债，见 §7）。
- 未决决策：实现中冒出的新决策点（如某 enum case 是否新增、某导航目的地归属）→ 不私自拍板，记录并升级给人工 Gate。

### 8.2 切片状态机

- 固定枚举：`pending` / `in_progress` / `implemented` / `verified` / `blocked` / `skipped_with_reason`。
- 一个 active worker 只推进分配给它的 current packet，不创建或转换 sibling slices；并行宽度由已确认 planning audit 的 `parallel_wave` 决定。
- `implemented` 只表示代码落地；未通过 `checkpoint` 与 `validation_commands` 的切片不得 `verified`。
- `blocked` 必须写明恢复条件与回指（详细设计回修 / L2 豁免 / 凭据 / 真机 / 模型）。
- `skipped_with_reason` 必须说明设计范围 / 用户范围为何不需要；不得用来隐藏未实现的 required 切片。

### 8.3 反模式

- trace 在 PR 前一次性补写（失去过程证据意义）。
- mutable evidence 只写"全部通过"（无命令、无测试名）。
- 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
- 把 `implement.md` 当设计补写位置；detail 确认后又把它当执行证据写入点。

---

## 9. 反模式总表（Gate `fail`）

| # | 反模式 | 违反锁定项 |
|---|--------|-----------|
| 1 | Domain 类型 `import` SwiftUI/Combine/RxSwift/WCDBSwift/FactoryKit/UIKit/AppKit | LOCK-1 |
| 2 | 跨层反向 / 横向依赖；`usecase` 持有 `viewmodel`/`view` 或 `import` UI 框架 | LOCK-1 |
| 3 | `view` / `viewmodel` 直接 `import WCDBSwift` 直访持久化，绕过 `repository` | LOCK-1 / LOCK-3 |
| 4 | 业务对象内手动 `init` 真实依赖链（`XxxUseCase(XxxRepository(...))`），不走 `@Injected` / `Factory` | LOCK-2 |
| 5 | repository 接口返回 WCDB 表对象 / repository 内含业务状态机 | LOCK-3 |
| 6 | 裸字符串错误 / `NSError` + `localizedDescription` 字符串比较，不收敛为分层 `enum Error` | LOCK-4 |
| 7 | 新增代码用 CoreData（`NSManagedObject`）/ SwiftData（`@Model`）/ 裸 sqlite3 替代 WCDBSwift | LOCK-5 |
| 8 | `viewmodel` 用 `@State` 做对外状态 / `@Published` 更新不回主线程 / viewmodel 内做导航 | LOCK-6 |
| 9 | `View` 间直接 `NavigationLink`/`present` 跳转，绕过 `AppCoordinator` | LOCK-6 |
| 10 | `private` 方法夹在 public 方法间，不进 `private extension` | LOCK-7 |
| 11 | 详细设计有执行流程步骤，代码只写"调用下游 / 处理异常 / 执行业务逻辑"式大方法 | 合同八项之 4 |
| 12 | 用 `InMemoryXxxRepository` / 内存数组 / fake adapter / 硬编码结果替代真实 repository/SDK 作生产路径 | 承接合同 |
| 13 | 默认 TDD / 先写测试牵引实现，或新增业务流程 / 集成 / UITests / repository-WCDB / mock-fake 测试定义业务语义 | §6 |
| 14 | 硬编码用户可见文案（不走 `Localizable.strings`）/ 新增 RxSwift 绑定（违 UI 框架收敛槽位） | project-conventions |
| 15 | API key / token / password / 加密 key 写进代码 / `Info.plist` / `xcconfig` / fixture / 日志 / `implement.md` | Secret 合同 |
| 16 | 用"存量豁免"绕过 LOCK 锁定项或本次新增代码的合同 | §7 |
| 17 | 自创非七类 doc_type（`transport-handler` / `service` / `datasource` / `controller`），或照抄 flutter/Go 类型名 | §0.1 七类权威 |
| 18 | trace 在 PR 前补写、mutable evidence 只写"全部通过"、切片不挂 `UNIT-<slug>` / 不标 doc_type | §8 与实现 Gate 结构底线 |
