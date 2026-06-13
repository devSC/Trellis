# 【PRD】Trellis 跨平台扩展方案 - Flutter/HTML/iOS/Android 四大项目类型支持

**发布日期**: 2026-06-13  
**优先级**: P0（架构级特性）  
**所有者**: devSC  
**受众**: Trellis 开发团队、Guru 客户端团队  

---

## 问题陈述

当前 Trellis guru/main 分支完全支持 Flutter 项目类型的初始化与配置，但缺乏对其他主流项目类型（HTML 前端、iOS 原生、Android 原生）的支持。

**现有困局**：
1. **项目类型硬编码** - 项目类型检测与工作流选择散落在 `init.ts` 与 `workflow-resolver.ts` 中，添加新项目类型需修改核心代码（500行 + 5天）
2. **规范集耦合** - guru-flutter-client spec 与 guru-client 工作流强绑定，无法独立复用或定制化
3. **适配器缺失** - 无清晰的平台适配机制，Codex/Claude Code 特定逻辑混杂在初始化流程中
4. **Skill 管理混乱** - 技能集合在 guru-template/ 中散乱存放，无中心管理与跨项目类型的复用
5. **扩展瓶颈** - 每添加新项目类型或新平台都需改动核心代码，回归风险高

**业务影响**：
- Guru 团队需支持多技术栈（Flutter 移动端、HTML 网页端、iOS/Android 原生）
- 当前架构制约了快速迭代与新项目类型接入
- 新开发者难以理解 init 逻辑，维护成本高

---

## 解决方案

采用 **Registry-Driven Architecture + 2D矩阵设计**，将项目类型、工作流、规范、技能等核心概念转化为可声明、可版本控制的注册表，从 hardcoding 转向配置驱动。

### 核心设计

#### 1. 四个声明式注册表

**ProjectTypeRegistry** - 项目类型定义中心
```
flutter: {
  detection: { files: [pubspec.yaml, ...] },
  defaultWorkflow: "guru-client",
  specTemplateId: "guru-flutter-client",
  platformAdapters: { claude: {...}, codex: {...} }
}

html: { detection, defaultWorkflow, specTemplateId, ... }
ios: { detection, defaultWorkflow, specTemplateId, ... }
android: { detection, defaultWorkflow, specTemplateId, ... }
```

**WorkflowRegistry** - 工作流定义与项目类型映射
```
native: { applicableTo: ["flutter", "html", "ios", "android"], ... }
guru-client: { applicableTo: ["flutter"], ... }
web-component-driven: { applicableTo: ["html"], ... }
```

**SpecRegistry** - 项目规范集与模块化
```
guru-flutter-client: { projectTypes: ["flutter"], modules: [...] }
spec-html-web: { projectTypes: ["html"], modules: [conventions-shared, ...] }
spec-ios-swift: { projectTypes: ["ios"], modules: [...] }
```

**SkillRegistry** - Skill 中心库与跨项目类型适配
```
requirement-writing: { applicableProjectTypes: ["*"], ... }
flutter-implementation-guru-writing: { applicableProjectTypes: ["flutter"], ... }
html-component-writing: { applicableProjectTypes: ["html"], ... }
```

#### 2. 项目类型 × 平台 2D 矩阵

```
                Claude Code    Codex
Flutter         ✓ guru-client  ✓ native
HTML            ✓ component    ○ native
iOS             ✓ native       ○ native
Android         ✓ native       ○ native
```

每个矩阵单元独立配置 → 无限扩展能力，无需修改核心代码。

#### 3. 双层适配器模式

**PlatformAdapters** (横轴 - 开发平台)：
- ClaudeCodeAdapter: settings.json 配置 + SessionStart/PreToolUse hooks
- CodexAdapter: AGENTS.md 生成 + hooks.json 配置
- （Cursor 不支持）

**ProjectTypeAdapters** (纵轴 - 项目类型)：
- FlutterAdapter: pubspec 检查、包保管
- HtmlAdapter: eslint/prettier 配置生成
- IosAdapter: Podfile 验证、CocoaPods 检查
- AndroidAdapter: gradle 检查、SDK 版本验证

