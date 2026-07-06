# Guru H5/Web（Next.js）— Spec 库导航 README

> 本 spec 库由 guru-template 安装（`trellis init -t guru-h5-web -r <registry>`），落位 `.trellis/spec/`（PROTECTED：`trellis update` 永不覆盖）。
> 平台基线：**Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)**。
> 模型对标 `guru-flutter-client`（同一套「行为 → owner → 承接索引 → 合同八问 → trace」骨架与五道 Gate），但 **doc_type 与分层一律以本平台 H5_BRIEF 权威七类为准——严禁照抄 flutter（controller/usecase/repository-datasource）或 Go 的类型名**。
> 规则唯一真源原则：writing/review skill 只**装载**本库，不复写规则；冲突时 **L1（harness/index.md、structure-single-source）> L2（detail-type-\*.md）> skill references > SKILL.md**。

本文件只做**导航**：目录树 → harness 文件职责表 → 与五阶段 workflow 的关系 → doc_type 七类 → 硬规则速览 → 五道 Gate 表。规则正文不在本文件，按指针进入对应 SSOT。

---

## 1. 目录树

```
.trellis/spec/                       # 安装落位根（PROTECTED）
├─ README.md                         # ← 本文件：包导航
├─ guides/
│  ├─ index.md                       # 通用方法入口（导航，不承载正文）          [已交付]
│  └─ golden-path.md                 # 通用方法 SSOT：分层依赖律 + 各 doc_type 迷你路径 + 禁止清单 + 门禁映射 [规划中]
├─ conventions/
│  ├─ index.md                       # 项目约定入口                              [规划中]
│  └─ project-conventions.md         # 本项目取值（init 后填写，硬前置 C1~C6）   [规划中]
├─ frontend/                         # by-layer 项目 spec：前端层（server/client component）
│  ├─ index.md                       # 本层导航入口（链到本层真实存在的 topic 文件）
│  ├─ directory-structure.md         # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ server-components.md           # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ client-components.md           # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ ui-components.md               # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ state.md                       # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ type-safety.md                 # 项目实际模式（bootstrap 从真实项目填实）
│  └─ quality.md                     # 项目实际模式（bootstrap 从真实项目填实）
├─ backend/                          # by-layer 项目 spec：backend/server 层（route/data-access/server-action）
│  ├─ index.md                       # 本层导航入口（链到本层真实存在的 topic 文件）
│  ├─ route-handlers.md              # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ data-access.md                 # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ server-actions.md              # 项目实际模式（bootstrap 从真实项目填实）
│  └─ error-handling.md              # 项目实际模式（bootstrap 从真实项目填实）
├─ shared/                           # by-layer 项目 spec：跨层通用（语言级 / 命名 / 协作）
│  ├─ index.md                       # 本层导航入口（链到本层真实存在的 topic 文件）
│  ├─ ts-conventions.md              # 项目实际模式（bootstrap 从真实项目填实）
│  ├─ naming-conventions.md          # 项目实际模式（bootstrap 从真实项目填实）
│  └─ git-conventions.md             # 项目实际模式（bootstrap 从真实项目填实）
└─ harness/                          # 五阶段方法 SSOT
   ├─ index.md                       # L1 入口：阶段映射 / doc_type 七类 / 编号纪律 / Gate 口径 [已交付]
   ├─ overview/
   │  └─ overview-structure-single-source.md  # 概要设计 SSOT：行为→owner→承接索引   [规划中]
   ├─ detail/
   │  ├─ detail-structure-single-source.md    # 详细设计 L1：合同八问 + 章节闭合     [规划中]
   │  ├─ detail-type-server-component.md       # L2：server-component（render 端）   [已交付·full]
   │  ├─ detail-type-client-component.md       # L2：client-component（interactive） [已交付·full]
   │  └─ detail-type-data-access.md            # L2：data-access（data 端）          [已交付·full]
   ├─ implementation/
   │  └─ implementation-trace-contract.md      # 实现 trace 合同：计划合同 + mutable evidence [已交付]
   └─ extraction-template.md          # 复盘萃取模板（九段结构，spec 回写）         [已交付]
```

