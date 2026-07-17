---
name: h5-implementation-guru-review
description: 按通用 golden-path 与实现 trace 合同审核 Guru H5（Next.js App Router + React + TypeScript strict）代码改动，判定能否进入 PR。核查与详细设计单元（UNIT-<slug>）合同八问的一致性、分层依赖律（route → server-component → data-access → domain-type；client-component → ui-component；server-action → data-access 单向无环）与 server-first / 'use client' 最小化 / server-client 边界 / metadata-SEO / 样式隔离 / 错误边界等 canonical、验证证据（tsc / eslint / build / test）完整性、注释/日志/文档路径追溯、Secret 与 server-client 边界合规红线，并执行存量豁免判定（SLOT-15 内记债不阻塞、清单外新增违例阻塞）。标准口径住 `.trellis/spec/harness/implementation/` 与 `.trellis/spec/guides/golden-path.md`，本 skill 只审核取证、不重定义规则。
---

# H5 实现审核

> 用于用户要求「审核 H5/Next.js 实现是否对齐详细设计」「检查代码是否按详细设计落地」「实现阶段门禁审核」「review H5 implementation / review Next.js PR」时。
> 本 skill 只做审核与取证，不默认改代码。若用户要求「审核并修复」，先输出 Findings，再按用户确认或明确指令进入修复。
> 平台生产基线：Next.js App Router + React + TypeScript(strict)。代码在 `app/`（route 段 page/layout/loading/error.tsx）、`components/`（client-component 与 ui-component）、`lib/`（data-access）、`actions/`（server-action）、`types/`（domain-type，含 zod schema）；约定槽位与目录映射以 project-conventions 为准。判定基准一律以 App Router 生产 golden-path 为准（server-first / RSC 数据获取经 data-access 封装 / server-action 变更 / route 段约定 / metadata-SEO / 样式隔离 / `strict: true`）。

## 装载顺序（硬前置，任一失败即终止并仅输出前置缺口）

1. 必须先读取通用方法 SSOT `.trellis/spec/guides/golden-path.md`（编码规则与判定基准唯一来源：分层依赖律、各层迷你路径、server-client 边界规则、错误边界范式、metadata/SEO 标准、样式隔离规则、禁止清单）。不可用 → 终止并提示先安装 guru H5 spec 模板。
2. 读取同级标准包 `.trellis/spec/harness/implementation/implementation-trace-contract.md`（实现 trace 过程合同 + 实现 Gate G1~G6 口径）与 `.trellis/spec/harness/index.md`（编号纪律 BHV/UNIT、doc_type 七类、Gate 4 脚本判定项、统一红线）。
3. 读取目标仓库 `.trellis/spec/conventions/project-conventions.md`，先跑校验清单 C1~C5；**重点装载 SLOT-15 存量违例清单**（存量豁免判定的唯一数据源）与本项目的 project-conventions 槽位取值：内容源（MDX/CMS）、状态管理（none/Zustand/Context）、UI 组件库（shadcn/MUI）、样式方案（Tailwind/CSS Modules）、测试（Vitest+RTL/Playwright）、lint（ESLint+Prettier）、数据库、认证（NextAuth）、图像优化（next/image）、部署（Vercel）、路由模式（App vs Pages），并确认项目 logger / logging helper / observability 门面和 server/client 日志边界。槽位缺失或待定超限 → 前置失败。
4. 定位审核对象：被审改动（diff/分支）、本任务承接的详细设计单元（full 链 `design_package/chapters/*.md` 的 `UNIT-<slug>`；light 链 `design.md` §详细）、`implement.md`（digest-bearing trace 计划合同）与 task-local mutable evidence（`implementation-evidence.jsonl`、`verification-evidence.jsonl`、`review-records/implementation-reviews.jsonl`）。trace 缺失或 mutable evidence 缺执行/验证记录 → 前置失败（实现 Gate 证据链不存在，不进入符合性判断）。
5. 命中需要项目级取值才能判定的项（如 lint 是否真按 `ESLint + Prettier` 跑、样式是否真按 Tailwind/CSS Modules 隔离、状态管理是否真用约定的 none/Zustand/Context、认证是否真走 NextAuth、路由模式是否真是 App Router），其取值只能来自 project-conventions 槽位与仓库真实代码，不得从详细设计正文推断；仓库内残留的 Pages Router/旧形态代码不能据此放行 App Router 项目合规。
6. **装载 slice packet / invariant matrix**（P1，high-risk slice 必做）：supervisor 经 `build_run_plan` 把 resolved `slice_packet=<path>` 注入为 `--file`，brief 含 `active_slice=<slice_id>`。以 resolved `slice_packet` 路径为准读取 packet 的 `review_evidence_schema_version`、`requirements_design_inputs`、`invariants[]`（唯一机器 SSOT）、`target_paths`、`deterministic_checks`、`semantic_review_provider` 与 `integration_slice`。packet/matrix 缺失而 brief 标记 high-risk → 输出 `DETAIL_DEFECT` / `PROCESS_DEFECT`，不得 clean。

