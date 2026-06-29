# Design — Guru 实现期审查强化

分期:**P0 = ①②③(OCR 等效核心)**,**P1 = ④⑤**。平台:**flutter-only**。
深层代码分析与 file:line 见 `../06-28-guru-review-governance-report/guru-skill-optimization-diagnosis.md`。

## 0. 边界与兼容性
- 改 `guru-template/**`(skills + `overlay/verify/*.py` + flutter 合同),改后 `pnpm -C packages/cli sync:guru` 同步镜像。
- `guru_supervise.py` 现已 module-load `from guru_gate import requirements_digest`;新增脚本/依赖须扩 `apply.sh` 拷贝清单 + ast.parse 自检 + `-B` import 冒烟。
- 兼容/rollout:不破坏现有 `run_action`/`run_implement_check` 既有路径;新增能力触发 = `flutter && (high | unknown | 确定性跨层/storage 信号)`,非 flutter + 经校验的 reviewer-approved-low flutter 保持旧行为。**blast radius 注意:所有无 risk 元数据的 flutter 任务都会被 unknown fail-closed 新纳入门(非仅 high-risk),需接受或补合法 approved-low 元数据**。
- 不引入 `ocr` 依赖;OCR 仅 optional、从属 SSOT。

## P0 技术设计

### ① 实现 review 逐行数据语义密度
- 文件:`overlay/agents-skills/flutter-implementation-guru-review/SKILL.md`。
- 现状:有 D1 合同逐项核对(`:17`)、D4 证据(`:23`)、只审改动面(`:50`),**缺改动行数据语义逐行核查**。
- 改:在 D1/D4 之外新增一节"数据层逐行核查"——对改动行强制核:排序键(同值/缺 attempts/稳定性)、JSON 解码健壮性(string-or-number/缺字段)、attempt/media 身份匹配(同 id 碰撞)、merge **集合成员**(保留 vs 可见分叉)、测试断言**可证伪性**。保留既有 canonical/合同核对,不删。
- 契约:输出仍走 `flutter-implementation-guru-review/SKILL.md` 的 `## 输出 / 机器可读收口字段`(`:37`,`review_result`+`route_class`);本节是审查口径增强,不改输出 schema。

### ② SSOT 否决闸 + 为 implement/check 显式加载正式包
- 文件:`overlay/verify/guru_supervise.py`(`build_run_plan`)、`flutter-implementation-guru-review/SKILL.md`、必要时 `guru_gate.py`(导出安全枚举器)。
- 现状:`build_run_plan` 对所有 action 只注入 skill + 本地 `prd/design/implement.md`(`:466-473`);正式 `requirement_package`/`design_package` 是 gate 概念(`_requirement_package_dir:497`/`_package_dir:470`/`_gate_artifacts:1604`),**不注入** implement/check worker。
- ⚠ **前置(codex blocker,必做在前)**:当前 `_gate_artifacts` 只对 requirement_package 传 repo_root;**design_package 经 `_package_dir`(`:470-494`,`repo_root=os.getcwd()` `:487`)解析、返回相对路径**,`_gate_artifacts:1620` 调它也没传 repo_root——supervise 在 cwd≠repo-root(`--root`)下注入会指错/丢失。故必须**先**重构 `_package_dir(task_dir, repo_root=None)`(及所有调用方)或新增公共 helper,使 **requirement_package 与 design_package 都按 `config.root` 解析为绝对、fenced 路径**,保留 `_gate_artifacts` digest/namespacing 语义,并补 **cwd≠repo-root 回归测试**。
- 改:(a) 在 `guru_gate.py` 暴露 **gate-local `collect_gate_artifacts(...) -> list[ArtifactEntry]`(失败抛 gate-local `GateArtifactError`;`guru_gate` **不得**反向 import `guru_supervise` 的异常,防循环 import——supervise 已在 module-load import guru_gate)**,基于 repo-root-safe 后的 `_gate_artifacts(task_dir,"detail",config.root)`(repo-root 围栏、canonical_excludes fail-closed `:591-668`、package fail-closed `:1239`、命名空间键 `_namespaced_key:1591-1601`/`:1622-1630`);(b) `build_run_plan` 对 flutter implement/check 调用它注入正式包;**不得另起第二套 package-walk**。(c) review skill 增加"SSOT 否决"口径:reviewer 建议与正式包行级约束冲突即否决。
- 契约/回滚(fail-closed 边界):公共 helper 定为 `collect_review_artifacts(task_dir, gate, repo_root) -> entries | fatal`。**仅 light 链或设计上本就无正式包才回落 task-local `design.md`**;若 `guru_chain=full` 且 `design_package` 声明却非法/缺失(`_package_dir` 返 None `:470-494`、gate 对此 fail-closed `:1307-1314`),或声明的 `requirement_package` 非法/缺失,**`collect_review_artifacts`(归 `guru_supervise.py`,调 gate 的 `collect_gate_artifacts`、把 `GateArtifactError` 包成 `GuruSupervisionError`)在 spawn 前返回非零(`main()` 模式;`build_run_plan` 仍返回 `RunPlan`,勿改返回类型)**——不得像 `_gate_artifacts:1645-1646` 那样静默回落本地 docs(`build_run_plan` 的 `_existing_paths`(`:265-267`/`:468-481`)还会过滤缺失文件,更易掩盖)。

