---
name: visual-brief
description: >-
  Turn source-backed research, screenshots, annotated UI states, diagrams, or
  generated explanatory visuals into a local, reviewable visual brief for a
  stakeholder reply, screenshot-led procedure, or public technical explainer.
  Use this whenever a user needs an audience-ready package with images next to
  the claims or steps they support, a concise Slack/Notion/Linear/blog/social
  draft, visual proof, an annotated screenshot, or a publishable explainer.
  Do not use it for ordinary text-only research, a routine browser lookup, or
  a normal explanation with no requested visual deliverable.
---

# Visual Brief

Create a package another person can understand quickly and verify responsibly.
Visuals reduce the effort to inspect a claim or action. Canonical sources keep
the result auditable. Neither replaces the other.

## Resolve The Request

Infer the mode, destination, audience, source access, capture method, browser
state policy, locale, and publication state before collecting evidence. Record
the resolved values in `source-manifest.json` using
[request-resolution.md](references/request-resolution.md).

- Honor an explicit Slack, Notion, Linear, V2EX, X, blog, email, or local
  destination without asking again.
- When no destination is stated, default to `local-html` and render
  `preview/index.html` before handoff.
- Ask only when the answer materially changes execution: an external destination
  is intended but ambiguous, authenticated access is required, browser state
  may be persisted, or an external action is about to occur.
- Keep publication as a local draft until separately approved.

## Choose A Mode

Infer the audience and destination when they are clear. Ask only about a real
blocker such as target account, approval boundary, or required source.

| Need | Mode | Primary reader experience |
| --- | --- | --- |
| Explain why a decision or claim is supported | `evidence-reply` | conclusion first, then decisive proof |
| Help a person complete an interface workflow | `visual-procedure` | action, adjacent image, expected state, success check |
| Teach or publish a technical idea | `public-explainer` | clear thesis, visual explanation, explicit provenance |

If the request only needs a text answer or ordinary citations, do not invoke
this skill. If it needs both a policy decision and a workflow, make a single
package with an `evidence-reply` section followed by a `visual-procedure`
section rather than duplicating the source chain.

## Work Locally First

Start a package under the active task or project directory. Use the structure
in [artifact-contract.md](references/artifact-contract.md). The required core
is:

```text
<package>/
  deliverable.md
  evidence-index.md
  source-manifest.json
  assets/01-meaningful-name.webp
```

The manifest is the source of truth for sources, claims, assets, output files,
and publication state. Use the template in
[templates/source-manifest.json](templates/source-manifest.json). Keep the
human-facing `deliverable.md` concise; put detailed traceability in
`evidence-index.md` and the manifest.

## Source And Claim Discipline

For every meaningful statement, record the narrowest support available:

- `observed`: a visible state in a product or source at a stated time;
- `documented`: wording from a canonical policy, documentation page, or system
  of record;
- `inference`: a reasoned conclusion that names its support and limitation;
- `illustrative`: a teaching aid, generated image, or diagram that proves
  nothing by itself.

Facts and inferences need one or more canonical source IDs. A screenshot may
make evidence easier to inspect but does not make an unsupported claim true.
Generated visuals, diagrams, and rendered cards are useful for explanation;
give every generated asset an explicit `illustrative` claim ID in its
`claim_ids`, and do not cite it as factual proof. Read
[evidence-and-claim-rules.md](references/evidence-and-claim-rules.md) when the
claim boundary is not obvious.

## Capture And Annotate

Use search, fetch, a structured API, or a CLI to discover and verify facts when
that is more reliable than browser automation. When the deliverable needs a
rendered web source, control, or workflow state, use Playwright to capture the
smallest decisive region. Prefer first-party sources and label secondary sources
as such.

Use an ephemeral Playwright context for public pages. For authenticated capture,
prefer an existing signed-in session or user-assisted login. Persist browser
state only when reuse is needed and approved; keep it outside the repository,
for example `~/.visual-brief/browser-state/<project>.json`. Treat that state as
a credential. Never copy it into the package or source control. Do not bypass
login, MFA, paid access, warning pages, or permissions. See
[capture-and-annotation.md](references/capture-and-annotation.md).

