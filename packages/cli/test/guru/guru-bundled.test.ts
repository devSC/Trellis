/**
 * Guru fork additions: bundled workflow/spec resolution, transient-error
 * retry, env-configurable timeouts, and defaults-style settings merge.
 */

import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  GURU_CLIENT_WORKFLOW_ID,
  GURU_GO_WORKFLOW_ID,
  GURU_IOS_WORKFLOW_ID,
  GURU_H5_WORKFLOW_ID,
  NATIVE_WORKFLOW_ID,
  listWorkflowTemplates,
  resolveWorkflowTemplate,
} from "../../src/utils/workflow-resolver.js";
import {
  downloadTemplateById,
  readTimeoutEnv,
  retryOnTransientError,
} from "../../src/utils/template-fetcher.js";
import {
  getBundledSpecFiles,
  listBundledSpecTemplateIds,
} from "../../src/templates/guru/index.js";
import { mergeJsonDefaults } from "../../src/configurators/shared.js";

const GURU_OVERLAY_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../src/templates/guru/overlay",
);
const GURU_TEMPLATE_ROOT = path.resolve(GURU_OVERLAY_ROOT, "..");
const GURU_SOURCE_OVERLAY_ROOT = path.resolve(
  GURU_OVERLAY_ROOT,
  "../../../../../../guru-template/overlay",
);
const TRELLIS_SOURCE_TASK_STORE = path.resolve(
  GURU_OVERLAY_ROOT,
  "../../../../../../.trellis/scripts/common/task_store.py",
);
const TRELLIS_TEMPLATE_SCRIPTS_ROOT = path.resolve(
  GURU_OVERLAY_ROOT,
  "../../trellis/scripts",
);
const DIST_CLI = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../dist/cli/index.js",
);
const PYTHON_NO_BYTECODE_ENV = {
  ...process.env,
  PYTHONDONTWRITEBYTECODE: "1",
};

function overlayPath(...segments: string[]): string {
  return path.join(GURU_OVERLAY_ROOT, ...segments);
}

function readOverlayFile(...segments: string[]): string {
  return fs.readFileSync(overlayPath(...segments), "utf8");
}

function listFilesRecursive(root: string): string[] {
  if (!fs.existsSync(root)) return [];

  const files: string[] = [];
  for (const entry of fs.readdirSync(root)) {
    const fullPath = path.join(root, entry);
    if (fs.statSync(fullPath).isDirectory()) {
      files.push(...listFilesRecursive(fullPath));
    } else {
      files.push(fullPath);
    }
  }

  return files;
}

