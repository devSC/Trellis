---
name: h5-design-overview-writing
description: 用于撰写 Guru H5/Next.js 平台（App Router 生产形态：Next.js + React + TypeScript strict、server-first、RSC 默认 + 'use client' 最小化）概要设计文档。按"判轨与设计包骨架、技术栈与约束确认（project-conventions C1~C5）、行为枚举（BHV 编号，按用户操作/系统反应（渲染与数据获取）/失败路径（error/notFound 边界）/生命周期与导航四类）、owner 归属判定（三问 + 分层依赖律自检，落 route/server-component/client-component/data-access/server-action/ui-component/domain-type 七类 doc_type）、架构总览人审视图（一句话架构/分层架构图/路由与边界图/核心 UC 表/UC 承接表/时序图策略表）、technology_decision_handoff 技术决策承接清单（含 credential strategy）、详细设计承接索引（doc_type 七分类，逐章落 chapters/<slug>.md）、架构就绪自检 G1~G8"的顺序推进；把概要写到"详细设计可直接展开而不需要重新决定边界"，但不进入可编码合同层（组件 props 字段级合同/zod schema 正文/fetch 调用参数/SDK 初始化参数/metadata 字段表/env 取值/secret value 禁写）。规则唯一来源是 .trellis/spec/harness/overview/ 的 L1 SSOT 与 .trellis/spec/guides/golden-path.md；本 skill 只编排写作动作，不复写规范正文。
---

# H5 (Next.js) 概要设计撰写

> 层级契约：L1（`.trellis/spec/harness/overview/overview-structure-single-source.md`）承载章节合同、归属方法与 Gate 完成条件；`golden-path.md` 承载分层依赖律与硬红线（server-first / 'use client' 最小化 / 私有数据获取边界）；`project-conventions.md` 承载项目槽位取值；本 SKILL.md 只做装载顺序、执行规则、阶段流程与输出要求；`references/` 只承载分章写法细则、模板与示例。冲突时 golden-path 硬红线 > L1 章节合同 > project-conventions 槽位 > references > 本文件。
>
> doc_type 与分层一律以 H5_BRIEF 钉死的七类为权威（见「H5 详细 doc_type 七分类」表），**禁止照抄 flutter（controller/usecase/repository-datasource）或 Go（transport/service/repository/domain）的类型名**；本文件凡引用对标 skill，只借其编排骨架，不借其类型名。

## 目标

- 输出可评审、可追踪、可指导详细设计的 H5/Next.js 概要设计文档；每个关键章节同时落出生成动作、约束边界与可验证信号。
- 以行为驱动组织概要：先枚举行为空间（`BHV-NNN` 编号），再判定唯一 owner 归属（三问理由），组件/route 段只在行为归属后形成——禁止「先有 `PostListServer` 组件再倒推它做什么」的名词先行。
- H5 行为以「用户操作 / 系统反应（渲染与数据获取）/ 失败路径（error/notFound 边界）/ 生命周期与导航」为枚举单位；归属 owner 一律落在七类 doc_type 之一：`route`（App Router 段入口）、`server-component`（RSC 渲染 + 数据获取编排，默认）、`client-component`（'use client' 交互）、`data-access`（数据访问层）、`server-action`（变更/API endpoint）、`ui-component`（纯展示可复用）、`domain-type`（TS 类型/zod schema/领域模型）。
- 在落 owner 前先做能力泛化抽象：识别下层承接对象是在形成稳定渲染编排（`server-component`）、交互状态单元（`client-component`）、数据访问合同（`data-access`）、变更/写入合同（`server-action`）、领域类型/校验 schema（`domain-type`）、纯展示可复用件（`ui-component`，无数据获取、无业务）、route 段约定（`route`），还是只把同一能力换名下传（不抽象）。纯展示组件（`ui-component`）是可随时复用的渲染件，**不持有数据获取、不进 server-component/route 的「业务依赖」清单**，只作为展示装配出现。
- 先完成「架构总览（人审视图）」再进入索引细化：一句话架构、分层架构图、路由与系统边界图、核心 UC 表、UC 承接表、时序图策略表是架构就绪门禁（L1 §2.5），不是可选的可读性优化。分层架构图箭头方向必须符合分层依赖律（见「边界约束」）。
- 把概要写到详细设计可直接展开：承接索引为每个 owner 提供 `chapter_target` 来源锚点（full 链逐条落到 `chapters/<slug>.md` 文件名），并标注 `detail_doc_type`（七分类）与 `l2_status`（render/interactive/data 三元组已出 L2，其余四类 pending）。
- 守住概要深度边界（L1 §5）：只闭合边界、语义、链路、取舍、索引；**不写**组件 props 字段级合同、zod schema 正文、`fetch`/ORM 调用参数、SDK 初始化/调用参数、`metadata` 字段表正文、`revalidate`/cache 数值、env 项默认值与取值、cookie/session 属性、secret value——这些可编码合同由详细设计承接，概要只说明「由哪个 `chapters/<slug>.md` 展开」。
- 命中外部 provider / CMS / 对象存储 / 云服务 / 三方 API / 数据库 / 认证 provider（NextAuth）等架构显著技术选择时进入 `technology_decision_handoff[]`（含 credential strategy：不保存 secret value，只写 `api_key_env_name` / `credential_ref` / 默认凭证链 / 运行平台身份注入；私有数据获取与 secret 只在 server 侧 owner，禁 client-component 直取）。
- 在进入详细设计前完成架构就绪收敛（L1 §6 G1~G8）。

