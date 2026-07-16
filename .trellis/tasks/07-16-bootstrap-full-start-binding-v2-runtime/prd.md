# Fix Full/high Start Guard Binding Cycle

## Goal

Repair the Full/high Start Guard hash cycle without weakening any existing
requirements, detail, review, risk, confirmation, envelope, or lifecycle check.
The chronological regression must prove:

```text
build risk packet
-> record one Full confirmation batch
-> check-start
-> guarded start artifact binding
```

This child task is the only implementation SSOT. The parent task is an umbrella
and is never an implementation target.

## Scope Freeze

The current task is limited to the existing Guru source behavior that causes the
cycle:

1. Define a versioned stable Start Guard digest for
   `guru-risk-contract-v2`.
2. Exclude requirements/detail confirmation record contents from that stable
   digest.
3. Keep Full confirmation freshness in `check-start`, where requirements,
   detail, reviews, and the complete risk-packet byte set are recomputed.
4. Keep selected risk, detail, decisions, attestation, envelope, and lifecycle
   CAS checks in Start Guard.
5. Add one chronological regression crossing the real builder, confirmation,
   `check-start`, and guarded binding boundaries.

The following are explicitly deferred to an independent later task and are not
preconditions for source implementation: protected signers, root-owned launch
gates, external monotonic receipts/registries, and malicious same-workspace
agent bypass resistance.

## Confirmed Facts

- Current `guru_task._gate_digest()` hashes the full requirements/detail
  confirmation records.
- Full v2 confirmation must hash the risk packet set before writing those
  records.
- Therefore the risk packet binds the pre-confirmation digest, while Start
  Guard recomputes a different post-confirmation digest.
- `_full_confirmation_batch_problem()` already independently recomputes current
  requirements, current detail, and the sorted risk-packet byte-set digest.
- `_artifact_binding()` already independently validates the selected slice
  packet, risk packet, confirmed detail digest, decision universe, attestation,
  envelope, and lifecycle request digests.
- GitNexus reports `_gate_digest` as LOW impact and
  `_full_confirmation_batch_inputs` as HIGH impact with 19 upstream symbols and
  four affected processes. The implementation therefore requires focused Gate,
  Start Guard, and chronological regression tests.

## Core Capability Priorities

- **P0**: make the v2 Start Guard digest stable across the Full batch write.
- **P0**: preserve independent `check-start` requirements/detail/risk freshness.
- **P0**: prove the chronological risk -> confirm -> check-start -> guarded
  binding lifecycle.
- **P1**: preserve v1, Lite, Micro, lifecycle CAS, and mirror release boundaries.

## Requirements

### BHV-001 [REQ-UC-001] Confirmation-independent Start Guard digest

- **Given** a Full/high task using `guru-risk-contract-v2`
- **When** risk evidence is built before the one Full confirmation batch
- **Then** the Start Guard stable digest excludes `guru_gates.requirements` and
  `guru_gates.detail` confirmation record contents
- **And** writing the confirmation batch leaves that digest byte-identical
- **And** stable review evidence, task chain flags, and the gate-contract digest
  remain bound
- **And** legacy `guru-risk-contract-v1` keeps its existing digest behavior.

### BHV-002 [REQ-UC-002] check-start keeps Full Gate strength

- **Given** the stable Start Guard digest no longer contains confirmation records
- **When** `guru_gate.py check-start` runs
- **Then** requirements, overview, and detail structural Gates are rerun
- **And** requirements review plus overview/detail review readiness are current
- **And** the one Full confirmation batch is recomputed from current
  requirements digest, current detail digest, and the sorted current
  `risk-packets/*.json` byte digests
- **And** requirements/detail confirmation records have the exact same canonical
  projection except their gate-specific `artifact_digest`
- **And** every existing confirmation metadata field is validated: actor/time,
  scope, allowed next action, prompt summary, batch id/digest, requirements,
  detail, risk-set digest, mode/via, turn reference, and user quote
- **And** both records carry a domain-separated
  `confirmation_projection_digest` recomputed from that canonical projection,
  so accidental field mutation remains fail closed without feeding dynamic
  confirmation bytes back into the pre-confirmation risk digest
- **And** missing, empty, added, removed, renamed, or changed risk packet bytes,
  or changed requirements/detail artifacts, block before start.

### BHV-003 [REQ-UC-003] Guarded Start keeps selected binding and lifecycle CAS

- **Given** `check-start` reports `START_READY`
- **When** guarded start validates the selected slice
- **Then** selected slice/risk/envelope/attestation digests must match the
  request
- **And** risk task/slice/route/detail/invariant/decision bindings remain current
- **And** pre-lock, lock-internal, final pre-call, post-return, after-start, and
  compensation checks remain unchanged
- **And** no direct official `task.py start` bypass is introduced.

### BHV-004 [REQ-UC-004] Chronological regression proves the repaired state transition

