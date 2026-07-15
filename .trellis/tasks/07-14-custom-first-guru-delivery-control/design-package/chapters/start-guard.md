# Core-free Start Guard Detailed Design

> `doc_type=usecase` | `l2_status=v1`
> `chapter_status=ready_for_review_after_migration_exception`
> Overview owner: design-main §4 UNIT-start-guard | TECH-005, TECH-006

### UNIT-start-guard

<!-- GURU-DECISION:DEC-START-001 -->
Until a platform-trusted human identity provenance adapter exists, any unresolved required critical/high decision fails closed. Agent-writable confirmation JSON and user-quote strings are audit context, not start authority.

## 1. 单元职责与 official 事实基线

承接 BHV-002、BHV-003。在不修改 Trellis Core 的前提下，用 `guru_task.py start` guarded wrapper 把 START_READY、current risk packet、trusted confirmation attestation、task status、session-scoped active-task pointer 与 artifact digests 绑定成 start lock + CAS 前置，并通过 durable start-attempt 给 `after_start` 提供可验证 compensation pre-state。

Official Trellis `0.6.7` 的 `task.py start` **不创建、切换或保存 supervisor run**：有 session identity 时先写 active-task pointer，再将 `planning -> in_progress`，然后运行 `after_start`；无 session identity 时不写 pointer，但仍将 status 改为 `in_progress`、运行 `after_start`并返回 `0`。Official `after_start` 失败只输出 warning，不改变 official start 的成功返回码。

因此：StartGuard 只拥有 official lifecycle 的 task status/pointer/attempt CAS；UNIT-bounded-supervisor 唯一拥有 run id、previous/current run、run lock、worker lease 和 terminal state。Guard success 是 Supervisor 创建 run 的前置，不是 run creation 本身。

正向依赖：GuruGate、ConfirmationAttestor、OfficialTaskAdapter、ActiveTaskPointerStore、StartAttemptStore、StartLock。反向禁止：不得由 `after_start`、worker prompt、run id 或用户 quote 字符串独自授予 START_READY；不得让 StartGuard 写 Supervisor run state。

## 2. 行为定义与接口

```python
@dataclass(frozen=True)
class StartRequest:
    task_dir: Path
    selected_slice_id: str
    expected_task_status: Literal["planning"]
    expected_context_key: str | None
    expected_active_task: str | None
    expected_gate_digest: str
    expected_risk_packet_digest: str
    expected_attestation_digest: str

@dataclass(frozen=True)
class OfficialLifecycleSnapshot:
    task_status: str
    context_key: str | None
    active_task_pointer: str | None
    gate_digest: str
    risk_packet_digest: str
    attestation_digest: str

@dataclass(frozen=True)
class StartAttempt:
    attempt_id: str
    task_id: str
    wrapper_pid_identity: str
    pre_snapshot: OfficialLifecycleSnapshot
    expected_post_status: Literal["in_progress"]
    expected_post_pointer: str | None
    state: Literal["prepared", "official_returned", "compensated", "verified", "manual_recovery_required"]

def validate_confirmation_attestation(attestation: "ConfirmationAttestationV1", expected: "ConfirmationExpectation") -> "AttestationVerdict": ...
def start_with_guard(request: StartRequest, lifecycle: "OfficialTaskAdapter") -> "StartResult": ...
def compensate_after_start(attempt_id: str, observed: OfficialLifecycleSnapshot) -> "CompensationResult": ...
```

### 2.1 START_READY hard preconditions

1. task is planning and matches explicit task path;
2. hook `TASK_JSON_PATH`, when present, resolves to the same task;
3. requirements confirmation current;
4. overview/detail required reviews current and detail deletion audit present;
5. detail confirmation current;
6. high/full-chain has one explicitly selected valid slice packet;
7. packet scope/invariants/digest current;
8. required ConfirmationAttestation exact-match current;
9. Supervisor reports no live/cleanup-required run for task/slice;
10. selected slice exists and dependencies are satisfied.

Supervisor run state is a read-only precondition query here. Its generation/run lock remains Supervisor-owned and is rechecked by `SupervisorStateMachine.start` before run creation.

## 3. 核心数据结构与 Capability 语义

