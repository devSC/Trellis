# Harden Guru runtime acceptance and Full repair continuation

## Goal

在不降低 Full 任务完成度的前提下，解决两类系统性问题：

1. 在实现前和实现后证明用户可见验收路径真正闭合，降低“测试与 Review 全绿，但用户实际运行仍失败”的概率。
2. 当用户反馈同一验收目标仍失败时，按缺陷所属的最高上游层级继续修复，只回退必要阶段，不默认重新执行 Requirements、Overview、Detail、双 Review 和确认全链路。

本任务及其后续实现不得修改任何 Trellis 自身脚本文件。

## User Value

- 用户不再为同一目标的实现缺陷重复支付完整 Full 需求与设计流程的时间和 token 成本。
- “完成”不再只代表静态检查和局部测试通过，而是明确区分技术验证、运行验收待定、运行验收失败和运行验收通过。
- 真实运行结果可以推翻错误或不完整的实现假设，并被路由到正确的需求、概要、详细设计、实现或流程层修复。
- 修复仍保留 Full 的风险标准、影响范围审查、回归测试和最终用户复验，不以缩短流程为由降低质量。

## Confirmed Facts

### Session evidence

会话 `019f666f-832a-7eb2-a460-abdcef26a649` 暴露了完整失败链：

- 局部补丁曾以 `52/52 passed` 和 `COMMIT_READY` 收口。
- 用户实际运行后反馈：接口已正确返回，但 Character Chat 仍显示 loading；再次修复后仍“不显示”。
- 最终根因是 `chats:detail` 已返回结构化 `userRole`，客户端仍只读取旧顶层 `userRoleCardId`，形成 `DTO 丢字段 -> Repository absent -> UseCase unresolved -> Controller loading`。
- 测试覆盖了角色卡 list/profile Repository 行为，却没有覆盖或可证伪 `detail -> DTO -> Repository -> UseCase -> Controller -> UI label` 的用户可见路径。
- 运行失败后，任务 Authority 和 Full Gate 使修复重新进入设计链；会话最终只取得 Overview clean，没有交付生产修复、完整回归和用户复验。

详细证据摘要见 `research/current-gaps.md`。

### Current process facts

- `trellis-implement` 通用 agent 合同没有强制 Acceptance Closure Matrix 或 runtime acceptance receipt。
- `trellis-check` 仅在改动触及 3+ 层时检查跨层 data flow；但单层 DTO/解析改动也可能决定完整用户行为。
- Full/high Flutter writer 只能修改 packet 目标并运行 packet 已声明 checks；错误或不完整 packet 会形成自洽的局部绿灯。
- Flutter reviewer 把 requirement/design/packet 当作行级权威，并限制未声明测试和审查范围；当前没有明确规定真实运行失败应使错误 SSOT 失效并上游路由。
- `trellis-finish-work` 在常规 dirty-path 检查后直接 archive，没有检查 runtime acceptance pending/failure。
- 当前无 `task.py reopen`，也无 archived Full baseline 的机器级继承。
- 修改 digest-bearing Requirement/Overview/Detail 产物会使现有下游 Review/确认失效；不修改这些产物时，现有证据可继续按其绑定规则复用。

## Terms

### Same Acceptance Goal

用户反馈的失败仍属于已确认的同一个 BHV/AC/用户结果，没有新增产品行为、扩大权限/数据边界或改变外部合同。它是 repair continuation 的任务亲和边界，不等于“文件相同”或“报错文案相似”。

### Acceptance Closure Matrix

在 Detail/`implement.md` 冻结的验收闭合合同。它把每个用户可见验收目标映射到入口、外部/本地权威、跨层转换、终态、正负向可证伪检查和 runtime probe，防止只验证局部改动。

### Runtime Acceptance

在目标运行环境中执行已声明用户路径后获得的结果。它可以由 agent 自动化、QA、开发者或用户执行，但必须记录环境、步骤/命令、预期、实际、证据和结论。

