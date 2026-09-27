# WEBSITE_AUDIT — Southern Spear public site

**Audit date:** 2026-09-27
**Auditor:** front-end / UX / a11y / performance review
**Live site:** https://theantipopau.github.io/southernspear-site/
**Site source:** `Site/` (`index.html`, `styles.css`, `site.js`)
**Publisher:** `Tools/publish_site.py`
**Public repo:** `theantipopau/southernspear-site`

> This file is an internal working document. It lives in the private game repository under
> `Docs/Website/` and is **not** published to the public site.

---

## 1. How the publishing pipeline works today

`Tools/publish_site.py` builds the public repository from a **fixed file map**:

| Public path | Source |
|---|---|
| `index.html` | `Site/index.html` |
| `styles.css` | `Site/styles.css` |
| `site.js` | `Site/site.js` |
| `assets/logo.png` | `Docs/images/logo.png` |
| `assets/header.png` | `Docs/images/header.png` |
| `assets/keyart.jpg` | `Docs/images/keyart.jpg` |
| `data/CHANGELOG.md` | `Docs/CHANGELOG.md` |
| `data/DEVELOPMENT_ROADMAP.md` | `Docs/DEVELOPMENT_ROADMAP.md` |
| `README.md` | `Site/README.site.md` |

Behaviour:

1. Clones `https://github.com/theantipopau/southernspear-site.git` into `Build/site` on first run,
   otherwise `git pull --ff-only`.
2. Copies each mapped file. **Refuses to publish an LFS pointer** (checks the first 64 bytes for
   `version https://git-lfs`).
3. Writes an empty `.nojekyll`.
4. `git add -A`, commits as `Publish site from SouthernSpear <game-repo-sha>`, pushes to `origin HEAD:main`.
5. `--build-only` stops after the copy, for local preview.

**Consequence for this work:** the file map is closed. Any new asset (responsive image
derivatives, favicon suite, social preview, self-hosted fonts, per-section data) will **not be
published** until the map is extended. Extending the map is safe and additive as long as the LFS
guard, the `.nojekyll` write and the commit/push flow are preserved. No engine, Lyra or game
content may ever be copied.

Data contract (must not break):

* `data/CHANGELOG.md` — `## Session NNN — YYYY-MM-DD — Title` headings, each with
  `### COMPLETED`, `### FILES CHANGED`, `### TESTING`, `### ASSETS`, `### DEFECTS FOUND`,
  `### RISKS`, `### NEXT ACTION`. Plus a `## Status At A Glance` table. 30 sessions, 143 KB.
* `data/DEVELOPMENT_ROADMAP.md` — `## N. Phase N — Name` headings, each with a
  `**Status: IN PROGRESS.**` line, `### Completed`, `### Remaining` and acceptance-criterion
  tables. Phases 0–6.

---

## 2. Measured baseline

Lighthouse 12, mobile form factor, simulated slow 4G, headless Chrome, against the **live** site.

| Category | Score |
|---|---|
| Performance | **67** |
| Accessibility | **100** |
| Best Practices | **100** |
| SEO | **100** |

| Metric | Value | Target | Verdict |
|---|---|---|---|
| First Contentful Paint | 3.0 s | < 1.8 s | fail |
| **Largest Contentful Paint** | **12.9 s** | < 2.5 s | **fail** |
| Total Blocking Time | 30 ms | < 200 ms | pass |
| Cumulative Layout Shift | 0 | < 0.1 | pass |
| Speed Index | 4.7 s | — | — |
| DOM elements | 4,839 | < 1,500 | fail |

Transfer on first load (mobile profile):

| Resource | Size | Note |
|---|---|---|
| `assets/logo.png` | **1,645 KB** | 1024×1024 PNG, used as the 44 px nav mark **and** the favicon |
| `assets/keyart.jpg` | 348 KB | hero, no `srcset`, no modern format |
| `data/CHANGELOG.md` | 50 KB | fetched on load, all 30 sessions rendered |
| fonts (Barlow Condensed ×2 woff2) | 29 KB | render-blocking third-party CSS |
| `marked.min.js` (jsDelivr) | 12 KB | third-party runtime dependency |
| `data/DEVELOPMENT_ROADMAP.md` | 6 KB | |
| `index.html` + `styles.css` + `site.js` | 21 KB | |
| **Total** | **≈ 2.11 MB** | |

