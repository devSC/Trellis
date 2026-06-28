# Design: Versioned Requirements SSOT Structure

> 本设计是既有 `requirement-doc-standard` 的**版本化外层补充**(方案 A),不重定义需求文档体系。
> 单一来源:`requirement-doc-standard/references/requirement-structure-single-source.md`(下称 single-source,引用其 §N)
> 与 `requirement-writing/references/document-organization.md`(下称 doc-org)。冲突时以既有标准为准。

## 1. Problem Framing

既有 Guru full 链已区分:正式需求包(`requirement-writing`/`requirement-review` 负责,均强制先读 single-source)、任务内 `prd.md`(行为规格抽取层)、设计包与实现 trace(overview/detail/implement)。

通读既有标准后确认:**版本化与变更管理并非缺口,而是既有标准的轻定义**——doc-org 已规定「版本化场景可在 `versions/` 下按同一结构分目录维护」并给出 `change-log.md + changes/` 变更流程;single-source §4 已把「版本入口/版本矩阵」定为 README 职责;harness 已有 task 级 `trace-matrix`。

因此本设计要解决的真实缺口收敛为四点治理增量:

1. 把 doc-org 的版本化轻定义**细化**为可机检的 canonical 模型(版本号语义、状态、入口、**演进/继承规则**)。
2. 新增机器入口 `manifest.yaml`,补既有「人读 README」在 agent/gate 场景的不足。
3. 把追溯/决策做成既有机制的**版本级聚合/审计层**,而非新主定义。
4. 新增关键节点 `snapshots/`,且明确其不进任何主链。

版本目录**内部**的文档体系、章节承载、核心能力定义、编号契约与完成收敛口径,一律沿用既有标准,不在本设计重写。

## 2. Canonical Directory Model

图中 `[既有]` 表示沿用 single-source/doc-org,`[新增]` 表示本任务治理增量:

```text
docs/requirements/
  README.md                          # [既有职责] 全局版本入口/版本矩阵(§4)

  versions/
    v1.0.0/
      README.md                      # [既有] 本版本导航/索引/追踪矩阵/版本入口(§4)
      manifest.yaml                  # [新增] README 版本入口的机器镜像(§2.3)

      requirement-main.md            # [既有] 第一/二章 + 核心能力定义(§5.2)
      requirement-api.md             # [既有] API 适用时(§5.1)
      requirement-cli-command.md     # [既有] CLI 适用时,按 §5.1 逐项目判定
      requirement-non-functional.md  # [既有] 非功能主定义
      modules/                       # [既有] 第三章起详细(§11 触发拆分)
        requirement-<module>.md

      changes/                       # [既有] 变更管理(§2 / doc-org)
        change-log.md                #   汇总条目
        changes/                     #   语义化详细变更说明

      traceability.md                # [新增] 版本级手维护审计参考(§2.5)
      decisions.md                   # [新增] 产品/范围级长期决策(§2.7)
      snapshots/                     # [新增] 关键节点快照(§2.8)
        2026-06-26-requirement-review/
```

与既有最小示例(`examples/unique-structure-minimal/`)的关系:把那套扁平结构整体下沉到 `versions/<version>/` 内,**文件清单与职责不变**,仅在外层加版本隔离与四个 `[新增]` 文件。

### 2.1 `docs/requirements/README.md`(既有职责落地)

全局唯一入口,落地 single-source §4「版本入口/版本矩阵」职责:声明 current released / current development / draft / superseded 版本,声明新任务默认沉淀到哪个 version,链接长期产品原则。不承载需求正文、模块细节、变更正文。

### 2.2 `versions/<version>/README.md`(既有职责)

本版本 canonical requirement package entry,职责同 single-source §4:导航、索引、章节追踪矩阵、编号差集结果、入口分支可达矩阵(参照既有 examples README)。声明本版本状态。明确 canonical root 是版本目录根部,不是任意 snapshot 或历史变更。

### 2.3 `manifest.yaml`(新增,README 的机器镜像)

为 agent/gate/review 提供确定机器入口。主从:版本事实以 README + 既有标准为准,manifest 是机器可读派生,不一致以 README/标准为准。

