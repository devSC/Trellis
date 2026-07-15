# Requirement Traceability Audit

This file is excluded from the canonical requirements digest. Historical `UNIT-*` names remain trace anchors for the preserved design package, not implementation obligations. The outcome design in `../design.md`, milestones M0-M4 in `requirement-main.md` and `../prd.md`, and the executable paths below are the current authority.

## Final Executable Trace

| REQ / BHV | Outcome Design Contract | Executable Code | Test / Operational Evidence | Current Result |
| --- | --- | --- | --- | --- |
| REQ-UC-001 / BHV-001 | M0 route policy + M1 operational route proof: low-risk work reaches route-specific value without Full ceremony | `overlay/policy/delivery-policy.json`; `resolve_delivery_selection`; `guru_after_create.py` | `test_delivery_policy.py`; four-route apply matrix; `M1_OPERATIONAL_ROUTE_PROOF.md` | M1 candidate complete; Lite TTFC 18s, confirmation 0, Worker 0 |
| REQ-UC-002 / BHV-002 | M0 risk/start guard + M1 pre-write proof: high/unknown-high promotes to Full before code | `resolve_delivery_selection`; `build_risk_packet`; `guru_task.py:start_with_guard` | `test_delivery_policy.py`; `test_start_guard.py`; M1 missing-risk smoke | M1 candidate complete; pre-start rc 2, `start_attempts=0` |
| REQ-UC-003 / BHV-003 | M0 bounded closure + M1 deterministic close + M2 confirmation reuse | `build_execution_envelope`; `guru_task.py:start_with_guard`; bounded supervisor; route confirmation budgets | start-guard/supervisor regressions; M1 close; M2 unchanged-attestation regression | Confirmation batches <=1; unchanged attestation creates 0 repeat batches |
| REQ-UC-004 / BHV-004 | M0 exact reuse + M2 all-intent compounding | `resolve_delivery_selection` evidence fingerprint and cost-budget intersection | `test_all_intents_compound_on_exact_evidence_and_invalidate_on_either_digest`; `M2_ALL_INTENT_COMPOUNDING_PROOF.md` | M2 candidate complete; 7/7 warm=70%, both drift classes 7/7 invalidated; real provider tokens unknown |
| REQ-UC-005 / BHV-005 | M0 deterministic consistency + M3 source/install mapping + M4 final trace | `v0_consistency_check`; typed `index.json`; workflows/specs; overlay README/apply; this trace | stale/missing consistency negatives; official 0.6.7 E2E; catalog 18/0; lifecycle 120/0 | Executable trace complete; final M4 check pending |
| REQ-UC-006 / BHV-006 | M1 observability + M2 Gate net value: only true dependency/risk boundaries block | delivery policy gate lists; exact evidence reuse; append-only milestone evidence | Lite zero-precode-Gate regression; M1 metrics; M2 Gate classification | M2 candidate complete; observed false-positive Gate rework 0/4, small sample |
| REQ-UC-007 / BHV-007 | M0 reversible lifecycle + M3 official cutover: owned state is recoverable without Core changes | typed `index.json`; four spec/workflow stacks; `apply.sh`; schema-v2 rollback/managed-assets receipt | official 0.6.7 E2E; `test_guru_catalog.py` 18/0; `apply_test.sh` 120/0; `M3_CUSTOM_TEMPLATE_CUTOVER_PROOF.md` | M3 candidate complete; blank fallback rejected, read-only lifecycle honest, immediate pre-upgrade rollback proven |

## Boundary Readback

```text
packages/cli/src/**: zero functional-phase diff
packages/core/**: zero functional-phase diff
.trellis/scripts/guru/**: zero candidate-copy diff
task bootstrap history: unchanged, not burned, not reused
provider: Codex only; same-provider review has no independence claim
```

## Milestone Evidence

| Milestone | Canonical report | Status |
| --- | --- | --- |
| M0 | commits `de52458f`, `52e64185`; `USABLE_V0_REPORT.md` historical snapshot | completed |
| M1 | `M1_OPERATIONAL_ROUTE_PROOF.md` | candidate complete |
| M2 | `M2_ALL_INTENT_COMPOUNDING_PROOF.md` | candidate complete |
| M3 | `M3_CUSTOM_TEMPLATE_CUTOVER_PROOF.md` | candidate complete |
| M4 | `HARDENED_STATUS_REPORT.md` plus final exact-snapshot Codex check | current |