> 状态标记说明：`[已交付]` = 本库已写入并可被 jsonl 装载；`[规划中]` = 模型已钉死（见 harness/index.md 与本文 §3/§4），文件待 guru-template 后续批次补齐。`route` / `ui-component` / `domain-type` / `server-action` 四类的 L2（`detail/detail-type-<doc_type>.md`）属 `l2_status: pending`：full 链命中须显式 `L2豁免` 或先补 L2（见 §4、§6）。

---

## by-layer 项目 spec（项目实例层）

`frontend/` `backend/` `shared/` 三个层目录是**按层组织的项目实例 spec**——记录「**这个项目实际**怎么写代码」，与 harness、conventions 是三类边界清晰、互不复写的文档：

- **harness（方法学 / HOW）**：五阶段方法 SSOT（阶段映射、doc_type 七类、合同八问、编号纪律、五道 Gate），写「任何 H5/Next.js 项目都该怎么走流程」，不写任何单个项目的实例。
- **conventions（钉死的 SLOT 决策）**：本项目的槽位取值（`SLOT-01~SLOT-18`：路由模式/内容源/状态管理/UI 库/样式/测试…），是**封闭式**的判定基线、所有阶段的 Gate 硬前置（C1~C6 未填即停），每个槽位只有一个被钉死的取值。
- **by-layer 项目 spec（本节，项目实例层 / 本项目实际长什么样）**：**开放式**的按层模式文档，承载本项目真实的**目录结构、命名、WRONG·CORRECT 代码**，供 sub-agent 匹配本项目风格落地实现，而非靠通用规则臆测。

边界纪律：

- **document reality 非理想**：by-layer 写「项目实际怎么做」，不写「应该怎么做」；三层目录由 `00-bootstrap-guidelines` 任务扫真实项目代码填实（当前 topic 文件多为 `To fill` 骨架，待 bootstrap 落地）。
- **不复写、只引用**：harness 的方法学正文与 `guides/golden-path.md` 的硬规则（TS strict / server-first / `'use client'` 最小化 / secret 只在 server 侧 / doc_type 七类 / 分层依赖律）一律只引用不照搬；项目级槽位取值以 `conventions/project-conventions.md` 为唯一权威，不在 by-layer 重复。
- **层划分**：`frontend/`（server-component / client-component，含目录结构、UI 组件、客户端状态、类型安全、质量门禁）、`backend/`（route-handler / data-access / server-action 及 server/client 错误边界）、`shared/`（跨层通用：TS 语言级 / 命名 / git 协作，不分 doc_type）。
- **各层 index.md 是导航入口**：`<layer>/index.md` 用 Guidelines Index 表链到**本层真实存在的** topic 文件（如 `frontend/index.md` → `directory-structure.md` / `server-components.md` / …），只做层内导航，不承载规则正文。

> 装载与引用一律用安装路径 `.trellis/spec/<layer>/...`（如 `.trellis/spec/frontend/server-components.md`）。

---

## 2. harness 文件职责表

> 装载路径一律用 `.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md`；任务把所读文件登记进 `implement.jsonl` / `check.jsonl`（带 reason）。

