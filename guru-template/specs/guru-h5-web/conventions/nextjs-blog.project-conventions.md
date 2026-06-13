# Project Conventions — Next.js Blog Starter（guru-h5-web 示例样例）

> 这是 guru-h5-web 平台的 **project-conventions 示例取值文件**，对标 `guru-flutter-client/conventions/seek.project-conventions.md` 的填写风格。安装配置包时本文件迁入目标 H5 仓库 `.trellis/spec/conventions/project-conventions.md`，由各阶段 writing/review skill 在硬前置中装载（装载路径一律 `.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md`）。
> **取值依据**：2026-06-14 对 `next.js/examples/blog` 的实测扫描（package.json / tsconfig.json / pages/ / theme.config.js / styles / scripts）。
> **doc_type 与分层一律以 H5_BRIEF 权威七类为准**：`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`。本文件**不照抄** flutter（controller/usecase/repository-datasource）或 Go 的类型名。
> **全程区分「示例实证 vs 生产级补充」**：示例 = `next.js/examples/blog` 可直接佐证的事实（Pages Router + Nextra + MDX + gray-matter + `strict:false`，故意简化）；生产级补充 = golden-path 锁定的 App Router 生产基线（`strict:true`、server-first、route 段约定、metadata/SEO、样式隔离、错误边界）。**凡示例与生产基线冲突，以生产基线为准。**

---

## 0. 元信息

| 字段 | 取值 |
|------|------|
| App 名称 / 包名 | Next.js Blog Starter Kit / `examples/blog`（package.json `"private": true`，无 `name` 字段） |
| 仓库路径 | `next.js/examples/blog`（Nextra 2 blog starter；`next: latest` / `react ^18.2.0` / `typescript ^4.7.4`） |
| 填写日期 / 填写人 | 2026-06-14 / client_agent 配置包（实测扫描） |
| 取值依据 | 实测扫描；本仓库为**示例样例**，非生产 App。生产取值以 App 仓库 redline + ADR 为准 |
| 平台基线 | Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)；示例为 Pages Router + Nextra + MDX |

---

## 1. 槽位清单（SLOT-01~SLOT-16，与 go/ios 同构的单一 SLOT-NN 体系）

> 编号体系（与 `conventions/index.md` 开篇规范、go/ios 平台对齐）：本平台项目约定**只用 `SLOT-NN` 单一前缀**（不用 `SLOT-HN`/`SLOT-MN` 等分套前缀），编号自 `SLOT-01` 起连续递增，创建后不复用、不重排、删除留洞，**存量违例清单固定为最后一个槽位**。本文件共 **16 个槽位**：取值槽 `SLOT-01~SLOT-11`（内容源/状态管理/UI 库/样式/测试/lint/数据库/认证/图像/部署/路由模式）+ 方法学纪律承接槽 `SLOT-12~SLOT-15`（doc_type 七类锁定/分层依赖律/写作顺序/编号纪律）+ 存量违例清单 `SLOT-16`。
> 每槽位字段：**决策问题**（钉死什么）· **本项目取值**（示例实证）· **生产级补充**（golden-path 基线，与示例差异显式标注）· **代码证据**（仓库内真实路径）· **生效范围**（示例 only / 全量）· **消费方**（哪个 doc_type / Gate 用）。
> 待定项必须写明决策人与期限，且待定总数 ≤ 2，否则项目约定视为未就绪（硬前置不通过）。本文件待定 0 项。

### SLOT-01 内容源
- 决策问题：data-access 从哪里取内容（MDX 文件 / Headless CMS / ORM(DB)）？front-matter 字段如何解析？
- 本项目取值（**示例实证**）：**MDX/Markdown 文件内容源** + `gray-matter` 解析 front-matter。文件即路由（`pages/posts/*.md`），front-matter 字段为 `title` / `date` / `description` / `tag` / `author`（单标签字符串，`tag.split(", ")` 拆分）；Nextra（`nextra ^2.0.0-beta.5` + `nextra-theme-blog`）负责把 MDX 渲染成博客主题。
- 生产级补充（**golden-path 基线**）：内容源形态不变（MDX 文件可继续用），但**读取改走 server 端 data-access 模块**（`lib/content/posts.ts` 一类），由 server-component 调用；front-matter 用 **zod schema 校验**产出 domain-type，而非裸 `frontmatter.data.*` 任意取字段。**禁止** client-component 直接 import 内容读取模块（违反 P1 私有数据边界 → 但 MDX 为公开内容时可放宽，须在合同八问之 4 显式声明）。
- 代码证据：`pages/posts/markdown.md`（front-matter 五字段）；`pages/posts/pages.md`；`scripts/gen-rss.js:22`（`matter(content)`）、`:29`（`frontmatter.data.tag.split(", ")`）；`package.json:9,11,12`（`gray-matter` / `nextra` / `nextra-theme-blog`）。
- 生效范围：示例 only（内容模型基线）；生产 data-access 形态见 `.trellis/spec/harness/detail/detail-type-data-access.md`。
- 消费方：`data-access`（获取形态）、`domain-type`（front-matter → 领域模型）。

