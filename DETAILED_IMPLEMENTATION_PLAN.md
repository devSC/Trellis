# Trellis 跨平台扩展详细实施计划

**目标**: Flutter + HTML + iOS + Android 四大项目类型全支持  
**周期**: 7周  
**团队**: 1-2名工程师  
**风险**: 低（架构文档完整，向后兼容明确）  

---

## 第一阶段：架构基础（第1-2周）

### Week 1: 类型系统与注册表框架

#### 任务1.1: 创建 types/ 目录和文件结构
```bash
mkdir -p packages/cli/src/types
mkdir -p packages/cli/src/registries
mkdir -p packages/cli/test/types
mkdir -p packages/cli/test/registries
```

**时间估算**: 0.5天

#### 任务1.2: 实现 project-types.ts
**文件**: `packages/cli/src/types/project-types.ts`

```typescript
/**
 * Project type definitions and registry.
 * 
 * Each project type defines:
 * - Detection logic (which files to look for)
 * - Default workflow (native, guru-client, etc)
 * - Associated spec template (where conventions/guides come from)
 * - Platform-specific overrides (how to adapt settings.json, hooks, etc)
 */

export interface DetectionConfig {
  files: string[];  // Files that indicate this project type (in priority order)
  minCount?: number;  // How many files must be present (default: 1)
  commands?: Array<{ cmd: string; versionMinimum?: string }>;
}

export interface PlatformAdapterConfig {
  hooks?: string[];  // Special hook types for this platform
  skillOverrides?: Record<string, string>;  // Map generic skill ID to platform-specific ID
  requiredFiles?: string[];  // Files that must exist for setup to work
}

export interface ProjectTypeDefinition {
  id: string;  // "flutter" | "html" | "ios" | "android"
  name: string;  // "Flutter App" | "Web (HTML/CSS/JS/TS)"
  icon?: string;  // Optional emoji or icon identifier
  
  detection: DetectionConfig;
  
  // Workflow & Spec association
  defaultWorkflow: string;  // "native" | "guru-client"
  availableWorkflows: string[];  // All workflows this type supports
  specTemplateId: string;  // "guru-flutter-client" | "spec-html-web" | "spec-ios-swift"
  bundledSpec: boolean;  // If true, spec is included in CLI binary; else fetch from marketplace
  
  // Platform customization
  platformAdapters: Record<string, PlatformAdapterConfig>;
  
  // Metadata
  tags: string[];  // ["mobile", "native", "cross-platform"] | ["web", "frontend"]
  version?: string;  // Project type definition version
}

export const PROJECT_TYPES: Record<string, ProjectTypeDefinition> = {
  flutter: {
    id: "flutter",
    name: "Flutter App",
    icon: "📱",
    
    detection: {
      files: ["pubspec.yaml", "ios/Runner.xcodeproj", "android/app/build.gradle"],
      minCount: 1,
    },
    
    defaultWorkflow: "guru-client",
    availableWorkflows: ["native", "guru-client"],
    specTemplateId: "guru-flutter-client",
    bundledSpec: true,  // guru-flutter-client is bundled in CLI
    
    platformAdapters: {
      claude: {
        hooks: ["SessionStart", "PreToolUse"],
        skillOverrides: {},  // Use default skills
      },
      codex: {
        hooks: ["PreToolUse"],
      },
    },
    
    tags: ["mobile", "native", "cross-platform"],
  },

  // Placeholder entries for Phase 3 & 4 (to be filled in later)
  html: {
    id: "html",
    name: "Web (HTML/CSS/JS/TS)",
    icon: "🌐",
    
    detection: {
      files: ["package.json", "index.html"],
      minCount: 1,
    },
    
    defaultWorkflow: "native",
    availableWorkflows: ["native"],  // Will add web-component-driven in Phase 3
    specTemplateId: "spec-html-web",
    bundledSpec: false,  // Will fetch from marketplace
    
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

  ios: {
    id: "ios",
    name: "iOS (Swift/Objective-C)",
    icon: "🍎",
    
    detection: {
      files: ["ios/Podfile", "ios/Podfile.lock", "ios/*.xcodeproj"],
      minCount: 1,
    },
    
    defaultWorkflow: "native",
    availableWorkflows: ["native"],  // Will add mobile-native-dev in Phase 4
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
    icon: "🤖",
    
    detection: {
      files: ["android/build.gradle", "android/app/build.gradle", "android/gradle.properties"],
      minCount: 1,
    },
    
    defaultWorkflow: "native",
    availableWorkflows: ["native"],
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

**时间估算**: 2天  
**测试**:
```typescript
// test/types/project-types.test.ts
describe("PROJECT_TYPES", () => {
  it("defines all four project types", () => {
    expect(Object.keys(PROJECT_TYPES)).toContain("flutter")
    expect(Object.keys(PROJECT_TYPES)).toContain("html")
    expect(Object.keys(PROJECT_TYPES)).toContain("ios")
    expect(Object.keys(PROJECT_TYPES)).toContain("android")
  })

  it("flutter defaults to guru-client workflow", () => {
    expect(PROJECT_TYPES.flutter.defaultWorkflow).toBe("guru-client")
  })

  it("flutter spec is bundled", () => {
    expect(PROJECT_TYPES.flutter.bundledSpec).toBe(true)
  })

  it("html spec is marketplace-fetched", () => {
    expect(PROJECT_TYPES.html.bundledSpec).toBe(false)
  })

  it("each type has valid platform adapters", () => {
    for (const type of Object.values(PROJECT_TYPES)) {
      expect(type.platformAdapters.claude).toBeDefined()
    }
  })
})
```

#### 任务1.3: 实现 workflows.ts
**文件**: `packages/cli/src/types/workflows.ts`

```typescript
export interface WorkflowDefinition {
  id: string;  // "native", "guru-client", etc
  name: string;
  description: string;
  
  // Which project types can use this workflow
  applicableTo: string[];  // ["flutter"] | ["html"] | ["flutter", "android", "ios"]
  
