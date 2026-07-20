# Install Guru bug fast path skill

## Goal

将已审查完成的单文件 `guru-bug-fast-path` Skill 纳入 Trellis Guru overlay 的共享安装链。目标项目执行 `trellis guru apply <platform>` 后，无论选择 Flutter、Go、H5 还是 iOS，都能在 `.agents/skills/` 与 `.claude/skills/` 中获得内容一致的 Skill。

该 Skill 属于 Guru 系能力，不进入 Trellis 通用 bundled Skills，也不进入公共 Marketplace。

## Requirements

### REQ-001 Preserve the reviewed Skill

- 以 `/Users/devSC/.agents/skills/guru-bug-fast-path/SKILL.md` 为本次导入来源。
- Guru source overlay 与 CLI template overlay 各保留一份字节一致的单文件 Skill。
- 不引入 Python 脚本、额外 reference 文件或运行时控制器。

### REQ-002 Install as a shared Guru Skill

- 将 `guru-bug-fast-path` 注册为 Guru shared Skill，不绑定单一平台。
- `apply.sh` 对 Flutter、Go、H5、iOS 都必须将其安装到 `.agents/skills/guru-bug-fast-path/`。
- 默认平台镜像流程还必须安装到 `.claude/skills/guru-bug-fast-path/`。
- 切换平台、剪枝或重复 apply 不得删除该 shared Skill。

### REQ-003 Keep mirrors and inventory current

- `guru-template/overlay/**` 与 `packages/cli/src/templates/guru/overlay/**` 保持镜像一致。
- 更新 `trellis-local` 的 Guru Skill 清单与变更记录。
- CLI npm 包必须包含该 Skill。

### REQ-004 Add focused regression coverage

- 现有 Guru bundled 集成测试应证明 Skill 被打包。
- 对每个支持平台执行 overlay apply，证明两个 Skill 根均存在且内容一致。
- 重复 apply 后结果保持一致。

### REQ-005 Install into confirmed sibling targets

- 将当前已验证的 Guru overlay 安装到 `/Users/devSC/Documents/JobProject/guru_ai_himora`，平台为 Flutter。
- 将当前已验证的 Guru overlay 安装到 `/Users/devSC/Documents/MyProject/safe_land_web`，平台为 H5。
- 保留两个目标仓库既有工作区改动，不提交、暂存、推送或归档目标仓库。
- 安装后验证两个 Skill 根与 Guru source overlay 的 SHA-256 和文件内容完全一致。

### REQ-006 Install from the complete Guru release ancestry

- 安装源分支必须包含 `guru-v0.6.7.1` / `042a5f34ed3961dcb1a07ca146d18ec2f4824c91`，不能只从分叉点 `cce44df6` 的旧快照构建。
- 当前分支与发布分支满足 fast-forward 条件时，使用 `git merge --ff-only`，保留发布分支的完整 20 提交祖先链，不只 cherry-pick 最后一条 workflow 修复。
- 合并前确认发布分支 113 个变更路径与当前未提交/未跟踪路径无重叠；保留当前 Skill 和用户既有工作区改动。
- 补齐发布分支遗留的 Guru source/template mirror 漂移，使 `sync:guru:check` 通过后再重新 build 和安装兄弟包。
- 重装后验证兄弟包中的 workflow 来自 `042a5f34` 当前模板，同时重新验证 `guru-bug-fast-path` 两个 Skill 根。

### REQ-007 Keep the 0.6.7 reinstall entrypoint layout-independent

- `reinstall-official-067.sh` 必须能从 canonical `guru-template/overlay` 和 CLI `src/dist/templates/guru/overlay` 两种布局读取当前 overlay、workflow 与 spec。
- source 测试与 CLI mirror 测试都必须使用各自相邻的 `templates/guru` 根，不能硬编码 `repo/guru-template`。
- 修复后重新同步 package peer，并分别执行 source/package 重装回归。

### REQ-008 Migrate approved historical managed Skills during direct apply

- direct `guru apply` 必须识别经真实字节 provenance 验证的历史托管 `guru-bug-fast-path` 版本，而不是把合法升级误判为用户自有同名 Skill。
- 批准集合仅包含 `a05f456ee66ea001ae408f74692d1ee96dc0006524eabbfd990ef0930c1b3212` 与 `d7df7d1d0f53e5b529c530ffa3e82340b0e7543cac4b7abbd2278ee9912b3242`；不得加入 rejected、intermediate 或目标仓库私有摘要。
- 未知同名 Skill 必须在正常目标写入前 fail-closed，并保留用户文件。
- 两份 `apply.sh` 与 direct apply 聚焦回归必须保持镜像一致；回归应使用两个历史版本的真实完整字节，而不是只验证摘要常量。