### SLOT-02 状态管理
- 决策问题：跨组件状态用 none / Zustand / Context？server-first 下默认形态是什么？
- 本项目取值（**示例实证**）：**none（无全局状态库）**。示例无 Zustand / Redux / Context Provider；唯一的客户端态来自 `pages/tags/[tag].mdx` 内 `useRouter().query` 读取路由参数（路由派生态，非应用状态）。
- 生产级补充：**默认 none，server-first**。仅在需要 state/event/hooks 的最小叶子组件标 `'use client'` 持局部交互态（`useState`/`useReducer`）；确需跨组件共享交互态时用 Context 包裹**最小 client 子树**，禁止把 Context Provider 提到根 layout 把整树变 client。私有数据态不进 client（走 server-component / server-action）。
- 代码证据：`pages/tags/[tag].mdx:6-11`（`useRouter().query` 读 `tag`）；`package.json` dependencies 无任何状态库。
- 生效范围：全量。
- 消费方：`client-component`（交互态字段表）、`server-component`（确认无客户端态写 N/A）。

### SLOT-03 UI 组件库
- 决策问题：展示型组件来源（shadcn / MUI / 自建 / 无）？
- 本项目取值（**示例实证**）：**无独立 UI 组件库**。展示完全由 `nextra-theme-blog` 主题接管（布局/排版/导航/footer），业务侧只写 MDX 内容 + `theme.config.js` 配置 footer（内联 `<style jsx>`）。
- 生产级补充：ui-component 来源基线由 App 仓库定（推荐 shadcn/ui，按需引入、可控样式 token）；ui-component 必须**纯展示、无数据获取、无业务**（分层依赖律：`client-component → ui-component`，ui-component 是被组合方）。`next/image` 为图像优化基线（见 SLOT-09）。
- 代码证据：`package.json:12`（`nextra-theme-blog ^2.0.0-beta.5`）；`theme.config.js:4-19`（footer + `<style jsx>`）；dependencies 无 shadcn/MUI/radix。
- 生效范围：示例 only。
- 消费方：`ui-component`（来源基线）。

### SLOT-04 样式方案
- 决策问题：样式隔离用 Tailwind / CSS Modules？全局样式边界在哪？
- 本项目取值（**示例实证**）：**全局 CSS + `styled-jsx` 内联**。`styles/main.css` 为单一全局样式表（裸 `body` / `h1` / `.prose a` / `.nav-line .nav-link` 全局选择器 + `@font-face`），在 `pages/_app.tsx` 顶层 `import "../styles/main.css"` 全局注入；theme footer 用 `<style jsx>`。**这是存量违例**（全局样式污染，见 SLOT-16.1）。
- 生产级补充（**golden-path 硬规则 6**）：**样式隔离用 CSS Modules 或 Tailwind，禁止全局样式污染**；唯一允许的全局层是受控的 `app/globals.css`（仅放设计 token / `@font-face` / reset），业务样式一律走 `*.module.css` 或 Tailwind 原子类。示例的裸标签全局选择器（`body`/`h1`/`.prose a`）在生产基线下不允许。
- 代码证据：`styles/main.css:17-83`（裸 `body`/`h1`/`h2`/`.prose a`/`.nav-line .nav-link` 全局选择器）；`pages/_app.tsx:1,4`（`import "nextra-theme-blog/style.css"` + `import "../styles/main.css"` 全局注入）；`theme.config.js:10-17`（`<style jsx>`）。
- 生效范围：示例 only（违例已登记 SLOT-16.1）；生产以 CSS Modules/Tailwind 为准。
- 消费方：`ui-component` / `client-component`（样式隔离方式）、实现 Gate（全局样式污染为阻塞项）。

