# Guru Client Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核（verify 强制）。**
> 规则唯一真源：`.trellis/spec/`（guru-flutter-client spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — requirements 已确认、overview/detail 当前 digest 双 clean（默认各含至少一次 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 已确认后才能 `task.py start`（before_start 钩子强制校验）
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
- **Guru Gate 机制**：planning 只保留 `requirements` 与 `detail` 两个人工确认；`overview` / `detail` 的设计 review 证据写入 `task.json.guru_gates.review_runs`，完整模型见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。通道按 config `guru.gate_mode`（**本节是通道唯一主定义**）：
  - `requirements`：结构 Gate 通过后按 route 选择默认 review。`full_chain` 且 `guru.supervision.adversarial_enabled=true` 时运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>` 做 opposite-provider 需求 review；`full_chain` 且配置为 false 时不默认 spawn adversarial worker，但仍要求当前 digest clean/current requirements review；`lite_task` 走 bounded requirements path，adversarial requirements review 可选；`micro_task` / `small_inline` 默认不做 task-local requirements adversarial review（若后续需要 commit，先创建/路由有效 contract）。`route_class=REQ_BLOCKER` 回需求修订并使下游 overview/detail 证据在需求 digest 变化后重跑，`review_result=clean/requirements-ready` 后才停下等待用户运行 `guru_gate.py confirm requirements <task_dir>`。requirements review 不使用 review-evidence Gate、不写 review_runs；`confirm requirements` / `check-start` 必须硬要求当前 digest clean/current requirements review，missing/deferred/blocked/stale 不得人工越过。需求发现阶段内置 Domain Grill，不再要求 post-draft grill Gate。
  - `overview`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（默认至少一条 reviewer 含 `adversarial`，通常由 `guru_supervise.py --adversarial overview` 的 opposite provider 记录；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean）后自动通过；`confirm overview` 必须失败。
  - `detail`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（默认至少一条 reviewer 含 `adversarial`，通常由 `guru_supervise.py --adversarial detail` 的 opposite provider 记录；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean）后，用户运行 `guru_gate.py confirm detail <task_dir>`。
  - 配置 `guru.supervision.adversarial_enabled: false` 可临时关闭 `--adversarial` 的 opposite-provider worker；gate 会动态读取该配置：requirements 不再强制 opposite-provider adversarial clean，overview/detail 不再要求 adversarial reviewer，但仍要求当前 digest、双 clean review、用户确认以及没有 blocked/medium+ 当前证据。
  - route-aware review policy 只放宽 adversarial 证据要求：`small_inline`/`micro_task` 不要求 requirements adversarial review；`lite_task` 采用 bounded review policy（requirements adversarial 可省略，overview/detail 仍要当前 digest 双 clean，但不强制 adversarial reviewer）；`full_chain` / `risk=unknown` / 缺失或非法 contract 保持 strict 路径，且仅当 `guru.supervision.adversarial_enabled=true` 时默认要求 requirements adversarial review。当前 digest 的 blocked、malformed、medium+ evidence 仍硬阻断。
  - **strict（默认）**：用户本人在交互式终端运行 `python3 .trellis/scripts/guru/guru_gate.py confirm requirements|detail`；agent 经工具运行因无 TTY 被拒。
  - **soft**：用户在对话中明确确认后，agent 运行 `guru_gate.py confirm requirements|detail --via-agent --user-quote "<用户确认原话>"` 代跑（`--user-quote` 必填，留痕标注 soft/agent + 用户原话）；**未获用户本轮明确确认不得执行**。
  - 进度用 `guru_gate.py status <task_dir>` 查；最终以 `guru_gate.py check-start <task_dir>` 作为 `task.py start` 前强制复查。
  - `check-start` 成功只产生 `START_READY`：下一步仅可运行 `task.py start`；实现/质检 worker 另由 `check-implementation` 要求 `task.json.status == in_progress`，提交另由 `check-commit` 校验 staged scope 与 implementation review。
- **风险路由合同**：收到任务后先收集任务/路径/差异证据并输出推荐 route。固定推荐表为 `low -> small_inline`、`low + commit -> micro_task`、`medium -> lite_task`、`high -> full_chain`。`gate-contract.json` 与 `gate-degradations.jsonl` 均位于任务目录；前者记录本任务 selected route、recommended route、route_selection 审计与 gate 条件，后者只能记录真实发生的 gate/tool 失败和补偿检查，是事实证据，不是预授权。非高风险 work 可在合法 user override 审计后选择受支持的较轻 route；高风险 work 的 override 只记录用户偏好，不能授权 `lite_task` 或 `micro_task`，Gate 必须要求 `full_chain`。route policy 只能放宽 adversarial 证据要求，不能绕过结构 Gate、人工确认、当前 blocked/medium+ 证据、staged scope 或 implementation review digest。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：风险 route 由 Request Triage 与任务目录 `gate-contract.json` 表达，不替换 Trellis `status`，也不替换 task.json `guru_chain`。`guru_chain` 仍只表达既有 Guru 产物形态（创建时 after_create 默认 `full`；`full=完整五阶段链`，`light=轻量链`）。

- `low -> small_inline`：局部 UI / 文案 / 注释 / 格式 / 非共享配置等低风险小改，且无高风险信号时，本轮 inline 处理，默认不创建完整 task。
- `low + commit -> micro_task`：低风险小改一旦需要 commit，必须创建或复用最小任务，并写入 `gate-contract.json` 承载 scoped commit contract。
- `medium -> lite_task`：局部业务行为、单层逻辑、小范围多文件或需要可复跑验证的变更，进入 lite route（产物形态仍复用既有 `guru_chain=light`）。lite route 使用 bounded review policy：低严重度措辞 nit / P3 follow-up 不强制刷新 PRD digest 或重跑 requirements review；一旦改变范围、行为、验收或命中高风险信号，必须停下请用户确认扩 scope 或升级 full，不得把 `evidence_ready` 静默改成 `user_confirmed`。
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

- 收到实现类需求时先做可审计分流：不要要求用户自己说 `full/lite/micro`；由 agent 按触达层级、风险与提交需求给出推荐。非高风险可在合法审计下 override，高风险不得降为 lite/micro。
- 若当前已有 active task 但新需求可能完全不同，先确认任务归属或新建任务；需要提交的微小改动在任务确定后用 `guru_gate.py init-contract` 写 `gate-contract.json`，避免污染当前任务。
- 简单对话/低风险小改：先分类请求。`low -> small_inline` 自动 inline 处理，默认不创建完整 Trellis task；如果用户要求 commit，则升级为 `low + commit -> micro_task`，创建或复用最小任务并写入 `gate-contract.json`。
- 进入任务后第一步加载 `client-small-iteration-dev` 的入口决策树：判定碰哪几层（只文案→l10n 路径；只接口→network+data；整页 feature→全链）、风险等级与 route。
- 固定推荐表：`low -> small_inline`、`low + commit -> micro_task`、`medium -> lite_task`、`high -> full_chain`。`unknown` 不得降为 low；扫描失败至少按 medium，含高风险关键词或路径信号时推荐 high/full_chain。
- **核心玩法 / 付费 / 广告 / 存档或持久化状态 / 权限 / 隐私或数据采集 / DB 或 schema / workflow、hook、gate、runtime / 跨层协议 / 发布交付链 → 默认推荐完整五阶段（full 链，目录级设计包）**。判轨结论落任务目录 `gate-contract.json`；非高风险选择更轻 selected route 时必须写入 `route_selection` 风险确认审计；高风险请求更轻 route 只能记录偏好，不能绕过 `full_chain`，`guru_chain` 保持既有 full/light 产物语义，不作为降级授权。
- 建任务许可 ≠ 实现许可：实现必须等 requirements 确认、overview/detail 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 确认后 `task.py start`。

[workflow-state:no_task]
无任务：先分类请求并征得建任务同意。低风险可 small_inline；commit 需 micro_task contract；中风险 lite_task；高风险 full_chain；选择较轻 route 必须记录 route_selection。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + 项目约定）
- 1.6 激活任务 `[required · once]`（review evidence + detail confirm → `task.py start`）
- 1.7 完成判定

[workflow-state:planning]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=route-aware req review+confirm→overview/detail 双 clean（full+配置开启含 adversarial；lite 不强制）→detail confirm；jsonl 齐后 start。
[/workflow-state:planning]

[workflow-state:planning-channel]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=route-aware req review+confirm→overview/detail 双 clean（full+配置开启含 adversarial；lite 不强制）→detail confirm；主会话跑 guru_supervise。
[/workflow-state:planning-channel]

[workflow-state:planning-sub-agent]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=route-aware req review+confirm→overview/detail 双 clean（full+配置开启含 adversarial；lite 不强制）→detail confirm；legacy sub-agent 用 Active task。
[/workflow-state:planning-sub-agent]

[workflow-state:planning-inline]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=route-aware req review+confirm→overview/detail 双 clean（full+配置开启含 adversarial；lite 不强制）→detail confirm；inline 先 trellis-before-dev。
[/workflow-state:planning-inline]

### Phase 2: Execute（实现阶段）

- 2.1 实现 `[required · repeatable]`
- 2.2 质检 `[required · repeatable]`
- 2.3 回退 `[on demand]`

[workflow-state:in_progress]
实现→质检→spec回写→commit→finish。默认用官方 trellis channel：主会话运行 guru_supervise.py implement-check（或拆分 implement/check / 等价 create/spawn/send/wait/messages），等待 done/error/killed，失败先读 messages --raw；worker 不 commit/push/merge。无 analyze/test 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress]

[workflow-state:in_progress-channel]
实现→质检→spec回写→commit→finish。channel：主会话运行 guru_supervise.py implement-check（官方 trellis channel；必要时拆分 implement/check），注入存在的 jsonl/任务产物/Guru skill，等待 done/error/killed，失败先读 messages --raw 和 log；worker 不 commit/push/merge。
[/workflow-state:in_progress-channel]

[workflow-state:in_progress-sub-agent]
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
4. 风险路由固定为 `low -> small_inline`、`low + commit -> micro_task`、`medium -> lite_task`、`high -> full_chain`。轻量链允许 prd 简版 + 仅所碰层的 design 合同，但 Gate 口径不降；`gate-degradations.jsonl` 只记录事实证据，不授权绕过。

### Active Task Routing

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `client-design-overview-writing` / `client-design-detail-writing`；Gate 判定 → 对应 `*-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements review 默认按 route：full_chain+配置开启才运行 `guru_supervise.py --adversarial requirements`，lite bounded 可选，micro/small 默认不跑；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → 默认运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task>`（必要时拆分 implement/check）（官方 `trellis channel`，注入 flutter implementation/review skill）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements review 默认按 route：full_chain+配置开启才运行 `guru_supervise.py --adversarial requirements`，lite bounded 可选，micro/small 默认不跑；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → legacy dispatch `trellis-implement` / `trellis-check`（guru 口径），prompt 以 `Active task: <path>` 开头。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements review 默认按 route：full_chain+配置开启才运行 `guru_supervise.py --adversarial requirements`，lite bounded 可选，micro/small 默认不跑；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- 编辑前 → `trellis-before-dev`；编辑后 → `trellis-check`（guru 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待 requirements 确认、overview/detail 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 确认后的 `task.py start`。
- 阶段跃迁必须经 `guru_gate.py confirm` 人工收口（strict=用户终端；soft=用户**本轮对话明确确认**后 agent 以 `--via-agent --user-quote "<用户原话>"` 代跑）；不得以自写 review 记录或机器检查通过替代；soft 下未获用户确认即代跑属违规（记录留痕可审计）。
- 合规 STOP：任何可能违反 App Store / Google Play 政策或美国法规的不确定性 → 立即停止，输出风险点+替代方案+人类确认清单。
- 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有验证证据。
- 产物语言中文优先（英文仅限标识符/命令/路径/协议字段/专有名词/缩写/原文引用）；面向用户的提问与结论一律中文。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。
after_create 钩子默认写入 `guru_chain: full` 和保守 `full_chain` contract。按 Request Triage 判定 selected route：`low -> small_inline` 默认不建完整 task；`low + commit -> micro_task` 创建或复用最小任务并写入 `gate-contract.json`；`medium -> lite_task` 可按既有轻量链产物形态使用 `guru_chain: light` 并记录理由；`high -> full_chain` 是强制提交合同；用户明确选择更轻 route 时只能通过 `route_selection` 记录风险确认，不能按较轻 selected route 执行。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包草稿**（项目 docs 需求目录；版本化组织见 `.trellis/spec/harness/requirements/versioned-requirements-package.md`：外层按 `versions/<version>/` 隔离、内部沿用 requirement-doc-standard、变更走 `changes/change-log.md` 不按日期目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 的 one-question loop 仍是高风险产品/范围/风险确认合同；`requirement-writing` 只能生成 `ai_drafted` / `evidence_ready` / open questions，不得绕过用户逐项确认。
**light 链**：加载 `trellis-brainstorm` 探索需求，直接产出 `prd.md`。
两轨 `prd.md` 口径一致：必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（默认一次只问用户 1 个最高优先级问题；仅当用户当前消息明确要求“批量确认/一次性确认/这几个都按推荐处理”等覆盖多个 OQ/decision id 时，才可列出 2~4 个并逐项记录确认；模糊“继续/好/按推荐”回退为单个 next_question，其余保持 open）。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：上述五要素缺一 → 留在本步修订。结构过后（`guru_gate.py requirements <task_dir>` 通过），按 route 选择 review 默认：`full_chain + guru.supervision.adversarial_enabled=true` 运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>`；`full_chain + adversarial_enabled=false` 不默认 spawn adversarial worker，但其余 strict gate 不降；`lite_task` 走 bounded requirements path，adversarial requirements review 可选；`micro_task`/`small_inline` 默认无 task-local requirements adversarial review（commit 前必须路由/创建有效 contract）。requirements review 如运行，必须先查 `prd.md`、正式需求包、task context 与 repo evidence；medium+ 需求阻断输出 `route_class=REQ_BLOCKER` 并留在 1.1 修订，需求 digest 变更后下游 overview/detail 证据需重跑；低严重度措辞 nit 不阻断；clean 输出 `review_result=clean/requirements-ready`。requirements review 不使用 review-evidence Gate、不写 review_runs、不代替人工确认；默认只有 clean/current 后才允许 **confirm 人工收口**（通道按 gate_mode，见 Trellis System 节），missing/deferred/blocked/stale 均硬阻断；配置关闭只动态放宽 adversarial review 要求，当前 digest 已有 blocked 或 medium+ 证据仍硬阻断。确认落盘后方可进 1.3。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。

