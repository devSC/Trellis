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

- Micro 默认 0 次确认；Lite 最多 1 批；Full 最多 2 批，且相同输入不得重复询问。
- 每个确认项必须包含建议答案、影响和选择不同方案的代价。
- 可由仓库事实、现有规范或可逆默认值决定的事项由 Agent 自主决定。

### R5. Semantic digest dependency graph

- requirements、overview、detail、implementation scope 和 execution evidence 使用独立 digest。
- 仅真实依赖该变化的下游证据失效；无关章节、格式、时间戳和 append-only execution evidence 不得让上游 review 失效。
- Lite `design.md §2` 变化不得使未变化的 `§1` Overview review stale。

### R6. Independent and convergent review

- Review evidence 记录 reviewer、worker、thread/context identity 和输入 digest；两个 run-id 不能替代独立 reviewer 证明。
- Review 次数按风险配置：低风险零次或机械检查，Lite 最多一次独立语义 review，Full 仅在必要时两次独立 review。
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

- 将两个失控会话抽象为 replay fixture：digest 震荡、重复 review、scope 扩张、无业务 diff、长等待和上下文膨胀。
- 建立 route matrix、digest metamorphic、reviewer independence、budget/stagnation、scope expansion、confirmation、context/token、reversibility、mirror/design-sync 测试。
- 建立覆盖全部任务类型的端到端 benchmark；单元测试全绿但仍出现长时间 planning + 零业务 diff 时，发布失败。

## Acceptance Criteria

- [ ] 功能实现期间 `git diff -- packages/cli/src packages/core` 无新增 Guru 功能修改。
- [ ] `guru-template/index.json` 完整登记 Flutter、Go、H5、iOS 的 workflow/spec，官方 marketplace resolver 可解析。
- [ ] 干净的官方 Trellis 项目不安装 fork 包即可安装并运行 Guru Template + Extension。
- [ ] Extension 支持 `plan/apply/status/unapply/verify`，重复 apply 幂等，修改过的用户文件不会在卸载时删除。
- [ ] `apply -> verify -> unapply` 在 fixture 项目中恢复安装前等价状态。
- [ ] Inline/Micro/Lite/Full/Review/Research/Repeated Debug 均有明确 artifact、预算、确认和停止策略。
- [ ] Lite detail-only 修改不改变 Overview digest；真实上游变化按依赖图精确失效。
- [ ] 同一 reviewer/context 伪造两个 run-id 不能满足独立 review。
- [ ] Scope/layer/risk 扩张会在继续实现前触发重新 intake，并只请求新增决定。
- [ ] 两个失控会话 replay 在预算内进入真实代码或返回明确终止状态，不再出现 98 分钟 planning + 零业务 diff。
- [ ] Micro 默认 0 次确认、Lite <= 1 批、Full <= 2 批；相同输入确认不会重复。
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

### Question Loop Log

| oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OQ-001 | 2026-07-14 | 是否接受“官方 Custom-first、功能阶段 Core 零修改、扩展包完整可卸载、最终另行删除现有 SDK 耦合”并允许创建 full-chain task？ | 接受；这是摆脱 fork 且保持硬 Gate 的最小可行边界 | 不接受则继续依赖 fork，升级和撤销成本持续增加 | 好，接受 | DEC-001 | prd.md、gate-contract.json |

- Open product/scope/risk questions: none — 当前架构、范围、风险容忍和任务创建均已确认；新不可逆决定才允许再次询问。

## Source Evidence

见同目录 `evidence-inventory.md`。
