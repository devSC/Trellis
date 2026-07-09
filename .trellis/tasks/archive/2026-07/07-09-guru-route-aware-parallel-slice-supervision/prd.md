# Guru 路由感知并行切片监督加固

## 目标

通过把切片包转化为可执行、路由感知、dispatch-mode aware 的监督计划，缩短 Guru full-chain 任务的整体周转时间。高风险 full-chain 任务在安全时应能按当前 dispatch mode 并行启动并完成相互独立的切片，同时保留现有的 fail-closed gate：规划确认、脏变更范围、实现 review、提交覆盖和 worker 生命周期清理都不能被削弱。

本任务来自最近两个 Himora 会话暴露出的同类系统瓶颈：

- 会话 `019f40db-94d0-7ed3-a551-ff820095c688`：用户批准高风险的 generated-media like 修复后，从创建任务到第一个切片开始实现大约耗时 2 小时 13 分钟；随后从第一个切片启动到全部切片 clean 又超过 5 小时。当前流程基本按一个切片接一个切片推进。
- 会话 `019f4298-f7ed-7ba1-872a-d08d68887fa4`：一个范围较小的 lite 修复仍然反复卡在 gate、上下文和 commit-tail 上。commit gate 与 review 恢复路径加载了过多上下文，较晚才修复规划产物，并且依赖单条最新 implementation review 记录。

目标不是放松 Guru，而是把昂贵步骤并发化、显式化、边界化。

## 背景

当前仓库事实：

- `guru_gate.py slice-plan <task_dir>` 是只读命令。它会输出切片包、脏变更范围、阻塞原因和每个切片推荐的 `implement-check` 命令，但不会创建、调度、预留或执行工作。
- `guru_supervise.py implement-check <task_dir> --slice <unit_id>` 支持一个已解析的单切片。存在多个包且未显式传入 `--slice` 时，它会以 `PACKET_AMBIGUOUS` 停止。
- 高风险且选中 `full_chain` 的任务在实现前正确要求切片包，但目前没有一等的“运行所有独立切片”编排能力。
- `commit-plan` / `check-commit` 当前读取 `review-records/implementation-reviews.jsonl` 中的最新一行；这不足以证明多切片实现，因为最新 clean 记录只能证明最后一次 review 的目标。
- `guru_supervise.py status --json` 已经区分 `live_workers` 和 `terminal_workers`，但任务执行与 commit-tail 流程仍然需要一个紧凑界面说明“什么在阻塞、什么可清理、什么可继续”。
- `.trellis/config.yaml` 当前设置 `codex.dispatch_mode: sub-agent`，因此 Codex implement/check 的默认执行面是 Trellis sub-agent。`channel.worker_guard.max_live_workers: 6` 仍是 channel 后端被显式选择时的有界并发预算。
- Trellis 平台规则要求平台 sub-agent 带有 `Active task: <path>` 上下文；channel runtime worker 使用 `.trellis/agents/{implement,check}.md` 与 channel event log。直接平台 sub-agent 调度与官方 channel worker 是不同后端，必须由 dispatch mode 显式选择，不能被隐式混用。

## 需求

### BHV-001 [REQ-UC-001] 切片计划暴露可执行并行分组

优先级：P0

Given 一个高风险 `full_chain` 任务拥有多个切片包。
When 运行 `guru_gate.py slice-plan <task_dir>`。
Then 它必须保持只读，同时输出确定性的执行图：切片 id、依赖关系、目标路径集合、脏变更范围状态、确定性检查、预估 writer/read-only 模式，以及 `parallel_group` 归属。

### BHV-002 [REQ-UC-001] Full-chain 调度器可以并发运行独立切片

优先级：P0

Given `slice-plan` 报告两个或更多切片属于同一个并行安全分组。
When 操作者运行新的 Guru supervision 入口。
Then Guru 应按当前 dispatch mode 为这些切片启动或输出有界并发 worker 计划：当前项目默认使用 Trellis sub-agent；仅当 `codex.dispatch_mode=channel` 或用户显式选择 durable channel runtime 时才使用 `trellis channel`。它不得强迫主会话逐个串行运行 `implement-check`。

### BHV-003 [REQ-UC-002] 并行 writer 启动前必须隔离

优先级：P0

Given 切片 worker 可能编辑文件。
When Guru 并行化实现工作。
Then 它只能并行化 `target_paths` 互不重叠、且脏状态干净或已显式隔离的 writer 切片。如果无法证明 writer 隔离安全，调度器必须回退到串行执行并说明原因。

### BHV-004 [REQ-UC-002] 只读 review 与确定性检查可以提前扇出

优先级：P1

Given 实现已经修改目标，或 staged/index 目标需要 review。
When 工作是只读的，或绑定到隔离的目标路径。
Then Guru 可以并发运行确定性检查、`implementation-review --slice` 和状态轮询，且不得启动 implement worker。

### BHV-005 [REQ-UC-003] 提交覆盖使用切片 review 集，而不是只看最新 review

优先级：P0

