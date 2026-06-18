# Guru H5/Next.js 详细设计 — 单一来源规范（L1 SSOT）

> 跨类型唯一权威。L2 类型文件只承载类型差异，不得与本文冲突；writing/review skill 只做编排与判定。
> 上游硬输入：概要设计的归属判定表 + `chapter_target → detail_doc_type` 承接索引 + `technology_decision_handoff[]`。
> 层级契约：本文（L1）承载规则正文与完成条件；writing/review skill 的 `references/` 只承载编排细则、模板与示例；冲突时 **L1 > L2 > references > SKILL.md**。
> 装载路径：本文件部署后由 harness 以 `.trellis/spec/harness/detail/detail-structure-single-source.md` 装载；通用 golden-path 由 `.trellis/spec/guides/golden-path.md` 装载。
> 平台基线：Next.js（**App Router 生产形态为目标**）+ React + TypeScript(strict)。`doc_type` 与分层一律以本文 §1 钉死的 H5 七类为权威，**禁止照抄 flutter（page-entry/controller/usecase/...）或 backend（Entry/Biz/Utility/...）的类型名**。

---

## §0 来源映射说明（H5 七类 ⇐ backend 九类 / flutter 九类）

本文的 `doc_type` 七类是 H5 平台的权威分层，由 backend/flutter 同名 SSOT 的分层语义**重投影**而来，不是改名照搬。下表只用于读者建立心智映射、复核分层归属是否漂移；任何冲突一律以 §1 七类定义为准，不以本映射表为准。

| H5 七类（权威） | backend 九类语义对应 | flutter 九类语义对应 | 重投影理由（为何不照搬名） |
|---|---|---|---|
| `server-component` | `Entry / API Behavior`（渲染编排入口）+ 部分 `Biz / Behavior`（服务端数据获取编排） | `page-entry`（页面结构）+ `controller`（状态容器，部分） | RSC 既是 HTTP 渲染入口又承载服务端数据获取编排，是 Next.js 特有形态，backend/flutter 无对应单一类型 |
| `client-component` | 无直接对应（前端交互层） | `controller`（事件→状态转移、生命周期、三态） | `'use client'` 边界是 Next.js 特有的运行时分割点，交互/状态/hooks 只能在此层 |
| `data-access` | `Data / Canonical` + `Utility / Technical Capability`（数据访问技术能力） | `repository-datasource` + `api-network` + `db-dao` | H5 数据源形态多样（MDX/CMS/ORM/fetch），合并为单一数据访问层，对齐 flutter repository/datasource 编排 |
| `route` | `Entry / API Behavior`（路由段/SEO） | `page-entry`（路由注册、Binding） | App Router 的 `page/layout/loading/error.tsx + metadata` 是文件系统路由段约定，独立成类 |
| `ui-component` | 无（纯展示无业务） | `service`（无状态，部分）/ widget 级 | 纯展示型可复用组件无数据获取无业务，对齐 backend Utility 的"业务无关"内核但限定为 UI 渲染 |
| `domain-type` | `Data / Canonical`（实体/字段语义）+ `External / Integration Contract`（结构化合同） | `service`（跨域转换 model）/ data model | TS 类型/zod schema/领域模型是 H5 的合同 owner 锚点，对齐 backend `entity_model_items`/`structured_contract` |
| `server-action` | `Entry / API Behavior`（变更端点）+ `Biz / Behavior`（变更业务） | `usecase`（有状态业务流程、业务 API） | Server Actions / route handlers 是 Next.js 服务端变更/API 形态，对齐 flutter usecase 的业务 owner |

映射纪律（强制）：

- 本表只做语义对照，**不引入 backend/flutter 的字段名、类型枚举、编号规则**到 H5 正文。
- 读概要承接索引时，若发现某 `chapter_target` 的归属用了 backend/flutter 类型名，按归属漂移处理 → 回退概要修订（§9），不在详细阶段就地翻译。
- 一个语义对象只能落到一个 H5 七类；跨类共享语义（如 `domain-type` 被多层引用）由各层 import 该类型，而非复制定义。

---

## §1 H5 详细设计 doc_type — 权威七类（全程唯一，禁止改名/增减/换数）

下列七类是 H5 详细设计的**唯一合法 `doc_type` 枚举**。索引项、章节文件头、下游 trace 一律只用这七个 token，不得新增第八类、不得合并、不得改名、不得用 backend/flutter 名替代。

