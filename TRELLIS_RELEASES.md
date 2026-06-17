# Trellis Guru Fork — 发布、更新与维护指南

## 概述

本文档记录 devSC/Trellis guru/main 分支的发布、包管理、上游同步与日常维护流程。

guru/main 是 Guru 团队定制的 Trellis 分支。当前 `0.6.0-guru.1` 基于官方 `v0.6.0` GA：官方 common 层采用 `0.6.0.json` migration manifest、`trellis-channel` bundled skill、刷新后的 `trellis-meta`、`trellis mem` / `trellis channel` / `@mindfoldhq/trellis-core` SDK 能力；Guru 差异保留在 `guru-template/**`、`packages/cli/src/templates/guru/**`、overlay/Gate 机制、GitHub Packages 私有发布路径与本仓库 dogfood `codex.dispatch_mode: sub-agent`。

Guru fork 包含以下核心引擎级改造：

1. **Bundled Guru workflows** — `guru-client` / `guru-go` / `guru-ios` / `guru-h5` 离线可用五阶段工作流模板
2. **Bundled Guru specs** — Flutter / Go / iOS / H5 项目规范集（conventions / guides / harness）
3. **Guru overlay + Gate** — `before_start` 硬 Gate、`guru_gate.py` confirm / grill digest、平台红线 hooks
4. **Packet-first design-grill** — `Design Grill Packet` 批量发现问题，独立 `NORMAL` 项可批量批准，BLOCKER/红线/依赖项仍逐项确认
5. **Fork release path** — `@devsc/*` GitHub Packages、registry-aware preflight、packed alias 校验

---

## 版本策略

### 版本号格式

```
<上游版本>-guru.<增量编号>
示例: 0.6.0-guru.1, 0.6.0-guru.2
```

- **上游版本部分** 跟随 upstream 官方版本；`0.6.0-guru.1` 基于官方 tag `v0.6.0`
- **-guru 后缀** 标记为 Guru 定制版本
- **增量编号** 每个 guru 发布递增（不重置）

### 包发布目标

| 包 | 发布地 | Scope |
|----|--------|-------|
| `@devsc/trellis` | GitHub Packages | CLI 工具（含 bundled 模板） |
| `@devsc/trellis-core` | GitHub Packages | 运行时库 + 类型定义 |

---

## 发布前清单

### 1. 代码准备

#### 1.1 验证所有改动已推送

```bash
cd /Users/devSC/Documents/MyProject/Trellis
git status
# 应显示 "working tree clean"

git branch -vv
# 应显示 guru/main 同步于 origin/guru/main
```

#### 1.2 运行完整测试套件

```bash
pnpm -C packages/cli test --run
# 期望: 测试通过；若失败，按当前输出确认是否为环境或 submodule 前置问题
```

#### 1.3 运行 apply.sh 端到端测试

```bash
bash guru-template/overlay/tests/apply_test.sh
# 期望: overlay 安装/升级场景全部通过
```

#### 1.4 验证 sync:guru 脚本完整性

```bash
pnpm -C packages/cli sync:guru
git diff packages/cli/src/templates/guru/
# 应无差异或仅有预期的次要更新
```

#### 1.5 运行 release preflight

```bash
node packages/cli/scripts/release-preflight.js check-versions
node packages/cli/scripts/release-preflight.js publish-plan --json
node packages/cli/scripts/release-preflight.js verify-packed-cli
```

- `publish-plan` 读取 `publishConfig.registry`，Guru 包必须指向 `https://npm.pkg.github.com`，`0.6.0-guru.N` 必须使用 `guru` dist-tag。
- `verify-packed-cli` 必须确认 CLI 的 `@mindfoldhq/trellis-core` alias 打包后解析为 `npm:@devsc/trellis-core@<同版本>`，不能落回官方 core。
- manifest 连续性分两类：`check-manifest-continuity.js --official` 检查官方 public npm；默认模式检查当前 Guru 包，并把 `0.6.0-guru.1` 映射到 `0.6.0.json` 基线 manifest。

### 2. 版本更新

#### 2.1 决定新版本号

假设当前版本为 `0.6.0-guru.1`，发布新版本为 `0.6.0-guru.2`：

```bash
cd /Users/devSC/Documents/MyProject/Trellis

# 更新 packages/cli/package.json
# "version": "0.6.0-guru.2"

# 更新 packages/core/package.json
# "version": "0.6.0-guru.2"
```

