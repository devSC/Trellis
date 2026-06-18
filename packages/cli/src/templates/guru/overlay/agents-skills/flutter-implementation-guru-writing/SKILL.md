---
name: flutter-implementation-guru-writing
description: 按详细设计合同执行 Flutter 编码与自测。编码规则唯一来源是通用 golden-path（分层迷你路径、DI canonical、禁止清单），过程按 implementation-trace 合同留证据。规则正文不在本 Skill 复写；标准口径住 `.trellis/spec/harness/implementation/`。
---

# Flutter 实现执行

## 装载顺序（硬前置，任一失败即终止）

1. 必须先读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（编码规则唯一来源）；不可用 → 终止并提示先安装 guru spec 模板。
2. 读取同级标准包 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（过程合同）与标准包 SKILL.md 的实现 Gate 定义。
3. 读取**`.trellis/spec/conventions/project-conventions.md`**（校验 C1~C5；重点消费 SLOT-01/02/03/05/08/11/12/15，并确认项目 logger / logging helper / 日志门面）。
4. 定位已通过 Gate 的详细设计文档；缺失 → 终止并提示回退设计阶段（探索性 spike 除外，须显式声明并隔离）。

## 边界约束

- 只实现详细设计合同内的内容；合同外结构不新增，合同错漏回退详细阶段（trace 记录回退）。
- 严守 golden-path §10 禁止清单与项目约定槽位；不私自拍板实现中冒出的新决策。
- **禁止执行 l10n 同步脚本**（`[SLOT-07]`，人工受控）。
- 测试先于或伴随实现（高风险切片先写失败测试再实现）。
- 注释与日志是实现证据的一部分：新增核心类/公开定义/跨层入口必须能从代码追溯到设计文档；非显然业务分支、错误/降级/并发/缓存/生命周期边界必须有简洁但足够具体的注释或日志。禁止堆砌"赋值/调用"类空注释。
- 日志必须复用项目已有 logger、logging helper 或日志门面；不得使用裸 `print`/`debugPrint` 替代项目日志，不得记录 secret、token、PII、完整请求体或用户生成内容原文。

## 执行流程

1. **WX-1 计划**：按 trace 合同 §1 产出任务切片（每片：设计单元 / 文件范围 / 完成信号 / 验证方式），人工确认从最小切片开始。
2. **WX-2 逐片实现**：按入口决策树组合迷你路径（golden-path §1，§3~§7）；每片完成即更新 trace §2 执行记录。
3. **WX-3 代码生成**：按 `[SLOT-08]` 顺序执行（仅在触发条件满足时）；记录于 trace。
4. **WX-4 逐片验证**：`flutter analyze` + 本片相关测试 + `guru_lints`（建成后）；结果记入 trace §3，失败先修复再进下一片。
5. **WX-5 注释/日志/文档追溯**：逐片完成前补齐维护性证据：
   - 新增核心类、public API、Controller/UseCase/Repository/DataSource、跨层 DTO/状态定义：优先用 Dart doc comment 写明职责、承接的 `UNIT-<slug>` / `BHV-NNN`，必要时附设计文档相对路径（如 `docs/design/.../chapters/<slug>.md` 或任务内 `design.md` 锚点）。
   - 复杂私有 helper、状态机分支、错误转换、缓存/恢复/降级、异步竞态、生命周期处置：用局部注释解释"为什么这样做"和对应设计约束。
   - 关键流程日志覆盖入口、成功收口、失败/降级、重试/恢复、外部依赖边界；日志字段只放低敏上下文（id/hash/status/duration），不泄露隐私或业务正文。
   - 在 trace §2 记录本片新增的注释/日志/文档路径引用；若某类代码不需要注释或日志，写明理由。
6. **WX-6 存量违例处置**：触碰 SLOT-15 条目时按标准包口径分类记录（绕行/顺手修复/记债）。
7. **WX-7 收口自检**：对照标准包实现 Gate G1~G4 + 注释/日志/文档追溯要求输出自检摘要；未验证项显式移交（Manual QA / 真机）。

## 输出

- 代码改动 + 新增/修订测试。
- 完整的 `implementation-trace.md`（四节齐全）。
- Gate G1~G4 自检摘要 + 注释/日志/文档路径追溯摘要 + 移交清单。

## 与流程 Skill 的组合

- 分支/worktree/提交/PR 流程隔离交给 `sop-task-runner`（复用后端，栈无关）：先用本 Skill 判定改动范围 → sop-task-runner 创建隔离 → 在隔离内继续本 Skill。

## 与官方 Trellis skill 的边界

本 skill 是 `trellis-implement` 在 Guru Flutter 项目的领域化执行口径：sub-agent 实现时按本 skill 的迷你路径与 trace 合同工作。Phase 2 dispatch 时在 prompt 中指明加载本 skill 口径。
