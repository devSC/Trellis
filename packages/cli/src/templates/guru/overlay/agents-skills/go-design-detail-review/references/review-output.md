# Go 详细审核输出合同（references）

> 输出分支、字段与顺序以本文件为唯一主定义；与其它说明冲突时以本文件为准（规则正文仍以 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md` 为准，取证矩阵见 `references/review-baseline.md`）。
> 规则回指口径：用结构化字段 `rule_ref=<规范文件路径#锚点>`，不复制规则正文。D1~D9 / G1~G7 / EX-1~EX-6 / P1~P3 编号即 SKILL.md 与 L1 同名项。

## 分支一：前置缺口输出（EX-1~EX-6 任一失败）

仅输出 EX 缺口与最小修复动作，不进入逐文档诊断。EX-3/EX-4/EX-5/EX-6 类缺口的修复动作必须写「回退概要 / 判轨 / 项目约定 / 需求」而非详细侧补造。

```markdown
## 详细审核：前置阻断

### 执行前置条件结果
- EX-1 输入键（guru_chain full/light 判轨）：`ok/failed`
- EX-2 路径与骨架（full: design_package/chapters/ 存在且边界合法；light: design.md §详细节存在）：`ok/failed`
- EX-3 承接索引（chapter_target → detail_doc_type → 目标文件 完整映射，doc_type 落七类全集）：`ok/failed`
- EX-4 概要 review evidence（guru_gate.py status 显示 overview 当前 digest 已有两个不同 run_id 的 clean review）：`ok/failed`
- EX-5 承接源 + 项目约定（技术决策 SLOT-01~SLOT-17 已选定，待定槽位 ≤2 且写明决策人/期限；pending L2 命中类型有 L2豁免；C1~C5 通过）：`ok/failed`
- EX-6 机器 Gate（guru_gate.py detail / trace-matrix --strict 结构结论可获取）：`ok/failed`

### EX 缺口（逐条）
- EX-<id> ｜ 缺口：<具体缺什么> ｜ 证据：<文件:小节 或 明确缺失对象>

### 修复动作（逐条最小动作）
- <动作；EX-3/EX-4/EX-5/EX-6 类必须写「回退概要/判轨/项目约定/需求」>

### 三类承接源状态（不伪造 Gate）
- capability 承接源：`skipped_by_ex_precheck_failure:<EX-id>`
- technology_decision 承接源：`skipped_by_ex_precheck_failure:<EX-id>`
- backward_compatibility 承接源：`skipped_by_ex_precheck_failure:<EX-id>`

### 结论
前置未通过，不进入逐文档诊断。
```

## 分支二：诊断输出（前置通过）

按以下小节顺序输出（与 SKILL.md「输出（互斥分支）」一致）。

### 1. scope 声明

```markdown
- review_scope：`current_chapter(<chapter_target/chapter_batch>)` / `layer_checkpoint(<domain|repository|service|transport|横切>)` / `directory_final`
- 链型：`full` / `light`
- 本轮范围内目标清单：`<chapter_target 列表>`
- 范围外未审清单：`<明示「范围外未审」，防误读为通过>`
- partial scope（仅 current_chapter 收窄时）：`chapter_subscope` / `behavior_subset` 描述
- covered_items[]：`<本轮已覆盖的 endpoint/route+method/behavior/entity/runtime_unit 列表 | not_applicable_by_full_chapter_scope | not_applicable_by_review_scope>`
- not_covered_items[]：`<同一 canonical chapter_target 内未覆盖项 | [] | not_applicable_by_full_chapter_scope | not_applicable_by_review_scope>`
- canonical_publish_status：`complete_by_full_scope_review | not_applicable_by_partial_scope | not_applicable_by_review_scope`
- scope_findings_summary：`none_in_current_scope | findings_present`
- directory_final_required：`required_after_chapter_loop | not_applicable_by_directory_final`
```

