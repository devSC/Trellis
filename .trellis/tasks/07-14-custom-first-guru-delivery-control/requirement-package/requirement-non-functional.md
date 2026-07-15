# Non-functional Requirements

## Reliability

- Filesystem lifecycle operations are crash-recoverable, idempotent and ownership-preserving.
- Gate and worker state transitions use current digest/scope CAS and a single-run lock.
- Budget expiry produces a terminal report; it never downgrades or skips a Gate.

## Performance And Cost

- TTFC applies only to implementation intent; other intents declare a route-specific first-value metric.
- Benchmark reports cold and warm runs separately using planning time, canonical context bytes and provider uncached+cached input-token telemetry as independent mandatory proxies; unavailable token telemetry blocks the comparison instead of becoming zero or being replaced by another proxy.
- The <=70% reuse rule applies independently to declared proxies and uses a documented minimum cold-baseline floor to avoid meaningless ratios.

## Security And Trust

- No secret value is stored in planning, install state or logs.
- Confirmation/reviewer identity binds trusted platform/TTY evidence, task, scope and artifact digest.
- Agent-authored strings and run ids are not authorization or independence proof.

## Compatibility

- Existing stable Template ids remain resolvable.
- The functional phase adds no Guru-specific Trellis Core/SDK API.
- Existing SDK Guru remains a temporary compatibility surface, never a silent runtime fallback.
- Precisely fingerprinted unchanged/reduced legacy v1 debt may be non-blocking only for the independent Custom-v2 release domain; it is never green and never proves fork SDK/npm readiness, while any new/changed failure or frozen-owner drift blocks.

## Observability

- Evidence records include version, digest, duration, invalidation reason and terminal state.
- Missing metrics are explicit `unknown` values.
- Source, template and installed-state drift is attributable to one owner and one recovery action.
