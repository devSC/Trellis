## 总评（reject）

reject：计划抓到了“只挂 confirm 会被手写 `guru_gates` 绕过”的主风险，但仍把若干真实入口、分发副本、digest 语义、镜像模式、detail 阶段和旧引用面漏掉；按当前计划落地会出现“模板库看似升级、发布包和存量项目仍旧名/可绕过/误阻断”的失败。

10 点裁决简表：

1. **“双挂 cmd_confirm + cmd_check 防绕过”**：只覆盖标准 `task.py start`，不覆盖 `worktree.yaml verify → guru_gate.py auto`，也不构成防伪造安全边界。
2. **“复用 artifact_digest/_gate_digest”**：不成立。代码只有 `_gate_digest(task_dir, gate)`，没有 art 粒度 `artifact_digest()` 函数；且 raw 内容哈希会被无害变更反复触发。
3. **“legacy 黑名单 rm -rf 清旧 4 份”**：高风险。会突破现有“只删 guru-managed 名称集合”的边界，可能误删用户自建同名 skill。
4. **“design-grill 进 SHARED_SKILLS 自动满足 §8”**：普通模式大体成立，项目镜像模式不成立，`USED_PROJECT_MIRROR=1` 时完全交给外部脚本。
5. **“盲读 spec 自发现 + 门控”**：不充分。四包源码都没有生效的 `project-conventions.md`，只有 template/样例；且 Go spec 自身有路径和 doc_type 口径漂移。
6. **“detail 不纳入 grill”**：真实漏洞。detail 是实现前最后一道设计合同，计划让它完全不受 grill 硬前置约束。
7. **“opt-out 只是诚实性辅助”**：表述诚实，但遗漏低成本加固：不应让 agent 直接写 `.grill-skip-*` 文件。
8. **“单 skill 不丢端特异维度”**：未被证明。旧 skill 中大量端特异红线、例型和代码锚点不只是“对照物清单”。
9. **“8 文件约 21 处”**：错误。全仓还有 `packages/cli/src/templates/guru/workflows/*` 和测试断言。
10. **“回滚分组可独立 revert”**：不成立。skill 名、workflow 引用、apply 安装、hook 文案、gate 读取是耦合发布面，单独 revert 会制造悬空引用或假安全。

## 致命/高危发现

**致命 | bundled CLI 模板漏改，发布包会继续引用旧 4 名 skill**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:105-106`、`.trellis/tasks/06-14-universal-design-grill/implement.md:30-33` 只列 `guru-template/workflows`、`trellis-local`、chapter-guide、incident 等“8 文件约 21 处”。

代码证据：`packages/cli/src/templates/guru/index.ts:3-8` 明确 `guru-template/` 是分发真源，编辑后要运行 `pnpm -C packages/cli sync:guru` 刷新 bundled copies；但 bundled workflows 仍有旧名：`packages/cli/src/templates/guru/workflows/guru-client.md:126`、`:135`、`:169`、`:178`，`packages/cli/src/templates/guru/workflows/guru-go.md:128`、`:137`、`:171`、`:180`，`packages/cli/src/templates/guru/workflows/guru-h5.md:164`、`:173`、`:207`、`:216`，`packages/cli/src/templates/guru/workflows/guru-ios.md:147`、`:156`、`:190`、`:199`。测试还硬断言旧名：`packages/cli/test/guru/guru-bundled.test.ts:40-43`。

为什么是问题：按计划“只改 `guru-template/`”会让本地 overlay 看似升级，但 CLI offline/bundled 初始化仍输出旧 `client-grill/go-design-grill/...` 引用，测试也会继续保护旧行为。发布后用户通过 CLI init/update 得到的是分叉状态。

建议修法：把 `pnpm -C packages/cli sync:guru` 明确纳入实施和验证；同步更新 bundled workflows 与 `guru-bundled.test.ts`，并把全仓验证改成 `rg -n 'client-grill\\b|go-design-grill|h5-design-grill|ios-design-grill' .`，允许项只能是 legacy 迁移白名单和历史文档。

**高危 | 双挂 confirm/check 不覆盖 `guru_gate.py auto` / worktree verify 路径**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:63-70` 认定双挂 `cmd_confirm` + `cmd_check` 是最终兜底。

