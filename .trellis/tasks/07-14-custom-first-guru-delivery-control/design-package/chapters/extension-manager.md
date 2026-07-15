# Reversible Extension Lifecycle Detailed Design

> `doc_type=usecase` | `l2_status=v1`
> `chapter_status=ready_for_review_after_migration_exception`
> Overview owner: design-main §4 UNIT-extension-manager | TECH-002, TECH-003, TECH-006

### UNIT-extension-manager

## 1. 单元职责

承接 BHV-007。拥有 `plan/apply/adopt/upgrade/status/verify/unapply/recover`、official install wrapper、首写前 durable WAL、Extension-created/replaced/adopted ownership、结构化 config node CAS、atomic InstallState publish、crash recovery 与 rollback。依赖 UNIT-marketplace-catalog 的 typed result；不重新解析 catalog id，不修改 Trellis Core，不删除 official 安装的 project-owned Workflow/Spec。

正向依赖：CatalogResolver、ExtensionManifest、FileSystemAdapter、StructuredConfigAdapter、TransactionJournal、TargetLock。反向禁止：不得调用 DeliveryPolicy/GuruGate 作为文件事务的一部分；`apply.sh` 不得绕过 manager；official Template install 与 Extension-owned mutation 不得伪装成一个可回滚 ownership 域。

## 2. Source/target 文件树与 manifest

### 2.1 最小 source tree

```text
guru-template/overlay/
  extension-manifest.json
  apply.sh                              # compatibility wrapper only
  verify/
    guru_catalog.py
    guru_official_install.py           # raw official staging + postcondition adapter
    guru_overlay.py                    # CLI + ExtensionManager
    guru_install_journal.py            # WAL/lock/path/atomic I/O
    guru_config_patch.py               # structured JSON/YAML node CAS
    tests/
      test_guru_catalog.py
      test_extension_manager.py
      test_https_git_fixture.py
      test_start_guard.py
  hooks/
    guru_task.py
    guru_after_start.py
  tests/
    official_067_e2e.sh
    https_git_fixture.py               # hermetic HTTPS smart Git test server
```

### 2.2 Target runtime tree

```text
.trellis/guru/
  manifest.json
  install-state.json
  transactions/<tx-id>.jsonl
  backups/<tx-id>/<operation-id>.bin
  backups/<tx-id>/<operation-id>.json
  start-attempts/<attempt-id>.json
  start-locks/<task-id>.lock
  violations.jsonl
.trellis/scripts/guru/
  guru_overlay.py
  guru_install_journal.py
  guru_config_patch.py
  guru_official_install.py
  guru_review_runner.py
  guru_review_cutover.py
  guru_task.py
  guru_after_start.py
```

成功 `unapply` 在事务 commit 后删除 manager-owned runtime/state；若 cleanup 中断，下一次 mutating `recover` 完成清理。只读 `status/verify` 报告 cleanup/recovery requirement，不顺便写盘。

### 2.3 `extension-manifest.json` 最小合同

```json
{
  "schema_version": 1,
  "extension": {"id": "guru-overlay", "version": "VERSION"},
  "requires": {"trellis_package": "@mindfoldhq/trellis", "trellis_version": "0.6.7"},
  "catalog": {"index": "../index.json"},
  "platforms": {
    "flutter": {
      "spec_id": "guru-flutter-client",
      "workflow_id": "guru-client",
      "layers": ["flutter", "service", "shared"],
      "skill_ids": [],
      "analyze_command": "flutter analyze"
    }
  },
  "assets": [
    {"id": "overlay-cli", "source": "verify/guru_overlay.py", "target": ".trellis/scripts/guru/guru_overlay.py", "mode": "0755", "owner": "extension_file"}
  ],
  "config_ops": [
    {"id": "after-start", "file": ".trellis/config.yaml", "format": "yaml", "op": "ensure_list_item", "path": ["hooks", "after_start"], "identity": "guru-after-start", "value": "python3 .trellis/scripts/guru/guru_after_start.py"}
  ],
  "assertions": [
    {"id": "official-spec", "owner": "project", "kind": "catalog_tree", "catalog_ref": "$platform.spec_id", "target": ".trellis/spec"},
    {"id": "official-workflow", "owner": "project", "kind": "catalog_file", "catalog_ref": "$platform.workflow_id", "target": ".trellis/workflow.md"}
  ]
}
```

Production manifest 补齐四个平台的 deterministic maps 和实际 assets；禁止 glob 产生不稳定顺序。`assertions` 只验证 official project-owned Template，不进入 removable ownership。

