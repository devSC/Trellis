# Implement — Guru 实现期审查强化(分期 P0→P1,flutter-only)

机器可读细节见 `design.md`;代码 file:line 见 `../06-28-guru-review-governance-report/guru-skill-optimization-diagnosis.md`。
约定:每步改完先本地验证 → 过 review gate;**P0 全绿并经 codex 对抗审查通过后再进 P1**。

## 通用验证命令
```bash
# 语法/导入(模板目录,勿留 __pycache__:用 ast.parse / -B)
# 步骤1/2(guru_risk.py 尚未建):只 ast.parse guru_supervise.py + guru_gate.py
python3 -c "import ast,sys;[ast.parse(open(f,encoding='utf-8').read()) for f in sys.argv[1:]]" guru-template/overlay/verify/guru_supervise.py guru-template/overlay/verify/guru_gate.py
# 步骤3+(guru_risk.py 已建后):上面 ast.parse 与下面 import 冒烟再加 guru_risk.py;步骤5+ 再加 guru_review_record.py
PYTHONDONTWRITEBYTECODE=1 bash guru-template/overlay/verify/tests/run_tests.sh
# 同步镜像 + 漂移检查(真 gate:sync 后镜像须 == 源)
pnpm -C packages/cli sync:guru
git diff --stat -- packages/cli/src/templates/guru   # 仅人工速览,非 gate(--stat 永远 exit0)
# 真 drift gate(需新增):pnpm -C packages/cli sync:guru:check —— sync 到临时目录、与 src/templates/guru 逐文件比对(含 workflow 文件名映射与 excludes),有差异 exit≠0
# 安装到临时目标后 sibling-import 冒烟(具体:建临时目标→apply→导入)
tmp=$(mktemp -d); (cd "$tmp" && trellis init -y)   # init 无 positional、须 cwd 内 + 非交互(-y);且须 **guru 版 CLI/core**(apply.sh:689-701 校验 core 含 run_blocking_task_hooks,装上游 core 会被自检拦);实参以本仓库 CLI usage 为准,或 scaffold 含该函数的 core 夹具
bash guru-template/overlay/apply.sh "$tmp" && echo APPLY_OK   # 先断言 apply.sh exit0,再跑下面 import 冒烟
(cd "$tmp/.trellis/scripts/guru" && PYTHONDONTWRITEBYTECODE=1 python3 -B -c "import guru_risk, guru_gate, guru_supervise")   # 步骤3+ 才含 guru_risk;步骤1/2 用 "import guru_gate, guru_supervise";步骤5+ 加 guru_review_record
# 若新增 verify 脚本:断言它已被 apply.sh 拷入 "$tmp/.trellis/scripts/guru/"
```

## Phase P0(①②③ = OCR 等效核心)

### 步骤 1 — ① 实现 review 逐行数据语义密度
- [x] 改 `flutter-implementation-guru-review/SKILL.md`:新增 D7"数据层逐行语义核查"节(排序键/解码/身份/merge 集合成员/断言可证伪性),保留 D1–D6,声明不依赖 OCR。✅ 2026-06-29
- verify:人工对 Himora diff 走一遍口径,确认能命中 U07/U12/U13/U16 类问题;skill 仍声明 OCR optional。

### 步骤 2 — ② SSOT 加载 + 否决闸
- [x] **前置(blocker)**:`_package_dir(task_dir, repo_root=None)` repo-root-safe(repo_root 给定时锚定它返绝对;None 时历史行为字节不变);`_gate_artifacts:1620` 透传 repo_root。digest 只哈希 key+内容(已确认),零回归(**run_tests 189/0**)。✅ 待补 cwd≠root 专项用例。
- [x] `guru_gate.py`:暴露 gate-local `collect_gate_artifacts(...) -> list` + gate-local `GateArtifactError`(复用 `_gate_artifacts` 围栏/exclude/命名空间;guru_gate 不 import supervise 异常,防循环);`guru_supervise.collect_review_artifacts` 调它并把 `GateArtifactError` 包成 `GuruSupervisionError`。✅ run_tests 189/0(循环 import 冒烟待 guru_risk 后并入)
- [x] ✅(189/0)`guru_supervise.py build_run_plan`:flutter implement/check 调 `collect_review_artifacts` 注入正式包(**不另起 package-walk**);**回落仅限 light 链/本就无包;full 链下声明却非法/缺失的 design_package/requirement_package → `collect_review_artifacts` 抛 `GuruSupervisionError`、spawn 前返回非零(dry-run 亦 fail-closed),**不改 `build_run_plan` 返回类型****。
- [x] ✅ review skill:加"SSOT 否决"口径(D1:正式包行级权威,reviewer/外部建议冲突即否决)。
- verify:run_tests.sh 新增"注入正式包"+ cwd≠repo-root 用例;**fail-closed 用例:full 链缺 design_package / 非法 `..` / symlink 逃逸 / 不存在的包 / 声明却缺的 requirement_package → 均返回非零不 spawn**;确认越界/未覆盖文件不会被注入。

