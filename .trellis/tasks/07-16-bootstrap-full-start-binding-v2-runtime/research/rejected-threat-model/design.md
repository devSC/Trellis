# Bootstrap Full Start Binding V2 Design Entry

This Full-chain child uses a directory-level design package and inherits product intent from the parent without redefining it.

- Parent architecture SSOT: [`../07-16-fix-full-start-binding-v2/design-package/design-main.md`](../07-16-fix-full-start-binding-v2/design-package/design-main.md)
- Child overview SSOT: [`design-package/design-main.md`](design-package/design-main.md)
- Detail index: [`design-package/README.md`](design-package/README.md)
- Stable binding/dispatch: [`design-package/chapters/stable-planning-binding.md`](design-package/chapters/stable-planning-binding.md)
- Confirmation/receipt: [`design-package/chapters/full-confirmation-authority.md`](design-package/chapters/full-confirmation-authority.md)
- Activation/registry: [`design-package/chapters/guarded-slice-activation.md`](design-package/chapters/guarded-slice-activation.md)
- Regression/release: [`design-package/chapters/binding-regression-release.md`](design-package/chapters/binding-regression-release.md)

The child delivery order is:

```text
legacy Full v1 child activation
-> implement reviewed A2/R/C/E/registry contracts
-> source/package/install verification
-> disposable Full v2 canary
-> parent integration
-> HIM-S1/HIM-S2 replay
```

Requirements remain authoritative in `prd.md`; ordered execution remains authoritative in `implement.md`.
