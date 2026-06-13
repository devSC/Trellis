# H5 详细审核取证矩阵与严重度判级（references）

> 编排层产物：只承载逐 doc_type 取证操作、判级细则与一份最小成稿示例；规则正文与完成条件（G1~G8）以 L1
> `.trellis/spec/harness/detail/detail-structure-single-source.md` 为唯一来源，类型差异以命中 L2（`detail-type-{server-component,client-component,data-access}.md`）为准。冲突时 **L1 > L2 > references > SKILL.md**。
> 本文不复写 L1/L2 规则正文：每条取证操作都回指 L1 章节号（§N）/ L2 / golden-path 条目。本文的 D1~D8 与 G1~G8 编号即 SKILL.md 诊断流程与 L1 §8 Gate 的同名项；横向硬规则真源 `.trellis/spec/guides/golden-path.md`，项目槽位 `.trellis/spec/harness/detail/detail-structure-single-source.md` §6（路由模式 / 内容源 / 状态 / UI 库 / 样式 / 测试 / lint / 数据库 / 认证 / 图像 / 部署）。
> 平台基线：Next.js（**App Router 生产形态为目标**）+ React + TypeScript(strict)。`doc_type` 一律用 L1 §1 钉死的 **H5 七类**（`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`），禁止照抄 flutter（page-entry/controller/usecase/repository-datasource）或 Go（entry-api/biz/repository-data）类型名。

## 0. 完成条件锚点对照（取证前先固化）

L1 §8 钉死的完成条件为 **G1~G8**（G1~G5 两轨共用；G6~G8 仅 full 链强制）。本文逐文档矩阵的「受影响 G 项」列一律回指此处，不另立编号：

| G 项 | 主题（L1 §8） | 闭合口径一句话 |
|------|---------------|----------------|
| G1 | 承接索引覆盖 | 承接索引每个条目都有对应详细单元，无遗漏（覆盖率闭合） |
| G2 | 八问 + 追溯 + 粒度 + 分层 | 每单元八问完整；字段/接口/状态可追溯概要 owner；满足 §3.1 粒度；无 §2.1 分层依赖律违例 |
| G3 | 测试映射 | 每条行为有测试映射（八问 7），覆盖成功 + 全部失败路径 |
| G4 | 边界与合规 | 私有数据/secret/session/三方域名/PII 单元附 §2.2 边界依据；secret 仅落 server 边三类；无私有 API key 明文 / 动态执行 / 制裁 TLD |
| G5 | 不得补造清单 | 八问 8 逐单元存在，含 §2.1 越层反面项 |
| G6 | 章节闭合 + 骨架 | 索引↔chapters/ 双向闭合；每章符合 §4 骨架；pending L2 命中项豁免齐全（§2.5） |
| G7 | chapter_loop 证据 | 逐章 `chapter_status=passed_by_method_evidence`，七层 checkpoint 全过，无一轮全量生成迹象 |
| G8 | 编号断链全清 + doc_type 合法 | `BHV-NNN`/`UNIT-<slug>` 双向闭合，无幽灵/悬空/重号/方向违例（§3.2）；doc_type 全程只用 §1 七类 token |

> 注：SKILL.md 输出节按链型把 G6~G8（full 链强制）在 light 链标 `N/A(light)` 并说明单文件口径已满足。directory_final 的目录级结论必须对 G1~G8 逐项给证据，不得用「基本满足」替代。

## 1. 取证准备（所有 scope 模式先做）

1. 固化编号与小节锚点（被审章节文件）：
   - `rg -n "UNIT-|BHV-" <章节文件>` 固化设计单元与承接行为编号（D3 断链取证、Finding location 引用都依赖它）。
   - `rg -n "^#{1,4} " <章节文件>` 固化小节锚点（D1 模板节打钩用）。
   - `rg -n "doc_type|l2_status" <章节文件>` 固化头部标注（D1 用：`doc_type` 落七类、`l2_status` v1/pending 标注）。
   - **执行边索引**：`rg -n "'use client'|server-only|process\.env|revalidate|generateMetadata" <章节文件>`，为 D4/D7（server/client 边界与 secret 红线）建立候选行。
   - **类型名越界扫描**：`rg -ni "controller|usecase|repository|datasource|handler|service|biz|entry-api|page-entry" <章节文件>` — 命中即疑似照抄 flutter/Go 类型名（落到 `doc_type` 头部或承接引用即 P1，D1 拦截）。
