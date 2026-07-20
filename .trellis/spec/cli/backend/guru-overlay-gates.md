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
  - `small_inline` has no commit contract. A commit request is a delivery action,
    not an intrinsic difficulty signal; it may add the minimal commit contract or
    select `micro_task` without reclassifying the underlying work as behaviorally
    more difficult.

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
  - `small_inline`: mechanical, explicit, low-risk work with no behavior-contract
    change; no full task, confirmation, or Worker is required by default.
  - `micro_task`: requirements adversarial review and overview/detail adversarial reviewer evidence are not required; commit remains bounded by explicit scope, file limits, and contract evidence. It is never valid for high-risk work.
  - `lite_task`: official `task.py create` standard task, task-local compact
    `prd.md`, repo evidence first, bounded Brainstorm only for unresolved product,
    scope, failure-path, or acceptance ambiguity, one digest-bound requirements
    confirmation, zero Workers, no Overview/Detail planning review, host-inline
    execution, and one scoped `deterministic_final` after code. Commit-ready
    requires a passed task-local `verification-evidence.jsonl` record whose
    `selection_generation`, `scope_fingerprint`, exact `target_paths` and staged
    `target_digest` are current; `docs_code_test_consistency` must be `passed` and
    `spec_sync` must be `passed` or `not_required`.
  - `full_chain`, `risk=unknown-high`, or missing/invalid contract: strict default
    policy. Current requirements, critical/high risks, and key irreversible design
    decisions are exposed before any implement Worker and confirmed in one batch.

### 3. Contracts

`gate-contract.json` must contain:

- `schema_version`: current integer schema version.
- `risk`: normalized risk, with unknown raw strings rejected during validation.
- `route`: selected runtime/commit route. `small_inline` is not a valid commit contract.
- `assessment.recommended_route`: normalized recommendation derived from risk assessment, for example `full_chain`.
- `route_selection`: selection audit block containing `selected_route`, `source`, `recommended_route`, `risk_acknowledged`, `user_quote`, `selected_by`, and `selected_at`.
- `route_selection.selection_generation`: positive monotonic generation for route changes.
- `route_selection.scope_fingerprint`: exact fingerprint of the selected scope.
- `route_selection.first_repository_write_at`: absent before the first repository
  write; once present, all subsequent route transitions are upgrade-only.
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
the route's single confirmation batch, current-digest checks, structure gates,
medium+ findings, blocked requirements evidence, staged-scope validation, or
implementation review digest checks. `adversarial_enabled=false` has the same
limited scope: it removes the adversarial reviewer requirement only and never
turns current blocked or medium+ evidence into clean evidence.

Low-severity clean evidence is clean evidence. Review output with
`max_severity=none|low` and no blocker/finding class may count as clean/current.
For `lite_task`, low/P3 follow-ups and wording nits should be tracked as
follow-ups without forcing a PRD digest refresh and requirements re-review,
unless they change behavior, scope, acceptance criteria, or a high-risk decision.

Lite scope expansion must be re-intaken before another repository write. High-risk
expansion promotes to `full_chain`, requires a current risk packet and guarded
start, and consumes at most the one Full confirmation batch for unresolved
critical/high decisions. Non-high-risk scope drift invalidates only the stale
scope/digest evidence. It must not silently rewrite `evidence_ready` or
assumptions as `user_confirmed`.

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
| `lite_task` without an official standard task or task-local compact `prd.md` | Block before the first repository write |
| `lite_task` with no requirements adversarial review | Allow; Lite uses repo-first evidence, conditional Brainstorm, and one current requirements confirmation instead |
| `lite_task` implementation with missing/stale confirmation digest, route, risk, or scope fingerprint | Block before the first repository write |
| `lite_task` implementation after current confirmation | Allow host-inline without Overview/Detail planning review; require focused checks and scoped deterministic final after code |
| `lite_task` commit with missing, failed, or stale `deterministic_final` evidence | Block without requesting another user confirmation; rerun focused checks and append current exact task-local evidence |
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

- Good: a low-risk mechanical UI/text change remains intrinsically Small when
  commit is requested; the delivery action adds only the minimal commit contract.
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
- Commit intent alone does not change intrinsic difficulty; the selected delivery
  route may add only the minimal commit contract required by the commit boundary.
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
- Route-aware execution policy: `micro_task` uses a bounded micro contract;
  `lite_task` uses an official task, task-local compact requirements, conditional
  Brainstorm, one confirmation, zero Workers, and no Overview/Detail planning
  review; `full_chain` exposes risk before Workers and uses one confirmation batch.
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

