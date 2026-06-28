# H5/Next.js 概要设计 — 单一来源规范（L1 SSOT）

> 本文件是 H5（Next.js + React + TypeScript）概要设计阶段的唯一权威规则。writing/review skill 只做编排与判定，不得复写本文规则正文。
> 上游硬输入：需求阶段产物（核心能力清单 P0/P1 + 行为规格）。
> 横向依赖：通用方法 SSOT `.trellis/spec/guides/golden-path.md`（分层依赖律）+ 目标仓库 `project-conventions.md`（H5 项目槽位）。
> 层级契约：本文（L1）承载规则正文与完成条件；writing/review skill 的 `references/` 只承载编排细则、模板与示例；详细设计 L2 文件 `.trellis/spec/harness/detail/detail-type-*.md` 承载逐类合同八问展开。冲突时 L1 > L2 > references > SKILL.md。
> 平台基线：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。**doc_type 与分层一律以本文件钉死的 H5 七类为权威，禁止照抄 flutter（Page/Controller/UseCase/Repository）或 Go（handler/service/repo）的类型名。**

---

## 0. 平台档案与"示例实证 vs 生产级补充"分隔线

### 0.1 H5 平台档案

| 维度 | 取值 | 备注 |
|------|------|------|
| 框架 | Next.js | App Router 生产形态为目标 |
| 视图层 | React 18+ | Server Components 默认，Client Components 最小化 |
| 语言 | TypeScript strict | `strict: true` 为生产硬底线 |
| 渲染策略 | server-first | RSC 默认服务端渲染 + 数据获取编排 |
| 路由模式 | App Router（`app/`） | golden-path 目标；Pages Router（`pages/`）为兼容/迁移形态 |

### 0.2 参考示例的性质声明（实证基线，非生产范本）

参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是一个**故意简化**的轻量 blog starter，技术构成经实证如下：

- **路由模式**：Pages Router（`pages/index.mdx`、`pages/posts/*.md(x)`、`pages/tags/[tag].mdx`、`pages/_app.tsx`、`pages/_document.tsx`），**不是** App Router。
- **内容引擎**：Nextra 2（`nextra` + `nextra-theme-blog`），MDX 直接作为页面文件，frontmatter 由约定渲染。
- **内容元数据**：`gray-matter` 解析 frontmatter（`title/date/description/tag/author`）；见 `scripts/gen-rss.js` 在 build 前用 `matter()` 读取 `pages/posts/*` 生成 `public/feed.xml`。
- **TS 配置实证**：`tsconfig.json` 中 `"strict": false`、`"target": "es5"`、`"jsx": "react-jsx"` ——**此为示例的简化取值，生产级 H5 不得照抄**。
- **动态路由实证**：`pages/tags/[tag].mdx` 用 `useRouter().query` 在客户端取参（Pages Router 写法）。
- **构建实证**：`package.json` scripts `build: "node ./scripts/gen-rss.js && next build"`，RSS 生成在构建期作为 data 旁路。

**分隔线（贯穿全文，每处引用必须标注归属）**：

| 标签 | 含义 | 在本文出现时的写法约束 |
|------|------|------------------------|
| `[示例实证]` | 该结论可在上述 blog 示例文件中直接验证（给出文件锚点） | 必须附 `examples/blog/<file>` 路径或行为锚点 |
| `[生产级补充]` | App Router 生产最佳实践，**示例未覆盖或与示例相反** | 必须显式说明"示例为何不适用/已过时"，不得伪装成示例实证 |

> 硬规则：凡引用 blog 示例做论据，必须挂 `[示例实证]` 并给文件锚点；凡 App Router 生产形态结论，必须挂 `[生产级补充]`。把 `[生产级补充]`（如 `strict: true`、Server Components、`app/` 路由）写成"示例已实证"即为审核 P2。

---

## 1. 装载与硬前置（WX/EX 共用）

执行写作（WX）或审核（EX）前必须依次确认，任一失败即终止并输出前置缺口：

- **P1** 本文件可读（`.trellis/spec/harness/overview/overview-structure-single-source.md`）。
- **P2** 通用 golden-path 可读（`.trellis/spec/guides/golden-path.md`）——分层依赖律是归属判定的基准。
- **P3** 目标仓库 `project-conventions.md` 可读，且通过其内置校验清单 C1~C5（含 §9 H5 项目约定槽位）。
- **P4** 需求产物可定位，且核心能力清单存在 P0/P1 条目。若需求产物缺失：仍可产出概要草稿，但必须记录**显式假设**（依据、影响范围、验证时点），不得宣称"可进入详细设计"。
- **P5** 判轨完成：task.json `guru_chain` 已确定（full/light）；full 链另须确认 `design_package` 路径已声明或将在阶段 0 声明。
- **P6**（H5 专属）路由模式槽位已在 `project-conventions.md` 锁定（App Router / Pages Router）——归属判定中 route 段的文件约定随此槽位切换，未锁定不得展开 route 归属。

