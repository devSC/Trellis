# Guru Go Backend Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核；verify 按 route 和 slice role 执行：Full/high ordinary 只运行 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 Integration 才运行 project-wide build/vet/lint/full regression，其他 route 保持既有验证合同。**
> 平台形态：Go monorepo（safa-land 形态），服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，`cmd/<svc>/main.go` 单一入口，跨服务契约在 `packages/contracts/`。
> 规则唯一真源：`.trellis/spec/`（guru-go-backend spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — Full/high-risk 必须先完成 current requirements/risk/design evidence 与一次批量确认，再通过 `guru_task.py start` 的 digest-bound guarded activation；Lite 使用官方标准 task、task-local compact `prd.md` 与一次需求确认，不继承 Full 的 Overview/Detail planning Gate
2. **Specs injected, not remembered** — 规则经 jsonl/hook 注入，不靠记忆；Go 分层依赖律与禁止清单从 `golden-path.md` 注入，不凭印象
3. **Persist everything** — 研究、决策、trace 全部落文件；编译/测试证据贴命令与退出态，不写"已完成"叙述
4. **Gate 不过不进下一阶段** — 缺陷只能回上游阶段修，禁止下游补造（handler 不补 SQL、service 不补路由）
5. **Capture learnings** — 任务完成按萃取九段结构回写 spec

---

## Trellis System（机制速查）

开发者身份、任务生命周期命令、workspace journal、`get_context.py` 用法与 Trellis 原版一致（`python3 ./.trellis/scripts/task.py --help` 为权威清单），此处不复述。

**Guru 关键差异**：

- `.trellis/spec/` 使用 guru-go-backend spec 库：`harness/`（五阶段 SSOT，入口 `harness/index.md`）、`guides/golden-path.md`（分层依赖律 + 各层迷你路径 + 禁止清单）、`conventions/project-conventions.md`（项目约定槽位 SLOT-01~SLOT-13）。阶段→SSOT 映射见 `.trellis/spec/harness/index.md`。
- 任何阶段开始前必须通过 `.trellis/spec/conventions/project-conventions.md` 的校验清单 **C1~C6**（槽位缺失/未填、证据路径不存在、取值与硬规则冲突 = 硬前置失败，先补约定）。
- 三条最高禁令（违反即任务失败，对齐 golden-path 锁定项，不可豁免）：① 禁止引入 gin/echo/fiber 等重型 Web 框架（HTTP 入口只用 `net/http ServeMux`）② 禁止违反分层依赖律的 import（`transport → service → repository → domain` 严格单向无环；除 `domain` 外不跨 `internal` 包导入；`service` 不得 import `transport`、`repository` 不得 import `service`）③ 禁止把真实密钥/口令写成字面量（secret 只写环境变量名引用，经 `config.Load()` 装载）。
- **Guru Gate 机制**：Small/Micro/Lite/Full 的确认预算固定为 `0/0/1/1 batch`。Lite 的一次确认绑定 task-local `prd.md` digest、route、risk 与 `scope_fingerprint`；Full 在实现 Worker 前把 current requirements、critical/high risk 与关键不可逆设计决定合并为一批确认。`overview` / `detail` review 证据写入 `task.json.guru_gates.review_runs`，完整模型见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。通道按 config `guru.gate_mode`（**本节是通道唯一主定义**）：
  - `requirements`：Full requirements review 只产出 current `requirements-ready` evidence，不单独请求用户确认；它与 current critical/high risk、关键不可逆设计决定一起进入实现前唯一确认批次。Lite 不进入 Full requirements review，而是对 task-local compact `prd.md` 做一次 digest-bound 确认。missing/deferred/blocked/stale 不得进入确认。
  - `overview`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 Codex clean review 后自动通过；不得运行 opposite-provider adversarial worker；`confirm overview` 必须失败。
  - `detail`：结构 Gate通过 + 当前 digest 下两个不同 `run_id` 的 clean review 后，把 current requirements/risk/design 作为一批请求用户确认；不得先做 requirements confirm 再做 detail confirm。
  - Custom 默认 `guru.supervision.adversarial_enabled: false`；这只删除 opposite-provider 前置，当前 digest、双 Codex clean、用户确认以及 blocked/medium+ finding 约束全部保留。
  - route-aware policy 必须匹配 delivery policy：`small_inline`/`micro_task` 不继承 Full planning review；`lite_task` 必须由官方 `task.py create` 创建标准 Trellis task，先查 repo evidence，仅对未解决的产品/范围/失败路径/验收歧义运行 bounded Brainstorm，在 task-local compact `prd.md` 当前 digest 获得一次确认后自动 start、host-inline implementation 与 `deterministic_final`，Worker 0、无 Overview/Detail planning review；`full_chain` / `risk=unknown-high` / 缺失或非法 contract 才保持 strict planning/review 路径。Lite 若出现 high-risk 或 scope expansion，在下一次写入前提升为 Full。
  - **strict（默认）**：用户本人通过已安装的 route-aware confirmation 入口记录当前 Lite requirements batch 或 Full requirements/risk/design batch；每个 selection generation 最多一批。
  - **soft**：用户在对话中明确确认后，agent 用 `--via-agent --user-quote "<用户确认原话>"` 记录同一批次；confirmation digest、route、risk、`scope_fingerprint` 必须 current。
  - 进度用 `guru_gate.py status <task_dir>` 查；Full/high-risk 以 `guru_gate.py check-start <task_dir>` 作为 guarded activation 前复查。
  - `check-start` 成功只产生 `START_READY`：Full/high-risk 下一步仅可运行已安装的 `python3 .trellis/scripts/guru/guru_task.py start ...` 并传入当前 gate/slice/risk/envelope/attestation digests；不得把 direct `task.py start` 当作 Full 正常入口。实现/质检 worker 另由 `check-implementation` 要求 `task.json.status == in_progress`，提交另由 `check-commit` 校验 staged scope 与 implementation review。
  - Full 在 detail review/confirm 前必须把按 slice 分组的完整 required critical/high decision universe 写入 `implement.md` 的唯一 `GURU:RISK_DECISION_INVENTORY` JSON fence；精确 schema、resolution evidence 和 Start Guard 重建规则只以 gate SSOT 为准。缺 inventory 或 unresolved 集合非空时不得启动。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：route 难度由需求清晰度、风险、耦合、可逆性与验证成本决定，commit intent 只是交付动作。Agent 自动推荐最低合法 route；更重 override 直接允许，更轻 override 必须满足目标 eligibility；High-risk/unknown-high 不得降级。首次仓库写入前可依据证据降级，首次写入后只允许升级。`gate-contract.json` 记录 selected/recommended route、`selection_source`、单调 `selection_generation` 与 `scope_fingerprint`；`guru_chain` 只保留产物兼容信息。

