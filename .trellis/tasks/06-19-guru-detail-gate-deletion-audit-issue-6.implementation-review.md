# Implementation Review: Guru detail gate deletion audit and skeleton regression

Task: `.trellis/tasks/06-19-guru-detail-gate-deletion-audit-issue-6/`
Source issue: https://github.com/devSC/Trellis/issues/6

## Scope

Reviewed implementation against:

- `.trellis/tasks/06-19-guru-detail-gate-deletion-audit-issue-6/prd.md`
- `.trellis/tasks/06-19-guru-detail-gate-deletion-audit-issue-6/design.md`
- `.trellis/tasks/06-19-guru-detail-gate-deletion-audit-issue-6/implement.md`

Reviewed changed surfaces:

- `guru-template/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/tests/run_tests.sh`
- `guru-template/overlay/agents-skills/*-design-detail-writing/SKILL.md`
- `guru-template/overlay/agents-skills/*-design-detail-review/**`
- `guru-template/specs/guru-*/harness/detail/detail-structure-single-source.md`
- mirrored files under `packages/cli/src/templates/guru/**`

## Round 1

Severity result: P3 only.

Findings:

- P3-1: H5 detail review skill still had several D1~D8 wording residues after adding D9 deletion audit. Fixed to D1~D9 and updated the example table.
- P3-2: H5 example table separator had one fewer column after adding D9. Fixed the separator row.
- P3-3: `DETAIL_SECTION_PATTERNS` had a duplicated `状态 / 边界管理` regex alternative. Removed the duplicate.

Risk checks:

- Verified four platform L1 skeleton headings are covered by the shallow analyzer:
  - Flutter: `Widget 设计`
  - Go: `数据合同`
  - iOS: `View 设计` / `导航设计`
  - H5: `路由 / 渲染 / SEO`
- Verified test helper only passes `--deletion-audit` for `detail`, not `overview`.
- Confirmed `_gate_digest()`, `_review_state()`, `_review_run_validation_error()`, and `_review_run_is_clean()` were not modified after GitNexus reported high-risk impact for review-state helpers.

Conclusion: no medium/high issues. P3 issues were fixed before Round 2.

## Round 2

Severity result: no findings.

Acceptance matrix:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Detail chapter keeping UNIT/BHV but losing L1 skeleton fails | Pass | `detail skeleton loss` shell fixture expects exit 2 and `缺 L1 章节` |
| Cleanup preserving behavior contracts and L1 skeleton passes | Pass | upgraded passing full/light fixtures preserve L1 skeleton |
| `record-review detail --result clean` without deletion audit fails | Pass | shell fixture `record-review detail clean 缺 deletion audit 被拒` |
| `record-review detail --result clean --deletion-audit "none"` succeeds | Pass | shell fixture `record-review detail clean 带 deletion audit 可写入` |
| Status preserves deletion-audit visibility | Pass | shell fixture expects `deletion-audit ✅ none` |
| Flutter/Go/iOS/H5 review skills include D9 | Pass | D9 rows and clean record-review command present in all four review skill/reference sets |
| Flutter/Go/iOS/H5 writing skills include deletion ledger guidance | Pass | all four writing skills include destructive edit protection and ledger fields |
| L1 detail structure docs mention destructive edit preservation | Pass | all four `detail-structure-single-source.md` copies updated |
| Source template and CLI template are synchronized | Pass | touched files copied from `guru-template/**` to `packages/cli/src/templates/guru/**` |
| GitNexus detect_changes before commit | Pass | `node .gitnexus/run.cjs detect_changes --scope staged --repo "/Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree"` ran before commit; risk reported `critical` because the staged change intentionally spans Guru source template, CLI bundled template, four platform skills/specs, and detail review/gate flows |

Validation already run:

```bash
python3 - <<'PY'
import os, py_compile, tempfile
paths = [
    'guru-template/overlay/verify/guru_gate.py',
    'guru-template/overlay/verify/guru_supervise.py',
    'packages/cli/src/templates/guru/overlay/verify/guru_gate.py',
    'packages/cli/src/templates/guru/overlay/verify/guru_supervise.py',
]
with tempfile.TemporaryDirectory() as td:
    for i, path in enumerate(paths):
        py_compile.compile(path, cfile=os.path.join(td, f'{i}.pyc'), doraise=True)
PY
bash guru-template/overlay/verify/tests/run_tests.sh
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
pnpm --filter @devsc/trellis test -- test/guru/guru-bundled.test.ts
```

Observed results:

- Python compile: pass.
- `guru-template` shell gate tests: `132 通过 / 0 失败`.
- packaged template shell gate tests: `132 通过 / 0 失败`.
- CLI Vitest run: `50 passed`, `1275 passed`.
- GitNexus staged detect changes: ran before commit; affected scope is intentionally broad and covered by the implementation review and tests above.

## Final Review Conclusion

Implementation matches the local PRD/design and issue #6 scope. The first version intentionally enforces deletion audit at the write path for new clean detail reviews and surfaces the latest audit in status, while leaving high-risk review-state digest helpers unchanged for compatibility.