前置全部通过后，才进入下面的执行流程。

## Full/high snapshot 与 evidence Gate

- 先审核 `implement.md` 的 slice planning audit：普通 slice 是否以最少 commit-stable slices 和最大安全并发宽度为目标，是否登记唯一文件级 mutable owner、`covered_units`、真实 `depends_on`、parallel wave、独立 commit/rollback 价值、资源隔离、focused checks 与 reviewer context。仅因 UNIT 或 `doc_type` 整齐而机械拆片，按 `DETAIL_DEFECT` 阻断；一个 slice 覆盖多个合法 H5 `doc_type` 本身不是缺陷，每个文件仍须遵守 owner 与 server/client 边界。
- 一个 current snapshot 恰好由一个 semantic reviewer 负责。snapshot 绑定 target bytes、`invariants`、`requirements_design_inputs`、`deterministic_checks`、review policy / `semantic_review_provider` 与 supervisor digest；同一 snapshot 不得启动第二 reviewer 或重新 aggregate。
- clean evidence 只有在 `review_evidence_schema_version=2` 且上述每个绑定组件逐项相等时才能复用。snapshot 改变后可产生一个新 current review；v1、缺组件或部分相等的 evidence 不得复用。
- finding 只使绑定组件实际变化的 receipt 失效，不自动保留或作废所有 sibling receipts。已有 current receipt 的 slice 不得再次 aggregate；未变化的 current receipts 保持可复用。
- 普通 slice 只审 packet、planning audit、目标 diff、选定 requirements/design 与 focused evidence，只消费或执行 ordinary focused checks；不得运行 full regression。Integration 才审最终 union snapshot、ordinary current receipts、cross-slice invariants 与 final deterministic summaries，且 full regression 只属于 Integration deterministic checks。
- Integration packet `target_paths` 是 review coverage，不是写授权。实际改动路径必须是 planning audit 中 exact `integration_owned_paths` 的子集；即使路径位于 packet coverage 内，只要不在 `integration_owned_paths` 也按 `PROCESS_DEFECT` 阻断。reviewer 只读，不派 implement worker、不改 planning artifact、不直接写 receipt，也不重复执行 supervisor 已运行的同一 deterministic command。

## doc_type 权威七类（全程唯一，禁止改名/增减/换数）

详细设计的 `detail_doc_type` 在 H5 平台只有以下七类，审核时严格按此名核对，**禁止照搬 flutter/Go 的类型名**：

1. `server-component` — RSC 服务端组件（渲染 + 数据获取编排，默认形态）。
2. `client-component` — `'use client'` 交互组件（状态/事件/hooks）。
3. `data-access` — 数据访问层（fetch 封装 / 内容源 MDX·CMS / ORM 查询）。
4. `route` — App Router route 段（`page/layout/loading/error.tsx` + metadata/SEO）。
5. `ui-component` — 展示型可复用组件（纯展示、无数据获取、无业务）。
6. `domain-type` — TS 类型 / zod schema / 领域模型。
7. `server-action` — Server Actions / route handlers（变更 / API endpoint）。

L2 详例覆盖度（审核时核对 trace 是否引对 L2）：v1 提供三类 L2 文件（render/interactive/data 三元组，对应 flutter controller/usecase/repository-datasource 的位置）——`detail-type-server-component.md`（render）/ `detail-type-client-component.md`（interactive）/ `detail-type-data-access.md`（data）。其余四类 `route` / `ui-component` / `domain-type` / `server-action` 为 `l2_status: pending`，按 L1 合同八问展开；**承接 pending 类型的详细设计单元若声明走 full 链，必须挂 L2 豁免说明**（指明 pending 状态 + 用 L1 合同八问替代）；无豁免说明而引用不存在的 L2 = 断链，P1。

## 分层依赖律与 owner 层（归属硬基准，违反 fail）

服务端链：`route → server-component → data-access → domain-type`。
交互链：`client-component → ui-component`。
变更链：`server-action → data-access`。

写作/实现顺序（自底向上，审核时核对 trace 切片顺序与依赖是否一致）：`domain-type → data-access → server-action → server-component → client-component → ui-component → route`。

