# Design - Guru Migration to Trellis 0.6.0 GA

## Purpose

This design translates `migration-plan.md` into the standard Trellis technical
design artifact for the accepted Guru target line `0.6.0-guru.1`. The task is
now `in_progress` and the live checkout already contains implementation changes.
This full-cycle repair pass is documentation-only: it audits the design against
the live worktree and does not modify product source code.

## Architecture

The migration has three ownership layers:

| Layer | Owner | Migration intent |
|---|---|---|
| Official GA common layer | Official Trellis `v0.6.0` | Adopt the GA migration manifest, `trellis-channel`, refreshed `trellis-meta`, and applicable configurator tests. |
| Guru overlay layer | Guru fork | Preserve Guru workflow/spec/overlay/gate behavior, including offline Guru workflow/spec distribution and `before_start` hard gates. |
| Fork release and dogfood layer | Guru fork | Rework package identity, root scripts, release preflight, private registry assumptions, local installed bundled skills, and dogfood version state. |

The common layer should stay as close as possible to official `v0.6.0`. Guru
behavior belongs in `guru-template/**`, `packages/cli/src/templates/guru/**`,
Guru sync scripts, and fork-specific release/dogfood logic. Official common
skills should not carry Guru-only workflow rules.

## Boundaries

Preserve these Guru surfaces:

- `guru-template/**`
- `packages/cli/src/templates/guru/**`
- `packages/cli/scripts/sync-guru-template.js`
- Guru workflow resolver and template fetcher additions
- Guru `before_start` hook support in Trellis task scripts
- AGENTS managed-block merge semantics
- Claude settings/defaults merge semantics
- legacy `codex.dispatch_mode: sub-agent` as an explicit rollback mode, not as
  the fresh Guru default

Adopt these official `0.6.0` surfaces:

- `packages/cli/src/migrations/manifests/0.6.0.json`
- `packages/cli/src/templates/common/bundled-skills/trellis-channel/**`
- refreshed `packages/cli/src/templates/common/bundled-skills/trellis-meta/**`
- applicable official configurator test deltas

Rework these fork surfaces:

- package versions to `0.6.0-guru.1`
- stale root package filters that still target `@mindfoldhq/...`
- release/preflight registry assumptions so Guru validation checks GitHub
  Packages and `@devsc/...` package names where appropriate
- packed CLI dependency verification so workspace aliases cannot silently point
  at official core packages
- `release.js` push targeting now guarded so Guru `patch`, `minor`, `major`,
  and `promote` releases require a `guru/*` current branch and cannot push
  `origin main --tags`
- Guru overlay version comparison so `0.6.0-guru.1` is treated as newer than
  upstream `0.6.0` for update/migration gates
- dogfood `.trellis/.version`, installed bundled skills, and template hashes
- full Guru overlay packaging from `guru-template/overlay/` into the packaged
  Guru template, excluding transient cache files
- `design-grill` interaction contract, per the accepted packet-first mode

Drop upstream release-task artifacts. They are planning history, not runtime or
package inputs.

## `design-grill` Packet-First Contract

The accepted `design-grill` change is an interaction contract change, not a
gate semantics change.

Current problem: the skill requires one question per turn, which preserves
decision ordering but is slow for mature PRD/design artifacts.

Target behavior:

1. `design-grill` first performs evidence-first lookup across spec, task
   artifacts, context docs, ADRs, and target code.
2. It emits a bounded `Design Grill Packet`, defaulting to no more than eight
   candidate items.
3. Each packet item includes:
   - ID
   - artifact anchor, such as `BHV-003`, a table row, a chapter, or a code path
   - risk level: `BLOCKER`, `HIGH`, or `NORMAL`
   - question or challenge
   - recommended answer
   - evidence
   - proposed write-back target
   - dependency status
4. Independent `NORMAL` items can be bulk-approved by the user.
5. `BLOCKER`, redline, compliance, and dependency-setting decisions still
   require sequential confirmation.
6. Redline fail behavior remains unchanged: a hard redline stops that branch
   and identifies the upstream artifact that must be repaired.
7. Packet text is not a completion credential. Durable completion remains only
   `guru_gate.py grill-done <gate> <task_dir>` or explicit skip via
   `guru_gate.py grill-skip <gate> <task_dir> --user-quote "<reason>"`.

This preserves the original safety property while reducing low-risk
question-answer round trips.

