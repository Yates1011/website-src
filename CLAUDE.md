# CLAUDE.md

## Project
Personal portfolio + blog for William Yates — william-yates.dev, served by nginx
from `/var/www/html` on an IONOS VPS. This repo is the **source**; the web root is
**build output**. Markdown + tooling live outside the web root, so nginx only ever
serves finished HTML.

## How it works
- Articles are Markdown files in `content/*.md` with a frontmatter header.
- `python3 build.py` (a.k.a. `make update`) renders everything into `$SITE_ROOT`
  (default `/var/www/html`): article pages, the injected feeds, static files.
- Hand-edited pages live in `templates/`; `build.py` injects the article feed
  between `<!-- POSTS:START -->` and `<!-- POSTS:END -->` in `index.html`
  (newest 5) and `writing.html` (all), and copies `projects.html` verbatim.
- `static/` (style.css, llms.txt, robots.txt) is copied verbatim to the web root.
- The Markdown library is vendored in `vendor/` — no system install, no venv.

## Structure
    build.py        generator (reads templates/ + content/, writes $SITE_ROOT)
    serve.py        local preview: builds to ./out, serves localhost:8000
    Makefile        make update / serve / publish / help
    content/*.md    article sources  <- you edit these
    templates/      index.html, writing.html, projects.html (hand-edited source)
    static/         style.css, llms.txt, robots.txt (copied verbatim)
    vendor/         vendored python-markdown (don't edit)

## Workflow
- New article: add `content/<slug>.md` with frontmatter, then `make update`.
  The filename (minus `.md`) becomes the URL: `/articles/<slug>.html`.
- Preview before publishing: `make serve` → http://localhost:8000.
- Publish: `make publish` (builds live into /var/www/html, then `git push`).

## Conventions
- Every page shares the same top bar (`<nav class="top-bar">`) and footer.
- British English spelling throughout.
- Don't change the colour palette / fonts without being asked.
- `templates/` pages are source — edit them here, never edit `/var/www/html`
  directly (the next build overwrites it).
- Frontmatter: `title`, `date` (YYYY-MM-DD), `tags: [A, B]`, `summary`,
  optional `reading_time` (auto-estimated if omitted).
