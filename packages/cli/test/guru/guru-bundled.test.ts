/**
 * Guru fork additions: bundled workflow/spec resolution, transient-error
 * retry, env-configurable timeouts, and defaults-style settings merge.
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
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
      expect(resolved.content).toContain("design-grill");
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
      const defaultRoute = workflowStateBlock(
        resolved.content,
        "in_progress",
      );
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
    expect(designGrill).toContain("grill-done");
    expect(designGrill).toContain("grill-skip");
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
  });

  it("keeps packaged Guru helper scripts in sync with the source overlay", () => {
    for (const helper of ["guru_config_patch.py", "guru_supervise.py"]) {
      const source = fs.readFileSync(
        path.join(GURU_SOURCE_OVERLAY_ROOT, "verify", helper),
        "utf8",
      );
      const packaged = readOverlayFile("verify", helper);
      expect(packaged).toBe(source);
    }
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

  function runPatch(platform: string): void {
    execFileSync(
      python,
      [
        patcher,
        "ensure-supervision-defaults",
        "--root",
        tmpDir,
        "--platform",
        platform,
      ],
      { encoding: "utf8" },
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
        { encoding: "utf8", stdio: "pipe" },
      ),
    ).toThrow(/guru is a scalar/);
  });
});

describe("guru_supervise.py", () => {
  let tmpDir: string;
  const python = process.env.PYTHON ?? "python3";
  const supervisor = overlayPath("verify", "guru_supervise.py");

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