`assets/header.png` (2,454 KB) is published but never referenced by the page — it is only used by
the GitHub-rendered `README.md`. It is 47 % of the repository's page weight for nothing.

**LCP element:** `<img src="assets/keyart.jpg" alt="" width="1536" height="1024">`.
LCP is 12.9 s for three compounding reasons: the image is a 348 KB legacy JPEG with no modern
derivative; a 2.4 s `transform: scale()` animation on the element keeps re-evaluating LCP until it
settles; and the element is only discovered after render-blocking CSS and the Google Fonts
stylesheet resolve.

Other Lighthouse findings: `render-blocking-resources`, `modern-image-formats`,
`uses-responsive-images`, `lcp-discovery-insight`, `dom-size`, `cache-insight`,
`image-delivery-insight`, `network-dependency-tree-insight`.

---

## 3. Current strengths — preserve these

1. **Genuinely good foundations.** Semantic `header`/`nav`/`main`/`footer`, one `h1`, ordered heading
   levels, a working skip link, `:focus-visible` outlines, `aria-expanded` on the menu button.
2. **Accessible by automated test.** Lighthouse accessibility is 100 and every colour pair in the
   existing token set passes WCAG AA. Measured ratios: body `#B9C1B4` on `#07100B` = 10.43,
   `--sage-400` on `--field-800` = 7.15, `--brass-500` on `--field-800` = 7.02,
   `--opfor-300` on `--field-800` = 5.78, button `#07100B` on `#C3A66D` = 8.27.
3. **Motion is already restrained and correct.** `prefers-reduced-motion` is honoured globally,
   reveal animation is opt-in via a `.js` class so content is never hidden without JavaScript, and
   there is no scroll hijacking.
4. **No framework, no build step, 607 lines total.** Progressive enhancement: the page is complete
   and readable with JavaScript disabled; the roadmap and changelog merely add detail.
5. **Honest data plumbing.** The status panel and changelog are generated from the project's own
   Markdown, with explicit empty/error states naming `data/` as the source. Nothing is duplicated
   or hard-coded.
6. **Content integrity is already strong.** The mirrored-faction explanation, the pre-alpha
   warnings, "there is no release to download", "donations are not being accepted", and the
   full fiction/Australian-Defence-Force disclaimer are all present and must survive.
7. **Correct GitHub Pages path handling.** All fetches and asset paths are relative
   (`data/…`, `assets/…`), so the site works under the `/southernspear-site/` sub-path.
8. **A strong approved brand asset exists** — a detailed emblem (brass-framed plate, Australian
   continent with topographic contours, Southern Cross, spear head), plus a 2508×627 banner
   lockup and a 1024×1024 square mark.

---

## 4. Visual weaknesses

1. **The hero is not cinematic — it is a screenshot with a logo pasted on it.** The only approved
   landscape artwork (`Docs/images/loadingscreen.png`, 1536×1024, published as `keyart.jpg`) has
   the emblem plate, the full `SOUTHERN SPEAR` wordmark, the tagline `REAL PEOPLE | TOUGH PLACES |
   GREATER TOGETHER` and two menu-style corner labels (`PEOPLE / PURPOSE`, `PLAY / BELONG`)
   **baked into the pixels**. The page then renders the logo a second time in the nav. The first
   screen therefore shows two logos, and the artwork contains interface text that looks like
   active navigation but is not.
2. **The hero is not full-viewport and the CTAs are below the fold.** Measured at 1366×768: hero
   height 909 px, all three buttons have `bottom: 942` — i.e. **not visible**. The brief requires
   the calls to action to be visible at 1366×768. Currently they are not.
3. **The hero is a 3:2 image letterboxed by `min(62vw, 82vh)` with `object-position: 50% 30%`** —
   the composition is arbitrary rather than art-directed, and the soldier (left) and the sunset
   (right) are both cropped awkwardly. There is no mobile-specific crop at all.
4. **No logo lockup treatment.** The nav shows a 44 px raster square plus browser-rendered text, so
   the approved lettering is never used at large size. There is no stacked hero logo, no
   monochrome footer mark, and no simplified favicon.
5. **Content hierarchy is a flat stack of identical card grids.** "In the build today" is six
   cards in one `repeat(3, 1fr)` grid; "Community" is three more; the pillars are three more. Four
   distinct ideas render as the same rectangle. Section alternation is only `wrap` vs `band`.
