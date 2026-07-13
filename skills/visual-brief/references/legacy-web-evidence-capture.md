# Legacy Web Evidence Capture Profile

Use this profile only when the request came through the deprecated
`web-evidence-capture` shim or explicitly requires its version 1 output names.
The shim preserves the old name and trigger boundary for one release cycle; all
research, capture, annotation, packaging, validation, and safety behavior comes
from `visual-brief`.

The compatibility window is the `visual-brief` `0.2.x` release cycle. Remove the
installed shim at `0.3.0` only after explicit old-name usage has been reviewed
and no extension is approved. The public repository still exposes only the
`visual-brief` Skill; an operator installs the shim template beside it only for
an existing environment that needs the deprecated name.

## Mode Mapping

| Legacy need | Visual Brief mode | Legacy reader file |
| --- | --- | --- |
| Evidence pack | `evidence-reply` | `evidence-reply.md` |
| Visual web guide | `visual-procedure` | `visual-guide.md` |

Create the package under `artifacts/web-evidence/<topic-slug>/`. Keep the normal
Visual Brief files and assets; the compatibility files are additive:

```text
artifacts/web-evidence/<topic-slug>/
  deliverable.md
  evidence-index.md
  source-manifest.json
  evidence-reply.md        # evidence-reply mode
  visual-guide.md          # visual-procedure mode
  notion-import.md         # when a Notion draft exists
  assets/
  preview/index.html       # when local-html is selected
```

Set `request.compatibility_profile` to `web-evidence-capture-v1`, then run:

```bash
python3 scripts/export_legacy_web_evidence.py --package <package>
```

The exporter copies the current reader deliverable to the old filename and
records the compatibility outputs in the manifest. A Notion destination must
already declare a real `outputs.notion_import`; the exporter then creates the
additive root-level `notion-import.md`. It does not upload, send, publish, or
maintain a second source of truth.
