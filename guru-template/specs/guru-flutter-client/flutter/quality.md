# Quality

> 本项目 UI 层的 analyze / format / lint 命令与质量门禁。

---

## Analyze & Lint

<!--
- 静态分析命令是什么（`flutter analyze` / `dart analyze`）？
- lint 规则集来自哪里（`analysis_options.yaml` / 自定义规则）？
- 本层关心的关键 lint（空断言 / dynamic / const 等）有哪些？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Format

<!--
- 格式化命令与配置是什么（`dart format`，行宽 / 排序约定）？
- import 排序、trailing comma 的约定是什么？
- 是否有 pre-commit / 编辑器自动格式化？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Gate / CI Enforcement

<!--
- 哪些检查是合并前的硬门禁（analyze 零告警 / format 校验 / 测试）？
- 门禁在哪里执行（本地脚本 / CI workflow）？命令是什么？
- 告警阈值与豁免（ignore）规则是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

```yaml
# WRONG:
# (绕过门禁 / 滥用 ignore 的反例配置)

# CORRECT:
# (本项目实际门禁配置片段，bootstrap 从真实项目补)
```

---

## Local Workflow

<!--
- 提交前应跑哪一串命令（format → analyze → test）？有没有一键脚本？
- 如何在本地复现 CI 的门禁结果？
- 常见门禁失败的快速排查清单是什么？
-->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
