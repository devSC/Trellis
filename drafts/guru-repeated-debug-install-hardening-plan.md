# Guru repeated-debug install hardening plan

## 结论

本计划用于修复一次反复“深挖”后才暴露出的系统性问题：实现阶段把分布式状态机、多写者状态、缓存/下载/远端权威同步当成局部 UI 或单点逻辑问题处理，导致 bug 在实现后仍然存在；Guru/Gate 配置又没有在安装后的目标仓库中强制 agent 及早升级任务、补齐状态模型、用结构化 review 记录和 spec writeback 防复发。

最适合当前架构的方案是**最小增量强化现有链路**，不是新增一套 `debug_contract`：

1. `gate-contract.json` 继续作为任务级 route/risk/commit policy 的唯一 schema owner。
2. high-risk slice packet 继续作为状态模型和 invariant 的唯一机器 SSOT。
3. `review-records/implementation-reviews.jsonl` 继续作为实现 review 的唯一结构化消费记录。
4. `commit-plan.json` / `check-commit` 继续作为提交前 staged scope、split decision、spec writeback evidence 的唯一决策入口。
5. `guru-template/**` 与 `packages/cli/src/templates/guru/**` 必须同步，确保 `guru apply` 后目标仓库真的获得新行为。

如果后续进入实现，本项必须走 full-chain 任务。它会修改 gate/schema/runtime/template/install 行为，不能按 micro/lite 或 no-task 直接实现。

## 背景

会话 `019f3c53-550b-7403-9c8d-6c4978be248b` 暴露了两类问题。

第一类是实现问题：

- 没有先建模 local/remote generated media 的状态机。
- 没有列全 writer inventory，导致本地缓存、远端权威、UI lifecycle、download timeout 等写者互相覆盖。
- 没有定义 authority matrix，V2 远端权威与本地 lifecycle state 冲突。
- 测试只覆盖局部路径，没有按 invariant 和 liveness 验证。
- cache download 没有 terminal timeout，导致 UI 可长期停在中间态。

第二类是 Guru 配置/gate 问题：

- repeated debug 和“继续深挖”没有触发早期 full-chain 升级。
- storage/cache/sync/reconcile 这类高风险状态信号没有被安装后的 target repo 稳定阻断。
- implementation review 曾因 provider/record shape 不一致落到 `MALFORMED_REVIEW_OUTPUT`。
- spec writeback 曾在 commit contract 之外，容易被 scope gate 阻断或混入无关文件。
- `guru apply` 成功不等于目标仓库配置真的生效，必须做 post-install smoke。

## 目标

1. repeated-debug/stateful/cache-sync 类任务在 intake 阶段被识别并升级到 `full_chain`。
2. high-risk stateful slice 在 implementation 前必须有机器可验证的 state model packet。
3. implementation review 必须按 state model/invariant 消费结构化证据，不能只靠 reviewer prose。
4. commit gate 必须强制 clean implementation review、staged scope 限域、split decision 和 spec writeback evidence。
5. 修改必须安装到目标仓库后生效，不能只在当前 dogfood `.trellis/` 里生效。
6. 对已有 legacy task 做兼容，不让旧任务因缺新字段突然不可操作；新任务必须 fail-closed。
7. 计划本身必须先冻结 `Invariant / Owner / Reader / Writer / Test / Install Surface` 矩阵；后续 review 必须按矩阵重跑全链路一致性，不再只检查上一轮 finding。

## 原始问题覆盖矩阵

本计划的验收对象不是“新增了若干 gate”，而是必须完整回答并阻断最初暴露的几个核心问题。后续实现完成时，下面每一行都必须有对应代码改动、测试证据和 installed target smoke；任一行缺证据，都不能宣称需求闭环。

| 原始问题 | 根因判断 | 方案内强制机制 | 实现后验收证据 |
| --- | --- | --- | --- |
| 为何实现后仍有 bug？ | agent 把 generated media/cache download 当成局部实现问题，没有在 implementation 前建立状态机、writer inventory、authority matrix、terminal/liveness model；测试只验证局部成功路径，未覆盖 timeout/cancel/remote-local 冲突。 | Phase 1 将 repeated-debug + Flutter runtime/cache/sync path 升级为 `full_chain/high`；Phase 2 要求 high-risk slice 在实现前提交合法 state model packet；packet 必须声明 writers、authorities、transitions、terminal states、liveness cases 和 invariants。 | `packet-preflight --json` 对缺 packet、缺 state model、孤儿 writer、无效 transition、不可达 terminal、缺 liveness case fail-closed；valid packet 先通过 base + state-model validator；implementation-review/commit gate 再要求每个 invariant 有结构化 evidence。 |
| “深挖”暴露当前项目配置中哪些问题？ | 当前配置没有把“反复深挖/重复失败/状态型缓存同步”上升为 workflow 风险；provider/review record/schema 之间存在漂移；spec writeback、commit scope、installed template 行为没有形成同一机器合同。 | `gate-contract.json` 增加 additive `quality_gates` / `spec_writeback` / `target_platform`；新增字段唯一 writer/accessor/consumer；Gate JSON contract / exit code / detail code 冻结；`MALFORMED_REVIEW_OUTPUT` 只用于真实 schema/provider/target malformed。 | contract validator/accessor 测试覆盖 legacy 默认、malformed fail-closed、unknown additive field round-trip；review normalization 测试区分 `IMPLEMENT_DEFECT` / `PROCESS_DEFECT` / `MALFORMED_REVIEW_OUTPUT`；commit-plan/check-commit 输出机器字段而非 prose。 |
| 如何优化当前仓库，确保安装后解决上述问题？ | 只改 dogfood `.trellis/` 或源码测试会产生假绿；`guru apply` 成功不代表 template/package/target 四表面都获得相同行为，新增 helper 也可能没进 copy list。 | Phase 5 固定 source/dogfood、template、package、installed target 四表面 smoke；`guru_preflight.py` 必须进入 `apply.sh` copy list；临时 target 必须 `git init`、packaged `trellis init`、baseline commit、packaged `trellis guru apply` 后验证。 | `sync:guru:check`、packaged `guru-bundled.test.ts`、source/template/package/target command help、target-local import/py_compile、`packet-preflight`、`slice-plan`、`implementation-review --dry-run`、`commit-plan/check-commit` 全部在 installed target 通过或按预期 fail-closed；不得手工 patch target config 伪造成功。 |
| 为何反复审查都会继续发现问题？ | 前几轮 review 是局部修补：只看上一轮 finding，未把字段 owner、gate 副作用、fixture 合法性、安装表面、legacy/new-task 兼容和原始问题本身纳入同一冻结矩阵。 | 本节矩阵 + `全链路冻结矩阵` + `Review 闭环规则` 共同成为每次 review 的必查清单；每次 review 必须重跑“原始问题覆盖、字段 owner、gate contract、四表面 smoke、fixture 合法性、当前代码事实”。 | 后续 review 输出必须逐行标记 coverage/pass/fail/not_applicable，并给出证据命令；只检查最新 finding 的 review 视为无效；Definition of Done 要求本矩阵所有行都有 deterministic check 和 installed target 证据。 |
| 如何证明最终实现完整满足需求？ | 不能靠“计划看起来很全”或单仓库测试；必须证明 intake、packet、review、commit、spec writeback、install 六段链路在目标仓库可执行。 | Phase 0-5 串成一条验收链：合同边界 -> risk intake -> state model packet -> structured implementation review -> commit/spec-writeback gate -> installed verification。 | 完成标准是同一 fixture 家族在 source/template/package/installed target 上跑通：repeated-debug intake 推荐 full-chain，缺 packet 阻断，valid state model 通过，dry-run read-only，review record 区分实现缺陷，commit gate 识别 spec-writeback/split，target install smoke 证明行为真实落位。 |

## 非目标

1. 不新增平行 `debug_contract`。
2. 不新增第二套 invariant/test evidence SSOT。
3. 不把所有出现 `cache`、`storage`、`sync` 文本的文档任务都强制 full-chain。
4. 不重写现有 `overview/detail` gate 语义。
5. 不放宽 high-risk required review。
6. 不允许 spec writeback 借口绕过 `split_required`，也不允许无关 spec 文档混入 implementation commit。
7. 第一版不为 Go/H5/iOS 开启 state model 强制 gate；这些平台在对应 harness 文档和安装 smoke 完成前保持现有 route/risk/review 行为。
8. 不在本 draft 中直接修改 runtime、template 或 task artifact。

## 当前仓库事实

现有机制已经提供可复用基础：

- `.trellis/spec/cli/backend/guru-overlay-gates.md` 已定义 `small_inline | micro_task | lite_task | full_chain` 路由、`gate-contract.json`、`intake`、`init-contract`、`check-commit`、`implementation-review` 和 route-aware finish。
- `guru-template/specs/guru-flutter-client/harness/detail/detail-structure-single-source.md` 已要求状态读写 owner、负向 invariant 和 high-risk slice invariant matrix。
- `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md` 已要求 high-risk slice packet、`invariant_ids`、negative case 和按 invariant 归档测试。
- `guru_review_record.py` 已在 packet `invariants[]` 内校验 `test_evidence` 字段类型（可为空数组），因此不得新增顶层 `tests_by_invariant`。
- `guru-template/specs/guru-flutter-client/harness/gate/gate-confirmation-model.md` 已把 `implementation-review` 定义为 check-only structured review record producer。
- 当前 state model 相关 harness 事实只覆盖 Flutter client；Go/H5/iOS workflow 文件存在，但没有同等 state model harness 约束。
- 当前仓库已有 active dirty scope，尤其是 `07-01-risk-based-gate-contract-routing` 和 `07-08-high-risk-slice-review-provider`，新计划必须与这些任务错峰或显式合并，不能直接叠加改动。
- 当前 `guru-template/overlay/apply.sh` 要求目标项目已存在 `.trellis/`，并通过显式 copy list 安装 `guru_gate.py`、`guru_risk.py`、`guru_contract.py`、`guru_review_record.py`、`guru_config_patch.py`、`guru_supervise.py`；新增 helper 必须进入该 copy list，否则 source/template/package 通过不代表 installed target 可用。
- 当前 `guru_config_patch.py` 对已有 `guru.platform` 会保留用户值并 warning，不会静默覆盖；install smoke 必须覆盖 fresh fallback 和 preexisting conflicting config 两种目标状态。
- 当前 `intake --write-contract` / `init-contract` 会基于 `default_contract()` 构造新 dict 再写入；unknown additive fields 的 round-trip 不能只交给 `write_contract()`，必须在命令级 writer 合并旧合同后验证。

## 全链路冻结矩阵

本节是后续实现和 review 的冻结基线。任何新增字段、gate 或 smoke 用例都必须落到本节矩阵；若实现时发现矩阵与代码冲突，先更新本计划和任务设计，再改 runtime。

### Invariant / Owner / Reader / Writer / Test / Install Surface

