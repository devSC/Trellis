# Custom-first Guru Delivery Control Plane Design Package

## Status

- Task: `07-14-custom-first-guru-delivery-control`
- Chain: `full`
- Risk: `high`
- Requirements source: `../prd.md`
- Formal requirements package: [`../requirement-package/`](../requirement-package/)
- Overview SSOT: [`design-main.md`](design-main.md)
- Package manifest: [`manifest.json`](manifest.json)
- Implementation plan: `../implement.md`

Lifecycle status is `in_progress`. Earlier Requirements and Detail confirmations exist, but this final consistency batch changes the canonical Requirements/Overview/Detail digests; current batch reviews and one user reconfirmation are therefore required before any additional slice dispatch or bootstrap burn. Existing `in_progress` state is historical lifecycle fact, not authorization to bypass current Gate evidence.

The first ten chapters were created before the required current Overview reviews. That historical P5/G7 order violation is preserved as a migration exception in `design-main.md` §11.1; it must be compensated by the declared review batches and must never be represented as method evidence or a passed chapter status.

The immutable historical verified-consumed bootstrap source is archived at `bootstrap/archive/bootstrap_start.e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3.py` with SHA-256 `e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3`. The live chain contains exactly `prepared -> consumed(failed_compensated) -> retry_prepared -> retry_consumed(verified)` and no `burned` event. The current hardened verifier is `bootstrap/bootstrap_start.py`; it may validate status and, only after all current Gate/review/risk/envelope/capability evidence is rebuilt, append the permanent burn. Burn requires the task to remain `in_progress`, one run-derived official Codex channel/session lineage, an exact pre-launch digest/invocation contract, canonical equality between the captured final Worker verdict and the selected review record, and equal pre/post/index/worktree/final digests. Its Codex-only same-provider review authorization is audit-only migration evidence and is not eligible for V2 independent review. No further bootstrap `run` is legal.

Current slice packet aggregation facts: 6 packets, 65 unique target paths, 56 invariant triples and 0 target overlap. The read-only aggregate still reports per-slice `SCOPE_INVALID` because a shared dirty worktree contains other slice and task-local bootstrap/review outputs; this must be resolved by isolated review/snapshot evidence, never hidden in `dirty_state.unrelated`. `release_checks` remain final-release-only evidence and must not be loaded into routine slice semantic review or local deterministic check loops.

## Navigation

| Area | Artifact | Trace scope |
| --- | --- | --- |
| Architecture and ownership | [`design-main.md`](design-main.md) | BHV-001 through BHV-007 |
| Official marketplace catalog | [`chapters/marketplace-catalog.md`](chapters/marketplace-catalog.md) | UNIT-marketplace-catalog |
| Reversible extension lifecycle | [`chapters/extension-manager.md`](chapters/extension-manager.md) | UNIT-extension-manager |
| Route and budget policy | [`chapters/delivery-policy.md`](chapters/delivery-policy.md) | UNIT-delivery-policy |
| Semantic dependency digests | [`chapters/semantic-digest.md`](chapters/semantic-digest.md) | UNIT-semantic-digest |
| Independent review evidence | [`chapters/review-identity.md`](chapters/review-identity.md) | UNIT-review-identity |
| Bounded orchestration | [`chapters/bounded-supervisor.md`](chapters/bounded-supervisor.md) | UNIT-bounded-supervisor |
| Core-free start enforcement | [`chapters/start-guard.md`](chapters/start-guard.md) | UNIT-start-guard |
| Delta context and reuse | [`chapters/context-reuse.md`](chapters/context-reuse.md) | UNIT-context-reuse |
| Design and implementation sync | [`chapters/design-sync.md`](chapters/design-sync.md) | UNIT-design-sync |
| End-to-end release benchmark | [`chapters/replay-benchmark.md`](chapters/replay-benchmark.md) | UNIT-replay-benchmark |

## Source Of Truth Rules

1. `design-main.md` owns system boundary, behavior ownership, shared control flow and chapter routing.
2. Each file under `chapters/` owns one UNIT contract and its BHV/test mapping.
3. `../design.md` is only a task-local pointer and summary; it must not duplicate normative design details.
4. `../implement.md` owns delivery slices and verification order, not architecture decisions.
5. Approved behavior meaning remains in `../prd.md`; design artifacts may map or refine it but may not redefine it.
