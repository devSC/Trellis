# Harness — 五阶段方法 SSOT 入口

## Pre-Development Checklist（每个任务开始前）

- [ ] 读 `.trellis/spec/conventions/project-conventions.md` 并通过其校验清单 C1~C5（缺失/未填 → 停止，先完成项目约定）
- [ ] 读 `.trellis/spec/guides/golden-path.md`（分层依赖律与禁止清单）
- [ ] 按本任务所处阶段读对应 SSOT（下表），并把所读文件登记进任务的 `implement.jsonl` / `check.jsonl`（带 reason）
- [ ] 若本任务处于 planning Gate 或准备 `task.py start`，读 [gate/gate-confirmation-model.md](./gate/gate-confirmation-model.md)
- [ ] 产物语言：中文优先（英文仅限代码标识符、命令、路径、协议字段、外部专有名词、缩写、原文引用）

> 项目实际按层模式见 `.trellis/spec/<layer>/`（by-layer 项目 spec，`flutter/`/`service/`/`shared/`，bootstrap 填实）；本 harness 只承载方法学，不写项目实例。

## 阶段 → SSOT 映射

**双轨制**：task.json `guru_chain` 判轨（创建默认 `full`）。full=完整五阶段链，需求走正式需求包、设计走目录级设计包（task.json `design_package`）；light=轻量链（分流+用户同意），产物为任务内单文件。下表产物列写作 `full / light`。

| 阶段 | 产物（full / light） | 装载 |
|------|------|------|
| 需求 | 正式需求包（requirement-writing 撰写 + requirement-review 门禁）+ `prd.md` 行为规格抽取 / 仅 `prd.md` | guru-ai-guides `requirement-writing`、`requirement-review` skill 及其标准包 `requirement-doc-standard`（**硬前置：未安装即停**）；jsonl 引用安装路径 |
| 概要设计 | `design_package/design-main.md` / `design.md` §概要 | [overview/overview-structure-single-source.md](./overview/overview-structure-single-source.md) |
| 详细设计 | `design_package/chapters/*.md`（逐章）/ `design.md` §详细 | [detail/detail-structure-single-source.md](./detail/detail-structure-single-source.md) + 涉及类型的 [detail-type-controller](./detail/detail-type-controller.md) / [detail-type-usecase](./detail/detail-type-usecase.md) / [detail-type-repository-datasource](./detail/detail-type-repository-datasource.md)（其余六类 doc_type 为 pending：full 链须显式 `L2豁免` 或先补 L2，light 链按 L1 合同八问展开并标注 `l2_status: pending`） |
| 实现 | 代码 + `implement.md`（trace） | golden-path + [implementation/implementation-trace-contract.md](./implementation/implementation-trace-contract.md) |
| 审核/复盘 | findings + spec 回写 | 各 SSOT 审核基线章节 + [extraction-template.md](./extraction-template.md) |

Guru Gate、review_runs 证据、confirm 快照、累积 digest 与失配恢复流程见 [gate/gate-confirmation-model.md](./gate/gate-confirmation-model.md)。摘要：requirements 结构通过后由用户确认；overview/detail 由当前 digest 下两个不同 run-id 的 clean review 记录驱动；detail 双 clean 后再由用户确认。

## Quality Check（阶段 Gate，verify 脚本同口径）

- 需求 Gate：无行为/前置条件/状态变化/失败路径/验收场景 → 不进概要。
- 概要 Gate：行为无唯一 owner+三问理由、归属违反分层依赖律、承接索引缺失 → 不进详细。
- 详细 Gate：合同八问缺项、追溯不到概要 owner、无测试映射、涉权限无合规依据 → 不进实现。
- 实现 Gate：analyze/test/lints/compliance 任一无证据、trace 四节不全 → 不进 commit。
- 审核：存量豁免判定（SLOT-15 内记债不阻塞；清单外新增违例阻塞）。

- 编号与追溯：行为以 `BHV-NNN`、单元以 `UNIT-<slug>` 标题定义，引用写编号 token；`guru_gate.py trace-matrix <task_dir> --write` 生成追溯矩阵，断链进不了详细/实现 Gate。

缺陷只能回上游修：审核发现结构性缺陷（归属错、合同越界）回到拥有该决策的阶段修订，禁止下游补造。
