# 示例：chapters/post-index-renderer.md（server-component 类最小成稿样例）

> **成稿形态示例**（取材一个通用文章索引内容模型，以 App Router 生产形态展开为 server-component 详设）；演示
> `server-component` 类章节的完整形态与粒度，**不是规则来源**。完整模板与逐节要求见 `../chapter-guide.md` §2 / §3.4，
> 类型差异见 L2 `detail-type-server-component.md`，完成条件见 L1 `detail-structure-single-source.md`。
>
> **示例设定**：内容模型为文章 frontmatter（`title/date/description/tag/author`），读取/解析收敛进 `data-access`
> （`getAllPosts`），本 server-component 只消费返回的领域模型。`UNIT-post-index-renderer` 承接 `BHV-001`（服务端渲染
> 文章索引列表，编号仅供演示），依赖 `getAllPosts`（owner：`data-access` 的 `UNIT-posts-data-access`）与领域类型 `Post`
> （owner：`domain-type` 的 `UNIT-post-type`）；展示交给 `ui-component` 的 `UNIT-post-card`。

````markdown
# post-index-renderer 详细设计

> doc_type：server-component ｜ l2_status：v1
> 承接索引：design-main.md 第 7 节 post-index-renderer ｜ 返回：[design-main](../design-main.md)
> 项目约定：route_mode=App ｜ 内容源=MDX ｜ 状态=none ｜ 样式=Tailwind（见 L1 §6 槽位 C1~C5）

## 1. 单元职责
`UNIT-post-index-renderer`：App Router 下文章索引页的服务端渲染编排（RSC），负责"经 `data-access` 取回全部文章 →
按发布日期倒序组装 → 把可序列化的文章数据传给展示组件"。
- 上承：`route` 的 `UNIT-posts-route`（`app/posts/page.tsx` 段约定，本组件作为其默认导出渲染编排）。
- 下调：`data-access` 的 `UNIT-posts-data-access`（`getAllPosts`）；`domain-type` 的 `UNIT-post-type`（`Post`，仅类型导入）。
- 向下传：`ui-component` 的 `UNIT-post-card`（纯展示，server→server 子树）。
- 不交互、不持客户端状态；方向符合 L1 §2.1 服务端链 `route → server-component → data-access → domain-type`。

## 2. 行为定义
### 2.1 行为清单
- renderPostIndex — 服务端渲染文章索引列表（BHV-001）｜详见 §4.1

### 2.2 接口定义（签名级）
```ts
import type { Post } from "@/domain/post"; // domain-type（仅类型导入）

// server-component：async RSC，无 'use client'；返回 RSC 树
export default async function PostIndexPage(): Promise<JSX.Element>;
```

## 3. 核心数据结构
### 3.1 数据模型 / Schema
本组件**不新造**类型，消费 `domain-type` 的 `Post`（owner：`UNIT-post-type`，字段语义来自 frontmatter
`title/date/description/tag/author`）：
```ts
// 来自 domain-type 的 UNIT-post-type（此处仅引用，不在本章定义）
type Post = {
  slug: string;        // 由文件名去扩展名得到（如 name.replace(/\.mdx?/, "")）
  title: string;
  date: string;        // ISO 字符串，跨 server→client 可序列化（不传 Date 实例外的类实例）
  description?: string;
  tag: string;
  author: string;
};
```
### 3.2 错误类型表
| 错误名 | 错误码/枚举 | 语义 | 上抛/收口位置 |
|-------|------------|------|--------------|
| ContentSourceError.read | read | 内容源读取失败（目录不可达/IO 错误） | data-access 转换点（SLOT-04），本组件不吞错、向上抛 |
| ContentSourceError.schema | schema | frontmatter 校验失败（zod parse 失败） | data-access 转换点，向上抛交 error.tsx |
> 错误类型 owner 归 `domain-type`/`data-access`，本组件**不新造错误类型**（八问之 8）。