| 文件 | 层级 | 职责（写了什么 / 不写什么） | 何时读 | 状态 |
|------|------|------------------------------|--------|------|
| `harness/index.md` | L1 入口 | 平台档案 + 钉死约定、Pre-Development Checklist、阶段→SSOT 映射、**doc_type 权威七类表**、owner 分层依赖律、写作顺序、编号纪律、合同八问骨架、**五道 Gate 口径**。不写 L2 类型差异、不写项目取值 | 任意阶段开工前必读 | 已交付 |
| `guides/golden-path.md` | 通用方法 SSOT | 分层依赖律方向、各 doc_type 迷你实现路径、入口决策树、server-first / `'use client'` 最小化、**禁止清单**、门禁映射。不写阶段流程、不写项目取值 | 写任何代码前 | 规划中 |
| `conventions/project-conventions.md` | 项目取值 | §1 槽位取值（按模板 `SLOT-01~SLOT-18`：路由模式/目录分界/内容源/数据获取缓存/错误边界/领域类型 schema/状态管理/UI 库/样式/图像/认证/DB/TS·lint/测试/构建脚本/部署/metadata·SEO）、SLOT-18 存量豁免清单、校验清单 C1~C6（单一 `SLOT-NN` 体系，与 go/ios 对齐，见 `conventions/index.md` 开篇规范）。不写方法规则 | 所有阶段硬前置（未填即停） | 规划中 |
| `harness/overview/overview-structure-single-source.md` | 概要 SSOT | 行为唯一 owner + 三问理由、归属表、**承接索引** `chapter_target → detail_doc_type`、架构总览（一句话架构/分层图/页面流/UC 表/UC 承接表/时序图策略）。不展开合同八问 | 概要设计阶段 | 规划中 |
| `harness/detail/detail-structure-single-source.md` | 详细 L1 | 合同八问通用骨架、粒度四标准、章节双向闭合（索引↔chapters）、pending L2 拦截规则。各类型差异下沉给 L2 | 详细设计阶段（与对应 L2 同读） | 规划中 |
| `harness/detail/detail-type-server-component.md` | 详细 L2 | `server-component` 类型特化：服务端取数 + 组件树组装 + 把交互下沉给 client-component；props 序列化边界、metadata/SEO 衔接 route、null→`notFound()` 分支。三元组 render 端（位同 flutter controller 渲染面） | 命中该 doc_type 时 | 已交付·full |
| `harness/detail/detail-type-client-component.md` | 详细 L2 | `client-component` 类型特化：`'use client'` 交互态/事件/hooks、组合 ui-component、**禁直取私有数据/读 secret**（走 server-action）。三元组 interactive 端 | 命中该 doc_type 时 | 已交付·full |
| `harness/detail/detail-type-data-access.md` | 详细 L2 | `data-access` 类型特化：fetch/缓存(`cache`/`next.revalidate`/tag) / 内容源(MDX·CMS) / ORM 查询封装；返回 domain-type、不新造类型；不被 client-component 直调。三元组 data 端（位同 flutter repository-datasource） | 命中该 doc_type 时 | 已交付·full |
| `harness/implementation/implementation-trace-contract.md` | 实现 SSOT | trace 计划合同与 mutable evidence（计划/执行/证据/阻塞偏差）、证据口径（`tsc --noEmit`/Vitest+RTL/Playwright/lint，测试名级）、裸 token 引用与断链拦截。不重定义 doc_type/分层 | 实现阶段 | 已交付 |
| `harness/extraction-template.md` | 复盘 SSOT | 九段萃取结构、「只沉淀这类任务如何做好、不沉淀本次需求事实」原则、回写 doc_type 对齐七类。Phase 3.3 由 `trellis-update-spec` 执行 | 审核/复盘阶段 | 已交付 |

---

## 3. 与五阶段 workflow 的关系

工作流（guru-client workflow）每个阶段从本库装载规则。**双轨制**：task.json `guru_chain` 判轨（创建默认 `full`）。full=完整五阶段链（需求走正式需求包、设计走目录级 `design_package`）；light=轻量链（分流 + 用户同意，产物为任务内单文件）。

```
需求(prd.md)        ← 需求三件套 SSOT（guru-ai-guides，经 jsonl 引用；requirement-writing/requirement-review 硬前置）
概要(design §概要)  ← harness/overview/overview-structure-single-source.md
详细(design §详细)  ← harness/detail/detail-structure-single-source.md + 命中类型的 detail-type-*.md（L2）
实现(implement)     ← guides/golden-path.md + harness/implementation/implementation-trace-contract.md
审核/复盘(check)    ← 各 SSOT 审核基线章节 + harness/extraction-template.md + conventions（SLOT-18 存量豁免）
```

| 阶段 | 产物（full / light） | 在本库读 |
|------|----------------------|----------|
| 需求 | 正式需求包 + `prd.md` 行为抽取 / 仅 `prd.md` | —（走需求三件套 SSOT；jsonl 引用安装路径） |
| 概要 | `design_package/design-main.md` / `design.md` §概要 | `harness/overview/overview-structure-single-source.md` |
| 详细 | `design_package/chapters/*.md`（逐章）/ `design.md` §详细 | `harness/detail/detail-structure-single-source.md` + 命中类型 `detail-type-*.md` |
| 实现 | 代码 + `implementation-trace.md` | `guides/golden-path.md` + `harness/implementation/implementation-trace-contract.md` |
| 审核/复盘 | findings + spec 回写 | 各 SSOT 审核基线 + `harness/extraction-template.md` |

