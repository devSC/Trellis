# implementation-trace 合同（Guru iOS 原生平台）

> `implement.md` / implementation-trace 是 detail Gate 的 digest-bearing planning contract——「不是做完感，而是证据感」。
> 装载顺序：先读 `.trellis/spec/guides/golden-path.md`（分层依赖律 + golden-path 锁定），再读本任务详细设计的章节合同（`.trellis/spec/harness/detail/detail-structure-single-source.md` + 命中的 L2），最后把 detail 确认后的执行/验证证据写入 mutable evidence。
> 建议落盘路径：目标仓库 `docs/design/<feature>/implementation-trace.md`。detail 确认后的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`；若必须修改已确认 trace，必须回退 detail Gate 并重新 review/confirm。
> 平台基准：DDD 四层 Domain → App → Infrastructure → UI（Domain 零依赖）；SwiftUI 主 + RxSwift 遗留；FactoryKit DI（`@Injected`）；Repository 模式（接口在 Domain、实现在 Infrastructure）；`enum Error` per domain；AppCoordinator 导航；WCDBSwift 持久化；ViewModel = `ObservableObject` + `@Published`。
> doc_type 一律用 iOS 权威七类：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`。**禁止自创 `transport-handler` / `service` / `controller` / `data-source` 之类的类型名。**

Delivery policy is executable, not prose-only. Implementation trace must quote the selected route from `guru_delivery_policy.py`: Small records first scoped code evidence and stops fast; Micro records explicit allowed paths/max files; Lite records compact task evidence, one confirmation batch maximum, and bounded review; Full records selected slice packet, risk packet, guarded start evidence, deterministic checks and implementation review. Budget expiry never removes required Gate/review/confirmation; it produces a terminal stop or re-intake.

## Full/high 风险决策清单

`guru-risk-contract-v2` 仅在 `full_chain + high|unknown` 时要求以下 block。它必须在 `implement.md` 中恰好出现一次，且 block 内只能有一个 JSON fence；Small/Micro/Lite 和兼容 v1 合同不得被该清单拖慢。

<!-- GURU:RISK_DECISION_INVENTORY:START -->
```json
{
  "schema_version": 1,
  "task_id": "<task.json.id>",
  "scope": {
    "selected_slice_id": "<selected-slice-id>",
    "official_start_authority": "selected_slice_only",
    "later_slice_authority": "supervisor_fail_closed"
  },
  "slices": {
    "<selected-slice-id>": [
      {
        "decision_id": "DEC-<DOMAIN>-001",
        "severity": "high",
        "status": "unresolved",
        "recommendation": "<recommended choice>",
        "alternatives": [
          "<credible alternative>"
        ],
        "impact": "<scope, data, compatibility, or rollback impact>",
        "irreversible": false,
        "invariant_ids": [
          "<invariant id from the selected slice packet>"
        ],
        "required": true,
        "source_refs": [
          {
            "artifact_key": "design:chapters/<detail-artifact>.md",
            "anchor": "GURU-DECISION:DEC-<DOMAIN>-001"
          }
        ]
      }
    ]
  }
}
```
<!-- GURU:RISK_DECISION_INVENTORY:END -->

只允许 `required=true` 的 `critical|high` 决策。`decision_id` 必须跨 slice 唯一，slice 和 `invariant_ids` 必须与 packet 精确匹配；每个 `source_ref` 必须指向 Detail artifact 中恰好出现一次且包含该 decision ID 的 anchor。决策确认后将 `status` 改为 `resolved`，并添加非空 `resolution.choice` 与 `resolution.evidence`；未确认时不得伪造 `resolution`。Detail 结构检查、Detail review/confirm、risk packet 和 guarded start 必须解析同一份清单。

## Full/high slice planning audit

Full/high 的 `implement.md` 必须有 slice planning audit，目标是**最少的 commit-stable slices 和最大的安全并发宽度**，不是按 UNIT、`doc_type`、ViewModel、UseCase、View 或章节机械拆分。每个普通 slice 登记 `slice_id`、真实标量 `owner_unit`、`covered_units`、文件级 `owned_paths`、`read_paths`、`depends_on`、`parallel_wave`、`independent_commit_value`、`rollback_contract`、`resource_locks` / 隔离方式、focused checks 和 reviewer context inputs/bytes。`covered_units` 是包含 `owner_unit` 在内的完整 Design UNIT 集合，只属于 planning audit；不得新增或重定义 packet / evidence schema 字段。

