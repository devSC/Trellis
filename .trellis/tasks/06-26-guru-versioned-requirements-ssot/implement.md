# Implementation Plan: Versioned Requirements SSOT Structure

> 方案 A(补充式):版本化作为既有 `requirement-doc-standard` 的外层 + 治理增量。
> 单一来源:`requirement-doc-standard/references/requirement-structure-single-source.md`、
> `requirement-writing/references/document-organization.md`。版本目录内部沿用既有标准,不重定义。

## 1. Plan

本任务当前停留在 planning 阶段。后续实现必须在用户确认落地档位(§5)后执行 `task.py start`,并遵守当前仓库已有未提交改动边界。

落地档位(与 design.md §7 对齐):档 1 仅改 Guru spec/workflow 文档(推荐);档 2 同步细化既有标准包 overlay + bundled;档 3 扩展 `guru_gate.py` requirements digest;档 4 迁移目标项目。默认先做档 1。

### Slice 1: 规范入口更新(档 1,specs/workflows 文档)

> 档位边界注:档 1 只在 spec/workflow 文档**描述**版本化外层;既有标准包(document-organization/single-source)仍指向旧扁平结构,真正的 SSOT 收敛(让 requirement-writing/review 流程强制新结构)须到档 2。档 1 完成后存在「spec 已描述、标准包未收敛」的暂时不一致,须在文档中显式标注为「档 2 待办」,避免被误读为已生效。

- Scope: Guru workflow / harness / spec 文档说明 full 链正式需求包采用「版本化外层 + 既有标准沿用」。
- Candidate files(均在 `guru-template/specs|workflows/`,**不在 overlay**,无 apply.sh 传染):
  - `guru-template/workflows/guru-client-workflow.md`
  - `guru-template/specs/guru-flutter-client/harness/index.md`
  - `guru-template/specs/guru-flutter-client/README.md`
- Done signal:
  - 文档明确正式需求包默认按 `docs/requirements/versions/<version>/` 组织,**且版本目录内部沿用 single-source §2-§6**。
  - 文档明确全局/版本 README 是既有 §4 版本入口职责的落地,不是新主定义。
  - 文档明确变更沿用既有 `changes/change-log.md + changes/changes/`,仅禁日期子目录;不引入 `changelog.md`。
  - 文档明确版本号语义与演进规则(prd REQ-012:full-copy+diff 继承、偏离基线锚定 README current-development 指针、pre-release 归一)。
  - 文档显式引用 single-source.md 与 document-organization.md。
- Validation:
  - `rg -n "versions/<version>|change-log.md|REQ-UC|requirement-cli-command|核心能力" guru-template/specs guru-template/workflows`(新写法已出现)
  - `rg -n "changes/[0-9]{4}-[0-9]{2}-[0-9]{2}|changelog\.md\b" guru-template/specs guru-template/workflows`(旧/错写法应无命中)

### Slice 2: 既有标准包对齐(档 2,**需用户确认**;改 overlay,风险见 §3)

- Scope: 把版本化升级为既有标准正式条目。
- Candidate files(在 `guru-template/overlay/agents-skills/`,改动触发 apply.sh / bundled 同步):
  - `requirement-writing/references/document-organization.md` —— 细化「版本与变更管理」:`versions/<version>/` 字段、状态、manifest、与完成收敛衔接;明确 `changes/change-log.md + changes/changes/` 不退化为日期目录。
  - `requirement-doc-standard/references/requirement-structure-single-source.md` —— 必要时在 §2 推荐目录把 `versions/` 列为顶层包装层;§4 补 manifest/traceability/decisions/snapshots 的版本级职责;保持核心能力定义 §5.2、编号 §6 不变。
- Done signal:
  - 两份标准包互引一致,`versions/` 与 `changes/` 口径统一。
  - 未改变既有章节承载、核心能力定义、编号契约与完成收敛口径。
- Validation:
  - `rg -n "versions/|change-log.md|snapshots|manifest" guru-template/overlay/agents-skills/requirement-writing guru-template/overlay/agents-skills/requirement-doc-standard`
  - `pnpm -C packages/cli run sync:guru` 后 `git diff --stat packages/cli/src/templates/guru` 核对仅本任务文件。

### Slice 3: 目录模板与字段示例(档 1/2)

