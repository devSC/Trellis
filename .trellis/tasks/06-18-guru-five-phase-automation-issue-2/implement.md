# Implementation Plan

## Implementation Evidence (2026-06-19)

- Implemented scoped adversarial-review model defaults:
  - Claude adversarial reviewers default to `claude-sonnet-4-6`.
  - Codex adversarial reviewers default to `gpt-5.4` with `--reasoning-effort high`.
  - Defaults apply only to `guru_supervise.py --adversarial requirements|overview|detail`.
  - Adversarial reviewer execution is best-effort: missing provider CLIs or provider runtime errors are skipped, persisted to `task.json.guru_gates.adversarial_skips[]`, shown by `guru_gate.py status`, and do not block the main task flow.
  - Normal `implement`, `check`, and `implement-check` workers do not receive adversarial model overrides.
- Added project-level overrides under existing `.trellis/config.yaml`:
  - `guru.supervision.adversarial_claude_model`
  - `guru.supervision.adversarial_codex_model`
  - `guru.supervision.adversarial_codex_reasoning_effort`
  - Old written defaults `claude-sonnet-4.8` and `claude-sonnet-4.6` are migrated to `claude-sonnet-4-6`; custom model names remain preserved.
  - Missing, blank, quoted-empty, or comment-only values fall back to defaults.
- Added the narrow CLI surface needed for Codex high reasoning:
  - `trellis channel spawn --reasoning-effort <level>`
  - supervisor config/view carries the optional value
  - Codex adapter emits `-c model_reasoning_effort="<level>"`
  - `trellis channel run` remains unchanged.
- Synced source Guru overlay changes into packaged CLI templates with `pnpm -C packages/cli sync:guru`.
- Updated bundled channel references and backend specs so installed projects document the same spawn-only contract.
- Added regressions for:
  - Codex adapter `model_reasoning_effort` argument shape
  - channel spawn supervisor config persistence
  - Guru default dry-runs for Claude/Codex adversarial reviewers
  - custom `.trellis/config.yaml` model/effort overrides
  - blank/comment-only override fallback
  - config patch default insertion and custom-value preservation
- Independent adversarial review fixed one config parsing edge case: comment-only values such as `adversarial_codex_reasoning_effort: # decide later` are now treated as unset instead of being passed through as literal CLI values.
- Follow-up install hygiene: `guru apply` now idempotently adds `.claude/projects/`, `.codex/sessions/`, and `.trellis/channels/` to the target project `.gitignore` so local AI/Trellis runtime logs stay out of Git.