### SLOT-05 测试
- 决策问题：单元/组件测试用 Vitest+RTL，e2e 用 Playwright？测试目录与命名约定？
- 本项目取值（**示例实证**）：**无测试**。`package.json` scripts 仅 `dev` / `build` / `start`，无 `test` 脚本；devDependencies 无 Vitest / Jest / RTL / Playwright；仓库无 `*.test.ts(x)` / `*.spec.ts(x)` / `__tests__/` / `e2e/`。**这是存量违例**（无测试，见 SLOT-16.3）。
- 生产级补充（**详细 Gate / 实现 Gate 要求**）：**Vitest + React Testing Library** 做单元/组件测试（domain-type schema 校验、data-access 解析逻辑、client-component 交互、server-component 渲染快照）；**Playwright** 做 e2e（route 段导航、metadata、错误边界）。每个 `BHV-NNN` 须有测试映射（成功路径 + 全部失败路径），合同八问之 7 逐单元给测试点。实现 Gate 要求 test 证据到**测试名级**。
- 代码证据：`package.json:3-7`（scripts 仅三条，无 `test`）；`package.json:17-22`（devDependencies 仅 `@types/*` + `typescript`，无测试框架）。
- 生效范围：示例 only（违例已登记 SLOT-16.3）；生产全量。
- 消费方：合同八问之 7（测试映射）、实现 Gate（test 证据）。

### SLOT-06 lint
- 决策问题：静态检查命令来源（ESLint + Prettier）？
- 本项目取值（**示例实证**）：**无 lint**。无 `.eslintrc*` / `eslint.config.*` / `.prettierrc*` / `prettier.config.*`；`package.json` 无 `lint` 脚本；devDependencies 无 `eslint` / `eslint-config-next` / `prettier`。**这是存量违例**（无 lint，见 SLOT-16.4）。
- 生产级补充（**实现 Gate 要求**）：**ESLint + Prettier**，ESLint 以 `eslint-config-next` 为基线（含 `react-hooks` / `@next/next` 规则，能拦 `'use client'` 误用与 Server/Client 边界问题）；Prettier 统一格式。实现 Gate 要求 lint 有证据。`'use client'` 滥用与全局样式污染在此层与 review 层双重拦截。
- 代码证据：`package.json:3-7`（无 `lint` 脚本）；`package.json:17-22`（devDependencies 无 eslint/prettier）；仓库无 eslint/prettier 配置文件。
- 生效范围：示例 only（违例已登记 SLOT-16.4）；生产全量。
- 消费方：实现 Gate（lint 证据）、`client-component`（`'use client'` 边界）。

### SLOT-07 数据库
- 决策问题：data-access / server-action 写路径依据（无 / Postgres / 其它 ORM）？
- 本项目取值（**示例实证**）：**无数据库**。内容全部来自文件系统（MDX 文件 + `gray-matter`），无 ORM、无连接池、无 `DATABASE_URL`；`scripts/gen-rss.js` 用 `fs.readdir` / `fs.readFile` 读 `pages/posts/`。
- 生产级补充：若引入数据库，写路径走 **server-action → data-access** 变更链（分层依赖律：`server-action → data-access`），ORM 查询封装在 data-access，**禁止** client-component 越过 server-action 直连 ORM（违反 P1）。连接串/凭证只走环境变量，**永不落文档**（只写环境变量名）。
- 代码证据：`scripts/gen-rss.js:1,13,19-21`（`fs.readdir` / `fs.readFile` 读文件系统）；dependencies 无任何 ORM/DB 驱动。
- 生效范围：全量（示例为「无 DB」即合法取值）。
- 消费方：`data-access` / `server-action`（写路径）。

### SLOT-08 认证
- 决策问题：server-action / route 的鉴权依据（无 / NextAuth / 其它）？
- 本项目取值（**示例实证**）：**无认证**。纯静态公开博客，无登录、无 session、无受保护 route；无 NextAuth、无中间件（无 `middleware.ts`）。
- 生产级补充：若需鉴权用 **NextAuth（Auth.js）**；鉴权校验只在 server 侧（server-component / data-access / server-action / route handler），session/token **禁止**暴露给 client-component 直取。涉鉴权/私有数据/secret 的单元，合同八问须附**合规与边界依据**（详细 Gate 要求）。
- 代码证据：仓库无 `middleware.ts`、无 `pages/api/auth/*`、无 `app/api/auth/*`；dependencies 无 `next-auth`。
- 生效范围：全量（示例为「无认证」即合法取值）。
- 消费方：`route` / `server-action`（鉴权边界）、详细 Gate（secret 合规）。

