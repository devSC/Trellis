---
name: client-design-overview-review
description: 用于审核 Flutter 客户端概要设计文档，判定能否进入详细设计。先做 EX 前置判定（判轨/包骨架/需求准入/项目约定），再按取证矩阵逐章审核：行为覆盖与粒度、owner 归属与分层依赖律、架构总览人审视图六件套、时序图策略闭合、技术决策合规依据、承接索引完整性；先证据后结论，输出分级 findings 与互斥三选一结论，并以用户终端 confirm 作为 Gate 收口。规则唯一来源是 `.trellis/spec/harness/overview/` 的 L1 SSOT。
---

# 客户端概要设计审核

> 层级契约：L1（`.trellis/spec/harness/overview/overview-structure-single-source.md`）承载规则正文与 G1~G8 完成条件；本 SKILL.md 只做前置判定、执行规则与审核流程；`references/review-baseline.md` 承载逐章取证矩阵与严重度判级，`references/review-output.md` 承载输出字段合同。冲突时 L1 > references > 本文件。

## 目标

- 审核概要设计是否达到进入详细设计的质量口径（L1 §6 G1~G8）。
- 只评审概要质量，不扩展到需求方向、视觉设计或实现方案。
- 基于文档证据输出问题清单与最小修订方案；先证据后结论。
- 架构总览（人审视图）是第一取证对象：评审者必须先能从六件套读懂"设计长什么样"，再进入逐章细查。

## 最小输入与自动补全

- 接受 task 目录、design_package 路径或单个 design-main.md/design.md 路径。
- 仅用于概要全稿完成后的门禁审核，不用于写作过程中的中间态审核。
- 候选文档不唯一时：能从 task.json `design_package` 或 README 唯一推断主文档则说明识别结果后继续；否则暂停向用户确认审核目标。

## 装载顺序与 EX 前置判定（任一失败 → 前置阻断输出，停止逐章审核）

1. 读 L1 主 SSOT；不可用 → 终止并提示先安装 guru spec 模板。
2. 读 `references/review-baseline.md`（取证矩阵）与 `references/review-output.md`（输出合同）。
3. 读 golden-path 与 project-conventions（校验 C1~C5）。
4. **EX-1 判轨**：task.json `guru_chain` 可判定；full 链 `design_package` 已声明。
5. **EX-2 包骨架（full 链）**：design_package 目录、README.md、design-main.md、chapters/ 齐全；light 链 design.md §1 存在。
6. **EX-3 需求准入**：需求产物可定位且有 P0/P1 核心能力；不可定位时，只有当概要已按 L1 §1-P4 记录显式假设才继续，否则前置阻断。
7. **EX-4 机器 Gate**：`python3 .trellis/scripts/guru/guru_gate.py overview <task_dir>` 通过（结构性缺口先由机检定位，人工审核聚焦语义）。

## 执行规则

1. 共享规范一律以 L1 为准；本 skill 与 references 不重复维护规范正文，逐项检查必须能回指 L1 章节号。
2. 先证据后结论：每条 finding 带章节锚点或明确缺失对象；引用正文优先给小节/表格行定位。
3. 架构就绪判定统一按 L1 §6 G1~G8 执行；G 项缺失即 P1，并在 finding 中标注受影响 G 项。
4. 分层依赖律违例（归属方向错、图中箭头逆向、外部直连越层）→ P1，**不得给出通过性结论**。
5. 图表与正文一致性是必查项：架构图组件 ⊆ 归属表；页面流图边 ↔ 行为集合；UC 承接表 bhv_refs ↔ BHV 双向闭合——任一向断链记 P1/P2（判级见 review-baseline）。
6. 时序图策略闭合（G7）：非豁免 UC 无可定位 sequenceDiagram、合并图缺覆盖清单、豁免缺理由、占位锚点残留 → P1。
7. 行为粒度按 L1 §3.1 四条判定；"处理登录"式粗粒度行为 → P1（不可直接展开详细设计）。
8. 技术决策承接按 L1 §2.6 字段合同逐条核查；涉权限/采集/三方域名缺 compliance_basis → P1；正文/示例出现真实 secret value → P1。
9. 概要越界（出现方法签名/字段合同/SDK 参数/DDL，L1 §5）→ P2 起步，并给最小回收方案（移入承接索引的 detail_expansion_targets）。
10. 承接索引核查：覆盖归属表全部 owner；doc_type 合法（详细 L1 §2 九分类）；full 链逐条有 chapters/<slug>.md 文件名；pending L2 命中而无豁免计划 → P1。
11. 命名按 L1 §4.1 抽查；Manager/Helper 类含混后缀或名词先行结构 → P2。
12. 发现需求层缺陷（行为缺失/矛盾）→ 结论标注"回退需求阶段"，不建议在概要补造。
13. 审核不重写设计：只给证据、影响与最小修订方案，不代写正文；修订形态建议按 L1 §8 区分局部修订 vs 文档级重构。
14. 概要文档无存量豁免：新文档必须全量符合 L1（存量豁免仅适用于实现阶段代码）。

