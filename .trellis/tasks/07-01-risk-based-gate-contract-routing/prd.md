# Risk-based intake routing with gate contracts

## Goal

实现一套 Guru/Trellis 收到任务后的风险分流机制：低风险自动走小改 inline，中风险走 lite task，高风险强制 full chain；同时把本任务允许的 gate 合同和实际降级记录落在任务目录中，让 commit gate 能区分“按合同降级”和“无记录绕过”。

## Background

问题会话 `019f1db7-3122-7f03-9644-4a7101dc73a0` 暴露了一个流程错配：一个很小的 UI 颜色改动被拖进 GitNexus/Guru 全链，期间 GitNexus 因 native binary 架构不匹配失败，commit 又因没有 ready task / planning task 歧义被阻断。这个问题不能靠口头“下次灵活一点”解决，需要在任务入口、task-local 合同、工具失败降级、commit gate 之间建立可复跑合同。

当前 Guru 已有一些基础：

- `task.json.guru_chain` 已支持 `full|light`，`guru_after_create.py` 默认写 `full`，降为 `light` 需要分流和用户同意。
- `client-small-iteration-dev` 已描述轻量链入口决策树，但当前规则仍以“用户同意降 light”为主，没有 low/medium/high 三档 intake contract。
- `guru_risk.py` 已有 `high|low|unknown` 风险 helper，并对 cross-layer/storage/payment/ads/permission/privacy 等信号 fail-closed。
- `guru_gate.py check-commit` 当前要求 `check-implementation` 通过、staged scope 落在最新 clean implementation review 的 `target_paths` 内，并拒绝仅提交 task/workspace artifacts。
- 当前本 worktree 没有 `.trellis/scripts/guru/` 本地 runtime，因此实现目标大概率是 Guru overlay/template 源，而不是只修当前本地 `.trellis/`。

本任务要演进这些已有机制，不新造一套平行状态机。

## Scope

In scope:

- 任务入口的风险分类：`low` / `medium` / `high` / `unknown`。
- 路由结果：`small_inline` / `micro_task` / `lite_task` / `full_chain`。
- 任务目录内的 `gate-contract.json`、`gate-degradations.jsonl`、`gate-evidence/`。
- Guru template / overlay / workflow / skills / gate scripts / tests 的同步方案。
- commit gate 读取全局 gate policy、任务合同、实际 staged diff 和降级证据。
- GitNexus 或其他 gate/tool 不可用时的允许降级、补偿检查和留痕。

Out of scope:

- 取消现有 `guru_chain=full|light`。
- 让高风险任务通过 task-local 文件绕过 full chain。
- 自动修复 GitNexus native binary / Node 架构问题。
- 将所有低风险对话都强制建 full task。
- 在本 PRD 阶段直接修改 runtime/template 代码。

## Definitions

- **risk**: intake 对任务影响面和失败代价的判断，取值 `low|medium|high|unknown`。
- **route**: 风险判断后的执行路径，取值 `small_inline|micro_task|lite_task|full_chain`。
- **gate-contract**: 任务目录中的选择结果，记录本任务采用的 route、允许的 gate、允许的降级、必需的补偿检查和 commit 条件。
- **gate-degradation**: 事实记录。只有 gate/tool 实际失败、不可用或被合同允许降级时才追加，不能预先写成绕行许可。
- **global gate policy**: 模板/脚本中的全局规则，决定哪些 gate 可以降级、哪些必须 fail-closed。task-local contract 只能选择和记录，不能扩大权限。
- **small_inline**: 无 task 或只在当前会话内处理的小改路径；默认不产生可提交合同。
- **micro_task**: 低风险但需要 commit 时自动创建或复用的最小任务；它只承载 scoped commit contract，不进入 full planning chain。
- **lite_task**: 中风险任务，使用轻量链的 PRD + 单文件 design / implement trace + 必要 review/check。
- **full_chain**: 高风险任务，强制 Guru full 五阶段，不能被 task-local contract 降为 lite/micro/inline。

