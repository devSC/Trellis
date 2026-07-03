# 允许用户覆盖 Guru 风险路由建议实施计划

## Preconditions

- Task remains in `planning` until this plan is reviewed and `task.py start` is run.
- Before editing Python symbols, run GitNexus impact where available per `AGENTS.md`; if the GitNexus MCP/CLI is unavailable, record the fallback caller search before editing.
- Preserve unrelated working tree changes: currently `AGENTS.md`, `CLAUDE.md`, and `marketplace` are pre-existing dirty entries.

## Scope

Primary source files:

- `packages/cli/src/templates/guru/overlay/verify/guru_contract.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
- `packages/cli/src/templates/guru/overlay/hooks/guru_after_create.py`
- `packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md`
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
- matching `guru-template/overlay/**` mirrors
- `.trellis/spec/cli/backend/guru-overlay-gates.md`

## Steps

1. Impact and call-site scan
   - Run impact for `validate_contract`, `validate_commit_contract`, `default_contract`, `task_route_and_risk`, `full_chain_packet_required`, `_contract_route_for_review_policy`, `cmd_init_contract`, and `guru_after_create.main`.
   - If GitNexus is unavailable, use targeted `rg` caller scans and record the fallback in this file or implementation evidence.

2. Contract schema helpers
   - Add helpers to normalize/read `recommended_route`, `selected_route`, and `route_selection`.
   - Add validation for high-risk non-full override audit: non-empty `user_quote`, `selected_by=user`, `risk_acknowledged=true`, valid selected route.
   - Remove unconditional high-risk non-full rejection.
   - Keep `small_inline` commit-contract rejection and micro scope/max-file checks.

3. Init contract writer
   - Extend `cmd_init_contract` option parsing to accept override metadata, or support a compact option set such as `--recommended-route`, `--user-override-quote`, `--risk-acknowledged`.
   - Populate `assessment.recommended_route` and `route_selection`.
   - Make missing override audit fail only when `risk=high` and selected route is non-full.

4. Runtime route policy
   - Update `_contract_route_for_review_policy` so valid high-risk non-full override returns the selected route.
   - Verify `lite_task` gets bounded review policy even when `risk=high`.
   - Keep missing/invalid contract and `risk=unknown` on strict default.

5. Slice packet preflight
   - Confirm `full_chain_packet_required` only returns true for selected `route=full_chain` and `risk=high`.
   - Update error wording: “or lower risk only by confirmed contract change” should become “or choose/update selected route with user override audit”.

6. Commit/scope gate
   - Update `validate_commit_contract` and commit-plan stage splitting so high-risk path signals are warnings for valid user-overridden non-full contracts.
   - Preserve blocking for scope, max_files, forbidden patterns, task artifacts, missing review evidence, and invalid contracts.

7. After-create and skill/spec wording
   - Reword default full-chain contract as conservative recommendation, not irreversible route.
   - Replace “强制 full / 不得降级 / cannot downgrade” wording in skill/spec with recommendation + override audit rules.

8. Tests
   - Update existing “init-contract rejects high-risk downgrade” test into:
     - missing override audit blocks high-risk non-full route
     - valid high-risk + lite override passes
     - valid high-risk + micro override passes only with scope/max_files
   - Add route policy assertion: high-risk selected lite uses lite bounded policy.
   - Add implementation preflight assertion: high-risk selected lite does not require slice packet.
   - Add commit contract assertion: high-risk path signal inside valid override scope does not block solely for high-risk signal.
   - Keep full-chain high-risk slice packet tests unchanged.

9. Mirror and verify
   - Mirror source/template changes.
   - Run `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`.
   - Run source/template diff checks for changed mirror files.
   - Run `git diff --check`.

## Validation Commands

```bash
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
diff -q packages/cli/src/templates/guru/overlay/verify/guru_contract.py guru-template/overlay/verify/guru_contract.py
diff -q packages/cli/src/templates/guru/overlay/verify/guru_gate.py guru-template/overlay/verify/guru_gate.py
diff -q packages/cli/src/templates/guru/overlay/verify/guru_risk.py guru-template/overlay/verify/guru_risk.py
diff -q packages/cli/src/templates/guru/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_supervise.py
diff -q packages/cli/src/templates/guru/overlay/hooks/guru_after_create.py guru-template/overlay/hooks/guru_after_create.py
diff -q packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md guru-template/overlay/agents-skills/client-small-iteration-dev/SKILL.md
git diff --check
```

## Review Checklist

- [x] PRD no longer says high-risk forces full.
- [x] Spec no longer says high-risk non-full route blocks when user override audit is valid.
- [x] Existing selected full-chain behavior remains strict.
- [x] Invalid/malformed contracts still fail closed.
- [x] Tests cover both positive override and missing-audit negative paths.

## Implementation Evidence

- 2026-07-03: GitNexus impact checks:
  - `validate_contract`: 15 impacted symbols, LOW, affected `cmd_status` / `main`.
  - `validate_commit_contract`: 7 impacted symbols, LOW, affected `main`.
  - `_contract_route_for_review_policy`: 17 impacted symbols, CRITICAL, affected `main` / `cmd_status` / `cmd_confirm` / `auto` / `guru_supervise.run_action`; implementation kept as narrow validation-gated route selection.
  - `guru_after_create.main`: 1 impacted symbol, LOW.
  - `cmd_init_contract`: not found in stale GitNexus index; fallback `rg` caller scan used.
- 2026-07-03: `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` passed: 507 passed / 0 failed.
- 2026-07-03: `python3 -m py_compile` passed for source and template `guru_contract.py`, `guru_gate.py`, and `guru_after_create.py`.
- 2026-07-03: Source/template mirror `diff -q` passed for changed verify scripts, tests, client-small-iteration skill, hooks, and guru workflows.
- 2026-07-03: `git diff --check` passed.
- 2026-07-03: `pnpm lint` and `pnpm typecheck` passed.
- 2026-07-03: GitNexus `detect-changes --scope all` reported 22 files, 86 symbols, 16 affected processes, risk CRITICAL. The result includes pre-existing unrelated dirty files `AGENTS.md`, `CLAUDE.md`, and `marketplace`; expected task scope is the Guru source/template/spec/task files listed in this task.
