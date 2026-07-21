# Guru Client Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核；verify 按 route 和 slice role 执行：selected Full/high ordinary 只运行 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 Integration 才运行 project-wide build/analyze/lint/full regression，其他 route 保持既有验证合同。**
> 规则唯一真源：`.trellis/spec/`（guru-flutter-client spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — selected `full_chain` 且 high-risk 必须先完成 current requirements/risk/design evidence 与一次批量确认，再通过 `guru_task.py start` 的 digest-bound guarded activation；Lite 使用官方标准 task、task-local compact `prd.md` 与一次需求确认，不继承 Full 的 Overview/Detail planning Gate
2. **Specs injected, not remembered** — 规则经 jsonl/hook 注入，不靠记忆
3. **Persist everything** — 研究、决策、trace 全部落文件
4. **Gate 不过不进下一阶段** — 缺陷只能回上游阶段修，禁止下游补造
5. **Capture learnings** — 任务完成按萃取九段结构回写 spec
6. **Runtime acceptance is separate** — Full 任务声明 `runtime_acceptance_required=true` 时，技术验证绿只到 `implementation_verified`；所有 required Acceptance Closure Matrix 行获得 current runtime pass 前保持 active，不得报告 `accepted` 或进入 archive

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
  - route-aware policy 必须匹配 delivery policy：`small_inline`/`micro_task` 不继承 Full planning review；`lite_task` 必须由官方 `task.py create` 创建标准 Trellis task，先查 repo evidence，仅对未解决的产品/范围/失败路径/验收歧义运行 bounded Brainstorm，在 task-local compact `prd.md` 当前 digest 获得一次确认后自动 start、host-inline implementation 与 `deterministic_final`，Worker 0、无 Overview/Detail planning review；selected `full_chain` / 缺失或非法 contract 才保持 strict planning/review 路径。Lite 若出现 high-risk 或 scope expansion，下一次写入前重新 intake 并默认推荐 Full；用户可用新的 override audit 保留或选择其他受支持 route，旧确认与证据必须失效。
  - **strict（默认）**：用户本人通过已安装的 route-aware confirmation 入口记录当前 Lite requirements batch 或 Full requirements/risk/design batch；每个 selection generation 最多一批。
  - **soft**：用户在对话中明确确认后，agent 用 `--via-agent --user-quote "<用户确认原话>"` 记录同一批次；`--user-quote` 必填，且 confirmation digest、route、risk、`scope_fingerprint` 必须 current。
  - 进度用 `guru_gate.py status <task_dir>` 查；selected `full_chain` 且 high-risk 以 `guru_gate.py check-start <task_dir>` 作为 guarded activation 前复查。
  - `check-start` 成功只产生 `START_READY`：selected `full_chain` 且 high-risk 的下一步仅可运行已安装的 `python3 .trellis/scripts/guru/guru_task.py start ...` 并传入当前 gate/slice/risk/envelope/attestation digests；不得把 direct `task.py start` 当作 Full 正常入口。实现/质检 worker 另由 `check-implementation` 要求 `task.json.status == in_progress`，提交另由 `check-commit` 校验 staged scope 与 implementation review。
  - Full 在 detail review/confirm 前必须把按 slice 分组的完整 required critical/high decision universe 写入 `implement.md` 的唯一 `GURU:RISK_DECISION_INVENTORY` JSON fence；精确 schema、resolution evidence 和 Start Guard 重建规则只以 gate SSOT 为准。缺 inventory 或 unresolved 集合非空时不得启动。
- **风险路由合同**：route 建议只由需求清晰度、风险、耦合、可逆性与验证成本决定，commit intent 只是交付动作。High-risk/unknown-high 默认推荐 `full_chain`，但用户可选择或切换到任一受支持 route；低于推荐的选择必须记录用户原话与风险确认。`gate-contract.json.route` 是执行权威；每次 route 变更都递增 `selection_generation` 并使旧确认与证据失效。`gate-degradations.jsonl` 只记录真实失败与补偿检查。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：风险 route 由 Request Triage 与任务目录 `gate-contract.json` 表达，不替换 Trellis `status`，也不替换 task.json `guru_chain`。`guru_chain` 仍只表达既有 Guru 产物形态（创建时 after_create 默认 `full`；`full=完整五阶段链`，`light=轻量链`）。

