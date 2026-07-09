# Prepare Guru repeated-debug hardening plan artifacts

## Goal

Convert `drafts/guru-repeated-debug-install-hardening-plan.md` into task-local Trellis planning artifacts that can be reviewed, refined, and later used as the input for a separate full-chain implementation task.

This is a lite, documentation-only planning slice. It must not change Guru runtime behavior, gate logic, schema validators, templates, packaged assets, tests, install scripts, or target-repo behavior.

## Background

The draft plan captures the root causes exposed by repeated "deep dive" debugging and repeated plan reviews:

- implementation started without an explicit state machine, writer inventory, authority matrix, and liveness model;
- repeated-debug/stateful/cache-sync signals were not promoted early enough into a full workflow;
- implementation review, commit evidence, spec writeback, and install verification lacked a single frozen acceptance chain;
- repeated reviews kept finding new issues because prior repairs checked the latest finding rather than the original questions and full matrix.

The user first asked to implement the full plan. Guru intake classified the full implementation as `full_chain` and `risk=high` because it would touch gate/schema/runtime/template/install surfaces. The user then explicitly selected the smaller option: create a lite task that prepares PRD/design/implementation planning artifacts only.

## Confirmed Facts

- Source draft: `drafts/guru-repeated-debug-install-hardening-plan.md`.
- Current task: `.trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/`.
- Contract: `gate-contract.json` is `route=lite_task`, `risk=medium`.
- Scope is limited to this task's planning/contract artifacts. The source draft is reference-only for this lite task and is not a writable surface.
- The full implementation remains out of scope for this task because it changes Guru gate/schema/template/install behavior and must be handled by a separate `full_chain` task.
- Repository evidence inspected:
  - `drafts/guru-repeated-debug-install-hardening-plan.md`
  - `.trellis/spec/guides/index.md`
  - `.trellis/spec/cli/backend/index.md`
  - `.trellis/spec/cli/unit-test/index.md`
  - `guru_gate.py intake` outputs for both full implementation and docs-only planning scope.

## Requirements

### REQ-001 Preserve the original problem chain

The task artifacts must preserve the original-question coverage from the draft:

- why implementation still had bugs after coding;
- which project configuration/gate problems repeated "deep dive" exposed;
- how the repository must be optimized so installed targets actually receive the behavior;
- why repeated reviews kept finding new issues;
- how a future implementation will prove complete satisfaction.

### REQ-002 Keep the lite boundary explicit

The artifacts must state that this task does not implement the Guru hardening itself. Any runtime/schema/template/package/install behavior change belongs to a future `full_chain` task.

### REQ-003 Convert the draft into actionable planning surfaces

The task must create or update:

- `prd.md`: user goal, facts, requirements, out-of-scope items, acceptance criteria;
- `design.md`: planning artifact structure, traceability approach, scope boundary, and handoff shape;
- `implement.md`: ordered checklist, validation commands, and guardrails for this lite task and for the later full-chain task.

### REQ-004 Preserve review-loop prevention

The artifacts must make the frozen review rule explicit: future reviews must re-check original-question coverage, field ownership, gate contract, four install surfaces, fixture validity, and live code facts, rather than only checking the latest finding.

### REQ-005 Prepare a clean handoff to the later full-chain task

The artifacts must leave a clear boundary for the later task:

- future task route: `full_chain`;
- future implementation title suggestion: `Harden Guru repeated-debug state-model gates after install`;
- future implementation must start from the original draft and this task package;
- this lite task must not claim those future checks have passed.

## Out Of Scope

- Editing `.trellis/scripts/guru/*.py`.
- Editing `guru-template/**`.
- Editing `packages/cli/src/templates/guru/**`.
- Editing `packages/cli/test/**`.
- Editing `drafts/guru-repeated-debug-install-hardening-plan.md`; it is source material for this task, not an output artifact.
- Adding or changing schema validators, review normalization, commit gates, state model validators, preflight helpers, or install smoke tests.
- Starting the future full-chain implementation task.
- Committing, archiving, or running finish-work unless separately requested.

## Acceptance Criteria

- [x] `prd.md` states the docs-only goal, confirmed facts, requirements, acceptance criteria, and out-of-scope boundaries.
- [x] `design.md` maps the draft sections into task-local planning and future full-chain implementation surfaces.
- [x] `implement.md` contains an ordered checklist and verification commands for this lite task.
- [x] `implement.jsonl` and `check.jsonl` contain real references and no placeholder example rows.
- [x] `gate-contract.json` allows only task-local planning/contract artifacts, not the source draft or runtime/schema/template/package paths.
- [x] The artifacts explicitly say that original full implementation remains a separate `full_chain` task.
- [x] The artifacts preserve the "original questions -> mechanism -> evidence" coverage requirement.
- [x] Validation confirms the key artifacts exist, markdown fences are balanced, and no source/runtime/template/package paths were modified by this task.

## Implementation Evidence

- Loaded all `implement.jsonl` references before editing: the source draft plan, shared thinking-guide index, CLI backend index, and CLI unit-test index.
- Confirmed `check.jsonl` points to real task-local validation surfaces and contains no placeholder rows.
- Left `drafts/guru-repeated-debug-install-hardening-plan.md` and all runtime, schema, template, package, test, and install behavior unchanged.
- Preserved the future boundary: behavior hardening still requires a separate `full_chain` task titled `Harden Guru repeated-debug state-model gates after install`.
- Spec update decision: no `.trellis/spec/` update is required for this lite task because it adds no new command/API/schema contract, no reusable coding convention, and no runtime behavior; the future full-chain task must revisit spec updates when it implements Guru hardening behavior.

## Open Questions

None. The user chose the lite planning slice by answering `2` after being offered a full implementation path versus a scoped planning-artifact path.

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`.
- Repository evidence inspected: current draft plan, task contract, Trellis phase guidance, guide indexes, CLI backend and unit-test indexes.
- Domain/terminology triggers: "implement the plan" was split into a full-chain implementation meaning and a lite planning-package meaning.
- Current code vs user intent conflicts: Guru intake correctly classifies the full implementation as high-risk/full-chain; the user intentionally selected the docs-only lite slice instead.
- Product decisions confirmed:
  - decision: Prepare task PRD/design/implement artifacts only.
  - user_quote: `2`
  - result: This task is scoped to planning artifacts; full implementation is deferred.
- Open product/scope/risk questions: none for the lite planning package.

## Notes

- If a future turn asks to actually change Guru behavior, rerun `guru_gate.py intake` against the implementation paths and create a separate `full_chain` task.
