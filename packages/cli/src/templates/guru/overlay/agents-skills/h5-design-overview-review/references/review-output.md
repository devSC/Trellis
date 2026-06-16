# H5 概要审核输出合同（references）

> 输出分支、字段与顺序以本文件为**唯一主定义**；字段新增/删改/命名调整只改本文件，SKILL.md 与 `review-baseline.md` 不并行维护输出字段名。规则正文仍以 L1 `.trellis/spec/harness/overview/overview-structure-single-source.md` 为准；冲突时 **L1 > references > SKILL.md**。
> 平台基线：Next.js（App Router 生产形态为目标）。doc_type 一律用 L1 §7.1 **H5 七类**（`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`），输出中禁止出现 flutter（Page/Controller/UseCase/Repository）或 Go（handler/service/repo）类型名。
> 完成条件锚点为 L1 §6 **G1~G9**（G1~G5 两轨共用；G6~G9 仅 full 链强制）；G 项主题对照见 `review-baseline.md` §0。

## 分支一：前置阻断输出（EX-1~EX-4 或 C1~C5 任一失败）

只输出以下三段，不展开逐章审核，不输出 G 项展开结论：

```markdown
## 概要审核：前置阻断

**前置缺口**（逐条：EX/C/P 编号 ｜ 缺口 ｜ 证据）
- EX-2：design_package 缺 chapters/ 目录（ls 取证：`docs/design/<feature>/` 下无 chapters/）
- P6：project-conventions 路由模式槽位未锁定（App/Pages 未取值，无法展开 route 归属）

**修复动作**（逐条最小动作，含回退指向）
- 建立 chapters/ 空目录并重跑 `python3 .trellis/scripts/guru/guru_gate.py overview <task_dir>`
- 在 project-conventions.md §9 锁定路由模式槽位（生产目标 App Router）后重新送审

**结论**：前置未通过，不进入逐章审核；修复后重新送审。
```

- **需求准入失败**（EX-3）时，修复动作必须写「回退需求阶段」而非概要侧补救；`Capability-to-Architecture Mapping` 只能判为「未建立」。
- **机器 Gate 失败**（EX-4）时，先指引重跑 `guru_gate.py overview <task_dir>`（结构性缺口由机检定位，人工审核聚焦语义与归属）。
- 前置阻断分支不输出架构视图摘要、不输出 findings 编号列表、不输出 G1~G9 状态表。

## 分支二：全量门禁输出（前置通过）

按以下顺序与字段输出。

### 1. 架构视图检查摘要（放最前——评审者先看图，对应 G6/G7）

```markdown
| 件（L1 §2.5） | 状态 | 备注 |
|----|------|------|
| ① 一句话架构 | ✅/❌ | 是否按固定格式、组件为真实七类 owner 名 |
| ② 分层架构图 | ✅/❌ | 节点×N；subgraph 分层；方向合规/违例位置（含有无 client-component→data-access 直连边） |
| ③ 路由/组件树图 | ✅/❌/N-A | route 段覆盖；渲染策略(SSR/SSG/ISR)与 metadata 标注；失败路径(error.tsx/notFound) |
| ④ 核心 UC 表 | ✅/❌ | UC×N；是否含 SSR 首屏/hydration 触发 |
| ⑤ UC 承接表 | ✅/❌ | bhv_refs/owner_refs/route_refs/index_refs 断链清单 |
| ⑥ 时序图策略表 | ✅/❌ | 独立×N / 合并×N / 豁免×N；占位残留清单；参与者真实性 |
```

### 2. Findings（按严重度分组，每条五字段）

无 findings 写 `无`，不保留编号占位。逐条格式：

```markdown
**P1-1** ｜ severity：P1
｜ location：§3 归属表 BHV-002 行 / UNIT-tag-filter-client
｜ problem：标签筛选的文章数据获取归给 client-component 直接 fetch，违反 §4.0 分层依赖律（私有数据获取只能在 server-component/data-access/server-action）
｜ evidence：归属表原文「TagFilterClient 内 useEffect fetch 文章列表」
｜ suggestion：取数 owner 改 data-access(UNIT-posts-by-tag-source)，由 server-component 编排，client 仅经 props 接收或经路由触发新一轮 SSR；按 L1 §9 局部修订
｜ 受影响 G 项：G2（兼 G3）
```

- 五字段固定：**severity（P0/P1/P2/P3）/ location（章节锚点 + 表格行 / 裸 token BHV-NNN·UNIT-<slug>，或明确缺失对象）/ problem / evidence（引正文原文或明确缺失对象）/ suggestion（最小修订，标注 L1 §9 局部修订 vs 文档级重构）**，外加 **受影响 G 项**。
- 同一根因多处表现合并为一条，列全部 location。
- 先证据后结论：每条 finding 必须带章节锚点或明确缺失对象。

### 3. 结构概况（一段话 + 关键字段）

