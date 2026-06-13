#!/usr/bin/env node
/**
 * Sync bundled guru assets from repo-root guru-template/ (SSOT) into
 * src/templates/guru/ (CLI bundled copies). Run after editing guru-template/:
 *   pnpm -C packages/cli sync:guru
 *
 * Data-driven: copies EVERY spec package under guru-template/specs/* and EVERY
 * platform workflow guru-template/workflows/<id>-workflow.md -> workflows/<id>.md.
 * Adding a platform needs no edit here.
 */
import { cpSync, rmSync, mkdirSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const repoRoot = join(import.meta.dirname, "../../..");
const src = join(repoRoot, "guru-template");
const dest = join(import.meta.dirname, "../src/templates/guru");

// Only wipe what this script manages; dest also holds hand-written index.ts.
rmSync(join(dest, "workflow.md"), { force: true }); // legacy single-file layout
rmSync(join(dest, "specs"), { recursive: true, force: true });
rmSync(join(dest, "workflows"), { recursive: true, force: true });
mkdirSync(join(dest, "specs"), { recursive: true });
mkdirSync(join(dest, "workflows"), { recursive: true });

let specCount = 0;
for (const name of readdirSync(join(src, "specs"))) {
  if (statSync(join(src, "specs", name)).isDirectory()) {
    cpSync(join(src, "specs", name), join(dest, "specs", name), { recursive: true });
    specCount++;
  }
}

let wfCount = 0;
for (const file of readdirSync(join(src, "workflows"))) {
  const m = file.match(/^(guru-[a-z0-9-]+)-workflow\.md$/);
  if (m) {
    cpSync(join(src, "workflows", file), join(dest, "workflows", `${m[1]}.md`));
    wfCount++;
  }
}

// Fail fast: a silent 0-sync (missing dirs / renamed files / regex drift) would
// ship a CLI with no bundled guru assets and only break later at runtime/tests.
if (specCount === 0 || wfCount === 0) {
  throw new Error(
    `No guru assets synced: ${specCount} spec packages, ${wfCount} workflows ` +
      `(check guru-template/specs/* and guru-template/workflows/*-workflow.md)`,
  );
}

console.log(`Synced guru-template/ -> src/templates/guru/ (${specCount} spec packages, ${wfCount} workflows)`);