- Scope: 在 spec 或 examples 补 canonical directory model 示例。
- Candidate files:
  - `guru-template/specs/guru-flutter-client/harness/`(spec 侧示例)
  - 或既有 `requirement-doc-standard/references/examples/`(若档 2 一并扩展示例,注意 overlay 传染)。
- Done signal:
  - 示例含 `README.md`、`manifest.yaml`、`requirement-cli-command.md`、核心能力定义占位、`traceability.md`、`changes/change-log.md`、`decisions.md`、`snapshots/` 的职责与 `[既有]/[新增]` 标注。
  - 明确 `snapshots/`、`changes/` 不替代 canonical root、不进 digest。
- Validation: `git diff --check`;示例 `Requirement ID` 用 `REQ-UC-XXX`(`rg -nP "REQ-(?!UC-)[A-Z]+-[0-9]"` 应无,即无非 UC 的模块前缀编号)。

### Slice 4: Review / Gate digest 改造(档 3,**需用户确认**,高风险)

- Scope: 仅当确认要让「改正式需求包 → 自动触发 requirements digest 失效」时。
- Candidate files: `guru_gate.py`(requirements digest 路径集合,纳入 `manifest.canonical_root` 减 `canonical_excludes`)。
- Done signal: requirements digest 覆盖版本 canonical root;`snapshots`/`changes` 默认排除;既有 review evidence 重放规则不变。
- Validation: harness 相关测试;`guru_gate.py requirements <task_dir>` 行为回归。
- 默认不做:不做时维持「review 读取正式需求包但 digest 只哈希 prd.md」的现状(design §5)。

### Slice 5: Bundled Copy / Regression Check(若动 guru-template)

- Candidate commands:
  - `pnpm -C packages/cli run sync:guru`(改 guru-template 源后**无条件**执行)
  - `git diff packages/cli/src/templates/guru`(核对源/bundled 一致,因测试不覆盖 spec/skill markdown 一致性)
  - `pnpm -C packages/cli test guru`(或 `pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts`)
- Done signal: 源模板与 bundled copy 一致;相关测试通过或失败有据。

## 2. Validation Checklist

Before reporting implementation complete:

- [ ] `git diff --check`
- [ ] `python3 ./.trellis/scripts/task.py validate 06-26-guru-versioned-requirements-ssot`
- [ ] 若改 `guru-template/`:**无条件** `pnpm -C packages/cli run sync:guru`,并 `git diff packages/cli/src/templates/guru` 核对(测试不兜底 markdown,忘 sync 会静默分叉,见 MEMORY)。
- [ ] 若改 source/bundled Guru 模板:`pnpm -C packages/cli test guru`(或精确 vitest)或记录无法运行的原因。
- [ ] `rg -n "changes/[0-9]{4}-[0-9]{2}-[0-9]{2}"` 在改动范围内无命中(无日期子目录)。
- [ ] `rg -n "changelog\.md\b"` 无命中,且 `rg -nP "REQ-(?!UC-)[A-Z]+-[0-9]"` 无命中(沿用既有 change-log.md;无另造模块前缀编号,排除 REQ-UC)。
- [ ] 版本目录示例含 `requirement-cli-command.md` 与核心能力定义占位(不丢既有必备产物)。
- [ ] 确认未回退任何无关 worktree 改动(§3 清单)。

## 3. Risk Points