  // Workflow phases
  phases: string[];  // ["planning", "in_progress", "review", "done"]
  
  // Where workflow content comes from
  source: "bundled" | "marketplace";
  bundledPath?: string;  // "src/templates/workflows/native/workflow.md"
  marketplaceId?: string;  // For marketplace lookup
  
  // Gating strategy
  gatePoints: "none" | "light" | "full";  // none=no gates, light=optional, full=required
  
  // Which platforms support this workflow
  teamTooling?: string;  // "none" | "claude-code" | "codex" | "both"
}

export const WORKFLOWS: Record<string, WorkflowDefinition> = {
  native: {
    id: "native",
    name: "Trellis Native Workflow",
    description: "General-purpose 5-phase workflow suitable for all project types",
    applicableTo: ["flutter", "html", "ios", "android"],
    phases: ["planning", "in_progress", "review", "done"],
    source: "bundled",
    bundledPath: "src/templates/trellis/workflow.md",
    gatePoints: "none",
    teamTooling: "both",
  },

  "guru-client": {
    id: "guru-client",
    name: "Guru Client Workflow",
    description: "Flutter-optimized 5-phase SDD workflow with human gates",
    applicableTo: ["flutter"],  // Flutter only
    phases: ["planning", "in_progress", "review", "done"],
    source: "bundled",
    bundledPath: "src/templates/guru/workflow.md",
    gatePoints: "full",  // Requires human approval at each phase
    teamTooling: "both",
  },

  // Phase 3 will add "web-component-driven" for HTML
  // Phase 4 will add "mobile-native-dev" for iOS/Android
};
```

**时间估算**: 1天

#### 任务1.4: 实现 specs.ts
**文件**: `packages/cli/src/types/specs.ts`

```typescript
export interface SpecModule {
  id: string;  // "conventions-shared", "harness-flutter"
  name: string;
  description?: string;
  reusableAcross: string[];  // Project types where this module is applicable
  files: string[];  // Relative paths within spec directory
}

export interface DirectorySpec {
  purpose: string;  // "Project conventions", "Team guides", "Implementation harness"
  files: string[];
  editable: boolean;  // Should user edit these files?
}

export interface SpecFileStructure {
  required: string[];  // Files that must exist
  optional?: string[];  // Files that may not exist
  directories: Record<string, DirectorySpec>;
}

export interface SpecTemplate {
  id: string;  // "guru-flutter-client", "spec-html-web"
  name: string;
  version: string;  // Semantic versioning
  
  // Which project types need this spec
  projectTypes: string[];  // ["flutter"] | ["html"]
  
  // Which platforms can use this spec (optional, default all)
  platforms?: string[];  // ["claude", "codex"]
  
  // Where spec comes from
  source: "bundled" | "marketplace";
  bundledPath?: string;  // Only if bundled
  marketplaceId?: string;  // For marketplace lookup
  
  // Spec file structure
  structure: SpecFileStructure;
  
  // Modular components for reuse
  modules: SpecModule[];
  
  // Metadata
  maintainer?: {
    team: string;
    contact?: string;
  };
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
          purpose: "Project conventions & slots",
          files: [
            "index.md",
            "calorie.project-conventions.md",
            "seek.project-conventions.md",
          ],
          editable: true,
        },
        guides: {
          purpose: "Team guides & patterns",
          files: ["index.md", "golden-path.md"],
          editable: false,
        },
        harness: {
          purpose: "Implementation details",
          files: ["index.md"],
          editable: false,
        },
      },
    },
    
    modules: [
      {
        id: "conventions-shared",
        name: "Shared Project Conventions",
        reusableAcross: ["flutter", "html", "ios", "android"],
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

  // Phase 3 will fill in spec-html-web
  // Phase 4 will fill in spec-ios-swift, spec-android-kotlin
};
```

**时间估算**: 1.5天

#### 任务1.5: 实现 skills.ts
**文件**: `packages/cli/src/types/skills.ts`

```typescript
export interface SkillDefinition {
  id: string;  // "requirement-writing", "flutter-implementation-guru-writing"
  name: string;
  description: string;
  
  // Which project types support this skill
  applicableProjectTypes: string[];  // ["*"] for all | ["flutter"] specific
  
  // Which platforms support this skill
  applicablePlatforms: string[];  // ["claude", "codex"]
  
  // Skill categorization
  category: "writing" | "review" | "utility" | "sop";
  phase?: "planning" | "design" | "implementation" | "review";  // Which workflow phase
  
  // Content source
  source: "bundled" | "marketplace";
  bundledPath?: string;
  marketplaceId?: string;
  
  // Dependencies
  dependencies?: string[];  // Other skill IDs this depends on
}

export const SKILLS: Record<string, SkillDefinition> = {
  // Universal skills (all project types)
  "requirement-writing": {
    id: "requirement-writing",
    name: "Requirement Writing",
    description: "Guide for writing clear project requirements",
    applicableProjectTypes: ["*"],  // All types
    applicablePlatforms: ["claude", "codex"],
    category: "writing",
    phase: "planning",
    source: "bundled",
    bundledPath: "src/templates/guru/skills/requirement-writing.md",
  },

  "requirement-review": {
    id: "requirement-review",
    name: "Requirement Review",
    description: "Guidelines for reviewing requirements",
    applicableProjectTypes: ["*"],
    applicablePlatforms: ["claude", "codex"],
    category: "review",
    phase: "planning",
    source: "bundled",
    bundledPath: "src/templates/guru/skills/requirement-review.md",
  },

  // Flutter-specific skills
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
  },

  "flutter-implementation-guru-review": {
    id: "flutter-implementation-guru-review",
    name: "Flutter Implementation Review",
    description: "Review Flutter implementations",
    applicableProjectTypes: ["flutter"],
    applicablePlatforms: ["claude", "codex"],
    category: "review",
    phase: "implementation",
    source: "bundled",
    bundledPath: "src/templates/guru/skills/flutter-implementation-review.md",
  },

  // Phase 3 will add HTML-specific skills
  // Phase 4 will add iOS/Android-specific skills
};
```

**时间估算**: 1天

#### 任务1.6: 创建注册表导出文件
**文件**: `packages/cli/src/registries/index.ts`

```typescript
export { PROJECT_TYPES, type ProjectTypeDefinition } from "../types/project-types.js"
export { WORKFLOWS, type WorkflowDefinition } from "../types/workflows.js"
export { SPECS, type SpecTemplate } from "../types/specs.ts"
export { SKILLS, type SkillDefinition } from "../types/skills.js"
```

**时间估算**: 0.5天

#### Week 1 小结
- ✅ 4个类型系统（ProjectType, Workflow, Spec, Skill）
- ✅ Flutter完整定义，其他三个项目类型占位符
- ✅ 注册表导出接口
- ✅ 单元测试 (20-30% 覆盖)
- **代码行数**: ~500行
- **提交**: `feat(types): add project type registry system`

---

### Week 2: Resolver 层与兼容性测试

#### 任务2.1: 实现 ProjectTypeResolver
**文件**: `packages/cli/src/resolvers/project-type-resolver.ts`

```typescript
import fs from "node:fs"
import path from "node:path"
import { PROJECT_TYPES, type ProjectTypeDefinition } from "../registries/index.js"

