# Implement — Guru slice packet + invariant matrix + 结构化 review record (P1)

约定:每期改完先本地验证 → 独立 commit → `sync:guru` 同步 mirror → `sync:guru:check` 无漂移;**每期(含收口)经 codex opposite-provider 对抗审查**(`adversarial-review.md`,从 scratchpad 跑)。SSOT:`../06-28-guru-review-governance-report/problem-report-and-solution.md` §4;设计:`design.md`。flutter-only。

**分期依赖序(codex R1-F1 修正)**:P1a(reader+writer 基础)→ P1b(packet 上下文接线 + preflight)→ P1c(verdict gating,**用 P1b 建立的 packet 上下文分流**)。verdict gating 必须晚于 packet 上下文,否则 supervisor 无法知道"有 packet 的 high-risk slice"。

## 通用验证命令
```bash
python3 -c "import ast; [ast.parse(open(f,encoding='utf-8').read()) for f in [
  'guru-template/overlay/verify/guru_risk.py','guru-template/overlay/verify/guru_gate.py',
  'guru-template/overlay/verify/guru_supervise.py','guru-template/overlay/verify/guru_review_record.py']]; print('ast OK')"
PYTHONPATH=guru-template/overlay/verify python3 -B -c "import guru_risk,guru_gate,guru_supervise,guru_review_record;print('import OK')"
PYTHONDONTWRITEBYTECODE=1 bash guru-template/overlay/verify/tests/run_tests.sh
pnpm -C packages/cli sync:guru && pnpm -C packages/cli sync:guru:check   # 无漂移
```

---

## Phase P1a — packet reader + record writer 基础 + guru_risk 扩展

### 步骤 1 — `guru_review_record.py` 骨架 + packet schema(两层)+ reader + writer
- [x] 新建 `guru-template/overlay/verify/guru_review_record.py`:枚举(REVIEW_RESULT/ROUTE_CLASS/三 gating + `supervisor_failure∈{none,SCOPE_INVALID,MALFORMED_REVIEW_OUTPUT,PACKET_MISSING,PACKET_INVALID,PACKET_AMBIGUOUS}`)、`class ReviewRecordError`、`schema_version=1` 护栏。**不 import guru_gate/guru_supervise**(防循环)。
- [x] **packet schema 两层(F3)**:`load_packet(task_dir, unit_id)`/`list_packets(task_dir)` 读 `<task_dir>/slice-packets/<unit_id>.json`,校验:
  - 必填:`schema_version=1`、`slice_id`、`owner_unit`、`target_kind`、`target_paths[]`、`invariants[]`(每条 `invariant_id/rule/source/owner/positive_case/negative_case/route_if_missing`,`test_evidence[]` 可空)。
  - 可选 + 默认:`risk`(R3-F3:可缺省;`high|critical|low`→参与;**`unknown`/null/空→规范化 `None` 回落 P0**;**其他字符串(如 `medium`)→`PACKET_INVALID`**)、`risk_reasons[]`、`deterministic_checks[]`、`dirty_state.unrelated[]`(缺→空集)。
  - **`semantic_review_provider` schema(R3-F4/R5-F1)**:present 时 `required:bool` / `provider∈{codex,claude,opposite}` / `ocr∈{optional,disabled}`;**缺→`{required:true,provider:opposite,ocr:optional}`**;`required=false` 仍须 opposite(不降格);**R5-F1:`required=true ∧ provider∈{manual,ocr_optional}` → `PACKET_INVALID`**(第一版 required 只支持 channel-spawnable;manual/ocr 仅补充记录,verify-record 路径 deferred,design §6);非法结构 → `ReviewRecordError`。
  - 非法(缺必填 / 未知 schema_version / 非 JSON / semantic_review_provider 结构非法)→ `ReviewRecordError`;**缺 `risk` 不 raise**。
