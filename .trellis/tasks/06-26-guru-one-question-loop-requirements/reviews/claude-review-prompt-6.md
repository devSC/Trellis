You are Claude doing adversarial requirements review. No tools. Return only JSON plus the machine line inside JSON.

Task: 06-26-guru-one-question-loop-requirements.

Validated locally after latest repairs:
- task.py validate passed
- git diff --check for task dir passed
- guru_gate.py requirements for task dir passed

Contract after repairs:
- Guru full-chain planning must ask one high-risk product/scope/risk question per turn.
- High-risk includes scope, P0/P1 capability, acceptance, compliance, API/data contract, payment, account, or safety.
- Each question includes decision point, why it matters, recommended answer, and trade-off.
- requirement-writing can only draft ai_drafted/evidence_ready/open_questions.
- evidence_ready is not user confirmation.
- user_confirmed* requires user_quote or confirmed_ref in same decision item or direct child.
- Full Question loop log is recommended, not mandatory.
- Product decisions confirmed positive entries require user_quote or confirmed_ref.
- Multiple OQ requires exactly one next_question/next_action; other OQ stay open.
- Batch confirmation only when current user message explicitly confirms multiple items and records covered OQ / decision ids for each confirmed decision. Vague batch acknowledgement falls back to one next_question.
- current-turn confirmation means current user message directly answers an OQ/decision or explicitly references an existing confirmed_ref and confirms reuse.
- Historical user_confirmed* or user_quote remains audit evidence for already-confirmed decisions but cannot authorize new promotion, OQ deletion, overview/detail, or task.py start.
- In planning, continue can collect evidence/review/clean structure but cannot promote ai_drafted/evidence_ready, remove high-risk OQ, enter overview/detail, or start unless current-turn confirmation covers the specific decision.

Plan coverage:
- Updates workflow breadcrumb and templates.
- Updates Guru workflow templates replacing old 1~4 default.
- Updates requirement-doc-standard and requirement-review.
- Updates trellis-continue.
- Updates guru_gate.py structural checks.
- Keeps overlay/template copies aligned via sync:guru or manual drift check.
- Adds tests for missing Brainstorm Evidence, positive decisions without evidence, multiple OQ without next action, user_confirmed* without evidence, evidence_ready no silent upgrade, stale confirmation not current-turn approval, explicit batch confirmation, vague batch fallback, optional Question loop log, and overview/detail/detail-confirm regressions.
- Adds manual checklist for Markdown-only skill behavior including continue one-question recovery, stale-confirmation guard, vague-batch fallback, and requirement-review blocker rules.
- Requires GitNexus impact before editing symbols and detect_changes before commit.
- Stays planning-only until user confirms implementation start.

Find at most 3 remaining blockers/process defects. If none remain, result must be clean.

Return ONLY JSON:
{"result":"clean"|"findings","findings":[{"severity":"high|medium|low","issue":"...","fix":"..."}],"machine":"review_result=<clean/requirements-ready|findings|blocked> route_class=<REQ_BLOCKER|PROCESS_DEFECT|none> max_severity=<critical|high|medium|low|none>"}
