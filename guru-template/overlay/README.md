# Overlay — 官方模板机制覆盖不到的装配件

官方 `trellis init -t/-r/--workflow` 只分发 spec 目录与 workflow.md 单文件；以下由安装器（Phase 2 apply.sh）装配：

| 件 | 装到目标项目 | 说明 |
|----|--------------|------|
| `agents-skills/client-*/` | `.agents/skills/` | 7 个执行类 skill（15 平台共享池） |
| `verify/guru_gate.py` | `.trellis/scripts/guru/` | 五阶段 Gate（worktree.yaml verify 调 `auto`） |
| `verify/guru_supervise.py` | `.trellis/scripts/guru/` | channel 驱动的 requirements/overview/detail/implement/check runner |
| `verify/guru_config_patch.py` | `.trellis/scripts/guru/` | 幂等补齐 `.trellis/config.yaml` 的 Guru 默认配置 |
| `hooks/guru_after_create.py` | `.trellis/scripts/guru/` | jsonl 基线注入（config.yaml after_create） |
| `hooks/platform/*.sh` | `.claude/hooks/` | 合规三拦截（l10n 同步/老目录/制裁 TLD） |
| `config-snippets/*` | 对应配置合并 | worktree.verify / config.hooks / claude settings |
| `trellis-local/SKILL.md` | `.claude/skills/trellis-local/` | 团队定制登记（官方自我迭代规范） |

安装后必做：①按 conventions 模板填 `.trellis/spec/conventions/project-conventions.md` ②按项目存量老目录约定填 block-legacy-dirs.sh 的 LEGACY_PATTERNS ③AGENTS.md 受管区块追加（Codex 等无 hook 平台兜底）。

## 安装/升级边界（apply.sh）

apply.sh 负责 guru 定制内容的完整安装与升级刷新：skills（.agents + 平台镜像）、gate/hook 脚本、
settings.json 接线、workflow.md、harness/guides SSOT、config 接线，并在装配后自检。

需要可撤销安装时，rollback bundle 必须放在目标项目外部。成功 apply 会把 preimage 与
post-apply target 做结构化 diff，在 `managed-assets.json` 中稳定记录实际新增、替换或删除的
非 Git assets，以及各自 pre/post type、mode、文件 digest/size 或 symlink target。普通
unapply 先校验 top-level manifest、managed evidence、preimage 和全部 managed post-state，
全部通过后才开始修改目标，并且只恢复这些 managed assets。无关文件的新增或修改不会阻断
unapply，也会逐字节保留；managed asset 漂移或 bundle/evidence 篡改会在首个 target mutation
前 fail closed。overlay 创建的目录只在清空 managed children 后仍为空时删除，目录中的用户
新增文件会连同非空目录保留。`.git` 从不进入 manifest/CAS/preimage，也不会被读取或修改：

```bash
bash /path/to/guru-template/overlay/apply.sh /path/to/project flutter \
  --rollback-bundle /tmp/guru-overlay-rollback
bash /path/to/guru-template/overlay/apply.sh --unapply /path/to/project \
  /tmp/guru-overlay-rollback
```

带 rollback bundle 的 apply 会先保存 `prepared` preimage，并在全部目标写入完成后记录
本进程最后一个 target digest checkpoint。之后若自检失败或收到 `INT`/`TERM`/`HUP`，只有
当前 target digest 仍精确匹配该 checkpoint 时才自动恢复 preimage；并发或外部目标漂移会
fail closed，bundle 保持 `prepared`、recovery 标为 `manual_required`，且不会伪装成可成功
unapply 的 `applied` 状态。自动恢复成功后 bundle 状态为 `recovered`，部分安装文件会被删除，
用户原有非 Git 文件按 preimage 精确恢复，`.git` 保持不动。rollback bundle 的解析后路径
必须位于目标项目外，且 bundle 路径本身不得是符号链接，避免通过路径别名绕回目标内部。
failed-apply recovery 仍使用这个 whole-target checkpoint，不使用尚未发布的 managed manifest。
旧 schema-v1 `applied` bundle 若没有 managed manifest，继续使用原有 whole-target exact-digest
unapply；不会猜测 ownership。

V0 的 docs/code/tests 一致性、四路由 policy smoke、Codex-only event 负例与 apply/unapply
round-trip，以及 failed-apply recovery/CAS 拒绝覆盖负例，由
`bash guru-template/overlay/tests/apply_test.sh` 一次性验证。

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
    high_risk_review_provider_policy: current
    adversarial_enabled: true
    adversarial_claude_model: claude-sonnet-4-6
    adversarial_codex_model: gpt-5.4
    adversarial_codex_reasoning_effort: high
```

`high_risk_review_provider_policy` 动态控制 slice-backed 高风险实现审查 provider：`current`（默认）沿用当前实现 provider，`opposite` 使用另一 provider，`codex` / `claude` 固定到指定 provider。带非空 `--user-quote` 的 `--same-provider` 一次性授权优先级最高；非 slice 的 staged/contract review 仍遵循既有 opposite-provider packet contract。该参数不改变审查是否 required，也不改变 `adversarial_enabled`。

需要将当前实现和高风险 slice 审查都硬锁到 Codex、避免 packet 的 `opposite` 元数据切换到 Claude 时，显式配置：

```yaml
guru:
  supervision:
    # 当前实现与普通 Guru worker 默认使用 Codex；命令行 --provider 仍可覆盖该值。
    provider: codex
    # 高风险 slice 审查固定使用 Codex，不跟随 current，也不接受 packet provider 元数据改写。
    high_risk_review_provider_policy: codex
```

`provider` 决定当前实现 provider；`high_risk_review_provider_policy` 只决定高风险 slice 的审查 provider。低风险 slice 继续服从自己的 packet contract，无 `--slice` 的 staged/contract review 继续要求既有 opposite-provider 证据。只有 policy 键完全缺失时才默认 `current`；显式 `null`、空串、纯空白、非字符串或未知值都会在生成 worker plan 前失败。

`adversarial_enabled: false` 只关闭 `guru_supervise.py --adversarial ...` 的 opposite-provider worker 启动，用来临时缩短任务耗时。它不会禁用高风险实现审查，也不会伪造 clean 证据；`guru_gate.py` 会动态读取该配置：requirements 不再强制 opposite-provider adversarial review，overview/detail 不再要求 adversarial reviewer，但仍要求当前 digest、双 clean review、用户确认以及没有 blocked/medium+ 当前证据。

安装/刷新 overlay 时可以显式写入这个开关：

```bash
trellis guru apply flutter /path/to/project --adversarial-enabled false
```

不传 `--adversarial-enabled` 时，安装脚本只补默认值并保留目标项目已有取值。
