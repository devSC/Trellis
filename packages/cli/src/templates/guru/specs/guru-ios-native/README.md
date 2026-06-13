# Guru iOS Native — Spec 库

> 本 spec 库由 guru-template 安装（`trellis init -t guru-ios-native -r <registry>`），落位目标仓库 `.trellis/spec/`（PROTECTED：`trellis update` 永不覆盖项目已填内容）。
> 知识源头：client_agent 仓库方法学母版 + iOS 平台实测仓库 `story-verse-mac`（DDD 四层 + SwiftUI 主 + RxSwift 遗留 + FactoryKit DI + WCDBSwift 持久化）。
> 规则唯一真源原则：writing / review skill 与 `guru_gate` 只**装载**本库规则、不复写；冲突时优先级 `harness/detail/detail-structure-single-source.md`（L1）> `harness/detail/detail-type-*.md`（L2）> `conventions` / `guides` references > SKILL.md。
> **doc_type 权威**：全程只认 iOS 七类（`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`）。禁改名 / 增减 / 换数；禁出现 flutter 的 `controller` / `page-entry` / `db-dao` 或 Go 的 `service` / `transport-handler` 等异平台类型名。本 README 是包导航入口，**只做索引与口径对齐，不承载规则正文**——正文在 `harness/` 与 `guides/golden-path.md`。

---

## 1. 目录树

安装后落位 `.trellis/spec/`；本仓库内同构于 `specs/guru-ios-native/`。

```
guru-ios-native/
├── README.md                                  ← 本文件：包导航（目录树 / harness 职责 / 五阶段关系 / 七类 / 硬规则 / 五道 Gate）
├── guides/
│   ├── index.md                               ← 通用方法入口（只导航）
│   └── golden-path.md                         ← 通用方法 SSOT：分层依赖律 + 各层迷你路径 + 入口决策树 + 禁止清单 + 门禁映射
├── conventions/
│   ├── index.md                               ← 项目约定槽位导航 + SLOT-01~16 全景 + C1~C6 校验 + Gate 消费口径
│   ├── project-conventions.template.md        ← 空槽位模板（新项目起点；不生效、不校验）
│   ├── story-verse.project-conventions.md     ← story-verse-mac 取值样例（仅参考；不生效、不校验）
│   └── project-conventions.md                 ← 【本项目取值唯一权威】init 后由模板填写，所有阶段硬前置只认它
└── harness/
    ├── index.md                               ← 五阶段方法 SSOT 导航
    ├── extraction-template.md                 ← 萃取模板（从存量代码反向提取设计单元）
    ├── overview/
    │   └── overview-structure-single-source.md ← 概要设计 SSOT（行为枚举 → owner 归属表 → 承接索引 → 架构总览六件套 → 技术决策承接）
    ├── detail/
    │   ├── detail-structure-single-source.md   ← 详细设计 SSOT（L1：合同八问骨架 + 章节结构 + Gate 基线）
    │   ├── detail-type-viewmodel.md            ← L2 类型规范：viewmodel（v1 提供）
    │   ├── detail-type-usecase.md              ← L2 类型规范：usecase（v1 提供）
    │   └── detail-type-repository.md           ← L2 类型规范：repository（v1 提供，接口+实现合并一类）
    └── implementation/
        ├── implementation-trace-contract.md    ← 实现 trace 合同（计划 / 执行 / 证据 / 阻塞偏差 四节）
        └── implementation-ios-standard.md       ← 实现 L1 编码标准（LOCK-1~7 / doc_type 七类 / 合同八问 / 实现 Gate / 测试 allowlist / 存量豁免）
```

