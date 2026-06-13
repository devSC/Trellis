# conventions/ 索引（Guru H5/Web 平台 · Next.js）

> 本文件是 H5/Web spec 库**项目约定槽位**的导航入口。它**只做导航与口径对齐**，不承载任何项目级取值正文（取值正文只许落在 `project-conventions.md`）。
> 平台基线：**Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)**。方法学母版对齐 `guru-flutter-client` 同名 SSOT（双层结构：方法锁约定、取值不进配置包）。
> 参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是 **Pages Router + Nextra + MDX + gray-matter** 的轻量 blog starter（故意简化、非生产形态）。golden-path 以 **App Router 生产最佳实践**为准，把该示例仅作**内容模型基线**。全文凡引用该示例处一律标注「**示例实证**」；凡 App Router 生产形态的补充一律标注「**生产级补充**」，二者不得混淆。
> 规则唯一真源：所有 writing/review skill 与 `guru_gate` 的硬前置**只装载本目录文件、不复写**；冲突时 L1（`harness/detail/detail-structure-single-source.md`）> L2（`harness/detail/detail-type-*.md`）> 本目录 references > SKILL.md。
> **doc_type 权威**：全程只认 H5 七类（`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`）。本目录任何处**不得**出现 flutter 的 `controller`/`usecase`/`repository-datasource`/`page-entry` 或 Go 的 `transport`/`service`/`repository`/`domain` 等类型名（仅在 §6 映射列作「方法学对应」时引用，且明确标注「不照抄类型名」）。
> **槽位编号规范（与 go/ios 平台对齐，单一体系）**：项目约定**只用 `SLOT-NN` 单一前缀**，**不用 `SLOT-HN`/`SLOT-MN`/`C1~C5` 等分套或派生编号**充当槽位号。编号自 `SLOT-01` 起连续递增、创建后不复用不重排、删除留洞，**存量违例清单固定为最后一个槽位**。本 `index.md` §2 槽位全景共 **12 个槽位**（`SLOT-01~SLOT-12`，末位 SLOT-12 = 存量违例清单）；落地取值文件按 `project-conventions.template.md`（`SLOT-01~SLOT-18`，更细粒度，末位 SLOT-18 = 存量违例清单）填写；示例样例 `nextjs-blog.project-conventions.md` 为 `SLOT-01~SLOT-16`（末位 SLOT-16 = 存量违例清单）。三份文件**槽位粒度可不同（如 go/ios 母版亦然），但前缀、连续编号纪律、「存量违例清单置末位」三条铁律一致**；不同文件内的同名概念以语义对齐、不强求同号。`C1~C6` 是**校验项编号**（见 §3），不是槽位号；README / harness 速览里的简写 `C1~C5` 指「必须可定位取值的关键必填槽位子集」，其指向的 SLOT-NN 见 §3 末。

---

## 1. 三类文件职责（导航）

本目录采用「方法锁取值、取值不进配置包」的双层结构。三类文件各司其职，缺一不可：

| 文件 | 职责 | 谁维护 | 是否参与校验 |
|------|------|--------|:---:|
| `project-conventions.md` | **当前项目取值的唯一权威**。按 `project-conventions.template.md` 复制填写，含元信息、`SLOT-01~SLOT-18` 取值（每槽位带代码证据路径）、校验清单 C1~C6、SLOT-18 存量违例清单。所有阶段硬前置只认本文件。**缺失时按下方模板复制建立并填写。** | 各 App 仓库（落位 `.trellis/spec/conventions/project-conventions.md`，PROTECTED：`trellis update` 永不覆盖） | ✅ 唯一生效 |
| `project-conventions.template.md` | **空槽位模板**（新项目起点）。复制 → 删说明 → 逐槽位填取值与证据。模板本身不生效，只作骨架。 | 配置包随版本演进 | ❌ |
| `nextjs-blog.project-conventions.md` | **next.js blog 示例取值样例**（仅参考）。演示一份「示例实证」基线长什么样：Pages Router + Nextra + MDX + gray-matter + RSS 生成（见 §7 与 §8）。其槽位用与本文同构的单一 `SLOT-NN` 体系（`SLOT-01~SLOT-16`，末位 SLOT-16 = 存量违例清单）、自检对标 §3 的 C1~C6。**不直接生效、不参与任何校验**，且因其为 Pages Router + `strict:false`，**不得**当作 App Router 生产取值照搬。 | 配置包样例 | ❌ |

