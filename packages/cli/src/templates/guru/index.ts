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

/**
 * Bundled guru workflow ids (selectable via `trellis init --workflow <id>`).
 * One five-phase workflow per supported platform.
 */
export const GURU_CLIENT_WORKFLOW_ID = "guru-client";
export const GURU_GO_WORKFLOW_ID = "guru-go";
export const GURU_IOS_WORKFLOW_ID = "guru-ios";
export const GURU_H5_WORKFLOW_ID = "guru-h5";

export interface BundledWorkflowMeta {
  id: string;
  name: string;
  description: string;
}

/**
 * Registry of bundled guru workflows. Data-driven: adding a platform means
 * dropping `workflows/<id>.md` (via `sync:guru`) and appending one entry here —
 * the resolver and `trellis workflow --list` pick it up with no further edits.
 */
export const BUNDLED_GURU_WORKFLOWS: BundledWorkflowMeta[] = [
  {
    id: GURU_CLIENT_WORKFLOW_ID,
    name: "Guru Flutter Client 5-Phase Workflow",
    description:
      "Flutter 客户端 需求→概要→详细→实现→审核 五阶段（三道文档 Gate + verify 强制）",
  },
  {
    id: GURU_GO_WORKFLOW_ID,
    name: "Guru Go Backend 5-Phase Workflow",
    description:
      "Go 后端 需求→概要→详细→实现→审核 五阶段（net/http 分层依赖律 + verify 强制）",
  },
  {
    id: GURU_IOS_WORKFLOW_ID,
    name: "Guru iOS Native 5-Phase Workflow",
    description:
      "iOS 原生 需求→概要→详细→实现→审核 五阶段（DDD 四层 + verify 强制）",
  },
  {
    id: GURU_H5_WORKFLOW_ID,
    name: "Guru H5/Next.js 5-Phase Workflow",
    description:
      "H5/Next.js 需求→概要→详细→实现→审核 五阶段（App Router server-first + verify 强制）",
  },
];

const WORKFLOW_ROOT = join(__dirname, "workflows");

/**
 * Read a bundled guru workflow's markdown by id.
 *
 * - Unregistered id → `null` (legitimately falls through to marketplace resolution).
 * - Registered id whose markdown is missing/unreadable → throws (a packaging
 *   error must surface loudly, not silently degrade to a network fetch).
 */
export function getBundledGuruWorkflow(id: string): string | null {
  if (!BUNDLED_GURU_WORKFLOWS.some((workflow) => workflow.id === id)) {
    return null;
  }
  try {
    return fs.readFileSync(join(WORKFLOW_ROOT, `${id}.md`), "utf-8");
  } catch (error) {
    throw new Error(
      `Bundled guru workflow "${id}" is registered but its markdown could not be read from ` +
        `${join(WORKFLOW_ROOT, `${id}.md`)}: ` +
        `${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

/**
 * Backward-compat alias: the flutter (guru-client) workflow content. Existing
 * callers that imported `guruWorkflowMdTemplate` keep working.
 */
export const guruWorkflowMdTemplate = ((): string => {
  // 该常量在 import 期 eager 求值。getBundledGuruWorkflow 对"已注册但文件缺失"会抛错
  // （打包错误应显式）——但不应让这个 backward-compat 常量在模块加载期崩掉整个 CLI 启动。
  // 故此处降级为 ""；运行时真正解析仍走 resolveWorkflowTemplate（缺失时会正常抛错）。
  try {
    return getBundledGuruWorkflow(GURU_CLIENT_WORKFLOW_ID) ?? "";
  } catch {
    return "";
  }
})();

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
