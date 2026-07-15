# Custom-first Guru delivery control plane

## Goal

以官方 Custom-first、功能阶段 Trellis Core 零修改、完整可卸载为硬边界，重构所有任务类型的 Guru/Trellis 交付控制面，使 Agent 在风险比例化流程中快速进入真实代码、提前暴露高风险、经过少量用户确认后自主闭环，并让 Gate、知识和证据持续降低后续任务的时间、Token 与返工成本。

成功不以“通过了多少 Gate”衡量，而以经过验证的业务交付净收益衡量：

`有效交付 = 正确且可验证的代码变更 /（交付时间 + Token + 用户确认 + 返工 + 文档维护成本）`

## Background

- 会话 `019f5b42-b507-7801-96ef-50b1ed01c863` 在用户要求 Lite 快速修复后运行约 98 分 42 秒，新增约 2345 万 total tokens、165 次模型周期，结束时仍处于 planning，业务源码修改为 0。
- 该会话出现 Overview/Detail digest 相互失效、重复 review、scope 扩张、长时间等待和巨型上下文重放。
- 本次会话初期也出现了“根因已经成立但继续扩大审计和后台 Agent”的倾向，说明问题不只属于 Lite，而属于所有任务类型共享的路由、监督、预算和停止机制。
- 当前仓库已经具备 Guru Workflow、Spec、Skills、Hooks、Gate 和 Supervisor，但官方 Custom 扩展与 Trellis SDK fork 定制并存，存在双重分发、双重真源和未来升级负担。

## Terminology

- **Trellis Core / SDK**：`packages/cli/src/**`、`packages/core/**` 及其发布包内的通用 Trellis 实现。
- **Guru Template Registry**：`guru-template/index.json`、`guru-template/workflows/**` 和 `guru-template/specs/**`，通过官方 workflow/spec marketplace 安装。
- **Guru Extension Pack**：官方 Template 目前不能分发的 project-local Skills、Agents、Hooks、Scripts 和 Config patch，源位于 `guru-template/overlay/**`。
- **TTFC**：Time to First Code，从用户提出实现请求到首个符合 scope 的业务代码 diff。
- **Gate-caused rework**：不是需求或代码真实变化，而是 Gate/digest/review 机制自身造成的证据重做或文档返工。
- **Semantic progress**：业务 diff、风险关闭、测试新增/转绿、明确决策或可验证 artifact 变化；单纯重读、等待和重复 review 不算进展。

## Confirmed Decisions

1. 重构面向所有任务类型，不只修 Lite：Small/Inline、Micro、Lite、Full、Review-only、Research/Docs 和 Repeated Debug 均在范围内。
2. 默认使用官方 Custom Workflow、Spec Template Marketplace、Custom Skills、Custom Agents、Custom Hooks 和 `.trellis/config.yaml`。
3. 功能实现阶段不得新增 Trellis Core/SDK 定制；默认允许写入范围仅为 `guru-template/index.json`、`guru-template/workflows/**`、`guru-template/specs/**` 和 `guru-template/overlay/**`。
4. 现存 SDK 内 Guru bundling、`trellis guru` 命令和 fork-only `before_start` 支持只作为后续独立 de-fork 清理候选；必须在官方 Trellis + Template/Extension 等价验证后才能删除。
5. Guru 定制必须支持 dry-run、安装、状态检查、卸载和安装后验证；卸载不得破坏用户修改。
6. 用户确认必须批量、最少且不可重复；只有新增的不可逆产品取舍、真实外部信息缺口或扩张后的关键风险才允许再次询问。
7. 用户于 2026-07-14 回复“好，接受”，确认上述架构基线并授权创建 full-chain Trellis task 进入规划。
8. 用户于 2026-07-15 确认 M5/M6 路由修订：四路由按需求清晰度、风险、耦合、可逆性与验证成本分工；Lite 必须创建标准 Trellis task、必要时进入有界 Brainstorm、确认一次需求后自主闭环；用户可指定 Route，但 High-risk 不得降级。

## Outcome-first Delivery Milestones

本节自 2026-07-15 起是剩余工作的执行权威。原设计包中的六个内部 slice、bootstrap burn、Marketplace/WAL、trusted reviewer identity 和 generic replay framework 不再构成完成标准；只有下面里程碑对应的用户结果构成完成标准。

