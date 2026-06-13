# L2 类型规范：usecase（Domain 业务编排）

> 从属于 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；本文件只写 `usecase` 类型相对合同八问骨架的差异规则。
> golden-path 对应：`.trellis/spec/guides/golden-path.md` 的 §2.1 分层依赖律、§2.5 边界、§3 Domain 迷你路径。
> doc_type 七类一律以 IOS_BRIEF 为权威（viewmodel / usecase / repository / domain-model / view / coordinator / external），本文件只展开 `usecase`，禁止照搬 flutter 的 `controller` 或 Go 的 `service` 等异平台类型名。
> 装载路径口径：本规范安装后位于 `.trellis/spec/harness/detail/detail-type-usecase.md`；下游 review/writing 装载亦走该路径。

## 适用对象

`usecase` 是 **Domain 层有状态业务流程编排 + 响应式发射的 owner**。它把"业务规则、状态转移、跨依赖编排"固化为一组协议方法与可观察发射，是 iOS 四层（Domain → App → Infrastructure → UI）里测试密度最高的层。

- **属于 usecase**：跨多个 repository / service 的业务编排；含中间业务状态（进行中、已取消、待重试）的有状态流程；对 UI 暴露的 `AsyncStream` / `@Published` 上游业务事件源。
- **不属于 usecase**：
  - 纯数据访问编排（增删改查、缓存回落、`WCDBSwift` 落库） → 归 `repository`。
  - 实体不变量、值对象、`enum Error` 定义本体 → 归 `domain-model`（usecase 只 *使用* 这些类型，不在自身文件里重定义实体）。
  - UI 状态容器（`ObservableObject` + `@Published`、事件→状态机、加载/错误三态） → 归 `viewmodel`。
  - 外部 SDK / 网络 / 持久化适配实现 → 归 `external` 或 `repository` 实现侧。

> 归属边界硬基准：`usecase` 的 owner 层是 **Domain**，因此**零 UI 依赖、零 Infrastructure 具体类型依赖**。一旦合同里出现 `import SwiftUI` / `import FactoryKit`（DI 装配属 `coordinator`）/ 直接 `import WCDBSwift` / 引用某个具体 `XxxRepository`（实现类）/ 引用 `ViewModel`，即判 P1。

## 合同八问的类型特化

> 通用八问骨架见 L1 §3；下列为 usecase 类型在每一问上的加码与可验证信号。

1. **承接哪些行为**：承接"业务规则与状态变化"类 `BHV-NNN`（裸 token 引用 prd 标题，幽灵引用 / 无承接均被 gate 断链拦截）。每条承接行为映射到协议 `IXxxUseCase` 的**一个公开方法或一条发射流**；一对一，不允许"一个方法笼统承接一堆 BHV"。

2. **输入 / 输出 / 错误结果**：
   - 接口全集**逐方法签名级**列出：方法名 / 参数（含 `async`、`throws`、`@escaping` 闭包、`@MainActor` 标注）/ 返回类型。签名是上限，禁止写方法体实现。
   - 维护的发射流逐条列出：流名 / 元素类型 / seed（订阅瞬间是否回放初始值）/ 发射时机。iOS 主用 `AsyncStream<T>`（新代码）与 `Observable<T>`（RxSwift 遗留，标 legacy）；新设计默认 `AsyncStream`，遗留流必须标注迁移方向。
   - 错误 = **本 domain 的 `enum Error`**（在 `domain-model` 定义，usecase 合同里引用其 case 全集），逐 case 标注语义 + 是否可恢复 + 是上抛给 viewmodel 还是内部降级。

3. **读取 / 写入哪些状态**：列出本 usecase 拥有的**业务状态清单**（唯一写 owner）。声明哪些状态经流对 viewmodel **只读暴露**（viewmodel 订阅、不回写）。线程安全机制必须声明（Swift 并发下推荐用 `actor` 封装可变共享状态——见证据 `StateManager` actor）。同一业务状态出现在两个 usecase 合同里 = P1，回概要重判归属。

