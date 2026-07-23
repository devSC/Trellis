---
name: trellis-check
description: "Comprehensive quality verification: spec compliance, lint, type-check, tests, cross-layer data flow, code reuse, and consistency checks. Use when code is written and needs quality verification, before committing changes, or to catch context drift during long sessions."
---

# Code Quality Check

Comprehensive quality verification for recently written code. Combines spec compliance, cross-layer safety, and pre-commit checks.

---

## Step 1: Identify What Changed

```bash
git diff --name-only HEAD
git status
```

## Step 2: Read Task Artifacts and Applicable Specs

Read the current task artifacts in order:

- `prd.md`
- `design.md` if present
- `implement.md` if present

```bash
python3 ./.trellis/scripts/get_context.py --mode packages
```

For each changed package/layer, read the spec index and follow its **Quality Check** section:

```bash
cat .trellis/spec/<package>/<layer>/index.md
```

Read the specific guideline files referenced — the index is a pointer, not the goal.

## Step 3: Run Project Checks

Run the project's lint, type-check, and test commands. Fix any failures before proceeding.

## Step 4: Review Against Checklist

### Code Quality

- [ ] Linter passes?
- [ ] Type checker passes (if applicable)?
- [ ] Tests pass?
- [ ] No debug logging left in?
- [ ] No suppressed warnings or type-safety bypasses?

### Test Coverage

- [ ] New function → unit test added?
- [ ] Bug fix → regression test added?
- [ ] Changed behavior → existing tests updated?

### Spec Sync

- [ ] Does `.trellis/spec/` need updates? (new patterns, conventions, lessons learned)

> "If I fixed a bug or discovered something non-obvious, should I document it so future me won't hit the same issue?" → If YES, update the relevant spec doc.

## Step 5: Cross-Layer And Acceptance Closure

Run source-to-sink closure whenever the accepted behavior crosses logical
boundaries, even if the current diff is confined to one file or layer. Triggers
include a user-visible terminal state, external API/schema, persistence/cache,
asynchronous state, or cross-layer field transformation. If none applies, keep
the same-layer checks below and record why full acceptance closure is not
needed.

### A. Acceptance Path

- [ ] Read the frozen Acceptance Closure Matrix row for each affected
      `acceptance_id`?
- [ ] Trace the declared entry point, authority fingerprint, field/state
      transformations, and allowed terminal result from source to sink?
- [ ] Cover positive and applicable missing/null, error, timeout, and degraded
      paths?
- [ ] Does the deterministic check fail on the known-bad implementation rather
      than only proving a fixed happy-path helper?
- [ ] Does the Integration check close the final user outcome instead of
      substituting an ordinary slice or local layer pass?
- [ ] For `runtime_acceptance_required=true`, is mutable evidence kept in
      task-local `verification-evidence.jsonl`, separate from the digest-bearing
      matrix?
- [ ] Does the review consume one fresh, complete `AcceptanceResolution`
      produced by `ClosureSpec`, rather than selecting evidence rows itself?
- [ ] Is `accepted` withheld while any required row is missing, pending, failed,
      stale, blocked by correction/reconciliation, or superseded, even when
      tests and review are green?

The evidence row statuses are `implementation_verified`,
`runtime_acceptance_pending`, `runtime_acceptance_failure`, and
`runtime_acceptance_pass`. `accepted` is a task-level reporting conclusion only
after all required rows are current pass; none of these values is a new
`task.json` lifecycle state.

#### A1. Canonical Resolution And Reconciliation Audit

This check Skill is a consumer of the acceptance contract, not a second
currentness owner. Require the `ClosureSpec-only` path below whenever the task
is runtime-required, a post-implementation failure is open, or the changed
contract itself owns acceptance closure.

1. **Exact result shape and freshness**

   `ClosureSpec` alone reads the complete raw evidence ledger and exact
   reconciliation journal and emits `AcceptanceResolution`. The result must
   preserve `baseline_binding`, `ledger_snapshot_ref`,
   `reconciliation_snapshot_ref`, `open_correction_debts`,
   `open_retrospective_reconciliations`, `row_results`,
   `selected_evidence_refs`, `blocking_evidence_refs`, `task_result`,
   `blocking_acceptance_ids`, and `next_probe`. Reject a private projection,
   direct row selection, or partial refresh. Any ledger append, journal event,
   or baseline change stales the whole result and requires a fresh full replay.

