# Codex 对抗审查轮次 — guru-skill-optimization-diagnosis.md

目标:codex(opposite-provider)对抗审查诊断文档,循环至 `verdict=APPROVE` 且零 findings。
配置:`codex exec`,model gpt-5.5,effort=high,read-only sandbox,cwd=scratchpad(避开 worktree Trellis hook 污染)。
每条 finding 我都读真实代码核实后才采纳,不盲信。

## Round 1

- verdict=REQUEST_CHANGES,blockers=1,should_fix=3,nice_to_have=0
- Findings(全部经核实成立):
  1. **[blocker] §5 ③ 机制错**:文档称"默认走对抗 provider(codex)",但 `--adversarial` 切到**对立** provider,`_opposite_provider("codex")=claude`(`guru_supervise.py:356-362`/`:407-412`);`ADVERSARIAL_MODEL_ACTIONS` 仅含 req/overview/detail(`:48`),模型旗标/对抗 prompt 也只对这三者(`:531-537`/`:589-598`)。
  2. **[should-fix] §5 ⑤ verdict 解析描述不准**:`route_class` 已容忍 `[:=：]` 且全文搜索(`:60-62`/`:345-353`);真正脆弱是 clean 精确子串(`:351`/`:52`)。
  3. **[should-fix] §3 过度归因**:"命中靠运气换 codex provider"——provider 因果未证(最终轮还叠加 OCR 多轮后上下文演化)。
  4. **[should-fix] §3 "全链 grep" 范围不清**:实为 Flutter-client 链;ios-detail-writing:117 / guru-arch-bugfix:42-46 有不变量槽位(但测试口径仍"成功+全部失败路径",同样漏成功路径排除)。
- 处置:4 条全部修入文档(③ 重写为"引入独立审查,审查者≠实现者,SSOT 接地②为根治";⑤ 精确化;§3 两处收紧)。
- Next:Round 2 复核。

## Round 2

- verdict=REQUEST_CHANGES,blockers=0,should_fix=3,nice_to_have=1(blocker 已清零)
- Findings(全部经核实成立):
  1. **[should-fix] ③ 仍不完全可落地**:`run_implement_check` 的 implement 与 check 共用同一 `config`/`spawned_provider`(`:1020-1038`),加 `--adversarial` 两者一起翻同一 provider → 仍不保证审查者≠实现者。须在 `run_implement_check` 做**双 provider** 路径。
  2. **[should-fix] "adversarial" 两义混淆**:req/overview/detail 是唯一 first-class 对抗 Gate(模型旗标+prompt+证据);implement-check 可手动 `--adversarial`(切 provider)但非默认、不隔离、无对抗 prompt/模型路径(`:4-10`/`:531-537`/`:589-598`)。
  3. **[should-fix] "仅 5 处"计数不可复现**:`guru-skill-chain-map.md:21-27` 未列出 5 条命中。→ 去掉精确数字,保留定性结论。
  4. **[nice] 跨平台旁注欠引**:补 `ios-design-detail-writing:119`(测试口径行)、纠正 Flutter 详细合同为 `detail-structure-single-source.md:50/:187`。
- 处置:4 条全部修入(③ 加双 provider + `run_implement_check` 目标;§3 对抗语义精确化;去掉"5 处";补/纠引用)。
- Next:Round 3 复核。

终止条件(用户更新):codex 零 blocker + 零 should-fix 即停;nice-to-have 可保留。

## Round 3

- verdict=REQUEST_CHANGES,blockers=0,should_fix=2,nice_to_have=0
- Findings(全部经核实成立):
  1. **[should-fix] ③ 配方仍不够精确**:`run_implement_check` 调的是 `build_run_plan("implement")`/`build_run_plan("check")`(`:1020-1038`),worker provider 取自 `config.provider`(`:507-518`);对抗旗标(`:531-537`)/prompt(`:589-599`)只对 `{requirements,overview,detail}` 触发,**对 "check" 不触发**。须 (a) 为 check 造 `check_config`(provider=对立)+ (b) 把 check 纳入对抗旗标/prompt 触发集。
  2. **[should-fix] §3 "跨平台仍成立" 过度结论**:仅 iOS/arch-bugfix 两点不足证全平台。→ 收敛为"Flutter 已证;iOS/arch-bugfix 同类信号;Go/H5 未审,不宣称全平台"。
- 处置:2 条全部修入(③ 给出完整两步配方;§3 结论收敛)。
- Next:Round 4 复核。