Install the image-processing dependency with `python3 -m pip install -r
requirements.txt` from this skill directory. The optional Playwright capture
helper expects Playwright to be installed in the project that runs it; do not
assume a skill installer provides browser binaries or credentials.

Capture the smallest readable region that retains enough source or product
context to be understood. Avoid browser chrome, full-page screenshots,
unrelated sidebars, whitespace, other tabs, and private account details. Name
assets in their reading order: `01-source-policy.webp`,
`02-confirmed-setting.webp`.

Use the bundled script for cropping, highlighting, irreversible redaction, and
real WebP encoding:

```bash
python3 scripts/annotate_image.py \
  --input raw.png \
  --output assets/01-decisive-state.webp \
  --crop 80,120,1200,620 \
  --highlight 210,260,720,95 \
  --label "What this proves"
```

Open every output image before sharing. Check legibility at normal size,
sufficient context, absence of sensitive data, and agreement between the image,
caption, source, and claim. A successful conversion command is not enough.

## Build The Reader Narrative

Lead with the outcome. Minimize setup prose. Put each image immediately after
the sentence or step it supports. State only what the sources support and make
uncertainty visible.

### Evidence Reply

Use [evidence-reply.md](templates/evidence-reply.md). Include a one- or
two-sentence answer, the smallest set of decisive claims, named canonical links,
and any limitation that could change the decision. Prepare a Slack Block Kit
draft only if requested; it remains local until explicitly approved.

### Visual Procedure

Use [visual-procedure.md](templates/visual-procedure.md). Each step needs an
action, an adjacent image when it removes ambiguity, an expected visible state,
and a stop point before a destructive, paid, permission-granting, or final
submission action. Finish with a visible success condition, not merely the last
click. State role, region, tenant, feature-flag, and timing dependencies.

### Public Explainer

Use [public-explainer.md](templates/public-explainer.md). Distinguish evidence
screenshots from diagrams or generated assets in captions. Draft channel-specific
copy in `packages/social-drafts.md`; do not post it. Keep source links and
claim boundaries in the long-form artifact even when a short channel cannot
carry all of them.

## Legacy Compatibility

When invoked through the deprecated `web-evidence-capture` shim, set
`request.compatibility_profile` to `web-evidence-capture-v1`, use
`artifacts/web-evidence/<topic-slug>/`, map Evidence pack to `evidence-reply`
and Visual web guide to `visual-procedure`, then run
`scripts/export_legacy_web_evidence.py`. Read
[legacy-web-evidence-capture.md](references/legacy-web-evidence-capture.md).
Do not maintain a second capture implementation in the shim.

## Package And Check

Use the destination rules in
[destination-packaging.md](references/destination-packaging.md). When
`local-html` is selected or inferred, render the local HTML preview before
validation and handoff:

```bash
python3 scripts/render_preview.py --package <package>
```

When the user requests a portable local export, convert that preview without
publishing it. The exporter accepts only the renderer-marked local preview,
disables JavaScript, blocks network requests, and rejects symlink or package-
external resources. It writes only under `exports/` and preserves existing
exports unless `--force` is explicitly supplied:

```bash
node scripts/export_preview.mjs --package <package>
```

Run the structural and safety preflight before handing the package over:

```bash
python3 scripts/validate_package.py --package <package>
```

The validator catches broken package links, invalid WebP assets, missing source
relations, unsafe URL patterns, and common secret-like strings in text. It
cannot prove an image lacks sensitive data; a human visual review remains
required.

## Publishing Gate

The default publication state is `draft` and `publication.approved: false`.
Creating a draft, preview, HTML file, social copy, or local Block Kit payload
does not authorize an external side effect. Before any upload, send, post,
public-repository creation, or final submission:

1. show the intended destination and exact material;
2. verify the package and inspect all images;
3. obtain explicit approval in the current conversation;
4. record the approval or leave the package as a draft.

Never infer approval from a request to prepare, format, preview, package, or
write a draft. Read [safety-and-privacy.md](references/safety-and-privacy.md)
for the full boundary.

## Final Handoff

State the package path, mode, source coverage, image inspection result, and
whether it is only a draft. Mention any source freshness, access, or inference
boundary that a reviewer needs before acting. Do not claim publication occurred
unless it was explicitly approved and actually completed.
