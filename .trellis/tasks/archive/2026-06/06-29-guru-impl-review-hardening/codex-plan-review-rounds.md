# Codex 对抗审查轮次 — planning 文档(prd/design/implement)

目标:codex(opposite-provider)审 planning 三文档,循环至 0 blocker + 0 should-fix 后才 `task.py start`(memory:planning 文档交付前须经 codex 对抗审查)。
配置:`codex exec` / gpt-5.5 / effort=high / read-only / cwd=scratchpad / 不调 `ocr`。每条 finding 读真实代码核实后采纳。

## Round 1

- verdict=REQUEST_CHANGES,blockers=1,should_fix=4,nice_to_have=0
- Findings(全部核实成立):
  1. **[blocker] ② cwd 安全 bug**:`_package_dir`(design_package,`:487`)按 `os.getcwd()` 解析返相对路径,`_gate_artifacts:1620` 调它没传 repo_root;只有 requirement_package repo-root-safe。supervise 在 cwd≠repo-root 下注入会指错/丢失。→ 前置重构 `_package_dir(...,repo_root)`/新 helper,两包都按 config.root 解析为绝对 fenced,补 cwd≠root 回归测试。
  2. **[SF] ③ 缺机器触发契约**:未定义 high-risk-flutter 的运行时判定源。→ 经导出/共享 `_risk_level`(`guru_gate.py:1705`)读 task.json + platform 门 + unknown 策略 + 四类测试。
  3. **[SF] prd 仍把已定决策列为"开放"**:与 fixed scope/design 冲突。→ 改"已确认决策"。
  4. **[SF] design ③ 引用错**:`:939-965` 是 run_action;实际 rc0 advisory 在 `_skip_adversarial:830-841`/`_execute_plan:844-924`,推进在 `:1027-1040`。→ 修引用。
  5. **[SF] implement 验证不可跑**:`<target>` 占位、未验 apply.sh 拷贝覆盖。→ 具体 temp-project smoke(mktemp→apply.sh→import)+ 新脚本拷贝断言。
- 处置:6 处全部修入(prd 决策、design ②前置+③触发/引用、implement 步2前置+步3触发+验证 smoke)。
- Next:Round 2 复核。

## Round 2 — 受阻(codex 代理外部故障)

- R2 @10:40 `ERROR: Selected model is at capacity`(gpt-5.5 满载,exit 1,无 verdict)。
- R2b @10:45(重试)`503 GW_ALL_PROVIDERS_UNAVAILABLE`(cooldown=2,exit 1,无 verdict)。
- 即 codex 代理持续不稳(容量/503 交替),非文档问题。两次均读完文件、收尾出 verdict 时被打断。
- 文档状态:已含 R1 全部 6 处修复(含 blocker 的 cwd-safety,blocker 底层事实已由我读真实代码核实)。
- 待办:codex 代理恢复后跑确认 verdict(0 blocker + 0 should-fix)→ 才 `task.py start`。

## Round 3 — 受阻(codex 503,4 连败)

- R3 @11:01:挺过 3 轮重连(读到 5256 行)收尾仍 `503 GW_ALL_PROVIDERS_UNAVAILABLE`(cooldown=2,exit 1,无 verdict)。
- 至此外部故障 4 连败:诊断 R13(503)/ planning R2(容量)/ R2b(503)/ R3(503)。即时重试已证无效,需代理真正恢复或用户侧检查 codex 代理/账号。
- 文档状态不变:R1 全部 6 处修复在位(含 blocker 的 cwd-safety,底层事实已读真实代码核实)。**确认 verdict 待代理恢复。**

## Round 4(代理恢复后)

