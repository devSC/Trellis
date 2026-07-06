# Fix Guru Check-Only Implementation Review Record Flow - Design

## §1 Overview / 概要设计

The fix separates Guru's execution loop from Guru's required implementation review evidence.

Current coupling:

```text
check-commit missing required review record
  -> tells operator to rerun implement-check
  -> implement-check launches implement worker
  -> implement worker may update implement.md
  -> implement.md changes detail digest
  -> detail confirmation becomes stale
```

Target boundary:

```text
implement-check
  Phase 2 implement + check repair loop
  may modify code while task is in_progress
  may produce required review record when run normally

implementation-review
  Phase 2.2 / commit-safe evidence producer
  never runs implement worker
  runs deterministic checks + check worker only
  writes normalized required implementation review record

check-commit
  Phase 3.4 read-only gate
  consumes record only
  never spawns worker or writes review record
```

### Behavior Owner / 归属 Table

| BHV | owner | 归属理由 / 三问 |
| --- | --- | --- |
| BHV-001 | UNIT-check-only-supervision | 为什么属于它: only the supervisor can launch the check worker and append the structured record. 为什么不属于别人: commit gate must stay read-only and `implement-check` must keep its Phase 2 loop role. 是否需独立存在: yes, it is the new command surface. |
| BHV-002 | UNIT-commit-gate-plan | 为什么属于它: commit recovery text and required commands are produced by `guru_gate.py`. 为什么不属于别人: supervisor should not decide commit readiness. 是否需独立存在: yes, it protects Phase 3 guidance. |
| BHV-003 | UNIT-commit-gate-plan | 为什么属于它: fail-fast staged scope and lifecycle decisions are made before recommending a worker command. 为什么不属于别人: check workers are too expensive to start for invalid scope. 是否需独立存在: yes, it prevents token/time waste. |
| BHV-004 | UNIT-check-only-supervision | 为什么属于它: worker briefs and evidence sinks are authored by supervisor run plans. 为什么不属于别人: digest computation only detects drift after the fact. 是否需独立存在: yes, it prevents detail artifact churn. |

### Detailed Design Handoff Index / 承接索引

| chapter_target | doc_type | owner | covered BHV |
| --- | --- | --- | --- |
| design.md §2 / UNIT-review-target-resolution | service | UNIT-review-target-resolution | BHV-001, BHV-003 |
| design.md §2 / UNIT-check-only-supervision | controller | UNIT-check-only-supervision | BHV-001, BHV-004 |
| design.md §2 / UNIT-commit-gate-plan | service | UNIT-commit-gate-plan | BHV-002, BHV-003 |

## §2 Detailed Design / 详细设计

### 单元职责

The detailed design has three units: target resolution, check-only supervision, and commit gate planning.

### 行为定义

行为清单: BHV-001, BHV-002, BHV-003, BHV-004.

### 核心数据结构

Core structures are `ReviewTarget`, `RunPlan`, structured implementation review records, and commit-plan JSON.

### 逐行为设计

Each BHV is mapped below to one or more UNIT sections, with target paths, digest source, worker behavior, and commit guidance kept explicit.

### 状态/边界管理

The state boundary is Phase 2 implementation, Phase 2.2 check-only evidence production, and Phase 3.4 read-only commit gating.

### 数据合同

Record data contracts remain owned by `guru_review_record`; gate contract and staged target contracts remain owned by `guru_gate.py` / `guru_contract.py`.

### 测试映射

Tests map to dry-run, staged digest acceptance, invalid staged scope, commit-plan guidance, and legacy clean-verdict parsing.

### 不得补造清单

Do not synthesize broad review targets, bypass structured record normalization, mutate confirmed detail artifacts, or make `check-commit` write records.

### UNIT-review-target-resolution

