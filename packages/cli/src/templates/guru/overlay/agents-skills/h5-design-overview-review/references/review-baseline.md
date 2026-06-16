# H5 概要审核取证矩阵与严重度判级（references）

> 编排层产物：只承载逐章取证操作、判级细则与一份最小成稿示例；规则正文与完成条件（G1~G9）以 L1
> `.trellis/spec/harness/overview/overview-structure-single-source.md` 为唯一来源。冲突时 **L1 > references > SKILL.md**。
> 本文不复写 L1 规则正文：每条取证操作都回指 L1 章节号（§N）或 G 项（GN）。
> 平台基线：Next.js（App Router 生产形态为目标）+ React + TypeScript(strict)。doc_type 一律用 L1 §7.1 钉死的 **H5 七类**（`server-component` / `client-component` / `data-access` / `route` / `ui-component` / `domain-type` / `server-action`），禁止照抄 flutter（Page/Controller/UseCase/Repository）或 Go（handler/service/repo）类型名。

## 0. 完成条件锚点对照（取证前先固化）

L1 §6 钉死的完成条件为 **G1~G9**（G1~G5 两轨共用；G6~G9 仅 full 链强制）。本文逐章矩阵的「受影响 G 项」列一律回指此处，不另立编号：

| G 项 | 主题（L1 §6） | 闭合口径一句话 |
|------|---------------|----------------|
| G1 | 行为覆盖 + 粒度 | P0/P1 核心能力逐条可追溯到 BHV-NNN，且每条行为满足 §3.1 粒度（含执行边标注） |
| G2 | 归属判定表 + 分层依赖律 | 每条行为唯一 owner（七类）+ 三问理由；无 §4.0 分层依赖律违例 |
| G3 | 合规依据 + secret 边界 | 涉认证/采集/三方域名/PII 行为有 `compliance_basis`；secret 引用仅落 server 边三类 |
| G4 | 承接索引覆盖 | 索引非空且覆盖归属表全部 owner；full 链逐条落 `chapters/<slug>.md` 并标 `l2_status` |
| G5 | 未决问题风险 | 无高风险未决项（或已获用户确认带假设进入） |
| G6 | 架构总览六件套 | §2.5 ①~⑥ 齐全，图中组件与归属表一致、依赖箭头合 §4.0 |
| G7 | 时序图策略闭合 | 非豁免 UC 有可定位 sequenceDiagram；合并图列覆盖清单；豁免有理由；无占位残留 |
| G8 | 技术决策承接字段完整 | `technology_decision_handoff[]` 逐条字段齐（§2.6）；渲染策略/缓存已成决策项；无「未选定但已被下游引用」 |
| G9 | golden-path 硬规则 | §8 锁定项自检通过（生产基线 strict:true/App Router/server-first/私有数据边界等均落实） |

> 注：SKILL.md 正文个别处写「G1~G8」，以 L1 §6 的 **G1~G9** 为准（G9 = golden-path 硬规则自检）。

## 1. 取证准备

- 建立编号索引：`rg -n "BHV-|UC-|UNIT-|TD-" <主文档>` 固化编号清单；`rg -n "^#{1,4} " <主文档>` 固化章节锚点。
- 引用证据一律用「章节 + 表格行 / 裸 token」定位（如 `§3 归属表 BHV-012 行`、`UNIT-tag-filter-client-component`），不引用模糊位置。
- full 链同时取证 README（是否承载了事实正文——承载即 P2）与任务内 `design.md`（是否仍承载主定义——承载即 P2 双主定义；L1 §2a 要求 `design.md` 退为指针+摘要）。
- 主定义位置：full = `design_package/design-main.md`；light = 任务内 `design.md` §1（L1 §2b）。
- **执行边索引**：`rg -n "'use client'|server-only|process\.env|revalidate" <主文档>`，为「server-first 与私有数据边界」核查（§3 第 5/6 章取证）建立候选行。
- **类型名越界扫描**：`rg -ni "controller|usecase|repository|datasource|handler|service|biz|entry-api" <主文档>` — 命中即疑似照抄 flutter/Go 类型名（落到归属表/索引 `doc_type` 列时 P1，详见 §3 第 7 章）。

