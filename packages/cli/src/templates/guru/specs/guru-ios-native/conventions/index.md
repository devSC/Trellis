# conventions/ 索引（Guru iOS 原生平台）

> 本文件是 iOS 原生 spec 库**项目约定槽位**的导航入口。它**只做导航与口径对齐**，不承载任何项目级取值正文。
> 平台档案来源：`story-verse-mac`（DDD 四层 + SwiftUI 主 + RxSwift 遗留 + FactoryKit DI + WCDBSwift 持久化）实测；方法学母版对齐 `guru-flutter-client` 同名 SSOT。
> 规则唯一真源：所有 writing/review skill 与 `guru_gate` 的硬前置**只装载本目录文件、不复写**；冲突时 L1（`harness/detail/detail-structure-single-source.md`）> L2（`harness/detail/detail-type-*.md`）> 本目录 references > SKILL.md。
> **doc_type 权威**：全程只认 iOS 七类（`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`）。本目录任何处不得出现 flutter 的 `controller` / `page-entry` / `service` / `db-dao` / `api-network` 等类型名，也不得自创 `transport-handler` / `service` 之类。

---

## 1. 三类文件职责（导航）

本目录采用「方法锁取值、取值不进配置包」的双层结构。三类文件各司其职，缺一不可：

| 文件 | 职责 | 谁维护 | 是否参与校验 |
|------|------|--------|:---:|
| `project-conventions.md` | **当前项目取值的唯一权威**。含元信息、SLOT-01~SLOT-16 取值（每槽位带代码证据路径）、校验清单 C1~C6、SLOT-16 存量违例清单。所有阶段硬前置只认本文件。**缺失时按下方模板复制建立并填写。** | 各 App 仓库（落位 `.trellis/spec/conventions/project-conventions.md`，PROTECTED） | ✅ 唯一生效 |
| `project-conventions.template.md` | **空槽位模板**（新项目起点）。复制 → 删说明 → 逐槽位填取值与证据。模板本身不生效，只作骨架。 | 配置包随版本演进 | ❌ |
| `story-verse.project-conventions.md` | **story-verse-mac 取值样例**（仅参考，演示一份填满的真实取值长什么样：SwiftUI 主 / FactoryKit / WCDBSwift / OSLog 等）。**不直接生效**，不参与任何校验。 | 配置包样例 | ❌ |

**铁律**：writing/review/Gate 的硬前置只读 `project-conventions.md`；`template` 与 `story-verse` 样例永不参与校验。一个新仓库若只放了 template 没填取值，视为「项目约定未就绪」，硬前置不通过。

> 与 flutter 母版的差异：flutter 样例为 `calorie` / `seek` 两份；iOS 平台样例锚定单一实测仓库 `story-verse-mac`（其余 App 接入时各自复制 template 落取值）。三类文件的职责结构与 flutter `conventions/index.md` 完全一致。

---

## 2. 槽位地图（SLOT 全景 → 谁消费 → 钉死什么）

iOS 平台项目约定共 **16 个槽位**（SLOT-01~SLOT-16），均在 `project-conventions.md` 内逐项填写。编号体系与 `project-conventions.template.md`（canonical 权威）**完全一致**——init 时模板复制为运行时 `.trellis/spec/conventions/project-conventions.md`，skills/gate 按本编号读取。下表是「槽位 → 决策问题 → 消费方」的全景地图，**取值正文不在此**（见 `project-conventions.md`）。

