# Guru Overlay Gates

> Executable contract for Guru risk routing, task-local gate contracts, degradation evidence, adversarial review config, and commit-gate behavior.

---

## Scenario: Risk-Based Gate Contract Routing

### 1. Scope / Trigger

Apply this spec when editing Guru template files under:

- `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_contract.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/hooks/guru_after_create.py`
- Matching `guru-template/**` mirror files

This is an executable gate surface. Changes must be fail-closed by default, mirrored between source/template trees, and covered by Guru verify tests.

### 2. Signatures

- Intake helper output:
  - `risk`: `low | medium | high | unknown`
  - `route`: recommended intake route, `small_inline | micro_task | lite_task | full_chain`
  - `confidence`: number
  - `reasons`: string array
  - `risk_flags`: string array
  - `needs_user_choice`: boolean
  - `recommended_contract`: route string
  - Runtime selection lives in `gate-contract.json.route`; recommendation fields must not force the selected route.

- Intake command:
  - `python3 guru_gate.py intake [task_dir] --description <text> [--path <path> ...] [--staged] [--commit-requested] [--write-contract]`
  - Without `task_dir`, the command must not bind to the active task; it only emits the route recommendation and suggested commands for the current request.
  - With `--write-contract`, an explicit task directory is required for `micro_task`, `lite_task`, or `full_chain`; the command writes `gate-contract.json` and updates task route metadata.
  - `small_inline` has no commit contract. If commit is requested, intake must route to `micro_task`.

- Task-local contract files:
  - `gate-contract.json`
  - `gate-degradations.jsonl`
  - `gate-evidence/`

- Contract generation:
  - `python3 guru_gate.py init-contract <task_dir> --route <route> --risk <risk> [--recommended-route <route>] [--user-override-quote <quote>] [--risk-acknowledged true] [--selected-by user] [--allowed-path <path> ...] [--max-files <n>]`
  - The command must call `guru_contract.default_contract()`, validate the result, and write `gate-contract.json` atomically or through the shared contract writer.
  - The command must reject invalid raw risk strings, invalid route names, non-positive max file limits, invalid micro scopes, and lower-than-recommended selected routes that lack user override audit.

- Degradation recording:
  - `python3 guru_gate.py record-degradation <task_dir> --gate <gate> --reason <reason> --command <cmd> [--stderr-excerpt <text>] [--allowed-by <json-pointer>] --check <name:status[:evidence]> ...`
  - The command must require an explicit task directory, load the current `gate-contract.json`, validate the proposed row plus existing `gate-degradations.jsonl`, and only then append.
  - Invalid rows must not be appended. Missing compensating checks, unauthorized gates, required-gate degradation, or high/full-chain degradation must fail closed.

- Full-chain slice planning:
  - `python3 guru_gate.py slice-plan <task_dir>`
  - The command emits read-only JSON summarizing whether a slice packet is required, available packets, dirty scope, blocking reasons, and recommended per-slice implement commands.
  - For `route=full_chain` and `risk=high`, `check-implementation` and `guru_supervise.py implement-check` must fail before worker launch when no slice packet exists.
  - Missing or invalid contracts on legacy tasks must not force packet creation by themselves; legacy full-chain strict behavior is preserved unless the task explicitly resolves to high-risk full-chain.

- Commit gate:
  - `python3 guru_gate.py check-commit [task_dir]`

- Check-only required implementation review:
  - `python3 guru_supervise.py implementation-review <task_dir> [--slice <unit_id>] [--staged]`
  - This command is the commit-safe producer of required structured implementation review records. It must run deterministic checks plus the check worker, must not launch an implement worker, and must not edit confirmed detail artifacts.

- Commit plan:
  - `python3 guru_gate.py commit-plan [task_dir] [--write]`
  - Without `--write`, the command is read-only stdout JSON.
  - With `--write`, it writes task-local `commit-plan.json` as mutable evidence and keeps stdout JSON identical to the written file.

- Worker status:
  - `python3 guru_supervise.py status <task_dir> [--json]`
  - JSON mode must distinguish `live_workers` from `terminal_workers`; terminal `done|killed|error` workers must not make `blocking=true`.
  - Cleanup must be exposed as one cleanup command plus structured cleanup candidates.

- Configuration key:
  - `.trellis/config.yaml` path: `guru.supervision.adversarial_enabled`
  - Default: `true`
  - `false` disables the adversarial reviewer requirement only.
  - `.trellis/config.yaml` path: `guru.supervision.high_risk_review_provider_policy`
  - Allowed values: `current | opposite | codex | claude`; only an absent key defaults to `current`.
  - For high-risk slice-backed implementation review, precedence is audited `--same-provider --user-quote` > project policy > packet provider metadata. Low-risk slices and non-slice staged/contract review retain their packet contracts.
  - Explicit null, empty, whitespace-only, non-string, or unknown policy values fail before worker-plan construction.

