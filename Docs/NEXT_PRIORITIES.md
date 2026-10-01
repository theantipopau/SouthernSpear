# NEXT PRIORITIES — what the game needs, in order

**Document ID:** `Docs/NEXT_PRIORITIES.md`
**Updated:** 2026-10-01, accuracy review against the current source configuration, inventory snapshot, and map audit.
**Read with:** `CLAUDE.md` → `Docs/HANDOVER_CLAUDE_CLOUD.md` → the latest `Docs/CHANGELOG.md` entry

This document answers one question: **what should be built next, and why.** Measurements and public specifications are distinguished from unverified appearance/runtime state. Asset inventory and producer clearance are recorded in `Docs/ASSET_REGISTER.md` §§4.9m–4.9o and `Docs/evidence/asset_inventory_20261001.md`.

It does not replace `Docs/PLAYER_MODEL_PLAN.md` (the character work, which is measured and ordered) or
`Docs/PROJECT_AUDIT.md` (the risk register). Where those already have detail, this links to them instead
of repeating them.

---

## 1. The producer's verdict, and what it measures

Four complaints from play, in the producer's words: the **character models look horrible**, the
**weapons are not looking great** and need better textures, the **VFX need work**, and the weapons need
**zeroing and recoil** built on real-world data.

The order the producer gave is also the right dependency order, and it is not a preference:

```
models ──▶ animations ──▶ VFX ──▶ maps
   └──────────────────────▶ weapon textures ──▶ recoil / zeroing
```

**Why models gate animations:** an animation retargeted onto a body that is about to be replaced is
work thrown away. The friendly body decision (ADR-042, Quantum on its own skeleton) means the retarget
target is settled, so this is now unblocked.

**Why texture/visual review precedes recoil tuning:** weapon presentation affects how recoil feels, so first establish which mesh and material the player sees. The relationship between surface finish and perceived recoil is a producer/design premise to validate in playtest, not a measured physical rule.

**Map art polish follows the producer's art order, but map readiness is not complete.** Dry River's Session 088 dressing pass and D-DR fixes are measured work, not producer sign-off: the playability audit still records 3 pass / 6 fail against its rules, and the in-game kangaroo and water checks remain open. Wandarra and Ravenshoe still need the attended R-82 navigation bake. Keep visual polish in the later art pass, but do not describe geometry/nav as finished.

---

## 2. Priority 1 — Character models

**State: Quantum is the producer-selected friendly body (ADR-042); final visual acceptance is still pending.** The active appearance uses Quantum shirt/jeans/arms/head modules on their own skeleton, with ADFRC vest/helmet gear and material overrides. The old G3 uniform/Modern Insurgent head assembly is superseded, not the current primary defect. See the current-state summary in `Docs/PLAYER_MODEL_PLAN.md` §1 and decision ADR-042.

| # | Task | Why first | State |
|---|---|---|---|
| P1 | **Make and accept the active Quantum outfit** | It must read as one deliberate soldier, not a sample mannequin with stacked parts; inspect camo, head/helmet, gloves/boots, vest/waist, shoulders, weapon pose and full silhouette under fixed conditions | **OPEN — visual rejection**: producer reports the last in-game class-select popup did not show a good model. The Session 091 screenshot is not available here; runtime-child preview sync is plumbing, not acceptance. Latest working-tree adjustments defer locality until component creation, expose the actual child meshes to capture, and use a centered full-body camera frame; build/capture still required. |
| P2 | **Measure current character cost and skeleton boundary** | R-58 concerns Manny as gameplay skeleton and Quantum retarget/gear leader-pose boundary; keep separate from art acceptance | **MEASURED (Session 091 report)** — 4 Quantum modules (351 bones) + 2 ADFRC gear items (164 bones); this inventory alone does not prove fit or runtime correctness. |
| P3 | **Audit current LOD/physics setup** | Historical R-59's 89,996-vertex total describes the retired G3 kit, not this active assembly | **MEASURED (Session 091 report)** — 107,016 LOD0 vertices, 6 parts, all only one LOD; Quantum modules report physics assets while the ADFRC vest/helmet lack them. Geometry totals are not a runtime performance profile. |
| P4 | **Verify and art-direct active camo/materials** | Confirm correct material instances, texture detail/scale, roughness and contrast on both garments under game lighting | **OPEN** — master is marked for skeletal use and instances were resaved; a visual screenshot/texture inspection is unavailable, and producer rejected latest preview. |
| P5 | **Make appearance review repeatable** | A fixed camera, fixed light, neutral pose and stable framing make the verdict reproducible | **IN_PROGRESS** — scene-capture code exists, but the checked-out evidence image is absent and the producer rejects current appearance; capture must be regenerated and reviewed. |

