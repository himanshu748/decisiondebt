import { chromium, expect } from "@playwright/test";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";

const origin = "https://decisiondebt.52.202.25.181.sslip.io";
const ew = "https://embodiweave.52.202.25.181.sslip.io/";
const output = process.env.DD_PROBE_OUTPUT || "work/external-ask";
await mkdir(output, { recursive: true });
const save = (name, value) =>
  writeFile(path.join(output, name), JSON.stringify(value, null, 2) + "\n");
const pause = (ms) => new Promise((r) => setTimeout(r, ms));
async function contentReceipt(url) {
  const response = await fetch(url, { cache: "no-store" });
  const body = Buffer.from(await response.arrayBuffer());
  return {
    url,
    status: response.status,
    bytes: body.length,
    sha256: createHash("sha256").update(body).digest("hex"),
  };
}
const receipt = {
  started_at: new Date().toISOString(),
  origin,
  runner: process.env.GITHUB_ACTIONS
    ? "GitHub-hosted ubuntu-24.04, outside deployment host"
    : "local",
  commit: process.env.GITHUB_SHA || null,
  run_url: process.env.GITHUB_RUN_ID
    ? `https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`
    : null,
  embodiweave_before: await contentReceipt(ew),
  cases: [],
  passed: false,
};

for (const width of [1440, 375]) {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width, height: 1000 },
    serviceWorkers: "block",
    permissions: ["clipboard-read", "clipboard-write"],
  });
  const page = await context.newPage();
  const result = {
    width,
    fresh_process: true,
    fresh_profile: true,
    chromium_version: browser.version(),
    console_errors: [],
    page_errors: [],
    failed_requests: [],
    responses: [],
    ui_writes: [],
    questions: [],
    exports: [],
    passed: false,
  };
  page.on("console", (m) => {
    if (m.type() === "error") result.console_errors.push(m.text());
  });
  page.on("pageerror", (e) => result.page_errors.push(e.message));
  page.on("requestfailed", (r) =>
    result.failed_requests.push({
      url: r.url(),
      error: r.failure()?.errorText,
    }),
  );
  page.on("response", (r) =>
    result.responses.push({ url: r.url(), status: r.status() }),
  );
  page.on("request", (r) => {
    if (!["GET", "HEAD", "OPTIONS"].includes(r.method()))
      result.ui_writes.push({ method: r.method(), url: r.url() });
  });
  try {
    result.health_before = await (
      await context.request.get(origin + "/api/health")
    ).json();
    expect(result.health_before).toMatchObject({
      mode: "public-readonly",
      graph_revision: 16,
      provider_configured: false,
    });
    const landing = await page.goto(origin + "/", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    expect(landing.status()).toBe(200);
    await expect(page.locator(".hero-counts strong").first()).toHaveText("12", {
      timeout: 15000,
    });
    await page.locator(".landing-ask").scrollIntoViewIfNeeded();
    await page.screenshot({
      path: path.join(output, `${width}-landing-teaser.png`),
    });
    await page
      .locator(".landing-ask")
      .getByRole("button", { name: "Ask graph", exact: true })
      .click();
    await expect(page).toHaveURL(/\/studio\?q=/);
    await expect(page.getByTestId("affected-count")).toHaveText("12", {
      timeout: 15000,
    });
    const panel = page.locator(".ask-graph");
    await expect(panel.locator(".ask-result-heading")).toContainText(
      "Ownership conflict",
    );
    result.landing_teaser_runs_question = true;
    for (const [intent, question, rows] of [
      ["owners", "Who owns Session Broker?", 2],
      ["dependents", "What would replacing Auth Gateway affect?", 12],
      ["projects", "Which projects use Billing API?", 1],
      ["reviewers", "Who should review a change to Auth Gateway?", 13],
      ["documents", "What documents mention Auth Gateway?", 5],
      ["gap", "Who owns Token Cache?", 1],
      ["ambiguous", "Who owns Gateway?", 0],
      ["unsupported", "Delete every service", 0],
    ]) {
      await pause(1300); // Respect the existing public per-client bucket.
      await panel
        .getByLabel("Company question", { exact: true })
        .fill(question);
      const pending = page.waitForResponse(
        (r) => r.url().includes("/api/company/ask?") && r.status() === 200,
      );
      await panel
        .getByRole("button", { name: "Ask graph", exact: true })
        .click();
      const response = await pending;
      const answer = await response.json();
      await expect(panel.locator(".ask-answer")).toHaveAttribute(
        "data-answer-status",
        answer.status,
      );
      expect(answer.row_count).toBe(rows);
      const expectedStatus = ["ambiguous", "unsupported"].includes(intent)
        ? intent
        : "answered";
      expect(answer.status).toBe(expectedStatus);
      if (expectedStatus === "answered") {
        expect(answer.graph_revision).toBe(16);
        expect(answer.citations.length).toBeGreaterThan(0);
        expect(
          answer.query_trace.every(
            (q) => q.row_count >= 0 && q.elapsed_ms >= 0 && q.params,
          ),
        ).toBe(true);
        expect(
          answer.citations.every(
            (c) => c.anchor_verified && c.excerpt.length > 0,
          ),
        ).toBe(true);
        await expect(panel.locator(".ask-rows > li")).toHaveCount(rows);
      }
      if (intent === "owners")
        expect(answer.rows.map((r) => r.label).sort()).toEqual([
          "Devon Shah",
          "Taylor Roy",
        ]);
      if (intent === "gap") expect(answer.counts.owners).toBe(0);
      if (intent === "dependents") {
        expect(answer.counts).toEqual({ services: 12, projects: 12 });
        expect(answer.truncated).toBe(true);
        expect(answer.cycle_detected).toBe(true);
        expect(answer.truncation_examples[0]).toMatchObject({
          name: "Directory Sync",
          depth: 6,
        });
        await expect(panel.locator(".ask-boundary").first()).toContainText(
          "Directory Sync at hop 6",
        );
      }
      if (intent === "ambiguous")
        expect(answer.suggestions.length).toBeGreaterThan(1);
      if (intent === "unsupported") expect(answer.query_trace).toEqual([]);
      const screenshot = `${width}-${intent}.png`;
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await panel.screenshot({ path: path.join(output, screenshot) });
      await save(`${width}-${intent}.json`, answer);
      result.questions.push({
        intent,
        question,
        status: answer.status,
        message: answer.message,
        row_count: answer.row_count,
        query_ms: answer.query_ms,
        graph_revision: answer.graph_revision,
        screenshot,
        answer_file: `${width}-${intent}.json`,
      });
      if (intent === "owners") {
        await panel.locator(".ask-citations summary").click();
        await panel.locator(".ask-query-proof summary").click();
        await panel.locator(".ask-citations").scrollIntoViewIfNeeded();
        await page.screenshot({
          path: path.join(output, `${width}-source-and-query-proof.png`),
        });
        const citation = answer.citations[0];
        await pause(1300);
        const source = await (
          await context.request.get(
            origin + "/api/sources/" + encodeURIComponent(citation.source_id),
          )
        ).json();
        expect(source.body.slice(citation.start, citation.end)).toBe(
          citation.excerpt,
        );
        expect(source.sha256).toBe(citation.source_sha256);
        result.source_span_rechecked_against_source_api = true;
      }
    }
    // Real deployed draft data; no API interception or synthetic test fixture.
    await page.getByRole("tab", { name: /03 Action Board/ }).click();
    const cards = page.locator(".task-card");
    await expect(cards.first()).toBeVisible();
    const tasks = (
      await (await context.request.get(origin + "/api/tasks")).json()
    ).tasks;
    for (const card of await cards.all()) {
      if (
        !(await card
          .getByRole("button", { name: "Copy as ticket", exact: true })
          .count())
      )
        continue;
      await card
        .getByRole("button", { name: "Copy as ticket", exact: true })
        .click();
      await expect(card.getByRole("status")).toContainText("Ticket copied");
      const markdown = await page.evaluate(() =>
        navigator.clipboard.readText(),
      );
      expect(markdown).toContain("## Why");
      expect(markdown).toContain("## Evidence");
      expect(markdown).toMatch(/\/api\/(claims|sources)\//);
      const taskId = await card.getAttribute("data-task-id");
      const task = tasks.find((t) => t.id === taskId);
      expect(task).toBeTruthy();
      const expectedOwner =
        task.owner_status === "single_primary" && task.owner_id
          ? task.owner_id
          : "unassigned: needs decision";
      expect(markdown).toContain(expectedOwner);
      expect(markdown).toContain(task.reason);
      const downloadEvent = page.waitForEvent("download");
      await card
        .getByRole("button", { name: "Download .md", exact: true })
        .click();
      const download = await downloadEvent;
      const filename = `${width}-${download.suggestedFilename()}`;
      await download.saveAs(path.join(output, filename));
      expect(await readFile(path.join(output, filename), "utf8")).toBe(
        markdown,
      );
      result.exports.push({
        task_id: taskId,
        filename,
        suggested_owner: expectedOwner,
        clipboard_matches_download: true,
        clipboard_sha256: createHash("sha256").update(markdown).digest("hex"),
      });
    }
    expect(result.exports.length).toBeGreaterThan(0);
    await page
      .locator(".action-grid")
      .screenshot({ path: path.join(output, `${width}-ticket-exports.png`) });
    result.write_denials = [];
    for (const route of [
      "/api/company/ask",
      "/api/admin/import",
      "/api/admin/agent/runs",
      "/api/admin/tasks/test/approve",
      "/api/admin/decisions/dec-auth-002/accept",
    ]) {
      const response = await context.request.post(origin + route, { data: {} });
      result.write_denials.push({ route, status: response.status() });
      expect(response.status()).toBe(403);
    }
    await pause(1300);
    result.health_after = await (
      await context.request.get(origin + "/api/health")
    ).json();
    expect(result.health_after).toEqual(result.health_before);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(result.ui_writes).toEqual([]);
    expect(result.page_errors).toEqual([]);
    expect(result.console_errors).toEqual([]);
    expect(
      result.failed_requests.filter((r) => r.url.startsWith(origin)),
    ).toEqual([]);
    expect(
      result.responses.filter(
        (r) => r.url.startsWith(origin) && r.status >= 400,
      ),
    ).toEqual([]);
    result.passed = true;
  } catch (error) {
    result.error = String(error);
    await page.screenshot({
      path: path.join(output, `${width}-failure.png`),
      fullPage: true,
    });
  } finally {
    receipt.cases.push(result);
    await browser.close();
    await save("receipt.json", receipt);
  }
  await pause(15000);
}
receipt.embodiweave_after = await contentReceipt(ew);
receipt.embodiweave_same_content =
  receipt.embodiweave_before.status === 200 &&
  receipt.embodiweave_after.status === 200 &&
  receipt.embodiweave_before.sha256 === receipt.embodiweave_after.sha256;
receipt.finished_at = new Date().toISOString();
receipt.passed =
  receipt.cases.every((c) => c.passed) && receipt.embodiweave_same_content;
await save("receipt.json", receipt);
console.log(
  JSON.stringify(
    {
      passed: receipt.passed,
      cases: receipt.cases.map(({ width, passed, error }) => ({
        width,
        passed,
        error,
      })),
      embodiweave_same_content: receipt.embodiweave_same_content,
    },
    null,
    2,
  ),
);
if (!receipt.passed) process.exitCode = 1;
