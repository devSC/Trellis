# Bootstrap Task: Fill Project Development Guidelines (H5 / Next.js / guru)

**You (the AI) are running this task. The developer does not read this file.**

The developer just ran `trellis init -t guru-h5-web` + the guru overlay
on this project for the first time. `.trellis/` now exists with the guru spec:
`harness/` (五阶段方法学 SSOT), `conventions/` (项目约定槽位), `guides/golden-path.md`
(通用方法), and **empty by-layer scaffolding** `frontend/ backend/ shared/`.

**Your job**: populate the project's *real* coding conventions into two places —
1. the **by-layer spec** (`.trellis/spec/frontend|backend|shared/*.md`) — open-ended
   pattern docs so every future `trellis-implement` / `trellis-check` sub-agent
   matches THIS project's actual style; and
2. the **conventions slots** (`.trellis/spec/conventions/project-conventions.md`) —
   the pinned SLOT decisions that the 五阶段 writing/review Gate hard-requires (C1~C6).

Empty spec = sub-agents write generic code. Real spec = sub-agents match the team's
actual patterns. **Do NOT fill `harness/` or `guides/golden-path.md`** — those are the
guru methodology (maintained by the config pack); you only *follow* them when filling
the by-layer files (respect the 分层依赖律 and the doc_type 七类).

Don't dump instructions. Open with a short greeting, figure out if the repo has any
existing convention docs (CLAUDE.md, .cursorrules, etc.), and drive the rest
conversationally.

---

## Status (update the checkboxes as you complete each item)

- [ ] Imported any existing convention docs (CLAUDE.md / .cursorrules / CONTRIBUTING.md)
- [ ] Filled `.trellis/spec/frontend/` (UI / 表现层：route / server-component / client-component / ui-component) with real patterns + code examples
- [ ] Filled `.trellis/spec/backend/` (server 侧：route handler / data-access / server-action) with real patterns + code examples
- [ ] Filled `.trellis/spec/shared/` (跨层规范) with real patterns + code examples
- [ ] Filled `.trellis/spec/conventions/project-conventions.md` slots (C1~C6 pass)
- [ ] Verified every code example references a REAL file path in this repo

---

## Spec files to populate

### `frontend/` — UI / Presentation layer（route / server-component / client-component / ui-component / state / type-safety / quality）

| File | What to document |
|------|------------------|
| `.trellis/spec/frontend/directory-structure.md` | `app/` 下路由段 / 组件 / hooks 的真实组织（route 段保留文件名、co-location、`_private`/`(group)` 分组、组件与 hooks 目录分界） |
| `.trellis/spec/frontend/server-components.md` | `server-component` 默认形态：RSC `async` 组件内编排取数、把交互下推给 client-component、props 序列化边界的真实写法 |
| `.trellis/spec/frontend/client-components.md` | `client-component` 的 `'use client'` 判定与边界：何时标最小叶子、交互态/事件/hooks、禁直取私有数据的真实约定 |
| `.trellis/spec/frontend/ui-components.md` | `ui-component`（UI 组件库 shadcn/MUI/自建）来源与 props 约定：纯展示、无数据获取、无业务的真实封装边界 |
| `.trellis/spec/frontend/state.md` | 实际客户端状态方案（none / Context / Zustand）、状态 owner 落点与 store 入口 |
| `.trellis/spec/frontend/type-safety.md` | `tsconfig` strict 档位、`domain-type`（type/interface/zod）类型组织与跨 server→client 序列化约定 |
| `.trellis/spec/frontend/quality.md` | eslint / `tsc --noEmit` / test（Vitest+RTL / Playwright）命令与门禁 |

### `backend/` — Server 侧（route handler / data-access / server-action / error boundary）

| File | What to document |
|------|------------------|
| `.trellis/spec/backend/route-handlers.md` | `route.ts`(Route Handler) / API 路由约定（GET/POST 形态、运行时 edge/node、返回与缓存语义） |
| `.trellis/spec/backend/data-access.md` | `data-access` 层的真实写法（**只在 server 侧 / 私有数据红线**：`import 'server-only'`、fetch 缓存显式、内容源 MDX/CMS/ORM 封装、出错上抛、返回 domain-type） |
| `.trellis/spec/backend/server-actions.md` | `server-action`（`'use server'`）约定：入参校验、鉴权先行、经 data-access 落数、`revalidatePath`/`revalidateTag` 后置 |
| `.trellis/spec/backend/error-handling.md` | server / client 错误边界收口位置（`error.tsx` / Suspense / 异常转换层 / server-action 失败返回形态、server 端不泄漏内部细节） |

### `shared/` — Cross-layer

| File | What to document |
|------|------------------|
| `.trellis/spec/shared/ts-conventions.md` | TypeScript 语言级约定（`unknown` 收窄、禁 `any`/`@ts-ignore`、`z.infer` 单一来源等） |
| `.trellis/spec/shared/naming-conventions.md` | 文件 / 组件 / 类型 / 变量命名规律（route 保留文件名、`*-component`/`*.module.css` 后缀、kebab/PascalCase 规律） |
| `.trellis/spec/shared/git-conventions.md` | 分支 / 提交 / PR 约定 |

### `conventions/project-conventions.md` — pinned SLOT decisions (Gate 硬前置)