- 一个普通 mutable path 在同一 implementation wave 只有一个 owner；symbol、函数或 diff hunk 不能绕过文件级 ownership。共享测试文件也必须唯一归属、分波次或合并。
- 多个 Design UNIT 和多个合法 iOS `doc_type` 可以合并为一个 implementation slice，只要每个文件仍遵守 iOS owner 层与依赖方向、合同已冻结且该 slice 有独立提交与回滚价值。`depends_on` 默认空；UNIT 编号或 domain-model → repository → usecase → viewmodel → view 写作顺序本身不是实现依赖。无法冻结且没有独立提交价值的候选 slices 必须合并。
- Full/high 恰好一个 Integration Slice。其 packet `target_paths` 是最终 union snapshot 的 review coverage；planning audit 的 `integration_owned_paths` 才是实际可写范围。普通 slices 只跑 focused checks，full regression 只出现在 Integration deterministic checks。
- 最终语义/静态证据必须检查 workflow 实际派发的 Implementation writer Skill 及其引用的 implementation standards；仅 Planner、Detail 或 reviewer parity 一致不足以满足 Integration。若任一 active Full/high ordinary consumer 仍要求 project/global build、analyze、lint 或 full regression command，或仍按 UNIT、layer、`doc_type`、ViewModel、UseCase 或 component 机械重切片，按 `IMPLEMENT_DEFECT` 阻断。
- 每个 v2 packet 保留并填实 `review_evidence_schema_version=2`、`requirements_design_inputs`、`target_paths`、`deterministic_checks`、`semantic_review_provider`、`invariants` 与 `integration_slice`。禁止为结构整齐默认生成一 UNIT 一 slice、单 ViewModel 一 slice、单 UseCase 一 slice 或单 View 一 slice。

---

## 0. 与详细设计的承接关系（开工前必须建立）

- 每个实现切片承接**至少一个** `UNIT-<slug>` 设计单元（语义 kebab-case 标题，下游引用裸 token）。引用不存在的 UNIT = 幽灵引用，被 gate 断链拦截。
- 每个 UNIT 自带一个 `doc_type`（七类之一）；切片的文件范围必须落在该 doc_type 的 owner 层内（归属硬基准，违反直接 fail）：
  - `view` / `viewmodel` → owner UI 层（`UI/Features/<Feature>/Views/`、`UI/Features/<Feature>/ViewModels/`）
  - `coordinator` → owner App 层（`App/Coordinators/`、`App/DependencyInjection/Container+*.swift`）
  - `usecase` / `domain-model` / `repository` 接口 → owner Domain 层（`App/UseCases/`、`Domain/Entities|ValueObjects|Enums|Errors/`、`Domain/Repositories/IXxxRepository.swift`）
  - `repository` 实现 / `external` → owner Infrastructure 层（`Infrastructure/Persistence/Repositories/`、`Infrastructure/Adapters/`、`Infrastructure/Services/`）
- 行为编号 `BHV-NNN`（来自 prd 标题）通过 UNIT 间接承接；trace 不重新发明行为。

---

## 必含四节

### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 任务切片 | 每片登记：① 真实标量 `owner_unit` 与 planning audit 中的 `covered_units`；② 涉及的 iOS 权威 `doc_type`；③ 文件范围（相对路径，每个文件落在对应 doc_type 的 owner 层内）；④ 完成信号；⑤ 验证方式。多个 ViewModel / UseCase / View 或跨多个合法 doc_type 可以合并，边界由文件级 ownership、冻结合同、独立 commit/rollback 价值与资源隔离决定。 |
| 执行顺序 | 按 audit 中真实 `depends_on` 与 `parallel_wave` 排序。`domain-model → repository → usecase → viewmodel → view + coordinator/external` 继续约束代码依赖方向，但不自动制造 slice 依赖；横切 DI 装配仍必须随其唯一 mutable owner 收口。 |
| 风险点 | 逐条预判高风险改动并写**验证手段**：① WCDBSwift 表结构/迁移（`ColumnCodable` 变更、`Table` 字段增删）；② FactoryKit DI 装配改动（`Container+*.swift` 改 graph 影响全局单例生命周期）；③ SwiftUI ↔ RxSwift 遗留桥接（`@Published` 与 `Observable` 共存的内存/线程风险）；④ AppCoordinator 导航枚举扩展（`NavigationDestination` 新增 case 的全量 switch 覆盖）；⑤ async/await 与 `MainActor` 线程归属。 |

