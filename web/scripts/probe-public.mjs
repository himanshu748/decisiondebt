import { chromium, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const origin = new URL(process.env.DD_BASE_URL).origin;
if (
  ![
    "http://decisiondebt.52.202.25.181.sslip.io:8081",
    "https://decisiondebt.52.202.25.181.sslip.io",
  ].includes(origin)
)
  throw new Error("Only the approved public origins may be probed.");
const output = process.env.DD_PROBE_OUTPUT || "work/external-public";
await mkdir(output, { recursive: true });
const receipt = {
  started_at: new Date().toISOString(),
  origin,
  runner: process.env.GITHUB_ACTIONS ? "GitHub-hosted ubuntu-24.04" : "local",
  commit: process.env.GITHUB_SHA || null,
  run_url: process.env.GITHUB_RUN_ID
    ? `https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`
    : null,
  cases: [],
};

for (const width of [1440, 375]) {
  for (const [name, route] of [
    ["landing", "/"],
    ["studio", "/studio"],
    ["action-board", "/studio?tab=Action%20Board"],
  ]) {
    // Each case gets a new browser process and empty storage, with no cached profile.
    const browser = await chromium.launch();
    const context = await browser.newContext({
      viewport: { width, height: 1000 },
      serviceWorkers: "block",
    });
    const page = await context.newPage();
    const result = {
      route,
      width,
      started_at: new Date().toISOString(),
      console_errors: [],
      page_errors: [],
      failed_requests: [],
      responses: [],
      passed: false,
    };
    page.on("console", (message) => {
      if (message.type() === "error")
        result.console_errors.push(message.text());
    });
    page.on("pageerror", (error) => result.page_errors.push(error.message));
    page.on("requestfailed", (request) =>
      result.failed_requests.push({
        url: request.url(),
        method: request.method(),
        error: request.failure()?.errorText,
      }),
    );
    page.on("response", (response) =>
      result.responses.push({
        url: response.url(),
        status: response.status(),
        resource_type: response.request().resourceType(),
      }),
    );
    try {
      const response = await page.goto(origin + route, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      });
      result.document_status = response?.status();
      result.user_agent = await page.evaluate(() => navigator.userAgent);
      expect(result.document_status).toBe(200);
      if (name === "landing") {
        await expect(
          page.getByRole("heading", {
            name: "One decision. A world of consequences.",
          }),
        ).toBeVisible();
        await expect(
          page.getByRole("heading", { name: "Replace OrionAuth with NovaID" }),
        ).toBeVisible();
        await expect(page.locator(".hero-counts strong").first()).toHaveText(
          "12",
          { timeout: 15000 },
        );
      } else {
        await expect(
          page.getByRole("heading", {
            name:
              name === "action-board"
                ? "Turn uncertainty into action."
                : "Decision workspace",
          }),
        ).toBeVisible();
        if (name === "action-board") {
          await expect(
            page.getByRole("tab", { name: /03 Action Board/ }),
          ).toHaveAttribute("aria-selected", "true");
          await expect(
            page.getByText(
              "Local drafts only. Approval creates an audit event.",
            ),
          ).toBeVisible();
          await page.getByRole("tab", { name: /01 Preview/ }).click();
        }
        await expect(page.locator(".metrics strong").first()).toHaveText("12", {
          timeout: 15000,
        });
        for (const [tab, heading] of [
          ["02 Evidence", "Unlinked obsolete mentions"],
          ["03 Action Board", null],
          ["01 Preview", "Replace OrionAuth with NovaID"],
        ]) {
          await page.getByRole("tab", { name: new RegExp(tab) }).click();
          if (heading)
            await expect(
              page.getByRole("heading", { name: heading, exact: true }),
            ).toBeVisible();
          else
            await expect(
              page.getByText(
                "Local drafts only. Approval creates an audit event.",
              ),
            ).toBeVisible();
        }
        if (name === "action-board")
          await page.getByRole("tab", { name: /03 Action Board/ }).click();
      }
      const previewResponse = await context.request.get(
        origin + "/api/decisions/dec-auth-002/preview",
      );
      const preview = await previewResponse.json();
      result.preview = {
        status: previewResponse.status(),
        decision_id: preview.decision_id,
        counts: preview.counts,
        graph_revision: preview.graph_revision,
      };
      expect(preview.decision_id).toBe("dec-auth-002");
      expect(preview.counts.services).toBe(12);
      const style = await page.evaluate(() => ({
        stylesheets: document.styleSheets.length,
        document_background: getComputedStyle(document.documentElement)
          .backgroundColor,
        no_horizontal_overflow:
          document.documentElement.scrollWidth <= innerWidth,
      }));
      result.style = style;
      expect(style.stylesheets).toBeGreaterThan(0);
      expect(style.document_background).not.toBe("rgba(0, 0, 0, 0)");
      expect(style.no_horizontal_overflow).toBe(true);
      const sameOriginErrors = result.responses.filter(
        (r) => r.url.startsWith(origin) && r.status >= 400,
      );
      expect(sameOriginErrors).toEqual([]);
      expect(result.page_errors).toEqual([]);
      expect(
        result.failed_requests.filter((r) => r.url.startsWith(origin)),
      ).toEqual([]);
      result.passed = true;
    } catch (error) {
      result.error = String(error);
    } finally {
      result.screenshot = `${width}-${name}.png`;
      await page.screenshot({
        path: path.join(output, result.screenshot),
        fullPage: true,
      });
      await writeFile(
        path.join(output, `${width}-${name}.html`),
        await page.content(),
      );
      result.finished_at = new Date().toISOString();
      receipt.cases.push(result);
      await browser.close();
      await writeFile(
        path.join(output, "receipt.json"),
        JSON.stringify(receipt, null, 2) + "\n",
      );
    }
    // Respect the public API's per-client token bucket between fresh profiles.
    await new Promise((resolve) => setTimeout(resolve, 15000));
  }
}
receipt.finished_at = new Date().toISOString();
receipt.passed = receipt.cases.every((result) => result.passed);
await writeFile(
  path.join(output, "receipt.json"),
  JSON.stringify(receipt, null, 2) + "\n",
);
console.log(
  JSON.stringify(
    {
      passed: receipt.passed,
      cases: receipt.cases.map(({ route, width, passed, error }) => ({
        route,
        width,
        passed,
        error,
      })),
    },
    null,
    2,
  ),
);
if (!receipt.passed) process.exitCode = 1;
