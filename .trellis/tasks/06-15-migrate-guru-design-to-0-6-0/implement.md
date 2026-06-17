# Implement - Guru Migration to Trellis 0.6.0 GA

## Current Gate State

- This task is already `in_progress`; this checklist is now an
  implementation-progress checklist, not a pre-start-only plan.
- The current user request is another `full-cycle-plan-repair` pass, so this
  turn may update task planning/review artifacts but must not modify product
  source code.
- The current repair target is `official-supervision-default-plan.md`; it
  supersedes earlier checklist text that treated Codex `sub-agent` dispatch as
  the long-term Guru dogfood default.
- Existing unrelated/user-owned dirty files remain untouched:
  - `.codex/config.toml`
  - `.agents/skills/gitnexus/`
- Official npm/tag state must be rechecked before final release validation
  because release state can drift.
- GitNexus impact analysis is required before editing any function, class, or
  method if GitNexus tools become available; if the index is stale, run the
  prescribed refresh before relying on it.

## Live Implementation Snapshot

- Package versions and root script filters appear moved to
  `@devsc/*@0.6.0-guru.1`.
- Official `0.6.0` manifest and `trellis-channel` assets appear present.
- Dogfood `.trellis/.version` appears moved to `0.6.0-guru.1`.
- `release-preflight.js` and `check-manifest-continuity.js` appear fork-aware.
- `sync-guru-template.js` now copies the full Guru overlay into packaged
  templates and excludes transient cache artifacts.
- `compareVersions` now treats Guru overlay builds as downstream patches newer
  than the matching upstream GA.
- Release push-target blocker is repaired: `packages/cli/scripts/release.js`
  pushes Guru non-prerelease releases to the current `guru/*` branch and fails
  before `git push` when the current branch is unsafe or unknown.
- Simulated packaged install blocker is repaired:
  `guru-template/overlay/apply.sh` now works in both source layout
  (`workflows/<id>-workflow.md`) and packaged layout (`workflows/<id>.md`).
  `packages/cli/test/guru/guru-bundled.test.ts` includes a regression for the
  packaged workflow filenames that `apply.sh` resolves.
- New supervision-default work remains planned, not implemented in this
  documentation-only repair pass: Guru fresh projects should default to
  official `trellis channel` supervision, with `sub-agent` kept only as
  explicit legacy rollback.
- Current `.trellis/config.yaml` still shows `codex.dispatch_mode: sub-agent`;
  after channel routing/helper/installed hook updates land, this migration
  worktree must be explicitly switched to `channel` for dogfood self-proof.

## Execution Checklist

### 0. Branch And Baseline

- [ ] Create or switch to a dedicated branch, for example
  `codex/migrate-guru-to-0.6.0-ga`.
- [ ] Record `git status --short` before edits.
- [ ] Recheck:
  - `git show --no-patch v0.6.0`
  - `npm view @mindfoldhq/trellis version dist-tags --json`
  - `npm view @mindfoldhq/trellis-core version dist-tags --json`
- [ ] Confirm target remains `0.6.0-guru.1`.

### 1. Import Official GA Assets

- [ ] Add `packages/cli/src/migrations/manifests/0.6.0.json`.
- [ ] Add
  `packages/cli/src/templates/common/bundled-skills/trellis-channel/**`.
- [ ] Refresh
  `packages/cli/src/templates/common/bundled-skills/trellis-meta/**`.
- [ ] Adopt applicable official configurator test deltas.
- [ ] Do not import upstream release-task artifacts.

### 2. Preserve Guru Overlay And Update `design-grill`

- [ ] Preserve `guru-template/**` as the Guru source of truth.
- [ ] Verify `sync-guru-template.js` bundles the full
  `guru-template/overlay/` tree into `packages/cli/src/templates/guru/overlay/`.
- [ ] Verify bundled overlay contains `design-grill`, `apply.sh`,
  `guru_gate.py`, and `grill-nudge.sh`.
- [ ] Verify bundled overlay excludes `__pycache__`, `.pyc`, and `.pyo`.
- [ ] Update `guru-template/overlay/agents-skills/design-grill/SKILL.md` to
  define the accepted packet-first `Design Grill Packet` contract.
- [ ] Preserve evidence-first lookup, redline fail behavior, sequential handling
  for blockers/dependencies, and Chinese-first artifact output.
- [ ] Preserve `guru_gate.py grill-done/skip` as the only durable completion or
  skip record.
- [ ] Ensure workflow text still orders `design-grill` before confirm and before
  `task.py start`.
- [ ] Run `pnpm -C packages/cli sync:guru`.
- [ ] Verify packaged Guru templates reflect source template changes.
- [x] Verify packaged `dist/templates/guru/overlay/apply.sh` can install into a
  fresh simulated project and copy `guru-client.md` into `.trellis/workflow.md`.

### 3. Version And Package Identity

