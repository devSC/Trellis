# Harness — iOS 原生平台五阶段方法 SSOT 入口

> 本文件是 **Guru iOS 原生平台（SwiftUI + DDD 四层）** 五阶段方法的唯一入口。
> 模型对齐 `guru-flutter-client` 同名 SSOT，但 **doc_type 与分层归属一律以本文 §3 钉死的七类为权威**——禁止照抄 flutter 的 `controller / page-entry / service / db-dao / api-network` 或 Go 平台的类型名。
> 实测来源：`story-verse-mac`（SwiftUI 主 + RxSwift 遗留、FactoryKit DI、WCDBSwift 持久化、AppCoordinator 导航）。证据锚点见 §3 表与 §6 各 Gate。
> 层级契约：本文（harness 入口）承载阶段映射、doc_type 权威表、编号纪律、Gate 口径；writing/review skill 的 `references/` 只承载编排细则、模板与示例；冲突时 本文 > L2 > references > SKILL.md。
> 项目实际按层模式见 `.trellis/spec/<layer>/`（by-layer 项目 spec，`ios/` + `shared/`，由 `00-bootstrap-guidelines` 扫真实项目填实）；本 harness 只承载方法学，不写项目实例。

---

## 1. Pre-Development Checklist（每个任务开始前，逐项落盘到 jsonl）

进入任何阶段前必须依次确认，任一失败即停止并先补前置：

- [ ] 读 `.trellis/spec/conventions/project-conventions.md` 并通过其校验清单 C1~C6（缺失/未填 → 停止，先完成项目约定，见 §5 槽位清单）。
- [ ] 读 `.trellis/spec/guides/golden-path.md`（iOS 分层依赖律 Domain→App→Infrastructure→UI 单向、FactoryKit DI 强制、Repository 模式强制、WCDBSwift 持久化、禁止清单）。
- [ ] 按本任务所处阶段读对应 SSOT（§2 映射表），并把所读文件登记进任务的 `implement.jsonl` / `check.jsonl`（带 reason）。
- [ ] 若本任务处于 planning Gate 或准备 `task.py start`，读 `.trellis/spec/harness/gate/gate-confirmation-model.md`。
- [ ] 确认 task.json `guru_chain`（full / light）；full 链另须确认 `design_package` 路径已声明或将在概要阶段 0 声明。
- [ ] 产物语言：中文优先——英文仅限 Swift 标识符（类名/方法名/属性名/enum case）、命令、路径、协议字段、框架名（SwiftUI/RxSwift/FactoryKit/WCDBSwift）、缩写、原文引用。
- [ ] iOS golden-path 五条硬规则在场可执行：FactoryKit `@Injected` DI（禁手动 `init` 装配）/ Repository 模式强制 / `enum Error` 分层定义 / WCDBSwift 持久化（禁 CoreData/SwiftData）/ ViewModel = `ObservableObject + @Published`（私有方法落 `private extension`）。

---

## 2. 阶段 → 产物映射

**双轨制**：task.json `guru_chain` 判轨（`guru_after_create` 创建默认 `full`）。full=完整五阶段链，需求走正式需求包、设计走目录级设计包（task.json `design_package`）；light=轻量链（分流 + 用户同意后显式降级），产物为任务内单文件。下表产物列写作 `full / light`。