## 4. 逐行为设计
### 4.1 renderPostIndex
- 函数签名：`export default async function PostIndexPage(): Promise<JSX.Element>`
- 行为简述：承接 BHV-001——经 `data-access` 取回全部文章并按发布日期倒序渲染索引列表（server 侧取数，可读私有内容源）。
- 输入参数表：
  | 参数 | 类型 | 取值域/约束 | 必填 |
  |------|------|-----------|------|
  | （无 route 参数） | — | 索引页无 `params`/`searchParams` | 否 |
- 输出表：
  | 返回值/渲染产物 | 类型 | 语义 |
  |----------------|------|------|
  | RSC 树 | `Promise<JSX.Element>` | `<ul>` 下每篇 `<PostCard post={...} />`，文章按 `date` 倒序 |
  | 传给 PostCard 的 props：`post` | `Post`（可序列化纯对象） | 跨 server→server 子树，无函数/无 secret |
- 执行流程：
  ```mermaid
  sequenceDiagram
      participant R as UNIT-posts-route(page.tsx)
      participant P as UNIT-post-index-renderer
      participant D as UNIT-posts-data-access(getAllPosts)
      participant C as UNIT-post-card
      R->>P: 1. 渲染默认导出 PostIndexPage()
      P->>D: 2. await getAllPosts()
      D-->>P: 3. Post[] / 抛 ContentSourceError
      P->>P: 4. 按 date 倒序排序（纯函数，无副作用）
      P->>C: 5. 逐篇渲染 <PostCard post={post} />
      P-->>R: 6. 返回 RSC 树（HTML/RSC payload，SEO 可索引）
  ```
- 流程详述（与图编号一一对应，满足 L1 §3.1 粒度）：
  1. `route` 段 `app/posts/page.tsx` 将本组件作为默认导出渲染（本组件即该段的 server-component，不算跳层）。
  2. `await getAllPosts()`（owner：`data-access` 的 `UNIT-posts-data-access`，唯一取数入口）；**不在本组件内联 `fs`
     读文件 / 解析 frontmatter**（取数实现已收敛进 data-access，规则 2）。
  3. 取数成功 → 得 `Post[]`；取数失败 → `getAllPosts` 抛 `ContentSourceError`，本组件不 `try/catch`，自然向上冒泡交
     就近 `error.tsx`（owner：`route` 的 `UNIT-posts-route`）。
  4. 对 `Post[]` 按 `date` 倒序排序（纯函数 `sort`，无 I/O、无状态、无副作用）。
  5. 逐篇渲染 `<PostCard post={post} />`（owner：`ui-component` 的 `UNIT-post-card`）；传入的 `post` 为可序列化纯对象，
     无函数、无 secret（即便 PostCard 为 server 子树，仍禁越 secret 边界，规则 5/6）。
  6. 返回 `<ul>` 容器 RSC 树；产物为 SEO 可索引 HTML/RSC payload（无客户端副作用，无 `useEffect`）。
- 异常处理表：
  | 异常情况 | 处置 | 错误转换位置 |
  |---------|------|-------------|
  | 内容源读取失败（read） | 不吞错，向上抛 → 就近 `error.tsx` 渲染兜底 | data-access（SLOT-04） |
  | frontmatter 校验失败（schema） | 向上抛 → `error.tsx`；不渲染半成品 | data-access（zod parse） |
  | 文章列表为空（合法空态） | 渲染空列表占位（非错误），不调 `notFound()` | 本组件（空数组分支） |

## 5. 状态 / 边界管理
- 客户端状态：`N/A：server_no_client_state`（无 `useState`/`useReducer`/`useEffect`/`useRef`/事件/浏览器 API；出现任一即
  类型误判 P1，应拆出 `client-component`）。
- 'use client' 边界声明：本单元**不含** `'use client'`（默认 server-component，server-first）；索引页无交互，整棵子树
  （含 `UNIT-post-card`）留在服务端；如后续需要"标签筛选/分页"等交互，下推为独立 `client-component`，本组件仅透传数据 props。