- `small_inline`：机械、明确、低风险且不改变行为合同；默认无完整 task、确认 0。
- `micro_task`：明确、低风险、路径有界的局部行为改变；最小 task contract、确认 0、focused check。
- `lite_task`：官方标准 task、task-local compact `prd.md`、repo evidence first、必要时 bounded Brainstorm、一次 digest-bound 需求确认、Worker 0、无 Overview/Detail planning review。
- `full_chain`：current requirements/risk/design evidence、一批确认、guarded activation 与 managed implementation。

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。Go 行为以「协议端点 / 编排步骤 / 数据访问 / 失败收口」为枚举单位。full 链另有**正式需求包**（requirement-writing/review，项目 docs 需求目录），prd.md 为其行为规格抽取层。
- 设计产物按链型分轨：
  - **full**：目录级设计包（task.json `design_package` 指向，如 `docs/design/<feature>/`）= `README.md`（导航）+ `design-main.md`（概要主定义，含行为→owner 归属表/三问理由/承接索引/架构就绪自检 G1~G8 + mermaid 架构图 + 时序图）+ `chapters/*.md`（详细设计逐章，directory_precheck + chapter_loop 生成）。任务内 `design.md` 退为指针+摘要。
  - **light**：任务内 `design.md` 两章：**§1 概要设计**（归属表+三问+承接索引）；**§2 详细设计**（逐 doc_type 合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/执行顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；detail 确认后保持 digest-bearing，不作为执行/验证证据 sink；执行、验证、阻塞偏差写入 task-local mutable evidence（`implementation-evidence.jsonl` / `verification-evidence.jsonl` / `commit-plan.json` / `review-records/implementation-reviews.jsonl`）。执行顺序自下而上：`domain → repository → service → transport → app/config/main`。
