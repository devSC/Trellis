# H5 详细审核输出合同（references）

> 输出分支、字段与顺序以本文件为**唯一主定义**；字段新增/删改/命名调整只改本文件，SKILL.md 与 `review-baseline.md` 不并行维护输出字段名。规则正文仍以 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md` 为准，取证矩阵见 `references/review-baseline.md`；冲突时 **L1 > L2 > references > SKILL.md**。
> 规则回指口径：用结构化字段 `rule_ref=<规范文件路径#锚点>`，不复制规则正文。D1~D8 / G1~G8 / EX-1~EX-6 / P1~P3 编号即 SKILL.md 与 L1 同名项。
> 平台基线：Next.js（App Router 生产形态为目标）。doc_type 一律用 L1 §1 **H5 七类**（`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`），输出中禁止出现 flutter（page-entry/controller/usecase/repository-datasource）或 Go（entry-api/biz/repository-data）类型名。
> 详细 Gate 口径对齐 L1 §8 的 **G1~G8**（G1~G5 两轨共用，G6~G8 仅 full 链强制）；light 链 G6~G8 标 `N/A(light)` 并说明单文件口径已满足。

## 分支一：前置缺口输出（EX-1~EX-6 任一失败）

仅输出 EX 缺口与最小修复动作，不进入逐文档诊断。EX-3/EX-4/EX-5/EX-6 类缺口（承接索引断链、概要未确认、承接源未选定、机器 Gate 断链）的修复动作必须写「回退概要 / 判轨 / 项目约定 / 需求」而非详细侧补造；非法 doc_type 名写「回退概要改名为权威七类之一」。

```markdown
## H5 详细审核：前置阻断

**review_scope**：<current_chapter / layer_checkpoint(checkpoint_layer=<server-chain|interactive-chain|mutation|route>) / directory_final>

### 执行前置条件结果
- EX-1 输入键（guru_chain full/light 判轨，full 含 design_package）：`ok/failed`
- EX-2 路径与骨架（full: design_package/chapters/ 存在；light: design.md §2 存在）：`ok/failed`
- EX-3 承接索引（design-main 第 7 节 chapter_target → doc_type → 目标文件 完整映射，doc_type 落七类全集）：`ok/failed`
- EX-4 概要确认（guru_gate.py status 显示 overview 已人工确认）：`ok/failed`
- EX-5 承接源（内容源/状态管理/UI 库/样式/数据库/认证/部署/路由模式等选定；pending L2 命中有 L2豁免）：`ok/failed`
- EX-6 机器 Gate（guru_gate.py detail <task_dir> 结构结论可获取）：`ok/failed`

### EX 缺口（逐条）
- EX-<id> ｜ 缺口：<具体缺什么> ｜ 证据：<文件:小节 或 明确缺失对象 / 命令输出断点>

### 修复动作（逐条最小动作）
- <动作；EX-3/EX-4/EX-5/EX-6 类必须写「回退概要/判轨/项目约定/需求」；非法 doc_type 名写「回退概要改名为权威七类之一」>

### 三类承接源状态（不伪造 Gate）
- capability 承接源：`skipped_by_ex_precheck_failure:<EX-id>`
- technology_decision 承接源：`skipped_by_ex_precheck_failure:<EX-id>`
- project_conventions 承接源：`skipped_by_ex_precheck_failure:<EX-id>`

### 结论
前置未通过，不进入逐文档诊断；修复后重新送审。
```

## 分支二：诊断输出（前置通过）

输出顺序固定为：scope 声明 → 逐文档概况表 → Findings 分级 → 跨链链路状态 → 概要承接索引与覆盖率状态 → 详细 Gate 状态表 → 三选一结论 → 修订形态建议 → Gate 收口指引。

### 1. scope 声明