从 `conventions/project-conventions.template.md` 复制为 `project-conventions.md`，逐 SLOT 填本项目取值；
参考同目录的样例 `nextjs-blog.project-conventions.md` 的填法与「实测扫描」元信息格式（注意：该样例是
Pages Router + `strict:false` 的简化 starter，仅作内容模型基线，**不得当作 App Router 生产取值照搬**）。
必须过 C1~C6 校验（元信息 / 全槽位取值 / 每槽代码证据 / **doc_type 纯净（七类锁定，不串 flutter/Go 类型名）** /
不与硬规则冲突 / 存量违例清单 SLOT-18）。

---

## How to fill the spec

### Step 1: Import from existing convention files first (preferred)

Search the repo for existing convention docs. If any exist, read them and extract the
relevant rules into the matching `.trellis/spec/` files — usually much faster than
documenting from scratch.

| File / Directory | Tool |
|------|------|
| `CLAUDE.md` / `CLAUDE.local.md` | Claude Code |
| `AGENTS.md` | Codex / Claude Code / agent-compatible tools |
| `.cursorrules` / `.cursor/rules/*.mdc` | Cursor |
| `.windsurfrules` / `.clinerules` / `.roomodes` | Windsurf / Cline / Roo |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `CONTRIBUTING.md` / `CONVENTIONS.md` | General project conventions |
| `.editorconfig` / `.eslintrc*` / `eslint.config.*` / `.prettierrc*` / `tsconfig.json` | Formatting / lint / strict rules |

### Step 2: Analyze the codebase (H5 / Next.js scan points)

Scan real code to discover patterns. Before writing each spec file, find 2-3 real
examples and reference **real file paths**. H5 扫描点：
- `package.json` — `next` 版本与路由模式信号、状态库（Zustand/Context）、UI 库（shadcn/MUI）、测试与 lint 脚本、构建链（`build` 是否前置内容派生脚本）（SLOT-07/08/09/14）。
- `app/` 目录树 — App Router 路由段组织（`page`/`layout`/`loading`/`error.tsx`/`route.ts`、`(group)`/`_private`/`[slug]`），与 `pages/` 是否并存的新旧分界（SLOT-01/02）。
- `grep "'use client'"` — `'use client'` 用量与位置（是否下推到最小叶子 vs 整页降级；client-component 边界判定，硬规则 2）。
- `lib/` / `data-access` 层 — 内容源读取与 fetch 封装入口（`import 'server-only'`、`getAllPosts/getPostBySlug` 形态、`gray-matter`/CMS SDK/ORM 查询、缓存语义）（SLOT-03/04/12）。
- `grep "'use server'"` / `app/**/route.ts` — `server-action` 与 Route Handler（变更链、入参校验、`revalidatePath`/`revalidateTag`）（SLOT-05）。
- `next/image` 用量 + `next.config.*` 的 `images.remotePatterns` — 图像优化与远程图域白名单（SLOT-10）。
- `middleware.ts` / `auth.ts` / `app/api/auth/*` — 认证（NextAuth/Auth.js 或自建 session）、鉴权拦截落点（SLOT-11）。
- `tsconfig.json` 的 `"strict"` — TS strict 档位（生产基线必须 `true`；示例 blog 为 `false`，以生产基线为准）（SLOT-13）。
- 既有架构违例（`grep` client-component 直取私有数据 / 反向 import / 整页 `'use client'` / 全局 CSS 污染）→ `conventions` SLOT-18 存量清单。

填 by-layer 时遵循 `guides/golden-path.md` 的分层依赖律（`route → server-component → data-access → domain-type`；`client-component → ui-component`；`server-action → data-access`）
与 `harness/` 的 doc_type 七类口径（`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`），
不复写它们的正文，只引用。

### Step 3: Document reality, not ideals

**Critical**: write what the code *actually does*, not what it should do. Sub-agents
match the spec, so aspirational patterns that don't exist in the codebase will cause
sub-agents to write code that looks out of place. If the team has known tech debt
(整页 `'use client'`、Pages Router 遗留、`strict:false`、全局 CSS 污染等), document the
current state in SLOT-18 — improvement is a separate conversation, not a bootstrap concern.

---

## Quick explainer of the runtime (share when they ask "why do we need spec at all")

- Every guru task spawns `trellis-implement` (writes code) + `trellis-check` (verifies).
- Each task's `implement.jsonl` / `check.jsonl` list which spec files to load; the guru
  `guru_after_create` hook seeds the baseline (golden-path + harness index + conventions
  + the relevant by-layer `index.md`), and Research/add-context picks the precise topics.
- The platform hook auto-injects those spec files + the task's `prd.md` into every
  sub-agent prompt — so sub-agents code/review per team conventions automatically.
- Source of truth: `.trellis/spec/`. Filling it well now pays off forever.

---

## Completion

When the developer confirms the checklist items above are done with real examples
(not placeholders), guide them to run:

```bash
python3 ./.trellis/scripts/task.py finish
python3 ./.trellis/scripts/task.py archive 00-bootstrap-guidelines
```

After archive, every new developer who joins this project gets a `00-join-<slug>`
onboarding task instead of this bootstrap task.

---

## Suggested opening line

"Welcome to guru/Trellis! Your init set me up to fill this project's spec — a one-time
setup so every future AI session matches your team's actual Next.js/H5 patterns instead of
writing generic code. I'll fill `frontend/`, `backend/`, `shared/` and the
`project-conventions.md` slots. Do you have existing convention docs (CLAUDE.md,
.cursorrules, CONTRIBUTING.md) I can pull from, or should I scan the codebase from
scratch?"
