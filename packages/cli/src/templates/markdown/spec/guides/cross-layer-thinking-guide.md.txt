# Cross-Layer Thinking Guide

> **Purpose**: Think through data flow across layers before implementing.

---

## The Problem

**Most bugs happen at layer boundaries**, not within layers.

Common cross-layer bugs:

- API returns format A, frontend expects format B
- Database stores X, service transforms to Y, but loses data
- Multiple layers implement the same logic differently

---

## Before Implementing Cross-Layer Features

### Step 1: Map the Data Flow

Draw out how data moves:

```
Source → Transform → Store → Retrieve → Transform → Display
```

For each arrow, ask:

- What format is the data in?
- What could go wrong?
- Who is responsible for validation?

### Step 2: Identify Boundaries

| Boundary              | Common Issues                     |
| --------------------- | --------------------------------- |
| API ↔ Service         | Type mismatches, missing fields   |
| Service ↔ Database    | Format conversions, null handling |
| Backend ↔ Frontend    | Serialization, date formats       |
| Component ↔ Component | Props shape changes               |

### Step 3: Define Contracts

For each boundary:

- What is the exact input format?
- What is the exact output format?
- What errors can occur?

### Step 4: Freeze The Acceptance Path

Cross-layer verification is triggered by the accepted user outcome, not by the
number of layers changed in the current diff. Trace the complete
source-to-sink path whenever an acceptance goal depends on a user-visible
terminal state, an external API or schema, persistence or cache state,
asynchronous state, or a cross-layer field transformation. A one-file DTO or
parser change can still decide the final behavior.

For a Full task with `runtime_acceptance_required=true`, and for every goal
with one of the triggers above, freeze an Acceptance Closure Matrix in Detail
or `implement.md`. Each independently decidable row records:

- `acceptance_id`, its `required` flag, and its BHV, AC, or invariant references
- the user outcome and allowed terminal states
- the entry point and target environment
- the external or local authority plus a minimal contract fingerprint
- every source-to-sink layer and key field or state transformation
- positive and negative paths, including missing/null, error, timeout, and
  degradation behavior when applicable
- a deterministic check that fails on the known-bad implementation
- the runtime probe, execution owner, required evidence, and owning ordinary
  and Integration slices

The matrix is a digest-bearing planning contract. Runtime results do not edit
it; append sanitized results and artifact references to task-local
`verification-evidence.jsonl` instead.

### Step 5: Resolve Runtime Evidence Through ClosureSpec Only

Runtime acceptance uses these evidence/reporting values:

- `implementation_verified`: deterministic checks and review passed, but the
  target-runtime outcome is not yet proven
- `runtime_acceptance_pending`: the declared probe awaits target-environment
  execution
- `runtime_acceptance_failure`: the actual outcome does not satisfy the row
- `runtime_acceptance_pass`: environment, steps, expected result, actual
  result, evidence, and current baseline binding are complete
- `accepted`: task-level conclusion only after every required row is current
  pass and every process blocker is closed

The first four values are evidence row statuses. `accepted` is a task-level
reporting conclusion, not an evidence row status, and none of these values adds
a task lifecycle state.

#### ClosureSpec-only currentness

`ClosureSpec` is the only owner allowed to read and replay the raw ledger and
retrospective reconciliation journal. It returns one exact
`AcceptanceResolution` with all of these fields:

- `baseline_binding`
- `ledger_snapshot_ref`
- `reconciliation_snapshot_ref`
- `open_correction_debts`
- `open_retrospective_reconciliations`
- `row_results`
- `selected_evidence_refs`
- `blocking_evidence_refs`
- `task_result`
- `blocking_acceptance_ids`
- `next_probe`

This is a `ClosureSpec-only` result. Implement, review, repair, workflow, and
finish consumers must preserve the complete object. They must not select rows,
project away provenance or blocker fields, or privately recompute currentness.
Any ledger append, reconciliation event, or baseline change makes the whole
resolution stale and requires a complete recomputation.

#### Complete ledger replay and corrections

`EvidenceLedger.readAllInAppendOrder()` returns every physical append in a
`LedgerReadSnapshot`; it must not return a filtered ID/status view or a prefix.
Its `LedgerSnapshotRef` contains `artifact_ref`, `append_count`,
`last_append_position`, and `content_digest`, all bound to the complete raw
bytes. Each append retains its stable position, raw record, parse outcome, and
every readable identity and baseline component.