- verdict=REQUEST_CHANGES,blockers=0(**blocker 已清,cwd-safety 修复被接受**),should_fix=3,nice_to_have=0
- Findings(全部核实成立):
  1. **[SF] import smoke 不可跑**:`apply.sh:17` 要求目标先有 `.trellis/` 否则 exit1;`mktemp -d` 是空目录。→ 加 `mkdir -p "$tmp/.trellis"`,实参仅 `<target>`。
  2. **[SF] ③ 缺 disabled-adversarial 契约**:`adversarial_enabled=false` 时 run_action 走 `_skip_adversarial` rc0;高风险 flutter implement-check 必须**返回非零阻断**(非 rc0 skip)+ 测试。→ design ③ 加硬契约,implement 步3 加用例 (e)。
  3. **[SF] design ① 引用 "§4.4 字段" 不存在**:flutter review skill 无 §4.4;字段在 `## 输出 / 机器可读收口字段`(`SKILL.md:37`)。→ 改引用。
- 处置:3 条全部修入(implement smoke、design ③ + implement 步3、design ①)。
- Next:Round 5 复核。

## Round 5 — 受阻(代理间歇 503)

- r5 @11:18 / r5b @11:20(重试)均 `503 GW_ALL_PROVIDERS_UNAVAILABLE`(cooldown=2,exit 1,无 verdict);r5b 秒崩。
- 代理在 r4 后又掉——**间歇性**(r4 是好窗口)。R4 的 3 条修复在位,只差确认 verdict。
- 现状评估:planning 文档已过 **2 个真实 codex 轮**(R1 1B+4SF、R4 0B+3SF,全部核实+修入,**blocker 已清**),findings 递减且趋外围(可跑性/测试用例/引用)。待一轮干净确认 verdict(0/0)即过闸。决策待用户:稳定窗口再跑确认 / 或按实质过闸进 start。

## Round 6(自动重试循环 attempt 2 命中;用户要求"不因代理停")

- 用自动重试循环(6 次/40s 间隔,命中 `^verdict=` 即停)熬过间歇 503:attempt1 503 → sleep → **attempt2 拿到 verdict**。
- verdict=REQUEST_CHANGES,blockers=1,should_fix=2,nice_to_have=0
- Findings(全部核实成立):
  1. **[blocker] unknown-risk 自相矛盾 + 可绕过 ③**:design 说"定义 unknown 策略"、implement 却写"unknown 行为不变";`_risk_level` 缺元数据返回 unknown(`:1730`,docstring `:1706` 明示 unknown 不自动 skip),本任务 task.json 无 risk_level → 会绕过新 check。→ unknown flutter **fail-closed 启用独立 check**(prd/design/implement 三处同步,加缺元数据→触发的回归)。
  2. **[SF] sync drift 非真 gate**:`git diff --stat` 永远 exit0,镜像 stale/缺文件不会失败。→ 标注 --stat 仅人工速览;真 gate = 新增 `sync:guru:check`(temp 比对)。
  3. **[SF] codex gate 不可复跑**:只指向 memory。→ 新建 `adversarial-review.md` 规程(read-only/禁 ocr/verdict 格式/通过条件/留痕),P0/P1 收口改引用它 + 存 `codex-review-p{0,1}.txt`。
- 处置:全部修入(blocker fail-closed 三处;sync gate 重述;新建 adversarial-review.md + 收口引用)。
- Next:Round 7 复核(继续自动重试循环熬代理)。

## Round 7(循环 attempt 3 命中)

- verdict=REQUEST_CHANGES,blockers=2,should_fix=2(自动重试:attempt1/2 503→attempt3 命中)
- Findings(全部核实成立):
  1. **[blocker] ③ unknown 仍矛盾**:R6 只改了 design+verify,`implement.md:35` 触发契约仍写"high-risk 才启用"。→ 三处对齐为 `flutter && {high,unknown}`。
  2. **[blocker] ② 回落太宽**:"无包则回落现状"会让 full 链下**声明却非法/缺失**的 design_package 静默回落 `design.md`(`_gate_artifacts:1645`),defeat SSOT。gate 自身对此 fail-closed(`:1307-1314`)。→ helper 契约 `collect_review_artifacts -> entries|fatal`:仅 light/本就无包才回落;声明却非法/缺失→返非零不 spawn + fail-closed 用例。
  3. **[SF] P0 验收过宽**:P0 ② 只能否决与**已有** SSOT 行冲突,elicit 新负向不变量是 P1 ④。→ 收窄 prd 验收 + goal 注 P0+P1 合力。
  4. **[SF] sync:guru:check 只提未排期**:命令不存在。→ implement P0 加"新增 sync:guru:check(temp 比对、exit≠0)"步。