**铁律**：writing/review/Gate 的硬前置只读 `project-conventions.md`；`template` 与 `blog` 样例永不参与校验。一个新仓库若只放了 template 没填取值，视为「项目约定未就绪」，硬前置不通过。

> 与 flutter 母版的差异：flutter 样例为 `calorie`/`seek` 两份真实 App；H5 平台样例锚定单一参考仓库 `next.js/examples/blog`，但**该仓库是简化 starter 而非生产 App**，故样例文件名为 `nextjs-blog.project-conventions.md` 且其取值需逐条标注「示例实证 vs 待生产级补充」。三类文件的职责结构与 flutter `conventions/index.md` 完全一致。

---

## 2. 槽位地图（SLOT 全景 → 钉死什么 → 谁消费）

下表是本导航口径下的 **12 个主题槽位全景地图**（`SLOT-01~SLOT-12`，末位 SLOT-12 = 存量违例清单）：「槽位 → 决策问题 → 团队栈级 canonical → 项目级可选范围 → 消费方」，**取值正文不在此**（见 `project-conventions.md`）。落地填写以 `project-conventions.template.md` 的更细粒度 `SLOT-01~SLOT-18` 为准（如把本表「数据库/ORM」拆成数据获取/缓存与 DB/ORM 两槽、把 metadata/SEO、错误边界、目录分界等单列）——这与 go/ios 母版「index 全景地图槽数可粗于 template 填写骨架」一致；两侧靠主题语义对齐，编号纪律（单一 `SLOT-NN` 前缀、连续递增、存量违例置末位）一致。

