# Go 后端概要审核输出合同（references）

> 输出分支、字段与顺序以本文件为唯一主定义；与 SKILL.md 文字描述冲突时以本文件为准（规则正文仍以 L1
> `.trellis/spec/harness/overview/overview-structure-single-source.md` 为准）。
> 两个互斥分支：前置阻断输出（EX-1~EX-4 / C1~C5 / 机器 Gate 任一失败）、全量门禁输出（前置通过）。
> 字段新增/删改/命名调整只改本文件；SKILL.md 与 `review-baseline.md` 只组织取证与执行顺序，不并行维护字段名。
> 严重度与判级以 `./review-baseline.md` §6 为准；G1~G8 定义与闭合口径以 L1 §6 为准，本文不复写。

## 分支一：前置阻断输出（EX-1~EX-4 / C1~C5 / 机器 Gate 任一失败）

只输出以下三段，不展开逐章审核，不输出 G 项展开结论：

```markdown
## 概要审核：前置阻断

**前置缺口**（逐条：EX/C 编号 / 缺口 / 证据）
- EX-2：design_package 缺 chapters/ 目录（`ls <design_package>` 取证）
- C3：project-conventions.md 未声明 DB 驱动槽位取值（校验清单第 N 项空槽）

**修复动作**（逐条最小动作，含回退指向）
- 建立 chapters/ 空目录并重跑 `python3 .trellis/scripts/guru/guru_gate.py overview <task_dir>`
- 在 project-conventions.md 填写 DB 驱动槽位（或显式标注沿用当前默认）后重新送审

**最小结构状态**
- 链型：`<full / light / 未判定>`
- 概要主定义位置：`<design_package/design-main.md / design.md §1 / 未定位>`
- 需求核心能力输入：`<已定位且有 P0/P1 / 未定位 / 未达准入：blocked 原因>`
- Capability-to-Architecture Mapping：`<未建立：需求核心能力输入未满足>`

**结论**：前置未通过，停止逐章审核；修复后重新送审。
```

分支选择与特例：

- EX-1 判轨失败（`guru_chain` 不可判定 / full 链 `design_package` 未声明）→ 修复动作写「补判轨 / 补 design_package 路径声明」。
- EX-2 包骨架失败（README.md / design-main.md / chapters/ 缺；light 链 design.md §1 缺）→ 修复动作写「补包骨架」。
- EX-3 需求准入失败（核心能力定义不可定位、无 P0/P1 且无合法 `exception_type=no_p0_p1`、仍为 `ai_drafted`、或概要未按 L1 §1-P4 落显式假设）→ 修复动作必须写「回退需求阶段」，不写概要侧补造业务规则。
- EX-4 机器 Gate 失败 → 修复动作写「过机器 Gate」并附机检报告中的结构缺口；机检定位的结构性缺口不重复进入人工 findings。
- C1~C5 失败（Go 版本/模块路径、分层目录约定、DB/迁移工具、网络与序列化栈、可观测性基线任一校验不过）→ 修复动作写「补项目约定」并指向 `project-conventions.md` 具体槽位。

## 分支二：全量门禁输出（前置通过）

按以下顺序与字段输出。架构视图检查摘要放最前——评审者先看图（L1 §6 G6 第一取证对象）。

### 1. 架构视图检查摘要（六件套，最前）

```markdown
| 件 | 状态 | 备注 |
|----|------|------|
| 一句话架构 | ✅/❌ | 格式合规/自由化；组件是否真实名 |
| 分层架构图 | ✅/❌ | 节点×N；方向合规/逆向箭头位置；外部直连下层位置 |
| 系统边界图 | ✅/❌ | 是否与分层架构图为两个产物；外部依赖×N |
| 核心 UC 表 | ✅/❌ | UC×N；列齐全性 |
| UC 承接表 | ✅/❌ | bhv_refs/owner_refs/index_refs 断链清单 |
| 时序图策略表 | ✅/❌ | 独立×N / 合并×N / 豁免×N；占位残留清单；外部直连下层边 |
```

light 链：系统边界图 / 时序图策略表无外部依赖/无异步时标 `N/A(light) + 依据`。

