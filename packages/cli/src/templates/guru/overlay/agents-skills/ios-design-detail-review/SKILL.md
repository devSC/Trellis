---
name: ios-design-detail-review
description: 用于审核 Guru iOS 原生平台（SwiftUI 主 + RxSwift 遗留、DDD 四层 Domain→App→Infrastructure→UI、FactoryKit @Injected DI、Repository 模式、WCDBSwift 持久化、AppCoordinator 导航）详细设计文档，判定能否进入实现编码。先做 EX 前置检查（判轨 / 项目约定 C1~C6 / 承接索引 / 概要 review evidence / 承接源 / 机器 Gate），再按 review_scope 三模式执行：current_chapter 单章逐行为诊断、layer_checkpoint 跨章协同诊断、directory_final 目录级三段式终审（逐文档 D1~D9 诊断 → 跨层调用链 → 概要承接索引与时序覆盖率）。核查合同八问、概要 owner 追溯、Domain→App→Infrastructure→UI 单向依赖律、per-domain enum Error 收口、@Published 三态收口、WCDBSwift 事务边界、测试映射、合规红线与可编码粒度；编号断链拦截（单元引用幽灵 BHV / 行为无单元承接 / 切片引用幽灵 UNIT）；先证据后结论，输出分级 findings 与互斥三选一结论，输出 record-review 证据，并在双 clean 后等待 detail confirm。doc_type 一律以 IOS_BRIEF 钉死七类（viewmodel / usecase / repository / domain-model / view / coordinator / external）为权威，禁照抄 flutter（controller/page-entry/db-dao/api-network）或 Go（transport/service）类型名。规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT 与 `.trellis/spec/harness/index.md`，本文件只组织取证、Finding 与输出。
---

# iOS 原生平台详细设计审核

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载合同八问规则正文与详细 Gate 完成条件；L2（`detail-type-{viewmodel,usecase,repository}.md`，v1 三类）承载类型差异与 iOS 硬规则；`.trellis/spec/harness/index.md` 承载 doc_type 权威七类、编号纪律与 Gate 口径。本 SKILL.md 只做前置检查、scope 编排与诊断流程，不重定义规范正文。`references/review-baseline.md` 承载逐 doc_type 取证矩阵与判级，`references/review-output.md` 承载输出字段合同。冲突时 `index.md > L1 > L2 > references > 本文件`。
> 横向硬依赖：通用方法 `.trellis/spec/guides/golden-path.md`（分层依赖律、FactoryKit DI、Repository 模式、enum Error 分层、WCDBSwift 持久化、禁止清单）+ 目标仓库 `.trellis/spec/conventions/project-conventions.md`（C1~C6 校验 + 项目约定槽位）。
> doc_type 七类一律以 IOS_BRIEF 为权威；出现 `transport-handler / service / page-entry / db-dao / api-network / manager / handler` 等异平台或自创类型名即归属红线（详细 Gate 直接 fail）。

## 目标

- 审核详细设计是否达到「可进入实现编码」的质量口径：合同八问落地、概要承接源已选定、Domain→App→Infrastructure→UI 单向依赖闭合、可编码粒度成立、测试映射齐全，与 L1 详细 Gate（`guru_gate.py detail`）同口径但补充人工语义判定。
- 逐文档诊断 + 跨章调用链核对的双层取证：单章合格不等于目录合格；单章无 Findings 只代表本范围 `findings=none`，不代表全目录无 gap。
- 拦截编号断链（幽灵 BHV / 行为无单元承接 / 幽灵 UNIT），拦截越层依赖（viewmodel 注入 repository 实现 / 直连 DatabaseManager·网络、usecase 反向 import SwiftUI·WCDBSwift·具体实现类、repository 反向注入 usecase、view 自行发起导航或访问持久化、状态双写），拦截设计层级越界（在详细正文展开本应延后到实现 trace 的 WCDB 表结构 / 引擎参数 / 实现体）。
- 识别「薄文档」：多章雷同骨架、无单元级实质内容（一轮全量生成迹象）→ 文档级重构，不接受局部补丁。
- 本 Skill 只组织取证、Finding 与输出，不重定义 L1/L2/index 规范正文，也不代写合同正文。

