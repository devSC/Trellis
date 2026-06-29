# Review Rounds

## Round 0 - Codex self-review before Claude

状态：initial draft complete

自审结论：

- 报告已覆盖 Guru review 漏检原因：结构 Gate 非语义证明、implementation review 输入过宽、slice 未运行时强制、缺少 invariant matrix、implementation 无结构化 review record。
- 方案已明确 OCR optional，不作为硬 Gate。
- 方案已提出可落地文件级修改点、验收命令和风险矩阵。

待 Claude 审查：

- 是否仍有隐藏 OCR 依赖。
- 是否有过度设计或落地缺口。
- 是否需要补充迁移 / compatibility 方案。

## Round 1 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r1`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. `slice packet` 只有 schema，没有定义落地路径、生产者、消费者和解析方。
2. `scope invalid -> PROCESS_DEFECT` 会进入现有 `REPAIRABLE_IMPLEMENT_ROUTES`，导致 implement-check 空转。
3. `manual` / `ocr_optional` provider 不能通过 `channel spawn` 落地和留痕。
4. high-risk slice 没有运行时判定机制，未接现有 `_risk_level()`。
5. 新增结构化输出字段没有 supervisor 解析或持久化定义。
6. invariant matrix 允许落在 `implement.md` 或设计包两处，会制造 SSOT 漂移。
7. nice-to-have：CLI template 镜像同步步骤未点名。

Revision applied：

- 当时明确 slice packet 唯一路径为 `<task_dir>/slice-packets/<slice_id>.yaml`；该决定已被 Round 2 修订为 JSON，以避免新增 YAML parser 依赖。
- 明确 packet 由 implementation writing / inline agent 生成，`guru_supervise.py` 与 review skill 消费。
- 明确 scope invalid 是 supervisor preflight hard stop，exit 2，不进入 repair loop。
- 明确 `implementation-reviews.jsonl` 为 implementation review 的任务内结构化记录。
- 明确 manual / ocr_optional provider 的留痕方式，不要求走 `channel spawn`。
- 明确 high-risk 判定复用 `_risk_level()` 语义，并增加 slice packet `risk` / `risk_reasons`。
- 明确 slice packet 是 invariant matrix 唯一机器 SSOT，`implement.md` 只摘要。
- 增加 `pnpm -C packages/cli sync:guru` 与 CLI template 镜像路径验收。

Next：启动 Claude Round 2，要求只审 revised report 是否仍有 blocker / should-fix。

## Round 2 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r2`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. `slice packet` 声称是 invariant matrix 的唯一机器 SSOT，但 schema 仍只有 invariant id，没有 `rule`、正/反例、测试证据和缺失路由字段。
2. 报告把 `packages/cli/src/templates/guru/**` 镜像文件列为手工改动文件；真实同步路径是 `guru-template/` 单向 sync 到 CLI template，镜像目录会被脚本删除并重建。
3. packet 后缀是 `.yaml`，但 `guru_supervise.py` / verify 脚本当前偏 stdlib 实现，没有 YAML parser；这会引入不必要依赖或落地缺口。
4. high-risk 方案允许复制 `_risk_level()` 逻辑，后续会形成两个风险判定 SSOT。
5. nice-to-have：`PROCESS_DEFECT` 承载 scope invalid 语义过载，建议拆出非修复型 scope route。
6. nice-to-have：新增结构化字段缺失时的行为还不够明确。
7. nice-to-have：manual provider 缺少 validated append 命令；没有命令前不应作为 high-risk required provider。

Revision applied：