### M0 — Custom V0 与自用生命周期（已完成）

- 四路由 policy、Lite 直达代码合同、High-risk 风险前置、一次确认上限、exact evidence reuse 与一致性检查已落地。
- Custom overlay 支持安装、owned partial-failure recovery、managed-asset unapply，并保留无关用户修改。
- 证据：`de52458f`、`52e64185`、`apply_test.sh 101/0`、Custom overlay `564/0`、Core-zero、Codex-only。

### M1 — 真实路由运行证明（candidate complete）

- 在 disposable 官方 Trellis target 安装已提交 Custom 包，执行四路由矩阵。
- 用两个历史失控会话分别执行 Lite 与 Full high-risk 最小 dogfood。
- 历史 M1 基线要求 Lite 在 5 分钟级进入代码、确认 0、Worker 0、无 Overview/Detail planning loop；其中确认 0 已由 M5 当前合同明确取代，TTFC/Worker/无 Full planning loop 证据继续保留。
- Full high-risk 必须在实现前暴露风险，最多一次确认，确认后自主运行到 deterministic check。
- 记录 TTFC、确认数、Worker 数、finding-to-fix cycles、full-suite run count 与 route wall time；全程不得出现 Claude event。
- 结果证据：`M1_OPERATIONAL_ROUTE_PROOF.md`；Lite TTFC `18s`、确认 `0`、Worker `0`；Full/high-risk 缺 risk packet 时 `rc=2`、`start_attempts=0`；独立检查 `2 HIGH + 1 MEDIUM` 已单批修复；apply/consistency `109/0`；Core-zero、Codex-only。

### M2 — 全意图成本递减与 Gate 净收益（candidate complete）

- 覆盖 implementation、review-only、research/docs/config/ops 与 repeated-debug 的 first-value 和终态。
- 相同 task fingerprint/digest 的 warm run 复用 evidence，受控 planning/context/token-budget proxy <= cold run 的 70%；digest 变化必须失效。
- scope expansion 在继续实现前重判；相同确认不重复；Gate-caused rework < 10%。
- 平台未提供真实 token telemetry 时标记 `unknown`，只能另列 proxy，不得冒充真实成本。
- 结果证据：`M2_ALL_INTENT_COMPOUNDING_PROOF.md`；7/7 intent exact warm proxy 为 cold 的 70%，target 与 docs/code/test digest 漂移各 7/7 失效；scope expansion 在下一次写入前提升为 Full/high；相同 attestation 不产生第二确认 batch；Gate-caused rework 候选样本为 `0/4`，真实 provider token telemetry 仍为 `unknown`。

### M3 — 官方 Custom 与 Template cutover readiness（candidate complete）

- 验证官方 Workflow/Spec/Config/Template resolver，不依赖 fork package，不修改 Core。
- 补齐只读 plan/status/verify 与兼容的 apply/upgrade/unapply 用户生命周期，复用现有 rollback bundle，不建设 WAL。
- 仅产出最小 Template cutover mapping；官方工具未要求时不新建 manifest 或 Marketplace 引擎。
- 结果证据：`M3_CUSTOM_TEMPLATE_CUTOVER_PROOF.md`；官方 Trellis `0.6.7` 四组 spec/workflow exact-byte 安装通过，blank fallback 被拒绝；Custom lifecycle `120/0`，catalog `18/0`；Codex review 的 1 个 HIGH 状态假绿已单批修复；Core-zero、Codex-only。

### M4 — 最终一致性与任务收口（historical candidate pass）

- 发布 hardened status，修复旧 V0 deferred 列表与当前实现不一致。
- 完成 `REQ/BHV -> design -> code -> test` trace、按最终 diff 运行验证、一次 Codex check-only review、`trellis-update-spec` 和最终提交。
- archive/finish 需要显式生命周期授权；不 push。
- M4 的旧 Lite `confirmation=0` 证明保留为历史快路径基线，不再代表当前 Route 合同；本轮修订由 M5/M6 接管，历史报告不得改写为仿佛当时已经要求 Lite 确认。

### M5 — 难度路由、标准 Lite task 与一次确认（current）

