import { expect, test } from "@playwright/test";

test("a new customer can sign up and reach the dashboard", async ({ page }) => {
  const email = `e2e+${Date.now()}@acme.example`;

  await page.goto("/signup");
  await page.getByLabel("Organization name").fill("Acme E2E");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("password123");
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("inactive")).toBeVisible();
});

test("a signed-in user can add a note and summarize it", async ({ page }) => {
  const email = `e2e+${Date.now()}-note@acme.example`;

  await page.goto("/signup");
  await page.getByLabel("Organization name").fill("Acme Notes");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("password123");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  await page.getByLabel("Note title").fill("Launch checklist");
  await page.getByLabel("Body").fill("Set up billing. Invite the team.");
  await page.getByRole("button", { name: "Add note" }).click();
  await expect(page.getByText("Launch checklist")).toBeVisible();

  await page.goto("/feature");
  await page.getByRole("button", { name: "Summarize" }).first().click();
  await expect(page.getByText(/Summary:/)).toBeVisible();
});
