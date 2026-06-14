# Directory Structure

> 本项目 `app/` 下路由段、组件、hooks 的真实组织方式与目录分界。

---

## Overview

<!-- 本项目源码根在哪？App Router（`app/`）还是仍有 Pages Router（`pages/`）遗留？新代码进哪个目录？顶层目录（app/components/lib/hooks）各放什么？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Route Segments

<!-- route 段如何组织？`page`/`layout`/`loading`/`error`/`not-found` 命名与落点？路由分组 `(group)`、动态段 `[slug]`、并行/拦截路由如何用？metadata/SEO 放哪？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Component Organization

<!-- 组件放 `app/` 内 colocate 还是统一 `components/`？server-component / client-component / ui-component 在目录上如何区分？共享 vs 路由私有组件的分界？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Hooks & Shared Logic

<!-- 自定义 hooks 放哪（`hooks/` / colocate）？数据访问（data-access）与工具函数（`lib/`）目录如何分？server-only 模块如何隔离（`server-only` 包 / 目录约定）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Naming Conventions

<!-- 文件/目录命名规则（kebab-case / PascalCase）？组件文件、hook 文件、类型文件的后缀约定？barrel `index.ts` 用不用？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```tsx
// WRONG: <填本项目踩过的目录组织反例 — 如 client-component 与 server-component 混放无边界 / 整页放 app 根>

// CORRECT: <填本项目正确的目录组织 — 真实路径>
```
