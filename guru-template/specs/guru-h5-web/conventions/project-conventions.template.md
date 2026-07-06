# Project Conventions 模板（H5 / Next.js 项目约定槽位）

> **这是什么**：guru-h5-web 配置包定义的「项目约定槽位」模板。配置包的 SSOT 只锁**方法**与**团队栈级 canonical**（分层依赖律、doc_type 七类、server-first、`'use client'` 最小化、样式隔离等，见 `.trellis/spec/guides/golden-path.md`）；**项目级取值永不进配置包**——每个 H5 仓库按本模板填一份取值文件（建议路径：目标仓库 `.trellis/spec/conventions/project-conventions.md`），由各阶段 writing/review Skill 在硬前置中装载。
> **填写规则**：复制本模板 → 删除说明文字 → 逐槽位填写。每个取值必须给**代码证据**（仓库内真实路径）；没有证据的取值视为未填。
> **变更规则**：修改任何槽位取值属于项目级架构决策，需要 ADR 记录后方可生效。
> **平台基线**：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。参考示例 `next.js/examples/blog` 是 Pages Router + Nextra + MDX + `gray-matter` 的轻量 blog starter（`tsconfig.strict:false`，故意简化），仅作**内容模型基线**；golden-path 以 **App Router 生产最佳实践**为准。本模板全程区分「**示例实证**（blog 可直接佐证）」与「**生产级补充**（golden-path 锁定、示例未覆盖）」，冲突时以生产基线为准。
> **doc_type 七类（权威，禁止改名/增减/换数）**：`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`。本模板出现的归属判定一律以这七类为准，**勿照抄 flutter/Go 的 controller/usecase/repository 等类型名**。

---

## 0. 元信息（必填）

| 字段 | 取值 |
|------|------|
| 站点名称 / npm 包名 | `<site_name>` / `<npm_package>` |
| 仓库路径 | `<repo>` |
| 填写日期 / 填写人 | `<date>` / `<who>` |
| 取值依据 | 实测扫描（`package.json` / `next.config.*` / `tsconfig.json` 等真实路径） / 团队决策（附 ADR 链接） |

---

## 1. 槽位清单（全部必填）

> 每个槽位字段：**决策问题**（要钉死什么）· **本项目取值** · **代码证据**（≥1 条真实路径）· **生效范围**（新代码 only / 全量）· **备注**。
> 取值可以是「待定」，但待定项必须写明决策人与期限，且待定总数 ≤ 2，否则项目约定视为未就绪（硬前置不通过）。
> 备注里标注的「示例实证」指 `next.js/examples/blog` 能直接佐证的形态；「生产级补充」指 golden-path 锁定、示例未覆盖、需本项目自行落地并给生产仓库证据的形态。

### SLOT-01 路由模式（App vs Pages）
- 决策问题：本项目用 **App Router**（`app/` 目录、RSC 默认、route 段 `page`/`layout`/`loading`/`error.tsx`）还是 **Pages Router**（`pages/` 目录、`getStaticProps`/`getServerSideProps`）？是否存在两者并存的过渡分界？
- 本项目取值：
- 代码证据：（如 `app/layout.tsx` 与 `app/page.tsx` 存在 → App Router；或 `pages/_app.tsx` → Pages Router）
- 生效范围：
- 备注：**生产级补充**——golden-path 以 App Router 为目标，`server-component` / `route` / `server-action` 的合同与依赖律均以 App Router 语义为准。示例 blog 为 **Pages Router**（证据 `next.js/examples/blog/pages/_app.tsx`），仅作内容模型基线；若本项目仍是 Pages Router，必须在此显式声明，并把 App↔Pages 的分界钉死（新代码进哪个目录）。**App↔Pages 不可在同一 route 段混用**是通用硬规则，本槽位只钉模式与分界。

### SLOT-02 新代码目录分界
- 决策问题：七类 doc_type 各落哪个目录？`route`（`app/<seg>/page.tsx` 等）、`server-component`/`client-component`/`ui-component`、`data-access`、`domain-type`、`server-action` 的目录约定与命名后缀？新旧谱系分界线在哪？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：目录分界是 hooks（PreToolUse 路径拦截）与 implementation-review 的数据源。**分层依赖律**（`route → server-component → data-access → domain-type`；`client-component → ui-component`；`server-action → data-access`）不可被本槽位豁免，目录约定不得诱导反向依赖（如把 `data-access` 放进 `ui-component` 目录）。

