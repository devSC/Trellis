---
name: ios-implementation-guru-review
description: 按通用 golden-path 与实现 trace 合同审核 Guru iOS 原生平台（SwiftUI + DDD 四层）代码改动，判定能否进入 PR。核查与详细设计单元（UNIT-<slug>）合同八问的一致性、分层依赖律（Domain → App → Infrastructure → UI 单向，Domain 零依赖）与 FactoryKit DI / Repository 模式 / enum Error 分层 / WCDBSwift 持久化 / ObservableObject+@Published 等 golden-path canonical、验证证据（xcodebuild build/test、SwiftLint）完整性、注释/日志/文档路径追溯、本地化/隐私合规红线，并执行存量豁免判定（SLOT-16 内记债不阻塞、清单外新增违例阻塞）。标准口径住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`，本 skill 只审核取证、不重定义规则。doc_type 严格用 iOS 权威七类（viewmodel/usecase/repository/domain-model/view/coordinator/external），禁止照抄 flutter 的 controller/page-entry/db-dao 或 Go 的 transport-handler/service。
---

# iOS 实现审核

> 用于用户要求「审核 iOS 原生实现是否对齐详细设计」「检查 Swift 代码是否按详细设计落地」「实现阶段门禁审核」「review iOS implementation」时。
> 本 skill 只做审核与取证，**不默认改代码**。若用户要求「审核并修复」，先输出 Findings，再按用户确认或明确指令进入修复。
> 平台形态：DDD 四层 `Domain → App → Infrastructure → UI`（Domain 零依赖）；SwiftUI 主 + RxSwift 遗留；FactoryKit DI（`@Injected`）；Repository 模式（接口在 `Domain/Repositories/`、实现在 `Infrastructure/Persistence/Repositories/`）；`enum Error` per domain；`AppCoordinator` 导航；WCDBSwift 持久化；ViewModel = `ObservableObject + @Published`。
> doc_type 一律用 iOS 权威七类：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`。**禁止自创 `transport-handler` / `service` / `controller` / `page-entry` / `db-dao` / `api-network` / `datasource` / `manager` / `handler` 之类的类型名**——出现即归属红线。

## 装载顺序（硬前置，任一失败即终止并仅输出前置缺口）

1. 必须先读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（编码规则与判定基准唯一来源：§2.1 分层依赖律、§3~§9 各 doc_type 迷你路径、§2.3 FactoryKit DI 策略、§2.5 enum Error 分层、§2.6 private extension 组织、§2.7 WCDBSwift 持久化、§11 禁止清单）。不可用 → 终止并提示先安装 guru iOS 原生 spec 模板。
2. 读取同级标准包 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（实现 trace 过程合同：必含四节口径 + 实现 Gate `GI-1~GI-7` + doc_type↔测试分层映射表 + 反模式）与 `.trellis/spec/harness/index.md`（§3 doc_type 权威七类表、§4.1 编号纪律 BHV/UNIT、§4.3 合同八问、§4.4 trace 四节、§6 五道 Gate 口径、统一红线）。
3. 读取目标仓库 `.trellis/spec/conventions/project-conventions.md`，先跑 Pre-Dev 校验清单 C1~C6；**重点装载 SLOT-16 存量违例清单**（存量豁免判定的唯一数据源）与本仓库各槽位取值（UI 框架 SwiftUI 主+RxSwift 遗留→纯 SwiftUI / 网络层 URLSession·Moya / 日志 SwiftyBeaver→OSLog / JSON 修复策略 / 测试框架 XCTest→Quick·Nimble / i18n / 主题 ThemeManager / feature 模块结构 / mock 生成 手写→Mockolo / 构建自动化 Fastlane），并确认项目 logger / logging helper / 日志门面和隐私字段约定。槽位缺失或 C1~C6 未过 → 前置失败。
4. 定位审核对象：被审改动（diff/分支）、本任务承接的详细设计单元（full 链 `design_package/chapters/*.md` 的 `UNIT-<slug>`；light 链 `design.md` §详细）、`implement.md`（trace 四节）。trace 缺失 → 前置失败（实现 Gate 的证据载体不存在，不进入符合性判断）。
5. 命中需要项目级取值才能判定的项（如 lint 是否真按 SwiftLint 规则集跑、网络栈是否落在 `[SLOT-network]`、新代码是否禁引入 RxSwift、mock 是否按 `[SLOT-mock]` 生成），其取值只能来自 project-conventions 槽位与仓库真实代码，**不得从详细设计正文或参考工程习惯推断**。

