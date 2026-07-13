#!/usr/bin/env node
// Capture one explicit browser element. This script deliberately has no click,
// form-fill, download, upload, or submit capability.

import { execFileSync } from "node:child_process";
import { lstatSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

function parseArgs(argv) {
  const values = new Map();
  const allowed = new Set(["--url", "--selector", "--output", "--storage-state", "--wait-for"]);
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new Error(`Unexpected argument: ${token}`);
    }
    if (!allowed.has(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    if (values.has(token)) {
      throw new Error(`Duplicate option: ${token}`);
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

function gitRootFor(candidate) {
  try {
    return realpathSync(execFileSync("git", ["-C", candidate, "rev-parse", "--show-toplevel"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim());
  } catch {
    let current;
    try {
      current = realpathSync(candidate);
    } catch {
      return null;
    }
    while (true) {
      try {
        lstatSync(path.join(current, ".git"));
        return current;
      } catch (error) {
        if (error?.code !== "ENOENT") {
          return current;
        }
      }
      const parent = path.dirname(current);
      if (parent === current) {
        return null;
      }
      current = parent;
    }
  }
}

function pathsOverlap(first, second) {
  return isWithin(first, second) || isWithin(second, first);
}

function loadStorageState(storageState) {
  if (!storageState) {
    return undefined;
  }
  if (!path.isAbsolute(storageState)) {
    throw new Error("--storage-state must be an absolute credential path");
  }
  const configuredRoot = process.env.VISUAL_BRIEF_BROWSER_STATE_ROOT;
  if (configuredRoot && !path.isAbsolute(configuredRoot)) {
    throw new Error("VISUAL_BRIEF_BROWSER_STATE_ROOT must be an absolute path");
  }
  const lexicalRoot = path.resolve(
    configuredRoot ?? path.join(os.homedir(), ".visual-brief", "browser-state"),
  );
  const lexicalState = path.resolve(storageState);
  if (!isWithin(lexicalRoot, lexicalState)) {
    throw new Error("--storage-state must live under the configured external browser-state root");
  }
  const activeProject = gitRootFor(process.cwd()) ?? realpathSync(process.cwd());
  if (pathsOverlap(activeProject, lexicalRoot)) {
    throw new Error("browser-state root must live outside the active project directory");
  }

  let rootStat;
  let stateStat;
  let canonicalRoot;
  let canonicalState;
  try {
    rootStat = lstatSync(lexicalRoot);
    stateStat = lstatSync(lexicalState);
    canonicalRoot = realpathSync(lexicalRoot);
    canonicalState = realpathSync(lexicalState);
  } catch {
    throw new Error("configured browser state is unavailable");
  }
  if (rootStat.isSymbolicLink() || !rootStat.isDirectory()) {
    throw new Error("browser-state root must be a real external directory");
  }
  if (stateStat.isSymbolicLink() || !stateStat.isFile()) {
    throw new Error("--storage-state must be a regular file, not a symlink");
  }
  if (!isWithin(canonicalRoot, canonicalState)) {
    throw new Error("--storage-state resolves outside the configured browser-state root");
  }

  if (pathsOverlap(activeProject, canonicalRoot)) {
    throw new Error("browser-state root must live outside the active project directory");
  }
  if (gitRootFor(path.dirname(canonicalState))) {
    throw new Error("--storage-state must not live inside any Git worktree");
  }

  try {
    const parsed = JSON.parse(readFileSync(canonicalState, "utf8"));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("invalid state object");
    }
    return parsed;
  } catch {
    throw new Error("stored browser state is not valid JSON");
  }
}

function prepareOutput(outputArgument) {
  const lexicalOutput = path.resolve(outputArgument);
  if (path.extname(lexicalOutput).toLowerCase() !== ".png") {
    throw new Error("Playwright capture output must be .png; use annotate_image.py for final WebP");
  }
  let parent;
  try {
    const parentStat = lstatSync(path.dirname(lexicalOutput));
    if (parentStat.isSymbolicLink() || !parentStat.isDirectory()) {
      throw new Error("unsafe parent");
    }
    parent = realpathSync(path.dirname(lexicalOutput));
  } catch {
    throw new Error("Playwright capture output parent must be an existing real directory");
  }
  const canonicalOutput = path.join(parent, path.basename(lexicalOutput));
  try {
    lstatSync(canonicalOutput);
  } catch (error) {
    if (error?.code === "ENOENT") {
      return canonicalOutput;
    }
    throw new Error("could not inspect Playwright capture output");
  }
  throw new Error("Playwright capture output already exists; refusing to overwrite it");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const url = new URL(args.get("--url"));
  if (!/^https?:$/.test(url.protocol)) {
    throw new Error("--url must use http or https");
  }
  const output = prepareOutput(args.get("--output"));
  const storageState = loadStorageState(args.get("--storage-state"));

  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch (error) {
    throw new Error("Playwright is not installed. Install it in the active project before browser capture.", { cause: error });
  }

  const browser = await chromium.launch({ headless: true });
  try {
    let context;
    try {
      context = await browser.newContext(storageState ? { storageState } : {});
    } catch {
      throw new Error("stored browser state is invalid or incompatible with Playwright");
    }
    const page = await context.newPage();
    try {
      await page.goto(url.toString(), { waitUntil: "domcontentloaded" });
    } catch {
      throw new Error("browser navigation failed");
    }
    if (args.get("--wait-for")) {
      await page.locator(args.get("--wait-for")).waitFor({ state: "visible" });
    }
    const locator = page.locator(args.get("--selector"));
    if (await locator.count() !== 1) {
      throw new Error("--selector must resolve to exactly one visible capture target");
    }
    await locator.waitFor({ state: "visible" });
    const screenshot = await locator.screenshot();
    try {
      writeFileSync(output, screenshot, { flag: "wx", mode: 0o600 });
    } catch {
      throw new Error("Playwright capture output could not be created safely");
    }
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
