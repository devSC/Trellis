# iOS 原生详细设计 — 单一来源规范（L1 SSOT）

> 跨类型唯一权威。L2 类型文件只承载类型差异，不得与本文冲突；writing/review 只做编排与判定。
> 上游硬输入：概要设计的归属判定表 + `chapter_target → doc_type` 承接索引 + `technology_decision_handoff[]`（技术决策承接）。
> 层级契约：本文（L1）承载规则正文与完成条件；writing/review skill 的 `references/` 只承载编排细则、模板与示例；冲突时 L1 > L2 > references > SKILL.md。
> 平台基准：DDD 四层（Domain → App → Infrastructure → UI），Domain 零依赖；SwiftUI 主 + RxSwift 遗留；FactoryKit `@Injected` DI；Repository 模式；`enum Error` per domain；`AppCoordinator` 导航；WCDBSwift 持久化；ViewModel = `ObservableObject` + `@Published`。
> 装载路径（安装后）：本文件位于 `.trellis/spec/harness/detail/detail-structure-single-source.md`；通用 golden-path 位于 `.trellis/spec/guides/golden-path.md`；L2 类型文件位于 `.trellis/spec/harness/detail/detail-type-<doc_type>.md`。

## 0. doc_type 类型来源说明（flutter/backend → iOS 七类映射）

iOS 原生平台的 `doc_type` 不照抄 flutter 客户端的九类（`page-entry/controller/usecase/service/repository-datasource/db-dao/api-network/config-l10n/external-platform`），也不照抄 backend 的九类（`Entry/API`、`Entry/CLI`、`Entry/Background Trigger`、`Biz/Behavior`、`Utility/Technical Capability`、`Data/Canonical`、`Config/Runtime Contract`、`External/Integration Contract`、`Runtime/Deployment Contract`）。iOS 类型集合以本平台档案（DDD 四层 + SwiftUI/FactoryKit/WCDBSwift 实测，story-verse-mac）为唯一权威，收敛为**严格七类**（见 §2）。下表只说明语义来源，**禁止在 iOS 文档中出现源平台的类型名**。

| iOS 七类（权威） | flutter 近似来源 | backend 近似来源 | iOS 差异要点（为什么不照抄） |
|------------------|------------------|------------------|------------------------------|
| `viewmodel` | `controller`（GetX 状态容器） | 无直接对应（backend 无 UI 状态层） | iOS 状态容器是 `ObservableObject` + `@Published`，不是 GetX `Rx`；事件→状态转移与生命周期绑定 SwiftUI `View`，无路由 owner（路由属 `coordinator`）。 |
| `usecase` | `usecase`（响应式业务流） | `Biz / Behavior`（厚业务核心） | iOS `usecase` 在 Domain 层、零 UI 依赖，承接核心能力 owner；不持有 GetX 流，状态对外用 Combine/`async` 或回调。 |
| `repository` | `repository-datasource`（数据访问合同） | `Data / Canonical` 的访问面 + 部分 `External` | iOS 将「Domain `IXxxRepository` 接口 + Infrastructure 实现」**合并为一类**：接口在 Domain（被任意层导入），实现在 Infrastructure（持有 WCDBSwift/网络）。 |
| `domain-model` | 散落在各类的 model（无独立类型） | `Data / Canonical` 的实体/字段语义 | iOS 把实体/值对象/`enum Error`/不变量收敛为独立类型，**零依赖、可被任意层导入**；不承载持久化 DDL（持久化形态归 `repository` 实现与 `external`）。 |
| `view` | `page-entry` 的 Widget 部分 | 无对应 | iOS `view` 是 SwiftUI `View`，只展示 + 输入，无业务、无导航、无持久化；事件回调给 `viewmodel`，导航请求交 `coordinator`。 |
| `coordinator` | `page-entry` 的路由/Binding 部分 | 无对应 | iOS 导航集中在 App 层 `AppCoordinator`，并承载 FactoryKit DI 装配（`Container` 注册）；flutter 的 Binding/Routes 在 iOS 由 coordinator 统一承接。 |
| `external` | `api-network` + `db-dao` 的底层 + `external-platform` | `External / Integration Contract` + `Config/Runtime` 的运行支撑 | iOS `external` 是 Infrastructure 外部集成：网络（URLSession/Moya）、三方 SDK、WCDBSwift 持久化引擎、平台通道、iOS 交付面（PrivacyInfo/entitlements/StoreKit）。 |

