# H5 实现阶段标准包（L1 · guru-h5-web / golden-path 锁定）

> 本文件是 `guru-h5-web` Harness 的实现阶段 **L1 标准 SSOT**，由代码编写与实现审核**同源引用**。
> 目标平台：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。
> grounded 在 `next.js/examples/blog` 真实写法（Pages Router + Nextra + MDX + gray-matter 的轻量 blog starter，故意简化）；**该示例作为内容模型基线**，golden-path 以 **App Router 生产最佳实践**为准。全文凡引用示例处显式标注「示例实证」，凡 App Router 生产形态处标注「生产级补充」，两者不得混淆。
> 实现阶段只**承接**已审核通过的详细设计，不重新设计业务行为、owner、依赖边界、数据获取策略、渲染边界、错误语义、SEO/metadata 合同、配置项或运行合同。
>
> 装载（安装后路径）：
> - 通用方法真源：`.trellis/spec/guides/golden-path.md`（模块形态、分层依赖律、server/client 边界、数据获取层范式、样式隔离、错误边界、禁止清单）。
> - 流程骨架与本标准包：`.trellis/spec/harness/implementation/implementation-h5-standard.md`（本文件）。
> - 项目槽位取值：`.trellis/spec/conventions/project-conventions.md`（内容源 / 状态管理 / UI 库 / 样式方案 / 测试 / lint / 数据库 / 认证 / 图像优化 / 部署 / 路由模式）。
> - trace 合同：`.trellis/spec/harness/implementation/implementation-trace-contract.md`。
> - L2 详细合同（render/interactive/data 三元组）：`.trellis/spec/harness/detail/detail-type-server-component.md` / `detail-type-client-component.md` / `detail-type-data-access.md`；其余四类（route / ui-component / domain-type / server-action）当前 `l2_status: pending`，按本文件 §2 合同八问展开，走 full 链须先取 L2 豁免。

---

## 0. 本标准包定位与边界

适用：
- Next.js + React + TypeScript H5 前端实现阶段的可编码合同定义、代码编写执行依据、实现审核依据。
- 从已审核详细设计单元（`UNIT-<slug>`）到 TS/TSX 代码的承接、`implement.md` trace 主文档、实现 Gate 判定、存量豁免口径。

不适用：
- 详细设计正文生成、需求 / 概要 / 详细设计审核（各有对应阶段 SSOT）。
- golden-path 与 project-conventions 槽位本体的重定义——本文件只引用，不复制其规则正文。

中立性约束：
- 本标准包**不执行**代码修改，也**不输出**审核 Findings。它定义"代码编写"与"实现审核"共同遵守的合同与判定口径。
- golden-path 的硬规则（TS strict、server/client 边界、数据获取层、样式隔离、错误边界、分层依赖律）在本文件中是**锁定前提（不可豁免）**；project-conventions 的槽位（内容源 / 状态管理 / UI 库 / 测试框架 / lint 等）是**可按项目调整的取值**，实现时读 `project-conventions.md` 当前值，不在本文件硬编码。

### 0.1 doc_type 权威七类（全程唯一，禁止改名/增减/换数）

H5 详细设计 doc_type 一律以 H5_BRIEF 为权威，**勿照抄 flutter（controller/usecase/repository）或 Go（handler/service/repository）的类型名**。

| doc_type | 角色 | 一句话职责 | L2 状态 |
|----------|------|-----------|---------|
| `server-component` | RSC 服务端组件（默认） | 渲染编排 + 数据获取编排（默认无 `'use client'`） | full（`detail-type-server-component.md`） |
| `client-component` | `'use client'` 交互组件 | 状态 / 事件 / hooks（浏览器侧交互） | full（`detail-type-client-component.md`） |
| `data-access` | 数据访问层 | fetch 封装 / 内容源（MDX/CMS）/ ORM 查询 | full（`detail-type-data-access.md`） |
| `route` | App Router route 段 | `page/layout/loading/error.tsx` + metadata/SEO | pending（按 §2 八问展开） |
| `ui-component` | 展示型可复用组件 | 纯展示，无数据获取、无业务 | pending |
| `domain-type` | TS 类型 / zod schema / 领域模型 | 类型 / 校验 schema / 领域模型 | pending |
| `server-action` | Server Actions / route handlers | 变更（mutation）/ API endpoint | pending |

> render/interactive/data 三元组（`server-component` / `client-component` / `data-access`）对应 flutter 的 controller/usecase/repository-datasource，但**类型名不互换**。其余四类 L2 `pending`，full 链须显式 L2 豁免并在 `implement.md` 记录。

---

## 1. golden-path 锁定前提（不可豁免）

下列规则来自 `.trellis/spec/guides/golden-path.md`，是 H5 平台的 golden-path 锁定项。实现阶段**任何切片**都不得违反，也不得在 `implement.md` 用"存量豁免"绕过；触碰即 Gate `fail`。

> 示例基线说明：`next.js/examples/blog` 的 `tsconfig.json` 实测为 `"strict": false`（示例实证），且是 **Pages Router**（`pages/_app.tsx`、`pages/posts/*.md`、`pages/tags/[tag].mdx`，示例实证）。**这是示例的故意简化，不作为 golden-path**。golden-path 锁定项以 App Router 生产形态为准（生产级补充），下文对每条 LOCK 明确标注。

### LOCK-1 TypeScript strict（生产级补充，覆盖示例）

- 生产工程 `tsconfig.json` 必须 `"strict": true`（含 `noImplicitAny` / `strictNullChecks`），并开 `"noUncheckedIndexedAccess"`、`"forceConsistentCasingInFileNames"`、`"isolatedModules"`（Server Component 编译需要）。
- 禁止 `any` 逃逸业务边界、禁止 `// @ts-ignore` / `@ts-nocheck` 抹平类型错误（确需抑制用 `@ts-expect-error` 且必须带原因注释 + 跟随修复债）。
- 外部输入（fetch 响应 / 路由参数 / 表单数据 / MDX frontmatter）跨入域内**必须经 `domain-type`（zod schema 或类型守卫）收窄**，不得 `as` 强转裸 `JSON.parse` 结果。
- 好例子（生产级补充）：`const post = PostSchema.parse(await res.json());` —— frontmatter / API 响应过 zod 校验后才进入 `domain-type`。
- 坏例子：示例式 `frontmatter.data.tag.split(", ")`（`scripts/gen-rss.js` 示例实证，`data` 为 `any`）直接进生产渲染路径，无类型收窄——触碰 LOCK-1，Gate `fail`。

