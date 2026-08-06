# Stoat docs

Source for <https://themedocs.github.io/stoat/> — the documentation for the Stoat WordPress theme.

Static HTML built from markdown. No JavaScript, no webfonts, no build service:
the stylesheet is inlined, so a docs page is one request. GitHub Pages serves
the committed `docs/` folder.

## Layout

```
content/index.md          the stoat docs home
content/<section>/<page>.md
docs/assets/              screenshots, referenced as /stoat/assets/…
nav.toml                  section + page order for the left nav
theme.toml                name, version, accent, demo/download/support links
docs/                     build output — this is what GitHub Pages publishes
```

A rebuild replaces everything in `docs/` except `docs/assets/`, so screenshots
are stored once rather than in both a source and a build copy.

Each page opens with front matter:

```markdown
---
title: "Install"
description: "One sentence, used for the meta description and search results."
---
```

`title` drives the `<h1>`, the left-nav label and the `<title>`. Leave
`description` empty and the first paragraph is used instead. Only `##` and
`###` headings reach the right-hand table of contents.

## Adding a page

1. Add the slug to the right `[[section]]` in `nav.toml`.
2. `python3 build.py --scaffold` — creates the missing `.md`.
3. Write it, then rebuild.

Removing a slug from `nav.toml` unpublishes the page.

## Building

```bash
python3 -m venv venv && venv/bin/pip install markdown   # first time
venv/bin/python build.py                                # content/ -> docs/
```

Commit `docs/` along with the source — that folder is what Pages publishes.

Currently 1 pages.