- 数据获取/缓存边界：缓存与重验证语义（`force-cache` / `next.revalidate` / `dynamic`）**引用** `data-access`/`route` 决策，
  本组件不决定 TTL（八问之 8）。

## 6. 路由 / 渲染 / SEO
`N/A`（本章为 server-component；段约定与 `metadata`/`generateMetadata`/`generateStaticParams` 全集归 `route` 的
`UNIT-posts-route` 合同，本组件只为其取数复用 `getAllPosts`，不在此决定 metadata 字段全集）。

## 7. 测试映射
| BHV/行为 | 测试层 | 测试点（成功 + 失败路径逐条） |
|----------|--------|----------------------------|
| BHV-001 成功路径 | component-RTL（Vitest+RTL） | mock `getAllPosts` 返回 2 篇 → await 渲染后断言渲染出 2 个 PostCard，且按 `date` 倒序 |
| BHV-001 props 边界 | component-RTL | 断言传给 PostCard 的 `post` 为可序列化纯对象、不含函数/secret |
| BHV-001 取数失败 | component-RTL | mock `getAllPosts` 抛 `ContentSourceError.read` → 断言异常向上冒泡（未被吞），交 error 边界 |
| BHV-001 空列表 | component-RTL | mock 返回 `[]` → 断言渲染空占位、不调 `notFound()` |
| BHV-001 SSR 输出 | e2e（Playwright） | 访问 `/posts` → SSR HTML 含全部文章标题（SEO 可见）；内容源故障时 `error.tsx` 兜底 |

## 8. 不得补造清单
- 不决定**交互与客户端状态**（标签筛选/分页交互 → `client-component`）。
- 不决定**取数实现 / 缓存 TTL / 数据源选型**（→ `data-access` 的 `UNIT-posts-data-access`；缓存段配置 → `route`）。
- 不新造**领域类型 / 错误类型 / zod schema**（→ `domain-type` 的 `UNIT-post-type`）。
- 不决定**route 段 metadata/SEO 字段全集与路由语义**（→ `route` 的 `UNIT-posts-route`）。
- 不决定**展示组件视觉/样式系统**（→ `ui-component` 的 `UNIT-post-card` + 样式槽位 Tailwind）。
- 不调用 `server-action`（无变更；提交/写操作 → `server-action`）。
````

要点提示（写作时自查，对应 `../chapter-guide.md` §4 检查单与 L2 判级）：

1. **流程详述必须能直接编码**——本例 §4.1 第 2 步写明"经 `getAllPosts`（唯一取数入口），不内联 `fs` 读文件"，
   而不是"取数据"。无调用对象/无 owner/无失败分支即粒度不达标（L1 §3.1 反例）。
2. **server-first 与边界硬信号**——§5 写 `N/A：server_no_client_state` 且文件无 `'use client'`；出现 `useState`/`useEffect`/
   内联取数/secret 进 props 即 P1（L2 server-component 判级）。
3. **失败路径不吞错**——§4.1 异常表的 read/schema 均"向上抛交 error.tsx"，与错误转换点（SLOT-04）归 `data-access` 一致。
4. **传向子组件的 props 标注序列化与 secret 边界**——§4.1 输出表逐项标"可序列化纯对象、无函数/无 secret"。
5. **测试映射覆盖全部失败路径**——成功 1 行 + 取数失败 + 空列表 + props 边界 + SSR 各 1 行是底线（八问之 7）。
6. **不得补造清单写指向式**——"不决定缓存 TTL（属 data-access/route）"这种可审计写法，而非空泛"不做缓存"。
7. **doc_type / 编号纪律**——文件头 `doc_type: server-component`、`l2_status: v1`；`BHV-001` 须存在于 prd，`UNIT-<slug>`
   语义 kebab-case，下游引用裸 token（L1 §3.2 双向闭合）。

> 其余六类（`domain-type`/`data-access`/`server-action`/`client-component`/`ui-component`/`route`）的成稿要点与签名样式
> 见 `../chapter-guide.md` §3.1~§3.7；本目录只提供 server-component 类的填充样例，避免多份样例漂移。