### 2. Findings（按严重度分组，每条五字段）

若无 Findings，写 `无`，不保留编号占位。若存在，逐条按下格式输出，先 P1 后 P2 后 P3：

```markdown
**P1-1** ｜ severity：P1
｜ location：§3 归属表 BHV-021 行
｜ problem：IP 解析重试规则归给 UserHandler，违反分层依赖律（业务规则下沉 transport）
｜ evidence：归属表原文「重试由 handler 定时发起」；与 §2.5 ② 分层架构图 `transport → service` 方向矛盾
｜ suggestion：owner 改 ClientIPLocationService（service 层持有重试/退避语义），handler 仅做协议归一与错误→HTTP 映射；按 L1 §8 属文档级重构（归属模型错误）
｜ 受影响 G 项：G2
```

字段定义：

- `severity`：`P1`（阻断）/ `P2`（非阻断）/ `P3`（建议）——判级见 `./review-baseline.md` §6。
- `location`：章节锚点 + 表格行 / 裸编号（`§5 ⑤ UC-003`、`§6 TECH-002`、`§7 <chapter_target>`），或明确缺失对象。
- `problem`：缺陷一句话描述（先证据后结论，不写概括性「基本满足」）。
- `evidence`：引用正文原文 / 双向差集断点 / 明确缺失对象；分层律与图文一致性类必须给出可定位的矛盾两端。
- `suggestion`：最小修订方案，标注局部修订 vs 文档级重构（按 L1 §8）；结构/归属/合同缺陷不得建议用局部补写保留错误模型。
- `受影响 G 项`：G1~G8 中受影响项（缺失即 P1，必标）。

同一根因多处表现合并为一条，列全部 location。

### 3. 结构概况（一段话，≤5 句）

- 链型：`<full / light>`。
- 主定义位置：`<design_package/design-main.md / design.md §1>`；full 链 README/design.md 是否仅做导航（双主定义风险）。
- 计数：BHV×N / UC×N / TECH×N / 第 7 章索引条目×N。
- 显式假设落盘状态：`<无 / 有：记录位置 + 三字段（依据/影响范围/验证时点）是否齐全>`。
- 向后兼容性决策：`<已确认 no / 已确认 yes 且范围合法（confirmation_ref 位置）/ 未确认 / 范围越界>`。

### 4. 技术决策承接预览 `technology_decision_handoff_source_preview`

逐 `TECH-NNN` 行输出（无触发写 `no_triggered_technology`）：

```markdown
| decision_id | trigger_source | selected | selection_status | credential_strategy_boundary | compliance_basis | detail_expansion_targets | 字段完整性 |
|-------------|----------------|----------|------------------|------------------------------|------------------|--------------------------|-----------|
| TECH-001 | architecture_driver | ip-api.com + 百度 opendata 双 provider | accepted | env/无凭证（公开 HTTP 查询，无 key） | 三方域名用途可解释 | external <chapter_target> | 完整/缺字段清单 |
```

- `selection_status` 必须为 `accepted` / `explicit_assumption`；出现 `needs_validation` 记 P1（G8）。
- credential 命中外部 provider/LLM/对象存储/云服务时必填，只写 `api_key_env_name`/`credential_ref`/默认凭证链/运行平台身份注入；扫描到真实 secret value 记 P1。
- 涉权限/采集/三方域名/PII 缺 `compliance_basis` 记 P1。

### 5. 承接索引状态（G4）

```markdown
- owner 覆盖：`<归属表 owner 全覆盖 / 未覆盖清单>`
- doc_type 七类合法：`<全部 ∈ {entry-api, biz, repository-data, domain, config, external, runtime} / 非法取值清单（含他平台类型名）>`
- full 链逐文件：`<每条有 chapters/<slug>.md / 缺文件名清单>`
- repository-data：`<存在持久化且含 ≥1 条 / 无持久化已声明 n/a / 有持久化但缺条目>`
- l2_status: pending 清单：`<命中 domain/config/external/runtime 的条目，逐条是否标 pending + L2 豁免计划（按详细 L1 八问展开）>`
- 已出 3 类回指：`<entry-api/biz/repository-data 条目能否回指对应 L2 承接深度>`
```

