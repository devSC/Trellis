# Design — 通用化 design-grill skill 与跨工具 grill 触发

> 第 3 版：采纳 Codex 对抗审查（reject）的更稳架构。核心变化：**grill 凭据走 `guru_gate.py` 命令记入 `guru_gates`（不写自由文件）；旧 4 名渐进 alias wrapper 替代（不 rm -rf）；三阶段可独立 revert；覆盖三道 gate + verify→auto 路径**。行号为 HEAD 参考，落地按 grep 匹配。

## 0. 决策基线

| 编号 | 决策 |
|------|------|
| D1 | 全任务硬前置 + 可 opt-out |
| D2′ | 收敛到单 `design-grill`，但**经 alias wrapper 渐进替代**（非一步硬删） |
| D3 | 只改模板库（含 bundled CLI 同步）；存量下次 apply 升级 |
| E1 | grill 凭据**走 `guru_gate.py` 命令**记入 `guru_gates`，复用 confirm 的 TTY/soft 审计+原子写+digest；不写 agent 自由文件 |
| E2 | grill 覆盖 **requirements/overview/detail 三道** gate |

## 1. 架构总览

```
skill 层：agents-skills/design-grill/（单份，平台无关）
  + 旧 4 名 = 薄 wrapper（alias「加载 design-grill」，过渡期共存，阶段3移除）
  运行时盲读 .trellis/spec + 门控三态 + 权威源选择/冲突 fail

触发层（grill 凭据走 guru_gate.py 命令，跨工具）：
  新增命令：guru_gate.py grill-done <gate> | grill-skip <gate> --user-quote ...
    → 复用 cmd_confirm 的 TTY/soft 审计 + _record 原子写 → guru_gates[gate].grill
  grill 校验函数 _grill_ok(task_dir, gate)：grill_status==done 且 digest 匹配（复用 _gate_digest）
  挂载三处：cmd_confirm（per-gate）+ cmd_check（start 兜底）+ auto（verify→auto 路径，planning 阶段）
  覆盖三道 gate；opt-out 走 grill-skip 命令（同审计强度）
  软提示：inject-workflow-state.py（UserPromptSubmit，两端）planning 块提醒

安装层：apply.sh
  design-grill 建目录 + 进 SHARED_SKILLS（成对，apply 启动自检）
  旧 wrapper 仍在 GURU_SKILLS → 走正常 install/prune（过渡期不需 rm -rf 黑名单）
  普通模式 §1/§4 两面装 + §8 diff -rq；镜像模式定义 sync 脚本契约 + fixture + 显式两面校验
  bundled CLI：pnpm -C packages/cli sync:guru 同步 + 改 guru-bundled.test.ts
```

## 2. design-grill skill 本体

### 2.1 骨架（写死，以 go/h5/ios 加厚版为基线）
六小节：做什么 / 拷问对照物（声明式探测）/ 会话六动作 / 决策四去向 / **触碰红线 fail 回退** / 边界 + 一句话定位链。正文不内联端 token。

### 2.2 对照物发现 + **权威源选择/冲突 fail**（采纳 Codex #8）
- golden-path.md（分层律/红线）、project-conventions.md（SLOT/存量违例）。
- **doc_type 权威源按平台定，不"都读"**：Go/H5 取 `harness/overview/overview-structure-single-source.md`（或 detail）、iOS 取 `conventions/index.md §5`；`conventions/index.md` 仅用于 project-conventions 校验规则。
- **冲突检测**：发现锚点间漂移（如 Go `conventions/index.md:22` 把 project-conventions 路径写成 `harness/conventions/`，与 apply 落位 `conventions/` 冲突）→ **fail 报告并停**，不把旧口径带入拷问。

### 2.3 适用域门控**三态**（采纳 Codex #7）
1. 非 guru 布局（无 golden-path）→ "grill 不适用"退出。
2. guru 但 `project-conventions.md` 未就绪（仅 `*.template.md`）→ **阻断提示"先完成项目约定 C1~Cn"，不降级成普通 grill**。
3. guru 且约定就绪 → 正常 grill。

