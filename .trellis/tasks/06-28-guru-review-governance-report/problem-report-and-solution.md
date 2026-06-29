# Guru Review 治理问题报告与解决方案

## 1. 执行摘要

Himora V2 grouped-media 迁移中，Guru 系 review 没有在早期挡住多个跨层语义缺陷。根因不是“没有强制 OCR”，而是 Guru review 的硬约束主要覆盖阶段完整性、结构闭合和宽泛实现审查；它缺少能让 reviewer 逐条判定的实现期不变量矩阵、slice scope gate、dirty diff 隔离和结构化 review record。

正确修复方向不是把 OCR 变成硬 Gate，而是把 Guru review 自身升级为：

1. deterministic checks 先行；
2. review target 必须窄化到 commit / range / staged diff / single slice；
3. high-risk slice 必须提供 invariant matrix；
4. semantic review provider 可替换，Claude / Codex / manual / OCR 都只是 provider；
5. review 结论必须结构化记录，并能触发 `REQ_BLOCKER` / `OVERVIEW_DEFECT` / `DETAIL_DEFECT` / `IMPLEMENT_DEFECT` / `PROCESS_DEFECT` 回退。

## 2. 事实与证据

### 2.1 当前 Guru Gate 的边界

`guru_gate.py` 明确声明“只查结构存在性与引用闭合，不做语义判断”。它能检查 `prd.md`、BHV / UNIT、review evidence、trace 四节，但不能判断 DTO 解析、repository projection、DAO merge、current selection 等跨层协议语义。

证据：

- `guru-template/overlay/verify/guru_gate.py:1`：Gate 脚本定位为五阶段 Gate 校验与追溯矩阵。
- `guru-template/overlay/verify/guru_gate.py:40`：设计约束是不做语义判断。

### 2.2 实现期 review 的输入过宽

`guru_supervise.py` 的 implementation check brief 仍是 “review the current diff under Guru quality rules”。这会让 check worker 面对混合 diff，而不是明确的单 slice review target。

证据：

- `guru-template/overlay/verify/guru_supervise.py:39`：implement-check 最多 3 个 repair loops。
- `guru-template/overlay/verify/guru_supervise.py:43`：adversarial model actions 只覆盖 requirements / overview / detail，不覆盖 implement / check。
- `guru-template/overlay/verify/guru_supervise.py:643`：implement-check 只要求 review current diff under Guru quality rules。

### 2.3 实现 review skill 有审查口径，但缺少运行时强制输入

`flutter-implementation-guru-review` 已要求合同一致性、分层、证据核查、route_class 输出，但它也声明只审改动面及直接依赖。没有 scope gate 时，大 diff 会让 reviewer 只能抽查主干路径。

证据：

- `guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md:17`：要求 diff 与详细设计单元逐一对照。
- `guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md:23`：要求核查 trace 和测试证据。
- `guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md:50`：边界是只审改动面与直接依赖。

### 2.4 trace 合同写了小 slice，但没被 runtime 强制

implementation trace 合同要求每个任务切片小到可独立 review，但当前实现 Gate 主要检查 trace 四节和 UNIT 引用，没有验证真实 diff 是否对应单 slice。

证据：

- `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md:12`：每片小到可独立 review。
- `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md:27`：静态检查证据。
- `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md:33`：上游缺陷应回退详细阶段。

### 2.5 Himora 事故表明缺的是负向不变量

Himora V2 grouped-media 最终缺陷是：远端 V2 group 未返回的本地 grouped media item 被 local merge 重新 append 回当前 visible `displayItems`。正确规则是：本地库可以补 facts，但不能决定当前 V2 Cell membership。

证据：

- 事故摘要显示日志里 moments 已 completed，但聊天侧仍显示 `remoteOnly`，定位到 merge / projection mismatch。
- 后续 fix 改为：V2 remote summary 只对 remote-present item 合并 local facts，不再 append unmatched local item。
- 新增测试 `keeps omitted V2 grouped media stored but not displayed`。

这类问题不是格式、lint 或普通架构违规，而是跨 API / DTO / repository / DAO / UI projection 的负向语义合同。

## 3. 根因分析

### 3.1 根因一：早期 review 没有可执行不变量矩阵

需求 / 设计里有“旧版本媒体继续展示”，也有“V2 group 权威结构”，但如果没有显式写成可判定规则，reviewer 容易把它理解成“本地已有旧媒体就尽量恢复展示”。