### LOCK-2 server-first / `'use client'` 最小化（生产级补充，示例为 Pages Router 无此概念）

- 默认所有组件是 `server-component`（RSC，无 `'use client'`）；仅在确需浏览器交互（事件、`useState`/`useEffect`/`useRef`、浏览器 API、第三方仅客户端库）时，才在文件**顶部首行**标 `'use client'` 转 `client-component`。
- `'use client'` 下沉到**叶子交互组件**，不在 `route` 段的 `layout.tsx` / `page.tsx` 顶层无差别标注（会把整棵子树拉成 client，破坏 server-first）。
- `client-component` 通过 `props` / `children` 接收 server 侧已获取的数据，**不在 client 侧重复发起私有数据获取**（见 LOCK-3）。
- 好例子（生产级补充）：`page.tsx`（`server-component`）`await getPost(slug)` 取数 → 把数据作为 prop 传给 `<LikeButton initialCount={...}/>`（`client-component`，只管点赞交互）。
- 坏例子：把整个 `page.tsx` 标 `'use client'` 后在组件内 `useEffect(() => fetch('/api/post'))` 客户端取数渲染首屏——破坏 server-first 与 SEO，触碰 LOCK-2，Gate `fail`。

### LOCK-3 数据获取层与 secret 边界（生产级补充）

- 私有数据获取、secret、long-lived token、DB 连接、CMS API key **只允许出现在 `server-component` / `data-access` / `server-action`**；`client-component` / `ui-component` **禁止**直接读 secret、禁止直连 DB、禁止持有服务端凭据。
- 数据获取统一收口到 `data-access` 层（`fetch` 封装 / 内容源读取 / ORM 查询），返回 `domain-type`；`server-component` 调 `data-access` 编排数据，不在组件体内散写裸 `fetch(url, { headers: { Authorization: SECRET }})`。
- secret 走 server-only 环境变量（无 `NEXT_PUBLIC_` 前缀）；凡需暴露到浏览器的配置才用 `NEXT_PUBLIC_*`，且其中**不得含 secret**。可用 `import 'server-only'` 给 `data-access` 模块加运行时护栏，防止被 client 误导入。
- 缓存 / 重验策略（`fetch` 的 `cache` / `next.revalidate`、`revalidatePath` / `revalidateTag`）由详细设计指定，实现期按合同落地，不自行更改缓存语义。
- 好例子（内容模型基线 = 示例实证 + 生产级补充）：示例用 `gray-matter` 读 `pages/posts/*.md` frontmatter（`scripts/gen-rss.js` 示例实证）作为内容源；生产形态把"读内容源"收进 `data-access`（如 `lib/posts.ts` 的 `getAllPosts()` / `getPostBySlug()`），返回 `domain-type` 的 `Post[]`，`server-component` 仅消费。
- 坏例子：`client-component` 内 `const key = process.env.CMS_SECRET` 直接拼请求——secret 泄漏到浏览器 bundle，触碰 LOCK-3，Gate `fail`。

### LOCK-4 route 段约定与 metadata/SEO（生产级补充，示例为 Pages Router 等价物）

- App Router route 段按约定文件组织：`page.tsx`（路由 UI 入口，`server-component`）、`layout.tsx`（共享布局 + `<html>/<body>` 根）、`loading.tsx`（Suspense fallback）、`error.tsx`（`'use client'` 错误边界，见 LOCK-6）、`not-found.tsx`（404）。
- metadata/SEO 标准化：静态用 `export const metadata: Metadata`，动态用 `export async function generateMetadata(...)`；动态路由用 `generateStaticParams()` 预生成（对齐示例的静态 blog 形态）。
- 路由参数 `params` / `searchParams` 进入 route 段后**必须经 `domain-type` 收窄**（LOCK-1）。
- 好例子（内容模型基线）：示例 `pages/tags/[tag].mdx`（示例实证，Pages Router 动态段）→ 生产形态 `app/tags/[tag]/page.tsx`（生产级补充）配 `generateStaticParams()` 列出全部 tag + `generateMetadata()` 输出 `title: 'Tagged: ${tag}'`。
- 坏例子：在 `route` 段把 metadata 写死成全站同一 `<title>`，或动态页缺 `generateMetadata` 导致所有详情页同标题——SEO 合同未落地，触碰 LOCK-4，Gate `fail`。

### LOCK-5 样式隔离（禁全局污染，生产级补充）

- 样式只允许 CSS Modules（`*.module.css`）或 Tailwind utility（取值见 `project-conventions.md`）；全局样式只允许 `app/globals.css` 一处（reset / 设计 token / 字体），且不含组件级选择器。
- 禁止裸全局 `className` 选择器污染（如在组件里写非 Module 的 `.title { ... }` 全局规则）；禁止跨组件用全局类名耦合。
- 字体走 `next/font`（生产级补充，自动 self-host + 无 CLS）；示例用 `pages/_app.tsx` 手动 `<link rel="preload" .../>` 预载字体（示例实证）是 Pages Router 旧法，生产不照抄。
- 好例子（生产级补充）：`import styles from './Card.module.css'` → `<div className={styles.card}>`；或 Tailwind `<div className="rounded-lg p-4">`。
- 坏例子：组件内 `<style jsx>{` footer { ... } `}</style>`（示例 `theme.config.js` 示例实证）当生产全局样式方案，或在 `globals.css` 写 `.card { ... }` 被多组件抢用——触碰 LOCK-5，Gate `fail`。

### LOCK-6 错误边界与加载边界（生产级补充）

