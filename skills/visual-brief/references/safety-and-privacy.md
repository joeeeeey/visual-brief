# Safety And Privacy

## Local And Draft By Default

The skill can create local Markdown, WebP assets, HTML previews, Block Kit JSON,
and channel-copy drafts. A request to prepare, package, or write material does
not authorize upload, send, post, public-repository creation, or form
submission.

## Identity And Authentication Material

- Treat persistent browser state, cookies, sessions, authorization headers,
  tokens, private keys, and signed download links as credentials.
- Store state outside the repository, for example
  `$HOME/.visual-brief/browser-state/`; do not copy it into a package, manifest,
  screenshot, or commit.
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

## Truthfulness

Use an image to answer what a reader needs to see now, not to imply an
unobserved outcome. Label generated or manually drawn visuals as `illustrative`.
For an unverified statement, write the limitation or open question.
