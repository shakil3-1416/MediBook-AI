import { expect, test } from "@playwright/test";

const email = process.env.E2E_PLATFORM_EMAIL ?? "";
const password = process.env.E2E_PLATFORM_PASSWORD ?? "";

test("platform admin signs in and opens the control center", async ({ page }) => {
  test.skip(email === "" || password === "", "set E2E_PLATFORM_EMAIL and E2E_PLATFORM_PASSWORD");
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto("/login");
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /continue to medibook/i }).click();
  await page.waitForURL((url) => url.pathname.startsWith("/login") === false, { timeout: 20_000 });
  for (const path of ["/control", "/control/operations"]) {
    const response = await page.goto(path, { waitUntil: "domcontentloaded" });
    expect(response?.status() ?? 0, `status of ${path}`).toBeLessThan(500);
    await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => undefined);
    await expect(page, `still signed in on ${path}`).not.toHaveURL(/login/);
  }
  expect(pageErrors).toEqual([]);
});