The empty-ledger identity is explicit: `append_count=0`,
`last_append_position=null`, and `content_digest` is the lowercase `SHA-256` of
the empty ledger file bytes. A non-empty digest always covers the complete
ledger file bytes for the referenced snapshot. For a nonempty snapshot,
`LedgerSnapshotRef.content_digest` equals the lowercase `SHA-256` of the exact complete ledger file bytes for that snapshot, never parsed, normalized,
filtered, or prefix bytes.

An unreadable append or a readable current-baseline append with an invalid
status or incomplete evidence creates an exact-position correction debt before
any acceptance-ID/status filtering. A correction must use
`corrects_append_position`, point to the earlier bad append, preserve every
parseable identity/baseline component, and supply a complete row. The newest
correction naming that position is authoritative; when it is invalid the debt
stays open. A normal later pass, wrong pointer, cross-ID row, baseline relabel,
or older correction cannot clear the debt or expose an older pass.

Only after every debt is closed may `ClosureSpec` select, by append position,
the newest effective current-baseline row for each required `acceptance_id` and
validate it. The canonical blocker order is: unavailable/corrupt reconciliation
journal, open retrospective reconciliation, open correction debt,
`runtime_acceptance_failure`, stale, missing, `runtime_acceptance_pending`, then
`implementation_verified`. Only an all-current-pass result with both open lists
empty can yield `task_result=accepted`.

#### Interruption-safe retrospective reconciliation

The journal is exactly `<task_dir>/retrospective-reconciliation.jsonl`, where
`task_dir` is the current active task or the linked active repair task. Setup
initializes the empty journal and rereads it completely. A fresh resolver only
locates it from `TaskRef`; it never creates a missing journal or discovers it
from a snapshot `artifact_ref`. Missing/unreadable and malformed journals are
respectively `reconciliation_register_unavailable` and
`reconciliation_register_corrupt`, both blocking `PROCESS_DEFECT` results with
`next_probe=null`.

The journal uses `journal-root-v1`. A complete newline-terminated
`ReconciliationJournalEvent` is appended for each transition. The first event
must have `event_position` `position=1` and
`previous_event_digest=null`; every later `previous_event_digest` is the
lowercase `SHA-256` of the previous event's complete UTF-8 bytes including its
newline. `RetrospectiveReconciliationSnapshot` contains `artifact_ref`,
`event_count`, `last_event_position`, `last_event_digest`, `content_digest`,
and replayed entries. For a non-empty journal, `last_event_digest` is the
lowercase `SHA-256` of the final complete newline-terminated event bytes and
`content_digest` is the lowercase `SHA-256` of the complete journal file bytes.
The empty-journal identity is `event_count=0`, `last_event_position=null`,
`last_event_digest=null`, and `content_digest` equal to the lowercase `SHA-256`
of the empty journal file bytes. All values must match a strict full replay.
Partial lines, a non-root prefix, gaps, duplicates, digest mismatch, invalid
transition, or snapshot mismatch are corrupt. A transition is acknowledged
only after strict full replay proves it is the unique legal last event; no
later side effect may run before that acknowledgment.

Before appending retrospective evidence, persist a
`RetrospectiveAppendAttempt` containing `attempt_id`, `acceptance_id`, the
current baseline, `retrospective_artifact_ref`, exact row digest,
`pre_append_ledger_snapshot_ref`, and `retry_ordinal` (0, or the single allowed
retry 1 with `retry_of`). The prepared event must be acknowledged before the
ledger append. `LedgerAppendResult` can be accepted, explicitly rejected, or
have missing acknowledgment (`retrospective_append_outcome_unknown`).

`LedgerAppendRef` is independently computed as
`deriveLedgerAppendRef(full_snapshot, exact_position)`: `artifact_ref`, exact
append position, and lowercase `SHA-256` of that position's complete raw append
bytes including its newline. Journal data must never participate in this
derivation. `RetrospectiveAppendReconciliation` first proves that the current
ledger prefix exactly equals the attempt's pre-append snapshot, then inspects
only the suffix. For ordinal 0, one exact suffix match is `committed`, zero is
`absent` and permits exactly one ordinal-1 retry on a newly acknowledged
boundary; boundary drift, a history-only/non-unique/unreadable match, or a
missing ordinal-1 acknowledgment is `ambiguous`. There is no third retry,
record, acceptance decision, runtime probe, or Finish bypass.

