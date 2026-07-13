# Focused Evaluation Notes

The public skill cases live in `skill-evals/evals.json` with small synthetic
fixtures beside them. They exercise the three reader experiences plus request
resolution and the one-release-cycle legacy profile:

1. an evidence reply with a narrow factual claim and a claim boundary;
2. a visual procedure with adjacent images, a safety stop, and a visible
   completion state;
3. a public explainer that distinguishes source-backed evidence from an
   illustrative visual and stays draft-only.
4. an unspecified destination that defaults to a local HTML preview;
5. explicit channel inference without redundant questions;
6. authenticated access that asks only for the missing access decision; and
7. explicit legacy-name evidence and guide requests routed through
   `visual-brief`.

The deterministic regression tests live in [`../tests/`](../tests/). Keep
broader benchmark work, private review output, browser state, and any real
system evidence outside this public repository.

All fixtures must remain synthetic. Do not put real portal screenshots, cookies,
browser states, private URLs, or customer data into an evaluation.