| Invariant | Owner | 唯一 Writer | Reader / Consumer | Test | Install Surface |
| --- | --- | --- | --- | --- | --- |
| repeated-debug/stateful/cache-sync 命中时必须升级 route/risk；Flutter supported 时才开启 state model required | `guru_risk.py` + `guru_gate.py intake/init-contract` | `intake --write-contract`、`init-contract` 通过 shared contract writer | `check-start`、`packet-preflight`、`slice-plan`、`commit-plan`、workflow intake 文档 | repeated-debug text+path、task-local failure history、docs-only 不误杀、Go/H5/iOS unsupported required=false | dogfood、template、package、installed target |
| `gate-contract.json` 是 route/risk/quality/spec-writeback 的机器合同，不承载具体状态机 | `guru_contract.py` | `merge_contract_update(previous, desired, writer_intent)` 后调用 `write_contract()` | `contract_quality_gates()`、`contract_spec_writeback()`、`contract_target_platform()`、`contract_state_model_supported()`、`resolve_gate_platform()` | legacy missing defaults、malformed block fail-closed、unknown additive fields command-writer round-trip | dogfood、template、package、installed target |
| high-risk stateful Flutter slice 在 implementation 前必须有合法 packet；state model 只在 packet 内 | `guru_review_record.py` + `guru_preflight.py` | `slice-packets/<unit>.json` 由 planning/implementation artifact writer 创建；gate 只读 | `packet-preflight`、`slice-plan`、`implementation-review --dry-run`、real implementation-review | base invalid、state model missing、cross-reference invalid、valid fixture self-check | dogfood、template、package、installed target |
| `packet-preflight` 是最低确定性入口，不被 planning gate、`check-start` 或 spec-writeback freshness 掩盖 | `guru_preflight.py` + `guru_gate.py` | 无持久化 writer；只输出 JSON/stdout/stderr | install smoke、agent recovery、`slice-plan`、`implementation-review --dry-run` | exit code、JSON schema、detail code、multi-packet ambiguity、stdout/stderr 边界 | dogfood、template、package、installed target |
| `implementation-review --dry-run` 解析 target/provider/packet plan 但全路径 read-only | `guru_supervise.py` + `guru_preflight.py` | 无 review-record writer；real review 才可 append record | install smoke、provider config diagnosis、agent recovery | missing/ambiguous/invalid/provider-blocked 成功和失败路径均不改 `implementation-reviews.jsonl` | dogfood、template、package、installed target |
| clean implementation review 是 commit gate 的结构化 evidence | `guru_review_record.py` + `guru_gate.py commit-plan/check-commit` | real `implementation-review` append-only 写 `review-records/implementation-reviews.jsonl` | `_implementation_review_problem()`、commit-plan/check-commit、spec-writeback record freshness | malformed vs implement defect、digest stale、required provider unsatisfied、invariant evidence missing | dogfood、template、package、installed target |
| spec writeback evidence 只信任 HEAD 中已提交 spec paths，task-local record 是 mutable evidence | `guru_gate.py commit-plan/check-commit` + `guru_contract.py` | `spec-writeback-records.jsonl` 的专用 writer / recovery command；implementation commit 不 co-stage record | commit-plan/check-commit、future finish/report | missing/stale/old-HEAD/dirty/spec path out-of-scope/record staged split_required | dogfood、template、package、installed target |
| 新 helper、CLI surface、模板 mirror 必须真实安装到 target | `guru-template/**` + `packages/cli/src/templates/guru/**` | `guru-template/overlay/apply.sh` copy list + packaged CLI build | target-installed `.trellis/scripts/guru/*` | `sync:guru:check`、package test、target-local help/import/py_compile/dry-run smoke | source、template、package、installed target |

### 新增字段唯一 writer / accessor / consumer

| 字段 | 唯一 Writer | 唯一 Accessor | Consumer |
| --- | --- | --- | --- |
| `target_platform` | `intake --write-contract`、`init-contract`，手写合同经 validator | `contract_target_platform(contract)` + `resolve_gate_platform(task_dir, explicit_platform)` | `packet-preflight`、`slice-plan`、`implementation-review --dry-run`、contract validator |
| `quality_gates.state_model_required` | repeated-debug/stateful intake writer；不由 packet 或 reviewer 改写 | `contract_quality_gates(contract)` | `contract_state_model_supported()` 前置校验、packet/state-model preflight、commit-plan explain |
| `quality_gates.state_model_platforms` | platform support writer；第一版仅 Flutter supported | `contract_state_model_supported(contract, platform)` | state model required fail-closed 判定、unsupported platform fallback |
| `quality_gates.repeated_debug_required` / `trigger_ids` | intake/risk writer；只消费 task-local structured failure history 或 text+path signal | `contract_quality_gates(contract)` | recovery explanation、commit-plan context、future analytics |
| `spec_writeback.required` / `allowed_paths` / `source_invariant_ids` / `evidence_record_required` | contract writer；full-chain repeated-debug 默认 required，lite 条件化 | `contract_spec_writeback(contract)` | commit-plan/check-commit、spec-writeback record writer、recovery command |
| `state_model.*` | slice packet artifact writer；合同和 review record 不写 | `validate_state_model(packet, required_context)` | packet-preflight、slice-plan、implementation-review preflight |
| `invariants[].test_evidence` | implementation/test artifact writer；Phase 2 只校验字段类型 | `load_packet()` + review normalization | implementation-review evidence normalization、commit evidence checks |
| `invariant_status.*` / `invariant_evidence.*` / `reviewed_target_digest` | real implementation-review record writer | `normalize_review_record()` / `_implementation_review_problem()` | commit-plan/check-commit、spec-writeback freshness |
| `spec-writeback-records.jsonl` row fields | spec-writeback record writer；record file 不进 implementation commit | shared spec-writeback freshness helper | commit-plan/check-commit |

`write_contract()` 只负责原子落盘，不负责保留调用方已经丢弃的字段。任何命令级 writer 在覆盖已有 `gate-contract.json` 前必须走 `merge_contract_update(previous, desired, writer_intent)`：只改本 writer 拥有的字段，保留未知 top-level 和未知 nested additive fields。

### Gate JSON contract / exit code / detail code

| Gate | JSON contract | Exit code | Detail code | Side effect |
| --- | --- | --- | --- | --- |
| `validate_contract` / `init-contract` / `intake --write-contract` | `gate-contract.json` v1 additive blocks；malformed present blocks fail-closed | `0` ready / `2` blocked | `CONTRACT_INVALID`、`PLATFORM_REQUIRED_FOR_STATE_MODEL`、`STATE_MODEL_UNSUPPORTED_PLATFORM` | only contract writer commands write |
| `packet-preflight --json` | fixed stdout schema: packet status、state model required、platform/source/support、provider-policy status、blocking reasons、recovery commands | `0` ready / `2` blocked | `PACKET_REQUIRED_BEFORE_IMPLEMENT`、`PACKET_AMBIGUOUS_WITHOUT_SLICE`、`PACKET_INVALID`、`PACKET_INVALID:STATE_MODEL_*` | read-only |
| `slice-plan` | slice list + same packet/state-model/provider-policy detail facts | `0` emits plan even when blocked | same helper detail code as `packet-preflight` | read-only |
| `implementation-review --dry-run` | target/provider/packet plan + config-resolved provider plan | `0` ready / `2` blocked | same packet detail code plus provider config blocked codes | read-only; must not append review record |
| real `implementation-review` | append-only structured review record | `0` clean / `2` blocked/not clean | `MALFORMED_REVIEW_OUTPUT` only for schema/provider/target malformed; `IMPLEMENT_DEFECT:*` / `PROCESS_DEFECT:*` for implementation evidence gaps | may append clean/not-clean/preflight failure record |
| `commit-plan` / `check-commit` | commit plan JSON + spec writeback freshness fields | `commit-plan`: `0` emits plan; `check-commit`: `0` allow / `2` block | `IMPLEMENTATION_REVIEW_REQUIRED`、`SPEC_WRITEBACK_REQUIRED`、`SPEC_WRITEBACK_STALE`、`SPLIT_REQUIRED` | `commit-plan --write` may write `commit-plan.json`; check is read-only |

所有 gate 的 tests 必须断言 JSON 字段和 detail code，不以人类 stderr 文案作为唯一验收。

### 四表面 smoke 冻结规则

| Surface | 证明对象 | 必跑检查 |
| --- | --- | --- |
| source / dogfood | 当前仓库 `.trellis/scripts/guru/*` 行为 | touched scripts `py_compile`、targeted verify tests、`packet-preflight --help`、`implementation-review --help` |
| template | `guru-template/overlay/verify/*` 和 specs/workflows SSOT | `sync:guru:check`、template script `py_compile`、template verify tests、helper import graph |
| package | `packages/cli/src/templates/guru/**` 打包前镜像 | `pnpm --dir packages/cli exec vitest run test/guru/guru-bundled.test.ts`、packaged-template fixture tests |
| installed target | 用户执行 packaged `trellis guru apply <platform> <target>` 后真实落位 | temp target `git init` + packaged `trellis init` baseline + `guru apply` + target-local command help/import/py_compile/dry-run/commit-plan smoke |

installed target smoke 不得手工 patch `.trellis/config.yaml` 伪造成功；fresh fallback、conflicting config、no-config negative 必须是三个独立 fixture。

### Fixture 合法性先证规则

每个 fixture 必须先证明自身合法，再用来证明 gate 行为：

1. valid packet fixture 必须先通过 base packet loader 和 state model validator；否则它只能用于 invalid fixture 测试，不能用于 green smoke。
2. invalid packet fixture 必须只破坏一个目标字段或交叉引用，避免一个 case 同时触发 base invalid、state-model invalid、planning gate failure。
3. target install fixture 必须先证明 target 是 git repo、已完成 Trellis init、baseline commit 存在、`guru apply` 成功、target-local helper 已安装。
4. config resolver fixture 必须拆成 fresh installed config fallback、preexisting conflicting `guru.platform`、no-config missing platform 三类，不能互相复用。
5. spec-writeback fixture 必须先证明 HEAD spec commit、record digest、dirty check 三者一致，再断言 implementation commit allow/split/block。

### Review 闭环规则

每次 review 必须从本节矩阵重新跑全链路一致性：

- 原始问题覆盖矩阵的每一行是否仍有实现机制、测试证据和 installed target 证据。
- 每个新增字段是否有唯一 writer、唯一 accessor、所有 consumer。
- 每个 gate 是否有 JSON contract、exit code、detail code 和 side-effect 边界。
- 每个 smoke 是否覆盖 source、template、package、installed target 四表面。
- 每个 fixture 是否先证明自身合法，再证明 gate 行为。
- 当前代码事实是否仍匹配 `apply.sh` copy list、`guru_config_patch.py` platform merge 语义、contract writer 覆盖语义和 `implementation-review --dry-run` 副作用边界。

## 架构决策

### AD-001: `gate-contract.json` 采用 v1 additive 扩展

第一版不 bump `schema_version`。原因是当前 `guru_contract.py` 的 `SCHEMA_VERSION=1` 已经服务 route/risk/commit policy；直接改为 v2 会让旧目标仓库和当前 dirty task 同时进入迁移风险。

新增字段作为 v1 additive optional blocks：

```json
{
  "target_platform": "",
  "quality_gates": {
    "state_model_required": false,
    "state_model_platforms": [],
    "state_model_reason": "",
    "repeated_debug_required": false,
    "trigger_ids": []
  },
  "spec_writeback": {
    "required": false,
    "allowed_paths": [],
    "source_invariant_ids": [],
    "evidence_record_required": false
  }
}
```

兼容规则：

- legacy contract 缺 `quality_gates` 时，normalize 为 `state_model_required=false`，不 retroactively 阻断旧任务。
- legacy contract 缺 `quality_gates.state_model_platforms` 时，normalize 为 `[]`；没有机器声明的平台 support 就等价于“不支持 state model 强制 gate”。
- legacy contract 缺 `target_platform` 时，normalize 为 `""`；只有显式 CLI `--platform` 或 installed Guru config 能补足平台来源。
- legacy contract 缺 `spec_writeback` 时，遵循现有 route-aware spec update 规则。
- 新 `intake --write-contract` 命中 repeated-debug/stateful high-risk 时必须写入这两个 blocks。
- validator 必须校验 `target_platform`、block 类型、布尔字段、数组字段、`state_model_platforms` platform id 和 `allowed_paths`，但不得因为 legacy contract 缺 block 而失败。
- `quality_gates.state_model_required=true` 是强语义，不是提示字段：新合同中它只能在 `resolve_gate_platform(...)` 可解析出平台且 `contract_state_model_supported(contract, platform)=true` 时成立；平台可来自 CLI、`target_platform` 或 fresh installed config fallback。若平台缺失或平台不在 `state_model_platforms` 内，validator / preflight 必须 fail-closed，不能把 `supported=false` 当成“跳过 required gate”。
- 只有未来需要删除或重解释现有字段时，才引入 `schema_version=2` 和显式 migration。

统一读写入口：