前置全部通过后，才进入下面的执行流程。

## 执行流程（D 步骤诊断）

> 审核范围先规范化为 `BHV-NNN/UNIT-<slug> → doc_type(七类) → 详细设计单元 → code_asset`；目标集合来自概要承接索引（`chapter_target → ios doc_type`）与本任务计划，**不得按代码文件名反推 `UNIT-<slug>`**。

### D1 合同一致性 / 八问闭合（对应 harness §4.3 合同八问 + Gate `trace-matrix` 切片挂 UNIT）

diff 与详细设计单元逐一对照——

- **承接行为（八问①）**：每个改动切片是否回指真实 `BHV-NNN`/`UNIT-<slug>`；引用了 prd 不存在的 `BHV-NNN`（幽灵行为，`unit_ghost_bhv`）或详细设计不存在的 `UNIT-<slug>`（幽灵单元，`slice_ghost_unit`）= 断链，P1。
- **输入/输出/错误（八问②）**：Swift 签名级对照——方法名/参数/返回类型/`async throws`、`domain-model` 的实体/值对象字段、`enum XxxError` 的每个 case 是否与代码一致；`viewmodel` 须逐 `@Published` 字段核对名称/类型/初始值/写入时机与 loading·empty·error 三态去向。合同外新增的导出类型/`public` 方法/`@Published` 字段、未实现的承接行为，列差集。
- **状态读写（八问③）**：写 owner 与概要归属一致——业务状态归 `usecase`、页面状态归 `viewmodel`；**禁两个 viewmodel 写同一业务状态**；是否出现归属外的写。
- **依赖出入边（八问④）**：`view` 不发起导航·不访问持久化；`viewmodel` 只注入 `usecase`/`IXxxRepository` 接口、不碰实现类/`DatabaseManager`/网络类；`usecase` 只注入 `repository`/其它 `usecase`/`external` 接口——见 D2。
- **失败收口（八问⑤）**：每条失败路径处置（重试/降级/上抛/用户提示）+ 错误转换位置（底层异常 → `enum Error` 映射表逐行对应一条失败 BHV）——见 D2 错误契约。
- **事件/后置（八问⑥）**：`@Published` 发射 / Combine·RxSwift 流时序 / 埋点 / 导航动作（去哪个 `NavigationDestination` case、带什么参数）/ 副作用是否落地或显式声明无。
- **测试映射（八问⑦）**：见 D4。
- **不得补造（八问⑧）**：实现是否猜测/发明了详细设计未定义的合同（如 `view` 擅自决定业务规则、`usecase` 擅自决定持久化介质、`viewmodel` 擅自决定缓存策略、`repository` 实现擅自散写 SQL 字面量）= P1。
- trace §4 是否记录与计划的偏差与处置；上游合同错漏（八问缺错误枚举、签名与实体不符、依赖方向写反、测试映射漏失败路径）应**回退详细阶段修订**而非就地改设计，trace 留回退记录。

### D2 分层依赖律与 canonical（对应 golden-path §2/§11 锁定项 + 统一红线，逐项检查改动代码）

