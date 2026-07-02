# Guru route-aware execution acceleration

## Goal

让上一轮 risk-based gate routing 在真实项目中“实际变快”，而不是只在 gate 层理论可用。重点修复当前仍会拖慢 `lite_task` / `full_chain` 的执行缺口：workflow 仍默认跑 adversarial requirements、合同创建靠手写、high-risk full 进入实现后才发现缺 slice packet、commit 尾部仍可能重新加载大上下文、terminal worker cleanup 缺少稳定机器输出。

## Background

上一任务 `07-01-risk-based-gate-contract-routing` 已提交 source 实现：`commit-plan/check-commit` 同源决策、`lite_task` bounded review policy、`adversarial_enabled=false` 只放宽 adversarial reviewer 要求、task-local `gate-contract.json` / `gate-degradations.jsonl` 校验。

复盘会话 `019f1dc3-6b3a-7750-bb1a-1e943a0d57ef` 后，当前剩余问题不是单一 gate 能力缺失，而是执行路径仍有高耗时环节：

- `lite_task` gate 允许省 adversarial requirements，但 workflow 详细步骤仍写“默认先运行 `guru_supervise.py --adversarial requirements`”，agent 可能照旧执行。
- `gate-contract.json` 没有一条标准生成命令，导致 contract 靠 agent 手写，容易缺失、字段错误或无法复用。
- `full_chain` high-risk slice 机制已存在，但缺 packet 往往到 implement worker 阶段才暴露，浪费一次 supervisor/worker 启动。
- `commit-plan` 当前只输出 stdout，不能稳定写入 mutable evidence，commit 尾部仍可能反复读取 workflow/spec/skill。
- 多 slice full 任务可以 `--slice` 执行，但缺少 `slice-plan` 这种只读计划摘要，agent 需要反复读 packet 和文档判断顺序。
- terminal `done|killed|error` worker 仍可能被主会话当作 live blocker，导致多轮 `ps/pgrep/kill`。
- source 新能力尚未安装到目标项目 `guru_ai_himora`，目标项目无法受益。

## Scope

In scope:

- 修正 Guru workflow / skill 中 requirements review 的 route-aware 默认行为。
- 增加 contract 生成/路由计划能力，至少覆盖 `init-contract` 或 `route-plan` 的最小可用命令。
- 在 implementation 前置阶段对 high-risk full slice packet 做 fail-fast 检查。
- 为 `commit-plan` 增加可持久化输出或明确的 mutable evidence 路径。
- 增加 `slice-plan` 或等价只读摘要，减少 full chain 多 slice 执行前的上下文读取。
- 增加 terminal worker status / cleanup 的机器可读输出，避免终态 worker 拖慢 commit 前收口。
- 将 source 最新 Guru overlay 安装到 `guru_ai_himora` 并做最小验证。

Out of scope:

- 降低 `full_chain` 的质量门禁。
- 让 high-risk 任务走 `lite_task`。
- 把 OCR 设为默认完成条件。
- 改写 Trellis task status 状态机。
- 自动串行执行所有 full slices 并跳过每片结果判断。
- 修复所有 provider/channel 稳定性问题；本任务只处理 terminal 状态识别和 cleanup 表达。

## Confirmed Decisions

- DEC-001: 继续使用 `low -> micro_task`、`medium -> lite_task`、`high -> full_chain` 的 route 规则；本任务本身命中 workflow/gate/runtime/template，因此必须是 `full_chain`。
- DEC-002: `lite_task` 加速只允许减少默认 adversarial / spec-update / commit-tail 成本，不允许绕过 current digest、double clean、blocked/medium+ evidence、human confirmation、staged scope 或 implementation review digest。
- DEC-003: `full_chain` 加速方式是 slice 化和前置 fail-fast，不削弱 full gate。
- DEC-004: 目标项目安装是本任务验收的一部分；只改 source/template 不能证明真实项目已受益。

## Behavior Specifications

### BHV-001 route-aware requirements review defaults

Priority: P0

Given task has a valid `gate-contract.json` with route `small_inline`, `micro_task`, or `lite_task`.
When workflow or status text recommends requirements review.
Then it must not default to `guru_supervise.py --adversarial requirements`; it should recommend the bounded route-aware path and only require adversarial requirements review for `full_chain` when `adversarial_enabled=true`.

### BHV-002 contract generation is tool-owned

Priority: P0

