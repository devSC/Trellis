# Guru iOS Native Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核（verify 强制：`swift build` + `swift test` / `xcodebuild test`）。**
> 平台 = iOS / macOS 原生（Swift + SwiftUI 主 + RxSwift 遗留，DDD 四层 + FactoryKit DI）。规则唯一真源：`.trellis/spec/`（guru-ios-native spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — requirements 已完成 adversarial review 且已确认、overview/detail 当前 digest 双 clean（各含至少一次 adversarial clean）、detail 已确认后才能 `task.py start`（before_start 钩子强制校验）
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
- **Guru Gate 机制**：planning 只保留 `requirements` 与 `detail` 两个人工确认；`overview` / `detail` 的设计 review 证据写入 `task.json.guru_gates.review_runs`，完整模型见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。通道按 config `guru.gate_mode`（**本节是通道唯一主定义**）：
  - `requirements`：结构 Gate 通过后，先运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>` 做 opposite-provider 需求 review；`route_class=REQ_BLOCKER` 回需求修订并使下游 overview/detail 证据在需求 digest 变化后重跑，`review_result=clean/requirements-ready` 后才停下等待用户运行 `guru_gate.py confirm requirements <task_dir>`。requirements review 不使用 review-evidence Gate、不写 review_runs，且不改变 `guru_gate.py confirm requirements` 语义；需求发现阶段内置 Domain Grill，不再要求 post-draft grill Gate。
  - `overview`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（至少一条 reviewer 含 `adversarial`，通常由 `guru_supervise.py --adversarial overview` 的 opposite provider 记录）后自动通过；`confirm overview` 必须失败。
  - `detail`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（至少一条 reviewer 含 `adversarial`，通常由 `guru_supervise.py --adversarial detail` 的 opposite provider 记录）后，用户运行 `guru_gate.py confirm detail <task_dir>`。
  - 配置 `guru.supervision.adversarial_enabled: false` 可临时关闭 `--adversarial` 的 opposite-provider worker；它只记录 skip/deferred，不产生 clean 证据，overview/detail 仍需 review evidence。
  - **strict（默认）**：用户本人在交互式终端运行 `python3 .trellis/scripts/guru/guru_gate.py confirm requirements|detail`；agent 经工具运行因无 TTY 被拒。
  - **soft**：用户在对话中明确确认后，agent 运行 `guru_gate.py confirm requirements|detail --via-agent --user-quote "<用户确认原话>"` 代跑（`--user-quote` 必填，留痕标注 soft/agent + 用户原话）；**未获用户本轮明确确认不得执行**。
  - 进度用 `guru_gate.py status <task_dir>` 查；最终以 `guru_gate.py check <task_dir>` 作为 `task.py start` 前强制复查。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：task.json `guru_chain`（创建时 after_create 默认 `full`）。**full=完整五阶段链**（核心玩法/付费/内购/存档/权限/数据采集/跨层 feature）；**light=轻量链**（单层小改且用户同意后显式降级，如仅文案、仅一个 ViewModel、仅一个 View 微调）。

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。full 链另有**正式需求包**（requirement-writing/review，项目 docs 需求目录），prd.md 为其行为规格抽取层。
- 设计产物按链型分轨：
  - **full**：目录级设计包（task.json `design_package` 指向，如 `docs/design/<feature>/`）= `README.md`（导航）+ `design-main.md`（概要主定义，含归属表/承接索引/架构就绪自检）+ `chapters/*.md`（详细设计逐章，directory_precheck + chapter_loop 生成）。任务内 `design.md` 退为指针+摘要。
  - **light**：任务内 `design.md` 两章：**§1 概要设计**（归属表+三问+承接索引）；**§2 详细设计**（逐 doc_type 合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；实现期持续追加 §2 执行 / §3 证据（`swift build`/`swift test` 输出）/ §4 阻塞偏差。
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

- 简单对话/小任务：先问是否需要建 Trellis 任务；用户说不需要则本轮跳过 Trellis。
- 进入任务后第一步判定碰哪几层（只文案 → i18n 路径；只一个 ViewModel/View → 局部链；跨层 feature → 全链）与风险等级。
- **核心玩法 / 付费内购 / 存档 / 涉权限或数据采集 / 跨 DDD 多层 → 必须走完整五阶段（full 链，目录级设计包）**；单层小改可走轻量链（prd 简版 + 所碰 doc_type 的详细合同 + 实现），但每步仍要 Gate。判轨结论落 task.json `guru_chain`（默认 full；降 light 需用户同意）。
- 建任务许可 ≠ 实现许可：实现必须等 requirements adversarial review + 确认、overview/detail 双 clean（各含 adversarial clean）、detail 确认后 `task.py start`。

[workflow-state:no_task]
无任务：先分类请求并征得建任务同意。单层小改可不建；核心玩法/付费/存档/权限/数据采集/跨 DDD 层必须建任务走完整五阶段（full 链）。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + iOS 项目约定）
- 1.6 激活任务 `[required · once]`（review evidence + detail confirm → `task.py start`）
- 1.7 完成判定

[workflow-state:planning]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=req review+confirm→overview/detail 双 clean(含 adversarial)→detail confirm；jsonl 齐后 start。
[/workflow-state:planning]

[workflow-state:planning-channel]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=req review+confirm→overview/detail 双 clean(含 adversarial)→detail confirm；主会话跑 guru_supervise。
[/workflow-state:planning-channel]

[workflow-state:planning-sub-agent]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=req review+confirm→overview/detail 双 clean(含 adversarial)→detail confirm；legacy sub-agent 用 Active task。
[/workflow-state:planning-sub-agent]

[workflow-state:planning-inline]
无需求→1.1；高风险决策 one-question：每轮 1 问，答后回写 prd/需求包；requirement-writing 只草拟，不代确认。无概要→1.3；无详细→1.4。Gate=req review+confirm→overview/detail 双 clean(含 adversarial)→detail confirm；inline 先 trellis-before-dev。
[/workflow-state:planning-inline]

### Phase 2: Execute（实现阶段）

- 2.1 实现 `[required · repeatable]`
- 2.2 质检 `[required · repeatable]`
- 2.3 回退 `[on demand]`

[workflow-state:in_progress]
实现→质检→spec回写→commit→finish。默认用官方 trellis channel：主会话运行 guru_supervise.py implement-check（或拆分 implement/check / 等价 create/spawn/send/wait/messages），等待 done/error/killed，失败先读 messages --raw；worker 不 commit/push/merge。无 swift build/test 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress]

[workflow-state:in_progress-channel]
实现→质检→spec回写→commit→finish。channel：主会话运行 guru_supervise.py implement-check（官方 trellis channel；必要时拆分 implement/check），注入存在的 jsonl/任务产物/Guru skill，等待 done/error/killed，失败先读 messages --raw 和 log；worker 不 commit/push/merge。
[/workflow-state:in_progress-channel]

[workflow-state:in_progress-sub-agent]
实现→质检→spec回写→commit→finish。legacy sub-agent：dispatch trellis-implement/check，prompt 以 Active task: <path> 开头；trace 记执行/swift build+test 证据/偏差；质检按 guru iOS 口径（分层律+DI+doc_type）；无 build/test 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress-sub-agent]

[workflow-state:in_progress-inline]
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 iOS spec，编辑后 trellis-check（guru iOS 口径）；swift build/test 证据记 implement.md，无证据不 commit；设计缺陷回 Phase1。
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
4. 轻量链允许 prd 简版 + 仅所碰 doc_type 的 design 合同，但 Gate 口径不降。
5. doc_type 全程只用钉死七类（`viewmodel`/`usecase`/`repository`/`domain-model`/`view`/`coordinator`/`external`）；归属违反分层依赖律 = 直接 fail。

### Active Task Routing

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `ios-design-overview-writing` / `ios-design-detail-writing`；Gate 判定 → 对应 `ios-design-overview-review` / `ios-design-detail-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → 默认运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task>`（必要时拆分 implement/check）（官方 `trellis channel`，注入 iOS implementation/review skill）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `ios-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → legacy dispatch `trellis-implement` / `trellis-check`（口径 = `ios-implementation-guru-writing` / `ios-implementation-guru-review`），prompt 以 `Active task: <path>` 开头。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `ios-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- 编辑前 → `trellis-before-dev`（读 iOS spec）；编辑后 → `trellis-check`（口径 = `ios-implementation-guru-review`）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待 requirements adversarial review + 确认、overview/detail 双 clean（各含 adversarial clean）、detail 确认后的 `task.py start`。
- 阶段跃迁必须经 `guru_gate.py confirm` 人工收口（strict=用户终端；soft=用户**本轮对话明确确认**后 agent 以 `--via-agent --user-quote "<用户原话>"` 代跑）；不得以自写 review 记录或机器检查通过替代；soft 下未获用户确认即代跑属违规（记录留痕可审计）。
- 合规 STOP：任何可能违反 App Store 审核政策（如隐私清单 `PrivacyInfo.xcprivacy`、ATT、内购规则）或美国法规的不确定性 → 立即停止，输出风险点+替代方案+人类确认清单。
- iOS 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有 `swift build` + `swift test`（或 `xcodebuild test`）验证证据。
- 产物语言中文优先（英文仅限标识符/命令/路径/协议字段/专有名词/缩写/原文引用）；面向用户的提问与结论一律中文。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。
after_create 钩子默认写入 `guru_chain: full`；按 Request Triage 判定为单层小改且**用户同意**走轻量链时，才把 task.json 改为 `guru_chain: light` 并记录理由。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包草稿**（项目 docs 需求目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 的 one-question loop 仍是高风险产品/范围/风险确认合同；`requirement-writing` 只能生成 `ai_drafted` / `evidence_ready` / open questions，不得绕过用户逐项确认。
**light 链**：加载 `trellis-brainstorm` 探索需求，直接产出 `prd.md`。
两轨 `prd.md` 口径一致，**需求五要素**：① 行为规格（Given/When/Then，每条 `BHV-NNN` 标题）② 核心能力清单（P0/P1）③ 失败路径（含 `enum Error` 预期分支，如校验失败 / 持久化失败 / 网络失败）④ 验收场景（可被 `swift test` 断言的可验证信号）⑤ 显式未决问题（默认一次只问用户 1 个最高优先级问题；仅当用户当前消息明确要求“批量确认/一次性确认/这几个都按推荐处理”等覆盖多个 OQ/decision id 时，才可列出 2~4 个并逐项记录确认；模糊“继续/好/按推荐”回退为单个 next_question，其余保持 open）。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：五要素缺一 → 留在本步修订。结构过后（`guru_gate.py requirements <task_dir>` 通过），先运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>`。review 必须先查 `prd.md`、正式需求包、task context 与 repo evidence；medium+ 需求阻断输出 `route_class=REQ_BLOCKER` 并留在 1.1 修订，需求 digest 变更后下游 overview/detail 证据需重跑；低严重度措辞 nit 不阻断；clean 输出 `review_result=clean/requirements-ready`。requirements review 不使用 review-evidence Gate、不写 review_runs、不代替人工确认；clean 后停下等待 **confirm 人工收口**（通道按 gate_mode，见 Trellis System 节）；确认落盘后方可进 1.3。

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
**light 链**：产出 `design.md` **§1 概要设计**。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`；手动分步时加载 `ios-design-overview-review` 做 clean-context review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录。当前 digest 两个不同 `run_id` clean、且至少一次 reviewer 含 `adversarial` 后自动进入 1.4；缺 adversarial 时运行 `guru_supervise.py --adversarial overview <task_dir>`。`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。**归属违反分层依赖律 = 直接 fail**（不放行、回本步重排归属）。

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
**light 链**：展开 `design.md` **§2 详细设计**（单文档多章节，逐 `UNIT-<slug>` 合同八问）。
**详细 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py detail <task_dir>`；手动分步时加载 `ios-design-detail-review` 做 clean-context review，并用 `guru_gate.py record-review detail <task_dir> ...` 记录。当前 digest 两个不同 `run_id` clean、且至少一次 reviewer 含 `adversarial` 后停下等待 `guru_gate.py confirm detail <task_dir>`；缺 adversarial 时运行 `guru_supervise.py --adversarial detail <task_dir>`。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` 回 1.3，`DETAIL_DEFECT` / `PROCESS_DEFECT` 修复后重审。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru iOS 必含条目**（各带 reason）：本任务涉及的 `harness/` SSOT 文件（含命中的 `detail-type-*.md` L2）、`.trellis/spec/guides/golden-path.md`、`.trellis/spec/conventions/project-conventions.md`。涉及持久化时追加 WCDBSwift / DatabaseManager 约定条目；涉及导航时追加 AppCoordinator / `Container+Coordinators` 条目。inline 平台跳过。

#### 1.6 激活任务 `[required · once]`

前置 = requirements 已完成 adversarial review 且已确认、overview/detail 当前 digest 双 clean（各含 adversarial clean）、detail 已确认（`guru_gate.py check <task_dir>` 通过）。然后 `task.py start <task-dir>`——其 before_start 钩子会再次强制校验，缺 evidence/缺确认直接失败；此时运行 `guru_gate.py status <task_dir>` 按最早缺口恢复，禁止绕过。

#### 1.7 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + adversarial requirements review clean/requirements-ready + 用户 confirm requirements（full 链含正式需求包 review 通过） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review，且至少一条 reviewer 含 adversarial（full=design-main.md；light=design.md §1；归属表无分层律违规） | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review，且至少一条 reviewer 含 adversarial + 用户 confirm detail（full=chapters/ 闭合；light=design.md §2；doc_type 限七类，pending 类已豁免或补 L2） | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + golden-path + iOS 项目约定条目 | ✅（inline 平台除外） |
| `task.py start` 已执行（before_start 校验通过） | ✅ |

---

## Phase 2 / Phase 3 步骤细则

与 Trellis 原版同构（dispatch 协议、commit 批量确认流程、finish-work 收尾不变），仅口径替换为 iOS：

#### 2.1 实现 `[required · repeatable]`

channel 默认：主会话运行 `python3 .trellis/scripts/guru/guru_supervise.py implement <task-dir>`（或等价官方 `trellis channel create/spawn/send/wait/messages`），helper 只注入存在的 `implement.jsonl`、任务产物和 `ios-implementation-guru-writing` skill，等待 `done/error/killed`。legacy sub-agent 平台 dispatch `trellis-implement`；inline 平台先加载 `trellis-before-dev` 读当前任务产物、`conventions/project-conventions.md`、`guides/golden-path.md` 与相关 harness SSOT（含命中的 `detail-type-*.md`）。编码按 `ios-implementation-guru-writing` 口径：组合需求真正触达的迷你路径，**按自底向上顺序**（`domain-model` → `repository` → `usecase` → `viewmodel` → `view`，`coordinator`/`external` 横切）逐片实现并持续更新 `implement.md` 的执行/证据/阻塞偏差。
golden-path 硬约束逐片落实：FactoryKit `@Injected` 注入（禁手动 init 依赖）、Repository 接口在 Domain 实现在 Infrastructure、`enum Error` 分层、ViewModel `ObservableObject`+`@Published`、private 方法置于 `private extension`、持久化只走 WCDBSwift。发现设计缺口停下回 Phase 1 修订，不在代码里绕过设计语义。

#### 2.2 质检 `[required · repeatable]`

channel 默认：主会话运行 `python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>`，helper 只注入存在的 `check.jsonl`、任务产物和 `ios-implementation-guru-review` skill，等待 `done/error/killed`；失败先读 `trellis channel messages --raw`。legacy sub-agent/inline 模式加载 `trellis-check`，按 `ios-implementation-guru-review` 口径审核（实现 trace 四节对齐）：需求/设计/实现合同一致性、**分层依赖律**（import 方向、Domain 零依赖、View 不直连持久化/网络、View 间不直接导航）、**DI canonical**（`@Injected` + `Container+*` 工厂，无手动初始化）、doc_type 归属与七类台账一致、项目约定槽位取值、`enum Error` 分层、合规红线（隐私清单/ATT/内购）与验证证据。无 `swift build` / `swift test`（或 `xcodebuild test`）/ lints 证据不得进入 commit。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（review + 用户 confirm）；不得在代码里绕过设计语义或下游补造 owner/合同/归属。

#### 3.1 质量验证 `[required · repeatable]`

复跑与变更范围匹配的验证命令（`swift build`、`swift test` 或 `xcodebuild -scheme <Scheme> test`，按需 SwiftLint），确认 `implement.md` §3 已记录命令、结果与说明。验证失败回 2.1/2.2；验证缺失不得进入 3.3。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前展示变更范围、`swift build`/`swift test` 验证证据与建议 commit 切分，等待用户确认；不 amend、不 push；只 stage 本任务相关文件，不回滚用户改动。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