- **import 方向（§2.1，归属硬基准，违反直接 fail）**：依赖只能 `Domain → App → Infrastructure → UI` 单向。逐项查改动文件 import——
  - `Domain/` 下文件出现非 `Foundation`/纯值类型库 import（`import SwiftUI` / `import WCDBSwift` / `import FactoryKit` / `import Moya`）= Domain 零依赖破坏，P1（`grep import` 应只见 `Foundation`）。
  - `view` 间直接导航（跨 feature `NavigationLink(destination: OtherFeatureView())`）绕过 `AppCoordinator` = P1。
  - `view` / `viewmodel` 直接访问持久化或 import repository 实现类/`WCDBSwift`（只能注入 `IXxxRepository`/`usecase` 协议）= P1。
  - `usecase` import SwiftUI / 持 `@Published` / 反向依赖 `viewmodel`，或 `usecase` 环形·双向依赖 = P1。
  - `repository` 实现绕过 `external`/`DatabaseManager` 在业务方法里散写 SQL 字面量 = 违例。
- **接口/实现分离（§2.2，不可豁免）**：`usecase`/`repository`/`external` 适配器接口（`IXxx`，`I` 前缀强制）与实现必须分两个文件；接口落 `Domain/`，实现落对应 owner 层目录；混一文件 = P1。`view`（struct）/`viewmodel`（class）不强制接口分离。
- **FactoryKit DI 策略（§2.3，团队栈级 canonical）**：依赖经 `@Injected(\.xxx)` / `@InjectedObject(\.xxx)` 注入，唯一容器 `extension Container` 的 `Factory<T>`；**禁业务类里手动 `new`（`XxxUseCase(...)` 直接构造）、禁 `view` 的 `body` 里 init ViewModel、禁用 `Xxx.shared` 顶替可注入业务依赖** = P1（例外：`ThemeManager.shared`/`ToastManager.shared`/`Logger` 等纯横切工具单例）。UI 相关 ViewModel 的 Factory 须 `@MainActor`；新增 `viewmodel`/`usecase`/`repository` 实现/`external` 须在 `Container+*.swift` 有对应 `Factory` 注册（见 D4 GI-7）。
- **enum Error 分层（§2.5）**：每域独立 `enum XxxError: Error`；需测试比较的实现 `Equatable`；`domain-model`/`usecase` 抛领域错误，`repository` 实现/`external` 抛 `PersistenceError` 或域错误，**不得把 `WCDBSwift` 原始错误裸抛到 UI**——边界须转换为 `PersistenceError` 或具体 case = P1。
- **private extension 组织（§2.6）**：`private` 方法/属性必须落 `private extension`（带 `MARK` 分组），不得与 `public`/`internal` 混合声明；违反 = 违例（极简类/协议扩展/测试类/自动生成代码放宽）。
- **WCDBSwift 持久化（§2.7，红线）**：唯一持久化栈经 `DatabaseManager`/`EnhancedDatabaseManager`；用 CoreData/SwiftData 替代 = P1（不可豁免）；表/列定义集中在 `Persistence/Entities|Models`，迁移逻辑集中，不散落业务方法。
- **本地化（§7）**：`view` 不硬编码用户可见文案（须走 `Localizable.strings`/`R.string.localizable`，按 `[SLOT-i18n]`）= 违例。
- **主题（§7/§11）**：颜色/尺寸不硬编码、经 `ThemeManager`（按 `[SLOT-theme]`）。
- **项目槽位律**：网络层走 `[SLOT-network]` 选定栈（URLSession/Moya）、日志走 `[SLOT-logging]`、JSON 修复走 `[SLOT-json-repair]`；feature 落 `[SLOT-feature-structure]` 目录、repository 实现落 `Infrastructure/Persistence/Repositories/`；新代码不得引入 RxSwift（若 `[SLOT-ui-framework]` 定纯 SwiftUI）。

### D3 存量豁免判定（逐违例必做，对应 harness §6 审核 Gate）

D1/D2 发现的每个违例对照 SLOT-16 清单——

