---
name: flutter-implementation-guru-review
description: 按通用 golden-path 与实现标准包审核 Flutter 代码改动，判定能否进入 PR。核查与详细设计合同的一致性、分层依赖律与 canonical 写法、验证证据完整性、注释/日志/文档路径追溯、合规红线，并执行存量豁免判定（存量记债不阻塞、新增违例阻塞）。标准口径住 `.trellis/spec/harness/implementation/`。
---

# Flutter 实现审核

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（判定基准唯一来源）。
2. 读取同级标准包 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（含实现 Gate 口径）。
3. 读取**`.trellis/spec/conventions/project-conventions.md`**，**重点装载 SLOT-15 存量违例清单**（存量豁免判定的数据源），并确认项目 logger / logging helper / 日志门面。
4. 定位：被审改动（diff/分支）、详细设计文档、`implement.md`（digest-bearing trace 计划合同）与 task-local mutable evidence（`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`）。trace 缺失或 mutable evidence 缺执行/验证记录 → 前置失败（实现 Gate 证据链不存在）。
5. **装载 slice packet / invariant matrix**（P1，high-risk slice 必做）：supervisor 经 `build_run_plan` 把
   resolved `slice_packet=<path>` 注入为 `--file`，brief 含 `active_slice=<slice_id>`。以 resolved
   `slice_packet` 路径为准读取 packet 的
   `review_evidence_schema_version`、`requirements_design_inputs`、`invariants[]`（**唯一机器 SSOT**）、
   `target_paths`、`deterministic_checks`、`semantic_review_provider` 与 `integration_slice`。packet/matrix 缺失而 brief
   标记 high-risk → 输出 `DETAIL_DEFECT`/`PROCESS_DEFECT`，不得 clean。
6. 对 `runtime_acceptance_required=true`，以及任何涉及用户可见终态、外部 API/schema、持久化/缓存、异步状态或跨层转换的验收目标，装载对应 Acceptance Closure Matrix 行、authority fingerprint、known-bad fixture、Integration evidence 与 current runtime evidence。required row 缺失按 `DETAIL_DEFECT` 阻断。

## Full/high snapshot 与 evidence Gate

- 先审核 `implement.md` 的 slice planning audit：普通 slice 是否以最少 commit-stable slices 和最大安全并发宽度为目标，是否登记唯一文件级 mutable owner、`covered_units`、真实 `depends_on`、parallel wave、独立 commit/rollback 价值、资源隔离、focused checks 与 reviewer context。仅因 UNIT、`doc_type` 或 data/domain/presentation 层级整齐而机械拆片，按 `DETAIL_DEFECT` 阻断。
- 一个 current snapshot 恰好由一个 semantic reviewer 负责。snapshot 绑定 target bytes、`invariants`、`requirements_design_inputs`、`deterministic_checks`、review policy / `semantic_review_provider` 与 supervisor digest；同一 snapshot 不得启动第二 reviewer 或重新 aggregate。
- clean evidence 只有在 `review_evidence_schema_version=2` 且上述每个绑定组件逐项相等时才能复用。snapshot 改变后可产生一个新 current review；v1、缺组件或部分相等的 evidence 不得复用。
- finding 只使绑定组件实际变化的 receipt 失效，不自动保留或作废所有 sibling receipts。已有 current receipt 的 slice 不得再次 aggregate；未变化的 current receipts 保持可复用。
- 普通 slice 只审 packet、planning audit、目标 diff、选定 requirements/design 与 focused evidence，只消费或执行 ordinary focused checks；不得运行 full regression。Integration 才审最终 union snapshot、ordinary current receipts、cross-slice invariants 与 final deterministic summaries，且 full regression 只属于 Integration deterministic checks。
- 最终语义/静态证据必须检查 workflow 实际派发的 Implementation writer Skill 及其引用的 implementation standards；仅 Planner、Detail 或 reviewer parity 一致不足以满足 Integration。若任一 active Full/high ordinary consumer 仍要求 project/global build、analyze、lint 或 full regression command，或仍按 UNIT、layer、`doc_type`、ViewModel、UseCase 或 component 机械重切片，按 `IMPLEMENT_DEFECT` 阻断。
- Integration packet `target_paths` 是 review coverage，不是写授权。实际改动路径必须是 planning audit 中 exact `integration_owned_paths` 的子集；即使路径位于 packet coverage 内，只要不在 `integration_owned_paths` 也按 `PROCESS_DEFECT` 阻断。reviewer 只读，不派 implement worker、不改 planning artifact、不直接写 receipt，也不重复执行 supervisor 已运行的同一 deterministic command。
- 对每个声明的 `acceptance_id`，review boundary 是该 matrix 行的完整 source-to-sink path，而不是 changed-layer count。可读取未改但决定终态的相邻合同与 current evidence；额外检查必须绑定该 row、单命令且有界，不得扩张为全仓开放式审计。
- ordinary clean receipt 只证明当前 slice 的局部 snapshot；Integration 必须在 final union snapshot 闭合最终终态。即使 Integration deterministic green，runtime-required row 未获 current `runtime_acceptance_pass` 时也只能报告 `implementation_verified` / `runtime_acceptance_pending`，不得报告 `accepted`。