describe("bundled guru-client workflow", () => {
  it("resolves offline without network access", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network must not be touched for bundled ids");
      }),
    );
    try {
      const resolved = await resolveWorkflowTemplate(GURU_CLIENT_WORKFLOW_ID);
      expect(resolved.source).toBe("bundled");
      expect(resolved.content).toContain("五阶段");
      expect(resolved.content).toContain("review_runs");
      expect(resolved.content).toContain("record-review");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("lists native and guru-client even when the marketplace is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("", { status: 500 })),
    );
    try {
      const { templates } = await listWorkflowTemplates();
      const ids = templates.map((t) => t.id);
      expect(ids).toContain(NATIVE_WORKFLOW_ID);
      expect(ids).toContain(GURU_CLIENT_WORKFLOW_ID);
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("bundled multi-platform guru workflows", () => {
  const PLATFORMS = [
    GURU_GO_WORKFLOW_ID,
    GURU_IOS_WORKFLOW_ID,
    GURU_H5_WORKFLOW_ID,
  ];

  function workflowStateBlock(content: string, name: string): string {
    const start = `[workflow-state:${name}]`;
    const end = `[/workflow-state:${name}]`;
    const startIndex = content.indexOf(start);
    const endIndex = content.indexOf(end);
    expect(startIndex, `missing ${start}`).toBeGreaterThanOrEqual(0);
    expect(endIndex, `missing ${end}`).toBeGreaterThan(startIndex);
    return content.slice(startIndex + start.length, endIndex);
  }

  it("lists every bundled platform workflow even when the marketplace is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("", { status: 500 })),
    );
    try {
      const { templates } = await listWorkflowTemplates();
      const ids = templates.map((t) => t.id);
      for (const id of [GURU_CLIENT_WORKFLOW_ID, ...PLATFORMS]) {
        expect(ids).toContain(id);
      }
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("resolves each platform workflow offline with five-phase content", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network must not be touched for bundled ids");
      }),
    );
    try {
      for (const id of PLATFORMS) {
        const resolved = await resolveWorkflowTemplate(id);
        expect(resolved.id).toBe(id);
        expect(resolved.source).toBe("bundled");
        expect(resolved.content).toContain("五阶段");
      }
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("defaults ordinary in_progress routing to channel while preserving rollback modes", async () => {
    for (const id of [GURU_CLIENT_WORKFLOW_ID, ...PLATFORMS]) {
      const resolved = await resolveWorkflowTemplate(id);
      const defaultRoute = workflowStateBlock(resolved.content, "in_progress");
      const channelRoute = workflowStateBlock(
        resolved.content,
        "in_progress-channel",
      );
      const legacyRoute = workflowStateBlock(
        resolved.content,
        "in_progress-sub-agent",
      );
      const inlineRoute = workflowStateBlock(
        resolved.content,
        "in_progress-inline",
      );

      expect(defaultRoute).toContain("trellis channel");
      expect(defaultRoute).toContain("guru_supervise.py");
      expect(defaultRoute).not.toContain("dispatch trellis-implement");
      expect(channelRoute).toContain("guru_supervise.py");
      expect(channelRoute).toContain("done/error/killed");
      expect(legacyRoute).toContain("dispatch trellis-implement");
      expect(legacyRoute).toContain("Active task: <path>");
      expect(inlineRoute).toContain("trellis-before-dev");
    }
  });
});

describe("bundled multi-platform guru spec packages", () => {
  const SPECS = ["guru-go-backend", "guru-ios-native", "guru-h5-web"];

  it("registers every platform spec as bundled (offline-installable)", () => {
    const ids = listBundledSpecTemplateIds();
    for (const id of ["guru-flutter-client", ...SPECS]) {
      expect(ids).toContain(id);
    }
  });

  it("each platform spec ships the core harness SSOT files", () => {
    for (const id of SPECS) {
      const files = getBundledSpecFiles(id);
      if (files === null) throw new Error(`expected bundled spec ${id}`);
      const keys = [...files.keys()];
      expect(keys).toContain("harness/index.md");
      expect(keys).toContain("guides/golden-path.md");
      expect(
        keys.some((k) =>
          k.startsWith("harness/overview/overview-structure-single-source"),
        ),
      ).toBe(true);
      expect(
        keys.some((k) =>
          k.startsWith("harness/detail/detail-structure-single-source"),
        ),
      ).toBe(true);
    }
  });

  it("each platform harness index mentions requirements adversarial review before confirmation", () => {
    for (const id of ["guru-flutter-client", ...SPECS]) {
      const files = getBundledSpecFiles(id);
      if (files === null) throw new Error(`expected bundled spec ${id}`);
      const index = files.get("harness/index.md");
      expect(index).toContain(
        "requirements 结构通过后先运行 opposite-provider adversarial requirements review",
      );
      expect(index).toContain("clean/requirements-ready 后由用户确认");
    }
  });

  it("each platform spec ships its by-layer project-spec index files", () => {
    const BYLAYER: Record<string, string[]> = {
      "guru-flutter-client": ["flutter", "service", "shared"],
      "guru-go-backend": ["backend", "shared"],
      "guru-ios-native": ["ios", "shared"],
      "guru-h5-web": ["frontend", "backend", "shared"],
    };
    for (const [id, layers] of Object.entries(BYLAYER)) {
      const files = getBundledSpecFiles(id);
      if (files === null) throw new Error(`expected bundled spec ${id}`);
      const keys = [...files.keys()];
      for (const layer of layers) {
        expect(keys).toContain(`${layer}/index.md`);
      }
    }
  });
});

describe("bundled guru overlay", () => {
  it("exposes Guru apply install-time switches", () => {
    const cliSource = fs.readFileSync(
      path.resolve(
        path.dirname(fileURLToPath(import.meta.url)),
        "../../src/cli/index.ts",
      ),
      "utf8",
    );
    const guruSource = fs.readFileSync(
      path.resolve(
        path.dirname(fileURLToPath(import.meta.url)),
        "../../src/commands/guru.ts",
      ),
      "utf8",
    );

    expect(cliSource).toContain("--with-gitnexus");
    expect(cliSource).toContain("--adversarial-enabled");
    expect(cliSource).toContain("withGitnexus");
    expect(cliSource).toContain("adversarialEnabled");
    expect(guruSource).toContain("GURU_WITH_GITNEXUS");
    expect(guruSource).toContain("GURU_ADVERSARIAL_ENABLED");
    expect(readOverlayFile("apply.sh")).toContain("GURU_WITH_GITNEXUS");
    expect(readOverlayFile("apply.sh")).toContain("GURU_ADVERSARIAL_ENABLED");
  });

  it("packs the Guru command and overlay files into the npm tarball", () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "guru-pack-"));
    try {
      execFileSync("pnpm", ["pack", "--pack-destination", tmpDir, "--json"], {
        cwd: path.resolve(
          path.dirname(fileURLToPath(import.meta.url)),
          "../..",
        ),
        encoding: "utf8",
      });
      const tarball = fs
        .readdirSync(tmpDir)
        .find((file) => file.endsWith(".tgz"));
      if (!tarball) {
        throw new Error("pnpm pack did not produce a tarball");
      }
      const tarballPath = path.join(tmpDir, tarball);
      const listing = execFileSync("tar", ["-tzf", tarballPath], {
        encoding: "utf8",
      }).split(/\r?\n/);

      expect(listing).toContain("package/bin/trellis.js");
      expect(listing).toContain("package/dist/commands/guru.js");
      expect(listing).toContain("package/dist/cli/index.js");
      expect(listing).toContain("package/dist/templates/guru/overlay/apply.sh");
      expect(listing).toContain(
        "package/dist/templates/guru/overlay/verify/guru_gate.py",
      );
      expect(listing).toContain(
        "package/dist/templates/guru/overlay/verify/guru_supervise.py",
      );
      expect(listing).toContain(
        "package/dist/templates/guru/overlay/agents-skills/h5-design-overview-review/SKILL.md",
      );

      const packedPackageJson = execFileSync(
        "tar",
        ["-xOf", tarballPath, "package/package.json"],
        { encoding: "utf8" },
      );
      const packedManifest = JSON.parse(packedPackageJson) as {
        dependencies?: Record<string, string>;
      };
      expect(packedManifest.dependencies?.["@mindfoldhq/trellis-core"]).toBe(
        "npm:@devsc/trellis-core@0.6.0-guru.1",
      );
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  it("installs a complete Guru overlay through the dist CLI", () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "guru-dist-e2e-"));
    try {
      fs.writeFileSync(
        path.join(tmpDir, "package.json"),
        '{"scripts":{"test":"echo ok"}}\n',
        "utf8",
      );

      execFileSync(
        process.execPath,
        [
          DIST_CLI,
          "init",
          "--codex",
          "--claude",
          "--template",
          "guru-h5-web",
          "--workflow",
          "guru-h5",
          "--yes",
          "--user",
          "smoke",
        ],
        { cwd: tmpDir, encoding: "utf8" },
      );
      execFileSync(process.execPath, [DIST_CLI, "guru", "apply", "h5"], {
        cwd: tmpDir,
        encoding: "utf8",
      });

      expect(
        fs.existsSync(path.join(tmpDir, ".trellis/scripts/guru/guru_gate.py")),
      ).toBe(true);
      expect(
        fs.existsSync(
          path.join(tmpDir, ".trellis/scripts/guru/guru_supervise.py"),
        ),
      ).toBe(true);
      expect(
        fs.existsSync(
          path.join(
            tmpDir,
            ".agents/skills/h5-design-overview-review/SKILL.md",
          ),
        ),
      ).toBe(true);
      expect(
        fs.existsSync(
          path.join(tmpDir, ".agents/skills/design-grill/SKILL.md"),
        ),
      ).toBe(true);
      expect(
        fs.readFileSync(path.join(tmpDir, ".trellis/config.yaml"), "utf8"),
      ).toContain("guru_gate.py check");
      expect(
        fs.readFileSync(path.join(tmpDir, ".trellis/worktree.yaml"), "utf8"),
      ).toContain("guru_gate.py auto");
      const gitignore = fs.readFileSync(path.join(tmpDir, ".gitignore"), "utf8");
      expect(gitignore).toContain(".claude/projects/");
      expect(gitignore).toContain(".codex/sessions/");
      expect(gitignore).toContain(".trellis/channels/");
      execFileSync(
        "python3",
        [
          path.join(tmpDir, ".trellis/scripts/guru/guru_supervise.py"),
          "--help",
        ],
        { cwd: tmpDir, encoding: "utf8" },
      );

      execFileSync(
        process.execPath,
        [
          DIST_CLI,
          "guru",
          "apply",
          "h5",
          tmpDir,
          "--adversarial-enabled",
          "false",
        ],
        {
          cwd: tmpDir,
          encoding: "utf8",
        },
      );
      expect(
        fs.readFileSync(path.join(tmpDir, ".trellis/config.yaml"), "utf8"),
      ).toContain("adversarial_enabled: false");
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  }, 30_000);

  it("passes --with-gitnexus from the dist CLI into the overlay installer", () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "guru-gitnexus-e2e-"));
    try {
      fs.mkdirSync(path.join(tmpDir, ".trellis/scripts/common"), {
        recursive: true,
      });
      fs.mkdirSync(path.join(tmpDir, ".trellis/spec/conventions"), {
        recursive: true,
      });
      fs.mkdirSync(path.join(tmpDir, ".claude"), { recursive: true });
      fs.writeFileSync(
        path.join(tmpDir, ".trellis/scripts/common/task_utils.py"),
        "def run_blocking_task_hooks():\n    pass\n",
        "utf8",
      );
      fs.writeFileSync(
        path.join(tmpDir, ".trellis/spec/conventions/project-conventions.md"),
        "# Project conventions\n",
        "utf8",
      );
      fs.writeFileSync(
        path.join(tmpDir, ".claude/settings.json"),
        "{}\n",
        "utf8",
      );
      fs.writeFileSync(
        path.join(tmpDir, "package.json"),
        '{"scripts":{"test":"echo ok"}}\n',
        "utf8",
      );
      fs.writeFileSync(
        path.join(tmpDir, "AGENTS.md"),
        `# User instructions

<!-- TRELLIS:START -->
# Trellis Instructions
<!-- TRELLIS:END -->
`,
        "utf8",
      );

      const fakeBin = path.join(tmpDir, "fake-bin");
      const logPath = path.join(tmpDir, "gitnexus.log");
      fs.mkdirSync(fakeBin);
      const fakeNpx = path.join(fakeBin, "npx");
      fs.writeFileSync(
        fakeNpx,
        `#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$FAKE_GITNEXUS_LOG"
if [ "$1" = "gitnexus" ] && [ "$2" = "analyze" ]; then
  mkdir -p .gitnexus
  cat > .gitnexus/meta.json <<JSON
{"repoPath":"$PWD","indexedAt":"2026-06-19T00:00:00.000Z","stats":{"files":3,"nodes":5,"edges":8,"processes":2}}
JSON
elif [ "$1" = "gitnexus" ] && [ "$2" = "status" ]; then
  echo "Repository indexed."
else
  exit 9
fi
`,
        "utf8",
      );
      fs.chmodSync(fakeNpx, 0o755);

      execFileSync(process.execPath, [DIST_CLI, "guru", "apply", "h5", tmpDir], {
        cwd: tmpDir,
        encoding: "utf8",
        env: {
          ...process.env,
          FAKE_GITNEXUS_LOG: logPath,
          GURU_WITH_GITNEXUS: "1",
          PATH: `${fakeBin}${path.delimiter}${process.env.PATH ?? ""}`,
        },
      });

      expect(fs.existsSync(logPath)).toBe(false);
      expect(fs.readFileSync(path.join(tmpDir, "AGENTS.md"), "utf8")).not.toContain(
        "<!-- gitnexus:start -->",
      );

      execFileSync(
        process.execPath,
        [DIST_CLI, "guru", "apply", "h5", tmpDir, "--with-gitnexus"],
        {
          cwd: tmpDir,
          encoding: "utf8",
          env: {
            ...process.env,
            FAKE_GITNEXUS_LOG: logPath,
            PATH: `${fakeBin}${path.delimiter}${process.env.PATH ?? ""}`,
          },
        },
      );

      expect(fs.readFileSync(logPath, "utf8")).toContain("gitnexus analyze");
      const agents = fs.readFileSync(path.join(tmpDir, "AGENTS.md"), "utf8");
      expect(agents).toContain("GitNexus - Code Intelligence");
      expect(agents).toContain("5 symbols");
      expect(agents).toContain("npx gitnexus setup");
      expect(agents.match(/<!-- gitnexus:start -->/g)).toHaveLength(1);
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  }, 30_000);

  it("ships workflow names that packaged apply.sh can resolve", () => {
    const applyScript = readOverlayFile("apply.sh");
    expect(applyScript).toContain('"$ROOT/workflows/${WF_NAME}.md"');

    for (const id of [
      GURU_CLIENT_WORKFLOW_ID,
      GURU_GO_WORKFLOW_ID,
      GURU_IOS_WORKFLOW_ID,
      GURU_H5_WORKFLOW_ID,
    ]) {
      expect(
        fs.existsSync(path.join(GURU_TEMPLATE_ROOT, "workflows", `${id}.md`)),
      ).toBe(true);
    }
  });

  it("ships the overlay skill and gate files needed by Guru installs", () => {
    const designGrill = readOverlayFile(
      "agents-skills",
      "design-grill",
      "SKILL.md",
    );
    expect(designGrill).toContain("Design Grill Packet");
    expect(designGrill).toContain("compatibility-only");
    expect(designGrill).toContain(
      "新流程的 Domain Grill 归属于 `trellis-brainstorm`",
    );
    expect(designGrill).toContain(
      "`guru_gate.py check` / `auto` 不依赖本 skill",
    );
    expect(designGrill).toContain("grill-done");
    expect(designGrill).toContain("grill-skip");
    expect(designGrill).not.toContain(
      "overview` / `detail` 在 full 或 high-risk 时必跑",
    );
    expect(designGrill).not.toContain("Policy: required | skippable");
    expect(designGrill).not.toContain(
      "Next Command: python3 .trellis/scripts/guru/guru_gate.py grill-done",
    );
    expect(fs.existsSync(overlayPath("apply.sh"))).toBe(true);
    expect(fs.existsSync(overlayPath("verify", "guru_gate.py"))).toBe(true);
    expect(fs.existsSync(overlayPath("verify", "guru_config_patch.py"))).toBe(
      true,
    );
    expect(fs.existsSync(overlayPath("verify", "guru_supervise.py"))).toBe(
      true,
    );
    expect(
      fs.existsSync(overlayPath("hooks", "platform", "grill-nudge.sh")),
    ).toBe(true);

    const trellisLocal = readOverlayFile("trellis-local", "SKILL.md");
    expect(trellisLocal).toContain("Domain Grill 已前移到需求发现");
    expect(trellisLocal).toContain("不再作为概要/详细 Gate");
    expect(trellisLocal).not.toContain("Gate 前拷问拍");
  });

  it("ships requirements adversarial review before requirements confirmation", () => {
    const workflowFiles = [
      "guru-client.md",
      "guru-go.md",
      "guru-h5.md",
      "guru-ios.md",
    ];
    for (const file of workflowFiles) {
      const workflow = fs.readFileSync(
        path.join(GURU_TEMPLATE_ROOT, "workflows", file),
        "utf8",
      );
      const reviewIndex = workflow.indexOf(
        "guru_supervise.py --adversarial requirements <task_dir>",
      );
      const confirmIndex = workflow.indexOf(
        "guru_gate.py confirm requirements <task_dir>",
        reviewIndex,
      );
      expect(reviewIndex).toBeGreaterThanOrEqual(0);
      expect(confirmIndex).toBeGreaterThan(reviewIndex);
      expect(workflow).toContain(
        "requirements review 不使用 review-evidence Gate",
      );
      expect(workflow).toContain("review_result=clean/requirements-ready");
      expect(workflow).toContain("route_class=REQ_BLOCKER");
    }

    const gateFiles = [
      "guru-flutter-client",
      "guru-go-backend",
      "guru-h5-web",
      "guru-ios-native",
    ];
    for (const spec of gateFiles) {
      const gateModel = fs.readFileSync(
        path.join(
          GURU_TEMPLATE_ROOT,
          "specs",
          spec,
          "harness",
          "gate",
          "gate-confirmation-model.md",
        ),
        "utf8",
      );
      const reviewIndex = gateModel.indexOf(
        "guru_supervise.py --adversarial requirements <task_dir>",
      );
      const confirmIndex = gateModel.indexOf(
        "guru_gate.py confirm requirements",
        reviewIndex,
      );
      expect(reviewIndex).toBeGreaterThanOrEqual(0);
      expect(confirmIndex).toBeGreaterThan(reviewIndex);
      expect(gateModel).toContain("review_result=clean/requirements-ready");
      expect(gateModel).toContain("route_class=REQ_BLOCKER");
      expect(gateModel).toContain("不写 `review_runs`");
    }
  });

  it("keeps overview writing guides on the Domain Grill route", () => {
    for (const skill of [
      "client-design-overview-writing",
      "h5-design-overview-writing",
      "ios-design-overview-writing",
    ]) {
      const guide = readOverlayFile(
        "agents-skills",
        skill,
        "references",
        "chapter-guide.md",
      );
      expect(guide).toContain("Domain Grill");
      expect(guide).toContain("REQ_BLOCKER");
      expect(guide).not.toContain("争议行先加载 `design-grill`");
      expect(guide).not.toContain("争议行先加载 `h5-design-overview`");
      expect(guide).not.toContain("或与用户确认");
    }
  });

  it("keeps packaged Guru helper scripts in sync with the source overlay", () => {
    expect(readOverlayFile("apply.sh")).toBe(
      fs.readFileSync(path.join(GURU_SOURCE_OVERLAY_ROOT, "apply.sh"), "utf8"),
    );
    for (const helper of [
      "guru_config_patch.py",
      "guru_gate.py",
      "guru_supervise.py",
    ]) {
      const source = fs.readFileSync(
        path.join(GURU_SOURCE_OVERLAY_ROOT, "verify", helper),
        "utf8",
      );
      const packaged = readOverlayFile("verify", helper);
      expect(packaged).toBe(source);
    }
    expect(readOverlayFile("verify", "tests", "run_tests.sh")).toBe(
      fs.readFileSync(
        path.join(GURU_SOURCE_OVERLAY_ROOT, "verify", "tests", "run_tests.sh"),
        "utf8",
      ),
    );
  });

  it("keeps the packaged task creation script in sync with the local Trellis script", () => {
    const packaged = fs.readFileSync(
      path.join(TRELLIS_TEMPLATE_SCRIPTS_ROOT, "common", "task_store.py"),
      "utf8",
    );
    const source = fs.readFileSync(TRELLIS_SOURCE_TASK_STORE, "utf8");
    expect(packaged).toBe(source);
  });

  it("creates packaged Trellis PRDs with brainstorm evidence and brainstorm-first guidance", () => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "trellis-task-create-"));
    const python = process.env.PYTHON ?? "python3";
    try {
      fs.mkdirSync(path.join(tmpDir, ".trellis"), { recursive: true });
      fs.cpSync(TRELLIS_TEMPLATE_SCRIPTS_ROOT, path.join(tmpDir, ".trellis", "scripts"), {
        recursive: true,
      });
      fs.mkdirSync(path.join(tmpDir, ".trellis", "tasks"), { recursive: true });
      execFileSync("git", ["init"], { cwd: tmpDir, encoding: "utf8" });
      execFileSync("git", ["config", "user.email", "trellis@example.invalid"], {
        cwd: tmpDir,
        encoding: "utf8",
      });
      execFileSync("git", ["config", "user.name", "Trellis Test"], {
        cwd: tmpDir,
        encoding: "utf8",
      });
      execFileSync("git", ["commit", "--allow-empty", "-m", "init"], {
        cwd: tmpDir,
        encoding: "utf8",
      });
      execFileSync(python, [".trellis/scripts/init_developer.py", "reviewer"], {
        cwd: tmpDir,
        encoding: "utf8",
        env: PYTHON_NO_BYTECODE_ENV,
      });

      const result = spawnSync(
        python,
        [
          ".trellis/scripts/task.py",
          "create",
          "Brainstorm smoke",
          "--slug",
          "brainstorm-smoke",
        ],
        {
          cwd: tmpDir,
          encoding: "utf8",
          env: PYTHON_NO_BYTECODE_ENV,
        },
      );
      expect(result.status, result.stderr).toBe(0);
      expect(result.stderr).toContain("Load trellis-brainstorm");
      const taskPath = result.stdout.trim();
      const prd = fs.readFileSync(path.join(tmpDir, taskPath, "prd.md"), "utf8");
      expect(prd).toContain("## Brainstorm Evidence");
      expect(prd).toContain("Domain/terminology triggers: pending");
    } catch (error) {
      if (error && typeof error === "object" && "stderr" in error) {
        const stderr = Buffer.isBuffer(error.stderr)
          ? error.stderr.toString("utf8")
          : String(error.stderr);
        throw new Error(stderr);
      }
      throw error;
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  it("ships requirements adversarial review state visibility", () => {
    const gate = readOverlayFile("verify", "guru_gate.py");
    const supervise = readOverlayFile("verify", "guru_supervise.py");

    expect(gate).toContain('REQUIREMENTS_REVIEW_KEY = "requirements_review"');
    expect(gate).toContain("需求对抗 Review");
    expect(gate).toContain("缺少 clean/current 的对抗审查证据");
    expect(gate).toContain(
      "python3 .trellis/scripts/guru/guru_supervise.py --adversarial requirements",
    );

    expect(supervise).toContain(
      'REQUIREMENTS_REVIEW_KEY = "requirements_review"',
    );
    expect(supervise).toContain(
      'REQUIREMENTS_CLEAN_MARKER = "review_result=clean/requirements-ready"',
    );
    expect(supervise).toContain("missing requirements review verdict");
  });

  it("does not bundle transient cache artifacts from the overlay source", () => {
    const relativeFiles = listFilesRecursive(GURU_OVERLAY_ROOT).map((file) =>
      path.relative(GURU_OVERLAY_ROOT, file),
    );
    expect(relativeFiles.length).toBeGreaterThan(0);
    expect(
      relativeFiles.filter(
        (file) =>
          file.includes("__pycache__") ||
          file.endsWith(".pyc") ||
          file.endsWith(".pyo"),
      ),
    ).toEqual([]);
  });
});

