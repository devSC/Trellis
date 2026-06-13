# iOS 详细审核取证矩阵与判级（references）

> 编排层产物：只承载取证操作、逐 doc_type 附加检查与严重度判级；规则正文以 `index.md` / L1（`detail-structure-single-source.md`）/ L2（`detail-type-{viewmodel,usecase,repository}.md`）为准。冲突时 `index.md > L1 > L2 > 本文件`。本文件不重定义合同八问、不重定义分层依赖律正文，只把它们落成可执行的取证动作与判级。
> doc_type 一律以 IOS_BRIEF 权威七类（`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`）为准；出现 `transport-handler` / `service` / `page-entry` / `controller` / `db-dao` / `api-network` / `Biz/Behavior` 等异平台或自创类型名即归属红线（详细 Gate fail）。

## 1. 取证准备（先证据后结论）

- 固化编号：`rg -n "UNIT-|BHV-" <章节文件>` 取设计单元与承接行为；`rg -n "^#{2,5} " <章节文件>` 取小节锚点；`rg -n "^#{2,5}\s+UNIT-" <章节文件>` 校验单元标题符合 `^#{2,5}\s+UNIT-[a-z0-9][a-z0-9-]*`，`rg -n "^#{2,5}\s+BHV-\d+" <prd>` 校验行为标题。
- 概要侧基线先取证（全部双向核对以此为准）：
  - `design-main.md` 第 3 节归属判定表的 owner 集合（七类 doc_type × UNIT-<slug>）；
  - 第 7 节详细设计承接索引的目标集合（`chapter_target → detail_doc_type → chapters/<slug>.md`，含 `l2_status`）；
  - 第 2.5 节 ⑤ UC 承接表（`bhv_refs` / `owner_refs` / `index_refs`）与 ⑥ 时序图策略表；
  - 第 6 节 `technology_decision_handoff[]` 技术决策清单（`selected` 状态）。
- 命中 doc_type 后装载对应 L2（只装命中类型，不全量装）：`viewmodel`→`detail-type-viewmodel.md`、`usecase`→`detail-type-usecase.md`、`repository`→`detail-type-repository.md`；pending 四类（`domain-model`/`view`/`coordinator`/`external`）不装 L2，按 L1 §3 合同八问 + L1 §3.2 类型专属要点取证，并核查 `l2_status: pending` 头标与 design-main `L2豁免：<doc_type> 理由：…` 声明。
- 机器 Gate 先行：`guru_gate.py detail <task_dir>` 与 `guru_gate.py trace-matrix <task_dir> --strict` 的结构 findings 直接并入（合同八问四标记缺失、`implement.md` trace §1 缺失、章节闭合失败、编号断链 `unit_ghost_bhv`/`bhv_no_unit`/`slice_ghost_unit`、pending L2 拦截 `_check_pending_l2`），人工不重复机检，只补语义判定。

## 2. 通用诊断矩阵（全部 doc_type 适用，对应 D1~D9）

每条 Finding 必须带「文件 + 小节/表格行/Swift 签名」锚点或明确缺失对象，并回指规则（`rule_ref=<规范文件#锚点>`）。