- `default_contract()` 写新合同时必须显式写入 `quality_gates` 和 `spec_writeback` blocks，使用 false/empty 默认值。
- `load_contract()` 可继续返回 raw dict，但所有消费方不得散落 `contract.get("quality_gates", {})` 或自行猜平台。必须通过 `contract_quality_gates(contract)`、`contract_spec_writeback(contract)`、`contract_target_platform(contract)`、`contract_state_model_supported(contract, platform)` 或等价 `normalize_contract(contract, mode="read")` accessor 读取。
- accessor 对 legacy missing block 做只读默认化；validator 对“block 存在但 malformed”的新旧合同都 fail-closed。
- `contract_state_model_supported(contract, platform)` 必须只读 `quality_gates.state_model_platforms`，返回 `platform in state_model_platforms`；所有 gate 在执行 `state_model_required` 前必须先调用该 accessor。注意：`supported=false` 只允许在 `state_model_required=false` 的平台边界下跳过 state model gate；`state_model_required=true` + `supported=false` 是 malformed contract。
- `resolve_gate_platform(task_dir, explicit_platform=None)` 是 gate/smoke 唯一平台解析入口，优先级固定为：CLI `--platform` > `gate-contract.json.target_platform` > installed `.trellis/config.yaml` / `guru apply <platform>` profile > `""`。禁止按 `target_paths` 文件名猜平台。
- 若 installed `.trellis/config.yaml` 的 `guru.platform` 与 `quality_gates.state_model_platforms` 不匹配，不得静默当作可用 fallback；preflight JSON 可以输出 `platform_source=config_conflict`，也可以输出 `platform_source=config` + `platform_supported=false`，但在 `state_model_required=true` 时必须 fail-closed，恢复命令指向显式 `--platform` 或修正 config。
- `write_contract()` 只负责原子落盘；未知字段保留由命令级 `merge_contract_update(previous, desired, writer_intent)` 负责，不得因为 `default_contract()` 覆盖旧 dict 而丢失未来字段或人工审计字段。
- `intake --write-contract` 和 `init-contract` 是唯一默认 writer；手写合同必须经过同一 validator。

必须覆盖的合同级测试：

- legacy v1 contract 缺两个 blocks 仍 validate，并经 accessor 读出 false/empty 默认。
- new default contract 包含两个 blocks。
- block 存在但 bool/list/platform/path 类型错误时 fail。
- `state_model_required=true` + `target_platform=flutter` + `state_model_platforms=["flutter"]` 通过。
- `state_model_required=true` + `target_platform=""` 或无法解析平台时 fail-closed 为 `PLATFORM_REQUIRED_FOR_STATE_MODEL`。
- `state_model_required=true` + `target_platform=go|h5|ios` + 未启用对应 `state_model_platforms` support 时合同 fail-closed，不得在 gate 中静默跳过。
- unknown additive fields 在 `load_contract()` / `write_contract()` round-trip 不丢失。
- existing contract 带 unknown top-level 或 nested additive fields 时，`intake --write-contract` / `init-contract` 通过 `merge_contract_update()` 更新 owned fields 后仍不得丢失未知字段。
- repeated-debug + Flutter runtime storage/cache path 且平台 support 已启用时，写入 `quality_gates.state_model_required=true`、`quality_gates.state_model_platforms=["flutter"]`、`quality_gates.repeated_debug_required=true`、`spec_writeback.evidence_record_required=true`。
- Go/H5/iOS legacy 或未启用 platform support 时，必须写出/保留 `state_model_required=false`；`contract_state_model_supported(...)=false` 只表示“不消费 Flutter state model gate”，不允许和 `state_model_required=true` 同时出现。
- `--platform flutter`、`target_platform=flutter`、fresh installed Flutter config 三种来源都解析为 `platform=flutter`，并在 preflight JSON 中输出对应 `platform_source`。
- preexisting conflicting `guru.platform` fixture 必须 fail-closed，不得被当作 valid installed config fallback。
- missing platform 在 `state_model_required=true` 时必须 fail closed 为 `PLATFORM_REQUIRED_FOR_STATE_MODEL`，不能默认当 Flutter，也不能默认跳过 state model。

### AD-002: state model 属于 high-risk slice packet

状态模型不进入 `gate-contract.json`，只进入 slice packet。合同只决定“是否需要 state model”；具体状态字段、writer、authority、transition、liveness 都属于被 review 的 slice 机器事实。

推荐 packet 结构：

```json
{
  "schema_version": 1,
  "slice_id": "UNIT-cache-download",
  "owner_unit": "UNIT-cache-download",
  "target_kind": "runtime",
  "target_paths": ["lib/data/datasources/media_platform_data_source_impl.dart"],
  "risk": "high",
  "risk_reasons": ["repeated_debug", "stateful_cache_merge"],
  "state_model": {
    "state_fields": [
      {
        "field": "cache_download_state",
        "owner_layer": "repository",
        "type": "enum",
        "states": ["idle", "loading", "available", "failed", "cancelled"],
        "initial": "idle"
      }
    ],
    "authorities": [
      {
        "field": "media_file",
        "sources": [
          {"source": "remote", "priority": 100},
          {"source": "local_cache", "priority": 60},
          {"source": "ui_lifecycle", "priority": 20}
        ],
        "conflict_resolution": "remote metadata owns durable availability; local lifecycle owns transient loading/failure"
      }
    ],
    "writers": [
      {
        "writer_id": "cache_download_worker",
        "owner_layer": "repository",
        "write_target": "cache_download_state",
        "trigger": "remote generated media snapshot requires local file",
        "authority_relationship": "local lifecycle writer under remote metadata authority"
      }
    ],
    "transitions": [
      {
        "from": "idle",
        "to": "loading",
        "trigger": "remote_snapshot_requires_local_file",
        "writer_id": "cache_download_worker",
        "guard": "remote metadata marks media available and local cache path is missing",
        "outcome": "transient_loading"
      },
      {
        "from": "loading",
        "to": "available",
        "trigger": "cache_file_ready",
        "writer_id": "cache_download_worker",
        "guard": "cache getFile completes before timeout",
        "outcome": "terminal_success"
      },
      {
        "from": "loading",
        "to": "failed",
        "trigger": "download_timeout",
        "writer_id": "cache_download_worker",
        "guard": "timeout elapsed before cache getFile completes",
        "outcome": "terminal_failure"
      },
      {
        "from": "loading",
        "to": "cancelled",
        "trigger": "message_disposed",
        "writer_id": "cache_download_worker",
        "guard": "UI lifecycle disposes the owning message before cache completion",
        "outcome": "terminal_cancelled"
      }
    ],
    "terminal_states": [
      {"state": "available", "kind": "success"},
      {"state": "failed", "kind": "failure", "error_type": "CacheDownloadTimeout"},
      {"state": "cancelled", "kind": "cancelled"}
    ],
    "liveness_cases": [
      {
        "case_id": "download_success",
        "trigger": "cache getFile completes",
        "terminal_state": "available",
        "invariant_id": "CACHE-DOWNLOAD-SUCCESS"
      },
      {
        "case_id": "download_timeout",
        "trigger": "cache getFile never completes",
        "terminal_state": "failed",
        "invariant_id": "CACHE-DOWNLOAD-TIMEOUT"
      },
      {
        "case_id": "download_cancelled",
        "trigger": "message disposed before cache getFile completes",
        "terminal_state": "cancelled",
        "invariant_id": "CACHE-DOWNLOAD-CANCELLED"
      }
    ],
    "side_effects": [
      {
        "effect_id": "cancel_download_timer",
        "trigger_transition": "loading->failed",
        "owner_layer": "repository",
        "idempotency": "idempotent"
      }
    ]
  },
  "invariants": [
    {
      "invariant_id": "CACHE-DOWNLOAD-SUCCESS",
      "rule": "Remote cache download must publish local availability after cache file resolution.",
      "source": "state_model.liveness_cases.download_success",
      "owner": "repository",
      "positive_case": "cache getFile returns before timeout",
      "negative_case": "remote snapshot has media but local file never resolves",
      "route_if_missing": "BLOCK_IMPLEMENTATION",
      "test_evidence": []
    },
    {
      "invariant_id": "CACHE-DOWNLOAD-TIMEOUT",
      "rule": "Remote cache download must terminate as success or typed failure.",
      "source": "state_model.liveness_cases.download_timeout",
      "owner": "repository",
      "positive_case": "cache getFile returns before timeout",
      "negative_case": "cache getFile never completes",
      "route_if_missing": "BLOCK_IMPLEMENTATION",
      "test_evidence": []
    },
    {
      "invariant_id": "CACHE-DOWNLOAD-CANCELLED",
      "rule": "Disposed media messages must cancel transient cache downloads without overwriting durable remote availability.",
      "source": "state_model.liveness_cases.download_cancelled",
      "owner": "repository",
      "positive_case": "message disposal cancels the local lifecycle writer",
      "negative_case": "disposed message later rewrites cache_download_state from a stale callback",
      "route_if_missing": "BLOCK_IMPLEMENTATION",
      "test_evidence": []
    }
  ],
  "semantic_review_provider": {
    "provider": "opposite",
    "required": true,
    "ocr": "optional"
  }
}
```

禁止新增顶层 `tests_by_invariant`。测试证据的唯一设计来源是 `invariants[].test_evidence`，review 输出里的 `invariant_evidence.<id>` 只是消费结果。

`test_evidence` 的阶段边界必须明确：

- Phase 2 pre-implementation state model gate 只要求 `invariants[].test_evidence` 字段存在且类型为 array；空数组允许通过，因为实现和验证尚未发生。
- Phase 3 implementation-review 才要求每个 passed invariant 有结构化 evidence，缺 evidence 归类为实现/流程缺陷。
- Phase 4 commit gate 通过 latest clean implementation review 和 spec-writeback record 间接强制 evidence 完整性，不在 packet preflight 阶段把空 `test_evidence` 判死。

base packet loader 与 state model gate 必须分层：

- `load_packet(task_dir, unit_id)` 继续只做 base packet schema loader：JSON、`schema_version`、非空 `target_paths`、非空 `invariants`、`semantic_review_provider`、risk/deterministic/dirty_state 等现有基础约束。
- 不修改 `load_packet()` 的签名来塞 contract/context；上下文强制规则放入 `validate_state_model(packet, required_context)`，或封装为 `load_packet_for_gate(task_dir, unit_id, require_state_model=True, reason=...)`。
- `required_context.require_state_model` 只能由 `contract_quality_gates(contract)`、route/risk intake 结果和 `contract_state_model_supported(contract, platform)` 共同得出；legacy contract 缺 `quality_gates` 时必须读成 false，不因历史 high-risk packet 自动 retroactive block。
- packet 自身 `risk_reasons` 可以作为 reviewer 提示或新 contract 写入依据，但不能绕过 contract accessor 直接让 legacy packet 进入 state model 强制失败。
- `packet-preflight`、`slice-plan`、`implementation-review --dry-run` 必须消费同一个 helper，避免三个入口给同一个坏 packet 报不同 detail code。
- `check-implementation` 只在 `check-start` 和 `task.json.status=in_progress` 已满足后复用同一 helper；它不是 deterministic packet smoke 的最低入口，也不得被要求在 planning/START_READY 缺失时输出 packet detail code。

state model 机器校验必须是元素级和交叉引用级，不只是检查数组存在：

- `state_fields[]` 每项必须有 `field`、`owner_layer`、`type`，枚举状态必须列出 `states` 和 `initial`。
- `writers[]` 每项必须有 `writer_id`、`owner_layer`、`write_target`、`trigger`、`authority_relationship`，且 `write_target` 必须引用已声明 state field。
- `authorities[]` 每项必须有 `field`、非空 `sources[]` 和 `conflict_resolution`；`sources[]` 每项必须有 `source` 和数值 `priority`。
- `transitions[]` 每项必须有 `from`、`to`、`trigger`、`writer_id`、`guard`、`outcome`；`writer_id` 必须引用已声明 writer，`from/to` 必须引用对应 state field 的合法状态。
- `terminal_states[]` 每项必须有 `state`、`kind`，并且每个 terminal state 至少被一个 transition 和一个 liveness case 触达。
- `liveness_cases[]` 每项必须有 `case_id`、`trigger`、`terminal_state`、`invariant_id`；`terminal_state` 必须引用 declared terminal state，`invariant_id` 必须引用 `invariants[].invariant_id`。
- 机器必选规则是“覆盖所有 declared terminal state”；`retry`、`remote_missing`、`local_only` 是 Flutter cache-sync harness 的领域推荐项。若某个领域推荐项对当前 slice 不适用，packet 必须在对应 invariant 或 state-model note 中写明 `not_applicable` reason，不能让 validator 和推荐 fixture 互相冲突。
- `side_effects[]` 每项必须有 `effect_id`、`trigger_transition`、`owner_layer`、`idempotency`，且 `trigger_transition` 必须能对应到 transition。

### AD-003: spec writeback 必须先提交到 HEAD

当前架构已有 `split_required`，不应为了 spec writeback 打开无关 spec/tooling 混入 implementation commit 的口子。

本计划采用**先提交 spec writeback，后 implementation commit 验证 HEAD evidence**。这里的关键边界是：被信任的是 `HEAD` 中已提交的 spec paths，不是 task-local JSONL record 自身。