- **命中清单且未扩大违例面** → tech-debt 注记，**不阻塞**（标注关联 `[SLOT-NN]` 编号与计划处置）。iOS 典型存量违例域：SwiftUI 主 + RxSwift 遗留桥接（迁移中双轨）、日志 SwiftyBeaver→OSLog 混用、mock 手写→Mockolo、测试框架 XCTest→Quick/Nimble、个别遗留 `Impl` 后缀实现类。
- **清单外，或扩大了违例面** → **新增违例，P1 阻塞**（例：新代码让 `view` 直连 WCDBSwift、新 `usecase` 反向 import SwiftUI、新引入 CoreData/SwiftData、新代码手动 `new` 替代 `@Injected`、新增 RxSwift 依赖于纯 SwiftUI 仓库、新增跨 feature 硬 `NavigationLink`、新增硬编码用户可见文案）。
- **改动修复了清单条目** → 标注「可从 SLOT-16 移除」并指明被修复的违例（如某遗留 ViewModel 由 RxSwift 改为 `@Published`）。
- 触碰存量但绕行（不修）须在 trace §4 写「为何不修」并挂 `[SLOT-NN]`；混入业务 diff 而不挂编号 = P2 起步。

### D4 证据核查（对应 trace §3 + Gate `GI-1`/`GI-3`，强调「证据感而非做完感」）

> 构建系统二选一按目标仓库实际形态：CocoaPods 工作区（`xcodebuild`，SwiftLint 经 Pods 集成）或纯 SPM 包（`swift build`/`swift test`）。trace 记录实际所用那套。

- **trace 四节齐全且非空（GI-1）**：计划节有 `UNIT-<slug>` 承接 + doc_type/文件范围 + 完成信号 + 验证方式；执行节有改动文件清单 + 偏差原因 + DI 装配登记；证据节有命令级记录；阻塞节如无则显式写「无」。缺任一节或留 TODO 占位 = 实现 Gate 不放行（P1）。
- **编译证据**：`xcodebuild build -workspace <App>.xcworkspace -scheme <App> -destination 'platform=macOS'`（或 SPM 包 `swift build`）贴命令 + 结果（`BUILD SUCCEEDED`/退出态）；只写「编译通过」无命令 = 证据不可信（P2 起步）。引入的编译失败未收口 = P1。
- **静态检查证据**：SwiftLint（`Pods/SwiftLint/swiftlint lint --strict` 或 `swiftlint`，按 `[SLOT-lint]`）逐条通过/失败 + 新增文件零新增违例；存量违例按 D3 记债。只写「lint 通过」无命令/无 violations 计数 = P2 起步。
- **测试证据（GI-3）**：测试名级别结果（XCTest 如 `test_createStory_校验失败_抛StoryManagementError.validationFailed`；Quick/Nimble 到 example 名级），**不只写「全部通过」**；覆盖承接 UNIT/BHV 的成功路径 + **全部失败路径**；新增测试清单（`XCTestCase` 子类名 + `test*` 方法名）可追溯到 `UNIT-<slug>`/`BHV-NNN`。按 doc_type↔测试分层映射核对——
  - `domain-model`：unit（不变量/`enum Error` 等值/值对象构造，纯逻辑无 mock）。
  - `repository`：unit（mock `DatabaseManager`，错误映射表逐条 + mapper 双向 + CRUD 幂等）+ integration（真实 WCDBSwift 临时库，多为未验证项）。
  - `usecase`：unit（mock `IXxxRepository` 接口）——**测试密度最高层**，每条承接行为 ≥1 成功 + ≥1 失败，业务错误枚举逐条。
  - `viewmodel`：unit（mock usecase 接口，断言 `@Published` 三态转移 loading/数据/error + 订阅取消无泄漏）。
  - `view`：不在此层做结构断言（逻辑应已下沉 viewmodel），列入未验证项或快照测试（若有基线）。
  - `coordinator`：unit（`NavigationDestination` 转移）+ DI 解析冒烟（`Container` 能解析全部新增 `Factory`）。
  - `external`：unit（mock SDK 边界，错误上抛不吞）+ integration（真实 SDK/网络留真机/Manual QA）。
  漏失败路径用例 = P2 起步；高风险链路（导航 case 覆盖/WCDBSwift 迁移/SDK 错误转换/RxSwift↔SwiftUI 桥接/`@MainActor` 线程归属）漏测 = P1。
