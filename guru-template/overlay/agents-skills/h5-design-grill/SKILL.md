---
name: h5-design-grill
description: H5 / Next.js App Router Gate 前拷问会话（grill-with-docs 的 guru-h5 适配版）。对照本平台领域模型（golden-path 分层依赖律 + server-client 边界、project-conventions 项目取值槽位 + 方法学纪律 + 存量违例槽、doc_type 权威七类、既有 BHV/UNIT 编号）逐分支对抗式拷问 prd 或概要归属表：磨尖术语、压测 server/client 边界与并发场景、与目标仓库代码现状交叉核对、当场把决策固化进 prd/design/CONTEXT/ADR，并校验是否触碰平台三条最高禁令。运行位置：需求 Gate 前（拷问 prd.md）与概要 Gate 前（拷问 design §1 / design-main.md 归属表逐行核对）。触碰红线时当场 fail 回退，不放行进 Gate。不替代 trellis-brainstorm（探索生成）、h5-design-*-writing（撰写）与 *-review（判定）。
---

# h5-design-grill — H5 / Next.js App Router Gate 前拷问

> 层级契约：拷问的对照基准是 `.trellis/spec/guides/golden-path.md`（分层依赖律 §2.1 + server-client 边界 §2.2 + 各 doc_type 迷你路径 §4 + 禁止清单 §7）、`.trellis/spec/conventions/project-conventions.md`（`SLOT-NN` 项目取值槽位 + 方法学纪律 + 存量违例槽，编号体系以该文件 canonical 为准）、`.trellis/spec/harness/overview/overview-structure-single-source.md`（归属判定方法 §4 + doc_type 七类 §7）。本 SKILL.md 只编排拷问动作与处置规则，不复写规范正文；冲突时 golden-path 硬红线 > overview L1 章节合同 > project-conventions 槽位 > 本文件。

## 做什么

对当前 task 产物（`prd.md` 或 `design.md` §1 / `design-main.md` 归属表）发起不留情面的逐分支对抗式拷问，直到达成共识：沿设计树逐支走，决策间依赖逐个解开，每个归属判定都经得起 overview L1 §4.1 的**三问**——"为什么属于它 / 为什么不属于别人（尤其排除把取数/secret 错放 client-component、把业务错放 ui-component、把渲染错放 route）/ 为什么需要（或不需要）独立存在"。**一次只问一个问题，每个问题附上你的推荐答案（含依据），等用户反馈再继续。** 能从代码（目标仓库 `app/**`、`lib/**`、`types/**`、`components/**`）/spec（golden-path、project-conventions、overview L1）找到答案的问题不要问用户——先自己读取证实再说。

拷问的产物不是一份新文档，而是把磨出来的决策**当场固化**回既有产物：行为/范围/失败路径 → `prd.md`；归属/owner/doc_type/server-client 归属 → `design.md` §1 / `design-main.md` 归属表三问理由；纯术语 → 仓库 `CONTEXT.md`（格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)）；难以回头的架构/契约/渲染策略权衡 → `docs/adr/`（格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)）。

## 拷问对照物（领域模型，硬前置装载）

执行拷问前必须依次确认可读，任一缺失即停止并输出前置缺口（不得凭印象拷问）：

1. `.trellis/spec/guides/golden-path.md` — 拷问归属/边界的唯一基准。重点装载：
   - §2.1 **分层依赖律**：服务端链 `route → server-component → data-access → domain-type`、交互链 `client-component → ui-component`、变更链 `server-action → data-access`，单向无环（"这条取数你打算让 route 段直接 import data-access？§2.1 不允许跳过 server-component；除非 page.tsx 自身就充当 server-component"）。
   - §2.2 **server-client 边界**：server-first 默认、`'use client'` 最小化（仅在真需 useState/useEffect/事件/浏览器 API/仅客户端库时下沉到最小叶子）、私有数据/secret 只在 server 侧、跨边界 props 必须可序列化。
   - §4 各 doc_type 迷你路径与边界、§7 禁止清单。
