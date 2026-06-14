# UI Components

> 本项目 ui-component（纯展示型可复用组件）的组件库选型与 props 约定。

---

## Component Library

<!-- 本项目 UI 基座用哪个（shadcn/ui / MUI / 自建）？组件来源与定制方式？样式方案（Tailwind / CSS Modules）如何配合？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Presentational Purity

<!-- ui-component 是否严格纯展示（无数据获取、无业务逻辑、无状态 owner）？输入只来自 props？哪些职责明确不放进 ui-component？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Props Conventions

<!-- props 命名/类型约定？是否用 discriminated union 表达变体？`className`/`children`/`asChild` 等透传约定？默认值如何给？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Variants & Theming

<!-- 组件变体如何表达（cva / variant props）？主题/design token 来源？暗色模式如何处理？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在 ui-component 上踩过哪些坑？（在展示组件里 fetch、塞业务逻辑、props 爆炸、样式全局污染） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```tsx
// WRONG: <填反例 — 如 ui-component 里做数据获取 / 含业务分支>

// CORRECT: <填本项目正确的纯展示组件 props 写法 — 真实路径>
```