- **可复跑抽查**：抽至少 1 条 trace 中声明的命令实际复跑，结果与记录不符 = 证据造假（P1）。
- **代码生成/脚手架记录**：启用 mock 生成（`[SLOT-mock]` 手写→Mockolo）或 R.swift 资源生成且触发条件满足时，须有生成命令与产物清单；未用生成则 trace 须写「本切片无生成步骤（手写实现 + 手写 mock）」，不得留空。
- **依赖整洁**：`Podfile`/`Podfile.lock`（CocoaPods）或 `Package.swift`/`Package.resolved`（SPM）变更须记 diff；新增第三方库须落在 project-conventions 已批准槽位（禁被锁框架，如纯 SwiftUI 仓库新增 RxSwift）。
- **未验证项**：无法本地验证的（真机/设备能力/大模型推理/TTS 真实音频/GPU 图像生成/WhisperKit 设备端表现/真实 WCDBSwift 唯一约束/RxSwift 桥接内存与线程）须显式列出并指明移交环节（Manual QA / 真机池 / 性能基准跑 / CI），不得隐瞒。

### D5 注释/日志/文档追溯核查（维护性证据）

检查实现是否能让后续维护者从代码回到设计决策，并能在真机/线上问题中定位关键路径。

- **核心定义追溯**：新增核心类型、public/internal API、ViewModel、UseCase、Repository 接口与实现、domain-model、Coordinator、external adapter、跨层 DTO/状态定义，必须有 Swift DocC 风格 `///` 或等价注释说明职责、承接的 `UNIT-<slug>` / `BHV-NNN`；必要时附设计文档相对路径（`docs/design/.../chapters/<slug>.md` 或任务内 `design.md` 锚点）。缺失通常为 P2；高风险链路或新增核心 owner 完全无追溯为 P1。
- **复杂逻辑解释**：非显然业务分支、错误映射、WCDB 迁移、SwiftUI↔RxSwift 桥接、`MainActor`/异步竞态、DI 装配、导航枚举、降级/恢复、生命周期处置必须解释"为什么这样做"，不能只靠代码形状猜意图。缺失按 P2 处理。
- **日志覆盖**：关键流程日志应覆盖入口、成功收口、失败/降级、重试/恢复、外部依赖边界、DI/导航/持久化关键边界；必须复用 SLOT-09 选定的 `ILogger`/`Logger`/OSLog 或项目日志门面。散落 `print`/`debugPrint`/`NSLog`、吞错无日志、外部依赖失败无上下文日志按 P2 起步，高风险不可观测路径按 P1。
- **日志安全**：日志不得记录 API key、token、PII、完整请求体、Keychain 值、用户生成内容原文或设备隐私原文；命中即 P1。
- **trace 记录**：trace §2/§3 应记录本次新增注释、日志、文档路径引用与无法覆盖的理由；缺记录为 P3，若导致审计不可复现为 P2。

### D6 合规红线 / 隐私合规（对应 harness 统一红线 + 平台合规）

- **本地化合规**：`view` 用户可见文案不得硬编码字面量，须走 `[SLOT-i18n]`（`Localizable.strings`/`R.string.localizable`）；新增硬编码文案 = 违例（hooks 拦），新增即阻塞按 D3。
- **密钥/凭据落地**：代码、`Info.plist`、config、fixtures、测试资产、trace 不得出现真实 API key、token、password、盐、长期凭据；只允许保存环境变量名引用/`credential_ref`/Keychain 读取。硬编码 secret = P1。
- **隐私与权限**：新增的权限申请（`Info.plist` 的 `NSXxxUsageDescription`）、数据采集、第三方 SDK 上报须与设计合规依据一致；私有 API、动态执行、未声明的数据采集 = P1。
- **禁用栈红线**：用 CoreData/SwiftData 替代 WCDBSwift、自创第八类 doc_type（`service`/`transport-handler`/`db-dao` 等当 token）、违反 `[SLOT-ui-framework]`（纯 SwiftUI 仓库新增 RxSwift）= 在对应判定直接 fail，不可豁免。