Manifest还必须把 semantic-review slice产出的 `guru_review_runner.py`、`guru_review_cutover.py` 和 provider adapter配置登记为 Extension assets；ExtensionManager只负责按 content digest安装/升级/撤销这些文件，不拥有其 review semantics。Runner capability由 UNIT-review-identity在消费token前判定，installer不得在缺 capability时补造 self-reported identity。

## 3. 行为定义与 CLI

### 3.1 接口

```python
class ExtensionManager(Protocol):
    def plan(self, request: "PlanRequest") -> "ExtensionPlan": ...
    def apply(self, plan: "ExtensionPlan", expected_target_digest: str) -> "InstallState": ...
    def adopt(self, request: "AdoptRequest", expected_target_digest: str) -> "InstallState": ...
    def upgrade(self, request: "UpgradeRequest", expected_state_digest: str) -> "InstallState": ...
    def status(self, target: Path) -> "ExtensionStatus": ...
    def verify(self, target: Path, expected_state_digest: str | None = None) -> "VerifyResult": ...
    def unapply(self, request: "UnapplyRequest", expected_state_digest: str) -> "UnapplyResult": ...
    def recover(self, target: Path, tx_id: str | None = None) -> "RecoveryResult": ...

class TransactionJournal(Protocol):
    def prepare(self, tx: "PreparedTransaction") -> str: ...
    def record_applied(self, tx_id: str, operation_id: str, observed_post_digest: str) -> None: ...
    def record_state_published(self, tx_id: str, install_state_digest: str) -> None: ...
    def commit(self, tx_id: str, install_state_digest: str) -> None: ...
    def recover(self, target: Path, tx_id: str) -> "RecoveryResult": ...
```

### 3.2 CLI surface

```text
guru_overlay.py catalog verify --registry-root ROOT --source-ref REF
guru_overlay.py plan    --target TARGET --platform STACK --registry-root ROOT --source-ref REF --format json
guru_overlay.py apply   --target TARGET --plan-file -
guru_overlay.py adopt   --target TARGET --platform STACK --registry-root ROOT --source-ref REF
guru_overlay.py upgrade --target TARGET --platform STACK --registry-root ROOT --source-ref REF --expected-state-digest DIGEST
guru_overlay.py status  --target TARGET --format json
guru_overlay.py verify  --target TARGET [--expected-state-digest DIGEST]
guru_overlay.py unapply --target TARGET --expected-state-digest DIGEST
guru_overlay.py recover --target TARGET [--tx-id TX]
```

`plan/status/verify` 严格只读且只输出 stdout；不得因 `--format json` 创建目标 temp/lock。Serialized plan 是 versioned input，不是授权：`apply` 必须重验 manifest/source/target digests 和 operation schema。

退出码：`0` success/current/idempotent no-op；`2` usage/schema/manifest invalid；`3` plan/CAS/ownership conflict；`4` verify drift；`5` recovery_required/corrupt journal；`6` source/I/O/durability failure；`7` live lock contention。

| Method | Mutation |
| --- | --- |
| plan/status/verify | none: no lock, backup, temp state, migration or repair |
| apply | created/replaced content + structured config nodes |
| adopt | metadata/state only after known-source and current-content hash match; still uses WAL |
| upgrade | old committed generation to new generation with rollback point |
| unapply | remove/restore only owned nodes whose CAS matches |
| recover | only complete/rollback a durable nonterminal transaction or cleanup |

## 4. 核心数据结构与 ownership

```python
class OwnershipKind(str, Enum):
    CREATED = "created"
    REPLACED = "replaced"
    ADOPTED = "adopted"

class ValueState(str, Enum):
    MISSING = "missing"
    NULL = "null"
    VALUE = "value"

@dataclass(frozen=True)
class OwnedNode:
    path: str
    node_kind: Literal["file", "map-key", "list-item", "parent-map"]
    ownership: OwnershipKind
    identity_key: str | None
    before_state: ValueState
    before_digest: str | None
    after_state: ValueState
    after_digest: str

@dataclass(frozen=True)
class InstallState:
    schema_version: int
    generation: int
    extension_version: str
    manifest_digest: str
    source_digest: str
    target_root_fingerprint: str
    owned_nodes: tuple[OwnedNode, ...]
    project_assertions: tuple["ProjectOwnedAssertion", ...]
    committed_tx_id: str
    state_digest: str
```

Config map ownership 用完整 key path；list ownership 必须有稳定 `identity_key`，不按数组下标。`missing` 与 JSON/YAML `null` 是不同 sentinel。Preexisting exact list item/map value 记 `ADOPTED`，unapply 只移除 metadata。Manager 创建的 parent map 只有在所有 managed children 已撤销、parent 仍为空且 CAS 匹配时删除。