- Route-aware review policy:
  - `small_inline`: no task-local requirements adversarial review is required; if the work later needs commit, create/route to `micro_task`.
  - `micro_task`: requirements adversarial review and overview/detail adversarial reviewer evidence are not required; commit remains bounded by explicit scope, file limits, and contract evidence. It is never valid for high-risk work.
  - `lite_task`: bounded review policy. Requirements adversarial review is optional, and overview/detail still require two current-digest clean review run ids but do not require an adversarial reviewer. Current blocked/malformed/medium+ review evidence remains blocking.
  - `full_chain`, `risk=unknown`, or missing/invalid contract: strict default policy. Requirements review is required when `adversarial_enabled=true`, and overview/detail require at least one counted adversarial clean review.

### 3. Contracts

`gate-contract.json` must contain:

- `schema_version`: current integer schema version.
- `risk`: normalized risk, with unknown raw strings rejected during validation.
- `route`: selected runtime/commit route. `small_inline` is not a valid commit contract.
- `assessment.recommended_route`: normalized recommendation derived from risk assessment, for example `full_chain`.
- `route_selection`: selection audit block containing `selected_route`, `source`, `recommended_route`, `risk_acknowledged`, `user_quote`, `selected_by`, and `selected_at`.
- `scope.allowed_paths`: explicit non-empty paths for `micro_task`; repo root is not allowed for `micro_task`.
- `scope.max_files`: positive integer for `micro_task`.
- `allowed_degradations`: rows with `gate` and non-empty `fallback_checks`.
- `commit_policy.allow_task_artifacts_only`: defaults false.

High-risk contracts must select `route=full_chain`. A `route_selection` user
override audit is evidence of the user's preference, not permission to run
high-risk work through `lite_task`, `micro_task`, or `small_inline`.

When non-high-risk work selects a `route` less strict than the recommended
route, the contract must include a valid user override audit:
`route_selection.source=user_override`, `route_selection.selected_by=user`,
`route_selection.risk_acknowledged=true`, a non-empty
`route_selection.user_quote`, a non-empty `route_selection.selected_at`, and a
valid stricter `route_selection.recommended_route`. Missing or invalid audit
blocks. The audit cannot override the high-risk `full_chain` requirement.

`gate-degradations.jsonl` is append-only evidence, not permission and not route
selection. Permission comes from global policy plus the current contract. Each
row must identify the gate and include passed compensating checks required by
the contract.

`task.json.guru_chain` remains the legacy artifact-shape selector `full | light`. New route names use `lite_task`; do not introduce a new light-prefixed task route.

`init-contract` is the preferred writer for task-local gate contracts. Handwritten
contracts are allowed only when they validate through the same validator. The
writer must not silently preserve an invalid existing contract, and an unreadable
existing contract must fail closed instead of being overwritten.

`slice-plan` is a runtime summary, not a planning contract. It must not edit
`prd.md`, `design.md`, `implement.md`, review records, confirmations, or gate
contracts. Dirty scope is advisory for planning and blocking when it proves the
selected packet is not isolated.

Route policy may relax only adversarial reviewer requirements. It must not bypass
requirements/detail human confirmations, current-digest checks, structure gates,
medium+ findings, blocked requirements evidence, staged-scope validation, or
implementation review digest checks. `adversarial_enabled=false` has the same
limited scope: it removes the adversarial reviewer requirement only and never
turns current blocked or medium+ evidence into clean evidence.

Low-severity clean evidence is clean evidence. Review output with
`max_severity=none|low` and no blocker/finding class may count as clean/current.
For `lite_task`, low/P3 follow-ups and wording nits should be tracked as
follow-ups without forcing a PRD digest refresh and requirements re-review,
unless they change behavior, scope, acceptance criteria, or a high-risk decision.

Lite scope expansion must stop for user confirmation. If review or supervision
finds that a `lite_task` now touches high-risk areas, additional layers, or
scope beyond the confirmed route/contract, it must ask the user whether to keep
the non-high-risk route with updated audit, expand the non-high-risk contract,
or promote to `full_chain`; high-risk expansion must promote to `full_chain`.
It must not silently rewrite `evidence_ready` or assumptions as `user_confirmed`.

### 4. Validation & Error Matrix

