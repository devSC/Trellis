# L2 类型规范：viewmodel（UI 层状态容器）

> doc_type：`viewmodel`（IOS_BRIEF 钉死七类之一，全程唯一，禁止改名/增减/换数）｜ owner 层：UI
> 从属于详细设计 L1 单一来源规范；本文件只承载 `viewmodel` 类型的**差异规则**，与 L1 冲突时以 L1 为准。
> golden-path 对应：装载后见 [`.trellis/spec/guides/golden-path.md`](.trellis/spec/guides/golden-path.md) 的 viewmodel 迷你路径、分层依赖律、FactoryKit DI 装配、禁止清单。
> 流程与模板见 `.trellis/spec/harness/*`；项目槽位取值见 `.trellis/spec/conventions/project-conventions.md`。

---

## 1. 适用对象与边界

**适用**：UI 层 `ObservableObject` + `@Published` 状态容器，承载单个页面 / 子组件的可观察状态、用户事件入口、生命周期钩子，把稳定的 Domain 行为适配为 SwiftUI 可绑定的状态。基类形态固定为 `class Xxx: ObservableObject`（SwiftUI 主轨）；RxSwift 遗留模块在迁移期内可暂存 `BehaviorRelay`，新增一律纯 `@Published`（见 project-conventions「UI 框架」槽位）。

**不适用，归属如下**（越界即 P1）：

| 误放到 viewmodel 的内容 | 正确 doc_type | 归属层 |
|----------------------|--------------|-------|
| 业务规则编排、跨用例事务、状态机推进 | `usecase` | Domain |
| 数据访问、缓存回落、local/remote 编排 | `repository` | Domain 接口 + Infrastructure 实现 |
| 实体 / 值对象 / `enum XxxError` / 不变量 | `domain-model` | Domain |
| 纯展示 + 输入的 SwiftUI 视图（无状态字段写入逻辑） | `view` | UI |
| 跨页面导航、DI 装配 | `coordinator` | App |
| 网络 / SDK / WCDBSwift 持久化 / 第三方 | `external` | Infrastructure |

> 证据基线：`StoryVerse/UI/Features/Home/ViewModels/HomeViewModel.swift`（`class HomeViewModel: ObservableObject`）、`StoryVerse/UI/Features/Voice/ViewModel/VoiceCreationViewModel.swift`（`@MainActor class VoiceCreationViewModel: ObservableObject`）。

---

## 2. 合同八问的 viewmodel 类型特化

> L1 §3 的合同八问为通用骨架；以下为 `viewmodel` 类型上的**收紧/特化**。每问括号内为可验证信号（审核按此取证）。

### 2.1 承接哪些行为
逐条引用 prd 的 `BHV-NNN`（裸 token），覆盖**本页面的用户操作**（点击/输入/下拉刷新）与**生命周期事件**（`onViewAppear` / `onDisappear` / `task`）。
（信号：每个 `@Published` 状态字段、每个对外命令方法都能回指至少一条 `BHV-NNN`；幽灵引用 / 无承接命令 = 断链 P1。）

### 2.2 输入 / 输出 / 错误
- **输入** = 路由入参（由 `coordinator` 传入，经 `init` 或属性注入）＋ 订阅的 usecase 异步流 / `async` 返回 ＋ 用户事件（命令方法参数）。
- **输出** = **状态字段全集**，必须以 `@Published 状态字段表`（见 §3）**逐字段列出**：名称 / 类型 / 初始值 / 写入时机 / owner ＋ 对外暴露的命令方法签名（Swift）。派生只读状态（`var isDisabled: Bool { ... }`，证据见 `VoiceCreationViewModel.isDisabled`）单列「计算属性」，不计入可写字段。
- **错误** = **三态收口**：每个异步加载型状态字段必须显式定义 `loading / empty(或 success/content) / error` 三态的展示去向（见 §4）。错误来源一律是 Domain 上抛的 `enum XxxError`（如 `StoryError`，证据见 `Domain/Errors/StoryError.swift`），viewmodel 负责**翻译为用户可见反馈**，不得新造业务错误码。