- `implement.jsonl` / `check.jsonl` — spec/research 注入清单（见 1.5）。
- **编号纪律** — 行为 `BHV-NNN`（prd 标题，不复用不重排，删除留洞）、设计单元 `UNIT-<slug>`（design §2 标题，slug 体现服务+层角色，如 `UNIT-user-service`/`UNIT-users-handler`/`UNIT-session-manager`）；跨产物引用一律写裸编号 token。`python3 .trellis/scripts/guru/guru_gate.py trace-matrix <task_dir> [--write]` 随时生成追溯矩阵（含「需求场景（REQ-UC）」列；--strict 断链拦截）。full 链 prd 的 BHV 标题可在短名前以 `[REQ-UC-XXX]`（多对多）承接正式需求包需求源场景（`### BHV-001 [REQ-UC-005] <短名>`），`trace-matrix --require-req-uc`（或 task.json `require_req_uc:true`）强制 BHV 须带 REQ-UC（旧 prd 默认不拦、列空、不断链）；版本级 `guru_gate.py trace-aggregate <version-dir> [--include-completed]` 反查指向某需求包版本目录的 task，把 `(REQ-UC, BHV, UNIT, Source Task)` 行展开聚合进 `traceability.md` 派生列（手维护 Code/Test/Status 按 key 回填保留；fail-closed：manifest `canonical_excludes` 须含 `traceability`）。**命名消歧**：`REQ-UC-XXX`（需求源场景）≠ overview `UC-<序号>`（架构核心用例），两套独立编号。
- **产物语言** — task 产物（prd/design/implement/research、spec 回写、findings）一律**中文优先**；英文仅限代码标识符、命令、文件路径、协议字段（如 `application_account_id`）、框架/库名（`net/http`、`lib/pq`）、缩写（HMAC-SHA256）、原文引用。commit message 跟随仓库历史风格（3.4 步已有学习机制）。

---

## Phase Index

```
Phase 1: Plan    → 需求 Gate → 概要 Gate → 详细 Gate → 激活任务
Phase 2: Execute → 实现（golden-path 迷你路径 + trace）→ 质检（guru 审核口径）
Phase 3: Finish  → route/slice-role 验证 → 萃取回写 spec → commit → 收尾
```

### Request Triage

- 收到实现类需求时先做可审计分流：不要要求用户自己说 `full/lite/micro`；由 Agent 按需求清晰度、风险、耦合、可逆性与验证成本自动推荐最低合法 route。用户可显式选择或切换；更重总是允许，更轻必须满足目标 eligibility，高风险不得降为 Lite/Micro。
- 若当前已有 active task 但新需求可能完全不同，先确认任务归属或新建任务；需要提交的微小改动在任务确定后用 `guru_gate.py init-contract` 写 `gate-contract.json`，避免污染当前任务。
- 简单对话/小任务：机械且不改变行为合同走 Small；明确、低风险、路径有界的局部行为改变走 Micro。commit intent 不改变任务难度，只决定是否需要最小提交合同。
- 进入任务后第一步加载 golden-path 的入口决策树：判定本任务落在哪个 `services/<svc>/`、碰哪几层（只查询/读取→repository+service；只新端点→transport+service；新服务/新协议→全链）与风险等级；确认是否需动 `packages/contracts/` 跨服务契约。
- **新服务 / 新协议端点 / 鉴权或会话 / DB 迁移 / 跨服务契约变更 → `full_chain`**。无 High-risk 的局部行为变更走 Lite：官方创建标准 task，repo evidence 后只对真实歧义运行 bounded Brainstorm，task-local compact `prd.md` 确认一次后自动执行。
- 建任务许可 ≠ 实现许可：Lite 标准 task 必须在 compact requirements 当前 digest 获得一次确认后自动 start；Full/high-risk 必须先暴露 current risk/decision evidence，并在一次批量确认后走 `guru_task.py start` guarded activation。

[workflow-state:no_task]
无任务：Agent 自动推荐最低合法 route；用户可显式切换。Small 默认不建完整 task；Micro 用最小 contract；Lite 必须官方创建标准 task；High-risk/unknown-high 必须 Full。commit intent 不决定难度。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 / `design-main.md` + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 / `chapters/*.md` + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + golden-path + 项目约定）
- 1.6 激活任务 `[required · once]`（Full review/risk evidence + detail confirm → `guru_task.py start`）
- 1.7 完成判定

[workflow-state:planning]
先按 delivery policy route：Lite=官方标准 task→repo evidence→必要 bounded Brainstorm→task-local compact prd→一次需求确认→自动 start→host-inline→deterministic_final，Worker 0、无 Overview/Detail planning review；Full=current requirements+risk+design→一次批量确认→guarded activation。
[/workflow-state:planning]

[workflow-state:planning-channel]
Lite 不进入 channel：官方标准 task→repo evidence→必要 bounded Brainstorm→task-local compact prd→一次需求确认→自动 host-inline；Full=current requirements+risk+design→一次批量确认→主会话 guarded activation。
[/workflow-state:planning-channel]

[workflow-state:planning-sub-agent]
Lite 不派 Worker：官方标准 task→repo evidence→必要 bounded Brainstorm→task-local compact prd→一次需求确认→自动 host-inline；Full=current requirements+risk+design→一次批量确认→legacy sub-agent 使用 Active task。
[/workflow-state:planning-sub-agent]