| Condition | Behavior |
| --- | --- |
| Missing contract on existing full-chain tasks | Preserve existing strict full-chain behavior |
| Malformed contract JSON or non-object root | Block commit |
| Raw risk typo such as an unknown word | Block contract validation |
| `small_inline` used for commit | Block and require `micro_task` |
| `micro_task` without explicit allowed paths | Block |
| `micro_task` with repo-root scope | Block |
| `micro_task` without positive `max_files` | Block |
| High-risk work with non-`full_chain` selected route and no valid `route_selection` user override audit | Block; high-risk requires `full_chain` |
| High-risk work with non-`full_chain` selected route and valid user override audit | Block; the audit cannot override the high-risk `full_chain` requirement |
| Unauthorized degradation row | Block |
| Empty `fallback_checks` | Block |
| Missing passed compensating checks | Block |
| Staged task/workspace artifact paths | Block for implementation commit contracts |
| Non-full staged path with gate/workflow/storage/privacy/payment signal and no valid user override audit | Block and recommend `full_chain` |
| Non-full staged path with gate/workflow/storage/privacy/payment signal inside confirmed scope and valid user override audit | Block when the contract risk is high; otherwise stop for user confirmation or promote to `full_chain` |
| `adversarial_enabled=false` with current blocked requirements review | Block |
| `adversarial_enabled=false` with missing adversarial reviewer only | Allow if other current clean-review/digest gates pass |
| `micro_task` with no requirements adversarial review | Allow; continue enforcing structure/confirmation only when that command is explicitly used |
| `lite_task` with no requirements adversarial review | Allow under bounded policy if risk is known and no current blocked/malformed/medium+ requirements evidence exists |
| `lite_task` with two ordinary clean overview/detail reviews and no adversarial reviewer | Allow under bounded policy |
| `lite_task` with current requirements `blocked` or clean `max_severity=medium+` | Block |
| `lite_task` review discovers high-risk or expanded scope | Stop for user confirmation; do not silently promote evidence-ready scope to user-confirmed |
| `risk=unknown` or invalid `gate-contract.json` | Strict default policy; do not apply route-aware adversarial relaxation |
| `init-contract --risk high --route lite_task|micro_task` without user override quote and `--risk-acknowledged true` | Block; high-risk requires `full_chain` |
| `init-contract --risk high --route lite_task|micro_task` with valid user override audit and valid selected-route scope | Block; high-risk requires `full_chain` |
| `init-contract` sees unreadable existing contract | Block; do not overwrite ambiguous state |
| high-risk selected `full_chain` implementation without slice packet | Block before worker launch with `PACKET_REQUIRED_BEFORE_IMPLEMENT` |
| high-risk selected `lite_task` with valid user override audit | Treat the contract as invalid and require `full_chain` before implementation |
| high-risk selected `full_chain` with one valid slice packet | Allow implementation preflight and expose recommended `--slice <id>` command |
| high-risk selected `full_chain` with multiple packets and no selected slice | Report `PACKET_AMBIGUOUS_WITHOUT_SLICE` in `slice-plan` |
| `status --json` sees only terminal workers | Return `blocking=false`, `cleanup_available=true` |

### 5. Good/Base/Bad Cases

- Good: a low-risk single-path UI/text change uses `micro_task` only when commit is requested, with explicit scope, positive `max_files`, and deterministic compensating checks for optional GitNexus degradation.
- Good: a high-risk request is recommended `full_chain`, and `gate-contract.json` records `route=full_chain` even if the user asked for a lower route.
- Good: a high-risk `micro_task` or `lite_task` user override is rejected before commit, check-implementation, or slice-plan can treat it as selected-route authority.
- Good: a high-risk full-chain runtime task writes a slice packet before implementation, runs `slice-plan`, then launches one explicit slice.
- Base: a task without `gate-contract.json` follows the existing full-chain `check-implementation` plus implementation-review digest and staged-scope checks.
- Bad: a task-local degradation row claims a required semantic review or commit gate can be skipped. Required gates are globally non-degradable and must fail closed.
- Bad: a high-risk task selects `lite_task` or `micro_task`, with or without user quote or explicit risk acknowledgement.
- Bad: a high-risk full-chain task starts an implementation worker before any slice packet exists.

### 6. Tests Required

Guru overlay verify tests must cover:

- Low request with no paths is not `small_inline`; it must route to medium/lite or require user choice.
- Low plus commit routes to `micro_task`.
- Medium local behavior changes route to `lite_task`.
- Payment, ads, privacy, permission, schema, workflow, hook, gate, runtime, storage, or cross-layer signals route to `full_chain`.
- `intake` without task_dir must not bind the active task; low/no-commit emits `small_inline` and no commit contract.
- `intake --commit-requested --write-contract <task_dir>` writes a valid `micro_task` contract, bounded scope, default optional GitNexus degradation allowances, and task route metadata.
- high-risk `intake --write-contract <task_dir>` writes `full_chain` with no allowed degradations.
- `record-degradation` appends only when the contract allows the gate and all required compensating checks are passed; invalid proposed rows leave the JSONL unchanged.
- Contract validation rejects empty micro scope, repo-root micro scope, risk typos, empty fallback checks, unauthorized degradations, and malformed roots.
- `check-commit` blocks staged task artifacts, out-of-scope staged paths, non-full high-risk paths, high-risk non-full contracts even with valid override audit, and missing compensating evidence.
- `check-commit` rejects high-risk path signals inside confirmed non-full scope when the contract itself is high-risk, even if valid user override audit is present.
- `adversarial_enabled=false` allows double ordinary clean reviews to proceed, but does not bypass current blocked or medium+ review evidence.
- Route-aware review policy: `micro_task` skips requirements adversarial review, `lite_task` bounded review accepts double ordinary clean, and `full_chain` keeps strict gates while only requiring requirements adversarial review when `adversarial_enabled=true`.
- `init-contract` generates valid micro/lite/full contracts and blocks high-risk non-full selected routes even with valid user override audit.
- `check-implementation` and `guru_supervise.py implement-check` block high-risk selected full-chain tasks with no slice packet before worker launch.
- `check-implementation` treats high-risk selected lite/micro contracts as invalid and requires full-chain routing before implementation.
- `slice-plan` covers zero, one, and multiple packet fixtures, including dirty out-of-scope reporting.
- `commit-plan --write` writes `commit-plan.json` identical to stdout JSON.
- `guru_supervise.py status --json` distinguishes live and terminal workers and exposes one cleanup command.
- Source/template mirror pairs are checked with `diff -q`.

