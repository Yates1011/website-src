#!/usr/bin/env python3
"""Static blog builder for william-yates.dev.

Write articles as Markdown files in content/ (with a small frontmatter header),
then run:  python3 build.py   (or: make update)

Source lives in this repo:
  templates/   hand-edited pages (index.html, writing.html, projects.html)
  static/      files copied verbatim (style.css, llms.txt, robots.txt)
  content/     your article Markdown sources

Output is written to $SITE_ROOT (default /var/www/html), which nginx serves.
Set SITE_ROOT to build elsewhere, e.g.  SITE_ROOT=out python3 build.py
"""

import sys, os, re, html, glob, shutil
from datetime import datetime

# Use the locally vendored copy of the markdown library (no system install).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import markdown  # noqa: E402

# --- Paths -------------------------------------------------------------------
HERE          = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR   = os.path.join(HERE, "content")
TEMPLATES_DIR = os.path.join(HERE, "templates")
STATIC_DIR    = os.path.join(HERE, "static")

# Where the finished site is written. Defaults to the nginx web root; override
# with the SITE_ROOT env var (e.g. for local previews via `make serve`).
SITE_ROOT = os.environ.get("SITE_ROOT", "/var/www/html")
ARTICLES  = os.path.join(SITE_ROOT, "articles")

INDEX_MAX = 5   # how many posts to show on the home page feed

# Pages whose <!-- POSTS:START/END --> region gets the article feed injected.
# (src template name, number of posts to show — None means all)
FEED_PAGES = [("index.html", INDEX_MAX), ("writing.html", None)]

# --- Shared fragments --------------------------------------------------------
TOP_BAR = """  <nav class="top-bar">
    <div class="wrap top-bar-inner">
      <a href="/" class="top-bar-title">William Yates</a>
      <ul class="top-bar-nav">
        <li><a href="/">Home</a></li>
        <li><a href="/writing.html">Writing</a></li>
        <li><a href="/projects.html">Projects</a></li>
        <li><a href="/#about">About</a></li>
      </ul>
    </div>
  </nav>"""

FOOTER = """    <footer>
      <span>&copy; 2026 William Yates</span>
      <span>william-yates.dev</span>
    </footer>"""

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} &middot; William Yates</title>
  <link rel="stylesheet" href="/style.css" />
</head>
<body>
{topbar}

  <div class="wrap">
    <article class="post-full">
      <a href="/writing.html" class="back-link">&larr; Back to writing</a>

      <h1>{title}</h1>
      <div class="article-meta">
        <span>{date}</span>
        <span>{reading}</span>
      </div>

{body}
    </article>

{footer}
  </div>
