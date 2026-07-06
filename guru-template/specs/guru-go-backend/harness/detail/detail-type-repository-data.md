# L2 类型规范：repository-data（数据访问 + 持久化）

> 从属于 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；本文件只承载 `repository-data` 类型相对 L1 合同八问的差异规则与 Go 硬规则。
> 通用方法真源：`.trellis/spec/guides/golden-path.md`（分层依赖律、错误处理范式、各层迷你路径、禁止清单）。
> 项目级取值（DB 驱动、ORM/原生 SQL、迁移工具、日志、测试框架等槽位）：目标仓库 `.trellis/spec/conventions/project-conventions.md`。
> 层级契约：冲突时 golden-path > L1 > 本 L2 > references。本文件不得与上层冲突；命中冲突回上层修订，不在本类型就地补造。

---

## 0. 类型定位（强制）

`repository-data` 是**运行时数据访问组件**：把上层（service / biz behavior）声明的"业务为什么访问数据、访问哪些实体字段、如何判定成功失败"翻译成对持久化存储的具体读写，并把底层存储错误**映射**成上层可判定的错误契约。

定位边界（与相邻类型的红线）：

- **不是** `data-canonical`（数据主定义）。表结构、字段字典、DDL、Entity protobuf、索引/约束的**权威定义**归 `data-canonical`；本类型只**引用** canonical 的实体/字段/索引锚点，并声明针对它们的**访问合同**（查询口径、写入语义、事务边界、错误映射）。本类型正文不得重新发明字段集合或表结构。
- **不是** `service` / `biz-behavior`（业务规则）。本类型不做业务校验、不编排跨实体业务流程、不决定业务可恢复性策略；只提供"一次数据访问做对"的最小语义单元。
- **不是** `entry-api` / `entry-cli`（入口）。本类型不解析请求、不写 HTTP/CLI 状态码、不组装对外响应体。
- 本类型**拥有**：存储访问语义（SQL/查询口径绑定 canonical 索引）、行模型 ↔ 域模型的映射（mapper）、底层错误 → repository 哨兵错误的映射、单次数据访问的事务边界。

> 关键澄清（接口归属）：本类型的**数据访问接口（合同）**由其消费方（service / domain）拥有并定义；**实现**落在 `repository` 包。Go 惯例是"消费方定义接口"（consumer-defined interface），接口随消费者放在 service/domain 侧，实现的 struct 放在 `repository` 包。本文件统一表述为"接口在 domain 侧 / 实现在 repository 包"——此处 domain 侧泛指**消费该合同的领域代码所在层**（service 包内的窄接口，或 domain 包内的领域端口），与 golden-path §2.1 分层依赖律一致；实现 struct 永远在 `repository` 包，绝不外漏到 transport/service。

---

## 1. 需求五要素（本类型实例化时必填）

每个 `repository-data` 设计单元（`### UNIT-<slug>`）落地前，必须能从概要承接索引解析出以下五要素；任一缺失 → 回退概要补齐，禁止在详细阶段补造。

| 要素 | 内容 | 来源锚点 |
| --- | --- | --- |
| 触发场景 | 哪些上层行为需要这次数据访问（读/写/聚合/版本递增） | 概要第4章 Scenario/Flow + 第6章承接索引 |
| 数据 owner | 本访问读/写哪些实体，写 owner 与概要归属表一致 | 概要归属表 + `data-canonical` 实体锚点 |
| 输入/输出契约 | 方法签名级入参（域参数对象）与返回域模型 | 本单元接口定义 + canonical 字段锚点 |
| 失败语义 | 底层失败如何映射成 repository 哨兵错误并上抛 | golden-path 错误处理范式 + 本文件 §5 |
| 验证信号 | 每个方法的成功路径 + 全部失败路径的测试点 | 本单元测试映射 + 项目测试框架槽位 |

---

## 2. 概要归属表 + 承接索引（绑定）

本类型不自带归属判定；它**消费**概要产物，并必须在文档头声明双向绑定。

