# Error Handling

> 本项目错误处理的真实约定：`enum Error` 分层定义与跨层转换点。

---

## Error Types per Layer

<!-- 每一层定义了哪些 `enum ...Error`（如 `NetworkError` / `RepositoryError` / `DomainError`）？各自落在哪个目录？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Cross-Layer Conversion

<!-- 错误在跨层时如何转换（Infrastructure 错误 → Domain 错误）？转换点在哪里、用什么方式（init / mapError）保留根因？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Propagation (throws / Result)

<!-- 错误如何向上传播（`async throws` vs `Result`）？本项目统一选哪种、为什么？何时吞错、何时上抛？ -->

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## User-Facing Presentation

<!-- 错误最终如何呈现给用户（落到 ViewModel error 态、文案映射、本地化）？哪些错误不应直接展示原始信息？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)

---

## Common Mistakes

<!-- 错误处理上反复踩过的坑（裸 `try?` 吞错、底层错误直透 UI、丢失根因、未分层等）？ -->

```swift
// WRONG:

// CORRECT:
```

(To be filled by bootstrap — 见 00-bootstrap-guidelines 任务)
