# L2 类型规范：client-component（'use client' 交互组件）

> 从属于 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；本文件只写 `client-component` 类型的差异规则，与 L1 冲突时以 L1 为准。
> 装载路径：本文与同级 L2 装载于 `.trellis/spec/harness/detail/*`；通用 golden-path 装载于 `.trellis/spec/guides/golden-path.md`。
> golden-path 对应：server-first / `'use client'` 最小化、交互链 `client-component → ui-component`、私有数据获取禁线、样式隔离、错误边界。
> doc_type 取值严格使用 H5_BRIEF 钉死的七类：`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`。本文件描述的是其中第 2 类 `client-component`，禁止照抄 flutter（controller/usecase/repository）或 Go 的类型名。

---

## 适用对象

`'use client'` 指令标注的 React 交互组件：拥有客户端状态（`useState`/`useReducer`）、绑定 DOM/用户事件（onClick/onChange/onSubmit）、使用浏览器侧 hooks（`useEffect`/`useRef`/`usePathname`/`useRouter`/`useFormStatus` 等），或消费 React Context。

**不适用**（划归其它 doc_type，越界即 owner 错配 P1）：

- 纯展示、无状态、无事件、无 hooks 的可复用组件 → `ui-component`。
- 服务端渲染 + 数据获取编排（默认 RSC，无 `'use client'`）→ `server-component`。
- fetch 封装 / MDX·CMS·ORM 查询 → `data-access`。
- 变更提交 / API endpoint（`'use server'` 函数、route handler）→ `server-action`。
- TS 类型 / zod schema / 领域模型 → `domain-type`。
- `page.tsx`/`layout.tsx`/`loading.tsx`/`error.tsx` 段 + metadata/SEO → `route`。

> 注：`error.tsx` 虽然按 React 约定必须是 Client Component（需 `'use client'` 才能接 `reset()` 与错误边界），但它是 route 段约定文件，owner 归 `route`，不在本类。本类仅承载被 `route`/`server-component` 引用的、独立命名的交互组件。

---

## 示例实证 vs App Router 生产级补充（必读，避免把简化示例当 golden-path）

参考示例 `next.js/examples/blog` 是 **Pages Router + Nextra + MDX + gray-matter** 的轻量 blog starter，对本类的可借鉴度**很低**，必须显式区分：

- **示例实证（可直接引用为内容模型基线）**：
  - 示例**几乎没有真正的 client-component**：唯一的客户端交互是 `pages/tags/[tag].mdx` 内联 `useRouter().query` 读取路由参数（`const { tag } = useRouter().query`）——这是「读路由态并渲染」，连受控状态都没有。
  - 示例**无 `'use client'` 指令**（Pages Router 早于 App Router 的 RSC/指令模型，整页默认在客户端水合，不存在 server/client 边界划分）。
  - 证据文件：`pages/tags/[tag].mdx`、`pages/_app.tsx`、`theme.config.js`（`<style jsx>` 局部样式）、`tsconfig.json`（注意示例 `"strict": false`）。
- **App Router 生产级补充（golden-path 锁定，本文绝大部分规则属此）**：
  - `'use client'` 指令、server/client 边界、`useFormStatus`/`useActionState` 接 server-action、Context Provider 下沉、`tsconfig` 必须 `"strict": true`（示例的 `strict:false` 不可照抄）。
  - 这些在示例中**无实证**，按 App Router 生产最佳实践补充；凡本文标注「生产级补充」处，实现时以 golden-path 为准，不得回退到示例形态。

---

## 合同八问的类型特化

> 通用骨架见 L1 §3；下列为 `client-component` 的差异化取证点。每个交互组件以 `### UNIT-<slug>` 定义，下游测试/实现切片裸 token 引用该 UNIT。

1. **承接哪些行为**：本组件承载的用户交互与客户端生命周期行为，逐条引用 `BHV-NNN`（必须存在于 prd，幽灵引用/无承接 = 断链 P1）。client-component 只承接「交互/状态/反馈」类行为，不承接业务规则与数据获取行为（后者归 server 链）。
2. **输入 / 输出 / 错误**：
   - **输入 = props（唯一数据入口）**：逐 prop 列表（名称 / 类型（引用 `domain-type` 的 TS 类型或 zod 推导类型）/ 必填 / 默认值 / 来源：由哪个 `server-component` 透传 / 哪个 `route` 段注入）。props 必须可序列化（RSC→Client 边界约束）；**禁止把不可序列化值（函数闭包除 server-action 引用外、Date 以外的类实例、Symbol）当 props 跨边界传入**。
   - **输出 = 客户端状态字段全集 + 对外回调**：状态字段**必须逐字段列表**（名称 / 类型 / 初始值 / 写入时机 / 写 hook：useState/useReducer）；对父级的回调 props（`onXxx` 签名）单列。
   - **错误 = 交互三态收口**：每个异步交互（提交、乐观更新、客户端校验）必须定义 `pending / success / error` 三态的展示去向（loading 占位 / 成功反馈 / 错误提示与重试入口）；接 server-action 时声明 `useActionState` 的返回形态（生产级补充）。
