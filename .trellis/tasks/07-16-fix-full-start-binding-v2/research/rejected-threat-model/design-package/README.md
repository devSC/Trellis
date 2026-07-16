# Full Start Binding V2 Design Package

## Status

- Task: `07-16-fix-full-start-binding-v2`
- Lifecycle: `planning`
- Route/risk: `full_chain/high`
- Requirements: [`../prd.md`](../prd.md)
- Overview SSOT: [`design-main.md`](design-main.md)
- Implementation plan: [`../implement.md`](../implement.md)

No production runtime symbol has been edited. The package is the review baseline for the versioned stable-planning, risk-set, confirmation, activation and compatibility contracts.

## Navigation

| Area | Artifact | Primary trace |
| --- | --- | --- |
| Architecture, ownership and flow | [`design-main.md`](design-main.md) | BHV-001 through BHV-010 |
| Stable planning identity and versioning | [`chapters/stable-planning-binding.md`](chapters/stable-planning-binding.md) | UNIT-stable-planning-binding |
| Risk set and canonical user authorization | [`chapters/full-confirmation-authority.md`](chapters/full-confirmation-authority.md) | UNIT-full-confirmation-authority |
| Guarded start and later-slice membership | [`chapters/guarded-slice-activation.md`](chapters/guarded-slice-activation.md) | UNIT-guarded-slice-activation |
| Lifecycle regression, compatibility and release | [`chapters/binding-regression-release.md`](chapters/binding-regression-release.md) | UNIT-binding-regression-release |

## Source Of Truth Rules

1. `design-main.md` owns architecture, behavior ownership, inter-unit flow and compatibility policy.
2. Each chapter owns one UNIT and its detailed data/error/test contract.
3. `../design.md` is a pointer only and must not become a second normative design.
4. `../prd.md` owns desired behavior and acceptance; design cannot redefine it.
5. `../implement.md` owns execution order, validation and rollback points.