[workflow-state:planning-inline]
Lite=官方标准 task→repo evidence→必要 bounded Brainstorm→task-local compact prd→一次需求确认→自动 start→host-inline；Full=current requirements+risk+design→一次批量确认→guarded activation；inline 先 trellis-before-dev。
[/workflow-state:planning-inline]

### Phase 2: Execute（实现阶段）

- 2.1 实现 `[required · repeatable]`
- 2.2 质检 `[required · repeatable]`
- 2.3 回退 `[on demand]`

[workflow-state:in_progress]
route=`gate-contract.json.route`. lite_task: current confirmation digest -> host-inline -> focused check -> mutable evidence -> Spec sync -> reversible commit-ready; Worker 0, no Overview/Detail planning review. full_chain: guru_supervise.py implement-slices <task-dir> --dry-run --backend auto; dispatch only selected_backend.
[/workflow-state:in_progress]

[workflow-state:in_progress-channel]
Lite 不进入 channel/Worker 路径；以下 channel 行为仅适用于 Full。
实现→质检→spec回写→commit→finish。channel：主会话运行 guru_supervise.py implement-check（官方 trellis channel；必要时拆分 implement/check），注入存在的 jsonl/任务产物/Guru skill，等待 done/error/killed，失败先读 messages --raw 和 log；worker 不 commit/push/merge。
[/workflow-state:in_progress-channel]

[workflow-state:in_progress-sub-agent]
Lite 不派 sub-agent；以下 sub-agent 行为仅适用于 Full。
实现→质检→spec回写→commit→finish。legacy sub-agent：dispatch trellis-implement/check，prompt 以 Active task: <path> 开头；trace 记执行/证据/偏差；Full/high ordinary 只要求 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 Integration 才要求 project-wide go build/vet/lint/full-regression evidence；设计缺陷回 Phase1。
[/workflow-state:in_progress-sub-agent]

[workflow-state:in_progress-inline]
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 golden-path/约定/harness，编辑后 trellis-check（guru 口径）；Full/high ordinary 只记录 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 Integration 记录 project-wide go build/vet/lint/full-regression evidence，Small/Micro/Lite/non-Full/v1 仍按原 route 记录验证；缺少当前角色必需证据不得 commit，设计缺陷回 Phase1。
[/workflow-state:in_progress-inline]

### Phase 3: Finish（审核与收尾）

- 3.1 质量验证 `[required · repeatable]`
- 3.2 Debug 复盘 `[on demand]`
- 3.3 Spec 回写 `[required · once]`（萃取九段结构）
- 3.4 Commit `[required · once]`
- 3.5 收尾提醒

[workflow-state:completed]
代码已提交。运行 /trellis:finish-work；工作区不净先回 3.4。`verification-evidence.jsonl` 或等价 task-local mutable evidence 必须包含当前 route/slice role 要求的证据：Full/high ordinary 为 packet 声明的 `deterministic_checks` 与 focused evidence，Integration 为 project-wide go build/vet/lint/full regression，其他 route 保持既有验证。
[/workflow-state:completed]

### Rules

1. 先定位当前 Phase 与步骤（planning 期按 artifact/章节存在性），从下一步继续。
2. `[required]` 步骤不可跳过；`[once]` 步骤产物已存在则跳过。
3. 阶段可回退：下游发现上游缺陷 → 回上游阶段修订产物 → 重入下游。**禁止下游补造**（详细阶段不补归属、实现阶段不改设计语义；handler 不决定 SQL、service 不决定路由）。
4. 风险路由以 `.trellis/scripts/guru/guru_delivery_policy.py` + `.trellis/policy/delivery-policy.json` 为唯一可执行真源；输入是需求清晰度、风险、耦合、可逆性与验证成本，commit intent 不参与难度判定。首次写入前可合法降级，首次写入后只允许升级。
5. `guru_chain=light` 只描述精简产物形态；Lite 执行是标准 task→repo evidence→必要 Brainstorm→compact prd→一次确认→自动 host-inline→deterministic_final，不继承 Full Overview/Detail Gate。预算耗尽只能 terminal stop 或 re-intake。
6. 三条最高禁令（轻框架锁定 / 分层单向依赖 / 无 secret 字面量）贯穿五阶段，对应 Gate 直接 fail。

### Active Task Routing

