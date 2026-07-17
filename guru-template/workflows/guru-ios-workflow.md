# Guru iOS Native Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核（verify 强制：`swift build` + `swift test` / `xcodebuild test`）。**
> 平台 = iOS / macOS 原生（Swift + SwiftUI 主 + RxSwift 遗留，DDD 四层 + FactoryKit DI）。规则唯一真源：`.trellis/spec/`（guru-ios-native spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — Full/high-risk 必须先完成 current requirements/risk/design evidence 与一次批量确认，再通过 `guru_task.py start` 的 digest-bound guarded activation；Lite 使用官方标准 task、task-local compact `prd.md` 与一次需求确认，不继承 Full 的 Overview/Detail planning Gate
2. **Specs injected, not remembered** — 规则经 jsonl/hook 注入，不靠记忆
3. **Persist everything** — 研究、决策、trace 全部落文件
4. **Gate 不过不进下一阶段** — 缺陷只能回上游阶段修，禁止下游补造
5. **分层依赖律是归属硬基准** — Domain 零依赖；依赖方向 Domain → App → Infrastructure → UI 单向；违反直接 fail，不在概要/详细/实现任一阶段放行
6. **Capture learnings** — 任务完成按萃取九段结构回写 spec

---

## Trellis System（机制速查）

开发者身份、任务生命周期命令、workspace journal、`get_context.py` 用法与 Trellis 原版一致（`python3 ./.trellis/scripts/task.py --help` 为权威清单），此处不复述。

**Guru iOS 关键差异**：

- `.trellis/spec/` 使用 guru-ios-native spec 库：`harness/`（五阶段 SSOT）、`guides/golden-path.md`（iOS golden-path）、`conventions/`（项目约定槽位）。入口与阶段映射见 `.trellis/spec/harness/index.md`。
- 任何阶段开始前必须通过 `.trellis/spec/conventions/project-conventions.md` 的校验清单（UI 框架 / 网络层 / 日志 / JSON 修复 / 测试框架 / i18n / 主题 / feature 模块结构 / mock 生成 / 构建自动化 等槽位，缺失或未填 = 硬前置失败，先补约定）。
- **iOS 三条最高禁令（违反即任务失败）**：① 禁止违反分层依赖律的 import（Domain 不得 import App/Infrastructure/UI；View 不得直接 import 持久化或网络）② 禁止 View 间直接导航（必须走 `AppCoordinator`）③ 禁止用 CoreData / SwiftData 落地持久化（持久化一律走 WCDBSwift + Repository）。
- **golden-path 锁定硬规则**：FactoryKit `@Injected` DI（禁手动 `init()` 注入依赖）；Repository 模式强制（接口在 Domain，实现在 Infrastructure）；`enum Error` 分层定义（per domain，如 `StoryError` / `PersistenceError`）；ViewModel = `ObservableObject` + `@Published`；private 方法收纳到 `private extension`。
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

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。full 链另有**正式需求包**（requirement-writing/review，项目 docs 需求目录），prd.md 为其行为规格抽取层。
- 设计产物按链型分轨：
  - **full**：目录级设计包（task.json `design_package` 指向，如 `docs/design/<feature>/`）= `README.md`（导航）+ `design-main.md`（概要主定义，含归属表/承接索引/架构就绪自检）+ `chapters/*.md`（详细设计逐章，directory_precheck + chapter_loop 生成）。任务内 `design.md` 退为指针+摘要。
  - **light**：任务内 `design.md` 两章：**§1 概要设计**（归属表+三问+承接索引）；**§2 详细设计**（逐 doc_type 合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；detail 确认后保持 digest-bearing，不作为执行/验证证据 sink；执行、验证、阻塞偏差写入 task-local mutable evidence（`implementation-evidence.jsonl` / `verification-evidence.jsonl` / `commit-plan.json` / `review-records/implementation-reviews.jsonl`）。
