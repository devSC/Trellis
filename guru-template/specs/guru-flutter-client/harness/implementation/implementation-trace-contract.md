# implementation-trace 合同

> `implement.md` / implementation-trace 是 detail Gate 的 digest-bearing planning contract。detail 确认后的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`。
> 建议路径：目标仓库 `docs/design/<feature>/implementation-trace.md`。若必须修改已确认 trace，必须回退 detail Gate 并重新 review/confirm。

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

## Acceptance Closure Matrix

当 Full 任务在 `prd.md`、Detail 或 `implement.md` 声明 `runtime_acceptance_required=true`，或任一验收目标涉及用户可见终态、外部 API/schema、持久化/缓存、异步状态或跨层字段转换时，Detail/`implement.md` 必须在开工前冻结 Acceptance Closure Matrix。触发条件取决于验收行为，不取决于本次 diff 修改了几层。

`runtime_acceptance_required=true` 只是 planning marker，不是 `task.json`、`gate-contract.json` 或新 lifecycle schema 字段。Matrix 是 detail Gate digest-bearing planning contract；Detail 确认后的执行结果只追加到 mutable evidence，不回写 Matrix。

每一行只描述一个可独立判定的验收目标，且至少包含：

| 字段 | 要求 |
| --- | --- |
| `acceptance_id` / 追溯 | 唯一 ID + 对应 BHV、AC 或 invariant + `required` |
| 用户结果 | 可见结果、允许的 terminal states，以及不得出现的中间态 |
| 入口/环境 | 触发入口、目标运行环境和必要前置 |
| 权威与 fingerprint | 外部/本地 source of truth；字段路径、presence/null 语义、脱敏 fixture/响应结构等最小合同指纹 |
| `source-to-sink` | 从权威输入到用户终态的所有逻辑层，以及关键字段/状态转换 |
| 正/负向路径 | 正常、缺字段/null、error/timeout/降级等适用路径与允许终态 |
| `falsifiable_check` | 能在旧错误实现上失败的 deterministic check；不能只证明修复后 helper 的 happy path |
| runtime probe/evidence | 目标环境步骤/命令、执行 owner、expected/actual 与所需脱敏 evidence refs |
| slice | 所属 ordinary Implementation Slice 与负责最终闭合的 Integration Slice |

模板：

| acceptance_id | BHV/AC/invariant | required | 用户结果/允许终态 | 入口/目标环境 | 权威 fingerprint | source-to-sink | 正/负向路径 | falsifiable check | runtime probe/owner/evidence | ordinary/Integration slice |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ACC-<DOMAIN>-001` | `BHV-NNN` | true | `<outcome / terminal states>` | `<entry / environment>` | `<authority / field-path / null semantics / sanitized fixture>` | `<source -> transforms -> sink>` | `<positive; missing/null; error/timeout/degraded>` | `<command/test that fails on known bad>` | `<steps / owner / expected / actual / evidence refs>` | `<ordinary slice / Integration>` |

普通 slice 的局部通过不能代替 Integration 的最终 source-to-sink 闭合。Integration 必须覆盖所有 runtime-required rows，并证明最终用户结果；无法自动化时必须保留明确 Manual QA/真机 owner 和 probe，不得以局部 green 补位。

### Runtime acceptance evidence 和 currentness

runtime 结果追加到 task-local `verification-evidence.jsonl`，每行至少记录 `acceptance_id`、`status`、current baseline binding（task/requirements/overview/detail/implementation snapshot）、environment、steps/command、expected、actual、脱敏 `evidence_refs`、`recorded_at` 和 `recorded_by`。历史行 append-only，不覆盖 failure/pass，不存储 secret、token、PII、完整请求/响应或用户内容。

