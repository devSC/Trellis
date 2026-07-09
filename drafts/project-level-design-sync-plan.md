# 项目级概要/详细设计同步方案草案

## 结论先行

本方案采用“两层设计合同”：

1. **任务级设计合同**：继续服务现有 Trellis/Guru 启动流程。`requirements -> overview -> detail -> task.py start` 仍然证明“当前任务可以进入实现”。
2. **项目级当前设计合同**：新增 `docs/design/current/`，表示当前分支最新实现的概要/详细设计还原。第一期只在本地提交阶段由新增的 `design-sync --staged` Gate 校验，不替代现有 `overview/detail` 启动 Gate；PR 级跨 commit 校验是二期能力。

关键约束：

- `docs/design/current/` **不得直接作为多个活跃任务共享的 `task.json.design_package`**。
- 现有 `guru_gate.py overview/detail` 继续审任务级设计包，不审全项目 current 包。
- 项目级 current 包的追溯使用独立的项目级行为编号 `PBHV-*` 和 `design-impact` 增量过滤，不能和单个任务 `prd.md` 的 `BHV-*` 全量混算。
- `design-sync` 第一期是新增 commit-level staged Gate；当前仓库尚未实现该子命令，本文描述的是待实现合同。PR 级 `--base-ref/--head-ref` 是二期能力。

## 背景

当前 Trellis/Guru 的任务级设计产物可以表达某次变更的计划与评审证据。但如果“概要设计”和“详细设计”的目标是还原项目当前最新代码，那么它们不应只属于单个任务：任务会完成、归档、过期，而项目当前实现会持续演进。

因此，需要引入一套项目级 current 设计包，让概要设计和详细设计成为当前代码的可审设计合同。所有会改变项目当前行为、边界、数据、状态、接口、依赖方向或测试口径的变更，都必须同步更新项目级文档，或者留下可验证的 `no-doc-impact` 证据。

## 目标

1. 项目级概要设计和详细设计能够还原当前分支最新实现的关键结构与行为。
2. 每次代码变更都能被判定是否影响项目级设计包。
3. 第一期要求影响项目级设计包的变更必须在同一 staged index 中同时包含代码、测试和项目级文档更新；PR 级跨 commit 校验是二期能力。
4. 文档与代码之间形成可验证的 traceability：项目级行为 `PBHV-*` -> 设计单元 -> 源码路径 -> 测试证据。
5. 任务级设计文档只记录本次变更 delta、任务级可实现性和评审证据，不再冒充项目当前完整设计。
6. 现有 Trellis/Guru 任务启动 Gate 不被项目级 current 包污染。

## 非目标

1. 不把每一行源码翻译成自然语言。
2. 不要求低风险纯文案、颜色、格式调整必须更新项目级设计正文。
3. 不用项目级文档替代源码事实；源码仍是实现细节的最终事实源。
4. 不要求一次性补齐全项目所有详细章节，可以按高风险和核心路径渐进覆盖。
5. 第一期不解决跨 repo/project-set 原子提交；项目集聚合是二期能力。

## 术语与权威边界

| 层级 | 名称 | 产物 | 作用 | 冲突时地位 |
| --- | --- | --- | --- | --- |
| L0 | implementation truth | 源码、测试、配置、迁移 | 精确实现事实 | 最终事实源 |
| L1 | generated fact inventory | 机器生成 inventory | 从源码抽取路由、API、schema、依赖、测试映射等事实 | 可重复生成的事实索引 |
| L2 | project-current design contract | `docs/design/current/` | 当前分支的人类可读设计合同 | 必须与 L0/L1 同步 |
| L3 | task delta proposal/evidence | `.trellis/tasks/<task>/` | 某次变更的需求、设计 delta、执行计划、评审证据 | 只服务当前任务 |

冲突优先级：

- L0 是事实源。
- L1 是从 L0 生成的证据索引。
- L2 是必须同步的可审合同。
- 当 L0/L1 与 L2 冲突时，`design-sync --staged` 必须阻断提交，责任是在同一 staged index 中修复 L2，或提供合法的 `no-doc-impact` 证据。PR 级跨 commit 修复需要二期 `--base-ref/--head-ref`。
- 不允许用“源码是真相”作为理由长期保留 stale 的 L2 文档。

## 与现有 Trellis/Guru 的兼容边界