| 诊断 | 取证操作 | 缺口判级 | rule_ref（默认回指） |
|------|---------|---------|---------------------|
| **D1 骨架符合性** | 对照 L1 §4 模板节清单逐节打钩：① 单元职责 ② 行为定义（清单 + Swift 签名）③ 核心数据结构（含 `enum Error` 表）④ 逐行为设计（含 `mermaid sequenceDiagram`）⑤ 状态管理 ⑥ View/导航设计（仅 `view`+`coordinator`，其余标 N/A）⑦ 测试映射 ⑧ 不得补造清单。头部 `doc_type` ∈ 七类、`owner 层` 与 doc_type 一致、`l2_status` 标注正确。 | 缺节 P1；N/A 节无声明 P2；`doc_type` 越七类 P1 | `detail-structure-single-source.md#4-章节正文骨架合同` |
| **D2 八问完整性** | 逐 `UNIT-<slug>` 按 L1 §3 合同八问 + 命中 L2 类型特化逐问取证（括号内可验证信号）：① 承接行为（裸 `BHV-NNN`）② 输入/输出/错误（Swift 签名级 + `enum Error` 表）③ 读写状态（写 owner 唯一）④ 调用依赖正反两面 ⑤ 失败收口 ⑥ 事件/后置（导航请求消费方=`coordinator`）⑦ 测试映射 ⑧ 不得补造。 | 任一问缺 P1 | `detail-structure-single-source.md#3-合同八问所有-doc_type-通用骨架` |
| **D3 追溯核查** | `UNIT ↔ BHV` 双向闭合（裸 token）：UNIT 承接的 `BHV-NNN` 在 prd 存在、prd 的 BHV 至少被一个 owner 单元承接；状态写 owner 回指概要归属表行且一致；声明依赖出现在概要架构图边上，并形成 `依赖 → init/@Injected 注入 → 字段持有 → usage` 闭环。 | 幽灵 BHV `unit_ghost_bhv` / 行为无单元 `bhv_no_unit` / owner 不一致 P1 | `index.md#编号纪律`、`detail-structure-single-source.md#3-合同八问所有-doc_type-通用骨架` |
| **D4 分层一致性** | 依赖正反面声明对照 Domain→App→Infrastructure→UI 单向律（golden-path §2.1）+ 命中 L2 硬规则逐条（viewmodel §5；usecase R2/R3/R7；repository R1/R6/R7）。Domain 零依赖：`domain-model`/`usecase`/`repository` 接口只 import `Foundation` + Domain 内部类型。 | 违例 P1（阻断） | `golden-path.md#21-分层依赖律`、`detail-structure-single-source.md#61-分层依赖律归属硬基准违反直接-fail` |
| **D5 接口签名级** | `usecase`/`repository` 协议全集逐方法 Swift 签名（参数 / `async`/`throws` / `@escaping` 闭包 / `@MainActor` / 返回类型）；`domain-model` 结构体/枚举 + 不变量；可穷举概念用具名 `enum`，禁裸魔法值；非签名级（「提供 XX 能力」无签名）P1。 | 非签名级 P1；签名局部缺约束 P2 | `detail-structure-single-source.md#4-章节正文骨架合同`（§2.2/§4.x） |
| **D6 粒度判定** | 抽查 ≥1 个行为全流程（L1 §3.1）：步骤逐条有具体被调用的下层协议方法与参数、本单元内部判定、错误返回/映射点与状态写入点、`mermaid sequenceDiagram`（参与者用真实组件名）。`repository` 多写须三选一标注事务形态（`performRead`/`performWrite`/`performTransaction`）并对 transaction 写「中途失败全回滚」不变量。 | 「见概要」「处理 XX」无调用对象 P1；事务结论缺 P2 | `detail-structure-single-source.md#31-粒度标准四条写作与审核共用` |
| **D7 测试映射** | 每条承接行为 ≥1 成功用例 + 全部失败路径各 1 用例，逐行映射 `BHV-NNN`/`UNIT-<slug>`；测试层合理（见 §3 表）；mock 走 project-conventions 槽位（手写 → Mockolo）；测试框架按槽位（XCTest → Quick/Nimble）。 | 高风险链路（付费/权限/数据删除/导出/持久化迁移）漏测 P1；普通失败路径漏测 P2 | `detail-structure-single-source.md#3-合同八问所有-doc_type-通用骨架`（八问 7） |
| **D8 错误与合规** | per-domain `enum XxxError` 分层（golden-path §2.5）：`usecase` 给 case 全集逐条（语义 + 可恢复性 + 上抛/降级），底层错误（`URLError`/`AIModelDownloaderError`/`WCDBError`）在单一映射点转本域 error 再上抛；`repository` 给 `WCDBError.code` 级错误映射表；`viewmodel` 三态收口、消费 Domain 错误不新造。异常表逐行对应一条失败路径 BHV 或八问 1 行为分支。合规扫描：`rg -i "secret|api_key|api key|token|password|私钥"`、制裁 TLD/私有 API/动态执行；密钥只写环境变量名/Keychain 引用。 | 字符串比较错误/空 catch 吞错/底层裸抛/UI 新造业务 error/`AsyncStream` 失败静默 P1；secret 落盘/私有 API P1；异常表逐行失配 P2 | `golden-path.md#25-错误每域一个-enum-error团队栈级-canonical`、`detail-structure-single-source.md#3-合同八问所有-doc_type-通用骨架`（八问 5） |
| **D9 补造红线 + 层级越界** | 概要外结构、改 owner、拍板未选定槽位、超签名级实现体（>15 行实现体=越界信号）；在 `usecase`/`repository` 详细正文展开 WCDB 表结构/列定义、引擎参数（WAL/加密/连接池）、迁移版本、`@Injected`/手动 `init` 装配等本应延后到实现 trace 或归 `external`/`coordinator` 的细节。 | 补造/越界 P1 | `detail-structure-single-source.md#62-禁止补造清单`、`overview-structure-single-source.md#5-阶段边界概要不做什么` |