### SLOT-03 内容源（MDX / CMS / DB）
- 决策问题：内容从哪来——本地 MDX（`@next/mdx` / `next-mdx-remote`）、Headless CMS（Contentful/Sanity/Strapi）、还是数据库？frontmatter 解析方案？内容文件目录？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**示例实证**——blog 用本地 Markdown/MDX + `gray-matter` 解析 frontmatter（证据 `next.js/examples/blog/pages/posts/markdown.md` 的 `title/date/description/tag/author` 头、`next.js/examples/blog/scripts/gen-rss.js` 中 `matter(content)` 与 `frontmatter.data.*`）。**生产级补充**——CMS/DB 内容源、内容 schema 校验（见 SLOT-06）示例未覆盖。无论何种来源，**内容读取与解析只能落在 `data-access`**（`server-component`/`server-action` 经由它取数），`client-component` 禁直读内容源——通用硬规则，不可豁免。

### SLOT-04 数据获取 / fetch 封装与缓存策略
- 决策问题：服务端数据获取的统一封装在哪（`data-access` 内的 fetch wrapper / ORM client）？默认缓存语义（`fetch` 的 `cache` / `next.revalidate`、`force-cache` vs `no-store`、ISR）？错误如何上抛？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**生产级补充**——示例 blog 无运行时 fetch（内容为构建期文件 + `scripts/gen-rss.js` 构建期派生，证据 `package.json` 的 `"build": "node ./scripts/gen-rss.js && next build"`）。**私有数据获取/secret 只在 `server-component`/`data-access`/`server-action`，禁 `client-component` 直取**是通用硬规则。本槽位钉缓存默认值与 fetch 封装入口；**`data-access` 不吞异常、底层错误必须上抛到调用层（由 `error.tsx`/边界收口）**亦为硬规则。

### SLOT-05 错误边界与失败路径收口位置
- 决策问题：route 段的 `error.tsx`/`not-found.tsx`/`loading.tsx` 在哪些层级提供？底层异常在哪一层转换为用户可消费错误（`data-access` 转换 / 集中 error normalizer + 调用层收口）？`server-action` 的失败返回形态（throw vs `{ error }`）？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**生产级补充**——示例未覆盖 App Router 错误边界。**每个有数据获取的 route 段必须有 `error.tsx` 兜底**是 golden-path 锁定的硬规则；本槽位只钉边界放置层级与异常转换发生的位置。失败路径是需求五要素之一，详细合同八问的「失败/边界」必须能 trace 到这里。

### SLOT-06 领域类型 / schema 校验方案
- 决策问题：`domain-type` 用纯 TS `interface`/`type` 还是 `zod`（或等价 runtime schema）？外部输入（CMS 返回、表单、route handler body）是否强制 runtime 校验？schema 与类型的单一来源（`z.infer`）？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**生产级补充**——示例 blog 无 schema 校验（`tsconfig.strict:false`，证据 `next.js/examples/blog/tsconfig.json`）。**生产基线要求 `tsconfig.strict:true`**（见 SLOT-13）。`domain-type` 位于分层最底，**不得反向依赖任何上层**；外部 untyped 输入（CMS/表单/handler）建议 runtime 校验，本槽位钉死方案与强制范围。

### SLOT-07 状态管理（none / Context / Zustand）
- 决策问题：客户端状态用什么——优先 none（server-first、URL/search params 承载状态）、React Context、还是 Zustand（或等价）？全局 store 入口文件？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**生产级补充**——示例 blog 无客户端状态库。**server-first / `'use client'` 最小化**是硬规则：能用 server-component 解决的禁止下沉到 client-component。状态库只服务于 `client-component` 链；**禁止在 `server-component` 内 import 客户端 store**。本槽位钉死方案与 store 入口。

