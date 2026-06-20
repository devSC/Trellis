# Adversarial Review Latency Optimization Plan

## Problem

The current Guru requirements adversarial review turns a planning repair into a
long synchronous loop. In the reference Codex thread
`019ee544-91bb-74f1-a551-1696e9dba891`, requirements adversarial review ran at
least three completed times:

- 14:32:16 -> 14:45:24, about 13 minutes.
- 14:57:36 -> 15:11:56, about 14 minutes.
- 15:14:00 -> 15:23:15, about 9 minutes.
- A fourth run started at 15:24:41 and was still running when inspected.

The second run already produced `review_result=clean/requirements-ready`, but
the session still patched P2/P3 follow-ups and reran the full opposite-provider
review. The result was a workflow that spent more time waiting for repeated
long-context review than converging the actual requirements.

## Goals

1. Keep adversarial review visible and auditable.
2. Stop rerunning full requirements adversarial review after a clean result when
   only non-blocking P2/P3 follow-ups are changed.
3. Allow timeout/provider failures to become explicit deferred evidence instead
   of leaving the main session blocked on a silent worker.
4. Preserve stricter overview/detail review evidence rules; this change targets
   requirements review latency first.
5. Avoid a scheduler, queue, database, or new task status.

## Non-Goals

- Do not remove requirements adversarial review from the workflow.
- Do not let skipped/deferred review masquerade as clean review.
- Do not change overview/detail double-clean readiness.
- Do not introduce a broad model registry or provider abstraction.
- Do not add dependencies.

## Current Evidence

- `guru_supervise.py --adversarial requirements` spawns the opposite provider and
  asks it to inspect `prd.md`, task metadata/jsonl, formal requirements package
  references, task context, repo evidence, code, tests, configs, docs, spec,
  `CONTEXT.md`, `CONTEXT-MAP.md`, and ADRs before product questions.
- Requirements review currently has no `record-review` command and no clean
  streak. The worker is expected to emit either `route_class=REQ_BLOCKER` or
  `review_result=clean/requirements-ready`.
- `guru_gate.py check` hard-checks requirements structure and user confirmation
  snapshot; overview/detail are the gates with structured `review_runs`
  readiness.
- Existing best-effort adversarial behavior persists provider failures into
  `task.json.guru_gates.adversarial_skips[]` and shows them in `guru_gate.py
  status`.

## Proposed MVP

Add a requirements-only review state under `task.json.guru_gates`:

```json
{
  "guru_gates": {
    "requirements_review": {
      "action": "requirements",
      "provider": "claude",
      "current_provider": "codex",
      "adversarial": true,
      "status": "clean",
      "artifact_digest": "<requirements digest>",
      "run_id": "20260620...",
      "channel": "guru-...",
      "worker": "requirements-claude-...",
      "reason": "review_result=clean/requirements-ready",
      "timestamp": "2026-06-20T..."
    }
  }
}
```

Allowed `status` values:

| Status | Meaning | Confirm handling |
| --- | --- | --- |
| `clean` | The opposite-provider requirements review completed with `review_result=clean/requirements-ready` for the current requirements digest. | No warning. |
| `blocked` | Review completed with `route_class=REQ_BLOCKER` or another medium+ blocker. | Print a clear blocked warning before `confirm requirements`; the human can still intentionally accept the visible risk, but agents must not treat this as clean. |
| `deferred` | The adversarial worker could not finish cleanly: provider missing, launch failure, wait failure, timeout, killed/error terminal status, or missing verdict. | Print a clear deferred warning before `confirm requirements`; the human can still intentionally accept the visible risk, but agents must not treat this as clean. |

The MVP does three small things:

1. `guru_supervise.py --adversarial requirements` records the state above after
   the worker exits or is skipped.
2. `guru_gate.py status` prints the requirements review state with digest
   freshness.
3. `guru_gate.py confirm requirements` warns when the current digest lacks a
   clean requirements adversarial review. In `strict` mode this warning is
   informational: the human still decides whether to confirm. In `soft` mode the
   warning is printed before the agent writes the confirmation with the user's
   quote.

## Rerun Policy

After a current-digest `clean` record exists:

- Do not rerun requirements adversarial review for low-severity wording,
  trace-table, changelog, or P2/P3 follow-up edits unless the user explicitly
  asks.
- Rerun if the edit changes P0/P1 behavior, BHV/REQ/API contracts, acceptance
  criteria, capability ownership, unresolved product decisions, or any file in
  the requirements digest.
- A `blocked` record must be repaired and rerun.
- A `deferred` record may proceed only with visible status/confirm warning.

This policy is mainly enforced by agent instructions and status visibility in
the MVP. A later version can split semantic digest from formatting digest if the
policy needs machine enforcement.

## Implementation Steps

1. Extend `guru_supervise.py`.
   - Add constants for `requirements_review` state.
   - Add helpers that parse worker messages for:
     - `review_result=clean/requirements-ready`
     - `route_class=REQ_BLOCKER`
   - Record `clean`, `blocked`, or `deferred` for adversarial requirements.
   - Keep existing `adversarial_skips[]` for historical skip list.
   - Do not change non-adversarial behavior.

2. Extend `guru_gate.py`.
   - Add a requirements review status reader.
   - Show current/stale/missing/deferred/blocked state in `status`.
   - Print a warning during `confirm requirements` if no current clean exists.
   - Do not block hard in `confirm`, because the user can intentionally accept a
     visible deferred review.

3. Sync source overlay to packaged template.