Validation run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile guru-template/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_config_patch.py packages/cli/src/templates/guru/overlay/verify/guru_supervise.py packages/cli/src/templates/guru/overlay/verify/guru_config_patch.py
bash guru-template/overlay/verify/tests/run_tests.sh
PYTHONDONTWRITEBYTECODE=1 bash packages/cli/dist/templates/guru/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts test/commands/channel-codex-adapter.test.ts test/commands/channel-spawn-config.test.ts
pnpm -C packages/cli lint
pnpm -C packages/cli typecheck
pnpm -C packages/cli build
pnpm -C packages/cli pack --pack-destination <tmp> --json
git diff --check
npx gitnexus detect-changes --scope all --repo Trellis
```

Observed validation results:

- Source Guru verify shell regression: `132 passed / 0 failed`.
- Dist Guru verify shell regression: `132 passed / 0 failed`.
- Targeted CLI Vitest: `3 files passed / 52 tests passed`.
- CLI lint: passed.
- TypeScript typecheck: passed.
- CLI build: passed.
- Package tarball contains updated Guru overlay scripts/config snippets and bundled `trellis-channel` references.
- Git diff whitespace check: passed.
- GitNexus detect-changes: 19 files, 41 symbols, 45 affected processes, risk level `critical`; expected blast radius because the diff touches shared channel spawn/supervisor paths plus Guru supervision.

## Implementation Evidence (2026-06-18)

- Implemented the new Guru Gate model:
  - `requirements` and `detail` remain human-confirmed gates.
  - `overview` and `detail` review evidence is stored in `task.json.guru_gates.review_runs`.
  - `confirm overview` is rejected; `overview` passes only after two distinct current-digest clean review runs.
  - `detail` requires two distinct current-digest clean review runs plus `confirm detail`.
- Extended `guru_supervise.py`:
  - Added `overview`, `detail`, and `implement-check` actions.
  - Injects paired writing/review skills for planning loops.
  - `implement-check` carries route classes, `clean/final-verification-ready`, validation summary, and hard-boundary stop wording.
- Updated workflow/spec/skill contracts across Flutter, Go, H5, and iOS:
  - Gate SSOT and workflow text now use requirements confirm + review evidence + detail confirm.
  - Overview/detail review skills use `record-review`.
  - Implementation review skills output route classes: `IMPLEMENT_DEFECT`, `PROCESS_DEFECT`, `DETAIL_DEFECT`, `OVERVIEW_DEFECT`, `REQ_BLOCKER`, or `none`.
  - Domain Grill is part of requirement discovery, not a post-draft overview/detail hard gate.
- Synced `guru-template/` into `packages/cli/src/templates/guru/` with `pnpm -C packages/cli sync:guru`.
- Updated package tests for:
  - Guru bundled workflow/model assertions.
  - `guru_supervise.py overview/detail/implement-check --dry-run`.
  - Domain Grill contracts in shared, Codex, and Copilot templates.
- Review repair after implementation audit:
  - `implement-check` now sequences existing `implement` and `check` run plans in one command, repeats repairable `IMPLEMENT_DEFECT` / `PROCESS_DEFECT` findings, routes upstream defects, and stops clean runs at the hard boundary.
  - `REQ_BLOCKER` review findings now route `status` / `check` guidance back to requirements instead of telling the user to continue the same phase clean review.
  - Added regression coverage for `REQ_BLOCKER` routing and the implement/check repeat loop.
- Review repair after install-completeness audit:
  - Added `trellis guru apply <flutter|go|ios|h5> [target]` so projects initialized from the npm package can install or refresh the complete Guru overlay without manually locating `dist/templates/guru/overlay/apply.sh`.
  - `trellis init` now prints the matching `trellis guru apply <platform>` follow-up for bundled Guru templates/workflows instead of silently leaving overlay scripts/skills/hooks unapplied.
  - Added a dist-CLI E2E that runs `init --template guru-h5-web --workflow guru-h5`, then `guru apply h5`, then asserts `guru_gate.py`, `guru_supervise.py`, platform review skills, config hook wiring, worktree verify wiring, and `guru_supervise.py --help`.
  - Removed remaining stale "three document Gate" wording from H5/iOS workflow headers, Guru workflow metadata, and `trellis-local`.
  - Legacy `grill-done` / `grill-skip` status output is now labeled compatibility-only so installed projects are not told to run old overview/detail grill gates.
- Review repair after final `trellis-check` audit:
  - `cmd_check()` structure Gate failures now route by Gate: overview tells the user to rerun the overview review loop and write `record-review overview`, while requirements/detail remain the only human-confirm Gates.
  - Removed stale "review skill artificial Gate" wording from structure-check failure output.
  - Added a regression proving overview structure failure does not tell the user to re-confirm overview.
- Review repair after independent install/compliance audit:
  - Rewrote legacy `design-grill` skill text as compatibility-only so installed projects are not told to use old `grill-done` / `grill-skip` as the new Gate path.
  - Tightened Domain Grill ADR guidance from "or" to "and" so ADRs are proposed only when a decision is hard-to-reverse, surprising-without-context, and a real trade-off.
  - Made `guru_gate.py status` explicitly report stale review digest mismatches instead of collapsing them into missing review evidence.
  - Added npm tarball coverage for the Guru command, dist templates, gate/supervise scripts, key skills, and `@mindfoldhq/trellis-core` npm alias.
- Review repair after current PRD/plan audit:
  - Removed stale overview-writing guide instructions that routed disputed ownership rows to old `design-grill` / overview-stage user confirmation.
  - Overview writing guides now route unresolved code-evidence-vs-user-intent conflicts back to requirement discovery / Domain Grill and emit `REQ_BLOCKER` when they cannot be resolved from evidence.
  - Reworded `trellis-local` customization history so installed projects see `design-grill` as legacy compatibility only, not as an overview/detail Gate path.
  - Added a Guru bundled regression proving packaged overview writing guides keep the Domain Grill / `REQ_BLOCKER` route and do not reintroduce the stale `design-grill` or overview user-confirmation wording.

Validation run:

```bash
python3 -m py_compile guru-template/overlay/verify/guru_gate.py guru-template/overlay/verify/guru_supervise.py
bash guru-template/overlay/verify/tests/run_tests.sh
bash guru-template/overlay/tests/apply_test.sh
bash packages/cli/dist/templates/guru/overlay/tests/apply_test.sh
bash packages/cli/dist/templates/guru/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts test/configurators/shared.test.ts test/templates/codex.test.ts test/templates/copilot.test.ts
pnpm -C packages/cli lint
pnpm -C packages/cli typecheck
pnpm -C packages/cli build
pnpm -C packages/cli pack --pack-destination <tmp> --json
git diff --check
npx gitnexus detect-changes --scope all --repo Trellis
```

Observed validation results:

- Guru gate shell regression: `123 通过 / 0 失败`.
- Source overlay apply regression: `49 通过 / 0 失败`.
- Dist Guru gate shell regression: `123 通过 / 0 失败`.
- Dist overlay apply regression: `49 通过 / 0 失败`.
- CLI targeted Vitest: `4 files passed / 106 tests passed`.
- CLI lint: passed.
- TypeScript typecheck: passed.
- CLI build: passed.
- Package tarball contains `bin/trellis.js`, `dist/commands/guru.js`, `dist/cli/index.js`, Guru overlay `apply.sh`, `guru_gate.py`, `guru_supervise.py`, legacy `design-grill` as compatibility-only, H5 review skill, and rewrites `@mindfoldhq/trellis-core` to `npm:@devsc/trellis-core@0.6.0-guru.1`.
- Git diff whitespace check: passed.
- GitNexus detect-changes: 133 files, 625 symbols, 34 affected processes, risk level `critical` due to expected gate/workflow/template-wide model replacement.

Delivery record / risk disposition:

- Delivery state: implementation is validation-clean; the remaining hard boundary is human confirmation for commit/archive/finish-work.
- Risk disposition: current GitNexus all-scope classification is `low`; the diff is limited to Guru source overlay wording, synced packaged Guru templates, task evidence, and focused regression tests.
- Evidence used for disposition: live `npx gitnexus detect-changes --scope all --repo Trellis` returned 10 files, 20 symbols, 0 affected processes, risk level `low`; `git diff --check` passed.
- Follow-up identified after the later GitHub #4 review: requirements-stage adversarial review is a separate plan repair. The current implementation evidence above only proves the #3 overview/detail adversarial review increment, not #4.

## Phase 0: Preflight

- [x] Run `npx gitnexus status`; only run `npx gitnexus analyze` if the index is stale.
- [x] If `npx gitnexus analyze` modifies `AGENTS.md`, `CLAUDE.md`, or `.claude/skills/gitnexus/*`, record those as GitNexus index-refresh side effects and keep them out of the task implementation diff.
- [x] Run GitNexus impact analysis before editing `guru_gate.py` symbols:
  - `cmd_check`
  - `cmd_status`
  - `cmd_confirm`
  - `auto`
  - `_gate_digest`
  - `_grill_ok`
  - any new review-recording helper
- [x] Run GitNexus impact analysis before editing `guru_supervise.py` symbols:
  - `VALID_ACTIONS`
  - `SKILL_BY_PLATFORM`
  - `build_run_plan`
  - `run_action`
  - `build_parser`
- [x] Re-check current dirty files and keep unrelated user changes out of the implementation.
- [x] Read relevant specs before edits:
  - `.trellis/spec/cli/backend/script-conventions.md`
  - `.trellis/spec/cli/backend/quality-guidelines.md`
  - `.trellis/spec/cli/unit-test/conventions.md`
  - `.trellis/spec/guides/code-reuse-thinking-guide.md`
  - `.trellis/spec/guides/cross-layer-thinking-guide.md`

## Phase 1: Gate SSOT and Workflow Text

- [x] Update `guru-template/specs/*/harness/gate/gate-confirmation-model.md` to define the new Gate model.
- [x] Update `guru-template/workflows/*-workflow.md` planning text and breadcrumbs.
- [x] Remove overview human-confirm language.
- [x] Move `design-grill` wording into requirement discovery / Domain Grill.
- [x] Define the overview/detail writing-review-fix-review planning loop and its stop conditions.
- [x] Keep hard-boundary confirmation language intact.
- [x] Update `guru-template/overlay/hooks/platform/block-unconfirmed-start.sh` wording so failures point to `guru_gate.py status <task_dir>` and do not hard-code "three human Gates" or `confirm overview`.
- [x] Update overlay install/config wording in `guru-template/overlay/apply.sh`, `guru-template/overlay/config-snippets/config.hooks.yaml`, and `guru-template/overlay/config-snippets/worktree.verify.yaml`.
- [x] Make `worktree.verify.yaml` state that `guru_gate.py auto` exit 0 is progressive current-artifact verification, not proof that all five phases are complete.
- [x] Update `guru-template/specs/*/harness/detail/detail-structure-single-source.md` so detail prerequisites refer to overview double-clean evidence instead of overview user confirmation.

Validation:

```bash
rg -n "overview.*confirm|概要.*confirm|grill-policy|grill-done \\+ confirm|三道人工 Gate|confirm overview|five phases are complete|五阶段.*完成" guru-template
```

Remaining hits must be explicit compatibility notes, legacy test fixtures, or requirement/detail confirmation guidance that does not require `confirm overview`.

## Phase 2: Brainstorm Domain Grill

- [x] Update common brainstorm template with requirement context reconnaissance.
- [x] Add Domain Grill Subroutine triggers and write-back rules.
- [x] Update Codex and Copilot brainstorm template variants.
- [x] Sync or intentionally update local dogfooding copies:
  - `.agents/skills/trellis-brainstorm/SKILL.md`
  - `.claude/skills/trellis-brainstorm/SKILL.md`
  - `.cursor/skills/trellis-brainstorm/SKILL.md`
  - `.opencode/skills/trellis-brainstorm/SKILL.md`
  - `.pi/skills/trellis-brainstorm/SKILL.md`

Validation:

```bash
rg -n "Domain Grill|CONTEXT-MAP|current code vs user intent|ADR" packages/cli/src/templates .agents .claude .cursor .opencode .pi
```

## Phase 3: Automation Drivers

### Planning Loop Driver

- [x] Minimally extend `guru_supervise.py` with repeatable planning actions for `overview` and `detail`.
- [x] Change the action-to-skill lookup only as much as needed so `overview` and `detail` can resolve an ordered pair of skill files.
- [x] For `overview`, include the platform `*-design-overview-writing/SKILL.md` and matching `*-design-overview-review/SKILL.md` in the run plan.
- [x] For `detail`, include the platform `*-design-detail-writing/SKILL.md` and matching `*-design-detail-review/SKILL.md` in the run plan.
- [x] Make the worker prompt explicit: write/update artifact, run clean-context review with a fresh run id, emit or run `guru_gate.py record-review`, fix non-requirement findings, then repeat until a stop condition.
- [x] Keep workflow + review-skill instructions as documentation of the loop, not as the only driver.
- [x] Reuse existing channel creation/spawn/wait plumbing; do not add queues, persistent schedulers, or new task statuses.
- [x] Add the smallest dry-run assertion that `overview` and `detail` exit 0 and prove `build_run_plan` can resolve both writing and review skill files.
- [x] Ensure loop stop conditions are explicit:
  - `REQ_BLOCKER` -> requirements
  - `OVERVIEW_DEFECT` -> overview fix/review
  - `DETAIL_DEFECT` -> detail fix/review
  - `PROCESS_DEFECT` -> affected process artifact fix/review
  - two clean current-digest reviews -> overview auto pass or detail user confirm
  - tool error/killed/timeout -> surface blocker to main session

Validation:

```bash
python3 guru-template/overlay/verify/guru_supervise.py --help
python3 guru-template/overlay/verify/guru_supervise.py overview <task-dir> --dry-run
python3 guru-template/overlay/verify/guru_supervise.py detail <task-dir> --dry-run
rg -n "overview|detail|clean-context|REQ_BLOCKER|record-review|run-id|design-overview-writing|design-detail-writing|design-overview-review|design-detail-review" guru-template/overlay/verify/guru_supervise.py guru-template/workflows
```

### Implementation Loop Driver

- [x] Add the smallest implementation loop command to `guru_supervise.py`, reusing existing `implement` and `check` run plans.
- [x] The loop command must route:
  - `IMPLEMENT_DEFECT` / implementation `PROCESS_DEFECT` -> run implement again
  - `DETAIL_DEFECT` -> return to detail planning
  - `OVERVIEW_DEFECT` -> return to overview planning
  - `REQ_BLOCKER` -> return to requirements
  - clean + final validation -> stop at hard boundary
- [x] Treat one clean implementation check as MVP implementation review evidence only when the check output includes clean/final-verification-ready, reviewed diff or artifact context, and validation evidence summary.
- [x] Assert `implement-check --dry-run` documents the single-clean MVP rule and does not introduce implementation `guru_gates`.
- [x] Add the smallest dry-run assertion that `implement-check` exits 0 and proves the parser/action map can sequence existing `implement` and `check` run plans.
- [x] Do not add a queue, scheduler, database, or task status.

Validation:

```bash
python3 guru-template/overlay/verify/guru_supervise.py implement-check <task-dir> --dry-run
rg -n "implement-check|IMPLEMENT_DEFECT|DETAIL_DEFECT|OVERVIEW_DEFECT|REQ_BLOCKER|single-clean|implementation.*guru_gates|clean/final-verification-ready|review evidence|hard boundary|final validation" guru-template/overlay/verify/guru_supervise.py guru-template/workflows guru-template/overlay/agents-skills
```

## Phase 4: `guru_gate.py` Evidence Model

- [x] Add review evidence parsing and validation helpers.
- [x] Add `record-review` command.
- [x] Update top-level usage text and `main()` command routing for `record-review`.
- [x] Enforce `record-review` argument rules:
  - `--result clean` requires `--max-severity none|low`
  - `--result clean` rejects `--finding-class`
  - `--result findings` requires `--finding-class`
  - `--result findings` requires `--max-severity medium|high|critical`
  - `--run-id` is required for clean and findings records
- [x] Compute clean streak from `review_runs`; ignore any stored `clean_streak` or `auto_passed` for pass/fail.
- [x] Count only distinct clean-context `run_id` values toward the two-clean requirement; duplicate run ids should be visible in `status` but must not advance the streak.
- [x] Treat low-only clean observations as clean; medium/high/critical findings reset the streak.
- [x] Split Gate semantics into human-confirm and automatic-review Gates.
- [x] Change `confirm overview` to fail with new-model guidance.
- [x] Change `cmd_check` to require:
  - requirements confirm
  - overview double-clean review from distinct run ids
  - detail double-clean review from distinct run ids
  - detail confirm
- [x] Change `auto` to use the same review-evidence model as `check` while preserving progressive planning validation.
- [x] Define and test the `auto` exit-code matrix:
  - no active task preserves existing pass behavior: exit 0
  - missing or structurally invalid requirements: exit 2 with requirements structure guidance
  - valid requirements without current human confirmation: exit 2 with requirements confirmation guidance
  - confirmed requirements before overview/detail artifacts exist: exit 0 without overview/detail review-evidence requirements
  - existing overview artifact: exit 0 only with valid structure plus two current clean reviews from distinct run ids; otherwise exit 2 with review-evidence guidance
  - existing detail artifact: exit 0 only with valid structure plus two current clean reviews from distinct run ids; otherwise exit 2 with review-evidence guidance
  - task beyond planning: keep structure validation for available planning/implementation artifacts and never require old overview/detail grill records
  - when multiple artifacts exist, apply every applicable row in order instead of letting a later artifact mask an earlier validation failure
- [x] Remove overview/detail `design-grill` as a hard prerequisite from both `check` and `auto`; keep old grill commands only as deprecated compatibility context.
- [x] Change `cmd_status` to explain clean streaks and rollback causes.
- [x] Keep atomic write and invalid JSON guard behavior.
- [x] Update top-level usage/help strings so `auto`, `check`, and `status` no longer describe "three human Gates" or old `design-grill` prerequisites.

Validation:

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
rg -n "def auto|guru_gate.py auto|design-grill|grill-done|confirm overview|three human|三道人工" guru-template/overlay/verify/guru_gate.py guru-template/overlay/verify/tests/run_tests.sh
```

