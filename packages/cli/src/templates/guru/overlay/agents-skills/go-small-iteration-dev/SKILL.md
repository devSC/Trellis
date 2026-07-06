---
name: go-small-iteration-dev
description: Go 后端小需求端到端闭环编排：按入口决策树分流（碰哪几层、风险多大），按 low/medium/high 风险推荐 small_inline / micro_task / lite_task / full_chain，组合需求澄清、必要详细设计单元、实现与验证；高风险默认推荐完整 SDD 链，但用户可明确选择受支持 route 并记录风险确认。本 Skill 只编排流程，不维护任何写作/审核规范；规则唯一来源是各阶段标准包与通用 golden-path。
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
   - `low -> small_inline`：局部注释 / 格式 / 非共享配置 / 低风险日志字段等小改，且未命中高风险信号时，默认本轮 inline 处理，不创建完整 Trellis task，不要求 full Guru gate。
   - `low + commit -> micro_task`：同一低风险小改一旦需要 commit，必须创建或复用最小任务，写入任务目录 `gate-contract.json`，只承载 scoped commit contract，不进入完整规划链。
   - `medium -> lite_task`：局部业务行为、单层逻辑、小范围多文件或需要可复跑验证的变更，进入轻量链（prd 简版 + 所碰层 design 合同 + 实现/验证），采用 bounded review policy。
   - `high -> full_chain`：新服务、新协议端点、鉴权/会话、DB/schema 或 migration、跨服务契约、并发/生命周期、支付/权限/隐私或数据采集、workflow/hook/gate/runtime 或发布交付链，默认推荐完整五阶段（full 链，目录级设计包）；用户明确选择 `lite_task` / `micro_task` 等受支持 route 时，必须写入 route override 审计和风险确认。

   **判轨落盘**：`guru_chain` 仍只表达 `full|light` 的既有 Guru 产物形态；`gate-contract.json.route` 记录实际执行 route（`micro_task|lite_task|full_chain`），`assessment.recommended_route` 记录风险系统推荐，`route_selection` 记录用户选择、推荐值、风险确认与用户原话。`gate-degradations.jsonl` 只能追加真实发生的 gate/tool 失败与补偿检查证据，是事实记录，不是预授权绕行单。风险 route 是建议，不是强制；当用户选择比推荐更轻的 route，必须有 `route_selection.source=user_override`、`risk_acknowledged=true` 和非空 `user_quote`，后续 Gate 按实际 selected route 执行。

   **route review policy**：route 只能放宽 adversarial 证据要求，不能绕过结构 Gate、人工确认、当前 blocked/medium+ 证据、staged scope 或 implementation review digest。`small_inline` / `micro_task` 不要求 requirements adversarial review；`lite_task` 不强制 requirements adversarial review，overview/detail 仍需当前 digest 两条 clean，但不强制 adversarial reviewer；`full_chain`、`risk=unknown`、缺失或非法 contract 保持 strict gate 路径，且只有 `guru.supervision.adversarial_enabled=true` 时才默认要求 requirements adversarial review。高风险推荐 full 但用户确认选择 lite/micro 时，Gate 使用 selected route 的 bounded/micro policy；缺少 override audit 时仍 fail closed。lite 中低严重度文案 nit / P3 follow-up 可作为后续项，不强制刷新 PRD digest 或重跑 requirements review；若 review/supervise 发现范围扩大、验收变化或高风险信号，必须停下请用户确认扩 scope、保持当前 route 或改选 full，不能把 `evidence_ready` 静默改成 `user_confirmed`。

2. **需求澄清（简版）**：行为（Given/When/Then）+ 边界（不做什么）+ 验收（怎么算对）三要素；未决问题向用户提问（一次 1~4 个），不私自拍板。

3. **必要的详细设计单元**：对所碰 doc_type 产出合同八问（装载 `.trellis/spec/harness/detail/` 的 L1 + 命中 L2；pending 类型按 L1 八问 + L2 豁免口径）；小改可单文档多章节，但每章独立满足合同。

4. **实现与验证**：按 `go-implementation-guru-writing` 执行（含 `implement.md` / implementation-trace、逐片验证、存量违例处置、错误链与分层红线）。

5. **每步人工 Gate**：产物给用户过目后再进下一步，不一次推到底。

6. **收口输出**：结论 → 改动 → 验证证据 → 风险 → 下一步。

## 与流程 Skill 的组合

需要分支/worktree 隔离时组合 `sop-task-runner`：先用本 Skill 判定改动范围 → sop-task-runner 创建隔离 → 隔离内继续。

## 边界约束

- 本 Skill 不写规范正文；阶段产物的"什么算对"一律以对应标准包为准。
- 分流到完整 SDD 后，本 Skill 让位于 requirement → overview → detail → implementation 链路。
- 未知风险不得降为 low；扫描失败至少按 medium 处理，含高风险关键词或路径信号时推荐 high/full_chain；用户选择更轻 route 时必须记录 override audit。

## 与官方 Trellis skill 的边界

本 skill 补充官方 Request Triage：triage 判定"是否建任务"，本 skill 的入口决策树判定"碰哪几层、走轻量链还是完整五阶段"。高风险需求默认推荐完整链；用户明确覆盖时按合同审计和 selected route 执行。
