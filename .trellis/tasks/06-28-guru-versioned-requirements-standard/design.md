# Design: Promote versioned requirements into requirement-doc-standard

> 规则来源:档 1 `harness/requirements/versioned-requirements-package.md`(commit `19049a88`)。

## 0. 方案修正(2026-06-28,实现期证伪 OQ-1)

原 OQ-1 倾向「最小侵入 single-source、主改 `document-organization.md`」**被实现证伪**:`requirement-review` 硬前置**只读** `single-source`(`SKILL.md:45`)+ `review-baseline`,**不读** `document-organization`(grep 零命中);规则放 doc-org 会让 review 读不到 → REQ-003(writing/review 都强制)落空。

**定案**:版本化规则**主定义放 `single-source` 新增 §15**(writing/review 都硬前置读它);`document-organization` 与 harness 导读改为**引用 §15**;`single-source §4` 加一句导航指针。**不改核心合同 §5/§6/§12/§13**。

## 1. Approach

软引导 → 硬执行:规则进 `single-source` §15(两个消费方都读),`document-organization`(writing 操作)与 harness(项目侧导读)引用 §15,无重复主定义。

## 2. 改动设计(逐文件)

### 2.1 `single-source.md` 新增 §15(主改,规则主定义)

在 §14 后新增 §15「版本化需求包(可选)」,收敛档 1 规则:15.1 目录结构、15.2 `manifest.yaml`、15.3 `changes/` 禁日期、15.4 `traceability.md` 手维护审计参考、15.5 `decisions.md`、15.6 `snapshots/`、15.7 版本演进 full-copy+diff、15.8 完成收敛附加项。引用本标准 §2-§13。§4 文档职责加一句导航指针到 §15。**§5/§6/§12/§13 核心合同字面不动**。

### 2.2 `document-organization.md` 改引用(writing 操作)

「版本与变更管理」节去规则正文,改为「主定义在 §15」+ 5 步 `requirement-writing` 操作要点;「模块化文档结构」节 `versions/` 一句加指针。

### 2.3 harness `versioned-requirements-package.md` 改导读(OQ-2)

档 1 建的完整规则 → guru-flutter-client **项目侧导读**:结构速览 + 要点(引用 §15)+ §15 不承载的**项目侧 Guru Gate 关系**(requirements digest 只哈希 prd.md、trace-matrix task 级不连通)。workflow/harness/README 对它的链接不变。

## 3. 主从与单一来源

```text
single-source §15（版本化需求包规则主定义,writing/review 硬前置都读）
  ← document-organization「版本与变更管理」（引用 §15 + writing 操作要点）
  ← harness/versioned-requirements-package（项目侧导读 + 项目侧 Gate 关系）
single-source §4 ──导航指针──> §15
```

三处无重复主定义:规则只在 §15。**review 现在经 §15 获得版本化规则(修复 REQ-003)**。

## 4. 向后兼容(REQ-004 守门)

§15 声明 `versions/` **可选**,扁平 `requirements/` 仍默认合法;最小示例不动;`requirement-review` 对扁平结构判定不变(§15 不强制 versions/)。核心合同 §5/§6/§12/§13 字面未改 → 既有撰写/审核行为零变化。

## 5. Bundled & Test

改 overlay(single-source / document-organization)+ specs(harness 导读)后 `node sync-guru-template.js`;按档 1 处理传染(还原 06-24 的 `apply.sh`/`guru-arch-bugfix` bundled,显式路径 `add`);`pnpm -C packages/cli test guru`。

## 6. 风险

- `single-source` 是全局硬前置:只**新增** §15 + §4 一句指针,**不改**核心合同节 → 既有判定零扰动(REQ-004 守门,git diff 逐段确认)。
- overlay 传染(项目 memory `guru-template-bundled-dual-source`)。
- 无重复主定义:规则只在 §15,doc-org/harness 仅引用(check 核对)。

## 7. Open Decisions

- 无遗留;OQ-1 已在 §0 定案,OQ-2(保留导读)已采纳。
