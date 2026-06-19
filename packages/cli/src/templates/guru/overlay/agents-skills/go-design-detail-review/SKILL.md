---
name: go-design-detail-review
description: 用于审核 Go monorepo 后端（net/http + 严格分层 transport→service→repository→domain + 原生 SQL）详细设计文档，判定能否进入实现编码。先做 EX 前置检查（判轨/项目约定 C1~C5/承接索引/概要 review evidence/承接源），再按 review_scope 三模式执行：current_chapter 单章逐步骤诊断、layer_checkpoint 跨章协同诊断、directory_final 目录级三段式终审（逐文档 D1~D9 诊断 → 跨层调用链 → 概要承接索引与时序覆盖率）。核查合同八问、概要 owner 追溯、分层单向依赖律、sentinel error 收口、测试映射、合规红线与可编码粒度；编号断链拦截（单元引用幽灵 BHV / 行为无单元承接 / 切片引用幽灵 UNIT）；先证据后结论，输出分级 findings 与互斥三选一结论，输出 record-review 证据，并在双 clean 后等待 detail confirm。规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT，本文件只组织取证、Finding 与输出。
---

# Go 后端详细设计审核

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载合同八问规则正文与详细 Gate 完成条件，L2（`detail-type-{entry-api,biz,repository-data}.md`）承载类型差异与 Go 硬规则；本 SKILL.md 只做前置检查、scope 编排与诊断流程。`references/review-baseline.md` 承载逐 doc_type 取证矩阵与判级，`references/review-output.md` 承载输出字段合同。冲突时 `L1 > L2 > references > 本文件`。
> 横向硬依赖：通用方法 `.trellis/spec/guides/golden-path.md`（分层依赖律、错误处理范式、生命周期、配置/隐私/契约红线）+ 目标仓库 `.trellis/spec/conventions/project-conventions.md`（SLOT-01~SLOT-17 项目约定槽位与 C1~C5 校验）。

## 目标

- 审核详细设计是否达到「可进入实现编码」的质量口径：合同八问落地、概要承接源已选定、分层单向依赖闭合、可编码粒度成立、测试映射齐全，与 L1 详细 Gate（`guru_gate.py detail`）同口径但补充人工语义判定。
- 逐文档诊断 + 跨章调用链核对的双层取证：单章合格不等于目录合格；单章无 Findings 只代表本范围 `findings=none`，不代表全目录无 gap。
- 拦截编号断链（幽灵 BHV / 行为无单元承接 / 幽灵 UNIT），拦截越层依赖（handler 直连 DB、repository 反向 import service、service↔service 双向、状态双写），拦截设计层级越界（在详细正文展开本应延后到实现 trace 的框架生成细节）。
- 识别「薄文档」：多章雷同骨架、无单元级实质内容（一轮全量生成迹象）→ 文档级重构，不接受局部补丁。
- 本 Skill 只组织取证、Finding 与输出，不重定义 L1/L2 规范正文，也不代写合同正文。

## Go 后端模型基线（取证锚点，规则正文仍以 L1/L2 为准）

- **分层与写作顺序**：依赖方向严格单向 `transport(handler) → service → repository → domain`，无环、无双向、除 `domain` 外不跨服务 `internal/` 包互相导入。写作自底向上：① domain → ② repository-data → ③ biz(service) → ④ entry-api(transport) → ⑤ 横切（config / external / runtime）。审核取证时按依赖方向核对调用链闭合，不要求被审范围已覆盖全部上层。
- **owner 层四值**：`transport` / `service` / `repository` / `domain`。某业务状态的唯一写 owner 落在 `service`；数据访问实现落在 `repository`；入口协议物件落在 `transport`；实体/值对象/参数结构体落在 `domain`。owner 跨层即归错层 → 回退概要重判归属。
- **doc_type 全集（详细承接索引 `chapter_target → detail_doc_type` 取值）**：`entry-api` / `biz` / `repository-data` / `domain` / `config` / `external` / `runtime`。前 3 类有 v1 L2（`detail-type-{entry-api,biz,repository-data}.md`）按类型正向写法审核；后 4 类为 pending（无 L2），按 L1 合同八问展开，头部须标注 `l2_status: pending`，且 full 链须在 design-main 给出 `L2豁免：<doc_type> 理由：…` 声明（无豁免 → P1）。
- **编号纪律**：行为 `BHV-NNN`（prd 标题 `### BHV-NNN <短名>`，创建后不复用、不重排、删除留洞，以「协议端点 / 编排步骤 / 数据访问 / 失败收口」为枚举单位）；设计单元 `UNIT-<slug>`（详细标题 `### UNIT-<slug>`，kebab-case 体现服务+层角色，如 `UNIT-user-service`/`UNIT-user-repository`/`UNIT-users-handler`）；下游引用一律写裸 token。
- **统一红线（贯穿）**：`net/http ServeMux` 唯一框架（禁 gin/echo/fiber）；sentinel error + `fmt.Errorf("%w: …")` + `errors.Is()`，禁字符串比较错误、禁吞错；`main()` 控信号 → `app.New/Run/Shutdown`，handler 接 `context` 透传 timeout；`config.Load()` 集中装载（env + 默认值 + 服务前缀）；`internal/` 隐私、跨服务契约只走 `packages/contracts/`；密钥只写环境变量名引用，禁落真实 key。任一红线违例 → P1（阻断），不可豁免。

