# Guru Client Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核（verify 强制）。**
> 规则唯一真源：`.trellis/spec/`（guru-flutter-client spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — Full/high-risk 必须先完成 current requirements/risk/design evidence 与一次批量确认，再通过 `guru_task.py start` 的 digest-bound guarded activation；Lite 使用官方标准 task、task-local compact `prd.md` 与一次需求确认，不继承 Full 的 Overview/Detail planning Gate
2. **Specs injected, not remembered** — 规则经 jsonl/hook 注入，不靠记忆
3. **Persist everything** — 研究、决策、trace 全部落文件
4. **Gate 不过不进下一阶段** — 缺陷只能回上游阶段修，禁止下游补造
5. **Capture learnings** — 任务完成按萃取九段结构回写 spec

---

## Trellis System（机制速查）

开发者身份、任务生命周期命令、workspace journal、`get_context.py` 用法与 Trellis 原版一致（`python3 ./.trellis/scripts/task.py --help` 为权威清单），此处不复述。

**Guru 关键差异**：

- `.trellis/spec/` 使用 guru-flutter-client spec 库：`harness/`（五阶段 SSOT）、`guides/golden-path.md`、`conventions/`（项目约定槽位）。入口与阶段映射见 `.trellis/spec/harness/index.md`。
- 任何阶段开始前必须通过 `.trellis/spec/conventions/project-conventions.md` 的校验清单 C1~C5（缺失/未填 = 硬前置失败，先补约定）。
- 三条最高禁令（违反即任务失败）：① 禁止执行 l10n 同步脚本（SLOT-07，人工受控）② 禁止在 SLOT-12 老目录新建业务模块 ③ 禁止违反分层依赖律的 import。
- **Guru Gate 机制**：Small/Micro/Lite/Full 的确认预算固定为 `0/0/1/1 batch`。Lite 的一次确认绑定 task-local `prd.md` digest、route、risk 与 `scope_fingerprint`；Full 在实现 Worker 前把 current requirements、critical/high risk 与关键不可逆设计决定合并为一批确认。`overview` / `detail` review 证据写入 `task.json.guru_gates.review_runs`，完整模型见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。通道按 config `guru.gate_mode`（**本节是通道唯一主定义**）：
  - `requirements`：结构 Gate 通过后按 route 选择默认 review。Full requirements review 只产出 current `requirements-ready` evidence，不单独请求用户确认；它与 current critical/high risk、关键不可逆设计决定一起进入实现前唯一确认批次。Lite 不进入 Full requirements review，而是对 task-local compact `prd.md` 做一次 digest-bound 确认。`route_class=REQ_BLOCKER` 回需求修订，missing/deferred/blocked/stale 不得进入确认。
  - `overview`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 Codex clean review 后自动通过；不得运行 opposite-provider adversarial worker；`confirm overview` 必须失败。
  - `detail`：结构 Gate通过 + 当前 digest 下两个不同 `run_id` 的 Codex clean review 后，把 current requirements/risk/design 作为一批请求用户确认；不得先做 requirements confirm 再做 detail confirm。
  - Custom 默认 `guru.supervision.adversarial_enabled: false`；这只删除 opposite-provider 前置，当前 digest、双 Codex clean、用户确认以及 blocked/medium+ finding 约束全部保留。
  - route-aware policy 必须匹配 delivery policy：`small_inline`/`micro_task` 不继承 Full planning review；`lite_task` 必须由官方 `task.py create` 创建标准 Trellis task，先查 repo evidence，仅对未解决的产品/范围/失败路径/验收歧义运行 bounded Brainstorm，在 task-local compact `prd.md` 当前 digest 获得一次确认后自动 start、host-inline implementation 与 `deterministic_final`，Worker 0、无 Overview/Detail planning review；`full_chain` / `risk=unknown-high` / 缺失或非法 contract 才保持 strict planning/review 路径。Lite 若出现 high-risk 或 scope expansion，在下一次写入前提升为 Full，不得在 Lite 内补跑 Full Gate。
  - **strict（默认）**：用户本人通过已安装的 route-aware confirmation 入口记录当前 Lite requirements batch 或 Full requirements/risk/design batch；每个 selection generation 最多一批。
  - **soft**：用户在对话中明确确认后，agent 用 `--via-agent --user-quote "<用户确认原话>"` 记录同一批次；`--user-quote` 必填，且 confirmation digest、route、risk、`scope_fingerprint` 必须 current。
  - 进度用 `guru_gate.py status <task_dir>` 查；Full/high-risk 以 `guru_gate.py check-start <task_dir>` 作为 guarded activation 前复查。
  - `check-start` 成功只产生 `START_READY`：Full/high-risk 下一步仅可运行已安装的 `python3 .trellis/scripts/guru/guru_task.py start ...` 并传入当前 gate/slice/risk/envelope/attestation digests；不得把 direct `task.py start` 当作 Full 正常入口。实现/质检 worker 另由 `check-implementation` 要求 `task.json.status == in_progress`，提交另由 `check-commit` 校验 staged scope 与 implementation review。
  - Full 在 detail review/confirm 前必须把按 slice 分组的完整 required critical/high decision universe 写入 `implement.md` 的唯一 `GURU:RISK_DECISION_INVENTORY` JSON fence；精确 schema、resolution evidence 和 Start Guard 重建规则只以 gate SSOT 为准。缺 inventory 或 unresolved 集合非空时不得启动。