**收益**：平台逻辑与项目类型逻辑完全分离 → 新增平台或项目类型无需修改彼此的代码。

#### 4. Init.ts 改造为清晰的 6 步流程

```
Step 1: 检测项目类型 → ProjectTypeResolver.detect() → PROJECT_TYPES[detected]
Step 2: 选择/验证工作流 → WorkflowResolver.validate() → WORKFLOWS[selected]
Step 3: 解析规范 → SpecResolver.resolve() → SPECS[typeDef.specTemplateId]
Step 4: 解析 Skills → SkillResolver.getSkillsFor() → SKILLS[...filtered]
Step 5: 创建适配器 → AdapterFactory.createPlatformAdapter() + createProjectTypeAdapter()
Step 6: 生成文件 → generateFilesWithAdapters(context)
```

从 monolithic 初始化逻辑 → 清晰的编排流程 → 易维护、易测试。

---

## 用户故事

### 用户故事分类：开发者视角

#### 架构基础 (Phase 1, Weeks 1-2)
1. 作为 Trellis 开发者，我需要将项目类型定义转化为类型安全的注册表，以便代码可以自动验证和文档化所有支持的项目类型
2. 作为 Trellis 开发者，我需要为四个注册表（ProjectType、Workflow、Spec、Skill）创建清晰的 TypeScript 接口，使新入职的开发者能快速理解扩展机制
3. 作为 Trellis 开发者，我需要实现 ProjectTypeResolver，使其能从目录结构自动检测项目类型（Flutter/HTML/iOS/Android），检测准确率 >95%
4. 作为 Trellis 开发者，我需要实现 WorkflowResolver，使其能验证工作流与项目类型的适配性，防止不兼容的组合
5. 作为 Trellis 开发者，我需要实现 SpecResolver，使其能从项目类型注册表自动关联正确的规范集
6. 作为 Trellis 开发者，我需要实现 SkillResolver，使其能根据项目类型 + 开发平台 + 阶段过滤出相关 Skills
7. 作为 Trellis 开发者，我需要为注册表添加 30%+ 的单元测试覆盖，确保基础架构的正确性

#### 核心改造 (Phase 2, Weeks 3-5)
8. 作为 Trellis 开发者，我需要改造 init.ts 为 6 步流程，使其与注册表系统集成，同时保持 Flutter 工作流的 100% 向后兼容性
9. 作为 Trellis 开发者，我需要创建 AdapterFactory，使其能工厂模式创建平台适配器与项目类型适配器，降低耦合度
10. 作为 Trellis 开发者，我需要实现 ClaudeCodeAdapter，使其能根据项目类型定制 settings.json 与 hooks 配置
11. 作为 Trellis 开发者，我需要实现 CodexAdapter，使其能根据项目类型定制 AGENTS.md 与 hooks.json 配置
12. 作为 Trellis 开发者，我需要为 init 改造编写集成测试，覆盖 Flutter + Claude Code / Codex 两条主流路径
13. 作为 Trellis 开发者，我需要验证 apply.sh 14 个测试场景全部通过，证明零回归
14. 作为 Trellis 开发者，我需要为改造后的 init 流程编写 70%+ 集成测试覆盖，确保适配器工厂、解析器、改造逻辑的正确性
15. 作为 Trellis 开发者，我需要测试边界情况（多类型指示符、未知类型、不兼容工作流等），确保错误提示清晰有用

