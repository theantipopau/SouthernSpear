# MAP NOTE — Training environment (M-006 candidate): the downloaded MOUT urban kit

**Document ID:** `Docs/MAPS_TRAININGRANGE.md`
**Status:** Note — downloaded and installed, **not adapted, not opened, not measured**
**Last updated:** 2026-09-29
**Source:** Fab pack staged at `Content/Downloaded/VaultCache/ModularM6dfea54fd98cV5/`, installed to `Content/MOUT_Civilian/`

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army. Any Southern Spear location built on this kit is an **invented** location, laid out from gameplay requirements, and must not reproduce a real base, installation or any operationally useful site.

---

## 1. What this note is

The producer asked for a note that a training environment map had been downloaded, that it can stand as an additional map for the game, and that it is probably the environment the training missions will use later.

This records **what is on disk, what it is, and what is not decided**. It is deliberately *not* a map design: there is no layout, no objective scheme, no scale and no numbers here, because none have been authored. The other `MAPS_*.md` documents earn their dimensions by stating the gameplay reason for each one. Nothing in this kit has earned a dimension yet.

The register already carries the destination this is aimed at:

| Register ID | Map | Layers required | Status | Notes |
|---|---|---|---|---|
| `M-006` | **Training range** | Training | `PLACEHOLDER` | Vertical slice |

and `DEVELOPMENT_ROADMAP.md` VS-17 asks for *"Training range + one qualification that saves"*, while GDD §5 makes training a core progression system in five modules. Section 4 is about whether this kit should fill `M-006` as written, or sit beside it.

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

`FirstPersonExampleMap` is **the only environment map added to `Content/` on 2026-09-29**. Everything else downloaded that day was either props (rusty cars) or architecture/prop kits that have not been added to `Content/` at all.

---

## 3. What is in the kit

- **Three modular mesh sets**: `Meshes/ModularAssets/BuildingKit`, `ChurchKit`, `AwningKit`
- **Thirteen prop sets** (`Materials/Props`): Bollards, BusStop, ClothesLine, ElectricityPole, Fencing, FireHydrant, Flag, Fountain, ParkBench, Playground, PoliceSign, PostBox, TrashCans
- **Buildings as blueprints**: `BP_Bungalow` ×3, `BP_House` ×2, `BP_GovernmentBuilding_01`, plus government awnings and electricity poles with cable structs
- **Interactable doors**: `BP_GlassDoors_Interactable`, `BP_GreenDoors_Interactable`, `BP_WoodenDoor_Interactable`, and matching `*_IndividualDoorOpening` variants — the only **game** content in the pack rather than scenery, and the one thing here that may be worth more than the buildings
- **219 textures**, and a first-person demo character and weapon under `Demo/`

**MOUT** is the vendor pack's own abbreviation for **Military Operation Urban Training** — a kit for building an urban training facility, of which the demo map is one already built. That is the whole reason it reads as a training environment rather than a town: it is not a town kit that happens to be quiet, it is a facility kit with lanes, walls and cover built in the shapes training layouts use.

---

## 4. The two candidate uses

### 4.1 As `M-006` Training range — a partial fit, and the partial matters

The register and the roadmap both say "training range". Read strictly, that is **open ground with long lanes**: it is the Marksman qualification (GDD §5 module 2) that needs lane-and-sightline geometry, and the project's open-range map already exists — Saltbush was built precisely "to test engagement ranges past 200 m".

**This kit is a village, not a range.** It has no long lanes, no berms, no safe backstop, no lane markers. On its own it does not answer VS-17's "training range".

What it *does* answer, better than anything else in the project:

| GDD §5 module | Fit | Why |
|---|---|---|
| 1. Induction | **Good** | Doorways, rooms, awnings, awning-to-ground transitions — close-quarters movement and doorway handling, which is the first thing a new player has to learn and the hardest thing to teach on open ground |
| 2. Weapons Qualification | **Partial** | Fine for the close-range half (controlled pairs, supported firing). Marksman lanes have to come from Saltbush or a purpose-built range |
| 3. Support Weapons | **Partial** | Bipod arcs want open lanes; suppression wants something to suppress *behind* |
| 4. Field Skills | **Good** | Identification training is explicit in the GDD, and a village of lookalike buildings and doors is exactly where silhouette-and-insignia reading gets tested. Cover and routes exist in quantity |
| 5. Leadership | **Weak** | Needs observable squads and clear approaches over distance |

**Verdict as written:** this is a strong candidate for an **urban / close-quarters training map**, and a weak candidate for the "training range" that VS-17 literally asks for. Whether `M-006` is redefined from range to urban-training, or this becomes a second training map beside it, is a producer decision and is left open in §6.

### 4.2 As an additional playable map