4. **调用哪些依赖，不调用哪些依赖**（正反两面都写）：
   - **允许注入**：`repository` 接口（`IXxxRepository`）、`service` 协议（无状态工具，仍走协议）、Infrastructure 能力的**协议抽象**（如 `IFileSystem`、`IApplicationInfoService`、下载器 `IAIModelDownloaderService`）。**单向注入其他 usecase 接口**（`IXxxUseCase`）允许但必须声明方向、禁止环与双向；若依赖其他 usecase，须说明为何不下沉为 service。
   - **禁止调用 / 禁止 import**：任何 `repository` *实现类*、`WCDBSwift` / `DatabaseManager`、`URLSession` / `Moya` 网络栈、SDK 具体类型、`ViewModel`、`View`、`SwiftUI`、`AppCoordinator`、`FactoryKit` `@Injected`（注入由 `coordinator` 在 App 层通过 `Container` 装配，usecase 自身只声明 `init(...)` 构造注入）。
   - 依赖必须经 `init` 构造注入并以**协议类型**持有（如 `private let aiModelRepository: any IAIModelRepository`），禁止 usecase 内部手动 `new` 任何实现（违反 golden-path 锁定的 FactoryKit DI 规则）。

5. **失败如何收口**：每个公开方法逐条失败路径写处置——
   - `throws` 上抛本 domain `enum Error`（映射点必须明确：底层 `XxxAdapterError`/`URLError` 在哪一行转成本域 error，对齐 `[SLOT-04]` 错误收口位置）；
   - 流内失败：发射"失败态元素"还是 `AsyncStream` 自然结束（iOS `AsyncStream<T>` 不携带 error 通道，失败必须建模为元素的 `case failed(message:)`，不可静默吞）；
   - 静默降级：仅限"状态更新失败但主流程可继续"，且必须写明日志（OSLog）。
   逐行异常表须能对应一条失败路径 BHV 或八问 1 的行为分支。

6. **产生哪些事件 / 后置结果**：流发射时序（"什么操作成功 / 失败后，哪些流必然发射、发射什么元素"）；副作用（落库经 repository、文件删除经 `IFileSystem`、埋点）逐条写明消费方；跨 usecase 通知（如有）声明触发条件。

7. **哪些测试验证它**：业务规则与状态转移 = **XCTest unit**（mock repository / service，FactoryKit 注册测试实例或直接构造注入 mock）；流时序 = unit（`expectation` + `for await` 断言发射序列，见证据 `testObserveModelDownloadStatus_*`）。**usecase 是测试密度最高的层**：每条承接行为至少 **1 成功 + 1 失败**用例；每个 `enum Error` case 至少 1 个断言它被抛出的用例。测试框架槽位 `[XCTest → Quick/Nimble]` 以 project-conventions 为准；mock 槽位 `[手写 → Mockolo]`。

8. **哪些内容不得在此补造**：不决定 UI 展示与文案（属 view/viewmodel）；不决定存储介质与缓存策略（属 repository——含是否走 `WCDBSwift`、是否加内存缓存）；不决定实体字段与序列化（属 domain-model / external）；不在未确认的业务规则上拍板（列入未决问题回概要/需求，禁止详细阶段私自定）。

## 类型硬规则（golden-path 锁定，违反直接 fail）