也可以使用 `packages/cli/scripts/bump-versions.js` 统一改写 CLI/core 版本；不要只改一个 package。

#### 2.2 更新 GURU_FORK.md 团队改动登记

在 `/Users/devSC/Documents/MyProject/Trellis/GURU_FORK.md` 的"团队改动登记"表添加一行：

```markdown
| 日期 | 改动 | 关联 issue | 发布版本 |
|------|------|-----------|---------|
| 2026-06-16 | 迁移到官方 v0.6.0 GA，保留 Guru overlay/Gate，更新 design-grill packet-first 合同 | Trellis task | 0.6.0-guru.1 |
| 2026-06-XX | <新改动说明> | <issue链接> | 0.6.0-guru.2 |
```

### 3. Git 提交与标签

#### 3.1 创建版本提交

```bash
git add packages/cli/package.json packages/core/package.json GURU_FORK.md
git commit -m "chore(release): prepare 0.6.0-guru.2

- @devsc/trellis @ 0.6.0-guru.2
- @devsc/trellis-core @ 0.6.0-guru.2

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

#### 3.2 创建 Git 标签（可选，推荐）

```bash
git tag -a v0.6.0-guru.2 -m "Release @devsc/trellis@0.6.0-guru.2"
git push origin guru/main --tags
```

---

## NPM 包发布流程

### 前置要求

1. **GitHub PAT Token** 配置
   - 需要 classic PAT（非 OAuth token）
   - 必须含 `write:packages` scope
   
   检查/配置 `~/.npmrc`：
   ```
   registry=http://registry.npmjs.org/
   @devsc:registry=https://npm.pkg.github.com
   //npm.pkg.github.com/:_authToken=<你的classic PAT>
   ```
   
   或通过交互式登录：
   ```bash
   npm login --registry=https://npm.pkg.github.com
   # 输入: 用户名 (devSC)
   #      密码 (粘贴 classic PAT)
   #      邮箱 (laikfomo@outlook.com)
   ```

2. **本地编译** ✅
   ```bash
   pnpm -C packages/core build
   pnpm -C packages/cli build
   ```

### 发布步骤

#### Step 1: 发布 trellis-core

```bash
cd /Users/devSC/Documents/MyProject/Trellis/packages/core

# 方案 A: 标准发布
pnpm publish --tag guru --no-git-checks

# 方案 B: 跳过 publish scripts（仅用于已手动完成测试/构建的紧急重发，需谨慎）
#         需先手动运行: pnpm test && pnpm build
pnpm publish --tag guru --ignore-scripts --no-git-checks
```

**期望输出：**
```
npm notice Published @devsc/trellis-core@0.6.0-guru.2 to https://npm.pkg.github.com
```

#### Step 2: 发布 trellis CLI

```bash
cd /Users/devSC/Documents/MyProject/Trellis/packages/cli

# 方案 A: 标准发布（会跑 prepublishOnly 的测试/构建）
pnpm publish --tag guru --no-git-checks

# 方案 B: 跳过 prepublishOnly（仅用于已手动完成测试/构建的紧急重发）
#         需先手动运行: pnpm test && pnpm build && cp ../../README.md ../../LICENSE .
pnpm publish --tag guru --ignore-scripts --no-git-checks
```

不要用 `npm publish` 发布 CLI 包：npm 不会把
`workspace:@devsc/trellis-core@*` 改写成发布产物需要的
`npm:@devsc/trellis-core@<version>` alias，容易生成下游无法安装的包。

**期望输出：**
```
npm notice Published @devsc/trellis@0.6.0-guru.2 to https://npm.pkg.github.com
```

### 发布验证

发布成功后，在本地或新环境验证安装可用性：

```bash
# 清空全局 @devsc/trellis（如已安装）
npm uninstall -g @devsc/trellis

# 重新安装最新 guru 版本
npm install -g @devsc/trellis@guru --registry https://npm.pkg.github.com

# 验证 CLI 可用
trellis --version
trellis init --help
```

---

## 上游同步流程

guru/main 定期需要与 upstream main 或后续稳定分支同步，获取上游的 bug 修复与新特性。

### 同步 SOP（按 GURU_FORK.md）

```bash
cd /Users/devSC/Documents/MyProject/Trellis

# Step 1: 更新所有 upstream 分支
git fetch upstream