- 自动 Intake 选择满足安全边界的最低成本 Route；用户可升级到更重 Route，向下降级必须证明目标 Route 准入条件，High-risk/unknown-high 永远保持 Full。
- `commit_requested` 是交付动作，不得单独决定任务难度；Small 可在初始提交授权下建立最小提交合同而不伪装为更复杂任务。
- Lite 使用官方 `task.py create` 创建标准 Trellis task，任务目录内管理 `task.json`、`gate-contract.json`、compact `prd.md`、Trellis jsonl 上下文与 mutable execution evidence。
- Lite 先查仓库证据，仅在真实产品/范围/失败路径/验收歧义存在时进入 bounded Brainstorm；用户确认当前 requirements digest 一次后，自动 start、实现、检查、证据/Spec 同步和可逆 commit-ready。
- Small/Micro/Lite/Full 的确认预算分别为 `0/0/1/1 batch`；Full 一批确认覆盖当前需求、风险和关键设计决定，Runtime 不得再要求 requirements/detail/commit 三轮重复确认。
- Route selection 记录 recommendation、selection source、generation 与 scope fingerprint；首次写入前可基于证据合法降级，首次写入后只能升级。

### M6 — 路由矩阵回放与最终候选收口（pending）

- 在 disposable target 验证四 Route、Lite 标准任务创建/确认/autoclose、Full 风险前置、合法 override、非法降级、evidence reuse 与 consistency drift。
- 回放两个历史失控会话的关键失败模式；Lite 从需求确认到 first code 保持 5 分钟级，Full 在 implement Worker 前持有 current risk/decision evidence，全程 Claude event 为 0。
- 只跑一次完整 overlay suite、一次官方 Custom apply/unapply、一次 Codex check-only final review；非 acceptance blocker 不扩展范围。

## Core Capabilities

- **P0**：全任务类型的风险比例路由、TTFC/成本硬预算和 semantic-progress watchdog。
- **P0**：高风险实现前 risk packet、scope expansion 重判和最少批量确认。
- **P0**：按语义依赖失效的 digest、独立 review 身份和停止 review ping-pong。
- **P0**：官方 Custom-first Template/Extension 分发以及完整可撤销安装。
- **P1**：上下文/Token 观测、同类任务知识复用和成本递减。
- **P1**：文档/代码/测试追踪、Gate 净收益观测和跨平台降级声明。

## Behavior Specifications

### BHV-001 [REQ-UC-001] 低风险任务快速进入真实代码

- **Given** intake 将任务判为 Inline、Micro 或 Lite，且不存在未关闭的关键风险
- **When** Agent 完成该路由的最小必要合同和检查
- **Then** 系统在对应 TTFC 预算内进入首个符合 scope 的业务代码 diff，不执行 Full 专属 planning/review

### BHV-002 [REQ-UC-002] 高风险在实现前暴露

- **Given** intake 将任务判为 Full 或执行中新增高风险 layer/path/contract
- **When** Agent 准备开始或继续实现
- **Then** 系统先生成或增量更新 risk packet，只对 unresolved critical/high 决策请求批量确认，确认前不得进入实现 worker

### BHV-003 [REQ-UC-003] Agent 少量确认后自主闭环

- **Given** 用户已经确认当前 scope、关键风险和不可逆取舍
- **When** requirements/design/code/test 输入没有新的语义变化
- **Then** Agent 自主完成实现、检查、同步和验证，不重复询问同一决定

### BHV-004 [REQ-UC-004] 同类任务成本递减

- **Given** 仓库存在同一 task family 的已验证决策、失败根因、验证命令和 evidence
- **When** 新任务只改变部分输入
- **Then** 系统复用未变化知识，只复核 delta，使 planning 时间、读取量和 token 不高于首个基准的 70%

### BHV-005 [REQ-UC-005] 文档代码测试保持一致

- **Given** 变更影响 route/API/schema/state/boundary/ownership/testing 等契约
- **When** Agent 完成实现并进入最终检查
- **Then** `REQ/BHV -> design -> code -> test` 映射完整，Template/Extension/安装后文件不存在未解释漂移

### BHV-006 [REQ-UC-006] Gate 减少而非制造返工

- **Given** artifact 的语义输入没有改变，或只改变不属于该 Gate 依赖的 section/evidence
- **When** Gate 再次运行
- **Then** 有效 evidence 被复用，无关上游 review 不失效，重复 finding 无新增证据时停止而不是继续循环

