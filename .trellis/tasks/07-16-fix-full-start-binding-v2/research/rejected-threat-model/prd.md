# Fix Full Start Binding V2

## Goal

修复 Full/high 任务从 risk packet、一次用户确认到 guarded start 的不可满足哈希环，并把 Full Start 的稳定规划事实、风险集合、用户授权和执行绑定拆成单向、可验证、可迁移的合同。

最终用户结果是：当修复后的 `guru_gate.py check-start` 输出 `START_READY` 时，同一批 requirements、detail、全部 expected risk packets 和用户确认必须能够通过 `guru_task.py start`；任一稳定产物、风险成员、授权证据或 selected/later slice 发生漂移时，系统继续 fail closed。最终 Himora 回放使用 `HIM-S1/HIM-S2`。

## Problem Statement

当前 Start Guard 的 `_gate_digest()` 把 `task.json.guru_gates.requirements` 和 `detail` 的完整 confirmation record 纳入 `risk_packet.artifact_digest`。Full v2 又要求先生成 risk packet，再用 risk packet set 生成一次 confirmation batch，并把 confirmation 写回这两个字段。

因此确认前 risk packet 绑定 `G0`，确认写入后 Start Guard 计算 `G1`；重写 risk packet 为 `G1` 又会改变 confirmation batch 的 risk-set digest。不存在合法的 artifact 生成顺序可以同时满足 confirmation freshness 和 guarded-start binding。

当前测试把 `confirm -> check-start` 与 Start Guard 分成两个静态 fixture，未覆盖真实状态转换。现有 Full batch 还只对 risk packet 文件做非空和字节哈希，没有验证全部 packet 的 schema、task/slice membership、policy、decision universe 或同一 batch 的 attestation/envelope 绑定。

## User-Confirmed Decisions

- 本修复是独立 P1、`full_chain/high` Trellis runtime 任务。
- 使用 Full Start Binding V2，不通过重复确认、迭代重算哈希或降低 Gate 强度绕过问题。
- 稳定规划摘要不得包含会在 risk packet 之后产生的 confirmation、attestation 或 envelope 内容。
- `check-start` 必须独立验证 requirements/detail/review readiness、完整 risk packet set 和一次 Full confirmation 的 current 状态。
- 全部 expected slices 必须由同一个 confirmation batch 覆盖；每个 later slice 在 worker 启动前仍需证明 membership。
- Legacy Full v1 和 Lite/Micro 必须保留各自原有流程；未知或混合版本 fail closed。
- Full Start Binding V2 必须由 task-level contract discriminator 选择；risk、attestation 或 envelope 不得自选版本，也不得在 V2 证据缺失时回退 legacy。
- canonical confirmation record 是 durable、可重放验证的用户授权 receipt 的 projection，不是信任根；TTY 仅是采集通道，无可信 receipt 时保持 planning/fail-closed。
- 当前任务固定为不启动的设计/集成 parent；实现进入独立 legacy Full v1/high bootstrap child，安装后用 disposable V2 canary 和 Himora 回放验收。
- Bootstrap child 的全部 `SDK-U1..SDK-U4` worker 固定使用 pre-repair installed v1 runtime；修复源码不得在 child 中途原地安装。所有 slice check 完成后，source-runtime 最终验证才可基于既有 v1 start evidence 创建 signed audited legacy registration，且不得借此授权新 slice。
- Child `prd.md` 在 requirements confirmation 前固定 `bootstrap_runtime_lock_sha256=62074a1fef9e68d758a57dbebb26a4bd9058839d529c89d77a42e0eff21397a7`；用户随后以 task tree 外的受信密钥签发 root-owned bootstrap anchor receipt。每个 worker 与 continuation registration 都以该外部 receipt 为 trust root，task-local PRD/lock/contract/confirmation 仅是 projections。
- Bootstrap anchor subject 绑定 repository/task、requirements digest、lock SHA、base commit/runtime tree 与 one-time event/nonce；用户必须使用 agent 无法调用的 passphrase/hardware-protected signing key，allowed-signers 和 receipt 由 root 在 workspace 外单次安装。现有无口令 `~/.ssh/id_rsa` 不合格。
- 先在独立 worktree 完成规划、实现和验证，再同步到目标 Himora 项目恢复其媒体进度任务。