| 槽位 | 决策问题（钉死什么） | 团队栈级 canonical 钉死值 | 项目级可选范围 / 迁移方向 | 主要消费方 |
|------|---------------------|--------------------------|--------------------------|-----------|
| **SLOT-01 路由模式** | App Router 还是 Pages Router？新代码进哪个目录（`app/` vs `pages/`）？新旧谱系分界？ | **新代码一律 App Router**（`app/`）；Pages Router 仅存量遗留 | 旧 `pages/` 只读维护、禁新建路由段；blog 示例的 `pages/`（**示例实证**）仅作内容模型基线，不作生产路由取值（**生产级补充**） | `route` 合同、hooks 目录拦截、implementation-review |
| **SLOT-02 内容源** | 页面内容来自 MDX / Headless CMS / ORM 查询的哪一种？解析与读取入口在哪一层？ | 内容读取**只在** `server-component`/`data-access`/`server-action`，禁 `client-component` 直取 | MDX（`@next/mdx` 或 `next-mdx-remote`，对标 blog 示例的 `gray-matter`+MDX，**示例实证**）/ CMS（Contentful/Sanity 等）/ ORM（Prisma/Drizzle）；单项目内一种主源 | `data-access` 合同、`domain-type`（frontmatter schema）、implementation-review |
| **SLOT-03 状态管理** | 客户端状态用 none（仅 RSC + URL state）/ React Context / Zustand 中哪个？状态 owner 落在哪类组件？ | 状态写 owner 唯一：交互状态只在 `client-component`；**server-first，能不上状态库就不上** | `none`（默认，推 server-first + searchParams）/ `Context`（局部）/ `Zustand`（跨页共享）；单项目内一种 | `client-component` 合同、implementation-review |
| **SLOT-04 UI 组件库** | 复用组件基座用 shadcn/ui 还是 MUI（或自建）？`ui-component` 的来源与定制方式？ | `ui-component` 纯展示、无数据获取、无业务（通用硬规则）；组件库二选一钉死 | `shadcn/ui`（Radix + Tailwind，无运行时主题）/ `MUI`（运行时主题）/ 自建；单项目内一种基座 | `ui-component` 合同、`client-component` 装配、implementation-review |
| **SLOT-05 样式方案** | Tailwind 还是 CSS Modules（或二者分界）？全局样式入口与隔离规则？ | **样式隔离**：禁全局污染（除 design token / reset）；`globals.css` 只放 token 与基线（通用硬规则） | `Tailwind`（utility，配合 SLOT-04 shadcn）/ `CSS Modules`（`*.module.css` 局部作用域）；单项目内一种主方案，分界须写明 | `ui-component`/`client-component`/`server-component` 合同、implementation-review |
| **SLOT-06 数据库 / ORM** | 是否有 DB？用 Prisma / Drizzle / 直连？schema 与 client 实例放哪？迁移工具？ | DB/secret 访问**只在** `data-access`/`server-action`（server-only），禁 `client-component` 触达（通用硬规则） | 无 DB（纯 MDX/CMS）/ Prisma / Drizzle；client 单例注入点固定，迁移目录组织钉死 | `data-access` 合同、`server-action` 合同、implementation-review |
| **SLOT-07 认证** | 是否启用认证？NextAuth(Auth.js) / 自建 session？session 读取与校验落在哪一层？ | secret/session 读取**只在** server 侧（`server-component`/`data-access`/`server-action`）；`client-component` 只拿脱敏后的最小态 | 无认证 / `NextAuth`(Auth.js) / 自建；middleware 鉴权落点、回调 URL 钉死 | `server-action`/`data-access`/`route`(middleware) 合同、合规红线 review |
| **SLOT-08 图像优化** | 图像统一走 `next/image` 还是允许裸 `<img>`？远程图域白名单？静态资源目录？ | 优先 `next/image`（LCP/CLS 优化）；远程图须 `next.config` `images.remotePatterns` 白名单（通用硬规则） | `next/image` 全量 / 局部豁免（须注明理由）；blog 示例用 `public/images/*`（**示例实证**），生产远程图域名白名单为（**生产级补充**） | `ui-component`/`server-component` 合同、implementation-review |
| **SLOT-09 测试** | 单测/组件测试用 Vitest+RTL 还是 Jest+RTL？E2E 用 Playwright？测试目录是否镜像 `app/` 结构？ | **新代码 Vitest + React Testing Library**（单测/组件）；E2E 用 **Playwright**；目录镜像源码 | `Vitest`+RTL（推荐）/ `Jest`+RTL；E2E `Playwright`（推荐）/ Cypress；server-component 测试策略钉死 | 合同八问之 7（测试映射）、implementation 证据节 |
| **SLOT-10 lint / 格式化** | ESLint 配置（`next/core-web-vitals`?）+ Prettier？`tsconfig` strict 档位？类型检查命令？ | **TS strict 必开**（`strict: true`，通用硬规则）；ESLint 启 `next/core-web-vitals`；Prettier 统一格式 | 具体 rule 集与 Prettier 配置按项目；注意 blog 示例 `tsconfig` 为 `strict:false`（**示例实证**），生产必须 `strict:true`（**生产级补充**） | implement Gate 证据节、code-logging/comments skill |
| **SLOT-11 部署 / 运行时** | 部署到 Vercel 还是自托管（Node/Edge runtime）？环境变量来源与 `NEXT_PUBLIC_` 边界？构建命令？ | secret 环境变量**禁带** `NEXT_PUBLIC_` 前缀（会泄漏到客户端，通用硬规则）；构建/产出命令钉死 | `Vercel`（默认）/ 自托管（`next start` / Docker）；runtime（`nodejs`/`edge`）按 route 段；blog 示例 build 前跑 `gen-rss.js`（**示例实证**） | implement 执行节、`route` 运行时声明、合规红线 review |
| **SLOT-12 存量违例清单** | 已知存量架构违例有哪些（供 review 存量豁免判定：触碰记债不阻塞、新增违例阻塞）？ | —（数据源，逐条登记） | 逐条：违例描述 + 文件路径；可为空但须显式声明「无」 | 所有 review 的存量豁免判定 |

