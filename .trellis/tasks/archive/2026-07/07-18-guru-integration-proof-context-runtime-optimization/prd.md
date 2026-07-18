# Guru Integration Proof Context Runtime Optimization

## Document Status

- Status: Planning complete; awaiting planning review and explicit start approval.
- Classification: Full/high.
- Priority: P1.
- Current boundary: planning review is authorized; runtime implementation,
  implementation-review provider dispatch, commit, and release actions remain
  unauthorized until the complete planning package receives explicit start
  approval.
- Predecessor: `07-17-guru-minimum-stable-parallel-slices` completed its local
  ordinary and Integration commits and has current receipts. This task must not
  rewrite that delivery history.

## Goal

Reuse the existing Guru Python lifecycle commands, without adding a TypeScript
command, and change Full/high Integration semantic review from reinjecting
ordinary slice and generated-mirror bodies to consuming a verifiable proof
bundle. Reduce reviewer latency and input size while preserving current-snapshot
binding, provider policy, append-only evidence, commit Gates, and rollback
semantics.

## User Value

- Detail plans and freezes the delivery graph once; ordinary slices can then
  implement concurrently and publish independent current receipts.
- Integration reviews only composition and Integration-owned bytes instead of
  rereading already-clean ordinary slice bytes.
- A verdict-envelope formatting failure does not pay for a second semantic
  review of the same snapshot.
- A change in one ordinary slice does not indiscriminately invalidate unrelated
  sibling receipts.
- Performance claims are backed by payload, token, reviewer, duplicate-read,
  projection, retry, and regression counters.

## Confirmed Baseline

The predecessor task's final Integration review was:

- run: `20260717233535-62394-review-1`
- reviewed-target digest:
  `977c27f9bf5396cecd73099e0d07a87e910dbfa393e9298123bb290ffec84f8f`
- semantic reviewer dispatch to clean verdict: approximately 262 seconds
- locally observed supervisor stream: approximately 114k serialized-context
  tokens; this is a transport estimate, not a provider billing claim
- deterministic admission: passed before semantic dispatch
- Integration invariants: `INV-SP-007`, `INV-SP-008`, and `INV-SP-009` passed

### Context Assembly

- The package-runtime `guru_supervise._focused_review_context_payload` is called
  by `run_implementation_review`.
- Its current payload includes full `target_paths`, `exact_staged_diff`, up to
  32000 characters of requirements/design text, deterministic summaries,
  dependency receipts, and the complete packet manifest.
- Existing limits apply to selected requirements/design sections, not to the
  final serialized provider prompt.

### Verdict Normalization

- `guru_review_record.normalize_review_record` is the single normalization
  entrypoint for required implementation-review records.
- `guru_supervise._route_from_output` still extracts route and result from free
  text.
- `MALFORMED_REVIEW_OUTPUT` currently creates an append-only blocked record.
  Deterministic evidence can be reused, but a completed semantic result cannot
  yet be reused for serialization-only repair.

### Receipt Currentness

- `guru_gate._validate_historical_slice_receipt` validates target, invariant,
  requirements/design, deterministic command/result, review policy, and
  supervisor-source digests.
- `_validate_slice_receipt` recomputes the slice-specific target, invariant,
  requirements/design, deterministic command/result, and policy components.
  Ordinary currentness intentionally ignores the current supervisor whole-file
  digest.
- Dependency receipts are recursively validated from the dependent packet. A
  changed ordinary component does not directly stale an unrelated sibling.
- The final Gate separately requires only the Integration receipt to bind the
  current supervisor source and can route stale recovery to Integration.
- Direct-owner currentness therefore already exists. This task preserves it and
  adds compatibility regressions; it must not add a receipt schema or parallel
  invalidation manifest.

### Canonical And Package Drift

The repository declares `guru-template` canonical and
`packages/cli/src/templates/guru` generated, while official commands currently
execute the package runtime. The relevant surfaces have substantial baseline
drift:

