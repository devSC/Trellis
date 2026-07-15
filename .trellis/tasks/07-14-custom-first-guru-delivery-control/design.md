# Custom-first Guru Delivery Control Plane Design

本任务是 `guru_chain=full` 的高风险控制面改造，正式设计 SSOT 位于：

- 导航：[`design-package/README.md`](design-package/README.md)
- 概要主定义：[`design-package/design-main.md`](design-package/design-main.md)
- 详细设计：[`design-package/chapters/`](design-package/chapters/)

## 摘要

设计以官方 Custom-first、功能阶段 Trellis Core 零修改、完整可卸载为边界。自 2026-07-15 起，交付由 `prd.md` 与 requirement package 的 M0-M4 outcome milestones 驱动；内部模块、slice 数量、bootstrap burn 和 reviewer identity 基础设施不是完成标准。

本文件仅保留任务入口和摘要；正式设计包作为历史设计与可选实现参考保留。若设计包与当前 outcome milestones 冲突，以 requirement package 和 `prd.md` 的最新里程碑为准。
