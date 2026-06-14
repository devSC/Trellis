# Directory Structure

> 本项目 `services/*/internal` 分层目录的真实组织方式。

---

## Overview

<!-- services 根下每个服务怎么切目录？internal 包含哪些子层（entry-api / biz / repository / domain / config）？哪些是约定、哪些是历史遗留？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Layer Layout

<!-- 每一层放在 internal 下的哪个包？包名与目录名的对应关系是什么？跨服务共享代码放在哪里（pkg / shared / common）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Dependency Direction

<!-- 允许的 import 方向是什么（entry-api → biz → repository → domain）？哪些反向 import 被禁止？如何在代码层面约束（linter / 包可见性）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Naming Conventions

<!-- 文件名、包名、目录名的命名约定？一个文件放一个 service / repository 还是按聚合分组？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 团队在分层组织上踩过的坑（错放层、循环依赖、internal 越界引用等）？ -->

```go
// WRONG: <!-- 反例：跨层 / 反向 import 的目录摆放 -->

// CORRECT: <!-- 正例：符合分层依赖律的目录摆放 -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