2. 概要侧基线先取证（后续全部双向核对以此为准，不在详细侧重建）：
   - `design-main.md` 归属判定表 owner 集合（七类 doc_type × `UNIT-<slug>`）；
   - 第 7 节详细设计承接索引目标集合 `chapter_target → detail_doc_type → chapters/<slug>.md`（含 `l2_status`）；
   - UC 承接表 `bhv_refs`/`index_refs`、时序图策略表；
   - `technology_decision_handoff[]` 的选定状态（映射 L1 §6 路由模式/内容源/状态/UI 库/样式/数据库/认证/图像/部署槽位）。
3. 机器 Gate 先行（人工不重复机检，结构 findings 直接并入）：
   - `python3 .trellis/scripts/guru/guru_gate.py detail <task_dir>`（合同八问标记、章节闭合、pending L2 拦截）；
   - 编号断链（幽灵 BHV / 悬空行为 / 幽灵 UNIT / 重号 / 方向违例编号，L1 §3.2）由机检定位，人工只补语义判定。
4. 命中 doc_type 后装载对应 L2（只装命中类型，不全量装）：`server-component`→`detail-type-server-component.md`（render）、`client-component`→`detail-type-client-component.md`（interactive）、`data-access`→`detail-type-data-access.md`（data）；pending 四类（`route`/`ui-component`/`domain-type`/`server-action`）不装 L2，按 L1 §3 合同八问展开，并核查 `l2_status: pending` 头标与 design-main `L2豁免：<doc_type> 理由：…` 声明（L1 §2.5）。
5. 跨层下游合同取证（D3/D4 用）：被审单元八问 4 声明的依赖逐条到对应章节文件，核对被调用的下层组件行为名/取数合同/action 签名确实存在，且方向符合 §2.1。

## 2. 通用诊断矩阵（七类 doc_type 共用，对应 D1~D8）

每条 Finding 必须带「文件 + 小节/表格行/TS 签名」锚点或明确缺失对象，并回指规则（`rule_ref=<规范文件#锚点>`）。

