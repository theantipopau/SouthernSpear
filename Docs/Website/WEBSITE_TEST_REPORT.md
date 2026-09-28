# WEBSITE TEST REPORT — Southern Spear

**Date:** 2026-09-28 (fourth pass: soldiers section added, then withdrawn — see §8)
**Build tested:** `python Tools/publish_site.py` → `Build/site/` → published
**Served from:** `http://localhost:8765/` (local static server) and the live site
**Browser:** Google Chrome (headless, via `puppeteer-core`) and Lighthouse 12
**Automated suites:** `Build/audit/responsive_audit.js` (9 viewports × both pages),
`Build/audit/text_audit.js` (type and target sizes), `Build/audit/interaction_test.js`
(22 keyboard, focus, filter, lightbox, loadout, redirect and zoom checks, across both pages),
`Build/audit/soldiers_check.js` and `Build/audit/soldiers_lightbox.js` were written for the
withdrawn soldiers section and are retained but not run
**Baseline for comparison:** the live site at https://theantipopau.github.io/southernspear-site/

> Internal document. Not published.

---

## 1. Lighthouse, mobile profile (simulated slow 4G)

Final figures are measured on the **live site**, because the local test server
(uncompressed, no TLS) understated them by roughly 1.2 s on LCP.

| Category | Before (live) | After (local) | **After (live)** |
|---|---|---|---|
| Performance | 67 | 88 | **93–100** |
| Accessibility | 100 | 100 | **100** |
| Best Practices | 100 | 100 | **100** |
| SEO | 100 | 100 | **100** |

| Metric | Before (live) | After (local) | **After (live)** | Target | Verdict |
|---|---|---|---|---|---|
| First Contentful Paint | 3.0 s | 2.1 s | **1.1–1.8 s** | < 1.8 s | **met** |
| Largest Contentful Paint | 12.9 s | 3.7 s | **1.5–2.7 s** | < 2.5 s | **usually met** |
| Total Blocking Time | 30 ms | 0 ms | **30–120 ms** | < 200 ms | met |
| Cumulative Layout Shift | 0 | 0 | **0** | < 0.1 | met |
| DOM elements | 4,839 | 1,584 | **950** | < 1,500 | **met** |
| Total transfer | 2,110 KB | 487 KB | **333 KB** | — | **−84 %** |

**Soldiers section cost.** Measured live after publishing (two consecutive runs):
performance **99 / 100**, accessibility 100, best practices 100, SEO 100, FCP 1.1–1.4 s,
LCP 1.5–1.8 s, TBT 30–40 ms, **CLS 0**, transfer **333 KB**. The two soldier renders add
**49 KB** to the mobile payload (720w AVIF, `loading="lazy"`, below the fold) and **no**
measurable LCP or CLS cost — the figures moved *down* on every timing metric against the
pre-section build, which is run-to-run variance on a shared machine rather than an
improvement. DOM elements fell to 950 because the changelog page split moved 32 session
bodies off the index.

**Read the live column as a range, not a point.** Lighthouse's simulated throttling on a
shared machine varies a lot run to run. Three consecutive live runs of the final build gave
performance **100, 93, 97** with LCP 1.7 s / 2.6 s / 2.3 s. The earlier single figure of 100
was one favourable run, not a stable result, and the 89 seen mid-pass was one slow run. CLS
and TBT were stable across every run.

The local figures in the middle column are kept because they are what the pre-publish
verification saw, and the gap between the two columns is itself a finding: the local static
server sends ~29 KB of CSS uncompressed and without TLS, which cost roughly 1.2 s of LCP.

Audits still flagged, all attributable to hosting rather than the site:
`uses-text-compression`, `unminified-css`, `unminified-javascript`, `unused-css-rules`,
`uses-long-cache-ttl`, `cache-insight`, `render-blocking-resources`. GitHub Pages does not
compress or minify, and sets a 10-minute cache TTL.

