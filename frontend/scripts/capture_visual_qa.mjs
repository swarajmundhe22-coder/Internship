import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";
import { PNG } from "pngjs";
import pixelmatch from "pixelmatch";

const root = process.cwd();
const outRoot = path.join(root, "artifacts", "visual_qa");
const beforeDir = path.join(outRoot, "before");
const afterDir = path.join(outRoot, "after");
const diffDir = path.join(outRoot, "diff");
const baseUrl = process.env.BASE_URL ?? "http://127.0.0.1:3000";

for (const dir of [beforeDir, afterDir, diffDir]) {
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

const beforeCSS = `
  .page-polish-home { padding-left: 1.5rem !important; padding-right: 1.5rem !important; padding-bottom: 5rem !important; padding-top: 2rem !important; }
  .page-polish-home .story-track { margin-top: 2rem !important; }
  .page-polish-home .story-track + section { margin-top: 1.5rem !important; gap: 1.25rem !important; }
`;

const beforeTrackAttributes = {
  "/": {
    compactStart: "top 82%",
    compactBeatStart: "top 72%"
  },
  "/dashboard": {
    compactStart: "top 82%",
    compactBeatStart: "top 72%"
  },
  "/simulations": {
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

async function withTimeout(promiseFactory, label, timeoutMs = 90000) {
  let timeoutId;
  const timeoutPromise = new Promise((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new Error(`Timeout while ${label}`));
    }, timeoutMs);
  });

  try {
    return await Promise.race([promiseFactory(), timeoutPromise]);
  } finally {
    clearTimeout(timeoutId);
  }
}

async function waitForSettled(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1400);
}

async function captureState(state, mode) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: state.viewport });
  const page = await context.newPage();

  try {
    await withTimeout(
      async () => {
        await page.goto(`${baseUrl}${state.page}`, { waitUntil: "domcontentloaded", timeout: 60000 });
        await waitForSettled(page);
      },
      `opening ${state.key} (${mode})`
    );

    if (mode === "before") {
      const attrs = beforeTrackAttributes[state.page] ?? null;
      await page.evaluate(
        ({ css, attrsConfig }) => {
          const existing = document.querySelector("style[data-qa-baseline='true']");
          if (!existing) {
            const style = document.createElement("style");
            style.setAttribute("data-qa-baseline", "true");
            style.textContent = css;
            document.head.appendChild(style);
          }

          if (attrsConfig) {
            document.querySelectorAll("[data-story-track='true']").forEach((node) => {
              node.setAttribute("data-story-compact-start", attrsConfig.compactStart);
              node.setAttribute("data-story-compact-beat-start", attrsConfig.compactBeatStart);
            });
          }
        },
        { css: beforeCSS, attrsConfig: attrs }
      );
      await page.waitForTimeout(300);
    }

    if (state.page === "/") {
      await page.mouse.move(Math.floor(state.viewport.width * 0.72), Math.floor(state.viewport.height * 0.24));
    } else {
      await page.mouse.move(Math.floor(state.viewport.width * 0.5), Math.floor(state.viewport.height * 0.35));
    }

    await page.waitForTimeout(250);

    const filePath = path.join(mode === "before" ? beforeDir : afterDir, `${state.key}.png`);
    await withTimeout(
      async () => {
        await page.screenshot({ path: filePath, fullPage: false, animations: "disabled" });
      },
      `capturing screenshot ${state.key} (${mode})`
    );
    return filePath;
  } finally {
    await context.close();
    await browser.close();
  }
}

async function run() {
  const report = [];

  for (const state of states) {
    console.log(`Capturing ${state.key}...`);
    const beforePath = await captureState(state, "before");
    const afterPath = await captureState(state, "after");

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
  }

  const reportPath = path.join(outRoot, "report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`Wrote visual QA report: ${reportPath}`);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