**计划切片登记示例（表格形态）：**

| 切片 | 承接 UNIT | doc_type | 文件范围 | 完成信号 | 验证方式 |
|------|-----------|----------|---------|---------|---------|
| S1 | owner `UNIT-story-repository`; covered `UNIT-story-repository`, `UNIT-story-entity`, `UNIT-story-management-usecase` | `domain-model` / `repository` / `usecase` | `Domain/Entities/Story.swift`、`Domain/Errors/StoryError.swift`、`Domain/Repositories/IStoryRepository.swift`、`Infrastructure/Persistence/Repositories/StoryRepository.swift`、`App/UseCases/StoryManagement/*` | 冻结的领域/持久化/业务合同作为一个独立提交闭合，每个文件保持合法 owner 与单向依赖 | focused `xcodebuild test`（Story domain/repository/usecase tests）+ SwiftLint |
| S2 | owner `UNIT-home-viewmodel`; covered `UNIT-home-viewmodel`, `UNIT-home-view`, `UNIT-app-coordinator` | `viewmodel` / `view` / `coordinator` | `UI/Features/Home/**`、`App/Coordinators/AppCoordinator.swift`、`App/DependencyInjection/Container+ViewModels.swift` | 页面状态、展示、导航与 DI 在唯一 mutable owner 下闭合，不重写 S1 核心字节 | focused `xcodebuild test`（HomeViewModel/Coordinator）+ build + SwiftLint |

> 横切说明：`coordinator` 切片同时覆盖 FactoryKit DI 装配（`Container+ViewModels.swift` / `Container+UseCases.swift` / `Container+Coordinators.swift`）——新增单元必须有对应 `Factory<I...>` 注册，否则 `@Injected` 运行期解析失败（属可验证完成信号之一）。

### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个任务切片完成时记录下列字段：

- **实际改动文件清单**（相对路径，逐文件）。区分新增 / 修改 / 删除。
- **与计划的偏差**：改了计划外文件 / 没改计划内文件 → **必须写原因**（例如「`Container+UseCases.swift` 计划外修改：新 UseCase 需注册 `Factory`，属 DI 装配必经」）。
- **DI 装配登记**：每个新增的 `viewmodel` / `usecase` / `repository` 实现 / `external` 必须在 `App/DependencyInjection/Container+*.swift` 注册 `Factory`（`self { ... }.singleton` 或非单例形态），并记录注册行位置。禁手动初始化（`init` 直接 new 依赖 = golden-path 违例，记债或回退）。
- **平台约定落地点**：逐项确认本切片触碰的 golden-path 锁定项已落地——
  - FactoryKit `@Injected` 注入（无手动初始化）；
  - Repository 模式（UI/usecase 不直连 WCDBSwift，必经 `IXxxRepository`）；
  - `enum Error` 分层定义（Domain 错误在 `Domain/Errors/`，UseCase 错误在各 UseCase 目录的 `XxxError.swift`，Infrastructure 错误在对应模块）；
  - WCDBSwift 持久化（**禁 CoreData / SwiftData**）；
  - ViewModel = `ObservableObject` + `@Published`；
  - `private` 方法置于 `private extension`。
- **代码生成 / 脚手架记录**：若使用 mock 生成（project-conventions 槽位：手写 → Mockolo）或 R.swift 资源生成，记录跑了哪个命令、产物文件。无代码生成则显式写「本切片无生成步骤（手写实现 + 手写 mock）」。

### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

> `verification-evidence.jsonl` 只写「全部通过」= 反模式。每条必须带**命令 + 结果（测试名级别）**。
> 构建系统基准：本平台为 CocoaPods 工作区（`Podfile` 依赖 SwiftLint 0.31.0 / RxSwift / Moya / SwiftyBeaver 等），主用 `xcodebuild`；纯 SPM 包（Domain 抽离为独立 package 时）可用 `swift build` / `swift test`。两套命令按目标仓库实际构建形态二选一，trace 记录实际所用那套。

