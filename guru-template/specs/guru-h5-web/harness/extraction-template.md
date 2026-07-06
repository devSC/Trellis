# 复盘萃取模板（九段结构）— Guru H5/Next.js Web 平台

> 平台：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。
> Phase 3.3（spec 回写）由 `trellis-update-spec` 按本模板执行。
> 原则：**不沉淀本次需求事实，只沉淀"这类任务如何被做好"**；一次性内容不进 spec。
> 即使结论是"无可沉淀"，也要走完判断并在任务 journal 记一句原因。
> 装载根：本平台 SSOT 装载路径统一为 `.trellis/spec/harness/*` 与 `.trellis/spec/guides/golden-path.md`。

---

## 0. 平台档案与全程钉死约定（萃取前必须对齐）

萃取动作产出的任何方法/反例/取值，其 `doc_type`、分层、归属，**一律以本平台 H5 详细设计七类权威为准**；禁止照抄 flutter（controller/usecase/repository-datasource）或 Go 后端的类型名。下游任何文件引用 doc_type、单元归属时，必须落到下面这套口径。

### 0.1 doc_type 权威七类（全程唯一，禁止改名 / 增减 / 换数）

| # | doc_type | 覆盖对象 | L2 状态 |
|---|----------|---------|---------|
| 1 | `server-component` | RSC 服务端组件：渲染 + 数据获取编排（默认形态） | **v1 提供** |
| 2 | `client-component` | `'use client'` 交互组件：状态 / 事件 / hooks | **v1 提供** |
| 3 | `data-access` | 数据访问层：fetch 封装 / 内容源（MDX/CMS）/ ORM 查询 | **v1 提供** |
| 4 | `route` | App Router route 段：`page/layout/loading/error.tsx` + metadata/SEO | pending |
| 5 | `ui-component` | 展示型可复用组件：纯展示、无数据获取、无业务 | pending |
| 6 | `domain-type` | TS 类型 / zod schema / 领域模型 | pending |
| 7 | `server-action` | Server Actions / route handlers：变更 / API endpoint | pending |

- v1 三元组（render / interactive / data，对应 flutter 的 controller/usecase/repository-datasource）：
  `detail-type-server-component.md` / `detail-type-client-component.md` / `detail-type-data-access.md`。
- 其余四类 `route` / `ui-component` / `domain-type` / `server-action` 为 **pending**：按 L1 合同八问展开，文档头标 `l2_status: pending`；full 链命中 pending 类型须显式 `L2豁免：<doc_type> 理由：…`，否则 gate 拦截。

### 0.2 owner 层与分层依赖律（归属硬基准，违反 fail）

```
服务端链：route → server-component → data-access → domain-type
交互链：  client-component → ui-component
变更链：  server-action → data-access
```

- 萃取出的任何"归属类方法"若把 owner 放错层（如让 `client-component` 直接调 `data-access`、让 `ui-component` 承载数据获取）→ 该萃取物**不合格**，回退到正确 owner 层再沉淀。

### 0.3 golden-path 硬规则（锁定，萃取物不得与之冲突）

- TypeScript `strict`（**注意区分示例**：blog 示例 `tsconfig.json` 为 `strict:false`/`target es5`，属示例简化，**非生产基线**）。
- server-first，`'use client'` 最小化（仅在需交互处声明）。
- 私有数据获取 / secret 只允许出现在 `server-component` / `data-access` / `server-action`；**禁止 `client-component` 直取**私有数据或 secret。
- route 段约定：`page/layout/loading/error.tsx` 各司其职。
- metadata/SEO 标准化（`generateMetadata` / `metadata` 导出）。
- 样式隔离：CSS Modules / Tailwind，**禁止全局样式污染**。
- 错误边界：`error.tsx` 兜底。

### 0.4 写作顺序（自底向上，萃取"生成顺序类"方法须遵循）

```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```

### 0.5 项目约定槽位（project-conventions，取值差异不进通用方法）

内容源(MDX/CMS) ｜ 状态管理(none/Zustand/Context) ｜ UI 组件库(shadcn/MUI) ｜ 样式方案(Tailwind/CSS Modules) ｜ 测试(Vitest+RTL / Playwright) ｜ lint(ESLint+Prettier) ｜ 数据库 ｜ 认证(NextAuth) ｜ 图像优化(next/image) ｜ 部署(Vercel) ｜ 路由模式(App vs Pages)。