映射纪律：

- 源平台「类型名」只用于本节说明语义来源；正文、骨架、索引、trace 一律使用 iOS 七类名。
- 不得自创 `transport-handler`、`service`、`page-entry`、`controller`、`Biz/Behavior` 之类的类型名（无论它在 flutter/backend 是否合法）。
- iOS 不存在独立的 `db-dao`/`api-network`/`config-l10n` 类型：DB 表定义与迁移、网络方法与 req/resp model 都收敛进 `repository`（业务访问合同）与 `external`（引擎/网络实现合同）；配置/ARB key/i18n 由 `project-conventions` 槽位与 `external` 交付面承接，不单列类型。
- iOS 不存在 backend 的 `Entry/Background Trigger`、`Runtime/Deployment Contract`：客户端没有服务端入口与运行拓扑；后台触发（推送/后台刷新）作为 `external` 的平台通道能力 + `usecase` 的业务编排承接。

## 1. 装载与硬前置

执行写作或审核前依次确认，任一失败即终止并输出前置缺口与概要修订动作：

- P1 本文件（`.trellis/spec/harness/detail/detail-structure-single-source.md`）可读；涉及类型的 L2 文件可读（v1 仅 `viewmodel`/`usecase`/`repository` 有 L2 文件 `detail-type-viewmodel.md`/`detail-type-usecase.md`/`detail-type-repository.md`；其余四类 `domain-model`/`view`/`coordinator`/`external` 按本文 §3 合同八问展开，并在文档头标注 `l2_status: pending`，full 链另须满足 §2 的 L2 豁免合同）。
- P2 通用 golden-path（`.trellis/spec/guides/golden-path.md`）可读，golden-path 硬规则（FactoryKit `@Injected` DI、Repository 模式、`enum Error` 分层、WCDBSwift 持久化、ViewModel = `ObservableObject`+`@Published`、private 方法置于 `private extension`）已加载。
- P3 目标仓库 `project-conventions.md` 可读且校验通过（C1~C5，见 §1.1）。
- P4 概要主定义可定位（full 链=`design_package/design-main.md`；light 链=`design.md` §1），且承接索引存在、可建立完整非空的 `chapter_target → doc_type` 目标集合。**索引缺失/为空 → 回退概要阶段，禁止在详细阶段补造归属。**
- P5 概要 Gate 已过且当前 digest 下已有两个不同 run-id 的 clean review evidence（`guru_gate.py status` 可查 overview review）；缺 evidence 不得开始详细写作。

### 1.1 project-conventions 槽位校验（C1~C5）

`project-conventions.md` 必须把以下槽位收口为确定取值（迁移态用「源 → 目标」记，详细设计按目标态写）。任一槽位为空或与 golden-path 冲突即 C 校验失败：

- C1 框架与状态：UI 框架（SwiftUI 主 + RxSwift 遗留 → 纯 SwiftUI）；ViewModel 形态（`ObservableObject`+`@Published`）；DI（FactoryKit `@Injected`）。
- C2 数据与网络：持久化（WCDBSwift，禁 CoreData/SwiftData）；网络层（URLSession / Moya，二选一并记取值）；JSON 修复策略（容错/严格 + 失败语义）。
- C3 横切：日志（SwiftyBeaver → OSLog）；i18n（本地化 key 来源与同步策略）；主题（`ThemeManager` 单例）。
- C4 工程结构：feature 模块结构（`UI/Features/<Feature>/` 下 View/ViewModel 组织）；mock 生成（手写 → Mockolo）；测试框架（XCTest → Quick/Nimble）。
- C5 构建：构建自动化（Fastlane）；签名/交付面引用（PrivacyInfo/entitlements/StoreKit）落点。