| 绑定项 | 强制写法 | Gate 校验点 |
| --- | --- | --- |
| 承接索引 | 文档头写 `承接索引：design-main.md 第7节 <chapter_target>`，且 `chapter_target → repository-data` 在概要承接索引中存在 | 索引↔chapter 文件双向闭合（L1 §7 G6） |
| 行为承接 | 每个 UNIT 八问之1 逐条引用 `BHV-NNN`（必须存在于 prd） | 断链/幽灵引用拦截（L1 §3、§7 G1） |
| 数据 owner 承接 | 每个写方法声明的写 owner 必须回指概要归属表对应行；引用 canonical 实体锚点 `<a id="dc-entity-...">` | owner 一致性（L1 §3 八问之3） |
| 技术决策承接 | 若概要 `technology_decision_handoff[]` 指向本 chapter（如 DB 驱动从 lib/pq 切 pgx、原生 SQL 切 sqlc），生成 `technology_decision_resolution[]`；未指向写 `N/A：no_technology_decision_target` | 未选定决策不得在详细拍板（L1 §6） |

承接索引示例（文档头）：

```markdown
# <chapter_target> 详细设计

> doc_type：repository-data ｜ l2_status：v1
> 承接索引：design-main.md 第7节 <chapter_target> ｜ 返回：[design-main](../design-main.md)
```

---

## 3. 合同八问的类型特化

每个 `### UNIT-<slug>` 必须完整回答以下八问（缺一即 P1）。括号内为可验证信号——审核按此取证。

1. **承接哪些行为**：逐条引用 `BHV-NNN`。每条行为映射到**一个**仓储方法（或一组协同方法）。读/写分别列：读行为 → 查询方法；写行为 → 写入/更新/删除方法；聚合/版本类行为 → 专门方法（如 `IncrementDesiredConfigVersions`）。（信号：每个方法旁标注承接的 BHV token，prd 中可定位。）

2. **输入 / 输出 / 错误结果**：
   - **接口逐方法签名级**列出：方法名、参数（统一 `ctx context.Context` 首参 + 域参数对象，如 `domain.CreateUserParams`）、返回类型（域模型 `*domain.X` / `[]domain.X` / `map[K]V` + `error`）。
   - **返回域模型，不外漏行模型 / DTO / 驱动类型**：`sql.NullString`、`sql.NullInt64`、`pq.Array`、`json.RawMessage` 等只能出现在仓储实现内部；跨边界一律转成域模型字段（`*string`、`*int64`、`[]string` 等）。mapper（scan + null 转换 + 反序列化）的归属必须在本单元显式声明。
   - **错误 = 底层错误 → 哨兵错误的映射表**（见 §5），逐行明细到 `sql.ErrNoRows → ErrNotFound` 这一级别。
   - 信号：接口签名表 + 输入参数表 + 输出表 + 错误映射表四表齐全。

3. **读取 / 写入哪些状态**：
   - 列出本仓储读/写的实体表清单（引用 canonical 锚点），读写分离。
   - 写方法声明**写 owner**，与概要归属一致；同一实体的写 owner 出现在两个仓储 = P1（回概要重判归属）。
   - **幂等性声明**：upsert（`ON CONFLICT ... DO UPDATE`）、按条件批量更新（如 `IncrementDesiredConfigVersions` 对空集返回 `nil`）、删除（重复删除的语义：第二次返回 `ErrNotFound` 还是幂等成功）必须逐方法写明。
   - 信号：实体读写矩阵 + 幂等性逐方法标注。

4. **调用哪些依赖，不调用哪些依赖**（正反两面）：
   - **调用**：仅注入持久化句柄/驱动抽象（如 `*sql.DB` 或事务执行器接口 `sqlExecutor`）；同包内私有 helper（scan、null 转换、`ensureRowsAffected`、`normalizeNodeIDs`）。
   - **不调用**（越层 = P1）：service / biz behavior（反向依赖）、transport/handler、其他 internal 包（除 domain）、其他 repository 的实现 struct（跨仓储依赖应由 service 编排，或在同仓储内私有方法组合，禁止仓储间横向 `import` 实现）。
   - 信号：依赖注入清单（构造函数入参） + 显式"不依赖"清单。

