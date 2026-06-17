import { describe, expect, it } from "vitest";

import { pushTarget } from "../../scripts/release.js";

describe("pushTarget", () => {
  it("keeps beta and rc releases on HEAD", () => {
    expect(
      pushTarget("beta", {
        cliPackageName: "@devsc/trellis",
        currentBranch: "guru/main",
      }),
    ).toBe("HEAD");
    expect(
      pushTarget("rc", {
        cliPackageName: "@devsc/trellis",
        currentBranch: "guru/main",
      }),
    ).toBe("HEAD");
  });

  it("keeps official stable releases on main", () => {
    expect(
      pushTarget("patch", {
        cliPackageName: "@mindfoldhq/trellis",
        currentBranch: "release/0.6",
      }),
    ).toBe("main");
    expect(
      pushTarget("promote", {
        cliPackageName: "@mindfoldhq/trellis",
        currentBranch: "release/0.6",
      }),
    ).toBe("main");
  });

  it("pushes Guru stable releases to the current guru branch", () => {
    for (const type of ["patch", "minor", "major", "promote"]) {
      expect(
        pushTarget(type, {
          cliPackageName: "@devsc/trellis",
          currentBranch: "guru/main",
        }),
      ).toBe("guru/main");
    }
  });

  it("allows normal Guru release branch names", () => {
    expect(
      pushTarget("patch", {
        cliPackageName: "@devsc/trellis",
        currentBranch: "guru/release-0.6.0",
      }),
    ).toBe("guru/release-0.6.0");
  });

  it("refuses Guru stable releases from main", () => {
    expect(() =>
      pushTarget("patch", {
        cliPackageName: "@devsc/trellis",
        currentBranch: "main",
      }),
    ).toThrow(/guru\/\*/);
  });

  it("refuses Guru stable releases when the current branch is unknown", () => {
    expect(() =>
      pushTarget("patch", {
        cliPackageName: "@devsc/trellis",
        currentBranch: "",
      }),
    ).toThrow(/Cannot determine/);
  });

  it("refuses unsafe Guru branch names before shelling out to git push", () => {
    expect(() =>
      pushTarget("patch", {
        cliPackageName: "@devsc/trellis",
        currentBranch: "guru/main;echo",
      }),
    ).toThrow(/unsupported characters/);
  });
});