Slice identifiers are namespaced:

- `SDK-U1..SDK-U4`: bootstrap child 的四个 canonical slice ids，分别映射 `UNIT-stable-planning-binding`、`UNIT-full-confirmation-authority`、`UNIT-guarded-slice-activation`、`UNIT-binding-regression-release`；risk filename 和 packet `slice_id` 只使用 `SDK-U*`。
- `FIX-F1/FIX-F2`: 隔离的两成员 canonical lifecycle regression fixture。
- `HIM-S1/HIM-S2`: 修复安装后目标 Himora 任务的两个业务 slices。

未带 namespace 的 `S1/S2` 不得作为需求、确认 subject 或测试证据。

## Confirmed Bootstrap Decision

当前 runtime 无法用已损坏的 V2 Guard 自举修复。用户已确认把当前任务固定为不启动的设计/集成 parent，并创建一个 legacy Full v1/high bootstrap child。该 child 使用旧版仍可满足的 requirements -> overview/detail -> detail confirmation -> risk/guard 顺序实现 runtime；安装后必须通过 disposable V2 canary，才允许 parent 集成和 `HIM-S1/HIM-S2` 回放。该确认只授权创建/规划 child，不授权启动或修改 production。user_quote: "确认"; confirmed_ref: Codex thread 019f69a6-c923-7792-8607-7863eae0430a。

## Requirements

### BHV-001 [REQ-UC-001] Confirmation-independent stable planning binding

- **Given** Full v2/high 任务已完成 current requirements、detail、decision inventory、policy/contract 和 review evidence
- **When** 系统在用户确认前生成一个或多个 risk packet
- **Then** 每个 packet 绑定同一个 versioned stable planning digest，且写入一次 Full confirmation 后该 digest 逐字节不变
- **And** 该摘要绑定 provider-asserted canonical repository namespace，防止跨 checkout/repository 重放
- **And** requirements/detail confirmation record、时间戳、turn reference、user quote、attestation 和 envelope 不得进入该稳定摘要

### BHV-002 [REQ-UC-002] Semantic risk packet set validation

- **Given** Full confirmation 将覆盖 `risk-packets/*.json`
- **When** confirm 或 check-start 读取该集合
- **Then** 一个共享 validator 必须验证每个 packet 的 schema/binding version、task、canonical filename、slice、matching slice packet、stable digest、scope/policy、decision universe、decision set 和 invariants
- **And** expected slice inventory 必须由 reviewed planning contract 独立定义，observed risk members 必须与 expected members 精确相等
- **And** malformed、empty、orphan、duplicate、cross-task、filename/slice mismatch、missing expected slice、unexpected slice、symlink escape 或混合版本均阻断

### BHV-003 [REQ-UC-003] One canonical Full confirmation authorization

- **Given** current stable planning binding 和完整 risk packet set 均有效
- **When** 用户进行 Full 单批确认
- **Then** 系统记录一个 versioned、domain-separated、task-bound 的 canonical Full confirmation authority
- **And** 它绑定 requirements digest、detail digest、stable planning digest、selection generation、policy version 和排序后的全部 risk members
- **And** authority 必须投影一个可重放验证的授权 receipt：受信平台 user-turn receipt、签名 interactive-terminal receipt 或签名外部 attestation；TTY presence、agent quote/turn-ref 字符串本身都不是信任根
- **And** signed subject 必须绑定 provider-asserted canonical repository namespace，且 audience 精确等于 `trellis-guru-full-start-v2:<repository_namespace>`
- **And** signed subject 必须包含 confirmed actor/time、via、turn ref、user quote digest 和 canonical action rows：selected slice 分别具有 `guarded_start`、`implement`、`check`，每个 later slice 分别具有 `implement`、`check`
- **And** `AuthorizationGrantCoreV2` 只包含 independently known immutable fields；不得包含 grant/authorization/batch/projection 派生 digest/id 或 replay-time `verified_at`
- **And** deterministic grant digest 先生成，authorization digest、batch id/digest 与全部 projection bytes 再按无环顺序唯一派生
- **And** requirements/detail 兼容记录不得成为 risk packet 的反向摘要输入

