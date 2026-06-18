# Harness — Guru H5/Next.js 五阶段方法 SSOT 入口

> 本文件是 H5（Next.js）平台五阶段方法的唯一入口与单一来源（SSOT）。模型对标
> `guru-flutter-client/harness/index.md`，但 **doc_type 与分层一律以本平台 H5_BRIEF 权威七类为准**——
> 严禁照抄 flutter（controller/usecase/repository-datasource）或 Go 的类型名。
> 层级契约：本文（L1 入口）承载阶段映射、doc_type 表、编号纪律、Gate 口径；
> 详细分层规则正文与 L2 类型差异由 `detail/*` 承载；writing/review skill 的 `references/` 只做编排与判定。
> 冲突时 **L1 > L2 > references > SKILL.md**。
> 项目实际按层模式见 `.trellis/spec/<layer>/`（by-layer 项目 spec：`frontend/` `backend/` `shared/`，由 `00-bootstrap-guidelines` 扫真实项目填实）；本 harness 只承载方法学，不写项目实例。

---

## 平台档案（next.js）+ 全局钉死约定

**基线**：Next.js（**App Router 生产形态为目标**）+ React + TypeScript（**strict 模式强制**）。

**示例实证 vs 生产级补充**（全程必须区分，禁止混淆）：

- **示例实证**：参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是
  **Pages Router + Nextra + MDX + gray-matter** 的轻量 blog starter（故意简化）。
  实证可见：`package.json`（`nextra ^2.0.0-beta.5` + `gray-matter ^4.0.3` + `rss ^1.2.2`，
  scripts 用 `next` 裸命令）；`pages/_app.tsx`（Pages Router `App({ Component, pageProps })`、
  `next/head` 注入 RSS link）；`pages/posts/*.md`（front-matter：title/date/description/tag/author）；
  `pages/tags/[tag].mdx`（动态路由用 `useRouter().query`）；`scripts/gen-rss.js`（build 前用
  `gray-matter` 读 front-matter 生成 `public/feed.xml`）；`tsconfig.json` **`strict: false` + `target: es5`**。
- **生产级补充（golden-path 以此为准）**：本平台 golden-path 锁定 **App Router 生产最佳实践**，
  把上面示例仅作为「内容模型基线」（front-matter→domain-type、读取内容源→data-access 的形态参考）。
  与示例的关键差异必须显式标注：① 路由模式 `App` 而非 Pages；② TS `strict: true` 而非示例的 `false`；
  ③ 内容获取走 RSC server-component / data-access，而非 Pages 的 `getStaticProps`；
  ④ RSS / SEO 走 App Router `app/feed.xml/route.ts` + `metadata` API，而非示例的 build 脚本 + `next/head`。

**golden-path 硬规则（锁定，违反进不了对应 Gate）**——表列结构与 `README.md` §6 同口径（**规则 | 内容 | 违反判级**，七条均为锁定项，违反即阻塞对应 Gate，判级 P1）：

| 规则 | 内容 | 违反判级 |
|------|------|:--------:|
| **1 TypeScript strict** | `strict: true`；禁 `any` 兜底（必要处显式 `unknown` + 收窄）。 | P1 |
| **2 server-first / `'use client'` 最小化** | 默认 RSC；仅在需要 state/event/浏览器 API/hooks 的最小叶子组件标 `'use client'`。 | P1 |
| **3 私有数据获取/secret 边界** | 私有 fetch、密钥、token 只允许出现在 server-component / data-access / server-action；**client-component 禁止直取私有数据或读 secret**。secret 永不落文档，只写引用方式（环境变量名）。 | P1 |
| **4 route 段约定** | `page.tsx` / `layout.tsx` / `loading.tsx` / `error.tsx`（`error.tsx` 必须 `'use client'`）按 App Router 语义就位。 | P1 |
| **5 metadata / SEO 标准化** | 用 App Router `metadata` 导出或 `generateMetadata`；动态页提供 OG/title/description。 | P1 |
| **6 样式隔离** | CSS Modules 或 Tailwind；**禁止全局样式污染**（除受控的 `globals.css` 设计 token 层）。 | P1 |
| **7 错误边界** | 每个有数据获取的 route 段提供 `error.tsx`（兜底）与 `loading.tsx`（Suspense 边界）。 | P1 |

