# Overlay — 官方模板机制覆盖不到的装配件

官方 `trellis init -t/-r/--workflow` 只分发 spec 目录与 workflow.md 单文件；以下由安装器（Phase 2 apply.sh）装配：

| 件 | 装到目标项目 | 说明 |
|----|--------------|------|
| `agents-skills/*/` | `.agents/skills/` | Client / Go / H5 / iOS 的设计、实现与小迭代 skills（平台共享池） |
| `verify/guru_gate.py` | `.trellis/scripts/guru/` | 五阶段 Gate（worktree.yaml verify 调 `auto`） |
| `verify/guru_delivery_policy.py` + `policy/delivery-policy.json` | `.trellis/scripts/guru/` + `.trellis/policy/` | 四路由、预算、证据复用与 Codex-only policy |
| `hooks/guru_task.py` + `hooks/guru_after_start.py` | `.trellis/scripts/guru/` | High-risk guarded start；官方 Core 的 direct start 只记录 advisory evidence |
| `verify/guru_supervise.py` | `.trellis/scripts/guru/` | channel 驱动的 requirements/overview/detail/implement/check runner |
| `verify/guru_config_patch.py` | `.trellis/scripts/guru/` | 幂等补齐 `.trellis/config.yaml` 的 Guru 默认配置 |
| `hooks/guru_after_create.py` | `.trellis/scripts/guru/` | jsonl 基线注入（config.yaml after_create） |
| `hooks/platform/*.sh` | `.claude/hooks/` | 合规三拦截（l10n 同步/老目录/制裁 TLD） |
| `config-snippets/*` | 对应配置合并 | worktree.verify / config.hooks / claude settings |
| `trellis-local/SKILL.md` | `.claude/skills/trellis-local/` | 团队定制登记（官方自我迭代规范） |

安装后必做：①按 conventions 模板填 `.trellis/spec/conventions/project-conventions.md` ②按项目存量老目录约定填 block-legacy-dirs.sh 的 LEGACY_PATTERNS ③AGENTS.md 受管区块追加（Codex 等无 hook 平台兜底）。

## 四级交付路由

`delivery-policy.json` 与 `guru_delivery_policy.py` 是执行真源。Agent 根据需求清晰度、风险、
耦合、可逆性和验证成本自动推荐 Route；commit intent 只是交付动作，不决定任务难度。
High-risk/unknown-high 默认推荐 `full_chain`，但用户可显式选择或切换任一受支持 Route。
低于推荐的选择必须记录用户原话与风险确认；`gate-contract.json.route` 是执行权威。每次切换
都递增 `selection_generation` 并使绑定旧 generation / `scope_fingerprint` 的确认与证据失效，
无论首次仓库写入是否已经发生。

- `small_inline`：机械、明确、低风险且不改变行为合同；默认无完整 task、确认 0、Worker 0。
- `micro_task`：明确、低风险、路径有界的局部行为改变；最小 task contract、确认 0、focused check。
- `lite_task`：默认用于无 High-risk 的局部行为，也可由用户在完整 override audit 后选择。用官方 `task.py create` 创建标准 Trellis task；先查 repo evidence，只对未解决的
  产品/范围/失败路径/验收歧义运行 bounded Brainstorm。compact requirements 与 Brainstorm
  evidence 保存在 task-local `prd.md`；当前 digest 确认一次后自动 start、host-inline、focused
  check、mutable evidence、Spec 同步与可逆 commit-ready。Worker 0，不运行 Overview/Detail
  planning review。commit-ready 前，`verification-evidence.jsonl` 的 `deterministic_final` 必须
  绑定当前 `selection_generation`、`scope_fingerprint`、精确 staged `target_paths` / `target_digest`，
  且 `docs_code_test_consistency=passed`、`spec_sync=passed|not_required`；缺失或 stale 只要求重跑
  focused check，不增加用户确认或 Worker。
- `full_chain`：High-risk/unknown-high 的默认推荐路线；selected route 为 Full 时，实现 Worker 前先暴露 current requirements、
  critical/high risk 与关键不可逆设计决定，并合并为一批用户确认，再 guarded activation。

Lite `check-commit` 成功后会把 exact target digest、Custom docs/code/test contract digest 与
`scope_fingerprint` 追加成 task-local `delivery_evidence_cache`。后续官方 `guru_gate.py intake`
对相同 scope 自动命中；若 task metadata 已带 `affected_paths`，`task.py create` 的 after-create
hook 也直接命中。任一 target 或 Custom consistency digest 变化都会自动回到 100%，无需用户
管理 cache 参数。

