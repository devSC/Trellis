import { spawn } from "node:child_process";
import fs from "node:fs";
import path, { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

export type GuruPlatform = "flutter" | "go" | "ios" | "h5";

export interface GuruApplyOptions {
  withGitnexus?: boolean;
  adversarialEnabled?: string;
}

const GURU_TEMPLATE_PLATFORMS: Record<string, GuruPlatform> = {
  "guru-flutter-client": "flutter",
  "guru-go-backend": "go",
  "guru-ios-native": "ios",
  "guru-h5-web": "h5",
};

const GURU_WORKFLOW_PLATFORMS: Record<string, GuruPlatform> = {
  "guru-client": "flutter",
  "guru-go": "go",
  "guru-ios": "ios",
  "guru-h5": "h5",
};

function isGuruPlatform(value: string): value is GuruPlatform {
  return ["flutter", "go", "ios", "h5"].includes(value);
}

function normalizeOptionalBoolean(value?: string): string | undefined {
  if (value === undefined) return undefined;

  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return "true";
  if (["0", "false", "no", "off"].includes(normalized)) return "false";
  throw new Error("--adversarial-enabled must be true or false");
}

export function inferGuruPlatform(
  templateId?: string | null,
  workflowId?: string | null,
): GuruPlatform | null {
  if (templateId && GURU_TEMPLATE_PLATFORMS[templateId]) {
    return GURU_TEMPLATE_PLATFORMS[templateId];
  }
  if (workflowId && GURU_WORKFLOW_PLATFORMS[workflowId]) {
    return GURU_WORKFLOW_PLATFORMS[workflowId];
  }
  return null;
}

export async function applyGuruOverlay(
  platform: string,
  target = process.cwd(),
  options: GuruApplyOptions = {},
): Promise<void> {
  if (!isGuruPlatform(platform)) {
    throw new Error("platform must be one of: flutter, go, ios, h5");
  }

  const applyScript = path.resolve(
    __dirname,
    "../templates/guru/overlay/apply.sh",
  );
  if (!fs.existsSync(applyScript)) {
    throw new Error(`Guru overlay installer not found: ${applyScript}`);
  }
  const adversarialEnabled = normalizeOptionalBoolean(
    options.adversarialEnabled,
  );

  await new Promise<void>((resolve, reject) => {
    const child = spawn("bash", [applyScript, path.resolve(target), platform], {
      stdio: "inherit",
      env: {
        ...process.env,
        GURU_WITH_GITNEXUS: options.withGitnexus ? "1" : "0",
        GURU_ADVERSARIAL_ENABLED: adversarialEnabled ?? "",
      },
    });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Guru overlay installer exited with code ${code}`));
      }
    });
  });
}
