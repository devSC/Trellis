---
name: h5-design-detail-writing
description: 用于把 Guru H5/Next.js 概要设计展开为可编码合同（详细设计 L3 执行编排）。基线为 Next.js App Router 生产形态 + React + TypeScript(strict)。full 链按 directory_precheck + chapter_loop 执行：P1~P6 前置检查通过后，按 H5 写作顺序 domain-type→data-access→server-action→server-component→client-component→ui-component→route 逐章/小批次（每批 1~3 章）生成 chapters/<slug>.md，每批立即自动 review 并修复闭环，层级完成后跑 checkpoint；light 链同口径展开 design.md §2。只对当前批次命中的 doc_type 装载对应 L2（v1 提供 server-component/client-component/data-access 三元组；route/ui-component/domain-type/server-action 为 pending，按 L1 §3 合同八问展开并标 l2_status: pending，full 链须有 L2豁免）。每个设计单元按合同八问 + 章节正文骨架撰写（UNIT 编号、签名级接口、逐行为输入输出表、mermaid 时序、异常表、测试映射）。doc_type 与分层一律以 H5_BRIEF 钉死的七类为权威，禁止照抄 flutter/Go 的类型名；规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT 与 `.trellis/spec/guides/golden-path.md`。
---

# H5/Next.js 详细设计撰写

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载规则正文与完成条件，L2（`detail-type-server-component.md` / `detail-type-client-component.md` / `detail-type-data-access.md`）承载类型差异；本 SKILL.md 只做装载顺序、前置检查、chapter_loop 编排与输出要求；`references/` 只承载逐类写法细则、模板与示例。冲突时 **L1 > L2 > references > 本文件**。
> 平台生产基线：Next.js **App Router** + React + TypeScript(strict)。golden-path 锁定 App Router 生产形态：server-first / 默认 `server-component` + RSC 数据获取经 `data-access` 封装 / `server-action` 变更 / route 段约定（page·layout·loading·error·not-found·route）+ `metadata`·`generateMetadata` SEO / `next/image` / CSS Modules 或 Tailwind 样式隔离 / `strict: true`。详细设计一律按此生产基线书写（见 L1 §10、本文「App Router 生产基线」节）。
> 对标：本 skill 对标 backend `backend-design-detail-writing` 与 flutter `client-design-detail-writing` 的 `directory_precheck + chapter_loop` 编排同口径，仅把分层投影到 H5 七类。

## 目标

- 把概要的 owner 与承接索引展开为可直接编码的合同：每个设计单元（UNIT）回答**合同八问**（L1 §3），正文符合**章节骨架合同**（L1 §4），粒度满足 L1 §3.1（可直接实现 / 明确调用关系 / 完整调用链 / 粒度一致）。
- full 链按 `directory_precheck + chapter_loop` 逐章/小批次推进并自动审修闭环——**禁止一次性全量输出全部章节**（必然退化为大纲级薄文档，被 L1 §8 G7 拦截）。
- 只承接概要已决定的 owner、技术决策（`technology_decision_handoff[]`）与 scope；缺口一律回退概要（L1 §9），**禁止在详细阶段补造**。
- doc_type 与分层**一律以 H5_BRIEF / L1 §1 钉死的七类为权威**：`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`。**禁止照抄 flutter（page-entry/controller/usecase/repository-datasource/...）或 Go（Entry/Biz/Utility/Data/...）的类型名**；发现概要承接索引误用 backend/flutter 类型名 → 归属漂移，回退概要修订（L1 §0 映射纪律），不在详细阶段就地翻译。
- 本 SKILL 只做执行编排和输出组织，不重定义规范正文；规则疑义回 L1，引用时给章节号与结构化字段（`rule_id` / `rule_ref`）。

## 最小输入与自动补全

- 输入参数（均可省略，省略时按默认推进）：
  - `overview_dir`（full 链根目录路径，至少含 `design-main.md`；light 链为任务内 `design.md`）。
  - `chapter_target`：本轮只写一个承接索引目标；必须属于 `chapter_target → detail_doc_type` 目标集合（七类之内）。
  - `chapter_batch`：本轮写多个明确列出的目标（≤3 章），全部属于目标集合，批次须足够小以只装载命中的 L2/上下文。
  - `partial_scope` / `chapter_subscope`：仅在已指定 `chapter_target` 或 `chapter_batch` 后，用于收窄当前 canonical 目标内部本轮覆盖项（如多区块 `server-component` 的区块子集、多来源 `data-access` 的来源子集），**不得扩展成新目标范围**；未覆盖项回填 `not_covered_items[]`，并记 `canonical_publish_status=not_applicable_by_partial_scope`。
  - 默认（全部省略）：按 §推荐写作顺序自动逐批推进，选下一个未通过或受影响后失效的目标作为当前小批次；**不得一次性输出全部目标正文**。