## Confirmed Decisions

- DEC-001: 使用三档风险分流。`low` 自动执行小改；`medium` 执行 lite；`high` 强制 full。
  user_quote: "低风险自动执行，中风险执行 light, 高风险强制 full"；latest_update: "light 改为 lite"
- DEC-002: gate contract 和 gate degradation 放在任务目录中管理。全局规则仍决定可降级边界，任务目录只记录本任务选择和事实证据。
  user_quote: "门禁的降级/绕行合同 能否和任务文件夹中管理？ 这样是否更好？"
- DEC-003: 收到任务后先分析收集任务信息，再按任务难度或类别自动选择，必要时让用户选择不同的 `gate-contract` 或 `gate-degradation`。
  user_quote: "可以做到收到任务后，分析收集任务信息和根据任务难度或类别自动或让用户选择不同的:gate-contract 或 gate-degradation 吗？"
- DEC-004: 轻量/复杂不新增 runtime status，优先用 task metadata、contract 和 route 表达，避免污染 Trellis status 状态机。
  confirmed_ref: 当前 repo 的 `trellis-continue` / workflow 仍以 `planning|in_progress|completed` 驱动，新增 status 会扩大恢复路由和 hook 同步面。
- DEC-005: 本任务先改 Guru source/template，即 `packages/cli/src/templates/guru/**` + `guru-template/**`；仅当验证确实需要时，才最小 dogfood 当前本地 `.trellis` / hooks 文件。
  user_quote: "是，先改 source/template，必要时最小 dogfood 本地文件。"
- DEC-006: 新风险 route 术语统一使用 `lite` / `lite_task`；既有兼容字段和产物形态 `task.json.guru_chain=light` 保持不变。
  user_quote: "light 改为 lite"

## Behavior Specifications

### BHV-001 低风险小改自动执行

Priority: P0

Given 用户提出只影响局部 UI、文案、注释、格式、非共享配置或等价低风险变更，且无支付、广告、权限、隐私、DB/schema、跨层状态、workflow/hook/gate 修改信号。
When intake classifier 收集任务信息并完成风险判断。
Then 系统应给出 `risk=low`、`route=small_inline`，默认不创建 full Trellis task，不要求 full Guru gate；如果用户随后要求 commit，则自动创建或复用 `micro_task` 并写入最小 `gate-contract.json`。

### BHV-002 中风险局部行为变更进入 lite task

Priority: P0

Given 用户请求会改变局部业务行为、局部页面交互、单层代码逻辑或需要可复跑测试，但没有 high-risk 信号。
When intake classifier 判定该任务不是纯 small inline。
Then 系统应给出 `risk=medium`、`route=lite_task`，创建/进入轻量任务，写入 `gate-contract.json`，并要求轻量链所需 PRD、设计、实现 trace、验证和 commit 条件。

### BHV-003 高风险任务强制 full chain

Priority: P0

Given 用户请求涉及支付、广告、权限、隐私/数据采集、DB/schema 迁移、跨服务/跨层协议、核心工作流、gate/hook/workflow/runtime、持久化状态、发布交付链或安全合规。
When intake classifier 或后续 staged diff / task metadata 命中任一 high-risk 信号。
Then 系统必须给出 `risk=high`、`route=full_chain`，保持或写入 `guru_chain=full`，拒绝 task-local contract 将其降为 `lite_task`、`micro_task` 或 `small_inline`。

### BHV-004 工具失败按合同降级并留证据

Priority: P0

Given GitNexus、semantic review provider、adversarial worker 或其他 gate/tool 不可用。
When 当前任务合同允许该 gate 的降级。
Then 系统必须追加 `gate-degradations.jsonl`，记录失败命令、stderr 摘要、时间、影响 gate、允许依据、补偿检查和操作者；commit gate 只有在补偿检查满足时才能继续。