- [x] **writer 基础(F2/F6/R2-F1/R3-F2/R5-F2/F3)**:`append_record(task_dir, record)`(**唯一 writer**:mkdir `review-records/` + 写 `implementation-reviews.jsonl`,**字段全集含 `review_target`(R3-F2)+ `deterministic_results[]`(R5-F2:逐条 command/cwd/exit_code/timed_out/stdout_summary/duration_ms/run_at)+ 可选 `message`/`candidates[]`(R5-F3)** + §4.4 全集;provider→channel/worker sentinel 派生)+ `preflight_failure_record(kind, run_id, unit_id=None, candidates=None)`(canonical `review_result=blocked, **route_class=none**[非 PROCESS_DEFECT,R2-F1:scope/packet failure 是 supervisor_failure 不是 worker route,PROCESS_DEFECT 在 REPAIRABLE 里], supervisor_failure=PACKET_MISSING|PACKET_INVALID|PACKET_AMBIGUOUS|SCOPE_INVALID, repairable=false`;**字段策略 R2-F6**:有 --slice→`slice_id=unit_id,target_paths=[],review_target=slice:<unit>`;无 --slice 且零 packet→`slice_id=null,target_paths=[],review_target=slice:unknown`;多 packet→候选入 `message`)。
- verify:单测——合法 packet(无 risk)通过;缺 invariant.negative_case / 缺 target_paths / 缺 owner_unit / 未知 schema_version / 非 JSON / `semantic_review_provider` 结构非法 → 各自 raise;**`invariants:[]`(空)/`target_paths:[]`(空)/空 path 字符串/非对象 invariant → PACKET_INVALID**(R9-F1 非空);**`risk` 缺/`unknown`/null→规范化 None 不 raise;`risk:medium`→PACKET_INVALID**(R3-F3);**`semantic_review_provider.required=true` 且 `provider∈{manual,ocr_optional}`→PACKET_INVALID**(R5-F1);append_record 写出行含 review_target 可重新解析且字段齐;preflight_failure_record 各 kind 产 repairable=false。

### 步骤 2 — `guru_risk.py` 接 slice_packet.risk + scan_dirty_paths
- [x] `RISK_REASON_KEYWORDS = {protocol_migration,cross_layer,stateful_cache_merge,db_migration,payment,ads,permission,privacy}`(§4.5.9)。
- [x] `slice_packet_risk(task_dir, unit_id) -> str|None`:经 `guru_review_record.load_packet` 读(单一 packet reader);`risk∈{high,critical}` 或 `risk_reasons` 命中关键词 → `"high"`;显式 `low`→`"low"`;无/unknown→`None`。
- [x] `scan_dirty_paths(repo_root)`(F4):复用 `scan_paths` 的 `git status --porcelain=v1 -z -uall`(单一 dirty path 来源,含 untracked/rename/delete);**不重新发明 `git diff` 弱扫描**。
- [x] **R3-F3:先把现 `implement_check_independent_required` 的 L160-183 原样抽成私有 `_p0_implement_check_independent_required(task_dir, platform, repo_root)`**(避免递归/复制),公开函数扩 `unit_id=None` 三分支:
  - `packet_risk = slice_packet_risk(task_dir, unit_id)`(unit_id=None→None)
  - `packet_risk=="high"` → `(True,"slice-packet high-risk")`(**先于** task,BHV-007)
  - **`packet_risk=="low"` → `(False,"slice-packet low-risk")`**(R8-F1:slice 级 low override,SSOT §4.5.9;**不调 _p0_**、不被 task high/unknown 或 git scan 抬高)
  - **`packet_risk is None`(无 packet / 无 risk / unknown / unit_id=None)→ 调 `_p0_...`**(原 L160-183 逻辑)
- verify:单测——**公开函数 `unit_id=None` 不递归、结果与旧函数字节一致**;packet.risk=high + task.json low → required(override);**packet.risk=low + task high → 不 required(R8-F1 slice low override);packet.risk=low + git scan 命中跨层 → 不 required**;**packet 无 risk + task unknown → required;packet 无 risk + dirty 跨层 → required**;packet 无 risk + 合法 approved-low 且无跨层 → 不 required;scan_dirty_paths 与 scan_paths 同口径(untracked 不折叠)。

**P1a commit + sync + codex 对抗。**

---

## Phase P1b — packet 上下文接线 + packet/scope preflight(F1:先于 verdict gating)

### 步骤 3 — CLI `--slice` + packet resolve + 风险判定接线
- [x] implement-check subparser 加 `--slice <unit_id>`。
- [x] `run_implement_check` 进循环前 packet resolve:`--slice` 显式 / 单 packet 自动选 / 多 packet 未指定 → `PACKET_AMBIGUOUS`;得到 `unit_id`(或 None=无 packet)。
- [x] 风险判定改 `guru_risk.implement_check_independent_required(str(task_dir), config.platform, str(root), unit_id=unit_id)`(packet.risk 优先)。