| 诊断 | 取证操作（先证据） | 缺口判级 | rule_ref（默认回指） |
|------|------------------|---------|---------------------|
| **D1 骨架符合性** | 对照 L1 §4 模板节逐节打钩：① 单元职责 ② 行为定义（清单 + TS 签名）③ 核心数据结构（含错误类型表）④ 逐行为设计（含 `mermaid sequenceDiagram`）⑤ 状态/边界管理 ⑥ 路由/渲染/SEO（route 必含，其余 N/A）⑦ 测试映射 ⑧ 不得补造清单。N/A 节须有声明；头部 `doc_type` ∈ 七类、`l2_status`（v1 三类标 v1/full，pending 四类标 pending）标注正确。 | 缺模板节 P1；N/A 节无声明 P2；`doc_type` 越七类（照抄 flutter/Go 名）P1；pending 类型缺 `l2_status: pending` 或缺 design-main `L2豁免` P1 | `detail-structure-single-source.md#§4-章节正文骨架合同` |
| **D2 八问完整性** | 逐 `UNIT-<slug>` 按 L1 §3 合同八问括号内可验证信号取证（① 承接 `BHV-NNN` ② 输入/输出/错误结果，RSC 含「数据获取入参→取数→渲染产物」链 ③ 读写状态与 owner ④ 调用依赖正反两面 ⑤ 失败收口 ⑥ 事件/后置（revalidate/redirect/cache 失效，逐条写消费方）⑦ 测试映射 ⑧ 不得补造）；命中 v1 类型叠加 L2 特化问。 | 任一问缺 P1 | `detail-structure-single-source.md#§3-合同八问所有-doc_type-通用骨架` |
| **D3 追溯核查** | `UNIT ↔ BHV` 双向闭合（裸 token）：UNIT 承接的 `BHV-NNN` 在 prd 存在、prd/概要已归属的 BHV 至少被一个 owner 单元承接；状态写 owner 回指概要归属表行且层一致；八问 4 依赖出现在概要架构图边上，且方向符合 §2.1。 | 幽灵 BHV / 悬空行为 / 幽灵 UNIT / owner 不一致 / 依赖无承接 P1 | `detail-structure-single-source.md#§32-编号断链拦截强制-gate-规则` |
| **D4 分层一致性** | 八问 4 依赖正反面对照 §2.1 分层依赖律（服务端链 `route→server-component→data-access→domain-type`、交互链 `client-component→ui-component`、变更链 `server-action→data-access`）+ 命中 L2 硬规则逐条（client-component 不直 import data-access/server-action 私有取数；server-component 不 import client-component 内部状态；ui-component 不反向依赖任何上层；domain-type 不反向依赖任何运行层；无环）。 | 任一违例 P1（阻断，不给通过性结论） | `golden-path.md#21-分层依赖律最重要归属硬基准违反-fail`、`detail-structure-single-source.md#21-分层依赖律归属硬基准违反-fail` |
| **D5 粒度判定（含签名级）** | 接口签名级（L1 §4.2.2）：渲染函数 props 类型、data-access 取数合同签名、server-action action 签名、client-component props + 回调签名齐全；可穷举概念用具名 union/enum，禁裸魔法值；超签名级实现体（>15 行实现体视为越界信号，D8 联动）。粒度（L1 §3.1 四条）：抽查 ≥1 行为全流程——每步有具体被调用的下层行为名 + 参数（如 `getPostBySlug(params.slug)`/`CommentRepository.insert(input)`）、本单元内部判定、失败返回/收口点、状态写入点、server↔client 边界数据流。 | 非签名级（「提供 XX 能力」无签名）P1；「见概要」「处理 XX」无调用对象 P1；server/client 边界数据流断点 P1；魔法值 P2 | `detail-structure-single-source.md#31-粒度标准四条写作与审核共用` |
| **D6 测试映射** | 每条承接行为 ≥1 成功用例 + 全部失败路径各 1 用例，逐行映射 `BHV-NNN`/`UNIT-<slug>`；测试层合理（RSC/数据层 Vitest+RTL 或集成、交互流 Playwright E2E，按 L1 §6 测试槽位）；成功+失败路径覆盖。 | 高风险链路（认证/支付/数据删除/server-action 变更）漏测 P1；普通失败路径漏测 P2；测试层错配 P2 | `detail-structure-single-source.md#§3-合同八问所有-doc_type-通用骨架`（八问 7） |
| **D7 合规核查（server/client 边界 + secret 红线）** | 私有数据获取 / 内容源访问 / secret / `process.env` 私有变量 / 带鉴权 token 的 fetch / DB 连接只允许在 `server-component`/`data-access`/`server-action`；`client-component`/`ui-component` 禁直取（只接收脱敏 props 或调用 action 引用）。`rg -i "secret\|api_key\|access_key\|token\|password\|NEXTAUTH"` 扫硬编码凭证；`.env` 当线上配置合同 / 制裁 TLD / 私有 API / 动态执行（`eval`/`new Function`/未净化 `dangerouslySetInnerHTML`）/ 全局样式污染扫描；`'use client'` 最小化（仅交互叶子，不裹可服务端渲染子树）；跨 server→client props 须可序列化。 | client-component/ui-component 直取私有数据或持 secret P1；真实 secret value / `.env` 当线上合同 P1；私有 API / 动态执行 / 制裁 TLD P1；`'use client'` 过度蔓延 P2（污染主链或致私有数据下放升 P1）；全局样式污染 P2；不可序列化 props 跨界 P2 | `golden-path.md#22-server-client-边界h5-平台特有最高优先级硬规则`、`detail-structure-single-source.md#22-硬规则golden-path-锁定` |
| **D8 补造红线 + 层级越界** | 概要外结构、改 owner、改 doc_type 名、私自拍板未选定技术决策（替概要选内容源/状态管理/UI 库等）、超签名级实现体（>15 行）、把私有数据/secret 下沉 client、引入 §2.1 反向边/越层调用、偏离 §6 项目约定槽位取值。异常表逐行对应一条失败路径 BHV 或八问 1 行为分支；错误转换位置（`error.tsx` / data-access 转换点 / action 返回）两侧一致。 | 补造 / 改 owner / 改 doc_type 名 / 拍板未选定决策 / 越界实现体 / 层级越界 P1；异常表↔失败 BHV 失配、错误转换位置缺标 P2 | `detail-structure-single-source.md#91-禁止补造清单`、`golden-path.md#7-禁止清单汇总门禁拦` |

> 说明：SKILL.md 诊断流程把「骨架」为 D1、「八问」D2、「追溯」D3、「分层」D4、「粒度（含签名级）」D5、「测试」D6、「合规（边界/secret）」D7、「补造红线+层级越界」D8，本表与之一一对齐；L1 §8 的 G2 同时覆盖本表 D2/D4/D5（八问、分层、粒度合并判定），G4 覆盖 D7，G5 覆盖 D8 的八问 8。