缺失的不变量示例：

| invariant_id | 规则 | 应覆盖的反例 |
| --- | --- | --- |
| INV-V2-GROUP-AUTHORITY | V2 nested group 一旦出现，同 source 的 flat fallback 不能补同类型 Cell | partial V2 group 缺 videoGroup 时，不得从 flat media 补 video Cell |
| INV-LOCAL-FACTS-ONLY | local DB 只能补 status / liked / attempt / url 等 facts，不能决定当前 V2 Cell membership | remote V2 group 未返回的本地 item 不得 append 到 visible displayItems |
| INV-CURRENT-SELECTION | group.current 决定 Cell 当前项 | selectedInGroup 不能被 fallback 或 local order 覆盖 |
| INV-LEGACY-ISOLATION | 非 V2 legacy flat media 在混合页仍保留 | V2 source 屏蔽 flat fallback 时不能误删非 V2 source |

### 3.2 根因二：review target 没有窄化

如果一个 check 同时面对 API client、DTO、repository projection、DAO local merge、controller、widget tests 和 generated files，reviewer 很难系统证明每个 edge case。

需要把 review target 改成：

- `target_kind`: `slice | staged | commit | range`
- `target_paths`: 文件清单
- `slice_id`: 关联 trace slice；第一版直接使用现有 `UNIT-<slug>` 作为 join key，避免另引入 `SL-xx` 体系
- `invariant_ids`: 本轮必须检查的不变量
- `deterministic_checks`: 已运行命令与结果
- `dirty_state`: 与本任务无关的 dirty paths

### 3.3 根因三：implementation check 缺少独立对抗 review

当前 adversarial 只覆盖 requirements / overview / detail。代码实现阶段最容易出现实际语义偏差，却没有相同等级的 opposite-provider review 机制。

这不意味着必须启用 OCR。更合理的是把 implementation semantic review provider 抽象出来：

- `manual`
- `codex`
- `claude`
- `ocr_optional`

高风险 slice 默认至少需要一个非实现者 review provider；OCR 不在默认必选集合。

### 3.4 根因四：review record 不够结构化

overview/detail 有 review_runs 和 digest；implementation check 主要依赖文本里的 `review_result=clean/final-verification-ready`。这不够支持审计：

- 不知道审的是哪个 target；
- 不知道覆盖了哪些 invariants；
- 不知道哪些 deterministic checks 先通过；
- 不知道剩余 P2 / follow-up / nice-to-have 是否被接受；
- 不知道是否有 dirty diff 干扰。

## 4. 解决方案

### 4.1 原则

1. OCR 不是硬依赖。OCR 只能作为 optional semantic review provider。
2. deterministic checks 是 gating 目标。P0 由 worker 按 packet 中可复跑命令执行并自报，packet 命令是可复跑 SSOT；supervisor-side 真正硬 Gate 在 P1 落地。
3. Guru review 的输入必须可判定。没有 slice packet / invariant matrix，不允许声称 clean。
4. 上游合同缺失必须回退。实现中发现 detail 缺不变量，应输出 `DETAIL_DEFECT`，先补设计合同。
5. dirty worktree 必须隔离。review target 之外的 staged / unstaged / untracked 必须显式列出并排除。

### 4.2 新增 Slice Review Packet

每个 high-risk implementation slice 在进入 semantic review 前必须生成一个机器可读 packet。

唯一落地位置：

```text
<task_dir>/slice-packets/<unit_id>.json
```

生产者：

- supervised 模式下，packet 是实现前输入合同：由主会话 / planning-writing 阶段基于 `implement.md` 与 detail contract 创建，必须在首次 `guru_supervise.py implement-check` 前已经存在；
- `flutter-implementation-guru-writing` 在实现 high-risk slice 前读取并校验 packet，可补充 deterministic check 计划，但不承担首次创建 packet；
- inline 模式由主 agent 在编辑前创建；
- packet 文件名、`slice_id` 和 `owner_unit` 第一版都使用现有 `UNIT-<slug>`；`implement.md` 计划节必须列出同一个 UNIT 与 `slice_packet` 路径，作为 packet ↔ trace 的机器 join key。

消费者：

