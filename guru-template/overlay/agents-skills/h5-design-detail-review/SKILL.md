---
name: h5-design-detail-review
description: 用于审核 Guru H5（Next.js App Router 生产形态）详细设计文档，判定能否进入编码。先做 EX 前置检查（判轨/索引/概要 review evidence/承接源/机检），再按 review_scope 三模式执行：current_chapter 单章诊断、layer_checkpoint 跨章协同诊断（checkpoint_layer=server-chain|interactive-chain|mutation|route）、directory_final 目录级三段式终审（逐文档 D1~D8 诊断 → 跨链路链接 → 索引与 SEO/scenario 覆盖率）。核查章节骨架符合性、合同八问、概要 owner 追溯、分层依赖律、编号断链拦截、server/client 边界与 secret 红线、测试映射与粒度；先证据后结论，输出分级 findings 与互斥三选一结论，输出 record-review 证据，并在双 clean 后等待 detail confirm。doc_type 严格用 H5_BRIEF 钉死的七类。规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT 与 `.trellis/spec/guides/golden-path.md`。
---

# H5（Next.js）详细设计审核

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载规则正文与 G1~G8 完成条件，L2 承载类型差异，golden-path（`.trellis/spec/guides/golden-path.md`）承载 Next.js 硬规则；本 SKILL.md 只做前置检查、scope 编排与诊断流程，`references/review-baseline.md` 承载逐 doc_type 取证矩阵与严重度判级，`references/review-output.md` 承载输出字段合同。冲突时 L1 > L2 > golden-path > references > 本文件。
> 平台生产基线：Next.js App Router + React + TypeScript(strict)。审核一律以 App Router 生产口径为准：server-first / RSC 数据获取经 data-access 封装 / server-action 变更 / route 段约定（page·layout·loading·error·not-found·route）/ `metadata`·`generateMetadata` 标准化 SEO / `next/image` / CSS Modules 或 Tailwind 样式隔离 / `strict: true`。`getStaticProps` / `_app.tsx` / 手写 `<Head>` 等 Pages Router 形态不能当作 App Router 通过证据，出现即按 golden-path 条目判 finding。

## 目标

- 审核详细设计是否达到进入编码的质量口径（L1 §8 G1~G8）。
- 逐文档诊断 + 跨链链路核对双层取证：单章合格不等于目录合格。
- 拦截编号断链：UNIT-<slug> 引用幽灵 BHV-NNN、下游裸 token 指向不存在的设计单元 → 直接阻断，不接受"含义自明"。
- 守住 server-first 边界：私有数据获取 / secret 越界进入 client-component、`'use client'` 过度蔓延、全局样式污染、route 段越权 → 文档级判定。
- 识别"薄文档"：多章雷同骨架、无单元级实质内容（一轮全量生成迹象）→ 文档级重构，不接受局部补丁。

## doc_type 权威七类（全程唯一，禁止改名/增减/换数）

以 H5_BRIEF 为权威，不照抄 flutter/Go 的类型名（无 controller/usecase/repository/Biz/Entry）：

1. `server-component` — RSC 服务端组件（渲染 + 数据获取编排，默认类型）
2. `client-component` — `'use client'` 交互组件（状态/事件/hooks）
3. `data-access` — 数据访问层（fetch 封装 / 内容源 MDX·CMS / ORM 查询）
4. `route` — App Router route 段（page/layout/loading/error.tsx + metadata/SEO）
5. `ui-component` — 展示型可复用组件（纯展示、无数据获取、无业务）
6. `domain-type` — TS 类型 / zod schema / 领域模型
7. `server-action` — Server Actions / route handlers（变更 / API endpoint）

**L2 落地状态**：v1 提供三类 L2 文件（render/interactive/data 三元组，对应 flutter 的 controller/usecase/repository-datasource）：
- `detail-type-server-component.md`（render）
- `detail-type-client-component.md`（interactive）
- `detail-type-data-access.md`（data）

其余四类 `route` / `ui-component` / `domain-type` / `server-action` 为 **pending**（按 L1 合同八问展开，头部标 `l2_status: pending`；full 链命中必须有 `L2豁免` 声明）。

## owner 层与分层依赖律（归属硬基准，违反 fail）