- **Given** a real Full v2/high fixture with current planning artifacts
- **When** the test builds risk evidence, records the Full batch, runs
  `check-start`, and evaluates guarded Start binding in that order
- **Then** the stable digest is identical before and after confirmation
- **And** the valid path reaches verified guarded binding/start
- **And** requirements, detail, risk-set, selected-risk, attestation, and envelope
  drift each fail closed at their owning boundary.

## Non-Functional Requirements

- **Compatibility**: legacy Full v1, Lite, and Micro behavior must not change.
- **Scope**: modify only Guru source/tests/spec paths already allowed by
  `gate-contract.json`.
- **No threat-model expansion**: do not add external providers, registries,
  launch wrappers, new signing dependencies, or new lifecycle protocols.
- **Source first**: source implementation and focused/full source tests may
  proceed after child activation.
- **Mirror boundary**: the known 38 source/package mirror drifts block only
  package sync, install, and installed canary. They do not block source repair
  or source tests.

## Failure Paths

- Stable v2 digest changes after confirmation: regression failure; source repair
  is incomplete.
- Current requirements/detail/risk bytes differ from the recorded Full batch:
  `check-start` blocks.
- Selected risk/attestation/envelope binding differs: Start Guard blocks.
- Legacy v1 digest behavior changes: compatibility regression.
- Source tests fail: stop implementation and repair within this scope.
- Mirror baseline remains unresolved: keep sync/install/canary blocked, but do
  not roll back a green source repair.

## Acceptance Criteria

- [ ] For v2, `stable_digest_before_confirm == stable_digest_after_confirm`.
- [ ] For v1, confirmation-record mutation keeps the existing digest behavior.
- [ ] Full batch confirmation still binds current requirements, detail, and all
  current risk-packet bytes.
- [ ] Requirements/detail confirmation projections are exact peers and their
  stored `confirmation_projection_digest` matches all existing metadata fields.
- [ ] `check-start` rejects changed requirements, detail, and risk packet set.
- [ ] `check-start` rejects mutation or divergence of actor/time/scope/action,
  prompt, batch, input digests, mode/via/turn, or user quote.
- [ ] Guarded binding rejects changed selected risk, attestation, or envelope.
- [ ] One chronological regression crosses real risk builder, Full batch writer,
  Full batch validator/`check-start`, and Start Guard binding.
- [ ] Existing lifecycle CAS and compensation tests remain green.
- [ ] Focused `test_delivery_policy.py`, `test_start_guard.py`, and the Guru
  source regression suite pass.
- [ ] No protected-signer, root-launcher, external-registry, or malicious-agent
  mechanism is added to current production source.
- [ ] Mirror drift remains a release-only blocker for sync/install/canary.

## Out Of Scope

- Protected or hardware-backed authorization providers.
- Root-owned bootstrap launch wrappers.
- External monotonic activation or worker receipt registries.
- Same-workspace malicious agent race/bypass resistance.
- Parent task start or parent-owned implementation.
- Trellis Core changes.
- Package mirror sync, installation, or canary while the 38-drift owner baseline
  is unresolved.
- Himora business implementation.
- Commit, push, merge, archive, or finish-work in this step.

## Open Questions

None. The user explicitly froze the scope to the hash-cycle repair, preserved
Gate strength, and the chronological lifecycle regression.

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`, `trellis-meta`, `python-design`, and
  GitNexus debugging/impact guidance.
- Repository evidence inspected: `guru_task._gate_digest`,
  `guru_task._artifact_binding`, `guru_gate._full_confirmation_batch_inputs`,
  `guru_gate._full_confirmation_batch_problem`, `guru_gate.cmd_check_start`,
  focused tests, and the live 38-drift mirror check.
- Domain/terminology triggers: "stable Start Guard digest" means the
  pre-confirmation v2 artifact binding; "Full batch freshness" remains the
  post-risk dynamic confirmation check.
- Current code vs user intent conflicts: the current v2 Start Guard digest
  includes confirmation records that can only be written after risk creation,
  so the promised one-batch order is unsatisfiable.
- Product decisions confirmed: stop threat-model expansion, keep the parent as an
  umbrella, make this child the only implementation SSOT, and enter source
  implementation quickly. user_quote: "立即停止继续扩张当前设计。当前任务只处理
  Full/high Start Guard 哈希环修复、保持 Gate 强度，并完成真实生命周期回归；尽快进入
  SDK source implementation。" confirmed_ref: current Codex turn.
- Open product/scope/risk questions: none: the latest user directive explicitly froze the current scope; scope, ownership, release blocker, and deferred topics are all explicit.
- Rejected expanded design is preserved under
  `research/rejected-threat-model/` for a later independent task and is
  non-normative here.

### Question Policy

question_policy: mixed

- 证据已回答: root cause, affected functions, existing Gate ownership, and
  mirror drift behavior.
- 用户已确认: current scope freeze, parent umbrella role, child-only
  implementation ownership, deferred hardening, and source-first execution.
