# Gate 确认模型 - SSOT

> 本文件是 Guru planning 阶段人工 Gate 的确认模型单一来源。workflow 只保留流程摘要与命令入口；`guru_gate.py` 只实现本文定义的结构底线与留痕口径。

## 1. 适用范围

本文覆盖从 planning 进入 implementation 前的三道人工 Gate：

- `requirements` - 需求 Gate。
- `overview` - 概要设计 Gate。
- `detail` - 详细设计 Gate。

实现 Gate、代码质量检查、测试证据和 commit 前审核属于实现/审核阶段，由 implementation trace 合同、平台 golden-path、实现 review skill 与 `trellis-check` 承载。

## 2. 三类检查的边界

| 机制 | 作用 | 可否替代其他机制 |
|------|------|------------------|
| 结构 Gate | `guru_gate.py requirements/overview/detail` 复查产物结构、编号纪律、引用闭合与最低可机检条件。 | 不替代 review 或用户确认。 |
| design-grill | Gate 前对抗式拷问，磨尖术语、owner、边界、失败路径和红线，确认后把决策回写产物。 | 不替代结构 Gate、review 或 confirm。 |
| confirm | 用户确认当前阶段产物可以作为下一阶段输入，并写入 `task.json` 的 `guru_gates` 快照。 | 不替代结构 Gate 或 design-grill。 |

完整跃迁顺序固定为：

```text
writing -> review -> grill policy -> guru_gate.py confirm
```

## 3. 为什么三道 Gate 独立

`requirements`、`overview`、`detail` 的决策对象不同，不能用一次确认覆盖全部阶段：

- 需求 Gate 确认用户可感知行为、失败路径和验收口径是否已定。
- 概要 Gate 确认 owner 归属、架构边界、分层依赖和详细设计承接索引是否已定。
- 详细 Gate 确认可编码合同、测试映射、不得补造清单和实现切片是否已定。

因此三道 Gate 必须分别记录 grill 凭据与 `confirm`。`requirements` 必须是 `grill-done`；`overview` / `detail` 只有在 low-risk 非 full 策略下才允许 `grill-skip`。缺任一阶段有效凭据时，不得 `task.py start`。

## 4. Gate 覆盖范围

| Gate | 完成命令 | 确认快照覆盖范围 | 决策含义 |
|------|----------|------------------|----------|
| `requirements` | `guru_gate.py grill-done requirements <task_dir>` + `guru_gate.py confirm requirements <task_dir>` | `prd.md` | 需求行为、失败路径、验收口径已定；不允许 skip。 |
| `overview` | required 时 `grill-done overview`；skippable 时可 `grill-skip overview --user-quote "<理由>"`；随后 `confirm overview` | `prd.md` + `design_package/README.md` + `design_package/design-main.md`；light 链为 `prd.md` + `design.md` | owner、架构归属、技术决策承接和详细设计索引已定。 |
| `detail` | required 时 `grill-done detail`；skippable 时可 `grill-skip detail --user-quote "<理由>"`；随后 `confirm detail` | overview 覆盖范围 + `design_package/chapters/*.md` + `implement.md`；light 链为 `prd.md` + `design.md` + `implement.md` | 可编码合同、测试映射、不得补造清单和实现切片已定。 |

## 5. 累积 digest 规则

确认快照按阶段累积：下游阶段包含上游产物。

规则：

- `requirements` digest 只覆盖需求产物。
- `overview` digest 覆盖需求产物和概要主定义。
- `detail` digest 覆盖需求产物、概要主定义、详细设计和实现计划。

这样可以防止上游产物在下游确认后被改动而仍然进入实现。若 `prd.md` 在 overview/detail 确认后发生变更，overview/detail 的确认快照会失配；若 `design-main.md` 或 `design.md` 概要部分发生变更，detail 的确认快照会失配。

失配时必须回到最早失配阶段，重新完成必要的 review、design-grill 和 confirm。

## 6. design-grill 策略

`requirements` 阶段必须运行 `design-grill`，只能用 `guru_gate.py grill-done requirements <task_dir>` 记录完成；`grill-skip requirements` 必须被拒绝。

`overview` / `detail` 采用 full/high-risk 触发策略：

- `task.json guru_chain=full`：必须运行 `design-grill`，不允许 skip。
- `risk_level=high` 或 `guru_risk.high_risk=true`：必须运行 `design-grill`，不允许 skip。
- `risk_level` 缺失或无法判定：按保守策略视为 required，必须运行 `design-grill`。
- 只有 `guru_chain=light` 且显式 `risk_level=low`（或 `guru_risk.low_risk=true`）时，`overview` / `detail` 才是 skippable。

low-risk skip 不是聊天口头豁免，必须由 `guru_gate.py grill-skip <overview|detail> <task_dir> --user-quote "<跳过理由>"` 写入 `task.json`，记录当时的 `policy`、`guru_chain`、`risk_level`、理由与 digest。若后续任务改为 full/high/unknown，既有 skip 凭据失效，必须重新 `grill-done` 或重新合法 skip。

## 7. grill-done、grill-skip 与 confirm

`design-grill` policy 是 confirm 的硬前置。结构 Gate 通过后、confirm 前必须满足下列条件之一：

- `grill-done <gate>` - 当前 gate 已运行 design-grill，并写入当前阶段 digest。
- `grill-skip overview|detail --user-quote "<跳过理由>"` - 仅 low-risk 非 full 策略下合法，写入理由与当前阶段 digest。

无效凭据：

- 聊天中说“已确认”。
- Design Grill Packet 文本。
- review skill 的“可进入下一阶段”结论。
- 手写 `.grilled-*`、`.grill-nudged-*` 或直接编辑 marker。

`confirm <gate>` 只在对应 gate 的 grill 凭据有效时才允许写入确认快照。grill digest、grill policy 或 confirm artifact digest 失配时，需要重新 `grill-done` / 合法 `grill-skip` 并重新 confirm。

## 8. strict 与 soft

`guru.gate_mode` 控制人工 Gate 写入通道：

- `strict`：默认模式。用户本人在交互式终端运行 `guru_gate.py grill-done` / `grill-skip` / `confirm`；agent 不得代跑。
- `soft`：用户在本轮对话中明确确认后，agent 可以用 `--via-agent --user-quote "<用户确认原话>"` 代跑，并在 `task.json` 留审计痕迹。

无论 strict 还是 soft，结构 Gate 复跑、grill digest、confirm artifact digest、`task.py start` 前的 `guru_gate.py check` 都必须生效。

## 9. 失配恢复流程

先查看状态：

```bash
python3 .trellis/scripts/guru/guru_gate.py status <task_dir>
```

按最早缺口恢复：

1. 缺结构产物或结构 Gate 不通过：回到对应 writing/review 阶段修产物。
2. 缺 grill 凭据：requirements/full/high/unknown 运行 `grill-done <gate>`；仅 low-risk 非 full 的 overview/detail 可运行 `grill-skip <gate> --user-quote "<理由>"`。
3. grill digest 或 policy 失配：说明产物或风险策略在 grill 后改过，重新 design-grill 或重新记录合法 skip。
4. confirm 快照失配：说明产物在 confirm 后改过，重新 confirm；若改动影响语义，先重新 review 与 design-grill。
5. 三道 Gate 均有效后，运行 `guru_gate.py check <task_dir>`，通过后才允许 `task.py start`。

最终检查：

```bash
python3 .trellis/scripts/guru/guru_gate.py check <task_dir>
```
