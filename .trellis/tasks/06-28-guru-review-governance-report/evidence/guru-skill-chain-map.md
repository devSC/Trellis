# Guru Flutter-client writing/review 技能链测绘 — 能否拦下 Himora 类跨层负向/排除不变量

> 只读诊断。仓库根：`/Users/devSC/Documents/MyProject/Trellis-guru-0.6.0-ga-worktree`
> 目标 bug 类（Himora）：**远端未返回(omitted)的 V2 grouped-media 项必须仍存本地（RETAIN），但不得被 append 进可见 `displayItems`（EXCLUDE）。**
> 这是一条耦合的跨层负向/排除不变量：RETAIN 属 repository-datasource（本地/远端编排），EXCLUDE 属派生可见集合（usecase 流或 controller 投影）的成员资格规则。bug = 生产 `displayItems` 的一侧把"全部本地项"当作"全部可见项"。

判定维度（每阶段四问）：
1. 当前强制产出/核查什么（承重原文 + file:line）。
2. 是否强制枚举负向 / 排除 / "must-not" 语义规则？
3. 是否要求开放式跨层对抗推理（主动发现没人写出来的规则）？还是只做清单/合同符合性核对？
4. 是否要求对排除/遗漏行为写负向测试？

文件路径前缀缩写：
- `OL = guru-template/overlay/agents-skills`
- `SP = guru-template/specs/guru-flutter-client`

---

## 全链关键事实（grep 证据，支撑"缺什么"）

- 全链对"负向/排除"只有一个固定封闭集：分层方向、owner 唯一、scope（不得补造）、编号来源、架构图范围。检索 `排除|exclusion|不得出现|must.?not|negative invariant|不变量` 在九个 skill + harness + guides 内的全部命中只有：
  - `OL/client-design-overview-writing/SKILL.md:51` / `SP/harness/overview/overview-structure-single-source.md:60`：「图中不得出现归属表之外的组件」——架构图范围 must-not。
  - `requirement-structure-single-source.md:217`：「不得出现无来源接口意图」——编号来源 must-not。
  - 其余 `遗漏` 均为「明显遗漏（自检）」「无遗漏（索引完整）」「遗漏关键模型…降级路径（高返工风险）」——都不是数据项级排除/保留。
  - **没有任何一处**出现"数据项保留但不可见 / 集合成员排除 / 远端遗漏项处置 / 权威集合 vs 可见集合分叉"语义。
- 检索 `保留.*本地|远端.*未返回|部分返回|partial|增量|软删除|墓碑|membership|可见.*隐藏`：唯一的 `partial` 命中是 `partial_scope`（写作分批的 covered/not_covered 概念，与"部分 API 响应"无关）；`covered/partial/missing` 在 `requirement-structure-single-source.md:421` 是 REQ-UC 追溯状态。**零**条命中数据层"保留本地/远端遗漏/部分响应"语义。
- 对抗审查只存在于 requirements/overview/detail 三个 Gate（`SP/harness/gate/gate-confirmation-model.md:9-11, 28-30`）。**实现 Gate 无对抗审查**（同文件:13 明确把实现踢出该模型）。且 overview/detail 的 "adversarial" 仅是同一个 review worker 的 opposite-provider 标志（reviewer 名 `clean-context-adversarial-<provider>`，:89/:131），跑的还是同一份正向取证矩阵——它提升独立性，不引入新的负向不变量推理口径。

---

## 阶段 1：需求（requirement-writing / requirement-review / requirement-doc-standard）

### 1) 强制产出/核查什么
- 写作目标是"完整、清晰、可测试的产品需求 + 识别重点/难点行为"，并强调**需求与设计分离，不写实现细节**：`OL/requirement-writing/SKILL.md:10-14`。
- SSOT 主定义在 `requirement-doc-standard/references/requirement-structure-single-source.md`：
  - 第一章必含"核心能力定义"主定义（§5.2）：`...md:51-52`。
  - 核心能力正式清单字段（全是正向价值链/后果框架）：`business_outcome / value_chain / difficulty_focus / complexity_source / design_focus / design_expansion_requirement / risk_if_missed / success_metrics / failure_impact / acceptance_bar / validation_strategy`：`...md:137-147`，`counterfactual_check`:152。
  - "主要功能及核心场景"= 正向场景清单 `REQ-UC-XXX`：§6 `...md:201-222`。
