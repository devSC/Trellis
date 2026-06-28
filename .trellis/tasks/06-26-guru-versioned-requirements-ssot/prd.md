# Define versioned requirements SSOT structure

## Goal

为 Guru full 链的正式需求包定义一套稳定、可审计、不会分裂 SSOT 的**版本化外层**规范。

关键定位(方案 A · 补充式):本规范**不另立**一套需求文档体系,而是作为既有 `requirement-doc-standard` 标准的**版本隔离外层 + 治理增量**。版本目录内部的文档体系、章节承载、编号契约与完成收敛口径**完全沿用**既有标准;本任务只新增「按版本隔离」「机器入口 manifest」「关键节点 snapshots」「版本级聚合视图(traceability/decisions/变更记录)」这几层治理能力。

解决以下问题:

- 正式需求应按软件版本隔离,但隔离方式必须复用既有标准而非重定义。
- 不应把 `changes/YYYY-MM-DD/` 作为变更结构;沿用既有 `changes/change-log.md + changes/changes/`,只禁止其退化为日期子目录。
- 小任务完成后只在改变正式产品事实时同步版本需求,变更/收敛判定复用既有 §12/§13。
- 判断代码与需求是否偏离,通过需求版本基线、稳定需求 ID(`REQ-UC-XXX`)、版本级 traceability 审计参考(手维护,与 harness BHV 维 `trace-matrix` 不自动连通)、测试/证据闭环完成。

本任务只负责把上述规范沉淀成 Trellis planning 包。是否修改 Guru 模板、workflow、harness 或既有标准包,必须在本任务后续阶段经用户确认后再执行。

## Alignment With Existing Standard(对齐声明,强制前置)

本规范的单一来源依赖以下既有文件,所有版本目录内部约定**以它们为准**,本 prd 仅定义版本化外层与治理增量;冲突时以既有标准为准:

- `guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`
  —— 需求文档语义 SSOT 中立主定义(目录形态 §2、文档职责 §4、API/CLI 适用 §5.1、核心能力定义 §5.2、编号契约 §6、单一来源 §9、修订形态 §12、完成收敛 §13)。
- `guru-template/overlay/agents-skills/requirement-writing/references/document-organization.md`
  —— 已定义版本化(`versions/` 按同一结构分目录,见其 §模块化结构/§版本与变更管理)与 `changes/change-log.md + changes/changes/` 变更管理。
- `guru-template/specs/guru-flutter-client/harness/index.md`
  —— `guru_gate.py trace-matrix <task_dir> --write` 基于 `BHV-NNN`/`UNIT-<slug>` 生成**任务级**追溯矩阵(列:BHV × owner × UNIT × 测试 × 切片,**不含 REQ-UC**),断链进不了详细/实现 Gate。
- `guru-template/specs/guru-flutter-client/harness/gate/gate-confirmation-model.md`
  —— `requirements` adversarial review 会读取「正式需求包」作为复核证据(§表 review 行);但 `requirements` digest 哈希范围仅 `prd.md`(§artifact digest 表 + 覆盖范围说明)。

继承点 / 增量点速览:

| 维度 | 既有标准已有(沿用) | 本任务增量 |
| --- | --- | --- |
| 版本隔离 `versions/<version>/` | document-organization §版本与变更管理 | 细化字段、命名、演进规则、与完成收敛衔接 |
| 版本目录内部正文 | single-source §2/§4(main/api/cli-command/non-functional/modules/README) | 无(完全沿用) |
| 核心能力定义 | single-source §5.2(requirement-main.md 强制主定义) | 无(完全沿用) |
| 编号契约 | single-source §6(`REQ-UC-XXX`/`API-INTENT`/`CLI-INTENT`) | 无(完全沿用) |
| 变更管理 | single-source §2 + document-organization(`changes/change-log.md + changes/changes/`) | 仅禁止退化为日期子目录 |
| 追溯 | README 追踪矩阵 + §6 编号差集 + harness `trace-matrix`(task 级 BHV/UNIT) | 版本级 `traceability.md`(手维护审计参考,非新主定义、非派生) |
| 决策 | confirmation_status(需求确认)+ ADR(架构) | 版本级 `decisions.md`(仅产品/范围级、非 ADR、非单条确认) |
| 机器入口 | 无(靠人读 README) | **新增** `manifest.yaml`(README 版本入口的机器镜像) |
| 关键节点快照 | 无 | **新增** `snapshots/` |
| 版本演进/继承 | document-organization 只给「按同一结构分目录」流程,未答继承 | **新增** REQ-012 演进规则(full-copy+diff) |

