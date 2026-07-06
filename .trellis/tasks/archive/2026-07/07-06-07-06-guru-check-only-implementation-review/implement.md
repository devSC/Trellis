# Fix Guru Check-Only Implementation Review Record Flow - Implementation Plan

## Preconditions

- Do not start implementation until the user explicitly approves after reviewing this plan.
- Before editing any function/class/method, run GitNexus impact analysis for the target symbol and report the blast radius.
- Keep unrelated dirty files (`AGENTS.md`, `CLAUDE.md`, `marketplace`) untouched.
- Keep task artifacts out of the final implementation commit unless a separate tooling/docs commit is explicitly planned.

## Ordered Work / 切片计划

Implementation slices are tied to the detailed design units:

- UNIT-review-target-resolution: review target resolution and digest source selection.
- UNIT-check-only-supervision: `implementation-review` command, check-only run plan, and mutable evidence prompt boundary.
- UNIT-commit-gate-plan: commit-plan/check-commit recovery guidance and fail-fast invalid-scope behavior.

## 执行范围和改动文件

1. Inspect live code paths and tests:
   - `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
   - `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
   - `packages/cli/src/templates/guru/overlay/verify/guru_review_record.py`
   - `packages/cli/test/guru/guru-bundled.test.ts`
   - Guru workflow templates under `packages/cli/src/templates/guru/workflows/`
   - `guru-template/` mirror files

2. Add the ReviewTarget helper:
   - Resolve slice packet targets.
   - Resolve staged/contract-derived targets.
   - Centralize target path, invariant, deterministic check, provider, and digest source handling.

3. Add `implementation-review` supervisor path:
   - Parser entry and dry-run output.
   - Check-only execution plan.
   - Deterministic checks.
   - Check worker verdict parsing.
   - Record normalization and append.
   - No implement worker launch.

4. Update commit gate guidance:
   - Replace `rerun implement-check` suggestions with `implementation-review --staged` or `implementation-review --slice <UNIT>`.
   - Keep `check-commit` read-only.
   - Keep `commit-plan` and `check-commit` decision model aligned.
   - Do not recommend `implementation-review` while staged scope / gate contract / implementation lifecycle preflight is already invalid.

5. Update mutable evidence prompt text:
   - Remove "keep implement.md evidence current" from post-detail worker instructions.
   - Add append-only evidence guidance.
   - Preserve detail-gate rollback if planning artifacts must change.

6. Update workflow/spec templates:
   - Document `implementation-review` as Phase 2.2 / commit-safe evidence producer.
   - Keep `implement-check` as Phase 2 implement/check repair loop.
   - Sync `packages/cli/src/templates/guru/...` and `guru-template/...`.

7. Add regression tests:
   - New check-only dry-run and record writer cases.
   - Commit-plan/check-commit blocker text cases.
   - Commit-plan invalid-scope case that blocks before recommending check-only review.
   - Staged digest acceptance.
   - Mutable evidence digest boundary.

8. Run validation:
   - `pnpm --filter @devsc/trellis run sync:guru:check`
   - `pnpm --filter @devsc/trellis test -- guru-bundled`
   - `pnpm --filter @devsc/trellis run lint:py`
   - `pnpm --filter @devsc/trellis typecheck`
   - `git diff --check`
   - GitNexus `detect_changes()` before commit.

## 证据 / analyze / test

- Python syntax: `python3 -m py_compile` for touched Guru overlay scripts.
- Template sync: `pnpm --filter @devsc/trellis run sync:guru:check`.
- Regression suite: `pnpm --filter @devsc/trellis test -- guru-bundled`.
- TypeScript: `pnpm --filter @devsc/trellis typecheck` and `pnpm --filter @devsc/trellis lint`.
- Diff hygiene: `git diff --check`.
- Impact check: GitNexus `detect-changes --scope all`.

## 阻塞与偏差

- Current known blocker: full Python `lint:py` has pre-existing basedpyright optional-type debt across installed `.trellis/scripts/guru/*` and template files; keep reporting it separately from the targeted py_compile/runtime tests.
- If a planning artifact changes after detail confirmation, return to the detail gate instead of forcing commit.
- If staged files include unrelated task artifacts or another workstream, split the commit before running commit review.

## Risk Areas

- `guru_review_record.normalize_review_record` is the required clean-record choke point; changes here can accidentally weaken gate security.
- `target_snapshot_digest(..., "index")` must stay byte-for-byte aligned with `check-commit` expectations.
- Lite/micro contract-derived targets must not become a broad `.` target that reviews too much or too little.
- Prompt text changes must not imply that workers can silently skip validation evidence.
- Template mirror drift can break `sync:guru:check`.

## Rollback

- If `implementation-review` destabilizes commit gates, revert the new command and gate guidance while preserving tests that encode the expected boundary.
- Do not remove existing `implement-check`; it is the compatibility fallback for normal Phase 2 repair loops.

## Completion Signal

The task is implementation-ready when PRD/design/implement artifacts are reviewed, the user explicitly approves start, and `task.py start` succeeds. It is complete only when the new check-only path is covered by tests and `check-commit` no longer recommends `implement-check` for missing/malformed required review records.