- 分章指南：基本原则是"完整性/可测试性（触发条件、输入输出、预期结果明确）/ 需求与设计分离"：`OL/requirement-writing/references/chapter-guide.md:24-29`；第一章只产出正向"核心能力定义/价值链"：`...chapter-guide.md:97`。
- 审核：核查阶段0三产物、字段合同、反模式、编号契约、`confirmation_status`；严重度矩阵围绕"无法开发/无法验收/范围无法界定/核心能力退化为场景重排"：`OL/requirement-review/references/review-baseline.md:132-166`。

### 2) 是否强制枚举负向/排除规则？
**否。** §5.2 全部字段是正向业务结果 + 价值链；唯一"负向"字段 `failure_impact / risk_if_missed / counterfactual_check`（`...md:143-152`）是**业务后果**框架（"延期会怎样"），不是**数据成员排除/保留不变量**。`acceptance_bar`（:146）理论上可承载"远端停发的项应消失但本地不丢"这类验收级负向规则，但**没有任何字段或步骤强制作者去枚举排除/保留不变量**。需求与设计分离（:13、chapter-guide:29）反而把作者推离"数据集分叉"这一层。

### 3) 开放式跨层对抗推理？
**部分，但口径不对路。** 全链唯一的开放式对抗在需求层：
- requirements adversarial review（`gate-confirmation-model.md:9, 21, 50, 149`）：opposite-provider，"先查 code/tests/config/docs/ADR，再问产品问题"。这是最接近开放式跨层推理的一步。
- Domain Grill（:20）："磨尖术语、边界、失败路径、状态/owner 和红线"。
- **但**：两者都被框定在"用户可感知行为、**失败路径**、验收口径、术语、产品边界"（:42、:50、:149）。没有任何指令要求它产出/核查"集合成员负向不变量"或"权威集合 vs 可见/存储集合的分叉"。Himora 的排除半边发生在**成功响应路径上**（部分遗漏=成功响应），不在"失败路径"词汇里。

### 4) 负向测试？
**否。** 需求阶段不写测试，只写 `validation_strategy`（需求阶段可执行的前置验证）`...md:147`。无排除/遗漏负向用例要求。

---

## 阶段 2：概要（client-design-overview-writing / -review + overview L1）

### 1) 强制产出/核查什么
- L1 必含章节：设计约束 / 行为集合 / **归属判定表（核心产物）** / 页面流 / 架构总览六件套 / 技术决策承接 / 详细承接索引 / 未决问题 / 架构就绪自检：`SP/harness/overview/overview-structure-single-source.md:36-46`。
- 行为枚举四类顺序：用户操作 → 系统反应 → **失败路径（网络失败、数据缺失、非法输入、权限拒绝、并发冲突）** → 生命周期：`...md:117-124`。每条 GWT：`Given <前置> When <触发> Then <后置 + 状态变化>`：`...md:125`。
- §3.1 粒度四条（可直接实现/明确触发归属/完整链路含失败路径/粒度一致）：`...md:128-138`。
- §4 归属：每行为/状态唯一 owner + 三问；**一个状态只能有一个写 owner**：`...md:162-167`。
- 审核取证矩阵：行为"无失败路径类行为 P1"、归属"分层律违例 P1"、六件套、图文一致：`OL/client-design-overview-review/references/review-baseline.md:14-52`。