## 2. 逐章取证矩阵（L1 §2 必含章节 1~9）

> 章序按 L1 §2「必含章节」。light 链只必含第 1~8 条，第 5 章可简化（保留一句话架构 + 路由/组件树描述，分层图与时序图策略表不强制），第 9 章可简化为 Gate 前自查（L1 §2b）。

| 章 | 应覆盖（L1 锚点） | 取证操作 | 缺口判级（受影响 G 项） |
|----|------------------|---------|------------------------|
| 1 设计约束与输入 | 承接 P0/P1 逐条带需求锚点；技术栈约束（§0 平台档案 + 路由模式槽位）；显式假设三字段（依据/影响范围/验证时点） | 对照需求核心能力清单做差集；抽查每条 P0/P1 锚点可定位；核对路由模式槽位（App/Pages）已锁定 | 缺章 P1（G1）；P0/P1 锚点缺失 P2（G1）；显式假设缺字段 P2（G5）；路由模式槽位未锁定 P1（L1 §1-P6，阻断 route 归属展开） |
| 2 行为集合 | §3 四类枚举（用户操作/系统反应/失败路径/生命周期）+ GWT 三段 + 执行边标注 + BHV 编号标题 + §3.1 粒度 | 逐条核对 `Given/When/Then` 三段与状态变化；每条核对是否标注**执行边（server/client）**；抽样 ≥1/3 行为做 §3.1 四条粒度判定 | 无失败路径类行为 P1（G1）；粗粒度核心行为（如「展示文章页」「处理评论」）P1（G1）；缺执行边标注 P2（G1）；GWT 缺段 P2（G1） |
| 3 归属判定表 | §4.0 唯一 owner（七类）+ §4.1 三问实质 + 分层依赖律 | 逐行核问：owner 在七类之内？三问有实质内容（非「同上」「同 flutter」）？写 owner 唯一？方向合 §4.0 三链？ | **分层依赖律违例 P1（G2，阻断）**；client-component 直取私有数据/持 secret P1（G2/G3）；多写 owner P1（G2）；三问空洞 P2（G2）；名词先行（Manager/Helper/Util/Provider）P2（G2） |
| 4 路由与组件树 | App Router 段树（`app/<seg>/page\|layout\|loading\|error.tsx`）、导航、入参（`params`/`searchParams`）、metadata/SEO 落点；非 UI 需求标 N/A | route 段名与 owner 抽查；失败/取消去向（`error.tsx`/`notFound()`）逐页核对；metadata/SEO 落点核对 | 整章缺失（UI 需求）P1（G6）；缺 metadata/SEO 承接 P2（核心可索引页升 P1，G6）；缺 `error.tsx` 错误边界归属 P2（G6） |
| 5 架构总览（六件套） | §2.5 ①~⑥ | 见 §3 专项矩阵 | 见 §3 专项（G6/G7） |
| 6 技术决策承接清单 | §2.6 字段合同 `technology_decision_handoff[]` | 逐条字段齐全性（decision_id/decision_point/candidates/selected/rationale/detail_expansion_targets/compliance_basis）；`rg -ni "key\|secret\|token\|access_key\|\.env"` 扫真实凭证 | 字段缺 P2（G8）；涉认证/采集/三方域名/PII 缺 `compliance_basis` P1（G3）；真实 secret value / `.env` 当线上配置合同 P1（G3）；「未选定」却被下游引用 P1（G8）；云/平台支持默认凭证链却要长期密钥 P1（G3） |
| 7 详细设计承接索引 | §7.2 owner 全覆盖 + §7.1 doc_type 七类 + 逐文件 + `l2_status` | 归属表 owner 集合 vs 索引覆盖集合差集；`doc_type` ∈ 七类；full 链逐条有 `chapters/<slug>.md`；pending 四类标注与豁免计划核对 | owner 未覆盖 P1（G4）；**doc_type 用 flutter/Go 类型名或自造类型 P1（G4）**；命中 pending 四类（route/ui-component/domain-type/server-action）缺 `l2_status: pending` 标注或缺八问展开计划 P1（G4）；full 链缺 `chapters/*.md` P1（G4） |
| 8 未决问题 | 风险等级 + 阻塞 G 项 | 高风险项是否存在未关闭 | 高风险未关闭 P1（G5） |
| 9 架构就绪自检（full 链必含） | G1~G9 逐项 + 证据 | 自检结论与本次审核结论交叉核对 | full 链缺自检节 P1；自检与实情不符 P1（标注受影响 G 项） |