- 处置:7 处全部修入。
- Next:Round 8 复核(自动重试循环)。

## Round 8(代理曾持续 ~34min down;loop8 全失败,loop8b attempt1 命中)

- 代理状态:loop8 6 次全 503(每次 ~5min 读完文件、出 verdict 时 503,12:08–12:42);loop8b attempt1 立即命中(12:44 恢复)。按用户"不因代理停"持续熬过。
- verdict=REQUEST_CHANGES,blockers=0(**2 blocker 已清**),should_fix=1,nice_to_have=1
- Findings(核实成立):
  1. **[SF] ③ 风险触发仍太窄**:只读 task-level `_risk_level`(`:1705-1730`),标 `risk_level=low` 的高风险跨层 slice 仍绕过;与上游 §4.5.8/§4.5.9(共享 `guru_risk.py`、`slice_packet.risk>task`、路径/关键词/跨层信号、确定性 override low)不一致。→ ③ 触发改用共享 `guru_risk.py` + 全信号 + 确定性 override task low + d3 测试。
  2. **[nice] prd Brainstorm Evidence 遗留文案**:"Open questions: 见下开放决策" 但下方已是"已确认决策"。→ 改 "none — 决策已确认"。
- 处置:2 条全部修入。
- Next:Round 9 复核(自动重试循环)。轨迹:R1(1B4SF)→R4(0B3SF)→R6(1B2SF)→R7(2B2SF)→R8(0B1SF1N),收敛中。

## Round 9(loop attempt1 命中)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=2,nice_to_have=2
- Findings(核实成立):
  1. **[SF] ③ guru_risk 契约不具体**:R8 加了信号集但没定 packet 读取/多 packet/target_paths 解析/关键词/层组/reviewer-approved-low 的具体契约。→ ③ 加"输入契约"子步,精确点引用上游报告 §4.2/§4.5.2/§4.5.8/§4.5.9(勿重发明)+ 测试(缺/非法/多 packet、无 target_paths、仅 dirty、packet.risk override)。
  2. **[SF] apply.sh 未收编 guru_risk.py**:新 sibling 模块须进拷贝清单(`:223-229`)+ echo(`:230`)+ ast.parse 自检(`:664-669`)+ import 冒烟,否则装后缺模块(false green)。→ 加一等 checklist 项 + import smoke 加 guru_risk。
  3. **[nice] design 两处引用**:digest 命名空间应为 `_namespaced_key:1591-1601`/`:1622-1630`;回落为 `_gate_artifacts:1645-1646`。→ 纠正。
  4. **[nice] 留痕文件名不一致**:implement `codex-review-p0.txt` vs adversarial-review `codex-plan-review-p0.txt`。→ 统一 `codex-review-p{0,1}.txt`。
- 处置:4 条全部修入。
- Next:Round 10 复核(自动重试循环)。

## Round 10 + 主动自审(用户质疑"为何这么多轮")

- **根因复盘**:多轮主因是我**边修边给 ②/③ 加具体性 → 新断言 → 下轮被审**的级联,叠加 R7 一次跨文档没改全。故本轮先做**主动自审**(通读三文档,补 5 处传导遗漏:design:48 / implement ast.parse / prd 双源 / prd ② 前置 / prd ③ fail-closed),再并入 R10。
- R10 verdict=REQUEST_CHANGES,blockers=2,should_fix=1(审的是自审前版本,均成立):
  1. **[blocker] ③ 依赖 packet/target_paths/--slice 但无生产者+CLI**:多 packet 无法指定、无 packet 时 fail-closed 卡死。→ **③ P0 重定为无 packet 依赖**(task.json + git-diff 跨层 + unknown fail-closed);packet 基精细风险(slice_packet.risk/--slice/target_paths)**随 P1 ④ 落地**(引用报告 §4.2/§4.5.2/§4.6.1)。
  2. **[blocker] ⑤ 缩成两字段不足以阻断 omission**:须完整 schema(review_target/provider/deterministic_checks/dirty_scope/invariant_coverage + `guru_review_record.py` 共享 writer)。→ ⑤ 扩为报告 §4.4 完整 schema,注明依赖 ④。
  3. **[SF] 通用验证把 step3 的 guru_risk import 提前成每步 gate**。→ 验证分阶段(step1/2 不含 guru_risk;step3+ 加;step5+ 加 guru_review_record)。
