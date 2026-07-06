# 黄金路径：Guru H5 / Next.js Web 开发（通用方法 SSOT · v1）

> **这是什么**：H5 平台（Next.js App Router + React + TypeScript strict）通用开发方法的单一可信源（SSOT）。本文只写**类别级方法**（任何 Next.js H5 页面怎么做对）与**团队栈级 canonical**（Guru 团队 Next.js 栈统一约定）。**项目级取值一律不出现在本文**——凡标注 `[SLOT-xx]` 处，取值见目标仓库 `.trellis/spec/conventions/project-conventions.md`（模板见配置包 `conventions/project-conventions.template.md`）。
> **派生关系**：脚手架模板、ESLint/`guru-lints-next` 规则、各 agent 适配层（概要/详细/实现三件套 Skill）**全部从本文派生**，不各写一份（对标 flutter ADR-0002）。改约定先改这里。
> **基线与实证边界**：基线为 **Next.js App Router 生产形态**。参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog`（以下简称 blog 示例）是 **Pages Router + Nextra + MDX + gray-matter** 的轻量 blog starter（故意简化）。本文以 App Router 生产最佳实践为准，把 blog 示例作为**内容模型基线**引用。全文凡标注 **【blog 示例实证】** 为该 starter 真实可见的写法证据；标注 **【App Router 生产级补充】** 为生产形态的权威要求（blog 示例未演示或采用了过时写法）。两者冲突时**以生产级补充为准**。
> **核心思想**：一个需求 = 它真正碰到的那几类详细设计单元（doc_type）的 canonical 迷你路径之组合。整页 feature 只是 "route + server-component + 下层数据链 + 必要的 client-component/ui-component" 的全栈组合；非 UI 需求就是 "只跑下层"（如只接一个数据源 = 只跑 data-access）。

---

## 0. doc_type 权威七类（全程唯一，禁止改名 / 增减 / 换数）

H5 详细设计单元的 `doc_type` 取值**只有以下七类**，下游（详细合同、实现 trace、门禁、脚手架）一律裸 token 引用，禁止照抄 flutter 的 `controller/usecase/repository-datasource` 或 Go 的类型名：

| # | doc_type | 一句话职责 | owner 链位置 | L2 状态 |
|---|----------|-----------|------------|:---:|
| 1 | `server-component` | RSC 服务端组件：渲染编排 + 数据获取（默认形态） | route 之下、data-access 之上 | full（v1 提供 L2） |
| 2 | `client-component` | `'use client'` 交互组件：状态 / 事件 / hooks | 交互链顶层 | full（v1 提供 L2） |
| 3 | `data-access` | 数据访问层：fetch 封装 / 内容源(MDX/CMS) / ORM 查询 | server 链底层 | full（v1 提供 L2） |
| 4 | `route` | App Router route 段：`page/layout/loading/error.tsx` + metadata/SEO | server 链顶层 | pending |
| 5 | `ui-component` | 展示型可复用组件：纯展示、无数据获取、无业务 | 交互链底层 | pending |
| 6 | `domain-type` | TS 类型 / zod schema / 领域模型 | 全链最底层（被依赖） | pending |
| 7 | `server-action` | Server Actions / route handlers：变更 / API endpoint | 依赖 data-access | pending |

**L2 文件（render/interactive/data 三元组，对应 flutter 的 controller/usecase/repository-datasource）**，v1 已提供，装载路径 `.trellis/spec/harness/detail/`：
- `detail-type-server-component.md`（render：渲染 + 数据获取编排）
- `detail-type-client-component.md`（interactive：交互 / 状态）
- `detail-type-data-access.md`（data：数据访问）

**pending 四类**（`route` / `ui-component` / `domain-type` / `server-action`）：暂无 L2 详细文件，按本文 §L1 合同八问（§详细合同）展开即可；凡 Gate 要求 "full 链须 L2" 时，这四类按 `l2_status: pending` **豁免**，但仍须在详细文档里回答完八问。

---

## 1. 入口决策树：这个需求碰哪几类 doc_type？

```
需求进来
 ├─ 要给用户看的新页面 / 新路由?
 │     → 跑 route(§route) + server-component(§server-component) + 它需要的下层
 │       （需交互再加 client-component；需复用展示件再加 ui-component）
 ├─ 只加一个交互组件（折叠/表单/筛选/弹窗，无新路由)?
 │     → 跑 client-component(§client-component) + 它消费的 ui-component
 ├─ 只接一个数据源 / 改内容获取（MDX/CMS/ORM 查询)?
 │     → 跑 data-access(§data-access)，再交给 server-component 消费
 ├─ 只做一次变更 / 写一个 API endpoint(提交表单/写库/调第三方)?
 │     → 跑 server-action(§server-action)，下接 data-access
 ├─ 只定义/改领域类型 / zod schema?
 │     → 只跑 domain-type(§domain-type)
 ├─ 只加/改一个纯展示组件（卡片/徽章/排版)?
 │     → 只跑 ui-component(§ui-component)
 └─ 只改 SEO/metadata/布局壳/错误页?
       → 只跑 route(§route) 对应文件段
