# Design: Guru repeated-debug hardening plan artifacts

## Scope

This design covers only the conversion of the existing draft plan into Trellis task-local planning artifacts. It is not the technical design for implementing Guru gate/schema/runtime/template changes.

The output of this task is a durable planning package:

- `prd.md`: requirements and acceptance for the lite documentation slice;
- `design.md`: structure, traceability, and boundaries for the planning package;
- `implement.md`: execution checklist and validation commands;
- `implement.jsonl` and `check.jsonl`: compact references for future sub-agent context.

## Source Material

Primary source:

- `drafts/guru-repeated-debug-install-hardening-plan.md`

Relevant repository guidance:

- `.trellis/spec/guides/index.md`
- `.trellis/spec/cli/backend/index.md`
- `.trellis/spec/cli/unit-test/index.md`

The draft remains the source for the full-chain implementation proposal. This task package organizes it for Trellis workflow use and prevents later readers from mistaking the draft for already-implemented behavior.

## Traceability Model

The planning package preserves five required traceability lines from the draft:

| Draft Concern | Task Artifact Representation |
| --- | --- |
| Implementation still had bugs after coding | PRD requirement REQ-001 and future full-chain handoff notes |
| Repeated "deep dive" exposed gate/config weaknesses | PRD background and design future-task boundary |
| Install must prove target behavior, not just source behavior | PRD acceptance and implement validation reminders |
| Repeated reviews found new issues | PRD REQ-004 and implement self-review checklist |
| Future implementation must prove complete satisfaction | PRD REQ-005 and implement handoff checklist |

## Boundary Rules

This lite task may edit only task-local planning/contract artifacts. The draft plan is read-only source material for this completion pass. It must not edit the draft or source/runtime/template/package/install files.

The writable task-local surfaces recorded in `gate-contract.json` are:

- `.trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/prd.md`
- `.trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/design.md`
- `.trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/implement.md`
- `.trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/implement.jsonl`
- `.trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/check.jsonl`
- `.trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/gate-contract.json`

The read-only source reference for this task is:

- `drafts/guru-repeated-debug-install-hardening-plan.md`

If implementation scope expands beyond these surfaces, stop and create a separate full-chain task.

The later full-chain task must keep the draft's original questions -> mechanism -> evidence matrix as its acceptance baseline. This lite package preserves that traceability requirement; it does not claim the future evidence has passed.

## Future Full-Chain Handoff

The later implementation task should use:

- title: `Harden Guru repeated-debug state-model gates after install`;
- route: `full_chain`;
- risk: `high`;
- input artifacts:
  - this task directory;
  - `drafts/guru-repeated-debug-install-hardening-plan.md`;
  - current `gate-contract.json` as evidence that the present task intentionally did not implement runtime behavior.

The future task must rerun intake with the real implementation paths and must perform GitNexus impact analysis before editing any symbol.

## Validation Strategy

Validation for this lite task is artifact validation only:

- confirm required files exist;
- confirm JSONL manifests no longer contain placeholder rows;
- confirm markdown code fences are balanced;
- confirm key traceability phrases exist;
- confirm `gate-contract.json` allows only task-local planning/contract artifacts;
- confirm `git diff --check` passes for changed planning artifacts;
- confirm no source/runtime/template/package files were modified as part of this task.

No runtime tests are expected because this task intentionally makes no runtime behavior change.
