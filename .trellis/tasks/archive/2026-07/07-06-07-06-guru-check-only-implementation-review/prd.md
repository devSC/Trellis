# Fix Guru check-only implementation review record flow

## Goal

Root-cause fix for Guru commit gate requiring structured implementation review records without re-entering implement-check or mutating detail digest artifacts.

## Problem Statement

Guru's commit gate currently consumes a structured implementation review record, but the only complete record-producing path for slice/packet flows is `guru_supervise.py implement-check --slice`. That entry is a Phase 2 implementation loop: it runs an implement worker before deterministic checks and check worker review. When a task reaches Phase 3 commit and `check-commit` discovers the record is missing, malformed, or stale, the gate tells the operator to rerun `implement-check`. This re-enters the implement phase and may mutate `implement.md`, which is part of the confirmed detail digest.

This creates a phase-boundary conflict:

- Phase 3 commit gate needs required implementation review evidence.
- The evidence producer is coupled to Phase 2 implementation execution.
- The implement worker is instructed to keep `implement.md` evidence current.
- Editing `implement.md` invalidates detail review/confirmation state.
- A commit-time evidence repair can therefore invalidate the planning gate it depends on.

The root fix must introduce a check-only required implementation review path and move post-detail execution evidence out of digest-bearing planning artifacts.

## Confirmed Repository Evidence

- `guru-client-workflow.md` defines `implement-check` inside Phase 2 Execute and `commit-plan` / `check-commit` inside Phase 3 Finish.
- `guru_supervise.py::run_implement_check` resolves packet/slice state, runs an implement worker, then deterministic checks, then a check worker, then writes `review-records/implementation-reviews.jsonl`.
- `guru_gate.py::_implementation_review_problem` blocks commit if the latest implementation review record is missing, malformed, non-clean, missing `reviewed_target_digest`, outside target paths, or digest-mismatched.
- `guru_gate.py::_implementation_review_problem` currently tells the operator to rerun `implement-check` for malformed or stale review records.
- `guru_review_record.target_snapshot_digest` already supports `source="worktree"` and `source="index"`, so the runtime can distinguish reviewed worktree state from staged commit state.
- `.trellis/spec/cli/backend/guru-overlay-gates.md` already defines a mutable evidence boundary: post-implementation evidence should go to append-only task-local files, while editing `implement.md` should continue to invalidate detail digest.

## Requirements

- Add a check-only implementation review supervisor command that can write the same required structured implementation review record without running an implement worker.
- Preserve the existing `implement-check` command as the Phase 2 implementation + review repair loop.
- Change commit gate recovery guidance so missing/malformed/stale implementation review records point to the check-only review path, not `implement-check`.
- Support commit-candidate review against staged index content so the `reviewed_target_digest` matches `check-commit`'s index digest check.
- Support slice packet review for full/high-risk packet tasks and contract-derived review targets for lite/micro tasks that do not have slice packets.
- Keep required clean records behind the existing `normalize_review_record` + `append_record` single-writer path; do not allow hand-written JSONL bypasses.
- Prevent post-detail workers from treating `implement.md` as mutable execution evidence. Execution/check/spec/commit evidence must go to append-only evidence files or `commit-plan.json`.
- Preserve fail-closed behavior for malformed verdicts, missing invariants, wrong provider, target-path drift, staged/worktree mismatch, and detail digest drift.
- Update workflow templates and specs so generated projects describe the new Phase 2.2 / Phase 3.4 boundary correctly.
- Add regression tests covering the original failure mode and the new check-only path.

## Core Capabilities

- P0: Provide `guru_supervise.py implementation-review` as the only commit-safe producer for missing, malformed, or stale required implementation review records.
- P0: Keep `check-commit` read-only and keep required clean records behind `guru_review_record.normalize_review_record` and `append_record`.
- P0: Prevent commit-plan from recommending check-only review while the staged scope, gate contract, or implementation lifecycle gate is already invalid.
- P1: Preserve `implement-check` as the Phase 2 implement plus check repair loop for normal execution work.
- P1: Document the new boundary in Guru specs, workflow templates, and generated overlay mirrors.

## Behavior Specifications

### BHV-001 Check-only implementation review produces commit evidence

Given a Guru task is already `in_progress` and needs a required implementation review record.
When the operator runs `guru_supervise.py implementation-review <task-dir> --slice <UNIT>` or `--staged`.
Then the supervisor runs deterministic checks and the check worker only, writes a structured implementation review record, and does not launch an implement worker.

### BHV-002 Commit recovery guidance stays out of implement-check

