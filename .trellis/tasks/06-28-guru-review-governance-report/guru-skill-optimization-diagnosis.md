# Guru Skill 优化诊断：逐行密度 + SSOT 接地 + 实现期对抗默认化

> 只读诊断产物。不引入 OCR 作为依赖,不创建实现 task,不修改任何模板。
> 目标改名(去 OCR 化):把 guru review 升级到「**逐行密度 + SSOT 接地 + 实现期对抗默认化**」——这是比 OCR 更强的目标,因为 OCR 恰恰缺 SSOT 接地。

## 0. 目标与硬约束

- **目的**:优化 guru 系各 skill 自身,解决"为什么 guru 没能在功能实现阶段提前拦下后来才暴露的跨层数据缺陷"。
- **硬约束(用户两次明确)**:**OCR(open-code-review,`ocr` CLI)不得成为必选引入项 / 任何 Gate 的硬依赖**;OCR 至多是 optional 补充工具,且其建议从属于 SSOT。
- 本诊断的全部优化都在 guru skill / 既有 `guru_supervise.py` 机制内完成,**不调用 `ocr` CLI**。

## 1. 事实地基

- 事故现场:Codex 会话 `019efd5f-199b-71e0-b010-4b5b18d970a4`(2026-06-25,项目 `guru_ai_himora`,branch `feature/msg`),线程名"修复重新生成后图片消息丢失的问题"。
- 核心 bug:`affiny_chat_local_data_source_impl.dart` 的 `_mergeRemoteMediaWithLocalFacts`(≈L912/915)把**远端 V2 group 未返回(omitted)的本地 media 项重新 append 回可见 `displayItems`**;测试 `affiny_chat_local_data_source_test.dart:1528` 把该错误行为锁死。
- 违反的 SSOT(项目侧):`design-main.md:37`(本地已完成、但 server V2 group 未含的 media 不得注入当前 V2 Cell)、`requirement-api.md:71`(V2 `mediaMessages[]` 权威)。
- OCR 是什么:阿里开源 `@alibaba-group/open-code-review`(`ocr` CLI),读 git diff 出行级评审意见;装在本机、模型 `gpt-5.5`。它在 `guru_ai_himora` 用,**不在 guru-template 内**。

### 1.1 真实时间线(诊断地基)

1. 功能实现后,**guru 实现 check 第 2 轮(claude-20104)判"仅 P3、可进 PR / final-verification-ready、无 P1/P2 阻塞"**(会话 ≈L6522)——OCR 介入前最后一道 guru 闸,**放行了满是缺陷的 diff**。
2. 用户调用 OCR:**23 次 `ocr review` / 20 完成轮 / 129 条去重发现**,密度极高;但**在核心合同上给了反向指导**(下 §2):OCR 审的是已存在的 diff,它明确建议保留漏项、**背书了 bug 行为且 20 轮从未纠正**,使该行为留在代码与测试 `:1528`(属"背书/未纠正",非 OCR 原创写入)。
3. 最终 **guru codex check 一轮命中核心 bug**——其 worker **显式引用项目侧 SSOT 行**(`design-main.md:37`/`requirement-api.md:71`)否决该 merge(会话 L14788),判 `IMPLEMENT_DEFECT` 并给正确修法;修复全程未再调用 OCR(L14793/14927/14959)。(注:这是 worker 自行引用,非 supervise 注入的权威基线,见 §5②。)

## 2. 关键纠正:OCR 不是金标准

在本任务核心 bug 上,**OCR 抓反了,不是漏抓**:

- **OCR 轮4 / 会话 L7681(finding U12)逐字**:"...local DAO still has them. **Please keep unmatched local display items in the merged list** after merging matched remote items"——把"丢弃漏项"当 bug,要求保留(= append 漏项)。20 轮从未反悔(U70/轮12 仅补副作用注记),还把"unmatched local media are preserved"当"已修复项"反复写进后续 `--background` 上下文。
- **最终 codex check / 会话 L14788 逐字**:P2——"`_mergeRemoteMediaWithLocalFacts` appends unmatched local display items... test `:1528` locks in that behavior... conflicts with `design-main.md:37` ... and `requirement-api.md:71`"。
- **根因**:OCR 只拿到 `--background` 散文上下文,**无法对齐 SSOT 行级硬约束**;guru codex check 的 worker **自行引用了项目侧需求/设计 SSOT 行**据此一轮命中(当前 supervise 并不向 implement/check 注入正式需求/设计包,见 §5②——故这是 worker 主动接地、尚非机制保证)。

⇒ 让 guru 依赖 OCR 是错的方向;正确方向是**吸收 OCR 的逐行密度,同时保住并强化 guru 独有的 SSOT 接地**。

## 3. 根因:两个独立缺口

