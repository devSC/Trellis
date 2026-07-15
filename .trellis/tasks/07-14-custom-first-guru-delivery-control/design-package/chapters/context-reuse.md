# Bounded Context And Verified Reuse Detailed Design

> `doc_type=repository-datasource` | `l2_status=v1`
> `chapter_status=ready_for_review_after_migration_exception`
> Overview owner: design-main §4 UNIT-context-reuse | TECH-007

### UNIT-context-reuse

## 1. 单元职责

承接 BHV-004。唯一拥有 phase-specific read fences、task-family query fence、candidate validity、deterministic trimming、planned ContextManifest、managed actual-read ledger 和 reuse cost counters。Live repo/current task 总是优先；memory 只提供候选，不覆盖 repository truth；planned bytes never claim observed reads。

正向依赖：RepoInventory、TaskArtifactReader、SpecIndex、BoundedMemorySearch。反向禁止：不得扫描全 history、读取 fence 外路径、加载完整 conversation 或复用 stale review/verification为 current。

## 2. 行为定义

### 2.1 接口定义

```python
@dataclass(frozen=True)
class ContextFence:
    phase: str
    repo_root: Path
    allowed_roots: tuple[PurePosixPath, ...]
    required_artifact_keys: tuple[str, ...]
    max_files: int
    max_depth: int
    max_single_file_bytes: int
    max_bytes: int
    task_family_query: str | None
    policy_version: str

@dataclass(frozen=True)
class ContextCandidate:
    source: Literal["current_task", "live_repo", "project_spec", "verified_reuse"]
    artifact_key: str
    repo_relative_path: PurePosixPath | None
    content_digest: str
    byte_size: int
    dependency_distance: int
    required: bool

class ContextPlanner(Protocol):
    def build(self, fence: ContextFence, fingerprint: "TaskFamilyFingerprint") -> "ContextManifest": ...
    def validate_reuse(self, candidate: "ReusableSummary", current: "ReuseExpectation") -> "ReuseVerdict": ...
    def observe_read(self, event: "ContextReadEventV1", expected_generation: int) -> "ContextUsageV1": ...

@dataclass(frozen=True)
class ContextReadEventV1:
    event_id: str
    envelope_id: str
    worker_id: str
    phase: str
    source: Literal["current_task", "live_repo", "project_spec", "verified_reuse"]
    artifact_key: str
    repo_relative_path: PurePosixPath | None
    content_digest: str
    delivered_bytes: int
    cache_status: Literal["uncached", "cached", "unknown"]
    sequence: int

@dataclass(frozen=True)
class ContextUsageV1:
    actual_reads_known: bool
    observed_read_events: int | None
    observed_context_bytes: int | None
    observed_unique_bytes: int | None
    duplicate_reads: int | None
    observer: Literal["managed_read_proxy", "host_inline_unknown"]
```

## 3. 核心数据结构

TaskFamilyFingerprint fields: intent, execution_route, platform, affected contract kinds, normalized path families, policy major version, design/digest profile。It excludes user text, timestamps and full conversation。

ContextManifest fields are planning facts only: schema/version, phase/fence digest, selected candidates in deterministic order, excluded candidates with reason, `planned_files/planned_unique_bytes`, reuse ids, repo/task/spec/memory candidate counters and deterministic byte proxy。It contains no `actual_reads`, no observed token claim and no implicit worker access proof。

ContextUsageV1 is execution evidence. ManagedProviderRunner may append a ContextReadEvent only when an enforced read-tool proxy delivered those exact bytes under filesystem isolation；every delivery, including cached/repeated content, increments observed bytes。Duplicate identity is `(phase,source,artifact_key,content_digest)` after the first delivery。With host-inline or any backend lacking both proxy and filesystem isolation, usage is `actual_reads_known=false` and every observed field is `None/unknown`, never `0` and never copied from ContextManifest。

### 3.1 Deterministic trimming order

Sort key ascending: `(required_rank, source_rank, dependency_distance, artifact_key)` where required=0; source order current_task=0, live_repo=1, project_spec=2, verified_reuse=3。Add candidate only if cumulative file/byte limits remain. Required candidate exceeding limit returns `RequiredContextOverBudget`; it is never silently dropped. Same inputs produce byte-identical manifest。

