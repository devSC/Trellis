# Brainstorm Flow Hardening Plan

## 1. Problem

目标会话 `019ee562-3303-7180-ad61-21a25f299d83` 暴露的问题不是 Trellis 完全未进入 planning，而是进入 planning 后没有真正执行 `trellis-brainstorm` 的需求发现合同。

实际偏差：

- 用户请求“出彻底修复方案”时，agent 将其先当作方案说明处理。
- 用户回复“好，继续”后，agent 创建了 Trellis task，但同一个 assistant turn 内直接写完 `prd.md`、`design.md`、`implement.md`。
- `task.py create` 后的 planning breadcrumb 通常要等下一次用户输入才会注入；同 turn 继续写规划文件时没有被 `[workflow-state:planning]` 纠偏。
- 新 Guru 流程中的 Domain Grill 已前移到 `trellis-brainstorm`，但该 skill 没有被加载，所以 Domain Grill 子流程也没有执行。
- `guru_gate.py status` 只展示旧 `legacy grill missing (ignored by current Gate model)`，没有展示新流程真正缺失的 Domain Grill / brainstorm evidence。

## 2. Requirements

### R1. Task creation must point to brainstorm as the next required action

When `task.py create` creates a planning task,
then the command output must tell the agent that the next required step is to load `trellis-brainstorm`, update `prd.md`, inspect repository evidence, and ask at most one highest-value product/scope/risk question only when a real user decision remains before creating or finalizing downstream artifacts.

This is an advisory guard, not a shell-level blocker, because `task.py create` is used by multiple workflows and should stay script-chain friendly.
The advisory belongs on stderr with the existing human-readable `Next steps` output. Stdout must remain the task path for shell chaining.

### R2. New `prd.md` files must carry Brainstorm Evidence placeholders

When shared Trellis `task.py create` creates a default `prd.md`,
then the template must include a generic `Brainstorm Evidence` section with explicit pending placeholders:

- Skill loaded
- Repository evidence inspected
- Domain/terminology triggers
- Current code vs user intent conflicts
- Product decisions confirmed
- Open product/scope/risk questions

The section must be visible in every new task before the agent writes design or implementation plans. In plain Trellis projects it is advisory evidence only; Guru Gate is the layer that enforces it.

### R3. Guru requirements Gate must detect missing Brainstorm Evidence

When `guru_gate.py requirements <task_dir>` checks a task,
then missing or still-pending Brainstorm Evidence must block the requirements Gate with a clear recovery instruction:

```text
load trellis-brainstorm, complete Domain Grill / one-question loop, then update prd.md
```

This blocking Gate behavior applies to Guru projects only. Plain Trellis projects may receive the generic Brainstorm Evidence section from shared task creation, but no plain Trellis Gate enforces Guru-specific Domain Grill semantics.
Missing `## Brainstorm Evidence` is a Guru requirements violation, including for old-format PRDs, because the failure mode being fixed is "no evidence but still passes." Existing in-progress Guru tasks recover by adding the section with real or explicit negative evidence before rerunning the Gate; no broad migration or grandfathering is part of this change.
Explicit negative evidence counts as filled when it states the reason, for example `Domain Grill triggers: none — no new terms or code/user-intent conflict found` or `Open product/scope/risk questions: none — repository evidence answered all non-preference facts`.
Because `_default_prd_content` is shared by plain Trellis and Guru projects, the default template must use the generic label `Domain/terminology triggers` rather than the Guru-specific phrase `Domain Grill triggers`. Guru Gate validation treats `Domain/terminology triggers` as the canonical field for Domain Grill evidence and may accept `Domain Grill triggers` as a compatibility alias in hand-written or older PRDs.

### R4. Guru status must show the real new-flow gap

When `guru_gate.py status <task_dir>` renders requirements state,
then it must show whether Brainstorm Evidence is present or missing.

The old `legacy grill` line may remain compatibility-only, but it must not be the only visible signal related to missing brainstorm / Domain Grill work.

### R5. Existing legacy grill compatibility must remain non-blocking

The implementation must not reintroduce `design-grill` as a required post-draft Gate.

The new guard is about evidence that the new requirement-discovery flow happened; it is not a revival of `grill-done` / `grill-skip`.

### R6. Packaged Guru templates must stay in sync

Any source overlay change under `guru-template/overlay/**` must be mirrored into `packages/cli/src/templates/guru/overlay/**` through the existing sync path or equivalent targeted patch.

Any Trellis script template change under `.trellis/scripts/**` that affects installed projects must also be reflected in `packages/cli/src/templates/trellis/scripts/**`.

### R7. Tests must cover the regression

Add the smallest checks that fail if a new Guru task can pass requirements without filled Brainstorm Evidence.