### BHV-007 [REQ-UC-007] Guru 定制可完整撤销

- **Given** Guru Template/Extension 已安装到官方 Trellis 项目，且用户可能修改部分 managed files
- **When** 用户运行 status/unapply
- **Then** 系统只撤销仍由 Guru 拥有且 hash 匹配的内容，保留并报告用户冲突，恢复 native Trellis 可用状态

### BHV-008 [REQ-UC-008] 自动推荐与受约束 Route override

- **Given** Intake 已获得仓库证据、需求清晰度、风险、耦合、可逆性和验证成本
- **When** Agent 自动推荐 Route 或用户指定不同 Route
- **Then** 系统选择最低合法 Route；向上切换直接允许，向下切换须满足目标准入条件，High-risk/unknown-high 不得降级，并持久化 generation 与 scope fingerprint

### BHV-009 [REQ-UC-009] Lite 标准任务与一次确认后自动闭环

- **Given** 任务被选为 Lite 且不存在 High-risk
- **When** 官方 Trellis task 已创建、仓库证据已检查、必要 Brainstorm 已关闭、用户确认当前 compact requirements digest
- **Then** 系统无需 Overview/Detail planning review 或实现 Worker，自动完成 start、实现、focused check、task-local evidence、Spec 同步和可逆 commit-ready，除真实 scope/high-risk/不可逆变化外不再确认

## Requirements

### R1. Universal risk-proportional routing

- 一套可执行路由覆盖 Small/Inline、Micro、Lite、Full、Review-only、Research/Docs 和 Repeated Debug。
- 路由输入必须包含影响面、可逆性、跨层范围、敏感领域、历史失败和变更路径，不能只靠关键词。
- 路由必须在 scope/layer/risk 变化时重判；高风险不得降级为非 Full。

### R2. Fast path to real implementation

- Inline、Micro、Lite 必须有独立的最小 artifact 和 Gate 集合，禁止把 Full 流程缩写后复用。
- 每条路由必须具有 planning、review、模型周期和无代码进展预算；越界后停止并给出单一恢复动作。
- 建议默认 SLO：Inline TTFC p95 <= 2 分钟，Micro <= 5 分钟，Lite <= 10 分钟；Full 在用户完成关键风险确认后 <= 15 分钟进入首个实现 slice。

### R3. Pre-implementation high-risk exposure

- Full 在首个业务代码 diff 前生成紧凑 risk packet，覆盖安全、隐私、迁移、兼容、数据损失、跨层契约、外部依赖和回滚。
- 只有 unresolved critical/high decision 阻止实现；普通设计争议不得伪装成高风险。
- 官方 Trellis 缺少跨平台原子 `before_start` 时，使用 wrapper、平台 Hook、启动后补偿校验、Agent preflight 和 commit/CI Gate 分层防御，并明确其信任边界。

### R4. Minimal user confirmation

- Small/Inline、Micro、Lite、Full 的确认预算分别为 `0/0/1/1 batch`，且相同 route/scope/requirements/risk 输入不得重复询问。
- Lite 的唯一确认绑定 task-local `prd.md`、selected route、risk 与 scope fingerprint；运行证据追加、focused repair 和 Spec 同步不得使该确认失效。
- Full 的唯一批量确认覆盖当前需求、critical/high risk 与关键不可逆设计决策；不得再拆成 requirements、detail 与可逆 commit 三轮确认。
- 每个确认项必须包含建议答案、影响和选择不同方案的代价。
- 可由仓库事实、现有规范或可逆默认值决定的事项由 Agent 自主决定。

### R5. Semantic digest dependency graph

- requirements、overview、detail、implementation scope 和 execution evidence 使用独立 digest。
- 仅真实依赖该变化的下游证据失效；无关章节、格式、时间戳和 append-only execution evidence 不得让上游 review 失效。
- Lite `design.md §2` 变化不得使未变化的 `§1` Overview review stale。

### R6. Honest and convergent review

- Review evidence 记录 provider、worker、thread/context provenance 和输入 digest；两个 run-id 或 same-provider context 不能替代独立 reviewer 证明。
- Review 次数按风险配置：低风险零次或机械检查，Lite 不设 pre-code planning review，Full 只在真实风险或最终实现快照需要时进行 bounded Codex check-only review。
- 同一 finding 两轮没有新增证据或 semantic delta 时进入 STALLED，不得继续 review ping-pong。

