# Domain Model

> 本项目 domain 层模型与 sentinel error 归属的真实约定。

---

## Overview

<!-- domain 层放什么？纯数据结构、业务不变量、还是行为方法？它是否零外部依赖（不 import 上层与基础设施）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Model Definition

<!-- domain 模型怎么定义（struct 字段、可见性、值对象 vs 实体）？构造/校验在哪做（工厂函数还是直接字面量）？ -->

```go
// WRONG: <!-- 反例：domain struct 带 json/db tag、import repository 或 entry-api -->

// CORRECT: <!-- 正例：纯净 domain 模型 + 构造函数保证不变量 -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Sentinel Errors Ownership

<!-- sentinel error（如 ErrNotFound）定义在哪一层、属于哪个 domain？命名约定？谁负责返回、谁负责翻译？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Invariants & Behavior

<!-- 业务不变量在哪强制（domain 方法还是 service）？domain 是否含行为方法？什么逻辑该进 domain、什么该留 biz？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- domain 层踩过的坑（贫血/失血模型、tag 污染、sentinel 放错层导致循环依赖等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