## 平台生产基线（务必先读）

H5 平台生产基线是 **Next.js App Router** + React + TypeScript(strict)。概要写作一律以此为准，下列维度为生产锁定项：

- **TS strict**：`tsconfig.json` 必须 `strict: true`，按生产 baseline 运行时。
- **App Router route 段约定**：`app/<seg>/page.tsx`、`layout.tsx`、`loading.tsx`、`error.tsx`、`not-found.tsx`、`route.ts`，归属一律以 App Router 段为准。
- **server-first 与 RSC**：默认 `server-component` 在服务端渲染 + 编排数据获取；`'use client'` 只在需交互处声明、最小化。
- **数据获取**：`data-access` 封装内容源读取（MDX / CMS / ORM-DB）；私有数据获取与 secret 只在 server 侧 owner（`server-component`/`data-access`/`server-action`），禁 `client-component` 直取。
- **变更**：`server-action`（`'use server'`）/ route handler（API endpoint）承接所有写入/变更/表单提交。
- **SEO / 边界 / 样式**：`metadata`/`generateMetadata` 标准化 SEO（禁手写 `<Head>`）、错误边界 `error.tsx`、`next/image` 图像优化、CSS Modules/Tailwind 样式隔离（禁全局污染）。

内容模型可按需建模（如 MDX 文章 + frontmatter `title/date/description/tag/author` → `domain-type` schema + `data-access` 读取；构建期 RSS 等派生产物 → route handler/构建脚本承接），但其取数、缓存、SEO、变更一律按上述生产基线落 owner，不得弱化生产硬规则。

## 与官方 trellis 工具的职责边界（务必先读，避免越权）

本 skill 是「设计**写**」——承接 `prd.md` 产出，生成概要 design 章（行为归属 + 架构总览 + 承接索引）。它与下列两个独立环节职责不重叠、不互相替代：

- **vs `trellis-brainstorm`（需求/构思阶段）**：brainstorm 负责把模糊意图收敛成 `prd.md` 的 `BHV-NNN` 行为规格、P0/P1 核心能力、失败路径与验收场景。本 skill **消费** prd，不生成 prd，不补造业务规则——prd 缺失或核心能力不可定位时只能产草稿并记显式假设，不得凭空生成 P0/P1。
- **vs 设计**审**（review evidence Gate）**：写完后由配套的 `h5-design-overview-review` skill 做 clean-context review，并用 `record-review overview` 写入当前 digest 的 clean/findings 证据；两个不同 `run_id` 的 clean review 后才可进入下一阶段（详细设计）。判的是归属是否正确、是否违反分层依赖律（server-first / 'use client' 最小化 / 私有数据获取边界）、架构视图是否就绪、承接索引是否闭合。
- **vs `trellis-check`（代码质检）**：`trellis-check` 查的是**代码层**质量——`tsc --noEmit`（strict）/ ESLint / Prettier / Vitest+RTL / Playwright 证据、secret 合规、存量违例豁免。本 skill 不产代码、不跑质检，概要阶段不输出任何编译/lint/测试证据。
- 一句话定位：**brainstorm 定「做什么」→ 本 skill 概要定「分给谁、边界在哪、谁承接展开」→ overview review evidence 判「能否进详细」→ 详细写「可编码合同」→ trellis-check 判「代码达标」**。本 skill 只占第二格，越界即停。