6. **The roadmap is not a roadmap.** `DEVELOPMENT_ROADMAP.md` is dumped as raw Markdown inside a
   single `<details>`. No phases, no timeline, no current-phase marker, no per-milestone
   disclosure, no deep links. The most distinctive transparency asset on the site is the least
   designed.
7. **The changelog is a wall.** Thirty `<details>` elements each rendering full Markdown, 4,839
   DOM nodes, no search, no filters, no date grouping, no anchors, no copy-link, no "latest"
   treatment, no categories.
8. **No media gallery, no maps/operations section, no FAQ**, and no place for them.
9. **The footer is three sentences of grey text.** No emblem, no status, no navigation, no
   back-to-top, no link to the roadmap or changelog.
10. **The brand is under-used.** The palette is decent but the page shows almost none of the
    specified motifs: no topographic contours, no map grid, no coordinate-style labels, no brass
    dividers, no fine hairline borders as a structural device. The one approved asset that *does*
    carry the topographic identity (the emblem) is shrunk to 44 px.
11. **Weak emphasis system.** Only three ad-hoc tags (`.ok` / `.wip` / `.todo`) distinguish state,
    all conveyed largely by colour. There is no Planned / In Progress / Testing / Complete /
    Blocked treatment system.
12. **No restrained atmosphere.** The brief's motion list (slow hero scale, fine line expansion,
    topographic drift, progress indicator) is entirely absent; the only animation is a 2.4 s
    one-shot scale that actively harms LCP.

---

## 5. Responsive issues

Verified live at 360×800, 390×844, 768×1024, 1366×768, 1440×900. No horizontal overflow detected
at 390 px (`scrollWidth 373 == clientWidth 373`).

1. **CTAs below the fold at 1366×768** — the single hardest requirement failure.
2. **The mobile menu is not a menu.** `display: none` → `.open` toggles a bare `<ul>` that flows
   in the header with no panel, no scrim, no heading and no separation from the page.
3. **Nine top-level nav items with `white-space: nowrap`** break to the hamburger at 900 px. At
   901–1024 px they are still on one line at full size, so the row is dense and fragile; the
   `Discord` pill plus eight links has no slack.
4. **No mobile art direction.** One 3:2 JPEG for every viewport, `object-position: 50% 30%`.
   On a 390×844 phone the soldier is cropped to a shoulder and the sunset is lost.
5. **`.facts dl` steps 5 → 3 → 2 → 1 columns** at 1280/1024/768/480 with no regard for content
   length, so tiles become ragged.
6. **Two `@media (max-width: 1024px)` blocks** are declared (lines 176 and 194) — duplicated
   breakpoint logic, easy to drift.
7. **`.wrap` padding steps 70 → 40 → 16 px** in three jumps, so tablet gutters are loose.
8. **Tap targets:** the skip link (8 px vertical padding), `.facts` tiles and the `summary`
   elements are all well under 44×44 px. The mobile menu links are 12 px + 12 px padding ≈ 44 px,
   which is only just compliant.
9. **200 % zoom / 320 px effective width** is untested; `.mirror-axis` and `.doc` tables are the
   likely failures.
10. **`.hero-copy { margin-top: -150px }`** pulls copy up over the image by a fixed pixel amount
    that has no relationship to the image's aspect ratio at any other width.

---

## 6. Accessibility issues

Automated score is 100, so these are the issues Lighthouse does not catch — all found by manual
review.

1. **Mobile menu: no focus trap, no `Escape` handler, no focus restoration.** Tabbing past the last
   link lands in the page behind the open menu. Focus is never returned to the toggle on close.
2. **The menu button's accessible name never changes** ("Menu" whether open or closed); no
   `aria-label` describing the controlled region beyond `aria-controls`.
3. **No active-section indication** in the navigation, and the current page is never marked
   (`aria-current` is absent everywhere).
4. **The nav has no scroll-state change**, so the brief's "transparent over hero → solid after
   scrolling" treatment is missing, and there is nothing to indicate position in the document.
5. **State is conveyed by colour in the status tags.** `.tag.ok/.wip/.todo` do carry text, which is
   good, but the roadmap's future milestone states would need a non-colour channel too.