5. **失败如何收口**：
   - 每条失败路径的处置：底层错误**不吞**，必经映射后上抛（datasource/驱动层不静默吞错——通用硬规则）。
   - 错误转换位置固定在仓储方法内（`errors.Is(err, sql.ErrNoRows)` 分支、`ensureRowsAffected` 的 0 行判定、未来的 `pq.Error.Code` 唯一约束/外键冲突分支）。
   - 区分"无数据"（`ErrNotFound`）与"出错"（包装后的原始 error）：禁止 catch 后返回空切片/零值掩盖错误。
   - 信号：异常处理表逐行可对应一条失败路径 BHV 或八问之1 的行为分支。

6. **产生哪些事件 / 后置结果**：
   - 数据变更的后置语义：`RETURNING` 回填生成主键/时间戳后返回完整域模型；写后是否需要重读（如 `Create` 写入后调用 `GetByID` 组装关联数据）。
   - 跨实体版本/同步副作用是否由本仓储承担（如 `desired_config_version + 1`）还是由 service 编排——必须声明边界。
   - 信号：每个写方法的返回值/回填字段表 + 副作用归属声明。

7. **哪些测试验证它**：
   - 映射到测试分层：mapper（行 → 域模型 null/反序列化）= unit test；查询口径/索引命中/排序稳定性、写入幂等、错误映射 = 集成测试（真实 PostgreSQL，按项目测试框架槽位）。
   - 错误映射表**逐条**有用例（`sql.ErrNoRows → ErrNotFound`、0 行更新 → `ErrNotFound`、唯一冲突 → `ErrConflict`）。
   - 每条承接行为至少 1 成功 + 全部失败路径用例。
   - 信号：`BHV/方法 → 测试层 → 测试点`映射表，覆盖成功+失败。

8. **哪些内容不得在此补造**：
   - 不实现业务校验/业务可恢复性策略（属 service / biz）。
   - 不新增 canonical 未定义的表/列/索引（回 `data-canonical` 补，再回本类型引用）。
   - 不决定 HTTP/CLI 错误码与对外文案（属 entry 层）。
   - 不在未选定的技术决策上拍板（DB 驱动/ORM 切换回概要）。
   - 信号：不得补造清单逐条存在。

### 3.1 粒度标准（与 L1 §3.1 一致，本类型补充）

- **可直接实现**：每个方法的 SQL 访问意图、参数绑定、scan 目标、null/反序列化处理、错误映射分支都具体到开发者可直接编码。
- **明确调用关系**：每个方法写明调用了哪个私有 helper（`scanUser`、`ensureRowsAffected`、`decodeStringArray`）。
- **完整调用链**：组合方法（如 `Create → GetByID`、`GetDesiredConfig → getNodeMetadata + listEntryListeners + listDomainBlacklistRules`）必须可追踪到所有下级私有方法。
- **粒度一致**：同一仓储内所有方法描述粒度一致。

---

## 4. 类型硬规则（Go golden-path 锁定，不可豁免）

下列规则锁定为 golden-path，命中违反一律 P1。

### 4.1 接口在 domain 侧、实现在 repository 包

- 数据访问**合同（interface）**由消费方拥有：放在 service 包（消费方定义的窄接口，如 `userStore`）或 domain 包（领域端口）。**实现 struct**（如 `UserRepository`）放在 `internal/repository`，由 `New<X>Repository(db *sql.DB)` 构造，通过构造注入传给 service。
- 实现 struct 不得被 transport/handler 直接引用；handler → service → repository 严格单向（golden-path §2.1）。
- 接口只暴露域语义方法签名（域参数对象 + 域模型返回）；驱动类型不进接口签名。

### 4.2 原生 SQL / 迁移（当前 profile：lib/pq + PostgreSQL）

- 当前 profile 锁定**原生 SQL + `database/sql` + `lib/pq` + PostgreSQL**（项目约定槽位，可整体切 ent/sqlc/pgx——但切换是概要技术决策，不在详细拍板）。
- SQL 写法约束：
  - 一律 `QueryContext` / `QueryRowContext` / `ExecContext`（传 `ctx`，支持 timeout/取消）。
  - 参数化占位符 `$1...$N`，禁止字符串拼接 SQL（注入红线）。
  - 数组参数用 `pq.Array(...)` + `= ANY($1)`；JSONB 写入用 `$N::jsonb` 显式转换；`inet` 读出用 `host(...)`。
  - `rows` 必须 `defer rows.Close()`，循环后必须检查 `rows.Err()`。
  - 写入用 `RETURNING` 回填生成列（主键、`created_at`/`updated_at`），避免二次查询。