- packet 路径改为 `<task_dir>/slice-packets/<slice_id>.json`，明确使用 Python stdlib `json`，不引入 YAML 依赖。
- packet schema 展开 `invariants[]` 对象，必填 `invariant_id`、`rule`、`source`、`owner`、`positive_case`、`negative_case`、`test_evidence`、`route_if_missing`。
- 明确 `slice-packets/*.json` 的 `invariants[]` 是唯一机器 SSOT；`implement.md` 和设计包只允许引用或摘要。
- 手工改动文件只保留 `guru-template/**`；`packages/cli/src/templates/guru/**` 改为 `pnpm -C packages/cli sync:guru` 生成物，并说明 sync 脚本会删除重建 specs / workflows / overlay。
- 风险判定改为新增共享 helper `guru-template/overlay/verify/guru_risk.py`；`guru_gate.py` 兼容代理，`guru_supervise.py` import 同一 helper，禁止复制 `_risk_level()`。
- scope invalid 改为 supervisor preflight 专用 `route_class=SCOPE_INVALID`，`repairable=false`，exit 2，不进入 implement repair loop。
- 当时定义 worker 输出 `clean` 但缺 gating 字段时，supervisor 记录 `malformed_review_output`，`route_class=PROCESS_DEFECT`，`repairable=false`，exit 2；该决定已被 Round 3 修订为 `supervisor_failure=MALFORMED_REVIEW_OUTPUT`，不再复用 `PROCESS_DEFECT`。
- manual provider 改为必须通过 `guru_review_record.py append` validated append path 才能满足 high-risk required provider；命令未落地前 manual 只能作为补充证据。

Next：启动 Claude Round 3，要求审查 Round 2 修复是否真正闭合，并继续列出任何 blocker / should-fix / nice-to-have。

## Round 3 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r3`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. `flutter-implementation-guru-writing/SKILL.md` 是 supervised implement 的真实 packet 生产侧，但 Phase A 只列了 review skill，导致 high-risk packet 可能无人生成。
2. `unknown defaults to high` 与“仅 high-risk 小改强制 invariant matrix”的非目标冲突，且要求先有 packet 才能标 low，形成 false hard-stop。
3. `guru_supervise.py` 是平台无关入口，但方案只更新 Flutter skill；若不限定平台，会让 go / ios / h5 high-risk check 要求不存在的 packet 生产者。
4. nice-to-have：`malformed_review_output` 复用 `PROCESS_DEFECT`，与拆出 `SCOPE_INVALID` 的非修复语义不一致。
5. nice-to-have：scope preflight 写成 “check 前”，但又要求不启动 implement worker，时序措辞冲突。
6. nice-to-have：packet 的 `slice_id` 与现有 trace `UNIT-<slug>` 连接键未定义。
7. nice-to-have：manual append 示例使用 `guru-template/overlay/verify/...`，不是目标项目 runtime 路径 `.trellis/scripts/guru/...`；新增 sibling import 也需部署验证。
8. nice-to-have：`SCOPE_INVALID` 列进 worker `route_class` 枚举，但又声明 supervisor-only。

Revision applied：

- Phase A 增加 `guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md`，并要求 supervised Flutter implement 后 high-risk packet 存在。
- packet 文件名、`slice_id`、`owner_unit`、`--slice` 参数统一使用既有 `UNIT-<slug>`，避免引入新 `SL-xx` join 体系。
- P0 范围明确限定为 `platform=flutter`；go / ios / h5 需补齐对应 writing/review skill 后再启用同等 packet preflight。
- unknown 风险默认改为不强制 packet；只有 explicit high/critical、risk_reasons 命中、或 target/task evidence 显示 cross-layer/protocol/stateful-db/cache 时按 high-risk 强制。
- `SCOPE_INVALID` 与 `MALFORMED_REVIEW_OUTPUT` 改为 `supervisor_failure`，不再属于 worker `route_class`，不扩展 worker `ROUTE_RE`。
- scope preflight 明确为 spawn implement worker 之前执行；scope invalid 时不启动 implement / check worker。
- manual append 示例改为 runtime 路径 `.trellis/scripts/guru/guru_review_record.py`。
- Phase B 增加 `guru-template/overlay/apply.sh`，要求把 `guru_risk.py` / `guru_review_record.py` 与 gate/supervise 一起部署到 `.trellis/scripts/guru/`。
- Phase C 增加 `PYTHONPATH=guru-template/overlay/verify python3 - <<'PY' ...` 的 import 验证。

Next：启动 Claude Round 4，要求审查 Round 3 修复是否真正闭合，并继续列出任何 blocker / should-fix / nice-to-have。