An accepted or `committed` append only supplies `accepted_append_ref`; it does
not close the attempt. Repair must build the canonical
`FailureRetrospectiveRecord` and `record_ref`, then `ClosureSpec` appends an
acknowledged `record-bound` event containing `accepted_append_ref`,
`record_ref`, and exact `closes_attempt_ids`. Without a retry, the list is
exactly ordinal 0; after a successful retry, it is exactly the ordinal-0 plus
ordinal-1 chain. Missing ancestors, extra IDs, or cross-acceptance,
cross-baseline, or cross-row chains remain open/corrupt. Every replayed entry
whose `record_ref` is null remains in `open_retrospective_reconciliations`
regardless of its state. Only full-replay acknowledgment of the valid
`record-bound` event closes the complete chain.

Finally run `retrospective-ledger-journal-correlation`: independently derived
ledger refs, acceptance ID, baseline, and row digest must identify exactly one
surviving journal chain for each retrospective ledger append. An older-valid
journal prefix, empty rollback, cross-position ref, or repeated identical raw
row that produces zero or multiple matches is corrupt and cannot be rescued by
a later pass.

### Step 6: Close Post-Implementation Failures

For every user- or QA-reported runtime failure, bind the repair retrospective
to the same `acceptance_id` and record:

- the evidenced direct cause
- the earliest Requirement, Design, Implementation, Test, Review, or Process
  Gate that should have caught it
- why existing tests and review produced a false green
- a regression check or runtime probe that fails on the old behavior
- exactly one complete `prevention_disposition`: `writeback_required` with an
  allowed Skill/workflow/spec owner and validation, or
  `no_writeback_required` with an explicit reason and evidence references

Only the acknowledged record-bound chain above can close the repair. Do not
close it when a field is missing, the disposition is a TODO, both or neither
disposition branches are present, or a writeback is invented despite sufficient
existing prevention evidence.

`verification-evidence.jsonl` may store the complete canonical, minimally
scoped and sanitized `VerificationEvidenceRow`: `acceptance_id`, `status`,
`baseline_binding`, `environment`, `steps_or_command`, `expected`, `actual`,
`evidence_refs`, `recorded_at`, `recorded_by`, and applicable correction or
retrospective artifact/control references. The reconciliation journal may store
the sanitized `ReconciliationJournalEvent` and attempt control metadata needed
for replay: positions/digests, attempt/acceptance/baseline identity,
`retrospective_artifact_ref`, exact row digest, pre/post snapshot refs,
retry/state, `accepted_append_ref`, `record_ref`, `closes_attempt_ids`, reason,
actor, and timestamp. These summary fields must not contain secrets, tokens,
PII, complete request/response bodies, user content, or a raw retrospective
payload/row. These contracts are Skill/spec/workflow policy only: they do not
authorize a new parser, schema, lifecycle state, script-level gate, or any
Trellis/Guru/CLI Python, shell, TypeScript, hook, verify, or apply change.

---

## Common Cross-Layer Mistakes

### Mistake 1: Implicit Format Assumptions

**Bad**: Assuming date format without checking

**Good**: Explicit format conversion at boundaries

### Mistake 2: Scattered Validation

**Bad**: Validating the same thing in multiple layers

**Good**: Validate once at the entry point

### Mistake 3: Leaky Abstractions

**Bad**: Component knows about database schema

**Good**: Each layer only knows its neighbors

### Mistake 4: Every Consumer Parses The Same Payload

**Bad**: A command reads JSONL events and casts fields inline:

```typescript
const thread = (ev as { thread?: string }).thread;
const labels = (ev as { labels?: string[] }).labels;
```

This looks local, but it means every consumer owns a private version of the
event contract. The next field change will update one command and miss another.

**Good**: Decode once at the event boundary, then export typed projections:

```typescript
if (!isThreadEvent(ev)) return false;
return ev.thread === filter.thread;
```