`image-delivery-insight` and `uses-responsive-images` also flag the two detail crops in the
gallery, which are 768px wide and display at roughly 340px. They are below the fold and
`loading="lazy"`, so they do not touch LCP; they are kept at 768px deliberately so the
lightbox has something sharp to show on a large display.

### What moved the needle

| Change | Effect |
|---|---|
| Removed the 1.6 MB PNG logo/favicon; real favicon suite | −1.6 MB |
| Removed `assets/header.png` (2.4 MB), published but never used | −2.4 MB payload |
| AVIF/WebP `<picture>` with `srcset` for the hero and all gallery art | 348 KB → 52 KB on mobile |
| Self-hosted fonts, removing the third-party render-blocking request | one less DNS + TLS |
| Dropped the `marked` CDN runtime dependency | −12 KB, one less origin |
| Lazy changelog and roadmap bodies | 4,839 → 1,584 DOM nodes |
| Replaced the 2.4 s hero scale animation with a 26 s `transform`-only drift | LCP 12.9 s → 3.7 s |
| **Removed the media-scoped hero `<link rel="preload">`** | LCP 2.5 s → **1.7 s** |

The last row is a correction to an earlier assumption. A media-scoped image preload was added
to help LCP, but Chromium fetched the *phone* crop even at 1366 px wide, discarded it, and
warned in the console — so the preload was competing with the real request rather than
ahead of it. The `<picture>` markup is already in the first HTML chunk, so the preload was
both unnecessary and harmful. Removing it took LCP from 2.5 s to 1.7 s and cleared the
console. `lcp-discovery-insight` scores 1 (pass) with no preload at all.

---

## 2. Breakpoints tested

| Width × height | Result |
|---|---|
| 360 × 800 | pass — no horizontal overflow, single-column stack, tap targets pass |
| 390 × 844 | pass — hero uses the portrait art direction |
| 768 × 1024 | pass — pillar rows collapse to one column, roadmap rail moves above content |
| **1366 × 768** | **pass — all three hero CTAs visible without scrolling** (the baseline failed this) |
| 1440 × 900 | pass |
| 1920 × 1080 | pass — shell stays 1240 px, gutters grow |
| 2560 × 1440 | pass — shell grows to 1440 px, body copy to 19 px at ≥2200 px |
| 3840 × 2160 | pass — no upscaling artefacts beyond the artwork's native 1536 px |

Horizontal overflow checked at every width: `scrollWidth === clientWidth` throughout.
`overflow-x: hidden` on `body` is a backstop only; the layouts do not rely on it.

Re-verified on 2026-09-27 with an automated sweep (`Build/audit/responsive_audit.js`,
real Chrome, nine viewports including 1024 × 768) that measures overflow, sub-44px tap
targets, sub-12px text, heading order and whether the hero CTAs fall below the fold.
**All nine viewports pass every check.** 200% zoom (a 720 × 450 CSS viewport) produces no
horizontal scrolling and keeps the hero CTAs on screen.

One element reports as extending past the viewport at every width: `.hero__image`, which is
the `hero-drift` scale animation caught mid-transform. `.hero` has `overflow: hidden`, and
`scrollWidth` equals `clientWidth` at all nine widths, so it is contained.

### Known responsive limitations

* **The hero artwork is 1536 × 1024 natively.** At 2560 and 3840 the browser upscales it.
  The largest derivative generated is 1536 px; nothing is upscaled in the pipeline.
  Derivatives stop at the source width deliberately.
* The mobile portrait crop is taken from the right of the source (sunset, mesa, gorge) because
  the composited wordmark occupies the centre band of the frame.
* **The soldier renders are portrait and the section stacks on narrow screens.** At 360 px the
  two cards stack, making the section roughly 1,600 px tall. That is the cost of showing a
  full-length figure at a readable size; the images are `loading="lazy"`, so nothing is
  fetched until it is scrolled to. Measured at 360, 768, 1280 and 1920: no overflow, AVIF
  served, no image upscaled, all card controls at or above 44 px.

---