> 槽位编号纪律：SLOT 编号创建后**不复用、不重排**，删除留洞。新增槽位往后追加。
> 取值「待定」上限：`project-conventions.md` 中待定槽位 ≤ 2，且每个待定项须写明决策人与期限，否则项目约定视为未就绪（硬前置 C2 不通过）。

### 2.1 槽位与硬规则的边界（不可被槽位豁免的 golden-path 钉死约定）

以下属**平台级硬规则**，是归属与合同的硬基准，**任何槽位取值不得与之冲突**（违反 = review 直接 fail）。完整正文见 `.trellis/spec/guides/golden-path.md`，此处只回顾以便填表对照：

- **TypeScript strict**：`tsconfig.json` `strict: true` 全程开启；禁用 `any` 兜底关键类型边界（blog 示例 `strict:false` 是简化 starter，**不得作为生产取值**）。
- **server-first，`'use client'` 最小化**：默认 `server-component`；`'use client'` 只标在**真正需要交互**（状态/事件/浏览器 API/hooks）的叶子组件上，禁止整页 `'use client'`。
- **私有数据获取/secret 只在 server 侧**：`server-component`/`data-access`/`server-action` 可读 DB/secret/内部 API；**禁 `client-component` 直接 fetch 私有数据源或读取未脱敏 secret**。
- **route 段约定**：App Router route 段文件名固定 `page` / `layout` / `loading` / `error`（外加按需 `not-found` / `template` / `route` handler）；语义不得错配。
- **metadata / SEO 标准化**：route 段通过 `metadata` 导出或 `generateMetadata()` 提供 SEO 元数据，禁止散落手写 `<head>`。
- **错误边界**：每个有数据依赖的 route 段须有 `error.tsx`（错误边界）兜底；服务端错误不得直接抛到客户端裸渲染。
- **样式隔离**：CSS Modules / Tailwind，禁全局污染（`globals.css` 仅放 token/reset/字体）。
- **分层依赖律（owner 归属硬基准，见 §6.1）**：服务端链 `route → server-component → data-access → domain-type`；交互链 `client-component → ui-component`；变更链 `server-action → data-access`。禁反向 / 跳层。

槽位只在这些硬规则**未覆盖的自由度**上取值（如内容源选 MDX 还是 CMS、样式选 Tailwind 还是 CSS Modules）。校验清单 C5 即检查取值不与上述硬规则冲突。

---

## 3. 校验清单（writing/review 硬前置使用，C1~C6）

装载本约定的任一 Skill 必须先对 `project-conventions.md` 执行以下校验，**任一不通过即终止并输出前置缺口与修复动作**：

