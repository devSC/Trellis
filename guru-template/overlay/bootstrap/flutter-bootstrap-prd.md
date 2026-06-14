# Bootstrap Task: Fill Project Development Guidelines (Flutter / guru)

**You (the AI) are running this task. The developer does not read this file.**

The developer just ran `trellis init -t guru-flutter-client` + the guru overlay
on this project for the first time. `.trellis/` now exists with the guru spec:
`harness/` (五阶段方法学 SSOT), `conventions/` (项目约定槽位), `guides/golden-path.md`
(通用方法), and **empty by-layer scaffolding** `flutter/ service/ shared/`.

**Your job**: populate the project's *real* coding conventions into two places —
1. the **by-layer spec** (`.trellis/spec/flutter|service|shared/*.md`) — open-ended
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
- [ ] Filled `.trellis/spec/flutter/` (UI / 表现层) with real patterns + code examples
- [ ] Filled `.trellis/spec/service/` (domain + data 层) with real patterns + code examples
- [ ] Filled `.trellis/spec/shared/` (跨层规范) with real patterns + code examples
- [ ] Filled `.trellis/spec/conventions/project-conventions.md` slots (C1~C6 pass)
- [ ] Verified every code example references a REAL file path in this repo

---

## Spec files to populate

### `flutter/` — UI / Presentation layer

| File | What to document |
|------|------------------|
| `.trellis/spec/flutter/directory-structure.md` | `lib/` 下页面/widget/路由/注入的真实组织 |
| `.trellis/spec/flutter/widget-guidelines.md` | const 构造、widget 拆分、build 边界的真实写法 |
| `.trellis/spec/flutter/state-management.md` | 实际状态方案（GetX/Provider/Bloc…）、controller 生命周期 |
| `.trellis/spec/flutter/navigation.md` | 路由注册位置（`routes.dart`/`app_pages.dart`）、跳转约定 |
| `.trellis/spec/flutter/type-safety.md` | 序列化（`@freezed`/`@JsonSerializable`）、空安全约定 |
| `.trellis/spec/flutter/pitfalls.md` | 本项目踩过的 UI 层坑（setState-after-dispose 等） |
| `.trellis/spec/flutter/quality.md` | analyze/format/lint 命令与门禁 |

### `service/` — Domain + Data layer

| File | What to document |
|------|------------------|
| `.trellis/spec/service/usecase-pattern.md` | usecase 编排的真实写法、依赖边界 |
| `.trellis/spec/service/repository-pattern.md` | repository 接口/实现、datasource 边界（`lib/new/data/...`） |
| `.trellis/spec/service/api-patterns.md` | 网络层（`@RestApi`/Dio 构建位置）、契约组织 |
| `.trellis/spec/service/error-handling.md` | 错误收口位置（集中 normalizer vs 分散 try-catch） |
| `.trellis/spec/service/dependency-injection.md` | DI 入口（`lib/app/injector/injector.dart`）、注册约定 |
| `.trellis/spec/service/local-storage.md` | 本地库（`lib/new/data/database/`）版本字段与迁移 |
| `.trellis/spec/service/logging.md` | logger 注入路径、结构化字段 |

### `shared/` — Cross-layer

| File | What to document |
|------|------------------|
| `.trellis/spec/shared/code-quality.md` | 强制代码质量规则（空断言/dynamic 禁用等），配 WRONG/CORRECT |
| `.trellis/spec/shared/dart-conventions.md` | Dart 语言级约定 |
| `.trellis/spec/shared/naming-conventions.md` | 文件/类/变量命名规律 |
| `.trellis/spec/shared/git-conventions.md` | 分支/提交/PR 约定 |

### `conventions/project-conventions.md` — pinned SLOT decisions (Gate 硬前置)

从 `conventions/project-conventions.template.md` 复制为 `project-conventions.md`，逐 SLOT 填本项目取值；
参考同目录的样例（如 `seek.project-conventions.md`）的填法与「实测扫描」元信息格式。必须过 C1~C6 校验
（元信息 / 全槽位取值 / 每槽代码证据 / doc_type 纯净 / 不与硬规则冲突 / 存量违例清单）。

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
| `.editorconfig` / `analysis_options.yaml` | Formatting / lint rules |

### Step 2: Analyze the codebase (Flutter scan points)

Scan real code to discover patterns. Before writing each spec file, find 2-3 real
examples and reference **real file paths**. Flutter 扫描点：
- `pubspec.yaml` — 依赖与代码生成（freezed/json_serializable/retrofit/get_it…）。
- `lib/` 目录树 — 新旧代码分界（如 `lib/new/` vs `lib/`）、页面/widget/路由组织。
- `grep '@freezed' / '@JsonSerializable'` — 序列化方案（SLOT-01）。
- `lib/app/injector/injector.dart` — DI 入口（SLOT-09）。
- `lib/route/routes.dart` + `app_pages.dart` — 路由（SLOT-10）。
- `lib/new/data/repositories/impl/` / `lib/new/data/database/` — repository + 本地库。
- `@RestApi` 类 + Dio 构建位置 — 网络层（SLOT-13）。
- `test/` 镜像结构 + `@GenerateMocks` — 测试（SLOT-14）。
- 既有架构违例（`grep` 反向依赖 / 禁区目录）→ `conventions` SLOT-15 存量清单。

填 by-layer 时遵循 `guides/golden-path.md` 的分层依赖律与 `harness/` 的 doc_type 七类口径
（controller/usecase/repository-datasource/… 的归属），不复写它们的正文，只引用。

### Step 3: Document reality, not ideals

**Critical**: write what the code *actually does*, not what it should do. Sub-agents
match the spec, so aspirational patterns that don't exist in the codebase will cause
sub-agents to write code that looks out of place. If the team has known tech debt,
document the current state in `pitfalls.md` / SLOT-15 — improvement is a separate
conversation, not a bootstrap concern.

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
setup so every future AI session matches your team's actual Flutter patterns instead of
writing generic code. I'll fill `flutter/`, `service/`, `shared/` and the
`project-conventions.md` slots. Do you have existing convention docs (CLAUDE.md,
.cursorrules, CONTRIBUTING.md) I can pull from, or should I scan the codebase from
scratch?"