命名、目录、序列化、日志门面等取值不得偏离上列槽位；详细设计正文出现的具体取值必须可回指 `project-conventions.md` 槽位。

## 2. 七类 doc_type（严格七类，全程唯一，禁止改名/增减/换数）

| doc_type | owner 层 | 覆盖对象 | 依赖律要点 | L2 状态 |
|----------|---------|---------|-----------|---------|
| `viewmodel` | UI | `ObservableObject` + `@Published` 状态容器：状态字段、事件→状态转移、订阅、生命周期、三态（loading/success/error） | 可依赖 `usecase`/`domain-model`；禁直接依赖 `repository` 实现、`external`、WCDBSwift；导航走 `coordinator` | **v1 提供** |
| `usecase` | Domain | 业务编排（零 UI 依赖）：核心能力 owner、业务规则、状态流转、业务 API | 可依赖 `repository` 接口、`domain-model`、其它 `usecase`；禁依赖 `viewmodel`/`view`/`coordinator`/UI 类型 | **v1 提供** |
| `repository` | Domain（接口）+ Infrastructure（实现） | `IXxxRepository` 接口（Domain）+ 实现（Infrastructure）：数据访问合同、local/remote 编排、缓存回落、错误转换点 | 接口在 Domain 零依赖；实现可持有 `external`（WCDBSwift/网络）；禁实现泄漏到 Domain；调用方只依赖接口 | **v1 提供** |
| `domain-model` | Domain | 实体 / 值对象 / `enum` / `enum Error` / 不变量；零依赖、可被任意层导入 | 零依赖（仅依赖 Foundation 级基础类型）；禁导入 `usecase`/`repository`/UI/Infrastructure；不承载持久化引擎细节 | pending |
| `view` | UI | SwiftUI `View`：只展示 + 输入，无业务 | 依赖 `viewmodel`（`@ObservedObject`/`@StateObject`）；禁含业务逻辑、禁 View 间直接导航（走 `coordinator`）、禁直接访问持久化（走 `repository`） | pending |
| `coordinator` | App | `AppCoordinator` 导航编排 + FactoryKit DI 装配（`Container` 注册/解析） | 编排 `view`/`viewmodel`/`usecase` 的装配与导航；禁承载业务规则；禁 `view` 绕过 coordinator 跳转 | pending |
| `external` | Infrastructure | 外部集成：网络（URLSession/Moya）/三方 SDK/WCDBSwift 持久化引擎/平台通道/iOS 交付面（PrivacyInfo/entitlements/StoreKit） | 被 `repository` 实现持有；禁承载业务规则与业务终态判定；只暴露技术合同 | pending |

**doc_type 严格七类**：上表七个名称是全程唯一合法集合。任何索引项、骨架、trace、gate 判定只允许使用这七个 token，禁止改名、禁止增减、禁止换数（不得出现第八类，也不得把七类压缩成更少）。

**承载形态按链型分轨**（轨道判定见概要 L1 §2）：

- **full 链（目录级设计包）**：每个 `chapter_target` 独立一个 `design_package/chapters/<slug>.md` 文件（文件名与概要承接索引一致，gate 检查双向闭合）。执行采用 **directory_precheck + chapter_loop**（合同见 §5）：先确认 design-main.md 承接索引存在且非空（缺失/为空 → 回退概要，禁止详细补造），再**逐章或小批次**生成正文——禁止一次性全量输出全部章节（全量输出必然退化为大纲级薄文档）。
- **light 链（单文件）**：合并为任务内 `design.md` §2 单文档多章节，每章仍须独立满足对应合同。

**pending L2 拦截（full 链）**：承接索引命中 L2 状态为 pending 的 doc_type（`domain-model`/`view`/`coordinator`/`external`）时，必须在 design-main.md 显式声明 `L2豁免：<doc_type> 理由：…`（说明按本文 §3 合同八问展开的风险与补齐计划），否则 gate 拦截；首选做法是先补齐对应 L2 再进详细设计。v1 类型（`viewmodel`/`usecase`/`repository`）命中时不需要豁免，直接按 L2 差异规则展开。

