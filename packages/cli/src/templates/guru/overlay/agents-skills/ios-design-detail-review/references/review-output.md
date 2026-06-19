# iOS 详细审核输出合同（references）

> 输出分支、字段与顺序以本文件为唯一主定义；与其他说明冲突时以本文件为准（规则正文仍以 `index.md` / L1 / L2 为准，判级口径见 `review-baseline.md`）。
> 规则回指用结构化 `rule_ref=<规范文件#锚点>`，不复制规则正文。doc_type 一律用 IOS_BRIEF 权威七类（`viewmodel`/`usecase`/`repository`/`domain-model`/`view`/`coordinator`/`external`）。
> 详细 Gate 口径对齐 L1（`detail-structure-single-source.md` §7）的 **G1~G8**（G1~G5 两轨共用，G6~G8 仅 full 链强制）；light 链 G6~G8 标 `N/A(light)` 并说明单文件口径已满足。

## 分支一：前置缺口输出（EX-1~EX-6 任一失败）

仅输出 EX 缺口与最小修复动作，不进入逐文档诊断。EX-3/EX-4/EX-5/EX-6 类缺口（承接索引断链、概要 review evidence 未达标、承接源未选定、机器 Gate 断链）必须写「回退概要 / 项目约定 / 需求」，不得在详细侧补造。

```markdown
## 详细审核：前置阻断

**review_scope**：<current_chapter / layer_checkpoint(<层>) / directory_final>
**EX 缺口**（逐条：EX 编号 / 缺口 / 证据锚点）
- EX-<id> ｜ <缺口一句话> ｜ 证据：<文件:小节 / 命令输出断点>
**修复动作**（逐条最小动作；EX-3/EX-4/EX-5/EX-6 类必须写「回退概要/项目约定/需求」而非详细侧补造）
1. <动作>
**三类承接源状态**：均写 `skipped_by_ex_precheck_failure:<EX-id>`（不伪造 Gate 状态）
- ui_framework_network_persistence_handoff_status：skipped_by_ex_precheck_failure:<EX-id>
- technology_decision_handoff_source_status：skipped_by_ex_precheck_failure:<EX-id>
- project_conventions_c1_c5_status：skipped_by_ex_precheck_failure:<EX-id>
**结论**：前置未通过，不进入逐文档诊断。
```

EX 编号语义（详见 SKILL.md「装载顺序与 EX 前置检查」）：EX-1 输入键 / EX-2 路径与骨架 / EX-3 承接索引（`chapter_target → doc_type` 七类映射，双向闭合）/ EX-4 概要 review evidence（`guru_gate.py status` 显示 overview 当前 digest 已有两个不同 `run_id` 的 clean review）/ EX-5 承接源 + 项目约定 C1~C5 + pending L2 豁免 / EX-6 机器 Gate（`detail` + `trace-matrix --strict`）。

## 分支二：诊断输出（前置通过）

输出顺序固定为：scope 声明 → 逐文档概况表 → Findings 分级 → 跨层调用链状态 → 概要承接索引与时序覆盖率状态 → 详细 Gate 状态表 → 三选一结论 → 修订形态建议 → Gate 收口指引。

### 1. scope 声明

```markdown
- review_scope：<current_chapter / layer_checkpoint(checkpoint_layer=<domain-model|repository|usecase|viewmodel|横切>) / directory_final>
- 范围内目标清单：<chapter_target 列表（裸 token / chapters/<slug>.md）>
- 范围外未审清单：<明示「范围外未审」，防止误读为通过>
- partial_chapter_scope：<chapter_subscope / behavior_subset 描述 | not_applicable_by_full_chapter_scope | not_applicable_by_review_scope>
- covered_items[]：<本轮已覆盖的行为/字段/实体列表 | not_applicable_by_full_chapter_scope>
- not_covered_items[]：<同一 canonical chapter_target 内未覆盖项 | [] | not_applicable_by_full_chapter_scope>
- canonical_publish_status：<complete_by_full_scope_review | not_applicable_by_partial_scope | not_applicable_by_review_scope>
- scope_findings_summary：<none_in_current_scope | findings_present>
- directory_final_required：<required_after_chapter_loop | not_applicable_by_directory_final>
```

`current_chapter` / partial scope 提醒：批次/单章无 Findings 只代表本范围 `findings=none`，不代表目录通过；partial scope 无 Findings 只代表 `covered_items[]` 干净，须回填 `not_covered_items[]` 与 `canonical_publish_status=not_applicable_by_partial_scope`，并保留 `directory_final_required`。

