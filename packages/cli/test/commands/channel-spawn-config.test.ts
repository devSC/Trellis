import type { ChildProcess } from "node:child_process";
import { spawn } from "node:child_process";
import { EventEmitter } from "node:events";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createChannel } from "../../src/commands/channel/create.js";
import { channelSpawn } from "../../src/commands/channel/spawn.js";
import {
  projectKey,
  workerFile,
} from "../../src/commands/channel/store/paths.js";

vi.mock("node:child_process", () => ({
  spawn: vi.fn(() => {
    const child = new EventEmitter() as ChildProcess;
    child.pid = 12345;
    child.unref = vi.fn((): ChildProcess => child);
    process.nextTick(() => child.emit("spawn"));
    return child;
  }),
}));

const noop = (): void => undefined;

interface SupervisorConfigProbe {
  provider: string;
  model?: string;
  reasoningEffort?: string;
}

describe("channel spawn supervisor config", () => {
  let tmpDir: string;
  let projectDir: string;
  let oldRoot: string | undefined;
  let oldProject: string | undefined;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "trellis-channel-spawn-"));
    projectDir = path.join(tmpDir, "project");
    fs.mkdirSync(projectDir);
    oldRoot = process.env.TRELLIS_CHANNEL_ROOT;
    oldProject = process.env.TRELLIS_CHANNEL_PROJECT;
    process.env.TRELLIS_CHANNEL_ROOT = path.join(tmpDir, "channels");
    delete process.env.TRELLIS_CHANNEL_PROJECT;
    vi.mocked(spawn).mockClear();
    vi.spyOn(process, "cwd").mockReturnValue(projectDir);
    vi.spyOn(console, "log").mockImplementation(noop);
    vi.spyOn(console, "error").mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    if (oldRoot === undefined) delete process.env.TRELLIS_CHANNEL_ROOT;
    else process.env.TRELLIS_CHANNEL_ROOT = oldRoot;
    if (oldProject === undefined) delete process.env.TRELLIS_CHANNEL_PROJECT;
    else process.env.TRELLIS_CHANNEL_PROJECT = oldProject;
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("writes spawn reasoning effort into the supervisor config", async () => {
    await createChannel("review", { by: "main" });
    await channelSpawn("review", {
      provider: "codex",
      as: "codex-review",
      cwd: projectDir,
      model: "gpt-5.4",
      reasoningEffort: "high",
    });

    const configPath = workerFile(
      "review",
      "codex-review",
      "config",
      projectKey(projectDir),
    );
    const config = JSON.parse(
      fs.readFileSync(configPath, "utf8"),
    ) as SupervisorConfigProbe;

    expect(config).toMatchObject({
      provider: "codex",
      model: "gpt-5.4",
      reasoningEffort: "high",
    });
  });
});