- `implement.jsonl` / `check.jsonl` — spec/research 注入清单（见 1.5）。
- **编号纪律** — 行为 `BHV-NNN`（prd 标题，不复用不重排）、设计单元 `UNIT-<slug>`（design §2 / chapters 标题）；跨产物引用一律写编号 token。`python3 .trellis/scripts/guru/guru_gate.py trace-matrix <task_dir> [--write]` 随时生成追溯矩阵（含「需求场景（REQ-UC）」列；--strict 断链拦截）。full 链 prd 的 BHV 标题可在短名前以 `[REQ-UC-XXX]`（多对多）承接正式需求包需求源场景（`### BHV-001 [REQ-UC-005] <短名>`），`trace-matrix --require-req-uc`（或 task.json `require_req_uc:true`）强制 BHV 须带 REQ-UC（旧 prd 默认不拦、列空、不断链）；版本级 `guru_gate.py trace-aggregate <version-dir> [--include-completed]` 反查指向某需求包版本目录的 task，把 `(REQ-UC, BHV, UNIT, Source Task)` 行展开聚合进 `traceability.md` 派生列（手维护 Code/Test/Status 按 key 回填保留；fail-closed：manifest `canonical_excludes` 须含 `traceability`）。**命名消歧**：`REQ-UC-XXX`（需求源场景）≠ overview `UC-<序号>`（架构核心用例），两套独立编号。
- **产物语言** — task 产物（prd/design/implement/research、spec 回写、findings）一律**中文优先**；英文仅限 Swift 标识符、命令（`swift build`/`xcodebuild`）、文件路径、协议字段、外部专有名词（FactoryKit/WCDBSwift/RxSwift）、缩写与原文引用。commit message 跟随仓库历史风格。

### iOS 详细设计 doc_type 权威七类（全程唯一，禁止改名/增减/换数）

> 下游引用、trace 矩阵、jsonl reason、`guru_gate.py` 校验一律只认这七个 token，**严禁自创 transport-handler / service / datasource / controller 之类**。owner 层标注必须与分层依赖律一致。

| # | doc_type | 归属层（owner） | 职责 | L2 状态 |
|---|----------|----------------|------|---------|
| 1 | `viewmodel`    | UI       | `ObservableObject` + `@Published` 状态容器，编排 UseCase，绝不含持久化/网络直连 | L2 full（`detail-type-viewmodel.md`） |
| 2 | `usecase`      | Domain   | 业务编排（零 UI 依赖），调用 Repository 接口，抛 `enum Error` | L2 full（`detail-type-usecase.md`） |
| 3 | `repository`   | Domain + Infrastructure（合并一类） | Domain 定义 `IXxxRepository` 接口 + Infrastructure 落地实现（WCDBSwift/网络） | L2 full（`detail-type-repository.md`） |
| 4 | `domain-model` | Domain   | 实体/值对象/`enum Error`/不变量；零依赖、可被任意层导入 | L2 pending |
| 5 | `view`         | UI       | SwiftUI View，只展示 + 输入，无业务逻辑 | L2 pending |
| 6 | `coordinator`  | App      | `AppCoordinator` 导航 + FactoryKit DI 装配（`Container+*` 工厂） | L2 pending |
| 7 | `external`     | Infrastructure | 外部集成：网络（URLSession/Moya）/ SDK / WCDBSwift 持久化引擎 / 第三方 | L2 pending |

- **L2 文件**（v1 已提供，与 flutter 的 controller/usecase/repository-datasource 三类一一对应）：`.trellis/spec/harness/detail/detail-type-viewmodel.md` / `detail-type-usecase.md` / `detail-type-repository.md`。
- **pending 四类**（`domain-model`/`view`/`coordinator`/`external`）：详细设计按 L1 合同八问展开，文档头标 `l2_status: pending`；full 链命中 pending 类型须在详细 Gate 前显式 `L2豁免：<doc_type> 理由：…`，否则 gate 拦截。
- **写作顺序（自底向上）**：`domain-model` → `repository` → `usecase` → `viewmodel` → `view`，`coordinator` / `external` 作横切随相关层落位。

---

## Phase Index

```
Phase 1: Plan    → 需求 Gate → 概要 Gate → 详细 Gate → 激活任务
Phase 2: Execute → 实现（golden-path 迷你路径 + trace）→ 质检（guru iOS 口径）
Phase 3: Finish  → 验证（swift build/test）→ 萃取回写 spec → commit → 收尾
```

### Request Triage

