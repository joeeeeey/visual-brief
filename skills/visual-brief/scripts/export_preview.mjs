#!/usr/bin/env node
// Export an existing local HTML preview to PDF and PNG without external access.

import { link, lstat, mkdir, mkdtemp, readFile, realpath, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

function parseArgs(argv) {
  const values = new Map();
  const valueOptions = new Set(["--package", "--pdf", "--image"]);
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new Error("Unexpected argument: " + token);
    }
    if (values.has(token)) {
      throw new Error("Duplicate option: " + token);
    }
    if (token === "--force") {
      values.set(token, true);
      continue;
    }
    if (!valueOptions.has(token)) {
      throw new Error("Unknown option: " + token);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error("Missing value for " + token);
    }
    values.set(token, value);
    index += 1;
  }
  if (!values.has("--package")) {
    throw new Error("Required option missing: --package");
  }
  return values;
}

function inside(packageDir, candidate, label) {
  const relative = path.relative(packageDir, candidate);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(label + " must stay inside the package");
  }
  return relative.split(path.sep).join("/");
}

function mapPackageCandidate(packageLexical, packageDir, rawCandidate, label) {
  const lexical = path.resolve(rawCandidate);
  for (const root of [packageLexical, packageDir]) {
    const relative = path.relative(root, lexical);
    if (relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))) {
      return path.join(packageDir, relative);
    }
  }
  throw new Error(label + " must stay inside the package");
}

async function checkedPath(packageDir, candidate, label, options = {}) {
  const lexical = path.resolve(candidate);
  const relative = inside(packageDir, lexical, label);
  let current = packageDir;
  let missing = false;
  for (const part of relative.split("/").filter(Boolean)) {
    current = path.join(current, part);
    if (missing) {
      continue;
    }
    let stat;
    try {
      stat = await lstat(current);
    } catch (error) {
      if (error?.code !== "ENOENT") {
        throw error;
      }
      missing = true;
      continue;
    }
    if (stat.isSymbolicLink()) {
      throw new Error(label + " must not use symlinks");
    }
  }
  if (options.mustExist && missing) {
    throw new Error(label + " does not exist");
  }
  if (options.regularFile) {
    const stat = await lstat(lexical);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      throw new Error(label + " must be a regular file");
    }
  }
  return lexical;
}

async function ensureSafeParent(packageDir, output, label) {
  const relative = inside(packageDir, path.dirname(output), label);
  let current = packageDir;
  for (const part of relative.split("/").filter(Boolean)) {
    current = path.join(current, part);
    try {
      const stat = await lstat(current);
      if (stat.isSymbolicLink() || !stat.isDirectory()) {
        throw new Error(label + " parent must be a real directory");
      }
    } catch (error) {
      if (error?.code !== "ENOENT") {
        throw error;
      }
      await mkdir(current);
    }
  }
}

async function prepareManifest(packageDir, manifestPath, manifest) {
  await checkedPath(packageDir, manifestPath, "source manifest", {
    mustExist: true,
    regularFile: true,
  });
  const temporaryDirectory = await mkdtemp(path.join(packageDir, ".visual-brief-manifest-"));
  const temporaryPath = path.join(temporaryDirectory, "source-manifest.json");
  await writeFile(temporaryPath, JSON.stringify(manifest, null, 2) + "\n", {
    encoding: "utf8",
    flag: "wx",
  });
  return { directory: temporaryDirectory, path: temporaryPath };
}