#### HTML 支持 (Phase 3, Week 6)
16. 作为 Trellis 开发者，我想在 ProjectTypeRegistry 中为 HTML 项目类型定义检测规则（package.json + index.html），使 HTML 项目能自动识别
17. 作为 Trellis 开发者，我想为 HTML 项目类型注册 native 与 web-component-driven 两个工作流选项
18. 作为 Trellis 开发者，我想为 HTML 项目类型注册 spec-html-web 规范集，包含 Web 特定的约定与指南
19. 作为 Trellis 开发者，我想为 HTML 项目类型注册 html-component-writing 与 web-css-architecture Skill
20. 作为 Trellis 开发者，我想实现 HtmlAdapter，使其能生成 .eslintrc.json、.prettierrc.json 等 Web 特定配置
21. 作为 Trellis 开发者，我想为 HTML 初始化编写端到端测试，验证 `trellis init --html --claude` 工作流程完整

#### iOS/Android 支持 (Phase 4, Week 7)
22. 作为 Trellis 开发者，我想在 ProjectTypeRegistry 中为 iOS 项目类型定义检测规则（Podfile + *.xcodeproj），使 iOS 项目能自动识别
23. 作为 Trellis 开发者，我想为 iOS 项目类型注册 native 工作流与 spec-ios-swift 规范集
24. 作为 Trellis 开发者，我想为 iOS 项目类型注册 ios-swift-implementation Skill
25. 作为 Trellis 开发者，我想实现 IosAdapter，使其能验证 Podfile 存在性与 CocoaPods 环境
26. 作为 Trellis 开发者，我想为 iOS 初始化编写端到端测试，验证 `trellis init --ios --claude` 工作流程完整
27. 作为 Trellis 开发者，我想在 ProjectTypeRegistry 中为 Android 项目类型定义检测规则（build.gradle + gradle.properties），使 Android 项目能自动识别
28. 作为 Trellis 开发者，我想为 Android 项目类型注册 native 工作流与 spec-android-kotlin 规范集
29. 作为 Trellis 开发者，我想为 Android 项目类型注册 android-kotlin-implementation Skill
30. 作为 Trellis 开发者，我想实现 AndroidAdapter，使其能验证 build.gradle 存在性与 Gradle 版本
31. 作为 Trellis 开发者，我想为 Android 初始化编写端到端测试，验证 `trellis init --android --claude` 工作流程完整

#### 扩展能力（所有阶段）
32. 作为新加入的 Trellis 开发者，我想快速学习如何添加新项目类型（按 5 步模板：注册表 + adapter + 测试），预计学习曲线 < 2 天
33. 作为 Trellis 开发者，我想快速学习如何添加新开发平台（创建新 PlatformAdapter），预计实现时间 < 1 天
34. 作为 Trellis 开发者，我想通过代码注释与 JSDoc 快速了解注册表结构，无需文档翻查

#### 长期价值
35. 作为 Guru 团队产品经理，我想支持 Flutter + HTML + iOS + Android 四大项目类型，以满足团队多技术栈需求
36. 作为 Guru 团队产品经理，我想通过架构升级大幅降低新项目类型的接入成本（从 5 天→4 小时，30 倍加速），为未来扩展 Node.js/Python/Go 等语言奠基
37. 作为 Guru 团队技术负责人，我想通过注册表机制实现项目类型与平台的 2D 矩阵管理，降低系统耦合度与维护成本

---

## 实现决策

### 架构决策

**决策 1: Registry-Driven 而非 If-Else Hardcoding**

现状: init.ts 中存在多处项目类型与工作流的分支判断，导致新增项目类型需修改核心逻辑。

决策: 将项目类型、工作流、规范、Skill 转化为声明式注册表，通过 TypeScript 类型系统保证一致性，通过 Resolver 类实现统一的查询接口。

原因: 
- 声明式配置易于阅读、维护和版本管理
- TypeScript 接口自动文档化支持的配置选项
- 新增项目类型只需在注册表中添加 50 行配置，无需修改核心代码
- 降低回归风险（改动集中在注册表，核心逻辑保持稳定）

**决策 2: 2D 矩阵（项目类型 × 平台）而非分立的适配层**

现状: 各项目类型与平台的适配散落在不同模块，难以全局管理。

决策: 采用 2D 矩阵设计，横轴代表平台（Claude Code / Codex），纵轴代表项目类型（Flutter / HTML / iOS / Android），矩阵每个单元可独立配置。

