# MAP NOTE — Training environment (M-006 candidate): the downloaded MOUT urban kit

**Document ID:** `Docs/MAPS_TRAININGRANGE.md`
**Status:** Historical candidate note — MOUT is now adapted into Wandarra (M-009); this document's pre-decision proposal is not current map status.
**Last updated:** 2026-10-01 (historical status reconciled)

> **Current state:** the producer selected a large urban training map on 2026-09-29. MOUT assets, RustyCarsFree wrecks and EuropeanBeech trees are used in the built Wandarra map. Wandarra's current build/verification status is in `MAPS_WANDARRA.md`; its attended nav bake (R-82), look review (R-89) and fit inspection (R-90) remain open. M-006 remains the separate open-range/training-range question. Sections below preserve the earlier candidate assessment and must not be read as saying MOUT is unopened or M-009 does not exist.
**Source:** Fab pack staged at `Content/Downloaded/VaultCache/ModularM6dfea54fd98cV5/`, installed to `Content/MOUT_Civilian/`

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army. Any Southern Spear location built on this kit is an **invented** location, laid out from gameplay requirements, and must not reproduce a real base, installation or any operationally useful site.

---

## 1. What this note originally recorded

The following describes the producer request and inventory as recorded on 2026-09-29; it is historical context, not the current project/map state. The later producer decision selected Wandarra (M-009) as the urban training map, while M-006 remains a separate open-range/training-range scope question.

This original 2026-09-29 intake snapshot recorded what was on disk and the then-open M-006 question. It was deliberately *not* a map design and accurately noted that the kit had no project-authored layout, objective scheme, scale or site dimensions at that point. Wandarra (M-009) was designed and built later; its current implementation and verification are documented in `MAPS_WANDARRA.md`.

The intake was originally linked to the then-existing M-006 Training range placeholder. `DEVELOPMENT_ROADMAP.md` VS-17 asks for *"Training range + one qualification that saves"*, while GDD §5 makes training a core progression system in five modules. The producer later selected MOUT for Wandarra (M-009); whether M-006 remains a separate open firing range or changes scope is still unresolved.

---

## 2. What arrived

Measured on disk, 2026-09-29 (`du`, `find`, `ls`; commands in §8):

| Property | Value |
|---|---|
| Staging folder | `Content/Downloaded/VaultCache/ModularM6dfea54fd98cV5/` — written 09:13–09:16 |
| Installed to | `Content/MOUT_Civilian/` — **untracked**; raw packs stay git-ignored (ADR-021, R-14) |
| Size | **2.1 GB**, **507 files** (504 `.uasset`, 3 `.umap`) |
| Authoring engine | **UE 4.26** — `++UE4+Release-4.26` in the map header. Opened by 5.8, so every asset is upconverted on load |
| `metadata` sidecar | **absent** — `find -iname metadata` over the whole pack returns nothing, so seller and `isAiForbidden` are **unverified**, not known-good (L-0016c standing action) |
| External actors | none — `__ExternalActors__` is empty, so all geometry lives inside the maps themselves |

Three maps shipped with it:

| Map | Size | What it is |
|---|---|---|
| `/Game/MOUT_Civilian/Demo/FirstPersonBP/Maps/FirstPersonExampleMap` | 8.5 MB (+ 14 MB `_BuiltData`) | the pack's demo urban block, walked in first person |
| `/Game/MOUT_Civilian/Maps/LVL_AssetShowcase` | 200 KB | asset showcase |
| `/Game/MOUT_Civilian/Maps/LVL_Blueprints` | 465 KB | blueprint showcase |

`FirstPersonExampleMap` was the only environment map added to `Content/` in the 2026-09-29 intake snapshot. Subsequent work built Wandarra from selected MOUT kit assets; see `MAPS_WANDARRA.md`.

---

## 3. What is in the kit

- **Three modular mesh sets**: `Meshes/ModularAssets/BuildingKit`, `ChurchKit`, `AwningKit`
- **Thirteen prop sets** (`Materials/Props`): Bollards, BusStop, ClothesLine, ElectricityPole, Fencing, FireHydrant, Flag, Fountain, ParkBench, Playground, PoliceSign, PostBox, TrashCans
- **Buildings as blueprints**: `BP_Bungalow` ×3, `BP_House` ×2, `BP_GovernmentBuilding_01`, plus government awnings and electricity poles with cable structs
- **Interactable doors**: `BP_GlassDoors_Interactable`, `BP_GreenDoors_Interactable`, `BP_WoodenDoor_Interactable`, and matching `*_IndividualDoorOpening` variants — the only **game** content in the pack rather than scenery, and the one thing here that may be worth more than the buildings
- **219 textures**, and a first-person demo character and weapon under `Demo/`

**MOUT** is the vendor pack's own abbreviation for **Military Operation Urban Training**. This is the pack's stated purpose; Wandarra's current role and design are described in `MAPS_WANDARRA.md`, not inferred solely from the vendor demo map.

---

## 4. Historical candidate uses (pre-Wandarra decision)

### 4.1 As `M-006` Training range — a partial fit, and the partial matters

The register and the roadmap both say "training range". Read strictly, that is **open ground with long lanes**: it is the Marksman qualification (GDD §5 module 2) that needs lane-and-sightline geometry, and the project's open-range map already exists — Saltbush was built precisely "to test engagement ranges past 200 m".

**Historical assessment (2026-09-29):** the vendor kit itself is an urban village, not an open firing range; that remains a distinction about the pack's assets, not the current project state. Wandarra uses the urban kit; M-006's separate open-range scope remains unresolved.

What it *does* answer, better than anything else in the project:

| GDD §5 module | Fit | Why |
|---|---|---|
| 1. Induction | **Good** | Doorways, rooms, awnings, awning-to-ground transitions — close-quarters movement and doorway handling, which is the first thing a new player has to learn and the hardest thing to teach on open ground |
| 2. Weapons Qualification | **Partial** | Fine for the close-range half (controlled pairs, supported firing). Marksman lanes have to come from Saltbush or a purpose-built range |
| 3. Support Weapons | **Partial** | Bipod arcs want open lanes; suppression wants something to suppress *behind* |
| 4. Field Skills | **Good** | Identification training is explicit in the GDD, and a village of lookalike buildings and doors is exactly where silhouette-and-insignia reading gets tested. Cover and routes exist in quantity |
| 5. Leadership | **Weak** | Needs observable squads and clear approaches over distance |

**Historical verdict (superseded for map selection):** this was a strong urban/close-quarters candidate and a poor literal open-range fit. The producer subsequently selected the urban use as Wandarra (M-009); M-006 remains a separate training-range decision.

### 4.2 As an additional playable map

Historical candidate assessment (2026-09-29, before Wandarra was built): the kit appeared to offer a second urban environment alongside Selat Canal (M-003). The producer subsequently selected that urban use as Wandarra (M-009), which now exists; the remaining concerns are current validation items listed in `MAPS_WANDARRA.md`.

- **Historical concerns, retained for context:** the kit's look and the absence of a project-authored layout were open questions before the producer's map decision. Wandarra is now built; its ADR-016 look review (R-89), fit inspection (R-90), nav bake (R-82), spawn layout and playability checks remain open, as recorded in `MAPS_WANDARRA.md`. Do not infer that those gates were already completed from the 2026-09-29 candidate review.

---

## 5. Provenance and licence

| Field | Value |
|---|---|
| Source | Fab (fab.com), downloaded through the Epic Games Launcher into `Content/Downloaded/VaultCache/` |
| Observed seller terms | Not verified from the local Vault chunk; do not assign a blanket Fab class |
| Project-use status | Producer-cleared for Southern Spear's F2P game under ADR-028/035, including acquired/held content; this project-specific direction is distinct from unverified local listing metadata |
| Seller | **Unverified.** The Vault pack wrote no `metadata` sidecar, so the listing it came from is not identifiable from local files. Recorded as unverified, never as clear |
| `isAiForbidden` | **Unverified** — same reason. This is a seller declaration, not a licence field (L-0016c) |
| Redistribution | Stays git-ignored (ADR-021, R-14). Project assets reference pack content **by path**; vendor assets are never modified in place |

Register rows were added **in the same change** as this note, per the L-0016b standing action: `LICENCE_REGISTER.md` (L-0016 table) and `ASSET_REGISTER.md` §4.9j.

---

## 6. Historical open questions (superseded by the 2026-09-29 producer decision)

1. **Historical range/village choice:** resolved for the urban map by the producer's selection of Wandarra (M-009). M-006 remains a separate open-range/training-range scope question.
2. **Historical map-ID question:** M-009 was subsequently opened and built as Wandarra; the no-layout/no-name concern no longer applies.
3. **Historical map-name question:** resolved as Wandarra, an invented locality; see `MAPS_WANDARRA.md`.
4. **Historical intake disposition:** the pack's `Demo/` tree was not selected for Wandarra or the current player/weapon path. This is a scope/use choice, not a prohibition on producer-cleared acquired content; preserve the distinction between vendor demo assets and the assets actually selected for the game.
5. **Door Blueprints:** their port/use remains unscoped; no current gameplay interaction is claimed in Wandarra (ADR-041). This is a feature decision, not a permission hold.

---

## 7. Risks raised by this note (historical; current status in PROJECT_AUDIT and MAPS_WANDARRA)

| ID | Risk | Note |
|---|---|---|
| **R-67** | The kit was authored in **UE 4.26** and loaded under 5.8. First load in the Wandarra build was silent (zero upconversion/redirect error lines); rendered texture survival, LOD, lightmap/texel density and draw cost remain unmeasured | First-load half measured; render-cost half remains open |
| **R-68** | Seller and `isAiForbidden` **unverified** for the whole 2.1 GB pack (no `metadata` sidecar) | Same class of residual risk as L-0016c. ADR-028/ADR-035 decide the licence; this is bookkeeping, and an absent sidecar is recorded as unverified |

Neither risk is a project-use permission hold under ADR-035. The first-load upconversion has since been measured as silent; remaining rendered texture/LOD/draw-cost checks are tracked under R-67, while current map status is in `MAPS_WANDARRA.md`.

---

## 8. How to re-verify the historical intake measurements

```bash
du -sh Content/MOUT_Civilian                                    # 2.1 GB
find Content/MOUT_Civilian -type f | wc -l                      # 507
find Content/MOUT_Civilian -type f | sed 's/.*\.//' | sort | uniq -c   # 504 uasset, 3 umap
find Content/MOUT_Civilian -iname "*.umap" -printf "%s %p\n"   # the three maps
find Content/Downloaded/VaultCache/ModularM6dfea54fd98cV5 -iname metadata   # empty -> absent
strings -n 4 Content/MOUT_Civilian/Demo/FirstPersonBP/Maps/FirstPersonExampleMap.umap | head
git status --porcelain                                          # Content/MOUT_Civilian/ is untracked
```

**Historical measurement boundary (2026-09-29):** the initial intake note did not open any of the three vendor maps or inspect a rendered scene. Subsequent Wandarra level/dressing and first-load checks are recorded in `MAPS_WANDARRA.md` and PROJECT_AUDIT R-67. No final attended visual sign-off, full texture/LOD/draw-cost assessment or nav bake is claimed by this note.