**Rule**: For append-only logs, JSON streams, RPC payloads, or config files,
create one owner for:

- event / payload type definitions
- type guards and normalization from `unknown`
- metadata projections used by UI commands
- reducers that replay state from the source of truth

Rendering code may format fields, but it must not redefine the payload contract.

---

## Checklist for Cross-Layer Features

Before implementation:

- [ ] Mapped the complete data flow
- [ ] Identified all layer boundaries
- [ ] Defined format at each boundary
- [ ] Decided where validation happens
- [ ] Identified acceptance-path triggers even when the planned diff changes
      only one layer
- [ ] Frozen one complete Acceptance Closure Matrix row for each required
      independently decidable user outcome
- [ ] Recorded an authority fingerprint and a check that fails on the known-bad
      implementation

After implementation:

- [ ] Tested with edge cases (null, empty, invalid)
- [ ] Verified error handling at each boundary
- [ ] Checked data survives round-trip
- [ ] Checked that consumers import shared decoders / projections instead of
      casting payload fields locally
- [ ] Checked that derived state points back to the source event identifier
      (`seq`, `id`, `version`) instead of inventing a second cursor
- [ ] Verified the Integration check closes the final source-to-sink outcome;
      an ordinary or local layer check is supporting evidence only
- [ ] Kept mutable runtime evidence append-only and separate from the frozen
      matrix
- [ ] Consumed one fresh, complete ClosureSpec-produced
      `AcceptanceResolution` with both snapshot refs and both open blocker sets
      intact; no consumer directly resolved or selected evidence rows

---

## Cross-Platform Template Consistency

In Trellis, command templates (e.g., `record-session.md`) exist in **multiple platforms** with identical or near-identical content. This is a cross-layer boundary.

### Checklist: After Modifying Any Command Template

