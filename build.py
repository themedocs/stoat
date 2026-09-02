#!/usr/bin/env python3
"""
Theme docs — static site builder.

    python3 build.py             content/ -> docs/
    python3 build.py --scaffold  create any .md listed in nav.toml but missing on disk

One repo holds one theme. Output is plain HTML: no webfonts, stylesheet inlined,
and the only script is the analytics tag, so a page is a single blocking request.
Only dependency is `markdown`.

GitHub Pages serves the docs/ folder on the default branch, which is why the
build output is committed rather than built by CI.
"""

import html
import json
import re
import shutil
import struct
import sys
import tomllib
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
BUILD = ROOT / "docs"
# Screenshots live inside the published folder and are the one thing a rebuild
# does not touch — copying them into place would double their weight in git.
ASSETS = BUILD / "assets"
STYLE = ROOT / "style.css"


# ---------------------------------------------------------------- small helpers


def load_toml(path):
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def split_front_matter(text):
    """Parse a leading `---` block of plain `key: value` lines."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, text[end + 4 :].lstrip("\n")


def titleise(slug):
    words = slug.replace("-", " ").split()
    fixed = {"rtl": "RTL", "css": "CSS", "faq": "FAQ", "faqs": "FAQs",
             "json": "JSON", "seo": "SEO", "html": "HTML", "amp": "AMP",
             "js": "JS", "php": "PHP", "wp": "WP"}
    text = " ".join(fixed.get(w, w) for w in words)
    return text[:1].upper() + text[1:]


def first_paragraph(body_html, limit=155):
    match = re.search(r"<p>(.*?)</p>", body_html, re.S)
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", "", match.group(1))
    text = html.unescape(" ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


# ------------------------------------------------------------- image dimensions
# Read width/height from the file header so every <img> can carry them. That is
# what keeps layout shift at zero on pages that are mostly screenshots.


def image_size(path):
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            return (int.from_bytes(data[24:27], "little") + 1,
                    int.from_bytes(data[27:30], "little") + 1)
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        return None
    if data[:2] == b"\xff\xd8":  # JPEG: walk segments to a start-of-frame
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2 : i + 4])[0]
    return None


def enrich_images(body_html, prefix):
    """Add width/height/lazy-loading to every <img> we can measure."""
    marker = f"{prefix}assets/"

    def repl(match):
        tag, src = match.group(0), match.group(1)
        if "width=" not in tag and src.startswith(marker):
            size = image_size(ASSETS / src[len(marker) :])
            if size:
                tag = tag[:-1] + f' width="{size[0]}" height="{size[1]}">'
        if "loading=" not in tag:
            tag = tag[:-1] + ' loading="lazy" decoding="async">'
        return tag

    return re.sub(r'<img [^>]*src="([^"]+)"[^>]*>', repl, body_html)


# ------------------------------------------------------------------ nav & pages


class Page:
    def __init__(self, section, slug, path, prefix):
        self.section = section
        self.slug = slug
        self.path = path
        self.prefix = prefix
        self.meta = {}

    @property
    def url(self):
        part = f'{self.section["dir"]}/' if self.section["dir"] else ""
        return f"{self.prefix}{part}{self.slug}/"

    @property
    def title(self):
        return self.meta.get("title") or titleise(self.slug)


def load_theme(prefix):
    theme = load_toml(ROOT / "theme.toml")
    theme["nav"] = load_toml(ROOT / "nav.toml").get("section", [])
    theme["pages"] = []
    for section in theme["nav"]:
        section["items"] = []
        for slug in section["pages"]:
            page = Page(section, slug, CONTENT / section["dir"] / f"{slug}.md", prefix)
            section["items"].append(page)
            theme["pages"].append(page)
    return theme


def scaffold(theme):
    made = 0
    for page in theme["pages"]:
        if page.path.exists():
            continue
        page.path.parent.mkdir(parents=True, exist_ok=True)
        page.path.write_text(
            f'---\ntitle: "{titleise(page.slug)}"\ndescription: ""\n---\n\n'
            "TODO — write this page.\n",
            encoding="utf-8",
        )
        made += 1
    return made


# -------------------------------------------------------------------- rendering


def render_nav(theme, current, prefix):
    name = html.escape(theme["name"])
    out = [f'<nav class="side" id="nav" aria-label="{name} documentation">',
           f'<a class="side-home" href="{prefix}">{name} docs</a>']
    for section in theme["nav"]:
        out.append(f'<b>{html.escape(section["title"])}</b>')
        for page in section["items"]:
            on = " class=on" if page is current else ""
            aria = ' aria-current="page"' if page is current else ""
            out.append(f'<a href="{page.url}"{on}{aria}>{html.escape(page.title)}</a>')
    out.append("</nav>")
    return "".join(out)


def render_toc(tokens):
    if not tokens:
        return ""
    out = ['<nav class="toc" aria-label="On this page"><b>On this page</b>']
    for token in tokens:
        out.append(f'<a href="#{token["id"]}">{html.escape(token["name"])}</a>')
        for child in token.get("children", []):
            out.append(f'<a class=sub href="#{child["id"]}">{html.escape(child["name"])}</a>')
    out.append("</nav>")
    return "".join(out)


def render_pager(theme, page):
    pages = theme["pages"]
    index = pages.index(page)
    previous = pages[index - 1] if index > 0 else None
    following = pages[index + 1] if index < len(pages) - 1 else None
    if not previous and not following:
        return ""
    out = ['<nav class="pager">']
    out.append(
        f'<a class=prev href="{previous.url}"><span>Previous</span>{html.escape(previous.title)}</a>'
        if previous else "<span></span>"
    )
    if following:
        out.append(f'<a class=next href="{following.url}"><span>Next</span>{html.escape(following.title)}</a>')
    out.append("</nav>")
    return "".join(out)


def breadcrumb_ld(base_url, trail):
    items = []
    for position, (name, url) in enumerate(trail, 1):
        item = {"@type": "ListItem", "position": position, "name": name}
        if url:
            item["item"] = base_url + url
        items.append(item)
    return json.dumps(
        {"@context": "https://schema.org", "@type": "BreadcrumbList",
         "itemListElement": items},
        separators=(",", ":"),
    )


def analytics(ga_id):
    """Google Analytics tag. Empty string when site.toml carries no ga_id."""
    if not ga_id:
        return ""
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>'
        "<script>window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments);}"
        f"gtag('js',new Date());gtag('config','{ga_id}');</script>"
    )


def shell(site, theme, *, title, description, url, body, nav, toc, crumbs, trail, css):
    base, prefix = site["base_url"], site["path_prefix"]
    accent = theme.get("accent", "#b45309")
    head = [
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        '<meta name=viewport content="width=device-width,initial-scale=1">',
        f"<title>{html.escape(title)}</title>",
    ]
    if description:
        head.append(f'<meta name=description content="{html.escape(description)}">')
    head += [
        f'<link rel=canonical href="{base}{url}">',
        # The site lives under a path prefix, so /favicon.ico at the origin is a
        # different theme's docs — every icon has to be named outright.
        f'<link rel=icon href="{prefix}assets/favicon.ico" sizes=any>',
        f'<link rel=icon type="image/png" sizes="32x32" href="{prefix}assets/favicon-32.png">',
        f'<link rel=icon type="image/png" sizes="16x16" href="{prefix}assets/favicon-16.png">',
        f'<link rel=apple-touch-icon href="{prefix}assets/apple-touch-icon.png">',
        f'<meta property="og:title" content="{html.escape(title)}">',
        f'<meta property="og:url" content="{base}{url}">',
        '<meta property="og:type" content="article">',
        f'<meta property="og:site_name" content="{html.escape(theme["name"])} docs">',
        '<meta name="twitter:card" content="summary">',
    ]
    if description:
        head.append(f'<meta property="og:description" content="{html.escape(description)}">')
    head.append(f"<style>:root{{--a:{accent}}}{css}</style>")
    head.append(f'<script type="application/ld+json">{breadcrumb_ld(base, trail)}</script>')
    head.append(analytics(site.get("ga_id")))

    links = "".join(
        f'<a href="{theme[key]}"{" rel=noopener target=_blank" if key != "support" else ""}>{label}</a>'
        for key, label in (("demo", "Demo"), ("feature", "Feature page"),
                           ("download", "Download"), ("support", "Support"))
        if theme.get(key)
    )
    bar = (
        f'<header class=bar><a class=brand href="{prefix}">'
        # The docs host's mark. The wordmark beside it already names the site,
        # so the image is decorative.
        f'<img src="{prefix}assets/{site.get("mark", "owldraft-mark.jpg")}" '
        f'alt="" width=24 height=24>'
        f'<span class=name>{html.escape(theme["name"])} <span>docs</span></span></a>'
        f"<nav class=bar-links>{links}</nav>"
        f'<a class=jump href="#nav">All pages</a></header>'
    )

    return (
        "".join(head)
        + "</head><body>"
        + '<a class=skip href="#main">Skip to content</a>'
        + bar
        # No table of contents (theme home) — let the content use that column.
        + f'<div class="wrap{"" if toc else " wide"}">'
        + f"<main id=main>{crumbs}{body}</main>"
        + nav
        + toc
        + "</div>"
        + "</body></html>"
    )


# ------------------------------------------------------------------------ build


def build():
    site = load_toml(ROOT / "site.toml")
    prefix = site["path_prefix"]
    css = re.sub(r"\s+", " ", re.sub(r"/\*.*?\*/", "", STYLE.read_text(), flags=re.S)).strip()
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css).replace(";}", "}")

    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists", "smarty"],
        extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}},
    )

    theme = load_theme(prefix)

    if "--scaffold" in sys.argv:
        print(f"  scaffold: {scaffold(theme)} new file(s)")
        return

    BUILD.mkdir(parents=True, exist_ok=True)
    for item in BUILD.iterdir():
        if item == ASSETS:
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()

    urls = []

    def write(url, markup):
        rest = url.removeprefix(prefix).strip("/")
        target = (BUILD / rest / "index.html") if rest else (BUILD / "index.html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markup, encoding="utf-8")
        urls.append(url)

    # ---- every page listed in nav.toml
    for page in theme["pages"]:
        if not page.path.exists():
            sys.exit(f"missing: {page.path.relative_to(ROOT)} (run --scaffold)")
        page.meta, raw = split_front_matter(page.path.read_text(encoding="utf-8"))
        md.reset()
        body = enrich_images(md.convert(raw), prefix)
        crumbs = (
            f'<nav class=crumbs><a href="{prefix}">{html.escape(theme["name"])}</a>'
            f'<span>{html.escape(page.section["title"])}</span></nav>'
        )
        write(
            page.url,
            shell(
                site, theme,
                title=f'{page.title} — {theme["name"]} docs',
                description=page.meta.get("description") or first_paragraph(body),
                url=page.url,
                body=f"<h1>{html.escape(page.title)}</h1>{body}{render_pager(theme, page)}",
                nav=render_nav(theme, page, prefix),
                toc=render_toc(md.toc_tokens),
                crumbs=crumbs,
                trail=[(theme["name"], prefix), (page.title, None)],
                css=css,
            ),
        )

    # ---- the theme's docs home
    meta, raw = split_front_matter((CONTENT / "index.md").read_text(encoding="utf-8"))
    md.reset()
    intro = enrich_images(md.convert(raw), prefix)
    cards = ["<div class=cards>"]
    for section in theme["nav"]:
        cards.append(f'<div class=card><h2>{html.escape(section["title"])}</h2>')
        shown = 8
        cards.append("".join(f'<a href="{p.url}">{html.escape(p.title)}</a>'
                             for p in section["items"][:shown]))
        if len(section["items"]) > shown:
            cards.append(f'<a class=more href="{section["items"][shown].url}">'
                         f'{len(section["items"]) - shown} more…</a>')
        cards.append("</div>")
    cards.append("</div>")
    write(
        prefix,
        shell(
            site, theme,
            title=meta.get("title") or f'{theme["name"]} documentation',
            description=meta.get("description") or first_paragraph(intro),
            url=prefix,
            body=f'<h1>{html.escape(theme["name"])} documentation</h1>{intro}{"".join(cards)}',
            nav=render_nav(theme, None, prefix),
            toc="",
            crumbs="",
            trail=[(theme["name"], None)],
            css=css,
        ),
    )

    # ---- 404
    (BUILD / "404.html").write_text(
        shell(
            site, theme,
            title="Page not found",
            description="",
            url=prefix,
            body="<h1>Page not found</h1><p>That page has moved or never existed. "
                 f'<a href="{prefix}">Start from the documentation home</a>.</p>',
            nav="", toc="", crumbs="", trail=[(theme["name"], prefix)], css=css,
        ),
        encoding="utf-8",
    )

    # ---- sitemap
    # Pages would otherwise hand the whole tree to Jekyll and drop nothing we need,
    # but skipping it makes the build deterministic and faster to publish.
    (BUILD / ".nojekyll").write_text("")

    base = site["base_url"]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        sitemap.append(f"<url><loc>{base}{url}</loc></url>")
    sitemap.append("</urlset>")
    (BUILD / "sitemap.xml").write_text("".join(sitemap), encoding="utf-8")

    total = sum(f.stat().st_size for f in BUILD.rglob("*") if f.is_file())
    print(f"  {len(urls)} pages · {total / 1024 / 1024:.1f} MB · css {len(css) / 1024:.1f} KB inlined")


if __name__ == "__main__":
    build()