### GAP A — 实现期审查密度不足
- 现象:OCR 在同一任务的**持续演化 diff**(审查文件集 16→35、跨 20 完成轮)上累计抓 **129 条去重发现**(多为 data-layer correctness,另含测试质量 27、task evidence、DI/codegen 等相邻类);guru 两轮 claude check **均未触及核心 V2 合并/排序/身份缺陷**:第 1 轮只命中诊断日志缺失与详细设计 owner mismatch 等非核心 P2/P3,第 2 轮仅 P3 即 final-verification-ready 放行。
- 根因:`flutter-implementation-guru-review` **已有** canonical/合同逐项核对(D1"diff 与详细设计单元逐一对照"`SKILL.md:17`、D4 证据核查 `:23`),但**缺对改动行的数据语义逐行扫描密度**(排序键/解码/身份/merge 成员/断言可证伪性),且只审改动面 + 直接依赖(`:50`)。

### GAP B — 全链无"负向/排除不变量"一等产物 + 实现 Gate 默认无对抗
- 现象:claude 轮没抓到核心合同违例;最终 codex 轮**靠 SSOT 接地**抓到。**注意:provider 因果未证实**(最终轮还叠加了"多轮 OCR 之后、diff/上下文已演化");可证实的只是——这次漏检**没有被系统性兜住**,SSOT 接地的那轮恰好兜住了。可靠结论落在机制层:缺负向/排除不变量 + 实现期审查密度不足 + 无独立审查。
- 结构根因(skill 链测绘):
  - 全链是"正向覆盖 + 合同符合性"流水线;被强制枚举的负向规则是固定封闭集(分层方向 / owner 唯一 / scope / 编号 / 图范围),**无一承载"跨层负向/排除数据不变量(数据内容 / 集合成员)"**。(注:新增的 REQ-UC×BHV 追溯矩阵 `guru_gate.py build_trace` 仍是**正向承接**追溯,未引入负向/排除维度——GAP B 不被它关闭,反而它是优化④的天然落点。)
  - grep 实证(**范围:`guru-skill-chain-map.md` 测绘的 Flutter-client 实现/规划链,不含其它平台与 bugfix skill**):该链 `排除/must-not/不变量` 命中极少且全为结构性 must-not(架构范围/编号来源等),`保留本地/远端未返回/部分返回/membership` 数据语义零命中。旁注(跨平台):`ios-design-detail-writing/SKILL.md:117` 有"不变量与边界"槽位、`guru-arch-bugfix/SKILL.md:42-46` 有不变量 owner 路由,但其测试口径(`ios-design-detail-writing/SKILL.md:119`)仍是"成功 + 全部失败路径",与 Flutter 详细合同(`detail-structure-single-source.md:50`/`:187`)同样漏成功路径排除——即 **Flutter-client 的 GAP B 已证;iOS / arch-bugfix 显示同类风险信号,但尚未审 Go/H5 等平台,不宣称全平台覆盖**。
  - **"全部失败路径"被错当"负向不变量覆盖"**:测试口径是"成功 + 全部失败路径"(`detail-structure-single-source.md:50`/`:187`),而 Himora 的排除规则**活在成功路径上**(部分遗漏 = 成功响应),从每一道 Gate 盲区穿过。
  - 实现 Gate **缺 first-class 对抗语义**:只有 requirements/overview/detail 是一等规划对抗 Gate、实现不在该 gate 模型内(`gate-confirmation-model.md:9-13`),而模型旗标/对抗 prompt 机制在 `guru_supervise.py:531-537`/`:589-598`;implement-check 虽可手动加 `--adversarial`(切对立 provider),但**非默认**,且 implement/check 虽是不同 worker、却**共用同一 provider/config、check 拿不到对抗 prompt/模型路径**(`guru_supervise.py:1020-1038`/`:531-537`/`:589-598`)。

## 4. 129 条 OCR 发现 → skill 映射

| OCR 发现类别(条数) | 本该拦截阶段 | 为何漏 | 补法(均不依赖 OCR) |
|---|---|---|---|
| 排序 by first-gen time(27) | 概要 + 详细 | 概要只写正向 GWT,无排序键歧义/同值/缺 attempts 边界 | 概要行为模型加排序边界;实现 review 逐行核排序键 |
| 测试质量 弱/误导断言(27) | 实现 review D4 + 详细测试映射 | D4 只对照测试映射,无"断言能否证伪 bug"口径 | D4 改为"每条断言必须能 fail 对应负向行为" |
| current/selected 解析(18) | 详细(group.current 合同) | 八问无"选中项回退/跨 attempt 串味"槽位 | 详细加 selection 负向用例 |
| **merge & 展示保留(17,含核心 bug)** | **详细 repository-datasource 合同(主)** | 作者从没被问"远端成功遗漏→保留+排除";好例子示范全量替换 | 新增负向/排除不变量一等产物 + 强制 elicitation |
| attempt/media 身份匹配(14) | 详细(身份匹配合同) | 合同沉默于"多本地 attempt 同 id 碰撞" | 详细加身份匹配负向用例 |
| JSON 解码健壮性(14) | 详细(DTO 解码)+ 实现 review | string-or-number/缺字段无强制核查 | DTO 合同加健壮性;实现 review 逐行核解码 |
| 其余(12) | 视具体而定 | — | — |

