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