### 7. Wrong vs Correct

#### Wrong

```json
{
  "schema_version": 1,
  "risk": "hihg",
  "route": "micro_task",
  "scope": {"allowed_paths": ["."], "max_files": null},
  "allowed_degradations": [{"gate": "implementation_review", "fallback_checks": []}]
}
```

This combines an unknown risk typo, a lower-than-recommended route without valid
user override audit, repo-root scope, missing max file bound, and an attempted
required-gate degradation.

#### Correct

```json
{
  "schema_version": 1,
  "risk": "high",
  "route": "full_chain",
  "assessment": {
    "confidence": 0.9,
    "reasons": ["workflow path touched"],
    "risk_flags": ["workflow"],
    "recommended_route": "full_chain"
  },
  "route_selection": {
    "selected_route": "full_chain",
    "source": "recommended",
    "recommended_route": "full_chain",
    "risk_acknowledged": false,
    "user_quote": "",
    "selected_by": "system",
    "selected_at": "2026-07-02T00:00:00Z"
  },
  "scope": {"allowed_paths": ["packages/cli/src/templates/guru/overlay/verify/guru_gate.py"], "max_files": null},
  "allowed_degradations": [],
  "commit_policy": {
    "require_in_progress": true,
    "require_clean_implementation_review": true,
    "allow_task_artifacts_only": false
  }
}
```

This keeps high-risk work on the full chain, records the recommendation, and
keeps required review gates non-degradable.

---

## Scenario: High-Risk Slice Review Provider Policy

### 1. Scope / Trigger

Apply this contract when changing Guru implementation-review provider
selection, supervision config installation, or required review-record provider
validation. The project policy applies only to high-risk slice-backed reviews.

### 2. Signatures

- Config key: `guru.supervision.high_risk_review_provider_policy`
- Allowed values: `current | opposite | codex | claude`
- CLI override: `implementation-review --same-provider --user-quote <quote>`
- Shared actions: `guru_supervise.py implement-check` and
  `guru_supervise.py implementation-review`

### 3. Contracts

- Only an absent config key defaults to `current`. The config installer writes
  `current` only when the key is absent and preserves every explicit raw value,
  including empty values, so runtime validation remains authoritative.
- High-risk slice precedence is valid quoted CLI override, then project policy,
  then packet provider metadata as audit-only context.
- Low-risk slices retain packet semantics. In particular,
  `opposite(required=true)` requires the opposite provider, while
  `opposite(required=false)` permits the current provider.
- Non-slice staged/contract review retains its synthetic
  `opposite(required=true)` contract unless the valid quoted CLI override is
  present.
- Supervisor records bind `provider_override_source`,
  `same_provider_user_quote`, `high_risk_review_provider_policy`,
  `check_provider`, `implement_provider`, and `review_target_kind` as one tuple.
  Worker `review_provider` must equal the actual `check_provider`.

### 4. Validation & Error Matrix

| Condition | Behavior |
| --- | --- |
| Policy key absent | Resolve `current`; installer may add `current` |
| Explicit null, empty, whitespace, bool, list, or unknown policy | Fail before worker-plan construction; installer must not rewrite it |
| High-risk slice with `current` | `check_provider == implement_provider` |
| High-risk slice with `opposite` | `check_provider != implement_provider` |
| High-risk slice with `codex` or `claude` | Pin the named provider |
| High-risk packet metadata conflicts with project policy | Keep metadata for audit; project policy wins |
| Low-risk packet `opposite(required=false)` | Keep current provider and accept a coherent clean record |
| Low-risk or staged packet `opposite(required=true)` | Require the opposite provider |
| Medium/unknown slice independently requires review | Keep its packet provider contract; do not apply the high-risk project policy |
| Packet risk absent/unknown and task risk is high | Treat the slice as effectively high-risk and apply the project policy |
| Missing CLI quote or inconsistent record tuple | Block before plan or normalize to `MALFORMED_REVIEW_OUTPUT` |

### 5. Good/Base/Bad Cases

- Good: project policy `current` keeps a Codex implementation review on Codex
  even when a high-risk slice packet says `opposite(required=true)`.
- Base: no policy key behaves as `current`, while installer output for a fresh
  project contains an explicit `current` default.
- Bad: installer converts `high_risk_review_provider_policy: ""` to `current`,
  hiding an invalid explicit configuration from runtime validation.
- Bad: record normalization accepts a worker-reported provider that differs
  from the supervisor's actual check provider.

### 6. Tests Required

- Matrix all four policies under current Codex and current Claude.
- Assert absent versus explicit null/empty/whitespace/bool/list/unknown values,
  with no `WORKER=`, `check-*`, or channel spawn plan on invalid config.
- Assert valid CLI override precedence and missing/blank quote rejection.
- Assert high-risk packet conflicts are audit-only, low-risk
  `opposite(required=true|false)` compatibility, medium/unknown packet-contract
  preservation, task-high fallback, and non-slice staged isolation.
