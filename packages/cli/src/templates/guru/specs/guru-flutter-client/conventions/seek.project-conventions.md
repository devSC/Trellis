# Project Conventions — ai_seek

> 按 [project-conventions.template.md](./project-conventions.template.md) 填写。安装配置包时将本文件迁入 seek 仓库 `.trellis/spec/conventions/project-conventions.md`。
> 取值依据：2026-06-11 对 `guru_ai_seek_270` 的实测扫描（详见 client-harness-design.md §6）。

## 0. 元信息

| 字段 | 取值 |
|------|------|
| App 名称 / Dart 包名 | AI Seek / `ai_seek` |
| 仓库路径 | `guru_ai_seek_270`（Flutter 3.32.8，gurusdk v4.0.4） |
| 填写日期 / 填写人 | 2026-06-12 / client_agent 配置包（实测扫描） |
| 取值依据 | 实测扫描；待团队 redline 确认 |

## 1. 槽位清单

### SLOT-01 序列化方案
- 本项目取值：新代码一律 `@freezed`（自动含 json_serializable 能力，`field_rename: snake_case`、`explicit_to_json: true`）；旧代码 `@JsonSerializable` 残留不强迁。
- 代码证据：`lib/new/domain/entities/session.dart`（@freezed）；`build.yaml`（json_serializable options）；旧例 `lib/domain/models/ai_model.dart`。
- 生效范围：新代码。

### SLOT-02 新代码目录分界
- 本项目取值：分界在**业务层**——新增 domain/data 代码进 `lib/new/domain/`、`lib/new/data/`（Clean Architecture 谱系）；presentation 无新旧分界，页面统一进 `lib/ui/pages/<feature>/`（controller/binding/page/design_model 同目录）。
- 代码证据：`lib/new/domain/usecases/chat_usecase.dart`；`lib/ui/pages/home/`。
- 生效范围：新代码。

### SLOT-03 接口文件命名
- 本项目取值：`xxx.dart`（接口，无 `I` 前缀类名）+ `xxx_impl.dart`（实现），impl 可置于 `impl/` 子目录。旧层 `I` 前缀（如 `IModelService`）为存量，不新增。
- 代码证据：`lib/new/domain/usecases/chat_usecase.dart` + `chat_usecase_impl.dart`；`lib/new/data/database/dao/` + `dao/impl/`。
- 生效范围：新代码。

### SLOT-04 错误收口位置
- 本项目取值：集中 normalizer——`DioException` 等由 `ClientErrorNormalizer.tryNormalize()` 统一转换为 `NormalizedClientError`，由 UseCase/Controller 层调用收口；repository/datasource 不吞异常、原样上抛。
- 代码证据：`lib/utils/client_error_normalizer.dart`。
- 生效范围：全量。

### SLOT-05 design model 形态
- 本项目取值：**无全局 AppDesignModel**；每页一份 `<Xxx>PageDesignModel`（`@DesignSpec(width, height)` 抽象类 + `@SpecFontSize/@SpecEdgeInsets/@SpecWidth` 字段 + 静态 `get()`）。
- 代码证据：`lib/ui/pages/home/home_page_design_model.dart`。
- 生效范围：新代码（存量 ~35% 硬编码尺寸属 tech-debt，见 SLOT-15）。

### SLOT-06 数据库 helper
- 本项目取值：`DatabaseHelperImpl`（接口 `DatabaseHelper`），版本字段 `_databaseVersion`（当前 4），DB 名 `ai_chat_client.db`；`_onUpgrade` 按 `oldVersion < N && newVersion >= N` 分支 ALTER；事务经 `executeInTransaction`。
- 代码证据：`lib/new/data/database/impl/database_helper_impl.dart`；`lib/new/data/database/database_helper.dart`。
- 生效范围：全量。

### SLOT-07 l10n
- 本项目取值：ARB 源 `lib/l10n/intl_en.arb`（81 语言，`intl_` 前缀）；引用生成的 `S` 类（`lib/generated/l10n.dart`，flutter_intl/intl_utils 风格）；同步脚本 **`seek_l10_sync.sh`**（写共享 Sheet `1Q-ThsmOPzWxjC5lJUis3wMrdCclGm_G79tXP92CTiGg` 的 `Main` 表，**agent 禁止自动执行**）。
- 代码证据：`seek_l10_sync.sh`；`lib/generated/l10n.dart`。
- 生效范围：全量。

