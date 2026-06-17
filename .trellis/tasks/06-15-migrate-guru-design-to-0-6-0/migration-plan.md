# Guru Design Migration Plan to Trellis 0.6.0 GA

## Status

- Task: `migrate-guru-design-to-0-6-0`
- Mode: implementation-in-progress plan repair
- Artifact role: Markdown migration plan plus full-cycle review record
- Product code status: live checkout already contains implementation changes; this
  review pass updates only task planning/review artifacts and leaves product code
  untouched
- Target package line: accepted `0.6.0-guru.1`
- Review method: `full-cycle-plan-repair`
- Accepted `design-grill` interaction change: packet-first batch discovery with
  bulk approval for independent items, while keeping blocking/dependency
  decisions on a one-by-one confirmation path.

This document started as the plan artifact requested by the user. As of the
latest repair pass on 2026-06-16, the task is already `in_progress` and the
worktree contains implementation changes. This pass does not implement or repair
product code; it re-audits the plan artifacts against the live checkout and
records the remaining implementation blockers.

## Intake Map

| Item | Current state |
|---|---|
| Task directory | `.trellis/tasks/06-15-migrate-guru-design-to-0-6-0` |
| Task status | `in_progress` |
| PRD | `.trellis/tasks/06-15-migrate-guru-design-to-0-6-0/prd.md` |
| Plan path | `.trellis/tasks/06-15-migrate-guru-design-to-0-6-0/migration-plan.md` |
| Tracker issue / PR | None linked |
| User mode | Full-cycle plan repair only in this request; no product-code changes in this pass |
| Source of truth | Live checkout + official `v0.6.0` tag + npm registry + official changelog |
| Current branch | `guru/main` |
| Dirty worktree state | Large implementation diff is present across package, release, template, dogfood, and test surfaces; preserve unrelated/user-owned changes |
| Pre-existing unrelated dirty files from initial intake | `.codex/config.toml`, `.agents/skills/gitnexus/` |
| GitNexus | Not available in this Codex session; do not treat it as authoritative for this pass |

## Confirmed Evidence

### Official 0.6.0 Baseline

- `git show --no-patch v0.6.0` resolves to commit
  `f2cc0745a72c98f4fd1adb726efcb5f35ad131e9`, tagged `v0.6.0`, timestamp
  `2026-06-15 15:34:36 +0800`.
- `npm view @mindfoldhq/trellis ...` reports:
  - `version = 0.6.0`
  - `dist-tags.latest = 0.6.0`
  - `dist-tags.beta = 0.6.0-beta.23`
  - `dist-tags.rc = 0.6.0-rc.0`
- `npm view @mindfoldhq/trellis-core ...` reports the same `0.6.0` latest,
  beta, and rc line.
- The npm dist-tags above were rechecked on 2026-06-16 and still point to
  official `0.6.0`.
- The user confirmed `0.6.0-guru.1` as the Guru GA migration target version on
  2026-06-16.
- The user confirmed on 2026-06-16 that `design-grill` should support a
  packet-first batch mode to avoid inefficient one-question-per-turn operation:
  batch-discover multiple questions and recommendations, allow bulk approval
  for independent low-risk items, and keep redline/dependency decisions on a
  one-by-one confirmation path.
- Official `v0.6.0-rc.0..v0.6.0` file delta includes:
  - added `packages/cli/src/migrations/manifests/0.6.0.json`
  - added `packages/cli/src/templates/common/bundled-skills/trellis-channel/**`
  - modified `packages/cli/src/templates/common/bundled-skills/trellis-meta/**`
  - modified `packages/cli/test/configurators/platforms.test.ts`
  - package version bumps to `0.6.0`
- Official changelog states that `0.6.0` is a stable promotion of rc.0 with no
  new `src/` runtime changes since rc.0.

### Current Guru Fork State Rechecked On 2026-06-16

- Task status is now `in_progress` in `task.json`; the working tree already
  contains implementation changes for this migration.
- Root scripts now target fork package filters:
  `package.json:6-21` uses `@devsc/trellis-core` and `@devsc/trellis` with
  `--fail-if-no-match`.
- CLI package identity is now
  `@devsc/trellis@0.6.0-guru.1` with GitHub Packages restricted publish config:
  `packages/cli/package.json:2-15`.
- Core package identity is now
  `@devsc/trellis-core@0.6.0-guru.1` with GitHub Packages restricted publish
  config: `packages/core/package.json:2-43`.
- CLI still imports the core under the official dependency key, but the
  workspace alias points at the fork core package:
  `packages/cli/package.json:56-58`.
- Official `0.6.0` assets are now present in the worktree:
  - `packages/cli/src/migrations/manifests/0.6.0.json`
  - `packages/cli/src/templates/common/bundled-skills/trellis-channel/**`
  - refreshed common `trellis-meta` surfaces
- Local dogfood version is now `.trellis/.version = 0.6.0-guru.1`.
- `.trellis/.template-hashes.json` now includes installed
  `trellis-channel` entries across `.agents`, `.claude`, `.cursor`,
  `.opencode`, and `.pi`, and refreshed `trellis-meta` hashes.
- Earlier migration work intentionally kept Codex sub-agent dogfood mode:
  `.trellis/config.yaml:70-71`. This is now superseded by
  `official-supervision-default-plan.md`: fresh Guru projects should default to
  official `trellis channel` supervision, while existing `sub-agent` values are
  preserved unless the user explicitly switches them.
- `guru_supervise.py` or an equivalent wrapper is a P0 migration artifact for
  the official supervision default. Workflow prose alone is not sufficient for
  Guru GA because the wrapper owns repeatable channel invocation, provider
  selection, Guru skill injection, dry-run verification, and failure evidence.
- Official supervision command examples are part of the migration contract:
  standalone blocks must declare `TASK` and derive channel / worker names from
  `RUN_ID`, including provider smoke, so repeated validation does not collide
  with old channel logs.
