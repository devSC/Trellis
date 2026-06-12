# Overlay — 官方模板机制覆盖不到的装配件

官方 `trellis init -t/-r/--workflow` 只分发 spec 目录与 workflow.md 单文件；以下由安装器（Phase 2 apply.sh）装配：

| 件 | 装到目标项目 | 说明 |
|----|--------------|------|
| `agents-skills/client-*/` | `.agents/skills/` | 7 个执行类 skill（15 平台共享池） |
| `verify/guru_gate.py` | `.trellis/scripts/guru/` | 五阶段 Gate（worktree.yaml verify 调 `auto`） |
| `hooks/guru_after_create.py` | `.trellis/scripts/guru/` | jsonl 基线注入（config.yaml after_create） |
| `hooks/platform/*.sh` | `.claude/hooks/` | 合规三拦截（l10n 同步/SLOT-12 老目录/制裁 TLD） |
| `config-snippets/*` | 对应配置合并 | worktree.verify / config.hooks / claude settings |
| `trellis-local/SKILL.md` | `.claude/skills/trellis-local/` | 团队定制登记（官方自我迭代规范） |

安装后必做：①按 conventions 模板填 `.trellis/spec/conventions/project-conventions.md` ②按 SLOT-12 填 block-legacy-dirs.sh 的 LEGACY_PATTERNS ③AGENTS.md 受管区块追加（Codex 等无 hook 平台兜底）。
