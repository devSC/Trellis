# ADR 格式（H5 / Next.js App Router 架构决策记录）

ADR 落在目标仓库 `docs/adr/`，顺序编号：`0001-slug.md`、`0002-slug.md` …… slug 用短横线连接、体现决策主题（如 `0001-content-source-mdx-over-cms`、`0002-render-strategy-isr`、`0003-app-router-over-pages`）。

`docs/adr/` 目录**惰性创建**——只在第一条 ADR 真正需要时建。

## 模板

```md
# {决策的一句话标题}

{1~3 句：上下文是什么、我们决定了什么、为什么。}
```

就这样。一条 ADR 可以只有一段。价值在于记录**做了一个决策**以及**为什么**——而不是把章节填满。正文中文优先，代码标识符/库名/路径/框架字段保留原文（如 `'use client'`、`server-only`、`generateMetadata`、`revalidateTag`、`next/image`、`app/feed.xml/route.ts`、`NEXT_PUBLIC_*`）。

## 可选章节

只在确实增加价值时加，多数 ADR 用不上：

- **Status** frontmatter（`proposed | accepted | deprecated | superseded by ADR-NNNN`）——决策会被重新审视时有用，对齐 project-conventions 槽位升级（如某 SLOT 从"当前取值"升到引入某方案）的状态流转。
- **Considered Options**——只在被否决的备选值得记住时（如"评估过 Headless CMS 与本地 MDX，选 MDX 因编辑者单一、内容量小"）。
- **Consequences**——只在有不显然的下游影响要点名时（如"改 ISR 后，所有列表页 `fetch` 必须显式声明 `next: { revalidate }`，且 `server-action` 变更后须 `revalidatePath` 对应路径，否则旧缓存不失效"）。

## 编号

扫描 `docs/adr/` 取现存最高编号 +1，不跳号、不复用。

## 何时提议 ADR（三条全中才提）

1. **难以回头** —— 以后改主意的代价不小。
2. **缺上下文会困惑** —— 未来读者看代码会想"为什么偏要这样做？"。
3. **真实权衡的产物** —— 确实有备选项，为具体理由选了其一。

易回退就跳过（反正会被改回去）；不令人意外就没人会问为什么；没有真备选就没什么可记的（"我们做了显而易见的事"不值得记）。

## H5 / Next.js 哪些决策够格记 ADR

拷问中命中以下情形、且三条全中时，当场起草 ADR（用户确认后落盘）：

- **内容源选型（内容源槽位，带锁定成本）**：本地 MDX vs Headless CMS vs ORM(DB)。内容源决定 data-access 形态与 domain-type 建模方式，迁移成本高（如本地 MDX 经 frontmatter 解析建模，切到 CMS 是架构级变更）。
- **渲染策略（SSR / SSG / ISR + 缓存语义）**：每页选哪种渲染、`fetch` 的 `cache`/`next.revalidate` 周期、按需失效靠 `revalidatePath`/`revalidateTag`。渲染策略与缓存语义是 server-component / route / server-action 的合同锁定点（overview L1 §2.6 要求其成为 `technology_decision_handoff` 决策项）。
- **路由模式（路由模式槽位）**：App Router（golden-path 默认）vs Pages Router。偏离 App Router 默认必须记理由（新项目退回 Pages 属架构决策 + 更新路由模式槽位；既有 Pages Router 扁平结构属存量违例清单登记的偏离形态）。
- **状态管理引入（状态管理槽位）**：默认 none（server-first）→ 引入 Zustand / 把 Context 包到某子树。把全局状态库或根级 Context 引进来会改变 `'use client'` 边界与 hydration 形态，是锁定决策（默认应优先用最小 client 叶子的 `useState`）。
- **认证 / 会话方案（认证槽位）**：无 → 引入 NextAuth(Auth.js) 或自实现 session。鉴权校验只在 server 侧（server-component/data-access/server-action/route handler），session/token 禁止暴露给 client-component 直取；切换方案记 ADR + 更新认证槽位。
- **数据 / 范围归属边界（显式的"不做"和"谁拥有"）**：如"front-matter 内容由 server-only 的 data-access（`lib/posts.ts`，`import 'server-only'`）拥有，client-component 只经可序列化 props 读，不反向 import 取数模块"；"私有 env / 凭证只经 `process.env.X` 在 server 边装载，不下发到 client bundle（`NEXT_PUBLIC_` 仅限非敏感公开值）"。显式的边界与拒绝和肯定同样有价值。
- **样式方案（样式方案槽位）**：Tailwind vs CSS Modules（单项目内统一）。混用与切换有迁移成本；偏离受控隔离（裸全局 CSS）是硬红线、应回退而非记 ADR。
- **代码不可见的约束**：合规/法规导致的技术选择（如"Cookie 同意横幅前不得加载第三方分析脚本""不可采集某类用户数据"）、外部契约的 SLA（如"首屏须 < 200ms 因合作方接口约束，故该页强制 SSG"）。
- **非显然的被否决备选**：评估过却否决、且半年后会有人再提的方案（如"评估过把整页标 `'use client'` 用纯客户端取数，否决，坚持 server-first + RSC 取数以保 SEO 与首屏"）——记下来，免得下次再被提一遍。

不够格的（不记，照 golden-path 默认走即可）：按迷你路径新增一个常规 server-component / route 段 / ui-component；复用既有 data-access 的 `getXxx` 函数；按既有 front-matter 模型加一个 domain-type 字段；沿用约定的 Vitest+RTL / Playwright 写测试；把一个交互叶子标 `'use client'` 持局部 `useState`。

> 注意：H5 三条最高禁令（分层依赖律违反 / client 直取私有数据·secret / 全局样式污染）本身是**不可豁免硬红线**——触碰应当场 fail 回退修订，**不是**用 ADR"背书例外"。ADR 记的是合法权衡（选型、策略、边界），不是为越线开口子。
