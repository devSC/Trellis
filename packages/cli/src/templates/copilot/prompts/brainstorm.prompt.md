---
description: "Guide requirements discovery for a Trellis task after task-creation consent."
---

# Trellis Brainstorm

## Non-Negotiable Interview Contract

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

## Non-Negotiable Evidence Rule

If a question can be answered by exploring the codebase, explore the codebase instead.

This is mandatory. Before asking the user a question, first check whether the answer is already available in code, tests, configs, docs, existing specs, or task history.

Do not ask the user to confirm facts that the repository can answer. Ask only for product intent, preference, scope, risk tolerance, or decisions that remain ambiguous after inspection.

## Domain Grill Subroutine

Run this subroutine before asking requirement questions when evidence shows any of the following:

- new domain terms or renamed concepts
- term conflicts with `CONTEXT.md`, `CONTEXT-MAP.md`, docs, ADRs, specs, or existing code
- overloaded or ambiguous wording
- unclear lifecycle, state, ownership, or boundary rules
- cross-context ownership ambiguity
- mismatch between current code facts and the user's requested behavior

When triggered:

1. Build a short context map from repository evidence first: code, tests, configs, docs, `.trellis/spec/`, `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`, and relevant task history.
2. Point out term conflicts directly instead of asking the user to rediscover them.
3. Recommend canonical terms for overloaded language and explain the trade-off.
4. Pressure-test boundaries with concrete scenarios, especially state transitions, ownership, failure paths, and cross-layer responsibilities.
5. When current code behavior conflicts with user intent, ask a "current code vs user intent" product decision question with a recommended answer.
6. Write confirmed long-term glossary or domain-boundary decisions to `CONTEXT.md` only when they are durable. Keep temporary task decisions in `prd.md`.
7. Propose an ADR only when the decision is hard-to-reverse, surprising-without-context, and a real trade-off.

Do not turn Domain Grill into a separate post-draft Gate. It is part of requirement discovery and feeds the requirements confirmation Gate.

---

Use this skill during Phase 1 planning to turn the user's request into clear requirements and planning artifacts.

## Preconditions

Use this skill only after task-creation consent has been given and the user is ready to enter Trellis planning.

If no task exists yet, create one:

```bash
TASK_DIR=$({{PYTHON_CMD}} ./.trellis/scripts/task.py create "<short task title>" --slug <slug>)
```

Use a concise title from the user's request. Use a slug without a date prefix. `task.py create` adds the `MM-DD-` directory prefix automatically.

`task.py create` creates the default `prd.md`. Update that file with the current understanding before asking follow-up questions.

## Planning Flow

1. Capture the user's request and initial known facts in `prd.md`.
2. Inspect available evidence before asking questions:
   - code, tests, fixtures, and configs
   - README files, docs, existing specs, domain notes, `CONTEXT.md`, `CONTEXT-MAP.md`, and `docs/adr/`
   - related Trellis tasks, research files, and session history when present
3. Separate what you found into:
   - confirmed facts
   - domain terms, ownership boundaries, and current code vs user intent conflicts
   - product intent still needed from the user
   - scope or risk decisions still needed from the user
   - likely out-of-scope items
4. Ask the single highest-value remaining question.
5. Include your recommended answer with the question.
6. After each user answer, update `prd.md` before continuing.
7. For complex tasks, create or update `design.md` and `implement.md` before implementation starts.

Do not invent a project-specific product/spec hierarchy. If the repository already has product, domain, or spec docs, use them. If it does not, proceed with the evidence that exists.

## Question Rules

Ask only one question per message.

Each question must include:

- the decision needed
- why the answer matters
- your recommended answer
- the trade-off if the user chooses differently

Do not ask process questions such as whether to search, inspect files, or continue brainstorming. Do the evidence work directly. Ask the user only when the remaining issue is a product decision, preference, scope boundary, or risk tolerance choice.

## Artifact Rules

`prd.md` records requirements and acceptance:

- goal and user value
- confirmed facts
- requirements
- acceptance criteria
- out of scope
- open questions that still block planning

`design.md` records technical design for complex tasks:

- architecture and boundaries
- data flow and contracts
- compatibility and migration notes
- important trade-offs
- operational or rollback considerations

`implement.md` records execution planning for complex tasks:

- ordered implementation checklist
- validation commands
- risky files or rollback points
- follow-up checks before `task.py start`

Lightweight tasks may have only `prd.md`. Complex tasks must have `prd.md`, `design.md`, and `implement.md` before `task.py start`.

`implement.md` is not a replacement for `implement.jsonl`. Use JSONL files only for manifest-style spec and research references when the task needs them.

## Quality Bar

Before declaring planning ready:

- `prd.md` contains testable acceptance criteria.
- Repository-answerable questions have already been answered through inspection.
- Remaining open questions are genuinely about user intent or scope.
- Complex tasks have `design.md` and `implement.md`.
- The user has reviewed the final planning artifacts or explicitly approved proceeding.

Do not start implementation until the user approves or asks for implementation.