### ③ 实现 Gate 独立对抗 check
- 文件:`overlay/verify/guru_supervise.py`(`run_implement_check`)。
- 现状:implement/check 共用同一 `config`/provider(`:1020-1038`/`:507-518`/`:407-418`);对抗旗标/prompt 只对 `{requirements,overview,detail}`(`:48`/`:531-537`/`:589-598`);对抗失败→`_skip_adversarial` advisory rc0(`:830-841`/`:844-924`);`run_implement_check` 无 `adversarial_enabled` 守卫(`:968-977`),三情形见诊断 ③。
- **触发契约(P0,对齐 `../06-28-guru-review-governance-report/problem-report-and-solution.md` §4.5.8/§4.5.9,但 P0 不引入 packet 生产者)**:新增/导出共享 `guru_risk.py`(`guru_gate._risk_level` 改兼容代理、`guru_supervise` import 同一 helper)。**P0 信号(无需 packet)**:① task.json risk(经 guru_risk.py,`:1705-1730`);② supervise 用 **`git status --porcelain=v1 -z`** 收集 staged/unstaged/renamed/deleted/**untracked** 路径(新建文件常未 tracked,`git diff` 会漏),归一后做 **跨层(datasource/repository/cache/controller)/storage 关键词检测**(用 `git -C config.root`;**git 不可用 / config.root 非 git worktree / porcelain 退出非零或不可解码 → `unknown_scan_failed`:禁 true-low 降级、fail-closed 启用独立 check**)。**true-low 定义**:仅当路径扫描无跨层信号 **且** task.json 含合法 approval(`guru_risk: {level: low, reviewer_approved: true, approved_by, approved_at, evidence}`)才算;**裸 `risk_level=low` 不算 true-low**。`config.platform=="flutter"` 下:high | unknown | 命中跨层信号 → 启用独立阻断 check(**fail-closed**:缺元数据 / 裸 low / 标 low 但路径跨层均不得绕过);true-low / 非 flutter → 旧行为。
- **packet 基的更精风险(`slice_packet.risk`>task、`target_paths` 来自 implement.md 计划节、`implement-check --slice <unit>` 选择、单 packet auto-select / 多 packet 无 `--slice` 硬停)依赖 packet 生产者(writing-skill/trace 合同),随 P1 ④ 的 packet/invariant 机制一并落地,不在 P0**——契约见 `../06-28-guru-review-governance-report/problem-report-and-solution.md` §4.2/§4.5.2/§4.6.1。
- 改:新增**独立 implementation-check-review 模式**——为 check 构造独立 review config(**失败阻断、非 advisory**;`provider=_opposite_provider(implement provider)`;填对抗 model/reasoning),与 implement worker 隔离;"审查者≠实现者"机器可判(记录 implement vs check 的 provider/worker/run_id 比对)。堵住两条:对抗失败被 `_skip_adversarial` 转 advisory rc0(`:830-841` / `_execute_plan:844-924`;独立 `check --adversarial` 经 `run_action:939-965`)、以及 `run_implement_check` 接受 `_execute_plan` rc0 即推进(`:1027-1040`,跳过 implement 误推进)。
- **disabled-adversarial 硬契约**:高风险 flutter implement-check 下,若独立 check 必需但 `guru.supervision.adversarial_enabled=false` / 无法 spawn 对立 provider,**返回非零、不推进**——不得退化成 `_skip_adversarial` 的 rc0 advisory 跳过(否则配置一关 gate 即失效)。
- 兼容:新模式触发 = `flutter && (high | unknown | 确定性跨层/storage 信号)`;合法 approved-low + 无跨层信号、非 flutter → 旧行为(与 §0 兼容/rollout 及触发契约口径一致)。

## P1 技术设计

### ④ REQ-UC×BHV 追溯矩阵扩负向/排除维度
- 文件:requirement/overview/detail skill + `detail-structure-single-source.md` + 视情 `guru_gate.py build_trace`(`:799`)/`render_matrix`(`:853`)。
- 改:在既有正向矩阵(BHV×REQ-UC×owner×UNIT×测试×切片)上挂**负向列**:"X 须保留但不得出现在 Y""权威集 vs 存储集分叉""成功路径上的排除";测试映射从"成功 + 全部失败路径"补"成功路径排除"。对齐 `requirement-doc-standard` SSOT,**勿另起结构**。

### ⑤ 负向测试强制 + verdict 结构化解析(完整 gating schema,依赖 ④)
- 文件:`flutter-implementation-guru-review/SKILL.md` + `overlay/verify/guru_supervise.py`(`_route_from_output:345-353` 及 implement-check 解析)+ 新增 `guru_review_record.py`(共享 schema/writer)。
- 改:(a) omission/exclusion/non-append 类不变量**强制负向测试**(正向 enrichment 测试不达标);(b) implement-check verdict 改**完整结构化 header/JSON**——不止 review_result+route_class,而是 `../06-28-guru-review-governance-report/problem-report-and-solution.md` §4.4 全套机检收口:`review_target`、`review_provider`、`deterministic_checks`、`dirty_scope`、`invariant_coverage`(+ record 的 `supervisor_failure`/`repairable`);**clean 须携带且各取通过值**(deterministic_checks=passed、dirty_scope∈{clean,isolated}、invariant_coverage=all_passed、validation_summary),缺字段/取值冲突/重复字段统一 `MALFORMED_REVIEW_OUTPUT` exit2;取代 route 全文搜索 + clean 精确子串。requirements 路径不强加(clean=`review_result=clean/requirements-ready`、blocker=`route_class=REQ_BLOCKER`)。
- (c) 新增 `guru_review_record.py` 共享校验/writer:supervisor parse-time gating 与 manual/optional-OCR append 共用同一 schema(勿两套);随 `apply.sh` 收编(拷贝/echo/ast.parse/import 冒烟,与 guru_risk 同)。schema 精确点以 `../06-28-guru-review-governance-report/problem-report-and-solution.md` §4.4/§4.6.7 为准,勿重发明。
- **依赖**:`invariant_coverage` 需 ④ 的负向/排除 invariants 才有意义,故 P1 内顺序为 ④→⑤。

## 风险与回滚
- 每条优化独立可回滚(git revert 对应改动 + sync:guru)。
- 高风险:②③ 改 `guru_supervise.py` 控制流——必须配套回归测试(run_tests.sh 扩 implement-check 双 provider / skip 阻断 / 结构化解析)。
- 部署回归:apply.sh 拷贝清单/状态 echo/ast.parse 自检/import 冒烟须收编**新增 `guru_risk.py`**,覆盖 guru_risk↔guru_gate↔guru_supervise 互依。
- 交付前经 codex opposite-provider 对抗审查(memory 规则)。