export interface DetectionResult {
  projectType: string;
  typeDef: ProjectTypeDefinition;
  confidence: number;  // 0-1
  detectedFiles: string[];
  reason: string;
}

export class ProjectTypeResolver {
  /**
   * Detect project type by examining directory structure.
   * 
   * Algorithm:
   * 1. For each project type, check detection.files in priority order
   * 2. Count how many files match
   * 3. Select type with highest match count
   * 4. If tie, select first in iteration order
   */
  detect(cwd: string): DetectionResult | null {
    let bestMatch: DetectionResult | null = null;
    let maxMatches = 0;

    for (const [typeId, typeDef] of Object.entries(PROJECT_TYPES)) {
      const files = typeDef.detection.files;
      const minCount = typeDef.detection.minCount ?? 1;
      
      const matches: string[] = [];
      for (const file of files) {
        try {
          fs.statSync(path.join(cwd, file));
          matches.push(file);
        } catch {
          // File not found, continue
        }
      }

      if (matches.length >= minCount && matches.length > maxMatches) {
        maxMatches = matches.length;
        bestMatch = {
          projectType: typeId,
          typeDef,
          confidence: Math.min(matches.length / files.length, 1),
          detectedFiles: matches,
          reason: `Found ${matches.length} detection files: ${matches.join(", ")}`,
        };
      }
    }

    return bestMatch;
  }

  getProjectType(typeId: string): ProjectTypeDefinition {
    const typeDef = PROJECT_TYPES[typeId];
    if (!typeDef) {
      throw new Error(
        `Unknown project type: "${typeId}". ` +
        `Supported: ${Object.keys(PROJECT_TYPES).join(", ")}`
      );
    }
    return typeDef;
  }

  getAllProjectTypes(): string[] {
    return Object.keys(PROJECT_TYPES);
  }
}
```

**时间估算**: 1.5天  
**测试**:
```typescript
describe("ProjectTypeResolver", () => {
  it("detects flutter projects by pubspec.yaml", () => {
    const resolver = new ProjectTypeResolver()
    const result = resolver.detect(flutterProjectPath)
    expect(result?.projectType).toBe("flutter")
    expect(result?.confidence).toBeGreaterThan(0.5)
  })

  it("detects html projects by package.json + index.html", () => {
    const result = resolver.detect(htmlProjectPath)
    expect(result?.projectType).toBe("html")
  })

  it("throws error for unknown project type", () => {
    const resolver = new ProjectTypeResolver()
    expect(() => resolver.getProjectType("unknown")).toThrow()
  })
})
```

#### 任务2.2: 改造 WorkflowResolver
**文件**: `packages/cli/src/resolvers/workflow-resolver.ts` (改造existing)

```typescript
// 改造existing的workflow-resolver.ts

import { WORKFLOWS, type WorkflowDefinition } from "../registries/index.js"

export class WorkflowResolver {
  /**
   * Resolve a workflow by ID.
   * Validates that workflow exists and is properly defined.
   */
  resolve(workflowId: string): WorkflowDefinition {
    const def = WORKFLOWS[workflowId];
    if (!def) {
      const available = Object.keys(WORKFLOWS).join(", ");
      throw new Error(
        `Unknown workflow: "${workflowId}". Available: ${available}`
      );
    }
    return def;
  }

  /**
   * Get all workflows applicable to a specific project type.
   */
  getWorkflowsFor(projectType: string): WorkflowDefinition[] {
    return Object.values(WORKFLOWS).filter(w =>
      w.applicableTo.includes(projectType)
    );
  }

  /**
   * Validate that a workflow can be used with a project type.
   * Returns error message if invalid, null if valid.
   */
  validateWorkflowForProjectType(
    workflowId: string,
    projectType: string
  ): string | null {
    const workflow = this.resolve(workflowId);
    if (!workflow.applicableTo.includes(projectType)) {
      const available = this.getWorkflowsFor(projectType)
        .map(w => w.id)
        .join(", ");
      return (
        `Workflow "${workflowId}" is not applicable to project type "${projectType}". ` +
        `Available workflows: ${available}`
      );
    }
    return null;
  }
}
```

**时间估算**: 1day

#### 任务2.3: 实现 SpecResolver
**文件**: `packages/cli/src/resolvers/spec-resolver.ts`

```typescript
import { SPECS, type SpecTemplate } from "../registries/index.js"

export class SpecResolver {
  resolve(specId: string): SpecTemplate {
    const spec = SPECS[specId];
    if (!spec) {
      const available = Object.keys(SPECS).join(", ");
      throw new Error(
        `Unknown spec template: "${specId}". Available: ${available}`
      );
    }
    return spec;
  }

