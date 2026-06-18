---
name: design-grill
description: 兼容用 Guru 对抗式拷问会话。新流程的 Domain Grill 已前移到 trellis-brainstorm；本 skill 只用于旧任务兼容审计或用户显式要求的额外深挖，不作为 requirements、overview 或 detail 的 Guru Gate 前置条件，不替代 brainstorm、writing、review 或 trellis-check。
---

# design-grill — compatibility-only 对抗式拷问

## 做什么

对当前 task 产物发起 compatibility-only 的对抗式拷问：需求侧拷问 `prd.md` 的行为集合；概要侧拷问 `design.md` 或 `design-main.md` 的归属表、三问理由与承接索引；详细侧拷问可编码合同、失败收口、测试映射和不得补造声明。沿设计树逐分支推进，决策间依赖逐个解开，每个归属判定都必须经得起"为什么属于它 / 为什么不属于别人 / 为什么需要或不需要独立存在"三问。

- 默认先输出一个有界 **Design Grill Packet**，批量暴露多个问题/建议；每个 packet 默认不超过 8 个候选项。
- 独立、低风险的 `NORMAL` 项允许用户批量批准；`BLOCKER`、红线、合规、会设定依赖顺序的决策仍必须逐项确认。
- 能从代码或 spec 找到答案的问题不要问用户，先自己读取证据。
- 本 skill 不从零生成需求或设计，不给正式 Gate 结论；它只在用户显式要求、旧任务迁移或兼容审计时磨稿、排雷、回写决策。
- 新流程的 Domain Grill 归属于 `trellis-brainstorm` 需求发现阶段；不要把本 skill 当作 requirements / overview / detail 的放行前置。
- `guru_gate.py check` / `auto` 不依赖本 skill；overview / detail 的放行凭据来自 `record-review`，requirements / detail 的硬边界来自人类 `confirm`。

## 拷问对照物

先做适用域门控，再装载领域模型。门控三态：

1. **非 guru 布局**：找不到 `.trellis/spec/guides/golden-path.md`，说明当前仓库不是 guru 领域模型布局。输出"design-grill 不适用当前布局"并退出，不降级成普通聊天式拷问。
2. **guru 但项目约定未就绪**：能找到 guru golden-path，但 `.trellis/spec/conventions/project-conventions.md` 缺失，或只存在 `*.template.md` / 样例文件而没有当前项目取值。阻断并提示"先完成项目约定"，列出应按 conventions index 完成的校验项，不继续拷问。
3. **guru 且约定就绪**：继续读取下列权威源，生成本端"拷问清单摘要"后再提第一个问题。

运行时必须读取并确认：

- `.trellis/spec/guides/golden-path.md`：分层依赖律、硬红线、禁止清单。
- `.trellis/spec/conventions/project-conventions.md`：当前项目取值、存量违例清单、校验清单结果。`project-conventions.template.md` 和样例文件只能作为修复提示，不能作为有效取值。
- `.trellis/spec/harness/gate/gate-confirmation-model.md`：Gate 凭据模型、digest 覆盖范围与失配恢复流程。
- 当前任务产物：`prd.md`、`design.md`、`task.json`，以及 full 链的 `design_package` / `design-main.md` / `chapters/`（存在时）。
- 术语与决策上下文：仓库根 `CONTEXT.md` 或 `CONTEXT-MAP.md`、`docs/adr/`（存在时）。
- 目标仓库真实代码：按 project-conventions 和当前设计表里的 owner / 路径线索使用 `rg` 定位；找到证据后再引用。

权威源选择与冲突处理：

- Go / H5 的归属与承接类型口径只取 `.trellis/spec/harness/overview/overview-structure-single-source.md`。
- iOS 的归属与承接类型口径只取 `.trellis/spec/conventions/index.md` 的第 5 节。
- Flutter / client 的归属判定与详细承接口径取 `.trellis/spec/harness/overview/overview-structure-single-source.md`。
- `.trellis/spec/conventions/index.md` 对 Go / H5 只用于 project-conventions 校验规则，不作为归属与承接类型的第二来源。
- 如发现锚点漂移或路径冲突（例如某 conventions index 声明项目约定在 `harness/conventions/`，但实际安装落位在 `conventions/`），立即 fail 报告冲突源、冲突路径和人工修复动作；不要"都读一遍"后混合口径。

