# Research: SL-02/03/04 Guru parallel slice supervision code map

- Query: 为后续 SL-02/SL-03/SL-04 准备 `guru_supervise.py`、`guru_review_record.py`、`guru_gate.py` 的只读代码地图，覆盖 dispatcher / dirty scope / packet validation / review records / latest-row commit gate / status JSON，并列出后续编辑前建议先跑 GitNexus impact 的 symbol。
- Scope: internal
- Date: 2026-07-09

## Findings

### Current Task / Context

- `python3 ./.trellis/scripts/task.py current --source` returned `Current task: (none)`, so this research used the explicit task path from the dispatch prompt: `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision`.
- The task itself is `in_progress` in `task.json` and has confirmed requirements/detail gate evidence (`task.json:6`, `task.json:26-87`).
- The task contract is high-risk `full_chain`, and its allowed paths include the live Guru scripts, `guru-template/overlay/verify/*`, `packages/cli/src/templates/guru/overlay/verify/*`, Guru workflow templates, and the task directory (`gate-contract.json:2-58`).
- Current repo config sets `codex.dispatch_mode: sub-agent`; channel worker guard remains available only if the selected backend is channel (`.trellis/config.yaml:70-72`, `.trellis/config.yaml:116-119`).

### Files Found

| Path | Description |
| --- | --- |
| `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision/prd.md` | Requirements for route-aware, dispatch-mode aware parallel slice supervision; explicitly says default Codex backend is Trellis sub-agent and channel is optional (`prd.md:16-24`, `prd.md:120-131`). |
| `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision/design.md` | Detailed design for slice-plan scheduler, dispatcher, worker isolation, review coverage aggregation, route/platform parity, and tests (`design.md:15-27`, `design.md:178-239`, `design.md:241-343`). |
| `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision/implement.md` | Execution slices; SL-02/03/04 map directly to `guru_supervise.py`, `guru_review_record.py`, and `guru_gate.py`; impact analysis required before edits (`implement.md:9-16`, `implement.md:17-26`, `implement.md:41-58`). |
| `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision/implement.jsonl` | Curated implement context specs/research (`implement.jsonl:1-7`). |
| `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision/check.jsonl` | Curated check context specs/research (`check.jsonl:1-6`). |
| `.trellis/tasks/07-09-guru-route-aware-parallel-slice-supervision/research/session-timing-evidence.md` | Prior session bottleneck evidence: serial slice loop, stale route contract, latest-row commit evidence, channel status as reusable input (`session-timing-evidence.md:59-74`). |
| `.trellis/workflow.md` | Confirms sub-agent dispatch protocol and `Active task: <path>` first-line contract for class-2 Codex sub-agents (`workflow.md:190-199`, `workflow.md:241-263`). |
| `.trellis/spec/cli/backend/guru-overlay-gates.md` | Executable Guru route, slice-plan, implementation-review, commit-plan, and status contract (`guru-overlay-gates.md:54-75`, `guru-overlay-gates.md:126-136`, `guru-overlay-gates.md:382-455`). |
| `.trellis/spec/cli/backend/commands-channel.md` | Channel spawn/status/worker lifecycle contract, including live-worker budget and durable event projection (`commands-channel.md:45-74`, `commands-channel.md:357-409`, `commands-channel.md:579-606`). |
| `.trellis/spec/cli/backend/platform-integration.md` | Platform sub-agent context delivery and active-task resolver contract; Codex agent files must use `.codex/agents/*.toml` and source/template copies must stay byte-identical where applicable (`platform-integration.md:121-143`, `platform-integration.md:342-444`). |
| `.trellis/spec/cli/backend/script-conventions.md` | Python script conventions: Python 3.9+, stdlib only, pathlib, subprocess capture, JSON handling (`script-conventions.md:7-10`, `script-conventions.md:116-181`). |
| `.trellis/spec/cli/unit-test/conventions.md` | Test conventions and expectation for regression/unit coverage of logic branches (`conventions.md:47-82`, `conventions.md:142-176`). |
| `.trellis/scripts/guru/guru_supervise.py` | Current Guru supervision runtime: channel run-plan builder, implement-check loop, implementation-review, status/kill CLI. |
| `.trellis/scripts/guru/guru_review_record.py` | Packet schema, target digest, deterministic check, verdict parsing/normalization, append-only implementation review writer. |
| `.trellis/scripts/guru/guru_gate.py` | Gate CLI: check-implementation, slice-plan, commit-plan, check-commit, latest implementation review consumption. |
| `guru-template/overlay/verify/tests/run_tests.sh` | Existing shell fixture suite for gate/supervisor/review-record behavior; already covers slice-plan, latest-row commit gate, status JSON, packet preflight. |
| `packages/cli/test/guru/guru-bundled.test.ts` | TypeScript bundled/template tests for supervisor dry-runs, implementation-review records, commit-plan, sync drift gate. |
| `.codex/agents/trellis-implement.toml`, `.codex/agents/trellis-check.toml` | Direct Codex sub-agent context loading and recursion guard; each requires dispatch prompt first line `Active task: <path>` (`trellis-implement.toml:10-17`, `trellis-implement.toml:31-37`, `trellis-check.toml:10-17`, `trellis-check.toml:31-37`). |
| `.trellis/agents/implement.md`, `.trellis/agents/check.md` | Channel worker definitions for official `trellis channel` backend; distinct from direct Codex sub-agent backend (`implement.md:1-26`, `check.md:7-13`, `check.md:145-160`). |

