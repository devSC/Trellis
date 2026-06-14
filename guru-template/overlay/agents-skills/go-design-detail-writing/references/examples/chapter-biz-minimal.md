# 示例：chapters/user-month-plan-service.md（缩减成稿样例 · biz 类）

> **成稿形态示例**：一个中性 worked example——通用 `UserService` 的月度套餐
> （month_plan）业务流，演示 `detail_doc_type=biz` 章节的完整形态与可编码粒度；**不是规则来源**，也不绑定任何具体参考仓库。
> 完整模板与逐节要求见 `../chapter-guide.md` §2，类型差异规则见 `.trellis/spec/harness/detail/detail-type-biz.md`（L2），
> 完成条件见 L1 `detail-structure-single-source.md`。
>
> 文件骨架（先与目标仓库代码现状核对再写，本例字段/签名/sentinel/测试点落在以下对应相对路径）：
> - `internal/service/user_service.go`（`CreateMonthPlan`/`UpdateMonthPlan`、`validateMonthPlanRange`、`validateMonthPlanDoesNotOverlap`）
> - `internal/domain/user.go`（`UserMonthPlan`、`CreateUserMonthPlanParams`、`UpdateUserMonthPlanParams`）
> - `internal/service/errors.go`（`var ErrValidation = errors.New("service: validation failed")`）
> - `internal/repository/errors.go`（`var ErrNotFound = errors.New("repository: not found")`）
> - `internal/service/user_month_plan_service_test.go`（重叠/区间/单字段更新用例与 fake store）

## 要点提示（写作时自查 · 全部对照目标仓库代码现状取证）

1. **行为流程必须能直接编码**——本例 §4.1 流程详述第 3 步写明"调 `repo.ListMonthPlansByUserIDs(ctx, []int64{userID})` 后逐条 `startsAt.Before(plan.EndsAt) && plan.StartsAt.Before(endsAt)` 判重叠"，而不是"检查是否重叠"。重叠算法对照 `validateMonthPlanDoesNotOverlap` 的实现。
2. **错误统一 `%w` 包装 sentinel**——所有校验失败写 `fmt.Errorf("%w: <字段说明>", ErrValidation)`（如 `validateMonthPlanRange`：`starts_at is required` / `ends_at is required` / `month plan starts_at must be before ends_at`）；找不到对应失败路径 BHV 的错误行说明行为枚举有漏，回退概要。
3. **状态/owner 与依赖回指概要归属表行**——`UserMonthPlan` 写 owner=`UserService`；依赖 `userStore`（repo 接口，构造注入）必须能回到归属表的边，审核会做双向核对。Utility 纯函数（如时间封装）直接调用，**不进 `direct_dependencies[]`**。
4. **测试映射覆盖全部失败路径**——成功 1 行 + 失败逐路径各 1 行是底线；本例的「区间非法」「同用户重叠」「不同用户同区间放行」「单字段更新」四点逐一对应 `user_month_plan_service_test.go` 的 `Test...` 函数，全部 `errors.Is(err, ErrValidation)` 断言。
5. **事务边界三选一给结论**——`CreateMonthPlan` 是「读已有套餐做重叠校验 + 单条写」→ 结论 `无显式事务`（重叠判定是只读校验，不需要把读校验与单条写塞进显式事务）；这种「指明三分法结论 + 理由」才可审计。
6. **不得补造清单写"决策属于谁"**——"不决定 month_plan 表的 EXCLUDE 约束与索引（属 repository-data / db/migrations）"这种指向式写法才可审计；落盘约束 `user_month_plans_no_overlap EXCLUDE USING gist (...)` 在迁移层，biz 只声明业务重叠语义，不声明它如何落盘。

## 成稿正文取材锚点（与上列证据一一对应，写作时直接套用 `../chapter-guide.md` §2 模板填充）

- **§2 行为定义**：`CreateMonthPlan(ctx, userID int64, params domain.CreateUserMonthPlanParams) (*domain.UserMonthPlan, error)`、`UpdateMonthPlan(ctx, userID, planID int64, params domain.UpdateUserMonthPlanParams) (*domain.UserMonthPlan, error)`——首参 `ctx`、末位 `error`，签名级完整（见 `user_service.go` 对应方法）。
- **§3.2 sentinel 全集**：业务可恢复 `service.ErrValidation`（handler 映射 400）；关联实体不存在 `repository.ErrNotFound`（`UpdateMonthPlan` 内 `repo.GetMonthPlan` 命中，handler 映射 404）。
- **§4 逐行为**：`CreateMonthPlan` = ① `userID <= 0` → `%w ErrValidation`；② `validateMonthPlanRange(StartsAt, EndsAt)`（非零 + `StartsAt.Before(EndsAt)`）；③ `validateMonthPlanDoesNotOverlap`（读已有套餐逐条比较）；④ `repo.CreateMonthPlan`。
- **§5 状态与事务**：`user_month_plans` 业务重叠语义写 owner=`UserService`；事务边界=`无显式事务`（只读校验 + 单条写）。
- **§7 测试映射**：`TestUserServiceCreateMonthPlanRejectsInvalidRange`、`...RejectsOverlapForSameUser`、`...AllowsSameRangeForDifferentUsers`、`TestUserServiceUpdateMonthPlanSupportsSingleFieldChange`、`...RejectsOverlap`——全部用 `newFakeUserMonthPlanStore()` 注入 fake repo（accept interfaces 惯例），无真实 DB。

为避免双份样例漂移，成稿正文请直接参考 `../chapter-guide.md` §2 的完整模板示例（同为 `UserService` 素材，已含 §1~§8 全节与 `sequenceDiagram`/参数表/异常表/测试映射的填充形态）；本文件只提供针对月度套餐这一真实单元的取材锚点与自查清单，不重复贴出整章正文。
