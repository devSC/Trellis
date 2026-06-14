# Quality

> 本项目 iOS 质量门禁的真实约定：SwiftLint / build / test 命令与 CI 门禁。

---

## SwiftLint

<!-- 启用哪套 SwiftLint 配置（`.swiftlint.yml` 位置）？开了哪些自定义/opt-in 规则？哪些告警提升为 error？运行命令是什么？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Build

<!-- 本项目标准 build 命令是什么（`xcodebuild` / scheme / destination）？哪些 warning 被当 error（`-warnings-as-errors`）？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Test

<!-- 测试如何运行（`xcodebuild test` / 框架 XCTest 或 Swift Testing）？覆盖率门槛是多少、在哪测量？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## CI Gate

<!-- CI 上 lint/build/test 的执行顺序与卡点是什么？合并前必须全绿的检查有哪些？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 质量门禁上反复踩过的坑（本地不跑 lint、跳过 test、用 `// swiftlint:disable` 绕过规则等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
