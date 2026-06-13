---
name: ios-design-grill
description: Guru iOS 原生平台 Gate 前拷问会话（grill-with-docs 的 iOS 适配版）。对照本平台领域模型（golden-path 分层依赖律 Domain → App → Infrastructure → UI、四条硬红线、七类 doc_type 权威口径）与 project-conventions SLOT-01~SLOT-16（含 SLOT-16 存量违例清单）逐行拷问 prd 的 BHV-NNN 行为集合（需求 Gate 前）或 design 概要的归属表（概要 Gate 前），磨尖术语（Story / Chapter / Creation 等领域名 vs 技术名）、压测探边场景（并发写 owner、失败收口层、缓存与网络回退）、与 story-verse-mac 真实代码交叉核对，决策当场固化进产物：行为/范围决策回写 prd、归属决策回写 design §归属表三问、纯术语回写 CONTEXT.md、项目级取值提示走 conventions 修订（需 ADR）。触碰四条硬红线（Domain 零依赖 / 单向无环 / view 间不直接导航 / view·viewmodel 不直连持久化）当场判 fail 并回退到拥有该决策的上游阶段，不在拷问里替对方补造。不替代 trellis-brainstorm（探索生成 prd）、ios-design-*-writing（生成 design 正文）与 ios-design-*-review（互斥 Gate 判定）。
---

# ios-design-grill — Guru iOS Gate 前拷问

> 层级契约：分层依赖律与四条硬红线以 `.trellis/spec/guides/golden-path.md` 为唯一真源；doc_type 七类口径与 owner 层映射以 `.trellis/spec/conventions/index.md` §5 为准；项目槽位取值以 `.trellis/spec/conventions/project-conventions.md`（SLOT-01~SLOT-16）为准；本 SKILL.md 只编排拷问动作与处置规则，不复写规范正文。冲突时 golden-path 硬红线 > conventions index 七类口径 > project-conventions 槽位 > 本文件。

## 做什么

对当前 task 产物（**需求 Gate 前拷问 `prd.md` 的 `BHV-NNN` 行为集合**；**概要 Gate 前拷问 `design.md` §归属表 / full 链 `design-main.md` 第 3 章归属判定表**）发起不留情面的逐分支拷问，直到达成共识可以送审：沿 `Domain → App → Infrastructure → UI` 自底向上逐层走，决策间依赖逐个解开。

- **一次只问一个问题，每个问题附上你的推荐答案**，等用户反馈再继续。
- **能从代码 / spec 找到答案的问题不要问用户——先自己查**（`rg` story-verse-mac 真实类型 / golden-path 红线 / project-conventions 槽位）。
- 拷问的目的不是写设计（那是 writing 的活），也不是给 Gate 结论（那是 review 的活），而是：在送审前把行为说清、把术语磨尖、把归属钉到唯一 owner、把红线违例当场拦下并回退。

## 拷问对照物（领域模型，硬前置装载，任一缺失即终止）

1. `.trellis/spec/guides/golden-path.md` — 分层依赖律（§2.1）与四条硬红线、七类 doc_type 权威口径、§11 禁止清单。拷问归属时的硬基准（"这条行为你打算让 `view` 自己拥有业务规则？§2.1 不允许，回退重判 owner"）。
2. `.trellis/spec/conventions/project-conventions.md` — SLOT-01~SLOT-16 取值与 **SLOT-16 存量违例清单**。先跑 conventions index §3 校验清单 C1~C6；不过则停止拷问，先提示补项目约定（"你说要新建网络层——SLOT-08 钉的是 `URLSession` 还是 `Moya`？取值未就绪不能往下拷问"）。
3. `.trellis/spec/conventions/index.md` §5 — doc_type 七类 → owner 层映射表（`viewmodel`/`view`→UI，`coordinator`→App，`usecase`/`repository` 接口/`domain-model`→Domain，`repository` 实现/`external`→Infrastructure）。
4. 当前任务既有产物：prd 的 `BHV-NNN` 行为集合（拷问需求时）、design §归属表 + 三问理由 + 承接索引（拷问概要时）。
5. 参考项目 `story-verse-mac` 真实代码（交叉核对锚点，先读证实再引用）：`Domain/Repositories/IStoryRepository.swift`（接口零依赖 + `IObservableRepository`）、`Domain/Errors/StoryError.swift`（`enum Error, Equatable`）、`App/UseCases/StoryManagement/StoryManagementUseCase.swift`（usecase 只 `import Foundation`）、`App/Coordinators/AppCoordinator.swift`（`@Published activeDestination` + `enum NavigationDestination`）、`App/DependencyInjection/Container+UseCases.swift`（`Factory<any IXxxRepository>` + `.singleton`）、`Infrastructure/Persistence/Repositories/StoryRepository.swift`（独占 `import WCDBSwift`，WCDB 错误经 `mapToRepositoryError` 转 `PersistenceError`）、`UI/Features/Home/{Views/HomeView.swift,ViewModels/HomeViewModel.swift}`（`@InjectedObject` / `@Injected` 注入）。
6. 仓库根 `CONTEXT.md`（术语表，存在则装载；story-verse-mac 当前**无** `CONTEXT.md`，首个领域术语敲定时按 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) 懒创建）。