## 最小输入与自动补全

- 输入参数：
  - `review_scope`：`current_chapter`（指定 `chapter_target`/`chapter_batch` 的文档级逐步骤诊断）/ `layer_checkpoint`（按层跨章协同诊断，配 `checkpoint_layer` ∈ {domain, repository, service, transport, 横切}）/ `directory_final`（默认，目录级三段式终审）。
  - `chapter_target` / `chapter_batch`：`current_chapter` 模式必填；若用户自然语言显式指定一个 `chapters/<slug>.md` 文件，执行期先反查其在概要承接索引中的 `chapter_target → detail_doc_type`，再据此装载对应 L2。
  - `chapter_subscope` / `behavior_subset`（可选）：在已定 target/batch 内收窄本轮审核项（如多 route 的 endpoint 子集、多实体的 entity 子集）；不改变承接索引目标集合或类型判定。
- 接受 task 目录或 `design_package` 路径（full 链）/ 任务内 `design.md`（light 链）；候选不唯一时先确认审核目标。
- 其它扩展输入只归档，不参与目标范围、类型、owner 或承接源判定。

## 装载顺序与 EX 前置检查（任一失败 → 前置缺口输出，停止逐文档诊断）

1. 读 L1 主 SSOT：`.trellis/spec/harness/detail/detail-structure-single-source.md`；再读 `references/review-baseline.md` 与 `references/review-output.md`。
2. 读 `.trellis/spec/guides/golden-path.md`（分层依赖律、错误范式、生命周期、红线清单）与 `.trellis/spec/conventions/project-conventions.md`（执行 C1~C5 校验）。
3. **EX-1 输入键**：task.json `guru_chain`（full 链含 `design_package` 字段，相对 repo root）可判定；判轨结果决定 full（目录级设计包）/ light（任务内单文件 `design.md`）口径。
4. **EX-2 路径与骨架**：full 链 `design_package/chapters/` 目录存在且路径边界合法；light 链 `design.md` §详细节存在。
5. **EX-3 承接索引**：concept `design-main.md` 详细设计承接索引（light 链 `design.md` 索引节）存在、非空，可建立 `chapter_target → detail_doc_type → 目标文件` 完整映射，且 doc_type 取值落在七分类全集内。
6. **EX-4 概要 review evidence**：`python3 .trellis/scripts/guru/guru_gate.py status` 显示 overview 当前 digest 已有两个不同 run-id 的 clean review；缺 evidence → 回退概要 review/fix loop。
7. **EX-5 承接源 + 项目约定**：被审章节引用的技术决策（鉴权机制、ORM/驱动、API 风格、配置加载、迁移工具等映射到 SLOT-01~SLOT-17）均已「选定」（待定槽位 ≤ 2 且写明决策人/期限）；命中 pending L2 的 doc_type 均有 `L2豁免：<doc_type> 理由：…` 声明（full 链；缺即 P1）；项目约定 C1~C5 全部通过。
8. **EX-6 机器 Gate**：`python3 .trellis/scripts/guru/guru_gate.py detail <task_dir>` 与 `guru_gate.py trace-matrix <task_dir> --strict` 的结构结论可获取（机检失败项——合同八问四标记缺失、章节闭合失败、编号断链、pending L2 拦截——直接并入 findings，人工聚焦语义判定，不重复机检）。
9. 按被审文档命中的 doc_type 读对应 L2；只装载命中类型（`entry-api`/`biz`/`repository-data`），不全量装；pending doc_type 不装 L2（已不存在），按 L1 八问取证 + 豁免核查。