### R7. Bounded supervisor state machine

- Supervisor 对每阶段记录 deadline、模型周期、tool call、repair round、等待时间和 semantic progress。
- 达到预算、连续无进展、worker idle 或 scope 扩张时必须终止当前循环并返回结构化状态。
- 禁止无界 `wait_agent`、follow-up 和相同上下文重放；并发只用于真正独立且有净收益的工作。

### R8. Context and cost control

- 每阶段从 task-local context manifest 构建最小上下文，阶段切换后重建，不携带完整历史。
- 记录 input/cached/output token、上下文大小、重复文件读取和 cache hit；cached token 仍计入时间与注意力预算。
- 第二个相同任务族应复用决策、失败根因、验证命令和稳定 evidence，只重审变化输入。

### R9. Scope expansion control

- 保存确认后的 scope fingerprint 和 layer/risk classification。
- 新增 layer、公共 API、schema、生成文件、基础设施、高风险路径或明显超出 allowed paths 时自动暂停并重新 intake。
- 只向用户呈现新增风险和新增决定；原确认不重复。

### R10. Documentation, code, and test consistency

- 维护 `REQ/BHV -> design unit -> code path/symbol -> test evidence` 可执行追踪。
- route/API/schema/state/boundary/ownership/testing 变化触发 design-sync；非契约性改动使用有证据的 `no-doc-impact`。
- source、Template Registry、安装后 Extension、平台镜像和测试不得存在多份手工 SSOT。

### R11. Gate value observability

- Gate evidence 记录 duration、finding 命中/误报、失效原因、repair round、artifact delta 和 Gate-caused rework。
- 相同 digest 的有效 evidence 必须复用；连续低收益或高误报 Gate 进入治理审查。
- Gate 通过不等于任务完成；最终完成必须包含业务结果、验证、同步和预算结果。

### R12. Official Custom-first distribution

- 四个平台的 workflow/spec 都登记在 `guru-template/index.json`，可由官方 marketplace source 解析。
- Workflow/Spec 规则落在官方 Template；Skills/Agents/Hooks/Scripts/Config 落在独立 Guru Extension Pack。
- 功能实现不得依赖 `@devsc/trellis`、bundled Guru IDs、`trellis guru` 或 fork-only Core symbol。

### R13. Reversible installation contract

- Extension Pack 提供 `plan`、`apply`、`status`、`unapply`、`verify`，默认 `plan`/dry-run 先行。
- 安装 manifest 记录扩展版本、来源、平台、managed files、安装前状态和安装后 hash。
- `unapply` 仅删除仍匹配 managed hash 的文件；用户修改保留为冲突，配置精确恢复原值。
- `apply -> verify -> unapply` 后，除明确保留的用户工作和审计记录外，目标项目恢复为安装前等价状态。

### R14. Cross-platform degradation policy

- 对 Hook、Sub-agent、Command 能力按平台声明 `enforced`、`compensated` 或 `advisory`，禁止把 advisory 说成 hard Gate。
- Codex 默认使用官方推荐的 inline；只有任务可并行且上下文隔离收益明确时才启用 channel/sub-agent。
- worker 数、idle timeout、warn-before 和 route budgets 使用保守默认，并允许项目配置覆盖。

### R15. Regression and benchmark suite

- 从两个失控会话提取最小 deterministic dogfood/replay case：digest 震荡、重复 review、scope 扩张、无业务 diff、长等待和上下文膨胀；不建设 generic replay framework。
- 建立 route matrix、digest metamorphic、reviewer independence、budget/stagnation、scope expansion、confirmation、context/token、reversibility、mirror/design-sync 测试。
- 使用 M1/M2 operational proof 覆盖全部任务类型的 first-value、成本和终态；单元测试全绿但仍出现长时间 planning + 零业务 diff 时，发布失败。

### R16. Difficulty routing and user override

- Route 难度按需求清晰度、风险、耦合、可逆性与验证成本判断；文件数和 commit intent 只能作为辅助输入。
- 自动推荐使用最低合法 Route；用户选择更重 Route 直接接受，选择更轻 Route 时重新验证目标 eligibility，失败时返回唯一 blocker 和可降级条件。
- Route selection 使用单调 `selection_generation`；首次写入前允许合法降级，首次写入后只允许升级，事后 relabel 不得满足缺失 Gate。