### 2.4 合并验证标准 = **行为等价矩阵 + 本端拷问清单摘要**（采纳 Codex #9，替代"无平台 token"）
端特异红线/边界/代码锚点/ADR 例型是**触发 cue**，不是示例。为 Go/H5/iOS/Flutter 各列"必须覆盖项"矩阵；design-grill 正文可不写具体 token，但**运行时须读 spec 生成本端"拷问清单摘要"**，验证检查摘要含本端关键维度（如 Go：handler 不持数据访问 / service 无 net/http / secret fail；H5：server-client 边界；iOS：Domain 零依赖）。

### 2.5 ADR/CONTEXT-FORMAT
统一通用版，剥平台示例，中文优先。

## 3. 触发层（grill 凭据走命令，E1）

### 3.1 新增 `guru_gate.py` 子命令
- `grill-done <gate> [task_dir]`：复用 `cmd_confirm` 的 TTY/soft 守卫（:704-727）+ `_record_*` 原子写（:646-688），把 `guru_gates[gate].grill = {status:"done", by, at, digest:_gate_digest(task_dir,gate)}` 写入 task.json。**只有 TTY 用户 / soft+--user-quote 能写**，杜绝 agent 自证文件（采纳 Codex #4）。
- `grill-skip <gate> --user-quote "<理由>"`：同审计，写 `grill={status:"skipped", reason, by, at}`。opt-out 走此命令，不再用 `.grill-skip-*` 自由文件。

### 3.2 grill 校验函数 `_grill_ok(task_dir, gate)`
`guru_gates[gate].grill.status=="done"` 且 `digest==_gate_digest(task_dir,gate)` → ok；`=="skipped"` → ok（留痕）；否则 BLOCK。**digest 复用现有 `_gate_digest`（采纳 Codex #3）**——与 confirm 同一累积快照语义：上游产物改动 → grill 与 confirm 一起失配重做，语义一致、不新造 digest。

### 3.3 三挂载点 × 三 gate（采纳 Codex #2、#6）
| 挂载点 | 位置 | 作用 |
|--------|------|------|
| `cmd_confirm` | :736 结构 checker 后、写盘前，per-gate | 人工收口：未 grill 不让确认 |
| `cmd_check` | :799-806 结构复跑段 | `task.py start` 兜底（Codex before_start / Claude PreToolUse 两路） |
| `auto` | :840 verify→auto，planning 阶段 + 对应 artifact 成形时 | 堵第三条"verify 看起来绿"路径 |
三处都对 **requirements/overview/detail** 调 `_grill_ok`。gate↔产物由现有 `_gate_artifacts` 决定，grill 与 confirm 对齐。

### 3.4 软提示 + 标记迁移
- workflow.md planning 块加 grill 提醒（inject-workflow-state.py 两端注入）。
- `grill-nudge.sh` 的 `.grilled-*` 改写 `.grill-nudged-*`（仅提示幂等）；apply 顺带清理/忽略存量旧 `.grilled-*` 并文档声明其不再表示完成（采纳 Codex 遗漏项）。

### 3.5 性质声明（采纳 Codex 中危）
全程措辞用**"防无意绕过 / 流程纪律"**，不写"防绕过"。guru_gate 自述 integrity aid 非安全边界（:554-561）；grill-done/skip 走命令已是现有最强审计强度，但仍非安全边界。

### 3.6 Codex 生效前提
挂 cmd_check/auto 的硬前置在 Codex 依赖 core `run_blocking_task_hooks`（guru fork CLI）；上游 CLI 装的项目 Codex 侧失效，Claude 侧 PreToolUse 兜底。写入风险节。

## 4. 安装与发布同步（apply.sh + bundled CLI）

### 4.1 skill 安装（成对 + 自检）
- design-grill 建目录（进 GURU_SKILLS）+ 进 SHARED_SKILLS。
- **apply 启动自检**：`for s in $SHARED_SKILLS: test -d agents-skills/$s`；§8 后断言 `.agents/.claude` 两面都含 design-grill（采纳 Codex 中危 #2）。
- 删 case `GRILL_SKILL` + sed（grep 定位，参考 :22-25/:120），grill-nudge 占位符硬写 design-grill。