## Round 4 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r4`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. `flutter-implementation-guru-review` 是 supervised check 的生产侧，但 §4.6 没明确要求它输出 §4.4 新增的 `review_target`、`review_provider`、`deterministic_checks`、`dirty_scope`、`invariant_coverage` 五个 gating 字段。
2. nice-to-have：unknown → high 的触发源写了 `target_paths`，但没有 packet 时读不到 `target_paths`，形成轻微循环依赖。
3. nice-to-have：`implementation-reviews.jsonl` 有 supervisor 和 `guru_review_record.py append` 两类写入方，未声明单一 writer / schema SSOT。
4. nice-to-have：`apply.sh` 要部署新增脚本，但报告没点名脚本拷贝清单和语法自检清单都要扩列。
5. nice-to-have：scope preflight 只覆盖实现前 dirty 隔离，check worker 的 `dirty_scope` 覆盖实现后 diff 越界，二者职责未显式切分。

Revision applied：

- §4.6 增加 review skill 输出合同：clean / final-verification-ready 分支必须置顶输出五个 gating 字段，否则 supervisor 判 `MALFORMED_REVIEW_OUTPUT`。
- Phase A 验收增加 supervised Flutter check clean 输出必须包含全部 gating 字段。
- unknown high-risk 上抬触发源改成 `task.json notes`、task metadata、`git diff --name-only` changed paths，不再依赖无 packet 时不可读的 `packet.target_paths`。
- `implementation-reviews.jsonl` 写入收敛为 `guru_review_record.py` 共享 schema 校验与 writer；supervisor 和 manual / OCR append 都复用同一模块。
- Phase B 验收增加：`apply.sh` 的脚本拷贝清单和语法自检清单都必须扩列 `guru_risk.py` / `guru_review_record.py`。
- §4.5 明确 scope preflight 负责实现前 dirty 隔离；check worker `dirty_scope` 负责实现后 diff 是否越界。

Next：启动 Claude Round 5，要求确认 Round 4 should-fix / nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。

## Round 5 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r5`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. supervised 模式下 packet 生产时序与 scope preflight 死锁：supervisor 要 spawn implement 前读 packet，但 packet 又被描述为 implement worker 创建。
2. Phase B 手工改动文件清单漏列 `guru-template/overlay/verify/guru_gate.py`，但方案要求它把 `_risk_level()` 改为 `guru_risk.py` 兼容代理。
3. §4.4 jsonl 行 schema 没列 `supervisor_failure` / `repairable`，但 §4.5 的 SCOPE_INVALID / MALFORMED 记录会写这两个字段。
4. nice-to-have：manual append 命令缺 `--run-id`，无法保证 jsonl `run_id` 与 evidence file 对齐。
5. nice-to-have：§4.4 输出块把 `supervisor_failure` 放进 worker 必须置顶输出，和 supervisor-only 语义冲突。
6. nice-to-have：Round 2 的 `malformed -> PROCESS_DEFECT` 历史记录未标注已被 Round 3 推翻。
7. nice-to-have：`slice_packet.risk > task.json risk` 与 `task.json risk_level=low` override 的冲突优先级未写清。

Revision applied：

- packet 改为实现前输入合同：supervised 模式下由主会话 / planning-writing 阶段基于 `implement.md` 与 detail contract 创建，必须在首次 `guru_supervise.py implement-check` 前存在。
- `flutter-implementation-guru-writing` 改为实现前校验 packet 已存在；缺失时停止并回到 planning / implementation-writing 补 packet，不在实现 worker 内临时补造语义合同。
- §4.5 改为 spawn implement / check worker 前读取已存在 packet；packet 缺失为 planning / implementation-writing 合同缺失，supervisor 硬停。
- Phase B 手工改动文件增加 `guru-template/overlay/verify/guru_gate.py`，并要求 `_risk_level()` 改为 `guru_risk.py` 兼容代理。
- `implementation-reviews.jsonl` 行 schema 增加 `supervisor_failure` 与 `repairable`；正常 worker 轮次 `supervisor_failure=none`，supervisor 硬停轮次填具体 failure。
- manual append 命令增加 `--run-id <run_id>`，并要求与 evidence file 文件名中的 run_id 一致。
- §4.4 输出块改为 worker 输出合同，不再要求 worker 输出 `supervisor_failure`；`supervisor_failure` 仅写入 jsonl。
- Round 2 旧记录补充“已被 Round 3 修订为 supervisor_failure=MALFORMED_REVIEW_OUTPUT”。
- 风险优先级写明：`slice_packet.risk` 优先；只有 packet 未声明 risk 时，`task.json risk_level=low` 才能作为 low override。

