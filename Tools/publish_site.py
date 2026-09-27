"""Build and publish the Southern Spear website to the public site repository.

The site source lives in Site/. The public repository
(github.com/theantipopau/southernspear-site) receives only:

    index.html, styles.css, site.js       from Site/
    robots.txt, sitemap.xml, 404.html,
    manifest.webmanifest                  from Site/
    assets/**                             from Site/assets/  (generated derivatives)
    fonts/*.woff2                         from Site/fonts/   (self-hosted subsets)
    data/CHANGELOG.md                     from Docs/CHANGELOG.md
    data/DEVELOPMENT_ROADMAP.md           from Docs/DEVELOPMENT_ROADMAP.md
    data/*.json                           from Site/data/    (site-owned view models)
    README.md                             from Site/README.site.md

Site/assets/ is produced by Tools/build_site_assets.py from the canonical,
unmodified artwork in Docs/images/. Canonical sources are never published
directly any more; only the optimised derivatives are.

No engine, Lyra or game content is ever copied: the game repository is private
and Epic content must not be republished.

Usage:
    python Tools/publish_site.py --build-only     # build into Build/site for preview
    python Tools/publish_site.py                  # build, commit and push

Exit codes: 0 ok, 1 failure.
"""

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Build", "site")
REMOTE = "https://github.com/theantipopau/southernspear-site.git"

FILES = {
    "index.html": "Site/index.html",
    "styles.css": "Site/styles.css",
    "site.js": "Site/site.js",
    "README.md": "Site/README.site.md",
    "robots.txt": "Site/robots.txt",
    "sitemap.xml": "Site/sitemap.xml",
    "404.html": "Site/404.html",
    "manifest.webmanifest": "Site/manifest.webmanifest",
    # Browsers request /favicon.ico at the site root regardless of any <link>,
    # so the 32px mark is published there as well as under assets/.
    "favicon.ico": "Site/assets/favicon.ico",
    "data/CHANGELOG.md": "Docs/CHANGELOG.md",
    "data/DEVELOPMENT_ROADMAP.md": "Docs/DEVELOPMENT_ROADMAP.md",
}

# Whole directories copied verbatim. These only ever hold site-owned build
# output: optimised image derivatives, self-hosted font subsets and JSON view
# models. They are allowlisted by extension so an accidental drop of game
# content into Site/ cannot be published.
DIRS = {
    "assets": "Site/assets",
    "fonts": "Site/fonts",
    "data": "Site/data",
}

ALLOWED_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg", ".ico",
    ".woff2", ".json", ".txt", ".xml", ".webmanifest", ".css",
}

# Assets that used to ship straight from Docs/images/. The page no longer
# references them, so they are not republished.
RETIRED = (
    "assets/logo.png",
    "assets/header.png",
    "assets/keyart.jpg",
    # The favicon is now generated as a raster suite from the approved emblem
    # crop (favicon.ico plus 32/48/96/180/192/512 PNGs), so the hand-written
    # SVG is dead weight. Anything dropped from the build must be listed here
    # or it stays published forever.
    "assets/favicon.svg",
)


def git(*args, cwd=OUT):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def assert_not_lfs(src_path, label):
    with open(src_path, "rb") as fh:
        head = fh.read(64)
    if head.startswith(b"version https://git-lfs"):
        sys.exit("ERROR: {} is an LFS pointer, not the real file".format(label))


def copy_one(dest, src):
    src_path = os.path.join(ROOT, src)
    if not os.path.isfile(src_path):
        sys.exit("ERROR: missing {}".format(src))
    assert_not_lfs(src_path, src)
    dest_path = os.path.join(OUT, dest)
    os.makedirs(os.path.dirname(dest_path) or OUT, exist_ok=True)
    shutil.copyfile(src_path, dest_path)


def copy_tree(dest, src):
    src_root = os.path.join(ROOT, src)
    if not os.path.isdir(src_root):
        return
    for dirpath, _dirnames, filenames in os.walk(src_root):
        for name in filenames:
            if name.startswith("."):
                continue
            suffix = os.path.splitext(name)[1].lower()
            if suffix not in ALLOWED_SUFFIXES:
                print("  SKIP (not allowlisted)", os.path.join(dirpath, name))
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, src_root).replace(os.sep, "/")
            assert_not_lfs(full, rel)
            dest_path = os.path.join(OUT, dest, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copyfile(full, dest_path)


def prune_empty(path):
    """Drop directories left behind by retired assets so the repo stays tidy."""
    if not os.path.isdir(path):
        return
    for entry in os.listdir(path):
        full = os.path.join(path, entry)
        if os.path.isdir(full):
            prune_empty(full)
            if not os.listdir(full):
                os.rmdir(full)


def build():
    if not os.path.isdir(os.path.join(OUT, ".git")):
        if os.path.isdir(OUT):
            shutil.rmtree(OUT)
        subprocess.run(["git", "clone", "-q", REMOTE, OUT], check=True)
    elif git("ls-remote", "--heads", "origin").strip():
        # A brand-new, empty site repo has nothing to pull yet.
        git("pull", "-q", "--ff-only")

    for dest, src in FILES.items():
        copy_one(dest, src)

    for dest, src in DIRS.items():
        copy_tree(dest, src)

    for rel in RETIRED:
        stale = os.path.join(OUT, rel)
        if os.path.exists(stale):
            os.remove(stale)
            print("  removed retired asset", rel)

    prune_empty(os.path.join(OUT, "assets"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print("built", OUT)


def publish():
    git("add", "-A")
    if not git("status", "--porcelain").strip():
        print("site unchanged; nothing to publish")
        return
    head = subprocess.run(["git", "log", "-1", "--format=%h"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    git("commit", "-q", "-m", "Publish site from SouthernSpear {}".format(head))
    git("push", "-q", "-u", "origin", "HEAD:main")
    print("published")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-only", action="store_true")
    args = ap.parse_args()
    build()
    if not args.build_only:
        publish()
    return 0


if __name__ == "__main__":
    sys.exit(main())