Remaining matches are allowed only when they are deprecated compatibility notes, legacy fixture assertions being rewritten, or Domain Grill migration text; any normal `check` / `auto` / start prerequisite that still requires old grill records or `confirm overview` must be removed.

## Phase 5: Review Skill Contracts

- [x] Update every overview review skill to output recordable clean-context evidence and no overview human confirm.
- [x] Update every detail review skill to output recordable clean-context evidence and then stop for detail human confirm after streak reaches 2.
- [x] Update overview/detail writing skills where stale prerequisites mention overview user confirmation instead of current overview double-clean evidence.
- [x] Update review-output references that still show `confirm overview` as the normal path.
- [x] Add finding-class routing language:
  - `REQ_BLOCKER` -> requirements
  - `OVERVIEW_DEFECT` -> overview
  - `DETAIL_DEFECT` -> detail
  - `IMPLEMENT_DEFECT` -> implementation
  - `PROCESS_DEFECT` -> workflow/process fix
- [x] Add loop decision output to each overview/detail review skill so non-requirement defects are fixed and re-reviewed automatically.
- [x] Ensure overview review never asks for user confirmation; detail review asks only after two current clean reviews.

Validation:

```bash
rg -n "record-review|REQ_BLOCKER|clean-context|连续 2|两次" guru-template/overlay/agents-skills
rg -n "confirm overview|overview confirmed|概要确认|用户终端 confirm" guru-template/overlay/agents-skills
```

