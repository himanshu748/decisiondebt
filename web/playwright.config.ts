import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  retries: 0,
  timeout: 60_000,
  outputDir: process.env.DD_UI_OUTPUT || "../work/ui-smoke",
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile: process.env.DD_UI_REPORT || "../work/ui-smoke/report.json",
      },
    ],
  ],
  use: {
    baseURL: process.env.DD_BASE_URL || "http://127.0.0.1:8000",
    browserName: "chromium",
    viewport: { width: 1440, height: 1100 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
