# M1 Operational Route Proof

Status: **candidate pass for M1 operational use after independent-check repair**. This is not a production-ready or final-task-closure claim.

Recorded at: `2026-07-15T13:28:59+08:00`

Exact changed-source digest: `0e80b3cd8559c23ab72982498d864c83ea0d87fd148cdedfd0882915e2500407`

## Scope

M1 used two official Trellis `0.6.7` initialized disposable targets. The final reproducible repair
smoke used `/tmp/trellis-guru-m1-rerun.6CzbLC`. Both targets and all M1 rollback bundles were
deleted after managed unapply verification.

The proof covered:

1. Installed four-route policy resolution.
2. A real Lite first-code edit derived from session `019f5b42-b507-7801-96ef-50b1ed01c863`.
3. A Full/high-risk pre-implementation guard derived from session
   `019f5f27-045d-7fc1-b84d-5ce21e8c8358`.
4. Official-Core Custom install/unapply without a Core or SDK fork.

## Blockers Found And Repaired

| Repair batch | Reproduced blocker | Repair | Result |
|---|---|---|---|
| 1 | Official `0.6.7` apply failed because missing fork-only `before_start` was fatal; the installer also omitted policy JSON, resolver, guarded task wrapper and `after_start` observer | Install the existing Custom runtime, use compensated official-Core mode, and route Full through `guru_task.py`; no Core edit | official apply passes |
| 1 | Four workflows still sent Lite through Overview/Detail and Full through direct `task.py start` | Align all four workflow breadcrumbs and phase text with policy: Lite compact host-inline; Full guarded activation | docs/code/tests consistency passes |
| 2 | `guru_after_create.py` ignored `task.json.description`, so a benign title hid `workflow/hook/gate/runtime` risk and produced `medium/lite_task` | Classify the combined title, description and affected paths before start | fresh task is `full_chain/high` |
| 2 | A local capability fixture briefly made task creation claim unverified `managed_parallel/enforced` | High-risk creation records only honest route/risk evidence until a runner is actually probed | no unverified execution topology in the contract |
| 3 | Independent check found all four workflows still contained normative light-chain Overview/Detail/Worker steps after the new Lite breadcrumb | Make `gate-contract.json.route` the execution authority and scope all planning, confirm, `check-implementation` and Worker text to Full | Lite path is host-inline only |
| 3 | The three installed `*-small-iteration-dev` skills still required two clean Overview/Detail reviews; the consistency check only looked for new positive phrases | Repair all installed skills and add a stale-contract negative fixture across workflows, skills and Gate usage | false-green closed; `109/0` |
| 3 | Delivery-policy rejection could fall back to the cheaper risk-only assessment | Fail closed to `full_chain/unknown` and cover duplicate scope rejection | no malformed scope becomes Micro/Lite |

GitNexus upstream impact was run before production edits. All affected files/symbols were LOW;
the largest reported direct caller count was 2 and no affected execution process was reported.

## Installed Route Matrix

These are measured CLI wall times from installed files, not policy deadlines.

| Input | Route | Risk | Topology decision | Confirmation budget | Worker budget | Measured CLI wall | Result |
|---|---|---|---|---:|---:|---:|---|
| low, no commit | `small_inline` | low | `host_inline` | 0 | 0 | 0.13s | PASS |
| low, scoped commit | `micro_task` | low | `managed_single` policy fixture | 0 | 1 | 0.11s | PASS |
| bounded behavior change | `lite_task` | medium | `host_inline` | 0 | 0 | 0.12s | PASS |
| workflow/hook/gate/runtime | `full_chain` | high | `managed_parallel` policy fixture | 1 | bounded | 0.11s | PASS |

The CLI topology fields above are selection fixtures, not proof that a live managed runner was
started. M1 started no provider Worker for route inspection.

## Lite Dogfood

The Lite clock started at `2026-07-15T12:53:20+08:00` and the first real code file existed at
`2026-07-15T12:54:41+08:00`.

| Measure | Observed |
|---|---:|
| initial `time_to_first_code` | 81s |
| user confirmations | 0 |
| Workers started | 0 |
| Overview/Detail artifacts or review loop | 0 |
| finding-to-fix cycles | 1 (`--assignee` required by disposable official target) |
| task route | `lite_task`, `medium`, `host_inline` |
| pre-code Gate | none |
| post-code Gate | `deterministic_final` only |

The real disposable edit was `lib/m1_lite_probe.dart`. `dart format --output=none
--set-exit-if-changed` passed, and the installed contract assertion printed
`LITE_DETERMINISTIC_FINAL_PASS`.

The post-repair reproducible run reached the same real code path in **18 seconds**. This is the
final M1 TTFC result; the initial 81-second observation above remains historical evidence rather
than being overwritten. The final run printed:

```text
LITE_OPERATIONAL_PASS route=lite_task risk=medium topology=host_inline pre_code_gates=0 confirmations=0 workers=0 deterministic_final=pass
LITE_COMMAND_RESULT format_rc=0 assert_rc=0 time_to_first_code_seconds=18
```

## Full High-Risk Dogfood

The Full clock started at `2026-07-15T12:55:33+08:00`; the missing-risk result was verified at
`2026-07-15T12:56:53+08:00`.

Before any start, task creation produced:

```text
status=planning
guru_chain=full
route=full_chain
risk=high
risk_flags=gate,hook,runtime,workflow
execution_policy_present=false
```

With a slice packet and execution envelope present but the risk packet absent,
`guru_task.py start` returned exit `2`. Readback proved `status=planning`, `start_attempts=0`, and
the risk packet was the only missing member of that three-artifact set. Measured end-to-end wall
time was 80s.