## 3. 逐 doc_type 附加检查

### 3.1 v1 类型（按 L2 逐条硬规则；只装命中类型，不全量装）

| doc_type | 附加取证（命中 L2 硬规则） | 典型 P1 | rule_ref |
|----------|--------------------------|---------|----------|
| `server-component`（render，L2: detail-type-server-component） | RSC 默认无 `'use client'`；数据获取经 `data-access` 编排（`async` 内 `await` 或下沉封装），不在此写 `useState/useEffect`；私有数据/secret 仅服务端持有；下传 client 的 props 已脱敏且可序列化；Suspense/loading 边界声明；只 import `data-access`/`domain-type`/`ui-component`/`client-component`（嵌入）。 | 标 `'use client'` 后仍直取 DB/secret；把私有数据原样下传 client；在 RSC 内写交互态；import client-component 内部状态做数据获取主链 | `detail-type-server-component.md`、`golden-path.md#server-component-迷你路径` |
| `client-component`（interactive，L2: detail-type-client-component） | 顶部 `'use client'`；状态字段 + 初始态 + 三态（loading/success/error）显式，写 owner 声明；只消费 props 或调用 server-action 暴露引用；只依赖 `ui-component`(+`domain-type` 仅类型导入)；`'use client'` 范围最小化（不裹可服务端渲染子树）；状态管理选型符合 L1 §6 状态槽位。 | 直接 import/调用 `data-access` 私有取数；client 内直取 env/secret / `useEffect+fetch` 取首屏私有数据；把整页提为 client；import `server-component` | `detail-type-client-component.md`、`golden-path.md#client-component-迷你路径` |
| `data-access`（data，L2: detail-type-data-access） | fetch 封装 / 内容源（MDX·gray-matter·CMS）/ ORM 查询；显式缓存语义（`fetch` 带 `cache`/`next.revalidate`，禁隐式默认）；错误转换表逐枚举并向上抛（不静默吞错返回空冒充成功）；返回值可序列化、按 `domain-type` 收敛；可读私有 env/凭证（`import 'server-only'` 保险栓）；无业务规则判定；不 import `server-component`/`route`（反向）；不被 `client-component`/`ui-component` import。 | 含业务规则判定；被 client-component 直接 import；secret 硬编码；catch 后返回 `[]` 冒充成功；缺显式缓存语义 | `detail-type-data-access.md`、`golden-path.md#data-access-迷你路径`、`golden-path.md#23-数据获取data-fetchingcanonical` |

### 3.2 pending 类型（L1 八问 + 豁免核查；不装 L2）

通用先核：头部 `l2_status: pending` 标注存在；full 链 design-main 须有对应 `L2豁免：<doc_type> 理由：…`（无豁免 → gate 拦截 P1，L1 §2.5）。各类附加取证：

- **`route`**：route 段文件职责（`page/layout/loading/error.tsx`）齐全或 N/A 声明；`metadata`/`generateMetadata` 承接（生产级补充，示例手写 `<Head>` 不充数）；动态段声明 `generateStaticParams` 策略；只编排 + SEO，不承载业务规则或数据访问实现细节（数据编排下放 `server-component`，简单页 page.tsx 自身充当 server-component 不算跳层）；`error.tsx` 必 `'use client'`、错误边界 owner 唯一；保留文件名不可改名。出现业务规则/数据访问实现 → P1（回退到 server-component/data-access）。
- **`ui-component`**：纯展示，八问 8 必含「不拥有数据获取/业务判定/状态」；样式隔离（CSS Modules/Tailwind，不写全局污染）；props 签名级、可序列化；不 import `data-access`、不依赖 `client-component`（交互链反向）；默认不标 `'use client'`（如需局部交互态应升级为 client-component）。出现取数/业务判定/全局样式/反向依赖 → P1。
- **`domain-type`**：TS 类型 / zod schema / 领域模型；跨 server→client 对象在此定义可序列化形态（如 `date` 用 ISO 字符串）；schema 由谁校验写明（server-action/data-access 入口）；零副作用、零 I/O、零 React，不 import 任何其他六类。type 层反向依赖任意运行层 / 带 I/O → P1。
- **`server-action`**：`'use server'` 或 route handler 边界；入参 zod 校验回指 `domain-type` schema；经 `data-access` 完成变更（不直连 DB driver、不重复写 data-access 逻辑）；`revalidatePath`/`revalidateTag` 与错误返回约定，消费方闭合；认证/授权依据（命中认证槽位，session 只在服务端读）。绕过 data-access 直拼查询 / 在 client 内内联定义 server 逻辑 / 被 data-access 反向依赖 → P1。

