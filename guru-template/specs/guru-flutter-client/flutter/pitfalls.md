# Pitfalls

> 本项目在 UI 层真实踩过的坑与规避方式。

---

## BuildContext Misuse

<!--
- 跨 async 间隙使用 context 导致的问题有哪些？本项目怎么规避（mounted 检查）？
- 在 dispose / 回调里误用 context 的真实案例是什么？
- 取错层级 context（Theme / Navigator / Provider 找不到）踩过什么坑？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (async 后未判 mounted 直接用 context 的真实反例)

// CORRECT:
// (本项目规避写法，bootstrap 从真实项目补)
```

---

## Rebuild & Performance Traps

<!--
- 哪些写法在本项目造成过过度 rebuild / 卡顿？
- 长列表 / 大图 / 动画踩过什么性能坑？
- 当时是怎么定位和修复的？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Async & Lifecycle Leaks

<!--
- 未取消的订阅 / 定时器 / Future 导致过什么问题？
- setState after dispose 之类的崩溃出现在哪些场景？
- 本项目的兜底约定是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (生命周期泄漏 / dispose 后回调的真实反例)

// CORRECT:
// (本项目正确释放与守卫写法)
```

---

## Layout & Overflow Gotchas

<!--
- 常见的 overflow / unbounded constraints 报错出现在哪些布局组合？
- 键盘弹出、安全区、不同屏幕尺寸踩过什么坑？
- 规避这些布局问题的约定是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Lessons Learned

<!--
- 把上面这些坑沉淀成几条「以后必须这样做」的硬规则。
- 哪些坑已经通过 lint / 封装 / review 清单永久消除？
- 还有哪些是「目前只能靠人记住」的？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