代码证据：`apply.sh` 同时写入两套门：`.trellis/worktree.yaml verify` 用 `python3 .trellis/scripts/guru/guru_gate.py auto`，见 `guru-template/overlay/apply.sh:356-359`；`config.yaml before_start` 才用 `guru_gate.py check`，见 `guru-template/overlay/apply.sh:373-379`。`auto()` 只跑结构 gate，完全不读人工确认或 grill 标记，见 `guru-template/overlay/verify/guru_gate.py:840-872`；`cmd_check()` 才读确认状态和 digest，见 `guru-template/overlay/verify/guru_gate.py:792-837`。

为什么是问题：如果 ralph-loop/check agent/工作树 verify 以 `worktree.yaml verify` 为质量停止条件，grill 缺失不会被发现。你修了 `task.py start` 的硬闸，但没有修 verify 这条“看起来通过”的通道，最终还是会出现“未 grill 但 verify 绿”的假安全。

建议修法：明确 grill 硬前置的边界。如果目标是“进入实现前必须 grill”，至少在 `auto()` 对 planning 且 requirements/overview artifact 已成形时校验 `.grill-done-*`；或者把 `worktree.yaml verify` 改成能在对应阶段调用同一 grill 校验函数，避免 `check` 和 `auto` 分叉。

**高危 | digest 方案的粒度和计划不一致，会误阻断或误放行**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:72-76`、`:121` 和 `.trellis/tasks/06-14-universal-design-grill/implement.md:18`、`:44` 说 `.grill-done-<art>` 复用现有 `artifact_digest/_gate_digest` 算法。

代码证据：代码没有 `artifact_digest()` 函数，只有 `_gate_digest(task_dir, gate)`，见 `guru-template/overlay/verify/guru_gate.py:600-611`；`artifact_digest` 只是写入 `task.json.guru_gates` 的字段名，见 `guru-template/overlay/verify/guru_gate.py:663-668`。更关键的是 `_gate_artifacts()` 是 gate 累积文件集：requirements 只含 `prd.md`，overview 含 `prd.md + README.md + design-main.md` 或 `prd.md + design.md`，detail 又叠加 chapters 和 `implement.md`，见 `guru-template/overlay/verify/guru_gate.py:568-597`。哈希直接串接 basename 和原始文件内容，见 `guru-template/overlay/verify/guru_gate.py:606-610`。

为什么是问题：计划的 `<art>` 粒度和真实 gate 粒度不同。`.grill-done-design` 如果用 overview digest，`prd.md` 或 `README.md` 导航文字、格式化、注释、章节重排都会使 design grill 失配，导致反复要求重 grill；如果只对 `design.md` 自写 hash，又和现有确认快照算法不一致，计划的“保证算法一致”不成立。

建议修法：新增明确的 `grill_digest(task_dir, art)`，定义 art 到文件集的精确映射，并决定是否 raw hash。若坚持“任何文本变化都重 grill”，在计划中明说这是有意成本；否则对 Markdown 做结构化/规范化摘要，或把 digest 校验降级成“产物修改后要求用户确认是否需要重 grill”。

**高危 | `.grill-done-*` 是自证标记，计划没有可信写入路径**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:74-75`、`.trellis/tasks/06-14-universal-design-grill/implement.md:18` 让 `design-grill` skill 收口时写标记。

代码证据：当前唯一带 TTY/soft 审计的写路径是 `cmd_confirm()`，先检查 TTY/soft quote，见 `guru-template/overlay/verify/guru_gate.py:704-727`，再通过 `_record_confirm()` 原子写 `task.json`，见 `guru-template/overlay/verify/guru_gate.py:646-688`。现有 nudge 只是 hook 直接 `touch "$MARK"`，见 `guru-template/overlay/hooks/platform/grill-nudge.sh:21-23`。`guru_gate.py main()` 只有 `digest/status/check/confirm/...`，没有任何 `grill-done` 记录命令，见 `guru-template/overlay/verify/guru_gate.py:899-927`。