## 4. 跨链链路核对（directory_final 第②段 / layer_checkpoint）

| 链边界 | 核对项 | 缺口判级 | rule_ref |
|--------|--------|---------|----------|
| route→server-component（route checkpoint） | route 只编排 + 段约定（page/layout/loading/error）+ metadata/SEO；page 调用的 server-component 存在；错误边界 owner 唯一；不跳层直堆复杂取数 | route 承载业务/取数 P1；段约定缺承接 P2（核心入口升 P1）；metadata 缺失 P2（生产级补充） | `detail-structure-single-source.md#§54-层级-checkpoint`（路由层后） |
| server-component→data-access（数据层/渲染层 checkpoint） | server-component 声明的数据依赖有承接 `data-access` 章节；返回类型为 `domain-type`；错误转换两侧一致；缓存/重验证决策只在 data-access；私有数据/secret 不外泄 | 依赖无承接 P1；secret 外泄 P1；类型不闭合 P2；错误转换位置失配 P2 | `detail-structure-single-source.md#§54-层级-checkpoint`（数据层/渲染层后） |
| data-access→domain-type（合同层 checkpoint） | 查询返回与 `domain-type`/zod schema 一致；schema 校验位置写明；domain-type 被引用方 import 路径成立、不反向依赖 | 类型漂移/无 schema P2；domain-type 反向依赖运行层 P1 | `detail-structure-single-source.md#§54-层级-checkpoint`（合同层后） |
| client-component→ui-component（交互层/展示层 checkpoint） | client 只调用 ui-component 展示 / server-action 变更；状态订阅有发射方；`'use client'` 不上提；三态完整；ui-component 纯展示无 fetch/无业务/样式隔离 | client 直连 data-access P1；状态无 owner P1；ui-component 取数/业务/全局样式 P1 | `detail-structure-single-source.md#§54-层级-checkpoint`（交互层/展示层后） |
| server-action→data-access（变更层 checkpoint） | 变更经 data-access；`revalidatePath/Tag` 消费方闭合；表单/输入校验回指 domain-type schema；认证依据存在 | 绕 data-access 直拼查询 P1；缺 revalidate 消费方 P2；缺认证依据（命中认证槽位）P1 | `detail-structure-single-source.md#§54-层级-checkpoint`（变更层后） |
| server/client 全局边界 | 私有数据/secret 不跨入 client；同一数据/状态 owner 全局唯一；同一错误枚举跨章一致；跨界 props 可序列化 | secret 越界 P1；多写 owner P1；错误枚举跨章漂移 P2；不可序列化 props P2 | `golden-path.md#22-server-client-边界h5-平台特有最高优先级硬规则` |

## 5. 覆盖率核对（directory_final 第③段）

1. **索引↔章节双向差集**：概要承接索引目标集合 vs 现存 `chapters/<slug>.md`：缺失目标文档只出「缺失结论 + 修订方案」（不进 D 诊断）；孤儿章节（有文件无索引条目）P1。归属表全部 owner 被索引覆盖（双向闭合）。
2. **归属表 owner 覆盖**：每个 owner（七类 doc_type）被至少一个 `UNIT-<slug>` 覆盖。
3. **UC 链路抽查**：UC 承接表 `index_refs`/`bhv_refs` vs 章节：每个 UC 的链路在详细侧（服务端链 `route→server-component→data-access→domain-type` 或交互/变更链 `client-component→server-action→data-access`）全链可达、无断点。
4. **时序↔行为抽查**：概要时序图参与者/调用 vs 详细逐行为设计：抽查 ≥1 个 UC 的时序步骤在对应章节有同名行为（裸 token 对得上）且调用方向一致；`sequenceDiagram` 不得出现 `client-component → data-access` 直连边（交互取/写数据须经 server-action 或经 route 的 server-component 加载链）。
5. **SEO/metadata 覆盖**：概要声明需 SEO 的 route 在详细侧有 `metadata`/`generateMetadata` 承接（生产级补充）；`technology_decision_handoff[].detail_expansion_targets` 有承担它的目标 doc_type 章节。

## 6. 薄文档判定（优先于逐条 finding）

满足任一即判薄文档 → 结论直接「不可进入」+ 文档级重构（L1 §9），不再逐条列局部 finding：