Workflow/Spec 是 `ProjectOwnedAssertion`，不是 `OwnedNode`。`ProjectTemplatePublish` 可作为 apply transaction 的 forward/rollback operation：失败 rollback时恢复 transaction前字节；成功 commit后项目成为新 Template内容的 owner，unapply只重验 assertion并保留内容。只有 manager亲自替换过 Extension asset/config node才可记 `REPLACED`；official staging产生的 Template内容不得伪装成 Extension `CREATED`。

### 4.1 错误枚举

| Error | Trigger | State after closure |
| --- | --- | --- |
| `TargetInvalid` | not official project、target fingerprint mismatch 或 path fence failure | unchanged |
| `PathFenceUnavailable` | platform cannot close required symlink/reparse race | unchanged |
| `PlanConflict` | ambiguous ownership or unsupported config structure | unchanged |
| `TargetChanged` | target digest/node CAS differs from plan | unchanged; re-plan required |
| `JournalDurabilityFailed` | backup/WAL file or directory fsync/atomic publish failed | unchanged before first write |
| `OperationFailed` | target mutation failed after WAL durable | rollback or recovery_required |
| `OwnershipConflict` | current owned node differs from expected post-state | preserved conflict; no delete |
| `StateCorrupt` | state/journal invalid, hash chain broken in middle or digest mismatch | recovery_required; no mutation |
| `UpgradeIncompatible` | source/state schema cannot transition | old committed version retained |
| `ReadOnlyViolation` | plan/status/verify attempted any write | hard test failure |
| `OfficialInstallPreflightFailed` | exact package/binary、remote ref、Catalog digest或fixture authority不匹配 | unchanged; no raw official run |
| `OfficialBlankFallback` | raw official rc=0 but expected spec/workflow/config postcondition absent or mismatched | unchanged target; stage cleaned; wrapper exits nonzero |
| `OfficialInstallPostconditionFailed` | staged bytes/source/hash boundary differ from typed Catalog result | unchanged target; stage cleaned; wrapper exits nonzero |
| `StageCleanupFailed` | external official stage/server/cert/bundle cannot be removed | nonzero; no target publish before cleanup succeeds, or committed cleanup_required after publish |

## 5. 逐行为设计：official wrapper、WAL、atomic publish 与 recovery

### 5.1 Official install wrapper

Raw official 0.6.7 是 compatibility executor，不是 success oracle。`apply/upgrade` 在任何真实 target mutation前必须按固定阶段执行：

1. **preflight**：验证 exact `@mindfoldhq/trellis@0.6.7` package/version/binary realpath、Catalog typed source/content digest、HTTPS smart Git advertised immutable ref和四个平台id；不得接受 file/local source或branch-only ref。
2. **staging**：在 target外的全新目录运行 raw `trellis init`，固定 PATH、CA和no-prompt环境，完整捕获 rc/stdout/stderr/tree digest。Raw spec failure可能 rc=0并 blank fallback，此事实不能被吞掉。
3. **postcondition**：逐字节/typed digest验证 spec tree、workflow、`registry.spec.source/template`、non-native workflow hash boundary、无 bundled Guru read。Raw rc=0但任何条件不满足即 `OfficialBlankFallback`/`OfficialInstallPostconditionFailed`。
4. **cleanup before publish**：将verified forward bytes封装为fsynced immutable payload后删除stage/server/cert；cleanup不成功则 wrapper nonzero且target不变。Payload随后作为PREPARED WAL引用，不能先写project files。
5. **publish**：按 WAL/CAS 将Template作为 `ProjectTemplatePublish`、Extension assets/config作为OwnedNode原子发布；commit后Template只进入project assertion，unapply保留。
6. **failure cleanup**：trap/signal/exception始终清理外部资源并保留primary error。Commit后仅payload cleanup失败时状态为`committed_cleanup_required`、返回nonzero，由mutating `recover`完成；不得谎报rollback或删除已commit project content。

这使raw rc0 blank fallback在Guru surface上稳定归一为nonzero，并保证false success不会污染真实target。Catalog只提供preflight truth；wrapper拥有stage/postcondition/cleanup/publish，不把责任推给shell调用方。

### 5.2 持久顺序

```text
durable backups
  -> BEGIN/PREPARED full reverse+forward plan (file fsync + parent fsync)
  -> target mutation(op)
  -> APPLIED(op, observed hash) + fsync, repeated
  -> InstallState temp fsync + os.replace + state-parent fsync
  -> STATE_PUBLISHED + fsync
  -> COMMITTED + fsync
```