为什么是问题：skill 是提示文本，不是可信执行主体。让 agent 在 task 目录写 `.grill-done-*`，本质和让 agent 写 `.grill-skip-*` 一样，是自证已完成。硬前置会变成“检查 agent 是否按指令给自己盖章”。

建议修法：新增 `guru_gate.py grill-done <art> <task_dir>` 命令，并沿用 strict/soft 审计规则；或更简单，把 grill 完成状态纳入 `guru_gate.py confirm` 的用户确认提示，由用户在确认 gate 时明确回答“已完成 grill/跳过原因”，记录到 `guru_gates[gate]`，不要让任意文件成为放行凭据。

**高危 | 项目镜像模式下 `SHARED_SKILLS` 不自动保证双面一致**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:102-103` 说 `design-grill` 进 `SHARED_SKILLS` 后走两面装，镜像模式只需确认脚本纳管。

代码证据：普通模式下 `.claude/skills` 由 apply 自己装，见 `guru-template/overlay/apply.sh:133-145`；但只要存在 `scripts/sync_platform_skills.py`，apply 就执行该脚本并设置 `USED_PROJECT_MIRROR=1`，见 `guru-template/overlay/apply.sh:126-132`。随后 §4.5 双面对齐整个跳过，见 `guru-template/overlay/apply.sh:153-207`；§8 也只调用项目脚本 `--check`，见 `guru-template/overlay/apply.sh:530-534`。现有 apply 测试的镜像脚本只写 `MIRROR_SENTINEL` 并返回 0，不验证任何 skill，见 `guru-template/overlay/tests/apply_test.sh:75-89`。

为什么是问题：himora 类项目一旦走镜像脚本，`design-grill` 是否进入 `.claude/skills` 完全取决于外部脚本。计划没有把镜像脚本契约、测试夹具和失败断言写具体，容易出现 `.agents` 有、`.claude` 无，但 `--check` 假绿。

建议修法：定义镜像脚本必须同步/校验 `SHARED_SKILLS` 的契约；在 `apply_test.sh` 场景 2 用真实镜像行为构造 fixture，断言 `.claude/skills/design-grill` 存在且旧四名不存在。对无法纳管的项目，apply 应在 `USED_PROJECT_MIRROR=1` 时显式检测 design-grill 两面存在。

**高危 | `detail 不纳入 grill` 留下实现前最大设计面绕过**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:14-15`、`:69` 决定 detail 不纳入。

代码证据：真实人工 gate 是三道：`HUMAN_GATES = ("requirements", "overview", "detail")`，见 `guru-template/overlay/verify/guru_gate.py:563`。`cmd_check()` 在 start 前总是复跑 requirements/overview/detail 三道结构 gate，见 `guru-template/overlay/verify/guru_gate.py:799-806`，并要求三道人工确认齐全，见 `guru-template/overlay/verify/guru_gate.py:807-818`。detail 产物包含 full 链 chapters 和 `implement.md`，见 `guru-template/overlay/verify/guru_gate.py:586-597`。

为什么是问题：概要 grill 只能拷问 owner/边界，详细设计才写合同八问、依赖正反面、失败收口、测试映射。计划让实现前最后一层设计完全不受 grill 约束，会留下“概要被拷问过，但详细合同偷换/补造/越界”的真实漏洞。

建议修法：至少为 detail 加 `.grill-done-detail` 或 `grill-done-contract`，并只在 detail artifact 存在时要求；如果暂不做 detail grill，就必须把风险写成显式非目标，并加强 detail-review 的红线覆盖，而不是宣称“全任务硬前置”。

