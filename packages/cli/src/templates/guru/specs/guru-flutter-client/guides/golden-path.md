# 黄金路径：Flutter 客户端开发（通用方法 SSOT · v2）

> **v2 双向拆分版**：本文只包含**类别级方法**（任何 Flutter 客户端怎么做对）与**团队栈级 canonical**（Guru 团队技术栈统一约定）。**项目级取值一律不出现在本文**——凡标注 `[SLOT-xx]` 处，取值见目标仓库的 `project-conventions.md`（模板：`.trellis/spec/conventions/project-conventions.template.md`）。
> 脚手架模板、`guru_lints` 规则、各 agent 适配层**全部从本文派生**，两端都指向本文，不各写一份（ADR-0002（见 client_agent 仓库 docs/adr/））。改约定先改这里。
> 相关决策：ADR-0001（client_agent 仓库） · ADR-0003（client_agent 仓库） · 设计文档：client-harness-design.md（client_agent 仓库 docs/design/，PRD：devSC/client_agent#1）
> v1 → v2 变更：移除 App 专属参数表与 calorie 特定取值（迁至 project-conventions）；§13 待校准关账（13.1/13.2/13.3/13.5/13.7 已关，13.4/13.6 结论落入 calorie conventions）；usecase 依赖规则按 seek 实测校准放宽。

核心思想：**一个需求 = 它真正碰到的那几层的 canonical 迷你路径之组合。** 整页 feature 只是"presentation + 下层"的全栈组合；非 UI 需求就是"只跑下层"。

---

## 1. 入口决策树：这个需求碰哪几层？

```
需求进来
 ├─ 要给用户看的新界面?          → 跑 §6 Presentation + 它需要的下层
 ├─ 只改业务规则/编排逻辑?        → 只跑 §3 Domain(service/usecase)
 ├─ 只改持久化/缓存/数据合约?      → 只跑 §4 Data(repository/datasource/DAO/DB)
 ├─ 只接一个后端接口?            → 只跑 §5 Network(@RestApi + model)，再交给 §4 消费
 └─ 只加/改文案?                → 只跑 §7 l10n
跑完任意层都要过 §8 代码生成 + §9 自检。
```

---

## 2. canonical 总则（跨层，所有迷你路径都遵守）

### 2.1 分层依赖律（最重要，见 ADR-0003）
依赖方向**只能从上往下**，严禁反向或同层横跳：
```
Presentation(page/controller)
        ↓ 只依赖
UseCase(业务流程编排，有状态/响应式流)
        ↓ 只依赖
Service(无状态工具/跨域转换)  +  Repository(数据访问合约)
        ↓ 只依赖
DataSource(local/remote)
        ↓ 只依赖
DAO / API
```
**硬禁止（lint 查 import 方向）**：
- ❌ data 层依赖 usecase（反向依赖）。
- ❌ controller 直接依赖 repository 实现 / DAO / API 类（跳过 usecase）。
- ❌ usecase 之间**环形或双向**依赖。

**usecase → usecase 单向依赖：允许**（v2 校准放宽，活例：seek `ChatUseCase` 构造注入 `AiUseCase`）。约束：必须单向、构造注入接口；当协调超过 2 个 usecase 或出现"互相调用"倾向时，抽更高层编排 usecase 或把共享逻辑下沉到 service/repository。

### 2.2 接口强制分离
service / usecase / repository / DAO / datasource 一律**接口与实现分两个文件**（通用硬规则，不可豁免）。接口文件命名风格（`i_xxx.dart` + `I` 前缀 vs `xxx.dart` + `xxx_impl.dart`）按 `[SLOT-03]` 取值，单项目内必须统一。

### 2.3 DI 唯一策略（团队栈级 canonical，ADR-0001）
- 实现类一律 `@LazySingleton(as: <接口>)` 注解进 injectable 生成图；`@Singleton` 仅限**无状态**单例且注释理由；**禁止**"无注解 + factory module"提供。
- controller 一律 `@injectable`；page binding 一律：
  ```dart
  Get.lazyPut<C>(() => Injector.provide<C>(), tag: C.tag);
  ```
- 禁止：binding 里直接 `new`、binding lambda 里手写 provide 子依赖、页面内 `Get.create`、`build()` 里 `Get.put`。`permanent: true` 仅限根壳 / Tab 宿主等真·全局，且需注释理由。
- DI 入口文件位置按 `[SLOT-09]`。

