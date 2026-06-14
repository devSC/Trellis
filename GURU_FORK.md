# Guru Fork 说明（devSC/Trellis）

> 本 fork 用于打造 Guru 团队的客户端 AI 开发 SDK：Trellis 当引擎（适配/编排/验证），
> client_agent 的 Harness 知识资产当内容。需求与设计见 PRD：devSC/client_agent#1。

## 分支策略

| 分支 | 用途 | 规则 |
|------|------|------|
| `main` / `feat/*` | 上游纯镜像 | **永不直接提交**，只从 upstream 同步 |
| `guru/main` | 团队主分支（基于 feat/v0.6.0-rc @ c463533c） | 团队全部改动在此；改动尽量集中于**新增文件**（guru-template/、GURU_FORK.md 等），最小化与上游的冲突面 |

## 上游同步 SOP

```bash
git fetch upstream
git checkout main && git merge --ff-only upstream/main && git push origin main   # 镜像
git checkout guru/main && git merge upstream/main                               # 吃上游更新
# 冲突预期≈0（团队改动集中在新增文件）；若官方托管文件冲突，以上游为准后重放团队补丁
```

## AGPL-3.0 义务（上游 license）

- 本 fork 为修改版：团队内分发（任何拿到二进制/包的成员）必须可获得对应源码——**本 fork 仓库本身即满足**，保持成员可访问。
- 不得以闭源形式将修改版作为网络服务对外提供（AGPL §13）。
- 保留上游 COPYRIGHT / LICENSE 文件，不移除版权声明。

## 团队改动登记

| 日期 | 改动 | 关联 issue |
|------|------|-----------|
| 2026-06-12 | 建立 guru/main 基线 + 本说明文件 | client_agent#2 |
| 2026-06-14 | 多平台扩展：go/ios/h5 三平台 spec+workflow+skills（references/grill 全套）；CLI 数据驱动 wiring + OCR 加固；bump `guru.2` | client_agent#1 |

## 包发布（GitHub Packages）

| 包 | 用途 |
|----|------|
| `@devsc/trellis` | CLI（bin: `trellis`/`tl`），内置 4 平台 workflow（guru-client/go/ios/h5）与 spec（guru-flutter-client/go-backend/ios-native/h5-web），离线可用 |
| `@devsc/trellis-core` | CLI 的运行时依赖（经 npm alias `@mindfoldhq/trellis-core` 引用，源码 import 零改动） |

版本策略：跟随上游 + guru 后缀（如 `0.6.0-rc.0-guru.1`）。当前 **`0.6.0-rc.0-guru.2`**（新增 go/ios/h5 三平台 bundled spec+workflow+skills）。

```bash
# 发布（需 PAT 含 write:packages；用 --ignore-scripts 跳过会跑测试的 prepublishOnly）
npm login --registry=https://npm.pkg.github.com   # 或 ~/.npmrc 配 //npm.pkg.github.com/:_authToken=<PAT>
# prerelease 版本必须带 --tag（实测：缺省报 "must specify a tag"）
# 先发 core（cli 的运行时依赖）：
pnpm -C packages/core publish --tag guru --no-git-checks
# 再发 cli。务必先 build 新鲜 dist + cp README/LICENSE，且必须用 pnpm publish（非 npm publish）——
# pnpm 会把 workspace:@devsc/trellis-core@* 替换成已发布的具体版本，npm publish 不会替换，
# 会把 workspace: 协议带进发布产物，下游 `npm i` 直接失败。
pnpm -C packages/cli build && cp README.md LICENSE packages/cli/
pnpm -C packages/cli publish --tag guru --ignore-scripts --no-git-checks
# 注意：需 PAT(classic) 含 write:packages —— gh CLI 的 OAuth token 无此 scope（实测 403）

# 团队安装（一次性 ~/.npmrc）：
#   @devsc:registry=https://npm.pkg.github.com
#   //npm.pkg.github.com/:_authToken=<read:packages PAT>
npm i -g @devsc/trellis

# 内容更新流：改 guru-template/ → pnpm -C packages/cli sync:guru → bump guru.N → publish
```