### 2. 逐文档概况表（current_chapter / directory_final 必含）

`per_document_results[]` 以表呈现，每个现存目标文档一行，D1~D9 逐列打钩（✅ 通过 / ⚠️ P2 / ❌ P1 / N/A）：

```markdown
| 章节(chapter_target) | doc_type | l2 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | findings |
|----------------------|----------|----|----|----|----|----|----|----|----|----|----|----------|
| 5-usecase-manage-ai-models-design | usecase | v1 | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | P2×1 |
```

- 缺失目标文档单列：`缺失清单 + 修订方案`（不进 D 诊断）；`per_document_results[]` 对应行写 `skipped_by_missing_target_docs:{missing_target_docs}`。
- 文档分流结果：`existing_target_docs=<列表>`，`missing_target_docs=<列表>`。
- 薄文档命中时（review-baseline §6）：跳过本表逐列，改输出薄文档证据（雷同章节对照 + 占位统计：空字段表数 / 无签名方法数 / sequenceDiagram 缺失章数 / 测试映射 ≤1 行的章数）+ 文档级重构方案。

### 3. Findings（按严重度分组，每条五字段 + 受影响 Gate 项）

五字段固定为 `location / problem / evidence / suggestion / 受影响 G 项`（受影响 G 项指 L1 §7 的 G1~G8）。同根因合并为一条、列全部位置；判级冲突取高。

```markdown
**P1-1** ｜ location：chapters/4-usecase-generate-story-design.md §4.2 downloadAIModel
｜ problem：底层 AIModelDownloaderError 裸抛给 viewmodel（缺单点错误映射）
｜ evidence：异常处理表「下载启动失败」行未标 [SLOT-error-mapping] 转换位置，无 mapXxxErrorToUseCaseError
｜ suggestion：在 usecase 边界把 AIModelDownloaderError 映射为 ManageAIModelsError 本域 case 再上抛（局部修订，L1 §9）
｜ 受影响 G 项：G2（八问 5）、rule_ref=detail-type-usecase.md#类型硬规则（R4）

**P2-1** ｜ location：chapters/6-repository-ai-model-design.md §4.3 deleteModel
｜ problem：多写操作未标注事务形态
｜ evidence：含两条写（删行 + 删本地文件索引）但无 performTransaction 与「中途失败全回滚」不变量
｜ suggestion：标注 performTransaction 并写回滚不变量（局部修订）
｜ 受影响 G 项：G2、rule_ref=detail-structure-single-source.md#31-粒度标准四条写作与审核共用
```

### 4. 跨层调用链状态（directory_final / layer_checkpoint 必含）

按 review-baseline §4 的五个层边界逐项 pass/fail + 失效位置：

```markdown
- view → viewmodel：<ok | risk:{失效位置 / 证据断点 / rule_ref}>
- viewmodel → usecase：<ok | risk:{...}>
- usecase → repository(接口)：<ok | risk:{...}>
- repository(实现) → external：<ok | risk:{...}>
- 全局(状态写 owner 唯一 / enum Error 跨章一致 / 导航经 coordinator / DI 装配闭合)：<ok | risk:{...}>
- directory_chain_review：<ok | not_applicable_by_review_scope | risk:{链路类型 / 涉及章节 / 证据断点 / rule_ref}>
```

`current_chapter` 时 `directory_chain_review` 写 `not_applicable_by_review_scope`（或仅回填当前目标关联边界摘要），并保留 `directory_final_required`。

### 5. 概要承接索引与时序覆盖率状态（directory_final 必含）

按 review-baseline §5 三项：

```markdown
- 索引↔章节差集：目标总数=<N>，命中=<N>，缺失=<N>；孤儿章节=<列表 | 无>
- 归属表 owner 覆盖：<全部 owner 被索引覆盖 ok | 缺口:{owner / rule_ref}>
- UC 链路抽查：<抽查 UC-<n> 链路可走通 ok | risk:{断点}>
- 时序覆盖率抽查：<抽查 UC-<n> 时序步骤在 §4.x 有同名行为 ok | risk:{失配 / sequenceDiagram 出现 View 直连持久化}>
- overview_coverage_review：<ok | not_applicable_by_review_scope | risk:{overview_ref / 缺口类型 / 缺失或漂移目标 / rule_ref}>
```

### 6. 详细 Gate 状态表（G1~G8）

