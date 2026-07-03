# 允许用户覆盖 Guru 风险路由建议

## Goal

风险识别只输出推荐路线；用户明确选择 `lite` / `full` / `micro` / 其他受支持模式时必须允许覆盖，并把推荐路线、实际路线、风险确认和用户 quote 写入 gate contract。Gate 按实际选择执行，不能因推荐 `full_chain` 强制阻断 `lite_task` 或其他用户选择的有效路线。

本任务修正上一轮 risk-based routing 的核心语义：风险系统负责告知和记录风险，不拥有最终路线选择权。用户拥有执行模式选择权；系统只能在选择风险更高时提示后果、要求留下可追溯确认，并在后续执行中按已确认的 selected route 运行。

## Current Evidence

- 现有 `.trellis/spec/cli/backend/guru-overlay-gates.md` 仍规定 high-risk non-full route 要 block，并写有 `init-contract --risk high --route lite_task|micro_task` 要 block。
- 现有 `packages/cli/src/templates/guru/overlay/verify/guru_contract.py` 的 `validate_contract()` 会拒绝 `risk=high` 且 `route!=full_chain`，也会拒绝 `risk=high` + `lite_task`。
- 现有 `guru_gate.py` 的 review policy 会在 high + non-full contract 时退回 strict default，导致 route-aware lite policy 不生效。
- 现有 commit/scope path gate 会在 non-full route 命中 high-risk staged paths 时 block。
- 现有 `guru_after_create.py` 对新 Guru task 默认写 `guru_chain=full` 和 `gate-contract route=full_chain`，文案为 fail-safe full_chain；这会让用户的低成本路线选择无法成为一等合同。
- 已观察到真实会话 `019f22b1-2bb9-7651-a6e3-5caa67e35074` 中，系统识别 high/full 后拒绝按 `lite_task` 推进。用户明确纠正：不能强制走 full，所有模式都是建议；识别 full 后用户说走 lite 或其他模式也要允许。

## Requirements

### REQ-001 Recommendation and Selection Must Be Separate

系统必须区分：

- `recommended_route`: 风险识别推荐路线，例如 `full_chain`。
- `selected_route`: 实际执行路线，以用户显式选择或默认策略决定。
- `risk`: 风险识别结果，仍可为 `low | medium | high | unknown`。

`risk=high` 不得再自动等价于 `selected_route=full_chain`。高风险只影响推荐、提示、审计和后续验证强度，不得覆盖用户选择。

### REQ-002 User Override Is Valid Policy, Not Degradation Evidence

当用户明确说“走 lite”“按 micro”“不要 full”“直接小任务”等路线选择时，系统必须允许把 `selected_route` 写成用户选择的有效路线。

这类选择不是 `gate-degradations.jsonl` 的工具失败降级，不需要伪造为 degradation row。它应写入 `gate-contract.json` 的 route selection / override 审计字段，作为任务合同的一部分。

### REQ-003 High-Risk Override Must Be Auditable

当 `recommended_route` 比 `selected_route` 更严格时，合同必须记录：

- `override.enabled=true`
- `override.from_route`
- `override.to_route`
- `override.by=user`
- `override.user_quote`
- `override.acknowledged_risk=true`
- `override.created_at`
- `assessment.reasons` / `assessment.risk_flags` 保留原始风险识别证据

若没有用户 quote 或没有明确风险确认，系统可以停下要求确认；但确认后不得继续以 high/full 推荐阻断 selected route。

### REQ-004 Gates Must Execute Selected Route

`requirements` / `overview` / `detail` / `check-implementation` / `check-commit` / `commit-plan` / `slice-plan` 必须按 `selected_route` 判定路线策略。

示例：

- high-risk + selected `lite_task`：使用 `lite_task` bounded review policy，不强制 full-chain slice packet，不因 high/full 推荐而要求 `PACKET_REQUIRED_BEFORE_IMPLEMENT`。
- high-risk + selected `micro_task`：允许合同创建和 commit preflight 进入 micro 口径，但仍执行 micro 的显式 scope、`max_files`、staged path、deterministic checks 和风险提示要求。
- selected `full_chain`：保持 full-chain strict gate，不因存在 override 字段而削弱。

### REQ-005 Unsupported Modes Still Fail Structurally

用户只能选择系统支持的路线枚举：`small_inline | micro_task | lite_task | full_chain`。不支持的 route 字符串、风险 typo、合同 JSON 损坏、缺少必要 scope 字段等结构错误仍必须 fail closed。

`small_inline` 仍不是 commit contract；如果用户选择 small inline 后要提交代码，系统应提示升级为 `micro_task` 或生成 commit-capable contract，而不是把 `small_inline` 直接写成 commit contract。

### REQ-006 Path/Risk Signals Become Warnings Unless Scope Contract Is Violated

non-full selected route 命中 high-risk path signals 时，不得仅因“高风险路径”本身 block。只有以下情况才应 block：

