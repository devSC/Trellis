# Product Decisions

## DEC-001 Custom-first Functional Boundary

- Status: confirmed product decision; the M4 exact-snapshot implementation review verifies the
  existing decision and does not reopen planning or require reconfirmation. Only a newly discovered
  irreversible choice, external-information gap, or expanded critical/high risk can do so.
- Date: 2026-07-14.
- Source task: `07-14-custom-first-guru-delivery-control`.
- Decision: use official Custom Workflow/Spec Template distribution, keep functional changes out of Trellis Core, require a fully reversible Extension, and defer SDK de-fork deletion to a later independently verified slice.
- Reason: removes the fork as a forward dependency without weakening current safety boundaries.
- Affected scenarios: REQ-UC-001 through REQ-UC-007.
- User evidence: exact quote `好，接受`, recorded in `../prd.md` Brainstorm Evidence.

## DEC-002 Outcome-first Milestone Authority

- Status: confirmed execution-scope decision; no new product behavior is introduced.
- Date: 2026-07-15.
- Source task: `07-14-custom-first-guru-delivery-control`.
- Decision: preserve the original user outcomes and execute them through milestones M0-M4; internal modules, six slice lifecycles, bootstrap burn, Marketplace/WAL infrastructure, trusted reviewer identity and generic replay infrastructure are not completion criteria.
- Reason: the user explicitly required fast, low-rework delivery across all task types and later directed the work to remain efficient, self-use scoped and aligned to the original goal.
- Affected scenarios: REQ-UC-001 through REQ-UC-007.
- User evidence: `好，那后续真正的目标任务是什么？可以按照里程碑同步到需求中` plus the earlier 90-minute V0 and self-use scope directives.