- 处置:R10 3 条 + 自审 5 处全部修入;P0 自包含、P1 承载 packet/record 机制。
- Next:Round 11 复核(自动重试循环)。

## Round 11(大重构后)

- verdict=REQUEST_CHANGES,blockers=2,should_fix=3(均成立;含我两处修不彻底)
- Findings:
  1. **[blocker] temp smoke 仍跑不通**:`apply.sh` 还校验 `task_utils.py` 含 `run_blocking_task_hooks`(`:689-701`),裸 mkdir .trellis 不够。→ 真 `trellis init` + 断言 apply.sh exit0。
  2. **[blocker] approved-low 无 schema**:裸 `risk_level=low` 仍绕过。→ 定 `guru_risk:{level,reviewer_approved,approved_by,approved_at,evidence}`,裸 low 不算 true-low + 测试。
  3. **[SF] design:9 兼容行矛盾**:仍写"high-risk 触发",与 unknown fail-closed 冲突。→ 改 `flutter&&(high|unknown|跨层)` + blast-radius rollout 注。
  4. **[SF] 跨层信号漏 untracked**:`git diff` 漏新建文件。→ 用 `git status --porcelain=v1 -z`(staged/unstaged/renamed/deleted/untracked)+ untracked 测试。
  5. **[SF] adversarial-review.md 门标准不一致**:"nice 可保留" vs prompt"零任何严重度"。→ 明确 deliberate `0B+0SF`、nice 非阻断。
- 处置:5 条全部彻底修入(③ 的绕过路径 unknown/裸low/approved-low-schema/untracked 全堵)。
- Next:Round 12 复核。轨迹(新代码):…R8(0B1SF1N)→R9(0B2SF2N)→R10(2B1SF)→R11(2B3SF);③ 反绕过持续硬化。

## Round 12(用户质疑后,改用穷举式扫净)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=4,nice_to_have=1(均成立,多为我的 partial-fix 残留)
- Findings:
  1. **[SF] §4.x 锚点指错文件**:§4.2/§4.4/§4.5.8… 在 `problem-report-and-solution.md`,**不在**诊断文件;codex 打开诊断找不到。→ 7 处锚点全改指向 `problem-report-and-solution.md`(全路径)。
  2. **[SF] design:34 触发又矛盾**:仍写"仅高风险触发"。→ 统一为 `flutter&&(high|unknown|跨层)`。
  3. **[SF] `trellis init "$tmp"` 非 CLI 形态**:init 无 positional、需 -y。→ `(cd "$tmp" && trellis init -y)` + guru 版 core 说明。
  4. **[SF] sync:guru:check 未落到 package.json**。→ 明确改 package.json + 实现 --check + 测试。
  5. **[nice] ② fail-closed 措辞**:build_run_plan 返 RunPlan、错误靠 GuruSupervisionError。→ 改措辞,勿改其返回类型。
- 处置:**穷举 grep 三文档,12 处一次改净**(锚点/触发/命令/措辞复发类全清)。
- Next:Round 13(用户已同意作为决定轮:0B+0SF 即过闸;否则按实质完成收尾)。

## Round 13(决定轮)

