---
name: client-design-overview-review
description: 按客户端概要设计标准包审核概要设计文档，判定能否进入详细设计。检查行为覆盖、owner 归属与分层依赖律一致性、技术决策合规依据、承接索引完整性；先证据后结论，输出分级 findings 与互斥结论。规则唯一来源是 `.trellis/spec/harness/overview/` 的 SSOT。
---

# 客户端概要设计审核

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取同级标准包主定义 `.trellis/spec/harness/overview/overview-structure-single-source.md`，**以中立主定义确认产物合同与完成口径**；若不可用，终止并提示先安装 guru spec 模板（trellis init -t guru-flutter-client）。
2. 读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律为归属判定依据）。
3. 读取**`.trellis/spec/conventions/project-conventions.md`** 并执行校验清单 C1~C5。
4. 定位被审概要文档与其上游需求产物。

## 执行流程

1. **EX-1 结构识别**：对照标准包 §2 产物合同，记录各章节存在性与位置；任何必含章节缺失 → 记 P1。
2. **EX-2 行为覆盖核查**（对应 G1）：逐条核对需求 P0/P1 核心能力是否被行为集合覆盖，列出差集。
3. **EX-3 归属判定核查**（对应 G2，核心）：逐行核查归属表——owner 唯一性、三问理由充分性、**分层依赖律一致性（违例直接 P1，不得给出通过性结论）**、名词先行反模式（无行为来源的 Manager/Helper）。
4. **EX-4 合规核查**（对应 G3）：涉权限/数据采集/三方域名的技术决策是否附合规依据。
5. **EX-5 承接索引核查**（对应 G4）：`chapter_target → detail_doc_type` 是否非空、是否覆盖归属表全部 owner、doc_type 取值是否合法（详细标准包九分类）。
6. **EX-6 阶段边界核查**：概要是否越界展开字段级合同/方法签名/DDL（标准包 §5）→ 越界记 P2 并给最小回收方案。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口与修复动作，不展开逐章审核。

**前置通过时**：
1. 逐条 findings：`severity(P1/P2/P3) / location(章节锚点) / problem / suggestion(最小修订方案)`——先证据后结论，每条必须带锚点或明确缺失对象。
2. 结构概况（一段话）。
3. **结论（三选一）**：可进入详细设计 / 带明确假设可进入（列出假设与验证时点）/ 不可进入（列出阻塞 P1 清单）。
4. 修订形态建议：按标准包 §8 标注每条 P1/P2 属局部修订还是文档级重构。

## 边界约束

- 概要文档无存量豁免：新文档必须全量符合标准包。
- 审核不重写设计：只给证据、影响与最小修订方案，不代写正文。
- 发现需求层缺陷（行为缺失/矛盾）→ 结论标注"回退需求阶段"，不建议在概要补造。

## 与官方 Trellis skill 的边界

本 skill 是 Phase 1 内的概要 Gate 判定（人工触发），区别于 Phase 2/3 的 `trellis-check`（代码质检）。审核对象是 `design.md` 概要章，不审代码。
