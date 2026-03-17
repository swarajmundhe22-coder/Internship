import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";
import { PNG } from "pngjs";
import pixelmatch from "pixelmatch";

const root = process.cwd();
const outRoot = path.join(root, "artifacts", "visual_qa_refinement_focus");
const beforeDir = path.join(outRoot, "before");
const afterDir = path.join(outRoot, "after");
const diffDir = path.join(outRoot, "diff");
const reportPath = path.join(outRoot, "report.json");
const baseUrl = process.env.BASE_URL ?? "http://127.0.0.1:3000";

for (const dir of [beforeDir, afterDir, diffDir]) {
  fs.mkdirSync(dir, { recursive: true });
}

const states = [
  { key: "home-mobile", page: "/", viewport: { width: 390, height: 844 } },
  { key: "home-tablet", page: "/", viewport: { width: 768, height: 1024 } },
  { key: "home-desktop", page: "/", viewport: { width: 1440, height: 900 } },
  { key: "about-mobile", page: "/about", viewport: { width: 390, height: 844 } },
  { key: "about-tablet", page: "/about", viewport: { width: 768, height: 1024 } },
  { key: "about-desktop", page: "/about", viewport: { width: 1440, height: 900 } },
  { key: "dashboard-mobile", page: "/dashboard", viewport: { width: 390, height: 844 } },
  { key: "dashboard-tablet", page: "/dashboard", viewport: { width: 768, height: 1024 } },
  { key: "dashboard-desktop", page: "/dashboard", viewport: { width: 1440, height: 900 } }
];

const beforeCSS = `
  .page-polish-about {
    --page-title-size: clamp(1.38rem, 4.4vw, 1.96rem) !important;
    --page-body-size: 0.88rem !important;
    --page-section-gap: 0.92rem !important;
  }

  .about-mobile-tight .type-title {
    line-height: 1.1 !important;
    max-width: none !important;
    text-wrap: wrap !important;
  }

  .about-mobile-tight .type-body {
    font-size: 0.9rem !important;
    line-height: 1.58 !important;
  }

  .about-mobile-tight .founder-quote {
    font-size: 0.86rem !important;
    line-height: 1.58 !important;
    max-width: none !important;
  }

  .founder-photo-image {
    object-position: 62% 36% !important;
  }
`;

const beforeTrackAttributes = {
  "/": {
    compactStart: "top 82%",
    compactBeatStart: "top 72%"
  },
  "/about": {
    start: "top 88%",
    end: "top 38%",
    scrub: "0.58",
    progressStart: "top 86%",
    progressEnd: "bottom 14%"
  },
  "/dashboard": {
    compactStart: "top 82%",
    compactBeatStart: "top 72%"
  }
};

function readPng(filePath) {
  return PNG.sync.read(fs.readFileSync(filePath));
}

function writePng(filePath, png) {
  fs.writeFileSync(filePath, PNG.sync.write(png));
}

async function waitForSettled(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1500);
}

async function captureStateWithRetry(state, mode, retries = 2) {
  let lastError = null;
  for (let attempt = 1; attempt <= retries + 1; attempt += 1) {
    try {
      return await captureState(state, mode);
    } catch (error) {
      lastError = error;
      if (attempt > retries) {
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 450));
    }
  }
  throw lastError;
}

async function captureState(state, mode) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: state.viewport });
  const page = await context.newPage();

  try {
    await page.goto(`${baseUrl}${state.page}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await waitForSettled(page);

    if (mode === "before") {
      const attrs = beforeTrackAttributes[state.page] ?? null;
      await page.evaluate(
        ({ css, attrsConfig }) => {
          const existing = document.querySelector("style[data-refinement-baseline='true']");
          if (!existing) {
            const style = document.createElement("style");
            style.setAttribute("data-refinement-baseline", "true");
            style.textContent = css;
            document.head.appendChild(style);
          }

          if (!attrsConfig) {
            return;
          }

          if (attrsConfig.compactStart) {
            document.querySelectorAll("[data-story-track='true']").forEach((node) => {
              node.setAttribute("data-story-compact-start", attrsConfig.compactStart);
              node.setAttribute("data-story-compact-beat-start", attrsConfig.compactBeatStart);
            });
          }

          if (attrsConfig.start) {
            document.querySelectorAll("[data-story-track='true']").forEach((node) => {
              node.setAttribute("data-story-start", attrsConfig.start);
              node.setAttribute("data-story-end", attrsConfig.end);
              node.setAttribute("data-story-scrub", attrsConfig.scrub);
              node.setAttribute("data-story-progress-start", attrsConfig.progressStart);
              node.setAttribute("data-story-progress-end", attrsConfig.progressEnd);
            });
          }
        },
        { css: beforeCSS, attrsConfig: attrs }
      );
      await page.waitForTimeout(350);
    }

    await page.mouse.move(Math.floor(state.viewport.width * 0.62), Math.floor(state.viewport.height * 0.32));
    await page.waitForTimeout(250);

    const outPath = path.join(mode === "before" ? beforeDir : afterDir, `${state.key}.png`);
    await page.screenshot({ path: outPath, fullPage: false, animations: "disabled" });
    return outPath;
  } finally {
    await context.close();
    await browser.close();
  }
}

async function run() {
  const report = [];

  for (const state of states) {
    try {
      console.log(`Capturing ${state.key} baseline and current...`);
      const beforePath = await captureStateWithRetry(state, "before");
      const afterPath = await captureStateWithRetry(state, "after");

      const beforePng = readPng(beforePath);
      const afterPng = readPng(afterPath);
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
        before: path.relative(root, beforePath).replaceAll("\\", "/"),
        after: path.relative(root, afterPath).replaceAll("\\", "/"),
        diff: path.relative(root, diffPath).replaceAll("\\", "/"),
        mismatchPixels,
        mismatchPercent
      });
    } catch (error) {
      report.push({
        state: state.key,
        page: state.page,
        viewport: state.viewport,
        error: error instanceof Error ? error.message : String(error)
      });
      console.error(`Failed for ${state.key}:`, error);
    }
  }

  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`Wrote focused refinement report: ${reportPath}`);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