| 槽位 | 决策问题（钉死什么） | 团队栈级 canonical 钉死值 | 项目级可选范围 / 迁移方向 | 主要消费方 |
|------|---------------------|--------------------------|--------------------------|-----------|
| **SLOT-01 UI 框架基线 / ViewModel 形态** | 新界面用什么 UI 框架？SwiftUI 与 RxSwift 遗留的分界线在哪一层？`viewmodel` 是 `ObservableObject`+`@Published` 还是 `@Observable`？ | **新代码纯 SwiftUI**（RxSwift 仅存量遗留）；**`viewmodel` = `ObservableObject` + `@Published`**（硬规则） | 旧 RxSwift 模块只读维护，禁新建；`view`/`viewmodel` 一律 SwiftUI + `ObservableObject` | `view`/`viewmodel` 合同、hooks 目录拦截、implementation-review |
| **SLOT-02 DDD 四层目录分界与归属** | 七类 doc_type → owner 层 → 物理目录如何一一映射？四层根路径是什么？ | doc_type→owner→目录映射，不得跨层混放 | 子目录命名按项目；实现/接口落点固定 | hooks（PreToolUse 分层目录拦截）、implementation-review（归属判定） |
| **SLOT-03 接口与命名约定** | 协议用 `IXxx` 前缀还是 `XxxProtocol` 后缀？实现类如何命名？接口实现是否分文件？ | 协议默认 `IXxx` 前缀；接口与实现分文件（硬规则） | 遗留允许 `XxxProtocol`，新代码统一 `IXxx` | `repository`/`external` 详细 writing 与 review（接口实现分文件、命名） |
| **SLOT-04 错误类型与收口位置（enum Error 分层）** | 每个领域错误是否独立 `enum XxxError: Error`？底层异常在哪一层转换为领域 `enum Error`？ | 每域一个 `enum XxxError: Error`，定义在 `Domain/Errors/`；转换点固定在 `repository`/`external` 实现边界 | 修复/转换策略按项目；UI 只消费已归一领域错误 | `repository`/`usecase`/`external` 合同八问、implementation-review（错误收口） |
| **SLOT-05 FactoryKit DI 注册规范** | 依赖注册写在哪些 `Container+*.swift`？用 `@Injected` 还是 `@LazyInjected`？是否禁止手动 `init` 拼装？ | **强制 FactoryKit `@Injected`，禁手动 `new` 依赖**（硬规则）；注册按层拆分 | 单例作用域/工厂闭包形态按项目 | `viewmodel`/`coordinator` 合同、implementation-review（DI/导航） |
| **SLOT-06 持久化方案（WCDBSwift）** | DB 管理类路径、注入方式、建表与迁移组织？是否绝对禁止 CoreData/SwiftData？ | **WCDBSwift 唯一持久化，禁 CoreData/SwiftData**（硬规则） | DB 管理类与迁移组织按项目 | `repository`/`external` 合同、implementation-review（持久化归属） |
| **SLOT-07 导航与 Coordinator** | 页面跳转走 `AppCoordinator` 还是 View 间直接 `NavigationLink`？导航动作如何注入 ViewModel？ | **所有跨页面导航走 `coordinator`，禁 View 间直接导航**（硬规则） | 目的地枚举与闭包注入形态按项目 | `viewmodel`/`coordinator` 合同、implementation-review（DI/导航） |
| **SLOT-08 网络层** | HTTP 客户端与封装：`URLSession` 裸用还是 `Moya` 抽象？请求/响应模型放哪？ | 二选一钉死，单项目唯一（默认待定候选） | `URLSession`（轻量）/ `Moya`（重抽象）；二者皆合法，新代码只能一种 | `external` 合同、implementation-writing（待定阻塞判定）、implementation-review |
| **SLOT-09 日志** | 日志门面用什么？`SwiftyBeaver` 遗留如何收口到 `OSLog`？是否禁裸 `print`？ | 统一经 `ILogger` 门面（`SwiftyBeaver`→`OSLog` 后端迁移），禁裸 `print` | 分级与脱敏规则随项目 | code-logging skill、`view`/`viewmodel` writing、implementation-review |
| **SLOT-10 JSON 解析与修复策略** | JSON 解析用 `Codable` 还是手写？不可信 JSON 是否过修复管线？修复在哪一层？ | 不可信 JSON 必经 `IJSONRepairService` 修复后解析，归属 `external`；转换点对齐 SLOT-04 | 修复策略（容错/严格）按项目 | `repository`/`usecase`/`external` 合同八问、implementation-review |
| **SLOT-11 主题** | 主题与 design token 形态：`ThemeManager` 单例如何被 `view` 消费？是否禁止硬编码尺寸/色值？ | **`ThemeManager` 单例**消费；**`view` 禁硬编码尺寸/色值字面量**（通用硬规则） | token 命名与分组按项目；单例获取入口固定 | hooks（裸字符串/硬编码颜色检查）、`view` 合同、implementation-review |
| **SLOT-12 i18n / 本地化** | 多语言源文件位置、key 引用入口（裸 `String(localized:)` / 封装）、与共享表同步脚本名？ | 同步脚本人工受控（**agent 禁止自动执行**）；`view` 文案禁裸字符串 | 源文件路径与 key 风格按项目；脚本名因 App 而异 | `view`/`viewmodel` 合同、hooks（脚本拦截）、figma-l10n-sync |
| **SLOT-13 feature 模块结构** | 新 feature 的目录骨架（`UI/Features/<Feature>/` 下 View/ViewModel 组织）？新旧谱系分界？ | feature 自包含：`UI/Features/<Feature>/{Views,ViewModels}` | 子目录命名按项目；禁在旧目录新建 feature | hooks（目录拦截）、implementation-review、`coordinator` 装配 |
| **SLOT-14 测试约定 + mock 生成** | 单测用 `XCTest` 还是 `Quick`/`Nimble`？测试目录是否镜像源码结构？mock 用手写还是 `Mockolo`？ | **`XCTest`→`Quick`/`Nimble`**、**mock 手写→`Mockolo`**（未落地前一律 XCTest + 手写 mock）；目录镜像源码 | `XCTest`（存量）/ `Quick`+`Nimble`（新）；mock 工具与生成顺序按项目 | 合同八问之 7（测试映射）、implementation 证据节、`repository`/`external` 测试映射 |
| **SLOT-15 构建自动化（Fastlane）** | 构建/签名/发布是否用 `Fastlane`？lane 定义与触发方式？是否禁止 agent 自动执行发布？ | **构建 `Fastlane`**；任何发布/签名 lane 人工执行（**agent 禁自动触发**，默认待定候选） | lane 名与触发方式按项目 | implementation-writing（待定阻塞判定）、CI 接入评审 |
| **SLOT-16 存量违例清单** | 已知存量架构违例有哪些（供 review 存量豁免判定：触碰记债不阻塞、新增违例阻塞）？ | —（数据源，逐条登记） | 逐条：违例描述 + 文件路径；可为空但须显式声明「无」 | 所有 review 的存量豁免判定 |