**高危 | 盲读 spec 的门控把“路径存在”和“项目约定可用”混为一谈**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:49-55`、`.trellis/tasks/06-14-universal-design-grill/prd.md:20-22` 主张盲读四锚，探测不到才降级。

代码证据：四个 guru spec 包源码都没有生效的 `conventions/project-conventions.md`，只有 template/样例；我核到 `guru-flutter-client/go-backend/h5-web/ios-native` 均 `MISS conventions/project-conventions.md`。`apply.sh` 在目标已有 `project-conventions.md` 时保护不覆盖，缺失时只是提示，见 `guru-template/overlay/apply.sh:324-336`。各端 spec 明确 template/样例不生效，只有目标项目 `.trellis/spec/conventions/project-conventions.md` 生效：Flutter `guru-template/specs/guru-flutter-client/conventions/index.md:7-12`，H5 `guru-template/specs/guru-h5-web/conventions/index.md:18-22`，iOS `guru-template/specs/guru-ios-native/conventions/index.md:16-20`，Go `guru-template/specs/guru-go-backend/conventions/index.md:12-16`。

为什么是问题：通用 skill 如果只探测 `golden-path + project-conventions` 文件存在，就会在项目约定缺失、模板未填、样例误用时继续 grill；如果要求 `project-conventions.md` 必存在，又会在新装项目 bootstrap 初期直接退出，但计划没有定义用户体验和修复路径。

建议修法：适用域门控分三态：非 guru 布局、guru 但 project-conventions 未就绪、guru 且可 grill。第二态必须输出“先完成项目约定 C1~C6/C1~C5”的阻断说明，不能降级成普通 grill。

**高危 | Go spec 自身存在路径/doc_type 污染，盲读会把旧口径带入新 skill**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:51` 说固定读 `conventions/index.md` 和 overview 双候选。

代码证据：Go `conventions/index.md` 把项目约定路径写成 `.trellis/spec/harness/conventions/project-conventions.md`，见 `guru-template/specs/guru-go-backend/conventions/index.md:20-23`，这和 apply 实际落位 `.trellis/spec/conventions/project-conventions.md` 冲突，见 `guru-template/overlay/apply.sh:307-336`。同一 Go conventions 文件还用旧 doc_type 示例 `transport/service/repository/domain/app/config/auth/api-network/db-migration`，见 `guru-template/specs/guru-go-backend/conventions/index.md:80-84`；而 Go overview/detail 权威七类是 `entry-api/biz/repository-data/domain/config/external/runtime`，见 `guru-template/specs/guru-go-backend/harness/overview/overview-structure-single-source.md:239-251` 和 `guru-template/specs/guru-go-backend/harness/detail/detail-structure-single-source.md:37-47`。

为什么是问题：计划说“不内联端特异内容，运行时现读现转述”，但真实 spec 锚之间已经有漂移。通用 skill 若不实现“权威源选择 + 冲突检测”，会在 Go 项目中把旧类型名拿去拷问，制造数据污染。

建议修法：为每个平台定义权威读取顺序和冲突处理：Go/H5 doc_type 只取 `harness/overview` 或 `harness/detail`，iOS 可取 `conventions/index.md §5`，`conventions/index.md` 只用于 project-conventions 校验规则。发现锚点冲突时 fail，不能“都读”。

**高危 | 旧 skill 合并不是纯骨架抽象，计划的验证会删掉关键端特异行为**

计划位置：`.trellis/tasks/06-14-universal-design-grill/prd.md:19`、`.trellis/tasks/06-14-universal-design-grill/design.md:45-47` 认为端特异主要在对照物清单和红线；`.trellis/tasks/06-14-universal-design-grill/implement.md:19` 甚至用 grep 禁止 `SLOT/server-component/viewmodel/entry-api` 等硬编码作为验证。