2. `.trellis/spec/conventions/project-conventions.md` — 拷问时区分"硬规则（不可豁免）/槽位取值（项目级，改值需 ADR）/存量违例（触碰记债、新增阻塞）"三档（槽位号一律以该文件 canonical 的单一 `SLOT-NN` 体系为准，下方按主题指代）：
   - **项目取值槽位**（路由模式 / 目录分界 / 内容源 / 数据获取与缓存 / 错误边界 / 领域类型 / 状态管理 / UI 库 / 样式方案 / 图像 / 认证 / 数据库 / TS·lint / 测试 / 构建脚本 / 部署 / metadata·SEO）——"你说新建一个全局状态——状态管理槽位钉的是 none（server-first），你这条交互态为什么不能落在最小 client 叶子的 `useState`？"
   - **方法学纪律**（doc_type 七类锁定 / 分层依赖律 / 写作顺序 / 编号纪律——这些是 golden-path 平台硬规则，不可被项目槽位豁免）。
   - **存量违例清单**（项目约定的最后一个槽位）——触碰记债不阻塞，**清单外同类新增一律按新增违例阻塞**。
3. `.trellis/spec/harness/overview/overview-structure-single-source.md` — 归属判定方法（§4：owner 层 + 行为→owner 三问归属判定表）与 doc_type 七类（§7.1）。owner 只取七类；私有数据获取/secret 只能归 server-component / data-access / server-action 三类。
4. 当前任务既有产物：prd 的 `BHV-NNN` 行为集合、design §1 / `design-main.md` 归属表（拷问概要时逐行核对）、`task.json` 的 `guru_chain`（full/light，决定拷问 `design.md` §1 还是 `design-main.md` + `chapters/`）。
5. 仓库根 `CONTEXT.md`（术语表，存在则装载；不存在时首个术语敲定时按 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) 创建）；`docs/adr/`（既有 ADR，存在则读最高编号，格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)）。

## doc_type 权威七类（拷问归属/承接时只用这七类）

`server-component`（RSC 服务端组件：渲染编排 + 数据获取，默认形态、不带 `'use client'`，私有取数收口在此）· `client-component`（`'use client'` 交互组件：状态/事件/hooks/浏览器 API，向下只依赖 ui-component + domain-type 类型）· `data-access`（数据访问层：`fetch` 封装 / 内容源 MDX·CMS / ORM 查询，server-only，向下只依赖 domain-type）· `route`（App Router route 段：`page`/`layout`/`loading`/`error.tsx` + metadata/SEO，段编排入口，不写业务）· `ui-component`（展示型可复用组件：纯展示、无数据获取、无业务、依赖图叶子）· `domain-type`（TS 类型 / zod schema / 领域模型，横切被依赖、自身不依赖业务层）· `server-action`（Server Actions / route handlers：变更/API endpoint，向下依赖 data-access）。**禁止串入他平台类型名**（flutter 的 controller/usecase/repository-datasource、Go 的 handler/service/repo，或 Manager/Helper/Util/Provider 等名词先行反模式），出现即就地纠正回这七类（doc_type 七类锁定，方法学纪律）。

## 会话期间

- **对照术语表挑战**：用语与 `CONTEXT.md` 既有定义冲突时立即点破——"术语表里 **Post** 定义为已发布的文章（front-matter `title/date/description/tag/author`），你这条 BHV 里的『草稿』指的是 **Post** 还是另一个概念 **Draft**？若术语表只有发布态，草稿是新概念，要不要单列 domain-type？"
- **磨尖模糊语言**：出现含混/过载词汇时给出精确候选——"你说『加载文章』——是 server-component 内 `await getAllPosts()`（首屏 SSR 取数，server 边），还是 client-component 用 `useEffect + fetch` 客户端拉？golden-path §2.3 禁止 client 用 `useEffect+fetch` 取首屏私有数据；这两条边不一样。"；"『展示组件』——是真正纯展示的 ui-component（不标 `'use client'`、零取数零状态），还是含 `useState` 的 client-component？两类的依赖边界不同（§2.1）。"行为命名同步回写 `BHV-NNN` 标题短名（粒度对齐 overview L1 §3.1：动词+宾语、可直接实现、有失败路径、标注**执行边 server/client**）。
- **具体场景压测（H5 专属探边）**：发明探边场景逼出概念边界、唯一写 owner 与 server/client 归属——
  - "这条交互态（如标签筛选 `tag`）的唯一写 owner 是谁？落 client-component 的 `useState`，还是你想提到根 layout 的 Context 把整树变 client？状态管理槽位是 none/server-first，Context 只能包最小 client 子树。"
  - "server-component `await getPostBySlug(slug)` 命中不存在的 slug，走 `notFound()` 还是抛错给 `error.tsx`？这条失败路径在 prd 里写了吗（overview L1 §3 失败路径枚举）？"
  - "从 server-component 传给 client-component 的 props 里有 `Date`/函数/类实例吗？§2.2 序列化边界——跨边界只能传 plain object，复杂对象先在 server 侧按 domain-type schema 转换。"
  - "这个 `fetch` 的缓存语义是什么？§2.3 要求显式声明 `cache: 'force-cache'|'no-store'` 或 `next: { revalidate: <秒> }`，不能依赖隐式默认；变更后谁调 `revalidatePath`/`revalidateTag`（应是 server-action）？"