`runtime_acceptance_required=true` 是写在 `prd.md`、Detail 或 `implement.md` 的规划标记，不是新增的 `task.json`、`gate-contract.json` 或脚本 schema 字段。

### Full Repair Continuation

同一活动 Full 任务在 runtime acceptance failure 后的延续模式。它保留原任务基线，先分类缺陷，再只回退到最高必要层级，并使受影响的证据失效。

### Maximum Rollback Level

修复所需的最高上游层级。缺陷分类越上游，回退范围越大；不得因实现 Bug 自动回到 Requirements，也不得把真实需求变化伪装成实现修复。

## Behavior Specifications

### BHV-001 Runtime-required Full completion

**Given** 一个 Full 任务在 PRD、Detail 或 `implement.md` 中声明 `runtime_acceptance_required=true`，且静态检查、测试和实现 Review 已通过

**When** 任一 required Acceptance Closure Matrix 行仍缺少 current `runtime_acceptance_pass`，或者存在更新的 pending/failure evidence

**Then** 流程只能报告 `implementation_verified` 或 `runtime_acceptance_pending/failure`，任务保持活动，`trellis-finish-work` 必须停止在 archive 前，并指出缺失的 acceptance row 和下一条 runtime probe

**And** 只有所有 required 行均存在绑定当前 baseline 的 pass、且没有更新 failure 时，才能报告 `accepted` 并进入 archive

### BHV-002 Same-goal implementation repair continuation

**Given** 用户或 QA 在活动 Full 任务中报告一个已确认 `acceptance_id` 的实际运行结果仍失败，且没有新增产品行为或扩大权限、数据、外部合同边界

**When** 证据证明 Requirement、Overview 和 Detail 已正确声明目标行为，而代码、测试或验证实现偏离该声明

**Then** 将失败分类为 `IMPLEMENT_DEFECT`，从 Phase 2 implementation/check 继续

**And** 不重跑 Requirements、Overview 或 Detail，只刷新受影响代码、可证伪测试、slice/Integration Review 和 runtime receipt

**And** 未受影响且 snapshot binding 仍 current 的 sibling evidence 保持可复用

### BHV-003 Maximum rollback by owning defect

**Given** same-goal runtime failure 已记录为 append-only `runtime_acceptance_failure`，并完成最小可复现和根因分类

**When** 最高上游缺陷分别属于 `PROCESS_DEFECT`、`DETAIL_DEFECT`、`OVERVIEW_DEFECT` 或 `REQ_BLOCKER`

**Then** 最大回退层级分别为当前 evidence/process、Detail、Overview 加受影响 Detail、或 Requirements Full affected chain

**And** 不得因为实现 Bug 默认回到 Requirements，也不得把 material requirement change 降级成实现修复

**And** 任何被现有 digest/snapshot Gate 判定 stale 的证据必须真实刷新，不得伪造 current 状态

### BHV-004 Runtime evidence contradicts planning SSOT

**Given** requirement/design/packet 已确认且 packet-local checks 为绿，但 current target-environment runtime evidence 证明其声明的用户可见结果未成立

**When** reviewer 核对 runtime 结果、外部合同 fingerprint 和 Acceptance Closure Matrix 的 source-to-sink 路径

**Then** reviewer 不得以“SSOT 已确认”或“测试未在 packet 声明”为理由忽略失败

**And** reviewer 不得自行改写产品语义，而必须按最早 owner 路由为 `REQ_BLOCKER`、`OVERVIEW_DEFECT`、`DETAIL_DEFECT`、`PROCESS_DEFECT` 或 `IMPLEMENT_DEFECT`

**And** 额外检查必须绑定具体 acceptance row，保持有界，不能扩大为全仓开放式审计

### BHV-005 Acceptance-path-driven cross-layer verification

**Given** 一个用户可见验收目标依赖外部响应、DTO/解析、Repository、UseCase/Controller 和 UI 终态，即使本次 diff 只修改其中一层