## iOS 平台模型基线（取证锚点，规则正文仍以 index/L1/L2 为准）

- **分层与写作顺序**：依赖方向严格单向 `Domain → App → Infrastructure → UI`，无环、无反向；**Domain 零依赖**（只 import `Foundation` + Domain 内部类型）。写作自底向上：① `domain-model` → ② `repository` → ③ `usecase` → ④ `viewmodel` → ⑤ `view` + `coordinator`/`external` 横切。审核取证时按依赖方向核对调用链闭合，不要求被审范围已覆盖全部上层。
- **doc_type 权威七类（详细承接索引 `chapter_target → ios doc_type` 取值，全集见 index §3，全程唯一禁改名/增减/换数）**：

  | # | doc_type | owner 层 | 一句话职责 | L2 状态 |
  |---|----------|----------|-----------|---------|
  | 1 | `viewmodel` | UI | `ObservableObject + @Published` 状态容器：状态字段、事件→状态转移、流订阅、生命周期、三态 | **v1 提供** |
  | 2 | `usecase` | Domain | 有状态业务编排（零 UI 依赖）：业务规则、状态转移、响应式发射、状态唯一写 owner | **v1 提供** |
  | 3 | `repository` | 接口=Domain / 实现=Infrastructure | `IXxxRepository` 接口 + 实现（**合并一类**）：数据访问合同、local/remote 编排、缓存回落、错误映射、mapper | **v1 提供** |
  | 4 | `domain-model` | Domain | 实体 / 值对象 / `enum XxxError` / 不变量（**零依赖、可被任意层导入**） | pending |
  | 5 | `view` | UI | SwiftUI `View`（只展示 + 输入，无业务、无导航发起、无持久化访问） | pending |
  | 6 | `coordinator` | App | `AppCoordinator` 导航 + FactoryKit DI 装配（`@Injected` Container 注册） | pending |
  | 7 | `external` | Infrastructure | 外部集成：网络（URLSession/Moya）/ SDK / WCDBSwift 持久化引擎 / 第三方 | pending |

  前 3 类有 v1 L2，按类型正向写法 + 类型硬规则审核（`detail-type-{viewmodel,usecase,repository}.md`）；后 4 类（`domain-model`/`view`/`coordinator`/`external`）为 pending（无独立 L2），按 L1 合同八问展开，头部须标注 `l2_status: pending`，且 full 链须在 design-main.md 给出 `L2豁免：<doc_type> 理由：…` 声明（无豁免 → `_check_pending_l2` 拦截，P1）。
- **owner 层四值（DDD 四层）**：`UI`（`view`/`viewmodel`）/ `App`（`coordinator`）/ `Domain`（`usecase` / `repository` 接口 / `domain-model`）/ `Infrastructure`（`repository` 实现 / `external`）。某业务状态的唯一写 owner 落在 `usecase`；页面状态唯一写 owner 落在 `viewmodel`；导航态归 `coordinator`；数据访问实现落在 `repository` 实现侧；实体/值对象/`enum Error` 落在 `domain-model`。owner 跨层即归错层 → 回退概要重判归属。
- **编号纪律**（机器追溯依据，详见 index §4.1）：行为 `### BHV-NNN <短名>`（prd 标题，正则 `^#{2,5}\s+BHV-\d+`，按「用户操作 / 系统反应 / 失败路径 / 生命周期」枚举，创建后不复用、不重排、删除留洞）；设计单元 `### UNIT-<slug>`（详细标题，正则 `^#{2,5}\s+UNIT-[a-z0-9][a-z0-9-]*`，slug 建议带 doc_type 后缀自证归属：`UNIT-home-viewmodel` / `UNIT-story-usecase` / `UNIT-story-repository` / `UNIT-story-model` / `UNIT-home-view` / `UNIT-app-coordinator` / `UNIT-database-external`）；下游引用（归属表、单元、测试映射、实现切片）一律写裸 token，`guru_gate.py trace-matrix` 据此生成 行为×需求场景（REQ-UC）×归属×单元×测试×切片 矩阵，断链被 Gate 拦截。
- **统一红线（贯穿，违反直接 fail）**：FactoryKit `@Injected` DI（禁手动 `init` 装配实现）；Repository 模式强制（UI/Domain 只触达接口）；per-domain `enum XxxError` 分层定义 + 底层异常单点映射（禁字符串比较错误、禁空 `catch {}` 吞错）；WCDBSwift 持久化（**禁 CoreData / SwiftData / `@Model` / `NSManagedObject`**）；ViewModel = `ObservableObject + @Published`（私有方法落 `private extension`）；并发 UI 写回主线程（`@MainActor` / `await MainActor.run`）；密钥只写环境变量名引用、禁落真实 key。任一红线违例 → P1（阻断），详细设计文档不可豁免。

