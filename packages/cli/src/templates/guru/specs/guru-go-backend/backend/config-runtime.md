# Config & Runtime

> 本项目 `config.Load`、env 前缀与启动/关闭序列的真实约定。

---

## Overview

<!-- 配置怎么加载（config.Load 入口在哪）？配置来源优先级（默认值 / 文件 / env）？配置结构体放哪一层？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Config Loading

<!-- config.Load 的签名与调用时机？校验在哪做（必填项缺失如何 fail-fast）？敏感配置如何处理？ -->

```go
// WRONG: <!-- 反例：散落的 os.Getenv 直读、缺失值静默兜底 -->

// CORRECT: <!-- 正例：集中 config.Load + 启动期校验 fail-fast -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Environment Variables

<!-- env 前缀约定是什么（如 APP_ / 服务名_）？env key 命名规则？哪些必须由 env 提供、哪些有默认？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Startup & Shutdown Sequence

<!-- main 中依赖的初始化顺序（config → logger → db → server）？优雅关闭怎么做（signal 监听、context 取消、资源释放顺序）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 配置/启动踩过的坑（关闭顺序错导致连接泄漏、env 缺失未 fail-fast、配置散落各层等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