Next：启动 Claude Round 6，要求确认 Round 5 should-fix / nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。

## Round 6 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r6`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. `unknown -> high` 自动上抬规则没有可执行信号，正好会漏掉 Himora 这类未打标但跨层的核心场景。
2. nice-to-have：`apply.sh` 语法自检用 `ast.parse`，捕获不到新增兄弟模块漏拷导致的 import 断裂。
3. nice-to-have：implement-check 修复循环中，scope preflight 是循环前一次还是每轮执行未写明。
4. nice-to-have：`deterministic_checks` 由 worker 自报，与“deterministic checks 是硬 Gate，不交给 AI review”的口径存在张力。
5. nice-to-have：逐条 invariant 支持 `not_applicable`，但 `invariant_coverage=all_passed|failed|missing` 的聚合映射未定义。

Revision applied：

- §4.5.9 增加确定性 unknown→high 触发信号：
  - task.json notes / task metadata 命中 risk keywords；
  - `git diff --name-only` 路径命中 stateful storage keywords；
  - `git diff --name-only` 路径横跨至少两个 layer groups。
- §4.5 明确 scope preflight 只在进入 implement-check 修复循环前执行一次；循环内实现后越界由 check worker 的 `dirty_scope` 承担。
- §4.4 明确 P0 中 `deterministic_checks` 由 worker 按 packet 命令执行并自报，packet 命令是可复跑 SSOT；supervisor-side hard Gate 列为 P1。
- §4.3 增加 `invariant_coverage` 聚合规则：任一 fail -> failed；任一 high-risk invariant 无证据且不能 N/A -> missing；其余含合理 N/A -> all_passed。
- Phase B 验收增加 apply.sh import 冒烟测试：除 `ast.parse` 外，还要在目标 `.trellis/scripts/guru/` 下执行 `python3 -B -c "import guru_risk, guru_review_record"`。
- Phase C 命令增加安装到临时目标后的 runtime import 验证，不允许用 `|| true` 吞掉 import 失败。

Next：启动 Claude Round 7，要求确认 Round 6 should-fix / nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。

## Round 7 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r7`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. unknown→high 的 git diff 信号在 pre-implementation 阶段可能为空；应读取 implement.md 计划 target paths / staged-or-dirty paths / post-implementation check diff paths，不能只靠首轮空 diff。
2. packet schema 里的 `dirty_state.unrelated` 没被 scope preflight 消费，会让已声明无关的 lockfile 被误判为 `SCOPE_INVALID`，形成 dead schema 和误报。
3. nice-to-have：P0 deterministic checks 仍是 worker 自报，和“硬 Gate 不交给 AI review”存在已知残留张力。
4. nice-to-have：`schema_version != 1` 时的解析行为未定义。

Revision applied：

- §4.5.9 unknown→high 的路径信号源扩展为：
  - pre-implementation planned paths from `implement.md` `slice_packet` / target file summary；
  - staged-or-dirty paths from `git diff --name-only` + `git diff --cached --name-only`；
  - post-implementation check diff paths。
- stateful storage keywords 和 layer group span 均作用于上述路径源，覆盖实现前 diff 为空但计划范围已知的 Himora 式场景。
- §4.5 preflight 明确消费 `dirty_state.unrelated`：dirty 文件属于 `target_paths` 视为 in-scope；属于 `dirty_state.unrelated` 记录为 isolated；两者都不属于才 `SCOPE_INVALID`。
- §4.2 schema 校验增加 `schema_version` 必须为 `1`；未知版本硬停并提示升级 `guru_supervise.py`。
- §4.4 明确 P0 deterministic checks 是 worker 自报 + packet 可复跑 SSOT，supervisor 可做廉价抽检但不作为 P0 必需项；supervisor-side hard Gate 保持 P1。

