# L2 类型规范：server-component（RSC 服务端组件）

> doc_type：`server-component`（H5_BRIEF 钉死七类之一，全程唯一，禁止改名/增减/换数）｜ l2_status：**full**（v1 提供 render/interactive/data 三元组之 render 端）
> 从属于 L1 `detail-structure-single-source.md`（H5 单一来源规范）；本文件只写 `server-component` 类型的差异规则，与 L1 冲突时以 L1 为准。
> 装载路径：本文 `.trellis/spec/harness/detail/detail-type-server-component.md`；通用 golden-path `.trellis/spec/guides/golden-path.md`。
> golden-path 对应：server-first 渲染律、`'use client'` 最小化、私有数据/secret 边界、props 序列化边界、metadata/SEO、样式隔离。
> 三元组定位：本类型对应 flutter 的 **controller**（render/编排端）——但 RSC 不持有客户端状态，编排重心落在"服务端数据获取顺序 + 组件树组装 + 把交互下沉给 client-component"。交互态归 `client-component`（对应 usecase 的状态流位移到 client），数据访问归 `data-access`（对应 repository-datasource）。

---

## 适用对象

App Router 下默认的 **React Server Component（RSC）**：在服务端渲染、负责"取数 + 组装组件树 + 编排子组件"的非交互组件，文件**不带** `'use client'` 指令。

**适用**：
- `page.tsx` / `layout.tsx` 的默认导出（未标 `'use client'` 时本身就是 server-component；其取数与组装编排适用本规范）。
- 服务端 `async` 组件（`async function Xxx()`，可 `await` 数据访问层）。
- 把私有数据获取结果向下传给展示组件（`ui-component`）或交互组件（`client-component`）的"编排壳"。

**不适用**（命中即归他类，不在本文展开）：
- 含状态/事件/hooks/浏览器 API 的交互组件 → `client-component`（`'use client'`）。
- 直接封装 fetch / ORM 查询 / MDX 内容读取的取数函数 → `data-access`。
- 纯展示、无取数无业务的可复用组件 → `ui-component`。
- TS 类型 / zod schema / 领域模型 → `domain-type`。
- 变更 / API endpoint / 表单提交 → `server-action`。
- route 段编排（page/layout/loading/error 文件的路由语义、metadata 导出、SEO）的整体合同 → `route`（本类型只承载 route 段内"取数 + 渲染"的实现差异；metadata 导出位置与 SEO 完整合同在 `route`）。

**owner 链定位（分层依赖律，归属硬基准，违反 fail）**：
`route → server-component → data-access → domain-type`（服务端链）。本类型**上承** `route`、**下调** `data-access`，并可向下传递给 `client-component`（交互链 `client-component → ui-component`）与 `ui-component`。**禁止反向**：`data-access` / `domain-type` 不得依赖 server-component。

> **示例实证 vs 生产级补充**：参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是 **Pages Router + Nextra + MDX + gray-matter** 的轻量 starter，**没有 RSC**（`getStaticProps`/`getStaticPaths` 心智、`_app.tsx`/`_document.tsx` 注入 `<Head>`）。本文凡标 **[示例实证]** 者可在该 starter 中找到对应内容模型（frontmatter、MDX 内容源、`gray-matter` 解析、`next/image`、`<Head>` 注入 SEO meta）；凡标 **[生产级补充]** 者为 App Router 生产最佳实践、该 starter 不具备，按 golden-path 锁定。两者**不得混用**：把 `getStaticProps` 当 RSC 写、或在 server-component 内调 `useState` 均为 P1。

---

## 合同八问的类型特化

> 编号纪律：每个设计单元以 `### UNIT-<slug>` 标题定义（语义 kebab-case，如 `UNIT-post-detail-page`、`UNIT-post-list-section`）；下游测试与实现切片对单元的引用一律写裸 `UNIT-<slug>` token；承接行为一律写裸 `BHV-NNN` token（必须存在于 prd，幽灵引用与无承接均被 gate 断链拦截）。