describe("guru_config_patch.py", () => {
  let tmpDir: string;
  const python = process.env.PYTHON ?? "python3";
  const patcher = overlayPath("verify", "guru_config_patch.py");

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "guru-config-patch-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  function runPatch(platform: string, extraArgs: string[] = []): void {
    execFileSync(
      python,
      [
        patcher,
        "ensure-supervision-defaults",
        "--root",
        tmpDir,
        "--platform",
        platform,
        ...extraArgs,
      ],
      { encoding: "utf8", env: PYTHON_NO_BYTECODE_ENV },
    );
  }

  function configText(): string {
    return fs.readFileSync(
      path.join(tmpDir, ".trellis", "config.yaml"),
      "utf8",
    );
  }

  it("fills fresh Guru projects with channel supervision defaults", () => {
    runPatch("go");

    expect(configText()).toContain(`codex:
  dispatch_mode: channel`);
    expect(configText()).toContain(`channel:
  worker_guard:
    idle_timeout: 10m
    max_live_workers: 4`);
    expect(configText()).toContain(`guru:
  supervision:
    provider: codex
    implement_timeout: 45m
    check_timeout: 30m
    warn_before: 5m
    adversarial_enabled: true
    adversarial_claude_model: claude-sonnet-4-6
    adversarial_codex_model: gpt-5.4
    adversarial_codex_reasoning_effort: high
  platform: go`);
  });

  it("preserves existing config choices and fills only missing child keys", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `codex:
  dispatch_mode: inline
channel:
  worker_guard:
    idle_timeout: 3m
guru:
  platform: flutter
  supervision:
    provider: claude
    implement_timeout: 90m
    adversarial_claude_model: custom-claude
    adversarial_codex_reasoning_effort: max
`,
      "utf8",
    );

    runPatch("h5");
    const once = configText();
    runPatch("h5");

    expect(configText()).toBe(once);
    expect(once).toContain("dispatch_mode: inline");
    expect(once).toContain("idle_timeout: 3m");
    expect(once).toContain("max_live_workers: 4");
    expect(once).toContain("platform: flutter");
    expect(once).toContain("provider: claude");
    expect(once).toContain("implement_timeout: 90m");
    expect(once).toContain("check_timeout: 30m");
    expect(once).toContain("warn_before: 5m");
    expect(once).toContain("adversarial_enabled: true");
    expect(once).toContain("adversarial_claude_model: custom-claude");
    expect(once).toContain("adversarial_codex_model: gpt-5.4");
    expect(once).toContain("adversarial_codex_reasoning_effort: max");
  });

  it("preserves explicit adversarial disable switches", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `guru:
  supervision:
    adversarial_enabled: false
`,
      "utf8",
    );

    runPatch("go");
    const once = configText();
    runPatch("go");

    expect(configText()).toBe(once);
    expect(once).toContain("adversarial_enabled: false");
  });

  it("overrides adversarial switch when requested by install", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `guru:
  supervision:
    adversarial_enabled: true
`,
      "utf8",
    );

    runPatch("go", ["--adversarial-enabled", "false"]);

    expect(configText()).toContain("adversarial_enabled: false");
  });

  it("upgrades legacy adversarial Claude defaults without replacing custom models", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    for (const legacyModel of ["claude-sonnet-4.8", "claude-sonnet-4.6"]) {
      fs.rmSync(path.dirname(configPath), { recursive: true, force: true });
      fs.mkdirSync(path.dirname(configPath), { recursive: true });
      fs.writeFileSync(
        configPath,
        `guru:
  supervision:
    adversarial_claude_model: ${legacyModel}
    adversarial_codex_model: custom-codex
`,
        "utf8",
      );

      runPatch("go");
      const once = configText();
      runPatch("go");

      expect(configText()).toBe(once);
      expect(once).toContain("adversarial_claude_model: claude-sonnet-4-6");
      expect(once).toContain("adversarial_codex_model: custom-codex");
    }
  });

  it("treats blank adversarial model choices as missing defaults", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `guru:
  supervision:
    adversarial_claude_model:
    adversarial_codex_model: # decide later
    adversarial_codex_reasoning_effort: ""
`,
      "utf8",
    );

    runPatch("go");
    const patched = configText();

    expect(patched).toContain("adversarial_claude_model: claude-sonnet-4-6");
    expect(patched).toContain("adversarial_codex_model: gpt-5.4");
    expect(patched).toContain("adversarial_codex_reasoning_effort: high");
    expect(patched).not.toContain("decide later");
  });

  it("fails fast when an existing mapping path is scalar", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(configPath, "guru: disabled\n", "utf8");

    expect(() =>
      execFileSync(
        python,
        [
          patcher,
          "ensure-supervision-defaults",
          "--root",
          tmpDir,
          "--platform",
          "ios",
        ],
        { encoding: "utf8", env: PYTHON_NO_BYTECODE_ENV, stdio: "pipe" },
      ),
    ).toThrow(/guru is a scalar/);
  });
});