### SLOT-09 图像优化
- 决策问题：图片走 `next/image` 还是裸 `<img>`？资源约定？
- 本项目取值（**示例实证**）：**`next/image`**。`pages/photos.mdx` 直接 `import Image from "next/image"` 并显式给 `width` / `height` / `priority` / `className`；静态资源置于 `public/images/`、字体置于 `public/fonts/`（`pages/_app.tsx` 用 `<link rel="preload" as="font">` 预加载）。Nextra 另有 `unstable_staticImage` 选项（`next.config.js` 注释，示例未开启）。
- 生产级补充：图像优化基线仍是 **`next/image`**（须给 `width`/`height` 或 `fill` 防 CLS、首屏图给 `priority`、其余懒加载）；server-component 渲染图片资源、ui-component 封装图片展示组件时统一走 `next/image`，禁止裸 `<img>` 绕过优化。
- 代码证据：`pages/photos.mdx:11-30`（`next/image` + `width={1125} height={750} priority`）；`pages/_app.tsx:16-22`（字体 preload）；`next.config.js:4`（`unstable_staticImage` 注释）；`public/images/photo.jpg` / `public/fonts/Inter-*.woff2`。
- 生效范围：全量。
- 消费方：`ui-component` / `server-component`（资源约定）。

### SLOT-10 部署
- 决策问题：部署目标（Vercel / 其它）？影响 route handler 运行时（edge/node）与缓存语义？
- 本项目取值（**示例实证**）：**Vercel**。README/`pages/index.mdx` 提供 Vercel「Deploy your own」一键克隆链接；`pages/_document.tsx` 的 OG image 用 `assets.vercel.com`；构建命令 `node ./scripts/gen-rss.js && next build`（build 前置 RSS 生成脚本）。
- 生产级补充：部署目标仍以 **Vercel** 为默认基线；App Router 下 route handler / server-action 的运行时（`export const runtime = 'edge' | 'nodejs'`）与缓存语义（`revalidate` / `dynamic`）须在对应 `route` / `server-action` 单元的合同八问之 6（后置结果）显式声明；`revalidatePath` / `revalidateTag` 的缓存重验证由 server-action 负责。
- 代码证据：`pages/index.mdx:13`（Vercel clone 链接）；`pages/_document.tsx:7`（`assets.vercel.com` OG image）；`package.json:5`（`build` 前置 `gen-rss.js`）。
- 生效范围：全量。
- 消费方：`route` / `server-action`（运行时与缓存语义）。

### SLOT-11 路由模式
- 决策问题：用 App Router 还是 Pages Router？（golden-path 默认 App，偏离须记理由）
- 本项目取值（**示例实证**）：**Pages Router**（`pages/` 目录，`_app.tsx` / `_document.tsx` 约定，`pages/tags/[tag].mdx` 动态段，文件即路由）。**这是相对 golden-path 的偏离**，偏离理由：示例为 Nextra 2 blog starter，故意用 Pages Router + MDX 简化内容编写；**仅作内容模型基线**，不代表生产路由形态。
- 生产级补充（**golden-path 默认**）：生产形态 = **App Router**（`app/**`），route 段约定 `page.tsx` / `layout.tsx` / `loading.tsx` / `error.tsx`（`error.tsx` 必须 `'use client'`）；数据获取走 RSC server-component / data-access（**非** Pages 的 `getStaticProps` / `getServerSideProps`）；RSS / SEO 走 App Router `app/feed.xml/route.ts` + `metadata` API（**非**示例的 build 脚本 + `next/head`）。Pre-Development Checklist 要求确认路由模式 = App，本仓库历史为 Pages 故在此槽位显式记偏离。
- 代码证据：`pages/_app.tsx:6`（`App({ Component, pageProps }: AppProps)` Pages Router 签名）；`pages/_document.tsx:1-3`（`next/document`）；`pages/tags/[tag].mdx`（`[tag]` 动态段 + `useRouter().query`）；`pages/posts/*.md`（文件即路由）；`scripts/gen-rss.js`（build 期 RSS，非 route handler）；`pages/_app.tsx:9-23`（`next/head` 注入 RSS link，非 metadata API）。
- 生效范围：示例 only（偏离已记理由）；生产以 App Router 为准。
- 消费方：`route`（段约定）、hooks（目录拦截）、Pre-Development Checklist。

---

## 2. 方法学纪律承接槽位（编号 / 写作顺序 / doc_type 锁定，非取值而是纪律重述）

