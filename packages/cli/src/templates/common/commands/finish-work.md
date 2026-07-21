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

This is an agent-owned admission check for the archive branch. It does not add a lifecycle state or change the archive script.

For the current active task:

1. Inspect `prd.md`, the current Detail package, and `implement.md` for the planning marker `runtime_acceptance_required=true`.
2. If this is not a runtime-required Full task, continue to Step 3.
3. If the marker is present, read the frozen Acceptance Closure Matrix and identify every row where `required=true`. A marker without a matrix or without at least one required row is a `DETAIL_DEFECT`: stop this command and return to the Detail owner. Do not infer a required set from whatever evidence happens to exist.
4. Resolve the current baseline from the task's current requirements, Overview, Detail, and implementation snapshot bindings. Then read the complete ledger in append order from task-local `verification-evidence.jsonl` (or the task's explicitly declared equivalent). If any append is unreadable or malformed such that its `acceptance_id` or baseline binding cannot be resolved, block archive as a `PROCESS_DEFECT`; never skip that append and fall back to older evidence.
5. For each required `acceptance_id`, first identify the newest append whose baseline binding matches the current baseline, using append position alone. Only after selecting that exact newest row may you validate its status and required fields. A selected pass is valid only when its target environment, steps/command, expected, actual, evidence references, recorder, and timestamp are complete. If the selected row is malformed, incomplete, or has an unsupported status, block and require a corrected append; do not search backward for an older pass. If there is no current-baseline append, classify any historical pass as stale or the row as missing. A valid selected `implementation_verified`, `runtime_acceptance_pending`, or `runtime_acceptance_failure` is a current non-pass and supersedes every earlier pass.

Use these evidence/reporting values without writing them into `task.json.status`:

| Status | Meaning | Archive decision |
| --- | --- | --- |
| `implementation_verified` | Static checks, tests, and implementation review are current, but runtime acceptance is incomplete | Block |
| `runtime_acceptance_pending` | A named owner has received the exact target-environment probe and has not returned a result | Block and keep the task active |
| `runtime_acceptance_failure` | Current target-environment evidence does not satisfy the row | Block and enter repair continuation |
| `runtime_acceptance_pass` | One row has complete current environment, steps, expected/actual, and evidence | Continue evaluating the other required rows |
| `accepted` | Every required row's newest current-baseline append validates as a pass; no newer append is skipped or ignored | The runtime guard is clear; continue the existing finish flow |

An unreadable ledger append or a malformed/incomplete newest current-baseline row is an evidence precondition failure, not a lower-priority runtime result. Report the exact line/row when possible, keep the ledger append-only, require a corrected append, and stop before applying the runtime-row priority below.

If any row is blocked, preserve the complete blocking list but report one next action using this priority: current failure, stale pass, missing evidence, then pending handoff. Include the exact `acceptance_id`, blocking reason, matrix-owned runtime probe, evidence owner, and required evidence:

- For a failure, the next action is same-goal repair classification; retain the original probe as the post-repair resume condition.
- For a stale pass or missing row, the next action is to rerun the row's original probe against the current baseline.
- For a pending row, the next action remains with its named runtime owner. If no owner is named, the handoff is invalid and must be repaired before recording pending evidence.

Report `implementation_verified`, `runtime_acceptance_pending`, or `runtime_acceptance_failure` as applicable, keep the task active/`in_progress`, and **stop this command here**. Do not run the archive command or any later lifecycle step. Tests green, a clean implementation review, `COMMIT_READY`, `implementation_verified`, one row's pass, or an older pass must never be reported as `accepted`.

Only when the required ID set has no difference from the current pass set and every required ID's exact newest current-baseline append validates as `runtime_acceptance_pass` may you report `accepted` and continue. Clearing this guard does not authorize commit, push, merge, archive, or any other action that the existing workflow still gates.

**Enforcement boundary:** this step constrains the agent following `{{CMD_REF:finish-work}}`. The unchanged lifecycle scripts do not parse the matrix or evidence ledger, and a user or tool that invokes `task.py archive` directly is not fail-closed by this contract. State that limitation if relevant; never claim script-level enforcement or fabricate a manual/user/QA receipt.

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