Prepared journal 引用的 backup bytes/mode/symlink-kind 必须先 durable；不能先改 target 再补 snapshot。每条 JSONL record 带 monotonic sequence、previous-record digest 和自身 digest。Recovery 只容忍 torn final line并截断到最后完整 record；中间 checksum/sequence 破损是 `StateCorrupt`，不得猜测 replay。

任一 mutating command 先检查 nonterminal journal：所有 planned op 的 observed post hash 与 target 一致时补发 state/commit；否则按已 APPLIED 顺序逆序 CAS rollback。Current 不等于 recorded post 时保留用户内容、记录 unresolved op 并进入 `recovery_required`。InstallState 已发布但 COMMITTED 缺失时以 `committed_tx_id` 和完整 postcondition 补 commit marker。

### 5.3 Lock 与 target identity

单 target 一个 mutation lock，记录 tx id、host/boot identity、pid、process start identity、expected state generation 和 target root fingerprint。Stale recovery 必须同时证明原 process identity 不存活且 journal 可恢复；不得按 mtime/PID 数字直接删除锁。

Target root fingerprint 至少绑定 canonical path、filesystem device/inode（或平台等价 file id）、`.trellis` marker/config identity。Mutation 前逐 ancestor `lstat` 并使用 dir-fd/`O_NOFOLLOW`/平台 reparse-point adapter 关闭 symlink swap；若平台无法原子保证，则重新核对 parent file id + node CAS，并在 capability 不足时返回 `PathFenceUnavailable`，不得只做一次 `realpath` 预检后写入。

### 5.4 失败收口

首写前失败保持 target 不变；首写后失败只能依据 durable journal 完成正向提交或 reverse-CAS rollback。任一 current value 不等于 recorded post-state 时保留用户内容并进入 `recovery_required`，不得猜测覆盖或静默回退旧 apply engine。

## 6. 数据合同：Structured config CAS

JSON 使用结构化 parser。YAML 使用 lossless strict subset：block mapping/list/scalar，保留无关文本、顺序与注释；duplicate key、anchor/alias、merge key、flow collection、tab、类型冲突或无法定位稳定 source span 时 fail closed，不继续使用 marker block或重复顶层 `hooks:`。

每次 config write 前比较 whole-file base digest，防止 parse 与 atomic replace 间覆盖并发修改；node ownership/unapply 仍按完整 key path或 list identity比较 semantic installed-after value，因此无关用户编辑可保留。文件写入同目录 temp、fsync、atomic replace、parent fsync。Manifest 不拥有 secret-bearing path；否则无法同时满足“不记录 secret”和精确 restore，必须 `PlanConflict`。

## 7. 状态 / 边界：Apply/adopt/upgrade/unapply 状态机

| Operation | Legal transitions | Illegal transition closure |
| --- | --- | --- |
| apply | `absent -> applying -> installed` or `recovery_required` | installed target must use upgrade |
| adopt | `unmanaged -> adopting -> installed(adopted)` or `conflicted` | unknown/user-modified hash remains external |
| upgrade | `installed(n) -> upgrading -> installed(n+1)` or rollback to `installed(n)`/recovery_required | absent/unmanaged blocked |
| unapply | `installed -> uninstalling -> absent` or `conflicted/recovery_required` | absent idempotently reports no-op; corrupt state blocks |
| recover | nonterminal tx -> committed previous/new generation or recovery_required | no journal is idempotent no-op |

Unapply：CREATED node CAS match 后删除；REPLACED 恢复 before bytes/value/mode；ADOPTED 只移除 metadata；project-owned assertions/content 保留。成功 unapply 后 Extension-owned target 等价于 pre-apply；切回 native workflow是单独 official command，不由字符串删除实现。

## 8. `apply.sh` 兼容/删除边界

保留：`apply.sh <target> [flutter|go|ios|h5]`、stack 到 spec/workflow/layers/skills/analyze 映射、`GURU_ADVERSARIAL_ENABLED`、现有 Guru runtime path、用户值保护意图和 syntax/import/breadcrumb verify。Wrapper 只翻译参数、调用 `plan` 再 `apply/verify`，原样返回 manager exit code。

删除：rm-rf/cp 覆盖 skill；双向 mtime 同步用户/非 Guru skills；直接覆盖 workflow/spec；marker YAML merge和 fork-only `before_start`；内容关键字猜 ownership；默认删除 `.grilled-*`；默认创建/覆盖 bootstrap task；事务内 GitNexus analyze/AGENTS mutation；先全部 mutation 再末尾 verify。`sync_platform_skills.py` 只检查并输出外部恢复命令；GitNexus 是独立 opt-in。兼容期不得保留第二个可写 apply engine；rollback 是整 slice 回退，不是运行时 fallback 到旧写入器。

