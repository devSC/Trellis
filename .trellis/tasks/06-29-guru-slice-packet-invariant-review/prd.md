# PRD — Guru slice packet + invariant matrix + 结构化 review record (P1)

## 背景与根因(SSOT:`../06-28-guru-review-governance-report/problem-report-and-solution.md`)

Himora V2 grouped-media 迁移中 guru review 没在早期挡住跨层语义缺陷。根因(报告 §3):guru review 缺
(a) 实现期可**逐条判定的 invariant matrix**(§2.5 负向不变量缺失);(b) **slice scope gate**(实现范围/dirty diff 无机器隔离);(c) **结构化 review record**(§3.4 verdict 是自由文本、route 靠全文搜索)。

**P0(已交付,task `06-29-guru-impl-review-hardening`)** 用**无 packet 的轻量版**达成 OCR 等效拦截:逐行数据语义密度(D7)、SSOT 接地 + `collect_gate_artifacts` fail-closed、独立对立-provider 阻断 check(`guru_risk` task.json risk + git scan 跨层信号触发)。P0 有意避开 packet,故"逐条可判定矩阵 / slice scope gate / 结构化 record"仍缺。

**本任务**落地报告 §4 的 **packet-centric 完整机制**,作为 ④⑤ 的基座。flutter-only(§4.5.1)。

## 范围

§4.2 slice packet + §4.3 invariant matrix + §4.4 结构化 verdict/record + §4.5 packet/scope preflight +
§4.6 flutter skill 集成 + §4.7 trace-contract + §4.8 workflow。**复用 P0 已落地的 `guru_risk.py`(§4.5.8 已做)与跨层/storage 判定(§4.5.9 大部分已做)**,本任务只补 `slice_packet.risk > task` 的优先级与 `risk_reasons` 关键词。

**非目标**:packet 自动生成——第一版由**主会话 / planning 阶段**在首次 `implement-check` 前**手工创建** packet;`flutter-implementation-guru-writing` **只读取/校验/在 implement.md 摘要,绝不创建、绝不在实现 worker 内补造**(§4.2/§4.6.1,防 invariant 按实现倒推);go/ios/h5(§4.5.1);替换 P0 的 task-level 轻量触发(P0 与 packet 并存,packet 优先)。

## 行为契约(BHV)

### BHV-001 high-risk flutter slice 须有 packet 才能 implement-check
Given flutter high-risk slice,When `guru_supervise implement-check` 找不到对应 `<task_dir>/slice-packets/<unit_id>.json`,Then 硬停 exit 2(packet 缺失是 **planning/主会话** 合同缺失[writing 仅校验、不创建],**不启动 implement worker 现场补造**;多 packet 未 `--slice` 指定也硬停,单 packet 可自动选)。

### BHV-002 scope preflight 隔离 dirty diff
Given 进入 implement-check 修复循环前,When `guru_risk.scan_dirty_paths`(唯一 dirty 来源:`git status --porcelain=v1 -z -uall`,**不另用 `git diff`**)的路径既不属于 packet `target_paths` 也不属于 `dirty_state.unrelated`,Then `SCOPE_INVALID` exit 2 + 写 `review-records/implementation-reviews.jsonl`,不启动 worker(属 target_paths→范围内;属 unrelated→记 `isolated`)。

### BHV-003 结构化 verdict 取值级 gating
Given check worker 置顶输出 7 字段(`review_result/route_class/review_target/review_provider/deterministic_checks/dirty_scope/invariant_coverage`),When 声明 `clean`(或 `final-verification-ready` 归一为 clean)但缺任一字段、或 `deterministic_checks≠passed` / `dirty_scope∉{clean,isolated}` / `invariant_coverage≠all_passed`、或 **`review_provider` 不满足 packet `semantic_review_provider`**(第一版 required 只 `{codex,claude,opposite}`,default 须实现者对立;**`manual`/`ocr_optional` 不作 required**——packet 声明它们作 required→`PACKET_INVALID`,仅作补充审计记录、worker 自报不可 clean,§4.6.7/R5-F1),Then `MALFORMED_REVIEW_OUTPUT` exit 2(不接受为成功,不让 implement worker 空转修复审查格式)。

### BHV-004 invariant matrix 逐条判定
Given high-risk slice review,When check worker 审查,Then 对 packet `invariants[]` 逐条给机器可解析 `invariant_status.<id>=pass/fail/not_applicable`(+ `invariant_evidence.<id>`[pass 必填非空] / `invariant_reason.<id>`[N/A 必填非空],R9-F2),supervisor 用 `aggregate_invariant_coverage` **重算**(§4.3:任一 fail→failed;pass 缺 evidence 或缺 status→missing;否则 all_passed;未知 id→MALFORMED);**packet `invariants[]` 须非空**(空→`PACKET_INVALID`,R9-F1);**无 matrix → `DETAIL_DEFECT`/`PROCESS_DEFECT`,不能 clean**。

### BHV-005 结构化 review record 单一 writer
Given 任何 provider(supervisor parse-time / manual / ocr_optional)写 review record,When append,Then 经 `guru_review_record.py` **单一共享 schema 校验 + writer** 写 `implementation-reviews.jsonl`(取值级一致性拒绝也在该共享函数:任何 clean 型裁决须同时满足三通过值,否则 `MALFORMED_REVIEW_OUTPUT`);严禁一个 jsonl 两套 writer。

### BHV-006 无 OCR 必选(硬约束,贯穿)
Given 任何完成路径,When 判定 clean,Then **绝不依赖 OCR**;OCR 仅 optional provider(只在用户要求/高风险抽检显式触发,记 `channel=ocr_optional`),默认不满足 `required` provider。

