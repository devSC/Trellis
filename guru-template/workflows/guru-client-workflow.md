# Guru Client Development Workflow（五阶段）

> 基于 Trellis native workflow 定制（官方定制契约见原版 "Customizing Trellis (for forks)" 节）。
> 五阶段 = 需求 → 概要设计 → 详细设计 → 实现 → 审核，映射进 Trellis 的 planning/in_progress 状态机：
> **Phase 1 Plan 承载前三阶段（三道文档 Gate），Phase 2/3 承载实现与审核（verify 强制）。**
> 规则唯一真源：`.trellis/spec/`（guru-flutter-client spec 库）；本文件只做流程路由，不复写规则正文。

---

## Core Principles

1. **Plan before code** — 需求/概要/详细三 Gate 全过才能 `task.py start`
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

### Planning Artifacts（guru 五阶段语义）

- `prd.md` — **需求阶段产物**：行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、未决问题。不含技术设计。
- `design.md` — 两章结构：**§1 概要设计**（行为集合、行为→owner 归属表+三问理由、页面流、技术决策承接、详细设计承接索引）；**§2 详细设计**（按承接索引逐 doc_type 展开合同八问）。
- `implement.md` — **实现计划**（trace 合同 §1：任务切片/顺序/风险，见 `.trellis/spec/harness/implementation/implementation-trace-contract.md`）；实现期持续追加 §2 执行 / §3 证据 / §4 阻塞偏差。
- `implement.jsonl` / `check.jsonl` — spec/research 注入清单（见 1.5）。

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
- **核心玩法 / 付费 / 广告 / 存档 / 涉权限或数据采集 → 必须走完整五阶段**；小改可走轻量链（prd 简版 + 所碰层的详细合同 + 实现），但每步仍要 Gate。
- 建任务许可 ≠ 实现许可：实现必须等三 Gate 全过后 `task.py start`。

[workflow-state:no_task]
无活动任务。先分类本轮请求并征得任务创建同意。小任务：问是否建 Trellis 任务，不建则跳过。复杂任务：征得同意后建任务进入 planning。核心玩法/付费/广告/存档/权限类需求必须走完整五阶段链。
[/workflow-state:no_task]

### Phase 1: Plan（承载 需求 → 概要 → 详细 三阶段）

- 1.0 创建任务 `[required · once]`（征得同意后）
- 1.1 需求阶段 `[required · repeatable]`（`prd.md` + 需求 Gate）
- 1.2 研究 `[optional · repeatable]`
- 1.3 概要设计 `[required · repeatable]`（`design.md` §1 + 概要 Gate）
- 1.4 详细设计 `[required · repeatable]`（`design.md` §2 + `implement.md` + 详细 Gate）
- 1.5 配置上下文 `[required · once]`（jsonl 必含 harness SSOT + 项目约定）
- 1.6 激活任务 `[required · once]`（三 Gate 全过 → `task.py start`）
- 1.7 完成判定

[workflow-state:planning]
按 design.md 章节存在性定位当前步骤：无 prd.md→1.1 需求；prd 过 Gate 无 design.md §1→1.3 概要；§1 过 Gate 无 §2→1.4 详细。
1.1 需求：trellis-brainstorm 探索 + 行为规格口径（Given/When/Then + P0/P1 + 失败路径 + 验收）写 prd.md。需求 Gate：无行为/前置/状态变化/失败路径/验收场景 → 不进概要。
1.3 概要：加载 client-design-overview-writing 写 design.md §1（归属表+三问+承接索引）。概要 Gate（client-design-overview-review）：行为无 owner 证据/违反分层依赖律 → 不进详细。
1.4 详细：加载 client-design-detail-writing 写 design.md §2（合同八问）+ implement.md（trace §1）。详细 Gate（client-design-detail-review）：合同追溯不到 owner/无测试映射/涉权限无合规依据 → 不进实现。
1.5 配置 jsonl：implement.jsonl/check.jsonl 必含本任务所读 harness SSOT、golden-path、project-conventions（带 reason）。
每道 Gate 由人工判定（review skill 给互斥结论）；Gate 不过回本步修订，禁止硬推进。全 Gate 过后 1.6 task.py start。
[/workflow-state:planning]

[workflow-state:planning-inline]
同 [workflow-state:planning] 的三步推进与 Gate 口径；inline 模式跳过 1.5 jsonl 策展，Phase 2 经 trellis-before-dev 直接读 spec。
[/workflow-state:planning-inline]

### Phase 2: Execute（实现阶段）

- 2.1 实现 `[required · repeatable]`
- 2.2 质检 `[required · repeatable]`
- 2.3 回退 `[on demand]`

[workflow-state:in_progress]
Flow: trellis-implement（按 flutter-implementation-guru-writing 口径）→ trellis-check（按 flutter-implementation-guru-review 口径）→ trellis-update-spec（萃取九段）→ commit（3.4）→ /trellis:finish-work。
实现口径：golden-path 迷你路径 + 项目约定槽位取值；implement.md 持续记 trace §2 执行/§3 证据（analyze/test 命令与结果）/§4 阻塞偏差；禁止执行 l10n 同步脚本；不私自拍板新决策（记 §4 升级人工）。
质检口径：与 design.md 合同一致性 + 分层依赖律/canonical + **存量豁免判定**（SLOT-15 清单内记债不阻塞；清单外新增违例阻塞）+ 合规红线。实现 Gate：analyze/test/lints/compliance 任一无证据 → 不进 commit。
发现设计缺陷 → 回 Phase 1 对应阶段修订（status 不变），修完重入 2.1；禁止在代码里绕过设计。
Dispatch prompt 以 `Active task: <task path>` 开头；sub-agent 不再自派 implement/check。
[/workflow-state:in_progress]

