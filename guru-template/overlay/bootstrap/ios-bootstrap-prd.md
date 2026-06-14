# Bootstrap Task: Fill Project Development Guidelines (iOS / guru)

**You (the AI) are running this task. The developer does not read this file.**

The developer just ran `trellis init -t guru-ios-native` + the guru overlay
on this project for the first time. `.trellis/` now exists with the guru spec:
`harness/` (五阶段方法学 SSOT), `conventions/` (项目约定槽位), `guides/golden-path.md`
(通用方法), and **empty by-layer scaffolding** `ios/ shared/`.

**Your job**: populate the project's *real* coding conventions into two places —
1. the **by-layer spec** (`.trellis/spec/ios|shared/*.md`) — open-ended
   pattern docs so every future `trellis-implement` / `trellis-check` sub-agent
   matches THIS project's actual style; and
2. the **conventions slots** (`.trellis/spec/conventions/project-conventions.md`) —
   the pinned SLOT decisions that the 五阶段 writing/review Gate hard-requires (C1~C6).

Empty spec = sub-agents write generic code. Real spec = sub-agents match the team's
actual patterns. **Do NOT fill `harness/` or `guides/golden-path.md`** — those are the
guru methodology (maintained by the config pack); you only *follow* them when filling
the by-layer files (respect the 分层依赖律 and the doc_type 七类).

Don't dump instructions. Open with a short greeting, figure out if the repo has any
existing convention docs (CLAUDE.md, .cursorrules, etc.), and drive the rest
conversationally.

---

## Status (update the checkboxes as you complete each item)

- [ ] Imported any existing convention docs (CLAUDE.md / .cursorrules / CONTRIBUTING.md)
- [ ] Filled `.trellis/spec/ios/` (UI + App + Domain + Infrastructure 四层) with real patterns + code examples
- [ ] Filled `.trellis/spec/shared/` (跨层规范) with real patterns + code examples
- [ ] Filled `.trellis/spec/conventions/project-conventions.md` slots (C1~C6 pass)
- [ ] Verified every code example references a REAL file path in this repo

---

## Spec files to populate

### `ios/` — UI / App / Domain / Infrastructure 四层

| File | What to document |
|------|------------------|
| `.trellis/spec/ios/directory-structure.md` | `UI/Features/<Feature>/{Views,ViewModels}` + DDD 四层（Domain / App / Infrastructure / UI）目录的真实组织 |
| `.trellis/spec/ios/viewmodel.md` | `viewmodel`：`ObservableObject` + `@Published`、loading/empty/error 三态、生命周期与流订阅收口的真实写法 |
| `.trellis/spec/ios/usecase.md` | `usecase`：Domain 业务编排、零 UI 依赖、注入接口的真实写法与依赖边界 |
| `.trellis/spec/ios/repository.md` | `repository`：接口在 Domain（`IXxxRepository`）/ 实现在 Infrastructure、经 `DatabaseManager` 的边界 |
| `.trellis/spec/ios/view-guidelines.md` | SwiftUI `view`：主题修饰器消费、禁裸色值/尺寸字面量、输入转发到 ViewModel 的真实写法 |
| `.trellis/spec/ios/coordinator-navigation.md` | `AppCoordinator` 导航约定（`NavigationDestination` enum + `navigateToXxx` + 闭包注入） |
| `.trellis/spec/ios/di-factorykit.md` | FactoryKit `@Injected` 注册规范（`Container+*.swift` 按层拆分、`@MainActor` Factory、消费形态） |
| `.trellis/spec/ios/error-handling.md` | `enum XxxError: Error` 分层定义、底层异常→领域错误的转换点（repository/external 边界） |
| `.trellis/spec/ios/quality.md` | SwiftLint / `xcodebuild build` / `xcodebuild test` 命令与门禁 |

### `shared/` — Cross-layer

| File | What to document |
|------|------------------|
| `.trellis/spec/shared/swift-conventions.md` | Swift 语言级约定（`private extension` 组织、`MARK` 分组、访问级别） |
| `.trellis/spec/shared/naming-conventions.md` | 文件/类/协议/变量命名规律（`IXxx` 接口前缀、`XxxView`/`XxxViewModel`/`<Domain>Error` 后缀） |
| `.trellis/spec/shared/git-conventions.md` | 分支/提交/PR 约定 |

### `conventions/project-conventions.md` — pinned SLOT decisions (Gate 硬前置)

从 `conventions/project-conventions.template.md` 复制为 `project-conventions.md`，逐 SLOT 填本项目取值；
参考同目录的样例（`story-verse.project-conventions.md`）的填法与「实测扫描」元信息格式。必须过 C1~C6 校验
（元信息 / 全槽位取值 SLOT-01~SLOT-16 / 每槽代码证据 / doc_type 纯净 / 不与硬规则冲突 / 存量违例清单）。

---

## How to fill the spec

### Step 1: Import from existing convention files first (preferred)

Search the repo for existing convention docs. If any exist, read them and extract the
relevant rules into the matching `.trellis/spec/` files — usually much faster than
documenting from scratch.

