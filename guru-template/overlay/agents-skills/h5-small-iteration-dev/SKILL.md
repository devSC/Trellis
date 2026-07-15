---
name: h5-small-iteration-dev
description: H5/Next.js 小需求端到端闭环编排：按入口决策树分流（碰哪几层、风险多大），按 low/medium/high 风险推荐 small_inline / micro_task / lite_task / full_chain，组合需求澄清、必要详细设计单元、实现与验证；高风险必须走完整 SDD 链；用户要求较轻 route 只能记录偏好和风险确认，不能授权降级。本 Skill 只编排流程，不维护任何写作/审核规范；规则唯一来源是各阶段标准包与通用 golden-path。
---

# H5 小迭代闭环

## 装载顺序（硬前置，任一失败即终止）

1. 通用方法 SSOT `.trellis/spec/guides/golden-path.md`（入口决策树、H5 分层迷你路径、server-first 红线）。
2. `.trellis/spec/conventions/project-conventions.md`（校验 C1~C5，读取路由模式、状态管理、内容源、测试、lint、部署等槽位）。
3. 按分流结果装载对应阶段 Skill 的标准包（见执行流程）。

## 执行流程

1. **分流（必做第一步）**：按 golden-path §1 入口决策树判定需求碰哪几层：
   - 只改文案 / SEO metadata / 静态展示 → route 或 ui-component 迷你路径 + 自检。
   - 只改数据读取 / 内容源映射 → data-access 迷你路径，必要时承接 domain-type。
   - 只改表单提交 / mutation / route handler → server-action + data-access 迷你路径。
   - 只改交互态 → client-component + ui-component 迷你路径，确认 `'use client'` 最小化。
   - 整段页面或新 route feature → route + server-component/client-component + 所需下层全链。

   同时判定风险并按固定表路由：
   - `low -> small_inline`：局部 UI / 文案 / 注释 / 格式 / 非共享配置等低风险小改，且未命中高风险信号时，默认本轮 inline 处理，不创建完整 Trellis task，不要求 full Guru gate。
   - `low + commit -> micro_task`：同一低风险小改一旦需要 commit，必须创建或复用最小任务，写入任务目录 `gate-contract.json`，只承载 scoped commit contract，不进入完整规划链。
   - `medium -> lite_task`：局部业务行为、单层逻辑、小范围多文件或需要可复跑验证的变更，只做 compact intake，然后由当前主会话 host-inline 实现并运行 scoped deterministic_final；不生成 PRD/Overview/Detail，不确认，不派 Worker。
   - `high -> full_chain`：认证/会话、支付、权限/隐私或数据采集、server-action 写入、DB/schema、内容源迁移、缓存/`revalidate` 语义、跨层协议、workflow/hook/gate/runtime 或发布交付链，默认推荐完整五阶段（full 链，目录级设计包）；即使用户要求 `lite_task` 或 `micro_task`，也必须写入偏好审计并保持 `full_chain`；override 不能授权高风险降级。

   **判轨落盘**：`guru_chain` 仍只表达 `full|light` 的既有 Guru 产物形态；`gate-contract.json.route` 记录实际执行 route（`micro_task|lite_task|full_chain`），`assessment.recommended_route` 记录风险系统推荐，`route_selection` 记录用户选择、推荐值、风险确认与用户原话。`gate-degradations.jsonl` 只能追加真实发生的 gate/tool 失败与补偿检查证据，是事实记录，不是预授权绕行单。非高风险 route 可在合法 user override 审计后选择更轻 route；高风险 override 只记录用户偏好，不能授权 `lite_task` 或 `micro_task`，后续 Gate 必须要求 `full_chain`。

   **route review policy**：以 `gate-contract.json.route` 为执行权威。`small_inline` / `micro_task` 不进入 Full planning review；`lite_task` 固定为 compact intake → host-inline → scoped deterministic_final，确认 0、Worker 0、无 requirements/Overview/Detail/check-implementation；只有 `full_chain`、`risk=unknown`、缺失或非法 contract 进入 strict Gate。Lite 发现 scope expansion 或 high-risk 时先 re-intake 为 Full，不在 Lite 内补跑 Full Gate。

2. **Lite 执行**：记录 compact intake 和精确 scope，立即 host-inline 修改真实代码，执行与改动匹配的 focused check 并写入 mutable evidence。只有新增 high-risk 或 scope expansion 才停止并提升为 Full。

3. **Full 需求与设计**：只有 Full 才执行需求澄清、Overview、Detail、合同八问及其 review/confirm。

4. **实现与验证**：按 `h5-implementation-guru-writing` 执行（含 `implement.md` / implementation-trace、逐片验证、存量违例处置、server/client 边界与 secret 合规）。

5. **人工 Gate**：只在 Full/high-risk 的批量风险确认与不可逆边界使用；Lite 不逐步询问。

6. **收口输出**：结论 → 改动 → 验证证据 → 风险 → 下一步。

## 与流程 Skill 的组合

需要分支/worktree 隔离时组合 `sop-task-runner`：先用本 Skill 判定改动范围 → sop-task-runner 创建隔离 → 隔离内继续。

## 边界约束

- 本 Skill 不写规范正文；阶段产物的"什么算对"一律以对应标准包为准。
- 分流到完整 SDD 后，本 Skill 让位于 requirement → overview → detail → implementation 链路。
- 未知风险不得降为 low；扫描失败至少按 medium 处理，含高风险关键词或路径信号时推荐 high/full_chain；非高风险选择更轻 route 时必须记录 override audit，高风险请求更轻 route 只能记录偏好且必须 full_chain。

## 与官方 Trellis skill 的边界

本 skill 补充官方 Request Triage：triage 判定"是否建任务"，本 skill 的入口决策树判定"碰哪几层、走轻量链还是完整五阶段"。高风险需求必须执行完整链；用户明确覆盖时只能记录合同审计，不能按较轻 selected route 执行。
