# Project Conventions — ai_diet（guru_ai_calorie）

> 按 [project-conventions.template.md](./project-conventions.template.md) 填写。本文件暂存于配置包，**待迁回 calorie 仓库** `.trellis/spec/conventions/project-conventions.md`。
> 取值依据：2026-06-12 对 `guru_ai_calorie` 的实测扫描（同时关闭 golden-path v1 §13.4/§13.6/§13.3 待校准项）。

## 0. 元信息

| 字段 | 取值 |
|------|------|
| App 名称 / Dart 包名 | AI Calorie / `ai_diet` |
| 仓库路径 | `guru_ai_calorie` |
| 填写日期 / 填写人 | 2026-06-12 / client_agent 配置包（实测扫描） |
| 取值依据 | 实测扫描；待团队 redline 确认 |

## 1. 槽位清单

### SLOT-01 序列化方案
- 本项目取值：一律 `@JsonSerializable`；**禁止引入 `@freezed`**。
- 代码证据：grep `@JsonSerializable` 127 处、`@freezed` 0 处。
- 生效范围：全量。

### SLOT-02 新代码目录分界
- 本项目取值：分界在 **UI 层**——新页面一律进 `lib/new/ui/pages/`（现 26 个目录、近期新增 36 个文件）；`lib/ui/pages/` 为旧谱系不再新增。domain/data 无新旧目录之分。
- 代码证据：`lib/new/ui/pages/`（analyze_food、scan_food、settings 等 8 个顶层页面）。
- 生效范围：新代码。

### SLOT-03 接口文件命名
- 本项目取值：`i_xxx.dart` + `I` 前缀类名（接口）+ `xxx_impl.dart` / `xxx_service.dart`（实现）。
- 代码证据：`lib/domain/usecase/i_goal_management_usecase.dart` + `goal_management_usecase.dart`。
- 生效范围：新代码（存量混合文件见 SLOT-15）。

### SLOT-04 错误收口位置
- 本项目取值：**repository 层** catch `DioException` 后转换/降级（如回落缓存）；无集中 normalizer。个别 usecase 自行处理属存量。
- 代码证据：`lib/data/repository/user_repository_impl.dart:81`。
- 生效范围：新代码。

### SLOT-05 design model 形态
- 本项目取值：**全局 `AppDesignModel`（存在，347 处引用）+ 页面级 `<Feature>DesignModel`** 双消费；`@DesignSpec` 注解（53 处）+ design_generator 生成。
- 代码证据：grep `AppDesignModel` 347 处、`@DesignSpec` 53 处。
- 生效范围：全量。

### SLOT-06 数据库 helper
- 本项目取值：`lib/data/local/database/database_manager.dart`，版本字段 `_dbVersion`（**第 13 行，当前 = 8**）；`_onCreate`（156–175 行）调 `db.execute(TableDefinitions.createXxxTableSql)`；`_onUpgrade`（178–277 行）按 `if (oldVersion < N)` 级联分支；DDL 集中在 `lib/data/local/database/table_definitions.dart`。
- 代码证据：上述路径与行号（2026-06-12 实测）。
- 生效范围：全量。

### SLOT-07 l10n
- 本项目取值：ARB 源 `lib/l10n/intl_en.arb`；代码引用经封装类 **`AppStrings`**（`lib/localizations/app_strings.dart`，`AppStrings.get()` 464 处 vs 裸 `S` 5 处）；同步脚本 **`sync_translate.sh`**（agent 禁止自动执行）。
- 代码证据：`lib/localizations/app_strings.dart:7-26`。
- 生效范围：全量。

### SLOT-08 代码生成脚本与顺序
- 本项目取值：`gurusdk_get.sh` → `code_prebuild.sh`（build_runner：injectable/retrofit/json_serializable/design_generator）→ `flutter pub run intl_utils:generate`（仅动 ARB）。
- 代码证据：仓库根目录三个脚本；pubspec.yaml `intl_utils`。
- 生效范围：全量。

### SLOT-09 DI 入口
- 本项目取值：`Injector.provide<T>()`（66 处引用），定义于 `lib/app/injector/injector.dart`。
- 代码证据：grep `Injector.provide` 66 处。
- 生效范围：全量。

