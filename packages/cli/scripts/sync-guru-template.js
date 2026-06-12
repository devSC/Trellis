#!/usr/bin/env node
/**
 * Sync bundled guru assets from the repo-root guru-template/ (single source of
 * truth for marketplace distribution) into src/templates/guru/ (CLI bundled
 * copies). Run after editing guru-template/ workflow or specs:
 *   pnpm -C packages/cli sync:guru
 */
import { cpSync, rmSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const repoRoot = join(import.meta.dirname, "../../..");
const src = join(repoRoot, "guru-template");
const dest = join(import.meta.dirname, "../src/templates/guru");

rmSync(dest, { recursive: true, force: true });
mkdirSync(join(dest, "specs"), { recursive: true });
cpSync(join(src, "workflows/guru-client-workflow.md"), join(dest, "workflow.md"));
cpSync(join(src, "specs/guru-flutter-client"), join(dest, "specs/guru-flutter-client"), { recursive: true });
console.log("Synced guru-template/ -> src/templates/guru/");