### 步骤 4 — packet preflight(BHV-001,F6)
- [x] flutter high-risk 且无 packet/packet 非法/多义 → `preflight_failure_record(PACKET_MISSING|PACKET_INVALID|PACKET_AMBIGUOUS)` + `append_record` + **exit2,绝不进 `REPAIRABLE_IMPLEMENT_ROUTES`**(不启 implement worker 现场补造)。
- verify:dry-run——high-risk 无 packet → exit2 + jsonl(repairable=false);单 packet 自动选;多 packet 未 --slice → PACKET_AMBIGUOUS exit2;**确认不进修复循环**。

### 步骤 5 — scope preflight(BHV-002,§4.5.3-6,F4)
- [x] 进循环前一次:`guru_risk.scan_dirty_paths(root)`(唯一 dirty 来源)与 packet `target_paths`(范围内)、`dirty_state.unrelated`(记 isolated)对比;两者都不属 → `preflight_failure_record(SCOPE_INVALID)` + append + exit2,不启 worker。
- verify:单测——dirty 属 target_paths→放行;属 unrelated→isolated 放行;越界→SCOPE_INVALID exit2;**untracked 新建越界文件也被检出**(复用 -uall)。

**P1b commit + sync + codex 对抗。**(触 control flow,回滚优先级高)

---

## Phase P1c — 结构化 verdict gating(用 P1b packet 上下文,取代全文搜索)

### 步骤 6 — `guru_review_record.py` verdict 校验 + 规范化(F2)
- [x] `validate_verdict_values(fields) -> failure_code|None`(R8 命名统一:取值校验层①,所有 provider 共用):`final-verification-ready`→`clean` 归一;clean 须 `deterministic_checks=passed ∧ dirty_scope∈{clean,isolated} ∧ invariant_coverage=all_passed`;缺任一 7 字段或取值非法 → `"MALFORMED_REVIEW_OUTPUT"`。
- [x] `normalize_review_record(fields, context) -> (record, failure_code)`(**唯一规范化入口**,**两层判定 R7-F2**):
  - ① `validate_verdict_values(fields)`(**所有 provider 共用**):7 字段存在性 + 枚举 + 三通过值一致性;不过→canonical blocked(MALFORMED)。
  - ② **required-provider gating** 只在 supervisor 消费 channel-spawned check 作 required clean 时执行(R2-F2/R5-F1):第一版 provider 只 `{codex,claude,opposite}`,required 只由 channel-spawned 满足(default 须实现者 opposite);clean 还须 **supervisor deterministic=passed(R3-F1)+ `aggregate_invariant_coverage` 重算=all_passed(R3-F5)**。
  - **manual/ocr append 走 supplemental**(`context.mode=supplemental`):只过 ①、不执行 ② required satisfaction;record 标 `required_satisfied=false`+`supplemental=true`,**保留为补充审计记录**(`--result clean` 也不被消费为 required clean、不打成 malformed)。`manual/ocr_optional` 作 packet required 仍在 load_packet 判 PACKET_INVALID。
  - 任一层不过 → canonical `review_result=blocked,route_class=none,supervisor_failure=MALFORMED_REVIEW_OUTPUT,repairable=false`;合格则原样。