## 执行规则

1. L3 不重定义 L1/L2 规则正文；每项检查回指 L1 章节号或 L2 硬规则条目（`rule_ref=<规范文件路径#锚点>`）。
2. 先证据后结论；每条 Finding 带「文件 + 小节/表格行/签名」锚点或明确缺失对象，再给最小修订方案；修订形态判定只引用 L1 修订形态章。
3. **directory_final 不得跳过逐文档阶段**：每个现存目标文档必须有独立的 D1~D9 诊断与 Finding 摘要；不得先输出整体通过/风险结论再补零散文档证据。缺失目标文档只输出缺失结论 + 修订方案，不进入 D 诊断。
4. `current_chapter` 不得扩大为全目录主审，但必须读取关联锚点核对上游（概要承接索引/归属表）与下游（被引用的 service/repository/domain 合同）边界；目录级完整复审标记为 `directory_final_required`。
5. 「范围内/范围外」仅由概要承接索引的目标集合判定；批次/单章无 Findings 只代表本范围 `findings=none`，不代表目录通过；partial scope 无 Findings 只代表 `covered_items[]` 无 Findings。
6. EX 失败（尤其 EX-3/EX-4/EX-5/EX-6 断链或承接源未选定）一律回退上游（概要/判轨/项目约定/需求），不得在详细侧补造后继续审；不得在详细阶段首次补造鉴权机制、ORM/驱动选型、API 风格或配置方案等本属概要/项目约定的决策。
7. **分层依赖律违例**（handler 注入/直连 repository 或 `database/sql`/`lib/pq`、repository 反向 import service、service↔service 双向依赖与环、协议物件 `http.Request`/`ResponseWriter` 进入 service、跨服务导入除 domain 外的 `internal/` 包）→ P1（阻断），不得给通过性结论。
8. **编号断链**（单元引用 prd 不存在的 `BHV-NNN` = 幽灵行为、行为无任何 `UNIT-<slug>` 承接、实现切片引用不存在的 `UNIT-<slug>` = 幽灵单元）→ P1；八问缺项、概要 owner 不一致或承接不闭合、章节闭合失败 → P1。
9. **状态唯一写 owner**：同一业务状态出现在两个 service 合同里 = 状态双写 P1（回概要重判归属）；handler/repository 持有业务状态 = 归错层 P1。
10. **错误收口范式**：service 须给 sentinel error 全集逐条（区分业务可恢复/系统不可恢复）；handler 须给「入口校验失败 / service sentinel error / 兜底未知错误」三态到 HTTP 状态码的映射表，且每个 sentinel 有 `errors.Is` 分支、存在兜底 500；出现字符串比较错误、吞错（`_ = err`/裸 `return`）、handler 自造平行错误体系、内部错误文案直接回客户端 → P1。
11. **粒度判定**：按 L1 可编码粒度逐文档抽查 ≥1 个行为全流程——步骤逐条有具体被调用的下层方法与参数、本单元内部判定、错误返回点与状态写入点；「见概要」「处理 XX 能力」「调用 service」式无调用对象的作答 → P1。事务边界须三选一给结论（无显式事务 / 本地数据库事务 / 一致性模式），缺结论 → P2。
12. **测试映射核查**：每条承接行为 ≥1 成功用例 + 全部失败路径各 1 用例，逐行映射 `BHV-NNN`/`UNIT-<slug>`，测试层合理（biz 用 mock repository 的 unit test、handler 用 `httptest` + mock service、repository 用集成测试）；高风险链路（鉴权/会话/数据删除/迁移/付费）漏测 → P1，普通失败路径漏测 → P2。
13. **合规核查**：鉴权/密钥/PII 单元的合规依据；扫描硬编码 secret、真实 API key、密码/盐字面量、`.env` 当线上合同、制裁 TLD、私有 API、动态执行；密钥须只写环境变量名引用回指 config（SLOT-08/SLOT-10）。任一命中 → P1。
14. **补造红线 + 设计层级越界**：概要外结构、改 owner、拍板未选定槽位、超签名级实现体（>15 行实现体视为越界信号）→ P1；go-guru profile 命中时在业务详细正文展开 generated Repo 方法表、`PropertyFilter/PageRequest/WithTx`、`*_guru.pb.go`、ProviderSet/Wire、proto/buf generate 细节（除非仅出现在 `framework_reference_ref`/实现期参考字段）→ 设计层级越界 P1。
15. **薄文档判定**（优先于逐条 Finding）：≥2 章骨架雷同且无单元级实质内容（参数表空 / 流程详述 <3 步 / 测试映射 ≤1 行）→ 结论直接「不可进入」+ 文档级重构建议，不逐条列局部 Finding。
16. 详细设计文档无存量豁免（SLOT-17 存量豁免只在实现/审核阶段对代码生效，不为详细设计缺陷开口）；修订形态建议只引用 L1 修订形态章。

