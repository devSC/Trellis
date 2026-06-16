# 示例：chapters/manage-ai-models-usecase.md（缩减成稿样例 · usecase 类）

> **成稿形态示例**（虚构模块 `ManageAIModelsUseCase` 的缩减演示），演示 `usecase` 类章节的
> 完整形态与粒度；**不是规则来源**。完整模板与逐节要求见 `../chapter-guide.md` §2，类型差异见 `detail-type-usecase.md`（L2），
> 完成条件见 `.trellis/spec/harness/detail/detail-structure-single-source.md`（L1）。
> 取证锚点为通用相对路径骨架与示例命名（落地时替换为目标仓库真实文件 / 类型，写作前先读证实）：
>
> - 接口 `IManageAIModelsUseCase` + `AIModelDownloadStatus`：`App/UseCases/ManageAIModels/IManageAIModelsUseCase.swift`
> - 实现 `ManageAIModelsUseCase`（构造注入 / `mapDownloaderErrorToUseCaseError` / `observeModelDownloadStatus` / `private actor StateManager`）：`App/UseCases/ManageAIModels/ManageAIModelsUseCase.swift`
> - 错误 `enum ManageAIModelsError: Error, Equatable`：`App/UseCases/ManageAIModels/ManageAIModelsError.swift`
> - DI 装配 `Container.manageAIModelsUseCase`（`.singleton`）：`App/DependencyInjection/Container+UseCases.swift`
> - 测试 `ManageAIModelsUseCaseTests`（真实 repository + `MockAIModelDownloaderService` 注入、成功/失败成对、流时序）：`<AppTests>/UseCases/ManageAIModels/ManageAIModelsUseCaseTests.swift`
>
> 本例 BHV-30x 为示例编号（演示承接形态），实际写作时一律引用 prd 中真实存在的 `BHV-NNN` 裸 token，幽灵引用被 gate 断链拦截。

要点提示（写作时自查，对齐 detail-type-usecase.md §U1~U7）：

1. **一条 BHV 映协议的一个公开方法或一条流**——本例每行为单独成节，禁止「一个方法笼统承接一堆 BHV」（U1）。
2. **接口签名级、`async throws`/`@escaping`/`AsyncStream` 标注齐全**——上限到签名级，不写方法体（U2）。证据：`downloadAIModel(modelId:progressHandler: @escaping (Double) -> Void) async throws`。
3. **错误用本 domain `enum Error`，底层错误单点转换**——`AIModelDownloaderError`/`URLError` 在 `mapDownloaderErrorToUseCaseError` 单点（SLOT-error-mapping）转成 `ManageAIModelsError` 后再抛，绝不裸抛给 viewmodel（U3/R4）。
4. **依赖全为协议、构造注入、DI 在 coordinator 装配**——`init` 全注入 `any IAIModelRepository`/`IAIModelDownloaderService`/`IApplicationInfoService`/`IFileSystem`；usecase 自身不碰 `@Injected`，注册在 `Container+UseCases`（U4）。
5. **可变共享状态用 actor、流生命周期闭合**——跨 `Task` 的 `activeOperations`/`subscriberMap` 封进 `private actor StateManager`；`observeModelDownloadStatus` 订阅即 `yield(initialProgress)`（seed），`onTermination` 清理订阅者（U5/R5/R6）。
6. **测试密度最高**——每条承接行为 1 成功 + 全部失败路径，每个 `enum Error` case 至少一条断言，流时序用 `for await` 断言（U6）。
7. **不得补造清单写「决策属于谁」**——「不决定模型存哪张表/缓存几秒——属 repository」这种指向式写法才可审计（U7）。

---

# manage-ai-models-usecase 详细设计

> doc_type：usecase ｜ l2_status：full（detail-type-usecase.md）｜ owner 层：Domain
> 承接索引：design-main.md 第 7 节 manage-ai-models-usecase ｜ 返回：[design-main](../design-main.md)
> partial_scope：N/A

## 1. 单元职责

`UNIT-manage-ai-models-usecase`（`IManageAIModelsUseCase` + 实现 `ManageAIModelsUseCase`）是 Domain 层 **AI 模型管理业务编排 + 全局下载状态发射的 owner**，零 UI 依赖。
承接 BHV-301（取全部模型状态）/ BHV-302（下载模型并回放进度）/ BHV-303（全局下载状态流）。