- [x] `aggregate_invariant_coverage(packet_invariants, reviewer_statuses) -> all_passed|failed|missing`(R3-F5/R9-F2,**唯一聚合**)。**per-invariant 机器合同(R9-F2)**:`invariant_status.<id>=pass|fail|not_applicable` + `invariant_evidence.<id>=<非空证据摘要/引用>` + `invariant_reason.<id>=<not_applicable 必填>`。规则:`pass` 须非空 evidence;`not_applicable` 须非空 reason;未知 id→MALFORMED;**缺 status / `pass` 缺 evidence→missing**;任一 fail→failed;否则 all_passed(packet invariants[] 仍是机器 SSOT)。
- [x] `run_deterministic_checks(commands, repo_root) -> (status, results)`(R3-F1/R5-F2,BHV-008):repo root 逐条跑 + timeout;全 exit0→passed;失败/timeout→failed;空/缺→missing;**`results` 逐条含 command/cwd/exit_code/timed_out/stdout_summary/duration_ms/run_at,写入 record `deterministic_results[]`(审计回放)**。
- [x] `parse_verdict_block(text) -> fields`:从 worker 输出置顶解析 7 字段 + per-invariant `invariant_status.*`/`invariant_evidence.*`/`invariant_reason.*`(行级 `key=value`,与 `aggregate_invariant_coverage` 同字段合同)。
- verify:单测——clean+三通过+provider 匹配+deterministic passed+聚合 all_passed→保留 clean;clean+deterministic_checks=failed → MALFORMED(不丢记录);缺 invariant_coverage → MALFORMED;findings/blocked 不要求三通过;**R5-F1:provider=manual/ocr_optional 作 required→PACKET_INVALID(load_packet);worker 自报 manual/ocr→不可 clean;default 同 provider→不可 clean;append 写的 manual/ocr 行仅补充审计、不被消费为 required clean;OCR 全程不在完成条件**;**R3-F1:supervisor deterministic failed → 不可 clean(即便 worker 自报 passed);packet deterministic 空→missing 不可 clean**;**R3-F5/R9-F2:任一 fail→failed;`pass` 缺 `invariant_evidence`→missing;`not_applicable` 缺 `invariant_reason`→拒;合法 N/A(有 reason)→all_passed;未知 id→MALFORMED;worker 自报 all_passed 但重算 missing→阻断;`invariants:[]` 空 high-risk packet→load_packet PACKET_INVALID**;**R7-F2:`mode=supplemental` 的 manual/ocr append 写 `--result clean` → 标 `supplemental=true`/`required_satisfied=false` 保留补充审计记录(不被消费为 required clean、不打成 malformed);但缺 7 字段/取值非法仍过①被拒**。

### 步骤 7 — `guru_supervise.py` verdict gating 取代 `_route_from_output`
- [x] **packet 注入 worker(R4-F2)**:`build_run_plan`/`RunPlan` 扩 `slice_context`——resolved packet path 加入 `artifact_candidates`/`--file`;implement/check brief 写 `active_slice=<unit_id>`/`slice_packet=<path>`/`review_target=slice:<unit_id>`/`target_paths` 摘要/`semantic_review_provider`;多 packet 只注入 resolved。否则 worker 拿不到 packet、无法输出 `invariant_status.*`/正确 provider。dry-run 须显示注入 packet。
- [x] **supervisor deterministic 执行(R3-F1/R4-F1/BHV-008)**:**每轮 implement worker 成功后**(非循环前一次)针对当前 repo 状态跑 `run_deterministic_checks(packet.deterministic_checks, root)`,结果注入**本轮** check context;repair 后下一轮重跑(**不复用过期结果**)。
- [x] check 输出解析改 `parse_verdict_block` + `normalize_review_record`(取代 `_route_from_output` ROUTE_RE 全文搜索 + clean 子串,L65-68/L350-358)。
- [x] **分流(用 P1b packet 上下文)**:有 packet high-risk slice → 强制 7 字段;**`normalize_review_record` 传 context**(packet `semantic_review_provider` + implement `config.provider` + check `check_config.provider` + **本轮 supervisor deterministic 结果 + reviewer invariant statuses**)做 provider gating + **本轮 deterministic 双过 + `aggregate_invariant_coverage` 重算**(R2-F2/R3-F1/F5);任一不过 → canonical record + exit2。无 packet 流程 → 保留旧 route 解析(过渡,design §5)。
- [x] **每轮总是 `normalize_review_record → append_record`**(F2:合格记裁决,malformed 记 canonical;绝不拒绝后手写 jsonl)。
- [x] brief 加 "Do not run OCR by default. OCR is optional and bounded." + 要求 check worker 审 invariant matrix、置顶输出 7 字段 + per-invariant `invariant_status.*`。
- verify:run_tests + dry-run——`--slice UNIT-a` spawn 命令含对应 packet `--file` 且 brief 含 active slice;结构化 clean(三通过+provider+本轮 deterministic 双过+聚合 all_passed)接受;**第一轮 deterministic failed→repair,第二轮 rerun passed 才 clean**;clean 但 invariant_coverage=missing / **本轮 supervisor deterministic failed(worker 谎报 passed)/ provider 不匹配** → exit2 MALFORMED + jsonl;**旧散文 `route_class: clean` 在 packet slice 不再误判 clean**;非 packet 流程旧行为不变。

**P1c commit + sync + codex 对抗。**(触 control flow,回滚优先级最高)

---

## Phase P1d — flutter skill 集成 + ④ 负向维度