## 3. 合同八问（所有 doc_type 通用骨架）

**编号纪律**：

- 行为编号 `BHV-NNN`：在 prd 标题中定义（语义化标题），下游一律以裸 token 引用。
- 设计单元编号 `UNIT-<slug>`：每个设计单元以 `### UNIT-<slug>` 标题定义（语义 kebab-case），测试与实现切片对单元的引用一律写 `UNIT-<slug>` 裸 token。
- **编号断链拦截**：任一 `BHV-NNN` 引用在 prd 中不存在（幽灵引用），或任一 `UNIT-<slug>` 无承接行为 / 无下游 trace，均被 gate 断链拦截（P1）。引用必须双向闭合：UNIT → BHV 可在 prd 命中；BHV → UNIT 可在详细设计命中至少一个 owner 单元。

每个设计单元必须回答以下八问，缺一不可（括号内为可验证信号——审核按此取证）：

1. **承接哪些行为**：逐条引用 `BHV-NNN` 裸 token（必须存在于 prd——幽灵引用与无承接行为均被 gate 断链拦截）；同时回指概要归属表行（owner 一致）。
2. **输入 / 输出 / 错误结果**：类型、取值域、错误枚举（输入/输出各有参数表；错误用 `enum Error` 表逐行列出，遵守 golden-path「`enum Error` 分层定义」——错误枚举归属层与本单元 owner 层一致，见 §4 表合同）。
3. **读取 / 写入哪些状态**：明确读写分离；写 owner 必须与概要归属一致（可回指归属表行）。`viewmodel` 写 `@Published` 状态；`usecase` 写业务状态；`view` 不写任何持有态（只持有 `@ObservedObject`/`@StateObject` 引用）。
4. **调用哪些依赖，不调用哪些依赖**：正反两面都写（防止越层）；依赖必须出现在概要架构图/归属表中，且方向遵守分层依赖律（§6）。FactoryKit `@Injected` 注入的依赖逐条列出，禁止手动 `init` 初始化被注入依赖。
5. **失败如何收口**：每条失败路径的处置（重试/降级/上抛/用户提示），错误转换位置遵循 `[SLOT-error-mapping]`（`enum Error` 转换发生在 `repository` 实现边界，UI 层只消费已归一的 Domain 错误；异常表逐行可对应一条失败路径 BHV 或八问 1 的行为分支）。
6. **产生哪些事件 / 后置结果**：`@Published` 发射、Combine/通知发布、埋点、副作用、导航请求（逐条写明消费方；导航请求的消费方必须是 `coordinator`）。
7. **哪些测试验证它**：映射到测试分层（unit / view（SwiftUI 快照或交互）/ integration / manual），逐行为给测试点（成功 + 全部失败路径）；测试框架按 `project-conventions` 槽位（XCTest → Quick/Nimble），mock 按槽位（手写 → Mockolo）。
8. **哪些内容不得在此补造**：显式列出本单元不拥有的决策（如 `view` 写「不决定状态转移——属 viewmodel」；`viewmodel` 写「不决定缓存策略——属 repository」；`repository` 接口写「不决定 DDL/网络协议——属 external 实现」）。

### 3.1 粒度标准（四条，写作与审核共用）

1. **可直接实现**：每个行为步骤具体到开发者可直接编码，不需要再分解业务逻辑或补充判定。
2. **明确调用关系**：每步指明调用的具体行为——下层组件的行为名与参数（如 `recipeRepository.fetch(id:)`）、本单元内部行为（`private` 方法）、外部依赖的具体调用。
3. **完整调用链**：从入口行为出发可追踪到所有下级行为，构成完整调用关系（与概要时序图一致）。
4. **粒度一致**：同一文档内所有行为描述粒度一致。

正反例（iOS / Swift）：