Every external reference must be a normalized repository-relative POSIX path. Absolute paths, `file:` URIs, empty/dot roots, parent traversal, NUL, symlink escape and an ancestor that changes identity between check/use are rejected. Directory enumeration is sorted, does not follow symlinks, stops at `max_depth`, and counts both files and bytes before selecting content. Non-regular files, binary/NUL content, unreadable files and a file larger than `max_single_file_bytes` fail if required and are excluded with a typed reason if optional. A hard runtime fence exists only when a managed backend proves filesystem isolation and forces every read through the ContextPlanner-owned proxy；otherwise the manifest is a plan/advisory boundary and actual reads remain unknown。

### 3.2 错误枚举

| Error | Trigger | Closure |
| --- | --- | --- |
| `FenceInvalid` | path escape, empty required set, non-positive budget | block context build |
| `FenceViolation` | reader attempts path/source outside fence | block and audit exact key |
| `RequiredContextMissing` | required task/spec artifact absent | block phase |
| `RequiredContextOverBudget` | required set alone exceeds budget | return exact overage; shrink scope/increase budget decision |
| `ReuseUnavailable` | memory tool unavailable | local-only degraded, no history scan |
| `ReuseStale` | repo/policy/artifact/version mismatch | exclude candidate |
| `TelemetryUnknown` | provider tokens unavailable | record unknown, never zero; byte count remains diagnostic and ReplayBenchmark comparison blocks |
| `ActualReadsUnknown` | host-inline or missing managed read proxy/filesystem isolation | planned manifest remains valid; hard actual-read/duplicate verdict blocks |
| `HardFenceUnavailable` | envelope requests enforced context budget without both required runner capabilities | block managed launch or explicitly select advisory host-inline before activation |
| `UnplannedContextRead` | managed proxy request is outside manifest/fence or digest differs | deny read, audit exact key, cancel on repeated violation |
| `UnsupportedContextKind` | symlink/device/socket/binary/URI/absolute or non-regular input | reject required input; typed exclusion for optional input |
| `PathIdentityChanged` | ancestor/inode changes between fence check and read | abort read; never retry with wider root |

## 4. 逐行为设计

### 4.1 Context build

```mermaid
sequenceDiagram
    participant P as PhaseRunner
    participant C as ContextPlanner
    participant R as RepoInventory
    participant S as SpecIndex
    participant M as BoundedMemorySearch
    participant W as ManagedReadProxy
    P->>C: 1. build(fence, task-family fingerprint)
    C->>R: 2. read only required task + allowed live paths
    C->>S: 3. resolve only referenced spec indexes
    alt exact family query exists
        C->>M: 4. bounded query(query, max_hits, max_bytes)
        M-->>C: 5. candidates with source/version/digests
    else no family match
        C->>C: 6. zero memory calls
    end
    C->>C: 7. validate candidates and deterministic sort/trim
    C-->>P: 8. planned ContextManifest + excluded reasons
    alt managed + filesystem isolation + read proxy
        P->>W: 9. launch with manifest/fence digest
        W->>C: 10. ContextReadEvent per delivered byte stream
        C-->>P: 11. observed ContextUsage + duplicate counters
    else host-inline or missing capability
        C-->>P: 9. actual_reads=unknown; no hard fence claim
    end
```

阶段切换建立新 fence/manifest，不继承上阶段完整 items。Memory query 必须由 exact fingerprint family 产生，并传 max_hits/max_bytes；无 query 即 zero calls。Candidate validity requires repo identity/base commit family, policy/profile compatibility and referenced evidence digest current。Managed proxy rejects a read not selected in the current phase manifest；host-inline cannot make that enforcement claim。

### 4.2 Cost reuse

Warm/cold comparison使用相同 fixture/environment/fence profile/topology。ContextPlanner emits planned unique bytes/files and, only under managed proxy, observed delivered/unique bytes and duplicates；provider token telemetry remains separate and unknown when unavailable。Second run <=70% rule由 ReplayBenchmark 统计；ContextPlanner不自判 pass，且 planned bytes不能满足 actual-read/token metric。

### 4.3 失败收口

Memory unavailable/stale 降级为 local-only，不扩大历史扫描。Required planned set over-budget 是 blocker with exact items/bytes；optional items按 deterministic order trim。Managed observed bytes/duplicates越界由 Supervisor budget terminal；unplanned read被 proxy拒绝。Fence violation不重试更宽 root，必须由外部确认 scope change。Host actual unknown blocks hard-budget/benchmark verdict rather than becoming zero。

## 5. 状态 / 边界