### Code Patterns

#### SL-02: Parallel Slice Dispatcher

Current dispatcher gap:

- `guru_supervise.py` has no `implement-slices` command. `build_parser()` only registers `requirements`, `overview`, `detail`, `implement`, `check`, `implement-check`, `implementation-review`, `status`, and `kill` (`guru_supervise.py:2053-2104`).
- `build_run_plan()` always constructs `trellis channel create/spawn/send/wait/messages` commands (`guru_supervise.py:604-698`). There is no `codex.dispatch_mode` reader in `SupervisionConfig` or `_load_config()`; `_load_config()` only reads Guru platform/provider/timeouts and channel worker guard values (`guru_supervise.py:473-526`).
- `run_implement_check()` runs exactly one resolved slice, then serially loops implement -> deterministic checks -> check up to `DEFAULT_IMPLEMENT_CHECK_MAX_LOOPS` (`guru_supervise.py:1442-1692`). Multiple packets without `--slice` write a `PACKET_AMBIGUOUS` record and return 2 (`guru_supervise.py:1476-1484`).
- Dry-run for `implement-check` prints one implement plan plus one check plan; both are channel plans (`guru_supervise.py:1552-1584`).
- `build_run_plan()` already emits the `Active task: <task_dir>` line in the worker brief (`guru_supervise.py:786-794`). That is reusable for direct sub-agent briefs, but channel prompts and direct Codex sub-agent prompts are different execution surfaces.

Recommended owner symbols for SL-02:

| Edit point | Owner symbol(s) | Current behavior / risk assumption | GitNexus impact to run first |
| --- | --- | --- | --- |
| Add `implement-slices` CLI and options `--dry-run`, `--parallel`, `--group`, `--backend auto|sub-agent|channel` | `build_parser`, `main` | Parser is argparse-based and command dispatch is centralized; adding a command changes CLI surface and tests. | `impact({target:"build_parser", direction:"upstream"})`, `impact({target:"main", direction:"upstream"})` |
| Read dispatch mode and choose backend | `_load_config`, `SupervisionConfig`, `_config_value` | Existing config model ignores `codex.dispatch_mode`; current default would accidentally keep using channel because `build_run_plan()` hardcodes channel commands. | `impact({target:"_load_config", direction:"upstream"})`, `impact({target:"SupervisionConfig", direction:"upstream"})`, `impact({target:"_config_value", direction:"upstream"})` |
| Reuse single-slice run-plan builder without forcing channel for sub-agent backend | `build_run_plan`, `RunPlan`, `_print_dry_run`, `_execute_plan` | `RunPlan` shape is channel-specific (`create_cmd`, `spawn_cmd`, `send_cmd`, `wait_cmd`, `messages_cmd`). Direct sub-agent backend probably needs a separate dry-run plan/brief instead of fake channel commands. | `impact({target:"build_run_plan", direction:"upstream"})`, `impact({target:"RunPlan", direction:"upstream"})`, `impact({target:"_execute_plan", direction:"upstream"})`, `impact({target:"_print_dry_run", direction:"upstream"})` |
| Build dispatcher loop over slice-plan groups | new helper near `run_implement_check`, plus `run_implement_check` for shared single-slice call shape | `run_implement_check()` owns preflight, packet loading, independent check config, implement/check loop, and structured record append. Dispatcher should call shared helpers rather than duplicate packet/provider logic. | `impact({target:"run_implement_check", direction:"upstream"})`, plus impact on any new helper after creation if refactored |
| Channel backend status/budget integration | `status_action`, `_load_channel_events`, `_terminal_worker_name` | Existing status is channel-only and suitable for channel backend decisions; sub-agent backend must not fabricate channel status. | `impact({target:"status_action", direction:"upstream"})`, `impact({target:"_load_channel_events", direction:"upstream"})` |
| Direct Codex sub-agent prompt parity | `.codex/agents/trellis-implement.toml`, `.codex/agents/trellis-check.toml` | Agents already require `Active task:` first line and forbid nested implement/check dispatch (`trellis-implement.toml:10-17`, `trellis-implement.toml:31-37`; `trellis-check.toml:10-17`, `trellis-check.toml:31-37`). CLI cannot itself call the platform Agent tool, so sub-agent backend should likely dry-run/output dispatch briefs for the main session. | For files, run GitNexus impact on relevant template writer/configurator symbols if edited; for runtime symbols, run impacts above. |

