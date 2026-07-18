# Integration Verdict Retry Evidence

### UNIT-verdict-evidence

## 单元职责 (Unit Responsibility)

Owns BHV-004: retry identity, formatting-failure classification, immutable raw
artifacts, append-only retry events, and final official normalization.

## 行为定义 (Behavior Definition)

Behavior list (行为清单): BHV-004 permits one formatting-only provider retry
only for an unchanged semantic snapshot and publishes no intermediate official
blocked row.

## 核心数据结构 (Core Data Structures)

`RetryIdentity` contains all target, invariant, requirements/design,
deterministic, policy, supervisor, and proof-bundle digests. Retry events use
schema version 1 and bind run metadata, identity, immutable artifact path/digest,
attempt, status, and timestamp.

GURU-DECISION:DEC-RETRY-AUDIT-001

GURU-DECISION:DEC-RETRY-LIMIT-001

## 逐行为设计 (Per-Behavior Design)

1. Validate the exact identity field set and compute a domain-separated digest.
2. Classify output as valid, retryable format, semantic finding, or non-retryable.
3. Atomically persist raw semantic output and append its event before retry.
4. Permit one serialization-only attempt for the same identity.
5. Persist retry output and append one normalized official row on success or one
   final blocked row on failure.
6. Preserve existing normalization for all legacy inputs.

## 状态/边界 (State And Boundary)

Requires a current baseline receipt. Owns only canonical
`guru_review_record.py` and its focused test. It never dispatches a provider,
reads repository source, reruns deterministic commands, or edits Gate runtime.

## 数据合同 (Data Contract)

Retry artifacts live under the current task's validated retry-evidence directory.
Run IDs determine names; path escape, overwrite, duplicate name, malformed event,
identity mismatch, or attempt greater than one is rejected.

## 失败收口 (Failure Closure)

Semantic finding, provider failure, missing invariant evidence, snapshot drift,
or changed digest is non-retryable. A failed sole serialization retry produces
one final official `MALFORMED_REVIEW_OUTPUT` row and stops.

## 测试映射 (Test Mapping)

- stable identity and tamper rejection
- atomic artifacts, replay, overwrite, and path-escape rejection
- classification matrix and retry limit
- normalized success, final blocked failure, and legacy compatibility
- exact official-row and append-only event counts

## 不得补造清单 (No-Invention List)

Do not add receipt schema version 2, a second official review stream, provider
orchestration, source probing, or artifact deletion.

## Deletion Audit

No evidence is deleted or overwritten. Rollback leaves historical raw/retry
artifacts readable.
