# Guru Custom Delivery Control V0

Status: **candidate usable**. This is the first runnable Custom-overlay version, not final production hardening.

Recorded at: `2026-07-15T09:26:23+08:00`

Current status note: this file preserves the original V0 deadline snapshot. Its
hardening list is superseded by `HARDENED_STATUS_REPORT.md`: failed-apply recovery,
managed-asset unapply, the full Custom overlay suite, and official Template
cutover have since completed. Deferred infrastructure that does not serve the six
user outcomes remains intentionally deleted from the critical path.

Exact V0 target digest: `cfea96ad35742e0a6088d7eed15873f0bcbbdbef00c71857096a97f1a48e66d5`

## What Is Usable

1. One delivery policy resolves `small_inline`, `micro_task`, `lite_task`, and `full_chain` high-risk work.
2. Lite resolves to direct `host_inline` implementation with `TTFC=300s`, zero confirmation, zero Worker, advisory metrics, and only `deterministic_final` after code.
3. Full high-risk work cannot start before current risk evidence and one digest-bound Codex confirmation. Missing or stale evidence blocks before any subprocess.
4. After that single confirmation, the bounded supervisor continues through deterministic checking without another confirmation Gate.
5. Exact scope fingerprint, target digest, and docs-code-tests digest reuse passed evidence at a 70% planning/token proxy budget; digest drift invalidates reuse.
6. A deterministic check catches docs/code/tests missing assets and rejects Claude provider plan/events.
7. The official Custom overlay installs into a disposable Trellis target and can restore its exact preimage through an external rollback bundle.

## Route Matrix

| Route input | Resolved route | TTFC | Pre-risk | Confirmations | Workers | Blocking shape | Exact reuse | Result |
|---|---|---:|---|---:|---:|---|---|---|
| small inline | `small_inline` | 120s | N/A | 0 | 0 | final deterministic only | 70%, drift invalidates | PASS |
| micro | `micro_task` | 300s | N/A | 0 | 1 | micro contract + final deterministic | 70%, drift invalidates | PASS |
| lite | `lite_task` | 300s | N/A | 0 | 0 | no pre-code Gate; final deterministic only | 70%, drift invalidates | PASS |
| full high-risk | `full_chain` | 900s | required | 1 | bounded budget | risk + guarded start before Worker; final deterministic | 70%, risk gates unchanged | PASS |

The six user outcomes all have an executable V0 proof:

| User outcome | V0 proof | Result |
|---|---|---|
| Lite quickly enters code | `test_lite_enters_implementation_without_precode_gate_confirmation_or_worker` plus live policy CLI output | PASS |
| High-risk exposes risk before code | risk packet pre-write flag plus start guard missing/stale-evidence negative tests | PASS |
| Few confirmations, autonomous closure | route budget is 0/0/0/1; supervisor proceeds to deterministic check | PASS |
| Repeated work becomes cheaper | exact evidence hit uses 70%; target/consistency digest drift returns 100% | PASS |
| Docs, code, tests stay aligned | real consistency matrix passes; missing-root fixture fails closed | PASS |
| Gate reduces rework | Lite has no pre-code review Gate; only high-risk and final/irreversible boundaries block | PASS |

## Historical Failure Replay

| Session | Replayed failure mode | Executable evidence | Result |
|---|---|---|---|
| `019f5b42-b507-7801-96ef-50b1ed01c863` | Lite remains in a long planning/review loop with no code | Lite direct-implement test, zero Worker/confirmation assertions, 300s TTFC, exact reuse test | PASS |
| `019f5f27-045d-7fc1-b84d-5ce21e8c8358` | high-risk launches before risk/confirmation, repeated confirmation, or Claude invocation | missing-confirmation blocks before subprocess, resolved/current evidence starts, one-batch budget, Claude launch/event negatives | PASS |

Replay subset: `5 passed / 0 failed`.

## Install And Try

The target must already be a Trellis project with `.trellis/`.

```bash
bash /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree/guru-template/overlay/apply.sh \
  /tmp/guru-v0-target flutter \
  --rollback-bundle /tmp/guru-v0-rollback
```

Inspect the Lite decision:

```bash
python3 /tmp/guru-v0-target/.trellis/scripts/guru/guru_delivery_policy.py \
  --description "bounded behavior change" \
  --commit-requested
```

Inspect the high-risk decision:

```bash
python3 /tmp/guru-v0-target/.trellis/scripts/guru/guru_delivery_policy.py \
  --description "change workflow hook gate runtime" \
  --path .trellis/workflow.md \
  --commit-requested
```

Unapply only while the target still matches the post-apply digest:

```bash
bash /Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree/guru-template/overlay/apply.sh \
  --unapply /tmp/guru-v0-target /tmp/guru-v0-rollback
```

If non-Git target content changed after apply, unapply fails closed instead of overwriting the user's new work. `.git` is excluded from the bundle, digest, and restoration.

## Verification

```text
Delivery policy + start guard: 42 passed / 0 failed
Custom apply/unapply + consistency: 87 passed / 0 failed
Historical failure-mode replay subset: 5 passed / 0 failed
Python py_compile: PASS
Shell bash -n: PASS
git diff --check: PASS
Core-zero: PASS, 0 changes under packages/cli/src and packages/core
Real staged tree: 399ac482382f242f0effb8e0dc5bb2620b5dfd80, unchanged
Bootstrap history: 4 events, retry_consumed(verified), 0 burned
Final Codex check-only review: PASS, findings=none, recommendation=candidate_usable
```

The V0 validation intentionally did not run the full overlay suite. That suite belongs to hardening, not this candidate-usable deadline.

## V0 Deferral Resolution

| V0 item | Current resolution |
| --- | --- |
| Partial failed-apply recovery | Completed: exact owned recovery or explicit `manual_required` fail-closed state |
| Incremental per-asset uninstall | Completed as managed-asset unapply with unrelated user content preserved |
| Full overlay regression | Completed: `564/0` hardening baseline; M4 owns the final proportional rerun |
| Template cutover hardening | Completed in `M3_CUSTOM_TEMPLATE_CUTOVER_PROOF.md`: official 0.6.7 four-stack E2E plus reversible lifecycle `120/0` |
| Bootstrap burn/reuse | Deleted from completion criteria; historical chain remains read-only and not burned/reused |
| Marketplace/WAL/trusted identity/generic replay/six slice lifecycles | Deleted from completion criteria because they add no required user outcome |
| Production release packaging | Still out of scope; current status remains a self-use hardened candidate |

The original V0 measurements above remain historical evidence and are not
rewritten as if they were collected by the later hardened implementation.