跑完任意类都要过 §构建生成 + §自检。
```

**判别口诀**：先问"有没有用户交互（状态/事件/浏览器 API）"——没有就留在 `server-component`（默认）；有交互才下沉到最小 `client-component`。再问"要不要私有数据/secret"——要就只能在 `server-component`/`data-access`/`server-action`，**绝不进 `client-component`**。

---

## 2. canonical 总则（跨类，所有迷你路径都遵守）

### 2.1 分层依赖律（最重要，归属硬基准，违反 fail）

依赖方向**只能从上往下**，严禁反向或同层乱跳。两条链：

```
【服务端渲染链】
route                  (page/layout/loading/error)
   ↓ 只依赖
server-component       (渲染编排 + 数据获取)
   ↓ 只依赖
data-access            (fetch/内容源/ORM 查询)
   ↓ 只依赖
domain-type            (TS 类型 / zod schema)

【交互链】
client-component       ('use client' 状态/事件)
   ↓ 只依赖
ui-component           (纯展示)

【变更链】
server-action          (Server Action / route handler)
   ↓ 只依赖
data-access → domain-type
```

**owner 层归属硬基准**：`route → server-component → data-access → domain-type`（服务端链）；`client-component → ui-component`（交互链）；`server-action → data-access`。

**硬禁止（ESLint import 边界 + review 查）**：
- ❌ `data-access` 反向依赖 `server-component` / `route`（反向依赖）。
- ❌ `route` 跳过 `server-component` 直接 import `data-access`（跳层；route 段只负责段约定与编排，数据获取下放 server-component；简单页可由 page.tsx 自身充当 server-component，此时它**就是** server-component，不算跳层）。
- ❌ `ui-component` 依赖 `client-component`（交互链反向）或 import 任何 `data-access`（展示件不取数）。
- ❌ `server-action` 反被 `data-access` 依赖（变更链反向）。
- ❌ `domain-type` 依赖以上任何一类（最底层不得反向）。
- ✅ `server-component` → `client-component`（通过 props 传序列化数据，允许且常见）；`client-component` 不得反向 import `server-component`（会把 server 代码拖进 client bundle）。

### 2.2 server-client 边界（H5 平台特有，最高优先级硬规则）

- **server-first 默认**：所有组件默认是 `server-component`（RSC），**不写** `'use client'`。
- **`'use client'` 最小化**：仅在真正需要 **状态(useState/useReducer)、生命周期/副作用(useEffect)、事件处理(onClick/onChange)、浏览器 API(window/localStorage)、第三方仅客户端库** 时，才把**最小的叶子组件**标记 `'use client'`。禁止把整页/大块标 client。
- **边界下推（push client down）**：交互只发生在某个小部件时，抽出该小部件为 `client-component`，让父级保持 `server-component`。server 组件可把 client 组件当 children 传入。
- **私有数据获取 / secret 只在 server 侧**：`process.env` 私有变量、DB 连接、私钥、带鉴权 token 的 fetch，**只允许**出现在 `server-component` / `data-access` / `server-action`。**严禁** `client-component` 直接取私有数据或读 server-only secret（`NEXT_PUBLIC_` 前缀变量除外，且仅限非敏感值）。可用 `import 'server-only'` 给 data-access 加保险栓。
- **序列化边界**：从 server 传给 client 的 props 必须是可序列化的（不能传函数、Date 以外的类实例、Symbol）；需要在 client 用的复杂对象先在 server 侧转成 plain object（用 domain-type 的 schema 校验/转换）。

### 2.3 数据获取（data fetching）canonical

- **取数位置**：数据获取归 `server-component`（直接 `async` 组件内 `await`）或下沉到 `data-access` 封装；**禁止** `client-component` 用 `useEffect + fetch` 取首屏私有数据（如确需客户端取公开数据，走明确标注的 client data hook，且只取 `NEXT_PUBLIC_`/公开 endpoint）。
- **缓存与 revalidate 显式化**：每个 fetch 必须**显式**声明缓存语义——`fetch(url, { cache: 'force-cache' | 'no-store' })` 或 `{ next: { revalidate: <秒> } }`；禁止依赖隐式默认。需要按需失效用 `revalidateTag` / `revalidatePath`（在 server-action 内调用）。
- **不在循环里串行 await**：并行取数用 `Promise.all`；避免请求瀑布（waterfall）。
- **错误与空态**：data-access 出错**向上抛**（交由 `error.tsx` 边界或调用方处理），不在 data-access 里静默吞错返回空数组冒充成功（通用硬规则）。
- 【blog 示例实证】blog 用 **构建期文件系统读取 + gray-matter** 解析 MDX frontmatter 作为内容源（见 `scripts/gen-rss.js`：`fs.readdir(pages/posts)` + `matter(content)` 取 `frontmatter.data.title/date/tag/...`）。这是"内容源 = 本地 MDX"的最简形态。
- 【App Router 生产级补充】生产形态把"读 MDX/CMS/ORM"封装进 `data-access` 模块（如 `lib/posts.ts` 暴露 `getAllPosts()/getPostBySlug()`），由 `server-component` 调用并显式声明缓存；CMS/DB 场景在此层做鉴权与字段裁剪，绝不把原始凭证暴露给下游。

### 2.4 样式隔离（禁全局污染）

- 样式方案按 `[SLOT-04]`（Tailwind / CSS Modules），单项目内统一。
- **禁止全局污染**：禁止裸写全局 `*.css` 选择器影响他组件；全局样式仅限 `app/globals.css` 的 reset/变量/字体声明，组件级样式一律走 **CSS Modules(`*.module.css`)** 或 **Tailwind utility class**。
- 【blog 示例实证】blog 用 Nextra 主题 CSS + `styles/main.css` + `<style jsx>`（见 `theme.config.js` 的 `<style jsx>{...}`）。`<style jsx>` 是 Pages Router 时代写法。
- 【App Router 生产级补充】App Router 生产**不用** `styled-jsx` 全局/内联样式作为主方案；用 Tailwind 或 CSS Modules，组件局部作用域。`error.tsx` 等也遵守同一隔离规则。

### 2.5 命名 / 目录 / route 段约定

- **route 段文件名固定**（App Router 约定，不可改名）：`page.tsx`(页面) / `layout.tsx`(布局壳) / `loading.tsx`(Suspense fallback) / `error.tsx`(错误边界，必须 `'use client'`) / `not-found.tsx` / `route.ts`(route handler)。
- **目录即路由**：`app/` 下目录段映射 URL；动态段用 `[slug]`，分组用 `(group)`，私有目录用 `_folder`（不映射路由，放内部实现）。
- **co-location**：组件/工具可与 route 段同目录共存，只有上述保留文件名才参与路由。
- 新页面进 `app/` 的目录分界、组件库存放目录、data-access 模块目录按 `[SLOT-13]`（路由模式：本文以 App Router 为准）/ `[SLOT-02]`，单项目内唯一。
- 【blog 示例实证】blog 是 **Pages Router**（`pages/index.mdx`、`pages/posts/*.md`、`pages/tags/[tag].mdx`、`pages/_app.tsx`、`pages/_document.tsx`），文件即路由，`[tag].mdx` 是动态路由。
- 【App Router 生产级补充】生产以 `app/` 目录为准；`_app.tsx`/`_document.tsx`(Pages) 的职责由 `app/layout.tsx`(根布局，含 `<html><body>`) 承接；`<Head>` 标签由 route 的 `metadata` 导出/`generateMetadata` 承接（见 §2.6）。

### 2.6 metadata / SEO 标准化

- **App Router metadata 是权威 SEO 入口**：静态用 `export const metadata: Metadata = {...}`；依赖动态参数用 `export async function generateMetadata({ params }): Promise<Metadata>`。覆盖 `title` / `description` / `openGraph` / `twitter` / `robots` / `alternates`（含 RSS）。
- 【blog 示例实证】blog 用 Pages Router 手写 `<Head>` + 一堆 `<meta property="og:...">`（见 `pages/_document.tsx`：`og:title/og:description/og:image` + `twitter:card=summary_large_image`），RSS 用 `<link rel="alternate" type="application/rss+xml">`（见 `pages/_app.tsx`）。
- 【App Router 生产级补充】上述手写 `<meta>` 全部由 `metadata`/`generateMetadata` 对象生成，**不手写 `<head>` 标签**；OG/Twitter 卡片走 `metadata.openGraph`/`metadata.twitter`，RSS 走 `metadata.alternates.types`。

### 2.7 TypeScript strict（团队栈级 canonical，硬规则）

- `tsconfig.json` 必须 `"strict": true`。**禁止** `any`（用 `unknown` + 收窄）、禁止隐式 any、禁止 `@ts-ignore`（确需用 `@ts-expect-error` 并注释理由）。
- 跨 server/client 边界传递的数据用 `domain-type`（type / interface / zod schema）显式建模并校验。
- 【blog 示例实证】blog 的 `tsconfig.json` 是 **`"strict": false`、`target: es5`、`typescript ^4.7.4`**——这是 starter 的故意简化，**不作为生产基线**。
- 【App Router 生产级补充】生产基线 `"strict": true`，`target` ≥ `es2017`，TS ≥ 5.x。新仓库脚手架直接钉死 strict。

---

## 3. 写作顺序（自底向上，对标 flutter）

```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```

底层先稳定（类型/取数），再编排（server 渲染/变更），最后接路由壳与交互件。非全栈需求只跑入口决策树命中的子集。

---

## 4. 各类迷你路径（canonical 正向生成动作 + 边界）

> 下列代码块为参数化骨架；`[SLOT-xx]` 取值见目标仓库 project-conventions。脚手架按入口决策树条件组合这些块。

### §domain-type 迷你路径（`doc_type: domain-type`）

正向动作：在 `[SLOT-02]` 钉死的类型目录新建/扩展类型与校验。
```ts
// types/post.ts  —— 领域类型 + zod schema（运行时校验用 [SLOT-06] 选定方案）
import { z } from 'zod';

export const PostFrontmatterSchema = z.object({
  title: z.string(),
  date: z.string(),                 // ISO 字符串，跨 server→client 可序列化
  description: z.string().optional(),
  tag: z.string(),
  author: z.string(),
});
export type PostFrontmatter = z.infer<typeof PostFrontmatterSchema>;
export type Post = PostFrontmatter & { slug: string; content: string };
```
边界：纯类型/纯校验，**零副作用、零 I/O、零 React**。是全链被依赖的叶子，**不 import 任何其他六类**。跨边界对象在此定义"可序列化"形态。

### §data-access 迷你路径（`doc_type: data-access`）

正向动作：把"读 MDX/CMS/ORM/外部 API"封装成纯数据函数，对外暴露按 domain-type 收敛的结果。
```ts
// lib/posts.ts  —— data-access（server-only）
import 'server-only';                 // 保险栓：误入 client bundle 直接报错
import { PostFrontmatterSchema, type Post } from '@/types/post';

export async function getAllPosts(): Promise<Post[]> {
  // 内容源按 [SLOT-05]：本地 MDX / CMS / ORM
  const raw = await readContentSource();          // fs/CMS SDK/ORM 查询
  return raw.map((r) => {
    const fm = PostFrontmatterSchema.parse(r.data); // 校验，失败上抛
    return { ...fm, slug: r.slug, content: r.content };
  });
  // ❌ 不在此处 catch 后返回 [] 冒充成功；错误向上抛给 error.tsx
}
```
边界：可读私有 env/凭证（server-only）；**显式缓存语义**（`fetch` 带 `cache`/`next.revalidate`）；出错上抛；返回值必须可序列化、按 domain-type 收敛。**禁止** import `server-component`/`route`（反向）；**禁止**被 `client-component`/`ui-component` import。
- 【blog 示例实证】等价逻辑散落在 `scripts/gen-rss.js`（`fs.readdir` + `gray-matter`），生产应抽成此模块供页面与脚本共用。

### §server-action 迷你路径（`doc_type: server-action`）

正向动作：变更/写操作或 API endpoint。两种形态：
```ts
// app/actions/subscribe.ts  —— Server Action（表单提交/变更）
'use server';
import { revalidatePath } from 'next/cache';
import { SubscribeSchema } from '@/types/subscribe';
import { saveSubscriber } from '@/lib/subscribers';   // data-access

export async function subscribe(formData: FormData) {
  const parsed = SubscribeSchema.parse(Object.fromEntries(formData)); // 入参校验
  await saveSubscriber(parsed);          // ✅ 经 data-access，不在此直连 DB driver
  revalidatePath('/');                   // 按需失效缓存
}
```
```ts
// app/api/feed.xml/route.ts  —— Route Handler（API endpoint，如 RSS/webhook）
import { getAllPosts } from '@/lib/posts';
export async function GET() {
  const posts = await getAllPosts();
  return new Response(buildRss(posts), { headers: { 'Content-Type': 'application/xml' } });
}
```
边界：`'use server'` 内必校验入参（zod），鉴权在此把关；变更后用 `revalidateTag/revalidatePath` 失效缓存；**只依赖 data-access + domain-type**，不直连 DB driver/不重复写 data-access 逻辑。**禁止**被 data-access 反向依赖。

### §server-component 迷你路径（`doc_type: server-component`，默认形态，render 三元组之一）

正向动作：`async` 组件内编排取数 + 渲染；把交互下推给 client-component。
```tsx
// app/posts/page.tsx 既是 route 段也可充当 server-component（简单页）
import { getAllPosts } from '@/lib/posts';     // ✅ 调 data-access 取数
import { PostList } from '@/components/post-list';   // ui-component（纯展示）

export default async function PostsPage() {     // ✅ async server component，无 'use client'
  const posts = await getAllPosts();            // ✅ server 侧取数，可读私有源
  return <PostList posts={posts} />;            // 传可序列化 props 给下游
}
```
边界：默认无 `'use client'`；可读私有数据/secret；**只依赖 data-access(+domain-type)**，不依赖 client-component 的内部实现（可把 client-component 当子组件渲染并传 props）；不在此写 `useState/useEffect`（那是 client-component 的事）。

### §client-component 迷你路径（`doc_type: client-component`，interactive 三元组之一）

正向动作：把"需要状态/事件/浏览器 API"的最小叶子标 `'use client'`。
```tsx
// components/tag-filter.tsx
'use client';                                   // ✅ 只在真需交互的叶子
import { useState } from 'react';
import type { Post } from '@/types/post';       // domain-type
import { PostCard } from '@/components/post-card';  // ui-component 纯展示

export function TagFilter({ posts }: { posts: Post[] }) {  // 数据由 server 经 props 注入
  const [tag, setTag] = useState<string | null>(null);
  const shown = tag ? posts.filter((p) => p.tag === tag) : posts;
  return (
    <>
      {/* 交互控件 */}
      {shown.map((p) => <PostCard key={p.slug} post={p} />)}
    </>
  );
}
```
边界：`'use client'` 置文件首行；**禁止**在此取私有数据/读 server secret（数据走 props 或公开 client hook）；**只依赖 ui-component(+domain-type)**，不 import server-component/data-access（会污染 client bundle）；props 必须可序列化。
- 【blog 示例实证】`pages/tags/[tag].mdx` 用 `useRouter().query` 取 `tag` 是客户端 hook 思路；生产里这类交互件标 `'use client'` 即为本类。

### §ui-component 迷你路径（`doc_type: ui-component`）

正向动作：纯展示、可复用、无数据获取、无业务。
```tsx
// components/post-card.tsx  —— 纯展示（不标 'use client'，可被 server/client 复用）
import type { Post } from '@/types/post';
export function PostCard({ post }: { post: Post }) {
  return (
    <article className="rounded-lg p-4">      {/* 样式按 [SLOT-04]，禁全局污染 */}
      <h3>{post.title}</h3>
      <time>{post.date}</time>
    </article>
  );
}
```
边界：**零数据获取、零业务逻辑、零状态**（如需局部交互态，它就该升级为 client-component 或拆分）；**不 import** data-access；可被 server-component 与 client-component 同时复用，因此默认不标 `'use client'`。
- 【blog 示例实证】blog 用 Nextra 主题组件承担展示，未单列 ui-component；生产里卡片/徽章/排版等抽为本类。

### §route 迷你路径（`doc_type: route`，server 链顶层）

正向动作：建立 route 段约定文件 + metadata/SEO。
```tsx
// app/posts/layout.tsx —— 布局壳（持久，不随子页重渲）
export default function PostsLayout({ children }: { children: React.ReactNode }) {
  return <section>{children}</section>;
}