### BHV-005 工具失败但合同不允许时 fail-closed

Priority: P0

Given gate/tool 失败发生在 high-risk 或合同未允许降级的 gate 上。
When 用户或 agent 尝试继续实现、check 或 commit。
Then 系统必须 fail-closed，提示缺失 gate、失败证据和可恢复动作，不得把失败记录伪装成通过。

### BHV-006 commit gate 使用 staged scope 与任务合同共同判定

Priority: P1

Given 用户执行 commit，当前 repo 存在 active Guru task 或 micro/lite/full task contract。
When commit hook 或 `guru_gate.py check-commit` 运行。
Then gate 必须读取 staged paths、当前任务 `gate-contract.json`、`gate-degradations.jsonl`、最新 review/check record，并确认 staged scope 属于合同允许范围；仅 task/workspace artifacts、越界文件、缺少 clean review 或缺少允许降级证据都必须被阻断。

### BHV-007 Finish 阶段按 route 使用不同完成预算

Priority: P0

Given 任务已经进入 Finish 阶段，且已有 route 或 task-local gate contract。
When agent 执行质量验证、spec update、worker cleanup、commit 前检查。
Then 系统必须按 `direct_small_inline|micro_task|lite_task|full_chain` 选择不同 finish budget；`micro_task` 默认不阻塞于 spec update，`lite_task` 仅在命中 reusable contract 时执行轻量 spec update，`full_chain` 保持完整 Phase 3.3。

### BHV-008 mutable evidence 不得造成 detail digest 失配

Priority: P0

Given detail Gate 已经基于当前 design / implement contract 确认。
When agent 追加测试结果、`detect_changes` 结果、spec 萃取、worker cleanup 或 commit-plan 证据。
Then 这些 mutable evidence 必须写入不参与 detail digest 的 evidence 文件；不得追加到 `implement.md` 后再要求 detail confirmation 保持 current。

### BHV-009 commit 前必须输出机器可读 commit plan

Priority: P1

Given 任务准备进入 `3.4 Commit` 或 direct low-risk commit。
When agent 或 hook 需要决定 staged scope。
Then `guru_gate.py commit-plan [task_dir]` 或等价命令必须输出 route、commit mode、allowed / forbidden paths、required evidence、blocking reasons 和 suggested stage commands；agent 不得临场读取 `guru_gate.py` 源码推断 stage 范围。

### BHV-010 terminal worker cleanup 不得拖慢 commit 前收口

Priority: P1

Given channel worker 已经处于 `done|killed|error` 终态。
When `guru_supervise status` 或 Finish 收口检查运行。
Then terminal worker 不得继续显示为 live blocker；系统应能自动归档或给出单条 cleanup 命令，主会话不应多轮 `pgrep` / `kill` / `status` 清理完成态 worker。

### BHV-011 commit-ready 后必须停止在用户确认边界

Priority: P0

Given route 对应验证已完成、gate status 已 ready、commit-plan 已生成。
When agent 到达 commit-ready。
Then agent 必须停止在 stage/commit/TAPD/archive 之前，向用户报告可执行的下一步，不得自动扩展到 spec rewrite、journal rewrite、archive、TAPD update 或额外 review。

### BHV-012 commit 前使用 compact commit context

Priority: P1

Given 会话已经进入 Finish / Commit 尾部，且上下文较大。
When agent 需要继续执行 commit 前检查。
Then agent 只加载 task_dir、route、latest review digest、validation evidence、dirty scope 和 commit-plan 摘要；不得重新加载完整 skill、memory、spec 全文，除非 commit-plan 明确报告缺口。

## Requirements

