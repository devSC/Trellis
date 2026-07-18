# Guru Integration Proof Runtime Design Package

## Status

- Route: Full/high.
- Role: formal design SSOT for the parent delivery graph.
- Runtime boundary: existing Python lifecycle modules only; no TypeScript command.
- Lifecycle: baseline first, two ordinary runtime children may implement in
  parallel, formal review/commit/receipt remains serial, Integration runs last.

## Navigation

| Area | Artifact | Trace |
| --- | --- | --- |
| Architecture, ownership, and frozen contracts | [`design-main.md`](design-main.md) | BHV-001..BHV-008 |
| Canonical baseline parity | [`chapters/baseline-parity.md`](chapters/baseline-parity.md) | UNIT-baseline-parity |
| Proof context and dispatch | [`chapters/proof-supervisor.md`](chapters/proof-supervisor.md) | UNIT-proof-supervisor |
| Retry evidence and normalization | [`chapters/verdict-evidence.md`](chapters/verdict-evidence.md) | UNIT-verdict-evidence |
| Generated peers and final proof | [`chapters/integration-proof.md`](chapters/integration-proof.md) | UNIT-integration-proof |
| Execution and rollback order | [`../implement.md`](../implement.md) | RT-BASELINE-PARITY..RT-INTEGRATION-PROOF |

The predecessor follow-up document is historical product evidence. This design
package and the parent PRD/implement plan are the current planning authority.