Key SL-02 implementation hazard:

- If `implement-slices --backend auto` reuses `build_run_plan()` blindly, it will create channel workers in this repo despite `.trellis/config.yaml codex.dispatch_mode: sub-agent` (`.trellis/config.yaml:70-72`). That would violate the task PRD and design (`prd.md:40-43`, `design.md:209-217`).

#### SL-03: Worker Isolation / Dirty Scope / Packet Target Validation / Overlap

Current path/dirty behavior:

- `guru_review_record.load_packet()` validates packet structure, non-empty `target_paths`, non-empty `invariants`, risk enum, semantic review provider, deterministic check strings, and `dirty_state.unrelated` shape (`guru_review_record.py:136-180`).
- `guru_review_record._clean_target_paths()` provides the strongest path normalization/escape guard for target paths and is used by `target_snapshot_digest()` (`guru_review_record.py:197-225`, `guru_review_record.py:546-617`).
- `guru_gate._dirty_scope_for_packet()` uses `guru_risk.scan_dirty_paths()`, filters with `guru_risk._is_scannable()`, and checks dirty paths with `_path_in_targets()` prefix semantics (`guru_gate.py:3927-3941`, `guru_gate.py:3151-3163`).
- `guru_supervise._scope_preflight()` also scans dirty paths, but it checks `p not in targets` with an exact `set(packet["target_paths"])` membership test (`guru_supervise.py:1187-1202`). This is stricter and inconsistent with `guru_gate._path_in_targets()`; a packet target like `lib` can cover `lib/x.dart` in gate, but not in supervisor preflight.
- `guru_supervise._staged_target_drift()` checks staged paths against `_path_covered_by_targets()` and then rejects unstaged overlap (`guru_supervise.py:1241-1269`). `_path_covered_by_targets()` lacks the `target == "."` special case that `guru_gate._path_in_targets()` has (`guru_supervise.py:1241-1242`, `guru_gate.py:3151-3163`).
- No symbol currently computes pairwise `target_paths` overlap or resource-lock conflicts across packets. `slice-plan` reports per-packet dirty state only and marks multiple packets as ambiguous (`guru_gate.py:3944-4003`).
- `run_deterministic_checks()` executes commands but does not infer resource locks; lock inference should happen before dispatch, not only when commands run (`guru_review_record.py:769-817`).

Recommended owner symbols for SL-03:

| Edit point | Owner symbol(s) | Current behavior / risk assumption | GitNexus impact to run first |
| --- | --- | --- | --- |
| Centralize path normalization / containment / overlap | `guru_review_record._clean_target_paths`, `guru_review_record._target_contains_path`, `guru_gate._path_in_targets`, `guru_supervise._path_covered_by_targets` | Three implementations exist; they differ on prefix and `"."` handling. A shared helper in `guru_review_record.py` avoids import cycles because `guru_review_record.py` intentionally does not import gate/supervise (`guru_review_record.py:1-10`). | `impact({target:"_clean_target_paths", direction:"upstream"})`, `impact({target:"_target_contains_path", direction:"upstream"})`, `impact({target:"_path_in_targets", direction:"upstream"})`, `impact({target:"_path_covered_by_targets", direction:"upstream"})` |
| Fix/extend dirty-scope isolation for dispatcher | `_scope_preflight`, `_dirty_scope_for_packet` | Gate and supervisor preflight can disagree; dispatcher must use one fail-closed model before spawning writer slices. `scan_dirty_paths` failure is fail-closed in supervisor but `"unknown"` advisory in slice-plan. | `impact({target:"_scope_preflight", direction:"upstream"})`, `impact({target:"_dirty_scope_for_packet", direction:"upstream"})` |
| Add pairwise target overlap / serial fallback reasons | new helper near packet/target functions, likely consumed by `_slice_plan_payload` and new dispatcher | Current `slice-plan` has no `parallel_groups`, no `depends_on`, no overlap metadata, and no per-slice `parallel_blockers` (`guru_gate.py:3947-3998`). | After naming helper, run impact on it; before edits run `impact({target:"_slice_plan_payload", direction:"upstream"})` and `impact({target:"load_packet", direction:"upstream"})` |
| Enforce spawn-time revalidation | new helper called by dispatcher, plus `_slice_review_target` / `run_implement_check` if shared | Design requires plan-time and spawn-time checks; current implement-check preflights a single slice only once before worker launch (`guru_supervise.py:1490-1504`). | `impact({target:"_slice_review_target", direction:"upstream"})`, `impact({target:"run_implement_check", direction:"upstream"})` |
| Resource-lock inference from deterministic checks | `run_deterministic_checks` should probably not own inference; a new pure helper can inspect `deterministic_checks` without executing them | Existing deterministic checks are raw shell strings and can include broad package/test commands (`guru_review_record.py:769-817`); lock inference must stay conservative and dry-run friendly. | `impact({target:"run_deterministic_checks", direction:"upstream"})`; impact new helper after creation |
| Preserve packet schema compatibility | `load_packet` | Adding optional fields like `depends_on`, `parallel_mode`, `resource_locks` is additive only if validation remains backward compatible. Required field changes would break existing packet fixtures (`run_tests.sh:3621-3718`). | `impact({target:"load_packet", direction:"upstream"})` |

Key SL-03 implementation hazards:

- Do not trust a stale `slice-plan` payload at dispatch time. The design explicitly says dispatcher must reread current disk state before spawn (`design.md:162-165`, `design.md:271-277`).
- Do not classify writer parallelism as safe merely because packet file names differ; current packet schema does not prove target disjointness.
- Treat directory-prefix overlap as overlap. Also normalize `./`, backslashes, and `"."` consistently across gate, supervisor, and digest code.
- If scanner status is unknown, dispatcher should block writer parallelism or downgrade to serial/read-only; otherwise `slice-plan` can look less strict than `implement-check`.

#### SL-04: Review Coverage Aggregation / Commit Tail

Current latest-row commit model:

- `_latest_jsonl_record()` reads `review-records/implementation-reviews.jsonl` and returns only the last valid JSON object (`guru_gate.py:3128-3148`).
- `_implementation_review_problem()` validates only that latest record is clean/current/required, that staged paths are covered by latest `target_paths`, and that latest `reviewed_target_digest` matches the current staged index digest for those target paths (`guru_gate.py:3166-3215`).
- `_review_commit_stage_paths()` computes allowed/forbidden paths from only one record (`guru_gate.py:4095-4108`).
- `_commit_plan_payload()` calls `_latest_jsonl_record()`, then `_implementation_review_problem()`, then `_review_commit_stage_paths()`; `cmd_check_commit()` consumes the same plan, so fixing `_commit_plan_payload()` fixes both `commit-plan` and `check-commit` (`guru_gate.py:4111-4285`, `guru_gate.py:4304-4335`).
- `_implementation_review_command()` always recommends `implementation-review <task> --staged` and cannot yet recommend per-slice `implementation-review --slice <id>` (`guru_gate.py:3455-3458`).
- `guru_review_record._append_supervisor_review_record()` computes and stores `reviewed_target_digest`, but records currently do not store a `reviewed_target_digest_source` field. The digest source is known in `ReviewTarget.digest_source` (`guru_supervise.py:210-218`, `guru_supervise.py:1390-1429`), but `_RECORD_FIELDS` omits it (`guru_review_record.py:187-194`).

Recommended owner symbols for SL-04:

| Edit point | Owner symbol(s) | Current behavior / risk assumption | GitNexus impact to run first |
| --- | --- | --- | --- |
| Replace latest-row loader with review-set loader | `_latest_jsonl_record` or new `_implementation_review_records` helper | `_latest_jsonl_record()` is the exact latest-row bottleneck. It can be kept for legacy recovery but should not authorize multi-slice staged scope globally. | `impact({target:"_latest_jsonl_record", direction:"upstream"})` |
| Validate each clean record and aggregate coverage | `_implementation_review_problem`, `_review_commit_stage_paths`, new coverage helper | Existing problem function returns one string for one record. A review-set helper likely needs structured result: covered paths, uncovered paths, stale digests, covering reviews, required commands. | `impact({target:"_implementation_review_problem", direction:"upstream"})`, `impact({target:"_review_commit_stage_paths", direction:"upstream"})` |
| Emit `review_coverage` in commit-plan | `_new_commit_plan`, `_finish_commit_plan`, `_commit_plan_payload` | Existing plan schema has allowed/forbidden paths but no review coverage section (`guru_gate.py:3486-3515`). Adding fields must remain additive. | `impact({target:"_new_commit_plan", direction:"upstream"})`, `impact({target:"_finish_commit_plan", direction:"upstream"})`, `impact({target:"_commit_plan_payload", direction:"upstream"})` |
| Keep `check-commit` aligned with `commit-plan` | `cmd_check_commit` | `cmd_check_commit()` already calls `_commit_plan_payload()`, so avoid introducing a second decision model (`guru_gate.py:4304-4335`). | `impact({target:"cmd_check_commit", direction:"upstream"})` |
| Recommend slice-specific missing review commands | `_implementation_review_command`, `_slice_plan_payload`, `guru_review_record.list_packets`, `guru_review_record.load_packet` | Current command builder only emits staged review. If staged path maps to one packet target, prefer `implementation-review --slice <id>`; otherwise `--staged`. | `impact({target:"_implementation_review_command", direction:"upstream"})`, `impact({target:"_slice_plan_payload", direction:"upstream"})`, `impact({target:"list_packets", direction:"upstream"})`, `impact({target:"load_packet", direction:"upstream"})` |
| Persist digest source if needed | `ReviewTarget`, `_append_supervisor_review_record`, `normalize_review_record`, `_RECORD_FIELDS`, `append_record` | Existing records store `reviewed_target_digest` but not whether it was computed from `worktree` or `index`. Multi-slice commit coverage may need this to explain stale/unsafe records. | `impact({target:"ReviewTarget", direction:"upstream"})`, `impact({target:"_append_supervisor_review_record", direction:"upstream"})`, `impact({target:"normalize_review_record", direction:"upstream"})`, `impact({target:"append_record", direction:"upstream"})` |
| Keep digest computation reusable | `target_snapshot_digest` | Existing code can compute worktree or index digest for a target set and already excludes task/workspace snapshot paths (`guru_review_record.py:546-617`, `guru_review_record.py:228-238`). | `impact({target:"target_snapshot_digest", direction:"upstream"})` |

Key SL-04 implementation hazards:

- A latest clean review for slice B currently authorizes only B's `target_paths`; it must not authorize staged paths for slice A. This is the exact behavior the PRD rejects (`prd.md:60-67`).
- Full/lite commit-plan recovery must remain compact: if contract/staged scope is invalid, do not recommend extra implementation-review commands (`guru_gate.py:4277-4282`; existing TS tests assert this around `guru-bundled.test.ts:2977-3040`).
- Task/workspace artifacts remain forbidden for implementation commits and should not count as covered implementation paths (`guru_gate.py:3188-3205`, `guru_gate.py:4201-4207`).
- If adding new record fields, keep `append_record()` as the single writer/validator and preserve supplemental/manual behavior (`guru_review_record.py:620-655`, `guru_review_record.py:861-962`, `guru_review_record.py:970-1010`).

#### Status JSON / Worker Lifecycle

- `status_action()` is channel-specific: it shells out to `trellis channel list --all --json`, filters channels by `guru-<task>-` prefix or task path, reads last 200 raw events, projects live vs terminal workers, and emits `cleanup_available`, one `cleanup_command`, and `cleanup_candidates` (`guru_supervise.py:1873-2025`).
- Terminal event attribution uses `_terminal_worker_name()`; it respects explicit `worker`, `supervisor:<worker>`, and ignores `cli:*` unless `worker` is present (`guru_supervise.py:1861-1870`).
- Existing tests already cover live/terminal split, blocking only on live, cleanup command, and `cli:kill` attribution (`run_tests.sh:4405-4457`).
- For sub-agent backend, status must be a dispatch report from the main/session side, not channel event replay. If SL-02 stores optional dispatch evidence, it must not make `guru_supervise.py status --json` pretend there are channel workers.

