# 复盘萃取模板（九段结构）— Go 后端适配

> Phase 3.3（spec 回写）由 `trellis-update-spec` 按本模板执行。
> 原则：**不沉淀本次需求事实，只沉淀"这类后端任务如何被做好"**；一次性内容（某个接口的字段、某条 SQL、某次排障的具体值）不进 spec。
> 即使结论是"无可沉淀"，也要走完判断并在任务 journal 记一句原因（写明对照了判定清单哪几条、为何不达标）。
> 语言政策：正文中文优先；英文仅限代码标识符、命令、路径、协议字段、框架/库名（net/http、ServeMux、lib/pq、bcrypt、HMAC-SHA256…）、缩写、原文引用。

## 适用范围与边界（先读这一段）

本模板服务于 Go monorepo 后端（服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，入口 `cmd/<svc>/main.go`）的复盘萃取。它回答两个问题：

1. 这次复盘里，有没有"换一个相似后端需求还能复用的方法/坑/约定"？
2. 如果有，按什么结构写、写到哪个文件、怎么让 Gate 检查得到。

它**不**回答："这次需求的事实是什么"——那留在任务产物（`prd.md` / `design.md` / `implement.md` / `check.md`）里，不进 spec。

---

## 萃取产物结构（九段，缺一不可）

按以下结构产出/更新 `.trellis/spec/` 下的方法文件（新方法建新文件；既有方法的增量直接改对应 SSOT/L2 并在文件头记一行修订）。每段都有 Go 后端的实质要求，不得留空或写占位符。

### 1. 名称

kebab-case 方法名，体现"一类后端任务"而非组件名。动词或动名词开头优先。

- 好：`service-error-wrapping`（服务级错误链式包装方法）、`http-handler-context-timeout`（Handler 接收 context 支持 timeout 的展开方法）、`config-env-prefix-isolation`（按服务前缀隔离环境变量配置的方法）、`graceful-shutdown-signal-routing`（main 控信号到 app.Shutdown 的关闭方法）。
- 坏：`user-service`（这是组件名，不是方法）、`fix-login-bug`（这是一次性事实，不是方法）、`go-best-practice`（粒度太粗，无法判定与展开）。

### 2. 适用场景

描述什么样的**一类**后端任务会用到它，给出可识别的触发信号（需求形态 / 代码层位 / 复用频率）。

- 必须能让下一个执行者一眼判断"我这次的任务算不算这一类"。
- Go 层位锚点要写明：是 transport(handler) / service / repository / domain / config / app 哪一层或哪几层的横切。
- 例：「凡是 service 层向上返回业务错误、且 handler 需要据错误类型映射 HTTP 状态码的任务，都用 `service-error-wrapping`；触发信号 = 出现新的 `service/*.go` 业务方法 + transport 层要区分 4xx/5xx。」

### 3. 输入

执行该方法需要什么前置物，逐项列：

- **上游产物**：本任务所处阶段的上游产出（需求包 / `prd.md` 行为规格、概要 `design-main.md` 归属判定表、详细 `chapters/*.md` 合同）。
- **约定槽位**：从 `.trellis/spec/conventions/project-conventions.md` 读到的取值（DI 框架 wire/无、ORM ent/sqlc/原生 SQL+lib/pq、日志 slog/zap/标准 log、测试框架 testify/ginkgo/testing、API 风格 REST JSON/gRPC、DB 驱动、lint golangci-lint、文档生成 Swagger/OpenAPI/无、会话鉴权 HMAC-SHA256 签名 cookie + bcrypt/自实现）。**方法正文里凡涉及这些取值的地方一律写槽位引用，不写死某项目的具体选型。**
- **代码现状**：需要先看的证据文件（如 `services/control-api/internal/app/app.go`、`transport/http/router.go`、`service/user_service.go`、`repository/user_repository.go`、`domain/user.go`、`config/config.go`、`db/migrations/`、`packages/contracts/proxy_node_config.go`、`go.mod`、`Makefile`、`AGENTS.md`）。
- **横向依赖**：通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律 = 归属/调用判定的基准）。

### 4. 正向生成动作

步骤顺序，动词开头，覆盖「识别 → 判定 → 展开 → 自检」四拍。每步要可执行、可验证，落到 Go 的真实层位。

模板（按实际方法替换具体动作，保留四拍）：

1. **识别**：从上游行为规格 / 归属表定位本方法该作用的层（transport/service/repository/domain），列出本次涉及的 `BHV-NNN` 与 `UNIT-<slug>`。
2. **判定**：按分层依赖律确认调用方向单向无环（`transport → service → repository → domain`），确认本动作不跨 `internal/` 包导入（除 `domain` 外）；按 `project-conventions.md` 槽位确认选型取值。
3. **展开**：按该方法的产物合同（第 6 段）生成代码骨架/合同字段；错误沿 `fmt.Errorf("%w: ...")` 链式包装、对外用 `errors.Is()` 检查 sentinel；Handler 接收 `context.Context` 并尊重 timeout/cancel。
4. **自检**：跑 `go build ./...` / `go vet ./...` / `golangci-lint run`（取值按 lint 槽位）与对应测试；核对未越层、错误链可被 `errors.Is` 命中、配置项有默认值、关闭路径覆盖。