**When** writer 和 reviewer 规划或检查该目标

**Then** 必须按 acceptance path 执行 source-to-sink closure，不得因 diff 未触及三层而跳过跨层检查

**And** deterministic check 必须能在已知错误实现上失败，Integration 必须闭合最终用户结果，ordinary slice 的局部通过不能替代 Integration/runtime evidence

### BHV-006 Post-implementation failure retrospective

**Given** 用户或 QA 报告一个 post-implementation runtime failure

**When** repair continuation 进入根因分析

**Then** 必须记录直接代码根因、最早应捕获该缺陷的 Gate、测试和 Review 未失败的原因、新增的可证伪测试/probe，以及 Skill/workflow/spec 预防回写决定

**And** `guru-bug-fast-path` 与 `trellis-break-loop` 复用同一 affinity、defect class 和 maximum rollback 规则，不另造生命周期

### BHV-007 Archived-task and no-script boundary

**Given** same-goal failure 来自已经 archive 的历史 Full 任务，且本任务明确禁止修改任何 Trellis 脚本

**When** 当前生命周期无法原地 reopen 或机器验证旧 baseline inheritance

**Then** 建立引用原 acceptance ID、artifact digest、receipt 和新 failure evidence 的 repair child/新任务

**And** 如实执行当前 Gate 要求，不能承诺零 Full replanning、原地 reopen 或机器级继承

**And** 任何需要修改 `task.py`、`guru_gate.py`、verify/hooks/apply、CLI TypeScript、Python 或 shell 脚本的方案必须停止并请求新的明确授权

### BHV-008 Source and installed-template parity

**Given** 后续实现已在允许的 source Skill、workflow、spec 或 agent instruction 中修改 Acceptance Closure、repair continuation、runtime completion 或 retrospective 合同

**When** 对应 packaged/install template mirrors 被同步并执行 parity review

**Then** 每个实际安装消费者必须获得与 source owner 语义一致的状态词汇、affinity 规则、maximum rollback 表、wrong-SSOT 路由和 pre-archive runtime 条件

**And** 任一缺失镜像、语义漂移或只改 source 未改安装模板的情况都必须阻断 review-ready/交付结论

**And** parity 修复仍只能编辑 `gate-contract.json.scope.allowed_paths` 中的文档/TOML surface，不得修改任何 Trellis/Guru/CLI 脚本

## Requirements

### REQ-001 Acceptance Closure Matrix

对 `runtime_acceptance_required=true` 的 Full 任务，以及任何涉及用户可见终态、外部 API/schema、持久化/缓存、异步状态或跨层数据转换的验收目标，Detail/`implement.md` 必须包含 Acceptance Closure Matrix。

每一行至少记录：

- `acceptance_id` / 对应 BHV、AC 或 invariant；
- 用户可见结果与允许的终态；
- 触发入口和目标环境；
- 外部/本地 source of truth 及合同 fingerprint；
- source-to-sink 层级与关键字段转换；
- 正向、缺字段/null、错误/超时/降级等负向路径；
- 能在旧错误实现上失败的 deterministic check；
- runtime probe、执行 owner 和所需证据；
- 所属 Implementation Slice / Integration Slice。

矩阵是 digest-bearing planning contract；运行结果写入 mutable evidence，不回写矩阵本身。

### REQ-002 Falsifiable verification

- Bug 修复测试必须证明它会在修复前失败，而不只是证明修复后某个正向 helper 返回成功。
- 外部响应/schema 相关实现必须记录最小合同 fingerprint，例如字段路径、presence/null 语义、fixture 或已脱敏真实响应结构。
- 用户可见行为跨层时，验证触发条件由验收行为决定，不由“本次 diff 改了几层”决定。
- Integration Slice 必须闭合所有 runtime-required 行，不能用 ordinary slice 的局部通过替代最终 source-to-sink 结果。

### REQ-003 Writer prevention contract

实现 Skill/agent 必须：

