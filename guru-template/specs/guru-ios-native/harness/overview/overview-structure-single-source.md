# iOS 原生概要设计 — 单一来源规范（L1 SSOT）

> 本文件是 iOS 原生（DDD 四层 + SwiftUI + FactoryKit + WCDBSwift）概要设计阶段的唯一权威规则。writing/review skill 只做编排与判定，不得复写本文规则正文。
> 上游硬输入：需求阶段产物（核心能力清单 P0/P1 + 行为规格，需求五要素已收敛）。
> 横向依赖：通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律 + 七类 doc_type 入口决策树）+ 目标仓库 `.trellis/spec/conventions/project-conventions.md`（项目槽位取值）。
> 层级契约：本文（L1）承载规则正文与完成条件；writing/review skill 的 `references/` 只承载编排细则、模板与示例；冲突时 **L1 > L2（detail-type-*.md）> references > SKILL.md**。
> 平台档案证据来源：`story-verse-mac`（DDD 四层实测仓库）。本文所有分层、目录、DI、持久化口径以该仓库 + 全局钉死约定为准，不照抄 flutter（Page/Controller/Service/DataSource/Dao/Api）或 Go（Entry/Biz/IC/Utility/Data）的类型名。

---

## 1. 装载与硬前置（WX 写作 / EX 审核共用）

执行写作或审核前必须依次确认，任一失败即终止并输出前置缺口（不展开后续章节）：

- **P1** 本文件可读：`.trellis/spec/harness/overview/overview-structure-single-source.md`。
- **P2** 通用 golden-path 可读：`.trellis/spec/guides/golden-path.md`。分层依赖律（Domain 零依赖 / Domain→App→Infrastructure→UI 单向）与七类 doc_type 入口决策树是归属判定基准。
- **P3** 目标仓库 `.trellis/spec/conventions/project-conventions.md` 可读，且通过其内置校验清单（UI 框架 / 网络层 / 日志 / JSON 修复 / 测试框架 / i18n / 主题 / feature 模块结构 / mock 生成 / 构建自动化等槽位已定值或显式标 pending）。
- **P4** 需求产物可定位，且核心能力清单存在 P0/P1 条目。若需求产物缺失：仍可产出概要草稿，但必须记录**显式假设**（依据、影响范围、验证时点），且不得宣称"可进入详细设计"。
- **P5** 判轨完成：task.json `guru_chain` 已确定（full / light）；full 链另须确认 `design_package` 路径已声明或将在阶段 0 声明。

平台前置补充（iOS 特有，P3 的延伸）：

- **P3a** project-conventions 的 UI 框架槽位若标记"SwiftUI 主 + RxSwift 遗留"，概要设计的 viewmodel/view 归属一律按纯 SwiftUI（`ObservableObject + @Published`）口径，RxSwift 只在涉及遗留模块迁移时显式标注，禁止新增 RxSwift 状态流作为概要决策。
- **P3b** 持久化槽位必须为 WCDBSwift；出现 CoreData/SwiftData 选型即 P1 阻断（违反全局钉死约定）。

---

## 2. 产物合同（按链型分轨）

**轨道判定**：task.json `guru_chain`（`guru_after_create` 创建时默认 `full`）。涉及核心玩法 / 付费 / 广告 / 存档 / 权限 / 数据采集 / 端侧 LLM / 跨进程持久化等高风险需求走 **full 链（目录级设计包）**；轻量链（`client-small-iteration-dev` 分流且获用户显式同意后降级）走任务内单文件 `design.md`。`guru_gate.py` 按链型自动切换检查口径。

### 2a. full 链：目录级设计包

- 位置：目标仓库 `docs/design/<feature>/`（版本级需求用 `docs/design/versions/<ver>/`），并写入 task.json `design_package` 字段（相对 repo root）。
- 骨架（概要阶段建立，gate 查存在性）：
  - `README.md` — 仅导航 / 索引 / 追踪矩阵入口，不承载事实正文。
  - `design-main.md` — 概要主定义，必含本节「必含章节」全部条目。
  - `chapters/` — 详细设计逐章承载区（文件本体在详细阶段产出）。
- 任务内 `design.md` 退为指针 + 摘要：链接 design_package，不承载主定义。
- 承接索引每条必须落到章节文件：`chapter_target → detail_doc_type → chapters/<slug>.md`；gate 在详细 Gate 检查索引↔文件双向闭合（引用缺文件、孤儿章节均拦截）。
- 详细文档命名：`<序号>-<doc_type>-<模块 slug>-design.md`（doc_type 取本文 §7 的七类裸 token）。

