# Implementation Plan

## Preconditions

- Local plan review completed with two consecutive rounds containing only minor issues:
  - `.trellis/tasks/06-19-guru-detail-gate-deletion-audit-issue-6.review.md`
- Before editing existing symbols, run GitNexus `impact` for each touched function/class/method and record the blast radius in the session.
- Before committing, run GitNexus `detect_changes()`.

## Steps

1. Read relevant Trellis specs before implementation.
   - `.trellis/spec/**` package/layer indexes for CLI/template Python scripts and shell tests.
   - `.trellis/spec/guides/index.md`.

2. Add skeleton-regression coverage to shell fixtures.
   - Passing fixture: detail chapter preserves L1 skeleton and behavior contracts.
   - Failing fixture: chapter keeps endpoint table plus UNIT/BHV tokens but deletes required sections.
   - Review fixture: clean detail review without `--deletion-audit` fails.
   - Review fixture: clean detail review with `--deletion-audit "none"` passes.

3. Update `guru_gate.py`.
   - Add `detail_chapter_blocks()`.
   - Add `analyze_detail_chapter_skeleton()`.
   - Integrate analyzer into `check_detail()`.
   - Add `--deletion-audit` parsing.
   - Require deletion audit for clean detail `record-review`.
   - Store deletion audit in review records.
   - Surface deletion audit in status/report output.

4. Update `guru_supervise.py`.
   - Detail clean-review command must include `--deletion-audit`.
   - Prompt must require D9 deletion audit evidence.

5. Update detail documentation and skills across all Guru platforms.
   - L1 detail structure docs: destructive edit preservation rule.
   - Detail writing skills: deletion ledger before destructive rewrites.
   - Detail review skills: D9 diagnostic and required deletion-audit output.
   - Review references: D9 baseline and output field.

6. Sync mirrored template surfaces.
   - `guru-template/**`
   - `packages/cli/src/templates/guru/**`

7. Update `trellis-local/SKILL.md` in both copies.

8. Run targeted validation.

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
pnpm --filter @devsc/trellis test -- guru-bundled.test.ts
node .gitnexus/run.cjs detect_changes --repo "/Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree"
```

9. Commit only issue #6 related changes.

Do not stage unrelated pre-existing changes such as `AGENTS.md` or `CLAUDE.md`.
