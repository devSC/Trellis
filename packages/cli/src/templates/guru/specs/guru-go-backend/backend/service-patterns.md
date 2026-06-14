# Service Patterns

> 本项目 biz 层（service 编排与依赖注入边界）的真实模式。

---

## Overview

<!-- biz 层承担什么职责？业务编排、事务边界、跨 repository 协调放在这一层吗？service 的粒度怎么定？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Service Composition

<!-- service 如何编排多个 repository / 子 service？一个用例（use case）对应一个方法还是一个 service？事务在哪里开启/提交？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Dependency Injection Boundary

<!-- 依赖怎么注入（构造函数 / wire / 手写 container）？service 依赖的是 repository 接口还是具体类型？接口定义在哪一层（消费方还是实现方）？ -->

```go
// WRONG: <!-- 反例：service 内部 new 具体 repository、依赖泄漏到 entry-api -->

// CORRECT: <!-- 正例：构造函数注入接口、依赖在装配处组装 -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Transaction & Orchestration

<!-- 跨多个写操作如何保证一致性？事务对象怎么在 service → repository 间传递？编排失败时如何回滚/补偿？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- biz 层踩过的坑（业务逻辑下沉到 repository、service 直接 import entry-api、事务边界错位等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
