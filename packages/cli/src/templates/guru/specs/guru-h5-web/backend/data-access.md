# Data Access

> 本项目 H5 平台 data-access 层的真实约定（只在 server 侧 / 私有数据红线）。

---

## Server-Only Boundary

<!-- 哪些模块只能在 server 侧 import、如何标记/隔离、构建期如何保证不泄露到 client bundle？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Data Source Access

<!-- DB / 外部 API / 缓存如何访问、连接与 client 在哪里初始化、复用还是每次新建？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Secrets & Private Data Red Lines

<!-- 密钥/token/私有数据的红线：什么绝对不能出现在 client、env 变量命名约定如何区分公私？ -->

```
// WRONG: (待 bootstrap 从真实代码填入私有数据泄露反例)

// CORRECT: (待 bootstrap 从真实代码填入正例)
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Query & Caching Conventions

<!-- 查询封装在哪、是否分页/批量、缓存策略与失效约定？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在 data-access 层踩过的坑 -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
