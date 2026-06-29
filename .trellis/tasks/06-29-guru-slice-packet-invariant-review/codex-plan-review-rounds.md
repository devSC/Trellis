# P1 planning codex 对抗审查轮次（opposite-provider,read-only/high)

按 `adversarial-review.md` 规程从 scratchpad 跑;每轮逐条**读真实代码/SSOT 核实后采纳**。过闸标准 `blockers=0 且 should_fix=0`。

## 收敛轨迹

| 轮 | verdict | 主题 |
|----|---------|------|
| R1 | 3B+3SF | 分期顺序不可执行 / append 拒绝-vs-写 jsonl 矛盾 / schema risk 必填冲突 / scan_dirty 复用 / 生产者统一 / packet failure canonical |
| R2 | 3B+4SF | provider gating 缺口 / **prd 分期残留(partial-fix)** / 生产者残留 / 三分支伪代码 / PACKET_MISSING 字段策略 / scope git diff 残留 |
| R3 | 1B+4SF | **deterministic supervisor hard Gate 纳入 P1** / review_target 入 jsonl / `_p0_` 抽取防递归 / semantic_review_provider schema / aggregate 函数 |
| R4 | 2B+3SF | deterministic **每轮**(非循环前)/ packet 注入 worker / risk unknown 口径 / **Brainstorm 残留(partial-fix)** / 收口验收 BHV-008 |
| R5 | 0B+2SF+1n | manual/ocr required **保守禁(PACKET_INVALID)** / deterministic_results 审计 / message 字段 |
| R6 | 1B+0SF | **provider 残留矛盾(partial-fix:改 schema 漏 normalize)** |
| R7 | 1B+1SF | **上游 SSOT(06-28)残留旧句(用户决定改 SSOT 对齐)** / supplemental append 语义 |
| R8 | 0B+1SF+1n | packet.risk=low slice 级 override / 命名统一 validate_verdict_values |
| R9 | 2B+0SF | packet `invariants[]`/`target_paths[]` 非空(防 fail-open) / per-invariant 机器合同(evidence/reason 字段) |
| **R10** | **APPROVE 0B+0SF+0n** | finding:none |

## 关键决策留痕

- **deterministic supervisor-side hard Gate**(R3→R4):SSOT §4.1/§4.4 明确是 P1 落地目标,纳入本 task;每轮 implement 后绑定本轮 diff 执行,clean 须 supervisor + worker 双过。
- **manual/ocr_optional 不作 required**(R5→R7):第一版保守禁(`PACKET_INVALID`),仅 supplemental 补充审计;verify-record 路径 deferred;**强化"无 OCR 必选"硬约束**。用户 2026-06-29 决定改上游 SSOT problem-report(§4.6.7/§5/§6/§7)对齐。
- **packet.risk=low 是 slice 级 override**(R8):SSOT §4.5.9,packet low 不被 task/git 抬高;仅无 packet/unknown 回落 P0。
- **packet 非空 + per-invariant 机器合同**(R9):invariants/target_paths 非空防 fail-open;invariant_status/evidence/reason 可解析字段防"信 worker 自报"。

## 教训（写给后续 + 自省）

- **partial-fix cascade 反复(R2/R4/R6/R8 残留)**:改一个**概念**时它散落多文档 × 多抽象层(schema/normalize/verify/BHV/架构图/SSOT),改"定义处"漏"使用处"。根治:改概念后 `grep 概念关键词`穷举**所有**出现逐一对齐 + 正反向 grep 双重自审,**不靠通读印象**([[test-self-confirmation-trap]] 同源)。
- packet-centric 机制**机器合同密集**(schema/invariant 字段/聚合/deterministic/provider/scope),每字段都有精确 fail-open/closed 语义,故轮数多于 P0;每条 finding 均成立(真 fail-open / 真返工风险),非噪声。
- 改上游 SSOT(06-28)是 R7 的范围决策,经用户 2026-06-29 确认。

## 留痕

R1-R10 verdict + findings 全文存 `codex-review-p1plan.txt`;本表为索引。过闸:R10 APPROVE(0B+0SF+0nice)。

---

# P1 **实现** codex 对抗审查轮次（opposite-provider,read-only/high)

planning 过闸(R10 APPROVE)+ P1a-e 实现(commit 744dd216/876ba1dd/ec5c340a/7430f525/c25fb900)完成后,再对**实现代码**跑同规程对抗审查。过闸 `blockers=0 且 should_fix=0`。

## 收敛轨迹