## Data And Control Flow

### Official GA Asset Flow

1. Import official GA assets from `v0.6.0`.
2. Let common bundled skill discovery pick up new directories through existing
   directory scanning.
3. Keep official common skills independent from Guru overlay behavior.
4. Validate common bundled skills are present in source and dogfood installs.

### Guru Overlay Flow

1. Treat `guru-template/**` as the source of truth.
2. After any Guru template edit, run `pnpm -C packages/cli sync:guru`.
3. Verify packaged Guru templates match the source template.
4. Verify the full `guru-template/overlay/` tree is bundled into
   `packages/cli/src/templates/guru/overlay/`, including `design-grill`,
   `apply.sh`, `guru_gate.py`, and `grill-nudge.sh`.
5. Verify transient overlay artifacts such as `__pycache__`, `.pyc`, and `.pyo`
   are not bundled.
6. Validate offline Guru workflows and specs still resolve without network.
7. Validate `before_start` hooks still block unconfirmed implementation starts.

### Release Flow

1. Update package metadata to `@devsc/*@0.6.0-guru.1`.
2. Repair root package filters before trusting root build/test commands.
3. Make release preflight registry-aware.
4. Verify packed CLI dependency metadata before publish.
5. Block release if packed CLI resolves to official core unexpectedly.
6. Keep the `release.js` push-target guard: Guru releases must push the current
   `guru/*` branch safely or fail with a clear error before `git push`.

### Dogfood Flow

1. Refresh the local Trellis dogfood state only after source/package changes are
   coherent.
2. Preserve user-owned local config and hooks.
3. Install official bundled skills, including `trellis-channel`, across local
   supported skill surfaces.
4. Move Guru default dispatch to official `trellis channel` supervision for
   fresh Guru projects.
5. Preserve legacy `sub-agent` and `inline` dispatch only as explicit rollback
   modes and existing-project choices that `apply.sh` must not silently
   overwrite.
6. Treat this migration worktree as a dogfood target: after channel routing and
   installed hooks are updated, explicitly switch its `.trellis/config.yaml` to
   `codex.dispatch_mode: channel` and validate the local hook/context output.

### Official Supervision Default Flow

The follow-up supervision plan is now part of the migration scope. Its
implementation must use official `trellis channel` runtime primitives rather
than forking supervisor internals.

1. Add `channel` as a first-class Codex dispatch mode in workflow-state and
   phase-detail routing.
2. Make Guru workflow ordinary `planning` and `in_progress` blocks represent
   the channel default.
3. Move legacy sub-agent wording to `planning-sub-agent` and
   `in_progress-sub-agent` blocks.
4. Inject platform-specific Guru implementation/review skills into official
   channel workers so generic `implement` / `check` agent cards do not lose
   Guru domain context.
5. Install `guru_supervise.py` or equivalent P0 wrapper from the Guru overlay
   so the default channel path is executable, dry-run verifiable, and not only
   workflow prose.
6. Repair `trellis-channel` bundled-skill reference drift where installed or
   packaged docs still show executable `--tag` examples even though the
   current command reference says the v0.6.0 CLI has no `--tag` flag.
7. Install an idempotent config patcher from the Guru overlay so fresh projects
   get `codex.dispatch_mode: channel`, `channel.worker_guard` defaults, and
   `guru.supervision` defaults without overwriting existing user choices.
   `channel.worker_guard` and `guru.supervision` must both merge by child key:
   preserve existing values and add only missing defaults.
8. Build channel spawn context from existing files only, including optional
   `implement.jsonl` / `check.jsonl`; missing manifests must not be passed to
   `trellis channel spawn`.
9. Keep workflow and smoke command examples copy-paste safe: each standalone
   block declares `TASK`, derives `CHANNEL` / worker names from `RUN_ID`, and
   avoids fixed smoke channel names.
10. Keep helper control commands exact: `status` must surface channel / worker
   handles, and `kill` must require those exact values instead of fixed worker
   prefixes.

## Compatibility

Official `0.6.0` is a stable promotion of `0.6.0-rc.0`, so runtime risk is
concentrated in release assets, bundled skills, package identity, and local
dogfood state rather than new core runtime code.

Compatibility constraints:

- Official update-chain continuity requires the `0.6.0.json` manifest.
- Guru private package continuity requires fork-aware release checks.
- Root scripts must fail if package selectors match no projects.
- Installed local skills must include both official common skills and Guru
  project-specific skills.
