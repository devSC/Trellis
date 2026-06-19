# Guru detail gate deletion audit and skeleton regression

Source issue: https://github.com/devSC/Trellis/issues/6

Reviewed plan:

- `.trellis/tasks/06-19-guru-detail-gate-deletion-audit-issue-6.md`
- `.trellis/tasks/06-19-guru-detail-gate-deletion-audit-issue-6.review.md`

## Goal

Prevent Guru detail review from reporting clean after a destructive detail document rewrite removes still-valid contract obligations. The first shipped fix must add deterministic skeleton regression checks and require deletion-audit evidence for clean `detail` reviews.

This is a harness/process fix. Prompt wording alone is not sufficient.

## Problem

Current `guru_gate.py detail` checks combined detail text for broad global tokens such as UNIT, behavior, failure handling, test mapping, and do-not-invent wording. A compressed endpoint table can satisfy those global tokens even when a chapter loses required L1 sections such as `行为定义`, `逐行为设计`, `测试映射`, and `不得补造清单`.

Current `record-review detail` also persists only free-text evidence. A reviewer can record a clean detail review without saying whether destructive edits removed obsolete facts, moved still-valid contracts, or accidentally deleted contract obligations.

The observed incident came from Flutter API alignment, but the shared Guru detail gate and review evidence model are platform-neutral. The fix must cover the existing Guru platforms: Flutter, Go, iOS, and H5.

## Requirements

- R1. Destructive detail edits must preserve L1 contract obligations. Obsolete interface facts may be removed, but still-valid contract categories must remain, move to a named replacement section, or be marked N/A with a reason.
- R2. Protected categories include L1 skeleton sections, UNIT definitions, BHV coverage, behavior lists, input/output/error contracts, state owner statements, dependency positive/negative statements, failure handling, events/postconditions, test mappings, and non-goal/do-not-invent constraints.
- R3. The `detail` gate must catch obvious L1 skeleton regressions in the current detail gate scope. It must not become a repository-wide historical document scan or a semantic markdown diff engine.
- R4. Clean `record-review detail` runs must require a structured deletion audit summary through `--deletion-audit`.
- R5. `none` is valid only when the reviewer asserts no destructive deletion was in scope.
- R6. Detail review skills must add D9 deletion audit and block clean reviews when large deletions lack replacement explanation, L1 sections disappear, endpoint/interface coverage is treated as behavior coverage, or UNIT/BHV tokens remain while behavior contract content is flattened.
- R7. Detail writing skills must instruct agents to build a deletion ledger before destructive detail rewrites and preserve the L1 skeleton while replacing stale facts.
- R8. `guru_supervise.py` must prompt detail reviewers to record deletion audit evidence.
- R9. Both template surfaces must stay synchronized:
  - `guru-template/**`
  - `packages/cli/src/templates/guru/**`
- R10. The harness customization must be recorded in both `trellis-local/SKILL.md` copies.

## Non-Goals

- No full semantic markdown diff engine.
- No automatic decision on whether a business rule remains valid after backend contract changes.
- No Git-history requirement for agents.
- No broad non-Guru Trellis workflow rewrite.
- No change to `_gate_digest()` unless implementation proves it unavoidable.

## Acceptance Criteria

- [x] A detail chapter that keeps UNIT/BHV tokens but loses required L1 skeleton sections fails `guru_gate.py detail`.
- [x] Correct cleanup that removes stale endpoint facts while preserving behavior contracts and L1 skeleton passes.
- [x] `record-review detail --result clean` without `--deletion-audit` exits non-zero.
- [x] `record-review detail --result clean --deletion-audit "none"` succeeds for a non-destructive review.
- [x] Review output/status preserves deletion-audit visibility for later agents.
- [x] Flutter, Go, iOS, and H5 detail review skills include D9 deletion audit.
- [x] Flutter, Go, iOS, and H5 detail writing skills include destructive edit preservation/deletion ledger guidance.
- [x] L1 detail structure docs mention destructive edit preservation.
- [x] Existing Guru shell fixture tests cover the false-green regression and the new review evidence requirement.
- [x] `guru-template/**` and `packages/cli/src/templates/guru/**` remain synchronized for touched files.
- [x] GitNexus `detect_changes()` is run before commit.

## Notes

- The reviewed local plan completed three review rounds. Round 1 found and fixed two medium issues; rounds 2 and 3 found only minor documentation precision issues.
- `_gate_digest()` was identified as high risk in preliminary GitNexus impact analysis and should be avoided for the first version.
