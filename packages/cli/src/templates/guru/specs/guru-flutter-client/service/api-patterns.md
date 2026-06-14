# API Patterns

> 本项目网络层（`@RestApi`/Dio）与契约组织的真实约定。

---

## Overview

<!--
- 网络层用什么栈（retrofit `@RestApi` + Dio / 纯 Dio / 其他）？
- API 客户端放在哪一层、如何命名（如 `XxxApi`、放在 `data/api/`）？
- base url / 环境切换在哪里配置？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## RestApi / Dio Setup

<!--
- `@RestApi` 接口如何声明？代码生成（retrofit/build_runner）的约定是什么？
- Dio 实例如何创建与共享？是否单例？见 dependency-injection.md。
- 超时/重试/baseOptions 的统一配置在哪里？
-->

```dart
// WRONG: <在此放本项目实际禁止的 Dio/RestApi 声明写法>

// CORRECT: <在此放本项目实际推荐的 Dio/RestApi 声明写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Interceptors & Headers

<!--
- 拦截器（鉴权 token、日志、错误转换）如何注册与排序？
- 公共 header（token / 版本 / 语言）在哪里统一注入？
- 日志拦截器与结构化日志的关系见 logging.md。
-->

```dart
// WRONG: <在此放本项目实际禁止的拦截器/header 写法>

// CORRECT: <在此放本项目实际推荐的拦截器/header 写法>
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Contract Organization

<!--
- 请求/响应 DTO 如何组织（按模块 / 按接口）？放在哪个目录？
- 接口契约（路径常量、API 定义、模型）如何分文件？
- 与后端契约的同步方式是什么（手写 / 代码生成 / OpenAPI）？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在网络层踩过的坑（如散落多个 Dio 实例、header 漏注入、契约与后端漂移等） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