3. **读取 / 写入哪些状态**：
   - 本组件是其 `useState/useReducer` 字段的**唯一写 owner**；从 props 接收的数据**只读**，不在本地复制后双写。
   - **禁止两个 client-component 写同一份共享状态**：跨组件共享态归 Context Provider / 状态库（`project-conventions` 状态管理槽位：none/Zustand/Context），并在合同中声明 owner。
   - **业务/服务端权威状态不在此持久**：服务端数据的真相源是 server 链；本地仅持有交互态（展开/选中/输入草稿/乐观快照）。
4. **调用哪些依赖，不调用哪些依赖**（正反两面都写）：
   - **可依赖**：`ui-component`（交互链 `client-component → ui-component`，把纯展示下沉）；React 客户端 hooks；从 props 传入的 server-action 引用（仅调用，不在此定义）；客户端工具函数（无 IO）。
   - **不可调用（越界 = P1）**：`data-access`（数据访问层只在 server 链）；直接 `fetch` 私有接口 / 读 secret / 读环境密钥（**私有数据获取只允许在 `server-component`/`data-access`/`server-action`，client-component 直取 = 硬规则违反 P1**）；ORM / 数据库 / 内容源（MDX/CMS）直读；`server-component`（不可反向 import 服务端组件实现）。
5. **失败如何收口**：每条失败路径 → 写入 error 态字段 + 用户可见反馈（toast / inline 错误 / 占位 / 重试按钮），且不吞错（错误既不静默丢弃也不裸 throw 到无边界处）；接 server-action 的失败经 `useActionState`/返回值回流到 error 态；运行时渲染异常由上层 `error.tsx`（owner：route）兜底，本组件声明「依赖哪个错误边界」。
6. **产生哪些事件 / 后置结果**：埋点事件清单（事件名 + 触发时机 + 参数）；客户端导航动作（`useRouter().push/replace` 去哪个 route 段、带什么参数）；副作用清单（`useEffect` 订阅/解绑、localStorage 读写、媒体播放）逐条写明消费方与清理时机。
7. **哪些测试验证它**：交互→状态转移 = 组件测试（`project-conventions` 测试槽位 Vitest+RTL，mock server-action 与回调 props）；端到端交互（提交链路、导航）= Playwright；三态（pending/success/error）逐条有用例；**不在此层测服务端数据正确性**（归 data-access/server-action 测试）。每条承接 BHV 至少 1 成功 + 全部失败路径用例。
8. **哪些内容不得在此补造**：不发明业务规则（属 `server-action`/server 链）；不决定数据获取/缓存/`revalidate`（属 `data-access`/`server-component`）；不定义领域类型/schema（属 `domain-type`，本组件引用而非新建）；不写 SEO/metadata（属 `route`）；不在 client 侧实现鉴权判定/读取 secret（属 server 链）。

---

## 类型硬规则（golden-path 锁定，违反 fail）

- **`'use client'` 最小化（server-first）**：指令置于文件首行，且只标注**真正需要交互的最小子树**。能拆出的纯展示部分必须下沉到 `ui-component`；不得为图省事把大块 server-component 整体改成 client。一个 `'use client'` 文件 import 的所有模块都会被打进客户端 bundle —— 合同需声明「为何必须 client（哪个 hook/事件触发了边界）」。
- **TS strict**：`tsconfig` 必须 `"strict": true`（示例 `strict:false` 不可照抄，属生产级补充）；props 与状态字段禁止 `any`；事件 handler 显式标注事件类型。
- **数据从 props / server-action 接，不直取私有数据**：组件不自行 `fetch` 私有接口、不读 secret/env、不直连内容源（MDX/CMS/ORM）。服务端数据由 `server-component` 通过可序列化 props 传入；变更通过 props 传入的 server-action 引用提交（`useActionState`/`<form action={...}>`，生产级补充）。
- **状态/事件/hooks 边界**：客户端 hooks 仅在 `'use client'` 文件内使用；`useEffect` 必须有清理（订阅/定时器/事件监听泄漏 = P1）；受控输入声明 value+onChange 配对。
- **样式隔离**：CSS Modules 或 Tailwind（`project-conventions` 样式槽位），**禁止全局样式污染**（示例的 `<style jsx>` 属 Pages Router 形态，App Router 生产以 CSS Modules/Tailwind 为准）。
- **共享状态归一**：跨组件状态用 Context/状态库（`project-conventions` 状态管理槽位），owner 唯一；同一份交互状态出现在两个 client-component 的写路径 = P1（回概要重判归属）。
- **可序列化边界**：跨 RSC→Client 的 props 必须可序列化；不可序列化能力以 server-action 引用或在 client 内部 hooks 重建，不跨边界透传。