---

## 2. 产物合同（按链型分轨）

**轨道判定**：task.json `guru_chain`（`guru_after_create` 创建时默认 `full`）。涉及付费/广告/鉴权/数据采集/SSR 私有数据获取/SEO 关键页等高风险需求走**目录级设计包**（full）；轻量链（`h5-small-iteration-dev` 分流且获用户同意后显式降级）走任务内单文件 `design.md`（light）。`guru_gate.py` 按链型自动切换检查口径。

### 2a. full 链：目录级设计包

- 位置：目标仓库 `docs/design/<feature>/`（版本级需求用 `docs/design/versions/<ver>/`），并写入 task.json `design_package` 字段（相对 repo root）。
- 骨架（概要阶段建立，gate 查存在性）：
  - `README.md` — 仅导航/索引/追踪矩阵入口，不承载事实正文。
  - `design-main.md` — 概要主定义，必含本节「必含章节」全部条目。
  - `chapters/` — 详细设计逐章承载区（文件本体在详细阶段产出）。
- 任务内 `design.md` 退为指针+摘要：链接 `design_package`，不承载主定义。
- 承接索引每条必须落到章节文件：`chapter_target → doc_type → chapters/<slug>.md`；gate 在详细 Gate 检查索引↔文件双向闭合（引用缺文件、孤儿章节均拦截）。

### 2b. light 链：单文件

概要主定义承载于任务内 `design.md` **§1 概要设计**，必含「必含章节」第 1~8 条（第 5 条架构总览可简化：保留一句话架构 + 路由/组件树描述，分层图与时序图策略表不强制；第 9 条自检可简化为 Gate 前自查，不强制成节）。

### 必含章节（两轨共用语义）

1. **设计约束与输入**：承接的需求核心能力（逐条引用 P0/P1 编号）、技术栈约束（含 §0 平台档案与路由模式槽位）、显式假设清单。
2. **行为集合**：行为枚举结果（见 §3）。
3. **归属判定表**：行为/状态 → owner 层（H5 七类）→ 归属理由（见 §4）。**这是概要的核心产物。**
4. **路由与组件树**：App Router 段树（`app/<seg>/page|layout|loading|error.tsx`）、页面间导航、入参出参（`params`/`searchParams`）、metadata/SEO 落点、deep link（仅 UI 需求；非 UI 需求显式标注 N/A）。
5. **架构总览（人审视图）**（full 链必含成节，合同见 §2.5）：一句话架构 + 分层架构图 + 路由/组件树图 + 核心 UC 表 + UC 承接表 + 时序图策略表（六件套）。
6. **技术决策承接清单** `technology_decision_handoff[]`：内容源选型（MDX/CMS）、状态管理选型、UI 库选型、SSR/SSG/ISR 渲染策略、缓存与 `revalidate` 策略、认证方案等架构显著决策（合同见 §2.6）。
7. **详细设计承接索引**：`chapter_target → doc_type` 映射（doc_type 取值见 §7 钉死的 H5 七类）。每个归属判定表中的 owner 必须被至少一个索引条目覆盖；full 链每条另附 `chapters/<slug>.md` 目标文件，并标 `l2_status`。
8. **未决问题**：显式列出，标注风险等级。
9. **架构就绪自检**（full 链必含成节）：对照 §6 G1~Gn 逐项自评（满足/缺口+闭合计划）；存在未闭合 G 项不得送审概要 Gate。

### 2.5 架构总览（人审视图）合同

架构总览是概要的人类可审核入口——评审者不读全文也能从这一节判断"这个设计长什么样、对不对"。full 链六件套缺一不可：

**① 一句话架构**。固定格式（H5 形态）：

> 用户经 `<入口 route 段/path>` 进入，由 `<server-component>` 编排数据获取并调用 `<data-access>`，交互部分下沉到 `<client-component>`（消费 `<ui-component>`），变更经 `<server-action>` 回写，按 `<渲染策略 SSR/SSG/ISR + metadata>` 收口到界面。

**② 分层架构图**（mermaid graph）。要求：