- **R1 协议 + 实现分文件**：协议 `protocol IXxxUseCase` 与实现 `final class XxxUseCase: IXxxUseCase` 分文件（命名按 project-conventions 槽位；证据：`IManageAIModelsUseCase.swift` / `ManageAIModelsUseCase.swift`）。下游所有引用一律面向协议类型。
- **R2 Domain 零 UI / 零具体实现依赖**：usecase 文件 import 集合只允许 `Foundation` + Domain 内部类型 + 注入的协议；出现 `SwiftUI`/`FactoryKit`/`WCDBSwift`/具体实现类 = P1。
- **R3 只注入 repository 接口 / service 协议 / 单向 usecase 接口**：依赖一律协议类型、构造注入；禁手动初始化任何实现（DI 装配在 `coordinator` 的 `Container` 扩展里完成，见证据 `Container+UseCases.swift` 的 `manageAIModelsUseCase` 工厂）。
- **R4 错误用本 domain `enum Error`**：上抛 case 来自 `domain-model` 定义的 `enum XxxError: Error`（证据：`ManageAIModelsError`，含 `modelNotFound` / `appVersionTooLow` / `modelNotDownloaded` / `cannotCancelOperation` 等带关联值 case），底层错误在 usecase 内显式 `map` 成本域 error 后再抛。
- **R5 可变共享状态线程安全**：跨 `Task` 共享的可变状态用 `actor` 封装（证据：`private actor StateManager` 管理 `activeOperations` / `subscriberMap` / 缓存 / 取消跟踪），禁裸 `var` 跨并发上下文读写。
- **R6 流生命周期闭合**：`AsyncStream` 的 `continuation` 必须声明谁创建、`onTermination` 谁清理订阅者（证据：`observeModelDownloadStatus()` 在 `onTermination` 里 `removeProgressSubscriber`）；多订阅者场景须声明广播语义（证据：`broadcastProgressUpdate()` 向所有订阅者 `yield`）。
- **R7 状态唯一写 owner**：同一业务状态只允许一个 usecase 是写 owner；双写即 P1。
- **R8 私有实现归并**：私有辅助方法置于 `private` 区（MARK: - 私有方法）或 `private extension`（对齐 Swift 代码组织规范），合同里不暴露私有方法签名（私有方法不是承接行为）。

## 章节骨架差异（相对 L1 §4）

usecase 章节在 L1 通用骨架上：

- **第 2.2 接口定义**：用 Swift 协议签名级（`protocol IXxxUseCase { func ... async throws -> T; func observeXxx() -> AsyncStream<Element> }`），不得超过签名级。
- **第 5 状态管理（usecase 必含）**：业务状态字段（含初始态、所在 actor）+ 状态转移（`mermaid stateDiagram` 或转移表）+ 写 owner 声明 + 流 seed/发射时机。无状态的纯编排 usecase 在此写"无中间业务状态，仅做单次编排"并说明理由。
- **第 6 Widget/View 设计**：usecase 恒为 `N/A（Domain 层无 UI）`。

## 好 / 坏例子（要点，全部锚定 ManageAIModels 证据）

### ✅ 好例子（合规）

- **协议签名级、async/throws 明确、闭包标注**（证据 `IManageAIModelsUseCase.swift`）：
  ```swift
  func getAllModelsWithStatus() async throws -> [AIModel]
  func downloadAIModel(modelId: String, progressHandler: @escaping (Double) -> Void) async throws
  func observeModelDownloadStatus() -> AsyncStream<[AIModelDownloadStatus]>
  ```
  每个方法都能映回一条承接行为；流元素类型 `[AIModelDownloadStatus]` 明确，seed = 订阅瞬间 `yield(initialProgress)`（证据实现 L803）。
- **错误用本 domain enum + 带关联值**：`getSpecificModelStatus` 找不到模型 → `throw ManageAIModelsError.modelNotFound(id: modelId)`；`checkForAIModelUpdate` 对未下载模型 → `throw .modelNotDownloaded(modelId:)`；底层下载器错误经 `mapDownloaderErrorToUseCaseError` 在单点转成 `.diskSpaceInsufficient` / `.networkError` / `.operationCancelled`（SLOT-04 单一收口点）。
- **只注入协议、构造注入、actor 管状态**：`init(aiModelRepository: any IAIModelRepository, aiModelDownloaderService: IAIModelDownloaderService, appInfoService: IApplicationInfoService, fileSystem: IFileSystem)` 全为协议；共享可变状态封进 `private actor StateManager`。
- **DI 在 coordinator 装配**：`Container.manageAIModelsUseCase` 工厂里 `self.aiModelRepository()` 等注入，usecase 自身不碰 `@Injected`。
- **测试密度达标**：成功 + 失败成对（`testGetSpecificModelStatus` / `testGetSpecificModelStatus_ModelNotFound`、`testDownloadAIModel_NotDownloaded` / `_AlreadyDownloaded` / `_ModelNotFound` / `_AppVersionTooLow`），流时序用 `expectation` + `for await` 断言（`testObserveModelDownloadStatus_*`），mock 注入真实 repository + `MockAIModelDownloaderService`。

