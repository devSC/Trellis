# Implementation Plan

## 1. Authorization Boundary

This file governs repaired and remaining execution. The task is already
`in_progress`, and the isolated control worktree contains the four ordinary
source commits through `b80af268d959e91314573014f912c9b02f4a1272`. The
current `OVERVIEW_DEFECT` rolls back only Overview plus affected Detail and
pauses further production edits; it does not reset Requirements or authorize a
second `task.py start`.

Before any later edit outside this task directory:

- obtain current independent Overview and Detail reviews plus the user's two
  digest-bound confirmations;
- keep task route `full_chain`, risk `high`;
- preserve the confirmed Requirements Gate and only refresh the affected
  Overview/Detail/downstream chain;
- resume in the existing isolated control worktree only after its base and
  cleanliness are reverified; do not rerun `task.py start`;
- do not treat these planning repairs or confirmations as permission for any
  forbidden path, lifecycle action, or fresh installed-target claim.

## 2. Non-Negotiable Guardrails

- Do not modify any Trellis-owned script file.
- Do not modify `.trellis/scripts/**`, Guru verify/hooks/apply scripts, packaged script mirrors, CLI TypeScript runtime, Python files, or shell files.
- Make no change outside `gate-contract.json.scope.allowed_paths`.
- If implementation requires a script/schema/parser/lifecycle change, stop and request a separately scoped task and explicit approval; do not smuggle it into this task.
- Keep ordinary slice ownership, Integration regression, Review provider, snapshot binding, and existing Full risk standards intact.
- Do not claim Skill/workflow enforcement is script-level fail-closed enforcement.
- Leave all unrelated dirty/staged/untracked work untouched.
- Do not commit, push, merge, archive, or run finish-work unless separately requested.

## 3. Planned Implementation Slices

The Detail phase has frozen exact ownership in §9. The concern groups below remain the explanatory view; §9 and the task-local packets are authoritative for file ownership, dependencies, checks, and reviewer admission.

### Slice A: Acceptance closure contract

Owned concerns:

- define the Acceptance Closure Matrix in the cross-layer and Guru implementation specs;
- change the cross-layer trigger from “diff touches 3+ layers” to “accepted behavior crosses a boundary”;
- require external contract fingerprint, source-to-sink trace, terminal state/liveness, negative cases, falsifiable check, runtime probe, and evidence owner;
- define technical verification versus runtime acceptance vocabulary.
- define exact `AcceptanceResolution`, complete ledger/register identities,
  both blocker sets, bounded append reconciliation, and invalidation.

Candidate source files:

- `packages/cli/src/templates/markdown/spec/guides/cross-layer-thinking-guide.md.txt`
- `packages/cli/src/templates/common/skills/check.md`
- `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md`

Required consumers:

- `.trellis/spec/guides/cross-layer-thinking-guide.md`
- `.agents/skills/trellis-check/SKILL.md`
- `packages/cli/src/templates/guru/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md`

### Slice B: Implementer and reviewer prevention

Owned concerns:

- make generic implement/check agents consume the closure matrix;
- require regression tests/probes that fail on the known wrong behavior;
- require bounded source-to-sink review for declared acceptance rows;
- allow real runtime failure to route an incorrect/incomplete SSOT upstream without permitting reviewer-authored product behavior;
- let missing packet checks produce `DETAIL_DEFECT`/`PROCESS_DEFECT` rather than packet-local false green;
- make Integration close all required runtime rows.
- require writer/reviewer/Integration to consume CH-01's exact canonical
  resolution without private projections or direct ledger selection.

Candidate source files:

- `packages/cli/src/templates/codex/agents/trellis-implement.toml`
- `packages/cli/src/templates/codex/agents/trellis-check.toml`
- `guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md`
- `guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md`

Required consumers:

- `.codex/agents/trellis-implement.toml`
- `.codex/agents/trellis-check.toml`
- matching Guru package consumers for the writing/review Skills.

### Slice C: Repair continuation and retrospective

Owned concerns:

- add same-acceptance-goal affinity rules;
- append `runtime_acceptance_failure` before repair;
- require CH-01 to recompute the complete post-append snapshot and select that
  failure before affinity, semantic classification, or production repair;
- use the shared maximum rollback table;
- reuse current unaffected receipts and invalidate affected evidence only;
- require direct root cause, earliest missed Gate, why tests/review stayed green, a new falsifiable probe, and a prevention disposition with either an owned writeback or an evidence-backed no-writeback reason;
- keep fast path verification strength equal to Full while avoiding repeated planning.

Candidate source files:

- `guru-template/overlay/agents-skills/guru-bug-fast-path/SKILL.md`
- `packages/cli/src/templates/common/skills/break-loop.md`

Read-only coordination input:

- `guru-template/workflows/guru-client-workflow.md` (mutable ownership belongs only to Slice D)

Required consumers:

- `packages/cli/src/templates/guru/overlay/agents-skills/guru-bug-fast-path/SKILL.md`
- `.agents/skills/trellis-break-loop/SKILL.md`

### Slice D: Runtime completion and archive protection

Owned concerns:

- define append-only `verification-evidence.jsonl` runtime rows;
- require runtime-required Full tasks to remain active while pending or failed;
- make finish-work inspect all required acceptance rows and stop before archive unless current pass exists;
- keep all raw-ledger replay/selection in CH-01; Finish consumes the exact fresh
  resolution and owns only allow/block;
- disclose that direct script invocation is not blocked because scripts are unchanged;
- document the archived-task fallback and its limitation.

Candidate source files:

- `packages/cli/src/templates/common/commands/finish-work.md`
- `guru-template/workflows/guru-client-workflow.md`

Required consumers:

- `.agents/skills/trellis-finish-work/SKILL.md`
- `packages/cli/src/templates/guru/workflows/guru-client.md`

### Integration Slice: Contract parity and scenarios

Owned concerns:

- ensure status names, affinity rules, defect routing, and archive conditions are identical across all consumers;
- ensure no ordinary writer/reviewer rule weakens Integration or Full verification;
- run the session `019f666f-832a-7eb2-a460-abdcef26a649` scenario as a documentation/contract regression;
- prove no forbidden script path changed.

Integration does not receive permission to rewrite Slice A-D source ownership. It closes their combined contract and writes only the 11 exact consumers derived from the 11 ordinary canonical sources.

## 4. Ordered Execution Checklist

1. **Reconfirm scope and impact**
   - Read `gate-contract.json`, `prd.md`, `design.md`, `implement.md`, and all JSONL references.
   - Capture `git status --short` by staged, unstaged, untracked, and dirty submodule state.
   - List allowed and forbidden paths before editing.
   - For any unexpected function/class/method edit, stop and run GitNexus upstream impact first; this plan does not expect symbol edits.

2. **Freeze contract vocabulary**
   - Use exactly: `implementation_verified`, `runtime_acceptance_pending`, `runtime_acceptance_failure`, `runtime_acceptance_pass`, `accepted`.
   - Treat these as evidence/reporting values, not new `task.json` lifecycle states.
   - Declare `runtime_acceptance_required=true` only in planning artifacts; do not add a task/Gate schema field or parser.
   - Use existing defect classes: `IMPLEMENT_DEFECT`, `PROCESS_DEFECT`, `DETAIL_DEFECT`, `OVERVIEW_DEFECT`, `REQ_BLOCKER`.
   - Use the same maximum rollback table in every consuming Skill/workflow.

3. **Implement Slice A**
   - Add the Acceptance Closure Matrix contract to source specs.
   - Update generic check behavior so acceptance-path boundaries trigger source-to-sink review.
   - Preserve single-layer checks; remove only the incorrect implication that cross-layer acceptance is skipped when the diff is local.
   - Leave all three mapped consumers to Integration; ordinary ownership stops at canonical sources.

4. **Implement Slice B**
   - Update implement/check agent contracts.
   - Update Flutter writer/reviewer contracts without expanding ordinary packet write scope.
   - Add wrong-SSOT routing and bounded missing-check findings.
   - Add Integration closure responsibility.
   - Leave all four mapped consumers to Integration.

5. **Implement Slice C**
   - Update fast-path affinity and maximum rollback behavior.
   - Update break-loop retrospective fields.
   - Treat the Guru workflow as read-only coordination input; Slice D is its sole canonical source owner.
   - Leave both mapped consumers to Integration.

6. **Implement Slice D**
   - Add runtime evidence/status handling to finish-work and Guru workflow.
   - Make archive stop on missing/stale/pending/failed required rows.
   - Add the no-script enforcement disclaimer and archived-task limitation.
   - Leave both mapped consumers to Integration.

7. **Run Integration contract review**
   - Do not dispatch Integration implementation through the installed supervisor; its current allowed write surface is all 22 packet review paths.
   - Verify the four ordinary commits/receipts are current, record the accepted Integration base commit, and create a clean disposable control worktree from that commit.
   - As coordinator, generate/reconcile only the 11 exact consumers from the 11 current ordinary sources.
   - Before staging, prove the ordinary canonical source diff is empty and the complete changed path set contains no path outside the 11-consumer allowlist.
   - Stage only the exact 11 consumers and prove the staged path set is set-equal to `integration_owned_paths`; subset, superset, rename, or untracked bypass fails containment.
   - If any ordinary source, extra path, stale receipt/base, missing consumer, or staged-set mismatch appears, abandon the disposable worktree and recreate it from the accepted ordinary commits; do not repair the contaminated worktree in place.
   - The installed supervisor may run only read-only semantic review after exact consumer-only staging.
   - Verify every consumer uses the same terms and routing.
   - Verify a packet-local green result cannot be called Accepted when a required runtime row is pending or failed.
   - Verify runtime failure routes upstream when it falsifies Detail/Requirement, instead of allowing reviewer-generated product behavior.
   - Verify unchanged sibling evidence is reusable only when current snapshot bindings remain valid.