- 服务端链：`route → server-component → data-access → domain-type`
- 交互链：`client-component → ui-component`
- 变更链：`server-action → data-access`

判级硬律（违反即 P1，不得给通过性结论）：
- `client-component` 直接调用 `data-access`、直取私有数据获取 / secret / DB → P1（必须经由 server-component / server-action 注入或经 props 下传已脱敏数据）。
- `server-component` / `ui-component` 反向依赖 `client-component`（把交互态上提到服务端渲染层）→ P1。
- `route` 段承载业务规则或数据访问实现细节（应只编排 + metadata/SEO）→ P1。
- `ui-component` 内出现数据获取 / 业务判定 / `'use client'` 之外的副作用 → P1（应纯展示）。
- `server-action` 绕过 `data-access` 直拼查询、或在 `client-component` 内内联定义 server 逻辑 → P1。
- `domain-type` 反向依赖任何运行层（type 层不得 import 组件/动作）→ P1。
- 环依赖（server-component ↔ server-component 互引成环、data-access 互引成环等）→ P1。

## golden-path 硬规则（锁定，逐条对照）

- TS strict：`tsconfig.json` 必须 `strict: true`，不依赖隐式 any。
- server-first，`'use client'` 最小化：仅在需要状态/事件/浏览器 API 处声明，且声明位置尽量下沉到叶子交互组件。
- 私有数据获取 / secret 只允许出现在 `server-component` / `data-access` / `server-action`；`client-component` / `ui-component` 禁直取。
- `route` 段约定：`page.tsx` / `layout.tsx` / `loading.tsx` / `error.tsx` 职责齐全（缺 `error.tsx` 错误边界、缺 `loading.tsx` 流式回退须有 N/A 声明）。
- `metadata` / SEO 标准化：route 类必须用 Metadata API（`metadata` 或 `generateMetadata`）承接 SEO，禁手写 `<Head>`。
- 样式隔离：CSS Modules / Tailwind，模块化/原子化，禁全局污染（禁裸全局 class 选择器、禁 `style jsx` 全局样式、禁跨组件样式泄漏）。
- 错误边界：`error.tsx`（段级）+ data-access 错误转换约定齐全。

## 最小输入与自动补全

- 输入参数：
  - `review_scope`：`current_chapter`（指定 chapter_target/batch 的文档级诊断）/ `layer_checkpoint`（按链跨章协同诊断，配 `checkpoint_layer`=`server-chain`|`interactive-chain`|`mutation`|`route`）/ `directory_final`（默认，目录级终审）。
  - `chapter_target` / `chapter_batch`：current_chapter 模式必填。
- 接受 task 目录或 design_package 路径；候选不唯一时先确认审核目标。

## 装载顺序与 EX 前置检查（任一失败 → 前置缺口输出，停止逐文档诊断）

1. 读 L1 主 SSOT（`.trellis/spec/harness/detail/detail-structure-single-source.md`）。
2. 读 `references/review-baseline.md`（取证矩阵）与 `references/review-output.md`（输出合同）。
3. 读 golden-path（`.trellis/spec/guides/golden-path.md`）与 project-conventions 槽位（见下「项目约定槽位」）。
4. **EX-1 输入键**：task.json `guru_chain`（full 链含 `design_package`）可判定。
5. **EX-2 路径与骨架**：design_package/chapters/ 存在（light 链 design.md §2 存在）。
6. **EX-3 承接索引**：design-main 第 7 节（light 链 design.md §1 索引节）存在、非空、可建立 `chapter_target → doc_type → 目标文件` 完整映射；doc_type 取值必须落在权威七类内（出现 controller/usecase/Biz 等非法类型名 → EX-3 失败，回退概要改名）。
7. **EX-4 概要 review evidence**：`python3 .trellis/scripts/guru/guru_gate.py status` 显示 overview 当前 digest 已有两个不同 run-id 的 clean review。
8. **EX-5 承接源**：被审章节引用的技术决策（内容源 / 状态管理 / UI 库 / 样式方案 / 数据库 / 认证 / 部署 / 路由模式）均"选定"；pending L2 命中（route/ui-component/domain-type/server-action）均有 `L2豁免` 声明。
9. **EX-6 机器 Gate**：`python3 .trellis/scripts/guru/guru_gate.py detail <task_dir>` 的结构结论可获取（机检失败项直接并入 findings，人工聚焦语义）。
10. 按被审文档命中的 doc_type 读对应 L2（仅 server-component/client-component/data-access 三类有 v1 L2，只装载命中类型，不全量装）；pending 四类走 L1 八问 + 豁免核查。

