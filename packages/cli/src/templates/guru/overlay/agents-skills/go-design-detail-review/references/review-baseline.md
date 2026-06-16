# Go 详细审核取证矩阵与严重度判级（references）

> 编排层产物：只承载取证操作、逐 doc_type 检查清单与判级细则；规则正文以 L1（`.trellis/spec/harness/detail/detail-structure-single-source.md`）与命中 L2（`detail-type-{entry-api,biz,repository-data}.md`）为准。冲突时 `L1 > L2 > references > SKILL.md`。
> 本文件的 D1~D9 与 G1~G7 编号即 SKILL.md 诊断流程与 L1 §7 Gate 的同名项；横向硬规则真源 `.trellis/spec/guides/golden-path.md`，项目槽位 `.trellis/spec/conventions/project-conventions.md`（SLOT-01~SLOT-17）。

## 1. 取证准备（所有 scope 模式先做）

1. 固化编号与小节锚点（被审章节文件）：
   - `rg -n "UNIT-|BHV-" <章节文件>` 固化设计单元与承接行为编号。
   - `rg -n "^#{1,4} " <章节文件>` 固化小节锚点（D1 模板节打钩、Finding location 引用都依赖它）。
   - `rg -n "doc_type|l2_status|entry_kind" <章节文件>` 固化头部标注（D1 用）。
2. 概要侧基线先取证（后续全部双向核对以此为准，不在详细侧重建）：
   - `design-main.md` 归属判定表 owner 集合（transport/service/repository/domain 四值）；
   - 详细设计承接索引目标集合 `chapter_target → detail_doc_type → chapters/<slug>.md`；
   - 第 5 节 UC 承接表 `bhv_refs`/`index_refs`、时序图策略表；
   - `technology_decision_handoff[]` 的 `selected`/`selection_status`（映射 SLOT-01~SLOT-17）；
   - 五字段执行基线 `stack_profile_ref`/`project_profile_ref` 等（EX-5 用）。
3. 机器 Gate 先行（人工不重复机检，结构 findings 直接并入）：
   - `python3 .trellis/scripts/guru/guru_gate.py detail <task_dir>`（合同八问四标记、章节闭合、pending L2 拦截）；
   - `python3 .trellis/scripts/guru/guru_gate.py trace-matrix <task_dir> --strict`（行为×归属×单元×测试×切片，编号断链）。
4. 跨层下游合同取证（D3/D4 用）：被审单元八问 4 声明的 `direct_dependencies[]` 逐条到对应章节文件，核对被调用接口/方法签名确实存在。

## 2. 通用检查矩阵（七类 doc_type 共用，对应 D1~D9）

