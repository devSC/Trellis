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

- Contract generation:
  - `python3 guru_gate.py init-contract <task_dir> --route <route> --risk <risk> [--allowed-path <path> ...] [--max-files <n>]`
  - The command must call `guru_contract.default_contract()`, validate the result, and write `gate-contract.json` atomically or through the shared contract writer.
  - The command must reject high-risk downgrade attempts, invalid raw risk strings, invalid route names, non-positive max file limits, and invalid micro scopes.

- Full-chain slice planning:
  - `python3 guru_gate.py slice-plan <task_dir>`
  - The command emits read-only JSON summarizing whether a slice packet is required, available packets, dirty scope, blocking reasons, and recommended per-slice implement commands.
  - For `route=full_chain` and `risk=high`, `check-implementation` and `guru_supervise.py implement-check` must fail before worker launch when no slice packet exists.
  - Missing or invalid contracts on legacy tasks must not force packet creation by themselves; legacy full-chain strict behavior is preserved unless the task explicitly resolves to high-risk full-chain.

- Commit gate:
  - `python3 guru_gate.py check-commit [task_dir]`

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

- Route-aware review policy:
  - `small_inline`: no task-local requirements adversarial review is required; if the work later needs commit, create/route to `micro_task`.
  - `micro_task`: requirements adversarial review and overview/detail adversarial reviewer evidence are not required; commit remains bounded by low-risk staged scope and contract evidence.
  - `lite_task`: bounded review policy. Requirements adversarial review is optional, and overview/detail still require two current-digest clean review run ids but do not require an adversarial reviewer. Current blocked/malformed/medium+ review evidence remains blocking.
  - `full_chain`, `risk=unknown`, or missing/invalid contract: strict default policy. Requirements review is required when `adversarial_enabled=true`, and overview/detail require at least one counted adversarial clean review.

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
scope beyond the confirmed route/contract, it must ask the user whether to
expand the contract or promote to `full_chain`; it must not silently rewrite
`evidence_ready` or assumptions as `user_confirmed`.

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
| `micro_task` with no requirements adversarial review | Allow; continue enforcing structure/confirmation only when that command is explicitly used |
| `lite_task` with no requirements adversarial review | Allow under bounded policy if risk is known and no current blocked/malformed/medium+ requirements evidence exists |
| `lite_task` with two ordinary clean overview/detail reviews and no adversarial reviewer | Allow under bounded policy |
| `lite_task` with current requirements `blocked` or clean `max_severity=medium+` | Block |
| `lite_task` review discovers high-risk or expanded scope | Stop for user confirmation; do not silently promote evidence-ready scope to user-confirmed |
| `risk=unknown` or invalid `gate-contract.json` | Strict default policy; do not apply route-aware adversarial relaxation |
| `init-contract --risk high --route lite_task|micro_task` | Block; high risk requires `full_chain` |
| `init-contract` sees unreadable existing contract | Block; do not overwrite ambiguous state |
| high-risk `full_chain` implementation without slice packet | Block before worker launch with `PACKET_REQUIRED_BEFORE_IMPLEMENT` |
| high-risk `full_chain` with one valid slice packet | Allow implementation preflight and expose recommended `--slice <id>` command |
| high-risk `full_chain` with multiple packets and no selected slice | Report `PACKET_AMBIGUOUS_WITHOUT_SLICE` in `slice-plan` |
| `status --json` sees only terminal workers | Return `blocking=false`, `cleanup_available=true` |

### 5. Good/Base/Bad Cases

- Good: a low-risk single-path UI/text change uses `micro_task` only when commit is requested, with explicit scope, positive `max_files`, and deterministic compensating checks for optional GitNexus degradation.
- Good: a high-risk full-chain runtime task writes a slice packet before implementation, runs `slice-plan`, then launches one explicit slice.
- Base: a task without `gate-contract.json` follows the existing full-chain `check-implementation` plus implementation-review digest and staged-scope checks.
- Bad: a task-local degradation row claims a required semantic review or commit gate can be skipped. Required gates are globally non-degradable and must fail closed.
- Bad: a high-risk full-chain task starts an implementation worker before any slice packet exists.

### 6. Tests Required

Guru overlay verify tests must cover:

- Low request with no paths is not `small_inline`; it must route to medium/lite or require user choice.
- Low plus commit routes to `micro_task`.
- Medium local behavior changes route to `lite_task`.
- Payment, ads, privacy, permission, schema, workflow, hook, gate, runtime, storage, or cross-layer signals route to `full_chain`.
- Contract validation rejects empty micro scope, repo-root micro scope, risk typos, empty fallback checks, unauthorized degradations, and malformed roots.
- `check-commit` blocks staged task artifacts, out-of-scope staged paths, non-full high-risk paths, and missing compensating evidence.
- `adversarial_enabled=false` allows double ordinary clean reviews to proceed, but does not bypass current blocked or medium+ review evidence.
- Route-aware review policy: `micro_task` skips requirements adversarial review, `lite_task` bounded review accepts double ordinary clean, and `full_chain` keeps strict gates while only requiring requirements adversarial review when `adversarial_enabled=true`.
- `init-contract` generates valid micro/lite/full contracts and rejects high-risk downgrade.
- `check-implementation` and `guru_supervise.py implement-check` block high-risk full-chain tasks with no slice packet before worker launch.
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
| `direct_small_inline` | scoped diff/check only | n/a | n/a | required | before commit |
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
- Good: a `full_chain` changes gate runtime behavior, requires Phase 3.3 spec update, then emits split-required commit-plan if task/spec/tooling files are mixed with implementation files.
- Base: existing full-chain tasks without the new mutable evidence files continue to use current strict review and commit gates.
- Bad: a worker appends Phase 3.3 extraction notes to `implement.md`, causing detail digest mismatch after quality is already green.
- Bad: agent reads `guru_gate.py` source at commit time to infer allowed stage paths instead of using commit-plan.
- Bad: terminal done workers trigger multiple `pgrep` / `kill` loops before commit.

### 10. Tests Required

Guru verify tests must cover:

- `commit-plan` JSON for direct small_inline, micro_task, lite_task, and full_chain.
- `commit-plan` and `check-commit` agree on representative pass/block fixtures.
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