- REQ-001: intake classifier 必须输出结构化结果：`risk`、`route`、`confidence`、`reasons`、`risk_flags`、`recommended_contract`、`needs_user_choice`。
- REQ-002: risk 信号必须覆盖路径、文件类型、diff 类型、任务文字、task metadata、staged diff、已有 `guru_risk.py` high-risk reasons。
- REQ-003: `unknown` 风险必须 fail-safe。默认升为 `medium/lite_task`；如果出现 high-risk 关键词或扫描失败且无法排除高风险，则升为 `high/full_chain`。
- REQ-004: `low -> small_inline` 默认不建任务；但一旦用户要求 commit，必须创建或复用 `micro_task`，因为 commit 需要持久合同和 staged scope 证据。
- REQ-005: `medium -> lite_task` 必须写 `task.json.guru_chain=light` 或等价 task metadata，并记录分流理由。
- REQ-006: `high -> full_chain` 必须保持 `task.json.guru_chain=full`，并要求 full chain 所需 requirements / overview / detail / implement / check gate。
- REQ-007: `gate-contract.json` 必须位于任务目录，至少包含 schema version、route、risk、allowed scope、required gates、optional gates、allowed degradations、compensating checks、commit policy、created source 和 digest。
- REQ-008: `gate-degradations.jsonl` 必须 append-only；每行记录一个实际失败/降级事实，不能修改历史行伪造通过。
- REQ-009: `gate-evidence/` 用于保存无法简短放入 JSONL 的命令输出、截图、review 摘要或环境诊断；JSONL 只引用相对路径。
- REQ-010: 全局 policy 必须是降级权限来源。task-local contract 不得允许 policy 禁止的降级；高风险 gate 永远不能通过 task-local contract 绕过。
- REQ-011: `check-commit` 必须支持 micro/lite/full 三类合同，但 full 当前严格行为不能被削弱。
- REQ-012: GitNexus 不可用时，低风险/micro 合同可以允许 `rg` / 手工调用链 / `git diff --check` / scoped tests 作为补偿；中风险 lite 需要更强补偿；高风险必须 fail-closed 或要求人工明确改走 full review。
- REQ-013: 用户选择只发生在 classifier 置信度不足、多个 route 合理或 contract 会影响 gate 严格度时；低风险高置信路径应自动执行，不机械打断用户。
- REQ-014: workflow、skills、overlay scripts、tests、`guru-template` 与 `packages/cli/src/templates/guru` 镜像必须同步，避免安装后的行为与源码不一致。
- REQ-015: Finish 阶段必须有 route matrix：`direct_small_inline` 只做 scoped commit gate，`micro_task` 默认 spec update deferred，`lite_task` spec update conditional，`full_chain` spec update required。
- REQ-016: mutable evidence 必须独立于 detail digest，至少规划 `implementation-evidence.jsonl`、`verification-evidence.jsonl`、`spec-extraction.jsonl`、`worker-cleanup.jsonl` 或等价证据文件。
- REQ-017: `guru_gate.py commit-plan [task_dir]` 必须输出机器可读 JSON，包含 `route`、`commit_mode`、`allowed_stage_paths`、`forbidden_stage_paths`、`required_commands`、`blocking_reasons`、`suggested_stage_commands`。
- REQ-018: `check-commit` 后续必须复用 commit-plan 的同一个 decision model，避免 plan 与实际 hook 判定漂移。
- REQ-019: `adversarial_enabled=false` 和 route-aware bounded review policy 只能影响 adversarial 证据要求，不能绕过 current digest、double clean、blocked/medium+ finding、人工确认或 staged scope。
- REQ-020: Finish 阶段的 terminal worker cleanup 必须区分 live worker 和 terminal worker；terminal worker 不能成为 commit 前阻塞项。
- REQ-021: commit-ready 后必须触发 stop rule，只报告下一步确认项，不自动 stage、commit、TAPD update、archive 或额外 spec/journal rewrite。

## Failure Paths