### BHV-007 slice_packet.risk 优先于 task 级(risk 字段可选)
Given packet 声明 `risk=high`(或 risk_reasons 命中关键词)而 task.json `risk_level=low`,When 风险判定,Then 以 packet 为准(§4.5.8;P0 的 task 级 low 不得覆盖 slice 级 high)。**同理 packet `risk=low` 是 slice 级 override(R8-F1,SSOT §4.5.9 `low-risk override is slice_packet.risk=low`):直接判 low,不被 task high/unknown 或 git scan 抬高。** **`risk` 是 packet 可选字段**:缺失或 unknown 时回落 P0 的 task.json+git scan 判定,**不得因缺 risk 把 packet 判非法**(否则违反"未声明回落 P0")。

### BHV-008 supervisor 独立执行 deterministic_checks(hard Gate,R3-F1)
Given high-risk packet slice 的 check,When 判定 clean,Then supervisor 须在 repo root **独立执行** packet `deterministic_checks[]`(逐条 command/exit/timeout 记录),clean 须 **supervisor 执行 passed ∧ worker 自报 `deterministic_checks=passed`**;packet `deterministic_checks` 空/缺 → `deterministic_checks=missing` 不可 clean;命令失败/timeout → `deterministic_checks=failed`。**本 task 即 problem-report 的 P1,§4.1/§4.4 明确 supervisor-side hard Gate 是 P1 落地目标,不再 defer。**

## 分期(详见 design.md / implement.md)

- **P1a reader/writer 基座**:`guru_review_record` packet schema(两层)+ `load_packet`/`append_record`/`preflight_failure_record` + `guru_risk` 接 `slice_packet_risk`/`scan_dirty_paths`(§4.5.8/4.5.9)。
- **P1b packet 上下文 + preflight**:`--slice` + packet resolve/auto-select/ambiguous + `implement_check_independent_required(unit_id=)` + packet preflight + scope preflight(§4.5.2-4.5.6;PACKET_*/SCOPE_INVALID 硬停、不进 repairable)。
- **P1c verdict gating**:`validate_verdict_values`/`normalize_review_record`(含 provider gating)+ `run_implement_check` 解析 7 字段取代全文搜索(§4.4/4.5.7,**用 P1b 建立的 packet 上下文分流**)。
- **P1d skill+④**:§4.6 writing **仅校验/摘要(不创建)** packet、review 装载 packet/matrix、D1 对照 matrix、D4 negative test、verdict 输出 7 字段;④ detail/requirement skill 负向/排除维度对齐 invariant matrix。
- **P1e trace+workflow**:§4.7 trace-contract(UNIT/target_paths/slice_packet)+ §4.8 workflow 完成条件。
- **收口**:apply.sh 收编 `guru_review_record.py`(同 guru_risk 模式)+ `sync:guru` + `sync:guru:check` 无漂移 + codex 对抗审查至 0B+0SF。

## 验收标准

- [ ] `run_tests.sh` 新增覆盖 BHV-001..008(packet 缺失硬停、scope invalid、verdict 取值级 gating、invariant 逐条+聚合、共享 writer 一致性拒绝、packet.risk override、provider gating、**supervisor deterministic 执行/缺失/失败/worker 谎报**、无 OCR 必选)
- [ ] 装配自检(ast/import 冒烟含 `guru_review_record.py`)+ `sync:guru:check` 无漂移
- [ ] **全程无 OCR 必选依赖**(codex 复核确认)
- [ ] codex opposite-provider 对抗审查至 `blockers=0 且 should_fix=0`(规程 `adversarial-review.md`,沿用 P0)

## 失败路径 / 未决问题

- **packet 生产者**:第一版**主会话/planning 阶段**在 implement-check 前手工创建;writing-skill 仅校验/摘要、不创建。自动生成 packet 属后续(非本任务)。
- **deterministic_checks supervisor-side hard Gate**:**已纳入本 P1**(BHV-008,§4.1/§4.4 的 P1 落地目标);supervisor 在 repo root 独立执行 + worker 自报,双过才 clean(不再 defer)。
- **packet ↔ trace join key**:第一版用既有 `UNIT-<slug>` 同时作 trace unit / packet 文件名 / `--slice` 参数(§4.2/4.7)。
- **manual/ocr_optional 作 required provider 的验证路径**(R5-F1):第一版禁止(`required=true ∧ provider∈{manual,ocr_optional}`→`PACKET_INVALID`),manual/ocr 仅作补充记录;完整 verify-record 路径(supervisor 读 append 行判 clean)deferred 后续(design §6)。这也强化 BHV-006:OCR 绝不作 required。

## Brainstorm Evidence

- Skill loaded: problem-report-and-solution.md §4(packet-centric 方案 SSOT)+ P0 archived implement.md
- Repository evidence: Explore 收集 P0/skill 集成点现状(见 design.md);P0 已落地 guru_risk(§4.5.8)+ 跨层判定(§4.5.9 部分)
- Domain triggers: slice packet / invariant matrix / structured verdict / scope preflight / review record
- Current code vs intent: P0 无 packet 轻量版已达 OCR 等效;P1 补 packet-centric 完整机制(并存,packet 优先)
- Product decisions confirmed: 用户 2026-06-29 选"建 task 进 planning",整体 P1 packet 机制 + ④⑤,flutter-only
- Open questions: packet 自动生成(deferred)。**deterministic supervisor-side hard Gate 已纳入本 P1(BHV-008,§4.1/§4.4),不再 deferred。**
