# H5/Next.js 详细设计分章写作指南（references）

> 编排层产物：只补充**逐类写法细则、章节模板与操作步骤**，不替代 L1/L2。规则正文与完成条件以
> `.trellis/spec/harness/detail/detail-structure-single-source.md`（L1）、`detail-type-server-component.md` /
> `detail-type-client-component.md` / `detail-type-data-access.md`（v1 三元组 L2）与
> `.trellis/spec/guides/golden-path.md`（通用方法 SSOT）为准。冲突时 **L1 > L2 > references > SKILL.md**。
> 平台基线：Next.js（**App Router 生产形态为目标**）+ React + TypeScript(strict)。`doc_type` 全程只用 L1 §1
> 钉死的 H5 七类 token：`server-component` / `client-component` / `data-access` / `route` / `ui-component` /
> `domain-type` / `server-action`。**禁止照抄 flutter（page-entry/controller/usecase/repository-datasource/...）
> 或 backend（Entry/Biz/Utility/Data/...）的类型名**。

## 0. 本文件定位

- 目标：把"按当前批次命中装载 → 逐章八问展开 → 批内自动审修 → 层级 checkpoint"变成稳定可重复的写作流水线。
- 范围：装载矩阵、章节模板、七类写法细则、批次收敛操作。**不**重定义八问/粒度/编号/checkpoint 完成条件（回 L1）。
- 不做：一轮全量生成全部章节；输出审核矩阵或二元放行结论（那是 `h5-design-detail-review` 的事）。
- 示例实证纪律：参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是 **Pages Router + Nextra + MDX +
  gray-matter** 的轻量 starter，仅作**内容模型基线**。凡涉及路由段 / RSC 边界 / 严格类型 / 缓存重验证 / SEO 标准化 /
  变更 / 测试，一律按 **[生产级补充]** 写并标注证据来源；只有 frontmatter 形态 / MDX 取数 / 内容字段语义可标
  **[示例实证]**（完整逐项对照见 L1 §10）。

## 1. 规范装载矩阵（按当前批次命中装载，**不全量装**）

| doc_type | L2（命中才读） | l2_status | 额外必读 |
|----------|---------------|-----------|---------|
| `domain-type` | 无（pending，按 L1 §3 八问） | pending | golden-path §domain-type 迷你路径 + §2.7（TS strict）+ §2.2 序列化边界 |
| `data-access` | `detail-type-data-access.md` | v1 / full | golden-path §data-access 迷你路径 + §2.3（数据获取/缓存/不吞错） |
| `server-action` | 无（pending，按 L1 §3 八问） | pending | golden-path §server-action 迷你路径 + §2.2 secret 边界 + L1 §5.4 变更层 checkpoint |
| `server-component` | `detail-type-server-component.md` | v1 / full | golden-path §server-component 迷你路径 + §2.2/§2.3 + §2.6 metadata |
| `client-component` | `detail-type-client-component.md` | v1 / full | golden-path §client-component 迷你路径 + §2.2 序列化边界 + §6 槽位 C3（状态管理） |
| `ui-component` | 无（pending，按 L1 §3 八问） | pending | golden-path §ui-component 迷你路径 + §2.4 样式隔离 |
| `route` | 无（pending，按 L1 §3 八问） | pending | golden-path §route 迷你路径 + §2.5 段约定 + §2.6 metadata/SEO |

装载纪律（强制，对应 SKILL.md「装载顺序」第 4 步）：

- **只对当前小批次命中的 doc_type 读对应 L2**；不得为后续章节预加载未命中的 L2、无关需求证据或无关示例。
- pending 四类（`route`/`ui-component`/`domain-type`/`server-action`）无独立 L2，按 L1 §3 合同八问展开，章节文件头标
  `l2_status: pending`；full 链命中 pending 类型时，design-main.md 须有 L1 §2.5 的 `L2豁免：<doc_type> 理由：… 风险：…
  补齐计划：…` 声明（无豁免 → 停止，见 WX-6）。
- 命中 v1 类型（`server-component`/`client-component`/`data-access`）时，章节文件头标 `l2_status: v1`，并叠加对应 L2 的
  "合同八问的类型特化"与"类型硬规则"。

## 2. 章节正文模板（L1 §4 骨架的操作版）

新章节从此模板起稿（full 链=`chapters/<slug>.md`；light 链=`design.md` §2 内一章，可压缩小节层级）。**模板是表达
形式，L1 §3 八问是完成条件，二者必须同时满足**（映射见 L1 §4 末表）。

