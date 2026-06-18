# Implement devSC/Trellis#2 Guru automated five-phase workflow

## Goal

Implement the workflow contract from `devSC/Trellis#2`: after the user confirms requirements, all non-requirement defects in the Guru five-phase flow are fixed, re-reviewed, and advanced by agents automatically until a real product decision or hard boundary is reached.

The change must preserve the existing Trellis task lifecycle (`planning` -> `in_progress`) and avoid adding a parallel task state machine. The durable control plane should remain the task artifacts and `task.json`.

## Source Requirement

- GitHub issue: https://github.com/devSC/Trellis/issues/2
- Current local evidence:
  - Guru workflows still describe three manual planning Gates.
  - `gate-confirmation-model.md` still treats `requirements`, `overview`, and `detail` as independent human confirmations.
  - `guru_gate.py check` currently blocks start unless all three stages have valid human confirmations and `design-grill` records.
  - `guru_gate.py auto` is a verify entrypoint and currently still enforces old `design-grill` prerequisites for planning artifacts.
  - `trellis-brainstorm` already has an evidence-first rule but does not yet include the explicit Domain Grill subroutine required by the issue.
  - `guru_supervise.py` currently supervises only implementation and final check actions, so planning-phase overview/detail repair loops still need an explicit driver contract.
  - The local `.agents/skills/trellis-brainstorm/SKILL.md` copy is the skill used in this worktree and must not remain stale when brainstorm templates are updated.

## Requirements

### R1. Human Gate Reduction

Human approval must be reduced to these boundaries:

- Requirements confirmation Gate.
- Detailed-design confirmation Gate, only after clean-context review evidence is clean twice.
- Hard-boundary Gate for commit, archive, finish-work, publish, external writes, and any other irreversible operation.

Overview design must not require user confirmation after requirements are confirmed.

### R2. Requirement Context Reconnaissance

Before asking requirement questions, `trellis-brainstorm` must inspect repository evidence first:

- code
- tests and fixtures
- configs
- docs and README files
- `.trellis/spec/`
- `CONTEXT.md`
- `CONTEXT-MAP.md`
- `docs/adr/`
- relevant Trellis task history when present

Questions answerable by repository evidence must not be asked to the user. Remaining questions must be product intent, scope, risk tolerance, or unresolved tradeoff decisions.

### R3. Domain Grill Subroutine

The domain-grilling behavior must move into the requirement discovery phase instead of remaining a separate post-draft Gate requirement.

The subroutine triggers only when evidence shows:

- new domain terms
- term conflicts with `CONTEXT.md` or `CONTEXT-MAP.md`
- overloaded or ambiguous wording
- unclear lifecycle, state, or ownership boundaries
- cross-context ownership ambiguity
- mismatch between current code facts and user intent

The subroutine must:

- point out term conflicts immediately
- recommend canonical terms for overloaded language
- pressure-test boundaries with concrete scenarios
- produce "current code vs user intent" conflict questions when code and requested behavior differ
- write only confirmed long-term glossary decisions to `CONTEXT.md`
- keep temporary requirement decisions in `prd.md`
- propose ADRs only for hard-to-reverse, surprising-without-context, real tradeoffs

Requirements-stage review stays in requirement discovery / Domain Grill plus human confirmation. This task must not add a `record-review requirements` target or a requirements clean-streak Gate.

### R4. Clean-Context Review Evidence

Overview and detailed design reviews must record durable review evidence in `task.json` rather than relying on chat conclusions.

Evidence must include:

- target Gate (`overview` or `detail`)
- current artifact digest
- review result (`clean` or `findings`)
- maximum finding severity
- finding class when applicable:
  - `REQ_BLOCKER`
  - `OVERVIEW_DEFECT`
  - `DETAIL_DEFECT`
  - `IMPLEMENT_DEFECT`
  - `PROCESS_DEFECT`
- reviewer/context marker proving the review was clean-context
- review run id proving that consecutive clean records came from separate clean-context runs
- short evidence summary
- timestamp

Two consecutive clean reviews for the current artifact digest are required before an automatic pass is valid. They must come from distinct clean-context review runs; two records with the same run id do not count as two reviews.

`clean` means no medium-or-higher actionable finding. A clean review may record `max_severity=low` for non-blocking nits or observations, but it must not carry a `finding_class`. Any medium/high/critical issue must be recorded as `findings` and must not count toward the clean streak.

### R5. Overview Automatic Pass

Overview must pass automatically when:

- `guru_gate.py overview <task_dir>` passes structural checks.
- There are two consecutive clean-context overview review records for the current overview digest.
- No medium-or-higher finding exists in the current clean streak.

Any overview artifact modification must invalidate the clean streak via digest mismatch.

If overview review finds `REQ_BLOCKER`, the workflow must route back to requirement clarification and downstream evidence must not be treated as current.