代码证据：Go 旧 skill 不只列对照物，还直接写“handler 不得持数据访问、service 不得含 `net/http`、secret 字面量 fail”等处置规则，见 `guru-template/overlay/agents-skills/go-design-grill/SKILL.md:20-28`、`:43-55`。H5 旧 skill 直接写 server/client 边界、私有数据、`'use client'` 过载等拷问动作和 fail 条件，见 `guru-template/overlay/agents-skills/h5-design-grill/SKILL.md:20-28`、`:53-67`。iOS 旧 skill 直接写目标代码锚点、并发/线程归属、Domain 零依赖等，见 `guru-template/overlay/agents-skills/ios-design-grill/SKILL.md:18-24`、`:45-55`。

为什么是问题：这些不是可有可无的“示例术语”。它们是触发模型提问的具体 cue。新 skill 如果只说“盲读 spec”，又禁止正文出现任何平台 token，实际触发质量会下降，尤其是“先自查代码证据再问用户”这类动作会失去路径锚。

建议修法：不要用“无平台 token”作为成功标准。改成行为等价矩阵：Go/H5/iOS/Flutter 各列出必须覆盖的红线、边界场景、代码交叉核对锚点、ADR 例型；通用 skill 可以不写具体 token，但必须规定读取后要生成本端“拷问清单摘要”，并在验证里检查摘要含端内关键维度。

## 中低风险

**中 | legacy `rm -rf` 黑名单会违反现有“绝不碰用户自有 skill”的安装边界**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:97-100`、`.trellis/tasks/06-14-universal-design-grill/implement.md:26-27`。

代码证据：当前剪枝边界是 `GURU_SKILLS` 从模板目录枚举，注释承诺“绝不碰用户自有/官方 trellis-* skill”，见 `guru-template/overlay/apply.sh:31-32`；剪枝只对这个集合里的名字执行，见 `guru-template/overlay/apply.sh:72-79` 和 `guru-template/overlay/apply.sh:134-143`。计划把旧四名在源码目录删除后再以显式黑名单每次 `rm -rf` 目标目录，会绕开这条“由模板目录证明托管身份”的边界。

为什么是问题：如果存量项目里有人自建了同名 skill，或者旧 skill 被团队本地改造保留，apply 会无提示删除。概率不高，但这是安装器最忌讳的数据破坏类风险。

建议修法：删除前做托管身份判断：比对旧模板 hash、frontmatter name+description、或在 overlay 安装的 skill 中加 managed marker。无法确认时改为备份到 `.trellis/backup/guru-legacy-skills/<timestamp>/` 并提示人工处理。

**中 | `SHARED_SKILLS` + 建目录的成对约束没有安装器级自检**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:93-96`。

代码证据：`GURU_SKILLS` 来自现有目录枚举，见 `guru-template/overlay/apply.sh:31-32`；`skill_in_scope()` 只看 `SHARED_SKILLS` 或平台 glob，见 `guru-template/overlay/apply.sh:34-44`。安装循环只遍历 `GURU_SKILLS`，见 `guru-template/overlay/apply.sh:72-79`。所以“加到 SHARED 但忘建目录”会静默不装；“建目录但忘加 SHARED”会被当作非本平台 skill 剪掉。§8 只比较两面一致，见 `guru-template/overlay/apply.sh:537-548`，不检查“必须包含 design-grill”。

建议修法：apply 启动时校验 `for s in $SHARED_SKILLS; test -d "$HERE/agents-skills/$s"`；自检阶段断言 `.agents/skills/design-grill` 和 `.claude/skills/design-grill` 均存在，旧四名均不存在。

