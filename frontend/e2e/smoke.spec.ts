import { expect, test } from "@playwright/test";

const PAGES = [
  "/",
  "/login",
  "/signup",
  "/forgot-password",
  "/doctors",
  "/hospital-login",
  "/assistant",
  "/appointments",
  "/profile",
  "/hospital-dashboard",
  "/control",
  "/widget/medibook-demo",
  "/embed/medibook-demo",
];

for (const path of PAGES) {
  test(`page ${path} renders without server or script errors`, async ({ page }) => {
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    const response = await page.goto(path, { waitUntil: "domcontentloaded" });
    expect(response?.status() ?? 0).toBeLessThan(500);
    await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => undefined);
    expect(pageErrors).toEqual([]);
  });
}