8. **Run mirror parity checks**
   - Use byte comparison for files intended to be exact copies.
   - Use targeted normalized clause checks for platform-specific wrappers.
   - Inspect every mismatch; do not blindly overwrite user changes.

9. **Run forbidden-path audit**
   - Compare the final changed path set to allowed paths.
   - Fail the implementation if any forbidden glob matches.
   - Explicitly report zero Trellis script changes.

10. **Run task and repository validation**
    - Parse JSON/JSONL.
    - Validate task artifacts.
    - Run Markdown fence and whitespace checks.
    - Run repository lint/test commands that cover template/Skill contracts without editing or invoking install scripts.
    - Run GitNexus `detect_changes()` before any later commit, as required by repository policy.

11. **Stop at review-ready**
    - Report changed files, validations, remaining no-script limitations, and runtime scenario results.
    - Do not commit or run lifecycle actions without separate user authorization.

## 5. Contract Regression Scenarios

### Scenario 1: Technical green, runtime pending or invalid newest evidence

Given a Full task requires runtime acceptance, technical green without current runtime pass remains pending/active and finish-work blocks. CH-01 reads the complete raw ledger and durable retrospective reconciliation register before filtering. Its exact `AcceptanceResolution` contains `baseline_binding`, `ledger_snapshot_ref`, `reconciliation_snapshot_ref`, `open_correction_debts`, `open_retrospective_reconciliations`, `row_results`, selected/blocking refs, task result, blocking IDs, and `next_probe`. An open retrospective attempt outranks correction/row blockers and forces `next_probe=null`; later pending/pass cannot bypass it. Otherwise malformed/unreadable current appends create exact-position debt; only a complete matching correction closes it, never a normal later pass/wrong pointer/cross-ID relabel. All consumers preserve the complete object. Any ledger append, register update, or baseline change stales it.

### Scenario 2: Same-goal implementation defect

Given the user reports the already-approved Character Chat label still loads forever, and Detail correctly requires structured `detail.userRole`, when the DTO ignores that field, then classification is `IMPLEMENT_DEFECT`; Requirements/Overview/Detail remain current; affected implementation, Integration, and runtime evidence are refreshed.

### Scenario 3: Detail defect

Given the approved Detail itself requires only legacy `userRoleCardId`, when runtime evidence proves the actual contract uses structured `userRole`, then classification is `DETAIL_DEFECT`; repair returns to Detail and affected downstream evidence, not Requirements or Overview.

### Scenario 4: Material requirement change

Given the original acceptance only displays the current role, when the user asks to support multi-role selection and persistence, then affinity fails and the change returns to Requirements/full affected planning.

### Scenario 5: Wrong SSOT

Given a confirmed packet is internally green, when a current target-environment receipt shows its declared user outcome fails, then reviewer cannot dismiss the failure as packet-external. It routes the earliest owning defect without directly editing SSOT.

### Scenario 6: Unaffected sibling reuse

Given one acceptance row fails and its repair does not alter another slice's target bytes, invariants, inputs, checks, policy, or supervisor binding, then the sibling receipt remains reusable; changed Integration and runtime bindings are refreshed.

### Scenario 7: Archived legacy task

Given the original task was already archived, when a same-goal failure arrives, then caller-supplied `ArchivedFailureInput` carries the original acceptance ID, artifact digests, receipt refs, and sanitized new-failure artifact ref as immutable history. Repair checks reference metadata and affinity without reading a ledger or selecting a current row; the workflow creates a linked repair task/child and discloses that current scripts may still require Full gates. If the linked active task later appends the failure, CH-01 must resolve the complete new snapshot before affinity/classification/repair. No in-place reopen or machine baseline inheritance is promised.

### Scenario 8: Forbidden script pressure

Given an implementation idea requires modifying `guru_gate.py`, `task.py`, verify/hooks/apply, CLI TypeScript, Python, or shell scripts, when scope is checked, then implementation stops and requests new explicit authorization.

### Scenario 9: Integration retrospective prevention disposition