Next：启动 Claude Round 8，要求确认 Round 7 should-fix / nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。

## Round 8 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r8`
Result：`review_result=findings`
Max severity：`should-fix`

Claude findings：

1. clean 判定只校验五个新增 gating 字段是否存在，没有定义取值级 gating；`review_result=clean` + `invariant_coverage=failed` 可能被误放行。
2. nice-to-have：`high-risk invariant` 在 packet schema 里没有字段，聚合规则无法机械判断哪些 invariant 必须有证据。
3. nice-to-have：§4.1 仍写 deterministic checks 是硬 Gate，不交给 AI review；但 §4.4 P0 实际是 worker 自报 + P1 supervisor-side hard Gate。
4. nice-to-have：Phase C runtime import 只导入 `guru_risk` / `guru_review_record`，没有导入消费者 `guru_supervise`。

Revision applied：

- §4.4 增加取值级 gating 真值表：`review_result=clean/final-verification-ready` 仅当 `deterministic_checks=passed`、`dirty_scope in {clean,isolated}`、`invariant_coverage=all_passed` 时可接受；自相矛盾的 clean 统一按 `MALFORMED_REVIEW_OUTPUT` 拒绝并写 jsonl。
- §4.3 定义第一版 high-risk invariant：`risk=high|critical` 的 slice packet 内全部 `invariants[]`，不增加 per-invariant criticality 字段。
- §4.1 原则 2 改为 deterministic checks 是 gating 目标：P0 worker 自报 + packet 可复跑 SSOT；P1 supervisor-side hard Gate。
- Phase C runtime import 命令增加消费者 `guru_supervise`：`python3 -B -c "import guru_risk, guru_review_record, guru_supervise"`。

Next：启动 Claude Round 9，要求确认 Round 8 should-fix / nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。

## Round 9 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r9`
Result：`review_result=findings`
Max severity：`nice-to-have`

Claude findings：

1. nice-to-have：§4.5.7 只写缺少 gating 字段时拒绝 clean，没有在实现清单里复述字段存在但取非通过值时也必须按 `MALFORMED_REVIEW_OUTPUT` 拒绝。
2. nice-to-have：§4.3 的“没有证据”、§4.2 示例空 `test_evidence`、§4.6.1 的“实现后只补 evidence”之间存在时序歧义，可能被误读成空 `test_evidence` 永久导致 `invariant_coverage=missing`。

Revision applied：

- §4.5.7 增加取值级拒绝规则：任一 `deterministic_checks` / `dirty_scope` / `invariant_coverage` 取非通过值却声明 `clean` 或 `final-verification-ready` 时，也按 `MALFORMED_REVIEW_OUTPUT` 硬停；取值级判定以 §4.4 为准。
- §4.3 增加证据来源和时序说明：`invariant_coverage` 按审查期 reviewer 对实际测试、命令输出、代码路径和记录文件的判定聚合；packet 创建期 `test_evidence[]` 是计划指针，可以为空。
- §4.3 / §4.6.1 明确实现后补测试名、命令或证据文件属于 evidence 补充，不改变 invariant 语义；不得在实现后改写 `rule`、`positive_case`、`negative_case`、`owner` 或 `route_if_missing` 来迁就实现。

Next：启动 Claude Round 10，要求确认 Round 9 nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。只有无任何问题时才接受 clean。

## Round 10 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r10`
Result：`review_result=findings`
Max severity：`nice-to-have`

Claude findings：

1. nice-to-have：§4.5.1 写 preflight 只对 Flutter implementation check 强制 slice packet，但未限定 high-risk，孤立阅读会与“unknown defaults to not forced”和“不要求所有小改都走 invariant matrix”冲突。
2. nice-to-have：§4.4 jsonl schema 强制 `channel` / `worker`，但 manual provider 不走 channel spawn，§4.6.7 命令也未传这两个字段。
3. nice-to-have：§4.5.9 unknown→high 实现前路径信号依赖 `implement.md` target file summary，但 §4.6.1 只强制 writing skill 写 UNIT + slice_packet 路径，未强制 target-path 摘要。

