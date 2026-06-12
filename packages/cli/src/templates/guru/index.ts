/**
 * Guru bundled templates (fork-specific).
 *
 * Source of truth for distribution is the repo-root `guru-template/`
 * (marketplace layout). These bundled copies let `trellis init` resolve the
 * guru workflow and spec entirely offline. After editing `guru-template/`,
 * run `pnpm -C packages/cli sync:guru` to refresh these copies.
 */

import fs from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { toPosix } from "../../utils/posix.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

/** Bundled guru workflow id (selectable via `trellis init --workflow guru-client`). */
export const GURU_CLIENT_WORKFLOW_ID = "guru-client";

export const guruWorkflowMdTemplate = fs.readFileSync(
  join(__dirname, "workflow.md"),
  "utf-8",
);

const SPEC_ROOT = join(__dirname, "specs");

/** List ids of spec templates bundled with the CLI. */
export function listBundledSpecTemplateIds(): string[] {
  try {
    return fs
      .readdirSync(SPEC_ROOT, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name);
  } catch {
    return [];
  }
}

/**
 * Read a bundled spec template as a map of POSIX-relative path → content.
 * Returns null when the id is not bundled.
 */
export function getBundledSpecFiles(id: string): Map<string, string> | null {
  const root = join(SPEC_ROOT, id);
  try {
    if (!fs.statSync(root).isDirectory()) return null;
  } catch {
    return null;
  }
  const files = new Map<string, string>();
  const walk = (dir: string): void => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile()) {
        files.set(
          toPosix(relative(root, fullPath)),
          fs.readFileSync(fullPath, "utf-8"),
        );
      }
    }
  };
  walk(root);
  return files;
}