### 2) 是否强制枚举负向/排除规则？
**否（结构性 must-not 除外）。** GWT 模板只有正向 `Then <后置+状态变化>`（`...md:125`）——**没有 "Then Y 不得出现在集合 Z" / "must-not" 形态**。失败四类里有"数据缺失"（:120），是最近的钩子，但：
- "远端成功但遗漏部分项"是**成功路径**，不是"数据缺失"失败路径；
- 即便枚举出该行为，模型也无槽位承载"保留+排除"这条成员资格不变量。
归属表的负向只有"单写 owner"（:166）和架构图范围（:60），都不是数据成员排除不变量。**没有"两个集合必须分叉（存储集 ≠ 可见集）"的口径。**

### 3) 开放式跨层对抗推理？
**否，是清单/取证矩阵合同核对。** review-baseline 是逐章取证矩阵（`...review-baseline.md` 全篇），按 G1~G8 / 六件套 / 分层律 / 双向闭合判级。overview 的 adversarial clean 只是 opposite-provider 跑同一矩阵（gate model:131），不引入"主动发现没人写出来的排除不变量"。缺失的排除不变量不会表现为"缺失行为"——除非已有人先把它枚举出来。写作期自查也只问"每个用户操作行为是否配了对应**失败路径**行为"（`OL/client-design-overview-writing/references/chapter-guide.md:73`）。

### 4) 负向测试？
**否。** 概要不写测试。

---

## 阶段 3：详细（client-design-detail-writing / -review + detail L1 + L2 controller/usecase/repository-datasource）

### 1) 强制产出/核查什么
- 合同八问（所有 doc_type 通用）：`SP/harness/detail/detail-structure-single-source.md:44-51`：
  - 八问1 承接 BHV；八问2 输入/输出/错误枚举；八问3 读写状态（写 owner 与概要一致）；
  - **八问4 调用哪些依赖、不调用哪些依赖：正反两面都写（防越层）**（:47）；
  - 八问5 失败收口（异常表逐行对应失败路径）；八问6 事件/后置；
  - **八问7 测试映射：成功 + 全部失败路径**（:50）；
  - **八问8 哪些内容不得在此补造**（:51）。
- §3.1 粒度（含完整调用链）：`...md:53-58`。章节骨架合同：`...md:70-121`。
- 完成 Gate G3「每条行为测试映射覆盖成功路径 + 全部失败路径」：`...md:187`。
- L2 repository-datasource 八问5：「**编排策略必须显式——remote 失败是否回落 local、缓存过期策略、离线写入队列与冲突合并**」：`SP/harness/detail/detail-type-repository-datasource.md:19`；好例子「先 local，**remote 成功后写回 local 并发射新值**；remote 失败返回 local + 标记 stale」：`...repository-datasource.md:32`；八问7「编排逻辑（回落/合并/幂等）= unit test」:21。
- L2 controller 八问2：输出 = 「**状态字段全集（必须逐字段列表）**」（含 displayItems 类字段）+ 三态收口：`SP/harness/detail/detail-type-controller.md:16`；八问8 不得补造（不发明业务规则/不决定缓存）:23。
- L2 usecase 八问3 状态唯一写 owner、八问8 不得补造：`SP/harness/detail/detail-type-usecase.md:14-21`。
- 审核 D1~D9 + 逐 doc_type 附加：repository-datasource「错误转换表逐枚举；缓存回落策略归属；datasource 无业务判断 / 典型 P1：repository 绕过 datasource；datasource 含判定」：`OL/client-design-detail-review/references/review-baseline.md:33`；D6 测试「行数 ≥ 成功路径数 + 失败枚举数」:20。

### 2) 是否强制枚举负向/排除规则？
**有负向，但口径错位——这是 Himora 最该被拦却没拦的地方。**
- 八问的负向只有两类：**八问4=依赖层面**（不调用谁，防越层）；**八问8=归属/scope 层面**（本单元不拥有什么决策）。`...detail-structure-single-source.md:47, 51`。**没有"数据内容/集合成员"层面的负向槽位**（"X 必须保留但不得进入 Y"）。
- repository L2 八问5 是最接近的钩子（`...repository-datasource.md:19`），但词汇被钉死在 **remote 失败回落 / 缓存过期 / 离线写入冲突合并**——全是**远端失败/缓存**场景，**没有"远端成功但遗漏部分项：本地保留？是否进入可见集？"的提问**。好例子（:32）直接示范**全量替换**（"remote 成功后写回 local 并发射新值"）——这恰好引导作者写出会丢弃或错误 append 遗漏项的合并逻辑。**作者从未被问到那个答案就是不变量的问题。**
- controller L2 八问2 列 displayItems 类字段（:16），但**无"保留集 vs 可见集"区分提问**。

