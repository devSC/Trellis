# Trellis 跨平台扩展架构分析与规划

## 一、当前架构分析

### 1.1 核心逻辑现状

#### A. 模板系统（Template System）
```
packages/cli/src/templates/
├── trellis/              # 通用 native 工作流
│   ├── workflow.md
│   ├── scripts/
│   ├── agents/
│   └── config.yaml
├── guru/                 # Guru 定制（Flutter优先）
│   ├── workflow.md       # 五阶段工作流
│   ├── specs/
│   │   └── guru-flutter-client/
│   │       ├── conventions/
│   │       ├── guides/
│   │       └── harness/
│   └── index.ts          # bundled 导出

特点:
  ✗ Flutter 硬编码在规范集里 (guru-flutter-client spec)
  ✗ 五阶段工作流假设为单一形态
  ✗ 没有跨项目类型的抽象层
  ✗ 规范与工作流耦合在一起
```

#### B. 初始化流程（Init Pipeline）
```
packages/cli/src/commands/init.ts
  ├── detectProject()              # 项目检测 (Flutter/Node/Python...)
  │   └── packages/cli/src/utils/project-detector.ts
  │       ├── Cargo.toml (Rust)
  │       ├── go.mod (Go)
  │       ├── pyproject.toml (Python)
  │       ├── package.json (Node)
  │       └── pubspec.yaml (Flutter) ← 唯一有完整规范支持
  │
  ├── Workflow Selection            # 工作流选择 (native / guru-client)
  │   └── packages/cli/src/utils/workflow-resolver.ts
  │       ├── NATIVE_WORKFLOW_ID
  │       └── GURU_CLIENT_WORKFLOW_ID (Flutter hardcoded)
  │
  ├── Spec Template Resolution      # 规范模板分辨率
  │   └── packages/cli/src/utils/template-fetcher.ts
  │       ├── marketplace lookup
  │       └── bundled check (仅guru-flutter-client)
  │
  └── File Generation               # 文件生成
      └── packages/cli/src/configurators/
          ├── shared.ts (JSON merge)
          ├── claude.ts (Claude Code)
          ├── codex.ts (Codex)
          └── ... (平台适配层)
```

#### C. 平台适配（Platform Adapters）
```
packages/cli/src/configurators/
├── shared.ts           # 跨平台通用: mergeJsonDefaults, JSON处理
├── claude.ts           # Claude Code (settings.json + hooks)
├── codex.ts            # Codex (AGENTS.md hooks)
├── copilot.ts          # GitHub Copilot
├── cursor.ts           # Cursor
└── ...

特点:
  ✓ 平台适配层分离得较好
  ✗ 无跨项目类型的定制化钩子
  ✗ Skill/Agent 以 hardcode 形式存在于模板
  ✗ 没有"项目类型 × 平台"的二维矩阵概念
```

#### D. 规范管理（Spec Management）
```
当前: guru-template/
  └── specs/
      └── guru-flutter-client/  (唯一完整的规范集)
          ├── README.md
          ├── RECONCILE.md
          ├── conventions/        (项目约定 + 槽位)
          ├── guides/             (可用性指南)
          └── harness/            (实现细则)

问题:
  ✗ 规范与项目类型强耦合
  ✗ 无"规范模块化"机制（如何复用部分规范？）
  ✗ 没有规范版本管理
  ✗ 规范与工作流选择没有关联
```

### 1.2 扩展瓶颈

| 维度 | 当前状态 | 扩展瓶颈 |
|------|---------|---------|
| **项目类型检测** | Flutter hardcoded + 通用检测 | 新类型需修改 project-detector.ts |
| **工作流选择** | NATIVE_WORKFLOW_ID + GURU_CLIENT (Flutter) | 每种项目类型需新增工作流ID |
| **规范集管理** | guru-flutter-client 唯一完整 | 需复制 16 个文件结构 × N 项目类型 |
| **Skills/Agents** | 在 guru-template/ 中与规范混在一起 | 无跨类型的 skill 抽象 |
| **平台适配** | 适配层分离，但无项目类型感知 | 无法针对项目类型定制 hook |
| **模板同步** | sync:guru 只同步单一规范 | 多规范时维护复杂 |

---

## 二、跨平台扩展方案

### 2.1 核心设计原则

