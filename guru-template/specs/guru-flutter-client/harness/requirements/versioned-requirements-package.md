# 版本化需求包结构（项目侧版本化外层）

> full 链正式需求包在**项目 docs 目录**的版本化组织规范。本文只定义「版本隔离外层 + 机器入口 + 审计/快照层 + 演进规则」;版本目录**内部**的文档体系、章节承载、编号契约与完成收敛口径**完全沿用**既有标准,冲突以既有标准为准:
>
> - `requirement-doc-standard/references/requirement-structure-single-source.md`(下称 single-source):目录形态 §2、文档职责 §4、API/CLI 适用 §5.1、核心能力定义 §5.2、编号契约 §6、单一来源 §9、修订形态 §12、完成收敛 §13。
> - `requirement-writing/references/document-organization.md`(下称 doc-org):已定义 `versions/` 按同一结构分目录 + `changes/change-log.md + changes/changes/` 变更管理。
>
> 本文是对上述既有能力的**细化与治理增量**,不是新需求体系。requirement-writing / requirement-review 撰写与审核正式需求包时,版本目录内部仍以 single-source 为准。

## 1. Canonical 目录结构

`[既有]` = 沿用 single-source/doc-org;`[新增]` = 版本化治理增量。

```text
docs/requirements/
  README.md                          # [既有职责] 全局版本入口/版本矩阵(single-source §4)

  versions/
    v1.0.0/
      README.md                      # [既有] 本版本导航/索引/追踪矩阵/版本入口(§4)
      manifest.yaml                  # [新增] README 版本入口的机器镜像(§3)

      requirement-main.md            # [既有] 第一/二章 + 核心能力定义(§5.2)
      requirement-api.md             # [既有] API 适用时(§5.1)
      requirement-cli-command.md     # [既有] CLI 适用时(§5.1,按项目判定)
      requirement-non-functional.md  # [既有] 非功能主定义
      modules/                       # [既有] 第三章起详细(§11 触发拆分)

      changes/                       # [既有] 变更管理(§2 / doc-org)
        change-log.md                #   汇总条目
        changes/                     #   语义化详细变更说明

      traceability.md                # [新增] 版本级手维护审计参考(§6)
      decisions.md                   # [新增] 产品/范围级长期决策(§7)
      snapshots/                     # [新增] 关键节点快照(§8)
```

与既有最小示例(`requirement-doc-standard/.../examples/unique-structure-minimal/`)的关系:把那套扁平结构整体下沉到 `versions/<version>/` 内,**文件清单与职责不变**,仅在外层加版本隔离与四个 `[新增]` 文件。

## 2. 版本隔离

- 正式需求正文位于 `docs/requirements/versions/<version>/`,版本目录根部是该版本的 canonical requirement root。
- 版本目录**内部结构、章节承载与编号契约必须沿用** single-source §2-§6;不得为版本化另造并行章节体系,不得裁剪既有必备文档——尤其 `requirement-cli-command.md`(按 §5.1 适用性判定,guru 类 CLI 工具通常适用)与 `requirement-main.md` 的核心能力定义(§5.2,requirement-review 头号审核项,缺失即不满足放行口径)。

## 3. 全局 / 版本 README 与 `manifest.yaml`

- `docs/requirements/README.md` 与 `versions/<version>/README.md` 落地 single-source §4「版本入口 / 版本矩阵」职责(导航、索引、章节追踪矩阵、编号差集、入口分支可达矩阵、版本状态),不是新概念,不承载需求正文。
- `manifest.yaml` 为 agent/gate/review 提供确定机器入口,是 README 版本入口信息的**机器镜像**;版本事实以 README + 既有标准为准,二者不一致以 README/标准为准并修正 manifest。

```yaml
version: v1.0.0              # 目录标识(带 v)
app_version: 1.0.0          # pubspec version(X.Y.Z,不带 v);X.Y.Z 与 version 一致且可机校验
status: candidate           # draft/candidate/approved/released/superseded
inherits_from: v0.9.0       # 上一版本目录(首版 null);配合演进策略 §9
supersedes: []              # 本版本取代/废弃的旧版本目录
canonical_root: .
canonical_excludes: [snapshots, changes]   # 不进 canonical digest 的子树
current_requirement_entry: README.md
traceability: traceability.md
change_log: changes/change-log.md
decisions: decisions.md
snapshots: snapshots
```

`build_number` 不进 manifest 主体、不参与 gate digest,仅在 `snapshots/` 或 release evidence 按节点记录。

## 4. 变更:沿用既有 `changes/`,禁日期子目录

- 变更承载位沿用既有 `changes/change-log.md`(汇总)+ `changes/changes/`(语义化详细),**不另造** `changelog.md`。
- 每次正式需求变化在 `change-log.md` 记:日期、变更标题、来源任务/issue、改动需求 ID(`REQ-UC-XXX`)、影响正文文件、验证状态。
- 默认**禁止**把变更结构退化为按日期拆分的子目录(`changes/YYYY-MM-DD/`、`versions/<version>/YYYY-MM-DD/`):日期非业务语义、同日多任务混淆、跨日任务被拆、易被误读为需求入口、增加 review 与 digest 入口歧义。既有 `change-log.md` 已用「每轮完成收敛作为独立变更记录」语义化承载。
- 如确有外部审计独立变更包,可用语义化单文件 `changes/changes/0001-<slug>.md`,并声明为变更包、非需求正文、不进 canonical digest。

