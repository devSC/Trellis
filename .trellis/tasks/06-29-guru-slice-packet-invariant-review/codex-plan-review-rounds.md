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
