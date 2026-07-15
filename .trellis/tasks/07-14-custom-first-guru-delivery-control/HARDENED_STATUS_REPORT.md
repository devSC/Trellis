# Guru Custom Delivery Control Hardened Status

Status: **historical M4 hardened candidate; superseded by current M5/M6 amendment**.
This report does not claim production packaging, archive or finish-work completion.

Supersession note: this report is the immutable M4 snapshot. The user-approved M5/M6 amendment replaces the current Lite `confirmation=0` contract with a standard Trellis task, conditional repository-first Brainstorm, one current requirements confirmation and autonomous closure. The measurements below remain historical evidence and must not be presented as the new contract.

Recorded at: `2026-07-15T15:01:27+08:00`

The current execution authority is the confirmed M0-M6 outcome-first milestone set in `prd.md` and
the requirement package; this report remains the immutable M4 evidence snapshot. Bootstrap burn, six independent slices, Marketplace/WAL infrastructure,
trusted reviewer identity and a generic replay framework are not completion criteria.

## Final Exact Snapshot

```text
domain: m4-final-implementation-snapshot-v1
file count: 30
reviewed digest: cdefa3d83bcbe18c13558c5895b72b432480ca39c20783a59a0019d3c486e712
provider: codex
review result: clean after one documentation repair batch
reviewer contexts: 1
independence/trusted-review claim: none
actual Claude invocation or review: 0
```

The snapshot excludes shared `AGENTS.md`, `CLAUDE.md`, the dirty `marketplace` submodule,
append-only `implementation-evidence.jsonl`, and this post-review report. Those exclusions prevent
unrelated or mutable evidence from changing the reviewed implementation digest.

## Six-Outcome Matrix

| User outcome | Executable or operational proof | Current result |
| --- | --- | --- |
| Lite quickly enters real code | Final M1 disposable run reached `lib/m1_lite_probe.dart` in 18s; route `lite_task/host_inline`; confirmation 0; Worker 0; pre-code Gate 0 | PASS |
| High-risk exposes risk before implementation | Full/high route required risk, slice and envelope evidence; missing risk packet returned 2 with `status=planning`, `start_attempts=0`, no official subprocess | PASS |
| Few confirmations then autonomous close | Small/Micro/Lite budgets are 0; Full is at most one batch; unchanged attestation creates no second batch; guarded continuation reaches deterministic check | PASS |
| Repeated work becomes cheaper | Exact evidence reused across 7/7 intents with a declared 70% controllable proxy; target drift and docs-code-test drift each invalidated 7/7; provider token telemetry remains `unknown` | PASS for proxy contract |
| Docs, code and tests stay aligned | Executable trace covers REQ-UC/BHV 001-007; consistency negatives reject missing or stale surfaces; final Codex review repaired the two remaining wording contradictions | PASS |
| Gate reduces rather than creates rework | Lite has no pre-code planning/review Gate; High-risk and stale evidence block before write; candidate false-positive Gate rework is 0/4 observed episodes, explicitly a small sample | PASS for measured sample |

## Milestone Readback

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 | completed | commits `de52458f`, `52e64185`; runnable Custom V0 and reversible self-use lifecycle |
| M1 | candidate complete | `M1_OPERATIONAL_ROUTE_PROOF.md`; final Lite TTFC 18s; Full missing-risk pre-start block; focused policy/start/apply suites |
| M2 | candidate complete | `M2_ALL_INTENT_COMPOUNDING_PROOF.md`; 7-intent exact reuse/invalidation, confirmation reuse and Gate-value accounting |
| M3 | candidate complete | `M3_CUSTOM_TEMPLATE_CUTOVER_PROOF.md`; official Trellis 0.6.7 four-stack resolution and six-operation Custom lifecycle |
| M4 | candidate pass, commit authorized | final trace/spec sync, full Custom verification bundle and clean exact-snapshot Codex review |

The task remains `in_progress`. The user supplied the one final commit authorization, and the
required GitNexus `detect_changes` readback ran before staging. Archive, finish-work and push
remain unauthorized.

## Custom And Official Cutover

The official Trellis `0.6.7` package resolved and installed all four typed pairs:

```text
guru-flutter-client + guru-client
guru-go-backend + guru-go
guru-h5-web + guru-h5
guru-ios-native + guru-ios
```

The official HTTPS Git E2E passed, and the raw blank-template fallback was rejected even though the
raw CLI returned zero. The exact current Guru candidate digest is
`1bddfb3af654adef0dccae0839201d3e4ffa7d80e5617ae28761c6a0b58aa917`.

The self-use Custom lifecycle is:

```text
plan -> apply -> status -> verify -> upgrade -> unapply
```

`plan`, `status` and `verify` are byte-read-only. Status is one of `installed-current`, `drifted`
or `not-applied`; `prepared/manual_required` is honestly reported as `drifted`. Upgrade requires a
fresh external rollback bundle, and its unapply restores the exact immediate pre-upgrade state
while preserving unrelated user content and `.git`.

## Verification Bundle

```text
bash guru-template/overlay/tests/apply_test.sh
120 passed / 0 failed

bash guru-template/overlay/verify/tests/run_tests.sh
564 passed / 0 failed

python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_guru_catalog.py' -v
18 passed / 0 failed

bash guru-template/overlay/tests/official_067_e2e.sh --catalog
official package 0.6.7: PASS
four spec/workflow stacks: PASS
raw blank fallback: REJECTED
hermetic HTTPS Git fixture: PASS

changed-Python py_compile: PASS
changed-shell bash -n: PASS
JSON and JSONL parse: PASS
git diff --check: PASS
packages/cli/src/**: zero task diff
packages/core/**: zero task diff
.trellis/scripts/guru/**: zero candidate copy
task-local bootstrap history: unchanged, not burned, not reused
```

The final Codex reviewer did not rerun deterministic tests. It consumed this bundle, reviewed the
exact 30-path snapshot, reported two MEDIUM documentation-consistency findings, and verified their
single repair batch against digest
`9d2396976da196ef89fffaaccbf6c423e545c695b31ca9dfe9a5505dbbe4ab5f`.
The pre-commit whitespace check then removed one M2 EOF blank line; the same reviewer verified that
the final worktree/index digest
`cdefa3d83bcbe18c13558c5895b72b432480ca39c20783a59a0019d3c486e712` changed no semantic claim.
All eight outcome/lifecycle invariants passed on the final snapshot.

## Honest Limits

- The 70% value is a deterministic planning/context/token-budget proxy, not provider billing data.
- The 0/4 Gate-rework value is a small candidate sample, not production-scale telemetry.
- Current status is a self-use hardened candidate, not production release packaging.
- Final commit is authorized; archive, finish-work and push are outside this authorization.

## Immediate Use

```bash
bash guru-template/overlay/apply.sh --plan /path/to/trellis-project flutter \
  --rollback-bundle /tmp/guru-overlay-rollback

bash guru-template/overlay/apply.sh /path/to/trellis-project flutter \
  --rollback-bundle /tmp/guru-overlay-rollback

bash guru-template/overlay/apply.sh --status /path/to/trellis-project \
  /tmp/guru-overlay-rollback

bash guru-template/overlay/apply.sh --verify /path/to/trellis-project \
  /tmp/guru-overlay-rollback

bash guru-template/overlay/apply.sh --unapply /path/to/trellis-project \
  /tmp/guru-overlay-rollback
```