- 在编码前读取 Acceptance Closure Matrix，并把目标字段/状态沿 source-to-sink 路径追到用户可见终态；
- 发现 packet、Detail、fixture 或 deterministic checks 无法证伪声明的验收目标时停止扩写代码，路由为 `DETAIL_DEFECT`、`REQ_BLOCKER` 或 `PROCESS_DEFECT`；
- 不得因 packet 未声明关键检查就把运行失败当成 packet 外问题；应先回到 planning owner 修复 packet/Detail；
- 为用户反馈的旧失败补回归测试、runtime probe 或明确的 Manual QA evidence owner；
- 只复用未受修复影响且 snapshot binding 仍 current 的证据。

### REQ-004 Reviewer closure and wrong-SSOT routing

实现 Review 必须以声明的用户验收行为为边界，沿其 source-to-sink 路径做有界 closure audit，而不是只按改动层数或 diff 的直接依赖决定是否检查。

当真实 runtime evidence 与 requirement/design/packet 冲突时：

- 不得仅以“SSOT 已确认”否决真实失败；
- 不得由 reviewer 私自重写需求或设计；
- 必须把冲突分类为 `REQ_BLOCKER`、`OVERVIEW_DEFECT`、`DETAIL_DEFECT`、`PROCESS_DEFECT` 或 `IMPLEMENT_DEFECT`，回到对应 owner 修复；
- 对声明的验收目标，如果 packet 缺少必要的可证伪检查，reviewer 可以要求补齐 planning contract，不受“不得运行 undeclared tests”规则阻止；
- 额外检查必须有界且与某一 Acceptance Closure Matrix 行直接关联，不能扩大为全仓开放式审计。

### REQ-005 Runtime acceptance completion states

对 runtime-required Full 任务，流程必须区分并记录：

1. `implementation_verified`：静态/测试/Review 通过，但尚未完成运行验收；
2. `runtime_acceptance_pending`：已移交目标环境执行，任务仍保持活动；
3. `runtime_acceptance_failure`：实际结果不满足声明验收，进入 repair continuation；
4. `runtime_acceptance_pass`：目标环境、步骤、预期、实际和证据齐全，允许声明 Accepted；
5. `accepted`：所有 required runtime 行均为 current pass，才可进入归档。

这些是 acceptance evidence 状态和对外结论，不是新增 task lifecycle 状态。状态记录复用现有 task-local `verification-evidence.jsonl`；`task.json.status` 继续使用现有值。不得把 `implementation_verified`、`COMMIT_READY` 或测试全绿表述为用户验收完成。

### REQ-006 Pre-archive protection

`trellis-finish-work` 及 Guru workflow 必须在 Skill/workflow 层检查：

- 任务是否声明 `runtime_acceptance_required=true`；
- 每个 required acceptance row 是否有 current `runtime_acceptance_pass`；
- 是否存在更新的 `runtime_acceptance_failure` 或仍 pending 的移交。

缺少 pass 或存在未关闭 failure 时，保持任务 `in_progress`，报告唯一下一步，不执行 archive。该约束是 agent 行为合同，不得描述为脚本级 fail-closed Gate。

### REQ-007 Maximum rollback routing

同一验收目标失败时按下表选择最大回退层级：

| Defect class | Maximum rollback | Required refresh |
| --- | --- | --- |
| `IMPLEMENT_DEFECT` | Phase 2 implementation/check | 受影响代码、测试、slice/integration review、runtime receipt |
| `PROCESS_DEFECT` | Phase 2 evidence/process 或 Detail（仅当 packet/计划需改） | 受影响 mutable evidence；修改 digest-bearing plan 时按 Detail 规则刷新 |
| `DETAIL_DEFECT` | Phase 1 Detail | 受影响 Detail、packet、slice/integration evidence；不重跑 Requirements/Overview |
| `OVERVIEW_DEFECT` | Phase 1 Overview + affected Detail | Overview 与受影响 Detail/downstream evidence；不重跑 Requirements |
| `REQ_BLOCKER` or material requirement change | Phase 1 Requirements | 完整受影响 Full chain |
| Environment/fixture-only failure | 当前 verification step | 环境/fixture evidence；不得改产品需求掩盖环境问题 |