---

## Pre-Development Checklist（每个任务开始前，逐项过）

- [ ] 读 `.trellis/spec/conventions/project-conventions.md` 并通过其校验清单 C1~C6（单一 `SLOT-NN` 体系，槽位编号规范见 `conventions/index.md` 开篇）；缺失/未填 → **停止**，先完成项目约定。
- [ ] 读 `.trellis/spec/guides/golden-path.md`（分层依赖律 + 上面 7 条硬规则的禁止清单）。
- [ ] 确认目标产物的 **路由模式**：本平台 golden-path = `App`（若仓库历史为 Pages Router，在 project-conventions `路由模式` 槽位显式记录并标偏离理由）。
- [ ] 按本任务所处阶段读对应 SSOT（下方「阶段 → SSOT 映射」），并把所读文件登记进任务的 `implement.jsonl` / `check.jsonl`（带 reason）。
- [ ] 若本任务处于 planning Gate 或准备 `task.py start`，读 `.trellis/spec/harness/gate/gate-confirmation-model.md`。
- [ ] 确认本任务命中的 doc_type 属于 **H5 权威七类**（见下表）；命中 `l2_status: pending` 的类型，full 链须显式 `L2豁免` 声明或先补 L2。
- [ ] 产物语言：**中文优先**（英文仅限代码标识符、命令、路径、协议字段、框架名/外部专有名词、缩写、原文引用）。

**project-conventions 槽位速览（H5 专属，未填即停）**——下表是按主题归并的导航口径（落地取值以 `project-conventions.template.md` 的 `SLOT-01~SLOT-18` 为准，单一 `SLOT-NN` 前缀、连续递增、存量违例置末位 SLOT-18）；其中「必须可定位取值的关键必填槽位子集」即 `conventions/index.md` §3 的 C1~C5 校验对象（C6 单独校验 SLOT-18 存量清单）：

| 槽位 | 取值域示例 | 说明 |
|------|-----------|------|
| 内容源 | MDX / Headless CMS / ORM(DB) | 决定 data-access 的获取形态（示例实证为 MDX + gray-matter） |
| 状态管理 | none / Zustand / Context | server-first 下默认 none；仅交互态用 client 局部状态 |
| UI 组件库 | shadcn / MUI / 无 | ui-component 的来源基线 |
| 样式方案 | Tailwind / CSS Modules | 对应硬规则 6 的样式隔离方式 |
| 测试 | Vitest+RTL / Playwright | 单元/组件 vs e2e |
| lint | ESLint + Prettier | 静态检查命令来源 |
| 数据库 | 无 / Postgres / 其它 | data-access / server-action 写路径依据 |
| 认证 | 无 / NextAuth | server-action / route 的鉴权依据 |
| 图像优化 | next/image | ui-component / server-component 资源约定 |
| 部署 | Vercel / 其它 | 影响 route handler 运行时（edge/node）与缓存语义 |
| 路由模式 | App / Pages | golden-path 默认 App；偏离须记理由 |

---

## 阶段 → SSOT 映射

**双轨制**：task.json `guru_chain` 判轨（创建默认 `full`）。full=完整五阶段链，需求走正式需求包、
设计走目录级设计包（task.json `design_package`）；light=轻量链（分流 + 用户同意），产物为任务内单文件。
下表「产物」列写作 `full / light`。装载路径一律用 `.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md`。

| 阶段 | 产物（full / light） | 装载 |
|------|------|------|
| 需求 | 正式需求包（requirement-writing 撰写 + requirement-review 门禁）+ `prd.md` 行为规格抽取 / 仅 `prd.md` | guru-ai-guides `requirement-writing`、`requirement-review` skill 及其标准包 `requirement-doc-standard`（**硬前置：未安装即停**）；jsonl 引用安装路径 |
| 概要设计 | `design_package/design-main.md` / `design.md` §概要 | `.trellis/spec/harness/overview/overview-structure-single-source.md` |
| 详细设计 | `design_package/chapters/*.md`（逐章）/ `design.md` §详细 | `.trellis/spec/harness/detail/detail-structure-single-source.md` + 涉及类型的 `.trellis/spec/harness/detail/detail-type-server-component.md` / `detail-type-client-component.md` / `detail-type-data-access.md`（其余四类 doc_type 为 pending：full 链须显式 `L2豁免` 或先补 L2，light 链按 L1 合同八问展开并标注 `l2_status: pending`） |
| 实现 | 代码 + `implement.md`（trace） | `.trellis/spec/guides/golden-path.md` + `.trellis/spec/harness/implementation/implementation-trace-contract.md` |
| 审核/复盘 | findings + spec 回写 | 各 SSOT 审核基线章节 + `.trellis/spec/harness/extraction-template.md` |

