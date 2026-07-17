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

## Full/high slice planning audit

Full/high 的 `implement.md` 必须有 slice planning audit，目标是**最少的 commit-stable slices 和最大的安全并发宽度**，不是按 UNIT、`doc_type`、层或章节机械拆分。每个普通 slice 登记 `slice_id`、真实标量 `owner_unit`、`covered_units`、文件级 `owned_paths`、`read_paths`、`depends_on`、`parallel_wave`、`independent_commit_value`、`rollback_contract`、`resource_locks` / 隔离方式、focused checks 和 reviewer context inputs/bytes。`covered_units` 是包含 `owner_unit` 在内的完整 Design UNIT 集合，只属于 planning audit；不得新增或重定义 packet / evidence schema 字段。

- 一个普通 mutable path 在同一 implementation wave 只有一个 owner；symbol、函数或 diff hunk 不能绕过文件级 ownership。共享测试文件也必须唯一归属、分波次或合并。
- 多个 Design UNIT 可以合并为一个 implementation slice，只要 ownership 不重叠、合同已冻结且该 slice 有独立提交与回滚价值。`depends_on` 默认空；UNIT 编号、`doc_type` 或 data/domain/presentation 写作顺序本身不是实现依赖。无法冻结且没有独立提交价值的候选 slices 必须合并。
- Full/high 恰好一个 Integration Slice。其 packet `target_paths` 是最终 union snapshot 的 review coverage；planning audit 的 `integration_owned_paths` 才是实际可写范围。普通 slices 只跑 focused checks，full regression 只出现在 Integration deterministic checks。
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
| 测试 | 每个切片对应的测试命令 + 结果（测试名级别，不只写"通过"）；新增测试清单。**P1：测试按 invariant 归档**（不只按文件/命令）——每条 high-risk invariant 至少一个正/负测试作为其 `invariant_evidence`。 |
| 未验证项 | 无法本地验证的（真机表现、双端差异）→ 显式列出 + 留给哪个环节（Manual QA / 真机池）。 |

### 4. 阻塞与偏差（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

- 上游缺陷：详细设计合同错/漏（**含 invariant 缺失**）→ 记录后**回退详细阶段修订**，不就地改设计、不在实现 worker 内补造 invariant（`implementation-evidence.jsonl` 留回退记录）。
- 存量违例触碰：列出触碰的 SLOT-15 条目编号 + 处置（绕行/顺手修复/记债）。
- 未决决策：实现中冒出的新决策点 → 不私自拍板，记录并升级给人工 Gate。

## 反模式

- ❌ trace 在 PR 前一次性补写（失去过程证据意义）。
- ❌ mutable evidence 只写"全部通过"（无命令、无测试名）。
- ❌ 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
