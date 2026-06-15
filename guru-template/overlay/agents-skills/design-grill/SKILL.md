---
name: design-grill
description: 通用 Guru Gate 前拷问会话。运行时读取当前项目 .trellis/spec/ 的 golden-path、project-conventions、harness / conventions 权威源，自动生成本端拷问清单摘要；逐分支拷问 prd 或概要归属表，磨尖术语、压测边界场景、与目标仓库代码交叉核对，并把决策当场固化进 prd/design/CONTEXT/ADR。触碰红线时当场 fail 回退，不打开硬 gate，不替代 brainstorm、writing、review 或 trellis-check。
---

# design-grill — Guru Gate 前拷问

## 做什么

对当前 task 产物发起送审前的对抗式拷问：需求 Gate 前拷问 `prd.md` 的行为集合；概要 Gate 前拷问 `design.md` 或 `design-main.md` 的归属表、三问理由与承接索引。沿设计树逐分支推进，决策间依赖逐个解开，每个归属判定都必须经得起"为什么属于它 / 为什么不属于别人 / 为什么需要或不需要独立存在"三问。

- 一次只问一个问题，每个问题附上你的推荐答案和依据，等用户反馈再继续。
- 能从代码或 spec 找到答案的问题不要问用户，先自己读取证据。
- 本 skill 不从零生成需求或设计，不给正式 Gate 结论；它只在送审前磨稿、排雷、回写决策。

## 拷问对照物

先做适用域门控，再装载领域模型。门控三态：

1. **非 guru 布局**：找不到 `.trellis/spec/guides/golden-path.md`，说明当前仓库不是 guru 领域模型布局。输出"design-grill 不适用当前布局"并退出，不降级成普通聊天式拷问。
2. **guru 但项目约定未就绪**：能找到 guru golden-path，但 `.trellis/spec/conventions/project-conventions.md` 缺失，或只存在 `*.template.md` / 样例文件而没有当前项目取值。阻断并提示"先完成项目约定"，列出应按 conventions index 完成的校验项，不继续拷问。
3. **guru 且约定就绪**：继续读取下列权威源，生成本端"拷问清单摘要"后再提第一个问题。

运行时必须读取并确认：

- `.trellis/spec/guides/golden-path.md`：分层依赖律、硬红线、禁止清单。
- `.trellis/spec/conventions/project-conventions.md`：当前项目取值、存量违例清单、校验清单结果。`project-conventions.template.md` 和样例文件只能作为修复提示，不能作为有效取值。
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

## 会话六动作

1. **对照术语表挑战**：用语与 `CONTEXT.md` / `CONTEXT-MAP.md` 既有定义冲突时立即点破；术语未入表且属于领域概念时，要求当场裁定。
2. **磨尖模糊语言**：遇到含混、过载、名词先行或跨平台串台的说法，给出精确候选和你推荐的收口方式；行为标题同步收窄到可实现、可验证的粒度。
3. **具体场景压测**：发明边界场景，逼出唯一写 owner、失败路径、并发/生命周期/跨边界责任、数据读写归属和回滚/补偿策略。
4. **与代码交叉核对**：把用户陈述、prd/design 草稿与目标仓库现状对照；有矛盾时给出具体文件或符号证据，再问用户以哪个为准。
5. **逐行归属拷问**：概要阶段按行为或状态逐行核对 owner、三问理由、承接索引与本端硬红线；不能用下游详细设计补造上游归属缺陷。
6. **节奏控制**：每轮只推进一个未决点。红线命中时停止该分支；普通歧义则给推荐答案并等待用户确认。

## 决策四去向

- 行为、范围、失败路径、验收场景决策 → 回写 `prd.md`，把未决问题改成已决并附一句依据。
- 归属、owner、承接索引、三问理由决策 → 回写 `design.md` / `design-main.md` 的对应表格或章节。
- 纯领域术语和歧义裁定 → 回写 `CONTEXT.md`，或按 `CONTEXT-MAP.md` 定位到对应 context。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。
- 难以回头、缺上下文会困惑、且确有真实权衡的决策 → 提议 ADR，经用户确认后写入 `docs/adr/`。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。

项目级约定变更只能提示走 conventions 修订和 ADR；本 skill 不私改 `project-conventions.md`，也不把未确认的技术选择写成已选定。

## 触碰红线 fail 回退

拷问清单摘要里的任一平台硬红线被当前产物触碰时，立即判定本次拷问分支 **fail**，不放行进对应 Gate。输出必须包含：

- 红线名称。
- 证据锚点：行为编号、设计章节、归属表行、承接索引项或代码路径。
- 为什么该问题不能在下游补救。
- 必须回退到哪个上游步骤修订：需求、概要归属、项目约定或 ADR。

fail 后停止继续问普通澄清题，直到相关产物修正。存量违例只在 project-conventions 的存量清单中登记时才可按"触碰记债"处理；清单外新增同类违例仍按新增违例 fail。

合规 STOP：触及鉴权、会话、密钥、用户数据采集、隐私、支付、政策或法规不确定性时，停止替用户拍板，输出风险点、可选替代方案和人类确认清单。

## 边界

- 不替代 `trellis-brainstorm`：探索和初稿生成在前，本 skill 只拷问已有草稿。
- 不替代平台 writing skill：本 skill 不代写完整需求或设计章节，只把拷问决策最小回写到既有产物。
- 不替代平台 review skill：拷问后的产物仍必须交给对应 review / Gate 得出互斥结论。
- 不替代 `trellis-check`：不做实现期构建、测试、lint 或代码质量 Gate。
- 不进入实现细节：方法签名全集、字段级 schema、DDL、SDK 参数、secret value、完整测试代码属于详细设计或实现阶段。
- 产物语言中文优先；代码标识符、命令、路径、协议字段、库名和原文引用保留原文。

一句话定位链：brainstorm 定"做什么" → writing 写"分哪层、边界、谁承接" → **design-grill 在送审前对抗式拷问、磨尖术语、固化决策、红线 fail 回退** → review 判"能否进下一阶段" → trellis-check 判"代码是否达标"。