- **迁移**：表/列/索引/约束变更走 `db/migrations/<NNNN>_<slug>.up.sql` + 对应 `.down.sql`（成对、版本号递增）。迁移内容（DDL、enum type、索引、check/exclude 约束、trigger）的**权威定义在 `data-canonical`**；本类型只引用迁移版本号与受影响实体锚点，不在 repository 正文复写 DDL。迁移用 `BEGIN; ... COMMIT;` 包裹保证原子性。

### 4.3 错误映射（哨兵 + 包装 + `errors.Is`）

- 仓储包定义自己的哨兵错误（如 `repository.ErrNotFound`），底层错误必须映射后才跨边界：
  - `sql.ErrNoRows` → `ErrNotFound`（`QueryRowContext` + `Scan` 分支）。
  - `ExecContext` 后 0 行影响（按条件更新/删除目标不存在）→ `ErrNotFound`（`ensureRowsAffected` 统一收口）。
  - PostgreSQL 约束冲突：唯一约束（`pq.Error.Code == "23505"`）→ `ErrConflict`；外键约束（`"23503"`）→ `ErrReference`（按本仓储需要定义哨兵；当前 safa-land 仓储用 `ON CONFLICT DO UPDATE` 规避唯一冲突，新增冲突语义时按此映射）。
- 非哨兵的其它底层错误：用 `fmt.Errorf("%w: ...", err)` 或直接 `return ..., err` 上抛，**保留 `%w` 链**，禁止丢弃原始 error、禁止用空切片/零值掩盖。
- service 层用 `errors.Is(err, repository.ErrNotFound)` 判定并翻译成业务错误（如 `ErrValidation` / 404 语义）；repository **不**决定上层如何翻译。
- mapper（scan + null 转换 + 反序列化）失败（如 `json.Unmarshal` 出错）必须上抛，不静默成空值。

### 4.4 事务边界（显式且最小）

- **单条写入、只读校验、单语句条件更新**不开显式事务——交给数据库语句级原子性（`RETURNING`、`ON CONFLICT DO UPDATE`、`UPDATE ... WHERE`）。把它们机械包成 `BeginTx` 是反模式（P2）。
- **仅当**一个业务原子操作需要**多条写语句在同一 DB 连接内全成或全败**时，才开显式事务：`tx, err := db.BeginTx(ctx, nil)` → 各语句走 `tx.ExecContext` → 成功 `tx.Commit()`、失败 `defer` 中 `tx.Rollback()`。
- 事务边界必须落在**同一仓储方法内**（接收 `ctx` 控制 timeout）；禁止把 `*sql.Tx` 漏到 service/handler 让上层手动管理生命周期，也禁止把 `DB + 外部副作用（MQ/HTTP）` 硬塞进一个本地事务边界（外部副作用不是本地事务的一部分）。
- 多仓储参与同一事务时，用接收 `sqlExecutor`（`*sql.DB` 与 `*sql.Tx` 共同满足的 `ExecContext/QueryContext` 接口）的方法形态，由编排方传入 `tx`；不得让仓储间互相 `import` 实现。
- 跨实体一致性若不要求强原子（如 `desired_config_version` 递增是最终一致的同步信号），**不**强开事务，只声明顺序与幂等。

---

## 5. 错误映射表（强制结构）

每个 `repository-data` 单元必须给出错误映射表，逐行对应一条失败路径。模板：

