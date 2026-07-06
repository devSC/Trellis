# implementation-trace 合同（Guru iOS 原生平台）

> `implement.md` / implementation-trace 是 detail Gate 的 digest-bearing planning contract——「不是做完感，而是证据感」。
> 装载顺序：先读 `.trellis/spec/guides/golden-path.md`（分层依赖律 + golden-path 锁定），再读本任务详细设计的章节合同（`.trellis/spec/harness/detail/detail-structure-single-source.md` + 命中的 L2），最后把 detail 确认后的执行/验证证据写入 mutable evidence。
> 建议落盘路径：目标仓库 `docs/design/<feature>/implementation-trace.md`。detail 确认后的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`；若必须修改已确认 trace，必须回退 detail Gate 并重新 review/confirm。
> 平台基准：DDD 四层 Domain → App → Infrastructure → UI（Domain 零依赖）；SwiftUI 主 + RxSwift 遗留；FactoryKit DI（`@Injected`）；Repository 模式（接口在 Domain、实现在 Infrastructure）；`enum Error` per domain；AppCoordinator 导航；WCDBSwift 持久化；ViewModel = `ObservableObject` + `@Published`。
> doc_type 一律用 iOS 权威七类：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`。**禁止自创 `transport-handler` / `service` / `controller` / `data-source` 之类的类型名。**

---

## 0. 与详细设计的承接关系（开工前必须建立）

- 每个实现切片承接**至少一个** `UNIT-<slug>` 设计单元（语义 kebab-case 标题，下游引用裸 token）。引用不存在的 UNIT = 幽灵引用，被 gate 断链拦截。
- 每个 UNIT 自带一个 `doc_type`（七类之一）；切片的文件范围必须落在该 doc_type 的 owner 层内（归属硬基准，违反直接 fail）：
  - `view` / `viewmodel` → owner UI 层（`UI/Features/<Feature>/Views/`、`UI/Features/<Feature>/ViewModels/`）
  - `coordinator` → owner App 层（`App/Coordinators/`、`App/DependencyInjection/Container+*.swift`）
  - `usecase` / `domain-model` / `repository` 接口 → owner Domain 层（`App/UseCases/`、`Domain/Entities|ValueObjects|Enums|Errors/`、`Domain/Repositories/IXxxRepository.swift`）
  - `repository` 实现 / `external` → owner Infrastructure 层（`Infrastructure/Persistence/Repositories/`、`Infrastructure/Adapters/`、`Infrastructure/Services/`）
- 行为编号 `BHV-NNN`（来自 prd 标题）通过 UNIT 间接承接；trace 不重新发明行为。

---

## 必含四节

### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 任务切片 | 每片登记：① 承接的设计单元编号（`UNIT-<slug>`，幽灵引用被 gate 拦截）；② `doc_type`（iOS 七类之一）；③ 文件范围（相对路径，落在该 doc_type 的 owner 层内）；④ 完成信号（可验证、非「做完感」）；⑤ 验证方式（编译 / 测试 / lint 命令，见第 3 节）。**每片小到可独立 review**——单 ViewModel、单 UseCase、单 Repository 接口+实现对、单 SwiftUI View 为一片的典型粒度。 |
| 执行顺序 | 按分层依赖**自底向上**排序：`domain-model → repository（接口+实现） → usecase → viewmodel → view + coordinator/external 横切`。这是 golden-path 锁定的写作顺序；横切（`coordinator` 的 DI 装配 / `external` 集成）在被依赖方稳定后接入。人工选择从最小切片开始。 |
| 风险点 | 逐条预判高风险改动并写**验证手段**：① WCDBSwift 表结构/迁移（`ColumnCodable` 变更、`Table` 字段增删）；② FactoryKit DI 装配改动（`Container+*.swift` 改 graph 影响全局单例生命周期）；③ SwiftUI ↔ RxSwift 遗留桥接（`@Published` 与 `Observable` 共存的内存/线程风险）；④ AppCoordinator 导航枚举扩展（`NavigationDestination` 新增 case 的全量 switch 覆盖）；⑤ async/await 与 `MainActor` 线程归属。 |

**计划切片登记示例（表格形态）：**

