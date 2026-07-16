# Full Start Binding V2 Design Entry

This Full-chain task uses a directory-level design package.

- Overview SSOT: [`design-package/design-main.md`](design-package/design-main.md)
- Detail index: [`design-package/README.md`](design-package/README.md)
- Stable binding owner: [`design-package/chapters/stable-planning-binding.md`](design-package/chapters/stable-planning-binding.md)
- Confirmation owner: [`design-package/chapters/full-confirmation-authority.md`](design-package/chapters/full-confirmation-authority.md)
- Activation owner: [`design-package/chapters/guarded-slice-activation.md`](design-package/chapters/guarded-slice-activation.md)
- Regression/release owner: [`design-package/chapters/binding-regression-release.md`](design-package/chapters/binding-regression-release.md)

The package defines a forward-only dependency graph:

```text
StablePlanningArtifactV2
-> RiskDecisionPacketV2 set
-> FullConfirmationAuthorizationV2
-> per-slice ExecutionEnvelopeV2
-> guarded start / later-slice preflight
```

Task requirements remain authoritative in `prd.md`; ordered execution and verification remain authoritative in `implement.md`.
