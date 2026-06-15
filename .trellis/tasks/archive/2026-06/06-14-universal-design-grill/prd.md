# 通用化 design-grill skill 与跨工具 grill 触发

## Goal

把当前按平台分散的 4 份 grill skill（`client-grill` / `go-design-grill` / `h5-design-grill` / `ios-design-grill`）收敛为**一份通用 `design-grill` skill**：拷问方法论写死，运行时读 `.trellis/spec/` 自动发现各端领域模型对照物（加新端零改动）；同时修复"grill 从未被主动触发"的根因，做成 **Codex 与 Claude Code 两种工具下都能生效**的触发机制。

用户价值：各端（flutter/go/h5/前端…）共享同一套 Gate 前拷问能力，维护一份而非 N 份；且拷问真正会被触发，而不是装了却从没人用。

## Confirmed Facts（已查实的诊断）

- **hook 层已通用化**：`grill-nudge.sh` 是单模板 + `__GRILL_SKILL__` 占位符，`apply.sh` 按平台 sed 替换（flutter→client-grill、go→go-design-grill、h5→h5-design-grill、ios→ios-design-grill）。未通用化的是 **skill 本体**——4 份独立，两两差异 75–87 行（文件本身 38–79 行）。
- **grill 从未成功触发过**：himora 项目 `.trellis/tasks/` 下有 prd.md/design.md，但**零个 `.grilled-*` 标记**，证明 nudge 从未响过。
- **根因三层**：① 机制上限只是"提示（exit 2 塞 stderr）"，不能自动执行；② 它是 Claude Code 的 `PostToolUse` hook，而需求/设计常用 **Codex** 写，Codex 不执行 `.claude/hooks/`；③ 即便在 Claude 下，命中条件过窄（仅 `Write/Edit` 命中 `.trellis/tasks/.../prd.md|design.md` 且过 `guru_gate.py`），而设计常写在 `docs/design/...`。
- himora 装的是旧名 `client-grill-nudge.sh`（未升级到平台化 `grill-nudge.sh`），settings.json 已注册但因上述原因从未生效。
- 拷问**方法论是各端通用的**（逐分支拷问、一次一问带推荐答案、磨术语、压测边界、与代码交叉核对、决策当场固化）；**对照物是端特异的**（flutter 的 golden-path 分层/BHV-UNIT 编号 vs go/h5/ios 各自规范）。

### 探索回填（understand workflow，4/5 维度）

- **骨架可抽**：四端方法论骨架高度同构（做什么 / 会话六动作 / 决策四去向 / ADR 三条全中 / 边界），可抽成一份；端特异只集中在「拷问对照物清单」「触碰红线→fail 回退」两节及示例术语。`client-grill` 是最早简版（38 行，缺 doc_type 七类枚举与独立红线 fail 节），**合并须以 go/h5/ios 加厚版为基线**，否则丢失"红线 fail 回退"关键能力。
- **spec 可盲读**：四个 guru 平台模板在固定相对路径上 100% 具备锚点（`guides/golden-path.md`、`conventions/project-conventions.md`、`conventions/index.md`、`harness/overview/overview-structure-single-source.md`）；安装后平台前缀被剥离为 `.trellis/spec/<layer>/`。运行时盲读可行，**无需新增"对照物清单"文件**（四锚已是事实清单）。
- **适用域裂缝**：vanilla（非 guru）Trellis 项目（**本仓库自身**）无这套锚点 → 通用 grill 适用域必须界定为"guru 系平台"，skill 开篇需做**适用域门控**，探测不到锚点即降级/退出，不能假设所有 Trellis 项目都有 golden-path。
- **doc_type 源不一致**：ios 把 doc_type→owner 映射放 `conventions/index.md §5`，go/h5 放 `harness/overview/overview-structure-single-source.md` → 通用 skill 需**双候选探测**（或未来统一到单一路径）。
- **Codex 触发根因纠正**：Codex **有**可编程 hook（PreToolUse/PostToolUse/UserPromptSubmit/SessionStart 等，himora 已 trust），但其 Pre/PostToolUse **只对 Bash 触发，对 `apply_patch/Edit/Write` 文件写入不 fire**（openai/codex #15486）。这才是 grill-nudge 在 Codex 永不响的真正根因——不是"Codex 不执行 hook"。
- **跨工具真正可靠点**：`guru_gate.py` 是两工具共用的纯 Python gate，`cmd_confirm` 逐 gate 跑 checker、不过即 BLOCK；**在此加 `.grilled` 标记前置校验即天然跨工具**，绕开 Codex hook 限制。`UserPromptSubmit` 型 `inject-workflow-state.py` 两边共用，可作软提示通道。
- **标记语义缺陷**：现 `.grilled-*` 标记由 `grill-nudge.sh` 在"提示时"写（语义=已提示），若直接用作 gate 硬前置会"一提示就解锁"；须改为 **grill 拷问完成落盘后才写**（语义=已拷问），否则前置失去意义。
- **apply.sh 改动单一**：把 `design-grill` 加进 `SHARED_SKILLS` 即四平台都装；可删 `GRILL_SKILL` 变量与 sed 行、把模板占位符硬写为 `design-grill`。需同步改 workflow / trellis-local / chapter-guide / incident。（注：原"旧 4 份靠剪枝自动删"被二次重核**部分推翻**，见下。）