## Scenario: Outcome-First Delivery And Reversible Custom Lifecycle

### 1. Scope / Trigger

Apply this contract when changing any of these Custom-first surfaces:

- `guru-template/overlay/policy/delivery-policy.json`
- `guru-template/overlay/verify/guru_delivery_policy.py`
- `guru-template/overlay/hooks/guru_after_create.py`
- `guru-template/overlay/hooks/guru_task.py`
- `guru-template/overlay/apply.sh`
- `guru-template/overlay/reinstall-official-067.sh`
- `guru-template/overlay/tests/reinstall_official_067_test.sh`
- `guru-template/overlay/agents-skills/*`
- matching workflows, execution skills, README, and focused regressions

The goal is to make low-risk work enter value quickly, expose high risk before
implementation, close after at most one confirmation batch, reuse exact evidence,
and keep the Custom package reversible without modifying Trellis Core.

### 2. Signatures

Delivery selection:

```python
resolve_delivery_selection(
    request: IntakeRequest,
    *,
    prior_evidence: dict | None = None,
    capability_report: dict | None = None,
) -> DeliverySelection
```

Lifecycle commands:

```text
apply.sh --plan <target> [flutter|go|ios|h5] [--rollback-bundle <external-empty-dir>]
apply.sh <target> [flutter|go|ios|h5] [--rollback-bundle <external-empty-dir>]
apply.sh --status <target> <rollback-bundle>
apply.sh --verify <target> <rollback-bundle>
apply.sh --upgrade <target> [flutter|go|ios|h5] --rollback-bundle <new-external-empty-dir>
apply.sh --unapply <target> <rollback-bundle>
reinstall-official-067.sh [--dry-run] [--platform flutter|go|ios|h5] [--backup-dir <external-empty-dir>] [--keep-backup] <target>
```

Official Template inputs remain `guru-template/index.json` entries with
`type: "spec"` or `type: "workflow"`; do not create a second resolver manifest
unless the official CLI can no longer consume that registry.

### 3. Contracts

Route contracts:

- `small_inline`: mechanical, explicit, low-risk work with no behavior-contract
  change; no full task, zero confirmations, zero Workers, and focused evidence.
- `micro_task`: explicit low-risk local behavior change with bounded paths/max
  files, a minimal task contract, zero confirmations, zero Workers by default,
  and a focused deterministic final.
- `lite_task`: official `task.py create` standard task, repo evidence first,
  conditional bounded Brainstorm, task-local compact `prd.md`, one confirmation
  binding the current requirements digest/route/risk/scope fingerprint, zero
  Workers, no Overview/Detail planning review, and host-inline deterministic final.
- `full_chain`: high/unknown-high work with current requirements/risk/design
  evidence before every implement Worker, one confirmation batch, guarded
  activation, managed implementation, and deterministic final.

Route difficulty is determined by requirements clarity, risk, coupling,
reversibility, and verification cost. Commit intent is orthogonal. The Agent
recommends the lowest legal route; users may select a heavier route freely or a
lighter route only when target eligibility passes. High/unknown-high can never
downgrade from Full. Route changes bind monotonic `selection_generation` and
`scope_fingerprint`; before the first repository write evidence may justify a
downgrade, while after the first write transitions are upgrade-only.

Evidence reuse requires the same policy version, intent/route, scope fingerprint,
target digest, docs-code-test digest, and a passed prior outcome. An exact hit
applies the declared 70 percent planning/context/token-budget proxy; either
digest changing invalidates reuse. This is not provider billing telemetry.

Lifecycle contracts:

- `plan`, `status`, and `verify` are byte-read-only for target and bundle.
- Apply creates the external preimage before target writes and publishes
  `state=applied` only after final exact CAS.
- Status values are `installed-current`, `drifted`, and `not-applied`.
- `prepared`, including `recovery.status=manual_required`, is `drifted`, never
  `not-applied`, because partial target writes may exist.
- Verify returns nonzero for missing receipt, drift, tamper, prepared/manual
  recovery, or invalid ownership evidence.