[workflow-state:in_progress-inline]
Flow: trellis-before-dev → 按 golden-path+约定编辑 → trellis-check（guru 审核口径含存量豁免）→ 验证证据记 implement.md → trellis-update-spec → commit（3.4）→ /trellis:finish-work。inline 模式不派 sub-agent。
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

[Claude Code, Cursor, OpenCode, codex-sub-agent, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

- 需求不清 → `trellis-brainstorm`（需求阶段口径）。
- 概要/详细撰写 → `client-design-overview-writing` / `client-design-detail-writing`；Gate 判定 → 对应 `*-review`。
- `in_progress` 实现/质检 → dispatch `trellis-implement` / `trellis-check`（guru 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`（萃取九段）。

[/Claude Code, Cursor, OpenCode, codex-sub-agent, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]

[codex-inline, Kilo, Antigravity, Windsurf]

- 需求不清 → `trellis-brainstorm`；概要/详细 → `client-design-*-writing/review`。
- 编辑前 → `trellis-before-dev`；编辑后 → `trellis-check`（guru 口径）。
- 反复 debug → `trellis-break-loop`；spec 回写 → `trellis-update-spec`。

[/codex-inline, Kilo, Antigravity, Windsurf]

### Guardrails

- 任务创建同意 ≠ 实现同意；实现等待三 Gate 全过后的 `task.py start`。
- 合规 STOP：任何可能违反 App Store / Google Play 政策或美国法规的不确定性 → 立即停止，输出风险点+替代方案+人类确认清单。
- 三条最高禁令（见 Trellis System 节）全程生效；planning 必须落盘到 task artifacts；完成报告前必须有验证证据。

### Loading Step Detail

```bash
python3 ./.trellis/scripts/get_context.py --mode phase --step <step>
```

---

## Phase 1 步骤细则

#### 1.0 创建任务 `[required · once]`

与 Trellis 原版一致：`task.py create "<title>" --slug <name>`（仅 create，不 start）。多交付物用 parent/child 树。

#### 1.1 需求阶段 `[required · repeatable]`

加载 `trellis-brainstorm` 探索需求，产物口径按需求 SSOT：`prd.md` 必含行为规格（Given/When/Then）、核心能力清单（P0/P1）、失败路径、验收场景、显式未决问题（一次问用户 1~4 个，不私自拍板）。
**需求 Gate**：上述五要素缺一 → 留在本步修订。

#### 1.2 研究 `[optional · repeatable]`

与 Trellis 原版一致（`trellis-research` sub-agent 或 inline，产物落 `{TASK_DIR}/research/`）。

#### 1.3 概要设计 `[required · repeatable]`

加载 `client-design-overview-writing`（`.agents/skills/`），硬前置装载 `.trellis/spec/harness/overview/overview-structure-single-source.md` + golden-path + 项目约定。产出 `design.md` **§1 概要设计**。
**概要 Gate**：加载 `client-design-overview-review` 审核，结论"可进入详细设计"方可进 1.4；归属违反分层依赖律 = 直接 fail。

#### 1.4 详细设计 `[required · repeatable]`

加载 `client-design-detail-writing`，按 §1 承接索引展开 `design.md` **§2 详细设计**（逐 doc_type 合同八问），并产出 `implement.md`（trace §1 计划）。
**详细 Gate**：加载 `client-design-detail-review` 审核，结论"可进入编码"方可进 1.5/1.6。

#### 1.5 配置上下文 `[required · once]`

按平台与 Trellis 原版一致地策展 `implement.jsonl` / `check.jsonl`，**guru 必含条目**：本任务涉及的 `harness/` SSOT 文件、`guides/golden-path.md`、`conventions/project-conventions.md`（各带 reason）。inline 平台跳过。

#### 1.6 激活任务 `[required · once]`

前置 = 三 Gate 结论均为"可进入"（或"带明确假设可进入"且假设已记录）。然后 `task.py start <task-dir>`。

#### 1.7 完成判定

| 条件 | 必须 |
|------|:---:|
| `prd.md` 过需求 Gate | ✅ |
| `design.md` §1 过概要 Gate | ✅ |
| `design.md` §2 过详细 Gate | ✅ |
| `implement.md`（trace §1）存在 | ✅ |
| jsonl 含 harness SSOT + 项目约定条目 | ✅（inline 平台除外） |
| `task.py start` 已执行 | ✅ |

---

## Phase 2 / Phase 3 步骤细则

与 Trellis 原版同构（dispatch 协议、commit 批量确认流程、finish-work 收尾不变），仅口径替换：

- **2.1 实现**：sub-agent 按 `flutter-implementation-guru-writing` 口径（golden-path 迷你路径组合 + 逐片验证 + trace 持续更新）。
- **2.2/3.1 质检**：`trellis-check` 按 `flutter-implementation-guru-review` 口径（合同一致性、分层律/canonical、存量豁免、合规红线、证据核查）。
- **2.3 回退**：质检暴露 prd/design 缺陷 → 回 Phase 1 对应步骤修订产物，再重入 2.1。
- **3.3 Spec 回写**：`trellis-update-spec` 按 `.trellis/spec/harness/extraction-template.md`（萃取九段结构）；即使结论是"无可沉淀"也要走判断。
- **3.4 Commit**：与原版批量 commit 流程一致（不 amend、不 push、一次性确认）。

---

## Customizing

本文件遵循 Trellis 官方 workflow 定制契约（`[workflow-state:*]` 块为唯一 per-turn breadcrumb 来源；scripts 只是 parser）。修改本文件后运行 `trellis update` 或重启会话生效。深层契约见 Trellis 原版 workflow.md 的 "Customizing Trellis (for forks)" 节与 `.trellis/spec/cli/backend/workflow-state-contract.md`（上游仓库）。