### 3) 开放式跨层对抗推理？
**否，是 D1~D9 合同符合性矩阵。** detail review 逐文档 D1~D9 + 跨层链路核对（`OL/client-design-detail-review/SKILL.md:60-69`、review-baseline 全篇）。跨层核对项是"页面只调 usecase 公开行为 / usecase 数据依赖有承接 / 状态写 owner 唯一 / 同一错误枚举跨章一致"（`...review-baseline.md:47-52`）——**没有"派生集合成员资格 / 保留-排除不变量"核对项**。SKILL.md:82 要求"回到 L1/L2 正向方法、不做形式检查"，但矩阵本质是合同覆盖度。detail adversarial clean 同样是 opposite-provider 跑同一矩阵。合同沉默 → 审核无据可指。

### 4) 负向测试？
**未对排除不变量强制。** 八问7 / G3 把负向测试面定义为"成功 + **全部失败路径**"（`...md:50, 187`），D6 量化为"成功路径数 + **失败枚举数**"（`...review-baseline.md:20`）。Himora 的排除断言（"遗漏项不得进入 displayItems"）发生在**成功响应路径**上：朴素"成功"= 展示远端返回的项，而它既不是这个 naive 成功用例，也不是"失败路径"——**于是不被任何测试映射强制**。repository L2:21 "合并 = unit test" 只会测合同写了的内容；合同没写排除，测试也不会有。

---

## 阶段 4：实现-写（flutter-implementation-guru-writing + golden-path + implementation-trace）

### 1) 强制产出/核查什么
- **只实现详细设计合同内的内容；合同外结构不新增，合同错漏回退详细阶段**：`OL/flutter-implementation-guru-writing/SKILL.md:18`。
- 测试先于/伴随实现，高风险切片先写失败测试再实现：`...SKILL.md:20`、`OL/flutter-implementation-guru-review/SKILL.md`（D4）。
- golden-path §10 禁止清单：全是分层/DI/序列化/不吞异常/不硬编码尺寸——**架构 canonical，零数据语义**：`SP/guides/golden-path.md:172-189`。
- trace 四节（计划/执行/证据/阻塞）：`SP/harness/implementation/implementation-trace-contract.md:7-36`。

### 2) 是否强制枚举负向/排除规则？
**否。** 禁止清单纯架构（`golden-path.md:174-184`）。实现被合同边界锁死（SKILL.md:18）；合同对排除不变量沉默 → 实现自由 append 遗漏项（即 bug 本体），不算违规。

### 3) 开放式跨层对抗推理？ 4) 负向测试？
- 写作侧无对抗审查口径；负向测试仅在"高风险切片先写失败测试"（:20），且"高风险/失败"沿用详细的失败路径定义 → **继承详细阶段的缺口**：合同没要求排除不变量测试，实现也不会写。

---

## 阶段 5：实现-审（flutter-implementation-guru-review）

### 1) 强制产出/核查什么
- D1 合同一致性：「diff 与详细设计单元逐一对照——合同外新增结构、未实现的承接行为，列差集」：`OL/flutter-implementation-guru-review/SKILL.md:17`。
- D2 分层/canonical；D3 存量豁免；D4 证据核查（测试覆盖**对照详细设计测试映射**，漏失败路径 P2 起步）：`...SKILL.md:18-23`。
- D5 注释/日志/追溯；D6 合规红线（制裁 TLD/私有 API/动态执行/PII）：`...SKILL.md:24-30`。
- 边界：**只审改动面 + 其直接依赖；不对存量代码做全量审计**：`...SKILL.md:50`。

