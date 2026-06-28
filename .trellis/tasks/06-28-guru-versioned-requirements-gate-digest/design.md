# Design: Extend requirements gate digest to versioned requirement package

> 改 `guru_gate.py` **+ `guru_supervise.py`**(overlay/verify)。结构/manifest:single-source §15。

## 0. codex 对抗审查修正(2026-06-28,gpt-5.5 opposite-provider)

codex 审查发现并已纳入(原方案只改 guru_gate.py、basename key、静默 fallback 均被推翻):

- **[blocker]** requirements digest 不是单一来源:`guru_supervise.py:755 _requirements_digest()` 独立实现(只 prd.md,不 import guru_gate)。只改 guru_gate.py → 两者分叉 → review 永远 stale。**→ 抽共享 helper,两脚本同口径。**
- **[major]** digest key 无 namespace → 正式需求包 `README.md` 与 design_package `README.md` 碰撞 → **namespaced key**。
- **[major]** 在 `_gate_digest` 反推文件来源边界不稳 → **枚举阶段返回结构化 `{path, source, key}`**,集中 realpath 围栏/canonical_root/exclude/key。
- **[major]** 排序按 basename 不稳(os.walk + 重复 basename)→ **按 key 全量排序 + walk sort**。
- **[major]** manifest 静默 fallback 掩盖配置错 → **缺失 fallback / 非法 fail-closed**。
- **[major]** 测试漏 supervisor+gate freshness 链路 → **加集成测试**。
- **[minor]** 字段读者审计;OQ-2 升级为完整决策。

## 1. Approach

加 task.json `requirement_package` 指针(类比 `design_package`);requirements digest 计算抽成**共享 helper(单一来源)**,`guru_gate.py` 与 `guru_supervise.py` 都调用;digest 用 **namespaced key + 结构化 artifact + 稳定排序**;manifest fail-closed。无指针 = 现状(向后兼容)。

## 2. 改动设计

### 2.1 共享 requirements digest helper(解 blocker)

- requirements digest 计算抽成单一函数(放 `guru_gate.py`,或新共享小模块),`guru_supervise.py` `from guru_gate import ...`(同 overlay/verify/ 目录)调用,**替换其独立 `_requirements_digest`**。
- 两脚本对 requirements digest 完全同口径 → supervise 写入的 review digest 与 gate 判断的 current digest 一致,不再假 stale。

### 2.2 结构化 artifact + 集中围栏(major 3)

- `_gate_artifacts`(或新 helper)返回结构化条目 `[{path, source, key}]`,`source ∈ {task, design, requirements}`。
- 在此**集中**做:`requirement_package` realpath 围栏(类比 `_package_dir` 行 462-486 的绝对/`..`/repo realpath 拒绝)、`canonical_root` 解析、`canonical_excludes` 过滤、key 生成。
- `_gate_digest` 不再反推来源,直接用条目 key。

### 2.3 namespaced digest key(major 2)+ 兼容边界

- key = `<source>:<relpath>`:`task:prd.md`、`design:README.md`/`design:chapters/x.md`(相对 design_package)、`requirements:README.md`/`requirements:modules/x.md`(相对 requirement_package 版本目录根)。
- **关键兼容**:启用 namespace 会改变 digest;若对所有任务启用,现有已确认任务全部变 stale。故 **namespace 仅在该任务有 `requirement_package` 时启用**(此时才同时出现 requirements/design 的 README 碰撞);**无指针任务保持纯 basename,digest 不变**(向后兼容)。

### 2.4 稳定排序(major 4)

- 生成每个 artifact 最终 key 后,按 `(key, realpath)` 全量排序(替换现 `key=os.path.basename`)。
- `requirement_package` 枚举用 `os.walk` + `dirs.sort()`/`files.sort()`,枚举确定。

### 2.5 manifest fail-closed(major 5)

- manifest **缺失** → fallback 默认(`canonical_root='.'`、`excludes=[snapshots, changes]`)。
- manifest **存在但解析失败/字段类型非法** → `guru_gate.py requirements` **阻断 + 修复提示**,不静默 fallback。
- stdlib 小解析器(只支持 §15 两键的 inline/block list 形态;无 Python yaml 依赖,经 rg 确认仓库无 `import yaml`)。

### 2.6 `requirement_package` 定位 + 字段审计(major 3 / minor 7)

- `_requirement_package_dir(task_dir)`:读 task.json `requirement_package`,realpath 围栏(类比 `_package_dir`)。
- 字段读者审计:确认 `requirement_package` 为 Guru-owned task.json 顶层字段(类比 `design_package`),已审查读者 = `task.py`(整体写回保留未知字段)、`guru_gate.py`、`guru_supervise.py`、session/context hooks;design 列出,不写"零影响"空话。

## 3. 单一来源

requirements digest 计算**单一来源**(共享 helper),`guru_gate.py` + `guru_supervise.py` 调用 —— 消除 codex blocker(两处独立实现)。

## 4. 测试(新增 + 回归)

- **集成(major 6,核心)**:有 `requirement_package` 时,`guru_supervise.py --adversarial requirements` 写 clean → `guru_gate.py status` 显示 current;改 canonical 正文 → stale;改 `excludes` 子树 → 仍 current;无指针 → 旧行为。
- namespace 碰撞:requirements `README.md` + design `README.md` 同存不碰撞。
- 排序稳定:不同创建/枚举顺序 → digest 一致。
- manifest:缺失 fallback、非法 fail-closed(inline/block/非法 yaml/非法类型)。
- 向后兼容:无指针任务 requirements digest 不变(纯 basename)。

## 5. 风险

- digest 是 confirm/check/review_runs/supervise **核心**:共享 helper 必须两边一致;只 requirements + 有指针扩展,其余零变化(回归守门)。
- namespace 启用边界:**仅有指针任务**,避免改旧任务 digest(否则全 stale)。
- overlay 传染(同档 1/2);改两个脚本 + 测试,改动面比档 1/2 大。

## 6. Open Decisions(用户拍板)

- OQ-2 升级为完整决策:`namespaced key + requirement_package-root relpath + stable key sort + 共享 digest helper`(整体采纳)。
- 共享 helper 放 `guru_gate.py`(supervise import)vs 新共享模块 —— 倾向前者(不新增文件),实现期定。