> 这些不是「项目取值」，是 H5_BRIEF 钉死、本文件必须显式承接的全局约定，供 review 在硬前置中核对「本仓库未私改类型名 / 未越层」。它们与上节取值槽共用同一 `SLOT-NN` 编号序列（接续 SLOT-11，为 SLOT-12~SLOT-15），不另起 `SLOT-MN` 分套前缀。

### SLOT-12 doc_type 七类锁定
- 本文件涉及的所有设计单元 `doc_type` 只能取：`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`。**禁止**出现 controller / usecase / repository / datasource / Manager / Helper / Util 等七类外的名（名词先行反模式，概要 Gate 阻塞）。
- L2 状态：`server-component` / `client-component` / `data-access` **v1 提供 L2**（render/interactive/data 三元组，对应 flutter controller/usecase/repository-datasource 的角色位，但**不沿用其名**）；`route` / `ui-component` / `domain-type` / `server-action` 为 `l2_status: pending`（full 链命中须显式 `L2豁免：<doc_type> 理由：…`，否则 gate 拦截）。

### SLOT-13 分层依赖律（owner 归属硬基准，违反 fail）
```
服务端链：  route → server-component → data-access → domain-type
交互链：    client-component → ui-component
变更链：    server-action → data-access
```
- 私有数据获取 / secret 只在 `server-component` / `data-access` / `server-action`；**禁** `client-component` 直取或读 secret（违反 P1）。
- `server-action` 走 `data-access` 落数据，不在交互链里直连 ORM/远端。
- 一份业务数据只有一个 `data-access` owner；client-component 不得越过 server-action 直接写数据库或读私有 fetch。

### SLOT-14 写作顺序（自底向上）
```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```
同一 feature 的 `data-access` 及其 `domain-type` 视为同一小批次优先完成。

### SLOT-15 编号纪律
- 行为：概要以 `### BHV-NNN <短名>` 定义（创建后不复用/不重排，删除留洞）；下游引用裸 `BHV-NNN` token。
- 设计单元：详细以 `### UNIT-<slug>` 定义（kebab-case，如 `UNIT-post-list-server-component`）；下游引用裸 `UNIT-<slug>` token。
- 幽灵引用与断链被 `guru_gate.py trace-matrix` 拦截；缺陷只能回上游修。

---

## 3. 存量违例清单（SLOT-16，tech-debt 登记 — 存量豁免机制数据源）

> 本仓库为示例 starter，与 golden-path 生产基线存在多处**结构性偏离**。下列为已登记存量违例：触碰存量记债不阻塞，**清单外的同类问题一律按「新增违例」阻塞**（审核 Gate 口径）。

1. **全局样式污染**（违反 golden-path 硬规则 6）：`styles/main.css` 用裸标签/全局选择器（`body` / `h1` / `h2` / `.prose a` / `.nav-line .nav-link`）并在 `pages/_app.tsx:4` 顶层全局 `import`，未走 CSS Modules / Tailwind 隔离。文件：`styles/main.css:17-83`、`pages/_app.tsx:1,4`。生产基线：仅受控 `app/globals.css` 放 token/字体/reset，业务样式走 `*.module.css` 或 Tailwind。
2. **TS 非 strict**（违反 golden-path 硬规则 1）：`tsconfig.json` `"strict": false` 且 `"target": "es5"`、`"allowJs": true`，类型安全弱、`any` 隐式兜底无拦截。文件：`tsconfig.json:6`（`strict: false`）、`:3`（`target: es5`）、`:5`（`allowJs: true`）。生产基线：`strict: true`，禁 `any` 兜底（必要处 `unknown` + 收窄）。
3. **无测试**（违反详细/实现 Gate 测试映射要求）：无 Vitest/RTL/Playwright、无 `test` 脚本、无任何 `*.test.*` / `*.spec.*` / `e2e/`。文件：`package.json:3-7,17-22`。生产基线：每行为有测试映射（成功 + 全部失败路径），实现 Gate 要求 test 证据到测试名级。
4. **无 lint**（违反实现 Gate lint 证据要求）：无 ESLint/Prettier、无 `lint` 脚本、无 `eslint-config-next`。文件：`package.json:3-7,17-22`、仓库无 eslint/prettier 配置。生产基线：ESLint(`eslint-config-next`) + Prettier，实现 Gate 要求 lint 证据，并拦 `'use client'` 误用。
5. **扁平结构 + Pages Router**（相对 golden-path App Router 的偏离）：内容/路由/样式平铺在 `pages/` + `styles/` + `scripts/`，无 `app/**` 段约定（`page`/`layout`/`loading`/`error.tsx`）、无 `metadata` API（SEO 走 `pages/_document.tsx` 手写 `<meta>` + `pages/_app.tsx` `next/head`）、无错误边界（`error.tsx`）、无 `loading.tsx` Suspense 边界。文件：`pages/_app.tsx`、`pages/_document.tsx:10-30`（手写 OG/twitter meta）、`pages/tags/[tag].mdx`、`scripts/gen-rss.js`。生产基线：App Router 段约定 + `metadata`/`generateMetadata` + `error.tsx`/`loading.tsx` + `app/feed.xml/route.ts`（替代 build 脚本生成 RSS）。
6. **构建期内容派生脚本（非 route handler）**：`scripts/gen-rss.js` 在 `next build` 前用 `gray-matter` 读 front-matter 生成 `public/feed.xml`，且 `frontmatter.data.*` 裸取字段（无 schema 校验，`strict:false` 下无类型保护）。文件：`package.json:5`、`scripts/gen-rss.js:22-35`。生产基线：RSS 改 App Router `app/feed.xml/route.ts`（route handler，运行时生成）+ domain-type zod schema 校验 front-matter。

