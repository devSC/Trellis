---
name: ios-small-iteration-dev
description: iOS 小需求端到端闭环编排：按需求清晰度、风险、耦合、可逆性和验证成本选择 small_inline / micro_task / lite_task / full_chain；Lite 使用标准 Trellis task 和一次需求确认，高风险必须 Full。本 Skill 只编排流程，规范以项目 golden-path 和平台标准包为准。
---

# iOS 小迭代闭环

## 装载顺序

1. 读取 `.trellis/spec/guides/golden-path.md` 与项目约定。
2. 根据涉及的 domain/repository/usecase/viewmodel/view/coordinator/external 层读取对应规范。
3. 先查仓库代码、测试和文档证据，再决定是否存在用户必须回答的问题。

## 四级路由

- `small_inline`：机械、明确、低风险且不改变行为合同；默认无完整 task、确认 0、Worker 0。初始要求 commit 时只补最小提交合同。
- `micro_task`：明确、低风险、路径有界的局部行为改变；最小 task contract、确认 0、focused check。
- `lite_task`：无 High-risk 的局部功能，但 repo evidence 后仍可能有产品/范围/验收歧义；官方 `task.py create` 标准任务、task-local compact `prd.md`、必要时 bounded Brainstorm、确认一次、Worker 0、无 Overview/Detail planning review。
- `full_chain`：跨层、持久化、权限/隐私、支付、迁移、公共契约、workflow/hook/gate/runtime 或发布风险；实现前完成 current risk/decision evidence 与一批用户确认，使用 guarded activation。

## Route 选择与切换

- 自动选择满足硬边界的最低成本 Route；`gate-contract.json` 记录 selected/recommended Route、`selection_source`、`selection_generation` 与 `scope_fingerprint`。
- 用户选择更重 Route 直接允许；选择更轻 Route 必须满足目标 eligibility；High-risk/unknown-high 不得降级。
- 首次写入前可基于新证据合法降级；首次写入后只允许升级。Lite 发现 scope expansion 或 High-risk 时，在下一次写入前升级 Full。

## Lite 自动闭环

官方创建标准任务后，先查 repo evidence；只对真实产品/范围/失败路径/验收歧义进入 bounded Brainstorm。把 compact requirements 与 Brainstorm Evidence 写入 task-local `prd.md`，用户确认当前 digest 后自动 start、host-inline 实现、focused `swift build`/`swift test`、mutable evidence、Spec 同步和可逆 commit-ready，不再逐步询问。

确认预算固定为 Small/Micro/Lite/Full=`0/0/1/1 batch`。Lite/Full 确认后自动推进；只有 scope/digest 实质变化、新 High-risk 或新不可逆决定才允许重新确认。全程不得调用 Claude。