## 3. 逐 doc_type 附加检查

### 3.1 v1 类型（按 L2 逐条硬规则）

| doc_type | 附加取证 | 典型 P1 | rule_ref |
|----------|---------|---------|----------|
| `viewmodel` | 每个 `@Published` 字段表完整（名称/类型/初始值/写入时机/owner/承接 BHV）、写 owner 唯一；异步字段三态收口（loading→content/empty/error 去向齐全，error 文案非「待定」）；依赖只 `@Injected` 协议（`any IXxxUseCase`/`any IXxxRepository`），导航委托 `coordinator`，无直接持久化/网络；并发回写 `@MainActor`/`await MainActor.run`；私有方法置 `private extension`。 | 注入 `XxxRepositoryImpl` 实现类 / 直连 `DatabaseManager`·`WCDBSwift` / 自行 push/present / `@Published` 持有业务状态本体（应只镜像 usecase 流投影） | `detail-type-viewmodel.md#类型硬规则`（§5） |
| `usecase` | 业务状态写 owner 全局唯一；usecase 间单向无环、构造注入接口（`any IXxxRepository`/单向 `any IXxxUseCase`）；`enum XxxError` case 全集 + 上抛/降级标注、底层错误单点 `map`；流生命周期闭合（`AsyncStream` `onTermination` 清理订阅者，多订阅者广播语义）；可变共享状态 `actor` 封装；零 UI 依赖（无 `import SwiftUI`、无 `@Published`）。 | usecase `import SwiftUI`/`FactoryKit`/`WCDBSwift` / 注入具体实现类 / 在自身 `@Injected`（DI 装配属 coordinator）/ usecase 环依赖 / 底层错误裸抛 / 双写业务状态 / 裸 `var` 跨 `Task` 共享 | `detail-type-usecase.md#类型硬规则golden-path-锁定违反直接-fail`（R1~R8） |
| `repository` | 接口 `IXxxRepository` 在 `Domain/Repositories/` 零依赖（只 import `Foundation`）、实现 `XxxRepository` 在 `Infrastructure/Persistence/Repositories/`、接口实现分文件；`WCDBError`/`URLError` 在实现边界单点转 `PersistenceError` 或本域 error；返回域模型不泄漏 WCDB Object/DTO；缓存回落/落库决策只在实现侧；事务形态三分法（read/write/transaction）。 | 接口出现 `import WCDBSwift`/`FactoryKit`/`SwiftUI` / 返回 `WCDBSwift.Table<...>` / 反向注入 `usecase`·`viewmodel` / 注入其他 `repository`（跨聚合回概要重判）/ 接口实现混一文件 | `detail-type-repository.md#类型硬规则`（R1/R6/R7） |

### 3.2 pending 类型（L1 八问 + L1 §3.2 专属要点 + 豁免核查）

通用先核：头部 `l2_status: pending` 标注存在；design-main 有对应 `L2豁免：<doc_type> 理由：…`（full 链；无豁免 → `_check_pending_l2` 拦截 P1）。