- 依赖（构造注入，全为协议）：`any IAIModelRepository`（repository 接口，取/存模型）、`IAIModelDownloaderService`（external 下载器协议）、`IApplicationInfoService`（external 应用信息协议，取当前 App 版本）、`IFileSystem`（external 文件系统协议）。
- 被调用：`AIModelManagementViewModel`（viewmodel）调其公开方法并订阅 `observeModelDownloadStatus()` 流。
- 依赖方向：UI(viewmodel) → Domain(本 usecase) → Domain(repository 接口)/Infrastructure 协议抽象，符合 L1 §6.1 分层依赖律（本单元不依赖 viewmodel/view/coordinator，不 import SwiftUI/FactoryKit/WCDBSwift）。

## 2. 行为定义

### 2.1 行为清单

- getAllModelsWithStatus — 取全部 AI 模型及当前状态（BHV-301）｜详见 §4.1
- downloadAIModel — 下载指定模型，经 `progressHandler` 回放进度（BHV-302）｜详见 §4.2
- observeModelDownloadStatus — 全局下载/更新状态流（BHV-303）｜详见 §4.3

### 2.2 接口定义（Swift 签名级，不写方法体）

```swift
protocol IManageAIModelsUseCase {
    func getAllModelsWithStatus() async throws -> [AIModel]
    func getSpecificModelStatus(modelId: String) async throws -> AIModelStatus
    func downloadAIModel(modelId: String, progressHandler: @escaping (Double) -> Void) async throws
    func observeModelDownloadStatus() -> AsyncStream<[AIModelDownloadStatus]>
}
```

> 注入声明（实现侧，构造注入，持有协议类型；不在 usecase 内 `@Injected` 或手动 new）：
> ```swift
> init(aiModelRepository: any IAIModelRepository,
>      aiModelDownloaderService: IAIModelDownloaderService,
>      appInfoService: IApplicationInfoService,
>      fileSystem: IFileSystem)
> ```

## 3. 核心数据结构

### 3.1 数据模型（签名级；实体本体归 domain-model，此处只引用 + 列流元素值对象）

```swift
// 流元素值对象（usecase 暴露给 viewmodel 的只读状态快照）
struct AIModelDownloadStatus: Equatable {
    let modelId: String
    let modelName: String
    let modelType: AIModelType
    let downloadType: DownloadType           // .download / .update(fromVersion:toVersion:)
    let progress: Double                     // 0.0...1.0
    let status: DownloadStatus               // .started/.inProgress/.completed/.cancelled/.failed(message:)
    let startTime: Date
    let estimatedTimeRemaining: TimeInterval?
}
```

`AIModel` / `AIModelStatus` / `AIModelType` 实体与领域枚举归 `domain-model`（本单元只 *使用*，不重定义）。

### 3.2 错误类型表（`enum ManageAIModelsError: Error, Equatable`，归属层 Domain）

| 错误名 | 枚举 case | 语义 | 归属层 | 转换/收口位置（SLOT-error-mapping） |
|--------|-----------|------|--------|------------------------------------|
| modelNotFound | `modelNotFound(id:)` | 仓库无此 modelId | Domain | usecase 入口 `guard` |
| appVersionTooLow | `appVersionTooLow(modelId:requiredVersion:currentVersion:)` | 当前 App 版本低于模型要求 | Domain | usecase 版本比对 |
| diskSpaceInsufficient | `diskSpaceInsufficient(requiredBytes:availableBytes:)` | 磁盘不足 | Domain | `mapDownloaderErrorToUseCaseError`（单点转换） |
| networkError | `networkError(description:)` | 网络连接错误 | Domain | `mapDownloaderErrorToUseCaseError` |
| operationCancelled | `operationCancelled(modelId:)` | 操作被取消 | Domain | `mapDownloaderErrorToUseCaseError` |
| downloadFailed | `downloadFailed(modelId:underlyingError:)` | 其它下载失败（兜底，含底层错误） | Domain | `mapDownloaderErrorToUseCaseError` 默认分支 |

> 需测试断言相等性，故 `ManageAIModelsError` 手写 `static func ==`（实现 `Equatable`，golden-path §2.5）。完整 case 集合见错误文件，本例只列承接行为触达的 case。

## 4. 逐行为设计

### 4.1 getAllModelsWithStatus

