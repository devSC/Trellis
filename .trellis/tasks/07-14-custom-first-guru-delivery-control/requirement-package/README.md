# Custom-first Guru Delivery Control Plane Requirements

## Package Contract

- Canonical root: this directory.
- Task behavior extraction: [`../prd.md`](../prd.md).
- Requirement main definition: [`requirement-main.md`](requirement-main.md).
- CLI intent definition: [`requirement-cli-command.md`](requirement-cli-command.md).
- Non-functional requirements: [`requirement-non-functional.md`](requirement-non-functional.md).
- Audit-only trace: [`traceability.md`](traceability.md), excluded from the canonical digest by `manifest.yaml`.
- Product decisions: [`decisions.md`](decisions.md).

This package does not redefine the approved requirements in `prd.md`. It assigns stable `REQ-UC-XXX` source identifiers and separates requirement truth from the task-level `BHV-NNN` extraction.

## Applicability

- UI/page requirements: N/A. This feature is a workflow, CLI and project-local control-plane capability with no product UI surface.
- HTTP/API endpoint requirements: N/A. No network service or public HTTP contract is introduced.
- CLI requirements: applicable for Extension lifecycle and deterministic Gate/control commands.
- Operations requirements: applicable only to local install, verification, rollback and benchmark fixtures; no production deployment is in scope.

## Confirmation Boundary

The user confirmed the Custom-first/Core-zero/reversible architecture as DEC-001 and later authorized the outcome-first milestone decomposition recorded as DEC-002. Milestone synchronization does not create a new product decision and must not restart Requirements/Overview/Detail review loops.

Only a new irreversible product choice, a real external-information gap, or newly expanded critical/high risk may require another user confirmation. Bootstrap burn, repeated planning review and same-provider independence claims are not prerequisites for the current milestones.