- **风险路由合同**：route 难度只由需求清晰度、风险、耦合、可逆性与验证成本决定，commit intent 只是交付动作。Agent 自动推荐满足硬边界的最低成本 route；用户可选择或切换 route。更重 override 直接允许，更轻 override 必须满足目标 eligibility；High-risk/unknown-high 永远保持 `full_chain`。首次仓库写入前可依据新证据合法降级，首次写入后只允许升级。`gate-contract.json` 记录 selected/recommended route、`selection_source`、单调 `selection_generation` 与 `scope_fingerprint`；`gate-degradations.jsonl` 只记录真实失败与补偿检查。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：风险 route 由 Request Triage 与任务目录 `gate-contract.json` 表达，不替换 Trellis `status`，也不替换 task.json `guru_chain`。`guru_chain` 仍只表达既有 Guru 产物形态（创建时 after_create 默认 `full`；`full=完整五阶段链`，`light=轻量链`）。

- `small_inline`：需求明确、机械、低风险且不改变行为合同；默认 inline、无完整 task、确认 0。初始 commit 请求只补最小提交合同，不改判任务难度。
- `micro_task`：需求明确、低风险、路径有界，但改变一个局部行为合同；使用最小 task contract、确认 0 与 focused check。
- `lite_task`：无 High-risk 的局部行为变更；官方创建标准 Trellis task，在任务目录维护 compact `prd.md` 与 Brainstorm evidence。repo evidence 后仍有产品/范围/失败路径/验收歧义时才进入 bounded Brainstorm；确认当前 requirements digest 一次后自动 start、host-inline、focused check、mutable evidence、Spec 同步与可逆 commit-ready，Worker 0、无 Overview/Detail planning review。
- `high -> full_chain`：核心玩法 / 付费 / 广告 / 存档或持久化状态 / 权限 / 隐私或数据采集 / DB 或 schema / workflow、hook、gate、runtime / 跨层协议 / 发布交付链，默认推荐 full 链；即使用户要求 `lite_task` 或 `micro_task`，合同也必须保持或升级为 `full_chain`；`route_selection` 只能记录偏好和风险确认，不能作为降级授权。

`gate-degradations.jsonl` 只能追加真实降级事实：失败命令、stderr 摘要、影响 gate、允许依据、补偿检查与操作者。它不能预先写作绕行许可，也不能扩大 `gate-contract.json` 和全局 gate policy 的权限。命中 high 后必须执行 `full_chain`；若用户请求更轻 route，可由 `gate-contract.json.route_selection` 记录推荐值、用户偏好和风险确认，但 validator 必须拒绝非 `full_chain` 合同。

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。full 链另有**正式需求包**（requirement-writing/review，项目 docs 需求目录；版本化组织见 `.trellis/spec/harness/requirements/versioned-requirements-package.md`），prd.md 为其行为规格抽取层。
- 设计产物按链型分轨：
  - **full**：目录级设计包（task.json `design_package` 指向，如 `docs/design/<feature>/`）= `README.md`（导航）+ `design-main.md`（概要主定义，含归属表/承接索引/架构就绪自检）+ `chapters/*.md`（详细设计逐章，directory_precheck + chapter_loop 生成）。任务内 `design.md` 退为指针+摘要。
  - **light**：任务内 `design.md` 两章：**§1 概要设计**（归属表+三问+承接索引）；**§2 详细设计**（逐 doc_type 合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；detail 确认后保持 digest-bearing，不作为执行/验证证据 sink；执行、验证、阻塞偏差写入 task-local mutable evidence（`implementation-evidence.jsonl` / `verification-evidence.jsonl` / `commit-plan.json` / `review-records/implementation-reviews.jsonl`）。