```markdown
- 链型：`full / light`
- 主定义位置：`full=design_package/design-main.md 路径 / light=design.md §1`
- README 角色：`仅导航（合规）/ 承载事实正文（P2）`；design.md 角色：`指针+摘要（合规）/ 仍承载主定义（P2 双主定义）`
- 编号计数：`BHV×N / UC×N / UNIT×N / 索引条目×N / TD×N`
- 显式假设落盘状态：`无 / 有（位置 + 三字段：依据/影响范围/验证时点是否齐全）`
- 路由模式槽位：`App / Pages（取自 project-conventions）`
- 整体形态评价：≤4 句（是否能从架构总览读懂应用形态、server/client 边界、数据链路）
```

### 4. 技术决策承接预览（`technology_decision_handoff_source_preview`，对应 G3/G8）

逐条列 `technology_decision_handoff[]`，无触发写 `no_triggered_technology`：

```markdown
| decision_id | decision_point | selected | 字段齐全 | compliance_basis | secret/凭证策略 | detail_expansion_targets |
|-------------|----------------|----------|----------|------------------|-----------------|--------------------------|
| TD-01 | 内容源 MDX vs CMS | MDX | 是/缺<字段> | N/A / <最小权限依据> | 未触发 / env 引用(process.env.X) / 默认凭证链 | §7 UNIT-posts-by-tag-source |
| TD-02 | 渲染策略 SSG vs ISR | SSG+generateStaticParams | ... | ... | ... | ... |
```

- 涉认证/采集/三方域名/PII 的条目 `compliance_basis` 缺失 → G3 Finding（P1）。
- 出现真实 secret value / 把 `.env` 当线上配置合同 → G3 Finding（P1）。
- 「未选定」却被下游引用 → G8 Finding（P1）。
- 渲染策略（SSR/SSG/ISR）与缓存/`revalidate` 未成决策项 → G8 Finding（P2 起步）。

### 5. 承接索引状态（对应 G4）

```markdown
- owner 覆盖：`归属表 owner 集合 N 个 ↔ 索引覆盖 N 个`；未覆盖清单：`无 / <owner 列表>`
- doc_type 合法性：`全部 ∈ 七类 / 出现非法类型名：<token>（flutter/Go/自造 → P1）`
- 逐文件（full 链）：`每条有 chapters/<slug>.md / 缺文件清单`
- l2_status 标注：
  - full（v1 有 L2）：`server-component / client-component / data-access` 条目 → 可回指 detail-type-*.md
  - pending（v1 无 L2）：`route / ui-component / domain-type / server-action` 条目 → 是否标 `l2_status: pending` + 是否给 L1 §7.4 八问展开计划
- pending 清单缺标注或缺八问计划 → G4 Finding（P1）
```

### 6. G1~G9 状态表（对应 L1 §6）

```markdown
| G 项 | 状态 | 证据 / 阻塞 finding |
|------|------|---------------------|
| G1 行为覆盖 + 粒度 | pass / fail | |
| G2 归属判定表 + 分层依赖律 | pass / fail | |
| G3 合规依据 + secret 边界 | pass / fail | |
| G4 承接索引覆盖 | pass / fail | |
| G5 未决问题风险 | pass / fail | |
| G6 架构总览六件套 | pass / fail / N/A(light) | |
| G7 时序图策略闭合 | pass / fail / N/A(light) | |
| G8 技术决策承接字段完整 | pass / fail / N/A(light) | |
| G9 golden-path 硬规则 + 标签 | pass / fail / N/A(light) | |
```

- light 链 G6~G9 标注 `N/A(light)` 并说明简化口径已满足（L1 §2b：一句话架构 + 路由/组件树描述保留，分层图/时序图策略表不强制）。
- 每个 fail 必须在「证据 / 阻塞 finding」列回指至少一条 Findings 编号；不得用「基本满足」替代逐项证据。

### 7. 三选一结论（互斥，对应 L1 §6）

- `可进入详细设计`：G1~G9 全部 pass，无 P0/P1（P3 可遗留）。
- `带明确假设可进入`：仅余已落盘的显式假设（逐条列：假设 / 依据 / 影响范围 / 验证时点），无 P0/P1。
- `不可进入`：存在 ≥1 条 P0/P1，列阻塞 P1 清单 + 修订形态建议（局部修订 / 文档级重构，按 L1 §9）。
- 发现上游需求缺陷（行为缺失/矛盾/范围漂移）→ 在结论中标注「回退需求阶段」，不在概要补造业务规则。

### 8. Gate 收口指引（结论为「可进入 / 带假设可进入」时必须输出）

按 config `guru.gate_mode` 输出对应通道（见 SKILL.md「Gate 收口」节）：

```markdown
**strict（默认）**：请用户本人在终端运行（agent 不得代跑，无 TTY 会被拒）：
python3 .trellis/scripts/guru/guru_gate.py confirm

**soft**：用户在对话中明确确认后，agent 运行：
python3 .trellis/scripts/guru/guru_gate.py confirm overview <task_dir> --via-agent --user-quote "<用户确认原话>"

确认落盘前不得进入详细设计。
```

## 复审闭环

按 findings 修订后复审：只复查受影响章节与其跨章一致性项，输出「复审范围 + 原 finding 关闭状态 + 新增 finding（若有）+ 更新后的 G1~G9 状态表与三选一结论」；不重复输出未受影响章节的全量取证。
