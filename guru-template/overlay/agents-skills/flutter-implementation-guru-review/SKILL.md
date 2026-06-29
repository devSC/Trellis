---
name: flutter-implementation-guru-review
description: 按通用 golden-path 与实现标准包审核 Flutter 代码改动，判定能否进入 PR。核查与详细设计合同的一致性、分层依赖律与 canonical 写法、验证证据完整性、注释/日志/文档路径追溯、合规红线，并执行存量豁免判定（存量记债不阻塞、新增违例阻塞）。标准口径住 `.trellis/spec/harness/implementation/`。
---

# Flutter 实现审核

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（判定基准唯一来源）。
2. 读取同级标准包 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（含实现 Gate 口径）。
3. 读取**`.trellis/spec/conventions/project-conventions.md`**，**重点装载 SLOT-15 存量违例清单**（存量豁免判定的数据源），并确认项目 logger / logging helper / 日志门面。
4. 定位：被审改动（diff/分支）、详细设计文档、implementation-trace。trace 缺失 → 前置失败（证据载体不存在）。

## 执行流程

1. **D1 合同一致性**（G1）：diff 与详细设计单元逐一对照——合同外新增结构、未实现的承接行为，列差集；trace §4 是否记录偏差与处置。**SSOT 否决闸**：注入的正式 requirement/design 包是**行级权威基线**；任何 reviewer 建议（含自身判断或外部审查器如 OCR）与 SSOT 行级约束冲突时**一律否决、不得采纳**——以 SSOT 为准，不让外部建议把违反需求/设计的改动放行。
2. **D2 分层与 canonical**：对照 golden-path §2/§10 逐项检查改动代码——import 方向（data→usecase、controller→repository/API）、接口分离、DI 形态（binding `new`、`build()` 里 `Get.put`、`permanent` 滥用）、datasource 必经、异常不吞、硬编码尺寸、序列化方案与目录槽位（SLOT-01/02/11/12）。
3. **D3 存量豁免判定**（G4，逐违例必做）：每个发现的违例对照 SLOT-15——
   - 命中清单且未扩大违例面 → **tech-debt 注记，不阻塞**；
   - 清单外或扩大违例面 → **新增违例，P1 阻塞**；
   - 改动修复了清单条目 → 标注"可从清单移除"。
4. **D4 证据核查**（G2）：trace 四节齐全性；analyze/测试命令与结果真实可复跑（抽查至少 1 条复跑）；代码生成执行记录；测试覆盖对照详细设计测试映射（漏失败路径用例 = P2 起步，高风险链路漏测 = P1）。
5. **D5 注释/日志/文档追溯核查**（维护性证据）：检查实现是否能让后续维护者从代码回到设计决策。
   - 新增核心类、public API、Controller/UseCase/Repository/DataSource、跨层 DTO/状态定义，必须有 Dart doc comment 或等价注释说明职责、承接的 `UNIT-<slug>` / `BHV-NNN`；必要时附设计文档相对路径（`docs/design/.../chapters/<slug>.md` 或任务内 `design.md` 锚点）。缺失通常为 P2；高风险链路或新增核心 owner 完全无追溯为 P1。
   - 非显然业务分支、错误/降级/恢复、缓存、异步竞态、生命周期处置、外部依赖边界必须解释"为什么这样做"，不能只靠代码形状猜意图。缺失按 P2 处理。
   - 关键流程日志应覆盖入口、成功收口、失败/降级、重试/恢复、外部依赖边界；必须复用项目 logger / logging helper / 日志门面。裸 `print`/`debugPrint`、吞错无日志、外部依赖失败无上下文日志按 P2 起步，高风险不可观测路径按 P1。
   - 日志不得记录 secret、token、PII、完整请求体或用户生成内容原文；命中即 P1。
   - trace §2/§3 应记录本次新增注释、日志、文档路径引用与无法覆盖的理由；缺记录为 P3，若导致审计不可复现为 P2。
6. **D6 合规红线**（G3）：制裁 TLD、私有 API、动态执行、权限/数据采集与设计合规依据不一致 = P1。
7. **D7 数据层逐行语义核查**（数据 / 状态 / merge / 解析 改动必做；补足"只核合同"的盲区，是 guru review 自身的逐行密度，**不依赖 OCR**）：对改动的数据层代码**逐行**核查语义正确性（非仅合同符合）——
   - **排序键**：排序是否稳定；同值 / 缺字段（如缺 `attempts`、`createdAt` 缺失）时回退是否确定、不依赖输入顺序。
   - **解码健壮性**：DTO/JSON 解码对 string-or-number、缺字段、null、类型不符是否有确定行为（不静默吞、不崩）。
   - **身份匹配**：按 id/key 匹配时，多条同 id（如多 attempt 同 `mediaMessageId`）是否串味/错配。
   - **merge 集合成员**：本地/远端合并时，**"本地保留集"与"当前可见集"是否被正确区分**——远端权威未返回的项不得被本地补回可见集（Himora 类负向/排除规则）。
   - **断言可证伪性**：相关测试断言是否真能对上述错误 `fail`——正向 enrichment 测试**不算**覆盖排除/遗漏类 bug。
   命中以上语义缺陷按 `IMPLEMENT_DEFECT`；若该语义本应由详细设计写成不变量却缺失，按 `DETAIL_DEFECT` 回退（机制详见 P1 的负向不变量 / REQ-UC×BHV 扩展）。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口与修复动作。

**前置通过时**：
0. **机器可读收口字段（必须置顶）**：
   - clean 且可进入 PR 时输出：`review_result=clean/final-verification-ready`、`route_class=none`、`validation_summary=<命令与证据摘要>`。
   - 有 finding 或阻塞时输出：`review_result=findings` 或 `review_result=blocked`，并给出最高优先级 `route_class`。
   - route class 只能取：`IMPLEMENT_DEFECT`（代码/测试/验证/注释/日志/脱敏缺陷）、`PROCESS_DEFECT`（trace/证据/流程执行缺陷）、`DETAIL_DEFECT`（详细设计合同错误或缺失）、`OVERVIEW_DEFECT`（概要归属/承接错误）、`REQ_BLOCKER`（需求行为/验收/边界缺陷）、`none`。
1. 逐条 findings：`severity(P1/P2/P3) / location(文件:行) / problem / suggestion(最小修订)`，先证据后结论。
   - 每条 finding 必须附 `route_class`；同一轮多类缺陷按 `REQ_BLOCKER > OVERVIEW_DEFECT > DETAIL_DEFECT > PROCESS_DEFECT > IMPLEMENT_DEFECT` 给最高优先级路由。
2. 存量豁免清单：本次触碰的 SLOT-15 条目 + 分类结果 + 可移除项。
3. 注释/日志/文档追溯摘要：覆盖的新增核心定义、日志点、设计文档路径引用，以及缺口。
4. **结论（三选一）**：可进入 PR / 修复 P2 后可进入 / 不可进入（列阻塞 P1）。
5. 反哺建议（可选）：本次暴露的新模式/新坑 → 建议更新 golden-path、L2 或槽位定义的条目。

## 边界约束

- 只审改动面 + 其直接依赖；不对存量代码做全量审计。
- 审核不代写代码；每条 finding 给最小修订方案。
- 测试失败/证据缺失时如实输出，不降级结论。

## 与官方 Trellis skill 的边界

本 skill 是 `trellis-check` 在 Guru Flutter 项目的领域化审核口径（分层依赖律 + canonical + 存量豁免 + 合规红线），与官方 lint/typecheck 检查叠加执行。
