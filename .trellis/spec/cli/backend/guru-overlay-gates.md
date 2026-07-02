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
  - `route`: `small_inline | micro_task | lite_task | full_chain`
  - `confidence`: number
  - `reasons`: string array
  - `risk_flags`: string array
  - `needs_user_choice`: boolean
  - `recommended_contract`: route string

- Task-local contract files:
  - `gate-contract.json`
  - `gate-degradations.jsonl`
  - `gate-evidence/`

- Commit gate:
  - `python3 guru_gate.py check-commit [task_dir]`

- Configuration key:
  - `.trellis/config.yaml` path: `guru.supervision.adversarial_enabled`
  - Default: `true`
  - `false` disables the adversarial reviewer requirement only.

### 3. Contracts

`gate-contract.json` must contain:

- `schema_version`: current integer schema version.
- `risk`: normalized risk, with unknown raw strings rejected during validation.
- `route`: commit route. `small_inline` is not a valid commit contract.
- `scope.allowed_paths`: explicit non-empty paths for `micro_task`; repo root is not allowed for `micro_task`.
- `scope.max_files`: positive integer for `micro_task`.
- `allowed_degradations`: rows with `gate` and non-empty `fallback_checks`.
- `commit_policy.allow_task_artifacts_only`: defaults false.

`gate-degradations.jsonl` is append-only evidence, not permission. Permission comes from global policy plus the current contract. Each row must identify the gate and include passed compensating checks required by the contract.

`task.json.guru_chain` remains the legacy artifact-shape selector `full | light`. New route names use `lite_task`; do not introduce a new light-prefixed task route.

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
| High-risk work with non-`full_chain` route | Block |
| Unauthorized degradation row | Block |
| Empty `fallback_checks` | Block |
| Missing passed compensating checks | Block |
| Staged task/workspace artifact paths | Block for implementation commit contracts |
| Non-full staged path with gate/workflow/storage/privacy/payment signal | Block and require `full_chain` |
| `adversarial_enabled=false` with current blocked requirements review | Block |
| `adversarial_enabled=false` with missing adversarial reviewer only | Allow if other current clean-review/digest gates pass |

### 5. Good/Base/Bad Cases

- Good: a low-risk single-path UI/text change uses `micro_task` only when commit is requested, with explicit scope, positive `max_files`, and deterministic compensating checks for optional GitNexus degradation.
- Base: a task without `gate-contract.json` follows the existing full-chain `check-implementation` plus implementation-review digest and staged-scope checks.
- Bad: a task-local degradation row claims a required semantic review or commit gate can be skipped. Required gates are globally non-degradable and must fail closed.

### 6. Tests Required

Guru overlay verify tests must cover:

- Low request with no paths is not `small_inline`; it must route to medium/lite or require user choice.
- Low plus commit routes to `micro_task`.
- Medium local behavior changes route to `lite_task`.
- Payment, ads, privacy, permission, schema, workflow, hook, gate, runtime, storage, or cross-layer signals route to `full_chain`.
- Contract validation rejects empty micro scope, repo-root micro scope, risk typos, empty fallback checks, unauthorized degradations, and malformed roots.
- `check-commit` blocks staged task artifacts, out-of-scope staged paths, non-full high-risk paths, and missing compensating evidence.
- `adversarial_enabled=false` allows double ordinary clean reviews to proceed, but does not bypass current blocked or medium+ review evidence.
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

This combines an unknown risk typo, a high-risk downgrade, repo-root scope, missing max file bound, and an attempted required-gate degradation.

#### Correct

```json
{
  "schema_version": 1,
  "risk": "low",
  "route": "micro_task",
  "scope": {"allowed_paths": ["lib/widgets/badge.dart"], "max_files": 1},
  "allowed_degradations": [
    {"gate": "gitnexus_impact", "max_risk": "low", "fallback_checks": ["rg_callers", "git_diff_check"]}
  ],
  "commit_policy": {
    "require_in_progress": false,
    "require_clean_implementation_review": false,
    "allow_task_artifacts_only": false
  }
}
```

This keeps the exception low-risk, scoped, bounded, and tied to deterministic compensating checks.
