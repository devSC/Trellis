# Implementation Plan

## Current Outcome-first Execution Authority (2026-07-15)

The requirement package and `prd.md` milestones M0-M4 supersede the six-slice/wave/bootstrap-burn execution sequence below. The remaining work is:

1. M1 operational route proof - candidate complete; evidence in `M1_OPERATIONAL_ROUTE_PROOF.md`.
2. M2 all-intent compounding and Gate-value proof - candidate complete; evidence in `M2_ALL_INTENT_COMPOUNDING_PROOF.md`.
3. M3 official Custom/Template cutover readiness using the existing rollback-bundle implementation - candidate complete; evidence in `M3_CUSTOM_TEMPLATE_CUTOVER_PROOF.md`.
4. M4 final consistency, spec update, final check and commit - current milestone.

Marketplace catalog, ExtensionManager WAL, trusted reviewer identity, generic replay infrastructure, bootstrap burn/reuse and six independent slice lifecycles are deferred non-requirements. The historical plan below remains read-only rationale and must not be used to block or sequence the current milestones.

## 计划与交付策略

使用一个 full-chain task 内的独立 vertical slices，避免为每个内部模块重复创建/确认任务。每个 slice 必须先有失败测试或可复现实验，再实现最小行为，完成局部检查后才进入下一片。功能阶段只允许修改 `guru-template/index.json`、`guru-template/workflows/**`、`guru-template/specs/**`、`guru-template/overlay/**`。

`python3 .trellis/scripts/guru/guru_gate.py slice-plan <task_dir>` 只是只读 inventory/preflight，当前 CLI 不接受 `--slice`。多个 packet 存在时顶层 `PACKET_AMBIGUOUS_WITHOUT_SLICE` 是预期提示：它只表示后续 writer/reviewer 命令必须显式选择 packet，不表示 `slice-plan` 自身失败。显式选择属于 `guru_supervise.py implement-check <task_dir> --slice <slice_id>` 和 `guru_supervise.py implementation-review <task_dir> --slice <slice_id>`。

功能阶段不把 candidate 文件反向复制进本仓库 `.trellis/scripts/guru/**`：该目录是当前 checkout 的 historical installed authority，不在已确认 allowed paths 内。V2 candidate 的结构 Gate、review 记录和回归必须直接运行 `guru-template/overlay/verify/guru_gate.py`；安装闭合只通过 Extension 的临时目标 E2E 验证。这样既避免用旧 local Gate 给新合同假盖章，也不把 dogfood 同步变成未审核的第二写入路径。

下表是 logical eligibility frontier，不是当前 `slice-plan` 的展示顺序：

| Topological wave | Required packet |
| --- | --- |
| Wave 1A, bootstrap owner | `delivery-control` |
| Wave 1B, parallel with 1A | `marketplace-catalog` |
| Wave 2A, after delivery-control | `semantic-review` |
| Wave 2B, after marketplace-catalog | `extension-manager` |
| Wave 3, after semantic-review | `bounded-context` |
| Wave 4, after all prior packets | `design-sync-replay` |

`depends_on` is authoritative. `completed` 只包含具有 current structured clean implementation review、`deterministic_checks=passed`、`invariant_coverage=all_passed`、`supervisor_failure=none` 和 `required_satisfied=true` 的 slice；`eligible` 只包含全部 `depends_on` 均在 `completed` 的 packet。初始 eligible=`delivery-control, marketplace-catalog`；两者分别完成后解锁 `semantic-review, extension-manager`；`semantic-review` 完成后解锁 `bounded-context`；前五个全部完成后才解锁 `design-sync-replay`。V2 Supervisor 必须验证完整图、拓扑排序并拒绝 missing/self/cycle；文件名、JSON array 和现有 `slice-plan` 展示顺序从不授予执行权。

Bootstrap limitation: 当前 `slice-plan` 不消费完成证据，`implement-slices` 只生成 dispatch JSON，legacy scope preflight 还会把已验证前序 slice 的 dirty outputs 当成后续 out-of-scope。故在 v2 Supervisor 落地前，不得声称现有 CLI 能自动连续执行 Wave 1→2，也不得把 g1 输出当作实际并发启动证明。本任务 root orchestrator 只能在一次性 bootstrap audit 下，对初始 eligible packets 先分别执行 `--dry-run`，再按 packet target paths 直接派发隔离 sub-agent；Wave 2/3 同样由上述 evidence predicate 显式选择。不得用 `dirty_state.unrelated` 吞掉前序实现。V2 Supervisor 必须把 current、digest-matching、clean-reviewed predecessor snapshots 作为只读 baseline，之后 Wave 4 才能由新入口调度。