Revision applied：

- §4.5.1 改为只对 Flutter 的 high-risk implementation check 强制 slice packet，并显式引用 §4.5.9 的 high-risk 判定。
- §4.5.2 改为 “对 high-risk Flutter check” 读取已存在 packet，避免 low-risk Flutter 小改被误 hard-stop。
- §4.4 增加非 channel provider sentinel：manual 行写 `channel=manual`、`worker=<reviewer>`；显式 OCR 行写 `channel=ocr_optional`、`worker=<tool-or-run-id>`。sentinel 由 `guru_review_record.py append` 根据 provider / reviewer / run-id 派生，不要求手工传 `--channel` / `--worker`。
- §4.6.7 增加 manual 行 `channel` / `worker` 派生说明，`ocr_optional` 显式触发时记录为 `channel=ocr_optional`。
- §4.6.1 增加 `implement.md` 计划节必须写 UNIT、`slice_packet` 路径和 `target_paths` 摘要；`target_paths` 摘要是 unknown-risk 实现前上抬的可读信号源，packet 存在时以 packet `target_paths` 为机器 SSOT。
- §4.7.1 增加 trace 计划节也要写 `target_paths` 摘要。

Next：启动 Claude Round 11，要求确认 Round 10 nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。只有无任何问题时才接受 clean。

## Round 11 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r11`
Result：`review_result=findings`
Max severity：`nice-to-have`

Claude findings：

1. nice-to-have：§4.6.1 把 `target_paths` 摘要写入动作放在“实现 high-risk slice 前”的硬步骤里，但 §4.5.9 又依赖 `implement.md` target file summary 来做 unknown-risk pre-implementation 上抬；孤立阅读会误以为只有 high-risk slice 才写 `target_paths` 摘要。

Revision applied：

- §4.6.1 改为：无论风险级别，writing skill 都按 trace-contract §1 在 `implement.md` 计划节为每个 slice 写同一个 UNIT 与 `target_paths` 文件范围摘要，作为 unknown-risk 实现前上抬的可读信号源。
- high-risk slice 额外校验 `<task_dir>/slice-packets/<unit_id>.json` 已存在，并在 `implement.md` 写 `slice_packet` 路径。
- packet 存在时仍以 packet `target_paths` 为机器 SSOT。

Next：启动 Claude Round 12，要求确认 Round 11 nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。只有无任何问题时才接受 clean。

## Round 12 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r12`
Result：`review_result=findings`
Max severity：`nice-to-have`

Claude findings：

1. nice-to-have：§4.7.1 仍把 `slice_packet` 路径、`target_paths` 摘要、`invariant_ids`、`negative_case` 摘要并列为计划节统一新增项，未同步 §4.6.1 的“全 slice 写 target_paths 摘要，仅 high-risk 写 packet / invariant”分层。
2. nice-to-have：同一可读信号源在 §4.5.9 / §4.6.1 / §4.7.1 三处命名不统一：`target file summary`、`target_paths` 文件范围摘要、`target_paths` 摘要。

Revision applied：

- §4.5.9 统一术语为 `target_paths` 文件范围摘要。
- §4.7.1 改为：计划节对所有 slice 增加同一个 UNIT 与 `target_paths` 文件范围摘要；high-risk slice 额外必填 `slice_packet` 路径、`invariant_ids` 和 `negative_case` 摘要。
- 保留 packet 存在时机器可读内容以 packet 为准、`UNIT-<slug>` 作为 trace unit / packet 文件名 / `--slice` join key。

Next：启动 Claude Round 13，要求确认 Round 12 nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。只有无任何问题时才接受 clean。

## Round 13 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r13`
Result：`review_result=findings`
Max severity：`nice-to-have`

Claude findings：

1. nice-to-have：§4.7.1 要求 high-risk slice 额外必填 `slice_packet` 路径、`invariant_ids` 和 `negative_case` 摘要，但 §4.6.1 的 producer skill 硬步骤只显式列出 `slice_packet` 路径，未列 `invariant_ids` / `negative_case` 摘要。