- `implement.jsonl` / `check.jsonl` — spec/research 注入清单（见 1.5）。
- **编号纪律** — 行为 `BHV-NNN`（prd 标题，不复用不重排）、设计单元 `UNIT-<slug>`（design §2 标题）；跨产物引用一律写编号 token。`python3 .trellis/scripts/guru/guru_gate.py trace-matrix <task_dir> [--write]` 随时生成追溯矩阵（含「需求场景（REQ-UC）」列；--strict 断链拦截）。full 链 prd 的 BHV 标题可在短名前以 `[REQ-UC-XXX]`（多对多）承接正式需求包需求源场景（`### BHV-001 [REQ-UC-005] <短名>`），`trace-matrix --require-req-uc`（或 task.json `require_req_uc:true`）强制 BHV 须带 REQ-UC（旧 prd 默认不拦、列空、不断链）；版本级 `guru_gate.py trace-aggregate <version-dir> [--include-completed]` 反查指向某需求包版本目录的 task，把 `(REQ-UC, BHV, UNIT, Source Task)` 行展开聚合进 `traceability.md` 派生列（手维护 Code/Test/Status 按 key 回填保留；fail-closed：manifest `canonical_excludes` 须含 `traceability`）。**命名消歧**：`REQ-UC-XXX`（需求源场景）≠ overview `UC-<序号>`（架构核心用例），两套独立编号。
- **产物语言** — task 产物（prd/design/implement/research、spec 回写、findings）一律**中文优先**；英文仅限代码标识符、命令、文件路径、协议字段、外部专有名词、缩写与原文引用。commit message 跟随仓库历史风格（3.4 步已有学习机制）。

---

## Phase Index

```
Phase 1: Plan    → 需求 Gate → 概要 Gate → 详细 Gate → 激活任务
Phase 2: Execute → 实现（golden-path 迷你路径 + trace）→ 质检（guru 审核口径）
Phase 3: Finish  → 验证 → 萃取回写 spec → commit → 收尾
```

### Request Triage

- 收到实现类需求时先做可审计分流：不要要求用户自己说 `full/lite/micro`；由 Agent 按需求清晰度、风险、耦合、可逆性与验证成本自动推荐最低合法 route。用户可显式选择或切换；更重总是允许，更轻必须满足目标 eligibility，高风险不得降为 Lite/Micro。
- 若当前已有 active task 但新需求可能完全不同，先确认任务归属或新建任务；需要提交的微小改动在任务确定后用 `guru_gate.py init-contract` 写 `gate-contract.json`，避免污染当前任务。
- 简单对话/低风险小改：机械且不改变行为合同走 `small_inline`；明确、低风险、路径有界的局部行为改变走 `micro_task`。commit intent 不改变难度，只决定是否需要最小提交合同。
- 进入任务后第一步加载 `client-small-iteration-dev` 的入口决策树：判定碰哪几层（只文案→l10n 路径；只接口→network+data；整页 feature→全链）、风险等级与 route。
- 固定推荐结果为 `small_inline|micro_task|lite_task|full_chain`；`unknown` 不得伪装成 low，unknown-high 与任何 high-risk 信号必须 `full_chain`。route 选择绑定 `selection_generation` 与 `scope_fingerprint`，首次写入后只允许升级。
- **核心玩法 / 付费 / 广告 / 存档或持久化状态 / 权限 / 隐私或数据采集 / DB 或 schema / workflow、hook、gate、runtime / 跨层协议 / 发布交付链 → 默认推荐完整五阶段（full 链，目录级设计包）**。判轨结论落任务目录 `gate-contract.json`；非高风险选择更轻 selected route 时必须写入 `route_selection` 风险确认审计；高风险请求更轻 route 只能记录偏好，不能绕过 `full_chain`，`guru_chain` 保持既有 full/light 产物语义，不作为降级授权。
- 建任务许可 ≠ 实现许可：Lite 标准 task 必须在 compact requirements 当前 digest 获得一次确认后自动 start；Full/high-risk 必须先暴露 current risk/decision evidence，并在一次批量确认后走 `guru_task.py start` guarded activation。