### 2b. light 链：单文件

概要主定义承载于任务内 `design.md` **§1 概要设计**，必含「必含章节」第 1~8 条（第 5 条架构总览可简化：保留一句话架构 + 页面流文字描述，分层图与时序图策略表不强制；第 9 条自检可简化为 Gate 前自查，不强制成节）。light 链仍须给出 viewmodel/usecase/repository/domain-model/view/coordinator/external 七类的归属判定，不得因单文件而省略归属表。

### 必含章节（两轨共用语义）

1. **设计约束与输入**：承接的需求核心能力（逐条引用 P0/P1 编号 + 需求五要素锚点）、技术栈约束（DDD 四层 / SwiftUI / FactoryKit / WCDBSwift）、显式假设清单、project-conventions 槽位取值快照。
2. **行为集合**：行为枚举结果（见 §3），每条 `### BHV-NNN <短名>`。
3. **归属判定表**：行为 / 状态 → 四层 owner（七类 doc_type）→ 三问归属理由（见 §4）。**这是概要的核心产物。**
4. **页面流与路由**：SwiftUI View 间导航（必经 AppCoordinator）、入参出参、deep link、失败 / 取消路径去向（仅 UI 需求；非 UI 需求显式标注 N/A 及依据）。
5. **架构总览（人审视图）**（full 链必含成节，合同见 §2.5）：一句话架构 + DDD 四层分层架构图 + 页面流图 + 核心 UC 表 + UC 承接表 + 时序图策略表。
6. **技术决策承接清单** `technology_decision_handoff[]`：端侧 / 远程 LLM 选型、TTS/STT SDK、WCDBSwift schema 策略、FactoryKit scope 策略、平台权限（麦克风 / 相册 / 文件）、缓存策略等架构显著决策（合同见 §2.6）。
7. **详细设计承接索引**：`chapter_target → detail_doc_type` 映射，`detail_doc_type` 取值**严格限定于 §7 的七类**。每个归属判定表中的 owner 必须被至少一个索引条目覆盖；full 链每条另附 `chapters/<slug>.md` 目标文件，并标注 `l2_status`（见 §2.7）。
8. **未决问题**：显式列出，标注风险等级（P1/P2/P3）。
9. **架构就绪自检**（full 链必含成节）：对照 §6 G1~Gn 逐项自评（满足 / 缺口 + 闭合计划）；存在未闭合 G 项不得送审概要 Gate。

### 2.5 架构总览（人审视图）合同

架构总览是概要的人类可审核入口——评审者不读全文也能从这一节判断"这个设计长什么样、对不对、违不违反分层依赖律"。full 链六件套缺一不可。

**① 一句话架构**。固定格式：

> 用户经 `<入口 SwiftUI View / 路由>` 进入，由 `<ViewModel>` 承接 `<核心行为>` 的状态，调用 `<UseCase>` 编排业务规则，经 `<Repository 接口>` 访问数据（实现在 Infrastructure），导航由 `<AppCoordinator>` 收口，按需经 `<external>` 集成 `<网络/SDK/WCDBSwift>`。

**② 分层架构图**（mermaid graph）。要求：

- 用 subgraph 表达 DDD 四层：`UI`（view / viewmodel）、`App`（coordinator / DI 装配）、`Domain`（usecase / repository 接口 / domain-model）、`Infrastructure`（repository 实现 / external）。
- 箭头只表达依赖方向，且必须符合分层依赖律：**Domain 零依赖；依赖方向 Domain ← App ← Infrastructure ← UI 的反向声明，但运行期调用方向为 UI → App → Domain ← Infrastructure（Infrastructure 实现 Domain 接口）**。图中不得出现 UI 直连 Infrastructure 持久化、View 间直接导航绕过 coordinator。
- 图中出现的组件必须与归属判定表的 owner 一一对应；图中不得出现归属表之外的组件，不得出现 Manager/Helper/Util 这类无行为来源结构。

**③ 页面流图**（mermaid graph 或 flowchart，仅 UI 需求）。要求：