### 2.3 读取 / 写入哪些状态
本 viewmodel 是其 `@Published` 字段的**唯一写 owner**；订阅的 usecase 流 / 返回值**只读消费**。
- **禁止两个 viewmodel 写同一份业务状态**——业务状态（如「当前会话」「下载进度」）归 `usecase`，viewmodel 只镜像投影。
- 导航状态（`activeDestination` 等）归 `coordinator`（`AppCoordinator: ObservableObject`，证据见 `App/Coordinators/AppCoordinator.swift`），viewmodel 不持有也不直接改写。
（信号：可回指概要归属表行，写 owner 唯一。）

### 2.4 调用哪些依赖，不调用哪些依赖（正反两面都写）
- **可调用**：`usecase` 接口（`IXxxUseCase`）、`repository` 接口（`IXxxRepository`，仅在无业务编排的纯读取页面允许，优先走 usecase）、UI 层横切单例（`ThemeManager.shared`、`ToastManager.shared`）。依赖**一律 `@Injected` 注入接口类型**，禁手动 `init` 构造实现。
  - 证据：`@Injected(\.storyManageUseCase) var storyManageUseCase`，DI 注册为 `Factory<IStoryManagementUseCase>`（`Container+UseCases.swift`）、`Factory<IExportStoryUseCase>`、`Factory<IVoiceProfileUseCase>`、`Factory<IFileSystem>`——全是接口。
- **不可调用（越层，P1）**：Repository **实现类**（`XxxRepositoryImpl`）、WCDBSwift / `DatabaseManager`、`URLSession` / Moya / 网络客户端、第三方 SDK 具体类型、**其他 viewmodel**、`view` 内部状态。这些越过 Domain 接口边界即违反「Domain→App→Infrastructure→UI 单向依赖律」。

### 2.5 失败如何收口
每条失败路径 → **写 error 态字段** ＋ **用户可见反馈**（`ToastManager` 提示 / 占位视图 / 重试入口三选一，逐条指明）。
- 错误转换位置遵循 project-conventions「JSON 修复策略 / 错误映射」槽位：Domain `enum XxxError` → viewmodel 内 `switch error { ... }` → 文案 + 状态。
- **禁止空 `catch {}`**（吞错即 P1，证据反例见 §6）。`do/catch` 必须落到状态字段或 `ToastManager`。
- `async` 任务在 `Task { }` 内执行，UI 写回必须切 `await MainActor.run { }` 或类型标 `@MainActor`（证据见 `HomeViewModel.loadStorys` 的 `await MainActor.run`、`VoiceCreationViewModel` 的 `@MainActor`）。

### 2.6 产生哪些事件 / 后置结果
- **埋点事件清单**：事件名 + 触发时机 + 参数（逐条；消费方为分析 `external`）。
- **导航动作**：去哪个目的地、带什么参数——一律**委托 `coordinator`**（调用 `Coordinating` 协议方法，如 `navigateToStoryDetail(storyId:)`），viewmodel 不直接 push/present，不在 view 间跳转。
- **副作用**：文件落盘 / 分享面板等走注入的 `external` 接口（如 `IFileSystem.saveFileToPanel`，证据见 `HomeViewModel.onTapStoryExport`），viewmodel 只编排调用顺序，不实现 IO。

### 2.7 哪些测试验证它
- 事件 → 状态转移 = **XCTest unit**（mock usecase/repository 接口，mock 生成走 project-conventions「mock 生成」槽位 = Mockolo；遗留手写 mock 迁移期可用）。每条命令方法覆盖**成功 + 全部失败路径**。
- 生命周期行为 = unit 覆盖 `onViewAppear` / `onDisappear` 触发的加载与订阅取消。
- 三态断言：loading→content / loading→empty / loading→error 三条转移各有断言。
- **不在此层测 UI 结构**（归 `view` 的 ViewInspector / 快照测试）。
（测试目录证据：`StoryVerseTests/`。）