---

## 4. 校验自检（writing/review 硬前置使用，对标 conventions/index.md C1~C6）

装载本约定文件的 Skill 必须先执行以下校验，任一不通过即终止并提示修复。校验项采用 `conventions/index.md` §3 的 C1~C6 体系（含 H5 专属 C4 doc_type 纯净），与 go/ios 同构；`C1~C5` 在 README / harness 速览里指「必须可定位取值的关键必填槽位子集」，对应映射见 `conventions/index.md` §3 末。

- [x] **C1 元信息齐全**：App 名 / 仓库路径 / 填写日期人 / 取值依据 / 平台基线五项齐全（§0）。
- [x] **C2 槽位完整，待定 0 项**：取值槽 SLOT-01~SLOT-11、方法学纪律承接槽 SLOT-12~SLOT-15、存量违例清单 SLOT-16 全部存在且有内容；无「待定」项。
- [x] **C3 证据可定位**：每个已填槽位至少 1 条 `next.js/examples/blog` 内真实路径（带行号锚点）。
- [x] **C4 doc_type 纯净**：全文 doc_type 只用 H5 权威七类（`server-component`/`client-component`/`data-access`/`route`/`ui-component`/`domain-type`/`server-action`），不出现 flutter（controller/usecase/repository-datasource）或 Go（transport/service/domain）类型名，也不自创 handler/provider 等（SLOT-12 显式锁定）。
- [x] **C5 不与硬规则冲突 / 冲突项已记债**：示例对 golden-path 7 条硬规则的偏离（全局样式 / 非 strict / 无测试 / 无 lint / 扁平 Pages / build 脚本派生）**全部登记入 SLOT-16**，并标注生产基线；分层依赖律 / doc_type 七类 / secret 边界**未被任何槽位豁免**（SLOT-12~SLOT-14 显式承接）。
- [x] **C6 存量清单存在**：SLOT-16 登记 6 条（非空），均带文件锚点 + 生产基线对照。

---

## 5. 槽位与门禁对应关系（参考）

| 槽位 | 谁消费 |
|------|--------|
| SLOT-01 内容源 | `data-access` / `domain-type` writing 与 review |
| SLOT-02 状态管理 | `client-component`（交互态字段表）、`server-component`（无客户端态声明） |
| SLOT-03 UI 库 / SLOT-09 图像 | `ui-component` / `server-component` writing |
| SLOT-04 样式方案 | `ui-component` / `client-component`、实现 Gate（全局样式污染拦截）、hooks |
| SLOT-05 测试 | 合同八问之 7、详细 Gate（测试映射）、实现 Gate（test 证据） |
| SLOT-06 lint | 实现 Gate（lint 证据）、`'use client'` 边界拦截 |
| SLOT-07 数据库 / SLOT-08 认证 | `server-action` / `data-access` / `route`、详细 Gate（secret/合规边界） |
| SLOT-10 部署 / SLOT-11 路由模式 | `route` / `server-action`（运行时/缓存）、hooks（目录拦截）、Pre-Development Checklist |
| SLOT-12~SLOT-15 方法学纪律承接 | 概要 Gate（doc_type 七类 / owner 归属 / 编号纪律）、trace-matrix |
| SLOT-16 存量违例清单 | 所有 review 的存量豁免判定（清单外新增违例阻塞） |
