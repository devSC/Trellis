# Project Conventions 模板（项目约定槽位）

> **这是什么**：配置包定义的"项目约定槽位"模板。配置包的 SSOT 只锁方法与团队栈级 canonical，**项目级取值永不进配置包**——每个 App 仓库按本模板填一份取值文件（建议路径：目标仓库 `.trellis/spec/conventions/project-conventions.md`），由各阶段 writing/review Skill 在硬前置中装载。
> **填写规则**：复制本模板 → 删除说明文字 → 逐槽位填写。每个取值必须给**代码证据**（仓库内真实路径）；没有证据的取值视为未填。
> **变更规则**：修改任何槽位取值属于项目级架构决策，需要 ADR 记录后方可生效。

---

## 0. 元信息（必填）

| 字段 | 取值 |
|------|------|
| App 名称 / Dart 包名 | `<app_name>` / `<dart_package>` |
| 仓库路径 | `<repo>` |
| 填写日期 / 填写人 | `<date>` / `<who>` |
| 取值依据 | 实测扫描 / 团队决策（附 ADR 链接） |

---

## 1. 槽位清单（全部必填）

> 每个槽位字段：**决策问题**（要钉死什么）· **本项目取值** · **代码证据**（≥1 条真实路径）· **生效范围**（新代码 only / 全量）· **备注**。
> 取值可以是"待定"，但待定项必须写明决策人与期限，且待定总数 ≤ 2，否则项目约定视为未就绪（硬前置不通过）。

### SLOT-01 序列化方案
- 决策问题：数据类用 `@JsonSerializable` 还是 `@freezed`（或按层混用，需写明分界）？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：此为合法的项目级选择（seek 用 freezed、calorie 禁 freezed 均合法）；但单个项目内**新代码必须只有一种**。

### SLOT-02 新代码目录分界
- 决策问题：新增 presentation / domain / data 代码各进哪个目录？新旧谱系的分界线在哪一层？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：seek 分界在业务层（`lib/new/` 仅 domain+data，UI 全在 `lib/ui/pages/`）；calorie 分界在 UI 层（`lib/new/ui/pages/`）。两者均合法，但必须钉死。

### SLOT-03 接口文件命名
- 决策问题：接口文件用 `i_xxx.dart` + `I` 前缀类名，还是 `xxx.dart`（接口）+ `xxx_impl.dart`（实现）？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**接口与实现必须分文件**是通用硬规则（不可豁免）；本槽位只钉命名风格。

### SLOT-04 错误收口位置
- 决策问题：`DioException` 等底层异常在哪一层转换为业务可消费错误？（repository 层 catch 转换 / 集中 normalizer 工具 + 调用层收口）
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**datasource/api 层不吞异常、必须上抛**是通用硬规则；本槽位只钉转换发生的位置。

### SLOT-05 design model 形态
- 决策问题：是否存在全局 `AppDesignModel`？页面级 design model 的命名与获取方式？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**页面 widget 禁止硬编码尺寸字面量**是通用硬规则；本槽位钉 design model 的具体形态。

### SLOT-06 数据库 helper
- 决策问题：DB 管理类文件路径、版本字段名、建表/迁移的组织方式？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**升级必须按版本分支、新增列给 DEFAULT 或 fromMap 兜底、版本号必须递增**是通用硬规则。

### SLOT-07 l10n
- 决策问题：ARB 源文件路径、生成命令、代码引用入口（裸 `S` / 封装类）、与共享 Sheet 同步的脚本名？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**同步脚本双向写共享 Sheet，agent 禁止自动执行**是通用硬规则；脚本名因 App 而异（calorie：`sync_translate.sh`；seek：`seek_l10_sync.sh`）。

### SLOT-08 代码生成脚本与顺序
- 决策问题：依赖获取、build_runner、intl 生成各用什么脚本、什么顺序、何时触发？
- 本项目取值：
- 代码证据：
- 生效范围：

### SLOT-09 DI 入口
- 决策问题：`Injector`（或等价物）定义在哪个文件？`injector.config.dart` 生成位置？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：DI 注册的 canonical 形态（`@injectable` + binding 内 `Get.lazyPut(() => Injector.provide<C>(), tag: C.tag)`）是团队栈级通用规则，不在本槽位内。

### SLOT-10 路由注册位置
- 决策问题：`RoutePath` 常量与 `GetPage` 注册分别在哪个文件？
- 本项目取值：
- 代码证据：
- 生效范围：

### SLOT-11 repository 实现目录
- 决策问题：repository 实现类落在哪个目录、类名后缀？
- 本项目取值：
- 代码证据：
- 生效范围：
- 备注：**repository 必经 datasource（不直连 DAO/API）**是通用硬规则；本槽位只钉目录与命名。

### SLOT-12 禁止新建页面的老目录
- 决策问题：哪些目录属于旧谱系、禁止新建页面/模块（hooks 将按此拦截）？
- 本项目取值：
- 代码证据：
- 生效范围：

### SLOT-13 网络 API 类
- 决策问题：`@RestApi` 类名、Dio 构建方式、版本号传递方式？
- 本项目取值：
- 代码证据：
- 生效范围：

### SLOT-14 测试约定
- 决策问题：mock 框架（mockito/mocktail）、测试目录是否镜像 lib/ 结构、golden test 是否启用？
- 本项目取值：
- 代码证据：
- 生效范围：

### SLOT-15 存量违例清单（tech-debt 登记）
- 决策问题：已知的存量架构违例有哪些（供 review 的存量豁免判定使用：触碰存量记债不阻塞、新增违例阻塞）？
- 本项目取值：（逐条：违例描述 + 文件路径）
- 生效范围：全量
- 备注：本槽位是**存量豁免机制**的数据源，必须维护；清单外的违例一律按"新增"处理。

---

## 2. 校验清单（writing/review 硬前置使用）

装载本约定文件的 Skill 必须先执行以下校验，任一不通过即终止并提示修复：

- [ ] C1 元信息四字段齐全。
- [ ] C2 SLOT-01 ~ SLOT-15 全部存在；"待定"槽位 ≤ 2 且均写明决策人与期限。
- [ ] C3 每个已填槽位至少 1 条代码证据路径（不校验路径内容，但路径必须存在于仓库）。
- [ ] C4 取值不得与通用硬规则冲突（分层依赖律、接口实现分文件、repository 必经 datasource、datasource 不吞异常、禁硬编码尺寸、同步脚本人工执行——这些不可被槽位豁免）。
- [ ] C5 SLOT-15 存量违例清单存在（可为空清单，但必须显式声明"无"）。

---

## 3. 槽位与门禁的对应关系（参考）

| 槽位 | 谁消费 |
|------|--------|
| SLOT-02 / SLOT-12 | hooks（PreToolUse 目录拦截）、implementation-review |
| SLOT-01 / SLOT-03 / SLOT-11 | detail/implementation writing 与 review |
| SLOT-04 | detail-type-repository-datasource 合同、implementation-review |
| SLOT-05 | detail-type-controller / page 合同、implementation-review |
| SLOT-07 / SLOT-08 | hooks（脚本拦截、代码生成检查）、implementation-writing |
| SLOT-15 | 所有 review 的存量豁免判定 |