describe("guru_supervise.py", () => {
  let tmpDir: string;
  const python = process.env.PYTHON ?? "python3";
  const supervisor = overlayPath("verify", "guru_supervise.py");
  const gate = overlayPath("verify", "guru_gate.py");

  beforeEach(() => {
    tmpDir = fs.realpathSync(
      fs.mkdtempSync(path.join(os.tmpdir(), "guru-supervise-")),
    );
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  function writeConfig(platform: string): void {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `guru:
  platform: ${platform}
channel:
  worker_guard:
    idle_timeout: 10m
    max_live_workers: 4
`,
      "utf8",
    );
  }

  function writeSkill(relativePath: string): string {
    const fullPath = path.join(tmpDir, relativePath);
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    fs.writeFileSync(fullPath, "# Guru skill\n", "utf8");
    return fullPath;
  }

  function writeTask(name: string): string {
    const taskDir = path.join(tmpDir, ".trellis", "tasks", name);
    fs.mkdirSync(taskDir, { recursive: true });
    fs.writeFileSync(path.join(taskDir, "prd.md"), "# PRD\n", "utf8");
    fs.writeFileSync(path.join(taskDir, "design.md"), "# Design\n", "utf8");
    fs.writeFileSync(
      path.join(taskDir, "implement.md"),
      "# Implement\n",
      "utf8",
    );
    return taskDir;
  }

  function runSupervisor(args: string[]): string {
    return execFileSync(python, [supervisor, "--root", tmpDir, ...args], {
      encoding: "utf8",
      env: PYTHON_NO_BYTECODE_ENV,
    });
  }

  function writeFakeTrellis(taskDir: string): string {
    const fake = path.join(tmpDir, "fake-trellis.sh");
    fs.writeFileSync(
      fake,
      `#!/usr/bin/env bash
set -euo pipefail
if [ "$1" = "channel" ] && [ "$2" = "list" ]; then
  cat <<'JSON'
[{"name":"guru-task-delta-implement-r4","task":"${taskDir}","workersAlive":0,"workersTotal":1,"lastEventKind":"done"}]
JSON
elif [ "$1" = "channel" ] && [ "$2" = "messages" ]; then
  cat <<'JSON'
{"kind":"spawned","as":"implement-codex-r4","provider":"codex"}
{"kind":"done","by":"implement-codex-r4"}
JSON
else
  echo "unexpected fake trellis args: $*" >&2
  exit 2
fi
`,
      "utf8",
    );
    fs.chmodSync(fake, 0o755);
    return fake;
  }

  function writeLoopFakeTrellis(): { fake: string; log: string } {
    const fake = path.join(tmpDir, "fake-loop-trellis.sh");
    const log = path.join(tmpDir, "loop.log");
    const count = path.join(tmpDir, "check-count.txt");
    fs.writeFileSync(
      fake,
      `#!/usr/bin/env bash
set -euo pipefail
LOG="${log}"
COUNT="${count}"
if [ "$1" = "channel" ] && [ "$2" = "create" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "spawn" ]; then
  agent=""
  worker=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --agent) agent="$2"; shift 2 ;;
      --as) worker="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  printf '%s %s\\n' "$agent" "$worker" >> "$LOG"
elif [ "$1" = "channel" ] && [ "$2" = "send" ]; then
  cat >/dev/null
elif [ "$1" = "channel" ] && [ "$2" = "wait" ]; then
  worker="worker"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --from) worker="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  printf '{"kind":"done","by":"%s"}\\n' "$worker"
elif [ "$1" = "channel" ] && [ "$2" = "messages" ]; then
  worker=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --from) worker="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  if [[ "$worker" == check-* ]]; then
    n=0
    if [ -s "$COUNT" ]; then n="$(cat "$COUNT")"; fi
    n=$((n + 1))
    echo "$n" > "$COUNT"
    if [ "$n" = "1" ]; then
      echo '{"kind":"message","by":"check","text":"review_result=findings route_class=IMPLEMENT_DEFECT validation_summary=fix code"}'
    else
      echo '{"kind":"message","by":"check","text":"review_result=clean/final-verification-ready route_class=none validation_summary=ok"}'
    fi
  else
    echo '{"kind":"message","by":"implement","text":"done"}'
  fi
else
  echo "unexpected fake trellis args: $*" >&2
  exit 2
fi
`,
      "utf8",
    );
    fs.chmodSync(fake, 0o755);
    return { fake, log };
  }

  function writeFailingSpawnTrellis(): string {
    const fake = path.join(tmpDir, "fake-spawn-fail-trellis.sh");
    fs.writeFileSync(
      fake,
      `#!/usr/bin/env bash
set -euo pipefail
if [ "$1" = "channel" ] && [ "$2" = "create" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "spawn" ]; then
  echo "provider executable not found" >&2
  exit 127
else
  echo "unexpected fake trellis args: $*" >&2
  exit 2
fi
`,
      "utf8",
    );
    fs.chmodSync(fake, 0o755);
    return fake;
  }

  function writeForbiddenTrellis(): string {
    const fake = path.join(tmpDir, "fake-forbidden-trellis.sh");
    const log = path.join(tmpDir, "forbidden-trellis.log");
    fs.writeFileSync(
      fake,
      `#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "${log}"
exit 9
`,
      "utf8",
    );
    fs.chmodSync(fake, 0o755);
    return fake;
  }

  function writeTerminalErrorTrellis(): string {
    const fake = path.join(tmpDir, "fake-terminal-error-trellis.sh");
    fs.writeFileSync(
      fake,
      `#!/usr/bin/env bash
set -euo pipefail
if [ "$1" = "channel" ] && [ "$2" = "create" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "spawn" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "send" ]; then
  cat >/dev/null
elif [ "$1" = "channel" ] && [ "$2" = "wait" ]; then
  echo '{"kind":"error","by":"requirements-claude-r1"}'
elif [ "$1" = "channel" ] && [ "$2" = "messages" ]; then
  echo '{"kind":"message","by":"requirements-claude-r1","text":"model unavailable"}'
else
  echo "unexpected fake trellis args: $*" >&2
  exit 2
fi
`,
      "utf8",
    );
    fs.chmodSync(fake, 0o755);
    return fake;
  }

  function writeRequirementsVerdictTrellis(verdictText: string): string {
    const suffix = verdictText.includes("clean/requirements-ready")
      ? "clean"
      : "blocked";
    const fake = path.join(tmpDir, `fake-requirements-verdict-${suffix}.sh`);
    fs.writeFileSync(
      fake,
      `#!/usr/bin/env bash
set -euo pipefail
if [ "$1" = "channel" ] && [ "$2" = "create" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "spawn" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "send" ]; then
  cat >/dev/null
elif [ "$1" = "channel" ] && [ "$2" = "wait" ]; then
  echo '{"kind":"done","by":"requirements-claude-fixture"}'
elif [ "$1" = "channel" ] && [ "$2" = "messages" ]; then
  echo ${JSON.stringify(JSON.stringify({ kind: "message", by: "requirements-claude-fixture", text: verdictText }))}
else
  echo "unexpected fake trellis args: $*" >&2
  exit 2
fi
`,
      "utf8",
    );
    fs.chmodSync(fake, 0o755);
    return fake;
  }

  it("dry-runs implement with codex provider, run id names, jsonl, and Guru skill context", () => {
    writeConfig("flutter");
    const skill = writeSkill(
      ".agents/skills/flutter-implementation-guru-writing/SKILL.md",
    );
    const taskDir = writeTask("task-alpha");
    const manifest = path.join(taskDir, "implement.jsonl");
    fs.writeFileSync(manifest, "{}\n", "utf8");

    const output = runSupervisor([
      "implement",
      taskDir,
      "--run-id",
      "run-1",
      "--dry-run",
    ]);

    expect(output).toContain("CHANNEL=guru-task-alpha-implement-run-1");
    expect(output).toContain("WORKER=implement-codex-run-1");
    expect(output).toContain(
      "trellis channel spawn guru-task-alpha-implement-run-1 --agent implement --provider codex --as implement-codex-run-1",
    );
    expect(output).toContain(`--file ${skill}`);
    expect(output).toContain(`--jsonl ${manifest}`);
    expect(output).toContain("--kind done,error,killed");
  });

  it("omits missing check.jsonl while still injecting the platform review skill", () => {
    writeConfig("h5");
    const skill = writeSkill(
      ".agents/skills/h5-implementation-guru-review/SKILL.md",
    );
    const taskDir = writeTask("task-beta");

    const output = runSupervisor([
      "check",
      taskDir,
      "--run-id",
      "r2",
      "--dry-run",
    ]);

    expect(output).toContain("CHANNEL=guru-task-beta-check-r2");
    expect(output).toContain("WORKER=check-codex-r2");
    expect(output).toContain(`--file ${skill}`);
    expect(output).not.toContain("--jsonl");
    expect(output).toContain("--kind done,error,killed");
  });

  it("dry-runs overview with writing/review skills and review evidence routing", () => {
    writeConfig("go");
    const writingSkill = writeSkill(
      ".agents/skills/go-design-overview-writing/SKILL.md",
    );
    const reviewSkill = writeSkill(
      ".agents/skills/go-design-overview-review/SKILL.md",
    );
    const taskDir = writeTask("task-overview");

    const output = runSupervisor([
      "overview",
      taskDir,
      "--run-id",
      "r5",
      "--dry-run",
    ]);

    expect(output).toContain("CHANNEL=guru-task-overview-overview-r5");
    expect(output).toContain("WORKER=overview-codex-r5");
    expect(output).toContain(`--file ${writingSkill}`);
    expect(output).toContain(`--file ${reviewSkill}`);
    expect(output).toContain("record-review overview");
    expect(output).toContain("two clean review passes");
    expect(output).toContain(
      "REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|IMPLEMENT_DEFECT|PROCESS_DEFECT",
    );
  });

  it("dry-runs detail with writing/review skills and review evidence routing", () => {
    writeConfig("ios");
    const writingSkill = writeSkill(
      ".agents/skills/ios-design-detail-writing/SKILL.md",
    );
    const reviewSkill = writeSkill(
      ".agents/skills/ios-design-detail-review/SKILL.md",
    );
    const taskDir = writeTask("task-detail");

    const output = runSupervisor([
      "detail",
      taskDir,
      "--run-id",
      "r6",
      "--dry-run",
    ]);

    expect(output).toContain("CHANNEL=guru-task-detail-detail-r6");
    expect(output).toContain("WORKER=detail-codex-r6");
    expect(output).toContain(`--file ${writingSkill}`);
    expect(output).toContain(`--file ${reviewSkill}`);
    expect(output).toContain("record-review detail");
    expect(output).toContain("two clean review passes");
    expect(output).toContain(
      "REQ_BLOCKER|OVERVIEW_DEFECT|DETAIL_DEFECT|IMPLEMENT_DEFECT|PROCESS_DEFECT",
    );
  });

  it("dry-runs requirements adversarial review with evidence-first blocker routing", () => {
    writeConfig("go");
    const requirementSkill = writeSkill(
      ".agents/skills/requirement-review/SKILL.md",
    );
    const taskDir = writeTask("task-requirements");
    const formalDoc = path.join(
      tmpDir,
      "docs",
      "requirements",
      "feature",
      "requirement-main.md",
    );
    const formalTrace = path.join(
      tmpDir,
      "docs",
      "requirements",
      "feature",
      "trace.jsonl",
    );
    const formalModule = path.join(
      tmpDir,
      "docs",
      "requirements",
      "feature",
      "modules",
      "requirement-api.md",
    );
    fs.mkdirSync(path.dirname(formalDoc), { recursive: true });
    fs.mkdirSync(path.dirname(formalModule), { recursive: true });
    fs.writeFileSync(formalDoc, "# Requirement Main\n", "utf8");
    fs.writeFileSync(formalTrace, "{}\n", "utf8");
    fs.writeFileSync(formalModule, "# Requirement API\n", "utf8");
    const taskJson = path.join(taskDir, "task.json");
    fs.writeFileSync(
      taskJson,
      JSON.stringify(
        {
          relatedFiles: ["docs/requirements/feature"],
        },
        null,
        2,
      ),
      "utf8",
    );
    const implementManifest = path.join(taskDir, "implement.jsonl");
    const checkManifest = path.join(taskDir, "check.jsonl");
    fs.writeFileSync(implementManifest, "{}\n", "utf8");
    fs.writeFileSync(checkManifest, "{}\n", "utf8");

    const codexOutput = runSupervisor([
      "--provider",
      "codex",
      "--adversarial",
      "requirements",
      taskDir,
      "--run-id",
      "r11",
      "--dry-run",
    ]);

    expect(codexOutput).toContain(
      "trellis channel spawn guru-task-requirements-requirements-r11 --agent requirements --provider claude --as requirements-claude-r11",
    );
    expect(codexOutput).toContain("--model claude-sonnet-4-6");
    expect(codexOutput).not.toContain("--reasoning-effort high");
    expect(codexOutput).toContain(`--file ${requirementSkill}`);
    expect(codexOutput).toContain(`--file ${taskJson}`);
    expect(codexOutput).toContain(`--file ${formalDoc}`);
    expect(codexOutput).toContain(`--file ${formalTrace}`);
    expect(codexOutput).toContain(`--file ${formalModule}`);
    expect(codexOutput).toContain(`--jsonl ${implementManifest}`);
    expect(codexOutput).toContain(`--jsonl ${checkManifest}`);
    expect(codexOutput).toContain(
      "adversarial requirements reviewer from the opposite provider (codex -> claude)",
    );
    expect(codexOutput).toContain(
      "repository evidence before asking product questions",
    );
    expect(codexOutput).toContain(
      "code, tests, configs, docs, .trellis/spec/, CONTEXT.md, CONTEXT-MAP.md, and docs/adr/",
    );
    expect(codexOutput).toContain("current-code-vs-user-intent");
    expect(codexOutput).toContain("route_class=REQ_BLOCKER");
    expect(codexOutput).toContain("review_result=clean/requirements-ready");
    expect(codexOutput).toContain(
      "Low severity wording nits or observations are non-blocking",
    );
    expect(codexOutput).toContain(
      "Keep temporary requirement decisions in prd.md",
    );
    expect(codexOutput).toContain("confirmed via Domain Grill rules");
    expect(codexOutput).toContain("Stop before confirm requirements");
    expect(codexOutput).not.toContain("record-review requirements");

    const claudeOutput = runSupervisor([
      "--provider",
      "claude",
      "--adversarial",
      "requirements",
      taskDir,
      "--run-id",
      "r12",
      "--dry-run",
    ]);

    expect(claudeOutput).toContain(
      "trellis channel spawn guru-task-requirements-requirements-r12 --agent requirements --provider codex --as requirements-codex-r12",
    );
    expect(claudeOutput).toContain("--model gpt-5.4 --reasoning-effort high");
    expect(claudeOutput).toContain(
      "adversarial requirements reviewer from the opposite provider (claude -> codex)",
    );

    const unknownOutput = runSupervisor([
      "--provider",
      "gemini",
      "--adversarial",
      "requirements",
      taskDir,
      "--run-id",
      "r13",
      "--dry-run",
    ]);

    expect(unknownOutput).toContain(
      "trellis channel spawn guru-task-requirements-requirements-r13 --agent requirements --provider codex --as requirements-codex-r13",
    );
    expect(unknownOutput).toContain("--model gpt-5.4 --reasoning-effort high");
    expect(unknownOutput).toContain(
      "adversarial requirements reviewer from the opposite provider (gemini -> codex)",
    );
  });

  it("skips failed adversarial reviewers without hiding normal worker failures", () => {
    writeConfig("go");
    writeSkill(".agents/skills/requirement-review/SKILL.md");
    const taskDir = writeTask("task-adversarial-skip");
    const failingSpawn = writeFailingSpawnTrellis();
    const terminalError = writeTerminalErrorTrellis();

    expect(() =>
      runSupervisor([
        "--trellis-bin",
        failingSpawn,
        "--provider",
        "codex",
        "--adversarial",
        "requirements",
        taskDir,
        "--run-id",
        "skip1",
      ]),
    ).not.toThrow();
    expect(() =>
      runSupervisor([
        "--trellis-bin",
        terminalError,
        "--provider",
        "codex",
        "--adversarial",
        "requirements",
        taskDir,
        "--run-id",
        "skip2",
      ]),
    ).not.toThrow();
    expect(() =>
      runSupervisor([
        "--trellis-bin",
        failingSpawn,
        "--provider",
        "codex",
        "requirements",
        taskDir,
        "--run-id",
        "fail",
      ]),
    ).toThrow();

    const task = JSON.parse(
      fs.readFileSync(path.join(taskDir, "task.json"), "utf8"),
    ) as { guru_gates?: { adversarial_skips?: Record<string, string>[] } };
    const skips = task.guru_gates?.adversarial_skips ?? [];
    expect(skips).toHaveLength(2);
    expect(skips[0]).toMatchObject({
      action: "requirements",
      provider: "claude",
      current_provider: "codex",
    });
    expect(skips[0]?.reason).toContain("exited 127");
    expect(skips[1]?.reason).toContain("worker terminal status was error");

    const statusOutput = execFileSync(python, [gate, "status", taskDir], {
      encoding: "utf8",
      env: PYTHON_NO_BYTECODE_ENV,
    });
    expect(statusOutput).toContain("对抗审查跳过记录");
    expect(statusOutput).toContain("requirements/claude");
    expect(statusOutput).toContain("worker terminal status was error");
  });

  it("skips disabled adversarial reviews before creating trellis channels", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `guru:
  platform: go
  supervision:
    adversarial_enabled: false
`,
      "utf8",
    );
    writeSkill(".agents/skills/requirement-review/SKILL.md");
    const taskDir = writeTask("task-adversarial-disabled");
    const forbiddenTrellis = writeForbiddenTrellis();

    expect(() =>
      runSupervisor([
        "--trellis-bin",
        forbiddenTrellis,
        "--provider",
        "codex",
        "--adversarial",
        "requirements",
        taskDir,
        "--run-id",
        "disabled1",
      ]),
    ).not.toThrow();
    expect(fs.existsSync(path.join(tmpDir, "forbidden-trellis.log"))).toBe(
      false,
    );

    const task = JSON.parse(
      fs.readFileSync(path.join(taskDir, "task.json"), "utf8"),
    ) as {
      guru_gates?: {
        adversarial_skips?: Record<string, string>[];
        requirements_review?: Record<string, string | boolean>;
      };
    };
    expect(task.guru_gates?.adversarial_skips?.[0]).toMatchObject({
      action: "requirements",
      provider: "claude",
      current_provider: "codex",
      reason: "disabled by guru.supervision.adversarial_enabled=false",
    });
    expect(task.guru_gates?.requirements_review).toMatchObject({
      action: "requirements",
      provider: "claude",
      current_provider: "codex",
      adversarial: true,
      status: "deferred",
      reason: "disabled by guru.supervision.adversarial_enabled=false",
      run_id: "disabled1",
    });
  });

  it("persists requirements adversarial clean and blocked verdicts", () => {
    writeConfig("go");
    writeSkill(".agents/skills/requirement-review/SKILL.md");
    const cleanTask = writeTask("task-requirements-clean");
    const blockedTask = writeTask("task-requirements-blocked");
    const cleanTrellis = writeRequirementsVerdictTrellis(
      "review_result=clean/requirements-ready route_class=none",
    );
    const blockedTrellis = writeRequirementsVerdictTrellis(
      "route_class=REQ_BLOCKER missing acceptance boundary",
    );

    runSupervisor([
      "--trellis-bin",
      cleanTrellis,
      "--provider",
      "codex",
      "--adversarial",
      "requirements",
      cleanTask,
      "--run-id",
      "clean1",
    ]);
    runSupervisor([
      "--trellis-bin",
      blockedTrellis,
      "--provider",
      "codex",
      "--adversarial",
      "requirements",
      blockedTask,
      "--run-id",
      "blocked1",
    ]);

    const clean = JSON.parse(
      fs.readFileSync(path.join(cleanTask, "task.json"), "utf8"),
    ) as {
      guru_gates?: {
        requirements_review?: Record<string, string | boolean>;
      };
    };
    const blocked = JSON.parse(
      fs.readFileSync(path.join(blockedTask, "task.json"), "utf8"),
    ) as {
      guru_gates?: {
        requirements_review?: Record<string, string | boolean>;
      };
    };

    expect(clean.guru_gates?.requirements_review).toMatchObject({
      action: "requirements",
      provider: "claude",
      current_provider: "codex",
      adversarial: true,
      status: "clean",
      reason: "review_result=clean/requirements-ready",
      run_id: "clean1",
    });
    expect(clean.guru_gates?.requirements_review?.artifact_digest).toMatch(
      /^[a-f0-9]{64}$/,
    );
    expect(blocked.guru_gates?.requirements_review).toMatchObject({
      action: "requirements",
      provider: "claude",
      current_provider: "codex",
      adversarial: true,
      status: "blocked",
      reason: "route_class=REQ_BLOCKER",
      run_id: "blocked1",
    });
  });

  it("dry-runs adversarial reviews with project model overrides", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `guru:
  platform: go
  supervision:
    adversarial_claude_model: custom-claude
    adversarial_codex_model: custom-codex
    adversarial_codex_reasoning_effort: max
`,
      "utf8",
    );
    writeSkill(".agents/skills/requirement-review/SKILL.md");
    const taskDir = writeTask("task-models");

    const claudeReviewer = runSupervisor([
      "--provider",
      "codex",
      "--adversarial",
      "requirements",
      taskDir,
      "--run-id",
      "m1",
      "--dry-run",
    ]);
    const codexReviewer = runSupervisor([
      "--provider",
      "claude",
      "--adversarial",
      "requirements",
      taskDir,
      "--run-id",
      "m2",
      "--dry-run",
    ]);

    expect(claudeReviewer).toContain("--provider claude");
    expect(claudeReviewer).toContain("--model custom-claude");
    expect(claudeReviewer).not.toContain("--reasoning-effort");
    expect(codexReviewer).toContain("--provider codex");
    expect(codexReviewer).toContain(
      "--model custom-codex --reasoning-effort max",
    );
  });

  it("dry-runs blank adversarial model overrides with defaults", () => {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(
      configPath,
      `guru:
  platform: go
  supervision:
    adversarial_claude_model:
    adversarial_codex_model: ""
    adversarial_codex_reasoning_effort: # decide later
`,
      "utf8",
    );
    writeSkill(".agents/skills/requirement-review/SKILL.md");
    const taskDir = writeTask("task-blank-models");

    const claudeReviewer = runSupervisor([
      "--provider",
      "codex",
      "--adversarial",
      "requirements",
      taskDir,
      "--run-id",
      "b1",
      "--dry-run",
    ]);
    const codexReviewer = runSupervisor([
      "--provider",
      "claude",
      "--adversarial",
      "requirements",
      taskDir,
      "--run-id",
      "b2",
      "--dry-run",
    ]);

    expect(claudeReviewer).toContain("--provider claude");
    expect(claudeReviewer).toContain("--model claude-sonnet-4-6");
    expect(claudeReviewer).not.toContain("--reasoning-effort");
    expect(codexReviewer).toContain("--provider codex");
    expect(codexReviewer).toContain(
      "--model gpt-5.4 --reasoning-effort high",
    );
    expect(codexReviewer).not.toContain("decide later");
  });

  it("dry-runs adversarial planning reviews with the opposite provider and marked evidence", () => {
    writeConfig("go");
    writeSkill(".agents/skills/go-design-overview-writing/SKILL.md");
    writeSkill(".agents/skills/go-design-overview-review/SKILL.md");
    writeSkill(".agents/skills/go-design-detail-writing/SKILL.md");
    writeSkill(".agents/skills/go-design-detail-review/SKILL.md");
    const taskDir = writeTask("task-adversarial");

    const codexOutput = runSupervisor([
      "--provider",
      "codex",
      "--adversarial",
      "overview",
      taskDir,
      "--run-id",
      "r8",
      "--dry-run",
    ]);

    expect(codexOutput).toContain(
      "trellis channel spawn guru-task-adversarial-overview-r8 --agent overview --provider claude --as overview-claude-r8",
    );
    expect(codexOutput).toContain("--model claude-sonnet-4-6");
    expect(codexOutput).toContain(
      "adversarial clean-context reviewer from the opposite provider (codex -> claude)",
    );
    expect(codexOutput).toContain(
      "--reviewer clean-context-adversarial-claude --run-id r8-claude-rN",
    );

    const claudeOutput = runSupervisor([
      "--provider",
      "claude",
      "--adversarial",
      "overview",
      taskDir,
      "--run-id",
      "r10",
      "--dry-run",
    ]);

    expect(claudeOutput).toContain(
      "trellis channel spawn guru-task-adversarial-overview-r10 --agent overview --provider codex --as overview-codex-r10",
    );
    expect(claudeOutput).toContain("--model gpt-5.4 --reasoning-effort high");
    expect(claudeOutput).toContain(
      "adversarial clean-context reviewer from the opposite provider (claude -> codex)",
    );
    expect(claudeOutput).toContain(
      "--reviewer clean-context-adversarial-codex --run-id r10-codex-rN",
    );

    const unknownOutput = runSupervisor([
      "--provider",
      "gemini",
      "--adversarial",
      "detail",
      taskDir,
      "--run-id",
      "r9",
      "--dry-run",
    ]);

    expect(unknownOutput).toContain(
      "trellis channel spawn guru-task-adversarial-detail-r9 --agent detail --provider codex --as detail-codex-r9",
    );
    expect(unknownOutput).toContain("--model gpt-5.4 --reasoning-effort high");
    expect(unknownOutput).toContain(
      "adversarial clean-context reviewer from the opposite provider (gemini -> codex)",
    );
    expect(unknownOutput).toContain(
      "--reviewer clean-context-adversarial-codex --run-id r9-codex-rN",
    );
  });

  it("dry-runs implement-check with paired skills, jsonl, route classes, and hard-boundary stop", () => {
    writeConfig("h5");
    const writingSkill = writeSkill(
      ".agents/skills/h5-implementation-guru-writing/SKILL.md",
    );
    const reviewSkill = writeSkill(
      ".agents/skills/h5-implementation-guru-review/SKILL.md",
    );
    const taskDir = writeTask("task-implement-check");
    const implementManifest = path.join(taskDir, "implement.jsonl");
    const checkManifest = path.join(taskDir, "check.jsonl");
    fs.writeFileSync(implementManifest, "{}\n", "utf8");
    fs.writeFileSync(checkManifest, "{}\n", "utf8");

    const output = runSupervisor([
      "implement-check",
      taskDir,
      "--run-id",
      "r7",
      "--dry-run",
    ]);

    expect(output).toContain("IMPLEMENT-CHECK LOOP");
    expect(output).toContain(
      "CHANNEL=guru-task-implement-check-implement-r7-implement-1",
    );
    expect(output).toContain(
      "CHANNEL=guru-task-implement-check-check-r7-check-1",
    );
    expect(output).toContain("WORKER=implement-codex-r7-implement-1");
    expect(output).toContain("WORKER=check-codex-r7-check-1");
    expect(output).toContain("repeat: implement -> check -> route");
    expect(output).toContain(`--file ${writingSkill}`);
    expect(output).toContain(`--file ${reviewSkill}`);
    expect(output).toContain(`--jsonl ${implementManifest}`);
    expect(output).toContain(`--jsonl ${checkManifest}`);
    expect(output).toContain("IMPLEMENT_DEFECT");
    expect(output).toContain("DETAIL_DEFECT");
    expect(output).toContain("OVERVIEW_DEFECT");
    expect(output).toContain("REQ_BLOCKER");
    expect(output).toContain("PROCESS_DEFECT");
    expect(output).toContain("review_result=clean/final-verification-ready");
    expect(output).toContain("reviewed diff/artifact context");
    expect(output).toContain("validation_summary");
    expect(output).toContain("Do not create implementation guru_gates");
    expect(output).toContain("final validation plus hard boundary");
  });

  it("runs implement-check as implement/check loop and repeats repairable implementation findings", () => {
    writeConfig("h5");
    writeSkill(".agents/skills/h5-implementation-guru-writing/SKILL.md");
    writeSkill(".agents/skills/h5-implementation-guru-review/SKILL.md");
    const taskDir = writeTask("task-loop");
    const { fake, log } = writeLoopFakeTrellis();

    const output = runSupervisor([
      "--trellis-bin",
      fake,
      "implement-check",
      taskDir,
      "--run-id",
      "loop",
    ]);

    expect(output).toContain("route_class=IMPLEMENT_DEFECT");
    expect(output).toContain("review_result=clean/final-verification-ready");
    expect(fs.readFileSync(log, "utf8").trim().split("\n")).toEqual([
      "implement implement-codex-loop-implement-1",
      "check check-codex-loop-check-1",
      "implement implement-codex-loop-implement-2",
      "check check-codex-loop-check-2",
    ]);
  });

  it("dry-runs kill with exact channel and worker handles", () => {
    writeConfig("go");
    const taskDir = writeTask("task-gamma");

    const output = runSupervisor([
      "kill",
      taskDir,
      "--channel",
      "guru-task-gamma-implement-r3",
      "--worker",
      "implement-codex-r3",
      "--dry-run",
    ]);

    expect(output.trim()).toBe(
      "trellis channel kill guru-task-gamma-implement-r3 --as implement-codex-r3",
    );
  });

  it("status reports exact channel and worker handles with copy-paste kill command", () => {
    writeConfig("flutter");
    const taskDir = writeTask("task-delta");
    const fakeTrellis = writeFakeTrellis(taskDir);

    const output = runSupervisor([
      "--trellis-bin",
      fakeTrellis,
      "status",
      taskDir,
    ]);

    expect(output).toContain("channel: guru-task-delta-implement-r4");
    expect(output).toContain(
      "worker: implement-codex-r4 provider=codex terminal=done",
    );
    expect(output).toContain(
      "python3 .trellis/scripts/guru/guru_supervise.py kill",
    );
    expect(output).toContain(
      "--channel guru-task-delta-implement-r4 --worker implement-codex-r4",
    );
  });
});

