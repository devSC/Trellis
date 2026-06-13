# L2 类型规范：repository（数据访问合同 — iOS 原生）

> 从属于 L1 `detail-structure-single-source.md`（iOS 原生详细设计单一来源）；本文件只写 `repository` 这一类的差异规则，不复述 L1 的合同八问骨架与 Gate。
> 装载路径（安装后）：本文件 = `.trellis/spec/harness/detail/detail-type-repository.md`；通用迷你路径 = `.trellis/spec/guides/golden-path.md`（对齐其 §Domain 零依赖、§依赖单向、§Infrastructure 持久化、§Repository 模式四节）。
> doc_type 权威：`repository` 是 IOS_BRIEF 钉死七类（`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`）之一，全程唯一，禁改名/增减。本类**合并**「Domain 侧 `IXxxRepository` 接口」+「Infrastructure 侧实现」为同一 doc_type，与 flutter 的 `repository-datasource` 一一对应——但 iOS **不拆 datasource 子类型**：本平台数据来源适配（WCDBSwift 持久化、网络 SDK）归 `external`，repository 直接编排 `external` 与 DatabaseManager。

---

## 适用对象

`IXxxRepository`（Domain 侧数据访问合约，零依赖协议）+ 其 Infrastructure 侧实现（`XxxRepository`，WCDBSwift 持久化与外部来源编排）。

**归本类**：领域聚合/实体的增删改查合约、查询条件（criteria）、分页、计数、批量、事务化的多表原子写、底层异常→`enum Error` 的映射、Domain 实体 ↔ 持久化 Object（WCDB `TableCodable`）的转换归属声明。

**不归本类**：
- 业务规则编排（属 `usecase`——repository 只做数据存取，不判业务前置条件）。
- WCDBSwift 引擎初始化/连接池/WAL/加密/损坏修复（属 `external`，由 `DatabaseManaging` / `DatabaseManager` 承载，repository 注入它）。
- 网络请求拼装与第三方 SDK 调用细节（属 `external`，repository 注入其接口）。
- 持久化行模型（`XxxObject: TableCodable`）的列定义本身（属 `external` 的表定义；repository 只声明转换映射）。

---

## 合同八问的类型特化

> 编号纪律：每个 repository 设计单元以 `### UNIT-<slug>`（kebab-case，如 `UNIT-story-repository`）为标题；承接的需求行为引用裸 token `BHV-NNN`（prd 标题）；下游（usecase）引用本单元写裸 `UNIT-<slug>` token。

1. **承接哪些行为**：数据读写、缓存、持久化、同步类 `BHV-NNN` 逐条引用（必须存在于 prd；幽灵引用与无承接行为均被 Gate 断链拦截）。每条行为映射到接口的一个 `func` 或一组 CRUD 方法。

2. **输入 / 输出 / 错误结果**：
   - **`IXxxRepository` 协议逐方法签名级**列出（方法名 / 参数（含 `criteria` 结构体字段、分页 `page`/`pageSize`）/ 返回类型 / `async throws`）。
   - **返回 Domain 实体或其值对象**（如 `Story` / `StorySummary`），**严禁把 WCDB Object（`StoryObject`/`StorySummaryObject`）或 DTO 泄漏给上层**——Object↔实体的 mapper 是本类责任，必须在合同声明（如 `StoryObject.from(story:)` / `object.toStory()`）。
   - **错误 = 底层异常到本域 `enum Error` 的映射表**（明细到 `WCDBError.code` 这一级）。证据可循：`StoryRepository.mapToRepositoryError(_:operation:)` 把 `WCDBError.code == .NotFound`（且 `operation == "findById"`）→ `PersistenceError.notFound`，`.Corrupt` → `.fetchFailed(reason: "数据库损坏")`，`.Constraint` → `.uniqueConstraintFailed(field:)`，并把基类 `ThreadSafeRepositoryError.validationFailed` → `.saveFailed(reason:)`。**映射表逐条可对应一条失败路径**。

