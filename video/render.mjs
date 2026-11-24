// Render intro.html to MP4: node render.mjs [out.mp4] [--stills t1,t2,...]
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { pathToFileURL } from "node:url";
import path from "node:path";

const FPS = 30;
const args = process.argv.slice(2);
const stillsArg = args.indexOf("--stills");
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(path.resolve("intro.html")).href);
await page.evaluate(() => document.fonts.ready);

if (stillsArg >= 0) {
  for (const t of args[stillsArg + 1].split(",")) {
    await page.evaluate(t => window.render(t), +t);
    await page.screenshot({ path: `frames/still-${t}.png` });
  }
} else {
  const out = args[0] || "english-coach-intro.mp4";
  const duration = await page.evaluate(() => window.DURATION);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS),
    "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
    "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
  const total = Math.round(duration * FPS);
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.render(t), i / FPS);
    const buf = await page.screenshot({ type: "png" });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (i % 300 === 0) console.log(`frame ${i}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  console.log(`wrote ${out}`);
}
await browser.close();
