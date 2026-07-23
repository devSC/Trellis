# Framework Source-Maintenance Detail Profile

## 1. Status and applicability

This is a task-local bootstrap review contract for:

- repository: the Trellis/Guru CLI source-maintenance checkout;
- task: `07-20-guru-runtime-acceptance-repair-continuation`;
- route/risk: `full_chain` / high;
- repository platform declaration: `guru.platform: cli`;
- implementation surface: Skill, workflow, spec, agent instruction, and
  source/template parity documents;
- forbidden surface: every Trellis/Guru/CLI Python, shell, hook, verify, apply,
  and TypeScript runtime file.

The user confirmed on 2026-07-20 that the missing CLI/framework Detail profile
is a same-goal `PROCESS_DEFECT` in the current task. The maximum necessary
planning rollback is Overview plus Detail; confirmed Requirements semantics and
their digest remain unchanged.

This file does not claim to be an installed `.trellis/spec/**` profile, does not
claim that `guru_gate.py` parses the framework taxonomy below, and does not
waive semantic review. It supplies the explicit source-maintenance review
contract needed to break the current bootstrap cycle. Permanent promotion into
repo-local spec/Skill paths remains a separately authorized pre-start action.

## 2. Source hierarchy

Reviewers use the following precedence:

1. Confirmed `prd.md` owns user-visible behavior, scope, acceptance, and the
   no-script boundary.
2. `design-package/design-main.md` owns architecture, logical owners, selected
   decisions, and chapter handoff.
3. This profile owns the task-local framework Detail taxonomy and review method.
4. Existing `.trellis/spec/cli/backend/**`,
   `.trellis/spec/cli/unit-test/**`, and `.trellis/spec/guides/**` own current
   repository conventions.
5. Current source files and their packaged consumers provide implementation and
   parity evidence.
6. Flutter/Go/H5/iOS source templates are consumer compatibility inputs only.
   They are not the installed project SSOT for this CLI repository.

No reviewer may import Flutter page, controller, repository, datasource, Dart,
DI, navigation, storage, or widget rules into this task merely because the
machine Gate falls back to Flutter taxonomy.

## 3. Framework detail types

| `detail_doc_type` | Ownership boundary | Task-local L2 status |
| --- | --- | --- |
| `evidence-contract` | Frozen acceptance rows, evidence ordering/currentness, source-to-sink closure, and reader/writer boundaries | v1 in §6.1 |
| `agent-contract` | Implement/review agent inputs, outputs, stop conditions, semantic authority, and false-green prevention | v1 in §6.2 |
| `workflow-contract` | Phase ownership, completion admission, same-goal affinity, maximum rollback, and honest capability limits | v1 in §6.3 |
| `template-parity` | Canonical source owner, tracked consumer mirrors, forbidden paths, parity checks, and rollback direction | v1 in §6.4 |

These four types are the only valid Detail types for the current task. An
unknown type or any Flutter fallback type is a P1 `OVERVIEW_DEFECT`.

## 4. Contract eight questions

Every `UNIT-*` must answer all eight questions with exact, falsifiable signals:

1. Which confirmed `BHV-NNN` and acceptance outcome does it carry?
2. What are its exact inputs, outputs, status values, and error/finding values?
3. Which artifact owns each mutable state or decision, and which artifacts are
   read-only consumers?
4. Which exact artifacts may it read or invoke, and which dependencies are
   explicitly forbidden?
5. How does every success and failure path terminate without hiding pending,
   stale, or contradictory evidence?
6. Which downstream action or phase route is emitted, and who is authorized to
   consume it?
7. Which focused success and failure checks would fail on the known bad
   behavior?
8. Which product semantics, lifecycle capabilities, scripts, schemas, and
   unrelated paths must not be invented or modified?

Answers such as "see Overview", "follow existing behavior", or "run relevant
tests" are incomplete.

## 5. Required chapter skeleton

Each chapter must contain exactly one primary `UNIT-*` and these reviewable
sections, with explicit N/A reasons where applicable:

1. Unit responsibility
2. Behavior definitions and signatures
3. Core structures/status/finding values
4. Per-behavior sequence, numbered flow, and failure table
5. State, evidence, and ownership boundary
6. UI/widget section as explicit N/A for framework-only work
7. Success and failure test mapping
8. No-fabrication list
9. Negative invariant matrix

The existing Chinese/English heading variants are acceptable when they map
unambiguously to all nine sections.

## 6. Type-specific L2 rules

### 6.1 `evidence-contract`

- The frozen Acceptance Closure Matrix and mutable evidence ledger have
  different owners; runtime evidence may not rewrite the matrix.
- Evidence ordering, snapshot/fingerprint binding, currentness, stale
  supersession, and pending/failure/pass meanings must be explicit.
- A consumer may derive a decision only from current evidence and may not
  fabricate a receipt.
- `implementation_verified` is not `runtime_acceptance_pass`; neither is
  `accepted`.
- The design must identify a deterministic check or runtime probe that fails on
  the known false-green path.

### 6.2 `agent-contract`

- Implement and review agents consume confirmed requirements, Detail, packet,
  and current evidence; they do not own product semantics.
- Runtime evidence that falsifies the planning baseline must route to the
  earliest owning defect class instead of being dismissed as packet-external.
- Ordinary workers remain packet-scoped. Missing acceptance-path checks are
  planning findings, not permission for arbitrary code expansion.
- Review must trace the accepted source-to-sink path even when the diff changes
  only one file or logical layer.
- Writer and reviewer authority, output records, stop conditions, and failure
  closure must remain distinct.

### 6.3 `workflow-contract`

- Same-goal affinity is determined by unchanged accepted outcome and external
  boundary, not by filename similarity.