### Historical bootstrap chain and current burn verifier

The verified-consumed source is historical evidence, not the current executable: SHA-256 `e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3` is preserved at `bootstrap/archive/bootstrap_start.e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3.py`. The four-event live chain already ends in `retry_consumed(verified)`, so another `run` is forbidden. The current hardened status/burn verifier is `bootstrap/bootstrap_start.py` at SHA-256 `88b8d467d167d617e0ee525c9b78f7f0ec4ee602e45976e0263b028a56d88f99`; it validates the immutable archive and all current Gate/risk/envelope/review/capability inputs but cannot rewrite historical source identity.

```bash
TASK=.trellis/tasks/07-14-custom-first-guru-delivery-control
HISTORICAL_BOOTSTRAP="$TASK/bootstrap/archive/bootstrap_start.e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3.py"
HISTORICAL_BOOTSTRAP_SHA256=e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3
CURRENT_BOOTSTRAP="$TASK/bootstrap/bootstrap_start.py"
CURRENT_BOOTSTRAP_SHA256=88b8d467d167d617e0ee525c9b78f7f0ec4ee602e45976e0263b028a56d88f99
test "$(shasum -a 256 "$HISTORICAL_BOOTSTRAP" | awk '{print $1}')" = "$HISTORICAL_BOOTSTRAP_SHA256"
test "$(shasum -a 256 "$CURRENT_BOOTSTRAP" | awk '{print $1}')" = "$CURRENT_BOOTSTRAP_SHA256"
python3 -m unittest discover -s "$TASK/bootstrap/tests" -p 'test_bootstrap_start.py'
python3 "$CURRENT_BOOTSTRAP" status "$TASK" --slice delivery-control --source-sha256 "$CURRENT_BOOTSTRAP_SHA256"
# No further bootstrap run is legal: the task is in_progress and retry_consumed is verified.
```

After final Requirements/Overview/Detail batch review and one user reconfirmation, current risk/envelope rebuilding, and one clean Codex check-only `delivery-control` implementation review, create canonical schema-v3 `bootstrap/burn-evidence.json`. In addition to the exact identity/selection fields and `implementation_review_run_id`, it must contain the exact migration-only authorization `{kind:codex_same_provider_user_directive_v1,user_directive:关闭调用claude,provider:codex,review_mode:check_only,independence_claim:none,trusted_review_envelope_eligible:false}`. The verifier derives and revalidates every hash itself, requires the task to remain `in_progress`, binds the pre-launch target-only index digest and deterministic-result digest into the official Worker prompt, parses the final Worker message through the official review normalizer, and requires canonical equality with the selected record plus equal post-worker index/current-worktree/final-CAS digests. Caller-supplied SHA claims are rejected. This evidence cannot satisfy `TrustedReviewEnvelopeV1` or any future independent-review count. Burn uses the same still-live target-only temporary index and is shown in the block below; deleting or switching that index before burn is forbidden.

### Temporary index review and Supervisor cutover

Per-slice staged review uses a fresh temporary index initialized from `HEAD`, then stages only the packet target paths. Copying the real mixed index is forbidden because it retains 48 paths outside this slice; after adding the Custom supervisor source required for pre-launch digest binding, the target-only construction has 23 staged paths and zero outside-target paths. The real index is never selected through `GIT_INDEX_FILE`, rebuilt or cleared; only its staged tree/path snapshot is compared before and after because Git may refresh stat-cache bytes during unrelated reads. This fixes only the staged review target; legacy `implement-check` still scans the full worktree and still misclassifies clean-reviewed predecessor outputs. Therefore root direct dispatch remains the one-time authority until v2 Supervisor cutover.

The review must run as one official Codex channel `check` worker so the verifier can read the platform-issued thread/session id and raw control-plane capture. `TRELLIS_CHANNEL_ROOT` must remain unset: redirected channel storage is rejected. The official supervisor derives the only accepted channel/worker names from the review run id and writes a canonical `review_invocation_contract` containing the run id, target, pre-launch digest, target-path digest, deterministic-result digest, provider tuple, override source and exact user directive. Temporarily select `codex.dispatch_mode=channel` through project `.trellis/config.yaml`, keep `guru.supervision.provider=codex` and `high_risk_review_provider_policy=codex`, then restore the config byte-for-byte immediately after the review record and terminal capture exist. This changes transport only; it never selects or invokes Claude.