3. **读取 / 写入哪些状态**：本 repository 拥有的持久化/缓存状态清单（哪些表、哪些索引、是否有派生摘要表如 `StorySummaryObject`）。写 owner 必须与概要归属一致（可回指归属表行）。**幂等性声明**：写方法的重复调用语义（如 WCDB `insertOrReplace` 为幂等 upsert；`delete(id:)` 重复调用对不存在记录为 no-op）。

4. **调用哪些依赖，不调用哪些依赖**（正反两面都写，违反 = P1）：
   - **允许注入**：`DatabaseManaging` / `EnhancedDatabaseManager`（持久化引擎，归 `external`）、`external` 侧外部来源接口（网络/SDK 适配）。
   - **禁止注入/调用**：`usecase`（反向依赖 = P1）、`viewmodel`、`view`、`coordinator`、**其他 repository**（跨聚合需求回概要重判边界，不在 repository 间横向调用）。
   - 协议本身（`IXxxRepository`）在 Domain，**零依赖**——只 import `Foundation`，不得 import WCDBSwift/FactoryKit/UIKit/SwiftUI。

5. **失败如何收口**：**错误转换位置必须显式且统一**——底层异常一律在 repository 实现内 `catch` 后经 `mapToRepositoryError(_:operation:)` 转成本域 `enum Error` 再 `throw`（不吞错、不返回空数组掩盖出错）。编排策略显式：多来源时（如先本地后远端）须写明回落/标记 stale/离线写入与冲突合并；纯本地持久化场景写明"无回落，失败直接上抛"。**事务边界**见下「类型硬规则」。

6. **产生哪些事件 / 后置结果**：数据变更通知方式逐条写明消费方。证据：`StoryRepository` 在 `save`/`delete` 成功后调用 `onAfterCURDOperation(.create/.delete, entity:)`（继承自 `ObservableRepository`），发射 CRUD 事件供上层订阅。若本 repository 不可观察，显式写"无事件，变更由 usecase 主动重查"。

7. **哪些测试验证它**：
   - 实体↔Object 转换、错误映射表 = unit test（XCTest，或 project-conventions 选定的 Quick/Nimble）逐条覆盖（每个 `WCDBError.code` 分支至少一条）。
   - CRUD/分页/计数/批量/事务原子性 = 集成测试（真实 WCDB，用 `DatabaseManager(databasePath:)` 自定义路径建临时库，测后 `clearDatabase()`）。
   - 事务原子性必须有专门用例：多表写中途失败 → 全部回滚（无半写）。

8. **哪些内容不得在此补造**：不实现业务规则（属 usecase）；不新增概要未定的表/索引/聚合（回概要技术决策承接）；不决定 UI 错误文案（属 viewmodel/view）；不在 repository 决定 WCDB 引擎参数（WAL/加密/连接池属 external 的 `DatabaseManager`）。

---

## 类型硬规则（golden-path 锁定，违反直接 fail）

- **接口在 Domain、实现在 Infrastructure**（分层硬基准）：
  - 协议 `IXxxRepository` 置于 `Domain/Repositories/`（证据：`Domain/Repositories/IStoryRepository.swift`）；实现 `XxxRepository` 置于 `Infrastructure/Persistence/Repositories/`（证据：`Infrastructure/Persistence/Repositories/StoryRepository.swift`）；**接口实现分文件**。
  - 依赖方向 Domain→App→Infrastructure→UI 单向；Domain 协议零依赖。

- **FactoryKit `@Injected` DI（禁手动初始化）**：repository 实现在 `Container+Infrastructure.swift` 以 `Factory<any IXxxRepository>` 注册（证据：`exportTaskRepository: Factory<any IExportTaskRepository> { self { ExportTaskRepository(databaseManager: self.enhancedDatabaseManager()) }.singleton }`）。上层（usecase）通过 `@Injected(\.xxxRepository)` 取用，**禁止在业务代码 `new`/直接 `init` repository**；其依赖（DatabaseManager）亦由 Container 注入。

