---
name: trellis-local
description: "本仓库的 Trellis 团队定制登记（guru-template）。记录 Guru 客户端五阶段 Harness 在本项目的全部定制：spec 库、workflow、skills、hooks、verify gates。任何后续 Trellis 定制都必须更新本文件（官方自我迭代原则）。"
---

# Trellis Local — Guru 客户端 Harness 定制登记

> 来源：guru-template（devSC/Trellis fork，guru/main）· PRD：devSC/client_agent#1
> 原则：每次修改 Trellis 行为 → 更新本文件（官方 self-iteration-guide）。

## Customizations Summary

- **Specs**: 1 个库（guru-flutter-client）→ `.trellis/spec/`：`harness/`（五阶段 SSOT：概要归属判定/详细合同八问+L2×3/实现 trace/萃取九段）、`guides/golden-path.md`（通用方法）、`conventions/`（项目约定槽位 + 本项目取值 `project-conventions.md`）
- **Workflow**: 替换为 guru-client 五阶段（需求→概要→详细→实现→审核映射进 planning/in_progress；Phase 1 含需求确认、概要/详细 review Gate 与详细确认）
- **Skills**: 8 个 `client-*`（`.agents/skills/`）+ shared legacy `design-grill`：design-overview/detail 的 writing+review、flutter-implementation 的 writing+review、small-iteration-dev（入口分流）；Domain Grill 已前移到需求发现，`design-grill` 仅作旧项目兼容 wrapper。
- **Hooks**: `after_create` → `guru_after_create.py`（jsonl 自动注入项目约定/golden-path/harness 基线条目）；平台 PreToolUse（l10n 同步拦截 / SLOT-12 老目录拦截 / 制裁 TLD / `task.py start` 前确认拦截 / 未进入实现期或未 clean review 的 `git commit` 拦截）；Codex 专属 hook 由 Guru overlay apply 在目标存在 `.codex/` 时写入 `.codex/hooks.json`
- **Verify**: `guru_gate.py auto` 进 `worktree.yaml verify`（phase 感知当前 artifact 渐进验证；exit 0 不代表五阶段全部完成）
- **Agents**: 0 新增（复用官方 channel/sub-agent 机制，经 `guru_supervise.py overview/detail/implement-check` 指明 guru 口径 skill）
- **Language**: task 产物与 findings 中文优先（英文仅限标识符/命令/路径/专有名词；commit message 跟随仓库历史风格）——落点：workflow Planning Artifacts/Guardrails/breadcrumb 块 + harness/index Checklist

## 关键约定

1. 规则唯一真源在 `.trellis/spec/`；skills/workflow/hooks 只做编排与装载，不复写规则正文。
2. 项目级取值只住 `.trellis/spec/conventions/project-conventions.md`（槽位机制）；缺失时各硬前置与 hook 会警告/拦截。
3. 存量豁免：审核按约定文件 SLOT-15 清单判定（清单内记债不阻塞、清单外新增阻塞）。
4. 三条最高禁令与合规 STOP 见 workflow Guardrails；Codex 需要用户级 `[features].hooks=true` 与 `/hooks` trust 才会执行 PreToolUse hook，命令级 SSOT 仍是 `guru_gate.py check-start|check-implementation|check-commit`。

## Changelog

| 日期 | 变更 | 关联 |
|------|------|------|
| 2026-06-12 | 初版：五阶段 Harness 全套定制落地 | client_agent#4 #5 #6 #7 |
| 2026-06-12 | 编号纪律+trace-matrix；产物语言中文优先 | client_agent#14 |
| 2026-06-12 | legacy design-grill 兼容提示接入；新流程的 Domain Grill 已前移到需求发现，不再作为概要/详细 Gate | — |
| 2026-06-19 | 详细设计 Gate 增加 L1 骨架假绿回归拦截；detail clean review 必须记录 deletion audit；四端 detail writing/review skills 增加删除审计与破坏性压缩保护 | devSC/Trellis#6 |
| 2026-06-30 | 生命周期 Gate 拆分为 check-start / check-implementation / check-commit；新增 Claude/Codex git commit hook，防止 START_READY 被误当实现或提交许可 | 019f171a 根因修复 |
