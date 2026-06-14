# Go Conventions

> 本项目 Go 语言级的真实约定与包可见性边界，配 WRONG/CORRECT 对照。

---

## Package Visibility & internal/

<!-- `internal/` 隐私边界怎么用？哪些代码必须进 `internal/`、哪些跨服务契约才进 `packages/contracts/`？导出（大写）与非导出（小写）标识符的取舍规则是什么？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Context Propagation

<!-- `context.Context` 如何在层间传递？哪些函数必须接收 ctx 作为首参？何时尊重 `ctx.Done()` / deadline？是否允许把值塞进 context？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Error Construction Style

<!-- sentinel error 用 `errors.New` 声明在哪？跨层用 `fmt.Errorf("%w: ...")` 的包装前缀约定是什么？判定一律 `errors.Is`/`errors.As`，禁止字符串比对——本项目实际怎么落？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Concurrency & Receivers

<!-- goroutine 生命周期如何管理（避免泄漏、谁负责 cancel）？指针 receiver 与值 receiver 如何取舍？是否禁用 `panic` 作控制流？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Forbidden Patterns

<!-- 本项目明令禁止的 Go 写法有哪些（散读 `os.Getenv`、全局可变状态、跨层反向 import、init() 副作用、空接口 `interface{}`/`any` 滥用等）？为什么禁？ -->

```go
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