- Helper control commands are part of the same contract: `status` must show
  exact channel / worker handles, and `kill` must require exact values so it
  maps to official `trellis channel kill <channel> --as <worker>` behavior.
- Guru config patching is child-key merge, not block replacement:
  `channel.worker_guard` and `guru.supervision` preserve existing child values
  and fill only missing defaults.
- Bundled `trellis-channel` docs must match the v0.6.0 no-tag CLI contract:
  packaged and installed references may explain that `--tag` is unsupported,
  but must not ship executable `trellis channel ... --tag` examples.
- This migration worktree is the Guru dogfood target, so it must be explicitly
  switched to `codex.dispatch_mode: channel` after routing/helper/installed
  hook support lands. That deliberate dogfood switch is separate from
  protecting arbitrary existing projects from silent `apply.sh` overwrites.
- `sync-guru-template.js` now copies every spec package, every Guru workflow,
  and the full `guru-template/overlay/` tree into
  `packages/cli/src/templates/guru/`, while excluding `__pycache__`,
  `.DS_Store`, `.pyc`, and `.pyo`: `packages/cli/scripts/sync-guru-template.js:7-22`
  and `45-88`.
- Guru bundled tests now verify the packaged overlay skill/gate files and
  transient-artifact exclusion: `packages/cli/test/guru/guru-bundled.test.ts:183-214`.
- `compareVersions` now intentionally treats Guru overlay builds as downstream
  patches newer than the matching upstream GA:
  `packages/cli/src/utils/compare-versions.ts:43-53`, covered by
  `packages/cli/test/utils/compare-versions.test.ts:145-159`.
- Release preflight is now registry-aware and accepts fork aliases in packed CLI
  verification: `packages/cli/scripts/release-preflight.js:66-99` and
  `110-115`.
- Manifest continuity now has separate default fork mode and `--official` mode,
  with Guru package versions mapped back to the official base manifest:
  `packages/cli/scripts/check-manifest-continuity.js:20-24` and `98-101`.
- Release-chain blocker repaired in this pass: `packages/cli/scripts/release.js`
  now exports a tested `pushTarget` guard. Official stable releases still push
  `main`, beta/rc releases still push `HEAD`, and Guru non-prerelease releases
  push the current `guru/*` branch or fail clearly before pushing tags.
- User-owned config preservation still must remain intact:
  - AGENTS managed-block merge: `packages/cli/src/commands/update.ts:157-182`
  - Claude settings defaults merge:
    `packages/cli/src/configurators/claude.ts:65-88`
  - shared merge semantics:
    `packages/cli/src/configurators/shared.ts:763-800`

## Target State

After migration, the Guru fork should be:

1. Based on official `v0.6.0` GA rather than `v0.6.0-rc.0`.
2. Published as `@devsc/trellis@0.6.0-guru.1` and
   `@devsc/trellis-core@0.6.0-guru.1`.
3. Fully compatible with official 0.6.0 runtime, update, channel, mem, and
   bundled-skill behavior.
4. Still preserving Guru-specific workflow/spec/overlay/gate design.
5. Able to pass root scripts, package tests, guru overlay tests, and release
   preflight without false positives.
6. Able to dogfood in this checkout without removing user files, Guru skills,
   existing local dispatch choices, or existing local customizations.
7. Able to run `design-grill` in the accepted packet-first mode without
   weakening Guru Gate semantics: the packet is a review accelerator, not a
   completion credential, and `guru_gate.py grill-done/skip` remains the only
   durable gate record.
8. Able to default fresh Guru workflows to official `trellis channel`
   supervision while preserving `inline` and legacy `sub-agent` rollback modes.

## Migration Strategy

Use a three-layer migration strategy:

| Layer | Action | Boundary |
|---|---|---|
| Official GA common layer | Adopt official `v0.6.0` manifest, `trellis-channel`, refreshed `trellis-meta`, and relevant tests | Do not import upstream release task history as product source |
| Guru overlay layer | Preserve Guru workflow/spec/overlay/gate/before_start behavior | Do not let official templates overwrite Guru contracts |
| Fork release/dogfood layer | Rework version, root scripts, release preflight, private registry, and local installed skills | Do not rely on official public npm assumptions |

## Preserve / Adopt / Rework / Drop Matrix

| Area | Decision | Details |
|---|---|---|
| `0.6.0.json` manifest | Adopt | Required for GA update-chain continuity, even though migrations are empty. |
| `trellis-channel` bundled skill | Adopt | Required for official 0.6.0 channel runtime user-facing support. |
| Official refreshed `trellis-meta` | Adopt with review | Keep official common skill canonical; Guru-specific guidance stays in Guru overlay / local skills. |
| `packages/cli/test/configurators/platforms.test.ts` official delta | Adopt if still applicable | Ensures bundled skill / platform config coverage matches official GA. |
| Official release task artifacts | Drop | Upstream planning records are not runtime/package inputs. |
| `guru-template/**` | Preserve | Guru SSOT for overlay/spec/workflow/skills. |
| `packages/cli/src/templates/guru/**` | Preserve | CLI-bundled Guru offline distribution. |
| `sync-guru-template.js` | Preserve | Keeps Guru SSOT and packaged copies synchronized. |
| Guru workflow resolver additions | Preserve | Required for offline `guru-*` workflow listing/resolution. |
| Guru spec offline install | Preserve | Required for Guru spec templates without marketplace/network. |
| `design-grill` interaction contract | Rework | Replace strict one-question-per-turn default with packet-first batch discovery: output bounded question/recommendation packets, permit bulk approval for independent low-risk items, and keep blocker/redline/dependency items on a sequential confirmation path. |
| AGENTS block merge | Preserve | Prevents clobbering user instructions. |
| Claude settings merge | Preserve | Prevents clobbering user hooks/settings. |
| `before_start` blocking hook | Preserve | Required for Guru hard gate before implementation starts. |
| `codex.dispatch_mode: sub-agent` in existing repos | Preserve as existing user choice | Superseded as a fresh Guru default by `official-supervision-default-plan.md`; keep only as explicit rollback / existing-project value. |
| Root `@mindfoldhq` pnpm filters | Rework | Current filters can produce false-green scripts after package fork. |
| Release/preflight npm assumptions | Rework | Must support `@devsc` + GitHub Packages and workspace alias packing. |
| `.trellis/.version` | Rework | Must become the Guru GA version after dogfood update. |