## 最小输入与自动补全

- 接受需求产物路径（`prd.md` / 正式需求包）、设计目标、路由边界（落在哪个 `app/<seg>/`）、内容源/数据源约定、已有草稿或 `design_package` 路径。
- 优先读取需求核心能力清单（P0/P1）与失败路径章节；不可定位时仍可产出概要草稿并记录显式假设，但**不得凭空生成 P0/P1**，不得宣称可进入详细设计。需求侧合法声明「无 P0/P1」时记录依据，不补造核心能力主线。
- 信息不足时收敛到最小可写范围，**不擅自补齐高风险业务规则**；未决问题显式列出并向用户提问（一次 1~4 个关键问题）。
- 有历史设计版本时，优先复用命名、章节和术语约定（先 `rg` 检索既有 `BHV-NNN` / `UC` / `UNIT-<slug>` / 组件名 / route 段名）。

## 执行模式（按需切换）

- **一次性交付模式（默认）**：按分阶段流程内部连续推进，一次性完成全稿或本轮目标；信息不足用显式假设，不因等待确认而阻塞。
- **共创式迭代模式**：仅当用户明确要求逐阶段确认或只看某一阶段时启用；一次只产出当前阶段内容。
- 模式必须在输出中显式标注。

## 装载顺序（硬前置，任一失败即终止）

1. 读 L1 概要 SSOT `.trellis/spec/harness/overview/overview-structure-single-source.md`；不可用 → 终止并提示先安装 guru spec 模板（`trellis init -t guru-h5-nextjs`）。
2. 读通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律 `route → server-component → data-access → domain-type`（服务端链）、`client-component → ui-component`（交互链）、`server-action → data-access`；server-first、`'use client'` 最小化、私有数据获取/secret 只在 server 侧、route 段约定、metadata/SEO 标准化、样式隔离、错误边界——这是 owner 归属判定与红线自检的基准）。
3. 读 `.trellis/spec/conventions/project-conventions.md` 并执行校验清单 C1~C5；任一不过（内容源 MDX/CMS、状态管理 none/Zustand/Context、UI 组件库 shadcn/MUI、样式方案 Tailwind/CSS Modules、测试 Vitest+RTL/Playwright、lint ESLint+Prettier、数据库、认证 NextAuth、图像优化 next/image、部署 Vercel、路由模式 App/Pages 等槽位缺失或与硬规则冲突）→ 终止并提示先填写项目约定。取值一律引用槽位（`SLOT-NN` 裸 token），不在概要另定。
4. 判轨：读 task.json `guru_chain`（`guru_after_create` 默认 `full`）。full=完整五阶段链（新路由段、新数据源接入、认证/会话、server-action 写入、内容源迁移等高风险需求）→ 走目录级设计包；light=同段内小迭代且获用户同意降级 → 任务内单文件 `design.md`。full 链确认/声明 task.json `design_package`（相对 repo root，如 `docs/design/<feature>/`）。
5. 详细阶段承接索引需要 doc_type 与 L2 状态时读详细 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；需要类型差异锚点时读已出三类 L2（render/interactive/data 三元组）`.trellis/spec/harness/detail/detail-type-{server-component,client-component,data-access}.md`（其余 `route` / `ui-component` / `domain-type` / `server-action` 为 pending，按 L1 八问展开并标注 `l2_status: pending` + `L2豁免`）。
6. 定位需求产物（`prd.md` / 正式需求包）；缺失走 L1 显式假设路径。
7. 需要分章写法细则与模板时读 `references/chapter-guide.md`；需要成稿样例时读 `references/examples/design-main-minimal.md`。