async function existingRegularFile(output, label) {
  try {
    const stat = await lstat(output);
    if (stat.isSymbolicLink() || !stat.isFile()) {
      throw new Error(label + " must be a regular file when it already exists");
    }
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const packageLexical = path.resolve(args.get("--package"));
  const packageStat = await lstat(packageLexical);
  if (packageStat.isSymbolicLink() || !packageStat.isDirectory()) {
    throw new Error("package must be a real directory, not a symlink");
  }
  const packageDir = await realpath(packageLexical);
  const manifestPath = await checkedPath(
    packageDir,
    path.join(packageDir, "source-manifest.json"),
    "source manifest",
    { mustExist: true, regularFile: true },
  );
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  if (
    manifest.outputs !== undefined &&
    (manifest.outputs === null ||
      typeof manifest.outputs !== "object" ||
      Array.isArray(manifest.outputs))
  ) {
    throw new Error("manifest outputs must be an object");
  }
  const previewRelative = manifest.outputs?.html_preview ?? "preview/index.html";
  if (previewRelative !== "preview/index.html") {
    throw new Error("outputs.html_preview must be preview/index.html before export");
  }
  const previewPath = await checkedPath(
    packageDir,
    path.resolve(packageDir, previewRelative),
    "HTML preview",
    { mustExist: true, regularFile: true },
  );
  const previewHtml = await readFile(previewPath, "utf8");
  if (!previewHtml.includes('<meta name="visual-brief-preview" content="1.1">')) {
    throw new Error("HTML preview is missing the trusted Visual Brief renderer marker");
  }

  const pdfPath = mapPackageCandidate(
    packageLexical,
    packageDir,
    args.get("--pdf") ?? path.join(packageDir, "exports", "brief.pdf"),
    "PDF output",
  );
  const imagePath = mapPackageCandidate(
    packageLexical,
    packageDir,
    args.get("--image") ?? path.join(packageDir, "exports", "brief.png"),
    "image output",
  );
  await checkedPath(packageDir, pdfPath, "PDF output");
  await checkedPath(packageDir, imagePath, "image output");
  const pdfRelative = inside(packageDir, pdfPath, "PDF output");
  const imageRelative = inside(packageDir, imagePath, "image output");
  if (!pdfRelative.startsWith("exports/") || !imageRelative.startsWith("exports/")) {
    throw new Error("PDF and image outputs must stay under exports/");
  }
  if (path.extname(pdfPath).toLowerCase() !== ".pdf") {
    throw new Error("--pdf must end in .pdf");
  }
  if (path.extname(imagePath).toLowerCase() !== ".png") {
    throw new Error("--image must end in .png");
  }
  await ensureSafeParent(packageDir, pdfPath, "PDF output");
  await ensureSafeParent(packageDir, imagePath, "image output");
  const pdfExists = await existingRegularFile(pdfPath, "PDF output");
  const imageExists = await existingRegularFile(imagePath, "image output");
  const force = args.get("--force") === true;
  if (!force && (pdfExists || imageExists)) {
    throw new Error("preview export output already exists; use --force to replace exports");
  }

  manifest.outputs = manifest.outputs ?? {};
  manifest.outputs.pdf_export = pdfRelative;
  manifest.outputs.image_export = imageRelative;

  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch (error) {
    throw new Error("Playwright is not installed. Install it in the active project before exporting previews.", {
      cause: error,
    });
  }

  const preparedManifest = await prepareManifest(packageDir, manifestPath, manifest);

  let pdfTemporaryDirectory = null;
  let imageTemporaryDirectory = null;
  try {
    pdfTemporaryDirectory = await mkdtemp(
      path.join(path.dirname(pdfPath), ".visual-brief-pdf-"),
    );
    imageTemporaryDirectory = await mkdtemp(
      path.join(path.dirname(imagePath), ".visual-brief-image-"),
    );
    const temporaryPdf = path.join(pdfTemporaryDirectory, "brief.pdf");
    const temporaryImage = path.join(imageTemporaryDirectory, "brief.png");
    const previousPdf = path.join(pdfTemporaryDirectory, "previous.pdf");
    const previousImage = path.join(imageTemporaryDirectory, "previous.png");
    let pdfBackedUp = false;
    let imageBackedUp = false;
    let pdfCommitted = false;
    let imageCommitted = false;

    const browser = await chromium.launch({ headless: true });
    try {
      const context = await browser.newContext({
        javaScriptEnabled: false,
        viewport: { width: 1280, height: 900 },
      });
      const page = await context.newPage();
      const blockedRequests = [];
      await page.route("**/*", async (route) => {
        const requestUrl = route.request().url();
        let parsed;
        try {
          parsed = new URL(requestUrl);
        } catch {
          blockedRequests.push("invalid URL");
          await route.abort("blockedbyclient");
          return;
        }
        if (parsed.protocol !== "file:") {
          blockedRequests.push(parsed.protocol);
          await route.abort("blockedbyclient");
          return;
        }
        try {
          await checkedPath(packageDir, fileURLToPath(parsed), "preview resource", {
            mustExist: true,
            regularFile: true,
          });
        } catch {
          blockedRequests.push("unsafe file");
          await route.abort("blockedbyclient");
          return;
        }
        await route.continue();
      });
      const assertNoBlockedRequests = () => {
        if (blockedRequests.length > 0) {
          const kinds = [...new Set(blockedRequests)].join(", ");
          throw new Error(`HTML preview requested blocked external or unsafe resources (${kinds})`);
        }
      };
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page.goto(pathToFileURL(previewPath).href, { waitUntil: "load" });
      assertNoBlockedRequests();
      await page.pdf({ path: temporaryPdf, format: "A4", printBackground: true });
      assertNoBlockedRequests();
      await page.screenshot({ path: temporaryImage, fullPage: true });
      assertNoBlockedRequests();
      await context.close();
    } finally {
      await browser.close();
    }

    await checkedPath(packageDir, pdfPath, "PDF output");
    await checkedPath(packageDir, imagePath, "image output");
    try {
      if (pdfExists) {
        await rename(pdfPath, previousPdf);
        pdfBackedUp = true;
      }
      if (imageExists) {
        await rename(imagePath, previousImage);
        imageBackedUp = true;
      }
      await link(temporaryPdf, pdfPath);
      pdfCommitted = true;
      await link(temporaryImage, imagePath);
      imageCommitted = true;
      await checkedPath(packageDir, manifestPath, "source manifest", {
        mustExist: true,
        regularFile: true,
      });
      await rename(preparedManifest.path, manifestPath);
    } catch (error) {
      if (imageCommitted) {
        await rm(imagePath, { force: true });
        imageCommitted = false;
      }
      if (pdfCommitted) {
        await rm(pdfPath, { force: true });
        pdfCommitted = false;
      }
      if (imageBackedUp) {
        await rename(previousImage, imagePath);
        imageBackedUp = false;
      }
      if (pdfBackedUp) {
        await rename(previousPdf, pdfPath);
        pdfBackedUp = false;
      }
      throw error;
    }
  } finally {
    if (pdfTemporaryDirectory) {
      await rm(pdfTemporaryDirectory, { recursive: true, force: true });
    }
    if (imageTemporaryDirectory) {
      await rm(imageTemporaryDirectory, { recursive: true, force: true });
    }
    await rm(preparedManifest.directory, { recursive: true, force: true });
  }
  console.log(JSON.stringify({ exported: true, pdf: pdfRelative, image: imageRelative }));
}

main().catch((error) => {
  console.error("export_preview: " + error.message);
  process.exitCode = 2;
});
