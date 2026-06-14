# Guru Flutter Client — Spec 库

> 本 spec 库由 guru-template 安装（`trellis init -t guru-flutter-client -r <registry>`），落位 `.trellis/spec/`（PROTECTED：`trellis update` 永不覆盖）。
> 知识源头：client_agent 仓库（PRD：devSC/client_agent#1）；规则唯一真源原则：writing/review 只装载，不复写。

## 目录导航

| 域 | 内容 | 何时读 |
|----|------|--------|
| `harness/` | 五阶段方法 SSOT：概要设计（行为→owner→承接索引）、详细设计（九类合同八问 + L2×3）、实现（trace 合同）、萃取模板 | 进入对应阶段前**必读**（经 implement.jsonl/check.jsonl 注入） |
| `guides/golden-path.md` | 通用方法 SSOT：分层依赖律、各层迷你路径、DI canonical、禁止清单、门禁映射 | 写任何代码前 |
| `conventions/` | 项目约定槽位：模板 + seek/calorie 取值。**本项目取值文件**：`conventions/project-conventions.md`（init 后由模板填写） | 所有阶段硬前置 |
| `flutter/` | by-layer 项目 spec — UI 表现层（widget/状态/路由/序列化）的项目实际模式（bootstrap 从真实项目填实） | 写/审 UI 表现层代码前，匹配本项目风格 |
| `service/` | by-layer 项目 spec — service 层（domain+data：usecase/repository/网络/DI/错误收口/本地库）的项目实际模式（bootstrap 从真实项目填实） | 写/审 domain+data 层代码前，匹配本项目风格 |
| `shared/` | by-layer 项目 spec — shared 跨层（代码质量/语言级/命名/git）的项目实际模式（bootstrap 从真实项目填实） | 写/审任意层代码前，匹配跨层约定 |

## by-layer 项目 spec（项目实例层）

`flutter/`、`service/`、`shared/` 是 by-layer 项目 spec：本平台按层划分为 `flutter/`（UI 表现层）、`service/`（domain+data）、`shared/`（跨层）。它与方法学层、约定层的边界如下：

- **harness/（方法学 / HOW）**：承载五阶段方法、doc_type 类型口径、Gate 判定等「怎么做」的规则；与具体项目实例无关。
- **conventions/（钉死的 SLOT 决策）**：项目约定槽位取值，是 Gate 的硬前置（不通过即停）。
- **by-layer（项目实例层）**：开放式「按层模式」文档 —— 记录本项目每一层的真实目录结构、命名规律、WRONG/CORRECT 代码示例，供 sub-agent 匹配本项目实际风格落地，而非强制 Gate。

要点：

- **document reality，非理想**：内容由 `00-bootstrap-guidelines` 任务扫描真实项目代码填实，写「这个项目实际怎么做」，不写应然的理想模式。
- **不复写、只引用**：分层依赖律、doc_type 类型口径、五阶段 Gate 等正文归 `harness/` 与 `guides/golden-path.md`，by-layer 文档只引用不复写。
- **index.md 是导航入口**：每层的 `index.md`（[flutter/index.md](./flutter/index.md)、[service/index.md](./service/index.md)、[shared/index.md](./shared/index.md)）链到本层真实存在的 topic 文件（如 flutter 的 `directory-structure.md`/`widget-guidelines.md`/`state-management.md` 等），从入口进入各层模式细节。

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