- `guru_supervise.py implement-check` 在 spawn implement / check worker 前读取 packet 并做 scope preflight；
- `flutter-implementation-guru-review` 审查时读取同一 packet；
- `implement.md` 只写人类摘要，不作为 matrix 的机器 SSOT。

schema 校验：

- P0 使用 Python stdlib `json` 解析，不引入 YAML 依赖；
- P0 先在 `guru_supervise.py` 内做最小 JSON 解析与必填字段校验；
- `schema_version` 必须为 `1`；未知版本硬停并提示升级 `guru_supervise.py`，不能静默按 v1 解析；
- 后续可抽到 `guru_gate.py validate-slice-packet <task_dir> <unit_id>`，但第一版不依赖新增命令。

```json
{
  "schema_version": 1,
  "slice_id": "UNIT-generated-media-local-state-dao",
  "risk": "high",
  "risk_reasons": ["protocol_migration", "cross_layer", "stateful_cache_merge"],
  "target_kind": "staged",
  "target_paths": [
    "lib/data/datasources/affiny_chat_local_data_source_impl.dart",
    "test/data/datasources/affiny_chat_local_data_source_test.dart"
  ],
  "owner_unit": "UNIT-generated-media-local-state-dao",
  "invariants": [
    {
      "invariant_id": "INV-LOCAL-FACTS-ONLY",
      "rule": "Local DB may enrich status, urls, attempt metadata, and persistence facts for remote-present V2 items, but must not append remote-omitted V2 items into visible displayItems.",
      "source": "detail",
      "owner": "DAO",
      "positive_case": "A remote-present item receives local facts without changing group membership.",
      "negative_case": "A remote-omitted V2 item remains stored locally but is not displayed in the current summary.",
      "test_evidence": [
        "flutter test test/data/datasources/affiny_chat_local_data_source_test.dart --name \"keeps omitted V2 grouped media stored but not displayed\""
      ],
      "route_if_missing": "DETAIL_DEFECT"
    },
    {
      "invariant_id": "INV-V2-GROUP-AUTHORITY",
      "rule": "When a V2 nested group exists for the same source, that remote V2 group is authoritative for visible cell membership.",
      "source": "detail",
      "owner": "repository_projection",
      "positive_case": "Remote V2 group members render as cells in current group order.",
      "negative_case": "Flat fallback or local cache does not add an omitted same-source cell.",
      "test_evidence": [],
      "route_if_missing": "DETAIL_DEFECT"
    }
  ],
  "deterministic_checks": [
    "dart analyze lib/data/datasources/affiny_chat_local_data_source_impl.dart test/data/datasources/affiny_chat_local_data_source_test.dart",
    "dart format --output=none --set-exit-if-changed lib/data/datasources/affiny_chat_local_data_source_impl.dart test/data/datasources/affiny_chat_local_data_source_test.dart"
  ],
  "dirty_state": {
    "unrelated": ["pubspec.lock"]
  },
  "semantic_review_provider": {
    "required": true,
    "provider": "claude",
    "ocr": "optional"
  }
}
```

### 4.3 新增 Invariant Matrix

Slice packet 的 `invariants[]` 是 invariant matrix 的唯一机器 SSOT；`implement.md` 和设计包只能引用或摘要，不再维护第二份机器矩阵。这样避免 gate 读 A、skill 读 B 时产生漂移。

| invariant_id | source | owner | positive case | negative case | test evidence | route if missing |
| --- | --- | --- | --- | --- | --- | --- |
| INV-LOCAL-FACTS-ONLY | detail / requirement-api | DAO | remote item gets local facts | omitted remote V2 item stays stored but not displayed | datasource unit test | DETAIL_DEFECT |

审查时必须逐条给出 `pass / fail / not_applicable`。packet schema 必填 `invariant_id`、`rule`、`source`、`owner`、`positive_case`、`negative_case`、`test_evidence`、`route_if_missing`；只给 invariant id 不合格，因为 reviewer 无法从 id 推断负向语义合同。
`invariant_coverage` 聚合规则：任一 invariant 为 `fail` 则 `failed`；任一 high-risk invariant 没有证据且不能合理标为 `not_applicable` 则 `missing`；其余情况，包括部分 invariant 明确 `not_applicable` 且理由成立，聚合为 `all_passed`。
这里的“证据”以审查期 reviewer 对实际测试、命令输出、代码路径和记录文件的判定为准；packet 创建期的 `test_evidence[]` 是计划指针，可以为空。实现后向某个 invariant 补充测试名、命令或证据文件属于允许的 evidence 补充，不改变 invariant 语义；不得在实现后改写 `rule`、`positive_case`、`negative_case`、`owner` 或 `route_if_missing` 来迁就实现。
第一版中，high-risk invariant 定义为 `risk=high|critical` 的 slice packet 内全部 `invariants[]`；不额外引入 per-invariant criticality 字段，避免同一 packet 内多套风险口径。

