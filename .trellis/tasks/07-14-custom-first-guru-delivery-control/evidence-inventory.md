# Evidence Inventory

## Official Trellis extension contracts

- `https://docs.trytrellis.app/advanced/custom-workflow`：`.trellis/workflow.md` 控制阶段、skill routing、workflow-state；修改后无需重建 Trellis。
- `https://docs.trytrellis.app/advanced/custom-spec-template-marketplace`：Git-backed `type: spec` registry、安装和版本化边界。
- `https://docs.trytrellis.app/advanced/custom-skills`：Skill 是主要自动触发扩展点。
- `https://docs.trytrellis.app/advanced/custom-agents`：平台级 sub-agent 定义、上下文和权限差异。
- `https://docs.trytrellis.app/advanced/custom-hooks`：SessionStart/UserPromptSubmit/PreToolUse/PostToolUse 能力及平台差异。
- `https://docs.trytrellis.app/advanced/configuration`：官方 config keys、非阻断 lifecycle hooks、Codex inline/sub-agent 与 channel guard。
- `https://docs.trytrellis.app/advanced/architecture`：workflow、task/spec wiki、context manifest 和 review boundary 的官方职责。

## Current registry and distribution

- `guru-template/index.json`：只登记 `guru-flutter-client` spec 与 `guru-client` workflow；Go/H5/iOS 文件存在但未完整登记。
- `guru-template/workflows/*.md`：四平台 Guru workflow 真源候选。
- `guru-template/specs/*`：四平台 spec registry 真源候选。
- `guru-template/overlay/README.md`：明确官方 workflow/spec Template 无法分发 Skills、Hooks、Scripts、Config，需要 overlay。
- `guru-template/overlay/apply.sh`：现有幂等安装/升级器；存在局部备份与失败回滚，但无完整 plan/status/unapply ownership contract。
- `guru-template/overlay/trellis-local/SKILL.md`：当前自定义登记和“spec 为规则唯一真源”的既有约定。

## Official 0.6.7 observed behavior

- npm artifact：`@mindfoldhq/trellis@0.6.7`，integrity `sha512-W67K3DvKGk2W/cFGWM3ev2HvMY9DzWc2sWegv7l+iBiY//Vf9lplQT9dy7jD7j4+MwHDLFIYSM7nZjFcGqgrrg==`，tarball SHA-256 `98e3c22bedf2f201d0370bd40e7baeb5c0e8b323f1f768abde433f3fb227cfaf`。
- Official `task.py` SHA-256 `46a94e4acf1c967fe5c3606ba5d1572cd0c43033a16fe01de55ac568954e6c18`；official `common/active_task.py` SHA-256 `8ac10263a88262aeaec2c600b33f3761f99d80c305718609a3bef97a2ff08938`。有 session identity 时 `task.py start` 先写 session pointer，再做 `planning -> in_progress`，最后运行 non-blocking `after_start`；无 identity 时仍改 status、运行 hook 并返回 `0`。
- Official `set_active_task` 会对 session JSON 执行 `current_run` 缺失时补 `null`、已有值时保留，同时更新 `current_task` 和 metadata。任何 guarded compensation 必须绑定整个 session preimage/postimage，不能只恢复 task pointer。
- 现场复现 `npx -y @mindfoldhq/trellis@0.6.7 init -y --codex --template __definitely_missing_template__`：输出 `Template ... not found` 和 `Falling back to blank templates...`，创建 blank Trellis project，退出码仍为 `0`。因此“错误 registry/template 必须 non-zero”只能由 Guru preflight + isolated staging + postcondition wrapper 提供，不能归因给 bare official CLI。
- Official custom registry parser 接受 GitHub/GitLab/Bitbucket/self-hosted Git source，不接受本地目录或 `file:`。验证当前未提交候选 bytes 需要 hermetic remote-compatible Git fixture；使用旧 pushed ref 不是当前候选 E2E。

## Current executable-environment facts

