# CONTEXT.md 格式（H5 / Next.js 领域术语表）

`CONTEXT.md` 是**领域术语表**——只收敛"这个项目的领域里同一概念有几种叫法、到底用哪个"，**不写实现细节、不写组件结构、不写 doc_type 归属**（归属在 design 归属表，结构在详细设计）。拷问中磨出来的纯术语决策固化到这里。

## 结构

```md
# {Context 名称}

{一两句：这个 context 是什么、为什么存在。}

## Language

**Post**：
已发布的一篇文章，由 front-matter（`title` / `date` / `description` / `tag` / `author`）+ 正文构成；跨 server→client 边界时以可序列化 plain object 传递。
_Avoid_: Article、Entry、Blog（混用）

**Tag**：
文章的单个分类标签；一篇 Post 可挂多个 Tag（内容源里以 `"a, b"` 形式书写，由 data-access 拆分）。
_Avoid_: Category、Label

**Slug**：
文章的 URL 标识段，对应 route 动态段 `[slug]`，由文件名/内容源派生，全局唯一。
_Avoid_: Id、Path、Permalink（混用）

## Relationships

- 一篇 **Post** 挂 0..n 个 **Tag**
- 一篇 **Post** 由唯一 **Slug** 寻址（route 动态段 `app/posts/[slug]`）
- 一个 **Tag** 聚合 0..n 篇 **Post**（标签聚合页）

## Example dialogue

> **Dev**：用户点一个 **Tag**，是在客户端筛已加载的 **Post** 列表，还是导航到该 **Tag** 的聚合页重新取数？
> **领域专家**：标签聚合页是独立 route（`/tags/[tag]`），SSR 重新取该 Tag 下的 Post；页面内再点标签 chip 做的是客户端筛选，不跳页。
> **Dev**：那"客户端筛选"的筛选态写 owner 是谁？
> **领域专家**：是那个 `'use client'` 交互叶子的局部状态，不跨页、不进全局。

## Flagged ambiguities

- "文章"曾同时指**已发布 Post** 与**未发布 Draft**——已厘清：本项目内容源只有发布态，Draft 若需要是独立概念，须单列。
- "标签"曾既指领域 **Tag** 又指 HTML/JSX 标签——术语表内 **Tag** 专指领域分类，JSX 元素一律说"元素/标签元素"避免混淆。
```

## 规则

- **要有主张（opinionated）**：同一概念有多种叫法时，挑最好的一个，其余列为 `_Avoid_` 别名。
- **显式标冲突**：术语被歧义使用时，在 "Flagged ambiguities" 点名并给出明确收口。
- **定义收紧**：一句话为限。定义它**是什么**，不写它**做什么**。
- **表达关系**：用粗体术语名 + 基数（cardinality）表达概念间关系。
- **只收本项目领域专属术语**：通用编程概念（缓存、超时、序列化、错误类型）**不进**术语表，即使项目大量使用。**`server-component`/`client-component`/`data-access`/`route`/`ui-component`/`domain-type`/`server-action` 是 doc_type（架构类型），不是领域术语，不进 CONTEXT.md**（它们的归属在 design 归属表）。加术语前自问：这是本 context 独有的领域概念，还是通用工程/框架概念？只有前者属于这里。
- **自然成簇时分小标题**：术语出现自然聚类（如 内容域 / 用户域）时用子标题分组；若全部属同一内聚领域，平铺一段即可。
- **写一段示例对话**：dev 与领域专家的对话，演示这些术语如何自然交互、厘清相邻概念边界（尤其对 H5 要顺带带出"这件事发生在 server 还是 client 边"这类边界自然落在对话里，但**不写实现**）。

## 单 context vs 多 context 仓库

**单 context（多数仓库）**：仓库根一个 `CONTEXT.md`。

**多 context**：仓库根放 `CONTEXT-MAP.md`，列出各 context、所在位置、彼此关系：

```md
# Context Map

## Contexts

- [Content](./lib/content/CONTEXT.md) — 文章 / 标签 / 内容源领域
- [Account](./lib/account/CONTEXT.md) — 用户 / 会话 / 鉴权领域（引入 NextAuth 后）

## Relationships

- **Content → Account**：受保护文章经 server 侧鉴权（server-component / server-action）校验 Account，再决定是否取 Content
- **Account ↔ Content**：共享 `AuthorId` 类型（domain-type），Content 按 ID 引用作者，不反向持有 Account 细节
```

skill 自动推断适用哪种结构：

- 存在 `CONTEXT-MAP.md` → 读它定位各 context；
- 只有仓库根 `CONTEXT.md` → 单 context；
- 两者皆无 → 首次敲定术语时惰性创建仓库根 `CONTEXT.md`。

多 context 时推断当前话题归属哪个；不明确则问用户。