- [ ] Update CLI/core versions to `0.6.0-guru.1`.
- [ ] Keep package names `@devsc/trellis` and `@devsc/trellis-core`.
- [ ] Preserve GitHub Packages publish config.
- [ ] Update lockfile if package metadata requires it.
- [ ] Verify packed CLI does not accidentally depend on official core.
- [ ] Verify Guru overlay version ordering in `compareVersions`: `0.6.0-guru.1`
  must sort after upstream `0.6.0` and `0.6.0-rc.0`.

### 4. Root Script Repair

- [x] Replace stale root filters targeting `@mindfoldhq/...`, including
  `.lintstagedrc`.
- [x] Prefer fork package names or path selectors that cannot silently no-op.
- [x] Add or update checks so "No projects matched the filters" is a failure.
- [x] Validate root `build`, `test`, `lint`, and package-scoped commands run the
  intended packages.

### 5. Release And Preflight Repair

- [ ] Make release scripts fork-aware.
- [ ] Make release preflight registry-aware using `publishConfig.registry`.
- [ ] Split official public continuity checks from Guru private package checks.
- [ ] Make packed CLI verification alias-aware.
- [x] Repair or block `release.js` so Guru `patch`, `minor`, `major`, and
  `promote` releases cannot push `origin main --tags`.
- [ ] Update release docs for the Guru private release path.

### 6. Dogfood Update

- [ ] Update `.trellis/.version` to the Guru GA version.
- [ ] Refresh installed bundled skills across local skill surfaces.
- [ ] Ensure `trellis-channel` is installed where bundled skills are supported.
- [ ] Refresh template hashes.
- [ ] Do not silently overwrite existing `.trellis/config.yaml`
  `codex.dispatch_mode`, but make fresh Guru projects default to
  `codex.dispatch_mode: channel` through the supervision config patch.
- [ ] After channel routing and installed hooks are updated, explicitly switch
  this migration worktree `.trellis/config.yaml` to
  `codex.dispatch_mode: channel` and record the rollback point.
- [ ] Confirm Guru overlay maintenance does not remove official bundled skills.
- [ ] Audit the large `trellis-meta` refresh/deletion set and confirm removed
  old reference files are replaced by the intended `local-architecture`
  structure rather than user-owned content loss.

### 7. Official Supervision Default

- [x] Implement `channel` mode in workflow-state injection and phase-detail
  routing.
- [ ] Update Guru workflow blocks so ordinary `planning` / `in_progress` are
  channel defaults, while legacy wording lives in `planning-sub-agent` /
  `in_progress-sub-agent`.
- [x] Add `guru_supervise.py` or equivalent P0 helper that wraps official
  `trellis channel` commands without reading/writing channel event stores
  directly.
- [x] Add an idempotent `guru_config_patch.py` or equivalent config patcher for
  `codex.dispatch_mode`, `channel.worker_guard`, `guru.platform`, and
  `guru.supervision`.
- [x] Ensure `guru_config_patch.py` merges `guru.supervision` by child key:
  preserve existing provider/timeouts and fill only missing defaults.
- [x] Ensure channel workers receive the platform-specific Guru
  implementation/review skill context.
- [x] Ensure helper dry-run only includes `--jsonl` when `implement.jsonl` /
  `check.jsonl` exists.
- [x] Add helper dry-run tests covering provider, run id naming, conditional
  jsonl injection, and Guru skill `--file` injection.
- [ ] Ensure workflow snippets and provider smoke are copy-paste safe: each
  declares `TASK` and uses run-id channel / worker names.
- [x] Repair packaged and installed `trellis-channel` skill references so they
  do not contain executable `trellis channel ... --tag` examples; keep only
  no-tag warning prose and add a grep verification.
- [x] Ensure helper `status` prints exact channel / worker handles and helper
  `kill` requires exact `--channel` + `--worker` values.
- [x] Cover `inline`, legacy `sub-agent`, and default `channel` routing in
  focused tests.
- [x] Run simulated Guru project smoke that proves Gate, `task.py start`,
  channel dry-run, and `trellis update --dry-run` all trigger correctly.
  Evidence from `/tmp/trellis-guru-smoke.q09dI9`:
  - first `task.py start` blocked in `before_start` on missing design-grill
    record;
  - after soft-mode smoke gate records, `guru_gate.py check` and second
    `task.py start` passed;
  - `guru_supervise.py implement/check --dry-run` emitted official
    `trellis channel create/spawn/send/wait/messages` commands with Flutter
    Guru skill files and `implement.jsonl` / `check.jsonl`;
  - `node packages/cli/bin/trellis.js update --dry-run` reported
    project/CLI version `0.6.0-guru.1` and made no changes.
- [ ] Run dogfood self-proof in this worktree after restoring a valid Trellis
  developer identity/current-task pointer for `.trellis/scripts/get_context.py`.

### 8. Documentation

- [ ] Update fork-facing release/migration docs.
- [ ] Document official features now supported:
  - migration manifest continuity
  - `trellis-channel`
  - refreshed `trellis-meta`
  - `trellis mem` compatibility assumptions from official `0.6.0`