- 用 subgraph 表达分层：`routing`（route）/ `server`（server-component / data-access / server-action / domain-type）/ `client`（client-component / ui-component）/ `external`（CMS/DB/三方）。
- 箭头只表达依赖方向，必须符合 §4 分层依赖律：`route → server-component → data-access → domain-type`（服务端链）；`client-component → ui-component`（交互链）；`server-action → data-access`。**禁止出现 `client-component → data-access` 直取数据的箭头。**
- 图中组件必须与归属判定表 owner 一一对应；图中不得出现归属表之外的组件。

**③ 路由/组件树图**（mermaid graph 或 flowchart，仅 UI 需求）。要求：

- 节点 = route 段（标注 `app/<seg>` 与产物文件 `page/layout/loading/error`），边 = 导航动作（标注触发行为 BHV 编号与入参 `params`/`searchParams` 要点）。
- 标注每个页面的渲染策略（SSR/SSG/ISR）与 metadata 来源。
- 覆盖本需求新增/修改的全部路由路径，含失败/取消路径去向（如 `error.tsx` 边界、`notFound()`）。
- 非 UI 需求（纯 API route handler/server-action）显式标注 N/A 及依据。

**④ 核心 UC 表**。从需求验收场景提炼用户可感知用例：

| 列 | 含义 |
|----|------|
| `uc_id` | UC-<序号>，创建后不复用不重排 |
| `uc_title` | 用户视角一句话（动词开头） |
| `actor_or_trigger` | 用户操作 / 系统事件 / 生命周期（含 SSR 首屏/客户端 hydration） |
| `source_refs` | 需求来源锚点（prd 章节或 BHV 编号） |
| `goal` | 用户可验证的完成态 |
| `priority` | 对应核心能力 P0/P1 |

**⑤ UC 承接表**。逐 UC 回答"谁实现它"：

| 列 | 含义 |
|----|------|
| `uc_id` | 对应④ |
| `route_refs` | 涉及 route 段 / path |
| `bhv_refs` | 承接的 BHV 编号（必须存在于 prd） |
| `owner_refs` | 归属表中的 owner（H5 七类组件名） |
| `index_refs` | §7 承接索引的 chapter_target |

**⑥ 时序图策略表**。逐 UC 声明时序图交付策略：

| 列 | 含义 |
|----|------|
| `uc_id` | 对应④ |
| `strategy` | `独立` / `合并` / `豁免` 三选一 |
| `sequence_section` | 可定位的 sequenceDiagram 所在小节锚点（独立/合并必填） |
| `merged_coverage` | 合并图覆盖的 uc_id 清单（合并时必填） |
| `exemption_reason` | 豁免理由 + 最小行为链（豁免时必填） |

**时序图回填硬约束**：送审概要 Gate 前，非豁免 UC 必须有可定位真实 `sequenceDiagram`（mermaid），覆盖 浏览器/route → server-component → data-access → external（CMS/DB/三方），交互路径另覆盖 client-component → server-action → data-access（按实际链路裁剪），步骤编号与文字详述一一对应。早期写作可用计划锚点占位，占位状态下不得宣称可送审。

### 2.6 技术决策承接清单合同

`technology_decision_handoff[]` 逐条字段，缺一即该条不完整：

| 字段 | 要求 |
|------|------|
| `decision_id` | TD-<序号> |
| `decision_point` | 决策点（如"内容源 MDX vs Headless CMS"、"渲染策略 SSG vs ISR"、"状态管理 none vs Zustand"） |
| `candidates` | 候选清单（≥1；只有一个候选时说明为何无备选） |
| `selected` | 选定项，或显式 `未选定`（未选定项禁止详细/实现阶段私自拍板） |
| `rationale` | 选择理由（回指架构驱动/约束，不得反向倒推） |
| `detail_expansion_targets` | 交给详细设计展开的字段/合同（指向 §7 索引条目） |
| `compliance_basis` | 涉认证/数据采集/三方域名/PII 时必填：最小权限与用途可解释依据；否则写 N/A |

不保存任何 secret value；密钥/凭证/API token 只写引用方式（环境变量名 `process.env.X`、平台注入），出现真实 key 即审核 P1。**私有数据获取/secret 引用只允许出现在 server-component / data-access / server-action 三类的决策项里，出现在 client-component 决策项即审核 P1。**

---

## 3. 行为枚举方法（生成动作）

从需求行为规格出发，按以下顺序枚举行为空间，**禁止从名词/组件出发**：