### 4.4 修改 Implementation Review 输出合同

implementation check 不再只输出自由文本。worker 输出必须置顶：

```text
review_result=clean|findings|blocked
route_class=none|IMPLEMENT_DEFECT|PROCESS_DEFECT|DETAIL_DEFECT|OVERVIEW_DEFECT|REQ_BLOCKER
review_target=<slice|staged|commit|range>:<id>
review_provider=<manual|codex|claude|ocr_optional>
deterministic_checks=<passed|failed|missing>
dirty_scope=<clean|isolated|invalid>
invariant_coverage=<all_passed|failed|missing>
```

字段语义：

- `review_result` 和 `route_class` 仍是 worker 输出的最小字段。
- `review_result` 的 jsonl 规范值固定为 `clean|findings|blocked`。worker 兼容输入可以把 `final-verification-ready` 作为 `clean` 的同义裁决；`guru_review_record.py` 在写入前统一归一为 `review_result=clean`，manual CLI `--result clean` 直接使用同一规范值。
- `review_target`、`review_provider`、`deterministic_checks`、`dirty_scope`、`invariant_coverage` 第一版作为 gating 字段解析；缺失任一字段时，check 不可 clean。
- 取值级 gating：归一后的 `review_result=clean` 仅当 `deterministic_checks=passed`、`dirty_scope in {clean,isolated}`、`invariant_coverage=all_passed` 时可接受；任一字段存在但取非通过值却仍声明 clean，supervisor 按 `MALFORMED_REVIEW_OUTPUT` 拒绝并写入 jsonl，不接受为成功。
- P0 中 `deterministic_checks` 由 worker 按 packet 命令执行并自报，packet 内命令是可复跑 SSOT；supervisor 可做廉价抽检但不作为 P0 必需项。若要把 deterministic checks 升级为真正 supervisor-side hard Gate，作为 P1 由 supervisor 在 preflight 后独立执行 packet.deterministic_checks 并比对结果。
- `SCOPE_INVALID` 和 `MALFORMED_REVIEW_OUTPUT` 是 supervisor-only failure code，写入 `implementation-reviews.jsonl.supervisor_failure`，不属于 worker `route_class`，不要求扩展 worker `ROUTE_RE`，也不要求 worker 在置顶输出里打印 `supervisor_failure`。
- worker 若输出 `clean` 但缺少新增 gating 字段，supervisor 记录 `review_result=blocked`、`route_class=none`、`supervisor_failure=MALFORMED_REVIEW_OUTPUT`、`repairable=false`，exit 2；不能把格式不合格的 clean 当作成功，也不能让 implement worker 空转修复审查格式。
- supervisor 在每轮 check 后追加结构化记录到：

```text
<task_dir>/review-records/implementation-reviews.jsonl
```

每行包含 `run_id`、`slice_id`、`target_paths`、`review_provider`、`route_class`、`review_result`、`deterministic_checks`、`dirty_scope`、`invariant_coverage`、`channel`、`worker`、`timestamp`、`supervisor_failure`、`repairable`。`supervisor_failure` 正常 worker 轮次为 `none`，supervisor 硬停轮次填 `SCOPE_INVALID` 或 `MALFORMED_REVIEW_OUTPUT`；`repairable` 正常 worker finding 根据 `route_class` 判定，supervisor 硬停为 `false`。channel events 仍保留原始审查输出，jsonl 是任务内可审计索引。非 channel provider 仍写同一字段：manual 行固定 `channel=manual`、`worker=<reviewer>`；显式触发的 OCR 行固定 `channel=ocr_optional`、`worker=<tool-or-run-id>`。这些 sentinel 由 `guru_review_record.py append` 根据 `--provider`、`--reviewer`、`--run-id` 派生，不要求手工传 `--channel` / `--worker`。supervisor 与 manual / OCR append 都必须复用 `guru_review_record.py` 的共享 schema 校验与写入函数，避免一个 jsonl 两套 writer 漂移。取值级一致性拒绝也属于该共享校验：任何 provider 写入 clean 型裁决时，必须同时满足 `deterministic_checks=passed`、`dirty_scope in {clean,isolated}`、`invariant_coverage=all_passed`；否则由共享 writer 拒绝并记录 / 返回 `MALFORMED_REVIEW_OUTPUT`。该判定由 `guru_review_record.py` 暴露的单一共享校验函数承担，supervisor 的 parse-time route / exit gating 与 manual / OCR append 的 write-time gating 都调用它，不能在两侧各自实现。

