# M2 All-Intent Compounding And Gate-Value Proof

Status: **candidate complete for the declared M2 controllable-proxy contract**. This report does not claim provider billing reduction, production readiness, or a live managed Worker cache.

Recorded at: `2026-07-15T13:44:53+08:00`

Exact executable-proof digest: `3be032cc9a8f0e821651714860ec18c0366b4be54a807ed476221187bfc0835f`

## Scope

M2 reused the installed Custom delivery policy rather than adding a benchmark framework or another execution platform. The executable matrix covers:

1. Route-specific first value, terminal conditions, write capability, confirmation budget and Worker budget for all declared intents.
2. Exact fingerprint plus target/docs-code-test digest reuse across all intents.
3. Target or docs-code-test digest drift invalidation.
4. Lite scope expansion to Full/high before another implementation action.
5. Reuse of the same digest-bound confirmation with a one-batch budget.
6. Gate-value accounting from observed M1 blocking episodes and the current consistency suite.

No production resolver symbol changed. GitNexus reported `resolve_delivery_selection` as HIGH blast radius with 7 direct callers, 22 upstream symbols and one affected hook process, so M2 added combination regressions around the current behavior instead of changing that shared function.

## All-Intent Matrix

The rows below are executable policy selections, not prose classifications. `workers` is the selected route budget, not a claim that a provider Worker was launched.

| Intent | Route / risk | First value | Write capability | Confirmations | Workers | Cold proxy | Exact warm proxy | Digest drift |
|---|---|---|---|---:|---:|---:|---:|---|
| implementation | `lite_task / medium` | `first_code` | `scoped_repository` | 0 | 0 | 100% | 70%, reused | invalidated |
| review-only | `lite_task / medium` | `first_verified_evidence` | `none` | 0 | 0 | 100% | 70%, reused | invalidated |
| research | `lite_task / medium` | `first_verified_evidence` | `none` | 0 | 0 | 100% | 70%, reused | invalidated |
| docs | `lite_task / medium` | `first_accepted_artifact` | `scoped_repository` | 0 | 0 | 100% | 70%, reused | invalidated |
| config | `micro_task / low` | `first_code` | `scoped_repository` | 0 | 1 | 100% | 70%, reused | invalidated |
| ops | `lite_task / medium` | `first_verified_evidence` | `task_artifacts` | 0 | 0 | 100% | 70%, reused | invalidated |
| repeated-debug | `lite_task / medium` | `first_code` | `scoped_repository` | 0 | 0 | 100% | 70%, reused | invalidated |

Every row has the same bounded terminal set:

```text
first_value_deadline
terminal_deadline
budget_exceeded
required_gate_failed
```

Every row also emitted `provider=codex`, `claude_forbidden=true`, `confirmation_batches<=1` and `autonomous_close=true`.

## Evidence Compounding

For each matrix row, M2 executed one cold selection and one exact warm selection with:

```text
same policy_version
same intent and execution route
same scope_fingerprint
same target_digest
same docs_code_test_digest
prior outcome=passed
```

All seven exact warm selections returned:

```text
evidence_reused=true
planning_cost_ratio_percent=70
required_gate_ids unchanged
model_cycles/tool_calls/planned_context_bytes/observed_context_bytes/duplicate_reads <= 70% of cold
```

Each row was then rerun with target digest drift and with docs-code-test digest drift. All 14 drift cases returned:

```text
evidence_reused=false
planning_cost_ratio_percent=100
```

This is a controllable planning/context/token-budget proxy. It proves deterministic policy reuse and invalidation; it does not claim actual provider tokens, billing or wall time fell by 30%.

## Scope And Confirmation

The same implementation request changed from one local code path to code plus `.trellis/workflow.md`. Re-intake changed the selection before another write:

```text
before: route=lite_task risk=medium confirmations=0
after:  route=full_chain risk=high confirmations=1
required pre-write gates include risk_packet and start_guard
```

Building the execution envelope twice with the unchanged selection and the same current attestation digest produced byte-equivalent dictionaries. The confirmation budget remained one batch and the same attestation digest was reused. Existing start-guard regressions separately reject missing or digest-stale confirmation evidence before the official subprocess.

## Gate Value

Gate-caused rework is defined here as a false-positive block that forces correct work to be undone or repeated. Necessary repair after a true contract violation is counted as a valid finding, not as Gate-caused rework.

| Observed blocking episode | Verdict | Rework classification |
|---|---|---|
| Full/high start without a risk packet | valid pre-implementation block | not Gate-caused |
| Workflow breadcrumb body exceeded the 400-byte executable limit | valid install-time contract finding | not Gate-caused |
| Stale Lite Full-Gate wording injected into a negative fixture | valid docs/code/test consistency finding | not Gate-caused |
| Required consistency surfaces removed in a negative fixture | valid docs/code/test consistency finding | not Gate-caused |

Candidate Gate-caused rework ratio:

```text
false-positive Gate blocks / observed blocking episodes = 0 / 4 = 0%
```

This is below the `<10%` milestone threshold, but the sample is only four observed blocking episodes. The earlier `90 passed / 19 failed` apply run represented one breadcrumb root cause across 19 assertions, not 19 independent Gate failures. The independent-check findings are also excluded because they were review findings, not Gate-caused rework.

## Verification

```text
python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_delivery_policy.py' -v
23 passed / 0 failed

bash guru-template/overlay/tests/apply_test.sh
109 passed / 0 failed
docs/code/tests mismatch negative fixture: blocked
stale Lite Full-Gate negative fixture: blocked
Codex plan/event: allowed
Claude plan/event: blocked
```

The exact executable-proof digest binds these paths in this order with path and byte separators:

```text
guru-template/overlay/policy/delivery-policy.json
guru-template/overlay/verify/guru_delivery_policy.py
guru-template/overlay/verify/tests/test_delivery_policy.py
guru-template/overlay/tests/apply_test.sh
```

Per-file SHA-256:

```text
delivery-policy.json    a0edb49c48311e76f8ccdc663bc17f776cff61ad972fba058998cb553289de2a
guru_delivery_policy.py e22d8b3b8a37ad9c6f26b9bb57b101f454ea44fd2f82e1fc594f16ae3aeae65f
test_delivery_policy.py a0204da28db8a9a353b6519fbc1702d5fd67bddd88edeeafd876d9ba206aa610
apply_test.sh            bd44f5749d57011415d5289aec4592e801995e40664ab52dec2056f5add350f8
```

## Telemetry And Decision

| Metric | M2 result |
|---|---|
| provider token telemetry | `unknown` |
| actual provider cost reduction | not claimed |
| controllable warm planning/context/token-budget proxy | 70% of cold across 7/7 intents |
| target-digest invalidations | 7/7 |
| docs-code-test digest invalidations | 7/7 |
| repeated identical confirmation | 0 new batches; same batch-1 attestation reused |
| Gate-caused rework | 0/4 observed episodes, 0%; small sample |
| new full overlay-suite runs | 0 |
| provider | Codex only |

M2 is candidate complete for the approved proxy-level acceptance: all intents have executable first-value and terminal contracts, exact evidence lowers the declared controllable budget to 70%, either relevant digest invalidates reuse, scope expansion promotes before another write, and the same current confirmation is not requested as a second batch.

M3 now owns official Custom/Template cutover readiness. M4 still owns final repository-wide traceability/spec synchronization and the final exact-snapshot check. Neither milestone may reinterpret this report as proof of provider billing reduction or production-scale Gate statistics.