- Upgrade must use a new external missing-or-empty bundle and reuses apply; its
  unapply restores the immediate pre-upgrade state.
- Managed unapply restores only owned, post-state-matching assets, preserves
  unrelated user content and `.git`, and fails before mutation on conflict.
- A newly claimed Guru-managed Skill name must not silently overwrite an
  unknown same-name project Skill. Direct apply may refresh the current
  template or an exact, provenance-verified historical managed version only.
  The accepted historical registry is Skill-specific and closed by default;
  adding a digest requires the real historical bytes plus a direct-apply
  regression. A rejected, intermediate, target-private, or digest-only fixture
  must not enter the registry.
- For `guru-bug-fast-path`, the accepted historical single-file SHA-256 values
  are `a05f456ee66ea001ae408f74692d1ee96dc0006524eabbfd990ef0930c1b3212`
  and `d7df7d1d0f53e5b529c530ffa3e82340b0e7543cac4b7abbd2278ee9912b3242`.
  Any other differing same-name tree fails before normal target writes.
- Official `0.6.7` reinstall provenance is content-derived whenever the
  adjacent template tree cannot be proven equal to clean `HEAD`. A proven
  clean checkout records `source_provenance.kind=git_commit`; dirty, untracked,
  detached-package, or otherwise unprovable inputs record
  `source_provenance.kind=template_tree_sha256` and the actual template-tree
  digest. `source_commit` is null for content-derived provenance.
- Reinstall index preservation uses
  `git-effective-index-logical-record-v3`: the raw Git-reported index path and
  existence state, stage/assume-unchanged, skip-worktree, resolve-undo, and
  both ITA views are digest-bound. All Git probes use
  `GIT_OPTIONAL_LOCKS=0`; regression coverage additionally proves the raw
  index bytes remain unchanged across dry-run, rollback, conflict, and success.
- Official reinstall exit codes are semantic: `0` means verified installation
  with no reconcile items, `3` means a usable candidate with retained
  Spec/Skill reconcile reports, `1` means failure with verified rollback when
  mutation started, and `70` means rollback verification itself failed.

### 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| Lite implementation request with no high-risk signal | Route `lite_task`; create an official standard task, gather repo evidence, run bounded Brainstorm only for true ambiguity, then request one requirements confirmation |
| Lite current confirmation is missing or stale | Block before the first repository write |
| Lite current confirmation is valid | Automatically start, host-inline implement, run focused checks, append evidence, sync Spec, and reach reversible commit-ready with zero Workers |
| High-risk path or signal | Route `full_chain`; risk packet and guarded start before any implement Worker |
| Exact prior evidence and both digests unchanged | Reuse evidence and apply 70 percent controllable proxy |
| Target or docs-code-test digest changed | Do not reuse evidence |
| Lite expands to high risk | Promote before next write; require risk/start evidence; confirmation batches remain at most one |
| Plan/status/verify | Target and bundle snapshots remain byte-identical |
| Missing bundle receipt | Status `not-applied`; verify nonzero |
| Applied current receipt | Status/verify `installed-current`; verify zero |
| Managed drift or receipt tamper | Status `drifted`; verify nonzero; zero mutation |
| Prepared/manual-required receipt | Status `drifted`; verify nonzero; zero mutation |
| Upgrade without a fresh bundle | Exit 2 before target mutation |
| Upgrade then unapply | Exact immediate pre-upgrade target restored |
| Current or approved historical managed Skill | Refresh from the current template and verify both installed roots |
| Unknown differing same-name project Skill | Fail before normal target writes; preserve the project Skill |
| Clean template checkout exactly matches `HEAD` | Record `git_commit` provenance |
| Dirty, untracked, or detached template input | Record `template_tree_sha256`; do not claim commit provenance |
| Effective target index logical record changes | Fail or roll back; never report `git_index_unchanged=true` |
| Reinstall completes with Spec/Skill reconcile items | Return 3, retain backup and reports, report `candidate usable with manual reconciliation` |
| Reinstall rollback verification fails | Return 70; do not report the target as restored |

### 5. Good/Base/Bad Cases

- Good: a bounded behavior change resolves to Lite, creates a standard task,
  answers repository-resolvable questions before asking the user, conditionally
  Brainstorms real ambiguity, receives one requirements confirmation, and then
  closes autonomously without Overview/Detail loops or Workers.