```markdown
| G 项 | 状态 | 证据 / 阻塞 finding |
|------|------|---------------------|
| G1 索引条目↔单元齐全、doc_type ∈ 七类 | <pass/fail/N/A(light)> | <证据锚点 / finding 编号> |
| G2 合同八问完整 + 可追溯 owner + 粒度（§3.1） | <...> | <...> |
| G3 测试映射覆盖成功 + 全部失败路径、框架/mock 符槽位 | <...> | <...> |
| G4 权限/采集/三方域名/PII/交付面合规依据，无私有 API/动态执行/制裁 TLD | <...> | <...> |
| G5 八问 8（不得补造清单）逐单元存在、含越层禁止项 | <...> | <...> |
| G6 章节闭合（索引↔chapters 双向）+ §4 骨架 + pending L2 豁免齐全 | <pass/fail/N/A(light)> | <...> |
| G7 分层依赖律全过（Domain 零依赖/单向无环/view 不导航不持久化/repository 接口实现分离） | <pass/fail/N/A(light)> | <...> |
| G8 chapter_loop 证据 + 编号双向闭合（无幽灵 BHV/无无承接 UNIT）、无一轮全量生成迹象 | <pass/fail/N/A(light)> | <...> |
```

### 7. 三选一结论（互斥）

- **可进入实现编码**：无 P1/P2，或 P2 全部已即时闭合。
- **带明确假设可进入**：仅 P2 且每条有明确修订路径——逐条列「假设 / 依据 / 验证时点」。
- **不可进入**：存在 P1——列阻塞 P1 清单 + 修订形态建议（概要缺陷标注「回退概要」）。

### 8. 修订形态建议（L1 §9）

逐条 Finding 标注 `局部修订` 或 `文档级重构`：

```markdown
- 局部修订：补 enum Error 枚举、补测试映射、补一条依赖声明（含 @Injected 项）、补一张 sequenceDiagram、补一条不得补造项、回填时序占位锚点、补 l2_status 标注。
- 文档级重构：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档）、分层依赖律系统性违反（view 普遍直连持久化 / usecase 依赖 viewmodel）、doc_type 系统性越界。
- 概要缺陷（归属错 / 索引漏 / 技术决策未选定）→ 回退概要修订，禁止在详细侧就地改归属或私自拍板。
```

### 9. Review Evidence（结论为「可进入」/「带明确假设可进入」时必须输出）

```markdown
python3 .trellis/scripts/guru/guru_gate.py record-review detail <task_dir> \
  --result clean \
  --max-severity low \
  --reviewer clean-context \
  --run-id <fresh-run-id> \
  --evidence "<本次 detail review 证据摘要>" \
  --deletion-audit "<none|删除审计摘要>"
```

`--deletion-audit none` 仅用于本轮确认无破坏性删除；若存在删除/压缩/替换，摘要必须覆盖 deletion ledger 的删除类别、原因、替代位置与 reviewer_decision。

### 10. Gate 收口指引（结论为「可进入」/「带明确假设可进入」时必须输出）

按 config `guru.gate_mode`（通道主定义见 workflow Trellis System 节）：

```markdown
**strict（默认）**：请用户本人在终端运行（agent 不得代跑，无 TTY 会被拒）：
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir>

**soft**：用户在对话中明确确认后，agent 运行（记录留痕标注 soft/agent）：
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir> --via-agent --user-quote "<用户确认原话>"

确认落盘前不得 task.py start（before_start 钩子强制拦截）。
```

## 必回填字段（防漏）

无论分支，结论区必须回填：`review_scope`、`per_document_results[]`（前置失败或缺失目标时写 `skipped_*` 分支）、`partial_chapter_scope` / `covered_items[]` / `not_covered_items[]` / `canonical_publish_status`、`scope_findings_summary`、`directory_final_required`。不适用字段一律用 `not_applicable_by_review_scope`，不留空、不伪造。三类承接源状态（`ui_framework_network_persistence_handoff_status` / `technology_decision_handoff_source_status` / `project_conventions_c1_c5_status`）在前置失败时写 `skipped_by_ex_precheck_failure:<EX-id>`。

## 复审闭环

按 Findings 修订后复审：只复查受影响章节的 D 诊断 + 其跨层引用，输出「复审范围 / 原 finding 关闭状态 / 新增 finding / 更新后 G 状态与结论」。`current_chapter` 复审通过不改变目录级结论——目录级结论只能由 `directory_final` 产生（`directory_final_required` 保持 `required_after_chapter_loop` 直至目录级终审完成）。
