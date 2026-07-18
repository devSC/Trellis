# Full/High Integration Proof Supervisor

### UNIT-proof-supervisor

## 单元职责 (Unit Responsibility)

Owns BHV-001, BHV-002, BHV-003, and BHV-006 for eligible Full/high v2
Integration review: deterministic admission, proof projection, final prompt
budgets, provider orchestration, and legacy-route isolation.

## 行为定义 (Behavior Definition)

Behavior list (行为清单):

- BHV-001 replaces current ordinary/mirror bodies with receipt and digest proofs.
- BHV-002 measures and hard-enforces the complete serialized prompt budget.
- BHV-003 starts exactly one semantic reviewer per snapshot.
- BHV-006 preserves every ineligible route and existing provider/Gate contract.

## 核心数据结构 (Core Data Structures)

Consumes `IntegrationProofBundle`, `OrdinaryReceiptProof`,
`GeneratedPeerProof`, `RetryIdentity`, and the frozen review-record operations.
Stable compact serialization and domain-separated digests bind the complete
proof before provider dispatch.

GURU-DECISION:DEC-BUDGET-001

GURU-DECISION:DEC-SCOPE-001

GURU-DECISION:DEC-TOKEN-001

## 逐行为设计 (Per-Behavior Design)

1. Require the exact eligibility tuple and current staged Integration target.
2. Validate all dependency receipts with existing Gate helpers.
3. Compute the ordinary target union and reject ordinary canonical writes.
4. Project equal peers and bounded requirements/design/deterministic evidence.
5. Include only the Integration-owned diff and exact packet invariant rules.
6. Serialize the complete proof brief and enforce both budgets.
7. Dispatch one semantic reviewer with zero file/JSONL injections.
8. Use the frozen review-record API and, only when allowed, dispatch one
   serialization-only request with no source tools.

## 状态/边界 (State And Boundary)

Requires a current baseline receipt. Owns only canonical `guru_supervise.py` and
its focused test. Gate and review-record modules are read-only. Eligibility false
uses existing behavior; malformed eligible input fails closed without fallback.

## 数据合同 (Data Contract)

Final admission requires `payload_bytes <= 98304` and
`ceil(payload_bytes / 3) <= 25000`. Missing/stale receipts, ambiguous/unequal
peers, unsafe paths, whole-file selectors, incomplete invariants, or changed
snapshot digests are invalid.

Both limits apply simultaneously: 75000 bytes passes, 75001 bytes fails the
token limit, 98304 bytes fails the token limit, and 98305 bytes fails both.

## 失败收口 (Failure Closure)

Stale receipt returns to its direct owner. Peer mismatch returns to Integration.
Over-budget, duplicate body/read, unsafe target, and premature provider dispatch
return to this unit. Identity drift creates a new semantic snapshot rather than
reusing retry evidence.

## 测试映射 (Test Mapping)

- eligibility and legacy-route compatibility
- receipt, union, overlap, peer, selector, and invariant admission
- exact projection omission/inclusion
- byte/token boundary and zero-dispatch failures
- one semantic call, zero duplicate reads/probes, and one serialization-only call

## 不得补造清单 (No-Invention List)

Do not add TypeScript commands, receipt schema, provider, tokenizer dependency,
full-context fallback, Gate production logic, or a new production Python module.

## Deletion Audit

No existing review path is deleted. The proof branch is additive and bounded;
rollback removes the branch and focused test together.