**Measurement, not adjectives.** P5 exists because the canopy-height defect in Session 084 was found by a
screenshot and missed by a passing placement report. A look verdict with a repeatable capture behind it is
the only kind that can be closed.

---

## 3. Priority 2 — Weapon textures

**State: tracked weapon assets are present, but current runtime assignments and visual finish are unverified.**
A prior Session 090 `Build/weapons_setup.json` report described five ADFRC texture slots on the A88;
that historical report is not independently verified as the current runtime graph. The tracked counts
below establish repository presence only, not which texture source is currently selected or how it renders.

The blanket statement that no weapon textures/materials are tracked is false. The tracked game-feature roots contain **271 A-series assets** across A88/A88G/A89/A4/A416/A25/A9, including 151 texture (`T_`) and 82 material-instance (`MI_`) assets. This establishes repository presence, not which assets are selected at runtime or whether the player-facing finish is visually acceptable.

| Problem | Evidence | State |
|---|---|---|
| Tracked weapon textures/materials exist | Git-tracked A-series feature assets; detailed snapshot in `Docs/evidence/asset_inventory_20261001.md` | Present for all seven named variants; runtime assignment and visual finish not comprehensively audited |
| A88 source/material setup was previously reported with five ADFRC texture slots | Session 090 `Build/weapons_setup.json` and original notes | Historical evidence only; not independently verified as the current runtime material graph in this review |
| Weapon meshes read as flat/untextured in game | Producer screenshot | Visual finish remains unverified in current builds |
| Normal/roughness/AO/metalness coverage on ADFRC-derived maps | Prior pack/source inspection (M-008l) | Material-channel coverage still needs review; tracked imports alone do not establish correct channel binding |
| `WID_SS_*` definitions are copies of Lyra's | Prior `strings` scan of `WID_SS_A88.uasset` | Historical baseline; see §5, verify current authored ballistics before implementation |

**Next: audit the active weapon material graphs before choosing a fix.** Confirm the mounted mesh/material
for each weapon in a current build, record bound texture channels and capture the player-facing result.
Only then decide whether to reuse a project-owned master material, adjust existing imported maps, or
create missing project-authored channels. Do not assume a channel is missing or prescribe a vendor-texture
replacement from repository counts alone.

---

## 4. Priority 3 — VFX

**State: casing eject and muzzle light are implemented; the visible flash integration is not confirmed.** A code-driven muzzle light is not the same as a Niagara/sprite flash. The asset scan found Lyra's `/Game/Effects/Particles/Weapons/NS_WeaponFire_MuzzleFlash_Rifle` candidate and a shotgun tracer candidate, but the reviewed records do not prove either is attached to the current A-series weapon in game.

| Effect | State | Next |
|---|---|---|
| Casing eject (`SSShellEjectSubsystem`) | In, tested (`SouthernSpear.Bridge.Casings.*`, 2 tests) | — |
| Muzzle light (`SSMuzzleLightSubsystem`) | In, tested (1 test) | — |
| **Muzzle flash** | Candidate exists at `/Game/Effects/Particles/Weapons/NS_WeaponFire_MuzzleFlash_Rifle`; current player-facing integration is unverified. The fire-cue alignment and code-driven muzzle light are separate systems. | Confirm the mounted effect per weapon in a current build; capture, then tune scale/intensity. |
| Impacts | `NS_ImpactConcrete`, `NS_ImpactGlass`, `NS_ImpactDataChannel`, `NS_ImpactDecals` present | Verify each surface type has a real impact; add dirt/sand/rock for the Dry River palette |
| Tracers, dust, weather | Lyra shotgun tracer Niagara candidate exists; no A-series tracer integration is verified. Dust/weather remain `PLACEHOLDER` in `ASSET_REGISTER` §4.7. | Verify the candidate is appropriate for rifle fire; implement/capture a player-facing tracer before calling it done. |