✅ 合格粒度——`viewmodel` 的 `submit()` 行为执行流程：
1. 调用本单元 `private func validateInput()`（邮箱格式 + 密码长度）；失败 → 置 `state = .error(.invalidInput)`，流程终止。
2. 置 `state = .loading`，`await authUseCase.login(email:password:)`（依赖经 `@Injected` 注入）。
3. 成功 → 业务会话态写入 owner 为 `AuthUseCase`（本单元不持有会话），随后发出导航请求 `coordinator.showHome()`。
4. 捕获 `AuthError.network` → 置 `state = .error(.networkRetry)`；`AuthError.invalidCredential` → 置 `state = .error(.badCredential)`。

❌ 不合格——`submit()` 行为：验证输入，调用登录，处理结果，更新界面。（无调用对象、无失败分支、无状态写入点、无 owner 声明）

### 3.2 类型差异挂载点（v1 三类 L2 入口）

合同八问是跨类型完成条件；以下差异由对应 L2 文件细化（命中即装载，冲突时 L1 > L2）：

- `viewmodel` → `detail-type-viewmodel.md`：八问 3（状态机/三态）与八问 6（`@Published` 发射）的强约束；生命周期（`onAppear`/`task`/订阅取消）；导航请求只产出不消费。
- `usecase` → `detail-type-usecase.md`：八问 1（核心能力 owner 承接，对齐 §3.6 capability handoff）与八问 5（业务失败终态收口）的强约束；零 UI 依赖断言。
- `repository` → `detail-type-repository.md`：八问 2（接口签名 vs 实现合同分离）与八问 5（`enum Error` 转换点 `[SLOT-error-mapping]`）的强约束；local/remote 编排与缓存回落决策 owner。

pending 四类（`domain-model`/`view`/`coordinator`/`external`）无 L2 文件，全部按本文 §3 合同八问 + §4 骨架 + 下表类型专属要点展开，并在文档头标注 `l2_status: pending`：

- `domain-model`：八问退化——只强约束 2（类型/`enum`/`enum Error` 签名）、5（不变量违反的错误语义）、8（零依赖断言：不补造任何 usecase/repository/UI 引用）；八问 1/3/4/6/7 中行为类项写 `N/A：值类型无运行时行为`，但不变量校验若存在则按行为展开并配测试。
- `view`：强约束 2（输入事件 → 回调签名）、4（只依赖 `viewmodel`，反面禁业务/导航/持久化）、6（事件回调与导航请求消费方）、8（不拥有状态转移/业务/导航决策）；状态读为只读（绑定 `@Published`）。
- `coordinator`：强约束 4（装配哪些 `view`/`viewmodel`/`usecase`，FactoryKit `Container` 注册项逐条列出）、6（导航后置结果与栈变化）、8（不拥有业务规则）；八问 2 用导航路由表（route → 目标 + 参数 + 装配依赖）表达。
- `external`：强约束 2（网络 req/resp model 或 SDK/引擎调用合同签名）、5（技术错误归一为 Domain `enum Error` 的转换边界）、8（不拥有业务规则/业务终态判定）；涉及交付面（PrivacyInfo/entitlements/StoreKit）的合规依据逐条落点。

## 4. 章节正文骨架合同（chapters/<slug>.md 模板）

full 链每个章节文件按以下骨架撰写（light 链 design.md §2 的每章同构，可压缩小节层级）。骨架与合同八问的映射在末表——**模板是表达形式，八问是完成条件**，二者必须同时满足。

