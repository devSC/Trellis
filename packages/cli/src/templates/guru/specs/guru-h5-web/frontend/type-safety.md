# Type Safety

> 本项目 TypeScript strict 档位、类型组织与领域类型（domain-type）约定。

---

## Strict Configuration

<!-- 本项目 `tsconfig.json` 的 strict 档位（`strict: true`？`noUncheckedIndexedAccess` 等额外开关）？`target`/`moduleResolution` 取值？是否禁用 `any` 兜底关键边界？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Type Organization

<!-- 类型放哪（colocate / `types/` / `lib/`）？domain-type 与组件 props 类型如何分？共享类型如何导出？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Runtime Validation & Schemas

<!-- 外部输入（frontmatter / API 响应 / searchParams）如何在运行时校验（zod / valibot）？schema 与静态类型如何同源（`z.infer`）？校验落在哪一层？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Boundary Typing

<!-- RSC 的 `params`/`searchParams`、server-action 入参/返回（`ActionResult`）、data-access 返回类型如何标注？跨 server/client 边界的类型约束？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在类型安全上踩过哪些坑？（用 `any`/`as` 绕过、未校验外部数据直接当类型、类型与运行时 schema 漂移） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```ts
// WRONG: <填反例 — 如 const data = res as PostMeta 跳过运行时校验 / any 兜底>

// CORRECT: <填本项目正确的类型组织与运行时校验写法 — 真实路径>
```
