---
name: requirement-review
description: 用于审核含前端（App/Web）、API-only 或 CLI-only 入口的产品需求文档。该技能仅用于需求全稿完成后的门禁审核，强制单一来源收敛；文档组织采用语义 SSOT 口径（README 导航 + requirement-main 第一章和第二章入口组织主定义），并要求先判定文档组织模式与审核口径再下结论。
---

# Requirement Review

## 目标

- 审核需求文档是否达到可进入设计或开发的质量口径。
- 只评审需求质量，不扩展到产品方向、视觉设计或实现方案。
- 基于文档证据输出问题清单和修订方案建议。
- 解决“先粗后细写作”与“单一来源完成收敛”之间的时态差异，避免前后审核口径摇摆。
- 按标准包 `5.2/7.0` 检查阶段 0 核心能力初版收敛与最终校正是否完成。
- 按标准包 `5.2` 检查核心能力是否聚焦重点/难点行为、避免退化为场景重排，并能承接概要设计与详细设计。

## 最小输入与自动补全

- 接受单个需求文档路径，或包含多份需求文档的目录路径。
- 该技能仅在需求文档全稿完成后调用，不用于阶段写作过程中的中间态审核。
- 输入是目录时，先识别主文档、模块文档、API 文档（若适用）、CLI 文档（若适用）和非功能文档。
- 候选文档不唯一时，若无法从 README、版本矩阵或用户指定路径唯一确定主文档/版本根，必须先暂停确认审核目标；只有主文档与版本根可唯一推断时，才说明识别结果与假设后继续审核。
- 识别用户是否在需求文档或审核指令中声明非功能范围豁免；优先采用已声明口径，只有声明冲突或无法判定且会影响审核结论时才暂停确认。

## 执行前置判定（输出顺序仍以 references/review-output.md 为准）

### 1) 文档组织模式

- 目标口径为语义 SSOT：README 仅导航，`requirement-main.md` 承载第一章/第二章入口组织主定义。
- 第三章起详细内容可采用模块化拆分或聚合详细文档。
- 若不满足语义 SSOT（如双主定义、边界混乱、不可追踪），不给出通过性结论；仅输出前置缺口与修订方案，不展开后续逐章门禁审核。

### 2) 审核口径

口径判定规则：
- 默认且唯一口径：门禁审核（用于整体复审/发布前/进入下一阶段）。

### 3) 核心能力目标一致性

- 核心能力目标、来源/归属、`top_level / derived` 分层、设计承接与反模式统一以标准包 `5.2` 为准。
- 若核心能力清单退化为“场景重列/场景重排/功能全量打包”，不得给出通过性结论。

## 执行规则