原因:
- 清晰的扩展维度：新增平台仅需创建 PlatformAdapter，新增项目类型仅需创建 ProjectTypeAdapter
- 无交叉耦合：平台适配器与项目类型适配器完全独立
- 易于可视化与决策：矩阵形式直观展示支持覆盖范围

**决策 3: 双层适配器模式**

现状: settings.json 配置与项目类型检查混杂在 init.ts 中。

决策: 
- PlatformAdapters: 处理平台特定的配置（settings.json for Claude Code, AGENTS.md for Codex）
- ProjectTypeAdapters: 处理项目类型特定的检查与文件生成（eslint for HTML, Podfile for iOS）

原因:
- 关注点分离：每层适配器只关注自己的职责
- 可测试性：每个适配器可独立单元测试
- 可扩展性：新增平台或项目类型无需跨越已有的适配器逻辑

**决策 4: Init.ts 改造为 6 步流程而非逐行改造**

现状: init.ts 是一个超过 2000 行的单体函数，逻辑混杂，难以维护。

决策: 将初始化流程重构为 6 个清晰的步骤，每步负责一个明确的职责：
1. 检测项目类型
2. 选择/验证工作流
3. 解析规范集
4. 解析 Skills
5. 创建适配器
6. 生成文件

原因:
- 清晰的编排流程，易于理解与维护
- 每步可独立测试与验证
- 便于未来对流程的扩展（如添加验证步骤、前置检查）

### 模块决策

**模块清单**

| 模块 | 职责 | 新增/改造 | 测试覆盖 |
|------|------|---------|--------|
| ProjectTypeRegistry | 项目类型声明 | 新增 | 单元 30% |
| WorkflowRegistry | 工作流声明 | 新增 | 单元 30% |
| SpecRegistry | 规范集声明 | 新增 | 单元 30% |
| SkillRegistry | Skill 声明 | 新增 | 单元 30% |
| ProjectTypeResolver | 项目类型检测 | 新增 | 单元 + 集成 |
| WorkflowResolver | 工作流解析与验证 | 改造 | 单元 + 集成 |
| SpecResolver | 规范集解析 | 新增 | 单元 |
| SkillResolver | Skill 过滤 | 新增 | 单元 |
| AdapterFactory | 适配器创建 | 新增 | 单元 |
| ClaudeCodeAdapter | Claude Code 平台配置 | 新增 | 集成 |
| CodexAdapter | Codex 平台配置 | 新增 | 集成 |
| FlutterAdapter | Flutter 项目类型配置 | 新增 | 集成 |
| HtmlAdapter | HTML 项目类型配置 | 新增 (Phase 3) | 集成 |
| IosAdapter | iOS 项目类型配置 | 新增 (Phase 4) | 集成 |
| AndroidAdapter | Android 项目类型配置 | 新增 (Phase 4) | 集成 |
| init.ts 改造 | 6 步流程编排 | 改造 核心 | 集成 70% |

**深模块识别**

深模块（通过简单接口封装复杂功能、极少变化）:
- **ProjectTypeResolver**: 简单接口 `detect(cwd)` → 完整的检测逻辑，检测规则由注册表定义，不需频繁改动
- **Resolver 系列** (Workflow/Spec/Skill): 统一的查询接口，内部逻辑由注册表驱动，易于维护
- **AdapterFactory**: 简单工厂接口 `create(platform, context)` 和 `createTypeAdapter(type)` → 完整的适配器创建逻辑，无需频繁改动

浅模块（当前应避免）:
- 直接操作注册表的代码（应通过 Resolver 间接访问）
- init.ts 中的平台特定逻辑（应移入 PlatformAdapters）

### 技术决策

**TypeScript 接口设计**

关键接口原型（来自 DETAILED_IMPLEMENTATION_PLAN.md 实现分析）:

```typescript
export interface ProjectTypeDefinition {
  id: string;                         // "flutter" | "html" | "ios" | "android"
  detection: DetectionConfig;
  defaultWorkflow: string;
  specTemplateId: string;
  bundledSpec: boolean;
  platformAdapters: Record<string, PlatformAdapterConfig>;
  tags: string[];
}

export interface WorkflowDefinition {
  id: string;
  applicableTo: string[];             // ["flutter"] | ["html"] | ...
  phases: string[];
  source: "bundled" | "marketplace";
  gatePoints: "none" | "light" | "full";
}

export interface SpecTemplate {
  id: string;
  projectTypes: string[];
  modules: SpecModule[];              // 模块化规范复用
  source: "bundled" | "marketplace";
  structure: SpecFileStructure;
}

export interface SkillDefinition {
  id: string;
  applicableProjectTypes: string[];   // ["*"] | ["flutter"] | ...
  applicablePlatforms: string[];
  category: "writing" | "review" | "utility" | "sop";
  phase?: string;
}
```

**向后兼容约束**

- Flutter 项目自动检测不变
- guru-client 工作流默认选择不变
- apply.sh 14 个测试场景 100% 通过（必要条件，否则视为回归）
- 现有文档、脚本、工具无任何改动

**Skill 管理策略**

- 通用 Skill 使用 `applicableProjectTypes: ["*"]` 标记
- 项目类型特定 Skill 使用 `applicableProjectTypes: ["flutter"]` 等具体类型
- 平台不兼容的 Skill 通过 `applicablePlatforms` 过滤
- Skill 解析器 (SkillResolver) 根据项目类型 + 平台 + 阶段三维过滤

**规范集模块化策略**

- 共通规范模块（如 `conventions-shared`）通过 `modules[].reusableAcross` 声明适用项目类型
- 项目类型特定模块（如 `harness-flutter`）仅适用于单一项目类型
- SpecResolver 能查询 `getReusableModules(projectType)` 返回跨项目可用的模块

---

## 测试决策

### 好的测试标准

- **外部行为优先**: 测试初始化后的文件结构、配置内容，而非内部函数实现细节
- **集成测试覆盖关键路径**: Flutter + Claude Code、HTML + Claude Code、iOS + Codex 等主流组合必须有集成测试
- **向后兼容测试非可选**: apply.sh 14 个场景全过是必要条件，不能作为选项
- **边界情况与错误路径**: 测试项目类型检测失败、不兼容工作流选择、缺失文件等错误情况
- **快照测试**: 对于生成的文件内容（settings.json、AGENTS.md）可用快照测试，变更时需人工审核

### 测试覆盖计划

| 模块 | 测试类型 | 覆盖率目标 | 先例 |
|------|---------|-----------|------|
| 注册表 (Phase 1) | 单元 | 30% | project-types.test.ts |
| Resolver (Phase 2) | 单元 + 集成 | 70% | workflow-resolver.test.ts |
| 适配器 (Phase 2) | 集成 | 70% | platform-adapter.integration.test.ts |
| init.ts 改造 (Phase 2) | 集成 | 70% | init-with-registry.test.ts, backward-compat-full.test.ts |
| 新项目类型 (Phase 3/4) | 集成 | 85% | html-init.integration.test.ts, mobile-init.integration.test.ts |
| 边界情况 | 集成 | 85% | edge-cases.integration.test.ts |

### 既有测试先例

参考现有测试模式：
- **向后兼容验证**: 使用 guru-template/overlay/tests/apply_test.sh（14 个场景）作为向后兼容的终极验证
- **集成测试结构**: packages/cli/test/integration/ 下使用真实目录与 Git 仓库进行端到端测试
- **Resolver 单元测试**: packages/cli/test/utils/ 下对 resolver 类的单元测试，模拟注册表数据

### 测试范围

需测试的模块：
- ProjectTypeResolver (自动检测准确率 >95%)
- WorkflowResolver (工作流与项目类型的兼容性验证)
- SpecResolver (规范集正确关联)
- SkillResolver (跨维度过滤逻辑)
- AdapterFactory (平台与项目类型适配器的正确创建)
- ClaudeCodeAdapter (settings.json 与 hooks 配置生成)
- CodexAdapter (AGENTS.md 与 hooks.json 配置生成)
- init.ts 改造 (6 步流程的编排与异常处理)