- `guru_supervise.py`: package relative to canonical approximately `+1440/-33`
- `guru_review_record.py`: approximately `+1844/-3`
- `guru_gate.py`: approximately `+2144/-165`
- `test_slice_commit_lifecycle.py`: package-only

Editing both sides independently would preserve dual ownership and make a later
sync overwrite one implementation. A serial baseline-parity child must first
copy the current package runtime back to canonical without changing package
behavior.

## Requirements

### BHV-001 Proof Bundle Projection

For a current Integration snapshot, the semantic payload must replace clean
ordinary target bodies with current receipt proofs and replace byte-identical
canonical/package mirror bodies with source/peer digest-equality proofs. It may
include only the Integration-owned diff, exact packet invariants, and bounded
requirements/design excerpts required to judge those invariants.

### BHV-002 Final Prompt Budget

Before provider dispatch, measure the complete serialized prompt, including the
invocation contract and proof bundle:

- `payload_bytes <= 98304`
- `estimated_tokens = ceil(payload_bytes / 3)`
- `estimated_tokens <= 25000`

Either exceeded budget must deterministically block before channel creation or
provider dispatch. Full/high v2 Integration has no full-context fallback.

### BHV-003 One Semantic Reviewer

One reviewed-target/evidence snapshot may start exactly one semantic reviewer.
The reviewer must not reread ordinary receipt bodies or mirror bodies and must
not rerun deterministic commands. A permitted serialization-only provider call
is not a semantic reviewer and receives no source or task JSONL context.

### BHV-004 Formatting-Only Retry

When a semantic result exists and only its verdict envelope is malformed, one
serialization-only provider retry may reuse it if and only if the complete
`RetryIdentity` is unchanged. Any target, requirements/design, invariant,
deterministic, policy, supervisor, or proof-bundle digest change requires a new
semantic snapshot. Semantic findings, provider failures, missing invariant
evidence, and snapshot drift are not formatting-only failures.

### BHV-005 Selective Receipt Currentness

Preserve the existing component-based receipt behavior. Changing an ordinary
target or direct binding stales only its owner receipt; unchanged sibling
receipts remain current. Integration may become stale through a changed
dependency receipt or current supervisor source and must then be refreshed.
Do not add receipt schema version 2, a parallel invalidation manifest, or a
blanket sibling refresh.

### BHV-006 Compatibility And Evidence Safety

- Keep the current `implementation-review` CLI entrypoint; add no TypeScript
  CLI/Core command or alternate Integration command.
- Preserve provider policy, same-provider consent, read-only reviewer snapshot,
  append-only JSONL, immutable raw artifacts, and commit-Gate semantics.
- Ordinary v2, Small, Micro, Lite, non-Full, and v1 behavior remains unchanged.
- Do not automatically push, merge, archive, install, canary, run full
  `sync:guru`, or run `finish-work`.

### BHV-007 Canonical Delivery

End with one authoritative runtime source and deterministic package parity. Do
not retain independent canonical and package implementations.

### BHV-008 Observability

One real Full/high Integration fixture must record serialized bytes, estimated
tokens, provider-reported input tokens when available, semantic reviewer count,
duplicate-read/probe count, full-regression count, projection counts,
formatting-retry identity/count, and the receipt invalidation set.

## Behavior Scenarios

### Scenario A: Proof-Only Integration Review

Given a Full/high v2 Integration packet has current ordinary dependency receipts,
an overlap-free staged target, exact generated peers, and passed deterministic
evidence.

When the supervisor assembles and admits the semantic reviewer prompt.

Then it includes only current receipt proofs, digest-equality peer proofs, exact
invariant excerpts, deterministic summaries, and the Integration-owned diff;
it enforces both final-prompt budgets before starting exactly one semantic
reviewer.

### Scenario B: Formatting-Only Recovery

Given the semantic reviewer completed against an unchanged snapshot and its
meaning is recoverable but the required verdict envelope is malformed.

When the supervisor requests formatting repair.