```
1. 分离关注点（Separation of Concerns）
   工作流 ≠ 规范 ≠ Skill ≠ 平台适配
   
2. 项目类型 × 平台二维矩阵
   - 纵轴: 项目类型 (Flutter, HTML, iOS, Android, Node...)
   - 横轴: 开发平台 (Claude Code, Codex, Cursor...)
   - 每个交点可独立定制
   
3. 规范模块化
   - 通用规范: conventions-shared, guides-patterns
   - 类型特定: conventions-flutter, harness-ios
   - 平台特定: tools-claude-code, tools-xcode
   
4. 向后兼容
   - 现有 guru-flutter-client 不破坏
   - 新类型渐进式接入
   - 版本管理清晰
```

### 2.2 提议的新架构

#### A. 项目类型系统（Project Type Registry）

```typescript
// packages/cli/src/types/project-types.ts

export interface ProjectTypeDefinition {
  id: string;                          // "flutter", "html", "ios", "android"
  name: string;                        // "Flutter App", "Web (HTML/CSS/JS)"
  icon?: string;
  
  detection: {
    files: string[];                   // [pubspec.yaml, package.json, ...] 优先级顺序
    dirsToCheck?: string[];
    commandsToRun?: { cmd: string; versionMinimum?: string }[];
  };
  
  defaultWorkflow: string;             // "native" / "guru-client" / "mobile-dev"
  availableWorkflows: string[];        // 该类型支持的工作流列表
  
  specTemplateId: string;              // "guru-flutter-client" / "spec-html-web" / "spec-ios-swift"
  bundledSpec?: boolean;               // 是否内置规范
  
  platformAdapters: {
    [platform: string]: {              // "claude" / "codex" / "cursor"
      hooks?: string[];                // 特定的 hook 类型
      requiredFiles?: string[];        // 必需文件清单
      skillOverrides?: Record<string, string>;
    };
  };
  
  tags: string[];                      // ["mobile", "native", "web", "ai-native"]
}

// 注册表
export const PROJECT_TYPES: Record<string, ProjectTypeDefinition> = {
  flutter: {
    id: "flutter",
    name: "Flutter App",
    detection: {
      files: ["pubspec.yaml", "ios/Runner.xcodeproj", "android/app/build.gradle"],
    },
    defaultWorkflow: "guru-client",
    availableWorkflows: ["native", "guru-client", "mobile-tdd"],
    specTemplateId: "guru-flutter-client",
    bundledSpec: true,
    platformAdapters: {
      claude: {
        hooks: ["SessionStart", "PreToolUse"],
        skillOverrides: { "pattern-exploration": "flutter-pattern-exploration" },
      },
      codex: {
        hooks: ["PreToolUse"],
      },
    },
    tags: ["mobile", "native", "cross-platform"],
  },
  
  html: {
    id: "html",
    name: "Web (HTML/CSS/JS/TS)",
    detection: {
      files: ["package.json", "index.html", "vite.config.js"],
    },
    defaultWorkflow: "native",
    availableWorkflows: ["native", "web-component-driven", "spa-tdd"],
    specTemplateId: "spec-html-web",
    bundledSpec: false,  // marketplace 获取，或后续 bundled
    platformAdapters: {
      claude: {
        hooks: ["SessionStart", "PreToolUse"],
        skillOverrides: { "flutter-implementation-guru-writing": "html-component-writing" },
      },
    },
    tags: ["web", "frontend", "component-driven"],
  },
  
  ios: {
    id: "ios",
    name: "iOS (Swift/Objective-C)",
    detection: {
      files: ["ios/Podfile", "ios/Podfile.lock", "ios/*.xcodeproj"],
    },
    defaultWorkflow: "mobile-native-dev",
    availableWorkflows: ["native", "mobile-native-dev"],
    specTemplateId: "spec-ios-swift",
    bundledSpec: false,
    platformAdapters: {
      claude: {
        hooks: ["SessionStart", "PreToolUse"],
        requiredFiles: ["ios/Podfile"],
      },
    },
    tags: ["mobile", "native", "ios"],
  },
  
  android: {
    id: "android",
    name: "Android (Kotlin/Java)",
    detection: {
      files: ["android/build.gradle", "android/app/build.gradle"],
    },
    defaultWorkflow: "mobile-native-dev",
    availableWorkflows: ["native", "mobile-native-dev"],
    specTemplateId: "spec-android-kotlin",
    bundledSpec: false,
    platformAdapters: {
      claude: {
        hooks: ["SessionStart", "PreToolUse"],
        requiredFiles: ["android/build.gradle"],
      },
    },
    tags: ["mobile", "native", "android"],
  },
};
```