Given `commit-plan` or `check-commit` finds a missing, malformed, stale, or digest-mismatched implementation review record.
When the staged scope and implementation lifecycle gates are otherwise valid.
Then the required recovery command points to `guru_supervise.py implementation-review ... --staged` instead of `implement-check`.

### BHV-003 Invalid scope fails before worker launch

Given staged paths violate the gate contract, contain only task artifacts, or the implementation lifecycle gate is not valid.
When `commit-plan` calculates required next commands.
Then it reports the scope or lifecycle blocker and does not recommend `implementation-review --staged`.

### BHV-004 Detail artifacts remain digest-bearing

Given detail review and confirmation were already recorded for `prd.md`, `design.md`, and `implement.md`.
When implementation or review workers need to update execution evidence.
Then mutable evidence is written to append-only task-local evidence files or `commit-plan.json`, and editing `implement.md` remains a detail-gate invalidation boundary.

## Acceptance Criteria

- [ ] `guru_supervise.py implementation-review <task-dir> --slice <UNIT>` runs deterministic checks and a check worker, writes a required structured review record, and never launches an implement worker.
- [ ] `guru_supervise.py implementation-review <task-dir> --staged` writes `reviewed_target_digest` from the staged index so a following `check-commit` accepts the exact staged target when clean.
- [ ] Lite/micro tasks can derive a valid review target from staged paths plus `gate-contract.json` without requiring a temporary slice packet.
- [ ] Missing/malformed/stale implementation review blockers in `commit-plan` / `check-commit` recommend the check-only implementation review command, not `implement-check`.
- [ ] `commit-plan` does not recommend `implementation-review --staged` when staged paths already violate the gate contract, task artifact boundary, or implementation lifecycle gate; it must fail fast with scope/contract repair guidance instead of starting a check worker.
- [ ] Required clean records are still rejected when verdict fields are incomplete, provider requirements are not satisfied, deterministic checks are missing/failed, invariant coverage is missing/failed, dirty scope is invalid, or target digest mismatches.
- [ ] `implement-check` remains available for normal Phase 2 repair loops and continues to produce required clean records when run before commit.
- [ ] Worker prompt text no longer instructs post-detail execution/check workers to update `implement.md` as mutable evidence.
- [ ] Appending `implementation-evidence.jsonl` / `verification-evidence.jsonl` does not change detail digest, while editing `implement.md` still does.
- [ ] Workflow docs and generated Guru templates describe `implementation-review` as the commit-safe evidence producer.
- [ ] Focused CLI tests pass for Guru overlay review/gate behavior.

## Out Of Scope

- Removing `implement.md` from the detail digest.
- Allowing `check-commit` to spawn workers or write review records itself.
- Allowing manual JSONL records to satisfy required implementation review.
- Reworking provider adapters or channel runtime lifecycle beyond what the new command needs.
- Changing non-Guru Trellis workflows except for shared template sync required by the Guru overlay.

## Failure Paths

- If the check worker emits an incomplete verdict, the supervisor appends a failed preflight or malformed review record and exits non-zero.
- If deterministic checks fail or required invariant coverage is missing, the structured review record is not accepted as clean commit evidence.
- If staged content changes after the clean review record is written, `check-commit` recomputes the index digest and blocks the commit.
- If staged paths already violate contract or task-artifact boundaries, `commit-plan` reports that blocker before any check worker is started.

## Open Questions

- None: repository evidence and the user's current request already define the scope as a Guru tooling boundary fix, not app business implementation.

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`, `trellis-meta`, `python-design`.
- Repository evidence inspected: Guru workflow template, `guru_supervise.py`, `guru_gate.py`, `guru_review_record.py`, `guru-overlay-gates.md`, Python script guidelines, unit-test conventions.
- Domain/terminology triggers: "implementation check" currently means both implementation loop and required review evidence; this task standardizes "implementation-review" as check-only evidence production.
- Current code vs user intent conflicts: current commit gate recovery path points to `implement-check`; user intent requires a root-cause fix that does not mutate `implement.md` after detail confirmation.
- Product decisions confirmed: commit gate must remain fail-closed; `implement.md` must remain digest-bearing; check-only review must not bypass structured record normalization.
  - confirmed_ref: current conversation asked for a root-cause fix and then approved continuation into implementation.
- Open product/scope/risk questions: none: repository evidence and current user direction define the repair boundary.

### Question Policy

- question_policy: mixed
- evidence answered: code, tests, specs, and workflow templates answered the phase-boundary and evidence-writer mechanics.
- user confirmed: current conversation confirmed the root-cause repair direction and continuation after the proposed fix plan.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