## 3. 架构总览六件套专项取证（L1 §2.5，G6 第一取证对象）

> 架构总览是人类可审核入口——评审者先看图、先能读懂「这个 H5 应用长什么样、route 段怎么组织、server/client 边界在哪、渲染与数据链路怎么走」，再进逐章细查。

| 件（L1 §2.5） | 取证操作 | 缺口判级（受影响 G 项） |
|----|---------|---------|
| ① 一句话架构 | 是否按 L1 §2.5① 固定格式（入口 route 段 → server-component 编排 data-access → 交互下沉 client-component 消费 ui-component → server-action 回写 → 渲染策略+metadata 收口），组件为真实七类 owner 名 | 缺失 P1（G6）；格式自由化 / 组件非真实名 P3（G6） |
| ② 分层架构图 | mermaid graph 存在；subgraph 分层（routing/server/client/external）；箭头全部符合 §4.0 三链方向；图中节点逐个回查归属表 | 缺图 P1（G6）；**逆向/跨层箭头（含 `client-component → data-access` 直取数据）P1（G2 分层律）**；图含归属表外组件 P1（G6，「图比表大」=补造） |
| ③ 路由/组件树图（仅 UI 需求） | 覆盖全部新增/修改 route 段；节点标 `app/<seg>` 与产物文件；边标 BHV 编号 + `params`/`searchParams` 要点；标渲染策略（SSR/SSG/ISR）与 metadata 来源；失败/取消路径（`error.tsx`/`notFound()`）存在 | 缺图（UI 需求）P1（G6）；缺渲染策略/metadata 标注 P2（G6/G8）；缺失败路径 P2（G6）；非 UI 需求未标 N/A 及依据 P2 |
| ④ 核心 UC 表 | 列齐全（uc_id/uc_title/actor_or_trigger/source_refs/goal/priority）；UC 非 BHV 重排（一 UC 覆盖 2~5 BHV 为常态，含 SSR 首屏/客户端 hydration 触发） | 缺表 P1（G6）；UC = 单 BHV 重排 P2（G6） |
| ⑤ UC 承接表 | `bhv_refs` 与行为集合双向闭合；`owner_refs` ⊆ 归属表（七类名）；`route_refs` ⊆ 第 4 章 route 段；`index_refs` ⊆ 第 7 章 chapter_target | 任一向断链 P1（G6） |
| ⑥ 时序图策略表 | 三选一齐备（独立/合并/豁免）；独立/合并有 `sequence_section` 且可定位；合并有 `merged_coverage` 清单；豁免有 `exemption_reason` + 最小行为链 | 缺表 P1（G6）；占位残留 P1（G7） |

### 3.1 sequenceDiagram 细查（每张抽查，L1 §2.5 时序图回填硬约束 / G7）

- **参与者必须用真实 owner 名**（route / server-component / client-component / data-access / server-action / external），不得用浏览器 / 抽象角色冒充。
- **方向合 §4.0**：服务端渲染链覆盖 `浏览器/route → server-component → data-access → external(CMS/DB/三方)`；交互变更链覆盖 `client-component → server-action → data-access`（回包用虚线）。
- **禁止 client-component 直连 data-access 的边**——交互取/写数据必须经 server-action 或经 route 的 server-component 加载链。出现此类直连边 → **P1（G7/G2）**。
- 图中步骤编号与图下文字详述一一对应；失败分支有表达（`alt` 块或独立图，覆盖 fetch 失败/`notFound()`/`error.tsx`）。
- 不符各记 P2（G7）；方向违例或 client 直连 data-access 记 **P1（G7/G2）**。