### REQ-009 Preserve dirty-checkout provenance and the complete target Git index

- dirty source checkout 不得以 Git commit 冒充实际安装内容；必须使用可复核的 template-tree 字节摘要。
- 重装前后的 target Git index 必须同时核对 stage/assume-unchanged、skip-worktree、resolve-undo、ITA visible/invisible，以及原始 index 字节和路径边界。
- linked worktree、非 UTF-8 路径、冗余路径分隔符、回滚和保护性 Spec/Skill 冲突不得削弱 provenance 或 index 完整性断言。
- 安装器的保护性冲突退出状态不得报告为完全成功，也不得误报为回滚失败；必须保留结构化 reconcile 报告。

## Acceptance Criteria

- [x] 两份 overlay 中的 `guru-bug-fast-path/SKILL.md` 均通过 Skill Creator 校验且内容一致。
- [x] `SHARED_SKILLS` 明确包含 `guru-bug-fast-path`。
- [x] Flutter、Go、H5、iOS apply 后，`.agents/skills` 与 `.claude/skills` 均存在该 Skill，且与模板内容一致。
- [x] 同平台重复 apply 后该 Skill 不漂移；跨平台 apply 后不会被剪枝。
- [x] CLI tarball 包含 `dist/templates/guru/overlay/agents-skills/guru-bug-fast-path/SKILL.md`。
- [x] `guru_ai_himora` 的 `.agents/skills` 与 `.claude/skills` 已安装一致的 `guru-bug-fast-path`。
- [x] `safe_land_web` 的 `.agents/skills` 与 `.claude/skills` 已安装一致的 `guru-bug-fast-path`。
- [x] 当前分支已 fast-forward 到 `042a5f34`，`git merge-base --is-ancestor 042a5f34 HEAD` 返回成功。
- [x] `042a5f34` 合并后的 CLI 已重新构建并重新安装到两个兄弟包，且目标 workflow 与当前模板一致。
- [x] `pnpm --filter @devsc/trellis run sync:guru:check`、聚焦 Vitest、`git diff --check` 全部通过。
- [x] canonical 与 CLI template 两种布局下的 `reinstall_official_067_test.sh` 均通过。
- [x] direct apply 能迁移两个批准历史版本，未知同名 Skill 仍在正常目标写入前 fail-closed。
- [x] source/package 重装回归覆盖 dirty checkout、logical/raw index、linked worktree、非 UTF-8 路径、回滚及保护性冲突。
- [x] 两个目标仓库的 Git index 在重装前后逐通道一致，既有工作区和 Safe Land 脏 submodule 均被保留。

## Verification Evidence