| 切片 | 承接 UNIT | doc_type | 文件范围 | 完成信号 | 验证方式 |
|------|-----------|----------|---------|---------|---------|
| S1 | `UNIT-story-entity` | `domain-model` | `Domain/Entities/Story.swift`、`Domain/Errors/StoryError.swift` | 实体+不变量+`enum StoryError` 编译通过，零 import（仅 `Foundation`） | `xcodebuild build` + SwiftLint |
| S2 | `UNIT-story-repository` | `repository` | `Domain/Repositories/IStoryRepository.swift`、`Infrastructure/Persistence/Repositories/StoryRepository.swift`、`Infrastructure/Persistence/Models/StoryObject.swift` | 接口在 Domain、实现在 Infrastructure，mapper 独立，错误映射表逐条落地 | `xcodebuild test`（`StoryRepositoryTests`） |
| S3 | `UNIT-story-management-usecase` | `usecase` | `App/UseCases/StoryManagement/IStoryManagementUseCase.swift`、`StoryManagementUseCase.swift`、`StoryManagementError.swift` | 公开方法签名级齐全，只注入 repository 接口，业务错误枚举落地 | `xcodebuild test`（`StoryManagementUseCaseTests`） |
| S4 | `UNIT-home-viewmodel` | `viewmodel` | `UI/Features/Home/ViewModels/HomeViewModel.swift` | `ObservableObject`+`@Published` 三态字段齐全，`@Injected` 注入 usecase 接口 | `xcodebuild test`（`HomeViewModelTests`） |
| S5 | `UNIT-home-view` + `UNIT-app-coordinator` | `view` / `coordinator` | `UI/Features/Home/Views/HomeView.swift`、`App/Coordinators/AppCoordinator.swift`、`App/DependencyInjection/Container+ViewModels.swift` | View 只展示+输入（无业务），导航走 coordinator，DI 装配补齐 | `xcodebuild build` + SwiftLint |

> 横切说明：`coordinator` 切片同时覆盖 FactoryKit DI 装配（`Container+ViewModels.swift` / `Container+UseCases.swift` / `Container+Coordinators.swift`）——新增单元必须有对应 `Factory<I...>` 注册，否则 `@Injected` 运行期解析失败（属可验证完成信号之一）。

### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个任务切片完成时记录下列字段：

- **实际改动文件清单**（相对路径，逐文件）。区分新增 / 修改 / 删除。
- **与计划的偏差**：改了计划外文件 / 没改计划内文件 → **必须写原因**（例如「`Container+UseCases.swift` 计划外修改：新 UseCase 需注册 `Factory`，属 DI 装配必经」）。
- **DI 装配登记**：每个新增的 `viewmodel` / `usecase` / `repository` 实现 / `external` 必须在 `App/DependencyInjection/Container+*.swift` 注册 `Factory`（`self { ... }.singleton` 或非单例形态），并记录注册行位置。禁手动初始化（`init` 直接 new 依赖 = golden-path 违例，记债或回退）。
- **平台约定落地点**：逐项确认本切片触碰的 golden-path 锁定项已落地——
  - FactoryKit `@Injected` 注入（无手动初始化）；
  - Repository 模式（UI/usecase 不直连 WCDBSwift，必经 `IXxxRepository`）；
  - `enum Error` 分层定义（Domain 错误在 `Domain/Errors/`，UseCase 错误在各 UseCase 目录的 `XxxError.swift`，Infrastructure 错误在对应模块）；
  - WCDBSwift 持久化（**禁 CoreData / SwiftData**）；
  - ViewModel = `ObservableObject` + `@Published`；
  - `private` 方法置于 `private extension`。
- **代码生成 / 脚手架记录**：若使用 mock 生成（project-conventions 槽位：手写 → Mockolo）或 R.swift 资源生成，记录跑了哪个命令、产物文件。无代码生成则显式写「本切片无生成步骤（手写实现 + 手写 mock）」。

### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

> `verification-evidence.jsonl` 只写「全部通过」= 反模式。每条必须带**命令 + 结果（测试名级别）**。
> 构建系统基准：本平台为 CocoaPods 工作区（`Podfile` 依赖 SwiftLint 0.31.0 / RxSwift / Moya / SwiftyBeaver 等），主用 `xcodebuild`；纯 SPM 包（Domain 抽离为独立 package 时）可用 `swift build` / `swift test`。两套命令按目标仓库实际构建形态二选一，trace 记录实际所用那套。