Given five fields/disposition, ClosureSpec persists ordinal-0 attempt with exact
TaskRef path, pre-ledger snapshot and row digest; root-v1/full replay ack precedes
append. Non-empty snapshot fields bind replay count/position, final newline event
SHA-256 and complete-file SHA-256. `deriveLedgerAppendRef(full_snapshot, position)`
uses only ledger artifact/position/exact newline append bytes, never journal ref.
Correlation fixtures cover older-valid/empty rollback, cross-position mismatch and
repeated identical rows; all block/null probe despite later pass. Accepted/unique
suffix committed yields only ref; every null record stays open. Repair builds ref,
then acknowledged `record-bound` closes exact ordinal-0 or 0+1 IDs. First absent
permits one ordinal-1; drift/non-unique/unreadable/second missing is ambiguous, with
no third retry, record, decision, probe or Finish bypass. Rejection remains open.

### Scenario 10: Detail producer/consumer resolution drift

Given CH-02 requires baseline binding, ledger/register snapshot provenance,
both open blocker sets, row results, selected/blocking refs, task result, IDs/probe,
when CH-01 produces a smaller or different `AcceptanceResolution`, then the
finding is `DETAIL_DEFECT`. Repair updates CH-01 and affected CH-02/CH-03/CH-04
plus packets/checks, refreshes Detail review/confirmation and downstream
evidence, and preserves confirmed Requirements and a still-correct Overview.

### Scenario 11: Overview currentness ownership drift

Given Detail has internally consistent dual-snapshot rules, when Overview still
allows consumers to resolve rows/register state or project away reconciliation,
then the finding is `OVERVIEW_DEFECT`. Repair returns to Overview plus affected
Detail/downstream, keeps `ClosureSpec` the single currentness owner, and does not
restart Requirements. A machine structural Gate passing before this semantic
repair is not sufficient evidence of completion.

### Scenario 12: Packet known-bad false green

Given control baseline `b80af268d959e91314573014f912c9b02f4a1272` still lets Finish read/select ledger rows and lacks the canonical resolution fields in ordinary consumers, when each ordinary packet runs its pre-repair focused checks, then at least one canonical-field/owner assertion or explicit legacy-algorithm rejection must fail. After that slice implements the repaired source contract, every packet `deterministic_checks` entry must pass. A broad alternation search that succeeds because any common word matches is forbidden evidence.

## 6. Validation Commands

These commands are planned for the later implementation. They inspect existing scripts but do not modify them.

```bash
TASK=.trellis/tasks/07-20-guru-runtime-acceptance-repair-continuation

python3 ./.trellis/scripts/task.py validate "$TASK"
jq empty "$TASK/task.json" "$TASK/gate-contract.json"
jq -c . "$TASK/implement.jsonl" >/dev/null
jq -c . "$TASK/check.jsonl" >/dev/null

for packet in "$TASK"/slice-packets/SL-{ACCEPTANCE-CLOSURE,IMPLEMENT-REVIEW,REPAIR-CONTINUATION,RUNTIME-COMPLETION}.json; do
  while IFS= read -r check; do
    sh -c "$check" || exit 1
  done < <(jq -r '.deterministic_checks[]' "$packet")
done

git diff --check -- "$TASK" \
  .codex/agents .agents/skills .trellis/spec/guides \
  guru-template/workflows guru-template/overlay/agents-skills \
  guru-template/specs/guru-flutter-client/harness/implementation \
  packages/cli/src/templates

git status --short --untracked-files=all -- \
  .trellis/scripts \
  guru-template/overlay/verify \
  guru-template/overlay/hooks \
  guru-template/overlay/apply.sh \
  packages/cli/src/templates/trellis/scripts \
  packages/cli/src/templates/guru/overlay/verify \
  packages/cli/src/templates/guru/overlay/hooks \
  packages/cli/scripts
```

The final validator must also inspect the complete changed path set for `.py`, `.sh`, and `packages/cli/src/**/*.ts`, because a clean status query on selected directories alone is insufficient in a dirty worktree.

## 7. Rollback Points

- **After Slice A**: revert its three canonical source contracts; Integration consumers are reconciled separately.
- **After Slice B**: writer and reviewer wording must roll back together; retaining only one side creates contradictory behavior.
- **After Slice C**: fast-path and break-loop contracts must roll back together; Slice C never owns the Guru workflow.
- **After Slice D**: finish-work and runtime status vocabulary must roll back together; otherwise tasks can remain pending without a completion consumer.
- **Integration**: any terminology or mirror mismatch blocks review-ready status.

No rollback step uses destructive Git commands or reverts unrelated work.

## 8. Resume Conditions Still Required

Before production implementation resumes:

- the user reviews and confirms the revised Overview/Detail planning package;
- required Full requirements/overview/detail reviews and digest-bound confirmation are current;
- context manifests are accepted;
- the no-script constraint remains in the Gate contract;
- exact source/template ownership is frozen in Detail;
- all four ordinary slice commits and current receipts precede Integration, and
  Integration uses the coordinator-only disposable-worktree route because the
  installed supervisor cannot enforce consumer-only writes;