- 单元职责: resolve review targets for slice packets, staged index review, and contract-derived lite/micro targets.
- 行为定义 / 行为清单: BHV-001, BHV-003.
- 核心数据结构: `ReviewTarget` contains `unit_id`, `review_target`, `packet`, `slice_packet_path`, `digest_source`, and `active_brief`.
- 逐行为设计: BHV-001 uses slice packet target paths or staged paths to bind review scope; BHV-003 rejects missing, ambiguous, out-of-contract, or task-artifact-only targets before a worker starts.
- 状态/边界管理: staged review uses `digest_source=index`; worktree slice review uses `digest_source=worktree`; commit readiness still rechecks the staged index digest.
- 数据合同: target paths are normalized by existing Guru review-record helpers and consumed by `target_snapshot_digest`.
- 测试映射 / 哪些测试: dry-run slice review, staged record acceptance, invalid staged contract, and digest acceptance tests in `guru-bundled.test.ts`.
- 失败收口: invalid packets, missing staged paths, contract violations, and digest errors return non-zero before writing a clean record.
- 不得补造清单: do not synthesize a broad repo-root target and do not hand-write JSONL records.

### UNIT-check-only-supervision

- 单元职责: add the `implementation-review` supervisor command and ensure it launches only a check worker.
- 行为定义 / 行为清单: BHV-001, BHV-004.
- 核心数据结构: existing `RunPlan`, `SupervisionConfig`, and `guru_review_record.normalize_review_record` remain the record-writing choke point.
- 逐行为设计: BHV-001 builds a check-only run plan and appends structured review evidence; BHV-004 changes worker briefs so mutable evidence goes to task-local evidence files instead of confirmed detail artifacts.
- 状态/边界管理: command requires `check-implementation` to pass and stops at one review pass.
- 数据合同: verdict parsing still requires route class, review result, validation summary, deterministic status, provider match, invariant coverage, and reviewed target digest.
- 测试映射 / 哪些测试: dry-run no deterministic execution, record writer, staged acceptance, and legacy clean verdict parser cases.
- 失败收口: malformed verdicts, provider mismatch, failed deterministic checks, or missing invariants are recorded as non-clean and exit non-zero.
- 不得补造清单: do not launch implement workers and do not edit `prd.md`, `design.md`, or `implement.md` from this command.

### UNIT-commit-gate-plan

- 单元职责: keep `commit-plan` and `check-commit` aligned while changing recovery guidance away from `implement-check`.
- 行为定义 / 行为清单: BHV-002, BHV-003.
- 核心数据结构: `commit-plan` JSON fields `blocking_reasons`, `required_commands`, `allowed_stage_paths`, and `forbidden_stage_paths`.
- 逐行为设计: BHV-002 recommends `implementation-review --staged` only for review-record problems; BHV-003 suppresses that recommendation when contract, staged scope, or lifecycle preflight is already invalid.
- 状态/边界管理: `check-commit` remains read-only and never spawns workers.
- 数据合同: `_implementation_review_problem` and `_commit_plan_payload` share the same staged digest and target-path model.
- 测试映射 / 哪些测试: commit-plan missing-record and invalid-scope regression tests.
- 失败收口: invalid staged scope produces gate repair guidance first, not a worker command.
- 不得补造清单: do not weaken `normalize_review_record`, do not bypass detail digest confirmation, and do not make commit gate write records.

### Existing Design Notes

#### Review Target Model

Introduce an internal review target abstraction, implemented as a small dataclass or dictionary helper inside the Guru overlay runtime:

```text
ReviewTarget
  kind: slice | staged | contract
  slice_id: string | None
  review_target: string
  target_paths: list[string]
  invariants: list[dict]
  deterministic_checks: list[dict]
  semantic_review_provider: dict
  digest_source: worktree | index
```

Sources:

- `slice`: built from existing slice packet files. Keeps current full/high-risk semantics.
- `staged`: built from currently staged code paths and the task gate contract. Digest source is `index`.
- `contract`: built from `gate-contract.json` and current target paths when no slice packet exists. This is the lite/micro bridge.

The abstraction hides the packet-vs-contract difference from the record writer. Required review records still use the existing record schema and validation functions.

#### Supervisor Commands

##### Existing `implement-check`

Keep `implement-check` as the Phase 2 repair loop:

1. Resolve review target when a packet exists.
2. Run implement worker.
3. Run deterministic checks.
4. Run check worker.
5. Normalize and append review record.
6. Stop on clean or route defects upstream.

No commit gate should recommend this command as a missing-record repair path.

##### New `implementation-review`

Add a new subcommand:

```bash
python3 .trellis/scripts/guru/guru_supervise.py implementation-review <task-dir> [--slice <UNIT>] [--staged] [--contract] [--run-id <id>] [--dry-run]
```