  getSpecsFor(projectType: string): SpecTemplate[] {
    return Object.values(SPECS).filter(s =>
      s.projectTypes.includes(projectType)
    );
  }

  /**
   * Get the primary spec for a project type.
   * This is determined by the ProjectTypeDefinition.specTemplateId
   */
  getPrimarySpec(projectType: string, projectTypeDef: any): SpecTemplate {
    return this.resolve(projectTypeDef.specTemplateId);
  }

  /**
   * Get reusable spec modules that apply to this project type.
   * These can be included alongside project-type-specific content.
   */
  getReusableModules(projectType: string): any[] {
    const specs = this.getSpecsFor(projectType);
    const modules: any[] = [];
    
    for (const spec of specs) {
      for (const module of spec.modules) {
        if (module.reusableAcross.includes(projectType)) {
          modules.push(module);
        }
      }
    }
    
    return modules;
  }
}
```

**时间估算**: 1day

#### 任务2.4: 实现 SkillResolver
**文件**: `packages/cli/src/resolvers/skill-resolver.ts`

```typescript
import { SKILLS, type SkillDefinition } from "../registries/index.js"

export interface SkillFilterOptions {
  projectType: string;
  platform: string;
  category?: "writing" | "review" | "utility" | "sop";
  phase?: string;
}

export class SkillResolver {
  resolve(skillId: string): SkillDefinition {
    const skill = SKILLS[skillId];
    if (!skill) {
      throw new Error(`Unknown skill: "${skillId}"`);
    }
    return skill;
  }

  /**
   * Get all skills applicable for a given context.
   * Filters by project type, platform, and optionally category/phase.
   */
  getSkillsFor(options: SkillFilterOptions): SkillDefinition[] {
    return Object.values(SKILLS).filter(skill => {
      // Check project type applicability
      const typeMatch =
        skill.applicableProjectTypes.includes("*") ||
        skill.applicableProjectTypes.includes(options.projectType);
      
      if (!typeMatch) return false;

      // Check platform applicability
      const platformMatch = skill.applicablePlatforms.includes(options.platform);
      if (!platformMatch) return false;

      // Check category if specified
      if (options.category && skill.category !== options.category) {
        return false;
      }

      // Check phase if specified
      if (options.phase && skill.phase !== options.phase) {
        return false;
      }

      return true;
    });
  }

  /**
   * Get skills for a specific workflow phase.
   */
  getSkillsByPhase(
    phase: string,
    projectType: string,
    platform: string
  ): SkillDefinition[] {
    return this.getSkillsFor({
      projectType,
      platform,
      phase,
    });
  }
}
```

**时间估算**: 1day

#### 任务2.5: 向后兼容性测试
**文件**: `packages/cli/test/integration/backward-compat.test.ts`

```typescript
describe("Backward Compatibility", () => {
  describe("Flutter + guru-client workflow", () => {
    it("detects flutter projects correctly", () => {
      const resolver = new ProjectTypeResolver();
      const result = resolver.detect(flutterProjectPath);
      expect(result?.projectType).toBe("flutter");
    });

    it("defaults to guru-client workflow for flutter", () => {
      const typeDef = resolver.getProjectType("flutter");
      expect(typeDef.defaultWorkflow).toBe("guru-client");
    });

    it("resolves guru-client workflow successfully", () => {
      const workflowResolver = new WorkflowResolver();
      const workflow = workflowResolver.resolve("guru-client");
      expect(workflow.applicableTo).toContain("flutter");
    });

    it("validates guru-client is applicable to flutter", () => {
      const error = workflowResolver.validateWorkflowForProjectType(
        "guru-client",
        "flutter"
      );
      expect(error).toBeNull();
    });

    it("resolves guru-flutter-client spec", () => {
      const specResolver = new SpecResolver();
      const spec = specResolver.resolve("guru-flutter-client");
      expect(spec.projectTypes).toContain("flutter");
    });

    it("filters flutter-specific skills correctly", () => {
      const skillResolver = new SkillResolver();
      const skills = skillResolver.getSkillsFor({
        projectType: "flutter",
        platform: "claude",
        phase: "implementation",
      });
      expect(skills.map(s => s.id)).toContain("flutter-implementation-guru-writing");
    });
  });

  describe("No regressions in init flow", () => {
    it("flutter + claude code initializes successfully", async () => {
      const result = await initWithNewArchitecture({
        cwd: flutterProjectPath,
        platform: "claude",
        workflow: "guru-client",
      });
      expect(result.success).toBe(true);
    });

    it("existing .trellis/workflow.md has expected content", async () => {
      // Verify guru-client workflow is applied
      expect(fs.readFileSync(...)).toContain("五阶段");
    });

    it("apply_test.sh scenarios still pass", async () => {
      // Run 14 test scenarios from apply_test.sh
      // All should pass
    });
  });
});
```

**时间估算**: 1.5天

#### Week 2 小结
- ✅ 4个 Resolver 完整实现
- ✅ 向后兼容性测试
- ✅ 单元测试 (40-50% 覆盖)
- **代码行数**: ~600行
- **提交**: `feat(resolvers): add project type/workflow/spec/skill resolvers`

---

## 第二阶段：核心改造（第3-5周）

### Week 3: 改造 init.ts 和适配器工厂

#### 任务3.1: 创建适配器接口与工厂
**文件**: `packages/cli/src/adapters/adapter-factory.ts`

```typescript
import { ProjectTypeDefinition, WorkflowDefinition, SpecTemplate } from "../types/index.js"
import { ProjectTypeAdapter, PlatformAdapter } from "./types.js"

export interface AdapterContext {
  cwd: string;
  projectType: ProjectTypeDefinition;
  workflow: WorkflowDefinition;
  spec: SpecTemplate;
  platform: string;
}

