# TS Conventions

> 本项目 TypeScript 语言级的实际约定与惯用法。

---

## Strict & Type Safety

<!-- `tsconfig` strict 档位是什么（必为 strict:true）？哪些编译选项额外开启（noUncheckedIndexedAccess 等）？`any`/`as`/非空断言 `!` 的使用边界与豁免规则是什么？ -->

```ts
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Type Modeling

<!-- 领域类型怎么建模（interface vs type alias、union/discriminated union、enum vs const 对象、zod schema 与 TS 类型的派生关系）？类型放哪一层（domain-type）？ -->

```ts
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Async & Promises

<!-- async/await、Promise、错误传播的写法约定是什么？server-action / data-access 的异步返回形态（Promise<T> / ActionResult）怎么统一？未处理 rejection 如何避免？ -->

```ts
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Imports & Module Organization

<!-- import 排序与分组规则是什么（外部/内部/相对）？路径别名（`@/*`）怎么配？barrel 文件用不用？`import type` 何时强制？server-only / client-only 边界如何在 import 层标注？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- TS 语言层面团队踩过的坑有哪些（隐式 any、`as` 强转绕过类型、可空收窄遗漏、enum 与字面量混用等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
