# Non-functional Requirements

## Reliability

- Filesystem lifecycle operations are idempotent and ownership-preserving. Trappable failures recover automatically when exact ownership is provable; power loss, `SIGKILL` or restore I/O failure retains an external preimage and one explicit manual-recovery action.
- Gate and worker state transitions use current digest/scope CAS and a single-run lock.
- Budget expiry produces a terminal report; it never downgrades or skips a Gate.

## Performance And Cost

- TTFC applies only to implementation intent; other intents declare a route-specific first-value metric.
- Benchmark reports cold and warm runs separately using planning time, canonical context bytes, model/tool cycles and provider token telemetry when available.
- Unavailable provider token telemetry remains `unknown`; a separately labelled controllable token-budget proxy may be reported but must not be presented as actual billing or provider-token reduction.
- The <=70% reuse rule applies independently to available controllable proxies and uses a documented minimum cold-baseline floor to avoid meaningless ratios.

## Security And Trust

- No secret value is stored in planning, install state or logs.
- This is a self-use local workflow, not a hostile local-bundle security boundary.
- Confirmation evidence binds task, scope and artifact digest for workflow correctness; it is not a cryptographic authorization claim.
- Provider/context provenance is recorded honestly. Agent-authored strings, same-provider contexts and run ids are not independence proof.

## Compatibility

- Existing stable Template ids remain resolvable.
- The functional phase adds no Guru-specific Trellis Core/SDK API.
- Existing SDK Guru remains a temporary compatibility surface, never a silent runtime fallback.
- Precisely fingerprinted unchanged/reduced legacy v1 debt may be non-blocking only for the independent Custom-v2 release domain; it is never green and never proves fork SDK/npm readiness, while any new/changed failure or frozen-owner drift blocks.

## Observability

- Evidence records include version, digest, duration, invalidation reason and terminal state.
- Missing metrics are explicit `unknown` values.
- Source, template and installed-state drift is attributable to one owner and one recovery action.