- 既有未提交改动(本任务外,不得回退):`guru-template/overlay/apply.sh`、`.trellis/tasks/06-24-guru-arch-bugfix-skill/`、`drafts/guru-arch-bugfix-skill-plan.md`、`guru-template/overlay/agents-skills/guru-arch-bugfix/`。
- **`sync:guru` 传染**:`sync-guru-template.js` 整树 copy,会把含 06-24 改动的 `overlay/apply.sh` 一并刷入 bundled,而 `guru-bundled.test.ts` 对 apply.sh 做源/bundled 严格相等断言,易触发测试红或误提交他人改动。**缓解:档 1 只改 `specs/`、`workflows/`,不碰 overlay,绕开传染;档 2 改 overlay 标准包时,sync 后必须 `git diff` 逐文件核对,只暂存本任务文件。**
- **测试盲区**:`guru-bundled.test.ts` 只断言 apply.sh/verify/*.py,不覆盖 specs/ 与 skill markdown 一致性;忘 sync 则 `pnpm test` 仍全绿、bundled 静默分叉。故 Checklist 用「无条件 sync + git diff 核对」而非「sync 或说明原因」。
- **核心能力定义遗漏**:版本目录若丢 single-source §5.2 核心能力定义,会过不了 requirement-review;模板/示例必须保留占位。
- **digest 改造范围**(档 3):改 `guru_gate.py` 风险高,应作为独立任务,不与文档对齐混在一次。
- Template duplication:`guru-template/` 是源,`packages/cli/src/templates/guru/` 是 bundled copy;单边更新会发布不一致行为。
- Scope creep:先建立规范,不迁移真实目标项目(如 `guru_ai_himora`),除非用户明确要求(档 4)。

## 4. Rollback Plan

- Planning artifacts:仅编辑/删除 `.trellis/tasks/06-26-guru-versioned-requirements-ssot/` 下文件即可回滚。
- 实现期回滚用**逐文件** `git checkout -- <仅本任务改动文件>`;**禁止** `git checkout .` / `git stash` 等全量操作(会波及 §3 无关改动)。
- 禁止操作路径(回滚时不得触碰):`guru-template/overlay/apply.sh`、`.trellis/tasks/06-24-guru-arch-bugfix-skill/`、`drafts/`、`guru-template/overlay/agents-skills/guru-arch-bugfix/`。
- 若 `sync:guru` 产出大范围 bundled 改动,先 `git diff` 审查,只暂存本任务文件,避免提交无关生成churn。

## 5. Open Confirmation Before Implementation

进入实现前确认落地档位(对应 design §7):

> 推荐档 1:仅更新 Guru spec/workflow 文档与示例,描述「版本化外层 + 既有标准沿用」,不改既有标准包源、不改 gate。

Trade-off:

- 档 1 快速给出标准、低风险、绕开 overlay/apply.sh 传染;但不会在既有 requirement-writing/review 流程里强制新结构(那需档 2)。
- 档 2/3/4(改既有标准包 / 改 gate digest / 迁移目标项目)各自独立、风险递增,建议拆成后续单独任务,逐个经用户确认。

## 6. 执行记录(Phase 2)

### Slice 1 — 规范入口更新 ✅(2026-06-27,档 1)

- 新建 `guru-template/specs/guru-flutter-client/harness/requirements/versioned-requirements-package.md`:版本化需求包结构 SSOT(§1 canonical 结构 [既有]/[新增] 标注 + §2 隔离 + §3 README/manifest + §4 变更沿用 changes/change-log + §5 判据归位 + §6 traceability 手维护审计参考 + §7 decisions + §8 snapshots + §9 full-copy+diff 演进 + §10 gate 现状),顶部强制引用 single-source + document-organization。
- 链接接入(仅 specs/workflows,**未碰 overlay**):`harness/index.md` 需求行装载列、`workflows/guru-client-workflow.md`(Planning Artifacts prd 定义 + 1.1 需求阶段)、`specs/guru-flutter-client/README.md` harness 行。
- 验证:rg 新写法 20 命中;`changelog.md`/日期目录仅否定语境;链接可达;`git diff --check` 无空白错误。
- Slice 3(档 1 示例)由新文件 §1 的 [既有]/[新增] 职责标注覆盖;不另建实际 `versions/` 目录(Out Of Scope)。

### Slice 5 — bundled sync ✅(2026-06-28)

- `node packages/cli/scripts/sync-guru-template.js` 同步 bundled;还原 06-24 传染(`git checkout` apply.sh、`rm` guru-arch-bugfix bundled),只留本任务 4 个 bundled 文件。source↔bundled 一致性抽查全过。

### 质检 ✅

- `trellis-check` sub-agent:fixed(1 处措辞自修 §88,无阻断);trace-matrix/gate 关键事实经 `guru_gate.py`/`gate-confirmation-model.md` 源码核验属实、未回退;需求落实 / 既有标准一致 / Slice 1 Done signal / 档 1 边界 / 校验命令全过。

### Spec 回写判断(3.3)

- **无可沉淀**到 `.trellis/spec/`:本任务产物本身即 guru-template spec(`versioned-requirements-package.md`),非「开发 feature 学习」需回写本项目 spec 库;判断已记录。

### 待办

- commit(用户确认,只暂存本任务文件);档 2/3/4 不在本次范围(用户已定档 1)。