- `spec_writeback.required=true` 时，implementation commit 不要求 co-stage spec 文件。
- spec update 必须先作为独立 docs/tooling/spec commit 落到当前 `HEAD`；“独立 staged pass”不能作为 implementation commit 的有效证据。
- spec commit 完成后写入 task-local mutable evidence：`.trellis/tasks/<task>/spec-writeback-records.jsonl`。该 record file 不是 implementation commit 的组成部分，也不要求随 `spec_commit` 一起提交。
- record file 可以是 dirty/uncommitted 的 task-local evidence；`check-commit` 可以读取它，但只能信任它指向的、当前 `HEAD` 已提交 spec paths。
- `check-commit` 在 implementation commit 阶段验证最新 current spec-writeback record 是否存在、是否只覆盖 `spec_writeback.allowed_paths`、是否绑定当前 clean implementation review、当前 contract 和当前 `HEAD` spec commit。
- 如果 implementation files 与 spec/task/journal/tooling 仍在同一 staged index 中，继续 `split_required`；如果 `spec-writeback-records.jsonl` 本身被 staged 到 implementation commit，也继续 `split_required`，避免自引用或 mixed-scope 提交。

推荐 evidence record：

```json
{
  "schema_version": 1,
  "record_id": "spec-writeback-20260708-cache-download-timeout",
  "route": "full_chain",
  "allowed_paths": [".trellis/spec/service/media-file-preparation.md"],
  "updated_paths": [".trellis/spec/service/media-file-preparation.md"],
  "source_invariant_ids": ["CACHE-DOWNLOAD-TIMEOUT"],
  "review_record_id": "implementation-review-...",
  "reviewed_target_digest": "sha256:...",
  "contract_digest": "sha256:...",
  "spec_commit": "HEAD commit sha containing the spec writeback",
  "source_ref": "HEAD",
  "allowed_paths_digest": "sha256:...",
  "updated_paths_digest": "sha256:...",
  "source_snapshot_digest": "sha256 of updated_paths read from spec_commit",
  "dirty_check": "clean",
  "created_at": "ISO-8601",
  "writer": "guru_gate.py spec-writeback-record"
}
```

current record 判定规则：

1. JSONL 必须可完整读取；任一非法 JSON 行都阻断，不跳过坏行。
2. 只接受最后一条同时匹配当前 `gate-contract.json.spec_writeback`、当前 clean `review_record_id`、当前 `reviewed_target_digest`、当前 `source_invariant_ids` 集合和当前 `allowed_paths` digest 的记录。
3. `updated_paths` 必须全部落在 `spec_writeback.allowed_paths` 内，且 `allowed_paths` 不能是 repo root、空字符串或宽泛通配。
4. `spec_commit` 必须等于 implementation commit 检查时的 `HEAD`，`source_ref` 必须为 `"HEAD"`，`source_snapshot_digest` 必须绑定 `spec_commit` 中 `updated_paths` 的已提交内容。
5. `updated_paths_digest` 是 normalized `updated_paths` path-set digest；`source_snapshot_digest` 是当前 `HEAD` 中 `updated_paths` 的 content snapshot digest。两者都必须重新计算并与 record 一致，且这些 spec paths 不得有 staged 或 unstaged dirty changes。
6. record file 自身不参与 `spec_commit` freshness 计算；它可以是 unstaged dirty evidence，但不得被 staged 到 implementation commit。
7. record 指向旧 `spec_commit`、spec 未提交、spec 提交后又被改脏、record 被混入 implementation staged scope、或当前 contract/review/invariant digest 不匹配，都必须阻断。
8. 找不到 current record 时，`commit-plan` / `check-commit` 必须阻断并给出 spec writeback 恢复命令。

digest 规范必须机器化，不能由 `commit-plan` / `check-commit` 各自临场拼 hash：

1. 新增或抽取一个共享 helper，例如 `spec_paths_snapshot_digest(repo_root, paths, source_ref="HEAD")`，复用 `target_snapshot_digest()` 的规范化 primitives，而不是另写简化版。
2. content snapshot digest 必须固定 domain/version prefix，例如 `guru-spec-writeback-snapshot-v1\0`；输入为 normalized repo-relative path 的稳定排序序列，并逐项写入 path、mode、type、content。
3. `source_ref=HEAD` 时只能从 Git tree 读取内容，不能从 worktree 或 index 读取；dirty worktree 由独立 `dirty_check=clean` 和 staged/unstaged path 检查阻断。
4. symlink 必须 hash link target；gitlink 必须 hash gitlink oid；删除态必须有明确 `STATE=DELETE` 编码；不支持的 mode 必须 fail-closed。
5. `allowed_paths_digest` 和 `updated_paths_digest` 使用共享 `path_set_digest(domain, paths)`：先 normalize repo-relative path，再排序，再 hash；拒绝 `""`、`.`、`*`、绝对路径和 `..` 穿越。
6. `commit-plan` 和 `check-commit` 必须调用同一 digest helper；测试必须证明 path 顺序不影响 digest、内容变化会改变 `source_snapshot_digest`、dirty worktree 不影响 `source_ref=HEAD` 的 snapshot 但会被 dirty check 阻断。

### AD-004: install smoke 默认不依赖 live LLM worker

安装 smoke 的目标是证明 packaged overlay 安装后 gate/schema/preflight 行为生效，不是证明外部 LLM provider 可用。

因此安装 smoke 默认使用 deterministic/preflight/dry-run 路径：

- `intake` 路由。
- `packet-preflight` 的 packet 缺失、base packet schema、contextual state model validation、provider policy prerequisites。`packet-preflight` 只能声明 provider policy 是否可规划，不能在未解析 supervisor config 时声称 provider plan 已 ready。
- `implementation-review --slice --dry-run` 或等价 config-resolved provider plan/preflight；dry-run 必须复用 shared packet/provider-policy preflight，再由 `guru_supervise.py` 解析当前 provider config，但不得调用 `_guru_gate_check_implementation()`，不得被 requirements/detail/overview/`START_READY` 或 `task.json.status=in_progress` 掩盖。
- `implementation-review --dry-run` 必须全路径 read-only：missing packet、ambiguous packet、invalid packet、invalid state model、provider policy/config blocked 时都不得 append `review-records/implementation-reviews.jsonl`。
- `spec-writeback-preflight` 作为逻辑边界由 `commit-plan` / `check-commit` 承担：只在提交阶段验证 spec-writeback HEAD evidence 和 split decision，不混进 `packet-preflight`。

`packet-preflight` 是 target install smoke 的最低确定性入口。它必须验证 installed contract accessor、packet existence、base packet schema、contextual state model validation、provider policy prerequisites，不启动 worker，不要求 full planning gate fixture，也不验证 spec-writeback 与 HEAD 的 freshness。`check-implementation` 可作为额外 integration 验证，但只有在另行定义 deterministic planning fixture generator 后才能进入 install smoke 的必须项。

`packet-preflight` CLI contract 必须固定，避免安装后每个表面输出不同：

```bash
python3 .trellis/scripts/guru/guru_gate.py packet-preflight <task_dir> [--slice <UNIT>] [--platform <flutter|go|h5|ios>] [--json]
```

退出码：

- `0`: ready，packet/state-model/provider-policy prerequisites 通过。
- `2`: blocked，存在 deterministic blocking reason。

`--json` stdout schema：

```json
{
  "schema_version": 1,
  "task_dir": ".trellis/tasks/fixture-repeated-debug-state-model",
  "slice_id": "UNIT-cache-download",
  "packet_required": true,
  "packet_status": "ready|missing|invalid|ambiguous|not_required",
  "state_model_required": true,
  "platform": "flutter",
  "platform_source": "cli|contract|config|config_conflict|missing",
  "platform_supported": true,
  "provider_policy_status": "ready|blocked|not_required",
  "provider_config_status": "not_checked",
  "blocking_reasons": [],
  "detail_code": "",
  "recovery_commands": []
}
```

`packet-preflight --json` 不得输出 `provider_plan_status=ready`。只有 `implementation-review --dry-run` 在 `guru_supervise.py` 读取当前 config、provider、same-provider quote 和 resolved check provider 后，才能输出 config-resolved `provider_plan_status=ready|blocked`。

多 packet task 未传 `--slice` 时必须返回 exit `2`，`detail_code=PACKET_AMBIGUOUS_WITHOUT_SLICE`，`blocking_reasons[]` 给出可选 slice id 和恢复命令。human stderr 可以存在，但 smoke 只能断言 JSON/detail fields，不断言含糊字符串。

platform 解析规则：

1. `--platform` 是最高优先级，主要给 install smoke 和跨平台 fixture 使用。
2. 没有 `--platform` 时读取 `gate-contract.json.target_platform`。
3. 合同缺字段时读取 installed `.trellis/config.yaml` 或 `guru apply <platform>` 写入的项目平台 profile。
4. installed config 与 `quality_gates.state_model_platforms` 冲突时输出 `platform_source="config_conflict"`，或输出 `platform_source="config"` 且 `platform_supported=false`；不得继续当成 config fallback ready。若 `state_model_required=true`，阻断为 platform conflict / unsupported detail code。
5. 仍无法解析时输出 `platform=""`、`platform_source="missing"`；若 `state_model_required=true`，阻断为 `PLATFORM_REQUIRED_FOR_STATE_MODEL`。
6. smoke 必须覆盖 Flutter ready、fresh installed config fallback、preexisting conflicting config fail-closed、Go/H5/iOS unsupported required=false、unsupported required=true fail-closed，以及独立 no-config fixture 的 missing platform blocked，证明 state model gate 不靠路径猜测。

完整 live worker review 留在 source repo integration 或人工端到端验证中，不作为临时 target install smoke 的最低通过条件。

命令可用性必须在四个表面同时验证：

1. dogfood copy：`.trellis/scripts/guru/guru_supervise.py implementation-review --help`。
2. template mirror：`guru-template/overlay/verify/guru_supervise.py implementation-review --help`。
3. packaged template：`packages/cli/src/templates/guru/overlay/verify/guru_supervise.py implementation-review --help`。
4. `guru apply` 后的临时 target repo：`.trellis/scripts/guru/guru_supervise.py implementation-review --help` 和 dry-run fixture。
5. 四个表面还必须暴露 `.trellis/scripts/guru/guru_gate.py packet-preflight --help`；不得只在 dogfood copy 有命令、template/package 缺命令。

`py_compile` 只能证明语法，不证明 CLI surface 一致；不得把 `py_compile` 当作命令可用性验收。

### AD-005: shared preflight helper 禁止 `guru_gate` / `guru_supervise` 互相借逻辑

`packet-preflight` 和 `implementation-review --dry-run` 都要消费 packet/provider policy，但当前代码方向是 `guru_supervise.py` import `guru_gate.py` 的 `_guru_gate_check_implementation()`。如果新增 `packet-preflight` 时让 `guru_gate.py` 反向 import `guru_supervise.py` 的 provider selection，会形成循环依赖；如果两边各写一份，会再次产生 provider-policy / provider-plan drift。

本计划采用一个低层 shared helper：

- 新增 `guru_preflight.py`，并同步到 dogfood、`guru-template/overlay/verify/`、`packages/cli/src/templates/guru/overlay/verify/`。
- `guru-template/overlay/apply.sh` 的 script copy list 必须同步加入 `guru_preflight.py`；否则 installed target 不是有效验收面。
- `guru_preflight.py` 只允许 import `guru_contract.py`、`guru_risk.py`、`guru_review_record.py` 和标准库；禁止 import `guru_gate.py` 或 `guru_supervise.py`。
- `guru_gate.py packet-preflight`、`guru_gate.py slice-plan`、`guru_supervise.py implementation-review --dry-run` 都只调用 `guru_preflight.py` 的同一 packet/state-model/provider-policy helper。
- `guru_preflight.py` 返回 provider-neutral facts：`semantic_review_provider`、`provider_policy_status`、`provider_policy_blocking_reasons`、`provider_config_status="not_checked"`、`same_provider_requires_user_quote`、`recovery_commands`。具体 worker config、current/check provider 和 spawn provider 仍由 `guru_supervise.py` 在 dry-run config resolution 或非 dry-run review 中处理。
- `implementation-review --dry-run` 必须在 `guru_supervise.py` 内把 shared helper 的 provider-neutral facts 与当前 config 合成 config-resolved dry-run plan，输出 `provider_plan_status=ready|blocked`、`current_provider`、`check_provider` 和 blocking reasons；但不得写 review record，不得调用 `_guru_gate_check_implementation()`。
- 如果未来希望 shared helper 直接返回 final provider plan，必须给 helper 显式传入 `ProviderContext(current_provider, configured_provider, same_provider_quote, platform, adversarial_enabled)`；禁止 helper 反向 import `guru_supervise.py` 偷读配置。

