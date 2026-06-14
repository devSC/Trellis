# Guru Fork / safe_land_web 问题排查报告

- **日期**：2026-06-14
- **仓库**：`Trellis`(guru/main)、`safe_land_web`
- **本轮结果**：修复 4 个问题 + 1 个方法论纠偏，推送 3 个 commit
- **相关 commit**：`762b62ac`（需求三件套）、`ee577e8e`（skill 双面对齐）、`258aca72`（core 缺口硬失败）

---

## 总览

| # | 问题 | 严重度 | 根因层 | 状态 | Commit |
|---|------|:---:|------|:---:|------|
| 1 | 需求三件套 `requirement-*` 全平台未安装，Phase1 需求阶段硬前置断链 | 🔴 高 | apply.sh 排除 + init 不装 | ✅ 已修 | `762b62ac` |
| 2 | `trellis-*` 引擎 skill 在客户端「未找到」 | 🟠 中 | 双 skill 面单向镜像 | ✅ 已修 | `ee577e8e` |
| 3 | safe_land_web 硬 Gate 静默失效（core 缺 before_start） | 🔴 高 | 用上游 CLI bootstrap | ✅ 已修 | 未提交¹ |
| 4 | apply.sh 对 core 缺口只软警告、仍报「装配通过」（假安全） | 🟠 中 | 安装器自检盲区 | ✅ 已修 | `258aca72` |
| 5 | 方法论：手改目标项目单文件，而非改安装器重跑 | — | 流程纠偏 | ✅ 已纠 | （并入 #4） |
| 6 | `trellis-start` 只在 `.agents/skills`、`.claude/skills` 缺（两面再漂移） | 🟠 中 | 平台 configurator 单面写 | ✅ 已修 | §4.5 重跑 + 自检 |

> ¹ safe_land_web 是业务项目、整套安装未提交（留 review），core 两文件的修复在其工作区内。

---

## 问题 1｜需求三件套全平台缺失

**现象**：安装的 skill 里没有 `requirement-doc-standard / requirement-writing / requirement-review`。

**根因（系统性）**：这三个 skill 被**所有平台 workflow 的 Phase1(需求)** 硬前置依赖（"先加载 requirement-writing，缺即停"），但只存在于 `guru-ai-guides`：

1. fork 的 `agents-skills/` 没 bundle 它们；
2. apply.sh 把它们当「项目自有」明确排除；
3. `SKILL_GLOBS` 是平台前缀（`h5-*` 等），匹配不到 `requirement-*`；
4. 上游 `trellis init` 也不装。

→ **纯用 fork 安装的项目，需求阶段整段不可用。**

**修复**：把三件套（平台无关，覆盖 App/Web/API/CLI，0 参考项目硬编码）copy 进 `guru-template/overlay/agents-skills/` 作 **shared skill**；apply.sh 加 `SHARED_SKILLS`（每平台都装、切平台不剪），§1/§4 改单遍历统一「装 shared + 平台 + 剪枝」。

**验证**：flutter=11(8+3)、go/ios/h5=10(7+3)，各平台都装、0 他平台残留、切平台保留 shared。

---

## 问题 2｜trellis-* 引擎 skill 客户端「未找到」

**现象**：safe_land_web 里 `$trell` 搜不到任何 skill，trellis-* 像「又没了」。

**根因（双 skill 面 drift）**：项目里有**两套 skill 目录**，两个安装器各管一套、从不对齐：

| 目录 | 谁读 | 谁装 |
|------|------|------|
| `.claude/skills/` | Claude Code | `trellis init --claude` 装 trellis-*；apply.sh 镜像 guru |
| `.agents/skills/` | Codex / 本地 agent 客户端 | 只有 apply.sh 装 guru |

`trellis init --claude` 把引擎 skill **只装进 `.claude/skills/`**，apply.sh 的镜像又**只搬 guru skill** → **没人把 trellis-* 镜像进 `.agents/skills/`**。读 `.agents/skills/` 的客户端因此永远看不到 trellis 引擎 skill。**不是回归，是单向镜像的固有缺口。**

**修复**：apply.sh 新增 §4.5「双面对齐」——把一面有、另一面缺的**非 guru** skill（引擎 trellis-*、trellis-local、用户自有）互补到对面，两面拉成同一并集。guru 越界项已在 §1/§4 从两面同时剪掉、且只补非 guru 项，故不复活被裁剪的他平台 skill。

**验证**：safe_land_web 补齐 9 个 trellis-*，两面各 19 个完全一致，二次 apply 补齐 ×0（幂等）；切平台 trellis 留存。

---

## 问题 3｜safe_land_web 硬 Gate 静默失效

**现象**：apply.sh 自检报 `✗ core 缺 before_start 阻断支持`。

**根因**：guru 硬 Gate 依赖 core 里的 `run_blocking_task_hooks`（`task.py` + `common/task_utils.py` 的 before_start 阻断路径），这是 guru fork 相对上游的增量。**safe_land_web 当初用上游 CLI `0.6.0-rc.0` init**（`.trellis/.version` 不带 `-guru`），其 core 没有这个函数。后果：apply.sh 把 `before_start: guru_gate.py check` 写进了 `config.yaml`，但 core 不支持阻断 → **该 Gate 被静默忽略，`task.py start` 拦不住，假安全。**

**根因验证**：用 guru fork CLI（`-guru.2`）init 的 throwaway，core **自带** `run_blocking_task_hooks`——证明只要用对 CLI 就无需手补。

**修复 + 端到端验证**：把 core 两文件升到 guru 模板版（字节一致）。实测临时任务 `task.py start`：

