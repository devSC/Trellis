Adversarial review. No tools. Review this planning contract only.

Task: 06-26-guru-one-question-loop-requirements.

Problem being fixed: Guru full-chain requirements currently can bypass Trellis brainstorm one-question loop by letting requirement-writing draft/confirm multiple high-risk decisions and by having guru_gate.py only check Brainstorm Evidence field shape.

Current contract:
- Default for high-risk product/scope/risk questions is one next question per user turn.
- A high-risk question affects scope, P0/P1 capability, acceptance, compliance, API/data contract, payment, account, or safety.
- The one question must include decision point, why it matters, recommended answer, and trade-off.
- requirement-writing may create drafts only: ai_drafted, evidence_ready, or open_questions.
- evidence_ready means AI evidence collected or assumptions bounded; it is not user confirmation.
- user_confirmed* requires user_quote or confirmed_ref in the same decision item or direct indented child block.
- Full Question loop log is recommended, not mandatory in this P1.
- Positive Product decisions confirmed requires user_quote or confirmed_ref.
- Multiple OQ means two or more OQ-* entries and requires a single next_question/next_action; other OQ remain open.
- Batch confirmation is allowed only when the current user message explicitly asks to confirm multiple items; one quote may cover multiple decisions only if each decision records covered OQ ids and uncovered OQ remain open.
- In planning, "continue" may collect evidence/review/clean structure but cannot promote ai_drafted/evidence_ready to user_confirmed*, remove high-risk OQ, enter overview/detail, or run task.py start unless the current user turn confirms the specific decision.

Implementation plan covers:
- workflow breadcrumb and Trellis template updates
- Guru workflow template updates replacing "1~4" default
- requirement-doc-standard and requirement-review updates
- trellis-continue update
- guru_gate.py structural checks
- overlay/template parity via sync:guru or manual drift check
- tests for missing Brainstorm Evidence, positive decisions without evidence, multiple OQ without next action, user_confirmed* without evidence, explicit batch confirmation, missing optional Question loop log, and existing overview/detail/detail-confirm regressions
- manual checklist for Markdown-only skill behavior
- GitNexus impact before editing symbols and detect_changes before commit

Already-fixed prior findings:
- Evidence minimum is consistently user_quote or confirmed_ref.
- sync:guru/template drift validation added.
- Batch exception behavior and quote ownership defined.
- positive decision/multiple OQ parsing defined.
- continue cannot promote confirmation or delete high-risk OQ without current-turn confirmation.
- overview/detail/detail-confirm regression required.
- unavailable Guru gate execution is blocking.
- evidence_ready defined.
- overview, detail, and start are blocked by continue boundary.
- "nearby" evidence wording replaced with same item/direct child.

Find at most 3 remaining blockers/process defects. If none, say requirements-ready.
End with exactly:
review_result=<clean/requirements-ready|findings|blocked> route_class=<REQ_BLOCKER|PROCESS_DEFECT|none> max_severity=<critical|high|medium|low|none>