### 2.4 命名 / 目录 / 序列化
- repository 实现目录与类名后缀按 `[SLOT-11]`，单项目内唯一。
- 序列化方案（`@JsonSerializable` vs `@freezed`）按 `[SLOT-01]`，单项目内新代码唯一。
- 新代码目录分界（新页面/新业务模块进哪）按 `[SLOT-02]`；禁止新建页面的老目录按 `[SLOT-12]`，由 hooks 拦截。

### 2.5 Service vs UseCase 职责边界
- **Service** = 无状态、可重用工具 + 跨域转换。**不维护流**。
- **UseCase** = 有状态业务流程 + 维护响应式流（`BehaviorSubject` / `Rx`）+ 提供业务 API 给 controller。

### 2.6 文件大小指南（非硬性）
usecase/repository > 600 行 → 评审职责单一性；> 1000 行 → 必须拆或写明理由；> 1500 行 → lint error 强制拆。

---

## 3. Domain 迷你路径（service / usecase）

新增 usecase（示例采用 `i_` 前缀风格演示，实际命名按 `[SLOT-03]`）：
```dart
// 接口文件（独立）
abstract class IRecipeManagementUseCase {
  Stream<List<Recipe>> observeRecipes();
  Future<void> saveRecipe(Recipe r);
}

// 实现文件（独立）
@LazySingleton(as: IRecipeManagementUseCase)
class RecipeManagementUseCase implements IRecipeManagementUseCase {
  final IRecipeRepository _repo;          // ✅ 注入 repository / service / 单向 usecase
  RecipeManagementUseCase(this._repo);    // ❌ 不得形成 usecase 环
}
```
需要无状态工具时再加 service（接口+实现分文件，`@LazySingleton(as: <接口>)`）。

## 4. Data 迷你路径（repository / datasource / DAO / DB）

```dart
// 接口（domain 侧）
abstract class IRecipeRepository { Future<List<Recipe>> all(); }

// 实现（目录按 [SLOT-11]）
@LazySingleton(as: IRecipeRepository)
class RecipeRepositoryImpl implements IRecipeRepository {
  final IRecipeLocalDataSource _local;     // ✅ 必经 datasource，不直接调 DAO/API（通用硬规则）
  final IRecipeRemoteDataSource _remote;
  RecipeRepositoryImpl(this._local, this._remote);
}
```

**新增一张表（DB）**（helper 文件位置与版本字段名按 `[SLOT-06]`）：
1. 表名/列名常量 + DDL 集中定义（不散落在 DAO 里）。
2. onCreate 注册建表语句。
3. onUpgrade **按版本分支**迁移，版本号 +1；新增列给 DEFAULT 或在 fromMap 兜底；不许跨版本漏写（通用硬规则）。
4. DAO 接口与实现分文件，`@LazySingleton(as: <接口>)`。

## 5. Network 迷你路径（API + model）
1. `@RestApi` 类（类名与 Dio 构建按 `[SLOT-13]`）加方法。
2. req/resp model 按 `[SLOT-01]` 序列化方案。
3. **datasource/api 层不吞 `DioException`，必须上抛**（通用硬规则）；转换为业务错误的位置按 `[SLOT-04]`。

## 6. Presentation 迷你路径（页面，= 全栈 feature 的顶层）

新建页面进 `[SLOT-02]` 钉死的目录。canonical 规则（权威见 ADR-0001）：

**Routes**（文件位置按 `[SLOT-10]`）：`RoutePath` 常量 + `GetPage(name, page, transition, binding)` 注册。

**Controller**（基类固定 `LifecycleController`，import 自 `package:gurusdk/guru_utils/controller.dart`）：
```dart
@injectable
class FooController extends LifecycleController {
  static String get tag => "FooController";
  final IFooManagementUseCase _useCase;   // ✅ 依赖 usecase/service，不依赖 repository/DAO
  FooController(this._useCase);
}
```

**Binding**（canonical DI 形态，见 §2.3）：
```dart
class FooBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<FooController>(() => Injector.provide<FooController>(), tag: FooController.tag);
  }
}
```