| status/结论 | 语义 |
| --- | --- |
| `implementation_verified` | 静态、deterministic checks 和 review 通过，但未证明目标环境用户结果 |
| `runtime_acceptance_pending` | 已移交声明的 runtime probe，仍等待执行/证据 |
| `runtime_acceptance_failure` | actual 不满足声明的用户结果，需进入根因分类/修复延续 |
| `runtime_acceptance_pass` | 目标环境、步骤、expected、actual、evidence 和 current binding 完整 |
| `accepted` | 任务级报告结论；仅当所有 required rows 的 latest valid evidence 都是 current pass |

`accepted` 不是 evidence row status，也不是新 `task.json.status`。对每个 required `acceptance_id`，先过滤不匹配当前受影响 baseline 的 stale evidence，再取最新有效行；任何更新的 current non-pass row（包括 `implementation_verified`、pending 或 failure）必须压过更早 pass。任一 required row missing、non-pass、stale 或被更新非 pass 行取代时，只能报告 technical/runtime 状态和原 matrix probe，不得报告 `accepted`。

### Post-implementation failure retrospective

用户/QA 报告 `runtime_acceptance_failure` 后，repair 收口证据必须绑定同一 `acceptance_id` 并记录：

- 已证实的直接根因；
- 最早应捕获该缺陷的 Requirement/Design/Implementation/Test/Review/Process Gate；
- 既有测试与 Review 为何 false green；
- 能在旧错误实现上失败的新 regression/probe；
- 恰好一个完整 `prevention_disposition`：`writeback_required` 必须包含允许的 Skill/workflow/spec owner 和验证；`no_writeback_required` 必须包含明确理由和 evidence refs。

上述五项任一缺失、只写 TODO、两个 disposition 分支都填/都不填，或在已有充分预防证据时补造无必要 writeback，都必须保持 repair 未关闭。

## Full/high slice planning audit

Full/high 的 `implement.md` 必须有 slice planning audit，目标是**最少的 commit-stable slices 和最大的安全并发宽度**，不是按 UNIT、`doc_type`、层或章节机械拆分。每个普通 slice 登记 `slice_id`、真实标量 `owner_unit`、`covered_units`、文件级 `owned_paths`、`read_paths`、`depends_on`、`parallel_wave`、`independent_commit_value`、`rollback_contract`、`resource_locks` / 隔离方式、focused checks 和 reviewer context inputs/bytes。`covered_units` 是包含 `owner_unit` 在内的完整 Design UNIT 集合，只属于 planning audit；不得新增或重定义 packet / evidence schema 字段。

- 一个普通 mutable path 在同一 implementation wave 只有一个 owner；symbol、函数或 diff hunk 不能绕过文件级 ownership。共享测试文件也必须唯一归属、分波次或合并。
- 多个 Design UNIT 可以合并为一个 implementation slice，只要 ownership 不重叠、合同已冻结且该 slice 有独立提交与回滚价值。`depends_on` 默认空；UNIT 编号、`doc_type` 或 data/domain/presentation 写作顺序本身不是实现依赖。无法冻结且没有独立提交价值的候选 slices 必须合并。
- Full/high 恰好一个 Integration Slice。其 packet `target_paths` 是最终 union snapshot 的 review coverage；planning audit 的 `integration_owned_paths` 才是实际可写范围。普通 slices 只跑 focused checks，full regression 只出现在 Integration deterministic checks。
- 最终语义/静态证据必须检查 workflow 实际派发的 Implementation writer Skill 及其引用的 implementation standards；仅 Planner、Detail 或 reviewer parity 一致不足以满足 Integration。若任一 active Full/high ordinary consumer 仍要求 project/global build、analyze、lint 或 full regression command，或仍按 UNIT、layer、`doc_type`、ViewModel、UseCase 或 component 机械重切片，按 `IMPLEMENT_DEFECT` 阻断。
- 每个 v2 packet 保留并填实 `review_evidence_schema_version=2`、`requirements_design_inputs`、`target_paths`、`deterministic_checks`、`semantic_review_provider`、`invariants` 与 `integration_slice`。禁止为结构整齐默认生成一 UNIT 一 slice 或一 `doc_type` 一 slice。