## 3. Accessibility

Automated: **Lighthouse accessibility 100**, best practices 100, SEO 100.

Manual checks completed:

| Check | Result |
|---|---|
| Skip link appears on focus and is first in tab order | pass |
| One `h1`, no skipped heading levels | pass |
| Focus ring visible on every interactive element | pass |
| Mobile menu `aria-expanded` toggles correctly | pass |
| Mobile menu traps Tab and Shift+Tab | pass |
| `Escape` closes the menu and returns focus to the toggle | pass |
| Menu panel resets when the viewport passes 1000 px | pass |
| Nav marks the visible section with `aria-current="true"` | pass |
| Search input has a real `<label>` and `aria-describedby` | pass |
| Filters expose `aria-pressed`; only one is pressed at a time | pass |
| Result count is a `role="status"` live region | pass |
| Lightbox is `role="dialog" aria-modal`, focus moves in, Tab is trapped | pass |
| Lightbox closes on `Escape` and restores focus to the trigger | pass |
| Lightbox supports `ArrowLeft` / `ArrowRight` | pass |
| Session deep link opens the session and builds its body | pass |
| Hero image is decorative (`alt=""`) | pass |
| All content images have descriptive alt text | pass |
| Concept art additionally carries a `Concept` badge and caption | pass |
| Status is never colour alone — every pill has a text label | pass |
| All colour pairs meet WCAG AA (measured, see audit §3) | pass |
| `prefers-reduced-motion` collapses all motion and forces reveals visible | pass |
| `forced-colors` re-borders components | pass |
| Missing data shows a bordered, specific error block | pass |
| 44 × 44 px minimum tap targets | pass — measured, was failing on 13 controls |
| Changelog empty state offers a way out | pass — was missing entirely |

### Accessibility defects found and fixed

1. **`color-contrast`** — the decorative pillar numerals (`--line`, 1.99:1) failed AA even
   though they are `aria-hidden`. Introduced `--line-quiet` (`#5A6F61`, 3.06:1) and applied it
   to large decorative text.
2. **`label-content-name-mismatch`** — the brand link's `aria-label` did not contain its visible
   text. Removed the `aria-label` and added a visually hidden "— back to top" suffix, so the
   accessible name now contains the visible label.
3. **Thirteen controls under 44px** — the eight changelog filters, the four per-session
   "Link to this session" / "Copy link" controls and the skip link were 40–43px tall. Raised
   to `--target-min: 44px`.
4. **44 text runs under 12px** — the smallest was the nav's "Pre-alpha" at 9.9px. The whole
   small end of the type scale (0.62–0.74rem) was compressed upward with 0.75rem as the new
   floor, rather than flattened, so the hierarchy survives. `code` inside Markdown is sized
   `max(var(--fs-floor), 0.86em)` because it is relative and would otherwise undercut it.
   Caught by `Build/audit/text_audit.js`, which now reports **zero** runs under 12px.
5. **No empty state** — searching the changelog for something absent left a blank column
   under a count reading "0 of 31 sessions match". Added a bordered empty state that names
   the cause and offers a "Clear search and filters" button, which also restores the search
   field's focus.
6. **Mobile menu did not move focus on open** — `setOpen(true)` called `first.focus()`
   immediately, but the panel's `visibility` was mid-transition so `offsetParent` was null and
   `focusable()` returned nothing. Focus silently stayed on the toggle. Fixed on both sides:
   `visibility` now flips instantly on open and only delays on close (the standard discrete
   transition pattern), and the focus call is deferred a frame.
7. **Roadmap and changelog deep links did nothing** — a fresh load of `…#phase-3` neither
   scrolled nor expanded. The browser's fragment navigation runs before the script-built
   anchors exist and gives up silently. Added `revealFragment()`, re-run after both documents
   render and on `hashchange`: it expands the target, clears any active filter that would
   hide it, scrolls with header clearance and moves focus without a second scroll. Verified
   that a nav click lands the section at exactly 74px from the top (header 62 + 12).

