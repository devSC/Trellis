# L2 类型规范：controller（页面状态容器）

> 从属于 L1 `detail-structure-single-source.md`；本文件只写 controller 类型的差异规则，冲突以 L1 为准。
> golden-path 对应：§6 Presentation 迷你路径、§2.3 DI、§2.5 边界。

## 适用对象

页面级 / widget 级状态容器（基类 `LifecycleController`）。不适用：无状态展示 widget（归 page-entry）、业务流程（归 usecase）。

## 合同八问的类型特化

1. **承接行为**：本页面的用户操作与生命周期事件（引用概要行为编号）。
2. **输入/输出/错误**：
   - 输入 = 路由入参 + 订阅的 usecase 流 + 用户事件。
   - 输出 = 状态字段全集（**必须逐字段列表**：名称 / 类型 / 初始值 / 写入时机）+ 对外暴露的命令方法签名。
   - 错误 = 三态收口：每个异步状态字段必须定义 loading / empty(或 success) / error 三态的展示去向。
3. **读写状态**：本 controller 是其状态字段的唯一写 owner；订阅的 usecase 流只读。**禁止两个 controller 写同一份业务状态**（业务状态归 usecase）。
4. **依赖**：只注入 usecase / service 接口（构造注入）。**不调用**：repository 实现、DAO、API 类、其他 controller（违反分层律，P1）。
5. **失败收口**：每条失败路径 → error 态字段 + 用户可见反馈（toast/占位/重试入口），错误转换遵循 `[SLOT-04]`。
6. **事件/后置**：埋点事件清单（事件名 + 触发时机 + 参数）；导航动作（去哪个 RoutePath、带什么参数）。
7. **测试映射**：事件→状态转移 = unit test（mock usecase，框架按 `[SLOT-14]`）；生命周期行为 = unit test 覆盖 onReady/onClose；不在此层测 UI 结构（归 widget test）。
8. **不得补造**：不发明业务规则（属 usecase）；不决定缓存/持久化（属 repository）；不直接操纵其他页面状态。

## 类型硬规则

- 基类一律 `LifecycleController`（gurusdk），`static tag` 必须定义。
- `@injectable` + binding `Get.lazyPut(() => Injector.provide<C>(), tag: C.tag)`（canonical，见 golden-path §2.3）。
- 订阅在 `onClose`/生命周期收口处必须取消（流泄漏 = P1）。
- 超过约 300 行考虑按职责域抽 mixin（指南）；mixin 间不共享 `final` 字段。
- design model 消费形态按 `[SLOT-05]`。

## 好 / 坏例子（要点）

- ✅ 好：状态字段表完整（`isLoading: RxBool = false，sendMessage() 置 true，流回包置 false`）；每个异步动作三态齐全；依赖只有 `IChatUseCase`。
- ❌ 坏：「管理聊天相关状态」一句话带过（无字段表）；注入 `ChatRepositoryImpl`；error 态"待定"；把 IceLevel 类业务判定写进 controller。