### SLOT-08 UI 组件库（shadcn / MUI / 自建）
- 决策问题：展示型组件基于哪个库（shadcn/ui、MUI、Radix、自建 design system）？`ui-component` 的封装边界（是否允许业务组件直接用三方组件，还是必须经本项目 `ui-component` 包一层）？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**生产级补充**——示例 blog 用 `nextra-theme-blog` 主题（证据 `next.js/examples/blog/pages/_app.tsx` 的 `import "nextra-theme-blog/style.css"`、`package.json` 的 `nextra`/`nextra-theme-blog`），非通用组件库，仅作主题基线。**`ui-component` 必须纯展示、无数据获取、无业务**是分类硬约束；本槽位钉死库与封装边界。

### SLOT-09 样式方案（Tailwind / CSS Modules）
- 决策问题：样式用 Tailwind、CSS Modules、还是两者分工？是否允许 styled-jsx / 全局 CSS？全局样式入口文件与允许范围？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**样式隔离、禁全局污染**是通用硬规则（不可豁免）。**示例实证**——blog 用全局 `styles/main.css`（证据 `next.js/examples/blog/pages/_app.tsx` 的 `import "../styles/main.css"`）与 `styled-jsx`（证据 `next.js/examples/blog/theme.config.js` 的 `<style jsx>`），属示例简化、**与生产基线冲突，以生产基线为准**：生产环境全局 CSS 仅限 reset/变量/字体，组件样式必须走 Tailwind 或 CSS Modules。本槽位钉死方案与全局 CSS 白名单。

### SLOT-10 图像优化（next/image）
- 决策问题：图片是否统一走 `next/image`？远程图片域名白名单（`next.config` 的 `images.remotePatterns`/`domains`）在哪？是否允许裸 `<img>`（及例外场景）？
- 本项目取值：
- 代码证据：（如 `next.config.js`/`next.config.ts` 的 `images` 配置）
- 生效范围：
- 备注：**生产级补充**——示例 blog 未配置 `next/image`。生产基线建议 `next/image` 统一图像优化；本槽位钉死是否强制、远程域名白名单位置、裸 `<img>` 的允许例外。

### SLOT-11 认证（NextAuth / 自建 session）
- 决策问题：认证方案（NextAuth/Auth.js、自建 session、第三方 IdP）？session 读取位置？受保护 route 的鉴权拦截在哪（middleware / layout / server-action 内校验）？
- 本项目取值：
- 代码证据：（如 `middleware.ts`、`auth.ts`、`app/api/auth/*`）
- 生效范围：
- 备注：**生产级补充**——示例 blog 无认证。**secret / 私有 session 只能在 `server-component`/`data-access`/`server-action` 读取，禁 `client-component` 直取**是通用硬规则；`server-action` 的变更必须先鉴权再落 `data-access`。本槽位钉死方案与鉴权拦截位置。

### SLOT-12 数据库 / ORM
- 决策问题：是否有数据库？ORM（Prisma/Drizzle/原生）？client 单例入口文件？schema/migration 组织方式与命令？
- 本项目取值：（无数据库则显式写「无」）
- 代码证据：（如 `prisma/schema.prisma`、`lib/db.ts`）
- 生效范围：
- 备注：**生产级补充**——示例 blog 无数据库（内容为文件）。**ORM 查询只能在 `data-access` 层**，`server-component`/`server-action` 经由它访问，**禁 `server-action` 在交互/变更链里直连 ORM/远端**（通用硬规则）。本槽位钉死 ORM、client 入口与 migration 组织。

### SLOT-13 TypeScript / lint / format
- 决策问题：`tsconfig.strict` 是否为 `true`？ESLint 配置（`eslint-config-next` + 自定义规则）与 Prettier 配置在哪？type-check / lint / format 命令分别是什么？
- 本项目取值：
- 代码证据：（`tsconfig.json`、`.eslintrc*`/`eslint.config.*`、`.prettierrc*`、`package.json` scripts）
- 生效范围：
- 备注：**生产级补充**——**生产基线强制 `tsconfig.strict:true`**。示例 blog 为 `strict:false`（证据 `next.js/examples/blog/tsconfig.json` 第 7 行 `"strict": false`），**与生产基线冲突，以生产基线为准**。实现 trace 计划合同与 mutable evidence 要求 `tsc` 无 error 证据，本槽位提供其命令来源。