> 注：`detail/` 下 v1 只提供三份 L2（与 flutter 的 `controller` / `usecase` / `repository-datasource` 一一对应）。其余四类 `domain-model` / `view` / `coordinator` / `external` 暂无独立 L2 文件（`l2_status: pending`），按 L1 合同八问展开；full 链命中 pending 类型时须在 `design-main.md` 显式声明 `L2豁免`（见 §4、§7）。
> `conventions/project-conventions.md` 在本配置包内通常不存在（属项目侧产物）；init 后由 `template` 复制并填写，落位目标仓库 `.trellis/spec/conventions/project-conventions.md`。

---

## 2. harness 文件职责表

每份 harness 文件是其阶段的**单一权威**，经任务的 `implement.jsonl` / `check.jsonl` 注入对应 writing / review skill。装载路径一律用安装后路径（`.trellis/spec/harness/*`）。

| 文件 | 阶段 | 核心职责（写什么、判什么） | 关键产物合同 | 何时读 |
|------|------|---------------------------|-------------|--------|
| `harness/index.md` | 全程 | 五阶段方法 SSOT 导航；不承载规则正文 | — | 入库先读 |
| `harness/overview/overview-structure-single-source.md` | 概要 | 从需求**行为**出发枚举行为空间（禁名词倒推）；判每条行为/状态的**唯一 owner 层 + 三问理由**；建 `chapter_target → detail_doc_type` 承接索引；产出架构总览（一句话架构 / 分层图 / 页面流图 / 核心 UC 表 / UC 承接表 / 时序图策略表）；登记 `technology_decision_handoff[]` | 归属判定表 + 承接索引 + 架构总览六件套 + 技术决策承接清单 | 写/审概要前 |
| `harness/detail/detail-structure-single-source.md`（L1） | 详细 | 合同八问骨架（承接 BHV / 输入输出错误 / 读写状态 / 依赖正反面 / 失败收口 / 事件后置 / 测试映射 / 不得补造）+ 章节结构 + 跨类型 Gate 基线 | 每 `UNIT-<slug>` 八问完整 + 追溯到概要 owner | 写/审详细前（与命中 L2 同读） |
| `harness/detail/detail-type-viewmodel.md`（L2） | 详细 | `viewmodel` 类型特化：`ObservableObject`+`@Published` 三态（loading/数据/error）状态机；`@Injected` 注入 usecase 接口；只读暴露、不回写业务态；导航交 coordinator | viewmodel 章节八问 + 状态转移 + 订阅生命周期 | 命中 viewmodel 单元时 |
| `harness/detail/detail-type-usecase.md`（L2） | 详细 | `usecase` 类型特化：Domain 业务编排，零 UI / 零具体实现依赖；协议签名级接口；`AsyncStream` 流 seed/时序；本域 `enum Error` 收口；`actor` 管可变共享状态；**测试密度最高层** | usecase 章节八问 + 状态写 owner 唯一 + 流生命周期闭合 | 命中 usecase 单元时 |
| `harness/detail/detail-type-repository.md`（L2） | 详细 | `repository` 类型特化（**接口+实现合并一类**）：`IXxxRepository` 在 Domain（零依赖）、实现在 Infrastructure；WCDBSwift 持久化；底层异常→本域 `enum Error` 映射表（细到 `WCDBError.code`）；多写包**事务**；返回域模型不泄漏 Object | repository 章节八问 + 错误映射表 + 事务边界 + mapper 归属 | 命中 repository 单元时 |
| `harness/implementation/implementation-trace-contract.md` | 实现 | **追踪合同**：trace 四节骨架——**计划**（切片承接 UNIT + doc_type + 文件范围 + 完成信号 + 验证方式，自底向上排序）/ **执行**（实际改动 + 偏差原因 + DI 装配登记 + 平台约定落地点）/ **证据**（命令 + 测试名级结果 + SwiftLint）/ **阻塞偏差**（上游缺陷回退 / 存量违例处置 / 未决升级） | 切片承接 `UNIT-<slug>` 无幽灵引用 + 命令级证据 | 实现期随做随记 |
| `harness/implementation/implementation-ios-standard.md`（L1） | 实现 | **L1 编码标准与审核基线**（同源被代码编写与实现审核引用）：golden-path 锁定项 LOCK-1~7（DDD 分层依赖律 / FactoryKit DI / Repository 模式 / `enum Error` 分层 / WCDBSwift 持久化 / `ObservableObject`+`@Published`+Coordinator 导航 / `private extension`，均不可豁免）+ doc_type 权威七类 + 可编码合同八问 + 实现顺序（自底向上 Phase 0~6）+ 实现 Gate（编译/测试名级/SwiftLint 证据）+ 测试边界 allowlist + 存量豁免口径 | LOCK-1~7 零违反 + 合同八项有代码锚点或 `blocked` 依据 + 命令级证据 | 实现期与 trace-contract 同读 |
| `harness/extraction-template.md` | 反向 | 从存量代码反向萃取设计单元（补建缺失的概要/详细文档时用） | — | 给存量补文档时 |

