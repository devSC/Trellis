---
name: client-design-detail-review
description: 用于审核 Flutter 客户端详细设计文档，判定能否进入编码。先做 EX 前置检查（判轨/索引/概要 review evidence/承接源），再按 review_scope 三模式执行：current_chapter 单章诊断、layer_checkpoint 跨章协同诊断、directory_final 目录级三段式终审（逐文档 D1~D9 诊断→跨层链路→索引与时序覆盖率）。核查章节骨架符合性、合同八问、概要 owner 追溯、分层依赖律、测试映射、合规红线、删除审计与粒度；先证据后结论，输出分级 findings 与互斥三选一结论，输出 record-review 证据，并在双 clean 后等待 detail confirm。规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT。
---

# 客户端详细设计审核

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载规则正文与 G1~G7 完成条件，L2 承载类型差异；本 SKILL.md 只做前置检查、scope 编排与诊断流程；`references/review-baseline.md` 承载逐 doc_type 检查矩阵与判级，`references/review-output.md` 承载输出字段合同。冲突时 L1 > L2 > references > 本文件。

## 目标

- 审核详细设计是否达到进入编码的质量口径（L1 §7 G1~G7）。
- 逐文档诊断 + 跨章链路核对双层取证：单章合格不等于目录合格。
- 识别"薄文档"：多章雷同骨架、无单元级实质内容（一轮全量生成迹象）→ 文档级重构，不接受局部补丁。

## 最小输入与自动补全

- 输入参数：
  - `review_scope`：`current_chapter`（指定 chapter_target/batch 的文档级诊断）/ `layer_checkpoint`（按层跨章协同诊断，配 `checkpoint_layer`=domain|data|presentation|横切）/ `directory_final`（默认，目录级终审）。
  - `chapter_target` / `chapter_batch`：current_chapter 模式必填。
- 接受 task 目录或 design_package 路径；候选不唯一时先确认审核目标。

## 装载顺序与 EX 前置检查（任一失败 → 前置缺口输出，停止逐文档诊断）

1. 读 L1 主 SSOT；再读 `references/review-baseline.md` 与 `references/review-output.md`。
2. 读 golden-path 与 project-conventions（C1~C5）。
3. **EX-1 输入键**：task.json `guru_chain`（full 链含 `design_package`）可判定。
4. **EX-2 路径与骨架**：design_package/chapters/ 存在（light 链 design.md §2 存在）。
5. **EX-3 承接索引**：design-main 第 7 节（light 链 design.md §1 索引节）存在、非空、可建立 `chapter_target → doc_type → 目标文件` 完整映射。
6. **EX-4 概要 review evidence**：`guru_gate.py status` 显示 overview 当前 digest 已有两个不同 run-id 的 clean review。
7. **EX-5 承接源**：被审章节引用的技术决策均"选定"；pending L2 命中均有 `L2豁免` 声明。
8. **EX-6 机器 Gate**：`python3 .trellis/scripts/guru/guru_gate.py detail <task_dir>` 的结构结论可获取（机检失败项直接并入 findings，人工聚焦语义）。
9. 按被审文档命中的 doc_type 读对应 L2；只装载命中类型，不全量装。

## 执行规则

