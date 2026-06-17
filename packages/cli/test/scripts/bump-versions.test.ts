import { describe, expect, it } from "vitest";

import { computeNext } from "../../scripts/bump-versions.js";
import { computeNpmTag } from "../../scripts/release-preflight.js";

describe("computeNext", () => {
  it("increments Guru patch suffix without dropping to the official version", () => {
    expect(computeNext("0.6.0-guru.1", "patch")).toBe("0.6.0-guru.2");
  });

  it("increments Guru suffix on an upstream prerelease base", () => {
    expect(computeNext("0.6.0-rc.0-guru.2", "patch")).toBe(
      "0.6.0-rc.0-guru.3",
    );
  });

  it("keeps the official prerelease patch behavior unchanged", () => {
    expect(computeNext("0.6.0-rc.0", "patch")).toBe("0.6.0");
  });
});

describe("computeNpmTag", () => {
  it("uses the Guru dist-tag for Guru fork versions", () => {
    expect(computeNpmTag("0.6.0-guru.1")).toBe("guru");
  });

  it("keeps official GA versions on latest", () => {
    expect(computeNpmTag("0.6.0")).toBe("latest");
  });
});