1. **用户操作**（点击、输入、提交表单、手势、导航跳转、进入/离开 route）。
2. **系统反应**（服务端数据获取、状态变化、客户端 hydration、缓存命中/`revalidate`、副作用、metadata 生成）。
3. **失败路径**（fetch 失败、数据缺失 → `notFound()`、非法输入、认证拒绝、`error.tsx` 边界命中、并发冲突）。
4. **生命周期事件**（首屏 SSR、客户端 hydration、`loading.tsx` 挂起、路由切换、`revalidate` 触发、server-action 重验证）。

每条行为：`Given <前置> When <触发> Then <后置 + 状态变化>`，并标注涉及的状态与数据、以及**执行边（server / client）**。

### 3.1 粒度标准（四条，写作与审核共用）

1. **可直接实现**：行为描述具体到详细设计可直接展开为合同，不需要再分解业务语义。
2. **明确触发与归属**：每条行为能指出触发者（用户/系统/生命周期）、执行边（server/client）与候选 owner（H5 七类）。
3. **完整链路**：从入口行为出发能追踪到全部下游行为（含失败路径与边界），无断链。
4. **粒度一致**：同一文档内所有行为描述粒度一致；出现"处理文章页"这类粗粒度行为即不达标。

正反例：

- ✅ `BHV-012 提交评论表单`：Given 文章页已渲染、评论内容已输入 When 用户点击提交 Then [client] 触发 server-action → [server] 校验+写入 data-access → `revalidatePath` 当前文章 → 返回新评论态 → 客户端乐观更新收口。涉及状态：评论列表、提交中态、错误态。
- ❌ `BHV-012 处理评论`：Given 用户要评论 When 操作 Then 评论完成。（无前置细节、无执行边、无失败路径、无状态变化）
- ✅ `BHV-003 渲染文章详情`：Given 路由 `app/posts/[slug]/page.tsx`、`params.slug` 已知 When SSR 首屏 Then [server] server-component 调 data-access 按 slug 取 MDX，命中缓存或 `notFound()`，生成 metadata，输出静态结构。
- ❌ `BHV-003 显示文章`：（无路由锚点、无数据源、无 not-found 路径）

### 3.2 行为 ↔ UC 回指

每条 BHV 必须能回指至少一个核心 UC（§2.5 ④）；UC 承接表（⑤）的 `bhv_refs` 与行为集合做双向核对，出现"行为无 UC 来源"或"UC 无行为承接"均为审核缺口。

### 3.3 编号纪律

每条行为以 `### BHV-NNN <短名>` 标题定义（NNN 数字；创建后不复用、不重排，删除留洞）。归属表、详细设计、测试与实现切片对行为的引用一律写 `BHV-NNN` 裸 token——这是机器追溯依据（`guru_gate.py trace-matrix` 据此生成 行为×需求场景×归属×单元×测试×切片 矩阵，断链被 Gate 拦截）。归属判定表逐行以 BHV 编号开头。设计单元命名 `UNIT-<slug>`（slug 取组件名 kebab-case，如 `UNIT-post-detail-server-component`），下游引用裸 token。

### 3.4 行为 ↔ REQ-UC 承接（需求源回指 + 命名消歧）

full 链存在正式需求包（版本化组织见需求包标准 single-source §15）时，BHV 标题可在短名前以 `[REQ-UC-XXX]`（可多个，多对多）显式承接需求源场景，形如 `### BHV-001 [REQ-UC-005, REQ-UC-007] 提交评论`。`trace-matrix` 解析该承接生成「需求场景（REQ-UC）」列（行展开），版本级 `trace-aggregate` 据此把多 task 聚合进 `traceability.md`。需求包标准 `--require-req-uc`（或 task.json `require_req_uc:true`）可强制 BHV 必须带 REQ-UC；旧 prd（BHV 无 REQ-UC）默认不拦、列空、不断链。

**命名消歧（强制）**：`REQ-UC-XXX` 是**需求源场景**（requirement source use case，主定义在需求包标准 single-source §6），与本文 §2.5/§3.2 的 `UC-<序号>`（概要设计**架构核心用例**，`uc_id`）是**两套独立编号**，不混用同一字段。`source_refs`/`bhv_refs` 仍指 overview 内的 `UC-<序号>` 与 BHV；BHV 标题的 `[REQ-UC-XXX]` 指需求源。§3.2 的 `BHV ↔ UC-<序号>` 人审映射不因本规则改写。

---

## 4. 归属判定方法（核心规则）

### 4.0 owner 层与分层依赖律（归属硬基准）