- [ ] **C1 元信息齐全**：App 名称 / npm 包名 / 仓库路径 / 填写日期 / 填写人 / 取值依据（实测扫描或团队决策+ADR 链接）齐全。
- [ ] **C2 槽位完整**：`project-conventions.md` 按模板 `SLOT-01 ~ SLOT-18` 全部存在；「待定」槽位 ≤ 2 且均写明决策人与期限。
- [ ] **C3 证据可定位**：每个已填槽位至少 1 条代码证据路径（不校验路径内容，但路径须真实存在于目标仓库，如 `app/(blog)/posts/[slug]/page.tsx`、`tsconfig.json`、`next.config.js`）。
- [ ] **C4 doc_type 纯净**：取值正文不引入 H5 七类之外的 doc_type 名；**不出现 flutter/Go 类型名**（`controller`/`usecase`/`repository-datasource`/`page-entry`/`transport`/`service`/`domain` 等），也不自创 `handler`/`provider`/`hook-layer` 之类。
- [ ] **C5 不与硬规则冲突**：取值不得违反 §2.1 平台硬规则（TS strict、server-first/`'use client'` 最小化、secret 只在 server 侧、route 段命名、metadata/SEO、error.tsx 边界、样式隔离、分层依赖律）。这些不可被槽位豁免。
- [ ] **C6 存量清单存在**：SLOT-18 存量违例清单存在（可为空清单，但必须显式声明「无」）。

> 与 flutter 母版差异：flutter 是 C1~C5；H5 增列 **C4 doc_type 纯净**（因 H5 七类与 flutter 九类、Go 多类不同名，需显式拦截类型名串台），故为 C1~C6。C1~C6 是**校验项编号**，与槽位编号（`SLOT-NN`）是两套独立序列；落地取值文件按模板填 `SLOT-01~SLOT-18`，本 §2 全景地图按主题归并为 `SLOT-01~SLOT-12`，示例样例为 `SLOT-01~SLOT-16`（详见开篇槽位编号规范）。

> **C1~C5「关键必填槽位」映射**（README / harness 速览口径——「必须可定位取值」的关键子集，**不是另一套槽位编号**）：C1↔元信息（template §0）；C2↔全部取值槽 `SLOT-01~SLOT-17`（路由模式 / 目录分界 / 内容源 / 数据获取缓存 / 错误边界 / 领域类型 schema / 状态管理 / UI 库 / 样式 / 图像 / 认证 / 数据库 / TS·lint / 测试 / 构建脚本 / 部署 / metadata·SEO，逐项可定位取值）；C3↔每槽位证据路径；C4↔doc_type 纯净（七类锁定）；C5↔不与硬规则冲突。存量违例清单 `SLOT-18` 由 C6 单独校验。**速览中提到的「SLOT-15 存量豁免」是历史笔误，应为 `SLOT-18`**（README / harness 已同步修正）。

---

## 4. 与 `guru_gate` 兼容口径（五阶段 Gate 如何消费本目录）

本目录是五阶段工作流每个阶段硬前置的装载点之一。装载路径一律用**安装后路径**（`trellis init -t guru-h5-web` 落位 `.trellis/spec/`，PROTECTED：`trellis update` 永不覆盖）：

```
需求(prd.md)         ← 需求三件套 SSOT（五要素：行为/前置条件/状态变化/失败路径/验收场景）
概要(design §概要)   ← .trellis/spec/harness/overview/overview-structure-single-source.md
                       （归属表 + chapter_target→detail_doc_type 承接索引 + technology_decision_handoff[]）
详细(design §详细)   ← .trellis/spec/harness/detail/detail-structure-single-source.md
                       + 涉及类型的 .trellis/spec/harness/detail/detail-type-{server-component,client-component,data-access}.md
实现(implement)      ← .trellis/spec/guides/golden-path.md
                       + .trellis/spec/harness/implementation/implementation-trace-contract.md（trace 四节）
审核(check)          ← 各 SSOT 审核基线 + 本目录 project-conventions.md 的 SLOT-18 存量豁免
```

### 4.1 各阶段从本目录消费什么