**中 | soft 模式和直接伪造仍可绕过，计划不能再使用“防绕过”绝对表述**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:78-81`。

代码证据：`guru_gate.py` 自己声明这只是 integrity aid，不是 security boundary；agent 可自取 digest 伪造 `guru_gates`、分配 pty、降 soft，见 `guru-template/overlay/verify/guru_gate.py:554-561`。soft 模式允许非交互 agent 在带 `--via-agent` 和 `--user-quote` 时确认，见 `guru-template/overlay/verify/guru_gate.py:712-727`。

建议修法：文案统一改成“防无意绕过/流程纪律”，不要写“防绕过”。若要低成本加固，skip/grill-done 都走 `guru_gate.py` 命令并记录 user_quote，至少和 confirm 同一审计强度。

**中 | 回滚分组不是独立可 revert**

计划位置：`.trellis/tasks/06-14-universal-design-grill/design.md:126`、`.trellis/tasks/06-14-universal-design-grill/implement.md:67-70`。

代码证据：workflow 会直接引用 skill 名，例如 `guru-template/workflows/guru-go-workflow.md:128`、`:171`；hook 文案也引用 skill 名占位符，见 `guru-template/overlay/hooks/platform/grill-nudge.sh:2-3`、`:23`；apply 决定安装哪个 skill，见 `guru-template/overlay/apply.sh:22-25`、`:119-120`。如果单独 revert “触发层”或“skill+引用”，很容易出现 workflow 指向不存在 skill，或 gate 要求 `.grill-done-*` 但没有任何 skill/命令生成。

建议修法：按可运行状态拆 commit，而不是按技术层拆：第一 commit 引入 `design-grill` 但保留旧四名兼容；第二 commit 切引用和安装；第三 commit 打开硬 gate；第四 commit 清 legacy。每一步都要有 apply + gate 测试通过。

## 计划遗漏的风险

- **缺 GitNexus 可用性降级说明**：implement 只写“先 `gitnexus_impact`”，见 `.trellis/tasks/06-14-universal-design-grill/implement.md:42`、`:75`。当前会话没有 GitNexus MCP 工具暴露，只有 GitHub/Figma/node 等工具可用；实施计划应写明没有 GitNexus 时的阻断或替代审查流程，否则会卡在工具前置。

- **缺“存量项目中旧 `.grilled-*` 标记迁移/清理”策略**：当前 `grill-nudge.sh` 会 `touch "$MARK"` 且 MARK 是 `.grilled-$ART`，见 `guru-template/overlay/hooks/platform/grill-nudge.sh:13-23`。计划会改成 `.grill-nudged-*`，但没有说存量 `.grilled-*` 怎么处理。建议 apply 清理或忽略旧标记，并在文档里声明旧标记不再表示完成。

- **缺“项目镜像脚本不可读/不可改”的外部依赖处理**：本仓库没有真实 `scripts/sync_platform_skills.py`，只有 apply 对目标项目脚本的调用，见 `guru-template/overlay/apply.sh:126-132`。待核实：himora 的镜像脚本是否允许同步新 shared skill、是否会删除旧四名、`--check` 是否真比较内容。

- **缺“用户如何完成 grill”的交互合同**：旧 nudge 只是提示加载某 skill，见 `guru-template/overlay/hooks/platform/grill-nudge.sh:21-24`；新计划要求写 `.grill-done-*`，但没有规定是用户命令、agent 命令、还是 confirm 时确认。建议把用户可执行命令和失败提示写进 workflow，避免 gate 报错后用户不知道怎样合法解锁。

## 被忽略的更简方案

更简单且更稳的做法：**先不硬删旧四份 skill，也不立刻做 `.grill-done-*` 新文件协议**。

第一阶段只做“单入口 alias + 引用切换”：新增 `design-grill`，旧四名保留为薄 wrapper，内容只写“加载 design-grill，并传入平台上下文”。apply 同时安装 `design-grill` 和旧 wrapper，workflow/hook 先切 `design-grill`。这样不需要危险 legacy `rm -rf`，也不会让存量旧引用立刻悬空。

第二阶段再把硬前置接到 `guru_gate.py confirm/check`，但不要引入自由写 `.grill-done-*` 文件；改成 `guru_gate.py confirm` 记录 `grill_status` 和 `grill_digest`。用户确认 gate 时同时确认“已 grill / 明确跳过并写理由”，复用现有 TTY/soft 审计、原子写和 digest 机制，减少一个伪造文件面。

第三阶段确认所有 bundled templates、项目镜像、测试和存量 apply 均过之后，再移除旧 wrapper。这样每一步都可独立 revert，且不会出现“引用已切、skill 被删、gate 已开但标记写不出来”的中间坏态。