import 方向严格单向无环；反向 import（如 `data-access` 反向依赖 `server-component`、`ui-component` 反向依赖 `client-component`、`domain-type` 依赖任何上层）= P1。

## 执行流程（D 步骤诊断）

> 审核范围先规范化为 `BHV-NNN/UNIT-<slug> → detail_doc_type（七类之一） → 详细设计单元 → code_asset`；目标集合来自概要承接索引与本任务计划，不得按代码文件名反推 `UNIT-<slug>`。

1. **D1 合同一致性 / 八问闭合**（对应 Gate 4 切片挂 UNIT + Gate 3 八问骨架）：diff 与详细设计单元逐一对照——
   - 承接行为（八问①）：每个改动切片是否回指真实 `BHV-NNN`/`UNIT-<slug>`；引用了 prd 不存在的 `BHV-NNN`（幽灵行为）或详细设计不存在的 `UNIT-<slug>`（幽灵单元）= 断链，P1。
   - 输入/输出/错误（八问②）：组件 props 类型、`server-action` 入参/返回、`data-access` 函数签名、`domain-type` 的 TS 类型/zod schema、错误形态（throw / `error.tsx` 边界 / action 返回错误对象）是否与代码一致；合同外新增的导出组件/函数/类型、未实现的承接行为，列差集。
   - 状态读写（八问③）：写 owner（client 端状态归属 / server 端数据源 / 缓存 tag/revalidate）与概要归属是否一致；是否出现归属外的写（如 ui-component 里冒出 `useState` 业务态、server-component 里出现写操作而不走 server-action）。
   - 依赖出入边（八问④）：分层方向与 owner 层是否一致——见 D2。
   - 失败收口（八问⑤）：见 D2 错误边界契约。
   - 事件/后置（八问⑥）：缓存失效（`revalidatePath`/`revalidateTag`）、`redirect`、副作用、审计是否落地或显式声明无。
   - 测试映射（八问⑦）：见 D4。
   - 不得补造（八问⑧）：实现是否猜测/发明了详细设计未定义的合同（如 server-component 擅自决定数据获取策略、route 擅自决定 metadata 内容、client-component 擅自引入全局状态库）= P1。
   - `implementation-evidence.jsonl` 是否记录与计划的偏差与处置；上游合同错漏是否回退详细阶段修订而非就地改设计（八问缺错误形态、props 类型与 domain-type 不符、测试映射漏失败路径 → 应回退，并在 mutable evidence 留回退记录）。
   - **slice packet / invariant 核查（P1 high-risk slice 必做）**：有 packet 时，diff 必须与 packet `invariants[]` 逐条对照，每条输出 `invariant_status.<id>=pass|fail|not_applicable`；`pass` 必附证据，`not_applicable` 必附理由。invariant 违反按其 `route_if_missing` / `IMPLEMENT_DEFECT` 路由。注入的正式 requirement/design 包与 packet invariants 是行级权威基线；任何 reviewer 建议（含自身判断或外部审查器如 OCR）与 SSOT 行级约束冲突时一律否决、不得采纳。

