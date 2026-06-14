# Bootstrap Task: Fill Project Development Guidelines (Go / guru)

**You (the AI) are running this task. The developer does not read this file.**

The developer just ran `trellis init -t guru-go-backend` + the guru overlay
on this project for the first time. `.trellis/` now exists with the guru spec:
`harness/` (五阶段方法学 SSOT), `conventions/` (项目约定槽位), `guides/golden-path.md`
(通用方法), and **empty by-layer scaffolding** `backend/ shared/`.

**Your job**: populate the project's *real* coding conventions into two places —
1. the **by-layer spec** (`.trellis/spec/backend|shared/*.md`) — open-ended
   pattern docs so every future `trellis-implement` / `trellis-check` sub-agent
   matches THIS project's actual style; and
2. the **conventions slots** (`.trellis/spec/conventions/project-conventions.md`) —
   the pinned SLOT decisions that the 五阶段 writing/review Gate hard-requires (C1~C6).

Empty spec = sub-agents write generic code. Real spec = sub-agents match the team's
actual patterns. **Do NOT fill `harness/` or `guides/golden-path.md`** — those are the
guru methodology (maintained by the config pack); you only *follow* them when filling
the by-layer files (respect the 分层依赖律 and the doc_type 七类).

Don't dump instructions. Open with a short greeting, figure out if the repo has any
existing convention docs (CLAUDE.md, AGENTS.md, etc.), and drive the rest
conversationally.

---

## Status (update the checkboxes as you complete each item)

- [ ] Imported any existing convention docs (CLAUDE.md / AGENTS.md / CONTRIBUTING.md)
- [ ] Filled `.trellis/spec/backend/` (transport + service + repository + domain 层) with real patterns + code examples
- [ ] Filled `.trellis/spec/shared/` (跨层规范) with real patterns + code examples
- [ ] Filled `.trellis/spec/conventions/project-conventions.md` slots (C1~C6 pass)
- [ ] Verified every code example references a REAL file path in this repo

---

## Spec files to populate

### `backend/` — transport / service / repository / domain layers

| File | What to document |
|------|------------------|
| `.trellis/spec/backend/directory-structure.md` | `services/*/internal/{app,config,transport,service,repository,domain,auth}` 分层目录的真实组织 + `cmd/<svc>/main.go` 入口 + `packages/contracts/` |
| `.trellis/spec/backend/api-design.md` | entry-api：`net/http` `ServeMux` 路由注册、JSON 编解码（`decodeJSON`/`writeJSON`）、错误→状态码映射的真实写法 |
| `.trellis/spec/backend/service-patterns.md` | biz：service 编排/入参校验、构造注入边界、service→service 单向依赖、最小接口收窄 |
| `.trellis/spec/backend/repository-data.md` | repository 数据访问（`*sql.DB` + `QueryContext`/`ExecContext`、行扫描、参数化查询）+ `db/migrations` 迁移成对组织 |
| `.trellis/spec/backend/domain-model.md` | domain 实体/入参 Params 结构/JSON tag、sentinel error 的归属（domain vs service vs repository） |
| `.trellis/spec/backend/config-runtime.md` | `config.Load()`/env 前缀（如 `CONTROL_API_*`）/`app.New/Run/Shutdown` 启动关闭序列与超时 |
| `.trellis/spec/backend/error-handling.md` | `sql.ErrNoRows`→sentinel 翻译、`%w` 包装风格（裸 sentinel vs 包装）、`errors.Is`/`errors.As` 判定 |
| `.trellis/spec/backend/logging.md` | logger 注入路径、结构化字段约定、请求链路 ID 传递 |
| `.trellis/spec/backend/quality.md` | `go build` / `go vet` / `go test` / `golangci-lint` / `gofmt` 命令与门禁 |

### `shared/` — Cross-layer

