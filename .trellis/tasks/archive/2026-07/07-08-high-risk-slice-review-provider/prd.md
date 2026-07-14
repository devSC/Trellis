# Configure high-risk slice review provider

## Goal

Add a configurable provider policy for high-risk Guru slice implementation reviews: default to current LLM subagent/review worker, with explicit opt-in for other LLM providers.

## Background

The current Guru high-risk slice path treats `risk=high` as an independent implementation-review requirement. In the live Himora case, `guru.supervision.provider: codex` plus a high-risk slice caused the supervisor to spawn `check-claude` because `_implementation_review_check_config()` flips to the opposite provider when `implement_check_independent_required()` returns true.

That behavior is too aggressive as a default. Teams need high-risk slices to stay independently reviewed, but the default review worker should stay within the current LLM provider unless the project explicitly opts into cross-LLM review.

This is separate from `guru.supervision.adversarial_enabled`. That flag only controls `guru_supervise.py --adversarial ...`; it must not be overloaded as the implementation-review provider policy.

## Confirmed Facts

- `guru.supervision.provider` is the current/default provider used by Guru supervision.
- `--adversarial` currently flips to the opposite provider and is skipped when `adversarial_enabled=false`.
- High-risk implementation review is currently driven by `guru_risk.implement_check_independent_required()` and then provider-flipped by `guru_supervise._implementation_review_check_config()`.
- Slice packets already carry `risk`, `risk_reasons`, and `semantic_review_provider`; raw provider metadata must be preserved for audit but is non-authoritative for slice-backed provider routing and provider-gate evidence.
- Required implementation review records validate the actual spawned `check_provider` against the worker's reported `review_provider`.
- Overlay scripts exist in local dogfood runtime, `guru-template`, `packages/cli/src/templates`, and `packages/cli/dist/templates`; source/template drift is a real risk.
- The dogfood runtime, Guru template, and CLI src template currently expose the same `implementation-review` path; the provider-policy implementation must preserve that parity.

## Semantic Review Provider Contract

The new high-risk policy distinguishes slice-backed provider routing from non-slice staged review:

- Provider precedence is `--same-provider` with a non-empty audited `--user-quote` > `guru.supervision.high_risk_review_provider_policy` > slice packet provider metadata. The one-off override always resolves to the current implementation provider and preserves the user quote in the review record.
- For `implement-check --slice` and `implementation-review --slice`, `guru.supervision.high_risk_review_provider_policy` is the authoritative provider decision. This remains true when the slice packet says `semantic_review_provider: {provider: opposite, required: true}`; otherwise a project configured with `current` could still spawn Claude and the parameter would not control the live behavior.
- Slice packet `semantic_review_provider` remains visible review metadata, but it does not override the configured provider policy for a high-risk slice.
- Required evidence must match the supervisor's actual resolved `check_provider`; deterministic checks and invariant coverage remain mandatory.
- If `implementation-review --staged` or `--contract` runs without `--slice`, it uses the existing staged-review synthetic packet and its explicit semantic provider contract unless a valid audited `--same-provider` one-off override is present. The high-risk config policy does not override that non-slice packet.

## Requirements

### BHV-001 High-risk default stays on current provider

Priority: P0

Given a high-risk Guru slice requires an independent implementation review, and no new provider-policy config is set.
When `guru_supervise.py implement-check ... --slice <UNIT>` or `guru_supervise.py implementation-review ... --slice <UNIT>` builds the check plan.
Then the check worker must use the current configured provider, not the opposite provider.

### BHV-002 Projects can opt into opposite-provider review

Priority: P0

Given `guru.supervision.high_risk_review_provider_policy: opposite`.
When a high-risk slice requires independent implementation review.
Then the check worker must use the opposite provider, preserving the old behavior intentionally.

### BHV-003 Projects can pin an explicit review provider

Priority: P1

Given `guru.supervision.high_risk_review_provider_policy: codex` or `claude`.
When a high-risk slice requires independent implementation review.
Then the check worker must use the pinned provider, regardless of current provider, and the review record must only accept that actual spawned provider.

### BHV-004 Invalid provider policy fails closed before spawning

Priority: P0

Given `guru.supervision.high_risk_review_provider_policy` is present but not one of `current`, `opposite`, `codex`, or `claude`.
When a Guru implementation/check supervision command would resolve provider policy.
Then it must fail before `trellis channel spawn`, with an actionable config error.

### BHV-005 Adversarial semantics remain separate

Priority: P0

Given `guru.supervision.adversarial_enabled=false`.
When a high-risk implementation review runs under the default provider policy.
Then `--adversarial` remains skipped, but high-risk implementation review still runs using the configured provider policy.

### BHV-006 Required evidence records same-provider high-risk review cleanly

Priority: P0

Given the high-risk provider policy resolves to the current provider.
When the worker emits a clean required implementation-review verdict with `review_provider` equal to the spawned provider.
Then `guru_review_record.normalize_review_record()` must accept it as required evidence when deterministic checks and invariant coverage pass.

### BHV-007 Template install preserves and exposes the policy

Priority: P1

Given `trellis guru apply <platform>` installs or refreshes the Guru overlay.
When the target config lacks the new policy.
Then the installer should add the default `current` policy while preserving existing explicit values; documentation and config snippets must describe the behavior.

## Failure Paths

