# Umbrella Execution Plan

计划: delegate all executable slices to the child.

## 1. Execution Boundary

This parent is never started and contains no production implementation.
执行 is child-only.

## 2. Preconditions

- [ ] Parent remains planning.
- [ ] Linked child is the only implementation SSOT.

## 2.1 Slice To Unit Trace

| Slice | UNIT | BHV | Result |
| --- | --- | --- | --- |
| UMB-TRACK | UNIT-child-implementation-delegation | BHV-001 | child owns source repair |
| UMB-DEFER | UNIT-deferred-hardening-boundary | BHV-002 | hardening stays independent |
| UMB-NOSTART | UNIT-parent-non-start | BHV-001 | parent remains planning |
| UMB-INTEGRATE | UNIT-umbrella-integration | BHV-001, BHV-002 | consume child source proof; keep release blocker separate |

## 3. Child Delegation

- [ ] Complete child Gates and explicit child start.
- [ ] Implement and test only in the child.
- [ ] Consume the child source verification summary.

## 4. Release Boundary

- [ ] Do not block source work on the 38 mirror drifts.
- [ ] Keep sync/install/canary blocked until the owner baseline is resolved.

## 5. Stop Conditions

Stop if the parent would be started or if deferred hardening is reintroduced as
a current source prerequisite.

阻塞与偏差: parent start and scope re-expansion are the only umbrella blockers.