| Entry/path | Capability | What is guaranteed | What is not guaranteed |
| --- | --- | --- | --- |
| `guru_task.py start` wrapper | `enforced`, scope=`guarded_entry` | no official start call before current Gate/packet/attestation + post-lock CAS | cannot prevent a user invoking official script directly |
| trusted platform blocking hook | `enforced`, scope=`platform_entry` | only that platform/tool entry is blocked | cross-platform/direct shell bypass |
| wrapper-started `after_start` with durable attempt id | `compensated` | exact status/pointer surfaces can be CAS-restored; wrapper returns non-zero | worker side effects cannot be made atomic after official start |
| direct official start without attempt id | `advisory` | violation is detected/reported; commit/CI remains hard boundary | previous pointer/status transition cannot be proven or safely restored |
| unsupported/missing hook | `unavailable` for that hook | no false enforcement claim | no automatic protection |

Project-level capability report must include `entry_scope` and bypass limits；不得把 `guarded_entry` enforced 宣称为“所有 official start 原子阻断”。`after_start` 固定最多 compensated，direct official start without pre-state 只能 advisory。

### 3.1 本任务一次性 bootstrap/migration start

<!-- GURU-DECISION:DEC-START-002 -->
The bootstrap exception is permanently limited to this task and the selected `delivery-control` slice. Burning it is irreversible, reuse is forbidden, and direct official start remains advisory rather than hard-enforced.

本任务曾存在不可循环自举约束：`guru_task.py`、`RiskDecisionPacketV1` writer 和 `ConfirmationAttestationV1` adapter 当时都是 `delivery-control` 的待实现产物，不能把“先使用已验证的新 wrapper/attestation”设为创建它们的前置。仅对 task `07-14-custom-first-guru-delivery-control`、仅对进入 `delivery-control` 的一次 start，使用了 audited migration path。该 path 已到达 `retry_consumed(verified)`，现在禁止再次 `run`；当前 candidate wrapper/risk/inventory 实现必须通过独立验证后才能永久 burn exception。

唯一 mutable evidence 是 task-local `bootstrap-exception.jsonl`，不复用 context manifest `implement.jsonl`。正常事件 hash-chain 只能按 `prepared -> consumed -> burned` 出现一次；若 `consumed.outcome=failed_compensated` 且 task/session preimage 全部 `restored_exact_preimage|restored_absent|not_applicable`，允许保留失败事件并追加一次 `retry_prepared -> retry_consumed -> burned`。任意缺失、重复、乱序、digest mismatch、corrupt tail、manual recovery 或非 exact bootstrap dirty scope 都阻塞，不自动修复：

| Event | Durable write | Required binding |
| --- | --- | --- |
| `prepared` | create final file with `O_CREAT|O_EXCL`, write one canonical framed JSON line, flush/fsync file, fsync parent | schema/event id, task id, reason, selected `delivery-control`, requirements/overview/detail digests, `gate-contract.json` sha256, packet sha256, canonical requirements/detail confirmation-record digests, canonical current overview/detail review-runs digest including deletion audit, actor, strict-TTY authorization observation, exact commands, hook capability, pre-task snapshot, `previous_event_sha256=null` |
| `consumed` | acquire exclusive companion lock, verify full chain and prepared bindings, append canonical line, flush/fsync, release and fsync parent | prepared line sha256, official command exit, post status/pointer/task snapshot, `check-implementation` result, exact `delivery-control --dry-run` result, previous event sha256 |
| `retry_prepared` / `retry_consumed` | same append protocol, only after clean `failed_compensated` | previous failed event sha256, new reviewed source sha256, same task/slice/current Gate bindings, exact bootstrap dirty-scope exception for source/test/evidence and blocked delivery-control implementation-review evidence only |
| `burned` | same exclusive append protocol | immutable historical verified-consumed source, current `in_progress` lifecycle plus strict Detail/review evidence, candidate risk/envelope/inventory binding, exact Codex-only migration review authorization, one pre-launch target-only index digest equal to the review record/post-worker index/current worktree/final CAS, deterministic-result digest carried by the invocation contract, canonical final-worker-verdict equality with the review record, official Codex session and raw control-plane lineage capture, isolated guarded-start capability probe, post-probe final CAS, previous event sha256 |