````markdown
# <chapter_target> 详细设计

> doc_type：<七类之一> ｜ l2_status：v1 / pending（pending 须有 L2豁免）
> 承接索引：design-main.md 第 7 节 <chapter_target> ｜ 返回：[design-main](../design-main.md)
> 项目约定：route_mode=App ｜ 内容源=<MDX/CMS/ORM-DB> ｜ 状态=<none/Zustand/Context> ｜ 样式=<Tailwind/CSS Modules>（见 L1 §6 槽位 C1~C5）

## 1. 单元职责
本章承载的 `UNIT-<slug>` 清单与一句话职责；与依赖/被依赖单元的关系（调用谁的什么行为、被谁调用），
方向须符合 L1 §2.1 依赖律（服务端链 `route → server-component → data-access → domain-type`；交互链
`client-component → ui-component`；变更链 `server-action → data-access`）。

## 2. 行为定义
### 2.1 行为清单（每行为一行：行为名 + 简述 + 承接的 BHV 编号）
### 2.2 接口定义（TypeScript 签名级，**禁止超过签名级的实现代码**）
```ts
// 按 doc_type 写对应签名（示例见 §3 各类要点）
```

## 3. 核心数据结构
### 3.1 数据模型 / Schema（TS type/interface/zod schema 签名级；序列化与校验方案按 L1 §6 槽位）
### 3.2 错误类型表
| 错误名 | 错误码/枚举 | 语义 | 上抛/收口位置（error.tsx / data-access 转换点 / action 返回） |

## 4. 逐行为设计（每个行为一小节）
### 4.x <行为名>
- 函数签名（TypeScript）
- 行为简述（一句话 + 承接 `BHV-NNN`）
- 输入参数表：| 参数 | 类型 | 取值域/约束 | 必填 |（RSC 含 `params`/`searchParams`；client 含 props/event）
- 输出表：| 返回值/渲染产物/发射值 | 类型 | 语义 |
- 执行流程（mermaid sequenceDiagram，参与者用真实组件名，步骤编号）
- 流程详述（编号列表，与图中编号一一对应，满足 L1 §3.1 粒度四条）
- 异常处理表：| 异常情况 | 处置（重试/降级/上抛 error.tsx/提示） | 错误转换位置 |

## 5. 状态 / 边界管理
- client-component：状态字段（含初始态）+ 状态转移（stateDiagram 或转移表）+ 写 owner 声明；三态（loading/success/error）显式。
- server-component / route：写 `N/A：server_no_client_state`，并声明数据获取/缓存重验证边界（引用，不决定 TTL）。
- 'use client' 边界声明：本单元是否含 `'use client'`、为何在此分割、哪些子树留在服务端。

## 6. 路由 / 渲染 / SEO（route 类必含；其余类写 N/A）
段约定（page/layout/loading/error.tsx 职责切分与触发）、metadata/generateMetadata（title/description/og）、
generateStaticParams/动态段策略、缓存与重验证（force-static / revalidate / dynamic）、错误边界落地。

## 7. 测试映射
| BHV/行为 | 测试层（unit/component-RTL/e2e-Playwright/manual） | 测试点（成功 + 全部失败路径逐条） |

## 8. 不得补造清单
本单元不拥有的决策逐条列出（含 L1 §2.1 依赖律禁止越层的反面项），写成指向式（"…属 <doc_type>/<UNIT>"）。
````

## 3. 七类写作要点（按 L1 §2.3 / §5.2 写作顺序：合同层 → 路由层）

每类共用 §2 模板骨架；以下只列**类型要点、签名样式与易错点**。命中 v1 类型时另读对应 L2 的"类型特化"与"硬规则"。

### 3.1 `domain-type`（合同层，pending，按 L1 §3 八问 + golden-path §domain-type）

- **先固化合同**：TS 类型/interface/zod schema/领域模型是全链被依赖的叶子，**第一个写**（L1 §5.2 第 1 层）。
- §2.2 接口定义写 zod schema + `z.infer` 推导的类型签名（上限到签名级，不写解析实现）。跨 server→client 的对象在此
  定义"可序列化"形态（基本类型/纯对象/数组/Date；不含函数、class 实例、Symbol——对齐 golden-path §2.2 序列化边界）。