**Tracers are the notable gap for a shooter.** A tracer is what makes a 300 m shot legible to a player, and
`ASSET_REGISTER` E-002 still reads `PLACEHOLDER`. At Dry River's engagement ranges it matters more than at
close quarters.

---

## 5. Priority 4 — Weapon zeroing and recoil, from real data

This is the area with **no measured zero-distance or recoil-tuning baseline**, so it gets the most detail. Existing RPM, magazine, spread and map-playability values are summarized as separate evidence in §5.2–§5.3.

### 5.1 What "zeroing" means here, precisely

Two different things get called zeroing. Both are wanted; they are separate systems:

1. **Weapon zero (sight alignment)** — the sight is aligned to the bore at a stated distance, so the
   point of aim and the point of impact coincide there. Real weapons have a zero set by the shooter or
   the unit. In game this is one number per weapon: the range at which the crosshair is true. It is a
   property of the *weapon and its optic*, not of the player.
2. **Zeroing in (player-adjustable)** — letting the player dial the optic to a range. Nice to have; it is a
   UI and state problem on top of (1), and it is not first.

3. **Recoil** — the muzzle climb per shot and how fast the sight comes back down. This is what the player
   feels and what the numbers in §5.3 feed.

### 5.2 Current implementation baseline (source/config review, 2026-10-01)

Session 090's `strings` scan is historical and is superseded for the current weapon-stat baseline by `Config/DefaultGame.ini` and `USSWeaponStatsSubsystem`. Project settings contain rows for the named A-series variants; when a configured weapon instance is encountered, the bridge applies magazine size, spare ammunition, spread scale and configured rounds-per-minute. A stats row alone does not establish that a weapon is loaded or used (notably A417; see §5.3). The bridge sets `FireDelayTimeSecs` from RPM, but explicitly does **not** enforce `bFullAuto=false`; zero-distance alignment and a separate recoil-tuning system are not established by this code/config review. Re-run the in-game probe and shot-timing/capture checks before claiming runtime behavior or visual results.

### 5.3 Source data and what it can support

Keep these three evidence types separate: (a) ADFRC config values transcribed in `WEAPON_SOURCE_DATA`, (b) public manufacturer/service specifications for particular variants and ammunition, and (c) Southern Spear tuning choices. None is a measured in-game recoil profile or a verified sight zero.

| In-game name | In-repo source configuration (not an independent service spec) | Public spec useful for context | Boundary / next check |
|---|---|---|---|
| **A88 / A88G** | ADFRC EF88 config: 682 rpm; 30-round ADFRC magazine class | Australian Army F88 page reports 930 m/s muzzle velocity, 30 rounds, 300 m effective range and 680–850 rpm | The official page is F88 data; do not silently treat every F88 figure as an exact EF88/A88 configuration. Confirm selected variant/ammunition before importing velocity or range. |
| **A89** | ADFRC Minimi config: 750 rpm; named 200-round 5.56 magazine | Australian Navy F89A1 page reports 700–1,000 rpm and 400 m point / 600 m area effective ranges; feed options include 100/200 rounds | Range describes effective engagement, not the sight's zero. The in-repo config and official variant specs differ in scope. |
| **A4** | ADFRC M4A5 config: 857 rpm; 30-round PMAG | Generic M4 figures vary with exact model, barrel and cartridge; do not carry over an unspecific range/velocity as fact | Pin the game's intended model and cartridge before adding external ballistics. |
| **A416** | ADFRC HK416 config: 857 rpm; 30-round PMAG | HK's current HK416 page reports 850 rpm, 790 m/s and 1,250 J (DM11 ammunition); effective main combat range 450 m and accurate suppressive fire 600 m | Manufacturer figures are variant/ammunition-specific and differ from the ADFRC config rate; retain both provenance sources rather than averaging them. |
| **A25** | ADFRC SR-25 config: semi-auto, 600 rpm cyclic figure, 1.5 MOA dispersion; no magazine declared in the extracted config | No matching product/variant spec verified in this review | Do not infer capacity, zero or recoil from the source class name. |
| **A9** | ADFRC G19 config: semi-auto, 600 rpm cyclic figure, 8.59 MOA dispersion; no magazine declared in the extracted config | No exact game-variant spec verified in this review | The project config currently supplies gameplay magazine data separately; it is not source evidence. |
| **A417** | Present in the ADFRC source-data registry (20-round magazine class; 857 semi / 600 full-auto values) | Has a project `SSWeaponStatsSettings` row but no tracked A417 Game Feature weapon root or configured loadout was identified in the 2026-10-01 inventory | Confirm whether A417 should be a future/active weapon; a stats row alone does not establish an imported weapon or runtime use. |

