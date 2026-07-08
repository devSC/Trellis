# Guru H5 (Next.js) Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载需求确认、概要/详细 review Gate 与详细确认，Phase 2/3 承载实现与审核（verify 强制：`tsc --noEmit` + `next build` + `eslint`）。**
> 平台 = H5 / Web（Next.js App Router 生产形态为目标 + React + TypeScript strict）。规则唯一真源：`.trellis/spec/`（guru-h5-web spec 库）；本文件只做流程路由，不复写规则正文。
> **基线声明**：golden-path 以 **App Router 生产最佳实践**为准；参考示例 `examples/blog`（Pages Router + Nextra + MDX + gray-matter 的轻量 blog starter，故意简化）仅作**内容模型基线与示例实证**，不作生产形态权威。全程显式区分"示例实证（blog/Pages Router）"与"App Router 生产级补充"。

---

## Core Principles

1. **Plan before code** — requirements 已确认、overview/detail 当前 digest 双 clean（默认各含至少一次 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 已确认后才能 `task.py start`（before_start 钩子强制校验）
2. **Specs injected, not remembered** — 规则经 jsonl/hook 注入，不靠记忆
3. **Persist everything** — 研究、决策、trace 全部落文件
4. **Gate 不过不进下一阶段** — 缺陷只能回上游阶段修，禁止下游补造
5. **分层依赖律是归属硬基准** — `route → server-component → data-access → domain-type`（服务端链）、`client-component → ui-component`（交互链）、`server-action → data-access`；反向依赖、`client-component` 直取私有数据/secret = 直接 fail，不在概要/详细/实现任一阶段放行
6. **Capture learnings** — 任务完成按萃取九段结构回写 spec

---

## Trellis System（机制速查）

开发者身份、任务生命周期命令、workspace journal、`get_context.py` 用法与 Trellis 原版一致（`python3 ./.trellis/scripts/task.py --help` 为权威清单），此处不复述。

**Guru H5 关键差异**：

