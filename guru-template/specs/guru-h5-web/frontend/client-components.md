# Client Components

> 本项目 client-component 的 `'use client'` 判定标准与 client/server 边界约定。

---

## When to Use `'use client'`

<!-- 本项目什么情况下才加 `'use client'`（状态 / 事件处理 / 浏览器 API / hooks / 第三方 client-only 库）？判定标准是什么？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Boundary Placement

<!-- `'use client'` 标在哪一层（尽量下沉到交互叶子组件，禁整页 client）？边界如何最小化？哪些组件是边界入口？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Props & Serialization

<!-- 从 server 传给 client 的 props 有何约束（必须可序列化，禁传函数/Date/类实例）？事件回调如何处理？server-action 如何作为 prop 传入？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Data Access Rules

<!-- client-component 是否禁止 import data-access / 直接 fetch 私有数据源 / 读未脱敏 secret？只能拿什么样的脱敏态？违反如何被拦截？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在 client-component 上踩过哪些坑？（整页 'use client'、把 server 逻辑搬进 client、边界过高导致 bundle 膨胀） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```tsx
// WRONG: <填反例 — 如整页顶部标 'use client' / client 组件直接 fetch('/internal/secret-api')>

// CORRECT: <填本项目正确的 client 边界写法 — 真实路径>
```