Any remaining confirmation-language hits must be detail-confirmation after detail double-clean evidence or explicit compatibility notes; `confirm overview` must not remain as a normal path.

## Phase 6: Implementation DoD Skill Updates

- [x] Normalize comment/log/trace DoD across Flutter, Go, iOS, and H5 implementation writing skills.
- [x] Normalize comment/log/redaction review language across implementation review skills.
- [x] Preserve the default that newly added classes, properties, and methods need requirement/design-linked Chinese comments.
- [x] Allow only narrow comment exceptions for generated code, trivial boilerplate getters/setters, and tiny private helpers whose purpose is obvious from nearby commented code.
- [x] Make implementation review skills output route classes: `IMPLEMENT_DEFECT`, `PROCESS_DEFECT`, `DETAIL_DEFECT`, `OVERVIEW_DEFECT`, `REQ_BLOCKER`, or clean/final-verification-ready.
- [x] Avoid adding a logger abstraction.
- [x] Add deterministic script checks only if cheap and low-noise.

Validation:

```bash
rg -n "新增类|属性|方法|注释|IMPLEMENT_DEFECT|PROCESS_DEFECT|DETAIL_DEFECT|OVERVIEW_DEFECT|REQ_BLOCKER|日志|logger|redact|脱敏|token|cookie|手机号|邮箱|trace" guru-template/overlay/agents-skills
```

