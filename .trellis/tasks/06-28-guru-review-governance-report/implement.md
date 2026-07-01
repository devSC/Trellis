# Guru Review Governance Root-Cause Repair Implementation Plan

## 1. 当前边界

本任务已在用户确认后执行：

```bash
python3 ./.trellis/scripts/task.py start .trellis/tasks/06-28-guru-review-governance-report
```

`task.json.status` 已从 `planning` 进入 `in_progress`。本轮实现只修改 Guru/Trellis runtime、overlay 模板、workflow/spec/skill 文案、测试和任务本地记录；不修改 Himora 业务代码，也不提交/归档。

## 2. 执行顺序

### P0 生命周期硬闸

1. 修改 `guru_gate.py`：
   - 增加 `check-start`、`check-implementation`、`check-commit`。
   - 保留 `check` 为 `check-start` alias。
   - 修改 `cmd_status` / `cmd_check` 输出，明确 `START_READY` 只允许 `task.py start`。
   - 为 `check-commit` 增加 staged scope / status / implementation review 基础校验。
2. 修改 `guru_supervise.py`：
   - `implement`、`check`、`implement-check` 启动前要求 `status == in_progress`。
   - fail-closed 时不启动 worker，并输出修复步骤。
3. 新增 `block-unstarted-commit.sh`：
   - 命令位识别 `git commit`。
   - 调用 `guru_gate.py check-commit`。
   - 失败退出 2。
4. 更新 hook/config 模板，确保脚本被安装并被平台 hook 引用：
   - Claude：更新 `apply.sh` 的 `SHARED_HOOKS` / `INSTALLED_HOOKS`，更新 `claude-settings.hooks.json` 的 `PreToolUse` `matcher=Bash`。
   - Codex：新增 `codex-hooks.hooks.json`，让 `apply.sh` 在目标存在 `.codex/` 时安装 `.codex/hooks/block-unstarted-commit.sh` 并幂等合并 `.codex/hooks.json` 的 `PreToolUse` `matcher=Bash`。
   - 不修改 Trellis 通用 `packages/cli/src/templates/codex/hooks.json` 来硬塞 Guru 专属逻辑；Guru overlay apply 是 Guru hook 的安装边界。

### P1 Brainstorm 和确认语义

1. 修改 `guru_gate.py` 的 `Brainstorm Evidence` 校验：
   - 支持 `Question Loop Log`。
   - 支持 `Question Policy: evidence_only|mixed`。
   - 禁止原始 bug quote 伪装成当前轮确认。
   - 禁止模糊确认批量关闭多个 OQ。
2. 修改 `requirement-writing/SKILL.md`：
   - 增加 `Question Loop Log` 输出要求。
   - 增加 `Question Policy` 输出要求。
   - 明确 `source_quote`、`confirmed_ref`、`current_turn_confirmation` 的差异。
3. 修改 `requirement-review/SKILL.md`：
   - 把缺少 loop/policy 的高风险 confirmed decision 判为 blocker。
4. 修改 `guru_gate.py confirm`：
   - 写入 `confirmation_scope`、`allowed_next_action`、`prompt_summary`、`user_quote`、`turn_ref`。
   - 旧 record 兼容显示。

### P2 Review record 写入一致性

1. 已检查 implementation review record 的单一 writer：`guru_review_record.py` 已负责 `review-records/implementation-reviews.jsonl` schema / append / verdict 校验。
2. 本轮不改 `record-review overview/detail` 的 task.json schema，不迁移 overview/detail 到 jsonl；本次事故根因是 start/implementation/commit 生命周期缺硬闸和 Brainstorm 证据模型不足，不是 implementation review writer 不存在。
3. `check-commit` 第一版保守读取最新 clean implementation review record 的 `target_paths`；缺记录或 staged scope 无法证明属于 reviewed slice 时 fail-closed。

### P3 模板镜像同步

1. 同步 `guru-template/...` 与 `packages/cli/src/templates/guru/...`。
2. 对 workflow 同步 `guru-template/workflows/guru-*-workflow.md` 与 `packages/cli/src/templates/guru/workflows/guru-*.md`。
3. 对 specs 同步所有 `guru-*` 平台的 `gate-confirmation-model.md`。

## 3. 预计改动文件