| # | doc_type | 覆盖对象 | owner 内核（一句话） | L2 状态 |
|---|----------|---------|---------------------|---------|
| 1 | `server-component` | RSC 服务端组件：渲染 + 数据获取编排（默认形态） | 服务端渲染入口，编排 `data-access` 取数后产出 RSC 树；私有数据/secret 可在此读取 | **v1 提供** |
| 2 | `client-component` | `'use client'` 交互组件：状态/事件/hooks | 浏览器侧交互 owner；持有 `useState/useEffect`、事件处理、表单状态 | **v1 提供** |
| 3 | `data-access` | 数据访问层：fetch 封装 / 内容源（MDX/CMS）/ ORM 查询 | 数据访问合同 owner；封装取数、缓存策略、错误转换；私有数据获取只在此与 server-component/server-action | **v1 提供** |
| 4 | `route` | App Router route 段：`page/layout/loading/error.tsx` + metadata/SEO | 文件系统路由段 owner；段约定、错误边界、`generateMetadata` SEO | pending |
| 5 | `ui-component` | 展示型可复用组件：纯展示、无数据获取、无业务 | 纯展示 owner；props 进、JSX 出；无 fetch、无业务分支、无私有状态机 | pending |
| 6 | `domain-type` | TS 类型 / zod schema / 领域模型 | 合同/类型 owner；字段语义、取值约束、运行期校验 schema | pending |
| 7 | `server-action` | Server Actions / route handlers：变更 / API endpoint | 服务端变更 owner；表单提交、写操作、revalidate、API endpoint | pending |

**v1 L2 文件**（render/interactive/data 三元组，对应 flutter controller/usecase/repository-datasource）：

- `.trellis/spec/harness/detail/detail-type-server-component.md`（render 轨：渲染编排）
- `.trellis/spec/harness/detail/detail-type-client-component.md`（interactive 轨：交互状态）
- `.trellis/spec/harness/detail/detail-type-data-access.md`（data 轨：数据访问）

**pending L2**：`route` / `ui-component` / `domain-type` / `server-action` 暂无独立 L2，按本文 §3 合同八问展开，并在章节文件头标注 `l2_status: pending`；full 链命中 pending 类型时另须满足 §2 的 **L2 豁免合同**。

---

## §2 owner 层、分层依赖律与承载形态

### 2.1 分层依赖律（归属硬基准，违反 fail）

H5 依赖方向必须单向无环，分两条链：

- **服务端链**：`route → server-component → data-access → domain-type`
- **交互链**：`client-component → ui-component`
- **变更链**：`server-action → data-access`

补充规则（强制）：

- `domain-type` 是叶子合同，被服务端链与变更链共同引用，但**不反向依赖任何运行层**。
- `client-component` 可消费 `domain-type`（仅类型导入，不引入服务端取数），可被 `server-component` 作为子树嵌入，但 `server-component` 不得 import `client-component` 的内部状态、`client-component` 不得直接 import `data-access`/`server-action` 的私有取数实现（只能通过 props 接收数据或调用暴露的 action 引用）。
- `ui-component` 是纯展示叶子，被 `client-component` 与 `server-component` 共用，**不得反向依赖任何上层**。
- 出现 `data-access → server-component`、`ui-component → client-component`、`domain-type → 任意运行层` 等反向边 → 归属漂移 → fail，回退概要修订。

### 2.2 硬规则（golden-path 锁定）

| 规则 | 内容 | 违反判级 |
|---|---|---|
| TS strict | `tsconfig.json` 必须 `"strict": true`；详细设计接口/类型签名按 strict 假设书写（不得依赖隐式 any） | P1 |
| server-first | 默认 `server-component`；`'use client'` 最小化，仅在确需交互（事件/状态/hooks/浏览器 API）处声明 | P1 |
| 私有数据 / secret 边界 | 私有数据获取、API key、token、私钥**只能**出现在 `server-component`/`data-access`/`server-action`；`client-component`/`ui-component` 禁直取，只能接收脱敏后的 props 或调用 action | P1 |
| route 段约定 | `route` 类必须明确 `page/layout/loading/error.tsx` 的职责切分与触发条件 | P1 |
| metadata / SEO | `route` 必须标准化 `metadata` 或 `generateMetadata`（title/description/og）；动态路由声明 `generateStaticParams` 策略 | P2 |
| 样式隔离 | CSS Modules 或 Tailwind；**禁全局污染**（禁止裸全局 class 选择器、禁止跨组件样式泄漏） | P2 |
| 错误边界 | 渲染失败路径必须落到 `route` 的 `error.tsx`（client error boundary）或 `data-access` 的错误转换点；不得静默吞错 | P1 |