- 八问之 4：**不 import 任何其他六类**；八问之 8 必列"零副作用、零 I/O、零 React——不拥有取数/渲染/状态"。
- 易错点：在 `domain-type` 写校验失败的处置流程（属 `data-access`/`server-action` 的错误收口）；反向 import 运行层
  （L1 §2.1 反向边 → fail）。frontmatter 字段语义可标 [示例实证]（见 §5 证据）。

### 3.2 `data-access`（数据层，v1，按 L2 `detail-type-data-access.md`）

- 合同**从领域需要出发**（不从接口/表结构出发）；按内容源（MDX / CMS·API / ORM-DB，对应 L1 §6 槽位 C2）分别列取数
  合同、缓存/重验证策略、错误转换点（`[SLOT-04]`）。
- §2.2 接口定义写取数函数签名（如 `getAllPosts(): Promise<Post[]>`、`getPostBySlug(slug: string): Promise<Post | null>`）。
- **缓存语义显式化**（golden-path §2.3）：每个 fetch 写明 `cache: 'force-cache' | 'no-store'` 或 `next: { revalidate: <秒> }`；
  禁依赖隐式默认。错误**向上抛**交 `error.tsx` 或调用方，**禁止 catch 后返回 `[]` 冒充成功**。
- 私有数据/secret 边界：可读私有 env/凭证（建议 `import 'server-only'` 保险栓），返回值必须可序列化、按 `domain-type`
  收敛。八问之 8 必列"不被 `client-component`/`ui-component` import；不反向 import `server-component`/`route`"。
- 易错点：把"读 MDX/CMS/ORM"的实现细节当成签名级（上限是签名 + 关键结构）；缓存 TTL 决策漂移到 `server-component`。

### 3.3 `server-action`（变更层，pending，按 L1 §3 八问 + golden-path §server-action）

- 两种形态：Server Action（`'use server'` 函数，表单提交/写操作）与 route handler（`app/api/.../route.ts` 的 `GET/POST`，
  如 RSS/webhook）。§2.2 写 action 签名（如 `submitComment(formData: FormData): Promise<ActionResult>`）。
- 八问之 2：入参**必经 zod 校验**，回指 `domain-type` 的 schema（如 `CommentInput`）；鉴权在此把关。
- 八问之 6（后置结果）：变更后 `revalidatePath('/posts/[slug]')` / `revalidateTag(...)` / `redirect(...)`，**逐条写明消费方**
  （哪个 `server-component`/`route` 的缓存因此失效）。
- 八问之 4：**只依赖 `data-access` + `domain-type`**，不直连 DB driver、不重复写 `data-access` 逻辑；八问之 8 必列"不被
  `data-access` 反向依赖（变更链反向 → fail）"。failure 路径见 L1 §3.1 正例（`INVALID_INPUT`/`DUPLICATE`/网络错误上抛）。
- 易错点：在 action 内直连 DB 绕过 `data-access`（越层）；secret 写进返回给 client 的结果对象。

### 3.4 `server-component`（渲染层，v1，按 L2 `detail-type-server-component.md`）

- **默认形态、server-first**：文件**不写** `'use client'`；可 `async function`，在组件内 `await` `data-access` 取数。
- 八问之 2 必写"数据获取入参（`params`/`searchParams`，类型来自 `domain-type`）→ 经 `data-access` 取数 → 渲染产物（JSX）"
  链；向下传子组件的 props **逐项标注**（名称/类型/是否跨 server-client 边界/是否可序列化）。
- 八问之 3：写 `N/A：server_no_client_state`（无 `useState/useEffect/useRef`/事件/浏览器 API——出现任一即类型误判 P1），
  并声明缓存/重验证边界为"引用 `data-access`/`route` 决策"，不决定 TTL。
- 八问之 5：取数失败**向上抛**交就近 `error.tsx`；资源不存在调 `notFound()` 触发 `not-found.tsx`；不 `try/catch` 吞错渲染空白。
- 八问之 4：只调 `data-access`（唯一取数入口）+ `domain-type` + 子 `server-component` + `ui-component` + 把 `client-component`
  当子节点渲染（只透传可序列化 props，**不传函数/secret**）；八问之 8 列"不决定交互/缓存 TTL/数据源/metadata 全集"。
- 易错点：内联裸 `fetch`/ORM/`fs`+`gray-matter` 取数（应收敛进 `data-access`）；把 `getStaticProps` 心智当 RSC 写（[混用即缺陷]）。

### 3.5 `client-component`（交互层，v1，按 L2 `detail-type-client-component.md`）

