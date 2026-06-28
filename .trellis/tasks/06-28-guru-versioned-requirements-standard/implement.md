# Implementation Plan: Promote versioned requirements into requirement-doc-standard

> 本任务即「档 2」。改 overlay 标准包,必经 sync + 传染处理(档 1 经验)。
> **方案修正见 design §0**:原 OQ-1「主改 doc-org」被实现证伪(`requirement-review` 不读 doc-org),改为规则主定义放 `single-source` §15。

## 1. Plan

### Slice 1: `single-source.md` 新增 §15(主改,规则主定义)

- Candidate: `guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`
- Done signal: §14 后新增 §15「版本化需求包」(15.1-15.8 全部版本化规则,引用本标准 §2-§13);§4 加导航指针;**§5/§6/§12/§13 核心合同字面未改**。
- Validation: `grep "## 15."`;`git diff` 确认核心节未动。

### Slice 2: `document-organization.md` 改引用 §15

- Candidate: `guru-template/overlay/agents-skills/requirement-writing/references/document-organization.md`
- Done signal: 「版本与变更管理」节去规则正文、改为「主定义在 §15」+ `requirement-writing` 操作要点;「模块化文档结构」节 `versions/` 一句加指针。
- Validation: `grep "§15"`;无重复规则正文。

### Slice 3: harness 导读改引用(OQ-2)

- Candidate: `guru-template/specs/guru-flutter-client/harness/requirements/versioned-requirements-package.md`(档 1 建)
- Done signal: 改项目侧导读;结构速览 + 要点引用 §15 + 项目侧 Guru Gate 关系;workflow/harness/README 链接可达。
- Validation: `rg "§15"`;链接可达。

### Slice 4: bundled sync + 传染 + 回归

- `node packages/cli/scripts/sync-guru-template.js`
- 还原传染(`git checkout` apply.sh、`rm` guru-arch-bugfix bundled),`git diff packages/cli/src/templates/guru` 核对仅本任务
- `pnpm -C packages/cli test guru`(或精确 vitest)

## 2. Validation Checklist

- [ ] `git diff --check`
- [ ] `python3 ./.trellis/scripts/task.py validate 06-28-guru-versioned-requirements-standard`
- [ ] 改 overlay → **无条件** sync + `git diff packages/cli/src/templates/guru` 核对(测试不兜底 skill md)
- [ ] `single-source.md` 仅 §4 加指针 + 新增 §15(§5/§6/§12/§13 核心节字面未动 —— `git diff` 逐段确认)
- [ ] `document-organization` / harness 改引用 §15,无重复主定义
- [ ] **review 经 `single-source §15` 能读到规则**(修复原方案缺陷)
- [ ] 扁平结构向后兼容;最小示例不破坏
- [ ] `guru-bundled.test.ts` 通过或失败有据
- [ ] 未回退 06-24 / 06-26 已有改动

## 3. Risk Points

- **硬前置全局影响**:`single-source` 是 writing/review 硬前置 → 只**新增** §15 + §4 一句指针,**不改**核心合同 → 既有判定零扰动(REQ-004 守门,git diff 逐段确认)。
- **overlay 传染**(同档 1):sync 整树带入 06-24 及任何其他未提交 overlay 改动 → 还原 + 显式 `add`,勿 `git add -A`。
- **无重复主定义**:规则只在 §15,doc-org/harness 仅引用(check 核对)。

## 4. Rollback Plan

- 逐文件 `git checkout -- <仅本任务文件>`;**禁** `git checkout .` / `git stash`。
- 禁止触碰:06-24 改动(apply.sh / guru-arch-bugfix / 06-24 task / drafts)、06-26 已提交内容。
- sync 大范围 bundled 改动先 `git diff` 审查,只 `add` 本任务文件。

## 5. 执行记录(Phase 2)

### 方案修正(2026-06-28)

- Slice 1 起初按原 OQ-1 把规则写进 `document-organization.md`;实现中 grep 发现 `requirement-review` 硬前置只读 single-source、**不读 document-organization** → 规则放 doc-org 会让 review 读不到(REQ-003 落空)。**改为规则主定义放 `single-source` §15**(design §0),doc-org 改引用。

### 已完成(Slice 1-3)

- `single-source.md` §14 后新增 §15「版本化需求包」(15.1-15.8 规则主定义)+ §4 导航指针;核心合同 §5/§6/§12/§13 未改。
- `document-organization.md`「版本与变更管理」节改为引用 §15 + writing 操作要点;「模块化文档结构」节 `versions/` 加指针。
- harness `versioned-requirements-package.md` 改项目侧导读(结构速览 + 引用 §15 + 项目侧 Guru Gate 关系)。

### Slice 4 + 质检 ✅(2026-06-28)

- bundled sync:`node sync-guru-template.js` + 还原 06-24 传染(`git checkout` apply.sh、`rm` guru-arch-bugfix bundled);3 组 source↔bundled `diff -q` 字节一致。
- 质检:`trellis-check` sub-agent **pass**(无 self-fix)。核心合同 §5/§6/§12/§13 字面零改动(single-source git diff 仅 +85/-0,两处 hunk);REQ-003 修复到位(规则在 review 可读的 §15);无重复主定义;向后兼容;边界干净;格式无破损。

### Spec 回写判断(3.3)

- **无可沉淀**到 `.trellis/spec/`:本任务产物即 requirement-doc-standard 标准包改动(§15),非「开发 feature 学习」需回写本项目 spec 库。

### 待办

- commit(用户确认,只暂存本任务文件)。
