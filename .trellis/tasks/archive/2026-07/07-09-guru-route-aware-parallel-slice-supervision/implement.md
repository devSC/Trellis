# Guru 路由感知并行切片监督实现计划

## 范围

为 Guru 实现路由感知的 full-chain 切片调度与多切片 review 覆盖。变更范围聚焦在 Guru gate/supervision 脚本、模板、workflow/spec 文本和测试。

除非用户在 gate 通过后明确要求，否则不要 commit、push、archive 或运行 finish-work。

## 实现前要求

- 按 `AGENTS.md` 要求，在编辑任何 function/class/method 前，先对目标 symbol 运行 GitNexus impact analysis。
- 编辑前重新读取 live diff，因为当前 checkout 已经包含无关脏变更。
- 在 `task.py start` 前确认 requirements 与 detail gate。
- 保留现有 `slice-plan` 只读行为。
- 不削弱 full-chain gate，也不把 full-chain 切片包开销加入 micro/lite 路由。

## 计划 / Implementation Slices

| Slice | UNIT | 目标 | 主要目标文件 |
| --- | --- | --- | --- |
| SL-01 | UNIT-slice-plan-scheduler | 增加 additive 的 `slice-plan` 调度元数据和 parallel-group dry-run payload。 | `.trellis/scripts/guru/guru_gate.py`, `guru-template/overlay/verify/guru_gate.py`, `packages/cli/src/templates/guru/overlay/verify/guru_gate.py` |
| SL-02 | UNIT-parallel-slice-dispatcher | 为安全切片分组增加 dispatch-mode aware 的有界 dispatcher dry-run 与执行循环。 | `.trellis/scripts/guru/guru_supervise.py`, `.codex/agents/*`, `.trellis/agents/*`, template copies |
| SL-03 | UNIT-worker-isolation-policy | 增加路径互斥、脏变更隔离、资源安全检查与串行回退原因。 | `guru_supervise.py`, `guru_review_record.py`, template copies |
| SL-04 | UNIT-review-coverage-aggregation | 用 review-set 覆盖替代 latest-row-only commit coverage。 | `guru_gate.py`, `guru_review_record.py`, template copies |
| SL-05 | UNIT-route-and-platform-parity | 在行为变化处更新 Guru workflow/template 文档和 agent prompt 一致性。 | `.trellis/workflow.md`, `guru-template/workflows/*`, `packages/cli/src/templates/guru/workflows/*`, `.trellis/agents/*` as needed |
| SL-06 | UNIT-tests | 为 plan schema、dispatch safety、route parity、status 和 commit coverage 增加 overlay verify 与 TypeScript 覆盖。 | `guru-template/overlay/verify/tests/run_tests.sh`, CLI template tests, package tests |

## 执行 / Ordered Steps

1. 建立基线。
   - 运行 `git status --short --branch`。
   - 运行 `python3 .trellis/scripts/guru/guru_gate.py status .trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision`。
   - 运行 `python3 .trellis/scripts/guru/guru_gate.py slice-plan .trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision`。

2. SL-01 `UNIT-slice-plan-scheduler`。
   - 编辑前对目标 symbol 做 impact check。
   - 增加带 schema version 的可选字段：`parallel_groups`、`parallel_safe`、`parallel_mode`、`parallel_blockers`、`depends_on`，并拆分推荐命令。
   - 保持 stdout JSON 且不写文件。
   - 为 0/1/multiple/overlap packet 增加 fixture。

3. SL-02 `UNIT-parallel-slice-dispatcher`。
   - 对 supervisor run/build-plan 相关 symbol 做 impact check。
   - 增加 `implement-slices` 或等价命令，支持 `--dry-run`、`--parallel`、`--group`、`--backend auto|sub-agent|channel` 和显式 task dir。
   - 启动时重新读取 `slice-plan`。
   - 默认读取 `.trellis/config.yaml codex.dispatch_mode`；当前项目为 `sub-agent`，因此默认输出/启动 Trellis sub-agent 派发 brief。
   - 仅当 `codex.dispatch_mode=channel` 或 CLI 显式 `--backend channel` 时使用官方 channel plan builder；不得使用临时后台 shell job。
   - 如有必要，只记录可变 dispatch evidence。