```bash
SLICE=delivery-control
PACKET="$TASK/slice-packets/$SLICE.json"
REAL_INDEX_TREE_BEFORE="$(git write-tree)"
REAL_INDEX_PATHS_BEFORE="$(git diff --cached --name-status | shasum -a 256 | awk '{print $1}')"
TMP_INDEX_DIR="$(mktemp -d)"
TMP_INDEX="$TMP_INDEX_DIR/index"
trap 'rm -rf "$TMP_INDEX_DIR"' EXIT
env GIT_INDEX_FILE="$TMP_INDEX" git read-tree HEAD
python3 -c 'import json,os,subprocess,sys; p=json.load(open(sys.argv[1])); e=dict(os.environ,GIT_INDEX_FILE=sys.argv[2]); subprocess.check_call(["git","add","-A","--",*p["target_paths"]],env=e)' "$PACKET" "$TMP_INDEX"
env GIT_INDEX_FILE="$TMP_INDEX" python3 guru-template/overlay/verify/guru_supervise.py implementation-review "$TASK" --slice "$SLICE" --staged --same-provider --user-quote "关闭调用claude" --dry-run
env GIT_INDEX_FILE="$TMP_INDEX" python3 guru-template/overlay/verify/guru_supervise.py implementation-review "$TASK" --slice "$SLICE" --staged --same-provider --user-quote "关闭调用claude"
test "$(git write-tree)" = "$REAL_INDEX_TREE_BEFORE"
test "$(git diff --cached --name-status | shasum -a 256 | awk '{print $1}')" = "$REAL_INDEX_PATHS_BEFORE"
env -u TRELLIS_CHANNEL_ROOT GIT_INDEX_FILE="$TMP_INDEX" python3 "$CURRENT_BOOTSTRAP" burn "$TASK" --slice delivery-control --source-sha256 "$CURRENT_BOOTSTRAP_SHA256" --evidence "$TASK/bootstrap/burn-evidence.json"
env -u TRELLIS_CHANNEL_ROOT GIT_INDEX_FILE="$TMP_INDEX" python3 "$CURRENT_BOOTSTRAP" status "$TASK" --slice delivery-control --source-sha256 "$CURRENT_BOOTSTRAP_SHA256"
rm -rf "$TMP_INDEX_DIR"
trap - EXIT
```

Cutover order is fixed: root directly dry-runs, dispatches, checks and staged-reviews `delivery-control`, then burns bootstrap; root does the same for `marketplace-catalog`, `semantic-review`, and `extension-manager` as each dependency becomes eligible; root directly implements/reviews `bounded-context`; only after its v2 Supervisor replay proves dependency graph validation plus digest-bound clean-reviewed predecessor snapshots does the new Supervisor become dispatch authority for `design-sync-replay`. Every symbol impact and final change scan uses the repo-pinned form `node .gitnexus/run.cjs ... --repo "$PWD"`; no bare global-repo lookup is accepted.

## UNIT implementation trace contract

下表是计划合同，不是执行证据。`pending` 只能由真实代码、测试结果和 implementation review 证据推进；规划文本不得改写为完成状态。

