# Claude Requirements Review Fix Log

## Review 1

`claude-requirements-review-1.md` is invalid evidence. The prompt passed `$(cat ...)` literally, so Claude did not receive the packet.

## Review 2

`claude-requirements-review-2.md` did not complete in useful time with the large packet and was interrupted.

## Review 3

Valid review evidence:

- File: `reviews/claude-requirements-review-3.md`
- Result: `review_result=findings route_class=PROCESS_DEFECT max_severity=high`

Findings and repairs:

- F-001: PRD and design disagreed on accepted confirmation evidence. Fixed by standardizing the hard minimum to `user_quote` or `confirmed_ref`.
- F-002: Implementation plan missed `sync:guru`. Fixed by adding a sync / overlay-template drift verification step.
- F-003: Batch exception lacked behavior specs. Fixed by adding BHV-006.
- F-004: Gate "positive" semantics were undefined. Fixed by defining positive decisions and multiple OQ structurally.
- F-005: `continue` evidence work could still mutate confirmation state. Fixed by forbidding `confirmation_status=user_confirmed*` changes or high-risk OQ removal without current-turn user confirmation.
- F-006: Existing Gate non-regression was not testable. Fixed by requiring Guru gate regression coverage for overview/detail/detail-confirm fixtures.
- F-007: Guru gate validation was skippable. Fixed by making unavailable gate execution blocking.

## Review 4

Valid review evidence:

- File: `reviews/claude-requirements-review-4.md`
- Result: `review_result=findings route_class=REQ_BLOCKER max_severity=high`

Findings and repairs:

- F-008: `confirmed_by` was an orphan hard-field reference. Fixed by removing it from the hard evidence requirement.
- F-009: `evidence_ready` was undefined and `REQ-006` did not protect it. Fixed by defining `evidence_ready` and extending `REQ-006` to both `ai_drafted` and `evidence_ready`.
- F-010: Batch quote ownership was unclear. Fixed by allowing a single batch quote to be copied to each covered decision while requiring covered OQ refs and leaving uncovered OQ open.
- F-011: `REQ-006` omitted detail design. Fixed by blocking overview, detail, and start.
- F-012: Markdown skill AC lacked automated validation. Fixed by defining manual checklist validation for skill behavior.
- F-013: "nearby" was vague. Fixed by requiring the same decision item or direct indented child block.

## Review 5

Invalid / inconclusive attempts:

- `claude-requirements-review-5.md`: invalid evidence, interrupted after no output.
- `claude-requirements-review-5b.md`: invalid evidence, interrupted after no output.
- `claude-requirements-review-5c.md`: invalid evidence, exited without output.
- `claude-requirements-review-5d.md`: invalid evidence, interrupted after no output.
- `claude-requirements-review-5e.md`: invalid evidence, interrupted after no output.
- `claude-requirements-review-5f.md`: invalid evidence, interrupted after no output.

Valid review evidence:

- File: `reviews/claude-requirements-review-5g.md`
- Result: `review_result=findings route_class=PROCESS_DEFECT max_severity=high`

Findings and repairs:

- F-014: Stale historical confirmation could be reused during `continue` as current approval. Fixed by defining `current-turn confirmation`, blocking stale confirmation reuse, and adding behavior / failure-path / test requirements.
- F-015: Batch confirmation could still be too loose for vague acknowledgements. Fixed by requiring explicit covered OQ / decision ids and routing vague batch language back to one `next_question`.
- F-016: `evidence_ready` upgrade and `user_confirmed*` evidence tests were not explicit enough. Fixed by adding gate/test requirements for no silent `evidence_ready` upgrade and mandatory confirmation evidence.

## Review 6

Valid review evidence:

- File: `reviews/claude-requirements-review-6.md`
- Result: `review_result=requirements-ready route_class=none max_severity=none`

Findings and repairs:

- No remaining findings. Claude returned `{"result":"clean","findings":[]}`.
