# Promote versioned requirements rules into requirement-doc-standard

## Goal

把档 1(`06-26-guru-versioned-requirements-ssot`,commit `19049a88`)定义的版本化需求包规则,从「Guru spec 侧软引导」**提升为** `requirement-doc-standard` 标准包的正式部分,使 `requirement-writing` / `requirement-review` 在硬前置装载标准包时即获得并**强制执行**版本化规则,而非仅靠 workflow 链接软引导。

这是档 1 prd `OQ-1` 的「档 2 路径」,解决档 1 留下的执行缺口。

## Background

- 档 1 已交付版本化规范 SSOT:`guru-template/specs/guru-flutter-client/harness/requirements/versioned-requirements-package.md`,并从 workflow/harness/README 链接。**它是档 2 的规则来源**。
- 但 `requirement-writing`(`SKILL.md` 执行规则 1:必读 `requirement-structure-single-source.md`)与 `requirement-review`(硬前置只读 `single-source` + `review-baseline`)**只装载 `requirement-doc-standard` 标准包**,不读 harness 侧的版本化规范。
- 现状:agent 走 workflow 会被软引导看到版本化,但撰写/审核 skill **不强制**按 `versions/` 产出/审核。档 2 把规则写进标准包,闭合此缺口。

## Confirmed Facts(承接档 1)

- 版本化是既有 `document-organization.md` 已有的轻定义(`versions/` 第 32 行、`changes/change-log.md` 第 68-75 行),档 2 是**细化而非发明**。
- 版本目录内部章节承载、核心能力定义 §5.2、编号契约 §6、完成收敛 §13 **不变**。
- **关键(实现期证实)**:`requirement-review` 硬前置只读 `single-source`、**不读** `document-organization`(grep 证实)。故版本化规则要让 review 读到,必须放在 single-source —— 见 OQ-1 定案。
- 标准包在 `guru-template/overlay/agents-skills/` 下,改它触发 `apply.sh` 传染 + bundled sync(项目 memory `guru-template-bundled-dual-source`);档 1 实测 `sync:guru` 整树会带入他人未提交 overlay 改动,需还原传染、只暂存本任务文件。

## Requirements

### REQ-001: `single-source.md` 新增 §15「版本化需求包」(主改动,规则主定义)

把档 1 `versioned-requirements-package.md` 的版本化外层规则收敛进 `single-source.md` **新增 §15**(在 §14 后):目录结构、`manifest.yaml`、`changes/change-log.md` 禁日期、`traceability.md`(手维护审计参考)、`decisions.md`/`snapshots/`、full-copy+diff 演进、完成收敛附加项。引用本标准 §2-§13,**不改核心合同 §5/§6/§12/§13**。

规则放 §15(而非 doc-org)的原因:`requirement-review` 硬前置只读 single-source、不读 document-organization,规则在 §15 才能让 writing/review 都读到(见 OQ-1 证伪记录)。

### REQ-002: `document-organization.md` 与 harness 导读改引用 §15

`document-organization.md`「版本与变更管理」节去规则正文、改为「主定义在 §15」+ `requirement-writing` 操作要点;档 1 harness `versioned-requirements-package.md` 改为项目侧导读(结构速览 + 引用 §15 + 项目侧 Guru Gate 关系)。`single-source §4` 加一句导航指针到 §15。三处无重复主定义。

### REQ-003: writing/review 经标准包自动获得版本化规则

规则进 single-source §15 后,`requirement-writing` 撰写时按 `versions/` 组织、`requirement-review` 审核时检查版本化结构——**无需改两个 skill 的 `SKILL.md` 正文**(它们已硬前置读 single-source)。

### REQ-004: 既有语义零破坏 + 向后兼容

不改变既有章节承载、核心能力定义 §5.2、编号契约 §6、完成收敛 §13、API/CLI 适用 §5.1 的任何判定口径。版本化是**外层叠加**(§15 声明 `versions/` 可选):扁平结构仍是合法形态,既有项目与最小示例不受影响。

