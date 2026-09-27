"""Build and publish the Southern Spear website to the public site repository.

The site source lives in Site/. The public repository
(github.com/theantipopau/southernspear-site) receives only:

    index.html, styles.css, site.js       from Site/
    assets/logo.png, assets/header.png    from Docs/images/ (canonical, unmodified)
    assets/keyart.jpg                     from Docs/images/keyart.jpg (JPEG of loadingscreen.png)
    data/CHANGELOG.md                     from Docs/CHANGELOG.md
    data/DEVELOPMENT_ROADMAP.md           from Docs/DEVELOPMENT_ROADMAP.md
    README.md                             from Site/README.site.md

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
    "assets/logo.png": "Docs/images/logo.png",
    "assets/header.png": "Docs/images/header.png",
    "assets/keyart.jpg": "Docs/images/keyart.jpg",
    "data/CHANGELOG.md": "Docs/CHANGELOG.md",
    "data/DEVELOPMENT_ROADMAP.md": "Docs/DEVELOPMENT_ROADMAP.md",
}


def git(*args, cwd=OUT):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def build():
    if not os.path.isdir(os.path.join(OUT, ".git")):
        if os.path.isdir(OUT):
            shutil.rmtree(OUT)
        subprocess.run(["git", "clone", "-q", REMOTE, OUT], check=True)
    elif git("ls-remote", "--heads", "origin").strip():
        # A brand-new, empty site repo has nothing to pull yet.
        git("pull", "-q", "--ff-only")

    for dest, src in FILES.items():
        src_path = os.path.join(ROOT, src)
        with open(src_path, "rb") as fh:
            head = fh.read(64)
        if head.startswith(b"version https://git-lfs"):
            sys.exit("ERROR: {} is an LFS pointer, not the real file".format(src))
        dest_path = os.path.join(OUT, dest)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copyfile(src_path, dest_path)
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