| 诊断 | 取证操作（先证据） | 缺口判级 |
|------|------------------|---------|
| D1 骨架 | 对照 L1 §4 章节模板（1 单元职责 / 2 行为定义 / 3 核心数据结构 / 4 逐行为设计 / 5 状态与事务 / 6 数据合同 / 7 测试映射 / 8 不得补造）逐节打钩；N/A 节须有声明；头部 `doc_type` 落七类、`l2_status`（v1/pending）、`entry_kind`（仅 entry-api）标注正确 | 缺模板节 P1；N/A 无声明 P2；pending 类型缺 `l2_status: pending` 或缺 design-main `L2豁免` P1 |
| D2 八问 | 逐 `UNIT-<slug>` 按 L1 §3 合同八问括号内可验证信号取证（承接 BHV / 输入·输出·错误结果 / 读写状态 / 调用依赖正反面 / 失败收口 / 事件后置 / 测试映射 / 不得补造）；命中 v1 类型叠加 L2 特化问 | 任一问缺 P1 |
| D3 追溯 | `UNIT ↔ BHV` 闭合（裸 token，无幽灵 BHV、无无承接单元）；状态写 owner 回指概要归属表行且层一致；八问 4 依赖在概要架构图边上，且形成「依赖 → New* 构造入参 → 字段赋值 → usage」闭环 | 幽灵 BHV / 孤儿行为 / owner 不一致 / 依赖无承接 P1 |
| D4 分层一致性 | 八问 4 依赖正反面对照 §6.0 分层依赖律 + 命中 L2 硬规则逐条（handler 不直连 repository/`database/sql`、repository 不反向 import service、service↔service 单向无环、协议物件 `http.Request`/`ResponseWriter` 不进 service、除 domain 外不跨 internal 兄弟包导入、domain 无 I/O） | 任一违例 P1（阻断，不给通过性结论） |
| D5 接口签名级 | service/handler 接口全集逐方法 Go 签名：首参 `ctx context.Context`、末返回 `error`；domain struct + JSON tag；可穷举概念用具名枚举/`iota`，禁裸魔法值；超签名级实现体（>15 行）视为越界信号 | 非签名级（「提供 XX 能力」无签名）P1；魔法值 P2 |
| D6 粒度判定 | 抽查 ≥1 行为全流程（§3.1 四条）：步骤逐条有具体被调用下层方法 + 参数（如 `userRepo.Create(ctx, params)`）、本单元内部判定、错误返回点、状态写入点、context/timeout；事务边界三选一给结论（无显式事务 / 本地 DB 事务 / 一致性模式） | 「见概要」「处理 XX」「调用 service」无调用对象 P1；事务边界缺结论 P2 |
| D7 测试映射 | 每条承接行为 ≥1 成功用例 + 全部失败路径各 1 用例，逐行映射 `BHV-NNN`/`UNIT-<slug>`；测试层合理（biz 用 mock repository 的 unit test、handler 用 `httptest`+mock service、repository 用集成测试，测试框架取 SLOT-04） | 高风险链路（鉴权/会话/数据删除/迁移/付费）漏测 P1；普通失败路径漏测 P2 |
| D8 错误与合规 | sentinel error 全集逐条 + 错误三态映射（入口校验失败 / service sentinel / 兜底未知错误 → HTTP 状态码），每个 sentinel 有 `errors.Is` 分支且存在兜底 500；异常表逐行对应一条失败路径 BHV 或八问 1 行为分支；`rg -i "secret\|api_key\|password\|token\|AKID\|-----BEGIN"` 扫硬编码凭证；制裁 TLD / 私有 API / 动态执行扫描；密钥只写 env 变量名引用回指 config（SLOT-08） | 字符串比较错误 / 吞错（`_ = err`、裸 `return`）/ handler 自造平行错误体系 / 内部文案直接回客户端 / 真实 secret / 私有 API / 动态执行 P1；异常表↔失败 BHV 失配、sentinel 枚举不全、转换位置缺标 P2 |
| D9 补造红线 + 层级越界 | 概要外结构、改 owner、私自拍板未选定 SLOT 槽位、超签名级实现体（>15 行）；项目约定声明引入 wire/sqlc 等 profile 时，业务详细正文展开 generated Repo 方法表 / `PropertyFilter/PageRequest/WithTx` / `*_guru.pb.go` / ProviderSet/Wire / proto·buf generate 细节（除非仅出现在 `framework_reference_ref`/实现期参考字段） | 补造 / 改 owner / 拍板槽位 / 越界实现体 P1；层级越界 P1 |

> 说明：SKILL.md 诊断流程把「接口签名级」单列为 D5、「粒度」为 D6、「测试」为 D7、「错误与合规」为 D8、「补造红线+层级越界」为 D9，本表与之一一对齐；L1 §7 的 G2 同时覆盖本表 D2/D4/D5/D6（粒度与分层在 G2 内合并判定）。

## 3. 逐 doc_type 附加检查

### v1 类型（按 L2 逐条硬规则；只装命中类型，不全量装）

| doc_type | 附加取证（命中 L2 硬规则） | 典型 P1 |
|----------|--------------------------|---------|
| `entry-api` | 头部 `entry_kind`（`http_endpoint`/`cli_command`/`scheduled_job`/`message_consumer`）已标注；每个 `route+method`（如 `POST /api/v1/users`）绑定独立 `BHV-NNN` + handler 方法 + 目标 service 方法；req/resp JSON struct 签名级；`r.Context()` 透传（禁 `context.Background()` 替代）；错误三态→HTTP 状态码映射闭合且有兜底 500；解码走严格解码（`DisallowUnknownFields`）；method 不匹配返回 405 而非静默 200 | handler 直连 repository/`database/sql`；handler 承载业务规则/校验；丢失 ctx；无兜底 500 |
| `biz` | service 是状态/能力 owner：业务状态写 owner 全局唯一；sentinel error 全集（区分业务可恢复 / 系统不可恢复）逐条且与 handler 映射一致；核心能力（P0/P1）拆为可编码步骤；service↔service 单向无环（构造注入具体类型）；事务边界三分法结论；不直接持有 `*sql.DB`、不拼 SQL、不 import `net/http` | 状态双写（同一业务状态出现在两个 service）；biz 直接写 SQL；service 互相调用成环；核心能力停留在「调用 X」黑盒 |
| `repository-data` | Repo 接口被某 service 声明消费；查询意图 / 过滤 / 排序稳定性 / 分页 / 事务边界写明；表 DDL 签名级（不写迁移脚本正文）+ 字段字典 + 索引/约束；`sql.ErrNoRows → domain/repository sentinel`（`ErrNotFound`）转换点标注且与 service 两侧一致；参数化查询（`$1` 占位符，禁字符串拼 SQL）；写操作 0 行→`ErrNotFound`；不承载业务规则、不返回 `ErrValidation` | repository 反向 import service；repository 含业务判定；裸抛 `sql.ErrNoRows`；字符串拼接 SQL；迁移跳号/无 down |