人工 Gate、design-grill 凭据、confirm 快照、累积 digest 与失配恢复流程见 `.trellis/spec/harness/gate/gate-confirmation-model.md`。摘要：requirements 必跑 `design-grill`；overview/detail 在 full/high-risk/unknown 时必跑，只有 low-risk 非 full 可由 `guru_gate.py grill-skip` 留痕跳过。

---

## H5 详细设计 doc_type 权威七类（全程唯一，禁止改名 / 增减 / 换数）

> 这是 H5 平台详细设计的归属硬基准。每条 owner 必须落在以下七类之一；
> 概要承接索引 `chapter_target → detail_doc_type` 的 `detail_doc_type` 取值只能取下表七个 token。
> v1 提供 L2 文件的三类对应 flutter 的 render / interactive / data 三元组
> （server-component ↔ controller 的渲染编排面、client-component ↔ controller 的交互面、data-access ↔ repository-datasource）。

| # | doc_type | 覆盖对象 | L2 状态（v1） | 证据锚点（示例实证 vs 生产补充） |
|---|----------|---------|--------------|----------------------------------|
| 1 | `server-component` | RSC 服务端组件：渲染编排 + 数据获取调度（默认形态） | **v1 提供** `detail-type-server-component.md` | 生产补充：App Router 默认 RSC（示例为 Pages，无 RSC 对应物，须显式标差异） |
| 2 | `client-component` | `'use client'` 交互组件：状态 / 事件 / hooks | **v1 提供** `detail-type-client-component.md` | 示例实证：`pages/tags/[tag].mdx` 用 `useRouter().query`（客户端 hook）；生产补充：拆为最小 `'use client'` 叶子 |
| 3 | `data-access` | 数据访问层：fetch 封装 / 内容源（MDX/CMS）/ ORM 查询 | **v1 提供** `detail-type-data-access.md` | 示例实证：`scripts/gen-rss.js` + `gray-matter` 读 front-matter；生产补充：封装为 server 端 data-access 模块 |
| 4 | `route` | App Router route 段：`page`/`layout`/`loading`/`error.tsx` + `metadata`/SEO | pending | 示例实证：`pages/_app.tsx`、`pages/posts/index.md`（Pages Router）；生产补充：App Router `app/**` 段约定 |
| 5 | `ui-component` | 展示型可复用组件：纯展示、无数据获取、无业务 | pending | 生产补充：shadcn/MUI 来源（project-conventions），`next/image` 资源约定 |
| 6 | `domain-type` | TS 类型 / zod schema / 领域模型 | pending | 示例实证：front-matter 字段（title/date/description/tag/author）→ 领域模型雏形；生产补充：zod schema + `strict` 类型 |
| 7 | `server-action` | Server Actions / route handlers：变更 / API endpoint | pending | 生产补充：App Router `'use server'` action 与 `app/**/route.ts`（示例无对应物） |

**承载形态按链型分轨**（轨道判定见概要 L1 §2）：

- **full 链（目录级设计包）**：每个 `chapter_target` 独立一个 `design_package/chapters/<slug>.md`（文件名与概要承接索引一致，gate 双向闭合）。逐章或小批次生成，禁止一次性全量输出全部章节。
- **light 链（单文件）**：合并为任务内 `design.md` §2，每章仍须独立满足对应合同。
- **pending L2 拦截（full 链）**：承接索引命中 L2 状态为 pending 的 doc_type（route / ui-component / domain-type / server-action）时，必须在 design-main.md 显式声明 `L2豁免：<doc_type> 理由：…`（按 L1 合同八问展开的风险与补齐计划），否则 gate 拦截；首选先补 L2 再进详细。

