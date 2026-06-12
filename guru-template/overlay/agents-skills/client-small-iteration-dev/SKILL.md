---
name: client-small-iteration-dev
description: 客户端小需求端到端闭环编排：按入口决策树分流（碰哪几层、风险多大），组合需求澄清、详细设计单元、实现与验证；高风险需求升级到完整 SDD 链。本 Skill 只编排流程，不维护任何写作/审核规范；规则唯一来源是各阶段标准包与通用 golden-path。
---

# 客户端小迭代闭环

## 装载顺序（硬前置，任一失败即终止）

1. 通用方法 SSOT `.trellis/spec/guides/golden-path.md`（入口决策树与分层迷你路径）。
2. `.trellis/spec/conventions/project-conventions.md`（校验 C1~C5）。
3. 按分流结果装载对应阶段 Skill 的标准包（见执行流程）。

## 执行流程

1. **分流（必做第一步）**：按 golden-path §1 入口决策树判定需求碰哪几层：
   - 只改文案 → l10n 迷你路径（§7）+ 自检。
   - 只接后端接口 → network + data 迷你路径（§5→§4）。
   - 只改业务规则/编排 → domain 迷你路径（§3）。
   - 整页 feature → presentation + 下层全链（§6 + 所需下层）。

   同时判定风险：**核心玩法 / 付费 / 广告 / 存档 / 涉权限或数据采集 → 停止轻量链**，建议升级完整 SDD（requirement-writing 起步），等待用户确认。

2. **需求澄清（简版）**：行为（Given/When/Then）+ 边界（不做什么）+ 验收（怎么算对）三要素；未决问题向用户提问（一次 1~4 个），不私自拍板。

3. **必要的详细设计单元**：对所碰层产出合同八问（装载 `.trellis/spec/harness/detail/` 的 L1 + 对应 L2）；小改可单文档多章节，但每章独立满足合同。

4. **实现与验证**：按 `flutter-implementation-guru-writing` 执行（含 implementation-trace、逐片验证、存量豁免处置）。

5. **每步人工 Gate**：产物给用户过目后再进下一步，不一次推到底。

6. **收口输出**：结论 → 改动 → 验证证据 → 风险 → 下一步。

## 与流程 Skill 的组合

需要分支/worktree 隔离时组合 `sop-task-runner`：先用本 Skill 判定改动范围 → sop-task-runner 创建隔离 → 隔离内继续。

## 边界约束

- 本 Skill 不写规范正文；阶段产物的"什么算对"一律以对应标准包为准。
- 分流到完整 SDD 后，本 Skill 让位于 requirement → overview → detail → implementation 链路。

## 与官方 Trellis skill 的边界

本 skill 补充官方 Request Triage：triage 判定"是否建任务"，本 skill 的入口决策树判定"碰哪几层、走轻量链还是完整五阶段"。高风险需求一律升级完整链。