- **`'use client'` 置文件首行**，只标在真需交互（状态/事件/hooks/浏览器 API）的**最小叶子**；§5 写 `'use client'` 边界声明
  （为何在此分割、哪些子树留服务端）。
- §5 状态节是一等公民：列状态字段（含初始态）+ 状态转移（stateDiagram 或转移表）+ 写 owner（回指概要归属表行，与 L1 §6
  槽位 C3 状态管理一致）+ 三态（loading/success/error）映射。
- 八问之 4：**只依赖 `ui-component`（+`domain-type` 仅类型导入）**；**禁止** import `server-component`/`data-access`（污染
  client bundle，L1 §2.1）；数据由 server 经 props 注入或调用暴露的 `server-action` 引用。
- 八问之 8 必列"不取私有数据/不读 server secret（§2.2 边界红线）；props 必须可序列化"。
- 易错点：在此 `useEffect + fetch` 取首屏私有数据；把整页/大块标 `'use client'`（应下推到最小交互叶子）。

### 3.6 `ui-component`（展示层，pending，按 L1 §3 八问 + golden-path §ui-component）

- **纯展示叶子**：props 进、JSX 出，**零数据获取、零业务逻辑、零状态**；不标 `'use client'`（可被 server/client 同时复用）。
- §2.2 写 props 类型签名（如 `PostCard(props: { post: Post }): JSX.Element`）；样式按 L1 §6 槽位 C5（Tailwind / CSS Modules）
  局部隔离，**禁全局污染**（禁裸全局 class 选择器、禁跨组件样式泄漏）。
- 八问之 4 反面项必写："不调用 `data-access`——属 `server-component`/`server-action`；不依赖 `client-component`（交互链反向
  → fail）"。八问之 8 列"不决定取数策略/缓存/业务分支——若需局部交互态，应升级为 `client-component` 或拆分"。
- 易错点：在 `ui-component` 写 `useState`/`fetch`/业务 if 分支（命中即应改归他类）。

### 3.7 `route`（路由层，pending，按 L1 §3 八问 + golden-path §route）

- §6（路由/渲染/SEO）是本类主体：写**段约定**——`page.tsx`(页面) / `layout.tsx`(布局壳) / `loading.tsx`(Suspense
  fallback) / `error.tsx`(错误边界，**必须 `'use client'`**) / `not-found.tsx`，逐文件写职责切分与触发条件。保留文件名不可改名。
- **SEO 走 metadata**（golden-path §2.6）：静态 `export const metadata: Metadata`；动态参数用
  `export async function generateMetadata({ params }): Promise<Metadata>`，覆盖 `title/description/openGraph/alternates`（RSS）；
  **不手写 `<head>`/`<meta>`**。动态段声明 `generateStaticParams` 策略；缓存写 `force-static`/`revalidate`/`dynamic`。
- 八问之 5：渲染失败路径必落 `error.tsx`（错误边界）或下层 `data-access` 错误转换点，不静默吞错。
- 八问之 4：数据编排**下放给 `server-component`**（简单页 `page.tsx` 自身充当 server-component，此时它**就是**
  server-component，不算跳层）；**禁止**在 route 段跳过 server-component 直堆复杂取数逻辑。
- 易错点：改 route 保留文件名；`error.tsx` 不标 `'use client'`；手写 `<Head>` 做 SEO（[示例实证] 的 Pages Router 写法，
  生产改 metadata 对象）。

## 4. 批次收敛与 checkpoint 操作细则

- **批内自动 review 检查单**（不等用户；逐项打钩后才置 `chapter_status`，对应 L1 §5.3）：
  1. **模板节齐全**：§2 模板 1~8 节齐全（含 `N/A：server_no_client_state` 等显式声明），非空。
  2. **八问逐 UNIT 可回指**：每个 `### UNIT-<slug>` 八问非空且满足 L1 §3 括号内可验证信号；命中 v1 类型时叠加该 L2
     "类型特化"。
  3. **粒度抽查**：任选一个行为按 L1 §3.1 四条逐条判（可直接实现 / 明确调用关系 / 完整调用链 / 粒度一致）；对照 §3.1 正例
     `submitComment`（有调用对象、有失败分支、有 owner、有后置消费方）vs 反例。
  4. **编号断链**（L1 §3.2）：`BHV-NNN` 存在于 prd（无幽灵 BHV）、无悬空行为、无幽灵 `UNIT-<slug>`、无重号、无方向违例编号；
     下游引用一律裸 token。
  5. **依赖与归属一致**（L1 §2.1）：八问之 4 的依赖出现在概要架构图/归属表中，方向符合服务端链/交互链/变更链。
  6. **硬规则**（L1 §2.2）：TS strict、server-first、私有数据/secret 边界、route 段约定、metadata/SEO、样式隔离、错误边界。
  7. **L2 差异规则**：命中 v1 类型时逐条核对该 L2 的"类型硬规则"与判级。
