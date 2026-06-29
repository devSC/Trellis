# OCR (Open Code Review) 会话评审发现抽取报告

**会话文件**: `/Users/devSC/.codex/sessions/2026/06/25/rollout-2026-06-25T14-02-08-019efd5f-199b-71e0-b010-4b5b18d970a4.jsonl` (14961 行 / ~30MB)
**目标项目**: `guru_ai_himora` (Flutter)；任务 `06-26-regenerate-version-media-groups`
**评审器**: 阿里 `ocr` / Open Code Review CLI（底层 `@alibaba-group/open-code-review`，模型 gpt-5.5），`--audience agent --background <业务上下文>`，异步 background 轮询取结果。
**抽取方法**: Python json 迭代 JSONL，按 payload.type 解析 function_call / function_call_output / message，跳过 >50KB 行做关键词定位，再精读定位行。所有定位给出会话内行号。

> 重要口径说明：OCR 在 `--audience agent` 模式下输出的是**散文式逐条评论**（`─── file:line ───` + 正文 + 可选 diff 建议），**不带 P1/P2/P3 严重度标签也不带类别字段**。因此下文 OCR 发现的“类别”为本报告按正文语义归类，“严重度”OCR 未提供（仅 Guru check-worker 的 finding 带 P1/P2/P3 + route_class）。

---

## 0. 时间线与总览

| 阶段 | 会话行号 | 事件 |
|---|---|---|
| 需求对抗审查 (Guru, claude) | ~L554–L810 | `requirements-claude-*`：`review_result=clean/requirements-ready`，无 REQ_BLOCKER（4 个非阻断 finding F-01..F-04）|
| 概要/详细设计审查 (Guru) | ~L3647–L4258 | `overview-*` / `detail-*` 评审 |
| 实现 check 第 1 轮 (Guru, claude-2039) | L6121起 | `review_result=findings` / IMPLEMENT_DEFECT：P2 缺诊断日志 + P2 设计 owner mismatch + 2×P3 |
| 实现 check 第 2 轮 (Guru, claude-20104) | L6522起 | `review_result=findings` / IMPLEMENT_DEFECT：**仅 P3**；结论“可进入 PR / final-verification-ready，无 P1/P2 阻塞” |
| **用户点名 OCR** | **L6585** | `调用 open-code-review ... 直至无任何问题` |
| OCR 连通性自检 | L6600–L6604 | `which ocr` / `ocr llm test` 通过（gpt-5.5）|
| **OCR 评审 20 轮** | **L6610–L13466** | 23 次 `ocr review` 调用 → 20 个完成轮，累计 **130 条评论**（129 去重）|
| 用户要求停止 OCR + 人工审查 | L13xxx–L14xxx | 修了 preview-like 丢失 V2 current selection、AC-006 partial V2 flat fallback |
| **实现 check 最终轮 (Guru, codex-41734)** | **L14667–L14789** | `review_result=findings` / IMPLEMENT_DEFECT：**P2 = 本任务核心 bug**（见 §3、§4）|

- OCR 实际完成评审轮数：**20**（另有 1 次 `--format json` 收尾尝试 L14091 在会话结束时仍未跑完）
- OCR 评论总数：**130**（去重后 **129** 条 unique finding）
- 评审文件数随轮次从 16 增长到 35（diff 持续扩大）

---

## 1. 每一次 OCR 调用（命令 + 业务上下文 prompt）

所有调用形如：`ocr review --audience agent --timeout 20 --background "<下列业务上下文>"`（最后一次额外加 `--format json --concurrency 1`）。`--background` 文案随轮次不断被加厚（从 885 字符演进到 ~2350 字符），共 22 个变体。完整 prompt 文本如下：

### Prompt 变体 1 — 调用行 [6610]（885 字符）
```text
Flutter data-layer fix for Character Chat regenerate V2 message structure. Server Story messages list moved to /api/v2/public/story/messages:list and returns versions[], imageGroup, videoGroup. Requirements: show only current/latest text version, keep old-version generated image/video media visible after regenerate, image/video each aggregate into one existing media Cell, order image/video Cells by each group first attempts[0].createdAtUnixMs descending, choose current displayed item by group.current mediaMessageId+attemptId, preserve completed media local facts across reopen/reconcile. Important constraint: no production UI/route/l10n interaction changes except data display changes required by new message structure. Current implementation normalizes V2 DTOs in ChatRepository into existing StoryMessageGroup/GeneratedMediaMessageSummary, keeps StoryChatUseCase/UI unchanged.
```

### Prompt 变体 2 — 调用行 [7148]（1399 字符）
```text
Flutter data-layer fix for Character Chat regenerate V2 message structure. Server Story messages list moved to /api/v2/public/story/messages:list and returns versions[], imageGroup, videoGroup. Requirements: show only current/latest text version, keep old-version generated image/video media visible after regenerate, image/video each aggregate into one existing media Cell, order image/video Cells by each group first attempts[0].createdAtUnixMs descending, choose current displayed item by group.current mediaMessageId+attemptId, preserve completed media local facts across reopen/reconcile. Important constraint: no production UI/route/l10n interaction changes except data display changes required by new message structure. Implementation normalizes V2 DTOs in ChatRepository into existing StoryMessageGroup/GeneratedMediaMessageSummary, keeps StoryChatUseCase/UI unchanged. Previous OCR findings fixed: Story messages V2 now uses dedicated AppApiMethodsV2 with /api/v2 base URL instead of combining a V2 absolute-ish path with the V1 client; grouped local media snapshots persist non-selected groups from current-first items.first instead of stale items.last; test fixture attemptNo now derives from attemptId. Build_runner generated Retrofit V2 output; injectable generation is blocked by pre-existing repository DI issues, so injector.config.dart was minimally updated for the new V2 provider.
```

### Prompt 变体 3 — 调用行 [7350]（1323 字符）
```text
Flutter data-layer fix for Character Chat regenerate V2 message structure. Server Story messages list moved to /api/v2/public/story/messages:list and returns versions[], imageGroup, videoGroup. Requirements: show only current/latest text version, keep old-version generated image/video media visible after regenerate, image/video each aggregate into one existing media Cell, order image/video Cells by each group first attempts[0].createdAtUnixMs descending, choose current displayed item by group.current mediaMessageId+attemptId, preserve completed media local facts across reopen/reconcile. Important constraint: no production UI/route/l10n interaction changes except data display changes required by new message structure. Implementation normalizes V2 DTOs in ChatRepository into existing StoryMessageGroup/GeneratedMediaMessageSummary, keeps StoryChatUseCase/UI unchanged. Previous OCR findings fixed: dedicated AppApiMethodsV2 /api/v2 client and DI, all direct AffinyRemoteDataSourceImpl call sites updated including integration_test, grouped local snapshots compare selected item with the same fallback grouping key, remote terminal failed/blocked/refunded/cancelled states now win over cached local paths, V2 active text version createdAtUnixMs is normalized into createdAt, and V2 fake no longer uses noSuchMethod.
```

### Prompt 变体 4 — 调用行 [7615]（914 字符）
```text
Flutter data-layer fix for Character Chat regenerate V2 message structure. Requirements: Story messages list uses /api/v2/public/story/messages:list, current/latest text only, old-version image/video media visible after regenerate, image/video aggregate into existing cells, media cells ordered by group first attempts[0].createdAtUnixMs descending, displayed item chosen by group.current, local completed facts preserved. UI/route/l10n behavior must not change. Prior OCR rounds fixed: dedicated AppApiMethodsV2 /api/v2 client and all constructor call sites including integration_test; local grouped snapshots use a single grouping key for explicit mediaMessageId and fallback keys; DAO restores selectedIndex from latest_attempt_id; selected/latest attempt is persisted; remote terminal statuses win over cached local paths; V2 active text createdAtUnixMs maps into createdAt; V2 fake fully implements interface.
```

### Prompt 变体 5 — 调用行 [7992]（1025 字符）
```text
Task: adapt Character Chat Story messages list to server V2 structure for regenerate version media groups. Requirements: Story messages list must use /api/v2/public/story/messages:list; display only active/current text version; versions with MESSAGE_STATE_REPLACED are not extra bubbles; imageGroup and videoGroup persist old-version media after regenerate; all imageGroup media aggregate into one image cell and all videoGroup media aggregate into one video cell; image/video cell order is by each group first attempt createdAt, newest group first; cell current item follows group.current; no text version switch UI; no production UI/route/l10n interaction changes allowed except data-display consequences of the new message structure. Recent OCR fixes: dedicated V2 Retrofit client, DAO/local grouped media persistence, explicit selected media group persistence via selected_media_item_id, remote terminal status overriding cached local-ready status, and preserving local grouped media items absent from latest V2 response.
```

### Prompt 变体 6 — 调用行 [8332]（1056 字符）
```text
Task: adapt Character Chat Story messages list to server V2 regenerate version media group structure. Requirements: use /api/v2/public/story/messages:list for story message list; show active/current text version only; old-version image/video generated media must remain visible after regenerate; imageGroup aggregates into one image cell, videoGroup into one video cell; image/video cell order follows group first generation time newest first; each cell current item follows group.current; no text version switch; no production UI/route/l10n interaction changes. Recent fixes after OCR run 5: local merge no longer matches by mediaMessageId when multiple local attempts exist; remote/local merge preserves unmatched local media; current item status drives media message status; V2 combined summary is current-first per kind rather than single global selectedIndex; local persistence stores image/video current in separate persistence groups and restores latest attempts first per kind; group first time defensively uses earliest parsable attempt createdAt.
```

### Prompt 变体 7 — 调用行 [8589]（1021 字符）
```text
Task: adapt Character Chat Story messages list to server V2 regenerate version media group structure. Requirements: use /api/v2/public/story/messages:list; show active/current text version only; old-version generated image/video media remain visible after regenerate; imageGroup and videoGroup each aggregate into one existing UI media cell; cell order by group first generation time newest first; each cell current item follows group.current; no text version switch; no production UI/route/l10n interaction changes. Recent OCR fixes: V2 counters use NonNullIntConverter for string-or-number payloads; V2 media summary source id falls back to active text version id; preferred persisted group ids are scoped/validated by chat/source; image/video persistence groups use stable chat/source/kind ids with separate display_order; missing mediaMessageId fallback keys include media kind; local merge avoids ambiguous mediaMessageId fact merging; current item status drives snapshot status; unmatched local media are preserved.
```

### Prompt 变体 8 — 调用行 [9081]（1235 字符）
```text
Task: adapt Character Chat Story messages list to server V2 regenerate version media group structure. Requirements: use /api/v2/public/story/messages:list; show active/current text version only; old-version generated image/video media remain visible after regenerate; imageGroup and videoGroup each aggregate into one existing UI media cell; image/video cell order is by each group first generation time newest first, falling back to media message time when attempts are absent; each cell current item follows group.current; legacy flat media for non-V2 sources in a mixed page must still merge; no text version switch; no production UI/route/l10n interaction changes. Recent fixes: string-or-number counters and string-or-number bools decode through converters; V2 media summary source id falls back to active text version id; preferred persisted group ids are scoped/validated by chat/source; display_order is preserved when later persistence omits it; V2 nested media filters only matching flat legacy media rather than the entire page; missing mediaMessageId fallback keys include media kind; local merge avoids ambiguous mediaMessageId fact merging; current item status drives snapshot status; unmatched local media are preserved.
```

### Prompt 变体 9 — 调用行 [9406]（876 字符）
```text
业务背景：本次需求只适配 /api/v2/public/story/messages:list 的新消息结构，除消息结构变化外，生产 UI 和用户交互行为不能变化。regenerate 后服务端返回 active/current 文本版本，versions[] 保存历史文本版本，旧文本版本不额外展示气泡且当前版本不做切换 UI；imageGroup/videoGroup 不跟随 regenerate 被清空，旧版本生成的图片/视频仍要在 UI 上继续展示。imageGroup 聚合为一个图片 Cell，videoGroup 聚合为一个视频 Cell；图片 Cell 和视频 Cell 的上下顺序由各自 group 中 mediaMessages 第一个 attempt 的 createdAtUnixMs 决定，时间新的在前，缺少 attempts 时回退 media message createdAtUnixMs；每个 Cell 具体显示哪一个由 group.current 决定。非 V2 legacy flat media 在混合分页里仍要保留合并。已做的关键修复包括：NonNullBoolConverter 支持 true/false、1/0、字符串数字；ApiMediaMessage 保留 sourceVersionMessageId；V2 嵌套 source key 收集和 page-level 过滤包含 sourceVersionMessageId；缺失 mediaMessageId 时生成稳定 fallback id；V2 regenerate group 的每种媒体使用稳定 kind-scoped persistence group id；DAO 按 group first generated time 倒序排序，display_order 仅作 tie-breaker。请重点审查数据结构适配、旧版本媒体保留、current 选择、排序、legacy 混合、持久化一致性和测试覆盖，不要建议改变现有 UI 交互。
```

### Prompt 变体 10 — 调用行 [9955]（1001 字符）
```text
业务背景：本次需求只适配 /api/v2/public/story/messages:list 的新消息结构，除消息结构变化外，生产 UI 和用户交互行为不能变化。regenerate 后服务端返回 active/current 文本版本，versions[] 保存历史文本版本，旧文本版本不额外展示气泡且当前版本不做切换 UI；imageGroup/videoGroup 不跟随 regenerate 被清空，旧版本生成的图片/视频仍要在 UI 上继续展示。imageGroup 聚合为一个图片 Cell，videoGroup 聚合为一个视频 Cell；图片 Cell 和视频 Cell 的上下顺序由各自 group 中 mediaMessages 第一个 attempt 的 createdAtUnixMs 决定，时间新的在前，缺少 attempts 时回退该 mediaMessage.createdAtUnixMs；每个 Cell 当前项由 group.current 决定。非 V2 legacy flat media 在混合分页里仍要保留合并。上一轮 OCR 5 条已处理：DAO group_first_generated_at 改为每个 mediaMessage 先取 first attempt，缺 attempts 时按该 mediaMessage/file created_at fallback，再 group min 排序；repository/local summary 新增 createdAt 贯穿到 MediaMessageSnapshot/MediaAttemptSnapshot，避免本地重开时用写入时间排序；mock interceptor 支持 /api/v2 base path；local merge 和 DAO 持久化避免 mediaMessageId 复用时把旧 attempt localPath 合到新 attempt；V2 summary id 保持稳定，local datasource 对 V2 regenerate group 用 kind-scoped persistence group id。请继续审查数据结构适配、旧版本媒体保留、current 选择、排序、legacy 混合、持久化一致性和测试覆盖，不要建议改变现有 UI 交互。
```

### Prompt 变体 11 — 调用行 [10130]（798 字符）
```text
业务背景：Himora Flutter 客户端适配 /api/v2/public/story/messages:list 的 regenerate 新消息结构。服务端返回 active text message，并在 text message 上携带 versions[]、imageGroup、videoGroup。需求要求：只展示当前 active 文本；旧版本文本不生成额外气泡；imageGroup 聚合成一个图片 Cell，videoGroup 聚合成一个视频 Cell；regenerate 后旧版本生成的图片/视频仍继续展示在对应 group 内；图片 Cell 和视频 Cell 的上下顺序由各自 group 的第一个生成时间决定，按 newest-first 排序，时间来源是 group 内每个 mediaMessage 的 attempts[0].createdAtUnixMs，缺失时回退 mediaMessage/file createdAt；具体显示哪个媒体由 group.current 决定；当前版本不做文本 versionNo 切换 UI。本次需求变动除消息结构变化外，其他 UI 和用户交互行为不能变化，生产 UI/route/l10n/generated 代码应保持无 diff。此前 OCR #9/#10 已修复：V2 basePath mock 匹配、V2 media createdAt 持久化、按 per-media first attempt 排序、跨 attempt stale local facts、selectedInGroup 只标记 group.current、true /api/v2 mock 测试。请继续重点审查这些修复是否仍有数据映射、持久化、排序、选择当前媒体、旧版本媒体保留、混合 legacy/V2 兼容、测试有效性问题。
```

### Prompt 变体 12 — 调用行 [10627]（971 字符）
```text
业务背景：Himora Flutter 客户端适配 /api/v2/public/story/messages:list 的 regenerate 新消息结构。服务端返回 active text message，并在 text message 上携带 versions[]、imageGroup、videoGroup。需求要求：只展示当前 active 文本；旧版本文本不生成额外气泡；imageGroup 聚合成一个图片 Cell，videoGroup 聚合成一个视频 Cell；regenerate 后旧版本生成的图片/视频仍继续展示在对应 group 内；图片 Cell 和视频 Cell 的上下顺序由各自 group 的第一个生成时间决定，按 newest-first 排序，时间来源是 group 内每个 mediaMessage 的 attempts[0].createdAtUnixMs，缺失时回退 mediaMessage/file createdAt；具体显示哪个媒体由 group.current 决定；当前版本不做文本 versionNo 切换 UI。本次需求变动除消息结构变化外，其他 UI 和用户交互行为不能变化，生产 UI/route/l10n/generated 代码应保持无 diff。此前 OCR #9/#10/#11 已修复：V2 basePath mock 匹配、V2 media createdAt 持久化、按 per-media first attempt 排序、跨 attempt stale local facts、selectedInGroup 只标记 group.current 且远端 current 覆盖本地旧值、V2 per-kind persisted group id 不随 active source message 变化、无 latestAttemptId 时本地文件保留需要 artifact 身份一致、远端 terminal 状态不再暴露 stale localPath、含用户文本 DTO 关闭 generated toString、测试断言补强。请继续重点审查是否仍有数据映射、持久化、排序、选择当前媒体、旧版本媒体保留、混合 legacy/V2 兼容、测试有效性问题。
```

### Prompt 变体 13 — 调用行 [10893]（1209 字符）
```text
业务背景：Himora Flutter 客户端适配 /api/v2/public/story/messages:list 的 regenerate 新消息结构。服务端返回 active text message，并在 text message 上携带 versions[]、imageGroup、videoGroup。需求要求：只展示当前 active 文本；旧版本文本不生成额外气泡；imageGroup 聚合成一个图片 Cell，videoGroup 聚合成一个视频 Cell；regenerate 后旧版本生成的图片/视频仍继续展示在对应 group 内；图片 Cell 和视频 Cell 的上下顺序由各自 group 的第一个生成时间决定，按 newest-first 排序，时间来源是 group 内每个 mediaMessage 的 attempts[0].createdAtUnixMs，缺失时回退 mediaMessage/file createdAt；具体显示哪个媒体由 group.current 决定；当前版本不做文本 versionNo 切换 UI。本次需求变动除消息结构变化外，其他 UI 和用户交互行为不能变化；生产 UI/route/l10n/generated 目录保持无 diff。此前 OCR #9/#10/#11/#12 已修复：V2 basePath mock 匹配、V2 media createdAt 持久化、按 per-media attempts[0] first time 排序、跨 attempt stale local facts、selectedInGroup 只标记 group.current 且远端 current 覆盖本地旧值、append local item 清理 stale selected、MediaMessagePersistInput 默认 non-mutating、V2 per-kind persisted group id 不随 active source message 变化、无 latestAttemptId 时本地文件保留需要 artifact 身份一致、远端 terminal 状态不再暴露 stale localPath、含用户文本 DTO 关闭 generated toString、ChatHistoryController DI 注册恢复、缺 mediaMessageId current fallback 测试补强。现有 UI helper 会把一个 GeneratedMediaMessageSummary 按 kind 拆为图片/视频 cell，这是既有行为，不应为了本需求改页面结构。请继续重点审查是否仍有数据映射、持久化、排序、选择当前媒体、旧版本媒体保留、混合 legacy/V2 兼容、测试有效性问题。
```

### Prompt 变体 14 — 调用行 [11052]（1326 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media must remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group mediaMessages first attempt createdAtUnixMs, newest first, with fallback to media message createdAt only when attempts are absent. The concrete displayed item inside each cell is selected by group.current. No text version switching UI in this iteration. Existing UI helper splits GeneratedMediaMessageSummary by kind into image/video cells; do not require UI rewrites unless data behavior is wrong. Recent OCR fixes: preserve attempt order from server, do not mutate selectedInGroup on media patch persistence, authoritative remote selectedInGroup, local fact matching hardened by attempt/media ids, V2 user createdAt supports createdAtUnixMs, per-kind stable persisted group ids, first-generation ordering tests added.
```

### Prompt 变体 15 — 调用行 [11573]（1420 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group mediaMessages first attempt createdAtUnixMs, newest first, with fallback to media message createdAt only when attempts are absent. The concrete displayed item inside each cell is selected by group.current. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; latest fix only teaches this existing split helper to map selectedInGroup into each per-kind cell selectedIndex so image/video current can both be honored without new UI, controls, routes, gestures, or interaction changes. Recent OCR fixes: media group DTO toString disabled, local identity matching includes kind/mediaMessageId compatibility, DAO no longer reorders attempts by latest_attempt_id, tests now assert attempts[0] ordering and selected/current via selectedInGroup/selectedIndex.
```