- Feed the real resolver context into record normalization and reject tampered
  source/policy/quote/target/provider tuples and worker-provider mismatches.
- Run installer/apply tests proving absent adds `current` while every explicit
  raw value is preserved, then verify dogfood/template/CLI source mirrors.

### 7. Wrong vs Correct

#### Wrong

```yaml
guru:
  supervision:
    high_risk_review_provider_policy: "" # silently rewritten to current
```

#### Correct

```yaml
guru:
  supervision:
    high_risk_review_provider_policy: current
```

An explicitly empty value must remain empty and fail at runtime; only a missing
key may acquire the `current` default.

---

## Scenario: Route-Aware Slice Dispatch and Review Coverage

### 1. Scope / Trigger

Apply this spec when editing Guru high-risk full-chain slice execution,
dispatch backend selection, or implementation review evidence aggregation.

Mandatory triggers:

- `guru_gate.py slice-plan` output shape changes.
- New or changed `guru_supervise.py implement-slices` behavior.
- Changes to direct platform sub-agent vs channel worker dispatch rules.
- Changes to commit-time required implementation review coverage.
- Changes to slice packet safety metadata, resource locks, or target isolation.

This surface is cross-layer workflow infrastructure. It must be fail-closed,
mirrored between `.trellis/scripts/guru`, `guru-template/overlay/verify`, and
`packages/cli/src/templates/guru/overlay/verify`, and covered by Guru verify
tests.

### 2. Signatures

- Read-only slice plan:
  - `python3 .trellis/scripts/guru/guru_gate.py slice-plan <task_dir>`
  - Emits stdout JSON only. It must not write packets, reviews, task metadata,
    channel state, or mutable evidence.

- Route-aware slice dispatcher:
  - `python3 .trellis/scripts/guru/guru_supervise.py implement-slices <task_dir> [--dry-run] [--parallel <n>] [--group <group_id>] [--backend auto|sub-agent|channel]`
  - `--backend auto` reads `.trellis/config.yaml` key
    `codex.dispatch_mode`.
  - `sub-agent` mode emits direct platform sub-agent briefs. The CLI cannot
    call the Codex Agent tool itself.
  - `channel` mode emits/uses channel-compatible commands only when configured
    or explicitly selected.

- Check-only slice review:
  - `python3 .trellis/scripts/guru/guru_supervise.py implementation-review <task_dir> [--slice <unit_id>] [--staged]`
  - This command must not launch an implement worker.

- Commit coverage:
  - `python3 .trellis/scripts/guru/guru_gate.py commit-plan <task_dir>`
  - `python3 .trellis/scripts/guru/guru_gate.py check-commit <task_dir>`
  - Both commands must evaluate the same staged-scope review coverage model.

### 3. Contracts

`slice-plan` JSON must include additive scheduling metadata:

```json
{
  "schema_version": 2,
  "packet_required": true,
  "slices": [
    {
      "slice_id": "UNIT-example",
      "target_paths": [],
      "depends_on": [],
      "resource_locks": [],
      "parallel_safe": false,
      "parallel_mode": "writer|read_only|serial",
      "parallel_group": "g1",
      "parallel_blockers": [],
      "recommended_commands": {
        "implement_check": "...",
        "implementation_review": "...",
        "implementation_review_staged": "..."
      }
    }
  ],
  "parallel_groups": [
    {
      "group_id": "g1",
      "mode": "writer|read_only|serial",
      "slice_ids": [],
      "max_parallel": 1,
      "blocking_reasons": []
    }
  ],
  "dispatch_advisory": {
    "configured_dispatch_mode": "sub-agent",
    "selected_backend": "sub-agent",
    "channel_is_default": false,
    "slice_plan_read_only": true,
    "sub_agent_requires_active_task_prelude": true
  }
}
```

`implement-slices` JSON must include:

- `selected_backend`: effective backend after CLI/config selection.
- `raw_configured_dispatch_mode` and `configured_dispatch_mode`.
- `slice_plan_reread=true`; the dispatcher must not trust stale caller JSON.
- `decision`: `parallel | serial | blocked`.
- `dispatch_items[]`, each with `slice_id`, `mode`, `target_paths`,
  `dispatch_now`, `recommended_command`, and backend-specific details.
- In `sub-agent` backend, each item must contain `sub_agent.agent` and
  `sub_agent.brief`. The brief must start with `Active task: <task path>` and
  must tell the worker it is already the dispatched worker and must not spawn
  another implement/check agent.
- In `channel` backend, each item must contain channel-compatible dry-run and
  execute commands. Sub-agent status must not be represented as channel status.
- `read_only_fanout[]` may recommend `implementation-review` commands and must
  mark `does_not_launch_implement_worker=true`.

`implementation-review` worker prompts are an output contract. They must list
the required verdict fields by name: `review_result`, `route_class`,
`review_target`, `review_provider`, `deterministic_checks`, `dirty_scope`, and
`invariant_coverage`. `review_provider` is the actual check worker provider
(`codex` or `claude`), not a semantic provider label such as `opposite`,
`manual`, or `ocr_optional`. Supervisor-owned record fields such as
`target_paths`, `required_satisfied`, and `reviewed_target_digest` must not be
accepted as substitutes for those seven verdict fields. The prompt must also
list the exact `expected_invariants` for the current review target, and staged
review targets must include the synthetic `staged_scope_reviewed` invariant so
the worker cannot borrow invariant ids from unrelated slice packets.