| 类别 | 文件 |
| --- | --- |
| Gate | `guru-template/overlay/verify/guru_gate.py`、`packages/cli/src/templates/guru/overlay/verify/guru_gate.py` |
| Supervise | `guru-template/overlay/verify/guru_supervise.py`、`packages/cli/src/templates/guru/overlay/verify/guru_supervise.py` |
| Review record | `guru-template/overlay/verify/guru_review_record.py`、`packages/cli/src/templates/guru/overlay/verify/guru_review_record.py` |
| Hooks | `guru-template/overlay/hooks/platform/block-unstarted-commit.sh`、`packages/cli/src/templates/guru/overlay/hooks/platform/block-unstarted-commit.sh` |
| Apply / hook registration | `guru-template/overlay/apply.sh`、`packages/cli/src/templates/guru/overlay/apply.sh` |
| Config snippets | `guru-template/overlay/config-snippets/config.hooks.yaml`、`guru-template/overlay/config-snippets/claude-settings.hooks.json`、新增 `guru-template/overlay/config-snippets/codex-hooks.hooks.json` and package mirrors |
| Skills | `guru-template/overlay/agents-skills/requirement-writing/SKILL.md`、`guru-template/overlay/agents-skills/requirement-review/SKILL.md` and package mirrors |
| Workflows | `guru-template/workflows/guru-*-workflow.md`、`packages/cli/src/templates/guru/workflows/guru-*.md` |
| Specs | `guru-template/specs/guru-*/harness/gate/gate-confirmation-model.md` and package mirrors |
| Tests | existing Guru overlay tests / CLI template tests / targeted new fixtures |

## 4. Impact Analysis 待办

在编辑任何函数、类或方法前，必须按 AGENTS.md 运行 GitNexus impact analysis 并报告影响面。优先目标：

1. `cmd_check`
2. `cmd_status`
3. `auto`
4. `_brainstorm_evidence_problems`
5. `cmd_confirm`
6. `build_plan` / `run_action` or equivalent `guru_supervise.py` implement/check entry
7. `append_record` or relevant review record writer if touched

若 GitNexus 工具不可用，先运行项目内 GitNexus CLI 查询或说明阻塞，再选择最小安全替代。

## 5. 验证命令

基础语法：

```bash
python3 -m py_compile guru-template/overlay/verify/guru_gate.py
python3 -m py_compile guru-template/overlay/verify/guru_supervise.py
python3 -m py_compile guru-template/overlay/verify/guru_review_record.py
bash -n guru-template/overlay/hooks/platform/block-unconfirmed-start.sh
bash -n guru-template/overlay/hooks/platform/block-unstarted-commit.sh
jq empty guru-template/overlay/config-snippets/claude-settings.hooks.json
jq empty guru-template/overlay/config-snippets/codex-hooks.hooks.json
```

模板一致性：

```bash
rg -n "check-commit|check-implementation|START_READY|Question Loop Log|Question Policy|block-unstarted-commit|codex-hooks" guru-template packages/cli/src/templates/guru
```

事故回归：

```bash
# fixture should create a planning Guru task, make start gate green, stage code, then prove check-commit/git commit is blocked before task.py start.
# apply smoke should prove Claude settings and Codex hooks.json both receive block-unstarted-commit when the target has .claude/.codex.
```

仓库级检查：

```bash
git diff --check
```

如测试入口可用，优先运行现有 Guru overlay/CLI regression tests；否则记录缺失测试入口并用 targeted smoke commands 覆盖。

## 6. 回退点

1. 如果 commit hook 命令位识别误伤，保留脚本但从 hook registration 中撤下；`check-commit` 仍可手动执行。
2. 如果 Brainstorm 新 gate 对历史 task 误伤，限制为新 task 或 confirmation refresh 时生效。
3. 如果 review_runs 加锁实现风险过大，先只加冲突检测和明确失败，迁移 jsonl 留后续任务。
4. 如果 Codex PreToolUse 在某个宿主版本不可用，保留 `.codex/hooks.json` 注册和用户提示，但不得降低 `guru_gate.py check-commit` / `guru_supervise.py` 的 fail-closed 规则。

## 7. 完成标准

1. 未 start 直接实现/提交路径被自动拦截。
2. `guru_gate.py check` 的输出不再可被合理解读为实现/提交放行。
3. Brainstorm 高风险 confirmed decision 必须有 loop/policy 证据。
4. `guru_supervise.py implement/check/implement-check` 在 planning 状态 fail-closed。
5. 源模板和打包镜像一致。
6. 自审无 blocker / should-fix。

## 8. 执行记录

### 8.1 已落地改动