## Round 4 — 受阻(codex 网关故障,非文档问题)

- 三次尝试(r4 @20:04、r4b @23:09、r4c @23:40)均 `CODEX_EXIT=1`,错误 `503 GW_ALL_PROVIDERS_UNAVAILABLE`(`cli_key=codex`,`cooldown=1 / open=0`,`http://127.0.0.1:37123`)。
- 即 codex 代理上游持续不可用,非诊断文档问题。
- 故障史:r4 @20:04 / r4b @23:09 / r4c @23:40 均 `503 GW_ALL_PROVIDERS_UNAVAILABLE`(exit 1);r4d + ping 同时 exit 144(外部信号杀,网关已不 503、在推理中被误杀)。
- **r4e @23:57 跑通(exit 0)**:verdict=REQUEST_CHANGES,blockers=0,should_fix=4,nice_to_have=0。
- Findings(全部经核实成立,均为 ③/§3 更细精度 + 1 致一致性):
  1. **[should-fix] ③ 配方缺一步**:`:531`/`:589-598` 旗标/prompt gated on `config.adversarial AND action`,故 check_config 须 `adversarial=True`(或新建不依赖 `--adversarial` 的 review 模式),不只是换 provider + 加 action。
  2. **[should-fix] "不隔离实现者/审查者" 过头**:implement/check 已是不同 worker(`:1020-1038`),真正缺的是 provider/对抗语义独立。→ ③ 改名"opposite-provider/新上下文对抗 check"。
  3. **[should-fix] §3 引用错挂**:模型旗标/对抗 prompt 在 `guru_supervise.py`,非 `gate-confirmation-model.md:9-13`。→ 拆引用。
  4. **[should-fix] 附件自相矛盾**:`ocr-session-findings.md:2546` 仍写"亲手把 bug 写进代码与测试",与正文已纠口径冲突。→ 软化为"背书/未纠正"。
- 处置:4 条全部修入(③ 完整配方 adversarial=True+opposite provider+model/reasoning;§3 拆引用 + 纠"不隔离";附件软化)。
- Next:Round 5 复核。

## Round 5

- verdict=REQUEST_CHANGES,blockers=0,should_fix=2,nice_to_have=0
- Findings(全部核实成立):
  1. **[should-fix] ③ `adversarial=True` 重载/危险**:对抗失败会转成 `_skip_adversarial` 的 **advisory skip rc 0**(`:830-915`,`:756`"skip 绝不阻断"),给实现 Gate 设 `adversarial=True` 会"失败即放过",更危险。→ ③ 重定标:新增**独立 implementation-check-review 模式**,解耦 advisory 跳过、失败必须阻断;完整安全设计(触发/disabled/timeout-killed-error 路由/解析/单测矩阵)明确划归**实现 task**,诊断只定位缺口+方向。
  2. **[should-fix] "129 条数据层问题" 过强**:129 含测试质量 27、task evidence、DI/codegen 等相邻类。→ 改"129 条去重发现,多为 data-layer correctness,另含相邻类"。
- 处置:2 条全部修入。
- Next:Round 6 复核。

## Round 6

- verdict=REQUEST_CHANGES,blockers=0,should_fix=3,nice_to_have=1
- 注:③ 本轮**未再被 flag**(重定标为诊断层级生效);findings 转向外围精度。
- Findings(全部核实成立):
  1. **[should-fix] §3 "只报到日志/注释级" 过强**:第 1 轮 claude 有 P2(日志缺失 + owner mismatch),第 2 轮才 P3 放行;两轮均未碰核心数据缺陷。→ 改精确。
  2. **[should-fix] ③ `:756` 引用错挂**:`:756` 是"skip 持久化失败 advisory",非"skip 执行 advisory";rc 0 在 `:830-841`、call sites `:849-915`、disabled `:956-962`。→ 改引用。
  3. **[should-fix] §6 跨审查者不可审计**:4 个 Claude agent 输出未落盘。→ 弱化为"会话内背景;可直接审计的异构证据是 codex-review-output2.txt"。
  4. **[nice] ⑤ 解析建议过窄**:→ 拓宽为"clean 与 findings 都结构化、恰好一个 review_result+route_class"。
- 处置:4 条全部修入。
- Next:Round 7 复核。
- 观察:should_fix 轨迹 3→3→2→4→2→3,在外围精度上震荡;核心论点(GAP A/B、OCR 非依赖、SSOT 否决、③ 方向)已稳定。

## Round 7 — APPROVE(循环完成)

