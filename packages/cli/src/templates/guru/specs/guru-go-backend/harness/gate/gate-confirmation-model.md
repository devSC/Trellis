# Gate 确认模型 - SSOT

> 本文件是 Guru planning 阶段 Gate 模型的单一来源。workflow 只保留流程摘要与命令入口；`guru_gate.py` 实现本文定义的结构底线、review 证据与人工确认快照。

## 1. 适用范围

本文覆盖从 planning 进入 implementation 前的 Guru Gate：

- `requirements` - 需求 Gate：结构检查 + 需求发现/Domain Grill + opposite-provider adversarial requirements review + 用户确认。
- `overview` - 概要设计 Gate：结构检查 + 当前 digest 下两次 clean review（至少一次 opposite-provider adversarial clean），自动通过，不需要用户确认。
- `detail` - 详细设计 Gate：结构检查 + 当前 digest 下两次 clean review（至少一次 opposite-provider adversarial clean），随后用户确认。

实现 Gate、代码质量检查、测试证据和 commit 前审核属于实现/审核阶段，由 implementation trace 合同、平台 golden-path、实现 review skill、`guru_supervise.py implement-check` 与 `trellis-check` 承载。planning Gate 的成功状态只叫 `START_READY`，只能授权下一步运行 `task.py start`。

Universal delivery policy is the entry contract for every task type, not only Lite: `small_inline` targets first scoped code without task ceremony, `micro_task` requires explicit path scope, `lite_task` requires compact task evidence plus at most one confirmation batch, and `full_chain` is mandatory for high or unknown-high-signal work. The executable policy lives in `.trellis/scripts/guru/guru_delivery_policy.py` with `.trellis/policy/delivery-policy.json`; workflows may summarize it, but must not create a second route table. High/full-chain start must use the guarded `guru_task.py start` entry once installed; direct official `task.py start` is only advisory evidence, never proof of hard enforcement.

当前 Custom-only Start Guard 的 capability truth 必须按以下边界解释：

- guarded entry 的 task/slice/risk/envelope digest、session identity、lifecycle CAS、exclusive lock、hook outcome 和 compensation 是结构与生命周期层面的 enforced binding。
- 平台可信的用户身份来源当前不可用。`task.json`、本地 confirmation record、attestation 或自称 `actor_type=human` 的 JSON 都是 agent-writable，不得作为 trusted confirmation。
- Full 的 digest-bearing `implement.md` 必须在唯一 `GURU:RISK_DECISION_INVENTORY` JSON fence 中保存按 slice 分组的完整 required critical/high decision universe。每项只能是 `unresolved|resolved`；`resolved` 必须带非空 `resolution.choice/evidence`。这个 inventory 随 detail digest 一起 review/confirm，缺失、重复 marker、重复 decision id、未知状态或未绑定 slice/invariant 一律 fail closed。
- `RiskDecisionPacketV1` 必须同时绑定当前 `detail_artifact_digest`、完整 `decision_universe_digest`、由 universe 确定性筛出的 unresolved `decision_items`、`decision_set_digest` 与 `confirmation_required`。Start Guard 从已确认 `implement.md` 重建 universe；删除、截断、替换、重排或只重算 packet/envelope/request hash 都不得消除阻塞决策。
- 集合非空时 Start Guard 必须以 `CapabilityUnavailable` / `ConfirmationMissing` fail closed；本地 attestation 即使与 task record 完全自洽也不能放行。只有当前 detail inventory 显式为空，或其中每个 required critical/high 决策都带 resolution evidence，重新生成的 blocking packet 才能为空；启动仍须通过当前 detail confirmation 与 `guru_gate.py check-start`。
- execution envelope 的 attestation 字段仅为未来外部 identity verifier 兼容位；当前能力下不得宣称 platform-signed、platform-trusted 或 hard human identity。direct official `task.py start` 仍只产生 advisory evidence。

## 2. 机制边界