- `.trellis/spec/` 使用 guru-h5-web spec 库：`harness/`（五阶段 SSOT）、`guides/golden-path.md`（H5 golden-path）、`conventions/project-conventions.md`（项目约定槽位）。入口与阶段映射见 `.trellis/spec/harness/index.md`。
- 任何阶段开始前必须通过 `.trellis/spec/conventions/project-conventions.md` 的校验清单 C1~C5（内容源 / 状态管理 / UI 组件库 / 样式方案 / 测试 / lint / 数据库 / 认证 / 图像优化 / 部署 / 路由模式 等槽位，缺失或未填 = 硬前置失败，先补约定）。
- **H5 三条最高禁令（违反即任务失败）**：① 禁止违反分层依赖律的 import（`data-access`/`domain-type` 不得依赖 `server-component`；`ui-component` 不得反向依赖 `client-component`）② 禁止 `client-component` 直接获取私有数据 / 读取 secret / 直连 DB（私有数据获取只在 `server-component`/`data-access`/`server-action`）③ 禁止全局样式污染（样式一律 CSS Modules / Tailwind 隔离，禁裸全局 CSS 覆盖第三方/跨组件）。
- **golden-path 锁定硬规则**：TS strict（`tsconfig.json` `"strict": true`，与 blog 示例 `"strict": false` 相反——示例是简化基线，**生产必须开 strict**）；server-first，`'use client'` 最小化（仅需交互处下沉到叶子组件）；私有数据获取/secret 只在 server 侧；route 段约定齐备（`page/layout/loading/error.tsx`）；`metadata`/SEO 标准化（`export const metadata` 或 `generateMetadata`）；样式隔离；错误边界（`error.tsx`）；server→client props 必须可序列化。
- **Guru Gate 机制**：planning 只保留 `requirements` 与 `detail` 两个人工确认；`overview` / `detail` 的设计 review 证据写入 `task.json.guru_gates.review_runs`，完整模型见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。通道按 config `guru.gate_mode`（**本节是通道唯一主定义**）：
  - `requirements`：结构 Gate 通过后按 route 选择默认 review。`full_chain` 且 `guru.supervision.adversarial_enabled=true` 时运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>` 做 opposite-provider 需求 review；`full_chain` 且配置为 false 时不默认 spawn adversarial worker，但仍要求当前 digest clean/current requirements review；`lite_task` 走 bounded requirements path，adversarial requirements review 可选；`micro_task` / `small_inline` 默认不做 task-local requirements adversarial review（若后续需要 commit，先创建/路由有效 contract）。`route_class=REQ_BLOCKER` 回需求修订并使下游 overview/detail 证据在需求 digest 变化后重跑，`review_result=clean/requirements-ready` 后才停下等待用户运行 `guru_gate.py confirm requirements <task_dir>`。requirements review 不使用 review-evidence Gate、不写 review_runs；`confirm requirements` / `check-start` 必须硬要求当前 digest clean/current requirements review，missing/deferred/blocked/stale 不得人工越过。需求发现阶段内置 Domain Grill，不再要求 post-draft grill Gate。
  - `overview`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（默认至少一条 reviewer 含 `adversarial`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean）后自动通过；`confirm overview` 必须失败。
  - `detail`：结构 Gate 通过 + 当前 digest 下两个不同 `run_id` 的 clean review（默认至少一条 reviewer 含 `adversarial`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean）后，用户运行 `guru_gate.py confirm detail <task_dir>`。
  - 配置 `guru.supervision.adversarial_enabled: false` 可临时关闭 `--adversarial` 的 opposite-provider worker；gate 会动态读取该配置：requirements 不再强制 opposite-provider adversarial clean，overview/detail 不再要求 adversarial reviewer，但仍要求当前 digest、双 clean review、用户确认以及没有 blocked/medium+ 当前证据。
  - route-aware review policy 只放宽 adversarial 证据要求：`small_inline`/`micro_task` 不要求 requirements adversarial review；`lite_task` 采用 bounded review policy（requirements adversarial 可省略，overview/detail 仍要当前 digest 双 clean，但不强制 adversarial reviewer）；`full_chain` / `risk=unknown` / 缺失或非法 contract 保持 strict 路径，且仅当 `guru.supervision.adversarial_enabled=true` 时默认要求 requirements adversarial review。当前 digest 的 blocked、malformed、medium+ evidence 仍硬阻断。
  - **strict（默认）**：用户本人在交互式终端运行 `python3 .trellis/scripts/guru/guru_gate.py confirm requirements|detail`；agent 经工具运行因无 TTY 被拒。
  - **soft**：用户在对话中明确确认后，agent 运行 `guru_gate.py confirm requirements|detail --via-agent --user-quote "<用户确认原话>"` 代跑（`--user-quote` 必填，留痕标注 soft/agent + 用户原话）；**未获用户本轮明确确认不得执行**。
  - 进度用 `guru_gate.py status <task_dir>` 查；最终以 `guru_gate.py check-start <task_dir>` 作为 `task.py start` 前强制复查。
  - `check-start` 成功只产生 `START_READY`：下一步仅可运行 `task.py start`；实现/质检 worker 另由 `check-implementation` 要求 `task.json.status == in_progress`，提交另由 `check-commit` 校验 staged scope 与 implementation review。

### Planning Artifacts（guru 五阶段语义，双轨制）

**判轨**：task.json `guru_chain`（创建时 after_create 默认 `full`）。**full=完整五阶段链**（核心玩法/付费/广告/存档/权限/数据采集/跨层 feature/新增 route 段）；**light=轻量链**（单层小改且用户同意后显式降级，如仅文案、仅一个 `ui-component`、仅一处 `client-component` 微调）。

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。full 链另有**正式需求包**（requirement-writing/review，项目 docs 需求目录），prd.md 为其行为规格抽取层。
- 设计产物按链型分轨：
  - **full**：目录级设计包（task.json `design_package` 指向，如 `docs/design/<feature>/`）= `README.md`（导航）+ `design-main.md`（概要主定义，含归属表/承接索引/架构就绪自检）+ `chapters/*.md`（详细设计逐章，directory_precheck + chapter_loop 生成）。任务内 `design.md` 退为指针+摘要。
  - **light**：任务内 `design.md` 两章：**§1 概要设计**（归属表+三问+承接索引）；**§2 详细设计**（逐 doc_type 合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；detail 确认后保持 digest-bearing，不作为执行/验证证据 sink；执行、验证、阻塞偏差写入 task-local mutable evidence（`implementation-evidence.jsonl` / `verification-evidence.jsonl` / `commit-plan.json` / `review-records/implementation-reviews.jsonl`）。
- `implement.jsonl` / `check.jsonl` — spec/research 注入清单（见 1.5）。
- **编号纪律** — 行为 `BHV-NNN`（prd 标题，不复用不重排）、设计单元 `UNIT-<slug>`（design §2 / chapters 标题）；跨产物引用一律写裸编号 token。`python3 .trellis/scripts/guru/guru_gate.py trace-matrix <task_dir> [--write]` 随时生成追溯矩阵（含「需求场景（REQ-UC）」列；--strict 断链拦截）。full 链 prd 的 BHV 标题可在短名前以 `[REQ-UC-XXX]`（多对多）承接正式需求包需求源场景（`### BHV-001 [REQ-UC-005] <短名>`），`trace-matrix --require-req-uc`（或 task.json `require_req_uc:true`）强制 BHV 须带 REQ-UC（旧 prd 默认不拦、列空、不断链）；版本级 `guru_gate.py trace-aggregate <version-dir> [--include-completed]` 反查指向某需求包版本目录的 task，把 `(REQ-UC, BHV, UNIT, Source Task)` 行展开聚合进 `traceability.md` 派生列（手维护 Code/Test/Status 按 key 回填保留；fail-closed：manifest `canonical_excludes` 须含 `traceability`）。**命名消歧**：`REQ-UC-XXX`（需求源场景）≠ overview `UC-<序号>`（架构核心用例），两套独立编号。
- **产物语言** — task 产物（prd/design/implement/research、spec 回写、findings）一律**中文优先**；英文仅限 TS/JS 标识符、命令（`tsc`/`next build`/`eslint`/`pnpm`）、文件路径、协议字段、外部专有名词（Next.js/React/App Router/RSC/Tailwind/zod/Vercel）、缩写与原文引用。commit message 跟随仓库历史风格。

### H5 详细设计 doc_type 权威七类（全程唯一，禁止改名/增减/换数）

> 下游引用、trace 矩阵、jsonl reason、`guru_gate.py` 校验一律只认这七个 token，**严禁自创 controller / service / datasource / page-controller / handler 之类**（这些是 flutter/Go 的类型名，H5 一律按本表）。owner 层标注必须与分层依赖律一致。

| # | doc_type | 归属层（owner） | 职责 | L2 状态 |
|---|----------|----------------|------|---------|
| 1 | `server-component` | 服务端渲染层 | RSC 服务端组件：渲染编排 + 数据获取编排（默认，不带 `'use client'`） | L2 full（`detail-type-server-component.md`） |
| 2 | `client-component` | 客户端交互层 | `'use client'` 交互组件：状态 / 事件 / hooks / 浏览器 API | L2 full（`detail-type-client-component.md`） |
| 3 | `data-access`      | 数据访问层 | fetch 封装 / 内容源（MDX/CMS）读取 / ORM 查询；服务端唯一取数出口 | L2 full（`detail-type-data-access.md`） |
| 4 | `route`            | 路由编排层 | App Router route 段：`page`/`layout`/`loading`/`error.tsx` + `metadata`/SEO | L2 pending |
| 5 | `ui-component`     | 展示层 | 纯展示型可复用组件：无数据获取、无业务逻辑 | L2 pending |
| 6 | `domain-type`      | 领域类型层 | TS 类型 / zod schema / 领域模型；零运行依赖、可被任意层导入 | L2 pending |
| 7 | `server-action`    | 变更/接口层 | Server Actions / route handlers：变更（mutation）/ API endpoint | L2 pending |

- **L2 文件**（v1 已提供 render/interactive/data **三元组**，对应 flutter 的 controller / usecase / repository-datasource）：`.trellis/spec/harness/detail/detail-type-server-component.md`（render 端，对应 controller）/ `detail-type-client-component.md`（interactive 端，对应 usecase 的状态流位移到 client）/ `detail-type-data-access.md`（data 端，对应 repository-datasource）。
- **pending 四类**（`route` / `ui-component` / `domain-type` / `server-action`）：详细设计按 L1 合同八问展开，文档头标 `l2_status: pending`；full 链命中 pending 类型须在详细 Gate 前显式 `L2豁免：<doc_type> 理由：…`，否则 gate 拦截。
- **owner 层与分层依赖律（归属硬基准，违反 fail）**：服务端链 `route → server-component → data-access → domain-type`；交互链 `client-component → ui-component`；变更链 `server-action → data-access`。反向依赖、`client-component` 直取私有数据/secret 一律 fail。
- **写作顺序（自底向上）**：`domain-type` → `data-access` → `server-action` → `server-component` → `client-component` → `ui-component` → `route`。

### 示例实证 vs 生产级补充（基线锚点）

> 唯一参考示例 `examples/blog`（`examples/blog/package.json` 证据：`next` + `nextra@2.0.0-beta` + `nextra-theme-blog` + `gray-matter` + `rss`；`examples/blog/pages/` 证据：Pages Router；`pages/posts/*.md(x)` 证据：MDX frontmatter 内容源；`scripts/gen-rss.js` 证据：构建期 `node ./scripts/gen-rss.js && next build`；`tsconfig.json` 证据：`"strict": false`、`target: es5`）。

| 维度 | 示例实证（blog，故意简化） | App Router 生产级补充（golden-path 权威） |
|------|---------------------------|------------------------------------------|
| 路由模式 | Pages Router（`pages/`，Nextra 主题托管） | App Router（`app/`，`page`/`layout`/`loading`/`error.tsx`） |
| 服务端模型 | `getStaticProps` 风格 / Nextra 静态渲染 | RSC（server-component 默认）+ `'use client'` 最小化 |
| 内容源 | MDX + `gray-matter` frontmatter（`pages/posts/*.mdx`） | 同为合法内容源基线；生产可换 CMS/ORM，统一收口到 `data-access` |
| 类型严格度 | `"strict": false`（示例简化） | **必须 `"strict": true`** |
| 数据变更 | 无（纯内容站，`gen-rss.js` 为构建脚本非运行时变更） | `server-action`（mutation / API endpoint） |
| SEO | Nextra/`_app.tsx` 内 `<Head>` 注入 RSS | `export const metadata` / `generateMetadata`，route 段标准化 |

写作铁律：凡引用 blog 示例须显式标注"示例实证（Pages Router/简化）"；凡给生产规则须标注"App Router 生产级补充"，不得把示例的简化项（如 `strict:false`、Pages Router、`<Head>` 内联 SEO）当作 golden-path 默认。

---

## Phase Index

```
Phase 1: Plan    → 需求 Gate → 概要 Gate → 详细 Gate → 激活任务
Phase 2: Execute → 实现（golden-path 迷你路径 + trace）→ 质检（guru H5 口径）
Phase 3: Finish  → 验证（tsc --noEmit / next build / eslint）→ 萃取回写 spec → commit → 收尾
```

### Request Triage

- 收到实现类需求时先跑可执行分流：`python3 .trellis/scripts/guru/guru_gate.py intake --description "<需求>" [--path <path> ...]`。不要要求用户自己说 `full/lite/micro`；系统给出推荐；非高风险可在合法审计下 override，高风险不得降为 lite/micro。
- 若当前已有 active task 但新需求可能完全不同，先不带 `task_dir` 跑 `intake`，确认任务归属或新建任务后才 `--write-contract`，避免污染当前任务。
- 简单对话/小任务：先问是否需要建 Trellis 任务；用户说不需要则本轮跳过 Trellis。
- 进入任务后第一步判定碰哪几层（只文案 → l10n/文案路径；只一个 `ui-component`/`client-component` → 局部链；新增 route 段 / 跨 server-client → 全链）与风险等级。
- **核心玩法 / 付费 / 广告 / 存档 / 涉权限或数据采集 / 跨 server-client 边界 / 新增 route 段 → 默认推荐完整五阶段（full 链，目录级设计包）**；单层小改可走轻量链（prd 简版 + 所碰 doc_type 的详细合同 + 实现），但每步仍要 Gate。判轨结论落 task.json `guru_chain`（默认 full；降 light 需用户同意）和 `gate-contract.json`；非高风险选择较轻 route 时必须记录 `route_selection` 风险确认审计；高风险请求较轻 route 只能记录偏好，不能绕过 `full_chain`。
- 建任务许可 ≠ 实现许可：实现必须等 requirements 确认、overview/detail 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 确认后 `task.py start`。

[workflow-state:no_task]
无任务：先跑 `guru_gate.py intake --description "<需求>" [--path <path> ...]` 分类请求并征得建任务同意。单层小改可不建；commit 需要 micro_task 合同；核心玩法/付费/广告/存档/权限/数据采集/跨 server-client/新增 route 段默认推荐完整五阶段（full 链）；非高风险选择较轻 route 时记录 route_selection 风险确认审计；高风险请求较轻 route 只记录偏好，仍按 full_chain 执行。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + H5 项目约定）
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
实现→质检→spec回写→commit→finish。默认用官方 trellis channel：主会话运行 guru_supervise.py implement-check（或拆分 implement/check / 等价 create/spawn/send/wait/messages），等待 done/error/killed，失败先读 messages --raw；worker 不 commit/push/merge。无 tsc/next build/eslint 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress]

[workflow-state:in_progress-channel]
实现→质检→spec回写→commit→finish。channel：主会话运行 guru_supervise.py implement-check（官方 trellis channel；必要时拆分 implement/check），注入存在的 jsonl/任务产物/Guru skill，等待 done/error/killed，失败先读 messages --raw 和 log；worker 不 commit/push/merge。
[/workflow-state:in_progress-channel]

[workflow-state:in_progress-sub-agent]
实现→质检→spec回写→commit→finish。legacy sub-agent：dispatch trellis-implement/check，prompt 以 Active task: <path> 开头；trace 记执行/tsc+next build+eslint 证据/偏差；质检按 guru H5 口径（分层律+server-client 边界+doc_type 七类）；无 build/lint 证据不 commit；设计缺陷回 Phase1。
[/workflow-state:in_progress-sub-agent]

[workflow-state:in_progress-inline]
实现→质检→spec回写→commit→finish。inline 不派 sub-agent：编辑前 trellis-before-dev 读 H5 spec，编辑后 trellis-check（guru H5 口径）；tsc/next build/eslint 证据记 `verification-evidence.jsonl` 等 task-local mutable evidence，无证据不 commit；设计缺陷回 Phase1。
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
5. doc_type 全程只用钉死七类（`server-component`/`client-component`/`data-access`/`route`/`ui-component`/`domain-type`/`server-action`）；归属违反分层依赖律 = 直接 fail；`client-component` 直取私有数据/secret = 直接 fail。

### Active Task Routing

[Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（前置探索）；full 链正式需求 → `requirement-writing` / `requirement-review`（guru-ai-guides）。
- 概要/详细撰写 → `h5-design-overview-writing` / `h5-design-detail-writing`；Gate 判定 → 对应 `h5-design-overview-review` / `h5-design-detail-review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements review 默认按 route：full_chain+配置开启才运行 `guru_supervise.py --adversarial requirements`，lite bounded 可选，micro/small 默认不跑；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → 默认运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-check <task>`（必要时拆分 implement/check）（官方 `trellis channel`，注入 H5 implementation/review skill）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-channel, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-sub-agent]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `h5-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements review 默认按 route：full_chain+配置开启才运行 `guru_supervise.py --adversarial requirements`，lite bounded 可选，micro/small 默认不跑；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- `in_progress` 实现/质检 → legacy dispatch `trellis-implement` / `trellis-check`（口径 = `h5-implementation-guru-writing` / `h5-implementation-guru-review`），prompt 以 `Active task: <path>` 开头。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-sub-agent]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；full 链正式需求 → `requirement-writing/review`；概要/详细 → `h5-design-*-writing/review`。
- 需求发现 / Domain Grill → `trellis-brainstorm`；requirements review 默认按 route：full_chain+配置开启才运行 `guru_supervise.py --adversarial requirements`，lite bounded 可选，micro/small 默认不跑；overview/detail 自动 review/fix → `guru_supervise.py overview|detail`。
- 编辑前 → `trellis-before-dev`（读 H5 spec）；编辑后 → `trellis-check`（口径 = `h5-implementation-guru-review`）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待 requirements 确认、overview/detail 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 确认后的 `task.py start`。
- 阶段跃迁必须经 `guru_gate.py confirm` 人工收口（strict=用户终端；soft=用户**本轮对话明确确认**后 agent 以 `--via-agent --user-quote "<用户原话>"` 代跑）；不得以自写 review 记录或机器检查通过替代；soft 下未获用户确认即代跑属违规（记录留痕可审计）。
- 合规 STOP：任何可能违反 App Store / Google Play 政策（H5 套壳/WebView 嵌入场景）或美国法规（隐私 / Cookie 同意 / 数据采集）的不确定性 → 立即停止，输出风险点+替代方案+人类确认清单。
- H5 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有 `tsc --noEmit` + `next build` + `eslint` 验证证据。
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
两轨 `prd.md` 口径一致，**需求五要素**：① 行为规格（Given/When/Then，每条 `BHV-NNN` 标题）② 核心能力清单（P0/P1）③ 失败路径（含 H5 预期分支：取数失败 / 客户端校验失败 / `server-action` 变更失败 / 错误边界 `error.tsx` 触发 / 渲染降级）④ 验收场景（可被 `next build` 通过、`tsc` 零报错、`eslint` 零违规或 RTL/Playwright 断言的可验证信号）⑤ 显式未决问题（默认一次只问用户 1 个最高优先级问题；仅当用户当前消息明确要求“批量确认/一次性确认/这几个都按推荐处理”等覆盖多个 OQ/decision id 时，才可列出 2~4 个并逐项记录确认；模糊“继续/好/按推荐”回退为单个 next_question，其余保持 open）。
prd 草稿成形后执行 Domain Grill：对照 golden-path/项目约定/既有 BHV 磨术语、压测边界、核对当前代码事实与用户意图，确认的长期术语/边界才回写长期知识，临时需求决策写入 prd。
**需求 Gate**：五要素缺一 → 留在本步修订。结构过后（`guru_gate.py requirements <task_dir>` 通过），按 route 选择 review 默认：`full_chain + guru.supervision.adversarial_enabled=true` 运行 `python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>`；`full_chain + adversarial_enabled=false` 不默认 spawn adversarial worker，但其余 strict gate 不降；`lite_task` 走 bounded requirements path，adversarial requirements review 可选；`micro_task`/`small_inline` 默认无 task-local requirements adversarial review（commit 前必须路由/创建有效 contract）。requirements review 如运行，必须先查 `prd.md`、正式需求包、task context 与 repo evidence；medium+ 需求阻断输出 `route_class=REQ_BLOCKER` 并留在 1.1 修订，需求 digest 变更后下游 overview/detail 证据需重跑；低严重度措辞 nit 不阻断；clean 输出 `review_result=clean/requirements-ready`。requirements review 不使用 review-evidence Gate、不写 review_runs、不代替人工确认；默认只有 clean/current 后才允许 **confirm 人工收口**（通道按 gate_mode，见 Trellis System 节），missing/deferred/blocked/stale 均硬阻断；配置关闭只动态放宽 adversarial review 要求，当前 digest 已有 blocked 或 medium+ 证据仍硬阻断。确认落盘后方可进 1.3。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。H5 典型研究项：RSC / `'use client'` 边界与 props 序列化约束、内容源能力（MDX + gray-matter 实证见 `examples/blog/pages/posts/*.mdx`；生产 CMS/ORM 选型补充）、缓存与 revalidate 策略、`next/image` 与字体优化、`metadata`/SEO 生成方式、Server Actions 与 route handlers 取舍。

#### 1.3 概要设计 `[required · repeatable]`

归属有争议时在 overview review/fix loop 内逐行核对**归属表**（唯一 owner、server vs client 归属、是否触碰私有数据红线、与代码现状核对）后再送审。
加载 `h5-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + `.trellis/spec/guides/golden-path.md` + `.trellis/spec/conventions/project-conventions.md`。
概要必含**归属表 + 三问 + 承接索引**：
- **归属表**：每个待建/改动单元 → doc_type（限七类）→ owner 层 → 落地文件路径；每行通过分层依赖律自检（服务端链 `route→server-component→data-access→domain-type`、交互链 `client-component→ui-component`、变更链 `server-action→data-access` 单向；`client-component` 不直取私有数据/secret；server→client props 可序列化；样式隔离）。
- **三问**：① 改动触达哪几层、是否跨 server-client 边界？② 是否新增/改动 `domain-type` 契约（类型/zod schema）或 `data-access` 取数出口？③ 是否新增 route 段 / `server-action` / 新外部依赖（内容源/CMS/ORM/认证）？
- **承接索引**：逐文件列出"由哪个 BHV 驱动、对应哪个 doc_type、是 server 还是 client、详细阶段在哪展开"，作为详细阶段 directory_precheck 的输入。
**full 链**：建立设计包骨架（`README.md` + `design-main.md` + `chapters/`），把包路径写入 task.json `design_package`，产出 `design-main.md` 概要主定义（含架构就绪自检与逐文件承接索引）；任务内 `design.md` 写指针+摘要。
**light 链**：产出 `design.md` **§1 概要设计**。
**概要 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>`，该 supervisor action 必须在 write/repair 后运行 overview review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `h5-design-overview-review` 做 clean-context review，并用 `guru_gate.py record-review overview <task_dir> ...` 记录，不能先进入下一阶段。当前 digest 两个不同 `run_id` clean 后自动进入 1.4；默认还要求至少一次 reviewer 含 `adversarial`，缺 adversarial 时运行 `guru_supervise.py --adversarial overview <task_dir>`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean，不要求 adversarial reviewer。`confirm overview` 禁止。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` / `PROCESS_DEFECT` 修复后重审。**归属违反分层依赖律 / client 直取私有数据 = 直接 fail**（不放行、回本步重排归属）。

#### 1.4 详细设计 `[required · repeatable]`

加载 `h5-design-detail-writing`，按概要承接索引展开详细设计（逐 doc_type **合同八问**），并产出 `implement.md`（trace §1 计划）。
**合同八问**（每个 `UNIT-<slug>` 必答，深度对标 L2 文件 `detail-type-server-component/client-component/data-access.md`）：
1. 正向生成动作 —— 这个单元正常路径做什么（输入→编排/取数/渲染→产物）；
2. 边界与不变量 —— 参数边界、错误分支、`domain-type` 不变量、server/client 执行环境约束（如 `'use client'` 不可 `await` 顶层服务端取数）；
3. 产物合同 —— 对外暴露的 props/导出类型/`data-access` 函数签名/`server-action` 入参出参/route 段 `metadata` 字段；
4. 依赖与归属 —— import 哪几层、是否守住分层依赖律与 server-client 边界（自证 `client-component` 不直取私有数据、server→client props 可序列化）；
5. 可验证信号 —— 用什么证据断言成功（`tsc --noEmit` 零错、`next build` 通过、`eslint` 零违规；按约定槽位补 Vitest+RTL / Playwright 断言点与 mock 边界）；
6. 好例子 / 坏例子 —— 至少一组对照（如 `client-component` 内 `fetch('/secret-api', {headers:{token}})` 直取 = 坏例 / 经 `server-component`→`data-access` 取数后以可序列化 props 下传 = 好例）；
7. 不适用场景 —— 明确本单元**不**承担什么（如 `ui-component` 不做取数/不含业务、`server-component` 不持客户端状态、`domain-type` 无运行时逻辑）；
8. Gate 判定 —— 本单元过详细 Gate 的判据（合同字段齐全、归属合法、server-client 边界自证、可验证信号可执行）。
**full 链**：directory_precheck（design-main 承接索引存在且非空，否则回退概要）→ chapter_loop **逐章/小批次**生成 `chapters/<slug>.md`（禁止一次性全量输出）；命中 pending L2 类型（`route` / `ui-component` / `domain-type` / `server-action`）须显式 `L2豁免：<doc_type> 理由：…` 或先补 L2（gate 拦截）。
**light 链**：展开 `design.md` **§2 详细设计**（单文档多章节，逐 `UNIT-<slug>` 合同八问）。
**详细 Gate**：默认运行 `python3 .trellis/scripts/guru/guru_supervise.py detail <task_dir>`，该 supervisor action 必须在 write/repair 后运行 detail review/fix 并记录当前 digest clean；手动分步时，writing 结束后必须立刻加载 `h5-design-detail-review` 做 clean-context review，并用 `guru_gate.py record-review detail <task_dir> ...` 记录，不能先请求用户确认。当前 digest 两个不同 `run_id` clean 后停下等待 `guru_gate.py confirm detail <task_dir>`；默认还要求至少一次 reviewer 含 `adversarial`，缺 adversarial 时运行 `guru_supervise.py --adversarial detail <task_dir>`；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean，不要求 adversarial reviewer。`REQ_BLOCKER` 回 1.1，`OVERVIEW_DEFECT` 回 1.3，`DETAIL_DEFECT` / `PROCESS_DEFECT` 修复后重审。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru H5 必含条目**（各带 reason）：本任务涉及的 `harness/` SSOT 文件（含命中的 `detail-type-*.md` L2，如 server-component/client-component/data-access）、`.trellis/spec/guides/golden-path.md`、`.trellis/spec/conventions/project-conventions.md`。涉及内容源时追加 MDX/CMS/gray-matter 约定条目；涉及变更时追加 `server-action`/route handler 约定条目；涉及样式时追加 Tailwind/CSS Modules 隔离条目。inline 平台跳过。

#### 1.6 激活任务 `[required · once]`

前置 = requirements 已确认、overview/detail 当前 digest 双 clean（默认各含 adversarial clean；`adversarial_enabled=false` 时不要求）、detail 已确认（`guru_gate.py check-start <task_dir>` 通过）。这只代表 `START_READY`，然后运行 `task.py start <task-dir>`；before_start 钩子会再次强制校验，缺 evidence/缺确认直接失败。`START_READY` 不授权实现、质检 worker、git commit 或发布；此时运行 `guru_gate.py status <task_dir>` 按最早缺口恢复，禁止绕过。

#### 1.7 完成判定

| 条件 | 必须 |
|------|:---:|
| 需求产物过需求 Gate + route-aware requirements review clean/current（full_chain 且配置开启要求 adversarial clean/requirements-ready；lite bounded 不强制 adversarial）+ 用户 confirm requirements（full 链含正式需求包 review 通过） | ✅ |
| 概要主定义过概要 Gate + 当前 digest 两个不同 run-id clean review（默认至少一条 reviewer 含 adversarial；配置关闭时只要求双 clean；full=design-main.md；light=design.md §1；归属表无分层律违规、无 client 直取私有数据） | ✅ |
| 详细设计过详细 Gate + 当前 digest 两个不同 run-id clean review（默认至少一条 reviewer 含 adversarial；配置关闭时只要求双 clean）+ 用户 confirm detail（full=chapters/ 闭合；light=design.md §2；doc_type 限七类，pending 类已豁免或补 L2） | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + golden-path + H5 项目约定条目 | ✅（inline 平台除外） |
| `task.py start` 已执行（before_start 校验通过） | ✅ |

---

## Phase 2 / Phase 3 步骤细则

与 Trellis 原版同构（dispatch 协议、commit 批量确认流程、finish-work 收尾不变），仅口径替换为 H5：

#### 2.1 实现 `[required · repeatable]`

进入本节的最低硬条件是 `python3 .trellis/scripts/guru/guru_gate.py check-implementation <task-dir>` 通过；`guru_supervise.py implement|check|implement-check` 会在启动 worker 前自动执行该 gate，`planning` 状态一律 fail-closed。

channel 默认：主会话运行 `python3 .trellis/scripts/guru/guru_supervise.py implement <task-dir>`（或等价官方 `trellis channel create/spawn/send/wait/messages`），helper 只注入存在的 `implement.jsonl`、任务产物和 `h5-implementation-guru-writing` skill，等待 `done/error/killed`。legacy sub-agent 平台 dispatch `trellis-implement`；inline 平台先加载 `trellis-before-dev` 读当前任务产物、`conventions/project-conventions.md`、`guides/golden-path.md` 与相关 harness SSOT（含命中的 `detail-type-*.md`）。编码按 `h5-implementation-guru-writing` 口径：组合需求真正触达的迷你路径，**按自底向上顺序**（`domain-type` → `data-access` → `server-action` → `server-component` → `client-component` → `ui-component` → `route`）逐片实现；执行/验证证据写入 task-local mutable evidence，不把 `implement.md` 当作 detail 确认后的可变证据文件。
golden-path 硬约束逐片落实：TS strict、server-first 且 `'use client'` 最小化（仅交互叶子下沉）、私有数据/secret 只在 server 侧取（`server-component`/`data-access`/`server-action`）、server→client props 可序列化、route 段约定齐备（`page`/`layout`/`loading`/`error.tsx`）、`metadata`/SEO 标准化、样式隔离（Tailwind/CSS Modules，禁全局污染）。发现设计缺口停下回 Phase 1 修订，不在代码里绕过设计语义。

#### 2.2 质检 `[required · repeatable]`

channel 默认：主会话运行 `python3 .trellis/scripts/guru/guru_supervise.py check <task-dir>`，helper 只注入存在的 `check.jsonl`、任务产物和 `h5-implementation-guru-review` skill，等待 `done/error/killed`；失败先读 `trellis channel messages --raw`。legacy sub-agent/inline 模式加载 `trellis-check`，按 `h5-implementation-guru-review` 口径审核（实现 trace 四节对齐）：需求/设计/实现合同一致性、**分层依赖律**（import 方向、服务端链/交互链/变更链单向、`data-access`/`domain-type` 不反向依赖 `server-component`）、**server-client 边界**（`client-component` 不直取私有数据/secret、不直连 DB、`'use client'` 最小化、props 可序列化）、doc_type 归属与七类台账一致、项目约定槽位取值、样式隔离、`metadata`/SEO 与错误边界齐备、合规红线（隐私 / Cookie 同意 / 数据采集）与验证证据。无 `tsc --noEmit` / `next build` / `eslint`（按约定槽位含 Vitest+RTL / Playwright）证据不得进入 commit。

#### 2.3 回退 `[on demand]`

质检暴露需求/概要/详细设计缺陷 → 回 Phase 1 对应步骤修订产物并重新过 Gate（review + 用户 confirm）；不得在代码里绕过设计语义或下游补造 owner/合同/归属。

#### 3.1 质量验证 `[required · repeatable]`

复跑与变更范围匹配的验证命令（`tsc --noEmit`、`next build`、`eslint`，按约定槽位补 `vitest` / `playwright test`），确认 `verification-evidence.jsonl`（或等价 task-local mutable evidence）已记录命令、结果与说明。若必须修改 `implement.md`，视为主动返回 detail Gate。验证失败回 2.1/2.2；验证缺失不得进入 3.3。

#### 3.2 Debug 复盘 `[on demand]`

同类 bug 或修复失败反复出现时，加载 `trellis-break-loop` 分析根因、失败原因与预防机制；有可沉淀结论才继续 3.3。

#### 3.3 Spec 回写 `[required · once]`

加载 `trellis-update-spec`，按 `.trellis/spec/harness/extraction-template.md` 萃取九段判断是否回写 spec；即使结论是"无可沉淀"也要在任务记录中说明。

#### 3.4 Commit `[required · once]`

提交前先运行 `python3 .trellis/scripts/guru/guru_gate.py commit-plan [task-dir]` 获取机器可读 JSON，按其中 `route`、`commit_mode`、`allowed_stage_paths`、`forbidden_stage_paths`、`can_commit_now`、`split_required`、`blocking_reasons` 汇报 staged scope 和建议切分；计划可提交时仍必须通过 `python3 .trellis/scripts/guru/guru_gate.py check-commit <task-dir>` 或等价 PreToolUse hook。

若实现已发生但缺有效合同，且 staged scope 是低风险 scoped implementation diff，commit-plan 必须进入 post-implementation intake recovery：阻断 direct commit，只推荐创建/切换 `micro_task` 并运行 `init-contract --route micro_task --risk low`，不得倒逼补 full PRD / overview / detail。

提交前展示 `commit-plan` 摘要、`tsc`/`next build`/`eslint` 验证证据与建议 commit 切分，等待用户确认；不 amend、不 push；只 stage 本任务相关文件，不回滚用户改动。

#### 3.5 收尾提醒

运行 `/trellis:finish-work` 或等价收尾流程；确认任务状态、journal、归档/后续动作与未提交变更均已说明。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
