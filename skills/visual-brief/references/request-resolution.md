# Request Resolution

Resolve the request from natural language. Do not require the user to provide a
configuration file or repeat information already present in the prompt.

## Resolved Fields

| Field | Allowed values | Default |
| --- | --- | --- |
| `destinations` | `local-html`, `slack`, `notion`, `linear`, `v2ex`, `x`, `blog`, `email`, `other` | `local-html` when absent |
| `source_access` | `public`, `authenticated`, `provided`, `mixed` | infer from sources |
| `capture` | `playwright`, `provided-assets`, `mixed`, `none` | `playwright` when rendered web evidence is required |
| `browser_state` | `none`, `ephemeral`, `existing-session`, `external-persistent` | `ephemeral` for public web capture |
| `locale` | BCP 47-style language tag | infer from the user and destination |
| `compatibility_profile` | `null`, `web-evidence-capture-v1` | `null` |

Record these values in the manifest `request` object. The publication object
remains the authority for draft, approval, and destination state. Keep
`publication.destination` null for a local-only preview; an explicit external
destination may be recorded while `publication.approved` remains false.

## Ask Or Continue

- Continue without asking when the destination is explicit.
- Default to a local HTML preview when no destination or external handoff intent
  is stated.
- Ask one concise question when the user intends an external handoff but the
  channel changes the deliverable and cannot be inferred.
- Ask for user-assisted login when an authenticated page has no usable signed-in
  session. Never ask for cookies, tokens, passwords, or storage-state contents.
- Ask before persisting browser state. Reuse an existing external state only when
  the user selected it or the active environment already provides it.
- Ask again immediately before an upload, send, post, or final submission. A
  destination choice is not publication approval.

## Research And Capture

Discovery and visual capture are separate decisions. Search, fetch, API, CLI, or
provided files may establish facts. Use Playwright when a reader needs the
rendered source wording, UI control, or workflow state. Do not open a browser
only to reproduce structured data already obtained from a more reliable source.