### ❌ 坏例子（拦截）

- **方法清单无签名**：合同写"提供 AI 模型管理能力"而非逐方法签名 → 八问 2 缺项，P1。
- **流无时序**：写 `observeModelDownloadStatus` "按需发射"而不写 seed（订阅即回放当前全量状态）与"任一模型状态变化后广播" → 八问 6 缺项，P2。
- **越层依赖**：usecase 里 `import WCDBSwift` 直接落库、或 `import SwiftUI`、或注入具体 `AIModelRepository`（实现类而非 `any IAIModelRepository`）、或在 usecase 内 `@Injected` / 手动 `AIModelRepository(databaseManager:)` → 违反 R2/R3，P1。
- **错误裸抛底层类型**：直接把 `AIModelDownloaderError` 或 `URLError` 抛给 viewmodel 而不经 `mapDownloaderErrorToUseCaseError` 转成 `ManageAIModelsError` → 违反 R4，P1（错误转换位置缺失，SLOT-04 断点）。
- **双写状态**：本 usecase 与另一 usecase 同时写"模型下载进度"业务状态 → 违反 R7，P1，回概要重判归属。
- **裸 var 跨 Task 共享**：把 `activeOperations` / `subscriberMap` 放普通 `var` 而非 `actor` → 违反 R5，P1（数据竞争）。
- **在此补造**：usecase 合同里规定模型用 `WCDBSwift` 哪张表存、缓存几秒过期，或规定下载进度条 UI 文案 → 越界补造（属 repository / view），八问 8 红线，P1。

## 不适用场景（明确划出，避免误归）

- **纯 CRUD / 缓存回落**：没有业务规则、只是"取数据塞缓存" → 归 `repository`，不要包一层空壳 usecase。
- **无状态计算**（版本号比较、JSON 修复、纯转换）：可下沉为 `service` 协议供 usecase 注入；`compareVersions` 这类若被多 usecase 复用应抽 service，本例内联私有方法是因仅单点使用——若出现第二处使用即应下沉。
- **UI 编排**（多个业务调用的页面级串联、加载/错误三态）：归 `viewmodel`，usecase 只暴露稳定业务行为。

## Gate 判定（usecase 专项，叠加 L1 §7 G1~G7）

- **U1**：每条承接 BHV 映射到协议的恰好一个公开方法或一条流，无"一对多笼统承接"，无幽灵 BHV。
- **U2**：接口全集签名级完整（参数 / `async`/`throws` / 闭包标注 / 返回类型）；维护的流逐条有元素类型 + seed + 发射时机。
- **U3**：错误全集为本 domain `enum Error` 的 case，逐 case 有语义 + 可恢复性 + 上抛/降级标注；底层错误转换点单一且对齐 SLOT-04。
- **U4**：依赖正反两面齐全；注入项全为协议类型、构造注入；无 R2/R3 越层 import 或手动初始化或 `@Injected`。
- **U5**：业务状态唯一写 owner 与概要归属一致；可变共享状态有 actor/串行化机制（R5）；流生命周期闭合（R6）。
- **U6**：每条承接行为有 unit 测试映射，覆盖 1 成功 + 全部失败路径；每个 error case 至少被一个用例断言；流时序有 `for await` 断言。
- **U7**：八问 8 不得补造清单逐单元存在，无 UI/存储/序列化越界。
任一 U1~U7 失败 → 该 usecase 章节 P1，回 chapter_loop 审修闭环修复后复查。