### Prompt 变体 16 — 调用行 [11835]（1449 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group mediaMessages first attempt createdAtUnixMs, newest first, with fallback to media message createdAt only when attempts are absent. The concrete displayed item inside each cell is selected by group.current. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; latest fix only maps selectedInGroup into each per-kind cell selectedIndex so image/video current can both be honored without new UI, controls, routes, gestures, or interaction changes. Recent OCR fixes: media group DTO toString disabled, local identity matching includes kind/mediaMessageId compatibility, DAO preserves attempt order and uses group source for reused V2 groups, first-attempt time fallback only when attempts absent, local creates use kind-scoped media group id, usecase merge preserves selectedInGroup.
```

### Prompt 变体 17 — 调用行 [12157]（1785 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group's original first generated time, newest group first: for a group, use each mediaMessage attempts[0].createdAtUnixMs and choose the earliest valid first-attempt time as the group's original generation time; only fall back to mediaMessage.createdAtUnixMs when that mediaMessage has no attempts. Do not use the latest regenerated media time to order image/video cells. The concrete displayed item inside each cell is selected by group.current. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; latest fix only maps selectedInGroup into each per-kind cell selectedIndex so image/video current can both be honored without new UI, controls, routes, gestures, or interaction changes. Recent OCR fixes: media group DTO toString disabled, local identity matching includes kind/mediaMessageId compatibility including mediaItemId fast path, DAO preserves attempt order and uses group source for reused V2 groups, first-attempt time fallback only when attempts absent, local creates use kind-scoped media group id, usecase merge preserves selectedInGroup, active text version missing createdAt preserves top-level timestamp.
```

### Prompt 变体 18 — 调用行 [12611]（2119 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group's original first generated time, newest group first: for a group, use each mediaMessage attempts[0].createdAtUnixMs and choose the earliest valid first-attempt time as the group's original generation time; only fall back to mediaMessage.createdAtUnixMs when that mediaMessage has no attempts. If an attempt row exists but lacks a valid created time, it must not fall back to the media message time. Do not use latest regenerated media time to order image/video cells. The concrete displayed item inside each cell is selected by group.current / selectedInGroup. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; it only maps selectedInGroup into each per-kind selectedIndex without new UI controls/routes/gestures. DAO internally stores generated_media_attempts.attempt_id as mediaMessageId::attemptId to prevent reused attempt ids across media messages from overwriting rows; restored domain/UI attemptId remains the original server attemptId. Recent OCR fixes: local identity matching includes kind/mediaMessageId compatibility including mediaItemId fast path, DAO preserves attempt order and uses group source for reused V2 groups, missing attempt timestamps are stored empty and ordered as missing, first-attempt fallback only when attempts absent, local creates use kind-scoped media group id, usecase merge lets incoming selectedInGroup/current override stale old current, active text version missing createdAt preserves top-level timestamp.
```

### Prompt 变体 19 — 调用行 [12966]（1973 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group's original first generated time, newest group first: for a group, use each mediaMessage attempts[0].createdAtUnixMs and choose the earliest valid first-attempt time as the group's original generation time; only fall back to mediaMessage.createdAtUnixMs when that mediaMessage has no attempts. If an attempt row exists but lacks a valid created time, it must not fall back to the media message time. Do not use latest regenerated media time to order image/video cells. The concrete displayed item inside each cell is selected by group.current / selectedInGroup. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; it only maps selectedInGroup into each per-kind selectedIndex without new UI controls/routes/gestures. DAO internally stores generated_media_attempts.attempt_id as mediaMessageId::attemptId to prevent reused attempt ids across media messages from overwriting rows; restored domain/UI attemptId remains the original server attemptId. Current fix preserves API/DAO attempt item order and does not move current to the front; selectedInGroup carries current. Flat media dedupe is identity-based: nested mediaMessageId+kind duplicates are filtered, nested media without ids falls back to source keys, and flat sibling media for partial V2 nested groups remains visible on the current V2 bubble.
```

### Prompt 变体 20 — 调用行 [13350]（2172 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group's original first generated time, newest group first: for a group, use each mediaMessage attempts[0].createdAtUnixMs and choose the earliest valid first-attempt time as the group's original generation time; only fall back to mediaMessage.createdAtUnixMs when that mediaMessage has no attempts. If an attempt row exists but lacks a valid created time, it must not fall back to the media message time. Do not use latest regenerated media time to order image/video cells. The concrete displayed item inside each cell is selected by group.current / selectedInGroup. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; it only maps selectedInGroup into each per-kind selectedIndex without new UI controls/routes/gestures. DAO internally stores generated_media_attempts.attempt_id as mediaMessageId::attemptId to prevent reused attempt ids across media messages from overwriting rows; restored domain/UI attemptId remains the original server attemptId. Current fix preserves API/DAO attempt item order and does not move current to the front; selectedInGroup carries current. Flat media dedupe is identity-based: nested mediaMessageId+kind duplicates are filtered, nested media without ids falls back to source keys plus media kind, and flat sibling media for partial V2 nested groups remains visible on the current V2 bubble. Create/retry generated-media commands may carry an existing V2 summary mediaGroupId only for local persistence grouping; it is not sent to backend and preserves existing UI behavior.
```

### Prompt 变体 21 — 调用行 [13588, 13750]（2353 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group's original first generated time, newest group first: for a group, use each mediaMessage attempts[0].createdAtUnixMs and choose the earliest valid first-attempt time as the group's original generation time; only fall back to mediaMessage.createdAtUnixMs when that mediaMessage has no attempts. If an attempt row exists but lacks a valid created time, it must not fall back to the media message time. Do not use latest regenerated media time to order image/video cells. The concrete displayed item inside each cell is selected by group.current / selectedInGroup. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; it only maps selectedInGroup into each per-kind selectedIndex without new UI controls/routes/gestures. DAO internally stores generated_media_attempts.attempt_id as mediaMessageId::attemptId to prevent reused attempt ids across media messages from overwriting rows; restored domain/UI attemptId remains the original server attemptId. Current fix preserves API/DAO attempt item order and does not move current to the front; selectedInGroup carries current. Flat media dedupe is identity-based: nested mediaMessageId+kind duplicates are filtered, nested media without ids falls back to source keys plus media kind, and flat sibling media for partial V2 nested groups remains visible on the current V2 bubble. Create/retry generated-media commands may carry an existing V2 summary mediaGroupId only for local persistence grouping; it is not sent to backend and preserves existing UI behavior. V2 summaries use an internal media_group_v2_* local grouping marker so grouping does not depend on backend id prefixes; old media_group_msggrp_* remains accepted for compatibility.
```

### Prompt 变体 22 — 调用行 [14091]（2349 字符）
```text
Himora Flutter chat regenerate V2 message structure change. Requirement: only message structure/data mapping changes are allowed; existing UI and user interaction behavior must not change. New /api/v2/public/story/messages:list text messages include versions[], imageGroup, videoGroup. Only active/current text version should display as text; replaced text versions are not separate bubbles. Old-version image/video media remain visible after regenerate. imageGroup aggregates into one image media cell, videoGroup aggregates into one video media cell. Image/video cell vertical order is by each group original first generated time, newest group first: for a group, use each mediaMessage attempts[0].createdAtUnixMs and choose the earliest valid first-attempt time as the group original generation time; only fall back to mediaMessage.createdAtUnixMs when that mediaMessage has no attempts. If an attempt row exists but lacks a valid created time, it must not fall back to the media message time. Do not use latest regenerated media time to order image/video cells. The concrete displayed item inside each cell is selected by group.current / selectedInGroup. No text version switching UI. Existing UI helper splits one GeneratedMediaMessageSummary by kind into image/video cells; it only maps selectedInGroup into each per-kind selectedIndex without new UI controls/routes/gestures. DAO internally stores generated_media_attempts.attempt_id as mediaMessageId::attemptId to prevent reused attempt ids across media messages from overwriting rows; restored domain/UI attemptId remains the original server attemptId. Current fix preserves API/DAO attempt item order and does not move current to the front; selectedInGroup carries current. Flat media dedupe is identity-based: nested mediaMessageId+kind duplicates are filtered, nested media without ids falls back to source keys plus media kind, and flat sibling media for partial V2 nested groups remains visible on the current V2 bubble. Create/retry generated-media commands may carry an existing V2 summary mediaGroupId only for local persistence grouping; it is not sent to backend and preserves existing UI behavior. V2 summaries use an internal media_group_v2_* local grouping marker so grouping does not depend on backend id prefixes; old media_group_msggrp_* remains accepted for compatibility.
```

---

## 2. OCR 每轮评审输出（逐轮 summary + 逐条评论）

各轮 `[ocr] Summary` 行与评论数：

| 轮 | 行号 | files reviewed | comments | 累计 token |
|---|---|---|---|---|
| 1 | L6672 | 16 | 3 | ~2.46M |
| 2 | L7209 | 21 | 5 | ~1.58M |
| 3 | L7427 | 22 | 2 | ~2.40M |
| 4 | L7681 | 23 | 2 | ~2.69M |
| 5 | L8091 | 24 | 7 | ~2.75M |
| 6 | L8410 | 24 | 13 | ~2.87M |
| 7 | L8681 | 24 | 12 | ~2.04M |
| 8 | L9145 | 24 | 6 | ~2.27M |
| 9 | L9486 | 25 | 5 | ~2.36M |
| 10 | L9972 | 29 | 3 | ~2.66M |
| 11 | L10227 | 29 | 10 | ~2.55M |
| 12 | L10705 | 29 | 8 | ~3.43M |
| 13 | L10954 | 30 | 9 | ~3.90M |
| 14 | L11177 | 30 | 6 | ~3.96M |
| 15 | L11661 | 32 | 6 | ~2.68M |
| 16 | L12016 | 33 | 4 | ~3.82M |
| 17 | L12277 | 33 | 7 | ~2.88M |
| 18 | L12738 | 34 | 8 | ~4.05M |
| 19 | L13075 | 34 | 6 | ~2.74M |
| 20 | L13466 | 35 | 8 | ~4.62M |

逐条评论（完整正文，含 OCR 给出的最小 diff 建议）：

### OCR 轮 1 — L6672（16 files, 3 comments）

**1.1  `lib/data/api/app_api_methods.dart:138-139`**

```
`AppApiMethods` is instantiated with `baseUrl: AffinyApiContract.defaultBaseUrl`, which already
includes `/api/v1`. Dio/retrofit will combine that base URL with this path, so the request can
resolve to `/api/v1/api/v2/public/story/messages:list` instead of the required
`/api/v2/public/story/messages:list`. Please route this method through a v2-specific base URL (or a
dynamic absolute `@Url` built from the authority only) so the generated request does not keep the v1
prefix.
```

**1.2  `test/data/repositories/chat_repository_test.dart:2089-2089`**

```
This conditional always returns `1`, so the fixture does not actually model different
`current.attemptNo` values when `imageCurrentAttemptId` changes. That can hide regressions if the
mapper later uses `attemptNo` as a fallback for current-item selection or ordering. Consider
deriving it from the attempt id (or making it an explicit fixture parameter).

-             'attemptNo': imageCurrentAttemptId == 'img_attempt_v2_1' ? 1 : 1,
+             'attemptNo': int.tryParse(imageCurrentAttemptId.split('_').last) ?? 1,
```

**1.3  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:363-369`**

```
For V2 summaries, `selectedIndex` can identify only one item across the combined image+video list,
while each media group has already been reordered so its own current item is first. For a
non-selected group/media message with multiple attempts, falling back to `items.last` can persist a
stale/non-current attempt as `latestAttempt` and `assetUrl` (e.g. video current first, image
selected overall). Please use the current-first ordering as the fallback, and normalize the id
comparison to avoid missing a selected item due to whitespace.

+     final selectedMediaMessageId = summarySelectedItem?.mediaMessageId?.trim();
      final latestItem =
-         summarySelectedItem != null &&
-             summarySelectedItem.mediaMessageId == mediaMessageId
+         summarySelectedItem != null && selectedMediaMessageId == mediaMessageId
          ? summarySelectedItem
          : items.isEmpty
          ? null
-         : items.last;
+         : items.first;
```

### OCR 轮 2 — L7209（21 files, 5 comments）

**2.1  `lib/data/datasources/affiny_remote_data_source_impl.dart:26-26`**

```
Adding `_apiV2` as a required positional constructor argument leaves at least one existing direct
instantiation (`integration_test/story_chat_real_api_e2e_test.dart`) passing
`TimestampApiRequestMetadataProvider` as the second argument, which will fail to compile. Please
update all `AffinyRemoteDataSourceImpl(...)` call sites to pass an `AppApiMethodsV2` before the
metadata provider (or provide a backwards-compatible constructor path if those call sites must
remain unchanged).
```

**2.2  `test/data/datasources/affiny_remote_data_source_impl_test.dart:440-441`**

```
Since `AppApiMethodsV2` currently has only `listStoryMessages`, this fake can implement the
interface completely without `noSuchMethod`. Keeping `noSuchMethod` here makes future additions to
the V2 API interface compile without updating the fake, which weakens this routing test and can hide
interface drift until runtime.
```

**2.3  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:363-369`**

```
This loses the selected attempt when items do not carry `mediaMessageId` and the grouping key falls
back to `_mediaMessageIdFromSummaryItem` (for example `mediaItemId`). In that case
`selectedMediaMessageId` is null, so the code always falls back to `items.first` even if
`summarySelectedItem` belongs to this group via the fallback key. That can persist the wrong
`latestAttempt`/asset after reopen. Consider deriving the selected item's grouping key with the same
helper used to build `itemsByMediaMessageId` and comparing that key to `mediaMessageId` (or
otherwise preserving `selectedIndex` within the group).

-     final selectedMediaMessageId = summarySelectedItem?.mediaMessageId?.trim();
+     final selectedItemMediaMessageId = summarySelectedItem?.mediaMessageId;
+     final selectedItemKey = summarySelectedItem == null
+         ? null
+         : selectedItemMediaMessageId != null &&
+               selectedItemMediaMessageId.trim().isNotEmpty
+         ? selectedItemMediaMessageId.trim()
+         : summarySelectedItem.mediaItemId.trim();
      final latestItem =
-         summarySelectedItem != null && selectedMediaMessageId == mediaMessageId
+         summarySelectedItem != null && selectedItemKey == mediaMessageId
          ? summarySelectedItem
          : items.isEmpty
          ? null
          : items.first;
```

**2.4  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:809-811`**

```
This makes any cached local file override newer remote terminal states such as `failed`, `blocked`,
`refunded`, or `cancelled`. If the server has invalidated the attempt, the UI will still treat it as
`localReady` and display stale media instead of the terminal/error state. Prefer preserving
`localReady` only when the remote state is still displayable or transient, and let terminal remote
states win.