当前 Guru 双轨：

| 链路 | 现有产物 | 现有用途 |
| --- | --- | --- |
| `light` | 任务内 `design.md §1/§2` | 任务级 overview/detail Gate |
| `full` | 任务 `task.json.design_package` 指向的 `README.md + design-main.md + chapters/` | 任务级 overview/detail Gate |

本方案不改变上述语义。新增项目级 current 包后，边界如下：

| 对象 | 是否可作为活跃任务 `design_package` | 用途 |
| --- | --- | --- |
| 任务级 `design.md` | 是，light 链 | 当前任务启动 Gate |
| 任务级 `design_package` 或任务级 snapshot/delta 包 | 是，full 链 | 当前任务启动 Gate |
| `docs/design/current/` | **否** | 项目当前设计合同，第一期由 commit-level `design-sync --staged` 校验 |

禁止事项：

1. 禁止把 `docs/design/current/` 直接写入多个活跃任务的 `task.json.design_package`。
2. 禁止让现有 `overview/detail` review 直接审全项目 current 包后作为任务启动依据。
3. 禁止把项目级全量 `UNIT-*` 与单任务 `prd.md` 的 `BHV-*` 用现有 `build_trace()` 全量混算。

允许事项：

1. 任务级 full 链可以引用项目级 current 的特定章节作为背景证据。
2. 任务级设计可以声明本次影响的项目级 `CAP-*`、`PBHV-*`、`UNIT-*`，并保留 source task `BHV-*` 映射。
3. 提交阶段，`design-sync --staged` 要求同一 staged index 同步更新 `docs/design/current/`。

### no-active-task / direct commit policy

当前 overlay 存在“无 active task 时可直接提交”的历史路径，但项目级 current 设计同步不能被该路径绕过。第一期采用最小 fail-closed 策略：

1. 若 commit guard 解析不到 active task，且 staged paths 含可扫描代码路径，提交不得直接放行。
2. 用户必须创建/选择 Trellis/Guru task，让 task-local `design-impact.jsonl` 承载本次 gate evidence。
3. 纯文档、纯文案、纯格式等低风险 direct commit 可以走二期 `design-sync --staged --direct` 模式；第一期不实现 direct 放行。
4. 若未来实现 `--direct`，其证据不得写入 `.trellis/tasks/<task>/`，必须定义独立落点，例如 `.trellis/workspace/<developer>/design-impact-direct.jsonl`，并同样绑定 staged digest。

对应测试：第一期覆盖无 active task + staged scannable code 时，commit guard 或 `check-commit` 必须阻断并提示创建/选择任务；二期若实现 direct 例外，再补无 active task + 非代码低风险路径 + 可复验证据的放行测试。

## 建议目录结构

第一期只支持单 repo：

```text
docs/design/
  current/
    manifest.yaml
    README.md
    design-main.md
    behavior-registry.md
    chapters/
      route-dashboard.md
      data-order.md
      flow-payment-confirmation.md
    traceability.md
    inventory.generated.json
    verification/
      last-sync.json
      drift-report.md
```

任务级 mutable evidence：

```text
.trellis/tasks/<task>/
  design-impact.jsonl
  verification-evidence.jsonl
  commit-plan.json
```

二期项目集或多 repo 聚合：

```text
docs/design-project-set/
  manifest.yaml
  design-main.md
  projects/
    web/
      repo_root: <declared in manifest>
      current/
    backend/
      repo_root: <declared in manifest>
      current/
  cross-project-flows/
    auth-session.md
    order-payment.md
```

二期必须额外定义 `projects[].repo_root`、`projects[].code_ref`、`submodule_gitlink`、`sync_unit` 和跨 repo 失败时的阻断/提交责任。第一期不得用单 repo Gate 假装完成跨 repo 原子性。

## 项目级概要设计 schema

`docs/design/current/design-main.md` 是项目当前设计的主索引，必须兼容 Guru full overview 的硬字段，同时允许扩展项目级视图。

必含章节：

