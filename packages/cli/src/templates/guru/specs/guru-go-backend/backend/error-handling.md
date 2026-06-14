# Error Handling

> 本项目错误处理的真实约定（`sql.ErrNoRows` → sentinel 翻译与包装风格）。

---

## Overview

<!-- 错误在各层如何流转？哪些层负责翻译、哪些层只透传？错误类型体系是什么（sentinel / 自定义类型 / wrapped）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Sentinel Translation

<!-- repository 如何把 sql.ErrNoRows 翻译成 domain sentinel（如 ErrNotFound）？翻译点在哪一层？基础设施错误是否禁止穿透到 biz？ -->

```go
// WRONG: <!-- 反例：sql.ErrNoRows 直接透传到 biz / handler -->

// CORRECT: <!-- 正例：repository 边界翻译成 domain sentinel -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Wrapping Style

<!-- 用 fmt.Errorf("%w", err) 包装的约定是什么？何时包装、何时直接返回？包装信息里放什么上下文？errors.Is/As 怎么用？ -->

```go
// WRONG: <!-- 反例：丢失原始错误链 / 重复包装 / 包装信息无上下文 -->

// CORRECT: <!-- 正例：%w 保留链 + 携带定位上下文 -->
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Logging vs Returning

<!-- 错误在哪一层记日志、哪一层返回？是否禁止「既记又抛」重复日志？最终面向客户端的错误在哪生成？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 错误处理踩过的坑（吞错、err.Error() 字符串比较、sentinel 漏翻译、重复日志等）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