- ≥2 章骨架雷同且无单元级实质内容：小节结构相同且正文为占位级（输入/输出参数表空 / 接口无 TS 签名 / 逐行为流程详述 <3 步 / 测试映射 ≤1 行 / 八问多问写「见概要」「同 flutter」/ 缺 `mermaid sequenceDiagram` 与异常表 / 普遍缺 server/client 边界数据流标注）。
- 全目录一次性全量生成迹象（违反 L1 §5.3 chapter_loop「每批 1~3 章、禁一轮全量」）叠加上一条任意命中：`chapter_status` 普遍缺失 / 无批内自动审修痕迹。
- 分层归属系统性错位（client-component 大面积直取数据、route 大面积承载业务规则、ui-component 大面积取数、domain-type 大面积反向依赖运行层）。

薄文档命中时输出薄文档证据（雷同章节对照 + 占位统计：空参数表数 / 无签名方法数 / `sequenceDiagram` 缺失章数 / 测试映射 ≤1 行的章数），不逐条列局部 finding。

## 7. 严重度判级规则（L1 §8.1）

- **P1（阻断）**：D1~D8 表中标注 P1 的项；§4 跨链 P1 项；薄文档；章节闭合失败、编号断链（机检并入，幽灵/悬空/重号/方向违例）；§2.1 分层依赖律违例；§2.2 硬规则违例（非 strict、`'use client'` 取私有数据、secret 边界泄漏、route 段约定缺、错误边界静默吞错）；doc_type 越七类；八问缺项；pending L2 缺 `L2豁免`——红线违例不可豁免、不给通过性结论。
- **P2（应修）**：表中 P2 项；粒度局部不达标（单个行为）；类型漂移；`metadata`/`revalidate` 缺失（非核心入口）；错误转换位置缺标；异常表逐行失配；样式污染；不可序列化 props；孤儿合同；`'use client'` 误用未污染主链；测试漏普通失败路径。
- **P3（建议）**：表述/格式/术语一致性；命名规范建议；示例实证未标注来源（不做「有没有写某个词」的纯形式检查）。
- 判级冲突取高；同根因合并为一条 finding 列全部位置；影响主链的 P2 升 P1。
- 详细设计文档无存量豁免（存量豁免只在实现阶段对代码生效，不为详细设计缺陷开口）。

## 8. 结论判定（互斥三选一，L1 §8）

- 任一 P1 → **不可进入编码**（阻塞 P1 清单 + 修订形态：局部修订 / 文档级重构按 L1 §9；概要缺陷标注「回退概要」）。
- 仅 P2 且每条有明确修订路径 + 用户已记录假设 → **带明确假设可进入**（逐条假设、依据、验证时点）。
- 无 P1/P2（P3 可遗留）→ **可进入编码**。
- 前置失败（EX-1~EX-6 任一）→ 不进入本节，按 `references/review-output.md` 分支一输出前置缺口。
- 结论为「可进入 / 带假设可进入」时必须给 Gate 收口指引（用户终端 `guru_gate.py confirm detail <task_dir>`，strict 模式 agent 不得代跑；详见 SKILL.md「Gate 收口」节）。修订形态判定只引用 L1 §9。

### 8.1 修订形态判定（L1 §9）

- **局部修订**：补错误枚举、补测试映射、补一条依赖声明、补一张 `sequenceDiagram`、补 `metadata`/`revalidate` 项、补一条 `'use client'` 边界说明、补一条不得补造项、补错误转换位置标注。
- **文档级重构**：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档）、doc_type 系统性误用、依赖方向系统性违例（client 普遍直取数据 / server-action 普遍绕 data-access）。
- 概要缺陷（归属错、索引漏、技术决策/槽位未选定）→ 回退概要修订，禁止在详细阶段就地改归属或私自拍板。

## 9. 最小成稿样例（`server-component` + `data-access` 双单元，锚定 blog 示例真实单元）

> 证据基准：blog 示例 `/Users/devSC/Documents/MyProject/next.js/examples/blog` 的内容读取逻辑实证于 `scripts/gen-rss.js`（`fs.readdir(pages/posts)` + `gray-matter` 解析 frontmatter，取 `frontmatter.data.title/date/description/tag/author`），frontmatter 字段模型实证于 `pages/posts/pages.md`（`title/date/description/tag/author`）。该示例本体是 Pages Router 简化形态（`tsconfig.json` 实证 `strict:false`/`target:es5`，无 `data-access` 模块、无 server-component），下方把同一**内容模型**（列出全部文章 / 按 slug 取单篇）重投影为 **App Router 生产形态**的 `data-access`（`getAllPosts`/`getPostBySlug`）+ `server-component`（`PostListServer`）双单元，凡示例可直接验证处标 `[示例实证]` 并给文件锚点，凡生产补充处标 `[生产级补充]`。**这是表达形态示例，不是要审核者照抄；审核仍以本文件 §2~§8 矩阵为准。**