| 底层错误/触发条件 | 映射结果 | 转换位置 | 上抛/收口 | 对应行为/BHV |
| --- | --- | --- | --- | --- |
| `sql.ErrNoRows`（QueryRow + Scan 无行） | `repository.ErrNotFound` | 方法内 `errors.Is` 分支 | 上抛 service | `BHV-<读>` |
| `ExecContext` RowsAffected == 0（条件更新/删除目标不存在） | `repository.ErrNotFound` | `ensureRowsAffected(result)` | 上抛 service | `BHV-<写>` |
| `pq.Error.Code == "23505"`（唯一约束冲突） | `repository.ErrConflict` | 方法内 `pq.Error` 类型断言 | 上抛 service | `BHV-<写>` |
| `pq.Error.Code == "23503"`（外键约束违反） | `repository.ErrReference` | 方法内 `pq.Error` 类型断言 | 上抛 service | `BHV-<写>` |
| `json.Unmarshal` / `decodeStringArray` 反序列化失败 | 原始 error（`%w` 包装） | mapper 内 | 上抛 service | `BHV-<读>` |
| 连接/查询级 IO 错误（其它 `err != nil`） | 原始 error（`%w` 包装） | 方法内 `if err != nil` | 上抛 service | 全部 |

> 收口口径：repository 只负责"识别 + 映射 + 上抛"；不重试（重试/降级策略属 service）、不写日志文案（结构化日志按项目日志槽位，由 service/transport 决定级别）、不静默吞错。

---

## 6. 实现 trace 计划合同与 mutable evidence（implementation-trace 承接）

进入编码后，本类型在 `.trellis/spec/harness/implementation/implementation-trace-contract.md` 约束下逐 UNIT 回填四节：

1. **接口 → 实现映射**：`UNIT-<slug>` 的接口方法 ↔ `internal/repository/<x>_repository.go` 的实现方法（文件:行）。声明消费方接口位置（service 包 `<x>Store` 或 domain 端口）。
2. **SQL → canonical 映射**：每个方法的 SQL 命中的表/列/索引 ↔ `data-canonical` 实体锚点 + 迁移版本号；查询口径 ↔ 索引名（如 `user_month_plans_user_starts_at_idx`）。
3. **错误映射 trace**：§5 表的每一行 ↔ 实现代码的映射分支（文件:行）；service 侧 `errors.Is` 翻译点。
4. **技术决策 trace**：若发生驱动/ORM 切换，回填 `retrieve_trace_id` / 选型来源 / 迁移命令（如 migrate 工具调用），说明原生 SQL 能力不足或切换理由。

---

## 7. 好 / 坏例子

### 7.1 ✅ 好例子（贴合 safa-land 实测）

接口（消费方在 service 包定义窄接口，golden-path §2.1）：

```go
// internal/service/user_service.go —— 消费方定义的数据访问合同
type userStore interface {
    GetByID(ctx context.Context, id int64) (*domain.User, error)
    Create(ctx context.Context, params domain.CreateUserParams) (*domain.User, error)
    UpdateStatus(ctx context.Context, id int64, status string) (*domain.User, error)
    Delete(ctx context.Context, id int64) error
}
```

实现（struct 在 repository 包，原生 SQL + 错误映射 + 域模型返回）：

```go
// internal/repository/user_repository.go
type UserRepository struct{ db *sql.DB }

func NewUserRepository(db *sql.DB) *UserRepository { return &UserRepository{db: db} }

func (r *UserRepository) GetByID(ctx context.Context, id int64) (*domain.User, error) {
    row := r.db.QueryRowContext(ctx, `SELECT ... FROM users WHERE id = $1`, id)
    user, err := scanUser(row)          // mapper：null 转换 + 反序列化在此收口
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, ErrNotFound      // 哨兵映射，区分"无数据"
        }
        return nil, err                  // 其它错误原样上抛，不掩盖
    }
    return &user, nil                    // 返回域模型，不外漏 sql.NullX
}
```

为什么是好例子：

- 合同写明每个方法"承接哪条读/写 BHV、返回哪个域模型、`sql.ErrNoRows → ErrNotFound`、0 行 `→ ErrNotFound`（`ensureRowsAffected`）"。
- 依赖仅 `*sql.DB` + 同包 helper；显式声明不依赖 service/transport/其它仓储实现。
- 写后用 `RETURNING` 回填，或 `Create → GetByID` 组装关联（`attachMonthPlans`），后置语义清晰。
- 幂等性显式：`UpsertSingleUpstreamForUser` 用 `ON CONFLICT (port_binding_id) DO UPDATE`；`IncrementDesiredConfigVersions` 对空集 `return nil`。
- 错误映射表逐条有集成测试用例。

