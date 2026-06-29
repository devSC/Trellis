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
 *
 * --check (drift gate): sync into a temp dir, then diff the three managed
 * subtrees (specs/workflows/overlay) against src/templates/guru/ file-by-file.
 * Any drift -> exit 1, working tree untouched. Catches "edited guru-template/
 * but forgot sync:guru", which would ship a forked/stale bundled CLI.
 *   pnpm -C packages/cli sync:guru:check
 */
import {
  cpSync,
  rmSync,
  mkdirSync,
  readdirSync,
  statSync,
  existsSync,
  mkdtempSync,
  readFileSync,
} from "node:fs";
import { extname, join, relative } from "node:path";
import { tmpdir } from "node:os";

const CHECK = process.argv.includes("--check");
const repoRoot = join(import.meta.dirname, "../../..");
const src = join(repoRoot, "guru-template");
const realDest = join(import.meta.dirname, "../src/templates/guru");
// --check syncs into a throwaway temp dir; normal run writes the real bundle.
const dest = CHECK ? mkdtempSync(join(tmpdir(), "guru-sync-check-")) : realDest;
const EXCLUDED_ENTRIES = new Set(["__pycache__", ".DS_Store"]);
const EXCLUDED_EXTENSIONS = new Set([".pyc", ".pyo"]);
// sync 只管理这三个子树；index.ts 等手写文件不在其列，--check 比对时跳过。
const MANAGED_SUBTREES = ["specs", "workflows", "overlay"];

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

// 递归列出 root 下所有文件的相对路径（应用同一 shouldSkip 排除；root 不存在→空）。
function listFiles(root) {
  const out = [];
  function walk(dir) {
    if (!existsSync(dir)) return;
    for (const entry of readdirSync(dir)) {
      if (shouldSkip(entry)) continue;
      const p = join(dir, entry);
      if (statSync(p).isDirectory()) walk(p);
      else out.push(relative(root, p));
    }
  }
  walk(root);
  return out;
}

// 比对 realDest（现有 bundle）与 freshDest（刚从 SSOT sync 出的临时副本）的三个
// 被管理子树，返回 drift 描述列表（空=一致）。workflow 文件名映射与 excludes 已由
// sync 逻辑处理，两边对称，故直接逐文件比对即可。
function diffManaged(real, fresh) {
  const drift = [];
  for (const sub of MANAGED_SUBTREES) {
    const realFiles = new Set(listFiles(join(real, sub)));
    const freshFiles = new Set(listFiles(join(fresh, sub)));
    for (const f of freshFiles) {
      if (!realFiles.has(f)) drift.push(`缺失(需新增): ${sub}/${f}`);
    }
    for (const f of realFiles) {
      if (!freshFiles.has(f)) drift.push(`多余(需删除): ${sub}/${f}`);
    }
    for (const f of freshFiles) {
      if (!realFiles.has(f)) continue;
      const a = readFileSync(join(real, sub, f));
      const b = readFileSync(join(fresh, sub, f));
      if (!a.equals(b)) drift.push(`内容差异: ${sub}/${f}`);
    }
  }
  return drift;
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

if (CHECK) {
  const drift = diffManaged(realDest, dest);
  rmSync(dest, { recursive: true, force: true }); // 临时副本用完即删，绝不触碰工作树
  if (drift.length) {
    console.error(
      `guru bundled mirror 漂移（${drift.length} 处）：guru-template/ 改了未 sync。\n` +
        drift.map((d) => `  ${d}`).join("\n") +
        `\n修复：pnpm -C packages/cli sync:guru`,
    );
    process.exit(1);
  }
  console.log("guru bundled mirror 与 guru-template/ 一致（无漂移）");
} else {
  console.log(
    `Synced guru-template/ -> src/templates/guru/ ` +
      `(${specCount} spec packages, ${wfCount} workflows, ${overlayCount} overlay files)`,
  );
}