- staged paths 超出 `scope.allowed_paths`
- staged file count 超过 `scope.max_files`
- 命中 `scope.forbidden_path_patterns`
- 缺少 selected route 要求的 review / deterministic checks / user confirmation
- 当前 review evidence 有 blocked / malformed / medium+ finding
- 合同缺失、损坏或 override audit 缺失

高风险路径命中应进入 warning / commit-plan reason / review prompt，但不能覆盖用户已确认的 `selected_route`。

### REQ-007 Source, Template, Spec, and Tests Must Stay Mirrored

实现必须同时更新 source template 与 dogfood template：

- `packages/cli/src/templates/guru/overlay/**`
- `guru-template/overlay/**`
- `.trellis/spec/cli/backend/guru-overlay-gates.md`

测试必须覆盖 source/template mirror 对齐，不允许只改本地 dogfood 文件。

## Acceptance Criteria

- [ ] `guru_gate.py init-contract --risk high --route lite_task` 能成功写合同，且合同保留 `risk=high`、`recommended_route=full_chain` 或等价推荐字段、`route/selected_route=lite_task`、用户 override 审计字段。
- [ ] `guru_gate.py init-contract --risk high --route micro_task` 在提供 micro 必需 scope/max_files 和用户 override 审计时能成功；缺少 micro scope/max_files 仍失败。
- [ ] `risk=high + selected_route=lite_task` 的 review policy 返回 lite bounded policy，而不是 strict full_chain/default policy。
- [ ] `risk=high + selected_route=lite_task` 的 `check-implementation` 不要求 full-chain slice packet。
- [ ] `risk=high + selected_route=full_chain` 仍要求 full-chain strict gate；缺 slice packet 仍以 `PACKET_REQUIRED_BEFORE_IMPLEMENT` 阻断。
- [ ] `check-commit` / `commit-plan` 对 high-risk non-full override 不再因 high-risk path signal 本身阻断，但仍阻断 out-of-scope、max_files、forbidden pattern、task artifacts、缺 review/确认等 selected route 本身的 gate 问题。
- [ ] `guru_after_create.py` 不再把 default full_chain 描述为不可降级；默认可保持 conservative recommendation，但必须允许后续用户选择覆盖为 micro/lite。
- [ ] `client-small-iteration-dev` skill 文案删除“强制完整五阶段”“不得降级”语义，改为“推荐 full，用户可覆盖，覆盖需记录风险确认”。
- [ ] `.trellis/spec/cli/backend/guru-overlay-gates.md` 的 Signature / Contract / Error Matrix / Tests Required 同步改为 recommendation vs selected route 语义。
- [ ] `guru-template/overlay/verify/tests/run_tests.sh` 新增或调整覆盖 high/full recommendation 被用户选择 lite/micro 后允许的正例，以及缺少 override audit 的反例。
- [ ] Source/template mirror pairs 通过 diff check。

## Brainstorm Evidence

- Skill loaded: `trellis-start`, `trellis-meta`, `trellis-brainstorm`
- Repository evidence inspected:
  - `.trellis/spec/cli/backend/guru-overlay-gates.md`
  - `.trellis/tasks/07-01-risk-based-gate-contract-routing/prd.md`
  - `.trellis/tasks/07-01-risk-based-gate-contract-routing/design.md`
  - `packages/cli/src/templates/guru/overlay/verify/guru_contract.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_gate.py`
  - `packages/cli/src/templates/guru/overlay/verify/guru_risk.py`
  - `packages/cli/src/templates/guru/overlay/hooks/guru_after_create.py`
  - `packages/cli/src/templates/guru/overlay/agents-skills/client-small-iteration-dev/SKILL.md`
  - matching `guru-template/overlay/**` files
  - `packages/cli/src/templates/guru/overlay/verify/tests/run_tests.sh`
- Domain/terminology triggers: 触发。`risk` 是系统识别结果，`recommended_route` 是建议路线，`selected_route` 是执行合同，`override` 是用户路线选择审计；这四者必须分离，不能继续用 `risk=high` 推导唯一 route。
- Current code vs user intent conflicts:
  - 当前合同校验把 high-risk non-full route 当作 invalid contract。
  - 当前 review policy 对 high-risk non-full contract 回退 strict full_chain。
  - 当前 commit/scope gate 对 non-full high-risk staged path 直接 block。
  - 当前 skill/spec 文案把 high -> full_chain 写成强制。
  - 用户明确要求所有模式都是建议，识别 full 后也必须允许用户选择 lite 或其他模式。
- Product decisions confirmed:
  - DEC-001: 路由识别结果只能作为推荐，不能强制 full。
    - confirmed_ref: 用户当前轮明确说“不能强制走 full，所有的模式都是建议，如果识别出是 full 用户如果说走 lite 或者其他模式也要允许。”
  - DEC-002: 用户 override 需要允许，但要记录风险和用户 quote。
    - confirmed_ref: 前一轮方案已给出 `recommended_route` / `selected_route` / `override.user_quote`，用户回复“好”同意创建任务固化。
- Open product/scope/risk questions: 无阻塞问题。`其他模式` 解释为当前 Guru 支持的 route enum；`small_inline` 保持 non-commit 模式，提交时仍需 micro 或更高合同。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