| UNIT | Planned module | Planned symbol | Test command | Expected result | Status |
| --- | --- | --- | --- | --- | --- |
| UNIT-marketplace-catalog | `guru-template/overlay/verify/guru_catalog.py` | `CatalogResolver` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_guru_catalog.py'` | typed workflow/spec resolution passes; invalid source/path cases fail closed | pending |
| UNIT-extension-manager | `guru-template/overlay/verify/guru_overlay.py`; `guru-template/overlay/verify/guru_install_journal.py` | `ExtensionManager`; `TransactionJournal` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_extension_manager.py'` | apply/adopt/upgrade/unapply and crash recovery preserve ownership and pre-state | pending |
| UNIT-delivery-policy | `guru-template/overlay/verify/guru_delivery_policy.py` | `resolve_delivery_selection`; `build_risk_packet` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_delivery_policy.py'` | intent/route matrix, promotion, risk packet and budget constraints pass | pending |
| UNIT-start-guard | `guru-template/overlay/hooks/guru_task.py` | `start_with_guard`; `compensate_after_start` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_start_guard.py'` | only current packet/risk/attestation tuple can start; compensation never claims enforcement | pending |
| UNIT-semantic-digest | `guru-template/overlay/verify/guru_digest.py` | `SemanticDigestService` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_semantic_digest.py'` | manifest closure and dependency invalidation are deterministic; execution JSONL is excluded | pending |
| UNIT-review-identity | `guru-template/overlay/verify/guru_review_identity.py` | `validate_review_identity`; `fingerprint_finding` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_review_identity.py'` | same-reviewer or same-context conflicts, stale/tampered records and prose-only finding changes fail closed | pending |
| UNIT-bounded-supervisor | `guru-template/overlay/verify/guru_supervise.py`; `guru-template/overlay/verify/guru_provider_runner.py` | `SupervisorStateMachine`; `ManagedProviderRunner` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_bounded_supervisor.py'`; `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_provider_runner.py'` | legal transitions, terminal idempotence, provider leases, budget events and cleanup pass with fake clock | pending |
| UNIT-context-reuse | `guru-template/overlay/verify/guru_context.py` | `ContextPlanner` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | fenced current context and deterministic trimming pass; stale/broad recall is rejected | pending |
| UNIT-design-sync | `guru-template/overlay/verify/guru_design_sync.py` | `DesignSyncService`; `verify-legacy-transition` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_design_sync.py'` | project SSOT/trace closure fails on a broken edge; pinned legacy debt stays non-green and any inventory/fingerprint/boundary regression blocks | pending |
| UNIT-replay-benchmark | `guru-template/overlay/verify/guru_replay.py` | `ReplayBenchmark` | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_replay_benchmark.py'` | all mandatory time/context/token ratios and hard release budgets pass independently | pending |

## Slice 0 — Baseline, impact, and executable policy contract

- [ ] 修复或重建 GitNexus index；对每个待修改 symbol 运行 upstream impact 并记录风险。
- [ ] 保存两个失败会话的最小 replay facts，不复制完整敏感 transcript。
- [ ] 新增 delivery policy schema/default fixture 和 route matrix failing tests。
- [ ] 新增 Core-zero guard：测试/脚本断言功能 slices 不修改 `packages/cli/src/**`、`packages/core/**`。
- [ ] 固定 bundled-v1 transition baseline：commit/tree/test OID、Vitest 版本、完整 82-test inventory digest、zero skip/todo 与五个 failure fingerprints；禁止只保存 `82/77/5` 数量或把 known debt 列入 mandatory-green。
- [ ] 保存 legacy bundled v1 baseline/coupling inventory 与 dirty-worktree exclusions；v1 是兼容快照，不是 v2 mirror/fallback。

**Stop/rollback**：GitNexus impact 不可用时不得编辑 Python symbol；先修索引或建立可审计 CLI impact 路径。

## Wave 1B — Official marketplace completeness

**设计承接**：UNIT-marketplace-catalog。

**执行 packet**：`slice-packets/marketplace-catalog.json`（运行时必须 `--slice marketplace-catalog`）。

- [ ] 为 Flutter、Go、H5、iOS 的 spec/workflow 补齐稳定 `index.json` entries。
- [ ] 增加 index schema、id uniqueness、path existence/type 测试。
- [ ] 使用官方 resolver/干净临时项目验证 `trellis init --registry/--template/--workflow-source/--workflow`。
- [ ] 验证瞬态错误不会静默 fallback 到 bundled Guru。

**Rollback**：仅回退新增 registry entries/tests，不影响既有 Flutter ids。

## Wave 2B — Reversible Extension Manager

**设计承接**：UNIT-extension-manager。

**执行 packet**：`slice-packets/extension-manager.json`（运行时必须 `--slice extension-manager`）。

- [ ] 先定义 typed install-state、managed file、config change、capability 和 operation result contracts。
- [ ] 新增 `extension-manifest.json` 与 `plan/apply/adopt/upgrade/status/verify/unapply/recover` CLI/exit-code contract。
- [ ] 实现只读 `plan`/`status`，覆盖现有安装和 adopt 冲突。
- [ ] 实现事务式 `apply`，durable backup/PREPARED WAL 先于首写、逐 op fsync、atomic state publish、显式 recover。
- [ ] 实现 `verify`，检查 Template/Extension version、managed hashes、workflow source/id、platform capability 和必要 Gate wiring。
- [ ] 实现 `unapply`，只删除 hash-matching ownership，恢复 pre-state，用户修改 fail-closed 保留。
- [ ] 将 `apply.sh` 收敛为兼容 wrapper，不保留第二套 ownership 真源。
- [ ] 覆盖 fresh/repeat/adopt/upgrade/failure/user-edit/unapply/missing-null-value/list identity/path swap/symlink/lock/PID reuse/crash-point 测试。

