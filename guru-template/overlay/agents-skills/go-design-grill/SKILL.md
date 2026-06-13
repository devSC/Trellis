---
name: go-design-grill
description: Go 后端 Gate 前拷问会话（grill-with-docs 的 guru-go 适配版）。对照本平台领域模型（golden-path 分层依赖律、project-conventions SLOT-01~SLOT-17、doc_type 七分类、既有 BHV/UNIT 编号）逐分支对抗式拷问 prd 或概要归属表：磨尖术语、压测边界/并发场景、与 safa-land 形态代码现状交叉核对、当场把决策固化进 prd/design/CONTEXT/ADR，并校验是否触碰平台三条最高禁令。运行位置：需求 Gate 前（拷问 prd.md）与概要 Gate 前（拷问 design §1 / design-main.md 归属表逐行核对）。触碰红线时当场 fail 回退，不放行进 Gate。不替代 trellis-brainstorm（探索生成）、go-design-*-writing（撰写）与 *-review（判定）。
---

# go-design-grill — Go 后端 Gate 前拷问

> 层级契约：拷问的对照基准是 `.trellis/spec/guides/golden-path.md`（分层依赖律 + 三条最高禁令 + 各层迷你路径）、`.trellis/spec/conventions/project-conventions.md`（SLOT-01~SLOT-17 槽位取值 + SLOT-17 存量违例清单）、`.trellis/spec/harness/overview/overview-structure-single-source.md`（归属判定方法 + doc_type 七分类）。本 SKILL.md 只编排拷问动作与处置规则，不复写规范正文；冲突时 golden-path 硬红线 > L1 章节合同 > project-conventions 槽位 > 本文件。

## 做什么

对当前 task 产物（`prd.md` 或 `design.md` §1 / `design-main.md` 归属表）发起不留情面的逐分支对抗式拷问，直到达成共识：沿设计树逐支走，决策间依赖逐个解开，每个归属判定都经得起"为什么属于它 / 为什么不属于别人 / 为什么独立存在"三问。**一次只问一个问题，每个问题附上你的推荐答案（含依据），等用户反馈再继续。** 能从代码（safa-land `services/<svc>/internal/*`）/spec（golden-path、project-conventions、harness L1）找到答案的问题不要问用户——先自己读取证实再说。

拷问的产物不是一份新文档，而是把磨出来的决策**当场固化**回既有产物：行为/范围 → `prd.md`；归属/owner → `design.md` §1 / `design-main.md` 归属表三问理由；纯术语 → 仓库 `CONTEXT.md`；难以回头的架构/契约权衡 → `docs/adr/`。

## 拷问对照物（领域模型，硬前置装载）

执行拷问前必须依次确认可读，任一缺失即停止并输出前置缺口（不得凭印象拷问）：

1. `.trellis/spec/guides/golden-path.md` — 分层依赖律（`transport → service → repository → domain` 单向无环）、三条最高禁令、各层迷你路径与禁止清单。拷问归属时这是判 owner 越界的唯一基准（"这条数据访问你打算让 handler 拥有？§2.1 不允许 transport 直 import repository 跑 SQL"）。
2. `.trellis/spec/conventions/project-conventions.md` — SLOT-01~SLOT-17 取值与 **SLOT-17 存量违例清单**。拷问时区分"硬规则（不可豁免）/槽位取值（项目级，改值需 ADR）/存量违例（触碰记债、新增阻塞）"三档（"你说新建 repository——SLOT-02 钉的是原生 SQL + `database/sql`，迁移落 `db/migrations/`，你这条走 ORM 了吗？"）。
3. `.trellis/spec/harness/overview/overview-structure-single-source.md` — 归属判定方法（§4）与 `detail_doc_type` 七分类（§6.1）。owner 四层只取 `transport/service/repository/domain`；横切（config/external/runtime）作为一等合同单独承接。
4. 当前任务既有产物：prd 的 `BHV-NNN` 行为集合、design §1 / `design-main.md` 归属表（拷问概要时逐行核对）、`task.json` 的 `guru_chain`（full/light，决定拷问 `design.md` §1 还是 `design-main.md`）。
5. 仓库根 `CONTEXT.md`（术语表，存在则装载；不存在时首个术语敲定时按 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) 创建）；`docs/adr/`（既有 ADR，存在则读最高编号，格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)）。

