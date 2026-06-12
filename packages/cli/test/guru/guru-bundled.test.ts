/**
 * Guru fork additions: bundled workflow/spec resolution, transient-error
 * retry, env-configurable timeouts, and defaults-style settings merge.
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  GURU_CLIENT_WORKFLOW_ID,
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
      expect(resolved.content).toContain("client-grill");
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