1. L3 不重定义 L1/L2；逐项检查回指 L1/L2 章节号。
2. 先证据后结论；finding 带「文件 + 小节/表格行」锚点。
3. **directory_final 不得跳过逐文档阶段**：每个现存目标文档必须有独立的 D1~D9 诊断与 finding 摘要；缺失目标文档只输出缺失结论与修订方案，不进入 D 诊断。
4. current_chapter 不得扩大为全目录主审，但必须读取关联锚点核对上游（概要索引/归属）与下游（被引用方）边界。
5. 「范围内/范围外」仅由概要承接索引的目标集合判定；批次/单章无 findings 只代表本范围 `findings=none`，不代表目录通过。
6. EX 失败一律回退上游（概要/判轨），不得在详细侧补造后继续审。
7. 分层依赖律违例（controller 注入 datasource、repository 绕过 datasource、usecase 环依赖等，对照 L2 硬规则）→ P1，不得给通过性结论。
8. 八问缺项、追溯断链（UNIT 引用幽灵 BHV、行为无承接）、章节闭合失败 → P1。
9. 粒度按 L1 §3.1 逐文档抽查 ≥1 个行为全流程；"见概要"式作答、无调用对象的步骤 → P1。
10. 测试映射核查覆盖成功 + 全部失败路径；高风险链路（付费/权限/数据删除）漏测 → P1，普通失败路径漏测 → P2。
11. 合规核查：权限/采集/三方域名/PII 单元的合规依据；制裁 TLD、私有 API、动态执行、真实 secret → P1。
12. 补造红线（L1 §6）：概要外结构、改 owner、拍板未选定决策、超签名级代码 → P1。
13. 薄文档判定：≥2 章骨架雷同且无单元级实质内容 → 结论直接「不可进入」+ 文档级重构建议（L1 §9），不逐条列局部 finding。
14. 详细设计文档无存量豁免；修订形态建议只引用 L1 §9。

## Full/high 实现切片 planning audit 复算

`directory_final` 对 `implement.md` 的 planning audit 独立复算，不能采信 writer
自报结论。章节批次不是实现切片边界；Flutter
domain→data→presentation→横切归属和依赖律仍须满足，但按一个 `UNIT`、
`doc_type`、层、ViewModel、UseCase 或 View 机械拆片属于 `DETAIL_DEFECT`。

1. 逐普通切片核对 `owner_unit`、`covered_units`、`read_paths`、
   `owned_paths`、`focused_checks`、`parallel_wave`、`resource_locks`、
   `resource_isolation`、`check_wave`、`independent_commit_value`、
   `rollback_contract`、`review_context_inputs`、`review_context_bytes` 和
   `rejected_merge_candidates`。`owner_unit` 必须是一个真实标量，
   `covered_units` 可含多个 Design UNIT。
2. 从实际路径集合计算同 wave 的两两 `owned_paths` 交集，必须为空；每个
   mutable path 只有一个 ordinary slice **mutable owner**，不得按 symbol、
   函数、类或 hunk 分摊。每个被修改的测试文件也只能有一个 owner。
3. 普通切片默认 `depends_on=[]`。非空项须指向被消费的真实输出 bytes；
   接口、schema、digest、错误语义和共享结构应在确认后的 Detail 先冻结。
   UNIT、章节、doc_type、层级或 review 顺序推导的依赖一律判缺陷。
4. 对冲突的 `resource_locks`，确认独立 worktree/cache/output 隔离，或确认
   checks 已分配串行 `check_wave`；两者都没有则必须合并切片。普通切片只能有
   focused checks，full regression 只能出现于 Integration。
5. 普通切片默认最多四个；例外须逐片证明独立 commit 价值与独立 rollback
   价值。缺任一价值的候选必须合并；`rejected_merge_candidates` 必须列出每个
   已考虑但拒绝的合并集合及保持分离理由。
6. 按 `review_context_inputs` 的精确、有序 inventory 重新读取同一 snapshot：
   只选 packet、planning audit、target diff/owned paths、相关 frozen contracts
   和 focused evidence，逐项复算选择范围的 UTF-8 bytes，再求精确整数总和。
   总和必须等于 `review_context_bytes` 且 `<= 262144`；wildcard、“相关文件”、
   估算值或只写不等式均不合格。
7. 确认恰好一个 Integration Slice，依赖全部普通切片，packet coverage 覆盖
   普通 target union，且实际写范围仅为 `integration_owned_paths`。它只能补
   集成字节、跨切片 invariant、full regression 与最终 spec/sync 检查，不得
   重写普通 owner 核心字节。
8. Full/high planning 时，从当前 route/platform contract 解析适用的
   `flutter-implementation-guru-writing` 及其实际引用的 contracts（Flutter
   没有独立 implementation standard），并将其作为只读 guidance 校验：其声明契约
   须消费已确认的 packet/planning audit，
   且 ordinary checks 须保持 packet-focused。不得把这些 framework 文件分配
   给 application slice，不得依赖固定 `slice_id`、新增 planning-audit 字段或
   修改已确认的 `implement.md`；实际 framework 维护归属与 receipt bookkeeping
   由相应 framework maintenance task、Integration validation 或 coordinator 处理。