### REQ-005: bundled 同步 + 回归

改 overlay 标准包(single-source / document-organization)+ specs(harness 导读)后 `sync:guru`,按档 1 经验处理传染(`git diff` 核对、还原他人改动、显式路径只暂存本任务),过 `guru-bundled.test.ts` 相关断言。

### REQ-006: 无重复主定义 + 主从清晰

`single-source §15`(规则主定义)、`document-organization`(引用 §15 + writing 操作)、harness `versioned-requirements-package.md`(项目侧导读)三处必须口径一致、无重复主定义、互相引用关系清晰。

## Acceptance Criteria

- [ ] `single-source.md` 新增 §15 含完整版本化规则,与档 1 `versioned-requirements-package.md` 口径一致;核心合同 §5/§6/§12/§13 字面未改(`git diff` 逐段确认)。
- [ ] `document-organization.md`「版本与变更管理」节 + harness 导读改为引用 §15,无重复主定义;`single-source §4` 加导航指针。
- [ ] `requirement-writing`/`requirement-review` 不改 `SKILL.md` 正文即可经 `single-source §15` 获得规则(**review 也能读到** —— 修复原方案缺陷)。
- [ ] 扁平结构(无 `versions/`)仍通过 `requirement-review`(向后兼容);最小示例不被破坏。
- [ ] bundled 同步,`git diff packages/cli/src/templates/guru` 核对仅本任务,传染已还原。
- [ ] `guru-bundled.test.ts` 通过或失败有据。

## Out Of Scope

- 不改 `guru_gate.py` / gate digest(档 3)。
- 不迁移任何真实项目 requirements 目录(档 4)。
- 不重写既有标准包的核心能力定义/编号/章节承载/完成收敛口径。
- 不定义 `REQ-UC ↔ BHV` 桥(档 3 前置)。

## Open Questions

- **OQ-1(已在实现中定案,2026-06-28)**:原倾向「最小侵入、主改 doc-org」**被实现证伪** —— `requirement-review` 硬前置只读 `single-source`、**不读** `document-organization`(grep 证实),规则放 doc-org 会让 review 读不到(REQ-003 落空)。**定案:版本化规则主定义放 `single-source` 新增 §15(writing/review 都读),`document-organization` 与 harness 导读改引用 §15,`single-source §4` 加导航指针;不改核心合同 §5/§6/§12/§13。**
- **OQ-2(已采纳)**:harness `versioned-requirements-package.md`(档 1)**保留为项目侧导读**(避免 workflow/harness/README 链接断裂),去重正文改为引用 §15,保留结构速览 + 项目侧 Guru Gate 关系。

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`(本轮 planning)
- Repository evidence inspected:
  - 档 1 `versioned-requirements-package.md`(规则来源)+ 档 1 prd/design
  - `requirement-doc-standard/references/requirement-structure-single-source.md`(主改目标:新增 §15)、`requirement-writing/references/document-organization.md`(改引用)
  - `requirement-writing/SKILL.md`、`requirement-review/SKILL.md` + `review-baseline.md`(硬前置链路:**两者都只读 single-source**)
- Domain/terminology triggers:
  - 「软引导 vs 硬执行」:档 1 在 workflow 链接=软引导;档 2 写进标准包硬前置=硬执行。
- Current code vs user intent conflicts:
  - 实现期发现:`requirement-review` 不读 `document-organization` → 原「主改 doc-org」方案会让 review 读不到规则 → 改放 `single-source §15`。
- Product decisions confirmed:
  - 档 2 路径成立;本任务即「档 2」。
  - **规则主定义放 `single-source §15`**(原「最小侵入 doc-org」被证伪);不改核心合同。
  - harness spec 保留为项目侧导读(OQ-2)。
- Open product/scope/risk questions:
  - 无遗留;OQ-1/OQ-2 均已定案。