**贯穿全程的产出纪律（Gate 兼容）**：

- 需求**五要素**：行为 / 前置条件 / 状态变化 / 失败路径 / 验收场景（缺任一不进概要）。
- 概要**归属表 + 承接索引**：每行为唯一 owner + 三问理由；承接索引 `chapter_target → detail_doc_type` 非空且覆盖全部 owner，`detail_doc_type` 取值只能落在七类内（§4）。
- 详细**合同八问**：每个 `UNIT-<slug>` 逐问回答（见下）。
- 实现 **trace 计划合同与 mutable evidence**：① 计划（切片→`UNIT-<slug>` + doc_type/文件范围/完成信号/验证方式，按写作顺序自底向上）；② 执行（实际改动文件 + 偏差 + 原因）；③ 证据（`tsc --noEmit`/Vitest+RTL/Playwright/lint 命令与结果，测试名级；未验证项显式留 Manual QA）；④ 阻塞与偏差（上游缺陷回退、SLOT-18 处置、未决升级人工）。

**详细合同八问（七类通用骨架，缺一不可）**：① 承接哪些行为（裸 `BHV-NNN`）；② 输入/输出/错误结果（TS 类型/取值域/错误枚举）；③ 读写哪些状态（读写分离，client 列交互态表，server 多为 N/A）；④ 调用/不调用哪些依赖（正反两面防越层）；⑤ 失败如何收口（error.tsx/Suspense/重试/上抛/提示，server 不泄漏内部细节）；⑥ 产生哪些事件/后置（导航/`revalidatePath`·`revalidateTag`/埋点/副作用）；⑦ 哪些测试验证它（Vitest/RTL/Playwright/manual，成功 + 全部失败路径）；⑧ 哪些内容不得在此补造（显式列出本单元不拥有的决策）。

**编号纪律（下游引用裸 token）**：行为 `### BHV-NNN <短名>`（数字，创建后不复用不重排，删除留洞）；设计单元 `### UNIT-<slug>`（语义 kebab-case，如 `UNIT-post-detail-server-component`）。`guru_gate.py trace-matrix <task_dir> --write` 据此生成 行为×需求场景（REQ-UC）×归属×单元×测试×切片 矩阵；幽灵引用与断链被 Gate 拦截。缺陷只能回上游修，禁止下游补造。

---

## 4. doc_type 权威七类（全程唯一，禁止改名 / 增减 / 换数）

> H5 详细设计归属硬基准。每条 owner 必须落在以下七类之一；承接索引 `detail_doc_type` 取值只能取下表七个 token。**勿照抄 flutter/Go 的类型名**。v1 提供 L2 的三类对应 flutter render/interactive/data 三元组（server-component↔controller 渲染面、client-component↔controller 交互面、data-access↔repository-datasource）。

| # | doc_type | 覆盖对象 | owner 层定位 | L2 状态（v1） |
|---|----------|---------|--------------|---------------|
| 1 | `server-component` | RSC 服务端组件：渲染编排 + 数据获取调度（**默认形态**） | 服务端链中段，上承 route、下调 data-access | **full**（`detail-type-server-component.md`） |
| 2 | `client-component` | `'use client'` 交互组件：状态 / 事件 / hooks | 交互链顶，组合 ui-component | **full**（`detail-type-client-component.md`） |
| 3 | `data-access` | 数据访问层：fetch 封装 / 内容源（MDX/CMS）/ ORM 查询 | 服务端链下段，产出 domain-type | **full**（`detail-type-data-access.md`） |
| 4 | `route` | App Router route 段：`page`/`layout`/`loading`/`error.tsx` + `metadata`/SEO | 服务端链顶，调 server-component | pending |
| 5 | `ui-component` | 展示型可复用组件：纯展示、无数据获取、无业务 | 交互链叶，被 client/server-component 组合 | pending |
| 6 | `domain-type` | TS 类型 / `zod` schema / 领域模型 | 叶子，被各层引用、不依赖运行层 | pending |
| 7 | `server-action` | Server Actions / route handlers：变更 / API endpoint | 变更链，依赖 data-access | pending |