## 最小输入与自动补全

- 输入参数：
  - `review_scope`：`current_chapter`（指定 `chapter_target`/`chapter_batch` 的文档级逐行为诊断）/ `layer_checkpoint`（按层跨章协同诊断，配 `checkpoint_layer` ∈ {`domain-model`, `repository`, `usecase`, `viewmodel`, `横切`}，横切含 `view`/`coordinator`/`external`）/ `directory_final`（默认，目录级三段式终审）。
  - `chapter_target` / `chapter_batch`：`current_chapter` 模式必填；若用户自然语言显式指定一个 `chapters/<slug>.md` 文件，执行期先反查其在概要承接索引中的 `chapter_target → ios doc_type`，再据此装载对应 L2（v1 三类才装 L2；pending 四类按 L1 八问取证 + 豁免核查，不装 L2）。
  - `chapter_subscope` / `behavior_subset`（可选）：在已定 target/batch 内收窄本轮审核项（如 viewmodel 的命令方法子集、repository 的实体子集、usecase 的业务流子集）；不改变承接索引目标集合或类型判定。
- 接受 task 目录或 `design_package` 路径（full 链）/ 任务内 `design.md`（light 链）；候选不唯一时先确认审核目标。
- 其它扩展输入只归档，不参与目标范围、类型、owner 或承接源判定。

## 装载顺序与 EX 前置检查（任一失败 → 前置缺口输出，停止逐文档诊断）

1. 读 L1 主 SSOT：`.trellis/spec/harness/detail/detail-structure-single-source.md`；读五阶段入口 `.trellis/spec/harness/index.md`（doc_type 七类 / 编号纪律 / Gate 口径）；再读 `references/review-baseline.md` 与 `references/review-output.md`。
2. 读 `.trellis/spec/guides/golden-path.md`（iOS 分层依赖律、FactoryKit DI、Repository 模式、enum Error 分层、WCDBSwift 持久化、禁止清单）与 `.trellis/spec/conventions/project-conventions.md`（执行 C1~C6 校验 + 槽位齐备：UI 框架 / 网络层 / 日志 / JSON 修复策略 / 测试框架 / i18n / 主题 / feature 模块结构 / mock 生成 / 构建自动化）。
3. **EX-1 输入键**：task.json `guru_chain`（full 链含 `design_package` 字段，相对 repo root）可判定；判轨结果决定 full（目录级设计包）/ light（任务内单文件 `design.md`）口径。
4. **EX-2 路径与骨架**：full 链 `design_package/chapters/` 目录存在且路径边界合法；light 链 `design.md` §详细节存在。
5. **EX-3 承接索引**：concept `design-main.md` 第 7 节详细设计承接索引（light 链 `design.md` 索引节）存在、非空，可建立 `chapter_target → ios doc_type → 目标文件` 完整映射，且 doc_type 取值落在 IOS_BRIEF 七类全集内（出现异平台/自创类型名 → 归属红线，回退概要重判）；归属表全部 owner 被索引覆盖（双向闭合）。
6. **EX-4 概要 review evidence**：`python3 .trellis/scripts/guru/guru_gate.py status` 显示 overview 当前 digest 已有两个不同 run-id 的 clean review；缺 evidence → 回退概要 review/fix loop。
7. **EX-5 承接源 + 项目约定**：被审章节引用的技术决策（UI 框架取向、网络层、日志、测试框架、mock 生成、主题、持久化等映射到 project-conventions 槽位）均已「选定」（待定槽位写明决策人/期限）；命中 pending L2 的 doc_type（`domain-model`/`view`/`coordinator`/`external`）均有 `L2豁免：<doc_type> 理由：…` 声明（full 链；缺即 P1）；项目约定 C1~C6 全部通过。
8. **EX-6 机器 Gate**：`python3 .trellis/scripts/guru/guru_gate.py detail <task_dir>` 与 `guru_gate.py trace-matrix <task_dir> --strict` 的结构结论可获取（机检失败项——合同八问四标记缺失[承接行为/失败收口/测试映射/不得补造]、`implement.md` trace §1 缺失、章节闭合失败、编号断链 `unit_ghost_bhv`/`bhv_no_unit`/`slice_ghost_unit`、pending L2 拦截 `_check_pending_l2`——直接并入 findings，人工聚焦语义判定，不重复机检）。
9. 按被审文档命中的 doc_type 读对应 L2；只装载命中类型（`viewmodel`/`usecase`/`repository`），不全量装；pending doc_type 不装 L2（不存在），按 L1 八问取证 + 豁免核查。