### 2.8 哪些内容不得在此补造
- 不发明业务规则 / 校验门槛（属 `usecase`）。
- 不决定缓存 / 持久化 / 落库策略（属 `repository`）。
- 不定义 `enum XxxError` 业务错误（属 `domain-model`，viewmodel 只消费）。
- 不直接操纵其他页面状态、不自行导航（属 `coordinator`）。
- 不在 viewmodel 里硬编码本应来自 usecase 的业务数据（反例见 §6 `loadMyCreationData` 的硬编码计数）。

---

## 3. @Published 状态字段表（强制产物合同）

每个 viewmodel UNIT 必含下表，**逐字段一行，不得一句话带过**：

| 字段名 | 类型 | 初始值 | 写入时机（命令方法 / 生命周期 / 流回包） | 写 owner | 承接 BHV |
|--------|------|--------|----------------------------------------|---------|---------|
| `recentStories` | `[Story]` | `[]` | `loadStorys()` 成功回包后置入（排序后） | 本 vm | BHV-NNN |
| `loadState` | `LoadState` | `.idle` | `loadStorys()` 入口置 `.loading`；成功置 `.content` 或 `.empty`；失败置 `.error(message)` | 本 vm | BHV-NNN |
| `creations` | `[Creation]` | `[]` | `loadCreationData()` 成功回包后构建 | 本 vm | BHV-NNN |

计算属性（派生只读，不可外部写）单列：

| 计算属性 | 类型 | 派生自 | 语义 |
|---------|------|--------|------|
| `isDisabled` | `Bool` | `title` / `image` / `audio` | 表单是否禁用提交（证据见 `VoiceCreationViewModel.isDisabled`） |

> 表是表达形式，「逐字段可追溯」是完成条件。无字段表或字段表缺 owner/写入时机列 = P2（合同不完整）。

---

## 4. 三态收口规范（异步状态字段强制）

每个异步加载型 `@Published` 字段必须定义三态枚举或等价标志，并指明每态的 view 去向。推荐 Domain 无关的 UI 状态枚举（声明在 viewmodel 文件内或 UI 层共享）：

```swift
enum LoadState: Equatable {
    case idle                 // 未触发
    case loading              // 加载中 → 展示骨架/菊花
    case content              // 有数据 → 展示列表
    case empty                // 加载成功但空集 → 展示空占位 + 引导
    case error(message: String) // 失败 → 展示错误占位 + 重试入口
}
```

三态 → view 去向矩阵（每个异步字段一份）：

| 状态 | 触发时机 | view 去向 | 用户反馈 |
|------|---------|----------|---------|
| `loading` | 命令方法入口立即置位 | 骨架屏 / `ProgressView` | 不可重复触发（防抖） |
| `content` | usecase 成功且非空 | 主列表 | — |
| `empty` | usecase 成功但 `isEmpty` | 空占位视图 | 引导创建入口 |
| `error` | `catch` 分支按 `XxxError` 翻译 | 错误占位 | `ToastManager` 提示 + 重试按钮回调命令方法 |

**硬要求**：`success` 与 `empty` 必须区分（空集不是错误）；`error` 文案来自 Domain 错误翻译，不得为「待定」「TODO」。

---

## 5. iOS 类型硬规则（golden-path 锁定，违反直接 fail）

