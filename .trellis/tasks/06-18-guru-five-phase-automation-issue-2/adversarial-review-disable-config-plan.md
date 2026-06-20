# Adversarial Review Disable Config Plan

## Goal

Add one project-level switch that lets an installed Guru project disable adversarial review even when workflow text or a user command passes `--adversarial`.

```yaml
guru:
  supervision:
    adversarial_enabled: false
```

## Contract

- Default is enabled. Missing config must preserve current behavior.
- The switch only affects runs that pass `--adversarial`; normal `requirements`, `overview`, `detail`, `implement`, `check`, and `implement-check` behavior must not change.
- When `--adversarial` is passed and `adversarial_enabled: false`, the supervisor must not call `trellis channel create`, `spawn`, `send`, `wait`, or `messages`.
- Disabled requirements adversarial review records the existing advisory state:
  - `task.json.guru_gates.adversarial_skips[]`
  - `task.json.guru_gates.requirements_review.status = "deferred"`
  - reason: `disabled by guru.supervision.adversarial_enabled=false`
- Do not add a new `disabled` status. `deferred` already means no clean/current adversarial review exists, and `confirm requirements` already treats it as a warning rather than a hard block.
- `guru_config_patch.py ensure-supervision-defaults` must add `adversarial_enabled: true` for new installs and preserve explicit `false`.

## Non-Goals

- No per-phase switch.
- No provider-specific switch.
- No scheduler or timeout policy change.
- No change to `guru_gate.py confirm requirements`; it remains warning-only when adversarial evidence is missing or deferred.

## Impact Notes

GitNexus impact before edits:

- `SupervisionConfig`: LOW, no indexed upstream callers.
- `_load_config`: HIGH because it is shared by `run_action`, `run_implement_check`, `status_action`, and `kill_action`.
- `run_action`: LOW.
- `_execute_plan`: LOW.
- `_skip_adversarial`: LOW.
- `patch_config_text` / `_ensure_scalar`: LOW.

The HIGH item is handled by making the new field read-only, defaulting it to `true`, and only checking it in the `--adversarial` execution path.

## Self-Review Loop

Pass 1 findings:

- Blocker: none.
- Should-fix: ensure disabled mode proves no fake trellis command ran. Add a fake trellis that fails if invoked.
- Should-fix: ensure default patch adds the new field and preserves explicit `false`.
- Nice-to-have: dry-run could display disabled behavior, but not required for MVP because dry-run is non-executing preview and current workflow needs runtime shortening.

Pass 2 after repair:

- Blocker: none.
- Should-fix: none before implementation.
- Accepted MVP boundary: dry-run continues to show the command plan. Runtime execution is the path that saves task time.

## Implementation Review Loop

Implemented files:

- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/guru_config_patch.py`
- synced packaged copies under `packages/cli/src/templates/guru/overlay/verify/`
- `packages/cli/test/guru/guru-bundled.test.ts`

Pass 1 findings after implementation:

- Blocker: none.
- Should-fix: lint rejected `Array<Record<string, string>>` in the new tests. Repaired to `Record<string, string>[]`.
- Should-fix: first Python `py_compile` verification created `__pycache__` under source and packaged overlays. Removed the cache directories and switched the syntax check to `compile(...)` with `PYTHONDONTWRITEBYTECODE=1`.

Pass 2 after repair:

- Blocker: none.
- Should-fix: none.
- Verification covers default-enabled behavior, explicit `false` preservation, runtime short-circuit before any trellis channel command, skip persistence, requirements-review `deferred` state, template sync, lint, typecheck, build, and install into `guru_ai_himora`.

Accepted residual risk:

- GitNexus reports critical whole-diff risk because `_load_config` is a shared entrypoint. The implemented branch is constrained to `config.adversarial and not config.adversarial_enabled`, so non-adversarial `status`, `kill`, `implement-check`, and normal supervision keep their existing path.

## Verification Evidence (2026-06-21)

- GitNexus index refreshed successfully after the prior index was stale.
- Impact analysis:
  - `patch_config_text`: LOW, 1 impacted symbol, 0 affected processes.
  - `_set_scalar`: LOW, 2 impacted symbols, 0 affected processes.
  - `_config_bool`: HIGH, affects `run_implement_check`, `run_action`, `status_action`, and `kill_action`.
  - `_load_config`: HIGH, affects the same shared supervisor entrypoints.
  - `run_action`: LOW, 0 affected processes.
  - `applyGuruOverlay`: LOW, 0 affected processes.
- Validation passed:
  - `git diff --check`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile guru-template/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_config_patch.py packages/cli/src/templates/guru/overlay/verify/guru_supervise.py packages/cli/src/templates/guru/overlay/verify/guru_config_patch.py`
  - `PYTHONDONTWRITEBYTECODE=1 bash guru-template/overlay/verify/tests/run_tests.sh` (`143 passed / 0 failed`)
  - `pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts` (`54 passed / 0 failed`)
  - `pnpm -C packages/cli lint`
  - `pnpm -C packages/cli typecheck`
  - `pnpm -C packages/cli build`
  - `PYTHONDONTWRITEBYTECODE=1 bash packages/cli/dist/templates/guru/overlay/verify/tests/run_tests.sh` (`143 passed / 0 failed`)
  - no `__pycache__` directories under `guru-template`, `packages/cli/src/templates/guru`, or `packages/cli/dist/templates/guru`
- `npx gitnexus detect-changes --scope all --repo Trellis` reports `31 files / 80 symbols / 27 affected processes / risk critical`.
- Critical risk disposition: accepted for this increment because the changed shared config path only reads a default-true boolean, and the runtime short-circuit is gated by `config.adversarial and not config.adversarial_enabled`. Focused regressions cover default-enabled behavior, explicit `false` preservation, install-time override, no channel calls when disabled, skip persistence, requirements review `deferred`, source/template sync, dist template behavior, lint, typecheck, and build.