> golden-path 横向支撑：上述任一阶段开工前都先读 `.trellis/spec/guides/golden-path.md`（分层依赖律是归属判定与 Gate 的硬基准）；项目槽位取值读 `.trellis/spec/conventions/project-conventions.md`（C1~C6 不过即「项目约定未就绪」，硬前置不通过）。

---

## 3. 与五阶段 workflow 的关系

guru-client workflow 的每个阶段从本库装载规则（装载路径=安装后路径）：

```
需求(prd.md)         ← 需求三件套 SSOT（五要素：行为 / 前置条件 / 状态变化 / 失败路径 / 验收场景；经 jsonl 引用）
概要(design §概要)   ← .trellis/spec/harness/overview/overview-structure-single-source.md
                       （归属表 + chapter_target→detail_doc_type 承接索引 + technology_decision_handoff[]）
详细(design §详细)   ← .trellis/spec/harness/detail/detail-structure-single-source.md（L1）
                       + 命中类型的 .trellis/spec/harness/detail/detail-type-{viewmodel,usecase,repository}.md（L2）
实现(implement)      ← .trellis/spec/guides/golden-path.md
                       + .trellis/spec/harness/implementation/implementation-trace-contract.md（trace 四节）
审核(check)          ← 各 SSOT 审核基线章节 + .trellis/spec/conventions/project-conventions.md 的 SLOT-16 存量豁免
```

**轨道分流**：task.json `guru_chain`（`guru_after_create` 默认 `full`）决定产物形态。

- **full 链**（核心玩法/付费/广告/存档/权限/数据采集等高风险）：目录级设计包 `docs/design/<feature>/{README.md, design-main.md, chapters/<slug>.md}`，写入 task.json `design_package`；承接索引每条落到章节文件，Gate 查索引↔文件双向闭合。
- **light 链**（`client-small-iteration-dev` 分流且获用户同意后显式降级）：任务内单文件 `design.md` §概要/§详细。

`guru_gate.py` 按链型自动切换检查口径；`trace-matrix <task_dir> --write` 据 `BHV-NNN` / `UNIT-<slug>` 裸 token 生成「行为×归属×单元×测试×切片」矩阵，**断链（幽灵引用 / 无承接行为 / 孤儿单元）被 Gate 拦截**。

**写作顺序（自底向上，与分层依赖律一致）**：

```
domain-model  →  repository  →  usecase  →  viewmodel  →  view + coordinator/external（横切）
```

层级 checkpoint：Domain（domain-model / repository 接口 / usecase）固化后核对 UNIT↔BHV 承接闭合、状态写 owner 唯一、usecase 单向无环；Infrastructure（repository 实现 / external）核对数据依赖全有承接、SLOT-04 错误转换点一致；UI（view / viewmodel）核对只调用稳定 Domain 行为、导航走 coordinator。