-     if (localPath != null) {
+     if (localPath != null &&
+         remote != GeneratedMediaItemSummaryStatus.failed &&
+         remote != GeneratedMediaItemSummaryStatus.blocked &&
+         remote != GeneratedMediaItemSummaryStatus.refunded &&
+         remote != GeneratedMediaItemSummaryStatus.cancelled) {
        return GeneratedMediaItemSummaryStatus.localReady;
      }
```

**2.5  `lib/data/repositories/impl/chat_repository_impl.dart:1123-1125`**

```
`_aiMessageFromJson` only reads `createdAt`/`created_at`, so the V2 version timestamp written as
`createdAtUnixMs` is ignored and the AI message falls back to `DateTime.now()`. That can make
reopened/resumed chats report the wrong `createdAt`/`updatedAt` and `lastMessageAt` for V2 history.
Normalize the field to a key consumed by `_aiMessageFromJson` (or teach that parser to read
`createdAtUnixMs`).

              'text': activeVersion.text,
              'state': activeVersion.state.wireName,
+             'createdAt': activeVersion.createdAtUnixMs,
              'createdAtUnixMs': activeVersion.createdAtUnixMs,
```

### OCR 轮 3 — L7427（22 files, 2 comments）

**3.1  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:365-369`**

```
This comparison can miss the selected item when it has an explicit `mediaMessageId`.
`_snapshotsFromGeneratedMediaSummary` groups with `item.mediaMessageId` first, but
`_mediaMessageIdFromSummaryItem` always falls back to the summary group id before the item id. For
V2 summaries where `mediaGroupId` is the version group (for example `media_group_msggrp_ai_001`) and
items have `mediaMessageId` like `media_img_from_v1`, `selectedItemKey` becomes `msggrp_ai_001`,
never matching the entry key. The snapshot then persists `items.first` as `latestAttempt`/`assetUrl`
instead of the current selected attempt, so reopen/reconcile can display the wrong regenerated
media. Use the same grouping-key function for both grouping and selected-item comparison.

      final selectedItemKey = summarySelectedItem == null
          ? null
-         : _mediaMessageIdFromSummaryItem(media, summarySelectedItem);
+         : _mediaMessageGroupingKey(media, summarySelectedItem);
      final latestItem =
          summarySelectedItem != null && selectedItemKey == mediaMessageId
```

**3.2  `test/data/datasources/affiny_chat_local_data_source_test.dart:982-985`**

```
This test is named around persisting the selected item, but it never verifies that `selectedIndex`
(or the currently displayed item) survives the persist/load round trip. With multiple fallback items
this can pass even if the datasource reloads `selectedIndex` as the default `0`, which would show
the wrong generated media after reopen. Please assert the restored
`generatedMediaMessage.selectedIndex` (or selected item id) before checking item fields.

-         final items =
-             seed.single.aiVersions.single.generatedMediaMessage!.displayItems;
+         final media = seed.single.aiVersions.single.generatedMediaMessage!;
+         final items = media.displayItems;
          expect(items, hasLength(2));
-         expect(items[1].mediaItemId, 'attempt_2');
+         expect(media.selectedIndex, 1);
+         expect(items[media.selectedIndex].attemptId, 'attempt_2');
```

### OCR 轮 4 — L7681（23 files, 2 comments）

**4.1  `lib/data/dao/generated_media_dao_impl.dart:703-706`**

```
This restores `selectedIndex` from every media file's `latest_attempt_id`. During persistence each
grouped media file gets a `latest_attempt_id` (non-selected files fall back to their first item), so
when a summary aggregates multiple media files the last row with any latest attempt will overwrite
the actual selected item. This can make local seeds reopen on the wrong image/video after a
regenerate. Please only apply the index for the file that represents the summary's selected/current
media item (for example by using the selected media id from `generated_media_messages`, or by
persisting a selection marker), rather than treating every `latest_attempt_id` as the group
selection.
```

**4.2  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:794-804`**

```
This rebuilds the merged media summary exclusively from `remote.displayItems`, so any already
persisted local media item that is absent from the latest V2 response is dropped from the page
returned by `mergeFetchedMessagePage` (and from the page passed to `upsertFetchedMessagePage`). That
can make old regenerate versions or locally completed media disappear after refresh, even though the
local DAO still has them. Please keep unmatched local display items in the merged list after merging
matched remote items, while preserving the remote/current selection semantics.
```

### OCR 轮 5 — L8091（24 files, 7 comments）

**5.1  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:805-808`**

```
Falling back to `mediaMessageId` can merge facts from the wrong regenerate attempt. In V2 grouped
media, several `GeneratedMediaItemSummary`s can share the same `mediaMessageId` while representing
different attempts; `localByMediaMessageId` stores only the first local item for that message. If a
remote item has a missing/new `attemptId`, this path can copy another attempt's `localPath`, status,
or `liked` flag onto it. Prefer matching only by item/attempt identity, or use the media-message
fallback only when the local group has a single candidate.

        final localItem =
            localByItemId[remoteItem.mediaItemId.trim()] ??
-           localByAttemptId[remoteItem.attemptId?.trim()] ??
-           localByMediaMessageId[remoteItem.mediaMessageId?.trim()];
+           localByAttemptId[remoteItem.attemptId?.trim()];
```

**5.2  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:471-477`**

```
This makes the whole grouped media cell `generating` whenever any preserved old attempt is still
generating/polling, even if the current item for the group is already completed. Since regenerate
groups keep old-version media alongside the current item, aggregate status should be derived from
the current/latest item (or from the reordered first attempt) before considering stale attempts;
otherwise the UI can keep showing a spinner/loading state for a completed current media cell.
```

**5.3  `lib/data/datasources/affiny_remote_data_source_impl.dart:0-0`**

```
Matching by `mediaMessageId` as the last fallback is unsafe for regenerated groups because multiple
attempts/items can share the same media message id. If the remote attempt id is missing or changed,
this can merge the cached local path/status/liked flag from the first local attempt into a different
remote attempt. Prefer only matching by item/attempt identifiers here, or use `mediaMessageId` only
when the local group has exactly one item for that id.

+       final mediaMessageId = remoteItem.mediaMessageId?.trim();
+       final localCandidatesByMediaMessageId = mediaMessageId == null
+           ? const <GeneratedMediaItemSummary>[]
+           : local.displayItems
+                 .where((item) => item.mediaMessageId?.trim() == mediaMessageId)
+                 .toList(growable: false);
        final localItem =
            localByItemId[remoteItem.mediaItemId.trim()] ??
            localByAttemptId[remoteItem.attemptId?.trim()] ??
-           localByMediaMessageId[remoteItem.mediaMessageId?.trim()];
+           (localCandidatesByMediaMessageId.length == 1
+               ? localCandidatesByMediaMessageId.single
+               : null);
```

**5.4  `lib/data/datasources/affiny_remote_data_source_impl.dart:172-176`**

```
When the remote selected index is invalid or the latest V2 response omits the current media item
that was preserved from local cache, this resets selection to the first remote item. That can ignore
the persisted grouped-media selection and show the wrong version after refresh/partial responses.
Consider falling back to the matching local selected item when it is still present in the merged
`items` list before defaulting to `0`.

- Future<StoryMessagePage> listStoryMessagesV2(
-     StoryMessageListPayload request,
-   ) {
-     return _apiV2.listStoryMessages(_requestId, _query(request));
-   }
+       selectedIndex: _mergedSelectedIndex(remote, local, items),
```

**5.5  `lib/data/datasources/affiny_remote_data_source_impl.dart:0-0`**

```
This derives the whole media message status from any generating/polling item before considering the
selected/current item. For regenerated media, preserved old attempts can coexist with the current
item; a stale non-current loading attempt would make a completed current cell persist as
`generating`, affecting display/actions. The aggregate status should be based on the selected/latest
item for this snapshot, or at least prioritize displayable current status over non-current loading
attempts.

-     if (items.any(
-       (item) =>
-           item.status == GeneratedMediaItemSummaryStatus.generating ||
-           item.status == GeneratedMediaItemSummaryStatus.polling,
-     )) {
+     final currentItem = items.isEmpty ? null : items.first;
+     if (currentItem?.status == GeneratedMediaItemSummaryStatus.generating ||
+         currentItem?.status == GeneratedMediaItemSummaryStatus.polling) {
        return MediaMessageStatus.generating;
      }
```

**5.6  `lib/data/repositories/impl/chat_repository_impl.dart:1204-1210`**

```
This flattens imageGroup and videoGroup into a single summary but `GeneratedMediaMessageSummary` has
only one `selectedIndex`. When both groups are present, the loop overwrites `selectedIndex` for each
group, so only the current item from the last sorted group is represented as selected. Downstream
persistence derives `selectedInGroup` from this single selected item, which can lose the
`group.current` selection for the other media cell after local reload/merge. Consider keeping
image/video as separate summaries/cells at the repository/domain level, or extending the model so
each media group carries its own current selection instead of a single global index.
```

**5.7  `lib/data/repositories/impl/chat_repository_impl.dart:1299-1304`**

```
This uses only `attempts.first` to determine the group's first generated time. Unless the V2 API
guarantees attempts are sorted oldest-first, a regenerated media message whose attempts arrive
newest-first (or otherwise unsorted) will give the wrong group timestamp, which can violate the
required image/video cell ordering by each group's first attempt `createdAt` (newest group first).
Safer is to parse all attempts for the media message and use the minimum createdAt value.

    int? _firstAttemptCreatedAt(ApiMediaMessage message) {
-     if (message.attempts.isEmpty) {
-       return null;
+     return message.attempts
+         .map((attempt) => int.tryParse(attempt.createdAtUnixMs))
+         .whereType<int>()
+         .fold<int?>(null, (previous, value) {
+           if (previous == null || value < previous) {
+             return value;
      }
-     return int.tryParse(message.attempts.first.createdAtUnixMs);
+           return previous;
+         });
    }
```

### OCR 轮 6 — L8410（24 files, 13 comments）

**6.1  `lib/data/dao/generated_media_dao_impl.dart:795-799`**

```
Returning the server-provided group id without checking the existing persisted group's chat/source
context can corrupt local state if that id is reused or malformed. The table is keyed only by
`(account_id, media_group_id)`, and the later `ConflictAlgorithm.replace` will overwrite the group
row while files are still filtered by `chat_id`, so another chat/source can inherit the wrong
`selected_media_item_id`. Before accepting a preferred id, load any existing row and either verify
`chat_id`/`source_ai_message_id` match or derive a scoped local id (for example include
chat/source/kind).
```

**6.2  `lib/data/datasources/affiny_remote_data_source_impl.dart:172-176`**

```
These new V2 numeric fields are decoded by the generated code with `(json['...'] as num?)?.toInt()`,
so a string-encoded value from the API (common for proto/JSON numeric fields in this codebase, and
already handled by `NonNullIntConverter`) will throw during story message deserialization. Please
apply the existing non-null int converter here (and to the corresponding generated code/tests) so
number and string payloads are both accepted.

- Future<StoryMessagePage> listStoryMessagesV2(
-   StoryMessageListPayload request,
- ) {
-   return _apiV2.listStoryMessages(_requestId, _query(request));
- }
+     @Default(0) @NonNullIntConverter() int versionNo,
```

**6.3  `lib/data/datasources/affiny_remote_data_source_impl.dart:0-0`**

```
`attemptNo` and `sourceTextVersionNo` are part of the new server response contract, but leaving them
as plain `int` makes deserialization fail if the backend encodes them as strings. Use the existing
`NonNullIntConverter` for consistency with flexible API scalar handling.

-     @Default(0) int attemptNo,
+     @Default(0) @NonNullIntConverter() int attemptNo,
      @Default('') @NonNullStringConverter() String sourceMessageId,
-     @Default(0) int sourceTextVersionNo,
+     @Default(0) @NonNullIntConverter() int sourceTextVersionNo,
```

**6.4  `lib/data/repositories/impl/chat_repository_impl.dart:1210-1212`**

```
This uses the raw top-level V2 message id as the media summary source, but `_v2AiMessageFromJson`
already falls back to the active text version id when the top-level `messageId` is blank. In that
case the media is visually attached by `_copyAiWithGeneratedMedia`, but `sourceAiMessageId` remains
empty, so local persistence skips it and media actions that send `sourceMessageId` can target an
empty id. Please resolve the media summary source id with the same fallback as the visible AI bubble
(top-level id, then active/current text version id).

+     final sourceAiMessageId =
+         _nonEmptyString(message.messageId) ??
+         _nonEmptyString(_activeTextVersion(message)?.messageId) ??
+         '';
      return GeneratedMediaMessageSummary(
        mediaGroupId: 'media_group_$mediaGroupId',
-       sourceAiMessageId: message.messageId,
+       sourceAiMessageId: sourceAiMessageId,
```

**6.5  `lib/data/api/models/story_models.g.dart:131-131`**

```
The V2 contract allows these numeric fields to arrive as JSON numbers or strings (e.g. `versionNo` /
`sourceTextVersionNo` are documented as int-or-string). With plain `int` fields, the generated
`fromJson` casts via `(json[...] as num?)`, so a string value will throw during story message list
deserialization and can break the whole chat load. Please use the existing `NonNullIntConverter` for
the new V2 numeric response fields so string-encoded numbers safely decode to integers/default 0.

- versionNo: (json['versionNo'] as num?)?.toInt() ?? 0,
+     @Default('') @NonNullStringConverter() String versionGroupId,
+     @Default(0) @NonNullIntConverter() int versionNo,
+     // V2 nested group 权威来源；旧结构缺省时保持空列表/null。
+     @Default(<ApiChatMessageVersion>[]) List<ApiChatMessageVersion> versions,
```

**6.6  `lib/data/api/models/story_models.g.dart:131-131`**

```
Same decoding issue here: `versionNo` is part of the server V2 version payload and may be
string-encoded. Without `NonNullIntConverter`, a valid string value causes deserialization to fail
before repository fallback logic can select the active/current version.

- versionNo: (json['versionNo'] as num?)?.toInt() ?? 0,
+     @Default('') @NonNullStringConverter() String messageId,
+     @Default('') @NonNullStringConverter() String versionGroupId,
+     @Default(0) @NonNullIntConverter() int versionNo,
+     @Default(MessageState.unspecified)
```

**6.7  `lib/data/api/app_api_methods_v2.dart:0-0`**

```
The new V2 numeric fields are decoded as plain `int`s. Other API models use converters for
server-provided numeric values because the backend may encode numbers as JSON strings; if
`versionNo` arrives as `'2'`, generated `fromJson` will throw before the story list can load. Please
apply the existing non-null int converter to these V2 counters (and likewise to
`attemptNo`/`sourceTextVersionNo` below) so both numeric and string payloads are accepted.

-     @Default(0) int versionNo,
+     @Default(0) @NonNullIntConverter() int versionNo,
```

**6.8  `lib/data/api/models/story_models.g.dart:0-0`**

```
`attemptNo` and especially `sourceTextVersionNo` are V2 wire fields used to identify the current
media attempt and source text version. The generated parser currently requires JSON numbers; if the
backend sends string-encoded values, deserialization fails or the current media group cannot be
restored. Apply `NonNullIntConverter` to these numeric response fields as well.

      @Default('') @NonNullStringConverter() String mediaMessageId,
      @Default('') @NonNullStringConverter() String attemptId,
-     @Default(0) int attemptNo,
+     @Default(0) @NonNullIntConverter() int attemptNo,
      @Default('') @NonNullStringConverter() String sourceMessageId,
-     @Default(0) int sourceTextVersionNo,
+     @Default(0) @NonNullIntConverter() int sourceTextVersionNo,
      @Default(false) bool liked,
```

**6.9  `lib/data/api/app_api_methods_v2.dart:0-0`**

```
These V2 attempt/version counters are plain `int`s, so string-encoded values from the API will fail
deserialization. Use the existing tolerant integer converter here as well to keep V2 media group
parsing compatible with the API's mixed numeric encoding patterns.

-     @Default(0) int attemptNo,
+     @Default(0) @NonNullIntConverter() int attemptNo,
      @Default('') @NonNullStringConverter() String sourceMessageId,
-     @Default(0) int sourceTextVersionNo,
+     @Default(0) @NonNullIntConverter() int sourceTextVersionNo,
```

**6.10  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:361-365`**

```
Using the current display order in the persistence key makes the same image/video group unstable. V2
orders cells by first-generation time, so adding a later video or receiving a different ordering can
change an existing image from `baseGroupId`/`baseGroupId_0_image` to another key. Because the DAO
uses this group id to restore selection/local paths, that can orphan prior local state or create
duplicate cells after refresh. Prefer a stable per-kind key that does not depend on item order, and
handle migration/lookup from the old single-kind `baseGroupId` when a second kind appears.

-     final orderIndex = orderedKinds.indexOf(targetKind);
      final suffix = targetKind == StoryMessageMediaKind.video
          ? 'video'
          : 'image';
-     return '${baseGroupId}_${orderIndex < 0 ? 0 : orderIndex}_$suffix';
+     return '${baseGroupId}_$suffix';
```

**6.11  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:458-462`**

```
This fallback returns the same stripped group id for every item without `mediaMessageId`. If such a
summary contains both image and video items, `_snapshotsFromGeneratedMediaSummary` will merge them
into one snapshot before `_persistenceMediaGroupId` can split image/video cells, so one kind can be
lost or persisted with the wrong status/kind. When item-level ids are absent, include the media kind
(or use the item id first) so image and video cannot collapse into the same media message key.

+     final itemId = item.mediaItemId.trim();
+     if (itemId.isNotEmpty) {
+       return itemId;
+     }
      if (groupId.startsWith('media_group_') && groupId.length > 12) {
-       return groupId.substring(12);
+       final suffix = item.kind == StoryMessageMediaKind.video
+           ? 'video'
+           : 'image';
+       return '${groupId.substring(12)}_$suffix';
      }
-     final itemId = item.mediaItemId.trim();
-     return itemId.isEmpty ? null : itemId;
+     return null;
```

**6.12  `test/data/repositories/chat_repository_mock_api_test.dart:161-161`**

```
Same concern as above: if the V2 response sends attempt/version numbers as JSON strings,
deserialization will fail because this field is currently generated as a direct `num` cast. Consider
using `@NonNullIntConverter()` for these counters to match the existing tolerant API model behavior.

- AppApiMethodsV2(dio, baseUrl: AffinyApiContract.defaultV2BaseUrl),
+     @Default(0) @NonNullIntConverter() int attemptNo,
+     @Default('') @NonNullStringConverter() String sourceMessageId,
+     @Default(0) @NonNullIntConverter() int sourceTextVersionNo,
```

**6.13  `test/data/repositories/chat_repository_mock_api_test.dart:0-0`**

```
These V2 numeric fields are decoded by the generated code with `(json['...'] as num?)?.toInt()`, so
a valid payload that encodes them as strings will throw before the default can apply. Since this
model already imports `NonNullIntConverter` for number-or-string tolerant response scalars, please
apply it consistently to version/attempt counters (including `versionNo`, `attemptNo`, and
`sourceTextVersionNo`) or confirm the V2 contract guarantees JSON numbers only.

-     @Default(0) int versionNo,
+     @Default(0) @NonNullIntConverter() int versionNo,
```

### OCR 轮 7 — L8681（24 files, 12 comments）

**7.1  `lib/data/api/models/generation_models.g.dart:203-203`**

```
`attemptCount` still uses a direct `num` cast while the V2 API counters are expected to be
string-or-number tolerant. If the server returns `"1"`, this deserialization throws before the media
group can be rendered. Please annotate `ApiMediaMessage.attemptCount` with `@NonNullIntConverter()`
in `generation_models.dart` and regenerate this file, matching the handling added for `attemptNo`
and `sourceTextVersionNo`.

-   attemptCount: (json['attemptCount'] as num?)?.toInt() ?? 0,
+   attemptCount: json['attemptCount'] == null
+       ? 0
+       : const NonNullIntConverter().fromJson(json['attemptCount']),
```

**7.2  `.trellis/tasks/06-26-06-26-regenerate-version-media-groups/task.json:146-147`**

```
These newly recorded review evidences appear to be truncated mid-sentence (`...success+failure path`
and `Cr`). The JSON remains valid, but task/audit tooling or future reviewers may treat these
records as incomplete evidence. Please either restore the full evidence text from the run output or
shorten it intentionally to a complete summary.
```

**7.3  `.trellis/tasks/06-26-06-26-regenerate-version-media-groups/task.json:156-157`**

```
This evidence value is cut off at `Cr`, which makes the audit record incomplete even though the JSON
syntax is valid. Please replace it with the full run evidence or a complete concise summary.
```

**7.4  `lib/data/api/models/story_models.dart:159-160`**

```
These V2 DTO booleans bypass the existing non-null bool converter, so generated deserialization uses
`json['current'] as bool?` / `json['activeVersion'] as bool?`. If the API returns proto-style
tolerant values such as `0/1` or `'true'/'false'` (the project already has `NonNullBoolConverter`
for this), message-list decoding can throw before the mapper can fall back, breaking regenerated
chats. Please apply the bool converter to these wire fields.

-     @Default(false) bool current,
-     @Default(false) bool activeVersion,
+     @Default(false) @NonNullBoolConverter() bool current,
+     @Default(false) @NonNullBoolConverter() bool activeVersion,
```

**7.5  `lib/data/api/models/story_models.dart:182-182`**

```
`liked` is decoded with a plain bool cast in the generated code. For the same reason as other API
bools in this layer, a string/number boolean payload would fail the whole media group decode and
could prevent the V2 message list from loading. Use `NonNullBoolConverter` here as well.

-     @Default(false) bool liked,
+     @Default(false) @NonNullBoolConverter() bool liked,
```

**7.6  `lib/data/api/models/story_models.freezed.dart:467-467`**

```
These new V2 boolean fields are generated without `NonNullBoolConverter`, so the matching `fromJson`
code casts them with `json['current'] as bool?` / `json['activeVersion'] as bool?`. If the
V2/proto-derived payload sends `0/1` or `'true'/'false'` (the project already has
`NonNullBoolConverter` for this), story message parsing will throw instead of defaulting. Please add
`@NonNullBoolConverter()` to `current` and `activeVersion` in `story_models.dart` and regenerate
this file.
```

**7.7  `lib/data/api/models/story_models.freezed.dart:621-621`**

```
`liked` has the same plain-bool deserialization risk: generated JSON code will do `json['liked'] as
bool?`, while the API model layer has `NonNullBoolConverter` to tolerate numeric/string/null boolean
payloads. Annotate this field with `@NonNullBoolConverter()` in the source model and regenerate to
avoid chat loading failures on non-bool values.
```

**7.8  `lib/data/dao/generated_media_dao_impl.dart:96-96`**

```
This overwrites an existing group's persisted order with `0` whenever a later save path does not
provide `displayOrder` (for example generation/fetch/patch persistence uses the default
`MediaMessagePersistInput`). That can move an already ordered grouped media cell unexpectedly after
regeneration or local refresh. Preserve the existing group's order when `input.displayOrder` is
null.

-         'display_order': input.displayOrder ?? 0,
+         'display_order':
+             input.displayOrder ?? existingGroup?['display_order'] as int? ?? 0,
```

**7.9  `lib/data/dao/generated_media_dao_impl.dart:1093-1095`**

```
If this file is the selected media message but `latestAttemptId` is missing from `fileItems` (e.g.
attempts are incomplete/filtered), `selectedIndex` remains on the previous/default item. Falling
back to the file's first item keeps the selected media message focused even when attempt data is not
fully available.

-     if (localIndex >= 0) {
-       selectedIndex = baseIndex + localIndex;
-     }
+     selectedIndex = localIndex >= 0 ? baseIndex + localIndex : baseIndex;
```

**7.10  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:960-964`**

```
This identity fallback treats only `null` attempt ids as absent, while the rest of this datasource
normalizes ids with `trim()` and treats empty strings as missing. If one side has `attemptId: ''`
and the other has `null`, otherwise identical single-attempt media items will not be considered the
same here, so `_mergedMediaSelectedIndex` can fail to preserve the local current item and fall back
to the remote index. Normalize both attempt ids before this check.

+     final leftHasAttemptId = leftAttemptId != null && leftAttemptId.isNotEmpty;
+     final rightHasAttemptId = rightAttemptId != null && rightAttemptId.isNotEmpty;
      return leftMediaMessageId != null &&
          leftMediaMessageId.isNotEmpty &&
          leftMediaMessageId == rightMediaMessageId &&
-         left.attemptId == null &&
-         right.attemptId == null;
+         !leftHasAttemptId &&
+         !rightHasAttemptId;
```

**7.11  `lib/data/repositories/impl/chat_repository_impl.dart:1000-1004`**

```
Because this flag is page-wide, the presence of any V2-shaped text message (for example one with
`versions`) makes `_messagesToGroups` skip all generated-media assistant messages and also makes
`_messagePageToGroups` skip merging `response.mediaMessages`. In a mixed response this can drop
legacy/flat media records, which is risky for the requirement that old-version generated media
remain visible after regenerate. Consider deciding per message whether to use the V2 media path, and
still merging `response.mediaMessages` that are not represented by nested `imageGroup`/`videoGroup`.
```

**7.12  `lib/data/repositories/impl/chat_repository_impl.dart:1273-1281`**

```
Group ordering currently ignores `ApiMediaMessage.createdAtUnixMs` and only looks at attempt
timestamps. When a media message has no attempts yet (or attempt timestamps are absent), this
returns null and ordering falls back to the fixed image/video `stableOrder`, which can violate the
“order by group first generation time newest first” requirement. Consider falling back to
`mediaMessage.createdAtUnixMs` when `_firstAttemptCreatedAt` is null.
```

### OCR 轮 8 — L9145（24 files, 6 comments）

**8.1  `lib/data/api/models/generation_models.dart:65-65`**

```
This relies on `NonNullBoolConverter` for the V2 `liked` value, but that converter only treats
boolean `true`, non-zero numeric values, and the literal string `"true"` as true. If the API sends a
string-encoded numeric bool such as `"1"` (covered by the string-or-number bool requirement), this
field will silently decode to `false`, causing liked state to be lost for media messages. Please
extend the converter to handle numeric strings before using it for this response field.
```

**8.2  `lib/data/api/models/generation_models.freezed.dart:386-386`**

```
`NonNullBoolConverter` currently only treats boolean strings equal to `"true"` as true;
string-number booleans such as `"1"` decode to `false`. Since this newly converter-backed `liked`
field is part of the V2 media payload and the requirement calls out string-or-number bools, a server
value like `"1"` would silently drop the liked state for the media cell. Please extend the converter
(and regenerate) to handle numeric strings consistently with numeric JSON values.
```

**8.3  `lib/data/dao/generated_media_dao_impl.dart:706-715`**

```
This ordering does not match the required media-cell ordering. `display_order` is persisted as a
group/kind ordering hint (and defaults to `0` when absent), so sorting by it ascending before time
can put older groups ahead of newer ones. The requirement says cells should be ordered by each
group's first generation time newest-first, falling back to the media message time when attempts are
absent. Consider ordering groups by a computed first-generation timestamp (e.g. min attempt
`created_at`, otherwise file/message `created_at`) in descending order, and only use `display_order`
as a tie-breaker if needed.
```

**8.4  `lib/data/repositories/impl/chat_repository_impl.dart:1076-1087`**

```
Flat page-level media is filtered through the typed `ApiMediaMessage`, but this helper only exposes
`sourceMessageId` and `sourceMessageGroupId`. The raw in-row filter also handles
`sourceVersionMessageId`, and the API model currently does not retain that field; if a mixed V2
response includes the same media both nested and in `mediaMessages` with only
`sourceVersionMessageId`, this filter will treat it as legacy and merge a duplicate media cell.
Consider retaining/checking that key (or filtering page-level media from the raw JSON before typed
conversion).
```

**8.5  `lib/data/repositories/impl/chat_repository_impl.dart:1624-1627`**

```
Dropping nested V2 media when `mediaMessageId` is empty can make an entire image/video group
disappear (`_v2MediaGroupSummary` returns null when all item lists are empty). The requirement calls
for fallback keys for missing `mediaMessageId` (scoped by source/kind); synthesize a stable fallback
id here from source ids/version/kind instead of returning an empty list.
```

**8.6  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:355-357`**

```
This makes the persisted group id depend on the current page shape: if a V2 message is fetched while
it only has an image group, the image is stored under `baseGroupId`; after a later fetch includes
both image and video, the same image group is stored under the kind-scoped id below. The old
`baseGroupId` rows are not removed and `loadMediaSummariesBySourceMessage` loads all non-hidden rows
for the same source message, so the message can regain a stale duplicate media cell after refresh.
Use a stable per-kind group id for V2 regenerated groups regardless of whether the sibling kind is
present, or migrate/clean up the previous base group when switching to kind-scoped ids.
```

### OCR 轮 9 — L9486（25 files, 5 comments）

**9.1  `lib/data/dao/generated_media_dao_impl.dart:709-709`**

```
The group timestamp calculation ignores media messages that have no attempts whenever any other item
in the same group has attempts. `COALESCE(MIN(attempt.created_at), MIN(file.created_at))` falls back
to file `created_at` only when the entire group has no attempts, but the requirement is per media
message: use each media message's first attempt time, falling back to that media message's
`createdAt` when attempts are missing, then sort groups by that effective first time. In mixed
groups this can order image/video cells incorrectly after regenerate.

-     COALESCE(MIN(NULLIF(a2.created_at, '')), MIN(NULLIF(f2.created_at, ''))) AS group_first_generated_at
+     MIN(
+       COALESCE(NULLIF(a2.first_attempt_created_at, ''), NULLIF(f2.created_at, ''))
+     ) AS group_first_generated_at
```

**9.2  `test/data/repositories/chat_repository_mock_api_test.dart:161-161`**

```
This mock repository now sends story-message pagination through `/api/v2/...`, but
`AffinyMockApiInterceptor` used by this test helper only strips `AffinyApiContract.basePath`
(`/api/v1`) before matching paths. As a result, V2 requests are seen as
`/api/v2/public/story/messages:list` and miss the existing `/public/story/messages:list` mock
response, causing a 501 once the repository calls `listStoryMessagesV2`. Please update the mock path
normalization/fixtures to handle the V2 base path before wiring the V2 client here.
```

**9.3  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:453-460`**

```
The persisted snapshots do not carry the V2 media/attempt `createdAtUnixMs`, so the DAO falls back
to `DateTime.now()` per `persistMediaMessageState` call. Because image/video groups are persisted
sequentially, their `created_at` values can reflect write order rather than the required “first
attempt createdAt desc, fallback media message createdAt” order; `displayOrder` will not help when
these fallback timestamps differ. Please propagate the V2 first-generated timestamp into
`MediaMessageSnapshot.createdAt`/attempt timestamps before persisting so local reloads keep the same
cell order.
```

**9.4  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:910-917`**

```
Falling back to a sole `mediaMessageId` match can merge local facts from an old attempt into a
different remote attempt when regenerate reuses the media message id. That can copy an old
`localPath`, liked state, and `localReady` status onto the newly current media. Consider only using
this fallback when the remote item has no attempt identity, or when the candidate's attempt identity
matches/ is also absent.
```

**9.5  `lib/data/repositories/impl/chat_repository_impl.dart:1325-1329`**

```
This summary uses a single `mediaGroupId` for the combined V2 image/video media summary. Because
`generatedMediaCellsFor` later splits cells by kind while preserving this id, both the image cell
and video cell can share the same base identity unless every downstream persistence path adds a kind
suffix. That conflicts with the V2 requirement for stable kind-scoped persistence group ids and can
cause image/video records from the same regenerate group to merge or overwrite each other when the
base id is not recognized by downstream heuristics. Consider emitting kind-scoped group ids at the
point where each V2 media group is represented, or include the media kind in the V2 group id before
it leaves the repository mapping.
```

### OCR 轮 10 — L9972（29 files, 3 comments）

**10.1  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:937-942`**

```
This fallback can still attach stale local facts to a new regenerated item when the remote item has
no attempt identity. In that case a reused `mediaMessageId` is enough to match a single local
candidate, and `_mergeRemoteMediaItemWithLocalFacts` will copy `localPath`, status, `createdAt`, and
liked state from the old attempt. Since V2 regeneration can retain/reuse media message ids while
attempts are the real asset identity, avoid matching by `mediaMessageId` if either side has an
attempt identity mismatch or the remote item lacks an attempt id; otherwise a new/current media can
be shown as the old cached file.

-     if (!remoteHasAttemptIdentity ||
-         candidateAttemptId == null ||
-         candidateAttemptId.isEmpty ||
+     if (!remoteHasAttemptIdentity) {
+       return null;
+     }
+     if (candidateAttemptId != null &&
+         candidateAttemptId.isNotEmpty &&
          candidateAttemptId == attemptId) {
        return candidate;
      }
```

**10.2  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:332-341`**

```
This marks the first item of each kind as selected in addition to the actual `selectedIndex`. For a
V2 `imageGroup` (or `videoGroup`) containing multiple media messages of the same kind, this can
persist a selected row that is not `group.current`; the DAO then stores `selected_media_item_id`
from whichever snapshot is persisted with `selectedInGroup=true`, so local reload may restore the
wrong current item. Selection should be driven only by the current/selected item for each logical
persisted group, not by the first item of the kind.

-     final seenKinds = <StoryMessageMediaKind>{};
-     for (final item in media.displayItems) {
-       if (!seenKinds.add(item.kind)) {
-         continue;
-       }
-       final key = _mediaMessageGroupingKey(media, item);
-       if (key != null) {
-         ids.add(key);
-       }
-     }
+     return Set<String>.unmodifiable(ids);
```

**10.3  `test/data/api/mock/affiny_mock_api_interceptor_test.dart:65-71`**

```
This setup does not actually exercise the interceptor's `/api/v2` path normalization: Retrofit keeps
the request path as `/public/story/messages:list` and stores `/api/v2` in `baseUrl`, while `_path()`
normalizes `options.path`. If the V2 stripping regresses, this test can still pass. To cover the
intended behavior, issue a request whose `options.path` includes
`/api/v2/public/story/messages:list` (for example by using the authority-only base URL and passing
the full V2 path), then assert the fixture is hit.
```

### OCR 轮 11 — L10227（29 files, 10 comments）

**11.1  `lib/data/api/models/story_models.dart:144-147`**

```
`ApiChatMessageVersion.text` is user-visible story content, but the new Freezed DTO will generate a
`toString()` that includes this field; additionally, `ApiChatMessage.toString()` now includes
`versions`, so logging an `ApiChatMessage` can expose all old/regenerated text versions. Since this
file already marks message text as not safe for logs, consider disabling generated `toString` for
this DTO (and for `ApiChatMessage` if messages may be logged) or otherwise excluding version text
from diagnostic output.

- @freezed
+ @Freezed(toStringOverride: false)
  abstract class ApiChatMessageVersion
      with _$ApiChatMessageVersion
      implements ApiModel {
```

**11.2  `lib/domain/usecases/story_chat_usecase_impl.dart:1292-1292`**

```
This makes `selectedInGroup` sticky: if a previously current media item is later returned as
non-current after `group.current` changes, the old item remains selected because
`existing.selectedInGroup` is OR'ed back in. That can produce multiple selected items in a V2 group
and persist the wrong `group.current` selection. Treat the remote/incoming flag as authoritative
when merging the same media item.

-       selectedInGroup: incoming.selectedInGroup || existing.selectedInGroup,
+       selectedInGroup: incoming.selectedInGroup,
```

**11.3  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:369-369`**

```
Appending `sourceAiMessageId` makes the persisted group id change when regenerate creates a new
active text message/version. The requirement says media generated by old and new text versions must
remain in the same image/video group, so this can split one logical image/video group into multiple
persisted groups/cells after the source message changes. Prefer deriving the per-kind group id only
from the server group identity plus kind (and chat/account scoping should be handled by DAO
uniqueness/fallback, not by the source version id).

-     return '${baseGroupId}_${chatId.trim()}_${sourceAiMessageId}_$suffix';
+     return '${baseGroupId}_${chatId.trim()}_$suffix';
```

**11.4  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:1020-1020`**

```
`selectedInGroup` represents the server group.current/current media. OR-ing it with the cached local
value can keep a stale local selection after the server changes current, so multiple media messages
in the same group may be persisted as selected and the final displayed item can depend on
persistence order rather than group.current. Keep the remote selection as authoritative when merging
remote data with local facts.

-       selectedInGroup: remote.selectedInGroup || local.selectedInGroup,
+       selectedInGroup: remote.selectedInGroup,
```

**11.5  `lib/data/dao/generated_media_dao_impl.dart:1032-1035`**

```
This still preserves cached local file metadata whenever the incoming snapshot has no
`latestAttemptId`, even if the server now points the same `mediaMessageId` at a different
`asset_ref`/`remote_url`. In mixed legacy/V2 or incomplete-attempt responses, that can leave
`local_path` and `download_status` attached to a stale media artifact and make the UI render the old
file. Please only keep the local file when the persisted artifact identity also matches (for example
compare non-empty `asset_ref`/`remote_url`, or clear the cache when the incoming asset identity
changed).

      if (normalizedLatestAttemptId == null ||
          normalizedLatestAttemptId.isEmpty) {
-       return true;
+       final existingAssetRef = (existing['asset_ref'] as String?)?.trim();
+       final existingRemoteUrl = (existing['remote_url'] as String?)?.trim();
+       // Keep local facts only after verifying the incoming snapshot still
+       // references the same artifact identity.
+       return false;
      }
```

**11.6  `test/data/repositories/chat_repository_test.dart:1199-1201`**

```
This fixture name is misleading: this test later asserts that this legacy media is preserved and
displayed. Renaming it will make the fallback expectation clearer and reduce the chance of future
test maintenance mistakes.

-                 mediaMessageId: 'legacy_image_should_not_show',
+                 mediaMessageId: 'legacy_image_should_show',
                  sourceMessageId: 'msg_ai',
                  mediaType: 'GENERATION_MEDIA_TYPE_IMAGE',
```

**11.7  `test/data/datasources/affiny_chat_local_data_source_test.dart:1134-1137`**

```
This test name says it verifies the V2 per-kind media group id remains stable, but the assertions
only check the restored display items. A regression that rewrites the existing image group's
`media_group_id` while still returning one image and one video item would still pass. Consider
asserting the rows in `generated_media_messages` (or another observable group identifier) include
the original image group id and the new sibling group id exactly once.

          expect(
            items.where((item) => item.mediaMessageId == 'media_img_1'),
            hasLength(1),
+         );
+         final rows = await _mediaGroupRows(
+           createTestChatLocalFixture().copyWith(local: local),
+           'acct_1',
          );
```

**11.8  `test/data/datasources/affiny_chat_local_data_source_test.dart:1062-1063`**

```
To make the group-id stability assertion possible, this test should use
`createTestChatLocalFixture()` instead of only the datasource so it can inspect the persisted
`generated_media_messages` rows. Without checking the stored group ids, the test can pass even if
the per-kind group id is rewritten while the display items remain correct.

-         final local = createTestChatLocalDataSource();
+         final fixture = createTestChatLocalFixture();
+         final local = fixture.local;
          const imageOnlySummary = GeneratedMediaMessageSummary(
```

**11.9  `lib/data/repositories/impl/chat_repository_impl.dart:0-0`**

```
This assertion only checks that the video row is selected somewhere, so the test would still pass if
the image group were also incorrectly persisted with `selected_media_item_id` (the scenario the test
name says should be excluded). To make this regression test effective, assert the full set of
non-null selected IDs, or explicitly assert that only the video group has a selected item.

          final rows = await _mediaGroupRows(fixture, 'acct_1');
-         final selectedIds = rows.map((row) => row['selected_media_item_id']);
-         expect(selectedIds, contains('media_video_1'));
+         final selectedIds = rows
+             .map((row) => row['selected_media_item_id'])
+             .whereType<String>()
+             .toList(growable: false);
+         expect(selectedIds, <String>['media_video_1']);
```

**11.10  `lib/data/repositories/impl/chat_repository_impl.dart:1529-1530`**

```
The test name says the remote terminal status wins over the cached local path, but the assertion
still requires the stale `localPath` to be present on a failed item. That makes the test codify an
inconsistent state (failed but locally ready file attached) and can mask stale local-file leakage
after regeneration/terminal failure. If terminal remote status is supposed to win, assert that the
cached local path is not exposed for the terminal item.

- status: item.status,
-       localPath: item.localPath,
+       expect(item.status, GeneratedMediaItemSummaryStatus.failed);
+       expect(item.localPath, isNull);
```

### OCR 轮 12 — L10705（29 files, 8 comments）

**12.1  `lib/app/injector/injector.config.dart:566-573`**

```
This generated config dropped the `ChatHistoryController` import/factory even though `RootBinding`
and `ChatHistoryBinding` still call `Injector.provide<ChatHistoryController>()`. Since
`ChatHistoryController` is still annotated with `@injectable`, GetIt will throw at runtime when the
Chats/Home history controller is created. Please regenerate/fix the DI output so the controller
remains registered; otherwise this change alters production route/UI behavior outside the V2 message
adaptation scope.

      gh.factory<_i346.ProfileController>(
        () => _i346.ProfileController(
          gh<_i170.PurchaseEntitlementUseCase>(),
          gh<_i550.PersonaUseCase>(),
          gh<_i147.AuthSessionUseCase>(),
          gh<_i144.UserLibraryUseCase>(),
        ),
+     );
+     gh.factory<_i466.ChatHistoryController>(
+       () => _i466.ChatHistoryController(gh<_i60.ChatHistoryUseCase>()),
      );
```

**12.2  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:896-898`**

```
Appending unmatched local items preserves their old `selectedInGroup` flag. On the next persistence
pass `_selectedMediaMessageIds` treats every `selectedInGroup` item as current, so an old
locally-retained regenerate item can compete with the latest remote `group.current` and, depending
on write order, overwrite `selected_media_item_id` back to the stale media. Clear/recompute
selection on appended local items when the remote payload provides the current item, so remote
current remains authoritative while still retaining old media.
```

**12.3  `lib/domain/usecases/story_chat_usecase_impl.dart:1487-1487`**

```
This drops the media-level timestamp when an attempt has no `createdAt`. The regenerate
ordering/persistence path relies on each media item carrying the first generation time, with a
fallback to the media message/file `createdAt`; leaving this null can make a V2/legacy mixed media
group lose its intended newest-first ordering after mapping through this use case. Please preserve
the fallback here.

-       createdAt: attempt.createdAt,
+       createdAt: attempt.createdAt ?? mediaMessage.createdAt,
```

**12.4  `lib/domain/models/media_models.dart:410-410`**

```
Defaulting this to `true` makes every persist path that does not explicitly carry group-current
information update the group's selected media. For example, fetch/poll/patch flows that construct
`MediaMessagePersistInput(snapshot: ...)` will mark the refreshed media as selected even if V2
`group.current` points to a different media message, which can overwrite the server-selected item
and break the “only group.current is selected” requirement. Consider making the default
non-mutating/`false` (or nullable with DAO preserving existing selection), and pass `true`
explicitly only from creation or selection-aware V2 mapping paths.

-     this.selectedInGroup = true,
+     this.selectedInGroup = false,
```

**12.5  `lib/data/dao/generated_media_dao_impl.dart:1217-1225`**

```
This single `selectedIndex` is shared by the combined summary keyed by `sourceMessageId`, but V2
persists image and video as separate media groups and each group can have its own `current`. When
both image and video groups contain multiple items and the non-first item is current, the later
group processed here overwrites the earlier group's selection. Downstream `generatedMediaCellsFor`
can then apply a non-zero selection to only one kind, so the other cell falls back to item 0 and may
show the wrong current media after loading from local persistence. Consider preserving selection per
group/kind (for example by emitting separate summaries per media group or carrying `selectedInGroup`
through the DAO summary items and deriving each cell's selected index from that).
```

**12.6  `lib/data/repositories/impl/chat_repository_impl.dart:1313-1329`**

```
This collapses `imageGroup` and `videoGroup` into a single `GeneratedMediaMessageSummary` by
concatenating their items and using one `mediaGroupId`. The V2 requirement is to render one image
cell and one video cell independently, ordered newest-first between those cells. With a single
summary, mixed image/video items share one cell/selection and one persisted identity; it also does
not match the DAO's V2 persistence-group convention that expects per-kind ids ending in
`_image`/`_video`, so local facts can be reused incorrectly or not reused across regenerations.
Please preserve per-kind summaries/cells (e.g. create/merge separate summaries with stable
`media_group_<versionGroupId>_<kind>` ids and attach/render them as separate media cells in the
existing message model flow).
```

**12.7  `lib/data/repositories/impl/chat_repository_impl.dart:1408-1419`**

```
The ordering timestamp for each mediaMessage is computed as the minimum over all attempts. The
requirement calls for `attempts[0].createdAtUnixMs` as the first-generation time, then fallback to
the media message/file createdAt. If the server returns attempts in attempt order but a later retry
has an older/missing timestamp (or if only the first attempt should define group recency), taking
the minimum can reorder image/video cells incorrectly. Consider using the first attempt's timestamp
directly, then falling back to `mediaMessage.createdAtUnixMs` (and any available file/artifact
createdAt if the model exposes it).

    int? _firstGenerationCreatedAt(ApiMediaMessage message) {
-     final firstAttemptCreatedAt = message.attempts
-         .map((attempt) => int.tryParse(attempt.createdAtUnixMs))
-         .whereType<int>()
-         .fold<int?>(null, (previous, value) {
-           if (previous == null || value < previous) {
-             return value;
-           }
-           return previous;
-         });
+     final firstAttemptCreatedAt = message.attempts.isEmpty
+         ? null
+         : int.tryParse(message.attempts.first.createdAtUnixMs);
      return firstAttemptCreatedAt ?? int.tryParse(message.createdAtUnixMs);
    }
```

**12.8  `test/data/repositories/chat_repository_test.dart:1166-1171`**

```
This case is intended to validate handling when a V2 nested media message has no `mediaMessageId`,
but it only checks that the fallback id is present. Because the group contains a single image item,
selection can still pass via the generic fallback path even if `group.current` is not matched by
`sourceMessageId`/`sourceTextVersionNo`. Please add a second image media message and assert the
intended fallback item is `selectedInGroup` (and/or its `mediaItemId` is first/current) so
regressions in current-media selection are caught.
```

### OCR 轮 13 — L10954（30 files, 9 comments）

**13.1  `lib/data/repositories/impl/generation_repository_impl.dart:59-59`**

```
`mergeRemoteMediaPatch` does not appear to receive or validate the V2 `group.current` pointer; it
persists each media patch as selected. Because `persistMediaMessageState` overwrites
`selected_media_item_id` when `selectedInGroup` is true, a non-current/old-version media patch can
replace the locally selected group item just based on patch arrival order. This violates the
requirement that only `group.current` marks the current media. Keep remote patch persistence
non-mutating unless the patch explicitly carries an authoritative current selection.
```

**13.2  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:446-452`**

```
Reordering the attempts before persistence can change which row is considered the first attempt
later. The DAO derives group first-generation time from the persisted attempts ordered by
`attempt_no`, and `_attemptOrder` falls back to the list index when the attempt id does not encode
an order. If the current attempt is moved to index 0, a regenerated/current attempt can become the
persisted `attempts[0]`, breaking the required image/video ordering based on the original first
generation time. Keep the attempt list in source order and rely on `latestAttempt`/selected metadata
to mark the current item.

-     final attempts = _currentFirstAttemptSnapshots(
-       latestItem,
-       items
+     final attempts = items
            .map((item) => _attemptSnapshotFromSummaryItem(item, mediaMessageId))
            .whereType<MediaAttemptSnapshot>()
-           .toList(growable: false),
-     );
+         .toList(growable: false);
```

**13.3  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:929-935`**

```
Matching local facts by `attemptId` alone can copy `localPath`, `liked`, `createdAt`, or status from
another media message if attempt ids are only unique within a media message/group (or collide
between image/video regenerate groups). Please include the media message id and/or kind in this
match before accepting the local item, or avoid the attempt-only lookup when those identities
disagree.

      final attemptId = remoteItem.attemptId?.trim();
+     final mediaMessageId = remoteItem.mediaMessageId?.trim();
      if (attemptId != null && attemptId.isNotEmpty) {
        final local = localByAttemptId[attemptId];
-       if (local != null) {
+       final localMediaMessageId = local?.mediaMessageId?.trim();
+       if (local != null &&
+           local.kind == remoteItem.kind &&
+           (mediaMessageId == null ||
+               mediaMessageId.isEmpty ||
+               localMediaMessageId == mediaMessageId)) {
          return local;
        }
      }
```

**13.4  `lib/data/api/app_api_methods_v2.dart:17-21`**

```
Reordering the persisted attempt list makes the selected/current attempt become index 0 when attempt
IDs do not encode an order. The DAO derives `attempt_no` from this list order as a fallback and then
uses the first attempt's `created_at` for media group ordering, so a regenerated current attempt can
replace the true first-generation timestamp and break the required newest-first ordering between
image/video cells. Keep `latestAttempt` as the current attempt, but persist `attempts` in their
original/API order.

- @GET('/public/story/messages:list')
- Future<StoryMessagePage> listStoryMessages(
-   @Header('X-Request-Id') String requestId,
-   @Queries() Map<String, dynamic> query,
- );
+     final attempts = items
+         .map((item) => _attemptSnapshotFromSummaryItem(item, mediaMessageId))
+         .whereType<MediaAttemptSnapshot>()
+         .toList(growable: false);
```

**13.5  `lib/domain/usecases/story_chat_usecase_impl.dart:1292-1292`**

```
This reorders the persisted attempt list so the selected/current attempt becomes index 0. The DAO
writes attempts using the list index as the fallback `attempt_no` when the attempt id has no numeric
suffix, and later calculates the group's first-generation time from the row with the smallest
`attempt_no`. In that case, persisting the current attempt first can make a regenerated/current
attempt look like `attempts[0]`, breaking the required newest-first ordering based on the original
first attempt. Keep the attempts in their API/original order and use
`latestAttempt`/`latestAttemptId` (or reconstruction-time ordering) to represent the current display
item instead.

- selectedInGroup: incoming.selectedInGroup,
+     final attempts = items
+         .map((item) => _attemptSnapshotFromSummaryItem(item, mediaMessageId))
+         .whereType<MediaAttemptSnapshot>()
+         .toList(growable: false);
```

**13.6  `test/data/datasources/affiny_chat_local_data_source_test.dart:1226-1242`**

```
This test is intended to guard ordering by the first generation time instead of a later retry, but
the synthetic retry is older than the first attempt. An implementation that incorrectly sorts by
`MIN(created_at)` or by the latest attempt's timestamp could still pass. Make the second attempt
newer than the video timestamp so using attempt #2 would visibly change the expected order, while
using attempt #1 keeps the test passing.

            await db.insert('generated_media_attempts', <String, Object?>{
              'account_id': 'acct_1',
              'attempt_id': 'img_attempt_2',
              'media_item_id': 'media_img_1',
              'media_message_id': 'media_img_1',
              'attempt_no': 2,
              'media_kind': GeneratedMediaKind.image.wireName,
              'status': MediaAttemptStatus.succeeded.wireName,
              'asset_ref': null,
              'remote_url': 'https://cdn.example.com/img_retry.png',
              'thumbnail_ref': null,
              'error_json': null,
              'created_at': DateTime.parse(
-               '2026-06-16T23:59:59Z',
+               '2026-06-17T00:00:02Z',
              ).toIso8601String(),
-             'updated_at': older.toIso8601String(),
+             'updated_at': DateTime.parse(
+               '2026-06-17T00:00:02Z',
+             ).toIso8601String(),
            });
```

**13.7  `test/data/repositories/chat_repository_test.dart:944-956`**

```
This test does not actually make the group ordering depend on `media_img_from_v2`'s `attempts[0]`:
the image group still contains `media_img_from_v1` with first-attempt time `1782360020000`, so the
group remains older than the video group (`1782360040000`) even if the implementation ignores this
modified V2 attempt. Consider making all image media first attempts newer than the video group's
first attempt while their later/current attempt is older, then assert the image cell comes first;
that would catch sorting by latest/current/list order instead of `attempts[0]`.

+         final imageV1 = imageMessages.singleWhere(
+           (message) => message['mediaMessageId'] == 'media_img_from_v1',
+         );
+         imageV1['attempts'] = <Map<String, Object?>>[
+           _attemptJson(
+             attemptId: 'img_attempt_v1_1',
+             state: 'GENERATION_ATTEMPT_STATE_COMPLETED',
+             createdAtUnixMs: '1782360060000',
+             url: 'https://cdn.example.com/generated/img_v1_1.jpg',
+           ),
+         ];
          imageV2['attempts'] = <Map<String, Object?>>[
            _attemptJson(
              attemptId: 'img_attempt_v2_1',
              state: 'GENERATION_ATTEMPT_STATE_GENERATING',
-             createdAtUnixMs: '1782360030000',
+             createdAtUnixMs: '1782360070000',
            ),
            _attemptJson(
              attemptId: 'img_attempt_v2_2',
              state: 'GENERATION_ATTEMPT_STATE_COMPLETED',
              createdAtUnixMs: '1782360001000',
              url: 'https://cdn.example.com/generated/img_v2_2.jpg',
            ),
          ];
```

**13.8  `lib/data/dao/generated_media_dao_impl.dart:737-740`**

```
This query now relies on SQLite window functions (`ROW_NUMBER() OVER ...`). With `minSdkVersion 24`,
some supported Android devices ship SQLite versions older than 3.25, where window functions are not
available, so loading generated media summaries can fail at runtime. Consider rewriting the “first
attempt per media” subquery using a correlated `MIN(...)`/join or another SQLite-compatible pattern
supported by the app's minimum Android version.
```

**13.9  `lib/data/repositories/impl/chat_repository_impl.dart:132-135`**

```
For V2 message pages, user messages commonly carry `createdAtUnixMs`, but `_userMessageFromJson`
only reads `createdAt` / `created_at` and otherwise fills `DateTime.now()`. Because this new
fallback uses `latestUser.createdAt`, a chat whose latest row is a user message can get a synthetic
current timestamp instead of the server timestamp. Please make the user-message mapping consume
`createdAtUnixMs` (or derive the fallback from the raw V2 timestamp) before relying on
`latestUser.createdAt` here.
```

### OCR 轮 14 — L11177（30 files, 6 comments）

**14.1  `lib/data/api/models/story_models.dart:169-172`**

```
`ApiMediaGroup` is a newly introduced DTO that can contain nested `ApiMediaMessage` data (including
media URLs/metadata). Unlike `ApiChatMessage`, it still uses the default Freezed `toString`, so any
accidental log/string interpolation of `imageGroup`/`videoGroup` can expose that nested media
payload. Please disable generated `toString` for the media group DTOs as well to keep the same
redaction behavior as the parent message DTO.

- @freezed
+ @Freezed(toStringOverride: false)
  abstract class ApiMediaGroupCurrent
      with _$ApiMediaGroupCurrent
      implements ApiModel {
```

**14.2  `lib/data/api/models/story_models.dart:190-191`**

```
`ApiMediaGroup` is a newly introduced DTO that can contain nested `ApiMediaMessage` data (including
media URLs/metadata). Unlike `ApiChatMessage`, it still uses the default Freezed `toString`, so any
accidental log/string interpolation of `imageGroup`/`videoGroup` can expose that nested media
payload. Please disable generated `toString` for the media group DTOs as well to keep the same
redaction behavior as the parent message DTO.

- @freezed
+ @Freezed(toStringOverride: false)
  abstract class ApiMediaGroup with _$ApiMediaGroup implements ApiModel {
```

**14.3  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:971-975`**

```
This treats `attemptId` alone as a complete identity when calculating the merged selected index. In
the V2 grouped shape, the same summary can contain image/video groups and multiple media messages;
unless `attemptId` is guaranteed globally unique, a collision can make a local selection match the
wrong remote item and override `remote.selectedIndex`. Please include at least `kind` and, when
present, `mediaMessageId` in this match, similar to `_matchingLocalMediaItem` above.

      if (leftAttemptId != null &&
          leftAttemptId.isNotEmpty &&
-         leftAttemptId == rightAttemptId) {
+         leftAttemptId == rightAttemptId &&
+         left.kind == right.kind) {
+       final leftMediaMessageId = left.mediaMessageId?.trim();
+       final rightMediaMessageId = right.mediaMessageId?.trim();
+       if (leftMediaMessageId == null ||
+           leftMediaMessageId.isEmpty ||
+           rightMediaMessageId == null ||
+           rightMediaMessageId.isEmpty ||
+           leftMediaMessageId == rightMediaMessageId) {
        return true;
+       }
      }
```

**14.4  `lib/data/dao/generated_media_dao_impl.dart:953-958`**

```
This reorders persisted attempts by moving `latest_attempt_id` to the front of `displayItems`. The
summary already carries `selectedIndex` via `addMediaFile`, so changing the list order can alter
carousel/order behavior and violates the V2 requirement to preserve server/persistence attempt
order. Keep the query order (`attempt_no ASC, created_at ASC`) and rely on
`selectedIndex`/`selectedInGroup` to indicate the current item.

      return attemptItems.isEmpty
          ? <GeneratedMediaItemSummary>[_summaryItem(fileRow)]
-         : _currentFirstSummaryItems(
-             attemptItems,
-             fileRow['latest_attempt_id'] as String?,
-           );
+         : attemptItems;
```

**14.5  `test/data/repositories/chat_repository_test.dart:925-925`**

```
This assertion does not actually distinguish the required “first attempt createdAtUnixMs” ordering
from an implementation that incorrectly sorts by the newest/current attempt: in this fixture both
strategies still put the image group first. To make the regression test meaningful, set the image
group's first attempt older than the video group's first attempt while a later image attempt is
newer, and assert the video group remains first (or otherwise assert the exact expected media
id/order).
```

**14.6  `test/data/datasources/affiny_chat_local_data_source_test.dart:1226-1244`**

```
This manually adds a second attempt but leaves `generated_media_files.latest_attempt_id` pointing at
the original attempt created by `mergeFetchedMessagePage`. That makes the fixture inconsistent with
a real regenerated/current item state, and the assertions below only check `mediaMessageId`, so a
regression that restores the old attempt as the displayed/current image would still pass. Please
either update the file row's `latest_attempt_id` to `img_attempt_2` (if this retry should be
current) and assert the restored `attemptId`, or avoid inserting a synthetic current attempt in this
ordering-only test.

            await db.insert('generated_media_attempts', <String, Object?>{
              'account_id': 'acct_1',
              'attempt_id': 'img_attempt_2',
              'media_item_id': 'media_img_1',
              'media_message_id': 'media_img_1',
              'attempt_no': 2,
              'media_kind': GeneratedMediaKind.image.wireName,
              'status': MediaAttemptStatus.succeeded.wireName,
              'asset_ref': null,
              'remote_url': 'https://cdn.example.com/img_retry.png',
              'thumbnail_ref': null,
              'error_json': null,
              'created_at': DateTime.parse(
                '2026-06-17T00:00:02Z',
              ).toIso8601String(),
              'updated_at': DateTime.parse(
                '2026-06-17T00:00:02Z',
              ).toIso8601String(),
            });
+           await db.update(
+             'generated_media_files',
+             <String, Object?>{'latest_attempt_id': 'img_attempt_2'},
+             where: 'account_id = ? AND media_message_id = ?',
+             whereArgs: <Object?>['acct_1', 'media_img_1'],
+           );
```

### OCR 轮 15 — L11661（32 files, 6 comments）

**15.1  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:334-343`**

```
When the payload already provides `selectedInGroup`, it should be authoritative for V2
`group.current`. Adding the legacy `selectedIndex` item as an extra selected media message can make
two media messages in the same persisted image/video group selected; because the DAO stores one
`selected_media_item_id` per group, the later snapshot may overwrite the API current selection and
restore the wrong cell item. Keep the `selectedIndex` fallback only for summaries that have no
`selectedInGroup` flags.

      if (ids.isNotEmpty) {
-       final selected = _selectedItem(media);
-       final selectedKey = selected == null
-           ? null
-           : _mediaMessageGroupingKey(media, selected);
-       if (selectedKey != null) {
-         ids.add(selectedKey);
-       }
        return Set<String>.unmodifiable(ids);
      }
```

**15.2  `lib/data/repositories/impl/chat_repository_impl.dart:1408-1413`**

```
This fallback changes the required ordering semantics: media message `createdAtUnixMs` should only
be used when the media message has no attempts. With the current code, a media item whose first
attempt exists but has an empty/unparseable `createdAtUnixMs` will be ordered by the media-message
timestamp instead, which can move the image/video cells relative to groups whose ordering should be
based strictly on `attempts[0]`. Please distinguish the “attempts absent” case from the “attempt
timestamp invalid” case and return `null` (or log/fallback to stable order) when attempts are
present but the first attempt timestamp cannot be parsed.

    int? _firstGenerationCreatedAt(ApiMediaMessage message) {
-     final firstAttemptCreatedAt = message.attempts.isEmpty
-         ? null
-         : int.tryParse(message.attempts.first.createdAtUnixMs);
-     return firstAttemptCreatedAt ?? int.tryParse(message.createdAtUnixMs);
+     if (message.attempts.isEmpty) {
+       return int.tryParse(message.createdAtUnixMs);
+     }
+     return int.tryParse(message.attempts.first.createdAtUnixMs);
    }
```

**15.3  `lib/data/repositories/impl/generation_repository_impl.dart:59-59`**

```
This marks the new locally-created media message as the selected item for the resolved persistence
group, but this call does not provide a kind-specific `mediaGroupId`. In the current DAO path,
`_resolveGroupId` can reuse an existing group by `sourceMessageId`, and the group has a single
`selected_media_item_id`; creating an image after a video (or vice versa) can therefore overwrite
the other kind's selected/current item on restore. That conflicts with the V2 requirement that image
and video currents can both be honored independently. Please persist local creates into a
kind-specific group or make selection storage kind-aware before setting this to true.
```

**15.4  `lib/data/repositories/impl/generation_repository_impl.dart:59-59`**

```
Same selection-overwrite risk here: when the response creates/replaces a media message but no
kind-specific `mediaGroupId` is supplied, `selectedInGroup: true` can replace the selected item for
the whole source-message group and lose the current selection for the other media kind. This should
only be set after ensuring the persisted group is separated by media kind (or selection is tracked
per kind).
```

**15.5  `lib/domain/usecases/story_chat_usecase_impl.dart:1292-1292`**

```
This merge path is also used when attaching/updating generation snapshots, but
`_generatedMediaItemFromAttempt` does not populate `selectedInGroup` (it defaults to `false`). A
later snapshot for an item that was already marked as the group current can therefore clear the
flag, so the split UI helper may fall back to index 0 and show the wrong image/video current. Since
these snapshots do not carry V2 group-current semantics, preserve an existing selection unless the
incoming item explicitly selects itself.

-       selectedInGroup: incoming.selectedInGroup,
+       selectedInGroup: existing.selectedInGroup || incoming.selectedInGroup,
```

**15.6  `lib/data/dao/generated_media_dao_impl.dart:716-719`**

```
For V2 regenerate groups, `_resolveGroupId` can intentionally reuse the same `media_group_id` across
different source text versions, while each `generated_media_files` row keeps the source id it was
originally persisted with. This query still exposes `f.source_ai_message_id` via `f.*`, and the
loader below groups summaries by `row['source_ai_message_id']`, so old-version media in the same
reused media group can be split under their old text message instead of being aggregated under the
current group/source. Select the group-level source id from `generated_media_messages` and use that
for summary grouping so replaced text versions do not produce separate media bubbles.

  SELECT f.*,
+   m.source_ai_message_id AS group_source_ai_message_id,
    m.selected_media_item_id AS selected_media_item_id,
    gt.group_first_generated_at AS group_first_generated_at,
    m.display_order AS group_display_order
```

### OCR 轮 16 — L12016（33 files, 4 comments）

**16.1  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:904-909`**

```
This item-id fast path bypasses the kind/mediaMessageId compatibility checks used by the attempt-id
path and `_sameMediaItemIdentity`. In V2 regenerated image/video groups, reusing or colliding
item/attempt ids across media messages can merge local facts (localPath, liked, status, attemptId)
into the wrong media item. Please guard this match with `_hasCompatibleMediaIdentity(local,
remoteItem)` before returning it, consistent with the intended scoped identity matching.

      if (itemId.isNotEmpty) {
        final local = localByItemId[itemId];
-       if (local != null) {
+       if (local != null && _hasCompatibleMediaIdentity(local, remoteItem)) {
          return local;
        }
      }
```

**16.2  `lib/ui/pages/character_chat/character_chat_media_cell.dart:57-57`**

```
This match path bypasses the kind/mediaMessageId compatibility checks used by the attempt-id path
below. If a regenerated V2 image/video item reuses or collides on `mediaItemId`, local facts such as
`localPath`, `liked`, and status can be merged into the wrong media message/kind. Please guard the
item-id match with the same compatibility rule before returning it.

- return cells.map(_cellWithSelectedInGroup).toList(growable: false);
+     if (itemId.isNotEmpty) {
+       final local = localByItemId[itemId];
+       if (local != null && _hasCompatibleMediaIdentity(local, remoteItem)) {
+         return local;
+       }
+     }
```

**16.3  `lib/data/repositories/impl/chat_repository_impl.dart:1388-1396`**

```
This uses the oldest first-attempt timestamp in the group. Since the cell order is sorted
newest-first, a group that contains preserved old media plus newly regenerated media can be
positioned by the old item instead of the newest media in that image/video group. Consider using the
latest first-attempt timestamp across the group's mediaMessages (while still only falling back to
mediaMessage.createdAt when attempts are absent) for the aggregate cell ordering key.

      final firstGeneratedAt = mediaMessages
          .map(_firstGenerationCreatedAt)
          .whereType<int>()
          .fold<int?>(null, (previous, value) {
-           if (previous == null || value < previous) {
+           if (previous == null || value > previous) {
              return value;
            }
            return previous;
          });
```

**16.4  `lib/data/repositories/impl/chat_repository_impl.dart:1236-1237`**

```
When a current V2 text version is present but its createdAtUnixMs is empty/missing, this overwrites
the top-level message timestamp with an empty value; _aiMessageFromJson then falls back to
DateTime.now(), changing history ordering/resume timestamps. Preserve the top-level createdAt value
when the active version does not provide one.

-             'createdAt': activeVersion.createdAtUnixMs,
-             'createdAtUnixMs': activeVersion.createdAtUnixMs,
+             'createdAt':
+                 _nonEmptyString(activeVersion.createdAtUnixMs) ??
+                 item['createdAtUnixMs'] ??
+                 item['createdAt'],
+             'createdAtUnixMs':
+                 _nonEmptyString(activeVersion.createdAtUnixMs) ??
+                 item['createdAtUnixMs'],
```

### OCR 轮 17 — L12277（33 files, 7 comments）

**17.1  `lib/data/dao/generated_media_dao_impl.dart:172-172`**

```
This changes missing attempt timestamps into the current persistence time. The V2 ordering contract
says group order must use `attempts[0].createdAtUnixMs`, and only fall back to the media message
`createdAt` when the media message has no attempts. If an attempt exists but its timestamp is
absent, writing `now` makes that group look newly generated and can move old regenerated media to
the top. Consider preserving an empty/null-equivalent value for missing attempt timestamps (and make
the summary-order SQL distinguish “no attempt row” from “attempt row with no valid timestamp”)
instead of substituting the write time.
```

**17.2  `lib/data/dao/generated_media_dao_impl.dart:728-728`**

```
This falls back to `f2.created_at` whenever the first attempt row has a null/empty timestamp. Per
the V2 contract, the media message `createdAt` fallback should be used only when the media message
has no attempts at all; if an attempt exists but lacks a valid first-attempt timestamp, using the
file timestamp can incorrectly order the cell by a later regenerated/persisted time. The subquery
should preserve whether an attempt row exists and only apply the file-created fallback in that
no-attempt case.
```

**17.3  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:454-457`**

```
For V2 groups the repository moves `group.current` to the front of `displayItems` for UI selection.
Persisting attempts in that same order can make the DAO assign fallback attempt_no=0 to the
current/regenerated attempt, and its `group_first_generated_at` query then uses the latest
regenerated time instead of the original first-attempt time. This violates the required image/video
cell ordering by original generation time. Build the persisted attempts in original
chronological/attempt order (e.g. earliest non-null `createdAt` first, with stable fallback) while
keeping `latestAttempt` driven by the selected/current item.

      final attempts = items
          .map((item) => _attemptSnapshotFromSummaryItem(item, mediaMessageId))
          .whereType<MediaAttemptSnapshot>()
-         .toList(growable: false);
+         .toList(growable: false)
+       ..sort((left, right) {
+         final leftCreatedAt = left.createdAt;
+         final rightCreatedAt = right.createdAt;
+         if (leftCreatedAt != null && rightCreatedAt != null) {
+           return leftCreatedAt.compareTo(rightCreatedAt);
+         }
+         if (leftCreatedAt != null) {
+           return -1;
+         }
+         if (rightCreatedAt != null) {
+           return 1;
+         }
+         return 0;
+       });
```

**17.4  `lib/domain/usecases/story_chat_usecase_impl.dart:1292-1292`**

```
This merge can keep a stale selected item selected when a V2 group’s `current` changes. If the
existing item was previously selected and the incoming summary explicitly marks it as unselected
while another item is selected, `||` leaves both items with `selectedInGroup == true`; the UI then
picks the first selected item and may display the old media instead of `group.current`. Prefer
letting the incoming flag override when merging an incoming group snapshot, while polling updates
already preserve the current flag in the constructed incoming item.

-       selectedInGroup: existing.selectedInGroup || incoming.selectedInGroup,
+       selectedInGroup: incoming.selectedInGroup,
```

**17.5  `test/ui/pages/character_chat/character_chat_media_cell_test.dart:104-111`**

```
This test is meant to verify independent per-kind selection, but both the image and video selected
items end up at local index `1`. An implementation that incorrectly reuses one selected index for
every split cell would still pass. Use different local selected positions (for example image index
`0`, video index `1`) so the test can catch cross-kind selection mapping regressions.

          GeneratedMediaItemSummary(
            mediaItemId: 'image_2',
            kind: StoryMessageMediaKind.image,
            status: GeneratedMediaItemSummaryStatus.completed,
            canRegenerate: false,
            canCancel: false,
-           selectedInGroup: true,
          ),
```

**17.6  `lib/data/repositories/impl/chat_repository_impl.dart:1417-1422`**

```
Using `now` when an attempt has no `createdAt` makes a missing V2 first-attempt timestamp look like
a valid generation time. Since `loadMediaSummariesBySourceMessage` orders groups from attempt
`created_at`, this can order old/regenerated media by local refresh time instead of the group's
original first generated time. Preserve the absence (for example as an empty string, since the
column is `TEXT NOT NULL`) and let the summary query fall back to the media message time only when
there are no attempt rows for that media message.

- int? _firstGenerationCreatedAt(ApiMediaMessage message) {
-     if (message.attempts.isEmpty) {
-       return int.tryParse(message.createdAtUnixMs);
-     }
-     return int.tryParse(message.attempts.first.createdAtUnixMs);
-   }
+           'created_at': attempt.createdAt?.toUtc().toIso8601String() ?? '',
```

**17.7  `test/data/datasources/affiny_chat_local_data_source_test.dart:1457-1458`**

```
This collision coverage only varies `mediaMessageId`/kind while keeping distinct `attemptId`s. The
persistence layer also keys/restores attempts by `attemptId`, so a reused attempt id across
different media messages could still overwrite or merge the wrong local facts without this test
failing. Please add a case where two different media messages/kinds reuse the same `attemptId` and
assert both restored items keep separate status/localPath/liked state.
```

### OCR 轮 18 — L12738（34 files, 8 comments）

**18.1  `lib/domain/usecases/story_chat_usecase_impl.dart:1489-1489`**

```
This falls back to the media message timestamp even when an attempt row exists but its created time
is missing. The V2 ordering rule requires fallback to `mediaMessage.createdAt` only when there are
no attempts; an existing attempt with no valid created time must remain missing so it doesn't
reorder the group by the message time.

-       createdAt: attempt.createdAt ?? mediaMessage.createdAt,
+       createdAt: attempt.createdAt,
```

**18.2  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:454-461`**

```
This reorders attempts by timestamp before persistence. The V2 contract relies on preserving the
incoming/DAO attempt order because later logic treats the first attempt as the group's original
generation time, and timestamp-less attempts must remain in their original position rather than
being moved after dated attempts. Sorting here can make a later regenerated attempt become
`attempts[0]` and produce incorrect image/video cell ordering. Please keep the item order provided
by the API/DAO and avoid timestamp sorting at this layer.

-     final attempts =
-         items
-             .map(
-               (item) => _attemptSnapshotFromSummaryItem(item, mediaMessageId),
-             )
+     final attempts = items
+         .map((item) => _attemptSnapshotFromSummaryItem(item, mediaMessageId))
              .whereType<MediaAttemptSnapshot>()
-             .toList(growable: false)
-           ..sort(_compareAttemptSnapshotByCreatedAt);
+         .toList(growable: false);
```

**18.3  `lib/data/dao/generated_media_dao_impl.dart:1081-1092`**

```
The storage/display invariant is tied to the owning `mediaMessageId` passed to DAO calls: rows are
queried by `media_message_id`, and `_displayAttemptId(mediaMessageId, attemptId)` only strips that
same prefix. Using `attempt.mediaMessageId` here can store an attempt as
`otherMediaMessageId::attemptId` while the row still belongs to `mediaMessageId`, so restored
domain/UI `attemptId` may leak the prefixed storage id and selected-attempt matching can fail.
Prefix with the DAO media message id consistently.

    String _storageAttemptId(
      String mediaMessageId,
      MediaAttemptSnapshot attempt,
    ) {
      final normalizedAttemptId = attempt.attemptId.trim();
-     final normalizedMediaMessageId = (attempt.mediaMessageId ?? mediaMessageId)
-         .trim();
+     final normalizedMediaMessageId = mediaMessageId.trim();
      if (normalizedMediaMessageId.isEmpty) {
        return normalizedAttemptId;
      }
      return '$normalizedMediaMessageId::$normalizedAttemptId';
    }
```

**18.4  `lib/data/repositories/impl/chat_repository_impl.dart:1005-1006`**

```
This deduplicates flat `mediaMessages` by source IDs collected from any nested V2 media group. If
the V2 payload contains only one nested kind (or the nested group is partial) while another
old-version image/video is still present only in the flat `mediaMessages` list, the flat item shares
`messageId`/`versionGroupId`/version IDs and will be dropped here, making valid old-version media
disappear. Please dedupe against the actual nested media message identity (for example
`mediaMessageId` plus kind, with source IDs only as a fallback when the nested media message itself
is present) instead of suppressing every flat item from the same source text group.
```

**18.5  `test/data/datasources/affiny_chat_local_data_source_test.dart:1267-1274`**

```
This selection of the group's original generation time can pick the wrong attempt when the server's
`attempts[0]` is not the row with the smallest parsed `attempt_no`. `_attemptOrder` derives
`attempt_no` from the attempt id suffix, so ids like `attempt_2`, `attempt_1` would make this query
use `attempt_1.created_at`, violating the V2 contract to use the first attempt in the API list and
only fall back when no attempt rows exist. Persist the input list index as `attempt_no` (or add a
separate original index) and order by that here, rather than by a parsed id-derived value.

- expect(
-   media.displayItems.map((item) => item.kind),
-   <StoryMessageMediaKind>[
-     StoryMessageMediaKind.video,
-     StoryMessageMediaKind.image,
-     StoryMessageMediaKind.image,
-   ],
- );
+ 	      SELECT gb.rowid
+ 	      FROM generated_media_attempts gb
+ 	      WHERE gb.account_id = ga.account_id
+ 	        AND gb.media_message_id = ga.media_message_id
+ 	      ORDER BY gb.attempt_no ASC
+ 	      LIMIT 1
```

**18.6  `test/data/datasources/affiny_chat_local_data_source_test.dart:0-0`**

```
This log runs for every restored attempt while loading chat media summaries, which is a hot path and
can emit one line per media attempt on normal rendering. That risks noisy production logs and
unnecessary overhead without changing behavior; please remove it or guard/demote it behind an
explicit debug-only diagnostic path.
```

**18.7  `test/domain/usecases/story_chat_usecase_test.dart:0-0`**

```
The storage key is required to be `mediaMessageId::attemptId`, but this uses
`attempt.mediaMessageId` when present. If a snapshot carries a mismatched/stale mediaMessageId, the
row is still written with the current `media_message_id` while the key is prefixed with a different
id, so `_displayAttemptId(currentMediaMessageId, attemptId)` will not strip the prefix and the
domain/UI can receive `otherMediaMessageId::serverAttemptId` instead of the original server attempt
id. It also bypasses the cleanup predicate that keeps only `$mediaMessageId::%` rows. Use the DAO
method's mediaMessageId parameter as the canonical prefix.

-     final normalizedMediaMessageId = (attempt.mediaMessageId ?? mediaMessageId)
-         .trim();
+     final normalizedMediaMessageId = mediaMessageId.trim();
```

**18.8  `test/domain/usecases/story_chat_usecase_test.dart:0-0`**

```
For missing attempt timestamps this falls back to the client write time, which makes an attempt row
look like it has a valid generation time. The V2 ordering rule says missing attempt timestamps must
be stored/ordered as missing and must not fall back to media message/latest regeneration time;
otherwise a cell can be ordered by a regenerate/write time. Store an empty value when
`attempt.createdAt` is absent, as done in `persistMediaMessageState`.

-         'created_at': attempt.createdAt?.toUtc().toIso8601String() ?? now,
+         'created_at': attempt.createdAt?.toUtc().toIso8601String() ?? '',
```

### OCR 轮 19 — L13075（34 files, 6 comments）

**19.1  `lib/data/dao/generated_media_dao_impl.dart:761-765`**

```
The group ordering treats any non-empty `generated_media_attempts.created_at` as a valid timestamp.
The golden path requires using the earliest *valid* first-attempt time and ignoring attempt rows
with missing/invalid created time without falling back to the media message time. With the current
`NULLIF(created_at, '')`, a malformed non-empty value can become `group_first_generated_at` and then
be ordered lexicographically, which can move image/video cells incorrectly. Consider validating the
timestamp before it participates in `MIN`/`ORDER BY` (or compute the group time in Dart with
`DateTime.tryParse`, only falling back to `f2.created_at` when no attempt row exists at all).

  		    SELECT account_id,
  		      media_message_id,
  		      1 AS has_attempt_row,
- 		      NULLIF(created_at, '') AS first_attempt_created_at
+ 		      CASE
+ 		        WHEN datetime(created_at) IS NOT NULL THEN created_at
+ 		        ELSE NULL
+ 		      END AS first_attempt_created_at
  		    FROM generated_media_attempts ga
```

**19.2  `test/data/repositories/chat_repository_test.dart:1219-1222`**

```
This assertion does not exercise the duplicate filtering path: the fixture never creates a media
item with mediaMessageId `legacy_duplicate_should_not_show` (the injected flat media has an empty
`mediaMessageId`), so the test would pass even if that flat duplicate is incorrectly retained.
Please assert against an identifier that the mapper would actually expose for this fixture (for
example the duplicate attempt id/URL, generated fallback id, or the expected display item count) so
the regression is caught.
```

**19.3  `lib/data/repositories/impl/generation_repository_impl.dart:57-60`**

```
This group id is derived from the action `sourceMessageId`, which for V2 story messages is the
active/current text message id. Remote V2 media groups are persisted using the stable version group
id (and chat/kind), so a regenerate/create result saved here can land in
`media_group_<currentMessageId>_<kind>` instead of the existing V2 `imageGroup`/`videoGroup`. That
splits the media into a separate local cell and breaks the requirement that old-version and
regenerated media stay aggregated by kind. Please use the same stable V2 group identity as the
list-message mapping, or pass that group id through the command/summary instead of reconstructing it
from `sourceMessageId`.
```

**19.4  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:850-853`**

```
This loses local facts when the server reuses the same attemptId across different mediaMessageIds,
which is explicitly supported by the new DAO storage format. The later local item overwrites the
earlier one, so `_matchingLocalMediaItem` may fail to match the correct local item (or match only
the last colliding attempt), dropping localPath/liked/createdAt during remote merge. Key this lookup
by `(mediaMessageId, attemptId)` or store a list and filter by mediaMessageId/kind when matching.

        final attemptId = item.attemptId?.trim();
-       if (attemptId != null && attemptId.isNotEmpty) {
-         localByAttemptId[attemptId] = item;
+       final mediaMessageId = item.mediaMessageId?.trim();
+       if (attemptId != null &&
+           attemptId.isNotEmpty &&
+           mediaMessageId != null &&
+           mediaMessageId.isNotEmpty) {
+         localByAttemptId['$mediaMessageId::$attemptId'] = item;
        }
```

**19.5  `lib/data/repositories/impl/chat_repository_impl.dart:1117-1120`**

```
This fallback dedupe matches only by source keys, so when a nested V2 media item is missing
`mediaMessageId`, any flat media sibling with the same `sourceMessageId`/group/version is filtered
regardless of media type. In partial V2 groups this can hide a legitimate flat video when only an
image is nested (or vice versa), which violates the requirement that flat sibling media remains
visible. Consider recording fallback identities with the media kind/type and requiring both source
key and kind to match before treating the flat media as a duplicate.
```

**19.6  `lib/data/repositories/impl/chat_repository_impl.dart:1180-1184`**

```
Same over-broad source-key dedupe applies to raw generated-media rows: a missing-id nested image
adds the source key, and then a flat video row with that same source key is skipped before it can be
attached to the V2 bubble. Please include the media kind in the fallback dedupe key (or otherwise
verify the raw row is the same media type as the missing-id nested item) so partial V2 nested groups
do not suppress valid flat sibling media.
```

### OCR 轮 20 — L13466（35 files, 8 comments）

**20.1  `lib/data/datasources/affiny_chat_local_data_source_impl.dart:356-361`**

```
This V2 detection is tied to `msggrp_` naming, but the V2 contract only guarantees nested
`imageGroup`/`videoGroup`, not that `versionGroupId` or `messageId` will use this prefix. If a V2
response has a different stable id, image and video snapshots are persisted under the same
`mediaGroupId`; the single `generated_media_messages.selected_media_item_id` row can then be
overwritten by the last kind persisted, so one cell loses its `selectedInGroup` selection after
restore. Consider deriving the split from the summary shape (e.g. mixed image/video items or
per-kind selected groups) rather than backend id prefixes.

+     final containsMixedKinds = media.displayItems
+         .map((item) => item.kind)
+         .toSet()
+         .length > 1;
      final isV2RegenerateGroup =
+         containsMixedKinds ||
          baseGroupId.startsWith('media_group_msggrp_') ||
          media.sourceAiMessageId.trim().startsWith('msggrp_');
      if (!isV2RegenerateGroup) {
        return baseGroupId;
      }
```

**20.2  `lib/domain/usecases/story_chat_usecase_impl.dart:1290-1290`**

```
This fallback can preserve a media-message timestamp on an item that is now backed by an attempt
whose `createdAt` is missing. The V2 ordering contract says an existing attempt row without a valid
created time must not fall back to the media message time, so merging a previous fallback item with
an incoming attempt can make the group look orderable by the wrong time. Consider distinguishing
attempt-backed incoming items and, for those, keep `createdAt` as `incoming.createdAt` even when it
is null.
```

**20.3  `test/data/repositories/generation_repository_test.dart:95-97`**

```
This V2 grouping test verifies local persistence, but it does not guard the backend contract that
`mediaGroupId` is only for local grouping and must not be sent to the create API. Please add an
assertion on `remote.lastCreateRequest!.json` so a regression that serializes `mediaGroupId` into
the request is caught.

              mediaGroupId: 'media_group_msggrp_ai_001',
              kind: GeneratedMediaKind.video,
              consumptionConfirmed: true,
```

**20.4  `test/data/repositories/generation_repository_test.dart:748-750`**

```
Since retry commands now carry `mediaGroupId`, this test should also assert the retry backend
payload does not include it. The requirement says the field is only for local persistence grouping,
so without this assertion the test can pass even if retry starts leaking `mediaGroupId` to the
backend.

              mediaGroupId: 'media_group_msggrp_ai_001',
              kind: GeneratedMediaKind.image,
              consumptionConfirmed: true,
```

**20.5  `test/domain/usecases/story_chat_usecase_test.dart:828-832`**

```
This verifies the selected item changes, but it would still pass if the merge implementation moves
`attempt_2` to the front. The requirement says current selection must be carried by
`selectedInGroup` while preserving API/DAO attempt order, so this regression test should also assert
the display item order remains `attempt_1`, then `attempt_2`.

+         expect(
+           items.map((item) => item.attemptId),
+           containsAllInOrder(<String>['attempt_1', 'attempt_2']),
+         );
          expect(items.where((item) => item.selectedInGroup), hasLength(1));
          expect(
            items.singleWhere((item) => item.selectedInGroup).attemptId,
            'attempt_2',
          );
```

**20.6  `lib/data/repositories/impl/generation_repository_impl.dart:172-177`**

```
This hard-codes V2 group recognition to `media_group_msggrp_*`. However the V2 summary builder can
fall back to `message.messageId` when `versionGroupId` is absent, producing IDs like
`media_group_msg_ai_...`; those will fail this check and `_mediaGroupIdForPersist` will persist
regenerated media under a source-derived `media_group_<source>_<kind>` instead of the existing
summary group. That can split locally-created regenerated media from the V2 image/video group until
refresh, causing duplicate or missing grouped cells. Consider deriving the persisted group ID from
the same shared V2 mapping used for fetched summaries, or passing an already kind-scoped group id
instead of relying on this prefix heuristic.
```

**20.7  `lib/data/repositories/impl/chat_repository_impl.dart:1426-1435`**

```
This V2 detection only accepts `media_group_msggrp_*`, but the V2 summary builder falls back to
`media_group_<messageId>` when `versionGroupId` is absent. In that case regenerate/create from an
existing V2 media cell will ignore the preferred group and persist under
`media_group_<sourceMessageId>_<kind>` instead of the same local grouping scheme used for V2
summaries, which can split the regenerated item out of its existing image/video cell. Consider
making the command carry an explicit V2/grouping mode, or accepting the same normalized V2
mediaGroupId formats produced by the chat repository rather than relying on the `msggrp_` prefix
only.
```

**20.8  `lib/data/dao/generated_media_dao_impl.dart:775-775`**

```
This ordering can pick the wrong “first attempt” when a media message has multiple rows with the
same `attempt_no`. The DAO's retry/append path inserts appended attempts with `attempt_no = 0`, so
SQLite is free to return a later retry row here, making `group_first_generated_at` use the
regenerated time and reordering cells against the golden-path requirement. Please make the
first-attempt selection deterministic (for example, order ties by insertion order/rowid or store
appended attempts with a strictly increasing attempt number) so regenerated attempts cannot become
the group's original generation time.

- 		      ORDER BY gb.attempt_no ASC
+ 		      ORDER BY gb.attempt_no ASC, gb.rowid ASC
```

---

## 3. OCR 去重后 unique findings 索引（129 条）

> 去重口径：同一 `文件 + 正文前 80 字符` 视为同一 finding；`rounds` 列为该 finding 出现的轮次（多轮 = 修复后又被复检/未收敛）。`首现行号` 为首次出现的会话行号。

| # | 文件 | 行 | 类别(本报告归类) | 首现轮/行 | 出现轮次 | 一句话问题 |
|---|---|---|---|---|---|---|
| U01 | `lib/data/api/app_api_methods.dart` | 138-139 | Other data-layer correctness | r1/L6672 | [1] | `AppApiMethods` is instantiated with `baseUrl: AffinyApiContract.defaultBaseUrl`, which already includes `/api/v1` |
| U02 | `test/data/repositories/chat_repository_test.dart` | 2089-2089 | Test quality (weak/misleading assertion or fixture) | r1/L6672 | [1] | This conditional always returns `1`, so the fixture does not actually model different `current.attemptNo` values when `i |
| U03 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 363-369 | Attempt/media identity matching | r1/L6672 | [1] | For V2 summaries, `selectedIndex` can identify only one item across the combined image+video list, while each media grou |
| U04 | `lib/data/datasources/affiny_remote_data_source_impl.dart` | 26-26 | Group/attempt ordering by first-generation time | r2/L7209 | [2] | Adding `_apiV2` as a required positional constructor argument leaves at least one existing direct instantiation (`integr |
| U05 | `test/data/datasources/affiny_remote_data_source_impl_test.dart` | 440-441 | Test quality (weak/misleading assertion or fixture) | r2/L7209 | [2] | Since `AppApiMethodsV2` currently has only `listStoryMessages`, this fake can implement the interface completely without |
| U06 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 363-369 | Attempt/media identity matching | r2/L7209 | [2] | This loses the selected attempt when items do not carry `mediaMessageId` and the grouping key falls back to `_mediaMessa |
| U07 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 809-811 | Media status aggregation | r2/L7209 | [2] | This makes any cached local file override newer remote terminal states such as `failed`, `blocked`, `refunded`, or `canc |
| U08 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1123-1125 | Group/attempt ordering by first-generation time | r2/L7209 | [2] | `_aiMessageFromJson` only reads `createdAt`/`created_at`, so the V2 version timestamp written as `createdAtUnixMs` is ig |
| U09 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 365-369 | Attempt/media identity matching | r3/L7427 | [3] | This comparison can miss the selected item when it has an explicit `mediaMessageId` |
| U10 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 982-985 | Test quality (weak/misleading assertion or fixture) | r3/L7427 | [3] | This test is named around persisting the selected item, but it never verifies that `selectedIndex` (or the currently dis |
| U11 | `lib/data/dao/generated_media_dao_impl.dart` | 703-706 | Current/selected-item resolution | r4/L7681 | [4] | This restores `selectedIndex` from every media file's `latest_attempt_id` |
| U12 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 794-804 | Local/remote merge & display retention | r4/L7681 | [4] | This rebuilds the merged media summary exclusively from `remote.displayItems`, so any already persisted local media item |
| U13 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 805-808 | Local/remote merge & display retention | r5/L8091 | [5] | Falling back to `mediaMessageId` can merge facts from the wrong regenerate attempt |
| U14 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 471-477 | Group/attempt ordering by first-generation time | r5/L8091 | [5] | This makes the whole grouped media cell `generating` whenever any preserved old attempt is still generating/polling, eve |
| U15 | `lib/data/datasources/affiny_remote_data_source_impl.dart` | 0-0 | Local/remote merge & display retention | r5/L8091 | [5] | Matching by `mediaMessageId` as the last fallback is unsafe for regenerated groups because multiple attempts/items can s |
| U16 | `lib/data/datasources/affiny_remote_data_source_impl.dart` | 172-176 | Local/remote merge & display retention | r5/L8091 | [5] | When the remote selected index is invalid or the latest V2 response omits the current media item that was preserved from |
| U17 | `lib/data/datasources/affiny_remote_data_source_impl.dart` | 0-0 | Current/selected-item resolution | r5/L8091 | [5] | This derives the whole media message status from any generating/polling item before considering the selected/current ite |
| U18 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1204-1210 | Local/remote merge & display retention | r5/L8091 | [5] | This flattens imageGroup and videoGroup into a single summary but `GeneratedMediaMessageSummary` has only one `selectedI |
| U19 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1299-1304 | Group/attempt ordering by first-generation time | r5/L8091 | [5] | This uses only `attempts.first` to determine the group's first generated time |
| U20 | `lib/data/dao/generated_media_dao_impl.dart` | 795-799 | Current/selected-item resolution | r6/L8410 | [6] | Returning the server-provided group id without checking the existing persisted group's chat/source context can corrupt l |
| U21 | `lib/data/datasources/affiny_remote_data_source_impl.dart` | 172-176 | JSON decode / type-cast robustness | r6/L8410 | [6] | These new V2 numeric fields are decoded by the generated code with `(json['...'] as num?)?.toInt()`, so a string-encoded |
| U22 | `lib/data/datasources/affiny_remote_data_source_impl.dart` | 0-0 | JSON decode / type-cast robustness | r6/L8410 | [6] | `attemptNo` and `sourceTextVersionNo` are part of the new server response contract, but leaving them as plain `int` make |
| U23 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1210-1212 | Current/selected-item resolution | r6/L8410 | [6] | This uses the raw top-level V2 message id as the media summary source, but `_v2AiMessageFromJson` already falls back to  |
| U24 | `lib/data/api/models/story_models.g.dart` | 131-131 | JSON decode / type-cast robustness | r6/L8410 | [6] | The V2 contract allows these numeric fields to arrive as JSON numbers or strings (e.g |
| U25 | `lib/data/api/models/story_models.g.dart` | 131-131 | JSON decode / type-cast robustness | r6/L8410 | [6] | Same decoding issue here: `versionNo` is part of the server V2 version payload and may be string-encoded |
| U26 | `lib/data/api/app_api_methods_v2.dart` | 0-0 | JSON decode / type-cast robustness | r6/L8410 | [6] | The new V2 numeric fields are decoded as plain `int`s |
| U27 | `lib/data/api/models/story_models.g.dart` | 0-0 | JSON decode / type-cast robustness | r6/L8410 | [6] | `attemptNo` and especially `sourceTextVersionNo` are V2 wire fields used to identify the current media attempt and sourc |
| U28 | `lib/data/api/app_api_methods_v2.dart` | 0-0 | JSON decode / type-cast robustness | r6/L8410 | [6] | These V2 attempt/version counters are plain `int`s, so string-encoded values from the API will fail deserialization |
| U29 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 361-365 | Group/attempt ordering by first-generation time | r6/L8410 | [6] | Using the current display order in the persistence key makes the same image/video group unstable |
| U30 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 458-462 | Attempt/media identity matching | r6/L8410 | [6] | This fallback returns the same stripped group id for every item without `mediaMessageId` |
| U31 | `test/data/repositories/chat_repository_mock_api_test.dart` | 161-161 | Test quality (weak/misleading assertion or fixture) | r6/L8410 | [6] | Same concern as above: if the V2 response sends attempt/version numbers as JSON strings, deserialization will fail becau |
| U32 | `test/data/repositories/chat_repository_mock_api_test.dart` | 0-0 | Test quality (weak/misleading assertion or fixture) | r6/L8410 | [6] | These V2 numeric fields are decoded by the generated code with `(json['...'] as num?)?.toInt()`, so a valid payload that |
| U33 | `lib/data/api/models/generation_models.g.dart` | 203-203 | JSON decode / type-cast robustness | r7/L8681 | [7] | `attemptCount` still uses a direct `num` cast while the V2 API counters are expected to be string-or-number tolerant |
| U34 | `.trellis/tasks/06-26-06-26-regenerate-version-media-groups/task.json` | 146-147 | Task evidence record integrity | r7/L8681 | [7] | These newly recorded review evidences appear to be truncated mid-sentence (`...success+failure path` and `Cr`) |
| U35 | `.trellis/tasks/06-26-06-26-regenerate-version-media-groups/task.json` | 156-157 | Task evidence record integrity | r7/L8681 | [7] | This evidence value is cut off at `Cr`, which makes the audit record incomplete even though the JSON syntax is valid |
| U36 | `lib/data/api/models/story_models.dart` | 159-160 | JSON decode / type-cast robustness | r7/L8681 | [7] | These V2 DTO booleans bypass the existing non-null bool converter, so generated deserialization uses `json['current'] as |
| U37 | `lib/data/api/models/story_models.dart` | 182-182 | JSON decode / type-cast robustness | r7/L8681 | [7] | `liked` is decoded with a plain bool cast in the generated code |
| U38 | `lib/data/api/models/story_models.freezed.dart` | 467-467 | JSON decode / type-cast robustness | r7/L8681 | [7] | These new V2 boolean fields are generated without `NonNullBoolConverter`, so the matching `fromJson` code casts them wit |
| U39 | `lib/data/api/models/story_models.freezed.dart` | 621-621 | JSON decode / type-cast robustness | r7/L8681 | [7] | `liked` has the same plain-bool deserialization risk: generated JSON code will do `json['liked'] as bool?`, while the AP |
| U40 | `lib/data/dao/generated_media_dao_impl.dart` | 96-96 | Group/attempt ordering by first-generation time | r7/L8681 | [7] | This overwrites an existing group's persisted order with `0` whenever a later save path does not provide `displayOrder`  |
| U41 | `lib/data/dao/generated_media_dao_impl.dart` | 1093-1095 | Attempt/media identity matching | r7/L8681 | [7] | If this file is the selected media message but `latestAttemptId` is missing from `fileItems` (e.g |
| U42 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 960-964 | Local/remote merge & display retention | r7/L8681 | [7] | This identity fallback treats only `null` attempt ids as absent, while the rest of this datasource normalizes ids with ` |
| U43 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1000-1004 | Other data-layer correctness | r7/L8681 | [7] | Because this flag is page-wide, the presence of any V2-shaped text message (for example one with `versions`) makes `_mes |
| U44 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1273-1281 | Group/attempt ordering by first-generation time | r7/L8681 | [7] | Group ordering currently ignores `ApiMediaMessage.createdAtUnixMs` and only looks at attempt timestamps |
| U45 | `lib/data/api/models/generation_models.dart` | 65-65 | JSON decode / type-cast robustness | r8/L9145 | [8] | This relies on `NonNullBoolConverter` for the V2 `liked` value, but that converter only treats boolean `true`, non-zero  |
| U46 | `lib/data/api/models/generation_models.freezed.dart` | 386-386 | JSON decode / type-cast robustness | r8/L9145 | [8] | `NonNullBoolConverter` currently only treats boolean strings equal to `"true"` as true; string-number booleans such as ` |
| U47 | `lib/data/dao/generated_media_dao_impl.dart` | 706-715 | Group/attempt ordering by first-generation time | r8/L9145 | [8] | This ordering does not match the required media-cell ordering |
| U48 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1076-1087 | Current/selected-item resolution | r8/L9145 | [8] | Flat page-level media is filtered through the typed `ApiMediaMessage`, but this helper only exposes `sourceMessageId` an |
| U49 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1624-1627 | Attempt/media identity matching | r8/L9145 | [8] | Dropping nested V2 media when `mediaMessageId` is empty can make an entire image/video group disappear (`_v2MediaGroupSu |
| U50 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 355-357 | Current/selected-item resolution | r8/L9145 | [8] | This makes the persisted group id depend on the current page shape: if a V2 message is fetched while it only has an imag |
| U51 | `lib/data/dao/generated_media_dao_impl.dart` | 709-709 | Group/attempt ordering by first-generation time | r9/L9486 | [9] | The group timestamp calculation ignores media messages that have no attempts whenever any other item in the same group h |
| U52 | `test/data/repositories/chat_repository_mock_api_test.dart` | 161-161 | Test quality (weak/misleading assertion or fixture) | r9/L9486 | [9] | This mock repository now sends story-message pagination through `/api/v2/...`, but `AffinyMockApiInterceptor` used by th |
| U53 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 453-460 | Group/attempt ordering by first-generation time | r9/L9486 | [9] | The persisted snapshots do not carry the V2 media/attempt `createdAtUnixMs`, so the DAO falls back to `DateTime.now()` p |
| U54 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 910-917 | Local/remote merge & display retention | r9/L9486 | [9] | Falling back to a sole `mediaMessageId` match can merge local facts from an old attempt into a different remote attempt  |
| U55 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1325-1329 | Persisted group-id stability | r9/L9486 | [9] | This summary uses a single `mediaGroupId` for the combined V2 image/video media summary |
| U56 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 937-942 | Local/remote merge & display retention | r10/L9972 | [10] | This fallback can still attach stale local facts to a new regenerated item when the remote item has no attempt identity |
| U57 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 332-341 | Current/selected-item resolution | r10/L9972 | [10] | This marks the first item of each kind as selected in addition to the actual `selectedIndex` |
| U58 | `test/data/api/mock/affiny_mock_api_interceptor_test.dart` | 65-71 | Test quality (weak/misleading assertion or fixture) | r10/L9972 | [10] | This setup does not actually exercise the interceptor's `/api/v2` path normalization: Retrofit keeps the request path as |
| U59 | `lib/data/api/models/story_models.dart` | 144-147 | Other data-layer correctness | r11/L10227 | [11] | `ApiChatMessageVersion.text` is user-visible story content, but the new Freezed DTO will generate a `toString()` that in |
| U60 | `lib/domain/usecases/story_chat_usecase_impl.dart` | 1292-1292 | Current/selected-item resolution | r11/L10227 | [11] | This makes `selectedInGroup` sticky: if a previously current media item is later returned as non-current after `group.cu |
| U61 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 369-369 | Local/remote merge & display retention | r11/L10227 | [11] | Appending `sourceAiMessageId` makes the persisted group id change when regenerate creates a new active text message/vers |
| U62 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 1020-1020 | Group/attempt ordering by first-generation time | r11/L10227 | [11] | `selectedInGroup` represents the server group.current/current media |
| U63 | `lib/data/dao/generated_media_dao_impl.dart` | 1032-1035 | Attempt/media identity matching | r11/L10227 | [11] | This still preserves cached local file metadata whenever the incoming snapshot has no `latestAttemptId`, even if the ser |
| U64 | `test/data/repositories/chat_repository_test.dart` | 1199-1201 | Test quality (weak/misleading assertion or fixture) | r11/L10227 | [11] | This fixture name is misleading: this test later asserts that this legacy media is preserved and displayed |
| U65 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 1134-1137 | Test quality (weak/misleading assertion or fixture) | r11/L10227 | [11] | This test name says it verifies the V2 per-kind media group id remains stable, but the assertions only check the restore |
| U66 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 1062-1063 | Test quality (weak/misleading assertion or fixture) | r11/L10227 | [11] | To make the group-id stability assertion possible, this test should use `createTestChatLocalFixture()` instead of only t |
| U67 | `lib/data/repositories/impl/chat_repository_impl.dart` | 0-0 | Test quality (weak/misleading assertion or fixture) | r11/L10227 | [11] | This assertion only checks that the video row is selected somewhere, so the test would still pass if the image group wer |
| U68 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1529-1530 | Test quality (weak/misleading assertion or fixture) | r11/L10227 | [11] | The test name says the remote terminal status wins over the cached local path, but the assertion still requires the stal |
| U69 | `lib/app/injector/injector.config.dart` | 566-573 | DI/codegen config | r12/L10705 | [12] | This generated config dropped the `ChatHistoryController` import/factory even though `RootBinding` and `ChatHistoryBindi |
| U70 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 896-898 | Local/remote merge & display retention | r12/L10705 | [12] | Appending unmatched local items preserves their old `selectedInGroup` flag |
| U71 | `lib/domain/usecases/story_chat_usecase_impl.dart` | 1487-1487 | Group/attempt ordering by first-generation time | r12/L10705 | [12] | This drops the media-level timestamp when an attempt has no `createdAt` |
| U72 | `lib/domain/models/media_models.dart` | 410-410 | Current/selected-item resolution | r12/L10705 | [12] | Defaulting this to `true` makes every persist path that does not explicitly carry group-current information update the g |
| U73 | `lib/data/dao/generated_media_dao_impl.dart` | 1217-1225 | Current/selected-item resolution | r12/L10705 | [12] | This single `selectedIndex` is shared by the combined summary keyed by `sourceMessageId`, but V2 persists image and vide |
| U74 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1313-1329 | Local/remote merge & display retention | r12/L10705 | [12] | This collapses `imageGroup` and `videoGroup` into a single `GeneratedMediaMessageSummary` by concatenating their items a |
| U75 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1408-1419 | Group/attempt ordering by first-generation time | r12/L10705 | [12] | The ordering timestamp for each mediaMessage is computed as the minimum over all attempts |
| U76 | `test/data/repositories/chat_repository_test.dart` | 1166-1171 | Test quality (weak/misleading assertion or fixture) | r12/L10705 | [12] | This case is intended to validate handling when a V2 nested media message has no `mediaMessageId`, but it only checks th |
| U77 | `lib/data/repositories/impl/generation_repository_impl.dart` | 59-59 | Local/remote merge & display retention | r13/L10954 | [13] | `mergeRemoteMediaPatch` does not appear to receive or validate the V2 `group.current` pointer; it persists each media pa |
| U78 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 446-452 | Group/attempt ordering by first-generation time | r13/L10954 | [13] | Reordering the attempts before persistence can change which row is considered the first attempt later |
| U79 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 929-935 | Attempt/media identity matching | r13/L10954 | [13] | Matching local facts by `attemptId` alone can copy `localPath`, `liked`, `createdAt`, or status from another media messa |
| U80 | `lib/data/api/app_api_methods_v2.dart` | 17-21 | Attempt/media identity matching | r13/L10954 | [13] | Reordering the persisted attempt list makes the selected/current attempt become index 0 when attempt IDs do not encode a |
| U81 | `lib/domain/usecases/story_chat_usecase_impl.dart` | 1292-1292 | Attempt/media identity matching | r13/L10954 | [13] | This reorders the persisted attempt list so the selected/current attempt becomes index 0 |
| U82 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 1226-1242 | Test quality (weak/misleading assertion or fixture) | r13/L10954 | [13] | This test is intended to guard ordering by the first generation time instead of a later retry, but the synthetic retry i |
| U83 | `test/data/repositories/chat_repository_test.dart` | 944-956 | Test quality (weak/misleading assertion or fixture) | r13/L10954 | [13] | This test does not actually make the group ordering depend on `media_img_from_v2`'s `attempts[0]`: the image group still |
| U84 | `lib/data/dao/generated_media_dao_impl.dart` | 737-740 | Other data-layer correctness | r13/L10954 | [13] | This query now relies on SQLite window functions (`ROW_NUMBER() OVER ...`) |
| U85 | `lib/data/repositories/impl/chat_repository_impl.dart` | 132-135 | Group/attempt ordering by first-generation time | r13/L10954 | [13] | For V2 message pages, user messages commonly carry `createdAtUnixMs`, but `_userMessageFromJson` only reads `createdAt`  |
| U86 | `lib/data/api/models/story_models.dart` | 169-172 | Current/selected-item resolution | r14/L11177 | [14, 14] | `ApiMediaGroup` is a newly introduced DTO that can contain nested `ApiMediaMessage` data (including media URLs/metadata) |
| U87 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 971-975 | Local/remote merge & display retention | r14/L11177 | [14] | This treats `attemptId` alone as a complete identity when calculating the merged selected index |
| U88 | `lib/data/dao/generated_media_dao_impl.dart` | 953-958 | Group/attempt ordering by first-generation time | r14/L11177 | [14] | This reorders persisted attempts by moving `latest_attempt_id` to the front of `displayItems` |
| U89 | `test/data/repositories/chat_repository_test.dart` | 925-925 | Test quality (weak/misleading assertion or fixture) | r14/L11177 | [14] | This assertion does not actually distinguish the required “first attempt createdAtUnixMs” ordering from an implementatio |
| U90 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 1226-1244 | Test quality (weak/misleading assertion or fixture) | r14/L11177 | [14] | This manually adds a second attempt but leaves `generated_media_files.latest_attempt_id` pointing at the original attemp |
| U91 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 334-343 | Current/selected-item resolution | r15/L11661 | [15] | When the payload already provides `selectedInGroup`, it should be authoritative for V2 `group.current` |
| U92 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1408-1413 | Group/attempt ordering by first-generation time | r15/L11661 | [15] | This fallback changes the required ordering semantics: media message `createdAtUnixMs` should only be used when the medi |
| U93 | `lib/data/repositories/impl/generation_repository_impl.dart` | 59-59 | Current/selected-item resolution | r15/L11661 | [15] | This marks the new locally-created media message as the selected item for the resolved persistence group, but this call  |
| U94 | `lib/data/repositories/impl/generation_repository_impl.dart` | 59-59 | Current/selected-item resolution | r15/L11661 | [15] | Same selection-overwrite risk here: when the response creates/replaces a media message but no kind-specific `mediaGroupI |
| U95 | `lib/domain/usecases/story_chat_usecase_impl.dart` | 1292-1292 | Current/selected-item resolution | r15/L11661 | [15] | This merge path is also used when attaching/updating generation snapshots, but `_generatedMediaItemFromAttempt` does not |
| U96 | `lib/data/dao/generated_media_dao_impl.dart` | 716-719 | Group/attempt ordering by first-generation time | r15/L11661 | [15] | For V2 regenerate groups, `_resolveGroupId` can intentionally reuse the same `media_group_id` across different source te |
| U97 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 904-909 | Local/remote merge & display retention | r16/L12016 | [16] | This item-id fast path bypasses the kind/mediaMessageId compatibility checks used by the attempt-id path and `_sameMedia |
| U98 | `lib/ui/pages/character_chat/character_chat_media_cell.dart` | 57-57 | Local/remote merge & display retention | r16/L12016 | [16] | This match path bypasses the kind/mediaMessageId compatibility checks used by the attempt-id path below |
| U99 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1388-1396 | Group/attempt ordering by first-generation time | r16/L12016 | [16] | This uses the oldest first-attempt timestamp in the group |
| U100 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1236-1237 | Group/attempt ordering by first-generation time | r16/L12016 | [16] | When a current V2 text version is present but its createdAtUnixMs is empty/missing, this overwrites the top-level messag |
| U101 | `lib/data/dao/generated_media_dao_impl.dart` | 172-172 | Group/attempt ordering by first-generation time | r17/L12277 | [17] | This changes missing attempt timestamps into the current persistence time |
| U102 | `lib/data/dao/generated_media_dao_impl.dart` | 728-728 | Group/attempt ordering by first-generation time | r17/L12277 | [17] | This falls back to `f2.created_at` whenever the first attempt row has a null/empty timestamp |
| U103 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 454-457 | Attempt/media identity matching | r17/L12277 | [17] | For V2 groups the repository moves `group.current` to the front of `displayItems` for UI selection |
| U104 | `lib/domain/usecases/story_chat_usecase_impl.dart` | 1292-1292 | Current/selected-item resolution | r17/L12277 | [17] | This merge can keep a stale selected item selected when a V2 group’s `current` changes |
| U105 | `test/ui/pages/character_chat/character_chat_media_cell_test.dart` | 104-111 | Test quality (weak/misleading assertion or fixture) | r17/L12277 | [17] | This test is meant to verify independent per-kind selection, but both the image and video selected items end up at local |
| U106 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1417-1422 | Group/attempt ordering by first-generation time | r17/L12277 | [17] | Using `now` when an attempt has no `createdAt` makes a missing V2 first-attempt timestamp look like a valid generation t |
| U107 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 1457-1458 | Test quality (weak/misleading assertion or fixture) | r17/L12277 | [17] | This collision coverage only varies `mediaMessageId`/kind while keeping distinct `attemptId`s |
| U108 | `lib/domain/usecases/story_chat_usecase_impl.dart` | 1489-1489 | Group/attempt ordering by first-generation time | r18/L12738 | [18] | This falls back to the media message timestamp even when an attempt row exists but its created time is missing |
| U109 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 454-461 | Group/attempt ordering by first-generation time | r18/L12738 | [18] | This reorders attempts by timestamp before persistence |
| U110 | `lib/data/dao/generated_media_dao_impl.dart` | 1081-1092 | Attempt/media identity matching | r18/L12738 | [18] | The storage/display invariant is tied to the owning `mediaMessageId` passed to DAO calls: rows are queried by `media_mes |
| U111 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1005-1006 | Attempt/media identity matching | r18/L12738 | [18] | This deduplicates flat `mediaMessages` by source IDs collected from any nested V2 media group |
| U112 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 1267-1274 | Test quality (weak/misleading assertion or fixture) | r18/L12738 | [18] | This selection of the group's original generation time can pick the wrong attempt when the server's `attempts[0]` is not |
| U113 | `test/data/datasources/affiny_chat_local_data_source_test.dart` | 0-0 | Test quality (weak/misleading assertion or fixture) | r18/L12738 | [18] | This log runs for every restored attempt while loading chat media summaries, which is a hot path and can emit one line p |
| U114 | `test/domain/usecases/story_chat_usecase_test.dart` | 0-0 | Test quality (weak/misleading assertion or fixture) | r18/L12738 | [18] | The storage key is required to be `mediaMessageId::attemptId`, but this uses `attempt.mediaMessageId` when present |
| U115 | `test/domain/usecases/story_chat_usecase_test.dart` | 0-0 | Test quality (weak/misleading assertion or fixture) | r18/L12738 | [18] | For missing attempt timestamps this falls back to the client write time, which makes an attempt row look like it has a v |
| U116 | `lib/data/dao/generated_media_dao_impl.dart` | 761-765 | Group/attempt ordering by first-generation time | r19/L13075 | [19] | The group ordering treats any non-empty `generated_media_attempts.created_at` as a valid timestamp |
| U117 | `test/data/repositories/chat_repository_test.dart` | 1219-1222 | Test quality (weak/misleading assertion or fixture) | r19/L13075 | [19] | This assertion does not exercise the duplicate filtering path: the fixture never creates a media item with mediaMessageI |
| U118 | `lib/data/repositories/impl/generation_repository_impl.dart` | 57-60 | Current/selected-item resolution | r19/L13075 | [19] | This group id is derived from the action `sourceMessageId`, which for V2 story messages is the active/current text messa |
| U119 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 850-853 | Local/remote merge & display retention | r19/L13075 | [19] | This loses local facts when the server reuses the same attemptId across different mediaMessageIds, which is explicitly s |
| U120 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1117-1120 | Attempt/media identity matching | r19/L13075 | [19] | This fallback dedupe matches only by source keys, so when a nested V2 media item is missing `mediaMessageId`, any flat m |
| U121 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1180-1184 | Other data-layer correctness | r19/L13075 | [19] | Same over-broad source-key dedupe applies to raw generated-media rows: a missing-id nested image adds the source key, an |
| U122 | `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 356-361 | Current/selected-item resolution | r20/L13466 | [20] | This V2 detection is tied to `msggrp_` naming, but the V2 contract only guarantees nested `imageGroup`/`videoGroup`, not |
| U123 | `lib/domain/usecases/story_chat_usecase_impl.dart` | 1290-1290 | Group/attempt ordering by first-generation time | r20/L13466 | [20] | This fallback can preserve a media-message timestamp on an item that is now backed by an attempt whose `createdAt` is mi |
| U124 | `test/data/repositories/generation_repository_test.dart` | 95-97 | Test quality (weak/misleading assertion or fixture) | r20/L13466 | [20] | This V2 grouping test verifies local persistence, but it does not guard the backend contract that `mediaGroupId` is only |
| U125 | `test/data/repositories/generation_repository_test.dart` | 748-750 | Test quality (weak/misleading assertion or fixture) | r20/L13466 | [20] | Since retry commands now carry `mediaGroupId`, this test should also assert the retry backend payload does not include i |
| U126 | `test/domain/usecases/story_chat_usecase_test.dart` | 828-832 | Test quality (weak/misleading assertion or fixture) | r20/L13466 | [20] | This verifies the selected item changes, but it would still pass if the merge implementation moves `attempt_2` to the fr |
| U127 | `lib/data/repositories/impl/generation_repository_impl.dart` | 172-177 | Persisted group-id stability | r20/L13466 | [20] | This hard-codes V2 group recognition to `media_group_msggrp_*` |
| U128 | `lib/data/repositories/impl/chat_repository_impl.dart` | 1426-1435 | Persisted group-id stability | r20/L13466 | [20] | This V2 detection only accepts `media_group_msggrp_*`, but the V2 summary builder falls back to `media_group_<messageId> |
| U129 | `lib/data/dao/generated_media_dao_impl.dart` | 775-775 | Local/remote merge & display retention | r20/L13466 | [20] | This ordering can pick the wrong “first attempt” when a media message has multiple rows with the same `attempt_no` |

### 3a. 按类别分布（unique）

| 类别 | 数量 |
|---|---|
| Test quality (weak/misleading assertion or fixture) | 27 |
| Group/attempt ordering by first-generation time | 27 |
| Current/selected-item resolution | 18 |
| Local/remote merge & display retention | 17 |
| Attempt/media identity matching | 14 |
| JSON decode / type-cast robustness | 14 |
| Other data-layer correctness | 5 |
| Persisted group-id stability | 3 |
| Task evidence record integrity | 2 |
| Media status aggregation | 1 |
| DI/codegen config | 1 |

### 3b. 按文件分布（unique，Top）

| 文件 | 数量 |
|---|---|
| `lib/data/datasources/affiny_chat_local_data_source_impl.dart` | 27 |
| `lib/data/repositories/impl/chat_repository_impl.dart` | 22 |
| `lib/data/dao/generated_media_dao_impl.dart` | 16 |
| `test/data/datasources/affiny_chat_local_data_source_test.dart` | 8 |
| `lib/domain/usecases/story_chat_usecase_impl.dart` | 7 |
| `test/data/repositories/chat_repository_test.dart` | 6 |
| `lib/data/datasources/affiny_remote_data_source_impl.dart` | 6 |
| `lib/data/repositories/impl/generation_repository_impl.dart` | 5 |
| `lib/data/api/models/story_models.dart` | 4 |
| `lib/data/api/models/story_models.g.dart` | 3 |
| `lib/data/api/app_api_methods_v2.dart` | 3 |
| `test/data/repositories/chat_repository_mock_api_test.dart` | 3 |
| `test/domain/usecases/story_chat_usecase_test.dart` | 3 |
| `.trellis/tasks/06-26-06-26-regenerate-version-media-groups/task.json` | 2 |
| `lib/data/api/models/story_models.freezed.dart` | 2 |
| `test/data/repositories/generation_repository_test.dart` | 2 |
| `lib/data/api/app_api_methods.dart` | 1 |
| `test/data/datasources/affiny_remote_data_source_impl_test.dart` | 1 |
| `lib/data/api/models/generation_models.g.dart` | 1 |
| `lib/data/api/models/generation_models.dart` | 1 |
| `lib/data/api/models/generation_models.freezed.dart` | 1 |
| `test/data/api/mock/affiny_mock_api_interceptor_test.dart` | 1 |
| `lib/app/injector/injector.config.dart` | 1 |
| `lib/domain/models/media_models.dart` | 1 |
| `lib/ui/pages/character_chat/character_chat_media_cell.dart` | 1 |
| `test/ui/pages/character_chat/character_chat_media_cell_test.dart` | 1 |

---

## 4. Guru check-worker 的 finding（IMPLEMENT_DEFECT 及描述）

会话里跑了 3 个 Trellis 官方 channel `implement-check` worker（均通过 `guru_supervise.py`）。三者都输出 `route_class=IMPLEMENT_DEFECT`，但严重度与命中内容差异巨大：

### 4.1 check-claude-20260626154656-2039（第 1 轮，会话 L6121 起；finding 综述在 L6816）

`review_result=findings` / 含 IMPLEMENT_DEFECT + DETAIL_DEFECT。原文（agent 综述）：

- **P2 IMPLEMENT_DEFECT**：缺少 text fallback、group current fallback、missing first time 的诊断日志。→ 已在 `ChatRepositoryImpl` 增加脱敏 `Log.w`（`event=story_v2_text_version_fallback` / `story_v2_media_current_fallback` / `story_v2_media_first_time_missing`）。
- **P2 DETAIL_DEFECT**：详细设计 owner 写成 `StoryChatUseCase`，实现实际在 `ChatRepositoryImpl`。→ 已修订 design-main.md 等文档使合同与实现一致。
- **P3**：`versions: []` 不能作为可靠 V2 marker（已保留 typed 非默认 marker 策略）。
- **P3**：GitNexus evidence 缺失（CLI 工具链阻塞）。
- 机械修复：移除 `ChatRepositoryImpl` 未使用的 `_V2MediaGroupSummary.sourceAiMessageId`。

### 4.2 check-claude-20260627005700-20104（第 2 轮，会话 L6522 起；综述在 L6816/L6528）

`review_result=findings`，**仅 P3**，`route_class=IMPLEMENT_DEFECT`；**Claude 结论：可进入 PR / final-verification-ready，无 P1/P2 阻塞**。原文：

- **P3-1**：`_fallbackV2GroupSelectedIndex`、`_currentFirstV2GroupItems`、`_v2GeneratedMediaSummaryFromMessage` 兜底/current-first 私有 helper 可补“为什么”注释。（无 P1/P2，故不扩大改动）
- **P3-2**：AC-006 wire path 可补 path-capture 字符串断言。（`.g.dart` 已静态钉死路径，故不扩大测试）

> 注意：这是用户在 L6585 点名 OCR **之前**的最后一道 Guru 闸。两轮 claude check 都没有触及任何 V2 数据合并/排序/身份匹配缺陷，等于把 diff 放行到了“可进入 PR”。

### 4.3 check-codex-20260627160445-41734-check-1（最终轮，会话 L14667 起；finding 原文在 L14788/L14789）

`review_result=findings` / `route_class=IMPLEMENT_DEFECT`。worker 原文（逐字，`Issues Not Fixed` 段）：

> **1. P2 / `lib/data/datasources/affiny_chat_local_data_source_impl.dart:915`** — `_mergeRemoteMediaWithLocalFacts` appends unmatched local display items into the remote summary. The test at `affiny_chat_local_data_source_test.dart:1528` locks in that behavior by expecting `media_video_1` to remain visible when the latest remote grouped summary only contains `media_img_1`. This conflicts with `design-main.md:37`, which says a local completed media message absent from the server V2 group must not be injected into the current V2 Cell, and with `requirement-api.md:71`, which makes V2 `mediaMessages[]` authoritative. Deferred because fixing this changes the merge contract and test expectation. Minimal fix direction: for V2 grouped summaries, merge local facts only onto matching remote items; keep omitted local facts in DAO storage but do not append them to the current remote summary. Then replace the current test expectation with “omitted local item remains stored but not displayed in the V2 Cell.”
>
> **2. P2 / `pubspec.lock:9`** — staged lockfile churn rewrites hosted package URLs from `https://pub.dev` to `https://pub.flutter-io.cn` throughout the lockfile and rewrites a local SDK path at `pubspec.lock:47`. There is no corresponding `pubspec.yaml` change in this task… (非本任务环境 churn，提交前需排除/人工确认)

- `Issues Found and Fixed: None.`（check pass 不静默改行为缺陷）
- worker note：`guru_supervise` 一度报 `check output missing route_class or review_result=clean/final-verification-ready; cannot route safely`（worker 把字段放在正文，解析口径再次踩坑，与 §0 需求轮的 `=` vs `:` 解析问题同源）。

**P2#1 即本任务的核心 bug**（用户描述的“远端未返回的 V2 媒体项被 local merge 重新 append 回可见 displayItems”）。agent 随后修复（L14835–L14959）：对命中 `_isV2RegenerateSummaryGroupId`（`media_group_v2_` / `media_group_msggrp_`）的 V2 group，只对远端仍返回的 item 合并 local facts，不再 append 漏项；测试改为 `keeps omitted V2 grouped media stored but not displayed`（漏项 `media_video_1` 仍在 `generated_media_files`，但不进可见 `displayItems`）。修复全程 **未调用 OCR**（L14793/L14927/L14959 明确）。

---

## 5. OCR 发现 ↔ Guru review 的对账

### 5.1 会话内是否有显式对账？

**没有 agent 主动写的并排对照表。** 会话里能确证对账关系的只有 3 个数据点：
- L14921 / L14943 `implement.md` 补记：“check worker 输出 `review_result=findings`/`IMPLEMENT_DEFECT`。**本轮未调用 OCR / Open Code Review**。”
- L14959 最终交付消息：“已继续完成，且**没有调用 OCR / Open Code Review**”，随后描述同一 V2 merge 修复。
- 即：本任务最关键的 P2（远端漏项被 append 进可见 V2 Cell）是 **Guru check-codex worker 抓到、且在没有 OCR 参与下修复的**。

### 5.2 关键发现：OCR 与 Guru 在这条 bug 上**结论相反**（本报告交叉比对得出，附行号）

| | OCR | Guru check-codex-41734 |
|---|---|---|
| 对“远端 V2 未返回、本地仍有的 media item” | **U12 (轮4 / L7681)**：明确建议 “keep unmatched local display items in the merged list after merging matched remote items” —— 把“丢弃漏项”当成 bug | **P2 / L14788**：把“append 漏项进 remote summary”当成 bug，引 `design-main.md:37` + `requirement-api.md:71` 判定违反 V2 `mediaMessages[]` 权威 |
| 测试 | OCR 的建议被固化成 `affiny_chat_local_data_source_test.dart:1528` 的“`media_video_1` 仍可见”断言 | 指出该测试“locks in”了错误行为，要求改为“stored but not displayed” |
| 净效果 | OCR 20 轮 **从未** 把 append 判为缺陷；U70(轮12/L10705) 只补了 append 的副作用（stale `selectedInGroup`），仍保留 append | 一轮即定位合同违例并给出最小修向 |

**结论：在本任务核心 bug 上，OCR 不是“漏抓”，而是给了与需求/设计 SSOT 相反的指导，背书了该 bug 方向并在后续 20 轮未纠正（属背书/未纠正，非 OCR 原创写入）。** 根因是 OCR 只拿到 `--background` 散文上下文，无法对齐 `design-main.md:37`「absent from server V2 group must not be injected into current V2 Cell」与 `requirement-api.md:71`「V2 mediaMessages[] authoritative」这类 SSOT 硬约束；Guru check worker 因为以需求/设计包为权威基线，才一轮命中。

### 5.3 反向差集：OCR 抓到、而（前两轮）Guru check 当时没抓到的

用户点名 OCR 之前的两轮 claude check 只产出 P2 日志 + P3 注释/wire-path，**放行到“可进入 PR”**。OCR 随后在同一 diff 上抓出 129 条 data-layer 问题，按类别（本报告归类）：

- Group/attempt 排序（按首次生成时间）：27 条 —— 反复出现，OCR 自己在多轮间来回（轮13 U78 让“别按时间排序保持源序”，轮17 U103 又让“按 createdAt 排序”，轮18 U109 再次让“别排序”，说明 OCR 对这条 SSOT 排序口径自身震荡、未收敛）
- 测试质量（弱/误导断言）：27 条
- current/selected 项解析：18 条
- 本地/远端 merge 与展示保留：17 条（含 U12/U70）
- attempt/media 身份匹配（id 复用/碰撞）：14 条
- JSON 解码/类型转换健壮性（num/string/bool converter）：14 条
- 其余（group-id 稳定、状态聚合、DI、task 证据）：12 条

这些里很多是真实数据层缺陷（如 U07 终态被本地缓存覆盖、U13/U56/U79/U119 attempt-id 碰撞串味、U16 selection 回退到 0），两轮 claude check 完全没有触及。

### 5.4 给“优化 guru review skill 达到 OCR 等效”的事实结论

- OCR 的强项是**大面积、逐行、可复跑（20 轮自收敛尝试）的实现层缺陷扫描**；本会话单条 diff 抓 129 条，覆盖解码/身份/状态/选择/排序/测试质量。Guru 的两轮 claude check 在同一 diff 上几乎只报日志与注释级问题，差距悬殊——这是 guru review skill 需要补齐的“代码级密度”。
- 但 OCR 的致命短板是**缺乏对需求/设计 SSOT 的接地**：在核心合同（V2 漏项不得注入可见 Cell）上给出相反指导。Guru check worker 因为以 `design-main.md` / `requirement-api.md` 为权威，反而一轮命中。
- 因此“等效”不应是“把 guru 换成 OCR”，而是：**guru review skill 在保留 SSOT 接地（design/requirement 行级引用）的同时，引入 OCR 式逐行实现扫描密度**；并且把 SSOT 约束作为对任何外部 reviewer（含 OCR）建议的否决闸——本会话若有此闸，U12 的错误建议就不会被采纳。
- 工程提醒：会话两处 Guru 解析口径坑（`review_result=`vs`:` L769/L789；最终 worker `cannot route safely` L14788）说明 `guru_supervise.py` 的 verdict 解析需要更鲁棒，否则会把 clean/findings 误判。