- 收到实现类需求时先做可审计分流：不要要求用户自己说 `full/lite/micro`；由 Agent 按需求清晰度、风险、耦合、可逆性与验证成本自动推荐最低合法 route。用户可显式选择或切换；更重总是允许，更轻必须满足目标 eligibility，高风险不得降为 Lite/Micro。
- 若当前已有 active task 但新需求可能完全不同，先确认任务归属或新建任务；需要提交的微小改动在任务确定后用 `guru_gate.py init-contract` 写 `gate-contract.json`，避免污染当前任务。
- 简单对话/小任务：机械且不改变行为合同走 Small；明确、低风险、路径有界的局部行为改变走 Micro。commit intent 不改变任务难度，只决定是否需要最小提交合同。
- 进入任务后第一步判定碰哪几层（只文案 → i18n 路径；只一个 ViewModel/View → 局部链；跨层 feature → 全链）与风险等级。
- **核心玩法 / 付费内购 / 存档 / 权限或数据采集 / 跨 DDD 多层 → `full_chain`**。无 High-risk 的局部行为变更走 Lite：官方创建标准 task，repo evidence 后只对真实歧义运行 bounded Brainstorm，task-local compact `prd.md` 确认一次后自动执行。
- 建任务许可 ≠ 实现许可：Lite 标准 task 必须在 compact requirements 当前 digest 获得一次确认后自动 start；Full/high-risk 必须先暴露 current risk/decision evidence，并在一次批量确认后走 `guru_task.py start` guarded activation。

[workflow-state:no_task]
无任务：Agent 自动推荐最低合法 route；用户可显式切换。Small 默认不建完整 task；Micro 用最小 contract；Lite 必须官方创建标准 task；High-risk/unknown-high 必须 Full。commit intent 不决定难度。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + iOS 项目约定）
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
实现→质检→spec回写→commit→finish。legacy sub-agent：dispatch trellis-implement/check，prompt 以 Active task: <path> 开头；trace 记执行/swift build+test 证据/偏差；质检按 guru iOS 口径（分层律+DI+doc_type）；无 build/test 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress-sub-agent]

[workflow-state:in_progress-inline]
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 iOS spec，编辑后 trellis-check（guru iOS 口径）；swift build/test 证据记 `verification-evidence.jsonl` 等 task-local mutable evidence，无证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress-inline]

### Phase 3: Finish（审核与收尾）

- 3.1 质量验证 `[required · repeatable]`
- 3.2 Debug 复盘 `[on demand]`
- 3.3 Spec 回写 `[required · once]`（萃取九段结构）
- 3.4 Commit `[required · once]`
- 3.5 收尾提醒

[workflow-state:completed]
代码已提交。运行 /trellis:finish-work；工作区不净先回 3.4。
[/workflow-state:completed]

### Rules

1. 先定位当前 Phase 与步骤（planning 期按 artifact/章节存在性），从下一步继续。
2. `[required]` 步骤不可跳过；`[once]` 步骤产物已存在则跳过。
3. 阶段可回退：下游发现上游缺陷 → 回上游阶段修订产物 → 重入下游。**禁止下游补造**（详细阶段不补归属、实现阶段不改设计语义）。
4. 风险路由以 `.trellis/scripts/guru/guru_delivery_policy.py` + `.trellis/policy/delivery-policy.json` 为唯一可执行真源；输入是需求清晰度、风险、耦合、可逆性与验证成本，commit intent 不参与难度判定。首次写入前可合法降级，首次写入后只允许升级。
5. `guru_chain=light` 只描述精简产物形态；Lite 执行是标准 task→repo evidence→必要 Brainstorm→compact prd→一次确认→自动 host-inline→deterministic_final，不继承 Full Overview/Detail Gate。预算耗尽只能 terminal stop 或 re-intake。
6. doc_type 全程只用钉死七类（`viewmodel`/`usecase`/`repository`/`domain-model`/`view`/`coordinator`/`external`）；归属违反分层依赖律 = 直接 fail。

### Active Task Routing