```markdown
# <chapter_target> 详细设计

> doc_type：<七类之一> ｜ l2_status：v1 / pending（pending 须有 L2豁免）
> owner 层：UI / App / Domain / Infrastructure（与 doc_type 一致）
> 承接索引：design-main.md 第 7 节 <chapter_target> ｜ 返回：[design-main](../design-main.md)

## 1. 单元职责
本章承载的 UNIT-<slug> 清单与一句话职责；与依赖/被依赖单元的关系（调用谁的什么行为、被谁调用）。依赖方向声明（必须符合 §6 分层依赖律）。

## 2. 行为定义
### 2.1 行为清单（每行为一行：行为名 + 简述 + 承接的 BHV-NNN 编号）
### 2.2 接口定义（Swift 签名级，禁止超过签名级的实现代码）
``swift
// Domain 层接口示例（repository / usecase）
protocol IRecipeRepository {
    func fetch(id: String) async throws -> Recipe
    func observe(id: String) -> AnyPublisher<Recipe, Never>
}
``
（viewmodel 写 `final class XxxViewModel: ObservableObject { @Published ... ; func ... }` 签名；view 写 `struct XxxView: View { @ObservedObject var vm: XxxViewModel ; var body: ... }` 要点；coordinator 写导航方法签名；external 写网络/SDK 调用签名）

## 3. 核心数据结构
### 3.1 数据模型（Swift struct/class/enum 签名级；序列化方案按 project-conventions JSON 槽位；domain-model 单元此节为主体）
### 3.2 错误类型表（enum Error，分层定义）
| 错误名 | 枚举 case | 语义 | 归属层 | 转换/收口位置 |

## 4. 逐行为设计（每个行为一小节）
### 4.x <行为名>
- 函数签名（Swift）
- 行为简述（一句话 + 承接 BHV-NNN 编号）
- 输入参数表：| 参数 | 类型 | 取值域/约束 | 必填 |
- 输出表：| 返回值/发射值 | 类型 | 语义 |
- 依赖调用表（八问 4）：| 依赖 | @Injected 注入 | 调用的行为 | 不调用边界 |
- 执行流程（mermaid sequenceDiagram，参与者用真实组件名，步骤编号）
- 流程详述（编号列表，与图中编号一一对应，满足 §3.1 粒度标准）
- 异常处理表：| 异常情况 | 处置（重试/降级/上抛/提示） | 错误转换位置（[SLOT-error-mapping]） |

## 5. 状态管理（viewmodel 必含；usecase 有业务状态时必含；无状态单元写 N/A）
状态字段定义（含初始态）+ 三态（loading/success/error）+ 状态转移（mermaid stateDiagram 或转移表）+ 写 owner 声明（@Published owner / 业务态 owner）。

## 6. View 设计（仅 view 类）/ 导航设计（仅 coordinator 类）
- view：组件层级（SwiftUI body 结构要点）、交互（手势/输入 → 回调）、响应式适配（`GeometryReader`/size class 要点）、状态绑定（只读消费 @Published）。
- coordinator：导航路由表（route → 目标 view + 参数 + 装配依赖）、FactoryKit `Container` 注册项、栈/呈现方式（push/sheet/fullScreenCover）。

## 7. 测试映射
| BHV/行为 | 测试层（unit/view/integration/manual） | 测试点（成功+失败路径逐条） | mock 对象（手写/Mockolo） |

## 8. 不得补造清单
本单元不拥有的决策逐条列出（含越层禁止项，回指 §6）。
```

**骨架 ↔ 八问映射**：

| 模板节 | 满足八问 |
|--------|---------|
| 1 单元职责 | 八问 4（依赖正反面的「谁」） |
| 2 行为定义 | 八问 1（BHV 承接）+ 2（签名） |
| 3 核心数据结构 | 八问 2（类型/`enum Error` 枚举） |
| 4 逐行为设计 | 八问 2/4/5/6（流程、依赖调用、失败收口、事件） |
| 5 状态管理 | 八问 3（读写状态与 owner） |
| 6 View/导航设计 | 八问 6（view 交互回调 / coordinator 导航后置） |
| 7 测试映射 | 八问 7 |
| 8 不得补造清单 | 八问 8 |

辅助性文本（描述、表格、图内标签）一律中文；代码语法元素（类名/方法名/参数名/字面量/`@Published`/`@Injected` 等关键字）保持英文。

## 5. chapter_loop 执行合同（full 链）

### 5.1 directory_precheck（写作/审核共用前置）

进入任何章节写作前确认：① design_package 路径合法且 `chapters/` 存在；② design-main 承接索引非空且每条有目标文件名与 `doc_type`（七类之一）；③ pending L2 命中项（`domain-model`/`view`/`coordinator`/`external`）均有 `L2豁免` 声明；④ `technology_decision_handoff[]` 中被本批引用的条目状态为「选定」（未选定 → 回退概要，禁止详细拍板，如 URLSession vs Moya、SwiftyBeaver→OSLog 迁移取舍未定时不得在详细阶段私选）。任一失败 → 停止，输出缺口与概要修订动作。

