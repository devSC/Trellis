# Trellis 跨平台扩展实施指南

## 核心原则（为什么要这样设计）

### 问题陈述

当前 Trellis guru/main 虽然完全支持 Flutter，但若要扩展至 HTML、iOS、Android，会面临：

```
当前瓶颈:
  1. 项目类型 hardcoded: 若要支持新类型需改 project-detector.ts
  2. 工作流写死: NATIVE_WORKFLOW_ID + GURU_CLIENT_WORKFLOW_ID 只有这两个
  3. 规范集耦合: guru-flutter-client 与工作流绑定，无法复用或改进
  4. Skill 分散: 在 guru-template/ 中混乱，无中心管理
  5. 平台感知缺失: 配置器无法针对项目类型定制

结果:
  - 添加新项目类型需修改核心代码 (init.ts, workflow-resolver.ts)
  - 测试回归风险高
  - 文档和代码不一致 (新开发者难以跟进)
```

### 解决方案（Registry-Driven Architecture）

```
核心思想:
  项目类型 ← 注册表驱动 → 工作流、规范、Skills
  
```

而非

```
项目类型 (hardcoded) → if/else 分支 → 逻辑散落各处
```

---

## 关键设计点

### 1. 四大注册表（4 Registries）

#### A. ProjectTypeRegistry
定义: "什么是一个项目类型？"

```typescript
interface ProjectTypeDefinition {
  id: "flutter" | "html" | "ios" | "android" | ...
  detection: { files: [...], commands: [...] }
  defaultWorkflow: "native" | "guru-client" | ...
  specTemplateId: "guru-flutter-client" | "spec-html-web" | ...
  platformAdapters: {
    "claude": { skillOverrides: {...} },
    "codex": { hooks: [...] }
  }
}
```

**价值**: 一个数据结构描述整个项目类型的特征 → 可视化、校验、扩展

#### B. WorkflowRegistry
定义: "什么是一个工作流？它适用于哪些项目？"

```typescript
interface WorkflowDefinition {
  id: "native" | "guru-client" | "web-component-driven" | "mobile-native-dev" | ...
  applicableTo: ["flutter"] | ["html"] | ["flutter", "android", "ios"] | ...
  phases: ["planning", "design", "implementation", "review"]
  source: "bundled" | "marketplace"
}
```

**价值**: 工作流与项目类型解耦 → 可在矩阵任意位置定制

#### C. SpecRegistry
定义: "规范集是什么？覆盖哪些项目类型？"

```typescript
interface SpecTemplate {
  id: "guru-flutter-client" | "spec-html-web" | "spec-ios-swift" | ...
  projectTypes: ["flutter"] | ["html"] | ...
  source: "bundled" | "marketplace"
  modules: [
    { id: "conventions-shared", reusableAcross: ["flutter", "ios", "android"] },
    { id: "harness-flutter", reusableAcross: ["flutter"] }
  ]
}
```

**价值**: Spec 模块化 → conventions 可共享，platform-specific harness 隔离

#### D. SkillRegistry
定义: "Skill 是什么？在哪些项目类型×平台组合上有效？"

```typescript
interface SkillDefinition {
  id: "requirement-writing" | "flutter-implementation-guru-writing" | "html-component-writing" | ...
  applicableProjectTypes: ["*"] | ["flutter"] | ["html"] | ...
  applicablePlatforms: ["claude", "codex"] | ["claude"] | ...
  category: "writing" | "review" | "utility"
  phase: "planning" | "design" | "implementation" | "review"
}
```

**价值**: Skill 与项目类型×平台关联 → 自动过滤和推荐

### 2. 二维矩阵（Project Type × Platform）

```
                Claude Code      Codex       Cursor
Flutter         ✓ guru-client   ✓ default   ○ native
HTML            ✓ component-d   ○ native    ○ native
iOS             ✓ native        ○ native    ○ native
Android         ✓ native        ○ native    ○ native
Node.js         ✓ native        ✓ native    ○ native

图例: ✓ 完全支持  ○ 基本支持  ✗ 不支持
```