```markdown
- review_scope：`current_chapter(<chapter_target/chapter_batch>)` / `layer_checkpoint(checkpoint_layer=<server-chain|interactive-chain|mutation|route>)` / `directory_final`
- 链型：`full` / `light`
- 本轮范围内目标清单：`<chapter_target 列表（裸 token / chapters/<slug>.md）>`
- 范围外未审清单：`<明示「范围外未审」，防误读为通过>`
- partial_chapter_scope（仅 current_chapter 收窄时）：`chapter_subscope` / `behavior_subset` 描述 | `not_applicable_by_full_chapter_scope` | `not_applicable_by_review_scope`
- covered_items[]：`<本轮已覆盖的 route 段/behavior/UNIT/domain-type 列表 | not_applicable_by_full_chapter_scope | not_applicable_by_review_scope>`
- not_covered_items[]：`<同一 canonical chapter_target 内未覆盖项 | [] | not_applicable_by_full_chapter_scope | not_applicable_by_review_scope>`
- canonical_publish_status：`complete_by_full_scope_review | not_applicable_by_partial_scope | not_applicable_by_review_scope`
- scope_findings_summary：`none_in_current_scope | findings_present`
- directory_final_required：`required_after_chapter_loop | not_applicable_by_directory_final`
```

`current_chapter` / partial scope 提醒：批次/单章无 Findings 只代表本范围 `findings=none`，不代表目录通过；partial scope 无 Findings 只代表 `covered_items[]` 干净，须回填 `not_covered_items[]` 与 `canonical_publish_status=not_applicable_by_partial_scope`，并保留 `directory_final_required`。

### 2. 逐文档概况表（current_chapter / directory_final 必含）

每个现存目标文档一行独立 D1~D8 诊断（directory_final 不得跳过逐文档阶段）。

```markdown
| 章节(chapter_target) | doc_type | l2 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | findings |
|----------------------|----------|----|----|----|----|----|----|----|----|----|----------|
| post-list-server | server-component | v1 | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | P2×1 |
| post-detail-route | route | pending | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | P1×1 |
```

- 状态符号：`✅` 通过 / `⚠️` 有 P2/P3 / `❌` 有 P1 / `N/A` 非适用（须在 findings 列或下方注明依据）。
- 缺失目标文档单列（不进 D 诊断）：`缺失清单 + 修订方案`；`per_document_results[]` 对应行写 `skipped_by_missing_target_docs:{missing_target_docs}`。
- 文档分流结果：`existing_target_docs=<列表>`，`missing_target_docs=<列表>`。
- per_document_results[]（与表同源，可结构化展开）：每条含 `chapter_target` / `detail_doc_type` / `l2_status` / `loaded_l2_ref`（命中 v1 类型 SSOT 或 `pending_no_l2`）/ `D1~D8 结果` / `findings_refs[]`。
- 薄文档命中时（review-baseline §6）：跳过本表逐列，改输出薄文档证据（雷同章节对照 + 占位统计：空参数表数 / 无签名方法数 / `sequenceDiagram` 缺失章数 / 测试映射 ≤1 行的章数）+ 文档级重构方案。

### 3. Findings（按严重度分组，每条五字段 + 受影响 G 项）

五字段固定为 `location / problem / evidence / suggestion / rule_ref`，外加 **受影响 G 项**（指 L1 §8 的 G1~G8）。同根因合并为一条、列全部位置；判级冲突取高。

```markdown
**P1-1** ｜ location：chapters/post-detail-route.md §4.2 UNIT-post-detail-route
｜ problem：route 段内实现内容过滤业务规则（route 越权承载业务），违反 §2.1（route 只编排 + metadata，业务下放 server-component/data-access）
｜ evidence：流程详述第 3 步「按 tag 过滤草稿文章」无下层调用对象，业务判定写在 route 段
｜ suggestion：过滤上收 server-component/data-access，route 只编排 + metadata/SEO（局部修订，L1 §9）
｜ rule_ref：detail-structure-single-source.md#21-分层依赖律归属硬基准违反-fail
｜ 受影响 G 项：G2

**P2-1** ｜ location：chapters/post-list-server.md §6 UNIT-post-list-server
｜ problem：动态 route 缺 generateMetadata 承接（metadata/SEO 缺失）
｜ evidence：§6 路由/渲染/SEO 节只写 page 渲染，无 metadata/generateMetadata 导出
｜ suggestion：补 generateMetadata（title/description/openGraph）（局部修订，L1 §9）
｜ rule_ref：golden-path.md#26-metadata--seo-标准化
｜ 受影响 G 项：G6
```