H5 owner 层就是 §7 钉死的七类。分层依赖律（违反即 review 直接 fail）：

```
服务端链：  route → server-component → data-access → domain-type
交互链：    client-component → ui-component
变更链：    server-action → data-access
横切：      domain-type 被任意层依赖，自身不依赖业务层
```

- `route` 是页面段编排入口，只装配 server-component / 设定 metadata / 边界（`loading`/`error`/`not-found`），不写业务。
- `server-component` 默认服务端执行，编排数据获取与渲染，向下只依赖 data-access 与 domain-type。
- `client-component`（`'use client'`）只承接交互/状态/hooks，向下只依赖 ui-component（与 domain-type 的类型），**禁止直接依赖 data-access**（私有数据获取与 secret 只在 server 边）。
- `server-action` 承接变更（mutation）与 API endpoint，向下依赖 data-access。
- `ui-component` 纯展示、无数据获取、无业务，是依赖图叶子。
- `data-access` 数据访问层（fetch 封装 / MDX 内容源 / CMS / ORM 查询），向下依赖 domain-type。
- `domain-type` 类型/zod schema/领域模型，是横切被依赖项。

### 4.1 行为 → owner 三问归属判定表

对每条行为/每个状态，按分层依赖律判定**唯一 owner**：

| 行为/状态类型 | 归属层（doc_type） | 判定理由模板 |
|--------------|-------------------|-------------|
| route 段装配、metadata/SEO、`params`/`searchParams` 入口、边界文件（layout/loading/error/not-found） | `route` | 页面段编排与 SEO 入口，不拥有业务规则 |
| 服务端数据获取编排、RSC 渲染、按需调用数据源拼装视图 | `server-component` | server-first 渲染 + 数据编排 owner，私有取数收口在此 |
| 交互状态字段、事件处理、hooks、客户端副作用、乐观更新 | `client-component` | `'use client'` 交互 owner，状态容器 |
| 纯展示、可复用、无数据获取无业务的视图片段、design token 消费 | `ui-component` | 只承接展示与输入，依赖图叶子 |
| 数据访问合同、fetch/缓存（`revalidate`/`cache`）策略、内容源（MDX/gray-matter）/CMS/ORM 查询、错误转换 | `data-access` | 数据一致性 owner，server 边唯一取数入口 |
| 领域类型、zod schema、frontmatter 模型、DTO/VO 形状 | `domain-type` | 类型与契约 owner，横切被依赖 |
| 变更（创建/更新/删除）、表单 action、API endpoint、重验证（`revalidatePath`/`revalidateTag`） | `server-action` | 变更与协议边界 owner |

归属判定表每行必须回答**三问**：
1. **为什么属于它？**（该行为的本质职责落在哪一层）
2. **为什么不属于别人？**（排除相邻层，尤其排除把取数/secret 错放 client-component、把业务错放 ui-component、把渲染错放 route）
3. **为什么需要（或不需要）独立存在？**（是否值得独立 UNIT，还是合并入既有 owner）

三问示例（`BHV-012 提交评论表单`）：

> owner = `server-action`（`UNIT-comment-submit-server-action`）。
> ① 属于它：评论提交是变更（mutation）+ 重验证，是 server-action 的本质职责。
> ② 不属于别人：不属于 client-component（client 只触发，不能直接写库/持有 secret）；不属于 data-access（data-access 只提供查询/写入封装，不编排重验证与表单语义）；不属于 server-component（server-component 负责读渲染，不承接变更）。
> ③ 需独立：评论提交被文章页与详情页两处复用、且有自身错误语义，值得独立 UNIT。

硬约束：
- 归属方向不得违反 §4.0 分层依赖律——违反即 review 直接 **fail**（如把 fetch 归给 client-component、把数据获取归给 route、把业务归给 ui-component）。
- 私有数据获取 / secret 只能归 server-component / data-access / server-action 三类；归到 client-component 即 **P1 fail**。
- 一个状态只能有一个写 owner；其他层只能读/订阅（client 态的写 owner 是 client-component；服务端数据的写 owner 是 server-action）。
- 不得在概要阶段发明 Manager/Helper/Util/Provider 等无行为来源的结构（名词先行反模式）。
- `'use client'` 最小化：能落 server-component 的不下沉 client；交互边界尽量小且叶子化。

### 4.2 命名规范（组件与行为）