</body>
</html>
"""

# --- Frontmatter + parsing ---------------------------------------------------
def parse_frontmatter(text):
    """Split a '--- key: value ---' header from the Markdown body."""
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if m:
        block, body = m.group(1), m.group(2)
        for line in block.splitlines():
            if not line.strip() or ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip()
            if val.startswith("[") and val.endswith("]"):
                val = [t.strip() for t in val[1:-1].split(",") if t.strip()]
            meta[key] = val
    return meta, body


def fmt_date(raw):
    """2026-06-15 -> '15 June 2026'. Falls back to the raw string."""
    for f in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(raw), f).strftime("%-d %B %Y")
        except ValueError:
            continue
    return str(raw)


def reading_time(md_body, override):
    if override:
        return override
    words = len(re.findall(r"\w+", md_body))
    return f"{max(1, round(words / 200))} min read"


def sort_key(a):
    try:
        return datetime.strptime(str(a["date_raw"]), "%Y-%m-%d")
    except ValueError:
        return datetime.min


# --- Build -------------------------------------------------------------------
def load_articles():
    articles = []
    for path in sorted(glob.glob(os.path.join(CONTENT_DIR, "*.md"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            meta, body_md = parse_frontmatter(fh.read())
        md = markdown.Markdown(extensions=["fenced_code", "tables", "sane_lists", "attr_list"])
        body_html = md.convert(body_md)
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        articles.append({
            "slug": slug,
            "title": meta.get("title", slug),
            "date_raw": meta.get("date", ""),
            "date": fmt_date(meta.get("date", "")),
            "tags": tags,
            "summary": meta.get("summary", ""),
            "reading": reading_time(body_md, meta.get("reading_time")),
            "body": body_html,
        })
    articles.sort(key=sort_key, reverse=True)
    return articles


def write_article_pages(articles):
    # Note: body HTML is inserted verbatim (no source re-indentation) so that
    # whitespace-significant <pre> code blocks render exactly as written.
    os.makedirs(ARTICLES, exist_ok=True)
    for a in articles:
        page = ARTICLE_TEMPLATE.format(
            title=html.escape(a["title"]),
            topbar=TOP_BAR,
            footer=FOOTER,
            date=html.escape(a["date"]),
            reading=html.escape(a["reading"]),
            body=a["body"],
        )
        out = os.path.join(ARTICLES, f"{a['slug']}.html")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(page)
        print(f"  article  -> articles/{a['slug']}.html")


def copy_static():
    """Copy everything in static/ verbatim into the site root."""
    if not os.path.isdir(STATIC_DIR):
        return
    for name in sorted(os.listdir(STATIC_DIR)):
        src = os.path.join(STATIC_DIR, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(SITE_ROOT, name))
            print(f"  static   -> {name}")


def feed_html(articles):
    items = []
    for a in articles:
        tags = ", ".join(html.escape(t) for t in a["tags"]) or "Blog"
        items.append(
            f'      <article class="post">\n'
            f'        <h3 class="post-title"><a href="/articles/{a["slug"]}.html">{html.escape(a["title"])}</a></h3>\n'
            f'        <p class="post-excerpt">{html.escape(a["summary"])}</p>\n'
            f'        <a href="/articles/{a["slug"]}.html" class="post-more">Read more...</a>\n'
            f'        <div class="post-meta">\n'
            f'          <span>Filed under: {tags}</span>\n'
            f'          <span>Posted {html.escape(a["date"])}</span>\n'
            f'        </div>\n'
            f'      </article>'
        )
    return "\n\n      <hr class=\"post-sep\" />\n\n".join(items)


def render_page(src_name, feed):
    """Read templates/<src_name>, inject the feed, write to SITE_ROOT/<src_name>."""
    src = os.path.join(TEMPLATES_DIR, src_name)
    dst = os.path.join(SITE_ROOT, src_name)
    with open(src, encoding="utf-8") as fh:
        page = fh.read()
    pattern = re.compile(r"(<!-- POSTS:START -->).*?(<!-- POSTS:END -->)", re.DOTALL)
    if not pattern.search(page):
        print(f"  WARNING: no POSTS markers in templates/{src_name} — copied as-is")
    else:
        page = pattern.sub(lambda m: m.group(1) + "\n" + feed + "\n      " + m.group(2), page)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"  page     -> {src_name}")


def copy_plain_templates(skip):
    """Copy templates that take no feed injection (e.g. projects.html) verbatim."""
    for name in sorted(os.listdir(TEMPLATES_DIR)):
        src = os.path.join(TEMPLATES_DIR, name)
        if name in skip or not os.path.isfile(src):
            continue
        shutil.copy2(src, os.path.join(SITE_ROOT, name))
        print(f"  page     -> {name}")


def main():
    os.makedirs(SITE_ROOT, exist_ok=True)
    articles = load_articles()
    print(f"Building {len(articles)} article(s) into {SITE_ROOT} ...")
    write_article_pages(articles)
    copy_static()
    feed_names = [name for name, _ in FEED_PAGES]
    for name, limit in FEED_PAGES:
        posts = articles if limit is None else articles[:limit]
        render_page(name, feed_html(posts))
    copy_plain_templates(skip=feed_names)
    print("Done.")


if __name__ == "__main__":
    main()
