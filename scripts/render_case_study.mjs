#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { chromium } from "playwright";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const input = resolve(root, "site/case-study/index.html");
const englishInput = resolve(root, "site/case-study/en.html");
const temporaryOutput = resolve(root, ".tmp-case-study-renders");

await mkdir(temporaryOutput, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1600, height: 1200 },
  deviceScaleFactor: 1,
});

await page.emulateMedia({ reducedMotion: "reduce" });
await page.goto(pathToFileURL(input).href, { waitUntil: "networkidle" });
await page.locator("#download-capture").screenshot({
  path: resolve(temporaryOutput, "05-employee-portal-download.png"),
});
await page.locator("#guide-preview").screenshot({
  path: resolve(temporaryOutput, "06-employee-guide-preview.png"),
});
await page.locator("#success-capture").screenshot({
  path: resolve(temporaryOutput, "07-device-check-complete.png"),
});
await page.goto(pathToFileURL(englishInput).href, { waitUntil: "networkidle" });
await page.locator("#guide-social-card-en").screenshot({
  path: resolve(temporaryOutput, "08-employee-guide-preview-en.png"),
});

await browser.close();

const conversion = spawnSync(process.env.PYTHON ?? "python3", [resolve(root, "scripts/convert_case_study_assets.py")], {
  cwd: root,
  stdio: "inherit",
});

if (conversion.status !== 0) {
  process.exit(conversion.status ?? 1);
}
