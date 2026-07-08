# Finish / Commit Route-Aware Local Markdown Adjustment Plan

## 1. 背景与结论

本方案补齐 `risk-based-gate-contract-routing` 任务在 Finish / Commit 阶段暴露出的流程缺口。

问题会话：`019f1e18-e3b7-77b1-ac30-06332e314250`。

该会话中，产品实现和质量验证在提交前已经基本收口，但从 `2026-07-02 11:18 CST` 到 `2026-07-02 11:29 CST` 又消耗了约 11 分钟和约 297 万 total token。新增消耗主要不是业务代码，而是：

- Phase 3.3 spec 回写被当作 commit 前必做项。
- mutable execution / extraction evidence 写入 `implement.md`，导致 detail digest 再次失配。
- terminal done worker 仍显示活跃，需要主会话多轮 status / pgrep / kill 清理。
- commit scope / staged-scope 规则需要 agent 临场读取 `guru_gate.py` 源码推断。
- 会话上下文已膨胀，每一次小检查都会产生 12 万到 14 万级 input token。

结论：现有 low / medium / high risk routing 解决了入口和 commit gate 的一部分问题，但 Finish / Commit 也必须 route-aware；否则低/中风险任务即使前面变轻，最后仍会被 full-chain 收口拖慢。

## 2. 本次 Markdown 调整目标

本文件先定义完整本地 Markdown 调整方案，不直接修改 Python runtime。

目标是把以下规则写入任务和本地规范，后续再按该方案实现 source/template：

1. Finish 阶段必须按 route 区分，不再所有任务无差别执行 full Phase 3.3。
2. Spec update、journal、implementation evidence、worker cleanup 不能扰动已确认的 planning / detail digest。
3. Commit 前必须有机器可读的 commit plan，agent 不再临场读源码推断 staged scope。
4. `adversarial_enabled=false` 只移除 adversarial reviewer 要求，不绕过 current digest、double clean、medium+ finding、human confirmation 或 commit staged-scope gate。
5. OCR 不作为默认 review 或 commit 前完成条件；本任务审查继续使用 non-OCR evidence。
6. route 术语统一为 `lite` / `lite_task`，只保留 `task.json.guru_chain=light` 作为兼容字段。

## 3. 调整范围

### 3.1 任务目录 Markdown

需要调整的本任务产物：

- `.trellis/tasks/07-01-risk-based-gate-contract-routing/prd.md`
- `.trellis/tasks/07-01-risk-based-gate-contract-routing/design.md`
- `.trellis/tasks/07-01-risk-based-gate-contract-routing/implement.md`
- 本文件：`.trellis/tasks/07-01-risk-based-gate-contract-routing/finish-commit-route-aware-md-plan.md`

### 3.2 本地 spec Markdown

需要调整的本地规范：

- `.trellis/spec/cli/backend/guru-overlay-gates.md`
- `.trellis/spec/cli/backend/index.md`，仅在新增小节或 scenario 后更新摘要。

### 3.3 Source / Template Markdown

后续实现时需要同步的模板 Markdown：

- `packages/cli/src/templates/guru/workflows/guru-client.md`
- `packages/cli/src/templates/guru/workflows/guru-go.md`
- `packages/cli/src/templates/guru/workflows/guru-h5.md`
- `packages/cli/src/templates/guru/workflows/guru-ios.md`
- `guru-template/workflows/guru-client-workflow.md`
- `guru-template/workflows/guru-go-workflow.md`
- `guru-template/workflows/guru-h5-workflow.md`
- `guru-template/workflows/guru-ios-workflow.md`
- `packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md`
- `guru-template/overlay/agents-skills/client-small-iteration-dev/SKILL.md`

### 3.4 暂不调整

本 Markdown 方案阶段不调整：

- Python runtime。
- hook shell。
- current local `.trellis/scripts/guru/*` dogfood runtime。
- marketplace submodule。
- global npm install 或 `node_modules`。

## 4. 新增需求定义

### REQ-FIN-001 Route-Aware Finish Policy