## Implementation Plan

### Phase 0: Branch and Guardrails

1. Create a dedicated branch such as `codex/migrate-guru-to-0.6.0-ga`.
2. Preserve existing unrelated dirty files:
   - `.codex/config.toml`
   - `.agents/skills/gitnexus/`
3. In full-cycle repair turns, do not edit product code unless the user asks for
   implementation repair. Treat any existing implementation diff as live
   evidence to audit, not as permission to expand code scope.
4. Record the current official npm dist-tags and local `v0.6.0` tag before
   any code change.

Acceptance:

- Branch exists.
- `git status --short` shows only expected pre-existing dirty paths plus new
  migration work.
- Official npm latest is still `0.6.0` for CLI and core.

### Phase 1: Import Official GA Assets

1. Bring in `packages/cli/src/migrations/manifests/0.6.0.json` from official
   `v0.6.0`.
2. Bring in the complete
   `packages/cli/src/templates/common/bundled-skills/trellis-channel/**`
   directory.
3. Refresh
   `packages/cli/src/templates/common/bundled-skills/trellis-meta/**` from
   official `v0.6.0`.
4. Bring in the official `packages/cli/test/configurators/platforms.test.ts`
   delta if it still matches the Guru fork structure.
5. Do not import upstream `.trellis/tasks/06-15-release-v0-6-0-ga/**`.

Acceptance:

- `find packages/cli/src/templates/common/bundled-skills/trellis-channel -type f`
  lists the official skill and reference files.
- `packages/cli/src/migrations/manifests/0.6.0.json` exists.
- Common bundled skill scanning requires no new registration code because
  `getBundledSkillTemplates()` already scans directories.

### Phase 2: Protect Guru Behavior During Merge

1. Verify `guru-template/**` remains the SSOT.
2. Run `pnpm -C packages/cli sync:guru` after any Guru template touch.
3. Verify `packages/cli/src/templates/guru/**` remains synchronized with
   `guru-template/**`.
4. Verify `sync-guru-template.js` copies the full `guru-template/overlay/` tree
   into the packaged Guru template and excludes transient cache artifacts.
5. Preserve workflow IDs:
   - `guru-client`
   - `guru-go`
   - `guru-ios`
   - `guru-h5`
6. Preserve offline workflow listing/resolution.
7. Preserve bundled spec offline install.
8. Preserve `before_start` blocking hook in `task.py` and `task_utils.py`.
9. Preserve AGENTS and settings merge semantics.
10. Update `guru-template/overlay/agents-skills/design-grill/SKILL.md` so the
   default interaction is a bounded `Design Grill Packet`, not unconditional
   one-question-per-turn.
11. Sync the `design-grill` contract into packaged Guru templates after the
    source template changes.

Acceptance:

- `packages/cli/test/guru/guru-bundled.test.ts` still passes.
- Packaged Guru overlay contains `design-grill`, `apply.sh`, `guru_gate.py`, and
  `grill-nudge.sh`, and does not bundle `__pycache__`, `.pyc`, or `.pyo`.
- Guru workflows resolve with `source = bundled` when network is unavailable.
- Guru specs install offline when no registry is provided.
- `task.py start` still calls `run_blocking_task_hooks("before_start", ...)`.
- The packaged `design-grill` skill describes the accepted packet-first
  contract:
  - packet size is bounded, defaulting to no more than eight candidate items;
  - each item includes ID, artifact anchor, risk, recommendation, evidence,
    proposed write-back target, and dependency status;
  - independent `NORMAL` items can be bulk-approved by the user;
  - `BLOCKER`, redline, and dependency-setting items still require sequential
    confirmation;
  - packet completion alone does not unlock the gate; only
    `guru_gate.py grill-done/skip` records the durable completion/skip state.

### Phase 3: Version and Package Identity

1. Update CLI and core packages to the chosen Guru GA version:
   `0.6.0-guru.1`.
2. Keep package names:
   - `@devsc/trellis`
   - `@devsc/trellis-core`
3. Keep GitHub Packages publish config.
4. Keep the CLI dependency key as `@mindfoldhq/trellis-core` only if packed
   package verification confirms the alias resolves to the fork package in a
   publish-safe way.
5. Document and test Guru overlay version ordering: `0.6.0-guru.1` is treated
   as newer than upstream `0.6.0` for update/migration gates, even though a
   standard SemVer prerelease would normally sort below the final release.
6. Update lockfile if package metadata changes require it.

Acceptance:

- CLI/core package versions match exactly.
- `node packages/cli/scripts/release-preflight.js check-versions` passes.
- Packed CLI does not resolve the core dependency to official
  `@mindfoldhq/trellis-core@0.6.0`.
- Focused `compareVersions` tests cover Guru overlay ordering against upstream
  GA and RC versions.

### Phase 4: Root Script Repair

1. Replace root package filters that target `@mindfoldhq/...`.
2. Use either:
   - `@devsc/trellis` / `@devsc/trellis-core`, or
   - path-based selectors if more robust for future fork naming.
3. Add a validation check that root scripts do not silently no-op.
4. Treat any `No projects matched the filters` output from root build/test/lint
   as failure.

Acceptance:

- `pnpm test` runs both core and CLI tests.
- `pnpm build` builds both core and CLI.
- Root `package.json` no longer uses stale official filters for fork package
  scripts.

### Phase 5: Release / Preflight Repair

1. Make `release.js` use the fork package filters or package metadata instead
   of hard-coded `@mindfoldhq` filters.