- 函数签名：`func getAllModelsWithStatus() async throws -> [AIModel]`
- 简述：承接 BHV-301——取全部模型及其当前状态，单次编排转发给 repository。
- 输入参数：无。
- 输出表：

  | 返回值 | 类型 | 语义 |
  |--------|------|------|
  | models | `[AIModel]` | 全部模型及状态（含未下载/下载中/已下载） |

- 依赖调用表（八问 4）：

  | 依赖 | 注入方式 | 调用的行为 | 不调用边界 |
  |------|---------|-----------|-----------|
  | `any IAIModelRepository` | 构造注入 | `fetchAllModels()` | 不直接碰 `WCDBSwift`/`DatabaseManager`（属 repository 实现） |

- 执行流程：

  ```mermaid
  sequenceDiagram
      participant U as ManageAIModelsUseCase
      participant R as IAIModelRepository
      U->>R: 1. fetchAllModels()
      R-->>U: 2. [AIModel] / throws PersistenceError
      U-->>U: 3. return [AIModel]（PersistenceError 透传上抛，本行为不二次转换）
  ```

- 流程详述：
  1. `try await aiModelRepository.fetchAllModels()` 取全部模型（仓储侧已将 WCDBSwift 原始错误转 `PersistenceError`）。
  2. 直接返回；本行为无业务规则，仅单次编排。
- 异常处理表：

  | 异常情况 | 处置 | 错误转换位置 |
  |---------|------|-------------|
  | 仓储读取失败 | 透传 `PersistenceError` 上抛（viewmodel 降级为错误态文案） | repository 实现边界（已转换） |

### 4.2 downloadAIModel

- 函数签名：`func downloadAIModel(modelId: String, progressHandler: @escaping (Double) -> Void) async throws`
- 简述：承接 BHV-302——校验存在性与版本，启动下载并经 `progressHandler` 回放进度，底层错误单点归一为 `ManageAIModelsError`。
- 输入参数：

  | 参数 | 类型 | 取值域/约束 | 必填 |
  |------|------|-----------|------|
  | modelId | `String` | 必须能在仓库命中 | 是 |
  | progressHandler | `@escaping (Double) -> Void` | 进度 0.0...1.0 回调 | 是 |

- 输出表：无返回值；副作用经 `progressHandler` 回放进度，并经 §4.3 流广播状态。
- 依赖调用表（八问 4）：

  | 依赖 | 注入方式 | 调用的行为 | 不调用边界 |
  |------|---------|-----------|-----------|
  | `any IAIModelRepository` | 构造注入 | `findModel(byId:)`、保存状态 | 不决定存哪张表/缓存策略（属 repository） |
  | `IApplicationInfoService` | 构造注入 | `getCurrentAppVersion()` | 不实现版本获取细节（属 external） |
  | `IAIModelDownloaderService` | 构造注入 | `downloadModel(...)`、`observeDownloadState(taskId:)` | 不实现网络/SDK 细节（属 external） |

- 执行流程：

  ```mermaid
  sequenceDiagram
      participant U as ManageAIModelsUseCase
      participant R as IAIModelRepository
      participant A as IApplicationInfoService
      participant D as IAIModelDownloaderService
      U->>R: 1. findModel(byId:)  // nil → throw .modelNotFound
      U->>A: 2. getCurrentAppVersion()  // 低于要求 → throw .appVersionTooLow
      U->>D: 3. downloadModel(from:modelId:specificFiles:)
      D-->>U: 4. 进度/状态流（observeDownloadState）→ progressHandler 回放
      U-->>U: 5. 失败：throw mapDownloaderErrorToUseCaseError(error:modelId:)
  ```

- 流程详述（满足 L1 §3.1 粒度标准）：
  1. `guard let model = try await aiModelRepository.findModel(byId: modelId)`，nil → `throw ManageAIModelsError.modelNotFound(id: modelId)`，流程终止。
  2. 若 `model.minimumRequiredAppVersion` 高于 `appInfoService.getCurrentAppVersion()` → `throw .appVersionTooLow(modelId:requiredVersion:currentVersion:)`。
  3. 按 `model.status` 分流：已在 `.downloading`/`.updating` → 附加 `progressHandler` 到现有操作并 return（不重复启动）；已是最新 `.downloaded` → return。
  4. 经 `aiModelDownloaderService.downloadModel(...)` 启动下载，置 `.downloading(progress: 0.0)` 并经 §4.3 广播；订阅 `observeDownloadState(taskId:)` 推进进度。
  5. 启动失败 → `throw await mapDownloaderErrorToUseCaseError(error: error, modelId: modelId)`（底层 `AIModelDownloaderError` 在此单点转 `ManageAIModelsError`，SLOT-error-mapping）。
