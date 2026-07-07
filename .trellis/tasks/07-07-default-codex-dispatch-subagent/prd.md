# Default Codex dispatch mode to sub-agent

## Goal

Fresh Guru overlay installs should default Codex execution/check dispatch to
legacy Trellis sub-agents instead of official `trellis channel` supervised
workers.

## Requirements

- Update the Guru overlay config patcher so a fresh Guru project receives
  `codex.dispatch_mode: sub-agent`.
- Preserve existing user choices: if a target project already sets
  `codex.dispatch_mode`, the patcher must not overwrite it.
- Keep official/common Trellis defaults unchanged unless they are directly
  required by the Guru overlay behavior.
- Keep channel worker guard and Guru supervision defaults unchanged.
- Update tests and user-facing test names/comments that assert the fresh Guru
  default.

## Acceptance Criteria

- [ ] Running the Guru config patcher on an empty project writes
      `codex.dispatch_mode: sub-agent`.
- [ ] Running the patcher on a project with `codex.dispatch_mode: inline`
      preserves `inline`.
- [ ] Existing Guru config patch tests pass.
- [ ] No unrelated current-worktree changes are absorbed into this task.

## Brainstorm Evidence

- Skill loaded: trellis-brainstorm.
- Repository evidence inspected:
  - Current dogfood `.trellis/config.yaml` already uses
    `codex.dispatch_mode: sub-agent`.
  - `packages/cli/src/templates/guru/overlay/verify/guru_config_patch.py`
    has Guru supervision `DEFAULTS` with `codex.dispatch_mode=channel`.
  - `packages/cli/test/guru/guru-bundled.test.ts` asserts the fresh Guru
    project receives channel supervision defaults.
  - Common Trellis template keeps `codex.dispatch_mode` commented as `inline`;
    this task is Guru-overlay scoped.
- Domain/terminology triggers:
  - "channel" means official `trellis channel` supervised workers.
  - "sub-agent" means Codex/Guru legacy `trellis-implement` /
    `trellis-check` sub-agent dispatch.
- Current code vs user intent conflicts:
  - Fresh Guru overlay defaults currently set `channel`; user requested default
    `subagent`.
- Product decisions confirmed:
  - Default should be `sub-agent` for fresh Guru projects.
    - user_quote: "好，默认改为 subagent"

### Question Policy

question_policy: mixed

证据已回答的问题：repository artifacts identify the affected Guru overlay config
patcher, mirror file, and matching test assertions.

用户已确认的问题：current_turn_confirmation confirmed that the default should be
`sub-agent`.

- Open product/scope/risk questions: none — repository evidence answered scope,
  and the user confirmed the only remaining product decision.
- GitNexus impact:
  - `patch_config_text` upstream impact is LOW: one direct caller,
    `ensure_supervision_defaults`.
  - `DEFAULTS` candidates have maximum LOW risk and no direct impacted symbols.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