- **`domain-model`**：八问退化——只强约束 2（类型/`enum`/`enum Error` 签名）、5（不变量违反的错误语义）、8（零依赖断言）；八问 1/3/4/6/7 中行为类项写 `N/A：值类型无运行时行为`，但不变量校验若存在则按行为展开并配测试。验证信号：该单元 `grep import` 只出现 `Foundation`，无 `SwiftUI`/`WCDBSwift`/`FactoryKit`。出现 IO/编排/持久化注解外泄 → 破坏「零依赖、可被任意层导入」P1。
- **`view`**：强约束 2（输入事件 → 回调签名）、4（只依赖 `viewmodel`，反面禁业务/导航/持久化）、6（事件回调与导航请求消费方=`coordinator`）、8（不拥有状态转移/业务/导航决策）；状态读为只读（绑定 `@Published`）；文案走本地化 key（`R.string.localizable` 等）、主题走 `ThemeManager`，不硬编码用户可见字符串。持有业务规则 / 发起导航 / 访问持久化 → P1。
- **`coordinator`**：强约束 4（装配哪些 `view`/`viewmodel`/`usecase`，FactoryKit `Container` 注册项逐条）、6（导航后置结果与栈变化）、8（不拥有业务规则）；八问 2 用导航路由表（route → 目标 + 参数 + 装配依赖）表达；导航态唯一写 owner=coordinator（`viewmodel`/`view` 直接改写导航态 → P1）。
- **`external`**：强约束 2（网络 req/resp model 或 SDK/引擎调用合同签名）、5（技术错误归一为 Domain `enum Error` 的转换边界）、8（不拥有业务规则/业务终态判定）；WCDB 引擎参数/表定义/迁移版本在此承载（不在 usecase/repository 正文展开）；凭证只引用环境变量名/Keychain，禁真实 key；涉交付面（PrivacyInfo/entitlements/StoreKit）合规依据逐条落点。承接业务语义/prompt 业务组装（应在 usecase）→ P1。

## 4. 跨层调用链核对（`directory_final` 第②段 / `layer_checkpoint`）

| 层边界 | 核对项 | 缺口判级 | rule_ref |
|--------|--------|---------|----------|
| `view → viewmodel` | view 只绑定 `@ObservedObject`/`@StateObject`/`@InjectedObject` 的 viewmodel、转发输入到 viewmodel 方法；导航请求经注入闭包/coordinator | view 直连 usecase/repository/持久化、view 间硬 `NavigationLink` 跨 feature 跳转 P1 | `golden-path.md#21-分层依赖律` |
| `viewmodel → usecase` | viewmodel 只注入 `any IXxxUseCase`/`any IXxxRepository` 协议；`@Published` 状态有对应 usecase 流/方法发射方；三态去向齐全 | viewmodel 注入实现类/直连 `DatabaseManager`/`WCDBSwift`、状态无发射方（幽灵订阅） P1 | `detail-type-viewmodel.md#类型硬规则` |
| `usecase → repository(接口)` | usecase 声明的数据依赖有承接 `IXxxRepository` 接口章节；错误转换位置（`[SLOT-error-mapping]`）在 repository 实现边界，两侧一致 | usecase 声明依赖无承接接口、错误转换位置两侧失配 P1 | `detail-type-repository.md#类型硬规则` |
| `repository(实现) → external` | 网络/SDK/WCDBSwift 合同被 repository 实现闭合；`external` 凭证只引用环境变量名；技术错误归一为 Domain `enum Error` | external 合同无 repository 消费方（孤儿合同）P2；凭证落真实 key P1 | `golden-path.md#8-external-迷你路径` |
| 全局 | 业务状态写 owner 全局唯一（同一业务状态出现在两个 usecase 合同=双写 P1）；同一 `enum XxxError` 跨章定义一致；导航全部经 `coordinator`；FactoryKit `Container` 注册项与各单元依赖闭合 | 多写 owner / 导航绕过 coordinator / DI 手动 `init` 替代 Factory P1 | `golden-path.md#23-di-唯一策略factorykit-injected` |

## 5. 覆盖率核对（`directory_final` 第③段）

1. **索引↔章节双向闭合**：概要第 7 节承接索引目标集合 vs 现存 `chapters/<slug>.md`：缺失目标文档只出「缺失结论 + 修订方案」（不进 D 诊断）；孤儿章节（有文件无索引条目）P1。归属表全部 owner 被索引覆盖（双向闭合）。
2. **UC 承接链路可走通**：第 2.5 节 ⑤ UC 承接表的 `index_refs` vs 章节：每个 UC 的 `view → viewmodel → usecase → repository(接口) → external` 链路在详细侧可走通、无断点。
3. **时序覆盖率**：第 2.5 节 ⑥ 时序图策略表与详细正文逐行为 `sequenceDiagram` 对照——抽查 ≥1 个非豁免 UC 的时序步骤（参与者/调用）在对应章节有同名行为；`sequenceDiagram` 不得出现 View 直连 Repository 实现/WCDBSwift 链路。

## 6. 薄文档判定（优先于逐条 Finding）

满足任一即判薄文档 → 结论直接「不可进入」+ 文档级重构（L1 §9），不再逐条列局部 Finding：