## 4. 跨章一致性取证（L1 §6 G6 图文一致性 + §3.2 行为↔UC 双向闭合）

逐项做差集，断链记 P1/P2：

1. **架构图组件集合 ⊆ 归属表 owner 集合**（图多出组件 → P1（G6），「图比表大」= 补造）。
2. **路由/组件树图边集合 ↔ 导航类 BHV**（互查差集 → P2（G6））。
3. **系统/分层架构图 external 节点（CMS/DB/认证/外部 API）↔ data-access / server-action / `technology_decision_handoff[]` owner**（外部依赖无 owner 承接 → P1（G6/G8））。
4. **UC 承接表 `bhv_refs` ↔ 行为集合 BHV-NNN**（双向断链 → P1（G6））。
5. **UC 承接表 `index_refs` ↔ 第 7 章 chapter_target**（断链 → P1（G4/G6））。
6. **`technology_decision_handoff[].detail_expansion_targets` ↔ 第 7 章索引条目**（指向不存在条目 → P2（G8））。
7. **写作顺序依赖闭合（L1 §4.3）**：自底向上链 `domain-type → data-access → server-action → server-component → client-component → ui-component → route`；上层引用的下层 owner 必须在归属表中存在且方向正确——断链或倒序依赖 → P1（G2）。

## 5. H5 硬规则专项取证（L1 §8 锁定项 / G9，全部 P1 起步）

逐项核查 owner 与技术决策是否违反 L1 §8 锁定项：

| 锁定项（L1 §8） | 取证操作 | 判级 |
|----------------|---------|------|
| TS strict | 第 1 章技术栈约束声明 `strict: true` | 概要把 `strict:false` 当生产基线 P1（G9） |
| server-first / `'use client'` 最小化 | `rg -n "'use client'"`；归类为 client-component 的单元须有真实交互理由（状态/事件/浏览器 API/hooks） | 纯展示/可服务端渲染单元误标 client-component P2（污染主链或导致私有数据下放升 P1，G2/G9）；server-component 内出现浏览器运行时逻辑 P1（G2/G9） |
| 私有数据 / secret 隔离 | 私有数据获取/内容源访问/secret 读取只能归 server-component / data-access / server-action | client-component 直取私有数据 / 持 secret / 直连 DB 或 CMS 私有端点 P1（G3/G2）；真实 `api_key`/`access_key`/`token`/NextAuth secret 落正文/示例/fixture P1（G3） |
| route 段约定 | route owner 承接 `page/layout/loading/error.tsx` 存在性与职责 | 缺段约定承接 P2（核心入口升 P1，G6）；缺 `error.tsx` 错误边界归属 P2（G6） |
| metadata / SEO | 核心可索引页 `generateMetadata`/静态 `metadata` 归属到 route owner | 缺 metadata/SEO 承接 P2（影响核心入口可达性升 P1，G6） |
| 样式隔离 | 样式方案按 project-conventions 锁定（Tailwind / CSS Modules）；归属表/技术决策出现全局样式污染或方案不一致 | 全局裸 CSS 覆盖 / 跨组件样式泄漏 / 方案与约定不一致 P2（G9） |
| 错误边界 | 渲染失败路径落 `error.tsx`；数据缺失走 `notFound()` | 失败路径无承接 owner P2（影响主链升 P1，G6） |
| 内容源 | MDX/CMS 经 data-access 封装 | 内容源直读绕开 data-access 封装边界 P2（影响私有数据边界升 P1，G2） |
| 图像优化 | 生产用 `next/image` | 缺承接 P3（非阻断，影响主链升 P2，G9） |

### 5.1 App Router 生产基线核查（L1 §10，G9）

- 概要归属与技术决策一律按 App Router 生产口径核查：`strict: true` / Server Components / `app/` 段约定 / `metadata` API / data-access 封装 / `server-action` 变更均为生产锁定项。
- 出现 Pages Router 结构当 route 段约定的替代、用「无 server-first 边界」豁免 client/server 分层、`getStaticProps`/手写 `<Head>`/全局 CSS 等旧形态 → P2 起步（导致分层律或私有数据边界被绕开升 P1，G9/G2）。
- 系统性写入旧形态弱化生产硬规则 → 按 L1 §9 文档级重构。