**所有平台块的 route 边界**：以 `gate-contract.json.route` 为准。Lite 始终 host-inline + deterministic_final；下文任何 `implement-slices`、implementation Worker 或 planning review 命令都仅适用于 Full。

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `go-design-overview-writing` / `go-design-detail-writing`（Go 平台专属设计 skill，按 Go doc_type 七分类展开）；Gate 判定 → 对应 `*-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- `in_progress` 实现/质检 → 先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto` 读取 dispatcher plan；按 `selected_backend` 派发，`channel` 仅 `selected_backend=channel` 时使用官方 worker/`implement-check`，`sub-agent` 按返回 brief，`inline` 串行；worker 不嵌套 spawn implement/check、不 commit/push/merge。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `go-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- `in_progress` 实现/质检 → 先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto`，只按返回的 `trellis-implement` / `trellis-check` brief 派发（按 `go-implementation-guru-writing` / `go-implementation-guru-review` 口径，prompt 首行 `Active task: <path>`，worker 不嵌套 spawn implement/check）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `go-design-*-writing/review`（按 Go doc_type 展开）。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- 编辑前 → `trellis-before-dev`（读 golden-path + project-conventions + harness SSOT）；编辑按 `go-implementation-guru-writing` 口径；编辑后 → `trellis-check`（按 `go-implementation-guru-review` 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；Full/high-risk 等确认与 current digests 后必须走 guarded wrapper，direct `task.py start` 不是文档化的 Full 入口。
- Lite 与 Full 各只有一次 route-specific confirmation batch；确认后自动推进，只有 material scope/digest 变化、新 High-risk 或新不可逆决定才重新确认。
- 合规 STOP：触及鉴权/会话/密钥/用户数据采集或任何法规/政策不确定性 → 立即停止，输出风险点 + 替代方案 + 人类确认清单；密钥一律走环境变量名引用，不落字面量。
- 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有当前 route/slice role 的验证证据：Full/high ordinary 只需 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 Integration 才需 project-wide go build/vet/lint/full regression，其他 route 保持既有验证。
- 产物语言中文优先（英文仅限标识符/命令/路径/协议字段/库名/缩写/原文引用）；面向用户的提问与结论一律中文。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

**Route applicability**：1.1-1.7 的正式需求包、Overview、Detail 与 guarded activation 仅适用于 `full_chain`。`lite_task` 复用 1.0 的官方 `task.py create`，只在任务目录维护 compact `prd.md` 与 Brainstorm evidence，完成一次 digest-bound 需求确认后自动 host-inline；不得为 Lite 补跑 Overview/Detail planning review。

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。
`guru_after_create` 按 delivery policy 写入 `gate-contract.json.route`，它是执行权威；`guru_chain` 只保留产物兼容信息，禁止用于推导 route。Lite 使用官方标准 task + task-local compact `prd.md`；Full 才进入正式设计链。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包草稿**（项目 docs 需求目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 的 one-question loop 仍是高风险产品/范围/风险确认合同；`requirement-writing` 只能生成 `ai_drafted` / `evidence_ready` / open questions，不得绕过用户逐项确认。
两轨 `prd.md` 口径一致：必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（无未决也须显式声明「无未决」；默认一次只问用户 1 个最高优先级问题；仅当用户当前消息明确要求“批量确认/一次性确认/这几个都按推荐处理”等覆盖多个 OQ/decision id 时，才可列出 2~4 个并逐项记录确认；模糊“继续/好/按推荐”回退为单个 next_question，其余保持 open）。Go 行为枚举到「协议端点 / 编排步骤 / 数据访问 / 失败收口」，例：`### BHV-012 创建代理用户` — Given 管理员会话有效 When `POST /api/users` 携带 `display_name`/`proxy_username` Then service 校验入参→repository 落库→触发 config 同步→返回 201；校验失败返回 400 携带 `ErrValidation`。反例 `### BHV-012 处理用户`（无前置/无协议/无失败路径）被需求 Gate 拒。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：五要素缺一 → 留在本步修订。Full requirements review 产出 current `requirements-ready` evidence 并继续设计，不在本步单独询问用户。Lite 不进入该 Full review path；它在 repo evidence 与必要 Brainstorm 后对 task-local compact `prd.md` 请求唯一一次确认。missing/deferred/blocked/stale 均硬阻断。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。Go 后端常见研究项：既有服务的 `internal/` 包结构与导入图（确认不引入反向依赖）、`packages/contracts/` 现有契约字段、`db/migrations/` 现状与迁移版本号、目标服务的 env 前缀与 `config.Load()` 现有键。

#### 1.3 概要设计 `[required · repeatable]`