```yaml
version: v1.0.0              # 目录标识(带 v)
app_version: 1.0.0          # pubspec version(X.Y.Z,不带 v);X.Y.Z 必须与 version 一致
status: candidate           # draft/candidate/approved/released/superseded
inherits_from: v0.9.0       # 上一版本目录(首版写 null);配合演进策略 §6
supersedes: []              # 本版本取代/废弃的旧版本目录列表
canonical_root: .
canonical_excludes: [snapshots, changes]   # 不进 canonical digest 的子树
current_requirement_entry: README.md
traceability: traceability.md
change_log: changes/change-log.md
decisions: decisions.md
snapshots: snapshots
```

字段收敛(对应审查 B9):

- `version` 与 `app_version` 不再二义:`version` 是带 `v` 的目录标识(权威),`app_version` 是 pubspec 的 `X.Y.Z` 取值,二者 `X.Y.Z` 部分必须一致且可机校验。
- `build_number` **移出 manifest 主体**:版本目录是「需求基线」而非某次构建,单值 build_number 无法表达「本版本对应哪些 build」。build_number 仅在 `snapshots/` 或 release evidence 按节点记录,且不参与 gate digest。
- `inherits_from` / `supersedes` 表达版本目录间继承/取代关系,配合 §6 演进策略。
- `canonical_excludes` 把「哪些子树不进 canonical digest」提升为机器可读字段,替代 `canonical_root: .` 字面会误纳 snapshots/changes 的隐患。

### 2.4 Requirement Body Files(完全沿用既有)

- `requirement-main.md`:single-source §3-§5 的第一/二章主定义,**且必须含 §5.2 核心能力定义**(候选池、正式核心能力清单、字段合同、`P0/P1/P2`、反证、`confirmation_status`)。版本化不豁免该产物。
- `requirement-api.md` / `requirement-cli-command.md`:按 §5.1 适用性逐项目判定创建;guru-template 自身是 CLI 工具,通常适用,不得遗漏 `requirement-cli-command.md`。
- `requirement-non-functional.md`、`modules/*.md`:同既有。
- 编号:需求场景用 `REQ-UC-XXX`,接口用 `API-INTENT-XXX`/`CLI-INTENT-XXX`(§6),遵守编号稳定性规则。**禁止** `REQ-<MODULE>-NNN`。

规则:正式需求正文以这些文件为准;不在 `changes/` 或 snapshot 中维护另一套正文。

### 2.5 `traceability.md`(新增,手维护审计参考)

定位:版本级审计参考,**不是新的追溯主定义,永不作硬 Gate**。

与既有机制的真实关系(经 `overlay/verify/guru_gate.py` 源码核验 `:12-13,:53-56`,不得误述):

- harness `trace-matrix` 是 **task 级**,矩阵列为「`BHV-NNN` × owner × `UNIT-<slug>` × 测试 × 切片」,**不含 `REQ-UC` 列、无多任务聚合入口**(脚本只识别 `BHV-\d+`/`UNIT-slug`,不处理 `REQ-UC`)。
- 因此版本级 traceability **无法**由 `trace-matrix` 直接派生/汇总;二者默认**不自动连通**。traceability 默认为**手维护审计参考**,`Requirement ID` 列人工回填(已知 drift 风险),靠 requirement-review 与完成收敛兜底,而非脚本保鲜。

建议表格(`Requirement ID` 强制用 `REQ-UC-XXX`):

```text
REQ-UC-ID | Source Task | Design Unit(UNIT-<slug>) | Code Entry | Test Evidence | Status
```

- 状态↔drift 映射:`covered`/`partial`/`missing`(需求缺代码)/`orphan_behavior`(代码超出需求)/`untested`(需求缺验证)/`blocked`;不得仅凭测试或结构校验通过即宣称对齐。
- 维护责任人与触发时机在 README/manifest 旁注明(默认随 `change-log.md` 的版本需求变更同步)。
- **自动连通是显式实现前置(非默认)**:需先定义 `REQ-UC ↔ BHV/UNIT` 映射桥 + 扩展 `trace-matrix` 多任务聚合到版本目录;列为后续独立改造,不在本任务范围。