- [ ] Document Guru intentional differences:
  - private package identity and registry
  - official channel supervision default
  - legacy Codex sub-agent rollback mode
  - Guru overlay/gate behavior

### 9. Final Validation

Run the minimum validation set:

```bash
pnpm install
pnpm --filter @devsc/trellis-core test
pnpm --filter @devsc/trellis test
pnpm test
pnpm --filter @devsc/trellis lint
pnpm --filter @devsc/trellis typecheck
pnpm --filter @devsc/trellis test -- test/utils/compare-versions.test.ts
pnpm --filter @devsc/trellis test -- test/guru/guru-bundled.test.ts
pnpm -C packages/cli sync:guru
git diff --exit-code packages/cli/src/templates/guru
bash guru-template/overlay/tests/apply_test.sh
node packages/cli/scripts/release-preflight.js check-versions
node packages/cli/scripts/release-preflight.js publish-plan --json
node packages/cli/scripts/release-preflight.js verify-packed-cli
```

Packaged install smoke:

```bash
pnpm build
node packages/cli/bin/trellis.js init -u SmokeGuru --yes --claude --codex --workflow guru-client --no-monorepo
bash packages/cli/dist/templates/guru/overlay/apply.sh <smoke-project> flutter
python3 .trellis/scripts/task.py create "Guru smoke flow" --slug guru-smoke-flow
python3 .trellis/scripts/task.py start .trellis/tasks/<task>   # first run must be blocked by before_start
python3 .trellis/scripts/guru/guru_gate.py check .trellis/tasks/<task>
python3 .trellis/scripts/task.py start .trellis/tasks/<task>   # after grill+confirm must pass
node packages/cli/bin/trellis.js update --dry-run
```

Run targeted checks:

```bash
rg "@mindfoldhq/trellis" package.json packages/cli/scripts
rg "function pushTarget|git push origin" packages/cli/scripts/release.js
rg "0.6.0 < 0.6.0-guru.1|Guru overlay" packages/cli/src/utils/compare-versions.ts packages/cli/test/utils/compare-versions.test.ts
find packages/cli/src/templates/common/bundled-skills -maxdepth 1 -type d | sort
find packages/cli/src/templates/guru/overlay -type f | sort
find .agents .claude .cursor .opencode .pi -path "*/skills/trellis-channel" -type d
rg "dispatch_mode: channel|in_progress-channel|in_progress-sub-agent" .trellis/config.yaml guru-template packages/cli/src/templates
rg "run_blocking_task_hooks" packages/cli/src/templates/trellis/scripts
rg "Design Grill Packet|packet-first|grill-done|grill-skip" guru-template packages/cli/src/templates/guru
python3 .trellis/scripts/get_context.py --mode phase --platform codex | rg "codex-channel|trellis channel"
python3 .trellis/scripts/guru/guru_supervise.py implement .trellis/tasks/<task> --dry-run
python3 .trellis/scripts/guru/guru_supervise.py check .trellis/tasks/<task> --dry-run
```

## Review Gates For Continued Implementation / Check Work

- [ ] PRD has no open product/scope blocker.
- [ ] `design.md` and `implement.md` are present and consistent with
  `migration-plan.md` and `official-supervision-default-plan.md`.
- [ ] `implement.jsonl` and `check.jsonl` include the PRD, plan, `design-grill`,
  workflow, gate, and test context.
- [ ] Current `in_progress` implementation state is acknowledged before
  dispatching further implement/check work.
- [x] Release-readiness review treats `release.js` push targeting as fixed for
  Guru releases, with regression coverage in `test/scripts/release.test.ts`.

## Rollback Points

| Phase | Rollback point |
|---|---|
| Official GA assets | Revert manifest/common bundled skill/test imports. |
| Guru overlay | Revert `guru-template/**`, rerun sync, and verify packaged templates. |
| Version identity | Revert package metadata and lockfile. |
| Root scripts | Revert selectors, then repair with path selectors if package selectors are fragile. |
| Release preflight | Revert release script edits and block publish. |
| Dogfood | Restore local `.trellis`, skill dirs, and hashes from diff before publish. |
| Official supervision default | Revert Guru config patch/helper/workflow-state routing while leaving official `trellis-channel` assets intact. |
| Published package failure | Do not overwrite; publish a corrected Guru patch. |

## Completion Criteria

- Source and dogfood state support official `0.6.0` GA features while preserving
  Guru-specific overlay behavior.
- `design-grill` packet-first mode is documented and installed without weakening
  hard gate semantics.
- Root scripts and release preflight cannot pass by silently targeting no
  packages or the wrong registry.
- Release orchestration cannot push `origin main --tags` for the Guru package
  line.
- Guru overlay version ordering and full overlay packaging are covered by
  focused tests.
- Official supervision default is covered by plan, routing tests, overlay
  config tests, dogfood self-proof, and simulated Guru project smoke.
- Validation commands pass, or any failures are documented with explicit
  blocker status.