**Rollback**：回退整个 slice；`apply.sh` 只能是 manager wrapper，禁止运行时 fallback 到旧可写 engine。新 manager 未 publish install-state 时由 durable journal recover，不得留下无真源半安装。

## Wave 1A — Universal route policy and start guard

**设计承接**：UNIT-delivery-policy、UNIT-start-guard。

**执行 packet**：`slice-packets/delivery-control.json`（运行时必须 `--slice delivery-control`）。

**唯一 ownership**：`guru_gate.py`、v2 contract/inventory validator 与 `verify/tests/run_tests.sh` 属于本 slice；`semantic-review` 不再拥有这些路径。Detail inventory 前置阻断必须在 Wave 1 交付，packet target overlap 保持 0。

<!-- GURU:RISK_DECISION_INVENTORY:START -->
```json
{
  "schema_version": 1,
  "task_id": "custom-first-guru-delivery-control",
  "scope": {
    "selected_slice_id": "delivery-control",
    "official_start_authority": "selected_slice_only",
    "later_slice_authority": "supervisor_fail_closed"
  },
  "slices": {
    "delivery-control": [
      {
        "decision_id": "DEC-POLICY-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Use official Custom Workflow/Template/Extension surfaces, keep feature work Core-zero and reversible, and de-fork only after equivalence proof.",
        "alternatives": [
          "Continue adding Guru behavior to the Trellis SDK fork.",
          "Remove the fork before official Custom equivalence is proven."
        ],
        "impact": "Prevents new SDK coupling while preserving a verified rollback and later template cutover path for every task type.",
        "irreversible": false,
        "invariant_ids": [
          "INV-POLICY-002",
          "INV-POLICY-004",
          "INV-START-004"
        ],
        "required": true,
        "resolution": {
          "choice": "Custom-first, feature-phase Core-zero, reversible Extension, de-fork later.",
          "evidence": "User accepted the architecture baseline on 2026-07-14; PRD Confirmed Decisions 1-5 preserve it."
        },
        "source_refs": [
          {
            "artifact_key": "design:chapters/delivery-policy.md",
            "anchor": "GURU-DECISION:DEC-POLICY-001"
          }
        ]
      },
      {
        "decision_id": "DEC-POLICY-002",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Promote high and unknown-high-signal work to Full before building a writable envelope.",
        "alternatives": [
          "Honor a Lite/Micro preference despite high-risk evidence.",
          "Start low and add Full gates after implementation begins."
        ],
        "impact": "Ensures critical scope, risk and confirmation gaps are exposed before code instead of causing late rework.",
        "irreversible": false,
        "invariant_ids": [
          "INV-POLICY-001",
          "INV-POLICY-003",
          "INV-POLICY-004"
        ],
        "required": true,
        "resolution": {
          "choice": "No High/unknown-high downgrade to Lite or Micro.",
          "evidence": "Confirmed PRD R1/R3 and delivery-policy route promotion contract."
        },
        "source_refs": [
          {
            "artifact_key": "design:chapters/delivery-policy.md",
            "anchor": "GURU-DECISION:DEC-POLICY-002"
          }
        ]
      },
      {
        "decision_id": "DEC-START-001",
        "severity": "high",
        "status": "resolved",
        "recommendation": "Fail closed when unresolved critical/high decisions lack platform-trusted confirmation identity provenance.",
        "alternatives": [
          "Trust agent-writable task JSON as human authorization.",
          "Treat a quoted user message as a platform-signed attestation."
        ],
        "impact": "Prevents locally self-consistent but untrusted evidence from authorizing high-risk implementation.",
        "irreversible": false,
        "invariant_ids": [
          "INV-START-001",
          "INV-START-002"
        ],
        "required": true,
        "resolution": {
          "choice": "Use unavailable_fail_closed until an external trusted identity adapter exists.",
          "evidence": "Confirmed gate capability truth and StartGuard hard-precondition design."
        },
        "source_refs": [
          {
            "artifact_key": "design:chapters/start-guard.md",
            "anchor": "GURU-DECISION:DEC-START-001"
          }
        ]
      },
      {
        "decision_id": "DEC-START-002",
        "severity": "critical",
        "status": "resolved",
        "recommendation": "Limit bootstrap to this task and delivery-control slice, burn it once after live proof, reject all reuse, and keep direct-official bypass advisory.",
        "alternatives": [
          "Generalize bootstrap as a reusable start path.",
          "Claim the after_start hook prevents direct official bypass."
        ],
        "impact": "Contains the unavoidable self-hosting exception without turning it into a permanent authorization bypass.",
        "irreversible": true,
        "invariant_ids": [
          "INV-START-003",
          "INV-START-005"
        ],
        "required": true,
        "resolution": {
          "choice": "One task, one selected slice, one permanent burn; direct official start remains advisory.",
          "evidence": "Confirmed Detail bootstrap protocol and preserved four-event retry history."
        },
        "source_refs": [
          {
            "artifact_key": "design:chapters/start-guard.md",
            "anchor": "GURU-DECISION:DEC-START-002"
          }
        ]
      }
    ]
  }
}
```
<!-- GURU:RISK_DECISION_INVENTORY:END -->