- Skill Creator：两份 Skill 均为 `Skill is valid!`。
- 当前 Skill SHA-256：个人源、Guru source overlay、CLI src/dist template overlay 均为 `90c6fe600fe81e310fb299d5c59e667dd7fb2586dfe891fa5e30abc2ecc1b20a`。
- direct apply 独立验收：两个批准历史 Skill 的真实完整字节均已解压、校验并执行迁移；聚焦 Vitest 为 `3 passed / 84 skipped`，未知同名 Skill 保护路径通过。
- direct apply 独立只读终审：`Verdict: PASS`，无 P1/P2；两份 `apply.sh` 与 dist 镜像 SHA-256 均为 `f3a72ca913a6967d3fffce5ff20a4170053fe51f9bb53835c4d5ae14dfa2e000`。
- Source overlay apply 回归：125/125 通过。
- CLI build / TypeCheck：通过。
- GitNexus 当前未提交范围 detect-changes：12 files、`risk=low`，0 个 execution process 受影响；symbol mapping 会随本地索引刷新变化，不作为稳定验收字段。
- `git diff --check`：通过。
- 全包 lint：仍命中 `packages/cli/test/guru/guru-bundled.test.ts:1497` 的既有 `no-useless-escape` 基线债务；当前任务 diff 未触及该行，未引入新的 lint finding。
- Source/package 官方 0.6.7 E2E：两套均退出 `0` 并输出 `REINSTALL_067_TEST_OK official=0.6.7 dry_run=pass detached_package=pass byte_provenance=pass rollback=pass success=pass spec_conflict=pass skill_conflict=pass`。
- Sibling reinstall：`guru_ai_himora` 与 `safe_land_web` 均完成官方 `@mindfoldhq/trellis@0.6.7` 重装；保护性冲突被报告为 `candidate usable with manual reconciliation`，没有误报为无冲突成功或回滚失败。
- Sibling Skill digest：两个目标仓库的 `.agents` / `.claude` 共四份 Skill 均为 `90c6fe600fe81e310fb299d5c59e667dd7fb2586dfe891fa5e30abc2ecc1b20a`，与 Guru source overlay 字节一致。
- Sibling Skill validation：两个目标仓库的 `.agents` / `.claude` 共四份均通过 Skill Creator `quick_validate`。
- Sibling workflow/platform：Himora workflow 与 `guru-client-workflow.md` 一致且 `guru.platform=flutter`；Safe Land workflow 与 `guru-h5-workflow.md` 一致且 `guru.platform=h5`；两个目标的 `get_context.py` smoke 通过。
- Target index：Himora 的 stage 两通道为 `48850594c9313a7836581ae7e5c0d758d4104d37a393ab7f7013ed0f94002be8`、resolve-undo 为 `62e06d122ea15703ce9b703f848b8c82c7945283f9923ad2d6cfd9fb48ea90b0`、ITA 两通道为空摘要；Safe Land 的 stage 两通道为 `a4b19d81270bb9fdf7641b402597195ca41c2bf0e6c22cb8c0311407a57e50b3`，其余三通道为空摘要。两仓均与重装前一致。
- Reconcile evidence：Himora 保留 2 个 Spec 与 3 个 Skill 冲突报告；Safe Land 保留 1 个 Spec、0 个 Skill 冲突报告；项目专属文件及 Safe Land 两个既有脏 submodule 均被保留。
- Release ancestry root cause：首次安装时当前 `HEAD=cce44df6`，而 `042a5f34` 仅存在于 `codex/guru-v0.6.7.1-install-hotfix-20260718`，不是当前分支祖先；安装器只构建当前工作树，不会自动合并其他分支。该发布分支从 `cce44df6` 起独有 20 个提交，因此首次安装使用了错误的旧 workflow 快照。
- Release ancestry correction：已确认 113 个发布分支变更路径与当前 34 条脏路径零重叠，并通过 `git merge --ff-only codex/guru-v0.6.7.1-install-hotfix-20260718` 将当前分支移动到 `042a5f34`，没有创建额外 merge commit。
- Source/template parity：`sync:guru:check` 通过；apply、reinstall、E2E test 与 fast-path Skill 的 source/src/dist 三面镜像逐字节一致。

## Out of Scope

- 不修改 `guru-bug-fast-path` 的行为规则，除非安装兼容性验证证明有必要。
- 不修改项目级 `tapd-bug-fix` Skill。
- 不发布到公共 Marketplace。
- 不推送、不合并；两个目标仓库仍不得提交、暂存、推送或归档。
- 当前 source 任务的 Spec 更新、工作提交、任务归档和 `finish-work` 已由用户于 2026-07-20 明确授权。

## Brainstorm Evidence

- Skill loaded: `trellis-start`, `trellis-meta`, `trellis-brainstorm`
- Repository evidence inspected:
  - `/Users/devSC/.agents/skills/guru-bug-fast-path/SKILL.md`
  - `guru-template/overlay/apply.sh`
  - `packages/cli/src/templates/guru/overlay/apply.sh`
  - 两份 `overlay/agents-skills/` 目录
  - 两份 `overlay/trellis-local/SKILL.md`
  - `packages/cli/test/guru/guru-bundled.test.ts`
  - `.trellis/spec/cli/backend/guru-overlay-gates.md`
  - `.trellis/spec/cli/unit-test/conventions.md`
- Domain/terminology triggers: 已确认。这里的“Guru 系子 Skill”解释为 Guru overlay 管理的 shared Skill，不是 Trellis 通用 bundled Skill，也不是 Marketplace Skill。
- Current code vs user intent conflicts: 当前 overlay 未包含该 Skill，且 `apply.sh` 的 `SHARED_SKILLS` 未注册它；仅复制目录会导致非平台前缀 Skill 被剪枝。
- Product decisions confirmed:
  - 用户要求将新增 Skill 作为 Trellis Guru 系子 Skill 安装。
  - 用户明确选择 `micro_task` 覆盖原 `lite_task / medium` 推荐并要求继续推进。
- Open product/scope/risk questions: 无。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