### R17. Standard Lite task and task-local authority

- Lite 必须复用官方 `task.py create`，不得新建并行 task framework；Custom 只负责 route contract、confirmation 和 task-local evidence 扩展。
- Compact requirements、Brainstorm Evidence、实现/验证证据、commit plan 与实际 review record 全部位于 Lite task 目录；不得只存在于聊天或仓库外临时文件。
- Lite 默认不创建正式 Overview/Detail；若局部设计扩大为跨层、公共契约或 High-risk，必须在下一次写入前升级 Full。

## Acceptance Criteria

- [ ] 功能实现期间 `git diff -- packages/cli/src packages/core` 无新增 Guru 功能修改。
- [ ] `guru-template/index.json` 完整登记 Flutter、Go、H5、iOS 的 workflow/spec，官方 marketplace resolver 可解析。
- [ ] 干净的官方 Trellis 项目不安装 fork 包即可安装并运行 Guru Template + Extension。
- [ ] Extension 支持 `plan/apply/status/unapply/verify`，重复 apply 幂等，修改过的用户文件不会在卸载时删除。
- [ ] `apply -> verify -> unapply` 在 fixture 项目中恢复安装前等价状态。
- [ ] Inline/Micro/Lite/Full/Review/Research/Repeated Debug 均有明确 artifact、预算、确认和停止策略。
- [ ] Lite 由官方 `task.py create` 产生标准 Trellis task，任务目录内存在 current compact requirements、route contract 和 mutable execution evidence。
- [ ] Lite 缺失或 stale requirements confirmation 时首次 repository write fail closed；确认后实现、检查、证据/Spec 同步和可逆 commit-ready 不产生第二次确认。
- [ ] 自动推荐、用户向上切换、合法向下降级、High-risk 降级拒绝和 first-write 后降级拒绝均有可执行回归。
- [ ] Lite detail-only 修改不改变 Overview digest；真实上游变化按依赖图精确失效。
- [ ] 同一 reviewer/context 伪造两个 run-id 不能满足独立 review。
- [ ] Scope/layer/risk 扩张会在继续实现前触发重新 intake，并只请求新增决定。
- [ ] 两个失控会话 replay 在预算内进入真实代码或返回明确终止状态，不再出现 98 分钟 planning + 零业务 diff。
- [ ] Small/Micro/Lite/Full 分别为 0/0/1/1 confirmation batch；相同输入确认不会重复。
- [ ] 第二个相同任务族的 planning 时间、上下文读取和 token 不高于首个基准的 70%。
- [ ] 契约性变更具备 requirement/design/code/test 映射，Template/Extension/安装后文件无未解释漂移。
- [ ] 相同 digest evidence 100% 复用，Overview/Detail review ping-pong 为 0，Gate-caused rework 目标 < 10%。
- [ ] 切回 native workflow 并卸载 Guru 后，官方 Trellis start/update/check/finish 基线仍通过。

## Failure Paths

- **Budget exceeded**：停止当前 worker/review，记录已完成进展和首个未完成 blocker，返回一个恢复动作；不得自动续开相同循环。
- **No semantic progress**：连续两个 repair/review cycle 无业务 diff、风险关闭或测试进展时返回 `STALLED`。
- **Scope expansion**：新增 layer/path/risk 后冻结当前执行，增量 intake；只请求新增决定。
- **Reviewer identity conflict**：两个 run-id 来自相同 reviewer/context 时不计为独立 clean。
- **Marketplace unavailable**：使用已 pin 的本地版本或明确失败；不得静默切换到 SDK bundled Guru。
- **Unsupported platform hook**：能力标记为 compensated/advisory，依靠 wrapper、Agent preflight 和 commit/CI Gate；不得宣称为原子阻断。
- **Unapply conflict**：managed file/config 已被用户修改时保留文件、输出冲突清单并返回非零；不得强删或猜测合并。
- **Template/Extension version mismatch**：安装和 upgrade fail closed，并给出兼容版本，不允许半安装。

## Unresolved Questions