- **WCDBSwift 持久化（禁 CoreData/SwiftData）**：实现 import `WCDBSwift`；持久化经 `Table<EntityObject>`（`EntityObject: TableCodable`）；查询用 WCDB `Expression`（项目内 `typealias WCDBExpression = WCDBSwift.Expression`）。**禁止**出现 `NSManagedObject`/`@Model`/CoreData/SwiftData。

- **`enum Error` 分层映射**：本域错误为独立 `enum`（如 `PersistenceError: Error, Equatable`，含 `saveFailed/fetchFailed/deleteFailed/notFound/underlyingError/uniqueConstraintFailed`）。底层异常（`WCDBError`、基类 `ThreadSafeRepositoryError`）一律映射为本域 `enum` 后上抛，**不把 WCDBError 直接抛给 usecase**。错误 `enum` 归属：repository 专用持久化错误可置于 Domain 协议同文件或 `Domain/Errors/`（证据：`Domain/Errors/StoryError.swift`），保持 Domain 零依赖。

- **事务边界（多写原子性强制）**：凡一个行为涉及**多于一个表/多条写**（主表 + 派生摘要表、批量、级联删除），必须包进**单一事务**。证据：`StoryRepository.save(story:)` 用 `performTransaction { table in try table.insertOrReplace(storyObject); try self.summaryTable.insertOrReplace(summaryObject) }`，确保主表与 `StorySummaryObject` 摘要表原子更新；`delete`/`deleteBatch`/`saveBatch` 同理。读多用 `performRead`（`.fast` config），单写用 `performWrite`，多写用 `performTransaction`（均由 `ThreadSafeRepository`/`EnhancedDatabaseManager` 提供，统一线程安全）。**合同必须逐方法标注用 read / write / transaction 哪一种**，并对 transaction 写明"中途失败全回滚"的不变量。

- **mapper 与校验归属**：实体↔Object 转换（`entityToObject`/`objectToEntity`）与写前 `validateEntity(_:)`（如 Story 标题非空、至少一章节）由实现声明；校验失败抛 `ThreadSafeRepositoryError.validationFailed` 再映射为本域错误。**结构性不变量校验属 domain-model；repository 只做持久化前的存储约束校验**，业务规则不在此。

- **`private` 方法在 `private extension`**（代码组织规范）：mapper 辅助、`buildSearchCondition`/`buildOrderBy`、`mapToRepositoryError` 等私有方法集中在 `private extension XxxRepository` 或 `// MARK: - 私有辅助方法` 段。

---

## 章节正文骨架对齐（本类填充要点）

> 完整骨架与「骨架↔八问映射」见 L1 §4；本类各节的填充重点如下，避免薄文档。

- **1 单元职责**：`UNIT-<slug>` 一句话职责 + 注入了谁（DatabaseManager / external 来源）+ 被谁调用（哪些 usecase）。
- **2 行为定义**：2.1 行为清单（行为名 + 简述 + `BHV-NNN`）；2.2 接口定义给 **Swift `protocol IXxxRepository` 签名级**（`func ... async throws -> ...`，禁超签名级实现）。
- **3 核心数据结构**：3.1 `criteria`/`summary` 等值对象（Swift `struct`/`enum` 签名级）；3.2 错误类型表（错误名 | 枚举 case | 语义 | 来源底层异常 | 转换位置）。
- **4 逐行为设计**：每方法一小节，含签名、承接 BHV、输入/输出表、执行流程（`mermaid sequenceDiagram`，参与者用真实组件名如 `StoryRepository`/`EnhancedDatabaseManager`/`summaryTable`，标注 read/write/transaction）、异常处理表（异常 | 处置 | 转换位置）。
- **5 状态管理**：表/索引清单 + 写 owner 声明 + 幂等性；非可观察 repository 写"无内存态，状态即持久化层"。
- **7 测试映射**：BHV/方法 → 测试层（unit/integration）+ 测试点（成功 + 全部失败路径）。
- **8 不得补造清单**：逐条列本单元不拥有的决策。

---

## 好 / 坏例子（要点）