Revision applied：

- §4.6.1 high-risk 分支补齐：high-risk slice 额外要求在 `implement.md` 计划节写 `slice_packet` 路径、`invariant_ids` 和 `negative_case` 摘要。
- §4.6.1 同时明确 packet 存在时以 packet `target_paths` 和 `invariants[]` 为机器 SSOT。

Next：启动 Claude Round 14，要求确认 Round 13 nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。只有无任何问题时才接受 clean。

## Round 14 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r14`
Result：`review_result=findings`
Max severity：`nice-to-have`

Claude findings：

1. nice-to-have：取值级 clean 一致性校验在 manual / OCR append 路径上的归属不显式。§4.4 把自相矛盾 clean -> `MALFORMED_REVIEW_OUTPUT` 描述为 supervisor 解析 worker 输出的行为，但 manual / OCR 直接经 `guru_review_record.py append` 落盘，未明确复用同一跨字段一致性校验。

Revision applied：

- §4.4 共享 writer 段补充：取值级一致性拒绝属于 `guru_review_record.py` 的共享 schema 校验；任何 provider 写入 `clean` 或 `final-verification-ready` 时，必须同时满足 `deterministic_checks=passed`、`dirty_scope in {clean,isolated}`、`invariant_coverage=all_passed`。
- 不满足时由共享 writer 拒绝并记录 / 返回 `MALFORMED_REVIEW_OUTPUT`，不能在 supervisor 和 manual / OCR append 两侧各自实现。

Next：启动 Claude Round 15，要求确认 Round 14 nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。只有无任何问题时才接受 clean。

## Round 15 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r15`
Result：`review_result=findings`
Max severity：`nice-to-have`

Claude findings：

1. nice-to-have：`review_result` 字段有三种表示：worker token `clean/final-verification-ready`、manual CLI `--result clean`、散文中的 `clean` 或 `final-verification-ready`，未固定 jsonl 落盘规范值和归一规则。
2. nice-to-have：§4.5.7 要求 supervisor parse 阶段硬停，§4.4 又写取值级一致性拒绝不能在 supervisor 和 manual / OCR append 两侧各自实现，缺少“supervisor parse-gating 与 writer persist-gating 调用同一个共享校验函数”的显式说明。

Revision applied：

- §4.4 固定 `review_result` jsonl 规范值为 `clean|findings|blocked`；worker 兼容输入可将 `final-verification-ready` 作为 `clean` 同义裁决，写入前统一归一为 `review_result=clean`。
- §4.4 的取值级 gating 改为归一后的 `review_result=clean` 才触发三条件校验。
- §4.4 / §4.5.7 明确取值级判定由 `guru_review_record.py` 暴露的单一共享校验函数承担；supervisor 的 parse-time route / exit gating 与 manual / OCR append 的 write-time gating 都调用它，不能两侧各自实现。
- §4.5.7 明确 `final-verification-ready` 先归一为 `clean`。

Next：启动 Claude Round 16，要求确认 Round 15 nice-to-have 是否闭合，并继续列出任何 blocker / should-fix / nice-to-have。只有无任何问题时才接受 clean。

## Round 16 - Claude review

Channel：`guru-review-governance-r1`
Worker：`claude-review-r16`
Result：`review_result=clean`
Max severity：`none`

Claude clean verification：

- Round 15 的两个 nice-to-have 均已闭合。
- `review_result` 的 jsonl 规范值已固定为 `clean|findings|blocked`，worker 兼容输入 `final-verification-ready` 会归一为 `clean`。
- 取值级一致性判定已收敛为 `guru_review_record.py` 暴露的单一共享校验函数，supervisor parse-time gating 与 manual / OCR append write-time gating 都调用它。
- packet 生产者 / 消费者、schema、risk 判定、scope preflight、review record、manual provider、deterministic checks P0/P1 边界未发现新的内部矛盾。
- OCR 仍是 optional bounded provider，未被放进默认必选 Gate。
- 落地路径与现有 `sync:guru` / `apply.sh` 一致。

Final status：无 blocker、无 should-fix、无 nice-to-have。