| File / Directory | Tool |
|------|------|
| `CLAUDE.md` / `CLAUDE.local.md` | Claude Code |
| `AGENTS.md` | Codex / Claude Code / agent-compatible tools |
| `.cursorrules` / `.cursor/rules/*.mdc` | Cursor |
| `.windsurfrules` / `.clinerules` / `.roomodes` | Windsurf / Cline / Roo |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `CONTRIBUTING.md` / `CONVENTIONS.md` | General project conventions |
| `.swiftlint.yml` / `.swiftformat` / `.editorconfig` | Formatting / lint rules |
| `docs/PROJECT_STRUCTURE.md` / `docs/Swift_代码组织规范.md` | 既有架构与代码组织文档（若有，优先导入） |

### Step 2: Analyze the codebase (iOS scan points)

Scan real code to discover patterns. Before writing each spec file, find 2-3 real
examples and reference **real file paths**. iOS 扫描点：
- `Podfile` / `Package.swift` — 依赖与栈基线（RxSwift 遗留 / Moya / Firebase / FactoryKit / WCDBSwift…），定 SLOT-01/08。
- DDD 四层目录树 — `Domain/` → `App/` → `Infrastructure/` → `UI/` 单向依赖与归属分界（SLOT-02），确认 Domain 零依赖（`grep import` 只见 `Foundation`）。
- `@Injected` / `@InjectedObject` + `Container+*.swift`（`App/DependencyInjection/`）— FactoryKit 注册形态（SLOT-05）。
- `enum XxxError: Error`（`Domain/Errors/` 等）— 错误分层与收口转换点（SLOT-04）。
- `import WCDBSwift` / `DatabaseManager` / `EnhancedDatabaseManager`（`Infrastructure/Persistence/`）— 持久化与建表迁移（SLOT-06）。
- `class XxxViewModel: ObservableObject` + `@Published` — ViewModel 形态与三态（SLOT-01/13）。
- `ThemeManager`（单例）+ `view` 修饰器 — 主题 token 消费、禁裸色值/尺寸（SLOT-11）。
- `R.swift` / `Localizable.strings`（`.lproj`）+ `R.string.localizable` — i18n 引用入口与同步约定（SLOT-12）。
- `AppCoordinator` + `NavigationDestination`（`App/Coordinators/`）— 导航约定（SLOT-07）。
- `XCTest` / `Quick`+`Nimble` 镜像测试目录 + mock（手写 / Mockolo）— 测试（SLOT-14）。
- 既有架构违例（`grep` 反向 import / view 间直接导航 / view 直连持久化）→ `conventions` SLOT-16 存量清单。

填 by-layer 时遵循 `.trellis/spec/guides/golden-path.md` 的分层依赖律（Domain→App→Infrastructure→UI 单向）
与 `.trellis/spec/harness/` 的 doc_type 七类口径（`viewmodel` / `usecase` / `repository` / `domain-model` /
`view` / `coordinator` / `external` 的归属），不复写它们的正文，只引用。

### Step 3: Document reality, not ideals

**Critical**: write what the code *actually does*, not what it should do. Sub-agents
match the spec, so aspirational patterns that don't exist in the codebase will cause
sub-agents to write code that looks out of place. If the team has known tech debt
(RxSwift 遗留 / `XxxProtocol` 后缀遗留 / `Impl` 后缀遗留 / view 间硬导航存量等),
document the current state in the relevant `ios/*.md` and pin it in SLOT-16 — improvement
is a separate conversation, not a bootstrap concern.

---

## Quick explainer of the runtime (share when they ask "why do we need spec at all")

- Every guru task spawns `trellis-implement` (writes code) + `trellis-check` (verifies).
- Each task's `implement.jsonl` / `check.jsonl` list which spec files to load; the guru
  `guru_after_create` hook seeds the baseline (golden-path + harness index + conventions
  + the relevant by-layer `index.md`), and Research/add-context picks the precise topics.
- The platform hook auto-injects those spec files + the task's `prd.md` into every
  sub-agent prompt — so sub-agents code/review per team conventions automatically.
- Source of truth: `.trellis/spec/`. Filling it well now pays off forever.

---

## Completion

When the developer confirms the checklist items above are done with real examples
(not placeholders), guide them to run:

```bash
python3 ./.trellis/scripts/task.py finish
python3 ./.trellis/scripts/task.py archive 00-bootstrap-guidelines
```

After archive, every new developer who joins this project gets a `00-join-<slug>`
onboarding task instead of this bootstrap task.

---

## Suggested opening line

"Welcome to guru/Trellis! Your init set me up to fill this project's spec — a one-time
setup so every future AI session matches your team's actual iOS patterns instead of
writing generic code. I'll fill `ios/`, `shared/` and the `project-conventions.md` slots.
Do you have existing convention docs (CLAUDE.md, .cursorrules, CONTRIBUTING.md, or a
`docs/PROJECT_STRUCTURE.md`) I can pull from, or should I scan the codebase from scratch?"
