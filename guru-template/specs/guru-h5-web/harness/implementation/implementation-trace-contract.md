# implementation-trace 合同（Guru H5 / Next.js Web）

> `implement.md` / implementation-trace 是 detail Gate 的 digest-bearing planning contract。交付判定看的不是"做完感"，而是"证据感"：每条改动都能追溯到设计单元、每个完成信号都有可复现的命令输出。
> 建议路径：目标仓库 `docs/design/<feature>/implementation-trace.md`。detail 确认后的执行、验证、packet、review、commit 证据写入 task-local mutable evidence：`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`、`commit-plan.json`；若必须修改已确认 trace，必须回退 detail Gate 并重新 review/confirm。
> 平台基线：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。参考示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 是 Pages Router + Nextra + MDX + gray-matter 的轻量 blog starter（故意简化），本合同的 golden-path 以 **App Router 生产最佳实践**为准，把该示例作为**内容模型基线**，并在涉及之处明确区分 "next.js blog 示例实证" 与 "App Router 生产级补充"。
> 层级契约：本文承载实现 trace 的过程记录规则与 Gate 判定口径；与详细设计合同（L1/L2）冲突时以详细设计为准——本文不重定义 doc_type、不重定义分层依赖律，只规定"实现如何留证"。

Delivery policy is executable, not prose-only. Implementation trace must quote the selected route from `guru_delivery_policy.py`: Small records first scoped code evidence and stops fast; Micro records explicit allowed paths/max files; Lite records compact task evidence, one confirmation batch maximum, and bounded review; Full records selected slice packet, risk packet, guarded start evidence, deterministic checks and implementation review. Budget expiry never removes required Gate/review/confirmation; it produces a terminal stop or re-intake.

## Full/high 风险决策清单

`guru-risk-contract-v2` 仅在 `full_chain + high|unknown` 时要求以下 block。它必须在 `implement.md` 中恰好出现一次，且 block 内只能有一个 JSON fence；Small/Micro/Lite 和兼容 v1 合同不得被该清单拖慢。

<!-- GURU:RISK_DECISION_INVENTORY:START -->
```json
{
  "schema_version": 1,
  "task_id": "<task.json.id>",
  "scope": {
    "selected_slice_id": "<selected-slice-id>",
    "official_start_authority": "selected_slice_only",
    "later_slice_authority": "supervisor_fail_closed"
  },
  "slices": {
    "<selected-slice-id>": [
      {
        "decision_id": "DEC-<DOMAIN>-001",
        "severity": "high",
        "status": "unresolved",
        "recommendation": "<recommended choice>",
        "alternatives": [
          "<credible alternative>"
        ],
        "impact": "<scope, data, compatibility, or rollback impact>",
        "irreversible": false,
        "invariant_ids": [
          "<invariant id from the selected slice packet>"
        ],
        "required": true,
        "source_refs": [
          {
            "artifact_key": "design:chapters/<detail-artifact>.md",
            "anchor": "GURU-DECISION:DEC-<DOMAIN>-001"
          }
        ]
      }
    ]
  }
}
```
<!-- GURU:RISK_DECISION_INVENTORY:END -->

只允许 `required=true` 的 `critical|high` 决策。`decision_id` 必须跨 slice 唯一，slice 和 `invariant_ids` 必须与 packet 精确匹配；每个 `source_ref` 必须指向 Detail artifact 中恰好出现一次且包含该 decision ID 的 anchor。决策确认后将 `status` 改为 `resolved`，并添加非空 `resolution.choice` 与 `resolution.evidence`；未确认时不得伪造 `resolution`。Detail 结构检查、Detail review/confirm、risk packet 和 guarded start 必须解析同一份清单。

## Full/high slice planning audit

Full/high 的 `implement.md` 必须有 slice planning audit，目标是**最少的 commit-stable slices 和最大的安全并发宽度**，不是按 UNIT、`doc_type` 或章节机械拆分。每个普通 slice 登记 `slice_id`、真实标量 `owner_unit`、`covered_units`、文件级 `owned_paths`、`read_paths`、`depends_on`、`parallel_wave`、`independent_commit_value`、`rollback_contract`、`resource_locks` / 隔离方式、focused checks 和 reviewer context inputs/bytes。`covered_units` 是包含 `owner_unit` 在内的完整 Design UNIT 集合，只属于 planning audit；不得新增或重定义 packet / evidence schema 字段。