- [ ] Find all platforms with the same command: `find src/templates/*/commands/trellis/ -name "<command>.*"`
- [ ] Update all platform copies (Markdown `.md` and TOML `.toml`)
- [ ] For Gemini TOML: adapt line continuations (`\\` vs `\`) and triple-quoted strings
- [ ] Run `/trellis:check-cross-layer` to verify nothing was missed

**Real-world example**: Updated `record-session.md` in Claude to use `--mode record`, but forgot iFlow, Kilo, OpenCode, and Gemini — caught by cross-layer check.

---

## Generated Runtime Template Upgrade Consistency

Some generated files are both documentation and runtime input. In Trellis,
`.trellis/workflow.md` is parsed by `get_context.py`, `workflow_phase.py`,
SessionStart filters, and per-turn hooks. Template changes must be validated
against both fresh init and upgrade paths.

### Checklist: After Modifying A Runtime-Parsed Template

- [ ] Identify every runtime parser that reads the template, not just the file
      writer that installs it
- [ ] Check whether relevant syntax lives outside obvious managed regions
      such as tag blocks
- [ ] Verify fresh `init` output and a versioned `update` scenario that writes
      the older `.trellis/.version`
- [ ] Add an upgrade regression using an older pristine template fixture, then
      assert the installed file reaches the current packaged shape
- [ ] Update the backend spec that owns the runtime contract

---

## Versioned Documentation Boundary

Versioned documentation is a cross-layer boundary: source paths, `docs.json`
version routing, and the rendered version selector must all describe the same
release line.

### Checklist: Before Editing Versioned Docs

- [ ] Identify the target release line: stable, beta, or RC
- [ ] Verify the edited MDX path matches that line:
  - stable: `docs-site/{start,advanced,...}` and `docs-site/zh/{start,advanced,...}`
  - beta: `docs-site/beta/**` and `docs-site/zh/beta/**`
  - RC: `docs-site/rc/**` and `docs-site/zh/rc/**`
- [ ] Verify `docs.json` navigation points the version label to the same paths
- [ ] Grep the opposite tree for release-line-specific terms before committing
- [ ] Treat beta content appearing under root release paths as a source-path bug,
      not a rendering bug

**Real-world example**: A beta-only task workflow change documented
`prd.md` + `design.md` + `implement.md`, task-creation consent, and Codex
mode banners under root `start/` and `advanced/` paths. The docs site then
served 0.6 beta behavior under the Release selector. The fix was to restore root
release docs, move the 0.6 content to `beta/` and `zh/beta/`, and add a grep
audit for beta markers against the root release tree.

**Real-world example**: Codex inline mode changed workflow platform markers from
`[Codex]` / `[Kilo, Antigravity, Windsurf]` to `[codex-sub-agent]` /
`[codex-inline, Kilo, Antigravity, Windsurf]`. Fresh init was correct, but
`trellis update` only merged `[workflow-state:*]` blocks and preserved stale
markers outside those blocks. Result: upgraded projects got new hook scripts
but old workflow routing, so `get_context.py --mode phase --platform codex`
could return empty Phase 2.1 detail.

---

## Mode-Detection Probe Checklist

When a CLI auto-detects a mode by probing a remote resource (e.g., checking if `index.json` exists to decide marketplace vs direct download):

### Before implementing:

- [ ] Probe runs in **ALL** code paths that use the result (interactive, `-y`, `--flag` combos)
- [ ] 404 vs transient error are distinguished — don't treat both as "not found"
- [ ] Transient errors **abort or retry**, never silently switch modes
- [ ] Shared state (caches, prefetched data) is **reset** when context changes (e.g., user switches source)
- [ ] **Shortcut paths** (e.g., `--template` skipping picker) must have the same error-handling quality as the probed path — check that downstream functions don't call catch-all wrappers

### After implementing:

- [ ] Trace every path from probe result to the mode-decision branch — no fallthrough
- [ ] External format contracts (giget URI, raw URLs) are tested or at least documented as comments
- [ ] Metadata reads consume a complete response or use a streaming parser — never parse a fixed-size prefix as full JSON
- [ ] When reconstructing a composite identifier from parsed parts, verify **all** fields are included and in the **correct position** (e.g., `provider:repo/path#ref` not `provider:repo#ref/path`)
- [ ] Verify that **action functions** called after a shortcut don't internally use the old catch-all fetch — they must use the probe-quality variant when error distinction matters

**Real-world example**: Custom registry flow had 8 bugs across 3 review rounds: (1) probe only ran in interactive mode, (2) transient errors fell through to wrong mode, (3) giget URI had `#ref` in wrong position, (4) prefetched templates leaked across source switches, (5) `--template` shortcut bypassed probe but `downloadTemplateById` internally used catch-all `fetchTemplateIndex`, turning timeouts into "Template not found".

**Real-world example**: Agent-session update hints fetched npm `latest` metadata with `response.read(4096)` and then parsed it as complete JSON. The `@mindfoldhq/trellis` package metadata exceeded 4 KB, so the JSON was truncated, parse failed silently, and the first session injection showed no update hint. Fix: read the complete response before parsing, and add a regression where `version` is followed by an 8 KB metadata tail.

---

## Cross-Platform Template Consistency

In Trellis, command templates (e.g., `record-session.md`) exist in **multiple platforms** with identical or near-identical content. This is a cross-layer boundary.

### Checklist: After Modifying Any Command Template

- [ ] Find all platforms with the same command: `find src/templates/*/commands/trellis/ -name "<command>.*"`
- [ ] Update all platform copies (Markdown `.md` and TOML `.toml`)
- [ ] For Gemini TOML: adapt line continuations (`\\` vs `\`) and triple-quoted strings
- [ ] Run `/trellis:check-cross-layer` to verify nothing was missed

**Real-world example**: Updated `record-session.md` in Claude to use `--mode record`, but forgot iFlow, Kilo, OpenCode, and Gemini — caught by cross-layer check.

---

## Generated Runtime Template Upgrade Consistency

Some generated files are both documentation and runtime input. In Trellis,
`.trellis/workflow.md` is parsed by `get_context.py`, `workflow_phase.py`,
SessionStart filters, and per-turn hooks. Template changes must be validated
against both fresh init and upgrade paths.

### Checklist: After Modifying A Runtime-Parsed Template

- [ ] Identify every runtime parser that reads the template, not just the file
  writer that installs it
- [ ] Check whether relevant syntax lives outside obvious managed regions
  such as tag blocks
- [ ] Verify fresh `init` output and a versioned `update` scenario that writes
  the older `.trellis/.version`
- [ ] Add an upgrade regression using an older pristine template fixture, then
  assert the installed file reaches the current packaged shape
- [ ] Update the backend spec that owns the runtime contract

**Real-world example**: Codex inline mode changed workflow platform markers from
`[Codex]` / `[Kilo, Antigravity, Windsurf]` to `[codex-sub-agent]` /
`[codex-inline, Kilo, Antigravity, Windsurf]`. Fresh init was correct, but
`trellis update` only merged `[workflow-state:*]` blocks and preserved stale
markers outside those blocks. Result: upgraded projects got new hook scripts
but old workflow routing, so `get_context.py --mode phase --platform codex`
could return empty Phase 2.1 detail.

---

## Mode-Detection Probe Checklist

When a CLI auto-detects a mode by probing a remote resource (e.g., checking if `index.json` exists to decide marketplace vs direct download):

### Before implementing:
- [ ] Probe runs in **ALL** code paths that use the result (interactive, `-y`, `--flag` combos)
- [ ] 404 vs transient error are distinguished — don't treat both as "not found"
- [ ] Transient errors **abort or retry**, never silently switch modes
- [ ] Shared state (caches, prefetched data) is **reset** when context changes (e.g., user switches source)
- [ ] **Shortcut paths** (e.g., `--template` skipping picker) must have the same error-handling quality as the probed path — check that downstream functions don't call catch-all wrappers

### After implementing:
- [ ] Trace every path from probe result to the mode-decision branch — no fallthrough
- [ ] External format contracts (giget URI, raw URLs) are tested or at least documented as comments
- [ ] Metadata reads consume a complete response or use a streaming parser — never parse a fixed-size prefix as full JSON
- [ ] When reconstructing a composite identifier from parsed parts, verify **all** fields are included and in the **correct position** (e.g., `provider:repo/path#ref` not `provider:repo#ref/path`)
- [ ] Verify that **action functions** called after a shortcut don't internally use the old catch-all fetch — they must use the probe-quality variant when error distinction matters

**Real-world example**: Custom registry flow had 8 bugs across 3 review rounds: (1) probe only ran in interactive mode, (2) transient errors fell through to wrong mode, (3) giget URI had `#ref` in wrong position, (4) prefetched templates leaked across source switches, (5) `--template` shortcut bypassed probe but `downloadTemplateById` internally used catch-all `fetchTemplateIndex`, turning timeouts into "Template not found".

**Real-world example**: Agent-session update hints fetched npm `latest` metadata with `response.read(4096)` and then parsed it as complete JSON. The `@mindfoldhq/trellis` package metadata exceeded 4 KB, so the JSON was truncated, parse failed silently, and the first session injection showed no update hint. Fix: read the complete response before parsing, and add a regression where `version` is followed by an 8 KB metadata tail.

---

## When to Create Flow Documentation

Create detailed flow docs when:

- Feature spans 3+ layers
- A user-visible outcome crosses boundaries even if the diff touches one layer
- An external API/schema, persistence/cache, async terminal state, or field
  transformation determines acceptance
- Multiple teams are involved
- Data format is complex
- Feature has caused bugs before

---

## Event Log / Projection Boundary

Append-only logs are cross-layer contracts. A single event travels through:

```
CLI input → event writer → events.jsonl → reader → filter → reducer → display
```

### Checklist: After Adding A New Event Kind Or Field

- [ ] Add the event kind to the central event taxonomy
- [ ] Add a typed event variant or type guard at the event layer
- [ ] Add normalization helpers for array/object fields that come from
      user input or JSON
- [ ] Keep `seq` / `id` assignment in the event writer only
- [ ] Make filters and reducers consume the typed event guard, not local casts
- [ ] Make display code consume reducer output or typed events, not raw JSON
- [ ] Add at least one regression that proves history replay and live filtering
      use the same filter model

**Real-world example**: Thread channels added `kind: "thread"`, `description`,
`context`, labels, and `lastSeq`. The first implementation replayed thread
state correctly, but several commands still re-parsed event payload fields with
local casts. The fix was to make the core event layer own `ThreadChannelEvent`
and `isThreadEvent`, make `reduceChannelMetadata` the only channel metadata
projection, and make `reduceThreads` the only thread replay reducer.