1. **形态**：`class Xxx: ObservableObject`，可观察状态一律 `@Published`，禁用裸 `var` 充当对外状态。
2. **DI**：依赖一律 `@Injected(\.xxx)` 注入**接口类型**（`IXxxUseCase` / `IXxxRepository`），禁手动 `init` 构造实现类；viewmodel 自身经 `Container.xxxViewModel` Factory 装配（证据见 `Container+ViewModels.swift` 的 `homeViewModel: Factory<HomeViewModel>`，含 `@MainActor`）。
3. **Repository 模式强制**：viewmodel 只触达 Domain 接口；禁直接持久化（WCDBSwift / `DatabaseManager`）、禁直接网络。
4. **持久化禁令**：禁 CoreData / SwiftData / 直接 WCDBSwift 调用；落库一律走 `repository`。
5. **错误分层**：消费 Domain `enum XxxError`，不在 UI 层新造业务错误枚举。
6. **并发**：UI 写回主线程（类型 `@MainActor` 或 `await MainActor.run`）；订阅 / `Task` 在生命周期收口处取消（流/任务泄漏 = P1）。
7. **private 方法在 `private extension`**：内部辅助方法（如数据组装、私有加载）放进 `private extension Xxx { }`，与对外命令方法分区（golden-path 代码组织规则）。
8. **体量**：单 viewmodel 超约 300 行考虑按职责域拆分（指南建议，非硬门禁）。

---

## 6. 好 / 坏例子（Swift 代码）

### 6.1 好例子（修正后，对齐硬规则）

```swift
import Foundation
import FactoryKit

/// 首页视图模型：承接 BHV-LOAD-RECENT-STORIES / BHV-DELETE-STORY / BHV-EXPORT-STORY
@MainActor
final class HomeViewModel: ObservableObject {

    // MARK: - @Published 状态（owner：本 vm）
    @Published private(set) var recentStories: [Story] = []
    @Published private(set) var creations: [Creation] = []
    @Published private(set) var loadState: LoadState = .idle   // 三态收口

    // MARK: - 依赖（@Injected 接口，禁手动 init）
    @Injected(\.storyManageUseCase) private var storyManageUseCase   // IStoryManagementUseCase
    @Injected(\.voiceProfileUseCase) private var voiceProfileUseCase // IVoiceProfileUseCase
    @Injected(\.exportStoryUseCase) private var exportStoryUseCase   // IExportStoryUseCase
    @Injected(\.fileSystem) private var fileSystem                   // IFileSystem
    @Injected(\.coordinator) private var coordinator                 // Coordinating

    // MARK: - 命令方法（对外）
    func onViewAppear() {
        Task { await loadStorys() }
        Task { await loadCreations() }
    }

    func onTapStory(_ id: String) {
        coordinator.navigateToStoryDetail(storyId: id)   // 导航委托 coordinator
    }

    func onTapStoryDelete(_ id: String) {
        Task {
            do {
                try await storyManageUseCase.deleteStory(storyId: id)
                await loadStorys()
            } catch let error as StoryError {            // 消费 Domain 错误，不空 catch
                loadState = .error(message: error.userMessage)
                ToastManager.shared.show(error.userMessage)
            } catch {
                ToastManager.shared.show("删除失败，请重试")
            }
        }
    }
}

// MARK: - 私有方法（private extension，按硬规则 7）
private extension HomeViewModel {
    func loadStorys() async {
        loadState = .loading                            // loading 态
        do {
            let stories = try await storyManageUseCase.fetchAllFullStories()
            recentStories = stories.sorted { $0.updatedAt > $1.updatedAt }
            loadState = recentStories.isEmpty ? .empty : .content  // empty/success 区分
        } catch let error as StoryError {
            loadState = .error(message: error.userMessage)         // error 态
        } catch {
            loadState = .error(message: "加载失败")
        }
    }

    func loadCreations() async {
        // creations 仅依赖 usecase 真实计数，view 数据由 view/usecase 提供，vm 不硬编码业务数
        guard let count = try? await voiceProfileUseCase.listVoiceProfiles().count else { return }
        creations = CreationFactory.make(voiceCount: count)        // 组装走工厂，不在 vm 写死列表
    }
}
```

要点：状态字段表完整、`@Published private(set)` 写 owner 唯一、三态齐全、依赖全是 `@Injected` 接口、导航委托 `coordinator`、私有方法在 `private extension`、错误来自 `StoryError`。

### 6.2 坏例子（贴 story-verse 实测 `HomeViewModel`，逐条标注问题）

