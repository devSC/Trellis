# Guru Integration Proof Context Runtime Optimization Design

## Status And Boundary

This is the technical design for a Full/high parent task. The parent owns the
requirements, delivery graph, frozen cross-child contracts, and final proof. It
does not directly implement runtime code.

The design changes the existing Python lifecycle only. It adds no TypeScript
command, no alternate review entrypoint, no receipt schema, and no automatic
push, merge, archive, install, canary, or finish-work behavior.

The first release applies only when all of these are true:

- the selected route is Full/high
- `review_evidence_schema_version == 2`
- `integration_slice == true`
- the review target is the current staged Integration snapshot

All ordinary v2, Small, Micro, Lite, non-Full, and v1 review flows retain their
current context and verdict behavior.

## Evidence And Blast Radius

The current package runtime is the execution authority but is not byte-equal to
the declared `guru-template` source:

| Surface | Package delta relative to canonical |
| --- | ---: |
| `guru_supervise.py` | approximately `+1440/-33` |
| `guru_review_record.py` | approximately `+1844/-3` |
| `guru_gate.py` | approximately `+2144/-165` |
| `test_slice_commit_lifecycle.py` | package-only |

GitNexus upstream impact on the current package implementation:

| Symbol | Risk | Impacted symbols |
| --- | --- | ---: |
| `_focused_review_context_payload` | MEDIUM | 41 |
| `_route_from_output` | LOW | 2 |
| `normalize_review_record` | MEDIUM | 84 |
| `_validate_slice_receipt` | MEDIUM | 50 |

No HIGH or CRITICAL symbol impact was reported. The large number of lifecycle
test callers requires focused tests plus the existing full lifecycle regression.

## Delivery Graph

```text
RT-BASELINE-PARITY
        |
        +----------------------------+
        |                            |
RT-PROOF-SUPERVISOR       RT-VERDICT-EVIDENCE
        |                            |
        +-------------+--------------+
                      |
              RT-INTEGRATION-PROOF
```

`RT-BASELINE-PARITY` is a serial prerequisite. After its current receipt exists,
the two ordinary runtime children have zero mutable-path overlap and no
implementation dependency. Their implementation may run concurrently. Formal
staged review, commit, and receipt publication remain serial in one control
worktree. `RT-INTEGRATION-PROOF` runs last.

The live aggregate `slice-plan` is intentionally not the Wave 1 dispatch
authority. It reports `PACKET_AMBIGUOUS_WITHOUT_SLICE` and
`PARALLEL_TARGET_PATH_OVERLAP` because it compares the serial baseline evolution
and Integration coverage union against every packet. After the baseline receipt,
the host coordinator independently recomputes only the two Wave 1 mutable sets,
requires their intersection to be empty, and dispatches them into two isolated
git worktrees using the explicit parent packets. The child task directories are
allocation/rollback context only; they are not independently started Guru tasks.
Workers write only their worktree-owned paths and return patch plus focused
evidence. The control worktree alone performs formal review, commit, and receipt
publication one slice at a time.

## RT-BASELINE-PARITY

### Responsibility

Restore one authoritative source without changing the behavior of the package
runtime currently used by official Guru commands.

### Owned Paths

- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/guru_review_record.py`
- `guru-template/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/tests/test_slice_commit_lifecycle.py`

The package counterparts are read-only inputs for this child. The child copies
their exact bytes to canonical, then proves all four pairs are byte-identical.
It does not run full `sync:guru`, because unrelated reinstall and README drift
remain outside this task.

This one-time source-restoration review is expected to carry approximately
448876 bytes of existing runtime drift before normal review metadata. The
planning budget is therefore explicitly 589824 bytes for this prerequisite,
matching the existing observed Full-route ceiling. This exception does not
apply to the new Integration proof path, whose final semantic prompt retains the
98304-byte and 25000-token hard limits.

### Acceptance

- the four canonical files equal their package counterparts byte for byte
- package runtime files are unchanged by the child
- the existing package lifecycle test passes before and after canonicalization
- the commit contains only the four canonical paths

## Frozen Internal Contracts

These contracts are internal Python values and task-local evidence. They do not
change packet or receipt schemas.

### IntegrationProofBundle

```text
schema_version
review_target
reviewed_target_digest
component_digests
ordinary_target_union_digest
ordinary_receipt_proofs[]
generated_peer_proofs[]
integration_owned_paths[]
integration_owned_diff
invariants[]
requirements_design_proofs[]
deterministic_result_proofs[]
payload_metrics
proof_bundle_digest
```

The bundle is serialized with stable key ordering and compact separators. Its
digest is domain-separated and computed from the complete bundle before it is
included in the reviewer brief.

### OrdinaryReceiptProof

```text
slice_id
commit_sha
receipt_id
review_run_id
reviewed_target_digest
invariant_verdicts_digest
target_paths_digest
requirements_design_digest
deterministic_commands_digest
deterministic_results_digest
review_policy_digest
state = current
```

The supervisor must validate each dependency receipt through the existing Gate
currentness helpers before projecting it. A missing, stale, non-ancestor, or
digest-inconsistent receipt blocks before provider dispatch.

### GeneratedPeerProof

```text
source
peer
source_digest
peer_digest
equal = true
```

Peer mapping follows the existing `sync-guru-template.js` contract:

- `guru-template/overlay/<suffix>` maps to
  `packages/cli/src/templates/guru/overlay/<suffix>`
- `guru-template/specs/<suffix>` maps to
  `packages/cli/src/templates/guru/specs/<suffix>`
- `guru-template/workflows/<id>-workflow.md` maps to
  `packages/cli/src/templates/guru/workflows/<id>.md`

The helper rejects a peer without a canonical source in the Integration target,
an ambiguous mapping, unequal bytes, missing files, deletions, and paths outside
the managed roots. Equal peer bodies are omitted from semantic context.

### RetryIdentity

```text
reviewed_target_digest
target_paths_digest
invariant_set_digest
requirements_design_digest
deterministic_commands_digest
deterministic_results_digest
review_policy_digest
supervisor_source_digest
proof_bundle_digest
```

Formatting-only retry is legal only when every component is identical before
and after the semantic worker. Any mismatch creates a new semantic snapshot and
prohibits retry reuse.

### VerdictEnvelope

The envelope contains the existing seven required header fields, exactly the
packet invariant IDs and their status/evidence/reason values, findings, reviewer
probe metadata, review target, provider, `RetryIdentity`, and proof bundle
digest. Existing clean/finding validation remains authoritative.

### Frozen Cross-Child API

The two concurrent runtime children share values, not mutable files. Detail
freezes the following `guru_review_record` operations before either child is
dispatched:

```text
build_retry_identity(component_digests) -> RetryIdentity
classify_retryable_format_failure(raw_output, expected_invariants,
                                  retry_identity) -> classification
append_format_retry_evidence(task_dir, run_metadata, retry_identity,
                             attempt, raw_output, status) -> evidence_ref
normalize_retry_verdict(raw_output, review_context,
                        retry_identity, proof_bundle_digest) -> review_record
```

All inputs and outputs are JSON-compatible mappings. `build_retry_identity`
requires exactly the fields listed in `RetryIdentity` and rejects missing,
extra, or non-string digest fields. `classification` is one of
`valid`, `retryable_format`, `semantic_finding`, or `non_retryable`; it never
causes provider dispatch or writes an official review record.

`RT-VERDICT-EVIDENCE` owns these operations and their append-only persistence.
`RT-PROOF-SUPERVISOR` owns orchestration and provider calls. During concurrent
implementation, supervisor focused tests use a stub with this exact contract;
verdict-evidence focused tests call the real operations directly. Neither child
may change a signature or value field without returning to Detail and
invalidating both child planning inputs.

## RT-PROOF-SUPERVISOR

### Owned Paths

- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/tests/test_integration_proof_context.py`

No new production Python module is added. New Python files are tests only, used
to preserve zero mutable overlap between ordinary children.

### Eligibility

The existing focused context remains the default. The proof path is selected
only for an Integration packet satisfying the first-release boundary. Missing
or malformed eligibility fields fail closed for Full/high and do not silently
fall back to full context.

### Admission Flow

```text
resolve staged Integration target
  -> validate all dependency receipts as current
  -> compute complete ordinary target union
  -> require staged ordinary canonical overlap = 0
  -> classify Integration-owned staged paths
  -> project exact generated peers to digest-equality proofs
  -> build Integration-owned diff only
  -> project requirements/design inputs to path/selector/digest proofs
  -> include exact packet invariant rules
  -> summarize already-passed deterministic results
  -> serialize complete reviewer brief
  -> enforce byte and estimated-token budgets
  -> dispatch exactly one semantic reviewer
```

Whole-file PRD/design/implement bodies are not included. A manifest entry with
an exact heading may include that bounded section when needed; whole-file inputs
are represented by path, selector, selected-content bytes, and digest. A
whole-file selector is rejected for this proof path. Packet invariant rules
remain the semantic contract.

### Budget

The budget is measured after the complete brief, invocation contract,
deterministic proof, and `IntegrationProofBundle` have been serialized:

```text
payload_bytes = len(brief.encode("utf-8"))
estimated_tokens = ceil(payload_bytes / 3)
payload_bytes <= 98304
estimated_tokens <= 25000
```

Both conditions must pass, so the effective maximum passing payload is 75000
bytes. A 75000-byte prompt passes the token estimator, 75001 bytes fails the
token limit, 98304 bytes fails the token limit even though it reaches only the
byte ceiling, and 98305 bytes fails both. Either failure blocks before channel
creation/provider dispatch. There is no full-context fallback. When provider
usage is available, it is recorded as an observation but does not replace
deterministic admission.

### Duplicate Reads And Regression Count