2. Make `release-preflight.js` registry-aware:
   - read `publishConfig.registry`
   - support GitHub Packages
   - do not hard-code public npm for fork publish checks
3. Keep official public npm checks only where explicitly checking upstream
   official continuity.
4. Make packed CLI verification alias-aware.
5. Clarify manifest continuity mode:
   - official package continuity check
   - Guru private package continuity check
6. Update release docs so humans do not accidentally run upstream-public
   release assumptions for Guru.
7. Repair or block `release.js` push targeting so Guru `patch`, `minor`,
   `major`, and `promote` releases cannot push `origin main --tags`.

Acceptance:

- `release-preflight.js publish-plan --json` reports the Guru package names.
- Registry checks use the expected registry for Guru publishing.
- `verify-packed-cli` passes for the fork package shape.
- No release script silently queries official public npm when validating a Guru
  private release, unless the mode explicitly says it is checking upstream.
- `packages/cli/scripts/release.js` either pushes the current Guru release
  branch safely or refuses Guru releases with a clear error. It must not push
  `origin main --tags` for the Guru package line.

### Phase 6: Dogfood Update in This Checkout

1. Update `.trellis/.version` to the Guru GA version.
2. Refresh installed bundled skills across supported local platforms:
   - `.agents/skills`
   - `.claude/skills`
   - `.cursor/skills`
   - `.opencode/skills`
   - `.pi/skills`
3. Ensure `trellis-channel` is installed where bundled skills are supported.
4. Refresh `trellis-meta`, `trellis-session-insight`, and
   `trellis-spec-bootstrap` to match the packaged templates.
5. Update `.template-hashes.json` accordingly.
6. Preserve any existing `.trellis/config.yaml` `codex.dispatch_mode` value
   unless the user explicitly switches it; fresh Guru installs should default
   to `codex.dispatch_mode: channel` via the official supervision plan.
7. For this migration worktree only, explicitly switch `.trellis/config.yaml`
   to `codex.dispatch_mode: channel` after routing/helper/installed hook support
   is in place, then run dogfood self-proof.
8. Verify Guru overlay maintenance does not remove official bundled skills.
9. Audit the large `trellis-meta` refresh/deletion set so removed reference
   files are confirmed to be replaced by the new local-architecture structure
   and are not user-owned content loss.

Acceptance:

- `trellis-channel` exists in the expected local skills directories.
- `.trellis/.version` equals the Guru GA package version.
- User-owned AGENTS content outside the managed block remains intact.
- User-owned Claude settings/hooks remain intact.
- Guru `before_start` gate still blocks unapproved starts.

### Phase 7: Documentation Update

1. Update fork-facing docs such as `GURU_FORK.md` and `TRELLIS_RELEASES.md`.
2. Document that Guru `0.6.0-guru.1` is based on official `v0.6.0` GA.
3. Document which official features are now supported:
   - channel runtime
   - `trellis mem`
   - refreshed bundled skills
   - migration manifest continuity
4. Document which defaults intentionally differ:
   - Guru fresh projects use official channel supervision by default
   - legacy Codex `sub-agent` remains an explicit rollback mode
5. Document the private release path and registry.

Acceptance:

- Humans can tell the difference between official 0.6.0 behavior, Guru
  additions, and Guru intentional defaults.

### Phase 8: Validation

Minimum validation commands:

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

Targeted validation checks:

```bash
rg "@mindfoldhq/trellis" package.json packages/cli/scripts
rg "function pushTarget|git push origin" packages/cli/scripts/release.js
rg "0.6.0 < 0.6.0-guru.1|Guru overlay" packages/cli/src/utils/compare-versions.ts packages/cli/test/utils/compare-versions.test.ts
find packages/cli/src/templates/common/bundled-skills -maxdepth 1 -type d | sort
find packages/cli/src/templates/guru/overlay -type f | sort
find .agents .claude .cursor .opencode .pi -path "*/skills/trellis-channel" -type d
rg "dispatch_mode: channel|in_progress-channel|in_progress-sub-agent" .trellis/config.yaml guru-template packages/cli/src/templates
python3 .trellis/scripts/get_context.py --mode phase --platform codex | rg "codex-channel|trellis channel"
python3 .trellis/scripts/guru/guru_supervise.py implement .trellis/tasks/<task> --dry-run
python3 .trellis/scripts/guru/guru_supervise.py check .trellis/tasks/<task> --dry-run
rg "run_blocking_task_hooks" packages/cli/src/templates/trellis/scripts
```

Validation interpretation:

- `@mindfoldhq/trellis-core` may remain as a dependency alias key only if packed
  package checks prove it resolves to Guru core.
- `@mindfoldhq/trellis` should not remain in root scripts or Guru private
  release paths.
- Any `No projects matched the filters` output in root script validation is a
  failure.
- `release.js` must not push `origin main --tags` for Guru release types. If the
  implementation intentionally avoids `release.js` for Guru releases, that
  exclusion must be documented and enforced by a clear script failure.
- Guru overlay version ordering is an intentional fork contract, not generic
  SemVer behavior; keep the tests close to `compareVersions`.

## Rollback Plan

| Failure point | Rollback |
|---|---|
| Official GA asset import breaks common templates | Revert Phase 1 files only. |
| Guru behavior regresses | Revert affected merge conflict resolutions; keep official assets isolated. |
| Version/package metadata breaks install | Revert Phase 3 package metadata and lockfile changes. |
| Root scripts fail after selector changes | Revert selectors, then repair with path selectors instead of package selectors. |
| Release preflight misclassifies registry/package | Revert release-script changes; block publish until fixed. |
| Dogfood update overwrites local customizations | Restore local `.trellis`, skills, and hash files from git/diff; do not publish. |
| Packed CLI points at official core | Block release; fix alias/publish metadata; publish only a corrected Guru version. |
| Published package is bad | Do not overwrite; publish the next Guru patch such as `0.6.0-guru.2`. |

## Full Risk Matrix

