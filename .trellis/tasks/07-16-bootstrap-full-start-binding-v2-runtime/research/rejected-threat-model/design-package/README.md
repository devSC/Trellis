# Bootstrap Full Start Binding V2 Design Package

## Status

- Role: legacy Full v1/high implementation child
- Parent: `07-16-fix-full-start-binding-v2`
- Lifecycle: planning
- Production edits: none

## Navigation

| Area | Artifact | Primary trace |
| --- | --- | --- |
| Architecture, ownership and bootstrap flow | [`design-main.md`](design-main.md) | BHV-001 through BHV-010 |
| Stable planning and dispatch | [`chapters/stable-planning-binding.md`](chapters/stable-planning-binding.md) | UNIT-stable-planning-binding |
| Risk set, receipt and confirmation | [`chapters/full-confirmation-authority.md`](chapters/full-confirmation-authority.md) | UNIT-full-confirmation-authority |
| Guarded activation and registry | [`chapters/guarded-slice-activation.md`](chapters/guarded-slice-activation.md) | UNIT-guarded-slice-activation |
| Regression, compatibility and release | [`chapters/binding-regression-release.md`](chapters/binding-regression-release.md) | UNIT-binding-regression-release |

## Source Of Truth

1. Parent PRD/design owns product architecture and final integration.
2. Child `prd.md` owns executable delivery requirements.
3. Child `design-main.md` owns implementation ownership and bootstrap flow.
4. Each chapter owns one UNIT.
5. `implement.md` owns order, checks and rollback.