- 一个普通 mutable path 在同一 implementation wave 只有一个 owner；symbol、函数或 diff hunk 不能绕过文件级 ownership。共享测试文件也必须唯一归属、分波次或合并。
- 多个 Design UNIT 和多个合法 `doc_type` 可以合并为一个 implementation slice，只要每个文件仍遵守 H5 owner 与 server/client 分层、合同已冻结且该 slice 有独立提交与回滚价值。`depends_on` 默认空；UNIT 编号或 domain-type → data-access → render/interaction 写作顺序本身不是实现依赖。无法冻结且没有独立提交价值的候选 slices 必须合并。
- Full/high 恰好一个 Integration Slice。其 packet `target_paths` 是最终 union snapshot 的 review coverage；planning audit 的 `integration_owned_paths` 才是实际可写范围。普通 slices 只跑 focused checks，full regression 只出现在 Integration deterministic checks。
- 每个 v2 packet 保留并填实 `review_evidence_schema_version=2`、`requirements_design_inputs`、`target_paths`、`deterministic_checks`、`semantic_review_provider`、`invariants` 与 `integration_slice`。禁止为结构整齐默认生成一 UNIT 一 slice 或一 `doc_type` 一 slice。

## 0. 装载与硬前置

执行实现写作前依次确认，任一失败即终止并输出前置缺口（不在实现阶段补造上游决策）：

- P1 本文件可读。
- P2 通用 golden-path 可读：`.trellis/spec/guides/golden-path.md`（分层依赖律与禁止清单）。
- P3 目标仓库 `.trellis/spec/conventions/project-conventions.md` 可读且校验通过（见 §6 项目约定槽位；缺失/未填即停，先完成项目约定）。
- P4 本任务承接的详细设计合同可定位，承接的每个设计单元均以 `UNIT-<slug>` 标题存在，行为以 `BHV-NNN` 定义；**trace 中引用一律写裸 token**（`UNIT-xxx` / `BHV-NNN`），幽灵引用被 trace-matrix 断链拦截。
- P5 详细设计 Gate 已过且人工确认已落盘；未确认不得开始实现。
- P6 装载路径统一走 `.trellis/spec/harness/*`（阶段 SSOT）与 `.trellis/spec/guides/golden-path.md`（分层律）；所读文件登记进任务的 `implement.jsonl`（带 reason）。

**doc_type 权威七类（全程唯一，禁止改名/增减/换数；勿照抄 flutter/Go 的类型名）**：

| doc_type | 覆盖对象 | L2 状态 |
|----------|---------|---------|
| `server-component` | RSC 服务端组件（渲染 + 数据获取编排，默认形态） | **v1 提供 L2** |
| `client-component` | `'use client'` 交互组件（状态/事件/hooks） | **v1 提供 L2** |
| `data-access` | 数据访问层（fetch 封装 / 内容源 MDX·CMS / ORM 查询） | **v1 提供 L2** |
| `route` | App Router route 段（page/layout/loading/error.tsx + metadata/SEO） | pending |
| `ui-component` | 展示型可复用组件（纯展示、无数据获取、无业务） | pending |
| `domain-type` | TS 类型 / zod schema / 领域模型 | pending |
| `server-action` | Server Actions / route handlers（变更 / API endpoint） | pending |

v1 的 L2（render/interactive/data 三元组，对应 flutter 的 controller/usecase/repository-datasource）：`detail-type-server-component.md` / `detail-type-client-component.md` / `detail-type-data-access.md`；其余四类（`route` / `ui-component` / `domain-type` / `server-action`）为 pending（按 L1 合同八问展开，full 链须显式 `L2豁免` 或先补 L2）。trace 不替这些类型补造 L2 决策——触碰 pending 类型且上游缺 L2 时按 §4 阻塞回退。

**分层依赖律（归属硬基准；文件越出对应 owner 或依赖反向即 fail，同一 slice 覆盖多个合法 owner 本身不 fail）**：
- 服务端链：`route → server-component → data-access → domain-type`。
- 交互链：`client-component → ui-component`。
- 变更链：`server-action → data-access`。
- 私有数据获取 / secret 只能出现在 `server-component` / `data-access` / `server-action`；`client-component` 直取私有数据或 secret → fail。

**写作/实现顺序（自底向上，与详细设计同序）**：`domain-type → data-access → server-action → server-component → client-component → ui-component → route`。该顺序约束代码依赖方向；若接口与语义已在 Detail 冻结，不自动转化为 implementation slice 的 `depends_on`。