### 步骤 8 — flutter skills(§4.6,F5:writing 仅校验)
- [x] `flutter-implementation-guru-writing/SKILL.md`:WX-1 加 UNIT/target_paths 计划节(所有 slice);high-risk **仅校验 packet 已存在** + 在 implement.md 摘要 slice_packet/invariant_ids/negative_case;**缺失即停回 planning,绝不在实现 worker 内创建/补造 packet**(F5,packet 由主会话/planning 阶段先建)。
- [x] `flutter-implementation-guru-review/SKILL.md`:装载加 packet/matrix;D1 扩"diff vs invariant matrix 逐条 pass/fail/N/A";D4 每条 high-risk invariant ≥1 正/负测试;clean/final-verification-ready 输出节加 5 gating 字段 + **per-invariant `invariant_status.<id>`/`invariant_evidence.<id>`/`invariant_reason.<id>`(R9-F2:`pass` 须非空 evidence、`not_applicable` 须非空 reason)**;无 matrix → DETAIL_DEFECT/PROCESS_DEFECT(BHV-004)。边界:不得要求 OCR 默认完成。
- [x] manual provider append 命令文档(§4.6.7)写进 review skill。

### 步骤 9 — ④ detail/requirement 负向维度
- [x] `detail-structure-single-source.md`:八问之 8 升级含 invariant(rule/owner/positive_case/negative_case/route_if_missing);加"不变量矩阵"章节模板,字段**对齐 packet schema**(勿另起,[[guru-requirement-doc-standard-is-ssot]])。
- [x] `requirement-doc-standard` references:补 invariant/负向/排除维度定义,对齐 detail-structure。
- verify:对 Himora INV-LOCAL-FACTS-ONLY 走查——detail 阶段能 elicit 出负向不变量;review skill 输出节字段与 §4.4 一致。

**P1d commit + sync + codex 对抗。**

---

## Phase P1e — trace-contract + workflow(§4.7/4.8)

### 步骤 10 — trace-contract + workflow
- [x] `implementation-trace-contract.md`:§1 计划节加 UNIT/target_paths(所有 slice);high-risk 加 slice_packet/invariant_ids/negative_case;§3 测试按 invariant 归档;§4 invariant 缺失回退 detail。
- [x] workflow(`guru-client-workflow.md`):Phase 2 semantic review provider 可替换;OCR 降 optional;完成条件 = deterministic passed + invariant all_passed + dirty scope clean/isolated + no blocker/should-fix;`No comments generated` 不作退出目标。
- verify:workflow breadcrumb 自检通过(apply.sh §);无 OCR 必选措辞。

**P1e commit + sync + codex 对抗。**

---

## 收口
- [x] **apply.sh 收编 `guru_review_record.py`**:copy list(L223-231)+ ast.parse(L665-675)+ import 冒烟(L677-681)三处扩列;import 冒烟改 `import guru_risk,guru_gate,guru_supervise,guru_review_record`。
- [x] 通用验证命令全绿(run_tests 覆盖 **BHV-001..008**,显式含 BHV-008 四类:supervisor command passed、packet deterministic 空/缺→missing、命令 failed/timeout→failed、worker 自报 passed 但 supervisor failed 不可 clean;**+ R5-F2:deterministic_results 逐条可从 jsonl 回放;R5-F1:required=manual/ocr_optional→PACKET_INVALID;R5-F3:PACKET_AMBIGUOUS 候选可回读**);`sync:guru` + `sync:guru:check` 无漂移;guru-bundled.test.ts 视情加 packet/verdict 用例。
- [x] **review gate:codex opposite-provider 对抗审查全 P1 改动至 0 blocker + 0 should_fix**;输出存 `codex-review-p1.txt`、轮次记 `codex-plan-review-rounds.md`。（R1→R6 收敛:**R6 codex 终审 APPROVE 0B+0SF+0n**;代理故障期补 Claude 独立复审发现并修 F1 fail-open/F2 pin 收窄/F3 文档;codex-review-p1.txt 存 R1-R6 全文,轮次记 codex-plan-review-rounds.md;314/0)
- [x] 确认全程无 OCR 必选依赖(codex 复核)。

## 回滚点
- 每期独立 commit;失败 `git revert` + `sync:guru` 还原镜像。
- P1b(preflight 硬停)/P1c(verdict gating)触 control flow,回滚优先级最高;保留每期通过的 commit 作下期基线。
- 源 + mirror 双源:用 `git add -p` 隔离与 06-24/其他并行任务的 apply.sh 改动(同 P0 教训)。