- 节点 = SwiftUI View（标注路由 / `NavigationDestination` 枚举值），边 = 导航动作（标注触发 BHV 编号 + 入参要点 + 经 AppCoordinator 的方法名如 `navigateToStoryDetail`）。
- 覆盖本需求新增 / 修改的全部页面路径，含失败 / 取消 / 权限拒绝路径的去向。
- 非 UI 需求（纯后台任务、纯持久化迁移、纯 external 集成）显式标注 N/A 及依据。

**④ 核心 UC 表**。从需求验收场景提炼用户可感知用例：

| 列 | 含义 |
|----|------|
| `uc_id` | UC-<序号>，创建后不复用不重排 |
| `uc_title` | 用户视角一句话（动词开头） |
| `actor_or_trigger` | 用户操作 / 系统事件 / 生命周期（前后台 / 进程恢复） |
| `source_refs` | 需求来源锚点（prd 章节或 BHV 编号） |
| `goal` | 用户可验证的完成态 |
| `priority` | 对应核心能力 P0/P1 |

**⑤ UC 承接表**。逐 UC 回答"谁实现它"：

| 列 | 含义 |
|----|------|
| `uc_id` | 对应④ |
| `page_refs` | 涉及 SwiftUI View / 路由 |
| `bhv_refs` | 承接的 BHV 编号（必须存在于 prd） |
| `owner_refs` | 归属表中的 owner（按七类 doc_type 写 UNIT-<slug>） |
| `index_refs` | §7 承接索引的 chapter_target |

**⑥ 时序图策略表**。逐 UC 声明时序图交付策略：

| 列 | 含义 |
|----|------|
| `uc_id` | 对应④ |
| `strategy` | `独立` / `合并` / `豁免` 三选一 |
| `sequence_section` | 可定位的 sequenceDiagram 所在小节锚点（独立 / 合并必填） |
| `merged_coverage` | 合并图覆盖的 uc_id 清单（合并时必填） |
| `exemption_reason` | 豁免理由 + 最小行为链（豁免时必填） |

**时序图回填硬约束**：送审概要 Gate 前，非豁免 UC 必须有可定位的真实 `sequenceDiagram`（mermaid），覆盖 `View → ViewModel → UseCase → Repository(接口) → Infrastructure(repository 实现 / external) → 返回 / 状态推进`（按实际链路裁剪），导航穿插 `AppCoordinator`，步骤编号与文字详述一一对应。早期写作可用计划锚点占位，占位状态下不得宣称可送审。`sequenceDiagram` 中禁止出现 View 直连 Repository 实现 / WCDBSwift 的链路（违反分层依赖律）。

### 2.6 技术决策承接清单合同

`technology_decision_handoff[]` 逐条字段，缺一即该条不完整：

| 字段 | 要求 |
|------|------|
| `decision_id` | TD-<序号> |
| `decision_point` | 决策点（如"端侧 LLM 选型"、"TTS 合成 SDK"、"WCDBSwift 表迁移策略"、"麦克风权限请求时机"、"FactoryKit scope（singleton/cached/shared）"） |
| `candidates` | 候选清单（≥1；只有一个候选时说明为何无备选） |
| `selected` | 选定项，或显式 `未选定`（未选定项禁止详细 / 实现阶段私自拍板） |
| `rationale` | 选择理由（回指架构驱动 / 约束，不得反向倒推） |
| `detail_expansion_targets` | 交给详细设计展开的字段 / 合同（指向 §7 索引条目 + 对应 doc_type，通常 external / repository / usecase） |
| `compliance_basis` | 涉权限 / 数据采集 / 三方域名 / PII 时必填：最小权限与用途可解释依据（如 `NSMicrophoneUsageDescription` 用途串）；否则写 N/A |

不保存任何 secret value；密钥 / 凭证只写引用方式（Keychain 引用 / 环境变量名 / 配置注入 / xcconfig 引用），出现真实 key 即审核 P1。

### 2.7 详细承接索引 doc_type 与 L2 状态合同

承接索引每条的 `detail_doc_type` 必须取自 §7 的七类裸 token，并标注 L2 承载状态：

