import { expect, test } from "@playwright/test";

const email = process.env.E2E_PATIENT_EMAIL ?? "";
const password = process.env.E2E_PATIENT_PASSWORD ?? "";

test("patient signs in and their appointments actually load", async ({ page }) => {
  test.skip(email === "" || password === "", "set E2E_PATIENT_EMAIL and E2E_PATIENT_PASSWORD");
  const failedCalls: string[] = [];
  page.on("response", (response) => {
    const url = new URL(response.url());
    if (url.pathname.startsWith("/api/appointments") && response.status() >= 400) {
      failedCalls.push(`${response.status()} ${url.pathname}`);
    }
  });
  await page.goto("/login");
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /continue to medibook/i }).click();
  await page.waitForURL((url) => url.pathname.startsWith("/login") === false, { timeout: 20_000 });
  await page.goto("/appointments");
  await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => undefined);
  await expect(page).not.toHaveURL(/\/login/);
  await expect(page.getByText(/could not load appointments/i)).toHaveCount(0);
  expect(failedCalls, "appointment requests that failed").toEqual([]);
});