### 5.2 推荐写作顺序（自底向上，对齐 DDD 依赖方向）

1. **domain-model**——实体/值对象/`enum Error`/不变量先固化（零依赖，被各层导入）。
2. **repository**（接口在 Domain，实现在 Infrastructure）——按 usecase 的数据依赖合同展开；接口先行，实现随后。
3. **usecase**——业务规则与状态 owner，依赖 repository 接口与 domain-model。
4. **viewmodel**——状态容器，依赖稳定的 usecase 行为。
5. **view + coordinator**——view 只做展示/输入到 viewmodel 的绑定；coordinator 收口导航与 DI 装配。
6. **external**（横切）——被 repository 实现引用的网络/SDK/WCDBSwift/交付面一等合同收口。

同一 feature 的 usecase 及其直接 repository（含接口与实现）视为同一小批次优先完成。

### 5.3 批次与自动审修闭环

- 每批 **1~3 章**；禁止一轮生成全部章节。
- 每批生成后**立即自动 review**（不等用户）：章节模板符合性（§4）、八问完成条件（§3）、粒度（§3.1）、依赖与概要归属一致、分层依赖律（§6）、L2 差异规则（命中 v1 类型时）、编号断链（§3 编号纪律）。
- 有 finding → 按 §9 判定修订形态 → 直接修复 → 复查受影响的行为/依赖/跨章引用。
- 当前批所有规则均有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。
- 只有「概要源缺失 / 业务语义必须人工确认 / 技术决策未选定 / 修复无法收敛」时才中断并升级用户。

### 5.4 层级 checkpoint

每完成一个层级（§5.2 的分组）执行跨章核对，失效项回到对应批次重走审修闭环：

- domain-model 后：实体/`enum Error` 零依赖（无任何 usecase/repository/UI 导入）；不变量校验行为有测试。
- repository 后：接口在 Domain、实现在 Infrastructure；usecase 声明的数据依赖全部有承接接口；错误转换位置（`[SLOT-error-mapping]`）只在实现边界；缓存/落库决策只在 repository 实现。
- usecase 后：UNIT↔BHV 承接闭合；业务状态写 owner 唯一；usecase 间依赖单向无环；零 UI 依赖。
- viewmodel 后：`@Published` 状态写 owner 唯一；导航请求只产出不消费；只调用稳定 usecase 行为。
- view + coordinator 后：view 无业务/无直接导航/无持久化访问；导航全部经 coordinator；FactoryKit `Container` 注册项与各单元依赖闭合；与概要页面流图、时序图一致。
- external 后：网络/SDK/WCDBSwift 合同被 repository 实现闭合；技术错误归一为 Domain `enum Error`；交付面（PrivacyInfo/entitlements/StoreKit）合规依据逐单元可定位。

### 5.5 完成判定输入

目录级完成 = 全部 chapter_target 的 `chapter_status=passed_by_method_evidence` + 各层级 checkpoint 通过 + gate 章节闭合（索引↔文件双向）通过 + 编号双向闭合（BHV↔UNIT）无断链。

## 6. 分层依赖律与禁止补造清单（详细阶段红线）

### 6.1 分层依赖律（归属硬基准，违反直接 fail）

- **Domain 零依赖**：`domain-model`、`usecase`、`repository` 接口只依赖 Foundation 级基础类型，不导入 App/Infrastructure/UI 任何类型。
- **依赖方向 Domain → App → Infrastructure → UI 单向**：禁止反向依赖与环。`usecase` 不依赖 `viewmodel`/`view`/`coordinator`；`domain-model` 不依赖任何上层。
- **禁 View 间直接导航**：`view` 不得直接持有或跳转到另一个 `view`/路由；所有导航请求交 `coordinator`。
- **禁 View 直接访问持久化**：`view` 不得直接调用 WCDBSwift/`repository` 实现；数据走 `viewmodel` → `usecase` → `repository` 接口。
- **repository 接口/实现分离**：接口在 Domain（被任意层导入），实现在 Infrastructure（持有 `external`）；调用方只依赖接口，不依赖具体实现类型。