分类必须以证据为依据。未修改的上游产物和未受影响 sibling slice receipts 保持可复用；若现有 Gate 因 digest binding 判为 stale，必须如实刷新，不能伪造 current evidence。

### REQ-008 Active-task continuation and archived-task boundary

- runtime-required Full 任务应在用户/QA runtime acceptance 完成前保持活动，从根源上避免 reopen。
- 同一活动任务收到 same-goal failure 时，不创建第二套 Requirement/Overview/Detail 包，直接记录 failure、分类并继续。
- 对已经 archive 的历史任务，因为本任务禁止修改脚本且当前无 reopen/baseline-inheritance 能力，只能建立 repair child/新任务并引用原基线；不得承诺机器级局部继承或完全跳过现有 Full Gate。
- archived-task 的真正 reopen 和自动 baseline inheritance 明确留作 future script-enabled capability，必须另获授权。

### REQ-009 Mandatory retrospective and prevention writeback

每个用户/QA 报告的 post-implementation runtime failure 都必须运行 `trellis-break-loop` 等价复盘，并记录：

- 直接代码根因；
- 缺陷最早应被哪个 Requirement/Design/Implementation/Test/Review/Process Gate 捕获；
- 为什么现有测试与 Review 没有失败；
- 本次补充的可证伪测试/probe；
- 需要回写的 Skill/workflow/spec；
- 无需回写时的明确理由。

`guru-bug-fast-path` 必须复用该分类与 rollback 规则，作为 repair continuation 的执行入口，而不是另建一套生命周期。

### REQ-010 Mirror parity and no-script boundary

- 后续实现只允许编辑 `gate-contract.json.scope.allowed_paths` 中的 Skill、workflow、spec、agent instruction 和模板镜像。
- source/template/package 对应文件必须保持语义一致，并有 parity 检查。
- 任何 `.trellis/scripts/**`、Guru verify/hooks/apply 脚本、CLI TypeScript runtime、Python 或 shell 脚本改动均越界，必须停止并请求新的明确授权。
- 不得把 Skill/workflow 纪律包装成不可绕过的机器安全属性。

## Out Of Scope

- 修改 `.trellis/scripts/**` 或任何 Trellis Python/shell/TypeScript runtime、CLI、hook、verify、apply 脚本。
- 新增 `repair-intake`、`task.py reopen`、自动 receipt parser、自动 digest dependency graph 或自动 archive/commit Gate。
- 为已归档 Full 任务实现机器级 baseline inheritance。
- 修复会话 `019f666f-832a-7eb2-a460-abdcef26a649` 对应业务仓库中的 Character Chat 生产代码。
- 弱化现有 Full route、风险分类、Review provider、snapshot binding、scope ownership 或 Integration regression 要求。
- 本轮执行 `task.py start`、修改 Skill/workflow/spec 正文、修改源码/测试、commit、push、merge、archive 或 finish-work。

## Acceptance Criteria