| 字段 | 要求 |
|------|------|
| `chapter_target` | 详细章节锚点（full 链对应 `chapters/<slug>.md`） |
| `detail_doc_type` | 七类之一：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external` |
| `owner_refs` | 回指归属表中的 UNIT-<slug>（同一 owner 可被多个索引条目复用，但语义不重叠） |
| `l2_status` | `full`（该 doc_type 已有 L2 文件 detail-type-*.md 承载合同八问展开口径）/ `pending`（暂按 L1 合同八问展开，L2 文件待补） |

**v1 L2 文件供给状态（钉死，下游据此判 l2_status）**：

- `viewmodel` → `detail-type-viewmodel.md`（**full**，与 flutter `controller` 对应位）。
- `usecase` → `detail-type-usecase.md`（**full**，与 flutter `usecase` 对应位）。
- `repository` → `detail-type-repository.md`（**full**，与 flutter `repository-datasource` 合并对应位）。
- `domain-model` → **pending**（暂按本文 §7 + 详细 L1 合同八问展开）。
- `view` → **pending**。
- `coordinator` → **pending**。
- `external` → **pending**。

`l2_status: pending` 的索引条目仍可进入详细设计，但详细阶段必须按合同八问全量展开（不得因无 L2 文件而豁免合同字段）；**full 链的完整链路 Gate 须显式记录这四类的 L2 豁免**（即"L2 文件 pending，按 L1 合同八问承载"是已知合法状态，不计为缺口）。

---

## 3. 行为枚举方法（生成动作）

从需求行为规格出发，按以下顺序枚举行为空间，**禁止从名词 / 组件 / SwiftUI View 名出发**：

1. 用户操作（点击、文本输入、手势、拖拽、进入 / 离开页面、长按菜单）。
2. 系统反应（`@Published` 状态变化、WCDBSwift 读写、网络请求、端侧 / 远程 LLM 调用、TTS/STT、副作用如导出 / 合成）。
3. 失败路径（网络失败、数据缺失、非法输入、权限拒绝（麦克风 / 相册 / 文件）、并发冲突、WCDBSwift 损坏 / 迁移失败、磁盘空间不足、模型下载失败）。
4. 生命周期事件（前后台切换、scene 销毁 / 恢复、进程被杀后恢复、长任务进度续传）。

每条行为：`Given <前置> When <触发> Then <后置 + 状态变化>`，并标注涉及的状态（哪个 ViewModel 的哪个 `@Published`）与数据（哪个 domain-model / 哪个 Repository）。

### 3.1 粒度标准（四条，写作与审核共用）

1. **可直接实现**：行为描述具体到详细设计可直接展开为合同（方法签名 / DDL / 字段），不需要再分解业务语义。
2. **明确触发与归属**：每条行为能指出触发者（用户 / 系统 / 生命周期）与候选 owner 层（七类 doc_type 中的一类）。
3. **完整链路**：从入口行为出发能追踪到全部下游行为（含失败路径），无断链；如 `提交创作` 必须能追踪到 usecase 编排 → repository 落库 → external LLM 调用 → 失败回退。
4. **粒度一致**：同一文档内所有行为的描述粒度一致；出现"处理创作"这类粗粒度行为即不达标。

正反例：

- ✅ `BHV-012 提交故事创作表单`：Given 标题 / 年龄段 / 类型已填 When 点击生成 Then ViewModel 校验输入 → 调 `GenerateStory` UseCase → 经 external 调端侧 LLM → 解析结果经 IStoryRepository 落 WCDBSwift → 成功推 `@Published` 故事态并经 AppCoordinator 导航详情页 / 失败展示分层 enum Error 文案。
- ❌ `BHV-012 处理创作`：Given 用户要创作 When 操作 Then 创作完成。（无前置细节、无失败路径、无状态 / 数据 / 层归属）

### 3.2 行为 ↔ UC 回指

每条 BHV 必须能回指至少一个核心 UC（§2.5 ④）；UC 承接表（⑤）的 `bhv_refs` 与行为集合做双向核对，出现"行为无 UC 来源"或"UC 无行为承接"均为审核缺口。

### 3.3 编号纪律

- 每条行为以 `### BHV-NNN <短名>` 标题定义（NNN 数字；创建后不复用、不重排，删除留洞）。
- 每个设计单元以 `UNIT-<slug>` 标识（详细标题用），slug 取组件领域语义（如 `UNIT-story-repository`、`UNIT-generate-story-usecase`、`UNIT-home-viewmodel`）。
- 归属表、详细设计、测试与实现切片对行为 / 单元的引用一律写裸 token（`BHV-NNN` / `UNIT-<slug>`）——这是机器追溯依据（`guru_gate.py trace-matrix` 据此生成 行为 × 需求场景 × 归属 × 单元 × 测试 × 切片 矩阵，断链被 Gate 拦截）。归属判定表逐行以 BHV 编号开头。