| Risk category | Evidence | Current behavior | Required plan coverage | Classification |
|---|---|---|---|---|
| Product goal and scope boundary | `task.json` status is `in_progress`; user asked for another full-cycle plan repair | Implementation diff exists, but this request is documentation/plan repair only | Status, PRD, design, and implement docs must say this pass does not edit product code | Covered after this repair |
| Official baseline drift | npm latest currently `0.6.0`; tag `v0.6.0` is local | Upstream target remains stable GA | Re-check npm/tag before final release validation | Covered |
| Official GA asset coverage | `0.6.0.json` and `trellis-channel/**` exist in the worktree | Official GA assets appear imported | Phase 1 keeps presence and dogfood install validation | Covered; verify before completion |
| Common bundled skill distribution | `common/index.ts:85-133` scans directories | New skill requires no registration | Phase 1 relies on directory scan and validates presence | Covered |
| Guru overlay ownership | `guru-template/**`, `sync-guru-template.js:7-22`, `45-88` | Guru SSOT now syncs specs, workflows, and full overlay | Phase 2 validates full overlay packaging and transient exclusions | Covered; targeted test required |
| Guru workflow offline behavior | `workflow-resolver.ts:201-273` | Guru workflows resolve bundled/offline | Phase 2 validates offline resolution | Covered |
| Guru spec offline behavior | `template-fetcher.ts:1205-1232` | Bundled specs install without registry | Phase 2 validates offline install | Covered |
| Hard gate / before_start | `task.py:95-100`, `task_utils.py:264-305` | Non-zero before_start aborts start | Phase 2 and 6 preserve and validate blocking hook | Covered |
| `design-grill` throughput | `design-grill` now contains `Design Grill Packet` | Packet-first mode has been added in source/package surfaces | Phase 2 keeps accepted packet contract and tests packaged overlay | Covered; verify before completion |
| `design-grill` gate integrity | `guru_gate.py` records `guru_gates[gate].grill` with digest | Completion is durable only through `grill-done/skip`, not hook markers or packet text | Phase 2 keeps packet as interaction aid only and preserves `guru_gate.py` completion semantics | Covered |
| User AGENTS preservation | `update.ts:157-182` | Managed block replacement preserves surrounding content | Phase 6 validates no clobber | Covered |
| User settings preservation | `claude.ts:65-88`, `shared.ts:763-800` | Existing JSON wins; template fills gaps | Phase 6 validates no clobber | Covered |
| Package identity | `packages/cli/package.json:2-15`, `packages/core/package.json:2-43` | CLI/core are now `@devsc/*@0.6.0-guru.1` | Phase 3 keeps fork identity and release preflight checks exact version match | Covered |
| Root script false green | `package.json:6-21` uses `@devsc` filters with `--fail-if-no-match` | Original root no-op blocker appears repaired in worktree | Phase 4 still validates selectors by running root commands | Covered; verify before completion |
| Release registry assumptions | `release-preflight.js:66-99`, `110-115` | Preflight reads package registries and uses `guru` tag | Phase 5 keeps registry-aware preflight | Covered; verify before publish |
| Packed dependency alias | `release-preflight.js:25-31`, `70-99` | Fork alias shape is accepted | Phase 5 runs `verify-packed-cli` before release | Covered; verify before publish |
| Manifest continuity mode | `check-manifest-continuity.js:20-24`, `98-101` | Default fork mode maps `0.6.0-guru.N` to `0.6.0.json`; `--official` checks upstream | Phase 5 keeps both modes explicit | Covered; verify before publish |
| Release push target | `release.js:86-130`, `test/scripts/release.test.ts` | Guru non-prerelease releases now push the current `guru/*` branch or fail before pushing tags | Phase 5 keeps this guarded and tests it | Covered |
| Guru version ordering semantics | `compare-versions.ts:43-53`, test lines `145-159` | Guru overlays sort after upstream GA to allow update-chain movement into Guru packages | Phase 3/8 document and test this intentional SemVer deviation | Should-fix before claiming release readiness |
| Dogfood version line | `.trellis/.version` is `0.6.0-guru.1` | Runtime/dogfood version identity is now aligned | Phase 6 validates no drift | Covered; verify before completion |
| Codex dispatch default | `.trellis/config.yaml:70-71` still shows an existing sub-agent value in this worktree | Existing external project values are preserved, but this migration dogfood worktree must be explicitly switched to channel after support lands | `official-supervision-default-plan.md` supersedes old dogfood-default wording; Phase 6 must not overwrite arbitrary existing projects silently | Covered |
| Installed skill completeness | `.template-hashes.json` includes `trellis-channel` across local surfaces | Dogfood skill refresh appears present | Phase 6 validates installed dirs and hashes | Covered; verify before completion |
| `trellis-meta` refresh blast radius | Large deletion/replacement set under local and bundled `trellis-meta` dirs | Official refresh appears to replace old reference layout with local-architecture docs | Phase 6 requires explicit diff/hash audit so user-owned content is not lost | Should-fix before completion |
| Tests | Guru bundled and compare-version tests include new coverage | Existing focused tests cover overlay files and version ordering | Phase 8 runs package/root/guru/overlay/release checks | Covered |
| Unsupported variants | No tracker issue or external docs sync requested | Plan is local repo only | Tracker sync excluded unless user requests it | Accepted MVP boundary |
| GitNexus absence | GitNexus tools unavailable in this session | Cannot use impact graph for code symbols | Plan records fallback evidence; this repair pass does not edit code symbols | Accepted planning limitation |
| Dirty worktree | Large implementation diff plus pre-existing `.codex/config.toml`, `.agents/skills/gitnexus/` | Many files were already dirty before this repair pass | Final checks must report docs changed and leave unrelated files untouched | Covered |

## Full-Cycle Review Iteration 1

Iterations 1-6 below are historical review records from the original
planning-first state. Their approval/start-gate wording is superseded by
Iteration 7 after the task moved to `in_progress`.