## 边界约束（概要只闭合，不展开）

- **只写概要，不写详细实现**：概要闭合「边界 / 语义 / 链路 / 取舍 / 索引」五件事；可编码合同（下列项）全部交给详细设计，概要只写「由哪个 `chapters/<slug>.md` 承接」。
  - 禁写：组件 props 字段级合同（`type PostListProps = { posts: Post[]; ... }` 级正文）、`zod` schema 正文与校验链、`fetch`/CMS/ORM 调用参数与 URL、SDK 初始化/调用参数、`metadata` 字段表正文、`revalidate`/`cache`/`fetchCache` 数值、route segment config 取值、env 前缀与默认值、cookie/session 属性、`next/image` `sizes`/`loader` 配置、secret value。
  - 可写（概要应写）：行为空间与 GWT 语义、行为→owner 归属与三问理由、分层依赖边（架构图箭头）、server/client 切分边界（哪段是 RSC、哪段需 `'use client'`）、关键取舍/ADR、技术决策承接清单（决策点 + owner + 详细落点 + credential strategy）、UC 承接链、`chapter_target → detail_doc_type` 索引。
- **分层依赖律是归属硬基准（golden-path 锁定，不可豁免）**：
  - 服务端链：`route → server-component → data-access → domain-type` 严格单向无环。
  - 交互链：`client-component → ui-component`（client 组件可装配纯展示件）。
  - 写入链：`server-action → data-access`（变更经数据访问层落库/出站）。
  - `domain-type` 可被各层共享（类型/schema 是稳定底座）；`ui-component` 纯展示、不持数据获取、不依赖 data-access/server-action。把数据获取归给 `client-component` 直取私有源、或让 `ui-component` 反向依赖 `data-access`，即归属错误，必须先回退重判。
- **server-first 与 'use client' 最小化（硬红线）**：默认 `server-component`（RSC）渲染 + 编排数据获取；`'use client'` 只在确有交互（状态/事件/hooks/浏览器 API）处声明，且下沉到最小叶子组件。把整页标 `'use client'`、或为「省事」让父级客户端化，即违反红线，归属判定阶段必须拦下。
- **私有数据获取与 secret 边界（硬红线）**：私有数据获取、API key、DB 连接、认证 secret 只能在 `server-component` / `data-access` / `server-action`；**禁** `client-component` 直接读取私有源或持有 secret（client bundle 会泄露）。需要在客户端展示的数据，必须由 server 侧获取后以 props/初始数据下传，或经 `server-action`/route handler 暴露受控接口。
- **route 段约定与外部触发边界**：App Router 段按 `page` / `layout` / `loading` / `error` / `not-found` / `route` 约定承接；架构图与 sequenceDiagram 中外部角色/浏览器请求只能进入 `route` 段（或其 `page`/`route handler`），**不能**直接调用 `data-access` / `server-action` / `domain-type`；发现直连先补显式 route 段入口。`metadata`/SEO 落 route/server-component，错误边界落 `error.tsx`（归 route），样式隔离用 CSS Modules/Tailwind（禁全局污染）。
- **生产基线不可弱化**：`strict:true`、App Router、server-first、server-action、私有数据获取边界均为生产硬规则，不可豁免——见「平台生产基线」节。
- **修订纪律**：按 L1 先判定局部修订 vs 文档级重构；发现需求缺陷回退需求阶段（brainstorm），不在概要补造业务规则；发现归属错回退第 3 章重判，不在下游补救。

## 执行规则