## 执行流程

1. **D1 合同一致性与 semantic authority**（G1）：diff 与详细设计单元逐一对照——合同外新增结构、未实现的承接行为，列差集；`implementation-evidence.jsonl` 是否记录偏差与处置。**有 slice packet 时（P1）：diff 须与 packet `invariants[]` 逐条对照**，每条给 `invariant_status.<id>=pass|fail|not_applicable`（pass 附 evidence、N/A 附 reason，见输出节）；invariant 违反按其 `route_if_missing`/`IMPLEMENT_DEFECT` 路由。注入的正式 requirement/design 包与 packet invariants 是产品语义和规划的行级权威；reviewer/OCR 的主观建议不得覆盖它们。但 current target-environment runtime evidence 是对实际结果的有效反证：不得以“SSOT 已确认”或“packet 未声明”为由否决 failure，也不得据此由 reviewer 直接改写 SSOT。应从 runtime row/fingerprint 依次核对 Requirement、Overview、Detail/packet、implementation、process，返回唯一 earliest-owner route：行为/边界缺失或 material change=`REQ_BLOCKER`，owner/架构错误=`OVERVIEW_DEFECT`，可执行合同/packet/check 错误=`DETAIL_DEFECT`，mutable evidence/执行错误=`PROCESS_DEFECT`，规划正确而代码/测试偏离=`IMPLEMENT_DEFECT`。environment/fixture-only failure 留在 current verification step，不作为第六个产品 defect class。
2. **D2 分层与 canonical**：对照 golden-path §2/§10 逐项检查改动代码——import 方向（data→usecase、controller→repository/API）、接口分离、DI 形态（binding `new`、`build()` 里 `Get.put`、`permanent` 滥用）、datasource 必经、异常不吞、硬编码尺寸、序列化方案与目录槽位（SLOT-01/02/11/12）。
3. **D3 存量豁免判定**（G4，逐违例必做）：每个发现的违例对照 SLOT-15——
   - 命中清单且未扩大违例面 → **tech-debt 注记，不阻塞**；
   - 清单外或扩大违例面 → **新增违例，P1 阻塞**；
   - 改动修复了清单条目 → 标注"可从清单移除"。