拷问前必须先输出一段**本端拷问清单摘要**，至少包含：

- 已装载的权威源和 readiness 结论。
- 本端硬红线摘要。
- 本端边界场景与唯一 owner / 失败收口 / 并发或跨边界探针。
- 本端代码交叉核对锚点（写出实际找到的路径或说明未找到）。
- 本端 ADR 触发例型。

## Design Grill Packet

完成适用域门控、权威源读取和本端拷问清单摘要后，先输出一个 **Design Grill Packet**。Packet 是交互提速器，不是 Gate 凭据；它只能帮助用户批量处理独立低风险项，不能替代 review、confirm、`record-review` 或 `guru_gate.py status`。

Packet 约束：

- 默认最多列 8 个候选项；若问题更多，先列风险最高和依赖最靠前的项，并说明剩余类别。
- 每个项必须包含：
  - `ID`：稳定短编号，如 `DG-001`。
  - `artifact_anchor`：产物锚点，例如 `BHV-003`、表格行、章节标题、承接索引项或代码路径。
  - `risk`：`BLOCKER` / `HIGH` / `NORMAL`。
  - `question_or_challenge`：要用户裁定的问题或对当前写法的挑战。
  - `recommended_answer`：你的推荐答案或推荐修法。
  - `evidence`：已读取的 spec、task artifact、ADR、CONTEXT 或代码证据。
  - `write_back_target`：确认后应最小回写到哪个文件/章节/表格。
  - `dependency_status`：`independent` / `depends_on:<ID>` / `blocks:<ID>` / `sequential_required`。
- `NORMAL + independent` 项可以让用户用一句话批量批准，例如"批准 DG-003、DG-004、DG-006"。
- `BLOCKER`、红线、合规 STOP、`HIGH` 且会改变 owner/依赖/范围的项，必须一项一问，等用户确认后再推进下一项。
- 发现 packet 内项目相互矛盾时，不允许批量批准；先把冲突项拆成顺序确认路径。
- 用户确认后只回写最小必要决策；未确认的推荐答案不能写成既定结论。

推荐输出形态：

```markdown
## Design Grill Packet

| ID | Anchor | Risk | Question / challenge | Recommended answer | Evidence | Write-back target | Dependency |
|----|--------|------|----------------------|--------------------|----------|-------------------|------------|
| DG-001 | BHV-003 | BLOCKER | ... | ... | ... | prd.md / BHV-003 | sequential_required |
| DG-002 | design-main.md owner row | NORMAL | ... | ... | ... | design-main.md | independent |

可批量批准：DG-002, DG-005
必须逐项确认：DG-001（BLOCKER）, DG-004（依赖设定）
```

Durable 状态约束：

- Gate 凭据模型、digest 覆盖范围与失配恢复流程以 `.trellis/spec/harness/gate/gate-confirmation-model.md` 为准；本 skill 只定义拷问会话执行方式。
- Packet 文本、聊天确认、手写 marker、`grill-done` 和 `grill-skip` 都不是新模型的 Gate 凭据。
- `python3 .trellis/scripts/guru/guru_gate.py grill-done <gate> <task_dir>` 和 `grill-skip` 仅保留为旧任务兼容审计记录；如果用户没有显式要求维护旧记录，不要把它们列为下一步命令。
- 兼容记录写入的 digest 或 policy 失配后，只说明旧记录过期；不要要求为了新模型放行而重跑本 skill。
- 新模型下一步只能是按当前阶段运行 brainstorm / writing / review、`record-review`、`confirm requirements`、`confirm detail` 或 `guru_gate.py status`。

## 收口输出

每次会话结束必须输出一个 **Design Grill Result**，方便用户判断建议修订；输出必须标明 compatibility-only，且不得把 `grill-done` / `grill-skip` 作为新模型的放行命令：

```markdown
## Design Grill Result

- Gate: requirements | overview | detail
- Policy: compatibility-only
- Risk Level: low | high | unknown
- Risk Reasons: ...
- Result: passed | blocked | needs-revision | advisory-only
- Written Back: yes | no
- Next Step: trellis-brainstorm | platform writing skill | platform review skill | guru_gate.py status | record-review | confirm requirements | confirm detail
```

规则：