### 2.6 `changes/change-log.md`(沿用既有命名)

沿用 single-source §2 / doc-org 的 `changes/change-log.md`(汇总)+ `changes/changes/`(语义化详细),**不另造** `changelog.md`。条目(示例用 text 块,避免裸 `##` 标题污染文档结构):

```text
[2026-06-26] Podcast UI Sync
Source task: .trellis/tasks/06-26-character-chat-feature-podcast-ui-sync/
Changed requirements: REQ-UC-031(新增 podcast tab 入口行为)
Affected files: modules/requirement-podcast.md, traceability.md
Review/收敛 impact: 按 single-source §12 判定为局部修订;re-review 触发引 gate-confirmation-model + requirement-review(见 §4 / prd REQ-004)
Validation: Widget test pending; Manual QA pending
```

「Review/收敛 impact」不写人工的 digest 失效结论,只声明按 §12/§13 与 review 门禁应触发的动作(见 §5)。

### 2.7 `decisions.md`(新增,划清边界)

只承载「产品/范围级、非架构 ADR、非单条需求确认,又需跨任务跨版本解释」的决策。架构决策走既有 ADR;单条需求确认走核心能力表 `confirmation_status`(含 `user_quote`/`confirmed_ref`)。`decisions.md` 引用上述位置,不重写。

```text
[DEC-001] Purchase History is out of v1.0.0
Status: accepted | Date: 2026-06-26 | Source task: .trellis/tasks/...
Decision: v1.0.0 不含 Purchase History;Restore Purchases 仍必需。
Reason: MVP 优先 entitlement 恢复,非历史账单展示。
Impacted requirements: REQ-UC-052(用 REQ-UC 稳定编号,不用模块前缀)
```

### 2.8 `snapshots/`(新增,不进主链)

关键节点完整快照(requirement-review/RC/release/外部审计),命名含日期与原因。**不**作 canonical root、**不**参与 §13 完成收敛、**不**进 §6 编号差集、**不**进 review 默认入口、**不**进 gate digest(由 `manifest.canonical_excludes` 兜底)。不每日自动生成。

## 3. Explicitly Rejected Default

不采用按日期拆分变更:

```text
versions/<version>/changes/YYYY-MM-DD/    # 拒绝
versions/<version>/YYYY-MM-DD/            # 拒绝
```

理由:日期非稳定业务边界、同版本内出现多个近似入口、误导 agent/reviewer/QA 的 canonical source、对 digest/review_runs/失配恢复不友好。

注意:这里拒绝的是**日期子目录**,不是 `changes/` 本身。既有 `changes/change-log.md + changes/changes/`(语义化)是被沿用的变更承载,本设计不另造 `changelog.md` 替代它。若未来有强审计需求,可用语义文件 `changes/changes/0001-story-chat-local-recovery.md`,但必须声明为变更包、非需求正文、不进 canonical digest。

## 4. Task-To-Requirement Flow

```text
.trellis/tasks/<task>/{prd,design,implement}.md   -> 任务过程、候选变更、执行计划、验证证据
docs/requirements/versions/<version>/             -> 仅沉淀已确认、可复用、跨任务有效的正式产品事实
```

任务完成前按 single-source §12/§13 执行「修订形态判定 + 完成收敛」:

- 不改变正式产品事实:不更新 version requirement。
- 局部修订(§12.1):更新 `versions/<version>/...`、`traceability.md`、`changes/change-log.md`。
- 文档级重构(§12.2):先修正正文主定义/主从边界/编号,再补证据与 review 输出。
- 影响跨版本长期规则:更新 `decisions.md`。
- 改变当前有效版本指针:更新 `docs/requirements/README.md` 与对应 `manifest.status`。
- 是否需要重新 requirement-review:不由 §12/§13 决定,引 `gate-confirmation-model` + requirement-review 门禁(见 prd REQ-004)。

## 5. Guru Gate Impact(区分现状与改造项)