## 5. 变更/收敛判据归位

- 变更属局部修订还是文档级重构 → single-source §12(修订形态)。
- 是否触发完成收敛清理 → single-source §13(完成收敛清单)。
- **是否需要重新 requirement-review** → **不归 §12/§13**(§12 只约束需求文档产物本身);引 `gate/gate-confirmation-model.md` 与 requirement-review 门禁。
- 不在本规范另造 Gate 失效判据。小任务不改变正式产品事实时,不更新版本需求与变更记录。

## 6. `traceability.md`(手维护审计参考)

版本级审计参考,**不是新的追溯主定义,永不作硬 Gate**。

与既有机制的真实关系(经 `overlay/verify/guru_gate.py` 源码核验):harness `trace-matrix` 是 **task 级**,矩阵列为「`BHV-NNN` × owner × `UNIT-<slug>` × 测试 × 切片」,**不含 `REQ-UC` 列、无多任务聚合入口**。因此版本级 traceability **无法**由 `trace-matrix` 直接派生,二者默认**不自动连通**;traceability 为**手维护审计参考**,`Requirement ID` 列人工回填(已知 drift 风险),靠 requirement-review 与完成收敛兜底。

- 最小字段:`REQ-UC-ID | Source Task | Design Unit(UNIT-<slug>) | Code Entry | Test Evidence | Status`。
- `Requirement ID` 强制用既有稳定编号 `REQ-UC-XXX`(及 `API-INTENT-XXX`/`CLI-INTENT-XXX`,single-source §6),**禁止**另造 `REQ-<MODULE>-NNN`。
- 状态↔drift 映射:`covered`/`partial`/`missing`(需求缺代码)/`orphan_behavior`(代码超出需求)/`untested`(需求缺验证)/`blocked`;不得仅凭测试或结构校验通过即宣称对齐。
- **自动连通是显式实现前置(非默认)**:需先定义 `REQ-UC ↔ BHV/UNIT` 映射桥 + 扩展 `trace-matrix` 多任务聚合到版本目录;列为后续独立改造。

## 7. `decisions.md`(划清边界)

只承载「产品/范围级、非架构 ADR、非单条需求确认,又需跨任务跨版本解释」的决策。架构决策走既有 ADR;单条需求确认走核心能力表 `confirmation_status`(含 `user_quote`/`confirmed_ref`)。`decisions.md` 引用上述位置,不重写。每条至少:Decision ID、状态、日期、来源任务、决策正文、原因、影响的 `REQ-UC-XXX`。

## 8. `snapshots/`(不进主链)

关键节点完整快照(requirement-review/RC/release/外部审计),命名含日期与原因。**不**作 canonical root、**不**参与 §13 完成收敛、**不**进 §6 编号差集、**不**进 requirement-review 默认入口、**不**进 gate digest(由 `manifest.canonical_excludes` 兜底)。不每日自动生成。

## 9. 版本演进 / 继承

默认 **full-copy + diff**:

- **版本号语义/来源**:`<version>` 用 semver `vX.Y.Z`,来源 `pubspec.yaml` 的 `version: X.Y.Z+N`(`+N` build 不进目录名);`X.Y.Z` 与 `manifest.app_version` 一致。
- **开新版本目录的触发/时机**:由 `docs/requirements/README.md` 的 current-development 指针决定,与 pubspec bump **解耦**(可先建 draft 版本目录写需求,bump 在发布对齐)。
- **继承**:新版本目录从上一版**整体复制**、自包含完整正文,`change-log.md` 只记相对上版 diff,`manifest.inherits_from` 指上一版。接受「稳定 `REQ-UC` 跨版本重复正文」为已知代价(换单版本自包含可读、digest/review 边界清晰)。**不采用** baseline+delta(单版本读不到完整需求、canonical root 名不副实);如项目坚持 baseline+delta,须在 README/manifest 写清解析顺序并经用户确认。
- **偏离基线**:代码与需求偏离判断锚定 README current-development 指针指向的版本目录;released 目录冻结只读(改动走新版本或 hotfix 版本号)。
- **pre-release/channel 后缀归一**:`1.0.0-rc.1` 等归一到 `v1.0.0` 目录,rc/channel 进 `manifest.status` 与 `snapshots/`,不另开目录。

## 10. 与 Guru Gate 的关系(现状,不得误述)

- `requirements` adversarial review **会读取**正式需求包作为复核证据;但 `requirements` digest **只哈希 `prd.md`**(见 [gate/gate-confirmation-model.md](../gate/gate-confirmation-model.md))。故「改正式需求包」**不会**自动改变 digest、不会自动使 `confirm requirements` 失效。
- `change-log.md` 与 `traceability.md` **不得**写「digest 已失效 / review 已重跑」这类人工结论(违背 gate 模型「不信任手写结论」),只声明按 §12/§13 与 review 门禁应触发的复核。
- 让 review 经 `manifest.canonical_root` 定位正式需求包、或让「改正式需求包」自动触发 requirements digest 失效,均为**显式实现前置**(需扩展 review 入口解析 / `guru_gate.py` requirements digest 路径集合),非默认;不做时维持「review 读取但 digest 不哈希」的现状。