Sources checked: Australian Army F88 page (930 m/s, 30-round capacity, 300 m effective range, 680–850 rpm); Australian Navy F89A1 page (700–1,000 rpm, effective ranges and feed options); Heckler & Koch HK416 product page (790 m/s, 1,250 J with DM11, 850 rpm, 450 m main combat / 600 m suppressive). In-repo configuration readings are documented in `Docs/WEAPON_SOURCE_DATA.md` and `.json`.

**No zero-distance table is established by these figures.** Effective range is not a sight zero. In particular, the old proposal to set zero distances equal to the public effective ranges was unsupported and is withdrawn. Choose the in-game sight/optic and weapon variant first, then obtain a source-specific zero or explicitly treat the selected range as an original game-design value. Likewise, muzzle energy alone does not determine camera recoil; cartridge, weapon mass, operating system, recoil impulse, muzzle device and the desired game feel all matter.

### 5.4 What the data supports for game feel

1. **A89 feed/capacity differentiates its role.** The source config names a 200-round magazine and the official F89A1 source lists 100/200-round options; use the actual game loadout/config capacity and handling mode. Do not infer that its per-shot recoil must match or exceed A88 from its LMG role alone.
2. **A88 and A88G have matching RPM, magazine, spare-ammo and spread-scale rows in project config.** The ADFRC registry distinguishes the grenade-launcher variant; confirm active weapon IDs and in-game behavior before claiming full gameplay parity or that they differ only cosmetically.
3. **Rate-of-fire figures are cyclic/source figures, not a complete game tuning prescription.** They can inform the chosen fire delay, but confirm each active weapon's current config and measured shot timing; semi-auto ability enforcement is explicitly incomplete in the current bridge implementation.
4. **Effective range is not damage falloff or zero distance.** Keep published descriptions separate from projectile simulation and optic alignment. Long sightlines should be designed and balanced by map playtest, not inferred solely from a weapon's effective-range label.

### 5.5 What real-world numbers can and cannot establish

**Free-recoil energy is not a game recoil value, and the specifications listed above do not rank camera recoil.** The checked sources provide some variant- and ammunition-specific rates, velocities, capacities, effective ranges and dispersion; they do not provide a verified recoil impulse/profile or a sight zero for every in-game weapon. Do not infer recoil direction, relative kick or zero distance from effective range, muzzle energy, weapon role or a source-class name.

The old 300 / 400–600 / 500 / 400 m proposal copied effective-range figures into a sight-zero table and is withdrawn. Confirm exact weapon variant, ammunition and optic, then use a source-documented zero only where one is actually found; otherwise record the zero as a game-design choice. Tune camera climb and recovery with measured shot traces and playtests, separately from sourced constraints.

### 5.6 Where the numbers have to live

For configured weapon instances, the current project applies magazine size, spare ammo, spread scale and configured rounds-per-minute through `SSWeaponStatsSettings` in `Config/DefaultGame.ini` and `USSWeaponStatsSubsystem`; a row does not prove a weapon is active, and `bFullAuto=false` is not yet enforced. There is no verified zero/recoil tuning implementation in this inventory. Add future tuning to project-owned config/data and tests—never patch vendored Lyra assets—and keep it distinct from source reference data. (The former `FSSWeaponBallistics`/material-override recommendation was not the implemented project path.)

---

## 6. Priority 5 — Maps

**State: asset dressing has advanced, but map readiness is not complete.** Dry River's Session 088 pass is measured construction, not producer sign-off; the playability audit still scores it 3 pass / 6 fail. Red Gum is not playable at its measured 17% nav coverage and 12 hard / 0 soft cover. Wandarra and Ravenshoe still need their attended R-82 nav bake, and Wandarra also has outstanding look/fit inspection. Saltbush is the strongest of the audited maps, not a finished or signed-off map.