## Confirmed Facts

- 当前仓库的 Guru client workflow 是五阶段:需求、概要设计、详细设计、实现、审核。
- Guru full 链中,`prd.md` 是任务内行为规格抽取层;正式需求包位于项目 docs 需求目录,并由 `requirement-writing` / `requirement-review` 负责,二者均强制先读 `requirement-doc-standard` 主定义。
- **既有标准已定义版本化**:`document-organization.md` 明确「版本化场景可在 `versions/` 下按同一结构分目录维护」并给出版本与变更管理流程;`requirement-writing/SKILL.md` 要求 agent 用 `rg --files` 定位版本目录。本任务是细化而非发明。
- **既有 `requirement-main.md` 必须承载「核心能力定义」**(single-source §5.2,全标准最长一节,含 capability 字段合同/候选池/P0-P2/反证/confirmation_status),是 requirement-review 头号审核项。版本化不得丢失该产物。
- **harness `trace-matrix` 是 task 级、BHV/UNIT 维、无 REQ-UC 列、无多任务聚合入口**(经 `guru_gate.py` 源码核验):因此版本级 traceability 无法由它直接派生,默认为手维护审计参考。
- `requirements` adversarial review 已会读取正式需求包,但 `requirements` digest 仅哈希 `prd.md`;因此「改正式需求包」不会自动使 `confirm requirements` 失效——这是现状,不是缺陷,但本规范不得假设它会自动失效。
- 用户偏好是让正式需求按版本隔离,并保留全局唯一入口,但不维护一个无限膨胀的全量总需求正文。

## Requirements

### REQ-001: 全局入口对齐既有 README「版本入口」职责

`docs/requirements/README.md` 作为全局唯一入口,声明当前有效版本、开发中版本、历史版本状态和阅读规则。其职责是既有标准 README「版本入口 / 版本矩阵」(single-source §4)在 `versions/` 之上的落地,**不是新概念**。

它不得承载完整业务需求正文,避免与版本目录内的正式需求重复并产生漂移。

### REQ-002: 正式需求按版本隔离,内部完全沿用既有标准

正式需求正文位于 `docs/requirements/versions/<version>/`。版本目录根部是该版本的 canonical requirement root。版本目录**内部结构、章节承载与编号契约必须沿用** single-source §2-§6,默认结构:

```text
docs/requirements/versions/v1.0.0/
  README.md                       # 既有:导航/索引/追踪矩阵/版本入口(§4)
  manifest.yaml                   # 新增:README 版本入口的机器可读镜像(REQ-011)
  requirement-main.md             # 既有:第一/二章主定义,含核心能力定义(§5.2)
  requirement-api.md              # 既有:API 适用时(§5.1)
  requirement-cli-command.md      # 既有:CLI 适用时,按 §5.1 逐项目判定(guru 类 CLI 工具通常适用)
  requirement-non-functional.md   # 既有:非功能主定义
  modules/                        # 既有:第三章起详细(§11 触发拆分)
  changes/                        # 既有:change-log.md + changes/(§2)
    change-log.md
    changes/
  traceability.md                 # 新增:版本级手维护审计参考(REQ-005)
  decisions.md                    # 新增:产品/范围级长期决策(REQ-006)
  snapshots/                      # 新增:关键节点快照(REQ-008)
```

不得在版本目录内裁剪既有必备文档(尤其 `requirement-cli-command.md` 与 `requirement-main.md` 的核心能力定义),也不得为版本化另造一套并行章节体系。