1. 必须先读取同级标准包主定义 `../requirement-doc-standard/references/requirement-structure-single-source.md`（从本 Skill 目录解析），以中立主定义确认组织结构与完成口径；若该文件不可用，终止并提示先安装 `requirement-doc-standard`。
2. 再判定文档组织模式与审核口径，建立章节覆盖表。
3. 先用 `rg` 与 `rg --files` 建立术语和文档索引，再逐章审核。
4. 先引用证据，再下结论；优先用 `nl -ba` 固化行号。
5. 默认按基线全量检查；对按标准包 `5.3` 或审核指令声明的非功能豁免项，只检查豁免清晰度与风险声明。
6. API/CLI 适用性按标准包 `requirement-structure-single-source.md` 的“API/CLI 适用标准”判定。
7. 必须按标准包 `5.2/7.0` 核查核心能力定义是否存在，以及阶段 0 三产物、字段合同、优先级、证据状态、设计承接、`top_level / derived` 分层与反模式是否满足要求；本技能不重复维护字段级判定规则。
8. 必须核查 `confirmation_status` 与 `open_questions` 是否满足进入概要设计的条件；`P0/P1` 核心能力若仍为 `ai_drafted`，或存在会改变范围/验收口径的高风险 `open_questions`，不得判定“可进入概要设计”；`evidence_ready` 只代表 AI 证据已收敛，不是用户确认，可在假设明确且无高风险待确认问题时放行，但不得当作 `user_confirmed*`。
9. 本技能只判断核心能力是否达到进入概要设计的文档条件，不替代用户完成业务确认，不得把核心能力状态写成 `user_confirmed` 或 `user_confirmed_with_edits`。
10. 必须核查 one-question loop 证据：P0/P1、范围、验收、合规、API/数据合同、付费、账号或安全决策若写成 `user_confirmed*`，同一决策条目或直接子块必须至少有 `user_quote` 或 `confirmed_ref`；缺失时按 `REQ_BLOCKER` 输出。
11. `Brainstorm Evidence` 必须具备可审计证据。高风险 confirmed decision 必须满足二选一：有结构化 `Question Loop Log`（`oq_id | asked_at | question | recommended_answer | tradeoff | user_quote | resolved_decision | artifact_update`），或有 `Question Policy` 且 `question_policy: evidence_only|mixed` 明确说明哪些问题由证据回答、哪些由用户当前轮确认。缺失时按 `PROCESS_DEFECT` 输出；若把原始 bug/source quote 当作当前轮 `user_quote` 或在 `evidence_only` 下写 `user_confirmed*`，按 `REQ_BLOCKER` 输出。
12. 若存在多个 high-risk `open_questions`，审核下一步是否只保留一个 `next_question` / `next_action`，并声明其他 OQ 保持 open；缺失时按 one-question loop 流程缺陷处理。
13. 批量确认只在当前用户消息明确覆盖多个 OQ / decision id 时成立；每个被标记 confirmed 的问题必须有独立 `user_quote` 或 `confirmed_ref` 并记录覆盖的 OQ id / decision id。模糊“继续”“好”“按推荐”不得让多个 OQ 同时变为 confirmed，必须回退到单个 `next_question`。
14. 历史 `user_confirmed*` 或历史 `user_quote` 只可作为它已经确认的决策的审计证据；不得作为本轮 current-turn approval 来提升其他决策状态、删除仍 open 的高风险 OQ、进入 overview/detail 或运行 `task.py start`。
15. 核心能力反模式命中后的严重度按 `references/review-baseline.md` 的严重度规则判定，不机械把所有 P2 视为阻断项。
16. 必须核查 API/CLI 适用性判定依据是否明确（适用/不适用 + 理由）且引用标准包“API/CLI 适用标准”；缺失判定依据按 `references/review-baseline.md` 的严重度规则赋级。
17. API/CLI（若适用）必查：按标准包第 `6` 章与 `6.1` 核查入口分支追踪、业务意图回指、复用/拆分条件与差集分类；API 同时按标准包第 `5` 章检查 `必要步骤` 覆盖与契约单一来源，CLI 同时检查命令语义、参数、退出码契约及其与 API 文档的解耦关系。
18. 编号契约必查：按标准包第 `6` 章与 `6.1` 核查 `REQ-UC-XXX`、`API-INTENT-XXX`（若适用）、`CLI-INTENT-XXX`（若适用）的完整性、稳定性、入口分支追踪与差集结果。
19. 编号差集分类、真实 `UC-接口映射豁免` 的声明主体统一引用标准包第 `6` 章；缺失映射赋级按 `references/review-baseline.md` 的严重度规则处理；API/CLI 整体不适用或 UI-only 正常不映射不得按豁免缺失处理。
20. 跨文档必查：单向维护、主从一致性、版本矩阵与引用链一致性。
21. 对“重复定义”按 `references/review-baseline.md` 的严重度规则判定严重度与阻断口径。
22. “第一章/第二章是否缺失”按文档集判定，不按 README 单文件判定。
23. 阻断与放行结论按 `references/review-baseline.md` 的严重度规则输出。
24. 若存在真实 `UC-接口映射豁免` 但缺少豁免原因或必要影响说明，按 `references/review-baseline.md` 的严重度规则赋级；API/CLI 整体不适用或 UI-only 正常不映射不得按豁免缺失处理。
25. 输出 Finding 的建议或修订方案时，必须按标准包第 `12` 章区分局部产物缺口与需求文档结构/语义模型缺陷；结构、归属或合同缺陷不得建议用局部补写保留错误模型。

## 审核流程

1. 开始评审前读取 `references/review-baseline.md`。
2. 识别文档结构，记录：文档组织模式、审核口径、第一章主定义位置、第二章入口组织主定义位置、章节映射与豁免清单；若语义 SSOT 前置不满足，输出前置缺口后停止。
3. 先审核“阶段 0：核心能力初版收敛与最终校正”与第一章核心能力定义，再按产品总述、入口组织结构（有 UI 时包含页面组织结构）、页面详细描述（若适用）、服务端 API（若适用）、CLI Command（若适用）、非功能需求逐章审核。
4. 执行一致性、可测试性、适度性、实用性交叉检查。
5. 输出 findings（按 P1/P2/P3）与必要结论；仅在用户要求或复杂文档需要说明覆盖情况时输出审核矩阵。
6. 在总结中明确：是否可进入下一阶段，以及前提条件。

## 输出要求

- 输出分支、字段与顺序以 `references/review-output.md` 为唯一主定义，本文件不再重复维护第二份字段清单。
- 若语义 SSOT 前置不满足，按 `references/review-output.md` 的“前置失败输出”仅输出前置缺口与修订方案。
- 若语义 SSOT 前置通过，按 `references/review-output.md` 的“常规门禁输出”输出 Findings、必要结构概况与总结；每条 Finding 包含严重度、位置、问题、建议。
- 若模板与其他说明冲突，以 `references/review-output.md` 为准。

## 命令建议

- 用 `rg` 搜索功能名、入口名、页面名（若适用）、API/CLI 名、命令名和关键术语。
- 用 `rg --files` 建立目录型文档清单。
- 用 `nl -ba` 和 `sed -n` 抽取可引用证据。

## 参考资料

- 需求文档体系中立主定义：同级标准包 `../requirement-doc-standard/references/requirement-structure-single-source.md`（从本 Skill 目录解析）
- 审核基线与详细检查矩阵：`references/review-baseline.md`
- 输出模板与复审闭环：`references/review-output.md`
- 最小示例模板（共享）：`../requirement-doc-standard/references/examples/unique-structure-minimal/`（从本 Skill 目录解析）