### 二次重核回填（代码变更后，recheck workflow 3/3 维度）

> 计划成文后代码演进了多个 commit（`762b62ac` shared 三件套、`ee577e8e`/`71442454`/`b74af292` skill 双面镜像+自检不变量、`258aca72` apply 自检硬失败、`77f8703b` 等）。以 HEAD 为基线重核：

- **路径修正**：`guru_gate.py` 源在 `guru-template/overlay/verify/guru_gate.py`（937 行），装到目标 `.trellis/scripts/guru/guru_gate.py`；Codex/Claude 共用同一份（之前误写 `.trellis/scripts/guru/` 为源路径）。
- **硬前置落点（纠正）**：`guru_gate.py` 当前**完全无 grill 字样**。`258aca72` ≠ before_start（只是 apply 在 core 缺 `run_blocking_task_hooks` 时硬失败）。`task.py start` 有两条放行路径——Codex：`config.yaml before_start → guru_gate.py check`；Claude：`PreToolUse block-unconfirmed-start.sh → guru_gate.py check`。`cmd_check`（:792-837）只验三道 confirm 落盘+快照一致，**不验 grill**。故只挂 `cmd_confirm` 会被"手写 guru_gates 绕过 confirm"破防 → **须同时挂 `cmd_confirm`（:704-751，循环内 :736 结构 checker 通过后）+ `cmd_check`（:799-806 结构复跑段）**。
- **gate↔art 非对称映射**：`HUMAN_GATES=("requirements","overview","detail")`（:563）；标记 art 用产物名：requirements→`.grilled-prd`、overview→`.grilled-design`。**detail 当前无 grill 标记机制**（grill-nudge 只覆盖 prd/design）。
- **标记语义冲突（纠正）**：`grill-nudge.sh` 现在仍写 `.grilled-*`（:22 touch，语义=已提示/幂等去重），`guru_gate.py` 不读它。硬前置**不能复用**该标记当"已拷问" → 须用独立标记 `.grill-done-<art>`（由 design-grill 拷问收口时写），grill-nudge 改写 `.grill-nudged-*`。
- **双面镜像/自检不变量（新硬约束）**：`§4.5` 双面对齐（apply.sh:147-207）+ `§8` `diff -rq` 内容级两面一致断言（:536-548，不一致 FAIL=1 硬失败）。design-grill 进 `SHARED_SKILLS` 由 §1/§4 两面装、字节一致即满足；但"建目录"与"进 SHARED_SKILLS"是**成对硬步骤**（缺一全不装或装不上）；项目镜像模式（`USED_PROJECT_MIRROR=1`，himora 类）走 `sync_platform_skills.py --check`，design-grill 须被该脚本纳管。
- **剪枝盲区（纠正关键坑）**：剪枝只 `rm -rf` `GURU_SKILLS` 集合内的名字。物理删旧 4 目录后旧名落出集合 → 已装项目的旧残留**不被自动清除**，反被 §4.5 当"非 guru 用户 skill"双向复制污染两面。需 legacy 迁移策略（见 D-A）。
- **Codex 生效前提**：挂 `cmd_check` 的硬前置在 Codex 依赖 core `run_blocking_task_hooks`（guru fork CLI bootstrap）；上游 CLI 装的项目 Codex 侧 before_start 被静默忽略 → grill 硬前置随之失效。Claude 侧有独立 PreToolUse，不依赖 core。
- **opt-out 性质**：标记文件在 agent 可写信任域，strict 的 TTY 守卫（:712-721）挡常规 agent，但蓄意 agent 仍可自建 skip + 分配 pty 绕过 → **诚实性辅助，非安全边界**，文案须同口径声明。
- **旧名引用更多**：8 文件约 21 处（4 workflow×4 + trellis-local×2 + 2 chapter-guide×2 + incident×1 + grill-nudge 注释×1）；`ios-design-overview-writing` 的 chapter-guide 误引 `client-grill`（命名已乱，统一成 design-grill 反而修了这个 bug）。
- **行号漂移**：apply.sh sed 在 `:120`（非 84）；grill-nudge 文案占位符在 `:23`（非 20，因 :16-18 插入 cd 锚定块）。落地按 grep 内容匹配，不按行号。
- **测试基线**：`apply_test.sh` 15 场景无 grill 覆盖，但场景1（:36-37 `diff -r` 双面一致）、场景4（:99-103 平台 apply）是现成断言模板；`run_tests.sh` confirm 测试群（:216-249）可复用 mk_pkg/$G 夹具挂 grill 单测。`guru_after_create.py` 改动（jsonl 末行换行守卫）与 grill 零冲突。