| 阶段 | guru_gate 口径（缺即拦截） | 本目录消费点 |
|------|---------------------------|-------------|
| 需求 Gate | **需求五要素**齐全：每条行为有 前置条件 / 触发 / 状态变化 / 失败路径 / 验收场景 | C1~C6 通过（项目约定就绪是任何阶段前置） |
| 概要 Gate | **归属判定表**（行为→唯一 owner 层+三问理由，无分层依赖律违例）+ **承接索引**（`chapter_target → detail_doc_type`，覆盖全部 owner）+ `technology_decision_handoff[]` 字段完整 | owner 层取 H5 七类对应层（见 §6）；SLOT-01/02/03/04/07 影响归属与命名 |
| 详细 Gate | **合同八问**逐单元完整（承接 BHV / 输入输出错误 / 读写状态 / 依赖正反面 / 失败收口 / 事件后置 / 测试映射 / 不得补造）+ 追溯到概要 owner + `UNIT-<slug>` 无断链 | SLOT-02/03/05/06/07/09 进入对应类型合同；pending L2 类型须 `L2豁免` 或先补 L2（见 §6） |
| 实现 Gate | **trace 四节**齐全（计划 / 执行 / 证据 / 阻塞与偏差）+ 静态检查与测试有命令级证据 | SLOT-09（测试）、SLOT-10（lint/strict）、SLOT-11（构建/部署）进入执行与证据节 |
| 审核 | 存量豁免判定：SLOT-18 内记债不阻塞，清单外新增违例阻塞 | SLOT-18 是存量豁免唯一数据源 |

### 4.2 编号与追溯（机器追溯依据）

- **行为**：`### BHV-NNN <短名>`（prd 标题），NNN 数字，创建后不复用不重排，删除留洞。
- **设计单元**：`### UNIT-<slug>`（详细设计标题，语义 kebab-case，如 `UNIT-post-detail-server-component`）。
- **下游引用裸 token**：归属表、详细合同、测试映射、实现切片对行为/单元的引用一律写**裸** `BHV-NNN` / `UNIT-<slug>` 编号 token；约定文件引用槽位同样写裸 `SLOT-NN`（不加链接包裹以便机器解析）。
- `guru_gate.py trace-matrix <task_dir> --write` 据此生成「行为×归属×单元×测试×切片」矩阵；**断链（幽灵引用 / 无承接行为 / 孤儿单元）被 Gate 拦截，进不了详细/实现 Gate**。

---

## 5. 详细合同八问（H5 适配口径，详细 Gate 逐单元校验）

每个设计单元以 `### UNIT-<slug>` 定义，合同须**显式覆盖**以下八问；缺项即详细 Gate 拦截：

1. **承接行为**：本单元承接哪些 `BHV-NNN`（裸 token），与概要归属表一致。
2. **输入 / 输出 / 错误**：props/参数（含 RSC 的 `params`/`searchParams`、`server-action` 的入参）、返回（JSX / `Promise<T>` / `ActionResult`）、错误类型与边界。
3. **读写状态**：读哪些数据源、写哪些状态（client 状态 owner 唯一；server 侧不持有可变全局态）。
4. **依赖（正反面）**：依赖谁（须遵守 §6.1 分层依赖律）+ **明确不依赖谁**（如 `client-component` 不得 import `data-access`，`ui-component` 不得做数据获取）。
5. **失败收口**：错误在哪一层 catch/转换（按 SLOT-02/06/07）；route 段是否有 `error.tsx` 兜底；server-action 失败返回形态。
6. **事件 / 后置**：副作用、`revalidatePath`/`revalidateTag`、缓存失效、重定向（`redirect()`）等后置动作。
7. **测试映射**：本单元由哪些测试覆盖（按 SLOT-09：Vitest+RTL 组件测试 / Playwright E2E / RSC 数据获取测试）。
8. **不得补造声明**：超出承接 BHV 的能力一律不实现；缺承接的需求回概要补归属，禁下游补造。

---

## 6. doc_type 七类 → owner 层 → L2 状态（详细阶段承接基准）

详细设计承接索引的 `detail_doc_type` **只能取以下七类**（H5_BRIEF 钉死，权威，禁改名/增减/换数）。owner 层归属是分层依赖律的硬基准。