Finish 阶段必须读取 route / gate contract，并按 `small_inline`、`micro_task`、`lite_task`、`full_chain` 使用不同完成预算。

规则：

- `small_inline`: 不进入 Trellis Finish。提交前只允许 direct scoped low-risk commit gate。
- `micro_task`: 只执行 scoped validation、diff check、commit-plan。spec update 默认记录为 follow-up，不阻塞 commit。
- `lite_task`: 执行必要验证和轻量 evidence；spec update 仅在命中 reusable contract 时执行，且不能改变 detail digest。
- `full_chain`: 保留完整 Finish，包括验证、spec update、commit、archive / finish-work 边界。

### REQ-FIN-002 Spec Update Budget

Phase 3.3 spec update 不再对所有 route 都是 commit 前硬阻塞。

规则：

- `micro_task`: 默认不写 spec，只写 `spec-update-decision.jsonl` 或 task-local note，状态为 `not_applicable` / `deferred`。
- `lite_task`: 只有满足 reusable engineering contract 条件时写 spec；否则记录 `deferred`.
- `full_chain`: spec update 仍为 required once。
- 所有 route 中，spec update 记录不得写入会参与 planning / detail digest 的文件。

### REQ-FIN-003 Mutable Evidence Digest Isolation

执行证据、验证证据、spec 萃取记录、worker cleanup 记录不得改变已确认 detail gate 的 artifact digest。

建议新增或规范化以下文件：

- `implementation-evidence.jsonl`
- `verification-evidence.jsonl`
- `spec-extraction.jsonl`
- `worker-cleanup.jsonl`
- `commit-plan.json`

禁止将以下内容追加到 `implement.md` 后再要求 detail Gate 保持 current：

- test/analyze/detect_changes 结果。
- Phase 3.3 九段萃取记录。
- worker cleanup 状态。
- commit scope 推断过程。

### REQ-FIN-004 Commit Plan Command

Commit 前需要一个机器可读计划，而不是让 agent 临场读取 `guru_gate.py` 源码推断。

期望命令：

```bash
python3 .trellis/scripts/guru/guru_gate.py commit-plan [task_dir]
```

输出内容：

```json
{
  "schema_version": 1,
  "route": "micro_task|lite_task|full_chain|direct_small_inline",
  "commit_mode": "direct|implementation|docs|tooling|split_required",
  "allowed_stage_paths": [],
  "forbidden_stage_paths": [],
  "required_commands": [],
  "optional_commands": [],
  "required_user_confirmations": [],
  "can_commit_now": false,
  "blocking_reasons": [],
  "suggested_stage_commands": []
}
```

### REQ-FIN-005 Commit Ready Stop Rule

一旦满足：

- route 对应验证完成。
- staged / dirty scope 已知。
- gate status ready 或 direct small_inline ready。
- commit-plan 已输出下一步 stage 范围。

主会话必须停止在 commit confirmation 前，不得自动扩展到 spec rewrite、journal rewrite、archive、TAPD update 或额外 review。

### REQ-FIN-006 Terminal Worker Auto Cleanup

`guru_supervise status` 或等价 runtime 应把 terminal `done|killed|error` worker 归档为非活跃，避免主会话多轮 `pgrep` / `kill`。

Markdown 先规定目标行为：

- status 显示 `terminal_workers` 和 `live_workers` 分开。
- `live_workers=0` 时不得提示还有阻塞 worker。
- 提供单条 `cleanup --terminal` 建议命令。

### REQ-FIN-007 Compact Commit Context

Commit 前应进入 compact commit context，只保留：

- `task_dir`
- `route`
- `gate-contract.json` 摘要
- latest current review run ids / digest
- allowed target paths
- validation commands and results
- dirty scope summary
- commit-plan output

不得在 commit 前重新加载完整 skill、memory、spec 全文，除非 commit-plan 报缺失。

## 5. PRD.md 调整方案

在 `.trellis/tasks/07-01-risk-based-gate-contract-routing/prd.md` 中增加以下内容。

