# Artifact Contract

A Visual Brief is a portable, reviewable directory, not a chat response detached
from its sources. `source-manifest.json` is the machine-readable anchor;
Markdown is the reader entry point; WebP assets are the shareable visual layer.

## Minimum Layout

```text
<brief-slug>/
  deliverable.md
  evidence-index.md
  source-manifest.json
  assets/
    01-readable-name.webp
```

The default unspecified destination adds a local HTML preview. Other optional
outputs belong under `packages/`, `preview/`, and `exports/`:

```text
  packages/slack-block-kit.json
  packages/notion-import.md
  packages/social-drafts.md
  preview/index.html
  exports/brief.pdf
  exports/brief.png
```

Never put browser profiles, cookies, installer credentials, `.env` files,
private keys, customer data, or unreviewed raw screenshots inside a brief.
Keep temporary raw material outside the package in a controlled location.
Package scripts reject symlink roots, symlink files, and symlink path components
instead of following them during reads or writes.

## `source-manifest.json`

Start with [the template](../templates/source-manifest.json). For structural
validation, use [the JSON Schema](../templates/source-manifest.schema.json).
Version `1.1` adds a resolved `request` profile. Version `1.0` remains accepted
for existing packages.

| Field | Purpose |
| --- | --- |
| `schema_version` | `1.1` for new packages; `1.0` remains readable. |
| `request` | Resolved destinations, source access, capture, browser state, locale, and compatibility profile. |
| `title`, `mode`, `audience`, `status` | What the brief is, who it serves, and its local state. |
| `publication.approved` | `false` by default; preparation is not permission to publish. |
| `sources[]` | Canonical URLs, titles, source kind, capture time, and access assumptions. |
| `claims[]` | Statements, claim kinds, source IDs, asset IDs, and boundaries. |
| `assets[]` | Final ordered WebP files, provenance, review state, and processing record. |
| `outputs` | Relative paths to reader-facing deliverables and optional channel drafts. |

When `request.destinations` includes `local-html`, `outputs.html_preview` must
point exactly to `preview/index.html`. `slack` requires
`outputs.slack_block_kit`; `notion` requires `outputs.notion_import`; and
`v2ex`, `x`, or `blog` requires `outputs.social_drafts`. When the legacy
compatibility profile is active, `outputs.legacy_deliverable` must point to
`evidence-reply.md` or `visual-guide.md`; a legacy Notion destination also
requires `outputs.legacy_notion_import` to point to `notion-import.md`.

Valid `mode` values are `evidence-reply`, `visual-procedure`, and
`public-explainer`. Valid `status` values are `draft`, `review`, `approved`,
and `published`. Recording `approved` or `published` does not execute an
external action; it only records an action that has already happened.

## Sources

Every source needs a stable ID, named URL, kind, capture time, and access
assumptions:

```json
{
  "id": "S-1",
  "title": "Canonical source title",
  "url": "https://example.com/canonical-page",
  "kind": "canonical",
  "captured_at": "2026-07-11T10:30:00+08:00",
  "access_assumptions": ["public documentation"]
}
```

Use `canonical`, `secondary`, or `fixture`. A `fixture` exists only for offline
teaching or tests and cannot support a real decision or public factual claim.
A content hash can freeze a downloadable artifact version, but never replaces
its URL, title, or capture time.

## Claims

Claims have stable IDs and a declared evidence boundary:

```json
{
  "id": "C-1",
  "kind": "documented",
  "statement": "The source states the narrow policy outcome.",
  "source_ids": ["S-1"],
  "asset_ids": ["A-1"],
  "boundary": "This does not establish behavior in every tenant."
}
```

Valid claim kinds are `observed`, `documented`, `inference`, and
`illustrative`. The first three need at least one canonical or clearly labeled
secondary source. An `illustrative` claim may use generated art or a diagram,
but it cannot masquerade as factual support.

## Assets

Final assets are ordered WebP files under `assets/`:

```json
{
  "id": "A-1",
  "path": "assets/01-policy-language.webp",
  "kind": "screenshot",
  "role": "evidence",
  "source_ids": ["S-1"],
  "claim_ids": ["C-1"],
  "inspected": true,
  "operations": ["crop", "highlight"],
  "sha256": "sha256:optional-digest"
}
```

Valid `kind` values are `screenshot`, `diagram`, and `generated`. Valid `role`
values are `evidence`, `instruction`, and `illustration`. A `generated` asset
may only attach to an `illustrative` claim through the standard `claim_ids`
field. Do not invent replacement fields such as `illustrates_claim_ids` or
`illustrative_asset_ids`; version 1 validation deliberately does not treat them
as part of the provenance contract.

`inspected: true` means a person reviewed readability, context, and privacy. It
is not a substitute for visual inspection.

## Reading Order And Preflight

Lead `deliverable.md` with the outcome. Put each important claim or action
directly before the image that supports it. Keep detailed traceability in
`evidence-index.md` and `source-manifest.json` rather than hiding reader-facing
explanation there.

Run before handoff:

```bash
python3 scripts/validate_package.py --package <brief-directory>
```

The validator checks structure, links, and common text leaks. It does not read
image content, so every final WebP still needs a human visual review.