2. **D2 分层依赖律 / server-client 边界 / canonical**（对应 golden-path 锁定项 + Gate 4 G5 + 统一红线，逐项检查改动代码）：
   - **import 方向 / 分层**：严格按上文 owner 层单向无环；`data-access` 反向 import 渲染层、`ui-component` 依赖 `client-component` 或 data-access、`route` 越过 server-component 直接持有数据访问细节、`domain-type` 依赖上层 = P1。
   - **server-first / `'use client'` 最小化**：默认 server-component，仅在真正需要交互（状态/事件/浏览器 API/hooks）处加 `'use client'`。整段大组件被无差别标 `'use client'`、把可服务端渲染的纯展示拆不出去、`'use client'` 文件里塞数据获取编排 = 违例（无设计依据时 P1，含设计依据但越界 P2）。
   - **server-client 边界（红线，不可豁免）**：私有数据获取 / secret / 数据库句柄 / 服务端 token 只允许出现在 `server-component`/`data-access`/`server-action`；`client-component` 直取私有数据源、直接 import 仅服务端模块、把 secret 通过 props 透传到 `'use client'` 子树、在 client 组件读取应只存在于 server 的环境变量（未加 `NEXT_PUBLIC_` 前缀却期望客户端可见，或把私密 env 透到客户端）= P1。Server Component 向 Client Component 传递的 props 必须可序列化（不得传函数/类实例/Date 以外的非序列化值，除非 golden-path 明确允许）。
   - **route 段约定**：`route` 单元须落在 App Router 约定文件（`page.tsx`/`layout.tsx`/`loading.tsx`/`error.tsx`），约定文件职责不混（数据获取编排在 server-component/page，交互降级在 client、`error.tsx` 必须是 `'use client'`）。
   - **metadata / SEO 标准化**：`route` 须导出标准 `metadata` 或 `generateMetadata`；动态路由缺 metadata、SEO 字段（title/description/og）与详细设计合同不符、硬编码而非按约定生成 = 违例（缺失关键 SEO 合同 P2，与设计明确冲突 P1）。
   - **错误边界**：需要兜底的 route 段须有 `error.tsx`（`'use client'`，含 reset），异步加载段须有 `loading.tsx` 或显式 Suspense；server-action/data-access 异常不得静默吞（`catch` 后空处理、`catch {}`、错误降级为 `null` 而丢失语义）= 违例（关键链路 P1）。
   - **样式隔离**：按 project-conventions 样式槽位（Tailwind / CSS Modules）落地；引入全局样式污染（非约定的全局 CSS、内联 `<style>`/`style jsx` 注入全局、跨组件泄漏的非 scoped class）= 违例。
   - **状态管理边界**：按 project-conventions 状态槽位（none / Zustand / Context）落地；新引入未批准的状态库、把服务端可得数据塞进客户端全局态 = 违例。
   - **图像 / 资源**：按图像优化槽位用 `next/image`（约定启用时）；裸 `<img>` 绕过优化、未约定的远程域 = 违例（按槽位判级）。
   - **生产基线为唯一判定基准**：判定基准一律为 App Router 生产 golden-path（App Router 目录、server-first、TS strict、错误边界、metadata 标准、样式隔离、data-access 封装内容源读取）；仓库内残留的旧形态（Pages Router 目录、`strict: false`、`style jsx` 全局注入、构建期裸读文件取数）不构成合规依据，出现即按对应 golden-path 条目判违例。

3. **D3 存量豁免判定**（逐违例必做，对应 Gate 5）：D1/D2 发现的每个违例对照 SLOT-15 清单——
   - **命中清单且未扩大违例面** → tech-debt 注记，**不阻塞**（标注关联 `[SLOT-NN]` 编号与计划处置）。
   - **清单外，或扩大了违例面** → **新增违例，P1 阻塞**（例：新代码让 client-component 直取私有数据源、把 secret 透传到客户端、新增未批准的状态库/UI 库、新写全局样式污染、新加跨层反向 import、新代码把项目从 strict 倒退）。
   - **改动修复了清单条目** → 标注「可从 SLOT-15 移除」并指明被修复的违例。
   - 触碰存量但绕行（不修）须在 `implementation-evidence.jsonl` 写「为何不修」并挂 `[SLOT-NN]`；混入业务 diff 而不挂编号 = P2 起步。

