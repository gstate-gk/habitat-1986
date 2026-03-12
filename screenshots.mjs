/**
 * Habitat automated screenshot capture using Playwright.
 * Takes screenshots of login, town square, bank, store, park, teleport hub.
 *
 * Usage: node screenshots.mjs
 * Requires: backend on :8003, frontend on :5176
 */
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const BASE = "http://localhost:5173";
const OUT = "../articles/images";
mkdirSync(OUT, { recursive: true });

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

/** Wait until text appears somewhere in the page body */
async function waitForText(page, text, timeout = 10000) {
  await page.waitForFunction(
    (t) => document.body.innerText.includes(t),
    text,
    { timeout }
  );
}

/** Wait for canvas to have non-black content (at least some colored pixels) */
async function waitForCanvasRender(page, timeout = 10000) {
  await page.waitForFunction(
    () => {
      const canvas = document.querySelector("canvas");
      if (!canvas) return false;
      const ctx = canvas.getContext("2d");
      if (!ctx) return false;
      // Sample pixels across the canvas to check for non-black content
      const w = canvas.width;
      const h = canvas.height;
      for (let x = 0; x < w; x += 40) {
        for (let y = 0; y < h; y += 40) {
          const pixel = ctx.getImageData(x, y, 1, 1).data;
          // If any pixel is not pure black (0,0,0), canvas has rendered
          if (pixel[0] > 5 || pixel[1] > 5 || pixel[2] > 5) return true;
        }
      }
      return false;
    },
    {},
    { timeout }
  );
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 700, height: 800 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  // 1. Login screen
  await page.goto(BASE);
  await page.waitForSelector('input[placeholder="Enter name..."]');
  await delay(500);
  await page.screenshot({ path: `${OUT}/habitat_login.png` });
  console.log("✓ habitat_login.png");

  // 2. Enter world as "Phread" (original Habitat character name)
  await page.fill('input[placeholder="Enter name..."]', "Phread");
  await page.click("text=Enter World");

  // Wait for WebSocket data to arrive (status bar shows region name + ONLINE)
  await waitForText(page, "ONLINE");
  await waitForText(page, "Town Square");
  // Wait for canvas to actually render something
  await waitForCanvasRender(page);
  await delay(500); // Extra frame buffer
  await page.screenshot({ path: `${OUT}/habitat_town_square.png` });
  console.log("✓ habitat_town_square.png");

  // 3. Click the sign to read it — use the action panel buttons
  const canvas = page.locator("canvas");
  const box = await canvas.boundingBox();
  if (box) {
    // Click near center-top where objects should be
    await canvas.click({ position: { x: box.width * 0.5, y: box.height * 0.22 } });
    await delay(500);

    // Click "Identify" button if visible
    const identifyBtn = page.locator("text=Identify");
    if (await identifyBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await identifyBtn.click();
      await delay(500);
    }

    // Click "Read" if it's a sign
    const readBtn = page.locator("text=Read");
    if (await readBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await readBtn.click();
      await delay(500);
    }
  }
  await page.screenshot({ path: `${OUT}/habitat_interact.png` });
  console.log("✓ habitat_interact.png");

  // 4. Navigate to Bank — click the Bank door (left area)
  if (box) {
    await canvas.click({ position: { x: box.width * 0.125, y: box.height * 0.45 } });
    await delay(500);
    const goBtn = page.locator("text=Go Through");
    if (await goBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await goBtn.click();
      await waitForText(page, "Bank");
      await waitForCanvasRender(page);
      await delay(500);
    }
  }
  await page.screenshot({ path: `${OUT}/habitat_bank.png` });
  console.log("✓ habitat_bank.png");

  // 5. Click ATM and check balance
  if (box) {
    await canvas.click({ position: { x: box.width * 0.5, y: box.height * 0.5 } });
    await delay(500);
    const balBtn = page.locator("text=Balance");
    if (await balBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await balBtn.click();
      await delay(500);
    }
  }
  await page.screenshot({ path: `${OUT}/habitat_atm.png` });
  console.log("✓ habitat_atm.png");

  // 6. Go back to Town Square and then to Store
  if (box) {
    await canvas.click({ position: { x: box.width * 0.5, y: box.height * 0.9 } });
    await delay(500);
    const goBtn = page.locator("text=Go Through");
    if (await goBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await goBtn.click();
      await waitForText(page, "Town Square");
      await waitForCanvasRender(page);
      await delay(500);
    }
    // Now in Town Square — click Store door (right side)
    await canvas.click({ position: { x: box.width * 0.875, y: box.height * 0.45 } });
    await delay(500);
    const goBtn2 = page.locator("text=Go Through");
    if (await goBtn2.isVisible({ timeout: 1000 }).catch(() => false)) {
      await goBtn2.click();
      await waitForText(page, "Store");
      await waitForCanvasRender(page);
      await delay(500);
    }
  }
  await page.screenshot({ path: `${OUT}/habitat_store.png` });
  console.log("✓ habitat_store.png");

  // 7. Say something in chat
  const chatInput = page.locator('input[placeholder="Say something..."]');
  if (await chatInput.isVisible({ timeout: 1000 }).catch(() => false)) {
    await chatInput.fill("Hello, Habitat! 1986 lives again.");
    await page.click("text=Speak");
    await delay(1000);
  }
  await page.screenshot({ path: `${OUT}/habitat_chat.png` });
  console.log("✓ habitat_chat.png");

  await browser.close();
  console.log("\nAll screenshots saved to articles/images/");
}

main().catch(console.error);
