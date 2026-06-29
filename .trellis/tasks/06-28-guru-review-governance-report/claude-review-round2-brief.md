# Claude Review Brief - Round 2

请审查修订后的 `.trellis/tasks/06-28-guru-review-governance-report/problem-report-and-solution.md` 与 `.trellis/tasks/06-28-guru-review-governance-report/review-rounds.md`。

重点检查 Round 1 的 6 个 should-fix 是否真正闭合：

1. slice packet 是否已定义路径、生产者、消费者、解析/校验方。
2. scope invalid 是否已避免进入 `REPAIRABLE_IMPLEMENT_ROUTES` 空转。
3. manual / ocr_optional provider 是否已有可审计留痕方式。
4. high-risk slice 判定是否已接入 `_risk_level()` 或等价明确机制。
5. 新增结构化输出字段是否已有解析 / gating / 持久化定义。
6. invariant matrix 是否已有单一机器 SSOT，避免 implement.md 和设计包漂移。
7. CLI template 镜像同步是否已从笼统描述变成可执行步骤。

请继续使用以下格式：

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

如果没有 blocker / should-fix，请明确输出 `review_result=clean` 与 `max_severity=none`。Nice-to-have 可以列出，但不要把偏好型建议升级为 should-fix。