确认预算固定为 Small/Micro/Lite/Full=`0/0/1/1 batch`。Lite/Full 确认后自动推进；只有 material
scope/digest 变化、新 High-risk 或新不可逆决定才允许重新确认。全程默认 provider 为 Codex，
当前 delivery policy 不得生成 Claude plan/event。

## 安装/升级边界（apply.sh）

apply.sh 负责 guru 定制内容的完整安装与升级刷新：skills（.agents + 平台镜像）、gate/hook 脚本、
settings.json 接线、workflow.md、harness/guides SSOT、config 接线，并在装配后自检。

用户生命周期保持在同一个兼容入口，不引入第二套状态或 ownership 真源：

| 操作 | 命令 | 是否写目标/rollback bundle |
|------|------|----------------------------|
| 计划 | `apply.sh --plan TARGET [platform] [--rollback-bundle NEW_BUNDLE]` | 否；只校验 target、平台、Template 输入和可选 bundle 路径 |
| 安装 | `apply.sh TARGET [platform] [--rollback-bundle NEW_BUNDLE]` | 是；原有语法保持兼容 |
| 状态 | `apply.sh --status TARGET BUNDLE` | 否；稳定输出 `installed-current`、`drifted` 或 `not-applied` |
| 验证 | `apply.sh --verify TARGET BUNDLE` | 否；复用 manifest、managed-assets 与 preimage 完整性，漂移或篡改返回非零 |
| 升级 | `apply.sh --upgrade TARGET [platform] --rollback-bundle NEW_BUNDLE` | 是；复用 apply 路径，bundle 必须为新的外部空目录 |
| 卸载 | `apply.sh --unapply TARGET BUNDLE` | 是；只恢复 bundle 拥有且 post-state 匹配的 assets |

`plan`、`status`、`verify` 不创建审计文件、不刷新时间戳，也不改 target 或 bundle 字节。
`prepared`（包括 failed-apply 的 `manual_required`）表示安装未完整收口，`status` 必须报告
`drifted`，不能把部分写入的 target 假报为 `not-applied`；只有缺失 receipt 或已
`recovered`/`restored` 的 bundle 才报告 `not-applied`。
显式 `upgrade` 先把升级前 target 保存进新的外部 rollback bundle，再运行原 apply 刷新逻辑；
因此随后用这个新 bundle 执行 `unapply`，会恢复到**本次升级前**，而不是首次安装前。
目标已有的用户 config 键、`project-conventions.md` 和其他非 managed 文件继续按既有 apply 合并/保留规则处理。

需要可撤销安装时，rollback bundle 必须放在目标项目外部。成功 apply 会把 preimage 与
post-apply target 做结构化 diff，在 `managed-assets.json` 中稳定记录实际新增、替换或删除的
非 Git assets，以及各自 pre/post type、mode、文件 digest/size 或 symlink target。普通
unapply 先校验 top-level manifest、managed evidence、preimage 和全部 managed post-state，
全部通过后才开始修改目标，并且只恢复这些 managed assets。无关文件的新增或修改不会阻断
unapply，也会逐字节保留；managed asset 漂移或 bundle/evidence 篡改会在首个 target mutation
前 fail closed。overlay 创建的目录只在清空 managed children 后仍为空时删除，目录中的用户
新增文件会连同非空目录保留。`.git` 从不进入 manifest/CAS/preimage，也不会被读取或修改：