4. **D4 证据核查**（G2）：`implement.md` 计划合同与 mutable evidence 齐全性；analyze/测试命令与结果在 `verification-evidence.jsonl` 中真实可复现；代码生成执行记录在 `implementation-evidence.jsonl`。Full/high ordinary slice 只要求并消费 packet 声明的 focused commands；仅当 current packet 或 planning audit focused checks 明确声明测试时，才核对测试名、正/负路径与新增测试映射，不得为通用 D4 自行运行 undeclared tests。若声明的 acceptance row 缺少必要的可证伪检查，或 current runtime failure 证明现有检查 false green，不得用“undeclared”忽略：输出 `DETAIL_DEFECT`/`PROCESS_DEFECT` 和绑定该 row 的最小检查要求，由 planning owner 修复合同；reviewer 仍不得自行启动全仓测试。全项目 `flutter analyze`、完整测试或其他 full regression 只由 Integration 承担；Integration 或 non-Full/v1 保留原测试覆盖合同。消费 supervisor 已记录的 deterministic 结果，不重复执行同一命令；需要额外语义抽查时只选未重复、与具体 acceptance row 直接关联的 focused check。每条 high-risk invariant 必须有 packet 允许的测试、命令或代码路径作为 `invariant_evidence`；不得把测试当作唯一证据形态。
5. **D5 注释/日志/文档追溯核查**（维护性证据）：检查实现是否能让后续维护者从代码回到设计决策。
   - 新增核心类、public API、Controller/UseCase/Repository/DataSource、跨层 DTO/状态定义，必须有 Dart doc comment 或等价注释说明职责、承接的 `UNIT-<slug>` / `BHV-NNN`；必要时附设计文档相对路径（`docs/design/.../chapters/<slug>.md` 或任务内 `design.md` 锚点）。缺失通常为 P2；高风险链路或新增核心 owner 完全无追溯为 P1。
   - 非显然业务分支、错误/降级/恢复、缓存、异步竞态、生命周期处置、外部依赖边界必须解释"为什么这样做"，不能只靠代码形状猜意图。缺失按 P2 处理。
   - 关键流程日志应覆盖入口、成功收口、失败/降级、重试/恢复、外部依赖边界；必须复用项目 logger / logging helper / 日志门面。裸 `print`/`debugPrint`、吞错无日志、外部依赖失败无上下文日志按 P2 起步，高风险不可观测路径按 P1。
   - 日志不得记录 secret、token、PII、完整请求体或用户生成内容原文；命中即 P1。
   - `implementation-evidence.jsonl` / `verification-evidence.jsonl` 应记录本次新增注释、日志、文档路径引用与无法覆盖的理由；缺记录为 P3，若导致审计不可复现为 P2。
6. **D6 合规红线**（G3）：制裁 TLD、私有 API、动态执行、权限/数据采集与设计合规依据不一致 = P1。
7. **D7 数据层逐行语义核查**（数据 / 状态 / merge / 解析 改动必做；补足"只核合同"的盲区，是 guru review 自身的逐行密度，**不依赖 OCR**）：对改动的数据层代码**逐行**核查语义正确性（非仅合同符合）——
   - **排序键**：排序是否稳定；同值 / 缺字段（如缺 `attempts`、`createdAt` 缺失）时回退是否确定、不依赖输入顺序。
   - **解码健壮性**：DTO/JSON 解码对 string-or-number、缺字段、null、类型不符是否有确定行为（不静默吞、不崩）。
   - **身份匹配**：按 id/key 匹配时，多条同 id（如多 attempt 同 `mediaMessageId`）是否串味/错配。
   - **merge 集合成员**：本地/远端合并时，**"本地保留集"与"当前可见集"是否被正确区分**——远端权威未返回的项不得被本地补回可见集（Himora 类负向/排除规则）。
   - **断言可证伪性**：相关测试断言是否真能对上述错误 `fail`——正向 enrichment 测试**不算**覆盖排除/遗漏类 bug。
   命中以上语义缺陷按 `IMPLEMENT_DEFECT`；若该语义本应由详细设计写成不变量却缺失，按 `DETAIL_DEFECT` 回退（机制详见 P1 的负向不变量 / REQ-UC×BHV 扩展）。
8. **D8 Acceptance Closure Matrix 审核**（G1/G2）：逐个 acceptance row 从 trigger/source 到用户可见 sink 核对 authority fingerprint、每一步字段/状态输入输出、owner、缺字段/null/错误/超时/降级分支、允许终态、focused/Integration/runtime evidence。即使 diff 只改一层也不得在该层停止。focused regression 必须有 known-bad/修复前失败证据；只证明 post-fix helper happy path 按 `DETAIL_DEFECT` 或 `IMPLEMENT_DEFECT` 阻断。ordinary receipt 不得代替 final Integration，Integration deterministic evidence 不得代替 runtime pass。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口与修复动作。