- 需求证据只从概要已显式引用的锚点读取最小片段；**不直接拿需求自然语言改变** `chapter_target` / `doc_type` / `owner` / 技术决策 / scope。需求证据只用于理解字段语义、异常语义、边界条件、私有数据/权限含义，并反向校验概要是否已收口。

## 装载顺序（硬前置，任一失败即终止）

1. 读 L1 SSOT：`.trellis/spec/harness/detail/detail-structure-single-source.md`；不可用 → 终止并提示先安装 guru H5 spec 模板。
2. 读通用 golden-path：`.trellis/spec/guides/golden-path.md`，与目标仓库 `.trellis/spec/conventions/project-conventions.md`（校验 §6 槽位 C1~C5）。
3. 定位概要主定义（full=`design_package/design-main.md` 第 7 节承接索引；light=`design.md` §1），建立 `chapter_target → detail_doc_type（→ 目标文件名）` 目标集合（七类之内、非空）。
4. **只对当前批次命中的 doc_type** 读对应 L2：
   - `server-component` → `.trellis/spec/harness/detail/detail-type-server-component.md`（**v1 / l2_status: full**，render 轨）
   - `client-component` → `.trellis/spec/harness/detail/detail-type-client-component.md`（**v1 / full**，interactive 轨）
   - `data-access` → `.trellis/spec/harness/detail/detail-type-data-access.md`（**v1 / full**，data 轨）
   - `route` / `ui-component` / `domain-type` / `server-action` → **pending**，无独立 L2，按 L1 §3 合同八问展开并在章节文件头标 `l2_status: pending`（full 链须满足 L1 §2.5 L2 豁免合同，见 WX-6）。
   - **不得为后续章节预加载未命中的 L2 类型 SSOT、无关需求证据或无关示例。**
5. 需要逐类写法细则、章节模板或时序图示例时读 `references/chapter-guide.md` / `references/examples/`（只提供编排提示，不替代 L1/L2）。

## WX 前置检查（directory_precheck，full 链；任一失败 → 停止并输出缺口与概要修订动作，不产出正文）

对齐 L1 §5.1 的 P1~P6，编号同步落为 WX-1~WX-6：

- **WX-1 输入键 / 文件可读**：L1 可读；本批命中类型的 L2 可读（v1 仅三元组有 L2；pending 类按 L1 §3 展开）。缺 L1/L2 → 执行级错误。
- **WX-2 通用 golden-path 可读**：`.trellis/spec/guides/golden-path.md` 可读。
- **WX-3 project-conventions 可读且校验通过**：§6 槽位 C1~C5（路由模式=App / 内容源 / 状态管理 / UI 库 / 样式方案）显式填写；缺一即前置失败。
- **WX-4 承接索引存在且非空**：概要主定义可定位；第 7 节承接索引存在、每条有 `doc_type` 与目标文件名，可建立完整非空的 `chapter_target → detail_doc_type` 目标集合（七类之内）。**索引缺失/为空 → 硬阻断，回退概要，禁止详细补造归属。** full 链另查 `<design_package>/chapters/` 已存在（缺目录属概要骨架缺口，**不自动创建**）；目标文件名均落在 `chapters/` 内（词法检查）。
- **WX-5 概要 review evidence 已达标**：`guru_gate.py status` 显示 overview 当前 digest 已有两个不同 `run_id` 的 clean review；未达标 → 停止，提示先运行概要 review 并用 `record-review overview` 留痕。
- **WX-6 承接源状态**：本批引用的 `technology_decision_handoff[]` 条目均为"选定"（未选定 → 回退概要，**禁止详细拍板**）；本批命中 pending L2 的 doc_type（`route`/`ui-component`/`domain-type`/`server-action`）均有 L1 §2.5 的 `L2豁免：<doc_type> 理由：… 风险：… 补齐计划：…` 声明（无豁免 → 停止，提示先补 L2 或写豁免）。

