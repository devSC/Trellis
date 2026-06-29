# Guru 实现期审查强化:逐行密度 + SSOT 接地 + 独立对抗 check

## Goal
让 guru 系**实现期审查自身**达到"逐行密度 + SSOT 接地 + 独立对抗 check",能在实现 review 阶段拦下 Himora 式跨层负向/排除语义缺陷——**不引入 OCR 作为依赖或完成条件**。(完整拦下靠 P0+P1 合力:P0 ② 否决与**已有** SSOT 冲突,P1 ④ 系统性 elicit **新**负向不变量。)

来源:`.trellis/tasks/06-28-guru-review-governance-report/guru-skill-optimization-diagnosis.md`(经 codex 对抗审查 R1–R13、核心 R11 背书;证据见该任务 `evidence/`)。

## Requirements(五条优化,flutter-first P0)
- **① 实现 review 逐行数据语义密度**:`flutter-implementation-guru-review` 增加对改动行的数据语义逐行核查(排序键/解码/身份/merge 集合成员/断言可证伪性),保留既有 canonical/合同核对(`SKILL.md:17/:23/:50`)。
- **② SSOT 否决闸 + 为 implement/check 显式加载正式 requirement/design 包**:复用 gate 安全枚举器(**前置:先令 design_package 也 repo-root-safe**;full 链下声明却非法/缺失的包 fail-closed;带 repo-root 围栏 / canonical_excludes fail-closed / 命名空间键),**不另起第二套 package-walk**;reviewer 建议与 SSOT 行级约束冲突即否决。
- **③ 实现 Gate 独立对抗 check**:`run_implement_check` 提供独立实现期 review 模式——check 用对立 provider/新上下文、**对抗失败阻断(非 advisory)**、与 implement worker 隔离;堵住"跳过 implement 误推进""独立 check advisory rc0 放过";触发经共享 `guru_risk.py`(**unknown / 标 low 但路径跨层均 fail-closed 启用**)。
- **④ REQ-UC×BHV 追溯矩阵扩负向/排除维度**:requirement/overview/detail skill 在既有矩阵(`guru_gate.py build_trace:799`)上挂"must-not / 保留-排除 / 成功路径排除"维度 + 测试映射;对齐 `requirement-doc-standard` SSOT,勿另起。
- **⑤ 负向测试强制 + verdict 结构化解析(依赖 ④)**:omission/exclusion/non-append 类不变量强制负向测试;implement-check verdict 改**完整结构化 schema**(`../06-28-guru-review-governance-report/problem-report-and-solution.md` §4.4:review_result/route_class/review_target/review_provider/deterministic_checks/dirty_scope/invariant_coverage + `guru_review_record.py` 共享校验),clean 须各取通过值否则 MALFORMED exit2;取代 route 全文搜索 + clean 子串。

## 双源/部署约束
- 改 `guru-template/**` 后须 `pnpm -C packages/cli sync:guru` 同步 bundled 镜像。
- 新增/改动 verify 脚本须 `apply.sh` 三处清单(拷贝/状态 echo/ast.parse 自检)+ import 冒烟同步(supervise 现已硬 import guru_gate,本任务再加 `guru_risk.py`,sibling-import 风险 live)。

## Acceptance Criteria
- [ ] ① 实现 review skill 对改动数据层有逐行语义核查口径。
- [ ] ② implement/check worker 拿到正式 requirement/design 包(经安全枚举器);**reviewer 建议/改动与正式包中已存在的 SSOT 行级约束冲突时可否决**(P0 ② 不声称独力拦下"未写出"的负向缺陷——系统性 elicit/编码新负向不变量属 P1 ④)。
- [ ] ③ 高风险 implement-check 走独立对抗 check(对立 provider、失败阻断),"审查者≠实现者"机器可判;**unknown-risk flutter fail-closed 启用(缺 risk 元数据不得绕过)**。
- [ ] ④ detail/overview/requirement 产出含负向/排除不变量 + 成功路径排除测试,挂在 REQ-UC×BHV 矩阵。
- [ ] ⑤ omission 类不变量有负向测试;implement-check verdict 为**完整结构化 schema**(review_result+route_class+review_target+review_provider+deterministic_checks+dirty_scope+invariant_coverage,clean 须各取通过值否则 MALFORMED exit2,经 `guru_review_record.py` 共享校验);依赖 ④。
- [ ] 既有 gate/supervise 测试通过 + 新增回归;`sync:guru` 后无漂移;变更经 codex 对抗审查通过。
- [ ] 全程无 OCR 依赖或完成条件。
- [ ] **审查门 = 0 blocker + 0 should-fix(deliberate)**;残留 nice-to-have 记为 accepted risk,**不计入"零问题"声明**(见 `adversarial-review.md`)。

## 非目标
- 不引入/不依赖 OCR(`ocr` CLI);OCR 至多 optional 补充、其建议从属 SSOT。
- 不改 Himora 产品代码。
- go/ios/h5 不在 P0(后续另开);不替代人工确认 Gate。

## Brainstorm Evidence
- Skill loaded: 本任务规划基于上游诊断(已含 5 个并行审查者 + codex R1–R13 对抗结论)。
- Repository evidence inspected: guru_supervise.py / guru_gate.py(含 +770 REQ-UC×BHV)/ flutter skills / detail·gate 合同 / apply.sh / sync-guru-template.js,均经真实代码核验(见诊断 file:line)。
- Domain/terminology triggers: OCR = open-code-review(外部审查器,非依赖);REQ-UC×BHV 追溯矩阵;SSOT = requirement/design 正式包。
- Current code vs user intent conflicts: 实现 Gate 无 first-class 对抗;正式包不注入 implement/check;verdict 解析脆弱——均为本任务要解的现状。
- Product decisions confirmed: OCR 不得为必选依赖(用户两次确认);诊断按"实质完成"收尾(用户确认)。
- Open product/scope/risk questions: none — 分期/结构/平台/OCR 决策已确认(见下「已确认决策」)。

## 已确认决策(2026-06-29)
- **分期**:单任务、phased——**P0 = ①②③(OCR 等效核心)**,**P1 = ④⑤(上游不变量 + 测试/解析)**。
- **结构**:单任务(phased implement.md),非父子拆分(②③⑤ 共改 `guru_supervise.py`,避免子任务冲突)。
- **平台**:**P0 仅 flutter**(go/ios/h5 后续另开)。
- **OCR**:不作依赖/完成条件(用户两次确认)。