| 轮 | verdict | 主题 |
|----|---------|------|
| R1 | 3B+3SF+1n | provider gating 漏 manual/ocr/未知+未绑实际 spawn / review_target 未绑当前 slice / deterministic 元素不校验+run traceback / findings+route none 不标 MALFORMED / append 裸 clean 绕过 / risk_reasons·dirty_state.unrelated 元素不校验 / deterministic_results 缺 duration·run_at |
| R2 | 1B+0SF+0n | **R1 七条经 codex 逐条复核全部确认真修 + 硬约束全过**;新 blocker:`_validate_semantic_review_provider` 未类型校验,unhashable provider/ocr 击穿 set membership 抛 TypeError 逃逸 fail-closed |
| R3 | 0B+2SF+2n | R2 blocker 确认修 + 并行 packet 路径核对全过;新 SF:`append_record`/`validate_verdict_values` 未对枚举/verdict **字段值**类型守卫(unhashable 击穿 set membership) |
| R4 | 0B+2SF+0n | R3 确认修;新 SF:`preflight_failure_record`/`aggregate_invariant_coverage` **嵌套结构**(kind/invariant_id/evidence)类型守卫 |
| R5 | 0B+3SF+0n | R4 确认修;新 SF:`validate`/`normalize`/`run_deterministic`/`preflight` **顶层 shape guard**(参数本身非预期类型) |
| R6 独立复审 | 0B+2SF+1n | codex 代理故障期 Claude 独立对抗复审(fallback):嵌套 packet 守卫缺失(**fail-open 风险**)+ provider pin 错位 + required 不消费;均已修/文档化 |
| **R6 codex 终审** | **APPROVE 0B+0SF+0n** | 代理恢复后补做;逐条确认 R5 顶层守卫 + 独立复审 F1(嵌套 packet/fail-open)/F2(pin 收窄)/F3 全部落地;三层守卫 + 硬约束全核对通过。**过闸** |

## R1 findings 与修复（逐条读真实代码核实——7 条全成立,真 fail-open / 防御缺口）

| # | sev | 缺陷 | 修复 |
|---|-----|------|------|
| F1 | B | `normalize` opposite gating 只查 `actual≠impl`,manual/ocr_optional/未知 provider 的 clean 漏判;未绑实际 spawn provider | 层② clean 加 `actual∈_CHANNEL_PROVIDERS{codex,claude}` + `actual==check_provider`(supervise 传 `check_config.provider`)+ 对立要求 fail-closed 默认(`independent_required` 缺省 True;low-risk override 显式 False 放行同 provider 自检,§4.5.9) |
| F2 | B | worker 自报 `review_target` 只校验存在,审错 slice 仍被当前 packet 消费,打穿 packet-centric 绑定 | `normalize` supervisor mode 加 `f.review_target == context.review_target` 校验,不符→MALFORMED |
| F3 | B | `deterministic_checks` 元素不校验,`run_deterministic([123]/[""])` 抛 traceback,不走 PACKET_INVALID、不写 jsonl | `load_packet` 用 `_require_str_list` 校验非空字符串数组 + `run_deterministic` 防御非串/空 argv/shlex error→failed entry 不 traceback |
| F4 | SF | `findings`/`blocked` + `route_class=none` 不标 MALFORMED,jsonl `supervisor_failure=none` 审计语义错 | `validate_verdict_values`(层①)加 route 一致性:clean↔none、findings/blocked↔非none |
| F5 | SF | `append_record`(唯一 writer)允许裸 clean 绕过 normalize 污染 jsonl | `sf=none` 的 record 复跑 `validate_verdict_values`,不过→`ReviewRecordError`;canonical failure record(`sf≠none`)跳过;测试改用规范化/preflight record |
| F6 | SF | `risk_reasons`/`dirty_state.unrelated` 元素不校验,`"cross_layer"` 字符串被静默忽略(不触发 high、不判 INVALID) | `load_packet` 统一 `_require_str_list` 校验 `risk_reasons`/`deterministic_checks`/`dirty_state.unrelated` 为字符串数组 |
| nice | n | `deterministic_results` 缺 design 承诺的 `duration_ms`/`run_at` | `run_deterministic` 每条记 `duration_ms`(monotonic)/`run_at`(ISO)/`stderr_summary` |

回归:新增 `R1-` 测试块 19 项(独立构造、断言可证伪,非自我印证),全套 **282/0**;`sync:guru` 无 drift。

## R2 finding 与修复（R1 七条经 codex 逐条复核全部确认真修 + 硬约束全过)

| # | sev | 缺陷 | 修复 |
|---|-----|------|------|
| R2-F1 | B | `_validate_semantic_review_provider` 未对 provider/ocr 做字符串类型校验,unhashable(list/dict)在 `provider in NON_REQUIRED_PROVIDERS` / `ocr in OCR_VALUES` 抛 `TypeError`,逃逸 packet preflight 的 `ReviewRecordError` 捕获 → 非法 packet traceback 崩溃而非 `PACKET_INVALID` fail-closed | `required` bool 校验后、membership 前加 provider/ocr `isinstance(str)` 校验,非字符串统一 `ReviewRecordError` |