| 章节 | 必需内容 | Gate 目的 |
| --- | --- | --- |
| 项目边界 | 当前项目负责/不负责范围，外部系统依赖 | 防止 owner 漂移 |
| 能力地图 | `CAP-*` 到业务/技术能力 | 给项目级行为注册表分组 |
| 项目级行为注册表摘要 | `PBHV-*` 来源、状态、owner、测试等级，以及对应任务 `BHV-*` 映射 | 给项目级 current trace 提供 namespace |
| 行为到 owner 归属表 | `PBHV-* -> owner`，逐行三问理由：为什么属于它/不属于别人/是否独立存在 | 供 `design-sync` 使用；任务级 `overview` 仍使用任务 `BHV-*` |
| 代码入口地图 | 路由、API、CLI、worker、页面入口、定时任务 | 支撑 inventory 对比 |
| 数据与状态总览 | 关键实体、状态机、缓存、持久化、同步关系 | 支撑 schema/state drift 检查 |
| 跨层依赖律 | 允许依赖和禁止反向依赖 | 支撑边界变更判断 |
| 详细设计承接索引 | `chapter_target -> detail_doc_type -> chapters/<file>.md -> L2 状态/豁免` | 兼容 full 链章节闭合 |
| 架构图/页面流图 | mermaid 图或平台等价图 | 兼容 Guru overview L1 |
| 时序图或时序图策略表 | 核心流程时序，或明确 N/A 依据 | 兼容 Guru overview L1 |
| 架构就绪自检 | G1~G8 或平台等价自检 | 支撑 review 一致性 |

承接索引必须使用当前平台权威 `detail_doc_type`。例如 H5 平台使用 `server-component`、`client-component`、`data-access`、`route`、`ui-component`、`domain-type`、`server-action` 等平台定义类型；Go/iOS/Flutter 使用各自 spec 中的类型。pending L2 类型必须在 `design-main.md` 显式声明 `L2豁免：<doc_type> 理由：...` 或等待对应 L2 建成。

示例索引行：

```markdown
| Project behavior | source task/BHV | owner | 三问理由 | chapter_target | detail_doc_type | chapter_file | L2 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PBHV-0012 | 07-08-order-payment/BHV-012 | order/payment | 属于 payment owner；不属于 account；需独立存在 | order-payment-confirmation | server-action | chapters/flow-payment-confirmation.md | v1 |
```

## 项目级详细设计 schema

详细设计按稳定设计单元维护，而不是按任务维护。每个章节对应当前代码中的一组稳定责任边界。

每个章节必须是 Guru detail skeleton 的超集，不能另起一套无法被现有审查规则识别的结构。

建议固定结构：

```markdown
# order-payment-confirmation 详细设计

> 承接索引：design-main.md / chapter_target=order-payment-confirmation
> detail_doc_type: server-action
> l2_status: v1

### UNIT-order-payment-confirmation

## 单元职责

承接 PBHV-0012（source: 07-08-order-payment/BHV-012）和 PBHV-0018。说明本单元负责什么、不负责什么、为什么独立存在。

## 当前代码锚点

- Source: src/server/actions/confirm-payment.ts
- Source: src/lib/orders/order-repository.ts
- Tests: tests/orders/payment-confirmation.test.ts

## 行为定义

| Project behavior | source task/BHV | 输入 | 输出 | 成功条件 | 失败收口 |
| --- | --- | --- | --- | --- | --- |
| PBHV-0012 | 07-08-order-payment/BHV-012 | ... | ... | ... | ... |

## 核心数据结构

列出领域类型、schema、状态字段、缓存键、持久化字段或明确 N/A。

## 逐行为设计

按 PBHV 说明调用链、依赖、状态变化、错误映射和副作用。

## 状态/边界

说明状态机、事务边界、幂等、缓存、并发、跨层依赖与禁止调用。

## 路由 / 渲染 / SEO

本标题是 H5 `route` 示例。实际章节必须使用目标平台当前 `DETAIL_SECTION_PATTERNS` 能识别的类型专属标题：H5 可用“路由 / 渲染 / SEO”，Go 可用“数据合同”，Flutter 可用“Widget 设计”，iOS 可用“View 设计”或“导航设计”。pending L2 时按合同八问展开并回指 overview 豁免。

## 测试映射

| Project behavior | source task/BHV | Test | Evidence status |
| --- | --- | --- | --- |
| PBHV-0012 | 07-08-order-payment/BHV-012 | tests/orders/payment-confirmation.test.ts | present |

## 不得补造清单

- 不决定不属于本 owner 的业务规则。
- 不越层读取 secret 或私有数据源。
- 不把实现期临时证据写回 digest-bearing planning 文档。
```