## Requirements（草案，待规划细化）

- **R1** 单 `design-grill` skill 替换 4 份 per-platform skill：通用拷问骨架写死 + 运行时读 `.trellis/spec/` 自发现本端对照物。
- **R2** 加新端无需新增/修改 skill（对照物来自该端自有 spec）。
- **R3** 跨工具触发：Codex 与 Claude Code 下，需求/概要产物成形后都能被提示去 grill。
- **R4** `apply.sh` 安装/剪枝逻辑同步：只装一份 design-grill，清理 4 份旧 skill 与历史 hook 名（含 `client-grill-nudge.sh`）。
- **R5** 不破坏现有 `trellis-brainstorm`（探索生成）/ `*-review`（判定）/ `guru_gate` 的分工与契约。

## Acceptance Criteria（草案，待补全）

- [ ] `init` 出来的各端项目只装一份 `design-grill`，无 4 份残留、无历史 hook 名残留。
- [ ] `design-grill` 在 flutter/go/h5/ios 项目中运行时能正确加载**本端**领域模型对照物。
- [ ] Codex 与 Claude Code 两种工具下，写完需求/概要产物后都能收到 grill 提示。
- [ ] 现有 review-gate 流程（brainstorm → grill → review → 人工 Gate）行为不回归。

## Out of Scope（草案）

- 不重写各端 `.trellis/spec/` 内容本身（grill 只读取，不改写）。
- 不改 `*-review` skill 与人工 Gate 的判定逻辑。

## 已据证据决定的技术选择（写入 design，不再问用户）

- **对照物发现策略**：运行时按固定相对路径盲读四锚（golden-path / project-conventions / conventions-index / harness-overview），doc_type/红线/SLOT 一律现读现转述，不在 skill 内联任何端的具体类目；软锚（项目域子目录、CONTEXT.md、docs/adr）用"存在即加载"的 glob；doc_type 源做双候选探测。
- **适用域门控**：skill 开篇探测 guru 锚点，缺失即判定"非 guru 领域模型布局，grill 降级/退出"。
- **标记语义**：新增独立标记 `.grill-done-<art>`（design-grill 拷问收口写）；grill-nudge 的 `.grilled-*` 改写 `.grill-nudged-*` 仅作提示幂等；gate 只认 `.grill-done-*`。
- **硬前置挂载点**：同时挂 `cmd_confirm`（:736 后）+ `cmd_check`（:799-806），覆盖人工收口与 Codex/Claude 两条 `task.py start` 放行路径。
- **apply.sh**：`design-grill` "建目录 + 进 `SHARED_SKILLS`"成对（缺一不装/装不上）；删 `GRILL_SKILL`/sed、占位符硬写；新装项目无旧残留，已装项目 legacy 清理见 D-A。
- **合并基线**：以 go/h5/ios 加厚版为骨架基线，保留"红线 fail 回退"能力。

## Decisions（已拍板）

- **D1 触发硬度** = 全任务硬前置 + 用户可主动 opt-out（不做 light 自动豁免）。
- **D2 命名/兼容** = 硬切单一 `design-grill`，不留别名。
- **D3 落地范围** = 只改模板库，存量下次 apply 升级。
- **D-D 硬前置挂载点**（据二次重核定，技术决策）= **同时挂 `cmd_confirm` + `cmd_check`**——只挂 confirm 会被"手写 guru_gates 绕过 confirm"破防。