### 5. 边界约束

显式写"不做什么、不替谁决策、不进入哪个阶段的领地"。Go 后端高频边界：

- 不在 transport 层写业务规则（handler 只做解析/校验/调用 service/序列化响应）。
- 不让 service 直接拿 DB 连接/写 SQL（数据访问归 repository；repository 之上不暴露驱动细节）。
- 不在 domain 之外被反向依赖（`internal/` 隐私约定：除 domain 外不跨包导入；跨服务契约只走 `packages/contracts/`）。
- 不引入 gin/echo 等重型框架替代 `net/http` ServeMux（golden-path 硬锁定，不可豁免）。
- 不在方法里替项目拍板 `project-conventions.md` 的槽位选型（如直接规定"用 ent"）——只写"按 ORM 槽位"。
- 不把一次性事实（具体路由路径、具体环境变量名值、具体迁移 SQL）写进方法正文。
- 不越阶段：方法是"怎么做对"的元规则，不重新决定需求 scope，也不在此展开某个单元的字段级合同（那属详细设计阶段产物）。

### 6. 输出产物合同

该方法产出的东西必须包含的结构（章节/字段/表/代码骨架形态）。按方法落到的阶段，对齐对应阶段 Gate 的结构合同：

- **若方法影响需求阶段产出** → 产物须含行为五要素：行为（`BHV-NNN` 标题）/ 前置条件 / 状态变化 / 失败路径 / 验收场景。
- **若方法影响概要阶段产出** → 产物须含归属判定表（行为 → owner 层 → 三问理由）+ 详细设计承接索引（`chapter_target → detail_doc_type`），且每个 owner 被至少一个索引条目覆盖。
- **若方法影响详细阶段产出** → 产物须满足合同八问（承接哪些 `BHV` / 输入·输出·错误 / 读写哪些状态 / 调用与不调用哪些依赖 / 失败如何收口 / 产生哪些事件后置 / 哪些测试验证 / 哪些不得补造），单元以 `UNIT-<slug>` 标题定义。
- **若方法影响实现阶段产出** → 产物须落实现 trace 计划合同与 mutable evidence：计划（切片承接 `UNIT`、执行顺序、风险点）/ 执行（实际改动文件、与计划偏差、代码生成记录）/ 证据（`go vet`·`golangci-lint`·测试命令与测试名级结果·未验证项）/ 阻塞与偏差（上游缺陷回退、存量违例处置、未决决策升级）。
- **Go 代码骨架合同**（涉及代码生成的方法必含）：接口/实现的层位归属、错误返回是否走 sentinel + `%w` 包装、Handler 是否透传 `context.Context`、配置是否经 `config.Load()` 集中读取、关闭路径是否串到 `app.Shutdown()`。

### 7. 可验证信号

人或脚本如何判断达标，逐条对应 Gate / `guru_gate.py` 可检查点或可执行命令：

- **机器可查（命令）**：`go build ./...` 通过；`go vet ./...` 无 warning；`golangci-lint run` 通过（按 lint 槽位）；目标测试命令（按测试框架槽位）逐测试名通过。
- **机器可查（结构 Gate）**：`guru_gate.py trace-matrix <task_dir> --write` 生成的 行为×需求场景（REQ-UC）×归属×单元×测试×切片 矩阵无断链；`BHV-NNN` / `UNIT-<slug>` 引用不存在幽灵编号；承接索引↔章节文件双向闭合（full 链）。
- **分层可查**：import 方向 `transport → service → repository → domain` 单向无环；除 domain 外无跨 `internal/` 包导入；无 gin/echo 引入。
- **错误链可查**：对外暴露的失败路径能被 `errors.Is(err, ErrXxx)` 命中（sentinel + `%w` 链未断）。
- 每个信号必须可由人复核或脚本判定，不能写"代码质量好"这类不可验证表述。

### 8. 好例子 / 坏例子

各至少一个，来自本次真实复盘（脱敏业务细节，保留结构与层位）。例子要能说明"按方法做"与"没按方法做"的可见差异。

