#!/usr/bin/env node
/**
 * Release orchestrator for the CLI + core pair.
 *
 * This keeps package.json as a thin command table while the release sequence
 * stays in one place:
 *   manifest/docs guards -> tests -> pre-release commit -> synchronized bump
 *   -> version check -> version commit -> tag -> push
 */
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CLI_DIR = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(__dirname, "../../..");
const CORE_PKG = path.join(REPO_ROOT, "packages/core/package.json");
const CLI_PKG = path.join(REPO_ROOT, "packages/cli/package.json");
const GURU_CLI_PACKAGE = "@devsc/trellis";
const SAFE_GURU_BRANCH_RE = /^guru\/[A-Za-z0-9._/-]+$/;

const RELEASE_TYPES = new Set([
  "patch",
  "minor",
  "major",
  "beta",
  "rc",
  "promote",
]);

function fail(message) {
  console.error(`x ${message}`);
  process.exit(1);
}

function readJSON(p) {
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function packageNames() {
  return {
    core: readJSON(CORE_PKG).name,
    cli: readJSON(CLI_PKG).name,
  };
}

function pnpmFilter(packageName, script) {
  return `pnpm --filter ${packageName} --fail-if-no-match ${script}`;
}

function run(command, options = {}) {
  execSync(command, {
    cwd: options.cwd ?? CLI_DIR,
    env: process.env,
    stdio: options.capture ? ["pipe", "pipe", "pipe"] : "inherit",
    encoding: "utf-8",
  });
}

function output(command, options = {}) {
  return execSync(command, {
    cwd: options.cwd ?? CLI_DIR,
    env: process.env,
    stdio: ["pipe", "pipe", "pipe"],
    encoding: "utf-8",
  }).trim();
}

function hasGitDiff() {
  try {
    execSync("git diff-index --quiet HEAD", {
      cwd: CLI_DIR,
      stdio: ["pipe", "pipe", "pipe"],
    });
    return false;
  } catch {
    return true;
  }
}

function docsGuard(type) {
  if (type === "beta" || type === "rc" || type === "promote") {
    run(`node scripts/check-docs-changelog.js --type ${type}`);
  }
}

export function pushTarget(type, options = {}) {
  if (type === "beta" || type === "rc") return "HEAD";

  const { cliPackageName, currentBranch } = options;
  if (cliPackageName !== GURU_CLI_PACKAGE) return "main";

  if (!currentBranch) {
    throw new Error(
      "Cannot determine the current branch for a Guru release; refusing to push tags.",
    );
  }
  if (!currentBranch.startsWith("guru/")) {
    throw new Error(
      `Guru releases must run from a guru/* branch, got "${currentBranch}"; refusing to push tags.`,
    );
  }
  if (!SAFE_GURU_BRANCH_RE.test(currentBranch)) {
    throw new Error(
      `Guru release branch "${currentBranch}" contains unsupported characters; refusing to push tags.`,
    );
  }
  return currentBranch;
}

function main() {
  const [type = "patch"] = process.argv.slice(2);
  if (!RELEASE_TYPES.has(type)) {
    fail(`usage: release.js <patch|minor|major|beta|rc|promote>`);
  }

  run("node scripts/check-manifest-continuity.js --official");
  run("node scripts/check-manifest-continuity.js");
  docsGuard(type);
  const packages = packageNames();
  const currentBranch = output("git branch --show-current", { cwd: REPO_ROOT });
  let target;
  try {
    target = pushTarget(type, {
      cliPackageName: packages.cli,
      currentBranch,
    });
  } catch (error) {
    fail(error instanceof Error ? error.message : String(error));
  }
  run(pnpmFilter(packages.core, "test"));
  run("pnpm test");

  run("git add -A -- ':!docs-site' ':!marketplace'");
  if (hasGitDiff()) {
    run("git commit -m 'chore: pre-release updates'");
  }

  const version = output(`node scripts/bump-versions.js ${type}`);
  run("node scripts/release-preflight.js check-versions");
  run("git add package.json ../core/package.json");
  run(`git commit -m "${version}"`);
  run(`git tag "v${version}"`);
  run(`git push origin ${target} --tags`);
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  main();
}
