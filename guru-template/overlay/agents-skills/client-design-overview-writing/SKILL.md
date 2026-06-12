---
name: client-design-overview-writing
description: 按客户端概要设计标准包撰写概要设计文档。从需求核心能力出发，枚举行为空间、判定 owner 归属、产出技术决策承接与详细设计承接索引。只编排写作动作，不复写共享规范正文；规则唯一来源是 `.trellis/spec/harness/overview/` 的 SSOT。
---

# 客户端概要设计撰写

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取同级标准包主定义 `.trellis/spec/harness/overview/overview-structure-single-source.md`，确认产物合同与完成口径；**若该文件不可用，终止并提示先安装 guru spec 模板（trellis init -t guru-flutter-client）**。
2. 读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`——归属判定基准。
3. 读取**`.trellis/spec/conventions/project-conventions.md`** 并执行其校验清单 C1~C5；**不可读或校验不过，终止并提示先填写项目约定**。
4. 定位需求产物（需求文档 + 核心能力清单 P0/P1）。缺失时按标准包 §1-P4 走显式假设路径。

## 边界约束

- 信息不足时收敛到最小可写范围，**不擅自补齐高风险业务规则**；未决问题显式列出并暂停向用户提问（一次 1~4 个关键问题）。
- 坚持概要阶段边界（标准包 §5）：不写字段级合同、方法签名、DDL、代码。
- 不得凭空生成 P0/P1 核心能力；不得替用户确认未决业务规则。
- 本 Skill 只编排写作动作；任何规则疑义以标准包为准，不在此另行定义。

## 执行流程

1. **WX-1 输入确认**：列出承接的 P0/P1 核心能力编号、技术栈约束、显式假设。
2. **WX-2 行为枚举**：按标准包 §3 四类顺序枚举（用户操作 → 系统反应 → 失败路径 → 生命周期），逐条 Given/When/Then。
3. **WX-3 归属判定**：按标准包 §4 判定表给每条行为/状态唯一 owner + 三问理由；对照分层依赖律自检无违例。
4. **WX-4 页面流与路由**（UI 需求）：页面导航、入参出参；非 UI 需求显式标注 N/A。
5. **WX-5 技术决策承接**：产出 `technology_decision_handoff[]`；涉权限/数据采集/三方域名的条目必须附合规依据。
6. **WX-6 承接索引**：产出 `chapter_target → detail_doc_type` 映射，自检覆盖归属表全部 owner。
7. **WX-7 完成自检**：对照标准包 §6 G1~G5 输出轻量自检摘要（逐项 通过/失败/N-A + 一句话证据）。

## 输出

- 概要设计文档（建议路径：目标仓库 `docs/design/<feature>/overview.md`，含标准包 §2 全部章节）。
- 末尾附：G1~G5 自检摘要 + 显式假设清单 + 高风险未决问题（仅此三类，不展开复述正文）。

## 修订

按 findings 修订前，先按标准包 §8 判定**局部修订 vs 文档级重构**，再动笔；发现需求缺陷回退需求阶段，不在概要补造。

## 与官方 Trellis skill 的边界

本 skill 在 Phase 1（planning）由 workflow 路由：`trellis-brainstorm` 负责需求探索产出 `prd.md`；本 skill 承接 prd 产出 `design.md` 的概要章（行为→owner→承接索引）。不替代 brainstorm，不进入详细合同。
