# Implementation Plan

## Guardrails

- Do not edit Guru runtime scripts, schema validators, review normalization, templates, package assets, tests, or install scripts.
- Do not start the future full-chain implementation in this task.
- Do not claim the hardening behavior is implemented by this task.
- Leave unrelated dirty worktree changes untouched.

## Checklist

1. Confirm task scope.
   - Verify the active task path from the dispatch prompt or `task.py current`.
   - Verify `task.json` status is `planning` before dispatch or `in_progress` during implementation.
   - Verify `gate-contract.json` is `route=lite_task`, `risk=medium`.
   - Verify allowed paths only cover this task's planning/contract artifacts.
   - Verify the source draft is referenced read-only and is not listed as a writable surface.

2. Convert the draft into planning artifacts.
   - Update `prd.md` with goal, facts, requirements, out-of-scope items, and acceptance criteria.
   - Add `design.md` with traceability and future full-chain handoff boundaries.
   - Add `implement.md` with this checklist, guardrails, and validation commands.

3. Replace placeholder manifests.
   - Replace `implement.jsonl` placeholder with source-plan and guideline references.
   - Replace `check.jsonl` placeholder with validation references.

4. Validate artifact completeness.
   - Check required files exist.
   - Check key traceability rows are preserved.
   - Check markdown code fences are balanced.
   - Check JSONL files parse line-by-line.

5. Validate scope discipline.
   - Run `git diff --check` on this task's changed planning artifacts.
   - Inspect changed paths and confirm no runtime/schema/template/package/install files were modified by this task.

6. Stop before implementation.
   - Report that the lite planning package is ready.
   - State that behavior implementation still requires a separate full-chain task.

## Validation Commands

```bash
python3 ./.trellis/scripts/task.py validate .trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts
cat .trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts/gate-contract.json
python3 - <<'PY'
from pathlib import Path
import json
import subprocess

task = Path(".trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts")
required = ["prd.md", "design.md", "implement.md", "implement.jsonl", "check.jsonl", "gate-contract.json"]
missing = [name for name in required if not (task / name).exists()]
if missing:
    raise SystemExit(f"missing files: {missing}")

for name in ["prd.md", "design.md", "implement.md"]:
    text = (task / name).read_text()
    if text.count(chr(96) * 3) % 2:
        raise SystemExit(f"unbalanced fences: {name}")

for name in ["implement.jsonl", "check.jsonl"]:
    for line_no, line in enumerate((task / name).read_text().splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if "_example" in obj:
            raise SystemExit(f"placeholder remains in {name}:{line_no}")
        ref = obj.get("file")
        if ref and not Path(ref).exists():
            raise SystemExit(f"missing referenced file in {name}:{line_no}: {ref}")

contract = json.loads((task / "gate-contract.json").read_text())
if contract.get("route") != "lite_task" or contract.get("risk") != "medium":
    raise SystemExit("gate-contract route/risk mismatch")
allowed = contract.get("scope", {}).get("allowed_paths", [])
task_prefix = task.as_posix() + "/"
outside = [path for path in allowed if not path.startswith(task_prefix)]
if outside:
    raise SystemExit(f"non-task writable path in gate-contract: {outside}")
forbidden = [".trellis/scripts/guru", "guru-template", "packages/cli", "tests", ".trellis/spec"]
status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all", "--", *forbidden], text=True)
if status.strip():
    raise SystemExit(f"forbidden source/runtime/template/package/spec changes present:\n{status}")

print("artifact validation passed")
PY
git diff --check -- .trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts
git diff --name-only -- .trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts
git status --short --untracked-files=all -- .trellis/tasks/07-08-guru-repeated-debug-hardening-plan-artifacts
```

## Future Full-Chain Start Conditions

The future implementation task can start only after:

- the user explicitly asks to implement behavior, not only prepare artifacts;
- `guru_gate.py intake` is rerun with real Guru implementation paths;
- a separate full-chain task is created;
- `prd.md`, `design.md`, and `implement.md` are reviewed for that full-chain task;
- GitNexus impact analysis is run before symbol edits.