- 异常处理表：

  | 异常情况 | 处置 | 错误转换位置 |
  |---------|------|-------------|
  | 模型不存在 | 上抛 `.modelNotFound`，流程终止 | usecase 入口 `guard` |
  | App 版本过低 | 上抛 `.appVersionTooLow` | usecase 版本比对 |
  | 磁盘不足 | 上抛 `.diskSpaceInsufficient` | `mapDownloaderErrorToUseCaseError` |
  | 网络失败 | 上抛 `.networkError` | `mapDownloaderErrorToUseCaseError` |
  | 用户/系统取消 | 上抛 `.operationCancelled` | `mapDownloaderErrorToUseCaseError` |
  | 其它下载失败 | 上抛 `.downloadFailed`（兜底） | `mapDownloaderErrorToUseCaseError` 默认分支 |

### 4.3 observeModelDownloadStatus

- 函数签名：`func observeModelDownloadStatus() -> AsyncStream<[AIModelDownloadStatus]>`
- 简述：承接 BHV-303——多订阅者广播全局下载/更新状态；订阅即回放当前全量状态（seed），任一模型状态变化时广播。
- 输入参数：无。
- 输出表：

  | 发射值 | 类型 | 语义 |
  |--------|------|------|
  | 状态快照 | `[AIModelDownloadStatus]` | 全部模型当前下载/更新状态；订阅瞬间 seed 一次，状态变化后广播 |

- 依赖调用表（八问 4）：

  | 依赖 | 注入方式 | 调用的行为 | 不调用边界 |
  |------|---------|-----------|-----------|
  | `private actor StateManager` | 内部持有 | `addSubscriber(_:)`、`removeProgressSubscriber` | 不暴露 actor 给上层（仅本单元内可见） |

- 执行流程：

  ```mermaid
  sequenceDiagram
      participant VM as AIModelManagementViewModel
      participant U as ManageAIModelsUseCase
      participant S as StateManager(actor)
      VM->>U: 1. observeModelDownloadStatus()
      U->>S: 2. addSubscriber(continuation)
      U-->>VM: 3. continuation.yield(initialProgress)  // seed：订阅即回放当前全量状态
      Note over U,S: 任一模型状态变化 → broadcastProgressUpdate() 向所有订阅者 yield
      VM->>U: 4. 订阅取消 → onTermination → removeProgressSubscriber(subscriberId)
  ```

- 流程详述：
  1. 创建 `AsyncStream<[AIModelDownloadStatus]>`，在 `Task` 中 `await stateManager.addSubscriber(continuation)` 取唯一 `subscriberId`。
  2. 立即 `continuation.yield(initialProgress)`（seed = 订阅瞬间当前全量状态）。
  3. 任一模型状态变化由 `broadcastProgressUpdate()` 向所有订阅者 `yield`（广播语义）。
  4. `continuation.onTermination` 中 `await self.removeProgressSubscriber(subscriberId:)` 清理订阅者（流生命周期闭合，R6）。
- 异常处理表：

  | 异常情况 | 处置 | 错误转换位置 |
  |---------|------|-------------|
  | 单模型下载失败 | 发射状态元素 `status = .failed(message:)`（`AsyncStream` 无 error 通道，失败建模为元素，不静默吞） | usecase 流内 |

## 5. 状态管理（usecase 必含）

- 业务状态清单（唯一写 owner = 本 usecase，封装在 `private actor StateManager`）：
  - `activeOperations: [String: OperationContext]`（进行中下载/更新操作，按 modelId 索引）
  - `subscriberMap: [Int: AsyncStream<[AIModelDownloadStatus]>.Continuation]`（订阅者表）
  - `modelStatusCache: [String: AIModel]`（状态缓存）、`cancelledModels: [String: Date]`（取消跟踪）