### 0.6 证据分层：示例实证 vs 生产级补充（萃取时必须标注来源）

萃取物涉及"Next.js 怎么做"时，**必须区分两类来源**，不得混为一谈：

- **【blog 示例实证】**：来自 `/Users/devSC/Documents/MyProject/next.js/examples/blog/` 的可验证事实。该示例是 **Pages Router + Nextra + MDX + gray-matter** 的轻量 blog starter（故意简化），适合作为**内容模型基线**（frontmatter 字段、内容源组织、RSS 生成）。可引用的证据文件：`package.json`、`pages/`（Pages Router）、`pages/posts/*.md(x)`、`scripts/gen-rss.js`、`theme.config.js`、`tsconfig.json`。
  - 示例可证：`gray-matter` 解析 frontmatter（`title/date/description/tag/author`）；`scripts/gen-rss.js` 在 build 前生成 `public/feed.xml`；`_app.tsx` 注入 RSS `<link>` 与字体 preload；`pages/tags/[tag].mdx` 动态路由 + `useRouter().query`。
- **【App Router 生产级补充】**：示例**未覆盖**、但 golden-path 以生产最佳实践要求的部分（RSC/Server Components、`'use client'` 边界、`app/` 目录的 `page/layout/loading/error`、`generateMetadata`、Server Actions、`strict` TS、CSS Modules/Tailwind 隔离）。这些**不能引示例为证**，必须标注为生产级补充。

> 萃取硬规则：任何"Next.js 怎么做"的方法句子，要么挂【blog 示例实证】+ 文件锚点，要么挂【App Router 生产级补充】+ golden-path 依据。两者皆无 → 不沉淀（属未验证猜测）。

---

## 1. 萃取产物结构（九段，缺一不可）

按以下结构产出/更新 `.trellis/spec/harness/` 下的方法文件（新方法建新文件并在 `harness/index.md` 登记；既有方法的增量直接改对应 SSOT/L2 并在文件头记一行修订）：

1. **名称**：kebab-case 方法名（如 `h5-route-segment-clarification`、`rsc-boundary-partitioning`、`server-action-mutation-contract`）。
2. **适用场景**：什么样的**一类**任务（不是这一次需求）。须点明落在七类 doc_type 的哪一类 / 哪条依赖链。
3. **输入**：执行该方法需要什么——上游产物（prd 行为编号 `BHV-NNN`、概要归属表、承接索引）、project-conventions 槽位取值、代码现状（`app/` 结构、已有 `'use client'` 边界）。
4. **正向生成动作**：步骤顺序（识别 → 判定 → 展开 → 自检），**动词开头**；涉及生成顺序须遵循 §0.4 自底向上链。
5. **边界约束**：不做什么、不替谁决策、不进入哪个阶段的领地（如详细阶段不改概要 owner）。
6. **输出产物合同**：产物必须包含的结构（章节 / 字段 / 表）；指明对应详细合同八问哪几问。
7. **可验证信号**：人或脚本如何判断达标（对应 Gate / `guru_gate.py` 可检查点：`tsc --noEmit`、ESLint、`'use client'` 静态扫描、trace 矩阵闭合）。
8. **好例子 / 坏例子**：各至少一个，来自本次真实案例（脱敏业务细节，保留结构）；好例须满足分层依赖律，坏例须示范一种典型越层 / 薄文档。
9. **不适用场景**：显式列出别用它的情况（如纯静态 `ui-component` 不要套数据获取方法）。

---

## 2. 萃取前判定清单（自问，全 [ ] 命中才允许沉淀）

- [ ] 它适用于**一类重复**任务，而不是本次需求？（否 → 不沉淀，事实留在任务产物里）
- [ ] 它规定了**生成顺序与判定方法**，而非仅模板/风格？（否 → 写进对应 L2 的备注即可）
- [ ] 换一个相似需求**还能复用**？（否 → 不沉淀）
- [ ] 它的 `doc_type` / owner 落在 §0.1 七类、§0.2 三条依赖链上，**没有改名/越层**？（否 → 先归位再判定）
- [ ] 与既有 SSOT **冲突**？（是 → 走 §5 修订形态判定：局部修订 vs 文档级重构，禁止并行两套口径）
- [ ] 属于**项目级取值差异**（内容源/状态管理/UI 库/样式/测试…）？（是 → 进 `conventions/project-conventions.md` 槽位 + ADR，不进通用方法）
- [ ] 涉及"Next.js 怎么做"时，已按 §0.6 标注**【blog 示例实证】或【App Router 生产级补充】**并附锚点/依据？（否 → 属未验证猜测，不沉淀）
- [ ] 是否触碰 §0.3 硬规则（server-first / `'use client'` 最小化 / 私有数据只在 server 侧 / 样式隔离 / 错误边界）？方法是否**强化**而非削弱这些规则？（削弱 → 不沉淀）