The historical one-shot executable is preserved at `bootstrap/archive/bootstrap_start.e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3.py`, SHA-256 `e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3`; it is evidence and cannot be invoked as a current entry. Its completed `run` transaction acquired the companion exclusive lock, validated exact task/slice/status, read-only `slice-plan`, `check-start`, Gate digests, contract/packet hashes and canonical confirmation/review records, then wrote the preserved four-event chain. The current `bootstrap/bootstrap_start.py`, SHA-256 `88b8d467d167d617e0ee525c9b78f7f0ec4ee602e45976e0263b028a56d88f99`, is a hardened status/burn verifier only. It requires the immutable historical bytes whenever the verified-consumed source differs from its own source and rejects direct execution of the archive as a current verifier bypass.

`run` invokes the actual checkout-local `.trellis/scripts/task.py`; the separately recorded official npm `0.6.7` integrity/tarball digest is comparison provenance only and is never execution authority. After official return, `run` verifies the exact lifecycle postimage and executes `check-implementation` plus the exact selected-slice dry-run before appending `consumed`. Any failure after lifecycle mutation performs digest-CAS restoration of the exact task/session preimages with atomic replace and parent fsync; a changed observed surface is preserved and recorded as `manual_recovery_required`. The companion lock cannot make uncooperative official writers atomic, so the utility does not claim to close direct-official bypass or kernel-level compare-and-swap.

The current read-only verification order is:

```bash
HISTORICAL_BOOTSTRAP="$TASK/bootstrap/archive/bootstrap_start.e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3.py"
HISTORICAL_BOOTSTRAP_SHA256=e6dbcc3b6c341902e4024af2690ca39d41f6112e12caaca31b509dc311d4c0e3
CURRENT_BOOTSTRAP="$TASK/bootstrap/bootstrap_start.py"
CURRENT_BOOTSTRAP_SHA256=88b8d467d167d617e0ee525c9b78f7f0ec4ee602e45976e0263b028a56d88f99
test "$(shasum -a 256 "$HISTORICAL_BOOTSTRAP" | awk '{print $1}')" = "$HISTORICAL_BOOTSTRAP_SHA256"
test "$(shasum -a 256 "$CURRENT_BOOTSTRAP" | awk '{print $1}')" = "$CURRENT_BOOTSTRAP_SHA256"
python3 "$CURRENT_BOOTSTRAP" status "$TASK" --slice delivery-control --source-sha256 "$CURRENT_BOOTSTRAP_SHA256"
# Never run bootstrap again; status must report four events and retry_consumed(verified).
```

Checkout-local `.trellis/scripts/guru/guru_gate.py` remains historical installed authority and validates requirements/overview/detail structure plus current confirmation/review/deletion audit. Candidate `guru-template/overlay/verify/guru_gate.py` additionally validates the v2 Full/high decision inventory before Detail review/confirm/start. Burn requires both the live lifecycle evidence and candidate `guru_task.py::_artifact_binding`, so neither old local Gate nor rehashed caller JSON can authorize stale risk/envelope/inventory state. Direct official bypass remains advisory; guarded wrapper/StartAttempt/CAS enforcement applies only through the wrapper entry.

`status` validates canonical framing, every payload/link digest, exact task/slice, the current verifier SHA and the immutable archived verified-consumed source. Torn tail, corrupt middle, archive missing/drift, current verifier drift, manual recovery and reuse fail closed. `burn --evidence <burn-evidence.json>` accepts only exact schema-v3 identity/selection fields plus `bootstrap_review_authorization={kind:codex_same_provider_user_directive_v1,user_directive:关闭调用claude,provider:codex,review_mode:check_only,independence_claim:none,trusted_review_envelope_eligible:false}`. It derives every hash itself and requires lifecycle status to remain `in_progress`, current strict Detail plus double-clean/deletion audit, candidate risk/envelope/inventory binding, and one exact `codex/codex/codex` review created by `guru-template/overlay/verify/guru_supervise.py implementation-review --same-provider --user-quote "关闭调用claude"`; the invocation contract binds that Custom supervisor path and source digest. The Custom supervisor captures the target digest before launch, writes that digest and a canonical invocation contract into the worker prompt, reruns the digest after deterministic checks and after the worker, and records the same digest. Burn then requires the temporary-index digest and current worktree digest to equal that pre-launch/record value. It parses the final captured worker message through the same `parse_verdict_block` and `normalize_review_record` path used by the supervisor and requires canonical equality with the selected JSONL record; a findings, malformed, unrelated or synthetic-clean mismatch cannot burn. It then re-reads source, Detail, bindings, reviewed target, Codex session and control-plane capture at the last possible point before append; any probe-window drift rejects burn. Duplicate run/burn is rejected. The record remains audit evidence outside planning digests and may seed `test_single_task_bootstrap_exception_burns_after_wrapper`; it never becomes a reusable route policy.

