# Error Handling

> 本项目错误收口位置与传播约定（集中 normalizer vs 分散 try-catch）。

---

## Overview

<!--
- 本项目错误在哪一层被收口（拦截器 / repository / usecase / 表现层）？
- 是集中式（统一 normalizer）还是分散式（各处 try-catch）？
- 网络错误、业务错误、本地错误如何分类？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Error Types

<!--
- 本项目定义了哪些自定义错误/异常类型？放在哪一层？
- DioException / 平台异常 如何被映射成领域错误？
- 错误是否携带错误码 / 可展示文案 / 原始 cause？
-->

```dart
// WRONG: <在此放本项目实际禁止的错误类型定义/抛出写法>

// CORRECT: <在此放本项目实际推荐的错误类型定义/抛出写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Normalization & Collection Point

<!--
- 错误规整（normalize）发生在哪一个具体位置？为什么选这里？
- 集中收口点接收什么、产出什么（统一 Failure / 统一异常）？
- 拦截器层的错误处理与上层收口如何分工？见 api-patterns.md。
-->

```dart
// WRONG: <在此放本项目实际禁止的错误收口写法（如多处重复 try-catch）>

// CORRECT: <在此放本项目实际推荐的集中收口写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Propagation to UI

<!--
- 错误如何传播到表现层（异常 / Either / Result）？
- 表现层如何决定展示文案、重试、上报？
- 哪些错误被静默吞掉？约定是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在错误处理上踩过的坑（如吞异常、收口点分散、原始 stack 丢失等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
