---
title: "Stoat"
description: "Stoat wp theme is a free WordPress theme."
---

Stoat wp theme is a free WordPress theme.

- **Demo:** [stoat.withemes.com](https://stoat.withemes.com)
- **License:** GPL-2.0-or-later
- **Requires:** WordPress 6.5+, PHP 7.4+
- **Key features:** Tiny js, self-hosted fonts, everything at minimum

### Download & Install

1. Download theme here: [stoat.zip](https://downloads.wordpress.org/theme/stoat.zip)
2. Install WordPress.
3. **WordPress Dashboard → Appearance → Themes → Add New → Upload Theme**, choose **stoat.zip** → **Install** → **Activate**.

### Theme options + settings

Stoat wp theme uses native WordPress customizer, you can customize your site in **Dashboard → Appearance → Customize**.

### Header - logo + menu

- **Logo:** Customize → Site Identity → Logo. Toggle the text title/tagline with **Display site title** / **Display tagline** in the same section.
- **Menu:** Dashboard → Appearance → Menus → assign a menu to **Primary Menu**. Should use 2-level depth for best paractice; collapses to a hamburger / off-canvas panel automatically on mobile.

### Footer - menu + copyright

- **Menu:** assign a menu to **Footer Menu** (flat, 1 level).
- **Copyright:** Customize → Footer:
  - **Show © + year** - prefixes `© <year>.`
  - **Copyright text** - your line (HTML allowed).
  - **Keep theme credit** - appends "Built with Stoat".

### Front page

Standard WordPress - **Dashboard → Settings → Reading → Your homepage displays**:

- **Your latest posts** - blog index.
- **A static page** - pick a Homepage and a Posts page.

### Typography (fonts)

Self-hosted via the WordPress Font Library - no external requests.

1. **Dashboard → Appearance → Fonts** → install font families.
2. **Customize → Typography** → pick **Heading font** and **Body font**.

- **Allowed:** any family installed under Dashboard → Appearance → Fonts.
- **Not allowed:** Google Fonts / remote URLs (Stoat wp theme serves `.woff2` from your own site only).
- **System default** = native font stack (fastest), and the only option below WordPress 7.0.

### Style (colors)

**Customize → Style** - five color pickers: text, accent, background, selection, selected text. Empty = theme default.

### Blog featured images

Stoat wp theme displays a post thumbnail differently from core:

1. Featured image, if set.
2. Otherwise, the **first image in the post content** ≥ 300px wide.
3. Otherwise, no thumbnail.

If you want to disable featured image, go to **Customize → Blog/archive**

### Page settings

Edit a Page → **Page options** box → check **Hide page title?** to drop the title on the front end.

Example - a full-bleed cover page: [page-with-cover](https://stoat.withemes.com/page-with-cover/) is just a Page with the title hidden, using the Gutenberg **Cover** block as content.

### Search

There is no search icon in the header - search is a plain Page.

1. Create a Page (e.g. "Search").
2. Add the **Search** block, publish.

Example: [Demo search page](https://stoat.withemes.com/search/).

Note: **Customize → Misc → Disable pages in search results** is on by default, so search returns posts only.

### FAQ

#### Can I use the classic editor?

Yes — Stoat wp theme is very classic-editor friendly.

#### How to remove the credit?

**Customize → Footer → Keep theme credit** — turn it off. GPL doesn't require keeping it.

#### How to set up an image logo?

**Customize → Site Identity → Logo** → upload your image. Hide the text title/tagline in the same section with **Display site title** / **Display tagline**.

#### How to set dark mode?

There's no dark-mode toggle button yet. You can make a permanently-dark site at **Customize → Style**: set **Background color** to a dark value and **Text color** to a light one.

#### How to use Google Fonts or another font service?

Not through the theme settings — Stoat wp theme only serves self-hosted fonts. It doesn't forbid external fonts, though: use any plugin that loads them, then point the theme's tokens at the family with `:root { --heading-font: ...; --body-font: ...; }` in **Customize → Additional CSS**.

#### How to get 99/100 page speed?

Page speed = theme + plugins + hosting. Stoat wp theme handles the theme part (tiny JS, one small stylesheet, self-hosted fonts). Each plugin adds a little weight (extra JS, Google Analytics code, etc.). A clean site on decent hosting usually scores 99/100 out of the box. A cache plugin like LiteSpeed Cache helps further — Stoat wp theme works fine with it.
