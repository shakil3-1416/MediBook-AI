import { expect, test } from "@playwright/test";

const email = process.env.E2E_HOSPITAL_EMAIL ?? "";
const password = process.env.E2E_HOSPITAL_PASSWORD ?? "";
const SECTIONS = ["", "/doctors", "/schedules", "/appointments", "/staff", "/integrations", "/audit", "/settings", "/ai"];

test("hospital admin signs in and opens every dashboard section", async ({ page }) => {
  test.skip(email === "" || password === "", "set E2E_HOSPITAL_EMAIL and E2E_HOSPITAL_PASSWORD");
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto("/hospital-login");
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.getByRole("button", { name: /continue to hospital dashboard/i }).click();
  await page.waitForURL(/\/hospital-dashboard/, { timeout: 20_000 });
  for (const section of SECTIONS) {
    const path = `/hospital-dashboard${section}`;
    const response = await page.goto(path, { waitUntil: "domcontentloaded" });
    expect(response?.status() ?? 0, `status of ${path}`).toBeLessThan(500);
    await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => undefined);
    await expect(page, `still signed in on ${path}`).not.toHaveURL(/hospital-login|\/login/);
  }
  expect(pageErrors).toEqual([]);
});