4. **D4 证据核查**（对应 Gate 4 G2/G3/G4 + `verification-evidence.jsonl`，强调「证据感而非做完感」）：
   - **计划合同与 mutable evidence 齐全且非空**：`implement.md` 计划节有 `UNIT-<slug>` 承接与完成信号；`implementation-evidence.jsonl` 有改动清单、偏差说明和阻塞/恢复记录；`verification-evidence.jsonl` 有命令级记录。缺任一证据链 = 实现 Gate 不放行（P1）。
   - **类型检查证据**（G2）：Full/high ordinary slice 只要求 packet 声明的 focused type command；全项目 `tsc --noEmit`（或 `next build` 内含类型检查）只由 Integration 承担。非 Full/high 任务继续按原 route 合同取证。项目须保持 TS strict，出现 `any` 泛滥、`@ts-ignore`/`@ts-expect-error` 无理由、关闭 strict 子项 = 证据不可信（P2 起步，关闭 strict 倒退 P1）。只写「类型通过」无命令/退出态 = 证据不可信（P2 起步）。引入的类型失败未收口 = P1。
   - **静态检查证据**（G3）：Full/high ordinary slice 只要求 packet 声明的 affected-path `eslint` + `prettier --check`；全项目检查只由 Integration 承担。非 Full/high 任务继续按原 route 合同取证。逐条记录通过/失败 + 处理；`eslint-disable` 豁免须写理由并指向 `[SLOT-15]`；已运行 build 时，其 RSC 边界告警（如 client 引服务端模块）须收口。
   - **构建证据**：Full/high ordinary slice 不要求全局 `next build`，除非 packet 明确将 bounded build 列为 focused command；完整 `next build` 只由 Integration 承担。非 Full/high 任务继续按原 route 合同取证。任何实际运行的 build 都须贴命令 + 退出态 + 关键告警处理。
   - **测试证据**（G4，按测试槽位 Vitest+RTL / Playwright）：测试名级别结果（如 `✓ PostList renders empty state`、Playwright `✓ [chromium] › detail page shows 404`），不只写「全部通过」；覆盖承接 UNIT/BHV 的成功路径 + **全部失败路径**（错误边界触发、空数据、加载态、表单校验失败、未授权）；新增测试清单可追溯到 `UNIT-<slug>`/`BHV-NNN`。漏失败路径用例 = P2 起步；高风险链路（认证 / server-action 变更 / server-client 边界 / 私有数据获取 / SEO 关键页）漏测 = P1。client-component 交互应有 RTL/事件测试；route 关键流应有 e2e。
   - **invariant 证据**（P1 high-risk slice）：每条 high-risk invariant 至少一个正向或负向测试、命令或代码路径作为 `invariant_evidence`；`pass` 无证据按 `invariant_coverage=missing` 阻断。负向语义（排除/遗漏/不得暴露 secret/不得 client 直取私有数据）缺测试或等价确定性检查按 P1/P2 判级。
   - **可复现抽查**：核对至少 1 条 `verification-evidence.jsonl` 命令的当前输入与输出证据；不得重复执行 supervisor 已运行的同一 deterministic command。需要额外语义取证时只跑未重复的 ordinary focused check；证据与当前 snapshot 不符 = 证据造假（P1）。
   - **代码生成 / 派生产物执行记录**：启用了生成型槽位（如 ORM 客户端生成 `prisma generate`、zod 推导、CMS 类型生成、内容索引/RSS 生成 `scripts/gen-rss.js` 等，依 project-conventions 选型）且触发条件满足时，须有生成命令与产物清单记录；当前 golden-path 默认无代码生成时 `implementation-evidence.jsonl` 须写「N/A：无代码生成槽位启用」，不得留空。
   - **依赖整洁**：`package.json`/lockfile 变更须记 diff；新增第三方库须落在 project-conventions 已批准槽位（状态/UI 库/认证等被锁选型不得擅自换）。
   - **未验证项**：无法本地验证的（真实 CMS/数据库联调、Vercel 部署后的边缘/Node runtime 行为、生产 `revalidate`/ISR 缓存实际失效、真实 SEO 抓取/OG 预览、跨设备/真机 H5 视口与首屏性能、NextAuth 真实回调）须显式列出并指明移交环节（CI / Preview 部署 / Manual QA / Lighthouse），不得隐瞒。

5. **D5 注释/日志/文档追溯核查**（维护性证据）：检查实现是否能让后续维护者从代码回到设计决策，并能在生产问题中定位 server/client 边界与关键链路。
   - 新增导出组件、`server-component`、`client-component`、`data-access` 函数、`server-action`、route 段入口、domain-type/zod schema，必须有 TSDoc/JSDoc 或等价注释说明职责、承接的 `UNIT-<slug>` / `BHV-NNN`；必要时附设计文档相对路径（`docs/design/.../chapters/<slug>.md` 或任务内 `design.md` 锚点）。缺失通常为 P2；高风险链路或新增核心 owner 完全无追溯为 P1。
   - 非显然 server/client 边界、缓存/`revalidate` 决策、鉴权、错误边界、hydration 规避、内容源兼容、SEO metadata 生成策略必须解释"为什么这样做"，不能只靠代码形状猜意图。缺失按 P2 处理。
   - 关键流程日志应覆盖 server 入口、成功收口、失败/降级、重试/恢复、外部依赖边界、`server-action` 变更结果；必须复用 project-conventions 日志槽位或项目 logger / observability 门面。生产散落 `console.log`/`console.debug`、吞错无日志、server-action 失败无上下文日志按 P2 起步，高风险不可观测路径按 P1。
   - 日志不得记录 secret、token、PII、完整请求体、cookie/session 或用户生成内容原文；client 侧不得输出服务端私密上下文。命中即 P1。
   - `implementation-evidence.jsonl` / `verification-evidence.jsonl` 应记录本次新增注释、日志、文档路径引用与无法覆盖的理由；缺记录为 P3，若导致审计不可复现为 P2。