Then immutable semantic evidence is recorded, one serialization-only provider
call receives no source/task JSONL context, and the official review stream gets
only the final normalized verdict or one final blocked row.

### Scenario C: Invalid Or Stale Proof

Given any dependency receipt is stale, a generated peer differs, Integration
writes an ordinary canonical path, the retry identity drifts, or either prompt
budget is exceeded.

When deterministic admission runs.

Then the responsible child is identified and provider dispatch is blocked
without falling back to full context or invalidating unrelated sibling receipts.

## Acceptance Criteria

- [ ] Current ordinary target bodies do not appear in Integration semantic
      context.
- [ ] Each equal canonical/package peer body appears at most once; its proof
      includes source digest, peer digest, and `equal=true`.
- [ ] The Integration-owned diff is complete and the ordinary canonical staged
      diff is empty.
- [ ] The complete serialized prompt is no more than 98304 bytes and no more
      than 25000 estimated tokens.
- [ ] An over-budget prompt blocks before provider dispatch and records zero
      semantic reviewer invocations.
- [ ] A normal snapshot records exactly one semantic reviewer invocation.
- [ ] Duplicate semantic reads/probes are zero and
      `integration_full_regression_count` is exactly one for the final
      post-feature Integration wave. Baseline prerequisite compatibility runs
      are recorded separately and do not increment this metric.
- [ ] A malformed envelope for the same snapshot performs at most one
      serialization-only retry while the semantic reviewer count remains one.
- [ ] A semantic finding, provider failure, snapshot drift, or evidence-digest
      drift never enters formatting-only retry.
- [ ] A direct-owner change stales only that receipt; a shared-contract change
      stales the exact affected set; unrelated siblings remain current.
- [ ] Receipt schema remains version 1 and existing append-only receipts remain
      valid without rewriting history.
- [ ] Raw semantic/retry evidence and official review/receipt history are
      append-only and are never overwritten or deleted.
- [ ] Canonical/package runtime parity passes with no TypeScript command change.
- [ ] Focused tests, bounded package parity, GitNexus `detect_changes`,
      `git diff --check`, and one real Full/high Integration regression pass.

## Non-Goals

- Redesigning the predecessor task's frozen minimum-stable-slice policy.
- Optimizing ordinary v2 or any Small, Micro, Lite, non-Full, or v1 review.
- Adding a TypeScript command, second Integration entrypoint, new provider, or
  weaker provider policy.
- Reinjecting complete ordinary diffs, task artifacts, or mirror bodies.
- Changing Gate production logic when compatibility tests can prove the
  existing selective currentness behavior.
- Fixing unrelated global `sync:guru` drift.

## Confirmed Decisions

All decisions below are `user_confirmed` on 2026-07-18.

### D1 Canonical Baseline

Create `RT-BASELINE-PARITY` as an independent serial prerequisite. It copies the
current package bytes for the three Python runtime files and lifecycle test to
canonical, proves parity, completes review/commit/receipt, and only then
unblocks the two zero-overlap runtime children.

Trade-off: one additional serial delivery absorbs the existing baseline drift,
but restores a single source of truth and prevents later canonical sync from
overwriting the optimization.

### D2 Hard Budget

For eligible Full/high v2 Integration, exceeding either final-prompt budget
hard-blocks before provider dispatch. There is no automatic full-context
fallback. Other routes and schemas retain current behavior.

### D3 First-Release Eligibility

Enable proof projection, final-prompt budgets, and duplicate-read enforcement
only when all are true: Full/high route, review evidence schema version 2,
`integration_slice=true`, and current staged Integration target.

### D4 Append-Only Retry Audit

Persist semantic raw output and `RetryIdentity` in a separate append-only retry
evidence stream. The official `implementation-reviews.jsonl` receives only the
final normalized verdict or, after retry exhaustion, one final blocked row.
Raw and retry evidence is never rewritten or deleted.

### D5 Retry Limit