## doc_type 权威七类（拷问归属/承接时只用这七类）

`entry-api`（`internal/transport/http` handler 入口：路由/解码/鉴权门禁/ctx 透传/错误→HTTP 状态码）· `biz`（`internal/service` 业务核心：校验/编排/状态流转/sentinel error/终态收口，**核心能力主承接方**）· `repository-data`（`internal/repository` + `db/migrations`：SQL/行扫描/事务/`ErrNotFound` 转换/表迁移）· `domain`（`internal/domain` 实体/值对象/Params/sentinel/不变量，唯一可被跨层 import）· `config`（`internal/config` + `config.Load`：env 前缀/默认值/credential 引用策略，不写 secret value）· `external`（外部 API/对象存储/三方 provider 集成 + `packages/contracts` 跨服务契约）· `runtime`（`cmd/<svc>/main.go` + `app.New/Run/Shutdown` 生命周期/信号/优雅关闭/连接池）。**禁止串入他平台类型名**（如 `ui-widget`/`infrastructure`/`server-component` 等），出现即就地纠正回这七类。

## 会话期间

- **对照术语表挑战**：用语与 `CONTEXT.md` 既有定义冲突时立即点破——"术语表里 `User` 定义为代理用户（proxy user），你这条 BHV 里的『账号』指的是 `User` 还是 `ApplicationAccount`？safa-land 里 `users` 与 `application_accounts` 是两张表、两个概念。"
- **磨尖模糊语言**：出现含混/过载词汇时给出精确候选——"你说『同步配置』——是 `ConfigSyncService.TouchNodesForUser` 触发期望态重算，还是 proxy-agent 拉取 `packages/contracts/DesiredNodeConfig`？这是 service 编排副作用与跨服务契约两件事。"行为命名同步回写 `BHV-NNN` 标题短名（粒度对齐 L1 §3.1：动词+宾语、可直接实现、有失败路径）。
- **具体场景压测**：发明探边场景逼出概念边界与唯一写 owner——"两条 BHV 并发改同一 `users` 行的 status，谁是唯一写 owner？service 编排 + repository 落库，还是你打算让两个 handler 各写一次？"；"`POST` 创建后 `ConfigSyncService` 同步失败，事务回滚还是补偿？这条失败路径在 prd 里写了吗？"
- **与代码交叉核对（safa-land 形态）**：用户陈述与代码现状矛盾时当场摆出证据——"你说 not-found 走 `service.ErrNotFound`，但现状 canonical sentinel 是 `repository.ErrNotFound`（`internal/repository/errors.go`），且被 transport 直接 `errors.Is` 引用——这是 SLOT-17 第 1 条登记的存量违例。新代码按 SLOT-13 在 service 层定义 sentinel，你这条是新增还是触碰存量？"
- **决策当场固化（落盘，不口头停留）**：
  - 行为/范围/失败路径决策 → 立即更新 `prd.md`（未决问题 → 已决，附一句依据；保持 Given/When/Then + 失败路径 + 验收场景结构）；
  - 归属/owner/doc_type 决策 → 立即更新 `design.md` §1 / `design-main.md` 归属表的三问理由（owner 落四层之一，doc_type 落七类之一）；
  - 纯术语 → 更新仓库 `CONTEXT.md`（只做术语表，零实现细节，格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)）；
  - 项目级槽位取值变化（如要引入 `wire`/`sqlc`/`slog`、改 env 前缀、改鉴权方案）→ **不当场私改 project-conventions**，提示走槽位修订（需 ADR），并按下方 ADR 条件评估是否当场起草。
- **克制地提议 ADR**（三条全中才提，格式与编号见 [ADR-FORMAT.md](./ADR-FORMAT.md)）：难以回头 + 缺上下文会令未来读者困惑 + 真实权衡的产物。Go 后端典型可记 ADR：分层依赖律的刻意偏离及其代价、SLOT 级技术栈切换（无 DI→`wire`、原生 SQL→`sqlc`/`ent`、`log`→`slog`、REST→gRPC）、跨服务契约协议形态（`packages/contracts` 同步 JSON vs 事件）、鉴权方案（自实现 HMAC 签名 cookie vs 第三方 JWT 库）、数据归属边界（"`users` 由 control-api 拥有，proxy-agent 只经 contract 按 ID 引用"）。纯遵循 golden-path 默认路径、易回退的决策不记 ADR。

