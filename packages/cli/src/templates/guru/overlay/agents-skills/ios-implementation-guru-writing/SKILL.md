---
name: ios-implementation-guru-writing
description: 按已过 Gate 的 iOS 原生（SwiftUI + DDD 四层）详细设计执行 Swift 编码与自测的执行编排 Skill（L3）。编码规则唯一来源是通用 golden-path（分层依赖律 Domain→App→Infrastructure→UI 单向、FactoryKit @Injected DI 强制、Repository 模式、enum Error 分层、WCDBSwift 持久化、ViewModel=ObservableObject+@Published、private 方法落 private extension）与 project-conventions 槽位（SLOT-01~SLOT-16）；`implement.md` 承载 implementation-trace 计划合同，detail 确认后的执行/验证证据写入 task-local mutable evidence，并补齐注释/日志/文档路径追溯。本 Skill 只做装载顺序、边界约束、WX 执行流程编排与产物要求，不重定义标准规则；标准口径住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`。doc_type 一律用 iOS 权威七类（viewmodel/usecase/repository/domain-model/view/coordinator/external），禁止自创或照抄 flutter/Go 类型名。
---

# iOS 原生实现执行

> 层级契约：规则正文与完成条件住 `.trellis/spec/guides/golden-path.md`（编码红线唯一来源）与 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（过程合同 §0~§4 + Gate GI-1~GI-7）；doc_type 取值、编号纪律（BHV/UNIT）、五道 Gate 口径住 `.trellis/spec/harness/index.md`；项目级取值（目录/命名/网络栈/日志/测试框架/存量清单）住 `.trellis/spec/conventions/project-conventions.md`（SLOT-01~SLOT-16）。本 SKILL.md 只承载装载顺序、边界约束、WX 编排与输出要求。冲突时以阶段子 SSOT 为准（harness index > L2 > references > 本 SKILL），规则疑义回 SSOT 并引章节号。
> 平台形态：DDD 四层 `Domain → App → Infrastructure → UI`（Domain 零依赖、可被任意层 import）；SwiftUI 主 + RxSwift 遗留；FactoryKit DI（`extension Container` + `Factory<T>` + `@Injected(\.x)`）；Repository 模式（接口在 `Domain/Repositories/IXxxRepository.swift`、实现在 `Infrastructure/Persistence/Repositories/XxxRepository.swift`）；每域一个 `enum XxxError: Error`；`AppCoordinator` 单一全局导航；WCDBSwift 唯一持久化；`ViewModel = ObservableObject + @Published`。证据基准为目标仓库对应位置（通用相对路径骨架，落地时替换为本仓库真实路径）：`docs/PROJECT_STRUCTURE.md`、`docs/Swift_代码组织规范.md`、`App/{DependencyInjection,Coordinators}/`、`Infrastructure/Persistence/`、`Domain/Errors/`、`UI/Features/<Feature>/`、`<App>Tests/`。

## 装载顺序（硬前置，任一失败即终止并输出前置缺口）

1. 必须先读 `.trellis/spec/guides/golden-path.md`（编码规则唯一来源）：确认五条锁定红线就绪——①分层依赖律 `Domain → App → Infrastructure → UI` 单向（Domain 零依赖，§2.1）；②FactoryKit `@Injected` DI 强制、禁手动 `init` 拼装（§2.3）；③Repository 模式（接口在 Domain、实现在 Infrastructure，接口实现分文件，§2.2/§4）；④每域 `enum XxxError: Error` 分层定义、底层异常在 Infrastructure 边界转 `PersistenceError`/域错误不裸抛 UI（§2.5）；⑤WCDBSwift 唯一持久化（禁 CoreData/SwiftData，§2.7）+ `ViewModel = ObservableObject + @Published`（§2.6 private 方法落 `private extension`）。不可用 → 终止并提示先安装/刷新 guru spec 模板（`apply.sh`），不在缺 SSOT 时凭记忆补规则。
2. 读 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（过程合同 §0 承接关系、§1 计划、§2 执行、§3 证据、§4 阻塞偏差）与 `.trellis/spec/harness/index.md` 的实现 Gate（`implement`，对应 trace 的 GI-1~GI-7）定义、doc_type 权威七类（§3）、编号纪律（§4.1：`BHV-NNN` / `UNIT-<slug>`，下游裸 token）。
3. 读 `.trellis/spec/conventions/project-conventions.md` 并校验 C1~C6（顺序短路）：C1 元信息齐全；C2 SLOT-01~SLOT-16 全在且「待定」≤2（默认待定候选 SLOT-08 网络层 / SLOT-15 构建自动化，各须写决策人+期限）；C3 已填槽位证据路径在目标仓库真实存在；C4 取值不违反通用硬规则；C5 doc_type 只用七类裸 token；C6 SLOT-16 存量清单存在（可为空但须显式「无」）。任一未通过 → 停止先定槽位/补约定，不在实现里私自拍板。本阶段实际消费的关键槽位：**SLOT-01**（UI 框架，新代码纯 SwiftUI 禁新增 RxSwift）、**SLOT-02**（doc_type→owner 层→物理目录映射）、**SLOT-03**（`IXxx` 前缀 + 接口实现分文件）、**SLOT-04/10**（`enum Error` 分层 + JSON 修复）、**SLOT-05**（FactoryKit 注册形态）、**SLOT-06**（WCDBSwift + `DatabaseManager` 注入）、**SLOT-07**（`AppCoordinator` 导航闭包注入）、**SLOT-09/11/12**（日志门面 `ILogger`/`Logger`/OSLog/主题 `ThemeManager`/本地化）、**SLOT-13**（feature `Views/`+`ViewModels/` 分目录）、**SLOT-14**（XCTest + 手写 mock，待迁 Quick/Nimble + Mockolo）、**SLOT-15**（Fastlane 待定，发布 lane 人工执行）、**SLOT-16**（存量违例豁免数据源）；同时确认项目 logger / logging helper / 日志门面和隐私字段约定。
4. 定位本任务承接的、已过详细 Gate 且人工确认已落盘的详细设计单元（full=`design_package/chapters/*.md` 逐章；light=`design.md` §详细），建立 `UNIT-<slug>` 单元清单 + 合同八问（①承接行为 ②输入/输出/错误 ③读写状态 ④调用/不调用依赖 ⑤失败收口 ⑥事件/后置 ⑦测试映射 ⑧不得补造）+ 测试映射；每个 UNIT 自带一个 doc_type（七类之一）。缺失或单元为幽灵引用（引用不存在的 UNIT/BHV）→ 终止并提示回退详细阶段（探索性 spike 除外，须显式声明、隔离、不并入交付）。
5. 建立构建基线：确认构建形态（CocoaPods 工作区 `<App>.xcworkspace` 主用 `xcodebuild`；Domain 抽为独立 SPM package 时可用 `swift build`/`swift test`），记录改动前 `xcodebuild build` 与 `Pods/SwiftLint/swiftlint lint` 的基线状态（用于区分「我引入的失败」与「既有失败」）；不可建立基线 → 记录环境阻塞，不得把未验证当通过。

## 边界约束

- 只实现详细设计合同内的内容；合同外结构（新 `enum XxxError` case、新 doc_type、新 feature 目录、新 `NavigationDestination` case、新 `Container` Factory、新 WCDB 表/列）一律不新增；合同错漏回退详细阶段，并在 `implementation-evidence.jsonl` 留回退记录（指向被修订的 `UNIT-<slug>` 与缺什么），不在实现里就地改设计 owner / 依赖方向 / scope。
- 严守 golden-path 锁定红线，不可豁免：
  - ①**分层依赖律**：`Domain → App → Infrastructure → UI` 严格单向；`Domain` 层文件只 `import Foundation`/标准库，绝不 import `SwiftUI`/`WCDBSwift`/`FactoryKit`/App/Infrastructure/UI 符号；`view` 不直接访问持久化（必经 `viewmodel → usecase → IXxxRepository`）、不在 feature 间硬 `NavigationLink` 直跳（走 `AppCoordinator`）；`viewmodel` 只注入 `usecase`/`IXxxRepository` 接口，不持 repository 实现类/`DatabaseManager`/网络 SDK；`usecase` 零 UI 依赖（不 `import SwiftUI`、不持 `@Published`），usecase↔usecase 只允许单向无环。
  - ②**接口实现分离**：`usecase`/`repository`/领域服务/`external` 适配器一律协议（`IXxx`）与实现分两个文件；接口落 `Domain/`，`usecase` 实现落 `App/UseCases/<Feature>/`，`repository` 实现落 `Infrastructure/Persistence/Repositories/`，`external` 适配器落 `Infrastructure/{Adapters,Services}/`（按 SLOT-02/03）。
  - ③**FactoryKit `@Injected` DI**：每个新增 `viewmodel`/`usecase`/`repository` 实现/`external` 必须在 `App/DependencyInjection/Container+*.swift` 注册 `Factory`（`self { ... }.singleton` 或 `@MainActor` 闭包给 UI ViewModel），消费侧用 `@Injected(\.x)` / `@InjectedObject(\.x)`；禁业务类里手动 `new`、禁 `view` 的 `body` 里 `init` ViewModel、禁用 `Xxx.shared` 顶替可注入业务依赖（`ThemeManager.shared`/`ToastManager.shared`/`Logger` 纯横切工具单例除外）。
  - ④**enum Error 分层**：`domain-model`/`usecase` 抛域错误（`StoryError`/`StoryManagementError`），`repository` 实现/`external` 把 WCDB/网络/SDK 原始错误在边界转为 `PersistenceError` 或域错误后上抛，绝不裸抛 UI、绝不静默吞错（`catch { return [] }` 把 DB 失败伪装成空结果＝违例）。需在测试比较的错误实现 `Equatable`。
  - ⑤**WCDBSwift 唯一持久化**（禁 CoreData/SwiftData）；`ViewModel = ObservableObject + @Published`；`private` 方法/属性必须落 `private extension` 并带 `// MARK: - Private Methods - <分组>`（极简类 1~2 个 private 方法、协议扩展、测试类可放宽）；`view` 文案走本地化（SLOT-12）、禁硬编码颜色/尺寸（SLOT-11）。
- 不私自拍板实现中冒出的新决策（网络栈二选一 URLSession/Moya、是否切 OSLog、是否引入 Quick/Nimble、是否引入 Mockolo、WCDB 表是否加索引、某 SDK 仅真机可用如何在 CI mock）→ 记录并升级人工 Gate，落到对应 SLOT 槽位或 `technology_decision_handoff` 后再继续。
- secret/credential 合规：代码、`Localizable.strings`、fixtures、trace 与 mutable evidence 只写 keychain key / 配置 key 名引用，不落真实 API key、token、签名密钥、密码明文；不可信 JSON（LLM/外部）必经 `IJSONRepairService` 修复后解析（SLOT-10），禁 `try? JSONDecoder().decode(...)` 静默吞错。
- 不采用默认 TDD/RED-GREEN：默认只运行 SLOT-14 测试框架槽位下的既有验证命令（XCTest + 手写 mock；未落地 Quick/Nimble 前不强造 BDD），不为驱动结构而先造一堆 fake；**高风险切片**（WCDBSwift 表结构/迁移、`Container+*.swift` DI 装配改 graph、SwiftUI↔RxSwift 遗留桥接、`NavigationDestination` 枚举扩展的全量 switch、async/await 与 `MainActor` 线程归属）按详细设计测试映射先补失败路径测试再实现。新增测试须可追溯到承接的 `BHV-NNN`/`UNIT-<slug>`。
- 注释与日志是实现证据的一部分：新增核心类型、public/internal API、ViewModel、UseCase、Repository 接口与实现、domain-model、Coordinator、external adapter、跨层 DTO/状态定义必须能从代码追溯到详细设计；非显然业务分支、错误转换、降级/恢复、WCDB 迁移、SwiftUI↔RxSwift 桥接、`MainActor`/并发、DI 装配、导航枚举与生命周期边界必须有简洁但具体的注释或日志。禁止堆砌"赋值/调用"类空注释。
- 日志必须复用 SLOT-09 选定的 `ILogger`/`Logger`/OSLog 或项目日志门面；不得用散落 `print`/`debugPrint`/`NSLog` 或临时 debug 输出替代生产日志，不得记录 API key、token、PII、完整请求体、Keychain 值、用户生成内容原文或设备隐私原文。
- 触碰存量违例（SLOT-16 清单）按标准包口径分类记录到 `implementation-evidence.jsonl`（绕行须写"为何不修"；顺手修复须独立标注、不混入业务 diff；记债须给 SLOT-16 条目）。iOS 典型存量域：RxSwift 遗留订阅（SLOT-01）、日志 SwiftyBeaver 未切 OSLog（SLOT-09）、`DatabaseManager.shared` 直接引用（SLOT-05/06）、手写 mock 未切 Mockolo（SLOT-14）、XCTest 未切 Quick/Nimble。触碰已登记存量做最小修复＝记债不阻塞；在已登记文件中**新增同类违例**＝阻塞。
- 若其它通用 skill、插件或 agent 习惯（测试优先、自动重构、引入 DI 容器替代 FactoryKit、在 View 里直接订阅 Rx、用 CoreData/SwiftData）与本平台 golden-path / trace 合同冲突，以平台 SSOT 为准，冲突项忽略或向用户确认。

## 执行流程（WX 步骤）

1. **WX-0 判定实现模式与构建基线**：判定空 feature 初始化 / 已有 feature 增量 / 重构校准；确定本任务落在哪个 `UI/Features/<Feature>/`、复用还是新建 `Domain/Repositories`、`App/UseCases/<Feature>`、`Infrastructure/Persistence/Repositories` 资产，是否需扩 `AppCoordinator.NavigationDestination` 或新建 WCDB 表；记录改动前 `xcodebuild build -workspace <App>.xcworkspace -scheme <App>` 与 SwiftLint 基线（用于区分既有失败）。
2. **WX-1 计划（开工前写）**：按 trace 合同 §1 在目标仓库 `implement.md`（建议 `docs/design/<feature>/implementation-trace.md`）产出任务切片表；若 detail 已确认则只读取该计划，不在实现阶段补写。每片含：① 承接的 `UNIT-<slug>`（幽灵引用被 `slice_ghost_unit` 拦截）；② doc_type（iOS 七类之一）；③ 文件范围（相对路径，落在该 doc_type 的 owner 层内，按 SLOT-02）；④ 完成信号（可验证、非「做完感」——如「`@Published` 三态字段齐全且 `@Injected` 注入接口」「错误映射表逐条落地」「`Factory` 注册行就位」）；⑤ 验证方式（编译/测试/lint 命令，见 §3）。执行顺序**自底向上**（golden-path 锁定）：`domain-model`（实体/值对象/`enum Error`）→ `repository`（Domain 接口 + Infrastructure 实现 + WCDB 表对象 + mapper）→ `usecase`（编排 + 域错误）→ `viewmodel`（`@Published` + `@Injected`）→ `view` + `coordinator`/`external` 横切（`coordinator` 含 DI 装配，被依赖方稳定后接入）。逐条预判高风险点并写验证手段（WCDB 表/迁移、DI graph 影响全局单例、Rx 遗留桥接内存/线程、导航枚举全量 switch、`MainActor` 线程归属）。人工确认从最小可独立 review 的切片开始（单 ViewModel / 单 UseCase / 单 Repository 接口+实现对 / 单 SwiftUI View 为典型粒度）。
3. **WX-2 逐片实现（随做随记）**：每片对照承接 `UNIT-<slug>` 的合同八问落地——②输入/输出/错误（Swift 签名级 `async throws`、`domain-model` 结构体、`enum XxxError` 的每个 case；`viewmodel` 逐 `@Published` 字段列名称/类型/初值/写入时机 + loading/empty/error 三态去向）；④调用/不调用依赖（`@Injected` 注入接口；`usecase` 调 `IXxxRepository` 不反向；`viewmodel` 不碰 `DatabaseManager`；`view` 不发起导航/不访问持久化）；⑤失败收口（每条失败路径处置 + 错误转换位置：底层异常→`enum Error` 映射表逐行对应一条失败 BHV）；⑥后置副作用（`@Published` 发射 / Combine·RxSwift 流时序 / 导航动作去哪个 destination 带什么参数 / 埋点）。每片完成**立即**追加 `implementation-evidence.jsonl`（实际改动文件清单逐文件标层与新增/修改/删除、与计划偏差及原因、DI 装配登记 `Container+*.swift` 注册行位置、本切片触碰的 golden-path 锁定项逐项确认、`AppCoordinator`/`Container`/`DatabaseManager` 等共享面单独标注），不积压到批末。
4. **WX-3 代码生成 / 脚手架（仅触发条件满足时）**：按 SLOT-14（mock 生成：手写 → Mockolo）与资源生成选型执行并追加 `implementation-evidence.jsonl`——若已切 Mockolo → 跑生成命令、记产物 mock 文件清单；若用 R.swift / SwiftGen 生成本地化或资源访问器 → 记命令与产物。**当前默认 SLOT-14＝手写 mock、无 Mockolo → 本项写「本切片无生成步骤（手写实现 + 手写 mock）」，不留空、不私自引入生成器。** 任何发布/签名 lane（SLOT-15 Fastlane 待定）一律人工执行，agent 禁自动触发上架/分发。
5. **WX-4 逐片验证（验证后记）**：按 trace 合同 §3 的字段要求追加 `verification-evidence.jsonl`——**编译**：工作区 `xcodebuild build -workspace <App>.xcworkspace -scheme <App> -destination 'platform=macOS'`（或 SPM 包 `swift build`），贴命令 + 结果（`BUILD SUCCEEDED`/失败摘要 + 处置）；**静态检查**：`Pods/SwiftLint/swiftlint lint --strict --reporter emoji`，零新增违例（存量按 §4 记 SLOT-16），nolint 豁免写理由并指向 SLOT-16；**测试到测试名级别**：`xcodebuild test -workspace <App>.xcworkspace -scheme <App> -destination 'platform=macOS' -only-testing:<App>Tests/<ClassName>/<testMethod>`（或 SPM `swift test --filter <ClassName>`；Quick/Nimble 用 `describe/it` 记到 example 名），新增测试逐条列 `XCTestCase` 子类名 + `test*` 方法名 + 承接 `BHV-NNN`/`UNIT-<slug>`。按 doc_type 取证：`domain-model`＝unit 纯逻辑无 mock；`repository`＝unit（mock `DatabaseManager`）+ integration（真实 WCDBSwift 临时库），错误映射表逐条用例 + mapper 双向；`usecase`＝unit（mock `IXxxRepository`）每条承接行为 ≥1 成功 + ≥1 失败、业务错误枚举逐条（**测试密度最高层**）；`viewmodel`＝unit（mock usecase 接口）断言 `@Published` 三态转移 + 订阅取消无泄漏；`coordinator`＝断言 `NavigationDestination` 转移 + `Container` 解析全部新增 `Factory` 冒烟；`view`＝逻辑已下沉 viewmodel，结构断言列「未验证项」或快照（若有基线）；`external`＝mock SDK 边界 + 真实集成留真机。失败先修复再进下一片；未验证项显式列出并指明留给哪个环节（真机/设备能力/大模型推理/TTS 真实音频/GPU 图像生成/WhisperKit 设备端表现 → Manual QA / 真机池 / 性能基准）。
6. **WX-5 注释/日志/文档追溯**：逐片完成前补齐维护性证据：
   - 新增核心类型、public/internal API、ViewModel、UseCase、Repository 接口与实现、domain-model、Coordinator、external adapter、跨层 DTO/状态定义：优先用 Swift DocC 风格 `///` 写明职责、承接的 `UNIT-<slug>` / `BHV-NNN`，必要时附设计文档相对路径（如 `docs/design/.../chapters/<slug>.md` 或任务内 `design.md` 锚点）。
   - 复杂私有 helper、错误映射、WCDB 迁移、SwiftUI↔RxSwift 桥接、`MainActor`/异步竞态、DI 装配、导航枚举、降级/恢复、生命周期处置：用局部注释解释"为什么这样做"和对应设计约束。
   - 关键流程日志覆盖入口、成功收口、失败/降级、重试/恢复、外部依赖边界、DI/导航/持久化关键边界；字段只放低敏上下文（request_id、hash 后 user_id、status、duration、error_kind），不泄露隐私或业务正文。
   - 在 `implementation-evidence.jsonl` 记录本片新增的注释/日志/文档路径引用；若某类代码不需要注释或日志，写明理由。
7. **WX-6 存量违例处置**：触碰 SLOT-16 条目时按标准包口径分类记录到 `implementation-evidence.jsonl`（绕行须写"为何不修"；顺手修复独立标注；记债给 SLOT-16 编号）。新增代码引入清单外新违例则阻塞（必须修或显式升级人工 Gate）。
8. **WX-7 收口自检**：对照实现 Gate GI-1~GI-7（见下「质量门禁」）+ 注释/日志/文档追溯要求输出自检摘要；上游缺陷已回退修订而非就地改设计；未验证项显式移交（Manual QA / 真机池 / 性能基准 / 集成环境）。

## 输出

- **实施计划先列**：`implement.md`（trace）路径、`UNIT-<slug>` 承接清单、`chapter_target → ios doc_type → Swift 代码资产`（owner 层/物理目录/文件）映射、自底向上的阶段顺序与高风险点、阻塞项；detail 确认后只报告计划合同位置，不把执行证据写回该文件。
- **代码改动 + 新增/修订测试**：改动文件按 doc_type/层标注（如 `App/UseCases/StoryManagement/StoryManagementUseCase.swift`（`usecase`/Domain）、`Infrastructure/Persistence/Repositories/StoryRepository.swift`（`repository` 实现/Infrastructure）、`App/DependencyInjection/Container+UseCases.swift`（`coordinator`/DI 装配））。
- **task-local mutable evidence 完整**：`implementation-evidence.jsonl` 记录执行/偏差/packet/注释日志追溯，`verification-evidence.jsonl` 记录命令级验证与测试名，`review-records/implementation-reviews.jsonl` 记录 required implementation review；`implement.md` 只作为已确认的 trace 计划合同读取。
- **Gate GI-1~GI-7 自检摘要 + 注释/日志/文档路径追溯摘要 + 移交清单**：逐项给结论（pass / 阻塞 / 移交环节）；交付时说明修改文件、对应设计锚点（`UNIT-<slug>` / `BHV-NNN`）、验证命令、维护性证据、未验证项与剩余阻塞。
- **若无法完成**：明确输出 `blocked` 的具体详细设计文件、缺失合同锚点（如八问缺 `enum Error` case、签名与 `domain-model` 不符、测试映射漏失败路径）与需回修的合同项；环境阻塞写准确命令、错误摘要、缺失依赖（如 SDK 仅真机可用）与恢复条件，结论不得标 `pass`。

## 质量门禁（与 `guru_gate.py implement` / 实现 Gate GI-1~GI-7 同口径）

切片可进入 commit/PR，当且仅当：

- **GI-1 trace 合同与 mutable evidence 齐全**：`implement.md` 必须存在且计划有 `UNIT-<slug>` 承接 + doc_type + 文件范围 + 完成信号；执行/偏差/DI 装配/验证证据在 `implementation-evidence.jsonl` 与 `verification-evidence.jsonl` 中可按切片恢复，阻塞如无则显式记录「无」；trace 不存在直接 fail，无 TODO 占位、无空章节。
- **GI-2 承接闭合 + 归属合法**：每切片承接的 `UNIT-<slug>` 存在于详细设计（无幽灵引用 `slice_ghost_unit`）；doc_type 为 iOS 七类之一且文件范围落在该 doc_type owner 层内（`view`/`viewmodel`→UI、`coordinator`→App、`usecase`/`domain-model`/`repository` 接口→Domain、`repository` 实现/`external`→Infrastructure，按 SLOT-02）。
- **GI-3 编译 + 测试 + lint 证据**：每切片有 `xcodebuild build`（或 `swift build`）结果 + 测试命令结果（**测试名级别**，覆盖承接 `UNIT-<slug>`/`BHV-NNN` 的成功路径 + 全部失败路径）+ SwiftLint 结果；无「全部通过」式无命令证据；新增测试清单可追溯到 UNIT；未执行的验证不得写成通过。
- **GI-4 golden-path 锁定项逐项落地**：FactoryKit `@Injected` 无手动初始化 / Repository 模式（接口实现分文件、UI·usecase 不直连 WCDB）/ `enum Error` 分层（Domain 错误在 `Domain/Errors/`、UseCase 错误在各 UseCase 目录、底层异常边界转换不裸抛 UI）/ WCDBSwift 无 CoreData·SwiftData / `ViewModel=ObservableObject+@Published` / `private` 方法在 `private extension`。
- **GI-5 分层依赖律零违反**：Domain 零依赖（Domain 文件无非 `Foundation`/标准库 import）；`Domain→App→Infrastructure→UI` 单向无逆行；`view` 不直连持久化、不互相导航；`viewmodel` 不 import repository 实现类/`WCDBSwift`；secret 只写 key 名引用无字面量密钥。
- **GI-6 偏差闭合 + 编号闭合**：PR diff 与计划逐项可对，计划外改动均有原因记录；切片均挂真实 `UNIT-<slug>`（幽灵单元被拦截）；上游结构性缺陷（归属错、合同越界、单元跟随名词而非行为）已回退拥有该决策的阶段修订，禁止在实现阶段补造。
- **GI-7 DI 装配闭合**：每个新增 `viewmodel`/`usecase`/`repository` 实现/`external` 在 `Container+*.swift` 有对应 `Factory` 注册（`@Injected` 运行期可解析），UI ViewModel 工厂标 `@MainActor`；存量违例均有记录与处置（SLOT-16），未决决策已升级（无私自拍板）。

任一未满足 → 不进 commit。`xcodebuild build` / `swiftlint lint --strict` / `xcodebuild test`（测试名级别）由目标仓库 worktree.yaml verify 条目执行，与本自检同口径；上游结构性缺陷只能回拥有该决策的阶段修订，禁止下游补造。

## 好例 / 坏例

✅ **合格切片登记与证据**（粒度可独立 review、命令级证据、可追溯、自底向上）：

```
切片 S3 | 承接 UNIT-story-management-usecase | doc_type=usecase（owner=Domain）
  文件范围：App/UseCases/StoryManagement/IStoryManagementUseCase.swift
            + StoryManagementUseCase.swift
            + StoryManagementError.swift
            + App/DependencyInjection/Container+UseCases.swift（DI 装配横切）
  完成信号：公开方法签名级齐全；只 @Injected 注入 IStoryRepository 接口（无实现类/无 DatabaseManager）；
            业务错误枚举 StoryManagementError 落地；private 方法落 private extension；Factory 注册行就位
  证据：
    - 编译：xcodebuild build -workspace <App>.xcworkspace -scheme <App>
            -destination 'platform=macOS' → BUILD SUCCEEDED
    - 静态检查：Pods/SwiftLint/swiftlint lint --strict → 0 violations（新增 3 文件）
    - 测试：xcodebuild test ... -only-testing:<App>Tests/StoryManagementUseCaseTests → 全 PASS
        · test_fetchAllFullStories_成功_返回按更新时间排序列表
        · test_createStory_校验失败_抛StoryManagementError.validationFailed
        · test_deleteStory_找不到ID_抛StoryManagementError.notFound
      新增测试：StoryManagementUseCaseTests（3 方法，mock IStoryRepository）
        承接 UNIT-story-management-usecase / BHV-012（成功）+ BHV-013（失败路径）
    - DI 装配：Container+UseCases.swift 注册 var storyManageUseCase: Factory<IStoryManagementUseCase> { ... }.singleton
    - 未验证项：无（纯 Domain 编排，本地全覆盖）
```

❌ **不合格切片登记**：「实现故事模块，改 usecase 和 repository，写完跑测试」——无 `UNIT` 编号、无 doc_type、无文件范围、无完成信号、跨多层无法独立 review；证据「全部编译通过，测试通过，lint 无问题」——无命令、无 `BUILD SUCCEEDED`、无测试名、无新增测试映射、未声明未验证项（违 GI-1/GI-3）。

❌ **红线违例**：在 `view` 的 `body` 里 `Task { try await storyRepository.findAll() }` 业务漏进 View 且直连 repository（违 §2.1 分层 + GI-5）；`viewmodel` 的 `init` 里 `self.repo = StoryRepository(databaseManager: DatabaseManager.shared)` 手动 new + 直连单例（违 SLOT-05 + GI-4/GI-7）；故事卡片 View 内 `NavigationLink(destination: StoryDetailView(...))` 硬跳绕 `AppCoordinator`（违 SLOT-07 + GI-5）；`repository` 实现 `catch { return [] }` 把 WCDB 失败伪装成空结果（违 SLOT-04）；`usecase` 文件 `import SwiftUI` 或持 `@Published`（违 §2.1/GI-5）；`domain-model` 文件 `import WCDBSwift`（破坏 Domain 零依赖，GI-5）；实现里擅自引入 Mockolo/Quick·Nimble 未升级 SLOT-14（违边界约束）；trace 在 PR 前一次性补写（失去过程证据，违反模式）。

## 不适用场景（本 Skill 不约束的边界）

- 详细设计阶段的接口/数据结构定义（合同八问）：实现 trace 只承接不重定义；八问缺错（漏 `enum Error` case、签名与 `domain-model` 实体不符、测试映射漏失败路径、依赖方向写反）→ 回退详细阶段，不在实现里改设计。
- 概要归属与技术决策（行为 owner、分层归属、技术选型）：属概要/详细 Gate；实现发现归属错只能回退（`implementation-evidence.jsonl` 记回退动作），不在 trace 里改 owner。
- SLOT 待定项的最终选型（网络栈 URLSession/Moya、日志切 OSLog、测试框架切 Quick/Nimble、mock 切 Mockolo、Fastlane 接入）：属 project-conventions 槽位决策；实现中冒出只能升级人工 Gate 落槽位，不私自拍板。
- 纯文档/注释/格式化变更（无行为改动、无新切片）：可不建独立 trace 切片，但仍需 SwiftLint/SwiftFormat 通过；与功能切片同 PR 则并入对应切片记录。
- SwiftUI `view` 的视觉结构断言：逻辑应已下沉 `viewmodel`；View 层结构归 Manual QA / 快照测试（若仓库已有快照基线），trace 列「未验证项」而非伪造单测通过。
- 设备能力依赖的真实验证（真机、大模型推理、TTS 真实音频、GPU 图像生成、WhisperKit 设备端表现）：本地不可验证，trace 显式列未验证项并移交 Manual QA / 真机池 / 性能基准，不标 `pass`。
- 分支/worktree/提交/PR 流程隔离：交给 `sop-task-runner`（复用后端，栈无关）——先用本 Skill 判定改动范围 → sop-task-runner 创建隔离 → 在隔离内继续本 Skill。

## 与官方 Trellis skill 及 review skill 的边界

本 skill 是官方 `trellis-implement` 在 Guru iOS 原生（典型形态：SwiftUI + DDD 四层 + FactoryKit DI + WCDBSwift + AppCoordinator）项目的领域化**写作/执行**口径：sub-agent 实现时按本 skill 的 WX 流程、golden-path 五条红线与 trace 合同四节工作；Phase 2 dispatch 时在 prompt 中指明加载本 skill 口径。`trellis-implement` 负责通用任务编排与状态机推进，本 skill 不重复其职责，只补齐 iOS 平台的分层依赖律、接口实现分离、FactoryKit DI 装配、`enum Error` 分层收口、WCDBSwift 持久化归属与 trace 证据要求。

本 skill 与 `ios-implementation-guru-review` 分工：本 skill 负责**生成代码 + 写 task-local mutable evidence + 自检 GI-1~GI-7**（写侧）；`ios-implementation-guru-review` 负责**按同口径审核代码改动判定能否进 PR + 执行 SLOT-16 存量豁免判定**（审侧，存量记债不阻塞、清单外新增违例阻塞）。两者共享同一组 SSOT（golden-path + implementation-trace-contract + harness index + project-conventions），冲突时以阶段子 SSOT 为准，本 skill 不重定义标准规则——规则正文住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`，doc_type 与 Gate 口径住 `.trellis/spec/harness/index.md`。