- `small_inline`：需求明确、机械、低风险且不改变行为合同；默认 inline、无完整 task、确认 0。初始 commit 请求只补最小提交合同，不改判任务难度。
- `micro_task`：需求明确、低风险、路径有界，但改变一个局部行为合同；使用最小 task contract、确认 0 与 focused check。
- `lite_task`：默认用于无 High-risk 的局部行为变更；也可由用户在完整 override audit 后显式选择。官方创建标准 Trellis task，在任务目录维护 compact `prd.md` 与 Brainstorm evidence。repo evidence 后仍有产品/范围/失败路径/验收歧义时才进入 bounded Brainstorm；确认当前 requirements digest 一次后自动 start、host-inline、focused check、mutable evidence、Spec 同步与可逆 commit-ready，Worker 0、无 Overview/Detail planning review。
- `high -> full_chain`：核心玩法 / 付费 / 广告 / 存档或持久化状态 / 权限 / 隐私或数据采集 / DB 或 schema / workflow、hook、gate、runtime / 跨层协议 / 发布交付链默认推荐 full 链；用户仍可选择任一受支持 route，低于推荐时由 `route_selection` 记录用户原话与风险确认，后续 Gate 按 selected route 执行。

`gate-degradations.jsonl` 只能追加真实降级事实：失败命令、stderr 摘要、影响 gate、允许依据、补偿检查与操作者。它不能预先写作绕行许可，也不能扩大 `gate-contract.json` 和全局 gate policy 的权限。命中 high 后默认推荐 `full_chain`；若用户请求更轻 route，`gate-contract.json.route_selection` 必须记录推荐值、用户原话和风险确认，validator 校验审计完整性，后续 Gate 按 selected route 执行。

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

- 收到实现类需求时先做可审计分流：不要要求用户自己说 `full/lite/micro`；由 Agent 按需求清晰度、风险、耦合、可逆性与验证成本自动推荐 route。用户可显式选择或切换任一受支持 route；低于推荐的选择必须记录完整 override audit。
- 若当前已有 active task 但新需求可能完全不同，先确认任务归属或新建任务；需要提交的微小改动在任务确定后用 `guru_gate.py init-contract` 写 `gate-contract.json`，避免污染当前任务。
- 简单对话/低风险小改：机械且不改变行为合同走 `small_inline`；明确、低风险、路径有界的局部行为改变走 `micro_task`。commit intent 不改变难度，只决定是否需要最小提交合同。
- 进入任务后第一步加载 `client-small-iteration-dev` 的入口决策树：判定碰哪几层（只文案→l10n 路径；只接口→network+data；整页 feature→全链）、风险等级与 route。
- 固定推荐结果为 `small_inline|micro_task|lite_task|full_chain`；`unknown` 不得伪装成 low，unknown-high 与任何 high-risk 信号默认推荐 `full_chain`。route 选择绑定 `selection_generation` 与 `scope_fingerprint`；每次切换都递增 generation 并使旧确认与证据失效。
- **核心玩法 / 付费 / 广告 / 存档或持久化状态 / 权限 / 隐私或数据采集 / DB 或 schema / workflow、hook、gate、runtime / 跨层协议 / 发布交付链 → 默认推荐完整五阶段（full 链，目录级设计包）**。判轨结论落任务目录 `gate-contract.json`；用户选择低于推荐的 route 时必须写入 `route_selection` 风险确认审计，Gate 按 selected route 执行；`guru_chain` 保持既有 full/light 产物语义，不作为 route 授权。
- 建任务许可 ≠ 实现许可：Lite 标准 task 必须在 compact requirements 当前 digest 获得一次确认后自动 start；selected `full_chain` 且 high-risk 必须先暴露 current risk/decision evidence，并在一次批量确认后走 `guru_task.py start` guarded activation。

[workflow-state:no_task]
无任务：Agent 按需求清晰度、风险、耦合、可逆性与验证成本自动推荐 route；用户可显式切换任一受支持 route。Small 默认不建完整 task；Micro 用最小 contract；Lite 必须官方创建标准 task；High-risk/unknown-high 默认推荐 Full，低于推荐时记录完整 override audit。commit intent 不决定难度。
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
Runtime-required Full: technical green -> `implementation_verified` -> exact runtime probe handoff; latest current pass 不完整时任务保持 active，禁止 archive/`accepted`。
[/workflow-state:in_progress]