light 链执行 WX-3/WX-4/WX-5/WX-6 的等价检查（索引在 `design.md` §1；产物写 §2）。

## 执行流程（chapter_loop）

1. **建立写作顺序（自底向上，与 L1 §2.3 / §5.2 一致）**：按层级排序目标集合——
   ① **合同层** `domain-type`（TS 类型/zod schema/领域模型先固化）
   → ② **数据层** `data-access`（按合同层展开取数/缓存/错误转换）
   → ③ **变更层** `server-action`（按数据层合同展开写操作/revalidate/API endpoint）
   → ④ **渲染层** `server-component`（编排 data-access 取数产出 RSC 树）
   → ⑤ **交互层** `client-component`（只做交互/状态到稳定服务端合同的适配）
   → ⑥ **展示层** `ui-component`（纯展示叶子收口）
   → ⑦ **路由层** `route`（段约定 page/layout/loading/error.tsx、metadata/SEO、错误边界收口）。
   同一 feature 的 `server-component` 及其直接 `data-access`、相关 `domain-type` 视为**同一小批次优先完成**。
2. **确定当前批次**：按输入参数或自动取下一批（1~3 章）；小批次必须属于承接索引目标集合，**只加载当前小批次命中的 L2、概要锚点、已完成章节锚点摘要、概要已指向的最小需求反向校验证据和必要示例**。
3. **逐章生成正文**：按 L1 §4 章节骨架合同撰写目标文件（full=`chapters/<slug>.md`；light=`design.md` §2 内一章）；每个 `### UNIT-<slug>` 按八问作答（命中 v1 类型时叠加 L2 类型差异规则）；暂无法回答的问题写入"未决问题"而非留空或编造。逐章要点：
   - 接口只写到**签名级**（TS 方法签名、数据结构 / zod schema 定义为上限），不写实现/伪代码。
   - 每个行为按 L1 §4 §4 节展开：函数签名 + 承接 `BHV-NNN` + 输入参数表 + 输出表 + mermaid sequenceDiagram（参与者用真实组件名）+ 流程详述（与图编号一一对应，满足 §3.1 粒度）+ 异常处理表。
   - RSC（`server-component`）须写"数据获取入参（`params`/`searchParams`）→ 取数 → 渲染产物"链；状态节写 `N/A：server_no_client_state` 并声明数据获取/缓存边界。
   - `client-component` 须写状态字段（含初始态）+ 状态转移 + 写 owner + 三态（loading/success/error）+ `'use client'` 边界声明（为何在此分割、哪些子树留服务端）。
   - `data-access` 按来源（MDX / CMS·API / ORM-DB）分别列取数合同、缓存/重验证策略、错误转换点（`[SLOT-04]`）；私有数据/secret 边界落点声明。
   - `server-action` 写 `'use server'` 签名 + 校验回指 `domain-type` schema + 写 owner + `revalidatePath/Tag`/`redirect` 后置结果及消费方。
   - `route` 写段约定（page/layout/loading/error.tsx 职责切分与触发）+ `metadata`/`generateMetadata`（title/description/og）+ `generateStaticParams`/动态段 + 缓存重验证策略 + 错误边界落地。
   - `ui-component` 纯展示：props 进、JSX 出；不得写 fetch/业务分支/私有状态机；样式按槽位（Tailwind/CSS Modules）隔离。
   - `domain-type` 写字段语义、取值约束、zod 运行期校验 schema；叶子合同不反向依赖运行层。
   - 辅助性文本（描述、表格、图内标签）一律**中文**；代码语法元素（类名/方法名/参数名/字面量/框架 API）保持**英文**。
4. **批内自动 review（不等用户）**：对照 L1 §5.3 清单——章节模板符合性（§4）、八问完成条件（§3）、粒度四条（§3.1）、编号断链（§3.2）、依赖与概要归属一致（§2.1 依赖律）、硬规则（§2.2）、L2 差异规则（命中 v1 类型时）。
5. **修复闭环**：有 finding → 按 L1 §9 判定修订形态（局部修订 / 文档级重构）→ 直接修复 → 复查受影响的行为/依赖/跨章引用；规则全部有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。**不用固定次数的 clean review 作为通过条件。**
6. **层级 checkpoint**：每完成一个层级跑 L1 §5.4 对应核对（合同层后 / 数据层后 / 变更层后 / 渲染层后 / 交互层后 / 展示层后 / 路由层后）；失效项回到对应批次重走审修闭环。
7. **受影响章节复查**：本批修改触及已完成章节的引用时，复查该引用闭合；层级 checkpoint 或最终复审修改了已通过章节 → 其通过状态失效，重新进入当前小批次写审修闭环。
8. **输出本批成果**（见输出要求）。
9. **下一目标推荐**：给出下一批建议与剩余目标清单；全目录完成时转入完成判定（L1 §5.5 / §8 G1~G8）并提示送审。