## 执行规则

1. L3 不重定义 index/L1/L2 规则正文；每项检查回指 L1 章节号或 L2 硬规则条目（`rule_ref=<规范文件路径#锚点>`，如 `rule_ref=detail-type-viewmodel.md#5`、`rule_ref=detail-type-usecase.md#R4`、`rule_ref=detail-type-repository.md#类型硬规则`）。
2. 先证据后结论；每条 Finding 带「文件 + 小节/表格行/Swift 签名」锚点或明确缺失对象，再给最小修订方案；修订形态判定只引用 L1 修订形态章。
3. **directory_final 不得跳过逐文档阶段**：每个现存目标文档必须有独立的 D1~D9 诊断与 Finding 摘要；不得先输出整体通过/风险结论再补零散文档证据。缺失目标文档只输出缺失结论 + 修订方案，不进入 D 诊断。
4. `current_chapter` 不得扩大为全目录主审，但必须读取关联锚点核对上游（概要承接索引/归属表）与下游（被引用的 usecase/repository/domain-model 接口与 `enum Error`）边界；目录级完整复审标记为 `directory_final_required`。
5. 「范围内/范围外」仅由概要承接索引的目标集合判定；批次/单章无 Findings 只代表本范围 `findings=none`，不代表目录通过；partial scope 无 Findings 只代表 `covered_items[]` 无 Findings，须回填 `not_covered_items[]` 与 `canonical_publish_status=not_applicable_by_partial_scope`。
6. EX 失败（尤其 EX-3/EX-4/EX-5/EX-6 断链或承接源未选定）一律回退上游（概要/判轨/项目约定/需求），不得在详细侧补造后继续审；不得在详细阶段首次补造 UI 框架取向、网络层、持久化介质、mock 方案等本属概要/项目约定的决策。
7. **分层依赖律违例（Domain→App→Infrastructure→UI 单向，违反 = P1 阻断，不得给通过性结论）**：
   - `viewmodel` 注入 Repository **实现类**（`XxxRepositoryImpl`）/ 直连 `DatabaseManager`·WCDBSwift / 直连 `URLSession`·Moya·SDK 具体类型 / 注入其他 `viewmodel` / 自行 push/present 导航（应委托 `coordinator`）。
   - `usecase` `import SwiftUI`/`FactoryKit`/`WCDBSwift` / 注入具体实现类（非 `any IXxxRepository` 协议）/ 引用 `ViewModel`·`View`·`AppCoordinator` / 在自身 `@Injected`（DI 装配属 `coordinator`，usecase 只 `init` 构造注入协议）/ usecase 间环依赖或双向依赖。
   - `repository` 反向注入 `usecase`/`viewmodel`/`view`/`coordinator` / 注入其他 `repository`（跨聚合回概要重判）；Domain 侧协议 `IXxxRepository` 出现 `import WCDBSwift`/`FactoryKit`/`UIKit`/`SwiftUI`（破坏 Domain 零依赖）；返回 WCDB Object/DTO 泄漏行模型给上层。
   - `domain-model` 引入任何外部依赖（破坏「零依赖、可被任意层导入」）。
   - `view` 持有业务规则 / 发起导航 / 访问持久化或网络。
