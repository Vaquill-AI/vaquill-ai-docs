# Documentation screenshots

Reproducible capture pipeline for the product screenshots in `images/`.
Re-run it when the UI changes rather than hand-replacing files.

## Why it is automated

Screenshots rot. Two images in this repo were already wrong before this
pipeline existed: `drafting.png` showed quick-start document types that had
been renamed, and the workflow builder shot predated a redesign. A scripted
capture makes a refresh cheap enough to actually do.

## Requirements

- Node 20+, `npm i playwright sharp`
- Chromium: `npx playwright install chromium`
- A seeded capture account (see "Seed data" below)

## Running

```bash
export VQ_USER='<capture account email>'
export VQ_PASS='<capture account password>'
export OUT="$PWD/.shots"
export CHROME_BIN="$HOME/Library/Caches/ms-playwright/chromium-<build>/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

node auth.mjs            # writes OUT/auth-state.json (a logged-in storage state)
node capture.mjs         # top-level surfaces, from the SHOTS list in the file
node capture_detail.mjs  # detail views, from OUT/detail_urls.json
node capture_rich.mjs    # interaction states (opened cells, expanded panels)
node optimize.mjs        # PNG -> WebP q82, capped at 150 KB
cp "$OUT"/shots/web/*.webp ../../images/
```

Capture one surface only: `node capture.mjs vendors-registry`

## House style

Follows Google, GitHub, GitLab and Cloudflare documentation guidance.

| Setting | Value | Why |
| --- | --- | --- |
| Viewport | 1440x900, DPR 2 | Retina without an unreadable column width |
| Theme | Light | Matches the docs site default |
| Format | WebP q82, <= 150 KB | ~94% browser support; AVIF softens small UI text |
| Max asset width | 1712px | Renders at 856px (Google's guidance) |
| Alt text | `Screenshot of <surface> showing <what>.` | GitHub's pattern, 40-150 chars |

Crop to the smallest region that answers the question. Full-app shots belong
on landing pages, not inside a procedure. Budget roughly 5 images per page.

**Shoot the interaction state, not the landing state.** A screen's resting view
is rarely the instructive one. The value is in the opened cell, the expanded
panel, the visible dropdown. `capture_rich.mjs` declares a `steps` function per
shot that runs before the shutter. Matrix cells expose `data-cell-id`; the
Review hub hides playbook and markup settings behind **Advanced options**.

## Gotchas that will cost you an hour

1. **Never remove `[data-tour]` elements.** Sidebar nav items carry tour
   anchors. Deleting them deletes the navigation.
2. **Guard chrome-stripping on rendered height, not child count.** The app root
   has few direct children but contains all the page text, so a text-only match
   removes the entire page. Prefer `visibility: hidden` over `remove()`.
3. **Cloudflare 403s the default Python/urllib User-Agent** (`error code: 1010`).
   Send a normal UA on any scripted API call. It looks exactly like an auth failure.
4. **The session lives in chunked SSR cookies** (`sb-dbs-auth-token.0/.1`), not
   localStorage. Join the parts, strip the `base64-` prefix, URL-decode, then
   base64-decode to reach `access_token`.
5. **The trial banner and "Upgrade Nd left" pill must be stripped** or a
   countdown gets baked into every image and is wrong the next day.

## Seed data

Captures need a populated account or every screen renders an empty state.
The capture account should hold fictional data only: no real client names, no
real matters, nothing privileged. Names used here are Acme Corporation,
Northwind Traders, Globex Industries, Initech Systems, Vertex Labs and
Meridian Health.

Keep the capture account on an active subscription. When a trial lapses every
endpoint returns 402 and the pipeline cannot be re-run.