export class AdapterFactory {
  /**
   * Create a platform adapter (Claude Code, Codex, etc).
   * Platform adapters handle:
   * - settings.json configuration
   * - Hook injection
   * - Platform-specific file structures
   */
  createPlatformAdapter(
    platform: string,
    context: AdapterContext
  ): PlatformAdapter {
    switch (platform) {
      case "claude":
        return new ClaudeCodeAdapter(context);
      case "codex":
        return new CodexAdapter(context);
      // NOTE: No Cursor support per requirements
      default:
        throw new Error(
          `Unknown platform: "${platform}". Supported: claude, codex`
        );
    }
  }

  /**
   * Create a project type adapter (Flutter, HTML, iOS, Android).
   * Project type adapters handle:
   * - Project type-specific configuration
   * - Framework-specific files (eslint, gradle, etc)
   * - Type-specific hooks
   */
  createProjectTypeAdapter(projectType: string): ProjectTypeAdapter {
    switch (projectType) {
      case "flutter":
        return new FlutterAdapter();
      case "html":
        return new HtmlAdapter();
      case "ios":
        return new IosAdapter();
      case "android":
        return new AndroidAdapter();
      default:
        return new DefaultProjectTypeAdapter();
    }
  }
}

// Imports (to be implemented in separate files)
import { ClaudeCodeAdapter } from "./platform-adapters/claude-code.js"
import { CodexAdapter } from "./platform-adapters/codex.js"
import { FlutterAdapter } from "./project-type-adapters/flutter-adapter.js"
import { HtmlAdapter } from "./project-type-adapters/html-adapter.js"
import { IosAdapter } from "./project-type-adapters/ios-adapter.js"
import { AndroidAdapter } from "./project-type-adapters/android-adapter.js"
import { DefaultProjectTypeAdapter } from "./project-type-adapters/default-adapter.js"
```

**时间估算**: 1.5天

#### 任务3.2: 改造 init.ts 命令
**文件**: `packages/cli/src/commands/init.ts` (改造existing, 关键部分)

```typescript
// KEY CHANGES to existing init.ts

import {
  ProjectTypeResolver,
  WorkflowResolver,
  SpecResolver,
  SkillResolver,
} from "../resolvers/index.js"
import { AdapterFactory } from "../adapters/adapter-factory.js"

export async function init(options: InitOptions) {
  // ============================================================================
  // STEP 1: Detect project type
  // ============================================================================
  const projectTypeResolver = new ProjectTypeResolver();
  const detectionResult = projectTypeResolver.detect(cwd);
  
  if (!detectionResult) {
    console.error(
      `Could not detect project type. ` +
      `Supported types: ${projectTypeResolver.getAllProjectTypes().join(", ")}`
    );
    process.exit(1);
  }

  const projectType = detectionResult.projectType;
  const projectTypeDef = detectionResult.typeDef;
  
  console.log(`Detected project type: ${projectTypeDef.name}`);

  // ============================================================================
  // STEP 2: Select/validate workflow
  // ============================================================================
  const workflowResolver = new WorkflowResolver();
  
  // If --workflow not specified, use default
  let workflowId = options.workflow || projectTypeDef.defaultWorkflow;
  
  // Validate workflow is applicable to project type
  const validationError = workflowResolver.validateWorkflowForProjectType(
    workflowId,
    projectType
  );
  
  if (validationError) {
    console.error(`❌ ${validationError}`);
    const available = workflowResolver
      .getWorkflowsFor(projectType)
      .map(w => w.id)
      .join(", ");
    console.log(`Available workflows: ${available}`);
    process.exit(1);
  }

  const workflowDef = workflowResolver.resolve(workflowId);
  console.log(`Using workflow: ${workflowDef.name}`);

  // ============================================================================
  // STEP 3: Resolve spec template
  // ============================================================================
  const specResolver = new SpecResolver();
  const specDef = specResolver.resolve(projectTypeDef.specTemplateId);
  
  if (!specDef.bundledSpec && specDef.source === "bundled") {
    // This shouldn't happen, but let's catch it
    throw new Error(
      `Spec ${specDef.id} marked as bundled but source is bundled. ` +
      `This is a configuration error.`
    );
  }

  console.log(`Using spec template: ${specDef.name}`);

  // ============================================================================
  // STEP 4: Resolve skills
  // ============================================================================
  const skillResolver = new SkillResolver();
  const skills = skillResolver.getSkillsFor({
    projectType,
    platform: options.platform,  // "claude" or "codex"
  });

  console.log(
    `Found ${skills.length} skills for ${projectType} on ${options.platform}`
  );

  // ============================================================================
  // STEP 5: Create adapters
  // ============================================================================
  const adapterFactory = new AdapterFactory();
  
  const platformAdapter = adapterFactory.createPlatformAdapter(
    options.platform,
    {
      cwd,
      projectType: projectTypeDef,
      workflow: workflowDef,
      spec: specDef,
      platform: options.platform,
    }
  );

  const projectTypeAdapter = adapterFactory.createProjectTypeAdapter(projectType);

  // ============================================================================
  // STEP 6: Generate files
  // ============================================================================
  await generateFilesWithAdapters({
    cwd,
    projectTypeDef,
    workflowDef,
    specDef,
    skills,
    platformAdapter,
    projectTypeAdapter,
    options,
  });

  console.log("✅ Initialization complete!");
}

/**
 * New helper function that uses adapters to generate files.
 * This replaces the old logic that was scattered throughout init.ts
 */
