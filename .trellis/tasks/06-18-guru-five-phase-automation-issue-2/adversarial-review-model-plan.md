# Adversarial Review Model Preference Plan

## Background

Guru adversarial review already switches to the opposite provider through:

```bash
python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements <task_dir>
python3 .trellis/scripts/guru/guru_supervise.py --adversarial overview <task_dir>
python3 .trellis/scripts/guru/guru_supervise.py --adversarial detail <task_dir>
```

The current behavior chooses the opposite provider only. It does not pin the stronger model requested for adversarial review.

## Requirement

When Guru adversarial review runs, prefer stronger reviewer models:

- Claude reviewer: use Claude Sonnet 4.8 by default.
- Codex reviewer: use GPT-5.4 with high reasoning effort.

The model names must be project-configurable. Defaults are only fallbacks when the project does not set overrides.

This should apply only to adversarial review workers, not to normal implementation or check workers.

## Scope

In scope:

- `guru_supervise.py --adversarial requirements`
- `guru_supervise.py --adversarial overview`
- `guru_supervise.py --adversarial detail`
- Project-level model override keys under existing `.trellis/config.yaml`.
- A narrow `trellis channel spawn` reasoning-effort pass-through, because strict Codex `high` reasoning cannot be represented by `--model` alone.
- Packaged Guru template sync so newly installed projects get the same behavior.
- CLI build/package validation, because npm installs consume `packages/cli/dist`.
- Dry-run/test coverage that proves the selected model is visible before execution.

Out of scope:

- Changing default `.trellis/agents/*.md` model frontmatter.
- Changing ordinary `implement`, `check`, or `implement-check` model selection.
- Adding a user-facing model preference registry, new config file, or broad configuration system.
- Changing `trellis channel run`; adversarial review uses `channel spawn`.
- Adding default reasoning effort to non-adversarial workers.

## Current Evidence

- `trellis channel spawn` already supports `--model`.
- Claude channel adapter forwards `model` to Claude CLI as `--model`.
- Codex channel adapter forwards `model` to Codex app-server as `-c model="<id>"`.
- Codex app-server generated schema includes `model_reasoning_effort`, so strict `gpt-5.4 high` requires a narrow channel spawn reasoning-effort pass-through.
- `guru_supervise.py` already reads `.trellis/config.yaml` via `_config_value`, including `guru.supervision.provider`, `implement_timeout`, `check_timeout`, and worker guard settings. Reusing this parser is enough for model overrides.
- The repo has prior history removing broad hardcoded model defaults because default `model: opus` caused cost and compatibility problems. This model preference should stay scoped to adversarial review only.

## Recommended Implementation

Use a small default map in `guru_supervise.py`, overridden by `.trellis/config.yaml`:

```text
claude -> model claude-sonnet-4-6
codex  -> model gpt-5.4, reasoning effort high
```

Project override contract:

```yaml
guru:
  supervision:
    adversarial_claude_model: claude-sonnet-4-6
    adversarial_codex_model: gpt-5.4
    adversarial_codex_reasoning_effort: high
```

Rules:

- Missing, blank, or comment-only override values fall back to defaults.
- Model names are pass-through strings. Do not validate them against a hardcoded SKU list.
- `adversarial_codex_reasoning_effort` is also pass-through, defaulting to `high`.
- These keys are read only when adversarial review is active; normal workers ignore them.
- Adversarial execution is best-effort: if the opposite provider CLI is missing
  or the provider invocation returns an error/killed/missing terminal status,
  log and persist the skip reason, show it in `guru_gate.py status`, and
  continue the main Guru task flow.
- `guru_config_patch.py ensure-supervision-defaults` writes these defaults into fresh Guru projects and preserves existing custom values.
- `config.hooks.yaml` documents the keys as optional project overrides.

Apply the map only when:

```text
config.adversarial == true
action in {"requirements", "overview", "detail"}
```

Add the smallest channel support required for that map:

- `channel spawn --reasoning-effort <level>` parses an optional value.
- The supervisor config/view carries `reasoningEffort` only when provided.
- The Codex adapter converts it to `-c model_reasoning_effort="<level>"`.
- The Claude adapter ignores it unless a future Claude CLI option exists.
- Existing `channel spawn` calls without the flag keep identical behavior.
- `channel run` remains unchanged.

Expected dry-run behavior:

```bash
# current provider codex -> adversarial provider claude
trellis channel spawn ... --provider claude --model claude-sonnet-4-6

# current provider claude -> adversarial provider codex
trellis channel spawn ... --provider codex --model gpt-5.4 --reasoning-effort high
```

Expected override dry-run behavior:

```yaml
guru:
  supervision:
    adversarial_claude_model: custom-claude
    adversarial_codex_model: custom-codex
    adversarial_codex_reasoning_effort: max
```

```bash
trellis channel spawn ... --provider claude --model custom-claude
trellis channel spawn ... --provider codex --model custom-codex --reasoning-effort max
```

## Files To Change

Source Guru template:

- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/guru_config_patch.py`
- `guru-template/overlay/config-snippets/config.hooks.yaml`

Packaged Guru template after sync:

- `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_config_patch.py`
- `packages/cli/src/templates/guru/overlay/config-snippets/config.hooks.yaml`

- `packages/cli/src/commands/channel/spawn.ts`
- `packages/cli/src/commands/channel/supervisor.ts`
- `packages/cli/src/commands/channel/adapters/index.ts`
- `packages/cli/src/commands/channel/adapters/codex.ts`
- `packages/cli/src/commands/channel/index.ts`

Docs for the public spawn flag:

- `.trellis/spec/cli/backend/commands-channel.md`
- `.trellis/spec/cli/backend/script-conventions.md`
- `packages/cli/src/templates/common/bundled-skills/trellis-channel/references/workers.md`
- `packages/cli/src/templates/common/bundled-skills/trellis-channel/references/command-reference.md`

Tests:

- `packages/cli/test/guru/guru-bundled.test.ts`
- `packages/cli/test/commands/channel-codex-adapter.test.ts`
- `packages/cli/test/commands/channel-spawn-config.test.ts`
- A focused Guru dry-run assertion for `.trellis/config.yaml` overrides. Keep it inside existing Guru tests; no new test harness.
- A config patch assertion that fresh Guru projects get the default adversarial model keys and existing custom keys are preserved.
- A fallback assertion that blank/comment-only model overrides do not leak comments into `--model` or `--reasoning-effort`.

## Validation Plan

Run the smallest checks that prove behavior:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_supervise.py --help
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_supervise.py --platform go --provider codex --adversarial requirements .trellis/tasks/06-18-guru-five-phase-automation-issue-2 --run-id model-check --dry-run
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_supervise.py --platform go --provider claude --adversarial requirements .trellis/tasks/06-18-guru-five-phase-automation-issue-2 --run-id model-check --dry-run
tmpdir="$(mktemp -d)"
cp -R .trellis "$tmpdir/.trellis"
cat > "$tmpdir/.trellis/config.yaml" <<'YAML'
guru:
  platform: go
  supervision:
    adversarial_claude_model: custom-claude
    adversarial_codex_model: custom-codex
    adversarial_codex_reasoning_effort: max
YAML
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_supervise.py --root "$tmpdir" --platform go --provider codex --adversarial requirements "$tmpdir/.trellis/tasks/06-18-guru-five-phase-automation-issue-2" --run-id model-override --dry-run
PYTHONDONTWRITEBYTECODE=1 python3 guru-template/overlay/verify/guru_supervise.py --root "$tmpdir" --platform go --provider claude --adversarial requirements "$tmpdir/.trellis/tasks/06-18-guru-five-phase-automation-issue-2" --run-id model-override --dry-run
pnpm -C packages/cli sync:guru
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts -t "adversarial"
pnpm -C packages/cli exec vitest run test/commands/channel-codex-adapter.test.ts
pnpm -C packages/cli exec vitest run test/commands/channel-spawn-config.test.ts
pnpm -C packages/cli build
pnpm -C packages/cli pack --pack-destination "$(mktemp -d)" --json
git diff --check
```

Also verify the public surface did not expand accidentally:

```bash
rg -- "--reasoning-effort" packages/cli/src/commands/channel packages/cli/src/templates/common/bundled-skills/trellis-channel .trellis/spec/cli/backend/commands-channel.md
```

Expected grep result:

- `spawn` implementation and spawn docs mention `--reasoning-effort`.
- Codex adapter mentions `model_reasoning_effort`.
- `channel run` implementation and run docs do not gain `--reasoning-effort`.
- Guru dry-run output includes the flag only for adversarial Codex workers.
- Guru dry-run output reflects `.trellis/config.yaml` model overrides when present.
- Fresh-project config patch output contains the three adversarial override keys; custom existing values are preserved.
- Built `dist` and npm tarball include the updated Guru overlay files and common `trellis-channel` references.

Before committing, run GitNexus checks required by `AGENTS.md`:

```bash
npx gitnexus impact build_run_plan --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree --file guru-template/overlay/verify/guru_supervise.py --direction upstream
npx gitnexus impact registerChannelCommand --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree --direction upstream
npx gitnexus impact channelSpawn --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree --direction upstream
npx gitnexus impact runSupervisor --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree --direction upstream
npx gitnexus impact buildCodexArgs --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree --direction upstream
npx gitnexus impact writeSupervisorConfig --repo /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree --direction upstream
npx gitnexus detect-changes --scope all --repo Trellis
```

If any channel symbol reports HIGH or CRITICAL impact, pause and report the blast radius before editing that symbol.

After `pnpm -C packages/cli sync:guru`, do not manually edit the packaged Guru copy. The bundled test should prove the source template and packaged template stay in sync.

## Risks And Decisions

- `claude-sonnet-4-6` is the default requested for Claude adversarial review. If the local Claude CLI does not accept this identifier, keep the default because model names are project-configurable pass-through strings; projects can override it without a code change.
- Model override keys live under existing `guru.supervision` config. Do not add a registry until there are more than these three knobs.
- Adding `--reasoning-effort` to channel spawn is a public CLI surface. Keep it optional and do not add it to unrelated commands unless needed.
- If Codex app-server changes the config key, the dry-run still proves intent but runtime may not honor high effort. The adapter test should assert the current `model_reasoning_effort` argument shape.
- Do not store these model preferences in agent frontmatter; that would affect non-adversarial worker cost and behavior.