### 5.1 Scope 增补

In scope 增加：

- Finish / Commit 阶段的 route-aware policy。
- Phase 3.3 spec update 是否阻塞 commit 的 route matrix。
- mutable evidence 与 planning/detail digest 的隔离规则。
- commit-plan 机器输出合同。
- terminal worker cleanup 的完成态归档规则。

Out of scope 增加：

- 本阶段不实现 runtime Python。
- 不引入 OCR 作为默认 review。
- 不把 spec update 完全取消；只按 route 降低默认阻塞性。

### 5.2 Definitions 增补

新增术语：

- **finish budget**: 每个 route 在验证、spec update、worker cleanup、commit-plan 上允许的最大默认收口范围。
- **mutable evidence**: 实现后产生的测试、验证、回写、cleanup、commit-plan 记录。
- **contract digest**: 用于 requirements / overview / detail confirmation 的稳定 artifact digest。
- **commit plan**: commit 前由 gate 生成的机器可读 staged-scope 计划。
- **commit ready stop**: 到达 commit 前硬边界时停止自动推进。

### 5.3 Behavior Specifications 增补

新增：

- BHV-007: micro/lite/full Finish 按 route 使用不同 spec update budget。
- BHV-008: mutable evidence 不得造成 detail Gate 快照失配。
- BHV-009: commit gate 必须提供 commit-plan，不要求 agent 读源码推断。
- BHV-010: terminal done worker 不应造成主会话继续等待或多轮清理。
- BHV-011: commit-ready 后主会话停止，不自动 stage/commit/TAPD/archive。
- BHV-012: compact commit context 限制尾部 token 增长。

### 5.4 Acceptance Criteria 增补

新增验收：

- 已完成质量验证的 `lite_task` 不会因为追加 Phase 3.3 记录到 `implement.md` 而导致 detail Gate 失配。
- `micro_task` 默认输出 spec update deferred，不阻塞 commit。
- `lite_task` 只有 reusable contract 命中时写 spec，且写入文件不在 detail digest 中。
- `full_chain` 仍要求完整 spec update。
- `guru_gate.py commit-plan` 能输出 allowed / forbidden stage paths 和 suggested stage commands。
- commit-ready 状态下，agent 给出下一步确认项后停止，不继续加载大段 skill/memory/spec。

## 6. Design.md 调整方案

在 `.trellis/tasks/07-01-risk-based-gate-contract-routing/design.md` 中增加 4 个设计单元。

### UNIT-finish-route-policy

职责：

- 读取 route / gate contract。
- 给出 Finish 预算。
- 决定 Phase 3.3 是 `required`、`conditional`、`deferred` 还是 `not_applicable`。

Route matrix：

| route | verification | spec update | worker cleanup | commit-plan | auto-stop |
| --- | --- | --- | --- | --- | --- |
| `direct_small_inline` | scoped diff/check only | n/a | n/a | required | stop before commit |
| `micro_task` | scoped deterministic checks | deferred by default | terminal-only | required | stop before commit |
| `lite_task` | focused tests + scoped analyze | conditional reusable contract | terminal-only | required | stop before commit |
| `full_chain` | full task validation | required | required | required | stop before commit/archive |

### UNIT-mutable-evidence-store

职责：

- 定义 mutable evidence 文件位置。
- 明确这些文件不参与 planning/detail digest。
- 替代向 `implement.md` 追加执行后证据的做法。

建议文件：

- `implementation-evidence.jsonl`
- `verification-evidence.jsonl`
- `spec-extraction.jsonl`
- `worker-cleanup.jsonl`

### UNIT-commit-plan-gate

职责：

- 在 commit 前输出机器可读 staged plan。
- 避免 agent 读取 `guru_gate.py` 源码推断。
- 统一 direct small_inline、micro_task、lite_task、full_chain 的 commit 入口。

输出应包含：

- route。
- commit_mode。
- allowed paths。
- forbidden paths。
- required evidence。
- can_commit_now。
- blocking reasons。
- suggested stage commands。

