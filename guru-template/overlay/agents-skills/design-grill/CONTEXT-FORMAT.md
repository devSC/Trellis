# CONTEXT.md 格式

`CONTEXT.md` 是仓库的领域术语表，只定义本项目语境里的概念、关系与歧义裁定。它不写实现细节、架构归属、doc_type、字段合同、代码路径或平台规则。拷问中磨出新术语或裁定一处歧义时，即按本格式回写。

## 结构

```md
# {上下文名称}

{一两句：这个 context 是什么、为什么存在。}

## Language

**{TermA}**：
{一句话定义它是什么。}
_避免_：{AliasA}、{AliasB}

**{TermB}**：
{一句话定义它是什么。}
_避免_：{AliasC}

## Relationships

- 一个 **{TermA}** 拥有零到多个 **{TermB}**
- **{TermB}** 只通过 **{TermA}** 被引用

## Example dialogue

> **开发：**"{用一句自然对话展示术语如何交互。}"
> **领域专家：**"{用一句回答澄清边界。}"

## Flagged ambiguities

- "{ambiguous word}" 曾同时指 **{TermA}** 与 **{TermB}** ——裁定：{清晰收口}。
```

## 规则

- **要有主见。** 同一概念有多个词时，挑一个主词，其余列为"避免"的别名。
- **显式标冲突。** 术语被歧义使用时，在 "Flagged ambiguities" 点名并给出裁定。
- **定义保持紧凑。** 一句话为限。定义它是什么，不写它怎么实现。
- **展示关系。** 用加粗术语名表达关系；能明确基数时写出基数。
- **只收领域术语。** 通用编程概念、框架类型、架构归属、平台规则、错误类型、缓存、重试、依赖注入、组件类型等不进术语表。
- **自然成簇时分组。** 术语多且能按领域子域聚类时，用小标题分组；否则保持平铺。
- **写一段示例对话。** 对话用于演示术语如何自然交互，并澄清相邻概念边界。

## 单上下文 vs 多上下文

**单上下文：** 仓库根一个 `CONTEXT.md`。

**多上下文：** 仓库根放 `CONTEXT-MAP.md`，列出各 context、所在位置、职责与关系：

```md
# Context Map

## Contexts

- [Context A](./path/to/a/CONTEXT.md) — {职责}
- [Context B](./path/to/b/CONTEXT.md) — {职责}

## Relationships

- **Context A → Context B**：{单向关系}
- **Context A ↔ Context B**：{共享概念或边界}
```

推断规则：

- 存在 `CONTEXT-MAP.md` → 先读它定位当前主题所属 context。
- 只有仓库根 `CONTEXT.md` → 单 context。
- 两者都无 → 首个术语裁定时，在仓库根懒创建 `CONTEXT.md`。
- 多 context 且归属不明确 → 先问用户，不擅自写入任意 context。