- ≥2 章骨架雷同且无单元级实质内容：`@Published` 字段表空 / 协议方法无签名 / 流程详述 <3 步 / 缺 `mermaid sequenceDiagram` 与异常表 / 测试映射 ≤1 行。
- 全目录一次性生成（违反 L1 §5.3「每批 1~3 章、禁一轮全量」），无批内审修痕迹（`chapter_status` 缺失），叠加上一条任意命中。
- 逐行为设计普遍缺 `mermaid sequenceDiagram` 与异常表，行为退化为大纲级标题。

薄文档命中时输出薄文档证据（雷同章节对照 + 占位统计：空字段表数 / 无签名方法数 / `sequenceDiagram` 缺失章数 / 测试映射 ≤1 行的章数），不逐条列局部 Finding。

## 7. 严重度判级规则

- **P1（阻断）**：D1~D9 表中标注 P1 的项；跨层 P1 项；薄文档；章节闭合失败（机检并入）；分层依赖律违例；编号断链（`unit_ghost_bhv`/`bhv_no_unit`/`slice_ghost_unit`）；八问缺项；`doc_type` 越七类；secret value 落盘；未选定决策被下游引用；pending L2 缺 `L2豁免`（`_check_pending_l2`）。
- **P2（应修）**：表中 P2 项；粒度局部不达标（单个行为）；`enum XxxError` 枚举不全；测试漏普通失败路径；事务形态结论缺；孤儿合同；异常表逐行失配。
- **P3（建议）**：表述/格式/术语一致性、命名规范建议（不做「有没有写某个词」的纯形式检查）。
- 判级冲突取高；同根因合并为一条 Finding 列全部位置。

## 8. 结论判定（互斥三选一）

- 任一 P1 → **不可进入**（阻塞 P1 清单 + 修订形态建议；概要缺陷标注「回退概要」）。
- 仅 P2 且每条有明确修订路径与验证时点 → **带明确假设可进入**（逐条假设 / 依据 / 验证时点）。
- 无 P1/P2 → **可进入实现编码**。
- 结论后必须给 Gate 收口指引（用户终端 `guru_gate.py confirm detail <task_dir>`，通道见 SKILL.md「Gate 收口」节）。修订形态判定只引用 L1 §9（局部修订 / 文档级重构）。

## 9. 最小成稿样例（`usecase` doc_type，锚定 story-verse-mac 真实单元）

> 证据基准：`story-verse-mac` 的 `App/UseCases/ManageAIModels/`（`IManageAIModelsUseCase.swift` / `ManageAIModelsUseCase.swift` / `ManageAIModelsError.swift`）+ 测试 `StoryVerseTests/UseCases/ManageAIModels/ManageAIModelsUseCaseTests.swift` + DI `App/DependencyInjection/Container+UseCases.swift` 的 `manageAIModelsUseCase` 工厂 + 接口 `Infrastructure/Persistence/Repositories/AIModelRepository.swift` 的 `protocol IAIModelRepository`。本样例演示 `usecase` 章节如何落地合同八问与逐行为设计（取真实签名与真实 `enum Error` case，按详细设计「签名级、零实现体」口径裁剪），并演示审核侧如何据此取证。**这是表达形态示例，不是要审核者照抄；审核仍以本文件 §2~§8 矩阵为准。**

### 9.1 章节头（D1 取证点）

```markdown
# 5-usecase-manage-ai-models-design 详细设计

> doc_type：usecase ｜ l2_status：v1
> owner 层：Domain
> 承接索引：design-main.md 第 7 节 5-usecase-manage-ai-models-design ｜ 返回：[design-main](../design-main.md)
```

审核：`doc_type ∈ 七类`✅、`owner 层=Domain` 与 doc_type 一致✅、`l2_status=v1`（命中 `detail-type-usecase.md`，不需 `L2豁免`）✅。

### 9.2 单元职责 + 行为定义（D1/D2-①②/D5 取证点）

