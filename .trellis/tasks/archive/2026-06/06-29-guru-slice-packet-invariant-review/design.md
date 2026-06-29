# Design — Guru slice packet + invariant matrix + 结构化 review record (P1)

SSOT:`../06-28-guru-review-governance-report/problem-report-and-solution.md` §4(packet 机制完整方案);本文聚焦**落地设计、模块边界、集成点(file:line)、分期、P0 复用**,不复述 §4 全文。

## 1. 架构总览

```
slice-packets/<unit_id>.json   ← planning / 主会话 手工创建（writing-skill 不创建；数据 SSOT：target_paths + invariants[] + risk? + deterministic_checks + dirty_state）
        │
        ├─ guru_risk.py        ← slice_packet.risk > task.json risk（§4.5.8）+ risk_reasons 关键词（§4.5.9）
        │
        ▼
guru_supervise.py implement-check
   1. packet resolve + preflight（缺失/多义 → 硬停 exit2，BHV-001）
   2. scope preflight（guru_risk.scan_dirty_paths[-z -uall] vs target_paths/dirty_state.unrelated → SCOPE_INVALID exit2，BHV-002）
   3. 每轮: implement(brief 注入 packet,R4-F2) → supervisor run_deterministic_checks(本轮 diff,R4-F1) → check(注入同一 packet) → 解析 7 字段 verdict(取代 _route_from_output)
   4. 取值级 gating（clean 须三通过 + provider gating + deterministic 双过 + 聚合重算，否则 MALFORMED exit2，BHV-003/008）
        │
        ▼
guru_review_record.py          ← 单一共享 schema 校验 + writer（BHV-005）；supervisor parse-time / manual / ocr append 全调它
        │
        ▼
review-records/implementation-reviews.jsonl   ← 任务内可审计索引
```

skill 侧:`flutter-implementation-guru-writing` **读取/校验/摘要 packet,不创建**(§4.6.1;可补 deterministic check 计划/证据,但不创建或改写 invariant 语义字段);`flutter-implementation-guru-review` 装载 packet/matrix + D1 对照 invariant matrix + D4 negative test + 置顶输出 7 字段(§4.6.2-6)。

## 2. 模块设计

### 2.1 `guru_review_record.py`(**新建**,核心)
single source of truth for review record schema + writer。**不 import guru_gate/guru_supervise**(防循环,同 guru_risk)。

- **枚举**:`REVIEW_RESULT={clean,findings,blocked}`(`final-verification-ready`→`clean` 归一);`ROUTE_CLASS={none,IMPLEMENT_DEFECT,PROCESS_DEFECT,DETAIL_DEFECT,OVERVIEW_DEFECT,REQ_BLOCKER}`;gating 三元 `deterministic_checks∈{passed,failed,missing}`/`dirty_scope∈{clean,isolated,invalid}`/`invariant_coverage∈{all_passed,failed,missing}`;`supervisor_failure∈{none,SCOPE_INVALID,MALFORMED_REVIEW_OUTPUT,PACKET_MISSING,PACKET_INVALID,PACKET_AMBIGUOUS}`(F6:preflight 专用码)。
- **packet schema(§4.2,两层,F3 解决 risk 必填 vs 回落冲突)**:
  - 必填(**且非空,R9-F1**):`schema_version=1`、`slice_id`、`owner_unit`、`target_kind`、**`target_paths[]`(非空字符串数组)**、**`invariants[]`(非空对象数组)**(每条必填 `invariant_id/rule/source/owner/positive_case/negative_case/route_if_missing`,`test_evidence[]` 可空)。**空数组 / 空 path 字符串 / 非对象 invariant → `ReviewRecordError`(supervisor 记 `PACKET_INVALID`)**;否则 high-risk packet 用 `invariants:[]` 可绕过"无 matrix 不能 clean"、`target_paths:[]` 让 scope gate 失去边界(fail-open)。
  - 可选 + fail-closed 默认:`risk`(R3-F3 口径:可缺省;`high|critical|low`→参与 slice risk 且优先于 task;**`unknown`/null/空字符串→规范化 `None` 回落 P0**;**其他字符串(如 `medium`)→`PACKET_INVALID`**,BHV-007)、`risk_reasons[]`、`deterministic_checks[]`(缺→`missing`,不可 clean,BHV-008)、`dirty_state.unrelated[]`(缺→空集:scope preflight 要求所有 dirty 须属 `target_paths`)。
  - **`semantic_review_provider` schema(R3-F4/R5-F1,present 时合法结构 + 判定表)**:字段 `required:bool`、`provider∈{codex,claude,opposite}`、`ocr∈{optional,disabled}`;**缺→`{required:true,provider:opposite,ocr:optional}`**;判定:`provider=opposite`→clean 须实现者对立 channel-spawn provider;`provider=codex|claude`→clean 须该 channel-spawn provider;`required=false`→clean **仍须 opposite**(不降格)。**R5-F1(保守,控制第一版范围):required provider 只支持 channel-spawnable `{codex,claude,opposite}`;`required=true ∧ provider∈{manual,ocr_optional}` → `PACKET_INVALID`**(第一版无 supervisor 读 append 记录判 clean 的消费路径,避免死路/旁路;manual/ocr_optional 仅作**补充记录**经 append CLI 写、**不满足 required**;完整 required-provider 验证路径[`--verify-review-record`/pending-resume]deferred 后续,见 §6 未决)。非法结构 → `ReviewRecordError`。
  - `load_packet(task_dir,unit_id)`/`list_packets(task_dir)`:非法(缺必填 / 未知 schema_version / 非 JSON)→ `ReviewRecordError`;**缺 `risk` 不算非法**。