```swift
class HomeViewModel: ObservableObject {
    @Published var recentStories: [Story] = []           // ❌ 无 private(set)，对外可被任意改写，写 owner 不唯一
    @Published var creations: [Creation] = []
    // ❌ 缺三态字段：没有 loading/empty/error，view 无从区分加载中与空集

    @Injected(\.storyManageUseCase) var storyManageUseCase
    @Injected(\.fileSystem) var fileSystem

    func loadStorys() {
        Task {
            do {
                let storys = try await storyManageUseCase.fetchAllFullStories()
                await MainActor.run {
                    recentStories = storys.sorted(by: { $0.updatedAt > $1.updatedAt })
                }
            } catch {
                // ❌ 空 catch：吞掉所有错误，无 error 态、无用户反馈（P1）
            }
        }
    }

    func onTapStoryExport(_ story: Story, format: ExportFormat) {
        Task {
            do {
                ToastManager.shared.showLoading()
                let result = try await exportStoryUseCase.execute(...)
                ToastManager.shared.hideLoading()
                try await fileSystem.saveFileToPanel(...)
            } catch {
                Logger.d("onTapStoryExport failed: \(error)") // ❌ 仅日志，无用户可见反馈、无 error 态
            }
        }
    }

    func loadMyCreationData(with voiceCount: String) {
        creations = [
            Creation(type: .photos, count: "24", isComingSoon: true, ...),  // ❌ 业务计数写死在 vm（"24"/"12"）
            Creation(type: .draw,   count: "12", isComingSoon: true, ...),  //    属 usecase/view 决策，viewmodel 补造业务数据
            // ...
        ]
    }
    // ❌ 私有 loadCreationData() 与对外方法混在同一 class body，未拆 private extension
}
```

问题清单（与 §2/§4/§5 一一对应）：① 缺三态（§4）；② 两处空/仅日志 `catch`（§2.5 P1）；③ `@Published` 无 `private(set)`，写 owner 边界松（§2.3）；④ `loadMyCreationData` 把业务计数硬编码进 vm（§2.8 补造）；⑤ 私有方法未入 `private extension`（§5.7）；⑥ 命令方法名拼写错误 `onViewAppera`（实测，命名纪律）。

---

## 7. 不适用场景（明确不走 viewmodel）

- **纯静态展示页**（无任何 `@Published` 写入、无用户事件触发业务）：直接归 `view`，不强制起 viewmodel。
- **跨页面共享会话/全局状态**：归 `usecase`（业务态）或 `coordinator`（导航态），不在 viewmodel 间共享 `final` 字段。
- **后台长任务进度**（如导出队列）：进度态归 `usecase`/`external` 持有，viewmodel 只订阅投影。

---

## 8. Gate 判定（viewmodel 专项，并入 L1 G1~G5）

| 检查项 | 通过信号 | 违反严重度 |
|--------|---------|-----------|
| 八问完整 | 8 问逐条有实质内容（非占位） | P1（缺项） |
| @Published 字段表 | 逐字段含 名称/类型/初始值/写入时机/owner/BHV | 缺表 P1；缺列 P2 |
| 三态收口 | 每个异步字段 loading/empty(或 success)/error 去向齐全 | P1（error 为「待定」即 fail） |
| 依赖正反面 | 只 `@Injected` 接口；显式列出不可调用项 | 注入实现类/越层 P1 |
| 禁直接持久化 | 无 WCDBSwift/DatabaseManager/CoreData/SwiftData/网络直连 | P1 |
| 写 owner 唯一 | 无两 vm 写同一业务态；导航委托 coordinator | P1 |
| 测试映射 | 每命令方法成功+全部失败路径有 XCTest 点 | 缺失路径 P2 |
| 不得补造清单 | §2.8 五条逐条存在 | 缺失 P1（G5） |
| private extension | 私有方法集中在 `private extension` | P3（组织建议） |

> 详细阶段文档无存量豁免（新文档全量合规）。findings 带本文章节锚点；前置失败只输出前置缺口。