### 步骤 3 — ③ 独立对抗 check
- [部分✅] guru_risk.py 已建(task_risk_level/git porcelain 跨层/approved-low schema/implement_check_independent_required,**单测通过、修了 repositor 复数 bug**)+ guru_gate._risk_level 改代理(单一来源)+ 循环 import 冒烟通过 + run_tests 189/0;**待:run_implement_check 接线用它**。原契约↓
- [ ] **触发契约(P0,与 design.md 一致,无 packet 依赖)**:新增/导出共享 `guru_risk.py`;P0 信号 = task.json risk + supervise 用 **`git status --porcelain=v1 -z`**(含 untracked,`git diff` 会漏新建文件)收集路径做跨层/storage 检测,**确定性跨层信号 override task low**;**true-low 须 task.json 合法 approval schema(`guru_risk:{level,reviewer_approved,approved_by,approved_at,evidence}`)+ 路径无跨层信号,裸 `risk_level=low` 不算**。`flutter && (high | unknown | 跨层信号)` → 启用独立阻断 check;true-low / 非 flutter → 旧行为。
- [ ] **(P1 defer,非 P0)** packet 基的更精风险(`slice_packet.risk`>task、`target_paths` 来自 implement.md、`implement-check --slice <unit>` 选择、单 packet auto-select / 多 packet 无 `--slice` 硬停)依赖 packet 生产者(writing-skill/trace),随 P1 ④ 落地;契约精确点见 `../06-28-guru-review-governance-report/problem-report-and-solution.md` §4.2/§4.5.2/§4.6.1,勿重发明。
- [ ] **`apply.sh` 收编 `guru_risk.py`(新 sibling 模块)**:拷贝清单(`:223-229`)+ 状态 echo(`:230`)+ `ast.parse` 自检清单(`:664-669`)三处都加;temp-install smoke 改 `import guru_risk, guru_gate, guru_supervise`;断言 `guru_risk.py` 已拷入 `$tmp/.trellis/scripts/guru`。
- [ ] `guru_supervise.py run_implement_check`:新增独立 implementation-check-review 模式(check 用对立 provider、**失败阻断非 advisory**、与 implement 隔离;记录 implement vs check 的 provider/worker/run_id 比对)。
- verify:run_tests.sh + dry-run 新增——(a) 高风险 flutter check 走对立 provider;(b) 对抗失败→阻断(非 rc0);(c) 跳过 implement 不得误推进;(d) 真·low(无跨层信号)flutter / 非 flutter 行为不变;**(d2) unknown-risk flutter(含本任务自身、缺 risk 元数据)→ fail-closed 启用**;**(d3) 裸 `risk_level=low` 但路径(含 untracked,经 `git status --porcelain`)跨 datasource+repository+controller → 仍启用;缺/非法 approval schema → 仍启用;仅合法 approved-low + 无跨层信号才旧行为;**untracked 新建 datasource/controller 文件也须被检出**;**(d4) git 不可用 / 非 git root / porcelain 失败 → `unknown_scan_failed`,`risk_level=low` 仍不绕过(fail-closed)****(packet.risk override 属 P1);(e) `adversarial_enabled=false` 下高风险 flutter implement-check **返回非零阻断**(非 _skip_adversarial rc0)。