- FP-001: GitNexus 命令失败且合同允许降级，但没有补偿检查证据：commit gate 必须阻断。
- FP-002: high-risk 任务写入 `gate-contract.json` 声称可走 lite/micro：gate 必须拒绝该合同并要求 full chain。
- FP-003: task-local `gate-degradations.jsonl` 存在记录，但失败 gate 不在 `allowed_degradations` 中：gate 必须阻断。
- FP-004: staged diff 越出 contract scope：commit gate 必须阻断。
- FP-005: 只有 task/workspace 文档被 staged：implementation commit gate 必须继续阻断，除非该 commit 明确是 planning/docs-only 路径且对应合同允许。
- FP-006: classifier 无法读取 git status / diff：不能判为 low；至少升为 medium，命中 high-risk 文本时升为 high。
- FP-007: `micro_task` 或 `lite_task` 在质量验证完成后把 spec 萃取记录追加进 `implement.md`，导致 detail digest 失配：gate 必须视为流程错误，要求迁移到 mutable evidence 文件。
- FP-008: commit-plan 显示 `split_required`，但 agent 仍把 task/spec/journal/tooling 文件混入 implementation commit：commit gate 必须阻断。
- FP-009: terminal done worker 被 status 当成 live blocker，导致 agent 多轮等待/kill：应作为 worker cleanup 缺陷记录，不应继续推进普通 review。
- FP-010: commit-ready 后 agent 未获用户确认却继续做 spec rewrite、journal rewrite、TAPD update 或 archive：违反 stop rule。

## Acceptance Criteria

- [ ] “修改未读小红点颜色”这类单文件、局部 UI 颜色任务被判为 `risk=low`、`route=small_inline`，默认不创建 full task。
- [ ] 同一低风险任务在用户要求 commit 时自动创建或复用 `micro_task`，生成 `gate-contract.json`，并允许记录 GitNexus native binary failure 的受控降级。
- [ ] “修一个局部业务行为 bug 并补测试”被判为 `risk=medium`、`route=lite_task`，需要 lite 任务产物和 scoped validation。
- [ ] “支付、广告、权限、隐私、DB/schema、workflow/hook/gate/runtime、跨层协议”任一命中时被判为 `risk=high`、`route=full_chain`，且 task-local contract 不能降级。
- [ ] `guru_gate.py check-commit` 对 micro/lite/full 合同有不同要求，但 full chain 现有 staged scope + clean implementation review 约束保持不弱化。
- [ ] GitNexus 不可用时，低风险合同能记录 `gate-degradations.jsonl` 并要求补偿检查；高风险合同同类失败必须 fail-closed。
- [ ] 单测覆盖 classifier route、contract validation、degradation validation、check-commit 合同读取、high-risk fail-closed、dirty worktree scoped staging、GitNexus unavailable fallback。
- [ ] 模板镜像一致性检查覆盖 `packages/cli/src/templates/guru/**` 与 `guru-template/**` 的对应文件。
- [ ] 文档/skill 明确说明 `gate-degradation` 是事实记录，不是预授权绕行单。
- [ ] `micro_task` 在质量验证完成后，缺少 spec update 不阻塞 implementation commit；系统记录 `spec_update=deferred|not_applicable`。
- [ ] `lite_task` 只有命中 reusable engineering contract 时才要求 spec update；普通局部 bugfix 可记录 deferred 后进入 commit-ready。
- [ ] `full_chain` 仍要求完整 Phase 3.3 spec update，现有严格行为不被削弱。
- [ ] 向 `verification-evidence.jsonl` 或 `spec-extraction.jsonl` 追加记录不会改变 detail digest；修改 `design.md` / `implement.md` 合同正文仍会改变 digest 并阻塞。
- [ ] `guru_gate.py commit-plan` 能为 direct small_inline、micro_task、lite_task、full_chain 输出不同 stage plan，并标注 split-required 文件。
- [ ] commit-ready 后 agent 停在用户确认边界，不自动 stage/commit/TAPD/archive。
- [ ] Finish 尾部不重新加载完整 skill/memory/spec；只使用 compact commit context 和 commit-plan 摘要。