| 机制 | 作用 | 可否替代其他机制 |
|------|------|------------------|
| 结构 Gate | `guru_gate.py requirements/overview/detail` 复查产物结构、编号纪律、引用闭合与最低可机检条件。 | 不替代语义 review 或用户确认。 |
| Domain Grill | 需求发现阶段的对抗式领域拷问，磨尖术语、边界、失败路径、状态/owner 和红线，并把已确认决策回写需求产物或长期知识。 | 不替代结构 Gate，不单独作为 post-draft Gate。 |
| requirements adversarial review | `confirm requirements` 前的 opposite-provider 需求复核：先查 `prd.md`、正式需求包、task metadata/jsonl、task context 与 repo evidence，再输出 `route_class=REQ_BLOCKER` 或 `review_result=clean/requirements-ready`。 | 不写 `review_runs`，不形成 requirements clean streak，不替代人工确认。 |
| review evidence | overview/detail review worker 把当前 artifact digest 下的 clean/findings 结果写入 `task.json.guru_gates.review_runs`；双 clean 中至少一条 clean reviewer 必须包含 `adversarial`。 | 不替代 requirements/detail 的人工确认。 |
| confirm | 用户确认 requirements 或 detail 当前产物可以作为后续输入，并写入确认快照。 | 不替代结构 Gate 或 review evidence。 |
| `check-start` | 复跑 requirements/overview/detail 结构 Gate、review evidence 与人工确认快照。 | 只产生 `START_READY`，不替代 `task.py start`、实现 Gate 或 commit Gate。 |
| `check-implementation` | 在 `check-start` 仍有效的基础上要求 `task.json.status == in_progress`。 | 只授权实现/质检 worker 启动，不授权 commit。 |
| `check-commit` | 在 `check-implementation` 通过后检查 staged scope 与最新 clean implementation review record。 | 只说明当前 staged scope 可提交，仍需用户明确 commit 确认。 |

完整 planning 跃迁顺序：

```text
requirements writing/review + Domain Grill -> guru_supervise.py --adversarial requirements <task_dir> -> guru_gate.py confirm requirements
overview writing -> overview review/fix loop -> two clean current-digest reviews (one adversarial opposite-provider clean) -> auto pass
detail writing -> detail review/fix loop -> two clean current-digest reviews (one adversarial opposite-provider clean) -> guru_gate.py confirm detail
```

`guru.supervision.adversarial_enabled: false` 可临时关闭 `guru_supervise.py --adversarial ...` 的 opposite-provider worker；关闭后 `guru_gate.py` 按配置动态判定：requirements 不再强制 opposite-provider adversarial review，overview/detail 不再要求 adversarial reviewer，但仍要求当前 digest、双 clean review、用户确认以及没有 blocked/medium+ 当前证据。

`confirm overview` 不是正常路径，必须失败并提示改用 `record-review overview`。

## 3. 人工确认边界

Guru planning 只保留两个阶段性人工确认：

- `requirements`：确认用户可感知行为、失败路径、验收口径、术语和产品边界已定。
- `detail`：在 overview/detail 都已有当前 digest 双 clean review（各自至少一次 opposite-provider adversarial clean）后，确认可编码合同、测试映射、不得补造清单和实现切片已定。

硬边界确认另行存在：commit、archive、finish-work、publish、外部系统写入和其他不可逆操作仍必须等待用户明确确认。

`guru_gate.py confirm` 写入的确认记录必须带作用域：

```json
{
  "confirmation_scope": "requirements_gate_only|detail_gate_only",
  "allowed_next_action": "overview_design|task_start",
  "prompt_summary": "...",
  "turn_ref": "..."
}
```

- `requirements` 确认的上限是继续概要/详细 planning，不允许开始实现。
- `detail` 确认的上限是运行 `task.py start`，不允许开始实现 worker 或 commit。
- 旧任务缺少这些字段时只能按 legacy confirmation 显示；重新确认必须写入新字段。

## 4. Gate 覆盖范围

| Gate | 完成条件 | artifact digest 覆盖范围 | 决策含义 |
|------|----------|--------------------------|----------|
| `requirements` | `guru_gate.py requirements <task_dir>` 通过 + `guru_supervise.py --adversarial requirements <task_dir>` 输出 `review_result=clean/requirements-ready` + `guru_gate.py confirm requirements <task_dir>` | `prd.md` | 需求行为、失败路径、验收口径、术语边界已定。 |
| `overview` | `guru_gate.py overview <task_dir>` 通过 + 两个不同 `run_id` 的当前 digest clean review；默认其中至少一条 reviewer 含 `adversarial`，`guru.supervision.adversarial_enabled=false` 时不要求 | `prd.md` + `design_package/README.md` + `design_package/design-main.md`；light 链为 `prd.md` + `design.md` | owner、架构归属、技术决策承接和详细设计索引已定。 |
| `detail` | `guru_gate.py detail <task_dir>` 通过 + 两个不同 `run_id` 的当前 digest clean review；默认其中至少一条 reviewer 含 `adversarial`，`guru.supervision.adversarial_enabled=false` 时不要求 + `guru_gate.py confirm detail <task_dir>` | overview 覆盖范围 + `design_package/chapters/*.md` + `implement.md`；light 链为 `prd.md` + `design.md` + `implement.md` | 可编码合同、测试映射、不得补造清单和实现切片已定。 |

## 5. Digest 与失效规则

确认快照与 review 证据都绑定 artifact digest。

规则：