| doc_type | 覆盖对象 | owner 层 | L2 状态 | flutter 对应（仅供方法学映射，**不照抄类型名**） |
|----------|---------|---------|:---:|------|
| `server-component` | RSC 服务端组件（渲染 + 数据获取编排，默认形态） | 渲染层（server） | **v1 提供 L2** | controller（render 编排职责） |
| `client-component` | `'use client'` 交互组件（状态 / 事件 / hooks） | 交互层（client） | **v1 提供 L2** | controller（interactive 职责） |
| `data-access` | 数据访问层（fetch 封装 / 内容源 MDX/CMS / ORM 查询） | 数据层（server-only） | **v1 提供 L2** | repository + datasource |
| `route` | App Router route 段（`page`/`layout`/`loading`/`error` + metadata/SEO） | 路由层（server） | pending | page-entry + routes |
| `ui-component` | 展示型可复用组件（纯展示、无数据获取、无业务） | 展示层 | pending | （无直接对应；flutter design widget） |
| `domain-type` | TS 类型 / zod schema / 领域模型 | 类型层 | pending | model |
| `server-action` | Server Actions / route handlers（变更 / API endpoint） | 变更层（server） | pending | usecase（变更编排） + api |

**v1 L2 供给**：`.trellis/spec/harness/detail/detail-type-{server-component,client-component,data-access}.md`（render/interactive/data 三元组，对标 flutter 三类 L2 controller/usecase/repository-datasource）。

**pending 四类**（`route` / `ui-component` / `domain-type` / `server-action`）：按 L1 合同八问展开（§5），文档头标注 `l2_status: pending`。**full 链命中 pending L2 类型时，必须在 `design-main.md` 显式声明 `L2豁免：<doc_type> 理由：…`（含按八问展开的风险与补齐计划），否则 gate 拦截**；首选先补对应 L2 再进详细设计。light 链按 L1 合同八问展开并标 `l2_status: pending` 即可。

### 6.1 owner 层与分层依赖律（归属硬基准，违反 fail）

```
服务端链：route  →  server-component  →  data-access  →  domain-type
交互链：  client-component  →  ui-component
变更链：  server-action  →  data-access
```

**硬禁止（review / lint 查 import 方向与 `'use client'` 边界）**：
- ❌ `client-component` import `data-access` / 直接 fetch 私有数据源 / 读未脱敏 secret（跳层 + secret 泄漏）。
- ❌ `ui-component` 做数据获取或含业务逻辑（必须纯展示）。
- ❌ `data-access` / `domain-type` 反向依赖 `route` / `server-component`（反向依赖）。
- ❌ `server-component` 标 `'use client'`（混淆 server/client 边界）；整页 `'use client'`。
- ❌ secret 环境变量带 `NEXT_PUBLIC_` 前缀（泄漏到客户端）。

### 6.2 写作顺序（自底向上，与分层依赖律一致）

```
domain-type  →  data-access  →  server-action  →  server-component  →  client-component  →  ui-component  →  route
```

层级 checkpoint：类型层（domain-type / zod schema）固化后核对 frontmatter/数据契约与 SLOT-02 内容源一致；数据层（data-access / server-action）核对 secret 只在 server 侧、错误收口点按 SLOT-06/07、`revalidate*` 后置完整；渲染层（server-component / route）核对 metadata/SEO 与 error.tsx 边界齐全、UNIT↔BHV 承接闭合；交互层（client-component / ui-component）核对 `'use client'` 最小化、状态 owner 唯一、ui-component 零数据获取。

---

## 7. 好 / 坏例子（填写质量基线 · 严格区分示例实证 vs 生产级补充）

填 `project-conventions.md` 时按下列基线把握取值的「可验证性」与「示例/生产」边界：