## 6. 行为粒度判定细则（L1 §3.1，G1）

抽样 ≥1/3 行为，逐条按四条判定：

1. **可直接实现**：具体到详细设计可直接展开为合同，无需再分解业务语义。
2. **明确触发与归属**：能指出触发者（用户/系统/生命周期）、**执行边（server/client）**与候选 owner（七类）。
3. **完整链路**：从入口行为可追踪全部下游行为（含失败路径与 `loading`/`error` 边界、生命周期），无断链。
4. **粒度一致**：同文档内行为粒度一致；出现「处理文章页」「显示文章」式粗粒度即不达标。

粗粒度核心行为 P1（G1，不可直接展开详细设计——须拆出渲染/数据获取/交互/错误态）。

## 7. 编号纪律核查（L1 §3.3）

- 行为用 `BHV-NNN`（三位数，prd 标题来源）；设计单元用 `UNIT-<slug>`（kebab-case，详细标题来源）；正文引用须为裸 token。
- 编号缺失 / 重号 / 跨层混用 / 删除未留洞重排 → P2（影响 trace-matrix 断链时升 P1）。
- 命名（L1 §4.2）抽查：组件 = 定语 + 名词 + 层角色（`PostDetail` server-component、`CommentForm` client-component、`PostCard` ui-component、`getPostBySlug`/`PostSource` data-access、`createComment` server-action、`PostSchema` domain-type）；取数动词区分 `list/one/get/fetch` 语义；含混 `Manager/Helper/Handler` 后缀 → P2；client-component 名未体现交互语义而实为纯展示 → 结合 §5 复核归类。

## 8. 越界核查（L1 §5，G 项视落点而定）

L1 §5 禁写项扫描——出现即概要越界，P2 起步并给最小回收方案（移入承接索引 `detail_expansion_targets` 或对应 `chapters/<slug>.md` 八问）：

- 字段级合同、组件 props 签名、zod schema 字段明细。
- fetch 具体 URL/查询参数、API 路径细节。
- SDK/CMS 客户端初始化参数、`next.config` 取值、环境变量取值、SQL/DDL。
- 代码、伪代码、`.tsx` 文件级实现安排。
- 把 `technology_decision_handoff[]` 中「未选定」决策（如 MDX vs CMS）写成已选定 → P1（G8）。

## 9. LLM/agent 承接核查（L1 §6 G8，触发时）

概要出现 LLM/agent/prompt 驱动调用时，按 L1 LLM 承接条款核查：逐次逻辑调用承接、`prompt_owner`、运行期上下文来源、上下文获取/编排行为锚点（须落 server-component / server-action / data-access，**不在 client-component**）、prompt 组装 owner、`detail_prompt_target`，以及 provider/model/SDK/invocation mode/config/凭证策略对应的 `technology_decision_handoff[]` 目标。缺口归入 G8；secret value 按 §5 私有数据/secret 隔离判 P1（G3）。

## 10. 严重度判级规则（L1 §6）

- **P1（阻断，不可进入详细设计）**：违反 §4.0 分层依赖律；client-component / 浏览器直取私有数据或持 secret；外部直连 data-access/server-action 越过 route；G1~G9 任一 Gate 项缺失；非豁免 UC 时序图缺失或时序图占位残留；缺 `compliance_basis`；真实 secret value / `.env` 误用；粗粒度核心行为；doc_type 用错类型名（flutter/Go/自造）；pending 四类缺 `l2_status` 标注或缺八问展开计划；双向断链（行为↔UC、owner↔索引）；双主定义（README/design.md 与 design-main 两套正文）；高风险未决未关闭；写生产基线为示例简化值（如把 `strict:false` 当生产基线）。
- **P2（应修，可带明确假设进入）**：`'use client'` 误用未污染主链；命名反模式；三问空洞；metadata/SEO 缺失（非核心入口）；样式污染；轻度越界（给回收方案）；共享能力误归类；执行边标注缺失；图文局部不一致；`technology_decision_handoff[]` 字段不全且未被下游引用；旧形态未按生产基线纠正（非系统性）。
- **P3（建议）**：表述与术语一致性；格式偏离模板但语义完整；图像优化等非主链承接缺失。
- 判级冲突时取高；同一根因多处表现合并为一条 finding（列全部位置）；影响主链的 P2 升 P1。

