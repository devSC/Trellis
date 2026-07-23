# 追溯矩阵（机器生成，勿手编）

| 行为 | 名称 | 需求场景（REQ-UC） | 归属（§1） | 承接单元（§2） | 测试映射 | 实现切片 |
|------|------|------|-----------|---------------|---------|---------|
| BHV-001 | Runtime-required Full completion | — | ✅ | UNIT-acceptance-closure-contract, UNIT-runtime-completion | ✅ | ✅ |
| BHV-002 | Same-goal implementation repair continuation | — | ✅ | UNIT-acceptance-closure-contract, UNIT-repair-continuation | ✅ | ✅ |
| BHV-003 | Maximum rollback by owning defect | — | ✅ | UNIT-acceptance-closure-contract, UNIT-repair-continuation | ✅ | ✅ |
| BHV-004 | Runtime evidence contradicts planning SSOT | — | ✅ | UNIT-acceptance-closure-contract, UNIT-implementation-review-closure, UNIT-repair-continuation | ✅ | ✅ |
| BHV-005 | Acceptance-path-driven cross-layer verification | — | ✅ | UNIT-acceptance-closure-contract, UNIT-implementation-review-closure | ✅ | ✅ |
| BHV-006 | Post-implementation failure retrospective | — | ✅ | UNIT-acceptance-closure-contract, UNIT-repair-continuation | ✅ | ✅ |
| BHV-007 | Archived-task and no-script boundary | — | ✅ | UNIT-acceptance-closure-contract, UNIT-repair-continuation, UNIT-template-parity | ✅ | ✅ |
| BHV-008 | Source and installed-template parity | — | ✅ | UNIT-acceptance-closure-contract, UNIT-template-parity | ✅ | ✅ |

## 孤儿/断链清单
- 无（承接链闭合）