---

## 不适用场景（明确边界，避免误归本类）

- 组件无 `useState/useEffect/事件/hooks` → 不应加 `'use client'`，归 `ui-component`。
- 组件需要在服务端取数据后渲染 → 归 `server-component`（保持默认 RSC）。
- 仅做表单提交/数据变更的纯函数（无 UI） → 归 `server-action`。
- `error.tsx`/`loading.tsx`/`page.tsx`/`layout.tsx` 段文件 → 归 `route`（即便 error.tsx 内部需 `'use client'`）。

---

## 好 / 坏例子（要点）

- ✅ **好**：
  - props 表完整且只读（`post: PostMeta`（引用 domain-type）/ `submitComment: (formData: FormData) => Promise<ActionResult>`（server-action 引用，由 server-component 透传）），可序列化边界明确。
  - 状态字段表齐全（`isExpanded: boolean = false，onClick toggle`；`draft: string = ''，onChange 写入`）；每个异步交互三态齐全（`useActionState` 的 `pending/error/success` 都有展示去向）。
  - `'use client'` 只标在「评论输入框 + 提交按钮」子树，文章正文与列表仍是 server-component 渲染并透传；展示细节下沉到 `ui-component`。
  - 依赖只有 ui-component + 传入的 server-action + 客户端 hooks；声明依赖 `error.tsx` 兜底渲染异常。
- ❌ **坏**：
  - 「管理交互相关状态」一句话带过（无 props 表、无字段表）。
  - 组件内 `fetch('/api/internal/...')` 直取私有数据 / `process.env.SECRET`（违反「私有数据只在 server 链」硬规则 P1）。
  - 整页加 `'use client'`（server-first 失败，把可 RSC 的数据获取也拖进客户端 bundle）。
  - error 态写「待定」；`useEffect` 订阅无清理；两个组件各自 `useState` 同一份选中态（双写）。
  - 照抄示例 `tsconfig` 的 `strict:false`、用 `<style jsx>` 全局/内联样式（生产级补充被回退）。

---

## Gate 判定（本类自检，喂给 L1 §7 G1~G5 / full 链 G6~G7）

- **G-CC-1**：每个 `### UNIT-<slug>` 八问齐全；props 表（只读 + 可序列化 + 来源）与状态字段表（名/类型/初始值/写时机）非空、无 `any`。
- **G-CC-2**：每条承接 `BHV-NNN` 真实存在于 prd 且可双向追溯；无幽灵引用、无无承接行为。
- **G-CC-3**：依赖正反面都写；命中「直取私有数据 / 读 secret / 直连 data-access·ORM·内容源」任一即 P1 fail。
- **G-CC-4**：`'use client'` 范围有「为何必须 client」论证且为最小子树；可下沉部分已归 `ui-component`。
- **G-CC-5**：异步交互三态（pending/success/error）齐全且每态有展示去向与测试映射（成功 + 全部失败路径）。
- **G-CC-6**：共享状态 owner 唯一（Context/状态库），无跨组件双写；`useEffect` 副作用有清理。
- **G-CC-7**：样式走 CSS Modules/Tailwind（无全局污染）；`tsconfig` strict（无 `strict:false` 照抄）。
- **G-CC-8**：§「不得补造」逐条存在（不发明业务规则/不决定缓存/不建 domain-type/不写 metadata）。

> l2_status: full（本类 v1 提供 L2，与同级 `detail-type-server-component.md` / `detail-type-data-access.md` 构成 render/interactive/data 三元组）。route / ui-component / domain-type / server-action 四类为 `l2_status: pending`，按 L1 合同八问展开并在 design-main 声明 `L2豁免`。