## 强制约束

**破坏性编辑保护**：任何删除、压缩、替换既有详细章节的改动，必须先列 deletion ledger（deleted_category / reason / replacement_location / removes_contract_obligation / reviewer_decision）。接口、路由或内容源事实可删除，仍有效的 L1 章节骨架、UNIT/BHV 承接、行为列表、输入输出错误合同、状态/边界 owner、失败收口、后置结果、测试映射、不得补造清单必须保留、移到命名替代位置，或以 `N/A：<理由>` 显式声明；不得把行为合同压扁成 endpoint/interface 映射表。

1. L3 不重定义 L1/L2/references；规则疑义回 L1，引用时给章节号并使用结构化字段 `rule_id=<规则ID>`、`rule_ref=<规范文件路径#章节锚点>`。
2. **禁止一轮全量生成**全部章节；每批 ≤3 章并完成批内审修后才进下一批（违反 → L1 §8 G7 拦截、§9.2 文档级重构）。
3. 不新增概要归属表之外的结构；不变更 owner / 技术决策 / scope；缺口回退概要（L1 §9）。`technology_decision_handoff[]` 中"未选定"的决策不得在详细阶段私自拍板。
4. 不写超过签名级的代码（TS 方法签名、数据结构 / zod schema 定义为上限）。
5. 命名 / 目录 / 序列化 / 样式取值按 `project-conventions` 槽位（L1 §6）；行为命名按概要锚点；doc_type 全程只用 L1 §1 七类 token，**不得用 backend/flutter 名替代**（doc_type 漂移红线）。
6. **分层依赖律（L1 §2.1，违反 fail）**：服务端链 `route → server-component → data-access → domain-type`；交互链 `client-component → ui-component`；变更链 `server-action → data-access`。`domain-type` 是叶子合同不反向依赖任何运行层；`ui-component` 是纯展示叶子不反向依赖上层；出现 `data-access → server-component`、`ui-component → client-component`、`domain-type → 任意运行层` 等反向边 → 归属漂移 → fail，回退概要修订。
7. **server-first + 私有数据/secret 边界（L1 §2.2 硬规则，P1）**：默认 `server-component`，`'use client'` 最小化仅在确需交互处声明；私有数据获取、API key、token、私钥、session **只能**出现在 `server-component`/`data-access`/`server-action`，`client-component`/`ui-component` 禁直取，只能接收脱敏后的 props 或调用暴露的 action 引用。`client-component` 不得直接 import `data-access`/`server-action` 的私有取数实现。
8. **错误边界**：渲染失败路径必须落到 `route` 的 `error.tsx` 或 `data-access` 的错误转换点，不得静默吞错；异常表逐行可对应一条失败路径 BHV 或八问 1 的行为分支。
9. **样式隔离**：CSS Modules / Tailwind，禁全局污染（禁裸全局 class 选择器、禁 `style jsx` 全局样式、禁跨组件样式泄漏）。
10. **TS strict**：详细设计接口/类型签名按 `tsconfig.json` `"strict": true` 假设书写，不依赖隐式 any。
11. `partial_scope` 只收窄不扩展；不改变 `chapter_target` / `detail_doc_type` / owner / 完整章节责任；未覆盖项必须显式回填 `not_covered_items[]`，保留 `covered_items[]` 与 `canonical_publish_status=not_applicable_by_partial_scope`，不得静默丢弃，也不得声明 canonical 目标完整通过。
12. 状态写 owner 必须与概要归属一致（回指归属表行）；发现归属错误 → 回退概要修订，不就地改。
13. 每行为测试映射覆盖成功 + 全部失败路径（八问之 7，映射到 unit/component-RTL/e2e-Playwright/manual）；写不出测试点的行为视为粒度不达标，回到执行流程第 3 步。
14. **编号断链拦截（L1 §3.2，P1）**：`BHV-NNN`（必须存在于 prd）与 `UNIT-<slug>`（语义 kebab-case）双向闭合——无幽灵 BHV、无悬空行为、无幽灵 UNIT、无重号、无方向违例编号；下游引用一律写裸 token；断链回到对应单元修订或回退概要补归属，**不得就地新造编号绕过**。
15. 涉权限/数据采集/三方域名/PII/secret/session 的单元必须落合规与边界依据（L1 §2.2、§7 边界 trace）；不写制裁 TLD、私有 API key 明文、动态执行类设计。
16. 辅助文本中文；代码语法元素英文。
17. 中断升级仅限四种情形：**概要源缺失 / 业务语义必须人工确认 / 技术决策未选定 / 修复无法收敛**；其余情况自动闭环推进，不等用户人工 review。
18. 写作结果不得输出审核矩阵或二元放行结论；全目录完成后提示送审：加载 `h5-design-detail-review`，Gate 结论"可进入编码"后先用 `record-review detail` 留下当前 digest 的两次 clean review evidence，再按 gate_mode 完成 `confirm detail` 人工收口。

