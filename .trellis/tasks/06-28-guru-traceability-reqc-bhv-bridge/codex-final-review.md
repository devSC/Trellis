# codex opposite-provider 代码终审 — 待补(gateway 阻塞)

实现已提交 `4c442d15`,经 trellis-check 独立 Go + 抓修 1 bug + 65+ 测试。
codex opposite-provider 跨视角终审因 gateway 连续 7 次阻塞(6×503 `GW_ALL_PROVIDERS_UNAVAILABLE` + 1×网络断流)未完成。

**日后网络稳定时,在 repo 根目录一条命令补做:**

```bash
codex exec -c sandbox_mode="read-only" -c approval_policy="never" -c model_reasoning_effort="medium" -c model_reasoning_summary="auto" - <<'PROMPT'
你是对抗性代码审查者(opposite-provider, gpt-5.5)。审查 Trellis 桥任务实现代码(已提交 4c442d15,trellis-check 已抓修 1 bug)。确认无 bug、合同落实、无新引入 -> Go / Needs-fix。中文。聚焦代码,勿读 workflow/skill 无关文件。

== 背景(3 决策)==
- 决策1: traceability 加 manifest.canonical_excludes 不触发 digest;实现方案 A(fail-closed 写前检查,不改 _MANIFEST_DEFAULT_EXCLUDES)。
- 决策2: BHV<->REQ-UC 多对多行展开。决策3: REQ-UC(需求源) vs UC-<序号>(overview)命名消歧。

== trellis-check 已修的 bug(请复核 fix 无遗漏)==
_parse_existing_manual 占位符往返不对称: render 写空 cell 为 "—",parse 读回字面 "—"(非逆),致空 REQ-UC live 行 key 从 ("",unit) 变 ("—",unit) → 活单元误判 orphan;空证据解析 truthy → phantom "已移除" 行 + 第2次 aggregate 起不幂等。fix: uncell() 归一 "—"→"" 使 parse 成 render 精确逆。验证是否所有 parse cell 都过 uncell、有无其他占位符/parse 点漏网。

== 审查文件 ==
guru-template/overlay/verify/guru_gate.py(REQ_UC_REF ~64、build_trace req_ucs、render_matrix、cmd_trace_matrix --require-req-uc、_aggregate_rows_for_task、_excludes_has_traceability、_collect_aggregate_candidates、cmd_trace_aggregate、_parse_existing_manual+uncell、main 分支)
+ 测试 .trellis/tasks/06-28-guru-traceability-reqc-bhv-bridge/tests/{test_trace_bridge.py, e2e_cli.sh}

== 核对(逐项 file:line)==
1. fail-closed: cmd_trace_aggregate 写前必经 _excludes_has_traceability?manifest 缺失/字段缺失回退默认(snapshots,changes 不含 traceability)拒写?无绕过?_MANIFEST_DEFAULT_EXCLUDES 未改?
2. 反查边界: 默认排除 archive、--include-completed 扫 archive/*/*/ 月份树、realpath 围栏复用、skipped 5 分类无静默丢弃?
3. require_req_uc 三级触发优先级 + 旧 task 无字段 PASS + schema 无冲突?
4. uncell fix + 单表回填幂等 + orphan 保留 + 生成区标记健壮?
5. render_matrix 旧 prd 不增行不断链 + 多 REQ-UC 展开?
6. 新引入: build_trace req_ucs 破坏调用方?REQ_UC_REF 误匹配 UC-<序号>?边界(空prd/畸形[REQ-UC]/嵌套括号)?

只读。每项给证据。结论: Go / Needs-fix。务必输出结论段。
PROMPT
```

补做后:若 Go,本任务彻底闭环;若 Needs-fix,据发现修正 → 重 sync:guru → 重跑测试 → amend 或追加 commit。