[workflow-state:in_progress-channel]
Lite 不进入 channel/Worker 路径；以下 channel 行为仅适用于 Full。
实现→质检→spec回写→commit→finish。channel：主会话运行 guru_supervise.py implement-check（官方 trellis channel；必要时拆分 implement/check），注入存在的 jsonl/任务产物/Guru skill，等待 done/error/killed，失败先读 messages --raw 和 log；worker 不 commit/push/merge。
Runtime-required Full 技术绿后只报 `implementation_verified` 并移交 exact probe；未全部 current pass 时保持 active，不运行 archive。
[/workflow-state:in_progress-channel]

[workflow-state:in_progress-sub-agent]
Lite 不派 sub-agent；以下仅适用于 Full。
实现→质检→spec回写→commit→finish。dispatch trellis-implement/check，prompt 首行 `Active task: <path>`；trace 记执行/证据/偏差。Full/high ordinary 仅要求 packet `deterministic_checks` + focused evidence；Integration 才要求 project-wide build/analyze/lint/full regression；设计缺陷回 Phase1。
Runtime-required Full 技术绿后只报 `implementation_verified` 并移交 exact probe；未全部 current pass 时保持 active，不运行 archive。
[/workflow-state:in_progress-sub-agent]

[workflow-state:in_progress-inline]
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 spec，编辑后 trellis-check。Full/high ordinary 仅记录 packet `deterministic_checks` + focused evidence；Integration 才记录 project-wide build/analyze/lint/full regression；其他 route 保持原验证合同。缺证据不得 commit；设计缺陷回 Phase1。
Runtime-required Full 技术绿后只报 `implementation_verified` 并移交 exact probe；未全部 current pass 时保持 active，不运行 archive。
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
4. 风险路由以 `.trellis/scripts/guru/guru_delivery_policy.py` + `.trellis/policy/delivery-policy.json` 为唯一可执行真源；输入是需求清晰度、风险、耦合、可逆性与验证成本，commit intent 不参与难度判定。用户可在首次写入前后切换任一受支持 route；每次切换都递增 `selection_generation` 并使旧确认与证据失效。
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

- 任务创建同意 ≠ 实现同意；selected `full_chain` 且 high-risk 等确认与 current digests 后必须走 guarded wrapper，direct `task.py start` 不是文档化的 Full 入口。
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

selected `full_chain` 且 high-risk 前置 = current requirements/risk/design 批次已确认、overview/detail 当前 digest 双 clean，且 `guru_gate.py check-start <task_dir>` 通过。`START_READY` 后必须运行 `python3 .trellis/scripts/guru/guru_task.py start <task-dir> --slice <id> --gate-digest <sha256> --slice-packet-digest <sha256> --risk-packet-digest <sha256> --envelope-digest <sha256> --attestation-digest <sha256>`；wrapper 会在调用官方 task lifecycle 前校验 current bindings。官方 Core 的 direct `task.py start` 不能替代该 Full 入口。Lite 在 compact requirements 确认 current 后自动 start。

#### 1.7 Full planning 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + route-aware requirements review clean/current（Lite 不适用该 Full Gate） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review + current requirements/risk/design 已一批确认 | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + 项目约定条目 | ✅（inline 平台除外） |
| selected `full_chain` 且 high-risk 的 `guru_task.py start` guarded activation 已验证；Lite 不适用 | ✅ |

---

## Phase 2 / Phase 3 步骤细则

Lite 在一次当前 requirements digest 确认后自动 host-inline 实现并运行 focused check 与 scoped deterministic_final，Worker 0、无 Overview/Detail planning review。随后自动追加 mutable evidence、同步 Spec 并进入可逆 commit-ready。以下 2.1/2.2 的 `check-implementation`、dispatcher 和 Worker 协议仅适用于 Full。

Full 与 Trellis 原版同构（dispatch 协议、guarded commit 与 finish-work 收尾不变），但 unchanged scope 不得再拆分 requirements/detail/commit 用户确认：

### Runtime-required Full 验收合同

