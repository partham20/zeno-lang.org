// Photographs each card in card.html into /og/<kind>.png, 1200 by 630.
// Run from the site root after tools/build.py: node tools/og/render.js
// The benchmarks card reads /benchmarks/data.json, so it shows the latest run.
// Then tools/og/clean.py strips everything but the pixels from the files.
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");

const root = path.resolve(__dirname, "..", "..");
const kinds = ["home", "playground", "benchmarks", "book", "download"];

(async () => {
  const data = fs.readFileSync(path.join(root, "benchmarks", "data.json"), "utf8");
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await page.addInitScript(`window.BENCH = ${data};`);
  fs.mkdirSync(path.join(root, "og"), { recursive: true });
  for (const kind of kinds) {
    await page.goto("file://" + path.join(__dirname, "card.html") + "?kind=" + kind);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(root, "og", kind + ".png") });
    console.log("og/" + kind + ".png");
  }
  await browser.close();
})();