- the task-local framework profile is the explicit Detail review contract and
  every reviewer discloses that the machine Gate does not parse its taxonomy;
- permanent repo-local profile promotion is either explicitly authorized and
  added to the Gate/slice scope before Detail confirmation, or explicitly
  deferred without claiming the repository-wide profile defect is fixed;
- the existing `in_progress` task authority is rechecked; do not invoke a
  second guarded Full start.

Until then, task status remains `in_progress` but production source and
Integration edits are paused at the Overview/Detail rollback boundary.

## 9. Full/High Slice Planning Audit

This audit is the Detail-frozen implementation grouping. It derives four ordinary slices from disjoint file ownership and independent commit/rollback value, not from one chapter, UNIT, doc_type, or conceptual layer per slice. All ordinary `depends_on=[]`: their shared vocabulary, schemas, error meanings, maximum rollback table, Acceptance Closure Matrix, and mirror map are frozen in the confirmed Detail package, so no ordinary slice must read another slice's produced bytes.

Implementation must occur in a clean isolated control worktree created from the later authorized baseline. The current dirty worktree is read-only background and is never packet-allowlisted. Ordinary text-only workers may edit their disjoint paths in `parallel_wave=1`; formal staging, review, commit, and receipt remain serial in the control worktree. `guru_gate.py slice-plan` may conservatively serialize because the Integration review coverage intentionally overlaps the ordinary target union; that output does not change the file-level ordinary ownership audit below.

Common ordinary rule: disjoint listed paths only; no shared output or package/build/sync/install action. In `check_wave=1`, run the packet checks verbatim/in order, record non-zero known-bad at `b80af268d959e91314573014f912c9b02f4a1272`, then require all zero. At review, reread each ordered inventory, record its exact total, and block above 262144.

### SL-ACCEPTANCE-CLOSURE

- `packet`: `slice-packets/SL-ACCEPTANCE-CLOSURE.json`
- `owner_unit`: `UNIT-acceptance-closure-contract`
- `covered_units`: [`UNIT-acceptance-closure-contract`]
- `read_paths`:
  - `prd.md`
  - `research/framework-source-maintenance-detail-profile.md`
  - `design-package/design-main.md`
  - `design-package/chapters/acceptance-closure-contract.md`
  - `implement.md`
  - `guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md` (framework guidance, read-only for this slice)
- `owned_paths`:
  - `packages/cli/src/templates/markdown/spec/guides/cross-layer-thinking-guide.md.txt`
  - `packages/cli/src/templates/common/skills/check.md`
  - `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md`
- `depends_on`: []
- `parallel_wave`: 1
- `resource_locks`: []
- `resource_isolation`: common ordinary rule.
- `check_wave`: 1
- `focused_checks`: common rule for this packet.
- `independent_commit_value`: reusable closure/evidence policy independent of consumers.
- `rollback_contract`: revert all 3 sources together; Integration reconciles mapped consumers.
- `review_context_inputs` (ordered planning-baseline inventory):
  1. `slice-packets/SL-ACCEPTANCE-CLOSURE.json`, whole file, UTF-8 bytes=9825.
  2. `prd.md`, whole file, UTF-8 bytes=22979.
  3. `research/framework-source-maintenance-detail-profile.md`, whole file, UTF-8 bytes=12442.
  4. `design-package/design-main.md`, whole file, UTF-8 bytes=49345.
  5. `design-package/chapters/acceptance-closure-contract.md`, whole file, UTF-8 bytes=45243.
  6. `implement.md`, whole file, UTF-8 bytes=38908.
  7. `packages/cli/src/templates/markdown/spec/guides/cross-layer-thinking-guide.md.txt`, whole current baseline file, UTF-8 bytes=19234.
  8. `packages/cli/src/templates/common/skills/check.md`, whole current baseline file, UTF-8 bytes=5166.
  9. `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md`, whole current baseline file, UTF-8 bytes=14376.
- `review_context_bytes`: 217518; common budget rule.
- `rejected_merge_candidates`:
  - `A+B`: rejected; policy and writer/reviewer consumers have independent value/rollback.
  - split A: rejected; its 3 files form one contract.

### SL-IMPLEMENT-REVIEW

- `packet`: `slice-packets/SL-IMPLEMENT-REVIEW.json`
- `owner_unit`: `UNIT-implementation-review-closure`
- `covered_units`: [`UNIT-implementation-review-closure`]
- `read_paths`:
  - `prd.md`
  - `research/framework-source-maintenance-detail-profile.md`
  - `design-package/design-main.md`
  - `design-package/chapters/implementation-review-closure.md`
  - `implement.md`
  - `design-package/chapters/acceptance-closure-contract.md`