- **verdict=APPROVE,blockers=0,should_fix=0,nice_to_have=0**(干净通过,无 findings;codex 本轮 ~295k tokens 核验)。
- 达成终止条件(0 blocker + 0 should-fix)。

## 汇总

- 轨迹:R1(1B+3SF)→ R2(0B+3SF+1N)→ R3(0B+2SF)→ R4(0B+4SF,前置 503×3 + 信号杀×1 后由 r4e 跑通)→ R5(0B+2SF)→ R6(0B+3SF+1N)→ **R7 APPROVE 0/0/0**。
- 纪律:每条 codex finding 均经"读真实代码核实"后才采纳,未盲信工具输出;codex 全程 read-only、cwd=scratchpad(避 hook 污染)、不调用 `ocr`。
- 产物:`guru-skill-optimization-diagnosis.md`(已含 R1-R6 全部修订);证据 `scratchpad/*`。

## 实现变更后再验证(Round 8+)

- 触发:session 后落 5 个 commit(`830ababc..HEAD`):`guru_gate.py` +770(REQ-UC×BHV 追溯矩阵 + 版本化需求包)、`guru_supervise.py` +23/−13(`_requirements_digest` 委托 guru_gate + 新 sibling import)、requirement/overview 结构、run_tests.sh +330。
- 复核结论:诊断重度引用的 `guru_supervise.py` 符号行号/行为**未变**(③/⑤ 成立);skills/合同未变;诊断未引用 `guru_gate.py`。核心论点未被取代。
- 已调整诊断 3 处:④ 重写为"在既有 REQ-UC×BHV 追溯矩阵上扩负向/排除维度(对齐 SSOT)";§3 加新矩阵注记(仍正向、不关闭 GAP B);加"实现现状注记"(supervise→gate import 已 live;R7 APPROVE 已对旧代码失效)。
- R7 APPROVE 作废(针对旧代码),启动 Round 8 对新代码重新背书,终止条件仍为 0 blocker + 0 should-fix。

### Round 8(新代码)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=2,nice_to_have=1
- Findings(全部核实成立):
  1. **[should-fix] ② SSOT 否决落地前提缺**:`build_run_plan` 只给 implement/check 注入 task 本地 `prd/design/implement.md`(`:468-473`),**正式需求/设计包仅 `requirements` action 展开**(`:474-480`)→ ② 须额外让 implement/check 显式加载正式包。
  2. **[should-fix] ③ disabled-adversarial 混淆**:`adversarial_enabled` 守卫在 `run_action`(`:956-962`),`run_implement_check` 无该守卫(`:968-977`)→ implement-check 忽略该开关(亦是隐患)。拆开表述。
  3. **[nice] "+770" 非稳定 file:line** → 换 `build_trace:799`/`render_matrix:853`/`cmd_trace_matrix:889`。
- 处置:3 条全部修入。
- Next:Round 9 复核。

### Round 9(新代码)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=1,nice_to_have=0
- Finding(核实成立):**[should-fix] ② 的 round-8 落地前提本身不精确**——`:474-480` 不是展开"正式需求/设计包",而是给 `requirements` 加 `task.json` + `relatedFiles`/markdown 链接可达文件(`_requirements_reference_files:320`,prompt `:607-620`);`requirement_package`/`design_package` 是 `guru_gate.py:497` 的 digest 概念,不注入 supervise worker。→ ② 改为"须为 implement/check 显式加载 requirement_package/design_package"。
- 处置:② 精确改写。
- Next:Round 10 复核。
- 观察:新代码轨迹 R8(2SF+1N)→ R9(1SF),收敛中。

### Round 10(新代码)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=5,nice_to_have=1(回升:②/③ 被深挖到实现规格精度)
- Findings(全部核实成立):
  1. **[SF] ⑤ 过度推广到 requirements 路径**:requirements clean 不要求 `route_class=none`(`:52`/`:778-786`/`gate-confirmation-model.md:147-155`)→ ⑤ 限定 implement-check。
  2. **[SF] ② design_package 引用错**:design 在 `_package_dir:470`、req 在 `:497`、digest 在 `_gate_artifacts:1604`。→ 修引用。
  3. **[SF] ② 未规定安全加载路径**:gate 有 repo-root 围栏/canonical-exclude fail-closed/digest 命名空间(`:497-529`/`:671`/`:1239`/`:1604`)→ ② 须复用 gate 安全枚举器、不另起 package-walk;精确接线归 impl task。
  4. **[SF] ③ skip 语义太笼统**:三情形(独立 check advisory rc0 `:939-965`;implement-check 跳过 implement 误推进 `:1020-1031`;check 跳过反 fail-closed rc2 `:1038-1057`)。→ 三情形精确化。
  5. **[SF] ① "没有逐行扫描密度" 过强**:skill 已有 D1 合同逐项核对(`:17`/`:23`),缺的是数据语义逐行(`:50` 改动面边界)。→ 软化。
  6. **[nice] §6 跨 provider 仍偏强** → 明确"Claude 收敛不作独立证据"。
