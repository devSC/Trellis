---
name: client-design-detail-writing
description: 用于把 Flutter 客户端概要设计展开为可编码合同（详细设计）。full 链按 directory_precheck + chapter_loop 执行：WX-1~WX-5 前置检查通过后，按 domain→data→presentation→横切 的层级顺序逐章/小批次（每批 1~3 章）生成 chapters/<slug>.md，每批立即自动 review 并修复闭环，层级完成后跑 checkpoint；light 链同口径展开 design.md §2。每个设计单元按合同八问 + 章节正文骨架撰写（UNIT 编号、签名级接口、逐行为输入输出表、mermaid 时序、异常表、测试映射）。规则唯一来源是 `.trellis/spec/harness/detail/` 的 L1/L2 SSOT。
---

# 客户端详细设计撰写

> 层级契约：L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）承载规则正文与完成条件，L2（`detail-type-*.md`）承载类型差异；本 SKILL.md 只做装载顺序、前置检查、chapter_loop 编排与输出要求；`references/` 只承载逐类写法细则、模板与示例。冲突时 L1 > L2 > references > 本文件。

## 目标

- 把概要的 owner 与承接索引展开为可直接编码的合同：每个设计单元（UNIT）回答合同八问，正文符合章节骨架合同（L1 §4），粒度满足 L1 §3.1（可直接实现/明确调用关系/完整调用链/粒度一致）。
- full 链逐章/小批次推进并自动审修闭环——**禁止一次性全量输出全部章节**（必然退化为大纲级薄文档）。
- 只承接概要已决定的 owner、技术决策与 scope；缺口一律回退概要，**禁止在详细阶段补造**。

## 最小输入与自动补全

- 输入参数（均可省略，省略时按默认推进）：
  - `chapter_target`：只写指定章节。
  - `chapter_batch`：指定小批次（≤3 章）。
  - `partial_scope`：只收窄当前章节内部条目（covered_items[]），**不得扩展成新目标范围**；未覆盖项回填 not_covered_items[]。
  - 默认（全部省略）：按 §推荐写作顺序自动逐批推进。
- 需求证据只从概要已显式引用的锚点读取最小片段；不直接拿需求自然语言改变 chapter_target/doc_type/owner。

## 装载顺序（硬前置，任一失败即终止）

1. 读 L1 `.trellis/spec/harness/detail/detail-structure-single-source.md`；不可用 → 终止并提示先安装 guru spec 模板。
2. 读通用 golden-path 与 `.trellis/spec/conventions/project-conventions.md`（校验 C1~C5）。
3. 定位概要主定义（full=`design_package/design-main.md`；light=`design.md` §1），建立 `chapter_target → detail_doc_type（→ 目标文件）` 目标集合。
4. **只对当前批次命中的 doc_type** 读对应 L2（`detail-type-controller / detail-type-usecase / detail-type-repository-datasource`）；命中 pending 类型按 L1 §3 八问展开并标注 `l2_status: pending`（full 链须有 L2豁免，见 WX-5）。
5. 需要逐类写法细则、章节模板或时序图示例时读 `references/chapter-guide.md` / `references/examples/`。

## WX 前置检查（directory_precheck，full 链；任一失败 → 停止并输出缺口与概要修订动作）

- **WX-1 输入键完整**：task.json 含 `guru_chain` 与（full 链）`design_package`；缺失 → 执行级错误，提示补判轨。
- **WX-2 路径边界**：design_package 目录存在且 `chapters/` 存在；目标文件名均落在 chapters/ 内（词法检查，不自动创建缺失目录——缺目录属概要骨架缺口）。
- **WX-3 承接索引**：design-main 第 7 节索引存在、非空、每条有 doc_type 与目标文件名；缺失/为空 → **硬阻断，回退概要**。
- **WX-4 概要 Gate 已确认**：`guru_gate.py status` 显示 overview 已人工确认；未确认 → 停止，提示先完成概要 Gate 收口。
- **WX-5 承接源状态**：本批引用的 `technology_decision_handoff[]` 条目均为"选定"（未选定 → 回退概要，禁止详细拍板）；本批命中 pending L2 的 doc_type 均有 `L2豁免：<doc_type> 理由：…` 声明（无豁免 → 停止，提示先补 L2 或写豁免）。

light 链执行 WX-3/WX-4/WX-5 的等价检查（索引在 design.md §1；产物写 §2）。

## 执行流程（chapter_loop）