## 项目约定槽位（project-conventions，EX-5 选定校验对象）

内容源（MDX/CMS）、状态管理（none/Zustand/Context）、UI 组件库（shadcn/MUI）、样式方案（Tailwind/CSS Modules）、测试（Vitest+RTL/Playwright）、lint（ESLint+Prettier）、数据库、认证（NextAuth）、图像优化（next/image）、部署（Vercel）、路由模式（App vs Pages）。被审章节引用到的槽位若仍为"待定/示例占位"，按 EX-5 失败回退概要。

## 执行规则

1. L3 不重定义 L1/L2/golden-path；逐项检查回指 L1/L2 章节号或 golden-path 条目。
2. 先证据后结论；finding 带「文件 + 小节/表格行」锚点。
3. **directory_final 不得跳过逐文档阶段**：每个现存目标文档必须有独立的 D1~D8 诊断与 finding 摘要；缺失目标文档只输出缺失结论与修订方案，不进入 D 诊断。
4. current_chapter 不得扩大为全目录主审，但必须读取关联锚点核对上游（概要索引/归属）与下游（被引用方）边界。
5. 「范围内/范围外」仅由概要承接索引的目标集合判定；批次/单章无 findings 只代表本范围 `findings=none`，不代表目录通过。
6. EX 失败一律回退上游（概要/判轨/改 doc_type 名），不得在详细侧补造后继续审。
7. 分层依赖律违例（client 直取 data-access、route 承载业务、ui-component 取数、server-action 绕 data-access、type 反向依赖、环依赖，对照上「owner 层与分层依赖律」）→ P1，不得给通过性结论。
8. 八问缺项、追溯断链（UNIT 引用幽灵 BHV、行为无承接、下游裸 token 指向不存在的 UNIT）、章节闭合失败 → P1。
9. 粒度按 L1 §3.1 逐文档抽查 ≥1 个行为全流程；"见概要"式作答、无调用对象的步骤、server/client 边界处的数据流断点 → P1。
10. 测试映射核查覆盖成功 + 全部失败路径；高风险链路（支付/认证/数据删除/server-action 变更）漏测 → P1，普通失败路径漏测 → P2；测试层合理（RSC/数据层用 Vitest+RTL/集成，交互流用 Playwright E2E）。
11. 合规与红线：私有数据/secret/env 在 client-component 或 ui-component 出现、`.env` 当线上合同、硬编码 token/api_key、制裁 TLD、私有 API、动态执行（`eval`/`new Function`/`dangerouslySetInnerHTML` 注入未净化）、全局样式污染 → P1。
12. 补造红线（L1 §6）：概要外结构、改 owner、改 doc_type 名、拍板未选定决策（替概要选内容源/状态管理/UI 库等）、超签名级代码（>15 行实现体视为越界信号）→ P1。
13. 薄文档判定：≥2 章骨架雷同且无单元级实质内容 → 结论直接「不可进入」+ 文档级重构建议（L1 §9），不逐条列局部 finding。
14. 详细设计文档无存量豁免；修订形态建议只引用 L1 §9。
15. App Router 生产口径未落地（`getStaticProps` / `_app.tsx` / 手写 `<Head>` / 全局 css 等 Pages Router 形态出现，或 server-first / data-access 封装 / metadata 标准化等缺失）一律按 golden-path 条目判 finding，不接受沿用旧形态。

## 编号纪律（断链拦截）

- 行为编号 `BHV-NNN`（三位数字），设计单元编号 `UNIT-<slug>`（slug 小写连字符）。
- 下游引用一律裸 token（直接写 `BHV-012` / `UNIT-post-list-rsc`，不加书名号、不加"见上文"代词）。
- 断链取证：`rg -n "UNIT-|BHV-" <章节文件>` 固化全部编号；每个 UNIT 承接的 BHV 必须在 prd/概要存在；每个被下游裸 token 引用的 UNIT 必须在某章节定义。指向不存在编号 → P1（断链阻断），同根因合并一条但列全部断点。