## 审核流程

1. **结构识别**：对照 L1 §2 产物合同（按链型取轨道），记录各章存在性与位置；缺章记 P1。
2. **架构总览取证**（G6）：六件套逐件核查（一句话架构格式、架构图分层与方向、页面流图覆盖、UC 表/承接表列完整、策略表三选一）。
3. **行为覆盖核查**（G1）：逐条核对 P0/P1 核心能力 → 行为集合差集；抽查粒度（§3.1）。
4. **归属判定核查**（G2，核心）：逐行核查 owner 唯一性、三问实质性（"同上"式三问记 P2）、分层依赖律一致性、名词先行反模式。
5. **图文一致性核查**：规则 5 的三组双向核对。
6. **时序闭合核查**（G7）：逐 UC 按策略表核对 sequenceDiagram 可定位性、参与者真实性、编号与详述对应。
7. **合规核查**（G3/G8）：技术决策逐条字段 + compliance_basis + secret 扫描。
8. **承接索引核查**（G4）：owner 覆盖、doc_type 合法、逐文件、pending L2 豁免。
9. **越界核查**：L1 §5 禁写项扫描。
10. **汇总**：G1~G8 状态表 + findings 分级 + 互斥结论（输出合同见 review-output.md）。

## 输出（互斥分支）

- **前置失败**：仅输出前置缺口与修复动作（含"回退需求/补判轨/补骨架"指引），不展开逐章审核。
- **前置通过**：按 `references/review-output.md` 的字段合同输出——架构视图检查摘要 → 逐条 findings（severity/location/problem/suggestion）→ 结构概况 → G1~G8 状态表 → **三选一结论**（可进入详细设计 / 带明确假设可进入（列假设与验证时点）/ 不可进入（列阻塞 P1 清单））→ 修订形态建议。

## 边界约束

- 概要文档无存量豁免：新文档必须全量符合标准包。
- 审核不重写设计：只给证据、影响与最小修订方案，不代写正文。
- 发现需求层缺陷（行为缺失/矛盾）→ 结论标注"回退需求阶段"，不建议在概要补造。

## 与官方 Trellis skill 的边界

本 skill 是 Phase 1 内的概要 Gate 判定（人工触发），区别于 Phase 2/3 的 `trellis-check`（代码质检）。审核对象是概要主定义（full=design-main.md；light=design.md §1），不审代码。

## Gate 收口（人工确认）

结论为"可进入详细设计"（或带明确假设可进入且假设已记录）时，提请**用户本人**在终端运行：

```bash
python3 .trellis/scripts/guru/guru_gate.py confirm overview <task_dir>
```

agent 不得代跑（无 TTY 会被拒）；确认未落盘前不得进入详细设计。

## 参考资料

- 概要阶段中立规范（L1）：`.trellis/spec/harness/overview/overview-structure-single-source.md`
- 取证矩阵与严重度判级：`references/review-baseline.md`
- 输出字段合同：`references/review-output.md`