**所有平台块的 route 边界**：以 `gate-contract.json.route` 为准。Lite 始终 host-inline + deterministic_final；下文任何 `implement-slices`、implementation Worker 或 planning review 命令都仅适用于 Full。

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `ios-design-overview-writing` / `ios-design-detail-writing`；Gate 判定 → 对应 `ios-design-overview-review` / `ios-design-detail-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- `in_progress` 实现/质检 → 先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto` 读取 dispatcher plan；按 `selected_backend` 派发，`channel` 仅 `selected_backend=channel` 时使用官方 worker/`implement-check`，`sub-agent` 按返回 brief，`inline` 串行；worker 不嵌套 spawn implement/check、不 commit/push/merge。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `ios-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- `in_progress` 实现/质检 → 先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto`，只按返回的 `trellis-implement` / `trellis-check` brief 派发（口径 = `ios-implementation-guru-writing` / `ios-implementation-guru-review`，prompt 首行 `Active task: <path>`，worker 不嵌套 spawn implement/check）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `ios-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- 编辑前 → `trellis-before-dev`（读 iOS spec）；编辑后 → `trellis-check`（口径 = `ios-implementation-guru-review`）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；Full/high-risk 等确认与 current digests 后必须走 guarded wrapper，direct `task.py start` 不是文档化的 Full 入口。
- Lite 与 Full 各只有一次 route-specific confirmation batch；确认后自动推进，只有 material scope/digest 变化、新 High-risk 或新不可逆决定才重新确认。
- 合规 STOP：任何可能违反 App Store 审核政策（如隐私清单 `PrivacyInfo.xcprivacy`、ATT、内购规则）或美国法规的不确定性 → 立即停止，输出风险点+替代方案+人类确认清单。
- iOS 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有 `swift build` + `swift test`（或 `xcodebuild test`）验证证据。
- 产物语言中文优先（英文仅限标识符/命令/路径/协议字段/专有名词/缩写/原文引用）；面向用户的提问与结论一律中文。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

**Route applicability**：1.1-1.7 的正式需求包、Overview、Detail 与 guarded activation 仅适用于 `full_chain`。`lite_task` 复用 1.0 的官方 `task.py create`，只在任务目录维护 compact `prd.md` 与 Brainstorm evidence，完成一次 digest-bound 需求确认后自动 host-inline；不得为 Lite 补跑 Overview/Detail planning review。

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。
after_create 按 delivery policy 写入 `gate-contract.json.route`，它是执行权威；`guru_chain` 只保留产物兼容信息，禁止用于推导 route。Lite 使用官方标准 task + task-local compact `prd.md`；Full 才进入正式设计链。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包草稿**（项目 docs 需求目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 的 one-question loop 仍是高风险产品/范围/风险确认合同；`requirement-writing` 只能生成 `ai_drafted` / `evidence_ready` / open questions，不得绕过用户逐项确认。
两轨 `prd.md` 口径一致，**需求五要素**：① 行为规格（Given/When/Then，每条 `BHV-NNN` 标题）② 核心能力清单（P0/P1）③ 失败路径（含 `enum Error` 预期分支，如校验失败 / 持久化失败 / 网络失败）④ 验收场景（可被 `swift test` 断言的可验证信号）⑤ 显式未决问题（默认一次只问用户 1 个最高优先级问题；仅当用户当前消息明确要求“批量确认/一次性确认/这几个都按推荐处理”等覆盖多个 OQ/decision id 时，才可列出 2~4 个并逐项记录确认；模糊“继续/好/按推荐”回退为单个 next_question，其余保持 open）。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：五要素缺一 → 留在本步修订。Full requirements review 产出 current `requirements-ready` evidence 并继续设计，不在本步单独询问用户。Lite 不进入该 Full review path；它在 repo evidence 与必要 Brainstorm 后对 task-local compact `prd.md` 请求唯一一次确认。missing/deferred/blocked/stale 均硬阻断。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。iOS 典型研究项：SDK 能力边界、WCDBSwift 表结构与迁移、SwiftUI 与 RxSwift 桥接、并发与 `@MainActor` 隔离。

#### 1.3 概要设计 `[required · repeatable]`

归属有争议时在 overview review/fix loop 内逐行核对**归属表**（唯一 owner、并发/线程场景、与代码现状核对、是否触碰 Domain 零依赖红线）后再送审。
加载 `ios-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + `.trellis/spec/guides/golden-path.md` + `.trellis/spec/conventions/project-conventions.md`。
概要必含**归属表 + 三问 + 承接索引**：
- **归属表**：每个待建/改动单元 → doc_type（限七类）→ owner 层（UI/App/Domain/Infrastructure）→ 落地文件路径；每行通过分层依赖律自检（依赖方向 Domain→App→Infrastructure→UI 单向、Domain 零依赖、View 不直连持久化/网络、View 间不直接导航）。
- **三问**：① 改动触达哪几层？② 是否新增/改动 Domain 契约（实体/`enum Error`/`IXxxRepository`）？③ 是否引入新外部依赖或新 `Container+*` DI 装配？
- **承接索引**：逐文件列出"由哪个 BHV 驱动、对应哪个 doc_type、详细阶段在哪展开"，作为详细阶段 directory_precheck 的输入。
**full 链**：建立设计包骨架（`README.md` + `design-main.md` + `chapters/`），把包路径写入 task.json `design_package`，产出 `design-main.md` 概要主定义（含架构就绪自检与逐文件承接索引）；任务内 `design.md` 写指针+摘要。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`，该 supervisor action 必须在 write/repair 后运行 overview review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `ios-design-overview-review` 做 clean-context Codex review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录，不能先进入下一阶段。当前 digest 两个不同 `run_id` 的 Codex clean 后自动进入 1.4；不得运行 `--adversarial` 或启动 opposite-provider worker。`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。**归属违反分层依赖律 = 直接 fail**（不放行、回本步重排归属）。