[workflow-state:no_task]
无任务：Agent 按需求清晰度、风险、耦合、可逆性与验证成本自动推荐最低合法 route；用户可显式切换。Small 默认不建完整 task；Micro 用最小 contract；Lite 必须官方创建标准 task；High-risk/unknown-high 必须 Full。commit intent 不决定难度。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + 项目约定）
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
实现→质检→spec回写→commit→finish。legacy sub-agent：dispatch trellis-implement/check，prompt 以 Active task: <path> 开头；trace 记执行/证据/偏差；质检按 guru 口径，无 analyze/test 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress-sub-agent]

[workflow-state:in_progress-inline]
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 spec，编辑后 trellis-check（guru 口径）；验证证据记 `verification-evidence.jsonl` 等 task-local mutable evidence，无证据不 commit；设计缺陷回 Phase1。
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

### Active Task Routing

**所有平台块的 route 边界**：以 `gate-contract.json.route` 为准。Lite 始终 host-inline + deterministic_final；下文任何 `implement-slices`、implementation Worker 或 planning review 命令都仅适用于 Full。

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `client-design-overview-writing` / `client-design-detail-writing`；Gate 判定 → 对应 `*-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- `in_progress` 实现/质检 → 先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto` 读取 dispatcher plan；按 `selected_backend` 派发，`channel` 仅 `selected_backend=channel` 时使用官方 worker/`implement-check`，`sub-agent` 按返回 brief，`inline` 串行；worker 不嵌套 spawn implement/check、不 commit/push/merge。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- `in_progress` 实现/质检 → 先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto`，只按返回的 `trellis-implement` / `trellis-check` brief 派发（guru 口径，prompt 首行 `Active task: <path>`，worker 不嵌套 spawn implement/check）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；Full 的 requirements/overview/detail review → `guru_supervise.py`；Lite 跳过这些 pre-code review 并保持 host-inline。
- 编辑前 → `trellis-before-dev`；编辑后 → `trellis-check`（guru 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；Full/high-risk 等确认与 current digests 后必须走 guarded wrapper，direct `task.py start` 不是文档化的 Full 入口。
- Lite 与 Full 各只有一次 route-specific confirmation batch：Lite 绑定 compact requirements，Full 绑定 current requirements/risk/design。确认后自动推进；只有 material scope/digest 变化、新 High-risk 或新不可逆决定才重新确认。
- 合规 STOP：任何可能违反 App Store / Google Play 政策或美国法规的不确定性 → 立即停止，输出风险点+替代方案+人类确认清单。
- 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有验证证据。
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
after_create 按 delivery policy 写入 `gate-contract.json.route`，它是执行权威；`guru_chain` 只保留产物兼容信息，禁止用于推导 route。`small_inline` 默认不建完整 task，`micro_task` 使用最小合同，`lite_task` 使用官方标准 task + task-local compact `prd.md`，`full_chain` 才进入正式设计链。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包草稿**（项目 docs 需求目录；版本化组织见 `.trellis/spec/harness/requirements/versioned-requirements-package.md`：外层按 `versions/<version>/` 隔离、内部沿用 requirement-doc-standard、变更走 `changes/change-log.md` 不按日期目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 的 one-question loop 仍是高风险产品/范围/风险确认合同；`requirement-writing` 只能生成 `ai_drafted` / `evidence_ready` / open questions，不得绕过用户逐项确认。
两轨 `prd.md` 口径一致：必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（默认一次只问用户 1 个最高优先级问题；仅当用户当前消息明确要求“批量确认/一次性确认/这几个都按推荐处理”等覆盖多个 OQ/decision id 时，才可列出 2~4 个并逐项记录确认；模糊“继续/好/按推荐”回退为单个 next_question，其余保持 open）。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：上述五要素缺一 → 留在本步修订。Full requirements review 必须先查 `prd.md`、正式需求包、task context 与 repo evidence；medium+ 阻断回 1.1，clean 只产出 current `requirements-ready` evidence 并继续设计，不在本步单独询问用户。Lite 不进入该 Full review path；它在 repo evidence 与必要 Brainstorm 后对 task-local compact `prd.md` 请求唯一一次确认。missing/deferred/blocked/stale 均硬阻断。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。

#### 1.3 概要设计 `[required · repeatable]`

归属有争议时在 overview review/fix loop 内逐行核对归属表（唯一写 owner、并发场景、与代码现状核对）后再送审。
加载 `client-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + golden-path + 项目约定。
**full 链**：建立设计包骨架（`README.md` + `design-main.md` + `chapters/`），把包路径写入 task.json `design_package`，产出 `design-main.md` 概要主定义（含架构就绪自检与逐文件承接索引）；任务内 `design.md` 写指针+摘要。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`，该 supervisor action 必须在 write/repair 后运行 overview review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `client-design-overview-review` 做 clean-context Codex review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录，不能先进入下一阶段。当前 digest 两个不同 `run_id` 的 Codex clean 后自动进入 1.4；不得运行 `--adversarial` 或启动 opposite-provider worker。`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。归属违反分层依赖律 = 直接 fail。

