# Product Decisions

## DEC-001 Custom-first Functional Boundary

- Status: confirmed product decision; an earlier Guru Requirements Gate confirmation exists, and final-digest batch review/reconfirmation is pending after consistency repair.
- Date: 2026-07-14.
- Source task: `07-14-custom-first-guru-delivery-control`.
- Decision: use official Custom Workflow/Spec Template distribution, keep functional changes out of Trellis Core, require a fully reversible Extension, and defer SDK de-fork deletion to a later independently verified slice.
- Reason: removes the fork as a forward dependency without weakening current safety boundaries.
- Affected scenarios: REQ-UC-001 through REQ-UC-007.
- User evidence: exact quote `好，接受`, recorded in `../prd.md` Brainstorm Evidence.
