// Render the README poster: title frame + play button. node poster.mjs
import { chromium } from "playwright";
import { pathToFileURL } from "node:url";
import path from "node:path";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(path.resolve("intro.html")).href);
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => {
  window.render(11.6);
  const b = document.createElement("div");
  b.innerHTML = `<svg width="132" height="132" viewBox="0 0 132 132"><circle cx="66" cy="66" r="66" fill="#1D1C1A"/>
    <path d="M54 42 L92 66 L54 90 Z" fill="#F4F0E8"/></svg>
    <div style="font: 30px -apple-system, Helvetica Neue, sans-serif; color:#6E6A62; margin-top:20px">Watch the 1-minute intro</div>`;
  b.style.cssText = "position:absolute;left:0;right:0;top:700px;display:flex;flex-direction:column;align-items:center";
  document.body.append(b);
});
await page.screenshot({ path: "poster.png" });
await browser.close();