**owner 层与分层依赖律（违反 fail，箭头 = 依赖方向，左依赖右、右不反向依赖左）**：

```
服务端链：  route → server-component → data-access → domain-type
交互链：    client-component → ui-component
变更链：    server-action → data-access
```

- 私有数据获取 / secret 只在 `server-component` / `data-access` / `server-action`；**禁 `client-component` 直取私有数据或读 secret**（违反 P1，走 server-action）。secret 永不落文档，只写引用方式（环境变量名）。
- 一份业务数据只有一个 `data-access` owner；`server-action` 走 `data-access` 落数据，不在交互链里直连 ORM/远端；不得发明 Manager/Helper/Util 等无行为来源结构（名词先行反模式）。

**写作顺序（自底向上，详细 chapter_loop 推荐层级）**：

```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```

先固化类型与 schema（domain-type），再定数据访问合同（data-access）、变更面（server-action），然后渲染编排（server-component）、交互（client-component）、展示（ui-component），最后收口路由段（route）。同一 feature 的 data-access 与其 domain-type 视为同一小批次优先完成。

**pending L2 拦截（full 链）**：承接索引命中 L2 为 pending 的 doc_type（route / ui-component / domain-type / server-action）时，必须在 design-main.md 显式声明 `L2豁免：<doc_type> 理由：…`（按 L1 合同八问展开的风险与补齐计划），否则 Gate 拦截；首选先补 L2 再进详细。light 链按 L1 合同八问展开并标注 `l2_status: pending`。

---

## 5. 示例实证 vs 生产级补充（全程区分，禁止混淆）

- **示例实证**：参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是 **Pages Router + Nextra + MDX + gray-matter** 的轻量 blog starter（故意简化）。可直接佐证的内容模型：`package.json`（`nextra ^2.0.0-beta.5` + `gray-matter ^4.0.3` + `rss ^1.2.2`，scripts 用 `next` 裸命令）；`pages/posts/*.md`（front-matter：title/date/description/tag/author → domain-type 雏形）；`pages/tags/[tag].mdx`（动态路由 `useRouter().query`，客户端 hook）；`scripts/gen-rss.js`（build 前用 `gray-matter` 读 front-matter 生成 `public/feed.xml` → data-access 形态参考）；`tsconfig.json`（**`strict: false` + `target: es5`**，仅作内容模型基线、非生产基线）。
- **生产级补充（golden-path 以此为准）**：本平台锁定 **App Router 生产最佳实践**，把上面示例仅当「内容模型基线」。关键差异必须显式标注：① 路由模式 **App** 而非 Pages；② TS **`strict: true`** 而非示例的 `false`；③ 内容获取走 RSC server-component / data-access，而非 Pages 的 `getStaticProps`；④ RSS/SEO 走 App Router `app/feed.xml/route.ts` + `metadata` API，而非示例的 build 脚本 + `next/head`。凡示例与生产基线冲突，**以生产基线为准**（把 `getStaticProps` 当 RSC 写、或在 server-component 内调 `useState` 均为 P1）。

---

## 6. 硬规则速览（golden-path 锁定，违反进不了对应 Gate）

> 表列结构与 `harness/index.md` 同口径：**规则 | 内容 | 违反判级**（七条均为 golden-path 锁定项，违反即阻塞对应 Gate，判级 P1；括号内为典型反例）。

