# Widget Guidelines

> 本项目 widget 的真实写法约定：const 构造、widget 拆分、build 边界。

---

## Const Constructors

<!--
- 哪些 widget 必须声明 const 构造？lint 是否强制？
- const 对 rebuild 的实际收益在本项目体现在哪里？
- 何时无法 const、应如何处理？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (漏掉 const / 阻断 const 传播的反例，bootstrap 从真实项目补)

// CORRECT:
// (正确使用 const 构造的正例，bootstrap 从真实项目补)
```

---

## Widget Decomposition

<!--
- 一个 widget 多大时必须拆分？按什么边界拆（语义块 / 复用 / rebuild 范围）？
- 拆成「独立 widget 类」还是「build 内私有方法」的取舍标准是什么？
- 拆分后参数怎么传，避免层层透传？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (巨型 build / 用方法返回 widget 导致 rebuild 失控的反例)

// CORRECT:
// (按本项目约定拆分为独立 widget 的正例)
```

---

## Build Method Boundaries

<!--
- `build` 里禁止做哪些事（IO / 副作用 / 重计算 / 状态变更）？
- 业务逻辑、数据获取应在哪里发生，而不是 build？
- 如何避免在 build 内创建新实例导致重复 rebuild？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Keys & Identity

<!--
- 列表 / 动态子树何时必须显式 Key？用哪种 Key？
- GlobalKey 的允许场景与禁用场景是什么？
- 误用 Key 导致状态错乱的真实案例是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!--
- 本项目 widget 层最常踩的写法错误有哪些？
- 哪些是 review 中反复打回的反模式？
- 每条对应的正确写法是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