- 每个有数据获取/可失败的 route 段必须有 `error.tsx`（`'use client'`，接 `error` + `reset` props）兜底；列表/详情等异步段配 `loading.tsx` 或显式 `<Suspense fallback>`。
- `not-found.tsx` + `notFound()` 用于"资源不存在"语义（对齐 `data-access` 返回 null 的契约），不与 500 错误混用。
- `server-action` / `data-access` 的失败按详细设计映射到错误语义（抛错 → `error.tsx` 捕获 / 返回结构化错误供 `client-component` 展示），不静默吞错。
- 好例子（生产级补充）：`getPostBySlug(slug)` 找不到 → `route` 段 `if (!post) notFound()` → 命中 `app/posts/[slug]/not-found.tsx`。
- 坏例子：异步 route 段无 `error.tsx`，取数失败时整页崩白屏；或 `catch {}` 静默吞掉错误——触碰 LOCK-6，Gate `fail`。

### LOCK-7 分层依赖律（严格单向、无循环）

- owner 层与依赖方向固定（归属硬基准，违反 fail）：
  - 服务端链：`route → server-component → data-access → domain-type`
  - 交互链：`client-component → ui-component`
  - 变更链：`server-action → data-access`
- `domain-type` 是最底层纯类型/schema，可被任意层导入；`ui-component` 纯展示可被 `client-component` / `server-component` 复用。
- **禁止反向/横向越界**：`data-access` 不导入 `server-component` / `route`；`ui-component` 不导入 `data-access`（不取数）；`client-component` 不导入 `server-action` 的服务端实现做直调（通过 action 引用调用）；`server-component` 不把 secret 透传进 `client-component`。
- 好例子（生产级补充）：`app/posts/[slug]/page.tsx`（`route`/`server-component`）→ `import { getPostBySlug } from '@/lib/posts'`（`data-access`）→ 返回 `Post`（`domain-type`）→ 渲染 `<Article post={post}/>`（`ui-component`）。
- 坏例子：`ui-component` 内 `await fetch('/api/...')` 自行取数，或 `data-access` `import` 了某个 `page.tsx`——反向/越界依赖，触碰 LOCK-7，Gate `fail`。

> 不适用场景：纯静态营销页（无数据获取、无交互）可只用 `route` + `ui-component`，不强制 `data-access` / `server-action`；纯客户端小工具（如不依赖 SEO 的内嵌 widget）经详细设计授权可整体 `client-component`，但仍须遵守 LOCK-1（strict）、LOCK-3（secret 边界）、LOCK-5（样式隔离），并在 `implement.md` 计划节显式声明理由。

---

## 2. 可编码合同（承接判定）

实现阶段的输入是**已审核通过的详细设计单元**（`UNIT-<slug>`）。一个详细设计单元"可编码"当且仅当下列八项合同齐全且无歧义；任一缺失则该切片置 `blocked`，回退详细阶段修订（见 §7），不得在代码里临时补设计。

合同八项（对齐详细 Gate 的合同八问，逐项必须能落到 TS/TSX 代码锚点）：

| # | 合同项 | 可编码判据（落到 H5 锚点） |
|---|--------|---------------------------|
| 1 | 承接行为 | 该单元承接哪些 `BHV-NNN`；prd 无此编号即幽灵引用，`blocked` |
| 2 | doc_type 与 owner | 单元归属七类之一，且 owner 链符合 LOCK-7；render/interactive/data 三类有 L2，其余四类按八问展开（无 L2 豁免记录则 `blocked`） |
| 3 | 接口/契约签名 | 组件 props 类型、`data-access` 函数签名（`(args) => Promise<DomainType>`）、`server-action` 入参/返回、`domain-type` 字段与 zod schema 可直接落地 |
| 4 | 数据与渲染边界 | 哪些数据由 `server-component`/`data-access` 取、缓存/重验策略、哪段必须 `'use client'`、`params/searchParams` 形态可直接定义 |
| 5 | 执行流程 | 每步骤可落到组件渲染分支、数据获取调用、状态更新、事件 handler、action 调用或错误返回（不允许"渲染页面/处理交互"式大组件占位） |
| 6 | 失败与边界收口 | 每类失败映射到 `notFound()` / `error.tsx` / 结构化错误 / 校验失败，以及 loading 边界；不静默吞错 |
| 7 | 依赖边界 | `direct_dependencies[]` 每项映射到 `import` 来源 + owner 层；无下层缺口（下游 `data-access`/`domain-type` 已定义或同切片先实现） |
| 8 | 测试映射 | 既有验证命令落点（`tsc` / `next build` / `eslint` / 既有 test）；或 §6 allowlist 允许的纯函数/纯展示组件最小单测目标 |

可验证信号：
- `implement.md` 的合同追踪表中，每个 `UNIT-<slug>` 都能回指上述八项的代码锚点或 `blocked` 依据。
- 每个执行流程步骤都有预期代码落点；每个 `direct_dependencies[]` 行都能映射到 `import` 来源 → owner 层 → 装配/调用点。
- 概要承接索引能从 `chapter_target → doc_type`（七类之一）落到具体文件路径（`app/.../page.tsx`、`lib/*.ts`、`components/*.tsx`、`types/*.ts`、`*.action.ts`）。

约束边界：
- 不从代码、习惯或参考工程反推需求；不猜测、发明、补全详细设计未定义的契约 / props / 字段 / 错误语义 / 缓存策略 / 路由段 / 依赖。
- 不把详细设计的行为步骤合并、改序、上移、下沉或省略，除非详细设计本身给出依据。
- 不为编译通过新增 fake、optional path、占位结果、内存 mock 数据、`any` 逃逸或硬编码依赖。
- 不把示例（Pages Router / `gray-matter` / `<style jsx>`）的简化写法当生产合同照抄。

---

## 3. 实现顺序（依赖方向从下至上）

代码阶段唯一执行顺序。先实现被依赖层，再实现调用层；上层不得用 fake / 占位 / 内存 mock / hardcoded 依赖绕过下层缺口。顺序对齐 LOCK-7 owner 链。