| 阶段 | 产物（full / light） | 装载路径（安装后） |
|------|---------------------|-------------------|
| 需求 | 正式需求包（requirement-writing 撰写 + requirement-review 门禁）+ `prd.md` 行为规格抽取 / 仅 `prd.md` | guru-ai-guides `requirement-writing`、`requirement-review` skill 及其标准包 `requirement-doc-standard`（**硬前置：未安装即停**）；jsonl 引用安装路径 |
| 概要设计 | `design_package/design-main.md`（含归属判定表 + `chapter_target → ios doc_type` 承接索引 + `technology_decision_handoff[]`）/ `design.md` §概要 | `.trellis/spec/harness/overview/overview-structure-single-source.md` |
| 详细设计 | `design_package/chapters/*.md`（逐章）/ `design.md` §详细 | `.trellis/spec/harness/detail/detail-structure-single-source.md` + 涉及类型的 §3 七类 L2（v1 提供 `detail-type-viewmodel.md` / `detail-type-usecase.md` / `detail-type-repository.md`；其余四类 `domain-model / view / coordinator / external` 为 pending） |
| 实现 | Swift 代码 + `implement.md`（trace 计划合同与 mutable evidence）/ 同 | `.trellis/spec/guides/golden-path.md` + `.trellis/spec/harness/implementation/implementation-trace-contract.md`（追踪合同：trace 计划合同与 mutable evidence）+ `.trellis/spec/harness/implementation/implementation-ios-standard.md`（L1 编码标准：golden-path 锁定项 LOCK-1~7 / doc_type 权威七类 / 可编码合同八问基线）。两文件职责分工：**trace-contract = 追踪合同**（钉 `implement.md` 计划合同、mutable evidence 边界与切片挂 `UNIT` 编号）；**ios-standard = 编码标准与审核基线**（钉 LOCK 锁定项、合同八问、实现 Gate 与存量豁免口径），同源被代码编写与实现审核引用 |
| 审核 / 复盘 | findings + spec 回写 / 同 | 各 SSOT 审核基线章节 + `.trellis/spec/harness/extraction-template.md` |

Guru Gate、review_runs 证据、confirm 快照、累积 digest 与失配恢复流程见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。摘要：requirements 结构通过后先运行 opposite-provider adversarial requirements review，clean/requirements-ready 后由用户确认；overview/detail 由当前 digest 下两个不同 run-id 的 clean review 记录驱动；detail 双 clean 后再由用户确认。

> 装载约定：所有阶段文件以 **安装后路径** `.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md` 装载并写入 jsonl；不要引用模板仓库内的源路径。

---

## 3. iOS 详细设计 doc_type 权威七类（全程唯一，禁止改名 / 增减 / 换数）

> 这七类是 **IOS_BRIEF 钉死的权威集合**。概要承接索引、详细章节 doc_type、`guru_gate.py` 的 `_index_doc_types` 命中判定、L2 豁免判定全部以本表为准。
> 不得自创 `transport-handler / service / page-entry / db-dao / api-network / manager / handler` 之类——出现即归属红线（详细 Gate 直接 fail）。

| # | doc_type | 覆盖对象（一句话职责） | owner 层 | L2 状态 | 证据锚点（story-verse-mac 实测） |
|---|----------|----------------------|----------|---------|-------------------------------|
| 1 | `viewmodel` | UI 层 `ObservableObject + @Published` 状态容器：状态字段、事件→状态转移、流订阅、生命周期、三态 | UI | **v1 提供**（`detail-type-viewmodel.md`） | `StoryVerse/UI/Features/Home/`、`StoryVerse/UI/States/` |
| 2 | `usecase` | Domain 业务编排（零 UI 依赖）：有状态业务流程、业务 API、状态写 owner | Domain | **v1 提供**（`detail-type-usecase.md`） | `StoryVerse/App/UseCases/`、`StoryVerse/Domain/Services/` |
| 3 | `repository` | Domain `IXxxRepository` 接口 + Infrastructure 实现（**合并一类**）：数据访问合同、local/remote 编排、缓存回落、错误转换点、mapper | 接口=Domain / 实现=Infrastructure | **v1 提供**（`detail-type-repository.md`） | `StoryVerse/Domain/Repositories/`（接口）、`StoryVerse/Infrastructure/Persistence/`（实现） |
| 4 | `domain-model` | Domain 实体 / 值对象 / `enum Error` / 不变量（**零依赖、可被任意层导入**） | Domain | pending（按 §4 合同八问展开，标 `l2_status: pending`；full 链须 `L2豁免`） | `StoryVerse/Domain/Entities/`、`StoryVerse/Domain/ValueObjects/`、`StoryVerse/Domain/Enums/`、`StoryVerse/Domain/Errors/` |
| 5 | `view` | UI 层 SwiftUI `View`（只展示 + 输入，无业务、无导航发起、无持久化访问） | UI | pending（同上） | `StoryVerse/UI/Features/Home/` |
| 6 | `coordinator` | App 层 `AppCoordinator` 导航 + FactoryKit DI 装配（`@Injected` Container 注册） | App | pending（同上） | `StoryVerse/App/Coordinators/`、`StoryVerse/App/DependencyInjection/` |
| 7 | `external` | Infrastructure 外部集成：网络（URLSession/Moya）/ SDK / WCDBSwift 持久化引擎 / 第三方 | Infrastructure | pending（同上） | `StoryVerse/Infrastructure/Persistence/DatabaseManager.swift`、`StoryVerse/Infrastructure/Services/` |