Recommended owner symbols:

| Edit point | Owner symbol(s) | Current behavior / risk assumption | GitNexus impact to run first |
| --- | --- | --- | --- |
| Channel status stays channel-only | `status_action`, `_load_channel_events`, `_terminal_worker_name` | Any schema additions must preserve existing `schema_version: 1`, live/terminal counts, `blocking`, and cleanup command behavior. | `impact({target:"status_action", direction:"upstream"})`, `impact({target:"_terminal_worker_name", direction:"upstream"})` |
| Dispatcher consumes status | new dispatcher helper plus `status_action` if reusing JSON | Good path: call or reuse channel status only for channel backend; report sub-agent dispatch separately. | Impact new helper after creation; run status impacts above before edits |
| Kill/cleanup action | `kill_action` | Existing cleanup command is `guru_supervise.py kill ... --channel ... --worker ...`; changing it alters tests and user recovery. | `impact({target:"kill_action", direction:"upstream"})` |

### Suggested GitNexus Impact Checklist

Run these before editing, grouped by likely slice. If GitNexus returns HIGH or CRITICAL, pause and warn the main session before edits.

SL-02:

- `build_parser`
- `main`
- `_load_config`
- `SupervisionConfig`
- `RunPlan`
- `build_run_plan`
- `_print_dry_run`
- `_execute_plan`
- `run_implement_check`
- `status_action`
- `_load_channel_events`
- `_terminal_worker_name`

SL-03:

- `load_packet`
- `_clean_target_paths`
- `_target_contains_path`
- `_path_in_targets`
- `_path_covered_by_targets`
- `_scope_preflight`
- `_dirty_scope_for_packet`
- `_slice_review_target`
- `_staged_target_drift`
- `_slice_plan_payload`
- `run_deterministic_checks`
- `target_snapshot_digest`

SL-04:

- `_latest_jsonl_record`
- `_implementation_review_problem`
- `_review_commit_stage_paths`
- `_implementation_review_command`
- `_new_commit_plan`
- `_finish_commit_plan`
- `_commit_plan_payload`
- `cmd_commit_plan`
- `cmd_check_commit`
- `ReviewTarget`
- `_append_supervisor_review_record`
- `normalize_review_record`
- `append_record`
- `target_snapshot_digest`

### Mirror / Sync Map

Python Guru runtime mirrors:

- Live scripts:
  - `.trellis/scripts/guru/guru_gate.py`
  - `.trellis/scripts/guru/guru_supervise.py`
  - `.trellis/scripts/guru/guru_review_record.py`
  - `.trellis/scripts/guru/guru_risk.py`
  - `.trellis/scripts/guru/guru_contract.py`
- Guru template SSOT mirror:
  - `guru-template/overlay/verify/guru_gate.py`
  - `guru-template/overlay/verify/guru_supervise.py`
  - `guru-template/overlay/verify/guru_review_record.py`
  - `guru-template/overlay/verify/guru_risk.py`
  - `guru-template/overlay/verify/guru_contract.py`
- Bundled CLI template mirror:
  - `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_review_record.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_contract.py`
- Read-only `cmp` check in this research found these three locations currently byte-identical for the five Guru verify scripts.

Workflow / prompt mirrors:

- Live workflow / task dispatch text:
  - `.trellis/workflow.md`
  - `packages/cli/src/templates/trellis/workflow.md`
- Channel worker definitions:
  - `.trellis/agents/implement.md`
  - `.trellis/agents/check.md`
  - `packages/cli/src/templates/trellis/agents/implement.md`
  - `packages/cli/src/templates/trellis/agents/check.md`
- Direct Codex sub-agent definitions:
  - `.codex/agents/trellis-implement.toml`
  - `.codex/agents/trellis-check.toml`
  - likely source template copies under `packages/cli/src/templates/codex/agents/`
- Guru workflow templates:
  - `guru-template/workflows/guru-client-workflow.md`
  - `guru-template/workflows/guru-go-workflow.md`
  - `guru-template/workflows/guru-h5-workflow.md`
  - `guru-template/workflows/guru-ios-workflow.md`
  - `packages/cli/src/templates/guru/workflows/guru-client.md`
  - `packages/cli/src/templates/guru/workflows/guru-go.md`
  - `packages/cli/src/templates/guru/workflows/guru-h5.md`
  - `packages/cli/src/templates/guru/workflows/guru-ios.md`