`commit-plan.review_coverage` must be present and additive:

```json
{
  "review_coverage": {
    "source": "review-records/implementation-reviews.jsonl",
    "records_considered": 0,
    "records_current_clean": 0,
    "covered_staged_paths": [],
    "uncovered_staged_paths": [],
    "forbidden_staged_paths": [],
    "covering_reviews": {},
    "covering_review_ids": [],
    "ignored_reviews": [],
    "ignored_covering_review_ids": [],
    "ignored_covering_staged_paths": [],
    "missing_review_commands": []
  }
}
```

Full-chain commit authorization must aggregate all current clean review records
whose `reviewed_target_digest` matches the staged index digest for that record's
`target_paths`. It must not authorize multi-slice staged scope from the latest
JSONL row alone.

Route awareness is mandatory. `micro_task` and `lite_task` must not inherit
full-chain slice packet requirements unless their selected contract explicitly
requires full-chain packet behavior.

### 4. Validation & Error Matrix

| Condition | Behavior |
| --- | --- |
| `route=full_chain`, `risk=high`, no slice packets | `slice-plan` reports `PACKET_REQUIRED_BEFORE_IMPLEMENT`; worker launch fails before implement/check |
| Multiple packets and no selected slice | `slice-plan` reports `PACKET_AMBIGUOUS_WITHOUT_SLICE`; per-slice commands include `--slice <unit_id>` |
| Packet target paths overlap | affected slices become `parallel_safe=false`, `parallel_mode=serial`, with `TARGET_PATH_OVERLAP:*` blockers |
| Packet deterministic checks contain broad package/tool commands such as Flutter, Dart, pnpm/npm/yarn/bun, Gradle, or Xcode | affected slices get `RESOURCE_LOCK:<lock>` blockers and do not enter writer parallel groups |
| Dirty scannable paths outside `target_paths` and `dirty_state.unrelated` | affected slice reports `SCOPE_INVALID` and dispatcher downgrades or blocks |
| `codex.dispatch_mode=sub-agent` and backend auto | selected backend is `sub-agent`; no channel is created or queried |
| backend explicitly `channel` | channel commands may be emitted; this is the only path that may query channel status |
| backend `sub-agent` | status source is platform sub-agent results; channel live/terminal status must not be fabricated |
| No safe writer group exists | dispatcher returns `decision=serial|blocked` with downgrade reasons |
| Read-only review fanout is emitted | commands must be `implementation-review`, not `implement-check` |
| Implementation review output omits any required verdict field or writes `review_provider=opposite`, `manual`, or `ocr_optional` | supervisor records `MALFORMED_REVIEW_OUTPUT`; the record cannot satisfy required review coverage |
| Staged implementation-review prompt omits the synthetic `staged_scope_reviewed` invariant id | worker output is likely malformed; prompt contract must be repaired before rerunning the review |
| Commit staged paths are covered by several current clean slice reviews | commit may proceed if all other gates pass |
| Only the latest review row is clean but earlier staged slice paths lack current clean review | commit blocks and recommends missing `implementation-review --slice <unit_id> --staged` commands when mappable |
| Task/workspace artifacts are mixed with implementation staged paths | commit remains split-required; review coverage does not authorize task artifacts |

### 5. Good/Base/Bad Cases

- Good: two independent clean slice packets with disjoint target paths and no
  resource locks produce one writer parallel group.
- Good: a current Codex project with `codex.dispatch_mode: sub-agent` produces
  platform `trellis-implement` briefs headed by `Active task:` and does not call
  `trellis channel`.
- Good: broad validation commands such as `flutter test` or `pnpm ...` make the
  writer group serial even if target paths are disjoint.
- Good: `commit-plan` covers staged `lib/a.dart` from review A and staged
  `lib/b.dart` from review B, with both review digests recomputed against the
  staged index.
- Base: a single-packet full-chain task continues to use explicit
  `implement-check --slice <unit_id>` and `implementation-review --slice`.
- Bad: direct platform sub-agent mode creates a channel and then waits on
  channel status.
- Bad: `commit-plan` uses only `_latest_jsonl_record` to authorize all staged
  paths.
- Bad: a reviewer sees `semantic_review_provider=opposite` and writes
  `review_provider=opposite`, or replaces the required verdict fields with
  `target_paths` / `required_satisfied`.
- Bad: a staged review prompt says "output every invariant" but does not list
  `staged_scope_reviewed`, causing the worker to copy invariant ids from old
  slice packets.
- Bad: `slice-plan` writes or mutates packet files to manufacture a runnable
  group.

### 6. Tests Required

Guru verify tests must cover:

- `slice-plan` zero/one/multiple packet output with `schema_version=2`.
- `slice-plan` `dispatch_advisory` for `sub-agent`, including
  `channel_is_default=false`.