```markdown
## 1. 单元职责
UNIT-manage-ai-models-usecase：AI 模型下载/更新/删除/取消与全局状态广播的业务编排 owner（Domain，零 UI 依赖）。
- 调用：`any IAIModelRepository`（取/存模型）、`IAIModelDownloaderService`（下载/观察/取消）、`IApplicationInfoService`（取当前 App 版本）、`IFileSystem`（删本地文件）——全部协议、构造注入。
- 被调用：`viewmodel` 经 `@Injected(\.manageAIModelsUseCase)` 消费（DI 装配在 coordinator 的 Container 扩展）。
- 依赖方向：仅依赖 Domain 接口（符合 golden-path §2.1 单向律，零反向）。

## 2. 行为定义
### 2.1 行为清单
- getSpecificModelStatus — 取单模型状态 — 承接 BHV-031
- downloadAIModel — 下载模型（进度回调）— 承接 BHV-032
- observeModelDownloadStatus — 全局状态流广播 — 承接 BHV-040
### 2.2 接口定义（Swift 签名级）
``swift
protocol IManageAIModelsUseCase {
    func getSpecificModelStatus(modelId: String) async throws -> AIModelStatus
    func downloadAIModel(modelId: String, progressHandler: @escaping (Double) -> Void) async throws
    func observeModelDownloadStatus() -> AsyncStream<[AIModelDownloadStatus]>
}
``
```

审核：八问①承接 `BHV-031/032/040` 裸 token（D3 回 prd 核对存在）；八问②签名级（`async throws`、`@escaping (Double) -> Void`、`AsyncStream<...>` 返回类型齐全，D5 通过）；八问④依赖正反两面齐全且全为协议（D4 对照 usecase R2/R3——无 `SwiftUI`/`WCDBSwift`/`FactoryKit`、无具体实现类，通过）。

### 9.3 核心数据结构——错误类型表（D2-②⑤/D8 取证点）

```markdown
## 3. 核心数据结构
### 3.2 错误类型表（enum ManageAIModelsError，分层定义）
| 枚举 case | 语义 | 可恢复性 | 上抛/降级 | 转换/收口位置 |
|-----------|------|---------|-----------|--------------|
| modelNotFound(id:) | 仓库无此模型 | 不可恢复 | 上抛 viewmodel 提示 | usecase 内 guard |
| appVersionTooLow(modelId:requiredVersion:currentVersion:) | App 版本过低 | 需升级 App | 上抛提示 | usecase 内版本比较 |
| diskSpaceInsufficient(requiredBytes:availableBytes:) | 磁盘不足 | 清理后重试 | 上抛提示 | 下层错误映射点 |
| operationCancelled(modelId:) | 被取消 | 可重发 | 降级为流 .cancelled | 下层错误映射点 |
| downloadFailed(modelId:underlyingError:) | 下载失败兜底 | 可重试 | 上抛提示 | 下层错误映射点 |
```

审核：D8——`ManageAIModelsError` 是本域 `enum Error: Equatable`（golden-path §2.5）；底层 `AIModelDownloaderError` 在单一映射点 `mapDownloaderErrorToUseCaseError(error:modelId:)` 转成本域 case 后再上抛（无裸抛、无字符串比较错误，通过 usecase R4）。异常表逐行对应一条失败路径（D8 逐行可对应通过）。

### 9.4 逐行为设计（D2-④⑤⑥/D6 取证点，示 `downloadAIModel`）

```markdown
## 4. 逐行为设计
### 4.2 downloadAIModel(modelId:progressHandler:)
- 行为简述：下载指定模型并回调进度（承接 BHV-032）。
- 依赖调用表（八问 4）：
  | 依赖 | 注入方式 | 调用的行为 | 不调用边界 |
  |------|---------|-----------|-----------|
  | IAIModelRepository | 构造注入(协议) | findModel(byId:) / saveModel(_:) | 不直接碰 WCDBSwift |
  | IAIModelDownloaderService | 构造注入(协议) | downloadModel(from:modelId:specificFiles:) / observeDownloadState(taskId:) | 不解析下载产物业务语义 |
  | IApplicationInfoService | 构造注入(协议) | getCurrentAppVersion() | — |
- 执行流程（mermaid sequenceDiagram，参与者用真实组件名）：
  participant VM as ViewModel
  participant UC as ManageAIModelsUseCase
  participant Repo as IAIModelRepository
  participant DL as IAIModelDownloaderService
  VM->>UC: downloadAIModel(modelId, progressHandler)
  UC->>Repo: findModel(byId:) —— nil → throw modelNotFound
  UC->>UC: 版本校验 → appVersionTooLow / 状态分支(.downloading/.downloaded 去重)
  UC->>Repo: saveModel(.downloading(0.0)) 并 broadcast
  UC->>DL: downloadModel(...) → 失败 map 为本域 error 上抛
  DL-->>UC: observeDownloadState 流 → 进度/完成/失败/取消 → saveModelAndBroadcast
- 异常处理表：
  | 异常 | 处置 | 错误转换位置 [SLOT-error-mapping] |
  | 模型不存在 | 上抛 modelNotFound | usecase guard |
  | 下载启动失败 | map 后上抛 downloadFailed/networkError/diskSpaceInsufficient | mapDownloaderErrorToUseCaseError |
  | 流观察失败 | handleDownloadError 置 .error 态、清理操作 | 流 catch 分支 |
```