每个单元可独立配置:
- Flutter + Claude Code = guru-client workflow + guru-flutter-client spec + flutter-specific skills
- HTML + Claude Code = native workflow + spec-html-web spec + html-component-writing skill
- iOS + Claude Code = native workflow + spec-ios-swift spec + ios-swift-implementation skill

### 3. 平台×项目类型的适配器

```
当前: configurators/
  └── claude.ts (仅平台感知)

改造后: 
  ├── platform-adapters/
  │   ├── claude-code.ts (平台通用逻辑)
  │   ├── codex.ts
  │   └── cursor.ts
  │
  └── project-type-adapters/
      ├── flutter-adapter.ts (项目类型特定逻辑)
      ├── html-adapter.ts
      ├── ios-adapter.ts
      └── android-adapter.ts
```

**示例**: 初始化 HTML + Claude Code 时
```
PlatformAdapter (Claude) 负责:
  - settings.json hooks (SessionStart, PreToolUse)
  - 平台特定的初始化

ProjectTypeAdapter (HTML) 负责:
  - Web 特定的 linter/formatter 配置 (eslint, prettier)
  - TypeScript 配置建议
  - Web Skill 清单生成
```

---

## 实施步骤

### Step 1: 创建类型系统（types/ 目录）

```bash
mkdir packages/cli/src/types
```

**文件**:
- `project-types.ts` — ProjectTypeDefinition interface + Flutter 注册表
- `workflows.ts` — WorkflowDefinition interface + 工作流注册表
- `specs.ts` — SpecTemplate interface + 规范注册表
- `skills.ts` — SkillDefinition interface + Skill 注册表

**关键点**:
```typescript
// project-types.ts
export interface ProjectTypeDefinition {
  id: string
  detection: { files: string[], commands?: [...] }
  defaultWorkflow: string
  specTemplateId: string
  platformAdapters: Record<string, PlatformAdapterConfig>
}

export const PROJECT_TYPES: Record<string, ProjectTypeDefinition> = {
  flutter: { /* 现有逻辑 */ },
  // 未来: html, ios, android
}
```

**测试**:
```typescript
// __tests__/types/project-types.test.ts
describe("ProjectTypeDefinition", () => {
  it("exports PROJECT_TYPES with 'flutter'", () => {
    expect(PROJECT_TYPES.flutter.id).toBe("flutter")
  })
  
  it("flutter has spec template defined", () => {
    expect(PROJECT_TYPES.flutter.specTemplateId).toBe("guru-flutter-client")
  })
})
```

### Step 2: 创建 Resolver 层（resolvers/ 目录）

```bash
mkdir packages/cli/src/resolvers
```

**关键修改**:

A. `project-type-resolver.ts` — 新增
```typescript
export class ProjectTypeResolver {
  resolve(cwd: string): ProjectTypeDefinition | null {
    // 用 PROJECT_TYPES.flutter.detection.files 检测
    // 返回 PROJECT_TYPES[detected]
  }
}
```

B. `workflow-resolver.ts` — 改造
```typescript
// 改前:
const BUNDLED_WORKFLOW_IDS = new Set(["native", "guru-client"])

// 改后:
export class WorkflowResolver {
  resolve(workflowId: string): WorkflowDefinition {
    const def = WORKFLOWS[workflowId]
    if (!def) throw new Error(`Unknown workflow: ${workflowId}`)
    return def
  }
  
  getWorkflowsFor(projectType: string): WorkflowDefinition[] {
    return Object.values(WORKFLOWS).filter(
      w => w.applicableTo.includes(projectType)
    )
  }
}
```

C. `spec-resolver.ts` — 新增
```typescript
export class SpecResolver {
  resolve(specId: string): SpecTemplate {
    const def = SPECS[specId]
    if (!def) throw new Error(`Unknown spec: ${specId}`)
    return def
  }
  
  getSpecsFor(projectType: string): SpecTemplate[] {
    return Object.values(SPECS).filter(
      s => s.projectTypes.includes(projectType)
    )
  }
}
```