// app/posts/loading.tsx —— Suspense fallback
export default function Loading() { return <p>加载中…</p>; }

// app/posts/error.tsx —— 错误边界（必须 'use client'）
'use client';
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return <button onClick={reset}>重试</button>;
}

// app/posts/[slug]/page.tsx —— 动态段 + metadata/SEO
import type { Metadata } from 'next';
import { getPostBySlug } from '@/lib/posts';   // 编排下放，经 data-access
export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const post = await getPostBySlug(params.slug);
  return { title: post.title, description: post.description,
           openGraph: { title: post.title }, alternates: { types: { 'application/rss+xml': '/feed.xml' } } };
}
export default async function PostPage({ params }: { params: { slug: string } }) {
  const post = await getPostBySlug(params.slug);   // 简单页 page 自身即 server-component
  return <article>{post.content}</article>;
}
```
边界：保留文件名不可改名；`error.tsx` 必 `'use client'`；SEO 走 `metadata`/`generateMetadata` 不手写 `<head>`；数据编排下放给 server-component（简单页 page.tsx 自身充当）。**禁止**在 route 段跳过 server-component 直接堆复杂取数逻辑（抽 data-access）。
- 【App Router 生产级补充】blog 示例无 `app/` 目录与上述五文件；根布局 `app/layout.tsx` 须含 `<html lang><body>` 并声明全局字体/RSS link（承接 blog `_document.tsx`/`_app.tsx` 职责）。

---

## 5. 构建生成（顺序固定，脚本名按 `[SLOT-08]`）

```
依赖安装（仅当 package.json 变动）：npm ci / pnpm i
内容/派生产物生成（仅当有内容源脚本，如 RSS/sitemap）：node scripts/gen-rss.js
类型检查 + 构建：next build   （生产构建顺带类型校验与静态分析）
```
- 【blog 示例实证】blog `package.json` 的 `build` 脚本是 **`node ./scripts/gen-rss.js && next build`**——"先生成派生内容（RSS）再构建"的固定顺序，本文据此钉死。`dev`=`next`、`start`=`next start`。
- 【App Router 生产级补充】生产可在 build 链补 `next build` 前的 `tsc --noEmit`（strict 下双保险）、`sitemap` 生成；脚本具体命名/编排按 `[SLOT-08]`。

---

## 6. 自检（任何类跑完都要过）

```bash
npx tsc --noEmit            # TS strict 类型门禁
npm run lint                # ESLint + import 边界规则（guru-lints-next）
npx next build              # 生产构建：RSC 边界/序列化/'use client' 误用会在此暴露
# 测试按 [SLOT-07]：vitest run / playwright test
```
- 【blog 示例实证】blog 无 lint/test 脚本（starter 简化）。生产仓库必须补齐 lint 与构建自检。

---

## 7. 禁止清单（汇总，门禁拦）

**通用硬禁止（任何 H5 项目不可豁免）**：
- ❌ 在 `client-component` 直接获取私有数据 / 读 server-only secret / 用私有 env（§2.2）。
- ❌ `'use client'` 标在整页或大块上（应下推到最小交互叶子）（§2.2）。
- ❌ `client-component` import `server-component` / `data-access`（污染 client bundle）（§2.1）。
- ❌ `ui-component` 取数 / 含业务逻辑 / 依赖 client-component（§ui-component / §2.1）。
- ❌ `data-access` 静默吞错返回空值冒充成功（§2.3）。
- ❌ fetch 不显式声明缓存/`revalidate`，依赖隐式默认（§2.3）。
- ❌ 跨 server→client 传不可序列化 props（函数/类实例/Symbol）（§2.2）。
- ❌ 手写 `<head>`/`<meta>` 做 SEO，绕过 `metadata`/`generateMetadata`（§2.6）。
- ❌ 改 route 保留文件名 / `error.tsx` 不标 `'use client'`（§2.5 / §route）。
- ❌ 全局 CSS 污染他组件（组件样式必须 Modules/Tailwind 局部）（§2.4）。
- ❌ `tsconfig` 非 strict / 使用 `any` / `@ts-ignore`（§2.7）。
- ❌ `route` 跳过 server-component 直堆复杂取数；`server-action` 直连 DB driver 绕过 data-access（§2.1 / §server-action）。
- ❌ `domain-type` 反向依赖任何其他六类 / 带 I/O 副作用（§domain-type）。

**按项目约定执行的禁止（取值见 project-conventions）**：
- ❌ 违反 `[SLOT-04]` 样式方案（如该项目定 Tailwind 则新代码不得引入 CSS Modules 混用，反之亦然）。
- ❌ 违反 `[SLOT-06]` 校验方案 / `[SLOT-03]` 状态管理选型（如定 none 则不得擅自引入 Zustand）。
- ❌ 组件 / data-access / 类型落在 `[SLOT-02]` 钉死目录之外。
- ❌ 违反 `[SLOT-13]` 路由模式（本配置包以 App Router 为准；项目若历史用 Pages 须在 conventions 写明分界）。

---

## 8. 门禁映射（三层各管什么）

| 规则 | 脚手架 | guru-lints-next(ESLint) | review |
|------|:---:|:---:|:---:|
| §2.1 分层依赖律（import 边界） | | ✅(import 方向) | ✅ |
| §2.2 server-client 边界 / secret 隔离 | ✅ | ✅(`'use client'` + server-only) | ✅ |
| §2.3 数据获取 / 缓存显式 / 不吞错 | | ✅(no-floating + 自定义) | ✅ |
| §2.4 样式隔离（禁全局污染） | ✅ | ✅(读 `[SLOT-04]`) | |
| §2.5 命名/目录/route 段约定 | ✅ | ✅(保留文件名) | |
| §2.6 metadata/SEO 标准化 | ✅ | | ✅ |
| §2.7 TS strict / 禁 any | ✅(tsconfig) | ✅(tsc + eslint) | |
| §7 禁止清单 | ✅ | ✅ | ✅ |
| §5/§6 构建/自检 | | | hooks 回灌 |

---

## 9. Gate 兼容映射（与配置包流程对齐）

> 装载路径统一用 `.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md`（即本文）。下游引用本文编号/token 一律裸 token（如 `server-component`、`BHV-001`、`UNIT-post-list-page`）。

### 9.1 需求五要素（概要阶段必答）
1. **触碰哪几类 doc_type**（入口决策树命中集合）；2. **owner 类归属**（§2.1 链上哪一层为主）；3. **server/client 边界判定**（是否需要 `'use client'`、私有数据在哪侧）；4. **数据来源与缓存语义**（内容源 `[SLOT-05]` + revalidate 策略）；5. **SEO/路由影响**（是否新增 route 段 / metadata 变更）。

### 9.2 概要归属表 + 承接索引
- **归属表**：每个改动单元列 `UNIT-<slug>` → `doc_type`（七类之一）→ owner 链位置 → 依赖的下层单元。
- **承接索引**：每个 `BHV-NNN`（行为编号）→ 落在哪些 `UNIT-<slug>` → 由哪类详细文档承接（L2 三类有 `detail-type-*`；pending 四类走 L1 八问 + `l2_status: pending` 豁免）。

### 9.3 详细合同八问（每个 UNIT 详细文档必答）
1. **doc_type 是什么**（七类裸 token）与 owner 链位置；2. **正向生成动作**（建哪些文件、写什么，引 §对应迷你路径）；3. **依赖边界**（依赖哪些下层 token、禁止依赖哪些，对照 §2.1）；4. **server/client 归属**（是否 `'use client'`、secret 是否涉及）；5. **产物合同**（导出签名 / props 形态 / 返回类型，按 domain-type）；6. **缓存/数据语义**（仅 data-access/server-component/server-action 必答）或 **交互/状态语义**（仅 client-component 必答）；7. **可验证信号**（自检命令 + 期望：tsc 通过、lint 无边界违规、build 无 RSC 序列化报错、对应测试）；8. **好/坏例子 + 不适用场景**（引本文示例；标明何时**不**该用本类）。

### 9.4 实现 trace 计划合同与 mutable evidence（实现阶段必填）
1. **变更文件清单**（绝对/仓内路径 → 对应 `UNIT-<slug>` 与 doc_type）；2. **合同对账**（逐条对回 §9.3 八问，特别是 server/client 边界与依赖方向）；3. **门禁结果**（§6 自检命令输出：tsc / lint / build / test 实际结果）；4. **偏差与豁免**（与本文/L2 的偏差，pending 四类的 `l2_status: pending` 豁免在此登记理由）。

---

## 10. 行为与设计单元编号纪律

- **行为**：`BHV-NNN`（三位数，需求级行为），如 `BHV-001 标签筛选文章列表`。
- **设计单元**：`UNIT-<slug>`（kebab-case slug），如 `UNIT-tag-filter`(client-component)、`UNIT-posts-data-access`(data-access)、`UNIT-post-card`(ui-component)、`UNIT-posts-route`(route)。
- 下游（概要表 / 详细合同 / 实现 trace / 门禁报告）引用一律**裸 token**，不加书名号/反引号包装编号本身。一个 `BHV-NNN` 可承接多个 `UNIT-<slug>`；一个 `UNIT-<slug>` 恰好一个 `doc_type`。

---

## 11. 派生关系（给 build 用）

- **脚手架模板** ← §4 各类代码块参数化（参数 = project-conventions 槽位 `[SLOT-xx]`）；按 §1 入口决策树条件组合（命中哪几类生成哪几类骨架）。
- **`guru-lints-next`（ESLint 规则集）** ← §2.1（import 边界方向）+ §2.2（`'use client'`/server-only 误用）+ §2.3（缓存显式/不吞错）+ §2.4（样式隔离，读 `[SLOT-04]`）+ §2.5（route 保留文件名）+ §2.7（strict/no-any）+ §7 禁止清单；槽位类规则运行时读取目标仓库 project-conventions。
- **配置包 Skill（概要/详细/实现三件套）** ← 本文全文 + 各自 references：概要用 §1/§9.1/§9.2；详细用 §0/§4 + L2 三件套(`detail-type-server-component/client-component/data-access`) + §9.3；实现用 §5/§6/§9.4。所有 agent 适配层**指向本文**，不各写一份。
- **hooks** ← §5/§6 构建自检回灌 + §7 禁止清单中可静态拦截项（如老目录新建、`'use client'` 取私有数据）+ `[SLOT-02]`/`[SLOT-13]` 目录与路由模式拦截。