**L2 提供与对应关系（v1 三类，与 flutter `controller / usecase / repository-datasource` 三类一一对应）**：

| iOS v1 L2 | flutter 对应 | 差异要点 |
|-----------|-------------|----------|
| `detail-type-viewmodel.md` | `detail-type-controller.md` | 基类从 `LifecycleController`（GetX）改为 `ObservableObject + @Published`；命令方法 + 生命周期 `onAppear/onDisappear`；订阅在销毁处收口（RxSwift `DisposeBag` 或 Combine `cancellables`）；私有方法落 `private extension` |
| `detail-type-usecase.md` | `detail-type-usecase.md` | Domain 零 UI 依赖；FactoryKit 注册而非 `@LazySingleton`；流形态 SwiftUI 用 `@Published`/Combine、遗留用 RxSwift `Observable`；状态唯一写 owner 不变 |
| `detail-type-repository.md` | `detail-type-repository-datasource.md` | **接口与实现合并为一类**（接口在 Domain `Repositories/`、实现在 Infrastructure）；持久化经 WCDBSwift（禁 CoreData/SwiftData）；底层异常→`enum Error` 映射表必填 |

**pending 四类展开规则**：`domain-model / view / coordinator / external` 在 v1 无独立 L2，必须按 §4 合同八问展开并在章节文档头标注 `l2_status: pending`；**full 链须在 design-main.md 显式声明 `L2豁免：<doc_type> 理由：…`**（说明按八问展开的风险与补齐计划），否则 `_check_pending_l2` 拦截。首选做法是先补齐对应 L2 再进详细设计。

---

## 4. 五阶段口径要点（写作骨架）

> 完整规则正文在各 SSOT；本节只钉 iOS 平台的差异硬点与编号纪律，供入口快速对齐。

### 4.1 编号纪律（贯穿五阶段，机器追溯依据）

- **行为**：`### BHV-NNN <短名>`（prd 标题，`guru_gate.py` 正则 `^#{2,5}\s+BHV-\d+`）。创建后不复用、不重排，删除留洞。
- **设计单元**：`### UNIT-<slug>`（详细章节标题，语义 kebab-case，正则 `^#{2,5}\s+UNIT-[a-z0-9][a-z0-9-]*`）。
- **下游引用一律写裸 token**（`BHV-001`、`UNIT-home-viewmodel`）——归属表、详细单元、测试映射、实现切片对行为/单元的引用全部用编号；`guru_gate.py trace-matrix` 据此生成 行为×需求场景×归属×单元×测试×切片 矩阵，断链被 Gate 拦截。
- **需求源回指（full 链，REQ-UC ↔ BHV）**：BHV 标题可在短名前以 `[REQ-UC-XXX]`（多对多）承接需求源场景（`### BHV-001 [REQ-UC-005] <短名>`）；`trace-matrix` 增 REQ-UC 列（行展开），`trace-aggregate <version-dir>` 聚合多 task 进版本级 `traceability.md`；`--require-req-uc`（或 task.json `require_req_uc:true`）强制 BHV 须带 REQ-UC，旧 prd 默认不拦、列空、不断链。**命名消歧**：`REQ-UC-XXX`（需求源场景）≠ overview `UC-<序号>`（架构核心用例），两套独立编号（详见 overview-structure §3.4）。
- slug 建议带 doc_type 后缀以自证归属：`UNIT-<feature>-viewmodel` / `-usecase` / `-repository` / `-model` / `-view` / `-coordinator` / `-external`。