### REQ-003: 变更结构沿用既有 `changes/`,仅禁止日期子目录

正式需求变更承载位沿用既有 `changes/change-log.md`(汇总)+ `changes/changes/`(详细),**不另造** `changelog.md`。

默认**禁止**把变更结构退化为按日期拆分的子目录:

```text
versions/<version>/changes/YYYY-MM-DD/   # 禁止
versions/<version>/YYYY-MM-DD/           # 禁止
```

原因:日期不是业务语义、同日多任务混淆、跨日任务被拆、易被误读为需求入口、增加 review 与 Gate digest 的入口歧义。既有 `changes/change-log.md` 已用「每轮完成收敛作为独立变更记录」的语义化方式承载,无需日期目录。

如确有外部审计独立变更包需求,可用语义化单文件 `changes/changes/0001-story-chat-local-recovery.md`,并显式声明其为变更包、非需求正文、不进 canonical digest。

### REQ-004: 变更历史进入既有 `changes/change-log.md`,判据归位

每次正式需求变化,在 `changes/change-log.md` 记录:日期、变更标题、来源任务/issue、改动的需求 ID(`REQ-UC-XXX`)、影响的正文文件、验证状态。

判据归位(避免越引):

- 变更属局部修订还是文档级重构,引用 single-source §12(修订形态)。
- 是否触发完成收敛清理,引用 single-source §13(完成收敛清单)。
- 「是否需要重新 requirement-review」**不归** §12/§13——single-source §12 明确只约束需求文档产物本身、不指导 re-review 触发——该判定引用 `gate-confirmation-model` 与 requirement-review 门禁。

本规范不另造一套 Gate 失效判据。小任务如果不改变正式产品事实,不需要更新版本需求和变更记录。

### REQ-005: traceability 是手维护的版本级审计参考(非派生、非主定义)

`versions/<version>/traceability.md` 记录需求到任务、设计、代码、测试/证据的映射,作为版本级审计参考,**不是新的追溯主定义**,**永不作硬 Gate**。

与既有机制的真实关系(经 `guru_gate.py` 源码核验,不得误述):

- harness `trace-matrix` 是 **task 级**,列为「`BHV-NNN` × owner × `UNIT-<slug>` × 测试 × 切片」,**不含 `REQ-UC` 列、无多任务聚合入口**。因此版本级 traceability **无法**由 `trace-matrix` 直接派生/汇总,二者默认**不自动连通**。
- 故 traceability 默认为**手维护审计参考**:`Requirement ID` 列人工回填,这是**已知 drift 风险**,靠 requirement-review 与完成收敛兜底,而非脚本保鲜。

约束:

- `Requirement ID` 列必须使用既有稳定编号 `REQ-UC-XXX`(及 `API-INTENT-XXX`/`CLI-INTENT-XXX`),禁止另造 `REQ-<MODULE>-NNN`。
- 最小字段:`REQ-UC-ID | Source Task | Design Unit(UNIT-<slug>) | Code Entry | Test Evidence | Status`。
- 状态枚举与 drift risk 的映射:`covered`(齐全)、`partial`(部分)、`missing`→需求缺代码、`orphan_behavior`→代码超出需求、`untested`→需求缺验证、`blocked`;不得仅凭测试或结构校验通过即宣称对齐。
- **若要让版本级 traceability 与 harness 自动连通**(非默认,显式实现前置/风险):需先定义 `REQ-UC ↔ BHV/UNIT` 映射桥,并扩展 `trace-matrix` 支持多任务聚合到版本目录——列为后续独立改造,不在本任务默认范围。

### REQ-006: 长期决策进入 `decisions.md`,与既有决策位划清边界

`decisions.md` 只承载「产品/范围级、非架构 ADR、非单条需求确认,又需跨任务跨版本解释」的决策。

边界:架构决策走既有 ADR;单条需求确认走既有核心能力表 `confirmation_status`(含 `user_quote`/`confirmed_ref`)。`decisions.md` 引用上述位置,不重写其内容,避免「为避免散落反而多一处散落」。

