# Visual Brief

> Turn AI research and browser work into a visual explanation another person can actually follow.

Visual Brief is a reusable workflow package for Codex, Claude Code, Cursor, and other Skills-compatible AI agents. It helps an agent find the important sentence, button, setting, or success state; capture only that useful region; keep the original source link; and prepare a reader-ready draft.

Use it for a Slack answer, a screenshot-led operating guide, or a public technical explainer.

![A synthetic employee guide created with Visual Brief](https://joeeeeey.github.io/visual-brief/assets/06-employee-guide-preview.webp)

## Install

Run this from the root of the project where you use your agent. Node.js and `npx` are required.

```bash
npx skills add joeeeeey/visual-brief --skill visual-brief --agent '*' --yes
```

This installs only the lightweight [`skills/visual-brief`](skills/visual-brief) directory for every supported agent detected in that project. Reopen your agent session after installation.

## Use It

After installation, use normal language in Codex CLI, Claude Code, or your other agent. No special command syntax is required.

For example:

> Using `<installation page URL or source material>`, create a visual step-by-step guide for installing the app on macOS. Walk through the web flow, screenshot only the important buttons and states, place each image directly after the step it explains, keep the original help links, and end with a visible success check. Prepare a draft only; do not publish or submit anything.

## Good Fits

- “Explain in Slack why we cannot use this approach, with the decisive official text highlighted.”
- “Turn this portal workflow into a beginner-friendly guide with one screenshot per useful step.”
- “Create a V2EX, blog, or X draft using real evidence screenshots and clearly labeled explanatory visuals.”

## Defaults

- Keep screenshots used as factual evidence next to the text they support.
- Keep original source links so readers can verify the claim.
- Treat generated images and diagrams as explanation, not evidence.
- Create drafts and previews first. Sending, uploading, or publishing requires explicit approval.
- Keep cookies, tokens, browser state, private URLs, and personal data out of the repository.

## Links

- [See the complete synthetic example](https://joeeeeey.github.io/visual-brief/case-study/)
- [Read the Skill](skills/visual-brief/SKILL.md)
- [中文说明](README.zh-CN.md)
- [MIT License](LICENSE)