8. **编号断链（= P1）**：单元引用 prd 不存在的 `BHV-NNN`（幽灵行为 `unit_ghost_bhv`）、行为无任何 `UNIT-<slug>` 承接（`bhv_no_unit`）、实现切片引用不存在的 `UNIT-<slug>`（幽灵单元 `slice_ghost_unit`）。八问缺项、概要 owner 不一致或承接不闭合、章节闭合失败（索引↔`chapters/` 双向）→ P1。
9. **状态唯一写 owner**：同一业务状态出现在两个 `usecase` 合同里 = 状态双写 P1（回概要重判归属）；两个 `viewmodel` 写同一份业务状态 = P1；`viewmodel` 持有业务状态本体（应只镜像 usecase 流投影）/ `repository` 持有业务状态 = 归错层 P1；导航态由 `viewmodel`/`view` 直接改写而非 `coordinator` = P1。
10. **错误收口范式（per-domain `enum XxxError` 分层）**：`usecase` 须给 `enum XxxError` case 全集逐条（语义 + 可恢复性 + 上抛/降级标注），底层错误（`URLError`/`AIModelDownloaderError`/`WCDBError` 等）在单一映射点转成本域 error 再上抛；`repository` 须给 `WCDBError.code` 级错误映射表（每条对应一条失败路径）；`viewmodel` 消费 Domain 错误翻译为用户反馈、不新造业务错误码。出现字符串比较错误、空/仅日志 `catch`（吞错）、底层异常裸抛给上层、UI 层新造业务 `enum Error`、`AsyncStream` 失败静默吞（应建模为 `case failed(message:)`）→ P1。
11. **粒度判定（可编码）**：按 L1 可编码粒度逐文档抽查 ≥1 个行为全流程——步骤逐条有具体被调用的下层协议方法与参数、本单元内部判定、错误返回/映射点与状态写入点、`mermaid sequenceDiagram`（参与者用真实组件名）；「见概要」「处理 XX 能力」「调用 usecase」式无调用对象的作答 → P1。`repository` 多写须三选一标注事务形态（`performRead` / `performWrite` / `performTransaction`）并对 transaction 写明「中途失败全回滚」不变量，缺结论 → P2。
12. **测试映射核查**：每条承接行为 ≥1 成功用例 + 全部失败路径各 1 用例，逐行映射 `BHV-NNN`/`UNIT-<slug>`，测试层合理（`viewmodel` 用 mock usecase/repository 接口的 XCTest unit + loading→content/empty/error 三态断言；`usecase` 是测试密度最高层，每条行为 1 成功 + 全部失败、每个 `enum Error` case 至少 1 断言、流时序用 `for await`；`repository` 错误映射/mapper 用 unit、CRUD/分页/事务原子性用集成测试且事务回滚专用用例；`view` 用 ViewInspector/快照测试）；mock 生成走 project-conventions 槽位（手写 → Mockolo）。高风险链路（付费/权限/数据删除/导出/持久化迁移）漏测 → P1，普通失败路径漏测 → P2。
13. **合规核查**：权限/采集/三方域名/PII 单元的合规依据；扫描硬编码 secret、真实 API key、密码/盐字面量、`.env` 当线上合同、制裁 TLD、私有 API、动态执行；密钥须只写环境变量名引用回指 `external`/config。任一命中 → P1。
14. **补造红线 + 设计层级越界**：概要外结构、改 owner、拍板未选定槽位、超签名级实现体（>15 行实现体视为越界信号）→ P1；在 `usecase`/`repository` 详细正文展开 WCDB 表结构/列定义、引擎参数（WAL/加密/连接池）、迁移版本、`@Injected`/手动 `init` 装配等本应延后到实现 trace 或归 `external`/`coordinator` 的细节（除非仅出现在实现期参考字段）→ 设计层级越界 P1。
15. **薄文档判定（优先于逐条 Finding）**：≥2 章骨架雷同且无单元级实质内容（`@Published` 字段表空 / 协议方法无签名 / 流程详述 <3 步 / 缺 `mermaid sequenceDiagram` 与异常表 / 测试映射 ≤1 行）→ 结论直接「不可进入」+ 文档级重构建议，不逐条列局部 Finding。
16. 详细设计文档无存量豁免（项目约定的存量豁免只在实现/审核阶段对代码生效，不为详细设计缺陷开口）；修订形态建议只引用 L1 修订形态章。

