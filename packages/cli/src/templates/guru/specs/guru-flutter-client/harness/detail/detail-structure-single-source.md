# 客户端详细设计 — 单一来源规范（L1）

> 跨类型唯一权威。L2 类型文件只承载类型差异，不得与本文冲突；writing/review 只做编排与判定。
> 上游硬输入：概要设计的归属判定表 + `chapter_target → detail_doc_type` 承接索引 + `technology_decision_handoff[]`。
> 层级契约：本文（L1）承载规则正文与完成条件；writing/review skill 的 `references/` 只承载编排细则、模板与示例；冲突时 L1 > L2 > references > SKILL.md。

## 1. 装载与硬前置

执行写作或审核前依次确认，任一失败即终止并输出前置缺口：

- P1 本文件可读；涉及类型的 L2 文件可读（v1 仅 controller/usecase/repository-datasource 有 L2；其余类型按本文 §3 合同八问展开并在文档头标注 `l2_status: pending`，full 链另须满足 §2 的 L2 豁免合同）。
- P2 通用 golden-path 可读。
- P3 目标仓库 `project-conventions.md` 可读且校验通过（C1~C5）。
- P4 概要主定义可定位（full 链=`design_package/design-main.md`；light 链=`design.md` §1），且承接索引存在、可建立完整非空的 `chapter_target → detail_doc_type` 目标集合。**索引缺失/为空 → 回退概要阶段，禁止在详细阶段补造归属。**
- P5 概要 Gate 已过且当前 digest 下已有两个不同 run-id 的 clean review evidence（`guru_gate.py status` 可查 overview review）；缺 evidence 不得开始详细写作。

## 2. 九类 detail_doc_type

| doc_type | 覆盖对象 | L2 状态 |
|----------|---------|---------|
| `page-entry` | 路由注册、Binding、页面结构、design model 消费、widget 级 controller | pending |
| `controller` | 页面状态容器：状态字段、事件→状态转移、流订阅、生命周期、三态 | **v1 提供** |
| `usecase` | 有状态业务流程、响应式流、业务 API | **v1 提供** |
| `service` | 无状态工具/跨域转换 | pending |
| `repository-datasource` | 数据访问合同、local/remote 编排、缓存回落、错误转换点 | **v1 提供** |
| `db-dao` | 表定义、版本迁移、DAO 合同 | pending |
| `api-network` | @RestApi 方法、req/resp model、错误上抛 | pending |
| `config-l10n` | 配置项、ARB key、受控同步 | pending |
| `external-platform` | 三方 SDK、平台通道、gurusdk 能力、iOS 交付面（PrivacyInfo/entitlements/StoreKit） | pending |

**承载形态按链型分轨**（轨道判定见概要 L1 §2）：

- **full 链（目录级设计包）**：每个 `chapter_target` 独立一个 `design_package/chapters/<slug>.md` 文件（文件名与概要承接索引一致，gate 检查双向闭合）。执行采用 **directory_precheck + chapter_loop**（合同见 §5）：先确认 design-main.md 承接索引存在且非空（缺失/为空 → 回退概要，禁止详细补造），再**逐章或小批次**生成正文——禁止一次性全量输出全部章节（全量输出必然退化为大纲级薄文档）。
- **light 链（单文件）**：合并为任务内 `design.md` §2 单文档多章节，每章仍须独立满足对应合同。

**pending L2 拦截（full 链）**：承接索引命中 L2 状态为 pending 的 doc_type 时，必须在 design-main.md 显式声明 `L2豁免：<doc_type> 理由：…`（说明按 L1 合同八问展开的风险与补齐计划），否则 gate 拦截；首选做法是先补齐对应 L2 再进详细设计。

## 3. 合同八问（所有 doc_type 通用骨架）

**编号纪律**：每个设计单元以 `### UNIT-<slug>` 标题定义（语义 kebab-case）；测试与实现切片对单元的引用一律写 UNIT 编号 token。