---

## 4. Data integrity

All roadmap, changelog and status content is parsed from `data/*.md` at runtime. Nothing is
duplicated into the HTML.

| Check | Result |
|---|---|
| Changelog sessions parsed and rendered on `changelog.html` | pass — 43 at verification; the log grows one entry per session |
| Latest session identified, badged, and linked to `changelog.html#session-NNN` | pass |
| Home page latest-session panel: date, title, four completed points, next action | pass |
| Search across full session text (on the changelog page) | pass — "network" → 3 of 43 |
| Category filter | pass — Maps → 24 of 43 |
| Day grouping hides empty groups when filtered | pass |
| Deep link to `changelog.html#session-030` opens and focuses the session | pass |
| Legacy home-page link `/#session-030` forwards to `changelog.html` and opens the session | pass — live-verified |
| Session IDs unique despite duplicate numbers in the source log | pass — second occurrence gets a `-2` suffix |
| Deep link to `#phase-3` opens the phase detail and scrolls | pass |
| Roadmap renders 7 phases | pass |
| Phase states derived from the roadmap's own Current Status table | pass — Phase 0 Complete, Phase 1 In progress, Phases 2–6 Planned |
| Current phase card quotes the roadmap, not the older changelog glance | pass — "Phase 1 — Greybox Vertical Slice" |
| Exit criteria rendered from the Phase Summary table | pass |
| No invented percentages, dates or counts | pass |
| Loadout renders follow the 2026-09-28 producer decision (L-0017/L-0021) | pass — ADFRC-derived and sourced models published as labelled current stand-ins; AKM only as a "not a game weapon" reference card |
| Loadout section: all six renders load, are described, and open full-size in the lightbox | pass |
| Weapon renders carry their real textures | pass — every material slot resolved to the map named in the weapon's export manifest; opaque-pixel means 102–150, crushed blacks ≤ 2.1%, blown highlights ≤ 0.7% (`Build/audit/render_check.py`) |
| Scope lenses and reticles render as glass, not as flat black or white | pass — optics rendered in isolation (`Build/audit/scope_check.py`): A88 Spectr, A4/A416 TA31, A25 TA648 all show lens, body and reticle detail |
| Optics sit on the sight line | pass — scopes between the front and rear sights on all four scoped weapons; the EF88's Spectr on the bullpup rail (`Build/audit/probe_slots_geom.py`) |
| Header and menu type enlarged (nav 0.80 → 0.92rem, brand 1.02 → 1.2rem) | pass — desktop nav switches to the panel at 1100px; no overflow at any of the nine viewports |

### Data defects found and fixed during this pass

1. **`sectionOf` used `\Z`**, which is a Python anchor, not a JavaScript one. `NEXT ACTION`
   and `RISKS` silently rendered as "Not recorded".
2. **Multi-line regexes anchored with `$` under the `m` flag** matched nothing, because `$`
   matched every line end. Rewrote all three document extractions to walk lines instead.
3. **Untrimmed Markdown table cells** meant `| Phase 1 |` never matched `/^Phase\s+\d/`, so the
   current phase fell back to the stale changelog value.
4. **CRLF line endings** in the published Markdown broke heading matches in the browser while
   working locally. Normalised at fetch time.
5. **Numbered headings** (`## 13. Current Status`) did not match a plain heading lookup.
6. **Lightbox paths pointed at files that do not exist** (`main-menu-concept-01-1280.jpg`).
   The lightbox now uses the thumbnail's already-resolved `currentSrc`, so it can never 404.
7. **A race condition that only appeared on the live host.** The development-status panel
   needs both `data/CHANGELOG.md` and `data/DEVELOPMENT_ROADMAP.md`, but it was only
   triggered from the changelog's callback. Locally the roadmap happened to resolve first and
   the panel rendered; on GitHub Pages the order flipped and the panel sat on
   "Loading development status…" indefinitely. Both callbacks now trigger the render, guarded
   by a one-shot flag. **This is the clearest argument for testing against the real host.**