## 会话期间（拷问动作清单）

- **对照术语表挑战**：用语与 `CONTEXT.md` 既有定义冲突时立即点破——"术语表里 `Story` 定义为甲，你现在说的『作品』指的是乙——到底哪个？"。术语未入表且属本平台领域概念（`Story` / `Chapter` / `Section` / `Creation` / `VoiceProfile` 等真实领域名）时当场敲定并回写。
- **磨尖模糊语言**：出现含混 / 过载词汇时给出精确候选——"你说『保存故事』——是 `repository.save(story:)` 的 upsert 整聚合，还是只更新 `@Published` 内存态？这是两层不同的事"；"你说『导出任务管理器』——是 `usecase` 编排还是有状态的 `ExportTaskManager`？"。行为命名同步回写 `BHV-NNN` 标题短名（动词 / 动词+宾语，区分 list/one/get/fetch 语义）。
- **doc_type 串台拦截**：对方用 flutter / Go 类型名（`controller` / `page-entry` / `service` / `datasource` / `transport-handler` / `db-dao` / `api-network`）时当场纠正回 iOS 七类——"你说的 `service` 在 iOS 七类里不存在：有状态业务编排归 `usecase`，外部出站合同归 `external`，没有第八类"（conventions index §0 / C4 doc_type 纯净）。
- **具体场景压测（发明探边场景逼出概念边界）**：
  - **唯一写 owner**："`HomeView` 与故事详情页同时在改 `recentStories`——同一份 `@Published` 状态谁是唯一写 owner？两个 ViewModel 都写 = P1，回退重判归属。"
  - **失败收口层**："`StoryRepository` 实现里 WCDBSwift 抛了原始错误——这个错误在哪一层转成 `PersistenceError`？按 SLOT-04 转换点固定在 `external`/repository 边界，不能裸抛到 `view`。"
  - **缓存与网络回退**："`fetchAllFullStories` 缓存空时走网络——这条网络回退是 `usecase` 编排还是 `repository` 实现内部？决定了它归 Domain 还是 Infrastructure。"
  - **并发 / 线程归属**："这个 `@Published` 在 `Task` 里被改——有没有 `await MainActor.run` 回主线程？UI 状态写 owner 的线程语义谁负责？"
- **与真实代码交叉核对**：用户陈述与 story-verse-mac 代码矛盾时当场摆出——"你说 ViewModel 直接持有 `Database`，可 `HomeViewModel.swift` 全是 `@Injected(\.storyManageUseCase)` 经用例，没有任何 `WCDBSwift` import——哪个对？"；"你说 `view` 间用 `NavigationLink` 直跳，可 `AppCoordinator` 的 `navigateToStoryDetail(storyId:)` 才是约定入口——为何要绕过 coordinator？"。
- **决策当场固化（落盘，不只口头）**：
  - 行为 / 范围决策 → 立即更新 `prd.md`（`BHV-NNN` 未决问题 → 已决，附一句依据 + 失败路径 + 验收场景，凑齐需求五要素）；
  - 归属决策 → 立即更新 `design.md` §归属表（owner 落七类之一 + owner 层 + **三问理由**：为何归此层 / 为何不属别人 / 为何需独立存在），并回填承接索引 `chapter_target → detail_doc_type`；
  - 纯术语 → 更新仓库根 `CONTEXT.md`（只做术语表，零实现细节，格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)；不存在则懒创建）；
  - 项目级取值变化（如想把 SLOT-08 从 `URLSession` 改 `Moya`、SLOT-14 测试框架切换）→ **提示走 conventions 修订流程（需 ADR），不在拷问里当场私改** `project-conventions.md`。