At minimum:

- default `prd.md` creation includes the `Brainstorm Evidence` section in both local script and packaged Trellis script template;
- `task.py create` output includes the brainstorm-first next-step prompt;
- Guru requirements Gate blocks missing/pending Brainstorm Evidence;
- Guru status reports missing/present Brainstorm Evidence separately from legacy grill compatibility.

## 3. Non-Goals

- Do not add a queue, scheduler, database table, or new task status.
- Do not make `task.py create` block normal script chaining.
- Do not require `design-grill` or old `grill-done` records for new-model Gate pass.
- Do not force every non-Guru Trellis task through Guru Gate enforcement or Guru-specific Domain Grill labels.
- Do not implement a broad prompt linter or conversation transcript parser.

## 4. Minimal Design

### 4.1 `task.py create` output

Update the create command next-step text from generic planning guidance to explicit brainstorm-first guidance:

```text
Next required step:
  - Load trellis-brainstorm and update prd.md before design.md or implement.md.
  - Inspect repository evidence first; if a user decision remains, ask exactly one product/scope/risk question next.
```

This covers the same-turn inertia problem without adding a blocker.

### 4.2 Default `prd.md` template

Add this section to `_default_prd_content`:

```md
## Brainstorm Evidence

- Skill loaded: pending
- Repository evidence inspected: pending
- Domain/terminology triggers: pending
- Current code vs user intent conflicts: pending
- Product decisions confirmed: pending
- Open product/scope/risk questions: pending
```

The template section is deliberately simple text so agents can fill it without learning a new JSON schema.

### 4.3 Guru requirements evidence check

Add a small parser in `guru_gate.py`:

- locate `## Brainstorm Evidence`;
- inspect the section until the next `##` heading;
- require the six labels, using `Domain/terminology triggers` as the canonical label and optionally accepting `Domain Grill triggers` as a Guru compatibility alias;
- reject values that are blank, `pending`, `TBD`, or equivalent placeholder text;
- accept explicit negative evidence such as `none`, `not triggered`, or `no open questions` when the line explains why no trigger/question remains;
- match labels case-insensitively, ignore leading list markers and whitespace, and prefer prefix matching on the six canonical label names;
- report one concise problem per missing/pending item.

Use this helper inside `check_requirements`.
This is the structural enforcement path, not another advisory: existing Guru projects install `hooks.before_start: python3 .trellis/scripts/guru/guru_gate.py check` in `guru-template/overlay/config-snippets/config.hooks.yaml:13`, and `cmd_check()` in `guru-template/overlay/verify/guru_gate.py:1472` reruns `check_requirements()` before allowing `task.py start`. `auto()` in the same file also calls `check_requirements()` while the task is still in planning. Therefore adding Brainstorm Evidence validation to `check_requirements()` blocks `guru_gate.py requirements`, progressive `guru_gate.py auto`, and the before-start activation path. If pre-implementation inspection finds the call path has drifted, wire `cmd_check()` and `auto()` through `check_requirements()` before adding the new evidence parser.

### 4.4 Guru status rendering

Add a status helper:

```text
Brainstorm Evidence — ✅ present
Brainstorm Evidence — ⬜ missing: Skill loaded pending; Domain Grill triggers pending
```

Render this in `cmd_status` near the requirements Gate line so users see the real new-flow gap.

### 4.5 Template sync

Edit source and packaged copies that are already tracked in the current worktree:

- `.trellis/scripts/common/task_store.py`
- `packages/cli/src/templates/trellis/scripts/common/task_store.py`
- `guru-template/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/tests/run_tests.sh`
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`

Sync boundaries:

- `pnpm -C packages/cli sync:guru` only covers `guru-template/**` into `packages/cli/src/templates/guru/**`.
- `.trellis/scripts/common/task_store.py` and `packages/cli/src/templates/trellis/scripts/common/task_store.py` are Trellis script copies; keep them aligned manually or through the Trellis script-template sync path if one is available.
- Add a `guru_gate.py` source-vs-packaged helper equality check to the existing `packages/cli/test/guru/guru-bundled.test.ts` sync assertions so the two Guru Gate copies cannot drift silently.
- Add a `run_tests.sh` source-vs-packaged equality check to `packages/cli/test/guru/guru-bundled.test.ts` so source Guru shell regression additions cannot be dropped from packaged templates.
- Add a `.trellis/scripts/common/task_store.py` vs `packages/cli/src/templates/trellis/scripts/common/task_store.py` equality check to `packages/cli/test/guru/guru-bundled.test.ts` so the task creation template/advisory copy cannot drift silently.
- After GitNexus impact, compare the impacted symbols/files with this file list. If `cmd_create`, `_default_prd_content`, `check_requirements`, or `cmd_status` resolve to another file, add that source file and its packaged/template counterpart before editing.

## 5. Implementation Plan

1. Verify the enforcement path in current code before editing: `guru_gate.py check` must call `check_requirements()`, and `auto()` must call `check_requirements()` while status is `planning`; if either call is absent, wire it first.
2. Run GitNexus impact before editing these symbols:
   - `cmd_create`
   - `_default_prd_content`
   - `check_requirements`
   - `cmd_status`
3. Patch the default PRD template and create-output text.
4. Patch Guru requirements/status evidence helpers.
5. Update the existing `mk_good()` / requirements-pass fixtures in both Guru shell test files so they include filled Brainstorm Evidence using explicit negative evidence where appropriate.
6. Add focused shell regression tests in both `guru-template/overlay/verify/tests/run_tests.sh` and `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`.
7. Add a local script regression that runs `python3 .trellis/scripts/task.py create` in a temporary repo fixture, then asserts the generated `prd.md` contains `## Brainstorm Evidence` and command output contains `Load trellis-brainstorm`.
8. Add focused package assertions in `packages/cli/test/guru/guru-bundled.test.ts` that exercise the packaged Trellis script template and assert generated `prd.md` contains `## Brainstorm Evidence`.
9. Add a focused packaged-template assertion that `task.py create` output contains `Load trellis-brainstorm`.
10. Extend `packages/cli/test/guru/guru-bundled.test.ts` so `guru_gate.py` is included in the existing source-vs-packaged helper equality check.
11. Extend `packages/cli/test/guru/guru-bundled.test.ts` so `guru-template/overlay/verify/tests/run_tests.sh` and `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh` have a source-vs-packaged equality check.
12. Extend `packages/cli/test/guru/guru-bundled.test.ts` with a source-vs-packaged equality check for `.trellis/scripts/common/task_store.py` and `packages/cli/src/templates/trellis/scripts/common/task_store.py`.
13. Run the smallest relevant validation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  .trellis/scripts/common/task_store.py \
  packages/cli/src/templates/trellis/scripts/common/task_store.py \
  guru-template/overlay/verify/guru_gate.py \
  packages/cli/src/templates/guru/overlay/verify/guru_gate.py

bash guru-template/overlay/verify/tests/run_tests.sh
tmpdir="$(mktemp -d)"
cp -R .trellis "$tmpdir/.trellis"
(
  cd "$tmpdir"
  set -e
  git init >/dev/null
  git commit --allow-empty -m init >/dev/null
  python3 .trellis/scripts/init_developer.py reviewer >/dev/null
  task_path="$(python3 .trellis/scripts/task.py create "Brainstorm smoke" --slug brainstorm-smoke 2>/tmp/brainstorm-smoke-create.stderr)"
  grep -q "Load trellis-brainstorm" /tmp/brainstorm-smoke-create.stderr
  grep -q "## Brainstorm Evidence" "$task_path/prd.md"
)
pnpm -C packages/cli exec vitest run test/guru/guru-bundled.test.ts
pnpm -C packages/cli build
PYTHONDONTWRITEBYTECODE=1 bash packages/cli/dist/templates/guru/overlay/verify/tests/run_tests.sh
git diff --check
npx gitnexus detect-changes --scope all --repo Trellis
```

Adjust validation if the changed test surface proves a narrower or broader command set is necessary.

## 6. Review Protocol For This Change

Before implementation:

1. Review this document locally.
2. Fix findings.
3. Repeat local review until two consecutive rounds have no findings.
4. Run Claude adversarial review on this document.
5. Fix findings and rerun until no blockers remain.

After implementation:

1. Review the diff against this document.
2. Fix findings.
3. Repeat local review until two consecutive rounds have no findings.
4. Run Claude adversarial review on the implementation.
5. Fix findings and rerun until no blockers remain.
6. Run validation and commit only the scoped changes for this objective.

## 7. Acceptance Criteria

- [ ] New task creation output clearly tells the agent to load `trellis-brainstorm` and inspect evidence before downstream planning artifacts.
- [ ] New default `prd.md` contains `Brainstorm Evidence`.
- [ ] Guru requirements Gate blocks missing/pending Brainstorm Evidence.
- [ ] Guru status exposes Brainstorm Evidence state independently from legacy grill compatibility.
- [ ] Legacy `design-grill` remains compatibility-only and non-blocking.
- [ ] Source and packaged template copies stay aligned.
- [ ] Regression tests fail before the fix and pass after the fix.
- [ ] Two local document review rounds pass without findings before implementation.
- [ ] Claude adversarial document review passes before implementation.
- [ ] Two local implementation review rounds pass without findings before commit.
- [ ] Claude adversarial implementation review passes before commit.