必须覆盖的 helper 级测试：

- dogfood/template/package 三份 `guru_preflight.py` import graph 不包含 `guru_gate` / `guru_supervise`。
- installed target `.trellis/scripts/guru/guru_preflight.py` 存在、可 `py_compile`，且 target-local `guru_gate.py` / `guru_supervise.py` import target-local helper。
- `packet-preflight --json`、`slice-plan`、`implementation-review --dry-run` 对同一 missing/ambiguous/base-invalid/state-model-invalid/provider-policy-blocked fixture 输出同一 `detail_code`。
- `packet-preflight --json` 对 provider 只输出 `provider_policy_status` 和 `provider_config_status=not_checked`；`implementation-review --dry-run` 才输出 config-resolved `provider_plan_status`。
- provider policy 变更只需改 shared helper 或 provider policy owner，不允许在 `guru_gate.py` 与 `guru_supervise.py` 各自复制分支。

## 实施前置条件

1. 新建独立 Trellis full-chain task，`route=full_chain`、`risk=high`。
2. 在实现前运行 `guru_gate.py intake --description "<本计划摘要>" --path .trellis/scripts/guru/guru_gate.py --path .trellis/scripts/guru/guru_contract.py --path .trellis/scripts/guru/guru_review_record.py --path packages/cli/src/templates/guru/overlay/verify/guru_gate.py`，确认推荐为 full-chain。
3. 当前工作树必须 clean，或在独立 worktree 中实施。本计划不得直接吸收现有 `07-01`、`07-08` 的 dirty changes。
4. `07-01-risk-based-gate-contract-routing` 和 `07-08-high-risk-slice-review-provider` 必须先完成、冻结或在新 PRD 中显式声明合并 scope。
5. 每个 phase 必须指定 DRI、review owner、不可修改范围。
6. 编辑任一 symbol 前必须按 AGENTS 跑 GitNexus impact；HIGH/CRITICAL 必须先汇报 blast radius。

## 平台边界与 DRI ownership

第一版实现范围是 **Flutter-only**。原因是原始 bug 属于 generated media/cache download/state lifecycle，当前 state model harness 文档也只在 `guru-flutter-client` 下存在。

平台 gate 规则：

1. `state_model_required=true` 只允许在 Flutter target 或显式启用 state model harness support 的平台上写入，同时必须写出 `target_platform` 和 `quality_gates.state_model_platforms`。
2. Go/H5/iOS 的 repeated-debug/stateful 信号可以继续提升 route/risk、要求 implementation review，但不得自动开启 state model required。
3. 共享 gate 代码必须通过 `resolve_gate_platform(...)` 获得平台，再通过 `contract_state_model_supported(contract, platform)` 先查平台支持，最后查 state model required；否则会把尚未具备 harness 的平台误杀。
4. 若本轮要扩展 Go/H5/iOS，必须同步更新对应 harness docs、template mirror、packaged template 和 target install smoke；否则保持非目标。

DRI 必须绑定到文件/模块，不使用抽象角色：

| Deliverable | DRI file/module | 验收责任 |
| --- | --- | --- |
| contract accessor/default/validator | `.trellis/scripts/guru/guru_contract.py`、`guru-template/overlay/verify/guru_contract.py`、`packages/cli/src/templates/guru/overlay/verify/guru_contract.py` | `target_platform`、`quality_gates` / `spec_writeback` defaults、`state_model_platforms`、`contract_target_platform`、`contract_state_model_supported`、legacy accessor、malformed block fail-closed |
| repeated-debug intake/history | `.trellis/scripts/guru/guru_risk.py` 及两个 template mirror | text+path+task-local failure history 阈值，不误杀 docs-only |
| base packet + state model validator | `.trellis/scripts/guru/guru_review_record.py` 及两个 template mirror | `load_packet` base schema 与 `validate_state_model` contextual gate 分层 |
| shared packet/provider-policy preflight helper | `.trellis/scripts/guru/guru_preflight.py`、`guru-template/overlay/verify/guru_preflight.py`、`packages/cli/src/templates/guru/overlay/verify/guru_preflight.py` | platform resolution、packet/state-model detail code、provider-neutral policy facts；禁止 import `guru_gate` / `guru_supervise` |
| packet preflight / commit-plan / check-commit | `.trellis/scripts/guru/guru_gate.py` 及两个 template mirror | deterministic preflight CLI、HEAD spec writeback freshness、split decision |
| implementation-review dry-run/preflight | `.trellis/scripts/guru/guru_supervise.py`、`guru-template/overlay/verify/guru_supervise.py`、`packages/cli/src/templates/guru/overlay/verify/guru_supervise.py` | dry-run 全路径 read-only，target/provider/packet plan 不启动 worker、不追加 record、不调用 `_guru_gate_check_implementation()` |
| install/template packaging | `guru-template/**`、`packages/cli/src/templates/guru/**`、`packages/cli/test/guru/guru-bundled.test.ts` | source/template/package/target 四表面一致 |
| Flutter harness docs | `guru-template/specs/guru-flutter-client/harness/**`、`packages/cli/src/templates/guru/specs/guru-flutter-client/harness/**` | state model packet、invariant evidence、preflight guidance |
| installed smoke tests | `packages/cli/test/guru/**` 和临时 target fixture | `guru apply` 后 deterministic preflight 行为真实生效 |

后续 `implement.md` 每个 checklist item 必须指定上表中的一个 DRI file/module，不能只写“Guru owner”。

## 计划分期

### Phase 0: schema 和合同边界

DRI: `.trellis/scripts/guru/guru_contract.py` + template/package mirrors
Review owner: Guru overlay gates reviewer
禁止范围: 不改 provider policy；不改 runtime 行为；不改 existing active task artifacts。

目标：把字段、owner、兼容策略和 gate 消费点定清楚，不先写 runtime。

改动范围：

- `.trellis/spec/cli/backend/guru-overlay-gates.md`
- `guru-template/specs/guru-flutter-client/harness/**`
- `packages/cli/src/templates/guru/specs/guru-flutter-client/harness/**`
- 后续 Trellis task 的 `prd.md/design.md/implement.md`

要求：

1. 文档明确禁止 `debug_contract`。
2. 文档明确 `gate-contract.json` v1 additive 策略。
3. 文档明确 state model 只属于 packet。
4. 文档明确 `spec-writeback-records.jsonl` 是 mutable evidence，不是新的 planning SSOT。
5. 文档明确 `tests_by_invariant` 不允许作为顶层字段。
6. 文档明确第一版 Flutter-only；Go/H5/iOS 不因本计划自动打开 `state_model_required`。
7. 文档明确 platform support 是 `target_platform` + `quality_gates.state_model_platforms` + `resolve_gate_platform` 的机器合同，不是 prose-only 约定。
8. 文档明确 shared preflight helper 的 import 方向，避免 `guru_gate.py` / `guru_supervise.py` 互相借逻辑或复制 provider 分支。
9. 文档冻结 `Invariant / Owner / Reader / Writer / Test / Install Surface` 矩阵，并要求后续 review 按矩阵全链路回扫。
10. 文档冻结新增字段唯一 writer/accessor/consumer、gate JSON contract/exit code/detail code、四表面 smoke 和 fixture 合法性先证规则。

验收：

- legacy v1 contract 缺新 blocks 时行为写清。
- new repeated-debug/high-risk contract 的 blocks 写清。
- spec writeback 必须先 committed to `HEAD`，implementation commit 只验证 HEAD evidence 的规则写清。
- Go/H5/iOS 平台边界写清并有 `resolve_gate_platform` / `contract_state_model_supported` 访问规则，且不会被 Flutter-only state model gate 误伤。
- missing platform 在 state-model-required context 下 fail closed，而不是默认 Flutter 或默认跳过。
- preexisting conflicting `guru.platform` 在 state-model-required context 下 fail closed，而不是作为 installed config fallback 假绿。
- `intake --write-contract` / `init-contract` 的 unknown additive fields command-writer round-trip 写清并进入测试。

### Phase 1: intake/risk 识别

DRI: `.trellis/scripts/guru/guru_risk.py` + template/package mirrors
Review owner: Guru gate contract owner
禁止范围: 不改 review record normalization；不改 provider selection。

目标：让 agent 在收到 repeated-debug/stateful/cache-sync 请求时先升级风险，而不是先开工。

改动范围：

- `.trellis/scripts/guru/guru_risk.py`
- `.trellis/scripts/guru/guru_gate.py`
- `guru-template/overlay/verify/guru_risk.py`
- `guru-template/overlay/verify/guru_gate.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`
- `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/tests/run_tests.sh`
- `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`

repeated-debug 阈值：

| 信号 | 行为 |
| --- | --- |
| 单次“深挖/继续调查/再查”且无 runtime/stateful path | 只加 `risk_flags.repeated_debug_observed`，不单独强制 full-chain |
| repeated-debug 文本 + Flutter runtime storage/cache/cross-layer path | `risk=high`, `route=full_chain`, `target_platform=flutter`, `state_model_required=true`, `state_model_platforms=["flutter"]` |
| 同一 Flutter task 连续 2 次 implementation/review failure | `risk=high`, `route=full_chain`, `target_platform=flutter`, `state_model_required=true`, `state_model_platforms=["flutter"]` |
| 同一 Flutter invariant 连续 fail 或同一 target path 反复修复 | `risk=high`, `route=full_chain`, `target_platform=flutter`, `state_model_required=true`, `state_model_platforms=["flutter"]` |
| Flutter 明确出现 remote/local reconcile、authority conflict、download stuck、cache lifecycle | `risk=high`, `route=full_chain`, `target_platform=flutter`, `state_model_required=true`, `state_model_platforms=["flutter"]` |
| Go/H5/iOS 出现 repeated-debug/stateful 信号但未启用平台 harness support | 可提升 `risk/route` 和 required review，但 `state_model_required=false` |

历史失败数据源：

1. 有 `task_dir` 时，优先读取 `review-records/implementation-reviews.jsonl`，按 `review_result`、`route_class`、`supervisor_failure`、`invariant_status.*`、`target_paths` 统计连续失败。
2. 其次读取 `implementation-evidence.jsonl` 和 `verification-evidence.jsonl`，只消费有明确 `unit_id`、`invariant_id`、`target_paths`、`result=failed` 的结构化行。
3. 可读取 `gate-degradations.jsonl` 作为补充信号，但 degradation 只证明曾经绕行或补偿，不单独证明 implementation failure。
4. 没有 `task_dir` 或找不到结构化历史时，只能使用文本 + path 触发规则，不得假装能判断“连续 2 次失败”。
5. 历史统计只看同一 task；跨 task 相似问题只能作为 `risk_flags.related_prior_failure_observed`，不能自动等同连续失败。

测试矩阵：

| Case | 预期 |
| --- | --- |
| `继续深挖 generated media 下载状态一直卡住` + Flutter datasource path | full_chain + repeated_debug + state_model_required |
| `深挖这个文档结构` + docs path | 不因 repeated-debug 单独 full-chain |
| `修正文案 typo` | small_inline 或 micro_task |
| docs 文件名包含 cache | 不因关键词单独 full-chain |
| Flutter runtime datasource/cache 文件变更 | full_chain |
| Flutter UI + repository 跨层变更 | full_chain |
| Flutter 同 invariant 第二次 fail | full_chain + state_model_required |
| Flutter 同 task 两条 failed implementation review record | full_chain + state_model_required |
| 无 task_dir 但描述说“第二次失败” | 不使用历史阈值，只按文本/path 判定 |
| `--commit-requested` low-risk | micro_task |
| Flutter repeated-debug stateful 命中 | full_chain + `target_platform=flutter` + `state_model_required=true` + `state_model_platforms=["flutter"]` |
| Go/H5/iOS runtime path + repeated-debug，平台 support 未启用 | full_chain 可成立，但不写 `state_model_required=true`，`contract_state_model_supported=false` |
| `state_model_required=true` 但无法解析 platform | `PLATFORM_REQUIRED_FOR_STATE_MODEL` |

GitNexus impact targets:

- `assess_intake`
- `path_high_risk_flags`
- `full_chain_packet_required`
- any new repeated-debug helper

### Phase 2: state model packet gate

