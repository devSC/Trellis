# implementation-trace 合同（Go 后端）

> `implement.md` / implementation-trace 是 detail Gate 的 digest-bearing planning contract。核心命题仍是"不是做完感，而是证据感"：每一步落地都要有可复跑命令与可比对产物，而非主观的"已完成"叙述。
> 建议路径：目标仓库 `docs/design/<feature>/implementation-trace.md`（light 链可并入任务内 `implement.md`）。detail 确认后的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`；若必须修改已确认 trace，必须回退 detail Gate 并重新 review/confirm。
> 上游硬输入：详细设计的 `UNIT-<slug>` 单元清单 + 合同八问 + 测试映射；通用约束 `.trellis/spec/guides/golden-path.md`（分层依赖律与禁止清单）+ `.trellis/spec/conventions/project-conventions.md`（槽位选型）。
> 平台形态：Go monorepo，服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，`cmd/<svc>/main.go` 单一入口；契约在 `packages/contracts/`。

Delivery policy is executable, not prose-only. Implementation trace must quote the selected route from `guru_delivery_policy.py`: Small records first scoped code evidence and stops fast; Micro records explicit allowed paths/max files; Lite records compact task evidence, one confirmation batch maximum, and bounded review; Full records selected slice packet, risk packet, guarded start evidence, deterministic checks and implementation review. Budget expiry never removes required Gate/review/confirmation; it produces a terminal stop or re-intake.

## Full/high 风险决策清单

`guru-risk-contract-v2` 仅在 `full_chain + high|unknown` 时要求以下 block。它必须在 `implement.md` 中恰好出现一次，且 block 内只能有一个 JSON fence；Small/Micro/Lite 和兼容 v1 合同不得被该清单拖慢。

<!-- GURU:RISK_DECISION_INVENTORY:START -->
```json
{
  "schema_version": 1,
  "task_id": "<task.json.id>",
  "scope": {
    "selected_slice_id": "<selected-slice-id>",
    "official_start_authority": "selected_slice_only",
    "later_slice_authority": "supervisor_fail_closed"
  },
  "slices": {
    "<selected-slice-id>": [
      {
        "decision_id": "DEC-<DOMAIN>-001",
        "severity": "high",
        "status": "unresolved",
        "recommendation": "<recommended choice>",
        "alternatives": [
          "<credible alternative>"
        ],
        "impact": "<scope, data, compatibility, or rollback impact>",
        "irreversible": false,
        "invariant_ids": [
          "<invariant id from the selected slice packet>"
        ],
        "required": true,
        "source_refs": [
          {
            "artifact_key": "design:chapters/<detail-artifact>.md",
            "anchor": "GURU-DECISION:DEC-<DOMAIN>-001"
          }
        ]
      }
    ]
  }
}
```
<!-- GURU:RISK_DECISION_INVENTORY:END -->

只允许 `required=true` 的 `critical|high` 决策。`decision_id` 必须跨 slice 唯一，slice 和 `invariant_ids` 必须与 packet 精确匹配；每个 `source_ref` 必须指向 Detail artifact 中恰好出现一次且包含该 decision ID 的 anchor。决策确认后将 `status` 改为 `resolved`，并添加非空 `resolution.choice` 与 `resolution.evidence`；未确认时不得伪造 `resolution`。Detail 结构检查、Detail review/confirm、risk packet 和 guarded start 必须解析同一份清单。

## Full/high slice planning audit

Full/high 的 `implement.md` 必须有 slice planning audit，目标是**最少的 commit-stable slices 和最大的安全并发宽度**，不是按 UNIT、internal layer 或章节机械拆分。每个普通 slice 登记 `slice_id`、真实标量 `owner_unit`、`covered_units`、文件级 `owned_paths`、`read_paths`、`depends_on`、`parallel_wave`、`independent_commit_value`、`rollback_contract`、`resource_locks` / 隔离方式、focused checks 和 reviewer context inputs/bytes。`covered_units` 是包含 `owner_unit` 在内的完整 Design UNIT 集合，只属于 planning audit；不得新增或重定义 packet / evidence schema 字段。

- 一个普通 mutable path 在同一 implementation wave 只有一个 owner；symbol、函数或 diff hunk 不能绕过文件级 ownership。共享测试文件也必须唯一归属、分波次或合并。
- 多个 Design UNIT 和多个合法 owner layer 可以合并为一个 implementation slice，只要每个文件仍遵守 Go 分层与 import 方向、合同已冻结且该 slice 有独立提交与回滚价值。`depends_on` 默认空；UNIT 编号或 domain → repository → service → transport 写作顺序本身不是实现依赖。无法冻结且没有独立提交价值的候选 slices 必须合并。
- Full/high 恰好一个 Integration Slice。其 packet `target_paths` 是最终 union snapshot 的 review coverage；planning audit 的 `integration_owned_paths` 才是实际可写范围。普通 slices 只跑 focused checks，full regression 只出现在 Integration deterministic checks。
- 每个 v2 packet 保留并填实 `review_evidence_schema_version=2`、`requirements_design_inputs`、`target_paths`、`deterministic_checks`、`semantic_review_provider`、`invariants` 与 `integration_slice`。禁止为结构整齐默认生成一 UNIT 一 slice 或一 internal layer 一 slice。

## 0. 装载与硬前置

开工前依次确认，任一失败即终止并输出前置缺口（不得在实现阶段补造上游决策）：

- P1 本文件可读；`.trellis/spec/harness/implementation/implementation-trace-contract.md` 为本阶段唯一权威。
- P2 `.trellis/spec/guides/golden-path.md` 可读：分层依赖律（handler→service→repository→domain，严格单向无环；除 domain 外不跨 internal 包导入）、轻框架锁定（net/http ServeMux，禁 gin/echo）、错误链式包装（sentinel + `fmt.Errorf("%w: ...")` + `errors.Is`）、启动/关闭契约（`main()` 控信号 → `app.New()` → `app.Run()` → `app.Shutdown()`）已就绪。
- P3 目标仓库 `project-conventions.md` 可读且校验通过：DI（当前无→可 wire）、ORM（原生 SQL + `lib/pq` + PostgreSQL→可 ent/sqlc）、日志（标准 `log`→可 slog/zap）、测试框架（`testing`→可 testify/ginkgo）、API 风格（REST JSON→可 gRPC）、lint（`golangci-lint`）、会话鉴权（HMAC-SHA256 签名 cookie + bcrypt）等槽位均已选定且未留空。
- P4 详细设计 Gate 已过、人工确认已落盘；本任务承接的 `UNIT-<slug>` 单元全部可定位（幽灵引用——指向不存在的单元——被 gate 断链拦截）。
- P5 编译基线可建立：`go.mod` 可读；Full/high ordinary slice 在改动前只复现 packet 对应 service/package 的 focused build baseline，`go build ./...` 仅由 Integration 建立。非 Full/high 任务继续按原 route 合同执行（用于区分"我引入的失败"与"既有失败"）。

## 必含四节

实现 trace 必须包含以下四节且每节非空；缺任一节，实现 Gate 不予放行（详见 §5）。detail 确认后的命令、测试名、偏差和阻塞记录写入 mutable evidence，并与 trace 字段合同合并恢复。

### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 任务切片 | 每片：真实 `owner_unit` + planning audit 中的 `covered_units` + 涉及的服务/层（`services/<svc>/internal/<layer>`）+ 文件范围 + 完成信号 + 验证方式。切片可以覆盖多个合法 internal layer，但每个文件仍须遵守 owner 与单向 import；边界由文件级 ownership、冻结合同、独立 commit/rollback 价值与资源隔离决定。 |
| 执行顺序 | 按 audit 中真实 `depends_on` 与 `parallel_wave` 排序。`domain` → `repository` → `service` → `transport` → `app`/`config`/`main` 继续约束代码依赖方向，但不自动制造 slice 依赖；契约变更（`packages/contracts/`）只有在消费方无法依赖已冻结合同独立实现时才形成前置。 |
| 风险点 | 逐条预判高风险改动并写验证手段：DB 迁移（向前/向后兼容、回滚脚本）、共享 `app.App` 装配与生命周期（启动顺序/关闭幂等）、跨服务契约 `packages/contracts/` 变更（消费方编译面）、env 前缀冲突（如 `CONTROL_API_*`）、并发与 `context` 超时传递、sentinel error 重命名导致的 `errors.Is` 断裂。 |

**切片登记示例**（合格粒度）：

```
切片 S1 | owner UNIT-user-repository | covered UNIT-user-domain, UNIT-user-repository
  范围：services/control-api/internal/domain/user.go +
       services/control-api/internal/repository/user_repository.go +
       db/migrations/0003_users.up.sql
  完成信号：User 与 sentinel errors、repository 错误映射、迁移 up/down 作为一个
           commit-stable 合同闭合；逐文件 import 仍遵守 repository → domain
  验证：go build ./services/control-api/...；
       go test ./services/control-api/internal/domain/ ./services/control-api/internal/repository/ -run 'Test(User|UserRepository)'
