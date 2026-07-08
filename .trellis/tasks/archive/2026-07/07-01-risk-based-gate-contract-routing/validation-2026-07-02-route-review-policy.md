# Route-aware review policy validation - 2026-07-02

## Scope

This note records the post-implementation validation for the route-aware Guru review policy extension.

Changed behavior:

- `small_inline` / `micro_task` do not require requirements adversarial review.
- `lite_task` uses bounded review policy: requirements adversarial review is optional, and overview/detail still require two current-digest clean review run ids but do not require an adversarial reviewer.
- `full_chain`, `risk=unknown`, missing contracts, malformed contracts, and invalid contracts fall back to strict default policy.
- Route policy only relaxes adversarial evidence requirements. It does not bypass structure gates, human confirmations, current digest checks, blocked/medium+ evidence, staged scope validation, or implementation review digest checks.

## Non-OCR review

The review was performed without OCR. Local source inspection, GitNexus CLI, Guru gates, and deterministic tests were used.

## Impact evidence

- `node .gitnexus/run.cjs impact _contract_route_for_review_policy --repo Trellis --file packages/cli/src/templates/guru/overlay/verify/guru_gate.py --direction upstream --include-tests`
  - Result: target not found, risk `UNKNOWN`, because the symbol is new relative to the current index.
- `node .gitnexus/run.cjs impact _review_policy --repo Trellis --file packages/cli/src/templates/guru/overlay/verify/guru_gate.py --direction upstream --include-tests`
  - Result: target not found, risk `UNKNOWN`, because the symbol is new relative to the current index.
- `node .gitnexus/run.cjs impact _requirements_review_problem --repo Trellis --file packages/cli/src/templates/guru/overlay/verify/guru_gate.py --direction upstream --include-tests`
  - Result: risk `LOW`, 3 impacted symbols, 2 affected processes.
- `node .gitnexus/run.cjs impact _review_state --repo Trellis --file packages/cli/src/templates/guru/overlay/verify/guru_gate.py --direction upstream --include-tests`
  - Result: risk `HIGH`, 11 impacted symbols, 4 affected processes. Direct callers include `_review_problem`, `_review_route_guidance`, `_review_status_mark`, `_block_review`, `_record_review`, `cmd_confirm`, `cmd_status`, `cmd_check`, and `auto`.
- `node .gitnexus/run.cjs detect_changes --scope unstaged --repo Trellis`
  - Result: 17 files, 40 symbols, 18 affected processes, risk `critical`.
  - Interpretation: expected for Guru gate/template workflow changes; this task itself remains full-chain governed.

## Validation commands

- `pnpm -C packages/cli sync:guru:check`
  - Passed: `guru bundled mirror 与 guru-template/ 一致（无漂移）`.
- `python3 -m py_compile packages/cli/src/templates/guru/overlay/verify/guru_gate.py guru-template/overlay/verify/guru_gate.py packages/cli/src/templates/guru/overlay/verify/guru_contract.py guru-template/overlay/verify/guru_contract.py packages/cli/src/templates/guru/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_supervise.py`
  - Passed.
- `bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
  - Passed: `477 通过 / 0 失败`.
- `python3 .trellis/scripts/guru/guru_gate.py requirements .trellis/tasks/07-01-risk-based-gate-contract-routing`
  - Passed.
- `python3 .trellis/scripts/guru/guru_gate.py overview .trellis/tasks/07-01-risk-based-gate-contract-routing`
  - Passed.
- `python3 .trellis/scripts/guru/guru_gate.py detail .trellis/tasks/07-01-risk-based-gate-contract-routing`
  - Passed.
- `python3 .trellis/scripts/guru/guru_gate.py implement .trellis/tasks/07-01-risk-based-gate-contract-routing`
  - Passed.
- `python3 .trellis/scripts/guru/guru_gate.py check-start .trellis/tasks/07-01-risk-based-gate-contract-routing`
  - Passed.
- `python3 .trellis/scripts/guru/guru_gate.py check-implementation .trellis/tasks/07-01-risk-based-gate-contract-routing`
  - Passed.
- `python3 .trellis/scripts/guru/guru_gate.py trace-matrix .trellis/tasks/07-01-risk-based-gate-contract-routing --strict`
  - Passed: BHV-001 through BHV-006 are closed; no orphan/broken chain.
- `python3 ./.trellis/scripts/task.py validate .trellis/tasks/07-01-risk-based-gate-contract-routing`
  - Passed: `implement.jsonl` and `check.jsonl` valid.
- `git diff --check`
  - Passed.

## Dogfood runtime

The local dogfood runtime `.trellis/scripts/guru/guru_gate.py` was synchronized from `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`.

Reason: the task previously hit `python3 .trellis/scripts/guru/guru_gate.py ...` file/runtime issues, and local validation now uses the same route-aware policy implementation as the source template.

Only `guru_gate.py` required dogfood sync; `guru_contract.py`, `guru_supervise.py`, `guru_risk.py`, and `guru_review_record.py` already matched their source-template counterparts.