- **克制地提议 ADR**（三条全中才提，格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)）：难以回头 + 缺上下文会令未来读者困惑 + 真实权衡的产物。iOS 典型可记 ADR：持久化栈选 WCDBSwift（排除 CoreData/SwiftData 的理由）、网络栈 `URLSession` vs `Moya`、RxSwift→SwiftUI 迁移边界、三方 SDK / LLM provider 接入与凭证策略、跨 feature 导航是否一律收口 `AppCoordinator`。纯命名 / 易回退的小决策不提 ADR。

## 触碰四条硬红线的处置：当场 fail 回退（不可豁免，不在拷问里补救）

拷问中一旦发现对方的行为 / 归属设计**触碰 golden-path §2.1 四条硬红线**，立即停止该分支的"磨语言"，转为**当场判 fail 并回退到拥有该决策的上游阶段**，把违例点、所属红线、回退目标写清，等修订后再继续拷问：

1. **Domain 零依赖**：`usecase` / `IXxxRepository` 接口 / 实体 / 值对象 / `enum Error` 不得 import `SwiftUI` / `Combine` / `AppKit` / `WCDBSwift` / `FactoryKit`，也不 import App·Infrastructure·UI 符号。命中 → fail，回退到归属判定（概要）或行为定义（需求），把"塞进 Domain 的 UI/SDK 能力"重新判到 UI 或 Infrastructure。
   - 取证基准：`IStoryRepository.swift` / `StoryError.swift` / `StoryManagementUseCase.swift` 实测只 `import Foundation`。
   - **存量违例区分**：story-verse-mac 中 `Domain/Adapters/IImageFromPromptProvider.swift`（`import SwiftUI`+`AppKit`）、`Domain/Services/IExportTaskManager.swift` 与 `ExportTaskManager.swift`（`import Combine`）、`Domain/Services/Files/ILocalImageStorageService.swift`（`import AppKit`）是**既有违例**。处置二分：若该违例已登记在 SLOT-16 存量违例清单 → 拷问中标"存量记债、不阻塞本次"，但**新行为不得新增同类违例**；若未登记且本次设计要触碰 / 复制它 → 当场 fail，要求先登记 SLOT-16 或修订，不在拷问里默许扩散。
2. **单向无环**：依赖方向只能 `Domain → App → Infrastructure → UI`，禁反向 / 同层横跳；`usecase → usecase` 仅允许单向无环（活例 `AppInitializationService` 协调多个 usecase）。命中环形 / 反向 → fail，回退归属判定重画依赖边。
3. **view 间不直接导航**：`view` 不得用 `NavigationLink` / push / present 硬跳到另一 feature 的 View，必须走 `AppCoordinator`（改 `@Published activeDestination`，经注入的导航闭包如 `navigateToStoryDetail`）。命中 → fail，回退把导航职责归到 `coordinator`。
4. **view·viewmodel 不直连持久化**：`view` / `viewmodel` 不得 import `WCDBSwift` / repository 实现类 / 直接持 `Database`，只能注入 `IXxxRepository` 接口或 `usecase` 协议。命中 → fail，回退把数据访问归到 `repository` 接口、经 `viewmodel`/`usecase` 中转。
   - **真实反例锚点**：story-verse-mac `HomeView.swift` 第 33、35 行 `@Injected(\.storyManageUseCase)` 与 `@Injected(\.storyRepository)` 直接在 `view` 里注入了 usecase / repository——这是 `view` 越过 ViewModel 直接持业务依赖的存量越界。拷问新设计时若出现同形态（`view` 注入 repository/usecase 而非经 `viewmodel`）即按此红线 fail，要求把依赖收回 `viewmodel`，除非该点已登记 SLOT-16。

