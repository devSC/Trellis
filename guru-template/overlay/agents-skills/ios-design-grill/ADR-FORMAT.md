# ADR 格式（Guru iOS 原生平台）

拷问会话中达成的、值得留痕的架构决策固化成 ADR。ADR 存放在仓库 `docs/adr/`，顺序编号：`0001-slug.md`、`0002-slug.md` ……

`docs/adr/` 目录**懒创建**——仅当出现第一条需要记录的 ADR 时才建立（story-verse-mac 当前无 `docs/adr/`，首条 ADR 落盘时新建）。

> 与"项目约定取值"的关系：ADR 记录**决策本身与理由**；当决策改变的是 `project-conventions.md` 的某个 SLOT 取值（如 SLOT-08 网络栈、SLOT-14 测试框架）时，ADR 是修订该槽位的前置依据（conventions 修订须挂 ADR 链接），但 ADR 不替代槽位取值正文——取值仍写在 `project-conventions.md`。

## 模板

```md
# {决策的一句话标题}

{1~3 句：上下文是什么、我们决定了什么、为什么。}
```

就这些。一条 ADR 可以只有一段。价值在于记录**做过这个决策**以及**为什么**——不在于把章节填满。

## 可选章节

仅当确实增加价值时才加（多数 ADR 不需要）：

- **Status** frontmatter（`proposed | accepted | deprecated | superseded by ADR-NNNN`）——决策会被重新审视时有用（如 RxSwift→SwiftUI 迁移边界后续推进）。
- **Considered Options**——仅当被否决的备选值得记住时（如"WCDBSwift vs CoreData vs SwiftData"中后两者为何被排除）。
- **Consequences**——仅当存在不显眼的下游影响需要点出时（如"选 `Moya` 后所有 `external` 适配器须经其 `Provider`，新代码不得裸 `URLSession`"）。

## 编号

扫描 `docs/adr/` 中现有最大编号 +1。

## 何时提议 ADR（三条全中才提）

1. **难以回头** —— 后续改主意的成本不小。
2. **缺上下文会令人困惑** —— 未来读者看代码会想"为什么偏要这么做？"。
3. **是真实权衡的产物** —— 确有备选，因具体理由选了其一。

若决策易回退，跳过（反正会改回去）；若不令人意外，没人会问为什么；若本无备选，除了"做了显然的事"没什么可记。

### iOS 平台典型够格的 ADR

结合本平台硬红线与 SLOT 取值，下列决策通常够格记 ADR：

- **持久化栈锁定**：WCDBSwift 为唯一持久化栈，排除 `CoreData` / `SwiftData`（golden-path §2.7 硬约定；记录排除理由，避免后人"好心"引入 SwiftData）。证据形态：`Infrastructure/Persistence/{DatabaseManager,EnhancedDatabaseManager}.swift`、`StoryRepository` 独占 `import WCDBSwift`。
- **网络栈选择（SLOT-08）**：`URLSession`（轻量）vs `Moya`（重抽象）二选一。挑选理由与对 `external` 适配器形态的约束值得留痕。
- **RxSwift→SwiftUI 迁移边界（SLOT-01）**：新代码纯 SwiftUI + `ObservableObject`，RxSwift 仅存量只读维护。分界线在哪一层、旧模块何时不再触碰——典型"难回头 + 缺上下文困惑"的边界决策。
- **跨 feature 导航一律收口 `AppCoordinator`**：禁 `view` 间直接 `NavigationLink`（golden-path §2.1/§9 红线）。把"为何不允许局部 push 跳别 feature"记下，挡住下次有人想抄近路。证据形态：`App/Coordinators/AppCoordinator.swift` 的 `@Published activeDestination` + `enum NavigationDestination` + `navigateToStoryDetail(storyId:)`。
- **三方 SDK / LLM provider 接入与凭证策略**：选定 provider、Domain 侧用 `IXxxAdapter` 协议隔离 SDK（活例 `IOnDeviceLLMAdapter`）、凭证不写 secret value（Keychain 引用 / Info.plist 注入 / 默认凭证来源）。
- **错误分层与转换点（SLOT-04）**：WCDBSwift 原始错误在 repository/`external` 边界统一转 `PersistenceError`（活例 `StoryRepository.mapToRepositoryError(_:operation:)`），领域 / 用例抛各自 `enum XxxError`（`StoryError` / `StoryManagementError`）。当转换点或分层策略是经权衡定的，值得记。
- **DI 容器拆分策略**：FactoryKit `extension Container` 按职责拆 `Container+{UseCases,Infrastructure,ViewModels,Coordinators,Domain}.swift`，接口型用 `Factory<any IXxxRepository>`、有状态对象用 `.singleton`、UI ViewModel 的 Factory 标 `@MainActor`。约定本身是团队 canonical，单项目偏离时记 ADR。
- **存量违例的有意保留（SLOT-16）**：决定暂不修某个 Domain 零依赖违例（如 `Domain/Services/ExportTaskManager.swift` 的 `import Combine`、`Domain/Adapters/IImageFromPromptProvider.swift` 的 `import SwiftUI`+`AppKit`），记债 + 不扩散边界。"为何先不修、什么前提下修"是 ADR 的合理内容。

### 不够格的（别记）

- 纯命名 / 目录摆放（`HomeViewModel` 还是 `HomeVM`）——易回退、不意外。
- 单纯遵守已有硬规则（"我们把 private 方法放进了 `private extension`"）——本无备选，没什么可记。
- 一个具体方法签名怎么写——属详细设计合同层，不是架构决策。