// 档 3：requirements gate digest 纳入正式需求包（requirement_package）。
// 这些用例直接驱动 SOURCE overlay 脚本（guru-template/overlay/verify），验证本任务实际改动；
// bundled 同步由主会话负责，独立的 in-sync 断言（line 676）单独守门。
describe("guru requirements digest versioned package (source overlay)", () => {
  let tmpDir: string;
  const python = process.env.PYTHON ?? "python3";
  const sourceSupervise = path.join(
    GURU_SOURCE_OVERLAY_ROOT,
    "verify",
    "guru_supervise.py",
  );
  const sourceGate = path.join(
    GURU_SOURCE_OVERLAY_ROOT,
    "verify",
    "guru_gate.py",
  );

  beforeEach(() => {
    tmpDir = fs.realpathSync(
      fs.mkdtempSync(path.join(os.tmpdir(), "guru-req-digest-")),
    );
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  function writeConfig(): void {
    const configPath = path.join(tmpDir, ".trellis", "config.yaml");
    fs.mkdirSync(path.dirname(configPath), { recursive: true });
    fs.writeFileSync(configPath, "guru:\n  platform: go\n", "utf8");
  }

  function writeTask(name: string): string {
    const taskDir = path.join(tmpDir, ".trellis", "tasks", name);
    fs.mkdirSync(taskDir, { recursive: true });
    fs.writeFileSync(path.join(taskDir, "prd.md"), "# PRD\n### BHV-001 x\n", "utf8");
    return taskDir;
  }

  function writeRequirementPackage(taskDir: string, relPkg: string): string {
    const pkg = path.join(tmpDir, relPkg);
    fs.mkdirSync(path.join(pkg, "modules"), { recursive: true });
    fs.mkdirSync(path.join(pkg, "snapshots"), { recursive: true });
    fs.mkdirSync(path.join(pkg, "changes"), { recursive: true });
    fs.writeFileSync(path.join(pkg, "README.md"), "# req nav\n", "utf8");
    fs.writeFileSync(
      path.join(pkg, "requirement-main.md"),
      "# requirement main v1\n",
      "utf8",
    );
    fs.writeFileSync(
      path.join(pkg, "modules", "requirement-page.md"),
      "# page module\n",
      "utf8",
    );
    fs.writeFileSync(path.join(pkg, "snapshots", "rc.md"), "# snapshot\n", "utf8");
    fs.writeFileSync(
      path.join(pkg, "changes", "change-log.md"),
      "# changelog\n",
      "utf8",
    );
    fs.writeFileSync(
      path.join(taskDir, "task.json"),
      JSON.stringify({ requirement_package: relPkg }, null, 2),
      "utf8",
    );
    return pkg;
  }

  function writeCleanRequirementsTrellis(): string {
    const fake = path.join(tmpDir, "fake-req-clean.sh");
    const verdict = JSON.stringify(
      JSON.stringify({
        kind: "message",
        by: "requirements-claude-fixture",
        text: "review_result=clean/requirements-ready route_class=none",
      }),
    );
    fs.writeFileSync(
      fake,
      `#!/usr/bin/env bash
set -euo pipefail
if [ "$1" = "channel" ] && [ "$2" = "create" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "spawn" ]; then
  exit 0
elif [ "$1" = "channel" ] && [ "$2" = "send" ]; then
  cat >/dev/null
elif [ "$1" = "channel" ] && [ "$2" = "wait" ]; then
  echo '{"kind":"done","by":"requirements-claude-fixture"}'
elif [ "$1" = "channel" ] && [ "$2" = "messages" ]; then
  echo ${verdict}
else
  echo "unexpected fake trellis args: $*" >&2
  exit 2
fi
`,
      "utf8",
    );
    fs.chmodSync(fake, 0o755);
    return fake;
  }

  function gateDigest(taskDir: string): string {
    return execFileSync(
      python,
      [sourceGate, "digest", "requirements", taskDir],
      { cwd: tmpDir, encoding: "utf8", env: PYTHON_NO_BYTECODE_ENV },
    ).trim();
  }

  function recordedReviewDigest(taskDir: string): string {
    const task = JSON.parse(
      fs.readFileSync(path.join(taskDir, "task.json"), "utf8"),
    ) as {
      guru_gates?: { requirements_review?: { artifact_digest?: string } };
    };
    return task.guru_gates?.requirements_review?.artifact_digest ?? "";
  }

  it("records a supervise digest that matches the gate current digest, and invalidates on canonical change", () => {
    writeConfig();
    fs.mkdirSync(
      path.join(tmpDir, ".agents", "skills", "requirement-review"),
      { recursive: true },
    );
    fs.writeFileSync(
      path.join(tmpDir, ".agents", "skills", "requirement-review", "SKILL.md"),
      "# skill\n",
      "utf8",
    );
    const taskDir = writeTask("task-req-digest");
    const pkg = writeRequirementPackage(
      taskDir,
      "docs/requirements/versions/v1.0.0",
    );
    const fake = writeCleanRequirementsTrellis();

    execFileSync(
      python,
      [
        sourceSupervise,
        "--root",
        tmpDir,
        "--trellis-bin",
        fake,
        "--provider",
        "codex",
        "--adversarial",
        "requirements",
        taskDir,
        "--run-id",
        "rqd1",
      ],
      { cwd: tmpDir, encoding: "utf8", env: PYTHON_NO_BYTECODE_ENV },
    );

    // supervise 写入的 review digest 与 gate 当前 digest 必须字节一致（共享 helper，不假 stale）
    const recorded = recordedReviewDigest(taskDir);
    expect(recorded).toMatch(/^[a-f0-9]{64}$/);
    expect(recorded).toBe(gateDigest(taskDir));

    // 改 canonical 正文 → gate digest 变 → 与 supervise 记录的旧 digest 不再一致（review 须重跑）
    fs.appendFileSync(
      path.join(pkg, "requirement-main.md"),
      "\nnew acceptance rule\n",
      "utf8",
    );
    const afterBody = gateDigest(taskDir);
    expect(afterBody).not.toBe(recorded);

    // 改 excludes 子树（snapshots/changes）→ gate digest 不变（仍等于 canonical 改动后的值）
    fs.appendFileSync(
      path.join(pkg, "snapshots", "rc.md"),
      "\nmore snapshot\n",
      "utf8",
    );
    fs.appendFileSync(
      path.join(pkg, "changes", "change-log.md"),
      "\nmore changes\n",
      "utf8",
    );
    expect(gateDigest(taskDir)).toBe(afterBody);
  });

  it("keeps no-pointer requirements digest on the legacy basename formula (backward compatible)", () => {
    writeConfig();
    const taskDir = writeTask("task-no-pointer");
    fs.writeFileSync(
      path.join(taskDir, "task.json"),
      JSON.stringify({}, null, 2),
      "utf8",
    );

    const prd = fs.readFileSync(path.join(taskDir, "prd.md"), "utf8");
    const legacy = createHash("sha256")
      .update("prd.md")
      .update(Buffer.from([0]))
      .update(prd)
      .update(Buffer.from([0]))
      .digest("hex");
    expect(gateDigest(taskDir)).toBe(legacy);
  });

  it("fails closed when the requirement package manifest is illegal", () => {
    writeConfig();
    const taskDir = writeTask("task-bad-manifest");
    const pkg = writeRequirementPackage(taskDir, "docs/requirements/v1");
    fs.writeFileSync(
      path.join(pkg, "manifest.yaml"),
      "canonical_excludes: notalist\n",
      "utf8",
    );

    const result = spawnSync(
      python,
      [sourceGate, "requirements", taskDir],
      { cwd: tmpDir, encoding: "utf8", env: PYTHON_NO_BYTECODE_ENV },
    );
    expect(result.status).toBe(2);
    expect(result.stderr).toContain("manifest 非法");
  });

  // [blocker 回归] codex：supervise --root <repo> 在 cwd≠root 下运行时，旧实现用 os.getcwd() 当
  // repo root 把 docs/... 解析成 <cwd>/docs/...（空包/错包），与 gate 从 repo root 算的 digest 分叉、
  // review 立刻 stale。此用例显式让 supervise 的 cwd ≠ --root，断言写入 digest 仍 == gate current digest。
  it("matches the gate digest when supervise runs with cwd different from --root (blocker regression)", () => {
    writeConfig();
    fs.mkdirSync(
      path.join(tmpDir, ".agents", "skills", "requirement-review"),
      { recursive: true },
    );
    fs.writeFileSync(
      path.join(tmpDir, ".agents", "skills", "requirement-review", "SKILL.md"),
      "# skill\n",
      "utf8",
    );
    const taskDir = writeTask("task-cwd-not-root");
    const pkg = writeRequirementPackage(
      taskDir,
      "docs/requirements/versions/v1.0.0",
    );
    const fake = writeCleanRequirementsTrellis();

    // 独立 cwd（绝对不等于 --root=tmpDir），模拟 `cd /somewhere-else && guru_supervise --root <repo>`
    const elsewhere = fs.realpathSync(
      fs.mkdtempSync(path.join(os.tmpdir(), "guru-elsewhere-")),
    );
    expect(path.resolve(elsewhere)).not.toBe(path.resolve(tmpDir));
    try {
      execFileSync(
        python,
        [
          sourceSupervise,
          "--root",
          tmpDir,
          "--trellis-bin",
          fake,
          "--provider",
          "codex",
          "--adversarial",
          "requirements",
          taskDir,
          "--run-id",
          "rqd-cwd",
        ],
        { cwd: elsewhere, encoding: "utf8", env: PYTHON_NO_BYTECODE_ENV },
      );

      const recorded = recordedReviewDigest(taskDir);
      expect(recorded).toMatch(/^[a-f0-9]{64}$/);
      // gate 从 repo root 算（cwd: tmpDir）；两者必须字节一致，否则 review 永久 stale
      expect(recorded).toBe(gateDigest(taskDir));
      // 且该 digest 真的纳入了正式需求包，不是退化成 prd.md-only（空包）
      const prd = fs.readFileSync(path.join(taskDir, "prd.md"), "utf8");
      const prdOnly = createHash("sha256")
        .update("prd.md")
        .update(Buffer.from([0]))
        .update(prd)
        .update(Buffer.from([0]))
        .digest("hex");
      expect(recorded).not.toBe(prdOnly);
      // 改 canonical 正文 → gate digest 变 → 与旧记录不再一致
      fs.appendFileSync(
        path.join(pkg, "requirement-main.md"),
        "\nnew rule\n",
        "utf8",
      );
      expect(gateDigest(taskDir)).not.toBe(recorded);
    } finally {
      fs.rmSync(elsewhere, { recursive: true, force: true });
    }
  });

  // [major 回归] codex：requirement_package 存在但目录不存在 → 必须 fail-closed 阻断（不空枚举伪装成 prd.md-only）。
  it("fails closed when the requirement package directory is missing", () => {
    writeConfig();
    const taskDir = writeTask("task-missing-pkg");
    fs.writeFileSync(
      path.join(taskDir, "task.json"),
      JSON.stringify(
        { requirement_package: "docs/requirements/versions/none" },
        null,
        2,
      ),
      "utf8",
    );
    const result = spawnSync(python, [sourceGate, "requirements", taskDir], {
      cwd: tmpDir,
      encoding: "utf8",
      env: PYTHON_NO_BYTECODE_ENV,
    });
    expect(result.status).toBe(2);
    expect(result.stderr).toContain("版本目录不存在");
  });

  // [major 回归] codex：canonical_root 穿越包外（../../..）→ 必须 fail-closed 阻断（不把包外目录纳入 digest）。
  it("fails closed when manifest canonical_root escapes the package directory", () => {
    writeConfig();
    const taskDir = writeTask("task-root-escape");
    const pkg = writeRequirementPackage(
      taskDir,
      "docs/requirements/versions/v1.0.0",
    );
    fs.writeFileSync(
      path.join(pkg, "manifest.yaml"),
      "canonical_root: ../../..\n",
      "utf8",
    );
    const result = spawnSync(python, [sourceGate, "requirements", taskDir], {
      cwd: tmpDir,
      encoding: "utf8",
      env: PYTHON_NO_BYTECODE_ENV,
    });
    expect(result.status).toBe(2);
    expect(result.stderr).toContain("canonical_root");
  });
});

describe("bundled guru-flutter-client spec", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "guru-bundled-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("is registered as a bundled spec", () => {
    expect(listBundledSpecTemplateIds()).toContain("guru-flutter-client");
    const files = getBundledSpecFiles("guru-flutter-client");
    if (files === null) throw new Error("expected bundled spec files");
    expect([...files.keys()]).toContain("harness/index.md");
    expect([...files.keys()]).toContain("guides/golden-path.md");
  });

  it("installs offline via downloadTemplateById when no registry is given", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network must not be touched for bundled specs");
      }),
    );
    try {
      const result = await downloadTemplateById(
        tmpDir,
        "guru-flutter-client",
        "overwrite",
      );
      expect(result.success).toBe(true);
      const specDir = path.join(tmpDir, ".trellis", "spec");
      expect(fs.existsSync(path.join(specDir, "harness", "index.md"))).toBe(
        true,
      );
      expect(
        fs.existsSync(path.join(specDir, "guides", "golden-path.md")),
      ).toBe(true);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("returns unknown ids to the marketplace path (no bundled match)", () => {
    expect(getBundledSpecFiles("not-a-bundled-spec")).toBeNull();
  });
});

