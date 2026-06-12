---
name: client-design-detail-review
description: 按客户端详细设计标准包审核详细设计文档，判定能否进入编码。核查合同八问完整性、概要 owner 追溯、测试映射覆盖、禁止补造红线与合规依据；先证据后结论，输出分级 findings 与互斥结论。规则唯一来源是 `.trellis/spec/harness/detail/` 的 SSOT。
---

# 客户端详细设计审核

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取同级标准包 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`，以中立主定义确认合同与完成口径；若不可用，终止并提示先安装 guru spec 模板。
2. 按被审文档涉及的 doc_type 读取对应 L2。
3. 读取通用 golden-path 与**`.trellis/spec/conventions/project-conventions.md`**（校验 C1~C5）。
4. **EX-承接**：概要文档可定位，承接索引存在且可建立完整非空的 `chapter_target → detail_doc_type` 映射；失败 → 只输出前置缺口（含"回退概要"指引），不展开诊断。

## 执行流程（逐设计单元诊断）

1. **D1 覆盖核查**（G1）：承接索引每个条目是否都有对应设计单元；列出差集。
2. **D2 八问完整性**（G2）：逐单元核对合同八问；缺项 = P1。
3. **D3 追溯核查**（G2）：字段/接口/状态是否可追溯到概要 owner；单元是否为概要之外新增结构（红线，P1）。
4. **D4 分层一致性**：依赖声明对照分层依赖律与对应 L2 硬规则（controller 注入 repository、repository 绕 datasource、usecase 环依赖等 = P1）。
5. **D5 测试映射**（G3）：逐行为核对测试点，成功 + 失败路径全覆盖；漏失败路径 = P2 起步，高风险链路漏测 = P1。
6. **D6 合规核查**（G4）：权限/数据采集/三方域名/PII 单元的合规依据；制裁 TLD、私有 API、动态执行类设计 = P1。
7. **D7 补造红线**（L1 §4）：未选定技术决策被拍板、超签名级代码、偏离项目约定槽位取值 = P1。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口与修复动作。

**前置通过时**：
1. 逐条 findings：`severity(P1/P2/P3) / location / problem / suggestion(最小修订方案)`，先证据后结论。
2. 逐单元概况表（doc_type / 八问完整度 / 追溯状态 / 测试映射状态）。
3. **结论（三选一）**：可进入编码 / 带明确假设可进入 / 不可进入（列阻塞 P1）。
4. 修订形态建议（L1 §7：局部修订 vs 文档级重构；概要缺陷标注"回退概要"）。

## 边界约束

- 详细设计文档无存量豁免；审核不代写合同正文。
- 审核项必须能回到 L1/L2 的正向方法，不做"有没有写某个词"的形式检查。

## 与官方 Trellis skill 的边界

本 skill 是 Phase 1 的详细 Gate 判定：`design.md` 详细章不达标不得 `task.py start`。区别于 `trellis-check`（实现后代码质检）。