### 4.2 概要：归属判定（按 iOS 七类 owner 层）

行为枚举禁止从名词/组件出发，按 用户操作 → 系统反应 → 失败路径 → 生命周期 顺序枚举，每条 `Given/When/Then` 并标状态与数据。归属判定按下表定唯一 owner，每行回答三问（为什么属于它 / 为什么不属于别人 / 为什么需独立存在）：

| 行为 / 状态类型 | 归属（iOS 七类） | owner 层 |
|----------------|-----------------|----------|
| SwiftUI 界面结构、交互响应、主题 token 消费 | `view` | UI |
| 页面状态字段、事件分发、流订阅、三态 | `viewmodel` | UI |
| 有状态业务流程、业务规则、响应式流 | `usecase` | Domain |
| 数据访问合同、缓存策略、错误转换、local/remote 编排 | `repository`（接口=Domain，实现=Infrastructure） | Domain / Infrastructure |
| 实体、值对象、`enum Error`、不变量 | `domain-model` | Domain |
| 页面间导航、路由、DI 装配 | `coordinator` | App |
| 三方 SDK、网络引擎、WCDBSwift 持久化、平台集成 | `external` | Infrastructure |

承接索引每条 `chapter_target → ios doc_type`（full 链另落 `chapters/<slug>.md` 文件名）；归属表全部 owner 必须被索引覆盖，gate 查双向闭合。

### 4.3 详细：合同八问（七类通用骨架）

每个 `UNIT-<slug>` 必须回答（缺一不可，括号为可验证信号 / iOS 特化）：

1. **承接哪些行为**：逐条引用 `BHV-NNN`（须存在于 prd——幽灵引用被 `unit_ghost_bhv` 拦截）。
2. **输入 / 输出 / 错误结果**：Swift 签名级（方法名 / 参数 / 返回类型 / `async throws`）；错误用 **per-domain `enum Error`** 枚举；`viewmodel` 须逐 `@Published` 字段列名称/类型/初始值/写入时机 + loading/empty/error 三态去向。
3. **读取 / 写入哪些状态**：读写分离；写 owner 与概要归属一致（业务状态归 `usecase`，页面状态归 `viewmodel`，**禁两个 viewmodel 写同一业务状态**）。
4. **调用哪些依赖 / 不调用哪些依赖**：正反两面（FactoryKit `@Injected` 注入接口；`view` 不发起导航、不访问持久化；`viewmodel` 只注入 `usecase`/`repository` 接口，不碰实现/`DatabaseManager`/网络类）。
5. **失败如何收口**：每条失败路径处置（重试/降级/上抛/用户提示）+ 错误转换位置（底层异常→`enum Error` 映射表逐行对应一条失败 BHV）。
6. **产生哪些事件 / 后置结果**：`@Published` 发射 / Combine/RxSwift 流时序 / 埋点 / 导航动作（去哪个 route，带什么参数）/ 副作用逐条写消费方。
7. **哪些测试验证它**：映射测试分层（XCTest unit / Quick-Nimble / UI test / manual）；逐行为给成功 + 全部失败路径测试点；`usecase` 是测试密度最高层。
8. **哪些内容不得在此补造**：显式列本单元不拥有的决策（如 `view` 不发明业务规则、`usecase` 不决定持久化介质、`viewmodel` 不决定缓存策略）。