#### 1.4 详细设计 `[required · repeatable]`

加载 `ios-design-detail-writing`，按概要承接索引展开详细设计（逐 doc_type **合同八问**），并产出 `implement.md`（trace §1 计划）。
**合同八问**（每个 `UNIT-<slug>` 必答，深度对标 L2 文件 `detail-type-viewmodel/usecase/repository.md`）：
1. 正向生成动作 —— 这个单元正常路径做什么（输入→编排→产物）；
2. 边界与不变量 —— 参数边界、`enum Error` 分支、Domain 不变量、`@MainActor`/线程约束；
3. 产物合同 —— 对外暴露的接口/`@Published` 状态/`IXxxRepository` 方法签名/`Container+*` 工厂键；
4. 依赖与归属 —— import 哪几层、DI 如何 `@Injected`、是否守住分层依赖律（自证不违红线）；
5. 可验证信号 —— 用什么 `swift test`/`xcodebuild test` 断言成功（断言点、mock 边界，配合 Mockolo/手写 mock）；
6. 好例子 / 坏例子 —— 至少一组对照（如 ViewModel 直连 WCDBSwift = 坏例 / 经 UseCase→Repository = 好例）；
7. 不适用场景 —— 明确本单元**不**承担什么（如 `view` 不做业务编排、`usecase` 不持 UI 状态）；
8. Gate 判定 —— 本单元过详细 Gate 的判据（合同字段齐全、归属合法、可验证信号可执行）。
**full 链**：directory_precheck（design-main 承接索引存在且非空，否则回退概要）→ chapter_loop **逐章/小批次**生成 `chapters/<slug>.md`（禁止一次性全量输出）；命中 pending L2 类型（`domain-model`/`view`/`coordinator`/`external`）须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2（gate 拦截）。
**详细 Gate**：当前 digest 两个不同 `run_id` clean 后，连同 current requirements、critical/high risk 与关键不可逆设计决定形成 Full 唯一确认批次；确认后不得再以 requirements/detail/commit 拆分询问。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` 回 1.3，`DETAIL_DEFECT` / `PROCESS_DEFECT` 修复后重审。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru iOS 必含条目**（各带 reason）：本任务涉及的 `harness/` SSOT 文件（含命中的 `detail-type-*.md` L2）、`.trellis/spec/guides/golden-path.md`、`.trellis/spec/conventions/project-conventions.md`。涉及持久化时追加 WCDBSwift / DatabaseManager 约定条目；涉及导航时追加 AppCoordinator / `Container+Coordinators` 条目。inline 平台跳过。

#### 1.6 激活任务 `[required · once]`

Full/high-risk 前置 = current requirements/risk/design 批次已确认、overview/detail 当前 digest 双 clean，且 `guru_gate.py check-start <task_dir>` 通过。`START_READY` 后必须运行 `python3 .trellis/scripts/guru/guru_task.py start <task-dir> --slice <id> --gate-digest <sha256> --slice-packet-digest <sha256> --risk-packet-digest <sha256> --envelope-digest <sha256> --attestation-digest <sha256>`。Lite 在 compact requirements 确认 current 后自动 start。

#### 1.7 Full planning 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + route-aware requirements review clean/current（Lite 不适用该 Full Gate） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review；归属表无分层律违规 | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review + current requirements/risk/design 已一批确认 | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + golden-path + iOS 项目约定条目 | ✅（inline 平台除外） |
| Full/high-risk 的 `guru_task.py start` guarded activation 已验证；Lite 不适用 | ✅ |

---

## Phase 2 / Phase 3 步骤细则

Lite 在一次当前 requirements digest 确认后自动 host-inline 实现并运行 focused check 与 scoped deterministic_final，Worker 0、无 Overview/Detail planning review。随后自动追加 mutable evidence、同步 Spec 并进入可逆 commit-ready。以下 2.1/2.2 的 `check-implementation`、dispatcher 和 Worker 协议仅适用于 Full。

Full 与 Trellis 原版同构（dispatch 协议、guarded commit 与 finish-work 收尾不变），但 unchanged scope 不得再拆分 requirements/detail/commit 用户确认：

**Full/high minimum-stable slice lifecycle（Agent planning SSOT）**：

- `Design UNIT` 只负责需求、行为和 invariant 追溯；`Implementation Slice` 才是独占修改、focused validation、review、commit 与 rollback 单元。多个 Design UNIT 可合并进一个 Implementation Slice，但 packet 继续只保留一个真实 `owner_unit`，其余写入 `implement.md.covered_units`；禁止按 UNIT、设计章节、doc_type 或技术层机械生成 slice。
- 所有四端都遵循 delivery policy 的同一组 Agent-only 默认值：`full_high_default_strategy=minimum_commit_stable_parallel_first`、`max_ordinary_slices=4`、`mutable_path_overlap=0`、`review_context_target_bytes=262144`、`ordinary_depends_on_default=[]`、`single_integration_slice=true`、`formal_evidence_control_worktree=serial`。Detail 应先冻结接口、schema、digest、错误语义和共享数据结构；共享 mutable path 必须重新分配唯一 owner 或合并，资源锁与 focused test 修改范围必须隔离、分波次或触发合并。
- `guru_supervise.py implement-slices ... --dry-run` 只输出 dispatch plan/brief，不启动 sub-agent，也不是实际 spawn 或 writer-parallel 的证明。完整 packet 集可能因 Integration coverage overlap 被当前 `slice-plan` 保守标为 serial；coordinator 必须回读 Detail planning audit，只派发 ownership 不重叠、`depends_on=[]` 且工具资源可隔离的 ordinary Implementation Slices。
- ordinary implementation 可以并发，但同一 snapshot 只启动一个 semantic reviewer；正式 staged review、commit 与 receipt 只在唯一 control worktree 串行收口。最后才运行唯一 `Integration Slice`，由它执行跨 slice invariants、full regression 和最终组合验证；Integration packet 的普通 target union 只是 review coverage，不授予重写 ordinary owner 核心字节的权限。Small、Micro、Lite、non-Full 和 v1 lifecycle 不受此策略影响。

#### 2.1 实现 `[required · repeatable]`

进入本节的最低硬条件是 `python3 .trellis/scripts/guru/guru_gate.py check-implementation <task-dir>` 通过；`guru_supervise.py implement|check|implement-check` 会在启动 worker 前自动执行该 gate，`planning` 状态一律 fail-closed。

dispatch-mode aware：主会话第一步先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto`，不得直接凭 `codex.dispatch_mode` 手工选择后端；该命令只产生 dispatch plan/brief，实际 spawn 必须由 coordinator 另行执行并留存 dispatch 记录。执行必须以 dry-run 报告的 `selected_backend`、`decision`、`dispatch_items`、`dispatch_now`、`deferred_slices`、`downgrade_reasons` 为准。`selected_backend=sub-agent` 时按返回的 `trellis-implement` brief 派发平台 sub-agent（prompt 第一行必须是 `Active task: <path>`，worker 已是被调度者，且不得再嵌套 spawn implement/check）；`selected_backend=channel` 时才使用官方 channel worker / `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task-dir>` plan；`selected_backend=inline` 时串行手工执行返回命令，并先加载 `trellis-before-dev` 读当前任务产物、`conventions/project-conventions.md`、`guides/golden-path.md` 与相关 harness SSOT（含命中的 `detail-type-*.md`）。`decision=serial|blocked` 必须按 `downgrade_reasons` 串行执行或停下处理，不得强行并行；只派发 `dispatch_now`，`deferred_slices` 留待后续轮次。helper 只注入存在的 `implement.jsonl`、任务产物和 `ios-implementation-guru-writing` skill，等待后端的 done/error/killed 或平台 final status。编码按 `ios-implementation-guru-writing` 口径，实现 Detail-approved Implementation Slice 覆盖的最小完整行为；`domain-model` → `repository` → `usecase` → `viewmodel` → `view` 只是合同与实现顺序，`coordinator`/`external` 仍作横切，但不得按 ViewModel、UseCase、View、doc_type 或技术层机械拆片。执行/验证证据写入 task-local mutable evidence，不把 `implement.md` 当作 detail 确认后的可变证据文件。
golden-path 硬约束逐片落实：FactoryKit `@Injected` 注入（禁手动 init 依赖）、Repository 接口在 Domain 实现在 Infrastructure、`enum Error` 分层、ViewModel `ObservableObject`+`@Published`、private 方法置于 `private extension`、持久化只走 WCDBSwift。发现设计缺口停下回 Phase 1 修订，不在代码里绕过设计语义。