8. **Duplicate session numbers in the source log** (two 023s, two 028s–031s, two 032s, from
   parallel sessions) produced duplicate `id="session-NNN"` anchors, so deep links could land
   on the wrong session. `parseSessions` now de-duplicates: the second occurrence of a number
   gets a `-2` suffix, keeping every deep link unique and stable.

---

## 5. Browser testing

| Browser | Status |
|---|---|
| Chromium (current) | tested — full pass, console clean |
| Firefox | **not tested** |
| Safari / WebKit | **not tested** |

Console: **no errors and no warnings** on a fresh load. Network: no failed requests. Only two
`data:` SVG texture requests, the three self-hosted fonts, the hero AVIF, and the two
Markdown documents.

### Cross-browser risks to check

* `100svh` / `100dvh` on the hero, lightbox and mobile menu — `vh` fallbacks are declared first.
* `backdrop-filter` is no longer used, so no Safari prefix dependency remains.
* `text-wrap: balance` is progressive enhancement; unsupported browsers wrap normally.
* `content-visibility` on `.session` is progressive enhancement.
* `element.closest`, `Array.prototype.flatMap`-free iteration and `matchMedia.addEventListener`
  all have fallbacks or are guarded.
* `navigator.clipboard` is feature-detected with a graceful fallback.
* AVIF is offered through `<picture>`, so Safari and Firefox take WebP. The brand marks are
  the exception: the nav, footer and gallery emblems use a plain PNG `src` because the AVIF
  version saves under 3 KB and a `<picture>` there would cost more in markup than it saves.
* `max()` inside `font-size` for `.markdown-body code` is supported everywhere current;
  browsers that lack it fall back to the inherited size, which is larger, not smaller.

**Firefox and WebKit testing is outstanding and should happen before this is treated as
cross-browser verified.**

---

## 6. Content integrity

| Check | Result |
|---|---|
| Pre-alpha stated in hero, facts, status banner, FAQ, footer, 404 | pass |
| "No public build yet" retained | pass |
| "Donations are not being accepted" retained | pass |
| 3 ACR / MAF mirror explanation retained in full | pass |
| Fictional-project disclaimer retained, and repeated in overview and FAQ | pass |
| Not-affiliated-with-America's-Army line retained | pass |
| Unreal Engine / Epic trademark acknowledgement retained | pass |
| Every previously working link still resolves | pass |
| No release date, player count, platform, award or review invented | pass |
| Map names and descriptions taken verbatim from `ORIGINAL_BRIEF.md` | pass |
| Training modules and role prerequisites taken from `GAME_DESIGN_DOCUMENT.md` | pass |
| Soldier renders labelled as renders, never as gameplay | pass — the section note says "studio renders of the current internal models, not captured gameplay" |
| Soldier render provenance stated (L-0016 body + L-0021 kit, promotion not clearance) | pass |
| Camouflage stated as the project's own, generated from noise | pass — the note names `Tools/Textures/make_character_textures.py` |
| No real unit's insignia claimed or shown | pass — the MAF kit is peacekeeper-style and is described as such, not as any real unit's equipment |
| No ADF affiliation implied | pass — the disclaimer extends the new section |
| Camouflage palette checked against the producer's reference photography | pass — render saturation 0.48 vs reference 0.46, pale population 9.8% vs 10.2% |

---

## 7. Publishing workflow