P0/P1 行为必须链接测试证据；P2 及以下可以声明测试豁免，但需要理由和回验时点。

## 项目级行为注册表

为了避免项目级全量 `UNIT-*` 与单任务 `prd.md` 的 `BHV-*` 断链，项目级 current 不能直接使用单个任务 `prd.md` 作为全量行为来源。

第一期采用项目级行为注册表，并固定使用独立编号 `PBHV-*`。裸 `BHV-*` 只表示任务局部行为，不得在项目级 current 中作为全局主键。

```text
docs/design/current/behavior-registry.md
```

注册表字段：

| 字段 | 含义 |
| --- | --- |
| `PBHV-*` | 项目级稳定行为编号 |
| `source_task` | 来源任务 |
| `source_bhv` | 来源任务内的 `BHV-*`，例如 `BHV-012` |
| `source_requirement` | 来源需求包、PR 或迁移记录 |
| `status` | active / deprecated / superseded |
| `owner` | 项目级 owner |
| `capability` | `CAP-*` |
| `chapter_target` | 详细设计单元 |
| `code_anchor` | 源码路径或 symbol |
| `test_anchor` | 测试路径或豁免 |

任务级 `prd.md` 中的新 `BHV-*` 只有在合入项目级 current 时，才映射成新的或既有的 `PBHV-*`。`design-sync` 只对 `design-impact.jsonl` 声明的 affected units 做增量追溯，不把全量 current 包喂给现有 `guru_gate.py detail`。

## `design-impact.jsonl`

`design-impact.jsonl` 是任务级 mutable gate evidence，不参与现有 overview/detail digest，不写入 `implement.md`，不写入项目级 current 包正文，也**不随实现提交 staged/commit**。它由 `commit-plan` 和 `design-sync` 在本地读取，必须绑定最终 staged index digest 防 stale。

建议路径：

```text
.trellis/tasks/<task>/design-impact.jsonl
```

记录示例：

```json
{
  "schema_version": 1,
  "mode": "index",
  "task": ".trellis/tasks/07-08-example",
  "staged_target_digest": "sha256:...",
  "staged_paths": ["src/server/actions/confirm-payment.ts"],
  "classifier_version": "design-sync-classifier-v1",
  "risk_flags": ["server-action", "payment", "state_change"],
  "design_impact": "required",
  "affected_capabilities": ["CAP-order-management"],
  "affected_project_behaviors": ["PBHV-0012"],
  "affected_source_behaviors": ["07-08-order-payment/BHV-012"],
  "affected_units": ["UNIT-order-payment-confirmation"],
  "required_project_docs": [
    "docs/design/current/design-main.md",
    "docs/design/current/chapters/flow-payment-confirmation.md",
    "docs/design/current/behavior-registry.md"
  ],
  "checked_command": "python3 .trellis/scripts/guru/guru_gate.py design-sync .trellis/tasks/07-08-example --staged",
  "checked_at": "2026-07-08T10:00:00Z"
}
```

`design-impact.jsonl` 的最终 staged digest 必须覆盖所有 staged code paths 和相关 project-current doc paths。staged 内容变更后，旧记录失效。实现提交只包含代码、测试和 `docs/design/current/**`；`.trellis/tasks/<task>/design-impact.jsonl` 留在任务工作区作为 gate evidence，像 implementation-review 记录一样服务本次提交门禁。

若 staged project-current docs 不在最新 implementation review 的 target scope 内，必须先运行覆盖这些路径的 staged implementation review，再运行 `check-commit`；否则现有提交 Gate 可能按 staged scope/out-of-scope 阻断。

## `no-doc-impact` 证据

`no-doc-impact` 是 `design-impact.jsonl` 中 `design_impact=none` 的记录形态，不另建文件。它只能用于合同不变的低风险变更，必须以最终 staged index digest 为证据根，不能使用笼统的 `code_ref: HEAD`。

合法记录示例：