### SLOT-10 路由注册位置
- 本项目取值：`lib/route/routes.dart`（`RoutePath` 常量）+ `lib/route/app_pages.dart`（`GetPage` 注册）。
- 代码证据：上述文件。
- 生效范围：全量。

### SLOT-11 repository 实现目录
- 本项目取值：`lib/data/repository/`（**不要** `repositories/`），类名 `<Name>RepositoryImpl`。
- 代码证据：`lib/data/repository/` 8 个 impl；违例 `lib/data/repositories/goal_repository_impl.dart` 见 SLOT-15。
- 生效范围：新代码（存量违例逐步迁移）。

### SLOT-12 禁止新建的老目录
- 本项目取值：`lib/ui/pages/`（旧谱系页面目录，禁止新建页面）；`lib/data/repositories/`（错误目录，禁止新增）。
- 代码证据：见 SLOT-02 / SLOT-11。
- 生效范围：新代码。

### SLOT-13 网络 API 类
- 本项目取值：`AppApiMethods`（主，`lib/network/app_api.dart:63`）+ `ServerTimeApiMethods`（行 341）；`@RestApi`（retrofit）。
- 代码证据：`lib/network/app_api.dart`。
- 生效范围：全量。

### SLOT-14 测试约定
- 本项目取值：待定（决策人：客户端负责人；期限：阶段 2 测试三件套落地前）。
- 生效范围：—

### SLOT-15 存量违例清单（tech-debt 登记）
- 本项目取值：
  1. `lib/data/repository/health_repository_impl.dart` —— 直连 `AppApiMethods` 绕过 datasource；且依赖 `IGoalManagementUseCase` 等 usecase（**data 反向依赖 usecase，分层律硬违例**）。
  2. `lib/data/repository/user_repository_impl.dart` —— 直连 `AppApiMethods` 绕过 datasource。
  3. `lib/data/repositories/goal_repository_impl.dart` —— 目录错位（应在 `repository/`）。
  4. `lib/domain/usecase/food_record_management_usecase.dart` —— 接口（行 126）与实现（行 597）混在同一文件。
  5. service 同文件存量：`file_upload_service.dart`、`network_connectivity_service.dart` 等 3 个（5/8 已分文件）。
  6. `GetxController` 直接使用 12 处（应为 `LifecycleController`）。
  7. binding 形态不统一（`Get.put` 20 处 vs canonical `Get.lazyPut` 7 处，含 `permanent: true` 滥用）。
- 生效范围：全量。**清单外的同类问题一律按"新增违例"阻塞。**
- 备注：`GoalManagementUseCase → FoodRecordManagementUseCase` 单向依赖在 golden-path v2 下已**合法**（允许单向、禁止环），不再列为违例。

## 2. 校验自检

- [x] C1 元信息齐全
- [x] C2 15 个槽位填写完毕，待定 1 项（SLOT-14，≤2 合规）
- [x] C3 已填槽位均有代码证据
- [x] C4 取值与通用硬规则无冲突
- [x] C5 存量违例清单已登记（7 条）

## 附：golden-path §13 关账记录（v1 → v2）

| § | 项 | 关账结论 |
|---|---|---------|
| 13.1 | LifecycleController 路径 | `package:gurusdk/guru_utils/lifecycle.dart`（calorie 实测；seek 经 `controller.dart`，均出自 gurusdk）✅ |
| 13.2 | design_generator 形态 | `@DesignSpec` + Spec 系列注解 + `.get()`（双 App 一致）✅ |
| 13.3 | l10n 引用入口 | **项目差异**：calorie=AppStrings 封装（99%）、seek=裸 `S` → 槽位化（SLOT-07）✅ |
| 13.4 | database_manager | 行号/写法实测如上（SLOT-06）✅ |
| 13.5 | @RestApi 约定 | AppApiMethods 双 App 一致，seek 多 ChatApiMethods ✅ |
| 13.6 | service 同/分文件比例 | calorie 5/8 分文件、usecase 5/6 分文件；混合文件入 SLOT-15 存量清单 ✅ |
| 13.7 | usecase 依赖 usecase | 放宽为"允许单向、禁止环与双向"（golden-path v2 §2.1）✅ |