Before those conditions are met, overview writing/review/fix/review must run as an agent-driven planning loop. Non-requirement overview defects must not stop for user intervention; the loop stops only on `REQ_BLOCKER`, two current clean reviews, tool failure, or a hard boundary.

### R6. Detail Clean Review Plus Human Confirmation

Detailed design must stop for user confirmation only after:

- `guru_gate.py detail <task_dir>` passes structural checks.
- There are two consecutive clean-context detail review records for the current detail digest.
- No medium-or-higher finding exists in the current clean streak.

Before those conditions are met, non-requirement/detail defects must be fixed and re-reviewed automatically.

After those conditions are met, the user must confirm detailed design before `task.py start` can pass.

Detailed design writing/review/fix/review must use the same planning loop pattern as overview. Detail findings are fixed and re-reviewed automatically until two current clean reviews exist, then the workflow stops for detail confirmation.

### R7. Backward Compatibility

Existing tasks that contain old `guru_gates` entries must fail closed with actionable status output rather than being silently accepted.

The old `grill-done` / `grill-skip` commands may remain for compatibility, but they must no longer be hard prerequisites for overview/detail start checks after the new model is active.

Every Guru verification entrypoint that can block planning or start, including `guru_gate.py check`, `guru_gate.py auto`, and before-start hook messaging, must use the new review-evidence model. Old `design-grill` records may be shown as deprecated context but must not unblock or block overview/detail under the new model.

### R8. Implementation DoD

Implementation skills and review skills must require each implementation slice to include:

- code changes
- requirement/design-linked Chinese comments for newly added classes, properties, and methods by default
- necessary structured logs using the existing project logger or logging facade
- log redaction for secrets, tokens, cookies, passwords, phone numbers, emails, complete request/response bodies, and user-generated content
- local validation evidence
- trace updates

Comment exceptions are allowed only for generated code, trivial boilerplate getters/setters, and tiny private helpers whose purpose is already obvious from surrounding commented code. The default for new business-bearing code is to explain the requirement/design reason, constraint, side effect, boundary, or risk in Chinese rather than translating code line by line.

Do not add a new logging abstraction merely for this task. If no logger exists, the decision must be documented in design or Phase 0.

### R9. Final Verification

The final check path must cover:

- build / typecheck / lint / tests appropriate to the touched area
- trace completeness
- planning review-evidence completeness
- implementation review evidence from the `implement-check` loop
- log redaction and no temporary debug output
- comment/log DoD where reviewable
- Guru template sync from `guru-template/` into packaged CLI templates
- spec compliance

### R10. Planning Automation Driver

The workflow must define the planning-phase driver that advances overview/detail without hand-managed chat steps.

The minimum acceptable driver is:

- reuse existing Trellis channel/sub-agent supervision patterns rather than adding a new state machine
- run the platform writing skill for the target planning phase
- run the matching clean-context review skill
- record review evidence with `guru_gate.py record-review`
- if review returns non-requirement findings, fix the planning artifact and repeat
- if review returns `REQ_BLOCKER`, route back to requirements and invalidate downstream evidence
- after two clean reviews for the current digest, advance overview automatically or stop for detail confirmation

The driver must be implemented as the smallest `guru_supervise.py` extension that provides repeatable `overview` and `detail` planning actions. Workflow and review-skill instructions must document the loop, but documentation alone is not sufficient unless an existing single command already runs the whole loop. It must not auto-confirm requirements/detail or cross hard boundaries.

### R11. Implementation Automation Driver

After detailed design is confirmed, implementation must also run as an agent-driven loop rather than a hand-managed alternation of `implement` and `check`.

The minimum acceptable implementation driver is:

- reuse the existing `guru_supervise.py implement` and `guru_supervise.py check` action mechanics
- add the smallest loop command or supervision command that runs implement, then clean-context check, then routes by check result
- if check returns `IMPLEMENT_DEFECT` or implementation `PROCESS_DEFECT`, run implement again with the finding context and repeat check
- if check returns `DETAIL_DEFECT`, `OVERVIEW_DEFECT`, or `REQ_BLOCKER`, stop and route back to the corresponding upstream stage
- if check is clean and final verification passes, stop at the hard-boundary Gate rather than committing, archiving, publishing, or externally writing

For the first implementation, one clean implementation check is sufficient review evidence if the check output explicitly includes clean/final-verification-ready status, the reviewed diff or artifact context, and the validation evidence summary. Do not add implementation `guru_gates` or a second clean streak unless a later requirement proves the single-clean evidence is insufficient.

This driver must not add a new lifecycle status, queue, database, scheduler, or implementation review database.

## Acceptance Criteria

