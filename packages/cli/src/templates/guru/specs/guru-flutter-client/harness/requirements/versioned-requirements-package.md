# 版本化需求包结构（guru-flutter-client 项目侧导读）

> 正式需求包版本化的**规则主定义**在标准包 `requirement-doc-standard` 的 `requirement-structure-single-source.md` **§15「版本化需求包」**(writing/review 硬前置均读),`requirement-writing` 的操作要点见 `requirement-writing/references/document-organization.md`「版本与变更管理」节。
> 本文是 guru-flutter-client **项目侧导读**:给结构速览 + 与本项目 Guru Gate 的关系;规则正文不在此复写,一律以 §15 为准。

## 结构速览（详见 single-source §15.1）

`[既有]` = 沿用 single-source §2 扁平结构;`[新增]` = 版本化治理层。

```text
docs/requirements/
  README.md                          # [既有职责] 全局版本入口/版本矩阵（§4）
  versions/
    v1.0.0/
      README.md                      # [既有] 本版本入口（§4）
      manifest.yaml                  # [新增] 机器入口（§15.2）
      requirement-main.md            # [既有] 第一/二章 + 核心能力定义（§5.2）
      requirement-api.md             # [既有] API 适用时（§5.1）
      requirement-cli-command.md     # [既有] CLI 适用时（§5.1）
      requirement-non-functional.md  # [既有] 非功能主定义
      modules/                       # [既有] 第三章起详细（§11）
      changes/                       # [既有] change-log.md + changes/（§15.3）
      traceability.md                # [新增] 手维护审计参考（§15.4）
      decisions.md                   # [新增] 长期决策（§15.5）
      snapshots/                     # [新增] 关键节点快照（§15.6）
```

要点(规则口径以 §15 为准):

- 版本目录内部沿用 single-source §2-§6(含 CLI §5.1、核心能力定义 §5.2、编号 §6);不另造并行体系,不裁剪既有必备文档。
- 变更沿用 `changes/change-log.md`,禁日期子目录,不另造 `changelog.md`(§15.3)。
- `traceability.md` 手维护审计参考,与 harness `trace-matrix` 不自动连通(§15.4 + 下文)。
- 版本演进默认 full-copy + diff(§15.7)。
- `manifest`/`snapshots`/`changes` 不进 canonical digest(§15.2 `canonical_excludes`)。

## 与本项目 Guru Gate 的关系（项目侧,§15 不承载）

本节是 §15 在 guru-flutter-client 的项目侧补充(中立标准包不绑特定 Gate,故留在本导读)。

- `requirements` adversarial review **会读取**正式需求包作为复核证据;但 `requirements` digest **只哈希 `prd.md`**(见 [../gate/gate-confirmation-model.md](../gate/gate-confirmation-model.md))。故「改正式需求包」**不会**自动改变 digest、不会自动使 `confirm requirements` 失效。
- harness `trace-matrix`(`overlay/verify/guru_gate.py`)是 **task 级**、矩阵列为「BHV × owner × UNIT × 测试 × 切片」、**不含 `REQ-UC`、无多任务聚合入口**;因此版本级 `traceability.md` **无法**由它直接派生,默认手维护审计参考(对接 §15.4)。
- `change-log.md` / `traceability.md` **不得**写「digest 已失效 / review 已重跑」这类人工结论(违背 gate「不信任手写结论」),只声明按 §12/§13 与门禁应触发的复核。
- 让 review 经 `manifest.canonical_root` 定位正式需求包、或让「改正式需求包」自动触发 requirements digest 失效,均为**显式实现前置**(扩展 review 入口解析 / `guru_gate.py` requirements digest 路径集合),非默认。