2. **Raw ledger and correction debt**

   `EvidenceLedger.readAllInAppendOrder()` must return a complete
   `LedgerReadSnapshot`, never an ID/status-filtered view or old prefix. Its
   `LedgerSnapshotRef` binds `artifact_ref`, `append_count`,
   `last_append_position`, and `content_digest` to every raw append and stable
   position. Verify that unreadable appends and readable current-baseline rows
   with invalid status or incomplete required evidence become exact-position
   debts before filtering.

   The empty-ledger identity must be `append_count=0`,
   `last_append_position=null`, with `content_digest` equal to the lowercase
   `SHA-256` of the empty ledger file bytes. For a non-empty snapshot, the
   `LedgerSnapshotRef.content_digest` equals the lowercase `SHA-256` of the exact complete ledger file bytes for that snapshot, never parsed, normalized,
   filtered, or prefix bytes.

   A correction uses `corrects_append_position`, points to the earlier bad
   append, preserves every parseable acceptance/baseline component, and is
   itself complete. The newest correction for that position is authoritative;
   an invalid newest correction remains blocking. A normal later pass, wrong
   pointer, cross-ID correction, baseline relabel, or older correction must not
   clear debt or expose an earlier pass. Only after all debt closes may the
   newest effective current-baseline row for each required ID be selected by
   position and validated.

3. **Exact journal discovery and root**

   The register is exactly
   `<task_dir>/retrospective-reconciliation.jsonl`, using the current or linked
   active repair `TaskRef`. Setup may initialize an empty file only when it then
   rereads the complete file. A resolver must not create a missing register or
   discover it from a snapshot `artifact_ref`. Missing/unreadable is
   `reconciliation_register_unavailable`; malformed is
   `reconciliation_register_corrupt`. Both are blocking `PROCESS_DEFECT`
   results and force `next_probe=null`.

   Under `journal-root-v1`, every `ReconciliationJournalEvent` is a complete
   newline-terminated event. The first event must use `event_position`
   `position=1` and `previous_event_digest=null`; each later
   `previous_event_digest` is the lowercase `SHA-256` of the previous complete
   UTF-8 event line including its newline. A
   `RetrospectiveReconciliationSnapshot` must contain `artifact_ref`,
   `event_count`, `last_event_position`, `last_event_digest`,
   `content_digest`, and replayed entries. For a non-empty journal,
   `last_event_digest` must equal the lowercase `SHA-256` of the final complete
   newline-terminated event bytes, while `content_digest` must equal the
   lowercase `SHA-256` of the complete journal file bytes. The empty-journal
   identity is `event_count=0`, `last_event_position=null`,
   `last_event_digest=null`, and `content_digest` equal to the lowercase
   `SHA-256` of the empty journal file bytes. Partial lines, non-root prefixes,
   gaps, duplicates, digest/transition/snapshot mismatch, or failure to prove a
   unique legal last event are corrupt. Each transition must be fully
   replay-acknowledged before its next side effect.

4. **Attempt-before-append and bounded unknown outcome**

   Before ledger append, require an acknowledged
   `RetrospectiveAppendAttempt` with `attempt_id`, `acceptance_id`, current
   baseline, `retrospective_artifact_ref`, exact row digest,
   `pre_append_ledger_snapshot_ref`, and `retry_ordinal`. Ordinal 0 is the first
   attempt; ordinal 1 is the one permitted retry and names `retry_of`. A
   `LedgerAppendResult` may be accepted, explicitly rejected, or lose its
   acknowledgment (`retrospective_append_outcome_unknown`).

   A `LedgerAppendRef` must come only from
   `deriveLedgerAppendRef(full_snapshot, exact_position)`, using ledger
   `artifact_ref`, the exact position, and lowercase `SHA-256` of that complete
   raw append including its newline. Journal data must not participate.
   `RetrospectiveAppendReconciliation` must first prove the current ledger
   prefix exactly equals the attempt's pre-append snapshot and then search only
   the suffix. For ordinal 0, a unique exact suffix match is `committed`; zero
   is `absent` and permits one newly prepared ordinal-1 retry. Boundary drift,
   history-only/non-unique/unreadable matching, or a missing ordinal-1
   acknowledgment is `ambiguous`. Reject any third retry, record, acceptance
   decision, runtime probe, or Finish bypass.

