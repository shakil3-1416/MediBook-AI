import { expect, test } from "@playwright/test";

const email = process.env.E2E_PATIENT_EMAIL ?? "";
const password = process.env.E2E_PATIENT_PASSWORD ?? "";

test("existing patient signs in and opens appointments", async ({ page }) => {
  test.skip(email === "" || password === "", "set E2E_PATIENT_EMAIL and E2E_PATIENT_PASSWORD");
  await page.goto("/login");
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /continue to medibook/i }).click();
  await page.waitForURL((url) => url.pathname.startsWith("/login") === false, { timeout: 20_000 });
  await page.goto("/appointments");
  await expect(page).not.toHaveURL(/\/login/);
});