---

## 1. 计划（开工前写）

开工前按 slice planning audit 登记最少的 commit-stable slices。切片落表，post-detail mutable evidence 回填时逐片对应。

| 字段 | 要求 |
|------|------|
| 任务切片 | 每片挂真实标量 `owner_unit`、planning audit 中的 `covered_units`、涉及的 H5 权威 `doc_type`、文件范围、完成信号与验证方式。多个 `doc_type` 可在 ownership、冻结合同与独立交付价值要求同时满足时合并；逐文件 owner 与 server/client 边界仍是硬约束。 |
| 执行顺序 | 按 audit 中真实 `depends_on` 与 `parallel_wave` 排序。`domain-type → data-access → server-action → server-component → client-component → ui-component → route` 继续约束依赖方向，不以层级或 doc_type 自动串行 slices。 |
| 风险点 | 逐条预判高风险改动并写验证手段。H5 高风险面（必查）：① server/client 边界误判（把私有数据获取或 secret 漏进 `'use client'` → 私密泄露 / 打包进客户端 bundle）；② `'use client'` 边界过大（交互最小化原则被破坏，水合体积膨胀）；③ Server/Client Component 序列化边界（向 Client Component 传不可序列化 props，如函数、Date 在 RSC payload 中的处理）；④ metadata/SEO 标准化（route 段缺 `generateMetadata` 或静态 `metadata`）；⑤ 错误边界（route 段缺 `error.tsx` / `not-found.tsx`）；⑥ 样式隔离（全局 CSS 污染、Tailwind 与 CSS Modules 混用规则）；⑦ 缓存/重新验证语义（`fetch` cache、`revalidatePath`/`revalidateTag`、`dynamic`/`revalidate` 段配置）；⑧ App Router vs Pages Router 形态混淆（参考示例为 Pages Router，生产为 App Router）。 |

### 1.1 切片计划表（模板）

每个切片写一行 `### <slice_id>`，正文用下表。完成信号必须是**可机器验证的信号**，不得写"功能正常"这类主观词。

| 项 | 内容 |
|----|------|
| 承接单元 | 真实 `owner_unit` + `covered_units`（裸 `UNIT-<slug>` token；必须存在于详细设计） |
| 承接行为 | `BHV-NNN`、`BHV-MMM`（逐条；必须存在于 prd） |
| doc_type | 涉及的权威七类之一或多类（例：`domain-type` + `data-access`）；逐文件归属必须合法 |
| 文件范围 | 相对路径清单（例：`app/posts/[slug]/page.tsx`、`lib/posts.ts`） |
| 完成信号 | Full/high ordinary 例："受影响文件 `eslint` 0 error；新增 vitest 用例 `posts.parse > 解析 frontmatter` 通过"；Integration 再记录全项目 `tsc --noEmit` 与 `next build` route 形态。 |
| 验证方式 | Full/high ordinary 引用 packet 的 exact focused commands；Integration 引用 §3 的全项目类型、build、lint、test commands。非 Full/high 任务继续按原 route 合同。 |

> 示例（基于 blog 示例的内容模型基线，落地为 App Router 生产形态）：
>
> ```
> ### SL-post-content
> owner_unit：UNIT-posts-data-access
> covered_units：UNIT-post-frontmatter-schema、UNIT-posts-data-access
> doc_type：domain-type、data-access
> 承接行为：BHV-012（frontmatter schema）、BHV-013（按 slug 读取文章）
> 文件范围：lib/schema/post.ts、lib/posts.ts 及其唯一归属测试
> depends_on：[]（schema 与读取合同已在 Detail 冻结）
> 完成信号：schema 拒绝非法 frontmatter；data-access 用该 schema 解析并正确处理命中/未命中；
>           逐文件 owner 与 data-access → domain-type 方向合法
> 验证方式：pnpm vitest run lib/schema/post.test.ts lib/posts.test.ts；pnpm eslint lib/schema/post.ts lib/posts.ts
> ```
>
> **示例实证 vs 生产级补充**：blog 示例用 `gray-matter` 在 `gen-rss.js`（Node 脚本，构建期）解析 frontmatter，且 `tsconfig.json` 中 `strict: false`。生产级补充：data-access 的 frontmatter 解析必须经 `domain-type` 的 zod schema 校验后再消费（示例未做校验），且 `tsconfig` 必须 `strict: true`——这两点在切片计划中作为"生产级补充"显式标注，不能以"示例没做"为由省略。