### 3.4 行为 ↔ REQ-UC 承接（需求源回指 + 命名消歧）

full 链存在正式需求包（版本化组织见需求包标准 single-source §15）时，BHV 标题可在短名前以 `[REQ-UC-XXX]`（可多个，多对多）显式承接需求源场景，形如 `### BHV-001 [REQ-UC-005, REQ-UC-007] 生成故事`。`trace-matrix` 解析该承接生成「需求场景（REQ-UC）」列（行展开），版本级 `trace-aggregate` 据此把多 task 聚合进 `traceability.md`。需求包标准 `--require-req-uc`（或 task.json `require_req_uc:true`）可强制 BHV 必须带 REQ-UC；旧 prd（BHV 无 REQ-UC）默认不拦、列空、不断链。

**命名消歧（强制）**：`REQ-UC-XXX` 是**需求源场景**（requirement source use case，主定义在需求包标准 single-source §6），与本文 §2.5/§3.2 的 `UC-<序号>`（概要设计**架构核心用例**，`uc_id`）是**两套独立编号**，不混用同一字段。`source_refs`/`bhv_refs` 仍指 overview 内的 `UC-<序号>` 与 BHV；BHV 标题的 `[REQ-UC-XXX]` 指需求源。§3.2 的 `BHV ↔ UC-<序号>` 人审映射不因本规则改写。

---

## 4. 归属判定方法（核心规则）

对每条行为 / 每个状态，按分层依赖律判定**唯一 owner**（七类 doc_type 之一）。判定口径（与 §7 doc_type 定义一一对应）：

| 行为 / 状态类型 | owner 层 | doc_type | 判定理由模板 |
|---------------|---------|----------|-------------|
| 界面结构、SwiftUI 视图布局、design token / ThemeManager 消费、用户输入采集 | UI | `view` | 只承接展示与输入，不拥有业务规则、不持有可变业务状态 |
| 页面级 `@Published` 状态字段、输入校验编排、调用 UseCase、订阅领域事件、导航触发委托 | UI | `viewmodel` | `ObservableObject` 页面生命周期内的状态容器，是该页面状态的唯一写 owner |
| 有状态 / 跨实体业务流程、业务规则与不变量编排、领域事件发布 | Domain | `usecase` | 业务编排 owner，零 UI 依赖，不直接操作持久化（经 Repository 接口） |
| 数据访问合同、查询 / 缓存策略、`enum PersistenceError` 转换、跨 DTO 映射 | Domain（接口）+ Infrastructure（实现） | `repository` | 数据一致性 owner；接口在 Domain 保证零依赖，实现在 Infrastructure 收口 WCDBSwift |
| 实体 / 值对象 / `enum Error` / 不变量定义、领域枚举 | Domain | `domain-model` | 领域事实 owner，零依赖、可被任意层导入，不含编排或 IO |
| 跨页面导航流、`NavigationDestination` 枚举、FactoryKit `Container` 装配 | App | `coordinator` | 导航与 DI 装配 owner；View 间不得直接导航必经此层 |
| 网络（URLSession/Moya）、端侧 / 远程 LLM、TTS/STT SDK、WCDBSwift 底层、第三方 SDK 集成 | Infrastructure | `external` | 外部依赖 / 平台能力收口，被 Domain 接口约束，不外泄技术细节给上层 |

归属判定表每行必须回答**三问**：

1. **为什么属于它？**（行为语义与该 doc_type 职责的对应证据）
2. **为什么不属于别人？**（排除相邻层的理由，尤其是 viewmodel↔usecase、usecase↔repository、repository↔external 的边界）
3. **为什么需要（或不需要）独立存在？**（单行为单元是否有独立边界证据；无则收回父单元）

硬约束（违反直接 review fail）：

- **归属方向不得违反分层依赖律**：Domain 零依赖（不得 import App/Infrastructure/UI）；不得把数据访问归给 viewmodel；不得把业务规则归给 view；不得把导航归给 view（必经 coordinator）；不得把持久化访问归给 view（必经 repository）。
- **一个状态只能有一个写 owner**：页面态写 owner 是对应 viewmodel，业务态写 owner 是对应 usecase；其他层只能读 / 订阅。
- **不得发明无行为来源的结构**：禁止在概要发明 `Manager` / `Helper` / `Util` / `Service`（除非已是 project-conventions 既有横切，且有行为来源）；尤其禁止自创 `transport-handler` / `service` 这类不在七类 doc_type 内的类型名。
- **FactoryKit DI 强制**：跨层依赖一律 `@Injected` 注入（禁手动 `init` 硬编码依赖），DI 装配归 `coordinator`。
- **enum Error 分层定义**：每个 domain 的错误是 `domain-model` 的 `enum Error`；持久化错误（`PersistenceError`）由 repository 实现转换，不外泄底层异常。