> 处置纪律：红线 fail **只能回上游修**——需求阶段缺陷回 brainstorm / prd，归属错误回概要归属判定章重判，**禁止在拷问会话里替对方把违例"圆"过去或下游补造**。回退后产物状态须显式标注"因触碰红线 N 回退，待修订重审"。

## 边界（与官方 trellis 工具及本平台 design-* skill 的职责切分）

- **vs `trellis-brainstorm`（探索 / 生成 prd）**：brainstorm 把模糊意图收敛成 `prd.md` 的 `BHV-NNN` 行为规格、P0/P1、失败路径、验收场景。本 skill **不生成 prd、不补造业务规则**——只对已有 prd 草稿做对抗式拷问；需求侧确有缺陷时回退 brainstorm，不在拷问里凭空生成核心能力。
- **vs `ios-design-overview-writing` / `ios-design-detail-writing`（生成 design 正文）**：writing 编排写作动作、产出概要 / 详细 design 正文（归属表、架构总览、承接索引、合同八问）。本 skill **不写 design 正文**——只拷问已有草稿，把拷问结论以最小回写固化进 writing 已产出的产物（prd / design §归属表 / CONTEXT.md），不替 writing 起草整章。
- **vs `ios-design-overview-review` / `ios-design-detail-review`（互斥 Gate 判定）**：review 做**人工 Gate 判定**（"能否进入下一阶段"），输出 PASS/FAIL 互斥结论，判四层归属是否正确、是否违分层依赖律、承接索引 / 合同是否完备。本 skill **不给 Gate 结论**——拷问出的修订落盘后，仍须走对应 review 取互斥 Gate 结论；拷问是 review 前的"磨稿与排雷"，不是 review 本身。
- **vs `trellis-check`（代码质检 / 实现·审核 Gate）**：`trellis-check` 查代码层质量（`xcodebuild` / SwiftLint / `xcodebuild test`（XCTest 或迁移后 Quick/Nimble）证据、secret 合规、SLOT-16 存量豁免）。本 skill **不产 Swift 代码、不跑构建测试**，只在需求 / 概要文档层拷问。
- **一句话定位**：brainstorm 定「做什么」→ writing 写「分哪层、边界、谁承接」→ **本 skill 在送审前对抗式拷问、磨尖术语、当场固化决策、红线违例当场 fail 回退** → review 人工判「能否进下一阶段」→ trellis-check 判「代码达标」。本 skill 只占 writing 与 review 之间的"送审前排雷"格，越界即停。
- 不进入详细可编码合同层（Swift 方法签名 / `@Published` 字段全集 / `enum Error` 每个 case / `Container` 注册条目 / WCDBSwift 表结构 / SDK 参数 / secret value——那是详细设计与实现阶段的领地）；不私自拍板项目约定（项目级取值走 conventions 修订 + ADR）。
- 产物语言：中文优先（英文仅限代码标识符、命令、路径、框架 / 库名如 `SwiftUI` `FactoryKit` `WCDBSwift` `@Injected` `@Published` `ObservableObject`、协议字段、外部专有名词、原文引用）。

## 运行位置（被 iOS workflow 引用的两个点）

1. **需求 Gate 前**：拷问 `prd.md` 的 `BHV-NNN` 行为集合——逐条核对需求五要素（行为 / 前置条件 / 状态变化 / 失败路径 / 验收场景），磨尖领域术语，把模糊行为压成可归属的清晰行为；缺要素回退 brainstorm 补，齐五要素方可进概要。
2. **概要 Gate 前**：**归属表逐行核对**——每行 `BHV-NNN` 走一遍："这条行为的唯一 owner 是七类哪一类？owner 层对不对？三问理由站得住吗？碰没碰四条硬红线？承接索引 `chapter_target → detail_doc_type` 落了吗（pending L2 类型须 `L2豁免` 声明）？"。逐行核完且无红线违例、无双写 owner、无 doc_type 串台，才提示加载 `ios-design-overview-review` 过概要 Gate。