> 结论若为"无可沉淀"：在任务 journal 记一句原因（如"本次仅命中既有 `detail-type-server-component.md` 合同，无新方法可抽"），不留空。

---

## 3. 回写位置路由（H5 适配）

| 萃取物类型 | 写到 | doc_type / 链锚点 |
|-----------|------|------------------|
| 新的一类任务方法 | `.trellis/spec/harness/<阶段域>/` 新文件 + 在 `.trellis/spec/harness/index.md` 登记 | 标注所属 doc_type 七类之一 + 所在依赖链（服务端链/交互链/变更链） |
| 既有方法的修正 / 反例 | 对应 SSOT / L2 文件就地修订（v1 三元组：`detail-type-server-component.md` / `detail-type-client-component.md` / `detail-type-data-access.md`） | 命中 pending 四类时改 L1 `detail-structure-single-source.md` 的合同八问段落 |
| 生产坑（一次根因，多次可踩） | `.trellis/spec/guides/`（如 hydration mismatch、`'use client'` 误标导致 bundle 膨胀、server-only secret 泄漏到 client、`fetch` 缓存语义踩坑）；或迁入 big-question 域后归位 | 必须区分【示例实证】/【生产级补充】 |
| 项目取值变化（内容源/状态管理/UI 库/样式/测试/认证/部署/路由模式） | `conventions/project-conventions.md` 对应槽位（需 ADR 记录） | 槽位名见 §0.5 |
| 存量违例修复 | 从 SLOT-18 清单移除并注明日期 | — |
| App Router vs Pages 取值切换 | `project-conventions.md` 路由模式槽位 + ADR（blog 示例是 Pages Router，生产目标是 App Router，迁移决策不进通用方法） | — |

> 装载提示：被引用方读取时一律走 `.trellis/spec/harness/*`（阶段 SSOT）与 `.trellis/spec/guides/golden-path.md`（分层依赖律与禁止清单）；下游引用单元一律写**裸 token**（`BHV-NNN`、`UNIT-<slug>`），不写散文式描述。

---

## 4. Gate 兼容性映射（萃取物落到哪个阶段的可检查点）

萃取出的方法必须能挂到下面某个阶段 Gate，否则不构成"如何被做好"的可验证沉淀。`verify` 脚本与人工 Gate 同口径。

### 4.1 需求五要素（萃取需求类方法须覆盖）

行为（`BHV-NNN`）/ 前置条件 / 状态变化 / 失败路径 / 验收场景 —— 任一缺失，不进概要。

### 4.2 概要：归属表 + 承接索引（萃取概要类方法须覆盖）

- 每条行为有**唯一 owner** + 三问理由；owner 归属遵循 §0.2 三条依赖链。
- 承接索引非空：`chapter_target → detail_doc_type`（七类之一）双向闭合；缺失 → 回退概要补，禁止详细阶段补造。
- 违反分层依赖律（如 `route` 直接挂 `domain-type`、`server-action` 越过 `data-access`）→ 不进详细。

### 4.3 详细：合同八问（萃取详细类方法须覆盖；所有 doc_type 通用骨架）

每个设计单元以 `### UNIT-<slug>` 定义，逐问回答（缺一不可）：