> 注意：`strict: true` 是 H5 golden-path **生产级补充**——blog 示例 `tsconfig.json` 实证为 `strict: false`、`target: es5`（见 §10 证据）。详细设计一律按生产基线 `strict: true` 书写，不沿用示例的宽松配置。

### 2.3 写作顺序（自底向上，与 §5.2 chapter_loop 对齐）

```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```

合同/类型先固化 → 数据访问与变更合同展开 → 服务端渲染编排 → 交互层 → 展示叶子 → 路由段收口。同一 feature 的 `server-component` 及其直接 `data-access`、相关 `domain-type` 视为同一小批次优先完成。

### 2.4 承载形态按链型分轨

- **full 链（目录级设计包）**：每个 `chapter_target` 独立一个 `design_package/chapters/<slug>.md`（文件名与概要承接索引一致，gate 双向闭合）。执行采用 **directory_precheck + chapter_loop**（合同见 §5）：先确认 design-main.md 承接索引存在且非空（缺失/为空 → 回退概要，禁止详细补造），再逐章或小批次生成正文——**禁止一次性全量输出全部章节**（全量输出必然退化为大纲级薄文档）。
- **light 链（单文件）**：合并为任务内 `design.md` §2 单文档多章节，每章仍须独立满足对应合同。

### 2.5 pending L2 拦截 + L2 豁免合同（full 链）

承接索引命中 L2 状态为 pending 的 doc_type（`route`/`ui-component`/`domain-type`/`server-action`）时，必须在 design-main.md 显式声明：

```
L2豁免：<doc_type> 理由：按 L1 §3 合同八问展开；风险：<具体风险>；补齐计划：<何时补 L2>
```

否则 gate 拦截。首选做法是先补齐对应 L2 再进详细设计。

---

## §3 合同八问（所有 doc_type 通用骨架）

**编号纪律（强制）**：

- 行为编号 `BHV-NNN`：每条承接行为唯一三位编号，必须存在于 prd（幽灵引用与无承接行为均被 gate 断链拦截）。
- 设计单元编号 `UNIT-<slug>`：每个设计单元以 `### UNIT-<slug>` 标题定义（语义 kebab-case，如 `UNIT-post-list-renderer`）。
- 下游引用一律写**裸 token**（`BHV-012`、`UNIT-post-list-renderer`），不得写"见上文那个行为"等模糊引用。

每个设计单元必须回答以下八问，缺一不可（括号内为可验证信号——审核按此取证）：

1. **承接哪些行为**：逐条引用 `BHV-NNN`（必须存在于 prd；幽灵引用 / 无承接行为均被 §3.2 编号断链拦截）。
2. **输入 / 输出 / 错误结果**：props/参数类型与取值域、返回/渲染产物、错误枚举（输入表 + 输出表 + 错误类型表，见 §4）。RSC 还须写"数据获取入参（如 `params`/`searchParams`）→ 取数 → 渲染产物"链。
3. **读取 / 写入哪些状态**：`client-component` 写 `useState/useReducer/store` 字段；`server-action` 写 `data-access`/DB；`server-component` 默认无客户端状态（写 `N/A：server_no_client_state`）。写 owner 必须与概要归属一致（回指归属表行）。
4. **调用哪些依赖，不调用哪些依赖**：正反两面都写（防越层）。依赖必须出现在概要架构图/归属表中，且方向符合 §2.1 依赖律。反面例：`ui-component` 明确写"不调用 `data-access`——属 server-component/server-action"。
5. **失败如何收口**：每条失败路径的处置（重试/降级/上抛到 `error.tsx`/用户提示）；错误转换位置遵循 `[SLOT-04]`（异常表逐行可对应一条失败路径 BHV 或八问 1 的行为分支）。
6. **产生哪些事件 / 后置结果**：客户端事件回调、`revalidatePath/revalidateTag`、`redirect`、cache 失效、埋点（逐条写明消费方）。
7. **哪些测试验证它**：映射到测试分层（unit / component(RTL) / e2e(Playwright) / manual），逐行为给测试点（成功 + 全部失败路径）。
8. **哪些内容不得在此补造**：显式列出本单元不拥有的决策（如 `ui-component`："不决定取数策略——属 data-access；不决定缓存——属 data-access/server-action"）。