每条 decision 至少:Decision ID、状态、日期、来源任务、决策正文、原因、影响的 `REQ-UC-XXX`。

### REQ-007: 任务文档与正式需求包分层,修订形态判定引用 §12/§13

`.trellis/tasks/<task>/prd.md`、`design.md`、`implement.md` 承载任务过程、候选变更、执行计划和验证证据;正式版本目录承载已确认、可复用、跨任务有效的产品事实。

任务结束时按既有 single-source §12/§13 判断变更属局部修订还是文档级重构,并回答:是否改变用户可见行为/业务规则/接口字段/入口流程,是否让某条验收失效,是否实现了需求外行为。只有答案为「是」时,才同步版本需求、`traceability.md`、`changes/change-log.md` 或 `decisions.md`(re-review 触发口径见 REQ-004)。

### REQ-008: 快照只用于关键节点,且不进任何主链

`snapshots/` 只用于需求评审、RC、发布、外部审计等关键节点,不每日自动生成。推荐命名 `snapshots/2026-06-26-requirement-review/`。

快照**不**作 canonical root、**不**参与 single-source §13 完成收敛、**不**进 §6 编号差集、**不**进 requirement-review 默认入口、**不**进 gate digest。

### REQ-009: 编号契约对齐既有 `REQ-UC-XXX`(强制)

版本化需求包及其所有聚合文件(traceability/change-log/decisions)引用需求时,一律复用 single-source §6 的稳定编号 `REQ-UC-XXX` / `API-INTENT-XXX` / `CLI-INTENT-XXX`,遵守其编号稳定性规则(不重排、语义变化新增、deprecated 不复用)。

禁止另造 `REQ-<MODULE>-NNN` 体系(任意大写模块前缀);如需模块视图,必须定义到 `REQ-UC-XXX` 的映射,不得替代稳定编号。

### REQ-010: 版本目录保留「核心能力定义」(强制)

版本目录的 `requirement-main.md` 必须按 single-source §5.2 承载「核心能力定义」(候选池、正式核心能力清单、字段合同、`P0/P1/P2`、反证、`confirmation_status`)。版本化是隔离外层,不改变章节承载与完成收敛合同(§13);缺失核心能力定义的版本包视为不满足 requirement-review 放行口径。

### REQ-011: `manifest.yaml` 是 README 版本入口的机器可读镜像

`manifest.yaml` 为 agent / gate / review 提供确定的机器入口,是既有 README「版本入口」信息的机器镜像。主从关系:版本事实以 README + 既有标准为准,`manifest.yaml` 是其机器可读派生,二者不一致时以 README/标准为准并修正 manifest。

建议字段(版本号语义见 REQ-012):

```yaml
version: v1.0.0              # 目录标识,带 v 前缀
app_version: 1.0.0          # pubspec version 取值(X.Y.Z),不带 v;与 version 的 X.Y.Z 必须一致
status: candidate           # draft/candidate/approved/released/superseded
inherits_from: v0.9.0       # 上一版本目录(首版写 null);配合演进策略,见 REQ-012
supersedes: []              # 本版本取代/废弃的旧版本目录列表
canonical_root: .           # 版本目录根
canonical_excludes: [snapshots, changes]   # 不进 canonical digest 的子树
current_requirement_entry: README.md
traceability: traceability.md
change_log: changes/change-log.md
decisions: decisions.md
snapshots: snapshots
```

`build_number` 不进 manifest 主体、不参与 gate digest(频繁 +1 不应扰动 digest),仅在 `snapshots/` 或 release evidence 按节点记录。

让 `requirement-review` 经 `manifest.canonical_root` 定位正式需求包是**显式实现前置**(现状 `review-baseline` 步骤 0 不消费 manifest,靠调用方指向目录);本任务只定义该机器入口,是否接入由后续 review 改造决定。

### REQ-012: 版本标识与演进规则(强制,补 canonical root 间关系)

