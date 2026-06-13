# L2 类型规范：data-access（数据访问合同）

> 从属于 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；本文件只写 `data-access` 类型的差异规则，与 L1 冲突时以 L1 为准。
> golden-path 对应：`.trellis/spec/guides/golden-path.md` §数据获取（fetch/cache/revalidate）、§内容源（MDX/CMS）、§分层依赖律、§server-first 边界。
> doc_type 取值严格使用 H5_BRIEF 钉死的权威七类（`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`）；本文件覆盖其中第 3 类 `data-access`。**勿照抄 flutter（repository/datasource）或 Go 的类型名**——本文出现 repository/datasource 仅作"等位参照"，不是本平台的合同类型名。

## 适用对象

数据访问层：屏蔽"数据从哪来、怎么取、怎么缓存、错误怎么转换"的全部细节，对上层（`server-component` / `server-action`）暴露**类型化的域模型**（域模型本身归 `domain-type`，本层只声明返回它、不定义它）。

覆盖三类来源适配（单文件可只含其一，多来源必须分别列合同）：

- **内容源（MDX / Markdown）**：文件系统读取 + frontmatter 解析 + 正文编译。本平台 v1 内容模型基线即此类（next.js blog 示例实证：`gray-matter` 解析 frontmatter）。
- **CMS / 远程 API**：`fetch` 封装 + Next.js fetch 缓存（`cache` / `next.revalidate` / tag）。
- **ORM / DB 查询**：数据库读取封装（项目约定槽位 `[SLOT-DB]` 选定 ORM 后展开）。

**不适用**（划清边界，越界即归错层）：

- 数据的"变更写入 / 表单提交 / 撤销重验证（`revalidatePath` / `revalidateTag`）"——归 `server-action`，本层只提供被其调用的读封装与查询封装。
- "渲染编排、把数据传给组件树、组合多个 data-access 调用"——归 `server-component`。
- 域模型 / zod schema 的定义本身——归 `domain-type`，本层 import 并复用，**不在此新造类型**。
- `'use client'` 交互组件**禁止直接调用本层任何函数**（私有数据获取/secret 不下放客户端，H5 硬规则）。

## 合同八问的类型特化

> 编号纪律：每个设计单元以 `### UNIT-<slug>` 定义（kebab-case）；承接行为引用裸 `BHV-NNN`；下游（`server-component` / `server-action`）引用本层一律写裸 `UNIT-<slug>` token。

1. **承接哪些行为**：数据读取、内容解析、缓存命中/重验证、查询类行为，逐条引用 `BHV-NNN`（必须存在于 prd；幽灵引用或无承接行为 = 断链 P1）。**变更类行为不在此**（属 `server-action`）。
2. **输入 / 输出 / 错误结果**：
   - **逐函数签名级**列出 TS 签名（函数名 / 参数类型 / 返回类型）。返回类型**必须是 `domain-type` 域模型**（如 `Promise<Post[]>` / `Promise<Post | null>`），**禁止把原始 frontmatter（`{ [key: string]: any }`）、CMS 原始 JSON、ORM 行模型直接外泄给上层**——「原始数据 → 域模型」的映射（mapper）责任在本层，必须独立声明 mapper 函数。
   - 输入有参数表（参数 / 类型 / 取值域 / 必填）；输出有返回表（返回值 / 类型 / 语义，含"未命中返回 `null` 还是抛"）。
   - 错误 = **底层异常 → 业务错误的映射表**，精确到这一级别：`ENOENT（文件不存在）→ ContentNotFoundError`、`fetch 非 2xx（res.ok === false）→ ContentSourceError`、`zod parse 失败 → ContentSchemaError`、`gray-matter 抛 YAML 解析错 → ContentParseError`。
3. **读取 / 写入哪些状态**：
   - 本层**对业务状态只读、不持有 React 渲染状态**（无 `useState`/无组件状态——那属 `client-component`）。
   - 唯一"有状态"面是**缓存语义**：必须逐函数声明 fetch cache 策略——`cache: 'force-cache'`（默认，静态）/ `cache: 'no-store'`（每次实时）/ `next: { revalidate: <秒> }`（ISR 时间窗）/ `next: { tags: ['<tag>'] }`（按 tag 失效）。内容源（文件系统读取）说明构建期静态化 vs 运行期读取的边界。
   - **幂等性声明**：同输入重复调用语义必须一致（读封装天然幂等；带 `no-store` 的实时读说明"每次返回最新、非幂等于时间维度"）。
