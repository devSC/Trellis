# Logging

> 本项目日志的真实约定（logger 注入、结构化字段、请求链路 ID）。

---

## Overview

<!-- 用哪个日志库（slog / zap / zerolog / 自研）？日志门面在哪封装？各层是否统一走同一 logger？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Logger Injection

<!-- logger 如何注入到各层（构造函数 / context / 全局）？是否禁止全局 logger？子 logger（带固定字段）怎么派生？ -->

```go
// WRONG: <!-- 反例：包级全局 logger / fmt.Println 直打 -->

// CORRECT: <!-- 正例：注入 logger 或从 context 取，带 component 字段 -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Structured Fields

<!-- 结构化字段的命名约定（key 规范、必带字段）？敏感字段如何脱敏？日志级别如何分配（debug/info/warn/error）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Request Trace ID

<!-- 请求链路 ID 在哪生成、怎么进 context、怎么贯穿各层日志？跨服务调用如何透传 trace ID？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 日志踩过的坑（无链路 ID、级别滥用、敏感信息泄漏、错误重复打印等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
