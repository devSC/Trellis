# Implementation Plan

## Preconditions

- Stay in `planning` until this PRD / design / implementation plan is reviewed.
- Do not edit unrelated dirty files.
- Before modifying Python or TypeScript symbols, run GitNexus impact analysis per project instruction.
- Before committing, run GitNexus `detect_changes()`.
- `guru_gate.py` must be runnable from this worktree before gate changes are considered verifiable. If neither `.trellis/scripts/guru/guru_gate.py` nor `guru-template/overlay/verify/guru_gate.py` can run the relevant tests, stop as blocked instead of documenting absence as acceptable.

## Steps

1. Update workflow wording.
   - Edit `.trellis/workflow.md` planning breadcrumb and Phase 1.1 detail.
   - Edit `packages/cli/src/templates/trellis/workflow.md` to keep generated output aligned.

2. Update Guru workflow templates.
   - Edit `packages/cli/src/templates/guru/workflows/guru-client.md`.
   - Edit `packages/cli/src/templates/guru/workflows/guru-go.md`.
   - Search all Guru workflow templates for `1~4` / `一次问用户` / `trellis-brainstorm 仅作前置探索` and align wording.

3. Update requirement standard and review skill.
   - Edit `guru-template/overlay/agents-skills/requirement-doc-standard/references/requirement-structure-single-source.md`.
   - Edit matching `packages/cli/src/templates/guru/overlay/...` file.
   - Edit `guru-template/overlay/agents-skills/requirement-review/SKILL.md`.
   - Edit matching template file.

4. Update continue recovery guidance.
   - Edit `.agents/skills/trellis-continue/SKILL.md`.
   - Edit generated template source for Codex/common continue skill.
   - Ensure planning + high-risk OQ routes to one-question loop.

5. Update Guru gate.
   - Run GitNexus impact analysis for functions to edit in `guru_gate.py`.
   - Enhance Brainstorm Evidence parsing and confirmation hint checks.
   - Mirror changes in template and overlay copies.

6. Sync Guru overlay and bundled templates.
   - Run the project-approved `sync:guru` flow if available.
   - If no `sync:guru` command exists in this worktree, manually verify every edited `guru-template/overlay/...` file has the matching `packages/cli/src/templates/guru/overlay/...` update, and document the command absence.
   - Treat unsynced overlay/template drift as blocking.

7. Add tests.
   - Missing `Brainstorm Evidence` still fails.
   - Positive `Product decisions confirmed` without confirmation reference fails.
   - Multiple OQ entries without single next action fails.
   - `confirmation_status=user_confirmed*` without confirmation hint fails.
   - `confirmation_status=evidence_ready` cannot be silently upgraded to `user_confirmed*` without current-turn confirmation evidence.
   - Stale historical `user_confirmed*` / `user_quote` does not authorize a new `continue` promotion, OQ deletion, overview/detail, or start when the current user turn lacks a specific confirmation.
   - Explicit batch confirmation fixture passes only when each confirmed decision has evidence.
   - Vague batch acknowledgement fixture fails or routes back to one `next_question` unless covered OQ / decision ids are explicit.
   - Missing full `Question loop log` does not fail when `user_quote` / `confirmed_ref` is present.
   - Existing overview/detail/detail-confirm Guru gate fixtures still pass, proving requirements changes did not regress later Gate behavior.
   - Add a manual review checklist for Markdown-only skill behavior: verify `trellis-continue` contains the planning + high-risk OQ recovery rule, stale-confirmation guard, and vague-batch fallback; verify `requirement-review` contains the blocker rule for missing one-question evidence.

8. Validate.
   - Run targeted Python gate tests.
   - Run relevant CLI/template tests.
   - Run `python3 ./.trellis/scripts/task.py validate 06-26-guru-one-question-loop-requirements`.
   - Run Guru requirements gate through the available path (`.trellis/scripts/guru/guru_gate.py` or `guru-template/overlay/verify/guru_gate.py`); unavailable gate execution is blocking, not skippable.
   - Complete the Markdown skill behavior checklist and record the reviewed file paths / rule snippets in the task review log.
   - Run `git diff --check`.

9. Final review boundary.
   - Present changed files and validation results.
   - Do not start implementation task or commit until user confirms.

## Confirmed Decisions

1. DEC-002: `Question loop log` is recommended, not mandatory, for this P1 patch. The hard minimum is `user_quote` / `confirmed_ref`.
   - User confirmation: "好" on 2026-06-26.

## Trellis-Check Fix Log

- 2026-06-26: Review found that `requirement-writing` still allowed `1~4` high-risk confirmation questions, preserving the old Guru full-chain bypass at the exact writer entrypoint. Fixed `guru-template/overlay/agents-skills/requirement-writing/SKILL.md` and the packaged template copy to default to one-question loop with explicit batch-confirmation exception only.
- 2026-06-26: Review found that `guru_gate.py` only checked bullet-style `confirmation_status=user_confirmed*` blocks, while the requirement standard uses table-shaped core capability records. Fixed overlay/template gate copies to scan table rows outside fenced code, require `user_quote` / `confirmed_ref` for table confirmations, and cover table-form `evidence_ready` to `user_confirmed*` upgrades with current-turn confirmation tests.