---

## 2. 执行（字段合同，post-detail 记录进 `implementation-evidence.jsonl`）

每个切片完成时即时记录下列字段（禁止事后补写）：

- **实际改动文件清单**（相对路径，逐个列）。
- **与计划的偏差**：改了计划外文件 / 没改计划内文件 → **必须写原因**。H5 常见偏差与必记原因：
  - 为修 server/client 边界，把组件拆成 `xxx.tsx`（server）+ `xxx-client.tsx`（`'use client'`）两个文件——记录拆分理由与边界（哪些 props 跨界、是否可序列化）。
  - 新增 `loading.tsx` / `error.tsx` / `not-found.tsx`（route 段错误边界与加载态）——记录该 route 段的 Gate 要求触发了新增。
  - 新增/改动 `app/**/layout.tsx` 或根 `metadata`——记录 SEO/metadata 标准化的归属。
- **构建产物对照**：若 `next build` 的 route 形态（静态 `○`/SSG `●`/动态 `ƒ`/ISR）与设计预期不符，记录差异与处置（是否调整 `export const dynamic` / `revalidate` / `fetch` cache 选项）。
- **生成/脚手架执行记录**：若用了内容生成或脚手架脚本（如示例中的 `node ./scripts/gen-rss.js`、或生产形态下的 RSS/sitemap 生成），记录脚本路径与执行结果。

> **示例实证**：blog 示例 `package.json` 的 `build` 为 `node ./scripts/gen-rss.js && next build`——构建前先生成 `public/feed.xml`。若本任务承接 RSS/feed 行为，执行节须记录该前置脚本的运行与产物路径。**生产级补充**：App Router 下 RSS/sitemap 推荐改用 route handler（`app/feed.xml/route.ts`，归 `server-action` doc_type）或 `app/sitemap.ts`，而非构建期 Node 脚本——若改造，须在偏差中记录归属变更与理由。

---

## 3. 证据（字段合同，post-detail 记录进 `verification-evidence.jsonl`）

`verification-evidence.jsonl` 是 Gate 取证的核心。**只写"全部通过"无效**——必须给命令、给关键输出、给测试名。所有切片的完成信号都要在此回填为可复现命令。Full/high ordinary slice 只运行 packet 声明的 focused checks；全项目 typecheck、build、lint 与 full regression 只由 Integration 运行。非 Full/high 任务继续按原 route 合同。

| 类型 | 命令（统一口径） | 要求 |
|------|------|------|
| 类型检查 | Integration：`pnpm exec tsc --noEmit`（或 `npx tsc --noEmit`）；ordinary：仅 packet 声明的 focused type command | 在 `strict: true` 下 **0 error**；贴出 error 数量与（若有）处理记录。strict 是 golden-path 锁定项，不得临时关 strict 或加 `// @ts-ignore` 绕过。 |
| 构建 | Integration：`pnpm next build`（或 `npx next build`）；ordinary：不运行全局 build，除非 packet 明确声明 bounded build | Integration 构建成功并贴出受影响 route 的形态行，与设计预期逐条对照；确认无 server/client 边界报错与异常 bundle 膨胀。 |
| Lint | ordinary：`pnpm eslint <paths>`；Integration：`pnpm eslint .` | **0 error**（warning 逐条说明保留/修复）；启用 React Hooks 与 Next.js 官方规则集，拦截 server/client、image/link 误用。 |
| 单元测试 | `pnpm vitest run <path>`（CI 用 `vitest run` 非 watch） | 每个切片对应测试命令 + 结果，**精确到测试名**（不只写"通过"）；新增测试逐个列清单。覆盖：成功路径 + 全部失败路径（data-access 的 fetch 失败/解析失败/未命中；server-action 的校验失败/写入失败；domain-type 的 schema 拒绝非法输入）。 |

### 3.1 切片粒度的测试挂载（UNIT → 测试）

每个 `UNIT-<slug>` 的测试在 `verification-evidence.jsonl` 挂 **`UNIT`** 标识（与详细设计合同八问第 7 问"哪些测试验证它"对齐），并标注测试分层。H5 测试分层与 doc_type 的对应：

