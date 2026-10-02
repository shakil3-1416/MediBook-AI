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

function brightness(color: string) {
  const oklch = color.match(/^oklch\(\s*([\d.]+)(%?)/);
  if (oklch) {
    return oklch[2] === "%" ? Number(oklch[1]) / 100 : Number(oklch[1]);
  }
  const channels = (color.match(/[\d.]+/g) ?? []).slice(0, 3).map(Number);
  return channels.length === 3 ? (channels[0] + channels[1] + channels[2]) / 765 : 0;
}

test("landing page headline is light on its dark background", async ({ page }) => {
  await page.goto("/");
  const color = await page.locator("h1").first().evaluate((element) => getComputedStyle(element).color);
  expect(brightness(color), `headline colour ${color}`).toBeGreaterThan(0.8);
});