```text
Phase 0  设计合同解析 + implement.md 计划            （不写生产代码）
Phase 1  domain-type：TS 类型 / zod schema / 领域模型
Phase 2  data-access：fetch 封装 / 内容源(MDX/CMS) / ORM 查询，返回 domain-type
Phase 3  server-action：Server Actions / route handlers（变更 / API endpoint）
Phase 4  server-component：渲染编排 + 数据获取编排（默认无 'use client'）
Phase 5  client-component：'use client' 交互（状态 / 事件 / hooks）
Phase 6  ui-component：纯展示可复用组件（无取数、无业务）
Phase 7  route：page/layout/loading/error/not-found.tsx + metadata/SEO + generateStaticParams
Phase 8  验证与符合性审查：tsc / next build / eslint / test + 证据回填
```

> 说明：`ui-component`（Phase 6）虽是叶子，但通常在 `client-component`/`server-component` 之后落地以便对齐其消费契约；若详细设计显式声明纯展示组件先行，可在 detail 确认前调整 `implement.md`；detail 确认后只能记录到 mutable evidence，需改变计划则回退 detail Gate。`route`（Phase 7）最后落地，因为它装配全部下层。

阶段共同规则：
- Phase 0 在 detail 确认前创建或更新 `implement.md` 计划合同；detail 确认后 `implement.md` 不再作为执行状态写入点。
- Phase 1~8 的切片状态、改动文件、偏差、阶段自检和恢复条件追加到 `implementation-evidence.jsonl`；验证命令和测试名级证据追加到 `verification-evidence.jsonl`。
- Phase 0 未通过不得写生产代码；Phase 1~7 只能按依赖方向推进；发现下层合同缺失，当前生产路径必须 `blocked`。

各 Phase 的产物合同与出入口条件见 §4。

---

## 4. 各 Phase 产物合同与出入口

### Phase 0 — 设计合同解析（不写生产代码）

输入：概要承接索引（`chapter_target → doc_type`，七类）、目标详细设计单元、`golden-path.md`、`project-conventions.md`、现有代码骨架。

代码前硬门禁：
- 必须先创建或更新 `implement.md` 的计划节；小迭代可缩小范围，但不得跳过计划，也不得"先写代码再补 trace"。若 detail 已确认而计划缺失或需改变，必须回退 detail Gate，不在实现阶段静默补写。
- 完成 `UNIT-<slug> → 代码资产`（文件路径 + owner 层）映射；识别 LOCK 锁定面（strict / server-client 边界 / secret 边界 / route 约定 / 样式隔离 / 错误边界 / 分层依赖）与 Secret/Credential 检查面；为每个切片写明 `checkpoint` 与 `validation_commands`。
- 对 `route`/`ui-component`/`domain-type`/`server-action`（L2 `pending`）四类，确认已按 §2 八问展开或已登记 L2 豁免。

出口条件：
- 每个目标单元都有合同追踪行与资产映射行；每个执行流程步骤都有预期代码落点；无未解释的设计缺口（有则 `blocked`）。

失败判定：`chapter_target → doc_type` 映射缺失或 doc_type 不在七类内；执行流程步骤无法落到代码目标；`direct_dependencies[]` 无法形成 owner 链闭环；缺 `implement.md` 计划节。

### Phase 1 — domain-type（最底层纯类型 / schema）

产物合同：
- 实体/视图模型 TS 类型 + 入参/出参类型；外部输入用 zod schema（或等价校验器，取值见 `project-conventions.md`）定义并导出 `z.infer` 类型。
- 可空/可选用 `?` 或 `| null` 显式表达（LOCK-1 strict 下不可隐式 `undefined`）；不在 `domain-type` 引入 React / fetch / DB 依赖（纯类型层）。
- 好例子（内容模型基线，生产级补充，对齐示例 frontmatter 字段 `title/date/description/tag/author`，示例实证）：

  ```ts
  // types/post.ts
  import { z } from 'zod';
  export const PostFrontmatterSchema = z.object({
    title: z.string(),
    date: z.string(),                 // 示例 frontmatter 用字符串日期
    description: z.string().optional(),
    tag: z.string(),                  // 逗号分隔，由 data-access 解析
    author: z.string(),
  });
  export type PostFrontmatter = z.infer<typeof PostFrontmatterSchema>;
  export interface Post extends PostFrontmatter { slug: string; tags: string[]; }
  ```

- 坏例子：`export type Post = any` 或 `export interface Post { data: object }` ——类型不收窄，破坏 LOCK-1。

出口条件：所有承接单元的类型、可空语义、校验 schema 落地；`tsc --noEmit` 对类型层通过。

失败判定：`domain-type` 含 React/取数逻辑；用 `any`/`object` 占位；外部输入无 schema 校验入口。

### Phase 2 — data-access（数据获取层）

产物合同：
- 每个数据获取函数签名形如 `async function getX(args): Promise<DomainType>` / `Promise<DomainType | null>`；内容源/CMS/ORM 读取封装在此层，返回 `domain-type`，**不返回原始未校验响应**。
- 私有数据获取/secret 只在此层（或 `server-component`/`server-action`），可加 `import 'server-only'` 护栏（生产级补充）；缓存/重验策略（`fetch` 的 `{ cache, next: { revalidate, tags } }`）按详细设计落地。
- "资源不存在"返回 `null`（供上层 `notFound()`），可恢复错误抛结构化 error（供 `error.tsx`），不静默吞错（LOCK-6）。
- 好例子（内容模型基线 = 示例实证 + 生产级补充）：示例用 `gray-matter` 读 `pages/posts/*.md`（示例实证）；生产收进 `data-access`：

  ```ts
  // lib/posts.ts
  import 'server-only';
  import { PostFrontmatterSchema, type Post } from '@/types/post';
  export async function getPostBySlug(slug: string): Promise<Post | null> {
    const file = await readPostFile(slug);          // 内容源 I/O
    if (!file) return null;                          // 不存在 → null（上层 notFound）
    const fm = PostFrontmatterSchema.parse(file.data); // LOCK-1 收窄
    return { ...fm, slug, tags: fm.tag.split(', ').map(t => t.trim()) };
  }
  ```