1. **承接哪些行为（BHV-NNN）**：本组件承接的是**"页面/区块的服务端渲染与取数编排"类行为**——例如"展示文章详情正文"、"列出文章索引"、"按 slug 服务端渲染对应内容"。逐条引用 `BHV-NNN`。**不承接**纯交互行为（点赞、展开、表单输入——归 `client-component` 的 BHV）。每条承接行为映射到"组件渲染出的一段确定 DOM + 其依赖的数据获取调用"。

2. **输入 / 输出 / 错误结果**：
   - **输入**（逐项列表）：① route 段注入的 `params` / `searchParams`（App Router 约定，类型来自 `domain-type`，[生产级补充]）；② 父 server-component 透传的 props（**必须可序列化**，见类型硬规则 props 序列化边界）；③ 经 `data-access` 取回的数据（**不在本组件内直接 fetch/ORM/读文件**，调 `data-access` 暴露的函数，对应 [示例实证] 的 `gray-matter` 解析 frontmatter）。
   - **输出**：组件返回的 **JSX/ReactNode 结构**（签名级写 `async function | function` 返回 `Promise<JSX.Element> | JSX.Element`）；向下传给子组件的 props 清单（**逐 prop 列表**：名称 / 类型 / 是否可序列化 / 去向是 client 还是 server 子树）。
   - **错误**：取数失败的去向——抛错交由就近 `error.tsx` 边界捕获（归 `route`），或 `notFound()` 触发 `not-found.tsx`；**错误枚举引用 `data-access` 抛出的错误类型**（不在本组件新造错误类型，错误模型归 `domain-type`）。

3. **读取 / 写入哪些状态**：
   - **读**：只读服务端数据（经 `data-access`）、route `params`/`searchParams`、环境/请求上下文（`headers()`/`cookies()` 读取，[生产级补充]）。
   - **写**：**RSC 不持有客户端可变状态**（无 `useState`/`useReducer`/`useRef`）。任何"写状态"出现在 server-component = P1（该状态应归 `client-component`）。变更服务端数据归 `server-action`，本组件**不写**。
   - 渲染缓存语义（`fetch` 的 `cache`/`revalidate`、`dynamic`/`revalidate` 段配置）**只声明引用**，落点决策归 `route`/`data-access`（见八问 8）。

4. **调用哪些依赖，不调用哪些依赖**（正反两面都写，防越层）：
   - **可调用**：`data-access` 暴露的取数函数（**唯一取数入口**）；`domain-type` 的类型/schema；子 `server-component`；`ui-component`（展示）；`client-component`（作为子节点渲染，只能透传可序列化 props）。
   - **禁止调用（违反即 P1）**：① 直接 `fetch` 私有/带 secret 的 API、直接 ORM/DB 查询、直接读文件解析 MDX（**必须经 `data-access`**）；② `server-action` 的业务变更（变更归 `server-action`，由 `client-component`/`<form action>` 触发）；③ 任何浏览器/客户端 API（`window`/`document`/`localStorage`/事件 hooks）；④ 反向依赖 `route`（不 import 路由段壳）。

5. **失败如何收口**：
   - 取数失败 → **向上抛**，由就近 `error.tsx` 渲染兜底（不在 server-component 内 `try/catch` 吞错后渲染空白——吞错=P2/P1 视后果）；
   - 资源不存在（如 slug 无对应文章）→ 调 `notFound()`（触发 `not-found.tsx`）；
   - 部分失败可降级 → 用 `<Suspense>` 包裹可独立失败的子树 + 子树自带 `error.tsx`/fallback（[生产级补充]）；
   - **失败语义逐条对应一条 BHV 失败分支或八问 2 的错误枚举**，错误转换位置在 `data-access`（本组件不做底层异常到业务错误的映射）。

6. **产生哪些事件 / 后置结果**：
   - server-component **无客户端副作用**（无 `useEffect`、无埋点 SDK 直调——埋点归 `client-component`）；
   - 后置结果 = ① 渲染产物（HTML/RSC payload，是 SEO 可索引内容）；② 触发的数据缓存/重验证由 `data-access`/`route` 的缓存配置决定（本组件**声明依赖**，不决定 TTL）；
   - 若需在渲染后让客户端发起交互/埋点 → **下沉给 `client-component`**，本组件只透传初始数据 props。

