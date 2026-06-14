# Navigation

> 本项目路由注册位置与页面跳转约定。

---

## Route Registration

<!--
- 路由方案是什么（Navigator 1.0 / go_router / auto_route / 自研）？
- 路由表 / 路由配置的真实文件位置在哪里？
- 新增一个页面，需要在哪里注册、注册成什么形式？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (路由注册位置 / 命名不符约定的反例)

// CORRECT:
// (按本项目约定注册路由的正例)
```

---

## Navigation Conventions

<!--
- 跳转用什么 API（push / pushNamed / context.go / 封装方法）？
- 是否禁止裸用 Navigator？必须走哪个封装入口？
- 返回 / 替换 / 清栈等场景分别怎么写？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```dart
// WRONG:
// (绕过封装裸跳转的反例，bootstrap 从真实项目补)

// CORRECT:
// (走本项目统一跳转入口的正例)
```

---

## Passing Arguments

<!--
- 页面间传参用什么方式（构造参数 / 路由 extra / 注入）？是否类型安全？
- 复杂对象怎么传，怎么避免传 dynamic / Map？
- 必传参数缺失如何被尽早发现？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Deep Links & Guards

<!--
- 是否支持 deep link / 外部唤起？落在哪里处理？
- 登录态 / 权限拦截（route guard）在哪里实现？
- 重定向规则的真实约定是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!--
- 本项目导航最常踩的坑有哪些（context 失效 / 重复 push / 栈错乱）？
- 哪些是 review 反复打回的跳转写法？
- 每条对应正确做法是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