- Good: workflow/runtime scope promotes to Full before code and fails closed if
  the risk packet is absent.
- Base: a successful apply has a current schema-v2 managed-assets receipt;
  status and verify are read-only and report `installed-current`.
- Good: direct apply receives one of the two byte-verified historical
  `guru-bug-fast-path` files, upgrades both Skill roots to the current template,
  and leaves an unrelated project Skill untouched.
- Good: a dirty source checkout records the exact template-tree digest, while
  a clean matching checkout records its commit; both leave the source and
  target index bytes unchanged.
- Bad: treating `state=prepared` as `not-applied`; failed recovery can leave
  partial target writes and must be reported as `drifted`.
- Bad: using a first-install bundle for upgrade rollback; every upgrade needs a
  fresh bundle so rollback semantics are the immediate pre-upgrade state.
- Bad: accepting every previous-looking same-name Skill, accepting a digest
  without the historical bytes, or adding a target-private digest to make one
  repository pass.
- Bad: returning 0 when reconcile reports contain conflicts, or calling exit 3
  a rollback failure.

### 6. Tests Required

- Policy unit tests cover all intent profiles, four routes, first-value/terminal
  budgets, exact reuse, both digest invalidations, high-risk promotion, and the
  one-batch confirmation ceiling.
- Route transition tests cover heavier override, target-eligible lighter
  override, high-risk downgrade rejection, monotonic selection generation,
  commit-intent orthogonality, pre-write downgrade, and post-write upgrade-only.
- Lite task tests cover official task creation, task-local compact requirements,
  repo-first evidence, conditional Brainstorm, current/stale confirmation
  binding, zero Workers, no Overview/Detail planning review, and autonomous close.
- Start-guard tests prove missing/stale risk, envelope, slice, or confirmation
  evidence blocks before the official subprocess.
- `apply_test.sh` snapshots target and bundle around every read-only command,
  tests current/drift/tamper/prepared states, fresh-bundle upgrade, exact
  upgrade rollback, managed unapply conflict behavior, docs-code-tests
  consistency, and Codex-only event rejection.
- Official `0.6.7` HTTPS Git E2E installs every spec/workflow pair from the typed
  registry and rejects raw blank-template fallback even when the CLI exits zero.
- Direct-apply regression extracts the real bytes for every accepted historical
  managed Skill, verifies each expected digest, executes the upgrade, and proves
  an unknown same-name tree exits before normal target writes without mutation.
- Source and package-layout `reinstall_official_067_test.sh` runs must both cover
  clean and dirty source provenance, detached package layout, linked worktrees,
  non-UTF-8 and redundant-separator index paths, stage flags, resolve-undo,
  visible/invisible ITA, raw index byte stability, forced rollback, success,
  Spec conflict, and Skill conflict.

### 7. Wrong vs Correct

#### Wrong

```text
lite_task -> requirements -> Overview x2 -> Detail x2 -> confirmation -> code
prepared rollback receipt -> status=not-applied
upgrade -> reuse the first-install rollback receipt
dirty source checkout -> source_provenance.kind=git_commit
unknown same-name Skill -> add its digest to the managed registry
reconcile conflicts -> exit 0
```

#### Correct

```text
lite_task -> official task -> repo evidence -> conditional Brainstorm -> compact prd -> one confirmation -> host-inline -> deterministic_final
full/high -> current requirements+risk+design -> one confirmation batch -> guarded start -> code/check
prepared rollback receipt -> status=drifted, verify nonzero, zero mutation
upgrade -> fresh external bundle -> unapply restores immediate pre-upgrade state
dirty source checkout -> source_provenance.kind=template_tree_sha256
approved historical Skill bytes -> exact registry match -> current managed template
unknown same-name Skill -> fail closed before normal target writes
reconcile conflicts -> exit 3 with retained structured reports
```

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

### Full v2 Start Guard Stable Binding

For `route=full_chain` with `policy_version=guru-risk-contract-v2`, the Start
Guard gate digest is a versioned stable planning binding. It binds the schema
discriminator, `guru_chain`, `require_req_uc`, current review runs, and the
exact `gate-contract.json` bytes. It must not include the dynamic
`guru_gates.requirements` or `guru_gates.detail` confirmation records.

