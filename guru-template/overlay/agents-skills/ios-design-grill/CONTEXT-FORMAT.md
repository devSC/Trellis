# CONTEXT.md 格式（Guru iOS 原生平台）

拷问会话中敲定的**纯领域术语**固化进仓库根 `CONTEXT.md`（术语表，零实现细节）。仓库尚无 `CONTEXT.md` 时，首个领域术语在拷问中敲定时按下方结构懒创建在仓库根。

> 落位区分：`CONTEXT.md` 只放**领域术语**（`Story` / `Chapter` 是什么、与谁有什么关系）；分层归属、`@Published` 字段、`enum Error` case、FactoryKit 注册条目这类**实现 / 设计细节不进 CONTEXT.md**——它们分别归 design §归属表与详细设计合同。doc_type 七类（`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`）是架构口径，也不是领域术语，不入表。

## 结构

```md
# {上下文名称}

{一两句：这个上下文是什么、为何存在。}

## Language（术语）

**Story**：
用户创作的一篇完整作品，是顶层聚合根，承载若干 Chapter 与 Character。
_避免_：作品、书、文档（这些在团队对话里指向不一）

**Chapter**：
Story 下的一章，承载若干 Section（段落），是导出 / 编辑的基本单位。
_避免_：章节内容、page

**Section**：
Chapter 下的一个段落 / 小节，是文本与配音绑定的最小粒度。
_避免_：段、片段

**Creation**：
首页展示的"创作"条目，是 Story 在用户视角的呈现态（与原始 Story 实体区分）。
_避免_：作品卡、item

**VoiceProfile**：
为角色 / 朗读配置的语音档案，供配音与导出引用。
_避免_：声音、配音设置

## Relationships（关系）

- 一个 **Story** 含一个或多个 **Chapter**
- 一个 **Chapter** 含一个或多个 **Section**
- 一个 **Section** 可绑定一个 **VoiceProfile**
- 首页的 **Creation** 由 **Story** 投影而来（展示态，非另一个实体）

## Example dialogue（示例对话）

> **Dev：**"用户在首页点开一条 **Creation**，是不是就等于打开了那个 **Story**？"
> **领域专家：**"展示上是，但 **Creation** 只是 **Story** 的投影态——真正可编辑的聚合是 **Story**，**Creation** 不持有 **Chapter** 细节。"

## Flagged ambiguities（已标记的歧义）

- "作品"曾同时指 **Story**（可编辑聚合）与 **Creation**（首页展示态）——已厘清：二者不同，编辑走 **Story**，列表展示走 **Creation**。
```

## 规则

- **要有主见**：同一概念存在多个词时，挑最好的一个，其余列为"避免"的别名。
- **冲突显式标记**：某术语被歧义使用时，在"Flagged ambiguities"里点出并给清晰裁决（拷问中"磨尖模糊语言"的产出落这里）。
- **定义收紧**：一句话为限，定义它**是什么**，不写它**做什么**（"做什么"属行为 / 用例，归 prd 的 `BHV-NNN` 与 `usecase`）。
- **展示关系**：术语名加粗，能明确基数时表达基数。
- **只收本上下文特有的领域术语**：通用编程概念（超时、错误类型、重试、缓存、依赖注入这类）不进表，即便项目大量使用。加术语前先问：这是本上下文独有的概念，还是通用编程概念？只有前者入表。**iOS 平台细节（`ObservableObject` / `@Published` / `FactoryKit` / `WCDBSwift` / `@Injected`）属技术栈，不是领域术语，不入表。**
- **自然聚类时分组**：术语多且能按领域子域聚类时用子标题分组；若都属同一内聚区域，平铺即可。
- **写一段示例对话**：开发者与领域专家的对话，演示术语如何自然交互、厘清相邻概念边界。

## 单上下文 vs 多上下文

**单上下文（多数情况）**：仓库根一个 `CONTEXT.md`。

**多上下文**：仓库根放 `CONTEXT-MAP.md`，列出各上下文、所在位置与关系：

```md
# Context Map

## Contexts

- [Story 创作](./Story/CONTEXT.md) — Story / Chapter / Section 的创作与编辑
- [Voice 配音](./Voice/CONTEXT.md) — VoiceProfile 与朗读配置
- [Export 导出](./Export/CONTEXT.md) — 导出任务与产物

## Relationships

- **Story 创作 → Voice 配音**：Section 引用 VoiceProfile 完成配音绑定
- **Story 创作 → Export 导出**：Export 消费整篇 Story 生成导出产物
- **Voice 配音 ↔ Export 导出**：共享 VoiceProfile 标识
```

skill 推断结构：

- 存在 `CONTEXT-MAP.md` → 读它定位各上下文。
- 仅有仓库根 `CONTEXT.md` → 单上下文。
- 两者皆无 → 首个术语敲定时在仓库根懒创建 `CONTEXT.md`。

多上下文时推断当前话题属哪个上下文；不明确则问。