- 五字段：`location`（`<chapter_target> §<节> UNIT-<slug>` 或明确缺失对象）/ `problem` / `evidence`（正文摘录或字段断点）/ `suggestion`（最小修订；形态判定只引用 L1 §9）/ `rule_ref`。
- 先证据后结论：每条 finding 必须带文档/章节锚点或明确缺失对象。
- 薄文档命中时（review-baseline §6）：跳过逐条列举，输出薄文档证据 + 文档级重构方案。

### 4. 跨链链路状态（directory_final / layer_checkpoint 必含）

按 review-baseline §4 六个链边界逐项 pass/fail + 失效位置：

```markdown
| 链边界 | 状态 | 失效位置 / 证据断点 / rule_ref |
|--------|------|-------------------------------|
| route→server-component | ok/risk | — |
| server-component→data-access | ok/risk | — |
| data-access→domain-type | ok/risk | — |
| client-component→ui-component | ok/risk | — |
| server-action→data-access | ok/risk | — |
| server/client 全局边界(私有数据/secret 不入 client、状态写 owner 唯一、错误枚举跨章一致、props 可序列化) | ok/risk | — |
| directory_chain_review | ok / not_applicable_by_review_scope / risk:{链路类型/涉及章节/证据断点/rule_ref} | — |
```

`current_chapter` 时 `directory_chain_review` 写 `not_applicable_by_review_scope`（或仅回填当前目标的上下游关联边界摘要），并保留 `directory_final_required`。

### 5. 概要承接索引与覆盖率状态（directory_final 必含）

按 review-baseline §5 五项：

```markdown
- 索引↔章节双向差集：`目标总数=<N>，命中=<N>，缺失=<N>`（列缺失/孤儿文件）
- 归属表 owner 覆盖：`<每个七类 owner 是否被 ≥1 UNIT 覆盖 | 缺口:{owner / rule_ref}>`
- UC 链路抽查：`<抽查 UC 在详细侧 服务端链/交互链/变更链 是否走通 | risk:{断点}>`
- 时序↔行为抽查：`<抽查 ≥1 UC 时序步骤在对应章节有同名行为与一致方向；sequenceDiagram 无 client-component→data-access 直连边 | risk:{失配 / 直连边位置}>`
- SEO/技术决策展开链：`<概要需 SEO 的 route 有 metadata/generateMetadata 承接；detail_expansion_targets 有承担它的目标 doc_type 章节 | risk:{缺口}>`
- overview_coverage_review：`ok | not_applicable_by_review_scope | risk:{overview_ref / 缺口类型 / 缺失或漂移目标 / rule_ref}`
```

`current_chapter` 模式只回填当前目标覆盖证据并保留 `directory_final_required=required_after_chapter_loop`。

### 6. 详细 Gate 状态表（G1~G8）

对照 L1 §8 逐项。light 链 G6~G8 标注 `N/A(light)` 并说明单文件口径已满足。每个 fail 必须在「证据/阻塞 finding」列回指至少一条 Findings 编号；不得用「基本满足」替代逐项证据。