Rules:

- It must pass `guru_gate.py check-implementation`.
- It must not execute `build_run_plan("implement", ...)`.
- It must run deterministic checks once for the resolved target.
- It must execute a `check` run plan with a brief that says this is check-only required review evidence, not implementation.
- It must parse the same 7-field verdict and invariant fields as `implement-check`.
- It must call `guru_review_record.normalize_review_record(..., mode="supervisor")`.
- It must call `guru_review_record.append_record(...)`.
- It must return non-zero for malformed verdicts, missing required provider, failed deterministic checks, invalid dirty scope, failed invariant coverage, or target digest errors.

For `--staged`, the normalized record must include `reviewed_target_digest` computed with `target_snapshot_digest(root, target_paths, "index")`.

For `--slice` and worktree review, the normalized record may use `source="worktree"` when used during Phase 2, but commit readiness still requires the staged digest to match.

#### Gate Behavior

`check-commit` remains read-only and fail-closed.

Change blocker text and `commit-plan.required_commands`:

- Missing record -> `implementation-review --staged`
- Malformed record -> `implementation-review --staged`
- Missing `reviewed_target_digest` -> `implementation-review --staged`
- Target digest mismatch -> `implementation-review --staged`
- Detail digest stale -> return to detail gate, not implementation review
- Staged task artifacts in implementation commit -> split or unstage task artifacts
- Contract/staged-scope invalid -> do not recommend or run `implementation-review`; first narrow staged paths or repair `gate-contract.json`

`commit-plan` and `check-commit` must continue to use one decision model.

#### Mutable Evidence Boundary

`implement.md` remains a detail/planning contract after detail confirmation. It must not be used as the default sink for Phase 2/3 mutable evidence.

New or existing append-only evidence files:

- `implementation-evidence.jsonl`
- `verification-evidence.jsonl`
- `spec-extraction.jsonl`
- `worker-cleanup.jsonl`
- `commit-plan.json`
- `review-records/implementation-reviews.jsonl`

Worker prompt text should change from "keep implement.md evidence current" to:

```text
Record execution/check evidence in task-local mutable evidence files.
Do not edit prd.md, design.md, or implement.md after detail confirmation unless intentionally returning to the detail gate.
```

#### Compatibility

- Existing tasks that already run `implement-check` successfully still work.
- Existing packet records remain valid.
- Existing `review-records/implementation-reviews.jsonl` schema remains valid.
- New command adds a safer path; it does not remove old commands.
- Template sync must update both `packages/cli/src/templates/guru/...` and `guru-template/...` mirrors.

#### Failure Handling

Fail closed for:

- Missing or ambiguous review target.
- Target paths outside gate contract.
- Staged paths not covered by target paths.
- Unstaged drift under staged review target unless explicitly allowed by a future design.
- Check worker verdict missing required fields.
- Check worker provider not matching the spawned provider.
- Required semantic provider not satisfied.
- Deterministic checks missing or failed.
- Invariant coverage missing or failed.
- Dirty scope invalid.
- Review target digest mismatch.

#### Test Strategy

Add focused tests in `packages/cli/test/guru/guru-bundled.test.ts` or a nearby Guru test file:

- Dry-run `implementation-review --slice` prints only a check plan, not an implement plan.
- Runtime fixture proves `implementation-review --slice` appends a normalized record.
- `implementation-review --staged` writes an index digest that `check-commit` accepts.
- Lite/micro contract-derived target does not require a temporary slice packet.
- `commit-plan` recommends `implementation-review`, not `implement-check`, when review record is missing or malformed.
- `commit-plan` does not recommend `implementation-review` when staged scope is already outside the gate contract.
- Malformed verdict still appends blocked record and exits non-zero.
- Mutable evidence append does not alter detail digest; editing `implement.md` still does.

#### Trade-Offs

The new command adds CLI surface area, but it makes phase boundaries explicit and removes the need to misuse `implement-check` as a commit-time record repair tool.

Deriving review targets for lite/micro tasks is stricter than the previous ad hoc packet workaround. This is intentional: commit evidence should be tied to a real gate contract or staged scope, not a hand-made temporary packet.