- `owned_paths`:
  - `packages/cli/src/templates/codex/agents/trellis-implement.toml`
  - `packages/cli/src/templates/codex/agents/trellis-check.toml`
  - `guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md`
  - `guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md`
- `depends_on`: []
- `parallel_wave`: 1
- `resource_locks`: []
- `resource_isolation`: common ordinary rule.
- `check_wave`: 1
- `focused_checks`: common rule for this packet.
- `independent_commit_value`: writer/reviewer closure independent of repair/finish.
- `rollback_contract`: revert all 4 sources together; Integration reconciles their consumers.
- `review_context_inputs` (ordered planning-baseline inventory):
  1. `slice-packets/SL-IMPLEMENT-REVIEW.json`, whole file, UTF-8 bytes=7655.
  2. `prd.md`, whole file, UTF-8 bytes=22979.
  3. `research/framework-source-maintenance-detail-profile.md`, whole file, UTF-8 bytes=12442.
  4. `design-package/design-main.md`, whole file, UTF-8 bytes=49345.
  5. `design-package/chapters/implementation-review-closure.md`, whole file, UTF-8 bytes=28662.
  6. `design-package/chapters/acceptance-closure-contract.md`, whole file, UTF-8 bytes=45243.
  7. `implement.md`, whole file, UTF-8 bytes=38908.
  8. `packages/cli/src/templates/codex/agents/trellis-implement.toml`, whole current baseline file, UTF-8 bytes=4160.
  9. `packages/cli/src/templates/codex/agents/trellis-check.toml`, whole current baseline file, UTF-8 bytes=6185.
  10. `guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md`, whole current baseline file, UTF-8 bytes=9871.
  11. `guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md`, whole current baseline file, UTF-8 bytes=16937.
- `review_context_bytes`: 242387; common budget rule.
- `rejected_merge_candidates`:
  - `B+A`: rejected; consumer and policy ownership are independently reviewable.
  - split B: rejected; TOML/Flutter writer-reviewer semantics roll back together.

### SL-REPAIR-CONTINUATION

- `packet`: `slice-packets/SL-REPAIR-CONTINUATION.json`
- `owner_unit`: `UNIT-repair-continuation`
- `covered_units`: [`UNIT-repair-continuation`]
- `read_paths`:
  - `prd.md`
  - `research/framework-source-maintenance-detail-profile.md`
  - `design-package/design-main.md`
  - `design-package/chapters/repair-continuation.md`
  - `design-package/chapters/acceptance-closure-contract.md`
  - `implement.md`
  - `guru-template/workflows/guru-client-workflow.md` (read-only; Slice D is the only mutable owner)
- `owned_paths`:
  - `guru-template/overlay/agents-skills/guru-bug-fast-path/SKILL.md`
  - `packages/cli/src/templates/common/skills/break-loop.md`
- `depends_on`: []
- `parallel_wave`: 1
- `resource_locks`: []
- `resource_isolation`: common ordinary rule.
- `check_wave`: 1
- `focused_checks`: common rule for this packet.
- `independent_commit_value`: bounded same-goal repair/retrospective independent of finish.
- `rollback_contract`: revert both sources together; Integration reconciles consumers.
- `review_context_inputs` (ordered planning-baseline inventory):
  1. `slice-packets/SL-REPAIR-CONTINUATION.json`, whole file, UTF-8 bytes=11518.
  2. `prd.md`, whole file, UTF-8 bytes=22979.
  3. `research/framework-source-maintenance-detail-profile.md`, whole file, UTF-8 bytes=12442.
  4. `design-package/design-main.md`, whole file, UTF-8 bytes=49345.
  5. `design-package/chapters/repair-continuation.md`, whole file, UTF-8 bytes=35001.
  6. `design-package/chapters/acceptance-closure-contract.md`, whole file, UTF-8 bytes=45243.
  7. `implement.md`, whole file, UTF-8 bytes=38908.
  8. `guru-template/overlay/agents-skills/guru-bug-fast-path/SKILL.md`, whole current baseline file, UTF-8 bytes=33059.
  9. `packages/cli/src/templates/common/skills/break-loop.md`, whole current baseline file, UTF-8 bytes=12499.
- `review_context_bytes`: 260994; common budget rule.
- `rejected_merge_candidates`:
  - `C+D`: rejected; repair and finish have disjoint paths/value/rollback.
  - split C: rejected; affinity and retrospective must land together.

### SL-RUNTIME-COMPLETION