D. `skill-resolver.ts` — 新增
```typescript
export class SkillResolver {
  resolve(skillId: string): SkillDefinition {
    return SKILLS[skillId]
  }
  
  getSkillsFor(options: {
    projectType: string
    platform: string
    phase?: string
  }): SkillDefinition[] {
    return Object.values(SKILLS).filter(s =>
      (s.applicableProjectTypes.includes("*") || 
       s.applicableProjectTypes.includes(options.projectType)) &&
      s.applicablePlatforms.includes(options.platform) &&
      (!options.phase || s.phase === options.phase)
    )
  }
}
```

**测试**:
```typescript
describe("WorkflowResolver", () => {
  it("returns workflows applicable to flutter", () => {
    const resolver = new WorkflowResolver()
    const wfs = resolver.getWorkflowsFor("flutter")
    expect(wfs.map(w => w.id)).toContain("guru-client")
  })
})
```

### Step 3: 改造 init.ts 流程

```typescript
// packages/cli/src/commands/init.ts (改造版)

export async function init(options: InitOptions) {
  // Step 1: 检测项目类型
  const typeResolver = new ProjectTypeResolver()
  const typeDef = typeResolver.resolve(cwd)
  if (!typeDef) {
    console.error(`Unknown project type. Supported: ${Object.keys(PROJECT_TYPES).join(", ")}`)
    return
  }
  
  // Step 2: 选择工作流
  const workflowResolver = new WorkflowResolver()
  let workflowId = options.workflow || typeDef.defaultWorkflow
  const workflowDef = workflowResolver.resolve(workflowId)
  
  // 验证该工作流适用于该项目类型
  if (!workflowDef.applicableTo.includes(typeDef.id)) {
    throw new Error(
      `Workflow "${workflowId}" not applicable to "${typeDef.id}". ` +
      `Available: ${workflowResolver.getWorkflowsFor(typeDef.id).map(w => w.id).join(", ")}`
    )
  }
  
  // Step 3: 解析规范
  const specResolver = new SpecResolver()
  const specDef = specResolver.resolve(typeDef.specTemplateId)
  
  // Step 4: 解析 Skills
  const skillResolver = new SkillResolver()
  const skills = skillResolver.getSkillsFor({
    projectType: typeDef.id,
    platform: options.platform,
  })
  
  // Step 5: 创建适配器
  const platformAdapter = createPlatformAdapter(options.platform, {
    typeDef,
    workflowDef,
    specDef,
  })
  
  const typeAdapter = createProjectTypeAdapter(typeDef.id)
  
  // Step 6: 生成文件
  await generateFiles({
    cwd,
    typeDef,
    workflowDef,
    specDef,
    skills,
    platformAdapter,
    typeAdapter,
    options,
  })
}
```

**关键改进**:
- ✓ 项目类型自动检测且有明确的注册表支持
- ✓ 工作流选择验证严格（防止不匹配）
- ✓ 规范基于项目类型自动确定
- ✓ Skills 过滤精确（项目类型 × 平台）
- ✓ 适配器创建清晰

### Step 4: 创建适配器工厂

```typescript
// packages/cli/src/adapters/adapter-factory.ts

export class AdapterFactory {
  createPlatformAdapter(
    platform: string,
    context: {
      typeDef: ProjectTypeDefinition
      workflowDef: WorkflowDefinition
      specDef: SpecTemplate
    }
  ): PlatformAdapter {
    // 根据 platform 返回不同的适配器
    switch (platform) {
      case "claude":
        return new ClaudeCodeAdapter(context)
      case "codex":
        return new CodexAdapter(context)
      case "cursor":
        return new CursorAdapter(context)
      default:
        throw new Error(`Unknown platform: ${platform}`)
    }
  }
  
  createProjectTypeAdapter(
    projectType: string
  ): ProjectTypeAdapter {
    // 根据 projectType 返回不同的适配器
    switch (projectType) {
      case "flutter":
        return new FlutterAdapter()
      case "html":
        return new HtmlAdapter()
      case "ios":
        return new IosAdapter()
      case "android":
        return new AndroidAdapter()
      default:
        return new DefaultProjectTypeAdapter()  // 通用适配器
    }
  }
}
```

### Step 5: 验证向后兼容性