- [ ] 让 intake/contract snapshot 解析 all-intent route policy 和 budgets。
- [ ] 更新四平台 workflow：route-specific artifacts、TTFC、确认上限、scope re-triage、review-only/read-only、research/debug stop rules。
- [ ] Codex 默认 inline；channel/sub-agent 只有在独立工作净收益明确时启用，并受 max workers/idle timeout 限制。
- [ ] 实现 Core-free `guru_task.py start` wrapper、platform capability report、supported hook guard 和 official after_start compensation。
- [ ] 首先关闭本任务一次性 bootstrap：实现/验证 v2 risk packet、trusted attestation、durable StartAttempt 和 burn-once audit；之后任何 start 都必须走 wrapper。
- [ ] 删除 overlay 对 fork-only `run_blocking_task_hooks` 的安装硬依赖；若存在仅作为 defense-in-depth。
- [ ] 覆盖 route matrix、high cannot downgrade、direct bypass/compensation、confirmation batch tests。

**Rollback**：wrapper 可退回现有 check-start + task.py start 文案；不得回退到静默假硬 Gate。

## Wave 2A — Semantic digest and independent review

**设计承接**：UNIT-semantic-digest、UNIT-review-identity。

**执行 packet**：`slice-packets/semantic-review.json`（运行时必须 `--slice semantic-review`）。

- [ ] 为 requirements/overview/detail/implement 定义 versioned dependency digest 和逐 artifact/section invalidation matrix。
- [ ] 实现 fence-aware Lite section state machine 和 Full manifest artifact selector；fenced code 内的 heading-like 行不得成为边界，缺失/重复 unfenced anchor 必须 fail closed。
- [ ] 将 mutable execution evidence 完全排除在 planning digest 外。
- [ ] 实现 `guru_review_cutover.py` + `test_review_cutover.py`：V1 records 只读冻结，CAS 激活唯一 V2 authority，并要求 predecessor/self snapshot 在 V2 managed adapter 下重新 review。
- [ ] 扩展 review records 的 platform-trusted reviewer/worker/thread/context identity、duration、repair ordinal、finding fingerprint 和 resolved/reopened 状态。
- [ ] review JSONL 使用 task/gate lock、framed hash chain、flush/fsync；torn tail 显式 recover，corrupt middle fail closed。
- [ ] 按 route 应用 0/1/2 review policy；相同 trusted reviewer 或相同 trusted context 即使更换 run/worker/thread 也不得伪造独立性。
- [ ] 实现 repeated-finding/no-delta STALLED。
- [ ] 覆盖 detail-only/overview-upstream/cross-gate matrix/format-noise/v1 read-only migration audit/identity spoof/concurrent append/tamper/stagnation tests。

**Rollback**：digest v1 records 保留只读兼容；v2 未完成时不覆盖或迁移历史 evidence。

## Wave 3 — Bounded Supervisor, context, and compounding

**设计承接**：UNIT-bounded-supervisor、UNIT-context-reuse。

**执行 packet**：`slice-packets/bounded-context.json`（运行时必须 `--slice bounded-context`）。