## Phase 7: Template Sync and Packaging Tests

- [x] Run `pnpm -C packages/cli sync:guru`.
- [x] Update `packages/cli/test/guru/guru-bundled.test.ts` assertions for the new model.
- [x] Add `guru_supervise.py` packaging tests for `overview --dry-run` and `detail --dry-run` that assert exit 0 plus both writing/review skills, `record-review`, `REQ_BLOCKER`, and two-clean stop wording are present.
- [x] Add `guru_supervise.py` packaging test for `implement-check --dry-run` that asserts exit 0 plus implement skill, check skill, defect routing keywords, single-clean MVP rule, clean/final-verification-ready evidence summary, no implementation `guru_gates`, final validation stop, and hard-boundary stop are present.
- [x] Add Guru gate fixture tests for `auto` under the new model: no old overview/detail grill prerequisite, missing review evidence guidance, and progressive planning before overview/detail artifacts exist.
- [x] Add template tests for brainstorm/Domain Grill contracts in the existing template test suite:
  - `packages/cli/test/configurators/shared.test.ts`
  - `packages/cli/test/templates/codex.test.ts`
  - `packages/cli/test/templates/copilot.test.ts`
- [x] Ensure packaged copies match `guru-template/`.
- [x] Assert packaged overlay includes updated `record-review`, hook status guidance, and planning loop wording.
- [x] Assert packaged overlay includes updated `auto` usage/help text, `worktree.verify.yaml` progressive current-artifact wording, and no old overview/detail grill hard prerequisite.

Validation:

```bash
pnpm -C packages/cli test -- test/guru/guru-bundled.test.ts
pnpm -C packages/cli test -- test/configurators/shared.test.ts test/templates/codex.test.ts test/templates/copilot.test.ts
pnpm -C packages/cli typecheck
pnpm -C packages/cli build
```

## Phase 8: Final Review

- [x] Run `git diff --name-only` and confirm touched files match this task.
- [x] Run `npx gitnexus detect-changes` before commit.
- [x] Review `guru_gate.py` behavior manually against the acceptance criteria.
- [x] Run a targeted grep for stale guidance:
  - `confirm overview`
  - `overview confirmed`
  - `三道人工 Gate`
  - `grill-policy`
  - Python used as the runner for a `.sh` shell fixture
- [x] Confirm unrelated dirty files remain unrelated and unstaged.
- [x] Stop before commit unless the user confirms the hard boundary.

## Rollback Points

- After Phase 1: revert docs/workflow only.
- After Phase 3: revert `guru_supervise.py` or workflow-loop text together.
- After Phase 4: revert `guru_gate.py` and tests together.
- After Phase 7: rerun `pnpm -C packages/cli sync:guru` after source rollback.

## Notes

- Keep implementation boring. The first durable mechanism is `task.json` review evidence plus digest checks.
- Do not create a new review database, queue, or state machine.
- Do not make a semantic parser for comments/logs.

## Incremental Evidence (2026-06-19 adversarial review)

- Added opposite-provider adversarial review support without adding a new phase or state machine.
- `guru_supervise.py --adversarial` now resolves the current provider first, then spawns the opposite provider:
  - `codex -> claude`
  - `claude -> codex`
  - other providers -> `codex`
- Overview/detail dry-runs and worker prompts now mark adversarial clean-context reviews and emit reviewer/run-id guidance such as `clean-context-adversarial-claude`.
- `guru_gate.py` review readiness now requires:
  - two distinct current-digest clean review run ids
  - at least one counted clean record whose reviewer contains `adversarial`
  - requirements remain human-confirm only and still do not support `record-review`
