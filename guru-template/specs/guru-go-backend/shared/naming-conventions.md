# Naming Conventions

> 本项目包/文件/类型/接口/常量的真实命名规律，配 WRONG/CORRECT 对照。

---

## Package & Directory Names

<!-- 包名与目录名的约定是什么（全小写、无下划线、单数还是复数）？分层目录（`transport`/`service`/`repository`/`domain`/`auth` 等）的命名是否固定？包名是否允许与目录名不一致？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## File Names

<!-- 文件名如何命名（snake_case？按领域 `user_repository.go` 还是按类型）？测试文件 `xxx_test.go` 与被测文件如何对应？一个文件放多少类型？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Types, Interfaces & Methods

<!-- 类型名用什么风格（PascalCase 导出/camelCase 私有）？接口命名约定是什么（消费方本地小接口 `xxxStore` / 被依赖方导出大接口 / `er` 后缀 / `I` 前缀禁用）？构造函数命名（`New` 还是 `NewXxx`）？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Constants, Enums & Errors

<!-- 可穷举字段（status/role/protocol/mode）用什么命名（具名常量集 / `iota`）？sentinel error 的 `ErrXxx` 命名约定？env 前缀（如 `CONTROL_API_*`）与配置常量如何命名？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 团队在命名上反复踩过的坑有哪些（缩写不一致、包名与导入路径冲突、stutter 如 `user.UserService`、receiver 名不统一等）？review 时高频打回的点？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