It qualifies, with caveats. The project already has one urban map (Selat Canal, M-003) and it is the only Special Forces map; this kit's close-quarters geometry would be a second urban environment with a different character — a civilian town against Selat Canal's canal district. The obstacles are the same ones that apply to §4.1 plus one more:

- **ADR-016 look check not done.** A church, a playground, police signage, bus stop, clothes lines and a European-influenced bungalow/terrace vernacular are not Southern Spear dressing by default. Singapore Canal was held back from the game for exactly this reason (see `LICENCE_REGISTER.md`, Singapore Canal row). The check has to happen **before** anything here is placed, not after.
- **No original layout exists.** Nothing here has been laid out by us, and a map is not a kit — it is a kit plus a layout, objectives, deployment, cover audit and a navmesh.

---

## 5. Provenance and licence

| Field | Value |
|---|---|
| Source | Fab (fab.com), downloaded through the Epic Games Launcher into `Content/Downloaded/VaultCache/` |
| Licence | **Fab Standard License — Class A**, as for every other Fab pack in this project (L-0016) |
| Clearance | **Already cleared.** ADR-028 clears Fab assets; ADR-035 clears them for the free product, including converted and derived work. **No licence check holds this up** |
| Seller | **Unverified.** The Vault pack wrote no `metadata` sidecar, so the listing it came from is not identifiable from local files. Recorded as unverified, never as clear |
| `isAiForbidden` | **Unverified** — same reason. This is a seller declaration, not a licence field (L-0016c) |
| Redistribution | Stays git-ignored (ADR-021, R-14). Project assets reference pack content **by path**; vendor assets are never modified in place |

Register rows were added **in the same change** as this note, per the L-0016b standing action: `LICENCE_REGISTER.md` (L-0016 table) and `ASSET_REGISTER.md` §4.9j.

---

## 6. What is not decided

1. **Range or village?** Whether `M-006` stays an open firing range, or is redefined as an urban training facility with a separate range later. Producer's call.
2. **No new map ID was opened.** The register's layout rule and the VS-17 line both assume one training map. Opening `M-009` here would commit the project to a map that has no layout, no author and no agreed name. `M-006` is left as it stands and this note records the candidate against it.
3. **No Southern Spear name.** Map docs are named after their in-fiction location (Dry River, Red Gum, Saltbush, Selat Canal, Ravenshoe). This has none, and inventing one is a design decision, not bookkeeping. When a name is chosen it must be an invented Australian location and must not describe a real facility. No `L_*` map asset has been created.
4. **The pack's `Demo/` tree is reference-only.** Its first-person character and weapon must not enter the game: weapons are script-built on Lyra sockets and gear is skinned to the Lyra mannequin (ADR-020), and the soldier bodies are Quantum/Modern Insurgent. Anything else would be a second, conflicting weapon path.
5. **Whether the doors are worth the port.** They are the only interactive content in the pack, and they may be worth more to the training design than the buildings are — but they are vendor Blueprints with no owner, and ADR-004 keeps presentation out of gameplay. Not scoped.

---

## 7. Risks raised by this note

| ID | Risk | Note |
|---|---|---|
| **R-67** | The kit was authored in **UE 4.26** and has never been opened in 5.8. 2.1 GB, 219 textures, unknown LOD policy, legacy materials, `EngineSky` sky sphere in the demo map. Nothing here has been measured — nav coverage, texel density, lightmap or draw cost are all unknown | New. Raised, not assessed |
| **R-68** | Seller and `isAiForbidden` **unverified** for the whole 2.1 GB pack (no `metadata` sidecar) | Same class of residual risk as L-0016c. ADR-028/ADR-035 decide the licence; this is bookkeeping, and an absent sidecar is recorded as unverified |

Neither is a blocker for reading the kit, and neither should hold up a decision about whether to design on it. They are recorded because the alternative — a 2.1 GB unreviewed pack with an unidentified seller sitting in `Content/` — is exactly the gap L-0016b was found and closed for.

---

## 8. How to re-verify every number above

```bash
du -sh Content/MOUT_Civilian                                    # 2.1 GB
find Content/MOUT_Civilian -type f | wc -l                      # 507
find Content/MOUT_Civilian -type f | sed 's/.*\.//' | sort | uniq -c   # 504 uasset, 3 umap
find Content/MOUT_Civilian -iname "*.umap" -printf "%s %p\n"   # the three maps
find Content/Downloaded/VaultCache/ModularM6dfea54fd98cV5 -iname metadata   # empty -> absent
strings -n 4 Content/MOUT_Civilian/Demo/FirstPersonBP/Maps/FirstPersonExampleMap.umap | head
git status --porcelain                                          # Content/MOUT_Civilian/ is untracked
```

**What was not run:** the editor was not opened on any of the three maps, no map was loaded, no screenshot taken, no navigation built, no asset audited. Every statement about how the content looks or performs is therefore unverified, and is written above as a question rather than an answer.
