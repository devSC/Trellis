# Issue #6 Local Plan: Guru detail gate deletion audit and skeleton regression

> Source issue: https://github.com/devSC/Trellis/issues/6
> Status: planning document only. No code changes have been made for this issue.
> Boundary: this document is intentionally separate from the currently active task `06-18-guru-five-phase-automation-issue-2`.

## 1. Problem Statement

Guru/Trellis detail review can currently report clean even after a destructive documentation rewrite removes still-valid detail design contracts.

Observed failure mode:

- A Flutter v1.0.0 backend API alignment task had valid behavior-level detail contracts: UNIT ownership, BHV coverage, repository mapping behavior, API error propagation, local datasource behavior, upload gateway behavior, test mapping, and non-goal constraints.
- Backend contract facts changed, so stale endpoint details needed to be removed or rewritten.
- During endpoint-first cleanup, a contract-heavy chapter was compressed into an endpoint mapping table.
- Stale facts were removed correctly, but still-valid behavior contracts were removed too.
- Multiple review rounds and the detail gate still passed because the system checked endpoint coverage, chapter existence, broad trace tokens, and global keywords instead of semantic preservation of required contract blocks.

User-visible risk:

- The agent can say requirements/design/detail are aligned while the implementable detail contract has become thinner.
- Product owner must manually notice that sections such as `行为定义` disappeared.
- This creates false confidence at the design gate and can lead implementation agents to build from a weakened contract.

This is a harness/process gap, not primarily a prompt wording issue.

## 2. Current Repository Findings

Current evidence from the local checkout:

- `guru_gate.py` owns structural gates and review evidence persistence.
- `check_detail()` currently checks detail content by scanning the combined detail text for broad patterns:
  - UNIT definition
  - `承接...行为`
  - `失败...收口`
  - `测试映射|哪些测试`
  - `不得...补造|不在此补造`
- This global scan can pass when only a compressed mapping table remains and a specific chapter has lost required L1 skeleton sections.
- Flutter detail L1 already defines the required chapter skeleton:
  - `## 1. 单元职责`
  - `## 2. 行为定义`
  - `## 3. 核心数据结构`
  - `## 4. 逐行为设计`
  - `## 5. 状态管理` or explicit N/A where allowed
  - `## 6. Widget 设计` or explicit N/A where allowed
  - `## 7. 测试映射`
  - `## 8. 不得补造清单`
- Detail review skills currently define D1-D8 diagnostics. They do not define D9 deletion audit.
- `record-review` stores only a free-text `evidence` summary and has no structured deletion-audit field.
- `guru_supervise.py` prompts reviewers to record clean evidence, but does not require deletion audit evidence.
- `trellis-local/SKILL.md` is the local customization registry for Guru harness changes.
- All four Guru platforms use the shared `guru_gate.py` detail gate. Flutter, Go, iOS, and H5 detail L1 files all define the same universal chapter skeleton shape: responsibilities, behavior definition, core data structure, per-behavior design, state/boundary section, type-specific section, test mapping, and do-not-invent list.
- `record-review detail` is platform-neutral. If the CLI requires deletion audit for clean detail reviews, all platform detail review/writing skills must be taught to produce that evidence, not only Flutter.

Important implementation constraint:

- `guru-template/**` and `packages/cli/src/templates/guru/**` are mirrored template surfaces. Any shipped change must update both.

## 3. Product Requirements

### R1. Destructive Edit Preservation

When a detail design chapter is rewritten, interface facts may be removed or replaced, but L1-required contract obligations must remain, move to a named replacement section, or be marked N/A with a reason.

Required protected content categories:

- L1 detail skeleton sections
- UNIT definitions
- BHV coverage
- behavior lists
- input/output/error contract
- state owner statements
- dependency positive/negative statements
- failure handling
- events/postconditions
- test mappings
- non-goal / do-not-invent constraints

### R2. Deletion Ledger

For large or destructive detail document edits, review evidence must include a deletion ledger.

Minimum ledger fields:

| Field | Meaning |
|-------|---------|
| deleted_category | What kind of content was removed |
| reason | Why it was removed |
| replacement_location | Where the equivalent contract now lives, or N/A |
| removes_contract_obligation | Whether the deletion removes a still-valid contract |
| reviewer_decision | replaced / superseded / intentional N/A / blocking loss |

### R3. Skeleton Regression Gate

The detail gate must catch obvious L1 skeleton regressions before clean review evidence can be trusted.

The gate should remain deterministic and lightweight. It should not attempt full semantic equivalence.

### R4. Review Diagnostic D9

Detail review skills must add D9 deletion audit.

D9 blocks clean review when:

- large deletions lack replacement explanation
- L1-required contract sections disappear
- endpoint/interface coverage is treated as behavior coverage
- UNIT/BHV references remain but behavior contract content is flattened

### R5. Evidence Model

Clean detail review evidence must include a deletion audit summary.

The status/reporting path should preserve existing clean/finding behavior while making deletion audit visible to later agents.

### R6. Scope Control