- 线程安全：上述可变共享状态全部经 `actor StateManager` 串行化访问（跨 `Task` 安全，R5）；禁裸 `var` 跨并发上下文读写。
- 状态转移（单模型下载态）：

  ```mermaid
  stateDiagram-v2
      [*] --> notDownloaded
      notDownloaded --> downloading: downloadAIModel
      downloading --> downloaded: 完成
      downloading --> notDownloaded: cancelled
      downloading --> error: failed(message)
      error --> downloading: 重试 downloadAIModel
  ```

- 流 seed/发射时机：`observeModelDownloadStatus` 订阅瞬间 `yield(initialProgress)`，此后任一模型状态变化广播。

## 6. View 设计

N/A（Domain 层无 UI——usecase 恒为 `N/A`，detail-type-usecase.md 章节骨架差异）。

## 7. 测试映射（测试框架 XCTest，mock 按 project-conventions 槽位；证据 `ManageAIModelsUseCaseTests`）

| BHV/行为 | 测试层 | 测试点（成功 + 失败路径） | mock 对象 |
|----------|--------|--------------------------|-----------|
| BHV-301 getAllModelsWithStatus | unit | 返回全部模型及状态 | 真实 `AIModelRepository`（临时 DB）|
| BHV-302 downloadAIModel 成功 | unit | 未下载模型可启动下载 | `MockAIModelDownloaderService` |
| BHV-302 modelNotFound | unit | 不存在 modelId → `throws .modelNotFound` | 真实 repository |
| BHV-302 appVersionTooLow | unit | 版本过低 → `throws .appVersionTooLow` | `MockApplicationInfoService` |
| BHV-302 已下载/下载中 | unit | 已下载/进行中不重复启动 | `MockAIModelDownloaderService` |
| BHV-303 observe 初始态 | unit | 订阅即 seed 当前全量状态（`for await` 首元素断言） | 真实 repository |
| BHV-303 observe 进度广播 | unit | 下载推进时广播状态（`for await` 序列断言） | `MockAIModelDownloaderService` |
| BHV-303 多订阅者 | unit | 多订阅者均收到广播 | `MockAIModelDownloaderService` |

> 每条承接行为有 1 成功 + 全部失败路径；每个触达的 `enum Error` case 至少一条断言它被抛出（`.modelNotFound`/`.appVersionTooLow`）；流时序用 `for await` 断言发射序列（证据 `testObserveModelDownloadStatus_*`）。

## 8. 不得补造清单

- 不决定模型存哪张表 / 缓存几秒过期 / local-remote 回落——属 `repository`（含是否走 WCDBSwift）。
- 不决定下载进度条 UI、文案、加载/错误三态展示——属 `view` / `viewmodel`。
- 不决定 `AIModel` 实体字段与序列化、领域枚举定义——属 `domain-model`。
- 不实现网络/下载器/文件系统/版本获取的技术细节——属 `external`（本单元只注入其协议）。
- 不在未确认的业务规则（如自动重试次数/超时阈值）上拍板——若概要未收口，列入 §10 未决问题回概要，禁止详细阶段私自定。

## 9. 不适用场景与产物合同

- 落盘产物：接口 `App/UseCases/ManageAIModels/IManageAIModelsUseCase.swift`、实现 `App/UseCases/ManageAIModels/ManageAIModelsUseCase.swift`、错误 `App/UseCases/ManageAIModels/ManageAIModelsError.swift`；DI 注册项 `Container+UseCases.swift` 的 `manageAIModelsUseCase`（`.singleton`）。
- 不负责：UI 展示、持久化引擎、网络/SDK 实现（见 §8）。

## 10. 未决问题与跨章引用

- 跨章稳定引用：`IAIModelRepository`（→ `UNIT-ai-model-repository`，repository 章）、`IAIModelDownloaderService`/`IApplicationInfoService`/`IFileSystem`（→ external 章）；上述接口签名变更时回本章复查依赖调用闭合。
- 未决问题：无（示例）。真实成稿若有未决项须显式列出并标风险等级，禁止留空、禁止 TODO。

---

> 写作收口提示：本例为 usecase 类**单章缩减样例**；真实成稿通常行为数 ×2~3、错误枚举与测试行更多，
> 其余六类（domain-model / repository / viewmodel / view / coordinator / external）的章节按 `../chapter-guide.md` §4 的对应类型要点同构展开，
> 此处不重复贴出，避免多份样例漂移。完成条件以 L1 §3 合同八问 + §3.1 粒度 + §7 G1~G8 为准；usecase 类另叠加 detail-type-usecase.md §U1~U7。