## 诊断流程

**Step 1** EX-1~EX-6（全部 scope 模式都执行）。

**Step 2** 解析 review_scope：
- `current_chapter`：对指定章节执行 D1~D8 + 上下游边界核对。
- `layer_checkpoint`：按 checkpoint_layer 执行对应跨章取证：
  - `server-chain`：route → server-component → data-access → domain-type 的调用与数据流闭合，metadata/SEO 承接，server-first 边界。
  - `interactive-chain`：client-component → ui-component 的事件/状态流闭合，`'use client'` 最小化与状态订阅/释放成对。
  - `mutation`：server-action → data-access 的变更链、入参 zod 校验、错误返回与 revalidate 约定。
  - `route`：route 段（page/layout/loading/error）职责齐全、metadata/SEO、错误边界 owner 唯一。
- `directory_final`（默认）三段式：① 逐现存目标文档 D1~D8，产出 per_document_results[]；② 基于①核对跨链链路（server-chain / interactive-chain / mutation / route 四链调用与状态流闭合 + server/client 边界）；③ 核对概要索引目标、UC 承接表、时序图、SEO/scenario 与详细正文的覆盖率。

**逐文档诊断 D1~D8**：
- D1 骨架符合性：L1 §4 模板节齐全（含 N/A 声明）；`doc_type`（七类之一）/`l2_status`（v1 三类标 full，pending 四类标 pending）头部标注正确。
- D2 八问完整性：逐 UNIT 八问可回指可验证信号。
- D3 追溯核查：UNIT↔BHV 闭合（编号断链拦截）；状态/数据 owner 回指概要归属表；依赖出现在概要架构图。
- D4 分层一致性：依赖声明对照分层依赖律 + 命中 L2 硬规则 + golden-path server/client 边界。
- D5 粒度判定：抽查行为流程详述（L1 §3.1 四条：逐步有调用对象与参数、失败分支、状态/数据写入点、server↔client 边界数据流）。
- D6 测试映射：成功+失败路径覆盖；测试层合理（Vitest+RTL vs Playwright）。
- D7 合规核查：规则 11（secret/env/client 越界/动态执行/全局样式）。
- D8 补造红线：规则 12 + 错误表↔失败路径 BHV 对应 + error.tsx/data-access 错误转换一致。

**Step 3** Findings 组织与修订形态判定（L1 §9）。
**Step 4** 输出（按下「输出合同」）。

## 逐 doc_type 附加检查

### v1 类型（按 L2 逐条硬规则）

| doc_type | 附加取证 | 典型 P1 |
|----------|---------|---------|
| `server-component`（render，L2: detail-type-server-component） | RSC 默认无 `'use client'`；数据获取经 data-access 编排；私有数据/secret 仅服务端持有；下传 client 的 props 已脱敏；Suspense/loading 边界声明 | 标 `'use client'` 后仍直取 DB/secret；把私有数据原样下传 client；在 RSC 内写交互态 |
| `client-component`（interactive，L2: detail-type-client-component） | 顶部 `'use client'`；状态/事件/hooks 明确；只消费 props 或调用 server-action；`'use client'` 范围最小化（不裹住可服务端渲染的子树） | 直接 import/调用 data-access；client 内直取 env/secret；把整页提为 client |
| `data-access`（data，L2: detail-type-data-access） | fetch 封装 / 内容源(MDX·CMS) / ORM 查询；错误转换表逐枚举；缓存/`revalidate`/`cache` 策略归属；返回 domain-type；无业务判定 | 含业务规则判定；被 client-component 直接 import；secret 硬编码 |

### pending 类型（L1 八问 + 豁免核查）