4. SL-03 `UNIT-worker-isolation-policy`。
   - 增加 spawn 前 writer 安全检查。
   - 将目标重叠、非法脏变更范围、未解决依赖和资源锁冲突视为 serial/blocking。
   - 让 status JSON 成为 live/terminal/cleanup 行为的调度输入。

5. SL-04 `UNIT-review-coverage-aggregation`。
   - 对 full/lite implementation commit，将基于 `_latest_jsonl_record` 的 commit 授权替换为 review-set coverage。
   - 仅在某条路由确实需要最新单目标恢复时保留 latest-row helper。
   - 输出精确的缺失 review 命令；如果能识别 packet owner，优先推荐 `implementation-review --slice <id>`。

6. SL-05 `UNIT-route-and-platform-parity`。
   - 只在行为变化处更新 workflow/template 文本。
   - 保留 `Active task: <path>` 与 nested-dispatch guard。
   - 明确 micro/lite 路由文档：不强制加入 full-chain packet 开销。
   - 检查 source/template 镜像文件对。

7. SL-06 `UNIT-tests`。
   - 扩展 Guru overlay verify 测试。
   - 当 template/workflow 文本或 sync 行为变化时，补充 TypeScript 测试。
   - 如果没有 shell fixture，则为 review coverage aggregation 增加聚焦的 Python 检查。

## 证据 / Validation Commands

先运行聚焦验证：

```bash
python3 -m py_compile \
  .trellis/scripts/guru/guru_gate.py \
  .trellis/scripts/guru/guru_supervise.py \
  .trellis/scripts/guru/guru_review_record.py \
  .trellis/scripts/guru/guru_risk.py
```

```bash
python3 -m py_compile \
  guru-template/overlay/verify/guru_gate.py \
  guru-template/overlay/verify/guru_supervise.py \
  guru-template/overlay/verify/guru_review_record.py \
  guru-template/overlay/verify/guru_risk.py
```

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
pnpm --filter @devsc/trellis run sync:guru:check
pnpm --filter @devsc/trellis run lint
pnpm --filter @devsc/trellis run typecheck
git diff --check
```

如果触及 TypeScript template 测试，还要运行负责 Guru bundled/template 行为的窄范围 Vitest shard。

提交前运行：

```bash
python3 .trellis/scripts/guru/guru_gate.py commit-plan .trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision
python3 .trellis/scripts/guru/guru_gate.py check-commit .trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision
node .gitnexus/run.cjs detect_changes --scope all --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree --limit 200
```

## 阻塞与偏差 / 风险与回滚

- 如果同 checkout 并行 writer 被证明不安全，先保持 writer 串行，只交付只读扇出与 review coverage aggregation。
- 如果 review-set aggregation 范围过宽，则保守回退为要求最终 staged 范围执行 `implementation-review --staged`。
- 如果 sub-agent 后端无法由 CLI 直接自动启动，则保留 `implement-slices --dry-run` 输出精确 Trellis sub-agent prompts，由主会话通过平台 Agent 工具并行派发。
- 如果 channel worker 并发不稳定，则 channel 后端保留 `implement-slices --dry-run` 加串行执行，并暴露精确下一步命令。
- 如果 template sync 出现漂移，先停止并重新同步 source/template copies，再继续。

## 完成标准

- PRD/design/implement 保持当前且可被 gate 读取。
- 记录 review evidence 后，requirements、overview 和 detail gates 均通过。
- 只有在用户确认 gate 后才执行 `task.py start`。
- Parallel dispatch 不能运行不安全的 writer 切片。
- 当前项目 `codex.dispatch_mode: sub-agent` 时，dispatcher 不默认创建 channel。
- 多切片 staged scope 不再只信任最新 review row 作为 commit coverage。
- 最终 diff 不包含无关脏 worktree 变更。
