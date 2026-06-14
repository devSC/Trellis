# Quality

> 本项目前端层的 eslint / tsc / test 命令与质量门禁约定。

---

## Lint & Format

<!-- 本项目 ESLint 配置（`next/core-web-vitals`？自定 rule 集）？Prettier 配置？lint 命令是什么（`pnpm lint`）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Type Check

<!-- 类型检查命令是什么（`tsc --noEmit` / `pnpm typecheck`）？是否在 CI/提交前强制？strict 失败如何处理？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Testing

<!-- 单测/组件测试用哪套（Vitest+RTL / Jest+RTL）？E2E 用 Playwright？测试目录是否镜像 `app/` 结构？server-component 数据获取怎么测？运行命令？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## CI Gates

<!-- 哪些检查是合并/发布的硬门禁（lint / typecheck / test / build）？跑顺序与命令级证据如何留存？门禁失败阻塞策略？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 本项目在质量门禁上踩过哪些坑？（跳过 typecheck、lint 关键规则被 disable、测试不覆盖 RSC 数据路径、本地过 CI 不过） -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```bash
# WRONG: <填反例 — 如本地只跑 dev 不跑 lint/typecheck/test 就提交>

# CORRECT: <填本项目实际的门禁命令序列 — 真实命令>
```