- 处置:5SF+1nice 全部修入(② 同 ③ 重定标为诊断层级:给安全约束、精确接线归 impl task)。
- Next:Round 11 复核。

### Round 11(新代码)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=2,nice_to_have=1(② 重定标见效:5→2)
- **codex 收尾段明确背书核心**:硬约束满足(五优化皆 skill/runtime、OCR optional 非必需)、GAP A/B 均有支撑、OCR 定性恰当("背书/未纠正非原创")。
- Findings(核实成立):
  1. **[SF] §3 "129 在同一 diff" 过强**:OCR 跨 20 轮、文件集 16→35(持续演化 diff)。→ 改"持续演化 diff 累计"。
  2. **[SF] ② 引用错**:`:671` 是 canonical_root 非 canonical_excludes;后者在 `:591-668`,package fail-closed `:1239`。→ 修引用。
  3. **[nice] codex 找不到 codex-review-rounds.md**(在任务目录、其 cwd 未达)→ 标明 co-located/session-local。
- 处置:3 条全部修入。
- Next:Round 12 复核。

### Round 12(新代码)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=3,nice_to_have=0(全为收尾精度,无一触及核心)
- Findings(核实成立):
  1. **[SF] §1.1/§2 "codex check 以 SSOT 为基线" 措辞**:supervise 不注入正式包,是 worker 自行引用项目侧 SSOT。→ 改为"worker 显式引用项目侧 SSOT、非注入基线"。
  2. **[SF] ② 漏列 requirements 也注入 `*.jsonl`**(`:481-488`)→ 补,并标注 task-local≠正式包。
  3. **[SF] ⑤ route 全文搜索也脆弱**(`_route_from_output:345-353` 会命中散文/陈旧 route)→ 补"取代 route 全文搜索 + clean 子串两条脆弱路径"。
- 处置:4 处全部修入(line23/31 + ② + ⑤)。
- 轨迹(新代码):R8(2)→R9(1)→R10(5)→R11(2)→R12(3),在收尾精度区间震荡;核心 R11 已被 codex 收尾段背书。
- Next:Round 13(建议作为停点判定轮)。

### Round 13(新代码)— 受阻(codex 503)

- 跑到 9975 行(已读文件+推理),收尾出 verdict 时撞 `503 GW_ALL_PROVIDERS_UNAVAILABLE`(cooldown=2,exit 1)——外部网关故障,非文档问题。**无 verdict 产出。**
- 文档状态:已含 R1–R12 全部修订(R12 的 3 条收尾精度已修);核心于 R11 经 codex 收尾段背书。
- 停点决策待用户定:(a) 等代理恢复跑 R13b 取最终 verdict;(b) 宣布实质完成(核心已背书、12 轮实质问题闭合,剩余属实现 task 该承载的规格精度)。

## 最终处置:实质完成(用户 2026-06-29 确认)

- **结论:实质完成。** 诊断核心于 R11 经 codex 逐条背书;R1–R12 全部 findings 已闭合;R13 仅因 codex 代理外部 503 未出字面 verdict,非文档问题。
- 总轨迹:旧代码 R1(1B+3SF)→…→R7(APPROVE 0/0/0);实现变更后 R8(2SF)→R9(1)→R10(5)→R11(2+核心背书)→R12(3,已修)→R13(503 无 verdict)。
- 纪律:每条 finding 均经读真实代码核实后采纳;codex 全程 read-only / cwd=scratchpad / 不调用 `ocr`;外部 503/信号杀如实记录、未造假、未用 Claude 假冒 codex 闸。
- 产物:`guru-skill-optimization-diagnosis.md`(终稿)、本日志、`scratchpad/` 证据。
- 待办(非本诊断范围):若进入实现,新建 Trellis task 落地五条优化(③/② 的精确接线 + 安全枚举器复用 + 负向不变量挂进 REQ-UC×BHV 矩阵)。