Given 一个 full-chain 任务已经实现多个切片。
When `commit-plan` 或 `check-commit` 评估 staged 范围。
Then 它必须证明每个 staged 实现路径都被其所属切片的当前 clean review 记录覆盖，或被显式 staged-scope implementation review 覆盖。单条最新 review 记录不得意外授权无关的早期切片。

### BHV-006 [REQ-UC-004] Dispatch worker 状态成为调度输入

优先级：P1

Given dispatch worker 可能处于 live、terminal、stuck 或 cleanup-eligible 状态。
When 调度器或 commit-tail 流程检查进度。
Then 状态接口必须按后端给出足够信息：sub-agent 后端报告已派发、待回收、待人工接续的子任务状态，channel 后端继续通过 `guru_supervise.py status --json` 报告 live/terminal/cleanup 信息，从而决定等待、清理、中断或启动下一个并行分组。

### BHV-007 [REQ-UC-005] Micro 与 lite 保持路由感知的有限行为

优先级：P0

Given 任务路由是 `micro_task`、`lite_task`、`small_inline` 或 legacy strict full-chain。
When Guru gate 与 supervisor 运行。
Then 新的并行切片要求只在合同要求切片包的地方生效，通常是高风险且选中 `full_chain` 的任务。Micro/lite 不得继承 full-chain 的规划开销，也不得被强制创建切片包。

### BHV-008 [REQ-UC-006] Dispatch mode 与平台调度保持一致

优先级：P1

Given Codex 和其他 pull-based 平台需要显式任务上下文。
When Guru 通过平台 sub-agent、channel worker 或 inline fallback 调度工作。
Then 调度必须先读取 `codex.dispatch_mode` / 平台能力并选择后端；每个 worker prompt 必须携带 active task 上下文，必须知道自己是否已经是被调度的 worker，并且不得再嵌套 spawn implement/check worker。

### BHV-009 [REQ-UC-007] Commit tail 在 plan 可用后保持紧凑

优先级：P1

Given 实现证据和 review 证据已经是当前状态。
When `commit-plan` 已可用。
Then 主会话不应重新加载完整 skill、完整 memory 或宽泛 spec，除非 plan 报告缺失依赖。最终步骤只应报告 blocker、必需命令、允许 stage 的路径和下一步不可逆动作。

## 非目标

- 不削弱 requirements/detail confirmation、current digest、dirty scope 或 implementation review gate。
- 不让 `slice-plan` 修改任务产物；它仍然是只读诊断与调度 payload。
- 当目标重叠、脏变更泄漏、依赖顺序或资源锁使结果不安全时，不在同一 checkout 中运行多个写入 worker。
- 不要求 micro/lite 任务创建切片包。
- 不用临时 shell 后台任务替代配置选中的 dispatch 后端；channel 语义只在 channel 后端被选择时适用。

## 失败路径

- 无效或缺失的切片包：报告 `PACKET_MISSING` / `PACKET_INVALID`，并且不 spawn worker。
- 存在多个包但没有选中分组或安全分组：报告 `PACKET_AMBIGUOUS_WITHOUT_SLICE` 或串行回退原因。
- 目标路径重叠：阻止并行 writer 模式，并输出冲突的切片 id 与路径。
- 存在范围外脏文件：阻止 writer 启动，除非包显式声明这些路径无关且依赖状态干净。
- 资源锁冲突，例如宽泛 Flutter/Dart 启动锁：串行化受影响切片，或只运行只读检查。
- Worker 预算耗尽：按后端报告 live worker 或已派发 sub-agent 数量，并给出 cleanup/wait/继续派发命令。
- Terminal 或 stale worker：暴露清理候选，不把 terminal worker 视为 live blocker；sub-agent 后端无法自动清理时必须给出主会话下一步。
- 提交时缺少多切片 review 覆盖：阻止 commit，并推荐精确的 `implementation-review --slice` 或 `--staged` 命令。
- Micro/lite 路由受到 full-chain 切片包压力：将其视为 route-policy 回归并阻止变更。

## 验收标准

- [ ] `slice-plan` JSON 包含 `parallel_groups`、每切片依赖/blocker 元数据和稳定的推荐命令，同时保持只读。
- [ ] 新的 dispatcher 命令，例如 `guru_supervise.py implement-slices <task_dir> [--parallel N] [--group <id>] [--backend auto|sub-agent|channel] [--dry-run]`，能在有界并发限制下为多个独立切片包生成或执行后端匹配的调度计划。
- [ ] 调度器拒绝不安全的并行 writer 分组，并给出可执行原因：目标路径重叠、范围外脏文件、缺失包、无效包、依赖未 clean 或资源锁冲突。
- [ ] 调度器支持针对 `implementation-review --slice` / 确定性检查任务的只读扇出，且不启动 implement worker。
- [ ] 多切片 `commit-plan` 能证明所有 staged 实现路径的覆盖，而不是只信任最新 JSONL review 记录。
- [ ] `check-commit` 与 `commit-plan` 在多切片 pass/block fixture 上判断一致。
- [ ] Worker status / dispatch report 提供足够数据，让调度器报告 live、terminal、cleanup-available、blocked 和 next-runnable 切片；sub-agent 后端不伪造 channel 状态。
- [ ] 平台调度文档与 prompt 保持 `Active task: <path>` 规则，并让 channel worker 与平台 sub-agent 的 nested-dispatch guard 一致。
- [ ] Micro/lite fixture 测试证明本变更没有引入 full-chain 切片包要求。
- [ ] 聚焦验证覆盖 Guru overlay 测试、Python compile、template/source sync 和相关 TypeScript test shard。

