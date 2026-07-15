# M3 Official Custom And Template Cutover Proof

Status: **candidate complete** for official Trellis `0.6.7` Custom resolution and the self-use Custom overlay lifecycle. This is not a production-readiness or hostile-local-bundle claim.

Recorded at: `2026-07-15T14:18:45+08:00`

Exact current Guru candidate digest: `1bddfb3af654adef0dccae0839201d3e4ffa7d80e5617ae28761c6a0b58aa917`

Exact Custom lifecycle proof digest: `4d0957a42175c6422f59eeaf410fda030ab26f2453e89576679634f1ab135532`

## Scope And Deletion Decision

M3 used the official Trellis registry, workflow and configuration surfaces plus the existing reversible Custom overlay. It did not add a Template resolver, Marketplace engine, ExtensionManager, WAL, trusted reviewer identity, or a second lifecycle state store.

The existing `guru-template/index.json` is the official resolver manifest. Because Trellis `0.6.7` resolves the current typed spec and workflow entries directly, M3 did not create a second cutover manifest.

The only new lifecycle implementation surface is:

```text
guru-template/overlay/README.md
guru-template/overlay/apply.sh
guru-template/overlay/tests/apply_test.sh
```

No M3 change exists under `packages/cli/src/**`, `packages/core/**`, `.trellis/scripts/guru/**`, or the task-local bootstrap history.

## Official Cutover Mapping

| Concern | Source authority | Official or Custom destination | Resolution and ownership |
| --- | --- | --- | --- |
| Flutter spec | `guru-template/specs/guru-flutter-client` | `.trellis/spec/**` | Official `trellis init --registry ... --template guru-flutter-client` from `index.json` `type=spec` |
| Go spec | `guru-template/specs/guru-go-backend` | `.trellis/spec/**` | Official `--template guru-go-backend` |
| H5 spec | `guru-template/specs/guru-h5-web` | `.trellis/spec/**` | Official `--template guru-h5-web` |
| iOS spec | `guru-template/specs/guru-ios-native` | `.trellis/spec/**` | Official `--template guru-ios-native` |
| Four workflows | `guru-template/workflows/*.md` | `.trellis/workflow.md` | Official `--workflow-source ... --workflow <guru-client|guru-go|guru-h5|guru-ios>` |
| Project config | tracked `.trellis/config.yaml` | official lifecycle hooks | Official `after_create` and `after_start`; unsupported blocking `before_start` is not falsely claimed |
| Delivery policy, Gate, hooks and skills | `guru-template/overlay/**` | project-local Custom assets | `apply.sh`; High-risk writable start remains `guru_task.py start`, while direct official start is advisory evidence |
| Lifecycle and rollback | external schema-v2 rollback bundle | `plan/apply/status/verify/upgrade/unapply` | existing preimage, managed-assets and exact CAS ownership; no WAL |

Official references used by the mapping:

- `https://docs.trytrellis.app/advanced/custom-workflow`
- `https://docs.trytrellis.app/advanced/custom-spec-template-marketplace`
- `https://docs.trytrellis.app/advanced/configuration`

## User Lifecycle Contract

| Operation | Mutation | Result contract |
| --- | --- | --- |
| `--plan` | none | validates target, platform, source inputs and optional rollback location, then reports `status=ready` |
| apply | target plus new external bundle | saves preimage before target writes and publishes `applied` only after final exact CAS |
| `--status` | none | reports `installed-current`, `drifted`, or `not-applied` |
| `--verify` | none | returns zero only for a current applied receipt; drift, tamper and incomplete apply return nonzero |
| `--upgrade` | target plus a required fresh external bundle | reuses apply and records the immediate pre-upgrade state |
| `--unapply` | owned target assets plus receipt state | restores the bundle-owned pre-state and preserves unrelated user work |

`prepared` is not treated as `not-applied`. A failed apply can retain partial target writes when recovery becomes `manual_required`; both status and verify therefore report `drifted`, verify is nonzero, and neither command mutates target or bundle.

## Official Trellis Evidence

The current post-review Guru candidate was served from a one-run hermetic HTTPS Git fixture and installed by the exact official package:

```text
@mindfoldhq/trellis 0.6.7
fixture commit 7146b4355dcafae6201a7b05d69226825684a665
fixture tag guru-candidate-7146b4355dca-51468b999260
candidate/reclone digest 1bddfb3af654adef0dccae0839201d3e4ffa7d80e5617ae28761c6a0b58aa917
```

Command and result:

```text
bash guru-template/overlay/tests/official_067_e2e.sh --catalog

OFFICIAL_PACKAGE_OK name=@mindfoldhq/trellis version=0.6.7
OFFICIAL_STACK_OK spec=guru-flutter-client workflow=guru-client
OFFICIAL_STACK_OK spec=guru-go-backend workflow=guru-go
OFFICIAL_STACK_OK spec=guru-h5-web workflow=guru-h5
OFFICIAL_STACK_OK spec=guru-ios-native workflow=guru-ios
OFFICIAL_RAW_FALLBACK_REJECTED raw_rc=0
OFFICIAL_067_CATALOG_OK
HERMETIC_HTTPS_GIT_OK requests=113
```

The negative fixture is important: official CLI raw exit `0` with a blank-template fallback is normalized to failure rather than accepted as an installed Guru stack.

Catalog resolver regression:

```text
python3 -m unittest discover \
  -s guru-template/overlay/verify/tests \
  -p 'test_guru_catalog.py' -v

18 passed / 0 failed
```

## Lifecycle Evidence

After one Codex-only semantic review and its single repair batch:

```text
bash guru-template/overlay/tests/apply_test.sh
120 passed / 0 failed
```

The executable suite proves:

```text
plan target/bundle byte-read-only
status missing receipt -> not-applied
status current applied receipt -> installed-current
status managed drift/tamper/prepared manual_required -> drifted
verify current -> zero
verify drift/tamper/prepared manual_required -> nonzero
upgrade without a fresh bundle -> exit 2 before mutation
apply -> upgrade -> unapply -> exact immediate pre-upgrade snapshot
unrelated user config/conventions/files and .git preserved
docs/code/tests consistency negative fixture blocked
Codex plan/event allowed; Claude plan/event rejected
```

Static checks:

```text
bash -n guru-template/overlay/apply.sh                         PASS
bash -n guru-template/overlay/tests/apply_test.sh              PASS
git diff HEAD --check -- <three lifecycle paths>               PASS
packages/cli/src/**                                            zero diff
packages/core/**                                               zero diff
.trellis/scripts/guru/**                                       zero diff
task-local bootstrap history                                   zero diff
```

## Codex Review

Review provider: `codex`.

Claude invocation or review in M3: `0`.

The single bounded semantic review found one acceptance blocker:

```text
HIGH: prepared/manual_required rollback bundle was reported as not-applied
```

It was repaired as one batch in the same three owned paths. The final contract reports incomplete or manual-recovery state as `drifted`; the new regression proves status rc `0`, verify nonzero, and byte-identical target/bundle before and after both read-only operations. The reviewer found the remaining M3 invariants clean and made no independence or trusted-reviewer claim.

## Exact Digests And Index Boundary

The lifecycle proof digest uses domain `m3-custom-lifecycle-v1` and length-prefixed path and byte fields in this order:

```text
guru-template/overlay/README.md
guru-template/overlay/apply.sh
guru-template/overlay/tests/apply_test.sh
```

Per-file SHA-256:

```text
README.md      327a8c56999d084e1163480f001421d7625d2909626f3248cb9d3fccc67964e4
apply.sh       71e1f91949d66f421a38052ea40d2f028cc0ea7252becf10a3aa135b3d337d06
apply_test.sh  24c5799a7e8a0116886c28a2c5bfdbe465bab66f05568b165313ce49209badf4
```

The shared real index was not modified by M3 validation or review. The validation-window staged diff digest remained:

```text
bd5044eb72caad355a77cc96dfedcf021c73fac3df497c75bcef91cf1fb7d3f8
```

The current index contains 16 pre-existing staged paths and tree `aaf6e701d74cec08ff30e770060b1a6f41251a66`; M3 does not claim those paths as its own and did not stage or unstage them.

## Decision

M3 is candidate complete:

- official Trellis `0.6.7` resolves and installs all four typed spec/workflow stacks from the current Custom source;
- raw blank fallback is rejected;
- project configuration uses only official supported lifecycle hooks and truthfully compensates for the missing blocking `before_start` hook;
- the user-visible Custom lifecycle is read-only where promised and reversible where mutating;
- upgrade requires a fresh external rollback bundle and rolls back to the immediate pre-upgrade state;
- docs, code and tests agree;
- Core-zero and Codex-only boundaries remain true.

M4 now owns final repository-wide consistency, hardened status, traceability/spec synchronization, proportional final verification, final Codex check-only review, and commit readback. Archive/finish and push remain outside current authorization.