async function generateFilesWithAdapters(context: {
  cwd: string;
  projectTypeDef: ProjectTypeDefinition;
  workflowDef: WorkflowDefinition;
  specDef: SpecTemplate;
  skills: SkillDefinition[];
  platformAdapter: PlatformAdapter;
  projectTypeAdapter: ProjectTypeAdapter;
  options: InitOptions;
}) {
  // 1. Create .trellis/ directory
  await fs.promises.mkdir(path.join(context.cwd, ".trellis"), { recursive: true });

  // 2. Install workflow
  await installWorkflow(context.cwd, context.workflowDef);

  // 3. Install spec files
  await installSpec(context.cwd, context.specDef);

  // 4. Platform adapter configuration
  await context.platformAdapter.configure(context);

  // 5. Project type adapter configuration
  await context.projectTypeAdapter.generateFiles(context);

  // 6. Write manifest
  await createManifest(context.cwd, {
    projectType: context.projectTypeDef.id,
    workflow: context.workflowDef.id,
    spec: context.specDef.id,
  });
}
```

**时间估算**: 2.5天

#### 任务3.3: 创建 Flutter 适配器（向后兼容）
**文件**: `packages/cli/src/adapters/project-type-adapters/flutter-adapter.ts`

```typescript
import { ProjectTypeAdapter } from "../types.js"

/**
 * Flutter-specific adapter.
 * Since Flutter was already supported, this adapter mostly wraps
 * existing logic and ensures backward compatibility.
 */
export class FlutterAdapter implements ProjectTypeAdapter {
  async generateFiles(context: any): Promise<void> {
    // Flutter-specific setup (if any)
    // For now, just ensure existing behavior is preserved
    
    // Could add:
    // - pubspec.yaml validation
    // - iOS/Android detection
    // - Flutter-specific hooks
  }

  async configureHooks(context: any): Promise<void> {
    // Flutter-specific hook configuration
  }

  getConfigDefaults(): Record<string, any> {
    return {
      // Flutter-specific defaults
      framework: "flutter",
      minDartVersion: "2.17",
    };
  }
}
```

**时间估算**: 0.5day

#### 任务3.4: 创建默认项目类型适配器
**文件**: `packages/cli/src/adapters/project-type-adapters/default-adapter.ts`

```typescript
import { ProjectTypeAdapter } from "../types.js"

/**
 * Default adapter for project types without special requirements.
 * Used for HTML, iOS, Android until their specific adapters are created.
 */
export class DefaultProjectTypeAdapter implements ProjectTypeAdapter {
  async generateFiles(context: any): Promise<void> {
    // Default: no additional files needed
  }

  async configureHooks(context: any): Promise<void> {
    // Default: no special hooks
  }

  getConfigDefaults(): Record<string, any> {
    return {};
  }
}
```

**时间估算**: 0.3day

#### Week 3 小结
- ✅ 改造 init.ts 使用注册表和解析器
- ✅ 适配器工厂和接口
- ✅ Flutter 适配器（向后兼容）
- ✅ 默认适配器
- **代码行数**: ~700行 (改造init.ts + 新适配器)
- **提交**: `refactor(init): use registry-driven architecture with adapters`

---

### Week 4: Claude Code 和 Codex 平台适配器

#### 任务4.1: Claude Code 平台适配器
**文件**: `packages/cli/src/adapters/platform-adapters/claude-code.ts`

```typescript
import { PlatformAdapter } from "../types.js"

/**
 * Claude Code platform adapter.
 * Handles:
 * - settings.json configuration
 * - Hook injection for SessionStart, PreToolUse
 * - Claude-specific file structures
 */
export class ClaudeCodeAdapter implements PlatformAdapter {
  async configure(context: any): Promise<void> {
    // Configure Claude Code specific settings
    await this.setupSettingsJson(context);
    await this.setupHooks(context);
  }

  private async setupSettingsJson(context: any): Promise<void> {
    // 1. Load existing settings.json if present
    // 2. Apply JSON merge defaults from shared.ts
    // 3. Write merged settings.json
    // 4. Record in manifest
  }

  private async setupHooks(context: any): Promise<void> {
    // 1. For each hook in platformAdapter config
    // 2. Create .claude/hooks/ directory
    // 3. Copy hook files
    // 4. Inject platform-specific references
  }
}
```

**时间估算**: 2days

#### 任务4.2: Codex 平台适配器
**文件**: `packages/cli/src/adapters/platform-adapters/codex.ts`

```typescript
export class CodexAdapter implements PlatformAdapter {
  async configure(context: any): Promise<void> {
    // Configure Codex specific settings
    await this.setupAgentsMd(context);
    await this.setupHooks(context);
  }

  private async setupAgentsMd(context: any): Promise<void> {
    // 1. Create .codex/AGENTS.md
    // 2. Inject skills into Codex format
    // 3. Apply block-level merging if existing AGENTS.md
  }