### 4.1 命名规范（组件与行为）

- **组件名（UNIT slug 与 Swift 类型名）**：定语 + 名词，定语体现领域（Story、Voice、Export、Home），名词体现层角色并使用本表既有后缀：
  - `view` → `XxxView`（SwiftUI）；`viewmodel` → `XxxViewModel`（`ObservableObject`）。
  - `usecase` → `XxxUseCase` / 动词短语 UseCase（如 `GenerateStoryUseCase`）。
  - `repository` → 接口 `IXxxRepository`（Domain）+ 实现 `XxxRepository`（Infrastructure）。
  - `domain-model` → 实体 `Xxx`（Story/Chapter/Section）、值对象 `XxxVO`、枚举 `XxxError` / `XxxType`。
  - `coordinator` → `AppCoordinator` / `XxxCoordinator` + `Container+Xxx`（DI 装配）。
  - `external` → `XxxAdapter` / `XxxService`（仅 Infrastructure 集成位，接口侧用 `IXxxAdapter` 留在 Domain）。
  - 禁止 `Manager` / `Helper` / `Handler` 等含混后缀作为新增概要组件（既有遗留除外，且须标注遗留）。
- **行为名**：单个动词或动词 + 宾语，≤2 个英文单词；不重复组件名（`StoryRepository` 的保存行为命名 `save`，不是 `saveStory`）。
- 取数动词区分语义：`list`（取多个）/ `one`（取单个）/ `get`（取必然存在的）/ `fetch`（取可能不存在的，对应 `IStoryRepository` 的可空返回）。
- 项目级取值（目录结构、feature 模块组织、文件名、序列化风格、mock 生成方式）以 `.trellis/spec/conventions/project-conventions.md` 槽位为准，本节不覆盖。

---

## 5. 阶段边界（概要不做什么）

概要只闭合：**边界、语义、链路、取舍、索引**。以下内容禁止在概要展开，发现即属越界：

- 字段级合同、Swift 方法签名 / 协议方法、WCDBSwift 表结构 / `TableCodable` 字段 / 迁移 DDL、具体 API 路径与 JSON schema（属详细设计，由对应 doc_type 承接）。
- SDK 初始化 / 调用参数、FactoryKit `register` 闭包细节、LLM prompt 正文、配置项取值、secret value（属详细设计 / 实现，secret 永不落文档）。
- Swift 代码、伪代码、`private extension` 内部实现安排、文件路径级实现安排（属实现阶段）。
- 重新决定需求 scope 或私自拍板未决业务规则（回需求阶段）。
- 把 `technology_decision_handoff[]` 中"未选定"的决策直接写成已选定。
- 把 `l2_status: pending` 的四类（domain-model/view/coordinator/external）的合同八问字段写成详细正文（概要只写归属与索引，详细阶段展开）。

---

## 6. 完成判定与 Gate（G1~Gn）

概要可进入详细设计，当且仅当（G1~G5 两轨共用；G6~G9 仅 full 链强制）：

