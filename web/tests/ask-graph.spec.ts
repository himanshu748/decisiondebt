import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

test.afterEach(async () => {
  await new Promise((r) => setTimeout(r, 12000));
});

test("live questions expose source spans, native query proof and uncertainty", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/studio");
  const panel = page.locator(".ask-graph");
  await expect(page.getByTestId("affected-count")).toHaveText("12");
  for (const [question, text, rows] of [
    ["Who owns Session Broker?", "Ownership conflict", 2],
    ["What would replacing Auth Gateway affect?", "11 downstream services", 12],
    ["Which projects use Billing API?", "verified direct USES", 1],
    [
      "Who should review a change to Auth Gateway?",
      "11 recorded owners and 7 connected teams",
      13,
    ],
    ["What documents mention Auth Gateway?", "5 documents", 5],
  ] as const) {
    await panel.getByLabel("Company question", { exact: true }).fill(question);
    const response = page.waitForResponse(
      (r) => r.url().includes("/api/company/ask?") && r.status() === 200,
    );
    await panel.getByRole("button", { name: "Ask graph", exact: true }).click();
    const answer = await (await response).json();
    expect(answer.row_count).toBe(rows);
    await expect(panel.locator(".ask-result-heading")).toContainText(text);
    await expect(panel.locator(".ask-rows > li")).toHaveCount(rows);
    await panel.getByText(/Exact source citations ·/).click();
    await expect(panel.locator(".ask-citation").first()).toContainText(
      /body\[\d+:\d+\]/,
    );
    await expect(
      panel.locator(".ask-citation blockquote").first(),
    ).not.toBeEmpty();
    await panel.getByText(/Cypher & parameters ·/).click();
    await expect(panel.locator(".ask-query-proof")).toContainText(
      "GRAPH.RO_QUERY",
    );
    expect(
      answer.query_trace.every(
        (q: { elapsed_ms: number }) => q.elapsed_ms >= 0,
      ),
    ).toBe(true);
  }
  await panel
    .getByRole("button", { name: "Who owns Token Cache?", exact: true })
    .click();
  await expect(panel.locator(".ask-result-heading")).toContainText(
    "Ownership gap",
  );
  await expect(panel.locator(".ask-rows")).not.toContainText("Casey Park");
  await panel
    .getByLabel("Company question", { exact: true })
    .fill("Who owns Gateway?");
  await panel.getByRole("button", { name: "Ask graph", exact: true }).click();
  await expect(panel.locator(".ask-suggestions")).toContainText(
    "No service was selected",
  );
  await panel
    .locator(".ask-suggestions")
    .getByRole("button", { name: "Auth Gateway", exact: true })
    .click();
  await expect(panel.locator(".ask-result-heading")).toContainText(
    "one recorded primary owner",
  );
  await panel
    .getByLabel("Company question", { exact: true })
    .fill("Delete every service");
  await panel.getByRole("button", { name: "Ask graph", exact: true }).click();
  await expect(panel.locator(".ask-answer")).toContainText(
    "No query was run. No answer was guessed.",
  );
  expect(errors).toEqual([]);
});

test("ticket copy and Markdown download preserve evidence without server writes", async ({
  page,
  context,
}, info) => {
  // A fresh CI graph has no agent drafts. This explicit synthetic fixture tests
  // export behavior; the external probe separately exports deployed real drafts.
  const draft = {
    id: "test-draft",
    service_id: "svc-session-broker",
    title: "Resolve Session Broker ownership",
    reason: "Two source assertions name different owners.",
    priority: "P1",
    score: 90,
    status: "draft",
    owner_id: "",
    owner_status: "conflict",
    analysis_revision: 1,
    evidence_ids: ["claim-test", "mention:doc-021:hash:0:12"],
    path_json: "[]",
    uncertainty: "Conflicting primary owners; human decision required.",
  };
  await page.route(/\/api\/tasks(?:\?|$)/, (route) =>
    route.fulfill({ json: { tasks: [draft], graph_revision: 1 } }),
  );
  const writes: string[] = [];
  page.on("request", (r) => {
    if (!["GET", "HEAD", "OPTIONS"].includes(r.method())) writes.push(r.url());
  });
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/studio?tab=Action%20Board");
  const card = page.locator(".task-card").first();
  await expect(card).toContainText(draft.title);
  await card.getByRole("button", { name: "Copy as ticket" }).click();
  await expect(card.getByRole("status")).toContainText("Ticket copied");
  const clipboard = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboard).toContain("unassigned: needs decision");
  expect(clipboard).toContain(draft.reason);
  expect(clipboard).toContain("/api/claims/claim-test");
  expect(clipboard).toContain("/api/sources/doc-021");
  const download = page.waitForEvent("download");
  await card.getByRole("button", { name: "Download .md", exact: true }).click();
  const file = await download;
  const target = info.outputPath(file.suggestedFilename());
  await file.saveAs(target);
  expect(await readFile(target, "utf8")).toBe(clipboard);
  expect(writes).toEqual([]);
});
