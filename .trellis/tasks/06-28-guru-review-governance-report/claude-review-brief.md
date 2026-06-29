# Claude Review Brief

你是本方案的独立审查者。请严格审查 `.trellis/tasks/06-28-guru-review-governance-report/problem-report-and-solution.md`，目标是找出会导致方案不可执行、不能解释 Guru review 漏检、仍然强依赖 OCR、或无法落地到当前 Guru 模板的缺陷。

## 审查上下文

用户明确要求：

- 输出问题报告和解决方案；
- 不希望 Guru 强依赖 OCR；
- 调用 Claude 反复审查方案直到无问题。

当前已知事实：

- `guru_gate.py` 只做结构存在性与引用闭合，不做语义判断。
- `guru_supervise.py implement-check` 当前 review 输入是宽泛 current diff。
- `flutter-implementation-guru-review` 有合同一致性和证据核查口径，但缺少 slice packet / invariant matrix 作为硬输入。
- Himora V2 grouped-media 事故最终缺陷是：远端 V2 group 未返回的本地 grouped media item 被 local merge 重新 append 回当前 visible displayItems；正确行为是只保留本地存储，不出现在当前 V2 remote summary 可见项。
- OCR 不应成为硬 Gate；方案应让 Guru review 自身通过 deterministic checks、scope control、invariant matrix 和 semantic review provider 闭环。

## 审查要求

请按以下格式输出：

```text
review_result=clean|findings
max_severity=none|blocker|should-fix|nice-to-have

总体判断：...

Blocker:
- 若无，写“无”。

Should-fix:
- 若无，写“无”。

Nice-to-have:
- 若无，写“无”。

逐条意见：
1. severity: blocker|should-fix|nice-to-have
   location: 文件或章节
   problem: ...
   impact: ...
   recommended_fix: ...
```

## 判定标准

Blocker：

- 方案仍把 OCR 作为默认硬依赖。
- 方案无法解释 Guru review 为什么没有提前检查出来。
- 方案缺少可落地修改点，只是原则口号。
- 方案与当前 Guru workflow / supervisor / review skill 明显冲突。

Should-fix：

- 方案方向正确，但缺少关键验收标准、迁移步骤、风险处理或边界定义。
- 方案没有说明如何处理 dirty worktree / broad diff / upstream contract defect。
- 方案无法区分 high-risk slice 与普通小改。

Nice-to-have：

- 表述可以更清晰，但不影响执行。
- 后续增强建议。

请不要给空泛赞美。没有 blocker / should-fix 时，明确输出 `review_result=clean` 与 `max_severity=none`。