#### 1.3 概要设计 `[required · repeatable]`

归属有争议时在 overview review/fix loop 内逐行核对归属表（唯一写 owner、并发场景、与代码现状核对）后再送审。
加载 `client-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + golden-path + 项目约定。
**full 链**：建立设计包骨架（`README.md` + `design-main.md` + `chapters/`），把包路径写入 task.json `design_package`，产出 `design-main.md` 概要主定义（含架构就绪自检与逐文件承接索引）；任务内 `design.md` 写指针+摘要。
**light 链**：产出 `design.md` **§1 概要设计**。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`，该 supervisor action 必须在 write/repair 后运行 overview review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `client-design-overview-review` 做 clean-context review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录，不能先进入下一阶段。当前 digest 两个不同 `run_id` clean 后自动进入 1.4；默认还要求至少一次 reviewer 含 `adversarial`，缺 adversarial 时运行 `guru_supervise.py --adversarial overview <task_dir>`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean，不要求 adversarial reviewer。`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。归属违反分层依赖律 = 直接 fail。

#### 1.4 详细设计 `[required · repeatable]`

加载 `client-design-detail-writing`，按概要承接索引展开详细设计（逐 doc_type 合同八问），并产出 `implement.md`（trace §1 计划）。
**full 链**：directory_precheck（design-main 承接索引存在且非空，否则回退概要）→ chapter_loop **逐章/小批次**生成 `chapters/<slug>.md`（禁止一次性全量输出）；命中 pending L2 类型须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2（gate 拦截）。
**light 链**：展开 `design.md` **§2 详细设计**（单文档多章节）。
**详细 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py detail <task_dir>`，该 supervisor action 必须在 write/repair 后运行 detail review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `client-design-detail-review` 做 clean-context review，并用 `guru_gate.py record-review detail <task_dir> ...` 记录，不能先请求用户确认。当前 digest 两个不同 `run_id` clean 后停下等待 `guru_gate.py confirm detail <task_dir>`；默认还要求至少一次 reviewer 含 `adversarial`，缺 adversarial 时运行 `guru_supervise.py --adversarial detail <task_dir>`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean，不要求 adversarial reviewer。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` 回 1.3，`DETAIL_DEFECT` / `PROCESS_DEFECT` 修复后重审。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru 必含条目**：本任务涉及的 `harness/` SSOT 文件、`guides/golden-path.md`、`conventions/project-conventions.md`（各带 reason）。inline 平台跳过。

#### 1.6 激活任务 `[required · once]`

前置 = requirements 已确认、overview/detail 当前 digest 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 已确认（`guru_gate.py check-start <task_dir>` 通过）。这只代表 `START_READY`，然后运行 `task.py start <task-dir>`；before_start 钩子会再次强制校验，缺 evidence/缺确认直接失败。`START_READY` 不授权实现、质检 worker、git commit 或发布；此时运行 `guru_gate.py status <task_dir>` 按最早缺口恢复，禁止绕过。

#### 1.7 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + route-aware requirements review clean/current（full_chain 且配置开启要求 adversarial clean/requirements-ready；lite bounded 不强制 adversarial）+ 用户 confirm requirements（full 链含正式需求包 review 通过） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review（默认至少一条 reviewer 含 adversarial；配置关闭时只要求双 clean；full=design-main.md；light=design.md §1） | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review（默认至少一条 reviewer 含 adversarial；配置关闭时只要求双 clean）+ 用户 confirm detail（full=chapters/ 闭合；light=design.md §2） | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + 项目约定条目 | ✅（inline 平台除外） |
| `task.py start` 已执行（before_start 校验通过） | ✅ |

---

## Phase 2 / Phase 3 步骤细则

与 Trellis 原版同构（dispatch 协议、commit 批量确认流程、finish-work 收尾不变），仅口径替换：

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

提交前展示 `commit-plan` 摘要、验证证据与建议 commit 切分，等待用户确认；不 amend、不 push；只 stage 本任务相关文件，不回滚用户改动。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