- `packet`: `slice-packets/SL-RUNTIME-COMPLETION.json`
- `owner_unit`: `UNIT-runtime-completion`
- `covered_units`: [`UNIT-runtime-completion`]
- `read_paths`:
  - `prd.md`
  - `research/framework-source-maintenance-detail-profile.md`
  - `design-package/design-main.md`
  - `design-package/chapters/runtime-completion.md`
  - `design-package/chapters/acceptance-closure-contract.md`
  - `design-package/chapters/repair-continuation.md`
  - `implement.md`
- `owned_paths`:
  - `packages/cli/src/templates/common/commands/finish-work.md`
  - `guru-template/workflows/guru-client-workflow.md`
- `depends_on`: []
- `parallel_wave`: 1
- `resource_locks`: []
- `resource_isolation`: common ordinary rule.
- `check_wave`: 1
- `focused_checks`: common rule for this packet.
- `independent_commit_value`: archive guard/handoff independent of writer and repair.
- `rollback_contract`: revert finish Skill/workflow together.
- `review_context_inputs` (ordered planning-baseline inventory):
  1. `slice-packets/SL-RUNTIME-COMPLETION.json`, whole file, UTF-8 bytes=6664.
  2. `prd.md`, whole file, UTF-8 bytes=22979.
  3. `research/framework-source-maintenance-detail-profile.md`, whole file, UTF-8 bytes=12442.
  4. `design-package/design-main.md`, whole file, UTF-8 bytes=49345.
  5. `design-package/chapters/runtime-completion.md`, whole file, UTF-8 bytes=25562.
  6. `design-package/chapters/acceptance-closure-contract.md`, whole file, UTF-8 bytes=45243.
  7. `implement.md`, whole file, UTF-8 bytes=38908.
  8. `packages/cli/src/templates/common/commands/finish-work.md`, whole current baseline file, UTF-8 bytes=8726.
  9. `guru-template/workflows/guru-client-workflow.md`, whole current baseline file, UTF-8 bytes=50563.
- `review_context_bytes`: 260432; common budget rule.
- `rejected_merge_candidates`:
  - `D+C`: rejected; archive admission and repair orchestration are independent.
  - split D: rejected; Skill/workflow must not contradict.

### Ordinary Ownership And Resource Proof

| slice | owned path count | pairwise same-wave intersection | depends_on | resource lock | check wave |
| --- | ---: | --- | --- | --- | ---: |
| `SL-ACCEPTANCE-CLOSURE` | 3 | empty | [] | none | 1 |
| `SL-IMPLEMENT-REVIEW` | 4 | empty | [] | none | 1 |
| `SL-REPAIR-CONTINUATION` | 2 | empty | [] | none | 1 |
| `SL-RUNTIME-COMPLETION` | 2 | empty | [] | none | 1 |

No ordinary slice owns a test file, runs a full regression, or writes package/build output. Four ordinary slices are the allowed default maximum. Every slice has independent contract value and a whole-slice rollback; no exception above four is used.

### SL-INTEGRATION

- `packet`: `slice-packets/SL-INTEGRATION.json`
- `owner_unit`: `UNIT-template-parity`
- `covered_units`: [`UNIT-acceptance-closure-contract`, `UNIT-implementation-review-closure`, `UNIT-repair-continuation`, `UNIT-runtime-completion`, `UNIT-template-parity`]
- `depends_on`: [`SL-ACCEPTANCE-CLOSURE`, `SL-IMPLEMENT-REVIEW`, `SL-REPAIR-CONTINUATION`, `SL-RUNTIME-COMPLETION`]
- `parallel_wave`: 2
- `target_paths`: the exact 22-path union enumerated in `slice-packets/SL-INTEGRATION.json` (11 ordinary canonical sources plus 11 tracked consumers used by the live source-to-install chain); no wildcard or directory shorthand is an ownership grant.
- `integration_owned_paths`:
  - `.codex/agents/trellis-implement.toml`
  - `.codex/agents/trellis-check.toml`
  - `.agents/skills/trellis-check/SKILL.md`
  - `.agents/skills/trellis-finish-work/SKILL.md`
  - `.agents/skills/trellis-break-loop/SKILL.md`
  - `.trellis/spec/guides/cross-layer-thinking-guide.md`
  - `packages/cli/src/templates/guru/workflows/guru-client.md`
  - `packages/cli/src/templates/guru/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md`
  - `packages/cli/src/templates/guru/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md`
  - `packages/cli/src/templates/guru/overlay/agents-skills/guru-bug-fast-path/SKILL.md`
  - `packages/cli/src/templates/guru/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md`