### 3.1 粒度标准（四条，写作与审核共用）

1. **可直接实现**：每个行为步骤具体到开发者可直接编码，不需再分解业务逻辑或补充判定。
2. **明确调用关系**：每步指明调用的具体行为——下层组件行为名与参数、本单元内部行为、外部依赖（fetch/ORM/SDK）的具体调用。
3. **完整调用链**：从入口行为出发可追踪到所有下级行为，构成完整调用关系（与概要时序图一致）。
4. **粒度一致**：同一文档内所有行为描述粒度一致。

**正例**（合格粒度——`server-action` 的 `submitComment` 行为执行流程）：

1. 调用本单元 `parseFormData(formData)`（zod schema `CommentInput` 校验，对应 `domain-type` 的 `UNIT-comment-input-schema`）；失败 → 返回 `{ ok:false, error:'INVALID_INPUT' }`，流程终止。
2. 调用 `CommentRepository.insert(input)`（owner：`data-access` 的 `UNIT-comment-repository`）。
3. 成功 → 调用 `revalidatePath('/posts/[slug]')`（后置结果：列表页缓存失效，消费方 `server-component` 的 `UNIT-post-detail`）。
4. `RepositoryError.conflict` → 返回 `{ ok:false, error:'DUPLICATE' }`；`RepositoryError.network` → 上抛交 `route` 的 `error.tsx`。

**反例**（不合格——`submitComment`）：校验输入，写数据库，刷新缓存，返回结果。（无调用对象、无失败分支、无 owner、无后置消费方）

### 3.2 编号断链拦截（强制 gate 规则）

详细阶段对 `BHV-NNN` 与 `UNIT-<slug>` 两类编号执行双向闭合检查，任一断链按 P1 阻塞：

- **幽灵 BHV**：单元八问 1 引用的 `BHV-NNN` 在 prd 中不存在 → 断链 fail。
- **悬空行为**：prd 已声明、概要已归属到某 `chapter_target` 的 `BHV-NNN` 在任何单元中均无承接 → 断链 fail（覆盖率缺口）。
- **幽灵 UNIT**：测试映射（八问 7）/跨章引用使用的 `UNIT-<slug>` 在任何章节均无定义 → 断链 fail。
- **重号**：同一 `BHV-NNN` 被多个互斥 owner 单元声明为主承接，或同一 `UNIT-<slug>` 在不同章节重复定义 → 断链 fail。
- **方向违例编号**：依赖（八问 4）引用的下游 `UNIT-<slug>` 其 doc_type 违反 §2.1 依赖律（如 `ui-component` 引用了 `data-access` 单元）→ 断链 fail。
- 编号断链一律回到对应单元修订或回退概要补归属（§9），**不得在详细阶段就地新造编号绕过**。

---

## §4 章节正文骨架合同（chapters/<slug>.md 模板）

full 链每个章节文件按以下骨架撰写（light 链 design.md §2 的每章同构，可压缩小节层级）。骨架与合同八问的映射在末表——**模板是表达形式，八问是完成条件**，二者必须同时满足。

````markdown
# <chapter_target> 详细设计

> doc_type：<七类之一> ｜ l2_status：v1 / pending（pending 须有 L2豁免）
> 承接索引：design-main.md 第 7 节 <chapter_target> ｜ 返回：[design-main](../design-main.md)
> 项目约定：route_mode=App ｜ 内容源=<MDX/CMS> ｜ 状态=<none/Zustand/Context> ｜ 样式=<Tailwind/CSS Modules>（见 §6 槽位）

## 1. 单元职责
本章承载的 UNIT 清单与一句话职责；与依赖/被依赖单元的关系（调用谁的什么行为、被谁调用），方向须符合 §2.1 依赖律。

## 2. 行为定义
### 2.1 行为清单（每行为一行：行为名 + 简述 + 承接的 BHV 编号）
### 2.2 接口定义（TypeScript 签名级，禁止超过签名级的实现代码）
```ts
// server-component / route：渲染函数签名 + props 类型
export default async function PostDetailPage(
  props: { params: { slug: string } }
): Promise<JSX.Element>;

// client-component：props 类型 + 暴露的回调签名
export function CommentForm(props: { postId: string; onSubmitted?: () => void }): JSX.Element;

// data-access：取数合同签名
export function getPostBySlug(slug: string): Promise<Post | null>;

// server-action：action 签名（'use server'）
export async function submitComment(formData: FormData): Promise<ActionResult>;
```