6. **`<details>`/`<summary>` is used for the entire roadmap** with no heading structure, no
   per-milestone disclosure, and no summary text that tells a screen-reader user what is inside.
7. **`aria-live="polite"` on `#status` wraps three whole cards** of injected Markdown — a verbose
   live region that will read out a long paragraph on every update.
8. **Icon-only/graphic content is weak:** the hero image is `alt=""` (correct, decorative) but the
   page has exactly one meaningful image and it is decorative. The `role="img"` mirror diagram
   relies on a long `aria-label` with no text alternative visible to anyone.
9. **No landmarks for the sub-navigation groups**; the roadmap/changelog regions are not
   `section`-labelled as navigable collections.
10. **`prefers-reduced-motion` disables all transitions globally** with `!important` — correct in
    spirit, but it also kills the focus-ring transition and any future meaningful motion cue.
11. **No `:focus-visible` styling on the roadmap/changelog `summary`** beyond the default outline,
    which is fine, but there is no `aria-expanded` management and no keyboard affordance hint.
12. **Headings:** "In the build today" and "How to play" use `h3` correctly, but the pillared
    content and card titles are visually weighted far above their heading level, so the visual and
    document hierarchies diverge.
13. **No `lang` on any non-English fragment** (not currently needed), and no
    `aria-describedby` linking the pre-alpha warning to the CTA group.
14. **Missing-image and missing-data fallbacks are text-only** and are not announced politely.

---

## 7. Performance issues

1. **LCP 12.9 s vs a 2.5 s target** — the headline failure.
2. **1,645 KB of PNG for a 44 px logo, downloaded as the favicon too.** A favicon should be ~2–8 KB.
3. **`header.png` (2,454 KB) published and never used.** Pure dead weight in the repository.
4. **No `srcset`, no `sizes`, no `<picture>`, no AVIF/WebP.** One 348 KB JPEG serves every device.
5. **`width`/`height` are present on the hero but the CSS `transform: scale(1.06)` animation delays
   LCP by 2.4 s** by keeping the element in an animating state.
6. **Render-blocking:** the Google Fonts stylesheet is a third-party render-blocking request, and
   `styles.css` is render-blocking. Fonts are not self-hosted, so they cost an extra DNS + TLS
   handshake to `fonts.gstatic.com`.
7. **4,839 DOM nodes** built at load from 30 fully-rendered changelog sessions. This is the main
   INP/long-task risk and the reason `dom-size` fails.
8. **A third-party CDN runtime dependency** (`marked` from jsDelivr) for Markdown rendering — a
   supply-chain and availability risk for a static site, and it is fetched on every page view.
9. **Both `data/*.md` files are fetched on load** even though the roadmap and changelog are
   below-the-fold; nothing is deferred or paginated.
10. **No `content-visibility` / lazy rendering** for the long changelog and roadmap.
11. **No preload of the genuinely critical hero asset**, and no `fetchpriority="high"`.
12. **`backdrop-filter: blur(10px)`** on the sticky header is a full-width compositing cost on
    low-end mobile for a small visual gain.
13. **No cache or compression strategy is verifiable** beyond GitHub Pages defaults; Lighthouse
    flags `cache-insight` and `uses-long-cache-ttl`.
14. **CSS has genuine dead weight** — duplicated 1024 px media blocks, `.note`, `.tag.todo`
    variants and several unused selectors survive from earlier iterations.

---

## 8. Content hierarchy issues

1. **The site has no answer to "what is this, in one line?"** in its `<title>` (currently just
   "Southern Spear") or meta description framing.
2. **The nav vocabulary does not match the brief or the content.** There is no *Overview*,
   *Features*, *Training*, *Operations*, *Development*, *FAQ*. "Factions" and "The build" are
   in-jargon. "Download" leads with something that does not exist.
3. **Four separate pre-alpha disclosures** ("Free · Community developed", the download card, the
   facts row, the footer) with no single authoritative status statement.
4. **The engineering story is invisible.** UE 5.8, Lyra, the 30-session evidence log, the phase
   gates and the acceptance criteria are the project's strongest credibility signals and none of
   them are surfaced as *achievements*. The page reads as marketing, not as a transparent portal.
5. **The TRAIN / OPERATE / PROGRESS / ADAPT pillars are absent entirely**, and the roadmap proves
   they are planned (Phase 3 "Training & Progression", Phase 4 "Maps & Layers").
