import { test, expect } from "@playwright/test";

test("public company-brain workflow uses live graph evidence and blocks writes", async ({
  page,
  request,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  const health = await request.get("/api/health");
  expect(health.status()).toBe(200);
  expect(await health.json()).toMatchObject({
    status: "ok",
    mode: "public-readonly",
    provider_configured: false,
  });
  const api = await request.get("/api/decisions/dec-auth-002/preview");
  const preview = await api.json();
  expect(preview.decision_status).toBe("proposed");
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "One decision. A world of consequences.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Replace OrionAuth with NovaID" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Explore the live company brain", exact: true })
    .click();
  await expect(page).toHaveURL(/\/studio$/);
  await expect(page.locator(".metrics strong").first()).toHaveText(
    String(preview.counts.services),
  );
  await expect(
    page.getByRole("button", { name: "Public read-only demo", exact: true }),
  ).toBeDisabled();
  const claim = page.getByRole("button", { name: /chat-077/ });
  await expect(claim).toBeVisible();
  await claim.click();
  await expect(
    page.getByRole("dialog", { name: "Source evidence" }),
  ).toContainText("SHA-256");
  await page.getByRole("button", { name: "Close source evidence" }).click();
  await page.getByRole("tab", { name: /02 Evidence/ }).click();
  await expect(
    page.getByRole("heading", {
      name: "Unlinked obsolete mentions",
      exact: true,
    }),
  ).toBeVisible();
  await page.screenshot({
    path: info.outputPath("desktop-evidence.png"),
    fullPage: true,
  });
  await page.getByRole("tab", { name: /03 Action Board/ }).click();
  // A fresh CI fixture can have no recorded tasks; a deployment snapshot retains them.
  await expect(
    page.getByText("Local drafts only. Approval creates an audit event."),
  ).toBeVisible();
  for (const path of [
    "/api/admin/import",
    "/api/admin/agent/runs",
    "/api/admin/tasks/test/approve",
    "/api/admin/decisions/dec-auth-002/accept",
  ]) {
    expect((await request.post(path, { data: {} })).status()).toBe(403);
  }
  await page.setViewportSize({ width: 375, height: 900 });
  await page.getByRole("tab", { name: /01 Preview/ }).click();
  await expect(page.locator(".metrics strong").first()).toHaveText(
    String(preview.counts.services),
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: info.outputPath("mobile-preview.png"),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