## 3. 核心数据结构
### 3.1 数据模型 / Schema（TS type/interface/zod schema 签名级；序列化与校验方案按 §6 槽位）
### 3.2 错误类型表
| 错误名 | 错误码/枚举 | 语义 | 上抛/收口位置（error.tsx / data-access 转换点 / action 返回） |

## 4. 逐行为设计（每个行为一小节）
### 4.x <行为名>
- 函数签名（TypeScript）
- 行为简述（一句话 + 承接 BHV 编号）
- 输入参数表：| 参数 | 类型 | 取值域/约束 | 必填 |（RSC 含 `params`/`searchParams`；client 含 props/event）
- 输出表：| 返回值/渲染产物/发射值 | 类型 | 语义 |
- 执行流程（mermaid sequenceDiagram，参与者用真实组件名，步骤编号）
- 流程详述（编号列表，与图中编号一一对应，满足 §3.1 粒度标准）
- 异常处理表：| 异常情况 | 处置（重试/降级/上抛 error.tsx/提示） | 错误转换位置 |

## 5. 状态 / 边界管理
- client-component：状态字段定义（含初始态）+ 状态转移（mermaid stateDiagram 或转移表）+ 写 owner 声明；三态（loading/success/error）显式。
- server-component / route：写 `N/A：server_no_client_state`，并声明数据获取边界（缓存/重验证策略引用）。
- 'use client' 边界声明：本单元是否含 `'use client'`、为何在此分割、哪些子树留在服务端。

## 6. 路由 / 渲染 / SEO（route 类必含；其余类写 N/A）
段约定（page/layout/loading/error.tsx 职责）、metadata/generateMetadata（title/description/og）、generateStaticParams/动态段策略、缓存与重验证（force-static / revalidate / dynamic）。

## 7. 测试映射
| BHV/行为 | 测试层（unit/component-RTL/e2e-Playwright/manual） | 测试点（成功+失败路径逐条） |

## 8. 不得补造清单
本单元不拥有的决策逐条列出（含 §2.1 依赖律禁止越层的反面项）。
````

**骨架 ↔ 八问映射**：

| 模板节 | 满足八问 |
|--------|---------|
| 1 单元职责 | 八问 4（依赖正反面的"谁"） |
| 2 行为定义 | 八问 1（BHV 承接）+ 2（签名） |
| 3 核心数据结构 | 八问 2（类型/错误枚举） |
| 4 逐行为设计 | 八问 2/4/5/6（流程、依赖调用、失败收口、事件） |
| 5 状态/边界管理 | 八问 3（读写状态与 owner） |
| 6 路由/渲染/SEO | 八问 6（后置结果：revalidate/redirect）+ §2.2 metadata 规则 |
| 7 测试映射 | 八问 7 |
| 8 不得补造清单 | 八问 8 |

辅助性文本（描述、表格、图内标签）一律中文；代码语法元素（类名/方法名/参数名/字面量/框架 API）保持英文。

---

## §5 chapter_loop 执行合同（full 链）

### 5.1 directory_precheck（写作/审核共用前置）

进入任何章节写作前依次确认，任一失败即停止并输出缺口与概要修订动作：

- **P1** 本文件可读；命中类型的 L2 文件可读（v1 仅 `server-component`/`client-component`/`data-access` 有 L2；其余按 §3 合同八问展开并标 `l2_status: pending`，full 链另须满足 §2.5 L2 豁免合同）。
- **P2** 通用 golden-path 可读（`.trellis/spec/guides/golden-path.md`）。
- **P3** 目标仓库 `project-conventions.md` 可读且校验通过（§6 槽位 C1~C5）。
- **P4** 概要主定义可定位（full 链=`design_package/design-main.md`；light 链=`design.md` §1），承接索引存在、可建立完整非空的 `chapter_target → detail_doc_type` 目标集合（七类之内）。**索引缺失/为空 → 回退概要阶段，禁止详细补造归属。**
- **P5** 概要 Gate 已过且当前 digest 下已有两个不同 run-id 的 clean review evidence（`guru_gate.py status` 可查 overview review）；缺 evidence 不得开始详细写作。
- **P6** pending L2 命中项均有 §2.5 `L2豁免` 声明；`technology_decision_handoff[]` 中被本批引用的条目状态为"选定"（未选定 → 回退概要，禁止详细拍板）。