- [ ] 为 supervisor 引入显式终态、fake clock、route deadlines、repair/worker/idle/no-progress budgets。
- [ ] 定义 semantic progress detector；wait/poll/log 不计进展。
- [ ] 将 delivery events 写 task-local append-only evidence，禁止修改 confirmed planning artifacts。
- [ ] 实现 phase context manifest 的 depth/file/single-file/total-byte/type budget、repo-relative path fence、delta loading 和 stale evidence rejection。
- [ ] 拒绝 absolute/`file:`/`..`/symlink escape/non-regular/binary/ancestor identity race；所有 worker context 入口必须委托同一 planner。
- [ ] 按 packet `depends_on` 做稳定拓扑排序，cycle/missing dependency fail closed；目录顺序不得启动 worker。
- [ ] 接入 task-family fingerprint + bounded `trellis mem` recall；无命中时零历史扫描。
- [ ] 输出 cost/outcome summary，并为稳定规则生成 spec promotion candidate。
- [ ] 覆盖 timeout/idle/cancel/scope expansion/no-progress/second-run cost tests。

**Rollback**：保留现有 worker command compatibility；新 supervisor 终态不可被自动重启。

## Wave 4 — Design sync and end-to-end replay

**设计承接**：UNIT-design-sync、UNIT-replay-benchmark。

**执行 packet**：`slice-packets/design-sync-replay.json`（运行时必须 `--slice design-sync-replay`）。

- [ ] 实现 contract-impact/no-doc-impact 分类和 `REQ/BHV -> design -> code -> test` 验证。
- [ ] 创建唯一 project-current SSOT `guru-template/overlay/docs/delivery-control-plane.md`，引用 machine policy/manifest；四平台只保留投影/链接。
- [ ] 只有 module/symbol/test file 真存在、exact command 对 current digest 通过时 trace 才能从 pending 变 covered。
- [ ] 将两个失控会话固化为最小 deterministic replay fixtures。
- [ ] 为 Inline/Micro/Lite/Full/Review/Research/Repeated Debug 建代表 benchmark。
- [ ] 采集 TTFC、context/token proxy、confirm batches、repair rounds、Gate invalidation 和 business diff。
- [ ] 证明 Lite 无 Overview/Detail ping-pong、Full 风险前置、同类任务第二次成本 <=70%、Gate-caused rework <10%。
- [ ] 验证 apply/verify/unapply 与 native Trellis baseline。
- [ ] `release_checks` 只在最终 release gate 运行；packet loader、slice semantic review 和局部 deterministic checks 不得自动触发 live-provider replay。最终 live suite 上限固定 `--max-live-runs 30`，必须独立归档 provider usage、TTFC/terminal/token/context/read-cache 和 Gate rework attribution。
- [ ] 新增 `guru_metrics_adapter.py`、`gate-rework-attribution.json` 与 replay fixtures，三类 Gate rework 指标分别证明 `<10%`，不得用总平均掩盖返工。

**Rollback**：benchmark 失败阻止发布；不得以单元测试通过降级放行。

## Wave 4 finalization — Documentation, migration readiness, and final gates

- [ ] 更新 `guru-template/overlay/README.md`、`trellis-local/SKILL.md` 和四平台 spec/workflow，保持规则正文唯一。
- [ ] 确认 `guru_official_install.py`、`https_git_fixture.py` 和 `test_https_git_fixture.py` 覆盖 official `0.6.7` HTTPS smart-Git 安装路径，blank/fallback 行为 fail-closed，不接受 `file://` 或 checkout path 作为 release 等价证明。
- [ ] 生成现存 SDK Guru coupling inventory 和可独立执行的 de-fork follow-up，不在本阶段删除 Core 代码。
- [ ] 运行 v2 source/manifest/installed closure、official no-fallback E2E、installer/Gate/benchmark、Core-zero diff 和 `git diff --check`。
- [ ] 运行 legacy `sync:guru:check` 仅作 transition audit；其已解释的 v1/v2 divergence 不得迫使修改 Core，也不得成为 v2 runtime fallback。
- [ ] 运行 normalized bundled-v1 transition audit；`KNOWN_DEBT_UNCHANGED|KNOWN_DEBT_REDUCED` 只能对 Custom-v2 非阻断且永远非绿色，任何 inventory/fingerprint/skip/owner-boundary drift 阻塞，fork SDK/npm 始终要求 legacy clean + aligned。
- [ ] 运行 `gitnexus detect-changes --scope compare --base-ref main` 或等价 repo-pinned command，确认无意外流程影响。
- [ ] 运行独立 implementation/check review，修复 finding 后重新执行受影响检查。
- [ ] 最后重读 `guru_gate.py status`、contract scope 和 dirty-worktree exclusions。

## Validation commands

具体命令在实现前按现有脚本入口校正。Mandatory Custom-v2 release-green 集合：