describe("retryOnTransientError", () => {
  it("succeeds on first attempt without retrying", async () => {
    let attempts = 0;
    const result = await retryOnTransientError(async () => {
      attempts++;
      return "ok";
    });
    expect(result).toBe("ok");
    expect(attempts).toBe(1);
  });

  it("retries once on a transient network error", async () => {
    let attempts = 0;
    const result = await retryOnTransientError(async () => {
      attempts++;
      if (attempts === 1) {
        throw new Error(
          "fatal: Could not read from remote repository.\nConnection closed by 198.18.0.21 port 443",
        );
      }
      return "ok";
    });
    expect(result).toBe("ok");
    expect(attempts).toBe(2);
  });

  it("does not retry deterministic errors", async () => {
    let attempts = 0;
    await expect(
      retryOnTransientError(async () => {
        attempts++;
        throw new Error("HTTP 404 Not Found");
      }),
    ).rejects.toThrow("404");
    expect(attempts).toBe(1);
  });
});

describe("readTimeoutEnv", () => {
  const KEY = "GURU_TEST_TIMEOUT_MS";

  afterEach(() => {
    delete process.env.GURU_TEST_TIMEOUT_MS;
  });

  it("reads a positive integer from the environment", () => {
    process.env[KEY] = "60000";
    expect(readTimeoutEnv(KEY, 30_000)).toBe(60_000);
  });

  it("falls back on missing, invalid, or non-positive values", () => {
    expect(readTimeoutEnv(KEY, 30_000)).toBe(30_000);
    process.env[KEY] = "not-a-number";
    expect(readTimeoutEnv(KEY, 30_000)).toBe(30_000);
    process.env[KEY] = "-5";
    expect(readTimeoutEnv(KEY, 30_000)).toBe(30_000);
  });
});

