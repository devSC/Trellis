# Configure high-risk slice review provider implementation plan

## Scope

Implement a configurable high-risk slice implementation-review provider policy with default `current`, explicit opt-in to `opposite`, and optional provider pinning to `codex` or `claude`.

Do not commit, push, archive, or run finish-work as part of implementation unless the user explicitly asks after gates pass.

## Pre-Implementation Requirements

- Before editing any function/class/method, run GitNexus impact analysis for the target symbol per `AGENTS.md`.
- Re-read live diffs for `.trellis/scripts/guru/guru_supervise.py`, `guru_risk.py`, `guru_config_patch.py`, and `.trellis/spec/cli/backend/guru-overlay-gates.md`; these files already have unrelated or prior task changes.
- Preserve existing uncommitted changes not made for this task.

## Implementation Steps

### Step 1 - Provider policy resolver

Targets:

- `.trellis/scripts/guru/guru_supervise.py`
- `guru-template/overlay/verify/guru_supervise.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
- generated `packages/cli/dist/templates/...` if required by repo convention

Tasks:

- Add high-risk provider policy constants and parser.
- Port the existing template `implementation-review` check-only path into dogfood `.trellis/scripts/guru/guru_supervise.py` so dogfood runtime exposes the same relevant action as `guru-template` and CLI src/dist copies.
- Distinguish slice-backed policy routing from non-slice staged opposite-provider routing.
- Default high-risk independent review to current provider.
- Preserve old behavior when policy is `opposite`.
- Support pinned `codex` and `claude`.
- Preserve strict precedence: audited `--same-provider --user-quote` > project policy > slice packet provider metadata; record the override source and quote.
- Route both `implement-check` and `implementation-review` through the same resolver; include `implementation-review --slice`, `implementation-review --slice --staged`, and staged/contract review targets in tests.
- Preserve raw packet semantic-review intent for audit, but make the resolved high-risk project policy authoritative for slice-backed worker selection.
- Do not let explicit slice packet provider metadata switch or block the provider resolved from `high_risk_review_provider_policy`.
- Without a valid audited CLI one-off override, keep non-slice `implementation-review --staged/--contract` governed by its existing staged synthetic packet and explicit `semantic_review_provider: opposite(required=true)`; the config policy applies only to slice-backed high-risk review targets.
- Include policy/reason in stderr/dry-run output.
- Treat dogfood/template parity drift as a blocker: `.trellis/scripts/guru/guru_supervise.py --help` must expose `implementation-review` after implementation, and dry-run coverage must include dogfood and template paths.

### Step 2 - Review record validation

Targets:

- `guru_review_record.py` in all overlay copies.

Tasks:

- Add explicit supervisor context to allow same-provider required review only when the resolved policy permits it.
- Pass explicit supervisor policy context so slice-backed clean records validate against the actual resolved `check_provider`.
- Keep packet provider metadata for audit without letting it override `current`, `opposite`, `codex`, or `claude` project policy.
- Keep non-slice staged/contract review on the existing explicit opposite-provider validation path when no valid audited CLI override is present.
- Keep actual worker provider validation strict.

### Step 3 - Config patch and docs

Targets:

- `guru_config_patch.py` in all overlay copies.
- `config.hooks.yaml` and overlay README in `guru-template`, CLI src templates, and dist templates.
- Existing CLI override parsing remains in `guru_supervise.py`; no new CLI command surface is required.

Tasks:

- Add default `high_risk_review_provider_policy: current`.
- Preserve target project explicit values.
- Document allowed values and separation from `adversarial_enabled`.
- Grep and update, or explicitly verify as out of scope, workflow templates, implementation review agent skills, and Guru harness gate/spec docs that mention `implementation-review`, `review_provider`, `semantic_review_provider`, `opposite-provider`, or `adversarial_enabled`.

### Step 4 - Tests

Targets:

- `guru-template/overlay/verify/tests/run_tests.sh`
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
- generated dist copy if required.

Test cases:

- Unset/default config keeps Codex high-risk check on Codex.
- Unset/default config keeps Claude high-risk check on Claude when Claude is the current provider.
- Unset/default config keeps `implementation-review --slice --dry-run` on Codex.
- `implementation-review --slice --staged --dry-run` follows the high-risk project policy even when the slice packet requests another provider.
- `implementation-review --staged/--contract --dry-run` without `--slice` and without a valid CLI override keeps the staged synthetic packet's explicit opposite(required=true) behavior.
- Dogfood `.trellis/scripts/guru/guru_supervise.py --help` includes `implementation-review`, and dogfood `implementation-review --slice --dry-run` uses the same resolved provider as the template/CLI copies.
- `opposite` flips Codex to Claude and Claude to Codex.
- `codex` / `claude` pin provider.
- Pinned provider remains authoritative when packet metadata requests another provider.
- Invalid policy fails before plan construction; assert non-zero, actionable stderr, and no `WORKER=`, `check-*` plan, or `trellis channel spawn` in either output stream.
- `--same-provider --user-quote` overrides `opposite` and `claude` policy values for one run; missing or blank quote fails before config resolution/plan creation, and successful records retain the quote.
- Non-slice staged review ignores conflicting `current|codex` config and stays opposite unless a valid CLI one-off override is present.
- Record normalization rejects incoherent source/policy/quote/check-provider tuples instead of trusting `same_provider_required_allowed` alone.
- Only an absent policy key uses default `current`; explicit null, empty string, whitespace-only string, non-string, and unknown values fail before plan construction.
- Same-provider required clean review is accepted with policy context and missing raw semantic provider.
- Same-provider required clean review is rejected without policy context.
- Required explicit semantic opposite in a slice packet cannot override `current`; same-provider clean is accepted only when it matches the actual spawned provider and supervisor policy context.
- Explicit `semantic_review_provider.provider=codex|claude(required=true)` remains audit metadata for slice-backed review; the actual check provider must match the configured policy.

### Step 5 - Validation

Run focused validation:

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
python3 -m py_compile .trellis/scripts/guru/guru_supervise.py .trellis/scripts/guru/guru_risk.py .trellis/scripts/guru/guru_config_patch.py .trellis/scripts/guru/guru_review_record.py
python3 -m py_compile guru-template/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_risk.py guru-template/overlay/verify/guru_config_patch.py guru-template/overlay/verify/guru_review_record.py
python3 .trellis/scripts/guru/guru_supervise.py --help | grep -q "implementation-review"
python3 guru-template/overlay/verify/guru_supervise.py --help | grep -q "implementation-review"
pnpm --filter @devsc/trellis --fail-if-no-match test -- guru-bundled
pnpm -C packages/cli sync:guru:check
git diff --check
```

The overlay shell tests must contain executable assertions for the provider-policy edges listed in Step 4. If broad overlay tests are too slow or noisy, record the exact blocker in task-local evidence and run the named narrow test snippets that cover those same edges.

## Rollback Points

- If provider policy parsing destabilizes normal `--adversarial`, revert only `guru_supervise.py` policy resolver and keep config docs pending.
- If review record validation becomes too broad, revert the same-provider acceptance branch and keep high-risk policy as `opposite` until a safer context field is ready.
- If template drift appears, stop and resync source/template copies before continuing.

## Completion Criteria

- PRD/design/implement are current.
- Requirements, overview, and detail gates pass after review evidence is recorded.
- Implementation reaches `task.py start` only after user confirmation gates.
- Final diff does not absorb unrelated dirty worktree changes.
