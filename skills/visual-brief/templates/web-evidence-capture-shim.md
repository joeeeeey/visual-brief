---
name: web-evidence-capture
description: >-
  Deprecated compatibility alias for visual-brief. Use only when the user
  explicitly invokes web-evidence-capture or $web-evidence-capture. Route a
  legacy Evidence pack to evidence-reply and a legacy Visual web guide to
  visual-procedure. Use visual-brief directly for every other visual request.
---

# Web Evidence Capture Compatibility Shim

This one-release-cycle shim contains no research, capture, image-processing,
packaging, or publishing implementation.

Compatibility window: `visual-brief` `0.2.x`. Review explicit old-name usage
before removing this shim at `0.3.0`.

1. Read the adjacent [visual-brief Skill](../visual-brief/SKILL.md) completely.
2. If it is missing, stop with an actionable dependency error. Do not recreate
   the removed legacy workflow.
3. Read the legacy profile at
   `../visual-brief/references/legacy-web-evidence-capture.md`.
4. If the user asks the legacy name for a public explainer, stop before creating
   files and ask them to invoke `visual-brief`; the v1 alias only covers Evidence
   pack and Visual web guide behavior.
5. Map Evidence pack to `evidence-reply` and Visual web guide to
   `visual-procedure`. If both are requested, choose the mode from the reader's
   first action and include the other section in the same package.
6. Set `request.compatibility_profile` to `web-evidence-capture-v1` and create
   the package under `artifacts/web-evidence/<topic-slug>/`.
7. Follow the current Visual Brief source, claim, capture, privacy, validation,
   local-preview, and publishing contracts without weakening them.
8. From this shim directory, run the sibling exporter before validation:

   ```bash
   python3 ../visual-brief/scripts/export_legacy_web_evidence.py --package <package>
   ```

   This creates the additive legacy reader filename without depending on the
   caller's current working directory.
9. State in the handoff that the deprecated alias was used and that
   `visual-brief` is the replacement.