6. **Maps are mentioned only in passing** ("Red Gum Station · Dry River") although
   `Docs/MAPS_DRYRIVER.md` and Phase 4 document five maps.
7. **FAQ is missing**, so the ten questions a visitor actually has — playable? release date? ADF
   association? America's Army? free? — are unanswered and will be answered by assumption.
8. **Provenance of imagery is not stated.** Nothing tells a visitor whether a picture is captured
   gameplay or concept art. `Saved/Screenshots/WindowsEditor/SSShot.png` is a genuine in-engine
   capture but carries in-frame debug warnings; `loadingscreen.png` is a designed title screen. The
   site must label these differently.
9. **The fictional-project disclaimer lives only in the footer**, 6,000 px down the page, whereas
   the two most misreadable claims on the site ("Australian", "3 ACR") are in the second screen.

---

## 9. Broken or incomplete functionality

Nothing is hard-broken, but these are unfinished or fragile:

| # | Issue | Impact |
|---|---|---|
| 1 | Hero CTAs below the fold at 1366×768 | Brief requirement fails |
| 2 | Baked-in logo + menu text in hero artwork | Two logos; fake interface on screen one |
| 3 | `assets/header.png` published unused | 2.4 MB dead weight |
| 4 | Favicon is a 1.6 MB 1024×1024 PNG | Favicon effectively broken on slow connections |
| 5 | Mobile menu: no focus trap, no `Escape`, no focus restore | Keyboard users can tab behind the menu |
| 6 | No `robots.txt`, `sitemap.xml`, `manifest`, `canonical`, `og:url`, `og:type`, Twitter card, `theme-color` | SEO/share incomplete (Lighthouse 100 hides it) |
| 7 | `og:image` is a relative URL (`assets/keyart.jpg`) | Social cards fail to resolve |
| 8 | No structured data | No rich result for a video-game project |
| 9 | Changelog renders all 30 sessions eagerly | 4,839 DOM nodes, slow INP |
| 10 | Roadmap is a raw Markdown dump | No phase timeline, no current-phase marker |
| 11 | `marked` loaded from a third-party CDN | Availability + supply-chain risk |
| 12 | Status panel shows only the latest session's 3 facts | Roadmap phase/milestone/recent/next never surfaced |
| 13 | `.hero-copy` uses a fixed `-150px` pull | Fragile at every width except the one it was tuned at |
| 14 | No 404 page | GitHub Pages serves its own |
| 15 | No image error fallback | A missing derivative shows a broken-image icon |

---

## 10. Asset requirements

### Available now (approved source, `Docs/images/`)

| File | Size | Dimensions | Fitness |
|---|---|---|---|
| `logo.png` | 1.68 MB | 1024×1024 RGBA | Approved emblem + `SOUTHERN SPEAR` lockup. Use as the source for every brand variant. |
| `header.png` | 2.45 MB | 2508×627 RGB | Approved banner lockup + a second landscape crop. Not a nav logo. |
| `loadingscreen.png` | 3.27 MB | 1536×1024 RGBA (fully opaque) | The landscape scene. **Contains baked-in logo, wordmark, tagline and corner UI.** |
| `keyart.jpg` | 356 KB | 1536×1024 RGB | JPEG of the above. |
| `southern-spear-website-design-spec.svg` | 12.2 MB | vector | Design reference only — far too large to publish. |
| `Saved/Screenshots/WindowsEditor/SSShot.png` | 2.34 MB | 2560×1440 | **Genuine in-engine capture** of Dry River. Carries in-frame debug warnings in red/yellow. |

### Gaps that must be closed

1. **No 4K hero artwork exists.** The largest approved landscape source is 1536×1024. A 2560 px
   or 3840 px viewport will upscale it. Derivatives must be generated honestly (no upscaling
   beyond ~1.25×) and the limitation documented.
2. **No separate main-menu concept** — the brief references one; only the title/loading screen
   exists. The hero decision below is blocked on this.
3. **No emblem-only, horizontal-lockup, monochrome or favicon variants.** These must be derived
   from `logo.png` / `header.png` without redrawing, reinterpreting the spear, altering the
   Southern Cross or changing proportions.