```

❌ 不合格切片登记：「实现用户模块，改 service 和 repository，写完跑测试」——无真实 owner/covered UNIT、无文件范围、无完成信号、无独立提交与回滚说明；问题不是跨层本身，而是 ownership 与合同不可审计。

### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个任务切片完成时**立即**记录下列字段（不积压到批末），保证 PR diff 与计划逐行可对：

- **实际改动文件清单**（相对路径，标层）：如 `services/control-api/internal/service/user_service.go`（service 层）、`packages/contracts/proxy_node_config.go`（跨服务契约）。
- **与计划的偏差**：改了计划外文件 / 未改计划内文件 → **必须写原因**。例：「额外改 `internal/transport/http/router.go`：S2 暴露的新 repository 错误需要 handler 映射 HTTP 状态码，原计划遗漏，已并入 S4 范围」。
- **代码生成执行记录**（按 `[SLOT-01]`（DI/wire）/ `[SLOT-02]`（ORM：sqlc/ent）/ `[SLOT-09]`（文档：swag）等代码生成相关槽位，依 project-conventions 选型）：
  - 选 wire DI → `go run github.com/google/wire/cmd/wire ./services/<svc>/internal/app/`，记录 `wire_gen.go` 是否变更。
  - 选 sqlc → `sqlc generate`，记录生成的 `db/*.sql.go` 清单。
  - 选 ent → `go generate ./services/<svc>/internal/ent`。
  - 选 stringer/mock/protoc 同理逐条记录命令与产物。
  - **当前 golden-path 默认无代码生成**（原生 SQL + 标准库）→ 本项写「N/A：无代码生成槽位启用」，不得留空。
- **装配与启动改动**：触碰 `app.New()`/`app.Run()`/`app.Shutdown()`/`config.Load()`/`cmd/<svc>/main.go` 时单独标注（这些是跨切片共享面，影响所有服务实例）。

### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

| 类型 | 要求 |
|------|------|
| 编译 | Full/high ordinary slice 只运行 packet 声明的 focused build（例如 `go build ./services/<svc>/...` 或 exact package path）；`go build ./...` 只由 Integration 运行。非 Full/high 任务继续按原 route 合同执行。**必须贴命令与退出态**；失败要写错误摘要 + 处置，不能只写"通过"。 |
| 静态检查 | Full/high ordinary slice 只运行 packet 声明的 affected service/package `go vet` 与 `golangci-lint` focused commands；`go vet ./...` + `golangci-lint run ./...` 只由 Integration 运行。非 Full/high 任务继续按原 route 合同执行。逐条记录通过/失败 + 处理；nolint 豁免须写理由并指向 `[SLOT-17]` 记债。 |
| 测试 | 每个切片对应的测试命令 + 结果，**测试名级别**（不只写"通过"）：`go test ./services/control-api/internal/service/ -run TestUserService_Login -v` 输出 `--- PASS: TestUserService_Login/bad_credential (0.00s)` 这样的子测试名。竞态敏感切片附 `go test -race`；覆盖关注切片附 `go test -cover`。新增测试清单逐条列出（文件 + 测试函数名 + 承接的 BHV/UNIT）。 |
| 依赖整洁 | 涉及 `go.mod`/`go.sum` 变更或导入调整时跑 `go mod tidy` 并记录 diff；新增第三方库须落在 project-conventions 已批准槽位内（禁 gin/echo 等被锁框架）。 |
| 未验证项 | 无法本地验证的显式列出 + 指明留给哪个环节：真实 PostgreSQL 集成行为（→ CI 集成测试 / 容器化 DB）、生产负载下的 `context` 超时与连接池表现（→ 压测/灰度）、跨服务契约在另一服务的运行时兼容（→ 集成环境）、信号驱动的优雅关闭实测（→ Manual QA / staging）。 |

**`verification-evidence.jsonl` 正反例**：

✅ 合格：
```
切片 S2 证据：
- go build ./services/control-api/... → 退出 0
- go vet ./services/control-api/... → 退出 0；golangci-lint run → 0 issues
- go test ./services/control-api/internal/repository/ -run TestUserRepository -v
    --- PASS: TestUserRepository_FindByEmail/found (0.01s)
    --- PASS: TestUserRepository_FindByEmail/not_found_maps_ErrUserNotFound (0.01s)
  新增测试：user_repository_test.go::TestUserRepository_FindByEmail（承接 UNIT-user-repository，覆盖 BHV-012 成功 + 失败路径）
- 未验证：真实 PG 唯一约束触发 ErrEmailTaken → 留给 CI 集成测试（本地仅 sqlmock 覆盖）
```

❌ 不合格：「全部编译通过，测试通过，vet 无问题」——无命令、无退出态、无测试名、无新增测试映射、未声明任何未验证项。

### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- **上游缺陷**：详细设计合同错/漏（如 `UNIT-<slug>` 八问缺错误枚举、签名与 domain 实体不符、测试映射漏失败路径）→ 记录后**回退详细阶段修订**，不在实现里就地改设计；`implementation-evidence.jsonl` 留回退记录（指向被修订的 UNIT 与修订动作）。例：「UNIT-user-service 八问 2 未定义 `ErrSessionExpired`，实现需要 → 回退详细补错误类型表，本切片暂挂」。
- **存量违例触碰**：列出触碰的 `[SLOT-17]` 条目编号 + 处置（绕行 / 顺手修复 / 记债）。Go 常见存量违例：跨层反向导入（repository 导入 service）、handler 直接拼裸字符串错误未走 sentinel、`gin`/`echo` 历史残留、`fmt.Errorf` 丢失 `%w` 导致 `errors.Is` 失效、`app.Shutdown()` 未释放某资源。绕行须写"为何不修"，记债须给清单编号。
- **未决决策**：实现中冒出的新决策点（DI 容器引入与否、是否切 sqlc、新增 env 前缀命名、连接池大小默认值）→ **不私自拍板**，记录并升级人工 Gate；落到 project-conventions 槽位或 `technology_decision_handoff` 后再继续。
- **分层依赖律违反**：发现必须违反单向依赖才能完成的需求 → 这是设计缺陷信号，不得用接口逆转之外的手段强行打通；回退详细评估归属。

## 5. 实现 Gate 判定（verify 脚本同口径）

实现切片可进入 commit/PR，当且仅当：

- G1 trace 合同与 mutable evidence 齐全：`implement.md` 计划有 `UNIT-<slug>` 承接与完成信号；执行/偏差/验证证据在 `implementation-evidence.jsonl` 与 `verification-evidence.jsonl` 中可按切片恢复；阻塞如无则显式记录「无」。
- G2 编译证据：当前 route/slice 类型要求的 `go build` 全绿（Full/high ordinary 为 packet focused build，Integration 为 full build；贴命令 + 退出 0）；引入的失败已全部收口。
- G3 静态检查证据：当前 route/slice 类型要求的 `go vet` + `golangci-lint` 通过（Full/high ordinary 为 packet focused checks，Integration 为 full checks），或豁免有理由且记债（`[SLOT-17]`）。
- G4 测试证据：每个切片有测试名级别结果，覆盖承接 UNIT/BHV 的成功路径 + 全部失败路径；新增测试清单可追溯到 UNIT。
- G5 分层与错误契约：无跨层反向/越层导入；服务级错误经 sentinel + `%w` 包装、`errors.Is` 可判定；轻框架未被破坏（无新引入的被锁框架）。
- G6 偏差闭合：PR diff 与计划逐项可对，所有计划外改动均有原因记录；上游缺陷已回退修订而非就地改设计。

任一未满足 → 不进 commit；上游结构性缺陷（归属错、合同越界）→ 回拥有该决策的阶段修订，禁止在实现阶段补造。

## 6. 反模式

- ❌ trace 在 PR 前一次性补写（失去过程证据意义，偏差与回退已不可追溯）。
- ❌ mutable evidence 只写"全部通过"（无命令、无退出态、无测试名）；`go build` 当成隐含步骤不记录。
- ❌ 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
- ❌ 触碰存量违例不挂 `[SLOT-17]` 编号，把绕行/顺手修复混入业务 diff。
- ❌ 用 `_ = err` 吞错或 `fmt.Errorf("...: " + err.Error())` 拼接（丢 `%w`），破坏 `errors.Is` 链。
- ❌ 为图省事在 handler/transport 层直接写 SQL 或调用 repository，跳过 service 层（违反分层依赖律）。
- ❌ 把"未决技术选型"在实现里私自拍板（如擅自引入 wire/sqlc），未升级 project-conventions。

## 7. 不适用场景（本合同不约束的边界）

- 详细设计阶段的接口/数据结构定义：属 detail 合同八问，实现 trace 只承接不重定义。
- 概要归属与技术决策：属概要 Gate，实现发现归属错只能回退，不在 trace 里改。
- 纯文档/注释/格式化变更（无行为改动、无新切片）：可不建独立 trace 切片，但仍需 `gofmt`/`golangci-lint` 通过；若与功能切片同 PR 则并入对应切片记录。
- 跨服务契约 `packages/contracts/` 的语义裁决：契约本身的字段语义属上游设计；trace 只记录"消费方编译面是否随契约变更而更新"这一执行事实。
