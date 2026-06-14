---
name: go-implementation-guru-writing
description: 按已过 Gate 的 Go 后端详细设计执行编码与自测的执行编排 Skill（L3）。编码规则唯一来源是通用 golden-path（分层依赖律、轻框架锁定、错误链式包装、生命周期契约、配置集中装载、internal/ 隐私与 packages/contracts/ 契约边界）与 project-conventions 槽位；过程按 implementation-trace 合同四节留证据。本 Skill 只做装载顺序、边界约束、WX 执行流程编排与产物要求，不重定义标准规则；标准口径住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`。
---

# Go 后端实现执行

> 层级契约：规则正文与完成条件住 `.trellis/spec/guides/golden-path.md`（编码红线唯一来源）与 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（过程合同）；类型差异与 doc_type 取值住 `.trellis/spec/harness/index.md` 与 detail L2。本 SKILL.md 只承载装载顺序、边界约束、WX 编排与输出要求。冲突时以阶段子 SSOT 为准，本文件为辅；规则疑义回 SSOT 并引章节号。
> 平台形态：Go monorepo，服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，`cmd/<svc>/main.go` 单一入口；跨服务契约在 `packages/contracts/`。

## 装载顺序（硬前置，任一失败即终止并输出前置缺口）

1. 必须先读 `.trellis/spec/guides/golden-path.md`（编码规则唯一来源）：确认分层依赖律、轻框架锁定、错误链式包装、`app.New/Run/Shutdown` 生命周期、`config.Load()` 集中配置、`internal/` 隐私、`packages/contracts/` 契约边界已就绪；不可用 → 终止并提示先安装/刷新 guru spec 模板（`apply.sh`）。
2. 读 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（过程合同 §0~§7）与 `.trellis/spec/harness/index.md` 的实现 Gate（Gate 4）定义、doc_type 七类、编号纪律（BHV/UNIT）。
3. 读 `.trellis/spec/conventions/project-conventions.md` 并校验 C1~C5：DI（当前无→可 wire）、ORM（原生 SQL + `lib/pq` + PostgreSQL→可 ent/sqlc）、日志（标准 `log`→可 slog/zap）、测试框架（`testing`→可 testify/ginkgo）、API 风格（REST JSON→可 gRPC）、DB 驱动、lint（`golangci-lint`）、文档生成（Swagger/OpenAPI 当前无）、会话鉴权（HMAC-SHA256 签名 cookie + bcrypt，当前自实现）等槽位均已选定且未留空；任一未填 → 停止先定槽位，不在实现里私自拍板。
4. 定位本任务承接的、已过详细 Gate 且人工确认已落盘的详细设计单元（full=`design_package/chapters/*.md`；light=`design.md` §详细），建立 `UNIT-<slug>` 单元清单 + 合同八问 + 测试映射；缺失或单元为幽灵引用 → 终止并提示回退设计阶段（探索性 spike 除外，须显式声明、隔离、不并入交付）。
5. 建立编译基线：`go.mod` 可读，记录改动前 `go build ./...` 的基线状态（用于区分"我引入的失败"与"既有失败"）；不可建立基线 → 记录环境阻塞，不得把未验证当通过。

## 边界约束

- 只实现详细设计合同内的内容；合同外结构（新包、新层、新 sentinel error、新 env 前缀、新跨服务契约字段）一律不新增；合同错漏回退详细阶段，trace §4 留回退记录（指向被修订的 `UNIT-<slug>` 与修订动作），不在实现里就地改设计。
- 严守 golden-path 锁定红线，不可豁免：①框架只用 `net/http ServeMux`，禁新引入 `gin`/`echo` 等重型框架；②分层 `transport(handler) → service → repository → domain` 严格单向无环，除 `domain` 外不跨 `internal` 包导入（handler 不直连 DB、不写 SQL；repository 不反向 import service）；③错误用 sentinel error + `fmt.Errorf("%w: …")` 链式包装 + `errors.Is()` 判定，禁 `fmt.Errorf("...: " + err.Error())` 拼接丢 `%w`、禁 `_ = err` 吞错；④生命周期 `main()` 控信号 → `app.New()` → `app.Run()` → `app.Shutdown()`，Handler 接 `context` 支持 timeout；⑤配置经 `config.Load()` 集中装载（env + 默认值，前缀区分服务如 `<SVC>_*`）；⑥`internal/` 隐私、跨服务结构体进 `packages/contracts/`。
- 不私自拍板实现中冒出的新决策（是否引入 wire、是否切 sqlc/ent、新增 env 前缀命名、连接池默认值、是否换日志库）→ 记录并升级人工 Gate，落到 project-conventions 槽位或 `technology_decision_handoff` 后再继续。
- secret/credential 合规：`config.Load()`、`.env.example`、fixtures、代码与 trace 只写环境变量名引用（如 `DATABASE_URL`、`<SVC>_SESSION_SECRET`），不落真实 API key、长期 AK/SK、token、session 签名密钥或 bcrypt 明文口令；密码态字段（`proxy_password_secret`、`SessionSecret`）按详细设计指定的脱敏/哈希策略处置。
- 不采用默认 TDD/RED-GREEN：默认只运行 project-conventions 测试框架槽位下的既有验证命令，不为驱动结构而先造 fake repo/fake store/fake adapter；高风险切片（DB 迁移、`app.App` 装配与生命周期、跨服务契约变更、并发与 `context` 超时、会话签名）按详细设计测试映射先补失败路径测试再实现。新增测试须可追溯到承接的 `BHV-NNN`/`UNIT-<slug>`。
- 触碰存量违例（`[SLOT-17]` 清单）按标准包口径分类记录（绕行/顺手修复/记债），不把绕行或顺手修复混入业务 diff。
- 若其它通用 skill、插件或 agent 习惯（测试优先、自动重构、引入 DI 容器、手写 ORM 包装）与本平台 golden-path / trace 合同冲突，以平台 SSOT 为准，冲突项忽略或向用户确认。

## 执行流程（WX 步骤）

1. **WX-0 判定实现模式与编译基线**：判定空服务初始化 / 已有服务增量 / 重构校准；确定本任务落在哪个 `services/<svc>/`，复用还是新建 `internal/{app,config,transport,service,repository,domain,auth}` 包，跨服务数据结构是否需进 `packages/contracts/`；记录改动前 `go build ./...` 基线。
2. **WX-1 计划（开工前写）**：按 trace 合同 §1 在目标仓库 `implement.md`（建议 `docs/design/<feature>/implementation-trace.md`）产出任务切片。每片含：承接的 `UNIT-<slug>`（幽灵引用被 Gate 拦截）+ 所属服务/层（`services/<svc>/internal/<layer>`）+ 文件范围 + 完成信号 + 验证方式。执行顺序**自下而上**：`domain`（实体/sentinel errors）→ `repository`（SQL/迁移）→ `service`（编排 + `%w` 包装）→ `transport`（ServeMux 路由 + handler）→ `app`/`config`/`main`（装配与启动）；`packages/contracts/` 契约变更排在所有消费方之前。逐条预判高风险点（DB 迁移兼容/回滚、`app.App` 装配生命周期、契约变更消费方编译面、env 前缀冲突、`context` 超时传递、sentinel 重命名导致的 `errors.Is` 断裂）。人工确认从最小可独立编译的切片开始。
3. **WX-2 逐片实现（随做随记）**：每片对照承接 `UNIT-<slug>` 的合同八问落地——②输入/输出/错误（函数签名、`domain` 结构体、错误枚举与 sentinel 表，对齐如 `service.ErrValidation`、`repository.ErrNotFound`）；④调用关系单向（service 调 repository 不反向，handler 走 service 不直连 DB）；⑤失败收口（`%w` 包装 + `errors.Is` 检查 + HTTP 状态码映射，逐条失败路径）；⑥后置副作用（如 config 同步触发 `configSync.TouchNodesForUser`）。每片完成**立即**更新 trace §2（实际改动文件清单标层、与计划偏差及原因、触碰 `app.New/Run/Shutdown`/`config.Load()`/`cmd/<svc>/main.go` 的共享面单独标注），不积压到批末。
4. **WX-3 代码生成（仅触发条件满足时）**：按 project-conventions 代码生成相关槽位选型执行并记入 trace §2——选 wire（`[SLOT-01]` DI）→ `go run github.com/google/wire/cmd/wire ./services/<svc>/internal/app/`（记 `wire_gen.go` 是否变更）；选 sqlc（`[SLOT-02]` ORM）→ `sqlc generate`（记生成 `db/*.sql.go` 清单）；选 ent（`[SLOT-02]` ORM）→ `go generate ./services/<svc>/internal/ent`；选 swag（`[SLOT-09]` 文档）/ stringer / mock / protoc 同理逐条记命令与产物。**当前 golden-path 默认无代码生成槽位（原生 SQL + 标准库）→ 本项写「N/A：无代码生成槽位启用」，不留空、不私自引入生成器。**
5. **WX-4 逐片验证（验证后记）**：按 trace 合同 §3 记入 trace §3——编译 `go build ./...` 或 `go build ./services/<svc>/...`（贴命令 + 退出态，失败写错误摘要 + 处置）；静态检查 `go vet ./...` + `golangci-lint run ./...`（逐条通过/失败，nolint 豁免写理由并指向 `[SLOT-17]`）；测试到**测试名级别**（如 `go test ./services/<svc>/internal/service/ -run TestUserService_Create -v` 给出子测试名），竞态敏感切片附 `-race`，新增测试逐条列文件 + 测试函数名 + 承接 `BHV-NNN`/`UNIT-<slug>`；依赖变更跑 `go mod tidy` 记 diff（新增库须落在已批准槽位内，禁被锁框架）。失败先修复再进下一片；未验证项显式列出并指明留给哪个环节（真实 PostgreSQL 集成 → CI 集成测试/容器化 DB；生产负载下连接池与 `context` 超时 → 压测/灰度；跨服务契约运行时兼容 → 集成环境；信号驱动优雅关闭 → Manual QA/staging）。
6. **WX-5 存量违例处置**：触碰 `[SLOT-17]` 条目时按标准包口径分类记录到 trace §4（绕行须写"为何不修"；顺手修复须独立标注；记债须给清单编号）。Go 常见存量违例：跨层反向导入（repository 导入 service）、handler 直接拼裸字符串错误未走 sentinel、`gin`/`echo` 历史残留、`fmt.Errorf` 丢 `%w`、`app.Shutdown()` 未释放某资源。
7. **WX-6 收口自检**：对照实现 Gate G1~G6（见下「质量门禁」）输出自检摘要；上游缺陷已回退修订而非就地改设计；未验证项显式移交（CI 集成 / 压测 / Manual QA / 真机）。

## 输出

- **实施计划先列**：`implement.md`（trace）路径、`UNIT-<slug>` 承接清单、`chapter_target → detail_doc_type → Go 代码资产`（服务/层/文件）映射、自下而上的阶段顺序与高风险点、阻塞项。
- **代码改动 + 新增/修订测试**：改动文件按层标注（如 `services/<svc>/internal/service/user_service.go`（service 层）、`packages/contracts/proxy_node_config.go`（跨服务契约））。
- **完整的 `implement.md`（trace 四节齐全且非空）**：计划 / 执行 / 证据 / 阻塞与偏差；证据节带命令级记录与测试名，无阻塞则显式写「无」。
- **Gate G1~G6 自检摘要 + 移交清单**：逐项给结论（pass / 阻塞 / 移交环节）；交付时说明修改文件、对应设计锚点（`UNIT-<slug>` / `BHV-NNN`）、验证命令、未验证项与剩余阻塞。
- **若无法完成**：明确输出 `blocked` 的具体详细设计文件、缺失合同锚点（如八问缺错误枚举）与需要回修的合同项；环境阻塞写准确命令、错误摘要、缺失依赖与恢复条件，结论不得标 `pass`。

## 质量门禁（与 `guru_gate.py implement` / 实现 Gate 同口径）

切片可进入 commit/PR，当且仅当：

- **G1 trace 四节齐全且非空**：计划有 `UNIT-<slug>` 承接与完成信号、执行有改动清单与偏差说明、证据有命令级记录、阻塞节如无则显式写「无」；`implement.md` 必须存在（trace 不存在直接 fail）。
- **G2 编译证据**：`go build ./...` 全绿（贴命令 + 退出 0）；本任务引入的失败已全部收口（编译不过的切片不存在"完成"）。
- **G3 静态检查证据**：`go vet ./...` + `golangci-lint run ./...` 通过，或豁免有理由且记债（`[SLOT-17]`）。
- **G4 测试证据**：每个切片有测试名级别结果，覆盖承接 `UNIT-<slug>`/`BHV-NNN` 的成功路径 + 全部失败路径；新增测试清单可追溯到 UNIT；未执行的验证不得写成通过。
- **G5 分层与错误契约**：无跨层反向/越层导入（除 `domain` 外不跨 `internal` 包）；服务级错误经 sentinel + `%w` 包装、`errors.Is` 可判定；轻框架未被破坏（无新引入被锁框架）；secret 只写环境变量名引用，无字面量密钥。
- **G6 偏差闭合 + 编号闭合**：PR diff 与计划逐项可对，计划外改动均有原因记录；切片均挂真实 `UNIT-<slug>`（幽灵单元被拦截）；上游结构性缺陷（归属错、合同越界、单元跟随名词而非行为）已回退拥有该决策的阶段修订，禁止在实现阶段补造。

任一未满足 → 不进 commit。`go build ./...` / `go vet ./...` / `golangci-lint run` / `go test ./...`（测试名级别）由 worktree.yaml verify 条目执行，与本自检同口径。

## 好例 / 坏例

✅ **合格切片登记与证据**（粒度可独立 review、命令级证据、可追溯）：

```
切片 S2 | 承接 UNIT-user-repository | services/<svc>/internal/repository/user_repository.go + db/migrations/0011_users_xxx.up.sql
  范围：UserRepository 原生 SQL（lib/pq），sql.ErrNoRows → domain/repository.ErrNotFound 转换
  完成信号：go build ./services/<svc>/... 退出 0；迁移可 up/down；无跨层导入
  证据：
    - go build ./services/<svc>/... → 退出 0
    - go vet ./services/<svc>/... → 退出 0；golangci-lint run → 0 issues
    - go test ./services/<svc>/internal/repository/ -run TestUserRepository -v
        --- PASS: TestUserRepository_GetByID/found (0.01s)
        --- PASS: TestUserRepository_GetByID/not_found_maps_ErrNotFound (0.01s)
      新增测试：user_repository_test.go::TestUserRepository_GetByID（承接 UNIT-user-repository / BHV-012 成功+失败路径）
    - 未验证：真实 PG 唯一约束触发 → 留给 CI 集成测试
```

❌ **不合格**：「实现用户模块，改 service 和 repository，写完跑测试」——无 `UNIT` 编号、无文件范围、无完成信号、跨多层无法独立 review；证据「全部编译通过，测试通过，vet 无问题」——无命令、无退出态、无测试名、无新增测试映射、未声明未验证项。

❌ **红线违例**：为图省事在 handler/transport 层直接写 SQL 或调 repository 跳过 service 层（违反单向依赖律）；用 `fmt.Errorf("create user: " + err.Error())` 拼接丢 `%w`（破坏 `errors.Is` 链）；实现里擅自引入 `wire`/`sqlc`/`gin` 未升级 project-conventions；trace 在 PR 前一次性补写（失去过程证据）。

## 不适用场景（本 Skill 不约束的边界）

- 详细设计阶段的接口/数据结构定义（合同八问）：实现 trace 只承接不重定义；八问缺错（漏错误枚举、签名与 `domain` 实体不符、测试映射漏失败路径）→ 回退详细阶段，不在实现里改设计。
- 概要归属与技术决策（行为 owner、分层归属、技术选型）：属概要 Gate；实现发现归属错只能回退，不在 trace 里改。
- 纯文档/注释/格式化变更（无行为改动、无新切片）：可不建独立 trace 切片，但仍需 `gofmt`/`golangci-lint` 通过；与功能切片同 PR 则并入对应切片记录。
- 跨服务契约 `packages/contracts/` 的字段语义裁决：契约语义属上游设计；trace 只记录"消费方编译面是否随契约变更更新"这一执行事实。
- 分支/worktree/提交/PR 流程隔离：交给 `sop-task-runner`——先用本 Skill 判定改动范围 → sop-task-runner 创建隔离 → 在隔离内继续本 Skill。

## 与官方 Trellis skill 的边界

本 skill 是官方 `trellis-implement` 在 Guru Go 后端（典型形态：`net/http` + 严格分层 + 原生 SQL）项目的领域化执行口径：sub-agent 实现时按本 skill 的 WX 流程、golden-path 红线与 trace 合同四节工作；Phase 2 dispatch 时在 prompt 中指明加载本 skill 口径。`trellis-implement` 负责通用任务编排与状态机推进，本 skill 不重复其职责，只补齐 Go 平台的分层依赖律、错误链契约、生命周期装配与 trace 证据要求。规则正文不在本 skill 复写，住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`。
