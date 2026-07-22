# Finish Work

Wrap up the current session: archive the active task (and any other completed-but-unarchived tasks the user wants to clean up) and record the session journal. Code commits are NOT done here — those happen in workflow Phase 3.4 before you invoke this command.

## Step 1: Survey current state

```bash
{{PYTHON_CMD}} ./.trellis/scripts/get_context.py --mode record
```

This prints:

- **My active tasks** — review whether any besides the current one are actually done (code merged, AC met) and should be archived this round.
- **Git status** — quick visual on what's dirty.
- **Recent commits** — you'll need their hashes in Step 5 for `--commit`.

If `--mode record` surfaces other completed tasks not tied to the current session, surface them to the user with a one-shot confirmation: "These N tasks look done — archive them too in this round? [y/N]". Default is no; the current active task proceeds toward Step 4 only if the runtime check in Step 2 and the dirty-path check in Step 3 admit it.

## Step 2: Check runtime acceptance before archive

This is an agent-owned admission check for the archive branch. It does not add a lifecycle state or change the archive script. `FinishSkill` owns only the final allow/block decision; `ClosureSpec` is the ClosureSpec-only owner of evidence currentness, reconciliation, row selection, blocker ordering, and probe selection.

For the current active task:

1. Read `prd.md`, current Detail, and `implement.md`. If `runtime_acceptance_required=true` is absent, continue to Step 3. If present, the frozen Acceptance Closure Matrix must contain at least one `required=true` row; otherwise stop with `DETAIL_DEFECT`. Never infer the required set from evidence.
2. Pass the current/linked-active `TaskRef`, matrix, and requirements/Overview/Detail/implementation baseline to `ClosureSpec`. Finish must not open, filter, replay, or select from `verification-evidence.jsonl` or `<task_dir>/retrospective-reconciliation.jsonl`; an `append acknowledgment` only triggers fresh resolution.
3. Consume only ClosureSpec-only fresh, exact `AcceptanceResolution`, preserving `baseline_binding`, `ledger_snapshot_ref`, `reconciliation_snapshot_ref`, `open_correction_debts`, `open_retrospective_reconciliations`, `row_results`, `selected_evidence_refs`, `blocking_evidence_refs`, `task_result`, `blocking_acceptance_ids`, and `next_probe`. A missing field or private projection is `DETAIL_DEFECT`.
4. `ClosureSpec` obtains the complete `LedgerReadSnapshot` through `EvidenceLedger.readAllInAppendOrder()`, strictly replays the exact reconciliation journal, and produces the resolution. Its currentness proof requires non-empty `LedgerSnapshotRef` to bind `artifact_ref`, `append_count`, `last_append_position`, and full-ledger-byte lowercase SHA-256 `content_digest`; non-empty `RetrospectiveReconciliationSnapshot` binds `artifact_ref`, `event_count`, `last_event_position`, final newline-event SHA-256 `last_event_digest`, and full-file SHA-256 `content_digest`. Any append/event/baseline change stales the resolution.
5. The exact journal uses `journal-root-v1`: first event `position=1`, `previous_event_digest=null`; later `previous_event_digest` is the prior complete newline-event SHA-256. `deriveLedgerAppendRef(full_snapshot, exact_position)` independently derives each `LedgerAppendRef` from ledger `artifact_ref`, position, and complete newline-append SHA-256, never a journal ref. `retrospective-ledger-journal-correlation` rejects older-valid/empty rollback, cross-position refs, and non-unique repeated rows. Missing/partial/gapped/duplicate/digest-, transition-, or snapshot-invalid journal is `reconciliation_register_unavailable` or `reconciliation_register_corrupt`; Finish never initializes, guesses, truncates, or falls back to a prefix.
6. Every null `record_ref` stays in `open_retrospective_reconciliations`, even with `accepted_append_ref`; accepted/committed proves only append identity. Only a strict-full-replay-acknowledged `record-bound` event with `accepted_append_ref`, `record_ref`, and exact `closes_attempt_ids` closes ordinal-0 or the full ordinal-0+1 chain. Missing/extra/cross-chain IDs, ambiguity, or a second missing acknowledgment stays open, permits no third retry/record/decision/probe, and forces `next_probe=null`.