> 槽位编号纪律：SLOT 编号创建后**不复用、不重排**，删除留洞。新增槽位往后追加。
> 取值「待定」上限：`project-conventions.md` 中待定槽位 ≤ 2，且每个待定项须写明决策人与期限，否则项目约定视为未就绪（硬前置不通过）。

### 2.1 槽位与硬规则的边界（不可被槽位豁免的「钉死约定」）

以下属**平台级硬规则**，是归属硬基准，**任何槽位取值不得与之冲突**（违反 = review 直接 fail）：

- **DDD 四层 + Domain 零依赖**：依赖方向 `Domain → App → Infrastructure → UI` 单向；`Domain` 层零外部依赖（可被任意层导入）。
- **FactoryKit `@Injected` DI**：禁手动 `init` 装配业务依赖；`coordinator` 负责 DI 装配。
- **Repository 模式强制**：`IXxxRepository` 接口在 `Domain`、实现在 `Infrastructure`（合并为 `repository` 一类 doc_type）。
- **`enum Error` 分层定义**：每个 domain 自有错误枚举；底层异常按 SLOT-04 在 `repository`/`external` 实现边界收口转换。
- **WCDBSwift 持久化**：禁 `CoreData` / `SwiftData`。
- **`ViewModel = ObservableObject + @Published`**：状态写 owner 唯一。
- **导航走 `coordinator`**：禁 `view` 间直接导航；禁 `view` 直接访问持久化（走 `repository`）。
- **`private` 方法在 `private extension`**：可见性组织硬约定。

槽位只在这些硬规则**未覆盖的自由度**上取值（如网络库选 `URLSession` 还是 `Moya`）。校验清单 C5 即检查取值不与上述硬规则冲突。

---

## 3. 校验清单（writing/review 硬前置使用，C1~C6）

装载本约定的任一 Skill 必须先对 `project-conventions.md` 执行以下校验，**任一不通过即终止并输出前置缺口与修复动作**：

