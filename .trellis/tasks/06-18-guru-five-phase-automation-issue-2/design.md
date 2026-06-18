# Technical Design

## Summary

Implement `devSC/Trellis#2` as a Guru overlay contract change, not as a Trellis core lifecycle rewrite.

The existing Trellis lifecycle remains:

```text
planning -> task.py start -> in_progress -> commit/archive/finish-work boundaries
```

The Guru-specific planning Gates are implemented as artifact checks plus durable evidence in `task.json`. This keeps the change local to Guru workflow assets, Guru specs, review skills, and `guru_gate.py`.

## Current State

The current Guru contract has three manual planning Gates:

```text
requirements: structure + design-grill + human confirm
overview:     structure + design-grill/skip + human confirm
detail:       structure + design-grill/skip + human confirm
```

That model appears in:

- `guru-template/workflows/*-workflow.md`
- `guru-template/specs/*/harness/gate/gate-confirmation-model.md`
- `guru-template/overlay/verify/guru_gate.py`
- packaged copies under `packages/cli/src/templates/guru/`
- installed local copies in `.agents/.claude/.cursor/.opencode/.pi` after template application

## Target State

The new Guru model is:

```text
requirements:
  structure + requirement discovery / Domain Grill + human confirm

overview:
  structure + two clean-context reviews for current digest -> automatic pass

detail:
  structure + two clean-context reviews for current digest -> stop for human confirm

implementation:
  code + comments + logs + validation + trace -> implementation review loop

hard boundary:
  commit/archive/finish-work/publish/external write -> human confirm
```

## Planning Automation Loop

Issue #2 requires more than durable review evidence. After requirements are confirmed, overview/detail planning defects must be driven by agents until a real user decision or hard boundary appears.

Use the existing Trellis dispatch model. Do not add a parallel planning state machine.

Minimum loop:

```text
overview:
  write/update overview artifact
  run overview clean-context review
  record-review overview
  if REQ_BLOCKER -> return to requirements and invalidate downstream evidence
  if OVERVIEW_DEFECT/PROCESS_DEFECT -> fix artifact and repeat
  if two clean reviews for current digest -> auto pass to detail

detail:
  write/update detail artifact and implement.md
  run detail clean-context review
  record-review detail
  if REQ_BLOCKER -> return to requirements and invalidate downstream evidence
  if OVERVIEW_DEFECT -> return to overview and invalidate detail evidence
  if DETAIL_DEFECT/PROCESS_DEFECT -> fix artifact and repeat
  if two clean reviews for current digest -> stop for user detail confirmation
```

The first implementation must add the smallest `guru_supervise.py` extension for repeatable planning actions.

Keep it boring: add only `overview` and `detail` actions that reuse existing channel creation/spawn/wait plumbing and platform writing/review skills. Do not introduce queues, persistent workers, or a new status model. Workflow and review-skill text still documents the loop, but text-only guidance is not enough for this PRD unless an existing single command is proven to run the whole loop.

### Supervisor Action Shape

Keep the existing `RunPlan` and channel plumbing. Extend only the action-to-skill lookup shape needed to represent planning actions:

- implementation actions may keep one skill path.
- `overview` must resolve to the platform overview writing skill and the matching overview clean-context review skill.
- `detail` must resolve to the platform detail writing skill and the matching detail clean-context review skill.

`build_run_plan` should add every resolved skill file to `artifact_files` and send one worker prompt that says: write or update the planning artifact, run the clean-context review with a fresh run id, record evidence with `guru_gate.py record-review`, and repeat only until a stop condition is reached.

Dry-run output is the regression contract. `overview` and `detail` dry-runs must exit 0 and prove the parser/action map can build a `RunPlan` with both skill paths, fresh run-id guidance, `record-review`, and the stop-condition keywords (`REQ_BLOCKER`, phase defect class, two clean reviews, tool failure).

## Implementation Automation Loop

After detail confirmation, implementation should reuse the same supervisor file and existing action mechanics.

Minimum loop:

```text
implementation:
  run existing implement action with implementation writing skill
  run existing check action with implementation review skill
  if IMPLEMENT_DEFECT or implementation PROCESS_DEFECT -> run implement again with finding context
  if DETAIL_DEFECT -> return to detail loop and invalidate implementation evidence
  if OVERVIEW_DEFECT -> return to overview loop and invalidate downstream evidence
  if REQ_BLOCKER -> return to requirements and invalidate downstream evidence
  if check clean -> run final validation and stop at hard-boundary confirmation
```