7. **哪些测试验证它**（映射到测试分层，逐行为给测试点，成功 + 全部失败路径）：
   - **组件渲染测试**（Vitest + React Testing Library，[生产级补充]）：mock `data-access`，断言给定数据 → 渲染出预期文本/结构；断言传给子 `client-component`/`ui-component` 的 props 正确且可序列化。
   - **async 组件**：RTL 对 server-component 的渲染需配合 async 渲染断言（`await` 渲染后查 DOM）。
   - **失败路径**：mock `data-access` 抛错 → 断言异常向上冒泡（交由 error 边界，不被吞）；slug 不存在 → 断言调用 `notFound()`。
   - **集成/E2E**（Playwright）：真实路由下页面 SSR 输出含目标内容（SEO 可见）、`error.tsx`/`not-found.tsx` 正确兜底。
   - **每条承接 BHV 至少 1 成功 + 1 失败用例**（含取数失败、资源不存在）。

8. **哪些内容不得在此补造**（显式列出本单元不拥有的决策）：
   - 不决定**交互与客户端状态**（归 `client-component`）；
   - 不决定**取数实现/缓存 TTL/数据源选型**（归 `data-access`，缓存段配置归 `route`）；
   - 不决定**数据变更/写库/表单提交**（归 `server-action`）；
   - 不新造**错误类型/领域类型/zod schema**（归 `domain-type`）；
   - 不决定**route 段的 metadata/SEO 字段全集与路由语义**（归 `route`，本组件只消费）；
   - 不决定**展示组件的视觉/样式系统**（归 `ui-component` + 样式方案槽位）。

---

## H5 硬规则（golden-path 锁定，违反判级见末表）

1. **RSC 默认（server-first）**：App Router 下组件**默认即 server-component**，文件顶部**不写** `'use client'`。`'use client'` 最小化——仅在真正需要交互处下沉到 `client-component`。在本类型文件出现 `'use client'` = 类型误判（应归 `client-component`），P1。

2. **服务端数据获取**：取数**只经 `data-access`**（封装 fetch/MDX/CMS/ORM）。可在 `async` 组件内 `await dataAccessFn()`。**禁止**在 server-component 内联裸 `fetch` 私有 API、裸 ORM 查询、裸 `fs`/`gray-matter` 读文件（[示例实证] 的 frontmatter 解析在生产里要收敛进 `data-access`，server-component 只消费其返回的领域模型）。

3. **不带交互**：无 `useState`/`useReducer`/`useEffect`/`useRef`/事件处理器（`onClick` 等）/浏览器 API（`window`/`document`/`localStorage`）。需要任一 → 拆出 `client-component` 作为子节点。

4. **async 组件**：server-component 可声明为 `async function`，直接 `await` 取数；返回 `Promise<JSX.Element>`。**client-component 不可 async**（这是区分两类的硬信号之一）。多个独立取数优先并行（`Promise.all` 或并列 `<Suspense>`），避免串行瀑布。

5. **不暴露 secret 给 client**：私有数据获取、API key、token、DB 连接串**只在 server-component / data-access / server-action 内出现**；**禁止**把 secret 写进传给 `client-component` 的 props、或放进会序列化进 RSC payload 的对象。环境变量遵循：非 `NEXT_PUBLIC_` 前缀者**不得**进入客户端可达路径。

6. **props 序列化边界（server → client 边界）**：从 server-component 传给 `client-component` 的 props **必须可序列化**（JSON-serializable：基本类型、纯对象、数组、Date 等 RSC 支持类型；**不可传**函数、class 实例、Symbol、不可序列化对象——函数式回调归 `server-action` 或在 client 内部定义）。server→server 之间无此限制（可传函数/组件），但仍**禁止把 secret 越过边界**。每个传向 client 子树的 prop 在合同里标注"是否跨 server/client 边界 + 是否可序列化"。

7. **route 段约定（page/layout/loading/error）**：本类型作为 `page.tsx`/`layout.tsx` 默认导出时遵循 App Router 段约定；`loading.tsx`/`error.tsx`/`not-found.tsx` 的存在与兜底归 `route` 合同，本组件只负责"抛对的错"让边界接住（见八问 5）。

