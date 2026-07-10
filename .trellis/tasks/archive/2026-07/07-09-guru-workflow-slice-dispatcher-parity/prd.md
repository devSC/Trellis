# H5/Go/iOS Guru workflow slice dispatcher parity

## 目标

把 H5、Go、iOS 的 Guru workflow Phase 2.1 实现入口与 Flutter/client workflow 对齐：主会话在派发实现 worker 前，必须先运行 `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task-dir> --dry-run --backend auto`，读取 `codex.dispatch_mode` 与当前 `slice-plan`，再按返回计划选择 direct platform sub-agent、channel 或 inline 串行执行。

追加范围（用户已确认）：把 H5、Go、iOS、client 四个平台的 `[workflow-state:in_progress]` breadcrumb 也从“默认 channel”修正为 dispatch-mode aware。breadcrumb 是每轮注入主会话的高优先级提示；如果它继续写 channel-first，会覆盖或干扰 Phase 2.1 正文语义，导致项目已配置 `sub-agent` 时仍被带回 channel。

目标不是增加新的调度能力；底层 `slice-plan`、`implement-slices`、review coverage 与 dispatch-mode aware 逻辑已经由已归档任务 `07-09-guru-route-aware-parallel-slice-supervision` 实现。本任务只补齐非 Flutter/client workflow 文档与模板镜像，让所有 Guru 平台都稳定走同一个加速入口，避免 H5/Go/iOS 继续凭泛化文案绕过 dispatcher。

## 背景 / 已确认事实

- 已归档任务 `07-09-guru-route-aware-parallel-slice-supervision` 已实现：
  - `guru_gate.py slice-plan` 输出 `parallel_groups`、`target_paths`、`dirty_scope`、`resource_locks` 和 recommended commands。
  - `guru_supervise.py implement-slices` 支持 `--dry-run --parallel N --group <id> --backend auto|sub-agent|channel`。
  - `auto` 后端会读取 `codex.dispatch_mode`；当前默认是 `sub-agent`，只有配置或显式选择 `channel` 时才用 channel。
  - sub-agent brief 第一行带 `Active task: <path>`，并禁止 nested spawn implement/check。
  - 不安全 writer 并行会降级串行。
- Flutter/client workflow 已在 Phase 2.1 明确要求先运行 `implement-slices --dry-run --backend auto`。
- H5、Go、iOS workflow 目前只写“先按 `codex.dispatch_mode` 选择后端”，没有统一要求先读取 `implement-slices` dry-run plan。
- H5、Go、iOS、client 的 `[workflow-state:in_progress]` 当前仍含“默认用官方 trellis channel”文案；这会在 active task 的 per-turn breadcrumb 中造成 channel-first 误导。
- Guru workflow 文件存在双镜像：
  - source template：`packages/cli/src/templates/guru/workflows/*.md`
  - bundled mirror：`guru-template/workflows/*-workflow.md`
  两边必须保持同步，通过 `pnpm --filter @devsc/trellis run sync:guru:check` 验证。
- 本任务是 workflow/dispatch 合同变更，`intake` 判定为 high risk / `full_chain`。

## 行为需求

### BHV-001 H5 workflow 先读取 slice dispatcher plan

优先级：P0

Given 当前项目使用 H5 Guru workflow，
When 任务进入 Phase 2.1 实现步骤，
Then workflow 必须明确要求主会话先运行 `implement-slices <task-dir> --dry-run --backend auto`，再根据返回的 `selected_backend`、`dispatch_items`、`dispatch_now`、`deferred_slices` 选择派发方式。

### BHV-002 Go workflow 先读取 slice dispatcher plan

优先级：P0

Given 当前项目使用 Go Guru workflow，
When 任务进入 Phase 2.1 实现步骤，
Then workflow 必须与 Flutter/client 语义一致：先运行 `implement-slices --dry-run --backend auto`，再按返回 brief 或 channel plan 派发，而不是直接凭 `codex.dispatch_mode` 手工选择后端。

### BHV-003 iOS workflow 先读取 slice dispatcher plan

优先级：P0

Given 当前项目使用 iOS Guru workflow，
When 任务进入 Phase 2.1 实现步骤，
Then workflow 必须先读取 `implement-slices` dry-run plan；sub-agent、channel、inline 的后续行为必须来自该 plan。

### BHV-004 所有平台保留 dispatch-mode aware 与安全降级

优先级：P0

Given `implement-slices` 报告 `selected_backend`、`decision` 和 `downgrade_reasons`，
When workflow 指导主会话执行实现，
Then 文案必须保留以下边界：

- `sub-agent` 模式按返回的 `trellis-implement` brief 派发平台 sub-agent。
- `channel` 模式才使用官方 channel worker / `guru_supervise.py implement-check`。
- `inline` 模式串行手工执行。
- `decision=serial|blocked` 时不得强行并行。
- prompt 第一行必须是 `Active task: <path>`。
- worker 不得再嵌套 spawn `trellis-implement` / `trellis-check`。

