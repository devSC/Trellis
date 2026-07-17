---
name: go-implementation-guru-review
description: 按通用 golden-path 与实现 trace 合同审核 Go monorepo 后端代码改动，判定能否进入 PR。核查与详细设计单元（UNIT-<slug>）合同八问的一致性、分层依赖律（transport→service→repository→domain 单向无环）与轻框架/错误链/生命周期 canonical、验证证据（go build/vet/golangci-lint/test）完整性、注释/日志/文档路径追溯、Secret/Config 合规红线，并执行存量豁免判定（SLOT-17 内记债不阻塞、清单外新增违例阻塞）。标准口径住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`，本 skill 只审核取证、不重定义规则。
---

# Go 实现审核

> 用于用户要求「审核 Go 后端实现是否对齐详细设计」「检查代码是否按详细设计落地」「实现阶段门禁审核」「review backend implementation」时。
> 本 skill 只做审核与取证，不默认改代码。若用户要求「审核并修复」，先输出 Findings，再按用户确认或明确指令进入修复。
> 平台形态：Go monorepo，服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，入口 `cmd/<svc>/main.go`，跨服务契约 `packages/contracts/`。

## 装载顺序（硬前置，任一失败即终止并仅输出前置缺口）

1. 必须先读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（编码规则与判定基准唯一来源：分层依赖律、各层迷你路径、错误处理范式、启动/关闭契约、禁止清单）。不可用 → 终止并提示先安装 guru go-backend spec 模板。
2. 读取同级标准包 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（实现 trace 过程合同 + 实现 Gate G1~G6 口径）与 `.trellis/spec/harness/index.md`（编号纪律 BHV/UNIT、Gate 4 脚本判定项、统一红线）。
3. 读取目标仓库 `.trellis/spec/conventions/project-conventions.md`，先跑校验清单 C1~C5；**重点装载 SLOT-17 存量违例清单**（存量豁免判定的唯一数据源）与本服务的 SLOT-01~SLOT-16 取值（DI/ORM/日志/测试框架/API 风格/DB 驱动/lint/配置/文档生成/会话鉴权/分层目录/迁移/错误风格/生命周期/接口抽象/枚举表达），并确认项目 logger / logging helper / 日志门面和字段约定。槽位缺失或待定超限 → 前置失败。
4. 定位审核对象：被审改动（diff/分支）、本任务承接的详细设计单元（full 链 `design_package/chapters/*.md` 的 `UNIT-<slug>`；light 链 `design.md` §详细）、`implement.md`（digest-bearing trace 计划合同）与 task-local mutable evidence（`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`）。trace 缺失或 mutable evidence 缺执行/验证记录 → 前置失败（实现 Gate 证据链不存在，不进入符合性判断）。
5. 命中需要项目级取值才能判定的项（如 lint 是否真按 `golangci-lint` 跑、DB 驱动是否落在 repository/app 层、会话鉴权是否 HMAC-SHA256 签名 cookie + bcrypt），其取值只能来自 project-conventions 槽位与仓库真实代码，不得从详细设计正文或参考工程习惯推断。
6. **装载 slice packet / invariant matrix**（P1，high-risk slice 必做）：supervisor 经 `build_run_plan` 把 resolved `slice_packet=<path>` 注入为 `--file`，brief 含 `active_slice=<slice_id>`。以 resolved `slice_packet` 路径为准读取 packet 的 `review_evidence_schema_version`、`requirements_design_inputs`、`invariants[]`（唯一机器 SSOT）、`target_paths`、`deterministic_checks`、`semantic_review_provider` 与 `integration_slice`。packet/matrix 缺失而 brief 标记 high-risk → 输出 `DETAIL_DEFECT` / `PROCESS_DEFECT`，不得 clean。

前置全部通过后，才进入下面的执行流程。

## Full/high snapshot 与 evidence Gate

- 先审核 `implement.md` 的 slice planning audit：普通 slice 是否以最少 commit-stable slices 和最大安全并发宽度为目标，是否登记唯一文件级 mutable owner、`covered_units`、真实 `depends_on`、parallel wave、独立 commit/rollback 价值、资源隔离、focused checks 与 reviewer context。仅因 UNIT 或 internal layer 整齐而机械拆片，按 `DETAIL_DEFECT` 阻断；一个 slice 覆盖多个合法 layer 本身不是缺陷，每个文件仍须遵守 Go owner 与单向 import。
- 一个 current snapshot 恰好由一个 semantic reviewer 负责。snapshot 绑定 target bytes、`invariants`、`requirements_design_inputs`、`deterministic_checks`、review policy / `semantic_review_provider` 与 supervisor digest；同一 snapshot 不得启动第二 reviewer 或重新 aggregate。
- clean evidence 只有在 `review_evidence_schema_version=2` 且上述每个绑定组件逐项相等时才能复用。snapshot 改变后可产生一个新 current review；v1、缺组件或部分相等的 evidence 不得复用。
- finding 只使绑定组件实际变化的 receipt 失效，不自动保留或作废所有 sibling receipts。已有 current receipt 的 slice 不得再次 aggregate；未变化的 current receipts 保持可复用。
- 普通 slice 只审 packet、planning audit、目标 diff、选定 requirements/design 与 focused evidence，只消费或执行 ordinary focused checks；不得运行 full regression。Integration 才审最终 union snapshot、ordinary current receipts、cross-slice invariants 与 final deterministic summaries，且 full regression 只属于 Integration deterministic checks。
- 最终语义/静态证据必须检查 workflow 实际派发的 Implementation writer Skill 及其引用的 implementation standards；仅 Planner、Detail 或 reviewer parity 一致不足以满足 Integration。若任一 active Full/high ordinary consumer 仍要求 project/global build、analyze、lint 或 full regression command，或仍按 UNIT、layer、`doc_type`、ViewModel、UseCase 或 component 机械重切片，按 `IMPLEMENT_DEFECT` 阻断。
- Integration packet `target_paths` 是 review coverage，不是写授权。实际改动路径必须是 planning audit 中 exact `integration_owned_paths` 的子集；即使路径位于 packet coverage 内，只要不在 `integration_owned_paths` 也按 `PROCESS_DEFECT` 阻断。reviewer 只读，不派 implement worker、不改 planning artifact、不直接写 receipt，也不重复执行 supervisor 已运行的同一 deterministic command。

## 执行流程（D 步骤诊断）

> 审核范围先规范化为 `BHV-NNN/UNIT-<slug> → detail_doc_type → 详细设计单元 → code_asset`；目标集合来自概要承接索引与本任务计划，不得按代码文件名反推 `UNIT-<slug>`。

1. **D1 合同一致性 / 八问闭合**（对应 Gate 4 切片挂 UNIT + Gate 3 八问骨架）：diff 与详细设计单元逐一对照——
   - 承接行为（八问①）：每个改动切片是否回指真实 `BHV-NNN`/`UNIT-<slug>`；引用了 prd 不存在的 `BHV-NNN`（幽灵行为）或详细设计不存在的 `UNIT-<slug>`（幽灵单元）= 断链，P1。
   - 输入/输出/错误（八问②）：函数签名、`domain` 结构体（如 `CreateUserParams`）、错误枚举与 sentinel error 表是否与代码一致；合同外新增的导出结构/方法、未实现的承接行为，列差集。
   - 状态读写（八问③）：写 owner（DB 行 / 会话态）与概要归属是否一致，是否出现归属外的写。
   - 依赖出入边（八问④）：`service` 调 `repository` 不反向、`handler` 不直连 DB——见 D2。
   - 失败收口（八问⑤）：见 D2 错误契约。
   - 事件/后置（八问⑥）：config 同步触发、审计、副作用是否落地或显式声明无。
   - 测试映射（八问⑦）：见 D4。
   - 不得补造（八问⑧）：实现是否猜测/发明了详细设计未定义的合同（如 handler 擅自决定 SQL、service 擅自决定路由）= P1。
   - `implementation-evidence.jsonl` 是否记录与计划的偏差与处置；上游合同错漏是否回退详细阶段修订而非就地改设计（八问缺错误枚举、签名与 domain 不符、测试映射漏失败路径 → 应回退，并在 mutable evidence 留回退记录）。
   - **slice packet / invariant 核查（P1 high-risk slice 必做）**：有 packet 时，diff 必须与 packet `invariants[]` 逐条对照，每条输出 `invariant_status.<id>=pass|fail|not_applicable`；`pass` 必附证据，`not_applicable` 必附理由。invariant 违反按其 `route_if_missing` / `IMPLEMENT_DEFECT` 路由。注入的正式 requirement/design 包与 packet invariants 是行级权威基线；任何 reviewer 建议（含自身判断或外部审查器如 OCR）与 SSOT 行级约束冲突时一律否决、不得采纳。

2. **D2 分层依赖律与 canonical**（对应 golden-path 锁定项 + Gate 4 G5 + 统一红线，逐项检查改动代码）：
   - **import 方向**：`transport(handler) → service → repository → domain` 严格单向无环；除 `domain` 外不跨 `internal` 包互相导入；`repository` 反向 import `service`、`handler` 直接 import `repository`/驱动跳过 service = P1。
   - **轻框架锁定**：路由必须是 `net/http` `ServeMux`；新引入 `gin`/`echo` 等重型框架 = P1（红线，不可豁免）。
   - **错误处理范式**：服务级 sentinel errors + `fmt.Errorf("%w: ...")` 链式包装 + `errors.Is()` 检查；丢 `%w`（`fmt.Errorf("...: " + err.Error())` 拼接）、`_ = err` 吞错、裸字符串比较错误、`panic` 作控制流 = P1（破坏 `errors.Is` 链）。错误→HTTP 状态码映射须在 `transport` 层用 `errors.Is()` 完成（SLOT-13）。
   - **启动/关闭生命周期**：`main()` 控信号（`SIGINT`/`SIGTERM`）→ `app.New()` → `app.Run()` → `app.Shutdown(ctx)`；handler 接收 `context.Context` 并尊重 deadline；优雅关闭幂等。触碰这些跨切片共享面（`app.go`/`main.go`）须 trace 单独标注。
   - **配置律**：连接串/池参数/密钥引用集中经 `config.Load()`；其它层读 `os.Getenv` = 违例。env 前缀须区分服务（如 `<SVC>_*`）。
   - **隐私与契约边界**：`internal/` 隐私不被跨服务 import；跨服务数据结构只走 `packages/contracts/`，契约变更须排在所有消费方编译面之前。
   - **DB 句柄边界**：`*sql.DB`/驱动 import 只允许出现在 `repository`/`app` 层（SLOT-02/SLOT-06）；service 直接持有连接 = 违例。

3. **D3 存量豁免判定**（逐违例必做，对应 Gate 5）：D1/D2 发现的每个违例对照 SLOT-17 清单——
   - **命中清单且未扩大违例面** → tech-debt 注记，**不阻塞**（标注关联 `[SLOT-NN]` 编号与计划处置）。
   - **清单外，或扩大了违例面** → **新增违例，P1 阻塞**（例：新代码绕过 service 让 handler 直连 DB、新增 gin/echo 依赖、新写 secret 字面量、新加跨层反向 import）。
   - **改动修复了清单条目** → 标注「可从 SLOT-17 移除」并指明被修复的违例。
   - 触碰存量但绕行（不修）须在 `implementation-evidence.jsonl` 写「为何不修」并挂 `[SLOT-NN]`；混入业务 diff 而不挂编号 = P2 起步。

4. **D4 证据核查**（对应 Gate 4 G2/G3/G4 + `verification-evidence.jsonl`，强调「证据感而非做完感」）：
   - **计划合同与 mutable evidence 齐全且非空**：`implement.md` 计划节有 `UNIT-<slug>` 承接与完成信号；`implementation-evidence.jsonl` 有改动清单、偏差说明和阻塞/恢复记录；`verification-evidence.jsonl` 有命令级记录。缺任一证据链 = 实现 Gate 不放行（P1）。
   - **编译证据**（G2）：Full/high ordinary slice 只要求 packet 声明的 focused build（例如 `go build ./services/<svc>/...` 或 exact package path）并贴命令 + 退出态；`go build ./...` 只由 Integration 承担。非 Full/high 任务继续按原 route 合同取证。只写「通过」无命令/退出态 = 证据不可信（P2 起步）。引入的失败未收口 = P1。
   - **静态检查证据**（G3）：Full/high ordinary slice 只要求 packet 声明的 affected service/package `go vet` 与 `golangci-lint` focused commands；`go vet ./...`、`golangci-lint run ./...` 只由 Integration 承担。非 Full/high 任务继续按原 route 合同取证。逐条记录通过/失败 + 处理；`nolint` 豁免须写理由并指向 `[SLOT-17]`。
   - **测试证据**（G4）：测试名级别结果（如 `--- PASS: TestUserService_Login/bad_credential`），不只写「全部通过」；覆盖承接 UNIT/BHV 的成功路径 + **全部失败路径**；新增测试清单可追溯到 `UNIT-<slug>`/`BHV-NNN`。漏失败路径用例 = P2 起步；高风险链路（鉴权/迁移/契约/并发超时）漏测 = P1。竞态敏感切片应附 `go test -race`。
   - **invariant 证据**（P1 high-risk slice）：每条 high-risk invariant 至少一个正向或负向测试、命令或代码路径作为 `invariant_evidence`；`pass` 无证据按 `invariant_coverage=missing` 阻断。负向语义（排除/遗漏/不得绕过鉴权/不得破坏错误链或迁移兼容）缺测试或等价确定性检查按 P1/P2 判级。
   - **可复现抽查**：核对至少 1 条 `verification-evidence.jsonl` 命令的当前输入与输出证据；不得重复执行 supervisor 已运行的同一 deterministic command。需要额外语义取证时只跑未重复的 ordinary focused check；证据与当前 snapshot 不符 = 证据造假（P1）。
   - **代码生成执行记录**：启用了生成型槽位（wire DI / sqlc / ent / mockgen / stringer 等，依 project-conventions 选型）且触发条件满足时，须有生成命令与产物清单记录（如 `wire_gen.go`/`db/*.sql.go` 是否变更）；当前 golden-path 默认无代码生成（原生 SQL + 标准库）则 `implementation-evidence.jsonl` 须写「N/A：无代码生成槽位启用」，不得留空。
   - **依赖整洁**：`go.mod`/`go.sum` 变更须 `go mod tidy` 并记 diff；新增第三方库须落在 project-conventions 已批准槽位（禁被锁框架）。
   - **未验证项**：无法本地验证的（真实 PostgreSQL 集成、生产负载下 `context` 超时与连接池、跨服务契约在另一服务的运行时兼容、信号驱动优雅关闭实测）须显式列出并指明移交环节（CI 集成 / 压测灰度 / Manual QA staging），不得隐瞒。

5. **D5 注释/日志/文档追溯核查**（维护性证据）：检查实现是否能让后续维护者从代码回到设计决策，并能在生产问题中定位关键路径。
   - 新增核心类型、导出函数/方法、transport handler、service、repository、domain model、config/app 生命周期入口、`packages/contracts/` 契约结构，必须有 Go doc comment 或等价注释说明职责、承接的 `UNIT-<slug>` / `BHV-NNN`；必要时附设计文档相对路径（`docs/design/.../chapters/<slug>.md` 或任务内 `design.md` 锚点）。缺失通常为 P2；高风险链路或新增核心 owner 完全无追溯为 P1。
   - 非显然业务分支、事务/迁移、错误转换与 sentinel 映射、降级/恢复、并发同步、`context` timeout/cancel、生命周期启动/关闭、外部依赖边界必须解释"为什么这样做"，不能只靠代码形状猜意图。缺失按 P2 处理。
   - 关键流程日志应覆盖入口、成功收口、失败/降级、重试/恢复、外部依赖边界、生命周期启动/关闭；必须复用 project-conventions 日志槽位选型或项目日志门面。散落 `fmt.Println`、无上下文 `log.Printf`、吞错无日志、外部依赖失败无上下文日志按 P2 起步，高风险不可观测路径按 P1。
   - 日志不得记录 secret、token、PII、完整请求体、密码明文或用户生成内容原文；命中即 P1。
   - `implementation-evidence.jsonl` / `verification-evidence.jsonl` 应记录本次新增注释、日志、文档路径引用与无法覆盖的理由；缺记录为 P3，若导致审计不可复现为 P2。

6. **D6 合规红线 / Secret 合规**（对应 Gate 4 config/secret 合规 + 统一红线）：
   - **密钥落地**：代码、config 结构、yaml、fixtures、测试资产、trace/mutable evidence 不得出现真实 API key、长期 AK/SK、token、password、盐等 `secret_value`；只允许保存环境变量名引用（如 `api_key_env_name`）、`credential_ref`、role/profile 引用等非敏感配置。硬编码 secret = P1。
   - **会话鉴权**（SLOT-10）：鉴权逻辑须收敛在 `internal/auth` 并经 `transport` middleware 注入，service/repository/domain 不感知 cookie/header；密钥来自 `config`，禁硬编码密钥/盐；HMAC-SHA256 签名 cookie + bcrypt 的签发/校验/过期是否与设计一致。
   - **`.env` 不作线上合同**：`.env` 仅本地开发引导，不得当生产配置合同。
   - **迁移合规**（SLOT-12）：迁移版本号单调递增、up/down 成对、不修改已应用的历史迁移；改 schema 一律追加新版本。
   - 红线违例（轻框架破坏 / 分层反向 / 丢 `%w` / 生命周期破坏 / 配置不集中 / internal 越界 / 契约不走 contracts / gofmt-goimports 未过 / 硬编码 secret）在对应判定直接 fail，不可豁免。

7. **D7 偏差闭合**（对应 Gate 4 G6）：PR diff 与计划逐项可对；所有计划外改动均有原因记录；上游结构性缺陷（归属错、合同越界、单元跟随名词而非行为）已回退拥有该决策的阶段修订而非就地补造。对不上靠 reviewer 自己发现 = P2 起步；就地改设计 = P1。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口（缺哪个装载源 / 槽位 / trace / 详细设计单元）+ 最小修复动作；不进入任何符合性判断，不给结论 pass/fail。

**前置通过时**，按以下顺序输出：

0. **机器可读收口字段（必须置顶）**：
   - 机器 verdict 第一段只能逐行输出以下 7 个字段；等号右侧只能是单个合法值，不得附加解释、分号摘要、斜杠组合值或 Markdown：
     ```text
     review_result=clean
     route_class=none
     review_target=slice:<slice_id>
     review_provider=<本 check worker 的 provider>
     deterministic_checks=passed
     dirty_scope=isolated
     invariant_coverage=all_passed
     ```
   - clean 分支固定使用 `review_result=clean`，不得输出 `final-verification-ready` 或 `clean/final-verification-ready`。有 finding 或阻塞时只把 `review_result` 改为 `findings` 或 `blocked`，并把 `route_class` 改为单个最高优先级 defect 枚举；其余字段仍各占一行且只含单值。
   - 有 slice packet 时紧接 7 字段逐条输出 `invariant_status.<id>=pass|fail|not_applicable`；`pass` 必随单行 `invariant_evidence.<id>=<非空证据>`，`not_applicable` 必随单行 `invariant_reason.<id>=<理由>`。无 findings 时另起一行输出 `findings=none`；摘要放在 verdict block 之后，不得拼入 7 字段取值。
   - 不运行开放式再发现 probe，不输出 multiline probe。确有必要补充 supervisor deterministic evidence 之外的只读检查时，只允许单行、单命令、边界明确的 `reviewer_probe_command.N=<exact command>`；不得重复 packet command。
   - 缺任一 gating 字段、取值带解释或组合值、取非通过值却声明 clean、或 provider 不满足 packet `semantic_review_provider`，supervisor 均按 `MALFORMED_REVIEW_OUTPUT` 阻断。
   - route class 只能取：`IMPLEMENT_DEFECT`（代码/测试/验证/注释/日志/脱敏缺陷）、`PROCESS_DEFECT`（trace/证据/流程执行缺陷）、`DETAIL_DEFECT`（详细设计合同错误或缺失）、`OVERVIEW_DEFECT`（概要归属/承接错误）、`REQ_BLOCKER`（需求行为/验收/边界缺陷）、`none`。

1. **结论（三选一）**：
   - **可进入 PR**：D1~D7 全过；`implement.md` 计划合同齐全，mutable evidence 中当前 route/slice 类型要求的 `go build`/`go vet`/`golangci-lint`/`go test` 证据有命令级结果且全绿（Full/high ordinary 仅 packet focused checks，Integration 才含 full regression）、承接 UNIT 的成功 + 全部失败路径有测试、注释/日志/文档路径追溯可审计、无 P1、无清单外新增违例、无未闭合偏差。
   - **修复 P2 后可进入**：无 P1，但存在 P2（证据不完整、偏差未全闭合、非高风险漏测、绕行未挂编号等）；列出 P2 修复项。
   - **不可进入 PR**：存在任一 P1（合同未实现 / 八问断链 / 分层反向 / 轻框架破坏 / 丢 `%w` / 生命周期破坏 / 硬编码 secret / 清单外新增违例 / 高风险漏测 / 编译未收口 / 证据造假 / 就地改设计）；逐条列阻塞 P1。验证因环境/凭据/DB/网络阻塞无法完成时，结论为 blocked，记录命令、错误摘要、缺失依赖与恢复条件，不得降级为 pass。

2. **逐条 Findings**（按 `P1 → P2 → P3` 排序；无则写 `none`），每条字段：
   ```md
   ### P<1|2|3> <标题>
   - route_class：`IMPLEMENT_DEFECT|PROCESS_DEFECT|DETAIL_DEFECT|OVERVIEW_DEFECT|REQ_BLOCKER`
   - 设计证据：`<UNIT-<slug>#八问几 / BHV-NNN / 详细设计文件:章节>`
   - 代码证据：`<services/<svc>/internal/<layer>/<file>:行 / 类型 / 方法 / app 装配 / config / 验证位置>`
   - 存量证据：`<命中的 [SLOT-NN] 条目 / 清单外；不适用写 N/A>`
   - 问题：`<代码与详细设计或 golden-path 红线的具体偏离>`
   - 影响：`<为何导致合同不闭合 / 验证不可信 / 红线破坏 / 无法判断>`
   - 建议（最小修订）：`<修代码 | 补/复跑验证 | 移除越界测试 | 回退详细阶段修订 | 挂 SLOT-17 记债 | 恢复验证环境>`
   ```
   同一轮多类缺陷按 `REQ_BLOCKER > OVERVIEW_DEFECT > DETAIL_DEFECT > PROCESS_DEFECT > IMPLEMENT_DEFECT` 给最高优先级路由，供 implement-check 自动回退。
   先证据后结论，严重度排序：
   - **P1**：合同未实现 / 执行流程步骤缺失·改序·下沉·上移无设计依据 / 八问断链（幽灵 BHV·UNIT）/ 实现阶段猜测发明未定义合同 / high-risk slice 缺 packet 或 invariant 失败 / 分层反向·越层 / 轻框架破坏 / 错误链丢 `%w`·吞错·panic 控制流 / 生命周期·context·优雅关闭破坏 / 配置不集中 / internal 越界 / 契约不走 `packages/contracts/` / 高风险核心 owner 完全无文档追溯 / 高风险路径不可观测 / 日志泄露 secret 或 PII / 硬编码 secret 或 config 存 secret value / 清单外新增违例（含扩大违例面）/ 高风险链路漏测 / 编译未收口 / 证据与复跑不符 / 就地改设计而非回退。
   - **P2**：编译/静态/测试证据不完整（无命令·无退出态·无测试名）/ 非高风险失败路径漏测 / invariant 证据字段不完整但未影响 high-risk 阻断语义 / 新增核心定义缺 Go doc 或设计锚点 / 非显然分支缺"为什么"注释 / 关键流程日志缺入口或失败上下文 / 偏差未全闭合靠 reviewer 发现 / 触碰存量绕行未挂编号 / 计划与验证命令轻微不一致但未绕过实现 / 因环境阻塞验证未完成。
   - **P3**：命名、包/文件组织、注释措辞、验证记录可读性问题，不影响合同闭合与红线。

3. **存量豁免清单**：本次触碰的 SLOT-17 条目 + 分类结果（记债不阻塞 / 新增阻塞 / 可移除）+ 对应 `[SLOT-NN]` 编号。

4. **注释/日志/文档追溯摘要**：覆盖的新增核心定义、日志点、设计文档路径引用，以及缺口和判级。

5. **验证命令汇总**：每条 `command / status(passed|failed|not_run|blocked_by_environment) / evidence(输出摘要或日志) / blocker`。未执行或环境阻塞的验证、失败的必要命令均不得支撑「可进入 PR」。

6. **反哺建议（可选）**：本次暴露的新模式/新坑 → 建议更新 golden-path、harness 标准包或 project-conventions 槽位定义的具体条目（如新增 SLOT-17 记债项、补 golden-path 禁止清单条目）。

## 好例 / 坏例（审核判读对照）

- ✅ 合格 ordinary 切片（放行）：`切片 S2 | 承接 UNIT-user-repository | repository/user_repository.go + db/migrations/0003_users.up.sql`；`verification-evidence.jsonl` 记录 packet focused checks：`go build ./services/<svc>/... → 退出 0`、`golangci-lint run ./services/<svc>/internal/repository/... → 0 issues`、`go test -run TestUserRepository_FindByEmail -v` 含 `not_found_maps_ErrUserNotFound` 子测试，新增测试映射到 `UNIT-user-repository` 覆盖 `BHV-012` 成功 + 失败路径；全仓库 regression 留给 Integration，真实 PG 唯一约束显式留 CI 集成。审核判：可进入 PR。
- ❌ 坏例（不可进入）：handler 内直接 `db.QueryRowContext(...)` 跳过 service 层（D2 分层反向，P1）；service 用 `fmt.Errorf("login failed: " + err.Error())` 拼接丢 `%w`（D2 错误链断裂，P1）；mutable evidence 只写「全部编译通过，测试通过」无命令无测试名（D4，P2）；新引入 `github.com/gin-gonic/gin`（D2 轻框架红线，P1）。
- ❌ 坏例（八问断链）：切片挂 `UNIT-user-cache` 但详细设计无此单元（幽灵单元，P1）；或 `BHV-012` 在概要有 owner 但无任何 `UNIT-<slug>` 承接（断链，P1）。

## 边界约束

- 只审改动面 + 其直接依赖；不对存量代码做全量审计（存量违例只走 SLOT-17 豁免判定）。
- 审核不代写代码；每条 finding 给最小修订方案。
- 规则正文不在本 skill 复写——分层依赖律、迷你路径、禁止清单以 `.trellis/spec/guides/golden-path.md` 为准；trace 计划合同、mutable evidence 边界、Gate G1~G6 以 `.trellis/spec/harness/implementation/implementation-trace-contract.md` 为准；BHV/UNIT 编号纪律、doc_type 七类、统一红线以 `.trellis/spec/harness/index.md` 为准；槽位取值与 SLOT-17 以 project-conventions 为准。
- 未执行的验证不得写成通过；测试失败/证据缺失/环境阻塞如实输出，不降级结论。
- 新增测试不能替代设计或实现证据；通过业务流程/集成/e2e/mock/fake 测试反向定义业务语义、测试补写详细设计 = P1，应回退详细或测试计划阶段。
- 不得要求 OCR 作为默认完成条件；OCR 仅 optional bounded provider（用户显式触发 / 高风险抽检），记 `channel=ocr_optional`，第一版不满足 required provider。
- manual provider 审查留痕（非 channel spawn，第一版 supplemental 补充审计、不满足 required provider）必须经验证型 append：
  ```bash
  python3 .trellis/scripts/guru/guru_review_record.py append --task-dir <task> --packet <packet> \
    --provider manual --reviewer <name> --run-id <run_id> --result clean --route-class none \
    --review-target slice:<slice_id> --deterministic-checks passed --dirty-scope isolated \
    --invariant-coverage all_passed --evidence-file <task>/review-records/manual-review-<run_id>.md
  ```
  `--run-id` 必须与 `--evidence-file` 名一致；`channel` / `worker` 由命令派生。

## 与官方 Trellis skill 的边界

本 skill 是 `trellis-check` 在 Guru Go 后端项目的领域化审核口径——在官方 lint/typecheck（`go vet`/`golangci-lint`/`go build`）之上，叠加领域化的合同八问闭合、分层依赖律 + 轻框架/错误链/生命周期 canonical、Secret/Config 红线与 SLOT-17 存量豁免判定，并落到实现 Gate G1~G6 与 PR 准入结论。官方检查跑工具级机检结构，本 skill 跑「代码是否承接已审核详细设计、是否守红线、证据是否可信」的语义判定，二者叠加执行、互不替代。结构机检（trace 计划合同、mutable evidence、切片挂 UNIT、断链）由 `guru_gate.py implement <task_dir>` 同口径执行，本 skill 复用其判定项而不复制其实现。