- verdict=REQUEST_CHANGES,blockers=0,should_fix=3(均成立,深层落地/安全细节):
  1. **[SF] ② 循环 import 风险**:guru_supervise 已 import guru_gate;若 gate 抛 GuruSupervisionError 即循环。→ gate 暴露 `collect_gate_artifacts`+`GateArtifactError`,supervise 的 `collect_review_artifacts` 包装;加循环 import 冒烟。
  2. **[SF] ③ git 失败未定义**:git 不可用/非 git repo 时 porcelain 行为未定。→ `unknown_scan_failed` fail-closed,low 不绕过 + 测试。
  3. **[SF] nice 门策略**:门=0B+0SF 与 prompt"零任何严重度"不一致。→ prd/implement/adversarial-review 明确 deliberate 0B+0SF、nice=accepted risk。
- 处置:3 条全部修入。

## 最终处置:planning 实质完成(用户 2026-06-29 确认 R13 为决定轮)

- **结论:planning 实质完成。** 13 轮 codex 对抗 + 1 次穷举自审;最终 3 轮(R8/R12/R13)**0 blocker**;findings 从核心逻辑收敛到深层实现安全细节(循环 import / git 失败 fail-closed / nice 门策略),均已修入。
- 关于"为何多轮":主因 (a) ③ 是准安全闸,逐一堵绕过(unknown/裸low/approved-low-schema/untracked/git-failure)是真硬化;(b) 我多次 partial-fix(改一处漏其它),最后用穷举 grep 根治;(c) codex 按实现规格精度审 planning 文档。
- **未做 R14**:R13 的 3 处修复已应用但未经 codex 再确认;按诊断同例,残留边界由**实现期那道 codex 闸**(`adversarial-review.md` 规程,implement 收口强制)继续兜。
- 产物:prd.md / design.md / implement.md / adversarial-review.md + `codex-plan-review-rounds.md`;P0 自包含、P1 承载 packet/record 机制、③ 反绕过多层硬化。
- 待办:用户批准后 `task.py start` 进 P0 实现。

---

# 实现期 P0 codex 对抗审查（opposite-provider,read-only/high,按 adversarial-review.md）

代码 diff 全文经 codex 逐轮审,findings 全文留痕见 `codex-review-p0.txt`。

| 轮 | verdict | 处置 commit | 要点 |
|----|---------|-------------|------|
| R1 | REQUEST_CHANGES 2B+2SF | `61cf1292` | B1 implement-check 强制 non-advisory;B2 full 链缺 design_package fail-closed;SF3 db/bloc 边界化+_is_scannable 过滤;SF4 补回归 |
| R2 | REQUEST_CHANGES 1B+2SF | `8c54c46e` | B1 task_risk_level high 全局优先(防 nested low_risk 吞 high);SF2 provider 不翻转(_load_config adversarial=False);SF3 collect 包骨架 README/design-main/chapters fail-closed |
| R3 | REQUEST_CHANGES 0B+1SF | `c4e81577` | SF1 sync:guru:check 接入 prepublishOnly + ci.yml(+`guru-template/**` paths) + publish.yml |
| **R4** | **APPROVE 0B+0SF+0nice** | — | findings: none;逐项 A–H 核验通过 |

- **过闸**:达 adversarial-review.md 标准(0B+0SF;nice 本就非阻断,本轮 0nice)。
- codex **每轮逐条经我读真实代码核实后采纳**(非盲信);4 轮均确认**无 OCR 必选依赖**(硬约束①)、**无循环 import**、**测试非自我印证**([[test-self-confirmation-trap]])。
- 期间独立测试额外抓出并修一个**真 bug**:`scan_paths` 默认 `git status --porcelain` 把未跟踪目录折叠成 `lib/`、丢失 `lib/data/x_datasource.dart` 层级 → 跨层/storage 漏判;加 `-uall` 修复(由 ③d3a/d3a2 独立构造用例抓出)。
- 关于"为何 8 条":③ 是准安全闸,逐一堵绕过(advisory-skip/provider 翻转/nested-low 吞 high/包骨架静默过滤)+ drift gate 接入真实闸,是真硬化;R1→R4 单调收敛(2B→1B→0B→APPROVE)。
