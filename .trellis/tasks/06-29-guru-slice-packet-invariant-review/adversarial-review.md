# 对抗审查规程(codex opposite-provider)

本任务 planning 文档与各阶段改动**交付/过闸前**须经 codex 对抗审查(memory: codex-adversarial-review-before-delivery)。本文件是可复跑规程,implement.md 的 review gate 引用它(而非引用 memory)。

## 运行方式
从 **scratchpad 目录(仓库外)** 跑,避免 worktree Trellis hook 把 skill 上下文灌进输出污染:
```bash
codex exec -C <scratchpad-dir> -s read-only --skip-git-repo-check \
  -c model_reasoning_effort="high" "$(cat <prompt-file>)" > <out> 2>&1
```
- `read-only` 沙箱(只读仓库内绝对路径);**禁止调用 `ocr`**;`effort=high`(xhigh 易超后台墙钟被杀)。
- 代理(`cli_key=codex` / 127.0.0.1:37123)间歇 503/容量:用自动重试循环熬(命中 `^verdict=` 即停),**不造假、不用 Claude 假冒 codex 闸**。

## prompt 要点
让 codex 读被审文档 + 对照**真实代码**(guru_supervise.py / guru_gate.py / flutter skills / detail·gate 合同 / apply.sh / sync-guru-template.js),逐条核:citation 准确性、可落地性、内部一致性、scope、**无 OCR 依赖**、验收可测。输出格式:
```
verdict=APPROVE|REQUEST_CHANGES
blockers=<n> should_fix=<n> nice_to_have=<n>
<numbered findings: severity | location | issue | concrete fix>
```

## 通过条件
**过闸标准:`blockers=0` 且 `should_fix=0`**(nice-to-have **刻意设为非阻断**——记录但不拦,与用户确认的终止条件一致;这是 deliberate gate,**不等同于"零任何严重度"**)。每条 finding 须**读真实代码核实后**才采纳,勿盲信工具输出。

## 留痕
审查输出存进任务目录(如 `codex-review-p1.txt` / `codex-review-p1.txt`);轮次记 `codex-plan-review-rounds.md`。
