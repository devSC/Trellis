You are reviewing a Trellis planning task before implementation.

Task: .trellis/tasks/06-26-guru-one-question-loop-requirements

Review goal:
Find any remaining requirement/design/implementation-plan blocker that could still let Guru full-chain requirements bypass Trellis one-question loop, or any inconsistency that makes the plan unimplementable or unverifiable.

Local validation already passed after the latest repairs:
- python3 ./.trellis/scripts/task.py validate 06-26-guru-one-question-loop-requirements
- git diff --check -- .trellis/tasks/06-26-guru-one-question-loop-requirements
- python3 guru-template/overlay/verify/guru_gate.py requirements .trellis/tasks/06-26-guru-one-question-loop-requirements

Current requirement contract:
- Goal: restore Trellis one-question loop in Guru full-chain requirements planning.
- High-risk product/scope/risk decisions default to exactly one next question per user turn.
- Each question must include decision point, why it matters, recommended answer, and trade-off.
- requirement-writing may draft formal requirement packages, but high-risk decisions remain ai_drafted, evidence_ready, or open until user confirmation exists.
- user_confirmed/user_confirmed_with_edits requires user_quote or confirmed_ref.
- Full Question loop log is recommended, not mandatory for this P1 patch.
- Product decisions confirmed is positive only when not a negative value and it contains DEC-* or a natural-language confirmed decision.
- Positive confirmed decisions require user_quote or confirmed_ref in the same decision item or its direct indented child block.
- Multiple OQ means two or more OQ-* entries in Open product/scope/risk questions.
- Multiple OQ requires a single next_question/next_action and all other OQ remain open.
- Batch confirmation is allowed only when the current user message explicitly asks for batch confirmation, e.g. "batch confirm", "confirm all at once", or "apply recommendations to these items".
- A single batch user quote may be copied to each covered decision only if each decision records which OQ ids the quote covers and uncovered OQ ids stay open.
- continue in planning may do evidence collection, structure cleanup, or review, but must not promote ai_drafted/evidence_ready to user_confirmed*, remove high-risk OQ, enter overview, detail, or task.py start unless the current user turn confirms the specific decision.
- evidence_ready means AI evidence is collected or assumptions are bounded; it is not user confirmation.

Current design:
- Harden planning breadcrumb and Guru workflow templates.
- Replace old "1~4 confirmation questions" default with one question by default and explicit batch exception.
- Update requirement-doc-standard so requirement-writing can produce ai_drafted/evidence_ready, not user_confirmed* without evidence.
- Update requirement-review to classify missing one-question evidence as REQ_BLOCKER for P0/P1/scope/acceptance/compliance/API/data/payment/account/safety, or PROCESS_DEFECT for field-only Brainstorm Evidence.
- Enhance guru_gate.py requirements with structural checks for Brainstorm Evidence, confirmed decisions, multiple OQ, and user_confirmed* evidence.
- Keep semantic judgment in requirement-review; gate remains structural.
- Update trellis-continue guidance to stop at one-question loop when planning still has high-risk OQ or ai_drafted/evidence_ready P0/P1.
- Keep local overlay and package template copies aligned.

Current implementation plan:
1. Update .trellis/workflow.md and packages/cli/src/templates/trellis/workflow.md.
2. Update Guru workflow templates, including guru-client.md, guru-go.md, and any other guru-* workflow with "1~4" or equivalent wording.
3. Update requirement-doc-standard and requirement-review in both guru-template/overlay and packages/cli template copies.
4. Update trellis-continue and the generated Codex/common continue template.
5. Before editing guru_gate.py symbols, run GitNexus impact analysis; before commit, run detect_changes.
6. Update guru_gate.py in overlay and template copies.
7. Run sync:guru if available; otherwise manually verify overlay/template parity and document command absence. Drift is blocking.
8. Add tests:
   - Missing Brainstorm Evidence fails.
   - Positive Product decisions confirmed without user_quote/confirmed_ref fails.
   - Multiple OQ without single next action fails.
   - user_confirmed* without confirmation hint fails.
   - Explicit batch confirmation passes only when each confirmed decision has evidence.
   - Missing full Question loop log passes when user_quote/confirmed_ref exists.
   - Existing overview/detail/detail-confirm Guru gate fixtures still pass.
   - Manual checklist validates Markdown-only skill behavior for trellis-continue and requirement-review.
9. Validate targeted Python gate tests, relevant CLI/template tests, task.py validate, Guru requirements gate, manual checklist, git diff --check.
10. Stay planning-only; do not start implementation or commit until user confirms.

Review history already fixed:
- F-001 PRD/design evidence mismatch fixed: hard minimum is user_quote or confirmed_ref.
- F-002 sync:guru/template drift verification added.
- F-003 batch exception behavior spec added.
- F-004 positive decisions and multiple OQ defined structurally.
- F-005 continue cannot promote confirmation status or remove high-risk OQ without current-turn confirmation.
- F-006 overview/detail/detail-confirm regression coverage required.
- F-007 unavailable Guru gate execution is blocking.
- F-008 orphan confirmed_by removed from hard evidence.
- F-009 evidence_ready defined and protected in continue.
- F-010 batch quote ownership defined.
- F-011 continue blocks overview, detail, and start.
- F-012 manual review checklist added for Markdown-only skill behavior.
- F-013 "nearby" replaced with same decision item or direct child block.

Output format:
- Findings first, highest severity first.
- For each finding include id, severity, affected artifact/section, why it blocks or risks readiness, and exact repair.
- If no findings remain, say the task is requirements-ready.
- End with exactly one machine-readable line:
review_result=<clean/requirements-ready|findings|blocked> route_class=<REQ_BLOCKER|PROCESS_DEFECT|none> max_severity=<critical|high|medium|low|none>
