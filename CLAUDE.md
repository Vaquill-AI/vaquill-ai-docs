# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mintlify-powered documentation and API reference site for **Vaquill AI** — app guides, API docs, and developer resources for legal research and citation intelligence. This repo contains only the docs configuration, MDX content, and static assets; there is no application code, build step, or test suite.

## Related Repos

- **vaquill-ai-site** — Landing page and marketing site. Refer to that repo for product context, feature descriptions, and branding details.

## Key Files

- **docs.json** — Central Mintlify configuration: theme, navigation, API reference (OpenAPI), color scheme, logo/favicon paths, and footer/navbar links.
- **logo/** — Light/dark SVG logos referenced by docs.json.
- **images/** — Static images (hero banners, UI screenshots) used in documentation pages.
- **favicon.svg** — Site favicon.

## Development

Preview docs locally with the Mintlify CLI:

```
npx mintlify dev
```

This serves the site at `http://localhost:3000` with hot reload.

## Architecture Notes

- The API Reference tab is auto-generated from the OpenAPI spec at `https://api.vaquill.ai/external/openapi.json` — endpoint docs are not hand-written MDX.
- The workspace app docs (`guides/`, `workflows/`, `workspace-api/`, `integrations/dms/`, `introduction.mdx`) are kept in the repo but unpublished: they are listed in `.mintignore` and removed from `docs.json` navigation. The Workspace API reference tab is gone too. Old URLs are covered by the wildcard `redirects` in `docs.json`. To bring them back, remove the `.mintignore` lines, restore the tabs, and drop the matching redirects.
- Auth method is Bearer token via the `Authorization` header (configured in `docs.json > api > mdx > auth`).
- Appearance is locked to light mode (`appearance.strict: true`).