### BHV-004 [REQ-UC-004] Confirmation tamper remains fail-closed

- **Given** stable planning digest 不再包含动态 confirmation 内容
- **When** confirmation grant/batch id/digest、risk set digest、confirmed actor/time、scope、slice action、mode/via、turn ref 或 user quote 被删除、分叉或重写
- **Then** check-start 和 guarded start 均阻断
- **And** official task start 在前置失败时不得被调用

### BHV-005 [REQ-UC-005] Attestation and envelope bind the same authorization

- **Given** selected slice 需要 high-risk confirmation
- **When** 生成 per-slice attestation 和 execution envelope
- **Then** 二者必须绑定同一个 confirmation batch id/digest、risk packet set digest、selected risk packet digest 和该 slice 的显式 authorized-action projection
- **And** 重新哈希旧 batch、跨 batch 拼接或切换 selected slice 仍然阻断

### BHV-006 [REQ-UC-006] Guarded start preserves lifecycle CAS

- **Given** Full Start Binding V2 所有前置条件 current
- **When** `guru_task.py start` 执行
- **Then** Start Guard 在锁前、锁内、official start 前最后边界和 official start 后复核稳定 artifact 与动态 authorization
- **And** 保留完整 task/session snapshot、status-only postcondition、after-start observation 和精确 compensation/manual-recovery 合同

### BHV-007 [REQ-UC-007] Every later slice proves membership

- **Given** selected slice 与 later slice `i` 被一次 Full confirmation batch 覆盖，且 selected slice 已 guarded-start
- **When** later slice `i` 的 implement/check worker 即将启动
- **Then** preflight 必须证明 `i` 的 risk digest 属于原 confirmation risk member set，且其 slice/risk/policy/decision binding current
- **And** selected slice 必须分别具备 `guarded_start`、`implement`、`check` action rows/E bindings，每个 later slice 必须分别具备 `implement`、`check`
- **And** confirmation 后新增、修改、删除或改名任一 expected packet 均阻断

### BHV-008 [REQ-UC-008] Versioned fail-closed compatibility

- **Given** 仓库可能存在 legacy Full v1、Full v2、Lite 或 Micro 任务
- **When** runtime 选择 start/confirmation 验证算法
- **Then** Full v2 只能由 `gate-contract.json.start_binding.version=2` 与兼容的 Full/high policy 共同选择；risk evidence 不得选择或降级 task-level 算法
- **And** V2 adoption 必须在生成 A2/risk 前写入外部单调 registry；planning/check-start/start dispatch 每次查询该记录，task-local 全量回滚不得降级为 v1
- **And** legacy Full v1 保留原两阶段确认路径，Lite 保留一次 requirements confirmation，Micro 不继承 Full artifacts
- **And** bootstrap child 的 SDK worker 在全部 slice check 完成前只使用 pinned pre-repair v1 runtime；此后 source-runtime check-commit 必须先取得 external audited legacy registration，且该 receipt 不授权新 slice 或 V2 evidence
- **And** bootstrap runtime lock 的原始 SHA-256 必须作为 child requirements artifact literal 被用户确认；worker/registration 对 confirmed anchor 做 live revalidation，协调改写 task-local lock/contract/runtime 仍阻断
- **And** signed root-owned bootstrap receipt 是唯一 trust root；requirements confirmation、PRD literal、lock、contract 与 worker evidence 都只是必须匹配的 projections
- **And** v1/v2 packet 混用、未知版本或无法证明等价的旧 evidence 不得自动升级为新用户授权

### BHV-009 [REQ-UC-009] Real lifecycle regression replaces split-fixture false green