每个设计单元必须回答，缺一不可（括号内为可验证信号——审核按此取证）：

1. **承接哪些行为**：逐条引用 `BHV-NNN` 编号（必须存在于 prd——幽灵引用与无承接行为均被 gate 断链拦截）。
2. **输入 / 输出 / 错误结果**：类型、取值域、错误枚举（输入/输出各有参数表；错误有错误类型表，见 §4 表合同）。
3. **读取 / 写入哪些状态**：明确读写分离；写 owner 必须与概要归属一致（可回指归属表行）。
4. **调用哪些依赖，不调用哪些依赖**：正反两面都写（防止越层；依赖必须出现在概要架构图/归属表中）。
5. **失败如何收口**：每条失败路径的处置（重试/降级/上抛/用户提示），错误转换位置遵循 `[SLOT-04]`（异常表逐行可对应一条失败路径 BHV 或八问 1 的行为分支）。
6. **产生哪些事件 / 后置结果**：流发射、埋点、副作用（逐条写明消费方）。
7. **哪些测试验证它**：映射到测试分层（unit / widget / integration / manual），逐行为给测试点（成功 + 全部失败路径）。
8. **哪些内容不得在此补造**：显式列出本单元不拥有的决策（如"不决定缓存策略——属 repository"）。

### 3.1 粒度标准（四条，写作与审核共用）

1. **可直接实现**：每个行为步骤具体到开发者可直接编码，不需要再分解业务逻辑或补充判定。
2. **明确调用关系**：每步指明调用的具体行为——下层组件的行为名与参数、本单元内部行为、外部依赖的具体调用。
3. **完整调用链**：从入口行为出发可追踪到所有下级行为，构成完整调用关系（与概要时序图一致）。
4. **粒度一致**：同一文档内所有行为描述粒度一致。

正反例（Flutter）：

✅ 合格粒度——`submit` 行为执行流程：
1. 调用本单元 `_validateForm()`（邮箱格式 + 密码长度）；失败 → 置 `errorState`，流程终止。
2. 置 `loading=true`，调用 `AuthUseCase.login(email, password)`。
3. 成功 → 写入会话态（owner：AuthUseCase），调用 `Get.offAllNamed(Routes.home)`。
4. `AuthFailure.network` → 置 `errorState=networkRetry`；`AuthFailure.credential` → 置 `errorState=badCredential`。

❌ 不合格——`submit` 行为：验证输入，调用登录，处理结果，更新界面。（无调用对象、无失败分支、无状态写入点）

## 4. 章节正文骨架合同（chapters/<slug>.md 模板）

full 链每个章节文件按以下骨架撰写（light 链 design.md §2 的每章同构，可压缩小节层级）。骨架与合同八问的映射在末表——**模板是表达形式，八问是完成条件**，二者必须同时满足。

**破坏性编辑保护（删除/压缩/替换）**：详细章节被重写时，接口事实可删除或替换，但仍有效的合同义务不得消失。删除前必须列 deletion ledger：`deleted_category` / `reason` / `replacement_location` / `removes_contract_obligation` / `reviewer_decision`。L1 章节骨架、UNIT/BHV 承接、行为定义、输入输出错误合同、状态 owner、失败收口、测试映射、不得补造清单必须保留、迁移到命名替代位置，或以 `N/A：<理由>` 显式声明；不得用 endpoint/interface 映射表替代行为合同。