```json
{
  "schema_version": 1,
  "mode": "index",
  "task": ".trellis/tasks/07-08-copy-only",
  "staged_target_digest": "sha256:...",
  "staged_paths": ["src/app/settings/page.tsx"],
  "classifier_version": "design-sync-classifier-v1",
  "risk_flags": ["copy_only"],
  "design_impact": "none",
  "allowed_reason_enum": "copy_only",
  "reason": "Only visible copy changed; no route, data, state, behavior, owner, dependency, error handling, or test contract changed.",
  "checked_command": "python3 .trellis/scripts/guru/guru_gate.py design-sync .trellis/tasks/07-08-copy-only --staged",
  "checked_at": "2026-07-08T10:00:00Z"
}
```

Fail-closed 规则：

- 命中支付、权限、隐私、认证、schema、状态机、路由/API、外部集成、缓存一致性、迁移等高风险信号时，不允许 `no-doc-impact` 自动放行。
- staged paths 中存在未分类代码变更时，不允许 `no-doc-impact` 放行。
- staged digest 与记录不匹配时，记录失效。

## `design-sync` Gate

`design-sync` 第一期是新增 commit-level staged Gate。它当前尚未在 `guru_gate.py` 实现；本文定义待实现合同。

第一期只实现 commit-level staged gate。`--staged` 只能证明当前 staged index 自洽，因此第一期删除“同一 PR 中后续 commit 补文档也可放行”的承诺。若后续需要 PR 级能力，另增 `design-sync --base-ref <base> --head-ref <head>`，只用于 CI/PR gate，不替代本地 `--staged`。

建议命令：

```bash
python3 .trellis/scripts/guru/guru_gate.py design-sync <task-dir> --staged
```

接入点：

1. `commit-plan` 输出 `design_sync` 字段，列出是否需要运行、预计影响范围、阻断原因。
2. `design-sync` 是 route-independent final commit requirement：所有含 staged 可扫描代码的提交，在 route/scope 校验之后、任何 `can_commit_now=True` 或 `COMMIT_READY` 之前，都必须计算 `design_sync` 状态。
3. `micro_task` 不能绕过 `design-sync`。它只能在 `design_sync.status=pass` 或合法 `no-doc-impact` 后放行；缺失或 stale `design-impact.jsonl`、非法 `no-doc-impact`、缺 project-current docs 时必须阻断。
4. `check-commit` 在 staged scope 检查、implementation review clean（full/lite）或 micro contract pass（micro_task）之后，调用或内联 `design-sync --staged`，再决定是否输出 `COMMIT_READY`。
5. `design-sync` 退出码采用现有 Gate 习惯：`0` 表示通过，`2` 表示阻断。
6. 阻断原因进入 `commit-plan.json`，便于任务级证据闭环。

二期 PR 命令草案：

```bash
python3 .trellis/scripts/guru/guru_gate.py design-sync <task-dir> --base-ref main --head-ref HEAD
```

该模式验证 PR diff 的整体 code/docs 同步，不用于本地 commit hook。

Gate 检查项：

| 检查项 | 失败条件 |
| --- | --- |
| staged 影响面识别 | 有代码变更但无法分类 |
| project-current manifest | 缺 `docs/design/current/manifest.yaml`，且变更命中需设计同步的路径 |
| inventory freshness | inventory 缺失、生成失败或 input digest 与 staged index 不匹配 |
| design-impact evidence | 缺 `design-impact.jsonl` 或 staged digest 不匹配 |
| 概要索引闭合 | 受影响 owner/PBHV/chapter 未进入 `design-main.md` |
| 详细章节闭合 | 受影响 `UNIT-*` 无章节或章节缺必需骨架 |
| 代码锚点有效 | 文档引用的源码路径不存在 |
| 测试映射有效 | P0/P1 行为无测试或合法豁免 |
| traceability 闭合 | 项目级 `PBHV -> UNIT -> code -> test` 断链 |
| no-doc-impact 合法 | 声明无影响但命中高风险路径、合同变化或 digest 不匹配 |

## inventory 生成与 staleness

`inventory.generated.json` 是 L1 事实索引，必须声明生成器、范围和 digest。

`manifest.yaml` 必须包含：