- `guru_gate.py`：新增 `check-start`、`check-implementation`、`check-commit`；`check` 降为 deprecated `check-start` alias；`status/check-start` 明确输出 `START_READY` 只允许 `task.py start`。
- `guru_gate.py`：`Brainstorm Evidence` 对高风险 confirmed decision 强制要求结构化 `Question Loop Log` 或 `question_policy: evidence_only|mixed`；`evidence_only` 禁止产出 `user_confirmed*`。
- `guru_gate.py confirm`：新 confirmation record 写入 `confirmation_scope`、`allowed_next_action`、`prompt_summary` 和可用的 `turn_ref`；旧记录只按 legacy 显示。
- `guru_supervise.py`：`implement`、`check`、独立入口 `implement-check` 都在启动 worker 前调用 `check-implementation`，planning 状态 fail-closed。
- 新增 `block-unstarted-commit.sh`：只识别命令位 `git commit`，调用 `guru_gate.py check-commit`，避免 `echo`/文档/grep 误伤。
- `block-unstarted-commit.sh`：补强命令位识别，覆盖 `git -C . commit`、`command git commit`、`env FOO=bar git commit` 等真实执行形态，同时不把 `command -v git` 查询误判成提交。
- Claude overlay：安装并注册 `.claude/hooks/block-unstarted-commit.sh`。
- Codex overlay：新增 `codex-hooks.hooks.json`，`apply.sh` 在目标已有 `.codex/` 时安装 `.codex/hooks/block-unstarted-commit.sh` 并幂等合并 `.codex/hooks.json`。
- Workflow/spec/skill：四端 workflow 和 gate-confirmation-model 均明确 `START_READY`、`check-implementation`、`check-commit` 的边界；requirement writing/review skill 补齐 Question Loop / Question Policy 合同。
- Python 3.9 compatibility：`guru_gate.py` 补齐 `from __future__ import annotations`，避免 `str | None` annotation 在 Python 3.9 运行入口时崩溃；源模板和 CLI 镜像同步。
- Mirror：以上改动已同步到 `packages/cli/src/templates/guru/...`。

### 8.2 验证证据

- `python3 -m py_compile guru-template/overlay/verify/guru_gate.py guru-template/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_review_record.py packages/cli/src/templates/guru/overlay/verify/guru_gate.py packages/cli/src/templates/guru/overlay/verify/guru_supervise.py packages/cli/src/templates/guru/overlay/verify/guru_review_record.py`：通过。
- `bash -n` 覆盖 source/package 的 `apply.sh`、`apply_test.sh`、`block-unconfirmed-start.sh`、`block-unstarted-commit.sh`：通过。
- `jq empty` 覆盖 source/package 的 `claude-settings.hooks.json`、`codex-hooks.hooks.json`：通过。
- `bash guru-template/overlay/tests/apply_test.sh`：63 通过 / 0 失败；新增场景 19 验证 Codex hook 安装、用户 hook 保留和二跑幂等。
- Lifecycle fixture：构造 `check-start=0` 的 planning task，验证 `check-implementation=2`、`check-commit=2`、`guru_supervise.py implement-check --dry-run=2`。
- Brainstorm fixture：有 confirmed decision 但缺 `Question Loop Log` / `Question Policy` 时，`guru_gate.py requirements` 返回 2，并输出对应缺口。
- Commit hook fixture：`git commit -m test` 触发 `check-commit` 并 exit 2；`echo git commit -m test` 不触发 gate，exit 0。
- Commit hook parser smoke：`git commit`、`git -C . commit`、`command git commit`、`env FOO=bar git commit` 均触发 gate；`echo git commit`、`command -v git commit` 不触发。
- Python 3.9 smoke：`python3.9 guru-template/overlay/verify/guru_gate.py --help` 与 package mirror 能执行到用法输出，不再因 annotation import 崩溃；`python3.9 guru-template/overlay/verify/guru_supervise.py --help` 与 package mirror 返回 argparse help。
- `git diff --check`：通过。
- Source/package mirror `diff -q`：通过。

### 8.3 trellis-check 修复记录