### BHV-005 不改变平台领域实现口径

优先级：P1

Given H5、Go、iOS workflow 各自有平台实现顺序与 golden-path 红线，
When 补齐 dispatcher 入口，
Then 只能替换 Phase 2.1 的 dispatch 前置步骤，不得削弱或删除现有平台特有约束：

- H5：自底向上 `domain-type -> data-access -> server-action -> server-component -> client-component -> ui-component -> route`，server/client 边界、metadata/SEO、样式隔离等。
- Go：自下而上 `domain -> repository -> service -> transport -> app/config/main`，`net/http ServeMux`、分层单向、sentinel + `%w` + `errors.Is` 等。
- iOS：自底向上 `domain-model -> repository -> usecase -> viewmodel -> view`，FactoryKit DI、Repository 归属、ViewModel 与 WCDBSwift 边界等。

### BHV-006 模板镜像保持一致

优先级：P0

Given Guru workflows 存在 source template 与 bundled mirror，
When 修改 H5、Go、iOS workflow，
Then `packages/cli/src/templates/guru/workflows/*.md` 与 `guru-template/workflows/*-workflow.md` 必须同步，且 `sync:guru:check` 通过。

### BHV-007 workflow-state:in_progress breadcrumb dispatch-mode aware

优先级：P0

Given 当前会话处于 `in_progress` 状态，
When hook 注入 H5、Go、iOS 或 client workflow 的 `[workflow-state:in_progress]` breadcrumb，
Then breadcrumb 必须提示主会话先运行 `implement-slices <task-dir> --dry-run --backend auto` 读取 dispatcher plan，再根据 `selected_backend` 选择 `sub-agent`、`channel` 或 `inline`；不得再写“默认用官方 trellis channel”。

边界：

- `sub-agent`：按返回 brief 派发 `trellis-implement/check`，prompt 第一行 `Active task: <path>`，worker 不得嵌套 spawn implement/check。
- `channel`：只有 `selected_backend=channel` 时才使用官方 channel worker / `guru_supervise.py implement-check`。
- `inline`：串行手工执行。
- `decision=serial|blocked` 不得强行并行，按 `dispatch_now` / `deferred_slices` 推进。
- 保留各平台“不具备验证证据不得 commit；设计缺陷回 Phase 1”的提示。

### BHV-008 bundled workflow regression test dispatch-mode aware

优先级：P0

Given bundled Guru workflow tests覆盖 ordinary `in_progress` breadcrumb，
When H5、Go、iOS、client 的 breadcrumb 从 channel-first 改为 dispatch-mode aware，
Then `packages/cli/test/guru/guru-bundled.test.ts` 必须同步断言 dispatcher-plan-first 合同，而不是继续要求 ordinary `in_progress` 包含 `trellis channel`。

边界：

- `in_progress-channel` 仍保留 channel 后端专属断言。
- `in_progress-sub-agent` 与 `in_progress-inline` rollback mode 断言继续存在。
- targeted Vitest 必须覆盖该断言，避免模板文案正确但测试合同仍锁旧语义。

## 非目标

- 不修改 `guru_gate.py`、`guru_supervise.py` 或 `guru_review_record.py` 的运行逻辑。
- 不新增 dispatcher 参数或并行策略。
- 不改变 Flutter/client Phase 2.1 正文；本轮用户已明确要求改变 client 的 `[workflow-state:in_progress]` breadcrumb。
- 不放松 requirements/detail confirmation、implementation review、commit-plan、check-commit 或 dirty scope gate。
- 不把 H5/Go/iOS 强制改成 channel-first；channel 仍然只是配置或显式选择的后端。
- 不启动真实 full_chain benchmark；benchmark 归属另一个任务 `07-09-guru-full-chain-slice-acceleration-benchmark`。

## 失败路径

- 只改 source template 未改 bundled mirror：`sync:guru:check` 必须失败，不能收口。
- 只写“按 dispatch_mode 选择后端”但未要求 `implement-slices --dry-run --backend auto`：视为未满足 BHV-001/BHV-002/BHV-003。
- 文案暗示 channel 是默认后端：视为 dispatch-mode aware 回归。
- 文案暗示 `sub-agent` worker 可再 spawn implement/check：视为 nested-dispatch guard 回归。
- 修改中误删平台 golden-path 约束：视为平台实现口径回归。
- 仅更新目标项目 `.trellis/workflow.md` 而未更新 package template：视为不完整，后续安装仍会漂移。

## 未决问题

无阻塞未决问题。用户已确认创建本 follow-up；仓库证据已经回答范围、归属和实现边界。

## 验收标准