Mirror caveat:

- Raw `cmp` found `.trellis/workflow.md` differs from `packages/cli/src/templates/trellis/workflow.md`, and the `guru-template/workflows/*-workflow.md` files differ from the `packages/cli/src/templates/guru/workflows/guru-*.md` files. This may be expected template transformation/naming, but do not assume byte sync for workflow files. Use `pnpm --filter @devsc/trellis run sync:guru:check` and existing template tests as the source of truth.
- `packages/cli/package.json` defines `sync:guru` and `sync:guru:check`; `prepublishOnly` runs `sync:guru:check` before tests/build (`packages/cli/package.json:32`, `packages/cli/package.json:41-42`).
- Existing TS tests include a sync drift gate that expects `sync:guru:check` to pass when bundled mirrors match and fail on injected drift (`guru-bundled.test.ts:3789-3820`).

### Minimal Test Suggestions

Baseline compile:

```bash
python3 -m py_compile \
  .trellis/scripts/guru/guru_gate.py \
  .trellis/scripts/guru/guru_supervise.py \
  .trellis/scripts/guru/guru_review_record.py \
  .trellis/scripts/guru/guru_risk.py
```

Mirror compile:

```bash
python3 -m py_compile \
  guru-template/overlay/verify/guru_gate.py \
  guru-template/overlay/verify/guru_supervise.py \
  guru-template/overlay/verify/guru_review_record.py \
  guru-template/overlay/verify/guru_risk.py \
  packages/cli/src/templates/guru/overlay/verify/guru_gate.py \
  packages/cli/src/templates/guru/overlay/verify/guru_supervise.py \
  packages/cli/src/templates/guru/overlay/verify/guru_review_record.py \
  packages/cli/src/templates/guru/overlay/verify/guru_risk.py
```

Focused behavior fixtures:

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
```

Add/update shell fixtures around these existing sections:

- Slice-plan / high-full packet preflight: `run_tests.sh:4153-4392`.
- Status JSON projection: `run_tests.sh:4405-4457`.
- Packet schema and `run_implement_check` preflight: `run_tests.sh:3621-3813`.
- Verdict normalization / implementation-review structured records: `run_tests.sh:3815-3955`.
- Commit-plan/check-commit latest-row cases: `run_tests.sh:1429-1660`.

Focused TypeScript/template tests:

```bash
pnpm --filter @devsc/trellis exec vitest run test/guru/guru-bundled.test.ts
```

Existing TS assertions to extend:

- Implementation-review dry-run and staged record acceptance: `guru-bundled.test.ts:2583-2775`.
- Commit-plan recommendation behavior for missing/malformed/stale review records and invalid staged scope: `guru-bundled.test.ts:2880-3040`.
- Sync drift gate: `guru-bundled.test.ts:3789-3820`.

Sync / broader checks after mirrored edits:

```bash
pnpm --filter @devsc/trellis run sync:guru:check
pnpm --filter @devsc/trellis run lint
pnpm --filter @devsc/trellis run typecheck
```

Before commit, main session should also run GitNexus `detect_changes()` per AGENTS.md / task plan after implementation, not during this read-only research.

## Caveats / Not Found

- No product code or template code was edited; only this research file was written under the task `research/` directory.
- No GitNexus impact calls were run in this research. The file lists target symbols for the later implementer/main session to run before edits.
- No `implement-slices` command exists today.
- No `parallel_groups` field exists in current `slice-plan` output; current `schema_version` is 1 and output is per-slice plus global blockers.
- No review-set aggregation helper exists today; `commit-plan` and `check-commit` still consume only `_latest_jsonl_record(...)`.
- No sub-agent backend status store exists today. `guru_supervise.py status --json` is channel-event based and should stay honest about that backend.
- Path containment logic is duplicated and inconsistent across `guru_review_record.py`, `guru_gate.py`, and `guru_supervise.py`; this is the highest-risk SL-03 area.
- External references were not needed; all evidence came from repo-local workflow/spec/task/code/test files. Local package versions observed: `@devsc/trellis` is `0.6.0-guru.1`, Vitest is declared as `^4.0.18`, TypeScript as `^5.7.2` (`packages/cli/package.json:1-3`, `packages/cli/package.json:68-79`).
