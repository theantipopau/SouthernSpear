# In-engine screenshots for the website

Captures placed here are published in the **Media** section of the website as
*in-engine captures*, labelled separately from concept art. The PNG files are
LFS-tracked like everything else in `Docs/images/`; only the web derivatives
built from them are published.

## Adding captures

1. Capture from a real run of the build, for example a windowed `-game` run with
   `-SSShotAt=45` (writes `Saved/Screenshots/WindowsEditor/SSShot.png`). Never
   screen-capture the desktop. 1920 px wide or larger is best; nothing is upscaled.
2. Copy the PNG here with a short, descriptive name, e.g. `dryriver-objective-a.png`.
3. Add an entry to `screenshots.json`:

   ```json
   {
     "screenshots": [
       {
         "file": "dryriver-objective-a.png",
         "title": "Dry River, approach to Objective A",
         "alt": "First-person view down a dry creek bed towards a fenced homestead, red dirt banks and gum trees either side, late-afternoon light.",
         "map": "Dry River",
         "captured": "2026-09-28",
         "session": "060",
         "note": "Greybox lighting pass; foliage is placeholder."
       }
     ]
   }
   ```

   `file`, `title`, `alt`, `map` and `captured` (YYYY-MM-DD) are required, and
   the build stops if any is missing. `session` (the changelog session the
   capture came from) and `note` (what is placeholder or unfinished) are optional
   but encouraged: they are shown on the page.
4. `python Tools/build_site_assets.py --only screenshots` writes
   `Site/assets/screenshots/shot-*` (AVIF, WebP and JPEG at 960 and 1920 px) and
   `Site/data/screenshots.json`.
5. Preview with `python Tools/publish_site.py --build-only`, look at every image on
   the page, then publish.

## Rules

* A capture must show the build as it is. No paint-over, no compositing, no
  concept art, no external tools' renders. Colour grading done in-engine is fine.
* A capture is only published after a person has looked at it (Session 042).
* The site lists captures newest first. To withdraw one, delete its entry and its
  PNG, rerun step 4, and add its `assets/screenshots/shot-<name>-*` files to
  `RETIRED` in `Tools/publish_site.py` so the published copies are removed.