DRI: `.trellis/scripts/guru/guru_review_record.py` + `.trellis/scripts/guru/guru_preflight.py` + `.trellis/scripts/guru/guru_gate.py packet-preflight` + template/package mirrors
Review owner: Flutter harness / implementation-review owner
禁止范围: 不改 `semantic_review_provider` semantics；不改 commit gate。

目标：状态机、多写者、远端/本地权威必须在实现前建模，不能靠实现后 review 补猜。

改动范围：

- `guru_review_record.py load_packet` base schema loader（签名不接 contract/context）
- `guru_review_record.py validate_state_model` 或同等 helper
- `guru_preflight.py` shared packet/state-model/provider-policy helper
- `guru_gate.py packet-preflight`
- `guru_gate.py check-implementation` integration reuse only after `START_READY + in_progress`
- `guru_gate.py slice-plan`
- `guru_risk.py full_chain_packet_required`
- Flutter harness detail/implementation specs
- verify tests

行为要求：

1. `route=full_chain` 且 `quality_gates.state_model_required=true` 时，缺 slice packet 阻断。
2. `load_packet()` 先保持 base schema fail-closed：空 `target_paths`、空 `invariants`、缺 `source` 等基础非法 packet 必须先报 base `PACKET_INVALID`，不能伪装成 state model 缺失。
3. 只有 base packet 合法且 contextual `require_state_model=true` 时，才进入 `validate_state_model()`；packet 缺 `state_model.state_fields`、`authorities`、`writers`、`transitions`、`terminal_states`、`liveness_cases` 任一关键字段时阻断。
4. `writers[]` 必须包含 writer id、owner layer、write target、trigger、authority relationship。
5. `authorities[]` 必须声明 remote/local/generated/cache/UI lifecycle 的优先级或冲突处理。
6. `transitions[]` 必须包含 from/to、trigger、writer、guard、terminal/failure outcome。
7. `liveness_cases[]` 必须覆盖所有 declared terminal state；timeout/cancel/retry/remote-missing/local-only 是 Flutter cache-sync harness 的领域推荐覆盖项，不适用时必须写 `not_applicable` reason，不能让 valid fixture 被推荐项误杀。
8. `invariants[]` 继续承载 `test_evidence`；Phase 2 只要求字段存在且为 array，允许空数组；不得新增 `tests_by_invariant`。
9. state model 校验必须做交叉引用：transition writer 必须存在，from/to 必须是合法状态，liveness invariant 必须存在，terminal states 必须可触达。
10. state model 校验只在 `contract_quality_gates(contract).state_model_required=true` 且 `contract_state_model_supported(contract, platform)=true` 时强制；如果 `state_model_required=true` 但 platform missing/unsupported，先按合同/平台错误 fail-closed，不能静默跳过；legacy high-risk packet 缺 `quality_gates` 时仍读成 `state_model_required=false`，不能被 retroactively 判死。

失败码与现有 packet code 的映射：

- 缺 packet 仍使用现有顶层 `PACKET_REQUIRED_BEFORE_IMPLEMENT`，不得改断既有恢复路径。
- packet 存在但缺 state model 时，`slice-plan.blocking_reasons[]` 和 preflight stderr 使用 `PACKET_INVALID:STATE_MODEL_REQUIRED`。
- state model 元素或交叉引用错误使用 `PACKET_INVALID:STATE_MODEL_INVALID:<detail_code>`。
- detail codes 包括 `WRITER_INVENTORY_MISSING`、`AUTHORITY_MATRIX_MISSING`、`TRANSITION_REFERENCE_INVALID`、`TERMINAL_STATE_UNREACHABLE`、`LIVENESS_CASE_MISSING`。
- `INVARIANT_TEST_EVIDENCE_MISSING` 不属于 Phase 2 state-model preflight；它只能由 Phase 3 implementation-review 或 Phase 4 commit gate 在验证实现证据时产生。
- `packet-preflight`、`slice-plan`、`implementation-review --dry-run` preflight 必须对同一坏 fixture 输出同一 detail code。
- `check-implementation` 只在另有 `START_READY + in_progress` integration fixture 时验证同一 helper；最低 target smoke 不断言它的 packet detail code。

测试矩阵补充：

| Case | 预期 |
| --- | --- |
| packet `target_paths=[]` | base packet invalid；不进入 `PACKET_INVALID:STATE_MODEL_*` |
| `quality_gates.state_model_required=true` 且无 packet | `PACKET_REQUIRED_BEFORE_IMPLEMENT` |
| base packet 合法且 `quality_gates.state_model_required=true`，packet 无 `state_model` | `PACKET_INVALID:STATE_MODEL_REQUIRED` |
| writer 缺 owner layer | `PACKET_INVALID:STATE_MODEL_INVALID:WRITER_INVENTORY_MISSING` |
| transition 引用不存在 writer | `PACKET_INVALID:STATE_MODEL_INVALID:TRANSITION_REFERENCE_INVALID` |
| liveness case 引用不存在 invariant | `PACKET_INVALID:STATE_MODEL_INVALID:LIVENESS_CASE_MISSING` |
| terminal state 未被 transition/liveness 触达 | `PACKET_INVALID:STATE_MODEL_INVALID:TERMINAL_STATE_UNREACHABLE` |
| legacy high-risk full-chain 但 contract 缺 `quality_gates` | 维持当前 packet 规则，不因 state_model retroactive block |
| 同一合法 packet 在 legacy path 读取 | `load_packet()` 通过 base schema，不要求 state model |
| 同一合法 packet 在 `state_model_required=true` context 读取 | state model 缺失或错误时阻断 |
| valid state model + `test_evidence: []` | `packet-preflight` 通过；实现证据留给 implementation-review/commit gate |
| valid state model 覆盖 success/failure/cancel terminal states 但 `retry/remote-missing/local-only` 明确 not applicable | `packet-preflight` 通过；领域推荐项不会被当成所有 slice 的硬性 terminal list |
| declared terminal state 缺 matching liveness case | `PACKET_INVALID:STATE_MODEL_INVALID:TERMINAL_STATE_UNREACHABLE` 或等价 liveness coverage detail |
| Go/H5/iOS 未启用 `state_model_platforms` support 且 `state_model_required=false` | 不因 state model 缺失阻断 |
| Go/H5/iOS 未启用 `state_model_platforms` support 但合同写出 `state_model_required=true` | contract/preflight fail-closed，不能当作 unsupported skip |

GitNexus impact targets:

- `load_packet`
- `_validate_invariant`
- any new `validate_state_model` helper
- any new `guru_preflight` helper
- `full_chain_packet_required`
- `_slice_plan_payload`
- `cmd_check_implementation`

### Phase 3: structured implementation review

DRI: `.trellis/scripts/guru/guru_supervise.py` + `.trellis/scripts/guru/guru_review_record.py` + template/package mirrors
Review owner: high-risk provider policy owner
禁止范围: 不改变 `07-08-high-risk-slice-review-provider` 已定义的 provider policy；不新增自由格式 review schema。

目标：review 不再靠自然语言“看起来覆盖了”，而是消费 packet 和 invariant evidence。

改动范围：

- `guru_supervise.py implementation-review`
- `guru_review_record.py`
- review worker prompt/skill
- `review-records/implementation-reviews.jsonl` normalization
- verify tests

行为要求：

1. supervisor 生成 canonical review skeleton，worker 只填值，不自由发明字段。
2. review record 必须包含现有 required fields：`review_provider`、`review_target`、`deterministic_checks`、`dirty_scope`、`invariant_coverage`、`reviewed_target_digest` 等。
3. 每个 packet invariant 必须有 `invariant_status.<id>`、`invariant_evidence.<id>`，`not_applicable` 必须有 `invariant_reason.<id>`。
4. 缺某 invariant evidence 时归类为 `IMPLEMENT_DEFECT` 或 `PROCESS_DEFECT`，不要一概落成 `MALFORMED_REVIEW_OUTPUT`。
5. 真正 schema/provider/target malformed 继续归类为 `MALFORMED_REVIEW_OUTPUT`。
6. provider policy 与 `semantic_review_provider` 的优先级沿用 `07-08-high-risk-slice-review-provider` 的设计。
7. `implementation-review --dry-run` 必须走同一 target resolution、shared packet/provider-policy preflight、provider config resolution 和 digest-source 计划，只是不执行 worker、不追加 record；dry-run 不能只是打印静态 help。
8. `implementation-review --dry-run` 必须绕过 `_guru_gate_check_implementation()` 和其中的 `check-start`/`task.json.status=in_progress` gate；只有真正执行 worker 并写 review record 的 review 才要求 implementation 已开始。
9. `implementation-review --dry-run` 的 missing packet、ambiguous packet、invalid packet、invalid state model、provider policy/config blocked 路径也必须 read-only；这些失败只能返回 exit/detail，不得追加 `preflight_failure_record`。
10. 真正执行 worker 的 implementation-review 失败路径可以继续追加 structured preflight failure record，用于 commit evidence/recovery；dry-run 与 real review 的副作用边界必须分开。
11. `--slice --staged` 必须在 worker-plan 创建前完成 staged target scope / digest-source 校验，避免先生成错误计划再失败。
12. `INVARIANT_TEST_EVIDENCE_MISSING` 属于 implementation-review evidence normalization 或 commit gate 的 detail code；它不得在 packet/state-model preflight 里出现。

测试矩阵：

| Case | 预期 |
| --- | --- |
| worker 少顶层字段 | MALFORMED_REVIEW_OUTPUT |
| worker 少某 invariant evidence | IMPLEMENT_DEFECT 或 PROCESS_DEFECT |
| worker 标记 invariant passed 但没有 evidence | `IMPLEMENT_DEFECT:INVARIANT_TEST_EVIDENCE_MISSING` 或等价 structured detail |
| worker 报错 provider | MALFORMED_REVIEW_OUTPUT |
| packet explicit opposite required 但 same-provider | fail closed |
| packet missing semantic provider + current policy | 按 provider policy 接受或拒绝 |
| deterministic checks fail | 不产生 required clean |
| `--dry-run` + missing packet | exit 2/detail code；`implementation-reviews.jsonl` 不存在或行数/mtime 不变 |
| `--dry-run` + ambiguous packet | exit 2/detail code；不追加 `preflight_failure_record` |
| `--dry-run` + invalid state model | exit 2/detail code；不追加 `preflight_failure_record` |
| real implementation-review + invalid packet | exit 2；可追加 structured preflight failure record |

GitNexus impact targets:

- `normalize_review_record`
- `aggregate_invariant_coverage`
- `parse_verdict_block`
- implementation-review command resolver in `guru_supervise.py`

### Phase 4: commit gate and spec writeback evidence

DRI: `.trellis/scripts/guru/guru_gate.py commit-plan/check-commit` + `.trellis/scripts/guru/guru_contract.py` + template/package mirrors
Review owner: Guru gate contract owner
禁止范围: 不放开 generic spec/tooling 混入 implementation commit；不改 task archive/finish 行为。

目标：把“这次深挖学到的防复发规则”纳入 commit contract，同时保留当前架构的 split discipline。

改动范围：

- `guru_contract.py`
- `guru_gate.py commit-plan`
- `guru_gate.py check-commit`
- `guru_gate.py` spec-writeback record reader/helper
- route-aware finish docs
- verify tests

行为要求：

1. `spec_writeback.required=true` 时，implementation commit 阶段验证 `.trellis/tasks/<task>/spec-writeback-records.jsonl` 里的 latest current record，不要求 spec 文件 co-staged。
2. `spec_writeback.allowed_paths` 必须非空且不能是 repo root。
3. spec writeback record 的 `updated_paths` 必须全部落在 allowed paths 中。
4. spec writeback record 必须同时关联 `source_invariant_ids`、`review_record_id`、`reviewed_target_digest`、`contract_digest`、`spec_commit`、`source_ref=HEAD`、`source_snapshot_digest`、`dirty_check=clean`。
5. implementation commit 检查时，record 的 `spec_commit` 必须等于当前 `HEAD`；`updated_paths` 的 normalized path-set digest 必须等于 `updated_paths_digest`，`updated_paths` 在 `HEAD` 中的 content snapshot digest 必须等于 `source_snapshot_digest`。
6. record 中的 `updated_paths` 不得有 staged 或 unstaged dirty changes；spec 未提交、提交后又被改脏、record 指向旧 HEAD 都必须 block。
7. `spec-writeback-records.jsonl` 自身可以作为 unstaged task-local evidence 存在；若它被 staged 到 implementation commit，则继续 `split_required`。
8. implementation files 与 task/spec/journal/tooling 文件同 staged index 时继续 `split_required`。
9. docs/spec-only commit 可作为 `commit_mode=docs|tooling` 独立通过，但必须不能包含 implementation files；它的结果必须先进入 `HEAD`，不能作为 staged-only evidence 被 implementation commit 使用。
10. `micro_task` 默认不因缺 spec update 阻断；`lite_task` 仅 reusable contract 命中时 conditional；`full_chain` 仍 required 或必须显式 not applicable。
11. 只读 `commit-plan` 必须把 spec-writeback 状态输出成机器字段：`spec_writeback_required`、`spec_writeback_current`、`spec_writeback_record_id`、`spec_writeback_blocking_reasons`、`spec_writeback_recovery_commands`、`spec_commit`、`source_ref`、`source_snapshot_digest`、`spec_dirty_paths`、`record_staged`。
12. `check-commit` 必须复用同一 helper，不得重新实现一份 record freshness 判断。