#### B. 工作流系统（Workflow Registry）

```typescript
// packages/cli/src/types/workflows.ts

export interface WorkflowDefinition {
  id: string;                          // "native", "guru-client", "mobile-tdd"
  name: string;
  description: string;
  
  applicableTo: string[];              // ["flutter", "android", "ios"] 项目类型
  phases: string[];                    // ["planning", "design", "implementation", "review"]
  
  source: "bundled" | "marketplace";
  bundledPath?: string;                // src/templates/workflows/...
  marketplaceId?: string;
  
  gatePoints: "none" | "light" | "full";  // 人工 gate 级别
  teamTooling?: string;                   // "none" / "claude-code" / "codex" / "both"
}

export const WORKFLOWS: Record<string, WorkflowDefinition> = {
  native: {
    id: "native",
    name: "Trellis Native Workflow",
    description: "General-purpose 5-phase workflow",
    applicableTo: ["flutter", "html", "ios", "android", "node", "python"],
    phases: ["planning", "in_progress", "review", "done"],
    source: "bundled",
    bundledPath: "src/templates/trellis/workflow.md",
    gatePoints: "none",
    teamTooling: "both",
  },
  
  "guru-client": {
    id: "guru-client",
    name: "Guru Client Workflow",
    description: "Flutter-optimized 5-phase SDD workflow",
    applicableTo: ["flutter"],
    phases: ["planning", "in_progress", "review", "done"],
    source: "bundled",
    bundledPath: "src/templates/guru/workflow.md",
    gatePoints: "full",
    teamTooling: "both",
  },
  
  "mobile-native-dev": {
    id: "mobile-native-dev",
    name: "Mobile Native Development (iOS/Android)",
    description: "Native mobile 5-phase workflow",
    applicableTo: ["ios", "android"],
    phases: ["planning", "design", "implementation", "review"],
    source: "marketplace",
    marketplaceId: "mobile-native-dev",
    gatePoints: "light",
    teamTooling: "both",
  },
};
```

#### C. 规范系统（Spec Registry）

```typescript
// packages/cli/src/types/specs.ts

export interface SpecTemplate {
  id: string;                          // "guru-flutter-client", "spec-html-web"
  name: string;
  version: string;                     // semantic versioning
  
  projectTypes: string[];              // ["flutter"]
  platforms?: string[];                // ["claude", "codex"] 可选，缺省=all
  
  source: "bundled" | "marketplace";
  bundledPath?: string;
  marketplaceId?: string;
  
  structure: SpecFileStructure;        // 文件树定义
  modules: SpecModule[];               // 可选的模块化规范
  
  maintainer?: {
    team: string;
    contact?: string;
  };
}

export interface SpecFileStructure {
  required: string[];                  // ["README.md", "conventions/index.md"]
  optional?: string[];                 // ["RECONCILE.md"]
  directories: Record<string, DirectorySpec>;
}

export interface DirectorySpec {
  purpose: string;                     // "项目约定模板"
  files: string[];
  editable: boolean;                   // 用户是否应修改
}

export interface SpecModule {
  id: string;                          // "conventions-shared", "harness-flutter"
  name: string;
  reusableAcross: string[];            // ["flutter", "ios", "android"]
  files: string[];
}

export const SPECS: Record<string, SpecTemplate> = {
  "guru-flutter-client": {
    id: "guru-flutter-client",
    name: "Guru Flutter Client Spec",
    version: "1.0.0",
    projectTypes: ["flutter"],
    platforms: ["claude", "codex"],
    source: "bundled",
    bundledPath: "src/templates/guru/specs/guru-flutter-client",
    structure: {
      required: [
        "README.md",
        "conventions/index.md",
        "guides/index.md",
        "harness/index.md",
      ],
      optional: ["RECONCILE.md"],
      directories: {
        conventions: {
          purpose: "项目约定 + 槽位模板",
          files: ["index.md", "calorie.project-conventions.md", "seek.project-conventions.md"],
          editable: true,
        },
        guides: {
          purpose: "团队可用性指南",
          files: ["index.md", "golden-path.md"],
          editable: false,
        },
        harness: {
          purpose: "实现细则 (Harness)",
          files: ["index.md", "detail/", "overview/", "implementation/"],
          editable: false,
        },
      },
    },
    modules: [
      {
        id: "conventions-shared",
        name: "Shared Conventions (can reuse in iOS/Android)",
        reusableAcross: ["flutter", "ios", "android"],
        files: ["conventions/index.md"],
      },
      {
        id: "harness-flutter",
        name: "Flutter-specific Harness",
        reusableAcross: ["flutter"],
        files: ["harness/"],
      },
    ],
    maintainer: {
      team: "Guru",
      contact: "guru-team@mindfold.ai",
    },
  },
  
  "spec-html-web": {
    id: "spec-html-web",
    name: "Web (HTML/CSS/JS) Spec",
    version: "1.0.0",
    projectTypes: ["html"],
    platforms: ["claude"],
    source: "marketplace",
    marketplaceId: "web-component-spec",
    structure: {
      required: [
        "README.md",
        "conventions/index.md",
        "guides/component-patterns.md",
      ],
      directories: {
        conventions: {
          purpose: "Web project conventions",
          files: ["index.md", "web-conventions.md"],
          editable: true,
        },
        guides: {
          purpose: "Web development patterns",
          files: ["component-patterns.md", "state-management.md"],
          editable: false,
        },
      },
    },
    modules: [
      {
        id: "conventions-shared",
        name: "Shared Conventions",
        reusableAcross: ["html", "flutter"],
        files: ["conventions/index.md"],
      },
    ],
  },
};
```