### 5.2 推荐写作顺序（层级，与 §2.3 一致）

1. **合同层**（`domain-type`）——TS 类型/zod schema/领域模型先固化。
2. **数据层**（`data-access`）——按合同层展开取数/缓存/错误转换。
3. **变更层**（`server-action`）——按数据层合同展开写操作/revalidate/API endpoint。
4. **渲染层**（`server-component`）——编排 data-access 取数产出 RSC 树。
5. **交互层**（`client-component`）——只做交互/状态到稳定服务端合同的适配。
6. **展示层**（`ui-component`）——纯展示叶子收口。
7. **路由层**（`route`）——段约定、metadata/SEO、错误边界收口。

同一 feature 的 `server-component` 及其直接 `data-access`、相关 `domain-type` 视为同一小批次优先完成。

### 5.3 批次与自动审修闭环

- 每批 **1~3 章**；**禁止一轮生成全部章节**。
- 每批生成后**立即自动 review**（不等用户）：章节模板符合性（§4）、八问完成条件（§3）、粒度（§3.1）、编号断链（§3.2）、依赖与概要归属一致（§2.1）、硬规则（§2.2）、L2 差异规则（命中 v1 类型时）。
- 有 finding → 按 §9 判定修订形态 → 直接修复 → 复查受影响的行为/依赖/跨章引用。
- 当前批所有规则均有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。
- 只有"概要源缺失 / 业务语义必须人工确认 / 技术决策未选定 / 修复无法收敛"时才中断并升级用户。

### 5.4 层级 checkpoint

每完成一个层级（§5.2 的 1~7 按链聚合）执行跨章核对，失效项回到对应批次重走审修闭环：

- **合同层后**：`domain-type` 的每个 schema/type 有唯一 owner；不反向依赖运行层；被引用方 import 路径成立。
- **数据层后**：`server-component`/`server-action` 声明的取数依赖全部有承接 `data-access` 单元；错误转换位置（SLOT-04）一致；缓存/重验证决策只在 `data-access`；私有数据/secret 不外泄（§2.2 边界）。
- **变更层后**：`server-action` 写 owner 唯一；`revalidatePath/Tag` 的消费方闭合；表单/输入校验回指 `domain-type` schema。
- **渲染层后**：`server-component` 只 import `data-access`/`domain-type`/`ui-component`/`client-component`（嵌入）；无 `'use client'` 误标；SEO/metadata 由 `route` 或 `generateMetadata` 收口。
- **交互层后**：`client-component` 只通过 props/action 引用与服务端交互，不直 import `data-access` 私有取数；三态完整。
- **展示层后**：`ui-component` 纯展示，无 fetch/无业务分支；样式隔离（无全局污染）。
- **路由层后**：`route` 段约定齐全（page/layout/loading/error.tsx）、metadata 标准化、错误边界落地、与概要页面流图/时序图一致。

### 5.5 完成判定输入

目录级完成 = 全部 `chapter_target` 的 `chapter_status=passed_by_method_evidence` + 七个层级 checkpoint 通过 + gate 章节闭合（索引↔文件双向）通过。

---

## §6 项目约定槽位（project-conventions）

`project-conventions.md` 必须显式填写以下槽位；directory_precheck P3 校验 C1~C5（缺一即前置失败）。详细设计中命名/序列化/取值不得偏离槽位。

| 槽位 | 候选值 | 校验项 | 备注 |
|---|---|---|---|
| 路由模式 | `App` / `Pages` | **C1** 必须明确；golden-path 目标=`App` | blog 示例实证为 `Pages`（§10），生产基线选 `App` |
| 内容源 | `MDX` / `CMS` / `ORM-DB` | C2 与 `data-access` 取数形态一致 | blog 示例实证为 `MDX + gray-matter`（§10） |
| 状态管理 | `none` / `Zustand` / `Context` | C3 `client-component` 状态字段 owner 与此一致 | server-first 下多数页面 `none` |
| UI 组件库 | `shadcn` / `MUI` / 自建 | C4 `ui-component` 引用库与此一致 | — |
| 样式方案 | `Tailwind` / `CSS Modules` | C5 与 §2.2 样式隔离规则一致 | 禁全局污染 |
| 测试 | `Vitest+RTL` / `Playwright` | 八问 7 测试分层映射来源 | unit/component=Vitest+RTL；e2e=Playwright |
| lint | `ESLint + Prettier` | 接口/类型签名书写风格基线 | — |
| 数据库 | `Postgres+Prisma` / `none` | `data-access`/`server-action` 写 owner 形态 | 无 DB 时内容源为 MDX/CMS |
| 认证 | `NextAuth` / `none` | secret 边界（§2.2）owner 声明 | session 只在服务端读取 |
| 图像优化 | `next/image` / 原生 | `ui-component`/`server-component` 图像形态 | — |
| 部署 | `Vercel` / 自托管 | `route` 缓存/重验证策略前提 | — |