5. **Record binding closes the complete chain**

   Accepted or `committed` only supplies `accepted_append_ref`; it does not
   close an attempt. Repair must build the canonical
   `FailureRetrospectiveRecord` and `record_ref`. Then `ClosureSpec` appends a
   `record-bound` event containing `accepted_append_ref`, `record_ref`, and
   exact `closes_attempt_ids`. With no retry, it closes exactly ordinal 0; after
   retry success, it closes exactly the ordinal-0 plus ordinal-1 chain. Missing
   ancestors, extra IDs, or a cross-acceptance, cross-baseline, or cross-row
   chain remains open/corrupt. Every replayed entry whose `record_ref` is null
   remains in `open_retrospective_reconciliations` regardless of state. Only a
   strict full-replay acknowledgment of the valid `record-bound` event closes
   the chain.

6. **Independent ledger/journal correlation**

   Require `retrospective-ledger-journal-correlation`: acceptance ID, baseline,
   exact row digest, and the independently derived ledger append ref must map
   every retrospective ledger row to exactly one surviving journal chain.
   Reject an older-valid journal prefix, empty rollback, cross-position/ref
   mismatch, or repeated identical raw rows that yield zero or multiple
   matches. A later pass never repairs this process defect.

7. **Task conclusion and privacy**

   Use the blocker order defined by `ClosureSpec`: unavailable/corrupt journal,
   open retrospective reconciliation, correction debt, current failure, stale,
   missing, pending, then `implementation_verified`. An open reconciliation
   always has `next_probe=null`. `task_result=accepted` requires both open lists
   empty and every required selected row to be current
   `runtime_acceptance_pass`.

   `verification-evidence.jsonl` may contain the complete canonical, minimally
   scoped and sanitized `VerificationEvidenceRow`: `acceptance_id`, `status`,
   `baseline_binding`, `environment`, `steps_or_command`, `expected`, `actual`,
   `evidence_refs`, `recorded_at`, `recorded_by`, plus applicable correction and
   retrospective artifact/control references. The journal may contain the
   sanitized event/attempt control metadata required for replay, including
   positions/digests, attempt/acceptance/baseline identity,
   `retrospective_artifact_ref`, exact row digest, snapshot refs, retry/state,
   `accepted_append_ref`, `record_ref`, `closes_attempt_ids`, reason, actor, and
   timestamp. Reject secrets, tokens, PII, complete request/response bodies,
   user content, or raw retrospective payloads/rows in any of those fields.
   This is a Skill/spec/workflow contract, not permission for a parser, schema,
   lifecycle state, script-level Gate, or Trellis/Guru/CLI Python, shell,
   TypeScript, hook, verify, or apply change.

### B. Data Flow

- [ ] Read flow traces correctly: Storage → Service → API → UI
- [ ] Write flow traces correctly: UI → API → Service → Storage
- [ ] Types/schemas correctly passed between layers?
- [ ] Errors properly propagated to caller?
- [ ] Local checks remain green without being treated as a substitute for the
      declared end-to-end result?

### C. Post-Implementation Failure Closure

For a user/QA-reported runtime failure, do not close the same-goal repair until
the retrospective records:

- [ ] Direct, evidenced cause?
- [ ] Earliest Requirement/Design/Implementation/Test/Review/Process Gate that
      should have caught it?
- [ ] Why existing tests and review produced a false green?
- [ ] A regression or runtime probe that fails on the old behavior?
- [ ] Exactly one complete `prevention_disposition`: `writeback_required` with
      an allowed Skill/workflow/spec owner and validation, or
      `no_writeback_required` with an explicit reason and evidence references?

Missing fields, a TODO, both disposition branches, neither branch, or an
unnecessary invented writeback leaves the repair incomplete.

### D. Code Reuse (modifying constants, creating utilities)

- [ ] Searched for existing similar code before creating new?
  ```bash
  grep -r "pattern" src/
  ```
- [ ] If 2+ places define same value → extracted to shared constant?
- [ ] After batch modification, all occurrences updated?

### E. Import/Dependency (creating new files)

- [ ] Correct import paths (relative vs absolute)?
- [ ] No circular dependencies?

### F. Same-Layer Consistency

- [ ] Other places using the same concept are consistent?

---

## Step 6: Report and Fix

Report violations found and fix them directly. Re-run project checks after fixes.
