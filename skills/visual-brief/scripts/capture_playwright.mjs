#!/usr/bin/env node
// Capture one explicit browser element. This script deliberately has no click,
// form-fill, download, upload, or submit capability.

import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDir, "../..");

function parseArgs(argv) {
  const values = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new Error(`Unexpected argument: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for ${token}`);
    }
    values.set(token, value);
    index += 1;
  }
  for (const key of ["--url", "--selector", "--output"]) {
    if (!values.has(key)) {
      throw new Error(`Required option missing: ${key}`);
    }
  }
  return values;
}

function isWithin(parent, candidate) {
  const relative = path.relative(parent, candidate);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const url = new URL(args.get("--url"));
  if (!/^https?:$/.test(url.protocol)) {
    throw new Error("--url must use http or https");
  }
  const output = path.resolve(args.get("--output"));
  if (path.extname(output).toLowerCase() !== ".png") {
    throw new Error("Playwright capture output must be .png; use annotate_image.py for final WebP");
  }
  const storageState = args.get("--storage-state");
  if (storageState) {
    if (!path.isAbsolute(storageState)) {
      throw new Error("--storage-state must be an absolute path outside this repository");
    }
    const resolvedState = path.resolve(storageState);
    if (isWithin(repositoryRoot, resolvedState)) {
      throw new Error("--storage-state must live outside this repository because it is credential material");
    }
  }

  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch (error) {
    throw new Error("Playwright is not installed. Run npm install before using authenticated capture.", { cause: error });
  }

  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext(storageState ? { storageState } : {});
    const page = await context.newPage();
    await page.goto(url.toString(), { waitUntil: "domcontentloaded" });
    if (args.get("--wait-for")) {
      await page.locator(args.get("--wait-for")).waitFor({ state: "visible" });
    }
    const locator = page.locator(args.get("--selector"));
    if (await locator.count() !== 1) {
      throw new Error("--selector must resolve to exactly one visible capture target");
    }
    await locator.waitFor({ state: "visible" });
    await locator.screenshot({ path: output });
    await context.close();
  } finally {
    await browser.close();
  }
  // Do not log the URL or storage-state path; either can contain sensitive context.
  console.log(JSON.stringify({ captured: true, outputFormat: "png" }));
}

main().catch((error) => {
  console.error(`capture_playwright: ${error.message}`);
  process.exitCode = 2;
});