1. **承接哪些行为**：逐条引用 `BHV-NNN`（幽灵引用 / 无承接行为被 gate 断链拦截）。
2. **输入 / 输出 / 错误结果**：类型（TS 签名级 / zod schema）、取值域、错误枚举（输入表 + 输出表 + 错误类型表）。
3. **读取 / 写入哪些状态**：读写分离；写 owner 与概要归属一致（`client-component` 是其本地 UI 状态唯一写 owner；服务端数据状态归 `data-access` / `server-action`）。
4. **调用哪些依赖，不调用哪些依赖**：正反两面都写。典型反面——`client-component` **不得** import server-only 模块 / 直取 secret；`ui-component` **不得**做数据获取或业务判定；`server-component` 默认无 `'use client'`。
5. **失败如何收口**：每条失败路径处置（重试 / 降级 / `error.tsx` 边界 / 用户提示 / `notFound()`），错误转换位置遵循 `[SLOT-04]`。
6. **产生哪些事件 / 后置结果**：埋点、副作用、`revalidatePath`/`revalidateTag`（server-action）、`redirect`（逐条写消费方）。
7. **哪些测试验证它**：映射到测试分层（Vitest+RTL 组件单测 / Playwright e2e / 类型级 `tsc`），逐行为给测试点（成功 + 全部失败路径）。
8. **哪些内容不得在此补造**：显式列出本单元不拥有的决策（如 `server-component` "不决定本地交互态——属 client-component"）。

**粒度标准（四条）**：可直接实现 / 明确调用关系 / 完整调用链 / 粒度一致。

正例（H5，server-component 链）：✅ `PostPage` 行为 `渲染文章`：① 调 `data-access` 的 `getPostBySlug(slug)`（承接 `BHV-012`）；② 命中 `null` → 调 `notFound()`（承接失败路径 `BHV-013`）；③ 把 `post` 透传给纯展示 `ui-component <Article/>`；④ 导出 `generateMetadata` 写 `title/description`（SEO 标准化）。
反例：❌ `PostPage`：获取数据、渲染页面、处理 SEO（无调用对象、无失败分支、无 owner、把交互态也塞进 server-component）。

### 4.4 实现：trace 计划合同与 mutable evidence（萃取实现类方法须覆盖）

1. **计划**（开工前）：任务切片承接 `UNIT-<slug>` + doc_type/文件范围 + 完成信号 + 验证方式；执行顺序按 §0.4 自底向上。
2. **执行**（随做随记）：实际改动文件清单（相对路径）+ 与计划偏差及原因。
3. **证据**（验证后）：`tsc --noEmit` / ESLint / Vitest / Playwright 命令 + 测试名级结果；`'use client'` 边界扫描结果；未验证项（如 SSR/CSR 真机表现）显式列出 + 留给哪个环节。
4. **阻塞与偏差**：上游缺陷回退对应阶段（不就地改设计）；触碰 SLOT-18 存量违例列编号 + 处置；未决决策升级人工 Gate。

> Gate 红线：详细八问缺项 / 追溯断链 / 私有数据进 client / 样式全局污染 / 缺 `error.tsx` 兜底 → 阻塞。`implement.md` 计划合同证据链不全或 mutable evidence 只写"全部通过" → 不进 commit。

---

## 5. 修订形态判定（与既有 SSOT 冲突时）

- **局部修订**：补一条错误枚举、补测试映射、补一条依赖正反声明、补一个 `'use client'` 边界判定、补一行 frontmatter 字段约定。→ 直接改对应 L1/L2 并在文件头记修订日期。
- **文档级重构**：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档迹象）、`doc_type` 被悄悄改名/越层。→ 升级，禁止并行两套口径。
- **概要缺陷**（归属错、承接索引漏）→ 回退概要阶段修订，禁止在详细/萃取阶段就地改归属。
- **示例 vs 生产混淆**（把 blog 示例的 Pages Router / `strict:false` 当成生产基线写进方法）→ 视为反例，按 §0.6 拆分来源后重写。

---

## 6. 好 / 坏萃取示例（结构脱敏）

- ✅ **好萃取**（沉淀为新方法 `rsc-boundary-partitioning`）：适用场景=任意"含交互的列表/详情页拆分"；正向动作=先在 `server-component` 完成数据获取与渲染编排 → 仅把需要事件/状态的最小子树下沉为 `client-component` → 纯展示抽 `ui-component`；可验证信号=`'use client'` 仅出现在交互子树、server-only import 不进 client bundle（构建期扫描）+ `tsc` 通过；来源=【App Router 生产级补充】。可复用、规定顺序、有信号、不越层 → 合格。
- ❌ **坏萃取**：把"本次给文章页加了 RSS 链接"当方法沉淀（一次性需求事实，应留任务产物）；或写"Next.js 用 gray-matter 解析 frontmatter 就够了"却不标【blog 示例实证】、并据此推断生产 CMS 方案（示例外推、越界）；或新方法里把 `client-component` 直连 `data-access`（违反 §0.2 交互链）。三者均不合格。