| doc_type | 主测试手段（项目约定槽位见 §6） | 测试分层标记 |
|----------|------|------|
| `domain-type` | zod schema 行为（合法接受 / 非法拒绝） | UNIT |
| `data-access` | fetch/解析/缓存回落的纯函数测试（mock 内容源/网络） | UNIT |
| `server-action` | 校验 + 变更 + 错误返回（mock data-access） | UNIT |
| `server-component` | 渲染编排（RTL 渲染 + 数据获取 mock；async RSC 测试） | UNIT |
| `client-component` | 交互/状态/事件（RTL + user-event） | UNIT |
| `ui-component` | 纯展示快照/可访问性（RTL） | UNIT |
| `route` | 段约定与 metadata（`generateMetadata` 返回、错误边界存在性）；端到端归 Playwright | UNIT（段单元）/ E2E（标注留给 Playwright 环节） |

`verification-evidence.jsonl` 模板（Full/high ordinary focused evidence）：

```
[UNIT-posts-data-access] data-access
- eslint lib/posts.ts: 0 error
- vitest run lib/posts.test.ts:
    ✓ getPostBySlug > 命中已知 slug 返回解析后的 Post
    ✓ getPostBySlug > 未命中返回 null
    ✓ getPostBySlug > frontmatter 缺 title 时抛 SchemaError（经 UNIT-post-frontmatter-schema 校验）
  3 passed
```

Integration 再追加全项目 `tsc --noEmit`、`next build`、全量 lint 与 full regression 证据；ordinary slice 不得用这些全局命令替代 packet 声明的 focused checks。

### 3.2 未验证项（显式列出 + 留给哪个环节）

无法在本地用上述四类命令验证的，**显式列出 + 指定后续环节**，不得隐瞒为"已验证"。H5 典型未验证项：

- 真实浏览器渲染 / 水合行为 / 交互回归 → 留给 **Playwright E2E**（项目约定的端到端测试环节）。
- Core Web Vitals（LCP/CLS/INP）、首屏性能、`next/image` 真实优化效果 → 留给 **Lighthouse / 真机 / Vercel 预览部署观测**。
- ISR/缓存重新验证的时序行为（`revalidate` 到期、`revalidateTag` 失效）→ 留给 **预览环境观测**。
- 认证流（NextAuth 会话、受保护 route 跳转）→ 若本地无凭证 → 留给 **集成/预览环境**。
- 多语言 / 不同视口的视觉表现 → 留给 **Manual QA**。

---

## 4. 阻塞与偏差（发生时记）

- **上游缺陷**：详细设计合同错/漏（八问缺项、归属违反分层依赖律、UNIT 追溯不到概要 owner、server/client 归属判错）→ 记录后**回退详细阶段修订**，不在实现阶段就地改设计（`implementation-evidence.jsonl` 留回退记录：回退到哪个文件、改了什么、Gate 重过的状态）。
- **pending L2 触碰**：切片落在 `route` / `ui-component` / `domain-type` / `server-action`（v1 无 L2）且 L1 八问展开不足以指导实现 → 不私自补造 L2，记录缺口并升级（full 链须先有 `L2豁免` 声明或先补 L2）。
- **存量违例触碰**：列出触碰的存量违例条目编号 + 处置（绕行 / 顺手修复 / 记债）。H5 常见存量违例：全局 CSS 污染、Pages Router 残留与 App Router 混存、过大的 `'use client'` 边界、未隔离的 secret 读取。
- **未决决策**：实现中冒出的新决策点（如内容源从 MDX 切到 CMS、状态管理引入 Zustand、是否启用 ISR）→ **不私自拍板**，记录并升级给人工 Gate。决策落定后回写到详细设计 / 项目约定，再继续实现。

---

## 5. 详细合同八问 → 实现 trace 对照（H5 取证锚点）

实现 trace 的可信度建立在"每条改动对得上设计单元的八问"。下表给出 H5 平台每问在 trace 中的取证锚点（审核按此核对 trace 与 diff 是否自洽）：

| 八问 | H5 取证锚点（trace 中体现处） |
|------|------|
| 1 承接哪些行为 | 切片表 `承接行为: BHV-NNN`；trace-matrix 校验断链 |
| 2 输入/输出/错误结果 | TS 类型/zod schema（domain-type）落地；`tsc --noEmit` 证类型一致；测试覆盖错误枚举 |
| 3 读/写哪些状态 | 写 owner 与分层一致：私有数据写入只在 `server-component`/`data-access`/`server-action`；client 端状态只在 `client-component`（vitest 交互用例佐证） |
| 4 调用 / 不调用哪些依赖 | 分层依赖律核对：`client-component` 不直取私有数据/secret（grep/eslint 佐证）；`route → server-component → data-access → domain-type` 不反向 |
| 5 失败如何收口 | `error.tsx`/`not-found.tsx` 存在性（route）；data-access 失败转换的 vitest 用例；server-action 错误返回 |
| 6 产生哪些事件 / 后置结果 | `revalidatePath`/`revalidateTag`、redirect、埋点；构建产物形态对照（§2） |
| 7 哪些测试验证它 | §3.1 的 `[UNIT-xxx]` 测试清单（成功 + 全部失败路径） |
| 8 哪些内容不得在此补造 | 偏差节核对：未越层补造（如 ui-component 不做数据获取、client-component 不读 secret） |