## App Router 生产基线（写作纪律）

详细设计一律按 App Router 生产形态书写，下列维度为生产锁定项（完整规则见 L1 §10）：

- **路由段**：App Router `app/` + `route` 类段约定（`page/layout/loading/error/not-found.tsx` + route handler `route.ts`）。
- **RSC 边界**：server-first、默认 `server-component` 在服务端渲染并编排数据获取；`'use client'` 仅在需交互处声明并最小化。
- **数据获取**：`data-access` 封装内容源读取（MDX / CMS·API / ORM-DB）+ Next fetch cache / `revalidateTag` + 错误转换点；私有数据/secret 只落服务端，禁内联裸 `fetch`/`fs`。
- **严格类型**：`strict: true` + zod 运行期校验。
- **SEO**：`metadata`/`generateMetadata` + `generateStaticParams`（禁手写 `<Head>`）。
- **样式隔离**：CSS Modules / Tailwind 禁全局污染（禁裸全局 class、禁 `style jsx` 全局样式）。
- **变更**：`server-action`（`'use server'`）/ route handlers + `revalidatePath`。
- **测试**：Vitest+RTL / Playwright。
- **混用即缺陷**：把 `getStaticProps`/`getStaticPaths` 当 RSC 写、在 `server-component` 内调 `useState`、写全局 CSS / `strict: false` ——均按 P1 处理。

## Full/high 实现切片计划（与章节批次解耦）

full/high 全目录完成时，写作者必须在 `implement.md` 建立切片 planning
audit；章节写作批次不是实现切片边界。H5 七类 doc_type、App Router
server-first 边界和 domain→data→change→render→interactive→ui→route
归属/依赖律继续生效，但不得机械要求每个 `UNIT`、`doc_type` 或层各占一个
切片。

1. 每个普通切片记录 `owner_unit`、`covered_units`、`read_paths`、
   `owned_paths`、`focused_checks`、`parallel_wave`、`resource_locks`、
   `resource_isolation`、`check_wave`、`independent_commit_value`、
   `rollback_contract`、`review_context_inputs`、`review_context_bytes` 和
   `rejected_merge_candidates`。packet 的 `owner_unit` 保持一个真实标量；
   `covered_units` 可包含多个 Design UNIT。
2. `owned_paths` 按文件级声明，同一 `parallel_wave` 的一个 mutable path
   只能有一个 ordinary slice **mutable owner**；不得以 symbol、函数、类或
   diff hunk 绕过。重叠路径须重新分配唯一 owner 或合并切片。
3. 普通切片默认 `depends_on=[]`。先在已确认 Detail 中冻结跨切片接口、
   schema、digest、错误语义和共享数据结构；只有必须读取另一切片实际输出
   bytes 时才允许非空依赖。UNIT、章节、doc_type、层级或 review 顺序都不是
   实现依赖。
4. 每个被修改的测试文件只能有一个 owner。普通切片只跑 focused checks；
   相同工具状态须以独立 worktree/cache/output 隔离，或记录同一
   `resource_locks` 并分配串行 `check_wave`；不能隔离时合并。full regression
   只交给 Integration。
5. 普通切片默认最多四个。每片必须有可独立提交的用户/合同价值和可独立执行
   的 rollback；缺任一项就拒绝该切片候选并合并。对考虑过但决定不合并的
   组合，在 `rejected_merge_candidates` 逐项写切片集合与保持分离的理由；
   超过四片时还须逐片说明独立价值和 rollback 例外理由。