### 6.2 禁止补造清单

- 不得新增概要归属表之外的结构（发现缺口 → 回退概要补归属，再回详细）。
- 不得变更概要已定的 owner、技术决策、scope。
- 不得把 `technology_decision_handoff[]` 中「未选定」的决策在详细阶段私自拍板（如 URLSession/Moya、XCTest/Quick+Nimble、SwiftyBeaver/OSLog 的迁移取舍）。
- 不得写实现代码/伪代码超过签名级（方法签名、数据结构定义为上限）。
- 命名、目录、序列化、DI、持久化、日志门面等取值不得偏离 project-conventions 槽位与 golden-path 硬规则（FactoryKit `@Injected`、Repository 模式、`enum Error` 分层、WCDBSwift、`ObservableObject`+`@Published`、`private extension`）。
- 不得自创七类之外的 `doc_type`（含照抄 flutter/backend 的类型名）。

## 7. 完成判定与 Gate

详细设计可进入编码，当且仅当（G1~G5 两轨共用；G6~G8 仅 full 链强制）：

- G1 承接索引的每个条目都有对应详细设计单元，无遗漏；每个单元 `doc_type` ∈ 七类。
- G2 每个单元的合同八问完整；字段/接口/状态可追溯到概要 owner；满足 §3.1 粒度标准。
- G3 每条行为有测试映射（八问之 7），覆盖成功路径 + 全部失败路径；测试框架与 mock 方式符合 project-conventions 槽位。
- G4 涉及权限/数据采集/三方域名/PII/交付面（PrivacyInfo/entitlements/StoreKit）的单元附合规依据；无私有 API、动态代码执行、制裁 TLD 类设计。
- G5 八问之 8（不得补造清单）逐单元存在，含越层禁止项。
- G6 章节闭合：索引↔chapters/ 文件双向闭合；每章符合 §4 骨架合同；pending L2 命中项（`domain-model`/`view`/`coordinator`/`external`）`L2豁免` 齐全。
- G7 分层依赖律（§6.1）全过：Domain 零依赖、单向无环、view 不导航/不持久化、repository 接口实现分离。
- G8 chapter_loop 证据 + 编号闭合：逐章 `chapter_status=passed_by_method_evidence`，层级 checkpoint 全过，无「一轮全量生成」迹象（多章雷同骨架、无单元级实质内容）；BHV↔UNIT 双向闭合无断链（无幽灵 `BHV-NNN`、无无承接 `UNIT-<slug>`）。

## 8. 审核基线

- 先证据后结论；finding 带文档/章节/UNIT 锚点。
- 严重度：P1（违反 §6 红线、分层依赖律违反、八问缺项、追溯断链（BHV/UNIT 编号断链）、合规缺失、章节闭合失败、`doc_type` 越七类——阻塞）；P2（合同不完整但可局部补，如 `enum Error` 枚举不全、粒度局部不达标、测试漏失败路径）；P3（表述建议）。
- 互斥分支：前置失败 → 只输出前置缺口；前置通过 → findings + 概况 + 三选一结论（可进入编码 / 带假设可进入 / 不可进入）。
- 详细设计文档无存量豁免（新文档全量合规）；存量豁免仅适用于实现阶段代码。
- 逐 doc_type 检查矩阵与判级细则、输出字段合同由 review skill 的 `references/` 承载（编排层产物，不得与本文冲突）。

## 9. 修订形态判定

- **局部修订**：补 `enum Error` 枚举、补测试映射、补一条依赖声明（含 `@Injected` 项）、补一张时序图、补一条不得补造项。
- **文档级重构**：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档迹象）、分层依赖律系统性违反（如 view 普遍直连持久化、usecase 依赖 viewmodel）、`doc_type` 系统性越界。
- 发现概要缺陷（归属错、索引漏、技术决策未选定）→ 回退概要修订，禁止在详细阶段就地改归属或私自拍板。