- **组件名**：定语 + 名词，尽量 ≤2 个英文单词；定语体现领域（Post、Comment、Tag、Auth），名词体现层角色并使用本表既有后缀/形态：route 用段名（`posts/[slug]`）；server-component / client-component / ui-component 用 `<Domain><Role>`（如 `PostDetail`、`CommentForm`、`PostCard`）；data-access 用 `<Domain>Source`/`get<Domain>`；domain-type 用类型名 / `<Domain>Schema`；server-action 用动词（`createComment`、`updatePost`）。禁止 Manager/Helper/Handler 等含混后缀。
- **行为名**：单个动词或动词+宾语，≤2 个英文单词；不重复组件名。
- 取数动词区分语义：`list`（取多个）/ `one`（取单个）/ `get`（取必然存在的）/ `fetch`（取可能不存在的，缺失走 `notFound()`）。
- 项目级取值（目录结构、文件名风格、`app/` 段命名）以 `project-conventions.md` 槽位为准，本节不覆盖。

### 4.3 写作顺序（自底向上，归属落表后据此排章）

```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```

先定类型与契约，再定取数与变更，再定渲染编排，最后收口交互与展示、装配 route。审核检查归属表与承接索引的章节顺序是否与此一致（乱序不强制 fail，但倒序依赖即 §4.0 违例）。

---

## 5. 阶段边界（概要不做什么）

概要只闭合：**边界、语义、链路、取舍、索引**。以下内容禁止在概要展开，发现即属越界：

- 字段级合同、组件 props 签名、zod schema 字段明细、fetch 具体 URL/查询参数、API 路径细节（属详细设计/L2 合同八问）。
- SDK/CMS 客户端初始化参数、`next.config` 取值、环境变量取值、secret value（属详细设计/实现；secret 永不落文档）。
- 代码、伪代码、`.tsx` 文件级实现安排（属实现阶段）。
- 重新决定需求 scope 或私自拍板未决业务规则（回需求阶段）。
- 把 `technology_decision_handoff[]` 中"未选定"的决策（如 MDX vs CMS）直接写成已选定。

---

## 6. 完成判定与 Gate（审核基线）

概要可进入详细设计，当且仅当（G1~G5 两轨共用；G6~Gn 仅 full 链强制）：

- **G1** 行为集合覆盖需求全部 P0/P1 核心能力（逐条可追溯），且每条行为满足 §3.1 粒度标准（含执行边标注）。
- **G2** 归属判定表完整：每条行为有唯一 owner（H5 七类）+ 三问理由；无 §4.0 分层依赖律违例（无 client 直取数据、无 route 写业务、无 ui-component 含业务）。
- **G3** 涉认证/数据采集/三方域名/PII 的行为，已在 `technology_decision_handoff[]` 标注合规依据（最小权限、用途可解释），且 secret 引用仅落 server 边三类。
- **G4** 详细设计承接索引非空，且覆盖归属表全部 owner（full 链逐条落到 `chapters/<slug>.md` 文件名，并标 `l2_status`）。
- **G5** 未决问题中无高风险项（或已获用户确认带假设进入）。
- **G6** 架构总览六件套齐全（§2.5 ①~⑥）：一句话架构、分层架构图、路由/组件树图（或 N/A 依据）、核心 UC 表、UC 承接表、时序图策略表，且图中组件与归属表一致、依赖箭头合 §4.0。
- **G7** 时序图策略闭合：非豁免 UC 均有可定位 sequenceDiagram（覆盖 server 渲染链 + 交互变更链）；合并图列出覆盖清单；豁免项有理由与最小行为链；无占位锚点残留。
- **G8** `technology_decision_handoff[]` 逐条字段完整（§2.6），无"未选定但已被下游引用"的条目；渲染策略（SSR/SSG/ISR）与缓存/`revalidate` 已成决策项。
- **G9**（H5 专属）golden-path 硬规则自检通过（§8 全部锁定项），且 `[示例实证]`/`[生产级补充]` 标签使用正确（无把生产补充伪装成示例实证）。

**严重度判级**：P1（违反 §4.0/§8 硬约束或 Gate 项缺失，阻塞）；P2（归属理由不充分、索引不完整、图表与表格不一致、标签误用，应修）；P3（表述/一致性建议）。

**输出互斥分支**：前置（§1）失败 → 只输出前置缺口与修复动作，不展开逐章审核；前置通过 → 逐条 findings（severity/location/problem/suggestion）+ 结构概况 + "是否可进入详细设计"互斥结论。每条 finding 必须带章节锚点或明确缺失对象（先证据后结论）。**概要文档本身无存量豁免**——新文档必须全量符合本规范。

---

## 7. 详细设计承接索引与 doc_type 七类（权威）