  private async setupHooks(context: any): Promise<void> {
    // 1. Create .codex/hooks.json
    // 2. Inject PreToolUse hooks
    // 3. Apply JSON merge if existing
  }
}
```

**时间估算**: 2days

#### Week 4 小结
- ✅ Claude Code 适配器完整
- ✅ Codex 适配器完整
- ✅ 集成测试 (初始化 + 文件验证)
- **代码行数**: ~800行
- **提交**: `feat(adapters): add platform-specific adapters for claude and codex`

---

### Week 5: 集成测试与向后兼容性验证

#### 任务5.1: 集成测试套件
**文件**: `packages/cli/test/integration/init-with-registry.test.ts`

```typescript
describe("Init with registry-driven architecture", () => {
  describe("Flutter + Claude Code", () => {
    it("initializes flutter project with guru-client workflow", async () => {
      // Create flutter project
      // Run init --claude
      // Verify all files exist
      // Verify .trellis/workflow.md contains guru-client content
      // Verify .claude/settings.json configured
    });
  });

  describe("HTML + Claude Code", () => {
    it("initializes html project with native workflow", async () => {
      // (Will pass once HTML support added in Phase 3)
    });
  });

  describe("iOS + Claude Code", () => {
    it("initializes ios project with native workflow", async () => {
      // (Will pass once iOS support added in Phase 4)
    });
  });

  describe("Android + Claude Code", () => {
    it("initializes android project with native workflow", async () => {
      // (Will pass once Android support added in Phase 4)
    });
  });

  describe("Workflow validation", () => {
    it("rejects unsupported workflow for project type", async () => {
      // Try to initialize html project with guru-client workflow
      // Should fail with clear error message
    });
  });
});
```

**时间估算**: 1.5天

#### 任务5.2: 向后兼容性测试
**文件**: `packages/cli/test/integration/backward-compat-full.test.ts`

```typescript
describe("Backward compatibility with existing Flutter setup", () => {
  it("applies.sh still passes all 14 scenarios", async () => {
    // Run guru-template/overlay/tests/apply_test.sh
    // Expect 14/14 pass
  });

  it("existing flutter projects detect correctly", async () => {
    // Create flutter project
    // Run init (no args)
    // Verify project type detected as "flutter"
    // Verify workflow defaulted to "guru-client"
  });

  it("guru-client workflow content unchanged", async () => {
    // Verify .trellis/workflow.md content matches original
  });

  it("guru-flutter-client spec unchanged", async () => {
    // Verify all 16 spec files present
    // Verify content unchanged
  });
});
```

**时间估算**: 1.5day

#### 任务5.3: 性能和边界测试
**文件**: `packages/cli/test/integration/edge-cases.test.ts`

```typescript
describe("Edge cases and error handling", () => {
  it("handles project with multiple type indicators", async () => {
    // Create project with both pubspec.yaml (flutter) and package.json (html)
    // Verify correct detection (pubspec.yaml has priority)
  });

  it("provides clear error for unknown project type", async () => {
    // Run init in empty directory
    // Expect helpful error message listing supported types
  });

  it("provides clear error for unsupported workflow", async () => {
    // Try html project with guru-client workflow
    // Expect error showing available workflows for HTML
  });

  it("handles missing spec templates gracefully", async () => {
    // Verify error if referenced spec doesn't exist in registry
  });
});
```

**时间估算**: 1day

#### Week 5 小结
- ✅ 集成测试 (80% 覆盖)
- ✅ 向后兼容性验证
- ✅ 边界情况处理
- ✅ 所有项目类型的基础检测工作
- **代码行数**: ~400行 (测试)
- **提交**: `test(integration): comprehensive tests for registry-driven init`

**Phase 2 总结**:
- 总投入: 3周
- 代码行数: ~2500行
- 改造影响: 仅 init.ts + 新增 adapters
- Flutter 向后兼容: 100% ✅
- 测试覆盖: ~70%

---

## 第三阶段：HTML支持（第6周）

### 任务6.1-6.5: 添加HTML项目类型

（按照跨平台文档中"添加新项目类型"的5步流程）

1. 在 PROJECT_TYPES 注册 HTML (50行)
2. 在 WORKFLOWS 注册 web-component-driven (20行)
3. 在 SPECS 注册 spec-html-web (40行)
4. 在 SKILLS 注册 html-component-writing (15行)
5. 创建 HtmlAdapter (50行)

**测试**:
```bash
mkdir /tmp/html-test && cd /tmp/html-test
npm init -y && echo "<html></html>" > index.html
trellis init --claude -y

# Verify
✅ Project type detected as "html"
✅ Default workflow is "native"
✅ spec-html-web applied
✅ html-component-writing skill injected
✅ .eslintrc.json/.prettierrc.json generated
```

**时间估算**: 5天  
**提交**: `feat(html): add complete HTML/Web project type support`

---

## 第四阶段：iOS/Android支持（第7周）

### 任务7.1-7.2: 快速接入iOS和Android

复用HTML的注册表和适配器样板。

1. iOS 注册 (30行) + IosAdapter (30行)
2. Android 注册 (30行) + AndroidAdapter (30行)

**时间估算**: 5天  
**提交**: `feat(mobile): add iOS and Android native project type support`

---

## 项目统计与里程碑

### 代码行数汇总

| 阶段 | 内容 | 行数 |
|------|------|------|
| Phase 1 | types + registries | 500 |
| Phase 2 | resolvers + init改造 + adapters | 2500 |
| Phase 2 | 测试 | 400 |
| Phase 3 | HTML support | 200 |
| Phase 4 | iOS + Android | 200 |
| **总计** | | **3800** |

### 时间投入

| 阶段 | 周数 | 人天 |
|------|------|------|
| 1: 基础 | 2 | 8 |
| 2: 改造 | 3 | 12 |
| 3: HTML | 1 | 4 |
| 4: 移动 | 1 | 4 |
| **总计** | **7** | **28** |

### 里程碑

```
Week 1-2: ✅ Architecture foundation
  └─ 4 registries, 4 resolvers, Flutter defined

Week 3-5: ✅ Core refactoring
  └─ init.ts refactored, adapters working, backward compat 100%

Week 6: ✅ HTML support
  └─ trellis init --html --claude works

Week 7: ✅ Mobile support
  └─ trellis init --ios --claude works
  └─ trellis init --android --claude works