- Maximum rollback is:
  `IMPLEMENT_DEFECT -> Phase 2`,
  `PROCESS_DEFECT -> current process/evidence owner, or Detail only when the
  packet/digest-bearing plan must change`,
  `DETAIL_DEFECT -> Detail`,
  `OVERVIEW_DEFECT -> Overview plus affected Detail`, and
  `REQ_BLOCKER/material change -> Requirements affected chain`.
- An environment/fixture-only failure is not a sixth product defect class. It
  remains at the current verification step, refreshes only environment/fixture
  evidence and the affected runtime probe, and must not rewrite product
  Requirements, Overview, Detail, or implementation.
- Runtime-required Full work remains active until current runtime pass; a Skill
  may stop before archive but must not claim script-level enforcement.
- Archived tasks use an honest linked repair task under the current no-script
  capability boundary.
- No new lifecycle state, reopen command, parser, digest graph, or automatic
  archive Gate may be implied.

### 6.4 `template-parity`

- Every semantic contract has one canonical source owner and an explicit list
  of tracked package consumers.
- Integration may update only declared consumer mirrors; it may not rewrite an
  ordinary source owner.
- Ignored `dist`, installed global packages, target repositories, hooks,
  scripts, and CLI runtime are never delivery sources for this task.
- Parity requires content/semantic comparison plus focused scenario checks; a
  build alone is insufficient.
- Rollback direction is consumer mirrors back to the surviving canonical source
  state, never promotion of a divergent mirror into a second SSOT.

## 7. Review preconditions

`directory_final` review starts only when:

1. `task.json` resolves to Full and the design package exists.
2. Current Requirements confirmation is still bound to the unchanged
   Requirements digest.
3. Current Overview digest has two independent clean reviews after the
   framework taxonomy correction.
4. The handoff index maps every chapter to exactly one type from §3.
5. Every referenced technical decision is selected.
6. `guru_gate.py detail` returns a structural result.
7. The reviewer explicitly records that the machine Gate does not validate the
   task-local framework taxonomy because installed CLI Detail SSOT is absent.
8. The current forbidden-path audit shows zero script/runtime changes.

Failure of items 1-5 returns to the owning planning artifact. Failure of item 6
is a structural Detail finding. Failure of items 7-8 is a P1
`PROCESS_DEFECT`; it may not be waived.

## 8. D1-D9 semantic review

For each chapter:

| Check | Required evidence | Blocking examples |
| --- | --- | --- |
| D1 skeleton | §5 sections, one primary UNIT, correct type header | Flutter fallback type, missing section |
| D2 eight questions | explicit answer and falsifiable signal for every §4 item | "see Overview", unspecified relevant tests |
| D3 trace | UNIT to BHV, owner, decision, packet, and mirror closure | ghost BHV, conflicting write owner |
| D4 dependency | positive and negative dependencies follow §2 and §6 | consumer owns source contract, mirror becomes SSOT |
| D5 granularity | numbered source-to-sink or phase flow with failure branches | labels without callers, parameters, or terminal result |
| D6 tests | success plus every declared failure path and known-bad falsifier | packet-local green with no user-outcome falsifier |
| D7 compliance | secrets/PII/domain/permission impact or explicit N/A | real credential, invented external capability |
| D8 no fabrication | signatures/statuses remain planning-level and in scope | new script schema, lifecycle command, product behavior |
| D9 deletion audit | no valid contract removed without replacement | lost failure mapping, invariant, mirror, or boundary |

Any D1-D9 P1/P2 finding blocks a clean review.

## 9. Cross-chapter and planning audit

The final reviewer must independently verify:

- `evidence-contract -> agent-contract -> workflow-contract` consumption is
  one-way and all status meanings remain identical.
- `workflow-contract -> template-parity` exposes every installed consumer
  without making the mirror an owner.
- Acceptance IDs, defect classes, maximum rollback, and runtime states match
  across all chapters.
- Four ordinary slices have disjoint mutable paths, independent commit and
  rollback value, empty ordinary dependencies unless real produced bytes are
  consumed, and focused checks only.
- Exactly one Integration slice depends on all ordinary slices, covers their
  target union, writes only its declared consumer mirrors, runs full regression,
  and audits forbidden paths.
- Every exact ordered review-context inventory is independently recomputed and
  remains at or below 262144 UTF-8 bytes.

## 10. Exit criteria

Detail is semantically clean only when:

- G1 every Overview handoff row has one existing chapter;
- G2 every UNIT answers §4 and preserves its unique owners;
- G3 success plus all failure paths have falsifiable checks;
- G4 compliance and no-script boundaries are explicit;
- G5 every UNIT contains a no-fabrication list and negative invariants;
- G6 taxonomy, chapter closure, cross-chapter vocabulary, and packet ownership
  are consistent;
- G7 all chapters have method evidence, independent planning-audit
  recomputation passes, and no thin-document pattern remains.

Two independent clean reviews must cite this profile, the unchanged
Requirements digest, the current Overview and Detail digests, the structural
Gate result, and the explicit machine-taxonomy limitation. Only then may the
user run `confirm detail`.

## 11. Permanent promotion boundary

The task-local profile is not the permanent fix. A separately explicit
pre-start authorization is required before adding or modifying repo-local
profile paths such as:

- `.trellis/spec/harness/detail/**`;
- `.trellis/spec/guides/golden-path.md`;
- `.trellis/spec/conventions/project-conventions.md`;
- `.agents/skills/cli-design-detail-review/**`.

Permanent promotion must preserve the same §2 hierarchy and §3 taxonomy, add
focused review fixtures or equivalent evidence, and remain free of all
forbidden script/CLI runtime changes. Until that promotion is implemented and
verified, the current task may use this bootstrap contract but must not report
the repository-wide profile defect as permanently fixed.