4. **调用哪些依赖，不调用哪些依赖**（正反两面都写，防越层）：
   - **可调用**：`fs`/`path`（内容源）、`gray-matter`（frontmatter 解析）、MDX 编译器（`next-mdx-remote` / `@next/mdx`，按 `[SLOT-CONTENT]`）、全局 `fetch`（CMS）、ORM client（按 `[SLOT-DB]`）、`domain-type` 的 zod schema/类型、环境变量中的 secret（仅服务端）。
   - **禁止调用（越层 = P1）**：`server-component`（反向依赖）、`server-action`（反向依赖）、`client-component` / `ui-component`、`react`/`react-dom` 渲染 API、`next/navigation` 的客户端 hook、其它 data-access 单元间的环形/双向依赖。
   - **server-only 强制**：本层文件必须 `import 'server-only'`（构建期保证永不被打进客户端 bundle）；含 secret 的函数严禁被 `'use client'` 文件 import（H5 硬规则）。
5. **失败如何收口**（编排策略必须显式，不许一句话带过）：
   - **远程失败回落策略必须显式**：CMS `fetch` 失败时——是回落到本地内容快照、还是抛 `ContentSourceError` 让上层 `error.tsx` 兜底、还是返回 `null` 由 `route` 渲染 `not-found`——三选一明确写出，并写明对缓存的影响（失败不写缓存）。
   - **缓存过期/重验证策略**：`revalidate` 窗口、`revalidateTag` 触发方（注明触发方是 `server-action`，本层只声明 tag 契约）。
   - **错误转换位置遵循 `[SLOT-ERR]`**：本层**不吞异常**——底层异常必须转换为业务错误类型后**上抛**（datasource 等位层不得 `catch` 后静默返回空）；区分"无数据（返回 `null`/空数组，是正常态）"与"出错（抛业务错误）"，二者语义不可混淆。
6. **产生哪些事件 / 后置结果**：
   - 缓存写入/命中（fetch cache 标记）、构建期静态生成产物（如 `generateStaticParams` 消费本层的 slug 列表）、派生产物（如 RSS feed 由构建脚本消费本层解析结果——next.js blog 示例 `scripts/gen-rss.js` 即用 `gray-matter` 读 frontmatter 产出 `public/feed.xml`，本层应把"列文章 + 取 frontmatter"沉淀为可被脚本与 `route` 共用的函数）。
   - 逐条写明消费方（哪个 `server-component` / `route` / 构建脚本消费本函数返回）。
7. **哪些测试验证它**（映射到测试分层，按 `[SLOT-TEST]`）：
   - 解析/映射逻辑（frontmatter → 域模型、zod 校验）= unit test（Vitest，喂固定 fixture MDX 字符串，断言域模型）。
   - 缓存/重验证策略 = unit test（mock `fetch`，断言传入的 `cache`/`next` 选项）或集成测试。
   - 错误映射表**逐条有用例**（`ENOENT` → `ContentNotFoundError`、非 2xx → `ContentSourceError`、schema 不符 → `ContentSchemaError`），覆盖成功路径 + 全部失败路径。
   - 不在本层测 UI 结构（归 `ui-component`/`server-component` 测试）。
8. **哪些内容不得在此补造**：
   - 不实现业务规则 / 渲染编排（属 `server-component`）；不实现变更与重验证写动作（属 `server-action`）。
   - 不新增 prd / 概要归属表之外的内容源、表、接口（回概要技术决策承接，禁详细阶段补造）。
   - 不在此定义域模型 / zod schema（属 `domain-type`，本层只 import）。
   - 不在此决定 UI 错误文案 / 占位（属 `server-component` / `route` 的 `error.tsx`）。

## 类型硬规则（golden-path 锁定）