## 9. 测试映射

| Path | Test | Expected result |
| --- | --- | --- |
| fresh/repeat | `test_fresh_apply`, `test_repeat_apply_is_noop` | WAL before write; generation stable/idempotent |
| every crash boundary | `test_crash_recovery_matrix` | old or new committed state, never mixed |
| journal integrity | `test_torn_tail_and_corrupt_middle` | torn tail recovers; middle corruption blocks |
| target/config CAS | `test_apply_rejects_changed_target`, `test_config_node_conflicts` | zero overwrite; unrelated config retained |
| adopt known/unknown | `test_adopt_known_hash`, `test_adopt_rejects_ambiguous` | metadata-only success / external conflict |
| upgrade rollback | `test_upgrade_rolls_back_previous_generation` | old content/state restored after injected failure |
| unapply ownership | `test_unapply_created_replaced_adopted_project_assertions` | created removed, replaced restored, adopted/Template retained |
| missing/null/list/parent | `test_config_missing_null_list_identity_parent_cleanup` | exact round-trip; no index ownership |
| read-only operations | `test_plan_status_verify_have_zero_writes` | adapter write trap 0 and target tree digest unchanged |
| path race/lock | `test_path_symlink_swap_hardlink_and_lock_identity` | no outside write; live/PID-reuse lock not stolen |
| exact official E2E | `bash guru-template/overlay/tests/official_067_e2e.sh --extension` | four stacks; raw rc0 blank fallback becomes wrapper nonzero/unchanged target; no fork/bundled fallback; unapply preserves Template |
| error enum matrix | `test_error_enum_closure_matrix` | every error preserves declared committed/recovery boundary |

每个 success path 配套 I/O failure、CAS conflict、corrupt state/journal、lock collision 和 rollback conflict。Plan/status/verify unit tests使用 write-trapping adapter；E2E 再比较完整 target tree/pre-state。

## 10. 不得补造清单

- 不得以 pre-state snapshot 替代首写前 durable backups + WAL。
- 不得让 plan/status/verify “顺便修复”状态。
- 不得按 list index、整文件字符串或 hash-mismatch 删除用户内容。
- 不得把 project-owned Workflow/Spec 登记为 Extension CREATED ownership。
- 不得只用 `realpath` 预检覆盖 mutation 时的 symlink/reparse race。
- 不得在 COMMITTED 前删除 journal/backup，也不得无证据清 stale lock。
- 不得把 raw official rc=0当作Guru install成功，或在真实target直接试错后清理。
- 不得将unsupported file/local registry或上轮旧remote/ref用于official release fixture。

## 11. 不变量矩阵

| invariant_id | rule | owner | positive_case | negative_case | route_if_missing |
| --- | --- | --- | --- | --- | --- |
| INV-EXT-001 | first target write must-not occur before durable backups and PREPARED journal file+directory fsync | UNIT-extension-manager | durable tx/reverse bytes precede mutation | crash after write with no recoverable reverse plan | block apply/upgrade/release |
| INV-EXT-002 | unapply must-not delete CAS/hash-mismatched user content | UNIT-extension-manager | conflict preserved | user edit deleted | recovery_required + hard release failure |
| INV-EXT-003 | plan/status/verify must-not write target/state/temp/lock | UNIT-extension-manager | write trap zero | status creates migration/repair state | block command |
| INV-EXT-004 | adopted/project-owned Template content must-not be treated as created Extension content | UNIT-extension-manager | metadata/assertion removed only | Template/adopted file deleted | rollback and ownership defect |
| INV-EXT-005 | every target mutation must revalidate target/ancestor identity and node CAS at use time | UNIT-extension-manager | symlink swap/path race rejected | preflight-realpath passes then outside path is written | recovery/security blocker |
| INV-EXT-006 | config unapply must preserve missing/null/value, stable list identity and unrelated edits | UNIT-extension-manager | exact node restore with unrelated text retained | marker/index/whole-file restore loses user data | ownership conflict + release fail |
| INV-EXT-007 | Guru official-install wrapper must preflight and stage exact 0.6.7 output, verify content postconditions and convert raw rc0 blank fallback or cleanup failure to nonzero without target pollution | UNIT-extension-manager | current HTTPS ref stages exact Template, cleanup succeeds, then WAL publishes project assertions and Extension nodes | raw rc0, blank/mismatched stage, stale ref or failed cleanup is treated as success or mutates the real target | unchanged target or committed cleanup_required; block release |

当前状态保持 `ready_for_review_after_migration_exception`；未产生 method review evidence。