### UNIT-finish-context-compact

职责：

- 定义 commit 前最小上下文。
- 禁止自动重读大体量 skill/spec/memory。
- 降低尾部每步 12 万+ input token 的风险。

触发条件：

- quality green。
- detect_changes / fallback evidence 已记录。
- current gate status 已确认或 direct small_inline ready。
- commit-plan 已生成。

## 7. Implement.md 调整方案

在 `.trellis/tasks/07-01-risk-based-gate-contract-routing/implement.md` 中增加后续切片。

### Slice 5 - Finish Route Policy Markdown / Spec

目标：先把 Finish route matrix 写入 task 和 spec。

计划：

- 更新 `prd.md` 的 BHV / REQ / AC。
- 更新 `design.md` 的 UNIT-finish-route-policy。
- 更新 `.trellis/spec/cli/backend/guru-overlay-gates.md`，新增 `Scenario: Route-Aware Finish and Commit Contract`。

验证：

- `guru_gate.py requirements|overview|detail|implement` 仍通过。
- trace matrix 覆盖新增 BHV。

### Slice 6 - Mutable Evidence Isolation

目标：后续 runtime 支持 evidence JSONL，不再把执行后证据写入 `implement.md`。

计划：

- 文档规定 mutable evidence 文件。
- runtime 后续实现 `_gate_digest("detail")` 排除这些文件。
- workflow/skills 改为把验证结果写 evidence JSONL。

验证：

- 向 evidence JSONL 追加记录后，detail digest 不变。
- 向 `design.md` / `implement.md` 修改合同正文后，detail digest 仍会变化并阻塞。

### Slice 7 - Commit Plan Contract

目标：新增 `commit-plan` 机器输出。

计划：

- 文档先定义 JSON schema。
- 后续 runtime 在 `guru_gate.py` 增加 `commit-plan`。
- `check-commit` 复用同一 decision model。

验证：

- direct small_inline 输出 `direct` plan。
- micro_task 输出 scoped plan。
- lite_task 输出 implementation review target paths。
- full_chain 输出 current strict target paths。
- task/spec/journal/tooling 混入 implementation commit 时输出 `split_required`。

### Slice 8 - Worker Cleanup and Commit Context

目标：减少 commit 前无意义等待和 token 膨胀。

计划：

- 文档定义 terminal worker 状态显示。
- 后续 runtime 增加 `cleanup --terminal` 或 status 自动归档。
- workflow/skills 增加 compact commit context 规则。

验证：

- terminal done worker 不再让主会话继续等待。
- commit-ready 后不再重读完整 skill/memory/spec。

## 8. Spec Markdown 调整方案

在 `.trellis/spec/cli/backend/guru-overlay-gates.md` 增加 scenario。

建议标题：

```md
### Scenario: Route-Aware Finish and Commit Contract
```

建议结构：

1. Scope / Trigger
2. Route Matrix
3. Mutable Evidence Boundary
4. Commit Plan Schema
5. Adversarial Disabled Boundary
6. Worker Cleanup Contract
7. Good / Bad Cases
8. Tests Required

核心规则：

- Finish policy 和 commit policy 同属 Guru gate surface。
- `adversarial_enabled=false` 只影响 adversarial reviewer requirement。
- mutable evidence 不参与 detail digest。
- spec update 按 route 分为 required / conditional / deferred / n/a。
- commit-plan 是 commit 前唯一 stage-scope SSOT。
- OCR 不作为默认完成条件。

## 9. Workflow / Skill Markdown 调整方案

### 9.1 Guru Workflow

更新位置：

- `packages/cli/src/templates/guru/workflows/guru-client.md`
- `packages/cli/src/templates/guru/workflows/guru-go.md`
- `packages/cli/src/templates/guru/workflows/guru-h5.md`
- `packages/cli/src/templates/guru/workflows/guru-ios.md`
- mirror: `guru-template/workflows/*`

新增规则：