This Codex-only migration review is an explicit exception to bootstrap burn evidence, not to `TrustedReviewEnvelopeV1`. The verifier rejects `TRELLIS_CHANNEL_ROOT` redirection and accepts only the default official channel/session stores, the exact channel and worker names derived from the review run id, one channel-wide spawned Codex `check` worker, one prompt/turn/terminal sequence, exact task artifacts, one platform-issued thread/session id, exact repo cwd, Trellis-channel session metadata, captured model/provider/CLI metadata, and no file-change/error/killed event. The prompt contract binds the run id, target, pre-launch digest, packet target-path digest, deterministic-result digest, provider tuple, override source and exact user directive. Raw worker log, Codex session, channel events, final message, parsed verdict and normalized record are separately hashed and final-CAS re-read. Those fields prove audit lineage and causal consistency only. They do not provide `reviewer_id`, `context_id` or platform attestation, claim no provider/reviewer/context independence, and are permanently ineligible for V2 trusted-review counting. Local JSONL/hash evidence also does not claim resistance to an operator who can maliciously rewrite the repo, channel store and Codex store together. Changing a run, worker, channel or thread id never upgrades this exception into independent evidence.

## 4. Error enum

| Error | Trigger | Closure |
| --- | --- | --- |
| `StartNotReady` | any Gate/review/confirm prerequisite missing | no official start |
| `RiskPacketStale` | packet/task/scope/artifact mismatch | re-build packet |
| `ConfirmationMissing` / `ConfirmationStale` | trusted attestation absent/exact key mismatch | request only new decisions |
| `LifecycleCASMismatch` | status/pointer/context/digest changed after validation | release start lock, re-read |
| `StartLockConflict` | another live guarded start attempt owns task | no official start |
| `SupervisorRunConflict` | live/cleanup-required run exists | no official start; Supervisor remains owner |
| `AttemptDurabilityFailed` | attempt temp/file/parent fsync or publish failed | no official start |
| `OfficialStartFailed` | official lifecycle call non-zero or postcondition invalid | compensate exact observed wrapper mutations or recovery_required |
| `CompensationConflict` | observed status/pointer no longer equals expected official post-state | preserve current; manual_recovery_required |
| `DirectBypassDetected` | after_start lacks valid wrapper attempt id | append violation; no unsafe restore |
| `CapabilityInsufficient` | policy requires a scope that platform cannot enforce | block before claiming support |

## 5. 逐行为设计：Guarded wrapper 与 TOCTOU closure

```mermaid
sequenceDiagram
    participant U as GuruTaskCLI
    participant S as StartGuard
    participant G as GuruGate
    participant L as StartLock
    participant A as StartAttemptStore
    participant T as OfficialTask067
    participant H as GuruAfterStart
    participant B as BoundedSupervisor
    U->>S: 1. start(StartRequest)
    S->>G: 2. validate START_READY + supervisor conflict query
    G-->>S: 3. current digests + attestation verdict
    S->>L: 4. acquire per-task start lock
    S->>S: 5. re-read status/context/pointer/digests and CAS snapshot
    alt any mismatch
        S-->>U: 6. LifecycleCASMismatch; no official start
    else current
        S->>A: 7. durable PREPARED attempt + expected post-state
        S->>T: 8. official task.py start with GURU_START_ATTEMPT_ID
        T->>H: 9. non-blocking after_start
        H->>A: 10. validate attempt without reacquiring start lock
        T-->>S: 11. official return code
        S->>S: 12. re-check Gate and exact official postcondition
        alt valid
            S->>A: 13. mark VERIFIED
            S-->>B: 14. guarded start result; Supervisor may create run under its own lock/CAS
        else invalid
            S->>A: 15. CAS compensation or manual recovery state
            S-->>U: 16. non-zero wrapper result
        end
    end
```