#### 2.2 质检 `[required · repeatable]`

dispatch-mode aware：`sub-agent` 模式 dispatch `trellis-check`（prompt 第一行必须是 `Active task: <path>`，且不得再嵌套 spawn check/implement）；`channel` 模式才运行 `python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>` 并可读 `trellis channel messages --raw`；`inline` 模式加载 `trellis-check`。helper 只注入存在的 `check.jsonl`、任务产物和 `ios-implementation-guru-review` skill，等待后端结果。按 `ios-implementation-guru-review` 口径审核（实现 trace 四节对齐）：需求/设计/实现合同一致性、**分层依赖律**（import 方向、Domain 零依赖、View 不直连持久化/网络、View 间不直接导航）、**DI canonical**（`@Injected` + `Container+*` 工厂，无手动初始化）、doc_type 归属与七类台账一致、项目约定槽位取值、`enum Error` 分层、合规红线（隐私清单/ATT/内购）与验证证据。无 `swift build` / `swift test`（或 `xcodebuild test`）/ lints 证据不得进入 commit。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（review + 用户 confirm）；不得在代码里绕过设计语义或下游补造 owner/合同/归属。

#### 3.1 质量验证 `[required · repeatable]`

复跑与变更范围匹配的验证命令（`swift build`、`swift test` 或 `xcodebuild -scheme <Scheme> test`，按需 SwiftLint），确认 `verification-evidence.jsonl`（或等价 task-local mutable evidence）已记录命令、结果与说明。若必须修改 `implement.md`，视为主动返回 detail Gate。验证失败回 2.1/2.2；验证缺失不得进入 3.3。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前先运行 `python3 .trellis/scripts/guru/guru_gate.py commit-plan [task-dir]` 获取机器可读 JSON，按其中 `route`、`commit_mode`、`allowed_stage_paths`、`forbidden_stage_paths`、`can_commit_now`、`split_required`、`blocking_reasons` 汇报 staged scope 和建议切分；计划可提交时仍必须通过 `python3 .trellis/scripts/guru/guru_gate.py check-commit <task-dir>` 或等价 PreToolUse hook。

若实现已发生但缺有效合同，且 staged scope 是低风险 scoped implementation diff，commit-plan 必须进入 post-implementation route recovery：阻断 direct commit，只推荐创建/切换 `micro_task` 并运行 `init-contract --route micro_task --risk low`，不得倒逼补 full PRD / overview / detail。

提交前展示 `commit-plan` 摘要、`swift build`/`swift test` 验证证据与建议 commit 切分。若 commit 已包含在当前 Lite/Full 唯一确认批次或用户初始指令中，则通过 Gate 后自动执行；否则停在可逆 commit-ready，不消耗第二次需求确认。不 amend、不 push；只处理本任务相关文件，不回滚用户改动。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
