#!/usr/bin/env bash
#
# Hardened pull-and-rebuild deploy for william-yates.dev.
#
# Runs on the VPS (as user `yates`) from cron. It is PULL-ONLY and outbound:
# it fetches origin/main over HTTPS (no credentials needed — the repo is
# public), and only rebuilds when origin has a genuinely newer commit.
#
# Safety properties:
#   - No inbound ports, no stored secrets (credential helper disabled for fetch).
#   - Fast-forward-only: refuses rewritten/force-pushed history.
#   - Builds into a throwaway staging dir, then copies into the web root, so
#     nginx never serves a half-written site. Top-level files are overwritten
#     (never deleted) so anything not managed by the build (e.g. .claude,
#     nginx defaults) is left untouched; only articles/ is mirrored with
#     --delete, since it is 100% build-managed.
#   - flock prevents overlapping runs.
#
set -euo pipefail

REPO="/home/yates/website-src"
BRANCH="main"
WEBROOT="/var/www/html"
LOG="$REPO/deploy.log"
LOCK="$REPO/.deploy.lock"

# Single-instance lock (non-blocking: if a run is in progress, skip this tick).
exec 9>"$LOCK"
flock -n 9 || exit 0

cd "$REPO"

# Fetch without using any stored credential helper (public repo = no auth).
git -c credential.helper= fetch --quiet origin "$BRANCH"

# If origin/main is already contained in HEAD (up to date, or local is ahead),
# there is nothing new to deploy.
if git merge-base --is-ancestor "origin/$BRANCH" HEAD; then
    exit 0
fi

echo "$(date -Is) deploy: $(git rev-parse --short HEAD) -> $(git rev-parse --short origin/$BRANCH)" >>"$LOG"

# Fast-forward only — refuse to deploy rewritten history.
git merge --ff-only "origin/$BRANCH" >>"$LOG" 2>&1

# Build into a fresh staging directory.
STAGING="$(mktemp -d /home/yates/.deploy-staging.XXXXXX)"
trap 'rm -rf "$STAGING"' EXIT
SITE_ROOT="$STAGING" python3 build.py >>"$LOG" 2>&1

# Publish: top-level files are overwritten but never deleted (protects
# unmanaged files in the web root); articles/ is mirrored exactly.
#
# Permissions: -p lets rsync manage perms on transferred items (including the
# existing web-root dir), and --chmod forces nginx-readable modes (dirs 755,
# files 644). This is the fix for the 403 caused by plain `rsync -a` copying
# the mktemp staging dir's 0700 mode onto /var/www/html. We skip -o/-g (can't
# chown as non-root) and -D (no device/special files here).
RSYNC="rsync -rlpt --chmod=D755,F644"
$RSYNC "$STAGING"/ "$WEBROOT"/ --exclude 'articles/' >>"$LOG" 2>&1
$RSYNC --delete "$STAGING/articles/" "$WEBROOT/articles/" >>"$LOG" 2>&1

echo "$(date -Is) deploy: done" >>"$LOG"