### D7 偏差闭合（对应 trace §4 + Gate `GI-6`）

PR diff 与计划逐项可对；所有计划外改动均有原因记录（如「`Container+UseCases.swift` 计划外修改：新 UseCase 需注册 `Factory`，属 DI 装配必经」）；上游结构性缺陷（归属错、合同越界、单元跟随名词而非行为）已**回退拥有该决策的阶段修订**而非就地补造。对不上靠 reviewer 自己发现 = P2 起步；就地改设计 = P1。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口（缺哪个装载源 / 槽位 / SLOT-16 / trace / 详细设计单元 / C1~C6 未过）+ 最小修复动作；不进入任何符合性判断，不给结论 pass/fail。

**前置通过时**，按以下顺序输出：

1. **结论（三选一，置顶）**：
   - **可进入 PR**：D1~D7 全过；trace 四节齐全（`GI-1`）、`xcodebuild build`/`xcodebuild test`（或 `swift build`/`swift test`）/SwiftLint 有命令级证据且全绿（`GI-3`）、承接 UNIT 的成功 + 全部失败路径有测试、注释/日志/文档路径追溯可审计、golden-path 锁定项逐项落地（`GI-4`：FactoryKit `@Injected` 无手动初始化 / Repository 模式 / `enum Error` 分层 / WCDBSwift 无 CoreData·SwiftData / ViewModel=`ObservableObject`+`@Published` / `private` 在 `private extension`）、分层依赖律零违反（`GI-5`）、DI 装配闭合（`GI-7`：新增单元在 `Container+*.swift` 有 `Factory` 注册且 `@Injected` 可解析）、无 P1、无清单外新增违例、无未闭合偏差。
   - **修复 P2 后可进入**：无 P1，但存在 P2（证据不完整、偏差未全闭合、非高风险漏测、绕行未挂编号、`private extension` 组织小瑕等）；列出 P2 修复项。
   - **不可进入 PR**：存在任一 P1（合同未实现 / 八问断链 / 分层反向·越层 / Domain 零依赖破坏 / `view` 直连持久化或互相导航 / 手动 `new` 替代 `@Injected` / `usecase` 触碰 UI 或环形依赖 / `WCDBSwift` 原始错误裸抛 UI / CoreData·SwiftData 替代 WCDBSwift / 自创 doc_type / 硬编码 secret / 清单外新增违例 / 高风险漏测 / 编译未收口 / 证据造假 / 就地改设计）；逐条列阻塞 P1。验证因环境/设备/真机/网络阻塞无法完成时，结论为 **blocked**，记录命令、错误摘要、缺失依赖与恢复条件，不得降级为 pass。
   - 机器可读收口字段必须同步输出：clean 且可进入 PR 时写 `review_result=clean/final-verification-ready`、`route_class=none`、`validation_summary=<命令与证据摘要>`；有 finding 或阻塞时写 `review_result=findings|blocked` 与最高优先级 `route_class`。
   - route class 只能取：`IMPLEMENT_DEFECT`（代码/测试/验证/注释/日志/脱敏缺陷）、`PROCESS_DEFECT`（trace/证据/流程执行缺陷）、`DETAIL_DEFECT`（详细设计合同错误或缺失）、`OVERVIEW_DEFECT`（概要归属/承接错误）、`REQ_BLOCKER`（需求行为/验收/边界缺陷）、`none`。

