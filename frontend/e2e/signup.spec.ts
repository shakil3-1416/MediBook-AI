import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const MAILPIT = process.env.E2E_MAILPIT_URL ?? "http://127.0.0.1:8025";
const TINY_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";

async function waitForCode(request: APIRequestContext, address: string): Promise<string> {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const search = await request.get(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:${address}`)}`);
    if (search.ok()) {
      const data = (await search.json()) as { messages?: { ID: string }[] };
      const first = data.messages?.[0];
      if (first) {
        const message = await request.get(`${MAILPIT}/api/v1/message/${first.ID}`);
        const body = (await message.json()) as { Text?: string };
        const match = /\b(\d{6})\b/.exec(body.Text ?? "");
        if (match) {
          return match[1];
        }
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }
  throw new Error(`no verification email for ${address}`);
}

async function enterCode(page: Page, code: string): Promise<void> {
  const boxes = page.locator('input[maxlength="1"]');
  if ((await boxes.count()) >= 6) {
    await boxes.first().click();
    await page.keyboard.type(code);
    return;
  }
  const single = page
    .locator(
      'input[autocomplete="one-time-code"], input[inputmode="numeric"], input[maxlength="6"], input[name*="code" i], input[placeholder*="code" i]',
    )
    .first();
  await single.waitFor({ state: "visible", timeout: 20_000 });
  await single.fill(code);
}

test("new patient signs up with an emailed verification code", async ({ page, request }) => {
  page.on("response", async (response) => {
    const path = new URL(response.url()).pathname;
    if (path.startsWith("/api/auth/")) {
      const detail = response.status() >= 400 ? " " + (await response.text().catch(() => "")).slice(0, 300) : "";
      console.log(`AUTH ${response.status()} ${response.request().method()} ${path}${detail}`);
    }
  });
  const stamp = Date.now();
  const address = `e2e-${stamp}@example.com`;
  const phone = `017${String(stamp).slice(-8)}`;
  const secret = `E2e-${stamp.toString(36)}-Aa9`;
  await page.goto("/signup");
  await page.locator('input:not([type]), input[type="text"]').first().fill("E2E Patient");
  await page.locator('input[type="email"]').first().fill(address);
  await page.locator('input[type="tel"]').first().fill(phone);
  const gender = page.locator("select").first();
  if ((await gender.count()) > 0) {
    await gender.selectOption({ index: 1 });
  }
  const photo = page.locator('input[type="file"]').first();
  if ((await photo.count()) > 0 && typeof (await photo.getAttribute("required")) === "string") {
    await photo.setInputFiles({ name: "avatar.png", mimeType: "image/png", buffer: Buffer.from(TINY_PNG, "base64") });
  }
  const secretFields = page.locator('input[type="password"]');
  await secretFields.nth(0).fill(secret);
  if ((await secretFields.count()) > 1) {
    await secretFields.nth(1).fill(secret);
  }
  await page.getByRole("button", { name: /^continue$/i }).click();
  const code = await waitForCode(request, address);
  await enterCode(page, code);
  const submit = page.getByRole("button", { name: /verify|confirm|create|complete|continue/i }).first();
  if (await submit.isVisible().catch(() => false)) {
    await submit.click();
  }
  await page.waitForURL((url) => url.pathname.startsWith("/signup") === false, { timeout: 30_000 });
  await expect(page).not.toHaveURL(/\/login/);
});