**现状(经 gate-confirmation-model.md 核验,不得误述):**

- `requirements` adversarial review **会读取**正式需求包(连同 `prd.md`、task metadata/jsonl、repo evidence)作为复核证据。
- 但 `requirements` digest **只哈希 `prd.md`**(§artifact digest 表;`requirements digest 只覆盖需求产物`)。因此「改正式需求包」**不会**自动改变 `requirements` digest,也不会自动使 `confirm requirements` 失效。
- clean streak 从当前 digest 的 `review_runs` 重放,不信任手写结论。

**因此本规范的约束:**

- `change-log.md` 与 `traceability.md` **不得**写「digest 已失效 / review 已重跑」这类人工结论(违背 gate 模型「不信任手写结论」)。它们只声明「按 §12/§13 与 review 门禁应触发 requirement-review 复核」。
- 让 review 经 `manifest.canonical_root` 定位正式需求包是**显式实现前置**(现状 `review-baseline` 步骤 0 不消费 manifest,靠调用方指向目录);`snapshots/`、`changes/` 经 `canonical_excludes` 默认排除,供未来 digest/定位使用。
- **可选改造项(显式前置,非默认,留待实现前确认)**:若要让「改正式需求包 → 自动触发 requirements digest 失效 / review 重跑」,需扩展 `guru_gate.py` 把 `manifest.canonical_root`(减 `canonical_excludes`)纳入 `requirements` digest 路径集合。本任务不默认要求该改造;不做时维持「review 读取但 digest 不哈希」的现状。

## 6. Compatibility

- 与既有标准:本设计是 single-source/doc-org 的版本化外层,版本目录内部 100% 兼容既有文档体系、章节、编号与完成收敛口径。
- **版本演进/继承(对应 prd REQ-012)**:默认 **full-copy + diff**——新版本目录从上一版整体复制、自包含完整正文,`change-log.md` 记相对上版 diff,`manifest.inherits_from` 指上一版;接受稳定 `REQ-UC` 跨版本重复正文为已知代价(换单版本自包含可读、digest/review 边界清晰)。**不采用** baseline+delta(单版本读不到完整需求、canonical root 名不副实)。偏离判断锚定 README current-development 指针;released 目录冻结只读;pre-release 后缀归一进 `manifest.status`/`snapshots`,不另开目录。
- 目标项目尚无 `docs/requirements/`:后续实现可只生成模板或文档规范,不强制迁移。
- 已有旧需求目录(扁平、无 versions 层):后续实现先生成迁移计划,把现有内容整体下沉到 `versions/<当前版本>/`,不直接搬动旧文件。
- 已有按日期快照:标记为 historical snapshot 或 change evidence,不作 current root。
- Flutter:版本号来自 `pubspec.yaml` 的 `version: X.Y.Z+N`;目录用 `vX.Y.Z`,`+N`(build number)只进 snapshots/release evidence,不进 manifest 主体/digest。

## 7. Open Implementation Decision

进入实现前需确认本任务落地范围(见 implement.md §5,与 prd Open Questions 对应):

- **档 1(推荐)**:仅更新 Guru spec/workflow 文档与示例,描述「版本化外层 + 既有标准沿用」,不改既有标准包源、不改 gate。
- **档 2**:把版本化升级为既有标准的**正式条目**——细化 `document-organization.md` 的版本与变更管理(含 REQ-012 演进规则)、必要时在 `single-source §2` 把 `versions/` 列入推荐顶层结构,并同步 bundled copy `packages/cli/src/templates/guru/.../requirement-doc-standard/` + `sync:guru`。
- **档 3**:加上 §5 的 `guru_gate.py` requirements digest 扩展(及 §2.5 的 REQ-UC↔BHV 桥)。
- **档 4**:迁移某目标项目现有 requirements 目录。

建议默认档 1;档 2/3/4 按需在后续单独任务推进。**另需 start 前拍板 prd OQ-1:本任务是否仍作独立任务,还是降级并入既有标准包维护(档 2 路径)。** 无论哪档,版本目录内部沿用既有标准这一点不变。