### 2) 负向/排除规则？ 3) 对抗推理？ 4) 负向测试？
- **全否。** D1 是合同 diff——合同沉默时，代码沉默 = "合规"，差集为空。D4 测试核查只对照详细的测试映射（`...SKILL.md:23`）——映射没有排除不变量用例，漏掉即非 finding。
- **实现 Gate 无对抗审查**（`gate-confirmation-model.md:13` 把实现踢出对抗模型）；唯一负向是架构 canonical 与合规红线，均与数据成员排除无关。
- "只审改动面"（:50）进一步降低发现跨集合不变量缺口的概率。

---

## 结论：Himora 类本应在哪拦下，各 skill 缺什么口径

### 应拦截顺位
1. **主：详细 / repository-datasource（叠加 usecase 或 controller）合同。** 合并编排在这里是显式主题（repository L2 八问5）。这是排除+保留不变量的天然归宿，也是缺口最直接放过它的地方。
2. **次：概要行为枚举。** 失败四类含"数据缺失"，controller 拥有 displayItems 状态——本可在此把"远端遗漏项处置"枚举为行为，但模型形态不支持。
3. **再次：需求验收。** 本应捕获用户可见规则"远端停发的项从 feed 消失但本地自有数据不丢"。
4. **实现审查不应被期待拦下**：合同沉默 → diff 无据；该 Gate 无对抗审查。

### 各 skill 具体缺的口径
- **需求（§5.2 / chapter-guide）**：无字段/步骤强制枚举**负向/排除数据不变量**（"X 须保留但不得出现在 Y"）或**权威/可见集合 vs 存储集合的分叉**。覆盖是正向场景 + 正向核心能力价值链；`failure_impact/risk_if_missed/counterfactual` 是业务后果负向，非数据成员负向。`requirement-structure-single-source.md:137-152`、`...:13`。
- **概要（overview L1 §3/§4）**：行为模型是正向 GWT（"Then X 发生"，`overview-...:125`），**无 "must-not"/排除行为形态**；失败四类有"数据缺失"却无"部分/遗漏权威响应 → 保留+排除"类目（`:120`）；归属只强制"单写 owner"（`:166`），不强制集合成员排除不变量；**无"两集合必须分叉"口径**。
- **详细（detail L1 八问 / repository-datasource L2 / controller L2）**：八问唯二负向是八问4（依赖→分层）与八问8（scope→归属），**无"数据内容/集合成员"负向槽位**（`detail-...:47, 51`）；repository 八问5 编排词汇只覆盖**远端失败回落 / 缓存过期 / 离线写入冲突合并**，**不覆盖远端成功遗漏的保留+排除**，好例子还示范全量替换（`repository-datasource.md:19, 32`）；controller 八问2 列 displayItems 却无"保留集 vs 可见集"区分（`controller.md:16`）；测试口径 = "成功 + **全部失败路径**"（`detail-...:50, 187`），把"成功路径上的排除不变量"漏在"成功"与"失败"之间。
- **实现（golden-path §10 / trace / review D1~D6）**：被合同边界锁死（`writing SKILL:18`）；禁止清单纯架构（`golden-path.md:172-189`）；审查是合同 diff + canonical + 存量豁免，"只审改动面"（`review SKILL:17, 50`）；**该 Gate 无对抗审查**（`gate-confirmation-model.md:13`）。继承详细缺口。

### 跨阶段根因
整条链是**正向覆盖 + 合同符合性**流水线。被强制的"负向规则"是一个**固定封闭集**：分层方向（八问4）、owner 唯一（单写 owner）、scope（八问8 不得补造）、编号来源、架构图范围。**全链没有一等公民产物来承载"跨层负向/排除语义不变量（数据内容 / 集合成员）"**；唯一的开放式对抗推理（requirements adversarial review + Domain Grill）位于需求层，被框定在失败路径/用户可感知行为/术语，且不要求产出或核查数据成员排除不变量。**"全部失败路径"被错当成"负向不变量覆盖"**，从而系统性漏掉活在成功路径上的排除规则——正是 Himora bug。
