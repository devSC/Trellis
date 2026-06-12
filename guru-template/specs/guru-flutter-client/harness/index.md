# Harness — 五阶段方法 SSOT 入口

## Pre-Development Checklist（每个任务开始前）

- [ ] 读 `.trellis/spec/conventions/project-conventions.md` 并通过其校验清单 C1~C5（缺失/未填 → 停止，先完成项目约定）
- [ ] 读 `.trellis/spec/guides/golden-path.md`（分层依赖律与禁止清单）
- [ ] 按本任务所处阶段读对应 SSOT（下表），并把所读文件登记进任务的 `implement.jsonl` / `check.jsonl`（带 reason）

## 阶段 → SSOT 映射

| 阶段 | 产物 | 装载 |
|------|------|------|
| 需求 | `prd.md` | 需求三件套 SSOT（guru-ai-guides requirement-doc-standard，jsonl 引用其安装路径） |
| 概要设计 | `design.md` §概要 | [overview/overview-structure-single-source.md](./overview/overview-structure-single-source.md) |
| 详细设计 | `design.md` §详细 | [detail/detail-structure-single-source.md](./detail/detail-structure-single-source.md) + 涉及类型的 [detail-type-controller](./detail/detail-type-controller.md) / [detail-type-usecase](./detail/detail-type-usecase.md) / [detail-type-repository-datasource](./detail/detail-type-repository-datasource.md)（其余六类 doc_type 按 L1 合同八问展开，标注 `l2_status: pending`） |
| 实现 | 代码 + `implement.md`（trace） | golden-path + [implementation/implementation-trace-contract.md](./implementation/implementation-trace-contract.md) |
| 审核/复盘 | findings + spec 回写 | 各 SSOT 审核基线章节 + [extraction-template.md](./extraction-template.md) |

## Quality Check（阶段 Gate，verify 脚本同口径）

- 需求 Gate：无行为/前置条件/状态变化/失败路径/验收场景 → 不进概要。
- 概要 Gate：行为无唯一 owner+三问理由、归属违反分层依赖律、承接索引缺失 → 不进详细。
- 详细 Gate：合同八问缺项、追溯不到概要 owner、无测试映射、涉权限无合规依据 → 不进实现。
- 实现 Gate：analyze/test/lints/compliance 任一无证据、trace 四节不全 → 不进 commit。
- 审核：存量豁免判定（SLOT-15 内记债不阻塞；清单外新增违例阻塞）。

缺陷只能回上游修：审核发现结构性缺陷（归属错、合同越界）回到拥有该决策的阶段修订，禁止下游补造。