- [ ] **C1 元信息齐全**：App 名称 / 仓库路径 / 填写日期 / 填写人 / 取值依据（实测扫描或团队决策+ADR 链接）四要素全。
- [ ] **C2 槽位完整**：SLOT-01 ~ SLOT-16 全部存在；「待定」槽位 ≤ 2 且均写明决策人与期限（默认待定候选：SLOT-08 网络层、SLOT-15 构建自动化）。
- [ ] **C3 证据可定位**：每个已填槽位至少 1 条代码证据路径（不校验路径内容，但路径须真实存在于目标仓库）。
- [ ] **C4 doc_type 纯净**：取值正文不引入 iOS 七类之外的 doc_type 名；不出现 flutter/Go 类型名（`controller`/`page-entry`/`service`/`db-dao`/`api-network`/`transport-handler` 等）。
- [ ] **C5 不与硬规则冲突**：取值不得违反 §2.1 平台硬规则（DDD 四层依赖律、Domain 零依赖、FactoryKit DI、Repository 模式、`enum Error` 分层、WCDBSwift 持久化、`ViewModel` 形态、导航走 coordinator、`view` 禁硬编码尺寸/色值）。这些不可被槽位豁免。
- [ ] **C6 存量清单存在**：SLOT-16 存量违例清单存在（可为空清单，但必须显式声明「无」）。

> 与 flutter 母版差异：flutter 是 C1~C5（15 槽位）；iOS 增列 **C4 doc_type 纯净**（因 iOS 七类与 flutter 九类不同名，需显式拦截类型名串台），故为 C1~C6（16 槽位 SLOT-01~SLOT-16）。

---

## 4. 与 `guru_gate` 兼容口径（五阶段 Gate 如何消费本目录）

本目录是五阶段工作流每个阶段硬前置的装载点之一。装载路径一律用**安装后路径**（`trellis init -t guru-ios-native` 落位 `.trellis/spec/`，PROTECTED：`trellis update` 永不覆盖）：

```
需求(prd.md)         ← 需求三件套 SSOT（五要素：行为/前置条件/状态变化/失败路径/验收场景）
概要(design §概要)   ← .trellis/spec/harness/overview/overview-structure-single-source.md
                       （归属表 + chapter_target→detail_doc_type 承接索引 + technology_decision_handoff[]）
详细(design §详细)   ← .trellis/spec/harness/detail/detail-structure-single-source.md
                       + 涉及类型的 .trellis/spec/harness/detail/detail-type-{viewmodel,usecase,repository}.md
实现(implement)      ← .trellis/spec/guides/golden-path.md
                       + .trellis/spec/harness/implementation/implementation-trace-contract.md（trace 四节）
审核(check)          ← 各 SSOT 审核基线 + 本目录 project-conventions.md 的 SLOT-16 存量豁免
```

### 4.1 各阶段从本目录消费什么

| 阶段 | guru_gate 口径（缺即拦截） | 本目录消费点 |
|------|---------------------------|-------------|
| 需求 Gate | **需求五要素**齐全：每条行为有 前置条件 / 触发 / 状态变化 / 失败路径 / 验收场景 | C1~C6 通过（项目约定就绪是任何阶段前置） |
| 概要 Gate | **归属判定表**（行为→唯一 owner 层+三问理由，无分层依赖律违例）+ **承接索引**（`chapter_target → detail_doc_type`，覆盖全部 owner）+ `technology_decision_handoff[]` 字段完整 | owner 层取 iOS 七类对应层（见 §5）；SLOT-01/02/07/13 影响归属与命名 |
| 详细 Gate | **合同八问**逐单元完整（承接 BHV / 输入输出错误 / 读写状态 / 依赖正反面 / 失败收口 / 事件后置 / 测试映射 / 不得补造）+ 追溯到概要 owner + `UNIT-<slug>` 无断链 | SLOT-03/04/05/06/07/08/09/10/14 进入对应类型合同；pending L2 类型须 `L2豁免` 或先补 L2 |
| 实现 Gate | **trace 四节**齐全（计划 / 执行 / 证据 / 阻塞与偏差）+ 静态检查与测试有命令级证据 | SLOT-09（日志）/ SLOT-14（测试框架 + mock 生成）/ SLOT-15（构建自动化）进入执行与证据节，与 `golden-path.md` §10 自检（SwiftLint + build/test）、§12 门禁映射共同定义实现合规基线；**超出槽位的硬规则（分层依赖律 / FactoryKit DI / Repository 模式）不在此取值、不可被槽位豁免**，见 `golden-path.md` §2 与 `harness/implementation/implementation-ios-standard.md` §1（LOCK-1~7） |
| 审核 | 存量豁免判定：SLOT-16 内记债不阻塞，清单外新增违例阻塞 | SLOT-16 是存量豁免唯一数据源 |

