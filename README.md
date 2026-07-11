# Visual Brief

> Turn deep context into a brief someone can inspect.

Visual Brief is an evidence-first skill for AI agents. It helps turn source-backed
research, decisive screenshots, annotated UI states, diagrams, and reader-aware
writing into a reviewable package.

It is built around one simple idea:

> A screenshot reduces the effort to inspect a claim. A canonical link preserves
> the ability to verify or challenge it. Neither replaces the other.

![A Visual Brief makes a context gap visible](https://joeeeeey.github.io/visual-brief/assets/01-context-gap.webp)

## Install

Install the lightweight skill for every supported agent in the current project:

```bash
npx skills add joeeeeey/visual-brief --skill visual-brief --agent '*' --yes
```

Or target one agent:

```bash
npx skills add joeeeeey/visual-brief --skill visual-brief --agent codex --yes
npx skills add joeeeeey/visual-brief --skill visual-brief --agent claude-code --yes
npx skills add joeeeeey/visual-brief --skill visual-brief --agent cursor --yes
```

`npx skills` installs only [`skills/visual-brief`](skills/visual-brief), not the
site, README images, examples, or evaluation workspace. Use `--global` only when
you intentionally want a user-level installation.

## Why It Exists

AI collaborators rarely start with the same context. One person has spent an
hour reading documents and product screens; another gets a conclusion and a
link dump. The bottleneck is not always research. It is turning research into
something a reader can understand and check without replaying the whole
investigation.

Visual Brief packages the smallest useful evidence, the source behind it, and a
narrative arranged for the next reader action.

![A claim, a decisive visual, and a source have different jobs](https://joeeeeey.github.io/visual-brief/assets/02-claim-visual-source.webp)

## Three Modes

| Mode | Use it for | Reader sequence |
| --- | --- | --- |
| `evidence-reply` | A stakeholder answer, Slack reply, or decision record | conclusion -> decisive proof -> source -> boundary |
| `visual-procedure` | A screenshot-led operating guide | action -> adjacent image -> expected state -> success check |
| `public-explainer` | A blog post, V2EX post, X thread, newsletter, or tutorial draft | thesis -> explanation/evidence -> sources and limits -> channel drafts |

![The three reader journeys](https://joeeeeey.github.io/visual-brief/assets/03-three-modes.webp)

## The Package Contract

Every brief is a local, reviewable directory. `source-manifest.json` is the
machine-readable anchor connecting sources, claims, assets, outputs, and the
publication state.

```text
brief/
  deliverable.md
  evidence-index.md
  source-manifest.json
  assets/01-decisive-state.webp
  packages/                  # optional local drafts
  preview/index.html         # optional local preview
```

The contract keeps factual support separate from explanatory art:

- `observed`, `documented`, and `inference` claims link to named sources.
- `illustrative` claims label diagrams, generated visuals, or rendered cards.
- A generated visual cannot be used as factual evidence.
- Every shareable image is a real WebP and must be visually inspected.

## Lightweight By Design

The installable payload stays small. Visual showcase files live on GitHub Pages;
synthetic examples and tests live at the repository root, outside the skill
directory. Persistent browser state belongs outside both the repository and a
brief package because it is credential material.

![The installable payload and public showcase stay separate](https://joeeeeey.github.io/visual-brief/assets/04-lightweight-install.webp)

## Quick Start

1. Choose a mode and create a package directory in your active project.
2. Copy [`source-manifest.json`](skills/visual-brief/templates/source-manifest.json)
   and a mode template from [`skills/visual-brief/templates`](skills/visual-brief/templates).
3. Capture the smallest readable visual region, then crop, redact, and annotate it.
4. Put each image immediately after the claim or step it supports.
5. Run the validator and inspect every WebP before sharing.

```bash
python3 -m pip install -r skills/visual-brief/requirements.txt

python3 skills/visual-brief/scripts/validate_package.py --package ./my-brief
python3 skills/visual-brief/scripts/render_preview.py --package ./my-brief
```

For reproducible browser capture, install Playwright in the project that will
run the capture helper. It is optional and is never installed by the skill:

```bash
npm install --save-dev playwright
npx playwright install chromium
```

Keep Playwright storage state outside the repository, for example
`$HOME/.visual-brief/browser-state/project.json`. Never commit cookies, tokens,
authorization headers, profiles, customer data, or user-specific installers.

## Safety Model

Visual Brief is draft-first. It can create local Markdown, WebP assets, HTML
previews, Slack Block Kit JSON, Notion-ready Markdown, and social drafts. It
does not upload, send, post, submit, or create repositories by itself.

Before an external action, show the exact destination and material, validate the
package, inspect the images, and obtain explicit approval in the current
conversation.

## Examples And Evaluation

- [`examples/`](examples) contains synthetic, privacy-safe packages for all
  three modes. They are teaching fixtures, not evidence about a real system.
- [`evals/`](evals) contains public prompts and fixtures for focused skill
  evaluation.
- [`skills/visual-brief/references`](skills/visual-brief/references) contains
  the source, claim, capture, privacy, and destination rules used by the skill.

Run the deterministic checks with Python 3 and Pillow:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Showcase

Visit the public visual introduction at
[joeeeeey.github.io/visual-brief](https://joeeeeey.github.io/visual-brief/).

For a Chinese introduction, see [README.zh-CN.md](README.zh-CN.md). Draft
sharing material for V2EX and X lives in [`docs/`](docs).

## License

[MIT](LICENSE)