```yaml
schema_version: 1
design_package_type: project_current
coverage_status: partial

platform_profile:
  id: h5-web
  doc_type_taxonomy_source: ".trellis/spec/harness/detail/detail-structure-single-source.md"
  detail_section_patterns_source: ".trellis/scripts/guru/guru_gate.py"

inventory:
  file: inventory.generated.json
  generator:
    command: "python3 .trellis/scripts/guru/design_inventory.py --staged --output docs/design/current/inventory.generated.json"
    version: "design-inventory-v1"
  generated_from: index
  source_roots:
    - src
    - app
    - lib
    - tests
  exclude_globs:
    - node_modules/**
    - dist/**
    - build/**
    - .next/**
    - coverage/**
  input_digest: "sha256:..."
  generated_at: "2026-07-08T10:00:00Z"

overview:
  entry: design-main.md

detail:
  chapters_dir: chapters
  unit_id_pattern: "UNIT-[a-z][a-z0-9-]*"

trace:
  behavior_registry: behavior-registry.md
  traceability: traceability.md

sync_policy:
  require_design_impact_for_code_changes: true
  require_code_anchors: true
  require_test_mapping_for_p0_p1: true
  allow_no_doc_impact:
    - copy_only
    - style_only
    - private_refactor_contract_unchanged
```

staleness 规则：

- `generated_from=index` 时，`input_digest` 必须匹配当前 staged index 中纳入 source roots 的文件集合。
- generator 失败时，`design-sync` fail-closed。
- inventory 缺失或 schema version 不匹配时，`design-sync` fail-closed，除非当前 staged paths 全部被合法 `no-doc-impact` 覆盖。
- 生成范围不得默认包含 vendor/build/generated artifacts，除非 manifest 显式声明。
- `platform_profile.doc_type_taxonomy_source` 读取失败时，`design-sync` fail-closed，不允许静默 fallback 到错误平台 taxonomy。

## 覆盖率与渐进落地

本文中的“第一期”只表示单 repo、commit-level、`--staged` 的能力边界；`report-only`、`partial`、`critical_paths`、`complete` 是该能力在不同项目中的启用等级。第一期 GA 验收必须以 `coverage_status=complete`，或 manifest 中明确声明的 enforced scope 为准，不能把 bootstrap/report-only 阶段误当成最终同步保障。

项目级 current 支持渐进覆盖，但覆盖状态必须显式记录：

| coverage_status | 含义 | Gate 行为 |
| --- | --- | --- |
| `partial` | 只覆盖高风险/核心路径 | `design-sync` 先报告 drift；对高风险路径阻断；不影响任务启动 Gate |
| `critical_paths` | 高风险和核心路径基本闭合 | 高风险和核心路径阻断；普通中风险可警告 |
| `complete` | 项目主要入口、行为、owner、UNIT、测试映射闭合 | 中高风险变更缺同步即阻断 |

在 `partial` 或 `critical_paths` 阶段，项目级 current 不得反向卡死普通任务启动。普通任务仍使用任务级 `overview/detail` Gate。只有达到 `complete` 后，才可以考虑让某些任务引用 current snapshot 作为基线，但仍不得让多个活跃任务共享同一个 mutable `docs/design/current` 目录作为 `design_package`。

升级条件：

| 升级 | 最低证据 |
| --- | --- |
| `partial -> critical_paths` | 所有 P0/P1 入口列入 inventory；P0/P1 `PBHV-*` 均有 owner、chapter、code_anchor；高风险路径连续两次 `design-sync` 无 drift；owner 代表确认 |
| `critical_paths -> complete` | 主要入口、行为、owner、UNIT、测试映射闭合；无未分类中高风险路径；`inventory.generated.json` 与 staged/main 基线连续两次匹配；项目维护者确认 |

升级记录必须写入 `last-sync.json` 或 manifest 审计字段，包含操作者、时间、证据 digest 和确认来源。

## 同步闭环

每次变更按以下流程闭环：

