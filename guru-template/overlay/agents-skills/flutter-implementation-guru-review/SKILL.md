---
name: flutter-implementation-guru-review
description: 按通用 golden-path 与实现标准包审核 Flutter 代码改动，判定能否进入 PR。核查与详细设计合同的一致性、分层依赖律与 canonical 写法、验证证据完整性、合规红线，并执行存量豁免判定（存量记债不阻塞、新增违例阻塞）。标准口径住 `.trellis/spec/harness/implementation/`。
---

# Flutter 实现审核

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（判定基准唯一来源）。
2. 读取同级标准包 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（含实现 Gate 口径）。
3. 读取**`.trellis/spec/conventions/project-conventions.md`**，**重点装载 SLOT-15 存量违例清单**（存量豁免判定的数据源）。
4. 定位：被审改动（diff/分支）、详细设计文档、implementation-trace。trace 缺失 → 前置失败（证据载体不存在）。

## 执行流程

1. **D1 合同一致性**（G1）：diff 与详细设计单元逐一对照——合同外新增结构、未实现的承接行为，列差集；trace §4 是否记录偏差与处置。
2. **D2 分层与 canonical**：对照 golden-path §2/§10 逐项检查改动代码——import 方向（data→usecase、controller→repository/API）、接口分离、DI 形态（binding `new`、`build()` 里 `Get.put`、`permanent` 滥用）、datasource 必经、异常不吞、硬编码尺寸、序列化方案与目录槽位（SLOT-01/02/11/12）。
3. **D3 存量豁免判定**（G4，逐违例必做）：每个发现的违例对照 SLOT-15——
   - 命中清单且未扩大违例面 → **tech-debt 注记，不阻塞**；
   - 清单外或扩大违例面 → **新增违例，P1 阻塞**；
   - 改动修复了清单条目 → 标注"可从清单移除"。
4. **D4 证据核查**（G2）：trace 四节齐全性；analyze/测试命令与结果真实可复跑（抽查至少 1 条复跑）；代码生成执行记录；测试覆盖对照详细设计测试映射（漏失败路径用例 = P2 起步，高风险链路漏测 = P1）。
5. **D5 合规红线**（G3）：制裁 TLD、私有 API、动态执行、权限/数据采集与设计合规依据不一致 = P1。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口与修复动作。

**前置通过时**：
1. 逐条 findings：`severity(P1/P2/P3) / location(文件:行) / problem / suggestion(最小修订)`，先证据后结论。
2. 存量豁免清单：本次触碰的 SLOT-15 条目 + 分类结果 + 可移除项。
3. **结论（三选一）**：可进入 PR / 修复 P2 后可进入 / 不可进入（列阻塞 P1）。
4. 反哺建议（可选）：本次暴露的新模式/新坑 → 建议更新 golden-path、L2 或槽位定义的条目。

## 边界约束

- 只审改动面 + 其直接依赖；不对存量代码做全量审计。
- 审核不代写代码；每条 finding 给最小修订方案。
- 测试失败/证据缺失时如实输出，不降级结论。

## 与官方 Trellis skill 的边界

本 skill 是 `trellis-check` 在 Guru Flutter 项目的领域化审核口径（分层依赖律 + canonical + 存量豁免 + 合规红线），与官方 lint/typecheck 检查叠加执行。