- [ ] `gate-confirmation-model.md` across Guru platform specs describes the new Gate model: requirements human confirmation, overview automatic double-clean, detail double-clean plus human confirmation, hard-boundary confirmation.
- [ ] Guru workflow markdown for Flutter, Go, iOS, and H5 no longer describes overview as a human confirmation Gate.
- [ ] Guru workflow markdown routes `design-grill` behavior through requirement discovery / Domain Grill rather than post-draft hard Gate completion.
- [ ] `trellis-brainstorm` templates document requirement context reconnaissance and Domain Grill Subroutine rules.
- [ ] Template tests assert the brainstorm/Domain Grill contracts for repository-answerable questions, current-code-vs-user-intent conflict lists, Domain Grill triggers, `CONTEXT.md` write protection, and ADR three-condition creation.
- [ ] `guru_gate.py` can record review evidence for `overview` and `detail`.
- [ ] `guru_gate.py check` passes overview without human confirmation only when two clean-context overview review records match the current artifact digest and have distinct review run ids.
- [ ] `guru_gate.py check` blocks detail without human confirmation even after two clean-context detail reviews from distinct review run ids.
- [ ] `guru_gate.py check` passes detail after two clean-context detail reviews from distinct review run ids and valid detail human confirmation.
- [ ] `guru_gate.py auto` uses the same new review-evidence semantics as `check`: it does not require old overview/detail `design-grill` records, reports missing review evidence, preserves progressive planning behavior before overview/detail artifacts exist, uses explicit exit-2 guidance for invalid or unconfirmed requirements and missing/stale review evidence, and still fails closed on stale or medium+ findings.
- [ ] `worktree.verify.yaml` source and packaged copies describe `guru_gate.py auto` as progressive current-artifact verification; `auto` exit 0 before overview/detail artifacts exist does not mean five-phase completion.
- [ ] `guru_gate.py status` clearly reports missing/one-clean/two-clean/finding/digest-mismatch states.
- [ ] Artifact mutation resets review clean streak through digest mismatch.
- [ ] Medium-or-higher review findings reset clean streak; low-only clean observations do not.
- [ ] `REQ_BLOCKER` findings route status guidance back to requirements.
- [ ] Old `grill` records do not replace the new review evidence.
- [ ] Overview/detail review skills output the evidence command or fields required by `guru_gate.py`.
- [ ] Planning workflow and supervision commands define the overview/detail writing-review-fix-review loop, including stop conditions for `REQ_BLOCKER`, two clean reviews, tool failure, and hard boundaries.
- [ ] `guru_supervise.py --help` exposes repeatable `overview` and `detail` planning actions, and dry-runs exit 0 while showing the expected writing skill, matching clean-context review skill, fresh run-id guidance, loop instruction, and `record-review` evidence path.
- [ ] `guru_gate.py record-review` CLI, top-level usage, parser routing, and tests enforce the clean-vs-findings argument contract.
- [ ] `record-review` requires `--run-id`; `--result clean` accepts `--max-severity none|low` and no `--finding-class`; `--result findings` requires `--finding-class` and `--max-severity medium|high|critical`.
- [ ] before-start hook messaging no longer tells users to confirm overview; it delegates next-step guidance to `guru_gate.py status`.
- [ ] Overlay install/config snippets, harness detail SSOT docs, overview/detail writing skills, review skills, and review-output references no longer preserve stale "three human Gate" or "overview user confirm" semantics except as explicit compatibility notes or legacy test fixtures.
- [ ] Current worktree skill copies for `trellis-brainstorm` are synced or verified against the updated source templates so Domain Grill is active in local dogfooding.
- [ ] Implementation writing/review skills across supported Guru platforms require design-linked Chinese comments for newly added classes/properties/methods, necessary structured logs, redaction, validation, and trace updates.
- [ ] Implementation supervision defines and tests an implement-check loop that automatically fixes `IMPLEMENT_DEFECT` / implementation `PROCESS_DEFECT`, routes upstream defects back to planning, records a single clean check as MVP implementation review evidence with clean/final-verification-ready summary, does not add implementation `guru_gates`, and stops at the hard boundary after final verification.
- [ ] `guru-template/overlay/verify/tests/run_tests.sh` covers the new happy path and failure paths.
- [ ] The shell fixture is run with `bash guru-template/overlay/verify/tests/run_tests.sh` or direct shell execution, not `python3`.
- [ ] Packaged Guru templates are synced with `pnpm -C packages/cli sync:guru`.
- [ ] Focused Guru packaging tests pass.
- [ ] No unrelated dirty files are reverted or absorbed.

## Out of Scope

- Do not implement a concrete business feature.
- Do not replace Trellis core task statuses with a new multi-stage status machine.
- Do not automatically run commit, archive, finish-work, publish, or external writes.
- Do not force every project to use a common logger abstraction.
- Do not build a semantic comment-quality parser.
- Do not write one-off product facts into long-term specs.
- Do not direct-merge or push changes as part of this task.
- Do not build a separate planning database, scheduler, or lifecycle state machine for the overview/detail loop.

## Open Questions

No product questions are currently blocking planning. The implementation should use the conservative model above.

If implementation discovers a compatibility edge case where existing active Guru tasks cannot be safely migrated or failed closed, return to planning before changing behavior.
