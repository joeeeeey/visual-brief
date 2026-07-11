# Evidence, Claims, And Boundaries

## Start With The Smallest Supportable Sentence

Break a broad statement such as "this approach is impossible" into a checkable
fact such as "at the capture time, the official documentation's listed regions
do not include the target region." The first is a conclusion; the second is a
source-backed observation. Only call the first an `inference` when its premises
and limits are explicit.

| Claim kind | What it can say | Required support | Common mistake |
| --- | --- | --- | --- |
| `observed` | A page showed a state at a time | capture time, source link, compact screenshot | Generalizing one account state to every account |
| `documented` | A policy or document explicitly says something | canonical URL and exact wording | Treating documentation as verified runtime behavior |
| `inference` | A reasoned conclusion from named support | sources, premises, and boundary | Writing a deduction as an established fact |
| `illustrative` | A model or example that helps explain | clear label and separate factual links | Making generated art look like evidence |

## Prefer A Source Hierarchy

Usually prefer: system record or official API -> first-party product page or
documentation -> formal announcement -> dated, attributed secondary analysis.
Secondary material can help discover a lead, but it does not replace a
first-party source that should exist.

Record account, tenant, region, browser, feature flag, subscription, and timing
dependencies in `access_assumptions` and `boundary`. A page behind a paywall or
an unavailable account must not be assumed reproducible for every reader.

## Use A Visual To Assist, Not Replace, A Source

- Show the sentence, field, control, or completion state a reader needs to see.
- Put a named canonical link near the visual; do not dump raw URLs into prose.
- Retain the smallest context needed to identify the source or product state.
- For charts, name filters, time range, units, and anything excluded.

## Generated And Rendered Visuals

Generated images, rendered HTML cards, drawings, Mermaid, and flow diagrams can
teach well. Label them "illustrative" or "explanatory diagram" and declare them
as `generated` or `diagram` in the manifest. Attach them only to illustrative
claims. When a diagram states a fact, place the original source next to the
diagram rather than making the diagram bear the burden of proof.

## Incomplete Or Conflicting Evidence

Do not fill unknown gaps just to make a narrative smooth. Use language such as:

- "The source establishes X; it does not establish Y."
- "This observation is from tenant A; applicability to tenant B is unverified."
- "The two sources have different update dates; this brief does not resolve the conflict."

When an important conclusion lacks support, stop at "needs verification". A
screenshot does not conceal an evidence gap.