```markdown
| G 项 | 含义 | 状态 | 证据 / 阻塞 finding |
|------|------|------|---------------------|
| G1 | 承接索引每条有详细单元，归属表 owner 全覆盖 | pass/fail | — |
| G2 | 八问完整 + 字段/接口/状态可追溯 owner + §3.1 粒度 + §2.1 分层依赖律 | pass/fail | P1-1 |
| G3 | 每条行为测试映射覆盖成功 + 全部失败路径，测试层符槽位 | pass/fail | — |
| G4 | 私有数据/secret/session/三方域名/PII 单元附边界依据；secret 仅 server 边三类；无私有 API/动态执行/制裁 TLD | pass/fail | — |
| G5 | 八问 8（不得补造清单，含越层反面项）逐单元存在 | pass/fail | — |
| G6 | 章节闭合（索引↔chapters 双向）+ §4 骨架 + pending L2 豁免齐全 | pass/fail/`N/A(light)` | P2-1 |
| G7 | chapter_loop 证据（逐章 chapter_status=passed_by_method_evidence + 七层 checkpoint + 无一轮全量生成迹象） | pass/fail/`N/A(light)` | — |
| G8 | 编号断链全清（BHV/UNIT 双向闭合，无幽灵/悬空/重号/方向违例）+ doc_type ∈ 七类 | pass/fail/`N/A(light)` | — |
```

### 7. 三选一结论（互斥，对应 review-baseline §8）

- **可进入编码**：G1~G8 全部 pass，无 P1/P2（P3 可遗留）。
- **带明确假设可进入**：仅余已落盘的显式假设（逐条列「假设 / 依据 / 验证时点」），无 P1。
- **不可进入**：存在 ≥1 条 P1——列阻塞 P1 清单 + 修订形态建议（局部修订 / 文档级重构，按 L1 §9；概要缺陷标注「回退概要」）。
- 发现上游需求缺陷（行为缺失/矛盾/范围漂移）→ 在结论中标注「回退需求阶段」，不在详细侧补造业务规则。

### 8. 修订形态建议（L1 §9）

逐条 Finding 标注 `局部修订` 或 `文档级重构`：

```markdown
- 局部修订：补错误枚举、补测试映射、补一条依赖声明、补一张 sequenceDiagram、补 metadata/revalidate 项、补一条 'use client' 边界说明、补一条不得补造项、补错误转换位置标注。
- 文档级重构：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档）、doc_type 系统性误用、依赖方向系统性违例（client 普遍直取数据 / server-action 普遍绕 data-access）。
- 概要缺陷（归属错 / 索引漏 / 技术决策/槽位未选定）→ 回退概要修订，禁止在详细阶段就地改归属或私自拍板。
```

### 9. Gate 收口指引（结论为「可进入」/「带明确假设可进入」时必须输出）

按 config `guru.gate_mode`（通道主定义见 workflow Trellis System 节）：

```markdown
**strict（默认）**：请用户本人在终端运行（agent 不得代跑，无 TTY 会被拒）：
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir>

**soft**：用户在对话中明确确认后，agent 运行（记录留痕标注 soft/agent）：
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir> --via-agent --user-quote "<用户确认原话>"

确认落盘前不得 task.py start（before_start 钩子强制拦截）。
```

## 必回填字段（防漏，所有分支）

- `review_scope`、`per_document_results[]`（前置失败或缺失目标时写 `skipped_*` 分支）、`partial_chapter_scope` / `covered_items[]` / `not_covered_items[]` / `canonical_publish_status`、`scope_findings_summary`、`directory_final_required`。
- 不适用字段一律用 `not_applicable_by_review_scope`，不留空、不伪造；前置失败用 `skipped_by_ex_precheck_failure:<EX-id>`；缺失目标文档用 `skipped_by_missing_target_docs:{missing_target_docs}`。
- 三类承接源状态（`capability` / `technology_decision` / `project_conventions`）在前置失败时写 `skipped_by_ex_precheck_failure:<EX-id>`。

## 复审闭环

按 Findings 修订后复审：只复查受影响章节的 D 诊断 + 其跨链引用，输出「复审范围 / 原 finding 关闭状态 / 新增 finding / 更新后 G 状态与结论」。`current_chapter` 复审通过不改变目录级结论——目录级结论只能由 `directory_final` 产生（`directory_final_required` 保持 `required_after_chapter_loop` 直至目录级终审完成）。