### pending 类型（L1 八问 + 豁免核查；不装 L2）

命中 `domain`/`config`/`external`/`runtime` 时：头部须 `l2_status: pending`；full 链 design-main 须有对应 `L2豁免：<doc_type> 理由：…`（无豁免 → P1）。各类附加取证：

- `domain`：实体/值对象/参数结构体（`<Entity>` / `<Entity>Params`）+ JSON tag；sentinel errors（`var ErrXxx = errors.New("...")`）唯一定义；纯函数业务规则、构造校验；八问 8 必含「无 I/O、无副作用、不导入任何 internal 兄弟包」。出现 `Validate()` 在 domain（应属 service）、`Scan()`（应属 repository）、import 兄弟包、ORM tag（未切 SLOT-02 前）→ P1。
- `config`：配置键 + env 变量名（前缀按服务区分 SLOT-08，如 `<SVC>_*`）+ 默认值 + `config.Load()` 装载 + 校验/启动失败行为 + 消费方引用；secret 只写 env 变量名/引用（不落明文）；业务规则默认值仍归 biz/domain。出现明文 secret、`.env` 当线上合同、配置反向依赖业务包 → P1。
- `external`：本系统出站调用外部系统的协议 / 请求·响应·错误 / 鉴权边界 / SLA·限流 / 超时重试 / adapter 消费边界；凭证只写 `api_key_env_name`/`credential_ref`/默认凭证链；跨服务契约落 `packages/contracts/`（零行为零业务依赖）。把本系统自有能力伪装成外部依赖、把对外暴露入口（Webhook/回调）误归 external（应归 entry-api 的 http_endpoint 子类）、真实 key → P1。
- `runtime`：进程/服务拓扑 + `main()→app.New()→app.Run()→app.Shutdown()` 生命周期 + 信号处理（SIGINT/SIGTERM）+ context 超时来自 config + 健康检查 + 启动顺序 + 发布/回滚边界。缺生命周期四步、`*http.Server` 无 timeout、Shutdown 漏关 db、把 `http.ErrServerClosed` 当致命错误、写部署脚本/Dockerfile/CI/Runbook 正文 → P1（最后一项属 L1 §10 不适用场景越界）。

## 4. 跨层链路核对（directory_final 第②段 / layer_checkpoint）

| 层边界 | 核对项 | 缺口判级 |
|--------|--------|---------|
| transport→service（entry checkpoint） | handler 只调稳定 service `XxxService` 行为，不直连 repository/DB；每个 `route+method` 绑定 `BHV-NNN`+handler+service 方法；ctx 透传；错误三态映射闭合且与 service sentinel 全集一致 | 直连 repository/DB P1；映射缺兜底 P1；route 无 BHV 承接 P1 |
| service→repository（service checkpoint） | service 声明的 `XxxRepository` 接口被对应 repository 章节定义；业务状态写 owner 全局唯一；service↔service 单向无环；sentinel error 全集与 handler 一致 | 状态双写 P1；环依赖 P1；接口无承接章节 P1 |
| repository→domain（repository checkpoint） | repository 返回/扫描的 domain 实体均已在 domain 章节定义；`sql.ErrNoRows → ErrNotFound` 转换点两侧一致；无业务判定下沉、无反向 import service | 依赖无承接 P1；转换两侧不一致 P2；业务下沉 repository P1 |
| domain（domain checkpoint） | 实体/值对象/sentinel error 唯一定义、被上层引用者均已定义；domain 无反向依赖、无 I/O、不导入 internal 兄弟包 | 反向依赖/有 I/O P1；引用未定义实体 P1 |
| 横切（config/external/runtime checkpoint） | config key 有消费方且 env 前缀按服务区分；external 凭证仅引用 env 变量名；runtime 生命周期 `New/Run/Shutdown` 与超时来自 config；合规依据（鉴权/采集/三方域名）逐单元可定位 | 孤儿合同 P2；凭证落明文 P1；生命周期断裂 P1 |
| 全局 | 状态写 owner 全局唯一；同一 sentinel error 枚举跨章定义一致；同一 domain 实体跨章引用形状一致 | 多写 owner P1；跨章定义漂移 P2 |