Keep it boring: add one minimal `implement-check` supervision loop or equivalent single command that sequences the existing `implement` and `check` actions. Do not add queues, persistent workers, a scheduler, or a new task status. Dry-run output must exit 0 and show the implement skill, check skill, defect routing keywords, final validation stop, and hard-boundary stop.

Implementation review evidence for this first version is intentionally smaller than planning evidence: one clean implementation check is enough if the check output says clean/final-verification-ready and includes the reviewed diff or artifact context plus validation evidence summary. Do not add implementation `guru_gates`, a second implementation clean streak, or a review database in this task. If this proves too weak later, extend the existing review evidence model then.

## Design Principles

- Keep `task.json` as the durable evidence store.
- Keep `guru_gate.py` deterministic and file-based.
- Do not encode semantic review judgment in Python. The script records and verifies review evidence produced by review skills.
- Fail closed when evidence is missing, stale, or medium+.
- Treat artifact digest as the invalidation mechanism.
- Keep old grill commands only for compatibility, not as the new hard Gate.
- Sync from `guru-template/` to packaged templates after source edits.

## Data Model

Store review evidence under `task.json.guru_gates`.

Recommended shape:

```json
{
  "guru_gates": {
    "requirements": {
      "confirmed_by": "devSC",
      "confirmed_at": "2026-06-18T00:00:00+08:00",
      "artifact_digest": "<requirements digest>"
    },
    "overview": {
      "artifact_digest": "<overview digest>",
      "review_runs": [
        {
          "result": "clean",
          "max_severity": "none",
          "finding_class": null,
          "reviewer": "clean-context",
          "run_id": "overview-review-20260618-0000-a",
          "evidence": "overview review found no medium+ issues",
          "artifact_digest": "<overview digest>",
          "at": "2026-06-18T00:00:00+08:00"
        },
        {
          "result": "clean",
          "max_severity": "low",
          "finding_class": null,
          "reviewer": "clean-context",
          "run_id": "overview-review-20260618-0005-b",
          "evidence": "second clean overview review for the same digest; low-only nits are non-blocking",
          "artifact_digest": "<overview digest>",
          "at": "2026-06-18T00:05:00+08:00"
        }
      ]
    },
    "detail": {
      "artifact_digest": "<detail digest>",
      "review_runs": [
        {
          "result": "clean",
          "max_severity": "none",
          "finding_class": null,
          "reviewer": "clean-context",
          "run_id": "detail-review-20260618-0010-a",
          "evidence": "detail review found no medium+ issues",
          "artifact_digest": "<detail digest>",
          "at": "2026-06-18T00:10:00+08:00"
        },
        {
          "result": "clean",
          "max_severity": "none",
          "finding_class": null,
          "reviewer": "clean-context",
          "run_id": "detail-review-20260618-0015-b",
          "evidence": "second clean detail review for the same digest",
          "artifact_digest": "<detail digest>",
          "at": "2026-06-18T00:15:00+08:00"
        }
      ],
      "confirmed_by": "devSC",
      "confirmed_at": "2026-06-18T00:00:00+08:00"
    }
  }
}
```

`clean_streak` is a derived value, not trusted stored state. `auto_passed` is also derived/display-only and should not be persisted as a source of truth. `check` and `status` must compute pass/fail from consecutive `review_runs` entries for the current artifact digest. If a legacy task contains stored `clean_streak` or `auto_passed`, ignore it for pass/fail decisions and warn in `status` only if useful.

Two clean records count as two reviews only when their `run_id` values are distinct. The supervisor should generate a fresh run id for each clean-context review attempt and include it in the `record-review` call. Reusing the same `run_id` is allowed in the log, but it does not advance the clean streak.

## Digest Semantics

Reuse `_gate_digest(task_dir, gate)` as the current artifact digest source.

- `requirements` digest covers `prd.md`.
- `overview` digest covers requirements plus overview artifacts.
- `detail` digest covers requirements, overview, detail artifacts, and `implement.md`.

Because downstream digests include upstream artifacts, upstream changes invalidate downstream clean reviews and confirmations automatically.

## `guru_gate.py` Changes

### Commands

Add:

```text
record-review <overview|detail> <task_dir>
  --result clean|findings
  --max-severity none|low|medium|high|critical
  [--finding-class REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|IMPLEMENT_DEFECT|PROCESS_DEFECT]
  --reviewer clean-context
  --run-id "<clean-context run id>"
  --evidence "<short summary>"
```