```bash
bash guru-template/overlay/tests/apply_test.sh
bash guru-template/overlay/verify/tests/run_tests.sh
python3 -m py_compile guru-template/overlay/verify/*.py
test -z "$(git status --porcelain=v1 --untracked-files=all -- packages/cli/src packages/core)"
git diff --check
```

Legacy transition audits are mandatory to execute but are not Custom-v2 mandatory-green authorities:

```bash
python3 guru-template/overlay/verify/guru_design_sync.py verify-legacy-transition --baseline guru-template/overlay/verify/baselines/legacy-bundled-v1.json
pnpm --filter @devsc/trellis sync:guru:check
```

The verifier captures the raw Vitest/mirror commands itself and emits separate suite, mirror, Custom-v2 and SDK release-domain verdicts. `KNOWN_DEBT_*` must remain `legacy_status=known_debt`, `custom_v2_release_effect=non_blocking`, `sdk_release_effect=blocking`; `REGRESSION|INVALID|UNEXPLAINED_DIVERGENCE|LEGACY_BOUNDARY_CHANGED` blocks finalization without expanding this task into Core repair.

新增 Extension/benchmark 测试必须能够独立运行，不得要求安装 fork npm 包或修改用户全局配置。

## Review and confirmation gates

1. requirements 结构 Gate 已通过；历史 confirmation 已保留，但最终 digest 仍需与 Overview/Detail 一次性批量 review，并由用户本人一次 reconfirm。
2. Overview 当前 digest 完成所需 clean review 后进入 Detail。
3. Detail 必须包含 deletion audit、当前 digest clean review 和用户本人 strict TTY confirmation。
4. V1→V2 review cutover 顺序固定：先冻结 delivery-control predecessor snapshot 与 semantic-review self snapshot，使用现行 V1 adapter 产生 legacy audit-only review，再执行 read-only `plan` 与 CAS `activate`，随后只允许 Extension-managed V2 provider runner 对同一 snapshot 重新 review；V2 两条 current clean 之前不得开放下游 slice，也不得把 V1 clean 和 V2 clean 混合计数。
5. Supervisor cutover 顺序固定：root direct dispatch 只覆盖 audited bootstrap 期间的 eligible packets；`delivery-control` burn 后，`marketplace-catalog`、`semantic-review`、`extension-manager`、`bounded-context` 仍按 predecessor evidence 显式选择和 review；只有 `bounded-context` 交付并证明 V2 Supervisor 的 dependency graph、clean-reviewed predecessor snapshot 与 provider runner capability 后，`design-sync-replay` 才能由新 Supervisor 调度。
6. 常规路径只有显式 slice、current `RiskDecisionPacketV1`、trusted `ConfirmationAttestationV1`、candidate `check-start` 与 `guru_task.py::start_with_guard` 全 current 才能进入实现。本任务的一次性 bootstrap 已形成四个不可删除事件：`prepared -> consumed(failed_compensated) -> retry_prepared -> retry_consumed(verified)`；verified-consumed source 由 immutable archive 固定，当前 hardened verifier 只负责 status/burn，任何再次 `run` 都非法。`burned` 仍未写入，只有最终三 Gate batch review/reconfirm、current risk/envelope/inventory、required clean implementation review、确定性检查、隔离 guarded-start probe 和 post-probe final CAS 全部通过后才能追加。该历史协议仍是 audited migration，不消除 direct-official bypass，禁止复用/泛化。
7. 每个实现 slice 必须通过局部 test + implementation review；最终通过 full benchmark 和 check-commit。

## 阻塞与偏差

- Gate、review、GitNexus 或平台能力不可用时，记录首个 blocker、已完成证据与一个恢复命令；不得伪造通过或自动扩大 scope。
- 实际实现若偏离 UNIT 合同、allowed paths、风险等级或 slice 顺序，立即停止当前 slice，更新受影响 planning artifact 并重新进入对应确认/review 边界。
- 任一 slice 达到预算或连续无 semantic progress 时按 UNIT-bounded-supervisor 的终态合同收口，不自动续开同一计划。

## Forbidden actions

- 不修改或回退用户已有 `AGENTS.md`、`CLAUDE.md`、dirty `marketplace` submodule。
- 不新增 Trellis Core/SDK Guru 功能，不用本任务优化目标绕过现有 Gate。
- 不伪造 TTY 用户确认、reviewer identity、token 或 benchmark evidence。
- 不提交、推送、归档，除非用户在后续明确要求并且所有 Gate 通过。
