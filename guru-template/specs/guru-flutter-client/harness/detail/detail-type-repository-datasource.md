# L2 类型规范：repository-datasource（数据访问合同）

> 从属于 L1 `detail-structure-single-source.md`；本文件只写 repository + datasource 类型的差异规则。
> golden-path 对应：§4 Data 迷你路径、§5 Network、§2.1 分层律。

## 适用对象

repository（数据访问合约 + local/remote 编排）与其下 datasource（单一数据来源适配）。DAO/表结构与 @RestApi 定义分别归 `db-dao` / `api-network` 类型（v1 暂按 L1 八问展开）。

## 合同八问的类型特化

1. **承接行为**：数据读写、缓存、同步类行为（引用概要行为编号）。
2. **输入/输出/错误**：
   - repository 接口逐方法签名；返回域模型（不泄漏 DTO/数据库行模型给上层——mapper 责任在此声明）。
   - datasource 接口逐方法签名（local/remote 分别列）。
   - 错误 = 底层异常到业务错误的映射表（`DioException.connectionTimeout → ClientNetworkError` 这一级别的明细）。
3. **读写状态**：管理的缓存/持久化状态清单；幂等性声明（重复调用的语义）。
4. **依赖**：repository **只注入 datasource 接口**（必经 datasource，通用硬规则——直连 DAO/API = P1）；datasource 只注入 DAO / API 类。**不调用**：usecase（反向依赖 = P1）、controller、其他 repository。
5. **失败收口**：**编排策略必须显式**——remote 失败是否回落 local、缓存过期策略、离线写入队列与冲突合并；错误转换位置遵循 `[SLOT-04]`（datasource/api 层不吞异常，必须上抛——通用硬规则）。
6. **事件/后置**：数据变更通知方式（返回值 / 流 / 由 usecase 轮询）。
7. **测试映射**：编排逻辑（回落/合并/幂等）= unit test（mock datasource）；datasource = unit test（mock DAO/API）或集成测试（真实 DB，按 `[SLOT-14]`）；错误映射表逐条有用例。
8. **不得补造**：不实现业务规则（属 usecase）；不新增概要未定的表/接口（回概要技术决策承接）；不在此决定 UI 错误文案。

## 类型硬规则

- 接口在 domain 侧、实现在 data 侧（目录按 `[SLOT-11]`）；接口实现分文件（命名按 `[SLOT-03]`）；`@LazySingleton(as: <接口>)`。
- mapper 必须独立声明（DTO/行模型 ↔ 域模型的转换归属），序列化方案按 `[SLOT-01]`。
- DB 版本迁移涉及时：引用 `[SLOT-06]` 的 helper 与版本字段，迁移分支写进合同（升级路径 + 兜底）。

## 好 / 坏例子（要点）

- ✅ 好：`all()` 合同写明"先 local，remote 成功后写回 local 并发射新值；remote 失败返回 local + 标记 stale"；错误映射表逐条；依赖仅 `IRecipeLocalDataSource` + `IRecipeRemoteDataSource`。
- ❌ 坏：「负责菜谱数据」（无编排策略）；构造函数注入 `AppApiMethods`（绕过 datasource）；catch 后返回空列表不区分"无数据"与"出错"（吞错）。