8. **metadata/SEO 标准化**：[示例实证] starter 用 `_document.tsx` + `<Head>` 注入 `og:*`/`twitter:*`/`description`/`robots`；[生产级补充] App Router 改用段内 `export const metadata` 或 `export async function generateMetadata()`——**该导出归 `route` 合同**，server-component 只提供 `generateMetadata` 所需的取数（经 `data-access`，可与正文取数共享缓存/dedupe）。

9. **样式隔离**：CSS Modules / Tailwind（项目槽位），**禁止全局样式污染**；server-component 不引入运行时 CSS-in-JS（如需 `styled-jsx` 等运行时方案，归 client 边界）。

---

## 好 / 坏例子（tsx 代码，签名级 + 关键结构，禁止超签名级实现）

> 设定：文章详情页。`UNIT-post-detail-page` 承接 `BHV-012`（按 slug 服务端渲染文章详情）。下例 `data-access` 函数 `getPostBySlug` 已在 `data-access` 类型合同中定义（封装 MDX/gray-matter 或 CMS 查询），返回领域类型 `Post`（定义在 `domain-type`）。

### ✅ 好例子

```tsx
// app/posts/[slug]/page.tsx —— server-component（无 'use client'，async）
// 承接：BHV-012（按 slug 服务端渲染文章详情）｜ UNIT-post-detail-page
import { notFound } from "next/navigation";
import { getPostBySlug } from "@/lib/data-access/posts"; // 唯一取数入口（data-access）
import type { Post } from "@/domain/post";                // 领域类型（domain-type）
import { PostBody } from "@/components/ui/post-body";      // ui-component（纯展示）
import { LikeButton } from "@/components/client/like-button"; // client-component（交互）

interface PageProps {
  params: { slug: string }; // route 段注入（路由约定）
}

export default async function PostDetailPage({ params }: PageProps) {
  const post: Post | null = await getPostBySlug(params.slug); // 服务端取数，经 data-access
  if (!post) notFound(); // 资源不存在 → 交 not-found.tsx（失败收口，八问5）

  return (
    <article>
      <h1>{post.title}</h1>
      {/* server 子树：纯展示，server→server 无序列化限制 */}
      <PostBody html={post.contentHtml} />
      {/* client 子树：只透传可序列化 props（id/初始计数），不传函数、不传 secret */}
      <LikeButton postId={post.id} initialLikes={post.likes} />
    </article>
  );
}
// 注：metadata/generateMetadata 导出归 route 合同，本组件只供其取数复用。
```

要点：① 无 `'use client'`、`async` 组件、`await` 经 `data-access` 取数；② 不存在 → `notFound()`，取数失败自然上抛交 `error.tsx`（不吞错）；③ 传给 `LikeButton`（client）的 props 全部可序列化（`postId: string`、`initialLikes: number`），无函数、无 secret；④ 展示交给 `PostBody`（ui-component），交互交给 `LikeButton`（client-component），各司其职。

### ❌ 坏例子

```tsx
// ❌ 反面：把多条硬规则违反堆在一个 server-component 里
"use client"; // ❌ P1：server-component 不写 'use client'（应归 client-component）
import { useState, useEffect } from "react";
import matter from "gray-matter";        // ❌ P1：直接读文件解析，绕过 data-access
import fs from "node:fs/promises";

export default function PostDetailPage({ params }: any) { // ❌ params 用 any（应来自 domain-type）
  const [post, setPost] = useState<any>(null); // ❌ P1：RSC 不持客户端状态

  useEffect(() => {                            // ❌ P1：server-component 不应有 useEffect
    fs.readFile(`posts/${params.slug}.md`).then((b) => { // ❌ 内联 fs/IO，且暴露内部路径
      const { data, content } = matter(b);     // ❌ 取数实现下沉到组件里
      setPost({ ...data, content });
    });
  }, []);

  if (!post) return <div />;                   // ❌ 静默吞"加载/失败"，无 loading/error 边界

  const apiKey = process.env.CMS_SECRET_KEY;   // ❌ P1：secret 进入将渲染到 client 的作用域
  return (
    <article>
      <h1>{post.title}</h1>
      {/* ❌ 把含 secret 的对象、回调函数传给子组件，越序列化/secret 边界 */}
      <LikeButton config={{ apiKey }} onLike={() => fetch("/private")} />
    </article>
  );
}
```