The proof Integration plan injects no target files and no task JSONL manifests.
The reviewer receives only the serialized proof brief. A clean proof verdict
must not declare reviewer source probes. Deterministic commands are reused from
the current evidence key and never rerun by the semantic reviewer. The final
Integration deterministic set owns exactly one post-feature full regression and
records `integration_full_regression_count=1`. Baseline prerequisite
compatibility runs are separate evidence and do not increment this counter.

## RT-VERDICT-EVIDENCE

### Owned Paths

- `guru-template/overlay/verify/guru_review_record.py`
- `guru-template/overlay/verify/tests/test_integration_verdict_retry.py`

### Retry Evidence

The existing official `implementation-reviews.jsonl` schema remains unchanged.
A separate task-local append-only stream owns formatting-retry audit events:

```text
review-records/implementation-review-format-retries.jsonl
review-records/implementation-review-format-retries/<run-id>-semantic.txt
review-records/implementation-review-format-retries/<run-id>-serialization.txt
```

Each JSONL event uses schema version 1 and records event kind, run ID, review
target, provider, `RetryIdentity`, raw artifact path/digest, attempt number,
status, and timestamp. Artifact names are derived from validated run IDs,
created atomically, and never overwritten.

### Retry State Machine

```text
semantic worker returns with unchanged read-only snapshot
  -> verdict valid: append one official normalized review
  -> retryable formatting failure:
       persist immutable semantic raw + retry event
       build serialization-only plan with files=[] and jsonls=[]
       include only raw output, invocation metadata, and envelope contract
       permit exactly one provider retry
       -> valid: persist serialization raw + append normalized official review
       -> invalid/error: persist failure event + append one final blocked row
  -> semantic finding or non-retryable malformed output:
       append the existing official finding/blocked row; no formatting retry
```

A retry is formatting-only only when the semantic worker completed, the
read-only snapshot is unchanged, deterministic evidence is passed/current, the
raw output has no semantic finding route, and the expected invariant set can be
recovered without reading source. Missing semantic evidence, repeated
deterministic probes, snapshot drift, provider failure, or changed digests are
not retryable.

The serialization-only plan has `files=[]` and `jsonls=[]`; it receives the raw
semantic output, fixed invocation metadata, `RetryIdentity`, proof-bundle
digest, expected invariant IDs, and the envelope contract only. It cannot use
repository tools or add semantic findings. Its provider invocation increments
the formatting-retry counter but not the semantic-reviewer counter.

## Receipt Compatibility

No Gate production change is planned. Existing receipt schema version 1 and
append-only histories remain valid.

`_validate_slice_receipt` already recomputes each slice's current component
digests and excludes current supervisor file digest from ordinary currentness.
The final Gate separately binds only the Integration receipt to current
supervisor source. Tests must prove:

- changing one ordinary component stales only its owner receipt
- unchanged sibling receipts remain current
- Integration becomes stale through the changed dependency receipt
- a supervisor runtime change requires only a new Integration receipt

## RT-INTEGRATION-PROOF

### Owned Paths

- `guru-template/overlay/tests/integration_proof_runtime_test.sh`
- exact package peers generated by that bounded test for the three runtime
  files, the existing lifecycle test, the two new focused test files, and the
  bounded test itself

The Integration child does not modify ordinary canonical runtime bytes. Its
bounded `--sync` table contains only task-owned runtime/test pairs, validates the
canonical-to-package mapping, copies without deletion, and checks byte equality.
It does not run full `sync:guru`.

### Final Proof

- both ordinary child receipts are current
- mutable ordinary overlap is zero
- package peers equal canonical bytes
- focused context tests pass
- verdict retry tests pass
- existing full slice lifecycle regression passes exactly once in the final
  post-feature Integration wave
- Small/Micro/Lite/non-Full/v1 compatibility tests pass
- one real Full/high Integration fixture records payload/reviewer/read/regression
  metrics and a structured verdict
- GitNexus `detect-changes`, `git diff --check`, formal review, local commit, and
  receipt complete in the control worktree

## Failure Routing

| Failure | Owner |
| --- | --- |
| package/canonical baseline differs after copy | RT-BASELINE-PARITY |
| stale/missing ordinary receipt | direct ordinary receipt owner |
| ordinary canonical staged during Integration | RT-PROOF-SUPERVISOR admission |
| peer missing, ambiguous, or unequal | RT-INTEGRATION-PROOF bounded sync |
| final prompt over either budget | RT-PROOF-SUPERVISOR |
| duplicate body/probe or repeated deterministic command | RT-PROOF-SUPERVISOR |
| retry identity drift | new semantic snapshot; no reuse |
| retry artifact or event invalid | RT-VERDICT-EVIDENCE |
| serialization retry fails once | one final official blocked verdict |
| receipt sibling incorrectly staled | compatibility regression; no Gate schema workaround |
| full lifecycle regression fails | responsible ordinary child, then rerun Integration |

## Rollback

Each child has an independent commit. Revert Integration mirrors/tests first,
then revert the responsible ordinary runtime child. The baseline parity commit
may remain because it does not change package runtime behavior. Reverting the
baseline while keeping later runtime children is prohibited because it restores
dual source-of-truth drift.
