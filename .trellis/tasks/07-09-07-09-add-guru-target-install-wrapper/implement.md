# Implementation Plan

## Scope

Writable source files:

- `packages/cli/scripts/guru-install-target.sh`
- `packages/cli/package.json`

Task-local artifacts may be updated for evidence, but the implementation diff must stay focused on the wrapper and package entrypoint.

## Approach

1. Add a Bash wrapper in `packages/cli/scripts/`.
2. Resolve the repo root from the script location, not from the caller's current directory.
3. Validate platform and target path.
4. Optionally initialize the target when `.trellis/` is missing.
5. Run source preparation unless disabled:
   - `pnpm --filter @devsc/trellis run sync:guru:check`
   - `pnpm --filter @devsc/trellis run build`
6. Run `packages/cli/bin/trellis.js guru apply <platform> <target>`.
7. Run target smoke checks:
   - compile Guru scripts with `PYTHONDONTWRITEBYTECODE=1`;
   - run `.trellis/scripts/get_context.py`;
   - run `guru_gate.py status` for bootstrap task if present;
   - run `guru_gate.py check-start` for bootstrap task as advisory only and accept the expected rc=2 gate block;
   - remove target `.trellis/scripts/**/__pycache__`.
8. Add `guru:install` package script.

## Guardrails

- Do not duplicate `apply.sh` internals.
- Do not commit, push, archive, or finish-work unless separately requested.
- Do not edit target business files.
- Do not treat bootstrap `check-start` rc=2 as install failure.

## Validation

```bash
bash -n packages/cli/scripts/guru-install-target.sh
pnpm --filter @devsc/trellis run sync:guru:check
pnpm --filter @devsc/trellis run build
pnpm --dir packages/cli run guru:install -- ios /Users/devSC/Documents/MyProject/wproxy --skip-source-prepare
git diff --check -- packages/cli/scripts/guru-install-target.sh packages/cli/package.json
```