- [ ] H5 source template Phase 2.1 明确包含 `implement-slices <task-dir> --dry-run --backend auto`。
- [ ] Go source template Phase 2.1 明确包含 `implement-slices <task-dir> --dry-run --backend auto`。
- [ ] iOS source template Phase 2.1 明确包含 `implement-slices <task-dir> --dry-run --backend auto`。
- [ ] 对应 `guru-template/workflows/*-workflow.md` 镜像同步。
- [ ] H5、Go、iOS、client 的 `[workflow-state:in_progress]` breadcrumb 均不再包含“默认用官方 trellis channel”，且包含 `implement-slices <task-dir> --dry-run --backend auto`。
- [ ] 三个平台仍保留各自平台实现顺序、平台 skill 名称与验证红线。
- [ ] 文案明确 `sub-agent` / `channel` / `inline` 从 `implement-slices` 返回计划选择，不回到 channel-first。
- [ ] `guru-bundled.test.ts` 的 ordinary `in_progress` 回归测试断言 dispatcher-plan-first，而不是 channel-first。
- [ ] `pnpm --filter @devsc/trellis run sync:guru:check` 通过。
- [ ] `git diff --check` 与 `git diff --cached --check` 通过。
- [ ] 若需要提交，`commit-plan` 只允许本任务合同范围内的 workflow 文件与任务 artifact，且 implementation review clean。

## Question Loop Log

question_policy: evidence_only

- decision: 创建 full_chain follow-up 修复 H5/Go/iOS workflow dispatcher parity。
  user_quote: "确认"
  result: 已创建任务 `.trellis/tasks/07-09-guru-workflow-slice-dispatcher-parity`，`gate-contract.json.route=full_chain`，`risk=high`。
- decision: 本任务只做 workflow parity，不做真实 benchmark。
  evidence: 用户前一轮确认的三步计划中，第 3 步已拆为独立 benchmark 任务。
  result: benchmark 任务 `.trellis/tasks/07-09-guru-full-chain-slice-acceleration-benchmark` 单独跟踪。
- decision: 以 Flutter/client workflow 当前 Phase 2.1 文案作为目标语义基线。
  evidence: `packages/cli/src/templates/guru/workflows/guru-client.md` 已明确要求先运行 `implement-slices <task-dir> --dry-run --backend auto`。
  result: H5/Go/iOS 应补齐同等入口，而不是另造新文案模型。
- decision: 将 H5/Go/iOS/client 的 `[workflow-state:in_progress]` breadcrumb 也统一为 dispatch-mode aware。
  user_quote: "把 H5/Go/iOS/client 的 workflow-state:in_progress breadcrumb 也统一成 dispatch-mode aware"
  result: 当前任务范围追加 breadcrumb parity；client 仅改 breadcrumb，不改 Phase 2.1 正文。

## Brainstorm Evidence

### Question Policy

question_policy: evidence_only

- Skill loaded: `trellis-start`、`trellis-brainstorm`。
- Repository evidence inspected:
  - `.trellis/tasks/archive/2026-07/07-09-guru-route-aware-parallel-slice-supervision/prd.md`
  - `packages/cli/src/templates/guru/workflows/guru-client.md`
  - `packages/cli/src/templates/guru/workflows/guru-h5.md`
  - `packages/cli/src/templates/guru/workflows/guru-go.md`
  - `packages/cli/src/templates/guru/workflows/guru-ios.md`
  - `guru-template/workflows/guru-h5-workflow.md`
  - `guru-template/workflows/guru-go-workflow.md`
  - `guru-template/workflows/guru-ios-workflow.md`
  - `.trellis/spec/cli/backend/workflow-state-contract.md`
  - `.trellis/spec/cli/backend/index.md`
- Domain/terminology triggers:
  - `dispatch-mode aware` 是规范术语，表示通过 `codex.dispatch_mode` 和 dispatcher plan 选择 backend。
  - `sub-agent` 指 direct platform sub-agent，不等同于 durable `trellis channel` worker。
  - `implement-slices --dry-run` 是调度预览入口，不等同于实际执行所有 slice。
- Current code vs user intent conflicts:
  - 用户意图：H5/Go/iOS 也稳定使用已实现的 slice dispatcher 加速抓手。
  - 当前代码事实：H5/Go/iOS Phase 2.1 只写“先按 `codex.dispatch_mode` 选择后端”，没有像 client 一样要求先跑 `implement-slices --dry-run --backend auto`。
- Product decisions confirmed:
  - 不新增 runtime 逻辑，只修 workflow parity。
    source_quote: "确认"
  - 不削弱各平台原有 golden-path。
    confirmed_ref: "repository-evidence: H5/Go/iOS current workflow platform-specific Phase 2.1 paragraphs"
  - 不把 channel 重新设为默认。
    confirmed_ref: "archived-task: 07-09-guru-route-aware-parallel-slice-supervision dispatch-mode aware decision"
- Open product/scope/risk questions:
  - 无阻塞问题；本任务可进入 overview/detail planning。

## 备注

- 本文档只记录需求、边界和验收；技术承接写在 `design.md`，执行顺序写在 `implement.md`。
