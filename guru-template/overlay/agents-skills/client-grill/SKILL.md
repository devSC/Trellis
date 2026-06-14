---
name: client-grill
description: Gate 前拷问会话（grill-with-docs 的 guru 适配版）。对照本项目领域模型（golden-path 分层语义、project-conventions 槽位、spec 项目域、既有 BHV/UNIT 编号）逐分支拷问 prd 或概要归属表，磨尖术语、压测边界场景、与代码交叉核对，决策当场固化进产物。运行位置：需求 Gate 前（拷问 prd.md）与概要 Gate 前（拷问 design.md §1）。不替代 trellis-brainstorm（探索生成）与 *-review（判定）。
---

# client-grill — Gate 前拷问

## 做什么

对当前 task 产物（`prd.md` 或 `design.md` §1）发起不留情面的逐分支拷问，直到达成共识：沿设计树逐支走，决策间依赖逐个解开。**一次只问一个问题，每个问题附上你的推荐答案**，等用户反馈再继续。能从代码/spec 找到答案的问题不要问用户——先自己查。

## 拷问对照物（领域模型，硬前置装载）

1. `.trellis/spec/guides/golden-path.md` — 分层语义与禁止清单（"这条行为你打算让 controller 拥有规则？分层律不允许"）。
2. `.trellis/spec/conventions/project-conventions.md` — 槽位取值与 SLOT-15 存量违例（"你说要新建 repository——SLOT-11 钉的目录是哪？"）。
3. `.trellis/spec/` 项目域（如本仓库的 `ueds/` 等子域目录）与 `_legacy` 之外的既有规范。
4. 当前任务既有产物：prd 的 `BHV-NNN` 行为集合、design §1 归属表（拷问概要时）。
5. 仓库根 `CONTEXT.md`（术语表，存在则装载；不存在时首个术语敲定时创建）。

## 会话期间

- **对照术语表挑战**：用语与 `CONTEXT.md` 既有定义冲突时立即点破——"术语表里 X 定义为甲，你现在的意思是乙——到底哪个？"
- **磨尖模糊语言**：出现含混/过载词汇时给出精确候选——"你说『账号』——是 Customer 还是 User？这是两个东西。"行为命名同步回写 `BHV-NNN` 标题短名。
- **具体场景压测**：发明探边场景逼出概念边界——"两个 BHV 并发触发时，这个状态谁是唯一写 owner？"
- **与代码交叉核对**：用户陈述与代码矛盾时当场摆出——"代码里是整单取消，你刚说支持部分取消——哪个对？"
- **决策当场固化**：
  - 行为/范围决策 → 立即更新 `prd.md`（未决问题 → 已决，附一句依据）；
  - 归属决策 → 立即更新 `design.md` §1 归属表三问理由；
  - 纯术语 → 更新仓库 `CONTEXT.md`（只做术语表，零实现细节，格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)）；
  - 项目级取值变化 → 提示走 conventions 修订（需 ADR），不当场私改。
- **克制地提议 ADR**（三条全中才提）：难以回头 + 缺上下文会令未来读者困惑 + 真实权衡的产物。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。

## 边界

- 不替代 `trellis-brainstorm`：探索与初稿生成在前（1.1/1.3 的 writing），本 skill 只拷问已有草稿。
- 不替代 `client-design-*-review`：拷问出的修订落盘后，仍走对应 review 给互斥 Gate 结论。
- 不进入实现细节（那是 design §2 / 实现阶段的领地）；不私自拍板项目约定。
- 产物语言：中文优先（标识符/命令/路径/专有名词除外）。
