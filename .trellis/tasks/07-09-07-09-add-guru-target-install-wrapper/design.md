# Design: Guru target install wrapper

## Overview

This is a thin operator wrapper around the existing Guru install authorities:

- source preparation: `sync:guru:check` and `build`;
- target setup: local `trellis init` when `.trellis/` is missing;
- overlay refresh: local `trellis guru apply`;
- target verification: smoke commands in the target repository.

The wrapper does not duplicate `apply.sh` internals and does not introduce a new TypeScript CLI command surface.

## Units

### UNIT-wrapper-cli

- Owner: `packages/cli/scripts/guru-install-target.sh`
- Responsibility: parse `<platform> <target> [options]`, validate dependencies, print phase-labeled output, and orchestrate the install flow.
- Boundaries: no package publishing behavior, no direct mutation of target project conventions, no business-code edits.

### UNIT-package-entry

- Owner: `packages/cli/package.json`
- Responsibility: expose `guru:install` as a maintainable entrypoint for repo-local invocation.

## Flow

1. Resolve `repo_root` from the script directory.
2. Validate `platform` and `target`.
3. Optionally run source preparation.
4. If target lacks `.trellis/`, optionally run local `trellis init` using the platform's Guru template/workflow pair.
5. Run local `trellis guru apply <platform> <target>`.
6. Run target smoke checks.
7. Clean target `.trellis/scripts/**/__pycache__`.

## Error Model

- Fatal errors exit non-zero immediately and print the failed phase.
- Bootstrap `check-start` rc=2 is advisory because bootstrap PRDs are not feature PRDs.
- Any other bootstrap `check-start` rc is treated as smoke failure.

## Validation

Primary validation is command-level:

- `bash -n packages/cli/scripts/guru-install-target.sh`
- `pnpm --filter @devsc/trellis run sync:guru:check`
- `pnpm --filter @devsc/trellis run build`
- `pnpm --dir packages/cli run guru:install -- ios /Users/devSC/Documents/MyProject/wproxy --skip-source-prepare`