`runtime_acceptance_required=true` 只允许作为 `prd.md`、Detail 或 `implement.md` 中的 planning marker；它不是 `task.json`、`gate-contract.json` 或任何 script schema 的新字段。声明该 marker 的 Full 任务复用 task-local `verification-evidence.jsonl` 记录 append-only evidence，并保持现有 task lifecycle status。每行至少绑定 `acceptance_id`、current baseline、environment、steps/command、expected、actual、evidence refs、recorded time 和 executor；证据只保留脱敏摘要与 artifact reference，不保存 secret、token、PII、完整响应体或用户内容。

五个对外证据/报告状态固定为：

| 状态 | 语义 |
| --- | --- |
| `implementation_verified` | static/test/implementation review 已通过，但 runtime 尚未闭合；不是用户验收完成 |
| `runtime_acceptance_pending` | exact target-environment probe 已移交给明确 owner，等待实际结果 |
| `runtime_acceptance_failure` | current 目标环境的实际结果不满足 frozen acceptance row，进入 repair continuation |
| `runtime_acceptance_pass` | 单个 acceptance row 的环境、步骤、预期、实际与证据齐全且绑定 current baseline |
| `accepted` | 所有 required rows 的 newest current-baseline append 经校验都是 pass；不得跳过任何更新 append；这是任务级报告结论，不是 lifecycle status |

技术验证完成后的 handoff 顺序：

1. 从 frozen Acceptance Closure Matrix 枚举全部 `required=true` 的 `acceptance_id` 和各自行内 runtime probe；不得从 ledger 已存在的行反推 required set。marker 存在但 matrix 缺失或 required set 为空时路由 `DETAIL_DEFECT`，停止完成流程。
2. 记录/报告 `implementation_verified`，对尚未实际执行的 required row 只有在 environment、exact probe、预期、evidence owner 和所需 evidence 均明确后才追加/保留 `runtime_acceptance_pending`。owner 缺失或 probe 不可证伪时 handoff 阻断，不得写一条可冒充有效移交的 pending row。
3. 把 exact probe 交给 agent、QA、开发者或用户中的已声明 owner；task 保持 active/`in_progress`。不为等待 runtime 先 archive 再 reopen。
4. 实际 executor 追加 `runtime_acceptance_pass` 或 `runtime_acceptance_failure`，不覆盖历史、不回写 digest-bearing matrix。新 evidence 到达后必须重新计算，不缓存旧 allow/deny 决定。

每次 finish/archive 前按以下方式消费 evidence：

1. 读取 current requirements/Overview/Detail/implementation baseline 和 frozen required ID set，再按 append order 读取完整 ledger。任一 append 无法解析到 `acceptance_id` 或 baseline binding 时，立即作为 `PROCESS_DEFECT` 阻断 archive；不得跳过坏行并回退使用旧 evidence。
2. 对每个 required `acceptance_id`，先只按 append position 找出绑定 current baseline 的 newest append，再校验该 exact row 的 status 和字段。不得先过滤“valid row”再选择。selected pass 必须具有完整 environment、steps/command、expected、actual、evidence refs、executor 和 timestamp；selected row malformed、incomplete 或 status 不支持时，要求 append corrected evidence 并阻断，绝不向前搜索旧 pass。没有 current-baseline append 时，历史 pass 归 stale，否则归 missing。
3. newest row 合法但为 current non-pass（包括 `implementation_verified`、`runtime_acceptance_pending` 或 `runtime_acceptance_failure`）时，它压过所有更早 pass。ledger unreadable 或 newest row 非法属于 evidence precondition failure，先报告 exact line/row 并停止；不得把它降级成普通 runtime blocker。
4. evidence structure 可完整求值后，任一 row missing、pending、failure 或 stale 时保存完整 blocking list，但只报告一个下一动作，优先级为 `failure > stale > missing > pending`。输出 exact `acceptance_id`、原因、matrix-owned probe、owner 和 evidence requirement。
5. failure 的唯一下一步是先保存 failure 并完成 same-goal/root-cause classification，原 probe 是 repair 后的 resume condition；stale/missing 重跑原 probe；pending 继续由已声明 owner 执行。
6. 只有 required ID set 与 current-pass set 完全相等，且每个 required ID 的 exact newest current-baseline append 都校验为 `runtime_acceptance_pass`，才能报告 `accepted` 并解除 runtime guard。解除只允许继续既有 finish/archive Gate，不自动授权 commit、push、merge 或 archive。