> 编号纪律：行为 `### BHV-NNN <短名>`（prd 标题，NNN 数字，创建后不复用不重排、删除留洞）；设计单元 `### UNIT-<slug>`（详细标题，语义 kebab-case）。归属表、详细合同、测试映射、实现切片对行为/单元的引用一律写**裸 token**。

---

## 4. doc_type 七类（权威，全程唯一）

详细设计承接索引的 `detail_doc_type` **只能取以下七类**（以 IOS_BRIEF 为权威，禁改名/增减/换数）。owner 层是分层依赖律的硬基准。

| doc_type | 覆盖对象 | owner 层 | L2 状态 | flutter 方法学映射（**不照抄类型名**） |
|----------|---------|---------|:---:|------|
| `viewmodel` | UI 层 `ObservableObject`+`@Published` 状态容器（事件→三态、流订阅） | UI | **v1 提供** | controller |
| `usecase` | Domain 业务编排（零 UI 依赖、有状态业务流程、响应式发射） | Domain | **v1 提供** | usecase |
| `repository` | Domain `IXxxRepository` 接口 + Infrastructure 实现（**合并一类**） | Domain（接口）/ Infrastructure（实现） | **v1 提供** | repository-datasource |
| `domain-model` | Domain 实体 / 值对象 / `enum Error` / 不变量（零依赖、可被任意层导入） | Domain | pending | （无直接对应，flutter 散在 model） |
| `view` | UI 层 SwiftUI `View`（只展示+输入，无业务） | UI | pending | page-entry |
| `coordinator` | App 层 `AppCoordinator` 导航 + FactoryKit DI 装配（`Container+*.swift`） | App | pending | （flutter 拆 binding+routes） |
| `external` | Infrastructure 外部集成（网络 / SDK / WCDBSwift 持久化 / 第三方） | Infrastructure | pending | external-platform / api-network / db-dao |

**v1 L2 供给**：`.trellis/spec/harness/detail/detail-type-{viewmodel,usecase,repository}.md`，与 flutter 三类 L2 一一对应。

**pending 四类**（`domain-model` / `view` / `coordinator` / `external`）：无独立 L2，按 L1 合同八问展开，文档头标 `l2_status: pending`。**full 链命中 pending 类型时，必须在 `design-main.md` 显式声明 `L2豁免：<doc_type> 理由：…`（含按八问展开的风险与补齐计划）**，否则 Gate 拦截；首选先补对应 L2 再进详细设计。

> owner 层归属对照（实现 trace 文件范围硬基准，违反直接 fail）：`view`/`viewmodel`→UI 层（`UI/Features/<Feature>/{Views,ViewModels}/`）；`coordinator`→App 层（`App/Coordinators/`、`App/DependencyInjection/Container+*.swift`）；`usecase`/`domain-model`/`repository 接口`→Domain 层（`App/UseCases/`、`Domain/{Entities,ValueObjects,Enums,Errors}/`、`Domain/Repositories/IXxxRepository.swift`）；`repository 实现`/`external`→Infrastructure 层（`Infrastructure/Persistence/Repositories/`、`Infrastructure/Adapters|Services/`）。

---

## 5. 硬规则速览（golden-path 锁定，任何阶段不可豁免）

以下为**平台级硬规则**（归属硬基准），任何项目约定槽位取值不得与之冲突；违反 = review 直接 fail。完整正文与门禁映射见 `.trellis/spec/guides/golden-path.md`。

