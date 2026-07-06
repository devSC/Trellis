# guides/ 索引（guru-h5-web）

> guru-h5-web spec 库的通用方法入口。本文件只做**导航**，不承载规则正文；规则正文在 `golden-path.md`，项目取值在 `conventions/`，阶段流程在 `harness/`。
> 平台基线：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。参考示例 `next.js/examples/blog` 是 Pages Router + Nextra + MDX + gray-matter 的轻量 blog starter（故意简化）；golden-path 以 **App Router 生产最佳实践**为准，把该示例当**内容模型基线**，并全程区分「示例实证 vs 生产级补充」。

## 本目录文件

| 文件 | 职责 |
|------|------|
| [golden-path.md](./golden-path.md) | 通用方法 SSOT：分层依赖律、各 doc_type 迷你路径、入口决策树、server-first/`'use client'` 最小化、禁止清单、门禁映射 |

- **项目级取值不在本目录**：内容源/状态管理/UI 库/样式/测试/lint/数据库/认证/图像/部署/路由模式等槽位取值一律走 [`../conventions/project-conventions.md`](../conventions/project-conventions.md)（入口见 [`../conventions/index.md`](../conventions/index.md)）。
- **五阶段流程规则不在本目录**：见 [`../harness/index.md`](../harness/index.md)。

## doc_type 权威七类（全程唯一，禁止改名/增减/换数）

> 这是 H5 详细设计的设计单元类型基准（`UNIT-<slug>` 的 `doc_type` 只能取下列七者）。**勿照抄 flutter/Go 的类型名**（controller/usecase/repository 等不在本平台）。

| doc_type | 角色 | L2 状态 |
|----------|------|---------|
| `server-component` | RSC 服务端组件：渲染 + 数据获取编排（默认形态） | L2 full：[detail-type-server-component.md](../harness/detail/detail-type-server-component.md) |
| `client-component` | `'use client'` 交互组件：状态/事件/hooks | L2 full：[detail-type-client-component.md](../harness/detail/detail-type-client-component.md) |
| `data-access` | 数据访问层：`fetch` 封装 / 内容源（MDX/CMS）/ ORM 查询 | L2 full：[detail-type-data-access.md](../harness/detail/detail-type-data-access.md) |
| `route` | App Router route 段：`page`/`layout`/`loading`/`error.tsx` + `metadata`/SEO | L2 pending（按 L1 合同八问展开；full 链须显式 `L2豁免`） |
| `ui-component` | 展示型可复用组件：纯展示、无数据获取、无业务 | L2 pending（同上） |
| `domain-type` | TS 类型 / `zod` schema / 领域模型 | L2 pending（同上） |
| `server-action` | Server Actions / route handlers：变更 / API endpoint | L2 pending（同上） |

> v1 仅交付 L2 三元组（render/interactive/data，对应 flutter 的 controller/usecase/repository-datasource 角色位）：`detail-type-server-component.md` / `detail-type-client-component.md` / `detail-type-data-access.md`。其余四类为 `l2_status: pending`。

## owner 归属与分层依赖律（硬基准，违反 fail）

> 依赖方向只能从上往下，禁反向 / 同层横跳。owner 归属表与承接索引（概要 Gate）、合同八问的依赖声明（详细 Gate）一律以此为权威。

```
服务端链：  route → server-component → data-access → domain-type
交互链：    client-component → ui-component
变更链：    server-action → data-access
```

- 私有数据获取 / secret 只在 `server-component` / `data-access` / `server-action`；**禁** `client-component` 直取（违反 fail）。
- `server-action` 走 `data-access` 落数据，不在交互链里直连 ORM/远端。

## 写作顺序（自底向上）

```
domain-type → data-access → server-action → server-component → client-component → ui-component → route
```

## 装载路径（harness 注入用）

- 通用方法：`.trellis/spec/guides/golden-path.md`
- 阶段 SSOT 与详细 L2：`.trellis/spec/harness/*`（概要/详细/实现/萃取；详细 L2 即上表 `detail-type-*.md`）
- 项目取值：`.trellis/spec/conventions/project-conventions.md`

## Gate 衔接（各阶段读什么、卡什么）

| 阶段 | 在本库读 | Gate 卡点（与 flutter 同口径） |
|------|----------|--------------------------------|
| 需求 | —（走需求三件套 SSOT，经 jsonl 引用） | 需求五要素：无行为 / 前置条件 / 状态变化 / 失败路径 / 验收场景 → 不进概要 |
| 概要 | `harness/overview/*` | 行为无唯一 owner+三问理由、归属违反上方分层依赖律、承接索引缺失 → 不进详细 |
| 详细 | `harness/detail/*` + 上表七类 `doc_type` | 合同八问缺项、追溯不到概要 owner、无测试映射、`pending` 类未标 `l2_status`/full 链未 `L2豁免` → 不进实现 |
| 实现 | `golden-path.md` + `harness/implementation/*` | 计划合同或 mutable evidence 不全、`tsc`/test/lint/compliance 任一无证据 → 不进 commit |
| 审核 | 各 SSOT 审核基线 + `harness/extraction-template.md` | 存量豁免判定；清单外新增违例阻塞 |

- 编号纪律：行为以 `BHV-NNN` 标题定义，设计单元以 `UNIT-<slug>` 标题定义；下游引用写裸 token（不带前后缀解释），断链进不了详细/实现 Gate。

## 示例实证 vs 生产级补充（全程区分）

- **示例实证**（`next.js/examples/blog` 可直接佐证）：MDX 内容源 + `gray-matter` frontmatter 解析、文件路由约定、`scripts/gen-rss.js` 这类构建期内容派生；但其为 **Pages Router + `tsconfig.strict:false`**，仅作内容模型基线。
- **生产级补充**（golden-path 锁定，示例未覆盖）：App Router route 段约定（`page`/`layout`/`loading`/`error.tsx`）、`metadata`/SEO 标准化、TS strict、server-first 与 `'use client'` 最小化、样式隔离（CSS Modules/Tailwind，禁全局污染）、错误边界（`error.tsx`）、Server Actions/route handlers。凡示例与生产基线冲突，**以生产基线为准**。
