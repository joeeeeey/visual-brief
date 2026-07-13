# Capture, Annotation, And Visual Review

## Playwright Capture

Use Playwright for rendered web evidence and workflow states, not as a mandatory
replacement for search, fetch, APIs, CLIs, or provided files during research.
Use an ephemeral context for public pages.

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

The helper reads and parses `--storage-state` into memory before Playwright is
started. It rejects state in any Git worktree, state outside
`$HOME/.visual-brief/browser-state/`, symlinked state or credential roots, and a
credential root that overlaps the active project. Set
`VISUAL_BRIEF_BROWSER_STATE_ROOT` only to an absolute, intentionally managed
external credential directory. The current working directory is the project
boundary when it is not inside a Git worktree. Capture output is created once
and never follows or overwrites an existing file or symlink. Install Playwright
and its browser in the project that runs this command. Do not commit
`node_modules`, browser profiles, or downloaded authentication files.

For authenticated pages, prefer an existing signed-in session or user-assisted
login. Ask before persisting reusable state, never ask the user to paste cookies
or tokens, and keep any saved state outside the repository with credential-level
permissions. MFA, consent, warning, payment, and permission prompts remain user
or approval boundaries.

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