6. `review_context_inputs` 必须列出 reviewer 实际选中的精确、有序 inventory
   （packet、planning audit、target diff/owned paths、相关 frozen contracts
   与 focused evidence），每项写选择范围和该 snapshot 的 UTF-8 bytes。
   `review_context_bytes` 是各项的精确整数和，必须 `<= 262144`；禁止 wildcard、
   “相关文件”或只写未实测不等式。超限先缩减到上述最小输入，再阻断确认。
7. 普通分组稳定后创建恰好一个 Integration Slice：它依赖全部普通切片，
   packet coverage 覆盖普通 target union；`integration_owned_paths` 单独限定
   实际可写路径。Integration 只补集成字节、跨切片 invariant、full regression
   和最终 spec/sync 检查，不重写普通 owner 的核心字节。
8. Full/high planning 时，从当前 route/platform contract 解析适用的
   `h5-implementation-guru-writing` 与 implementation standard，并将其作为
   只读 guidance 校验：其声明契约须消费已确认的 packet/planning audit，且
   ordinary checks 须保持 packet-focused。不得把这些 framework 文件分配给
   application slice，不得依赖固定 `slice_id`、新增 planning-audit 字段或修改
   已确认的 `implement.md`；实际 framework 维护归属与 receipt bookkeeping 由
   相应 framework maintenance task、Integration validation 或 coordinator 处理。

## 输出要求（writing 专属）

每批输出（对齐 backend/flutter 同名 skill 的输出结构）：

- `execution_mode=directory_precheck+chapter_loop`（light 链标注 `light+chapter_loop`）
- `目标集合解析`：`index_resolution` / `target_count` / 已完成 / 本批 `chapter_target` 清单与 `doc_type` / `chapter_sequence` / `current_chapter_scope`
- `WX 前置状态`：首批输出 WX-1~WX-6 逐项（含 `project-conventions` 槽位 C1~C5 解析、`technology_decision_handoff[]` 选定状态、pending L2 豁免状态）；后续批只报变化
- `partial_scope`（如有）：`covered_items[]` / `not_covered_items[]` / `canonical_publish_status`
- `requirement_reverse_validation_evidence`：概要已指向的最小需求反向校验证据（只读，不改 scope/owner/doc_type）
- `requirement_to_overview_gap_findings`：若需求暴露概要未收口的行为/字段/技术决策 → 记 `overview_revision_action` 并中断对应正文补造
- 本批正文（或落盘文件清单 + 行数）
- `批内自动 review 结果`：finding 数 / 修复迭代次数 / `chapter_status` / `method_evidence_status`
- `层级 checkpoint 状态`（到达层级边界时输出，含失效项与回退动作）
- `未决问题与升级项`（如有，按强制约束 17 四类分类）
- `下一目标推荐`：下一批建议与剩余目标清单

全目录完成时追加：`完成判定`（L1 §5.5 / §8 G1~G8）+ `实现 trace 计划合同与 mutable evidence`指引（L1 §7：承接 trace / 依赖 trace / 边界 trace / 测试 trace）+ 上述切片 planning audit + 送审与人工确认指引（强制约束 18）。

前置失败输出：`writing_stage=draft_requires_overview_fix` + `draft_blockers`（缺口清单）+ `recommended_next_step`（概要修订动作），**不产出正文**。

## 参考资料

- 详细阶段 L1 SSOT：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- v1 类型差异 L2（render/interactive/data 三元组）：
  - `.trellis/spec/harness/detail/detail-type-server-component.md`（render）
  - `.trellis/spec/harness/detail/detail-type-client-component.md`（interactive）
  - `.trellis/spec/harness/detail/detail-type-data-access.md`（data）
- pending 类（按 L1 §3 八问展开 + §2.5 L2 豁免）：`route` / `ui-component` / `domain-type` / `server-action`，暂无独立 L2
- 通用方法 SSOT：`.trellis/spec/guides/golden-path.md`；项目取值：`.trellis/spec/conventions/project-conventions.md`
- 逐类写法细则与章节模板、章节成稿样例：`references/chapter-guide.md` / `references/examples/`
- 对标参照：backend `backend-design-detail-writing` SKILL、flutter `client-design-detail-writing` SKILL（同口径 `directory_precheck + chapter_loop`，分层投影到 H5 七类）