1. 共享规范（章节合同、图表合同、归属方法、Gate 完成条件）一律以 L1 为准，硬红线以 golden-path 为准；本 skill 与 references 不重复维护规范正文。
2. 默认一次性交付模式：按阶段内部推进，不要求用户逐阶段确认；只在出现高风险未决项时暂停提问（一次 1~4 个）。
3. 显式假设必须标注依据、影响范围、验证时点，并落盘到 `design-main.md`（或 light 链 `design.md` §概要）对应章节——不允许只在会话输出里口头声明。
4. 阶段 0 必须完成判轨落盘：full 链建立设计包骨架（`README.md` + `design-main.md` + `chapters/` 空目录）并把包路径写入 task.json `design_package`；任务内 `design.md` 只写指针 + 摘要。light 链直接写 `design.md` §概要。
5. 阶段 0 必须确认技术栈基线并明确路由边界：本任务落在哪个 `app/<seg>/`，复用还是新建 `page/layout/loading/error/not-found/route` 段，内容源（MDX/CMS）与数据源接入点，server/client 切分初判；取值（内容源、状态管理、UI 库、样式方案、测试、lint、数据库、认证、图像优化、部署、路由模式）一律引用 project-conventions 槽位 `SLOT-NN`，不在概要另定。`strict: true` 与 App Router 为生产基线。
6. 行为枚举（阶段 2）按 H5 四类顺序（**用户操作 → 系统反应（渲染与数据获取）→ 失败路径（error/notFound 边界）→ 生命周期与导航**），逐条 Given/When/Then + `### BHV-NNN <短名>` 编号标题；每条满足 L1 粒度标准（有前置、有触发/导航、有渲染或状态变化、有失败路径）；禁止从组件/route 名出发。`BHV-NNN` 创建后不复用、不重排，删除留洞。
   - ✅ `### BHV-008 渲染文章详情页` — Given 用户访问 `/posts/[slug]` When `server-component` 经 `data-access` 按 slug 读内容源 Then RSC 渲染正文 + `metadata` 注入 SEO；slug 不存在时由 `not-found.tsx` 收口返回 404。
   - ❌ `### BHV-008 显示文章` — Given 有页面 When 渲染 Then 显示。（无前置、无路由/触发、无失败路径、无数据获取语义）