- 本工作树实际执行的 `.trellis/scripts/task.py` SHA-256 是 `6c65801a1f56648fd4765a1d216493d3094827c1db4761e55fdaa548c1801798`，不是 official tarball 内脚本；其 `active_task.py`、`task_utils.py`、`io.py`、`config.py` SHA-256 分别为 `6c88ed40ef7289bca0f6d2ecba0f8b8aef46cd58788080fbeeea88de138a431f`、`f5ef4af87ba3e11d8b19630c0c96d009de1811fc9be56c2027a9c96e21ed103e`、`6480b181f2bc505323b28ed7a66963d7b7edc96251e83b4c8e7a45907cc721c8`、`25c5a53ad20d6909be5209222e4208a84528805316a4d78350529459a364edb1`。Bootstrap 必须绑定实际调用链；official hash 只作独立兼容基线。
- `codex-cli 0.142.5` 的 persisted rollout JSONL 提供累积/单轮 `input_tokens`、`cached_input_tokens`、`output_tokens` 和 `total_tokens`；其中 `input_tokens` 已含 cached，故 uncached 必须计算为 `input_tokens - cached_input_tokens`。采集器必须绑定 session/turn、源文件字节范围和 adapter version，不能只搜索任意历史日志。
- Repo-pinned GitNexus index current；两份同名 Trellis index 并存时必须显式运行 `node .gitnexus/run.cjs ... --repo "$PWD"`。省略 `--repo` 的最终命令不可作为可执行证据。
- 真实 Git index 在本任务规划期间已有用户/任务 staged state。逐 slice `--staged` review 必须使用临时 `GIT_INDEX_FILE` 并验证真实 index SHA/tree 未变；该做法不修复 legacy non-staged full-worktree preflight，也不构成连续调度能力。

## Current SDK coupling to remove later

- `packages/cli/src/templates/guru/**`：Guru workflow/spec/overlay bundled mirror。
- `packages/cli/src/utils/workflow-resolver.ts`：将 Guru IDs 注册为 offline bundled workflows。
- `packages/cli/src/utils/template-fetcher.ts`：将 Guru specs 注册为 bundled specs。
- `packages/cli/src/commands/guru.ts` 与 `packages/cli/src/cli/index.ts`：fork-specific `trellis guru apply`。
- `packages/cli/src/commands/init.ts`：Guru overlay 安装提示。
- `packages/cli/src/templates/trellis/scripts/task.py` 与 `common/task_utils.py`：fork-specific blocking `before_start` lifecycle hook。
- `packages/cli/test/guru/guru-bundled.test.ts`：以 SDK bundle 为前提的大量测试；未来需迁移为 Template/Extension contract tests。

## Confirmed convergence defects

- `guru-template/overlay/verify/guru_gate.py`：Lite Overview digest 取完整 `design.md`，Detail-only 改动会让 Overview evidence stale。
- `guru-template/overlay/verify/guru_gate.py`：双 clean 只要求不同 run-id，未证明 reviewer/context 独立。
- `guru-template/overlay/verify/guru_supervise.py`：Lite/Full planning 没有 route-specific hard budget、semantic progress watchdog 或 repair 上限。
- `.trellis/spec/cli/backend/guru-overlay-gates.md`：规范要求 scope expansion 停止/重判，但 runtime 未形成完整可执行状态机。
- `guru-template/overlay/verify/tests/run_tests.sh`：现有 Lite bounded 测试主要证明 adversarial 可关闭，缺 digest metamorphic、review identity、scope expansion 和 budget/stagnation 回归。

## Frozen v1 transition baseline

- Baseline commit：`da9b9460cdf381c3abbeec608bb0c88400ea2dc2`；bundled owner tree：`ff5a13764b18f021b321f05a9c07ad05ab035c88`；`guru-bundled.test.ts` blob：`801728af418489dc504c3c4fc6237739f9373690`。
- Vitest `4.0.18` exact shard：82 total、77 passed、5 failed、0 skipped/todo；完整 sorted full-name inventory digest：`9cd2482285eac07bc163a094e8dda603bf13a283a11a6562c3a0df6403cf9ab5`。
- 五个 failure 分别是 staged implementation-review/check-commit acceptance，以及 missing/malformed/stale/mixed-scope commit-plan recovery 合同；baseline fixture 必须保存 full test name + exception class + normalized stable assertion signature，不能只保存数量。
- `bash guru-template/overlay/verify/tests/run_tests.sh` 当前 source-overlay 回归为 554 passed / 0 failed；`pnpm --filter @devsc/trellis sync:guru:check` 在 v2 divergence 前当前为 green。
- 这些五个 failure 是 Custom-v2 的非绿色 transition debt，不是 mandatory-green Gate；exact unchanged/reduced debt 对 Custom-v2 可非阻断，但 SDK/npm readiness 仍要求 legacy clean + raw mirror aligned。任何新增/变形 failure、test inventory/skip/owner-boundary 变化都阻塞。

## Session evidence

- `019f5b42-b507-7801-96ef-50b1ed01c863`：约 98 分 42 秒、2345 万 total tokens、165 模型周期、59 exec、54 wait_agent、26 followup_task，最终 planning、业务源码 0 diff。
- 本任务前置审计：在根因已经成立后仍启动多个后台审计，证明 orchestration 本身缺少“信息已经足够”的停止规则。

## Dirty-worktree exclusions

- `AGENTS.md`：用户已有修改，本任务不覆盖。
- `CLAUDE.md`：用户已有修改，本任务不覆盖。
- `marketplace`：dirty submodule，本任务不吸收、不回退。