### 4.2 编号与追溯（机器追溯依据）

- **行为**：`### BHV-NNN <短名>`（prd 标题），NNN 数字，创建后不复用不重排，删除留洞。
- **设计单元**：`### UNIT-<slug>`（详细设计标题，语义 kebab-case）。
- **下游引用裸 token**：归属表、详细合同、测试映射、实现切片对行为/单元的引用一律写裸 `BHV-NNN` / `UNIT-<slug>` 编号 token。
- `guru_gate.py trace-matrix <task_dir> --write` 据此生成「行为×需求场景（REQ-UC）×归属×单元×测试×切片」矩阵；**断链（幽灵引用 / 无承接行为 / 孤儿单元）被 Gate 拦截，进不了详细/实现 Gate**。

---

## 5. doc_type 七类 → owner 层 → L2 状态（详细阶段承接基准）

详细设计承接索引的 `detail_doc_type` **只能取以下七类**（权威，禁改名/增减/换数）。owner 层归属是分层依赖律的硬基准。

| doc_type | 覆盖对象 | owner 层 | L2 状态 | flutter 对应（仅供方法学映射，**不照抄类型名**） |
|----------|---------|---------|:---:|------|
| `viewmodel` | UI 层 `ObservableObject`+`@Published` 状态容器 | UI | **v1 提供 L2** | controller |
| `usecase` | Domain 业务编排（零 UI 依赖、有状态业务流程） | Domain | **v1 提供 L2** | usecase |
| `repository` | Domain `IXxxRepository` 接口 + Infrastructure 实现（**合并一类**） | Domain（接口）/ Infrastructure（实现） | **v1 提供 L2** | repository-datasource |
| `domain-model` | Domain 实体 / 值对象 / `enum Error` / 不变量（零依赖、可被任意层导入） | Domain | pending | （无直接对应；flutter 散在 model） |
| `view` | UI 层 SwiftUI `View`（只展示+输入，无业务） | UI | pending | page-entry |
| `coordinator` | App 层 `AppCoordinator` 导航 + FactoryKit DI 装配 | App | pending | （flutter 拆 binding+routes） |
| `external` | Infrastructure 外部集成（网络 / SDK / WCDBSwift 持久化 / 第三方） | Infrastructure | pending | external-platform / api-network / db-dao |

**v1 L2 供给**：`.trellis/spec/harness/detail/detail-type-{viewmodel,usecase,repository}.md`，与 flutter 三类 L2（controller / usecase / repository-datasource）一一对应。

**pending 四类**（`domain-model` / `view` / `coordinator` / `external`）：按 L1 合同八问展开，文档头标注 `l2_status: pending`。**full 链命中 pending L2 类型时，必须在 `design-main.md` 显式声明 `L2豁免：<doc_type> 理由：…`（含按八问展开的风险与补齐计划），否则 gate 拦截**；首选先补对应 L2 再进详细设计。

### 5.1 写作顺序（自底向上，与分层依赖律一致）

```
domain-model  →  repository  →  usecase  →  viewmodel  →  view + coordinator/external（横切）
```

层级 checkpoint：Domain 层（domain-model/repository 接口/usecase）固化后核对 UNIT↔BHV 承接闭合、状态写 owner 唯一、usecase 单向无环；Infrastructure 层（repository 实现/external）核对数据依赖全有承接、SLOT-04/SLOT-10 错误转换点一致；UI 层（view/viewmodel）核对只调用稳定 Domain 行为、导航走 coordinator。

---

## 6. 装载次序速查（任何阶段开工前）

1. 读 `.trellis/spec/conventions/project-conventions.md`，跑校验清单 C1~C6——不过则停止，先完成项目约定。
2. 读 `.trellis/spec/guides/golden-path.md`（DDD 四层依赖律与禁止清单）。
3. 按本任务阶段读对应 `.trellis/spec/harness/*` SSOT，并登记进任务 `implement.jsonl` / `check.jsonl`（带 reason）。
4. 产物语言：中文优先（英文仅限代码标识符、命令、路径、框架名、协议字段、外部专有名词、原文引用）。

> 缺陷只能回上游修：审核发现结构性缺陷（归属错、合同越界、doc_type 串台）回到拥有该决策的阶段修订，禁止下游补造。