- `requirements` digest 只覆盖需求产物。
- `overview` digest 覆盖需求产物和概要主定义。
- `detail` digest 覆盖需求产物、概要主定义、详细设计和实现计划。
- 当前产物 digest 改变后，旧 review 记录和确认快照只作为历史证据，不再放行当前 Gate。
- clean streak 必须从当前 digest 的 review_runs 重放计算；不得信任手写的 `clean_streak`、`auto_passed` 或聊天结论。

失配时回到最早失配阶段。需求变更会使 overview/detail review 证据和 detail 确认失效；概要变更会使 detail review 证据和 detail 确认失效。

## 6. Review Evidence 模型

overview/detail review evidence 存在 `task.json.guru_gates.review_runs`：

```json
{
  "guru_gates": {
    "requirements": {
      "confirmed_by": "devSC",
      "confirmed_at": "2026-06-18T00:00:00+08:00",
      "artifact_digest": "<requirements digest>"
    },
    "detail": {
      "confirmed_by": "devSC",
      "confirmed_at": "2026-06-18T00:30:00+08:00",
      "artifact_digest": "<detail digest>"
    },
    "review_runs": {
      "overview": [
        {
          "run_id": "overview-20260618-a",
          "reviewer": "clean-context-adversarial-claude",
          "recorded_at": "2026-06-18T00:10:00+08:00",
          "artifact_digest": "<overview digest>",
          "result": "clean",
          "max_severity": "low",
          "evidence": "overview review found no medium+ issues"
        }
      ],
      "detail": [
        {
          "run_id": "detail-20260618-a",
          "reviewer": "clean-context",
          "recorded_at": "2026-06-18T00:20:00+08:00",
          "artifact_digest": "<detail digest>",
          "result": "findings",
          "max_severity": "medium",
          "finding_class": "DETAIL_DEFECT",
          "evidence": "UNIT test mapping missing for BHV-002"
        }
      ]
    }
  }
}
```

命令：

```bash
python3 .trellis/scripts/guru/guru_gate.py record-review overview <task_dir> \
  --result clean \
  --max-severity low \
  --reviewer clean-context \
  --run-id overview-review-20260618-a \
  --evidence "no medium+ overview findings"
```

规则：

- `record-review` 只支持 `overview` 和 `detail`；不得添加 requirements clean streak。
- `clean` 只允许 `max_severity=none|low`，且不得写 `finding_class`。
- `findings` 必须是 `max_severity=medium|high|critical`，且必须写 `finding_class`。
- `finding_class` 只用于路由：`REQ_BLOCKER`、`OVERVIEW_DEFECT`、`DETAIL_DEFECT`、`IMPLEMENT_DEFECT`、`PROCESS_DEFECT`。
- 两次 clean 必须来自当前 digest 下两个不同 `run_id`。默认当前 clean streak 中至少一条 clean 记录的 `reviewer` 包含 `adversarial`（推荐形如 `clean-context-adversarial-<provider>`）；若 `guru.supervision.adversarial_enabled=false`，只要求双 clean，不要求 adversarial reviewer。
- requirements 阶段通过需求发现 / Domain Grill / adversarial review 暴露 blocker 或 clean/ready 结论；requirements review 不写 `review_runs`，不得添加 requirements clean streak，但 `confirm requirements` / `check-start` 必须要求当前 digest 的 clean/current requirements review。
- medium+ findings 会打断当前 clean streak；后续需要重新得到两个不同 run-id 的 clean。

## 7. Automation Driver

planning 阶段使用 `guru_supervise.py` 的最小 channel 驱动，不引入新 task status、队列、数据库或调度器。

```bash
python3 .trellis/scripts/guru/guru_supervise.py overview <task_dir>
python3 .trellis/scripts/guru/guru_supervise.py detail <task_dir>
python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>
python3 .trellis/scripts/guru/guru_supervise.py --adversarial overview <task_dir>
python3 .trellis/scripts/guru/guru_supervise.py --adversarial detail <task_dir>
```

stop conditions：

- requirements adversarial review：先查 code/tests/config/docs/.trellis/spec/CONTEXT.md/CONTEXT-MAP.md/ADRs，再问产品问题；medium+ 需求阻断输出 `route_class=REQ_BLOCKER`，回到 requirements repair；低严重度措辞 nit 不阻断；clean 输出 `review_result=clean/requirements-ready`，并停在 confirm requirements 前。
- `REQ_BLOCKER`：回到 requirements；需求 digest 变更后 overview/detail 下游证据不得视为当前，必须重跑。
- `OVERVIEW_DEFECT`：修复 overview 产物并重新 review。
- `DETAIL_DEFECT`：修复 detail 产物并重新 review。
- `PROCESS_DEFECT`：修复受影响流程产物并重新 review。
- 当前 digest 两个 clean review，且至少一条为 opposite-provider adversarial clean：overview 自动通过；detail 停下等待用户确认。
- 工具失败、timeout、killed：向主会话暴露 blocker。