Each `RetryIdentity` permits at most one serialization-only provider retry. If
that retry is still invalid, append one final blocked
`MALFORMED_REVIEW_OUTPUT` row and stop.

### D6 Token Estimator

Add no tokenizer dependency. Use `ceil(UTF-8 bytes / 3)` on the complete
serialized prompt and enforce both 98304-byte and 25000-token limits before
dispatch. Record provider usage afterward when available for calibration only.

## Open Questions

None. Remaining implementation choices must be derived from these confirmed
requirements, the design's frozen contracts, and repository evidence without
expanding product scope.

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`.
- Repository evidence inspected: current GitNexus index; package supervisor,
  review-record, and Gate symbols; slice lifecycle tests; predecessor final
  review and receipts.
- GitNexus index: current at `e916a54e`.
- Domain/terminology triggers: declared canonical bytes differ from the current
  execution runtime; formatting retry must be distinguished from semantic
  re-review.
- Current code vs user intent conflicts: current focused context reinjects full
  bodies, malformed output becomes an official blocked row immediately, and
  canonical/package runtime bytes have substantial drift.
- Product decisions confirmed: serial baseline parity, hard final-prompt
  budgets without fallback, Full/high v2 Integration-only eligibility,
  append-only retry evidence, one formatting retry, and UTF-8 bytes/3 token
  estimation.
  - DEC-001 canonical baseline: `confirmed_ref: OQ-001 user answer on 2026-07-18`.
  - DEC-002 hard budget: `confirmed_ref: OQ-002 user answer on 2026-07-18`.
  - DEC-003 first-release scope: `confirmed_ref: OQ-003 user answer on 2026-07-18`.
  - DEC-004 retry audit: `confirmed_ref: OQ-004 user answer on 2026-07-18`.
  - DEC-005 retry limit: `confirmed_ref: OQ-005 user answer on 2026-07-18`.
  - DEC-006 token estimator: `confirmed_ref: OQ-006 user answer on 2026-07-18`.
- Open product/scope/risk questions: none because OQ-001 through OQ-006 were
  answered one at a time by the user and are recorded below.

### Question Loop Log

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-001 | 2026-07-18 | Restore canonical parity as a separate prerequisite? | Yes, copy current package runtime to canonical first. | Adds one serial delivery but removes dual source ownership. | 是 | DEC-001 | PRD, design, implement, child graph |
| OQ-002 | 2026-07-18 | Hard-block when either final prompt budget is exceeded? | Yes, block before dispatch with no full-context fallback. | Projection defects become visible instead of silently expensive. | 是 | DEC-002 | PRD, design, supervisor child |
| OQ-003 | 2026-07-18 | Limit first release to Full/high v2 Integration? | Yes, preserve all ordinary and lower-route behavior. | Ordinary v2 does not receive the first performance gain. | 是 | DEC-003 | PRD, design, supervisor child |
| OQ-004 | 2026-07-18 | Separate raw retry evidence from official review rows? | Yes, append raw/identity evidence separately and publish only the final official result. | Requires a bounded task-local evidence stream. | 是 | DEC-004 | PRD, design, verdict child |
| OQ-005 | 2026-07-18 | Permit only one formatting retry per identity? | Yes, then write one final blocked row. | Repeated formatting failures require a later explicit rerun. | 是 | DEC-005 | PRD, design, verdict child |
| OQ-006 | 2026-07-18 | Use dependency-free UTF-8 bytes/3 estimation? | Yes, enforce both byte and token budgets. | Conservative for ASCII-heavy prompts but deterministic. | 是 | DEC-006 | PRD, design, supervisor child |

next_action: no further requirement question; complete current-digest planning
reviews and request one explicit Full/high confirmation batch before start.

### Question Policy

question_policy: mixed

Evidence answered: current context assembly, normalization, receipt currentness,
canonical/package drift, call graph, and baseline performance came from the live
repository and predecessor evidence.

User confirmed in the current turn: OQ-001 through OQ-006 were asked and answered
one at a time; each answer selected the recommended option recorded above.