---

## §7 实现 trace（四节，进入编码前落盘）

详细设计交付前须为每个 `chapter_target` 落实现 trace 四节，作为编码与回归基线：

1. **承接 trace**：`BHV-NNN ↔ UNIT-<slug> ↔ chapter_target ↔ doc_type` 的四元闭合表（无幽灵、无悬空，§3.2）。
2. **依赖 trace**：每个 `UNIT-<slug>` 的下游依赖（doc_type + 单元）与方向校验（符合 §2.1 服务端链/交互链/变更链）。
3. **边界 trace**：私有数据/secret/session 的 owner 落点（只在 `server-component`/`data-access`/`server-action`），逐项可定位；`'use client'` 分割点逐处可定位。
4. **测试 trace**：每条 `BHV-NNN` 的测试层（unit/component/e2e/manual）+ 成功路径 + 全部失败路径覆盖记录。

---

## §8 完成判定与 Gate（G1~Gn）

详细设计可进入编码，当且仅当（G1~G5 两轨共用；G6~G8 仅 full 链强制）：

- **G1** 承接索引的每个条目都有对应详细设计单元，无遗漏（覆盖率闭合）。
- **G2** 每个单元的合同八问完整；字段/接口/状态可追溯到概要 owner；满足 §3.1 粒度标准。
- **G3** 每条行为有测试映射（八问 7），覆盖成功路径 + 全部失败路径。
- **G4** 涉及私有数据/secret/session/三方域名/PII 的单元附边界依据（§2.2），且 secret 只在 `server-component`/`data-access`/`server-action`；无私有 API key 明文、无动态执行类设计、无制裁 TLD。
- **G5** 八问之 8（不得补造清单）逐单元存在，含 §2.1 越层反面项。
- **G6** 章节闭合：索引 ↔ chapters/ 文件双向闭合；每章符合 §4 骨架合同；pending L2 命中项豁免齐全（§2.5）。
- **G7** chapter_loop 证据：逐章 `chapter_status=passed_by_method_evidence`，七个层级 checkpoint 全过，无"一轮全量生成"迹象（多章雷同骨架、无单元级实质内容）。
- **G8** 编号断链全清：`BHV-NNN`/`UNIT-<slug>` 双向闭合，无幽灵/悬空/重号/方向违例（§3.2）；doc_type 全程只用 §1 七类 token。

### 8.1 审核基线

- 先证据后结论；finding 带文档/章节锚点。
- 严重度：**P1**（违反 §2.2 硬规则、违反 §2.1 依赖律、八问缺项、编号断链、边界泄漏、章节闭合失败——阻塞）；**P2**（合同不完整但可局部补，如错误枚举不全、metadata 缺项、粒度局部不达标）；**P3**（表述建议）。
- 互斥分支：前置失败 → 只输出前置缺口；前置通过 → findings + 概况 + 三选一结论（可进入编码 / 带假设可进入 / 不可进入）。
- 详细设计文档无存量豁免（新文档全量合规）；存量豁免仅适用于实现阶段代码。

---

## §9 禁止补造清单与修订形态判定（详细阶段红线）

### 9.1 禁止补造清单

- 不得新增概要归属表之外的结构（发现缺口 → 回退概要补归属，再回详细）。
- 不得变更概要已定的 owner、技术决策、scope。
- 不得把 `technology_decision_handoff[]` 中"未选定"的决策在详细阶段私自拍板。
- 不得写实现代码/伪代码超过签名级（方法签名、数据结构/zod schema 定义为上限）。
- 不得把私有数据获取/secret 下沉到 `client-component`/`ui-component`（§2.2 边界红线）。
- 不得引入违反 §2.1 依赖律的反向边或越层调用。
- 不得用 backend/flutter 类型名替代 §1 七类（doc_type 漂移红线）。
- 命名、目录、序列化、样式等取值不得偏离 §6 project-conventions 槽位。