#### D. Skill 系统（Skills Registry）

```typescript
// packages/cli/src/types/skills.ts

export interface SkillDefinition {
  id: string;                          // "requirement-writing", "flutter-implementation-guru-writing"
  name: string;
  description: string;
  
  applicableProjectTypes: string[];    // ["flutter", "android", "ios", "*"]
  applicablePlatforms: string[];       // ["claude", "codex", "cursor"]
  
  category: "writing" | "review" | "utility" | "sop";
  phase?: "planning" | "design" | "implementation" | "review";
  
  source: "bundled" | "marketplace";
  bundledPath?: string;
  marketplaceId?: string;
  
  dependencies?: string[];             // 依赖的其他 skill IDs
  
  requiredTemplates?: {
    projectType?: string[];
    specs?: string[];
  };
}

export const SKILLS: Record<string, SkillDefinition> = {
  "requirement-writing": {
    id: "requirement-writing",
    name: "Requirement Writing",
    description: "Guide for writing clear project requirements",
    applicableProjectTypes: ["*"],  // 所有项目类型通用
    applicablePlatforms: ["claude", "codex"],
    category: "writing",
    phase: "planning",
    source: "bundled",
    bundledPath: "src/templates/guru/skills/requirement-writing.md",
  },
  
  "flutter-implementation-guru-writing": {
    id: "flutter-implementation-guru-writing",
    name: "Flutter Implementation (Guru-styled)",
    description: "Flutter implementation with Guru patterns",
    applicableProjectTypes: ["flutter"],
    applicablePlatforms: ["claude", "codex"],
    category: "writing",
    phase: "implementation",
    source: "bundled",
    bundledPath: "src/templates/guru/skills/flutter-implementation-writing.md",
    requiredTemplates: {
      projectType: ["flutter"],
      specs: ["guru-flutter-client"],
    },
  },
  
  // 平台差异化: 不同项目类型的同一阶段可用不同 skill
  "html-component-writing": {
    id: "html-component-writing",
    name: "HTML Component Implementation",
    description: "Component writing for web projects",
    applicableProjectTypes: ["html"],
    applicablePlatforms: ["claude"],
    category: "writing",
    phase: "implementation",
    source: "marketplace",
    marketplaceId: "html-component-writing",
  },
  
  "ios-swift-implementation": {
    id: "ios-swift-implementation",
    name: "iOS Swift Implementation",
    description: "Swift implementation patterns for iOS",
    applicableProjectTypes: ["ios"],
    applicablePlatforms: ["claude"],
    category: "writing",
    phase: "implementation",
    source: "marketplace",
    marketplaceId: "ios-swift-implementation",
  },
};
```

