# Logging

> 本项目 logger 注入路径与结构化字段的真实约定。

---

## Overview

<!--
- 本项目用什么日志方案（logger 包 / 自封装门面 / 平台通道上报）？
- 日志门面如何获取（DI 注入 vs 全局静态）？见 dependency-injection.md。
- 日志输出去向是什么（控制台 / 文件 / 远端上报）？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Logger Injection Path

<!--
- logger 在 service 层如何注入到 usecase/repository/datasource？
- 是构造注入还是从容器直取？约定是什么？
- 是否按模块/标签创建子 logger？命名约定是什么？
-->

```dart
// WRONG: <在此放本项目实际禁止的 logger 获取/注入写法（如散落 print）>

// CORRECT: <在此放本项目实际推荐的 logger 注入写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Structured Fields

<!--
- 结构化日志包含哪些固定字段（trace id / 用户态 / 模块 / 事件名）？
- 字段命名与类型约定是什么？如何统一拼装？
- 网络请求日志与拦截器的关系见 api-patterns.md。
-->

```dart
// WRONG: <在此放本项目实际禁止的非结构化日志写法>

// CORRECT: <在此放本项目实际推荐的结构化日志写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Levels & Redaction

<!--
- 日志等级如何划分与使用（debug/info/warn/error）？发布版如何降噪？
- 敏感字段（token / 手机号 / 身份信息）如何脱敏？约定是什么？
- 错误日志与 error-handling.md 的收口点如何配合？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在日志上踩过的坑（如直接 print、敏感信息未脱敏、字段不一致难检索等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
