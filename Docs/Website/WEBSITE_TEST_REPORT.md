# WEBSITE TEST REPORT — Southern Spear

**Date:** 2026-09-27
**Build tested:** `python Tools/publish_site.py --build-only` → `Build/site/`
**Served from:** `http://127.0.0.1:8080/` (local static server)
**Browser:** Chromium (headless, via the Freebuff preview) and Lighthouse 12
**Baseline for comparison:** the live site at https://theantipopau.github.io/southernspear-site/

> Internal document. Not published.

---

## 1. Lighthouse, mobile profile (simulated slow 4G)

Final figures are measured on the **live site**, because the local test server
(uncompressed, no TLS) understated them by roughly 1.2 s on LCP.

| Category | Before (live) | After (local) | **After (live)** |
|---|---|---|---|
| Performance | 67 | 88 | **100** |
| Accessibility | 100 | 100 | **100** |
| Best Practices | 100 | 100 | **100** |
| SEO | 100 | 100 | **100** |

| Metric | Before (live) | After (local) | **After (live)** | Target | Verdict |
|---|---|---|---|---|---|
| First Contentful Paint | 3.0 s | 2.1 s | **1.1 s** | < 1.8 s | **met** |
| Largest Contentful Paint | 12.9 s | 3.7 s | **1.7 s** | < 2.5 s | **met** |
| Total Blocking Time | 30 ms | 0 ms | **30 ms** | < 200 ms | met |
| Cumulative Layout Shift | 0 | 0 | **0** | < 0.1 | met |
| DOM elements | 4,839 | 1,584 | **1,584** | < 1,500 | marginal |
| Total transfer | 2,110 KB | 487 KB | **278 KB** | — | **−87 %** |

All three headline targets are met on the live host: LCP 1.7 s, CLS 0, TBT 30 ms.

The local figures in the middle column are kept because they are what the pre-publish
verification saw, and the gap between the two columns is itself a finding: the local static
server sends ~29 KB of CSS uncompressed and without TLS, which cost roughly 1.2 s of LCP.

Audits still flagged, all attributable to hosting rather than the site:
`uses-text-compression`, `unminified-css`, `unminified-javascript`, `unused-css-rules`,
`uses-long-cache-ttl`, `cache-insight`, `render-blocking-resources`. GitHub Pages does not
compress or minify, and sets a 10-minute cache TTL.

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

### Known responsive limitations

* **The hero artwork is 1536 × 1024 natively.** At 2560 and 3840 the browser upscales it.
  The largest derivative generated is 1536 px; nothing is upscaled in the pipeline.
  Derivatives stop at the source width deliberately.
* The mobile portrait crop is taken from the right of the source (sunset, mesa, gorge) because
  the composited wordmark occupies the centre band of the frame.

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
| 44 × 44 px minimum tap targets | pass |

### Two accessibility defects found and fixed during this pass

1. **`color-contrast`** — the decorative pillar numerals (`--line`, 1.99:1) failed AA even
   though they are `aria-hidden`. Introduced `--line-quiet` (`#5A6F61`, 3.06:1) and applied it
   to large decorative text.
2. **`label-content-name-mismatch`** — the brand link's `aria-label` did not contain its visible
   text. Removed the `aria-label` and added a visually hidden "— back to top" suffix, so the
   accessible name now contains the visible label.

---

## 4. Data integrity

All roadmap, changelog and status content is parsed from `data/*.md` at runtime. Nothing is
duplicated into the HTML.

| Check | Result |
|---|---|
| 30 changelog sessions parsed and rendered | pass |
| Latest session identified as Session 029, badged "Latest update" | pass |
| Search across full session text | pass — "navigation" → 4 of 30 |
| Category filter | pass — Maps → 17 of 30 |
| Day grouping hides empty groups when filtered | pass |
| Roadmap renders 7 phases | pass |
| Phase states derived from the roadmap's own Current Status table | pass — Phase 0 Complete, Phase 1 In progress, Phases 2–6 Planned |
| Current phase card quotes the roadmap, not the older changelog glance | pass — "Phase 1 — Greybox Vertical Slice" |
| Exit criteria rendered from the Phase Summary table | pass |
| No invented percentages, dates or counts | pass |

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
* AVIF is offered through `<picture>`, so Safari and Firefox take WebP.

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
| `.gitattributes` keeps `Site/assets/**` out of Git LFS, as the publisher requires | pass |

---

## 8. Outstanding items

### Assets still required

1. **A clean 4K hero without composited interface text.** This is the single highest-value
   asset. The current artwork has the emblem, the wordmark, the tagline and two menu-style
   corner labels (`LAND / PEOPLE / PURPOSE` and `TRAIN / PLAY / BELONG`) burned into the
   pixels. Per instruction the artwork is used unmodified, so the hero shows those corner
   labels and the site's own `h1` had to be composed beneath the artwork's own wordmark
   rather than replacing it.
2. **Frozen in-engine gameplay captures.** `Saved/Screenshots/WindowsEditor/SSShot.png` is
   overwritten by the editor every session and is gitignored, so it cannot be published. The
   gallery currently contains concept art only and says so.
3. Map, role and environment artwork for the five map concepts.
4. An official horizontal wordmark lockup, for a richer header lockup than emblem + HTML text.

### Engineering follow-ups

1. Minify CSS and JS in the build step. GitHub Pages serves both uncompressed, so
   `styles.css` (~29 KB) and `site.js` (~40 KB) are the largest avoidable transfers left.
2. DOM size is 1,584 against a 1,500 target — close enough not to matter now that the bodies
   are lazy, but worth keeping in mind if more sections are added.
3. Test in Firefox and WebKit.
4. The gallery is currently three items; the markup is data-shaped so adding captures needs
   no JavaScript change.

### Known visual trade-offs accepted

* The hero's baked-in wordmark is the de facto title, so the page's own `h1` is the
  positioning statement with a visually hidden brand prefix. Duplicating a large
  "Southern Spear" heading over the artwork's own would have read as two competing logos.
* The corner labels in the hero are part of the approved artwork and are left in place.
  They are explained in the MAIN MENU CONCEPT caption as belonging to the concept.