| 类型 | 要求 | iOS 命令基线（按实际仓库填实参） |
|------|------|------|
| 编译 / 静态检查 | Full/high ordinary slice 只运行 packet 声明的 focused build/test/lint；全 workspace build 与全项目 SwiftLint 只由 Integration 运行。非 Full/high 任务继续按原 route 合同。记录命令 + 通过/失败 + 失败处理。 | ordinary：affected-file SwiftLint 与 packet exact focused command；Integration：SPM `swift build` 或 workspace `xcodebuild build ...` + full SwiftLint |
| 测试 | 每个切片对应测试命令 + 结果**到测试名级别**（不只写「通过」）；新增测试清单逐条列出（`XCTestCase` 子类名 + `test*` 方法名）。 | SPM 包：`swift test --filter <ClassName>`；工作区：`xcodebuild test -workspace StoryVerse.xcworkspace -scheme StoryVerse -destination 'platform=macOS' -only-testing:StoryVerseTests/<ClassName>/<testMethod>` |
| 未验证项 | 无法本地验证的（真机 / 设备能力 / 大模型推理 / TTS 真实音频 / GPU 图像生成 / WhisperKit 设备端表现）→ **显式列出** + 留给哪个环节（Manual QA / 真机池 / 性能基准跑）。 | — |

**测试分层与 doc_type 映射（取证口径，与详细设计「测试映射」八问之七对齐）：**

| doc_type | 主测试层 | 取证要点 |
|----------|---------|---------|
| `domain-model` | unit（`XCTest`） | 不变量 / `enum Error` 等值（`Equatable`）/ 值对象构造校验，纯逻辑无 mock |
| `repository` | unit（mock DatabaseManager，见 `MockDatabaseManager.swift`）+ integration（真实 WCDBSwift，临时库文件） | 错误映射表逐条用例；mapper 双向；CRUD 幂等；`StoryRepositoryTests` / `VoiceProfileRepositoryTests` 为参照 |
| `usecase` | unit（mock repository 接口）——**测试密度最高层** | 每条承接行为 ≥1 成功 + ≥1 失败用例；业务错误枚举逐条；`StoryManagementUseCaseTests` 为参照 |
| `viewmodel` | unit（mock usecase 接口，断言 `@Published` 状态转移） | 事件 → 三态（loading / 数据 / error）转移；订阅取消（无内存泄漏） |
| `view` | 不在此层做结构断言（SwiftUI 视图归 Manual QA / 快照，按需）；逻辑应已下沉 viewmodel | 列入「未验证项」或快照测试（若仓库已有快照基线） |
| `coordinator` | unit（断言 `NavigationDestination` 转移）+ DI 解析冒烟（`Container` 能解析全部新增 `Factory`） | 导航枚举 case 转移；`@Injected` 解析不崩 |
| `external` | unit（mock SDK 边界）+ integration（真实集成留真机/Manual QA） | 错误上抛不吞；SDK 异常 → 业务错误映射；网络/SDK 真实路径列未验证项 |

> 测试框架口径：project-conventions 槽位为「XCTest → Quick/Nimble」。trace 记录本切片实际所用框架；存量 `XCTest`（如 `StoryVerseTests/`）按存量处置，新增切片若已切 Quick/Nimble 则用 `describe/it` 命名，证据仍记到 example 名级别。

**证据登记示例（切片 S3）：**

```
切片 S3 / UNIT-story-management-usecase / doc_type=usecase
- focused 静态检查：Pods/SwiftLint/swiftlint lint <affected-files> --strict → 0 violations
- 测试：xcodebuild test ... -only-testing:StoryVerseTests/StoryManagementUseCaseTests → 全部 PASS
  · test_createStory_成功_返回持久化Story
  · test_createStory_校验失败_抛StoryManagementError.validationFailed
  · test_deleteStory_找不到ID_抛StoryManagementError.notFound
  · test_observeStories_保存后流发射新列表
- 新增测试：StoryManagementUseCaseTests（4 个 test 方法，mock IStoryRepository + MockSystemStoriesInitializer）
- 未验证项：无（纯 domain 编排，本地全覆盖）
```

### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- **上游缺陷（详细设计错/漏）**：详细设计合同写错或漏（如 UNIT 的错误枚举不全、依赖方向写反、签名与实现对不上）→ 记录后**回退详细阶段修订**，不在 trace / 代码里就地改设计。`implementation-evidence.jsonl` 留回退记录（哪个 UNIT、缺什么、回退动作）。
  - 示例：「`UNIT-voice-repository` 合同未声明 remote 失败回落策略，实现无据可依 → 回退详细设计补编排策略，trace 暂挂该切片。」