# Step 2: 更新 main 分支（镜像）
git checkout main
git merge --ff-only upstream/main
git push origin main

# Step 3: 合并到 guru/main
git checkout guru/main
git merge upstream/main
# 或如果有冲突:
# git merge --no-ff upstream/main
# (解决冲突后)
# git commit
```

### 冲突处理

guru/main 的改动集中在新增文件，与 upstream 的冲突面应该很小。若发生冲突：

1. **查看冲突文件**
   ```bash
   git status
   ```

2. **以 upstream 版本为准，之后重新应用 guru 补丁**
   ```bash
   # 对托管文件（如 project-detector.ts），保持 upstream 版本
   git checkout --ours <file>
   
   # 对 guru 新增文件（guru-template/, 改动的 index.ts 等），保持 guru 版本
   git checkout --theirs <file>
   ```

3. **完成合并**
   ```bash
   git add .
   git commit -m "chore(guru): merge upstream/main into guru/main

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
   ```

### 合并后验证

```bash
# 运行完整测试
pnpm -C packages/cli test --run

# 如测试失败，可能需要调整 guru 侧的改动以适配上游变化
# 修复后重新运行 apply_test.sh
bash guru-template/overlay/tests/apply_test.sh
```

---

## 日常维护

### Guru 模板内容更新

guru-client workflow 与 guru-flutter-client spec 的 SSOT 在 `guru-template/` 目录。

修改后需同步到 CLI 编译版本：

```bash
# 编辑 guru-template/workflows/guru-client-workflow.md 或 guru-template/specs/guru-flutter-client/*

# 同步到 packages/cli/src/templates/guru/
pnpm -C packages/cli sync:guru

# 验证
git diff packages/cli/src/templates/guru/
# 应显示更新内容

# 提交
git add guru-template/ packages/cli/src/templates/guru/
git commit -m "docs(guru): update workflow/spec templates

<具体改动说明>

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### apply.sh 与 install 脚本维护

guru-template/overlay/ 包含安装/升级器脚本（apply.sh + verify/ 目录）。

若需修改：

1. **编辑脚本**
   ```bash
   # 编辑 guru-template/overlay/apply.sh
   # 编辑 guru-template/overlay/verify/guru_gate.py
   ```

2. **本地测试**
   ```bash
   bash guru-template/overlay/tests/apply_test.sh
   # 期望 overlay 安装/升级场景全部通过
   ```

3. **提交**
   ```bash
   git add guru-template/overlay/
   git commit -m "fix/feat(guru): <脚本改动说明>"
   ```

### 处理客户端反馈

client_agent 项目使用 guru/main 的 Trellis 版本。若接到反馈：

1. **复现问题**（在 guru/main 本地验证）
2. **定位改动所属** 三类：
   - **CLI 代码** (packages/cli/src/) → 直接修改
   - **Core 库** (packages/core/src/) → 直接修改
   - **模板/脚本** (guru-template/) → 修改后 sync:guru
3. **验证修复**
   ```bash
   pnpm -C packages/cli test --run
   bash guru-template/overlay/tests/apply_test.sh
   ```
4. **发布新版本**（按上述发布流程）

---

## 故障排查

### Issue: "prepublishOnly 报错"

**症状：** `npm publish` 时测试或构建失败，导致发布中止。

**解决：**
1. 在本地修复问题（通常是测试失败）
2. 重新运行 `pnpm -C packages/cli test --run` 确保通过
3. 重新运行 `pnpm -C packages/cli build`
4. 再次尝试 `npm publish`

或使用 `--ignore-scripts` 跳过（仅当确信已在本地验证过）：
```bash
pnpm -C packages/cli test --run && pnpm -C packages/cli build && \
cp ../../README.md ../../LICENSE . && \
npm publish --tag guru --ignore-scripts
```

### Issue: "marketplace submodule 测试失败"

**症状：** 测试套件失败，错误涉及 `marketplace/workflows/native/workflow.md`。

**说明：** 这是预期的失败（marketplace 与 docs-site 是 git submodule，本地开发环境无需初始化），与 guru/main 改动无关。

**影响：** 不影响发布；发布后安装/使用完全正常。

### Issue: "sync:guru 更新超出预期"

**症状：** `pnpm -C packages/cli sync:guru` 产生大量不预期的改动。

**原因：** 可能 guru-template/ 与 bundled 版本不同步。

