# H5/Go/iOS Guru workflow slice dispatcher parity 实施计划

## 范围

允许修改的 implementation 文件由 `gate-contract.json` 约束：

- `packages/cli/src/templates/guru/workflows/guru-h5.md`
- `packages/cli/src/templates/guru/workflows/guru-go.md`
- `packages/cli/src/templates/guru/workflows/guru-ios.md`
- `packages/cli/src/templates/guru/workflows/guru-client.md`
- `packages/cli/test/guru/guru-bundled.test.ts`
- `guru-template/workflows/guru-h5-workflow.md`
- `guru-template/workflows/guru-go-workflow.md`
- `guru-template/workflows/guru-ios-workflow.md`
- `guru-template/workflows/guru-client-workflow.md`

Task-local planning/check evidence 可以写入当前任务目录。

## 前置条件

- Requirements review/confirm 完成。
- Overview/detail review clean x2 完成。
- Detail confirmation 完成。
- 运行 `python3 .trellis/scripts/task.py start .trellis/tasks/07-09-guru-workflow-slice-dispatcher-parity` 后才进入实现。

## 实施切片

### Slice 1：H5 workflow parity

- [ ] 在 source template H5 Phase 2.1 开头加入 `implement-slices <task-dir> --dry-run --backend auto` 前置。
- [ ] 明确 `sub-agent` 按返回 `trellis-implement` brief 派发。
- [ ] 明确 `channel` 才使用官方 channel worker / `implement-check`。
- [ ] 明确 `inline` 串行手工执行。
- [ ] 保留 H5 自底向上实现顺序和 golden-path 红线。
- [ ] 同步 `guru-template/workflows/guru-h5-workflow.md`。

### Slice 2：Go workflow parity

- [ ] 在 source template Go Phase 2.1 开头加入同等 dispatcher 前置。
- [ ] 明确按 `selected_backend` / `decision` / `dispatch_items` 行动。
- [ ] 保留 Go 分层实现顺序、ServeMux、错误链、生命周期和 secret 约束。
- [ ] 同步 `guru-template/workflows/guru-go-workflow.md`。

### Slice 3：iOS workflow parity

- [ ] 在 source template iOS Phase 2.1 开头加入同等 dispatcher 前置。
- [ ] 明确 serial/blocked 不得强行并行。
- [ ] 保留 iOS 自底向上实现顺序、FactoryKit、Repository、ViewModel 与 WCDBSwift 边界。
- [ ] 同步 `guru-template/workflows/guru-ios-workflow.md`。

### Slice 4：验证与提交尾段

- [ ] 搜索八个 workflow 文件，确认均出现 `implement-slices <task-dir> --dry-run --backend auto`。
- [ ] 跑 `pnpm --filter @devsc/trellis run sync:guru:check`。
- [ ] 跑 `git diff --check && git diff --cached --check`。
- [ ] 若需要 commit，stage 本任务 implementation 文件并运行 `implementation-review --staged`。
- [ ] 运行 `commit-plan` 和 `check-commit`。

### Slice 5：workflow-state breadcrumb parity

- [ ] 将 client source/mirror 的 `[workflow-state:in_progress]` 改为 dispatch-mode aware。
- [ ] 将 H5 source/mirror 的 `[workflow-state:in_progress]` 改为 dispatch-mode aware。
- [ ] 将 Go source/mirror 的 `[workflow-state:in_progress]` 改为 dispatch-mode aware。
- [ ] 将 iOS source/mirror 的 `[workflow-state:in_progress]` 改为 dispatch-mode aware。
- [ ] 四个平台 breadcrumb 均保留各自验证证据提示与“设计缺陷回 Phase 1”。
- [ ] 四个平台 breadcrumb 均不再写“默认用官方 trellis channel”。

### Slice 6：bundled workflow regression test parity

- [ ] 将 `guru-bundled.test.ts` 的 ordinary `in_progress` 断言从 channel-first 改成 dispatcher-plan-first。
- [ ] 保留 `in_progress-channel` / `in_progress-sub-agent` / `in_progress-inline` rollback mode 断言。
- [ ] 跑 targeted Vitest，证明测试不再锁旧 channel breadcrumb。

## 验证命令

```bash
rg -n "implement-slices <task-dir> --dry-run --backend auto" \
  packages/cli/src/templates/guru/workflows/guru-h5.md \
  packages/cli/src/templates/guru/workflows/guru-go.md \
  packages/cli/src/templates/guru/workflows/guru-ios.md \
  guru-template/workflows/guru-h5-workflow.md \
  guru-template/workflows/guru-go-workflow.md \
  guru-template/workflows/guru-ios-workflow.md

rg -n "implement-slices <task-dir> --dry-run --backend auto" \
  packages/cli/src/templates/guru/workflows/guru-client.md \
  guru-template/workflows/guru-client-workflow.md

rg -n "默认用官方 trellis channel" \
  packages/cli/src/templates/guru/workflows/guru-client.md \
  packages/cli/src/templates/guru/workflows/guru-h5.md \
  packages/cli/src/templates/guru/workflows/guru-go.md \
  packages/cli/src/templates/guru/workflows/guru-ios.md \
  guru-template/workflows/guru-client-workflow.md \
  guru-template/workflows/guru-h5-workflow.md \
  guru-template/workflows/guru-go-workflow.md \
  guru-template/workflows/guru-ios-workflow.md \
  && exit 1 || true

pnpm --filter @devsc/trellis run sync:guru:check
git diff --check && git diff --cached --check
pnpm --dir packages/cli exec vitest run test/guru/guru-bundled.test.ts -t "routes ordinary in_progress through dispatcher plan while preserving rollback modes"
python3 .trellis/scripts/guru/guru_gate.py commit-plan .trellis/tasks/07-09-guru-workflow-slice-dispatcher-parity
```

## 风险与回滚点

- 风险：文案只补字符串但没有约束 `decision=serial|blocked`。回滚/修复：补充 dry-run report 字段是执行依据。
- 风险：误删平台 golden-path。回滚/修复：对照修改前段落恢复平台约束。
- 风险：source template 与 mirror 漂移。回滚/修复：运行 `sync:guru` 或手动同步，直到 `sync:guru:check` 通过。
- 风险：误触目标项目 workflow。回滚/修复：本任务不修改目标项目，只修改 package source + bundled mirror。

## 不做事项

- 不改 runtime Python 脚本。
- 不安装到 sibling repos。
- 不跑真实 benchmark。
- 不提交、push、archive 或 finish-work，除非用户后续明确授权。