```bash
bash /path/to/guru-template/overlay/apply.sh --plan /path/to/project flutter \
  --rollback-bundle /tmp/guru-overlay-rollback
bash /path/to/guru-template/overlay/apply.sh /path/to/project flutter \
  --rollback-bundle /tmp/guru-overlay-rollback
bash /path/to/guru-template/overlay/apply.sh --status /path/to/project \
  /tmp/guru-overlay-rollback
bash /path/to/guru-template/overlay/apply.sh --verify /path/to/project \
  /tmp/guru-overlay-rollback
bash /path/to/guru-template/overlay/apply.sh --upgrade /path/to/project flutter \
  --rollback-bundle /tmp/guru-overlay-upgrade-rollback
bash /path/to/guru-template/overlay/apply.sh --unapply /path/to/project \
  /tmp/guru-overlay-upgrade-rollback
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

## 从旧 Guru/Trellis 项目完整重装官方 0.6.7

需要先清掉目标项目里旧的 Trellis/Guru 管理文件，再安装官方
`@mindfoldhq/trellis@0.6.7` 和本 checkout 的 Custom overlay 时，使用：

```bash
bash guru-template/overlay/reinstall-official-067.sh --dry-run /absolute/path/to/target
bash guru-template/overlay/reinstall-official-067.sh --keep-backup /absolute/path/to/target
```

脚本只接受目标 Git 仓库根目录，自动从现有 `guru.platform`/Spec 检测
`flutter|go|ios|h5`；歧义时用 `--platform <platform>`。`--backup-dir` 可指定目标外部的
空目录。脚本通过临时 npm prefix 安装并校验精确官方包，不使用全局 Trellis，也不修改全局 npm
包或 `~/.agents/skills`、`~/.codex/skills`、`~/.claude/skills`。

重装时：

- `.trellis/tasks/**`、`.trellis/workspace/**` 原样恢复并校验 digest；旧 `.runtime/**` 不恢复；
- 新官方/Guru Spec 为底，项目约定和项目独有文件恢复，同路径差异写
  `spec-reconcile-report.json`；
- 官方和 Guru Skills 刷新，项目 Skills 保留，同名差异写
  `skill-reconcile-report.json`；
- `.trellis/scripts/**`、workflow、Guru policy/runtime 使用新版本，supervision 固定
  `codex/codex/adversarial=false`；
- 任一阶段失败会从外部 snapshot 恢复原托管面，并验证 `.git/index` 未变化。

无冲突返回 `0`；安装成功但有 Spec/Skill 手工 reconcile 项返回 `3` 并保留 backup；回滚本身失败
返回 `70`。无冲突成功时默认删除已验证 backup，传 `--keep-backup` 可保留所有 manifest、报告和
冲突证据。该入口是 operator-facing candidate，不替代 `apply.sh` 的常规升级/卸载生命周期。

V0 的 docs/code/tests 一致性、四路由 policy smoke、Codex-only event 负例与 apply/unapply
round-trip，以及 failed-apply recovery/CAS 拒绝覆盖负例，由
`bash guru-template/overlay/tests/apply_test.sh` 一次性验证。

官方 Trellis Core 目前没有阻断式 `before_start`。安装器不会写入一个 Core 会忽略的假硬 Gate，
而是安装 `guru_task.py start` 作为 High-risk 可写入口，使用 `after_start` 记录 direct official
start 的 advisory evidence，并由 Codex commit guard 保留不可逆边界。若目标 checkout 确实提供
blocking `before_start`，安装器才在 Guru config marker 中追加该 hook。

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
    adversarial_enabled: false
    adversarial_codex_model: gpt-5.4
    adversarial_codex_reasoning_effort: high
```

当前 Custom delivery boundary 固定 `provider: codex`，`high_risk_review_provider_policy: current`
因此仍解析为 Codex。`adversarial_enabled: false` 是安装和升级的默认值：Full 继续要求当前
digest 下两个不同 `run_id` 的 Codex clean review，但不生成 opposite-provider worker。旧项目里
残留的 provider/model 配置不会获得执行权，非 Codex launch 仍 fail closed。

也可以显式把高风险 slice 审查固定为 Codex：

```yaml
guru:
  supervision:
    # 当前实现与普通 Guru worker 使用 Codex。
    provider: codex
    # 高风险 slice 审查固定使用 Codex。
    high_risk_review_provider_policy: codex
    adversarial_enabled: false
```

`provider` 决定实现 provider；`high_risk_review_provider_policy` 只决定高风险 slice 的审查
provider。当前 Custom workflow 只使用 `current` 或 `codex`。`adversarial_enabled: false` 不会
削弱风险包、双 clean、一次确认、实现审查或 deterministic final；它只删除与 Codex-only
边界互锁的 opposite-provider 前置。

安装/刷新 overlay 时可以显式写入这个开关：

```bash
trellis guru apply flutter /path/to/project --adversarial-enabled false
```

不传 `--adversarial-enabled` 时，安装/升级会把该 Custom-owned执行默认值收敛为 `false`；
显式旧值也不能绕过非 Codex launch 的 fail-closed 边界。
