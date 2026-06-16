# iOS 概要审核输出合同（references）

> 输出分支、字段与顺序以本文件为唯一主定义；与其它说明冲突时以本文件为准（规则正文仍以 L1
> `.trellis/spec/harness/overview/overview-structure-single-source.md` 为准）。
> 严重度判级与取证组织见 `./review-baseline.md`；修订形态（局部修订 / 文档级重构）判定回指 L1 §9。
> doc_type 七类名一律以 L1 / 详细 L1 为准（`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`），输出中禁出现自创类型名。

## 分支一：前置阻断输出（EX-1~EX-4 / C1~C10 任一失败）

只输出以下三段，不展开逐章审核，不输出 G 项展开结论：

```markdown
## iOS 概要审核：前置阻断

**前置缺口**（逐条：EX/C 编号 ｜ 缺口 ｜ 证据）
- EX-2 ｜ design_package 缺 chapters/ 目录 ｜ `ls docs/design/<feature>/` 取证
- C2 ｜ project-conventions 网络层槽位（URLSession / Moya）未定值，external 网络承接无法对齐 ｜ project-conventions.md 槽位缺

**修复动作**（逐条最小动作，含回退指向）
- 建立 chapters/ 空目录并重跑 `python3 .trellis/scripts/guru/guru_gate.py overview <task_dir>`
- 在 project-conventions.md 补 C2 网络层取值或显式标 pending 后重新送审

**结论**：前置未通过，不进入逐章审核；修复后重新送审。
```

口径说明：

- 需求准入失败（EX-3）时，修复动作必须写「回退需求阶段」而非概要侧补救；`Capability-to-Architecture Mapping` 只能判为「未建立：需求核心能力输入未满足」。
- 机器 Gate（EX-4 `guru_gate.py overview`）未过时，结构性缺口先由机检定位，修复动作指向重跑机检；人工审核聚焦语义与归属，不在前置阻断里展开 G 项。
- 缺 L1 主 SSOT 时（装载步骤 1 失败），修复动作写「先安装 guru spec 模板：`trellis init -t guru-ios-native`」。

## 分支二：全量门禁输出（前置通过）

按以下顺序与字段输出。light 链第 5 / 6.架构总览相关项标 `N/A(light)` 并说明简化口径已满足（L1 §2b：保留一句话架构 + 页面流文字描述，分层图与时序图策略表不强制）。

### 1. 架构视图检查摘要（放最前——评审者先看图，G6）

```markdown
| 件 | 状态 | 备注 |
|----|------|------|
| 一句话架构 | ✅/❌ | 格式是否按 L1 §2.5①；组件是否为归属表真实名 |
| 分层架构图 | ✅/❌ | 节点×N；DDD 四层 subgraph 是否齐；方向合规 / 违例位置（逆 Domain→App→Infrastructure→UI 单向 / UI 直连持久化） |
| 页面流图 | ✅/❌/N-A | 边是否经 AppCoordinator；失败 / 取消 / 权限拒绝去向；非 UI 需求 N/A 依据 |
| 核心 UC 表 | ✅/❌ | UC×N；是否从验收场景提炼（非 BHV 一对一重排） |
| UC 承接表 | ✅/❌ | bhv_refs / owner_refs / index_refs 三向闭合；断链清单 |
| 时序图策略表 | ✅/❌ | 独立×N / 合并×N / 豁免×N；占位残留清单；参与者真实性（无 View 直连 external/持久化、无 View 间直连导航边） |
```

### 2. Findings（按严重度分组，每条五字段）

每条：**severity ｜ location ｜ problem ｜ evidence ｜ suggestion**，并标注受影响 G 项。先证据后结论。

```markdown
**P1-1** ｜ severity：P1（阻断）
｜ location：§3 归属表 BHV-007「展示最近故事」行
｜ problem：最近故事的列表加载（数据访问）被归给 `viewmodel`（HomeViewModel 直接列出 WCDBSwift 查询结果），违反分层依赖律——viewmodel 不得直连持久化，必须经 usecase → repository 接口
｜ evidence：归属表原文「HomeViewModel 直接读取 Story 表填充 recentStories」；与 L1 §4 硬约束「不得把数据访问归给 viewmodel」「viewmodel 直接持有 WCDBSwift 句柄」违例形态一致
｜ suggestion：局部修订——数据访问 owner 改为 `usecase`（如 `UNIT-story-management-usecase` 的 fetchAllFullStories）+ `repository`（`UNIT-story-repository` 的 IStoryRepository.findAll），HomeViewModel 仅持有 @Published 状态并调 usecase
｜ 受影响 G 项：G2
```

口径说明：

- 同一根因多处表现合并为一条 finding，列全部 location。
- 分层依赖律违例 / golden-path 硬规则违例（CoreData/SwiftData、手动 DI、Repository 模式缺失、View 间直连导航、View 直连持久化、自创 doc_type、secret value、缺 compliance_basis、粗粒度核心行为、pending 四类缺 l2_status 或缺豁免计划）一律 P1，且不得给通过性结论。
- suggestion 必须区分局部修订 / 文档级重构（按 L1 §9，判定细则见 review-baseline §12）；结构 / 归属 / 合同缺陷不得建议用局部补写保留错误模型。
- 若无 Findings，写 `无`，不保留编号占位。

### 3. 结构概况（一段话，≤4 句）

```markdown
- 链型：full / light（判定依据 task.json `guru_chain`）
- 主定义位置：full=`docs/design/<feature>/design-main.md`；light=任务内 `design.md` §1
- 显式假设落盘状态：无 / 有（记录位置 + 依据 + 影响范围 + 验证时点）
- 计数：BHV×N / UC×N / 归属 owner×N / 承接索引条目×N
- 整体形态评价：自底向上写作顺序是否成立、归属模型是否自洽（≤2 句）
```