Reviewer stance: find blocker/should-fix risks in this plan before
implementation.

### Findings

1. Blocker: root script false-green risk must be implementation-blocking, not a
   validation footnote.
   - Evidence: root `package.json:6-19` targets `@mindfoldhq/...` while package
     files are `@devsc/...`.
   - Impact: migration can look green while not running core/CLI checks.
   - Repair: Phase 4 makes selector repair a dedicated phase and marks no-op
     output as failure.
   - Status: repaired in this plan.

2. Blocker: release/preflight public npm assumptions can make a private Guru
   release unsafe.
   - Evidence: `release-preflight.js:89-110` and `268-292` query public npm;
     packages publish to GitHub Packages per package JSON.
   - Impact: publish-plan and verify-npm can check the wrong registry.
   - Repair: Phase 5 requires registry-aware preflight and explicit
     official-vs-Guru modes.
   - Status: repaired in this plan.

3. Should-fix: packed CLI alias behavior must be verified, not assumed.
   - Evidence: `release-preflight.js:225-262` expects exact official dependency
     shape, while CLI uses a workspace alias at `packages/cli/package.json:56-58`.
   - Impact: package may publish with wrong or unverifiable core dependency.
   - Repair: Phase 5 adds alias-aware packed verification and blocks release if
     it points to official core.
   - Status: repaired in this plan.

4. Should-fix: dogfood skill refresh is required to claim official feature
   coverage.
   - Evidence: live installed skills do not include `trellis-channel`; current
     common bundled skills also lack it.
   - Impact: source may contain official skill, but current repo users do not
     receive it.
   - Repair: Phase 6 refreshes installed skills and hashes.
   - Status: repaired in this plan.

5. Nice-to-have: split this plan into Trellis `design.md` and `implement.md`
   later.
   - Evidence: complex Trellis tasks often use split design/implement
     artifacts; this user explicitly requested one Markdown plan artifact first.
   - Impact: current user asked for one MD document; splitting now would violate
     the requested artifact shape.
   - Repair: keep this single document now; PRD now names `migration-plan.md`
     as the current plan-first review artifact and defers any split until
     implementation is approved or a Trellis gate requires it.
   - Status: accepted boundary.

6. Should-fix: PRD and plan artifact shape must agree.
   - Evidence: the original PRD acceptance criteria named `design.md` and
     `implement.md`, while the user requested a single Markdown plan document.
   - Impact: planning could appear incomplete even after the requested plan doc
     is reviewed.
   - Repair: PRD was updated to make `migration-plan.md` the current reviewed
     plan artifact and to preserve a later split only as an implementation-gate
     step.
   - Status: repaired.

## Full-Cycle Self-Review Iteration 2

Checklist re-run against the matrix above:

- Product goal and scope: covered for the original planning-first pass;
  superseded by Iteration 7 after the task moved to `in_progress`.
- Official baseline: covered; implementation must re-check npm/tag.
- Official feature coverage: covered; manifest, `trellis-channel`, and
  `trellis-meta` are explicit Phase 1 inputs.
- Guru behavior preservation: covered; workflow/spec/offline/gate/merge
  contracts are explicit Phase 2/6 gates.
- Version/package/release: covered with blockers on root scripts and registry
  preflight before publish.
- Dogfood: covered; `.trellis/.version`, installed skills, hashes, and
  `sub-agent` preservation are explicit.
- Tests and manual QA: covered by Phase 8.
- Local PRD consistency: covered; PRD now treats `migration-plan.md` as the
  current reviewed artifact and defers split design/implement files until later.
- Tracker sync: accepted out of scope because none was requested or linked.
- Unrelated dirty files: covered by Phase 0 and final status checks.

Result:

- Remaining blockers in the plan: none.
- Remaining should-fix gaps in the plan: none.
- Nice-to-have / accepted boundaries:
  - convert this single MD into separate `design.md` / `implement.md` later if
    Trellis phase start requires those artifacts;
  - GitNexus remains unavailable for this planning pass;
  - no tracker issue sync is planned unless the user requests it.

## Full-Cycle Review Iteration 3

Trigger: user confirmed `0.6.0-guru.1` as the target Guru GA migration version
and requested another `full-cycle-plan-repair` pass.

### Findings

1. Should-fix: version decision was still recorded as pending.
   - Evidence: previous plan status said `proposed 0.6.0-guru.1`, and the final
     section was `User Decision Still Needed`.
   - Impact: implementers could pause for a decision that the user has already
     made, or accidentally choose another Guru version line.
   - Repair: plan status, PRD confirmed facts, risk matrix, and this review
     record now treat `0.6.0-guru.1` as accepted.
   - Status: repaired.

2. Should-fix: official npm baseline should be rechecked after the date changed.
   - Evidence: official release state is externally mutable; the current date is
     2026-06-16.
   - Impact: if `latest` moved past `0.6.0`, the migration target would need an
     explicit scope freeze.
   - Repair: `npm view @mindfoldhq/trellis` and
     `npm view @mindfoldhq/trellis-core` were re-run on 2026-06-16; both still
     report `latest = 0.6.0`.
   - Status: repaired.

3. Should-fix: sub-agent manifests were still placeholder examples.
   - Evidence: `implement.jsonl` and `check.jsonl` contained only `_example`
     entries.
   - Impact: when implementation/check sub-agents are dispatched later, they
     would not automatically receive the PRD and migration plan context.
   - Repair: both JSONL files now point to the PRD and this migration plan as
     spec/research inputs, with no product-code paths.
   - Status: repaired.

## Full-Cycle Self-Review Iteration 4

Checklist re-run after Iteration 3 repairs:

- Product goal and scope: covered for the original planning-first pass;
  superseded by Iteration 7 after the task moved to `in_progress`.
- Target version: covered; `0.6.0-guru.1` is accepted, not pending.
- Official baseline: covered; npm latest for CLI/core rechecked on 2026-06-16
  and remains `0.6.0`.
