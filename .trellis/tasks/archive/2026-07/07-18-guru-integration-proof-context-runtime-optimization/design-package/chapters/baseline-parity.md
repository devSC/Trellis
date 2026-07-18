# Canonical Runtime Baseline Parity

### UNIT-baseline-parity

## 单元职责 (Unit Responsibility)

Owns BHV-007 canonical source restoration. It copies the currently executed
package bytes for the three runtime modules and lifecycle test to canonical,
without changing package behavior.

## 行为定义 (Behavior Definition)

Behavior list (行为清单): BHV-007 requires one authoritative canonical runtime
before descendant feature work starts.

## 核心数据结构 (Core Data Structures)

The closed copy table contains four source/destination pairs and pre/post SHA-256
digests. Package paths are sources and read-only; canonical paths are destinations
and the only mutable ownership.

## 逐行为设计 (Per-Behavior Design)

1. Record package and canonical pre-copy digests.
2. Run the current package lifecycle regression.
3. Copy exact package bytes to the four canonical paths.
4. Compare every pair byte for byte and compile all runtime modules.
5. Run both canonical and package lifecycle entrypoints and prove package paths
   have no diff from the pre-copy package snapshot.

## 状态/边界 (State And Boundary)

This serial prerequisite has no dependency. Neither ordinary child is
dispatchable until its formal local commit and current receipt exist. It does not
run full sync and does not repair behavior.

## 数据合同 (Data Contract)

Input is the current package snapshot at the parent's planning digest. Output is
four byte-identical canonical files. Any extra input/output path is invalid.

GURU-DECISION:DEC-BASELINE-001

## 失败收口 (Failure Closure)

Package drift, pre/post lifecycle failure, missing pair, unequal digest, or extra
changed path blocks the child and returns to baseline planning. No feature repair
is allowed here.

## 测试映射 (Test Mapping)

- canonical and package lifecycle entrypoints
- canonical and package `py_compile`
- four exact byte comparisons
- package-diff absence and `git diff --check`

The prerequisite compatibility executions are recorded separately from the
final `integration_full_regression_count`, which is owned by Integration.

The baseline copy diff is expected to be approximately 448876 bytes. Its formal
review uses the one-time 589824-byte Full planning allowance; it is not evidence
that the new proof Integration prompt may exceed its own hard budgets.

## 不得补造清单 (No-Invention List)

Do not edit package runtime, add a migration command, run full `sync:guru`, add a
schema, or absorb unrelated drift.

## Deletion Audit

No deletion is planned. A missing source/destination or deletion blocks.