### 4.5 修改 `guru_supervise.py implement-check`

优先级 P0：

1. 第一版 P0 范围限定为 `platform=flutter`。`guru_supervise.py` 的 preflight 只对 Flutter 的 high-risk implementation check 强制 slice packet；high-risk 判定见 §4.5.9。go / ios / h5 不在本次治理 P0 范围，避免平台无关 supervisor 要求非 Flutter skill 产出不存在的 packet。
2. 对 high-risk Flutter check，在进入 implement-check 修复循环前读取已存在的 `<task_dir>/slice-packets/<unit_id>.json`。第一版可以通过 `--slice <unit_id>` 显式传入；若未传入且 task 只有一个 packet，可自动选择；多个 packet 且未指定时硬停。packet 缺失是 planning / implementation-writing 合同缺失，supervisor 直接硬停，不启动 implement worker 现场补造。
3. 在进入 implement-check 修复循环前执行一次 scope preflight：
   - `git status --short`
   - `git diff --name-only`
   - `git diff --cached --name-only`
   - 与 slice packet `target_paths` 对比
   - 与 slice packet `dirty_state.unrelated` 对比
4. scope invalid 时不启动 implement / check worker，不进入 `REPAIRABLE_IMPLEMENT_ROUTES`；supervisor 直接 exit 2，并写入 `review-records/implementation-reviews.jsonl`：

```text
review_result=blocked
route_class=none
supervisor_failure=SCOPE_INVALID
repairable=false
```

这类问题需要人工隔离 worktree 或重选 target 后重跑，不能让 implement worker 空转修复。
scope preflight 只负责实现前 dirty 隔离，并且只在进入修复循环前执行一次。dirty 文件若属于 `target_paths`，视为本 slice 范围内；若属于 `dirty_state.unrelated`，允许保留但记录为 `isolated`；两者都不属于，才是 `SCOPE_INVALID`。循环内每轮 implement 后 diff 是否越出 packet `target_paths` 由 check worker 输出的 `dirty_scope=clean|isolated|invalid` 承担。两段都通过时，才能认为 review target 可审计。

5. brief 明确 “Do not run OCR by default. OCR is optional and bounded.”
6. check worker 必须审 invariant matrix；没有 matrix 时输出 `DETAIL_DEFECT` 或 `PROCESS_DEFECT`，不能 clean。
7. `run_implement_check` 解析新增字段：缺 `review_target` / `review_provider` / `deterministic_checks` / `dirty_scope` / `invariant_coverage` 时，不接受 clean，并按 `MALFORMED_REVIEW_OUTPUT` 硬停；任一 `deterministic_checks` / `dirty_scope` / `invariant_coverage` 取非通过值却声明 `clean` 或 `final-verification-ready` 时，也按 `MALFORMED_REVIEW_OUTPUT` 硬停。取值级判定调用 §4.4 所述 `guru_review_record.py` 共享校验函数，`final-verification-ready` 先归一为 `clean`。
8. 将现有 `guru_gate.py` 的 `_risk_level()` 语义抽成共享 helper `guru-template/overlay/verify/guru_risk.py`；`guru_gate.py` 的 `_risk_level()` 只做兼容代理，`guru_supervise.py` 必须 import 同一个 helper，禁止复制一份风险读取逻辑。判定优先级为 `slice_packet.risk` > task.json `risk_level|guru_risk_level|guru_risk|risk` > unknown；若 `slice_packet.risk=high` 且 `task.json risk_level=low`，以 packet 为准，不允许 task 级 low 覆盖 slice 级 high。
9. high-risk 判定：

