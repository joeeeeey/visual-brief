# Publishing Safely

This repository prepares material for public communication; it is not a
publishing client. Creating a draft, a preview, an image, or a repository does
not authorize an external action.

## Before Publishing

1. Verify the factual claims against their named canonical sources.
2. Open every final WebP at normal reading size.
3. Check for private URLs, query strings, tokens, account data, customer data,
   browser chrome, unrelated tabs, and unlicensed material.
4. Label diagrams and generated visuals as illustrative. Do not use them as
   proof for external facts.
5. Show the destination, final text, images, account, and public URL to the
   approving person.
6. Obtain explicit approval in the current conversation before upload, send,
   post, submission, or public-repository creation.

## Public Images

The GitHub Pages site for this project publishes only synthetic showcase images
under `https://joeeeeey.github.io/visual-brief/assets/`. Those URLs can be
embedded in a V2EX post or another public draft after the image and caption
have been reviewed.

The employee device-check case study lives at
`https://joeeeeey.github.io/visual-brief/case-study/`. Its `05`, `06`, and `07`
assets are browser-rendered synthetic screens and contain no real company,
account, employee, installer, or device data.

The English README and social-ready guide use
`https://joeeeeey.github.io/visual-brief/assets/08-employee-guide-preview-en.webp`,
rendered from `site/case-study/en.html`.

Regenerate the reviewed case-study images locally with:

```bash
python3 -m pip install -r requirements-dev.txt
npm install
npx playwright install chromium
npm run render-case-study
```

Do not use GitHub Pages as a shortcut for screenshots that contain credentials,
customer data, private tenant state, or access-controlled material.

## Channel Drafts

- [V2EX draft (Chinese)](V2EX-DRAFT.zh-CN.md)
- [X / Twitter drafts](X-DRAFT.md)

Both files are drafts only. They do not imply that a post was uploaded or sent.