### 2.3 文件结构重组

```
packages/cli/src/
├── types/
│   ├── project-types.ts          # ProjectTypeDefinition + registry
│   ├── workflows.ts              # WorkflowDefinition + registry
│   ├── specs.ts                  # SpecTemplate + registry
│   └── skills.ts                 # SkillDefinition + registry
│
├── registries/
│   ├── project-type-registry.ts  # 导出 PROJECT_TYPES
│   ├── workflow-registry.ts      # 导出 WORKFLOWS
│   ├── spec-registry.ts          # 导出 SPECS
│   └── skill-registry.ts         # 导出 SKILLS
│
├── resolvers/
│   ├── project-type-resolver.ts  # detectProjectType() → ProjectTypeDefinition
│   ├── workflow-resolver.ts      # 改造: 使用 WorkflowRegistry
│   ├── spec-resolver.ts          # NEW: resolveSpec()
│   └── skill-resolver.ts         # NEW: resolveSkills()
│
├── templates/
│   ├── workflows/                # 工作流 bundled 存储
│   │   ├── native/
│   │   ├── guru-client/
│   │   └── mobile-native-dev/
│   │
│   ├── specs/                    # 规范 bundled 存储
│   │   ├── guru-flutter-client/
│   │   ├── spec-html-web/        # (未来: 若 bundled)
│   │   └── ...
│   │
│   └── skills/                   # Skill 内容
│       ├── universal/            # 跨项目类型
│       ├── flutter/
│       ├── html/
│       └── mobile/
│
├── commands/
│   ├── init.ts                   # 改造: 使用新注册表
│   └── update.ts
│
└── configurators/
    ├── shared.ts
    ├── platform-adapters/        # 分离平台适配
    │   ├── claude-code.ts
    │   ├── codex.ts
    │   └── cursor.ts
    └── project-type-adapters/    # NEW: 项目类型适配
        ├── flutter-adapter.ts
        ├── html-adapter.ts
        └── mobile-adapter.ts
```

### 2.4 改造 init.ts 流程

```typescript
// packages/cli/src/commands/init.ts (改造版)

import { PROJECT_TYPES } from "../registries/project-type-registry.js";
import { WORKFLOWS } from "../registries/workflow-registry.js";
import { SPECS } from "../registries/spec-registry.js";
import { SKILLS } from "../registries/skill-registry.js";

export async function init(options: InitOptions) {
  // Step 1: 检测项目类型
  const projectType = detectProjectType(cwd);  // → "flutter" / "html" / "ios" / ...
  const typeDef = PROJECT_TYPES[projectType];
  if (!typeDef) throw new Error(`Unknown project type: ${projectType}`);
  
  // Step 2: 选择工作流（在该项目类型支持的工作流范围内）
  let workflowId = options.workflow || typeDef.defaultWorkflow;
  const workflowDef = WORKFLOWS[workflowId];
  if (!workflowDef.applicableTo.includes(projectType)) {
    throw new Error(
      `Workflow "${workflowId}" not applicable to "${projectType}". ` +
      `Available: ${typeDef.availableWorkflows.join(", ")}`
    );
  }
  
  // Step 3: 解析规范模板（基于项目类型自动确定）
  const specId = typeDef.specTemplateId;
  const specDef = SPECS[specId];
  
  // Step 4: 解析该项目类型+平台的 Skills
  const platformSkills = resolveSkills({
    projectType,
    platform: options.platform,  // "claude" / "codex" / ...
    phase: "all",  // 或特定阶段
  });
  
  // Step 5: 平台适配
  const platformAdapter = createPlatformAdapter(
    options.platform,
    { projectType, workflow: workflowDef, spec: specDef }
  );
  
  // Step 6: 项目类型适配
  const typeAdapter = createProjectTypeAdapter(projectType);
  
  // Step 7: 生成文件
  await generateFiles({
    workflow: workflowDef,
    spec: specDef,
    skills: platformSkills,
    platformAdapter,
    typeAdapter,
  });
}
```

---

## 三、实施路线图

### Phase 1: 架构奠基（2 周）

