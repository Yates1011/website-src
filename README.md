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

## Automatic deploy (installed)

A cron job on the VPS (`deploy.sh`, run every minute as `yates`) publishes
automatically: **push to `main` from anywhere → the site updates within a
minute**. No need to be on the VPS.

`deploy.sh` is pull-only and outbound — it fetches `origin/main` (public repo,
so no credentials), and only acts when there is a genuinely newer commit. It is
hardened:

- **fast-forward only** — refuses rewritten/force-pushed history;
- builds into a throwaway staging dir, then publishes, so nginx never serves a
  half-written site;
- top-level files are overwritten but never deleted (protects unmanaged files
  in the web root); `articles/` is mirrored exactly;
- `flock` prevents overlapping runs;
- runs as the unprivileged `yates` user, never root.

Deploys are logged to `deploy.log` (git-ignored). To pause auto-deploy:
`crontab -e` and comment out the `deploy.sh` line. To deploy by hand:
`./deploy.sh`.

Note: because the deploy pulls with no credentials, the VPS needs no GitHub
token to publish. A token is only needed to *push from the VPS*
(`make publish`); if you push from elsewhere, keep no token on the VPS.