✅ **好（对齐 `StoryRepository` 实测）**：
- 协议 `protocol IStoryRepository`（Domain，只 import `Foundation`）逐方法签名：`func save(story: Story) async throws`、`func findById(id: String) async throws -> Story?`、`func findAllSummaries(criteria: StorySearchCriteria?, page: Int, pageSize: Int) async throws -> [StorySummary]`、`func delete(id: String) async throws`、`func count(criteria: StorySearchCriteria?) async throws -> Int`。
- `save` 合同写明："经 `performTransaction` 原子写主表 `StoryObject` + 摘要表 `StorySummaryObject`，成功后 `onAfterCURDOperation(.create, entity:)` 发射事件；任一表写失败整体回滚。"
- 错误映射表逐条：`WCDBError.code == .Constraint` → `PersistenceError.uniqueConstraintFailed(field:)`；`.Corrupt` → `.fetchFailed(reason: "数据库损坏")`；`validationFailed` → `.saveFailed(reason:)`。
- 依赖声明："注入 `EnhancedDatabaseManager`（external）；不注入任何 usecase / 其他 repository。"
- DI：`Container+Infrastructure.swift` 注册 `storyRepository: Factory<any IStoryRepository>`，usecase 用 `@Injected` 取用。

❌ **坏**：
- 协议方法清单写「负责故事数据相关能力」——无签名、无 `async throws`、无 criteria 字段（八问 2 失败）。
- 在 Domain 协议文件 `import WCDBSwift`，或返回 `StoryObject` 给上层（破坏 Domain 零依赖 + 泄漏行模型 = P1）。
- 主表与摘要表分两次裸 `insertOrReplace` 不包事务（中途失败 → 数据半写不一致 = P1 违反事务边界）。
- `catch { return [] }` 吞掉 `WCDBError` 不区分"无数据"与"出错"（八问 5 失败）；或把 `WCDBError` 直接 `throw` 给 usecase（未做 `enum Error` 分层映射）。
- 业务代码里 `StoryRepository(databaseManager: DatabaseManager.shared)` 手动初始化（绕过 FactoryKit `@Injected` = P1）。
- 在 repository 里判"用户是否有权限保存故事"等业务规则（越权，属 usecase = P1）。

---

## 不适用场景（本类不承载）

- 纯内存/无持久化的临时状态：归 `viewmodel`（`@Published`）或 `usecase` 业务状态，不为其造 repository。
- 一次性外部能力调用（如调一次图像生成 SDK、发一次网络请求且无落库）：归 `external`，由 usecase 直接注入 `external` 接口，不强行包 repository。
- WCDB 表结构/迁移/引擎参数：归 `external`。

---

## Gate 判定（本类专用补充，叠加 L1 §7 G1~G7）

- **R1（分层归属）**：`IXxxRepository` 在 `Domain/Repositories/` 且零依赖（grep 协议文件无 `import WCDBSwift`/`FactoryKit`/`UIKit`/`SwiftUI`）；实现在 `Infrastructure/Persistence/Repositories/`，接口实现分文件。任一不符 = P1。
- **R2（DI 强制）**：实现以 `Factory<any IXxxRepository>` 注册于 Container，无业务侧手动 `init`。否则 = P1。
- **R3（错误分层）**：底层异常全部经 `mapToRepositoryError`/等价转换映射为本域 `enum Error` 上抛；错误映射表逐 `WCDBError.code` 分支可取证。缺映射/吞错 = P1。
- **R4（事务边界）**：多表/批量/级联写均标注并使用 `performTransaction`，合同含"全回滚"不变量与对应集成测试。多写未包事务 = P1。
- **R5（返回域模型）**：接口返回 Domain 实体/值对象，无 Object/DTO 泄漏，mapper 归属已声明。泄漏行模型 = P1。
- **R6（不越层）**：依赖正反面均写，无 usecase/其他 repository 注入；无业务规则补造。违反 = P1。
- **R7（持久化栈）**：实现用 WCDBSwift；无 CoreData/SwiftData/`@Model`/`NSManagedObject`。违反 = P1。