坏点对照（每条对应一条硬规则）：误标 `'use client'`（规则1/3）；`useState`/`useEffect`（规则3，RSC 不带交互/不持状态）；内联 `fs` + `gray-matter` 取数（规则2，绕过 data-access）；`process.env.CMS_SECRET_KEY` 进入客户端可达作用域并经 props 外泄（规则5）；向 client 传 `apiKey` 与 `onLike` 函数（规则6，越序列化边界 + 泄 secret）；`return <div />` 静默吞错（八问5，应抛错交 error 边界或 `notFound()`）；`params: any`（八问2，类型应来自 domain-type）。

### 不适用场景（命中即改归他类，不在本文成立）

- 组件需要 `onClick`/`useState`/受控输入/动画/`localStorage` → `client-component`。
- 文件只做 `fetch` 封装 / MDX 读取 / ORM 查询、不返回 JSX → `data-access`。
- 组件纯展示、props 进、JSX 出、无取数无业务 → `ui-component`。
- 文件只导出 `metadata`/`generateMetadata`/路由段语义且无实质渲染编排 → 合同主体归 `route`。
- 处理表单提交 / 写数据 / 暴露 API → `server-action`。

---

## Gate 兼容（与 L1 §7 G1~G7 对齐；本类型可验证信号清单）

每个 `UNIT-<slug>`（server-component）落地前须可取证以下信号，缺一即 finding：

**需求五要素承接**：每条承接行为有裸 `BHV-NNN`，且该编号存在于 prd（断链 → P1，对应 G1/G3）。

**概要归属表 + 承接索引**：本组件出现在概要归属表，且 owner 链满足 `route → server-component → data-access → domain-type`；`chapter_target → detail_doc_type=server-component` 在承接索引可双向闭合（缺失 → 回退概要补归属，禁止详细补造，对应 G1/G6）。

**详细合同八问**：八问逐条非空且满足 §"合同八问的类型特化"；输入/输出/props 透传有逐项列表；错误引用 `data-access`/`domain-type` 既有类型（对应 G2/G5）。

**实现 trace 计划合同与 mutable evidence**（实现阶段回填，验证 trace 闭合）：
1. **组件签名**：`(async )function <Name>(props): (Promise<)JSX.Element` 与合同输入/输出一致，文件无 `'use client'`。
2. **取数调用点**：逐处 `await` 的 `data-access` 函数与八问 4 的"可调用"清单一致；无内联 fetch/ORM/fs（对应规则2）。
3. **边界落点**：传向 `client-component` 的 props 全部可序列化、无 secret（对应规则5/6）；失败路径落到 `error.tsx`/`notFound()`（对应八问5）。
4. **测试 trace**：每条 BHV 的成功 + 失败用例存在并通过（对应 G3/八问7）。

**判级**：
- **P1（阻塞）**：出现 `'use client'`/客户端状态/`useEffect`/浏览器 API（类型误判）；内联取数绕过 `data-access`；secret 进入 client 可达路径或经 props 外泄；不可序列化 props 越 server/client 边界；BHV 断链；越层（直调 server-action 业务变更 / 反向依赖 route）；owner 链违反。
- **P2（可局部补）**：错误未抛而静默吞、缺 `notFound()` 分支；props 透传清单缺序列化标注；测试缺失败路径用例；串行取数瀑布（应并行）。
- **P3（建议）**：组件过大宜按区块抽子 server-component；命名/样式槽位偏好。

> 红线（详细阶段，对齐 L1 §6）：不得新增概要归属表外结构；不得在本类型决定缓存 TTL/数据源选型/metadata 字段全集（分别归 data-access/route）；代码不得超签名级（签名 + 关键结构为上限，禁完整实现/伪代码堆砌）。辅助文本一律中文，代码语法元素（类名/方法名/参数名/字面量/框架名）保持英文。