| File | What to document |
|------|------------------|
| `.trellis/spec/shared/go-conventions.md` | Go 语言级约定、包可见性（`internal/` 隐私、`packages/contracts/` 边界）、accept interfaces/return structs |
| `.trellis/spec/shared/naming-conventions.md` | 文件/类型/构造函数/变量命名规律（`<Entity>Repository`/`New<Entity>Service`/`handle<Resource>`） |
| `.trellis/spec/shared/git-conventions.md` | 分支/提交/PR 约定 |

### `conventions/project-conventions.md` — pinned SLOT decisions (Gate 硬前置)

从 `conventions/project-conventions.template.md` 复制为 `project-conventions.md`，逐 SLOT 填本项目取值；
参考同目录的样例（如 `safa-land.project-conventions.md`）的填法与「实测扫描」元信息格式。必须过 C1~C6 校验
（元信息 / 全槽位取值 SLOT-01~17 / 每槽代码证据 / 取值不与硬规则冲突 / SLOT-17 存量违例清单 / 多服务取值粒度标注）。

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
| `.golangci.yml` / `.golangci-lint.yml` / `Makefile` | Lint / build / format rules |

### Step 2: Analyze the codebase (Go scan points)

Scan real code to discover patterns. Before writing each spec file, find 2-3 real
examples and reference **real file paths**. Go 扫描点：
- `go.mod` — module path、依赖与是否引入 DI 框架（`google/wire`）/ ORM（`ent`/`sqlc`）/ 日志/测试库（SLOT-01/02/03/04）。
- `services/*/internal/{transport,service,repository,domain}` 目录树 — 分层包划分、按领域 vs 按角色聚合、文件命名（SLOT-11）。
- `internal/config/config.go` — `config.Load()`、env 前缀（`CONTROL_API_*`）、默认值与必填校验（SLOT-08）。
- `service/errors.go` + `repository/errors.go` — sentinel error 声明位置与归属（`ErrValidation`/`ErrNotFound`，SLOT-13）。
- `db/migrations/` — 迁移工具、`NNNN_*.up.sql`/`.down.sql` 成对命名与版本号规则（SLOT-12）。
- `Makefile` / `.golangci.yml` — `go build`/`go vet`/`go test`/`golangci-lint`/`gofmt` 目标名与启用的 linters（SLOT-07）。
- `packages/contracts/` — 跨服务契约结构体（`Desired*`、JSON 字段冻结）、是否只放纯数据（SLOT-11）。
- `internal/app/app.go` + `cmd/<svc>/main.go` — DI 装配位置、`app.New/Run/Shutdown` 生命周期、连接池参数（SLOT-01/14）。
- `internal/transport/http/router.go` — 路由注册、`ServeMux` 模式、错误→状态码映射、`requireAdmin` 鉴权（SLOT-05/10）。
- `internal/auth/` — HMAC-SHA256 签名 cookie + bcrypt 自实现（SLOT-10）。
- 既有架构违例（`grep` 反向依赖 / handler 直连 DB / `service` import `net/http` / `os.Getenv` 散读）→ `conventions` SLOT-17 存量清单。

填 by-layer 时遵循 `guides/golden-path.md` 的分层依赖律（`transport → service → repository → domain` 严格单向无环）与 `harness/` 的 doc_type 七类口径（`entry-api`/`biz`/`repository-data`/`domain`/`config`/`external`/`runtime` 的归属），不复写它们的正文，只引用。

### Step 3: Document reality, not ideals

**Critical**: write what the code *actually does*, not what it should do. Sub-agents
match the spec, so aspirational patterns that don't exist in the codebase will cause
sub-agents to write code that looks out of place. If the team has known tech debt,
document the current state in `error-handling.md` / SLOT-17 — improvement is a separate
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
setup so every future AI session matches your team's actual Go patterns instead of
writing generic code. I'll fill `backend/`, `shared/` and the
`project-conventions.md` slots. Do you have existing convention docs (CLAUDE.md,
AGENTS.md, CONTRIBUTING.md) I can pull from, or should I scan the codebase from
scratch?"
