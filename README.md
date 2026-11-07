# Vaquill docs

Documentation for the [Vaquill](https://vaquill.ai) US primary law Data API, the MCP servers and the corpus.
The site is built with Mintlify and published at [vaquill.ai/docs](https://vaquill.ai/docs).

## Local development

```bash
npx mintlify dev
```

Serves at `http://localhost:3000` with hot reload.

## Checks

Both scripts need only Python 3 and run on every pull request.

```bash
python3 scripts/lint_docs.py          # style rules, prints file:line, exits non-zero on violations
python3 scripts/gen_llms_txt.py       # regenerate llms.txt from docs.json and page frontmatter
python3 scripts/gen_llms_txt.py --check   # fail if llms.txt is out of date
```

`llms.txt` is generated.
Never edit it by hand.
Change a page title, a page description or `docs.json`, then run the generator and commit the result.

## Style and structure guide

### Page types

Every page is one of four types.
Do not mix them on one page.

- **Tutorial or quickstart.** One path from nothing to a working result. No option tables.
- **Guide or recipe.** One task, with the steps to finish it.
- **Concept.** How something works and why. No step lists.
- **Reference.** Exact fields, codes and limits, scannable, no narrative.

Navigation groups follow the types: Get started, Core concepts, Guides, Data, Reference, Releases.
Add a new page to the group that matches its type.

### One fact in one place

State a fact once, on the page that owns it, and link to it from everywhere else.
Text that must appear on several pages (a pricing rule, a retry rule, a warning) lives in `/snippets` and is imported.
Do not hard-code counts such as sections, jurisdictions or corpus types.
Counts live on the Coverage page and are read from the API.
Elsewhere, describe in words and link to Coverage.
Do not ignore `/snippets` in `.mintignore`.

### Fold long detail

Use an Accordion for detail that most readers skip and that runs over about 8 lines: edge cases, full field lists, per-provider setup, long error tables.
The page must make sense with every Accordion closed.
Use a Warning only for data loss, billing or a wrong answer.
Use a Note for everything else, and sparingly.

### Writing rules

- **Sentence per line.** Put each full sentence on its own line in the source. Never wrap a sentence across lines. Mintlify renders the lines as one paragraph.
- **No em or en dashes** in any `.mdx`, `docs.json`, `llms.txt` or this file. Use a period, a comma, a colon or parentheses.
- **Sentence case** for titles, headings and navigation group names ("Core concepts", not "Core Concepts").
- **Description** in frontmatter: required on every published page, one sentence, at most 140 characters, no counts.
- **Sidebar title.** Add `sidebarTitle` of three or four words when the title is long enough to wrap in the sidebar.
- **Product name.** Write "Vaquill". Say "the Data API", not "the Statutes API".
- **Banned phrases** are listed in `scripts/lint_docs.py` (for example "leverage", "seamless", "in order to").

### Frontmatter template

```yaml
---
title: "Corpus types"
sidebarTitle: "Corpus types"
description: "How each corpusType token scopes a search and which tokens need a state."
---
```

## Moving a page

Prefer moving a page in `docs.json` over moving its file.
If a file must move, add a redirect from the old path in `docs.json` and fix every link to it.
Error pages under `/errors/{code}` are linked from API responses: never move `errors/codes.mdx`.

## Contributing

1. Fork the repo.
2. Make your change and run both scripts above.
3. Open a pull request. CI runs the same checks.

## Links

- [Dashboard](https://app.vaquill.ai)
- [MCP connector](https://pypi.org/project/vaquill-mcp/)
- [Open US Law Dataset](https://vaquill.ai/open-us-law)

## Community

Questions or ideas?
Join the Vaquill community on [Discord](https://discord.gg/GQtnwxf8nQ).