- Review 发现 `guru-template/overlay/verify/tests/run_tests.sh` 的 good PRD 夹具仍缺 `Question Loop Log` / `Question Policy`，导致新增 Brainstorm Evidence gate 把大量后续 lifecycle / implement-check 夹具短路；已补齐结构化 `Question Loop Log`，并新增 `mixed` / `evidence_only` 正例与“缺 loop/policy 必拦”反例。
- Review 发现新增 lifecycle split 和 commit gate 的事故回归证据不够集中；已在 `run_tests.sh` 增加 `check-start` / `check-implementation` / `check-commit` / `block-unstarted-commit.sh` 的 planning 与 in_progress 回归夹具。
- Review 发现 `run_implement_check` packet/preflight 单元块被新增 lifecycle gate 短路；已在对应 Python 夹具内 stub `_guru_gate_check_implementation`，让 lifecycle 由独立 shell fixture 覆盖，packet/preflight 测试继续验证自身目标。
- Source fixture 已同步到 `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`，`pnpm --filter @devsc/trellis sync:guru:check` 验证无 mirror 漂移。
- Full test 修复：`packages/cli/test/guru/guru-bundled.test.ts` 的 supervisor fixture 已改成真实 `in_progress` + start gate ready 的 light Guru task，避免 dry-run 测试被 `check-implementation` 短路；`marketplace/workflows/native/workflow.md` 已同步 `packages/cli/src/templates/trellis/workflow.md` 的 one-question loop 规则；验证 `pnpm test` 在 bundled arm64 Node 下通过。

### 8.4 requirements / design review-before-confirm 增量

- 用户确认 DEC-019F-002：requirements confirm 前必须先跑 requirements review 到无 medium+ 问题；overview/detail write 后必须先跑各自 review 到无 medium+ 问题，再进入下一阶段或请求用户确认。
- 已实现：
  - `guru_gate.py confirm requirements` 调用 `_block_requirements_review("confirm", task_dir)`；missing / deferred / blocked / stale / 非法 status 全部返回 BLOCK，不再只是 warning。
  - `guru_gate.py check-start` 在人工确认与 overview/detail review 证据之外，新增 clean/current requirements review 前置，防止手写确认绕过。
  - `guru_gate.py status` 把 requirements review 缺口作为 `confirm requirements` 前置 next action，避免状态页诱导用户直接确认。
  - `guru_supervise.py --adversarial requirements` 对 `REQ_BLOCKER`、缺少 verdict、worker skip/deferred、`adversarial_enabled=false` 均返回非 0，同时把 `requirements_review.status` 记录为 `blocked` 或 `deferred`；只有 `review_result=clean/requirements-ready` 返回成功。
  - `guru_review_record.py` 新增 target content digest，`check-commit` 使用 latest clean implementation review 的 `reviewed_target_digest` 对比当前 staged index digest，避免只凭 target path 放行。
  - `check-commit` 只把当前 `task_dir` 下的任务产物视为 task artifact，不再全局豁免 `.trellis/workspace/`。
  - commit hook parser 覆盖多命令、wrapper、嵌套 shell 与 gate 缺失 fail-closed 场景；Codex hook 安装不再依赖目标项目预先存在 `.codex/`。
  - `run_tests.sh` / `guru-bundled.test.ts` 已加入 missing / deferred / blocked / stale requirements review、invalid `question_policy`、staged target digest、workspace artifact exemption、Codex hook 安装等回归。
  - 四端 workflow、四端 gate-confirmation-model 和 README 均同步 review-before-confirm：requirements clean/current 后才能确认；overview/detail write/repair 后必须立刻 review/fix 到当前 digest 双 clean，其中至少一次 adversarial clean，detail clean 后才请求用户确认。

### 8.5 当前验证证据

- `python3 -m py_compile` 覆盖 source/package 的 `guru_gate.py`、`guru_supervise.py`、`guru_review_record.py`：通过。
- `bash -n` 覆盖 source/package 的 `apply.sh`、`apply_test.sh`、`block-unconfirmed-start.sh`、`block-unstarted-commit.sh`：通过。
- Source/package changed mirror `diff -q`：通过。
- `bash guru-template/overlay/tests/apply_test.sh`：67 通过 / 0 失败。
- `bash guru-template/overlay/verify/tests/run_tests.sh`：336 通过 / 0 失败。
- `pnpm --filter @devsc/trellis sync:guru:check`：通过，Guru bundled mirror 无漂移。
- `pnpm --dir packages/cli exec vitest run test/guru/guru-bundled.test.ts`：62 通过 / 0 失败。
- `pnpm --filter @devsc/trellis test`：51 个测试文件 / 1297 个测试全部通过。
- OCR 第一轮发现的真实 high/medium 问题已修复；当前轮仍需在最终 lint/typecheck/diff 后重新运行 OCR 复审，确认无剩余中等及以上问题。