Optional shorthand can be added later, but the first implementation should stay explicit.

Validation rules:

- `--result clean` requires `--max-severity none|low`.
- `--result clean` must reject `--finding-class`.
- `--result findings` requires `--finding-class`.
- `--result findings` requires `--max-severity medium|high|critical`.
- `--run-id` is required for both results.
- Any `findings` result does not count toward the clean streak.
- Medium/high/critical findings reset the current clean streak and must be visible in `status`.
- Low-only clean observations count toward the clean streak when the review is otherwise clean.
- Duplicate `run_id` values do not count as distinct clean reviews.
- `REQ_BLOCKER` routes status guidance back to requirements and makes downstream overview/detail evidence non-current.

The top-level usage string, `main()` command routing, invalid-argument messages, and tests must be updated with `record-review`; helper-only implementation is not sufficient.

`record-review` intentionally has no `requirements` target in this task. Requirements review remains requirement discovery / Domain Grill plus human confirmation, not a durable clean-streak Gate.

### Gate Sets

Replace the old conceptual `HUMAN_GATES` usage with:

```python
GATES = ("requirements", "overview", "detail")
HUMAN_CONFIRM_GATES = ("requirements", "detail")
AUTO_REVIEW_GATES = ("overview", "detail")
```

Keep compatibility labels for output.

### Confirmation

`confirm` should only accept `requirements` and `detail` in the new model.

Calling `confirm overview` should fail with guidance:

```text
overview is an automatic clean-review Gate; record two clean reviews instead
```

### Check

`cmd_check` should validate:

1. `requirements` structure passes.
2. `requirements` human confirmation exists and digest matches.
3. `overview` structure passes.
4. `overview` has two consecutive clean review records for the current digest.
5. `detail` structure passes.
6. `detail` has two consecutive clean review records for the current digest.
7. `detail` human confirmation exists and digest matches.

`grill` records should not be required by `cmd_check`.

### Auto

`auto` is also a verification entrypoint, so it must follow the same new model instead of preserving the old `design-grill` hard prerequisite.

`auto` should keep progressive planning with explicit exit-code semantics:

| State | Validation | Exit |
| --- | --- | --- |
| No active task | Keep existing no-task pass behavior. | 0 |
| Requirements missing or structurally invalid | Report the requirements structure gap. | 2 |
| Requirements structure valid but human confirmation missing or stale | Report requirements confirmation guidance; do not ask for grill evidence. | 2 |
| Requirements confirmed and no overview artifact exists yet | Preserve progressive planning; no overview or detail review evidence is required before the artifact exists. | 0 |
| Overview artifact exists | Require overview structure plus two current clean review records with distinct run ids. Missing/stale evidence reports review-evidence guidance, not `grill-done`. | 0 when satisfied, 2 when missing/stale |
| Detail artifact exists | Require detail structure plus two current clean review records with distinct run ids. Missing/stale evidence reports review-evidence guidance; detail human confirmation remains the `check` / start-boundary requirement. | 0 when satisfied, 2 when missing/stale |
| Task is already beyond planning | Continue validating available planning and implementation artifact structure; never reintroduce old overview/detail grill prerequisites. | 0 when satisfied, 2 when invalid |

When multiple artifacts exist, `auto` applies every applicable row in order; a later artifact does not replace validation for earlier artifacts.

`auto` exit 0 under progressive planning means "all currently existing artifacts pass their current Gate checks"; it does not mean the five-phase workflow is complete.

It must not require overview/detail `grill-done` or `grill-skip`. Old grill records may be displayed as deprecated context by `status`, but they must not unblock or block `check` or `auto`.

### Status

`cmd_status` should report:

- missing review evidence
- one clean review
- duplicate clean review run id
- two clean reviews / auto passed
- low-only clean observations
- medium+ finding and clean-streak reset
- `REQ_BLOCKER` and requirement rollback guidance
- artifact digest mismatch
- missing detail confirmation
- valid detail confirmation

### Compatibility

Old records:

- If an old `overview.confirmed_by` exists but no new review evidence exists, status should say it is legacy evidence and not sufficient for the new overview Gate.
- Old `grill` records may still render as deprecated context, but should not unblock or block `check` / `auto`.
- Existing invalid JSON handling and atomic writes must be preserved.

## Workflow and Skill Changes

### Guru Workflows

Update all platform workflows under `guru-template/workflows/`:

- `guru-client-workflow.md`
- `guru-go-workflow.md`
- `guru-ios-workflow.md`
- `guru-h5-workflow.md`

Required edits:

- Core principles mention requirements confirmation, overview auto clean review, detail confirmation, hard boundary.
- Planning breadcrumbs stop saying `Gate=writing->review->grill-policy->confirm`.
- Active task routing moves `design-grill` from Gate-before-confirm to requirement discovery / Domain Grill.
- Step 1.3 says overview auto-passes after two clean-context reviews.
- Step 1.4 says detail stops for user confirmation after two clean-context reviews.
- Step 1.6 says `guru_gate.py check` enforces the new model.

### Gate SSOT

Update every platform's `harness/gate/gate-confirmation-model.md`:

- `guru-template/specs/guru-flutter-client/...`
- `guru-template/specs/guru-go-backend/...`
- `guru-template/specs/guru-ios-native/...`
- `guru-template/specs/guru-h5-web/...`

Also update each platform's `harness/detail/detail-structure-single-source.md` where it treats "overview confirmed" as the prerequisite. The new prerequisite is current overview structure plus two clean overview review records.

### Brainstorm

Update common brainstorm templates:

- `packages/cli/src/templates/common/skills/brainstorm.md`
- `packages/cli/src/templates/codex/skills/brainstorm/SKILL.md`
- `packages/cli/src/templates/copilot/prompts/brainstorm.prompt.md`

Add requirement context reconnaissance and Domain Grill Subroutine.

Template tests must assert the load-bearing brainstorm contracts instead of relying only on grep:

- repository-answerable questions must not be asked
- current code vs user intent conflicts must produce a conflict list
- Domain Grill trigger list is present
- `CONTEXT.md` is reserved for confirmed long-term glossary decisions
- ADR creation requires the three conditions: hard to reverse, surprising without context, and a real tradeoff

Also sync or verify worktree-installed copies used for dogfooding:

- `.agents/skills/trellis-brainstorm/SKILL.md`
- `.claude/skills/trellis-brainstorm/SKILL.md`
- `.cursor/skills/trellis-brainstorm/SKILL.md`
- `.opencode/skills/trellis-brainstorm/SKILL.md`
- `.pi/skills/trellis-brainstorm/SKILL.md`

Do not hand-maintain divergent wording in each copy if a project script can apply the template. If no script exists, make the copied edits intentionally and verify all copies contain the same Domain Grill contract.

### Review Skills

Update platform overview/detail review skills:

- `client-design-overview-review`
- `client-design-detail-review`
- `go-design-overview-review`
- `go-design-detail-review`
- `ios-design-overview-review`
- `ios-design-detail-review`
- `h5-design-overview-review`
- `h5-design-detail-review`

Each review output must include the recordable evidence fields or exact `guru_gate.py record-review` command.

Each review skill must also state the loop decision:

- `REQ_BLOCKER` -> stop planning loop and return to requirements.
- `OVERVIEW_DEFECT` -> fix overview and repeat overview review.
- `DETAIL_DEFECT` -> fix detail and repeat detail review.
- `PROCESS_DEFECT` -> fix workflow/process artifact and repeat the affected review.
- clean -> run `record-review` and continue only if the current digest has fewer than two clean reviews.

Overview review must not tell the user to confirm overview. Detail review may ask for user confirmation only after the second clean review for the current digest is recorded.

### Planning Writing Skills

Update platform overview/detail writing skills where they mention old Gate prerequisites or "overview confirmed" wording. They should point to current requirements confirmation, overview double-clean evidence, and detail confirmation only after detail double-clean evidence.

Review-output reference files under overview/detail review skill directories must match the same `record-review` contract and must not keep `confirm overview` as the normal path.

### Implementation Skills

Update all implementation writing/review skills for Flutter, Go, iOS, and H5 so the comment/log/trace DoD is consistent.

The Flutter skills already contain much of this language; use them as the baseline rather than inventing a new standard.

The comment DoD must keep the issue-level default: newly added classes, properties, and methods need requirement/design-linked Chinese comments unless they are generated code, trivial boilerplate accessors, or tiny private helpers whose purpose is obvious from surrounding commented code.

Implementation review skills must output the same routing classes used by the supervision loop:

- `IMPLEMENT_DEFECT`
- `PROCESS_DEFECT`
- `DETAIL_DEFECT`
- `OVERVIEW_DEFECT`
- `REQ_BLOCKER`
- clean/final-verification-ready

### Hooks