- 头部 `l2_status: pending` 标注存在；design-main 有对应 `L2豁免：<doc_type> 理由：…`（full 链；无豁免 → P1）。
- `route`：route 段文件职责（page/layout/loading/error）齐全或 N/A 声明；`metadata`/`generateMetadata` 承接 SEO（手写 `<Head>` 不充数）；只编排不承载业务规则；错误边界 owner 唯一。出现业务规则/数据访问实现 → P1（回退到 server-component/data-access）。
- `ui-component`：纯展示，八问 8 必含"不拥有数据获取/业务判定"；样式隔离（CSS Modules/Tailwind，不写全局）；props 签名级。出现取数/业务判定/全局样式 → P1。
- `domain-type`：TS 类型 / zod schema / 领域模型；无运行层反向依赖；schema 由谁校验写明（server-action/data-access 入口）。type 层 import 组件/动作 → P1。
- `server-action`：`'use server'` 或 route handler 边界；入参 zod 校验；经 data-access 完成变更；`revalidatePath`/`revalidateTag` 与错误返回约定；认证/授权依据（命中 NextAuth 槽位）。绕过 data-access 直拼查询、在 client 内内联定义 → P1。

## 跨链链路核对（directory_final 第②段 / layer_checkpoint）

| 链边界 | 核对项 | 缺口判级 |
|--------|--------|---------|
| route→server-component | route 只编排，page 调用的 server-component 存在；metadata/SEO 承接闭合 | route 承载业务/取数 P1；metadata 缺失 P2 |
| server-component→data-access | server-component 声明的数据依赖有承接 data-access 章节；返回类型为 domain-type；错误转换两侧一致 | 依赖无承接 P1；类型不闭合 P2 |
| data-access→domain-type | 查询返回与 domain-type / zod schema 一致；schema 校验位置写明 | 类型漂移/无 schema P2 |
| client-component→ui-component | client 只调用 ui-component 展示/server-action 变更；状态订阅有发射方；`'use client'` 不上提 | client 直连 data-access P1；状态无 owner P1 |
| server-action→data-access | 变更经 data-access；revalidate 约定存在；认证依据存在 | 绕 data-access P1；缺 revalidate P2 |
| server/client 全局边界 | 私有数据/secret 不跨入 client；同一数据/状态 owner 全局唯一；同一错误枚举跨章一致 | secret 越界 P1；多 owner P1 |

## 覆盖率核对（directory_final 第③段）

1. 概要索引目标集合 vs 现存章节文件：缺失清单（缺失只出"缺失结论+修订方案"，不进 D 诊断）。
2. UC 承接表 index_refs vs 章节：每个 UC 的链路在详细侧可走通（route→server-component→data-access 或 client-component→server-action 全链可达）。
3. 概要时序图参与者/调用 vs 详细行为设计：抽查 ≥1 个 UC 的时序步骤在对应章节有同名行为（裸 token 对得上）。
4. SEO/metadata 覆盖：概要声明需 SEO 的 route 在详细侧有 metadata/generateMetadata 承接。

## 薄文档判定（优先于逐条 finding）

满足任一即判薄文档 → 结论「不可进入」+ 文档级重构（L1 §9），不再逐条列局部 finding：

- ≥2 章骨架雷同：小节结构相同且正文为占位级（参数表空 / 流程详述 <3 步 / 测试映射 ≤1 行 / 八问多问写"见概要"）。
- 全目录一次提交生成且无批内审修痕迹（chapter_status 缺失）叠加上一条任意命中。
- 逐行为设计普遍缺 mermaid 时序与异常表，或普遍缺 server/client 边界数据流标注。

## 严重度判级规则

- **P1（阻断）**：D1~D8 表中标注 P1 的项；分层依赖律违例；编号断链；server/client 边界 secret 越界；跨链 P1 项；薄文档；章节闭合失败（机检并入）。
- **P2（应修）**：表中 P2 项；粒度局部不达标（单个行为）；类型漂移；metadata/revalidate 缺失；孤儿合同。
- **P3（建议）**：表述/格式/术语一致性。
- 判级冲突取高；同根因合并为一条 finding 列全部位置。

## 结论判定（互斥三选一）

- 任一 P1 → **不可进入**（阻塞清单 + 修订形态：局部修订 / 文档级重构，按 L1 §9；概要缺陷标注"回退概要"）。
- 仅 P2 且每条有明确修订路径 → **带明确假设可进入**（逐条假设、依据、验证时点）。
- 无 P1/P2 → **可进入编码**。
- 结论后必须给 Gate 收口指引（见下「Gate 收口」）。

## 输出（互斥分支）

### 分支一：前置缺口输出（EX-1~EX-6 任一失败）

