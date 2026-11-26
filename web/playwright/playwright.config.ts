import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests",
  // The plan's scenarios are independent, but the runs are compared with the
  // other frameworks, which run one test at a time; do the same here.
  workers: 1,
  retries: 0,
  reporter: [["list"], ["junit", { outputFile: process.env.JUNIT_FILE ?? "results/junit.xml" }]],
  use: {
    baseURL: process.env.WEB_URL ?? "http://localhost:4173",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // Only for running against a locally installed browser.
        launchOptions: { executablePath: process.env.PW_EXECUTABLE || undefined },
      },
    },
  ],
});