- `micro_task` and `lite_task` no-packet cases do not get
  `PACKET_REQUIRED_BEFORE_IMPLEMENT`.
- Disjoint writer packets produce a writer group.
- Overlapping target paths downgrade to serial.
- Resource-lock deterministic checks downgrade to serial.
- `implement-slices --backend auto` in sub-agent mode emits sub-agent briefs
  with `Active task:` and does not create/query channel.
- Explicit `--backend channel` emits channel plan data.
- `implementation-review --slice --staged` remains check-only.
- `implementation-review` rejects malformed reviewer output that omits one of
  the seven required verdict fields, and rejects semantic provider labels in
  `review_provider` even when the packet requires opposite-provider evidence.
- `implementation-review --staged --dry-run` exposes the synthetic
  `staged_scope_reviewed` invariant id in the active review brief.
- `commit-plan` multi-slice pass fixture covers all staged paths using a review
  set.
- `commit-plan` missing-slice fixture recommends only the missing slice review
  command.
- Source/template mirror checks cover gate, supervisor, tests, and workflow
  copies.

### 7. Wrong vs Correct

#### Wrong

```text
channel 默认：主会话运行 guru_supervise.py implement-check <task-dir>
```

This makes channel look like the default even when the project has
`codex.dispatch_mode: sub-agent`, causing operators to route work through the
wrong backend.

#### Correct

```text
dispatch-mode aware: first read codex.dispatch_mode. In sub-agent mode emit
Active task-prefixed trellis-implement briefs; use channel only when configured
or explicitly selected.
```

This keeps direct platform sub-agent dispatch and durable channel dispatch as
separate, explicit backends.

---

## Scenario: Route-Aware Finish and Commit Contract

### 1. Scope / Trigger

Apply this spec when editing Guru Finish / Commit behavior, including:

- Phase 3.3 spec update requirements.
- post-implementation evidence recording.
- detail digest boundaries.
- commit-plan / check-commit staged-scope decisions.
- terminal channel worker cleanup.
- workflow / skill instructions for commit-ready behavior.

This scenario exists because a task can be correctly implemented and verified but still spend excessive time and tokens before commit if Finish is treated as full-chain for every route.

### 2. Route Matrix

Finish behavior must be selected by route:

| route | verification | spec update | worker cleanup | commit-plan | stop boundary |
| --- | --- | --- | --- | --- | --- |
| `direct_small_inline` | scoped diff/check only | n/a | n/a | required; recovery-only when no contract exists | before commit |
| `micro_task` | scoped deterministic checks | deferred by default | terminal-only | required | before commit |
| `lite_task` | focused tests + scoped analyze/checks | conditional reusable contract | terminal-only | required | before commit |
| `full_chain` | full task verification | required | required | required | before commit/archive |

`full_chain` behavior must not be weakened. Route-aware Finish only reduces default spec/update/review tail work for lower-risk routes.

### 3. Mutable Evidence Boundary

Post-implementation evidence must not be written to planning/detail contract files when the goal is to preserve confirmed digest state.

Mutable evidence examples:

- test/analyze/format/diff-check output.
- GitNexus `detect_changes` or fallback evidence.
- Phase 3.3 extraction decisions.
- worker cleanup status.
- commit-plan decisions.

Preferred task-local files:

- `implementation-evidence.jsonl`
- `verification-evidence.jsonl`
- `spec-extraction.jsonl`
- `worker-cleanup.jsonl`
- `commit-plan.json`

Appending these files must not change requirements, overview, or detail digest. Editing `design.md`, `implement.md`, or other planning contract files must still change digest and invalidate stale confirmations/reviews.

When a task has passed detail confirmation, `implement.md` is a digest-bearing planning contract. Implementation/check workers must record post-detail execution evidence in mutable evidence files rather than treating `implement.md` as the default evidence sink. If `implement.md` must change, the task is intentionally returning to detail Gate.

### 4. Commit Plan Schema

Commit decisions must be available through a machine-readable plan before staging or committing.

Required command shape:

```bash
python3 .trellis/scripts/guru/guru_gate.py commit-plan [task_dir] [--write]
```

Required JSON fields:

```json
{
  "schema_version": 1,
  "route": "direct_small_inline|micro_task|lite_task|full_chain",
  "commit_mode": "direct|implementation|docs|tooling|split_required",
  "allowed_stage_paths": [],
  "forbidden_stage_paths": [],
  "required_commands": [],
  "optional_commands": [],
  "required_user_confirmations": [],
  "can_commit_now": false,
  "blocking_reasons": [],
  "suggested_stage_commands": []
}
```

`check-commit` and `commit-plan` must use the same decision model. `commit-plan` without `--write` is a read-only diagnostic; `commit-plan --write` persists the same JSON into task-local `commit-plan.json` mutable evidence. Final behavior must avoid two independent pass/block implementations.

When commit-time evidence exists but no valid commit contract exists, `commit-plan`
must not force retroactive full planning for scoped low-risk work. If staged
paths are low-risk implementation files within the direct small-inline limits,
the plan must block direct commit and recommend post-implementation intake
recovery: create or switch to a `micro_task`, run `init-contract --route
micro_task --risk low` with explicit allowed paths and max file count, then rerun
`commit-plan` / `check-commit`. It must not list requirements, overview, detail,
or `check-implementation` as the recovery command for that low-risk case.
Medium, high, mixed, or unclear staged scopes remain fail-closed and require
user route selection, promotion to `lite_task` / `full_chain`, or split staging.

