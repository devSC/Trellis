# Guru Go Backend Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核（verify 强制）。**
> 平台形态：Go monorepo（safa-land 形态），服务在 `services/<svc>/internal/{app,config,transport,service,repository,domain,auth}`，`cmd/<svc>/main.go` 单一入口，跨服务契约在 `packages/contracts/`。
> 规则唯一真源：`.trellis/spec/`（guru-go-backend spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — requirements 已确认、overview/detail 当前 digest 双 clean（默认各含至少一次 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 已确认后才能 `task.py start`（before_start 钩子强制校验）
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
- **Guru Gate 机制**：planning 只保留 `requirements` 与 `detail` 两个人工确认；`overview` / `detail` 的设计 review 证据写入 `task.json.guru_gates.review_runs`，完整模型见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。通道按 config `guru.gate_mode`（**本节是通道唯一主定义**）：
  - `requirements`：结构 Gate 通过后，先运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>` 做 opposite-provider 需求 review；`route_class=REQ_BLOCKER` 回需求修订并使下游 overview/detail 证据在需求 digest 变化后重跑，`review_result=clean/requirements-ready` 后才停下等待用户运行 `guru_gate.py confirm requirements <task_dir>`。requirements review 不使用 review-evidence Gate、不写 review_runs；`confirm requirements` / `check-start` 必须硬要求当前 digest clean/current requirements review，missing/deferred/blocked/stale 不得人工越过。需求发现阶段内置 Domain Grill，不再要求 post-draft grill Gate。
  - `overview`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（默认至少一条 reviewer 含 `adversarial`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean）后自动通过；`confirm overview` 必须失败。
  - `detail`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（默认至少一条 reviewer 含 `adversarial`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean）后，用户运行 `guru_gate.py confirm detail <task_dir>`。
  - 配置 `guru.supervision.adversarial_enabled: false` 可临时关闭 `--adversarial` 的 opposite-provider worker；gate 会动态读取该配置：requirements 不再强制 opposite-provider adversarial clean，overview/detail 不再要求 adversarial reviewer，但仍要求当前 digest、双 clean review、用户确认以及没有 blocked/medium+ 当前证据。
  - **strict（默认）**：用户本人在交互式终端运行 `python3 .trellis/scripts/guru/guru_gate.py confirm requirements|detail`；agent 经工具运行因无 TTY 被拒。
  - **soft**：用户在对话中明确确认后，agent 运行 `guru_gate.py confirm requirements|detail --via-agent --user-quote "<用户确认原话>"` 代跑（`--user-quote` 必填，留痕标注 soft/agent + 用户原话）；**未获用户本轮明确确认不得执行**。
  - 进度用 `guru_gate.py status <task_dir>` 查；最终以 `guru_gate.py check-start <task_dir>` 作为 `task.py start` 前强制复查。
  - `check-start` 成功只产生 `START_READY`：下一步仅可运行 `task.py start`；实现/质检 worker 另由 `check-implementation` 要求 `task.json.status == in_progress`，提交另由 `check-commit` 校验 staged scope 与 implementation review。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：task.json `guru_chain`（创建时 `guru_after_create` 默认 `full`）。**full=完整五阶段链**（新服务、新协议端点、鉴权/会话、DB 迁移、跨服务契约 `packages/contracts/` 变更等高风险需求）；**light=轻量链**（同包内小迭代且用户同意后显式降级）。

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。Go 行为以「协议端点 / 编排步骤 / 数据访问 / 失败收口」为枚举单位。full 链另有**正式需求包**（requirement-writing/review，项目 docs 需求目录），prd.md 为其行为规格抽取层。
- 设计产物按链型分轨：
  - **full**：目录级设计包（task.json `design_package` 指向，如 `docs/design/<feature>/`）= `README.md`（导航）+ `design-main.md`（概要主定义，含行为→owner 归属表/三问理由/承接索引/架构就绪自检 G1~G8 + mermaid 架构图 + 时序图）+ `chapters/*.md`（详细设计逐章，directory_precheck + chapter_loop 生成）。任务内 `design.md` 退为指针+摘要。
  - **light**：任务内 `design.md` 两章：**§1 概要设计**（归属表+三问+承接索引）；**§2 详细设计**（逐 doc_type 合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/执行顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；实现期持续追加 §2 执行 / §3 证据 / §4 阻塞偏差。执行顺序自下而上：`domain → repository → service → transport → app/config/main`。
- `implement.jsonl` / `check.jsonl` — spec/research 注入清单（见 1.5）。
- **编号纪律** — 行为 `BHV-NNN`（prd 标题，不复用不重排，删除留洞）、设计单元 `UNIT-<slug>`（design §2 标题，slug 体现服务+层角色，如 `UNIT-user-service`/`UNIT-users-handler`/`UNIT-session-manager`）；跨产物引用一律写裸编号 token。`python3 .trellis/scripts/guru/guru_gate.py trace-matrix <task_dir> [--write]` 随时生成追溯矩阵（含「需求场景（REQ-UC）」列；--strict 断链拦截）。full 链 prd 的 BHV 标题可在短名前以 `[REQ-UC-XXX]`（多对多）承接正式需求包需求源场景（`### BHV-001 [REQ-UC-005] <短名>`），`trace-matrix --require-req-uc`（或 task.json `require_req_uc:true`）强制 BHV 须带 REQ-UC（旧 prd 默认不拦、列空、不断链）；版本级 `guru_gate.py trace-aggregate <version-dir> [--include-completed]` 反查指向某需求包版本目录的 task，把 `(REQ-UC, BHV, UNIT, Source Task)` 行展开聚合进 `traceability.md` 派生列（手维护 Code/Test/Status 按 key 回填保留；fail-closed：manifest `canonical_excludes` 须含 `traceability`）。**命名消歧**：`REQ-UC-XXX`（需求源场景）≠ overview `UC-<序号>`（架构核心用例），两套独立编号。
- **产物语言** — task 产物（prd/design/implement/research、spec 回写、findings）一律**中文优先**；英文仅限代码标识符、命令、文件路径、协议字段（如 `application_account_id`）、框架/库名（`net/http`、`lib/pq`）、缩写（HMAC-SHA256）、原文引用。commit message 跟随仓库历史风格（3.4 步已有学习机制）。

---

## Phase Index

```
Phase 1: Plan    → 需求 Gate → 概要 Gate → 详细 Gate → 激活任务
Phase 2: Execute → 实现（golden-path 迷你路径 + trace）→ 质检（guru 审核口径）
Phase 3: Finish  → 验证（go build/vet/test + golangci-lint）→ 萃取回写 spec → commit → 收尾
```

### Request Triage

- 简单对话/小任务：先问是否需要建 Trellis 任务；用户说不需要则本轮跳过 Trellis。
- 进入任务后第一步加载 golden-path 的入口决策树：判定本任务落在哪个 `services/<svc>/`、碰哪几层（只查询/读取→repository+service；只新端点→transport+service；新服务/新协议→全链）与风险等级；确认是否需动 `packages/contracts/` 跨服务契约。
- **新服务 / 新协议端点 / 鉴权或会话 / DB 迁移 / 跨服务契约变更 → 必须走完整五阶段（full 链，目录级设计包）**；同包内小改可走轻量链（prd 简版 + 所碰层的详细合同 + 实现），但每步仍要 Gate。判轨结论落 task.json `guru_chain`（默认 full；降 light 需用户同意）。
- 建任务许可 ≠ 实现许可：实现必须等 requirements 确认、overview/detail 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 确认后 `task.py start`。

[workflow-state:no_task]
无任务：先分类请求并征得建任务同意。小任务可不建；新服务/新协议端点/鉴权会话/DB迁移/跨服务契约变更必须建任务走完整五阶段。先按 golden-path 入口决策树定服务边界与所碰层。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 / `design-main.md` + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 / `chapters/*.md` + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + golden-path + 项目约定）
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
实现→质检→spec回写→commit→finish。默认用官方 trellis channel：主会话运行 guru_supervise.py implement-check（或拆分 implement/check / 等价 create/spawn/send/wait/messages），等待 done/error/killed，失败先读 messages --raw；worker 不 commit/push/merge。无 go build/vet/test 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress]

[workflow-state:in_progress-channel]
实现→质检→spec回写→commit→finish。channel：主会话运行 guru_supervise.py implement-check（官方 trellis channel；必要时拆分 implement/check），注入存在的 jsonl/任务产物/Guru skill，等待 done/error/killed，失败先读 messages --raw 和 log；worker 不 commit/push/merge。
[/workflow-state:in_progress-channel]

[workflow-state:in_progress-sub-agent]
实现→质检→spec回写→commit→finish。legacy sub-agent：dispatch trellis-implement/check，prompt 以 Active task: <path> 开头；trace 记执行/证据/偏差；质检按 guru 口径，无 go build/vet/test 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress-sub-agent]

[workflow-state:in_progress-inline]
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 golden-path/约定/harness，编辑后 trellis-check（guru 口径）；go build/vet/test 证据记 implement.md，无证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress-inline]

### Phase 3: Finish（审核与收尾）

- 3.1 质量验证 `[required · repeatable]`
- 3.2 Debug 复盘 `[on demand]`
- 3.3 Spec 回写 `[required · once]`（萃取九段结构）
- 3.4 Commit `[required · once]`
- 3.5 收尾提醒

[workflow-state:completed]
代码已提交。运行 /trellis:finish-work；工作区不净先回 3.4。go build/vet/test 与 golangci-lint 证据须已落 implement.md §3。
[/workflow-state:completed]

### Rules

1. 先定位当前 Phase 与步骤（planning 期按 artifact/章节存在性），从下一步继续。
2. `[required]` 步骤不可跳过；`[once]` 步骤产物已存在则跳过。
3. 阶段可回退：下游发现上游缺陷 → 回上游阶段修订产物 → 重入下游。**禁止下游补造**（详细阶段不补归属、实现阶段不改设计语义；handler 不决定 SQL、service 不决定路由）。
4. 轻量链（同包内小迭代）允许 prd 简版 + 仅所碰层的 design 合同，但 Gate 口径不降。
5. 三条最高禁令（轻框架锁定 / 分层单向依赖 / 无 secret 字面量）贯穿五阶段，对应 Gate 直接 fail。

### Active Task Routing

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `go-design-overview-writing` / `go-design-detail-writing`（Go 平台专属设计 skill，按 Go doc_type 七分类展开）；Gate 判定 → 对应 `*-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → 默认运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task>`（必要时拆分 implement/check）（官方 `trellis channel`，注入 Go implementation/review skill）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `go-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → legacy dispatch `trellis-implement`（按 `go-implementation-guru-writing` 口径）/ `trellis-check`（按 `go-implementation-guru-review` 口径），prompt 以 `Active task: <path>` 开头。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `go-design-*-writing/review`（按 Go doc_type 展开）。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements adversarial review → `guru_supervise.py --adversarial requirements`；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- 编辑前 → `trellis-before-dev`（读 golden-path + project-conventions + harness SSOT）；编辑按 `go-implementation-guru-writing` 口径；编辑后 → `trellis-check`（按 `go-implementation-guru-review` 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待 requirements 确认、overview/detail 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 确认后的 `task.py start`。
- 阶段跃迁必须经 `guru_gate.py confirm` 人工收口（strict=用户终端；soft=用户**本轮对话明确确认**后 agent 以 `--via-agent --user-quote "<用户原话>"` 代跑）；不得以自写 review 记录或机器检查通过替代；soft 下未获用户确认即代跑属违规（记录留痕可审计）。
- 合规 STOP：触及鉴权/会话/密钥/用户数据采集或任何法规/政策不确定性 → 立即停止，输出风险点 + 替代方案 + 人类确认清单；密钥一律走环境变量名引用，不落字面量。
- 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有 `go build`/`go vet`/`go test`/`golangci-lint` 验证证据。
- 产物语言中文优先（英文仅限标识符/命令/路径/协议字段/库名/缩写/原文引用）；面向用户的提问与结论一律中文。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。
`guru_after_create` 钩子默认写入 `guru_chain: full`；按 Request Triage 判定为同包内小改且**用户同意**走轻量链时，才把 task.json 改为 `guru_chain: light` 并记录理由。创建后先按 golden-path 入口决策树确认服务边界（落在哪个 `services/<svc>/`、复用还是新建 `internal/` 子包、是否动 `packages/contracts/`）。

#### 1.1 需求阶段 `[required · repeatable]`

**full 链**：先加载 `requirement-writing`（guru-ai-guides，硬前置=其标准包 requirement-doc-standard 可读，缺即停）撰写/补齐**正式需求包草稿**（项目 docs 需求目录），全稿后加载 `requirement-review` 做门禁审核；review 通过后把行为规格抽取为任务内 `prd.md`（BHV 编号承接需求包场景）。`trellis-brainstorm` 的 one-question loop 仍是高风险产品/范围/风险确认合同；`requirement-writing` 只能生成 `ai_drafted` / `evidence_ready` / open questions，不得绕过用户逐项确认。
**light 链**：加载 `trellis-brainstorm` 探索需求，直接产出 `prd.md`。
两轨 `prd.md` 口径一致：必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（无未决也须显式声明「无未决」；默认一次只问用户 1 个最高优先级问题；仅当用户当前消息明确要求“批量确认/一次性确认/这几个都按推荐处理”等覆盖多个 OQ/decision id 时，才可列出 2~4 个并逐项记录确认；模糊“继续/好/按推荐”回退为单个 next_question，其余保持 open）。Go 行为枚举到「协议端点 / 编排步骤 / 数据访问 / 失败收口」，例：`### BHV-012 创建代理用户` — Given 管理员会话有效 When `POST /api/users` 携带 `display_name`/`proxy_username` Then service 校验入参→repository 落库→触发 config 同步→返回 201；校验失败返回 400 携带 `ErrValidation`。反例 `### BHV-012 处理用户`（无前置/无协议/无失败路径）被需求 Gate 拒。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：五要素（行为编号 `BHV-NNN`、Given/When/Then、P0/P1 清单、失败路径章节、验收场景章节、未决问题章节）缺一 → 留在本步修订。结构过后（`guru_gate.py requirements <task_dir>` 通过），默认先运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>`。review 必须先查 `prd.md`、正式需求包、task context 与 repo evidence；medium+ 需求阻断输出 `route_class=REQ_BLOCKER` 并留在 1.1 修订，需求 digest 变更后下游 overview/detail 证据需重跑；低严重度措辞 nit 不阻断；clean 输出 `review_result=clean/requirements-ready`。requirements review 不使用 review-evidence Gate、不写 review_runs、不代替人工确认；默认只有 clean/current 后才允许 **confirm 人工收口**（通道按 gate_mode，见 Trellis System 节），missing/deferred/blocked/stale 均硬阻断；若 `guru.supervision.adversarial_enabled=false`，confirm/check-start 按配置动态放宽 adversarial review 要求，但当前 digest 已有 blocked 或 medium+ 证据仍硬阻断。确认落盘后方可进 1.3。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。Go 后端常见研究项：既有服务的 `internal/` 包结构与导入图（确认不引入反向依赖）、`packages/contracts/` 现有契约字段、`db/migrations/` 现状与迁移版本号、目标服务的 env 前缀与 `config.Load()` 现有键。

#### 1.3 概要设计 `[required · repeatable]`

归属有争议时在 overview review/fix loop 内逐行核对归属表（唯一写 owner、并发场景、与代码现状核对、不让 handler 持有数据访问）后再送审。
加载 `go-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + `.trellis/spec/guides/golden-path.md` + `.trellis/spec/conventions/project-conventions.md`。
按行为枚举 → 分层归属判定 → 承接索引展开：每条 `BHV-NNN` 给唯一 owner（doc_type 取七类之一：`entry-api`/`biz`/`repository-data`/`domain`/`config`/`external`/`runtime`）+ 三问理由（为什么属于它 / 为什么不属于别人 / 为什么需独立存在）。归属示例：路由注册/请求解析/JSON 编解码/状态码 → `entry-api`；业务编排/入参校验/sentinel error → `biz`；SQL/行映射/`ErrNotFound` 转换 → `repository-data`。把数据访问归给 handler 或让 repository 反向 import service 即违反单向依赖律，直接 fail。
**full 链**：建立设计包骨架（`README.md` + `design-main.md` + `chapters/`），把包路径写入 task.json `design_package`，产出 `design-main.md` 概要主定义（含架构就绪自检 G1~G8、mermaid 架构图、时序图或时序图策略表、逐文件承接索引落到 `chapters/<file>.md`）；任务内 `design.md` 写指针+摘要。
**light 链**：产出 `design.md` **§1 概要设计**。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`，该 supervisor action 必须在 write/repair 后运行 overview review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `go-design-overview-review` 做 clean-context review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录，不能先进入下一阶段。当前 digest 两个不同 `run_id` clean 后自动进入 1.4；默认还要求至少一次 reviewer 含 `adversarial`，缺 adversarial 时运行 `guru_supervise.py --adversarial overview <task_dir>`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean，不要求 adversarial reviewer。`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。`guru_gate.py overview <task_dir>` 复查归属表/三问/承接索引（full 链另查骨架+G1~G8+架构图+时序图）。

#### 1.4 详细设计 `[required · repeatable]`

加载 `go-design-detail-writing`，按概要承接索引展开详细设计（逐 doc_type 合同八问），并产出 `implement.md`（trace §1 计划）。
合同八问（写作完成条件）：① 承接哪些 `BHV-NNN`；② 输入/输出/错误结果（Go 签名级：函数签名、`domain` 结构体、sentinel error 表）；③ 读写哪些状态（DB 行/会话态，写 owner 与概要一致）；④ 调用哪些依赖、不调用哪些（service 调 repository 不反向；handler 不直连 DB）；⑤ 失败如何收口（`fmt.Errorf("%w: ...")` 链式包装 + `errors.Is(err, ErrValidation/ErrNotFound)` 检查 + HTTP 状态码映射，逐条失败路径对应处置）；⑥ 产生哪些事件/后置（config 同步触发、审计、副作用）；⑦ 哪些测试验证它（映射到 `internal/<pkg>/*_test.go` 的 `testing`，逐行为给成功 + 全部失败路径测试点）；⑧ 哪些内容不得在此补造（handler 不决定 SQL、service 不决定路由）。
**full 链**：directory_precheck（design-main 承接索引存在且非空，否则回退概要）→ chapter_loop **逐章/小批次**生成 `chapters/<slug>.md`（禁止一次性全量输出）；命中 pending L2 类型（`domain`/`config`/`external`/`runtime`）须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2（gate 拦截）；v1 提供 L2 的类型为 `entry-api`/`biz`/`repository-data`。
**light 链**：展开 `design.md` **§2 详细设计**（单文档多章节，命中 pending L2 类型按 L1 合同八问展开并标注 `l2_status: pending`）。
**详细 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py detail <task_dir>`，该 supervisor action 必须在 write/repair 后运行 detail review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `go-design-detail-review` 做 clean-context review，并用 `guru_gate.py record-review detail <task_dir> ...` 记录，不能先请求用户确认。当前 digest 两个不同 `run_id` clean 后停下等待 `guru_gate.py confirm detail <task_dir>`；默认还要求至少一次 reviewer 含 `adversarial`，缺 adversarial 时运行 `guru_supervise.py --adversarial detail <task_dir>`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean，不要求 adversarial reviewer。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` 回 1.3，`DETAIL_DEFECT` / `PROCESS_DEFECT` 修复后重审。`guru_gate.py detail <task_dir>` 复查合同八问四机检标记（承接行为/失败收口/测试映射/不得补造声明）+ `implement.md` 存在 + 承接断链（幽灵 `BHV-NNN`、行为无单元承接）；full 链另查章节双向闭合与 pending L2 拦截。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru 必含条目**（各带 reason）：本任务涉及的 `harness/` 阶段 SSOT 文件（如 `harness/detail/detail-type-biz.md`）、`guides/golden-path.md`、`conventions/project-conventions.md`。inline 平台跳过 jsonl 策展，改在编辑前由 `trellis-before-dev` 现读这些文件。

#### 1.6 激活任务 `[required · once]`

前置 = requirements 已确认、overview/detail 当前 digest 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 已确认（`guru_gate.py check-start <task_dir>` 通过）。这只代表 `START_READY`，然后运行 `task.py start <task-dir>`；before_start 钩子会再次强制校验，缺 evidence/缺确认直接失败。`START_READY` 不授权实现、质检 worker、git commit 或发布；此时运行 `guru_gate.py status <task_dir>` 按最早缺口恢复，禁止绕过。

#### 1.7 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + adversarial requirements review clean/requirements-ready + 用户 confirm requirements（full 链含正式需求包 review 通过） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review（默认至少一条 reviewer 含 adversarial；配置关闭时只要求双 clean；full=design-main.md 含 G1~G8+架构图+时序图；light=design.md §1） | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review（默认至少一条 reviewer 含 adversarial；配置关闭时只要求双 clean）+ 用户 confirm detail（full=chapters/ 双向闭合；light=design.md §2） | ✅ |
| `implement.md`（trace §1 计划，执行顺序自下而上）存在 | ✅ |
| jsonl 含 harness SSOT + golden-path + 项目约定条目 | ✅（inline 平台除外） |
| `task.py start` 已执行（before_start 校验通过） | ✅ |

---

## Phase 2 / Phase 3 步骤细则

与 Trellis 原版同构（dispatch 协议、commit 批量确认流程、finish-work 收尾不变），仅口径替换为 Go：

#### 2.1 实现 `[required · repeatable]`

进入本节的最低硬条件是 `python3 .trellis/scripts/guru/guru_gate.py check-implementation <task-dir>` 通过；`guru_supervise.py implement|check|implement-check` 会在启动 worker 前自动执行该 gate，`planning` 状态一律 fail-closed。

channel 默认：主会话运行 `python3 .trellis/scripts/guru/guru_supervise.py implement <task-dir>`（或等价官方 `trellis channel create/spawn/send/wait/messages`），helper 只注入存在的 `implement.jsonl`、任务产物和 `go-implementation-guru-writing` skill，等待 `done/error/killed`。legacy sub-agent 平台 dispatch `trellis-implement`；inline 平台先加载 `trellis-before-dev` 读当前任务产物、`conventions/project-conventions.md`、`guides/golden-path.md` 与相关 harness SSOT。编码按 `go-implementation-guru-writing` 口径：组合需求真正触达的迷你路径，按执行顺序自下而上（`domain → repository → service → transport → app/config/main`）逐切片实现，每片挂 `UNIT-<slug>` 编号 + 所属 `services/<svc>/internal/<layer>` + 完成信号 + 验证方式（一片不跨两个 internal 层），并持续更新 `implement.md` 的执行/证据/阻塞偏差。守住硬规则：`net/http ServeMux`（禁 gin/echo）、分层单向无环、sentinel + `%w` + `errors.Is`、`app.New/Run/Shutdown` 生命周期、`config.Load()` 集中配置、secret 只引用 env 名。发现设计缺口停下回 Phase 1 修订（不在代码里补造 owner/合同）。

#### 2.2 质检 `[required · repeatable]`

channel 默认：主会话运行 `python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>`，helper 只注入存在的 `check.jsonl`、任务产物和 `go-implementation-guru-review` skill，等待 `done/error/killed`；失败先读 `trellis channel messages --raw`。legacy sub-agent/inline 模式加载 `trellis-check`，按 `go-implementation-guru-review` 口径审核：需求/设计/实现合同一致性、分层依赖律（无反向/横向 `internal` 包导入）、框架锁定（无 gin/echo 新增依赖）、错误三件套（sentinel + `%w` + `errors.Is`，无字符串比对错误）、启动序列与 `context` 超时传递、项目槽位取值（SLOT-01~SLOT-13）、`SLOT-15` 存量豁免判定、合规红线（无 secret 字面量）与验证证据。无 `go build`/`go vet`/`go test`/`golangci-lint`/合规证据不得进入 commit。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（review + 用户 confirm）；不得在代码里绕过设计语义或下游补造 owner/合同（如让 handler 直连 DB 绕过缺失的 repository 设计）。

#### 3.1 质量验证 `[required · repeatable]`

复跑与变更范围匹配的验证命令（`go build ./...` 或 `go build ./services/<svc>/...` + `go vet ./...` + `golangci-lint run ./...` + `go test ./services/<svc>/internal/<pkg>/ -run <Test> -v`，竞态切片附 `-race`），确认 `implement.md` §3 已记录命令、退出态、测试名级结果与未验证项（真实 PostgreSQL 集成、生产负载下 `context` 超时/连接池、跨服务契约运行时兼容、信号驱动优雅关闭）。验证失败回 2.1/2.2；验证缺失不得进入 3.3。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；Go 高发根因示例：跨层反向导入、`fmt.Errorf` 丢 `%w` 致 `errors.Is` 失效、`app.Shutdown()` 漏释放资源、env 前缀冲突。有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec（只沉淀「这类任务如何被做好」，不沉淀本次需求事实；存量违例修复须从 `SLOT-15` 清单移除并注明日期）；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前必须先通过 `python3 .trellis/scripts/guru/guru_gate.py check-commit <task-dir>` 或等价 PreToolUse hook；它要求任务已 `in_progress`、staged scope 落在最新 clean implementation review 的 `target_paths` 内。

提交前展示变更范围、验证证据（`go build`/`go vet`/`go test`/`golangci-lint` 结果）与建议 commit 切分，等待用户确认；不 amend、不 push；只 stage 本任务相关文件，不回滚用户改动。涉及 `go.mod`/`go.sum` 变更须确认已跑 `go mod tidy` 且新增依赖在已批准槽位内。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作（如 DB 迁移上线时机、跨服务契约消费方同步）与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