技术绿、clean review、ordinary slice pass、`COMMIT_READY`、`implementation_verified`、单行 pass 或旧 baseline pass 都不得表述为 `accepted`。未闭合时 `/trellis:finish-work` 必须停在 archive 前，报告 `implementation_verified`、`runtime_acceptance_pending` 或 `runtime_acceptance_failure`，并保持任务 active。

current runtime failure 必须先 append `runtime_acceptance_failure`，再核对 original `acceptance_id`/BHV/用户结果及权限、数据、外部合同、material scope 是否变化。同一 active task 且 goal/boundary 未变时沿原任务继续，不创建第二套 Requirements/Overview/Detail：

| 最早 defect owner | 最大回退 | 必须刷新 |
| --- | --- | --- |
| `IMPLEMENT_DEFECT` | Phase 2 implementation/check | 受影响代码/测试、slice/Integration review、runtime receipt |
| `PROCESS_DEFECT` | current evidence/process；仅 packet 或 digest-bearing plan 需改时回 Detail | 受影响 evidence；plan 改变时刷新 Detail downstream |
| `DETAIL_DEFECT` | Phase 1 Detail | affected Detail/packet、slice/Integration/runtime evidence |
| `OVERVIEW_DEFECT` | Phase 1 Overview + affected Detail | Overview 与 affected Detail/downstream evidence |
| `REQ_BLOCKER` / material change | Phase 1 Requirements affected chain | 完整 affected Full chain |

Environment/fixture-only 是 verification disposition，不是第六个 defect class。confirmed packet、digest-bearing plan、fixture contract 或 declared check 本身错误/不完整时分类为 `PROCESS_DEFECT`，且只有实际修改 packet/plan 时才回 Detail；packet/plan 与 implementation 都正确、仅 target environment 配置或 runtime fixture instance 错误时，留在 current verification step，只刷新 environment/fixture evidence 与 affected probe，不改产品 planning 或 implementation。

未变化且 binding 仍 current 的 planning 与 sibling receipts 保持可复用；任何被现有 digest/snapshot Gate 判 stale 的 evidence 必须真实刷新。对 archived 历史 Full task，当前无脚本能力只支持在获得相应任务创建授权后建立引用原 `acceptance_id`、artifact digest、receipt 和新 failure evidence 的 linked repair child/new task，并如实执行当前 Gate；不得声称 in-place reopen、机器级 baseline inheritance 或零 Full replanning。

**执行边界**：以上是 agent/Skill/workflow 行为合同。所有 Trellis/Guru/CLI lifecycle、Gate、verify、hook、apply、Python、shell 和 TypeScript scripts 均保持不变，因此 direct `task.py archive` 等绕过 agent 的调用不会被机器 fail-closed 阻断。不得把本合同包装成 script-level guard、自动 parser 或新 lifecycle capability；如需该能力必须另行授权。

**Full/high minimum-stable slice lifecycle（Agent planning SSOT）**：

- `Design UNIT` 只负责需求、行为和 invariant 追溯；`Implementation Slice` 才是独占修改、focused validation、review、commit 与 rollback 单元。多个 Design UNIT 可合并进一个 Implementation Slice，但 packet 继续只保留一个真实 `owner_unit`，其余写入 `implement.md.covered_units`；禁止按 UNIT、设计章节、doc_type 或技术层机械生成 slice。
- 所有四端都遵循 delivery policy 的同一组 Agent-only 默认值：`full_high_default_strategy=minimum_commit_stable_parallel_first`、`max_ordinary_slices=4`、`mutable_path_overlap=0`、`review_context_target_bytes=262144`、`ordinary_depends_on_default=[]`、`single_integration_slice=true`、`formal_evidence_control_worktree=serial`。Detail 应先冻结接口、schema、digest、错误语义和共享数据结构；共享 mutable path 必须重新分配唯一 owner 或合并，资源锁与 focused test 修改范围必须隔离、分波次或触发合并。
- `guru_supervise.py implement-slices ... --dry-run` 只输出 dispatch plan/brief，不启动 sub-agent，也不是实际 spawn 或 writer-parallel 的证明。完整 packet 集可能因 Integration coverage overlap 被当前 `slice-plan` 保守标为 serial；coordinator 必须回读 Detail planning audit，只派发 ownership 不重叠、`depends_on=[]` 且工具资源可隔离的 ordinary Implementation Slices。
- ordinary implementation 可以并发，但同一 snapshot 只启动一个 semantic reviewer；Full/high ordinary 只运行 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 `Integration Slice` 才运行 project-wide build/analyze/lint/full regression；Small、Micro、Lite、non-Full 和 v1 保留原 route verification。正式 staged review、commit 与 receipt 只在唯一 control worktree 串行收口；Integration 最后执行跨 slice invariants 和最终组合验证，其普通 target union 只是 review coverage，不授予重写 ordinary owner 核心字节的权限。