## 诊断流程

**Step 1** 执行 EX-1~EX-6（全部 scope 模式都执行；不得因只审小批次而跳过概要承接源、项目约定、技术决策判定）。

**Step 2** 解析 `review_scope`：

- `current_chapter`：对指定章节执行 D1~D9 + 上下游边界核对；有 `chapter_subscope`/`behavior_subset` 时只对 `covered_items[]` 诊断，未覆盖项进 `not_covered_items[]`，回填 `canonical_publish_status=not_applicable_by_partial_scope`，并记录跨章待闭合风险。
- `layer_checkpoint`：按 `checkpoint_layer` 执行跨章协同诊断，不要求未来层级正文已存在。
  - `domain`：实体/值对象/参数结构体主语义唯一，序列化 tag 一致；被上层引用的 domain 类型已定义、无反向依赖。
  - `repository`：每个 `<Entity>Repository` 接口被某 service 声明消费；`ErrNotFound` 等数据层错误转换位置两侧一致；无业务判定下沉、无反向 import service。
  - `service`：业务状态写 owner 全局唯一；service↔service 单向无环；sentinel error 全集与 handler 映射一致；承接 P0/P1 核心能力已拆为可编码步骤。
  - `transport`：每个 `route+method` 绑定独立 `BHV-NNN`、handler 方法、目标 service 方法；context 透传；错误三态映射闭合；不直连 repository/DB。
  - `横切`（config/external/runtime）：config key 有消费方且 env 前缀按服务区分；external 凭证只引用环境变量名；runtime 生命周期 `New/Run/Shutdown` 与超时来自 config。
- `directory_final`（默认）三段式：① 逐现存目标文档 D1~D9，产出 `per_document_results[]`；② 基于①核对跨层调用链（`transport→service→repository→domain` 调用与状态流闭合、错误转换两侧一致、状态写 owner 全局唯一、横切合同被引用方闭合）；③ 核对概要承接索引目标集合、归属表、UC/场景承接、时序图与详细正文的覆盖率。

**逐文档诊断 D1~D9**：

- **D1 骨架符合性**：L1 详细模板节齐全（含 N/A 声明）；头部 `doc_type` / `l2_status` 标注正确（pending 类型须 `l2_status: pending` + design-main `L2豁免` 声明）。
- **D2 八问完整性**：逐 `UNIT-<slug>` 按 L1 合同八问 + 命中 L2 类型特化逐问取证（承接行为 / 输入·输出·错误结果 / 读写状态 / 调用依赖正反面 / 失败收口 / 事件后置 / 测试映射 / 不得补造）；任一问缺 P1。
- **D3 追溯核查**：`UNIT ↔ BHV` 闭合（裸 token），无幽灵 BHV、无无承接单元；状态写 owner 回指概要归属表行且一致；声明的 `direct_dependencies[]` 出现在概要架构图边上，并形成 `依赖 → New* 构造入参 → 字段赋值 → usage` 闭环。
- **D4 分层一致性**：依赖正反面声明对照分层单向律 + 命中 L2 硬规则逐条（规则 7/9）。
- **D5 接口签名级**：service/handler 接口全集逐方法 Go 签名（首参 `ctx context.Context`、末返回 `error`）；domain 结构体与 JSON tag；可穷举概念用具名枚举/`iota`，禁裸魔法值；非签名级（「提供 XX 能力」无签名）P1。
- **D6 粒度判定**：抽查行为全流程（规则 11）+ 事务边界三分法结论。
- **D7 测试映射**：规则 12。
- **D8 错误与合规**：sentinel/错误三态收口（规则 10）+ 合规扫描（规则 13）；异常表逐行对应一条失败路径 BHV 或八问 1 的行为分支，失配 P2。
- **D9 删除审计 + 补造红线 + 层级越界**：规则 14；对破坏性删除/压缩/替换检查 deletion ledger，区分 obsolete fact 删除、合同迁移、N/A 声明、blocking contract loss。L1 章节骨架消失、仍有效 UNIT/BHV/行为合同被 endpoint/interface 覆盖替代、测试映射或不得补造清单丢失 → P1。