审核：D6 粒度——每步有具体被调用的下层协议方法与参数（`findModel(byId:)`/`downloadModel(from:modelId:specificFiles:)`/`observeDownloadState(taskId:)`）、本单元内部判定（版本校验、状态去重分支）、错误映射点与状态写入点（`saveModelAndBroadcast`），`sequenceDiagram` 参与者为真实组件名（通过）。D2-⑤失败收口逐路径有处置；D2-⑥后置经 `broadcastProgressUpdate()` 向订阅者 `yield`。

### 9.5 状态管理 + 流生命周期（D2-③/usecase R5/R6/R7 取证点）

```markdown
## 5. 状态管理
- 业务状态：各模型下载/更新状态（写 owner 唯一 = 本 usecase，viewmodel 只镜像流投影）。
- 可变共享状态：activeOperations / subscriberMap / 缓存 / 取消跟踪 由 private actor StateManager 封装（线程安全）。
- 流生命周期：observeModelDownloadStatus() 用 AsyncStream，addSubscriber 注册、onTermination → removeProgressSubscriber 清理；多订阅者由 broadcastProgressUpdate 广播。
```

审核：R7 状态唯一写 owner（本 usecase，非双写，通过）；R5 可变共享状态用 `actor`（通过）；R6 流生命周期闭合——`onTermination` 有清理、广播语义已声明（通过）。若此处把 `activeOperations` 写成裸 `var` 跨 `Task` 共享 → R5 违例 P1；若失败用静默吞而非建模为 `case failed(message:)` → D8 P1。

### 9.6 测试映射（D2-⑦/D7 取证点）

```markdown
## 7. 测试映射
| BHV/行为 | 测试层 | 测试点（成功+失败逐条） | mock 对象 |
|----------|--------|------------------------|-----------|
| BHV-031 getSpecificModelStatus | unit(XCTest) | 成功 testGetSpecificModelStatus；失败 testGetSpecificModelStatus_ModelNotFound | 真实 AIModelRepository + 临时库 |
| BHV-032 downloadAIModel | unit+integration | testDownloadAIModel_NotDownloaded / _AlreadyDownloaded / _ModelNotFound / _AppVersionTooLow | MockAIModelDownloaderService / MockApplicationInfoService |
| BHV-040 observeModelDownloadStatus | unit(流) | testObserveModelDownloadStatus_InitialState / _DownloadProgress / _MultipleSubscribers（for await 断言时序） | Mock 下载服务 |
```

审核：D7——每条行为 ≥1 成功 + 全部失败路径各 1 用例（`downloadAIModel` 的 ModelNotFound/AppVersionTooLow 失败路径均有用例），测试层合理（usecase 是测试密度最高层：每条行为 1 成功 + 全部失败、`enum Error` case 有断言、流时序用 `for await`），mock 走槽位（手写 Mock + 真实库做集成，符合 project-conventions mock 槽位）。模型下载属持久化/下载链路——若漏关键失败路径测试则 D7 P1；普通失败漏测 P2。

### 9.7 不得补造清单（D2-⑧/D9 取证点）

```markdown
## 8. 不得补造清单
- 不决定 WCDBSwift 表结构/列定义/迁移版本——属 external/repository 实现（不在本 usecase 正文展开）。
- 不决定下载并发上限/重试退避具体取值——属 external 适配器与 project-conventions 槽位。
- 不持有 @Published / 不 import SwiftUI——UI 状态属 viewmodel。
- 不在本 usecase @Injected 装配依赖——DI 装配属 coordinator 的 Container 扩展。
```

审核：D9——八问⑧逐条含越层禁止项；若正文出现 WCDB 表结构/引擎参数/`@Injected` 装配 → 设计层级越界 P1；若新增概要归属表之外的结构 → 补造 P1（回退概要）。