```
[guru-gate:requirements] 未通过，缺口：- prd.md 不存在或为空
[BLOCK] before_start hook rejected the operation: python3 .trellis/scripts/guru/guru_gate.py check
Error: task activation blocked by before_start hook
→ exit=1   ✓ 硬 Gate 真的拦住了
```

---

## 问题 4｜apply.sh 对 core 缺口「假安全」

**现象**：core 缺口时 apply.sh 只打印软警告，却仍输出「装配完成，自检通过」。

**根因**：自检里该分支没置 `FAIL=1`。**最危险的失败**——用户以为有硬 Gate，实则没有。

**修复**（`258aca72`）：改为**硬失败 exit 1** + 打印根因（`.trellis/.version` 非 `-guru`）+ 可复现修复命令（`npm i -g @devsc/trellis@guru && trellis update`，对 core 两文件取模板版）。core 仍按脚本头部边界归 `trellis update` 的哈希合并管理，overlay 不碰 core——只是把「接了 Gate 却没 core 支撑」这一矛盾从静默变响亮。

**验证**：上游 core 项目跑 apply.sh → exit=1 红牌中止；safe_land_web（已修）→ exit=0 通过。

---

## 问题 5｜方法论纠偏：手改单文件 vs 改安装器

**质疑**：「为什么修改单个文件，而不是反复调用 trellis 的安装脚本？」——**成立。**

- skill 缺口（#1/#2）改的是**安装脚本**再重跑（对）；
- core 缺口（#3）**手 `cp` 了两个文件**（错——不可复现的 drift，只修这一个项目）。

**为什么会手抄**：当时没有任一安装脚本能就地修 core——apply.sh 按设计不碰 core，`trellis update` 又需 guru CLI（全局是上游）且交互式无法在自动化环境跑。**但真正根因是 safe_land_web 用错 CLI bootstrap**，不是「该不该手抄」。

**纠偏动作**：不是继续手补，而是**堵住安装器盲区**（即 #4 的硬失败）——以后这类缺口安装器自己喊停、逼用正确机制，没人再去手 patch。

**沉淀的原则**：

- 修缺口先定位「哪个安装器该负责它」：guru 内容/skill/hook/spec → 改 `apply.sh` 重跑；core → 归 `trellis update`（用 guru CLI）。改安装器（幂等带上，或缺失时硬失败指路），而非手 patch 目标。
- guru 项目必须用 guru fork CLI（`@devsc/trellis@guru`）做 init/update，否则 core 缺 before_start、硬 Gate 静默失效。

---

## 问题 6 + 维护规约｜skill 双面对齐是「点对点」而非「持续」

**现象**：上轮 §4.5 把两面拉平后，`trellis-start` 又出现「只在 `.agents/skills`、`.claude/skills` 缺」。

**根因**：`trellis-start` 是 **Codex/agents 平台专属**引导 skill（Claude 用 SessionStart hook 代替，不装它）。平台 configurator / `trellis update` 会向**单面**写 skill（Codex 侧的 trellis-start 只进 `.agents/skills`），而 §4.5 双面对齐**只在 apply.sh 运行那一刻**生效——之后任何 update/reconfigure 都可能重新制造不对称。**点对点对齐 ≠ 持续保证。**

**修复**：重跑 `apply.sh`（§4.5 补齐 ×1），两面恢复一致（各 20 含 trellis-start）。

**维护规约（方案 A，已落地）**：

1. **每次 `trellis update` / 平台 reconfigure 后，补跑一次 `bash apply.sh <proj> <platform>`**——§4.5 幂等拉平两面。
2. apply.sh 自检新增**「两面一致」不变量断言**（`.agents/skills == .claude/skills`，非项目镜像模式下）：不一致即 `FAIL=1` 打印 diff，把漂移从静默变响亮。
3. apply.sh 收尾打印该维护规约提示。

> 备注：`trellis-start` 的自动引导链（`inject-workflow-state.py` hook）当前**未在 settings.json 接线**、且无 `.codex/`，故它现在只能**手动** `$trellis-start` 调用，不会自动注入 `<trellis-bootstrap>`。如需自动引导，须补接 UserPromptSubmit hook（属上游 Codex 平台配置，另议）。

---

## safe_land_web 完整体检结论

| 项 | 状态 |
|----|------|
| 引擎基座（harness / guides / README / workflow.md / guru 脚本 / config / worktree） | ✅ 全在 |
| skills（两面 19 个对齐） | ✅ |
| conventions + by-layer（Codex 真实扫描填，0 残留） | ✅ |
| hooks ×4 + settings.json（无悬空引用） | ✅ |
| grill-nudge→h5-design-grill / AGENTS.md / bootstrap(已归档) | ✅ |
| **core before_start 阻断** | ✅ 已修，端到端实测可拦截 |
| SLOT-12 空 | ✅ 纯新项目合规（无老目录） |

**结论：必要内容全部齐备，功能上完整可用。**

---

## 待定夺 / 收尾项

1. **彻底纯净化 safe_land_web core**（非必须，功能已正常）：终端跑
   `npm i -g @devsc/trellis@guru` + `cd safe_land_web && trellis update`，重新基线哈希清单。
2. **架构选择**：维持「apply.sh 不碰 core、只硬失败指路」（推荐，边界清晰）？还是让 apply.sh
   自带 guru core 增量、上游 init 的项目也能纯靠 apply.sh 修好（代价：overlay 捎带 core、与
   update 哈希管理重叠）？
3. safe_land_web 整套安装仍未提交（留 review）。