- `Policy` 固定为 `compatibility-only`；不得输出 `required` / `skippable` 作为新 Gate 策略。
- 若用户显式要求维护旧记录，可附加一行 `Legacy Record: grill-done ...` 或 `Legacy Record: grill-skip ...`，并说明这只用于旧审计，不会放行新模型 Gate。
- 如果拷问中发现当前 low-risk 判断过低，只能建议回写 task 风险原因并重新走 brainstorm / review，不得要求为了放行而走 `grill-done`。

## 会话六动作

1. **对照术语表挑战**：用语与 `CONTEXT.md` / `CONTEXT-MAP.md` 既有定义冲突时立即点破；术语未入表且属于领域概念时，要求当场裁定。
2. **磨尖模糊语言**：遇到含混、过载、名词先行或跨平台串台的说法，给出精确候选和你推荐的收口方式；行为标题同步收窄到可实现、可验证的粒度。
3. **具体场景压测**：发明边界场景，逼出唯一写 owner、失败路径、并发/生命周期/跨边界责任、数据读写归属和回滚/补偿策略。
4. **与代码交叉核对**：把用户陈述、prd/design 草稿与目标仓库现状对照；有矛盾时给出具体文件或符号证据，再问用户以哪个为准。
5. **逐行归属拷问**：概要阶段按行为或状态逐行核对 owner、三问理由、承接索引与本端硬红线；不能用下游详细设计补造上游归属缺陷。
6. **节奏控制**：先用 Design Grill Packet 暴露候选项；独立 `NORMAL` 项可批量批准，`BLOCKER` / 红线 / 合规 / 依赖设定项逐项推进。红线命中时停止该分支；普通歧义给推荐答案并等待用户确认。

## 决策四去向

- 行为、范围、失败路径、验收场景决策 → 回写 `prd.md`，把未决问题改成已决并附一句依据。
- 归属、owner、承接索引、三问理由决策 → 回写 `design.md` / `design-main.md` 的对应表格或章节。
- 纯领域术语和歧义裁定 → 回写 `CONTEXT.md`，或按 `CONTEXT-MAP.md` 定位到对应 context。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。
- 难以回头、缺上下文会困惑、且确有真实权衡的决策 → 提议 ADR，经用户确认后写入 `docs/adr/`。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。

项目级约定变更只能提示走 conventions 修订和 ADR；本 skill 不私改 `project-conventions.md`，也不把未确认的技术选择写成已选定。

## 触碰红线 fail 回退

拷问清单摘要里的任一平台硬红线被当前产物触碰时，立即判定本次拷问分支 **fail**，不输出通过建议，也不作为任何 Gate 放行依据。输出必须包含：

- 红线名称。
- 证据锚点：行为编号、设计章节、归属表行、承接索引项或代码路径。
- 为什么该问题不能在下游补救。
- 必须回退到哪个上游步骤修订：需求、概要归属、项目约定或 ADR。

fail 后停止继续问普通澄清题，直到相关产物修正。存量违例只在 project-conventions 的存量清单中登记时才可按"触碰记债"处理；清单外新增同类违例仍按新增违例 fail。

合规 STOP：触及鉴权、会话、密钥、用户数据采集、隐私、支付、政策或法规不确定性时，停止替用户拍板，输出风险点、可选替代方案和人类确认清单。

## 边界

- 不替代 `trellis-brainstorm`：探索、初稿生成和新流程 Domain Grill 在前，本 skill 只用于 compatibility-only 的额外拷问。
- 不替代平台 writing skill：本 skill 不代写完整需求或设计章节，只把拷问决策最小回写到既有产物。
- 不替代平台 review skill：拷问后的产物仍必须交给对应 review 得出互斥结论，并由 `record-review` 写入新模型证据。
- 不替代 `trellis-check`：不做实现期构建、测试、lint 或代码质量 Gate。
- 不进入实现细节：方法签名全集、字段级 schema、DDL、SDK 参数、secret value、完整测试代码属于详细设计或实现阶段。
- 产物语言中文优先；代码标识符、命令、路径、协议字段、库名和原文引用保留原文。

一句话定位链：brainstorm 通过 Domain Grill 定"做什么"并磨尖术语 → writing 写"分哪层、边界、谁承接" → review 判"能否进下一阶段" → trellis-check 判"代码是否达标"；**design-grill 只在旧任务兼容审计或用户显式要求时额外使用**。