- Phase 3.3 由 route-aware finish policy 决定是否阻塞。
- commit 前必须运行或读取 `commit-plan`。
- 到 `COMMIT_READY` 后停止，等待用户确认 stage/commit。
- 不把 verification / extraction evidence 追加到 `implement.md`。
- 不默认 OCR。

### 9.2 Client Small Iteration Skill

更新位置：

- `packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md`
- `guru-template/overlay/agents-skills/client-small-iteration-dev/SKILL.md`

新增规则：

- low / medium / high route 表中补 Finish budget。
- `lite_task` 的 spec update 是 conditional，不是机械 full-chain。
- direct small_inline commit 只适用于 no-task、低风险、最多 3 个实现文件、无 high-risk / cross-layer / task artifact staged。
- commit-ready 后不继续做 spec/journal/archive。

## 10. 后续 Runtime 实现切片

本文件只定义 Markdown 调整方案。后续实现建议按以下顺序：

1. 先更新任务 PRD/design/implement 和 spec Markdown。
2. 加 `commit-plan` JSON decision model，但暂不改变 `check-commit` 行为。
3. 将 `check-commit` 改为复用 `commit-plan` decision。
4. 加 mutable evidence JSONL，并让 detail digest 不包含这些文件。
5. 改 workflow/skill，停止把 post-implementation evidence 写 `implement.md`。
6. 加 worker terminal cleanup。
7. 加 compact commit context 文案。
8. 跑 source/template mirror check 和 verify suite。

## 11. 验证矩阵

| Case | Expected |
| --- | --- |
| direct small_inline 两个低风险 staged 文件 | `commit-plan.can_commit_now=true`, mode `direct` |
| direct small_inline 包含 `.trellis/tasks/**` | block, require micro/lite/full task |
| micro_task GitNexus unavailable with allowed degradation | pass only if compensating checks present |
| micro_task spec update missing | not block by default |
| lite_task reusable contract hit | spec update conditional required |
| lite_task non-reusable implementation fix | spec update deferred, commit can continue |
| full_chain missing spec update | block |
| append `verification-evidence.jsonl` | detail digest unchanged |
| append `implement.md` contract body | detail digest changed and blocked |
| adversarial_enabled=false + current double clean | adversarial not required |
| adversarial_enabled=false + current medium finding | still blocked |
| terminal done worker remains in status | cleanup reports terminal, not live blocker |
| commit-ready reached | main session stops before stage/commit |

## 12. 风险与取舍

- 将 Phase 3.3 改为 route-aware 会降低低/中风险任务尾部成本，但必须保证 full_chain 不被削弱。
- mutable evidence 脱离 `implement.md` 后，需要明确哪些文件是审计证据，避免证据散落。
- `commit-plan` 会增加一个命令，但能减少 agent 临场推断和错误 stage。
- compact commit context 会降低 token，但要求前置 evidence 已结构化，否则 agent 可能缺上下文。
- worker cleanup 自动化要避免误杀仍在运行的 worker，只能清 terminal 状态。

## 13. 推荐落地顺序

推荐先做 Markdown 调整，再实现 runtime：

1. 将本方案评审通过。
2. 按第 5-9 节更新 PRD/design/implement/spec/workflow/skill Markdown。
3. 跑结构 gate 和 trace matrix。
4. 实现 `commit-plan`，让输出先只读。
5. 将 `check-commit` 迁移到复用 `commit-plan`。
6. 实现 mutable evidence isolation。
7. 实现 route-aware Phase 3.3。
8. 实现 terminal worker cleanup。
9. 增加 verify tests 和 mirror checks。
10. 再进入 commit/archive。

## 14. 完成定义

本 Markdown 调整完成后，应满足：

- 本任务 PRD/design/implement 明确覆盖 Finish / Commit route-aware 规则。
- 本地 spec 有可复用 Guru gate scenario。
- workflow/skill 文案不再暗示所有 route 都必须 full Phase 3.3。
- 后续 runtime 实现有清晰切片和验证矩阵。
- 不触碰 Python runtime，不改变当前未提交代码行为。