## 诊断流程

**Step 1** 执行 EX-1~EX-6（全部 scope 模式都执行；不得因只审小批次而跳过概要承接源、项目约定、技术决策判定）。

**Step 2** 解析 `review_scope`：

- `current_chapter`：对指定章节执行 D1~D9 + 上下游边界核对；有 `chapter_subscope`/`behavior_subset` 时只对 `covered_items[]` 诊断，未覆盖项进 `not_covered_items[]`，回填 `canonical_publish_status=not_applicable_by_partial_scope`，并记录跨章待闭合风险。
- `layer_checkpoint`：按 `checkpoint_layer` 执行跨章协同诊断，不要求未来层级正文已存在。
  - `domain-model`：实体/值对象/`enum XxxError` 主语义唯一、不变量声明；被上层引用的 domain 类型已定义、零依赖、无反向依赖；`enum XxxError` 跨章定义一致。
  - `repository`：每个 `IXxxRepository` 接口被某 `usecase` 声明消费；接口在 `Domain/Repositories/` 零依赖、实现在 `Infrastructure/Persistence/`、接口实现分文件；错误映射两侧一致；无业务判定下沉、无反向注入 usecase、无 Object 泄漏。
  - `usecase`：业务状态写 owner 全局唯一；usecase 间单向无环；`enum XxxError` 全集与上抛/降级标注、底层错误单点映射；承接 P0/P1 核心能力已拆为可编码步骤；流生命周期闭合（`AsyncStream` `onTermination` 清理订阅者）。
  - `viewmodel`：每个 `@Published` 字段表完整（名称/类型/初始值/写入时机/owner/BHV）、写 owner 唯一；异步字段三态收口（loading/empty(或 success)/error 去向齐全，error 文案非「待定」）；依赖只 `@Injected` 接口、导航委托 `coordinator`、无直接持久化/网络。
  - `横切`（`view`/`coordinator`/`external`）：`view` 无业务/无导航发起/无持久化访问、主题走 `ThemeManager`、i18n 走 key；`coordinator` 导航目的地与 DI 装配（`Container` Factory 注册接口类型）闭合；`external` 凭证只引用环境变量名、WCDB 引擎参数/表定义在此承载、被引用方（repository）闭合。
- `directory_final`（默认）三段式：① 逐现存目标文档 D1~D9，产出 `per_document_results[]`；② 基于①核对跨层调用链（`view → viewmodel → usecase → repository → external` 调用与 `@Published`/流状态闭合、错误映射两侧一致、状态写 owner 全局唯一、导航全部经 coordinator、横切合同被引用方闭合）；③ 核对概要承接索引目标集合、归属表、UC/场景承接、时序图与详细正文的覆盖率。

**逐文档诊断 D1~D9**：