**Step 3** Findings 组织（同根因合并为一条，列全部位置；判级冲突取高）与修订形态判定（L1 修订形态章）。

**Step 4** 输出（按 `references/review-output.md` 合同）。

## 输出（互斥分支）

- **前置失败**（EX-1~EX-6 任一失败）：仅输出 EX 缺口（编号 / 缺口 / 证据）与最小修复动作（EX-3/EX-4/EX-5/EX-6 类缺口必须写「回退概要/项目约定/需求」而非详细侧补造）+「前置未通过，不进入逐文档诊断」结论。三类承接源状态按 `references/review-output.md` 写 `skipped_by_ex_precheck_failure:<EX-id>`，不伪造 Gate 状态。
- **前置通过**：按 `references/review-output.md`——scope 声明（含范围外未审清单，防误读为通过）→ 逐文档概况表（D1~D9 + findings 列）→ Findings 分级（每条五字段 + 受影响 Gate 项）→ 跨层调用链状态（`directory_final` / `layer_checkpoint` 必含）→ 概要承接索引与时序覆盖率状态（`directory_final` 必含）→ 详细 Gate 状态表 → **三选一结论**（可进入实现编码 / 带明确假设可进入 / 不可进入）→ 修订形态建议 → Gate 收口指引。
- 必须回填 `review_scope`、`per_document_results[]`、`partial_chapter_scope` / `covered_items[]` / `not_covered_items[]` / `canonical_publish_status`（无 partial scope 时按非适用分支）；不适用字段用 `not_applicable_by_review_scope`。

## 边界约束

- 详细设计文档无存量豁免；审核不代写合同正文。
- 审核项必须能回到 L1/L2 的正向写法，不做「有没有写某个词」的形式检查。
- 当前小批次审核不得装载未命中的 L2 类型、无关需求证据或无关示例；跨章取证只读概要索引、已完成章节锚点摘要与当前范围必要引用。

## 与官方 Trellis skill 的边界

- **设计写（`go-design-detail-writing`，姊妹 skill）**：承接概要 `design-main.md` 承接索引，按 domain→repository-data→biz→entry-api→横切 顺序逐章生成 `chapters/<slug>.md` 的合同八问正文——它产出 design 章。
- **设计审（本 skill）**：是 Phase 1 的详细 Gate 人工判定——判定详细设计能否进入下一阶段（实现编码）。详细设计不达标不得 `task.py start`。
- **区别于官方 `trellis-brainstorm`**：brainstorm 在更早阶段做需求/方案发散，不产出受 L1/L2 约束的 design 章，也不做 Gate 判定。
- **区别于官方 `trellis-check`**：`trellis-check` 是实现后的代码质检（对照已落地代码查质量/回归）；本 skill 是实现前的设计文档 Gate（对照 L1/L2 查设计合同是否可编码），二者阶段、对象、判定口径均不同，不互相替代。

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
- 五阶段方法入口（编号纪律 / doc_type 七类 / Gate 口径）：`.trellis/spec/harness/index.md`
- 类型差异（L2，仅前三类提供）：
  - `.trellis/spec/harness/detail/detail-type-entry-api.md`
  - `.trellis/spec/harness/detail/detail-type-biz.md`
  - `.trellis/spec/harness/detail/detail-type-repository-data.md`
- 通用方法与红线：`.trellis/spec/guides/golden-path.md`
- 项目约定槽位与 C1~C5：`.trellis/spec/conventions/project-conventions.md`
- 逐 doc_type 取证矩阵与判级：`references/review-baseline.md`
- 输出字段合同：`references/review-output.md`