1. **建立写作顺序**：按 L1 §5.2 层级排序目标集合——① domain（usecase/service）→ ② data（repository-datasource/db-dao/api-network）→ ③ presentation（page-entry/controller）→ ④ 横切（config-l10n/external-platform）；同一 feature 的 usecase 与其直接 repository 同批优先。
2. **确定当前批次**：按输入参数或自动取下一批（1~3 章）。
3. **逐章生成正文**：按 L1 §4 章节骨架合同撰写目标文件；每个 UNIT 按八问作答（L2 命中时叠加类型差异规则）；暂无法回答的问题写入"未决问题"而非留空或编造。
4. **批内自动 review（不等用户）**：对照 L1 §5.3 清单——骨架符合性、八问完成条件、粒度四条、依赖与概要归属一致、L2 差异规则。
5. **修复闭环**：有 finding → 按 L1 §9 判定修订形态 → 直接修复 → 复查受影响的行为/依赖/跨章引用；规则全部有可验证信号且无未修复 finding → 该批 `chapter_status=passed_by_method_evidence`。
6. **层级 checkpoint**：每完成一个层级跑 L1 §5.4 对应核对；失效项回到对应批次重走审修闭环。
7. **受影响章节复查**：本批修改触及已完成章节的引用时，复查该引用闭合。
8. **输出本批成果**（见输出要求）。
9. **下一目标推荐**：给出下一批建议与剩余目标清单；全目录完成时转入完成判定（L1 §5.5）并提示送审。

## 强制约束

1. L3 不重定义 L1/L2；规则疑义回 L1，引用时给章节号。
2. **禁止一轮全量生成**全部章节；每批 ≤3 章并完成批内审修后才进下一批。
3. 不新增概要归属表之外的结构；不变更 owner/技术决策/scope；缺口回退概要（L1 §6）。
4. 不写超过签名级的代码（方法签名、数据结构定义为上限）。
5. 命名/目录/序列化取值按 project-conventions 槽位；行为命名按概要 L1 §4.1。
6. `partial_scope` 只收窄不扩展；未覆盖项必须显式回填 not_covered_items[]，不得静默丢弃。
7. 状态写 owner 必须与概要归属一致；发现归属错误 → 回退概要修订，不就地改。
8. 每行为测试映射覆盖成功 + 全部失败路径（八问之 7）；写不出测试点的行为视为粒度不达标，回到第 3 步。
9. 涉权限/数据采集/三方域名/PII 的单元必须落合规依据；不写制裁 TLD、私有 API、动态执行类设计。
10. 辅助文本中文；代码语法元素英文。
11. 中断升级仅限四种情形：概要源缺失 / 业务语义必须人工确认 / 技术决策未选定 / 修复无法收敛；其余情况自动闭环推进。
12. 全目录完成后提示送审：加载 `client-design-detail-review`；Gate 结论"可进入编码"后按 gate_mode 完成 confirm 人工收口（通道与红线见 review skill「Gate 收口」节及 workflow 机制节）。

## 输出要求（writing 专属）

每批输出：

- `execution_mode=directory_precheck+chapter_loop`（light 链标注 light+chapter_loop）
- `目标集合解析`（总数 / 已完成 / 本批 chapter_target 清单与 doc_type）
- `WX 前置状态`（首批输出 WX-1~WX-5 逐项；后续批只报变化）
- `partial_scope`（如有：covered_items[] / not_covered_items[]）
- 本批正文（或落盘文件清单）
- `批内自动 review 结果`（finding 数 / 修复迭代次数 / chapter_status）
- `层级 checkpoint 状态`（到达层级边界时输出）
- `未决问题与升级项`（如有，按强制约束 11 分类）
- `下一目标推荐`

全目录完成时追加：`完成判定`（L1 §5.5 三要素）+ 送审与人工确认指引（强制约束 12）。

前置失败输出：`writing_stage=blocked_requires_overview_fix` + 缺口清单 + 概要修订动作，不产出正文。

## 参考资料

- 详细阶段中立规范（L1）：`.trellis/spec/harness/detail/detail-structure-single-source.md`
- 类型差异（L2）：`.trellis/spec/harness/detail/detail-type-controller.md` / `detail-type-usecase.md` / `detail-type-repository-datasource.md`
- 逐类写法细则与章节模板：`references/chapter-guide.md`
- 章节成稿样例：`references/examples/chapter-usecase-minimal.md`
- 通用方法 SSOT：`.trellis/spec/guides/golden-path.md`；项目取值：`.trellis/spec/conventions/project-conventions.md`