```text
high if risk in high|critical
high if risk_reasons contains protocol_migration|cross_layer|stateful_cache_merge|payment|ads|permission|privacy|db_migration
unknown defaults to not forced for packet/invariant gating
low-risk override is slice_packet.risk=low, or task.json risk_level=low only when packet does not declare risk
if risk is unknown, supervisor treats it as high only when one of these deterministic signals is true:
- task.json notes / task metadata contains any risk keyword: protocol_migration, cross_layer, stateful_cache_merge, db_migration, payment, ads, permission, privacy
- pre-implementation planned paths from implement.md `target_paths` 文件范围摘要 / `slice_packet`, staged-or-dirty paths from `git diff --name-only` + `git diff --cached --name-only`, or post-implementation check diff paths contain stateful storage keywords: datasource, data_source, dao, database, db, cache, storage, local_data_source
- those same planned/staged/dirty/check paths span at least two layer groups: api/client, dto/model, repository, datasource/dao/db/cache, domain/usecase, controller/state, ui/widget/route
```

### 4.6 修改 Flutter implementation skills

优先级 P0：

1. `flutter-implementation-guru-writing` 增加硬步骤：无论风险级别，writing skill 都按 trace-contract §1 在 `implement.md` 计划节为每个 slice 写同一个 UNIT 与 `target_paths` 文件范围摘要，作为 unknown-risk 实现前上抬的可读信号源。high-risk slice 额外要求校验 `<task_dir>/slice-packets/<unit_id>.json` 已存在，并在 `implement.md` 计划节写 `slice_packet` 路径、`invariant_ids` 和 `negative_case` 摘要；若 packet 缺失，停止并回到 planning / implementation-writing 补 packet，不在实现 worker 内临时补造语义合同。packet 存在时以 packet `target_paths` 和 `invariants[]` 为机器 SSOT。实现完成后只允许补充 deterministic check evidence、测试名、命令和证据文件，不改变 invariant 语义字段。
2. `flutter-implementation-guru-review` 装载顺序增加 slice packet / invariant matrix。
3. D1 合同一致性从“diff 与详细设计单元逐一对照”扩展为“diff 与 invariant matrix 逐条对照”。
4. D4 证据核查要求每条 high-risk invariant 至少一个正向或负向测试；高风险负向语义缺失按 P1/P2。
5. 边界约束增加：不得要求 OCR 作为默认完成条件。
6. `flutter-implementation-guru-review` 的输出节必须与 §4.4 同步：clean / final-verification-ready 分支除 `review_result`、`route_class`、`validation_summary` 外，必须置顶输出 `review_target`、`review_provider`、`deterministic_checks`、`dirty_scope`、`invariant_coverage`；缺任一字段的 clean 都会被 supervisor 判为 `MALFORMED_REVIEW_OUTPUT`。
7. manual provider 的审查留痕不通过 `channel spawn`。P0 新增验证型追加命令：

```bash
python3 .trellis/scripts/guru/guru_review_record.py append \
  --task-dir .trellis/tasks/<task> \
  --packet .trellis/tasks/<task>/slice-packets/<unit_id>.json \
  --provider manual \
  --reviewer <name-or-id> \
  --run-id <run_id> \
  --result clean \
  --route-class none \
  --review-target slice:<unit_id> \
  --deterministic-checks passed \
  --dirty-scope isolated \
  --invariant-coverage all_passed \
  --evidence-file .trellis/tasks/<task>/review-records/manual-review-<run_id>.md
```

该命令复用 packet schema 校验与 review record schema 校验后追加 `implementation-reviews.jsonl`；`--run-id` 必须与 `--evidence-file` 文件名中的 `<run_id>` 一致。manual 行的 `channel` / `worker` 由 append 命令派生为 `manual` / `<reviewer>`，不需要额外参数。在该命令落地前，manual provider 不能满足 high-risk slice 的 `semantic_review_provider.required=true`；只能作为补充说明。`ocr_optional` 也只在显式触发时写同一记录，记录为 `channel=ocr_optional`，且默认不满足 required provider，除非 packet 明确选择它。

### 4.7 修改 `implementation-trace-contract`

优先级 P1：