### SLOT-14 测试约定（Vitest+RTL / Playwright）
- 决策问题：单元/组件测试用 Vitest + React Testing Library 还是 Jest？E2E 用 Playwright 还是 Cypress？测试目录是否镜像源码结构？`server-component`/`server-action` 如何测（RSC 渲染/直接调用）？
- 本项目取值：
- 代码证据：（如 `vitest.config.ts`、`playwright.config.ts`、`__tests__/` 或 `*.test.tsx`）
- 生效范围：
- 备注：**生产级补充**——示例 blog 无测试。详细合同八问要求每个设计单元有测试映射、实现 trace 计划合同与 mutable evidence 要求 test 证据；本槽位提供测试框架、目录约定与 RSC/Action 的测试手法基准。

### SLOT-15 代码生成 / 构建期内容派生脚本
- 决策问题：构建/部署链路中有哪些自动生成或内容派生步骤（RSS/sitemap/搜索索引/类型生成）？脚本路径、触发命令、与 `next build` 的先后顺序？哪些 agent 禁止自动执行？
- 本项目取值：（无则显式写「无」）
- 代码证据：
- 生效范围：
- 备注：**示例实证**——blog 在 build 前跑 `scripts/gen-rss.js` 派生 `public/feed.xml`（证据 `next.js/examples/blog/package.json` 的 `"build": "node ./scripts/gen-rss.js && next build"`、`next.js/examples/blog/scripts/gen-rss.js` 的 `fs.writeFile("./public/feed.xml", ...)`）。本槽位钉死本项目的派生步骤与顺序；**对外写入/发布类脚本 agent 禁止自动执行**（参照通用硬规则）。

### SLOT-16 部署目标（Vercel / 自托管）
- 决策问题：部署到 Vercel 还是自托管（Node server / Docker / static export）？输出模式（`output: 'standalone'` / `export`）？这会约束 SSR/ISR/`server-action`/`route handler` 可用性。
- 本项目取值：
- 代码证据：（如 `next.config.*` 的 `output`、`vercel.json`、`Dockerfile`）
- 生效范围：
- 备注：**生产级补充**——示例 blog 默认部署形态（`next start`，证据 `package.json` 的 `"start": "next start"`）。若选 `output: 'export'`（纯静态），`server-action`/动态 `route handler`/SSR 不可用，详细设计阶段必须据此约束 doc_type 选型——本槽位是该约束的来源。

### SLOT-17 metadata / SEO 标准化
- 决策问题：`metadata` 走 App Router 的静态 `export const metadata` / `generateMetadata`，还是 Pages 的 `next/head`？站点级默认（title 模板、OG、sitemap、robots、RSS）在哪定义？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**示例实证**——blog 用 `next/head` 注入 RSS link（证据 `next.js/examples/blog/pages/_app.tsx` 的 `<link rel="alternate" type="application/rss+xml" .../>`），属 Pages Router 形态。**生产级补充**——App Router 用 `metadata`/`generateMetadata` 标准化。**`route` 段 metadata/SEO 标准化**是 golden-path 锁定项；本槽位钉死本项目的 metadata 入口与站点级默认。

### SLOT-18 存量违例清单（tech-debt 登记）
- 决策问题：已知的存量架构违例有哪些（供 review 的存量豁免判定使用：触碰存量记债不阻塞、新增违例阻塞）？
- 本项目取值：（逐条：违例描述 + 文件路径 + 违反的硬规则/槽位 + 建议偿还方式）
  - 示例条目格式：`client-component 内直读环境变量 secret | app/(dashboard)/widget.tsx | 违反「secret 仅 server 侧」硬规则 | 改为 server-component 注入 prop`
- 生效范围：全量
- 备注：本槽位是**存量豁免机制**的数据源，必须维护；清单外的违例一律按「新增」处理（阻塞）。即使为空也须在 SLOT-18 显式声明「无」（见 C6）。

---

## 2. 校验清单（writing/review 硬前置使用，C1~C6，与 `conventions/index.md` §3 同构）

> 校验项编号 `C1~C6` 与槽位编号 `SLOT-NN` 是两套独立序列：本模板槽位为 `SLOT-01~SLOT-18`（末位 SLOT-18 = 存量违例清单，单一 `SLOT-NN` 前缀、连续递增、删除留洞）。README / harness 速览里的简写 `C1~C5` 指「必须可定位取值的关键必填槽位子集」，其指向的 SLOT-NN 见 `conventions/index.md` §3 末映射。
> 装载本约定文件的 Skill 必须先执行以下校验，任一不通过即终止并提示修复：