### 4. 技术决策承接预览（`technology_decision_handoff_source_preview`）

逐 `TD-<序号>` 行给出字段齐全性与合规 / 凭证状态（对照 L1 §2.6）：

```markdown
| decision_id | decision_point | selected | rationale | detail_expansion_targets | compliance_basis | 状态 |
|-------------|----------------|----------|-----------|--------------------------|------------------|------|
| TD-01 | 端侧 LLM 选型 | <选定/未选定> | <回指架构驱动> | §7 external <chapter_target> | N/A（不涉权限） | 已闭合 / 缺口 |
| TD-02 | 麦克风权限请求时机 | <选定> | <…> | §7 external <chapter_target> | NSMicrophoneUsageDescription 用途串 + PrivacyInfo.xcprivacy 取向 | 缺 compliance_basis → P1 |
```

- 无触发写 `no_triggered_technology`。
- 涉权限（麦克风 / 相册 / 文件 / 定位 / 通知 / ATT）/ 数据采集 / 三方域名 / PII 的条目缺 `compliance_basis` → P1（G3）。
- 凭证只写引用方式（Keychain 引用 / 默认凭证链 / 环境变量名 / xcconfig 引用）；真实 secret value（`api_key` / `access_key_id` / `secret_access_key` / `secret_key` / `token` / 私钥）落盘 → P1。
- 未选定决策被下游引用 → P1（G8）。

### 5. 承接索引状态（G4 / G9）

```markdown
- owner 覆盖：归属表 owner×N 全部被索引覆盖 / 未覆盖清单（→ P1）
- doc_type 合法性：全部 ∈ 七类（viewmodel/usecase/repository/domain-model/view/coordinator/external）/ 自创类型清单（→ P1）
- full 链逐文件：每条索引有 chapters/<slug>.md / 缺文件清单
- 已出 3 类 L2（full）：viewmodel→detail-type-viewmodel.md ｜ usecase→detail-type-usecase.md ｜ repository→detail-type-repository.md；命中条目是否回指对应 L2 八问承接深度
- pending 4 类 `l2_status: pending` 清单：domain-model / view / coordinator / external 命中条目逐条标注 + 按详细 L1 八问展开的 L2 豁免计划（缺标注或缺计划 → P1）
```

### 6. G1~G9 状态表

```markdown
| G 项 | 状态 | 证据 / 阻塞 finding |
|------|------|--------------------|
| G1 行为覆盖（P0/P1 → BHV，粒度 §3.1） | pass / fail | |
| G2 归属判定（唯一 owner + 三问 + 分层依赖律） | pass / fail | |
| G3 合规依据（权限 / 采集 / 三方域名 / PII） | pass / fail | |
| G4 承接索引（owner 全覆盖 + 七类 + 逐文件 + l2_status） | pass / fail | |
| G5 未决问题无高风险（或带假设确认） | pass / fail | |
| G6 架构总览六件套齐全（图 ⊆ 归属表、无分层违例链路） | pass / fail | |
| G7 时序图策略闭合（非豁免可定位 / 合并覆盖清单 / 豁免理由 / 无占位） | pass / fail | |
| G8 technology_decision_handoff 字段完整 + 无未选定被引用 + 无 secret | pass / fail | |
| G9 L2 承接状态清晰（pending 四类豁免记录 / 已出三类口径一致） | pass / fail | |
```

light 链 G6~G9 标注 `N/A(light)` 并说明简化口径已满足（L1 §2b）；G1~G5 两轨共用，light 链仍须给出七类归属判定。

### 7. 三选一结论（互斥）

- `可进入详细设计`：G1~G9 全部已闭合，无 P0/P1（P3 可遗留）。
- `带明确假设可进入`：仅余已落盘的显式假设，无 P0/P1——逐条列假设、依据、影响范围、验证时点。
- `不可进入`：存在 ≥1 条 P0/P1——列阻塞清单 + 修订形态建议（局部修订 / 文档级重构，按 L1 §9）。
- 发现需求层缺陷（行为缺失 / 矛盾 / 范围漂移）→ 结论附「回退需求阶段」，不建议在概要补造业务规则。

### 8. Gate 收口指引（结论为「可进入」/「带假设可进入」时必须输出）

按 config `guru.gate_mode` 二选一（通道主定义见 SKILL.md「Gate 收口」）：

```markdown
# strict（默认）：提请用户本人在终端运行（agent 不得代跑，无 TTY 会被拒）
python3 .trellis/scripts/guru/guru_gate.py confirm

# soft：用户在本轮对话明确确认后，agent 代跑并留痕
python3 .trellis/scripts/guru/guru_gate.py confirm overview <task_dir> --via-agent --user-quote "<用户确认原话>"
```

确认未落盘前不得进入详细设计（详细阶段入口前提）。

## 复审闭环

按 findings 修订后复审：只复查受影响章节与其跨章一致性项，输出「复审范围 + 原 finding 关闭状态 + 新增 finding（若有）+ 更新后的 G1~G9 状态表与三选一结论」；不重复输出未受影响章节的全量取证。

## 输出字段维护纪律

- 本文件是输出字段与顺序的唯一主定义；字段新增 / 删改 / 命名调整只改本文件，不在 SKILL.md 或 review-baseline.md 并行维护输出字段清单。
- 取证操作与判级口径在 `./review-baseline.md`；规则正文与 G1~G9 完成条件在 L1。三者职责不重叠。