1. 计划节对所有 slice 增加同一个 UNIT 与 `target_paths` 文件范围摘要；high-risk slice 额外必填 `slice_packet` 路径、`invariant_ids` 和 `negative_case` 摘要。机器可读内容以 packet 为准；第一版用既有 `UNIT-<slug>` 同时作为 trace unit、packet 文件名和 `--slice` 参数。
2. 证据节要求测试按 invariant 归档，不只按文件或命令归档。
3. 阻塞与偏差节要求：发现 invariant 缺失时回退 detail，不允许就地补造实现语义。

### 4.8 修改 workflow

优先级 P1：

1. Phase 2 明确 implementation semantic review provider 可替换。
2. OCR 降级为 optional provider，只有用户要求或高风险抽检时使用。
3. `No comments generated` 不作为退出目标。
4. 完成条件改为：deterministic checks passed + invariant coverage all passed + dirty scope clean/isolated + no blocker/should-fix.

## 5. 风险矩阵

| 风险 | 严重度 | 当前缺口 | 修复动作 | 验证 |
| --- | --- | --- | --- | --- |
| 大 diff 让 reviewer 漏掉二阶边界 | P0 | current diff 宽泛输入 | scope preflight + slice packet | dirty mixed diff 时记录 supervisor_failure=SCOPE_INVALID |
| 设计没有负向不变量 | P0 | trace 只写正向保留 facts | invariant matrix + negative case | 缺 matrix 时 check 返回 DETAIL_DEFECT |
| OCR 变成默认实现循环 | P0 | policy 未进 Guru runtime | provider 抽象 + OCR optional | brief / skill 禁止默认 OCR |
| implementation clean 不可审计 | P1 | 无结构化 record | review result schema | review-rounds 可回放 target/provider/checks |
| unrelated dirty files 干扰审查 | P1 | 只在事后提醒 | dirty scope gate | staged unrelated file 被标为 isolated/invalid |
| 对抗 review 缺失在实现阶段 | P1 | adversarial 只覆盖 planning | high-risk slice 要非实现者 provider | Claude/manual/Codex 任一 provider 记录 |
| packet / matrix 漂移 | P1 | 允许多处维护 | packet 为唯一机器 SSOT，implement.md 只摘要 | gate / skill 只读取同一 packet |
| manual provider 无法审计 | P1 | 不走 channel spawn | implementation-reviews.jsonl 统一记录 | manual / claude / codex 记录字段一致 |

## 6. 实施计划

### Phase A：文档合同修复

手工改动文件：

- `guru-template/workflows/guru-client-workflow.md`
- `guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md`
- `guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md`
- `guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md`

生成物：

- `packages/cli/src/templates/guru/**` 只由 `pnpm -C packages/cli sync:guru` 从 `guru-template/` 单向生成，不手工编辑。

验收：

- 文档不再表达 OCR 硬依赖。
- high-risk slice 明确需要 invariant matrix。
- 首次 supervised Flutter implement-check 前，high-risk slice 的 `slice-packets/<unit_id>.json` 已存在并与 `implement.md` UNIT 对齐。
- supervised Flutter check 的 clean 输出包含 `review_target`、`review_provider`、`deterministic_checks`、`dirty_scope`、`invariant_coverage` 全部 gating 字段。
- semantic review provider 模型写清楚。
- 运行 `pnpm -C packages/cli sync:guru` 后，`guru-template/` 与 `packages/cli/src/templates/guru/` 对应文件一致。

### Phase B：runtime preflight

手工改动文件：

- `guru-template/overlay/verify/guru_supervise.py`
- `guru-template/overlay/verify/guru_gate.py`
- `guru-template/overlay/verify/guru_risk.py`
- `guru-template/overlay/verify/guru_review_record.py`
- `guru-template/overlay/verify/tests/run_tests.sh`
- `guru-template/overlay/apply.sh`

生成物：

- `packages/cli/src/templates/guru/overlay/verify/**` 只由 `pnpm -C packages/cli sync:guru` 生成。sync 脚本会删除并重建 `src/templates/guru/specs`、`workflows`、`overlay`，因此 CLI 镜像路径不是手工 patch 目标。

验收：