**解决：**
```bash
# 检查差异
git diff guru-template/ packages/cli/src/templates/guru/

# 若是意外改动，撤销
git checkout packages/cli/src/templates/guru/

# 重新同步
pnpm -C packages/cli sync:guru
```

---

## AGPL-3.0 合规清单

本 fork 遵循上游的 AGPL-3.0 license。发布时需确保：

- [ ] 保留上游的 COPYRIGHT 与 LICENSE 文件
- [ ] 本 fork 仓库保持可公开访问（团队成员可获取源码）
- [ ] 不以闭源形式将修改版作为网络服务对外提供（AGPL §13）
- [ ] 如用于网络服务，需在服务中暴露源码获取地址

---

## 快速参考

### 发布一个新版本的典型命令序列

```bash
# 1. 进入 Trellis 根目录
cd /Users/devSC/Documents/MyProject/Trellis

# 2. 验证状态
git status  # 应为 "working tree clean"
git branch -vv  # 应为 "guru/main up to date with origin/guru/main"

# 3. 运行完整测试
pnpm -C packages/cli test --run
bash guru-template/overlay/tests/apply_test.sh

# 4. 更新版本号（编辑 package.json）
# packages/cli/package.json: "version": "0.6.0-guru.2"
# packages/core/package.json: "version": "0.6.0-guru.2"

# 5. 运行 release preflight
node packages/cli/scripts/release-preflight.js check-versions
node packages/cli/scripts/release-preflight.js publish-plan --json
node packages/cli/scripts/release-preflight.js verify-packed-cli

# 6. 提交版本提交
git add packages/cli/package.json packages/core/package.json GURU_FORK.md
git commit -m "chore(release): prepare 0.6.0-guru.2"

# 7. 构建（会在 publish 时自动做，这里显式提前构建以检查）
pnpm -C packages/core build
pnpm -C packages/cli build

# 8. 发布到 npm（GitHub Packages）
( cd packages/core && pnpm publish --tag guru --no-git-checks )
pnpm -C packages/cli build && cp README.md LICENSE packages/cli/
( cd packages/cli && pnpm publish --tag guru --ignore-scripts --no-git-checks )

# 9. 推送 Git 提交
git push origin guru/main

# 10. 验证安装
npm install -g @devsc/trellis@guru --registry https://npm.pkg.github.com
trellis --version
```

### 与上游同步的典型命令序列

```bash
cd /Users/devSC/Documents/MyProject/Trellis

git fetch upstream
git checkout main && git merge --ff-only upstream/main && git push origin main
git checkout guru/main && git merge upstream/main

# 若有冲突，解决后:
git commit -m "chore(guru): merge upstream/main"

# 验证
pnpm -C packages/cli test --run
bash guru-template/overlay/tests/apply_test.sh

# 若无问题，推送
git push origin guru/main
```

---

## 联系与支持

- **项目 CONTEXT**: 见 client_agent CONTEXT.md
- **技术决策**: 见 GURU_FORK.md
- **发布历史**: 本文档下方维护版本日志

---

## 版本日志

| 版本 | 发布日期 | 说明 |
|------|---------|------|
| 0.6.0-guru.1 | 2026-06-16 | 迁移到官方 `v0.6.0` GA：采用 `0.6.0.json` manifest、`trellis-channel`、刷新 `trellis-meta`，保留 Guru overlay/Gate/offline 工作流与私有发布路径 |
| | | - `design-grill` 改为 bounded `Design Grill Packet` 合同 |
| | | - root scripts 改用 `@devsc/*` + `--fail-if-no-match` |
| | | - release-preflight 改为 registry-aware，并验证 packed CLI alias 指向 `npm:@devsc/trellis-core@<version>` |
| 0.6.0-rc.0-guru.1 | 2026-06-13 | 初始发布：Phase 3-5 引擎级定制完整化（bundled 模板 + 健壮性修复 + @devsc 包化） |
| | | - Bundled guru-client workflow |
| | | - Bundled guru-flutter-client spec (16 文件) |
| | | - Submodule 初始化检测 |
| | | - 智能 JSON 合并 (settings.json + AGENTS.md) |
| | | - 可配置超时与重试 |
| | | - apply.sh 安装/升级器 (14 用例验证) |

---

**文档维护者**: devSC  
**最后更新**: 2026-06-16
**License**: AGPL-3.0 (与上游一致)
