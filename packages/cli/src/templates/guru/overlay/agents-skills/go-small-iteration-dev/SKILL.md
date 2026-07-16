---
name: go-small-iteration-dev
description: Go 后端小需求端到端闭环编排：按入口决策树分流（碰哪几层、风险多大），按 low/medium/high 风险推荐 small_inline / micro_task / lite_task / full_chain，组合需求澄清、必要详细设计单元、实现与验证；高风险必须走完整 SDD 链；用户要求较轻 route 只能记录偏好和风险确认，不能授权降级。本 Skill 只编排流程，不维护任何写作/审核规范；规则唯一来源是各阶段标准包与通用 golden-path。
---

# Go 后端小迭代闭环

## 装载顺序（硬前置，任一失败即终止）

1. 通用方法 SSOT `.trellis/spec/guides/golden-path.md`（入口决策树、Go 分层迷你路径、轻框架与错误链红线）。
2. `.trellis/spec/conventions/project-conventions.md`（校验 C1~C5，读取 DI/ORM/日志/API 风格/lint/迁移/鉴权/存量违例等槽位）。
3. 按分流结果装载对应阶段 Skill 的标准包（见执行流程）。

## 执行流程

1. **分流（必做第一步）**：按 golden-path §1 入口决策树判定需求碰哪几层：
   - 只改注释 / 文档 / 日志字段 / 非共享配置默认值 → 对应迷你路径 + 自检。
   - 只改 transport 入参/响应/状态码映射 → entry-api/transport 迷你路径，确认 service sentinel error 已存在。
   - 只改业务编排 → biz/service 迷你路径，确认 repository/domain 依赖边界。
   - 只改数据查询 / repository / 迁移 → repository-data 迷你路径，确认事务、错误转换、迁移 up/down。
   - 新 endpoint / 新服务 / 跨服务契约 / 鉴权会话 / DB schema / 生命周期装配 → 走全链判定。

   同时判定风险并按固定表路由：
   - `small_inline`：需求完全明确、机械且不改变行为合同的局部注释 / 格式 / 非共享配置 / 低风险日志字段变更；默认不创建完整 task。commit 是交付动作，初始要求 commit 时只补最小提交合同。
   - `micro_task`：需求完全明确、低风险、路径有界，但改变一个局部行为合同；创建或复用最小任务和 `gate-contract.json`，不进入完整规划链。
   - `lite_task`：无 High-risk 的局部业务行为、单层逻辑或小范围多文件变更，但仓库取证后仍可能有产品/范围/验收歧义。必须用官方 `task.py create` 建标准 Trellis task，任务内维护 compact `prd.md`；必要时 bounded Brainstorm，用户确认当前 requirements digest 一次后 host-inline 实现并运行 scoped deterministic_final，Worker 0、无 Overview/Detail planning review。
   - `high -> full_chain`：新服务、新协议端点、鉴权/会话、DB/schema 或 migration、跨服务契约、并发/生命周期、支付/权限/隐私或数据采集、workflow/hook/gate/runtime 或发布交付链，默认推荐完整五阶段（full 链，目录级设计包）；即使用户要求 `lite_task` 或 `micro_task`，也必须写入偏好审计并保持 `full_chain`；override 不能授权高风险降级。

   **判轨落盘**：`gate-contract.json` 记录 selected/recommended Route、`selection_source`、`selection_generation` 与 `scope_fingerprint`。更重 override 直接允许；更轻 override 必须满足目标 eligibility；High-risk/unknown-high 不能降级。首次写入前可合法降级，首次写入后只允许升级。

   **route review policy**：Small/Micro 确认 0；Lite=标准 task→repo evidence→必要 Brainstorm→compact requirements→确认一次→host-inline→scoped deterministic_final，Worker 0、无 Overview/Detail/check-implementation；Full 在实现前完成 current risk/decision evidence 与一批确认。Lite 发现 scope expansion 或 High-risk 时在下一次写入前升级 Full。

2. **Lite 执行**：官方创建标准任务，先查 repo evidence；只对真实歧义运行 bounded Brainstorm。compact requirements 与 Brainstorm Evidence 写入 task-local `prd.md`，用户确认当前 digest 后自动 start、host-inline 实现、focused check、mutable evidence、Spec 同步和可逆 commit-ready。

3. **Full 需求与设计**：只有 Full 才执行正式需求、Overview、Detail 与风险包；实现前把当前需求、critical/high risk 和关键不可逆设计决定合并为一批用户确认。

4. **实现与验证**：按 `go-implementation-guru-writing` 执行（含 `implement.md` / implementation-trace、逐片验证、存量违例处置、错误链与分层红线）。

5. **人工 Gate**：Small/Micro/Lite/Full=`0/0/1/1 batch`；Lite/Full 确认后自动推进，只有 scope/digest 实质变化、新 High-risk 或新不可逆决定才重新确认。

6. **收口输出**：结论 → 改动 → 验证证据 → 风险 → 下一步。

## 与流程 Skill 的组合

需要分支/worktree 隔离时组合 `sop-task-runner`：先用本 Skill 判定改动范围 → sop-task-runner 创建隔离 → 隔离内继续。

## 边界约束

- 本 Skill 不写规范正文；阶段产物的"什么算对"一律以对应标准包为准。
- 分流到完整 SDD 后，本 Skill 让位于 requirement → overview → detail → implementation 链路。
- 未知风险不得降为 low；扫描失败至少按 medium 处理，含高风险关键词或路径信号时推荐 high/full_chain；非高风险选择更轻 route 时必须记录 override audit，高风险请求更轻 route 只能记录偏好且必须 full_chain。

## 与官方 Trellis skill 的边界

本 skill 补充官方 Request Triage：triage 判定"是否建任务"，本 skill 的入口决策树判定"碰哪几层、走轻量链还是完整五阶段"。高风险需求必须执行完整链；用户明确覆盖时只能记录合同审计，不能按较轻 selected route 执行。