Update `guru-template/overlay/hooks/platform/block-unconfirmed-start.sh` wording.

The hook should still call `guru_gate.py check`, but any failure message should point to:

```bash
python3 .trellis/scripts/guru/guru_gate.py status <task_dir>
```

It must not hard-code "three human Gates" or tell users to confirm overview.

### Overlay Install and Config Text

Update overlay install/config text that users see when hooks are applied:

- `guru-template/overlay/apply.sh`
- `guru-template/overlay/config-snippets/config.hooks.yaml`
- `guru-template/overlay/config-snippets/worktree.verify.yaml`

These files must describe the new `guru_gate.py check/status/auto` model rather than "three human Gate" confirmation. `worktree.verify.yaml` must make the `auto` progressive-pass meaning explicit: exit 0 means the currently existing artifacts pass current checks, not that all five phases are complete.

## Template Sync

`guru-template/` is the source of truth. After source edits:

```bash
pnpm -C packages/cli sync:guru
```

This regenerates:

- `packages/cli/src/templates/guru/specs/`
- `packages/cli/src/templates/guru/workflows/`
- `packages/cli/src/templates/guru/overlay/`

Do not hand-maintain packaged copies unless a sync script defect is being fixed.

## Testing Strategy

Use the existing shell fixture first:

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
```

Add focused cases:

- overview one clean review blocks
- overview two clean reviews pass without human confirmation
- overview medium+ finding blocks and resets streak
- overview low-only clean observation still counts toward clean streak
- duplicate overview `run_id` does not count as two clean reviews
- overview artifact mutation blocks after prior clean reviews
- detail two clean reviews still blocks without detail confirmation
- detail two clean reviews plus detail confirmation passes
- `auto` does not require old overview/detail `design-grill` records
- `auto` reports missing overview/detail review evidence instead of asking for `grill-done`
- `auto` preserves progressive planning behavior before overview/detail artifacts exist
- `worktree.verify.yaml` and its packaged copy describe `auto` as progressive current-artifact verification, not five-phase completion
- `REQ_BLOCKER` status routes back to requirements
- stored `clean_streak=2` with insufficient current clean `review_runs` still blocks
- stored `auto_passed=true` with insufficient current clean `review_runs` still blocks
- old grill records do not unblock new model
- `confirm overview` fails with migration guidance
- `record-review` appears in top-level usage and is routed by `main()`
- clean review accepts `--max-severity none|low`, rejects `--finding-class`, and rejects medium+ severity
- findings review requires `--finding-class`, `--run-id`, and medium+ severity
- before-start hook failure points to `guru_gate.py status`, not `confirm overview`
- `overview`, `detail`, and `implement-check` dry-runs exit 0 and show the expected parser/action-map output, skill paths, routing keywords, and stop conditions
- `implement-check` dry-run shows implement skill, check skill, defect routing keywords, single-clean MVP rule, clean/final-verification-ready evidence summary, no implementation `guru_gates`, final validation stop, and hard-boundary stop
- implementation review skill output includes implementation/upstream defect routing classes plus clean/final-verification-ready evidence summary
- brainstorm template tests cover repo-answerable questions, code-vs-intent conflict lists, Domain Grill triggers, `CONTEXT.md` write protection, and ADR three-condition creation

Then run packaging checks:

```bash
pnpm -C packages/cli test -- test/guru/guru-bundled.test.ts
pnpm -C packages/cli typecheck
pnpm -C packages/cli build
```

If touched TypeScript behavior expands beyond template packaging, run broader focused tests before full suite.

## Rollback

Rollback is file-level:

- revert `guru-template/` changes
- rerun `pnpm -C packages/cli sync:guru`
- rerun focused tests

Because the new evidence lives in `task.json`, no database migration is needed. Existing active tasks with legacy evidence fail closed and can be repaired by recording new review evidence.

## Risks

### RISK-1: Review evidence can be forged by an agent.

This is already true for `task.json`-based workflow evidence. The goal is process integrity, not cryptographic security. Preserve clear audit fields and fail closed on missing/stale evidence.

### RISK-2: Existing active Guru tasks may be mid-flow.

Old `overview` confirmations should not silently pass. Status output must explain the new requirement and give the exact next command.

### RISK-3: Documentation drift across four platform workflows.

Use shared wording where possible, then sync packaged copies. Packaging tests should assert key new phrases exist.

### RISK-4: Over-checking comments/logs with scripts creates false positives.

Keep deterministic script checks small. Let review skills judge semantic comment/log quality.