(129 条逐条见 `scratchpad/ocr-session-findings.md`。)

## 5. 五条优化(去 OCR 化;均在 guru skill / 既有机制内)

| # | 优化 | 改动目标 | 是否需要 OCR |
|---|---|---|---|
| ① | **实现 review 逐行扫描密度** | `flutter-implementation-guru-review` 审查口径:对改动面**逐文件逐行**过数据层正确性(排序键、解码、身份、merge、测试可证伪性),不止改动面合同符合性 | 否(内化 OCR 的*做法*,不调 `ocr`) |
| ② | **SSOT 否决闸** | guru review 以 requirement/design SSOT 行级约束为权威基线;**任何 reviewer 建议与之冲突即否决**。⚠ 落地前提:`build_run_plan` 对所有 action 只注入 skill + task 本地 `prd/design/implement.md`(`guru_supervise.py:466-473`);仅 `requirements` 额外加 `task.json` + 经 `relatedFiles`/markdown 链接可达的文件(`_requirements_reference_files:320-334`、`:474-480`)+ task 本地 `*.jsonl`(`:481-488`,prompt 审"task jsonl manifests"`:607-620`)——但这些都是 **task-local**,非正式包。`requirement_package`(`guru_gate.py:_requirement_package_dir:497`)/`design_package`(`_package_dir:470`)及其 digest 产物模型(`_gate_artifacts:1604`)是 **gate** 概念,**不**注入 supervise 的 implement/check worker。故 ② 须为 implement/check 显式加载这两个包;**且必须复用 gate 的安全枚举器**(导出等价于 `_gate_artifacts(task_dir,"detail",repo_root)` 的公共 helper,带 repo-root 围栏 `:497-529`、manifest/canonical_excludes fail-closed `:591-668`、package 级 fail-closed `_requirement_package_problem:1239`、canonical_root 围栏 `:671`、digest 命名空间 `:1604`),**不得另起第二套 package-walk**——否则会审到 digest 未覆盖/越界的文件。⚠ 精确接线(扩 `build_run_plan` 抑或 skill preflight)归**实现 task**;本诊断只定缺口与安全约束。 | 否(通用"SSOT > 任何审查者"原则;顺带能挡 OCR 错误建议,但不要求 OCR 存在) |
| ③ | **实现 Gate 引入 opposite-provider/新上下文对抗 check(独立的实现期 review 模式)** | 现状:implement/check 已是不同 worker 但**共用同一 `SupervisionConfig`/provider**(`:1020-1038`、`:507-518`、`:407-418`),`--adversarial` 让两者一起翻同一 provider;且对抗机制**重载**——模型旗标/prompt 仅对 `{requirements,overview,detail}` 生效(`:48`、`:531-537`、`:589-598`),而对抗 skip 走 `_skip_adversarial` 返回 rc 0(`:830-841`,`_execute_plan` 各失败路径委派 `:844-924`)。三种情形须分清:(i) 独立 `check --adversarial` 经 `run_action`,worker 失败或 `adversarial_enabled=false` 时 **advisory rc 0 通过、不解析 route**(`:939-965`);(ii) `implement-check --adversarial` 若 **implement 阶段被 skip,会被当成功并推进到 check**(`:1020-1031`);(iii) check 阶段被 skip 通常因无 clean/route 标记**反而 fail-closed 返回 rc 2**(`:1038-1057`)。故实现 task 须提供**非 advisory 的实现期 review 模式**,堵住 (i)(ii)。**故不能简单给 check 设 `adversarial=True`**——那会把"失败即 rc 0 放过"的 advisory 语义带进实现 Gate,反更危险。方向:新增**独立的 implementation-check-review 模式**,将"对立 provider/model/prompt"与"advisory 跳过"解耦,且**对抗失败必须阻断(非 advisory)**。⚠ 完整安全设计(provider/model/prompt 触发、disabled-adversarial 行为、timeout/killed/error 路由、clean/finding 解析、dry-run/单测矩阵)归**实现 task**;本诊断只定位缺口与方向。**真正拦下本案的是 SSOT 接地(见②),非某具体 provider;②是根治、③只提供 provider/上下文独立性。** | 否(全程 opposite-**provider** 换 LLM,不调/不依赖 `ocr`) |
| ④ | **在既有 REQ-UC×BHV 追溯矩阵上扩"负向/排除"维度(对齐 SSOT,勿另起)** | 现状:`guru_gate.py` 已建 BHV×REQ-UC×owner×UNIT×测试×切片 **正向**追溯矩阵(`build_trace`)+ 版本化需求包,但**只追正向承接,无负向/排除语义维度**。修法:让 requirement/overview/detail skill 在 REQ-UC/BHV 上显式枚举"X 须保留但不得出现在 Y""权威集 vs 存储集分叉"等 **must-not**,并**挂进同一追溯矩阵的负向列**(而非另设结构),测试映射补"成功路径上的排除"。对齐 `requirement-doc-standard` SSOT,勿重复发明。 | 否(纯 skill/合同口径) |
| ⑤ | **负向测试强制 + verdict 解析鲁棒化** | 对 omission/exclusion/non-append 类不变量强制负向测试;**verdict 解析**:`route_class` 语法容忍 `[:=：]`(`:60-62`),但 `_route_from_output` **全文搜索**(`:345-353`)本身也脆弱(会命中 worker 散文/上下文/示例里的陈旧或引用 route),clean 标记又是精确子串(`:351`、`:52`)——应改为(**仅限 implement-check**)结构化 header/JSON,在指定位置**恰好一个 `review_result` + 恰好一个 `route_class`**,**取代 route 全文搜索与 clean 子串两条脆弱路径**;requirements 路径不强加此规则(其 clean 标记 `review_result=clean/requirements-ready`、blocker 用 `route_class=REQ_BLOCKER`,`:52`/`:778-786`/`gate-confirmation-model.md:147-155`) | 否 |

