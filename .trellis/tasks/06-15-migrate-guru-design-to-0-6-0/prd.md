# Migrate guru design to Trellis 0.6.0

## Goal

Research and plan a complete migration of the current `guru/main` fork design onto the official Trellis `0.6.0` GA baseline without losing guru-specific workflow, templates, specs, gates, or operational guarantees.

## Requirements

- Establish the correct official baseline for `0.6.0` using upstream Git tags, npm registry state, and official changelog/docs.
- Inventory the current guru design surface:
  - fork-level docs and release notes
  - `guru-template/`
  - CLI template and configurator integration
  - Trellis workflow / agents / skills / hooks / config conventions
  - tests and verification gates that protect guru behavior
- Compare `guru/main` against official `v0.6.0` and classify every meaningful delta as one of:
  - keep as guru-specific value
  - replace with official `0.6.0` behavior
  - rework to fit the `0.6.0` architecture
  - drop because official support supersedes it
- Produce a detailed Markdown migration plan that covers file ownership, compatibility risks, expected conflict zones, rollback points, validation strategy, and full-cycle self-review.
- Keep `design.md` and `implement.md` consistent with `migration-plan.md` after implementation starts.
- During plan-review / full-cycle repair turns, do not change product source code unless the user explicitly asks for implementation repair. Planning artifacts under this task may be edited to reflect the live checkout.

## Confirmed Facts

- User confirmed this task should create a Trellis planning task on 2026-06-15.
- Current branch is `guru/main`.
- Current task is `.trellis/tasks/06-15-migrate-guru-design-to-0-6-0`.
- Existing uncommitted changes before this task:
  - `.codex/config.toml`
  - `.agents/skills/gitnexus/`
- Initial local package versions on `guru/main` were `@devsc/trellis@0.6.0-rc.0-guru.2` and `@devsc/trellis-core@0.6.0-rc.0-guru.2`.
- Upstream remote is `https://github.com/mindfold-ai/Trellis.git`.
- Local tag `v0.6.0` points to `f2cc0745a72c98f4fd1adb726efcb5f35ad131e9` with tag message `0.6.0`.
- Official npm registry reports `@mindfoldhq/trellis` latest as `0.6.0`; beta is `0.6.0-beta.23`; rc is `0.6.0-rc.0`.
- Official npm registry reports `@mindfoldhq/trellis-core` latest as `0.6.0`; beta is `0.6.0-beta.23`; rc is `0.6.0-rc.0`.
- Official changelog says `v0.6.0` was released on 2026-06-15 and is a stable promotion of `0.6.0-rc.0` with no new `src/` changes.
- User confirmed `0.6.0-guru.1` as the Guru GA migration target version on 2026-06-16.
- User confirmed on 2026-06-16 that `design-grill` should support a packet-first batch mode: batch-discover multiple questions and recommendations, allow bulk approval for independent low-risk items, and keep blocking/dependency decisions on a one-by-one confirmation path.
- Official npm registry was rechecked on 2026-06-16 and still reports `@mindfoldhq/trellis` and `@mindfoldhq/trellis-core` latest as `0.6.0`.
- GitNexus MCP tools are not exposed in this Codex session. `npx gitnexus status` did not complete and was terminated; GitNexus will not be treated as an authoritative source for this planning pass unless it becomes available.
- As of the latest full-cycle repair pass on 2026-06-16, this task is already `in_progress` and the live worktree contains implementation changes for the Guru GA migration.
- The live package metadata now shows `@devsc/trellis@0.6.0-guru.1` and `@devsc/trellis-core@0.6.0-guru.1`; root scripts now target `@devsc/...` package filters with `--fail-if-no-match`.
- The live implementation adds Guru overlay version ordering in `compareVersions`, treating `0.6.0-guru.1` as newer than official `0.6.0`. This is an intentional fork update-contract deviation from standard SemVer prerelease ordering and must stay documented and tested.
- The live implementation expands `sync-guru-template.js` to bundle the full `guru-template/overlay/` tree into `packages/cli/src/templates/guru/overlay/` while excluding transient cache artifacts.
- Release-chain blocker repaired in this pass: `packages/cli/scripts/release.js` now refuses Guru non-prerelease releases from non-`guru/*` branches and pushes the current `guru/*` branch instead of `origin main --tags`.
- Simulated packaged install found and repaired a runtime packaging blocker:
  `dist/templates/guru/overlay/apply.sh` originally looked for
  `workflows/<id>-workflow.md`, while packaged Guru workflows are normalized to
  `workflows/<id>.md`.