6. **D6 合规红线 / Secret 与 server-client 边界合规**（对应 Gate 4 config/secret 合规 + 统一红线）：
   - **密钥落地**：代码、配置、`.env.example`、fixtures、测试资产、trace/mutable evidence 不得出现真实 API key、token、password、数据库连接串、签名密钥等 `secret_value`；只允许保存环境变量名引用、`credential_ref`。硬编码 secret = P1。
   - **server-client 秘密边界**（红线，不可豁免）：私密配置只走服务端 env（无 `NEXT_PUBLIC_` 前缀）且只在 server-component/data-access/server-action 读取；把私密 env、服务端 token、数据库句柄经 props 或 import 暴露到 `'use client'` 子树 = P1。仅前端可见值若误标私密、或私密值误加 `NEXT_PUBLIC_` 前缀外泄 = P1。
   - **认证合规**（认证槽位 NextAuth 启用时）：鉴权/会话校验须在服务端（middleware / server-component / server-action）完成，client 端只做 UI 态展示不做权限裁决；密钥来自 env，禁硬编码；回调/CSRF/session 策略与设计一致。
   - **`.env` 不作线上合同**：`.env` 仅本地开发引导，不得当生产配置合同；线上配置走部署平台（Vercel）环境变量。
   - **合规依据一致**：权限/数据采集（埋点、第三方 SDK、cookie/storage 使用）须与设计合规依据一致；新增采集而设计无依据 = P1。
   - 红线违例（server-client 边界破坏 / 私有数据获取下沉 client / 分层反向 / 硬编码 secret / 私密 env 外泄 / strict 倒退 / prettier·eslint 未过 / 未批准重型依赖替换被锁槽位）在对应判定直接 fail，不可豁免。

7. **D7 偏差闭合**（对应 Gate 4 G6）：PR diff 与计划逐项可对；所有计划外改动均有原因记录；上游结构性缺陷（归属错、合同越界、单元跟随名词而非行为、doc_type 用错名）已回退拥有该决策的阶段修订而非就地补造。对不上靠 reviewer 自己发现 = P2 起步；就地改设计 = P1。

## 输出（互斥分支）

**前置失败时**：仅输出前置缺口（缺哪个装载源 / 槽位 / trace / 详细设计单元 / doc_type 用错名）+ 最小修复动作；不进入任何符合性判断，不给结论 pass/fail。

**前置通过时**，按以下顺序输出：

1. **结论（三选一，置顶）**：
   - **可进入 PR**：D1~D7 全过；`implement.md` 计划合同齐全，mutable evidence 中当前 route/slice 类型要求的类型、lint、format、build、测试证据有命令级结果且全绿（Full/high ordinary 仅 packet focused checks，Integration 才含全项目 `tsc`/`next build`/full regression）、承接 UNIT 的成功 + 全部失败路径有测试、注释/日志/文档路径追溯可审计、无 P1、无清单外新增违例、无未闭合偏差、server-client 边界与 secret 合规。
   - **修复 P2 后可进入**：无 P1，但存在 P2（证据不完整、偏差未全闭合、非高风险漏测、`'use client'` 越界但有降级、metadata/SEO 字段缺失、绕行未挂编号等）；列出 P2 修复项。
   - **不可进入 PR**：存在任一 P1（合同未实现 / 八问断链 / 分层反向·越层 / server-client 边界破坏 / 私有数据获取下沉 client / 硬编码 secret 或私密 env 外泄 / strict 倒退 / 错误吞噬关键链路 / doc_type 用错名 / 清单外新增违例 / 高风险漏测 / 类型或构建未收口 / 证据造假 / 就地改设计）；逐条列阻塞 P1。验证因环境/凭据/CMS/网络阻塞无法完成时，结论为 blocked，记录命令、错误摘要、缺失依赖与恢复条件，不得降级为 pass。
   - 机器可读收口字段必须同步输出：clean 且可进入 PR 时写 `review_result=clean`（或 `review_result=final-verification-ready`，supervisor 归一为 clean）、`route_class=none`、`review_target=slice:<slice_id>`、`review_provider=<本 check worker 的 provider>`、`deterministic_checks=passed|failed|missing`、`dirty_scope=clean|isolated|invalid`、`invariant_coverage=all_passed|failed|missing`、`validation_summary=<命令与证据摘要>`。有 slice packet 时还须逐条输出 per-invariant：`invariant_status.<id>=pass|fail|not_applicable`；`pass` 必随 `invariant_evidence.<id>=<非空证据：测试名/命令/代码路径>`；`not_applicable` 必随 `invariant_reason.<id>=<理由>`。不得输出 `review_result=clean/final-verification-ready` 这类组合值。缺任一 gating 字段、或取非通过值却声明 clean、或 provider 不满足 packet `semantic_review_provider` → supervisor 判 `MALFORMED_REVIEW_OUTPUT` 阻断。有 finding 或阻塞时写 `review_result=findings|blocked` 与最高优先级 `route_class`。
   - route class 只能取：`IMPLEMENT_DEFECT`（代码/测试/验证/注释/日志/脱敏缺陷）、`PROCESS_DEFECT`（trace/证据/流程执行缺陷）、`DETAIL_DEFECT`（详细设计合同错误或缺失）、`OVERVIEW_DEFECT`（概要归属/承接错误）、`REQ_BLOCKER`（需求行为/验收/边界缺陷）、`none`。