| 规则 | 内容 | 违反判级 |
|------|------|:--------:|
| **1 TS strict** | `strict: true`，禁 `any` 兜底（必要处显式 `unknown` + 收窄）。反例：`(data as any).title` 兜底 | P1 |
| **2 server-first / `'use client'` 最小化** | 默认 RSC，仅在需 state/event/浏览器 API/hooks 的最小叶子标 `'use client'`。反例：整页顶部一行 `'use client'` 把全树降级为客户端 | P1 |
| **3 私有数据/secret 边界** | 私有 fetch、密钥、token 只在 server-component/data-access/server-action；client-component 禁直取；secret 不落文档。反例：client-component 内 `fetch('/api/secret', { headers: { token } })` | P1 |
| **4 route 段约定** | `page`/`layout`/`loading`/`error.tsx` 按 App Router 语义就位（`error.tsx` 必须 `'use client'`）。反例：有数据获取的段缺 `error.tsx`/`loading.tsx` | P1 |
| **5 metadata/SEO 标准化** | 用 `metadata` 导出或 `generateMetadata`；动态页给 OG/title/description。反例：动态详情页无 metadata、靠 `next/head` 拼 | P1 |
| **6 样式隔离** | CSS Modules 或 Tailwind，**禁全局样式污染**（除受控 `globals.css` 设计 token 层）。反例：组件内写裸全局选择器污染他处 | P1 |
| **7 错误边界** | 每个有数据获取的 route 段提供 `error.tsx`（兜底）+ `loading.tsx`（Suspense 边界）。反例：数据获取失败白屏、无 fallback | P1 |

完整禁止清单与门禁映射见 `.trellis/spec/guides/golden-path.md`。涉鉴权/私有数据/secret 的单元，详细阶段须附合规与边界依据（详细 Gate 取证）。

---

## 7. 五道 Gate 表（verify 脚本同口径）

| Gate | 通过条件（满足才进下一阶段） | 阻塞项（任一命中即不通过） |
|------|------------------------------|----------------------------|
| **需求 Gate** | 需求五要素齐全：行为 / 前置条件 / 状态变化 / 失败路径 / 验收场景 | 缺任一要素 → 不进概要 |
| **概要 Gate** | 行为有唯一 owner + 三问理由（为何属它/为何不属别人/为何独立存在）；归属符合分层依赖律；承接索引非空且覆盖全部 owner，`detail_doc_type` 落在七类内；架构总览（一句话架构 + 分层图 + 页面流 + UC 表 + UC 承接表 + 时序图策略）齐全 | 无唯一 owner、归属违反分层律（如 client-component 持数据获取）、承接索引缺失、`detail_doc_type` 用了七类外的名 → 不进详细 |
| **详细 Gate** | 合同八问无缺项；追溯到概要 owner；每行为有测试映射（成功 + 全部失败路径）；涉鉴权/私有数据/secret 的单元附合规与边界依据；八问之 8 逐单元存在；full 链章节闭合（索引↔chapters 双向）+ pending L2 命中项豁免齐全 | 合同八问缺项、追溯断链、无测试映射、client-component 直取私有数据/读 secret、secret 落文档、`l2_status: pending` 无豁免 → 不进实现 |
| **实现 Gate** | `implement.md` 计划合同齐全；mutable evidence 中 analyze（`tsc --noEmit`）/ test（Vitest+RTL / Playwright，测试名级）/ lint（ESLint+Prettier）/ 边界合规 均有证据 | 任一无证据、计划合同或 mutable evidence 不全、`'use client'` 滥用、全局样式污染、`any` 兜底 → 不进 commit |
| **审核/复盘 Gate** | 存量豁免判定：清单内（SLOT-18）记债不阻塞；清单外新增违例阻塞；findings 带文档/章节锚点；缺陷回上游修 | 清单外新增违例、就地补造掩盖上游缺陷 → 阻塞 |

**严重度**：P1（违反硬规则/红线、八问缺项、追溯断链、边界缺失、doc_type 越界——阻塞）；P2（合同不完整但可局部补）；P3（表述建议）。**审核互斥分支**：前置失败 → 只输出前置缺口与修复动作，不展开逐章审核；前置通过 → findings（severity/location/problem/suggestion）+ 概况 + 三选一结论（可进入下一阶段 / 带假设可进入 / 不可进入）。

---

## 起步指引

1. 读 `harness/index.md`（L1 入口，含 Pre-Development Checklist 与本文未展开的细节）。
2. 读 `conventions/project-conventions.md` 并通过校验清单 C1~C6（未填即停）。
3. 读 `guides/golden-path.md`（分层依赖律 + §6 硬规则的完整禁止清单）。
4. 按任务所处阶段读 §2/§3 指向的 SSOT，并登记进 `implement.jsonl` / `check.jsonl`（带 reason）。