- **G1** 行为集合覆盖需求全部 P0/P1 核心能力（逐条可追溯到 BHV 编号），且每条行为满足 §3.1 粒度标准。
- **G2** 归属判定表完整：每条行为有唯一 owner（七类 doc_type 之一）+ 三问理由；无分层依赖律违例（Domain 零依赖 / 单向依赖 / 无 View 直连持久化 / 无 View 间直接导航 / FactoryKit DI / enum Error 分层）。
- **G3** 涉及权限（麦克风 / 相册 / 文件 / 网络）/ 数据采集 / 三方域名 / PII 的行为，已在 `technology_decision_handoff[]` 标注合规依据（最小权限、用途串可解释）。
- **G4** 详细设计承接索引非空，且覆盖归属表全部 owner；每条 `detail_doc_type` 取自 §7 七类，并标注 `l2_status`（full 链逐条落到 `chapters/<slug>.md` 文件名）。
- **G5** 未决问题中无高风险项（或已获用户确认带假设进入）。
- **G6** 架构总览六件套齐全（§2.5 ①~⑥）：一句话架构、DDD 四层分层架构图、页面流图（或 N/A 依据）、核心 UC 表、UC 承接表、时序图策略表，且图中组件与归属表一一对应、无分层违例链路。
- **G7** 时序图策略闭合：非豁免 UC 均有可定位 sequenceDiagram（覆盖 View→ViewModel→UseCase→Repository→Infrastructure 链、导航穿插 AppCoordinator）；合并图列出覆盖清单；豁免项有理由 + 最小行为链；无占位锚点残留。
- **G8** `technology_decision_handoff[]` 逐条字段完整（§2.6），无"未选定但已被下游引用"的条目；无 secret value 落盘。
- **G9** L2 承接状态清晰：每条索引条目 `l2_status` 已标注；`pending` 的四类（domain-model/view/coordinator/external）已在 full 链 Gate 记录为已知合法的 L2 豁免，未被误判为缺口；`full` 的三类（viewmodel/usecase/repository）索引指向的 detail-type-*.md 口径与归属表 doc_type 一致。

---

## 7. iOS 详细设计 doc_type 权威七类（全程唯一，禁改名 / 增减 / 换数）

下游所有 `detail_doc_type` 取值、UNIT 归属、索引条目一律用以下七类裸 token。**禁止自创 `transport-handler` / `service` / `datasource` / `dao` / `controller` 等不在表内的类型名**（flutter/Go 的类型名不适用于 iOS）。

| # | doc_type | 层 | 定义 | 正向产物（详细阶段展开） | 不适用场景 | 好例 | 坏例 |
|---|----------|----|------|------|----------|------|------|
| 1 | `viewmodel` | UI | `ObservableObject + @Published` 状态容器，承接页面态、输入校验编排、调用 UseCase、订阅领域事件、委托导航 | 状态字段集、输入→UseCase 编排合同、错误态映射、生命周期钩子 | 承接业务规则 / 不变量（应在 usecase）；直接读写 WCDBSwift（应经 repository） | `HomeViewModel` 持有 `@Published var stories` 并调 `ListStoriesUseCase` | `HomeViewModel` 内直接 `database.getObjects(...)` |
| 2 | `usecase` | Domain | 业务编排，零 UI 依赖，规则 / 不变量 / 状态流 owner，经 Repository 接口访问数据 | 编排步骤、不变量校验、领域事件发布、失败语义（抛 domain enum Error） | 持有 UI 状态 / `@Published`；直接 import Infrastructure 实现 | `GenerateStoryUseCase` 编排校验→生成→落库→发事件 | `GenerateStoryUseCase` 直接 `import WCDBSwift` |
| 3 | `repository` | Domain 接口 + Infrastructure 实现（合并一类） | 数据访问合同 + 缓存 / 查询策略 + `PersistenceError` 转换；接口 `IXxxRepository` 在 Domain，实现 `XxxRepository` 在 Infrastructure | 接口方法语义（list/one/get/fetch/save/delete）、查询条件、错误转换边界、缓存口径 | 暴露 WCDBSwift 类型给上层；承接业务规则（应在 usecase） | `IStoryRepository` + `StoryRepository`（WCDBSwift 实现）转 `PersistenceError` | 接口方法返回 `WCDBSwift.Table<...>` |
| 4 | `domain-model` | Domain | 实体 / 值对象 / `enum Error` / 领域枚举 / 不变量，零依赖、可被任意层导入 | 实体字段语义、值对象不变量、`enum XxxError` 分层错误、领域枚举 | 含 IO / 编排 / 持久化注解外泄；import 其他三层 | `Story` 实体 + `StoryError` enum + `StoryType` 枚举 | `Story` 内嵌 WCDBSwift `TableCodable` 持久化逻辑 |
| 5 | `view` | UI | SwiftUI View，只展示 + 输入，无业务、无可变业务态 | 视图结构、ThemeManager / token 消费、输入采集、绑定 viewmodel、导航触发委托 | 持有业务状态；调用 UseCase / Repository；View 间直接导航 | `HomeView` 绑定 `HomeViewModel` 并经 coordinator 跳转 | `HomeView` 内 `if story.isValid { save() }` 业务判断 |
| 6 | `coordinator` | App | `AppCoordinator` 导航流 + `NavigationDestination` 枚举 + FactoryKit `Container` DI 装配 | 导航方法语义、目的地枚举、DI 注册 scope 策略（singleton/cached/shared） | 承接业务规则；持有领域状态；混入持久化 | `AppCoordinator.navigateToStoryDetail` + `Container+ViewModels` 注册 | `AppCoordinator` 内编排故事生成业务 |
| 7 | `external` | Infrastructure | 外部集成：网络（URLSession/Moya）、端侧 / 远程 LLM、TTS/STT SDK、WCDBSwift 底层、第三方 SDK | 集成边界、协议适配（实现 Domain 的 `IXxxAdapter`）、技术错误归一、SDK 调用边界 | 承接业务语义 / prompt 业务组装（应在 usecase）；外泄技术细节给 Domain | `OnDeviceLLMAdapter` 实现 `IOnDeviceLLMAdapter`、`DatabaseManager` 收口 WCDBSwift | LLM adapter 内做"低置信度则降级业务规则"判断 |