多版本物理隔离(REQ-002)定义了「每个版本目录根是 canonical root」,本 REQ 定义多个 canonical root 之间的关系,避免版本目录沦为复制粘贴式分裂(与「不维护无限膨胀全量正文」冲突)。

- **版本号语义/来源**:`<version>` 采用 semver `vX.Y.Z`,来源 `pubspec.yaml` 的 `version: X.Y.Z+N`(`+N` build 不进目录名);`X.Y.Z` 与 `manifest.app_version` 可机校验一致。
- **开新版本目录的触发与时机**:由 `docs/requirements/README.md` 的 current-development 指针决定,与 pubspec bump **解耦**(可先建 `draft` 版本目录开始写需求,bump 在发布时对齐);谁决定开新版本由产品 owner 在 README 声明。
- **继承策略(二选一,默认写死)**:默认采用 **full-copy + diff**——新版本目录从上一版本**整体复制**,自包含完整正文;`change-log.md` 只记相对上一版的 diff;`manifest.inherits_from` 指向上一版本。接受「稳定 `REQ-UC` 编号跨版本重复正文」为已知代价(换取每个版本目录自包含、单版本可读、review/digest 边界清晰)。**不采用** baseline+delta(单版本读不到完整需求、canonical root 名不副实)。如项目坚持 baseline+delta,须在 README/manifest 写清解析顺序并经用户确认——属偏离默认。
- **多版本并存时的偏离基线**:代码与需求偏离判断锚定 `README` current-development 指针指向的版本目录;released 版本目录冻结,只读不改(改动走新版本或 hotfix 版本号)。
- **pre-release/channel 后缀归一**:`1.0.0-rc.1` 等归一到 `v1.0.0` 版本目录,rc/channel 信息进 `manifest.status` 与 `snapshots/`,不另开目录。

> 继承策略 full-copy+diff 是工程默认(适配 guru 单 app / 小团队);如需改 baseline+delta 请在定档时说明。

## Acceptance Criteria

### Planning 验收(本任务范围内,据实勾选)

- [x] `prd.md` 明确版本化需求 SSOT 的目标、约束和验收口径,并显式声明对既有 `requirement-doc-standard` 的继承点/增量点/冲突点。
- [x] `prd/design/implement` 顶部均显式引用 `requirement-structure-single-source.md` 与 `document-organization.md`。
- [x] `design.md` 明确目录结构、文件职责、变更流转、Gate/digest 影响和兼容边界,且版本目录内部沿用既有 §2-§6(含 CLI、核心能力定义、`REQ-UC-XXX`)。
- [x] `implement.md` 明确后续落地步骤、验证命令、风险点和回滚策略,并把既有标准包纳入改造范围。
- [x] `implement.jsonl` 与 `check.jsonl` 登记既有标准包(single-source / document-organization)、harness `implementation-trace-contract.md` 及 workflow / golden-path。
- [x] `task.json` relatedFiles 与正文证据、jsonl 三者一致。
- [x] `prd.md` 含版本标识与演进规则(REQ-012:版本号来源、开目录时机、full-copy+diff 继承策略、偏离基线、pre-release 归一)。
- [x] traceability(REQ-005)对 harness `trace-matrix` 的关系已按源码实测修正为「不自动连通、手维护审计参考」,无不可兑现的派生断言。

### Implementation 验收(`task.py start` 后适用,本任务不勾,标 `defer to implementation`)

- [ ] (defer) 后续实现不得引入 `changes/YYYY-MM-DD/`;沿用 `changes/change-log.md + changes/changes/`。验证:`rg -n "changes/[0-9]{4}-[0-9]{2}-[0-9]{2}" docs/requirements`(应无命中)。
- [ ] (defer) requirement-review / overview-detail / traceability 的默认入口指向 `versions/<version>/README.md` 或 `manifest.canonical_root`。
- [ ] (defer) 版本目录内部沿用 single-source §2-§6:`requirement-cli-command.md` 按 §5.1 适用性、核心能力定义按 §5.2、需求编号用 `REQ-UC-XXX`。
- [ ] (defer) `.trellis/tasks/<task>/` 与正式需求目录职责分层保持;`snapshots/`/`changes/` 不进 canonical digest。