First version focuses on Guru detail design documents across the existing Guru platforms. The Flutter API-alignment incident is the primary regression fixture, but the shared gate must remain compatible with Go, iOS, and H5 detail skeletons. The check applies to the current `detail` gate/review scope, not to an unrelated background sweep of every historical document. This must not become a general semantic markdown diff engine.

## 4. Non-Goals

- Build a full semantic markdown diff engine.
- Prove every rewritten behavior is semantically equivalent to old content.
- Automatically decide whether a business rule is still valid after backend contract changes.
- Change non-Guru Trellis workflows unless they share the same detail gate mechanism.
- Require Git history in every agent environment.
- Block small typo edits or additive-only documentation edits.
- Replace human review.
- Rework the whole trace matrix system.
- Change user prompts as the main fix.

## 5. Proposed Design

### 5.1 Small Detail Chapter Skeleton Analyzer

Add a small analyzer inside `guru_gate.py`.

Add two small helpers inside `guru_gate.py`:

```python
def detail_chapter_blocks(task_dir: str) -> list[tuple[str, str]]:
    ...

def analyze_detail_chapter_skeleton(name: str, text: str) -> list[str]:
    ...
```

`detail_chapter_blocks()` owns block enumeration so callers do not need to know the full/light storage format. `analyze_detail_chapter_skeleton()` owns the deterministic per-block skeleton checks.

Input to the analyzer:

- markdown text for each detail chapter
- optional platform doc type context if available from chapter header or design-main index

Output:

- missing section findings
- missing token findings
- N/A findings where a required section is absent without explicit N/A reason

Expected checks:

- chapter contains at least one `UNIT-<slug>` definition
- chapter contains `BHV-NNN` references unless explicitly N/A by contract
- universal section headings or accepted aliases exist:
  - `单元职责`
  - `行为定义`
  - `核心数据结构`
  - `逐行为设计`
  - `状态管理` / `状态与事务` / `状态 / 边界管理`
  - platform type-specific section such as `Widget 设计`, `View 设计`, `导航设计`, `数据合同`, `路由 / 渲染 / SEO`, or explicit N/A
  - `测试映射`
  - `不得补造`
- important contract tokens exist in the relevant chapter body:
  - behavior definition/list
  - failure handling
  - test mapping
  - non-goal/do-not-invent statement
- absent optional sections must use `N/A` / `不适用` with a reason.

The analyzer should not judge whether behavior wording is correct. It only catches obvious skeleton loss.

### 5.2 `check_detail()` Integration

Update `check_detail()`:

- full chain: analyze each chapter in the current design package independently; this is the current detail gate scope.
- light chain: analyze detail chapter blocks under `design.md` §2; do not treat each `UNIT-` heading as a full chapter because section headings usually wrap one or more UNIT blocks.
- fallback: if light-chain headings cannot be split reliably, analyze the whole detail section as one block and still keep the existing UNIT/BHV trace checks.
- report exact chapter name in gate failures.
- keep existing trace checks for ghost BHV and behavior-without-unit.

This prevents a single remaining endpoint table or another chapter from satisfying global keywords for all chapters.

### 5.3 Deletion Audit Field For Review Evidence

Extend `record-review detail` with a minimal option:

```bash
--deletion-audit "<summary>"
```

Rules:

- Required for `record-review detail --result clean`.
- Optional for findings, but recommended.
- `none` is valid only when the reviewer asserts no destructive deletion was in scope.
- Store as `deletion_audit` in each review run record.
- Include it in status output when present.

Do not change `_gate_digest()` in the first version. GitNexus impact analysis marks `_gate_digest` as high-risk because it affects confirm/status/check/review state. The safer low-risk touch points are `check_detail()` and `_record_review()`.

### 5.4 D9 Review Diagnostic

Update all platform detail review skills:

- Add D9 to the diagnostic flow.
- Require deletion audit in review output.
- Require reviewers to distinguish:
  - obsolete interface fact removed
  - contract moved to named replacement
  - contract intentionally N/A with reason
  - behavior contract lost
- Treat missing replacement for still-valid contracts as blocking P1.

### 5.5 Writing SOP

Update detail writing guidance for backend/API alignment work:

1. Extract backend/interface facts.
2. Extract current document skeleton and contract tokens.
3. Build deletion ledger before editing.
4. Replace stale facts inside the existing L1 skeleton.
5. Run endpoint/interface diff checks.
6. Run skeleton-regression checks.
7. Run Guru gate.
8. Record review evidence with deletion audit summary.
9. Final response includes deletion risk summary.

This SOP belongs in every platform detail-writing skill where destructive detail rewrites are possible. Flutter remains the required regression path, but Go backend API alignment is also in scope.

## 6. File Impact Plan

Core scripts:

- `guru-template/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/guru_supervise.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`

Detail standards and skills:

- `guru-template/specs/guru-flutter-client/harness/detail/detail-structure-single-source.md`
- `guru-template/specs/guru-go-backend/harness/detail/detail-structure-single-source.md`
- `guru-template/specs/guru-ios-native/harness/detail/detail-structure-single-source.md`
- `guru-template/specs/guru-h5-web/harness/detail/detail-structure-single-source.md`
- matching files under `packages/cli/src/templates/guru/specs/**`
- `guru-template/overlay/agents-skills/client-design-detail-writing/SKILL.md`
- `guru-template/overlay/agents-skills/go-design-detail-writing/SKILL.md`
- `guru-template/overlay/agents-skills/ios-design-detail-writing/SKILL.md`
- `guru-template/overlay/agents-skills/h5-design-detail-writing/SKILL.md`
- matching writing skills under `packages/cli/src/templates/guru/overlay/agents-skills/**`
- `guru-template/overlay/agents-skills/client-design-detail-review/SKILL.md`
- `guru-template/overlay/agents-skills/go-design-detail-review/SKILL.md`
- `guru-template/overlay/agents-skills/ios-design-detail-review/SKILL.md`
- `guru-template/overlay/agents-skills/h5-design-detail-review/SKILL.md`
- each matching review skill under `packages/cli/src/templates/guru/overlay/agents-skills/**`
- each detail-review `references/review-baseline.md` and `references/review-output.md` for all four platforms, in both template copies.

Local customization registry:

- `guru-template/overlay/trellis-local/SKILL.md`
- `packages/cli/src/templates/guru/overlay/trellis-local/SKILL.md`

Tests:

- `guru-template/overlay/verify/tests/run_tests.sh`
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
- `packages/cli/test/guru/guru-bundled.test.ts` if packaging/ship assertions need to cover new strings or CLI option presence.

## 7. Test Plan

Use the existing shell fixture runner. Do not introduce a new test framework.

### T1. Regression: false-green skeleton loss

False-green regression fixture:

- detail chapter keeps endpoint mapping table and `UNIT/BHV` tokens
- deletes `行为定义`, `逐行为设计`, `测试映射`, and `不得补造清单`

Expected:

- `python3 guru_gate.py detail <task_dir>` exits 2
- output names the affected chapter and missing sections

### T2. Passing replacement

Fixture:

- obsolete endpoint facts are removed
- behavior definitions, UNIT/BHV traceability, error handling, datasource behavior, upload gateway behavior, test mapping, and non-goal constraints are rewritten inside L1 skeleton

Expected:

- detail gate passes

### T3. Explicit N/A

Fixture:

- a section is intentionally N/A with a reason

Expected:

- detail gate passes when N/A satisfies L1 contract

### T4. Missing deletion audit

Fixture:

- run `record-review detail --result clean` without `--deletion-audit`

Expected:

- command exits 2

### T5. Present deletion audit

Fixture:

- run `record-review detail --result clean --deletion-audit "none"` for a non-destructive review
- run another clean with a real audit summary for a destructive rewrite

Expected:

- records are written
- status/reporting can display deletion audit summary

### T6. Correct cleanup is not blocked

Fixture:

- stale interface facts are deleted and replaced by a clearly named endpoint contract section while L1 behavior skeleton remains

Expected:

- no false positive

## 8. Validation Commands

Targeted checks:

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
pnpm --filter @devsc/trellis test -- guru-bundled.test.ts
node .gitnexus/run.cjs detect_changes --repo "/Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree"
```

Optional broader checks if touched files expand:

```bash
pnpm --filter @devsc/trellis test
pnpm --filter @devsc/trellis typecheck
```

Do not rely on root scripts that still target stale package filters. Use `@devsc/trellis` in this fork.

## 9. Acceptance Criteria

- A detail chapter that loses required L1 skeleton sections cannot pass `guru_gate.py detail`.
- A clean detail review cannot be recorded without deletion audit evidence.
- Review guidance includes D9 deletion audit and blocks missing replacement for still-valid contract content.
- API/backend alignment writing guidance instructs agents to replace stale facts inside the existing skeleton.
- Tests reproduce the observed false-green class and prove correct cleanup still passes.
- Both Guru template copies stay synchronized.
- `trellis-local` changelog records the harness customization.
- GitNexus `detect_changes()` is run before commit if implementation proceeds.

## 10. Recommended Implementation Order

1. Create or activate a dedicated Trellis task for issue #6 before code changes.
2. Add failing shell fixture for skeleton loss.
3. Add skeleton analyzer and integrate it into `check_detail()`.
4. Add `--deletion-audit` parsing and persistence for detail review runs.
5. Update `guru_supervise.py` prompt text to require deletion audit on clean detail review.
6. Update detail L1 and detail writing/review skills for Flutter, Go, iOS, and H5.
7. Update `trellis-local` changelog.
8. Sync `guru-template/**` to `packages/cli/src/templates/guru/**`.
9. Run targeted tests.
10. Run GitNexus impact/detect changes before commit.

## 11. Risk Notes

- `check_detail()` impact is low: direct caller is the gate command/auto path.
- `_record_review()` impact is low: direct caller is `main`.
- `_gate_digest()` impact is high and should not be changed for this issue unless a later implementation proves it unavoidable.
- The main compatibility risk is over-blocking older detail docs. Limit blocking behavior to the current detail gate/review scope; do not add a repository-wide historical document scan. If changed-file detection is unavailable, require manual deletion audit for the current review scope instead of inferring all deletions automatically.
