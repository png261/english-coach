// Render the README poster: title frame + play button. node poster.mjs
import { chromium } from "playwright";
import { pathToFileURL } from "node:url";
import path from "node:path";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(path.resolve("intro.html")).href);
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => {
  window.render(39.0);
  document.querySelectorAll('.scene:last-of-type .cmd, .scene:last-of-type .cursor').forEach(e => e.style.display = 'none');
  [...document.querySelectorAll('.scene:last-of-type .sub')].slice(1).forEach(e => e.style.display = 'none');
  const b = document.createElement("div");
  b.innerHTML = `<svg width="132" height="132" viewBox="0 0 132 132"><circle cx="66" cy="66" r="66" fill="#FF6A45"/>
    <path d="M54 42 L92 66 L54 90 Z" fill="#FFFFFF"/></svg>
    <div style="font: 30px -apple-system, Helvetica Neue, sans-serif; color:#C9C2CC; margin-top:20px">Watch the 45-second intro</div>`;
  b.style.cssText = "position:absolute;left:0;right:0;top:640px;display:flex;flex-direction:column;align-items:center";
  document.body.append(b);
});
await page.screenshot({ path: "poster.png" });
await browser.close();