## Out Of Scope(已进入实现 · 档 1)

- 档 1 范围内**仅修改** `guru-template/specs/` 与 `guru-template/workflows/` 文档及示例;**不碰** `guru-template/overlay/`(标准包 / apply.sh)与 `guru_gate.py`。
- 不创建实际 `docs/requirements/versions/vX.Y.Z/` 目录(只在 spec 描述结构)。
- 不改既有标准包源(档 2 另议)、不改 gate digest(档 3 另议)、不迁移目标项目 `guru_ai_himora` 或任何已安装项目(档 4 另议)。
- 本规范**不取代**既有 `requirement-doc-standard` 的文档体系、章节承载、编号契约与完成收敛口径;只新增版本化外层与治理增量。

## Open Questions(进入实现前需用户拍板)

- **OQ-1 任务定位**:✅ 已决(2026-06-27 用户拍板)——**保持独立任务**。剩余真增量(manifest + snapshots + 版本级审计参考 + 禁日期子目录 + REQ-012 演进规则)作为独立 spec 文档落地,不降级并入既有标准包。
- **OQ-2 继承策略**:✅ 已决——沿用默认 **full-copy+diff**。
- **OQ-3 落地档位**:✅ 已决——**档 1**(仅改 Guru spec/workflow 文档与示例,绕开 overlay),见 implement.md §5。
- **OQ-4(仍 open)**:让「改正式需求包」自动触发 requirements digest 失效需扩展 `guru_gate.py`,属显式实现前置(档 3);留待档 1 完成后按需评估。

## Brainstorm Evidence

- Skill loaded: `.agents/skills/trellis-brainstorm/SKILL.md`
- Existing standard inspected(通读全文):
  - `requirement-doc-standard/references/requirement-structure-single-source.md`(主定义,356 行)
  - `requirement-writing/references/document-organization.md`(versions/ 与 changes/ 变更管理已有)
  - `requirement-writing/references/chapter-guide.md`、`requirement-writing/SKILL.md`、`requirement-doc-standard/SKILL.md`
  - `requirement-review/references/review-baseline.md`、`requirement-doc-standard/references/examples/unique-structure-minimal/README.md`
- Harness/source evidence inspected:
  - `harness/index.md`、`harness/gate/gate-confirmation-model.md`
  - `overlay/verify/guru_gate.py`(`trace-matrix` 实测:task 级、BHV/UNIT 列、无 REQ-UC、无多任务聚合)
- 两轮 agent-team review 结论(详见 scratchpad `review-report.md`、`re-review-report.md`、`alignment-existing-ssot-vs-task.md`):
  - 既有标准已定义 `versions/` 与 `changes/` 变更管理 → 细化而非发明(组 A)。
  - 既有 `requirement-main.md` 强制核心能力定义、编号 `REQ-UC-XXX`、README 版本入口 → 版本目录必须沿用(组 B)。
  - traceability/decisions 与既有 trace-matrix/confirmation_status/ADR 重叠 → traceability 重定位为手维护审计参考、decisions 划清边界(组 C / 复审 B5)。
  - 复审 B6:补 REQ-012 版本演进/继承模型(full-copy+diff)。
  - `manifest.yaml`/`snapshots/` 为真增量,保留并对齐主从、声明不进主链(组 D)。
- Product decisions confirmed:
  - 方案 A 补充式:版本化作为既有标准的隔离外层,不另立需求体系。
  - 沿用既有 `changes/change-log.md + changes/changes/`,仅禁日期子目录。
  - traceability 为手维护审计参考(与 trace-matrix 不自动连通),需求编号统一 `REQ-UC-XXX`。
  - 版本演进默认 full-copy+diff。
  - 任务定位:保持独立任务(非降级并入既有标准包)。
  - 落地档位:档 1(仅 Guru spec/workflow 文档与示例,绕开 overlay/apply.sh 传染)。
