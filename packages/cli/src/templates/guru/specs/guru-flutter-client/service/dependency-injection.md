# Dependency Injection

> 本项目 DI 入口与注册约定的真实写法。

---

## Overview

<!--
- 本项目用什么 DI 方案（get_it / injectable / riverpod / provider / 手写工厂）？
- DI 容器在哪里初始化、何时初始化（main 启动阶段）？
- service 层的对象（usecase/repository/datasource/Dio）如何被装配？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Registration Conventions

<!--
- 各类对象用什么生命周期注册（singleton / lazySingleton / factory）？约定是什么？
- 注册代码组织在哪里（按模块 / 集中一个文件 / 代码生成）？
- 注册顺序与依赖关系如何保证（先 Dio 后 api 后 repository）？
-->

```dart
// WRONG: <在此放本项目实际禁止的注册写法（如错误的生命周期）>

// CORRECT: <在此放本项目实际推荐的注册写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Resolution & Injection

<!--
- 对象在何处被取出/注入（构造注入 vs 全局容器读取）？
- 哪些层允许直接访问容器，哪些层必须构造注入？
- usecase / repository 的依赖如何穿透注入？见 usecase-pattern.md。
-->

```dart
// WRONG: <在此放本项目实际禁止的解析/获取写法（如到处 service locator 直取）>

// CORRECT: <在此放本项目实际推荐的解析/注入写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Scopes & Lifecycle

<!--
- 是否存在按页面/会话/登录态划分的作用域？如何创建与销毁？
- 登出/切环境时哪些注册需要重置？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在 DI 上踩过的坑（如循环依赖、单例被误注册为 factory、容器在 UI 层滥用等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
