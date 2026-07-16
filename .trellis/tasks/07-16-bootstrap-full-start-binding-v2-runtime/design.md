# Full Start Binding Cycle Repair Design Entry

This child task is the only implementation SSOT.

- Overview: [`design-package/design-main.md`](design-package/design-main.md)
- Stable digest: [`design-package/chapters/stable-planning-binding.md`](design-package/chapters/stable-planning-binding.md)
- Full confirmation freshness: [`design-package/chapters/full-confirmation-authority.md`](design-package/chapters/full-confirmation-authority.md)
- Guarded binding: [`design-package/chapters/guarded-slice-activation.md`](design-package/chapters/guarded-slice-activation.md)
- Chronological regression: [`design-package/chapters/binding-regression-release.md`](design-package/chapters/binding-regression-release.md)
- Execution order: [`implement.md`](implement.md)

The binding order is:

```text
stable v2 Start Guard digest
-> risk packet
-> one Full confirmation batch
-> check-start freshness validation
-> guarded Start selected binding and lifecycle CAS
```

The rejected external trust/launch design is historical research only under
`research/rejected-threat-model/`.