- ✅ **好例子（service 错误链式包装）**：`service/user_service.go` 定义 `var ErrUserNotFound = errors.New("user not found")`；查询未命中时 `return fmt.Errorf("%w: id=%s", ErrUserNotFound, id)`；transport 层 `if errors.Is(err, service.ErrUserNotFound) { writeJSON(w, http.StatusNotFound, ...) }`。错误语义在 service 拥有，HTTP 映射在 transport 收口，链未断、可被 `errors.Is` 命中，符合分层归属。
- ❌ **坏例子**：service 直接 `return errors.New("not found")`（裸字符串错误，无 sentinel）；handler 用 `strings.Contains(err.Error(), "not found")` 匹配字符串映射状态码。错误语义靠文本匹配，重构即断；且把"什么错对应什么状态"的判定散落在字符串比较里，无单一 owner。
- ✅ **好例子（graceful shutdown）**：`main()` 监听 `SIGINT/SIGTERM` → `app.New(cfg)` → `app.Run(ctx)` → 收到信号 cancel → `app.Shutdown(ctx)` 串联关闭 server 与 repository 连接；Handler 全程接收 `context.Context` 并在 timeout 时返回。
- ❌ **坏例子**：`main()` 里直接 `http.ListenAndServe`，无信号处理、无 `Shutdown`，进程被 kill 时连接与 in-flight 请求被硬断；Handler 用 `context.Background()` 忽略上游 cancel。

### 9. 不适用场景

显式列出别用它的情况，避免方法被误套：

- 一次性事实（这个接口的字段、这条迁移的列名、这次排障的具体环境变量值）→ 留任务产物，不进 spec。
- 仅本项目的选型取值（"本服务用 sqlc 不用原生 SQL"）→ 进 `conventions/project-conventions.md` 槽位，不进通用方法。
- 与既有 SSOT 冲突且属"换口径"性质 → 不直接新写一份，走第二节判定清单的修订形态判定。
- 粒度过粗无法判定/展开（"写好 Go 代码"）→ 不沉淀，拆细或不写。
- 仅风格偏好且无生成顺序与判定方法（缩进、注释口吻）→ 进对应 L2 备注或 lint 槽位，不单列方法。

---

## 判定清单（萃取前自问）

逐项打勾才进入九段撰写；任一为"否"按括号内分流处置，并在 journal 记一句。

- [ ] 它适用于一类重复的后端任务，而不是本次需求？（否 → 不沉淀，事实留任务产物）
- [ ] 它规定了生成顺序与判定方法（识别→判定→展开→自检可落地到 Go 层位）？（否 → 可能只是模板/风格，写进对应 L2 的备注或 lint 槽位即可）
- [ ] 换一个相似后端需求（另一个服务、另一个 handler）还能复用？（否 → 不沉淀）
- [ ] 与既有 SSOT / golden-path 冲突？（是 → 走修订形态判定：局部修订 vs 文档级重构，禁止并行两套口径）
- [ ] 属于项目级取值差异（DI/ORM/日志/测试/API 风格/DB 驱动/lint/文档生成/鉴权槽位）？（是 → 进 `conventions/project-conventions.md` 槽位，不进通用方法，并按需补 ADR）
- [ ] 它是否触碰分层依赖律 / `internal/` 隐私约定 / 轻量框架硬锁？（是 → 校验是否仍单向无环、未跨包、未引重型框架；硬规则不可被方法豁免）

---

## 回写位置路由

装载后（安装路径）的回写目标。开发期模板路径 `guru-template/` 不在此出现。

| 萃取物类型 | 写到 |
|-----------|------|
| 新的一类后端任务方法 | `.trellis/spec/harness/<阶段域>/` 新文件（阶段域取 `overview` / `detail` / `implementation` 之一）+ 在 `.trellis/spec/harness/index.md` 登记 |
| 既有方法的修正 / 新增反例 | 对应 SSOT / L2 文件就地修订（`.trellis/spec/harness/detail/detail-type-*.md` 等），文件头记一行修订日期与原因 |
| 通用方法本身的规则增删（分层律、错误范式、启动/关闭契约、迷你路径） | `.trellis/spec/guides/golden-path.md` 就地修订（改约定先改这里，并按需补 ADR） |
| 生产坑（一次根因，多次可踩，如 context 泄漏、连接未关、迁移漏写版本分支） | `.trellis/spec/guides/`（或迁入 big-question 域后归位） |
| 项目取值变化（槽位选型从 A 换 B） | `.trellis/spec/conventions/project-conventions.md` 槽位（需 ADR 记录） |
| 存量违例修复 | 从存量豁免清单（SLOT-17 / 项目存量清单）移除并注明日期 |

### 回写后必做

1. 在 `.trellis/spec/harness/index.md` 的「阶段 → SSOT 映射」表确认新文件被引用（新方法文件未登记即为孤儿，Gate 不识别）。
2. 若改动触碰分层律 / 错误范式 / 启动关闭契约 / 槽位选型 → 在对应仓库 `docs/adr/` 追加或更新 ADR，并在被改文件头回指 ADR 编号。
3. 编号纪律：行为引用写裸 `BHV-NNN` token，设计单元引用写裸 `UNIT-<slug>` token；新方法文件内若引用具体行为/单元，一律用编号 token，便于 `guru_gate.py trace-matrix` 追溯。