### owner 层与分层依赖律（归属硬基准，违反 fail）

H5 平台分两条主链 + 一条交叉边界，箭头 = 依赖方向（左依赖右，右不反向依赖左）：

```
服务端链：  route → server-component → data-access → domain-type
交互链：    client-component → ui-component
变更链：    server-action → data-access
```

- **route** 只编排页面段（page/layout/loading/error）与 metadata，调用 server-component；不直接做数据获取。
- **server-component** 编排渲染 + 调度 data-access；可嵌入 client-component（作为交互叶子）；不写交互态。
- **data-access** 唯一持有 fetch/查询/缓存合同，产出 **domain-type**；不被 client-component 直接调用。
- **client-component** 只持有交互态与事件，组合 ui-component；**禁止直取私有数据 / 读 secret**（走 server-action）。
- **ui-component** 纯展示，无数据获取无业务；被 client-component 或 server-component 组合。
- **domain-type** 是叶子（类型/schema），被各层引用，不依赖任何运行层。
- **server-action** 处理变更（写入/提交/调用），依赖 data-access；可被 client-component 通过表单/调用触发，但 secret 边界仍在 server 侧。

**硬约束**：① 一份业务数据只有一个 data-access owner；② client-component 不得越过 server-action 直接写数据库或读私有 fetch；③ 不得在概要发明 Manager/Helper/Util 等无行为来源结构（名词先行反模式）。

### 写作顺序（自底向上，详细阶段 chapter_loop 推荐层级）

```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```

先固化类型与 schema（domain-type），再定数据访问合同（data-access），再定变更面（server-action），
然后是渲染编排（server-component）、交互（client-component）、展示（ui-component），最后收口路由段（route）。
同一 feature 的 data-access 及其 domain-type 视为同一小批次优先完成。

---

## 编号纪律

- **行为**：概要阶段以 `### BHV-NNN <短名>` 标题定义（NNN 数字；创建后不复用、不重排，删除留洞）。归属表、详细设计、测试与实现切片对行为的引用一律写裸 `BHV-NNN` token。
- **设计单元**：详细阶段每个设计单元以 `### UNIT-<slug>` 标题定义（语义 kebab-case，如 `UNIT-post-list-server-component`）；下游测试与实现切片对单元的引用一律写裸 `UNIT-<slug>` token。
- **追溯**：`guru_gate.py trace-matrix <task_dir> --write` 据此生成 行为 × 归属 × 单元 × 测试 × 切片 矩阵；幽灵引用（指向不存在的 BHV/UNIT）与断链均被 Gate 拦截，进不了详细 / 实现 Gate。
- **缺陷只能回上游修**：审核发现结构性缺陷（归属错、合同越界、doc_type 用错七类之外的名）回到拥有该决策的阶段修订，禁止下游补造。

---

## 详细合同八问（所有七类 doc_type 通用骨架）

每个 `UNIT-<slug>` 必须回答，缺一不可（括号内为可验证信号——审核按此取证）：

1. **承接哪些行为**：逐条引用 `BHV-NNN`（必须存在于 prd；幽灵引用与无承接行为均被 gate 断链拦截）。
2. **输入 / 输出 / 错误结果**：TS 类型、取值域、错误枚举（输入/输出各有参数表；错误有错误类型表）。server-component/server-action 须列 props/参数与返回 JSX/数据契约。
3. **读取 / 写入哪些状态**：明确读写分离；写 owner 与概要归属一致。client-component 列交互态字段表（名称/类型/初值/写入时机）；server 类多为无客户端态（写 N/A 并说明）。
4. **调用哪些依赖，不调用哪些依赖**：正反两面都写（防越层）。如 client-component **不调用** data-access；route **不调用** 私有 fetch；依赖必须出现在概要架构图/归属表。
5. **失败如何收口**：每条失败路径处置（error.tsx 边界 / Suspense fallback / 重试 / 上抛 / 用户提示）；server 端错误不泄漏内部细节到客户端。
6. **产生哪些事件 / 后置结果**：导航（router.push 去哪个 route、带什么参数）、缓存重验证（`revalidatePath`/`revalidateTag`）、埋点、副作用（逐条写消费方）。
7. **哪些测试验证它**：映射测试分层（Vitest 单元 / RTL 组件 / Playwright e2e / manual），逐行为给测试点（成功 + 全部失败路径）。
8. **哪些内容不得在此补造**：显式列出本单元不拥有的决策（如 client-component「不决定数据获取——属 data-access」）。