```
Week 1:
  □ 创建 types/ 目录 (project-types.ts, workflows.ts, specs.ts, skills.ts)
  □ 定义 ProjectTypeDefinition + Flutter 注册表样例
  □ 创建 registries/ 导出函数
  □ Unit tests (30% coverage)

Week 2:
  □ 创建 resolvers/ (project-type-resolver, workflow-resolver, spec-resolver)
  □ 改造 project-detector.ts 返回 ProjectTypeDefinition
  □ 改造 workflow-resolver.ts 使用 WORKFLOWS 注册表
  □ 创建 spec-resolver.ts
  □ Integration tests
```

### Phase 2: 适配层改造（3 周）

```
Week 3:
  □ 创建 platform-adapters/ 目录
  □ 重构 configurators/shared.ts → platform-adapters/shared.ts
  □ 创建 claude-code.ts, codex.ts 平台适配
  □ 创建 project-type-adapters/ 目录

Week 4:
  □ 创建 flutter-adapter.ts (Flutter 特有逻辑)
  □ 改造 init.ts 使用新适配层
  □ 集成测试: trellis init --flutter --claude

Week 5:
  □ 创建 skill-resolver.ts
  □ 重构 Skill 加载逻辑（从硬编码 → 注册表驱动）
  □ 端到端测试
```

### Phase 3: 新项目类型接入（HTML 示例）

```
Week 6:
  □ 在 PROJECT_TYPES 注册 "html" 定义
  □ 创建 spec-html-web 规范集 (从 marketplace 或新建 bundled)
  □ 创建 html-adapter.ts
  □ 测试: trellis init --html --claude

Week 7:
  □ iOS + Android 快速注册 (基于 HTML 样板)
  □ smoke 测试
  □ 文档: 跨平台扩展指南
```

### Phase 4: 文档与交付

```
Week 8:
  □ 更新 TRELLIS_RELEASES.md
  □ 创建 CROSS_PLATFORM_EXTENSION.md (开发者指南)
  □ 发布 guru.2 版本
```

---

## 四、扩展示例

### 示例 1: 添加 HTML 项目类型

#### Step 1: 注册项目类型
```typescript
// packages/cli/src/registries/project-type-registry.ts

export const PROJECT_TYPES: Record<string, ProjectTypeDefinition> = {
  // ... Flutter ...
  
  html: {
    id: "html",
    name: "Web (HTML/CSS/JS/TS)",
    detection: {
      files: ["package.json", "index.html", "vite.config.js"],
      commandsToRun: [
        { cmd: "npm --version", versionMinimum: "8.0.0" },
      ],
    },
    defaultWorkflow: "native",
    availableWorkflows: ["native", "web-component-driven"],
    specTemplateId: "spec-html-web",
    bundledSpec: false,  // marketplace 获取
    platformAdapters: {
      claude: {
        hooks: ["SessionStart", "PreToolUse"],
        skillOverrides: {
          "flutter-implementation-guru-writing": "html-component-writing",
        },
      },
    },
    tags: ["web", "frontend"],
  },
};
```

#### Step 2: 创建 HTML 适配器
```typescript
// packages/cli/src/configurators/project-type-adapters/html-adapter.ts

import { ProjectTypeAdapter } from "../../types/adapters.js";

export const htmlAdapter: ProjectTypeAdapter = {
  projectType: "html",
  
  // 返回 HTML 特有的配置
  getConfigDefaults() {
    return {
      framework: "vanilla",  // vanilla / react / vue / svelte
      bundler: "vite",       // vite / webpack / parcel
      linter: "eslint",
      formatter: "prettier",
    };
  },
  
  // HTML 特有的文件生成
  async generateFiles(context: GenerateFileContext) {
    const { targetDir, spec, skills } = context;
    
    // 生成 Web 特有的 Skill 清单
    await createWebSkillManifest(targetDir, skills);
    
    // 生成 eslint 配置（如果需要）
    if (context.options.linter === "eslint") {
      await copyTemplate("html/.eslintrc.json", `${targetDir}/.eslintrc.json`);
    }
  },
  
  // HTML 特有的 hook 注入
  async configureHooks(context: ConfigureHooksContext) {
    // Web 项目可能需要特殊的 TypeScript hook
    if (context.platform === "claude") {
      await injectTypeScriptHook(context.targetDir);
    }
  },
};
```