The positive path used one explicitly synthetic disposable confirmation (`confirmation_batch=1`)
inside the deterministic start-guard fixture. The exact installed `guru_task.py` and
`guru_after_start.py` bytes matched the tested source. The fixture completed guarded official-start
simulation, observed the real `after_start` contract, verified lifecycle postconditions, and then
passed its deterministic check. The missing-confirmation sibling fixture failed before the official
subprocess.

No real user confirmation was consumed by M1. No live provider Worker was started by either dogfood.

The post-repair Full smoke created the other two artifact locations while deliberately leaving only
`risk-packets/delivery-control.json` absent. The guarded command returned before an official
subprocess or start attempt:

```text
[guru-task:start] blocked: StartNotReady: required artifact missing: delivery-control.json
HIGH_RISK_OPERATIONAL_PASS route=full_chain risk=high missing_artifact=risk_packet status=planning start_attempts=0 official_subprocess=not_started
FULL_HIGH_COMMAND_RESULT rc=2
```

The first invocation on this disposable target lacked a Git repository and failed before the guard
with `cannot find repo root`; `git init -q` supplied the documented repository prerequisite. This is
counted as one operational recovery cycle rather than omitted from the evidence.

## Reproducible Command Bundle

The commands below are the normalized command sequence used by the final smoke. `$TASK_REL` was the
single directory returned by the matching `find` command.

```bash
TARGET=$(mktemp -d /tmp/trellis-guru-m1-rerun.XXXXXX)
BUNDLE=$(mktemp -d /tmp/trellis-guru-m1-bundle.XXXXXX); rmdir "$BUNDLE"
(cd "$TARGET" && npx -y @mindfoldhq/trellis@0.6.7 init -y --codex -u codex-m1)
bash guru-template/overlay/apply.sh "$TARGET" flutter --rollback-bundle "$BUNDLE"

cd "$TARGET"
python3 .trellis/scripts/task.py create "M1 Lite operational smoke" \
  --slug m1-lite-operational-smoke --assignee codex-m1 \
  --description "bounded behavior change with focused test" --no-start
# Codex host-inline edit added lib/m1_lite_probe.dart.
dart format --output=none --set-exit-if-changed lib/m1_lite_probe.dart

python3 .trellis/scripts/task.py create "M1 Full high-risk operational smoke" \
  --slug m1-full-high-operational-smoke --assignee codex-m1 \
  --description "change workflow hook gate runtime" --no-start
git init -q
ZERO=0000000000000000000000000000000000000000000000000000000000000000
python3 .trellis/scripts/guru/guru_task.py start "$TASK_REL" \
  --slice delivery-control --gate-digest "$ZERO" \
  --slice-packet-digest "$ZERO" --risk-packet-digest "$ZERO" --envelope-digest "$ZERO"

bash guru-template/overlay/apply.sh --unapply "$TARGET" "$BUNDLE"
```

The wrapper's filename-only error was normalized by a readback assertion proving that the slice
packet and execution envelope existed, the risk packet alone was absent, task status remained
`planning`, and `start-attempts/` did not exist.

## Metrics

| Metric | M1 value |
|---|---:|
| initial `time_to_first_code` | 81s |
| final post-repair `time_to_first_code` | 18s |
| `user_confirmation_count` after milestone confirmation | 0 |
| synthetic disposable confirmation batches | 1 |
| whole-milestone implementation Worker count (outside Lite dogfood) | 1 |
| whole-milestone review Worker count | 1 |
| product finding-to-fix cycles | 3 repair batches |
| Lite fixture recovery cycles | 1 |
| post-repair operational prerequisite recovery cycles | 1 (`git init`) |
| full 564-overlay-suite runs | 0 |
| final focused suites | policy 20/20; start guard 22/22; apply/consistency 109/109 |
| planning digest invalidations | 0 |
| evidence-cache digest invalidations exercised in M1 | 0 |
| provider token telemetry | unknown |
| controllable token/context proxy | not claimed for M1 dogfood |
| Gate-triggered repair | breadcrumb budget caught one oversized repair before install; no false-positive Gate block |

## Verification

```text
delivery policy focused suite: 20 passed / 0 failed
start guard focused suite: 22 passed / 0 failed
apply/unapply and consistency suite: 109 passed / 0 failed
post-repair route consistency: 4 workflows + 3 installed skills + Gate usage PASS
targeted guarded positive: 1 passed / 0 failed
targeted missing confirmation: 1 passed / 0 failed
bash -n: PASS
py_compile: PASS
git diff --check: PASS
Core-zero: PASS
task-local bootstrap changes: 0
real staged paths: AGENTS.md, CLAUDE.md only
real staged diff digest: 1833ab52309f425e0eded8fed066ad8750b1c573ceada78daa3a589a159c56b7
Claude invocation or task-channel event: none
managed unapply: restored, unrelated dogfood files preserved before target deletion
```

The policy contains the expected `claude_forbidden=true` string. That is a negative policy field,
not a provider plan, event or invocation.

## M1 Decision

M1 passes the operational threshold for self-use:

- Lite initially reached code in 81 seconds; the final post-repair reproducible run reached the
  same code path in 18 seconds, with no confirmation, Worker, or planning review loop.
- High-risk classification occurred before start and missing risk evidence blocked with no start attempt.
- The one-confirmation guarded continuation passed on an exact-byte deterministic fixture.
- The Custom package installed and uninstalled on official Trellis without Core/SDK edits.
- The independent check's two HIGH findings were repaired as one batch, and both operational paths
  were rerun from exact commands before the disposable target was removed.

M2 still owns live all-intent cost compounding, actual managed-runner capability evidence, warm-cache
measurement, and Gate-value/rework ratios. M1 does not claim those outcomes are complete.