### 9.1 章节头（D1 取证点）

```markdown
# UNIT-posts-source 详细设计

> doc_type：data-access ｜ l2_status：v1（命中 detail-type-data-access.md，不需 L2豁免）
> 承接索引：design-main.md 第 7 节 UNIT-posts-source ｜ 返回：[design-main](../design-main.md)
> 项目约定：route_mode=App ｜ 内容源=MDX ｜ 状态=none ｜ 样式=Tailwind（见 L1 §6 槽位）
```

审核：`doc_type ∈ 七类`✅、`l2_status=v1`（命中 `detail-type-data-access.md`）✅；若头部写成 `repository`/`datasource`（flutter/Go 名）→ **D1 P1（doc_type 越七类）**。

### 9.2 单元职责 + 接口签名（D1/D2-①②/D5 取证点）

```markdown
## 1. 单元职责
UNIT-posts-source：文章内容源访问 owner（data-access，server-only）。封装 MDX frontmatter 读取与 zod 校验，对外暴露按 domain-type 收敛的结果。
- 调用：内容源读取（MDX/gray-matter，[示例实证] scripts/gen-rss.js）、UNIT-post-schema（domain-type，zod 校验）。
- 被调用：UNIT-post-list-server（server-component）经 import 消费；不被 client-component/ui-component import。
- 依赖方向：只依赖 domain-type（符合 §2.1 服务端链底层，零反向）。

## 2. 行为定义
### 2.1 行为清单
- getAllPosts — 列出全部文章（按 date 倒序）— 承接 BHV-001
- getPostBySlug — 按 slug 取单篇 — 承接 BHV-002
### 2.2 接口定义（TypeScript 签名级）
``ts
import 'server-only';
export function getAllPosts(): Promise<Post[]>;
export function getPostBySlug(slug: string): Promise<Post | null>;
``
```

审核：八问①承接 `BHV-001/002` 裸 token（D3 回 prd 核对存在）；八问②签名级（`Promise<Post[]>`/`Promise<Post | null>` 返回类型齐全，D5 通过）；八问④依赖正反两面齐全（D4 对照 §2.1——只依赖 domain-type、不被 client import，`import 'server-only'` 保险栓声明，通过 D7 secret 边界）。

### 9.3 核心数据结构 + 错误类型表（D2-②⑤/D8 取证点）

```markdown
## 3. 核心数据结构
### 3.1 数据模型（owner=UNIT-post-schema，domain-type）
Post = PostFrontmatter & { slug: string; content: string }；PostFrontmatter = { title; date(ISO 字符串，跨 server→client 可序列化); description?; tag; author }（字段模型 [示例实证] pages/posts/pages.md）。
### 3.2 错误类型表
| 错误名 | 错误码/枚举 | 语义 | 上抛/收口位置 |
|--------|-----------|------|--------------|
| ContentParseError | CONTENT_PARSE | frontmatter zod 校验失败 | data-access 转换点上抛 → route error.tsx |
| PostNotFound | （getPostBySlug 返回 null，非异常）| slug 无命中 | server-component 调 notFound() |
```

审核：D8——`date` 取 ISO 字符串保证跨界可序列化（生产级补充，[示例实证] gen-rss.js 用 `frontmatter.data.date` 字符串）；校验失败向上抛（不静默吞错返回 `[]` 冒充成功，通过 data-access L2 与 golden-path §2.3）；异常表逐行对应一条失败路径（D8 逐行可对应通过）。若此处 catch 后返回 `[]` → **D8/D7 P1（吞错冒充成功）**。

### 9.4 逐行为设计（D2-④⑤⑥/D5 取证点，示 getPostBySlug + PostListServer 渲染）