测试矩阵：

| Case | 预期 |
| --- | --- |
| full_chain repeated-debug 缺 spec-writeback record | block |
| record JSONL 有非法行 | block |
| record `review_record_id` 不是最新 clean review | block |
| record `reviewed_target_digest` 与最新 clean review 不同 | block |
| record `contract_digest` 与当前 contract 不同 | block |
| record `source_invariant_ids` 缺当前 required invariant | block |
| record `updated_paths` 超出 allowed paths | block |
| record `allowed_paths` 为 repo root / 空字符串 / `*` | block |
| spec writeback 未提交但 record 存在 | block |
| spec writeback 已提交且 `spec_commit=HEAD`、digest 匹配 | allow |
| `updated_paths` 顺序不同但路径集合相同 | `updated_paths_digest` 不变 |
| spec path 内容在 `HEAD` 中变化 | `source_snapshot_digest` 变化 |
| spec path worktree dirty 但 `HEAD` 内容未变 | `source_snapshot_digest` 仍按 `HEAD` 计算，同时 dirty check block |
| symlink/gitlink spec path | digest 按 mode/type/content 或 gitlink oid 稳定计算 |
| spec 提交后又产生 staged/unstaged dirty change | block |
| record 指向旧 `spec_commit` | block |
| valid record file dirty/uncommitted 但未 staged，且指向 HEAD spec paths | allow 继续评估 implementation commit |
| valid record file 被 staged 到 implementation commit | split_required |
| spec-only allowed path commit | docs/tooling commit mode 可通过，作为后续 implementation HEAD evidence |
| implementation commit + valid spec-writeback record | allow, 不 co-stage spec |
| implementation commit co-staged allowed spec | split_required |
| implementation commit co-staged unrelated spec | split_required/block |
| allowed_paths 为 `.` | block |
| lite_task 无 reusable contract | defer |
| implementation files 混 task artifact | split_required |

GitNexus impact targets:

- `default_contract`
- `validate_contract`
- `validate_commit_contract`
- `cmd_commit_plan`
- `cmd_check_commit`
- `_implementation_review_problem`
- any new `contract_quality_gates` / `contract_spec_writeback` accessors
- any new spec-writeback helper

### Phase 5: installed verification

DRI: `guru-template/**` + `packages/cli/src/templates/guru/**` + `packages/cli/test/guru/**`
Review owner: Guru bundled test owner
禁止范围: 不依赖 live LLM worker；不手工 patch target config 伪造 installer 成功。

目标：证明 `guru apply` 后目标仓库获得新 gate/schema/preflight 行为。

改动范围：

- `guru-template/**`
- `packages/cli/src/templates/guru/**`
- CLI tests/build/install smoke

source repo 验证链：

1. `pnpm --filter @devsc/trellis run sync:guru:check`
2. `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile` touched Guru scripts in source/template/dogfood copies
3. shared helper parity/import graph:
   - dogfood/template/package 三份 `guru_preflight.py` 存在
   - import graph check confirms `guru_preflight.py` does not import `guru_gate.py` or `guru_supervise.py`
   - `guru_gate.py` and `guru_supervise.py` both import/use shared preflight helper rather than duplicating packet/provider branch logic
   - `guru-template/overlay/apply.sh` script copy list includes `guru_preflight.py`
4. CLI surface parity:
   - `python3 .trellis/scripts/guru/guru_gate.py packet-preflight --help`
   - `python3 guru-template/overlay/verify/guru_gate.py packet-preflight --help`
   - `python3 packages/cli/src/templates/guru/overlay/verify/guru_gate.py packet-preflight --help`
   - `python3 .trellis/scripts/guru/guru_supervise.py implementation-review --help`
   - `python3 guru-template/overlay/verify/guru_supervise.py implementation-review --help`
   - `python3 packages/cli/src/templates/guru/overlay/verify/guru_supervise.py implementation-review --help`
5. `pnpm --dir packages/cli exec vitest run test/guru/guru-bundled.test.ts`
6. build packaged CLI
7. run packaged-template fixture tests for contract accessor defaults, platform resolution, state model validation, commit-plan/check-commit spec-writeback freshness against HEAD, shared preflight helper parity, and implementation-review dry-run command availability/read-only behavior

target fixture setup:

1. create temporary target directory and run `git init`
2. run packaged `trellis init` or an equivalent packaged init path that creates `.trellis/config.yaml` and baseline Trellis scripts
3. create and commit a baseline so staged-diff and HEAD-based spec-writeback checks are meaningful
4. run packaged `trellis guru apply flutter <target>`; do not hand-edit `.trellis/config.yaml` to fake installer success
5. assert installed command surface and helper presence:
   - `python3 .trellis/scripts/guru/guru_gate.py intake --help`
   - `python3 .trellis/scripts/guru/guru_gate.py slice-plan --help`
   - `python3 .trellis/scripts/guru/guru_gate.py packet-preflight --help`
   - `python3 .trellis/scripts/guru/guru_supervise.py implementation-review --help`
   - `python3 -m py_compile .trellis/scripts/guru/guru_preflight.py .trellis/scripts/guru/guru_gate.py .trellis/scripts/guru/guru_supervise.py`
   - import graph confirms target-local `guru_gate.py` / `guru_supervise.py` import target-local `guru_preflight.py`
6. create `.trellis/tasks/fixture-repeated-debug-state-model/task.json` with only the minimum fields required by deterministic preflight; do not require `check-start` / `START_READY` state for smoke.
7. create `gate-contract.json` with `route=full_chain`, `risk=high`, `target_platform=flutter`, `quality_gates.state_model_required=true`, `quality_gates.state_model_platforms=["flutter"]`, `spec_writeback.required=true`, concrete `spec_writeback.allowed_paths`, and Flutter platform support.
8. create runtime file path such as `lib/data/datasources/media_platform_data_source_impl.dart`
9. create staged runtime diff
10. run `packet-preflight --json --platform flutter` and assert JSON includes `platform=flutter`, `platform_source=cli`, `platform_supported=true`
11. create a variant contract with `target_platform=""` and no CLI `--platform` in the same applied target; assert fresh installed `.trellis/config.yaml` fallback resolves `platform=flutter`, `platform_source=config`, `platform_supported=true`
12. create a separate preexisting-conflict applied target where `.trellis/config.yaml` already has `guru.platform: go` before `trellis guru apply flutter`; assert no CLI and no contract `target_platform` yields `platform_source=config_conflict` or `platform_source=config` + `platform_supported=false`, not config fallback ready
13. create Go/H5/iOS contracts with explicit `target_platform=go|h5|ios`, `state_model_required=false`, and no state-model platform support; assert repeated-debug can still raise route/risk/review while `platform_supported=false` and no state-model block is enforced
14. create contradictory Go/H5/iOS contracts with `state_model_required=true` but no matching `state_model_platforms` support; assert contract/preflight fail-closed instead of silently skipping state model
15. create a separate no-config resolver negative fixture that does not run `guru apply` and does not carry `.trellis/config.yaml` `guru.platform`; with `state_model_required=true`, no CLI `--platform`, and no contract `target_platform`, assert `platform_source=missing` and `detail_code=PLATFORM_REQUIRED_FOR_STATE_MODEL`
16. first run without packet and assert `packet-preflight --json` exits `2` with `detail_code=PACKET_REQUIRED_BEFORE_IMPLEMENT`
17. before any `implementation-review --dry-run` failure smoke, record `review-records/implementation-reviews.jsonl` absence/line count/mtime
18. create invalid packets for each state-model detail code and assert `packet-preflight --json` / `slice-plan` / `implementation-review --dry-run` report the same `PACKET_INVALID:STATE_MODEL_*` mapping; failure reason must not be requirements/detail/overview/`START_READY` or spec-writeback freshness; dry-run must not create or modify `implementation-reviews.jsonl`.
19. create a base-invalid packet with `target_paths=[]` and assert it fails as base `PACKET_INVALID`, not as `PACKET_INVALID:STATE_MODEL_*`.
20. create multiple valid packet files and assert `packet-preflight --json` without `--slice` exits `2` with `detail_code=PACKET_AMBIGUOUS_WITHOUT_SLICE`; `implementation-review --dry-run` for the same ambiguity must not append record.
21. create `slice-packets/UNIT-cache-download.json` with non-empty `target_paths`, valid `state_model` covering all declared terminal states, documented not-applicable domain recommendations where needed, and `invariants[].test_evidence: []`; first assert the fixture itself passes base + state-model validation before using it for green gate behavior.
22. run `packet-preflight --json` and `slice-plan`; assert provider output is provider-policy only (`provider_policy_status`, `provider_config_status=not_checked`) and does not claim config-resolved `provider_plan_status=ready`
23. run `implementation-review --slice UNIT-cache-download --dry-run` or config-resolved provider plan/preflight equivalent and assert it resolves target/provider/packet, outputs config-resolved provider plan fields, and does not call `_guru_gate_check_implementation()`, launch worker, append record, or require `task.json.status=in_progress`
24. do not assert `check-implementation` packet detail in this minimal smoke; only add it to a separate integration fixture after `START_READY + task.json.status=in_progress`
25. only after packet/provider-policy preflight is green, run the logical `spec-writeback-preflight` via `commit-plan` / `check-commit`; first run implementation commit check without the record and assert block
26. create stale/old-HEAD/dirty spec-writeback record rows and assert block
27. create committed spec writeback in allowed path, then create valid unstaged `spec-writeback-records.jsonl` with `spec_commit=HEAD`, `source_ref=HEAD`, matching canonical `source_snapshot_digest`, and `dirty_check=clean`
28. rerun `commit-plan` / `check-commit` and assert split/allow decisions match expectations, including `split_required` if the record file itself is staged with implementation code

`check-implementation` may be added as an integration-only smoke after a separate current planning fixture generator exists. It must never be the first proof of packet/state-model gate behavior because current `check-implementation` runs `check-start` before packet preflight.

target commands:

```bash
python3 .trellis/scripts/guru/guru_gate.py intake --help
python3 .trellis/scripts/guru/guru_gate.py packet-preflight --help
python3 .trellis/scripts/guru/guru_supervise.py implementation-review --help
python3 .trellis/scripts/guru/guru_gate.py intake --description "继续深挖 generated media cache download stuck" --path lib/data/datasources/media_platform_data_source_impl.dart
python3 .trellis/scripts/guru/guru_gate.py packet-preflight .trellis/tasks/fixture-repeated-debug-state-model --slice UNIT-cache-download --platform flutter --json
python3 .trellis/scripts/guru/guru_gate.py slice-plan .trellis/tasks/fixture-repeated-debug-state-model
python3 .trellis/scripts/guru/guru_supervise.py implementation-review .trellis/tasks/fixture-repeated-debug-state-model --slice UNIT-cache-download --dry-run
python3 .trellis/scripts/guru/guru_gate.py commit-plan .trellis/tasks/fixture-repeated-debug-state-model
python3 .trellis/scripts/guru/guru_gate.py check-commit .trellis/tasks/fixture-repeated-debug-state-model
```

验收：

