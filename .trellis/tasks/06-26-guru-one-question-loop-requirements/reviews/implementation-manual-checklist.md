# Implementation Manual Checklist

Date: 2026-06-26

## Markdown Skill / Workflow Behavior

- `.agents/skills/trellis-continue/SKILL.md` contains the planning recovery rule for high-risk open product/scope/risk questions and P0/P1 `confirmation_status=ai_drafted` / `confirmation_status=evidence_ready`.
- `.agents/skills/trellis-continue/SKILL.md` forbids promotion to `user_confirmed*`, high-risk OQ removal, overview/detail/start, and stale `user_quote` / `user_confirmed*` reuse as current-turn approval during `continue`.
- `.agents/skills/trellis-continue/SKILL.md` requires a single highest-priority `next_question` unless the current user message explicitly requests batch confirmation and covers concrete OQ / decision ids; vague "continue/ok/use recommendation" replies fall back to one question.
- `guru-template/overlay/agents-skills/requirement-review/SKILL.md` classifies missing one-question confirmation evidence on P0/P1, scope, acceptance, compliance, API/data contract, payment, account, or safety decisions as `REQ_BLOCKER`.
- `guru-template/overlay/agents-skills/requirement-review/SKILL.md` classifies field-only Brainstorm Evidence without traceable confirmation as `PROCESS_DEFECT`, while keeping full `Question loop log` recommended rather than mandatory.
- `guru-template/overlay/agents-skills/requirement-review/SKILL.md` states that `evidence_ready` is not `user_confirmed*`, stale confirmation is only audit evidence, and vague batch confirmation must fall back to a single `next_question`.

## Sync Evidence

- `pnpm --dir packages/cli sync:guru` was attempted but pnpm aborted on non-TTY module purge.
- `node packages/cli/scripts/sync-guru-template.js` succeeded and reported `4 spec packages, 4 workflows, 99 overlay files`.