#### Step 3: 注册 HTML Workflow
```typescript
// packages/cli/src/registries/workflow-registry.ts

export const WORKFLOWS: Record<string, WorkflowDefinition> = {
  // ... existing ...
  
  "web-component-driven": {
    id: "web-component-driven",
    name: "Web Component-Driven Development",
    description: "Component-first workflow for web projects",
    applicableTo: ["html"],  // ← 仅限 Web
    phases: ["design", "component", "integration", "testing"],
    source: "marketplace",
    marketplaceId: "web-component-driven",
    gatePoints: "light",
    teamTooling: "both",
  },
};
```

#### Step 4: 注册 HTML Spec
```typescript
// packages/cli/src/registries/spec-registry.ts

export const SPECS: Record<string, SpecTemplate> = {
  // ... existing ...
  
  "spec-html-web": {
    id: "spec-html-web",
    name: "Web (HTML/CSS/JS) Spec",
    version: "1.0.0",
    projectTypes: ["html"],
    platforms: ["claude"],
    source: "marketplace",
    marketplaceId: "web-component-spec",
    structure: {
      required: [
        "README.md",
        "conventions/web-conventions.md",
        "guides/component-patterns.md",
      ],
      directories: {
        conventions: {
          purpose: "Web project conventions",
          files: ["web-conventions.md", "html-guidelines.md"],
          editable: true,
        },
        guides: {
          purpose: "Web development patterns",
          files: ["component-patterns.md", "state-management.md"],
          editable: false,
        },
      },
    },
  },
};
```

#### Step 5: 注册 HTML Skills
```typescript
// packages/cli/src/registries/skill-registry.ts

export const SKILLS: Record<string, SkillDefinition> = {
  // ... existing ...
  
  "html-component-writing": {
    id: "html-component-writing",
    name: "Web Component Implementation",
    description: "Component writing for HTML/CSS/JS projects",
    applicableProjectTypes: ["html"],
    applicablePlatforms: ["claude"],
    category: "writing",
    phase: "implementation",
    source: "marketplace",
    marketplaceId: "html-component-writing",
  },
  
  "web-css-architecture": {
    id: "web-css-architecture",
    name: "CSS Architecture & Design Systems",
    description: "Design systems and CSS patterns for web",
    applicableProjectTypes: ["html"],
    applicablePlatforms: ["claude"],
    category: "writing",
    phase: "design",
    source: "marketplace",
    marketplaceId: "web-css-architecture",
  },
};
```

#### Step 6: 测试
```bash
# 首次尝试初始化 HTML 项目
cd /tmp/web-project
npm init -y  # 创建 package.json
echo "<html></html>" > index.html

trellis init --claude -y
# 应该检测到 "html" 项目类型
# 自动选择 "native" workflow
# 应用 spec-html-web 规范
# 注入 HTML-specific skills
```

---

## 五、API 接口定义

### A. ProjectTypeDetector
```typescript
export interface ProjectTypeDetector {
  detect(cwd: string): Promise<DetectionResult>;
}

export interface DetectionResult {
  projectType: string;           // "flutter" / "html" / "ios"
  confidence: number;            // 0-1
  detectedFiles: string[];
  reason: string;
}

// 使用
const detector = new ProjectTypeDetector();
const result = await detector.detect(cwd);
console.log(result.projectType);  // "flutter"
```

### B. RegistryResolver
```typescript
export interface RegistryResolver {
  getProjectTypeDefinition(type: string): ProjectTypeDefinition;
  getWorkflowDefinition(id: string): WorkflowDefinition;
  getSpecTemplate(id: string): SpecTemplate;
  getSkill(id: string): SkillDefinition;
  
  // 过滤接口
  getWorkflowsFor(projectType: string): WorkflowDefinition[];
  getSkillsFor(options: {
    projectType: string;
    platform: string;
    phase?: string;
  }): SkillDefinition[];
}

// 使用
const resolver = new RegistryResolver();
const workflows = resolver.getWorkflowsFor("html");
const skills = resolver.getSkillsFor({
  projectType: "flutter",
  platform: "claude",
  phase: "implementation",
});
```