| 类型 | 要求 | iOS 命令基线（按实际仓库填实参） |
|------|------|------|
| 编译 / 静态检查 | 切片编译通过；SwiftLint 零新增违例（存量违例按第 4 节记债）。记录命令 + 通过/失败 + 失败处理。 | SPM 包：`swift build`；工作区：`xcodebuild build -workspace StoryVerse.xcworkspace -scheme StoryVerse -destination 'platform=macOS'`；lint：`Pods/SwiftLint/swiftlint lint --strict --reporter emoji`（CocoaPods 集成的 SwiftLint，Debug 配置） |
| 测试 | 每个切片对应测试命令 + 结果**到测试名级别**（不只写「通过」）；新增测试清单逐条列出（`XCTestCase` 子类名 + `test*` 方法名）。 | SPM 包：`swift test --filter <ClassName>`；工作区：`xcodebuild test -workspace StoryVerse.xcworkspace -scheme StoryVerse -destination 'platform=macOS' -only-testing:StoryVerseTests/<ClassName>/<testMethod>` |
| 未验证项 | 无法本地验证的（真机 / 设备能力 / 大模型推理 / TTS 真实音频 / GPU 图像生成 / WhisperKit 设备端表现）→ **显式列出** + 留给哪个环节（Manual QA / 真机池 / 性能基准跑）。 | — |

**测试分层与 doc_type 映射（取证口径，与详细设计「测试映射」八问之七对齐）：**

| doc_type | 主测试层 | 取证要点 |
|----------|---------|---------|
| `domain-model` | unit（`XCTest`） | 不变量 / `enum Error` 等值（`Equatable`）/ 值对象构造校验，纯逻辑无 mock |
| `repository` | unit（mock DatabaseManager，见 `MockDatabaseManager.swift`）+ integration（真实 WCDBSwift，临时库文件） | 错误映射表逐条用例；mapper 双向；CRUD 幂等；`StoryRepositoryTests` / `VoiceProfileRepositoryTests` 为参照 |
| `usecase` | unit（mock repository 接口）——**测试密度最高层** | 每条承接行为 ≥1 成功 + ≥1 失败用例；业务错误枚举逐条；`StoryManagementUseCaseTests` 为参照 |
| `viewmodel` | unit（mock usecase 接口，断言 `@Published` 状态转移） | 事件 → 三态（loading / 数据 / error）转移；订阅取消（无内存泄漏） |
| `view` | 不在此层做结构断言（SwiftUI 视图归 Manual QA / 快照，按需）；逻辑应已下沉 viewmodel | 列入「未验证项」或快照测试（若仓库已有快照基线） |
| `coordinator` | unit（断言 `NavigationDestination` 转移）+ DI 解析冒烟（`Container` 能解析全部新增 `Factory`） | 导航枚举 case 转移；`@Injected` 解析不崩 |
| `external` | unit（mock SDK 边界）+ integration（真实集成留真机/Manual QA） | 错误上抛不吞；SDK 异常 → 业务错误映射；网络/SDK 真实路径列未验证项 |

> 测试框架口径：project-conventions 槽位为「XCTest → Quick/Nimble」。trace 记录本切片实际所用框架；存量 `XCTest`（如 `StoryVerseTests/`）按存量处置，新增切片若已切 Quick/Nimble 则用 `describe/it` 命名，证据仍记到 example 名级别。

**证据登记示例（切片 S3）：**

```
切片 S3 / UNIT-story-management-usecase / doc_type=usecase
- 编译：xcodebuild build -workspace StoryVerse.xcworkspace -scheme StoryVerse -destination 'platform=macOS' → BUILD SUCCEEDED
- 静态检查：Pods/SwiftLint/swiftlint lint --strict → 0 violations（新增文件 3 个）
- 测试：xcodebuild test ... -only-testing:StoryVerseTests/StoryManagementUseCaseTests → 全部 PASS
  · test_createStory_成功_返回持久化Story
  · test_createStory_校验失败_抛StoryManagementError.validationFailed
  · test_deleteStory_找不到ID_抛StoryManagementError.notFound
  · test_observeStories_保存后流发射新列表
- 新增测试：StoryManagementUseCaseTests（4 个 test 方法，mock IStoryRepository + MockSystemStoriesInitializer）
- 未验证项：无（纯 domain 编排，本地全覆盖）
```

### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- **上游缺陷（详细设计错/漏）**：详细设计合同写错或漏（如 UNIT 的错误枚举不全、依赖方向写反、签名与实现对不上）→ 记录后**回退详细阶段修订**，不在 trace / 代码里就地改设计。`implementation-evidence.jsonl` 留回退记录（哪个 UNIT、缺什么、回退动作）。
  - 示例：「`UNIT-voice-repository` 合同未声明 remote 失败回落策略，实现无据可依 → 回退详细设计补编排策略，trace 暂挂该切片。」
- **存量违例触碰**：列出触碰的存量违例条目编号（golden-path / 详细设计的存量豁免清单中登记的违例）+ 处置（绕行 / 顺手修复 / 记债）。iOS 典型存量违例域：
  - SwiftUI 主 + **RxSwift 遗留**桥接代码（迁移中的双轨）；
  - 日志 SwiftyBeaver → OSLog 迁移期的混用；
  - mock 手写 → Mockolo 迁移期的手写 mock；
  - 测试框架 XCTest → Quick/Nimble 迁移期。
  触碰时若不在本切片 scope 内，记债不阻塞；新增代码引入新违例则阻塞（必须修或显式升级）。
- **未决决策**：实现中冒出的新决策点（如「WCDBSwift 表加索引会否影响现有迁移」「某 SDK 仅真机可用，CI 如何 mock」）→ **不私自拍板**，记录并升级人工 Gate。
- **分层依赖律违反（硬 fail，必须当场处置）**：实现中若出现以下任一，立即停止该切片并记录回退动作——
  - Domain 层文件出现非 `Foundation`/标准库 import（Domain 零依赖被破坏）；
  - `view` 直接访问 WCDBSwift / Repository 实现（绕过 viewmodel→usecase→repository）；
  - `view` 间直接导航（未走 coordinator）；
  - 依赖方向逆行（如 `usecase` 反向依赖 `viewmodel`，或 Domain 依赖 Infrastructure 具体实现而非接口）；
  - 手动 `init` 注入替代 FactoryKit `@Injected`。

---

## Gate 判定（实现阶段进 commit 的充要条件）

实现切片可进入 commit，当且仅当：

- **GI-1** `implement.md` 计划合同与 mutable evidence 齐全（计划 / 执行 / 证据 / 阻塞偏差），无空记录、无 TODO 占位。
- **GI-2** 每个切片承接的 `UNIT-<slug>` 均存在于详细设计（无幽灵引用）；`doc_type` 为 iOS 七类之一且文件范围落在该 doc_type owner 层内。
- **GI-3** `verification-evidence.jsonl`：每切片有编译命令结果 + 测试命令结果（**测试名级别**）+ SwiftLint 结果；无「全部通过」式无命令证据。
- **GI-4** golden-path 锁定项逐项落地（FactoryKit `@Injected` 无手动初始化 / Repository 模式 / `enum Error` 分层 / WCDBSwift 无 CoreData·SwiftData / ViewModel=`ObservableObject`+`@Published` / `private` 在 `private extension`）。
- **GI-5** 分层依赖律零违反（Domain 零依赖；Domain→App→Infrastructure→UI 单向；View 不直连持久化、不互相导航）。
- **GI-6** 偏差与存量违例均有记录与处置；未决决策已升级（无私自拍板）。
- **GI-7** DI 装配闭合：每个新增 `viewmodel`/`usecase`/`repository` 实现/`external` 在 `Container+*.swift` 有对应 `Factory` 注册，`@Injected` 可解析。

任一不满足 → 不进 commit；上游结构性缺陷只能回拥有该决策的阶段修订，禁止下游补造。

---

## 反模式

- ❌ trace 在 PR 前一次性补写（失去过程证据意义）。
- ❌ mutable evidence 只写「全部通过」/「编译 OK」（无命令、无测试名、无 SwiftLint 结果）。
- ❌ 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
- ❌ doc_type 自创（写成 `service` / `controller` / `data-source` / `transport-handler`——必须用 iOS 权威七类）。
- ❌ 切片不承接 UNIT 或承接不存在的 UNIT（幽灵引用）。
- ❌ 实现期就地改详细设计 owner / 依赖方向 / scope（应回退详细阶段）。
- ❌ 手动 `init` new 依赖替代 FactoryKit `@Injected`；`view` 直连 WCDBSwift；`view` 间 `NavigationLink` 直跳绕过 AppCoordinator。
- ❌ 用 CoreData / SwiftData 替代 WCDBSwift；用 `class` 普通对象替代 `ObservableObject`+`@Published` 的 ViewModel。