### 5. Spec Update Budget

Spec update is route-aware:

- `direct_small_inline`: no spec update.
- `micro_task`: default `spec_update=deferred|not_applicable`; commit must not block only because spec update is absent.
- `lite_task`: spec update is conditional. It is required only when the work produces a reusable engineering contract, cross-layer convention, or repeated failure prevention rule.
- `full_chain`: spec update remains required before final commit/finish unless explicitly marked not applicable with evidence.

Spec extraction records must go to mutable evidence or workspace journal, not `implement.md`, unless the design contract itself truly changed and the task is intentionally returning to detail Gate.

### 6. Worker Cleanup Contract

Channel status must distinguish live and terminal workers.

Expected summary shape:

```json
{
  "live_workers": 0,
  "terminal_workers": 2,
  "cleanup_available": true,
  "blocking": false
}
```

Terminal `done|killed|error` workers must not be presented as live blockers. Cleanup should be automatic or exposed as a single terminal cleanup action.

### 7. Commit-Ready Stop Rule

When quality evidence is green, current gate status is ready, and commit-plan is available, the main session must stop before:

- staging files,
- committing,
- TAPD / external tracker status updates,
- archive / finish-work,
- speculative spec rewrite,
- extra review runs not required by the plan.

The final response should report the commit-plan summary and ask for the next explicit irreversible action if needed.

### 8. Compact Commit Context

Commit-tail context must be compact. After commit-plan is available, the agent should only load:

- task path and route,
- current gate/review digest summary,
- validation summary,
- dirty/staged scope,
- commit-plan output,
- explicit user confirmations.

It should not reload full skills, full memory, or large spec files unless commit-plan reports a missing dependency that requires them.

### 9. Good/Base/Bad Cases

- Good: a `lite_task` finishes focused tests and `detect_changes`, records spec update as `deferred` because no reusable contract was created, emits a commit-plan, then stops before staging.
- Good: a low-risk implementation was already staged before a task contract existed; `commit-plan` blocks direct commit, recommends `micro_task` recovery, and avoids retroactive PRD/overview/detail backfill.
- Good: a `full_chain` changes gate runtime behavior, requires Phase 3.3 spec update, then emits split-required commit-plan if task/spec/tooling files are mixed with implementation files.
- Good: `check-commit` reports a missing or stale required implementation review record and recommends `guru_supervise.py implementation-review <task_dir> --staged`, which writes a structured record without launching an implement worker.
- Base: existing full-chain tasks without the new mutable evidence files continue to use current strict review and commit gates.
- Bad: a worker appends Phase 3.3 extraction notes to `implement.md`, causing detail digest mismatch after quality is already green.
- Bad: `check-commit` tells the operator to rerun `implement-check` only to repair a missing commit-time review record.
- Bad: agent reads `guru_gate.py` source at commit time to infer allowed stage paths instead of using commit-plan.
- Bad: terminal done workers trigger multiple `pgrep` / `kill` loops before commit.
- Bad: commit gate sees a scoped low-risk staged diff with no valid contract and tells the user to fill PRD/overview/detail after implementation.

### 10. Tests Required

Guru verify tests must cover:

- `commit-plan` JSON for direct small_inline, micro_task, lite_task, and full_chain.
- no-task or non-ready active-task low-risk staged implementation diff blocks direct commit and recommends micro_task recovery without requirements/check-implementation commands.
- `commit-plan` and `check-commit` agree on representative pass/block fixtures.
- `implementation-review --staged` writes a required clean record whose `reviewed_target_digest` matches the staged index digest consumed by `check-commit`.
- `implementation-review --slice <unit_id> --staged` uses the slice packet target without launching an implement worker.
- Missing/malformed/stale required implementation review records make `commit-plan` recommend `implementation-review --staged`, not `implement-check`.
- task/spec/journal/tooling files mixed into implementation commit produce `split_required`.
- `micro_task` missing spec update does not block by itself.
- `lite_task` spec update can be `deferred` when no reusable contract exists.
- `full_chain` missing required spec update blocks finish/commit when the route requires it.
- appending `verification-evidence.jsonl` does not change detail digest.
- editing `implement.md` still changes detail digest.
- terminal done workers are not live blockers.
- commit-ready stop rule prevents automatic stage/commit/archive in workflow instructions.

### 11. Wrong vs Correct

#### Wrong

```md
## 5. Phase 3.3 Spec 回写

All extraction evidence is appended to implement.md after detail Gate was confirmed.
```

This mutates the detail digest after confirmation and forces unnecessary re-review.

#### Correct

```json
{
  "schema_version": 1,
  "kind": "spec_extraction",
  "route": "lite_task",
  "status": "deferred",
  "reason": "no reusable engineering contract beyond this local bugfix",
  "created_at": "2026-07-02T11:25:00+08:00"
}
```

This records the Finish decision without changing the planning/detail contract digest.
