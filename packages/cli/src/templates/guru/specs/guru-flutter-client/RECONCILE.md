# Reconcile 记录：flutter-trellis-spec-template（0.3.10 旧模板）vs golden-path v2

> 结论日期：2026-06-12 · 对照源：`flutter-trellis-spec-template/.trellis/spec/` 六域 vs `guides/golden-path.md`
> 原则：**规则正文以 golden-path 为唯一真源**；旧模板冲突条目废弃、重叠条目降级、独有价值按需迁入。
> v0.1 模板刻意只收录 golden-path 体系 + 本记录；独有价值文件待试点后按需迁入（"从真实案例长出来"原则）。

## 一、冲突（旧模板条目废弃，以 golden-path 为准）

| 旧模板文件 | 冲突点 | golden-path 条款 |
|-----------|--------|------------------|
| `service/dependency-injection.md` | 推荐 get_it/injectable 为主、GetX Binding 可选；`@singleton` 无限制 | §2.3：唯一 canonical = `@injectable` + `Get.lazyPut(() => Injector.provide<C>(), tag)`；`@Singleton` 仅限无状态且注释理由 |
| `service/usecase-pattern.md` | UseCase 用 `@injectable`（每次新建） | §3：`@LazySingleton(as: <接口>)` |
| `service/error-handling.md` | 固定 repository 层 catch 转 Failure | §5：datasource/api 不吞异常（硬规则）；转换位置按 `[SLOT-04]` 槽位 |
| `service/api-patterns.md` | 手动异常处理示例含吞错 | §5：必须上抛 |
| `flutter/directory-structure.md` | 固定目录与 l10n 位置 | §2.4/§7：目录与 l10n 按 `[SLOT-02]/[SLOT-07]` 槽位 |

## 二、重叠（不矛盾；旧文件如保留须标注"规则正文以 golden-path 为准"）

`service/repository-pattern.md`（§4）· `service/directory-structure.md`（§2.1）· `flutter/state-management.md`（§2.5）· `flutter/navigation.md`（§6+SLOT-10）· `flutter/widget-guidelines.md`（§6）· `shared/naming-conventions.md`（§2.4）· `service/networking.md`（§5）· `service/local-storage.md`（§4）

## 三、独有价值（golden-path 未覆盖；试点后按需迁入本 spec）

- **必读级**：`big-question/` 七个生产坑（BuildContext/setState-after-dispose/GetX 生命周期/JSON 坑/平台通道/流泄漏/图片内存）· `testing/mock-strategy.md`（Tier1-3 渐进 mock）· `guides/pre-implementation-checklist.md`
- **推荐级**：`flutter/theme-i18n.md` · `service/logging.md` · `guides/bug-root-cause / code-reuse / cross-layer` 思维指南 · `shared/code-quality.md`
- **参考级**：`flutter/type-safety.md` · `flutter/pitfalls.md` · `shared/git-conventions.md`

## 处置状态

- [x] golden-path v2 冻结为唯一真源（本 spec `guides/golden-path.md`）
- [x] 冲突清单成文（上表一）
- [ ] 旧模板仓库 README 标注"已被 guru-template 取代，规则正文以 golden-path 为准"（Phase 2 执行）
- [ ] 独有价值必读级三件迁入本 spec（试点后，Phase 2/4）