**doc_type ↔ 四层 owner 映射**：UI = `view` + `viewmodel`；App = `coordinator`；Domain = `usecase` + `repository`（接口）+ `domain-model`；Infrastructure = `repository`（实现）+ `external`。

**写作顺序（自底向上）**：`domain-model` → `repository` → `usecase` → `viewmodel` → `view` + `coordinator` / `external`（横切）。归属表与索引按此顺序组织有利于校验依赖方向。

**与 flutter 对应位（仅供 L2 文件供给参照，不得反向照抄类型名）**：`viewmodel`↔flutter `controller`、`usecase`↔flutter `usecase`、`repository`↔flutter `repository-datasource`（合并）；其余四类无 flutter 对应 L2，按本文 §7 + 详细 L1 合同八问展开。

---

## 8. 审核基线（review 专用）

- **先证据后结论**：每条 finding 必须带章节锚点或明确缺失对象；引用正文时给出可定位的小节 / 表格行 / BHV 编号 / UNIT slug。
- **严重度**：
  - **P1**（阻塞）：违反硬约束 / Gate 项缺失——分层依赖律违例（Domain 有依赖 / View 直连持久化 / View 间直接导航 / 手动 DI 替代 FactoryKit / CoreData/SwiftData 替代 WCDBSwift）、doc_type 用了七类之外的名字、归属表缺失或行为无 owner、secret value 落盘、未选定决策被下游引用。
  - **P2**（应修）：归属三问理由不充分、索引不完整或未覆盖全部 owner、`l2_status` 未标注、图表与归属表不一致、enum Error 未分层、时序图占位未回填。
  - **P3**（建议）：表述 / 一致性 / 命名规范建议。
- **输出互斥分支**：前置（§1）失败 → 只输出前置缺口与修复动作，不展开逐章审核；前置通过 → 逐条 findings（severity / location / problem / suggestion）+ 结构概况 + "是否可进入详细设计"互斥结论。
- **存量豁免**：仅适用于实现阶段代码违例（如遗留 RxSwift / 遗留 Manager），**概要文档本身无存量豁免**——新概要文档必须全量符合本规范。`l2_status: pending` 的四类不是存量豁免，而是 §2.7 钉死的合法 L2 缺省承载状态。
- 逐章取证矩阵与判级细则的执行口径在 review skill 的 `references/`（编排层产物，不得与本文冲突）；冲突时本文（L1）为准。

---

## 9. 修订形态判定

按 findings 修订前必须先判定形态：

- **局部修订**（在原文档上改）：补一条行为、补一行归属三问理由、补一条索引条目、补 / 改一张图、改措辞、补 `l2_status` 标注、回填一个时序图占位锚点。
- **文档级重构**（重做对应章节，禁止用局部补丁掩盖错误模型）：
  - 归属模型错误（owner 大面积错位、doc_type 用错层、Domain 依赖外泄被系统性默许）。
  - 行为枚举从名词 / SwiftUI View 名 / 组件名倒推（违反 §3 生成动作）。
  - 索引与归属表系统性脱节（owner 未被索引覆盖、索引指向不存在的 doc_type）。
  - 架构总览与正文两套口径（图中组件与归属表不一致、依赖方向矛盾）。
  - 自创 doc_type 类型名（transport-handler/service/datasource 等）贯穿全文。

审核发现上游缺陷（需求行为缺失 / 矛盾 / 五要素不全）→ 回退需求阶段修订，禁止在概要补造业务规则或拍板未决 scope。