| # | 硬规则 | 正向锚点（story-verse-mac 实测） | 违反判级 |
|---|--------|----------------------------------|:---:|
| H1 | **DDD 四层 + Domain 零依赖**：依赖方向 `Domain → App → Infrastructure → UI` 单向；Domain 层只 import `Foundation`/标准库，可被任意层导入 | `Domain/{Entities,Repositories,Errors}` 协议文件无 `WCDBSwift`/`FactoryKit`/`SwiftUI` import | P1 |
| H2 | **FactoryKit `@Injected` DI**：禁手动 `init`/`new` 装配业务依赖；DI 装配集中在 `coordinator`（`Container+*.swift`） | `Container+Infrastructure.swift` 注册 `Factory<any IStoryRepository>`；usecase/viewmodel 用 `@Injected(\.xxx)` 取用 | P1 |
| H3 | **Repository 模式强制**：`IXxxRepository` 接口在 Domain、实现在 Infrastructure；**接口实现分文件**；UI/usecase 不直连持久化，必经接口 | `Domain/Repositories/IStoryRepository.swift` + `Infrastructure/Persistence/Repositories/StoryRepository.swift` | P1 |
| H4 | **`enum Error` 分层定义**：每个 domain 自有错误枚举；底层异常（`WCDBError`/`URLError`/SDK）在 `external`/repository 实现内收口映射后再上抛，不裸抛 | `Domain/Errors/StoryError.swift`、`PersistenceError`；`StoryRepository.mapToRepositoryError(_:operation:)` 单点转换（对齐 SLOT-04） | P1 |
| H5 | **WCDBSwift 持久化**：禁 `CoreData` / `SwiftData`；持久化经 `Table<EntityObject>`（`TableCodable`） | `Infrastructure/Persistence/DatabaseManager.swift`、`EnhancedDatabaseManager.swift` | P1 |
| H6 | **`ViewModel = ObservableObject + @Published`**：状态写 owner 唯一；三态（loading/数据/error）经 `@Published` 暴露 | `UI/Features/<Feature>/ViewModels/*ViewModel.swift` | P1 |
| H7 | **导航走 `coordinator`**：禁 `view` 间直接导航（`NavigationLink` 直跳）；导航集中 `AppCoordinator` | `App/Coordinators/AppCoordinator.swift` 的 `NavigationDestination` 枚举 | P1 |
| H8 | **多写包事务**：一个行为涉及多表/批量/级联写时包进单一事务（中途失败全回滚） | `StoryRepository.save` 用 `performTransaction` 原子写 `StoryObject`+`StorySummaryObject` | P1 |
| H9 | **可变共享状态线程安全**：跨 `Task` 共享的可变状态用 `actor` 封装，禁裸 `var` 跨并发上下文读写 | usecase 内 `private actor StateManager` | P1 |
| H10 | **`private` 方法在 `private extension`**：私有辅助集中 `private extension XxxType` 或 `// MARK: - 私有方法` 段 | 代码组织规范（`Swift_代码组织规范.md` 口径） | P2 |

**项目约定槽位**（取值见 `project-conventions.md`，编号体系与 `conventions/project-conventions.template.md` canonical 一致 SLOT-01~SLOT-16，不在硬规则里钉死、只在硬规则未覆盖的自由度上取值）：SLOT-01 UI 框架基线 / ViewModel 形态（SwiftUI 主+RxSwift 遗留→纯 SwiftUI，`ObservableObject`+`@Published`）/ SLOT-02 DDD 四层目录分界与归属 / SLOT-03 接口与命名约定（`IXxx` 前缀，接口实现分文件）/ SLOT-04 错误类型与收口位置（`enum Error` 分层，转换点在 repository/external 边界）/ SLOT-05 FactoryKit DI 注册规范 / SLOT-06 持久化方案（WCDBSwift，禁 CoreData/SwiftData）/ SLOT-07 导航与 Coordinator / SLOT-08 网络层（`URLSession`/`Moya` 二选一）/ SLOT-09 日志（`SwiftyBeaver`→`OSLog`）/ SLOT-10 JSON 解析与修复策略（修复点固定在 `external`）/ SLOT-11 主题（`ThemeManager` 单例，`view` 禁硬编码尺寸/色值）/ SLOT-12 i18n（同步脚本人工受控，**agent 禁自动执行**）/ SLOT-13 feature 模块结构（`UI/Features/<Feature>/`）/ SLOT-14 测试约定 + mock 生成（`XCTest`→`Quick`/`Nimble`，手写→`Mockolo`）/ SLOT-15 构建自动化（`Fastlane`）/ SLOT-16 存量违例清单（存量豁免唯一数据源）。槽位全景与 C1~C6 校验见 `conventions/index.md`。

