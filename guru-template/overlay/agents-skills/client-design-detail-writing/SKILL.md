---
name: client-design-detail-writing
description: 按客户端详细设计标准包，把概要的 owner 与承接索引展开为可编码合同（合同八问）。按 detail_doc_type 分流到对应 L2 骨架；只引用 L1/L2 的合同与完成条件，不并行维护规则正文。规则唯一来源是 `.trellis/spec/harness/detail/` 的 SSOT。
---

# 客户端详细设计撰写

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取同级标准包 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；若不可用，终止并提示先安装 guru spec 模板（trellis init -t guru-flutter-client）。
2. 按本次涉及的 doc_type 读取对应 L2（`.trellis/spec/harness/detail/detail-type-*.md` 对应类型）；L2 为 pending 的类型按 L1 §3 合同八问展开，并在文档头标注 `l2_status: pending`。
3. 读取通用 golden-path 与**`.trellis/spec/conventions/project-conventions.md`**（校验 C1~C5）。
4. **WX-承接**：从概要文档的承接索引建立 `chapter_target → detail_doc_type` 目标集合；索引缺失/为空 → 终止并提示回退概要（L1 §1-P4），**禁止在详细阶段补造归属**。

## 边界约束

- 只承接概要已决定的 owner 与技术决策，展开为合同；不重新决定归属、技术栈、scope。
- 遵守 L1 §4 禁止补造清单：未选定的技术决策不拍板、不写超过签名级的代码。
- 命名/目录/序列化等一律按项目约定槽位取值，不自行发明。
- 本 Skill 只编排写作动作，规则疑义以标准包为准。

## 执行流程

1. **WX-1 目标集合确认**：列出本次要产出的设计单元清单（来自承接索引），逐条标注 doc_type。
2. **WX-2 逐单元展开**：按对应 L2（或 L1 八问）逐问作答；八问缺一不可，暂无法回答的写入未决问题而非留空。
3. **WX-3 追溯标注**：每个单元头部标注承接的概要行为编号与 owner；字段/接口/状态出现处反向引用。
4. **WX-4 测试映射**：逐行为给测试点（成功 + 全部失败路径），分层按 L1 八问之 7。
5. **WX-5 合规自查**：涉权限/数据采集/三方域名/PII 的单元附合规依据（L1 §5-G4）。
6. **WX-6 完成自检**：对照 L1 §5 G1~G5 输出轻量自检摘要。

## 输出

- 详细设计文档（建议路径：目标仓库 `docs/design/<feature>/detail-<doc_type>-<name>.md`，或小型 feature 单文档多章节）。
- 末尾附：G1~G5 自检摘要 + 未决问题清单。

## 修订

按 findings 修订前先按 L1 §7 判定局部修订 vs 文档级重构；发现概要缺陷（归属错/索引漏）→ 回退概要修订，不就地改归属。

## 与官方 Trellis skill 的边界

本 skill 在 Phase 1（planning）后段：把 `design.md` 概要章展开为详细合同章（九类 doc_type 合同八问）。`implement.md` 的执行计划仍按官方约定另行产出。