```markdown
# <chapter_target> 详细设计

> doc_type：<九类之一> ｜ l2_status：v1 / pending（pending 须有 L2豁免）
> 承接索引：design-main.md 第 7 节 <chapter_target> ｜ 返回：[design-main](../design-main.md)

## 1. 单元职责
本章承载的 UNIT 清单与一句话职责；与依赖/被依赖单元的关系（调用谁的什么行为、被谁调用）。

## 2. 行为定义
### 2.1 行为清单（每行为一行：行为名 + 简述 + 承接的 BHV 编号）
### 2.2 接口定义（Dart 签名级，禁止超过签名级的实现代码）
``dart
abstract class FoodRecognitionUseCase {
  Stream<RecognitionState> get state;
  Future<RecognitionResult> recognizeFromPhoto(PhotoInput input);
}
``

## 3. 核心数据结构
### 3.1 数据模型（Dart class/enum 签名级；序列化方案按 project-conventions 槽位）
### 3.2 错误类型表
| 错误名 | 错误码/枚举 | 语义 | 上抛/收口位置 |

## 4. 逐行为设计（每个行为一小节）
### 4.x <行为名>
- 函数签名（Dart）
- 行为简述（一句话 + 承接 BHV 编号）
- 输入参数表：| 参数 | 类型 | 取值域/约束 | 必填 |
- 输出表：| 返回值/发射值 | 类型 | 语义 |
- 执行流程（mermaid sequenceDiagram，参与者用真实组件名，步骤编号）
- 流程详述（编号列表，与图中编号一一对应，满足 §3.1 粒度标准）
- 异常处理表：| 异常情况 | 处置（重试/降级/上抛/提示） | 错误转换位置 |

## 5. 状态管理（controller/usecase 类必含；无状态单元写 N/A）
状态字段定义（含初始态）+ 状态转移（mermaid stateDiagram 或转移表）+ 写 owner 声明。

## 6. Widget 设计（仅 page-entry 类）
组件层级（Widget 树要点）、交互（手势/输入）、响应式适配（MediaQuery/LayoutBuilder 要点）。

## 7. 测试映射
| BHV/行为 | 测试层（unit/widget/integration/manual） | 测试点（成功+失败路径逐条） |

## 8. 不得补造清单
本单元不拥有的决策逐条列出。
```

**骨架 ↔ 八问映射**：

| 模板节 | 满足八问 |
|--------|---------|
| 1 单元职责 | 八问 4（依赖正反面的"谁"） |
| 2 行为定义 | 八问 1（BHV 承接）+ 2（签名） |
| 3 核心数据结构 | 八问 2（类型/错误枚举） |
| 4 逐行为设计 | 八问 2/4/5/6（流程、依赖调用、失败收口、事件） |
| 5 状态管理 | 八问 3（读写状态与 owner） |
| 7 测试映射 | 八问 7 |
| 8 不得补造清单 | 八问 8 |

辅助性文本（描述、表格、图内标签）一律中文；代码语法元素（类名/方法名/参数名/字面量）保持英文。

## 5. chapter_loop 执行合同（full 链）

### 5.1 directory_precheck（写作/审核共用前置）

进入任何章节写作前确认：① design_package 路径合法且 `chapters/` 存在；② design-main 承接索引非空且每条有目标文件名；③ pending L2 命中项均有 `L2豁免` 声明；④ `technology_decision_handoff[]` 中被本批引用的条目状态为"选定"（未选定 → 回退概要，禁止详细拍板）。任一失败 → 停止，输出缺口与概要修订动作。

### 5.2 推荐写作顺序（层级）

1. **domain 层**（usecase / service）——业务规则与状态 owner 先固化。
2. **data 层**（repository-datasource / db-dao / api-network）——按 domain 的依赖合同展开。
3. **presentation 层**（page-entry / controller）——只做展示/输入到稳定 domain 行为的适配。
4. **横切**（config-l10n / external-platform）——被各层引用的一等合同收口。

同一 feature 的 usecase 及其直接 repository 视为同一小批次优先完成。

### 5.3 批次与自动审修闭环

- 每批 **1~3 章**；禁止一轮生成全部章节。
- 每批生成后**立即自动 review**（不等用户）：章节模板符合性（§4）、八问完成条件（§3）、粒度（§3.1）、依赖与概要归属一致、L2 差异规则（命中 v1 类型时）。
- 有 finding → 按 §9 判定修订形态 → 直接修复 → 复查受影响的行为/依赖/跨章引用。
- 当前批所有规则均有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。
- 只有"概要源缺失 / 业务语义必须人工确认 / 技术决策未选定 / 修复无法收敛"时才中断并升级用户。