- `resource_locks`: [`node_package_manager`, `git_index`]
- `resource_isolation`: serial coordinator-only reconciliation from accepted ordinary commits; supervisor implementation dispatch forbidden. Require empty source diff and exact 11-consumer staged set; stale/missing/extra mismatch abandons the worktree. Build output stays isolated; ignored `dist` is not source.
- `check_wave`: 2
- `focused_checks` / final regression:
  - `pnpm --filter @devsc/trellis run sync:guru:check`
  - `pnpm --filter @devsc/trellis test`
  - `pnpm --filter @devsc/trellis run build`
  - `git diff --check`
  - `git status --short --untracked-files=all -- .trellis/scripts guru-template/overlay/verify guru-template/overlay/hooks guru-template/overlay/apply.sh packages/cli/src/templates/trellis/scripts packages/cli/src/templates/guru/overlay/verify packages/cli/src/templates/guru/overlay/hooks packages/cli/scripts`
- `independent_commit_value`: source/consumer parity, combined scenarios, regression and scope proof.
- `rollback_contract`: revert all 11 consumers together; regenerate later or revert matching ordinary sources, never leave drift.
- `review_context_inputs` (ordered planning-baseline inventory):
  1. `slice-packets/SL-INTEGRATION.json`, whole file, UTF-8 bytes=10266.
  2. `research/framework-source-maintenance-detail-profile.md`, whole file, UTF-8 bytes=12442.
  3. `implement.md`, whole file, UTF-8 bytes=38908.
  4. `design-package/chapters/template-parity.md`, whole file, UTF-8 bytes=29595.
  5. `slice-packets/SL-ACCEPTANCE-CLOSURE.json`, whole file, UTF-8 bytes=9825.
  6. `slice-packets/SL-IMPLEMENT-REVIEW.json`, whole file, UTF-8 bytes=7655.
  7. `slice-packets/SL-REPAIR-CONTINUATION.json`, whole file, UTF-8 bytes=11518.
  8. `slice-packets/SL-RUNTIME-COMPLETION.json`, whole file, UTF-8 bytes=6664.
  9. final scoped diff over the packet's 22 exact `target_paths`, planning baseline empty selection, UTF-8 bytes=0.
  10. ordinary current receipt selections, planning baseline absent, UTF-8 bytes=0.
  11. focused/full deterministic result summaries, planning baseline absent, UTF-8 bytes=0.
- `review_context_bytes`: 126873; add current diff/receipts/results, record exact total, block above 262144.
- `rejected_merge_candidates`:
  - with ordinary: rejected; Integration requires all receipts and owns only consumers.
  - second Integration: rejected; one union owner/regression.

`target_paths` are review coverage, not write authority. The supervisor grants
all 22, so Integration implementation remains coordinator-only under the
base/receipt/consumer-set proofs above; supervisor is read-only review after
staging. This is process containment, not script fail-closed. Any failure
abandons/recreates the worktree. Integration may report, not repair, an ordinary
source inconsistency.

### Framework Guidance Audit

The user-confirmed task-local CLI/framework profile is read-only review input,
not installed SSOT. Slice A solely owns trace, B writer/reviewer; other slices
read only. Workers cannot edit planning/audits or forge receipts; coordinator
owns Integration mirror/receipt evidence.

## 10. Detail Completion Audit

- Closure: 5/5 indexed, no orphan; all chapters use the task-local taxonomy and
  `passed_by_method_evidence`; BHV-001..008 have UNIT/tests/slices and §10 layer
  checkpoints. The machine Gate's Flutter fallback is not semantic evidence.
- Grouping: four disjoint ordinary slices plus one Integration; no mechanical
  chapter/layer split. Packets contain no forbidden target; changed-path audit
  remains mandatory.
- Runtime/deletion: `ACC-RUNTIME-001`..`ACC-PARITY-005` remain pending mutable
  evidence; all five chapters are additions and no confirmed contract was deleted.
- Boundary: fresh Overview/Detail reviews are still required. This audit does
  not authorize profile promotion, source/start/dispatch/lifecycle or Git actions.

## 11. Implement Gate Trace Index

### 计划与切片

§3/§9 and five packets freeze four disjoint ordinary slices plus Integration,
with exact owners/dependencies/checks/rollback/review inputs and 11-to-11 map.

### 执行与改动文件

§4 orders A-D (`3/4/2/2` sources) before coordinator-only Integration, which
uses a disposable worktree and writes exact 11 consumers, never the 22-path
supervisor implementation surface.

### 证据

§5/§6 require known-bad, focused/full checks, current receipts/snapshots, exact
staged set, runtime probes, semantic review, byte budgets and forbidden audit;
§9 binds review to packet inventory/current snapshot.

### 阻塞与偏差

Stop on dirty/non-isolated control, stale digest/receipt/base, missing consumer,
budget/forbidden/extra path, staged-set mismatch, or script/schema/lifecycle
need. Integration containment failure abandons/recreates from accepted ordinary
commits; supervisor limits are disclosed, never claimed fail-closed.
