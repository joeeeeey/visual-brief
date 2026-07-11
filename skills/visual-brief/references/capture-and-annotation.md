# Capture, Annotation, And Visual Review

## Playwright Capture

Prefer a stable selector for one useful content region over a full-page
screenshot. The bundled helper accepts only element screenshots so browser
chrome, other tabs, and unrelated page areas are less likely to enter the
deliverable.

```bash
node scripts/capture_playwright.mjs \
  --url "https://example.com/page" \
  --selector "main .policy-result" \
  --output /secure-temp/source-state.png \
  --storage-state "$HOME/.visual-brief/browser-state/example.json"
```

The helper only reads `--storage-state`; it will reject state stored inside the
repository. Install Playwright and its browser in the project that runs this
command. Do not commit `node_modules`, browser profiles, or downloaded
authentication files.

## Crop, Highlight, And Redact

Use the final asset helper for a real WebP result:

```bash
python3 scripts/annotate_image.py \
  --input /secure-temp/source-state.png \
  --output <brief-directory>/assets/01-relevant-state.webp \
  --crop 80,120,1200,620 \
  --redact 900,0,180,60 \
  --highlight 210,260,720,95 \
  --label "Decisive wording"
```

Coordinates are relative to the original image. The script crops first, then
transforms highlight and redaction coordinates. Redaction is an irreversible
solid overlay. Do not treat the unredacted raw screenshot as a deliverable.
Use annotation to guide attention, never to alter or exaggerate source meaning.

## Human Quality Gate

Open every final WebP and confirm:

1. The key text, control, or value is legible at normal reading size.
2. The crop retains enough source or product context to remain interpretable.
3. No password, token, cookie, QR code, contact detail, device identifier,
   customer content, or unrelated tab is visible.
4. File name, order, caption, claim ID, source link, and manifest agree.
5. Any synthetic, rendered, or generated area is clearly labeled illustrative.

Automation can check file format and common text patterns. It cannot prove that
an image contains no sensitive material or that a claim is properly scoped.