## 5. 覆盖率核对（directory_final 第③段）

1. 概要承接索引目标集合 vs 现存 `chapters/<slug>.md`：双向差集（索引引用缺文件 / 孤儿章节文件）。缺失目标文档只出「缺失结论 + 修订方案」，不进 D 诊断。
2. 归属表 owner 全集 vs 详细单元：每个 owner（transport/service/repository/domain）被至少一个 `UNIT-<slug>` 覆盖。
3. UC 承接表 `index_refs`/`bhv_refs` vs 章节：每个 UC 的链路在详细侧（entry→biz→repository→domain）可走通。
4. 概要时序图参与者/调用 vs 详细逐行为设计：抽查 ≥1 个 UC 的时序步骤在对应章节有同名行为与一致调用方向。
5. `technology_decision_handoff[].detail_expansion_targets` vs 索引：被引用的技术合同有承担它的目标 doc_type 章节（如游标分页落 repository-data、provider 凭证落 config/external）。

## 6. 薄文档判定（优先于逐条 finding）

满足任一即判薄文档 → 结论直接「不可进入」+ 文档级重构（L1 §9），不再逐条列局部 finding：

- ≥2 章骨架雷同且无单元级实质内容：小节结构相同且正文为占位级（输入/输出参数表空 / 逐行为流程详述 <3 步 / 测试映射 ≤1 行 / 无 mermaid 时序与异常表）。
- 全目录一次性全量生成迹象（违反 L1 §5 chapter_loop「禁止一轮生成全部章节」）叠加上一条任意命中：`chapter_status` 普遍缺失 / 无批内自动审修痕迹。
- 逐行为设计普遍缺接口签名（D5 大面积非签名级）或普遍缺错误三态映射。
- 分层归属系统性错位（biz 大面积直接写 SQL、handler 大面积承载业务规则、domain 大面积 import 兄弟包）。

## 7. 严重度判级规则

- **P1（阻断）**：D1~D9 表中标注 P1 的项；§4 跨层 P1 项；薄文档；章节闭合失败、编号断链（机检并入）；§6.0 golden-path 任一硬规则违例（重型框架、跨层/反向/循环依赖、非 sentinel 错误体系、缺生命周期、明文 secret）——红线违例不可豁免、不给通过性结论。
- **P2（应修）**：表中 P2 项；粒度局部不达标（单个行为）；孤儿合同；事务边界缺结论；错误转换位置缺标；sentinel 枚举不全；跨章定义漂移。
- **P3（建议）**：表述 / 格式 / 命名一致性 / 图标签中文化。
- 判级冲突取高；同根因合并为一条 finding 列全部位置。
- 详细设计文档无存量豁免（SLOT-17 存量豁免只在实现/审核阶段对代码生效，不为详细设计缺陷开口）。

## 8. 结论判定（互斥三选一）

- 任一 P1 → **不可进入实现编码**（阻塞 P1 清单 + 修订形态：局部修订 / 文档级重构按 L1 §9；概要缺陷标注「回退概要」）。
- 仅 P2 且每条有明确修订路径 + 用户已记录假设 → **带明确假设可进入**（逐条假设、依据、验证时点）。
- 无 P1/P2 → **可进入实现编码**。
- 前置失败（EX-1~EX-6 任一）→ 不进入本节，按 `references/review-output.md` 分支一输出前置缺口。
- 结论为「可进入 / 带假设可进入」时必须给 Gate 收口指引（用户终端 `guru_gate.py confirm detail <task_dir>`，strict 模式 agent 不得代跑；详见 SKILL.md Gate 收口节）。
