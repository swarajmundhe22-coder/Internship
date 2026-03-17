import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";
import { PNG } from "pngjs";
import pixelmatch from "pixelmatch";

const root = process.cwd();
const baseUrl = process.env.BASE_URL ?? "http://127.0.0.1:3000";

const baselineDir = path.join(root, "artifacts", "visual_qa", "after");
const outRoot = path.join(root, "artifacts", "visual_qa_intensity");
const currentDir = path.join(outRoot, "current");
const diffDir = path.join(outRoot, "diff");

for (const dir of [currentDir, diffDir]) {
  fs.mkdirSync(dir, { recursive: true });
}

const states = [
  { key: "home-mobile", page: "/", viewport: { width: 390, height: 844 } },
  { key: "home-tablet", page: "/", viewport: { width: 768, height: 1024 } },
  { key: "home-desktop", page: "/", viewport: { width: 1440, height: 900 } },
  { key: "dashboard-mobile", page: "/dashboard", viewport: { width: 390, height: 844 } },
  { key: "dashboard-tablet", page: "/dashboard", viewport: { width: 768, height: 1024 } },
  { key: "dashboard-desktop", page: "/dashboard", viewport: { width: 1440, height: 900 } },
  { key: "simulations-mobile", page: "/simulations", viewport: { width: 390, height: 844 } },
  { key: "simulations-tablet", page: "/simulations", viewport: { width: 768, height: 1024 } },
  { key: "simulations-desktop", page: "/simulations", viewport: { width: 1440, height: 900 } }
];

function readPng(filePath) {
  return PNG.sync.read(fs.readFileSync(filePath));
}

function writePng(filePath, png) {
  fs.writeFileSync(filePath, PNG.sync.write(png));
}

async function captureCurrentState(state) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: state.viewport });
  const page = await context.newPage();

  try {
    await page.goto(`${baseUrl}${state.page}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(1600);

    if (state.page === "/") {
      await page.mouse.move(Math.floor(state.viewport.width * 0.72), Math.floor(state.viewport.height * 0.24));
    } else {
      await page.mouse.move(Math.floor(state.viewport.width * 0.5), Math.floor(state.viewport.height * 0.35));
    }

    await page.waitForTimeout(450);

    const outPath = path.join(currentDir, `${state.key}.png`);
    await page.screenshot({ path: outPath, fullPage: false, animations: "disabled" });
    return outPath;
  } finally {
    try {
      await context.close();
    } catch {}
    try {
      await browser.close();
    } catch {}
  }
}

async function captureWithRetry(state, attempts = 2) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await captureCurrentState(state);
    } catch (error) {
      lastError = error;
      console.warn(`Retry ${attempt}/${attempts} failed for ${state.key}`);
      await new Promise((resolve) => setTimeout(resolve, 600));
    }
  }
  throw lastError;
}

async function run() {
  const report = [];

  for (const state of states) {
    console.log(`Intensity diff capture: ${state.key}`);

    const baselinePath = path.join(baselineDir, `${state.key}.png`);
    if (!fs.existsSync(baselinePath)) {
      throw new Error(`Missing baseline screenshot: ${baselinePath}`);
    }

    const currentPath = await captureWithRetry(state, 3);
    const beforePng = readPng(baselinePath);
    const afterPng = readPng(currentPath);

    if (beforePng.width !== afterPng.width || beforePng.height !== afterPng.height) {
      throw new Error(`Dimension mismatch for ${state.key}`);
    }

    const diffPng = new PNG({ width: beforePng.width, height: beforePng.height });
    const mismatchPixels = pixelmatch(
      beforePng.data,
      afterPng.data,
      diffPng.data,
      beforePng.width,
      beforePng.height,
      { threshold: 0.09, includeAA: false }
    );

    const totalPixels = beforePng.width * beforePng.height;
    const mismatchPercent = Number(((mismatchPixels / totalPixels) * 100).toFixed(3));
    const diffPath = path.join(diffDir, `${state.key}.png`);
    writePng(diffPath, diffPng);

    report.push({
      state: state.key,
      page: state.page,
      viewport: state.viewport,
      baseline: path.relative(root, baselinePath).replaceAll("\\", "/"),
      current: path.relative(root, currentPath).replaceAll("\\", "/"),
      diff: path.relative(root, diffPath).replaceAll("\\", "/"),
      mismatchPixels,
      mismatchPercent
    });
  }

  const reportPath = path.join(outRoot, "report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`Wrote intensity diff report: ${reportPath}`);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
