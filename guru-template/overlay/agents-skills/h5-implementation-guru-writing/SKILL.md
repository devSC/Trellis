---
name: h5-implementation-guru-writing
description: 按已过 Gate 的 H5（Next.js App Router + React + TypeScript strict）详细设计执行编码与自测的执行编排 Skill（L3）。编码规则唯一来源是通用 golden-path（server-first/'use client' 最小化、分层依赖律、私有数据获取隔离、route 段约定、metadata/SEO 标准化、样式隔离、错误边界）与 project-conventions 槽位；过程按 implementation-trace 合同四节留证据。本 Skill 只做装载顺序、边界约束、WX 执行流程编排、Gate 自检与产物要求，不重定义标准规则；标准口径住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`，doc_type 取值住 `.trellis/spec/harness/index.md`。
---

# H5 实现执行（Next.js / React / TypeScript）

> 层级契约：规则正文与完成条件住 `.trellis/spec/guides/golden-path.md`（编码红线唯一来源）与 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（过程合同）；doc_type 七类取值与分层依赖律住 `.trellis/spec/harness/index.md` 与 detail L2（render/interactive/data 三元组）。本 SKILL.md 只承载装载顺序、边界约束、WX 编排、Gate 自检与输出要求。冲突时以阶段子 SSOT 为准，本文件为辅；规则疑义回 SSOT 并引章节号，不在本文件就地裁决。
> 平台形态：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。`app/` 承载 route 段（`page/layout/loading/error.tsx` + `metadata`），数据访问与 Server Actions 在服务端模块，`'use client'` 仅出现在需要交互的组件。**证据基线说明**：参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是 Pages Router + Nextra + MDX + gray-matter 的轻量 blog starter（`package.json` 用 `nextra`/`nextra-theme-blog`，`pages/` 为 Pages Router，`pages/posts/*.md(x)` 为内容源，`scripts/gen-rss.js` 用 `gray-matter` 解析 frontmatter，`tsconfig.json` 里 `strict: false`、`target: es5`），**故意简化**；本平台 golden-path 以 App Router 生产最佳实践为准，把该示例仅作为「内容模型基线」消费。凡示例与生产红线冲突（Pages vs App、`strict:false` vs `strict:true`），一律以生产红线为准并在 trace 中标注「示例实证 vs 生产级补充」。

## doc_type 权威七类（全程唯一，禁止改名/增减/换数）

承接详细设计时，每个 `UNIT-<slug>` 必带且仅带以下七类之一（取值住 `.trellis/spec/harness/index.md`，本表为消费侧落地映射，名称一字不改、不照抄 flutter/Go 的类型名）：

1. `server-component` — RSC 服务端组件（渲染 + 数据获取编排，默认形态）。
2. `client-component` — `'use client'` 交互组件（状态 / 事件 / hooks）。
3. `data-access` — 数据访问层（`fetch` 封装 / 内容源 MDX/CMS / ORM 查询）。
4. `route` — App Router route 段（`page/layout/loading/error.tsx` + `metadata`/SEO）。
5. `ui-component` — 展示型可复用组件（纯展示、无数据获取、无业务）。
6. `domain-type` — TS 类型 / zod schema / 领域模型。
7. `server-action` — Server Actions / route handlers（变更 / API endpoint）。

**L2 覆盖说明**：v1 提供 L2 文件（render/interactive/data 三元组，对应 flutter 的 controller/usecase/repository-datasource）——`detail-type-server-component.md`（render）/ `detail-type-client-component.md`（interactive）/ `detail-type-data-access.md`（data）。其余四类 `route`/`ui-component`/`domain-type`/`server-action` 当前为 `l2_status: pending`，按 L1 合同八问展开；承接到这四类且任务要求 full 链时，须确认上游已对该类做 L2 豁免（`l2_exemption`）记录，否则回退详细阶段。

## 分层依赖律（归属硬基准，违反 fail）

详细设计 owner 层与依赖方向钉死如下，实现不得越层、不得反向、不得新增层：

- 服务端链：`route → server-component → data-access → domain-type`。
- 交互链：`client-component → ui-component`。
- 变更链：`server-action → data-access`。

判定要点：`route` 段只编排不直查数据库；`server-component` 可调 `data-access` 但不得被 `client-component` 反向 import 渲染逻辑；`data-access` 只依赖 `domain-type`，不反向 import `server-component`/`route`；`client-component` 只组合 `ui-component`，不得直接调用私有 `data-access`/`fetch` 私有源；`server-action` 走 `data-access` 落变更，不在组件内联裸 mutation。

## 装载顺序（硬前置，任一失败即终止并输出前置缺口）

1. 必须先读 `.trellis/spec/guides/golden-path.md`（编码规则唯一来源）：确认 server-first / `'use client'` 最小化、分层依赖律、私有数据获取/secret 隔离、route 段约定（`page/layout/loading/error`）、`metadata`/SEO 标准化、样式隔离（CSS Modules/Tailwind，禁全局污染）、错误边界（`error.tsx`）红线已就绪；不可用 → 终止并提示先安装/刷新 guru spec 模板（`apply.sh`）。
2. 读 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（过程合同 §0~§7）与 `.trellis/spec/harness/index.md` 的实现 Gate 定义、doc_type 七类、编号纪律（行为 `BHV-NNN`、设计单元 `UNIT-<slug>`，下游引用裸 token，不带前缀解释）。
3. 读 `.trellis/spec/conventions/project-conventions.md` 并校验项目约定槽位均已选定且未留空：内容源（MDX/CMS）、状态管理（none/Zustand/Context）、UI 组件库（shadcn/MUI）、样式方案（Tailwind/CSS Modules）、测试（Vitest+RTL/Playwright）、lint（ESLint+Prettier）、数据库、认证（NextAuth）、图像优化（`next/image`）、部署（Vercel）、路由模式（App vs Pages）。任一未填 → 停止先定槽位，不在实现里私自拍板（尤其「路由模式」必须显式确认为 App Router 才走生产链，留空或为 Pages 须升级人工 Gate）。
4. 定位本任务承接的、已过详细 Gate 且人工确认已落盘的详细设计单元（full=L2 章节 `detail-type-*.md` 对应的设计章节；light=`design.md` §详细），建立 `UNIT-<slug>` 单元清单 + 合同八问 + 测试映射；缺失或单元为幽灵引用（无对应详细文档）→ 终止并提示回退设计阶段（探索性 spike 除外，须显式声明、隔离、不并入交付）。
5. 建立构建基线：`package.json`（确认 scripts：`dev`/`build`/`start` 等）与 `tsconfig.json`（确认 `strict: true`；若示例残留 `strict:false` 须以 golden-path 为准修正或升级人工 Gate）可读，记录改动前 `tsc --noEmit` 与 `next build`（或 `next lint`）的基线状态（用于区分「我引入的失败」与「既有失败」）；不可建立基线 → 记录环境阻塞，不得把未验证当通过。

## 边界约束

- 只实现详细设计合同内的内容；合同外结构（新 route 段、新 doc_type 单元、新 `domain-type`、新 `server-action` endpoint、新内容源、新全局样式入口）一律不新增；合同错漏回退详细阶段，trace §4 留回退记录（指向被修订的 `UNIT-<slug>` 与修订动作），不在实现里就地改设计。
- 严守 golden-path 锁定红线，不可豁免：①**server-first**——默认 `server-component`，`'use client'` 仅在需要状态/事件/浏览器 API 处出现且尽量下沉到叶子组件，禁把整页标 `'use client'`；②**私有数据获取/secret 隔离**——私有 `fetch`、API key、DB 连接、token 只在 `server-component`/`data-access`/`server-action`，**禁 `client-component` 直取**或把 secret 经 props 透传到客户端边界；③**分层依赖律**（见上）严格单向无环；④**route 段约定**——`page/layout/loading/error.tsx` 各司其职，`error.tsx` 必为 `'use client'` 错误边界，异步段配 `loading.tsx`；⑤**metadata/SEO 标准化**——用 `metadata` 导出或 `generateMetadata`，禁手写裸 `<head>` 污染；⑥**样式隔离**——CSS Modules 或 Tailwind，禁新增全局 `*.css` 污染（`globals.css` 仅 reset/token，不放组件样式）；⑦**TS strict**——禁 `any` 兜底、禁 `@ts-ignore` 无理由豁免。
- 不私自拍板实现中冒出的新决策（是否引入 Zustand、是否换 UI 库、是否新增 `next/image` loader、是否切内容源 MDX→CMS、是否启用 ISR/`revalidate` 策略、缓存 `fetch` 的 `cache`/`next.revalidate` 取值）→ 记录并升级人工 Gate，落到 project-conventions 槽位或 `technology_decision_handoff` 后再继续。
- secret/credential 合规：`.env.example`、fixtures、代码与 trace 只写环境变量名引用（如 `DATABASE_URL`、`NEXTAUTH_SECRET`、`NEXT_PUBLIC_*` 仅放可公开值），不落真实 API key、token、会话密钥；区分 `NEXT_PUBLIC_` 前缀（会进客户端 bundle，禁放敏感值）与服务端专属变量。
- 不采用默认 TDD/RED-GREEN：默认只运行 project-conventions 测试框架槽位下的既有验证命令（Vitest+RTL / Playwright），不为驱动结构而先造 mock 组件/fake fetch；高风险切片（`server-action` 变更与鉴权、数据获取缓存/`revalidate`、错误边界与 `loading` 边界、`client-component` 的 hydration 行为、route 参数与 `generateStaticParams`）按详细设计测试映射先补失败路径测试再实现。新增测试须可追溯到承接的 `BHV-NNN`/`UNIT-<slug>`。
- 触碰存量违例（项目约定中的存量违例清单）按标准包口径分类记录（绕行/顺手修复/记债），不把绕行或顺手修复混入业务 diff。
- 若其它通用 skill、插件或 agent 习惯（整页 `'use client'`、自动重构、引入状态库、把数据获取塞进客户端组件、手写全局样式）与本平台 golden-path / trace 合同冲突，以平台 SSOT 为准，冲突项忽略或向用户确认。
- **与 `trellis-implement` 的边界**：本 skill 是官方 `trellis-implement` 在 Guru H5 项目的领域化执行口径——`trellis-implement` 负责通用任务编排与状态机推进（grab/dispatch/状态流转），本 skill 不重复其职责，只补齐 H5 平台的 server-first 红线、分层依赖律、私有数据获取隔离、route 段约定与 trace 证据要求；Phase 2 dispatch 时在 prompt 中指明加载本 skill 口径。规则正文不在本 skill 复写，住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`。

## 执行流程（WX 步骤）

1. **WX-0 判定实现模式与构建基线**：判定空项目初始化 / 已有项目增量 / 重构校准；确定本任务落在哪个 route 段与模块目录，复用还是新建 `server-component`/`client-component`/`data-access`/`ui-component`/`domain-type`/`server-action` 资产，是否触碰共享面（`layout.tsx`、`globals.css`、`metadata` 基线、`next.config`）。记录改动前 `tsc --noEmit` + `next lint`（或 `eslint`）基线退出态。
2. **WX-1 计划（开工前写）**：按 trace 合同 §1 在目标仓库 `implement.md`（建议 `docs/design/<feature>/implementation-trace.md`）产出任务切片。每片含：承接的 `UNIT-<slug>`（幽灵引用被 Gate 拦截）+ 所属 doc_type + 文件范围 + 完成信号 + 验证方式。执行顺序**自底向上**（钉死）：`domain-type`（TS 类型/zod schema）→ `data-access`（fetch/内容源/查询封装）→ `server-action`（变更/handler）→ `server-component`（渲染编排）→ `client-component`（交互）→ `ui-component`（展示复用）→ `route`（段装配 + metadata）。逐条预判高风险点（server/client 边界划分、私有 secret 是否会越界进客户端 bundle、`fetch` 缓存与 `revalidate` 语义、`error.tsx`/`loading.tsx` 边界、`generateMetadata` 与动态参数、hydration 不匹配）。人工确认从最小可独立通过 `tsc` 的切片开始。
3. **WX-2 逐片实现（随做随记）**：每片对照承接 `UNIT-<slug>` 的合同八问落地——②输入/输出/错误（组件 props 类型、`server-action` 入参与返回、`data-access` 函数签名、zod schema 校验失败分支）；④调用关系单向（`server-component` 调 `data-access` 不反向、`client-component` 只组合 `ui-component`、`server-action` 走 `data-access`）；⑤失败收口（`error.tsx` 错误边界、`data-access` 失败抛错或返回判别联合、`server-action` 校验失败的结构化返回）；⑥后置副作用（`server-action` 后 `revalidatePath`/`revalidateTag`、`redirect`）。每片完成**立即**更新 trace §2（实际改动文件清单标 doc_type、与计划偏差及原因、触碰 `layout.tsx`/`globals.css`/`metadata` 基线/共享 `ui-component` 的共享面单独标注），不积压到批末。
4. **WX-3 代码生成 / 内容流水线（仅触发条件满足时）**：按 project-conventions 选型执行并记入 trace §2——内容源为 MDX → 记 MDX 编译/`gray-matter` frontmatter 解析约定（示例 `scripts/gen-rss.js` 用 `gray-matter` 提取 `title/date/description/tag/author`，生产侧若保留 RSS/sitemap 生成须把命令与产物记清）；启用 ORM 代码生成（如 Prisma `prisma generate`）→ 记命令与产物；zod schema 推导类型 → 记 `z.infer` 落点。**当前 golden-path 默认无强制代码生成槽位 → 本项写「N/A：无代码生成槽位启用」，不留空、不私自引入生成器。**
5. **WX-4 逐片验证（验证后记）**：按 trace 合同 §3 记入 trace §3——类型检查 `tsc --noEmit`（贴命令 + 退出态，失败写错误摘要 + 处置；strict 下不得用 `any`/`@ts-ignore` 掩盖）；构建/lint `next build` 或 `next lint`（或 `eslint .`，逐条通过/失败，eslint-disable 豁免写理由并指向存量违例清单）；测试到**测试名级别**（Vitest+RTL：`vitest run src/components/PostCard.test.tsx -t "renders title"` 给出用例名；Playwright：`playwright test post-detail.spec.ts --grep "loads post"`），新增测试逐条列文件 + 用例名 + 承接 `BHV-NNN`/`UNIT-<slug>`；依赖变更跑包管理器安装记 diff（新增库须落在已批准槽位内，禁被锁红线绕开，如擅自引入状态库/UI 库）。失败先修复再进下一片；未验证项显式列出并指明留给哪个环节（真实数据源/CMS 联调 → 集成环境；SEO/metadata 实际抓取 → 部署后 Lighthouse/抓取验证；hydration/交互真机表现 → Manual QA / 真机；缓存与 `revalidate` 生产行为 → 灰度/预发）。
6. **WX-5 存量违例处置**：触碰存量违例清单条目时按标准包口径分类记录到 trace §4（绕行须写「为何不修」；顺手修复须独立标注；记债须给清单编号）。H5 常见存量违例：整页 `'use client'` 历史残留、`client-component` 直取私有 `fetch`、全局 `*.css` 组件样式污染、`metadata` 缺失/手写裸 `<head>`、缺 `error.tsx`/`loading.tsx`、`tsconfig` 残留 `strict:false` 或散落 `any`。
7. **WX-6 收口自检**：对照实现 Gate G1~G6（见下「质量门禁」）输出自检摘要；上游缺陷已回退修订而非就地改设计；未验证项显式移交（集成环境 / Lighthouse / Manual QA / 真机 / 灰度）。

## 输出

- **实施计划先列**：`implement.md`（trace）路径、`UNIT-<slug>` 承接清单、`chapter_target → detail_doc_type → H5 代码资产`（route 段/模块/文件）映射、自底向上的阶段顺序与高风险点（server/client 边界、secret 越界、缓存语义、错误/加载边界）、阻塞项。
- **代码改动 + 新增/修订测试**：改动文件按 doc_type 标注（如 `app/posts/[slug]/page.tsx`（route）、`app/posts/[slug]/PostView.tsx`（server-component）、`lib/posts.ts`（data-access）、`components/PostCard.tsx`（ui-component）、`types/post.ts`（domain-type）、`app/actions/comment.ts`（server-action）、`components/LikeButton.tsx`（client-component））。
- **完整的 `implement.md`（trace 四节齐全且非空）**：计划 / 执行 / 证据 / 阻塞与偏差；证据节带命令级记录与测试名，无阻塞则显式写「无」。
- **Gate G1~G6 自检摘要 + 移交清单**：逐项给结论（pass / 阻塞 / 移交环节）；交付时说明修改文件、对应设计锚点（`UNIT-<slug>` / `BHV-NNN`）、验证命令、未验证项与剩余阻塞。
- **若无法完成**：明确输出 `blocked` 的具体详细设计文件、缺失合同锚点（如八问缺 props 类型/缺 `server-action` 失败分支/缺测试映射）与需要回修的合同项；环境阻塞写准确命令、错误摘要、缺失依赖与恢复条件，结论不得标 `pass`。

## 质量门禁（与 `guru_gate.py implement` / 实现 Gate 同口径）

切片可进入 commit/PR，当且仅当：

- **G1 trace 四节齐全且非空**：计划有 `UNIT-<slug>` 承接与完成信号、执行有改动清单与偏差说明、证据有命令级记录、阻塞节如无则显式写「无」；`implement.md` 必须存在（trace 不存在直接 fail）。
- **G2 类型与构建证据**：`tsc --noEmit` 全绿（贴命令 + 退出 0，strict 下无新增 `any`/无理由 `@ts-ignore`）；`next build` 或 `next lint` 通过；本任务引入的失败已全部收口（类型/构建不过的切片不存在「完成」）。
- **G3 静态检查证据**：`next lint`/`eslint .`（+ Prettier 如槽位启用）通过，或豁免有理由且记债（指向存量违例清单）。
- **G4 测试证据**：每个切片有测试名级别结果（Vitest+RTL 用例名 / Playwright grep 名），覆盖承接 `UNIT-<slug>`/`BHV-NNN` 的成功路径 + 全部失败路径（如 `server-action` 校验失败、`data-access` 取数失败、`error.tsx` 触发）；新增测试清单可追溯到 UNIT；未执行的验证不得写成通过。
- **G5 分层与 server-first 契约**：分层依赖律无反向/越层（`client-component` 未直取私有 `data-access`/`fetch`、`route` 未直查 DB、`data-access` 未反向 import `route`/`server-component`）；`'use client'` 最小化未把整页标客户端；私有 secret 未越界进客户端 bundle（无 `NEXT_PUBLIC_` 误放敏感值、无 secret 经 props 透传到 `'use client'` 边界）；`metadata`/SEO 标准化、`error.tsx`/`loading.tsx` 按 route 约定就位；样式隔离未新增全局污染。
- **G6 偏差闭合 + 编号闭合**：PR diff 与计划逐项可对，计划外改动均有原因记录；切片均挂真实 `UNIT-<slug>`（幽灵单元被拦截）；上游结构性缺陷（归属错、合同越界、单元跟随名词而非行为）已回退拥有该决策的阶段修订，禁止在实现阶段补造。

任一未满足 → 不进 commit。`tsc --noEmit` / `next lint` / `next build` / 测试（测试名级别）由 worktree 验证条目执行，与本自检同口径。

## 好例 / 坏例

✅ **合格切片登记与证据**（粒度可独立 review、命令级证据、可追溯、server-first 守住）：

```
切片 S2 | 承接 UNIT-post-data-access (doc_type: data-access)
  范围：lib/posts.ts —— getPostBySlug(slug) 用 gray-matter 解析 MDX frontmatter（title/date/description/tag/author），
        失败返回判别联合 { ok:false; reason:'not-found' }；类型来自 UNIT-post-type(domain-type)
  完成信号：tsc --noEmit 退出 0；私有读取仅在服务端模块；无被 client-component import
  证据：
    - tsc --noEmit → 退出 0（strict，无 any）
    - next lint → 0 problems
    - vitest run lib/posts.test.ts -t "getPostBySlug"
        ✓ getPostBySlug > returns post when slug exists
        ✓ getPostBySlug > returns not-found when missing
      新增测试：lib/posts.test.ts（承接 UNIT-post-data-access / BHV-014 成功+失败路径）
    - 未验证：真实 CMS 源联调 → 留给集成环境；RSS/sitemap 生成（参考示例 gen-rss.js）本切片不涉
```

❌ **不合格**：「实现文章详情页，改 page 和组件，写完跑一下」——无 `UNIT` 编号、无 doc_type、无文件范围、无完成信号、跨多层无法独立 review；证据「全部编译通过，测试通过，lint 无问题」——无命令、无退出态、无测试名、无新增测试映射、未声明未验证项。

❌ **红线违例**：把整个 `page.tsx` 标 `'use client'` 只为用一个 `useState`（违反 server-first，应下沉交互到叶子 `client-component`）；在 `client-component` 里直接 `fetch('/internal-api', { headers:{ Authorization: process.env.SECRET }})`（私有 secret 越界进客户端 bundle，违反隔离红线）；新增 `globals.css` 写组件级样式（破坏样式隔离）；route 段缺 `error.tsx` 又用 `try/catch` 在组件里吞错（绕过错误边界约定）；实现里擅自引入 Zustand/MUI 未升级 project-conventions；trace 在 PR 前一次性补写（失去过程证据）。

## 不适用场景（本 Skill 不约束的边界）

- 详细设计阶段的接口/数据结构定义（合同八问）：实现 trace 只承接不重定义；八问缺错（漏 props 类型、`server-action` 签名与返回不符、测试映射漏失败路径、未指定缓存/`revalidate` 策略）→ 回退详细阶段，不在实现里改设计。
- 概要归属与技术决策（行为 owner、分层归属、doc_type 选型、技术选型）：属概要 Gate；实现发现归属错（如某单元本应是 `server-component` 却被标 `client-component`）只能回退，不在 trace 里改。
- 纯文档/注释/格式化变更（无行为改动、无新切片）：可不建独立 trace 切片，但仍需 Prettier/`eslint` 通过；与功能切片同 PR 则并入对应切片记录。
- 内容源语义裁决（MDX frontmatter 字段含义、CMS schema、内容模型）：属上游设计；trace 只记录「消费方类型与解析是否随内容模型更新」这一执行事实。
- l10n / 文案同步脚本：人工受控，本 skill 不触发执行。
- 分支/worktree/提交/PR 流程隔离：交给流程 Skill（`sop-task-runner`，复用后端、栈无关）——先用本 Skill 判定改动范围 → 流程 Skill 创建隔离 → 在隔离内继续本 Skill。

## 与官方 Trellis skill 的边界

本 skill 是官方 `trellis-implement` 在 Guru H5（Next.js App Router + React + TypeScript strict 形态）项目的领域化执行口径：sub-agent 实现时按本 skill 的 WX 流程、golden-path 红线（server-first / 私有数据隔离 / 分层依赖律 / route 段约定 / metadata 标准化 / 样式隔离 / 错误边界）与 trace 合同四节工作；Phase 2 dispatch 时在 prompt 中指明加载本 skill 口径。`trellis-implement` 负责通用任务编排与状态机推进，本 skill 不重复其职责，只补齐 H5 平台特有的执行约束与证据要求。规则正文不在本 skill 复写，住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`，doc_type 七类取值住 `.trellis/spec/harness/index.md`。