Given an agent classifies a task as `micro_task`, `lite_task`, or `full_chain`.
When it needs to write `gate-contract.json`.
Then it should use a stable Guru command such as `guru_gate.py init-contract` or `guru_gate.py route-plan --write`, not hand-author a JSON contract from memory.

### BHV-003 high-risk full slice packet missing fails before worker launch

Priority: P0

Given route is `full_chain` and risk evidence includes DB/schema/storage/workflow/gate/runtime/cross-layer or other high-risk signals.
When `check-start`, `check-implementation`, or `implement-check --dry-run` runs before implementation.
Then missing or ambiguous required slice packets should be reported before implement worker launch with a clear `PACKET_REQUIRED_BEFORE_IMPLEMENT` or equivalent blocking reason.

### BHV-004 commit-plan can persist mutable evidence

Priority: P1

Given a task is near commit-ready.
When `guru_gate.py commit-plan <task_dir> --write` or equivalent runs.
Then the plan should be written to a mutable evidence file such as `commit-plan.json` without changing requirements/detail digest, and stdout should still remain machine-readable.

### BHV-005 slice-plan summarizes full-chain slice execution

Priority: P1

Given a full-chain task has one or more `slice-packets/*.json`.
When `guru_gate.py slice-plan <task_dir>` or equivalent runs.
Then it should list slice ids, target paths, risk, deterministic checks, required provider, dirty-scope preflight status, and the next recommended `guru_supervise.py implement-check --slice ...` command.

### BHV-006 terminal worker cleanup is machine-readable

Priority: P1

Given channel workers are in terminal states `done|killed|error`.
When `guru_supervise.py status <task_dir> --json` or equivalent runs.
Then terminal workers should be counted separately from live workers, `blocking=false` when no live blockers exist, and a single cleanup command should be reported when cleanup is available.

### BHV-007 target project receives the new overlay

Priority: P0

Given source/template changes pass local validation.
When this task is implemented.
Then the built Guru CLI should apply the updated overlay into `/Users/devSC/Documents/JobProject/guru_ai_himora`, and target validation should prove the new `commit-plan`, route-aware workflow text, and contract commands are present without modifying unrelated UI scope.

## Requirements

- REQ-001: Update all Guru workflow templates (`client`, `go`, `h5`, `ios`) and `guru-template` mirrors so requirements review instructions are route-aware.
- REQ-002: Preserve strict full-chain behavior when route is missing, invalid, `risk=unknown`, or `adversarial_enabled=true` with `full_chain`.
- REQ-003: Add a contract generation command or route-plan writer that uses `guru_contract.default_contract()` / validation helpers instead of duplicated schema strings.
- REQ-004: Contract generation must reject high-risk downgrade to `lite_task` / `micro_task`.
- REQ-005: Add preflight for high-risk full tasks that need slice packets before implementation; missing/ambiguous packets must stop before worker launch.
- REQ-006: Add tests for route-aware requirements recommendation so `lite_task` no longer suggests `--adversarial requirements` by default.
- REQ-007: Add tests for `init-contract` / `route-plan` generation and invalid downgrade rejection.
- REQ-008: Add tests for `commit-plan --write` or equivalent persisted mutable evidence.
- REQ-009: Add tests for `slice-plan` on zero, one, and multiple packet tasks.
- REQ-010: Add tests for terminal worker status JSON if status/cleanup is implemented in this task.
- REQ-011: Mirror source/template pairs and keep dogfood `.trellis` edits minimal and intentional.
- REQ-012: Install to `guru_ai_himora` after source build and verify target overlay contains the new commands/text.

## Failure Paths

- FP-001: `lite_task` workflow still tells the agent to run `--adversarial requirements` by default; this is a P0 regression because the route policy is not reflected in execution.
- FP-002: Generated contract is malformed or uses unknown risk/route; command must fail without writing partial invalid JSON.
- FP-003: `full_chain` high-risk implementation starts a worker before required slice packet absence is reported; this keeps the current long-wait failure mode.
- FP-004: `commit-plan --write` updates `design.md` / `implement.md` or any digest-bearing planning contract; this invalidates current review evidence and must fail review.
- FP-005: `slice-plan` recommends a slice while current dirty scope would trigger `SCOPE_INVALID`; it must surface the scope problem instead.
- FP-006: Terminal worker status reports completed workers as live blockers; this keeps the stale-worker wait loop.
- FP-007: Target overlay install changes unrelated user work or UI scope in `guru_ai_himora`.