- **修复闭环**（L1 §5.3/§9）：有 finding → 判定修订形态（局部修订 / 文档级重构）→ 直接修复 → 复查受影响的行为/依赖/跨章
  引用；当前批所有规则均有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。**不用固定次数的
  clean review 作为通过条件。** 同一 finding 修复 2 轮仍不收敛 → 按 SKILL.md 强制约束 17 升级用户，不带病置 passed。
- **层级 checkpoint**（L1 §5.4）操作：每完成一个层级（合同层/数据层/变更层/渲染层/交互层/展示层/路由层）→ 列出该层全部
  `UNIT-<slug>` → 跑对应核对项 → 失效项标注到章节 → 回批次重走审修闭环。**合同层 checkpoint 通过前不开始数据层批次。**
- **受影响章节复查**：本批修改触及已完成章节的引用时复查闭合；层级 checkpoint 或最终复审修改了已通过章节 → 其通过状态
  失效，重新进入当前小批次写审修闭环。
- 单章/单批通过 ≠ 全目录通过；最终目录级复审仍由 `h5-design-detail-review` 执行（写作期不输出审核矩阵或二元放行结论）。

## 5. 示例素材证据（blog starter，仅 [示例实证] 内容层基线）

写作引用示例时只用于佐证"内容模型 / frontmatter 形态 / MDX 取数"，证据路径：

- frontmatter 字段 `title/date/description/tag/author`：`/Users/devSC/Documents/MyProject/next.js/examples/blog/pages/posts/pages.md`、
  `pages/posts/markdown.md`（真实 frontmatter 块实证）；page-type frontmatter `type/title/date` 见 `pages/index.mdx`、`pages/posts/index.md`。
- `gray-matter` 解析 frontmatter + 构建期文件读取（`fs.readdir(pages/posts)` 跳过 `index.` + `matter(content)` 取
  `data.title/date/description/tag/author`）：`scripts/gen-rss.js`。**这是 `data-access` 取数与 `server-component` 文章索引渲染
  的真实数据模型来源**（生产里收敛进 `data-access`，server-component 只消费返回的领域模型）。
- 依赖 `nextra`/`nextra-theme-blog`/`gray-matter`/`rss`、build 脚本 `node ./scripts/gen-rss.js && next build`：`package.json`。
- 手写 `<Head>`（RSS link / font preload）：`pages/_app.tsx`；`<style jsx>` 全局样式：`theme.config.js`。
- TS 宽松配置 `strict: false` / `target: es5` / `typescript ^4.7.4`：`tsconfig.json`（**生产基线一律 `strict: true`，不沿用**）。

完整的"示例实证 vs App Router 生产级补充"逐项对照见 L1 §10；成稿样例见 `examples/`。

## 6. 禁止事项（写作期红线速查，详见 SKILL.md 强制约束 + L1 §9）

1. 一轮全量生成全部章节（每批 ≤3 章，批内审修后才进下一批；违反 → L1 §8 G7 拦截、§9.2 文档级重构）。
2. 越过签名级写实现代码/伪代码（TS 方法签名、数据结构/zod schema 定义为上限）。
3. 补造概要归属表之外的结构、改 owner / 技术决策 / scope；`technology_decision_handoff[]` 中"未选定"的决策私自拍板。
4. 把"见概要"当八问答案（每问就地作答，可引用但须有本地结论）。
5. 跳过失败路径的测试映射（八问之 7 须覆盖成功 + 全部失败路径）。
6. 用 backend/flutter 类型名替代 L1 §1 七类 token（doc_type 漂移红线）。
7. 把私有数据获取/secret 下沉到 `client-component`/`ui-component`（L1 §2.2 边界红线）。
8. 引入违反 L1 §2.1 依赖律的反向边或越层调用（如 `data-access → server-component`、`ui-component → client-component`）。
9. 把 blog starter 的全局 CSS / `strict: false` / `getStaticProps` / 手写 `<Head>` 当生产合同（示例实证 ≠ 生产合同，L1 §10）。
10. 写作结果输出审核矩阵或二元放行结论（送审交 `h5-design-detail-review`）。