#### 1.4 详细设计 `[required · repeatable]`

加载 `client-design-detail-writing`，按概要承接索引展开详细设计（逐 doc_type 合同八问），并产出 `implement.md`（trace §1 计划）。
**full 链**：directory_precheck（design-main 承接索引存在且非空，否则回退概要）→ chapter_loop **逐章/小批次**生成 `chapters/<slug>.md`（禁止一次性全量输出）；命中 pending L2 类型须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2（gate 拦截）。
**详细 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py detail <task_dir>`，在 write/repair 后记录当前 digest clean。当前 digest 两个不同 `run_id` clean 后，连同 current requirements、critical/high risk 与关键不可逆设计决定形成 Full 唯一确认批次；确认后不得再以 requirements/detail/commit 拆分询问。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` 回 1.3，`DETAIL_DEFECT` / `PROCESS_DEFECT` 修复后重审。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru 必含条目**：本任务涉及的 `harness/` SSOT 文件、`guides/golden-path.md`、`conventions/project-conventions.md`（各带 reason）。inline 平台跳过。

#### 1.6 激活任务 `[required · once]`

Full/high-risk 前置 = current requirements/risk/design 批次已确认、overview/detail 当前 digest 双 clean，且 `guru_gate.py check-start <task_dir>` 通过。`START_READY` 后必须运行 `python3 .trellis/scripts/guru/guru_task.py start <task-dir> --slice <id> --gate-digest <sha256> --slice-packet-digest <sha256> --risk-packet-digest <sha256> --envelope-digest <sha256> --attestation-digest <sha256>`；wrapper 会在调用官方 task lifecycle 前校验 current bindings。官方 Core 的 direct `task.py start` 不能替代该 Full 入口。Lite 在 compact requirements 确认 current 后自动 start。

#### 1.7 Full planning 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + route-aware requirements review clean/current（Lite 不适用该 Full Gate） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review + current requirements/risk/design 已一批确认 | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + 项目约定条目 | ✅（inline 平台除外） |
| Full/high-risk 的 `guru_task.py start` guarded activation 已验证；Lite 不适用 | ✅ |

---

## Phase 2 / Phase 3 步骤细则

Lite 在一次当前 requirements digest 确认后自动 host-inline 实现并运行 focused check 与 scoped deterministic_final，Worker 0、无 Overview/Detail planning review。随后自动追加 mutable evidence、同步 Spec 并进入可逆 commit-ready。以下 2.1/2.2 的 `check-implementation`、dispatcher 和 Worker 协议仅适用于 Full。

Full 与 Trellis 原版同构（dispatch 协议、guarded commit 与 finish-work 收尾不变），但 unchanged scope 不得再拆分 requirements/detail/commit 用户确认：

#### 2.1 实现 `[required · repeatable]`

进入本节的最低硬条件是 `python3 .trellis/scripts/guru/guru_gate.py check-implementation <task-dir>` 通过；`guru_supervise.py implement|check|implement-check` 会在启动 worker 前自动执行该 gate，`planning` 状态一律 fail-closed。

