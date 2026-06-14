# API Design

> 本项目 entry-api 层（net/http 路由、JSON 编解码、错误码映射）的真实约定。

---

## Overview

<!-- entry-api 层职责边界是什么？只做传输/编解码还是也含校验？用标准库 net/http 还是某框架？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Routing

<!-- 路由如何注册（mux / ServeMux / 第三方 router）？路径与 handler 的组织方式？中间件链怎么挂？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Request / Response Encoding

<!-- 请求体如何解码成 DTO？响应如何编码 JSON？字段命名（json tag）约定？分页/包裹结构长什么样？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Error Code Mapping

<!-- domain/sentinel error 如何映射成 HTTP 状态码与业务错误码？映射表放在哪一层？默认兜底是什么？ -->

```go
// WRONG: <!-- 反例：handler 里裸 err.Error() 直接回写、状态码硬编码散落 -->

// CORRECT: <!-- 正例：集中错误映射 + 稳定错误码 -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- entry-api 层踩过的坑（业务逻辑泄漏到 handler、编解码不一致、错误码漂移等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