**partial-fix 自审**(本轮主动穷举,印证教训):codex 仅 flag `semantic_review_provider` 一处,我 `grep` 全部 set membership 逐一核左值来源——`_normalize_packet_risk` 已有 `isinstance(str)` 守卫(安全)、verdict 字段经 `parse_verdict_block` 必为 str(安全)、append record 枚举仅消费内部规范化值(codex 复核确认无并行 writer),唯 `semantic_review_provider` 缺守卫已修。

回归:新增 `R2-` 测试 3 项(provider=[]/ocr=[] → `ReviewRecordError`;端到端 `run_implement_check` unhashable provider → exit2 + jsonl `PACKET_INVALID`/route none/repairable false),全套 **285/0**;`sync:guru` 无 drift。

## R3–R5 finding 与修复（同主题:public 入口类型健壮性,三层穷尽 fail-closed）

R2-F1 暴露的是「未校验类型 + set membership → TypeError 逃逸 fail-closed」一类缺陷。R3/R4/R5 codex 逐层深入,
把 `guru_review_record` **所有 public 入口**对任意 Python 对象输入都收敛为 fail-closed(每轮先确认前轮真修 + 硬约束不回退):

| 轮 | 层次 | 缺陷点 | 修复 |
|----|------|--------|------|
| R3 | 字段**值** | `append_record`(review_result/route_class/supervisor_failure)、`validate_verdict_values`(7 字段) unhashable 值击穿 membership | append 加 `isinstance(str)` 守卫;validate 把字段校验收敛为「非空 str」 |
| R4 | **嵌套**结构 | `preflight_failure_record`(kind)、`aggregate_invariant_coverage`(packet/item/id/status/evidence/reason) | kind isinstance str;aggregate 入口形状 + 逐项类型守卫,非预期 → MALFORMED/missing;另补 `parse_verdict_block` 非 str → 空 fields |
| R5 | **顶层**参数 | `validate`/`normalize`(fields/context 非 mapping)、`run_deterministic_checks`(commands 非 list)、`preflight`(candidates 非字符串数组) | 顶层 `isinstance` shape guard:非 mapping→MALFORMED、非 list commands→failed、candidates 非字符串数组→ReviewRecordError |

codex 每轮均确认「真实主路径不受影响」(supervisor 传常量/`load_packet` 已校验/`parse_verdict_block` 产 str),
属 public API defense-in-depth 穷尽;`guru_supervise`/`guru_risk` 的 membership 只消费 `load_packet` 产物 + argparse
受控 args,无外部未校验 JSON 直达。回归累积:R3 +9(294/0)、R4 +8(302/0)、R5 +7(309/0);`sync:guru` 每轮无 drift。

## R6 独立复审（代理故障 fallback)与修复

codex 代理(`127.0.0.1:37123`)在 R6 阶段持续故障(HTTP 000 拒连,非短暂 503)。为不空等,以**独立 Claude agent** 作对抗复审
(明确标注:**非 opposite-provider,codex R6 终审待代理恢复补做**;此为 fallback 不替代 codex gate)。verdict=ISSUES_FOUND
(0 blocker),逐条实证(跑真实代码)后修复:

| # | sev | 缺陷(实证) | 修复 |
|---|-----|------|------|
| F1 | should_fix | `normalize_review_record` 第三层(嵌套 packet)守卫缺失:R5 只守 fields/context 顶层,`context["packet"]` / `packet["semantic_review_provider"]` 非 dict → AttributeError;且若天真 `or {}` 回落,`aggregate([],{})==all_passed` 会产出**零 invariant 核验的 clean(真 fail-open)** | clean 分支前置 packet dict + **非空 invariants** + srp dict 守卫,malformed 一律 blocked(**绝不 `or {}` 回落**,否则重新引入 fail-open) |
| F2 | should_fix(fail-closed) | 具体 provider pin 错位:supervisor 总 spawn opposite(`check_config=_opposite_provider`),从不读 `semantic_review_provider.provider`,故 pin=codex/claude 只在巧合==opposite 时生效、否则永久 MALFORMED(pin 实际失效/误导) | normalize 收窄:仅 `provider=opposite` 作 required clean,具体 pin 第一版 deferred(同 manual/ocr);docstring 文档化 |
| F3 | nice | `required` 字段被校验却不被 gating 消费(独立性由 risk / §4.5.9 low-risk override 决定) | docstring 文档化:`required` 第一版仅约束 provider 类别、不作独立性下限 |

独立复审同时确认:R1–R5 核心 gating **无 fail-open / off-by-one / 条件写反**,三层守卫(除 F1 嵌套层)全闭,回归 0,
硬约束全守(OCR 非必选 / fail-closed / 单 writer / packet 非空 / 无循环 import)。新增 `R6-` 测试 6 项(malformed packet /
空 invariants / srp 非 dict / 具体 pin → 全 MALFORMED 不 traceback;补独立复审指出的 pin 分支测试缺口),全套 **314/0**;`sync:guru` 无 drift。
