# 大型需求文档组织与管理

说明：本文补充“大型文档拆分与版本管理”实践；文档体系定义必须以同级标准包 `../requirement-doc-standard/references/requirement-structure-single-source.md` 为单一来源（从 requirement-writing Skill 目录解析），由入口 `SKILL.md` 负责定位并读取标准包。

在以下场景读取本文件：
- 单份需求文档已经过大，难以继续维护。
- 需求需要版本管理、变更记录或多模块并行编辑。
- 用户明确要求输出目录结构、拆分方案或版本策略。

## 模块化文档结构（推荐拆分形态）

推荐拆分方式（可选）：

```text
requirements/
├── README.md
├── requirement-main.md
├── requirement-api.md                # 若适用
├── requirement-cli-command.md        # 若适用
├── requirement-non-functional.md
├── modules/
│   ├── requirement-auth.md
│   ├── requirement-home.md
│   └── requirement-settings.md
├── changes/
│   ├── change-log.md
│   └── changes/
├── templates/
└── assets/
```

版本化场景可在 `versions/` 下按同一结构分目录维护。

## 各文档职责

- `README.md`：导航、索引、追踪矩阵、版本入口。
- `requirement-main.md`：第一章与第二章入口组织主定义（摘要层骨架；有 UI 时包含页面组织结构）。
- `requirement-[module].md` 或等价聚合详细文档：第三章起页面详细主定义（规则层）。

说明：
- 详细章节可先聚合在单文档中，不强制立即拆分到 `modules/`。
- 当体量、并行冲突或评审可维护性问题出现时，再触发拆分。
- `requirement-api.md`：API 契约与交互主定义（若适用）。
- `requirement-cli-command.md`：CLI Command 契约主定义（若适用）。
- `requirement-non-functional.md`：非功能主定义。

## 双时态下的重复事实策略

### 阶段写作时态

- 允许 `requirement-main.md` 第二章入口摘要与详细页面/API/CLI 文档暂时并存同一业务事实。
- 约束：`requirement-main.md` 只可保留摘要，不可定义规则细节。

### 完成收敛时态

- 必须执行“重复事实清理”：
  - 第二章删去规则细节，只保留摘要与链接。
  - 详细页面/API（若适用）/CLI（若适用）/非功能保留规则主定义。
- 若清理后仍有双主定义，不得给出“可进入下一阶段”结论。

## 单一来源与单向维护

- 同一契约（字段定义、状态口径、异常边界）只在一个主文档维护。
- API/CLI 适用性判定见标准包 `requirement-structure-single-source.md` 的“API/CLI 适用标准”。
- 通用规范只定义“规则与适用条件”，不维护消费方清单。
- 消费方文档显式声明“遵循某规范”并链接主定义位置。

## 版本与变更管理

执行方式：
1. 每个版本在 `versions/` 下创建独立目录（可选）。
2. 更新版本入口与版本矩阵。
3. 在 `changes/change-log.md` 增加汇总条目。
4. 在 `changes/changes/` 创建详细变更说明。
5. 每轮“完成收敛”作为独立变更记录。

## 与审核技能的闭环

```text
$requirement-writing（阶段写作）
  -> 写作内置轻量自检 / 必要时阶段确认
  -> 完成收敛清理
  -> $requirement-review（门禁审核）
  -> 若存在阻断问题，回到 writing 修正；否则进入下一阶段
```

## 最小样例入口

- 最小示例：`../requirement-doc-standard/references/examples/unique-structure-minimal/`（从 requirement-writing Skill 目录解析）