粒度标准四条（可直接实现 / 明确调用关系 / 完整调用链 / 粒度一致）。章节正文按 detail L1 §4 骨架（单元职责 / 行为定义 / 核心数据结构 / 逐行为设计含 mermaid sequenceDiagram / 状态管理 / View 设计仅 `view`+`viewmodel` / 测试映射 / 不得补造清单）。

写作顺序（自底向上）：`domain-model` → `repository` → `usecase` → `viewmodel` → `view` + `coordinator`/`external` 横切。full 链每批 1~3 章，生成后立即自动 review，无未修复 finding 才记 `chapter_status=passed_by_method_evidence`。

### 4.4 实现：trace 计划合同与 mutable evidence

实现阶段装载两份 SSOT，职责分工：`.trellis/spec/harness/implementation/implementation-trace-contract.md`（**追踪合同**，钉 `implement.md` 计划合同、mutable evidence 边界与切片挂 `UNIT` 编号）+ `.trellis/spec/harness/implementation/implementation-ios-standard.md`（**L1 编码标准**，钉 golden-path 锁定项 LOCK-1~7、doc_type 权威七类、可编码合同八问与编码合同基线，同源被代码编写与实现审核引用）。

`implement.md` 必含计划合同，mutable evidence 必含执行/验证/阻塞偏差记录；切片挂 `UNIT` 编号（`slice_ghost_unit` 拦截幽灵单元）：

1. **计划**：每片承接 `UNIT-<slug>` + doc_type/文件范围 + 完成信号 + 验证方式；执行顺序按依赖自底向上。
2. **执行**：实际改动文件清单（相对路径）+ 与计划偏差原因 + 代码生成记录（Mockolo 生成 mock 等，按 `[SLOT-mock]`）。
3. **证据**：静态检查（`swift build` / SwiftLint）+ 测试命令与结果（测试名级，XCTest/Quick-Nimble）+ 未验证项（真机/双端差异留给 Manual QA）。
4. **阻塞与偏差**：上游缺陷回退详细阶段；存量违例触碰记 SLOT-16 编号；新决策点不私自拍板，升级人工 Gate。

---

## 5. project-conventions 槽位清单（C1~C6 校验对象）

iOS 平台必须在目标仓库 `project-conventions.md` 填齐以下槽位（编号体系与 `conventions/project-conventions.template.md` canonical 一致：SLOT-01~SLOT-16），未填即 Pre-Dev 停止：

| 槽位 | iOS 取值方向（story-verse-mac 现状 → 目标） |
|------|------------------------------------------|
| SLOT-01 UI 框架基线 / ViewModel 形态 | SwiftUI 主 + RxSwift 遗留 → 纯 SwiftUI（新代码禁新增 RxSwift）；`viewmodel` = `ObservableObject` + `@Published` |
| SLOT-02 DDD 四层目录分界与归属 | 七类 doc_type → owner 层 → 物理目录映射，不跨层混放 |
| SLOT-03 接口与命名约定 | 协议 `IXxx` 前缀，接口与实现分文件 |
| SLOT-04 错误类型与收口位置（enum Error 分层） | 每域一个 `enum XxxError: Error`，转换点固定在 repository/external 实现边界 |
| SLOT-05 FactoryKit DI 注册规范 | 强制 `@Injected`，禁手动 init 拼装 |
| SLOT-06 持久化方案 | WCDBSwift 唯一，禁 CoreData/SwiftData |
| SLOT-07 导航与 Coordinator | 跨页面导航走 `AppCoordinator`，禁 View 间直接导航 |
| SLOT-08 网络层 | URLSession / Moya（默认待定候选） |
| SLOT-09 日志 | SwiftyBeaver → OSLog（统一经 `ILogger` 门面） |
| SLOT-10 JSON 解析与修复策略 | 不可信 JSON 经 `IJSONRepairService` 修复，转换点对齐 SLOT-04 |
| SLOT-11 主题 | `ThemeManager` 单例 token 消费，view 禁硬编码尺寸/色值 |
| SLOT-12 i18n | `.lproj` / `Localizable.strings` key 受控同步 |
| SLOT-13 feature 模块结构 | `UI/Features/<Feature>/` 内 view + viewmodel + states 组织 |
| SLOT-14 测试约定 + mock 生成 | 测试 XCTest → Quick/Nimble；mock 手写 → Mockolo |
| SLOT-15 构建自动化 | Fastlane（默认待定候选，发布 lane 人工执行） |
| SLOT-16 存量违例清单 | 存量豁免唯一数据源（逐条登记，可为空但须显式声明「无」） |

