# Implement — 通用化 design-grill skill 与跨工具 grill 触发

> 第 3 版：三阶段（A 引入 / B 硬前置 / C 收尾），每阶段独立可运行、可单独 revert。行号为 HEAD 参考，**落地按 grep 内容匹配**。只改 `guru-template/` + 同步 `packages/cli` bundled 副本。

## 决策基线
D1 全任务硬前置+可 opt-out | D2′ 经 alias wrapper 渐进收敛到单 design-grill | D3 只改模板库（含 bundled 同步） | E1 grill 凭据走 `guru_gate.py` 命令记入 `guru_gates`（不写自由文件） | E2 grill 覆盖 requirements/overview/detail 三道。

---

## 阶段 A — 引入 design-grill（无硬 gate，无悬空）

- [ ] **A0 取证**：通读 4 份旧 skill，产出"行为等价矩阵"（Go/H5/iOS/Flutter 各自必覆盖的红线/边界场景/代码交叉核对锚点/ADR 例型）。
- [ ] **A1 写 skill**：`agents-skills/design-grill/{SKILL,CONTEXT-FORMAT,ADR-FORMAT}.md`。含骨架（design §2.1）、对照物发现 + **权威源选择/冲突 fail**（§2.2）、**门控三态**（§2.3）、运行时生成**本端拷问清单摘要**（§2.4）。以 go/h5/ios 加厚版为基线。
- [ ] **A2 旧 4 名改 wrapper**：`{client-grill,go-design-grill,h5-design-grill,ios-design-grill}/SKILL.md` 内容改为薄 alias「加载 design-grill，传入平台上下文」（保留目录，仍属 GURU_SKILLS）。
- [ ] **A3 apply.sh**：`SHARED_SKILLS` 加 design-grill（与 A1 建目录成对）；加启动自检 `for s in $SHARED_SKILLS: test -d agents-skills/$s`；删 `GRILL_SKILL` case + sed 行（grep 定位），grill-nudge 占位符硬写 design-grill + 改注释平台映射表。
- [ ] **A4 引用同步（overlay）**：4 workflow（各 4 处）+ trellis-local（2）+ 2 chapter-guide（修 ios 误引 client-grill）+ incident → design-grill。
- [ ] **A5 bundled CLI**：`pnpm -C packages/cli sync:guru` 刷新 `packages/cli/src/templates/guru/`；确认 bundled workflows 引用已更新；改 `packages/cli/test/guru/guru-bundled.test.ts:43`（client-grill → design-grill）。
- **A 验证**：四平台 `apply.sh` → `.agents/.claude` 两面含 design-grill + wrapper、`diff -rq` 干净；`rg -n 'client-grill\b|go-design-grill|h5-design-grill|ios-design-grill' .` 仅命中 wrapper 目录与历史文档；`bash tests/apply_test.sh`、`pnpm -C packages/cli test` 过。
- **可 revert**：整组回退即恢复旧 4 skill；无硬 gate、无悬空引用。

## 阶段 B — 打开 grill 硬前置（E1/E2）

文件 `guru-template/overlay/verify/guru_gate.py`。**改 `cmd_confirm`/`cmd_check`/`auto` 前先 `gitnexus_impact`（不可用时见 follow-up 降级）。**
- [ ] **B1 新命令**：`grill-done <gate> [task_dir]` 与 `grill-skip <gate> --user-quote "<理由>"`，复用 `cmd_confirm` 的 TTY/soft 守卫（:704-727）+ `_record_*` 原子写（:646-688），写 `guru_gates[gate].grill={status,by,at,digest:_gate_digest(task_dir,gate)}`。
- [ ] **B2 校验函数**：`_grill_ok(task_dir,gate)`：status==done 且 digest 匹配 → ok；skipped → ok（留痕）；否则 BLOCK。
- [ ] **B3 三挂载 × 三 gate**：`cmd_confirm`（:736 后 per-gate）、`cmd_check`（:799-806）、`auto`（:840，planning + artifact 成形时）都对 requirements/overview/detail 调 `_grill_ok`。
- [ ] **B4 标记迁移**：grill-nudge `.grilled-*` → `.grill-nudged-*`；apply 清理/忽略存量旧 `.grilled-*` 并文档声明其失效。
- [ ] **B5 交互合同**：workflow 写明"如何合法完成 grill"（跑 `guru_gate.py grill-done <gate>` 或 confirm 时回答）+ BLOCK 时的提示给出命令。
- [ ] **B6 镜像契约**：定义 `sync_platform_skills.py` 同步/校验 SHARED_SKILLS 契约；`apply_test.sh` 场景 2 真实镜像 fixture，断言 `.claude/skills/design-grill` 在、旧名不在；apply 镜像模式显式校验两面。
- **B 验证**：`run_tests.sh` confirm 测试群（:216-249）扩 grill 单测：三 gate × {缺→BLOCK、done+digest 匹配→PASS、skip→PASS+留痕、digest 失配→BLOCK}；confirm/check/auto 三路都验；measure verify→auto 也拦。
- **可 revert**：回退 B 即回到"装了 design-grill 但不强制"的 A 态。

## 阶段 C — 收尾硬切（移除 wrapper）

- [ ] **C1** 确认 bundled / 镜像 / 测试 / 存量 apply 全过。
- [ ] **C2** 移除旧 4 wrapper 目录；apply 加"托管身份判断（比对模板 hash/frontmatter name+description）+ 备份到 `.trellis/backup/guru-legacy-skills/<ts>/`"清存量残留（**不无脑 rm -rf**）。
- **C 验证**：`rg` 全仓无旧名（除历史文档）；apply 幂等；存量项目升级后 design-grill 单份、双面一致。
- **可 revert**：回退 C 即恢复 wrapper 共存态。

---

## 风险文件
- 高：`apply.sh`（自检/镜像/wrapper 清理）、`guru_gate.py`（`cmd_confirm`/`cmd_check`/`auto` 三处 BLOCK 误拦）、bundled sync（漏 sync 致发布分叉）。

## task.py start 前 follow-up
- [ ] 三件套经用户 review 批准。
- [ ] **gitnexus 降级**：本环境若无 gitnexus MCP 工具，改用 `rg` 找 `cmd_confirm`/`cmd_check`/`auto`/`_gate_digest` 的调用方做手工 impact，并在 prd/此处记录降级，不卡前置。
- [ ] 确认全仓 `rg` 旧名白名单（历史文档/incident）已明确。