dispatch-mode aware：主会话先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto` 读取 `codex.dispatch_mode` 与 slice-plan；`sub-agent` 模式按返回的 `trellis-implement` brief 派发平台 sub-agent（prompt 第一行必须是 `Active task: <path>`，且不得再嵌套 spawn implement/check）；`channel` 模式才使用官方 channel worker/`guru_supervise.py implement-check` 命令；`inline` 模式串行手工执行。必要时可拆分 `implement` 与 `check`。worker 注入存在的 jsonl、任务产物和平台 implementation writing/review skill，等待后端的 done/error/killed 或平台 final status。**P1 high-risk full_chain slice（packet 机制）**：仅当 selected route 为 `full_chain` 且 risk 为 high 时要求 `--slice <unit_id>`（多 packet 必填，单 packet 自动选）；supervisor 进修复循环前做 packet preflight + scope preflight（packet 缺失/非法/多义 → `PACKET_*`、dirty 越界 packet `target_paths`/`dirty_state.unrelated` → `SCOPE_INVALID`，均硬停 exit2、不启 worker、不进 repairable loop）；每轮 implement 成功后 supervisor 独立执行 packet `deterministic_checks`（绑定本轮 diff，hard Gate）。编码按平台 Guru implementation writing/review 口径：组合需求真正触达的迷你路径，逐片实现；执行/验证证据写入 task-local mutable evidence，不把 `implement.md` 当作 detail 确认后的可变证据文件。发现 `DETAIL_DEFECT` / `OVERVIEW_DEFECT` / `REQ_BLOCKER` 按 Phase 1 回退。

#### 2.2 质检 `[required · repeatable]`

check 可作为 `implement-check` 的拆分子命令运行：`python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>`。审核按平台 Guru review 口径覆盖需求/设计/实现合同一致性、分层依赖律、合规红线与验证证据；无 analyze/test/lints/compliance 证据不得进入 commit。需要只补 commit gate 所需结构化 review record 时，使用 `python3 .trellis/scripts/guru/guru_supervise.py implementation-review <task-dir> --staged`（或 `--slice <unit_id> --staged`），该入口只跑 deterministic checks + check worker，不启动 implement worker，不修改 confirmed detail artifacts。**P1 完成条件（有 packet）**：check worker 置顶输出 7 字段 verdict + 逐条 `invariant_status.*`；clean 须同时满足 **deterministic passed（supervisor 执行 + worker 自报双过）+ invariant_coverage all_passed（supervisor 从 packet invariants 聚合重算）+ dirty_scope clean/isolated + review_provider 满足 packet `semantic_review_provider` + 无 blocker/should-fix**；缺字段或取非通过值却声明 clean → `MALFORMED_REVIEW_OUTPUT` 硬停。**OCR 仅 optional bounded provider**（用户显式触发/高风险抽检），不作默认完成条件；`No comments generated` 不作退出目标。每轮 review 记录由单一 writer 追加 `review-records/implementation-reviews.jsonl`（可审计回放）。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（requirements confirm、overview/detail review_runs、detail confirm 按需失效重跑）；不得在代码里绕过设计语义或下游补造 owner/合同。

#### 3.1 质量验证 `[required · repeatable]`

复跑与变更范围匹配的验证命令，确认 `verification-evidence.jsonl`（或等价 task-local mutable evidence）已记录命令、结果与说明。若必须修改 `implement.md`，视为主动返回 detail Gate。验证失败回 2.1/2.2；验证缺失不得进入 3.3。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前先运行 `python3 .trellis/scripts/guru/guru_gate.py commit-plan [task-dir]` 获取机器可读 JSON，按其中 `route`、`commit_mode`、`allowed_stage_paths`、`forbidden_stage_paths`、`can_commit_now`、`split_required`、`blocking_reasons`、`review_coverage` 汇报 staged scope 和建议切分；计划可提交时仍必须通过 `python3 .trellis/scripts/guru/guru_gate.py check-commit <task-dir>` 或等价 PreToolUse hook。full/lite 的既有 Guru gate 语义不降：full 链要求任务已 `in_progress`，且 staged implementation paths 被当前 clean implementation review set 覆盖（切片 review 集或完整 `--staged` review），不得只信最新一条 review row；lite route 仍需 scoped 验证和 review 证据（产物形态兼容 `guru_chain=light`）。若 commit gate 只缺 required implementation review record，恢复命令是 `guru_supervise.py implementation-review <task-dir> --staged`，能映射 slice 时优先用 `--slice <unit_id> --staged`，不是 `implement-check`。`small_inline` 不能直接 commit；低风险一旦需要 commit 必须走 `micro_task` 并由任务目录 `gate-contract.json` 约束 staged scope。若实现已发生但缺有效合同，且 staged scope 是低风险 scoped implementation diff，commit-plan 必须进入 post-implementation route recovery：阻断 direct commit，只推荐创建/切换 `micro_task` 并运行 `init-contract --route micro_task --risk low`，不得倒逼补 full PRD / overview / detail。`gate-degradations.jsonl` 只可作为真实失败与补偿检查证据，不能预授权跳过 gate；high/full_chain 是推荐与 selected route 组合，用户选择较轻 route 时必须由 `route_selection` 审计承接。

提交前展示 `commit-plan` 摘要、验证证据与建议 commit 切分。若 commit 已包含在当前 Lite/Full 唯一确认批次或用户初始指令中，则通过 Gate 后自动执行；否则停在可逆 commit-ready，不消耗第二次需求确认。不 amend、不 push；只处理本任务相关文件，不回滚用户改动。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