- 坏例子：在此层返回 `frontmatter.data`（裸 `any`）不过 schema；或把 `fetch` 的 secret header 同时暴露给 `NEXT_PUBLIC_*`——触碰 LOCK-1/LOCK-3。

出口条件：每个承接单元的数据读取路径落地；`null`/错误语义与设计一致；缓存策略与设计一致；类型层通过编译。

失败判定：`data-access` 返回未校验响应；用内存 mock 数组代替真实内容源/查询；secret 暴露到客户端可见前缀；静默吞错。

### Phase 3 — server-action（Server Actions / route handlers）

产物合同：
- 变更（mutation）用 Server Actions（`'use server'` 函数）或 route handlers（`app/api/.../route.ts` 的 `GET/POST/...`）；入参经 `domain-type`（zod）校验，返回结构化结果（成功/字段错误）供 `client-component` 消费。
- 变更后按详细设计执行 `revalidatePath` / `revalidateTag` / `redirect`，不自行更改重验语义；写操作的副作用（DB / 外部 API）走 `data-access`（LOCK-7 变更链 `server-action → data-access`），action 不直接散写裸 SQL/secret 拼接。
- 鉴权/会话校验在此层前置（取值见 `project-conventions.md`，如 NextAuth），未授权返回明确错误，不在 `client-component` 做权限判定真源。
- 好例子（生产级补充）：

  ```ts
  // app/posts/actions.ts
  'use server';
  import { CreateCommentSchema } from '@/types/comment';
  import { insertComment } from '@/lib/comments';   // data-access
  import { revalidatePath } from 'next/cache';
  export async function addComment(_: unknown, formData: FormData) {
    const parsed = CreateCommentSchema.safeParse(Object.fromEntries(formData));
    if (!parsed.success) return { ok: false, errors: parsed.error.flatten() };
    await insertComment(parsed.data);
    revalidatePath(`/posts/${parsed.data.slug}`);
    return { ok: true };
  }
  ```

- 坏例子：action 内直连 DB 写裸 SQL（绕过 `data-access`，违 LOCK-7）；或入参不校验直接落库（违 LOCK-1）。

出口条件：`BHV` 类变更行为每步骤定位到代码；入参校验 + 重验/重定向 + 错误返回与设计一致；类型层通过编译。

失败判定：action 入参不校验；绕过 `data-access` 直访数据源；在 `client-component` 充当权限真源；secret 拼进 action 响应。

### Phase 4 — server-component（渲染编排 + 数据获取编排，默认）

产物合同：
- 默认无 `'use client'`；可 `async` 直接 `await` `data-access` 取数，把数据 props 下传给 `ui-component`/`client-component`；编排多个 `data-access` 调用（必要时 `Promise.all` 并行）。
- 不持有交互状态（无 `useState`/`useEffect`）；需要交互处下沉到 `client-component`（LOCK-2）。
- 资源不存在调 `notFound()`；用 `<Suspense>` 包裹慢段配 fallback（LOCK-6）。
- 好例子（生产级补充）：

  ```tsx
  // server-component（非 route 段时可独立文件）
  import { getPostBySlug } from '@/lib/posts';
  import { Article } from '@/components/Article';      // ui-component
  import { LikeButton } from '@/components/LikeButton'; // client-component
  export async function PostView({ slug }: { slug: string }) {
    const post = await getPostBySlug(slug);
    if (!post) return null;                             // route 段负责 notFound
    return <><Article post={post} /><LikeButton slug={post.slug} /></>;
  }
  ```

- 坏例子：`server-component` 内 `useState`（编译/运行报错，违 LOCK-2）；或组件体内裸 `fetch(url, { headers: { Authorization: SECRET }})` 不走 `data-access`（违 LOCK-3/LOCK-7）。

出口条件：渲染编排每步骤有落点；无交互状态；取数走 `data-access`；类型层通过编译。

失败判定：`server-component` 含 hooks/事件；客户端取数渲染首屏；secret 散写在组件体；把整树拉成 client。

### Phase 5 — client-component（`'use client'` 交互）

产物合同：
- 文件首行 `'use client'`；持有交互状态（`useState`/`useReducer`）、事件 handler、浏览器 API、仅客户端第三方库；状态管理取值见 `project-conventions.md`（none / Context / Zustand）。
- 通过 props 接收 server 侧已取数据，**不在 client 重复发起私有数据获取**（LOCK-3）；调变更走 `server-action`（`useActionState`/`useFormStatus` 或直接调用 action 引用），不在 client 持 secret。
- 仅做必要交互，展示部分复用 `ui-component`（LOCK-7 交互链 `client-component → ui-component`）。
- 好例子（生产级补充）：

  ```tsx
  'use client';
  import { useState } from 'react';
  export function LikeButton({ slug }: { slug: string }) {
    const [liked, setLiked] = useState(false);
    return <button onClick={() => setLiked(v => !v)} aria-pressed={liked}>
      {liked ? '已赞' : '点赞'}
    </button>;
  }
  ```

- 坏例子：`client-component` 内 `process.env.CMS_SECRET` 拼请求（secret 进 bundle，违 LOCK-3）；或 `useEffect(() => fetch('/api/private-data'))` 客户端取首屏私有数据（违 LOCK-2/LOCK-3）。

出口条件：交互行为每步骤有落点；无私有取数/secret；变更走 action；类型层通过编译。

失败判定：`client-component` 持 secret/直连 DB；客户端取首屏私有数据；充当权限真源；`'use client'` 标在 route 段顶层把整树拉 client。

### Phase 6 — ui-component（纯展示可复用组件）

产物合同：
- 纯展示，输入靠 props，**无数据获取、无业务判定、无 secret、无 `'use client'`（除非自身需交互则归 `client-component`）**；样式走 CSS Modules / Tailwind（LOCK-5）。
- props 类型来自 `domain-type` 或本地展示 props 类型；可被 `server-component` / `client-component` 复用。
- 好例子（生产级补充）：

  ```tsx
  // components/Article.tsx
  import styles from './Article.module.css';
  import type { Post } from '@/types/post';
  export function Article({ post }: { post: Post }) {
    return <article className={styles.article}><h1>{post.title}</h1>...</article>;
  }
  ```