---

## 6. 项目约定槽位（project-conventions，trace 引用）

trace 的命令与判定依赖项目约定的实际取值。开工前在 `.trellis/spec/conventions/project-conventions.md` 确认下列槽位，`verification-evidence.jsonl` 命令以约定取值为准（下方为槽位与本合同默认口径）：

| 槽位 | 说明 / 本合同默认 |
|------|------|
| 路由模式 | **App Router**（生产目标）；blog 示例为 Pages Router（仅作内容模型基线，不作路由形态基线） |
| 内容源 | MDX / CMS（示例为本地 MDX + gray-matter；生产可换 CMS，换源记入偏差） |
| 状态管理 | none / Zustand / Context（默认 server-first，client 状态最小化） |
| UI 组件库 | shadcn / MUI |
| 样式方案 | Tailwind / CSS Modules（禁全局污染） |
| 测试 | **Vitest + RTL**（单元/组件，对应 §3 `vitest`）；**Playwright**（E2E，§3.2 未验证项归此） |
| lint | **ESLint + Prettier**（含 `next/core-web-vitals`，对应 §3 `eslint`） |
| 数据库 | 按约定填（ORM 查询归 data-access） |
| 认证 | NextAuth（受保护数据获取归 server-component/data-access/server-action） |
| 图像优化 | `next/image`（eslint 规则集拦截误用） |
| 部署 | Vercel（预览部署作为 §3.2 未验证项的观测环节） |

---

## 7. Gate 判定（实现 Gate，verify 脚本同口径）

实现 Gate 通过的充要条件，任一不满足即"不进 commit"：

1. **计划合同与 mutable evidence 齐全**：`implement.md` §1 计划、`implementation-evidence.jsonl` 执行/阻塞偏差、`verification-evidence.jsonl` 证据均非空且实质（无 TODO/占位/空记录）。
2. **证据可复现**：Full/high ordinary 的 packet focused checks 齐备且有命令与输出；Integration 的 `tsc --noEmit`（strict，0 error）、`next build`（成功 + route 形态对照）、全项目 `eslint` 与 full test regression 齐备。非 Full/high 任务按原 route 合同。只写"通过"判 fail。
3. **切片挂 UNIT 闭合**：每个切片的真实 `owner_unit` 与 planning audit `covered_units` 均使用裸 `UNIT-<slug>` 且 trace-matrix 无断链；幽灵引用 / 无承接行为 fail。
4. **分层依赖律未违反**：server/client 边界正确（私有数据/secret 不入 `client-component`）、`'use client'` 最小化、`route → server-component → data-access → domain-type` 与交互链/变更链无反向。
5. **doc_type 合规**：切片涉及的每个 doc_type 均严格属权威七类，无改名/增减；逐文件归属合法；触碰 pending 类型且无 `L2豁免`/L2 → 阻塞。
6. **偏差与未验证项闭合**：计划外/未做项有原因，未验证项有明确后续环节归属，上游缺陷已回退修订并留记录。

### 反模式（命中即 fail）

- ❌ trace 在 PR 前一次性补写（失去过程证据意义）。
- ❌ mutable evidence 只写"全部通过"（无命令、无测试名、无 route 形态对照）。
- ❌ 偏差不记录，PR diff 与计划对不上靠 reviewer 自己发现。
- ❌ 为过 `tsc` 临时关 `strict` 或撒 `// @ts-ignore`、`any` 绕过类型（不记入偏差）。
- ❌ 把私有数据获取 / secret 写进 `'use client'` 组件（边界泄露）。
- ❌ 照抄 blog 示例的 Pages Router 形态 / `strict: false` 当生产基线（示例是简化的内容模型基线，不是生产路由/类型基线）。
- ❌ doc_type 用 flutter/Go 的类型名（controller/usecase/repository 等）而非 H5 权威七类。