归属有争议时在 overview review/fix loop 内逐行核对归属表（唯一写 owner、并发场景、与代码现状核对、不让 handler 持有数据访问）后再送审。
加载 `go-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + `.trellis/spec/guides/golden-path.md` + `.trellis/spec/conventions/project-conventions.md`。
按行为枚举 → 分层归属判定 → 承接索引展开：每条 `BHV-NNN` 给唯一 owner（doc_type 取七类之一：`entry-api`/`biz`/`repository-data`/`domain`/`config`/`external`/`runtime`）+ 三问理由（为什么属于它 / 为什么不属于别人 / 为什么需独立存在）。归属示例：路由注册/请求解析/JSON 编解码/状态码 → `entry-api`；业务编排/入参校验/sentinel error → `biz`；SQL/行映射/`ErrNotFound` 转换 → `repository-data`。把数据访问归给 handler 或让 repository 反向 import service 即违反单向依赖律，直接 fail。
**full 链**：建立设计包骨架（`README.md` + `design-main.md` + `chapters/`），把包路径写入 task.json `design_package`，产出 `design-main.md` 概要主定义（含架构就绪自检 G1~G8、mermaid 架构图、时序图或时序图策略表、逐文件承接索引落到 `chapters/<file>.md`）；任务内 `design.md` 写指针+摘要。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`，该 supervisor action 必须在 write/repair 后运行 overview review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `go-design-overview-review` 做 clean-context Codex review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录，不能先进入下一阶段。当前 digest 两个不同 `run_id` 的 Codex clean 后自动进入 1.4；不得运行 `--adversarial` 或启动 opposite-provider worker。`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。`guru_gate.py overview <task_dir>` 复查归属表/三问/承接索引（full 链另查骨架+G1~G8+架构图+时序图）。

#### 1.4 详细设计 `[required · repeatable]`

加载 `go-design-detail-writing`，按概要承接索引展开详细设计（逐 doc_type 合同八问），并产出 `implement.md`（trace §1 计划）。
合同八问（写作完成条件）：① 承接哪些 `BHV-NNN`；② 输入/输出/错误结果（Go 签名级：函数签名、`domain` 结构体、sentinel error 表）；③ 读写哪些状态（DB 行/会话态，写 owner 与概要一致）；④ 调用哪些依赖、不调用哪些（service 调 repository 不反向；handler 不直连 DB）；⑤ 失败如何收口（`fmt.Errorf("%w: ...")` 链式包装 + `errors.Is(err, ErrValidation/ErrNotFound)` 检查 + HTTP 状态码映射，逐条失败路径对应处置）；⑥ 产生哪些事件/后置（config 同步触发、审计、副作用）；⑦ 哪些测试验证它（映射到 `internal/<pkg>/*_test.go` 的 `testing`，逐行为给成功 + 全部失败路径测试点）；⑧ 哪些内容不得在此补造（handler 不决定 SQL、service 不决定路由）。
**full 链**：directory_precheck（design-main 承接索引存在且非空，否则回退概要）→ chapter_loop **逐章/小批次**生成 `chapters/<slug>.md`（禁止一次性全量输出）；命中 pending L2 类型（`domain`/`config`/`external`/`runtime`）须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2（gate 拦截）；v1 提供 L2 的类型为 `entry-api`/`biz`/`repository-data`。
**详细 Gate**：当前 digest 两个不同 `run_id` clean 后，连同 current requirements、critical/high risk 与关键不可逆设计决定形成 Full 唯一确认批次；确认后不得再以 requirements/detail/commit 拆分询问。`guru_gate.py detail <task_dir>` 仍复查合同八问、`implement.md` 与承接断链。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru 必含条目**（各带 reason）：本任务涉及的 `harness/` 阶段 SSOT 文件（如 `harness/detail/detail-type-biz.md`）、`guides/golden-path.md`、`conventions/project-conventions.md`。inline 平台跳过 jsonl 策展，改在编辑前由 `trellis-before-dev` 现读这些文件。

#### 1.6 激活任务 `[required · once]`

Full/high-risk 前置 = current requirements/risk/design 批次已确认、overview/detail 当前 digest 双 clean，且 `guru_gate.py check-start <task_dir>` 通过。`START_READY` 后必须运行 `python3 .trellis/scripts/guru/guru_task.py start <task-dir> --slice <id> --gate-digest <sha256> --slice-packet-digest <sha256> --risk-packet-digest <sha256> --envelope-digest <sha256> --attestation-digest <sha256>`。Lite 在 compact requirements 确认 current 后自动 start。

#### 1.7 Full planning 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + route-aware requirements review clean/current（Lite 不适用该 Full Gate） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review（design-main.md 含 G1~G8+架构图+时序图） | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review + current requirements/risk/design 已一批确认 | ✅ |
| `implement.md`（trace §1 计划，执行顺序自下而上）存在 | ✅ |
| jsonl 含 harness SSOT + golden-path + 项目约定条目 | ✅（inline 平台除外） |
| Full/high-risk 的 `guru_task.py start` guarded activation 已验证；Lite 不适用 | ✅ |

---

## Phase 2 / Phase 3 步骤细则

Lite 在一次当前 requirements digest 确认后自动 host-inline 实现并运行 focused check 与 scoped deterministic_final，Worker 0、无 Overview/Detail planning review。随后自动追加 mutable evidence、同步 Spec 并进入可逆 commit-ready。以下 2.1/2.2 的 `check-implementation`、dispatcher 和 Worker 协议仅适用于 Full。

Full 与 Trellis 原版同构（dispatch 协议、guarded commit 与 finish-work 收尾不变），但 unchanged scope 不得再拆分 requirements/detail/commit 用户确认：

**Full/high minimum-stable slice lifecycle（Agent planning SSOT）**：

- `Design UNIT` 只负责需求、行为和 invariant 追溯；`Implementation Slice` 才是独占修改、focused validation、review、commit 与 rollback 单元。多个 Design UNIT 可合并进一个 Implementation Slice，但 packet 继续只保留一个真实 `owner_unit`，其余写入 `implement.md.covered_units`；禁止按 UNIT、设计章节、doc_type 或技术层机械生成 slice。
- 所有四端都遵循 delivery policy 的同一组 Agent-only 默认值：`full_high_default_strategy=minimum_commit_stable_parallel_first`、`max_ordinary_slices=4`、`mutable_path_overlap=0`、`review_context_target_bytes=262144`、`ordinary_depends_on_default=[]`、`single_integration_slice=true`、`formal_evidence_control_worktree=serial`。Detail 应先冻结接口、schema、digest、错误语义和共享数据结构；共享 mutable path 必须重新分配唯一 owner 或合并，资源锁与 focused test 修改范围必须隔离、分波次或触发合并。
- `guru_supervise.py implement-slices ... --dry-run` 只输出 dispatch plan/brief，不启动 sub-agent，也不是实际 spawn 或 writer-parallel 的证明。完整 packet 集可能因 Integration coverage overlap 被当前 `slice-plan` 保守标为 serial；coordinator 必须回读 Detail planning audit，只派发 ownership 不重叠、`depends_on=[]` 且工具资源可隔离的 ordinary Implementation Slices。
- ordinary implementation 可以并发，但同一 snapshot 只启动一个 semantic reviewer；Full/high ordinary 只运行 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 `Integration Slice` 才运行 project-wide go build/vet/lint/full regression；Small、Micro、Lite、non-Full 和 v1 保留原 route verification。正式 staged review、commit 与 receipt 只在唯一 control worktree 串行收口；Integration 最后执行跨 slice invariants 和最终组合验证，其普通 target union 只是 review coverage，不授予重写 ordinary owner 核心字节的权限。

#### 2.1 实现 `[required · repeatable]`

进入本节的最低硬条件是 `python3 .trellis/scripts/guru/guru_gate.py check-implementation <task-dir>` 通过；`guru_supervise.py implement|check|implement-check` 会在启动 worker 前自动执行该 gate，`planning` 状态一律 fail-closed。

dispatch-mode aware：主会话先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto` 读取 `codex.dispatch_mode` 与 slice-plan；该命令只产生 dispatch plan/brief，实际 spawn 必须由 coordinator 另行执行并留存 dispatch 记录。执行必须按 dry-run report 的 `selected_backend`、`decision`、`dispatch_items`、`dispatch_now`、`deferred_slices`、`downgrade_reasons` 字段行动，`decision=serial|blocked` 不得被强行并行。`sub-agent` 模式按返回的 `trellis-implement` brief 派发平台 sub-agent（brief/prompt 第一行必须是 `Active task: <path>`，worker 已经是被调度的 `trellis-implement`，不得再嵌套 spawn implement/check）；`channel` 模式才使用官方 channel worker / `guru_supervise.py implement-check` 命令；`inline` 模式串行手工执行 report 推荐命令，并先加载 `trellis-before-dev` 读当前任务产物、`conventions/project-conventions.md`、`guides/golden-path.md` 与相关 harness SSOT。helper 只注入存在的 `implement.jsonl`、任务产物和 `go-implementation-guru-writing` skill，等待后端的 done/error/killed 或平台 final status。编码按 `go-implementation-guru-writing` 口径，实现 Detail-approved Implementation Slice 覆盖的最小完整行为；`domain → repository → service → transport → app/config/main` 只是合同与实现顺序，不得按 `UNIT-<slug>` 或 `internal/<layer>` 机械拆片，也不要求一个 slice 只能跨一个 internal 层。执行/验证证据写入 task-local mutable evidence，不把 `implement.md` 当作 detail 确认后的可变证据文件。守住硬规则：`net/http ServeMux`（禁 gin/echo）、分层单向无环、sentinel + `%w` + `errors.Is`、`app.New/Run/Shutdown` 生命周期、`config.Load()` 集中配置、secret 只引用 env 名。发现设计缺口停下回 Phase 1 修订（不在代码里补造 owner/合同）。

#### 2.2 质检 `[required · repeatable]`

dispatch-mode aware：`sub-agent` 模式 dispatch `trellis-check`（prompt 第一行必须是 `Active task: <path>`，且不得再嵌套 spawn check/implement）；`channel` 模式才运行 `python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>` 并可读 `trellis channel messages --raw`；`inline` 模式加载 `trellis-check`。helper 只注入存在的 `check.jsonl`、任务产物和 `go-implementation-guru-review` skill，等待后端结果。按 `go-implementation-guru-review` 口径审核：需求/设计/实现合同一致性、分层依赖律（无反向/横向 `internal` 包导入）、框架锁定（无 gin/echo 新增依赖）、错误三件套（sentinel + `%w` + `errors.Is`，无字符串比对错误）、启动序列与 `context` 超时传递、项目槽位取值（SLOT-01~SLOT-13）、`SLOT-15` 存量豁免判定、合规红线（无 secret 字面量）与 route/slice-role 验证证据。Full/high ordinary 只核对 packet 声明的 `deterministic_checks` 与 focused evidence；唯一 Integration 才核对 project-wide go build/vet/lint/full regression；Small/Micro/Lite/non-Full/v1 沿用原验证合同。缺少当前角色要求的 evidence/compliance 证据不得进入 commit。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（review + 用户 confirm）；不得在代码里绕过设计语义或下游补造 owner/合同（如让 handler 直连 DB 绕过缺失的 repository 设计）。

#### 3.1 质量验证 `[required · repeatable]`

按 route/slice role 复跑验证：Full/high ordinary 只运行 packet 声明的 `deterministic_checks` 与 focused evidence（可包含 packet 指定的 package/service 定向 `go test`）；唯一 Integration 才运行 project-wide `go build ./...`、`go vet ./...`、`golangci-lint run ./...` 与 full regression；Small/Micro/Lite/non-Full/v1 运行各自原 route 的 Go 验证。确认 `verification-evidence.jsonl`（或等价 task-local mutable evidence）已记录命令、退出态、测试名级结果与未验证项（真实 PostgreSQL 集成、生产负载下 `context` 超时/连接池、跨服务契约运行时兼容、信号驱动优雅关闭）。若必须修改 `implement.md`，视为主动返回 detail Gate。当前角色验证失败回 2.1/2.2；必需证据缺失不得进入 3.3。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；Go 高发根因示例：跨层反向导入、`fmt.Errorf` 丢 `%w` 致 `errors.Is` 失效、`app.Shutdown()` 漏释放资源、env 前缀冲突。有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec（只沉淀「这类任务如何被做好」，不沉淀本次需求事实；存量违例修复须从 `SLOT-15` 清单移除并注明日期）；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前先运行 `python3 .trellis/scripts/guru/guru_gate.py commit-plan [task-dir]` 获取机器可读 JSON，按其中 `route`、`commit_mode`、`allowed_stage_paths`、`forbidden_stage_paths`、`can_commit_now`、`split_required`、`blocking_reasons` 汇报 staged scope 和建议切分；计划可提交时仍必须通过 `python3 .trellis/scripts/guru/guru_gate.py check-commit <task-dir>` 或等价 PreToolUse hook。

若实现已发生但缺有效合同，且 staged scope 是低风险 scoped implementation diff，commit-plan 必须进入 post-implementation route recovery：阻断 direct commit，只推荐创建/切换 `micro_task` 并运行 `init-contract --route micro_task --risk low`，不得倒逼补 full PRD / overview / detail。

提交前展示 `commit-plan` 摘要、当前 route/slice role 的验证证据与建议 commit 切分：Full/high ordinary 只展示 packet 声明的 `deterministic_checks` 与 focused evidence，Integration 展示 project-wide go build/vet/lint/full regression，Small/Micro/Lite/non-Full/v1 展示原 route evidence。若 commit 已包含在当前 Lite/Full 唯一确认批次或用户初始指令中，则通过 Gate 后自动执行；否则停在可逆 commit-ready，不消耗第二次需求确认。不 amend、不 push；只处理本任务相关文件，不回滚用户改动。涉及 `go.mod`/`go.sum` 变更须按当前 route/slice role 的合同确认是否需要 `go mod tidy`，且新增依赖必须位于已批准槽位。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作（如 DB 迁移上线时机、跨服务契约消费方同步）与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
