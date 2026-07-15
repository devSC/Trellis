# CLI Requirement Intent

## Applicability

CLI is applicable to Extension lifecycle, Gate inspection and benchmark execution. Exact Python signatures, file formats and exit-code enumerations belong to detailed design; this document owns only user-visible intent.

| CLI intent | Source scenario | Required outcome | Failure outcome |
| --- | --- | --- | --- |
| `plan` | REQ-UC-007 | Read-only proposed mutations, conflicts and required capabilities | Non-zero for invalid target/catalog; no target mutation |
| `apply` | REQ-UC-007 | Durable journal, atomic state publish and installed verification | Automatic rollback or recoverable journal state |
| `adopt` | REQ-UC-007 | Explicit ownership only for known source hashes | Ambiguous/user-modified files remain external conflicts |
| `upgrade` | REQ-UC-007 | Version transition preserving ownership and rollback point | Old installed version remains recoverable |
| `status` | REQ-UC-007 | Read-only ownership, drift and recovery state | Invalid state reported without repair mutation |
| `verify` | REQ-UC-005, REQ-UC-007 | Template/Extension/capability/Gate consistency verdict | Non-zero with exact mismatch |
| `unapply` | REQ-UC-007 | Remove only owned current content and restore pre-state | Conflicts preserved; recovery state retained |
| `intake` / route inspection | REQ-UC-001, REQ-UC-002 | Intent and execution route resolved independently | Invalid/unknown risk fails closed |
| `slice-plan` | REQ-UC-002, REQ-UC-003 | Read-only dependency/lock-aware packet plan | Missing/invalid/ambiguous packet blocks worker launch |

No command may write user global configuration, launch an implementation worker, confirm a Gate or mutate task lifecycle unless that mutation is the command's explicit documented purpose and all trusted preconditions pass.