### 4.2 旧 4 名 = wrapper（过渡，免 rm -rf）
过渡期把旧 4 目录内容改为薄 wrapper（alias「加载 design-grill」）。它们仍在 GURU_SKILLS → 走**正常 install/prune**，无需危险 legacy 黑名单。阶段 3 移除 wrapper 时才做"托管身份判断（比对模板 hash/frontmatter）+ 备份到 `.trellis/backup/guru-legacy-skills/<ts>/`"清存量（采纳 Codex #3 中危）。

### 4.3 镜像模式契约（采纳 Codex #5）
`USED_PROJECT_MIRROR=1` 时 §4.5 跳过、§8 只 `--check`。定义 `sync_platform_skills.py` 必须同步/校验 SHARED_SKILLS 的契约；`apply_test.sh` 场景 2 用真实镜像行为构造 fixture，断言 `.claude/skills/design-grill` 在、旧名不在；apply 在镜像模式显式校验 design-grill 两面存在。

### 4.4 bundled CLI 发布面（采纳 Codex 致命 #1）
改完 `guru-template/` 后跑 `pnpm -C packages/cli sync:guru` 刷新 `packages/cli/src/templates/guru/`；更新 bundled workflows 引用；改 `packages/cli/test/guru/guru-bundled.test.ts:43`（旧断言 client-grill → design-grill）。全仓验证：`rg -n 'client-grill\b|go-design-grill|h5-design-grill|ios-design-grill' .`，允许项仅 legacy 迁移白名单/历史文档。

### 4.5 引用同步
4 workflow（overlay + bundled 两套）+ trellis-local + 2 chapter-guide（修 ios 误引）+ incident + grill-nudge 注释 → design-grill。

## 5. 三阶段实施（每步可运行、可独立 revert — 采纳 Codex 更简方案）

- **阶段 A（引入，无硬 gate）**：新增 design-grill；旧 4 名改 wrapper alias；apply 装两者；overlay+bundled workflow/hook 引用切 design-grill；sync:guru + 改 bundled 测试。验证：apply 四平台 + `diff -rq` 双面 + 全仓 rg 干净 + 现有测试过。**此时无悬空、无硬 gate。**
- **阶段 B（打开硬前置）**：guru_gate.py 加 grill-done/grill-skip 命令 + `_grill_ok`，挂 confirm/check/auto 三处 × 三 gate；grill-nudge 改 `.grill-nudged-*`；workflow 写"如何合法完成 grill"交互合同。验证：confirm/check/auto 单测（缺/done/skip/digest 失配）。
- **阶段 C（收尾硬切）**：确认 bundled/镜像/测试/存量 apply 全过后，移除旧 wrapper（托管身份判断 + 备份）。验证：全仓 rg 无旧名（除历史文档）。

## 6. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 漏 bundled 导致发布分叉 | sync:guru 纳入流程 + 全仓 rg 验证 + 改 bundled 测试 |
| verify→auto 漏网 | auto 也调 `_grill_ok`（planning + artifact 成形时） |
| digest 误伤 | 复用 _gate_digest（与 confirm 同语义，不额外引入误伤面） |
| 镜像模式假绿 | 脚本契约 + 真实 fixture + 显式两面校验 |
| 误删用户同名 skill | 不 rm -rf；阶段 C 托管身份判断 + 备份 |
| 门控误判/旧口径污染 | 三态门控 + 权威源选择 + 冲突 fail |
| 合并丢端特异触发力 | 行为等价矩阵 + 本端拷问清单摘要验证 |
| Codex 硬前置失效 | 注明前提=guru fork CLI；Claude PreToolUse 兜底 |
| GitNexus 不可用 | implement 写降级（grep/手工 impact），不卡前置 |

**回滚**：阶段 A/B/C 各自可运行、可独立 revert（Codex 更简方案的核心收益）。

## 7. 验证（详见 implement.md）
apply 四平台 + 双面 diff + design-grill 两面在/旧名按阶段；guru_gate grill-done/skip/_grill_ok 单测（三 gate × 缺/done/skip/失配）；confirm+check+auto 三路都拦；himora 端到端（盲读 spec、权威源、拷问清单摘要含本端维度）；vanilla 门控三态；bundled 测试与 rg 全仓。
