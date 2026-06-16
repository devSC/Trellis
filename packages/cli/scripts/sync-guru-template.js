#!/usr/bin/env node
/**
 * Sync bundled guru assets from repo-root guru-template/ (SSOT) into
 * src/templates/guru/ (CLI bundled copies). Run after editing guru-template/:
 *   pnpm -C packages/cli sync:guru
 *
 * Data-driven: copies EVERY spec package under guru-template/specs/*, EVERY
 * platform workflow guru-template/workflows/<id>-workflow.md -> workflows/<id>.md,
 * and the full guru-template/overlay/ tree. Adding a platform or overlay file
 * needs no edit here.
 */
import { cpSync, rmSync, mkdirSync, readdirSync, statSync, existsSync } from "node:fs";
import { extname, join } from "node:path";

const repoRoot = join(import.meta.dirname, "../../..");
const src = join(repoRoot, "guru-template");
const dest = join(import.meta.dirname, "../src/templates/guru");
const EXCLUDED_ENTRIES = new Set(["__pycache__", ".DS_Store"]);
const EXCLUDED_EXTENSIONS = new Set([".pyc", ".pyo"]);

function shouldSkip(entry) {
  return EXCLUDED_ENTRIES.has(entry) || EXCLUDED_EXTENSIONS.has(extname(entry));
}

function copyDirectory(srcDir, destDir) {
  mkdirSync(destDir, { recursive: true });

  let copied = 0;
  for (const entry of readdirSync(srcDir)) {
    if (shouldSkip(entry)) continue;

    const from = join(srcDir, entry);
    const to = join(destDir, entry);
    if (statSync(from).isDirectory()) {
      copied += copyDirectory(from, to);
    } else {
      cpSync(from, to);
      copied++;
    }
  }

  return copied;
}

// Only wipe what this script manages; dest also holds hand-written index.ts.
rmSync(join(dest, "workflow.md"), { force: true }); // legacy single-file layout
rmSync(join(dest, "specs"), { recursive: true, force: true });
rmSync(join(dest, "workflows"), { recursive: true, force: true });
rmSync(join(dest, "overlay"), { recursive: true, force: true });
mkdirSync(join(dest, "specs"), { recursive: true });
mkdirSync(join(dest, "workflows"), { recursive: true });
mkdirSync(join(dest, "overlay"), { recursive: true });

// 源目录缺失时给出清晰报错（否则 readdirSync 直接抛 ENOENT 栈，定位困难）
for (const sub of ["specs", "workflows", "overlay"]) {
  if (!existsSync(join(src, sub))) {
    throw new Error(`源目录 guru-template/${sub}/ 不存在，无法 sync（确认 ${src} 完整）`);
  }
}

let specCount = 0;
for (const name of readdirSync(join(src, "specs"))) {
  if (statSync(join(src, "specs", name)).isDirectory()) {
    copyDirectory(join(src, "specs", name), join(dest, "specs", name));
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

const overlayCount = copyDirectory(join(src, "overlay"), join(dest, "overlay"));

// Fail fast: a silent 0-sync (missing dirs / renamed files / regex drift) would
// ship a CLI with no bundled guru assets and only break later at runtime/tests.
if (specCount === 0 || wfCount === 0 || overlayCount === 0) {
  throw new Error(
    `No guru assets synced: ${specCount} spec packages, ${wfCount} workflows, ` +
      `${overlayCount} overlay files ` +
      `(check guru-template/specs/*, guru-template/workflows/*-workflow.md, and guru-template/overlay/)`,
  );
}

console.log(
  `Synced guru-template/ -> src/templates/guru/ ` +
    `(${specCount} spec packages, ${wfCount} workflows, ${overlayCount} overlay files)`,
);
