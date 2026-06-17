/**
 * Compare two semver versions (handles prerelease versions)
 * Returns: -1 if a < b, 0 if a == b, 1 if a > b
 *
 * Semver rules:
 * - 0.3.0-beta.1 < 0.3.0 (prerelease is less than release)
 * - 0.3.0-alpha < 0.3.0-beta (alphabetically)
 * - 0.3.0-beta.1 < 0.3.0-beta.2 (numerically)
 * - 0.3.0-beta.16 < 0.3.0-rc.0 (alphabetically: "beta" < "rc")
 * - 0.6.0 < 0.6.0-guru.1 (Guru overlay builds are downstream patches)
 */
export function compareVersions(a: string, b: string): number {
  // Split into base version and prerelease parts on the FIRST hyphen.
  // `String.split("-", 2)` cannot be used here: in JavaScript the limit
  // truncates the result instead of joining the tail (unlike Python's
  // `maxsplit`), so `"1.0.0-alpha-1".split("-", 2)` yields
  // `["1.0.0", "alpha"]` and silently drops `-1`. SemVer permits hyphens
  // inside a single prerelease identifier (e.g. `1.0.0-alpha-1`), so we
  // must preserve everything after the first hyphen.
  const splitOnFirstHyphen = (v: string): [string, string | undefined] => {
    const idx = v.indexOf("-");
    return idx === -1 ? [v, undefined] : [v.slice(0, idx), v.slice(idx + 1)];
  };
  const [aBase, aPrerelease] = splitOnFirstHyphen(a);
  const [bBase, bPrerelease] = splitOnFirstHyphen(b);

  // Parse base version (only numeric parts before any hyphen)
  const parseBase = (v: string): number[] =>
    v.split(".").map((n) => parseInt(n, 10) || 0);

  const aBaseParts = parseBase(aBase);
  const bBaseParts = parseBase(bBase);
  const maxBaseLen = Math.max(aBaseParts.length, bBaseParts.length);

  // Compare base versions first
  for (let i = 0; i < maxBaseLen; i++) {
    const aVal = aBaseParts[i] ?? 0;
    const bVal = bBaseParts[i] ?? 0;
    if (aVal < bVal) return -1;
    if (aVal > bVal) return 1;
  }

  const isGuruOverlay = (prerelease: string | undefined): boolean =>
    prerelease === "guru" || prerelease?.startsWith("guru.") === true;

  const aIsGuruOverlay = isGuruOverlay(aPrerelease);
  const bIsGuruOverlay = isGuruOverlay(bPrerelease);

  // Guru overlay versions are a downstream distribution line built from the
  // same base release. Treat them as patches after the matching upstream GA so
  // update/migration gates can move from upstream RC/GA into the Guru package.
  if (aIsGuruOverlay && !bIsGuruOverlay) return 1;
  if (!aIsGuruOverlay && bIsGuruOverlay) return -1;

  // Base versions are equal, compare prerelease
  // No prerelease > prerelease (1.0.0 > 1.0.0-beta)
  if (!aPrerelease && bPrerelease) return 1;
  if (aPrerelease && !bPrerelease) return -1;
  if (!aPrerelease && !bPrerelease) return 0;

  // Both have prerelease, compare them (guaranteed non-null by checks above)
  // Split prerelease by dots and compare each part
  const aPre = (aPrerelease as string).split(".");
  const bPre = (bPrerelease as string).split(".");
  const maxPreLen = Math.max(aPre.length, bPre.length);

  for (let i = 0; i < maxPreLen; i++) {
    const aP = aPre[i];
    const bP = bPre[i];

    // Missing part means shorter prerelease comes first
    if (aP === undefined) return -1;
    if (bP === undefined) return 1;

    // Try numeric comparison first
    const aNum = parseInt(aP, 10);
    const bNum = parseInt(bP, 10);
    const aIsNum = !isNaN(aNum) && String(aNum) === aP;
    const bIsNum = !isNaN(bNum) && String(bNum) === bP;

    // Numeric identifiers have lower precedence than string identifiers
    if (aIsNum && !bIsNum) return -1;
    if (!aIsNum && bIsNum) return 1;

    if (aIsNum && bIsNum) {
      if (aNum < bNum) return -1;
      if (aNum > bNum) return 1;
    } else {
      // String comparison
      if (aP < bP) return -1;
      if (aP > bP) return 1;
    }
  }

  return 0;
}