- **verdict + record 单一流程(F2,解决"append 拒绝 vs §4.4 必须写 jsonl"矛盾)**:
  - `validate_verdict_values(fields) -> failure_code|None`(R8 命名统一:取值校验层①,所有 provider 共用):归一后 7 字段存在性 + 枚举 + 三通过值一致性(clean 须 `deterministic_checks=passed ∧ dirty_scope∈{clean,isolated} ∧ invariant_coverage=all_passed`);缺任一 7 字段或取值非法 → `MALFORMED_REVIEW_OUTPUT`。
  - `normalize_review_record(fields, context) -> (record, failure_code)`:**唯一规范化入口**,**两层判定(R7-F2,拆清 supplemental append 语义)**:
    - ① `validate_verdict_values(fields)`(**所有 provider 共用**):7 字段存在性 + 枚举 + 三通过值一致性;不过 → canonical blocked(`MALFORMED_REVIEW_OUTPUT`)。
    - ② **required-provider gating** 只在 **supervisor 消费 channel-spawned check verdict 作 required clean** 时执行(R2-F2/R5-F1,§4.6.7):第一版 `provider` 只 `{codex,claude,opposite}`,required satisfaction 只由 channel-spawned `codex/claude/opposite-resolved` 满足(default 须实现者对立、同 provider 不可 clean)。
    - **manual/ocr_optional append 走 supplemental 路径**:`context.mode=supplemental` 时**只过 ①、不执行 ② required satisfaction**;record 标 `required_satisfied=false`+`supplemental=true`、`channel=manual|ocr_optional`,**保留为补充审计记录**(即便 `--result clean`,记的是补充审计裁决,**不被 supervisor 消费为 required clean、也不打成 malformed**)。`manual`/`ocr_optional` 作 packet `required` provider 仍在 `load_packet` 判 `PACKET_INVALID`(不可作完成闸)。
    - 合格则原样成 record;clean 缺字段/取值不通过同样转 canonical。
  - `append_record(task_dir, record)`:**唯一 writer**,写 `review-records/implementation-reviews.jsonl`(字段全集:run_id/slice_id/**review_target**/target_paths/review_provider/route_class/review_result/三 gating/**`deterministic_results[]`(R5-F2:逐条 `command/cwd/exit_code/timed_out/stdout_summary/duration_ms/run_at`,供审计回放)**/channel/worker/timestamp/supervisor_failure/repairable/**可选 `message`+`candidates[]`(R5-F3:PACKET_AMBIGUOUS 候选)+ `supplemental`+`required_satisfied`(R7-F2:manual/ocr 补充审计行标记)**——R3-F2:`review_target` 入 jsonl 全集;manual→channel=manual/worker=<reviewer>,ocr_optional→channel=ocr_optional/worker=<tool>)。**调用方永远 `normalize_review_record → append_record`,绝不拒绝后自己手写 jsonl**(BHV-005;malformed/scope/packet failure 都经此入 jsonl,满足 §4.4"malformed clean 也写")。
  - `preflight_failure_record(kind, run_id, unit_id=None, candidates=None) -> record`(R2-F1+F6):supervisor-only 硬停 canonical record——`review_result=blocked, route_class=none`(**SSOT §4.5.4:scope/packet failure 是 `supervisor_failure`,不是 worker `route_class`;绝不用 PROCESS_DEFECT——它在 `REPAIRABLE_IMPLEMENT_ROUTES` 里会被误进 repair loop**), `supervisor_failure=PACKET_MISSING|PACKET_INVALID|PACKET_AMBIGUOUS|SCOPE_INVALID, repairable=false`。**字段策略(F6,解决无 packet 时 slice_id/target_paths 缺失)**:有 `--slice`→`slice_id=unit_id, target_paths=[], review_target=slice:<unit_id>`;无 `--slice` 且零 packet→`slice_id=null, target_paths=[], review_target=slice:unknown`;多 packet(PACKET_AMBIGUOUS)→候选 packet 列入 `message`。只由本函数生成、经 append_record 写。
  - `append` CLI(§4.6.7):manual/ocr 追加;校验 `--run-id` 与 evidence-file 名一致;内部走 `normalize_review_record → append_record`(写时 gating)。
  - `aggregate_invariant_coverage(packet_invariants, reviewer_statuses) -> all_passed|failed|missing`(R3-F5/R9-F2,**唯一聚合函数**)。**per-invariant 机器合同(R9-F2,可解析字段)**:`invariant_status.<id>=pass|fail|not_applicable` + `invariant_evidence.<id>=<非空证据摘要/引用>` + `invariant_reason.<id>=<not_applicable 必填>`。**规则**:`pass` 须非空 `invariant_evidence`;`not_applicable` 须非空 `invariant_reason`;**未知 invariant id→`MALFORMED`**;**缺 status / `pass` 缺 evidence→`missing`**;任一 `fail`→`failed`;否则 `all_passed`。`parse_verdict_block` 与本函数用同一字段合同(packet `invariants[]` 仍是机器 SSOT)。worker 可自报 aggregate,但 supervisor/append **从 statuses 重算校验**,不只信 worker 字符串。
  - `run_deterministic_checks(commands, repo_root) -> (status, results)`(R3-F1/R5-F2,BHV-008):supervisor-side 执行——在 repo root 逐条跑 packet `deterministic_checks[]`(subprocess + timeout);全 exit0→`passed`;任一失败/timeout→`failed`;空/缺→`missing`。**`results` 逐条含 `command/cwd/exit_code/timed_out/stdout_summary/duration_ms/run_at`,经 normalize→append_record 写入 record `deterministic_results[]`(R5-F2 审计回放)**。clean 须本函数 `passed` ∧ worker 自报 `deterministic_checks=passed`(双过)。(用 subprocess,但仍不 import 兄弟模块。)
- **不 import guru_gate/guru_supervise**(防循环,同 guru_risk);schema_version=1 护栏拒未知版本。

### 2.2 `guru_risk.py`(**扩**,复用 P0)
- 新增 `slice_packet_risk(task_dir, unit_id)`:经 `guru_review_record.load_packet` 读 packet(单一 packet reader,不另解析 JSON);`risk∈{high,critical}` 或 `risk_reasons∩{protocol_migration,cross_layer,stateful_cache_merge,db_migration,payment,ads,permission,privacy}≠∅` → `"high"`;显式 `low`→`"low"`;无/unknown→`None`(§4.5.9)。
- 新增 `scan_dirty_paths(repo_root)`(F4):**唯一 dirty path 来源**——复用现有 `scan_paths` 的 `git status --porcelain=v1 -z -uall`(含 untracked/rename/delete,与 P0 同口径);scope preflight 调它,**不重新发明 `git diff` 弱扫描**(P0 已证 `git diff` 漏新建文件)。
- **R3-F3:先把当前 L160-183 原逻辑原样抽成私有 `_p0_implement_check_independent_required(task_dir, platform, repo_root)`**(避免递归/复制),公开 `implement_check_independent_required(task_dir, platform, repo_root, unit_id=None)` 三分支:`slice_packet_risk=="high"`→`(True,"slice-packet high-risk")`(BHV-007);**`slice_packet_risk=="low"`→`(False,"slice-packet low-risk")`(R8-F1:slice 级 low override,SSOT §4.5.9 `low-risk override is slice_packet.risk=low`;**不调 _p0_**、不被 task high/unknown 或 git scan 抬高)**;`None`/无 packet/无 risk/`unit_id=None`→调 `_p0_...`(回落 P0 task.json+git scan)。
- **不破坏 P0**:`unit_id=None` 经 `_p0_...` 与旧函数字节一致(P0 调用方零影响)。

### 2.3 `guru_supervise.py`(**改** run_implement_check,复用 P0 provider 隔离)
**执行序(R2-F1 packet 上下文先于 verdict;R4-F1 deterministic 每轮绑定本轮 diff;R4-F2 packet 注入 worker)**:① CLI `--slice <unit_id>`;② packet resolve(单/多/`PACKET_AMBIGUOUS`);③ packet preflight;④ scope preflight(**仅循环前一次**);⑤ 进修复循环;**⑥ 每轮:implement worker(brief 注入 resolved packet)→ supervisor `run_deterministic_checks`(针对本轮 repo 状态,R4-F1)→ check worker(注入同一 packet)→ verdict gating(clean 须**本轮** supervisor `passed` ∧ worker 自报 `passed`;repair 后下一轮重跑,不复用过期结果)**。
- **packet preflight**(BHV-001,F6):flutter high-risk(经 `guru_risk.implement_check_independent_required(...,unit_id=)`,packet.risk 优先)→ `load_packet`;缺失/非法/多义 → `preflight_failure_record(PACKET_MISSING|PACKET_INVALID|PACKET_AMBIGUOUS)` + `append_record` + **exit2,绝不进 `REPAIRABLE_IMPLEMENT_ROUTES`**(`repairable=false`,不启 implement worker 现场补造)。
- **scope preflight**(BHV-002,§4.5.3-6,F4):dirty path **复用 `guru_risk.scan_dirty_paths`(单一 `-z -uall` 来源,与 P0 同口径)** vs packet `target_paths`(范围内)/`dirty_state.unrelated`(记 isolated);越界 → `preflight_failure_record(SCOPE_INVALID)` + append + exit2,不启 worker。
- **packet 注入 worker**(R4-F2,补真实集成):`build_run_plan`/`RunPlan` 扩 `slice_context`——resolved packet path 加入 `artifact_candidates`/`--file`,implement/check brief 写 `active_slice=<unit_id>`/`slice_packet=<path>`/`review_target=slice:<unit_id>`/`target_paths` 摘要/`semantic_review_provider`;多 packet **只注入 resolved**(`PACKET_AMBIGUOUS` 不进 worker)。否则 worker 拿不到 packet、无法输出 `invariant_status.*`/正确 provider/review_target → 被误判 MALFORMED。dry-run 须显示注入的 packet 文件。
- **supervisor deterministic_checks**(R3-F1/R4-F1,BHV-008):**每轮 implement worker 成功后**(非循环前一次)针对当前 repo 状态跑 `run_deterministic_checks(packet.deterministic_checks, repo_root)`,结果注入**本轮** check context;空/缺→`missing`(不可 clean);repair 后下一轮重跑。**supervisor 执行是真 hard Gate,不只信 worker 自报、不复用过期结果**。
- **verdict 解析重构**(§4.5.7,F1):check worker 输出经 `parse_verdict_block` + `normalize_review_record`,**取代** `_route_from_output`(L65-68/L350-358);`context` 带 packet semantic_review_provider + implement/check provider + **supervisor deterministic 结果** + reviewer per-invariant statuses(supervisor 用 `aggregate_invariant_coverage` **重算**,R3-F5,不只信 worker `invariant_coverage` 字符串);分流用②建立的 packet 上下文——**有 packet high-risk slice 强制:7 字段 + provider gating + deterministic 双过 + 聚合重算校验**(任一不过→canonical + exit2),无 packet 流程保留旧 route 解析(过渡,见 §5)。
- **每轮写 jsonl**(F2):check 后总是 `normalize_review_record → append_record`(合格记 worker 裁决,malformed 记 canonical blocked record;**绝不拒绝后手写**)。
- **brief**:加 "Do not run OCR by default. OCR is optional and bounded."(§4.5.5)+ 要求 check worker 审 invariant matrix、置顶输出 7 字段。
- requirements 路径**不**强加 7 字段(§4.5.7 仅 implement-check)。

### 2.4 `guru_gate.py`(**可选**,P1 末或 defer)
`validate-slice-packet <task_dir> <unit_id>` 命令(§4.2 L157"第一版不依赖新增命令")——**defer 到 skill/supervise 用 guru_review_record.load_packet 校验**,gate 命令非必需。④ 的 trace matrix 负向列:`build_trace`/`render_matrix`(L811-898)可选扩负向维度,但 invariant matrix 的机器 SSOT 是 packet(§4.3),gate matrix 仅展示——**第一版只读 packet 渲染,不另存第二份矩阵**(§4.3 防漂移)。

### 2.5 Skill 改(§4.6/4.7,文档)
- `flutter-implementation-guru-writing/SKILL.md`:WX-1 加 UNIT/target_paths 计划节(所有 slice);high-risk 额外校验 packet 存在 + 写 slice_packet/invariant_ids/negative_case 摘要;缺失停回 planning(不补造)。
- `flutter-implementation-guru-review/SKILL.md`:装载顺序加 packet/matrix(**来自 supervise build_run_plan 注入,R4-F2**);D1 扩"diff vs invariant matrix 逐条";D4 每条 high-risk invariant ≥1 正/负测试;输出节加 5 个 gating 字段(review_target/review_provider/deterministic_checks/dirty_scope/invariant_coverage)+ per-invariant `invariant_status.*`。
- `implementation-trace-contract.md`:§1 计划节加 UNIT/target_paths;high-risk 加 slice_packet/invariant_ids/negative_case;§3 测试按 invariant 归档。
- `detail-structure-single-source.md` + `requirement-doc-standard`:④ 负向/排除维度——八问之 8"不得补造"升级为含 invariant(rule/owner/positive_case/negative_case/route_if_missing);加"不变量矩阵"章节模板,**对齐 packet schema 字段**(勿另起,[[guru-requirement-doc-standard-is-ssot]])。

### 2.6 `apply.sh`(**扩**,同 guru_risk 模式)
copy list(L223-231)+ ast.parse(L665-675)+ import 冒烟(L677-681)三处扩列 `guru_review_record.py`;import 冒烟改 `import guru_risk, guru_gate, guru_supervise, guru_review_record`。

## 3. 分期(对应 implement.md;每期独立 commit + sync + 本地验证)

| 期 | 内容 | 关键文件 | 验收 |
|----|------|---------|------|
| **P1a** | packet reader + record writer 基础(`load_packet`/`append_record`/`preflight_failure_record` schema)+ guru_risk(`slice_packet_risk`/`scan_dirty_paths`) | guru_review_record.py、guru_risk.py | packet 校验单测;packet.risk override(BHV-007);**缺 risk 不判非法**;scan_dirty 复用 -uall |
| **P1b** | **packet 上下文接线(F1:先于 verdict gating)**:`--slice` + packet resolve/auto-select/ambiguous + `implement_check_independent_required(unit_id=)` + packet preflight + scope preflight(用 P1a reader/writer/scan_dirty) | guru_supervise.py、guru_risk.py | BHV-001/002 dry-run + 硬停(PACKET_*/SCOPE_INVALID exit2,**不进 REPAIRABLE**) |
| **P1c** | verdict 结构化:`validate_verdict_values`/`normalize_review_record`(provider gating)+ `aggregate_invariant_coverage`(聚合重算)+ `run_deterministic_checks`(supervisor hard Gate,**每轮**)+ **packet 注入 build_run_plan(R4-F2)** + verdict gating(用 P1b packet 上下文分流) | guru_review_record.py、guru_supervise.py | BHV-003/005/008 单测;旧散文 route 不误命中;deterministic 每轮双过/缺/失败/worker 谎报;invariant 逐条+聚合;provider gating;packet `--file` 注入 + brief active_slice;非 packet 流程旧行为不变 |
| **P1d** | skill 集成(§4.6 writing **仅校验**/review)+ ④ detail/requirement 负向维度 | 4 个 SKILL/spec md | BHV-004;对 Himora INV-LOCAL-FACTS-ONLY 走查能 elicit |
| **P1e** | trace-contract(§4.7)+ workflow(§4.8)完成条件 | trace-contract.md、workflow | 完成条件 = det+invariant+scope+no blocker |
| **收口** | apply.sh 收编 + sync:guru(+:check 无漂移)+ codex 对抗 0B0SF | apply.sh、mirror | 装配自检含 guru_review_record;codex APPROVE |