## Acceptance Criteria

- [ ] `lite_task` and `adversarial_enabled=false` workflow instructions no longer default to `guru_supervise.py --adversarial requirements`.
- [ ] `full_chain` instructions still require strict review when configured and valid.
- [ ] A stable command can create a valid `gate-contract.json` for `micro_task`, `lite_task`, and `full_chain`.
- [ ] The command rejects high-risk downgrade attempts.
- [ ] High-risk full tasks with required slice evidence missing are blocked before implement worker launch.
- [ ] `commit-plan` can be persisted as mutable evidence without changing detail digest.
- [ ] `slice-plan` gives a compact execution plan for full-chain packet tasks.
- [ ] Terminal worker status distinguishes live and terminal workers in machine-readable form.
- [ ] Source/template mirror checks pass.
- [ ] Guru overlay verify tests pass.
- [ ] Updated overlay is applied to `guru_ai_himora` and target verification confirms new behavior is present.

## Open Questions

- 无阻断问题：OQ-001 已由当前用户确认，范围为“生成 Trellis 任务来实现上述优化”。本任务先以 full-chain tooling task 记录 route-aware execution acceleration 的需求/设计/实施计划；后续进入实现前仍需按 Guru requirements/detail Gate 做正式确认。

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm` read on 2026-07-02.
- Repository evidence inspected:
  - `.trellis/spec/cli/backend/guru-overlay-gates.md`
  - `packages/cli/src/templates/guru/workflows/guru-client.md`
  - `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_contract.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
  - `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
  - previous task `.trellis/tasks/07-01-risk-based-gate-contract-routing`
- Domain/terminology triggers: triggered. `lite_task`, `full_chain`, `gate-contract`, `slice packet`, `commit-plan`, and `terminal worker` are execution-policy terms; this PRD keeps them tied to existing Guru contracts rather than inventing new Trellis status.
- Current code vs user intent conflicts:
  - Gate policy now allows lite to skip adversarial requirements, but workflow text still defaults to `--adversarial requirements`.
  - Contract validation exists, but contract creation is not yet a stable user-facing command.
  - Slice packet runtime exists, but preflight is late relative to the user-visible long-wait problem.
- Product decisions confirmed:
  - DEC-001: 生成一个新的 Trellis 任务来实现 route-aware execution acceleration 优化。
    - user_quote: "好，生成一个 trellis 任务来实现上面优化"
  - DEC-002: 本任务按 high/full_chain 处理，因为它触达 workflow/gate/runtime/template 与目标 overlay 安装。
    - confirmed_ref: prd.md Scope + gate-contract.json route=full_chain/risk=high；仓库证据显示相关修改会触达 `guru_gate.py`、`guru_supervise.py`、workflow templates 和 target overlay。
  - DEC-003: 优化内容以当前讨论收敛的 P0/P1 清单为准：route-aware adversarial 默认、contract generation、full slice preflight、commit-plan persistence、slice-plan、terminal worker status、target install。
    - confirmed_ref: 当前对话中用户先问“当前实现还有要调整的吗？”，随后确认“好，生成一个 trellis 任务来实现上面优化”。
- Open product/scope/risk questions:
  - 无阻断问题：OQ-001 已解决。P2 cleanup 自动化深度可在 detail review 时调整，不阻塞当前 planning snapshot。

### Question Loop Log

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-001 | 2026-07-02 | 是否把上述 route-aware execution acceleration 优化生成一个正式 Trellis 任务？ | 是，创建 P1 full-chain tooling 任务，先落 PRD/design/implement，不直接进入代码实现。 | 立即建任务会产生新的 planning artifacts；不建任务则这些优化仍停留在聊天结论里，后续容易丢失执行边界。 | 好，生成一个 trellis 任务来实现上面优化 | DEC-001 / DEC-002 / DEC-003 | prd.md, design.md, implement.md, gate-contract.json |

### Question Policy

question_policy: mixed

证据已回答：当前 source 已有 `commit-plan/check-commit`、`guru_contract.py`、route-aware review policy、slice packet runtime 与 workflow 残留的 `--adversarial requirements` 默认建议；这些均由仓库文件和上一任务产物回答。

用户已确认：把上述优化正式生成 Trellis 任务实现，且本任务应承接当前讨论收敛的优化清单。
