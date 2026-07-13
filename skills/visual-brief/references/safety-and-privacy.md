# Safety And Privacy

## Local And Draft By Default

The skill can create local Markdown, WebP assets, HTML previews, Block Kit JSON,
and channel-copy drafts. A request to prepare, package, or write material does
not authorize upload, send, post, public-repository creation, or form
submission.

## Identity And Authentication Material

- Treat persistent browser state, cookies, sessions, authorization headers,
  tokens, private keys, URL userinfo, and signed download links as credentials.
- Store state outside the repository, for example
  `$HOME/.visual-brief/browser-state/`; do not copy it into a package, manifest,
  screenshot, or commit.
- Prefer an ephemeral context or an existing signed-in session. Ask before
  persisting state for reuse, and never ask a user to paste credential contents.
- Keep persistent state in a real external directory, never a symlink or any Git
  worktree. The capture helper loads validated JSON into memory so Playwright
  does not receive or report the credential path.
- Do not bypass login, MFA, paywalls, warning pages, permission prompts, or
  organization controls.

## Screenshot Risk

Before capture, reduce the visible browser area. Review notifications, address
bars, sidebars, tabs, profiles, URL queries, QR codes, device identifiers,
payment values, customer data, and internal project names. Crop whenever
possible; use irreversible redaction when context must remain visible.

## Text Risk

Run `validate_package.py` before handoff, but do not treat it as DLP. It scans
common token, authorization, cookie, and local-URL patterns only. In a sensitive
environment, add approved organization DLP, OCR checks, and human review.

## Local Export Risk

Treat HTML preview input as untrusted even when it is local. The bundled exporter
accepts only the renderer-marked `preview/index.html`, disables JavaScript,
blocks network access, restricts file loads to the package, rejects symlink
paths and encoded local-path ambiguity, confines generated files to their output
partitions, and commits exports plus manifest as one rollback-capable update. A
failed export must not be treated as a partial success.

## Truthfulness

Use an image to answer what a reader needs to see now, not to imply an
unobserved outcome. Label generated or manually drawn visuals as `illustrative`.
For an unverified statement, write the limitation or open question.
