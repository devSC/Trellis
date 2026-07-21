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
- [ ] Is each required row resolved from the latest valid evidence bound to the
      current baseline, with any newer current non-pass row (including
      `implementation_verified`, pending, or failure) superseding an earlier
      pass?
- [ ] Is `accepted` withheld while any required row is missing, pending, failed,
      stale, or superseded, even when tests and review are green?

The evidence row statuses are `implementation_verified`,
`runtime_acceptance_pending`, `runtime_acceptance_failure`, and
`runtime_acceptance_pass`. `accepted` is a task-level reporting conclusion only
after all required rows are current pass; none of these values is a new
`task.json` lifecycle state.

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