- [ ] **C1 元信息齐全**：第 0 节四字段（站点名/包名、仓库路径、填写日期/人、取值依据）全部非空。
- [ ] **C2 槽位完整 + 待定受控**：SLOT-01 ~ SLOT-18 全部存在；标「待定」的槽位 ≤ 2，且每个待定项写明决策人与期限。
- [ ] **C3 证据可达**：每个已填槽位至少 1 条代码证据路径，且路径真实存在于仓库（不校验文件内容，但路径必须存在；SLOT-12/15 等显式声明「无」者免证据）。
- [ ] **C4 doc_type 纯净**：取值正文只用 H5 权威七类（`server-component`/`client-component`/`data-access`/`route`/`ui-component`/`domain-type`/`server-action`）；不得改名/增减/换数，不出现 flutter（controller/usecase/repository-datasource/page-entry）或 Go（transport/service/domain）类型名，也不自创 handler/provider/hook-layer 之类。
- [ ] **C5 不与通用硬规则冲突**：取值不得违反以下任一不可豁免硬规则——
  - 分层依赖律：`route → server-component → data-access → domain-type`、`client-component → ui-component`、`server-action → data-access`（禁反向/同层横跳）；
  - server-first / `'use client'` 最小化（能 server 解决禁下沉 client）；
  - 私有数据获取 / secret 只在 `server-component`/`data-access`/`server-action`，禁 `client-component` 直取；
  - `data-access` 不吞异常、底层错误必须上抛；内容/ORM 查询只在 `data-access`；
  - 样式隔离、禁全局污染；有数据获取的 route 段必须有 `error.tsx` 兜底；
  - 生产基线 `tsconfig.strict:true`。
  - （凡 SLOT 取值与示例 blog 的简化形态冲突——如 Pages Router/`strict:false`/全局 CSS——一律以生产基线为准；本项目若确为示例形态，须在对应槽位显式声明并登记 SLOT-18。）
- [ ] **C6 存量清单存在**：SLOT-18 存在（可为空清单，但必须显式声明「无」）。

---

## 3. 槽位与门禁的对应关系（参考）

| 槽位 | 谁消费 |
|------|--------|
| SLOT-01 / SLOT-02 / SLOT-16 | hooks（PreToolUse 路径/模式拦截）、概要归属表与承接索引、implementation-review |
| SLOT-03 / SLOT-04 / SLOT-12 | `data-access` 合同八问、implementation-writing/review |
| SLOT-05 | `route`/`server-component`/`server-action` 合同（失败路径与错误边界）、implementation-review |
| SLOT-06 / SLOT-13 | `domain-type` 合同、实现 trace 计划合同与 mutable evidence（`tsc` 证据） |
| SLOT-07 / SLOT-08 / SLOT-09 / SLOT-10 | `client-component`/`ui-component` 合同、样式/图像合规检查 |
| SLOT-11 | `server-action`/`route`/`server-component` 鉴权合同、安全合规检查 |
| SLOT-14 | 详细合同八问的测试映射、实现 trace 计划合同与 mutable evidence（test 证据） |
| SLOT-15 / SLOT-17 | hooks（脚本执行拦截）、`route` 的 metadata/SEO 合同、构建链检查 |
| SLOT-18 | 所有 review 的存量豁免判定 |

---

## 4. 与上游 SSOT 的衔接（导航）

- 通用方法 SSOT（分层依赖律、doc_type 七类、迷你路径、禁止清单）：`.trellis/spec/guides/golden-path.md`
- 阶段 SSOT 与详细 L2（render/interactive/data 三元组等）：`.trellis/spec/harness/*`
- 本取值文件落地路径：`.trellis/spec/conventions/project-conventions.md`
- 编号纪律：行为以 `BHV-NNN` 标题定义，设计单元以 `UNIT-<slug>` 标题定义；下游引用写裸 token，断链进不了详细/实现 Gate。本约定文件的槽位取值在合同八问的「依赖声明 / 项目约定引用」处被裸 `SLOT-NN` 引用。