### SLOT-08 代码生成脚本与顺序
- 本项目取值：`gurusdk_get.sh`（仅 gurusdk/依赖变动）→ `code_prebuild.sh`（`dart run build_runner build --delete-conflicting-outputs`：injectable/retrofit/freezed/json_serializable）→ intl 生成（仅动 ARB 时）。
- 代码证据：`code_prebuild.sh`；`gurusdk_get.sh`；`build.yaml`。
- 生效范围：全量。

### SLOT-09 DI 入口
- 本项目取值：`Injector.provide<T>()`，定义于 `lib/app/injector/injector.dart`；生成文件 `lib/app/injector/injector.config.dart`。
- 代码证据：`lib/app/injector/injector.dart`。
- 生效范围：全量。

### SLOT-10 路由注册位置
- 本项目取值：`lib/route/routes.dart`（`RoutePath` 常量）+ `lib/route/app_pages.dart`（`GetPage` 注册）；导航经 `route_center.dart` / `session_navigator.dart`。
- 代码证据：`lib/route/routes.dart`；`lib/route/app_pages.dart`。
- 生效范围：全量。

### SLOT-11 repository 实现目录
- 本项目取值：新代码 `lib/new/data/repositories/impl/`，类名 `<Name>RepositoryImpl`；mapper 置 `repositories/mappers/`。旧层 `lib/infrastructure/repositories/` 为存量。
- 代码证据：`lib/new/data/repositories/impl/chat_repository_impl.dart`。
- 生效范围：新代码。

### SLOT-12 禁止新建的老目录
- 本项目取值：新业务逻辑禁止进 `lib/domain/`、`lib/infrastructure/`、`lib/application/`（旧谱系，应进 `lib/new/`）；`lib/services/` 仅限既有跨切面 manager 维护，新业务流程不得在此直连 API。
- 代码证据：违例样本见 SLOT-15。
- 生效范围：新代码。

### SLOT-13 网络 API 类
- 本项目取值：`AppApiMethods` + `ChatApiMethods`（`@RestApi`，retrofit）；Dio 经 `AppDioBuilder`（guru_ai_ui）构建；版本号经 `@Path("version")` 动态传递。
- 代码证据：`lib/network/app_api.dart`；`lib/network/chat_api.dart`。
- 生效范围：全量。

### SLOT-14 测试约定
- 本项目取值：mockito（`@GenerateMocks` + build_runner 生成 `.mocks.dart`）；`test/` 镜像 `lib/` 结构（含 `test/new/...`）；widget 测试启用；golden test 未启用。
- 代码证据：`test/new/domain/usecases/`；6 个 `.mocks.dart`。
- 生效范围：全量。

### SLOT-15 存量违例清单（tech-debt 登记）
- 本项目取值：
  1. `lib/services/annual_summary/annual_summary_api_service.dart` —— services 层直连 `AppApi`（绕过 repository）。
  2. `lib/ui/pages/chat/chat_controller.dart` —— controller 直接 import `ChatApi`（跳过 usecase）。
  3. `lib/infrastructure/repositories/model_repository_impl.dart` —— repository 直连 `_appApi`（绕过 datasource）。
  4. `lib/domain/services/model_service.dart` —— 接口与实现混在同一文件。
  5. 页面存量硬编码尺寸（约 35%，如 `lib/ui/pages/history/history_page.dart` 的 `height: 44`）。
  6. binding 形态不统一（约 60% `Get.put` 手动构造 / `permanent` 滥用，目标 canonical 见 golden-path §2.3）。
- 生效范围：全量。**清单外的同类问题一律按"新增违例"阻塞。**

## 2. 校验自检

- [x] C1 元信息齐全
- [x] C2 15 个槽位全部填写，待定 0 项
- [x] C3 每槽位均有代码证据
- [x] C4 取值与通用硬规则无冲突（freezed 为合法项目选择；分层律/接口分离/datasource 必经/异常不吞均未被豁免）
- [x] C5 存量违例清单已登记（6 条）
