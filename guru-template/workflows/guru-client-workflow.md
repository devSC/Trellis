# Guru Client Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核（verify 强制）。**
> 规则唯一真源：`.trellis/spec/`（guru-flutter-client spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — requirements 已确认、overview/detail 当前 digest 双 clean、detail 已确认后才能 `task.py start`（before_start 钩子强制校验）
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
  - `requirements`：结构 Gate 通过后，用户运行 `guru_gate.py confirm requirements <task_dir>`；需求发现阶段内置 Domain Grill，不再要求 post-draft grill Gate。
  - `overview`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review 后自动通过；`confirm overview` 必须失败。
  - `detail`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review 后，用户运行 `guru_gate.py confirm detail <task_dir>`。
  - **strict（默认）**：用户本人在交互式终端运行 `python3 .trellis/scripts/guru/guru_gate.py confirm requirements|detail`；agent 经工具运行因无 TTY 被拒。
  - **soft**：用户在对话中明确确认后，agent 运行 `guru_gate.py confirm requirements|detail --via-agent --user-quote "<用户确认原话>"` 代跑（`--user-quote` 必填，留痕标注 soft/agent + 用户原话）；**未获用户本轮明确确认不得执行**。
  - 进度用 `guru_gate.py status <task_dir>` 查；最终以 `guru_gate.py check <task_dir>` 作为 `task.py start` 前强制复查。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：task.json `guru_chain`（创建时 after_create 默认 `full`）。**full=完整五阶段链**（核心玩法/付费/广告/存档/权限/数据采集）；**light=轻量链**（client-small-iteration-dev 分流且用户同意后显式降级）。

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。full 链另有**正式需求包**（requirement-writing/review，项目 docs 需求目录），prd.md 为其行为规格抽取层。
- 设计产物按链型分轨：
  - **full**：目录级设计包（task.json `design_package` 指向，如 `docs/design/<feature>/`）= `README.md`（导航）+ `design-main.md`（概要主定义，含归属表/承接索引/架构就绪自检）+ `chapters/*.md`（详细设计逐章，directory_precheck + chapter_loop 生成）。任务内 `design.md` 退为指针+摘要。
  - **light**：任务内 `design.md` 两章：**§1 概要设计**（归属表+三问+承接索引）；**§2 详细设计**（逐 doc_type 合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；实现期持续追加 §2 执行 / §3 证据 / §4 阻塞偏差。
- `implement.jsonl` / `check.jsonl` — spec/research 注入清单（见 1.5）。
- **编号纪律** — 行为 `BHV-NNN`（prd 标题，不复用不重排）、设计单元 `UNIT-<slug>`（design §2 标题）；跨产物引用一律写编号 token。`python3 .trellis/scripts/guru/guru_gate.py trace-matrix <task_dir> [--write]` 随时生成追溯矩阵（--strict 断链拦截）。
- **产物语言** — task 产物（prd/design/implement/research、spec 回写、findings）一律**中文优先**；英文仅限代码标识符、命令、文件路径、协议字段、外部专有名词、缩写与原文引用。commit message 跟随仓库历史风格（3.4 步已有学习机制）。

---

## Phase Index

```
Phase 1: Plan    → 需求 Gate → 概要 Gate → 详细 Gate → 激活任务
Phase 2: Execute → 实现（golden-path 迷你路径 + trace）→ 质检（guru 审核口径）
Phase 3: Finish  → 验证 → 萃取回写 spec → commit → 收尾
```

### Request Triage

- 简单对话/小任务：先问是否需要建 Trellis 任务；用户说不需要则本轮跳过 Trellis。
- 进入任务后第一步加载 `client-small-iteration-dev` 的入口决策树：判定碰哪几层（只文案→l10n 路径；只接口→network+data；整页 feature→全链）与风险等级。
- **核心玩法 / 付费 / 广告 / 存档 / 涉权限或数据采集 → 必须走完整五阶段（full 链，目录级设计包）**；小改可走轻量链（prd 简版 + 所碰层的详细合同 + 实现），但每步仍要 Gate。判轨结论落 task.json `guru_chain`（默认 full；降 light 需用户同意）。
- 建任务许可 ≠ 实现许可：实现必须等 requirements 确认、overview/detail 双 clean、detail 确认后 `task.py start`。

[workflow-state:no_task]
无任务：先分类请求并征得建任务同意。小任务可不建；核心玩法/付费/广告/存档/权限/数据采集必须建任务走完整五阶段。
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
无需求→1.1；无概要→1.3；无详细→1.4。Gate=req confirm→overview 双 clean→detail 双 clean+confirm；planning 默认 guru_supervise overview/detail；jsonl 齐后 start。
[/workflow-state:planning]

[workflow-state:planning-channel]
无需求→1.1；无概要→1.3；无详细→1.4。Gate=req confirm→overview 双 clean→detail 双 clean+confirm；主会话跑 guru_supervise.py overview/detail/channel。
[/workflow-state:planning-channel]

[workflow-state:planning-sub-agent]
无需求→1.1；无概要→1.3；无详细→1.4。Gate=req confirm→overview 双 clean→detail 双 clean+confirm；legacy sub-agent用Active task提示。
[/workflow-state:planning-sub-agent]

[workflow-state:planning-inline]
无需求→1.1；无概要→1.3；无详细→1.4。Gate=req confirm→overview 双 clean→detail 双 clean+confirm；inline先trellis-before-dev。
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
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 spec，编辑后 trellis-check（guru 口径）；验证证据记 implement.md，无证据不 commit；设计缺陷回 Phase1。
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
4. 轻量链（client-small-iteration-dev 分流）允许 prd 简版 + 仅所碰层的 design 合同，但 Gate 口径不降。