- **与代码现状交叉核对**：用户陈述与目标仓库代码现状矛盾时当场摆出证据——"你说在 client-component 里读 front-matter 内容源——读文件系统是 server 边动作，生产形态应抽成 server-only 的 data-access（如 `lib/<name>.ts`，`import 'server-only'`），由 server-component 调用。client-component import data-access 会把读文件代码拖进 client bundle，是三条最高禁令之一。"；"你打算手写 `<head>`/`<meta>` 做 SEO——App Router 一律走 `metadata`/`generateMetadata`（§2.6），新代码手写 `<head>` 是新增违例。"
- **决策当场固化（落盘，不口头停留）**：
  - 行为/范围/失败路径决策 → 立即更新 `prd.md`（未决问题 → 已决，附一句依据；保持 Given/When/Then + 失败路径 + 验收场景 + **执行边标注** 结构）；
  - 归属/owner/doc_type/server-client 归属决策 → 立即更新 `design.md` §1 / `design-main.md` 归属表的三问理由（owner 落七类之一，标明 server 还是 client 边）；
  - 纯术语 → 更新仓库 `CONTEXT.md`（只做术语表，零实现细节，格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)）；
  - 项目级槽位取值变化（如要从 MDX 切到 Headless CMS、引入 Zustand、改样式方案、从 App Router 退回 Pages、引入 NextAuth）→ **不当场私改 project-conventions**，提示走槽位修订（需 ADR），并按下方 ADR 条件评估是否当场起草。
- **克制地提议 ADR**（三条全中才提，格式与编号见 [ADR-FORMAT.md](./ADR-FORMAT.md)）：难以回头 + 缺上下文会令未来读者困惑 + 真实权衡的产物。H5 典型可记 ADR：内容源选型（MDX vs Headless CMS，内容源槽位）、渲染策略（SSG vs ISR vs SSR + `revalidate` 周期）、路由模式（App vs Pages，路由模式槽位；偏离 golden-path 默认须记理由）、状态管理引入（none → Zustand/Context，状态管理槽位）、认证方案（无 → NextAuth，认证槽位）、数据/边界归属（"front-matter 内容由 data-access 拥有，client-component 只经可序列化 props 读，不反向 import"）。纯遵循 golden-path 默认路径、易回退的决策不记 ADR（如按迷你路径新增一个常规 server-component、复用既有 ui-component、加一个 domain-type 字段）。

## 触碰红线 → 当场 fail 回退（处置规则）

拷问发现产物触碰下列任一 **H5 三条最高禁令 / golden-path 硬红线**时，立即判定本次拷问 **fail**，不放行进对应 Gate，输出"红线条目 + 证据锚点（BHV/UNIT/章节）+ 必须回退到哪个上游步骤修订"，并停止继续往下问，直到产物改正：

1. **分层依赖律违反**（最高禁令①，golden-path §2.1）：`data-access`/`domain-type` 反向依赖 `server-component`/`route`；`ui-component` 反向依赖 `client-component` 或 import 任何 `data-access`；`client-component` import `server-component`/`data-access`（会污染 client bundle）；`server-action` 反被 `data-access` 依赖；`route` 跳过 `server-component` 直堆复杂取数逻辑；任意两类成 import 环。
2. **client 直取私有数据 / 读 secret / 直连 DB**（最高禁令②，golden-path §2.2）：把私有数据获取、server-only secret、私有 `process.env`、带鉴权 token 的 fetch、ORM/DB 连接归给 `client-component`，或在 client 用 `useEffect+fetch` 取首屏私有数据。私有取数只能归 `server-component`/`data-access`/`server-action` 三类（`NEXT_PUBLIC_` 非敏感公开值除外，且须显式声明）。
3. **全局样式污染**（最高禁令③，golden-path §2.4）：归属/承接里出现裸全局 CSS 选择器覆盖第三方/跨组件，而非 CSS Modules / Tailwind 隔离（受控 `app/globals.css` 仅放 reset/token/字体除外）。