2. **逐条 Findings**（按 `P1 → P2 → P3` 排序；无则写 `none`），每条字段：
   ```md
   ### P<1|2|3> <标题>
   - route_class：`IMPLEMENT_DEFECT|PROCESS_DEFECT|DETAIL_DEFECT|OVERVIEW_DEFECT|REQ_BLOCKER`
   - 设计证据：`<UNIT-<slug>#八问几 / BHV-NNN / 详细设计文件:章节>`
   - 代码证据：`<相对路径:行 / 类型 / 方法 / @Published 字段 / Container+*.swift 注册行 / 验证位置>`
   - 存量证据：`<命中的 [SLOT-NN] 条目 / 清单外；不适用写 N/A>`
   - 问题：`<代码与详细设计或 golden-path 红线的具体偏离>`
   - 影响：`<为何导致合同不闭合 / 验证不可信 / 红线破坏 / 无法判断>`
   - 建议（最小修订）：`<改代码 | 补/复跑验证 | 移除越界测试 | 回退详细阶段修订 | 挂 SLOT-16 记债 | 补 Container Factory 注册 | 恢复验证环境>`
   ```
   同一轮多类缺陷按 `REQ_BLOCKER > OVERVIEW_DEFECT > DETAIL_DEFECT > PROCESS_DEFECT > IMPLEMENT_DEFECT` 给最高优先级路由，供 implement-check 自动回退。
   先证据后结论，严重度排序：
   - **P1**：合同未实现 / 执行流程步骤缺失·改序·下沉·上移无设计依据 / 八问断链（幽灵 BHV·UNIT）/ 实现期猜测发明未定义合同 / 分层反向·越层（Domain 非 `Foundation` import、`view` 直连持久化、`view` 间硬导航、`viewmodel`/`usecase` 触碰实现或 `WCDBSwift`、`usecase` 环形依赖）/ 手动 `new` 替代 FactoryKit `@Injected` / `WCDBSwift` 原始错误裸抛 UI 或缺 `enum XxxError` / 高风险核心 owner 完全无文档追溯 / 高风险路径不可观测 / 日志泄露 secret 或 PII / CoreData·SwiftData 替代 WCDBSwift / 自创第八类 doc_type / 硬编码 secret / 私有 API·动态执行 / 清单外新增违例（含扩大违例面）/ 高风险链路漏测 / 编译未收口 / 证据与复跑不符 / 就地改设计而非回退。
   - **P2**：编译/静态/测试证据不完整（无命令·无退出态·无测试名·无 violations 计数）/ 非高风险失败路径漏测 / 新增核心类型或 public/internal API 缺 DocC 设计锚点 / 非显然分支缺"为什么"注释 / 关键流程日志缺入口或失败上下文 / 偏差未全闭合靠 reviewer 发现 / 触碰存量绕行未挂编号 / DI 装配登记缺位（Factory 已注册但 trace 未记）/ `private` 方法未进 `private extension` / 计划与验证命令轻微不一致但未绕过实现 / 因环境阻塞验证未完成。
   - **P3**：命名后缀（`I` 前缀/`View`/`ViewModel` 后缀）、目录/文件组织、`MARK` 分组、注释措辞、验证记录可读性问题，不影响合同闭合与红线。

3. **存量豁免清单**：本次触碰的 SLOT-16 条目 + 分类结果（记债不阻塞 / 新增阻塞 / 可移除）+ 对应 `[SLOT-NN]` 编号。

4. **注释/日志/文档追溯摘要**：覆盖的新增核心定义、日志点、设计文档路径引用，以及缺口和判级。

5. **验证命令汇总**：每条 `command / status(passed|failed|not_run|blocked_by_environment) / evidence(输出摘要或测试名) / blocker`。未执行或环境阻塞的验证、失败的必要命令均不得支撑「可进入 PR」。

6. **反哺建议（可选）**：本次暴露的新模式/新坑 → 建议更新 `.trellis/spec/guides/golden-path.md`、`.trellis/spec/harness/*` 标准包或 project-conventions 槽位定义的具体条目（如新增 SLOT-16 记债项、补 golden-path §11 禁止清单条目、给 pending 四类补 L2）。

## 好例 / 坏例（审核判读对照）

- ✅ **合格切片（放行）**：`切片 S2 | 承接 UNIT-story-repository | doc_type=repository | Domain/Repositories/IStoryRepository.swift + Infrastructure/Persistence/Repositories/StoryRepository.swift + Infrastructure/Persistence/Models/StoryObject.swift + Container+UseCases.swift`；证据节贴 `xcodebuild build ... → BUILD SUCCEEDED`、`swiftlint --strict → 0 violations（新增 3 文件）`、`xcodebuild test ... -only-testing:<App>Tests/StoryRepositoryTests` 含 `test_save_找不到ID_映射PersistenceError.notFound` 等测试名，新增测试映射到 `UNIT-story-repository` 覆盖 `BHV-012` 成功 + 失败路径，DI 装配登记 `Container+UseCases.swift var storyRepository: Factory<any IStoryRepository>`（见对应文件），未验证项（真实 WCDBSwift 唯一约束触发）显式留 Manual QA。审核判：可进入 PR。
- ❌ **坏例（不可进入）**：`HomeViewModel` 里 `let repo = StoryRepository(databaseManager: ...)` 手动 `new` 并 `import WCDBSwift`（D2 §2.3 手动初始化 + §2.1 viewmodel 直连持久化，P1）；`StoryRepository` 把 WCDBSwift 原始 `Error` 直接 `throw` 到 ViewModel（D2 §2.5 裸抛，P1）；trace 证据节只写「全部编译通过，测试通过」无命令无测试名（D4，P2）；新引入 CoreData 替代 WCDBSwift（D2/D5 红线，P1）；`HomeView` 里 `NavigationLink(destination: SettingView())` 跨 feature 硬跳绕过 `AppCoordinator`（D2 §2.1，P1）。
- ❌ **坏例（八问断链）**：切片挂 `UNIT-home-cache` 但详细设计无此单元（幽灵单元 `slice_ghost_unit`，P1）；或 `BHV-012` 在概要有 owner 但无任何 `UNIT-<slug>` 承接（断链 `bhv_no_unit`，P1）。
- ❌ **坏例（doc_type 自创）**：trace 把切片 doc_type 写成 `service`/`db-dao`/`transport-handler`（非 iOS 七类，归属红线，P1，应回退用 `usecase`/`repository`/`external`）。

## 边界约束

- 只审改动面 + 其直接依赖；不对存量代码做全量审计（存量违例只走 SLOT-16 豁免判定）。
- 审核不代写代码；每条 finding 给最小修订方案。
- 规则正文不在本 skill 复写——分层依赖律、迷你路径、禁止清单以 `.trellis/spec/guides/golden-path.md` 为准；trace 四节、Gate `GI-1~GI-7`、doc_type↔测试分层映射以 `.trellis/spec/harness/implementation/implementation-trace-contract.md` 为准；BHV/UNIT 编号纪律、doc_type 权威七类、合同八问、统一红线以 `.trellis/spec/harness/index.md` 为准；槽位取值与 SLOT-16 以 project-conventions 为准。
- 未执行的验证不得写成通过；测试失败/证据缺失/环境阻塞如实输出，不降级结论。
- 新增测试不能替代设计或实现证据；通过集成/e2e/mock/fake 测试反向定义业务语义、测试补写详细设计 = P1，应回退详细或测试计划阶段。

## 与官方 Trellis skill 的边界

本 skill 是 `trellis-check` 在 Guru iOS 原生项目的领域化审核口径——在官方/工具级检查（`xcodebuild build`、`xcodebuild test`、SwiftLint）之上，叠加领域化的合同八问闭合、分层依赖律（Domain 零依赖 + 单向）+ FactoryKit DI / Repository 模式 / `enum Error` 分层 / WCDBSwift / `ObservableObject`+`@Published` canonical、本地化/隐私/secret 红线与 SLOT-16 存量豁免判定，并落到实现 Gate `GI-1~GI-7` 与 PR 准入结论。工具级检查跑机检结构（编译、lint 规则、import 方向），本 skill 跑「代码是否承接已审核详细设计、是否守红线、证据是否可信」的语义判定，二者叠加执行、互不替代。结构机检（trace 四节、切片挂 UNIT、幽灵单元/行为断链、pending L2 豁免）由 `guru_gate.py implement <task_dir>` 与 `guru_gate.py trace-matrix --strict` 同口径执行，本 skill 复用其判定项而不复制其实现。
