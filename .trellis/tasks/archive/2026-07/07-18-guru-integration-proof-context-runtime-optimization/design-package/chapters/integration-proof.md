# Integration Runtime Proof And Package Parity

### UNIT-integration-proof

## 单元职责 (Unit Responsibility)

Owns BHV-005 and BHV-008 and supports BHV-001 through BHV-007 by generating
seven exact package peers, proving combined compatibility/currentness, recording
performance counters, and completing Integration-last review/commit/receipt.

## 行为定义 (Behavior Definition)

Behavior list (行为清单):

- BHV-005 proves direct-owner receipt invalidation remains selective.
- BHV-008 records prompt, token, reviewer, read/probe, projection, retry,
  regression, and invalidation metrics from a real Full/high fixture.

## 核心数据结构 (Core Data Structures)

The bounded pair table contains the three runtime files, lifecycle test, two new
focused tests, and the Integration Shell test. The Integration packet depends on
both ordinary receipts and separates review coverage from exact write ownership.

## 逐行为设计 (Per-Behavior Design)

1. Require both ordinary receipts current and no ordinary canonical staged diff.
2. Run bounded `--sync` over the closed seven-pair table without deletion.
3. Prove byte equality and reject any table-external write.
4. Run focused, retry, currentness, and legacy compatibility suites.
5. Run the post-feature full lifecycle regression exactly once and record
   `integration_full_regression_count=1`.
6. Run one real Full/high v2 proof fixture and capture all acceptance metrics.
7. Complete one official Integration semantic review, local commit, receipt, and
   final no-slice Gate in the control worktree.

## 状态/边界 (State And Boundary)

This unit runs only after both ordinary formal receipts are current. It owns the
canonical bounded Shell test and seven exact package peers. All ordinary
canonical runtime/test bytes are read-only during Integration.

## 数据合同 (Data Contract)

Each peer maps from the canonical suffix under the existing template roots. The
table rejects missing, ambiguous, unequal, duplicate, external, or deleted
paths. Full repository sync is not an acceptance command.

## 失败收口 (Failure Closure)

Receipt staleness returns to the direct owner. Prompt/projection failure returns
to the supervisor. Retry evidence failure returns to review-record. Peer or final
composition failure remains here. After any repair, publish a new Integration
proof without refreshing unchanged sibling receipts.

## 测试映射 (Test Mapping)

- bounded sync and read-only parity, including deletion/external-path negatives
- focused supervisor and verdict suites
- direct-owner/sibling/Integration receipt currentness
- Small/Micro/Lite/non-Full/v1 compatibility
- exactly one post-feature Integration full lifecycle regression and one
  semantic reviewer
- real Full/high metrics and final `git diff --check`

## 不得补造清单 (No-Invention List)

Do not edit ordinary canonical bytes, run full `sync:guru`, repeat full
regression, add a second reviewer, or push/merge/archive/install/canary/finish.

## Deletion Audit

No deletion is planned. Bounded sync copies only declared pairs and blocks any
generated deletion or external baseline write.