- **存量违例触碰**：列出触碰的存量违例条目编号（golden-path / 详细设计的存量豁免清单中登记的违例）+ 处置（绕行 / 顺手修复 / 记债）。iOS 典型存量违例域：
  - SwiftUI 主 + **RxSwift 遗留**桥接代码（迁移中的双轨）；
  - 日志 SwiftyBeaver → OSLog 迁移期的混用；
  - mock 手写 → Mockolo 迁移期的手写 mock；
  - 测试框架 XCTest → Quick/Nimble 迁移期。
  触碰时若不在本切片 scope 内，记债不阻塞；新增代码引入新违例则阻塞（必须修或显式升级）。
- **未决决策**：实现中冒出的新决策点（如「WCDBSwift 表加索引会否影响现有迁移」「某 SDK 仅真机可用，CI 如何 mock」）→ **不私自拍板**，记录并升级人工 Gate。
- **分层依赖律违反（硬 fail，必须当场处置）**：实现中若出现以下任一，立即停止该切片并记录回退动作——
  - Domain 层文件出现非 `Foundation`/标准库 import（Domain 零依赖被破坏）；
  - `view` 直接访问 WCDBSwift / Repository 实现（绕过 viewmodel→usecase→repository）；
  - `view` 间直接导航（未走 coordinator）；
  - 依赖方向逆行（如 `usecase` 反向依赖 `viewmodel`，或 Domain 依赖 Infrastructure 具体实现而非接口）；
  - 手动 `init` 注入替代 FactoryKit `@Injected`。

---

## Gate 判定（实现阶段进 commit 的充要条件）

实现切片可进入 commit，当且仅当：

- **GI-1** `implement.md` 计划合同与 mutable evidence 齐全（计划 / 执行 / 证据 / 阻塞偏差），无空记录、无 TODO 占位。
- **GI-2** 每个切片的真实 `owner_unit` 与 planning audit `covered_units` 均存在于详细设计（无幽灵引用）；涉及的每个 `doc_type` 均为 iOS 七类之一，且每个文件落在对应 doc_type owner 层内。
- **GI-3** `verification-evidence.jsonl`：Full/high ordinary slice 有 packet focused commands 的结果，Integration 有 full build/regression/SwiftLint 结果；非 Full/high 任务按原 route 合同。测试结果必须到测试名级别；无「全部通过」式无命令证据。
- **GI-4** golden-path 锁定项逐项落地（FactoryKit `@Injected` 无手动初始化 / Repository 模式 / `enum Error` 分层 / WCDBSwift 无 CoreData·SwiftData / ViewModel=`ObservableObject`+`@Published` / `private` 在 `private extension`）。
- **GI-5** 分层依赖律零违反（Domain 零依赖；Domain→App→Infrastructure→UI 单向；View 不直连持久化、不互相导航）。
- **GI-6** 偏差与存量违例均有记录与处置；未决决策已升级（无私自拍板）。
- **GI-7** DI 装配闭合：每个新增 `viewmodel`/`usecase`/`repository` 实现/`external` 在 `Container+*.swift` 有对应 `Factory` 注册，`@Injected` 可解析。

任一不满足 → 不进 commit；上游结构性缺陷只能回拥有该决策的阶段修订，禁止下游补造。

---

## 反模式

- ❌ trace 在 PR 前一次性补写（失去过程证据意义）。
- ❌ mutable evidence 只写「全部通过」/「编译 OK」（无命令、无测试名、无 SwiftLint 结果）。
- ❌ 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
- ❌ doc_type 自创（写成 `service` / `controller` / `data-source` / `transport-handler`——必须用 iOS 权威七类）。
- ❌ 切片不承接 UNIT 或承接不存在的 UNIT（幽灵引用）。
- ❌ 实现期就地改详细设计 owner / 依赖方向 / scope（应回退详细阶段）。
- ❌ 手动 `init` new 依赖替代 FactoryKit `@Injected`；`view` 直连 WCDBSwift；`view` 间 `NavigationLink` 直跳绕过 AppCoordinator。
- ❌ 用 CoreData / SwiftData 替代 WCDBSwift；用 `class` 普通对象替代 `ObservableObject`+`@Published` 的 ViewModel。