This exclusion does not relax `check-start`. The one Full confirmation batch
must independently bind the current requirements digest, current detail
digest, and the complete sorted `risk-packets/*.json` byte set. Requirements
and detail records must be exact canonical peers except for their
gate-specific `artifact_digest`; both carry the same domain-separated
`confirmation_projection_digest` over all actor, time, scope, action, prompt,
batch, current-input, mode, via, turn, and user-quote metadata. Unknown,
missing, divergent, stale, or invalid optional fields fail closed.

The required chronological regression is:

```text
compute stable v2 binding
-> build the real risk packet
-> write one real Full confirmation batch
-> run Full freshness validation and check-start
-> validate the real guarded selected artifact binding
```

The stable digest must be byte-identical before and after confirmation.
Selected risk, attestation, envelope, lifecycle CAS, and compensation checks
remain owned by the existing Start Guard. Contracts other than Full v2 retain
the legacy digest payload byte-for-byte.

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

### Full/high Slice Commit Receipts

Schema-v2 Full/high-like work uses this lifecycle:

```text
stage exact slice
-> unique deterministic checks once
-> independent read-only semantic review
-> SLICE_COMMIT_READY
-> main-session commit
-> official append-only slice receipt
```

The evidence key binds target bytes, invariant set, selected
requirements/design bytes, deterministic command set, provider/review policy,
and supervisor source. A clean review is reusable only while every component is
identical. Reviewers must not repeat successful supervisor commands, but may run
distinct read-only adversarial probes.

`check-commit --slice <id>` requires exact staged scope, current clean
per-invariant evidence, and valid ancestor receipts for every dependency.
`record-slice-commit --slice <id>` is the only receipt producer and runs only
after the main-session work commit. A later slice may modify a shared path, but
its new bytes require a new review; the earlier receipt remains historical
commit-tree evidence.

All-missing bootstrap may use one explicit aggregate review. The selected slice
set must exactly equal the dependency-complete set covering staged paths in both
directions. Targets, invariants, requirements/design selectors, and commands are
unioned; commands are deduplicated and the strictest risk/provider policy wins.
The official aggregate producer writes one topological batch. Same-commit
dependencies are valid only when every constituent receipt belongs to that one
schema-valid batch; partial, split, duplicate, or conflicting replay fails.

Final `check-commit` without `--slice` activates only for a Full/high-like task
with one explicit integration packet. It validates the packet DAG, exactly one
integration slice, target-union coverage, every required receipt and dependency,
HEAD ancestry, historical commit-tree bytes, receipt-time supervisor bytes, and
the integration receipt against final HEAD, index, and worktree bytes. The
integration receipt must be newer than all ordinary current slice receipts.
Equal commit SHAs are allowed only for receipts in the same validated atomic
aggregate batch and official aggregate review. The success record includes
topological slice-to-commit mappings, `reviewers_spawned=0`, and `elapsed_ms`;
slice-specific failures include an exact recovery command. This path must not
run deterministic commands or spawn a reviewer and must complete within ten
seconds.

Legacy Full tasks without an integration packet, v1 review evidence, non-Full,
Lite, Micro, and direct commit routes retain their existing dispatch. Known
canonical/template mirror drift blocks sync/install/canary only; it does not
block canonical source implementation or tests, and the mirror must not be
edited manually to manufacture a pass.

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

## Scenario: Serialized Integration Proof Review

### 1. Scope / Trigger

Apply this contract when a Full/high `SL-INTEGRATION` implementation review is
projected from current ordinary-slice receipts, generated peers, Integration-owned
staged paths, requirements/design evidence, and deterministic results. The semantic
reviewer must judge the serialized proof only; it must not rediscover repository
context.

### 2. Signatures

- Operator command:
  - `python3 guru_supervise.py implementation-review <task_dir> --slice SL-INTEGRATION --staged`
- Proof projection:
  - `_integration_proof_bundle(...) -> dict`
  - `_serialize_integration_proof_prompt(bundle, invocation_contract, component_digests) -> (prompt, projected_bundle, retry_identity)`
- Context-free reviewer plan:
  - `_without_injected_context(plan, prompt, isolated_cwd)` removes `--agent`,
    `--file`, `--jsonl`, and any inherited `--cwd`, then adds exactly the isolated
    cwd and sets `files=[]`, `jsonls=[]`.