### P0 收口
- [x] **新增 `sync:guru:check`**:`packages/cli/package.json` 加 script + `sync-guru-template.js --check`(临时目录逐文件比对 specs/workflows/overlay 三受管子树、drift→exit1、不改工作树);补 `guru-bundled.test.ts` 通过态+注入探针失败态防退化;**并接入强制闸**(prepublishOnly + ci.yml[+`guru-template/**` paths] + publish.yml,R3)。
- [x] 通用验证命令全绿(**run_tests 215/0**);**`sync:guru` + `sync:guru:check` 无漂移**(真 gate);apply.sh 收编 `guru_risk.py` + import 冒烟覆盖 guru_risk↔guru_gate↔guru_supervise。
- [x] **review gate:codex opposite-provider 对抗审查 P0 → 0 blocker + 0 should_fix**(4 轮 R1 2B2SF→R2 1B2SF→R3 0B1SF→**R4 APPROVE 0B0SF0nice**);输出存 `codex-review-p0.txt`、轮次记 `codex-plan-review-rounds.md`。
- [x] 确认全程无 OCR 依赖(codex 4 轮逐轮确认:OCR 仅作外部建议且受 SSOT 否决,无命令接入任何 gate)。

**P0 实质完成(2026-06-29):①②③ + 收口全绿,codex R4 APPROVE 过闸。10 个 commit `ce960b7b..c4e81577`;期间额外修一个真 bug(scan_paths `-uall` 未跟踪目录折叠)。**

## Phase P1(④⑤,P0 通过后)

> **DEFERRED(2026-06-29,用户决定)**:P0 已 codex 过闸交付、并安装到 guru_ai_himora。P1(④⑤)
> 依赖 packet 生产者机制(writing-skill/trace,见 §步骤4 line 40 标注),前置未就绪,**拆为后续独立
> 任务**,不在本任务范围内收口。下方 ④⑤ 设计保留作为该后续任务的输入。

### 步骤 4 — ④ REQ-UC×BHV 扩负向/排除维度
- [ ] requirement/overview/detail skill + `detail-structure-single-source.md`:加"must-not / 保留-排除 / 成功路径排除"维度 + 测试映射;对齐 requirement-doc-standard,勿另起。
- [ ] 视情扩 `guru_gate.py build_trace`/`render_matrix` 承载负向列。
- verify:对 Himora 的 INV-LOCAL-FACTS-ONLY 走一遍,确认能在 detail 阶段被 elicit 出来。

### 步骤 5 — ⑤ 负向测试强制 + verdict 结构化解析(依赖 ④;完整 gating schema)
- [ ] review skill:omission/exclusion/non-append 类不变量强制负向测试。
- [ ] `guru_supervise.py` + 新增 `guru_review_record.py`:implement-check verdict 改**完整结构化 header/JSON**——`review_result`+`route_class`+`review_target`+`review_provider`+`deterministic_checks`+`dirty_scope`+`invariant_coverage`(+record `supervisor_failure`/`repairable`);clean 须各取通过值,否则 `MALFORMED_REVIEW_OUTPUT` exit2;取代 route 全文搜索 + clean 子串;requirements 路径不强加。schema 以 `../06-28-guru-review-governance-report/problem-report-and-solution.md` §4.4/§4.6.7 为准。
- [ ] `guru_review_record.py` 共享校验/writer:supervisor parse-time 与 manual/OCR append 共用;**随 apply.sh 收编(拷贝/echo/ast.parse/import 冒烟,与 guru_risk 同)**。
- verify:run_tests.sh 新增——散文旧 route 不命中、重复字段阻断、缺任一 gating 字段阻断、clean 但 deterministic_checks/dirty_scope/invariant_coverage 未通过阻断。

### P1 收口
- [ ] 全验证命令绿;sync:guru 无漂移(真 drift gate);codex 对抗审查 P1 至 0 blocker + 0 should-fix(按 `adversarial-review.md`,输出存 `codex-review-p1.txt`)。

## 回滚点
- 每步独立 commit;失败按步 `git revert` + `sync:guru` 还原镜像。
- ②③ 触控制流,回滚优先级最高;保留 P0 通过的 commit 作为 P1 基线。
