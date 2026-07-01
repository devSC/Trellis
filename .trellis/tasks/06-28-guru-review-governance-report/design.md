# Guru Review Governance Root-Cause Repair Design

## 1. 目标

基于 `session-019f171a-root-cause-repair-plan.md` 落地 Guru/Trellis 流程防线，防止以下事故复现：

1. full-chain task 仍处于 `planning`，但 agent 直接实现和提交。
2. `Brainstorm Evidence` 只有结构标签，没有真实 one-question loop 或 evidence-only policy。
3. `guru_gate.py check` 被误解为实现/提交放行，而非 `task.py start` 前置。

本设计修 Guru/Trellis 工具、模板、workflow、skills 和测试，不评价 Himora 业务提交 `b841e5dd` 的代码正确性。

## 2. 当前实现事实

| 区域 | 当前事实 | 设计影响 |
| --- | --- | --- |
| `guru_gate.py` | `cmd_check` 只检查 requirements/overview/detail/review/confirm，输出“放行”；`auto` 在 planning 只做渐进 gate | 需要把 start / implementation / commit 目的拆开，保留兼容 alias。 |
| `config.hooks.yaml` | 只把 `guru_gate.py check` 接到 `before_start` | 只能拦未过 gate 的 `task.py start`，拦不住跳过 start 直接 commit。 |
| Claude hook wiring | `apply.sh` 只安装 `block-unconfirmed-start.sh` 等共享 hook，并通过 `claude-settings.hooks.json` 合并到 `.claude/settings.json` | 新 commit hook 必须加入 `SHARED_HOOKS` / `INSTALLED_HOOKS` 和 Claude settings snippet，否则只新增脚本不会生效。 |
| Codex hook wiring | `.codex/hooks.json` 当前只有 `UserPromptSubmit` workflow-state 注入；没有 Bash/PreToolUse commit guard | 019f171a 事故发生在 Codex，会话级硬闸必须覆盖 Codex，不能只修 Claude Code。 |
| `block-unconfirmed-start.sh` | 只识别命令位 `task.py start` | 需要新增独立 commit hook，而不是塞进 start hook。 |
| `guru_supervise.py` | implement/check prompt 禁止 commit，但入口未硬性要求 status=in_progress | 入口必须 fail-closed；prompt 不能作为安全边界。 |
| `guru_review_record.py` | 已有 packet/implementation review record schema 与唯一 writer | 实现期审查不要另造记录格式；commit gate 读取这个通道。 |
| `requirement-writing/review` | 已禁止模糊“好/继续”批量确认，但没有强制 `Question Loop Log` / `Question Policy` | 需要补模板和 gate 校验。 |
| workflow templates | Guru workflow 被 `guru-template/overlay/apply.sh` 从 `guru-template/workflows/guru-*-workflow.md` 安装到目标 `.trellis/workflow.md` | workflow 文案要改源模板和 CLI 镜像，不只改当前 `.trellis/workflow.md`。 |

## 3. 设计原则

1. `check-start` 只回答“能否运行 `task.py start`”，不能隐式回答“能否实现/提交”。
2. `task.json.status == in_progress` 是实现和提交的最低硬条件。
3. `Brainstorm Evidence` 需要可审计证据，不接受只补齐标签。
4. 人工确认必须带作用域和下一步上限，不能跨 gate 复用。
5. Hook 是提前拦截；`guru_gate.py check-commit` 是可复跑的命令级 SSOT。
6. 源模板和打包镜像必须同改同测。
7. `requirements` / `overview` / `detail` 的 write 与 confirm 边界必须由 review 证据硬隔离：requirements review clean/current 才能 confirm requirements；overview/detail write/repair 后必须先完成各自当前 digest review，detail 双 clean 后才能请求 confirm detail。

## 4. Lifecycle Gate 设计

### 4.1 命令拆分

新增命令：

```bash
python3 .trellis/scripts/guru/guru_gate.py check-start <task-dir>
python3 .trellis/scripts/guru/guru_gate.py check-implementation <task-dir>
python3 .trellis/scripts/guru/guru_gate.py check-commit <task-dir>
```

兼容：

- `guru_gate.py check` 保留，作为 `check-start` alias。
- alias 输出兼容提示：`[guru-gate:check] deprecated alias for check-start; START_READY only`。

### 4.2 状态规则

| Gate | 必要条件 | 成功语义 |
| --- | --- | --- |
| `check-start` | requirements confirmed、overview/detail review clean、detail confirmed、artifact digest 有效 | 只能运行 `task.py start` |
| `check-implementation` | `check-start` 仍有效、`task.json.status == in_progress`、传入 task 与 active task 一致或可由显式 task_dir 证明 | 可启动 implement/check worker |
| `check-commit` | `check-implementation` 通过、staged 范围属于 task、必要实现审查 clean | 可提交当前 staged scope |