```typescript
// test/integration/backward-compat.test.ts

describe("Backward Compatibility", () => {
  it("flutter + guru-client workflow works as before", async () => {
    const result = await init({
      cwd: flutterProjectPath,
      platform: "claude",
      workflow: "guru-client",
    })
    
    expect(result.success).toBe(true)
    expect(fs.existsSync(path.join(flutterProjectPath, ".trellis/workflow.md"))).toBe(true)
  })
  
  it("auto-detects flutter and applies guru-client by default", async () => {
    const result = await init({
      cwd: flutterProjectPath,
      platform: "claude",
      // workflow not specified
    })
    
    expect(result.workflowUsed).toBe("guru-client")
  })
})
```

---

## 添加新项目类型的模板流程

### 例: 添加 HTML 支持

#### 1. 注册项目类型
```typescript
// packages/cli/src/registries/project-type-registry.ts

export const PROJECT_TYPES: Record<string, ProjectTypeDefinition> = {
  // ... flutter ...
  
  html: {
    id: "html",
    name: "Web (HTML/CSS/JS/TS)",
    icon: "🌐",
    detection: {
      files: ["package.json", "index.html"],
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
        skillOverrides: {
          "flutter-implementation-guru-writing": "html-component-writing",
        },
      },
    },
    tags: ["web", "frontend"],
  },
}
```

#### 2. 注册工作流
```typescript
// packages/cli/src/registries/workflow-registry.ts

export const WORKFLOWS: Record<string, WorkflowDefinition> = {
  // ... existing ...
  
  "web-component-driven": {
    id: "web-component-driven",
    name: "Web Component-Driven Development",
    description: "Develop web apps component-by-component",
    applicableTo: ["html"],
    phases: ["design", "component", "integration", "review"],
    source: "marketplace",
    marketplaceId: "web-component-driven",
    gatePoints: "light",
    teamTooling: "both",
  },
}
```

#### 3. 注册规范
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
          files: ["web-conventions.md"],
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
        files: ["conventions/web-conventions.md"],
      },
    ],
  },
}
```

#### 4. 注册 Skills
```typescript
// packages/cli/src/registries/skill-registry.ts

export const SKILLS: Record<string, SkillDefinition> = {
  // ... existing ...
  
  "html-component-writing": {
    id: "html-component-writing",
    name: "Web Component Implementation",
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
    applicableProjectTypes: ["html"],
    applicablePlatforms: ["claude"],
    category: "writing",
    phase: "design",
    source: "marketplace",
    marketplaceId: "web-css-architecture",
  },
}
```

#### 5. 创建 HTML 适配器
```typescript
// packages/cli/src/adapters/project-type-adapters/html-adapter.ts

export class HtmlAdapter implements ProjectTypeAdapter {
  async generateFiles(context: GenerateFileContext) {
    const { cwd, options } = context
    
    // 生成 eslint 配置
    if (options.linter === "eslint") {
      await copyTemplate("html/.eslintrc.json", `${cwd}/.eslintrc.json`)
    }
    
    // 生成 prettier 配置
    if (options.formatter === "prettier") {
      await copyTemplate("html/.prettierrc.json", `${cwd}/.prettierrc.json`)
    }
    
    // 生成 HTML 特定的 Skill 清单
    await createHtmlSkillManifest(cwd)
  }
  
  async configureHooks(context: ConfigureHooksContext) {
    // Web 项目的 TypeScript hook
    if (context.platform === "claude") {
      await injectWebTypescriptHook(context.cwd)
    }
  }
}
```

#### 6. 测试
```bash
# 创建 HTML 测试项目
mkdir /tmp/html-test-project
cd /tmp/html-test-project
npm init -y
echo "<html></html>" > index.html

# 初始化
trellis init --claude -y

# 验证
ls -la .trellis/
ls -la .claude/
```

**期望**:
```
✅ 项目类型自动检测为 "html"
✅ 默认工作流选择 "native"
✅ 应用 spec-html-web 规范
✅ 注入 html-component-writing skill
✅ 生成 .eslintrc.json、.prettierrc.json
```

---

## 文件树对比

### 当前结构
```
packages/cli/src/
├── commands/init.ts        # 所有逻辑混在这里
├── utils/
│   ├── project-detector.ts # 项目检测
│   ├── workflow-resolver.ts # 工作流
│   └── template-fetcher.ts
└── configurators/
    ├── shared.ts           # 平台通用
    ├── claude.ts           # Claude Code
    └── ...