- `design-grill` packet-first mode must remain compatible with current
  `guru_gate.py` `confirm`, `check`, and `auto` behavior.
- Guru overlay versions intentionally sort after the matching upstream GA in
  `compareVersions`. This is a fork update-contract rule, not generic SemVer
  prerelease behavior.
- Official supervision support must preserve Guru Gate order: channel workers
  may run implementation/check work only after `guru_gate.py check` permits
  the task to start.
- Official channel agent cards are generic; Guru domain skill injection is a
  compatibility requirement, not optional documentation.

## Parent / Child Task Decision

This migration contains multiple independently verifiable deliverables, and the
current task is already `in_progress`. Do not create child tasks during this
documentation-only repair pass. If the remaining implementation/check work is
too large for one execution pass, split into children before dispatching more
implementation or check work:

- official GA asset import
- Guru overlay preservation and `design-grill` packet-first contract
- package identity and release/preflight repair
- dogfood update and validation

Any split child must restate its dependency ordering in that child's `prd.md`
and `implement.md`; tree position alone must not imply dependencies.

## Rollout And Rollback

Rollout should proceed in ordered phases:

1. branch and guardrails
2. official GA assets
3. Guru overlay preservation and `design-grill` contract update
4. version and package identity
5. root script repair
6. release/preflight repair
7. dogfood update
8. documentation
9. validation

Rollback should be phase-scoped. Revert only the phase that introduced the
failure unless packed/published artifacts have already escaped. If a bad Guru
package is published, do not overwrite it; publish a corrected patch such as
`0.6.0-guru.2`.

## Risks

| Risk | Mitigation |
|---|---|
| Root scripts appear green but run no packages | Repair selectors first and treat "No projects matched" as failure. |
| Release preflight checks public npm instead of GitHub Packages | Make preflight registry-aware and split official/Guru continuity modes. |
| Packed CLI points at official core | Add alias-aware packed verification and block release on mismatch. |
| `release.js` pushes `origin main --tags` for Guru non-prerelease releases | Covered by `pushTarget`: Guru non-prerelease releases require a `guru/*` current branch and fail otherwise. |
| Guru overlay version ordering is mistaken for normal SemVer | Document and test `0.6.0 < 0.6.0-guru.1` as a Guru update-contract rule. |
| Full Guru overlay packaging is only partially validated | Verify packaged overlay files and transient-artifact exclusion with focused tests. |
| Official skill import overwrites Guru behavior | Keep official common skills and Guru overlay surfaces separate. |
| Dogfood update removes local user customizations | Preserve merge semantics and inspect local skill/config diff before completion. |
| Packet-first `design-grill` weakens gate discipline | Keep packet as an interaction aid only; preserve `guru_gate.py` digest-backed completion. |
| Guru defaults drift between `sub-agent` and official channel supervision | Treat `official-supervision-default-plan.md` as the superseding plan; keep `sub-agent` only as explicit rollback. |
| Channel workers lose Guru implementation/review context | Inject the platform-specific Guru skill file into each official channel worker run. |
| `guru_supervise.py` is treated as optional despite being required for stable default supervision | Keep the wrapper, packaged copy, and helper dry-run tests in P0. |
| Current dogfood checkout never exercises channel default | Explicitly switch this migration worktree to `codex.dispatch_mode: channel` after routing support lands and run dogfood self-proof. |
| Missing jsonl manifests produce false context injection | Helper adds `--jsonl` only when the manifest exists. |
| Smoke or workflow examples collide across runs | Require standalone `TASK` declarations and run-id channel / worker names in every copied command block. |
| Helper kill cannot target run-id workers | `status` prints exact handles; `kill` requires exact channel + worker and maps to official `trellis channel kill <channel> --as <worker>`. |
| Partial `guru.supervision` config remains incomplete | Config patcher fills missing child keys without overwriting existing provider or timeout values. |
| Bundled `trellis-channel` references still show stale `--tag` command examples | Repair packaged and installed skill docs, then grep for executable `trellis channel ... --tag` examples while allowing no-tag warning prose. |
| GitNexus index is stale | Do not rely on stale graph evidence; use local source inspection unless GitNexus is refreshed. |

## Open Decisions

No product/scope decision currently blocks the migration plan.

No product/scope decision currently blocks the migration plan. No release
push-target implementation blocker remains from this pass.