### 7.1 doc_type 权威七类（全程唯一，禁止改名/增减/换数，禁止照抄 flutter/Go 类型名）

| # | doc_type | 角色 | flutter 类比（仅辅助理解，**不得写入产物**） |
|---|----------|------|------------------------------------------------|
| 1 | `server-component` | RSC 服务端组件：渲染 + 数据获取编排（默认形态） | ≈ Controller（render 三元组之一） |
| 2 | `client-component` | `'use client'` 交互组件：状态/事件/hooks | ≈ Controller 的交互面（interactive） |
| 3 | `data-access` | 数据访问层：fetch 封装 / 内容源 MDX/CMS / ORM 查询 | ≈ Repository + DataSource（data） |
| 4 | `route` | App Router route 段：page/layout/loading/error.tsx + metadata/SEO | ≈ Page（路由壳） |
| 5 | `ui-component` | 展示型可复用组件：纯展示、无数据获取、无业务 | ≈ 无状态 Widget |
| 6 | `domain-type` | TS 类型 / zod schema / 领域模型 | ≈ entity/model |
| 7 | `server-action` | Server Actions / route handlers：变更/API endpoint | ≈ UseCase 的变更面 |

> 类比列仅为人理解，**产物（design-main.md / chapters / 索引 / trace 矩阵）中只允许出现左侧七个 doc_type token，禁止写 Page/Controller/UseCase/Repository/handler/service 等。**

### 7.2 承接索引合同

每个归属表 owner 至少被一条索引覆盖。索引条目字段：

| 字段 | 要求 |
|------|------|
| `chapter_target` | 章节/单元标识，对应 `UNIT-<slug>` |
| `doc_type` | §7.1 七类之一 |
| `chapter_file` | full 链：`chapters/<slug>.md`；light 链：本文件内小节锚点 |
| `bhv_refs` | 本单元承接的 BHV 编号（裸 token，逗号分隔） |
| `l2_status` | `full`（已有 L2 模板可遵循）/ `pending`（L2 待补，按 §7.4 合同八问展开）/ `exempt`（豁免，仅 full 链且记理由） |

### 7.3 L2 文件供给与 v1 状态

v1 提供 **render/interactive/data 三元组** L2 文件（对应 flutter 的 controller/usecase/repository-datasource 三元组，但 H5 落到本平台三类），其余四类为 pending：

| doc_type | L2 文件 | `l2_status` v1 |
|----------|---------|----------------|
| `server-component` | `.trellis/spec/harness/detail/detail-type-server-component.md` | `full` |
| `client-component` | `.trellis/spec/harness/detail/detail-type-client-component.md` | `full` |
| `data-access` | `.trellis/spec/harness/detail/detail-type-data-access.md` | `full` |
| `route` | （v1 无 L2） | `pending`（按 §7.4 八问展开） |
| `ui-component` | （v1 无 L2） | `pending`（按 §7.4 八问展开） |
| `domain-type` | （v1 无 L2） | `pending`（按 §7.4 八问展开） |
| `server-action` | （v1 无 L2） | `pending`（按 §7.4 八问展开） |

> full 链送审硬约束：索引中 `l2_status: full` 的条目其 `chapter_file` 必须遵循对应 L2 模板；`l2_status: pending` 的条目必须在 `chapter_file` 内**自带合同八问**（§7.4）作为 L2 豁免补偿——pending 不等于可空，pending 等于"无 L2 模板但八问须就地齐全"。`l2_status: exempt` 仅允许纯类型透传/零行为的占位单元，须记豁免理由与最小行为链。

### 7.4 详细合同八问（pending 类就地展开 / 详细 Gate 检查口径）

每个详细设计单元（无论是否有 L2 模板）必须回答八问：

1. **职责边界**：本单元承接哪些 BHV（裸 token），不承接什么。
2. **执行边**：server 还是 client（`'use client'` 与否），为何在此边。
3. **输入合同**：props / `params` / `searchParams` / action 入参的形状与来源（指向 domain-type）。
4. **产物合同**：渲染输出 / 返回值 / 副作用（`revalidate` 目标）/ metadata。
5. **依赖与调用**：向下依赖哪些 owner（必须合 §4.0），调用顺序。
6. **状态与数据**：读/写哪些状态，写 owner 是谁，缓存策略。
7. **失败与边界**：失败路径去向（`error.tsx` / `notFound()` / 错误态），可验证信号。
8. **测试与 trace**：覆盖 BHV 的测试形态（Vitest+RTL / Playwright）与 trace 锚点。