- **Given** 当前 unit/shell suites 可以在真实组合流程失败时保持全绿
- **When** 本修复完成
- **Then** 至少一个独立 fixture 必须连续执行 `build FIX-F1/FIX-F2 risk -> Full confirm -> check-start -> FIX-F1 guarded start -> FIX-F2 full authorization preflight`
- **And** 目标边界不得用 unconditional `START_READY`、伪 risk JSON 或预置 confirmation 绕过
- **And** installed-runtime canary 必须使用 `CANARY-SELECTED/CANARY-LATER`、外部临时 signer/registry 和可重放 evidence 文件

### BHV-010 [REQ-UC-010] Source, packaged mirror and installed target remain consistent

- **Given** `guru-template/` 是 Guru overlay source of truth
- **When** runtime 修复通过 focused verification
- **Then** 使用项目标准 sync command 生成 `packages/cli/src/templates/guru/overlay` mirror，并通过 mirror/apply/install verification
- **And** 当前 checkout 已存在的历史 mirror drift 不得被无审查地混入本任务
- **And** 标准 sync 只能由 named guarded-sync verifier 在 owner zero-drift baseline 通过后调用；apply/install、canary 和 source-runtime check-commit 必须重新验证 current mirror proof

## Non-Functional Requirements

- **Security**: 所有未知、缺失、混合或重放证据 fail closed；不能以 agent 可写字符串代替授权 provenance。
- **Bootstrap safety**: runtime 必须在 check-start、Start Guard 和 before-start hook 共同硬拒绝 design parent；bootstrap child 只能使用单独确认的 legacy Full v1/high 合同，且不能携带或回退自 V2 marker。
- **Determinism**: 所有 digest 使用 domain separation、显式 schema 和 canonical sorted inputs；文件创建顺序不得影响集合摘要。
- **Atomicity**: confirmation authority 和兼容 projections 必须原子写入或在部分写入时不可被视为 current。
- **Observability**: 错误必须区分 stable artifact stale、risk set invalid、confirmation stale、attestation mismatch、slice membership missing 和 lifecycle CAS conflict。
- **Compatibility**: 不静默改变 legacy field 的语义；版本选择必须可审计。
- **Scope discipline**: 不修改 Trellis Core，不处理 unrelated reinstall 产物，不修改目标 Himora 业务代码。

## Failure Paths

- **Stable binding drift**: requirements/detail/contract/review-policy/decision inventory 改变后，A2 或 current Gate 失配；阻断 risk generation、confirmation 或 start，要求回到规划证据刷新。
- **Risk set invalid**: malformed、orphan、cross-task、mixed-version、filename/slice mismatch、symlink escape 或 missing member；confirm/check-start 在写授权前阻断。
- **Confirmation stale/tampered**: canonical authority、requirements/detail projections 或 current input 不一致；A2 保持稳定，但 live authorization validation 阻断。
- **Attestation/envelope replay**: batch、risk set、selected member、task 或 selection generation 不一致；Start Guard 或 later-slice preflight 阻断。
- **Lifecycle race**: 锁内 final CAS 或 post-start exact check 失败；official start 前零副作用，official start 后执行精确 compensation，冲突时进入 manual recovery。
- **Legacy/migration ambiguity**: 无法证明 v1/v2 等价或版本混用；不自动升级、不降级 Gate，保持任务 planning/fail-closed。
- **Bootstrap deadlock**: broken V2 runtime cannot activate its own repair; keep parent planning, require separately approved legacy bootstrap child, then require repaired-runtime V2 canary before target sync.
- **Bootstrap runtime replacement**: repaired source/runtime is loaded by an SDK worker before all child slice checks, or the pinned installed v1 digest drifts; block the worker/release. After slice completion, source-runtime verification requires audited legacy registration from the existing v1 start and grants no new implementation.
- **Bootstrap lock rewrite**: task-local lock、contract projection、runtime 与 worker evidence 被一起改写；child requirements confirmation snapshot/literal 不再匹配，worker 与 legacy continuation registration 均阻断。
- **Bootstrap external anchor missing**: protected signer、root-owned allowed-signers/receipt 未就绪或 subject/signature/current registry 不匹配；child requirements confirmation/start 保持 operator-blocked，worker/registration 不得继续。
- **Mirror integration drift**: package sync 仍包含 unrelated baseline drift；阻断镜像集成，不把未审查文件混入本任务。
- **Mirror verifier bypass**: direct sync creates package files without a current guarded-sync proof, or proof/owner artifact/source mapping is stale; apply/install/canary/check-commit independently block.