- PRD/plan consistency: covered; PRD confirmed facts include the accepted target
  and fresh npm recheck.
- Sub-agent readiness: covered; `implement.jsonl` and `check.jsonl` now contain
  real spec/research manifest entries.
- Previous blockers: root script false-green and release registry assumptions
  remain explicit implementation blockers and are not closed by planning alone.
- Previous should-fix items: packed alias verification, manifest continuity mode,
  dogfood skill refresh, and PRD artifact alignment all remain represented in
  phases, validation, and risk matrix.
- Tracker sync: accepted out of scope because no tracker issue/PR is linked or
  requested.
- Unrelated dirty files: still out of scope; `.codex/config.toml` and
  `.agents/skills/gitnexus/` must remain untouched.

Result:

- Remaining blockers in the plan: none.
- Remaining should-fix gaps in the plan: none.
- Accepted boundaries:
  - the original no-product-code boundary is superseded by the current
    implementation-in-progress state, but remains relevant to documentation-only
    repair turns;
  - split `design.md` / `implement.md` was later completed and is now maintained
    alongside this plan;
  - no tracker sync unless requested;
  - GitNexus remains unavailable for this planning pass.

## Full-Cycle Review Iteration 5

Trigger: user accepted the `design-grill` packet-first batch interaction
proposal.

### Findings

1. Should-fix: the accepted interaction change must be represented as a Guru
   migration scope item, not left only in chat.
   - Evidence: current `design-grill` skill still requires one question per
     turn, while the user accepted packet-first batch discovery.
   - Impact: implementation could migrate official `0.6.0` assets but leave the
     biggest day-to-day `design-grill` usability issue unchanged.
   - Repair: PRD confirmed facts, acceptance criteria, target state, strategy
     matrix, Phase 2, and risk matrix now include the packet-first contract.
   - Status: repaired.

2. Should-fix: packet-first mode must not weaken hard Gate semantics.
   - Evidence: `guru_gate.py` currently treats only `guru_gates[gate].grill`
     with matching digest as completion, while hook marker files are merely
     reminders.
   - Impact: if future implementation treats a packet as completion evidence,
     users could bypass `grill-done/skip` and digest invalidation.
   - Repair: the plan states that packet output is only an interaction aid;
     `guru_gate.py grill-done/skip` remains the only durable completion/skip
     record.
   - Status: repaired.

3. Should-fix: batch mode must preserve sequential handling for high-impact
   decisions.
   - Evidence: the current one-question contract protects dependency-ordered
     decisions and redline fail behavior.
   - Impact: a naive bulk questionnaire could mix independent polish items with
     blocker/redline decisions and let users approve contradictory choices.
   - Repair: the accepted contract permits bulk approval only for independent
     low-risk items; blocker, redline, and dependency-setting items remain on a
     one-by-one confirmation path.
   - Status: repaired.

## Full-Cycle Self-Review Iteration 6

Checklist re-run after Iteration 5 repairs:

- Product goal and scope: covered for the original planning-first pass;
  superseded by Iteration 7 after the task moved to `in_progress`.
- Target version: covered; `0.6.0-guru.1` remains the accepted version line.
- `design-grill` usability: covered; packet-first batch discovery is now an
  explicit migration requirement.
- `design-grill` safety: covered; redline fail, dependency ordering,
  evidence-first lookup, and `guru_gate.py grill-done/skip` completion
  semantics remain required.
- Sub-agent readiness: needs manifest update so implementation/check agents
  see the relevant `design-grill`, workflow, gate, and test files.

Result:

- Remaining blockers in the plan: none.
- Remaining should-fix gaps in the plan: none after manifest update.

## Full-Cycle Review Iteration 7

Trigger: user requested another `full-cycle-plan-repair` pass after the task had
moved to `in_progress` and the live checkout contained implementation changes.

### Findings

1. Blocker: plan artifacts still described the task as planning-only even though
   live task state is `in_progress`.
   - Evidence: `task.json` reports `status = in_progress`, while the previous
     plan status and split artifacts still said implementation was not approved
     and `task.py start` had not run.
   - Impact: later implement/check agents could follow stale gates, or reviewers
     could miss that the codebase now needs implementation-progress validation.
   - Repair: PRD, migration plan, `design.md`, and `implement.md` now treat this
     pass as documentation-only review of an implementation-in-progress checkout.
   - Status: repaired in plan artifacts.

2. Blocker: Guru release orchestration could still push the wrong branch.
   - Evidence: `packages/cli/scripts/release.js:86-113` returns `main` from
     `pushTarget(type)` for non-beta/non-rc releases and runs
     `git push origin ${pushTarget(type)} --tags`.
   - Impact: a Guru `patch`, `minor`, `major`, or `promote` release from
     `guru/main` could push `origin main --tags`, which contradicts the Guru
     release path and is unsafe for the fork.
   - Repair: Phase 5, validation, PRD acceptance criteria, design risks, and
     implement checklist were updated first. This implementation pass then
     changed `pushTarget` so Guru non-prerelease releases require a `guru/*`
     branch and added focused regression tests.
   - Status: repaired in plan artifacts and code.

3. Should-fix: Guru overlay version ordering is an intentional SemVer deviation
   and must not stay implicit.
   - Evidence: `compareVersions` now treats `0.6.0-guru.1` as newer than
     `0.6.0`, with focused tests covering GA/RC comparisons.
   - Impact: maintainers might later "simplify" the comparator back to generic
     SemVer behavior and break update/migration movement into Guru packages.
   - Repair: Phase 3, Phase 8, PRD acceptance, and design compatibility now
     document and test this as a Guru update-contract rule.
   - Status: repaired in plan artifacts.

