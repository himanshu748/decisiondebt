import { test, expect } from "@playwright/test";

const demo = "https://youtu.be/_a0vrYwOlME";
const writeReason = "Public read-only demo: writes are disabled.";

// These tests use the real public server's token bucket, including after a retry.
test.afterEach(async () => {
  await new Promise((resolve) => setTimeout(resolve, 12000));
});

test("blocked JavaScript retains a useful HTML recovery screen", async ({
  page,
}, info) => {
  await page.route("**/assets/*.js", (route) => route.abort());
  await page.goto("/studio");
  await expect(
    page.getByRole("heading", { name: "DecisionDebt", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Retry loading" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Watch the recorded demo" }),
  ).toHaveAttribute("href", demo);
  await page.screenshot({
    path: info.outputPath("blocked-javascript.png"),
    fullPage: true,
  });
  await page.unroute("**/assets/*.js");
  await page.getByRole("button", { name: "Retry loading" }).click();
  await expect(page.getByTestId("affected-count")).toHaveText("12");
});

test("render failure reaches the React boundary and retry recovers", async ({
  page,
  request,
}, info) => {
  const real = await (
    await request.get("/api/decisions/dec-auth-002/preview")
  ).json();
  const preview = "**/api/decisions/dec-auth-002/preview";
  await page.route(preview, (route) =>
    route.fulfill({ json: { ...real, impacts: null } }),
  );
  await page.goto("/studio");
  await expect(
    page.getByRole("heading", { name: "The workspace couldn't open." }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Watch the recorded demo" }),
  ).toHaveAttribute("href", demo);
  await page.screenshot({
    path: info.outputPath("react-error-boundary.png"),
    fullPage: true,
  });
  await page.unroute(preview);
  await page.getByRole("button", { name: "Retry loading" }).click();
  await expect(page.getByTestId("affected-count")).toHaveText("12");
});

test("graph outage uses public copy even when health also fails", async ({
  page,
}, info) => {
  await page.route("**/api/**", (route) =>
    route.fulfill({
      status: 503,
      json: {
        error: { code: "GRAPH_UNAVAILABLE", message: "Injected graph outage" },
      },
    }),
  );
  await page.goto("/studio");
  await expect(
    page.getByText(
      "The live graph didn't respond. Retry, or watch the recorded demo.",
    ),
  ).toBeVisible();
  await expect(page.getByText(/Start FalkorDB and import/)).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Import source", exact: true }),
  ).toHaveAccessibleDescription(writeReason);
  await page.screenshot({
    path: info.outputPath("public-graph-outage.png"),
    fullPage: true,
  });
  await page.unroute("**/api/**");
  await page.getByRole("button", { name: "Retry connection" }).click();
  await expect(page.getByTestId("affected-count")).toHaveText("12");
});

test("disabled public writes have an accessible reason in every tab", async ({
  page,
}) => {
  await page.goto("/studio");
  await expect(page.getByTestId("affected-count")).toHaveText("12");
  for (const name of [
    "Import source",
    "Import new evidence",
    "Run investigation",
  ]) {
    const control = page.getByRole("button", { name, exact: true });
    await expect(control).toBeDisabled();
    await expect(control).toHaveAccessibleDescription(writeReason);
    await expect(control).toHaveAttribute("title", writeReason);
  }
  for (const tab of [/02 Evidence/, /03 Action Board/]) {
    await page.getByRole("tab", { name: tab }).click();
    const controls = page.getByRole("button", {
      name: /Run investigation|Approve locally/,
    });
    for (const control of await controls.all()) {
      await expect(control).toBeDisabled();
      await expect(control).toHaveAccessibleDescription(writeReason);
    }
  }
});