## 触碰红线 → 当场 fail 回退（处置规则）

拷问发现产物触碰下列任一**平台三条最高禁令 / 分层硬红线**时，立即判定本次拷问 **fail**，不放行进对应 Gate，输出"红线条目 + 证据锚点（BHV/UNIT/章节）+ 必须回退到哪个上游步骤修订"，并停止继续往下问，直到产物改正：

1. **轻框架锁定违反**：归属/承接里出现 gin/echo/fiber/chi 等替代 `net/http ServeMux` 的入口框架（golden-path §2.1 框架律）。
2. **分层依赖律违反**：把数据访问/SQL 归给 `entry-api`（handler）；让 `repository-data` 反向 import service；`biz`（service）承接里出现 `net/http`/`http.Request`/`http.ResponseWriter`；`domain` 承接里出现 import 本服务其它 internal 包；跨服务直接 import 另一服务 `internal/`（应走 `packages/contracts/`）；任意两 internal 包成 import 环（golden-path §2.1）。
3. **secret 字面量**：prd/design 里把真实密钥/口令/token/AK/SK 写成字面量，而非环境变量名引用（应经 `config.Load()` 装载，doc_type=`config`，credential 只写 `api_key_env_name`/`credential_ref`）。

附加 fail 触发（同样当场回退，不进 Gate）：

- **owner 越界但被包装成"新约定"**：用户想把存量违例（SLOT-17 已登记项，如 transport 直 import repository、handler 持 `*sql.DB`）当作新代码的合法模式扩散——明确区分"触碰存量记债"与"新增违例阻塞"，新增即 fail。
- **doc_type 串台**：归属/承接索引用了七类之外的类型名（他平台类型），就地纠正；拒不改正即 fail。
- **越界拍板**：把 project-conventions 的待定槽位或 `technology_decision_handoff` 里"未选定/needs_validation"的决策在拷问中私自写成"已选定"而无用户确认或 ADR——回退，要求走槽位修订/ADR 或标显式假设。

合规 STOP（与 workflow Guardrails 一致）：触及鉴权/会话/密钥/用户数据采集或任何法规/政策不确定性时，立即停止拷问，输出风险点 + 替代方案 + 人类确认清单，不替用户拍板。

## 边界（与官方/平台 skill 的职责切分）

- **不替代 `trellis-brainstorm`**：探索与初稿生成在前（1.1 light 链 prd 探索 / full 链正式需求由 `requirement-writing` 产出），本 skill 只对**已有草稿**做对抗式拷问，不从零生成需求。
- **不替代 `grill-with-docs`（官方）/ `trellis-check`**：本 skill 是 grill-with-docs 的 guru-go 适配版，把通用拷问绑定到 Go 分层依赖律、SLOT 槽位与 doc_type 七分类；不做官方 trellis-check 的实现期质检。
- **不替代 `go-design-overview-writing` / `go-design-detail-writing`**：撰写动作（章节合同、架构总览六件套、合同八问、承接索引）属 writing skill；本 skill 只拷问已写出的草稿并把决策回写，不代写章节正文。
- **不替代 `go-design-overview-review` / `go-design-detail-review`**：拷问出的修订落盘后，仍须走对应 review 给出"可进入下一阶段"的互斥 Gate 结论；本 skill 不出 Gate 判定，只在 Gate 前清障与红线拦截。本 skill 的 fail 是"拷问发现红线、回退修订"，不是 review 的正式 Gate 结论。
- **不进入实现细节**：方法签名、sentinel error 全集、SQL/DDL 正文、`config.Load()` 键表、env 取值、SDK 调用参数属详细设计/实现阶段领地（doc_type 承接），拷问不在此展开；只磨边界、语义、链路、取舍、归属、术语。
- **不私自拍板项目约定**：SLOT 取值变化、待定槽位收口须经用户确认 + ADR/槽位修订，本 skill 只提议不私改 `project-conventions.md`。
- **产物语言**：中文优先（代码标识符/命令/路径/协议字段如 `application_account_id`/库名 `net/http`/缩写 HMAC-SHA256/原文引用除外）。