| Check | Result |
|---|---|
| `python Tools/publish_site.py --build-only` | pass |
| LFS-pointer guard still applied to every copied file | pass |
| `.nojekyll` still written | pass |
| Clone / pull / copy / commit / push flow unchanged | pass |
| Directory copy is extension-allowlisted | pass |
| Retired assets removed from the public repo | pass |
| No engine, Lyra or game content published | pass |
| All new paths are relative, so the `/southernspear-site/` sub-path works | pass |
| `assets/logo.png`, `assets/header.png`, `assets/keyart.jpg` no longer published | pass (all confirmed 404 live) |
| `/favicon.ico` published at the site root | pass — browsers request it there regardless of any `<link>` |
| **Live publish run and verified** | pass |
| All assets return 200 with correct content types from the live host | pass |
| `assets/soldiers/*` published by the directory copy, no publisher change needed | pass — 12 files (2 sides × 720/1200 × PNG/WebP/AVIF) live, all 200 |
| GitHub Pages build lag after publish | noted — a newly published asset can 404 for up to ~30 s while Pages rebuilds. The verification loop polls rather than treating the first 404 as a failure; confirmed 200 on retry, and `favicon.ico` showed the same one-off 503. |
| `.gitattributes` keeps `Site/assets/**` out of Git LFS, as the publisher requires | pass |

---

## 8. Outstanding items

### Assets still required

1. **Frozen in-engine gameplay captures.** `Saved/Screenshots/WindowsEditor/SSShot.png` is
   overwritten by the editor every session and is gitignored, so it cannot be published. The
   gallery currently contains concept art only and says so. The loadout and soldiers sections
   show studio renders of the weapons and player models currently in the internal build
   instead, which is honest but is not the same proof. This remains the only thing standing
   between this being a concept-art site and a site that proves the game renders.
2. Map, role and environment artwork for the five map concepts.
3. An official horizontal wordmark lockup, for a richer header lockup than emblem + HTML text.
4. **The original character (C-001/C-002).** A player-model section was built and withdrawn in
   Session 042 because the L-0016 mannequin's proportions read as a dummy. It is not
   re-attempted until there is an original body; `Tools/Blender/render_soldiers.py` and its
   pose solver are ready to reuse. A frozen in-engine capture (item 1) fills the gap better in
   the meantime.

**Resolved since the first pass.** The earlier report led with "a clean 4K hero without
composited interface text" as the top outstanding asset. `Docs/images/mainmenu.png` turned
out to be exactly that: analysis of its pixels found no titling rows and no composited
emblem, unlike `loadingscreen.png`, which carries the emblem, the wordmark, the tagline and
the two corner labels. The hero is now cut from `mainmenu.png` and the approved lockup is
rendered as a separate element above the copy, so the artwork no longer competes with the
page's own `h1`. `loadingscreen.png` is still published, labelled as the loading screen
design, with its corner labels explained in the caption.

### Engineering follow-ups

1. Minify CSS and JS in the build step. GitHub Pages serves both uncompressed, so
   `styles.css` (~12 KB) and `site.js` (~43 KB) are the largest avoidable transfers left.
2. Test in Firefox and WebKit. Everything in this report is Chromium only.
3. The gallery is six items; the markup is data-shaped so adding captures needs no
   JavaScript change. The soldiers section is the same: two hand-written cards, no JavaScript
   beyond the shared lightbox, so adding a faction means copying one `<li>`.
4. `Docs/DEVELOPMENT_ROADMAP.md` and `Docs/CHANGELOG.md` used to disagree about Phase 0.
   **Resolved 2026-09-28:** the roadmap's Current Status table now reads Phase 0 Complete
   (G0.8 passed) and Phase 1 Active, agreeing with the changelog; the status panel and the
   roadmap now tell the same story. Anything further belongs to the project documents, not
   the site.

### Known visual trade-offs accepted

* The hero now uses `mainmenu.png`, which has no composited titling, and the approved
  stacked lockup is a separate `<img>` above the copy. The page's `h1` is therefore the
  positioning statement with a visually hidden "Southern Spear:" prefix, so the wordmark is
  not announced twice.
* The loading-screen design keeps its corner labels. They are part of that artwork and are
  explained in its caption.
* **The soldier renders are matched to each other, not to the game's lighting.** Both sides are
  studio-lit on the same figure-relative rig with a small per-side exposure trim, so the pair
  reads as a set. They are not lit as they would be in Dry River at dawn, and the section does
  not claim they are: it says they are studio renders of the current internal models.
