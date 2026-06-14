# Type Safety

> 本项目序列化与空安全约定。

---

## Null Safety Conventions

<!--
- 可空类型的使用边界是什么？哪些字段允许 nullable，哪些必须非空？
- 空断言 `!` 的允许场景与禁用场景是什么？
- 默认值 / `??` / `?.` 的统一约定是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (滥用空断言 ! / 用错可空边界的反例)

// CORRECT:
// (符合本项目空安全约定的正例)
```

---

## Serialization

<!--
- 序列化用什么方案（json_serializable / freezed / 手写 fromJson）？
- model 类放在哪一层，UI 层如何消费？
- 字段命名映射、可空字段、默认值如何处理？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (手写易错 / 字段类型不严的序列化反例)

// CORRECT:
// (按本项目方案生成 / 编写序列化的正例)
```

---

## Avoiding dynamic

<!--
- `dynamic` 在本项目是否禁用？例外场景有哪些？
- 解析外部数据（JSON / 路由 extra）时如何尽早收敛到具体类型？
- lint 是否对 dynamic / implicit-dynamic 做门禁？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Enums & Sealed Types

<!--
- 有限取值用 enum 还是字符串常量？转换怎么做？
- 是否用 sealed class / freezed union 表达状态机？
- 穷尽匹配（exhaustive switch）的约定是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!--
- 本项目类型安全最常见的错误有哪些（空崩溃 / dynamic 漏网 / 序列化错配）？
- 哪些是线上事故 / review 反复打回的来源？
- 每条对应正确做法是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