## Acceptance Criteria

- [ ] `stable_digest_before_confirm == stable_digest_after_confirm`。
- [ ] 一个真实 Full v2/high fixture 完成 `FIX-F1/FIX-F2` canonical happy path并到达 verified guarded start。
- [ ] requirements、detail、contract、review/policy、decision inventory、slice packet、selected/unselected risk、confirmation、attestation 和 envelope 的逐项 drift 均有 fail-closed 回归。
- [ ] malformed/extra/orphan/cross-task/filename-mismatch risk packet 在 confirm 和 check-start 前被拒绝。
- [ ] reviewed expected-slice inventory 与 observed risk members 不精确相等时，confirm、check-start、guarded start 和 later-slice preflight 均阻断。
- [ ] confirmation 两个兼容 projection 任一安全字段不一致时，stable digest 保持不变但 live authorization validation 阻断。
- [ ] 无可信 authorization provenance、伪造 agent quote/turn-ref 或 authority projection 与授权事件不一致时均阻断。
- [ ] raw TTY 记录不能单独授权；receipt signature/token、subject digest、task、selection 或 verifier identity 任一不匹配时均阻断。
- [ ] grant subject 覆盖 actor/time/via/turn/quote/actions；相同 receipt 只能得到 byte-identical grant/batch/projections。
- [ ] `AuthorizationGrantCoreV2` 排除 self-derived identifiers 和 replay observations；grant -> authorization/batch -> projections 无环派生。
- [ ] 每个 E 绑定一个精确 `{slice_id, action}` row/digest；selected member 分别证明 `guarded_start`、`implement`、`check`，later members 分别证明 `implement`、`check`。
- [ ] attestation/envelope 全部重哈希后仍不能跨 batch 或跨 selected slice 重放。
- [ ] `FIX-F1/FIX-F2` 一次确认，FIX-F2 worker authorization current；确认后任一 fixture member 变化阻断。
- [ ] 当前 parent 的 check-start/guard/hook 均返回 `PARENT_TASK_NOT_STARTABLE`，official start/registry reservation 未调用；单独批准的 legacy bootstrap child 可达、范围受限。
- [ ] Bootstrap child 的全部 SDK worker runtime path/digest 与 pre-repair lock 相同；所有 slice check 后才创建 audited legacy registration，且 registration 不授权新 slice/V2 evidence。
- [ ] Child requirements confirmation 绑定 exact runtime-lock SHA-256 literal；每个 worker 与 continuation registration 从该 confirmed anchor 重算并拒绝协调改写。
- [ ] Root-owned external bootstrap receipt 由受保护用户密钥签发并绑定 requirements digest/lock/base/runtime；task-local projections 协调改写仍无法通过签名与 registry 验证。
- [ ] installed-runtime canary 以 `CANARY-SELECTED/CANARY-LATER` 生成可重放 PASS evidence 后，才允许 parent integration。
- [ ] Legacy Full v1 两阶段确认和 Lite 单 requirements 确认回归通过。
- [ ] V2 binding adoption 在 risk 前外部注册；协调删除全部 task-local V2 证据仍阻断 legacy downgrade。
- [ ] Start Guard 锁、pre/post snapshot、after-start hook 和 compensation 回归通过。
- [ ] Guru focused unit tests、shell verify tests、apply tests、mirror sync check 和 `git diff --check` 通过。
- [ ] Guarded mirror sync 生成 current integration proof；apply/install、V2 canary 和 source-runtime check-commit 均拒绝 proof 缺失、过期、owner baseline 未合入或额外 package delta。
- [ ] GitNexus `detect_changes --scope compare --base-ref main` 或 repo-pinned equivalent 只报告预期 runtime flows。
- [ ] 修复同步到目标项目后，目标 `HIM-S1/HIM-S2` risk packet、唯一 confirmation batch、check-start 和 guarded binding 可重放。