4. Should-fix: full Guru overlay bundling was implemented but not fully
   represented in the migration plan.
   - Evidence: `sync-guru-template.js` now copies `guru-template/overlay/` and
     tests verify packaged overlay files plus transient-artifact exclusion.
   - Impact: future reviewers could validate only specs/workflows and miss the
     gate/skill/hook files required for offline Guru installs.
   - Repair: Phase 2, validation, risk matrix, PRD acceptance, and implement
     checklist now include full overlay packaging.
   - Status: repaired in plan artifacts.

5. Should-fix: the large `trellis-meta` refresh/deletion set needs explicit
   completion audit.
   - Evidence: `git status --short` shows many deleted old `trellis-meta`
     reference files and new `local-architecture` replacements across bundled
     and local skill surfaces.
   - Impact: the migration could accidentally remove user-meaningful guidance
     while updating official common skills.
   - Repair: Phase 6 and the risk matrix now require a diff/hash audit before
     completion.
   - Status: repaired in plan artifacts; implementation audit still required.

## Full-Cycle Self-Review Iteration 8

Checklist re-run after Iteration 7 repairs:

- Product goal and request boundary: covered. This pass is now explicitly
  documentation-only even though implementation has started.
- Official baseline: covered. The plan keeps `0.6.0-guru.1` anchored on
  official `v0.6.0` GA and keeps npm/tag recheck in the validation path.
- Current implementation snapshot: covered. Package identity, root scripts,
  official assets, dogfood version, overlay bundling, version comparator,
  release preflight, and manifest continuity are now represented with live
  evidence.
- Guru behavior preservation: covered. The packet-first `design-grill` contract,
  `guru_gate.py` completion semantics, before-start hooks, offline specs,
  offline workflows, and full overlay packaging all remain explicit.
- Release safety: covered. `release.js` push target behavior for Guru
  non-prerelease releases is now guarded by code and focused tests.
- Validation: covered. Focused checks now include `compareVersions`,
  `guru-bundled`, `release.js` push-target inspection, full overlay listing,
  release preflight, and root no-op protection.
- Tracker sync: accepted out of scope because no tracker issue/PR is linked or
  requested.
- Unrelated dirty files: accepted risk. The worktree is already very dirty; this
  repair pass edits only task planning artifacts.

Result:

- Remaining blockers in the plan: none.
- Remaining should-fix gaps in the plan: none.
- Remaining implementation blockers before Guru release readiness: none known
  from this full-cycle pass.
- Remaining implementation should-fix before completion:
  - run focused Guru overlay/version tests;
  - audit `trellis-meta` refresh/deletion blast radius;
  - verify full overlay packaging and transient-artifact exclusion;
  - run release preflight and packed alias validation.

## Implementation Adjustment - Release Push Target

Trigger: user requested adjustment after the full-cycle plan identified
`release.js` push targeting as the remaining release-readiness blocker.

Changes:

- `packages/cli/scripts/release.js` now exports a pure `pushTarget` function for
  focused testing.
- Official package releases keep previous behavior:
  - `patch`, `minor`, `major`, and `promote` push `main`;
  - `beta` and `rc` push `HEAD`.
- Guru package releases now refuse unsafe stable/promote pushes:
  - `beta` and `rc` still push `HEAD`;
  - `patch`, `minor`, `major`, and `promote` require the current branch to start
    with `guru/`;
  - if the current branch is unknown, not `guru/*`, or contains unsupported
    characters, the script fails before tests, commits, tags, or `git push`.
- Added `packages/cli/test/scripts/release.test.ts` to cover the above matrix.

Validation:

- Passed: `pnpm --filter @devsc/trellis exec vitest run test/scripts/release.test.ts`
- Passed: `pnpm --filter @devsc/trellis exec vitest run test/scripts/bump-versions.test.ts`
- Partial / unrelated failure: the mistakenly broad command
  `pnpm --filter @devsc/trellis test -- test/scripts/release.test.ts` ran most
  of the suite and failed on pre-existing long-running tests:
  - `test/utils/template-fetcher.test.ts` Git-backed registry timeout cases;
  - `test/regression.test.ts` `session_auto_commit` string-variant timeout.

## Implementation Adjustment - Packaged Overlay Workflow Resolver

Trigger: the required simulated-project install used the built package artifact
and failed when running:

```bash
bash packages/cli/dist/templates/guru/overlay/apply.sh <smoke-project> flutter
```

Root cause:

- Source Guru workflows live as
  `guru-template/workflows/<id>-workflow.md`.
- `sync-guru-template.js` intentionally normalizes packaged workflow filenames
  to `packages/cli/src/templates/guru/workflows/<id>.md`.
- `apply.sh` was copied into the packaged overlay unchanged and still looked
  only for `workflows/<id>-workflow.md`, so packaged installs could not copy the
  Guru workflow into `.trellis/workflow.md`.

Repair:

- `guru-template/overlay/apply.sh` now resolves `workflows/<id>.md` first and
  falls back to `workflows/<id>-workflow.md`.
- `pnpm -C packages/cli sync:guru` propagates the same fix into
  `packages/cli/src/templates/guru/overlay/apply.sh`.
- `packages/cli/test/guru/guru-bundled.test.ts` now asserts the packaged
  workflow filenames exist and are resolvable by `apply.sh`.

Validation:

- Passed: `bash guru-template/overlay/tests/apply_test.sh` → 49/0.
- Passed: `bash packages/cli/src/templates/guru/overlay/tests/apply_test.sh` →
  49/0, covering the packaged source layout.
- Passed: `pnpm --filter @devsc/trellis exec vitest run test/guru/guru-bundled.test.ts`
  → 20/20.
- Passed: built `dist`, ran packaged `apply.sh` against a fresh simulated
  Flutter-shaped project, then verified:
  - `trellis init --workflow guru-client --claude --codex`;
  - Guru overlay skill/spec/hook install;
  - first `task.py start` blocked by `before_start`;
  - `grill-done` + soft `confirm` wrote durable Gate state;
  - `guru_gate.py check` passed;
  - second `task.py start` advanced the smoke task to `in_progress`;
  - `trellis update --dry-run` completed without making changes.