- **server-only**：文件首行 `import 'server-only'`；TS strict（`tsconfig` `strict: true`，**不沿用 blog 示例的 `strict: false`**——见下"示例实证 vs 生产级补充"）；函数返回类型显式标注，禁 `any` 外泄。
- **域模型边界**：原始数据（frontmatter / CMS JSON / ORM 行）一律先过 `domain-type` 的 zod schema 校验，再映射为域模型；mapper 独立函数，可单测。frontmatter 类型来自 blog 示例的 `frontmatter.data.{title,date,description,tag,author}` 字段族（实证），但**生产级须用 zod 收紧**，不接受 `any`。
- **缓存策略显式**：每个数据获取函数必须在合同里写明 fetch cache 取值（`force-cache` / `no-store` / `revalidate` / `tags`），无默认靠猜；内容源函数写明"构建期静态读 vs 运行期读"。
- **错误不吞、必上抛**：datasource 等位层（最贴近 `fs`/`fetch` 的函数）禁 `catch` 后返回空；业务错误转换位置统一在 `[SLOT-ERR]`。
- **secret 隔离**：API key / token / 连接串只在本层经环境变量读取，**禁出现在返回值**、禁被客户端 import。
- **多来源分文件 / 分函数**：内容源、CMS、ORM 三类来源的封装分别独立，mapper 各自独立；单项目内目录与命名按 `[SLOT-DATA-DIR]` 统一。
- **App Router 形态**：以 App Router RSC 内的 `async` 数据获取 + Next.js 扩展 `fetch` 为 golden-path 形态；**不使用** `getStaticProps` / `getServerSideProps`（那是 Pages Router，blog 示例属之，仅作内容模型参照，不作生产形态）。

## 示例实证 vs 生产级补充（必须区分）

| 维度 | next.js blog 示例实证（Pages Router + Nextra + gray-matter） | App Router 生产级补充（golden-path 以此为准） |
|------|------|------|
| 内容解析 | `matter(content)` 取 `frontmatter.data.{title,date,description,tag,author}`（`scripts/gen-rss.js` 实证） | 同样用 `gray-matter` 解析，但 `.data` 必经 `domain-type` zod schema 校验后映射域模型，禁 `any` 外泄 |
| 文件读取 | `fs.readdir`/`fs.readFile` 读 `pages/posts/*.mdx`，`name.startsWith("index.")` 过滤 | `data-access` 函数封装"列 slug / 按 slug 取单篇"，供 `route` 的 `generateStaticParams` 与构建脚本共用 |
| 类型严格度 | `tsconfig.json` `strict: false`（示例故意放松） | TS **strict: true**，返回类型显式，不接受示例的宽松配置 |
| 数据获取范式 | Pages Router（无 App Router fetch 缓存语义；RSS 走构建脚本） | App Router RSC `async` + 扩展 `fetch`（`cache`/`next.revalidate`/`tags`），ISR/标签重验证 |
| 缓存 | 示例无显式 fetch cache（静态站点构建期产出） | 每函数显式声明缓存策略；CMS 走 `revalidate`/tag，内容源走构建期静态化 |

## 好 / 坏例子（要点，grounded 在 blog 的 gray-matter / gen-rss）

- ✅ 好（内容源 `UNIT-post-content-source`）：`getAllPosts(): Promise<Post[]>` 合同写明"`fs.readdir` 列 `content/posts/*.mdx` → 过滤 `index.*` → 逐篇 `gray-matter` 解析 frontmatter → 经 `PostSchema`（domain-type）zod 校验 → 映射 `Post` 域模型；构建期静态读，无运行期 IO"；`getPostBySlug(slug)` 写明"`ENOENT → ContentNotFoundError`，调用方决定渲染 `not-found`"；mapper `toPost(raw)` 独立可单测；文件含 `import 'server-only'`；返回 `Post` 不外泄 `frontmatter.data`。
- ✅ 好（CMS `UNIT-cms-fetch`）：`getFeaturedPosts(): Promise<Post[]>` 写明 `fetch(url, { next: { revalidate: 300, tags: ['posts'] } })`，「非 2xx（`res.ok === false`）→ 抛 `ContentSourceError`，不写缓存」，secret 经 `process.env.CMS_TOKEN` 仅服务端读取且不入返回值；`revalidateTag('posts')` 的触发方注明为 `server-action`。
- ❌ 坏：函数合同写「负责文章数据」一句话带过（无签名、无缓存策略、无回落策略）；`getAllPosts` 直接 `return matter(content).data`（外泄原始 frontmatter `any`，无 zod、无域模型映射）；`catch` 掉 `fs`/`fetch` 错误后 `return []`（吞错，混淆"无文章"与"读失败"）；在 `'use client'` 组件里 import 本函数（secret 与 server IO 下放客户端 = P1）；用 `getServerSideProps` 取数（Pages Router 范式，违反 App Router golden-path）；在本层定义 `Post` 类型而非 import `domain-type`（越界补造类型）。