- 坏例子：`ui-component` 内 `await fetch(...)` 自行取数（违 LOCK-7）；或写全局 `<style jsx>{` article { ... } `}</style>`（示例 `theme.config.js` 示例实证）当生产样式（违 LOCK-5）。

出口条件：展示组件 props 契约落地；无取数/业务/secret；样式隔离；类型层通过编译。

失败判定：`ui-component` 取数/含业务分支/读 secret/写全局样式选择器。

### Phase 7 — route（App Router route 段 + metadata/SEO）

产物合同：
- 按约定落 `app/<segment>/{page,layout,loading,error,not-found}.tsx`；`page.tsx` 是 `server-component` 入口，装配下层；动态段配 `generateStaticParams()`（对齐示例静态 blog 形态）。
- metadata 标准化：静态 `export const metadata: Metadata`，动态 `export async function generateMetadata({ params })`；`params`/`searchParams` 经 `domain-type` 收窄（LOCK-1/LOCK-4）。
- `error.tsx` 为 `'use client'` 错误边界（接 `error`+`reset`）；`not-found.tsx` 对接 `data-access` 的 `null` → `notFound()`（LOCK-6）。
- 好例子（内容模型基线，生产级补充，对齐示例 `pages/posts/*` 与 `pages/tags/[tag].mdx` 示例实证）：

  ```tsx
  // app/posts/[slug]/page.tsx
  import { notFound } from 'next/navigation';
  import { getAllSlugs, getPostBySlug } from '@/lib/posts';
  import type { Metadata } from 'next';
  export async function generateStaticParams() {
    return (await getAllSlugs()).map(slug => ({ slug }));
  }
  export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
    const post = await getPostBySlug(params.slug);
    return { title: post?.title ?? 'Not found', description: post?.description };
  }
  export default async function Page({ params }: { params: { slug: string } }) {
    const post = await getPostBySlug(params.slug);
    if (!post) notFound();
    return <Article post={post} />;
  }
  ```

- 坏例子：动态详情页缺 `generateMetadata` 导致全站同标题（违 LOCK-4）；异步 route 段无 `error.tsx`（违 LOCK-6）；`layout.tsx` 顶层标 `'use client'` 把整站拉 client（违 LOCK-2）。

出口条件：route 段文件齐全；SEO/metadata 与设计一致；`generateStaticParams` 覆盖动态参数；`next build` 对该路由通过。

失败判定：缺 metadata/动态页同标题；缺 error/loading 边界；route 段顶层无差别 `'use client'`；`params` 不收窄。

### Phase 8 — 验证与符合性审查

见 §5（实现 Gate）。

---

## 5. 实现 Gate（tsc / next build / eslint / test + 证据）

实现 Gate 是"证据感，不是做完感"。每次实现闭环至少运行下列命令，并把命令与结果（命令 + 失败项/测试名级别，非"全部通过"）追加到 `verification-evidence.jsonl`；implementation review verdict 进入 `review-records/implementation-reviews.jsonl`。

### 5.1 必跑验证命令（既有命令优先）

| 类型 | 命令 | 通过判据 |
|------|------|---------|
| 类型检查 | `npx tsc --noEmit`（或 `package.json` 既有 `typecheck` 脚本） | 退出码 0，无类型错误（strict 下） |
| 生产构建 | `next build` | 退出码 0；route 段、`generateStaticParams`、RSC/client 边界编译通过 |
| lint | `npx eslint .`（lint 取值见 `project-conventions.md`，含 ESLint + Prettier） | 退出码 0，无新增告警；`next lint` 的 RSC/`'use client'` 相关规则不报错 |
| 测试 | `project-conventions.md` 指定命令（Vitest+RTL / Playwright） | 退出码 0；记录受影响用例名 |
| 启动/冒烟 | 最小真实启动（`next dev` / `next start`）+ 关键 route 渲染冒烟 | 关键页面 200、首屏由 server 渲染、交互可用 |
| Secret 残留 | 检查代码 / `.env.example` / fixture / `implement.md` / mutable evidence 无明文 secret，且无 `NEXT_PUBLIC_` 前缀承载 secret | 仅出现 env var 名 / 引用，无真实 key/AK/SK/token |

> 示例对照：`next.js/examples/blog` 的 `package.json` 仅有 `dev`/`build`/`start`，且 `build` 为 `node ./scripts/gen-rss.js && next build`（示例实证），**无 typecheck/eslint/test 脚本**（示例简化）。生产工程必须补齐 `typecheck`/`lint`/`test`（生产级补充），不照抄示例缺省。

`verification-evidence.jsonl` 要求：
- 每个切片对应"命令 + 结果"；类型/构建写到具体失败文件或"无错误"，测试写到用例名级别（如 `Article.test.tsx > renders title`）。
- 无法本地验证项（真机表现、外部 CMS/DB 联调、视觉回归）显式列出，标注留给哪个环节（Manual QA / 远程冒烟 / 视觉走查）。

### 5.2 Gate 结构判定（guru_gate.py 结构底线）

实现 Gate 结构检查（`guru_gate.py implement`）要求 `implement.md` 计划合同与 mutable evidence 齐全，且**切片挂 UNIT**：

- 计划节（含"计划"或"切片"）
- 执行节（含"执行"或"改动文件"）
- `verification-evidence.jsonl`（含"证据"或 analyze/test/build）
- 阻塞与偏差节（含"阻塞"或"偏差"）
- 若存在 `UNIT-<slug>`，trace 中必须出现 `UNIT-` 引用（裸编号 token，兼容未来双链包裹）。

下游引用一律写**裸编号 token**：行为写 `BHV-001`，设计单元写 `UNIT-post-detail-page`；不重排、不复用、删除留洞。

### 5.3 Gate 语义判定（实现审核口径）

`pass` / `fail` / `blocked` 三态，语义判定由实现审核（人工 Gate）逐条核：