4. **No map, role or environment artwork.** `Docs/MAPS_DRYRIVER.md` documents Dry River in detail;
   Red Ridge, Ironbark, Port Wakefield and Wattle Creek appear only as roadmap phase-4 names.
5. **No topography or grid texture.** Should be generated as CSS/SVG, not raster, to avoid
   shipping megabytes of noise.

### Derivatives required (web-optimised, generated — not hand-drawn)

`southern-spear-emblem-*.png|svg`, `southern-spear-logo-horizontal-light.*`,
`southern-spear-logo-stacked.*`, `southern-spear-logo-mono.*`, `favicon.svg` + `favicon-32/180/192/
512.png`, `hero-*.{avif,webp,jpg}` at 640/960/1280/1920/2560 for desktop **and** mobile crops,
`main-menu-concept-01.*`, `screenshot-dryriver-01.*`, `social-preview-1200x630.jpg`,
`og-image-*.jpg`, self-hosted `woff2` subsets for the three type families.

---

## 11. Recommended implementation order

Preserve a working baseline first: `publish_site.py --build-only` must reproduce today's site
byte-for-byte before any change lands.

| Stage | Work | Gate |
|---|---|---|
| 0 | Snapshot baseline; extend `publish_site.py` to copy `Site/assets/`, `Site/fonts/`, `Site/data/` while keeping the LFS guard, `.nojekyll` and push flow | `--build-only` still publishes today's site unchanged |
| 1 | Asset pipeline: brand variants, favicon suite, responsive hero derivatives, social preview, texture-free CSS motifs | variants visually match the approved source |
| 2 | Design tokens + `WEBSITE_DESIGN_SYSTEM.md` | every colour/font/spacing value is a custom property |
| 3 | Semantic structure, SEO/share, `robots.txt`, `sitemap.xml`, manifest, structured data | Lighthouse SEO 100 with no new warnings |
| 4 | Hero + sticky navigation | CTAs visible at 1366×768; no double logo; no layout shift on scroll state |
| 5 | Overview, TRAIN / OPERATE / PROGRESS / ADAPT, development status, maps, FAQ, footer | alternating compositions, no fabricated claims |
| 6 | Roadmap timeline + changelog search/filters/grouping | both render from existing Markdown; DOM nodes < 1,500 |
| 7 | Media gallery + lightbox with concept-art labelling | keyboard operable, lazy loaded, captions separate |
| 8 | Responsive pass at all eight breakpoints | no horizontal overflow; 44 px tap targets |
| 9 | Accessibility pass to WCAG 2.2 AA | focus trap, `Escape`, `aria-current`, non-colour state, 200 % zoom |
| 10 | Performance pass | LCP < 2.5 s, CLS < 0.1, INP < 200 ms measured |
| 11 | Test + document | `WEBSITE_TEST_REPORT.md` with real numbers |

---

## 12. Open decision — hero artwork

The only approved landscape artwork **at the time of the audit** had the emblem, the wordmark,
the tagline and two menu-style corner labels composited into the pixels. The brief
simultaneously requires (a) the approved logo rendered **separately from the background**,
(b) no active-navigation or interface text inside the artwork, and (c) genuine use of the
supplied artwork.

**Resolved.** `Docs/images/mainmenu.png` was supplied later and is a different composition:
pixel analysis finds no titling rows and no composited emblem, so it satisfies all three
requirements at once. The hero is cut from it, and the approved stacked lockup is a separate
element above the copy. `loadingscreen.png` is still published as the loading-screen design,
with its corner labels explained in its caption. **No image has been altered.**

---

## 13. Content integrity — do not fabricate

The following must be preserved verbatim in substance, and no release date, player count,
community size, award, review, partnership, confirmed platform or unapproved feature may be added.

* The mirrored-faction (3 ACR / MAF) explanation and its "cosmetic only" note.
* "Pre-alpha", "no public build yet", "donations are not being accepted".
* The full fiction disclaimer, the "not affiliated with America's Army" line, and the Unreal Engine
  trademark acknowledgement.
* Roadmap, changelog, status and their `data/` provenance.
* Every currently working link: `#top #about #mirror #build #how-to-play #download #roadmap
  #changelog #community`, the Discord invite, and the public repository URL.
* Honest provenance labelling: `SSShot.png` is captured in-engine; `loadingscreen.png` is a
  designed title screen, not gameplay.