1. 任务启动前，继续走现有任务级 requirements/overview/detail Gate。
2. 实现后，扫描 staged index，识别 code/doc/test 影响面。
3. 生成 provisional impact classification：只列出预计影响的 `PBHV-*`、`UNIT-*`、project-current docs，不作为最终放行证据。
4. 若影响项目级 current，则更新并 stage `docs/design/current/design-main.md`、`behavior-registry.md`、对应 `chapters/*.md`、`traceability.md` 和 `inventory.generated.json`。
5. 若无设计影响，则准备 `no-doc-impact` 记录。
6. 基于最终 staged index 重新生成任务级 `.trellis/tasks/<task>/design-impact.jsonl`；该文件是非 staged gate evidence，不进入实现提交。最终记录的 staged digest 必须覆盖最终 staged code/test/project-current doc paths。
7. 如 staged project-current docs 超出最新 implementation review scope，先运行覆盖这些路径的 staged implementation review。
8. 运行 `commit-plan --write`，确认 stdout 与 `.trellis/tasks/<task>/commit-plan.json` 都包含同一份完整 `design_sync` schema：`required/status/blocking_reasons/required_commands/evidence_path/staged_target_digest/no_doc_impact_reason`。
9. 运行 `check-commit`，由其调用或要求 `design-sync --staged`；任何 route（包括 `micro_task`）都必须在 design-sync pass 或合法 no-doc-impact 后才能输出 `COMMIT_READY`。
10. 第一期要求同一 staged index 中同时包含实现变更和项目级设计更新；否则提交被阻断。

## 并发与冲突策略

多个任务可能同时修改 `docs/design/current`。第一期采用 staged index + 分支重基线策略：

1. `design-sync` 以 staged index 为证据根，不用工作区未 staged 内容证明通过。
2. 合入前如果 main 上 `docs/design/current` 已变化，当前分支必须 rebase 或 merge 后重新生成 inventory 和 design-impact。
3. `last-sync.json` 记录 base commit、head commit、inventory digest 和 project-current digest。
4. owner 分片可降低冲突：不同 owner 优先修改不同章节；共享 `design-main.md` 的索引段必须通过生成区或稳定排序减少冲突。
5. 不引入长时间锁。锁只能作为本地写入保护，不能作为跨 PR 正确性证明。

`last-sync.json` 示例：

```json
{
  "repo": "example-project",
  "branch": "feature/order-payment",
  "base_commit": "abc1234",
  "head_commit": "def5678",
  "generated_from": "index",
  "inventory_digest": "sha256:...",
  "project_current_digest": "sha256:...",
  "generated_at": "2026-07-08T10:00:00Z",
  "status": "synced",
  "checked_paths": ["src", "app", "lib", "tests"],
  "design_package": "docs/design/current"
}
```

## 项目集二期边界

项目集设计只在单 repo 方案稳定后启用。二期必须显式解决：

1. 每个 project 的 `repo_root`、`code_ref`、staged/index 来源。
2. submodule gitlink 与子仓 HEAD 是否一致。
3. 跨 repo design-impact 的归属和提交责任。
4. 跨 repo current 包不能假装一个 `guru_gate.py --staged` 可以原子验证。
5. project-set 顶层只聚合跨项目 flow，不承载单项目详细实现合同。

## 落地路线

1. 建立项目级 current 设计包骨架：`manifest.yaml + README.md + design-main.md + behavior-registry.md + chapters/ + traceability.md`。
2. 先覆盖高风险/高价值区域：API、路由、数据模型、状态机、权限、支付、外部集成、核心页面流。
3. 更新 executable spec：修改 `.trellis/spec/cli/backend/guru-overlay-gates.md` 的 “Route-Aware Finish and Commit Contract”，把 `design_sync` 写入 Commit Plan Schema，并明确 `check-commit` 必须使用同一 `_commit_plan_payload` 决策，在任何 `can_commit_now=True` 或 `COMMIT_READY` 前完成 `design_sync` 判定。
   - `design_sync` 字段至少包含：`required`、`status`、`blocking_reasons`、`required_commands`、`evidence_path`、`staged_target_digest`、`no_doc_impact_reason`。
   - spec 必须覆盖 full/lite、`micro_task`、no-active-task direct policy，以及 `commit-plan --write` 与 stdout 一致性。
