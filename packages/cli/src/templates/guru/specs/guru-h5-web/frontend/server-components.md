# Server Components

> 本项目 server-component（RSC，默认形态）的写法、数据获取与渲染编排约定。

---

## Default to Server

<!-- 本项目是否以 server-component 为默认（无 `'use client'` 即 server）？哪些场景一定走 server？如何避免误把整页变成 client？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Data Fetching

<!-- server-component 里如何取数据（直接 async/await fetch / 调 data-access 层 / ORM 查询）？内容源是 MDX / CMS / DB？私有数据/secret 是否只在 server 侧读？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Caching & Revalidation

<!-- fetch 缓存策略（`cache`/`next.revalidate`）如何用？`revalidatePath`/`revalidateTag` 在哪触发？静态 vs 动态渲染如何选择？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Composing with Client Components

<!-- server-component 如何向 client-component 传 props（可序列化约束）？children 透传模式如何用？server/client 装配边界在哪？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在 server-component 上踩过哪些坑？（误用浏览器 API、向 client 传不可序列化值、在 server 组件里用 hooks 等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```tsx
// WRONG: <填反例 — 如 server-component 里用 useState / 直接在 client 里 fetch 私有数据源>

// CORRECT: <填本项目正确的 server-component 数据获取写法 — 真实路径>
```