- ✅ 好（SLOT-02 内容源）：「MDX 内容源：`content/posts/*.mdx`，frontmatter 用 `gray-matter` 解析（**示例实证**：对标 blog 示例 `scripts/gen-rss.js` 用 `matter(content)` 读 `data.title/date/description/tag/author`），生产用 `next-mdx-remote` 在 `app/posts/[slug]/page.tsx` 的 RSC 内读取（**生产级补充**：示例是 Pages Router 的 Nextra 渲染，生产改为 App Router RSC）；frontmatter 形状由 `domain-type` 的 zod schema 约束。证据：`content/posts/`、`lib/posts.ts`。」——取值具体、有落点、有证据、明确区分示例与生产、不与硬规则冲突。
- ❌ 坏（SLOT-02）：「用 MDX 写文章」——无解析库、无读取层落点、无证据路径，C3 不通过；且未说明读取是否落在 server 侧，留下 secret/分层盲区。
- ✅ 好（SLOT-10 lint/strict）：「`tsconfig.json` `strict: true`；ESLint extends `next/core-web-vitals`；Prettier 统一格式，`pnpm lint` + `pnpm typecheck`（`tsc --noEmit`）。**注意**：blog 示例 `tsconfig` 为 `strict:false`、`target:es5`（**示例实证**，简化 starter），生产**必须** `strict:true`（**生产级补充**）。证据：`tsconfig.json`、`.eslintrc.json`。」
- ❌ 坏（C5 冲突）：「为快速上线把首页整页标 `'use client'` 并在组件里直接 `fetch('/internal/secret-api')`」——违反 server-first/`'use client'` 最小化 + secret 只在 server 侧两条硬规则，C5 直接拦截，不得作为合法取值登记。
- ❌ 坏（C4 串台）：「数据访问层叫 `repository`，渲染编排叫 `controller`」——引入 flutter 类型名，C4 直接拦截；H5 必须用 `data-access` / `server-component`。

---

## 8. 装载次序速查（任何阶段开工前）

1. 读 `.trellis/spec/conventions/project-conventions.md`，跑校验清单 C1~C6——不过则停止，先完成项目约定。
2. 读 `.trellis/spec/guides/golden-path.md`（TS strict、server-first、分层依赖律与禁止清单）。
3. 按本任务阶段读对应 `.trellis/spec/harness/*` SSOT（含 §6 涉及的 `detail-type-*.md`），并登记进任务 `implement.jsonl` / `check.jsonl`（带 reason）。
4. 产物语言：中文优先（英文仅限代码标识符、命令、路径、框架名、协议字段、外部专有名词、原文引用）。

---

## 9. 不适用场景（本目录不解决的问题）

- **不写五阶段产物**：BHV/UNIT、概要归属表、详细合同八问、implement trace 一律在任务目录或设计包内产出，不在 conventions/。
- **不复写硬规则正文**：TS strict、server-first、分层依赖律、route 段约定、metadata/SEO、error.tsx 边界、样式隔离等正文在 `golden-path.md`；本目录只回顾与对照，避免双真源漂移。
- **不把 blog 示例当生产取值**：`next.js/examples/blog` 是 Pages Router + Nextra + `strict:false` 的简化 starter；它只作内容模型基线（**示例实证**），App Router / RSC / `strict:true` / metadata / error 边界等生产形态须另行钉死（**生产级补充**）。混用即 C5/C1 不过。
- **不替代 ADR**：槽位取值变更的决策记录走 ADR；conventions/ 只承载「当前生效取值 + 证据」，不承载决策推导过程。
- **不裁决跨平台差异**：Flutter / iOS / Go 等其它平台的约定各自有 `guru-<platform>/conventions/`，本目录只管 H5/Web（Next.js）。
- **不做语义评审**：「取值是否合理」由对应 review skill 的人工 Gate 判定；本目录的校验（C1~C6）只查结构存在性、doc_type 纯净与硬规则不冲突，「判不动的规则不进校验」。

> 缺陷只能回上游修：审核发现结构性缺陷（归属错、合同越界、doc_type 串台、示例当生产）回到拥有该决策的阶段修订，禁止下游补造。
