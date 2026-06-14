# Repository & Data

> 本项目 repository 层数据访问与 db 迁移的真实约定。

---

## Overview

<!-- repository 层职责边界是什么？只做 CRUD/查询还是也含映射？用 database/sql、sqlx、还是某 ORM？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Repository Interface & Implementation

<!-- repository 接口在哪定义、由谁实现？方法签名约定（返回 domain 模型还是行结构）？context 如何贯穿？ -->

```go
// WRONG: <!-- 反例：repository 返回原始 sql 行 / 泄漏 *sql.DB 给上层 -->

// CORRECT: <!-- 正例：返回 domain 模型、接口由 biz 消费方定义 -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Query & Mapping

<!-- SQL 写在哪（内联 / 文件 / 生成）？行如何映射成 domain 模型？空值/可空列怎么处理？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## DB Migrations

<!-- 迁移工具是什么（migrate / goose / 自研）？迁移文件放哪、命名规则？何时/如何执行（启动时还是独立步骤）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- repository 层踩过的坑（N+1、连接未释放、迁移漂移、把 sql.ErrNoRows 透传等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