7. 归属判定（阶段 3）按 L1 判定表给每条行为唯一 owner（七类 doc_type 之一）+ 三问理由（为什么属于它 / 为什么不属于别人 / 为什么需独立存在）；对照分层依赖律自检无违例（服务端链/交互链/写入链单向无环、server-first、`'use client'` 最小化、私有数据获取边界、外部触发只进 route）；一个业务状态/写入只能有一个写 owner（同一变更出现在两个 `server-action` 里 = P1，回退重判）。归属表逐行以 `BHV-NNN` 开头。
8. 命名遵守 L1：组件 = 定语 + 名词 + 角色后缀（`PostListServer` / `LikeButtonClient` / `PostCard`（ui-component）/ `getPosts`（data-access）/ `publishPost`（server-action））；route 段用 App Router 段名（`app/posts/[slug]/page.tsx`）；类型/schema = 领域名 + 角色（`Post` / `PostFrontmatterSchema`）；设计单元 `UNIT-<slug>` 体现对象 + doc_type 角色（`UNIT-post-detail-page` / `UNIT-post-list-server` / `UNIT-like-button-client` / `UNIT-posts-data-access` / `UNIT-publish-post-action`）；行为 = 动词/动词 + 宾语；list/one/get/fetch 语义区分。
9. 架构总览（阶段 5）按 L1 §2.5 六件套合同产出：一句话架构 → 分层架构图（mermaid）→ 路由与系统边界图 → 核心 UC 表 → UC 承接表 → 时序图策略表；图中组件必须与归属表一一对应，不得出现归属表之外的组件；分层架构图箭头方向必须符合分层依赖律（服务端链/交互链/写入链单向无环），并以视觉区分 server 段（RSC/data-access/server-action）与 client 段（client-component/ui-component）。
10. 时序图策略表逐 UC 声明 独立/合并/豁免；早期可用计划锚点，**送审概要 Gate 前非豁免 UC 必须回填可定位的真实 `sequenceDiagram`**（参与者用真实组件名如 `PostDetailPage`/`PostListServer`/`getPosts`/`publishPost`，步骤编号与详述一一对应；server/client 边界与数据获取方向必须可读）；占位残留不得宣称可送审。
11. 技术决策承接（阶段 6）按 L1 字段合同逐条建立 `technology_decision_handoff[]`：决策点 / 选定值（或显式「未选定」）/ owner（doc_type）/ 详细落点（`chapters/<slug>.md`）/ 关键取舍锚点（回指第 3 章 ADR）。技术选择命中时必须先在第 3 章形成 ADR/关键取舍再建清单。命中外部 provider / CMS / LLM / 对象存储 / 云服务 / 三方 API / 数据库 / 认证 provider（NextAuth）时必填 credential strategy：**不保存任何 secret value**，默认凭证链优先，通过 `api_key_env_name` / `credential_ref` / `default_credential_provider_chain` / 运行平台身份注入短期凭证表达；secret 与私有数据获取只在 server 侧 owner，不下放 client-component。「未选定」必须显式标注，禁止让下游引用未选定决策。列表/分页先判定普通分页还是连续消费（无限滚动/游标）语义，普通分页不触发游标决策。
12. 承接索引（阶段 7）覆盖归属表全部 owner（七类 doc_type 全覆盖）；full 链每条附 `chapters/<slug>.md` 目标文件名（文件本体详细阶段产出）；`detail_doc_type` 取值只用七分类（见下表），命中 pending L2 类型（`route` / `ui-component` / `domain-type` / `server-action`）时在此阶段就写明 `L2豁免：<doc_type> 理由：…` 或改走先补 L2 路径；render/interactive/data 三元组（`server-component`/`client-component`/`data-access`）走已出 L2。
13. 概要禁写项（见「边界约束」）全程生效：发现自己在写组件 props 合同、zod schema 正文、fetch/SDK 参数、metadata 字段表、env 取值即停下，回收到「交给详细设计展开」的索引条目。
14. UC 与行为双向回指：每条 `BHV-NNN` 回指 ≥1 个 UC；UC 承接表 `bhv_refs` 与行为集合双向核对，不留孤儿行为、不留空 UC。
15. 阶段 9 自检按 L1 §6 G1~G8 逐项输出（满足/缺口 + 闭合计划），full 链写成 `design-main` 的「架构就绪自检」章节；存在未闭合 G 项不得送审，不得用概括性「基本满足」替代逐项证据。
16. 产物语言：辅助性正文一律中文；英文仅限代码标识符、命令、路径、框架/库名（`Next.js`、`React`、`zod`、`next/image`、`NextAuth`）、路由段/组件名、缩写与原文引用。
17. 完稿后提示送审：加载 `h5-design-overview-review` 做 clean-context review；review worker 用 `guru_gate.py record-review overview <task_dir> ...` 记录证据。当前 digest 下两个不同 `run_id` 的 clean review 后 overview 自动通过并进入详细设计；不要运行 `confirm overview`，也不要做任何 overview 人工收口。

## H5 详细 doc_type 七分类（承接索引取值，H5_BRIEF 钉死，禁改名/增减/换数）

承接索引 `chapter_target → detail_doc_type` 的 doc_type 取下表之一；引用裸 token。`l2_status` 标注当前是否已提供类型差异 L2 文件：render/interactive/data 三元组已出 L2，其余四类 pending（须 `L2豁免：<doc_type> 理由：…` 或先补 L2，否则详细 Gate 拦截）。

| doc_type | owner / 覆盖对象 | 证据锚点（H5 形态） | L2 状态 |
|----------|------------------|----------------------|---------|
| `server-component` | RSC 服务端组件 — 服务端渲染 + 数据获取编排（默认）；调用 `data-access` 取数、组装下传 props、注入 `metadata` | `app/posts/[slug]/PostDetailServer.tsx`（render 三元组） | **已出 L2**（`detail-type-server-component.md`） |
| `client-component` | `'use client'` 交互组件 — 状态/事件/hooks/浏览器 API；最小化、下沉到叶子 | `components/LikeButton.client.tsx`（interactive 三元组） | **已出 L2**（`detail-type-client-component.md`） |
| `data-access` | 数据访问层 — `fetch` 封装 / 内容源（MDX/CMS）读取 / ORM 查询；私有源与 secret 只在此与 server 侧 | `lib/data/posts.ts`、`lib/cms.ts`（data 三元组） | **已出 L2**（`detail-type-data-access.md`） |
| `route` | App Router route 段 — `page`/`layout`/`loading`/`error`/`not-found`/`route handler` + `metadata`/SEO；外部触发唯一入口 | `app/posts/[slug]/{page,layout,loading,error}.tsx`、`app/api/*/route.ts` | pending（L1 八问 + `L2豁免`） |
| `ui-component` | 展示型可复用组件 — 纯展示、无数据获取、无业务；只接 props 渲染 | `components/PostCard.tsx`、`components/Tag.tsx` | pending（L1 八问 + `L2豁免`） |
| `domain-type` | TS 类型 / `zod` schema / 领域模型 — frontmatter schema、DTO、领域实体；各层共享底座 | `types/post.ts`、`schemas/post.ts` | pending（L1 八问 + `L2豁免`） |
| `server-action` | Server Actions / route handlers — 变更/写入/表单提交/API endpoint；经 data-access 落库或出站 | `app/posts/actions.ts`（`'use server'`）、`app/api/*/route.ts` | pending（L1 八问 + `L2豁免`） |

