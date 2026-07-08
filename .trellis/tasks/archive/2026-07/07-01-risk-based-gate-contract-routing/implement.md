# Risk-based intake routing with gate contracts implementation plan

## §1 计划 / 切片

### Slice 1 - Contract model and validation

Design unit: UNIT-gate-contract-store

Goal: add the task-local contract/degradation model without changing commit behavior yet.

Tasks:

- Add `guru_contract.py` or an equivalent shared module under Guru overlay verify scripts.
- Define global policy for `micro_task`, `lite_task`, and `full_chain`.
- Implement read/validate helpers for `gate-contract.json`.
- Implement append/read/validate helpers for `gate-degradations.jsonl`.
- Keep all helpers Python standard-library only.

Validation:

- Unit fixtures for valid micro/lite/full contracts.
- Negative fixtures for high-risk downgrade, malformed JSON, unauthorized degradation, and missing compensating checks.

### Slice 2 - Intake risk router

Design unit: UNIT-intake-risk-router

Goal: extend existing risk logic into low/medium/high route selection while reusing current `guru_risk.py` high-risk signals.

Tasks:

- Extend `guru_risk.py` with medium risk vocabulary and route decision helpers.
- Keep high-risk precedence over low hints.
- Treat scan failure as non-low.
- Update `client-small-iteration-dev` and Guru workflow request triage text to describe `small_inline`, `micro_task`, `lite_task`, and `full_chain`.

Validation:

- Low UI/color/text request fixture -> `small_inline`.
- Low + commit fixture -> `micro_task`.
- Medium local behavior bug fixture -> `lite_task`.
- Payment/privacy/schema/workflow/gate fixture -> `full_chain`.
- Git scan failure fixture -> not low.

### Slice 3 - Commit gate integration

Design unit: UNIT-commit-contract-gate

Goal: make `guru_gate.py check-commit` contract-aware while preserving full-chain strict behavior.

Tasks:

- Load and validate gate contract in `cmd_check_commit`.
- Preserve current no-contract/full-chain branch byte-for-byte where feasible.
- Add `micro_task` branch with scoped staged path, low-risk, degradation, and compensating-check validation.
- Add `lite_task` branch that keeps existing in-progress/review requirements and adds contract validation.
- Improve blocking messages with route and next recovery action.

Validation:

- Existing check-commit tests still pass.
- New micro task tests cover allowed scoped commit, task-artifact-only block, out-of-scope staged path block, high-risk path block, and GitNexus unavailable allowed degradation.
- New full-chain test proves unauthorized degradation does not weaken strict branch.

### Slice 4 - Template mirror and docs

Design unit: UNIT-template-sync

Goal: keep source template and standalone guru-template aligned.

Tasks:

- Mirror changed overlay/workflow/skill/spec files between `packages/cli/src/templates/guru/**` and `guru-template/**`.
- Update any config snippets or hook comments that describe `check-commit`.
- Record whether local dogfood files were touched; default is no local `.trellis` / `.codex` edits.

Validation:

- Targeted mirror diff for every changed pair.
- `git diff --check`.
- Guru verify test script for overlay verify changes.

### Slice 5 - Finish route policy markdown and spec

Design unit: UNIT-finish-route-policy

Goal: make Finish / Commit route-aware in task and spec artifacts before touching runtime.

Tasks:

- Extend `prd.md` with BHV-007..BHV-012, REQ-015..REQ-021, failure paths, and acceptance criteria.
- Extend `design.md` with UNIT-finish-route-policy, UNIT-mutable-evidence-store, UNIT-commit-plan-gate, and UNIT-worker-cleanup-and-compact-context.
- Extend `.trellis/spec/cli/backend/guru-overlay-gates.md` with `Scenario: Route-Aware Finish and Commit Contract`.
- Keep OCR out of the default review path.

Validation:

- `guru_gate.py requirements|overview|detail|implement` still pass for this task.
- `guru_gate.py trace-matrix --strict` includes BHV-007..BHV-012.
- `git diff --check` is clean for touched Markdown.

### Slice 6 - Commit plan decision model

Design unit: UNIT-commit-plan-gate

Goal: expose the staged-scope decision before commit so agents do not read runtime source to infer stage commands.

Tasks:

- Add `guru_gate.py commit-plan [task_dir]`.
- Implement a read-only commit decision model that reports route, commit mode, allowed/forbidden paths, blocking reasons, and suggested stage commands.
- Make direct small_inline, micro_task, lite_task, and full_chain decisions visible through the same JSON schema.
- Keep `check-commit` behavior unchanged in the first step if needed, then migrate it to reuse the decision model.

Validation:

- Direct small_inline fixture returns `commit_mode=direct`, `can_commit_now=false`, and micro_task recovery commands when no valid commit contract exists.
- Active planning/no-contract low-risk staged fixture returns micro_task recovery commands and does not point recovery at requirements or check-implementation.
- Task/spec/journal mixed with implementation files returns `commit_mode=split_required`.
- Full-chain review digest mismatch returns blocking reason.
- `check-commit` and `commit-plan` agree on pass/block cases once integration is complete.

### Slice 7 - Mutable evidence isolation

Design unit: UNIT-mutable-evidence-store

Goal: stop post-implementation evidence from invalidating detail Gate confirmation.

Tasks:

- Add or document task-local mutable evidence files: `verification-evidence.jsonl`, `spec-extraction.jsonl`, `worker-cleanup.jsonl`, `commit-plan.json`.
- Ensure detail digest excludes mutable evidence files.
- Update workflow/skill text so verification and spec extraction evidence is written to mutable evidence, not appended to `implement.md`.
- Keep modifications to `design.md` / `implement.md` contract text as digest-affecting.

Validation:

- Appending mutable evidence does not change `guru_gate.py digest detail`.
- Editing `implement.md` still changes detail digest.
- Existing tasks without mutable evidence files behave as before.

### Slice 8 - Worker cleanup and compact commit context

Design unit: UNIT-worker-cleanup-and-compact-context

Goal: reduce commit-tail waiting and token growth after quality is green.

Tasks:

- Update `guru_supervise status` or adjacent helper to distinguish live and terminal workers.
- Provide terminal cleanup as a single action, not a manual multi-command sequence.
- Update workflow/skill text to switch to compact commit context after quality green + commit-plan.
- Enforce commit-ready stop: no automatic stage/commit/TAPD/archive or speculative spec rewrite.

Validation:

- Terminal-only worker state is not a live blocker.
- Live worker state still blocks or asks the user to wait/interrupt.
- Commit-ready state reports next confirmation and stops.

## §2 执行 / 改动文件

Planned source files:

- `packages/cli/src/templates/guru/overlay/verify/guru_contract.py` or equivalent new shared module.
- `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`.
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`.
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`.
- `packages/cli/src/templates/guru/overlay/hooks/guru_after_create.py`.
- `packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md`.
- `packages/cli/src/templates/guru/workflows/guru-client.md`.
- Platform variants only if they carry duplicated routing text that would otherwise drift.
- Matching `guru-template/**` mirror files.
- Future Slice 6/7/8 runtime files:
  - `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
  - local dogfood `.trellis/scripts/guru/guru_gate.py` / `guru_supervise.py` only if needed for validation.

Before editing symbols:

- Run GitNexus impact for edited symbols required by `AGENTS.md`, at minimum `task_risk_level`, `cmd_check_commit`, `_implementation_review_problem`, and any new imported helper call sites.
- For Slice 6/7/8 runtime changes, also run impact or static fallback for `cmd_check_commit`, `_direct_low_risk_commit_problem`, `_implementation_review_problem`, `_gate_digest`, `cmd_status`, and any new `cmd_commit_plan` / worker cleanup helper.
- If GitNexus is unavailable, record the exact blocker and use static fallback (`rg` callers, tests, diff scope). Because this task is about gate degradation, such a failure must be documented, not silently ignored.

Execution log:

- 2026-07-01: `task.json.status` 已确认是 `in_progress`，用户批准后开始 source/template 实现。
- 2026-07-01: GitNexus impact 按 AGENTS 要求执行但失败；命令：
  `node .gitnexus/run.cjs impact task_risk_level --direction upstream && node .gitnexus/run.cjs impact cmd_check_commit --direction upstream && node .gitnexus/run.cjs impact _implementation_review_problem --direction upstream`。
  阻塞原因：LadybugDB `lbugjs.node` native binary 是 `arm64`，当前 Node 需要 `x86_64`，无法加载。按本任务降级原则记录为工具不可用，未继续反复重建索引。
- 2026-07-01: 静态补偿：用 `rg` 搜索 `task_risk_level`、`cmd_check_commit`、`_implementation_review_problem`、`assess_intake`、`default_contract`、`validate_contract`、`validate_degradations`、`ROUTE_*` 调用面；变更面限定在 Guru overlay verify/hooks/workflow/skill 及 `guru-template` 镜像。
- 2026-07-01: 已新增 `guru_contract.py` 合同/降级 helper，扩展 `guru_risk.py` intake route，接入 `guru_gate.py check-commit` micro/lite/full 合同路径，更新 `guru_after_create.py` 默认 fail-safe 合同，更新 `apply.sh` 和 verify tests。
- 2026-07-01: 按用户最新要求将中风险新 route 命名统一为 `lite_task`，同时保留既有 `task.json.guru_chain=light` 兼容语义。
- 2026-07-01: 未修改当前本地 `.trellis/scripts/guru/` 或本地 platform hooks；仅任务产物 `.trellis/tasks/07-01-risk-based-gate-contract-routing/` 作为 dogfood 记录被更新。
- 2026-07-02: 按用户“审查不要通过 OCR”要求，本轮未运行 OCR/open-code-review；独立 `trellis-check` 子代理启动失败，返回 provider 503 `GW_ALL_PROVIDERS_UNAVAILABLE`，因此改由主会话执行同等本地检查并记录结果。
- 2026-07-02: 用户补充真实简单任务失败场景：`guru_ai_himora` 中仅 staged `character_chat_ai_bubble.dart` 与 `character_chat_message_list_test.dart`，`git diff --cached --check` 和 GitNexus `detect_changes` 均通过，但 `git commit -m "fix: style character chat dialogue text"` 被 `check-commit` 以“无法定位任务目录，请显式传 task_dir”拦截。修复方向：`check-commit` 在无显式 task_dir、无可解析当前 task 时，不再使用唯一 planning fallback，而是先读取 staged paths；若 staged scope 是最多 3 个非 task/workspace、非 high-risk、非跨层/storage 的实现文件，则允许 direct `small_inline` commit，否则要求创建/切换 `micro_task` 或 `lite/full`。
- 2026-07-02: Slice 6 runtime/source-template implementation started after Markdown structure update. GitNexus impact was attempted for `cmd_check_commit`, `_direct_low_risk_commit_problem`, `_implementation_review_problem`, and `main`; helper symbols were not found by the index (`risk=UNKNOWN`), while `main` was ambiguous with max `LOW`. `_gate_digest` was not modified because earlier impact showed high blast radius.
- 2026-07-02: Added read-only `guru_gate.py commit-plan [task_dir]` to source template, `guru-template`, and local dogfood runtime. The command emits compact JSON with `route`, `task_dir`, `staged_paths`, `can_commit_now`, `split_required`, `blocking_reasons`, `required_commands`, `suggested_stage_commands`, and contract validity fields. It reuses existing direct low-risk, micro contract, implementation-ready, implementation review, and contract validation checks without writing evidence or changing digest behavior.
- 2026-07-02: Updated source and mirror workflows for client/go/h5/ios so Phase 3.4 first reads `commit-plan`, reports its compact summary, and still relies on `check-commit` / PreToolUse hook as the hard gate before any commit.

## §3 证据 / analyze / test

Required validation commands:

- `python3 packages/cli/src/templates/guru/overlay/verify/guru_gate.py requirements .trellis/tasks/07-01-risk-based-gate-contract-routing`
- `python3 packages/cli/src/templates/guru/overlay/verify/guru_gate.py overview .trellis/tasks/07-01-risk-based-gate-contract-routing`
- `python3 packages/cli/src/templates/guru/overlay/verify/guru_gate.py detail .trellis/tasks/07-01-risk-based-gate-contract-routing`
- `python3 packages/cli/src/templates/guru/overlay/verify/guru_gate.py implement .trellis/tasks/07-01-risk-based-gate-contract-routing`
- `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
- `git diff --check`
- Targeted mirror consistency checks for changed `packages/cli/src/templates/guru/**` and `guru-template/**` pairs.

Optional broader checks:

- `pnpm typecheck` only if TypeScript template registration or CLI code is touched.
- `pnpm test` targeted suites only if template registration / packaging code is touched.

Evidence log:

- 2026-07-01: `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` 在 `lite_task` 改名前完成一轮全量 Guru verify 测试：454 passed / 0 failed。`lite_task` 改名后需要重跑。
- 2026-07-01: `diff -q` 检查以下 source/template 镜像对无差异：`guru_contract.py`、`guru_risk.py`、`guru_gate.py`、`guru_after_create.py`、`apply.sh`、`run_tests.sh`、`client-small-iteration-dev/SKILL.md`、client workflow。
- 2026-07-01: `python3 -m py_compile` 覆盖 source 与 mirror 的 `guru_contract.py`、`guru_risk.py`、`guru_gate.py`、`guru_after_create.py`，通过。
- 2026-07-01: 旧中风险 route 字面量/常量残留检查覆盖 `packages/cli/src/templates/guru`、`guru-template`、当前任务目录，无残留。
- 2026-07-01: `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` 在 `lite_task` 改名后重跑，结果：454 passed / 0 failed。
- 2026-07-01: `guru_gate.py requirements|overview|detail|implement .trellis/tasks/07-01-risk-based-gate-contract-routing` 全部通过。
- 2026-07-01: `python3 ./.trellis/scripts/task.py validate .trellis/tasks/07-01-risk-based-gate-contract-routing` 通过，`implement.jsonl` 与 `check.jsonl` 各 6 entries。
- 2026-07-01: `guru_gate.py trace-matrix .trellis/tasks/07-01-risk-based-gate-contract-routing --strict` 通过，BHV-001..BHV-006 均闭合，无孤儿/断链。
- 2026-07-01: `git diff --check` 通过。
- 2026-07-01: `apply.sh` 注册检查：source 与 mirror 均拷贝 `verify/guru_contract.py` 到 `.trellis/scripts/guru/guru_contract.py`，安装后 import smoke 包含 `guru_contract`。
- 2026-07-02: `cp packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh guru-template/overlay/verify/tests/run_tests.sh` 同步上一轮 heredoc 缩进修复后的测试镜像。
- 2026-07-02: `python3 -m py_compile` 再次覆盖 source 与 mirror 的 `guru_contract.py`、`guru_risk.py`、`guru_gate.py`、`guru_after_create.py`，通过。
- 2026-07-02: `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` 全量通过，结果：463 passed / 0 failed。新增覆盖包含 no-path low keyword -> medium/lite、micro 空 scope 阻断、空 fallback_checks 阻断、risk typo 阻断、malformed contract 不 traceback、non-full high-risk staged path 阻断、`adversarial_enabled=false` 动态放行双普通 clean 但不绕过 current requirements blocker。
- 2026-07-02: `guru_gate.py requirements|overview|detail|implement .trellis/tasks/07-01-risk-based-gate-contract-routing` 全部通过。
- 2026-07-02: `python3 ./.trellis/scripts/task.py validate .trellis/tasks/07-01-risk-based-gate-contract-routing` 通过，`implement.jsonl` 与 `check.jsonl` 各 6 entries。
- 2026-07-02: `guru_gate.py trace-matrix .trellis/tasks/07-01-risk-based-gate-contract-routing --strict` 通过，BHV-001..BHV-006 均闭合，无孤儿/断链。
- 2026-07-02: 全部 16 个 source/template 对应文件执行 `diff -q`，无镜像差异；覆盖 overlay、hook、verify、workflow、四个 gate-confirmation specs。
- 2026-07-02: 旧 light 系列 route/token 残留扫描覆盖 `packages/cli/src/templates/guru`、`guru-template`、当前任务目录，除用户原始引用作为决策证据保留并附 `latest_update: "light 改为 lite"` 外无残留。
- 2026-07-02: `git diff --check` 通过。
- 2026-07-02: Phase 3.3 spec update completed：新增 `.trellis/spec/cli/backend/guru-overlay-gates.md`，记录 risk routing、gate-contract、gate-degradation、`adversarial_enabled` 和 commit-gate fail-closed 合同；并更新 `.trellis/spec/cli/backend/index.md`。
- 2026-07-02: Phase 3.4 pre-commit staging completed with explicit pathspecs excluding unrelated `marketplace`; `git diff --cached --check` initially found trailing whitespace in `prd.md`, then passed after mechanical cleanup.
- 2026-07-02: GitNexus `detect_changes --scope staged` was attempted before commit:
  `node .gitnexus/run.cjs detect_changes --scope staged --repo "/Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree"`。
  Result: blocked by the same LadybugDB native binary architecture mismatch (`lbugjs.node` has `arm64`, current Node needs `x86_64`).
