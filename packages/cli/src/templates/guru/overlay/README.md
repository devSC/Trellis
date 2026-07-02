# Overlay — 官方模板机制覆盖不到的装配件

官方 `trellis init -t/-r/--workflow` 只分发 spec 目录与 workflow.md 单文件；以下由安装器（Phase 2 apply.sh）装配：

| 件 | 装到目标项目 | 说明 |
|----|--------------|------|
| `agents-skills/client-*/` | `.agents/skills/` | 7 个执行类 skill（15 平台共享池） |
| `verify/guru_gate.py` | `.trellis/scripts/guru/` | 五阶段 Gate（worktree.yaml verify 调 `auto`） |
| `verify/guru_supervise.py` | `.trellis/scripts/guru/` | channel 驱动的 requirements/overview/detail/implement/check runner |
| `verify/guru_config_patch.py` | `.trellis/scripts/guru/` | 幂等补齐 `.trellis/config.yaml` 的 Guru 默认配置 |
| `hooks/guru_after_create.py` | `.trellis/scripts/guru/` | jsonl 基线注入（config.yaml after_create） |
| `hooks/platform/*.sh` | `.claude/hooks/` | 合规三拦截（l10n 同步/SLOT-12 老目录/制裁 TLD） |
| `config-snippets/*` | 对应配置合并 | worktree.verify / config.hooks / claude settings |
| `trellis-local/SKILL.md` | `.claude/skills/trellis-local/` | 团队定制登记（官方自我迭代规范） |

安装后必做：①按 conventions 模板填 `.trellis/spec/conventions/project-conventions.md` ②按 SLOT-12 填 block-legacy-dirs.sh 的 LEGACY_PATTERNS ③AGENTS.md 受管区块追加（Codex 等无 hook 平台兜底）。

## 安装/升级边界（apply.sh）

apply.sh 负责 guru 定制内容的完整安装与升级刷新：skills（.agents + 平台镜像）、gate/hook 脚本、
settings.json 接线、workflow.md、harness/guides SSOT、config 接线，并在装配后自检。

不负责（边界）：
- **CLI core 脚本**（task.py/common/*）：归 `trellis update` 的 hash 三方合并；apply.sh 只检测
  before_start 支持并警告。
- **conventions/project-conventions.md**：项目取值，永不覆盖。
- **.codex/skills 项目级内容**（如 guru-ai-guides 的 requirement-* 技能）与 AGENTS.md 项目区块：
  项目自有，入项目 git 管理。

## Guru supervision 配置

`apply.sh` 会在目标项目 `.trellis/config.yaml` 下补齐默认值：

```yaml
guru:
  supervision:
    provider: codex
    implement_timeout: 45m
    check_timeout: 30m
    warn_before: 5m
    adversarial_enabled: true
    adversarial_claude_model: claude-sonnet-4-6
    adversarial_codex_model: gpt-5.4
    adversarial_codex_reasoning_effort: high
```

`adversarial_enabled: false` 关闭 `guru_supervise.py --adversarial ...` 的 opposite-provider worker 启动，用来临时缩短任务耗时。它不会伪造 clean 证据；`guru_gate.py` 会动态读取该配置：requirements 不再强制 opposite-provider adversarial review，overview/detail 不再要求 adversarial reviewer，但仍要求当前 digest、双 clean review、用户确认以及没有 blocked/medium+ 当前证据。

安装/刷新 overlay 时可以显式写入这个开关：

```bash
trellis guru apply flutter /path/to/project --adversarial-enabled false
```

不传 `--adversarial-enabled` 时，安装脚本只补默认值并保留目标项目已有取值。