### 2. 逐文档概况表（current_chapter / directory_final 必含）

每个现存目标文档一行独立 D1~D9 诊断（directory_final 不得跳过逐文档阶段）。

```markdown
| 章节(chapter_target) | doc_type | l2 | entry_kind | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | findings |
|----------------------|----------|----|------------|----|----|----|----|----|----|----|----|----|----------|
| 03-biz-user-service-design | biz | v1 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | P2×1 |
```

- 状态符号：`✅` 通过 / `⚠️` 有 P2/P3 / `❌` 有 P1 / `N/A` 非适用（须在 findings 列或下方注明依据）。
- 缺失目标文档单列（不进 D 诊断）：`缺失清单 + 修订方案`。
- per_document_results[]（与表同源，可结构化展开）：每条含 `chapter_target` / `detail_doc_type` / `l2_status` / `entry_kind`（仅 entry-api）/ `loaded_l2_ref`（命中 v1 类型 SSOT 或 `pending_no_l2`）/ `D1~D9 结果` / `findings_refs[]`。

### 3. Findings（按严重度分组，每条五字段 + 受影响 Gate 项）

同根因合并为一条，列全部位置；判级冲突取高。

```markdown
**P1-1** ｜ location：03-biz-user-service-design §4.1 UNIT-user-service
｜ problem：UserService.Create 流程详述只写「调用 repository 创建用户」，无具体方法/参数/失败分支（粒度不达标，无法直接编码）
｜ evidence：流程详述第 2 步缺 `repo.Create(ctx, params)` 调用对象与 ErrValidation 返回点
｜ suggestion：按 L1 §3.1 补步骤——字段校验失败 `%w: ErrValidation`、`repo.Create(ctx, params)`、`routeSync.SyncUser(ctx, user.ID)` 失败上抛
｜ rule_ref：.trellis/spec/harness/detail/detail-structure-single-source.md#31-粒度标准四条写作与审核共用
｜ 受影响 Gate 项：G2
```

- 五字段：`location`（`<chapter_target> §<节> UNIT-<slug>` 或明确缺失对象）/ `problem` / `evidence`（正文摘录或字段断点）/ `suggestion`（最小修订；形态判定只引用 L1 §9）/ `rule_ref`。
- 受影响 Gate 项：回指 §6 的 G1~G7。
- 薄文档命中时（review-baseline §6）：跳过逐条列举，输出薄文档证据（雷同章节对照 + 占位统计）+ 文档级重构方案。

### 4. 跨层调用链状态（directory_final / layer_checkpoint 必含）

按 review-baseline §4 六个层边界逐项 pass/fail + 失效位置。

```markdown
| 层边界 | 状态 | 失效位置 / 证据断点 |
|--------|------|---------------------|
| transport→service | ok/risk | — |
| service→repository | ok/risk | — |
| repository→domain | ok/risk | — |
| domain | ok/risk | — |
| 横切(config/external/runtime) | ok/risk/not_applicable_by_review_scope | — |
| 全局(状态写 owner 唯一/sentinel 跨章一致) | ok/risk | — |
```

current_chapter 模式此节写 `not_applicable_by_review_scope`，但仍回填当前目标的上下游关联边界摘要。

### 5. 概要承接索引与时序覆盖率状态（directory_final 必含）

按 review-baseline §5 五项。

```markdown
- 索引↔章节双向差集：`目标总数=<N>，命中=<N>，缺失=<N>`（列缺失/孤儿文件）
- 归属表 owner 覆盖：`<每个 transport/service/repository/domain owner 是否被 ≥1 UNIT 覆盖>`
- UC 链路抽查：`<抽查 UC 在详细侧 entry→biz→repository→domain 是否走通>`
- 时序↔行为抽查：`<抽查 ≥1 UC 时序步骤在对应章节有同名行为与一致方向>`
- technology_decision 展开链：`<detail_expansion_targets 是否有承担它的目标 doc_type 章节>`
```