- **D1 骨架符合性**：L1 详细模板节齐全（单元职责 / 行为定义 / 核心数据结构 / 逐行为设计含 `mermaid sequenceDiagram` / 状态管理 / View 设计[仅 `view`+`viewmodel`，`usecase`/`repository`/`domain-model` 标 `N/A`] / 测试映射 / 不得补造清单，含 N/A 声明）；头部 `doc_type` / `l2_status` 标注正确（pending 类型须 `l2_status: pending` + design-main `L2豁免` 声明）。
- **D2 八问完整性**：逐 `UNIT-<slug>` 按 L1 合同八问 + 命中 L2 类型特化逐问取证：① 承接行为（裸 `BHV-NNN`）② 输入/输出/错误结果（Swift 签名级；`viewmodel` 逐 `@Published` 字段表 + 三态；`usecase` 逐方法签名 + 流 seed/时机；`repository` 逐 `func` 签名 + 错误映射表 + 返回域模型）③ 读写状态（写 owner 唯一）④ 调用依赖正反两面 ⑤ 失败收口 ⑥ 事件后置 ⑦ 测试映射 ⑧ 不得补造。任一问缺 P1。
- **D3 追溯核查**：`UNIT ↔ BHV` 闭合（裸 token），无幽灵 BHV、无无承接单元；状态写 owner 回指概要归属表行且一致；声明的依赖出现在概要架构图边上，并形成 `依赖 → init/@Injected 注入 → 字段持有 → usage` 闭环。
- **D4 分层一致性**：依赖正反面声明对照 Domain→App→Infrastructure→UI 单向律 + 命中 L2 硬规则逐条（规则 7/9；viewmodel §5、usecase R2/R3/R7、repository R1/R6/R7）。
- **D5 接口签名级**：`usecase`/`repository` 协议全集逐方法 Swift 签名（参数 / `async`/`throws` / `@escaping` 闭包 / `@MainActor` / 返回类型）；`domain-model` 结构体/枚举与不变量；可穷举概念用具名 `enum`，禁裸魔法值；非签名级（「提供 XX 能力」无签名）P1。
- **D6 粒度判定**：抽查行为全流程（规则 11）+ `repository` 事务边界三分法（read/write/transaction）结论。
- **D7 测试映射**：规则 12。
- **D8 错误与合规**：per-domain `enum XxxError` 分层 + 三态收口（`viewmodel`）/ 错误映射表（`repository`）/ case 全集与上抛降级（`usecase`）（规则 10）+ 合规扫描（规则 13）；异常表逐行对应一条失败路径 BHV 或八问 1 的行为分支，失配 P2。
- **D9 删除审计 + 补造红线 + 层级越界**：规则 14；对破坏性删除/压缩/替换检查 deletion ledger，区分 obsolete fact 删除、合同迁移、N/A 声明、blocking contract loss。L1 章节骨架消失、仍有效 UNIT/BHV/行为合同被 endpoint/interface 覆盖替代、测试映射或不得补造清单丢失 → P1。

**Step 3** Findings 组织（同根因合并为一条，列全部位置；判级冲突取高）与修订形态判定（L1 修订形态章；概要缺陷标注「回退概要」）。

**Step 4** 输出（按 `references/review-output.md` 合同）。

## 输出（互斥分支）

- **前置失败**（EX-1~EX-6 任一失败）：仅输出 EX 缺口（编号 / 缺口 / 证据）与最小修复动作（EX-3/EX-4/EX-5/EX-6 类缺口必须写「回退概要/项目约定/需求」而非详细侧补造）+「前置未通过，不进入逐文档诊断」结论。三类承接源状态按 `references/review-output.md` 写 `skipped_by_ex_precheck_failure:<EX-id>`，不伪造 Gate 状态。
- **前置通过**：按 `references/review-output.md`——scope 声明（含范围外未审清单，防误读为通过）→ 逐文档概况表（D1~D9 + findings 列）→ Findings 分级（每条五字段[location / problem / evidence / suggestion / 受影响 G 项] + 受影响 Gate 项）→ 跨层调用链状态（`directory_final` / `layer_checkpoint` 必含）→ 概要承接索引与时序覆盖率状态（`directory_final` 必含）→ 详细 Gate 状态表 → **三选一结论（互斥）**：`可进入实现编码` / `带明确假设可进入`（逐条假设/依据/验证时点）/ `不可进入`（阻塞 P1 清单 + 修订形态建议）→ 修订形态建议 → Gate 收口指引。
- 必须回填 `review_scope`、`per_document_results[]`、`partial_chapter_scope` / `covered_items[]` / `not_covered_items[]` / `canonical_publish_status`（无 partial scope 时按非适用分支）；不适用字段用 `not_applicable_by_review_scope`。薄文档命中时跳过逐条列举，输出薄文档证据（雷同章节对照 + 占位统计）+ 文档级重构方案。