## Open Questions

- 无阻断问题：OQ-001 已由当前用户回答，范围确定为先改 source/template，必要时最小 dogfood 本地文件。

## Brainstorm Evidence

- Skill loaded: 已加载 `trellis-continue`、`trellis-brainstorm`、`trellis-meta`，当前处于 Phase 1.1 requirement exploration。
- Repository evidence inspected: 已检查 `.trellis/workflow.md` / `get_context.py` 输出、`packages/cli/src/templates/guru/workflows/guru-client.md`、`packages/cli/src/templates/guru/overlay/verify/guru_risk.py`、`packages/cli/src/templates/guru/overlay/verify/guru_gate.py`、`packages/cli/src/templates/guru/overlay/hooks/guru_after_create.py`、`packages/cli/src/templates/guru/overlay/hooks/platform/block-unstarted-commit.sh`、`packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md` 以及对应 `guru-template/**` 镜像线索。
- Domain/terminology triggers: 触发。`gate-contract`、`gate-degradation`、`small_inline`、`micro_task`、`lite_task`、`full_chain`、`guru_chain`、`risk_level` 的边界会影响 lifecycle gate 和 commit gate，必须在任务内定义清楚。
- Current code vs user intent conflicts: 当前代码已有 `full|light` 和 `high|low|unknown`，但没有完整的 low/medium/high intake contract；`check-commit` 只认 in_progress + clean implementation review，不知道 micro/lite 合同；GitNexus/tool failure 没有 task-local degradation 事实账。
- Product decisions confirmed:
  - DEC-001: 三档风险路由：low 自动执行，medium 执行 lite，high 强制 full。
    - user_quote: "低风险自动执行，中风险执行 light, 高风险强制 full"；latest_update: "light 改为 lite"
  - DEC-002: gate contract / degradation 进入任务目录管理。
    - user_quote: "门禁的降级/绕行合同 能否和任务文件夹中管理？ 这样是否更好？"
  - DEC-003: 收到任务后先分析收集信息，再按难度/类别自动或让用户选择 contract / degradation。
    - user_quote: "可以做到收到任务后，分析收集任务信息和根据任务难度或类别自动或让用户选择不同的:gate-contract 或 gate-degradation 吗？"
  - DEC-005: 实现范围先改 Guru source/template，必要时最小 dogfood 本地文件。
    - user_quote: "是，先改 source/template，必要时最小 dogfood 本地文件。"
- Open product/scope/risk questions:
  - 无阻断问题：OQ-001 已解决；后续可进入 design.md / implement.md 规划补齐。

### Question Loop Log

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-001 | 2026-07-01 | 本任务实现范围是只改 Guru overlay/template 源，还是同时改当前 worktree 的本地 `.trellis/workflow.md` / `.codex/hooks` 做 dogfood？ | 先实现 source/template，即 `packages/cli/src/templates/guru/**` + `guru-template/**`；只在验证确实需要时最小 dogfood 本地文件。 | dogfood 本地文件见效快，但会增加本地 drift 和模板同步负担；只改模板更适合发布复用，但当前仓库不能马上享受完整行为。 | 是，先改 source/template，必要时最小 dogfood 本地文件。 | DEC-005 source/template 优先，必要时最小 dogfood | prd.md |

### Question Policy

question_policy: mixed

证据已回答：当前 `full|light` 基座、`guru_risk.py` 风险 helper、`guru_gate.py check-commit` 当前约束、`guru_after_create.py` 默认 full、当前 worktree 缺少 `.trellis/scripts/guru/` runtime，均由仓库文件回答。

用户已确认：low/medium/high 路由原则、task-local gate contract/degradation 方向、收到任务后先自动分析再按风险选择合同、source/template 优先实现范围，均来自当前对话用户原话。