### 6. 核心能力承接闭环（G9）

```markdown
- Capability-to-Architecture Mapping：`<已建立且字段级 readiness 通过 / 应建未建（受影响子项 + 失败状态）/ N/A：合法 exception_type=no_p0_p1 + 声明位置>`
- detail_wx6_readiness：`<pass:established_complete / pass:not_applicable_by_no_p0_p1 / fail:<failure_state>>`（任一 fail 不得判定可进入）
- owner 行为落点：`<每个 P0/P1 owner_behaviors 是否命中 detail_doc_type=biz chapter_target>`
- p2_ordinary_behavior_trace：`<not_applicable_by_no_p2 / complete / fail:<state>>`
- LLM 调用承接（触发时）：`<逐 llm_invocation_ref 闭合 prompt_owner/上下文来源/上下文获取行为/prompt 组装 owner/detail_prompt_target 与技术决策目标 / 未触发>`
```

### 7. G1~G8 状态表

```markdown
| G 项 | 状态 | 证据 / 阻塞 finding |
|------|------|---------------------|
| G1 行为覆盖（P0/P1 全覆盖 + 粒度 + P2 trace） | 已闭合 / 需修订 | |
| G2 归属判定表 + Go 分层依赖律 + net/http 锁定 | 已闭合 / 需修订 | |
| G3 外部 provider/LLM/存储/云/鉴权/采集 的选型 + credential + 合规 | 已闭合 / 需修订 / 无触发 | |
| G4 承接索引（七类 doc_type + owner 覆盖 + 逐文件 + repository-data） | 已闭合 / 需修订 | |
| G5 未决问题无高风险 + 执行基线五字段 + 向后兼容确认 | 已闭合 / 需修订 | |
| G6 架构总览六件套齐全且图表与归属表一致 | 已闭合 / 需修订 / N/A(light) | |
| G7 时序图策略闭合（非豁免可定位 + 合并覆盖清单 + 豁免理由 + 无占位） | 已闭合 / 需修订 / N/A(light) | |
| G8 technology_decision_handoff[] 字段完整 + 无 needs_validation + detail_expansion_targets 可回指 | 已闭合 / 需修订 / N/A(light) | |
| G9 核心能力承接闭环 + detail_wx6_readiness 合法通过 | 已闭合 / 需修订 | |
```

> 注：L1 §6 完成判定列出 G1~G9（G1~G5 两轨共用，G6~G9 仅 full 链强制）；SKILL.md 多处以「G1~G8」概称该收敛区间，二者指向同一组完成条件——本状态表按 L1 逐项展开至 G9，full 链九项齐审，light 链 G6~G9 标 `N/A(light)` 并说明简化口径已满足（L1 §2b）。

### 8. 三选一结论（互斥）

- `可进入详细设计`：G1~G9 全部已闭合，无 P0/P1。
- `带明确假设可进入`：仅余已落盘的显式假设，无 P0/P1——逐条列假设、依据、影响范围、验证时点。
- `不可进入`：存在 ≥1 条 P1——列阻塞 P1 清单 + 修订形态建议（局部修订 / 文档级重构，按 L1 §8）；需求层缺陷标注「回退需求阶段」。

### 9. Review Evidence 收口指引（结论为可进入 / 带假设可进入时必须输出）

```markdown
记录本次 clean review（使用新的 run_id）：
python3 .trellis/scripts/guru/guru_gate.py record-review overview <task_dir> --result clean --max-severity low --reviewer clean-context --run-id <fresh-run-id> --evidence "<本次概要审核证据摘要>"

当前 digest 下两个不同 run_id 的 clean review 后，overview 自动通过；不要运行 confirm overview。
```

## 复审闭环

按 findings 修订后复审：只复查受影响章节与其跨章一致性项，输出「复审范围 + 原 finding 关闭状态 + 新增 finding（若有）+ 更新后的 G1~G9 状态表与结论」；不重复输出未受影响章节的全量取证。