无阻塞未决问题。若设计阶段发现官方 Custom 无法满足新的不可逆需求，必须把该新增决定批量升级给用户；当前已确认决策不得重问。

## Constraints

- 保留当前工作树中用户已有的 `AGENTS.md`、`CLAUDE.md` 和 dirty `marketplace` submodule，不吸收、不覆盖、不回退。
- 手工编辑使用 `apply_patch`；修改 symbol 前必须完成 GitNexus upstream impact 分析，高/关键风险先告知用户。
- GitNexus 当前索引曾因 FTS `file_fts` 不一致而刷新失败；实现前必须修复或建立可用的 impact/detect-changes 路径。
- source live checkout 是当前事实；历史 memory 中已修复的 `implement.md` mutable-evidence 问题不得重新列为当前缺陷。
- 高风险 workflow/Gate 改动必须保持 full-chain，不允许以本任务正在优化流程为由绕过现有任务 Gate。

## Out of Scope

- 本阶段不新增 Trellis Core API、CLI command、fork-only task status 或 SDK 配置键。
- 本阶段不直接删除现存 SDK Guru bundling；删除属于 Template/Extension 等价验证后的独立 de-fork slice。
- 不承诺控制模型供应商的底层计费或平台自身的隐藏上下文，只约束本仓库可控制的调度、prompt、context 和循环。
- 不把 Agent 可写 evidence 宣称为安全授权；最终 commit/CI/用户 attestation 的信任边界单独保留。

## Known Risks

- 官方 lifecycle hooks 只有非阻断 `after_*`；跨平台原子 pre-start Gate 需要 wrapper + Hook + compensation + commit/CI 分层替代。
- Workflow marketplace 当前复制 workflow 内容但不持久化远程 source；Extension manifest 必须记录来源并提供显式 status/upgrade。
- 平台 Hook 能力不同；必须测试降级路径，不能只在 Claude/Codex 单平台证明。
- 完整卸载涉及 YAML/JSON/平台设置合并，必须使用结构化 patch 和 ownership hash，不能依赖字符串删除。

## Brainstorm Evidence

- Skill loaded: complete — `trellis-brainstorm`、`requirements-ambiguity-decomposition`、`trellis-meta`。
- Repository evidence inspected: complete — workflow/spec registry、overlay installer、Gate/Supervisor、config、官方 Custom 文档和两个会话取证。
- Domain/terminology triggers: resolved — 区分 Trellis Core、Template Registry、Extension Pack、Gate 与安全边界。
- Current code vs user intent conflicts: documented — SDK bundling、fork-only before_start、incomplete registry、non-reversible apply、Codex sub-agent default。
- Product decisions confirmed:
  - DEC-001: all-task scope、Custom-first、功能阶段 Core zero-addition、reversible extension、de-fork later 作为统一架构基线
    - user_quote: "好，接受"
    - confirmed_ref: current-session architecture-baseline approval on 2026-07-14
  - DEC-002: 四级难度分工、自动推荐和受约束 override、Lite 标准 Trellis task、条件式 Brainstorm、Lite/Full 各一次确认后自动闭环
    - user_quote: "已确认"
    - confirmed_ref: current-session complete-adjustment-plan approval on 2026-07-15

### Question Loop Log

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-001 | 2026-07-14 | 是否接受“官方 Custom-first、功能阶段 Core 零修改、扩展包完整可卸载、最终另行删除现有 SDK 耦合”并允许创建 full-chain task？ | 接受；这是摆脱 fork 且保持硬 Gate 的最小可行边界 | 不接受则继续依赖 fork，升级和撤销成本持续增加 | 好，接受 | DEC-001 | prd.md、gate-contract.json |
| OQ-002 | 2026-07-15 | 是否确认四级难度路由、Lite 标准任务、条件式 Brainstorm、一次确认后自动闭环与受约束 Route override 的完整调整方案？ | 确认并作为 M5/M6 唯一当前合同 | 不确认则保留 Lite 0-confirmation 的历史合同，继续存在需求误解风险 | 已确认 | DEC-002 | prd.md、requirement package、design.md、implement.md |

- Open product/scope/risk questions: none — 当前架构、范围、风险容忍和任务创建均已确认；新不可逆决定才允许再次询问。

## Source Evidence

见同目录 `evidence-inventory.md`。