ContextManifest immutable per `(phase, fence digest, repo snapshot, task artifact digest)`；ContextUsage is append-only execution evidence bound to envelope/worker/manifest digest and excluded from planning digest。ReusableSummary append-only candidate with verification refs/expiry; stable rule promotion只输出 candidate，不自动改 Spec。Sensitive transcript never enters summary。

## 6. 数据合同

- Reader APIs require repo-relative artifact keys; absolute paths仅内部 fence comparison，不写 manifest。
- Exclusion reason enum: over_budget, stale, family_mismatch, duplicate, fence_denied, unsupported_kind。
- Cached tokens still count when telemetry available。
- `unknown` token metric accompanied by bytes proxy; no fabricated estimate presented as actual tokens。
- `planned_unique_bytes` and `observed_context_bytes` are separate namespaces；cached/repeated delivery counts again only in observed bytes and duplicate reads。
- hard path/context enforcement requires managed filesystem isolation + ContextPlanner read proxy；host-inline and legacy channel actual reads are unknown。

## 7. 测试映射

| Path | Command | Expected result |
| --- | --- | --- |
| deterministic trim | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | byte-identical planned order/output |
| fence escape/path kinds/race | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | no outside/non-regular/binary read; identity race aborts |
| depth/file/byte limits | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | exact first overflow and stable manifest |
| required over budget | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | RequiredContextOverBudget |
| no family match/stale reuse | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | zero broad calls; stale candidate excluded |
| phase rebuild | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | no implicit previous items |
| planned versus actual | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | plan fields cannot satisfy actual reads; cached/repeated delivery increments observed bytes/duplicate count |
| managed hard fence | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | only isolated managed proxy enforces; unplanned read denied |
| inline unknown telemetry | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | actual reads/tokens unknown, never zero or planned substitute |
| error enum matrix | `python3 -m unittest discover -s guru-template/overlay/verify/tests -p 'test_context_reuse.py'` | `FenceInvalid`, `FenceViolation`, `RequiredContextMissing`, `RequiredContextOverBudget`, `ReuseUnavailable`, `ReuseStale`, `TelemetryUnknown`, `ActualReadsUnknown`, `HardFenceUnavailable`, `UnplannedContextRead`, `UnsupportedContextKind`, `PathIdentityChanged` reach declared closure |
| warm fixture | ReplayBenchmark command in replay chapter | ContextManifest counters feed <=70% stats |

## 8. 不得补造清单

- 不得在 no-match 时全量扫描 memory/history。
- 不得使用 LLM subjective ranking作为 trimming order。
- 不得静默丢 required context 或扩大 read fence。
- 不得把 stale reuse、memory claim 或 token estimate 当 current repo evidence。
- 不得把 ContextManifest planned bytes/files 写成 actual reads/token facts。
- 不得在 host-inline、legacy channel或缺少 filesystem isolation/read proxy 时宣称 hard context fence。

## 9. 不变量矩阵

| invariant_id | rule | owner | positive_case | negative_case | route_if_missing |
| --- | --- | --- | --- | --- | --- |
| INV-CONTEXT-001 | no family match must-not trigger memory/history scan | UNIT-context-reuse | zero calls | broad recall | local-only mode |
| INV-CONTEXT-002 | deterministic trimming must-not drop required artifacts | UNIT-context-reuse | explicit over-budget | missing task contract hidden | block phase |
| INV-CONTEXT-003 | memory/reuse must-not override live repository truth | UNIT-context-reuse | stale excluded | old summary selected | block reuse candidate |
| INV-CONTEXT-004 | every context input must-not bypass repository-relative path fencing and deterministic depth/file/byte/kind limits | UNIT-context-reuse | one planner enforces all limits and stable order | absolute/URI/traversal/symlink/binary/direct read enters worker context | block phase |
| INV-CONTEXT-005 | planned context manifest bytes must-not be reported as observed actual reads or token telemetry | UNIT-context-reuse | managed read events count delivered bytes while inline stays unknown | plan totals become actual zero/pass evidence | block hard budget/benchmark verdict |
| INV-CONTEXT-006 | hard context fencing must require a managed backend with both filesystem isolation and ContextPlanner-owned read proxy | UNIT-context-reuse | unplanned managed read is denied and audited | host/legacy/unisolated worker is called hard fenced | block launch/claim |

当前状态保持 `ready_for_review_after_migration_exception`；未产生 method review evidence。