**前置通过时**：
0. **机器可读收口字段（必须置顶）**：
   - 第一段只能逐行输出以下 7 个字段；等号右侧只能是单个合法值，不得附加解释、分号摘要、斜杠组合值或 Markdown：
     ```text
     review_result=clean
     route_class=none
     review_target=slice:<slice_id>
     review_provider=<本 check worker 的 provider>
     deterministic_checks=passed
     dirty_scope=isolated
     invariant_coverage=all_passed
     ```
   - clean 分支固定使用 `review_result=clean`，不得输出 `final-verification-ready` 或 `clean/final-verification-ready`。有 finding 或阻塞时只把 `review_result` 改为 `findings` 或 `blocked`，并把 `route_class` 改为单个最高优先级 defect 枚举；其余字段仍各占一行且只含单值。
   - 有 slice packet 时，紧接 7 字段逐条输出 `invariant_status.<id>=pass|fail|not_applicable`；`pass` 必随单行 `invariant_evidence.<id>=<非空证据>`，`not_applicable` 必随单行 `invariant_reason.<id>=<理由>`。无 findings 时另起一行输出 `findings=none`；摘要放在 verdict block 之后，不得拼入 7 字段取值。
   - 不运行开放式再发现 probe，不输出 multiline probe。确有必要补充 supervisor deterministic evidence 之外的只读检查时，只允许单行、单命令、边界明确的 `reviewer_probe_command.N=<exact command>`；不得重复 packet command。
   - 缺任一 gating 字段、取值带解释或组合值、取非通过值却声明 clean、或 provider 不满足 packet `semantic_review_provider`，supervisor 均按 `MALFORMED_REVIEW_OUTPUT` 阻断。
   - route class 只能取：`IMPLEMENT_DEFECT`（代码/测试/验证/注释/日志/脱敏缺陷）、`PROCESS_DEFECT`（trace/证据/流程执行缺陷）、`DETAIL_DEFECT`（详细设计合同错误或缺失）、`OVERVIEW_DEFECT`（概要归属/承接错误）、`REQ_BLOCKER`（需求行为/验收/边界缺陷）、`none`。
1. 逐条 findings：`severity(P1/P2/P3) / location(文件:行) / problem / suggestion(最小修订)`，先证据后结论。
   - 每条 finding 必须附 `route_class`；同一轮多类缺陷按 `REQ_BLOCKER > OVERVIEW_DEFECT > DETAIL_DEFECT > PROCESS_DEFECT > IMPLEMENT_DEFECT` 给最高优先级路由。
2. 存量豁免清单：本次触碰的 SLOT-15 条目 + 分类结果 + 可移除项。
3. 注释/日志/文档追溯摘要：覆盖的新增核心定义、日志点、设计文档路径引用，以及缺口。
4. **结论（三选一）**：可进入 PR / 修复 P2 后可进入 / 不可进入（列阻塞 P1）。该结论只覆盖当前 review target；ordinary clean 不代表 Integration 或 runtime accepted。runtime-required work 在 runtime pass 前必须同时声明 `implementation_verified` / `runtime_acceptance_pending`。
5. 反哺建议（可选）：本次暴露的新模式/新坑 → 建议更新 golden-path、L2 或槽位定义的条目。

## 边界约束

- 只审改动面 + 声明的 Acceptance Closure Matrix 行所需 source-to-sink path/current evidence；不对存量代码做全量审计。
- 审核不代写代码；每条 finding 给最小修订方案。
- 测试失败/证据缺失时如实输出，不降级结论。
- 一个 current snapshot 恰好只有一个满足 packet provider policy 的 semantic reviewer；不得为同一 binding 启动第二 reviewer、重新 aggregate 或用 supplemental reviewer 覆盖 required provider 结论。snapshot 变化后才生成新的 current review，且 binding 未逐项相等的旧 receipt 不得复用。
- **不得要求 OCR 作为默认完成条件**；OCR 仅 optional bounded provider（用户显式触发 / 高风险抽检），记 `channel=ocr_optional`、第一版不满足 required。
- **manual provider 审查留痕**（非 channel spawn，第一版 supplemental 补充审计、不满足 required provider）经验证型 append：
  ```bash
  python3 .trellis/scripts/guru/guru_review_record.py append --task-dir <task> --packet <packet> \
    --provider manual --reviewer <name> --run-id <run_id> --result clean --route-class none \
    --review-target slice:<slice_id> --deterministic-checks passed --dirty-scope isolated \
    --invariant-coverage all_passed --evidence-file <task>/review-records/manual-review-<run_id>.md
  ```
  `--run-id` 必须与 `--evidence-file` 名一致；`channel`/`worker` 由命令派生。

## 与官方 Trellis skill 的边界

本 skill 是 `trellis-check` 在 Guru Flutter 项目的领域化审核口径（分层依赖律 + canonical + 存量豁免 + 合规红线），与官方 lint/typecheck 检查叠加执行。
