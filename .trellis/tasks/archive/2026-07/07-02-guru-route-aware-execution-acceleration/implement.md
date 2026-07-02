# Guru route-aware execution acceleration implementation plan

## §1 计划 / 切片

### Slice 1 - route-aware workflow defaults

Design unit: UNIT-route-aware-workflow-defaults

BHV: BHV-001

Goal: remove stale unconditional adversarial requirements defaults from workflow/skill text while preserving full-chain strict behavior.

Target paths:

- `packages/cli/src/templates/guru/workflows/guru-client.md`
- `packages/cli/src/templates/guru/workflows/guru-go.md`
- `packages/cli/src/templates/guru/workflows/guru-h5.md`
- `packages/cli/src/templates/guru/workflows/guru-ios.md`
- `guru-template/workflows/guru-client-workflow.md`
- `guru-template/workflows/guru-go-workflow.md`
- `guru-template/workflows/guru-h5-workflow.md`
- `guru-template/workflows/guru-ios-workflow.md`
- `packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md`
- `guru-template/overlay/agents-skills/client-small-iteration-dev/SKILL.md`

Validation:

- `! rg "默认先运行 .*--adversarial requirements|default.*--adversarial requirements" packages/cli/src/templates/guru guru-template`
- Guru verify tests.

### Slice 2 - contract generation command

Design unit: UNIT-contract-command

BHV: BHV-002

Goal: add a stable command to create validated `gate-contract.json` files.

Target paths:

- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_contract.py`
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
- `guru-template/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/guru_contract.py`
- `guru-template/overlay/verify/tests/run_tests.sh`
- `.trellis/scripts/guru/guru_gate.py` and `.trellis/scripts/guru/guru_contract.py` only if dogfood validation requires it.

Validation:

- Generate valid micro/lite/full contracts.
- Reject high-risk downgrade.
- Validate generated JSON through `guru_contract.validate_contract`.

### Slice 3 - full slice preflight

Design unit: UNIT-full-slice-preflight

BHV: BHV-003

Goal: fail fast before implement worker launch when high-risk full work requires slice packets.

Target paths:

- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_review_record.py`
- mirrored `guru-template/overlay/verify/*`
- tests.

Validation:

- high/full no packet -> packet-required block before worker.
- high/full multiple packets -> explicit `--slice` requirement.
- non-high full -> no forced packet.

### Slice 4 - commit-plan write

Design unit: UNIT-commit-plan-write

BHV: BHV-004

Goal: persist commit-plan as mutable evidence without changing planning contract digests.

Target paths:

- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
- mirrored `guru-template` files.

Validation:

- `commit-plan --write` writes `commit-plan.json`.
- stdout remains JSON.
- no changes to `design.md` or `implement.md`.

### Slice 5 - slice-plan

Design unit: UNIT-slice-plan

BHV: BHV-005

Goal: provide compact read-only execution plan for full-chain packet tasks.

Target paths:

- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_review_record.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`
- tests and mirrors.

Validation:

- zero packet fixture.
- one packet fixture.
- multiple packet fixture.
- dirty out-of-scope fixture.

### Slice 6 - worker status JSON

Design unit: UNIT-worker-status-cleanup

BHV: BHV-006

Goal: distinguish live and terminal workers and expose cleanup as one machine-readable action.

Target paths:

- `packages/cli/src/templates/guru/overlay/verify/guru_supervise.py`
- tests and mirrors.

Validation:

- no workers.
- live worker.
- terminal done/killed/error workers.
- malformed event rows fail closed without traceback.

### Slice 7 - target overlay install

Design unit: UNIT-target-overlay-install

BHV: BHV-007

Goal: install source changes into `guru_ai_himora` after source validation.

Target repo:

- `/Users/devSC/Documents/JobProject/guru_ai_himora`

Validation:

- source CLI build passes.
- `guru apply flutter /Users/devSC/Documents/JobProject/guru_ai_himora` passes.
- target contains new commands/text.
- target `git diff --check` passes.
- target changed paths are reported.

## §2 Required Commands

Baseline source checks:

```bash
python3 -m py_compile \
  packages/cli/src/templates/guru/overlay/verify/guru_gate.py \
  packages/cli/src/templates/guru/overlay/verify/guru_contract.py \
  packages/cli/src/templates/guru/overlay/verify/guru_supervise.py \
  packages/cli/src/templates/guru/overlay/verify/guru_risk.py \
  packages/cli/src/templates/guru/overlay/verify/guru_review_record.py \
  guru-template/overlay/verify/guru_gate.py \
  guru-template/overlay/verify/guru_contract.py \
  guru-template/overlay/verify/guru_supervise.py \
  guru-template/overlay/verify/guru_risk.py \
  guru-template/overlay/verify/guru_review_record.py
```

```bash
bash packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh
```

Mirror checks:

```bash
diff -q packages/cli/src/templates/guru/overlay/verify/guru_gate.py guru-template/overlay/verify/guru_gate.py
diff -q packages/cli/src/templates/guru/overlay/verify/guru_contract.py guru-template/overlay/verify/guru_contract.py
diff -q packages/cli/src/templates/guru/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_supervise.py
diff -q packages/cli/src/templates/guru/overlay/verify/guru_risk.py guru-template/overlay/verify/guru_risk.py
diff -q packages/cli/src/templates/guru/overlay/verify/guru_review_record.py guru-template/overlay/verify/guru_review_record.py
diff -q packages/cli/src/templates/guru/workflows/guru-client.md guru-template/workflows/guru-client-workflow.md
diff -q packages/cli/src/templates/guru/workflows/guru-go.md guru-template/workflows/guru-go-workflow.md
diff -q packages/cli/src/templates/guru/workflows/guru-h5.md guru-template/workflows/guru-h5-workflow.md
diff -q packages/cli/src/templates/guru/workflows/guru-ios.md guru-template/workflows/guru-ios-workflow.md
diff -q packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md guru-template/overlay/agents-skills/client-small-iteration-dev/SKILL.md
```

Target install:

```bash
pnpm --filter @devsc/trellis --fail-if-no-match build
node packages/cli/dist/cli/index.js guru apply flutter /Users/devSC/Documents/JobProject/guru_ai_himora
```

## §3 Stop Boundaries

- Stop after planning artifacts are ready unless user explicitly asks to implement.
- Stop after quality gates and `commit-plan` before staging/commit.
- Do not archive or update external trackers unless explicitly requested.

## §4 Notes

- This task is full-chain because it touches workflow/gate/runtime/template behavior.
- Avoid writing validation evidence into `design.md` / `implement.md` after detail confirmation; use mutable evidence files for later execution records.