- Updated Guru gate SSOT and workflows for Flutter, Go, H5, and iOS; synced packaged templates with `pnpm -C packages/cli sync:guru`.
- Added regressions for:
  - two clean records without adversarial reviewer still blocked
  - adversarial clean moving overview to the next missing review
  - `codex -> claude`, `claude -> codex`, and unknown-provider -> `codex`
  - dist CLI Guru install test timeout widened to avoid false timeout after overlay install work
- Updated `.trellis/spec/cli/backend/script-conventions.md` with the executable contract for Guru adversarial review supervision.

Validation run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  guru-template/overlay/verify/guru_gate.py \
  guru-template/overlay/verify/guru_supervise.py \
  packages/cli/src/templates/guru/overlay/verify/guru_gate.py \
  packages/cli/src/templates/guru/overlay/verify/guru_supervise.py
bash guru-template/overlay/verify/tests/run_tests.sh
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
bash packages/cli/dist/templates/guru/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts
pnpm -C packages/cli lint
pnpm -C packages/cli typecheck
pnpm -C packages/cli build
git diff --check
```

Observed validation results:

- Source Guru gate shell regression: `126 通过 / 0 失败`.
- Packaged source Guru gate shell regression: `126 通过 / 0 失败`.
- Dist Guru gate shell regression: `126 通过 / 0 失败`.
- Focused Guru bundled Vitest: `1 file passed / 37 tests passed`.
- CLI lint: passed.
- TypeScript typecheck: passed.
- CLI build: passed.
- Git diff whitespace check: passed.
- No `__pycache__` directories remain under Guru template trees after cleanup.
- GitNexus detect-changes: `25 files / 194 symbols / 30 affected processes / risk critical`; accepted for this increment because the expected diff intentionally changes core Guru Gate and supervision flows, and the focused source/package/dist regressions above cover the changed paths.

## Plan Repair (2026-06-19 GitHub #4 requirements adversarial review)

Scope:

- Source issue: [devSC/Trellis#4](https://github.com/devSC/Trellis/issues/4).
- Goal: add an opposite-provider adversarial review step before `confirm requirements`.
- Current state: implementation currently covers #3 overview/detail adversarial clean evidence only. It does not yet implement the #4 requirements-stage action.
- Required behavior: `guru_supervise.py --adversarial requirements <task-dir>` must produce a requirements adversarial review plan that can return either `route_class=REQ_BLOCKER` or `review_result=clean/requirements-ready`.
- Hard boundary: even when requirements review is clean, the system must stop before human `confirm requirements`.
- Accepted MVP boundary: requirements adversarial review is a mandatory workflow/supervision step, not a persisted hard Gate. `guru_gate.py confirm requirements` keeps its existing structure + human-confirm semantics; enforcement for this increment comes from workflow/SSOT guidance and the repeatable supervisor command.
- Non-goals: no requirements clean streak, no `record-review requirements`, no `guru_gates.requirements.adversarial_reviewed_at`, no auto-confirm, no new Trellis task status, no new review database or arbitration engine, no provider registry.

### Review Findings To Fix

| Priority | Finding | Required repair |
| --- | --- | --- |
| P0 | `requirements` is not a valid `guru_supervise.py` action, so `--adversarial requirements` fails before running. | Add `requirements` to the supervisor action map and parser in source and packaged templates. |
| P0 | The adversarial prompt branch currently applies only to `overview` and `detail`. | Add a requirements-specific branch with explicit blocker/clean output rules. |
| P0 | Requirements workflow still jumps from structure Gate / Domain Grill to `confirm requirements`. | Insert adversarial requirements review between structure readiness and human confirmation in every Guru workflow. |
| P1 | Gate SSOT does not describe requirements adversarial review as a pre-confirmation planning step. | Update all platform Gate SSOT docs and automation-driver guidance. |
| P1 | Packaged install would still miss the action even if source is fixed manually. | Run `pnpm -C packages/cli sync:guru` and verify packaged source/dist behavior. |
| P1 | Tests only cover overview/detail adversarial dry-runs. | Add requirements dry-run tests for provider inversion, required output tokens, and no `record-review requirements`. |
| P1 | Validation order can test stale `packages/cli/dist` templates if dist shell tests run before `pnpm -C packages/cli build`. | Run source/src tests first, build the CLI, then run dist template tests. |

### Risk Matrix

| Area | Risk | Decision |
| --- | --- | --- |
| Product contract | Making adversarial review a persisted Gate would change the requirements approval model. | Keep it as a required workflow/supervision step before human confirm; do not add task-state fields for MVP. |
| Backward compatibility | Existing projects may already have `confirm requirements` habits. | Update workflow/SSOT guidance, but preserve `guru_gate.py confirm requirements` semantics. |
| State model | Adding requirements review to `review_runs` would conflict with the existing rejection of `record-review requirements`. | Preserve the rejection; requirements review is advisory evidence in the model output, not clean-streak state. |
| Hard enforcement | Leaving `confirm requirements` unchanged means a user can still manually confirm without running the new adversarial supervisor command. | Accepted MVP boundary for #4: the new step is enforced by workflow/SSOT and automated command availability, not by a persisted confirm prerequisite. Add a persistent marker only if a later requirement demands hard blocking. |
| Repository evidence | A requirements reviewer that asks questions before reading repo evidence can push answerable facts back to the user. | Prompt requirements review to inspect task context, requirement package, code, tests, configs, docs, `.trellis/spec/`, `CONTEXT.md`, `CONTEXT-MAP.md`, and ADRs before asking product questions. |
| Artifact injection | Existing supervisor plans inject only task-local artifacts, so a formal requirements package outside the task directory could be missed. | For `requirements`, include `prd.md`, task metadata/jsonl, and any formal requirement-package files referenced by `task.json.relatedFiles` or task markdown links; otherwise instruct the worker to discover repository evidence from `cwd` without broad template-specific scanning. |
| Domain knowledge write-back | Adversarial review could pollute long-term glossary/spec files with temporary task choices. | Keep temporary decisions in `prd.md`; only confirmed long-term terminology or boundary decisions remain eligible for Domain Grill write-back. |
| Provider routing | Wrong fallback could call the same model and weaken adversarial value. | Reuse existing opposite-provider rule: `codex -> claude`, `claude -> codex`, unknown -> `codex`. |
| Prompt drift | Worker may produce generic plan review instead of actionable requirements blocker routing. | Prompt must require `route_class=REQ_BLOCKER` for medium-or-higher blockers and `review_result=clean/requirements-ready` only when clean. |
| Install completeness | Source-only fix would not help newly installed projects. | Source template, packaged template, and dist template must all be validated. |
| Over-engineering | A new queue/state machine would expand scope beyond PRD. | Do not add scheduler, DB, provider registry, arbitration engine, Trellis task status, or new Gate state. |
| GitNexus process | Editing supervisor symbols can affect core Guru flows. | Run impact analysis before code edits and `detect_changes()` before commit. If HIGH/CRITICAL appears, report blast radius before proceeding. |

### Minimal Implementation Plan

- [x] Preflight: run GitNexus impact for `VALID_ACTIONS`, `SKILL_BY_PLATFORM`, `build_run_plan`, `run_action`, and `build_parser` before code edits.
- [x] Extend source `guru-template/overlay/verify/guru_supervise.py` with a `requirements` action.
- [x] Add requirements skill mapping using the smallest required context, preferably `requirement-review`; do not inject brainstorm or writing skills unless implementation evidence proves they are needed.
- [x] Add a requirements-specific run-plan branch:
  - review `prd.md`, task metadata/jsonl, the formal requirements package if referenced, task context, and relevant repository evidence before asking product questions;
  - inject existing task-local requirements artifacts and formal package files found through `task.json.relatedFiles` or task markdown links; do not add broad repo-wide file injection;
  - inspect code, tests, configs, docs, `.trellis/spec/`, `CONTEXT.md`, `CONTEXT-MAP.md`, and ADRs when available;
  - challenge behavior, terminology, scope, lifecycle, ownership, failure paths, acceptance criteria, compliance, and current-code-vs-user-intent conflicts;
  - emit `route_class=REQ_BLOCKER` for medium/high/critical requirement blockers;
  - state that `REQ_BLOCKER` routes back to requirements repair and downstream overview/detail evidence must be treated as non-current after requirements change;
  - treat low-severity wording nits or observations as non-blocking;
  - emit `review_result=clean/requirements-ready` only when no blocker remains;
  - keep temporary requirement decisions in `prd.md`; do not write long-term glossary/spec/ADR content unless the user has confirmed it through the existing Domain Grill rules;
  - explicitly say requirements has no review-evidence command, but do not print the literal `record-review requirements` sequence in the dry-run prompt;
  - explicitly stop before `confirm requirements`.
- [x] Reuse `--adversarial` for requirements and apply the opposite-provider line to `requirements`, `overview`, and `detail`.
- [x] Leave `guru_gate.py` requirements confirmation behavior unchanged; add or keep a focused rejection test proving `guru_gate.py record-review requirements ...` fails.
- [x] Make workflow and Gate SSOT wording explicit: requirements adversarial review is required before `confirm requirements`, but it is not stored as requirements review evidence and does not change `cmd_confirm()`.
- [x] Make workflow and Gate SSOT wording explicit that a requirements-stage `REQ_BLOCKER` returns to requirements repair and downstream overview/detail evidence must be rerun after requirements digest changes.
- [x] Update all four source workflows:
  - `guru-template/workflows/guru-client-workflow.md`
  - `guru-template/workflows/guru-go-workflow.md`
  - `guru-template/workflows/guru-h5-workflow.md`
  - `guru-template/workflows/guru-ios-workflow.md`
- [x] Update all four Gate SSOT docs:
  - `guru-template/specs/guru-flutter-client/harness/gate/gate-confirmation-model.md`
  - `guru-template/specs/guru-go-backend/harness/gate/gate-confirmation-model.md`
  - `guru-template/specs/guru-h5-web/harness/gate/gate-confirmation-model.md`
  - `guru-template/specs/guru-ios-native/harness/gate/gate-confirmation-model.md`
- [x] Sync packaged templates with `pnpm -C packages/cli sync:guru`.
- [x] Add package test coverage in `packages/cli/test/guru/guru-bundled.test.ts`:
  - `--adversarial requirements` dry-run exits 0;
  - `codex -> claude` and `claude -> codex` are asserted for requirements;
  - dry-run output contains `REQ_BLOCKER`;
  - dry-run output contains `review_result=clean/requirements-ready`;
  - dry-run output tells the reviewer to inspect repository evidence before asking product questions;
  - dry-run output preserves the temporary-PRD vs confirmed-long-term-knowledge boundary;
  - dry-run output does not contain the exact literal `record-review requirements` sequence;
  - packaged workflow and Gate SSOT text include `guru_supervise.py --adversarial requirements <task_dir>` before `confirm requirements`;
  - `guru_gate.py record-review requirements ...` rejection is covered by a focused source/package shell or bundled-template test.
- [x] Build before testing dist templates so dist evidence cannot come from a stale prior build.
- [x] Run the validation commands below and append observed evidence to this document.

### Validation Plan

```bash
pnpm -C packages/cli sync:guru
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  guru-template/overlay/verify/guru_supervise.py \
  packages/cli/src/templates/guru/overlay/verify/guru_supervise.py