- `pass`：所有承接单元切片为 `verified` 或明确 `skipped_with_reason`；无悬空 `in_progress`；无被当成完成交付的未验证 `implemented`；LOCK-1~7 全部满足；§5.1 必跑命令全部执行成功并有证据；合同八项无偏离；Secret 残留检查通过；doc_type 严格落在七类内。
- `fail`：存在合同未实现 / 实现偏离；无 plan 先行证据却已写生产代码；计划已 `blocked` 但代码绕过继续；`implemented` 未验证却交付为完成；触碰任一 LOCK 锁定项；明文 secret 写入代码/`.env.example`/fixture 或 `NEXT_PUBLIC_` 承载 secret；fake / 占位 / 内存 mock 生产路径；`any` 逃逸/`@ts-ignore` 抹平；把示例简化写法当生产合同照抄；新增测试超出 §6 allowlist；测试补写业务语义。
- `blocked`：详细设计缺失 / 冲突 / 需确认且已按 §7 记录并回退，未写临时代码绕过；或环境 / 凭据 / CMS/DB 基础设施缺失导致验证无法继续，保留恢复条件；或四类 `pending` doc_type 无 L2 且未取豁免。

逐条核查清单：
1. `implement.md` 存在且计划合同齐全，能恢复实现范围、计划状态、设计锚点；代码落点、阶段自检、验证状态、阻塞原因可由 `implement.md` 字段合同与 mutable evidence 合并恢复。
2. 每个切片挂 `UNIT-<slug>`，无幽灵引用（prd 无此 `BHV`）；doc_type 落在七类内。
3. 代码有 plan 先行证据；计划 `blocked` 但代码继续绕过 → 不得 `pass`。
4. 合同八项每项有代码锚点或 `blocked` 依据；执行流程每步骤有落点。
5. LOCK-1~7 全部满足（strict / server-first / 数据获取+secret 边界 / route+SEO / 样式隔离 / 错误边界 / 分层依赖）。
6. 数据获取/缓存/重验/错误/SEO/metadata 字段未弱化；render/client 边界与设计一致。
7. 生产路径无 fake / 占位 / 硬编码结果 / 内存 mock；无 `any` 逃逸。
8. 默认只跑既有验证命令；新增测试仅限 §6 allowlist 并回指切片与 `test_target`。
9. Secret 合同闭合：代码 / `.env.example` / fixture / trace / mutable evidence 无 secret value；`NEXT_PUBLIC_` 不承载 secret。
10. `client-component` 不持 secret/不直连 DB/不取首屏私有数据；`server-component` 无交互状态；`ui-component` 不取数；`data-access` 不被 client 误导入。

---

## 6. 实现期测试边界

- 默认只运行既有验证命令（§5.1），**不默认新增测试用例**，不采用 TDD / RED-GREEN，不先写测试再反向收敛生产代码。
- 新增测试用例不是详细设计承接来源，也不得牵引代码结构。
- allowlist（唯一允许新增的测试）：**无状态、幂等、输入输出明确的纯函数 / 纯展示 `ui-component`（无副作用、无取数）/ `domain-type` zod schema** 最小单测（Vitest + RTL，取值见 `project-conventions.md`）。例如可对 `tag.split(', ')` 解析函数、`PostFrontmatterSchema.parse` 成功/失败分支、`<Article post={...}/>` 渲染输出补最小单测；新增前必须已有 `implement.md` 计划或 slice packet 的 `test_target`，detail 确认后新增测试证据写入 `verification-evidence.jsonl`。
- 禁止：新增业务流程测试 / 集成测试 / e2e（Playwright）/ `data-access`-真实源测试 / `server-action`-DB 测试 / 外部系统 mock-fake 测试来定义业务语义；为测试通过新增 fake `data-access`/mock 数据/硬编码结果或放宽断言。
- 不适用场景：详细设计已附带独立测试计划 / 业务验收用例（如关键交互的 RTL 用例、关键流程的 Playwright e2e）时，按该计划执行属于既有验证，不受 allowlist 限制；detail 确认后的执行结果登记到 `verification-evidence.jsonl`。

---

## 7. 存量豁免口径

实现阶段触碰**存量代码**时按以下口径处理；豁免只针对存量违例，**不豁免** golden-path 锁定项（LOCK-1~7）与本次新增代码。

### 7.1 豁免对象与边界

- 豁免对象：仓库内已存在、不符合当前 golden-path / 合同但在本次切片范围**外**的代码（典型：旧的 Pages Router 残页、客户端取首屏数据的旧组件、未收窄的 `any`、全局样式污染、缺 metadata 的旧路由）。
- 不可豁免：LOCK-1~7 锁定项（任何代码都不可违反）；本次切片**新增 / 修改**的代码（必须符合全部合同与 LOCK）。
- 触碰即修 vs 记债：本次切片为完成目标**必须**改动到的存量违例 → 顺手修复并在 `implementation-evidence.jsonl` 记录；本次切片**不必**改动、改动会扩散影响面的存量违例 → 记债（列出位置 + 原因），不在本次扩大范围（外科手术式改动原则）。

### 7.2 处置记录（写入 mutable evidence）

每条触碰的存量违例记录：
- 违例位置（相对路径 + 符号/组件名）。
- 处置：`绕行` / `顺手修复` / `记债`。
- 理由：为什么本次不全量修（影响面 / 范围 / 风险，如旧 Pages Router 迁移工作量）。
- 若是 LOCK 锁定项被存量违反且落在本次必经路径 → 必须修复（不可记债豁免），因为 LOCK 不可豁免（例：本次必经的旧 `client-component` 持 secret，必须就地清除 secret）。

### 7.3 Gate 交互

- 存量记债项**不阻塞**本次实现 Gate（已显式记录、不在本次范围）。
- 范围外新增违例（本次切片引入的新违例）**阻塞** Gate（`fail`）。
- 缺陷只能回上游修：审核发现结构性缺陷（归属错、doc_type 错、合同越界）回到拥有该决策的阶段修订，禁止下游补造。

---

## 8. `implement.md`（trace）主文档合同与 mutable evidence 边界