不测试的细节：
- 注册表数据本身（通过类型系统保证合法性）
- 底层文件系统操作（由现有 file-writer.ts 保证）
- 网络请求（使用 mock 或 fixture）

---

## 范围外

以下内容在本 PRD 范围外：

1. **Cursor 平台支持** - 仅支持 Claude Code 与 Codex，Cursor 支持留待后续
2. **其他编程语言项目类型** (Node.js, Python, Go, Rust) - 仅支持 Flutter/HTML/iOS/Android，其他语言留待后续基于本架构扩展
3. **Marketplace 子模块初始化** - docs-site 与 marketplace submodules 的初始化或网络 clone 由现有机制处理，本 PRD 不涉及
4. **性能优化** - 初始化性能优化（如并行化、缓存）留待后续迭代
5. **国际化** - 用户界面消息的多语言支持留待后续
6. **设置向导** - 交互式初始化向导留待后续（本 PRD 仅涉及自动检测与默认选择）

---

## 进一步说明

### 为什么这个架构解决了问题

1. **从 hardcoding 到配置化**: 项目类型、工作流、规范不再散落在代码中，而是集中在类型安全的注册表，新增项目类型无需修改核心逻辑
2. **降低耦合度**: 2D 矩阵设计确保平台逻辑与项目类型逻辑分离，新增任一维度不影响另一维度
3. **提升开发效率**: 添加新项目类型从 5 天→4 小时（30 倍加速），基于简明的 5 步模板
4. **确保可维护性**: 清晰的 6 步 init 流程、深模块 (Resolver) 的简单接口、完整的单元与集成测试
5. **保证向后兼容**: Flutter 工作流、现有脚本、文档完全不变；apply.sh 14 场景强制全过

### 实施阶段与风险

| 阶段 | 周数 | 风险 | 缓解 |
|------|------|------|------|
| Phase 1: 架构 | 1-2 | 低 | 类型系统、单元测试验证 |
| Phase 2: 改造 init | 3-5 | 中 | 向后兼容测试、逐步集成、版本控制 |
| Phase 3: HTML | 6 | 低 | 复用 5 步模板、E2E 测试 |
| Phase 4: iOS+Android | 7 | 低 | 复用 HTML 模板、E2E 测试 |

**低风险原因**: 
- 清晰的分阶段计划，每阶段可独立验证
- 向后兼容约束明确，apply.sh 14 场景强制检查
- Flutter 逻辑保持不变，新增项目类型相对独立
- 任何时刻可回滚（Git 版本控制）

### 预期交付时间与资源

- **时间**: 7 周（1-2 名全职工程师）
- **代码行数**: ~3940 行（新增 2500 + 改造 800 + 测试 640）
- **测试投入**: 整体测试覆盖从 70%（Phase 2 后）→ 85%（Phase 4 后）
- **维护成本**: 长期降低（后续新项目类型接入成本 1 天内，复用模板）

### 成功标准

| 阶段 | 成功标准 |
|------|--------|
| Phase 1 | 4 个注册表接口清晰，Flutter 定义 100% 完整，单元测试 30%+ |
| Phase 2 | init.ts 改造完成，apply.sh 14/14 通过，集成测试 70%+ |
| Phase 3 | `trellis init --html --claude` 成功，E2E 测试通过 |
| Phase 4 | `trellis init --ios/android --claude` 成功，全量 E2E 测试 85%+ 覆盖 |

---

**关联文档**:
- DETAILED_IMPLEMENTATION_PLAN.md - 周级任务分解与时间估算
- CROSS_PLATFORM_IMPLEMENTATION.md - 实现细节与 API 参考
- CROSS_PLATFORM_ARCHITECTURE.md - 架构设计与问题分析