> 项目级取值（目录、文件名、序列化风格、DI 注册形态）以 `project-conventions.md` 槽位为准，本文与 golden-path 不覆盖。
> 默认待定候选：SLOT-08 网络层、SLOT-15 构建自动化（待定 ≤ 2，各须写决策人与期限）。

---

## 6. 五道 Gate 口径（对齐 `guru_gate.py`，verify 脚本同口径）

> 结构底线由 `guru_gate.py` 检查（exit 0=通过/合法跳过，exit 2=拦截 + stderr 缺口清单）；语义判定由对应 review skill 人工 Gate 负责。括号内为脚本实际命中点。

- **需求 Gate**（`requirements`）：缺行为编号（`BHV-NNN` 标题）/ 缺行为规格（Given/When/Then 三段式）/ 缺核心能力清单（P0/P1 标记）/ 缺失败路径章 / 缺验收场景章 / 缺未决问题章（无未决也须显式声明）→ 任一缺即不进概要。**iOS 五要素**：行为 + 前置条件 + 状态变化 + 失败路径 + 验收场景。
- **概要 Gate**（`overview`）：缺行为→owner 归属表 / 归属表未引用 BHV 编号（追溯断点）/ 归属表缺三问理由 / 缺承接索引（`chapter_target → ios doc_type`）/ full 链承接索引未落 `chapters/<file>.md`；语义层另查归属违反 Domain→App→Infrastructure→UI 单向律（违反直接 fail）、状态非唯一写 owner、架构总览六件套缺项 → 任一缺即不进详细。
- **详细 Gate**（`detail`）：缺 `UNIT-<slug>` 编号 / 缺承接行为（八问之1）/ 缺失败收口（八问之5）/ 缺测试映射（八问之7）/ 缺不得补造声明（八问之8）/ `implement.md`（trace §1 计划）不存在 / 单元引用幽灵行为（`unit_ghost_bhv`）/ 行为无设计单元承接（`bhv_no_unit`）；full 链另查设计包骨架 + 章节闭合（索引↔`chapters/` 双向）+ pending L2 豁免（`domain-model/view/coordinator/external` 命中无 `L2豁免` → 拦截）→ 任一缺即不进实现。
- **实现 Gate**（`implement`）：`implement.md` 计划合同齐全（计划/切片）+ mutable evidence 齐全（执行/改动文件 · 证据/analyze·test · 阻塞/偏差）/ 切片挂 `UNIT` 编号 / 无幽灵单元（`slice_ghost_unit`）；项目级 `swift build`/SwiftLint/test/compliance 由 worktree.yaml 其余 verify 条目执行，任一无证据 → 不进 commit。
- **审核 / 复盘 Gate**：存量豁免判定（SLOT-16 内记债不阻塞；清单外新增违例阻塞）；设计文档本身无存量豁免（新文档全量合规）。复盘按 `extraction-template.md` 九段萃取，只沉淀"这类任务如何被做好"，不沉淀本次需求事实。

**追溯与缺陷回流**：`guru_gate.py trace-matrix <task_dir> --write` 生成追溯矩阵，`--strict` 在断链时 exit 2。缺陷只能回上游修——审核发现归属错/合同越界，回到拥有该决策的阶段修订，禁止下游补造。
