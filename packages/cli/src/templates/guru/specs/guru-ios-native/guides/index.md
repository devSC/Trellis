# guides/ 索引

> guru-ios-native spec 库的通用方法入口。本文件只做导航，不承载规则正文。
> 平台基线：DDD 四层（Domain → App → Infrastructure → UI，Domain 零依赖）+ SwiftUI 主（RxSwift 遗留）+ FactoryKit DI（`@Injected`）+ Repository 模式 + WCDBSwift 持久化。

| 文件 | 职责 |
|------|------|
| [golden-path.md](./golden-path.md) | 通用方法 SSOT：分层依赖律、各层迷你路径（domain-model / repository / usecase / viewmodel / view / coordinator / external）、入口决策树、禁止清单、门禁映射 |

- **doc_type 七类是权威分层口径**：`viewmodel` / `usecase` / `repository` / `domain-model` / `view` / `coordinator` / `external`。全程唯一，禁止改名、增减或换数；下游引用一律用裸 token，不得自创 `service` / `transport-handler` 之类（详见 golden-path.md）。
- **项目级取值不在本目录**：UI 框架、网络层、日志、JSON 修复策略、测试框架、i18n、主题、feature 模块结构、mock 生成、构建自动化等槽位取值一律走 [`../conventions/project-conventions.md`](../conventions/project-conventions.md)（入口见 [`../conventions/index.md`](../conventions/index.md)）。
- **五阶段流程规则不在本目录**：需求五要素、概要归属表、详细合同八问、实现 trace 计划合同与 mutable evidence 及各 Gate 判定见 [`../harness/index.md`](../harness/index.md)。

安装后这些文件落在目标仓库的 `.trellis/spec/` 下：方法 SSOT 见 [`.trellis/spec/guides/golden-path.md`](.trellis/spec/guides/golden-path.md)，流程与模板见 `.trellis/spec/harness/*`，项目槽位见 `.trellis/spec/conventions/project-conventions.md`。