Start lock 从 validation 后覆盖最终 CAS、attempt publish、official subprocess 和 postcondition；hook 通过 attempt id 读取同一 pre-state，不重复获取 start lock以免死锁。Attempt 在 official call 前使用 temp fsync + atomic replace + parent fsync；没有 durable attempt 不调用 official start。

有 session identity 时 expected post 是 `status=in_progress + pointer=selected task`；无 session identity时 expected post是 `status=in_progress + pointer unchanged/absent`。Official postcondition不包含 run。

## 6. `after_start` compensation 与 direct bypass

Wrapper path：hook 只接受环境 `GURU_START_ATTEMPT_ID` 指向当前 task、live wrapper identity、PREPARED attempt 和 exact pre/post digests。Gate 在 official mutation 后失效时，按 CAS 将 `in_progress -> planning`，并仅在当前 pointer仍为 selected task时恢复 previous pointer/删除 wrapper-created pointer；追加 violation 并把 attempt 标 `compensated`。Wrapper 即使观察到 official return `0`，也必须读取 attempt/hook outcome并返回 non-zero。

Direct official path：没有可信 pre-snapshot，hook不知道 task 原先是否已 `in_progress`、也不知道 previous pointer，禁止猜测回滚。它只写 append-only violation（若证据目录可写）、输出精确 recovery/status信息，capability=`advisory`。Commit/CI/check-implementation 是最后 hard boundary。不得用 status-only best effort 冒充完整 compensation。

Compensation CAS conflict 时保留现场，记录 expected/observed snapshots和 `manual_recovery_required`。StartAttempt/violation 属 execution evidence，不进入 planning digest。

### 6.1 失败收口

Guarded path 在 official call 前失败必须保持 lifecycle 不变；call 后失败按 durable attempt 做 exact CAS compensation，否则保留现场并标 `manual_recovery_required`。Direct bypass 没有可信 pre-state，只记录 advisory violation 和恢复命令，绝不猜测写回。

## 7. 状态 / 边界：owner boundary

Official lifecycle 合法 transition只有 wrapper观察的 `planning -> in_progress` 和 optional session pointer update。StartGuard 不定义 run lifecycle。Guarded start成功后，Supervisor用独立 run generation/lock创建 `planned -> running`；live/terminal/previous run 语义全在 UNIT-bounded-supervisor。

Start lock记录 task、attempt、host/boot、pid start identity和expected lifecycle digest。Stale lock恢复需证明 wrapper process identity不存活并读取attempt terminal/recovery state，不按mtime清锁。Attempt terminal update幂等；不同 terminal digest冲突进入 manual recovery。

## 8. 数据合同

- StartRequest 同时绑定 explicit task_dir 和 injected `TASK_JSON_PATH`（若存在）；不一致 fail closed。
- Risk packet/attestation只读校验；StartGuard不重写它们。
- Attempt保存 status/pointer/context和digest，不保存用户 secret/quote正文。
- Direct hook evidence追加写，不修改 confirmed planning artifacts。
- `guru_task.py`通过配置/manifest定位 exact official `.trellis/scripts/task.py`；不得导入/调用 fork-only symbol。

## 9. 测试映射