#### 2.1 实现 `[required · repeatable]`

进入本节的最低硬条件是 `python3 .trellis/scripts/guru/guru_gate.py check-implementation <task-dir>` 通过；`guru_supervise.py implement|check|implement-check` 会在启动 worker 前自动执行该 gate，`planning` 状态一律 fail-closed。

dispatch-mode aware：主会话先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto` 读取 `codex.dispatch_mode` 与 slice-plan；该命令只产生 dispatch plan/brief，实际 spawn 必须由 coordinator 另行执行并留存 dispatch 记录。`sub-agent` 模式按返回的 `trellis-implement` brief 派发平台 sub-agent（prompt 第一行必须是 `Active task: <path>`，且不得再嵌套 spawn implement/check）；`channel` 模式才使用官方 channel worker/`guru_supervise.py implement-check` 命令；`inline` 模式串行手工执行。必要时可拆分 `implement` 与 `check`。worker 注入存在的 jsonl、任务产物和平台 implementation writing/review skill，等待后端的 done/error/killed 或平台 final status。**P1 high-risk full_chain slice（packet 机制）**：仅当 selected route 为 `full_chain` 且 risk 为 high 时要求 `--slice <unit_id>`（多 packet 必填，单 packet 自动选）；supervisor 进修复循环前做 packet preflight + scope preflight（packet 缺失/非法/多义 → `PACKET_*`、dirty 越界 packet `target_paths`/`dirty_state.unrelated` → `SCOPE_INVALID`，均硬停 exit2、不启 worker、不进 repairable loop）；每轮 implement 成功后 supervisor 独立执行 packet `deterministic_checks`（绑定本轮 diff，hard Gate）。编码按平台 Guru implementation writing/review 口径，实现 Detail-approved Implementation Slice 覆盖的最小完整行为，而不是把 UNIT/doc_type/技术层机械转换为 slices；执行/验证证据写入 task-local mutable evidence，不把 `implement.md` 当作 detail 确认后的可变证据文件。发现 `DETAIL_DEFECT` / `OVERVIEW_DEFECT` / `REQ_BLOCKER` 按 Phase 1 回退。

#### 2.2 质检 `[required · repeatable]`

check 可作为 `implement-check` 的拆分子命令运行：`python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>`。审核按平台 Guru review 口径覆盖需求/设计/实现合同一致性、分层依赖律、合规红线与 route/slice-role 验证证据：Full/high ordinary 只核对 packet 声明的 `deterministic_checks` 与 focused evidence，唯一 Integration 才核对 project-wide build/analyze/lint/full regression，Small/Micro/Lite/non-Full/v1 沿用原验证合同；缺少当前角色要求的 evidence/compliance 证据不得进入 commit。需要只补 commit gate 所需结构化 review record 时，使用 `python3 .trellis/scripts/guru/guru_supervise.py implementation-review <task-dir> --staged`（或 `--slice <unit_id> --staged`），该入口只跑 deterministic checks + check worker，不启动 implement worker，不修改 confirmed detail artifacts。**P1 完成条件（有 packet）**：check worker 置顶输出 7 字段 verdict + 逐条 `invariant_status.*`；clean 须同时满足 **deterministic passed（supervisor 执行 + worker 自报双过）+ invariant_coverage all_passed（supervisor 从 packet invariants 聚合重算）+ dirty_scope clean/isolated + review_provider 满足 packet `semantic_review_provider` + 无 blocker/should-fix**；缺字段或取非通过值却声明 clean → `MALFORMED_REVIEW_OUTPUT` 硬停。**OCR 仅 optional bounded provider**（用户显式触发/高风险抽检），不作默认完成条件；`No comments generated` 不作退出目标。每轮 review 记录由单一 writer 追加 `review-records/implementation-reviews.jsonl`（可审计回放）。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（requirements confirm、overview/detail review_runs、detail confirm 按需失效重跑）；不得在代码里绕过设计语义或下游补造 owner/合同。

#### 3.1 质量验证 `[required · repeatable]`

按 route/slice role 复跑验证：Full/high ordinary 只运行 packet 声明的 `deterministic_checks` 与 focused evidence；唯一 Integration 运行 project-wide build/analyze/lint/full regression；Small/Micro/Lite/non-Full/v1 运行各自原 route 的验证。确认 `verification-evidence.jsonl`（或等价 task-local mutable evidence）已记录命令、结果与说明。若必须修改 `implement.md`，视为主动返回 detail Gate。当前角色验证失败回 2.1/2.2；必需证据缺失不得进入 3.3。

对于 runtime-required Full，以上验证与 review 全绿只产生 `implementation_verified`。按本节 Runtime 验收合同完成 active-task handoff；target runtime 尚未返回 current pass 时可继续既有 spec/commit Gate，但不得进入 archive 或把技术完成改称 `accepted`。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前先运行 `python3 .trellis/scripts/guru/guru_gate.py commit-plan [task-dir]` 获取机器可读 JSON，按其中 `route`、`commit_mode`、`allowed_stage_paths`、`forbidden_stage_paths`、`can_commit_now`、`split_required`、`blocking_reasons`、`review_coverage` 汇报 staged scope 和建议切分；计划可提交时仍必须通过 `python3 .trellis/scripts/guru/guru_gate.py check-commit <task-dir>` 或等价 PreToolUse hook。full/lite 的既有 Guru gate 语义不降：full 链要求任务已 `in_progress`，且 staged implementation paths 被当前 clean implementation review set 覆盖（切片 review 集或完整 `--staged` review），不得只信最新一条 review row；lite route 仍需 scoped 验证和 review 证据（产物形态兼容 `guru_chain=light`）。若 commit gate 只缺 required implementation review record，恢复命令是 `guru_supervise.py implementation-review <task-dir> --staged`，能映射 slice 时优先用 `--slice <unit_id> --staged`，不是 `implement-check`。`small_inline` 不能直接 commit；低风险一旦需要 commit 必须走 `micro_task` 并由任务目录 `gate-contract.json` 约束 staged scope。若实现已发生但缺有效合同，且 staged scope 是低风险 scoped implementation diff，commit-plan 必须进入 post-implementation route recovery：阻断 direct commit，只推荐创建/切换 `micro_task` 并运行 `init-contract --route micro_task --risk low`，不得倒逼补 full PRD / overview / detail。`gate-degradations.jsonl` 只可作为真实失败与补偿检查证据，不能预授权跳过 gate；high/full_chain 是推荐与 selected route 组合，用户选择较轻 route 时必须由 `route_selection` 审计承接。

提交前展示 `commit-plan` 摘要、当前 route/slice role 的验证证据与建议 commit 切分：Full/high ordinary 只展示 packet 声明的 `deterministic_checks` 与 focused evidence，Integration 展示 project-wide build/analyze/lint/full regression，Small/Micro/Lite/non-Full/v1 展示原 route evidence。若 commit 已包含在当前 Lite/Full 唯一确认批次或用户初始指令中，则通过 Gate 后自动执行；否则停在可逆 commit-ready，不消耗第二次需求确认。不 amend、不 push；只处理本任务相关文件，不回滚用户改动。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程。对 runtime-required Full，先按 frozen matrix/current baseline 找到每个 required row 的 newest append，再校验该 exact row；禁止过滤无效更新后回退旧 pass。ledger/newest row unreadable、malformed 或 incomplete，或 missing/stale/pending/failure 任一存在时保持任务 active，输出唯一 evidence repair 或 next probe/owner 并停在 archive 前。全部 exact newest current rows 校验为 pass 时只解除 runtime guard，再按既有授权确认任务状态、journal、归档/后续动作与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
