# Design: Guru detail deletion audit and skeleton regression

## Boundaries

This task changes the Guru detail harness and its bundled template guidance. It applies to the current `detail` gate/review scope only. It does not scan unrelated historical documents and does not attempt semantic equivalence across arbitrary markdown revisions.

The implementation must update both mirrored template surfaces:

- `guru-template/**`
- `packages/cli/src/templates/guru/**`

## Detail Skeleton Analyzer

Add small deterministic helpers inside `guru_gate.py`:

```python
def detail_chapter_blocks(task_dir: str) -> list[tuple[str, str]]:
    ...

def analyze_detail_chapter_skeleton(name: str, text: str) -> list[str]:
    ...
```

`detail_chapter_blocks()` enumerates the current detail gate input without leaking full-chain/light-chain storage details to `check_detail()`.

`analyze_detail_chapter_skeleton()` checks one markdown block for obvious skeleton loss. It should be intentionally shallow:

- require at least one `UNIT-<slug>` definition
- require `BHV-NNN` references unless the block is explicitly N/A by contract
- require universal headings or accepted aliases:
  - `单元职责`
  - `行为定义`
  - `核心数据结构`
  - `逐行为设计`
  - `状态管理`, `状态与事务`, or `状态 / 边界管理`
  - platform type-specific section such as `Widget 设计`, `View 设计`, `导航设计`, `数据合同`, `路由 / 渲染 / SEO`, or explicit N/A
  - `测试映射`
  - `不得补造`
- require shallow contract tokens for behavior, failure handling, test mapping, and non-goal/do-not-invent wording
- accept explicit `N/A` / `不适用` only when a reason is present in the relevant section text

Full chain behavior:

- analyze each chapter file in the current design package independently
- report the exact chapter name in findings

Light chain behavior:

- analyze the detail section under `design.md` section 2 as a block
- do not split by every `UNIT-` token, because L1 section headings may wrap one or more UNIT blocks

Existing ghost-BHV and behavior-without-UNIT trace checks must remain.

## Review Evidence

Extend `record-review detail` with:

```bash
--deletion-audit "<summary>"
```

Rules:

- required when `gate == "detail"` and `result == "clean"`
- optional for finding records
- stored as `deletion_audit` in the review run record
- truncated consistently with existing evidence fields
- surfaced in status/reporting output when present

`none` is accepted as a summary for non-destructive detail reviews.

## Review And Writing Guidance

Add D9 deletion audit to all platform detail review skills:

- `client-design-detail-review`
- `go-design-detail-review`
- `ios-design-detail-review`
- `h5-design-detail-review`

D9 blocks clean review when:

- large deletions lack replacement explanation
- L1-required sections disappear
- endpoint/interface coverage is treated as behavior coverage
- UNIT/BHV references remain but behavior contract content is flattened

Update all platform detail writing skills and L1 detail structure docs to require a deletion ledger before destructive rewrites.

Minimum deletion ledger fields:

| Field | Meaning |
|-------|---------|
| deleted_category | What kind of content was removed |
| reason | Why it was removed |
| replacement_location | Where the equivalent contract now lives, or N/A |
| removes_contract_obligation | Whether the deletion removes a still-valid contract |
| reviewer_decision | replaced / superseded / intentional N/A / blocking loss |

## Risk Control

- Keep `_gate_digest()` unchanged.
- Run GitNexus impact analysis before editing each existing function/method/class symbol.
- Avoid broad parser rewrites; implement the analyzer with local regex helpers already consistent with `guru_gate.py`.
- Add failing shell fixtures before or alongside the implementation so the observed false-green class is executable.