### C. AdapterFactory
```typescript
export interface AdapterFactory {
  createPlatformAdapter(
    platform: string,
    context: AdapterContext
  ): PlatformAdapter;
  
  createProjectTypeAdapter(
    projectType: string
  ): ProjectTypeAdapter;
}

export interface PlatformAdapter {
  configure(context: ConfigureContext): Promise<void>;
  injectHooks(targetDir: string): Promise<void>;
}

export interface ProjectTypeAdapter {
  getConfigDefaults(): Record<string, any>;
  generateFiles(context: GenerateFileContext): Promise<void>;
  configureHooks(context: ConfigureHooksContext): Promise<void>;
}

// 使用
const factory = new AdapterFactory();
const platformAdapter = factory.createPlatformAdapter("claude", {...});
const typeAdapter = factory.createProjectTypeAdapter("flutter");
```

---

## 六、向后兼容策略

### 现有 flutter 项目的保护

```typescript
// packages/cli/src/commands/init.ts

// ✅ 保持现有行为：--workflow guru-client
// ✅ 自动检测 Flutter 项目时默认选择 guru-client
// ✅ guru-flutter-client spec 始终 bundled

if (projectType === "flutter" && !options.workflow) {
  options.workflow = "guru-client";  // 默认行为不变
}

// ✅ 兼容旧的 --template 参数（通过废弃警告）
if (options.template) {
  console.warn(
    "Deprecation: --template is superseded by --workflow. " +
    "Use --workflow instead."
  );
  // 自动映射
  options.workflow = oldTemplateToWorkflow(options.template);
}
```

### 迁移路径

```
现状 (v0.6.0-guru.1):
  trellis init --template guru-client-workflow
  → 工作但显示废弃警告

目标 (v0.6.0-guru.2+):
  trellis init --workflow guru-client
  → 新用户推荐用法
  
  trellis init --workflow native
  trellis init --workflow web-component-driven
  (新项目类型)
```

---

## 七、验证清单

### 设计阶段
- [ ] 评审 ProjectTypeDefinition 结构
- [ ] 确认 2×N 矩阵（项目类型 × 平台）的边界
- [ ] 确认 Spec 模块化粒度（conventions-shared 是否太粗？）

### 实现阶段
- [ ] Unit tests: 注册表加载与查询
- [ ] Integration tests: init 流程跨项目类型
- [ ] Smoke tests: 现有 Flutter 流程不受影响
- [ ] E2E tests: HTML/iOS/Android 初始化成功

### 文档
- [ ] CROSS_PLATFORM_EXTENSION.md (开发者指南)
- [ ] 每个项目类型的快速开始指南
- [ ] API 参考

---

## 八、预期收益

| 维度 | 当前 | 改造后 |
|------|------|--------|
| **添加新项目类型成本** | ~500 行代码 + 5 天 | ~50 行注册表 + 1 小时配置 |
| **项目类型 × 平台矩阵** | 无感知 (hardcoded) | 清晰的二维矩阵，易可视化 |
| **Spec 复用** | 复制粘贴 (16 文件 × N) | 模块化，引用即可 |
| **扩展点数量** | 2 (workflow-resolver, init.ts) | 8+ (registries, adapters, resolvers) |
| **文档清晰度** | 人工追踪 | 代码即文档 (DefinitionType) |
| **用户体验** | "trellis init" 通用提示 | 项目类型感知的定制化提示 |

---

## 九、总结

### 核心思想

1. **从 hardcoded 到 registry-driven**
   - 从 if/else 分支 → 声明式注册表
   - 易于扩展，无需修改核心逻辑

2. **从耦合到分离**
   - 工作流 ≠ 规范 ≠ Skill ≠ 平台
   - 每个维度独立演进

3. **从一维到二维**
   - 项目类型 × 平台组合
   - 矩阵某位置的定制化支持

4. **从全量复制到模块化**
   - Spec 文件树 → Spec 模块
   - 跨项目类型的规范共享

### 实施优先级

```
必做 (P0):
  1. ProjectTypeDefinition + registry
  2. 改造 init.ts 使用新注册表
  3. Unit + E2E 测试 (Flutter 保护)

高优 (P1):
  4. Workflow + Spec 注册表
  5. HTML 项目类型接入 (PoC)
  6. 文档: 扩展指南

中等 (P2):
  7. iOS/Android 快速接入
  8. Skill 系统优化
  9. marketplace 集成

可选 (P3):
  10. GUI 可视化矩阵编辑器
  11. 项目类型 AI 自推荐
```