2. **逐条 Findings**（按 `P1 → P2 → P3` 排序；无则写 `none`），每条字段：
   ```md
   ### P<1|2|3> <标题>
   - route_class：`IMPLEMENT_DEFECT|PROCESS_DEFECT|DETAIL_DEFECT|OVERVIEW_DEFECT|REQ_BLOCKER`
   - 设计证据：`<UNIT-<slug>#八问几 / BHV-NNN / detail_doc_type（七类之一）/ 详细设计文件:章节>`
   - 代码证据：`<app|components|lib|actions|types/<file>:行 / 组件 / 函数 / 'use client' 边界位置 / metadata / 验证位置>`
   - 存量证据：`<命中的 [SLOT-NN] 条目 / 清单外；不适用写 N/A>`
   - 问题：`<代码与详细设计或 golden-path 红线的具体偏离>`
   - 影响：`<为何导致合同不闭合 / 验证不可信 / 边界·红线破坏 / 无法判断>`
   - 建议（最小修订）：`<修代码 | 补/复跑验证 | 移除越界结构 | 回退详细阶段修订 | 挂 SLOT-15 记债 | 恢复验证环境>`
   ```
   同一轮多类缺陷按 `REQ_BLOCKER > OVERVIEW_DEFECT > DETAIL_DEFECT > PROCESS_DEFECT > IMPLEMENT_DEFECT` 给最高优先级路由，供 implement-check 自动回退。
   先证据后结论，严重度排序：
   - **P1**：合同未实现 / 执行流程步骤缺失·改序·下沉·上移无设计依据 / 八问断链（幽灵 BHV·UNIT）/ 实现阶段猜测发明未定义合同 / high-risk slice 缺 packet 或 invariant 失败 / 分层反向·越层 / server-client 边界破坏（client 直取私有数据·secret 透传客户端·私服模块 client 端 import）/ 高风险核心 owner 完全无文档追溯 / 高风险路径不可观测 / 日志泄露 secret 或 PII / 私密 env 外泄 / 硬编码 secret / TS strict 倒退 / 关键链路错误吞噬·缺错误边界 / doc_type 用错名（非七类）/ 清单外新增违例（含扩大违例面）/ 高风险链路漏测 / 当前 route/slice 类型要求的类型或 build 未收口 / 证据与复跑不符 / 就地改设计而非回退。
   - **P2**：当前 route/slice 类型要求的类型/静态/构建/测试证据不完整（无命令·无退出态·无测试名）/ 非高风险失败路径漏测 / invariant 证据字段不完整但未影响 high-risk 阻断语义 / 新增导出组件或核心函数缺 TSDoc/JSDoc 设计锚点 / 非显然 server-client 边界或缓存策略缺"为什么"注释 / 关键流程日志缺入口或失败上下文 / `'use client'` 越界但有降级 / metadata·SEO 关键字段缺失 / 偏差未全闭合靠 reviewer 发现 / 触碰存量绕行未挂编号 / 计划与验证命令轻微不一致但未绕过实现 / 因环境阻塞验证未完成。
   - **P3**：命名、目录/文件组织、注释措辞、验证记录可读性问题，不影响合同闭合与红线。

3. **存量豁免清单**：本次触碰的 SLOT-15 条目 + 分类结果（记债不阻塞 / 新增阻塞 / 可移除）+ 对应 `[SLOT-NN]` 编号。

4. **注释/日志/文档追溯摘要**：覆盖的新增核心定义、日志点、设计文档路径引用，以及缺口和判级。

5. **验证命令汇总**：每条 `command / status(passed|failed|not_run|blocked_by_environment) / evidence(输出摘要或日志) / blocker`。未执行或环境阻塞的验证、失败的必要命令均不得支撑「可进入 PR」。

6. **反哺建议（可选）**：本次暴露的新模式/新坑 → 建议更新 golden-path、harness 标准包或 project-conventions 槽位定义的具体条目（如新增 SLOT-15 记债项、补 golden-path 禁止清单条目、补某 pending doc_type 的 L2 详例）。

## 好例 / 坏例（审核判读对照）

- ✅ 合格 ordinary 切片（放行）：`切片 S3 | 承接 UNIT-post-data-access（detail_doc_type=data-access）| lib/posts.ts`；`verification-evidence.jsonl` 记录 packet focused checks：`eslint lib/posts.ts → 0 problems`、`prettier --check lib/posts.ts → 0`、`vitest run posts.test.ts` 含 `✓ getPostBySlug 命中`、`✓ getPostBySlug not_found 返回 null（失败路径）`，新增测试映射到 `UNIT-post-data-access` 覆盖 `BHV-007` 成功 + 失败路径；全项目 `tsc --noEmit`、`next build` 与 full regression 留给 Integration；私有内容源只在 data-access 经服务端 env 读取，真实 CMS 联调显式留 Preview 部署。审核判：可进入 PR。
- ❌ 坏例（不可进入）：`client-component`（`'use client'` 文件）里直接 `import { db } from '@/lib/db'` 并读私有数据（D2/D5 server-client 边界破坏，P1）；server-component 把 `process.env.API_SECRET` 经 props 透传给 `'use client'` 子组件（D5 私密 env 外泄，P1）；`error.tsx` 漏写或未标 `'use client'`、catch 后空处理吞掉变更失败（D2 错误边界，关键链路 P1）；mutable evidence 只写「编译通过、测试通过」无命令无退出态无测试名（D4，P2）；详细设计单元把 `detail_doc_type` 写成 `repository`/`controller`（照搬 flutter/Go 类型名，非七类，D6，P1）。
- ❌ 坏例（八问断链 / 旧形态误放行）：切片挂 `UNIT-photo-gallery` 但详细设计无此单元（幽灵单元，P1）；或以 `style jsx` 全局注入、Pages Router 目录、`strict: false` 等旧形态作为合规依据放行 App Router 项目（D2 旧形态非生产基准，按所掩盖的违例判级）。

## 边界约束

- 只审改动面 + 其直接依赖；不对存量代码做全量审计（存量违例只走 SLOT-15 豁免判定）。
- 审核不代写代码；每条 finding 给最小修订方案。
- 规则正文不在本 skill 复写——分层依赖律、各层迷你路径、server-client 边界规则、禁止清单以 `.trellis/spec/guides/golden-path.md` 为准；trace 计划合同、mutable evidence 边界、Gate G1~G6 以 `.trellis/spec/harness/implementation/implementation-trace-contract.md` 为准；BHV/UNIT 编号纪律、doc_type 七类、统一红线以 `.trellis/spec/harness/index.md` 为准；槽位取值与 SLOT-15 以 project-conventions 为准。
- 判定基准一律为 App Router 生产 golden-path；任何把仓库内残留旧形态（Pages Router / `strict: false` / 全局样式注入）当合规模板的放行都视为误判。
- 未执行的验证不得写成通过；测试失败/证据缺失/环境阻塞如实输出，不降级结论。
- 新增测试不能替代设计或实现证据；通过业务流程/集成/e2e/mock/fake 测试反向定义业务语义、测试补写详细设计 = P1，应回退详细或测试计划阶段。
- 不得要求 OCR 作为默认完成条件；OCR 仅 optional bounded provider（用户显式触发 / 高风险抽检），记 `channel=ocr_optional`，第一版不满足 required provider。
- manual provider 审查留痕（非 channel spawn，第一版 supplemental 补充审计、不满足 required provider）必须经验证型 append：
  ```bash
  python3 .trellis/scripts/guru/guru_review_record.py append --task-dir <task> --packet <packet> \
    --provider manual --reviewer <name> --run-id <run_id> --result clean --route-class none \
    --review-target slice:<slice_id> --deterministic-checks passed --dirty-scope isolated \
    --invariant-coverage all_passed --evidence-file <task>/review-records/manual-review-<run_id>.md
  ```
  `--run-id` 必须与 `--evidence-file` 名一致；`channel` / `worker` 由命令派生。

## 与官方 Trellis skill 的边界

本 skill 是 `trellis-check` 在 Guru H5（Next.js）项目的领域化审核口径——在官方 lint/typecheck（`tsc`/`eslint`/`next build`）之上，叠加领域化的合同八问闭合、分层依赖律 + server-first/`'use client'` 最小化/server-client 边界/metadata-SEO/样式隔离/错误边界 canonical、Secret 与 server-client 边界红线、doc_type 七类核对与 SLOT-15 存量豁免判定，并落到实现 Gate G1~G6 与 PR 准入结论。官方检查跑工具级机检结构，本 skill 跑「代码是否承接已审核详细设计、是否守红线、证据是否可信」的语义判定，二者叠加执行、互不替代。结构机检（trace 计划合同、mutable evidence、切片挂 UNIT、断链、doc_type 名合法性）由 `guru_gate.py implement <task_dir>` 同口径执行，本 skill 复用其判定项而不复制其实现。