## 边界约束

- 详细设计文档无存量豁免；审核不代写合同正文。
- 审核项必须能回到 index/L1/L2 的正向写法，不做「有没有写某个词」的形式检查。
- 当前小批次审核不得装载未命中的 L2 类型、无关需求证据或无关示例；跨章取证只读概要索引、已完成章节锚点摘要与当前范围必要引用。

## 与官方 Trellis skill 的边界

- **设计写（`ios-design-detail-writing`，姊妹 skill）**：承接概要 `design-main.md` 承接索引，按 `domain-model → repository → usecase → viewmodel → view`+`coordinator`/`external` 顺序逐章生成 `chapters/<slug>.md` 的合同八问正文——它产出 design 章。
- **设计审（本 skill）**：是 Phase 1 的详细 Gate 人工判定——判定详细设计能否进入下一阶段（实现编码）。详细设计不达标不得 `task.py start`。
- **区别于官方 `trellis-brainstorm`**：brainstorm 在更早阶段做需求/方案发散，不产出受 index/L1/L2 约束的 design 章，也不做 Gate 判定。
- **区别于官方 `trellis-check`**：`trellis-check` 是实现后的代码质检（对照已落地 Swift 代码查质量/回归）；本 skill 是实现前的设计文档 Gate（对照 index/L1/L2 查设计合同是否可编码），二者阶段、对象、判定口径均不同，不互相替代。

## Review Evidence 与 detail 确认

结论为「可进入编码」或「带明确假设可进入」时，先写入 review evidence，不直接开始实现：

```bash
python3 .trellis/scripts/guru/guru_gate.py record-review detail <task_dir> \
  --result clean \
  --max-severity low \
  --reviewer clean-context \
  --run-id <fresh-run-id> \
  --evidence "<本次 detail review 证据摘要>" \
  --deletion-audit "<none|删除审计摘要>"
```

若存在 medium+ finding，必须输出 `--result findings --max-severity medium|high|critical --finding-class REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|IMPLEMENT_DEFECT|PROCESS_DEFECT`，并停止进入编码。

当前 digest 下两个不同 `run_id` 的 clean review 记录后，提示用户运行：

```bash
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir>
```

confirm detail 的 strict/soft 通道以 workflow Trellis System 节为准；未确认前不得 `task.py start`。

## 参考资料

- 五阶段方法入口（doc_type 权威七类 / 编号纪律 / 五道 Gate 口径）：`.trellis/spec/harness/index.md`
- 详细阶段中立规范（L1，合同八问与详细 Gate 完成条件）：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- 类型差异（L2，v1 仅前三类提供）：
  - `.trellis/spec/harness/detail/detail-type-viewmodel.md`
  - `.trellis/spec/harness/detail/detail-type-usecase.md`
  - `.trellis/spec/harness/detail/detail-type-repository.md`
  - （pending 四类 `domain-model`/`view`/`coordinator`/`external` 无 L2，按 L1 八问 + `L2豁免` 核查）
- 通用方法与红线：`.trellis/spec/guides/golden-path.md`
- 项目约定槽位与 C1~C6：`.trellis/spec/conventions/project-conventions.md`
- 实现 trace 合同：`.trellis/spec/harness/implementation/implementation-trace-contract.md`
- 逐 doc_type 取证矩阵与判级：`references/review-baseline.md`
- 输出字段合同：`references/review-output.md`