```

### 改造后结构
```
packages/cli/src/
├── types/                          # 数据定义
│   ├── project-types.ts           # ProjectTypeDefinition
│   ├── workflows.ts               # WorkflowDefinition
│   ├── specs.ts                   # SpecTemplate
│   └── skills.ts                  # SkillDefinition
│
├── registries/                     # 注册表 (可导出、可缓存)
│   ├── project-type-registry.ts
│   ├── workflow-registry.ts
│   ├── spec-registry.ts
│   └── skill-registry.ts
│
├── resolvers/                      # 解析器 (从注册表查询)
│   ├── project-type-resolver.ts
│   ├── workflow-resolver.ts        # (改造)
│   ├── spec-resolver.ts
│   └── skill-resolver.ts
│
├── adapters/                       # 适配器
│   ├── adapter-factory.ts
│   ├── platform-adapters/
│   │   ├── shared.ts
│   │   ├── claude-code.ts
│   │   ├── codex.ts
│   │   └── cursor.ts
│   └── project-type-adapters/
│       ├── flutter-adapter.ts
│       ├── html-adapter.ts
│       ├── ios-adapter.ts
│       └── android-adapter.ts
│
├── commands/
│   ├── init.ts                    # (改造: 使用注册表+解析器+工厂)
│   └── update.ts
│
└── configurators/
    ├── shared.ts                  # (复用，无改动)
    ├── claude.ts
    └── ...
```

---

## 测试策略

### 单元测试
```typescript
// packages/cli/test/registries/project-type-registry.test.ts
describe("PROJECT_TYPES", () => {
  it("defines flutter project type", () => {
    expect(PROJECT_TYPES.flutter).toBeDefined()
    expect(PROJECT_TYPES.flutter.specTemplateId).toBe("guru-flutter-client")
  })
})

// packages/cli/test/resolvers/workflow-resolver.test.ts
describe("WorkflowResolver", () => {
  it("returns applicable workflows for flutter", () => {
    const resolver = new WorkflowResolver()
    const wfs = resolver.getWorkflowsFor("flutter")
    expect(wfs.some(w => w.id === "guru-client")).toBe(true)
  })
})
```

### 集成测试
```typescript
// packages/cli/test/integration/init-flows.test.ts
describe("Init flows", () => {
  it("initializes flutter project with guru-client", async () => {
    // 在真实 Flutter 项目中运行 init
  })
  
  it("initializes html project with native workflow", async () => {
    // 在真实 HTML 项目中运行 init
  })
  
  it("rejects unsupported workflow for project type", async () => {
    // 尝试 html + guru-client → 应失败
  })
})
```

### 向后兼容测试
```typescript
// test/backward-compatibility.test.ts
describe("Backward compatibility", () => {
  it("flutter + guru-client works exactly as before", async () => {
    // 验证 apply_test.sh 的 14 个场景仍过
  })
})
```

---

## 总结

| 阶段 | 投入 | 产出 |
|------|------|------|
| **Phase 1: 架构** | 2 周 | 4 个注册表 + 4 个 resolver |
| **Phase 2: 改造** | 3 周 | 改造 init.ts + 工厂 + 向后兼容测试 |
| **Phase 3: HTML** | 1 周 | 完整的 HTML 支持 |
| **Phase 4: iOS/Android** | 1 周 | 快速接入 (基于 HTML 模板) |

**总计**: 7 周 → Flutter + HTML + iOS + Android 全支持

---

## 价值评估

```
投入: ~1400 小时代码 (累计)
产出:
  ✓ 添加新项目类型: 从 500 行代码 → 50 行注册表
  ✓ 扩展点从 2 个 → 8 个 (降低耦合)
  ✓ 项目类型 × 平台清晰矩阵化 (易维护)
  ✓ Spec 模块化 (可复用)
  ✓ 代码即文档 (新开发者快速上手)

定性收益:
  ✓ 10 倍更易扩展
  ✓ 回归风险大幅下降
  ✓ 新项目类型集成时间 1 周 → 1 天
```

