---
name: requirement-doc-standard
description: 需求文档体系标准包（中立规范），用于定义语义SSOT、阶段写作合同与完成收敛口径，供 requirement-writing 与 requirement-review 共同引用。
---

# Requirement Doc Standard

## 目标

- 提供需求文档体系的单一来源写作合同，避免写作与复核口径漂移。
- 把“阶段 0：核心能力收敛”定义为进入概要设计前必须完成的需求产物，统一顶层/派生核心能力的定义与提取口径。
- 集中定义 API/CLI 适用标准，避免“默认必有”或多处判定不一致。
- 集中定义第二章入口组织口径、编号追踪与完成判定，避免写作与复核各维护一套判定标准。
- 集中定义非功能范围豁免的最小记录口径，避免写作输出与审核输出各维护一套豁免字段。
- 集中定义需求文档的产物修订形态判定，指导写作、自检与按 Findings 修订时区分局部修订和文档级重构。
- 作为中立标准包被其他 skill 引用，不承载业务实现或具体执行编排逻辑。

## 使用方式

- 规范主定义：`references/requirement-structure-single-source.md`
- 要求由 `requirement-writing` 与 `requirement-review` 在执行前读取。
- 未安装本标准包时，调用方应终止并提示先完成安装。

## 版本管理

- 建议在变更中注明标准版本与影响范围。