## 未决问题

当前没有阻塞规划的问题。推荐实现方向保持保守：只有在隔离可证明时并行化 writer 切片，否则先使用只读扇出加串行 writer 执行。

## Question Loop Log

question_policy: mixed

- decision: 为路由感知并行切片监督创建一个高风险 full-chain Guru 任务。
  user_quote: "同意，新建 full_chain 任务"
  result: 任务 `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision` 已处于 planning 状态，且 `gate-contract.json.route=full_chain`。
- decision: 将不安全的同 checkout 并行写入排除在默认快速路径之外。
  evidence: Trellis channel worker 共享项目 checkout；当前 `implement-check` review digest 和确定性检查都假设目标状态隔离。Sub-agent 后端是否共享 checkout 或 fork workspace 由平台能力决定，仍需要显式隔离合同。
  result: 默认设计要求在并行 writer 启动前，先按 dispatch backend 证明目标路径互不重叠，并通过隔离/资源检查。
- decision: 将当前任务文档从“channel 优先”修正为“dispatch-mode aware”。
  user_quote: "当前任务文档从“channel 优先”修正为“dispatch-mode aware"
  result: 当前项目 `codex.dispatch_mode: sub-agent` 成为默认后端；channel 仅在配置为 `channel` 或用户显式选择 durable channel runtime 时使用。

## Brainstorm Evidence

### Question Policy

question_policy: mixed

- evidence answered: 仓库检查已经确认当前 `slice-plan`、`implement-check`、`implementation-review`、`commit-plan`、worker status、route policy、`codex.dispatch_mode: sub-agent` 和平台调度行为。
- user confirmed: 当前用户回合已明确同意创建 full-chain 任务，并明确要求把任务文档从“channel 优先”修正为“dispatch-mode aware”。

- Skill loaded: 已加载 trellis-brainstorm、trellis-meta。
- Repository evidence inspected: 已检查 `.trellis/workflow.md`、`.trellis/config.yaml`、`.trellis/agents/{implement,check}.md`、`.trellis/spec/cli/backend/guru-overlay-gates.md`、`.trellis/spec/cli/backend/commands-channel.md`、`.trellis/spec/cli/backend/platform-integration.md`、`.trellis/scripts/guru/guru_gate.py`、`.trellis/scripts/guru/guru_supervise.py`、`.trellis/scripts/guru/guru_review_record.py`、`guru-template/workflows/*`、`packages/cli/src/templates/guru/workflows/*`，以及历史任务 `.trellis/tasks/07-08-high-risk-slice-review-provider`。
- Session evidence inspected: 已检查 `019f40db-94d0-7ed3-a551-ff820095c688`、`019f4298-f7ed-7ba1-872a-d08d68887fa4`；摘要见 `research/session-timing-evidence.md`。
- Domain/terminology triggers:
  - `full_chain route` 与 legacy `task.json.guru_chain=full` 相关但不完全相同。本任务针对 route/gate contract 与切片 runtime 行为。
  - `subagent` 可能指直接平台 sub-agent，也可能被误用来泛指官方 `trellis channel` worker。本任务采用 `dispatch mode` 作为规范术语：当前项目默认 direct Trellis sub-agent；channel 是可选 durable worker 后端。
  - “并行实现”只对已隔离的 writer 切片安全；只读 review 扇出成本更低也更安全。
- Current code vs user intent conflicts:
  - 用户意图：通过在可能时并行运行切片工作，缩短 full-chain 总耗时。
  - 当前代码：`slice-plan` 是只读诊断，只输出每切片串行命令；`implement-check` 只解析一个切片；`commit-plan` 消费最新 implementation review 记录。
- Product decisions confirmed: 使用 full-chain 任务承载本变更。
  - user_quote: "同意，新建 full_chain 任务"
  - 保留 route-aware 行为，确保 micro/lite 不继承 full-chain 开销。
    user_quote: "这样调整的话，多所有任务类型（micro, lite, full 等）都会有影响吗？" 随后同意继续推进限定范围的 full-chain 任务。
  - 将调度后端从 channel-first 修正为 dispatch-mode aware。
    user_quote: "当前任务文档从“channel 优先”修正为“dispatch-mode aware"
    result: 当前项目默认 `sub-agent`；channel 仅作为配置或显式选择的后端。
- Open product/scope/risk questions:
  - 无阻塞项；实现前仍需完成 requirements/detail confirmation。

## 备注

- `prd.md` 只聚焦需求、约束和验收标准。
- 本 planning 任务不启动实现。Full-chain gate 仍要求 requirements confirmation、overview/detail clean reviews、detail confirmation，然后才能执行 `task.py start`。
