# Full/high Start Guard Cycle Repair Umbrella

## Goal

Track the user outcome without owning implementation. The linked child
`07-16-bootstrap-full-start-binding-v2-runtime` is the only implementation SSOT
for the Start Guard hash-cycle repair, preserved Gate strength, and
chronological lifecycle regression.

## Core Capability Priorities

- **P0**: keep this parent unstarted and route all source work to the child.
- **P0**: prevent deferred hardening from blocking the child.
- **P1**: keep mirror drift as a release-only blocker.

## Scope

### BHV-001 [REQ-UC-001] Delegate the current source repair

- **Given** the Full/high confirmation hash cycle
- **When** the current repair is implemented
- **Then** only the linked child owns production source, tests, specs, and
  implementation evidence
- **And** this parent remains planning and is never started.

### BHV-002 [REQ-UC-002] Keep deferred hardening independent

- **Given** protected signers, root launch gates, external monotonic receipts,
  and malicious workspace-agent bypass resistance are valuable hardening topics
- **When** the current child proceeds
- **Then** those topics do not block or expand the source repair
- **And** their rejected draft is preserved under `research/rejected-threat-model/`
  as input to a later independent task.

## Acceptance Criteria

- [ ] Parent status remains planning.
- [ ] The linked child is the only implementation SSOT.
- [ ] Child source repair and source tests may proceed after child activation.
- [ ] Known 38 mirror drifts block only final sync/install/canary.
- [ ] Deferred threat-model hardening is not implemented in this task tree.

## Failure Paths

- Parent start attempted: block and return to the child.
- Source implementation appears in the parent: move ownership to the child.
- Deferred hardening becomes a child prerequisite: remove the prerequisite.
- Mirror drift blocks source tests: preserve source execution and keep only the
  release block.

## Out Of Scope

- Parent start or parent production edits.
- Reopening the child threat model unless a discovery directly violates the
  core hash-cycle/Gate-strength invariants.
- Treating mirror drift as a source implementation blocker.

## Open Questions

None. The user explicitly froze this topology and scope.

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm` and `trellis-meta`.
- Repository evidence inspected: live parent/child topology, task contracts,
  source Gate functions, tests, and mirror drift output.
- Domain/terminology triggers: parent means umbrella only; child means the sole
  implementation SSOT.
- Current code vs user intent conflicts: the previous parent package owned an
  expanded trust design that the user explicitly removed.
- Product decisions confirmed: parent umbrella, child-only implementation,
  deferred hardening, and release-only mirror blocker. user_quote: "立即停止继续扩张当前设计。" confirmed_ref: current Codex turn.
- Open product/scope/risk questions: none: scope and ownership were explicitly frozen by the user.

### Question Policy

question_policy: mixed

- 证据已回答: live topology and affected source boundaries.
- 用户已确认: umbrella/child ownership and deferred hardening.