附加 fail 触发（同样当场回退，不进 Gate）：

- **跨边界 props 不可序列化**：server→client 传函数 / 类实例 / `Date` 以外的复杂对象 / Symbol（§2.2 序列化边界），且未在 server 侧按 domain-type 转 plain object。
- **owner 越界但被包装成"新约定"**：用户想把存量违例清单已登记的违例（如全局样式污染、手写 `<head>` SEO、Pages Router 扁平结构、无 schema 裸取 front-matter）当作新代码的合法模式扩散——明确区分"触碰存量记债"与"新增违例阻塞"，新增即 fail。
- **doc_type 串台**：归属/承接索引用了七类之外的类型名（flutter/Go 类型名或 Manager/Helper/Util），就地纠正；拒不改正即 fail（doc_type 七类锁定，方法学纪律）。
- **`'use client'` 过载**：把整页/大块标 `'use client'` 而非下推到最小交互叶子（§2.2 边界下推）；或本可留在 server-component 的渲染/取数被无理由下沉到 client。
- **越界拍板**：把 project-conventions 待定槽位或 `technology_decision_handoff` 里"未选定/needs_validation"的决策（如 MDX vs CMS、SSG vs ISR）在拷问中私自写成"已选定"而无用户确认或 ADR——回退，要求走槽位修订/ADR 或标显式假设。

合规 STOP（与 workflow Guardrails 一致）：触及鉴权/会话/密钥/用户数据采集、Cookie 同意 / 隐私 / 数据采集等美国法规，或 H5 套壳/WebView 嵌入触及 App Store / Google Play 政策的任何不确定性时，立即停止拷问，输出风险点 + 替代方案 + 人类确认清单，不替用户拍板。

## 边界（与官方/平台 skill 的职责切分）

- **不替代 `trellis-brainstorm`**：探索与初稿生成在前（1.1 light 链 prd 探索 / full 链正式需求由 `requirement-writing` 产出），本 skill 只对**已有草稿**做对抗式拷问，不从零生成需求。
- **不替代 `grill-with-docs`（官方）/ `trellis-check`**：本 skill 是 grill-with-docs 的 guru-h5 适配版，把通用拷问绑定到 H5 分层依赖律、server-client 边界、SLOT 槽位与 doc_type 七类；不做官方 trellis-check 的实现期质检（`tsc`/`next build`/`eslint`/测试证据是实现 Gate 的事）。
- **不替代 `h5-design-overview-writing` / `h5-design-detail-writing`**：撰写动作（章节合同、架构总览六件套、合同八问、承接索引）属 writing skill；本 skill 只拷问已写出的草稿并把决策回写，不代写章节正文。
- **不替代 `h5-design-overview-review` / `h5-design-detail-review`**：拷问出的修订落盘后，仍须走对应 review 给出"可进入下一阶段"的互斥 Gate 结论；本 skill 不出 Gate 判定，只在 Gate 前清障与红线拦截。本 skill 的 fail 是"拷问发现红线、回退修订"，不是 review 的正式 Gate 结论。
- **不进入实现细节**：组件 props 字段级签名、zod schema 字段明细、`fetch` 具体 URL/查询参数、`next.config` 取值、环境变量取值、SDK/CMS 客户端初始化参数、secret value 属详细设计（合同八问）/实现阶段领地（secret 永不落文档）；拷问不在此展开，只磨边界、语义、链路、取舍、归属、术语、server/client 执行边。
- **不私自拍板项目约定**：SLOT 取值变化、待定槽位收口、`technology_decision_handoff` 未选定项须经用户确认 + ADR/槽位修订，本 skill 只提议不私改 `project-conventions.md`。
- **产物语言**：中文优先（代码标识符/命令/路径/框架与库名如 `'use client'`/`server-only`/`next/image`/`generateMetadata`、缩写 RSC/SSR/SSG/ISR/SEO、原文引用除外）；面向用户的提问与结论一律中文。