### 5.4 层级 checkpoint

每完成一个层级（§5.2 的 1~4）执行跨章核对，失效项回到对应批次重走审修闭环：

- domain 层后：UNIT↔BHV 承接闭合；状态写 owner 唯一；usecase 间依赖单向无环。
- data 层后：domain 声明的数据依赖全部有承接单元；错误转换位置（SLOT-04）一致；缓存/落库决策只在 repository。
- presentation 层后：页面/controller 只调用稳定 domain 行为；与概要页面流图、时序图一致。
- 横切后：config/ARB key、三方 SDK 合同被引用方闭合；合规依据（权限/采集）逐单元可定位。

### 5.5 完成判定输入

目录级完成 = 全部 chapter_target 的 `chapter_status=passed_by_method_evidence` + 四个层级 checkpoint 通过 + gate 章节闭合（索引↔文件双向）通过。

## 6. 禁止补造清单（详细阶段红线）

- 不得新增概要归属表之外的结构（发现缺口 → 回退概要补归属，再回详细）。
- 不得变更概要已定的 owner、技术决策、scope。
- 不得把 `technology_decision_handoff[]` 中"未选定"的决策在详细阶段私自拍板。
- 不得写实现代码/伪代码超过签名级（方法签名、数据结构定义为上限）。
- 命名、目录、序列化等取值不得偏离 project-conventions 槽位。

## 7. 完成判定与 Gate

详细设计可进入编码，当且仅当（G1~G5 两轨共用；G6~G7 仅 full 链强制）：

- G1 承接索引的每个条目都有对应详细设计单元，无遗漏。
- G2 每个单元的合同八问完整；字段/接口/状态可追溯到概要 owner；满足 §3.1 粒度标准。
- G3 每条行为有测试映射（八问之 7），覆盖成功路径 + 全部失败路径。
- G4 涉及权限/数据采集/三方域名/PII 的单元附合规依据；无制裁 TLD、私有 API、动态执行类设计。
- G5 八问之 8（不得补造清单）逐单元存在。
- G6 章节闭合：索引↔chapters/ 文件双向闭合；每章符合 §4 骨架合同；pending L2 命中项豁免齐全。
- G7 chapter_loop 证据：逐章 `chapter_status=passed_by_method_evidence`，层级 checkpoint 全过，无"一轮全量生成"迹象（多章雷同骨架、无单元级实质内容）。

## 8. 审核基线

- 先证据后结论；finding 带文档/章节锚点。
- 严重度：P1（违反 §6 红线、八问缺项、追溯断链、合规缺失、章节闭合失败——阻塞）；P2（合同不完整但可局部补，如错误枚举不全、粒度局部不达标）；P3（表述建议）。
- 互斥分支：前置失败 → 只输出前置缺口；前置通过 → findings + 概况 + 三选一结论（可进入编码 / 带假设可进入 / 不可进入）。
- 详细设计文档无存量豁免（新文档全量合规）；存量豁免仅适用于实现阶段代码。
- 逐 doc_type 检查矩阵与判级细则在 `client-design-detail-review` skill 的 `references/review-baseline.md`；输出字段合同在其 `references/review-output.md`（编排层产物，不得与本文冲突）。

## 9. 修订形态判定

- **局部修订**：补错误枚举、补测试映射、补一条依赖声明、补一张时序图。
- **文档级重构**：合同与概要 owner 系统性脱节、单元划分跟随名词而非行为、八问大面积空缺、多章雷同骨架（薄文档迹象）。
- 发现概要缺陷（归属错、索引漏）→ 回退概要修订，禁止在详细阶段就地改归属。
