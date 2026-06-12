# Guru Flutter Client — Spec 库

> 本 spec 库由 guru-template 安装（`trellis init -t guru-flutter-client -r <registry>`），落位 `.trellis/spec/`（PROTECTED：`trellis update` 永不覆盖）。
> 知识源头：client_agent 仓库（PRD：devSC/client_agent#1）；规则唯一真源原则：writing/review 只装载，不复写。

## 目录导航

| 域 | 内容 | 何时读 |
|----|------|--------|
| `harness/` | 五阶段方法 SSOT：概要设计（行为→owner→承接索引）、详细设计（九类合同八问 + L2×3）、实现（trace 合同）、萃取模板 | 进入对应阶段前**必读**（经 implement.jsonl/check.jsonl 注入） |
| `guides/golden-path.md` | 通用方法 SSOT：分层依赖律、各层迷你路径、DI canonical、禁止清单、门禁映射 | 写任何代码前 |
| `conventions/` | 项目约定槽位：模板 + seek/calorie 取值。**本项目取值文件**：`conventions/project-conventions.md`（init 后由模板填写） | 所有阶段硬前置 |

## 与五阶段工作流的关系

工作流（guru-client workflow.md）的每个阶段从这里装载规则：

```
需求(prd.md)        ← 需求三件套 SSOT（guru-ai-guides，经 jsonl 引用）
概要(design.md §1)  ← harness/overview/overview-structure-single-source.md
详细(design.md §2)  ← harness/detail/detail-structure-single-source.md + detail-type-*.md
实现(implement)     ← guides/golden-path.md + harness/implementation/implementation-trace-contract.md
审核(check)         ← 各 SSOT 的审核基线章节 + conventions/project-conventions.md 的 SLOT-15 存量豁免
```

## 硬规则（任何阶段不可豁免）

分层依赖律方向、接口实现分文件、repository 必经 datasource、datasource/api 不吞异常、页面禁硬编码尺寸、l10n 同步脚本人工执行、合规红线（制裁 TLD/私有 API/动态执行）。完整清单见 `guides/golden-path.md` §10。