- [ ] `prd.md` 明确同时解决首次实现防漏和 same-goal repair continuation，而不是只优化事后流程。
- [ ] Acceptance Closure Matrix 合同覆盖用户结果、外部合同 fingerprint、source-to-sink、正负路径、可证伪检查、runtime probe 和证据 owner。
- [ ] Full completion 明确区分 technical green、runtime pending/failure/pass 和 Accepted；runtime-required 未 pass 不得 archive。
- [ ] `IMPLEMENT_DEFECT` 场景不重跑 Requirements/Overview/Detail，只刷新受影响实现、验证、Review 和 runtime evidence。
- [ ] `DETAIL_DEFECT` 只回 Detail；`OVERVIEW_DEFECT` 只回 Overview + 受影响 Detail；只有 `REQ_BLOCKER`/material requirement change 才完整回 Requirements。
- [ ] 真实 runtime failure 与错误 SSOT 冲突时会被上游路由，不会因 packet/SSOT 已确认而被否决或忽略。
- [ ] 用户可见跨层检查按 acceptance path 触发，不再依赖 diff 是否触及 3+ 层。
- [ ] post-implementation runtime failure 必须产生 root-cause、漏检 Gate、补充测试/probe 和预防回写记录。
- [ ] 活动 Full 任务可以通过“保持 in_progress 直到 runtime pass”避免完整 reopen；已归档任务的无脚本限制被明确披露。
- [ ] source/template/package mirror 清单和 parity 验证完整。
- [ ] `gate-contract.json` 显式禁止所有 Trellis/Guru/CLI 脚本路径，且后续实现计划包含 forbidden-path audit。
- [ ] `implement.jsonl` / `check.jsonl` 使用真实 spec/research 引用，不保留 `_example`。
- [ ] 规划产物通过 task artifact validation、JSON/JSONL parse、Markdown fence 检查和 `git diff --check`。
- [ ] 本规划阶段没有修改任何 Trellis 脚本、没有启动任务，也没有执行实现或生命周期动作。

## Brainstorm Evidence

- Skill loaded: `trellis-brainstorm`.
- Repository evidence inspected:
  - session `019f666f-832a-7eb2-a460-abdcef26a649`;
  - `.codex/agents/trellis-implement.toml`;
  - `.codex/agents/trellis-check.toml`;
  - `.agents/skills/trellis-check/SKILL.md`;
  - `.agents/skills/trellis-finish-work/SKILL.md`;
  - `.agents/skills/trellis-break-loop/SKILL.md`;
  - Guru Flutter implementation writing/review Skills;
  - `guru-bug-fast-path`;
  - Guru client workflow;
  - cross-layer thinking and implementation trace specs;
  - repeated-debug hardening draft and planning task.
- Domain/terminology triggers:
  - “Full 任务完成” currently conflates technical verification, archive, and runtime acceptance;
  - “Bug 修复” must distinguish same-goal defect from material requirement change;
  - “保证完成度” requires both pre-failure prevention and post-failure bounded repair.
- Current code vs user intent conflicts:
  - current flow can archive without runtime receipt;
  - current review can be packet-correct while the user journey is still broken;
  - current archived task has no no-script reopen mechanism.

### Question Policy

question_policy: mixed

- Evidence-answered: repository and session evidence determined the current false-green root cause, existing Skill/workflow gaps, active-task continuation capability, and archived-task no-script limitation; these facts required no product guess from the user.
- User-confirmed in current turns: the user explicitly confirmed the no-script scope boundary and then confirmed the complete current planning package.

- Product decisions confirmed: DEC-001 adopts Acceptance Closure plus Full Repair Continuation for this P1 `full_chain` task; DEC-002 forbids modifying any Trellis-owned script file; DEC-003 confirms the complete current PRD/design/implementation planning package. user_quotes: `确认，记住本次调整不能修改任何 trellis 自己的脚本文件`; `已确认`. confirmed_ref: Codex task `019f7f4e-2054-72b3-bce0-e4a1cbf35807`.
- Open product/scope/risk questions: none; reason: the user explicitly confirmed the no-script boundary and then confirmed the complete current planning package in this Codex task.

## Planning Confirmation

- Confirmation status: user confirmed.
- Confirmed artifacts: current `prd.md`, `design.md`, `implement.md`, context manifests, and the no-script scope recorded in `gate-contract.json`.
- User quote: `已确认`.
- Confirmed reference: Codex task `019f7f4e-2054-72b3-bce0-e4a1cbf35807`, current user turn.
- Authorization boundary: this confirmation approves the planning package. It does not authorize `task.py start`, Skill/workflow/spec implementation edits, commit, push, merge, archive, or finish-work.

## Open Questions

None. The no-script boundary is confirmed; the remaining archived-task limitation is documented rather than hidden.