Celebration: 🎉 Flutter + HTML + iOS + Android all supported!
```

---

## 关键指标与质量保障

### 测试覆盖目标

| 阶段 | 覆盖率 | 重点 |
|------|--------|------|
| Phase 1 | 30% | Registries 正确性 |
| Phase 2 | 70% | Init 流程, 适配器, 向后兼容 |
| Phase 3+ | 85% | 新项目类型功能 |

### 向后兼容检查点

- ✅ Flutter 项目自动检测
- ✅ guru-client 默认工作流
- ✅ apply.sh 14 场景全过
- ✅ 现有文档无改动
- ✅ 现有 shell 脚本无改动

### 代码质量指标

| 指标 | 目标 |
|------|------|
| TypeScript 编译 | 无错误 |
| Lint 检查 | 0 warnings |
| 单元测试 | >80% 覆盖 |
| 集成测试 | 所有场景通过 |
| E2E 测试 | 4 项目类型 × 2 平台 |

---

## 风险管理

### 识别的风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 改造 init.ts 导致回归 | 中 | 高 | 完整的向后兼容测试 |
| 注册表维护复杂 | 低 | 中 | 清晰的 TS interfaces |
| 新开发者理解困难 | 低 | 中 | 详细的代码注释和文档 |
| 项目类型检测冲突 | 低 | 中 | 优先级排序和测试 |

### 应急方案

如果 Phase 2 遇到问题，可以：
1. 回滚到改造前的 init.ts（版本控制）
2. Flutter 功能不受影响（新代码逐步集成）
3. 继续使用旧的工作流解析（兼容层）

---

## 交付物清单

### Phase 1
- [ ] src/types/project-types.ts (ProjectTypeDefinition)
- [ ] src/types/workflows.ts (WorkflowDefinition)
- [ ] src/types/specs.ts (SpecTemplate)
- [ ] src/types/skills.ts (SkillDefinition)
- [ ] test/types/*.test.ts (单元测试)

### Phase 2
- [ ] src/resolvers/project-type-resolver.ts
- [ ] src/resolvers/workflow-resolver.ts (改造)
- [ ] src/resolvers/spec-resolver.ts
- [ ] src/resolvers/skill-resolver.ts
- [ ] src/commands/init.ts (改造, 核心)
- [ ] src/adapters/adapter-factory.ts
- [ ] src/adapters/platform-adapters/claude-code.ts
- [ ] src/adapters/platform-adapters/codex.ts
- [ ] src/adapters/project-type-adapters/flutter-adapter.ts
- [ ] src/adapters/project-type-adapters/default-adapter.ts
- [ ] test/integration/backward-compat-full.test.ts
- [ ] test/integration/init-with-registry.test.ts

### Phase 3
- [ ] UPDATE src/registries/project-type-registry.ts (add HTML)
- [ ] UPDATE src/registries/workflow-registry.ts (add web-component-driven)
- [ ] UPDATE src/registries/spec-registry.ts (add spec-html-web)
- [ ] UPDATE src/registries/skill-registry.ts (add HTML skills)
- [ ] src/adapters/project-type-adapters/html-adapter.ts
- [ ] test/integration/html-init.test.ts

### Phase 4
- [ ] UPDATE registries (add iOS + Android)
- [ ] src/adapters/project-type-adapters/ios-adapter.ts
- [ ] src/adapters/project-type-adapters/android-adapter.ts
- [ ] test/integration/mobile-init.test.ts

### 文档
- [ ] CROSS_PLATFORM_ARCHITECTURE.md (已完成)
- [ ] CROSS_PLATFORM_IMPLEMENTATION.md (已完成)
- [ ] 此计划文档 (DETAILED_IMPLEMENTATION_PLAN.md)
- [ ] 开发指南 (添加新项目类型的 SOP)
- [ ] API 参考 (Resolver, Adapter 接口)

---

## 开发工作流

### 每日工作

```bash
# 开始工作
git checkout -b feat/cross-platform-phase-N

# 编写代码
code src/types/project-types.ts

# 运行测试
pnpm -C packages/cli test --run

# 查看覆盖率
pnpm -C packages/cli test --coverage

# 提交
git commit -m "feat: ..."

# 推送到 origin
git push origin feat/cross-platform-phase-N
```

### 代码审核清单

- [ ] TypeScript 编译无错误
- [ ] ESLint 无 warnings
- [ ] 新接口有 JSDoc 注释
- [ ] 单元测试存在且通过
- [ ] 向后兼容性已验证
- [ ] 没有 console.log 或调试代码

### 分支合并策略

```bash
# Phase 完成后
git checkout guru/main
git pull origin guru/main
git merge feat/cross-platform-phase-N
git push origin guru/main

# 发布新版本
# 更新 package.json: 0.6.0-rc.0-guru.2
# npm publish --tag guru
```

---

## 成功标准

### Phase 1 成功标准
- ✅ 4 个注册表接口清晰
- ✅ Flutter 定义完整（所有字段都有值）
- ✅ 其他3个项目类型占位符合理
- ✅ 单元测试 30%+ 覆盖

### Phase 2 成功标准
- ✅ init.ts 改造完成
- ✅ apply.sh 14 场景全过
- ✅ Flutter 无任何功能回归
- ✅ 集成测试 70%+ 覆盖
- ✅ 新开发者可按指南添加新项目类型

### Phase 3/4 成功标准
- ✅ `trellis init --html --claude` 成功
- ✅ `trellis init --ios --claude` 成功
- ✅ `trellis init --android --claude` 成功
- ✅ 所有新项目类型的集成测试通过

---

## 常见问题

### Q: 如何处理项目类型检测冲突？
A: 在 detectionConfig 中定义 files 的优先级。检测器按顺序检查，找到匹配最多的就是该类型。

### Q: 新项目类型需要新的工作流吗？
A: 不一定。可以复用 "native" 工作流。但如果需要特定的阶段或gate策略，可创建新工作流。

### Q: 如何向后兼容现有脚本？
A: 所有改造都在内部（init.ts）。外部 CLI 接口不变。apply.sh 完全不需改动。

### Q: 注册表如何版本管理？
A: 在 ProjectTypeDefinition / WorkflowDefinition 中添加 version 字段。迁移逻辑在 resolver 中。

### Q: 测试应该在什么时候写？
A: TDD 方式：先写测试（红），再实现（绿），再重构（蓝）。或每完成一个任务立即补测试。

---

## 下一步行动

### 立即（今天）
1. 评审此计划
2. 获得批准
3. 创建 feature branch: `feat/cross-platform-phase-1`

### 本周（第1周开始）
1. 创建 src/types/ 目录结构
2. 实现 project-types.ts
3. 编写单元测试

### 预期产出
- Week 1 结束: 4 个注册表完整, 100 行测试
- Week 2 结束: 4 个 resolver, 向后兼容验证
- Week 3 结束: init.ts 改造完成, 20 个集成测试
- Week 5 结束: 所有测试通过, 代码审核完成
- Week 6 结束: HTML 完整支持
- Week 7 结束: iOS + Android 完整支持

---

**文档作者**: Claude Fable 5  
**创建日期**: 2026-06-13  
**版本**: 1.0  
**状态**: 准备实施