| Path | Test | Expected result |
| --- | --- | --- |
| guarded current preconditions | `test_guarded_start_calls_official_once` | status/pointer expected; no run created by adapter |
| missing/stale risk/confirmation | parameterized precondition tests | zero official call; exact error |
| TOCTOU status/pointer/context/digest | `test_snapshot_changes_between_check_and_start` | CAS mismatch; zero official mutation |
| live Supervisor run | `test_supervisor_run_conflict_is_read_only` | no official start; no StartGuard run write |
| attempt durability | `test_attempt_fsync_failure_prevents_official_start` | zero official call |
| wrapper hook compensation | `test_wrapper_attempt_restores_status_and_pointer` | exact official surfaces restored; wrapper non-zero |
| no-session official behavior | `test_no_session_still_changes_status_and_runs_hook` | pointer unchanged; status compensated from durable pre-state |
| direct bypass | `test_direct_official_start_is_advisory_only` | violation; no guessed pointer/status restore; official may return 0 |
| hook failure return semantics | `test_official_hook_failure_does_not_change_official_zero` | official 0, wrapper independently returns non-zero when invalid |
| lock/reentry | `test_hook_does_not_reacquire_wrapper_start_lock` | no deadlock; exact attempt consumed |
| capability wording | `test_capability_scope_never_overclaims` | after_start not enforced; direct path advisory |
| executable bootstrap utility | `python3 -m unittest discover -s .trellis/tasks/07-14-custom-first-guru-delivery-control/bootstrap/tests -p 'test_bootstrap_start.py'` | temp-only fixture covers exact task/slice/source, chain integrity, official/postcheck compensation, all `current_run` preimages, CAS conflict, reuse and burn |
| exact Codex migration authorization | `test_bootstrap_review_authorization_manifest_is_exact`; `test_same_provider_record_must_match_the_exact_user_directive` | only schema-v3 `关闭调用claude` + `codex/codex/codex` + official same-provider audit is eligible; no independence or V2 claim |
| Codex control-plane lineage | `test_codex_control_plane_capture_fails_closed`; `test_redirected_channel_store_is_rejected`; `test_control_plane_drift_during_burn_cannot_append_burned` | only the default official channel/session stores, run-derived worker/channel, exact invocation contract, one check-only thread/turn and a final verdict canonically equal to the record pass; findings/malformed/mismatch, extra worker, wrong digest/quote/session metadata, redirected or drifting capture blocks burn |
| bootstrap lifecycle state | `test_burn_requires_live_in_progress_task_state` | stable `planning`/`completed` cannot burn; initial and final state must remain `in_progress` |
| bootstrap migration | `test_single_task_bootstrap_exception_burns_after_wrapper` | exact exclusive/fsynced normal or clean-compensated retry chain is accepted only for this task/current digests/`delivery-control`; corrupt, repeated, manual-recovery or later use is rejected |
| error enum matrix | `test_error_enum_closure_matrix` | every error prevents call or reaches exact compensation/manual boundary |
| existing Gate | `bash guru-template/overlay/verify/tests/run_tests.sh` | check-start/check-implementation regression green |

每个 success path paired with missing confirmation、stale packet、CAS race、pointer conflict、no-session、hook failure、direct bypass和compensation conflict。

## 10. 不得补造清单

- 不得声称 official `task.py start` 创建 current/previous run。
- 不得把 product quote、Agent string 或 run id 当 trusted confirmation。
- 不得在 start lock 后省略 status/pointer/context/digest re-read CAS。
- 不得把 non-blocking `after_start` 称为 hard/enforced/atomic。
- 不得在没有 durable wrapper pre-state 时猜测恢复 status/pointer。
- 不得让 StartGuard写 Supervisor run lock/state。
- 不得把一次性 bootstrap audit exception 泛化为 route policy 或 official 0.6.7 hard enforcement。
- 不得把 Codex thread/channel/run/worker id 或 raw capture digest 描述成 reviewer/context independence 或 `TrustedReviewEnvelopeV1`。

## 11. 不变量矩阵

| invariant_id | rule | owner | positive_case | negative_case | route_if_missing |
| --- | --- | --- | --- | --- | --- |
| INV-START-001 | guarded wrapper must-not call official start unless all START_READY/risk/confirmation preconditions are current | UNIT-start-guard | exact current tuple and one official call | stale attestation reaches official start | block guarded start |
| INV-START-002 | guarded start must-not use pre-lock lifecycle snapshot without post-lock CAS and durable attempt | UNIT-start-guard | status/pointer/context/digests re-read; attempt fsynced | check/use race or official call without attempt | abort and re-read |
| INV-START-003 | wrapper compensation must restore every official surface it can prove, while direct official start must-not guess unknown pre-state | UNIT-start-guard | wrapper status/pointer restored; direct path advisory | status-only rollback or invented previous pointer | manual recovery defect |
| INV-START-004 | official task lifecycle must-not own or fabricate Supervisor run state | UNIT-start-guard | Supervisor creates run only after guarded result | wrapper/after_start writes previous/current run | block start/run integration |
| INV-START-005 | bootstrap exception must remain one exclusive hash-chained task/digest/slice event and burn after wrapper verification | UNIT-start-guard | exact `prepared -> consumed -> burned` binds current Gates/reviews/confirmation/contract/packet/postchecks for this task and `delivery-control` only | missing/corrupt/reused record, invented TTY ref, bypassed postcheck or official-hard claim | block bootstrap/future start |

当前状态保持 `ready_for_review_after_migration_exception`；未产生 method review evidence。