4. Add shell regressions in `guru-template/overlay/verify/tests/run_tests.sh`.
   - Status shows current clean requirements review.
   - Status shows stale requirements review after `prd.md` changes.
   - Confirm requirements prints a warning when review state is missing or
     deferred.

5. Add bundled-template regression in `packages/cli/test/guru/guru-bundled.test.ts`
   so source and packaged templates both contain the new state keys and warning
   text.

## Self-Review Loop

### Pass 1 Findings

- Blocker: none.
- Should-fix: avoid making deferred review look equivalent to clean. The plan
  now keeps `status=deferred` separate from `status=clean` and only changes
  status/confirm visibility.
- Should-fix: avoid broad semantic digest machinery in this increment. The MVP
  uses current requirements digest only; semantic digest is deferred.
- Nice-to-have: background adversarial review could further improve latency, but
  it needs channel lifecycle policy and is not required for the first fix.

### Pass 2 Findings

- Blocker: none.
- Should-fix: `confirm requirements` must not silently pass when review is
  blocked. The implementation should print a clear blocked warning before any
  human/soft confirmation. Keeping final authority with the human is acceptable
  because requirements adversarial is workflow-required but not currently a
  structured hard check in `cmd_check`.
- Nice-to-have: a future version can add `--requirements-review-budget 8m` or a
  config key, but this first implementation should avoid changing timeout
  semantics while existing channel timeout work is already in the tree.

## Implementation Evidence

Implemented in source Guru overlay and synced to packaged templates:

- `guru_supervise.py` records `task.json.guru_gates.requirements_review` for
  adversarial requirements runs.
- Completed worker output containing `review_result=clean/requirements-ready`
  records `status=clean`.
- Completed worker output containing `route_class=REQ_BLOCKER` records
  `status=blocked`.
- Provider launch/wait/message failures, non-`done` terminal statuses, and
  missing verdicts record `status=deferred`.
- Existing `adversarial_skips[]` history remains intact for skip history.
- `guru_gate.py status` prints `需求对抗 Review` with
  missing/current/stale/clean/blocked/deferred visibility.
- `guru_gate.py confirm requirements` prints a warning when the current
  requirements digest lacks clean/current adversarial review state, while still
  allowing explicit human confirmation.
- `packages/cli/test/guru/guru-bundled.test.ts` now asserts source/package
  sync for `guru_gate.py`, `guru_supervise.py`, and the shell regression file,
  plus direct persistence tests for clean and blocked requirements verdicts.

Validation run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  guru-template/overlay/verify/guru_supervise.py \
  guru-template/overlay/verify/guru_gate.py \
  packages/cli/src/templates/guru/overlay/verify/guru_supervise.py \
  packages/cli/src/templates/guru/overlay/verify/guru_gate.py

bash guru-template/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli sync:guru
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts
git diff --check
git diff --cached --check
node .gitnexus/run.cjs detect-changes --repo Trellis --scope all
```

Observed results:

- Python compile: passed.
- Source Guru shell regression: `143 passed / 0 failed`.
- Packaged Guru bundled Vitest: `51 tests passed`.
- `git diff --check`: passed.
- `git diff --cached --check`: passed.
- GitNexus detect-changes: `32 files, 114 symbols, 62 affected processes,
  risk level critical`; this is the whole dirty worktree, including existing
  staged/unstaged channel and Guru work. Focused impact checks for touched
  indexed call sites were LOW; new helper symbols were not yet in the index and
  returned UNKNOWN until the next analyze.

## Implementation Self-Review

### Pass 3 Findings

- Blocker: none.
- Should-fix found and fixed: shell regression initially failed because existing
  Brainstorm Evidence test fixtures had a BSD `sed` delimiter issue and a CJK
  P0 fixture lacked Brainstorm Evidence after prior dirty-worktree changes.
  Fixed the fixtures without changing production behavior.
- Should-fix found and fixed: initial tests covered status/confirm visibility
  but not direct `guru_supervise.py` persistence on successful adversarial
  requirements completion. Added a fake trellis channel test for clean and
  `REQ_BLOCKER` verdict persistence.

### Pass 4 Findings

- Blocker: none.
- Should-fix: none remaining.
- Residual MVP boundary: rerun suppression after a current clean record is
  policy/status-visible rather than automatically enforced. That is intentional
  for this increment because a semantic digest or scheduler would add more
  machinery than the latency issue requires.
- Residual MVP boundary: `confirm requirements` warning is not a hard block for
  blocked/deferred review. This matches the plan: humans may accept visible
  risk, while agents must not report missing/deferred/blocked as clean.

## Validation Plan

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  guru-template/overlay/verify/guru_supervise.py \
  guru-template/overlay/verify/guru_gate.py \
  packages/cli/src/templates/guru/overlay/verify/guru_supervise.py \
  packages/cli/src/templates/guru/overlay/verify/guru_gate.py

bash guru-template/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli sync:guru
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts -t "requirements review"
git diff --check
node .gitnexus/run.cjs detect-changes --repo Trellis --scope all
```

## Acceptance Criteria

- A completed clean requirements adversarial review is persisted to task state.
- A deferred requirements adversarial review is persisted separately from clean.
- `guru_gate.py status` shows the latest requirements review state and whether
  it matches the current digest.
- `guru_gate.py confirm requirements` makes missing/deferred/blocked review
  state visible before confirmation.
- No overview/detail readiness behavior changes.
- No new dependency or scheduler is added.
