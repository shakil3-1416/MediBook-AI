import { expect, test } from "@playwright/test";

const email = process.env.E2E_PLATFORM_EMAIL ?? "";
const password = process.env.E2E_PLATFORM_PASSWORD ?? "";

test("platform admin lands in the control center and its data loads", async ({ page }) => {
  test.skip(email === "" || password === "", "set E2E_PLATFORM_EMAIL and E2E_PLATFORM_PASSWORD");
  const pageErrors: string[] = [];
  const failedCalls: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    const url = new URL(response.url());
    if (url.pathname.startsWith("/api/dashboard/") && response.status() >= 400) {
      failedCalls.push(`${response.status()} ${url.pathname}`);
    }
  });
  await page.goto("/login");
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /continue to medibook/i }).click();
  await page.waitForURL(/\/control/, { timeout: 20_000 });
  for (const path of ["/control", "/control/operations"]) {
    const response = await page.goto(path, { waitUntil: "domcontentloaded" });
    expect(response?.status() ?? 0, `status of ${path}`).toBeLessThan(500);
    await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => undefined);
    await expect(page, `still signed in on ${path}`).not.toHaveURL(/login/);
    await expect(page.getByText(/authentication required/i), `error on ${path}`).toHaveCount(0);
  }
  expect(failedCalls, "control center requests that failed").toEqual([]);
  expect(pageErrors).toEqual([]);
});