- target repo 的 intake 输出 full_chain。
- `packet-preflight --platform flutter --json` 输出 `platform=flutter`、`platform_source=cli`、`platform_supported=true`；同一 applied target 在 contract 缺 `target_platform` 且无 CLI override 时输出 `platform_source=config`。
- preexisting conflicting `guru.platform` applied target 不得输出 `platform_source=config` ready，必须 fail-closed 并给出修复命令。
- Go/H5/iOS 未启用 support 且 `state_model_required=false` 时输出 unsupported 且不强制 state model；若 `state_model_required=true` 却 unsupported，则合同/preflight fail-closed。
- 独立 no-config resolver negative fixture 中，`state_model_required=true` 且 platform missing 时阻断为 `PLATFORM_REQUIRED_FOR_STATE_MODEL`。
- 缺 state model packet 时 `packet-preflight` 阻断为 `PACKET_REQUIRED_BEFORE_IMPLEMENT`。
- invalid state_model 在 `packet-preflight` / `slice-plan` / `implementation-review --dry-run` 中输出一致 detail code，且不会被 requirements/detail/overview/`START_READY` 或 spec-writeback failure 掩盖。
- multi-packet 且未传 `--slice` 时 `packet-preflight --json` 输出 `PACKET_AMBIGUOUS_WITHOUT_SLICE`。
- 补 valid packet 后 `packet-preflight` / `slice-plan` 消费 state_model，且空 `test_evidence: []` 不在 Phase 2 被误杀。
- dry-run/preflight 能证明 implementation-review target/provider/packet 计划正确，`packet-preflight` 只输出 provider-policy status，`implementation-review --dry-run` 才输出 config-resolved provider plan status，且成功/失败路径都不启动 worker、不追加 review record；missing/ambiguous/invalid dry-run 不创建或修改 `implementation-reviews.jsonl`。
- 缺 spec-writeback record 时 check-commit 阻断。
- stale、old-HEAD、dirty spec-writeback record 时 check-commit 阻断。
- 有合法 current spec-writeback record 时 implementation commit 不要求 co-staged spec；record file 未 staged 可作为 mutable evidence，record file 被 staged 时 split_required。
- source/template/package drift check 通过。
- dogfood/template/package/target 四个表面的 command help、target-local helper import/py_compile 与 dry-run smoke 全部通过。

## 与现有任务的关系

本计划不得直接覆盖以下正在进行的任务：

- `.trellis/tasks/07-01-risk-based-gate-contract-routing/`
- `.trellis/tasks/07-08-high-risk-slice-review-provider/`

推荐顺序：

1. 先收敛 `07-01-risk-based-gate-contract-routing`，确保 route/gate contract 和 commit-plan 基线稳定。
2. 再收敛 `07-08-high-risk-slice-review-provider`，确保 provider policy 与 review record normalization 稳定。
3. 最后基于稳定基线创建新的 full-chain 任务实现本计划。

如果必须合并实施，必须在新任务 PRD 中显式声明继承哪些已有 BHV、哪些不改，避免同一字段被两个任务同时定义。

## 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 自动 full-chain 误伤太多任务 | 工作流不可用 | repeated-debug 阈值 + runtime path + changed files 组合判定 |
| schema 分裂 | gate 和 review 读不同字段 | 所有新字段挂 `gate-contract.json` 或 packet，不新增 `debug_contract` |
| 测试证据分裂 | review/gate 不知道读哪份 evidence | 删除顶层 `tests_by_invariant`，只用 `invariants[].test_evidence` |
| review malformed 增加 | agent 卡在格式问题而非实现问题 | supervisor 生成 canonical skeleton，worker 只填值 |
| spec writeback 与 split_required 死锁 | commit 无法通过 | spec writeback 先独立提交到 HEAD 并记录 evidence，implementation commit 只验证 HEAD record |
| spec-writeback record 自引用或混入 implementation commit | record 写在 spec commit 后导致无法同时满足 `spec_commit=HEAD` 和 clean commit | record file 定义为 task-local mutable evidence；`check-commit` 只信任 HEAD spec paths，record staged 到 implementation commit 时 `split_required` |
| stale spec writeback record 误放行 | 旧 spec evidence 被当成当前修复证据 | record 同时绑定 current contract、latest clean review、reviewed target digest、canonical allowed/updated path-set digest、source invariant set、`spec_commit=HEAD`、`source_ref=HEAD`、canonical HEAD content snapshot digest 和 dirty check |
| state model 空壳通过 | gate 看似要求状态机，实际只检查数组存在 | 元素 schema + 交叉引用校验 + invalid fixture 覆盖 |
| 推荐 packet fixture 自身非法 | 文档示例误导实现和测试，导致 smoke 只能证明坏 fixture 被挡 | 示例 transition/liveness 必须触达所有 terminal state；Phase 2 允许空 `test_evidence`，证据完整性放到 Phase 3/4 |
| command surface drift | dogfood/template/package/target 行为不一致 | 四表面 `implementation-review --help` / dry-run smoke + `sync:guru:check` |
| `packet-preflight` CLI 各表面语义不一致 | smoke 只能 grep 文案，无法证明安装行为 | 固定 args、exit code、JSON schema、multi-packet `PACKET_AMBIGUOUS_WITHOUT_SLICE` 和 stdout/stderr 边界 |
| 平台来源不确定 | Flutter gate 可能失效，或 Go/H5/iOS 被误杀 | `--platform`、`target_platform`、installed config 的固定优先级 + `platform_source` JSON + applied-target config fallback smoke + 独立 no-config missing platform fail-closed |
| installed config 预置了冲突 `guru.platform` | `guru apply flutter` 后 fallback 读到旧平台，导致 Flutter gate 假失败或假跳过 | preexisting-conflict target fixture；`platform_source=config_conflict` 或 `platform_source=config` + `platform_supported=false` 的 blocked state；显式 `--platform` 可恢复 |
| `check-implementation` 抢先 `check-start` 掩盖 packet detail | smoke 误把 START_READY failure 当成 state model gate 行为 | 最低 smoke 只断言 `packet-preflight`/`slice-plan`/dry-run；`check-implementation` 仅在 `START_READY + in_progress` integration fixture 中验证 |
| dry-run 失败路径污染 review records | invalid packet smoke 生成 stale/malformed implementation review evidence | dry-run 成功/失败全路径 read-only；missing/ambiguous/invalid fixture 断言 `implementation-reviews.jsonl` 行数/mtime 不变 |
| shared provider preflight 出现循环 import 或复制逻辑 | `guru_gate.py` 与 `guru_supervise.py` provider 决策再次漂移 | 新增低层 `guru_preflight.py`；禁止 import `guru_gate`/`guru_supervise`；`packet-preflight` 只输出 provider-policy status，`implementation-review --dry-run` 负责 config-resolved provider plan |
| target smoke 被 planning gate 或 spec-writeback gate 误挡 | 误把 unrelated failure 当成 state model gate 生效 | target smoke 以 `packet-preflight` 为最低入口，spec-writeback 只在 `commit-plan`/`check-commit` 阶段验证；`check-implementation` 只做另有 planning fixture generator 的 integration |
| 只改 dogfood 不进安装包 | 下游安装无效 | `sync:guru:check` + packaged CLI build + temp target install smoke |
| 新 helper 未进入 `apply.sh` copy list | source/template/package 都绿，但 installed target import 失败 | `apply.sh` copy list 纳入 `guru_preflight.py`；target-local helper presence/import/py_compile smoke |
| fixture 自身非法 | green smoke 证明的是坏 fixture 被拦，不是 gate 正确 | fixture 合法性先证：valid fixture 先过 base + state-model validator；invalid fixture 单点破坏 |
| legacy task 被新 gate 判死 | 旧任务无法推进 | legacy 缺字段 normalize 为默认 false，新任务 fail-closed |
| live LLM worker 影响 install smoke | 安装测试不稳定 | smoke 使用 deterministic/preflight/dry-run，live worker 另设 integration |
| 非 Flutter 平台被误杀或误放行 | Go/H5/iOS 尚无 state model harness 却被强制阻断，或 `state_model_required=true` 被 unsupported skip 静默放行 | `quality_gates.state_model_platforms` + `contract_state_model_supported` 作为机器合同；未启用 support 时只能在 `state_model_required=false` 下提升 route/risk/review，矛盾合同 fail-closed |

## Definition of Done

1. 没有新增 `debug_contract` 或第二套 invariant/test evidence SSOT。
2. 原始问题覆盖矩阵的每一行都有落地机制、deterministic test 和 installed target smoke 证据；缺任一证据时不得宣称“完整满足需求”。
3. `gate-contract.json` v1 additive 扩展被 validator/default writer/accessor 覆盖，legacy 缺字段不阻断，存在但 malformed 的 block fail-closed；`target_platform`、`quality_gates.state_model_platforms`、`resolve_gate_platform` 和 `contract_state_model_supported` 是 state model 平台边界的机器合同；命令级 writer 通过 `merge_contract_update()` 保留 unknown additive fields。
4. repeated-debug/stateful/cache-sync intake 能按阈值推荐 `full_chain`，历史阈值只消费明确 task-local 结构化 failure records，纯 docs/text 不误杀。
5. Flutter high-risk stateful slice 缺 state model packet 会在 implementation 前阻断；Go/H5/iOS 未启用 `state_model_platforms` support 且 `state_model_required=false` 时不因 state model 缺失阻断；若 `state_model_required=true` 却 unsupported，则合同/preflight fail-closed。
6. state model 做元素级 schema 和交叉引用校验；空壳数组、孤儿 writer、无效 transition、不可达 terminal state、缺 liveness case 都会 fail。
7. packet fixture 覆盖所有 declared terminal states；success/failure/cancel terminal transitions 通过，Flutter cache-sync 领域推荐项若不适用必须有 `not_applicable` reason；Phase 2 允许空 `test_evidence: []`，`INVARIANT_TEST_EVIDENCE_MISSING` 只在 implementation-review/commit gate 阶段出现。
8. shared preflight helper 在 dogfood/template/package/installed target 中同步，且 `guru_preflight.py` 不 import `guru_gate.py` / `guru_supervise.py`；`packet-preflight`、`slice-plan`、`implementation-review --dry-run` 共用同一 detail-code helper，`apply.sh` copy list 和 target-local import/py_compile smoke 证明安装后可用。
9. implementation review 按 packet invariants 消费结构化 evidence，dry-run 走同一 target/provider-policy/packet preflight 并在 `guru_supervise.py` 解析 config-resolved provider plan，但绕过 `_guru_gate_check_implementation()` / `check-start`，不启动 worker、不追加 record；missing/ambiguous/invalid dry-run 失败路径也不写 `implementation-reviews.jsonl`。
10. `MALFORMED_REVIEW_OUTPUT` 只用于结构/schema/provider/target 真实 malformed，不吞掉实现缺陷。
11. spec writeback 通过 `.trellis/tasks/<task>/spec-writeback-records.jsonl` 限域，并绑定 current contract、latest clean review、reviewed target digest、canonical allowed/updated path-set digest、source invariant set、`spec_commit=HEAD`、`source_ref=HEAD` 和 canonical HEAD content snapshot digest；record file 是 mutable evidence，未提交/dirty/old-HEAD spec、record staged 到 implementation commit 都阻断或 split_required。
12. `packet-preflight` CLI 的 args、exit code、JSON schema、multi-packet 行为、platform resolution、stdout/stderr 边界在 dogfood/template/package/target 四表面一致。
13. source/template/package mirror 全部同步，且 dogfood/template/package/target 四表面 command surface 一致。
14. 临时目标 repo `guru apply` 后 deterministic `packet-preflight` / dry-run smoke 证明新 gate 行为生效；applied target 覆盖 CLI platform override、fresh installed config fallback、preexisting config conflict fail-closed，独立 no-config fixture 覆盖 missing platform fail-closed；target smoke 不依赖 `check-start`，不把 requirements/detail/overview/`START_READY` 或 spec-writeback failure 误当成 state model gate 成功；`check-implementation` 只在另有 started-task integration fixture 中验证。
15. valid fixture 先证明自身合法，再证明 gate 行为；invalid fixture 单点破坏，不能用多重失败 fixture 证明 detail-code contract。
16. 后续每次 review 按冻结矩阵重跑原始问题覆盖、字段 owner、gate contract、四表面 smoke、fixture 合法性和当前代码事实，不再只检查上一轮 finding。
17. 执行前已创建并激活 full-chain Trellis task，且 GitNexus impact/detect_changes 按 phase impact matrix 执行。

## 建议的后续实施任务标题

`Harden Guru repeated-debug state-model gates after install`

建议任务类型：

- `route=full_chain`
- `risk=high`
- 主要 owner: CLI backend / Guru overlay gates
- 需要 sub-agent review: yes