- 2026-07-02: Local dogfood config updated per user request: `.trellis/config.yaml` now sets `guru.supervision.adversarial_enabled: false`; this should only remove the adversarial reviewer requirement and must not bypass current digest, double clean review, current blocked review, or medium+ findings.
- 2026-07-02: After config dogfood, `guru_gate.py status` shows requirements adversarial review is disabled by config as expected. `guru_gate.py check-implementation` still blocks because the requirements Gate is not human-confirmed yet; this proves the config does not bypass confirmation gates.
- 2026-07-02: User attempted the prompted command `python3 .trellis/scripts/guru/guru_gate.py confirm requirements ...` and hit file-not-found because this source worktree did not have the Guru overlay runtime installed locally. Minimal dogfood installed the same seven Python runtime files that `overlay/apply.sh` copies into `.trellis/scripts/guru/`: `guru_gate.py`, `guru_risk.py`, `guru_contract.py`, `guru_review_record.py`, `guru_after_create.py`, `guru_config_patch.py`, and `guru_supervise.py`. Validation: `python3 -m py_compile .trellis/scripts/guru/*.py`, import smoke, and `guru_gate.py status` all passed.
- 2026-07-02: Himora simple-task commit blocker regression covered. Added direct `small_inline` check-commit tests for no-task scoped low-risk commit, high-risk `.trellis/config.yaml` path block, more than 3 files block, and hook execution when old planning/in_progress tasks exist but no current task resolves. Local smoke reproduced the reported shape in a temp repo with staged `lib/ui/character_chat_ai_bubble.dart` + `test/ui/character_chat_message_list_test.dart`; result: `[guru-gate:check-commit] COMMIT_READY: direct small_inline scoped low-risk commit`.
- 2026-07-02: `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` rerun after the simple-task hook fix, result: 467 passed / 0 failed.
- 2026-07-02: Source/template/local runtime sync rechecked for `guru_gate.py` and `run_tests.sh`: `packages/cli/src/templates/guru/overlay/verify/guru_gate.py` equals `guru-template/overlay/verify/guru_gate.py` and local dogfood `.trellis/scripts/guru/guru_gate.py`; source `run_tests.sh` equals `guru-template` mirror.
- 2026-07-02: GitNexus impact for the newly edited `cmd_check_commit` branch was re-attempted after the native binary repair. Command: `node .gitnexus/run.cjs impact cmd_check_commit --direction upstream --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree`. Result: tool ran but index returned `Target 'cmd_check_commit' not found`, `risk=UNKNOWN`, `impactedCount=0`; static compensation remains the source/template/local mirror diff review plus the 467-pass Guru verify suite.
- 2026-07-02: GitNexus `detect_changes --scope staged --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree` ran successfully after staging. Result: 48 files, 192 symbols, 18 affected processes, risk `critical`. This is expected for Guru gate/template/hook changes and confirms the overall task must remain on full-chain commit governance; the direct `small_inline` branch only applies to no-task low-risk downstream commits, not to this source/template change.
- 2026-07-02: Non-OCR review evidence recorded through `guru_gate.py record-review`: overview has two current-digest clean run ids (`main-overview-a-20260702-direct-small-inline`, `main-overview-c-20260702-direct-small-inline`) after resolving a parallel-write race; detail has two current-digest clean run ids (`main-detail-a-20260702-direct-small-inline`, `main-detail-b-20260702-direct-small-inline`) with deletion audit `none`. `guru_gate.py status` now shows requirements confirmed, overview review clean x2, detail review clean x2, and the remaining blocker is user-run `confirm detail` in strict mode.
- 2026-07-02: Added local Markdown adjustment plan `finish-commit-route-aware-md-plan.md` after diagnosing session `019f1e18-e3b7-77b1-ac30-06332e314250`: quality green to commit boundary consumed about 11 minutes and about 2.97M total tokens because Phase 3.3/spec extraction, mutable evidence digest churn, terminal worker cleanup, and commit-scope inference were not route-aware.
- 2026-07-02: Updated `prd.md`, `design.md`, `implement.md`, and `.trellis/spec/cli/backend/guru-overlay-gates.md` structure to cover Finish/Commit route-aware policy before adding new runtime behavior.
- 2026-07-02: `python3 -m py_compile packages/cli/src/templates/guru/overlay/verify/guru_gate.py guru-template/overlay/verify/guru_gate.py .trellis/scripts/guru/guru_gate.py` passed after adding `commit-plan`.
- 2026-07-02: `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` passed after adding `commit-plan` fixtures. Result: 482 passed / 0 failed. New coverage includes direct `small_inline` commit-plan pass/block JSON, `micro_task` commit-plan pass JSON, no-staged-changes block JSON, and root `target_paths=["."]` fallback that must not suggest `git add -- .`.
- 2026-07-02: Source/template/local runtime mirror checks passed for `guru_gate.py`; source/template mirror checks passed for `run_tests.sh` and all four workflow files (`guru-client`, `guru-go`, `guru-h5`, `guru-ios`).
- 2026-07-08: Added post-implementation intake recovery to `commit-plan` / `check-commit`: low-risk staged implementation diffs without a valid active contract now block direct commit and recommend micro_task recovery (`task.py create` + `init-contract --route micro_task --risk low`) instead of requirements/overview/detail backfill. Added regression coverage for no-task direct low-risk and active planning/no-contract low-risk recovery. Synced source, `guru-template`, and local dogfood runtime.
- 2026-07-08: Installed the refreshed Guru overlay into sibling repos `/Users/devSC/Documents/JobProject/guru_ai_himora` (`flutter`) and `/Users/devSC/Documents/MyProject/safe_land_web` (`h5`) via source `overlay/apply.sh`. Both installers passed built-in self-checks, target `guru_gate.py` py_compile passed, target `guru_gate.py` / workflow matched source templates, config dry-runs preserved existing supervision settings, and smoke `commit-plan` in temp repos produced `micro_task` post-implementation recovery instead of PRD/overview/detail backfill.
- 2026-07-08: User challenged that post-implementation recovery was not a complete "received task" routing mechanism. Added executable `guru_gate.py intake [task_dir] --description ... [--path ...] [--commit-requested] [--write-contract]` so low/no-commit returns `small_inline`, low+commit writes `micro_task`, medium routes `lite_task`, and high writes `full_chain`. `intake` without an explicit `task_dir` no longer binds the active task, preventing unrelated new requests from polluting the current task.
- 2026-07-08: Added executable `guru_gate.py record-degradation <task_dir> --gate ... --reason ... --command ... --check name:status[:evidence] ...`. The command validates the proposed degradation against `gate-contract.json` and existing `gate-degradations.jsonl` before append; invalid or under-compensated rows are rejected without modifying the JSONL.
- 2026-07-08: Guru verify suite passed after the intake/degradation command additions: `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` -> `517 passed / 0 failed`. New coverage includes no-task `intake` not binding active task, low+commit contract generation, high/full contract generation, valid degradation append, and invalid degradation no-append.
- 2026-07-08: Closed P0 high-risk override gap found in review. `guru_contract.validate_contract()` now rejects every `risk=high` contract whose selected route is not `full_chain`; staged high-risk path validation and micro commit guidance no longer exempt valid user override audits. High-risk `lite_task` / `micro_task` override attempts now fail in `init-contract`, `check-commit`, `check-implementation`, and `slice-plan`; source, `guru-template`, and local dogfood runtime were mirrored.

## §4 阻塞与偏差

Known risks:

- GitNexus may fail due to local native binary architecture mismatch. If it repeats, do not spin on re-analysis; record command and fallback evidence.
- `check-commit` is a high-risk gate surface. Existing full-chain behavior must be preserved before adding micro/lite exceptions.
- Adding a new Python file may require template registration or copy logic review if Guru overlay packaging does not automatically include it.
- Mirror drift between `packages/cli/src/templates/guru/**` and `guru-template/**` is a release blocker.
- Local dogfood edits are not in default scope. If required, they must be explicitly listed and kept out of source-template conclusions unless mirrored intentionally.

Rollback points:

- After Slice 1: remove `guru_contract.py` and tests; no runtime behavior should have changed.
- After Slice 2: revert risk/router text and helper additions; `check-commit` still old behavior.
- After Slice 3: revert `guru_gate.py` integration and commit tests; contract files become inert.
- After Slice 4: restore mirror pairs from source of truth and rerun diff checks.

Current status:

- Source/template implementation and local verification are complete. Awaiting final user decision on commit/archive; unrelated dirty `marketplace` remains untouched.