> doc_type 与详细 L1 §2 同步维护，类型名以 H5_BRIEF 七类为权威；命中 pending 类型且无 `L2豁免` 声明即被详细 Gate 拦截。**禁止把这七类换成 flutter/Go 的类型名。**

## H5 分层与写作顺序（依赖向下，写作自底向上）

- **依赖方向**（运行时调用与归属判定基准）：
  - 服务端链 `route → server-component → data-access → domain-type`；
  - 交互链 `client-component → ui-component`；
  - 写入链 `server-action → data-access`；
  - 均严格单向无环，`domain-type` 为各层共享底座，`ui-component` 纯展示不反向依赖。
- **概要写作顺序**（自底向上，先定稳定层再定上层依赖）：① `domain-type`（类型/schema 边界，对应 flutter 的稳定底座层，但**只用 H5 类型名**）→ ② `data-access`（数据访问合同边界）→ ③ `server-action`（变更/写入合同边界）→ ④ `server-component`（RSC 渲染 + 数据获取编排，render 三元组）→ ⑤ `client-component`（交互状态单元，interactive 三元组）→ ⑥ `ui-component`（纯展示可复用件）→ ⑦ `route`（段约定与外部边界、metadata/SEO、错误边界）。
- 该顺序只约束「概要里先把哪类的边界与归属定清楚」，不等于详细设计的编码顺序，也不改变运行时依赖方向。行为枚举与归属判定仍按 BHV 行为逐条进行，自底向上顺序用于组织第 3~4 章的边界叙述与第 7 章索引的收敛节奏。

## 分阶段流程（writing 专属）

1. **阶段 0 判轨与骨架**：判轨落盘（规则 4）；技术栈基线 + 路由边界 + server/client 切分初判 + 内容源/数据源确认（规则 5，引用 `SLOT-NN`，`strict:true`/App Router 为生产基线）；full 链建包骨架 + `design.md` 指针。
2. **阶段 1 README 与元信息**：full 链写 `README.md` 导航（不承载正文）+ `design-main` 元信息/修订历史。
3. **阶段 2 行为枚举**：第 1~2 章（设计约束与输入、行为集合）；按用户操作/系统反应（渲染与数据获取）/失败路径（error/notFound 边界）/生命周期与导航四类枚举 `BHV-NNN` + GWT + 粒度自检。
4. **阶段 3 归属判定**：第 3 章归属判定表（owner ∈ 七类 doc_type + 三问理由）；分层依赖律自检（服务端链/交互链/写入链单向无环、server-first、`'use client'` 最小化、私有数据获取边界、外部触发只进 route、唯一写 owner）；按自底向上顺序（domain-type→data-access→server-action→server-component→client-component→ui-component→route）收敛边界叙述。
5. **阶段 4 关键取舍与 ADR**：第 3 章续——架构驱动、关键结构策略、关键取舍/ADR（server/client 切分取舍、内容源 MDX vs CMS、渲染策略 static/dynamic/ISR、状态管理选型）；命中技术选择先形成 ADR 再为阶段 6 清单埋锚点。
6. **阶段 5 架构总览**：第 4 章六件套（一句话架构 → 分层架构图 → 路由与系统边界图 → 核心 UC 表 → UC 承接表 → 时序图策略表）；图区分 server/client 段；本阶段建立人审链路，时序图可先计划锚点。
7. **阶段 6 技术决策承接**：第 5 章 `technology_decision_handoff[]`（决策点/选定值或未选定/owner doc_type/详细落点/credential strategy；secret 与私有数据获取只在 server 侧）。
8. **阶段 7 承接索引**：第 6 章 `chapter_target → detail_doc_type`（→ `chapters/<slug>.md`）；覆盖七类 doc_type 全部 owner；回填 UC 承接表 `index_refs`；render/interactive/data 三元组走已出 L2，pending L2（route/ui-component/domain-type/server-action）处写 `L2豁免` 或先补 L2。
9. **阶段 8 未决问题**：第 7 章显式列出 + 风险等级；无未决也须显式声明「无未决」。
10. **阶段 9 架构就绪收敛**：回填全部时序图占位 → 第 8 章 G1~G8 自检 → 送审提示（规则 17）。

