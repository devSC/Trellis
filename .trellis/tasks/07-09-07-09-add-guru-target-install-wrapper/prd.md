# Add Guru target install wrapper script

## Goal

Add a one-command wrapper for initializing/applying/verifying Guru overlay installation into a target repo.

## Confirmed Facts

- User approved adding a direct install script after the `wproxy` installation required too many manual steps.
- Existing low-level installer remains `trellis guru apply <platform> <target>`.
- Existing source build/sync commands are `pnpm --filter @devsc/trellis run build` and `pnpm --filter @devsc/trellis run sync:guru:check`.
- This task must not reimplement `apply.sh`; it should provide a thin operator wrapper around current install and smoke-check commands.
- `guru_gate.py intake` recommended `route=lite_task`, `risk=medium`, with write scope limited to `packages/cli/scripts/guru-install-target.sh` and `packages/cli/package.json`.
- User confirmed sibling-package install targets after wrapper creation: `/Users/devSC/Documents/JobProject/guru_ai_himora` and `/Users/devSC/Documents/MyProject/safe_land_web`.

## Requirements

### BHV-001 Add one-command Guru target installation

Given a maintainer is in the Trellis source checkout and has a target repository path,
When they run the wrapper with a supported platform and target path,
Then the command prepares the local source, applies Guru overlay from this checkout, runs target smoke checks, and exits non-zero on real install/smoke failure.

### BHV-002 Avoid duplicating installer internals

Given `trellis guru apply` and `guru-template/overlay/apply.sh` are the existing install authorities,
When the wrapper installs or refreshes a target,
Then it delegates to those authorities instead of copying overlay install logic into a second implementation.

### BHV-003 Treat bootstrap gate gaps as advisory

Given bootstrap tasks are not real feature PRDs and may fail `check-start`,
When the wrapper runs post-install smoke checks,
Then it reports bootstrap `check-start` as advisory and does not classify the expected rc=2 gate block as an install failure.

### REQ-001 Provide a one-command operator entrypoint

Add a repo-local script that installs or refreshes Guru overlay into a target repo from the current source checkout with:

- platform argument: `flutter|go|ios|h5`;
- target path argument;
- optional init behavior for targets that do not yet have `.trellis/`;
- optional source build/check control.

### REQ-002 Preserve existing installer boundaries

The wrapper must call existing Trellis/Guru commands instead of duplicating `apply.sh` logic.

It must not overwrite target project conventions, business code, or target repository git state beyond what `trellis init` and `trellis guru apply` already do.

### REQ-003 Verify target behavior after install

The wrapper must run target smoke checks that catch the class of false-green install failures seen in prior debugging:

- Guru Python scripts compile;
- `get_context.py` runs;
- `guru_gate.py status .trellis/tasks/00-bootstrap-guidelines` runs when bootstrap task exists;
- generated Python `__pycache__` under target `.trellis/scripts` is removed afterward.

### REQ-004 Keep command output operator-friendly

Output must clearly distinguish:

- source preparation;
- target initialization;
- overlay apply;
- target smoke checks;
- expected bootstrap gate gaps vs install failures.

### REQ-005 Expose the script through package scripts

Add an npm/pnpm script entry so maintainers can invoke the wrapper without remembering its path.

## Core Capabilities

- P0: Install or refresh Guru overlay into an existing target repo with one command.
- P0: Run target smoke checks after apply and fail on real install errors.
- P0: Keep wrapper implementation thin by delegating to existing installer commands.
- P1: Optionally initialize a target without `.trellis/` before applying overlay.
- P1: Provide flags to skip source preparation when the caller has already built the source.

## Failure Paths

- Unsupported platform exits non-zero before changing the target.
- Missing target path exits non-zero before changing the target.
- Missing `pnpm`, `node`, or `python3` exits non-zero with an actionable message.
- Source preparation failure exits non-zero before target apply.
- `guru apply` failure exits non-zero.
- Target smoke failure exits non-zero, except documented advisory bootstrap `check-start` failure.

## Open Questions

None. The first version is intentionally a local maintainer wrapper, not a published end-user command with a new TypeScript CLI surface.

## Acceptance Criteria

- [ ] `packages/cli/scripts/guru-install-target.sh` exists and is executable.
- [ ] `packages/cli/package.json` exposes `guru:install`.
- [x] Running the wrapper against `/Users/devSC/Documents/MyProject/wproxy` with platform `ios` completes successfully.
- [x] The wrapper output includes install/apply/smoke phases and preserves `guru apply` self-check output.
- [x] The wrapper cleans target `.trellis/scripts/**/__pycache__`.
- [x] `pnpm --filter @devsc/trellis run sync:guru:check` passes.
- [x] `pnpm --filter @devsc/trellis run build` passes.
- [ ] Existing Guru overlay apply tests still pass or the relevant targeted install smoke is documented.
- [x] Running the wrapper against `/Users/devSC/Documents/JobProject/guru_ai_himora` with platform `flutter` completes successfully or any target-local blocker is reported with evidence.
- [x] Running the wrapper against `/Users/devSC/Documents/MyProject/safe_land_web` with the detected web platform completes successfully or any target-local blocker is reported with evidence.

## Brainstorm Evidence

- Skill loaded: `trellis-before-dev`.
- Repository evidence inspected: `package.json`, `packages/cli/package.json`, `packages/cli/scripts/`, `packages/cli/src/commands/guru.ts`, `guru-template/overlay/apply.sh`, previous `wproxy` install/smoke output.
- Domain/terminology triggers: "one-command install" means operator wrapper, not a replacement for `apply.sh`.
- Current code vs user intent conflicts: prior active task was docs-only and explicitly forbade install script changes, so this implementation is isolated in this child task.
- Product decisions confirmed:
  - decision: add a repo-local thin wrapper and package script.
  - source_quote: `好`
  - result: implement `guru-install-target.sh` plus `guru:install`.
  - decision: install the wrapper output into sibling packages after confirming target scope.
  - source_quote: `是，包括 safe_land_web`
  - result: target install scope is `guru_ai_himora` plus `safe_land_web`.
- Open product/scope/risk questions:
  - reason: no blocking product question remains; user explicitly approved the wrapper and repository evidence fixes the first-version scope.

### Question Policy

question_policy: evidence_only

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
