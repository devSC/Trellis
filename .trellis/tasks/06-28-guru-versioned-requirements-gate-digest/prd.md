# Extend requirements gate digest to track versioned requirement package

## Goal

让 requirements gate digest 纳入正式需求包(`versions/<version>/` canonical 文件),使「改正式需求包」自动触发 `confirm requirements` / requirements review 失效重跑 —— 闭合档 1/2 留下的「review 读取正式需求包但 digest 只哈希 `prd.md`」缺口(档 1 design §5、single-source §15.8)。

这是档位划分中的「档 3」。

## Background

- 现状(`guru_gate.py` 核实):`_gate_artifacts(task_dir,"requirements")`(行 969-971)只返回 `[prd.md]`;`_gate_digest`(993-1004)按 basename 哈希。
- **codex 对抗审查发现(已纳入,见 design §0)**:requirements digest **不是单一来源** —— `guru_supervise.py:755 _requirements_digest()` 是独立实现(只哈希 `prd.md`,不 import guru_gate),与 `guru_gate._gate_digest` 并存。两者现在碰巧一致(都只 prd.md),但只改 `guru_gate.py` 纳入正式需求包会让两者分叉、review 永远 stale。**故本任务范围 = `guru_gate.py` + `guru_supervise.py` + 共享 digest helper。**
- 成例:`design_package` 指针(`_package_dir` 行 468)。

## Requirements

### REQ-001: task.json `requirement_package` 指针(可选)+ 字段审计

加可选顶层字段 `requirement_package`(相对 repo root,指向版本目录如 `docs/requirements/versions/v1.0.0`)。明确为 Guru-owned 顶层字段(类比 `design_package`),design 列出已审查读者(`task.py`/`guru_gate.py`/`guru_supervise.py`/hooks)。无字段 = 现状。

### REQ-002: requirements digest 共享单一来源(解 codex blocker)

requirements digest 计算抽成**共享 helper**,`guru_gate.py` 与 `guru_supervise.py` 都调用、同口径。有 `requirement_package` 时纳入该目录 canonical 文件(减 `manifest.canonical_excludes`,默认 `snapshots`/`changes`)。改正式需求包正文 → digest 变 → confirm 失效、review 须重跑;且 supervise 写入的 review digest 与 gate 判断的 current digest 一致(不假 stale)。

### REQ-003: namespaced digest key + 结构化 artifact

digest 取材返回结构化条目 `{path, source, key}`,key = `<source>:<relpath>`(`task:`/`design:`/`requirements:`),在枚举处集中做 realpath 围栏、`canonical_root` 解析、`canonical_excludes` 过滤。**namespace 仅在该任务有 `requirement_package` 时启用**(无指针任务保持纯 basename,digest 不变);解决 codex 指出的 requirements/design `README.md` key 碰撞。

### REQ-004: digest 稳定排序

生成最终 key 后按 `(key, realpath)` 全量排序(替换 basename 排序);`os.walk` 枚举 `dirs.sort()`/`files.sort()` —— 同一文件集合不因枚举顺序产生不同 digest。

### REQ-005: manifest fail-closed

manifest **缺失** → fallback 默认;**存在但解析失败/字段非法** → `guru_gate.py requirements` 阻断 + 修复提示(不静默 fallback)。stdlib 小解析器(无 Python yaml 依赖)。

### REQ-006: 向后兼容

无 `requirement_package` 任务:requirements digest 仍只 `prd.md`、纯 basename key(digest 不变);不破坏现有 confirm/`review_runs`/失配恢复;light 链不受影响。

### REQ-007: bundled 同步 + 集成回归

改 `guru_gate.py` + `guru_supervise.py` 后 sync + 处理传染;跑 **supervisor+gate freshness 集成测试** + namespace 碰撞 + 排序稳定 + manifest fail-closed + 无指针回归。

## Out Of Scope

- **REQ-UC↔BHV 桥**(独立能力,单独 task,OQ-1)。
- 不迁移真实项目 requirements 目录(档 4)。
- 不改 review worker 读取逻辑(只改 digest 取材范围)。

## Open Questions(进入实现前需拍板)

- **OQ-1**:REQ-UC↔BHV 桥并入?**倾向不并入**(独立能力)。
- **OQ-2(已升级,codex)**:整体决策 = `namespaced key + requirement_package-root relpath + stable key sort + 共享 digest helper`(不只 relpath)。**倾向整体采纳**(codex 建议,已写入 design)。
- **OQ-3**:`requirement_package` 显式指向版本目录,gate 不自动跟 README current-development(避免歧义)。
- **OQ-4**:正式需求变更使 overview/detail 失效 —— 符合 Gate 模型,**已接受为正向**(codex 同意不算过度)。

## Acceptance Criteria

- [ ] `requirement_package` 字段支持 + design 列出读者审计。
- [ ] requirements digest 共享 helper:guru_gate + guru_supervise 同口径(集成测试:supervise clean → gate `current`;改 canonical 正文 → `stale`;改 excludes 子树 → `current`)。
- [ ] namespaced key 无碰撞(requirements `README.md` + design `README.md` 同存)。
- [ ] 稳定排序(不同枚举顺序 digest 一致)。
- [ ] manifest 缺失 fallback / 非法 fail-closed(有测试)。
- [ ] 向后兼容(无指针 digest 不变,回归测试)。
- [ ] bundled 同步;`guru_gate` + `guru_supervise` 相关测试通过或失败有据。

## Brainstorm Evidence

- Repository: `guru_gate.py` `_gate_artifacts`(961)/`_gate_digest`(993)/`_package_dir`(468);**`guru_supervise.py:755 _requirements_digest`(独立)**;`gate-confirmation-model.md`;single-source §15。
- **codex 对抗审查(gpt-5.5,见 `scratchpad/codex-review-tier3.txt`)**:[blocker] guru_supervise 独立 digest + [major]×5(namespace/结构化/排序/manifest/测试)+ [minor]×2(字段审计/OQ-2),**全部纳入**。
- Product decisions: `requirement_package` 指针;digest 共享单一来源;namespace 仅有指针启用;桥单独(OQ-1)。
- **流程**:planning 已经 codex opposite-provider 对抗审查(memory `codex-adversarial-review-before-delivery`)。