## 输出要求（writing 专属）

- 默认先给完整正文，再给结构化状态；共创式迭代模式只给当前阶段正文 + 当前阶段状态。
- 一次性交付模式默认输出下列字段：
  - `交付范围`（全稿/当前阶段）与 `执行模式`
  - `链型`（full/light）与 `概要主定义位置`（`design-main.md` / `design.md` §概要）
  - `路由边界`（落在哪个 `app/<seg>/`，复用/新建段清单 page/layout/loading/error/not-found/route）
  - `内容源/数据源`（MDX/CMS/DB 接入点，引用 `SLOT-NN`）
  - `生产基线符合状态`（`strict:true` / App Router 段 / server-first / 私有数据获取边界 / metadata SEO / 样式隔离是否均按生产基线落 owner）
  - `显式假设`（无/有：假设、依据、影响范围、验证时点）及 `落盘状态`
  - `项目约定校验状态`（C1~C5 逐项 通过/不过；不过即标终止原因）
  - `行为集合状态`（`BHV-NNN` 条数、四类分布、粒度自检结论）
  - `归属判定状态`（覆盖行为数、七类 doc_type owner 分布、分层依赖律自检结论、server-first / 'use client' 最小化 / 私有数据获取边界自检、唯一写 owner 自检）
  - `架构总览状态`（六件套逐件 完整/缺失；server/client 段是否在图中区分；缺失时标注影响 G6/G7）
  - `时序图承接状态`（非豁免 UC 是否全部有可定位 `sequenceDiagram`；占位残留清单）
  - `技术决策承接状态`（无触发/已建立/存在缺口；未选定清单；命中外部 provider/CMS/存储/云服务/认证时 credential strategy 是否齐备且 secret 只在 server 侧）
  - `承接索引状态`（七类 doc_type owner 覆盖率；full 链逐文件 `chapters/<slug>.md` 清单；doc_type 分布；render/interactive/data 走 L2、pending L2 命中与 `L2豁免`/补 L2 计划）
  - `架构就绪结论`（仅阶段 9 或全稿完成时输出 G1~G8 逐项 满足/缺口；草稿阶段只说明不可送审原因）
  - `需用户确认项`（若有）
- 完稿输出末尾给出送审与 review evidence 指引（规则 17）：加载 `h5-design-overview-review` 过概要 Gate；由 review worker 用 `record-review overview` 记录当前 digest 的 clean/findings 证据，区别于 `trellis-check` 代码质检。

## 参考资料

- 概要阶段中立规范（L1）：`.trellis/spec/harness/overview/overview-structure-single-source.md`
- 详细阶段 L1 与已出 L2（render/interactive/data 三元组）：`.trellis/spec/harness/detail/detail-structure-single-source.md`、`.trellis/spec/harness/detail/detail-type-{server-component,client-component,data-access}.md`
- 通用方法 SSOT（分层依赖律/硬红线/禁止清单）：`.trellis/spec/guides/golden-path.md`
- 项目约定取值（C1~C5 硬前置）：`.trellis/spec/conventions/project-conventions.md`
- 分章写法细则与模板：`references/chapter-guide.md`
- 最小成稿样例：`references/examples/design-main-minimal.md`