## 11. 结论判定（L1 §6 输出互斥分支）

- 存在任一 P0/P1 → **不可进入**（列阻塞清单与修订形态建议，按 L1 §9 区分局部修订 vs 文档级重构）。
- 仅余 P2 且每条已有明确假设/修订路径 → **带明确假设可进入**（列假设、依据、影响范围、验证时点）。
- 无 P0/P1/P2（P3 可遗留）→ **可进入详细设计**。
- 结论为「可进入 / 带假设可进入」时必须给 Gate 收口指引（用户终端 confirm，见 SKILL.md「Gate 收口」节）。

## 12. 修订形态判定（L1 §9）

- **局部修订**：补一条行为、补归属三问、补一条索引、补一张图、补 `l2_status`、改措辞、修标签、补执行边标注 → 在原文档上改。
- **文档级重构**：归属模型错误（owner 大面积错位/违反 §4.0）、行为枚举从名词倒推、索引与归属表系统性脱节、架构总览与正文两套口径、系统性写入旧形态弱化生产基线 → 重做对应章节，禁止用局部补丁掩盖错误模型。
- 发现上游需求缺陷（行为缺失/矛盾/范围漂移）→ 结论标注「回退需求阶段」，禁止在概要补造业务规则。

## 13. 最小成稿示例（取证锚点演示）

> 用途：演示一个**真实功能单元**的概要骨架长什么样、审核取证时锚点应落在哪里。功能取一个通用的「按标签筛选文章列表」单元（内容源 frontmatter 模型 `title/date/description/tag/author`，按 `tag` 过滤），以 **App Router 生产形态**展开。本示例只示形态与取证锚点，不是审核对象本身。

### 13.1 一句话架构（L1 §2.5①）

> 用户经 `app/tags/[tag]/page.tsx`（route 段）进入，由 `PostListServer`（server-component）编排数据获取并调用 `getPostsByTag`（data-access），交互的标签切换下沉到 `TagFilterClient`（client-component，消费 `PostCard` ui-component），无写操作（纯查询页，`server-action` 标 N/A），按 SSG + `generateStaticParams` + `generateMetadata` 收口到界面。

### 13.2 行为集合骨架（L1 §3，节选 BHV 编号）

- `BHV-001 按标签筛选并渲染文章列表`：Given route `app/tags/[tag]/page.tsx`、`params.tag` 已知 When SSR 首屏 Then [server] `PostListServer` 调 `getPostsByTag(tag)` 取 frontmatter 命中文章（内容源模型 `title/date/description/tag/author`），命中则渲染列表，零命中走 `notFound()`，生成 metadata。涉及状态：文章列表（服务端数据，无客户端状态）。执行边：server。
- `BHV-002 客户端切换可见标签`：Given 列表已 SSR 渲染、当前 tag 已知 When 用户点击另一标签 chip Then [client] `TagFilterClient` 用 `useState` 切换路由 `/tags/<newTag>`（`useRouter().push`），不在客户端直取私有数据。涉及状态：当前选中 tag（client 态，写 owner = `TagFilterClient`）。执行边：client。
- `BHV-003 标签下无文章的空态`：Given `params.tag` 无任何文章 When SSR 取数返回空 Then [server] `getPostsByTag` 返回空数组、`PostListServer` 调 `notFound()` 命中 `app/tags/[tag]/not-found.tsx` 边界。执行边：server。

### 13.3 归属判定表骨架（L1 §4，节选 + 三问演示）