### 9.2 修订形态判定

- **局部修订**：补错误枚举、补测试映射、补一条依赖声明、补一张时序图、补 metadata 项、补一条 `'use client'` 边界说明。
- **文档级重构**：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档迹象）、doc_type 系统性误用、依赖方向系统性违例。
- 发现概要缺陷（归属错、索引漏、技术决策未选定）→ 回退概要修订，禁止在详细阶段就地改归属。

---

## §10 next.js blog 示例实证 vs App Router 生产级补充

参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是 **Pages Router + Nextra + MDX + gray-matter** 的轻量 blog starter（故意简化）。golden-path 以 **App Router 生产最佳实践**为准，把该示例作为**内容模型基线**。下表逐项区分"示例实证"与"生产级补充"，写作时**不得把示例的简化形态当成生产合同**。

| 维度 | blog 示例实证（来源文件） | App Router 生产级补充（golden-path 锁定） |
|---|---|---|
| 路由模式 | Pages Router：`pages/_app.tsx`、`pages/index.mdx`、`pages/posts/*.md`（`pages/` 目录实证） | App Router：`app/` 目录 + `route` 类的 `page/layout/loading/error.tsx` 段约定（§1 #4、§2.2） |
| TS 严格度 | `tsconfig.json`：`"strict": false`、`"target": "es5"`、`"allowJs": true`（实证） | `"strict": true`（§2.2 硬规则）；详细设计接口按 strict 假设书写 |
| 数据获取 | 构建期文件读取：`scripts/gen-rss.js` 用 `gray-matter` 读 `pages/posts/*.md` frontmatter（实证） | `data-access` 类封装取数 + 缓存/重验证（`fetch` cache / `revalidateTag`）+ 错误转换点（§1 #3、§5.4 数据层） |
| 内容源 | MDX + Nextra 主题（`package.json`：`nextra`/`nextra-theme-blog`/`gray-matter`/`rss` 依赖实证） | 内容源作为 §6 槽位（MDX/CMS/ORM-DB）；`data-access` 按槽位形态展开，不绑定 Nextra |
| RSC / 'use client' | 无：Pages Router 全量是客户端 React 组件（`_app.tsx` 实证，无 RSC 概念） | server-first：默认 `server-component`，`'use client'` 最小化仅交互处（§2.2、§1 #1/#2） |
| 元数据 / SEO | `pages/_app.tsx` 内手写 `<Head>`（RSS link/font preload 实证）；frontmatter `title/date/description`（`pages/posts/pages.md` 实证） | `route` 类 `metadata`/`generateMetadata` 标准化 + `generateStaticParams`（§1 #4、§2.2 metadata 规则、§4 模板 §6 节） |
| 样式 | 全局：`_app.tsx` import `nextra-theme-blog/style.css` + `styles/main.css`；`theme.config.js` 用 `<style jsx>`（实证，全局形态） | CSS Modules / Tailwind，样式隔离禁全局污染（§2.2、§6 槽位） |
| 变更 / 写操作 | 无：纯静态内容站（示例无表单/无 mutation） | `server-action`（`'use server'`）/ route handlers 承载变更 + `revalidatePath`（§1 #7、§5.2 变更层） |
| 类型 / 校验 | 仅 `@types/*` + `AppProps`（`_app.tsx` 实证）；无运行期 schema 校验 | `domain-type` 用 zod schema 做运行期校验 + 类型推导（§1 #6、§3.1 正例 `CommentInput`） |
| 测试 | 示例无测试目录（实证缺失） | Vitest+RTL（unit/component）+ Playwright（e2e）（§6 槽位、八问 7） |

写作纪律：凡引用示例只为佐证"内容模型/frontmatter 形态/MDX 取数"等内容层基线；凡涉及路由段、RSC 边界、严格类型、缓存重验证、SEO 标准化、变更与测试，**一律按 App Router 生产级补充列书写**，并在文档中标注证据来源（示例实证 / 生产补充），不混用。

---

> 本文为 H5/Next.js 详细设计 L1 SSOT。writing/review 必须先读取本文件，再执行写作或审核动作；任何与本文冲突的 L2/references/SKILL.md 表述以本文为准（L1 > L2 > references > SKILL.md）。