`check-commit` 的第一版 staged scope 可采用保守策略：

1. 若没有 staged changes，fail。
2. 若 task 非 `in_progress`，fail。
3. 若存在 `review-records/implementation-reviews.jsonl` 且最后记录为 blocking/finding，fail。
4. 若没有 implementation review record，但 staged 只包含规划文档，fail；这是防止 planning 文档被当成交付提交。
5. 若无法判断 active task，fail 并要求显式传 task_dir。

### 4.3 Requirements Review 硬闸

`requirements_review` 不进入 `review_runs` clean streak，但它是 `confirm requirements` 和 `check-start` 的硬前置：

1. `guru_supervise.py --adversarial requirements <task_dir>` 只有解析到 `review_result=clean/requirements-ready` 才返回成功。
2. `route_class=REQ_BLOCKER`、缺 verdict、worker skip、`adversarial_enabled=false` 等都记录 `requirements_review.status=blocked|deferred`，并返回阻断。
3. `guru_gate.py confirm requirements` 在 `requirements_review` missing/deferred/blocked/stale 时返回 BLOCK，不进入人工确认写入。
4. `guru_gate.py check-start` 同样校验 clean/current `requirements_review`，防止手写/旧确认绕过。
5. `status` 的下一步提示优先指向 requirements review；只有 clean/current 后才提示用户运行 `confirm requirements`。

### 4.4 Overview / Detail Review-before-confirm

`guru_supervise.py overview|detail` 是默认 write/repair + review/fix 包装入口。若手动拆分 writing skill：

1. overview writing 完成后必须先运行 overview review，并用 `record-review overview` 写入当前 digest clean；未双 clean（含 adversarial）不得进入 detail writing。
2. detail writing 完成后必须先运行 detail review，并用 `record-review detail` 写入当前 digest clean；未双 clean（含 adversarial）不得请求 `confirm detail`。
3. `confirm overview` 继续禁止；overview 只通过 review gate 进入下一阶段。
4. `confirm detail` 已通过 `_review_state` 硬校验 overview/detail 双 clean，继续作为人工启动前收口。

## 5. Direct Commit Hook 设计

新增：

```text
guru-template/overlay/hooks/platform/block-unstarted-commit.sh
packages/cli/src/templates/guru/overlay/hooks/platform/block-unstarted-commit.sh
```

行为：

1. 从 PreToolUse JSON 中取 Bash command。脚本必须兼容 Claude/Codex 常见 payload：优先读 `tool_input.command`，必要时兼容等价 command 字段；解析失败时静默放过非 Bash 事件。
2. 用 `shlex` 只识别命令位 `git commit`，不误伤 `echo "git commit"`、文档编辑、grep。
3. 进入项目根后运行：

```bash
python3 .trellis/scripts/guru/guru_gate.py check-commit <resolved-task-dir>
```

4. 失败时退出 2，并提示：

```text
BLOCKED: Guru task is not ready to commit.
Run guru_gate.py status <task-dir>; if START_READY, run task.py start first.
```

注册：

- Claude Code：
  - `guru-template/overlay/apply.sh` 和 CLI 镜像的 `SHARED_HOOKS` / `INSTALLED_HOOKS` 必须安装 `block-unstarted-commit.sh` 到 `.claude/hooks/`。
  - `guru-template/overlay/config-snippets/claude-settings.hooks.json` 和 CLI 镜像必须在 `PreToolUse` `matcher=Bash` 下注册该脚本。
  - `apply.sh` 现有幂等合并逻辑会按 `INSTALLED_HOOKS` 过滤 snippet；因此新增脚本、`SHARED_HOOKS` 和 snippet 必须同改。
- Codex：
  - `apply.sh` 必须在目标存在 `.codex/` 时安装同一脚本到 `.codex/hooks/block-unstarted-commit.sh`，并幂等合并 `.codex/hooks.json` 的 `PreToolUse` `matcher=Bash` command。
  - 新增 `guru-template/overlay/config-snippets/codex-hooks.hooks.json` 及 CLI 镜像，避免把 Codex hook 注册逻辑硬编码在文档里。
  - `packages/cli/src/templates/codex/hooks.json` 当前是 Trellis 通用模板，不应直接塞 Guru 专属 hook；Guru overlay apply 负责在已安装 Guru 的项目中追加。
  - Codex hook 还依赖用户级 `[features].hooks = true` 和 `/hooks` trust；`apply.sh` 必须输出明确提示，但不能把这个提示当作硬闸本身。硬闸的可复跑 SSOT 仍是 `guru_gate.py check-commit`。

## 6. Brainstorm Evidence 设计

`prd.md` 中 `## Brainstorm Evidence` 需要新增二选一证据：

### 6.1 `Question Loop Log`

必须包含表格字段：

```text
oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update
```

Gate 规则：