实现阶段使用：

```bash
python3 .trellis/scripts/guru/guru_gate.py check-implementation <task_dir>
python3 .trellis/scripts/guru/guru_supervise.py implement-check <task_dir>
```

`guru_supervise.py implement|check|implement-check|implementation-review` 必须在启动 worker 前自动执行 `check-implementation`；若任务仍是 `planning`，fail-closed，不启动 worker。`implement-check` 复用实现 writing skill 与实现 review skill，干净后停在最终验证和 hard-boundary confirmation，不写新的 implementation `guru_gates`。`implementation-review` 是 check-only 结构化记录入口，只跑 deterministic checks + check worker，不启动 implement worker；它必须在 deterministic checks 前固定目标摘要，在 checks 后确认摘要未变，把 run/target/摘要/target paths/deterministic results/provider 绑定写入 `review_invocation_contract` 后才启动 worker，并在 worker 返回后再次确认摘要未变，最终 record 只能使用该启动前摘要。实现 review record 由 `review-records/implementation-reviews.jsonl` 承载，commit gate 读取最新 clean record。

## 8. Legacy design-grill 兼容

旧 `grill-done` / `grill-skip` 命令可以保留，用来读取或记录历史项目的兼容审计信息。但在新模型下：

- overview/detail 的放行不得依赖旧 grill 记录。
- 旧 grill 记录不得 unblock 或 block `guru_gate.py auto` / `guru_gate.py check-start`；`guru_gate.py check` 只是 `check-start` 的兼容别名，不能被解释成实现或提交许可。
- `status` 可以把旧 grill 状态显示为 legacy context，但下一步提示必须以 requirements confirm、review_runs、detail confirm 为准。

Domain Grill 的长期位置是需求发现阶段，而不是 overview/detail 之后的额外 Gate。

## 9. strict 与 soft

`guru.gate_mode` 控制人工确认写入通道：

- `strict`：默认模式。用户本人在交互式终端运行 `guru_gate.py confirm requirements|detail`；agent 不得代跑。
- `soft`：用户在本轮对话中明确确认后，agent 可以用 `--via-agent --user-quote "<用户确认原话>"` 代跑，并在 `task.json` 留审计痕迹。

无论 strict 还是 soft，结构 Gate 复跑、review digest、confirm artifact digest、`task.py start` 前的 `guru_gate.py check-start` 都必须生效。`check-start` 通过后的状态名是 `START_READY`：下一步只允许 `task.py start`；实现 worker 必须再过 `check-implementation`，提交必须再过 `check-commit`。

## 10. 失配恢复流程

先查看状态：

```bash
python3 .trellis/scripts/guru/guru_gate.py status <task_dir>
```

按最早缺口恢复：

1. 缺结构产物或结构 Gate 不通过：回到对应 writing/review 阶段修产物。
2. 需求未确认或需求确认快照失配：先运行 `guru_supervise.py --adversarial requirements <task_dir>`，clean/ready 后再运行 `confirm requirements`；若输出 `REQ_BLOCKER`，修订需求并重跑下游 overview/detail 证据。
3. overview 缺当前 digest 双 clean或缺 adversarial clean：运行 `guru_supervise.py overview <task_dir>`，缺 adversarial 时运行 `guru_supervise.py --adversarial overview <task_dir>`。
4. detail 缺当前 digest 双 clean或缺 adversarial clean：运行 `guru_supervise.py detail <task_dir>`，缺 adversarial 时运行 `guru_supervise.py --adversarial detail <task_dir>`。
5. detail 未确认或确认快照失配：双 clean（含 adversarial）后重新运行 `confirm detail`。
6. `guru_gate.py check-start <task_dir>` 通过后只允许 `task.py start`；不得把 `START_READY` 当成实现、review worker、commit 或发布许可。
7. 需要启动实现/质检 worker：确认 `task.py start` 已把 `task.json.status` 置为 `in_progress`，并运行 `guru_gate.py check-implementation <task_dir>`。
8. 需要提交：只 stage 本任务实现范围内的文件，确保最新 `review-records/implementation-reviews.jsonl` 为 clean；若只缺提交候选的结构化 review record，先运行 `guru_supervise.py implementation-review <task_dir> --staged`，再运行 `guru_gate.py check-commit <task_dir>`。
9. `guru_gate.py check <task_dir>` 仅为旧命令兼容 alias，语义等同 `check-start`。

最终检查：

```bash
python3 .trellis/scripts/guru/guru_gate.py check-start <task_dir>
python3 .trellis/scripts/guru/guru_gate.py check-implementation <task_dir>
python3 .trellis/scripts/guru/guru_gate.py check-commit <task_dir>
```