### Active Task Routing

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `client-design-overview-writing` / `client-design-detail-writing`；Gate 判定 → 对应 `*-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → 默认运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task>`（必要时拆分 implement/check）（官方 `trellis channel`，注入 flutter implementation/review skill）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → legacy dispatch `trellis-implement` / `trellis-check`（guru 口径），prompt 以 `Active task: <path>` 开头。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `client-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- 编辑前 → `trellis-before-dev`；编辑后 → `trellis-check`（guru 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待 requirements 确认、overview/detail 双 clean、detail 确认后的 `task.py start`。
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
after_create 钩子默认写入 `guru_chain: full`；按 Request Triage 判定为小改且**用户同意**走轻量链时，才把 task.json 改为 `guru_chain: light` 并记录理由。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包**（项目 docs 需求目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 仅作前置探索，不替代正式需求链。
**light 链**：加载 `trellis-brainstorm` 探索需求，直接产出 `prd.md`。
两轨 `prd.md` 口径一致：必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（一次问用户 1~4 个，不私自拍板）。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：上述五要素缺一 → 留在本步修订。结构过后（`guru_gate.py requirements <task_dir>` 通过），完成 **confirm 人工收口**（通道按 gate_mode，见 Trellis System 节）；确认落盘后方可进 1.3。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。

#### 1.3 概要设计 `[required · repeatable]`

归属有争议时在 overview review/fix loop 内逐行核对归属表（唯一写 owner、并发场景、与代码现状核对）后再送审。
加载 `client-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + golden-path + 项目约定。
**full 链**：建立设计包骨架（`README.md` + `design-main.md` + `chapters/`），把包路径写入 task.json `design_package`，产出 `design-main.md` 概要主定义（含架构就绪自检与逐文件承接索引）；任务内 `design.md` 写指针+摘要。
**light 链**：产出 `design.md` **§1 概要设计**。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`；手动分步时加载 `client-design-overview-review` 做 clean-context review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录。当前 digest 两个不同 `run_id` clean 后自动进入 1.4；`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。归属违反分层依赖律 = 直接 fail。

#### 1.4 详细设计 `[required · repeatable]`

加载 `client-design-detail-writing`，按概要承接索引展开详细设计（逐 doc_type 合同八问），并产出 `implement.md`（trace §1 计划）。
**full 链**：directory_precheck（design-main 承接索引存在且非空，否则回退概要）→ chapter_loop **逐章/小批次**生成 `chapters/<slug>.md`（禁止一次性全量输出）；命中 pending L2 类型须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2（gate 拦截）。
**light 链**：展开 `design.md` **§2 详细设计**（单文档多章节）。
**详细 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py detail <task_dir>`；手动分步时加载 `client-design-detail-review` 做 clean-context review，并用 `guru_gate.py record-review detail <task_dir> ...` 记录。当前 digest 两个不同 `run_id` clean 后停下等待 `guru_gate.py confirm detail <task_dir>`；`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` 回 1.3，`DETAIL_DEFECT` / `PROCESS_DEFECT` 修复后重审。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru 必含条目**：本任务涉及的 `harness/` SSOT 文件、`guides/golden-path.md`、`conventions/project-conventions.md`（各带 reason）。inline 平台跳过。

#### 1.6 激活任务 `[required · once]`

前置 = requirements 已确认、overview/detail 当前 digest 双 clean、detail 已确认（`guru_gate.py check <task_dir>` 通过）。然后 `task.py start <task-dir>`——其 before_start 钩子会再次强制校验，缺 evidence/缺确认直接失败；此时运行 `guru_gate.py status <task_dir>` 按最早缺口恢复，禁止绕过。

#### 1.7 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + 用户 confirm requirements（full 链含正式需求包 review 通过） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review（full=design-main.md；light=design.md §1） | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review + 用户 confirm detail（full=chapters/ 闭合；light=design.md §2） | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + 项目约定条目 | ✅（inline 平台除外） |
| `task.py start` 已执行（before_start 校验通过） | ✅ |

---

## Phase 2 / Phase 3 步骤细则

与 Trellis 原版同构（dispatch 协议、commit 批量确认流程、finish-work 收尾不变），仅口径替换：

#### 2.1 实现 `[required · repeatable]`

channel 默认：主会话运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task-dir>`；必要时可拆分 `implement` 与 `check`。worker 注入存在的 jsonl、任务产物和平台 implementation writing/review skill，等待 `done/error/killed`。编码按平台 Guru implementation writing/review 口径：组合需求真正触达的迷你路径，逐片实现并持续更新 `implement.md` 的执行/证据/阻塞偏差；发现 `DETAIL_DEFECT` / `OVERVIEW_DEFECT` / `REQ_BLOCKER` 按 Phase 1 回退。

#### 2.2 质检 `[required · repeatable]`

check 可作为 `implement-check` 的拆分子命令运行：`python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>`。审核按平台 Guru review 口径覆盖需求/设计/实现合同一致性、分层依赖律、合规红线与验证证据；无 analyze/test/lints/compliance 证据不得进入 commit。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（requirements confirm、overview/detail review_runs、detail confirm 按需失效重跑）；不得在代码里绕过设计语义或下游补造 owner/合同。

#### 3.1 质量验证 `[required · repeatable]`

复跑与变更范围匹配的验证命令，确认 `implement.md` §3 已记录命令、结果与说明。验证失败回 2.1/2.2；验证缺失不得进入 3.3。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前展示变更范围、验证证据与建议 commit 切分，等待用户确认；不 amend、不 push；只 stage 本任务相关文件，不回滚用户改动。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