describe("mergeJsonDefaults", () => {
  it("keeps existing scalars and fills missing keys", () => {
    const merged = mergeJsonDefaults(
      { env: { KEEP: "1" }, custom: true },
      { env: { KEEP: "template", ADD: "2" }, hooks: {} },
    ) as Record<string, unknown>;
    expect(merged).toEqual({
      env: { KEEP: "1", ADD: "2" },
      custom: true,
      hooks: {},
    });
  });

  it("unions arrays without duplicating deep-equal entries", () => {
    const userHook = { matcher: "Bash", hooks: [{ command: "user.sh" }] };
    const templateHook = {
      matcher: "Bash",
      hooks: [{ command: "trellis.py" }],
    };
    const merged = mergeJsonDefaults(
      { hooks: { PreToolUse: [userHook, templateHook] } },
      { hooks: { PreToolUse: [templateHook] } },
    ) as { hooks: { PreToolUse: unknown[] } };
    expect(merged.hooks.PreToolUse).toHaveLength(2);
    expect(merged.hooks.PreToolUse[0]).toEqual(userHook);
  });
});

describe("sync:guru:check drift gate", () => {
  const SYNC_SCRIPT = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "../../scripts/sync-guru-template.js",
  );
  const BUNDLED_OVERLAY = GURU_OVERLAY_ROOT;

  function runCheck() {
    return spawnSync(process.execPath, [SYNC_SCRIPT, "--check"], {
      encoding: "utf8",
    });
  }

  it("passes (exit 0) when bundled mirror matches guru-template/ SSOT", () => {
    const result = runCheck();
    // 兜底诊断：失败时打印 drift 列表，提示 `pnpm sync:guru`。
    expect(result.stdout + result.stderr).toContain("无漂移");
    expect(result.status).toBe(0);
  });

  it("detects drift (exit 1) when the bundled mirror diverges from SSOT", () => {
    // 在 bundle 注入一个源不存在的探针文件 → check 应报「多余(需删除)」。
    // 验证 gate 真能检测漂移，而非退化成永远通过的注释。finally 必删探针。
    const probe = path.join(BUNDLED_OVERLAY, "__drift_probe__.md");
    fs.writeFileSync(probe, "drift probe — must be detected by sync:guru:check\n");
    try {
      const result = runCheck();
      expect(result.status).toBe(1);
      expect(result.stderr).toContain("漂移");
      expect(result.stderr).toContain("__drift_probe__.md");
    } finally {
      fs.rmSync(probe, { force: true });
    }
  });
});