**关键区分**:① 是"学 OCR 的*做法*、写进 guru skill 自己执行",不是"调用 OCR 工具"。五条无一把 `ocr` CLI 变成运行依赖或完成条件。与原报告"OCR 仅 optional、不做硬 Gate"立场一致。

> **实现现状注记(2026-06-29,session 后落了 5 个 commit):** (a) `guru_supervise.py` 现已 module-load `from guru_gate import requirements_digest`,**sibling-import 风险已 live**——`apply.sh` 拷贝清单/import 冒烟须覆盖 guru_gate↔guru_supervise 互依。(b) `guru_gate.py` 新增 REQ-UC×BHV 追溯矩阵(`build_trace:799`、`render_matrix:853`、`cmd_trace_matrix:889`)+ 版本化需求包,"不做语义判断"宪章仍在(:46);本诊断 GAP/五条优化**未被取代**。codex 对抗循环 R1–R13:旧代码 R7 干净 APPROVE → 实现变更 → 新代码 R8–R13。**核心于 R11 经 codex 收尾段逐条背书**(五优化皆 skill/runtime、OCR optional 非必需、GAP A/B 有据、OCR 定性"背书非原创"),R8–R12 全部 findings(实质 + 收尾精度)已闭合;R13 因 codex 代理外部 503 未出字面 verdict——**经用户确认按"实质完成"收尾**。详见同任务目录 `codex-review-rounds.md`(session-local 留痕、非独立审计证据)。

## 6. 交叉印证(可信度)

- 本诊断由会话内 5 个并行审查者支撑:4 个 Claude agent(事实核验 / 可落地性 / 对抗根因 / 部署链路,**为会话内背景,未作为文件附于 §8**)+ 1 个非 Claude 的 codex(gpt-5.5)。
- **本文可直接审计的异构证据是 `codex-review-output2.txt`**:codex 独立审原报告 `APPROVE_WITH_RESERVATIONS`、6 should-fix + 1 nice。其中"机制只在 invariant 预写时才拦得住""非实现者审查机器不可校验""排除类不变量须负向测试"等结论,与会话内 Claude 审查同向;**可直接审计的支撑是 `codex-review-output2.txt`**;同 provider 的 Claude 收敛属会话上下文,各 agent 输出未落盘、不可从 §8 独立复核,**故不作为独立证据**。

## 7. 非目标

- 不引入 OCR 作为依赖或完成条件;OCR 保持 optional 且从属 SSOT。
- 本诊断不创建实现 task、不修改任何模板/项目代码。
- 不替代人工确认 Gate。

## 8. 证据附件(`evidence/`,已随任务目录,自包含)

- `evidence/ocr-session-findings.md` — 129 条 OCR 发现逐条 + 22 个 prompt 全文 + 3 个 guru check-worker 结论 + OCR↔Guru 对账(均附会话行号)。
- `evidence/guru-skill-chain-map.md` — guru skill 链各阶段口径与负向/排除盲区(附 file:line)。
- `evidence/codex-review-output2.txt` — codex 对原报告的独立审查全文(verdict + 6 should-fix)。