current_chapter 模式只回填当前目标覆盖证据并保留 `directory_final_required=required_after_chapter_loop`。

### 6. 详细 Gate 状态表（G1~G7）

对照 L1 §7 逐项。light 链 G6~G7 标注 `N/A(light)` 并说明单文件口径已满足。

```markdown
| G 项 | 含义 | 状态 | 证据 / 阻塞 finding |
|------|------|------|---------------------|
| G1 | 承接索引每条有详细单元，归属表 owner 全覆盖 | pass/fail | — |
| G2 | 八问完整 + 字段/接口/状态/sentinel 可追溯 owner + §3.1 粒度 + 分层依赖律 + 错误范式可验证 | pass/fail | P1-1 |
| G3 | 每条行为测试映射覆盖成功 + 全部失败路径（含 ctx 超时、sentinel 分支） | pass/fail | — |
| G4 | 鉴权/会话/采集/三方域名/PII 单元附合规依据；无私有 API/动态执行/明文 secret | pass/fail | — |
| G5 | 八问 8（不得补造清单，含分层越界禁止项）逐单元存在 | pass/fail | — |
| G6 | 章节闭合（索引↔文件双向）+ 每章符合 §4 骨架 + pending L2 豁免齐全 | pass/fail/`N/A(light)` | — |
| G7 | chapter_loop 证据（逐章 chapter_status=passed_by_method_evidence + 五层 checkpoint + 无一轮全量生成迹象） | pass/fail/`N/A(light)` | — |
```

### 7. 三选一结论（互斥）

按 review-baseline §8：

- `可进入实现编码`：无 P1/P2。
- `带明确假设可进入`：仅 P2 且每条有修订路径；逐条假设、依据、验证时点。
- `不可进入`：任一 P1；阻塞 P1 清单 + 修订形态建议（局部修订 / 文档级重构，按 L1 §9；概要缺陷标注「回退概要」）。

### 8. 修订形态建议（L1 §9）

- 局部修订：补 sentinel error 枚举、补测试映射、补一条依赖声明、补一张时序图、补一个错误转换位置、补 context/timeout 透传声明、补事务边界结论。
- 文档级重构：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档）、分层归属系统性错位、错误范式整体偏离 sentinel 三件套。
- 概要缺陷（归属错、索引漏、技术决策/SLOT 槽位未选定）→ 回退概要修订，禁止详细侧就地改归属或私自拍板槽位。

### 9. Review Evidence（结论为可进入 / 带假设可进入时必须输出）

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

### 10. Gate 收口指引（结论为可进入 / 带假设可进入时必须输出）

```markdown
请按 config guru.gate_mode 完成人工收口：
- strict（默认）：请用户本人在终端运行（agent 不得代跑，无 TTY 会被拒）：
  python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir>
- soft：用户对话中明确确认后，agent 运行（记录留痕标注 soft/agent）：
  python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir> --via-agent --user-quote "<用户确认原话>"
确认落盘后方可 task.py start（before_start 钩子强制校验）。
```

## 必填回填字段（所有分支）

- `review_scope`、`per_document_results[]`、`partial_chapter_scope` / `covered_items[]` / `not_covered_items[]` / `canonical_publish_status`（无 partial scope 时按非适用分支：`not_applicable_by_full_chapter_scope` 或 `not_applicable_by_review_scope`）。
- 不适用字段一律用 `not_applicable_by_review_scope`；前置失败用 `skipped_by_ex_precheck_failure:<EX-id>`；缺失目标文档用 `skipped_by_missing_target_docs:{missing_target_docs}`。

## 复审闭环

按 findings 修订后复审：只复查受影响章节的 D 诊断 + 其跨层引用，输出「复审范围 / 原 finding 关闭状态 / 新增 finding / 更新后 G 状态与结论」。current_chapter 复审通过不改变目录级结论——目录级结论只能由 directory_final 产生。