**Page**：消费 design model（形态按 `[SLOT-05]`），**禁止硬编码 `EdgeInsets`/尺寸字面量**（通用硬规则）。`@DesignSpec(width, height)` + `@SpecFontSize/@SpecEdgeInsets/@SpecWidth` 注解 + `_XxxDesignModel.get()` 由 design_generator 生成。

**widget 级 controller**：也必须 `@injectable` + 在**页面 binding** 里 `lazyPut`；禁止 `build()` 里 `Get.put`。

**mixin**：controller 超过约 300 行时按"完整职责域"抽 mixin，mixin 之间不得共享 `final` 字段（指南，不强制，不进 lint）。

## 7. l10n 迷你路径（跨切面）
1. 往 ARB 源文件（路径按 `[SLOT-07]`）加 key（英文源）。
2. 生成：`flutter pub run intl_utils:generate`。
3. 代码引用入口按 `[SLOT-07]`（裸 `S` 或项目封装），跟随现有页面写法。
4. ⚠️ **l10n 同步脚本双向写共享 Google Sheet：agent 禁止自动执行，属人工受控步骤**（通用硬规则；脚本名按 `[SLOT-07]`，hooks 按此拦截）。

## 8. 代码生成（顺序固定，脚本名按 `[SLOT-08]`）
```
依赖获取脚本（仅当 gurusdk/依赖变动）
build_runner 脚本（injectable / retrofit / json_serializable|freezed / design_generator）
intl 生成（仅当动了 ARB）
```

## 9. 自检
```bash
dart run custom_lint    # guru_lints 门禁（建成后）
flutter analyze
```

---

## 10. 禁止清单（汇总，门禁拦）

**通用硬禁止（任何项目不可豁免）**：
- ❌ data 层 import usecase；controller 直连 repository 实现/DAO/API（§2.1）。
- ❌ usecase 环形/双向依赖（§2.1）。
- ❌ 接口与实现混在一个文件（§2.2）。
- ❌ 无注解 + factory module 提供依赖（§2.3）。
- ❌ repository 绕过 datasource 直调 API/DAO（§4）。
- ❌ datasource/api 层吞 `DioException`（§5）。
- ❌ binding 里 `new` / 页面里 `Get.create` / `build()` 里 `Get.put`（§6）。
- ❌ controller 不继承 `LifecycleController`（§6）。
- ❌ 页面 widget 硬编码 `EdgeInsets`/尺寸字面量（§6）。
- ❌ agent 自动执行 l10n 同步脚本（§7）。

**按项目约定执行的禁止（取值见 project-conventions）**：
- ❌ 违反 `[SLOT-01]` 序列化方案（如该项目禁 freezed 则新代码不得引入）。
- ❌ 在 `[SLOT-12]` 老目录下新建页面/模块。
- ❌ repository 实现落在 `[SLOT-11]` 之外的目录。

## 11. 门禁映射（三层各管什么）
| 规则 | 脚手架 | guru_lints | review |
|------|:---:|:---:|:---:|
| §2.1 分层依赖律 | | ✅(import 方向) | ✅ |
| §2.2 接口分离 | ✅ | ✅ | |
| §2.3 DI 策略 | ✅ | ✅ | ✅ |
| §2.4 命名/目录/序列化 | ✅ | ✅(读项目约定) | |
| §2.5 service/usecase 边界 | | | ✅ |
| §2.6 文件大小 | | ✅(>1500 error) | ✅ |
| §4 repository 经 datasource | ✅ | ✅ | |
| §5 异常不吞 | | ✅ | ✅ |
| §6 presentation 5 条 | ✅ | ✅ | ✅ |
| §7 同步脚本受控 | | | hooks |

## 12. 派生关系（给 build 用）
- **脚手架模板** ← §3/§4/§5/§6 的代码块参数化（参数 = project-conventions 槽位）；按入口决策树条件组合。
- **`guru_lints` 规则** ← §2 + §4 + §5 + §6 + §10（槽位类规则运行时读取目标仓库 project-conventions）。
- **配置包 Skill（概要/详细/实现三件套）** ← 全文 + 各自 references；所有 agent 适配层**指向本文**，不各写一份（ADR-0002）。
- **hooks** ← §7 同步脚本拦截 + §10 老目录拦截（读 `[SLOT-07]`/`[SLOT-12]`）+ §8/§9 自检回灌。
