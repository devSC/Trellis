# L2 类型规范：usecase（业务流程编排）

> 从属于 L1 `detail-structure-single-source.md`；本文件只写 usecase 类型的差异规则。
> golden-path 对应：§3 Domain 迷你路径、§2.1 分层律、§2.5 边界。

## 适用对象

有状态业务流程 + 响应式流的 owner。不适用：无状态转换（归 service）、数据访问编排（归 repository）。

## 合同八问的类型特化

1. **承接行为**：业务规则与状态变化类行为（引用概要行为编号）；每条行为映射到一个公开方法或流。
2. **输入/输出/错误**：
   - 接口全集：**逐方法签名级**列出（方法名 / 参数 / 返回类型）；维护的流逐条列出（流名 / 元素类型 / seed / 发射时机）。
   - 错误 = 业务错误枚举（哪些可恢复、哪些上抛给 controller）。
3. **读写状态**：本 usecase 拥有的业务状态清单（唯一写 owner）；声明哪些状态对 controller 只读暴露（经流）。
4. **依赖**：注入 repository / service 接口；**允许单向注入其他 usecase 接口（禁止环与双向，golden-path v2 §2.1）**——若依赖其他 usecase，必须在合同中声明方向并说明为何不下沉。**不调用**：datasource、DAO、API、controller、UI。
5. **失败收口**：每个公开方法的失败语义（返回错误 / 流发射 error / 静默降级），与 `[SLOT-04]` 错误收口位置一致。
6. **事件/后置**：流发射时序（什么操作后哪些流必然发射）；跨 usecase 通知（如有）。
7. **测试映射**：业务规则与状态转移 = unit test（mock repository/service）；流时序 = unit test（expectLater 流断言）。**usecase 是测试密度最高的层**：每条承接行为至少 1 成功 + 1 失败用例。
8. **不得补造**：不决定 UI 展示与文案；不决定存储介质与缓存策略（属 repository 合同）；不在未确认的业务规则上拍板（列入未决问题回需求/概要）。

## 类型硬规则

- 接口与实现分文件（命名按 `[SLOT-03]`）；`@LazySingleton(as: <接口>)`。
- 流的生命周期：声明谁创建、谁关闭（dispose 责任）；`BehaviorSubject` 必须有关闭点。
- 状态唯一写 owner：同一业务状态出现在两个 usecase 的合同里 = P1（回概要重判归属）。

## 好 / 坏例子（要点）

- ✅ 好：`Stream<List<Recipe>> observeRecipes()`（seed: 空表，saveRecipe 成功后发射新列表）；错误枚举 `RecipeSaveError{quotaExceeded, persistFailed}`；依赖声明"注入 IRecipeRepository；不注入其他 usecase"。
- ❌ 坏：方法清单"提供菜谱相关能力"（无签名）；流"按需发射"（无时序）；同时写 `IInventoryUseCase` 也维护的库存余额（双写）。
