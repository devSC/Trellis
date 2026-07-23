# Current gaps: runtime acceptance and Full repair continuation

## Scope of this research

This note records repository and session evidence for planning. It does not authorize implementation and does not propose changes to Trellis scripts.

## Session regression case

Source session: `019f666f-832a-7eb2-a460-abdcef26a649`.

Observed sequence:

1. Focused validation reported `52/52 passed` and the change was described as `COMMIT_READY`.
2. The user ran the real Character Chat path and reported that the API response was correct but the UI still showed loading.
3. A later user retry still did not display the role.
4. The eventual root cause was a missing cross-layer field mapping:
   - `chats:detail` returned structured `userRole`;
   - the client still read the legacy top-level `userRoleCardId`;
   - DTO/repository resolution therefore produced absence;
   - the use case could not resolve the role;
   - the controller remained loading.
5. Existing tests covered the role-card list/profile repository behavior, but did not falsify the broken path `detail -> DTO -> Repository -> UseCase -> Controller -> UI label`.
6. When the failure was reported, authority and planning-Gate rules routed the work back through Full planning. The session eventually obtained only a clean Overview; it did not deliver the production repair, full regression, or user re-verification.

## Repository evidence

### General implementation and review contracts

- `.codex/agents/trellis-implement.toml` requires scoped work and spec compliance but does not require a user-visible acceptance closure or runtime receipt.
- `.codex/agents/trellis-check.toml` asks the reviewer to inspect actual code paths and tests, but does not bind completion to a falsifiable user journey or target-environment result.
- `.agents/skills/trellis-check/SKILL.md` makes data-flow review conditional on changes touching three or more layers. A one-layer DTO change can still determine a cross-layer user outcome, so the trigger is too narrow.

### Guru Flutter packet constraints

- `flutter-implementation-guru-writing` correctly restricts Full/high ordinary workers to packet-declared targets and checks. This preserves ownership but also means an incomplete packet can produce locally consistent green evidence.
- `flutter-implementation-guru-review` treats packet invariants and injected requirements/design as line-level authority and normally forbids undeclared tests. It also scopes review to the diff and direct dependencies. These rules need an explicit route for real runtime evidence that disproves an incomplete or incorrect planning baseline.
- The reviewer already supports `REQ_BLOCKER`, `OVERVIEW_DEFECT`, `DETAIL_DEFECT`, `PROCESS_DEFECT`, and `IMPLEMENT_DEFECT`; repair continuation can reuse those classes without adding a script or schema.

### Completion and repair behavior

- `.agents/skills/trellis-finish-work/SKILL.md` archives the active task after dirty-path checks. It has no runtime-acceptance-pending check.
- `guru-bug-fast-path` is useful for affinity and bounded repair, but it still follows the current Full gates and cannot prevent premature task completion.
- `trellis-break-loop` provides the right retrospective shape, but it is on-demand and is not automatically tied to a user-reported post-implementation failure.
- Current task lifecycle has no documented `reopen` command. Without script changes, archived Full tasks cannot inherit a machine-verified baseline or reopen in place.

### Detail review precondition mismatch in the Trellis source repository

The planning run exposed a separate `PROCESS_DEFECT` before Detail semantic review:

- This checkout declares `guru.platform: cli`, and its installed `.trellis/spec/` contains CLI, docs-site, and generic guide specs. It does not contain the platform harness Detail L1/L2 files, `guides/golden-path.md`, or `conventions/project-conventions.md`.
- `guru_gate.py detail` reads the installed Detail L1 taxonomy when present, but falls back to Flutter v1 types when it is absent. The current `usecase` and `repository-datasource` chapters therefore pass the machine structure Gate even though no matching installed target-repository SSOT exists.
- `client-design-detail-review` correctly requires the installed `.trellis/spec/harness/detail/` L1/L2 SSOT, `golden-path.md`, and a validated project-conventions file. Independent clean-context reviewers therefore stopped at the EX precondition instead of inventing a waiver or treating canonical source templates as installed project SSOT.
- The public CLI has no standalone spec-only install/sync command. `trellis init --template ... --append` continues through full initialization; `trellis update` also collects scripts, workflow, agents, and platform templates; `guru apply` supports only Flutter, Go, iOS, and H5 and refreshes scripts, hooks, workflow, skills, and specs together.
- Installing the Flutter spec package into this CLI/framework-maintenance checkout would satisfy path presence while introducing the wrong project conventions and platform semantics. It is not a valid repair.

The current Detail digest must not receive a clean review until this precondition is resolved through an explicitly authorized, repository-appropriate SSOT/review profile. A future framework-maintenance task should provide either a real CLI/framework Detail profile or another explicit canonical review contract; this task must not self-waive the EX blocker or modify Trellis/Guru scripts to work around it.

### Confirmed maximum-rollback decision

On 2026-07-20 the user explicitly confirmed that this missing profile is handled
as a same-goal `PROCESS_DEFECT` in the current task. Requirements semantics and
the confirmed Requirements digest remain unchanged. The maximum necessary
planning rollback is Overview plus affected Detail; no new Full task is opened.

The task-local bootstrap contract is
`research/framework-source-maintenance-detail-profile.md`. It defines an honest
CLI/framework taxonomy and review method without pretending that source
templates are installed project SSOT. This confirmation authorizes planning
artifact repair only. Actual repo-local spec/Skill promotion, `task.py start`,
implementation, commit, push, archive, and every script change remain
unauthorized.

## Root-cause classification

The session failure was not only an implementation typo. It was a combined failure:

| Class | Failure |
| --- | --- |
| Implementation | The DTO/repository path did not consume the new structured `userRole` response. |
| Test design | The passing suite did not contain an assertion that would fail when `detail.userRole` was ignored. |
| Detail/packet | The verification packet did not require the full source-to-sink Character Chat outcome. |
| Review | Review accepted packet-local evidence without proving the user-visible terminal state. |
| Completion process | Technical checks were treated as completion before runtime acceptance in the real path. |
| Repair workflow | A same-goal failure was handled as renewed Full planning rather than a bounded continuation with the smallest necessary rollback. |

## No-script design boundary

The approved implementation surface is limited to Skill, workflow, spec, agent instruction, and packaged-template documentation. Therefore this task can design and later implement:

- a required Acceptance Closure Matrix;
- runtime acceptance evidence conventions in existing task-local JSONL evidence;
- Skill-level prevention of premature archive;
- defect classification and maximum rollback rules;
- scoped reuse of unchanged slice/review evidence;
- source/template mirror parity checks.

It cannot honestly provide, without future separately approved script work:

- a new executable `repair-intake` command;
- a `task.py reopen` lifecycle transition;
- automatic baseline inheritance for archived tasks;
- dependency-graph-based digest invalidation;
- script-enforced commit/archive blocking based on runtime receipts.

The practical prevention mechanism is therefore to keep runtime-required Full tasks active until runtime acceptance passes. Skill/workflow compliance can strongly direct agents, but it is not a script-level fail-closed boundary.