| BHV | owner（UNIT-<slug>） | doc_type | 三问要点（节选） |
|-----|----------------------|----------|------------------|
| BHV-001 | `UNIT-post-list-server` | `server-component` | ①属于它：server-first 渲染 + 数据编排是 server-component 本质职责；②不属于别人：不属于 route（route 只装配段与 metadata，不做取数编排）、不属于 client-component（私有内容源访问不能下放客户端）；③需独立：被 `/tags/[tag]` 与 `/posts` 两处复用，值得独立 UNIT |
| BHV-001 | `UNIT-posts-by-tag-source` | `data-access` | ①属于它：内容源（MDX 读取 + frontmatter 解析）访问 + 缓存语义是 data-access 本质职责；②不属于别人：不属于 server-component（编排不拥有取数合同）、不属于 client-component（禁直取私有内容源）；③需独立：取数合同跨页复用 |
| BHV-002 | `UNIT-tag-filter-client` | `client-component` | ①属于它：`useState` + 点击事件 + `useRouter` 是交互 owner 职责；②不属于别人：不属于 server-component（含浏览器运行时交互）、不属于 ui-component（持状态非纯展示）；③需独立：交互边界最小化叶子 |
| BHV-001 | `UNIT-post-card` | `ui-component` | ①属于它：纯展示文章卡片、props 进 JSX 出；②不属于别人：不取数（属 data-access）、不持状态（属 client-component）；③需独立：列表项复用 |
| — | `UNIT-post-frontmatter-schema` | `domain-type` | ①属于它：`title/date/tag/...` 字段语义 + zod 校验 frontmatter 模型；②不属于别人：横切被依赖，不归任何运行层；③需独立：跨 data-access/页面共享合同 |

> 取证演示：若把 `UNIT-tag-filter-client` 的取数职责写成「直接 `fetch` 文章数据」→ **P1（G2，client-component 直取私有数据，违反 §4.0）**；若把 `UNIT-post-card` 标注承接「按 tag 过滤逻辑」→ P2（G2，业务下放 ui-component，影响主链升 P1）。

### 13.4 承接索引骨架（L1 §7.2，演示 l2_status）

| chapter_target | doc_type | chapter_file | bhv_refs | l2_status |
|----------------|----------|--------------|----------|-----------|
| UNIT-post-list-server | server-component | chapters/post-list-server.md | BHV-001,BHV-003 | full |
| UNIT-posts-by-tag-source | data-access | chapters/posts-by-tag-source.md | BHV-001,BHV-003 | full |
| UNIT-tag-filter-client | client-component | chapters/tag-filter-client.md | BHV-002 | full |
| UNIT-post-card | ui-component | chapters/post-card.md | BHV-001 | **pending**（按 L1 §7.4 八问就地展开） |
| UNIT-post-frontmatter-schema | domain-type | chapters/post-frontmatter-schema.md | BHV-001 | **pending**（按 L1 §7.4 八问就地展开） |
| UNIT-tags-route | route | chapters/tags-route.md | BHV-001,BHV-002,BHV-003 | **pending**（按 L1 §7.4 八问就地展开） |

> 取证演示：`server-component`/`client-component`/`data-access` 三类 v1 有 L2 模板（`l2_status: full`），可回指 `.trellis/spec/harness/detail/detail-type-*.md`；`route`/`ui-component`/`domain-type`/`server-action` 四类 v1 无 L2，命中即须标 `l2_status: pending` 并给八问展开计划，缺标注 → **P1（G4）**。若任一 `doc_type` 列写成 `Page`/`Controller`/`Repository` → **P1（G4，doc_type 用错类型名）**。

### 13.5 时序图策略表骨架（L1 §2.5⑥）

| uc_id | strategy | sequence_section | merged_coverage | exemption_reason |
|-------|----------|------------------|-----------------|------------------|
| UC-01 标签筛选浏览 | 独立 | §5.x 标签筛选时序 | — | — |

对应 `sequenceDiagram` 参与者：`浏览器 → app/tags/[tag]/page.tsx(route) → PostListServer(server-component) → getPostsByTag(data-access) → 内容源(external)`；交互切换边 `用户 → TagFilterClient(client-component) → useRouter 路由跳转`（**不出现 `TagFilterClient → data-access` 直连边**——切换经路由触发新一轮 SSR 加载链）。若画出 `TagFilterClient → getPostsByTag` 直连 → **P1（G7/G2）**。