4. 在 overlay SSOT 实现：修改 `guru-template/overlay/verify/guru_gate.py`，新增 `guru-template/overlay/verify/design_inventory.py`。
5. 同步 bundled mirror：将 overlay 变更同步到 `packages/cli/src/templates/guru/overlay/verify/**`，并运行 `pnpm -C packages/cli sync:guru:check` 保证 mirror 无漂移。
6. 补 source overlay 测试面：`guru-template/overlay/verify/tests/run_tests.sh` 覆盖 `design-sync` pass/fail/stale/no-doc-impact，并覆盖 commit gate 集成：
   - `commit-plan` stdout 和 `commit-plan --write` 生成的 `.trellis/tasks/<task>/commit-plan.json` 都输出完整 `design_sync` schema：`required/status/blocking_reasons/required_commands/evidence_path/staged_target_digest/no_doc_impact_reason`。
   - `check-commit` 在缺失或 stale `design-impact.jsonl`、缺 project-current docs、非法 `no-doc-impact` 时阻断。
   - `check-commit` 在 clean implementation review + design-sync pass 时放行。
   - `micro_task + 缺 design-impact.jsonl` 阻断；`micro_task + stale design-impact digest` 阻断；`micro_task + 合法 no-doc-impact` 放行。
   - 若存在 high-risk override 允许走 micro，也必须经过同样的 design-sync/no-doc-impact 断言。
   - commit guard smoke 证明 hook 走到 `check-commit` 后会传播 `design-sync` 阻断。
   - no-active-task + staged scannable code 时阻断并提示创建/选择任务。
7. 补 bundled 安装测试：`packages/cli/test/guru/guru-bundled.test.ts` 证明安装后的 `.trellis/scripts/guru/design_inventory.py` 与 `guru_gate.py design-sync` 存在且可调用；bundled test 不替代 source overlay gate integration fixtures。
8. 实现 inventory generator，先只读输出 `inventory.generated.json` 和 drift report。
9. 引入任务级 `design-impact.jsonl`，所有代码变更必须说明是否影响项目级设计。
10. 实现只读 `design-sync`，先报告 drift，不阻断。
11. `coverage_status=partial` 时，仅对高风险路径启用阻断。
12. `coverage_status=critical_paths` 后，对核心路径中风险变更启用阻断。
13. `coverage_status=complete` 后，对中高风险变更缺项目级同步启用阻断。
14. 将 `design-sync` 接入 `commit-plan`、`check-commit`、`micro_task` final commit path 和 no-active-task commit guard policy。

## 修复后仍需确认的产品/流程决策

1. 各平台的 `detail_doc_type` 是否需要统一抽象，还是完全沿用平台 spec。
2. P0/P1 测试证据缺失时，是允许短期豁免，还是一律阻断。
3. 二期 project-set 是否需要独立 aggregator，而不是塞进单 repo `guru_gate.py`。

## 自洽性检查摘要

本版方案满足以下约束：

1. 不把项目级 current 直接作为活跃任务共享 `design_package`。
2. 不替换现有任务级 `overview/detail` 启动 Gate。
3. 项目级行为固定使用 `PBHV-*`，不把项目级全量 `UNIT-*` 与单任务 `prd.md` 全量混算。
4. 项目级 overview/detail schema 是现有 Guru 结构合同的超集。
5. `design-sync` 明确为新增 commit-level staged Gate，并声明接入点；PR 级命令是二期能力。
6. `no-doc-impact` 以 staged index digest 为证据根。
7. `design-impact.jsonl` 明确是非 staged gate evidence，避免与现有 `check-commit` staged task artifact 规则冲突。
8. 同步闭环先生成 provisional impact，最终放行证据必须基于最终 staged index 生成，避免天然 stale。
9. 第一期只承诺 commit-level `--staged`，PR-level `--base-ref/--head-ref` 是二期能力。
10. 落地路线覆盖 Guru overlay SSOT、bundled mirror、`sync:guru:check` 和测试面。
11. 落地路线要求同步 `.trellis/spec/cli/backend/guru-overlay-gates.md`，把 `design_sync` 写入 executable spec 和 Commit Plan Schema，避免草案/代码/测试与 spec 分叉。
12. no-active-task direct commit 路径在 staged scannable code 场景下 fail-closed，不会绕过 `design-sync`。
13. commit-plan/check-commit 集成测试被列为必做，不只测试 `design-sync` 子命令存在。
14. `micro_task` 被纳入 route-independent design-sync final requirement，不再是绕过路径。
15. `commit-plan --write` 的持久化证据必须包含和 stdout 一致的完整 `design_sync` 字段：`required/status/blocking_reasons/required_commands/evidence_path/staged_target_digest/no_doc_impact_reason`。
16. `UNIT-*` 正则与现有 Guru Gate 保持一致：`UNIT-[a-z][a-z0-9-]*`。
17. inventory 的生成范围、digest、staleness、platform taxonomy source 和 fail-closed 行为有明确合同。
18. partial coverage 不会反向卡死普通任务启动。