`implement.md` 是 detail Gate 的 digest-bearing planning/trace contract。建议路径：目标仓库 `docs/design/<feature>/implement.md`（或 `docs/implementation/<module_slug>/implement.md`）。它在 detail 确认前完成并进入 digest；detail 确认后不得作为执行证据默认写入点。实现阶段的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`。若必须修改 `implement.md`，必须回退 detail Gate 并重新 review/confirm。

### 8.1 必含四节（计划合同结构底线）

#### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 切片 | 每片承接的设计单元编号（`UNIT-<slug>`，幽灵引用被 Gate 拦截）+ doc_type（七类之一）/ 文件范围 / 完成信号 / 验证方式；每片小到可独立 review |
| 执行顺序 | 按依赖排序（§3 自下而上：domain-type → data-access → server-action → server-component → client-component → ui-component → route），从最小切片开始 |
| 风险点 | 预判高风险改动（server/client 边界变更、缓存/重验策略、动态 SEO、旧 Pages Router 迁移、secret 边界），逐条写验证手段 |

#### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个切片完成时记录下列字段：
- 实际改动文件清单（相对路径）。
- 与计划的偏差（改了计划外文件 / 没改计划内文件 → 必须写原因）。
- 代码生成 / 内容源/迁移执行记录（跑了哪个脚本 / migration / codegen）。

#### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

| 类型 | 要求 |
|------|------|
| 类型 | `tsc --noEmit` 结果（通过 / 失败文件 + 处理） |
| 构建 | `next build` 结果（含 RSC/client 边界、`generateStaticParams`、route 段编译） |
| lint | `eslint .` / `next lint` 结果 |
| 测试 | 每个切片对应测试命令 + 结果（用例名级别，非"通过"）；新增测试清单（限 §6 allowlist） |
| 启动 | 最小启动 + 关键 route 渲染冒烟（首屏 server 渲染、交互可用） |
| Secret | Secret 残留检查结果（含 `NEXT_PUBLIC_` 审查） |
| 未验证项 | 无法本地验证的（真机、外部 CMS/DB 联调、视觉回归）→ 显式列出 + 留给哪个环节 |

#### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- 上游缺陷：详细设计合同错 / 漏 / doc_type 错 → 记录后**回退详细阶段修订**，不就地改设计（`implementation-evidence.jsonl` 留回退记录与恢复条件）。
- 存量违例触碰：列出位置 + 处置（绕行 / 顺手修复 / 记债，见 §7）。
- 未决决策：实现中冒出的新决策点（如新缓存策略、新状态管理引入）→ 不私自拍板，记录并升级给人工 Gate。

### 8.2 切片状态机

- 固定枚举：`pending` / `in_progress` / `implemented` / `verified` / `blocked` / `skipped_with_reason`。
- 同一时间最多一个切片 `in_progress`；detail 确认后该状态写入 `implementation-evidence.jsonl`。
- `implemented` 只表示代码落地；未通过 `checkpoint` 与 `validation_commands` 的切片不得 `verified`。
- `blocked` 必须写明恢复条件与回指（详细设计回修 / L2 豁免待批 / 凭据 / 基础设施）。
- `skipped_with_reason` 必须说明设计范围 / 用户范围为何不需要；不得用来隐藏未实现的 required 切片。

### 8.3 反模式

- trace 在 PR 前一次性补写（失去过程证据意义）。
- mutable evidence 只写"全部通过"（无命令、无失败文件/测试名）。
- 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
- 把 `implement.md` 当设计补写位置；detail 确认后又把它当执行证据写入点。

---

## 9. 反模式总表（Gate `fail`）

| # | 反模式 | 违反 |
|---|--------|------|
| 1 | `tsconfig` 非 strict / `any` 逃逸业务边界 / `@ts-ignore` 抹平 / 外部输入不过 zod 收窄 | LOCK-1 |
| 2 | 整页/`layout` 顶层无差别 `'use client'`，把子树拉成 client / `server-component` 含 hooks/事件 | LOCK-2 |
| 3 | `client-component`/`ui-component` 直读 secret、直连 DB、客户端取首屏私有数据 / secret 走 `NEXT_PUBLIC_` | LOCK-3 |
| 4 | route 段缺 metadata / 动态页同标题 / `params` 不收窄 / 缺 `generateStaticParams` | LOCK-4 |
| 5 | 组件内全局样式选择器 / `<style jsx>` 当生产方案 / `globals.css` 写组件级规则 | LOCK-5 |
| 6 | 异步 route 段缺 `error.tsx`/`loading` / `catch {}` 静默吞错 / 不存在不走 `notFound()` | LOCK-6 |
| 7 | `data-access` 导入 `route`/`server-component` / `ui-component` 取数 / `server-action` 绕 `data-access` 直访数据源 | LOCK-7 |
| 8 | 详细设计有执行流程步骤，代码只写"渲染页面 / 处理交互 / 调用接口"式大组件 | 合同八项之 4/5 |
| 9 | 用内存 mock 数组 / fake `data-access` 替代真实内容源/查询；为编译/测试新增占位结果 | 承接合同 / §6 |
| 10 | 默认 TDD / 先写测试牵引实现；新增业务流程 / 集成 / e2e / mock-fake 测试定义业务语义 | §6 |
| 11 | 把 API key / AK·SK / token / password 写进代码 / `.env.example` / fixture / 测试 / 日志 / `implement.md` | Secret 合同 |
| 12 | 把 `next.js/examples/blog` 的简化写法（Pages Router / `gray-matter` 裸 `any` / `<style jsx>` / 非 strict / 手动字体 preload）当生产合同照抄 | §0.0 示例 vs 生产区分 |
| 13 | doc_type 改名 / 增减 / 换数（如照抄 flutter controller / Go handler 命名）或越 owner 层归属 | §0.1 / LOCK-7 |
| 14 | 用"存量豁免"绕过 LOCK 锁定项或本次新增代码的合同 | §7 |
| 15 | trace 在 PR 前补写、mutable evidence 只写"全部通过"、切片不挂 `UNIT-<slug>`、四类 `pending` doc_type 无 L2 又未取豁免 | §8 / §5.2 |