## Out of Scope

- 修改官方 Trellis Core lifecycle。
- 允许 direct official `task.py start` 代替 Full guarded start。
- 重构全部 Guru review/provider 模型。
- 自动认可旧用户 quote 为 Full v2 authorization。
- 修改 Himora 媒体进度业务设计或生产 Dart。
- 在本任务中吸收当前 reinstall 任务或 38 处既有 package mirror drift。

## Open Questions

无阻塞未决问题。`OQ-002` 已由用户当前回合明确确认；child 创建/规划可继续，但 parent/child start、production edits 和 lifecycle actions仍需各自 Gate 与后续授权。

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`, PUA Amazon architecture route, GitNexus debugging/impact analysis.
- Repository evidence inspected: `guru_task.py`, `guru_gate.py`, `guru_delivery_policy.py`, `guru_supervise.py`, current specs, focused tests, git history/blame and current mirror check.
- Domain/terminology triggers: current `_gate_digest` name overloads document Gate digest and Start Guard CAS digest; canonical terms are defined in `design.md`.
- Current code vs user intent conflicts: Full v2 promises one requirements/risk/design batch, but current Start Guard requires a confirmation-dependent risk digest and later slices cannot prove membership.
- Product decisions confirmed: versioned four-layer binding, one canonical Full authorization, fail-closed legacy compatibility, `HIM-S1/HIM-S2` membership, isolated runtime worktree; user_quote: "确认"; confirmed_ref: "Codex thread 019f69a6-c923-7792-8607-7863eae0430a".
- Product decisions confirmed: DEC-002 makes the current task a non-started design/integration parent and authorizes creation/planning of one legacy Full v1/high bootstrap child followed by a V2 canary; user_quote: "确认"; confirmed_ref: "Codex thread 019f69a6-c923-7792-8607-7863eae0430a".
- Open product/scope/risk questions: none; reason: every recorded architecture and bootstrap question has an explicit current-thread user confirmation.
  - next_action: proceed to parent and child planning reviews; no additional user question is open.

### Question Policy

question_policy: mixed

- 证据已回答: current code ownership, digest graph, regression commit, impact surface, test blind spots, mirror drift and compatibility behavior.
- 用户已确认: OQ-001 architecture/scope and OQ-002 bootstrap topology decisions in the current Codex thread.

### Question Loop Log

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-001 | 2026-07-16 | 是否采用 Full Start Binding V2，并创建独立 worktree 与 P1 Full-chain Trellis task 进入规划？ | 采用四层单向 binding；按 `SDK-U1..SDK-U4` 实现单元完成消环和多 Slice 授权，再同步 Himora | 只删除 confirmation 字段更快，但不能证明 malformed risk、cross-batch attestation 或 later-slice membership | "确认" | DEC-001: Full Start Binding V2 + isolated P1 Full planning | prd.md, design.md, implement.md, gate-contract.json |
| OQ-002 | 2026-07-16 | 是否批准当前任务作为不启动的 design/integration parent，并另建 legacy Full v1/high bootstrap child 实现 runtime，随后用 V2 canary 验证？ | 批准；这是不绕过 broken V2 Guard 且不降低 Gate 的唯一可执行自举边界 | 会增加一个 child task 和一次 canary，但避免 direct start 或伪称 V2 自授权 | "确认" | DEC-002: non-started parent + separately gated legacy bootstrap child + repaired-runtime V2 canary | prd.md, design-main.md, implement.md, gate-contract.json |

## Notes

- User confirmed task creation and planning on 2026-07-16.
- Task creation consent is not implementation consent. Keep status `planning` until final artifacts are reviewed and activation is explicitly approved.
- The bootstrap signer/receipt is an external-state prerequisite, not a task-local planning decision. Current state is blocked because no eligible protected key or root-owned anchor receipt exists.