## 必含四节

### 1. 计划（开工前写）

| 字段 | 要求 |
|------|------|
| 任务切片 | 每片：真实 `owner_unit` + planning audit 中的 `covered_units` + 涉及的 doc_type / **`target_paths` 文件范围摘要** / 完成信号 / 验证方式。切片边界由文件级 mutable ownership、冻结合同、独立 commit/rollback 价值与资源隔离共同决定，不按 UNIT 或层机械拆分。**P1 high-risk slice 额外必填**：`slice_packet` 路径 + `invariant_ids` + `negative_case` 摘要（机器内容以 packet 为准）。 |
| 执行顺序 | 按 audit 中真实 `depends_on` 与 `parallel_wave` 排序；data → domain → presentation 只约束平台依赖方向，不自动制造 slice 依赖。 |
| 风险点 | 预判的高风险改动（迁移、共享状态、平台差异），逐条写验证手段。 |

### 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个任务切片完成时记录下列字段：
- 实际改动文件清单（相对路径）。
- 与计划的偏差（改了计划外文件 / 没改计划内文件 → 必须写原因）。
- 代码生成执行记录（跑了哪个脚本，按 `[SLOT-08]`）。

### 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

| 类型 | 要求 |
|------|------|
| 静态检查 | Full/high ordinary slice 只记录 packet 中 exact focused command 的结果（例如受影响路径的 analyze/custom_lint）；全项目 `flutter analyze`、完整 custom lint 或其他 full regression 只由 Integration 记录。非 Full/high 任务继续按原 route 合同记录。 |
| 测试 | Full/high ordinary 仅当 current packet 或 planning audit focused checks 明确声明测试时，才记录测试命令、测试名级别结果、新增测试清单及正/负路径；不得为满足通用 trace Gate 自行运行 undeclared tests。Integration 或 non-Full/v1 保留原合同：每个切片记录测试命令与测试名级别结果，并按 invariant 归档 high-risk 正/负测试证据。 |
| Acceptance closure | 记录每个受影响 `acceptance_id` 的 deterministic check、known-bad 失败证据、source-to-sink Integration 结果和 baseline binding；不得用 ordinary/local green 代替 Integration 或 runtime outcome。 |
| Runtime acceptance | 对 required rows 追加 `implementation_verified` / `runtime_acceptance_pending` / `runtime_acceptance_failure` / `runtime_acceptance_pass` 与目标环境、步骤、expected/actual、脱敏 evidence refs 和 current baseline binding；全部 latest current pass 之前不得记录或报告 `accepted`。 |
| 未验证项 | 无法本地验证的（真机表现、双端差异）→ 显式列出 + 留给哪个环节（Manual QA / 真机池）。 |

### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- 上游缺陷：详细设计合同错/漏（**含 invariant 缺失**）→ 记录后**回退详细阶段修订**，不就地改设计、不在实现 worker 内补造 invariant（`implementation-evidence.jsonl` 留回退记录）。
- 验收闭合缺口：Acceptance Closure Matrix 缺行/路径、fingerprint 不足、check 无法在 known-bad 上失败，或 runtime probe/evidence owner 不可执行 → 停止扩写实现，记录精确缺口并回到 planning owner；不因当前 diff 仅有一层而跳过。
- Runtime failure retrospective：用户/QA 失败后，直接根因、最早漏检 Gate、false-green 原因、known-bad 可失败 regression 与恰好一个完整 prevention disposition 未齐全时，必须显式保持 repair 未关闭。
- 存量违例触碰：列出触碰的 SLOT-15 条目编号 + 处置（绕行/顺手修复/记债）。
- 未决决策：实现中冒出的新决策点 → 不私自拍板，记录并升级给人工 Gate。

## 反模式

- ❌ trace 在 PR 前一次性补写（失去过程证据意义）。
- ❌ mutable evidence 只写"全部通过"（无命令；当前 route/packet 声明测试时还缺测试名）。
- ❌ 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