### 7.2 ❌ 坏例子（命中红线）

- 「负责用户数据」——无方法签名、无 SQL 访问意图、无错误映射（八问之2/5 空缺，P1）。
- 接口返回 `*sql.Rows` / `sql.NullString` / `json.RawMessage` 给 service——行模型/驱动类型外漏（违反 §3 八问之2，P1）。
- `if errors.Is(err, sql.ErrNoRows) { return []domain.User{}, nil }`——把"无数据"与"出错"混为一谈，吞错（违反 §4.3/§5，P1）。
- `func GetByID(id int64)` 不接 `ctx`——无法 timeout/取消（违反 §4.2，P1）。
- `db.QueryContext(ctx, "SELECT ... WHERE name = '"+name+"'")`——字符串拼接 SQL，注入红线（P1）。
- 把单条 `UPDATE users SET status=$2 WHERE id=$1` 包进 `BeginTx/Commit`——无谓事务（违反 §4.4，P2）。
- 仓储 `import` 另一个仓储的实现 struct 做跨表写——仓储间横向依赖（应由 service 编排或同仓储私有方法组合，违反 §4.1/§4.4，P1）。
- repository 内 `errors.Is(err, ErrNotFound)` 后直接构造 HTTP 404 响应——越层决定对外协议（违反 §0/§3 八问之8，P1）。
- DDL 直接写在 `repository.go` 里建表——绕过 `db/migrations` 与 canonical（违反 §4.2，P1）。

---

## 8. 不适用场景（本类型不承载）

以下场景**不**用 `repository-data` 类型承载，命中即回对应类型：

- 纯表结构/字段字典/Entity protobuf/索引定义 → `data-canonical`。
- 业务校验、跨实体业务流程编排、可恢复性策略、事务跨多个聚合的业务原子性决策 → `service` / `biz-behavior`。
- 缓存层（内存/Redis）作为独立数据来源的编排 → 若引入，作为 datasource 切片由 service/repository 注入抽象，缓存过期/回落策略属编排合同，不在原生 SQL 仓储正文混写。
- 对外接口的请求解析、响应组装、HTTP/CLI 错误码 → `entry-api` / `entry-cli`。
- 三方存储/外部系统（对象存储、外部 API 持久化）→ `external-integration-contract`。
- 配置项/环境变量读取 → `config-runtime-contract`（仓储只消费已加载的 `*sql.DB`，不读 env）。

---

## 9. Gate 判定（结构检查可通过的最小条件）

`guru_gate.py` 结构检查与 L1 §7 完成判定对本类型的取证点：

- **G1 承接闭合**：承接索引每个 `repository-data` 条目有对应 UNIT，无遗漏；每个 UNIT 八问之1 的 `BHV-NNN` 在 prd 可定位（无断链/幽灵引用）。
- **G2 合同八问完整**：八问逐条有可验证信号；接口签名表 + 输入/输出表 + 错误映射表（§5）齐全；字段/方法可追溯到 canonical owner；满足 §3.1 粒度。
- **G3 测试映射**：每个方法有测试映射，覆盖成功路径 + 全部失败路径；错误映射表逐行有用例。
- **G4 红线无违反**：无字符串拼接 SQL、无驱动类型外漏、无吞错、无越层、无无谓事务、无 DDL 内联（§4/§7.2 红线清单）。
- **G5 不得补造清单**：八问之8 逐 UNIT 存在。
- **G6 章节闭合**（full 链）：索引 ↔ `chapters/<slug>.md` 双向闭合；本章符合 L1 §4 骨架；`repository-data` 在 v1 提供 L2，不需 L2 豁免声明。
- **G7 实现 trace 就位**（进入编码后）：§6 四节可回填，接口↔实现、SQL↔canonical、错误映射↔代码分支可定位。

判定形态：前置（承接索引/技术决策选定）失败 → 只输出前置缺口并回退概要；前置通过 → findings（带 UNIT/章节锚点 + P1/P2/P3 分级）+ 三选一结论（可进入编码 / 带假设可进入 / 不可进入）。