详细 Gate 据此检查每个 chapter 文件的八问闭合，断链拦截。

---

## 8. golden-path 硬规则（锁定项，G9 自检 + 审核 P1 口径）

| 锁定项 | 规则 | 标签 |
|--------|------|------|
| TS strict | 生产 `tsconfig.json` 必须 `strict: true`（示例为 `false`，不得照抄） | `[生产级补充]`（示例 `tsconfig.json` 实证为 `strict:false`） |
| server-first | 默认 Server Components，`'use client'` 最小化、仅需交互处 | `[生产级补充]`（示例 Pages Router 无 RSC 概念） |
| secret 隔离 | 私有数据获取/secret 只在 server-component/data-access/server-action；client-component 禁直取 | `[生产级补充]` |
| route 段约定 | App Router `page/layout/loading/error(/not-found)` 文件约定齐备 | `[生产级补充]`（示例为 Pages Router `_app`/`_document`） |
| metadata/SEO | 标准化（`generateMetadata`/静态 `metadata`）；示例靠 `_app.tsx` Head 注入与 `gen-rss.js` | `[示例实证]` RSS：`scripts/gen-rss.js`；`[生产级补充]` App Router metadata API |
| 样式隔离 | CSS Modules / Tailwind，禁全局污染 | `[生产级补充]`（示例用 `nextra-theme-blog/style.css` + 全局 `main.css`，属简化） |
| 错误边界 | `error.tsx` 兜底；数据缺失走 `notFound()` | `[生产级补充]` |
| 内容源 | MDX/CMS 经 data-access 封装；示例用 Nextra MDX + `gray-matter` 直读 | `[示例实证]` `pages/posts/*.md(x)` + `gray-matter`；`[生产级补充]` App Router 下经 data-access 封装 |
| 图像优化 | 生产用 `next/image` | `[生产级补充]`（示例 `public/` 静态图，无 `next/image`） |

> 审核时凡 owner 或决策违反上表锁定项即 P1；凡标签归属（实证 vs 补充）写反即 P2。

---

## 9. 修订形态判定

按 findings 修订前必须先判定：

- **局部修订**：补一条行为、补归属三问、补一条索引、补一张图、补 `l2_status`、改措辞、修标签 → 在原文档上改。
- **文档级重构**：归属模型错误（owner 大面积错位/违反 §4.0）、行为枚举从名词倒推、索引与归属表系统性脱节、架构总览与正文两套口径、把 `[生产级补充]` 系统性当 `[示例实证]` → 重做对应章节，禁止用局部补丁掩盖错误模型。

审核发现上游缺陷（需求行为缺失/矛盾）→ 回退需求阶段修订，禁止在概要补造业务规则。

---

## 附录 A：装载路径速查

| 用途 | 路径 |
|------|------|
| 本文件（L1 SSOT） | `.trellis/spec/harness/overview/overview-structure-single-source.md` |
| 通用方法 SSOT | `.trellis/spec/guides/golden-path.md` |
| L2 server-component | `.trellis/spec/harness/detail/detail-type-server-component.md` |
| L2 client-component | `.trellis/spec/harness/detail/detail-type-client-component.md` |
| L2 data-access | `.trellis/spec/harness/detail/detail-type-data-access.md` |
| 项目槽位 | 目标仓库 `project-conventions.md`（含 §9 H5 槽位） |
| full 链设计包 | 目标仓库 `docs/design/<feature>/`（design-main.md + chapters/ + README.md） |

## 附录 B：H5 project-conventions 槽位清单

| 槽位 | 候选 | 默认/golden-path |
|------|------|------------------|
| 内容源 | MDX / Headless CMS | MDX（小站）/ CMS（多编辑者） |
| 状态管理 | none / Zustand / Context | none（server-first 优先） |
| UI 组件库 | shadcn / MUI | shadcn |
| 样式方案 | Tailwind / CSS Modules | Tailwind |
| 测试 | Vitest+RTL（单元/组件）/ Playwright（E2E） | Vitest+RTL + Playwright |
| lint | ESLint + Prettier | 强制 |
| 数据库 | （按需）Postgres/SQLite + ORM | 按需声明 |
| 认证 | NextAuth | 按需声明 |
| 图像优化 | next/image | 强制（生产） |
| 部署 | Vercel | Vercel |
| 路由模式 | App Router / Pages Router | App Router（生产目标） |

> 项目级取值以目标仓库 `project-conventions.md` 为准；本附录为缺省指引，被仓库槽位覆盖。