## Open Questions（二次重核新增，需用户拍板）

- **D-A legacy 残留清理**：物理删旧 4 grill 目录后，已装项目旧残留不被剪枝、反被 §4.5 双面对齐污染。策略？① 旧 4 名在 `GURU_SKILLS` 保留一个过渡版本专供剪枝（下版再删目录）② apply 加一次性 legacy grill 清理代码 ③ 仅文档告知用户手动删。
- **D-B grill 标记是否校验 digest**：`.grill-done-<art>` ① 仅存在性（写空也解锁，改产物后不重 grill）② 含 `artifact_digest`，产物变更后失配需重 grill（更严，与现有 check 快照机制一致）。
- **D-C detail gate 是否纳入硬前置**：当前 grill 只覆盖 requirements/overview（prd/design）。detail 阶段要不要也强制 grill？（要则需先给 detail 定义标记机制。）→ **被对抗审查重开，见下。**

## 对抗审查回填（Codex，裁决 reject — 完整报告 `research/codex-adversarial-review.md`）

已回到真实代码逐一交叉验证，**5/5 最关键发现全部属实**。下列缺陷**直接采纳进 design/implement**：

1. **【致命】漏发布面**：`packages/cli/src/templates/guru/` 是分发真源（`index.ts` 注明编辑 `guru-template/` 后须 `pnpm -C packages/cli sync:guru`），bundled workflows 四份仍旧名、`packages/cli/test/guru/guru-bundled.test.ts:43` 硬断言 `client-grill`。→ 实施须 sync + 更新 bundled + 改测试断言 + 全仓 `rg` 验证。
2. **【高危】第三放行路径**：`worktree.yaml verify → guru_gate.py auto`（:840）只跑结构 gate、不读 confirm/grill。双挂 confirm+check 仍漏此路径。→ grill 校验须覆盖 verify→auto（planning 阶段）或显式划定边界。
3. **【高危】digest 失配/函数名错**：无 `artifact_digest()`，只有 `_gate_digest(task_dir,gate)`；`_gate_artifacts` 是累积集。→ 需新定义 `grill_digest(task_dir,art)` 明确 art→文件集，或把 grill 状态纳入 confirm。
4. **【高危】镜像模式**：`USED_PROJECT_MIRROR=1` 时 §4.5 跳过、§8 只调外部脚本 `--check`，design-grill 两面一致全靠外部脚本。→ 定义脚本契约 + apply_test fixture + 显式两面校验。
5. **【高危】门控混淆"路径存在 vs 约定可用"**：四包仅 `*.template.md`、Go 路径漂移。→ 门控三态（非guru / guru但约定未就绪→阻断提示 / 可grill）+ 权威源选择+冲突 fail。

**其它直接采纳**：legacy `rm -rf` 改"托管身份判断 + 备份到 `.trellis/backup/`"（不无脑删）；apply 加 SHARED↔目录成对自检 + design-grill 两面在/旧名两面无断言；"防绕过"措辞改"防无意绕过/流程纪律"（guru_gate 自述 integrity aid 非安全边界，:554-561）；合并验证标准改"行为等价矩阵 + 本端拷问清单摘要"（端特异红线是触发 cue，非示例术语，删了会降触发质量）；补 GitNexus 不可用降级、旧 `.grilled-*` 标记迁移、"用户如何合法完成 grill"交互合同。

**触发两个需用户重新拍板的决策**（见下）：

## Open Questions（对抗审查后新增/重开）

- **E1 架构路线**：是否采纳 Codex 的"更简更稳"方案？= ①旧 4 名保留为**薄 wrapper（alias 指向 design-grill）**而非 `rm -rf` 硬删；②grill 凭据**走 `guru_gate.py` 命令记录到 `guru_gates`**（复用 confirm 的 TTY/soft 审计 + 原子写 + digest），不引入"agent 自由写 `.grill-done-*` 文件"这一伪造面；③按"可运行状态"三阶段拆 commit、每步可独立 revert。代价：旧 wrapper 临时共存、分三阶段。**这会推翻原 D2 硬切/D-A legacy/D-B 文件标记/D-D 落点。**
- **E2（D-C 重开）detail 是否纳入 grill**：Codex 论证 detail 才是"实现前最后一道设计合同"（合同八问/失败收口/测试映射），最该 grill，反对豁免。要重新决定 detail 是否纳入。