### 3. Contracts

- The serialized payload must include `integration_proof_bundle`, the exact
  nine-field `retry_identity`, `expected_invariant_ids`, `verdict_contract`, and
  first-class `acceptance_metrics`.
- `acceptance_metrics` must expose `semantic_reviewer_count=1`,
  `duplicate_read_probe_count=0`, `integration_full_regression_count=1`,
  `projection_counts`, `formatting_retry_count=0`,
  `receipt_invalidation_set`, and structured `provider_input_tokens` availability.
  Serialization adds stable `payload_bytes`, `estimated_tokens`, `budget_verdict`,
  budget limits, and `formatting_retry_identity`.
- The proof-only reviewer runs from a temporary isolated cwd with no agent card or
  repository/task file injection. Removing only `--file` and `--jsonl` is
  insufficient: an inherited `--agent check` resolves relative to the isolated cwd
  and makes the review environment-dependent.
- The deterministic evidence set must contain the exact full lifecycle regression
  command once. Zero or duplicate occurrences are invalid proof, even when all
  command exit codes are zero.

### 4. Validation & Error Matrix

| Condition | Behavior |
| --- | --- |
| Proof-only plan retains `--agent`, `--file`, or `--jsonl` | Block before semantic review |
| Reviewer plan has no isolated cwd | Block; do not permit repository context discovery |
| Full lifecycle regression count is not exactly one | Raise `Integration proof requires exactly one full lifecycle regression` |
| Payload exceeds byte or estimated-token limits | Raise `Integration proof prompt budget exceeded` |
| Payload metrics do not stabilize with the proof digest | Raise `Integration proof prompt metrics did not stabilize` |
| Reviewer tool trace reports a source probe | Record the probe and reject a clean proof verdict |
| Acceptance metrics are absent or implicit only in logs | Treat the proof as incomplete; do not issue a current receipt |

### 5. Good/Base/Bad Cases

- Good: one isolated Codex reviewer receives only the serialized proof, the tool
  trace contains no source probe, every expected invariant has passed evidence,
  and all acceptance metrics are present in the reviewed payload.
- Base: provider input-token usage is unavailable, so the payload records
  `{ "available": false, "value": null }` instead of inventing a value.
- Bad: the supervisor retains `--agent check` while moving the reviewer into an
  empty temp directory; agent-card resolution fails before the proof is reviewed.
- Bad: lifecycle regression ran once in an earlier wave but is absent from the
  current proof evidence set; historical success cannot satisfy the current proof.

### 6. Tests Required

- Assert the proof-only plan has `files=[]`, `jsonls=[]`, no `--agent`, `--file`,
  or `--jsonl`, and ends with the explicit isolated `--cwd`.
- Assert prompt serialization reaches stable byte/token metrics, records the same
  metrics inside `acceptance_metrics`, passes budget enforcement, and binds the
  exact nine-field formatting retry identity.
- Assert the acceptance metric schema and projection counts are complete, including
  explicit provider-token unavailability and an empty receipt invalidation set.
- Assert zero and duplicate full lifecycle regression commands fail; exactly one
  current command passes.
- Assert undeclared source-tool events are counted from the channel trace and cannot
  be hidden by zero injected files.
- Run source/template parity checks plus the focused proof-context, verdict-retry,
  and lifecycle regression suites before recording the Integration receipt.

### 7. Wrong vs Correct

#### Wrong

```text
spawn ... --agent check --cwd /tmp/guru-integration-proof-semantic-XYZ
files=[] jsonls=[]
metrics are mentioned only in the operator log
```

This still depends on repository-relative agent-card resolution and gives the
reviewer no auditable acceptance-metric contract.

#### Correct

```json
{
  "spawn_contract": {
    "agent": null,
    "files": [],
    "jsonls": [],
    "cwd": "/tmp/guru-integration-proof-semantic-XYZ"
  },
  "acceptance_metrics": {
    "semantic_reviewer_count": 1,
    "duplicate_read_probe_count": 0,
    "integration_full_regression_count": 1,
    "formatting_retry_count": 0,
    "receipt_invalidation_set": [],
    "provider_input_tokens": {"available": false, "value": null}
  }
}
```

The isolated reviewer is environment-independent, and the proof carries the
acceptance evidence that the reviewer and receipt validator must consume.