```markdown
## H5 详细审核：前置阻断

**EX 缺口**（逐条：EX 编号 / 缺口 / 证据）
**修复动作**（逐条最小动作；EX-3/EX-5 类缺口必须写"回退概要"而非详细侧补造；非法 doc_type 名写"回退概要改名为权威七类之一"）
**结论**：前置未通过，不进入逐文档诊断。
```

### 分支二：诊断输出（前置通过）

1. **scope 声明**：`review_scope`（current_chapter / layer_checkpoint(<链>) / directory_final）+ 本次范围内目标清单 + 范围外未审清单（明示"范围外未审"）。
2. **逐文档概况表**（current_chapter / directory_final 必含）：

   ```markdown
   | 章节 | doc_type | l2 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | findings |
   |------|----------|----|----|----|----|----|----|----|----|----|----|
   | post-list-rsc | server-component | v1 | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | P2×1 |
   | post-detail-route | route | pending | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | P1×1 |
   ```

   缺失目标文档单列：`缺失清单 + 修订方案`（不进 D 诊断）。
3. **Findings**（按严重度分组，每条五字段 + 受影响 G 项）：

   ```markdown
   **P1-1** ｜ location：chapters/post-detail-route.md §4.2 ｜ problem：route 段内实现内容过滤业务规则（route 越权）
   ｜ evidence：流程详述第 3 步"按 tag 过滤草稿文章" ｜ suggestion：过滤上收 server-component/data-access，route 只编排 + metadata
   ｜ 受影响 G 项：G4
   ```

   薄文档命中时：跳过逐条列举，输出薄文档证据（雷同章节对照 + 占位统计）+ 文档级重构方案。
4. **跨链链路状态**（directory_final / layer_checkpoint 必含）：四链边界（server-chain / interactive-chain / mutation / route）+ server/client 全局边界逐项 pass/fail + 失效位置。
5. **覆盖率状态**（directory_final 必含）：索引↔章节差集 / UC 链路抽查 / 时序↔行为抽查 / SEO 承接抽查。
6. **G1~G8 状态表**：

   ```markdown
   | G 项 | 状态 | 证据/阻塞 finding |
   ```

   light 链 G6~G7 标注 `N/A(light)` 并说明单文件口径已满足。
7. **三选一结论**（互斥，见「结论判定」）。
8. **Gate 收口指引**（结论为可进入/带假设可进入时必须输出，见「Gate 收口」）。

## 复审闭环

按 findings 修订后复审：只复查受影响章节的 D 诊断 + 其跨链引用，输出「复审范围 / 原 finding 关闭状态 / 新增 finding / 更新后 G 状态与结论」。current_chapter 复审通过不改变目录级结论——目录级结论只能由 directory_final 产生。

## 边界约束

- 详细设计文档无存量豁免；审核不代写合同正文。
- 审核项必须能回到 L1/L2/golden-path 的正向方法，不做"有没有写某个词"的形式检查。
- doc_type 全程只用权威七类；任何改名/增减/换数尝试一律 EX-3 或 D1 拦截。
- 一律以 App Router 生产口径为放行依据；沿用旧形态（Pages Router / 手写 `<Head>` / 全局 CSS）不构成豁免。

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
  --evidence "<本次 detail review 证据摘要>"
```

若存在 medium+ finding，必须输出 `--result findings --max-severity medium|high|critical --finding-class REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|IMPLEMENT_DEFECT|PROCESS_DEFECT`，并停止进入编码。

当前 digest 下两个不同 `run_id` 的 clean review 记录后，提示用户运行：

```bash
python3 .trellis/scripts/guru/guru_gate.py confirm detail <task_dir>
```

confirm detail 的 strict/soft 通道以 workflow Trellis System 节为准；未确认前不得 `task.py start`。

## 参考资料

- 详细阶段中立规范（L1）：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- 类型差异（L2，v1 三类）：
  - `.trellis/spec/harness/detail/detail-type-server-component.md`
  - `.trellis/spec/harness/detail/detail-type-client-component.md`
  - `.trellis/spec/harness/detail/detail-type-data-access.md`
- golden-path 硬规则：`.trellis/spec/guides/golden-path.md`
- 取证矩阵与严重度判级：`references/review-baseline.md`
- 输出字段合同：`references/review-output.md`