```markdown
## 4. 逐行为设计
### 4.2 getPostBySlug(slug)
- 函数签名：`getPostBySlug(slug: string): Promise<Post | null>`
- 行为简述：按 slug 读取单篇 MDX 并校验（承接 BHV-002）。
- 输入参数表：| 参数 | 类型 | 取值域/约束 | 必填 | ｜ slug | string | kebab-case 文件名 | 是 |
- 输出表：| 返回 | 类型 | 语义 | ｜ post | Post \| null | 命中=Post；无命中=null |
- 执行流程（mermaid sequenceDiagram，参与者用真实组件名）：
  participant SC as PostListServer(server-component)
  participant DA as getPostBySlug(data-access)
  participant Schema as UNIT-post-schema(domain-type)
  SC->>DA: getPostBySlug(slug)
  DA->>DA: 读 pages/posts/<slug>.md（gray-matter 解析 frontmatter）—— 文件不存在 → return null
  DA->>Schema: PostFrontmatterSchema.parse(data) —— 失败 → throw ContentParseError
  DA-->>SC: 返回 Post（含 slug/content）
- 流程详述（与图编号一一对应，§3.1 粒度）：1. 拼路径读文件，不存在返回 null；2. gray-matter 解析；3. 调 UNIT-post-schema 校验，失败上抛 ContentParseError；4. 收敛为 Post 返回（缓存语义见 §5）。
- 异常处理表：| 异常 | 处置 | 错误转换位置 | ｜ 文件不存在 | 返回 null（由 server-component 调 notFound()）| data-access | ｜ 校验失败 | 上抛 ContentParseError | data-access 转换点 → route error.tsx |
```

审核：D5 粒度——每步有具体被调用对象（`PostFrontmatterSchema.parse(data)`）、内部判定（文件存在性）、错误返回/收口点（return null / throw ContentParseError）、`sequenceDiagram` 参与者为真实七类 owner 名（通过）。D4——`PostListServer → getPostBySlug → UNIT-post-schema` 方向符合服务端链 §2.1（通过）；若画出 `client-component → getPostBySlug` 直连边 → **D4/§4 P1**。

### 9.5 状态 / 边界管理 + 缓存语义（D2-③/data-access·server-component 边界取证点）

```markdown
## 5. 状态 / 边界管理
- data-access：写 `N/A：无客户端状态`；缓存语义显式声明（内容源为本地 MDX，构建期读取等价 force-static；CMS/ORM 场景须显式 `next.revalidate` 或 `cache`，禁隐式默认）。
- 'use client' 边界：本单元 server-only（`import 'server-only'` 保险栓），无 'use client'。
- 私有数据/secret 边界：内容源访问只在本 data-access 与 server-component（D7 通过）。
```

审核：D7——`import 'server-only'` 保险栓 + 私有访问只在 server 边三类（通过 golden-path §2.2/§2.3）；缓存语义显式（通过 §2.3）。若 CMS 场景缺显式 `revalidate`/`cache` → **D7 P2（缓存隐式默认）**。

### 9.6 测试映射（D2-⑦/D6 取证点）

```markdown
## 7. 测试映射
| BHV/行为 | 测试层 | 测试点（成功+失败逐条） |
|----------|--------|------------------------|
| BHV-001 getAllPosts | unit(Vitest) | 成功 列出并按 date 倒序；失败 frontmatter 校验失败上抛 ContentParseError |
| BHV-002 getPostBySlug | unit(Vitest) | 成功 命中返回 Post；失败 slug 无命中返回 null / 校验失败上抛 |
| 渲染 PostListServer | component(RTL) | 成功 渲染列表；失败 取数上抛 → error.tsx 边界 |
```

审核：D6——每条行为 ≥1 成功 + 全部失败路径各 1 用例（校验失败、无命中均有用例），测试层合理（data-access/RSC 用 Vitest+RTL，符合 L1 §6 测试槽位）。内容源访问非高风险变更链；若漏校验失败用例则普通失败路径漏测 D6 P2。

### 9.7 不得补造清单（D2-⑧/D8 取证点）

```markdown
## 8. 不得补造清单
- 不决定内容源选型（MDX vs CMS vs ORM）——属概要 technology_decision_handoff，本单元按选定槽位展开。
- 不承载业务规则判定（如「草稿是否可见」）——属 server-component/server-action 编排。
- 不被 client-component/ui-component import——server-only 边界。
- 不手写 fetch 具体 URL/CMS 客户端初始化参数——超签名级，属实现 trace。
```

审核：D8——八问⑧逐条含越层禁止项；若正文出现内容源选型拍板（概要未选定）→ **D8 P1（拍板未选定决策，回退概要）**；若 data-access 内出现「草稿可见性」业务判定 → **D8/D4 P1（业务下沉，应属 server-component/server-action）**。