- The packaged overlay installer now resolves both packaged `<id>.md` and
  source-template `<id>-workflow.md` layouts; a Guru bundled regression test
  covers the packaged layout.
- User requested on 2026-06-17 that Guru workflow should default to official
  supervision. The local plan is
  `official-supervision-default-plan.md`, and it supersedes earlier task text
  that treated dogfood `codex.dispatch_mode: sub-agent` as the long-term Guru
  default.
- The accepted supervision direction is: fresh Guru projects default to
  official `trellis channel` supervision, while `inline` and legacy
  `sub-agent` remain explicit rollback modes.
- The current migration worktree is also a Guru dogfood target. After channel
  routing, helper installation, and installed hook copies are updated, it must
  be explicitly switched to `codex.dispatch_mode: channel` for self-proof; this
  does not permit `apply.sh` to silently overwrite arbitrary existing projects.

## Acceptance Criteria

- [ ] Official `0.6.0` baseline is identified with concrete commit/tag/package evidence.
- [ ] Guru design deltas are inventoried across files, templates, specs, hooks, tests, and docs.
- [ ] Official `0.6.0` features that overlap with guru design are mapped explicitly.
- [ ] Guru `design-grill` migration includes the accepted packet-first interaction contract and preserves redline fail behavior, evidence-first lookup, and `guru_gate.py grill-done/skip` completion semantics.
- [ ] Migration strategy distinguishes preserve/adopt/rework/drop decisions.
- [ ] `migration-plan.md` explains target architecture, ownership boundaries, compatibility risks, rollback approach, ordered execution plan, validation commands, and full-cycle review findings.
- [ ] `design.md` and `implement.md` remain consistent with `migration-plan.md` while the task is `in_progress`.
- [x] Guru release orchestration cannot push `origin main` for Guru `patch`, `minor`, `major`, or `promote` releases; `release.js` targets the current `guru/*` branch or fails clearly.
- [ ] Guru overlay version ordering is documented and covered by focused `compareVersions` tests.
- [ ] Full Guru overlay bundling is verified, including exclusion of `__pycache__`, `.pyc`, and `.pyo` artifacts.
- [x] Packaged Guru overlay installation works from `dist/templates/guru/overlay/apply.sh`, including workflow copy, spec/hook/skill install, gate blocking, soft confirm, and `task.py start` release after Gate completion in a fresh simulated project.
- [ ] `official-supervision-default-plan.md` passes full-cycle repair and is
  consistent with `prd.md`, `design.md`, `implement.md`, and
  `migration-plan.md`.
- [ ] Guru default supervision is designed around official `trellis channel`
  runtime without forking channel internals.
- [ ] `guru_supervise.py` or equivalent channel wrapper is treated as P0, not a
  documentation convenience, because Guru default supervision must be
  executable and dry-run verifiable.
- [ ] Legacy `sub-agent` mode remains available as an explicit rollback path,
  but is not the default Guru workflow path for fresh projects.
- [ ] The current migration worktree proves the same default by explicitly
  running on `codex.dispatch_mode: channel` after routing support is installed.
- [ ] `guru_supervise.py` or equivalent helper only passes `--jsonl` manifests
  that exist, so missing `implement.jsonl` / `check.jsonl` cannot create false
  green dry-runs.
- [ ] Official supervision command examples and smoke commands are copy-paste
  safe: each declares its task path and uses run-id channel / worker names.
- [ ] Bundled `trellis-channel` skill references shipped in packaged and
  installed copies do not contain executable `trellis channel ... --tag`
  examples; no-tag warning prose remains allowed.
- [ ] `guru_supervise.py status/kill` uses exact channel and worker handles,
  matching official `trellis channel kill <channel> --as <worker>` semantics.
- [ ] Guru config patching preserves existing `guru.supervision` child keys and
  fills only missing `provider`, `implement_timeout`, `check_timeout`, and
  `warn_before` defaults.
- [ ] Open product/scope decisions are reduced to only questions that cannot be answered from the repository or upstream evidence.
- [ ] No existing user changes are overwritten.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- Current plan/review artifact set is `migration-plan.md`, `design.md`,
  `implement.md`, and `official-supervision-default-plan.md`.
- This PRD now reflects the current implementation-in-progress state, while still preserving the user's boundary that this full-cycle repair turn should not edit product source code.
