# Destination Packaging

## Local HTML Preview

- Use `local-html` when no destination is stated and no external handoff is
  clearly intended.
- Render `preview/index.html` from `deliverable.md` and the manifest before
  handoff. Keep Markdown and the manifest as the editable and auditable sources.
- A local HTML preview may later be exported to PDF or an image. Exporting a
  local file with `scripts/export_preview.mjs` does not authorize
  upload or publication.
- Preview images must be local package files. Export disables JavaScript, blocks
  every non-`file:` request, allows only package-contained files, and fails if a
  remote or unsafe resource is requested.
- The renderer writes only `preview/index.html`. PDF and PNG export paths must
  remain under `exports/`; existing exports are preserved unless the caller uses
  the explicit `--force` option. Slack JSON stays under `packages/`.
- Give the user the local preview path and state that it is a draft.

## Slack Or Email Reply

- Start with one or two sentences that answer the reader's question.
- Attach only the few visuals that can change the decision, in reader order.
- Pair each important claim with a named source link; keep the full evidence
  index as optional depth.
- Generate Block Kit only as local JSON. Do not fabricate image URLs when no
  approved public asset URL exists.

## Notion Or Linear Procedure

- State the role, starting condition, and visible completion result first.
- Put every action next to its screenshot, expected state, and safety stop.
- Before a permission, payment, deletion, upload, installation, irreversible
  change, or final submission, state exactly where the reader must stop for
  approval.
- Do not imply that different tenants, roles, regions, or feature flags have an
  identical UI.

## Public Explainer

- Retain named canonical links, source times, and boundaries in the long-form
  article. Short posts should link back to it.
- Draft channel-specific text for X, V2EX, blogs, newsletters, or other
  destinations rather than posting automatically.
- Caption real product/source screenshots separately from diagrams, generated
  art, or rendered cards.
- Review trademark, copyright, customer data, screenshot authorization, visible
  accounts, and platform terms before publishing.

## Before Any External Action

Preparing or previewing does not authorize upload or send. Show the exact
destination, final copy, and files; complete validation and image review; then
obtain explicit approval in the current conversation before an external side
effect occurs.