- Invalid `high_risk_review_provider_policy` value must block before worker-plan construction or channel creation, must not silently fall back, and must emit no `WORKER=`, `check-*` plan, or `trellis channel spawn` command.
- `--same-provider` without a non-empty `--user-quote` must fail before config resolution or worker-plan construction.
- Slice-backed review records must validate against the provider resolved from `high_risk_review_provider_policy`, even when packet metadata requests `opposite(required=true)`.
- Missing `semantic_review_provider` must not be normalized into an implicit opposite-provider requirement that makes the default `current` policy impossible to satisfy.
- Without a valid audited CLI one-off override, non-slice staged/contract review keeps its existing explicit opposite-provider contract.
- Disabling `adversarial_enabled` must not skip high-risk implementation review.
- Template/source drift must block completion until synchronized or explicitly recorded as out of scope.

## Open Questions

None. The user confirmed the required product decision: high-risk slice review defaults to the current LLM subagent/review worker and can be configured to call another LLM.

## Question Loop Log

question_policy: evidence_only

- decision: Add a high-risk slice review provider policy.
  user_quote: "这样吧，给 high-risk slice 增加一个配置， 默认为调用 当前 llm 的 subagent 来进行审查，可配置为调用其他 LLM"
  result: Default policy is `current`; explicit values can opt into `opposite`, `codex`, or `claude`.
- decision: Create a full-chain task before implementation.
  user_quote: "好，同意"
  result: Task `.trellis/tasks/07-08-high-risk-slice-review-provider` created with `route=full_chain`, `risk=high`.
- decision: Make project config authoritative over slice packet provider metadata.
  user_quote: "确认"
  result: For slice-backed high-risk review, `high_risk_review_provider_policy: current` must keep the review on the current provider even when the packet requests `opposite(required=true)`; non-slice staged review remains unchanged.

## Acceptance Criteria

- [ ] Default high-risk `implement-check --dry-run` with current provider `codex` produces a `check-codex` worker, not `check-claude`.
- [ ] `high_risk_review_provider_policy: opposite` produces the previous `codex -> claude` and `claude -> codex` behavior.
- [ ] `high_risk_review_provider_policy: codex|claude` pins the check provider exactly.
- [ ] Invalid policy values fail before channel spawn.
- [ ] Invalid policy output contains the field name and allowed values, while stdout/stderr contain no `WORKER=`, `check-*` worker plan, or `trellis channel spawn`.
- [ ] `--same-provider --user-quote` overrides `opposite` and `claude` config values for one run, generates `check-codex` when the current provider is Codex, and preserves the quote in the record; missing/blank quote fails before any plan.
- [ ] Same-provider high-risk required clean review records are accepted only when the actual `check_provider` matches `review_provider`.
- [ ] Slice packet `semantic_review_provider: {provider: opposite, required: true}` cannot override `high_risk_review_provider_policy: current`; the generated worker and accepted record both remain bound to the configured current provider.
- [ ] Missing `semantic_review_provider` plus default `current` accepts same-provider high-risk required clean review when deterministic checks and invariants pass.
- [ ] `implementation-review --slice --dry-run` and `implementation-review --staged/--contract --dry-run` are covered separately from `implement-check --dry-run`.
- [ ] `implementation-review --staged/--contract` without `--slice` remains governed by its staged synthetic packet when no valid audited CLI one-off override is present; the high-risk config policy applies only to slice-backed targets.
- [ ] Dogfood `.trellis/scripts/guru/guru_supervise.py`, `guru-template`, CLI src template, and CLI dist template all expose the same relevant `implementation-review` provider-policy behavior, or drift is treated as a blocker.
- [ ] `adversarial_enabled=false` continues to skip only `--adversarial`, not implementation-review provider policy.
- [ ] `guru_config_patch.py` and `trellis guru apply` support preserving/defaulting the new policy.
- [ ] Runtime/template copies and overlay docs/config snippets are kept in sync.
- [ ] Workflow templates, implementation review agent skills, and Guru harness gate/spec docs are either updated or explicitly verified as only describing `--adversarial`.
- [ ] Existing Guru overlay verify tests pass, with new focused tests for provider policy.

## Brainstorm Evidence

### Question Policy

question_policy: mixed

- 证据已回答: repository evidence established the current high-risk provider flip and the config/runtime/template surfaces that must change.
- 用户已确认: current-turn confirmation "好，同意" authorizes continuing the full-chain task workflow.

- Skill loaded: trellis-brainstorm
- Repository evidence inspected: `.trellis/scripts/guru/guru_supervise.py`, `.trellis/scripts/guru/guru_risk.py`, `.trellis/scripts/guru/guru_config_patch.py`, `guru-template/overlay/verify/tests/run_tests.sh`, `guru_review_record.py`, CLI `guru apply` command wiring, config snippets, and related spec text.
- Domain/terminology triggers: "adversarial" vs "high-risk independent review" were overloaded; this PRD separates them.
- Current code vs user intent conflicts: current code flips high-risk implementation review to the opposite provider by default; user wants current-provider review by default.
- Product decisions confirmed:
  - decision: Default high-risk slice review to current LLM subagent/review worker; allow explicit other-LLM configuration.
    user_quote: "这样吧，给 high-risk slice 增加一个配置， 默认为调用 当前 llm 的 subagent 来进行审查，可配置为调用其他 LLM"
  - decision: Create a full-chain task before implementation.
    user_quote: "好，同意"
- Open product/scope/risk questions:
  - reason: repository evidence and user quotes resolved naming/default/scope for planning; no open user-intent blocker remains.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
