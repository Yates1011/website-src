# william-yates.dev

Source and build tooling for [william-yates.dev](https://william-yates.dev).
So I can write articles in Markdown, run a command, and the styled site is generated
into the nginx web root (`/var/www/html`). 

## Writing a new article

1. Create `content/<slug>.md`. The filename (minus `.md`) becomes the URL:
   `/articles/<slug>.html`.

2. Start with a frontmatter header, then write Markdown:

   ```
   ---
   title: My New Post
   date: 2026-10-21
   tags: [Coding, C++]
   summary: One or two sentences shown as the excerpt in the feed.
   reading_time: 6 min read   # optional — auto-estimated if omitted
   ---
   ## First heading

   Normal **Markdown**: lists, links, images, and fenced code blocks.
   ```

3. Preview, then publish (see below).

## Commands

    make serve     # build into ./out and preview at http://localhost:8000
    make update    # build live into /var/www/html (publishes immediately)
    make publish   # build live, then push source to GitHub
    make help      # list targets

`make` targets just wrap `python3 build.py` / `python3 serve.py`, so those work
directly too. Build somewhere other than the web root with
`SITE_ROOT=some/dir python3 build.py`.

## Layout

    build.py        the generator (reads templates/ + content/, writes $SITE_ROOT)
    serve.py        local preview server
    Makefile        command shortcuts
    content/*.md    your article sources        <- you edit these
    templates/      index.html, writing.html, projects.html (hand-edited source)
    static/         style.css, llms.txt, robots.txt (copied verbatim on build)
    vendor/         vendored python-markdown (don't edit, don't need a venv)

Posts are sorted by `date` (newest first; use `YYYY-MM-DD`). `tags:` can be
`[A, B]` or a plain comma list, shown as "Filed under: …". The article feed is
injected between `<!-- POSTS:START -->` and `<!-- POSTS:END -->` in
`templates/index.html` (newest 5) and `templates/writing.html` (all); everything
else on those pages is hand-edited and left untouched. Shared fragments (top bar,
footer, article page shell) are constants near the top of `build.py`.

> Edit pages in `templates/`, never in `/var/www/html` — the next build
> overwrites the web root.

## Putting this on GitHub (one time)

1. Create an empty repo on GitHub (no README/license), then:

   ```
   git remote add origin git@github.com:<you>/<repo>.git
   git push -u origin main
   ```

2. From then on: write a post, `make serve` to check it, `make publish` to go
   live and push to GitHub in one step.

## Optional: deploy automatically on `git push`

Because you build directly on the VPS, `make publish` already makes a post live.
If you later want pushing from *another* machine to publish automatically,
install a **GitHub Actions self-hosted runner** on this VPS and add a workflow:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: [self-hosted]       # the runner installed on this VPS
    steps:
      - uses: actions/checkout@v4
      - run: python3 build.py    # writes straight to /var/www/html
```

Runner setup: GitHub repo → Settings → Actions → Runners → New self-hosted
runner, and follow the install commands. Until a runner is registered, leave
this workflow out (jobs would queue forever with nowhere to run).