## 4. 关键设计决策与不变量

- **单一 writer/校验函数**(BHV-005):取值级一致性拒绝只在 `guru_review_record.validate_verdict_values` 一处;supervisor 与 manual/ocr 都调它——绝不两侧各实现(§4.4 末明令)。
- **packet 是 invariant 唯一机器 SSOT**(§4.3):gate/skill/implement.md 只引用或摘要,不存第二份机器矩阵(防漂移)。
- **fail-closed 一致**(F6):packet 缺失/非法/多义、scope invalid、verdict malformed 全经 `preflight_failure_record`/`normalize_review_record` 生成 canonical `repairable=false` record + append_record + exit2,**绝不进 `REPAIRABLE_IMPLEMENT_ROUTES`(={IMPLEMENT_DEFECT,PROCESS_DEFECT})、不启/不空转 implement worker**。
- **无 OCR 必选**(BHV-006,硬约束):OCR 仅 optional provider;brief 显式 "Do not run OCR by default";完成条件不含 OCR。
- **P0 并存**:packet 优先,packet 未声明时回落 P0 的 task.json+git scan 触发(向后兼容,P0 调用方 `unit_id=None` 字节不变)。
- **防循环 import**:guru_review_record 不 import 兄弟模块(同 guru_risk);guru_supervise import guru_review_record + guru_risk + guru_gate。