| Map | State | Gated on |
|---|---|---|
| Dry River (M-001) | Session 088 dressing pass measured; playability audit remains 3 pass / 6 fail. Kangaroo material appearance and creek-water appearance still need in-game visual confirmation | Playability fixes plus visual review; do not call the overhaul complete |
| Red Gum (M-002) | `MAPS_PLAYABILITY_AUDIT.md`: 17% nav coverage, 12 hard and 0 soft cover — not playable as measured | Substantial playability/cover and navigation work; not merely art polish |
| Wandarra (M-009) | Built and dressed; saved nav coverage is 0 until attended bake; visual look/fit inspection remains open | **R-82** attended bake; also close R-89/R-90 inspections |
| Ravenshoe (M-008) | Built and dressed; navigation not baked | **R-82** attended bake; map playability still requires validation |
| Bluestone (M-005) | Built and on the operations menu; no playability audit or design sign-off identified | Audit and fine-tune |
| Saltbush (M-004) | Strongest of the four audited maps (7 pass / 3 fail), but still has measured failures | Resolve remaining audit failures and playtest |

R-82 is the attended-editor constraint for maps whose saved nav data is missing; headless `BUILDPATHS` consumes no new geometry on this machine. The map-specific table separates that bake from other playability and visual work.

---

## 7. What is NOT on this list, and why

- **Casualty care (ADR-040).** Steps 1–2 are built and passing; step 3 is the Lyra bridge and it is
  blocked on reading the 5.8 Lyra source first (prompt C in the handover). Real work, but it is a
  *feature*, not a defect, and the producer's verdict was about how the game *looks and feels*.
- **Dedicated server (R-09).** Blocked on the engine distribution. Not actionable.
- **Map readiness.** Geometry/dressing and navigation remain distinct from asset art polish: playability audit findings remain open on Dry River and Red Gum, while Wandarra and Ravenshoe need the attended R-82 nav bake.
- **Asset permission holds.** None for assets acquired/held for Southern Spear's free-to-play game: the producer reaffirmed ADR-028/035 on 2026-10-01. Keep provenance, seller flags and credits as bookkeeping; this is project-specific, does not authorize raw vendor-source redistribution, and does not make the local cache equivalent to shipped/game-used assets. See `ASSET_REGISTER.md` §§4.9m–4.9o.

---

## 8. One-page order of work

1. **Audit and visually verify the tracked weapon materials/textures** — assets exist in the A-series feature folders, but current runtime selections and visible finish still need a measured check. Choose a material or texture fix only after that audit.
2. **Muzzle flash + impacts + tracers** — verify the existing candidates in a current game build; integrate/capture the rifle flash and tracer that actually render.
3. **Weapon zero/recoil** — first confirm active weapon IDs, exact optic/variant, source figures and current implementation; do not equate effective range with zero. Add project-owned tuning and calibrate recoil by measured shot traces and playtest.
4. **R-82 attended nav bake** — bake and verify saved navigation for Wandarra and Ravenshoe; Red Gum's measured 17% coverage needs its own substantive nav/playability correction, not merely a declaration that the bake is done.
5. **Character P1–P5** — in parallel, owned by the character thread; do not duplicate that work.
6. **Dry River playability and visual verification** — fix the measured audit failures and confirm kangaroo and water appearance in game.

---

## 9. Sources

- Australian Army, *F88 Austeyr* — `https://www.army.gov.au/equipment/small-arms/f88-austeyr`
- Australian Navy, *F89A1 Minimi* — `https://www.navy.gov.au/capabilities/weapons/f89a1-minimi`
- Heckler & Koch, *HK416* — `https://www.heckler-koch.com/en/Products/Military%20and%20Law%20Enforcement/Assault%20rifles/HK416` (variant/ammunition footnotes apply)
- In-repo ADFRC config extraction — `Docs/WEAPON_SOURCE_DATA.md` / `.json` (source-config values, not independent published specifications)
- In-repo: `Docs/PLAYER_MODEL_PLAN.md`, `Docs/ASSET_REGISTER.md` §4.7 and M-008l,
  `Docs/evidence/vfx_muzzle_candidates.json`, `Docs/MAPS_DRYRIVER.md`, `Docs/PROJECT_AUDIT.md`,
  `Build/weapons_setup.json`

**Real names are used deliberately** (ADR-035, ADR-034): EF88, F89, M4 and HK416 are all named in
`CLAUDE.md` as permitted, and the in-game A-series names map to them. The ADF is not endorsed by this
project and no Commonwealth emblem or insignia is reproduced.