---

## 6. 五道 Gate 表

五阶段工作流逐阶段 Gate；`guru_gate.py` 按 `guru_chain` 切换口径。**前置永远先过**：`project-conventions.md` 校验清单 C1~C6 不通过 → 任何阶段判「项目约定未就绪」，硬前置不通过、不展开本阶段判定。

| Gate | 阶段 | 通过的充要条件（缺即拦截） | 失败处置 |
|------|------|---------------------------|---------|
| **G-需求** | 需求 | **需求五要素**齐全：每条 `BHV-NNN` 行为有 前置条件 / 触发 / 状态变化 / 失败路径 / 验收场景；行为粒度可直接实现、有触发者与候选 owner、链路无断链、同文档粒度一致 | 缺要素回需求阶段补；禁下游补造业务规则 |
| **G-概要** | 概要 | **归属判定表**（每行为唯一 owner 层 + 三问理由，无分层依赖律违例）+ **承接索引**（`chapter_target → detail_doc_type` 覆盖全部 owner，full 链逐条落 `chapters/<slug>.md`）+ **架构总览六件套**（一句话架构 / 分层图 / 页面流图或 N/A / 核心 UC 表 / UC 承接表 / 时序图策略表，图中组件与归属表一致）+ `technology_decision_handoff[]` 字段完整、无「未选定但已被下游引用」 | 归属错/名词倒推/索引脱节 → 重做对应章节；上游缺陷回需求 |
| **G-详细** | 详细 | **合同八问**逐 `UNIT-<slug>` 完整（承接 BHV / 输入输出错误 / 读写状态 / 依赖正反面 / 失败收口 / 事件后置 / 测试映射 / 不得补造）+ 追溯到概要 owner + `BHV-NNN`/`UNIT-<slug>` 无断链；命中类型对齐其 L2；**pending L2 类型须 `L2豁免` 声明或先补 L2**；doc_type 纯净（七类内、无串台） | 八问缺项/越界补造 → 回 chapter_loop 审修；doc_type 串台 → 改回七类 |
| **G-实现** | 实现 | **trace 四节**齐全（计划/执行/证据/阻塞偏差，无空章节、无 TODO）+ 切片承接 UNIT 无幽灵引用、文件范围落在该 doc_type owner 层 + **命令级证据**（编译 + 测试名级结果 + SwiftLint，无「全部通过」式空证据）+ golden-path 锁定项逐项落地（H1~H10）+ 分层依赖律零违反 + DI 装配闭合（新增单元在 `Container+*.swift` 有 `Factory` 注册、`@Injected` 可解析） | 任一不满足不进 commit；结构性缺陷回拥有该决策的阶段，禁下游就地改设计 |
| **G-审核** | 审核 | 先证据后结论（每 finding 带章节锚点/缺失对象）；severity 分级 P1（违硬约束/Gate 项缺失，阻塞）/ P2（理由不足、索引不全、图表不一致）/ P3（表述建议）；**存量豁免**仅适用实现期代码违例——SLOT-16 清单内触碰记债不阻塞、清单外新增违例阻塞；概要/详细文档本身无存量豁免 | 局部修订（补行为/理由/索引/图）就地改；结构性错误（owner 大面积错位、名词倒推、口径分裂）重做章节 |

> Gate 互斥分支：前置失败只输出前置缺口与修复动作，不展开逐章判定；前置通过才逐条 findings + 结构概况 + 互斥结论。缺陷只能回上游修——审核发现 doc_type 串台、归属错、合同越界，回到拥有该决策的阶段修订，禁止在下游补造。
