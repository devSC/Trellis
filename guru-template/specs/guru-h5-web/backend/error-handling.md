# Error Handling

> 本项目 H5 平台 server / client 错误边界的真实约定。

---

## Error Types

<!-- 自定义错误类型/枚举有哪些、业务错误与系统错误如何区分？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Server-Side Error Boundary

<!-- server 侧错误在哪里捕获、如何记录日志、哪些细节不能透传给 client？ -->

```
// WRONG: (待 bootstrap 从真实代码填入向 client 泄露内部错误细节的反例)

// CORRECT: (待 bootstrap 从真实代码填入正例)
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Client-Side Error Boundary

<!-- client 侧如何捕获并展示错误、降级/兜底 UI 约定、如何上报？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## API Error Responses

<!-- 错误响应统一结构、错误码约定、HTTP 状态码如何映射？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在错误处理上踩过的坑 -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