**粒度标准（四条）**：① 可直接实现；② 明确调用关系（下层行为名 + 参数）；③ 完整调用链（与概要时序图一致）；④ 同文档粒度一致。

正反例（H5）：

✅ 合格——`UNIT-post-detail-server-component` 的 `render` 行为：
1. 调用 `data-access` 的 `getPostBySlug(slug)`（承接 `BHV-021`）；返回 `Post | null`。
2. `null` → 调用 `notFound()`（命中 route 的 `not-found.tsx`），流程终止。
3. 命中 → 导出 `generateMetadata` 填 title/description/OG（承接 `BHV-022`）。
4. 渲染服务端树，把交互叶子（`UNIT-post-like-button-client-component`）作为 children 注入，自身不持交互态。

❌ 不合格——「负责文章详情页」一句话带过（无承接 BHV、无 null 分支、无 metadata、无依赖调用点）。

---

## 五道 Gate 口径（verify 脚本同口径）

| Gate | 通过条件（满足才进下一阶段） | 阻塞项（任一命中即不通过） |
|------|------------------------------|----------------------------|
| **需求 Gate** | 需求五要素齐全：行为 / 前置条件 / 状态变化 / 失败路径 / 验收场景 | 缺任一要素 → 不进概要 |
| **概要 Gate** | 行为有唯一 owner + 三问理由（为什么属于它/为什么不属别人/为什么独立存在）；归属符合分层依赖律；承接索引非空且覆盖全部 owner，`detail_doc_type` 取值落在七类内；架构总览（一句话架构 + 分层图 + 页面流 + UC 表 + UC 承接表 + 时序图策略）齐全 | 无唯一 owner、归属违反分层律（如 client-component 持数据获取）、承接索引缺失、`detail_doc_type` 用了七类外的名 → 不进详细 |
| **详细 Gate** | 合同八问无缺项；追溯到概要 owner；每行为有测试映射（成功 + 全部失败路径）；涉鉴权/私有数据/secret 的单元附合规与边界依据；八问之 8 逐单元存在；full 链章节闭合（索引↔chapters 双向）+ pending L2 命中项豁免齐全 | 合同八问缺项、追溯断链、无测试映射、client-component 直取私有数据/读 secret、secret 落文档、`l2_status: pending` 无豁免 → 不进实现 |
| **实现 Gate** | trace 四节齐全（计划 / 执行 / 证据 / 阻塞偏差）；analyze（`tsc --noEmit`）/ test（Vitest+RTL/Playwright，测试名级）/ lint（ESLint+Prettier）/ 边界合规 均有证据 | 任一无证据、trace 四节不全、`'use client'` 滥用、全局样式污染、`any` 兜底 → 不进 commit |
| **审核 / 复盘 Gate** | 存量豁免判定：清单内（SLOT-18）记债不阻塞；清单外新增违例阻塞；findings 带文档/章节锚点；缺陷回上游修 | 清单外新增违例、就地补造掩盖上游缺陷 → 阻塞 |

**实现 trace 四节**（实现 Gate 证据载体，对标 `implementation-trace-contract.md`）：① 计划（任务切片 → `UNIT-<slug>` + doc_type/文件范围/完成信号/验证方式，按写作顺序自底向上）；② 执行（实际改动文件清单 + 与计划偏差 + 原因）；③ 证据（`tsc --noEmit`/lint/测试命令与结果，测试名级；未验证项显式列出留给 Manual QA）；④ 阻塞与偏差（上游缺陷回退详细阶段、SLOT-18 存量违例处置、未决决策升级人工，不私自拍板）。

**互斥分支（审核）**：前置失败 → 只输出前置缺口与修复动作，不展开逐章审核；前置通过 → findings（severity/location/problem/suggestion）+ 概况 + 三选一结论（可进入下一阶段 / 带假设可进入 / 不可进入）。严重度：P1（违反硬规则/红线、八问缺项、追溯断链、边界缺失、doc_type 越界——阻塞）；P2（合同不完整但可局部补）；P3（表述建议）。