1. 存在 `user_confirmed*` 的高风险 decision 时，必须能回指 `oq_id` 或 `decision_id`。
2. `好/继续/按推荐/已确认` 只有在最近一个未关闭 OQ 且只有一个 OQ 时可接受。
3. 多个 OQ 不能被一句模糊确认批量关闭。

### 6.2 `Question Policy`

允许 `question_policy: evidence_only` 或 `question_policy: mixed`。

Gate 规则：

1. `evidence_only` 只能产出 `evidence_ready`，不能产出 `user_confirmed*`。
2. `mixed` 必须列出哪些由证据回答，哪些由用户当前轮确认回答。
3. 原始 bug quote、TAPD 标题、历史需求文本只能作为 `source_quote` 或 `confirmed_ref`，不能作为 `current_turn_confirmation`。

## 7. Confirmation Scope 设计

`guru_gate.py confirm` 继续兼容旧字段，同时新增字段：

```json
{
  "confirmation_scope": "requirements_gate_only|detail_gate_only",
  "allowed_next_action": "overview_design|task_start",
  "prompt_summary": "...",
  "user_quote": "...",
  "turn_ref": "..."
}
```

兼容规则：

1. 旧 task 缺新字段时，status 显示 legacy confirmation；重新确认时写新字段。
2. `requirements` 的 `allowed_next_action` 不得超过 `overview_design`。
3. `detail` 的 `allowed_next_action` 不得超过 `task_start`。
4. `check-commit` 不读取人工 gate 的 `allowed_next_action` 作为提交许可。

## 8. Supervise Guard 设计

`guru_supervise.py` 对 `implement`、`check`、`implement-check` 增加入口前置：

1. 调用或复用 `guru_gate.py check-implementation` 的内部逻辑。
2. 若 status 非 `in_progress`，写入可审计失败记录或 stderr 明确说明，不启动 worker。
3. 对 `implement-check`，继续复用 `guru_review_record.py` 的 packet/review record 机制。

## 9. Review Record 写入设计

`guru_review_record.py` 已是 implementation review 的单一 writer。第一版不迁移 overview/detail record schema，但必须修两个问题：

1. `record-review overview/detail` 写 `task.json` 时采用原子读写，避免并发丢记录。
2. 同一 `artifact_digest + run_id` 不得重复写；冲突要 fail，而不是静默覆盖。

如果实现中发现 task.json review_runs 原子锁成本过高，可把 overview/detail 迁移到 jsonl 作为后续独立 task；但本任务至少要让并发写丢变成显式失败。

## 10. 模板同步范围

必须同步以下源和镜像：

| 源 | 镜像 |
| --- | --- |
| `guru-template/overlay/verify/guru_gate.py` | `packages/cli/src/templates/guru/overlay/verify/guru_gate.py` |
| `guru-template/overlay/verify/guru_supervise.py` | `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py` |
| `guru-template/overlay/verify/guru_review_record.py` | `packages/cli/src/templates/guru/overlay/verify/guru_review_record.py` |
| `guru-template/overlay/hooks/platform/*.sh` | `packages/cli/src/templates/guru/overlay/hooks/platform/*.sh` |
| `guru-template/overlay/config-snippets/config.hooks.yaml` | `packages/cli/src/templates/guru/overlay/config-snippets/config.hooks.yaml` |
| `guru-template/overlay/agents-skills/requirement-writing/SKILL.md` | `packages/cli/src/templates/guru/overlay/agents-skills/requirement-writing/SKILL.md` |
| `guru-template/overlay/agents-skills/requirement-review/SKILL.md` | `packages/cli/src/templates/guru/overlay/agents-skills/requirement-review/SKILL.md` |
| `guru-template/workflows/guru-*-workflow.md` | `packages/cli/src/templates/guru/workflows/guru-*.md` |
| `guru-template/specs/guru-*/harness/gate/gate-confirmation-model.md` | `packages/cli/src/templates/guru/specs/guru-*/harness/gate/gate-confirmation-model.md` |
| `guru-template/overlay/apply.sh` | `packages/cli/src/templates/guru/overlay/apply.sh` |
| `guru-template/overlay/config-snippets/claude-settings.hooks.json` | `packages/cli/src/templates/guru/overlay/config-snippets/claude-settings.hooks.json` |
| `guru-template/overlay/config-snippets/codex-hooks.hooks.json` | `packages/cli/src/templates/guru/overlay/config-snippets/codex-hooks.hooks.json` |

## 11. 回退策略

1. `check` alias 保留，现有 `before_start` 不断。
2. 新 hook 若误伤，可先从 `.claude/settings.json` / `.codex/hooks.json` 取消注册，但保留 `check-commit` 命令作为手动 gate。
3. Brainstorm 新规则只在重新跑 requirements gate 或新任务中生效；不回写 archived 历史任务。
4. 旧 confirmation record 缺 scope 字段时不立即 fail，但重新 confirm 后必须写新字段。