任一复算失败都产生 P1 `DETAIL_DEFECT`，不得输出 clean review 或进入
`confirm detail`。

## 诊断流程

**Step 1** EX-1~EX-6（全部 scope 模式都执行）。
**Step 2** 解析 review_scope：
- `current_chapter`：对指定章节执行 D1~D9 + 上下游边界核对。
- `layer_checkpoint`：按 checkpoint_layer 执行 L1 §5.4 对应核对项的跨章取证。
- `directory_final`（默认）三段式：① 逐现存目标文档 D1~D9，产出 per_document_results[]；② 基于①核对跨层链路（presentation→domain→data→横切 调用与状态流闭合）；③ 核对概要索引目标、UC 承接表、时序图与详细正文的覆盖率。

**逐文档诊断 D1~D9**：
- D1 骨架符合性：L1 §4 模板节齐全（含 N/A 声明）；doc_type/l2_status 头部标注正确。
- D2 八问完整性：逐 UNIT 八问可回指可验证信号。
- D3 追溯核查：UNIT↔BHV 闭合；状态写 owner 回指概要归属表；依赖出现在概要架构图。
- D4 分层一致性：依赖声明对照分层律 + 命中 L2 硬规则。
- D5 粒度判定：抽查行为流程详述（L1 §3.1 四条）。
- D6 测试映射：成功+失败路径覆盖；测试层合理。
- D7 合规核查：规则 11。
- D8 补造红线：规则 12 + 错误表↔失败路径 BHV 对应。
- D9 删除审计：对破坏性删除/压缩/替换检查 deletion ledger； obsolete fact 删除、合同迁移、N/A 声明、blocking contract loss 必须区分。L1 章节骨架消失、仍有效 UNIT/BHV/行为合同被 endpoint/interface 覆盖替代、测试映射或不得补造清单丢失 → P1。

**Step 3** Findings 组织与修订形态判定（L1 §9）。
**Step 4** 输出（按 review-output.md 合同）。

## 输出（互斥分支）

- **前置失败**：仅输出 EX 缺口与修复动作（含回退指向）。
- **前置通过**：按 `references/review-output.md`——scope 声明 → 逐文档概况表 → findings 分级 → 跨层链路状态（directory_final）→ G1~G7 状态表 → **三选一结论**（可进入编码 / 带明确假设可进入 / 不可进入）→ 修订形态建议。

## 边界约束

- 详细设计文档无存量豁免；审核不代写合同正文。
- 审核项必须能回到 L1/L2 的正向方法，不做"有没有写某个词"的形式检查。

## 与官方 Trellis skill 的边界

本 skill 是 Phase 1 的详细 Gate 判定：详细设计不达标不得 `task.py start`。区别于 `trellis-check`（实现后代码质检）。

## Review Evidence 与 detail 确认

结论为「可进入编码」或「带明确假设可进入」时，先写入 review evidence，不直接开始实现：

```bash
python3 .trellis/scripts/guru/guru_gate.py record-review detail <task_dir> \
  --result clean \
  --max-severity low \
  --reviewer clean-context \
  --run-id <fresh-run-id> \
  --evidence "<本次 detail review 证据摘要>" \
  --deletion-audit "<none|删除审计摘要>"
```

若存在 medium+ finding，必须输出 `--result findings --max-severity medium|high|critical --finding-class REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|IMPLEMENT_DEFECT|PROCESS_DEFECT`，并停止进入编码。

当前 digest 下两个不同 `run_id` 的 clean review 记录后，提示用户运行：

```bash
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir>
```

confirm detail 的 strict/soft 通道以 workflow Trellis System 节为准；未确认前不得 `task.py start`。

## 参考资料

- 详细阶段中立规范（L1）：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- 类型差异（L2）：`.trellis/spec/harness/detail/detail-type-*.md`
- 逐 doc_type 检查矩阵与判级：`references/review-baseline.md`
- 输出字段合同：`references/review-output.md`
