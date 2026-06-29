# Claude Review Brief - Round 4

请审查修订后的 `.trellis/tasks/06-28-guru-review-governance-report/problem-report-and-solution.md` 与 `.trellis/tasks/06-28-guru-review-governance-report/review-rounds.md`。

本轮目标：确认 Round 3 的 3 个 should-fix 和 5 个 nice-to-have 是否已经闭合，并继续找出任何 blocker、should-fix 或 nice-to-have。用户要求最终“无任何问题”，所以 nice-to-have 也必须列出；但不要把偏好型建议升级为 should-fix。

重点检查：

1. packet 生产侧是否闭合：`flutter-implementation-guru-writing/SKILL.md` 是否已进入 Phase A 手工改动与验收，supervised Flutter implement 后是否要求 `slice-packets/<unit_id>.json` 存在。
2. packet ↔ trace 的连接键是否统一：是否已用现有 `UNIT-<slug>` 作为 packet 文件名、`slice_id`、`owner_unit` 和 `--slice` 参数。
3. unknown 风险默认值是否不再与“仅 high-risk 强制”冲突：unknown 是否默认不强制；cross-layer/protocol/stateful-db/cache evidence 是否仍可触发 high-risk。
4. 跨平台范围是否明确：P0 是否只治理 Flutter；go / ios / h5 是否不会被平台无关 supervisor 的 packet preflight 卡死。
5. `SCOPE_INVALID` / `MALFORMED_REVIEW_OUTPUT` 是否已从 worker `route_class` 中移出，作为 supervisor-only `supervisor_failure`，且不会进入 `REPAIRABLE_IMPLEMENT_ROUTES`。
6. scope preflight 时序是否统一为 spawn implement worker 之前。
7. manual append 和新 helper 的 runtime 路径 / 部署一致性是否闭合：`.trellis/scripts/guru/guru_review_record.py` 示例、`apply.sh` 部署、import 验证是否都写清楚。
8. 是否仍隐含 OCR 硬依赖，或者是否把 OCR 放到了默认必选 Gate。
9. 是否仍有无法落地、过度复杂、与当前 Guru workflow / sync script 冲突的部分。

请使用以下格式：

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

只有在没有 blocker、should-fix、nice-to-have 时，才输出 `review_result=clean` 与 `max_severity=none`。如果仍有任何问题，请输出 `review_result=findings` 并分类。