- 无 slice packet / invariant matrix 的 high-risk check 不可 clean。
- dirty scope invalid 时记录 `supervisor_failure=SCOPE_INVALID`。
- dirty scope invalid 不进入 implement repair loop，而是 supervisor exit 2。
- `review-records/implementation-reviews.jsonl` 记录每轮 target / provider / checks / invariant coverage。
- default brief 不触发 OCR。
- `guru_gate.py` 与 `guru_supervise.py` 通过同一个 `guru_risk.py` 读取风险级别。
- `guru_gate.py` 的 `_risk_level()` 改为 `guru_risk.py` 的兼容代理，不再保留第二套风险判定逻辑。
- supervisor 与 manual provider 都通过 `guru_review_record.py` 共享 writer / schema 校验追加 `implementation-reviews.jsonl`；manual provider 只能通过 `guru_review_record.py append` 这样的 validated append path 满足 required provider。
- `apply.sh` 把 `guru_risk.py` / `guru_review_record.py` 与 `guru_gate.py` / `guru_supervise.py` 一起部署到目标项目的 `.trellis/scripts/guru/`。
- `apply.sh` 的脚本拷贝清单和语法自检清单都扩列 `guru_risk.py` / `guru_review_record.py`，不能只扩列其中一处。
- `apply.sh` 在 `ast.parse` 语法自检之外增加不写字节码的 import 冒烟测试，例如在 `.trellis/scripts/guru/` 下执行 `python3 -B -c "import guru_risk, guru_review_record"`，捕获兄弟模块漏拷导致的 runtime ImportError。

### Phase C：验证与回归

命令：

```bash
bash guru-template/overlay/verify/tests/run_tests.sh
python3 -m py_compile \
  guru-template/overlay/verify/guru_gate.py \
  guru-template/overlay/verify/guru_supervise.py \
  guru-template/overlay/verify/guru_risk.py \
  guru-template/overlay/verify/guru_review_record.py
PYTHONPATH=guru-template/overlay/verify python3 - <<'PY'
import guru_risk
import guru_review_record
PY
# after applying the overlay into a temp target repo
(cd <target>/.trellis/scripts/guru && python3 -B -c "import guru_risk, guru_review_record, guru_supervise")
pnpm -C packages/cli sync:guru
git diff --check
```

验收：

- 既有 Gate 测试通过。
- 新增 scope / invariant / provider 相关回归测试通过。
- `guru_risk.py` / `guru_review_record.py` 在模板同目录导入成功；安装后 runtime 路径 `.trellis/scripts/guru/...` 下也能用 `python3 -B` 导入 `guru_risk` / `guru_review_record` / `guru_supervise` 成功。
- 模板与 CLI 镜像 diff 一致。
- `pnpm -C packages/cli sync:guru` 后没有未同步漂移。

## 7. 成功标准

1. 对 Himora V2 local merge 这类问题，若 detail 已写 invariant，implementation check 必须能定位到具体 `IMPLEMENT_DEFECT`。
2. 若 detail 未写 invariant，implementation check 必须输出 `DETAIL_DEFECT`，不能靠代码实现私自拍板。
3. 无 OCR 的情况下，Claude / Codex / manual review provider 能完成语义审查闭环。
4. OCR 可继续存在，但只作为 optional bounded provider。
5. dirty worktree 下 review target 必须可审计，不能把 unrelated lockfile / generated churn 混进 clean 结论。
6. scope-invalid 不会触发 3 次 implement repair 空转。
7. packet 是 invariant matrix 的唯一机器 SSOT；不会出现 implement.md 与设计包矩阵漂移。
8. `packages/cli/src/templates/guru/**` 的变更来自 sync 命令，不来自手工 patch；sync 后可审查生成镜像 diff，避免源模板与 CLI 内置模板漂移。

## 8. 非目标

- 本方案不直接修改 Himora 产品代码。
- 本方案不删除 OCR 工具，也不禁止用户显式要求 OCR。
- 本方案不要求所有小改都走 invariant matrix；仅 high-risk / cross-layer / stateful / protocol migration slice 强制。
- 本方案 P0 只治理 Flutter implementation review；go / ios / h5 平台必须另行补齐对应 writing/review skill 后再开启同等 packet preflight。
- 本方案不替代人工确认 Gate；它只增强实现期 semantic review 的输入和证据质量。

## 9. 当前待审问题

本方案需要 Claude 重点审查：

1. 是否仍隐含 OCR 硬依赖。
2. scope preflight / invariant matrix / provider abstraction 是否足以解释 Guru review 漏检根因。
3. 是否存在无法落地、过度复杂或与现有 Guru workflow 冲突的部分。
4. 是否遗漏了实现期 review 的关键风险。
