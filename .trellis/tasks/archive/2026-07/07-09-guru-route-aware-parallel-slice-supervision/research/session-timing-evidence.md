# 会话耗时证据

## 来源

- Codex 会话 `019f40db-94d0-7ed3-a551-ff820095c688`
  - Session path: `/Users/devSC/.codex/sessions/2026/07/08/rollout-2026-07-08T16-32-40-019f40db-94d0-7ed3-a551-ff820095c688.jsonl`
  - CWD: `/Users/devSC/Documents/JobProject/guru_ai_himora`
- Codex 会话 `019f4298-f7ed-7ba1-872a-d08d68887fa4`
  - Session path: `/Users/devSC/.codex/sessions/2026/07/09/rollout-2026-07-09T00-39-09-019f4298-f7ed-7ba1-872a-d08d68887fa4.jsonl`
  - CWD: `/Users/devSC/Documents/JobProject/guru_ai_himora`

## 会话 019f40db 瓶颈时间线

这是 generated-media like attempt-scope 的 full-chain 案例。

| UTC 时间 | 事件 | 观察 |
| --- | --- | --- |
| 2026-07-08 08:34 | 用户报告根因任务 | 根因分析开始。 |
| 2026-07-08 08:52 | 用户同意继续 | Agent 将修复归类为 high/full-chain。 |
| 2026-07-08 08:53 | `task.py create` | 新任务 `.trellis/tasks/07-08-07-08-fix-generated-media-like-attempt-scope` 创建。 |
| 2026-07-08 09:42-10:17 | requirements review/status 循环 | requirements review 和 status 检查在确认路径推进前消耗多个回合。 |
| 2026-07-08 10:36-10:49 | detail review worker 运行后被中断 | Worker 漂移到过宽范围；主会话中断并收窄提示词。 |
| 2026-07-08 11:03 | `check-start`, `task.py start` | 任务最终进入 implementation-ready。 |
| 2026-07-08 11:03-11:05 | `slice-plan` / packet 检查 | 发现切片包，但 plan 仍然只是诊断信息。 |
| 2026-07-08 11:06 | 第一个 `implement-check --slice` | 第一个切片实现在任务创建后约 2 小时 13 分钟才启动。 |
| 2026-07-08 11:06-16:16 | 切片循环 | 九个切片包基本串行推进。到 16:16 时全部 clean records 已存在。 |
| 2026-07-08 16:39-16:42 | commit-plan 并停止 | 实现完成，但 commit tail 仍报告 staged-scope blockers。 |

关键观察：

- 第一个实现切片直到较长的 planning/review 链结束后才启动。
- 实现开始后，主会话仍然一个接一个运行切片包。
- 多个等待属于只读 review/check 等待，本可通过状态轮询或扇出并行化。
- 后续切片命中 `SCOPE_INVALID`，因为已完成切片留下的脏路径没有作为下一包的 unrelated state 表达。
- 当前工具已经拥有切片包和 review records，但缺少能分组、启动并聚合它们的编排层。

## 会话 019f4298 瓶颈时间线

这是 generated-media reopen flicker / selected-index 修复案例。

| UTC 时间 | 事件 | 观察 |
| --- | --- | --- |
| 2026-07-08 16:40 | 用户报告 bug | 根因追踪开始。 |
| 2026-07-08 16:51 | 用户说“好，修复” | 实现意图确认。 |
| 2026-07-08 16:54 | Gate/contract 修正 | 现有任务是 lite 状态，但存在陈旧 full-chain/high contract，导致 packet-required 误路由。 |
| 2026-07-08 17:00 | implementation gate 通过 | 可以继续实现。 |
| 2026-07-09 00:10-00:16 | commit gate review 恢复 | 提交 gate 需要 detail review 和 implementation review；随后 review worker 因规划范围与实际 UI 扩张不一致而阻塞。 |
| 2026-07-09 00:23-00:24 | overview/detail review records 修复 | 主会话在 commit tail 较晚刷新 planning review records。 |
| 2026-07-09 00:33 | `slice-plan` 出现在 commit 恢复中 | 使用单个 packet 解锁 staged implementation review。 |
| 2026-07-09 00:41 | commit 成功 | 在较晚的 review 与 gate 修复后，commit 最终落地。 |

关键观察：

- 该任务并非 high/full-chain，但陈旧 route contract 数据触发了类似 full-chain 的 packet 行为，直到被修复。
- 提交恢复依赖最新 implementation review 状态，而不是紧凑的 multi-review coverage model。
- 提交尾段在实现已完成后重新加载宽泛 gate 代码，并修复 overview/detail 产物。
- 紧凑的 commit-plan 加 staged review 命令方向正确，但必须避免不必要地重新打开 planning，并且必须精确处理 route 与 review coverage。

## 当前仓库证据

- `guru_gate.py slice-plan` 是只读命令，存在多个 packet 时会输出 `PACKET_AMBIGUOUS_WITHOUT_SLICE`。
- `guru_supervise.py implement-check` 只解析单个 `--slice`；只有在恰好存在一个 packet 时才自动选择一个，遇到多个 packet 会 hard-stop 为 ambiguous。
- `guru_supervise.py implementation-review` 是 check-only，可针对 slice 或 staged scope，不会启动 implement worker。
- `guru_gate.py commit-plan` / `check-commit` 调用 `_latest_jsonl_record(...)` 读取 `review-records/implementation-reviews.jsonl`；最新 clean row 无法证明多个早期切片的覆盖。
- `guru_supervise.py status --json` 已报告 `live_workers`、`terminal_workers`、`cleanup_available` 和 `cleanup_command`；它应成为切片调度和 commit-tail 恢复的输入。
- `.trellis/config.yaml` 设置 `codex.dispatch_mode: sub-agent`，说明当前 Codex 默认应使用 Trellis sub-agent；`channel.worker_guard.max_live_workers: 6` 仅说明 channel 后端被选择时也有有界并发配置。

## 设计含义

1. `slice-plan` 应保持只读，但升级为稳定的调度 payload。
2. 应由独立 supervision 命令按 dispatch mode 运行或输出 plan 中的分组，并通过 `--dry-run` 显示精确 worker 命令或 sub-agent brief。
3. Writer 并行必须要求隔离。同 checkout 并发写入 worker 默认不安全，除非调度器能证明目标互不重叠、脏变更范围干净或隔离、资源锁安全且依赖就绪。
4. 只读扇出风险较低，应提前支持：确定性检查、`implementation-review --slice`、dispatch worker status polling 和 cleanup checks；sub-agent 后端不得伪造 channel 状态。
5. 提交覆盖必须按目标路径和切片 id 聚合。“最新 clean review”不是多切片 staged scope 的有效证明。