## 5. 风险 / 回滚

- ②③(P1b/c)触 control flow(verdict 解析 + preflight 硬停),回滚优先级最高;每期独立 commit,失败 `git revert` + `sync:guru` 还原镜像。
- verdict 解析重构风险:旧 check worker(未输出 7 字段)在 P1c 后对**有 packet 的 high-risk slice**会被判 MALFORMED——需 P1d skill 同步输出 7 字段;**P1c 与 P1d 之间的过渡**:P1c gating 用 P1b 建立的 packet 上下文分流——仅"有 packet 的 high-risk slice"强制 7 字段,无 packet 流程保留旧 route 解析,避免打断存量非 packet 流程(精确边界见 implement.md)。
- codex 对抗审查每期/收口执行(memory:[[codex-adversarial-review-before-delivery]]);沿用 P0 的 `adversarial-review.md` 规程从 scratchpad 跑(memory:[[codex-exec-adversarial-review-howto]])。

## 6. 未决 / deferred(第一版范围外)

- **manual/ocr_optional 作 required provider 的验证路径**(R5-F1):第一版禁止(`required=true ∧ provider∈{manual,ocr_optional}` → `PACKET_INVALID`);完整路径(`--verify-review-record <run_id>` 或 pending-resume:supervisor 读同一 `slice_id/review_target/run_id` 的 manual/ocr append 行,重新 `normalize_review_record` 并绑定本轮 deterministic/invariant/scope 才允许 clean)**deferred 后续任务**。第一版 manual/ocr_optional 仅作**补充记录**(append CLI 写),不满足 required。
- **packet 自动生成**:第一版主会话/planning 手工创建(见 prd 非目标)。
- **deterministic_checks 结果文件化**:第一版 `deterministic_results[]` 内联 jsonl(stdout_summary 截断);若行过大,后续可改 `deterministic_results_path` 引用单独文件。