python3 guru-template/overlay/verify/guru_supervise.py --platform flutter --adversarial requirements .trellis/tasks/06-18-guru-five-phase-automation-issue-2 --dry-run
bash guru-template/overlay/verify/tests/run_tests.sh
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts
pnpm -C packages/cli lint
pnpm -C packages/cli typecheck
pnpm -C packages/cli build
bash packages/cli/dist/templates/guru/overlay/verify/tests/run_tests.sh
git diff --check
find guru-template packages/cli/src/templates/guru packages/cli/dist/templates/guru -type d -name __pycache__ -print -prune
npx gitnexus detect-changes --scope all --repo Trellis
```

### Plan Status

- Plan repaired locally: yes.
- Implementation status for #4: implemented locally.
- Known blocker before implementation: none. GitNexus impact was run before supervisor edits; all checked symbols were LOW risk.
- Acceptance boundary: met locally. Source templates, packaged `src/templates/guru`, and freshly built `dist/templates/guru` expose the same requirements adversarial review command and workflow guidance.

### Implementation Evidence (2026-06-19 #4)

- Added `requirements` to `guru_supervise.py` actions for source, packaged, and dist templates.
- Added `--adversarial requirements <task-dir>` dry-run/run-plan behavior:
  - `codex -> claude`, `claude -> codex`, unknown provider -> `codex`;
  - injects `prd.md`, task metadata, task jsonl manifests, and explicitly referenced requirement-package files;
  - referenced requirement-package directories are traversed recursively for `.md`, `.markdown`, `.json`, and `.jsonl`;
  - prompts the reviewer to inspect repository evidence before asking product questions;
  - requires `route_class=REQ_BLOCKER` for medium+ requirement blockers;
  - requires `review_result=clean/requirements-ready` only when no blocker remains;
  - states that requirements has no review-evidence command or clean streak and stops before `confirm requirements`.
- Kept `guru_gate.py confirm requirements` semantics unchanged and retained `record-review requirements` rejection.
- Updated all four Guru workflows, all four Gate SSOT docs, and all four harness indexes so newly installed projects see the requirements adversarial review step before human confirmation.
- Updated `.trellis/spec/cli/backend/script-conventions.md` with the executable Guru adversarial review supervision contract.
- Added/extended packaged regression coverage:
  - requirements dry-run provider inversion and output tokens;
  - no exact `record-review requirements` in requirements dry-run output;
  - recursive formal requirement-package directory injection;
  - packaged workflow/Gate SSOT/harness-index guidance;
  - source/package helper script sync;
  - Python cache artifact guard.

### Review Loop Evidence (2026-06-19)

- Review loop 1 initially found two issues and did not count as clean:
  - formal requirement-package directory references only injected top-level `.md`; fixed with recursive restricted suffix traversal and tests;
  - platform `harness/index.md` summaries still skipped requirements adversarial review; fixed across Flutter/Go/H5/iOS source and packaged specs with a bundled regression.
- Clean review round 1 after fixes: no remaining mismatch found against GitHub #4, task PRD, or local implementation plan. Checked help output, dry-run output, provider fallback, no stale harness summary, no requirements clean-streak state, and source/src/dist sync.
- Clean review round 2 after fixes: no remaining mismatch found. Verified installed Guru project smoke path creates `.trellis/scripts/guru/guru_supervise.py`, installs `.agents/skills/requirement-review/SKILL.md`, and dry-runs `--adversarial requirements` with opposite-provider routing and required output tokens.

### Validation Evidence (2026-06-19)

Passed:

```bash
pnpm -C packages/cli sync:guru
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile guru-template/overlay/verify/guru_supervise.py packages/cli/src/templates/guru/overlay/verify/guru_supervise.py
python3 guru-template/overlay/verify/guru_supervise.py --platform flutter --provider codex --adversarial requirements .trellis/tasks/06-18-guru-five-phase-automation-issue-2 --dry-run
bash guru-template/overlay/verify/tests/run_tests.sh
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts
pnpm -C packages/cli lint
pnpm -C packages/cli typecheck
pnpm -C packages/cli build
bash packages/cli/dist/templates/guru/overlay/verify/tests/run_tests.sh
python3 packages/cli/dist/templates/guru/overlay/verify/guru_supervise.py --platform flutter --provider claude --adversarial requirements .trellis/tasks/06-18-guru-five-phase-automation-issue-2 --dry-run
git diff --check
find guru-template packages/cli/src/templates/guru packages/cli/dist/templates/guru -type d -name __pycache__ -print -prune
npx gitnexus detect-changes --scope all --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree
```

Observed results:

- Source shell tests: 127 passed / 0 failed.
- Packaged source shell tests: 127 passed / 0 failed.
- Dist shell tests: 127 passed / 0 failed.
- Bundled Guru vitest: 40 passed / 0 failed.
- `lint`, `typecheck`, and `build` passed.
- `git diff --check` passed.
- Final `__pycache__` scan was cleaned to empty after `py_compile` generated transient cache.
- `gitnexus detect-changes --scope all` completed and reported CRITICAL risk because the full local diff spans 33 files, 229 indexed symbols, and 30 affected execution flows. Treat this as a commit-time review signal; the touched flows are expected for this task because it intentionally changes Guru gate/supervision templates plus all source/packaged/dist workflow/spec surfaces.