Evidence/reporting values never become `task.json.status`: `implementation_verified` means technical-only green; `runtime_acceptance_pending` awaits its named owner; `runtime_acceptance_failure` routes repair; `runtime_acceptance_pass` closes one current row; `accepted` is task-level and requires the canonical all-pass result.

For any stale resolution, register error, open debt/reconciliation, non-pass row, or other blocker, preserve the whole object and its order. Report `blocking_acceptance_ids`, `blocking_evidence_refs`, both open sets, and canonical `next_probe` unchanged; do not downgrade, search backward, reorder, select, or rebuild. Hand a non-null probe to its owner; for `next_probe=null`, report only canonical evidence/reconciliation repair; hand a selected failure's exact resolution to Guru workflow for repair routing. Keep the task active/`in_progress` and **stop before Step 3**.

Continue only when fresh `task_result=accepted`, both open sets and all blocking IDs/refs are empty, and `selected_evidence_refs` contains complete current pass refs. Tests/review/`COMMIT_READY`/`implementation_verified`/one or old pass never qualify. Runtime clearance grants no commit, push, merge, archive, or other authorization.

**Enforcement boundary:** this agent contract cannot make unchanged lifecycle scripts fail closed; direct `task.py archive` can bypass it. Never claim script-level enforcement or fabricate a manual/user/QA receipt.

## Step 3: Sanity check — classify dirty paths

Run:

```bash
git status --porcelain
```

Filter out paths under `.trellis/workspace/` and `.trellis/tasks/` — those are managed by `add_session.py` and `task.py archive` auto-commits and will appear dirty as part of this skill's own work.

For each remaining dirty path, decide whether it belongs to **the current task** or to **other parallel work** (e.g., another terminal window editing the same repo). Heuristics:

- Paths referenced in the current task's `prd.md` / `implement.jsonl` / `check.jsonl` → current task
- Paths in code areas matching the task's stated scope, or that you remember editing this session → current task
- Paths in unrelated areas you have no recollection of touching this session → other parallel work

Then route:

- **Any remaining path looks like current-task work** — bail out with:
  > "Working tree has uncommitted code changes from this task: `<list>`. Return to workflow Phase 3.4 to commit them before running `{{CMD_REF:finish-work}}`."

  Do NOT run `git commit` here. Do NOT prompt the user to commit. The user goes back to Phase 3.4 and the AI drives the batched commit there.
- **All remaining paths look unrelated** (other parallel-window work) — report them once and continue to Step 4:
  > "FYI, dirty files outside this task's scope — leaving them for the other window: `<list>`."
- **Genuinely unsure** — ask the user once: "Are `<list>` this task's work I forgot to commit, or another window's? (commit / ignore)" — then route per their answer.

## Step 4: Archive task(s)

```bash
{{PYTHON_CMD}} ./.trellis/scripts/task.py archive <task-name>
```

At minimum: the current active task (if any), but only after Step 2 admits it. Plus any extra tasks the user confirmed in Step 1; apply Step 2 independently to every runtime-required Full task before archiving it. Each archive produces a `chore(task): archive ...` commit via the script's auto-commit.

If there is no active task and the user did not confirm any cleanup archives, skip this step.

## Step 5: Record session journal

```bash
{{PYTHON_CMD}} ./.trellis/scripts/add_session.py \
  --title "Session Title" \
  --commit "hash1,hash2" \
  --summary "Brief summary"
```

Use the work-commit hashes produced in Phase 3.4 (visible in Step 1's `Recent commits` list, or via `git log --oneline`) for `--commit`. Do not include the archive commit hashes from Step 4. This produces a `chore: record journal` commit.

Final git log order: `<work commits from 3.4>` → `chore(task): archive ...` (one or more) → `chore: record journal`.
