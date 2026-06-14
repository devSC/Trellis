# State

> 本项目客户端状态方案、状态 owner 归属与生命周期约定。

---

## State Patterns

<!-- 本项目客户端状态用哪种（none：仅 RSC + URL state / React Context / Zustand / 其它）？默认是否 server-first、能不上状态库就不上？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## When to Use Which

<!-- 什么状态留在 URL（searchParams）？什么用本地 `useState`？什么用 Context（局部共享）？什么才用全局 store（跨页共享）？判定边界是什么？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## State Ownership

<!-- 交互状态 owner 是否唯一、只落在 client-component？server 侧是否禁止持有可变全局态？store 实例/Provider 注入点在哪？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Server State & Sync

<!-- 服务端数据与客户端状态如何同步（mutation 后 `revalidate*` / 乐观更新 / refetch）？是否用 React Query/SWR？与 server-action 如何衔接？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在状态管理上踩过哪些坑？（把可派生数据塞进 store、用全局 store 存本可留 URL 的状态、状态 owner 漂移、server 侧持有可变态） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```tsx
// WRONG: <填反例 — 如把 server 数据复制进 client store 并手动同步 / 整页提升状态>

// CORRECT: <填本项目正确的状态方案与 owner 归属 — 真实路径>
```
