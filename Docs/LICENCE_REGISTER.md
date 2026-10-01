# LICENCE REGISTER — Southern Spear

**Document ID:** `Docs/LICENCE_REGISTER.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-10-01

> **Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army.**

---

## 0. Current position — ADR-035 (producer, reaffirmed 2026-10-01) — read this first

**Southern Spear is a free-to-play product. The producer confirms that assets held or acquired for this project are free to use in the game**: Fab (ADR-028), other acquired/free sources and the ADF Re-Cut pack (L-0021). This project-specific direction was reaffirmed on 2026-10-01. **Real names** — weapons, the Australian Army, ranks and insignia, ADF equipment and camouflage — are also allowed under ADR-035.

Where an entry below says *hold*, *prohibited*, *Class D/E* or *release blocker* solely because of a commercial or fiction-only reading, **ADR-035 supersedes it**. Those entries remain historical where useful and are corrected in their operative status. This direction is not a universal marketplace licence claim and does not authorize redistribution of raw source packs. It does not approve ripped commercial-game content (L-0007/L-0008), remove no-endorsement or content-ethics rules, waive applicable attribution/credit obligations, or reverse a specific producer-declined disposition such as Electric Dreams (ADR-013/L-0012) absent a new decision.

This register still does two jobs:
- It records **provenance and credits** (publisher, source, attribution) for the credits screen and CC BY lines.
- It records what stands for **non-licence reasons**: no endorsement claim; MAF portrayal (§5.3); no *America's
  Army* content (L-0008) and no ripped commercial-game assets (L-0007), because neither comes from a cleared source.

**R-57 (closed / producer-accepted under ADR-035):** the producer accepts use of acquired assets and marks in this project-specific F2P game. Retain available source/credit records and the no-endorsement statement. This entry creates no rename/swap, permission, legal-review or release gate.

---

## 1. Purpose

A single authoritative record of third-party dependencies, observed source/provenance, attribution obligations and project-use clearance. The producer's F2P clearance is recorded separately from the seller's published terms and local metadata; missing provenance is an inventory gap, not a permission hold under ADR-035.

### The rule

> **No third-party asset, plugin, library or code enters this repository without a row in this register.**

This is enforced in CI: a build fails if a new `.uasset`/`.umap` appears with no corresponding register entry.

### Marketplace metadata is not the producer's project-use decision

Marketplace price, seller metadata and missing sidecars are provenance observations. Under ADR-028/035, the producer clears acquired assets for Southern Spear's free-to-play game; preserve known attribution/credit and no-raw-source-redistribution rules. Do not generalize this project-specific direction into a universal licence claim or treat cache-only records as game-used assets.

---

## 2. Licence Compatibility Classes

| Class | Meaning | Register treatment |
|---|---|---|
| **A** | Seller/publisher terms documented as permitting the stated use without attribution | Record applicable terms and any limits |
| **B** | Seller/publisher terms documented with attribution required | Ship the required credit |
| **C** | Terms include share-alike or source-disclosure obligations | Record and satisfy the obligations |
| **D** | Terms state non-commercial / research / evaluation restrictions | Preserve as source metadata; producer's project-specific direction governs Southern Spear use |
| **E** | Source terms unclear or undocumented | Record the gap; not a project-use hold under ADR-035 |
| **F** | Original work created for this project | No third-party licence dependency |

These classes describe observed source terms/provenance; they do not override the producer's clearance for Southern Spear's free-to-play use. Credits, raw-source handling, no-endorsement and content ethics remain separately tracked.

---

## 3. Register

### L-0001 — Lyra Starter Game 5.8

| Field | Value |
|---|---|
| **Component** | Lyra Starter Game (source, plugins, content) |
| **Publisher** | Epic Games, Inc. |
| **Source** | Obtained via Epic Games distribution (Fab / Epic Games Launcher) for UE 5.8 |
| **Version** | 5.8 (`EngineAssociation: "5.8"`) |
| **Licence** | Unreal Engine EULA — as applies to samples/projects |
| **Class** | **B** — attribution required in shipping product |
| **Status** | Verified for internal development; **release packaging requires confirmation of the sample-content terms in force at release** |
| **Modifications** | Vendored into this repository; project renamed to `SouthernSpear`; Southern Spear plugins added. Lyra internal type names preserved (see TDD departure D-01) |
| **Attribution required** | Yes — "Lyra Starter Game, Epic Games" in credits |
| **Action** | Confirm sample-content redistribution and shipping terms before any public release |

> Lyra is used as an **architectural foundation**. Its art is not automatically classified as placeholder content: replace or retain each sample visual according to the shipping art plan. Confirm applicable Epic sample-content and EULA terms at release (separate from the producer's clearance for other acquired project assets).

### L-0002 — Unreal Engine 5.8.3

| Field | Value |
|---|---|
| **Component** | Unreal Engine 5.8.3 (Installed Build, `E:\Unreal\UE_5.8`) |
| **Publisher** | Epic Games, Inc. |
| **Licence** | Unreal Engine EULA |
| **Class** | **B** — royalty/attribution obligations apply per EULA |
| **Modifications** | **None.** Installed Build used as-is |
| **Action** | Track EULA obligations (royalty reporting, credit notice) in release planning |

### L-0003 — Rank insignia and unit insignia — producer-accepted; historical review record

> **ADR-035 (2026-09-28; reaffirmed 2026-10-01):** no project-use hold. Australian Army ranks and insignia may be used as directed, with the no-endorsement disclaimer maintained. The historical review below is not the current disposition.


| Field | Value |
|---|---|
| **Component** | RAN-style rank slides/slides, progression insignia, friendly and hostile unit insignia |
| **Publisher** | — |
| **Source** | To be created |
| **Historical source/licence fields** | The original review listed these as pending / Class E; superseded by ADR-035 for this project's use. |
| **Current status** | Producer-accepted for Southern Spear's free-to-play game; no per-asset permission hold. No endorsement is claimed. |
| **Current treatment** | No per-asset project-use hold under ADR-035. Keep the no-endorsement disclaimer and content-ethics rules; no independent pre-release legal-review/substitution gate is created by this historical entry. |

> The quoted restriction below is retained as historical record only and is not an operative project-use hold.

### L-0004 — Australian Defence Force / Australian Army name and marks — producer-accepted under ADR-035

> **ADR-035 (2026-09-28; reaffirmed 2026-10-01):** real names, ranks, equipment, insignia and camouflage are allowed in Southern Spear. Keep the no-endorsement disclaimer; this producer direction does not claim official sponsorship.

| Field | Value |
|---|---|
| **Component** | Use of "Australian Army", ADF insignia, service branding |
| **Historical source status** | No separate trademark/branding licence is recorded; this status does not prohibit the producer-directed project use under ADR-035. |
| **Current use status** | Producer-accepted for Southern Spear's free-to-play game; no endorsement is claimed. |
| **Rule** | The game must **not** present itself as endorsed, developed, sponsored or approved by the ADF, the Department of Defence or the Australian Army. Ship the fictional-work disclaimer and maintain the content-ethics rules. |

### L-0005 — Third-party audio

| Field | Value |
|---|---|
| **Component** | Weapon, impact, footstep, ambience and UI audio |
| **Status** | ADFRC AUG weapon audio is recorded under L-0021 and ASSET_REGISTER AUD-AUG-001; other audio sources are tracked as acquired. This row is not a claim that no third-party audio is in the project. |
| **Rule** | Producer-cleared acquired audio may be used for Southern Spear's F2P game under ADR-035. Preserve source/credit details. **No recorded real voice content.** Voice chat is never recorded without explicit per-player consent and a documented privacy design. |
| **Action** | Record new audio sources and applicable attribution in this register before use. |

### L-0012 — Electric Dreams environment (producer-declined — historical evaluation record only)

| Field | Value |
|---|---|
| **Component** | "Electric Dreams" environment pack, briefly staged outside the repository at `E:\Unreal\Environment\` |
| **Status** | **Producer-declined; excluded from this project absent a new producer decision** |
| **Import status** | **NOT IMPORTED** — no asset from this pack has entered the repository, project or build, per the recorded inventory |
| **Project disposition** | Excluded by explicit producer decision ADR-013; this is a project selection decision, not a general statement about its licence or a precedent for other acquired assets |
| **Licence/provenance** | Not read in the recorded evaluation; do not infer a class or universal restriction from the declined disposition |
| **Authoritative decision** | **ADR-013** — Electric Dreams was explicitly declined; third-party environment packs may otherwise be used under later producer directions such as ADR-028/035 |

**The specific declined disposition remains in force unless the producer changes it.** The older evaluation and wording are retained below as history; this row must not be generalized into a blanket rule against Fab/Vault or other acquired environments, which ADR-028/035 explicitly clears for this game.

**Current disposition:** do not use Electric Dreams in Southern Spear unless a new producer decision supersedes ADR-013. This is a scope-specific choice, not an inference from unread terms. Preserve original-map/layout requirements where they independently apply.

**Historical evaluation record (retained, non-authoritative).** Before the pack was
declined it was evaluated and recorded deliberately at class **E** with the note that
"free" is not a licence category and an unread licence is treated as prohibited. The
evaluation considered using it as a base map, and separately as a source of generic
modular pieces. Both were rejected in ADR-013 on originality grounds: the vertical slice
is to be built original, and a third-party environment's art direction cannot enter a
product that claims entirely fictional authorship. The pack was never imported and the
licence text was never read, because the decision was made before extraction was
necessary.

| Field | Value |
|---|---|
| **Action** | None. The pack is declined and unused. If it is ever revisited, it requires a **new** ADR superseding ADR-013, plus a full licence read, **not** a reclassification of this row. |

---

### L-0006 — Fab / Marketplace assets

> **Superseded by ADR-028 / ADR-035:** Fab assets acquired/held for Southern Spear are cleared for the F2P game; record observed provenance and credits (see L-0016, L-0023, L-0025).

| Field | Value |
|---|---|
| **Component** | Any asset acquired from Fab |
| **Status** | Multiple Fab/Fab-library and Vault assets are installed, cached or used; see ASSET_REGISTER §§4.9h–p and the current map dependency subset in PACK_MANIFEST. |
| **Tooling note** | PROJECT_AUDIT R-03 records Launcher/Fab in-editor availability limitations. They do not mean no assets were acquired and are not clearance holds. |
| **Action** | Record source/publisher/available credit information and distinguish cached, installed, referenced and game-used states. Producer direction clears project use; preserve raw-source handling and prohibited-source rules. |

### L-0007 — Prohibited sources (standing prohibition)

> **Narrowed by ADR-035:** real-world camouflage and real weapon models **from cleared sources** (Fab, ADFRC,
> free sources) are allowed. What stands: nothing **ripped** from commercial games or model-ripping sites, and
> no traced manufacturer CAD. Neither is a cleared source.

| Field | Value |
|---|---|
| **Component** | Manufacturer CAD, commercial game models, ripped assets, real-world camouflage textures |
| **Status** | ❌ **PROHIBITED SOURCE TYPES ONLY** |
| **Rule** | Do not use ripped commercial-game assets or trace/rip manufacturer CAD. Real-world names, equipment, camouflage and assets acquired/held for Southern Spear are producer-cleared under ADR-035; this is distinct from an asset ripped from a commercial game. |

### L-0008 — *America's Army 2* (standing prohibition)

| Field | Value |
|---|---|
| **Component** | Any content from *America's Army 2* |
| **Status** | ❌ **PROHIBITED** |
| **Rule** | No source code, map layouts, mission names, UI, audio, dialogue, artwork or proprietary assets. Southern Spear is an **original work** inspired by a design philosophy, not a derivative work. Every map layout, name, UI screen and asset must be demonstrably original |

### L-0009 — Epic Online Services (proposed, not yet integrated)

| Field | Value |
|---|---|
| **Component** | EOS SDK — authentication, lobbies, session discovery, invitations, player reports, cross-platform identity |
| **Publisher** | Epic Games, Inc. |
| **Licence** | EOS developer terms — **REVIEW REQUIRED** |
| **Class** | **E** — unresolved pending integration |
| **Status** | Evaluated, not integrated |
| **Rule** | The entire online-services layer sits behind `ISSOnlineSession`. EOS can be replaced or supplemented without touching gameplay code |

### L-0010 — C++ third-party libraries (none yet)

| Field | Value |
|---|---|
| **Component** | Any third-party C++ library added to `Source/` or a plugin |
| **Status** | **NONE** |
| **Rule** | Record each dependency's source, version, observed terms and attribution. Producer direction governs F2P project use for acquired assets; no raw-source redistribution, prohibited commercial-game rips, or unapproved paid dependencies. |

### L-0011 — Blender 5.2.2 LTS

| Field | Value |
|---|---|
| **Component** | DCC tool for original asset creation |
| **Publisher** | Blender Foundation |
| **Licence** | GPL v3 (the application) — output of a GPL tool is not subject to the GPL |
| **Class** | **F** for produced assets — our own work, no obligation |
| **Action** | Assets created in Blender are original work owned by this project. No entry needed per asset |

---

### L-0013 — Split Point, Victoria (Australia) — photogrammetry scan

| Field | Value |
|---|---|
| **Component** | Split Point, Victoria (Australia) — photogrammetry scan |
| **Author** | SAVollgger (Sketchfab) |
| **Source** | https://sketchfab.com/3d-models/d95f3ad4d0044c20a56ebb7bd507d515 |
| **Local copy** | `Content/Sourced/Environmental/splitpoint-victoria` (git-ignored until adapted) |
| **Licence** | CC Attribution 4.0 (read from the Sketchfab API, 2026-09-27) |
| **Class** | **B** — credit "Split Point, Victoria (Australia)" by SAVollgger, CC BY 4.0, in the shipping credits |
| **Status** | Cleared for use under ADR-021 as environment reference/dressing; layout stays original (ADR-013) |

### L-0014 — Bingie Bingie, NSW (Australia) — photogrammetry scan

| Field | Value |
|---|---|
| **Component** | Bingie Bingie, NSW (Australia) — photogrammetry scan |
| **Author** | SAVollgger (Sketchfab) |
| **Source** | https://sketchfab.com/3d-models/b3cdf8650ee44dd786f205c6c849ad59 |
| **Local copy** | `Content/Sourced/Environmental/bingie-bingie` (git-ignored until adapted) |
| **Licence** | CC Attribution 4.0 (read from the Sketchfab API, 2026-09-27) |
| **Class** | **B** — credit "Bingie Bingie, NSW (Australia)" by SAVollgger, CC BY 4.0, in the shipping credits |
| **Status** | Cleared for use under ADR-021 as environment reference/dressing; layout stays original (ADR-013) |

### L-0015 — Ross River, Northern Territory, Australia — scan

| Field | Value |
|---|---|
| **Component** | Ross River, Northern Territory, Australia — scan |
| **Author** | jack.simmons (Sketchfab) |
| **Source** | https://sketchfab.com/3d-models/baeea992de754e3c8c7dca203f1daa40 |
| **Local copy** | `Content/Sourced/Environmental/rossriver-nt (file named untitled.zip; match by title/size to be confirmed on import)` (git-ignored until adapted) |
| **Licence** | CC Attribution 4.0 (read from the Sketchfab API, 2026-09-27) |
| **Class** | **B** — credit "Ross River, Northern Territory, Australia" by jack.simmons, CC BY 4.0, in the shipping credits |
| **Status** | Cleared for use under ADR-021 as environment reference/dressing; layout stays original (ADR-013) |

## 4. Original Work (Class F)

Everything in this list is created specifically for Southern Spear and carries no third-party obligation. **A new class-F asset is not a licence event**, but it is still tracked in `ASSET_REGISTER.md`.

| Category | Examples |
|---|---|
| C++ source | All `SouthernSpear*` plugins and modules |
| Game design | All original mechanics, modes, maps, layers |
| Data assets | All `DF_SS_*` / `DT_SS_*` definitions |
| Weapon data | All tuning values; reference data is descriptive and separately sourced |
| Fiction | The hostile faction, its backstory, insignia, unit names |
| Original art | Characters, weapons, animations, VFX, UI, all created in Blender or UE |
| Audio | Recorded or synthesised for this project |
| Documentation | All files in `Docs/` |

---

## 5. Original-Fiction Constraints (not licence law, but binding)

Separately from copyright, the following are **hard constraints** on the fiction.

### 5.1 Fictional organisations (ADR-016)

Every organisation below is **invented for Southern Spear** and is not affiliated with,
endorsed by, or derived from any real body:

- **Commonwealth Defence Service (CDS)** — fictional
- **Commonwealth Land Service (CLS)** — fictional
- **Australian Commonwealth Regiment (ACR)**, incl. 1/3/5/7 ACR — fictional
- **2nd Commando Group (2 CG)** — fictional, and **not** the real 2nd Commando Regiment
- **Special Operations Regiment (SOR)** — fictional, and **not** the SASR
- **Murasian Armed Forces (MAF)** — fictional; not a real state, ethnicity, religion, political movement or contemporary armed group
- **Commonwealth Multi-Environment Combat Uniform (CMECU)** — an original fictional camouflage and uniform system

**No official affiliation or endorsement is claimed** by the Australian Government, the
Department of Defence, the Australian Defence Force or the Australian Army.

### 5.2 Real-world material and explicit source exclusions

- **ADF/Army insignia and camouflage:** producer-directed acquired examples may be used under ADR-035; use of real marks does not imply endorsement. Retain any available provenance/credits.
- **Fiction and setting direction:** invented battalion titles, mottos and MAF art direction remain choices of the fictional setting. They are not a project-use permission restriction; a producer-directed real-world reference may be used consistently with ADR-035.
- **Commercial game rips remain excluded:** no copied/ripped commercial-game assets or content from model-ripping sites. This is an explicit source exclusion outside the acquired-asset clearance.
- **Content ethics remain:** do not portray MAF as a real ethnic, religious, political or contemporary armed group, and do not use derogatory imagery or stereotypes.

### 5.3 Fictional-fiction constraints

1. **The opposing force is fictional** and must not represent any real ethnic, religious, political or contemporary armed group.
2. **No culturally derogatory imagery, language or stereotypes.** The Murasian Armed Forces are presented as a credible **conventional military force**, never as terrorists, extremists, an ethnic or religious militia, or a racial caricature.
3. **Fictional faction names, insignia and backstory**; authentic Australian Army ranks/insignia may appear under ADR-034/035 without implying affiliation.
4. **No real base, installation or operationally useful site layout** in any map.
5. **No realistic manufacturing, modification or unlawful-use instructions.** All weapon work is game simulation. Placeholder weapon silhouettes carry no dimensioned, functional or manufacturing-revealing detail.
6. **Faction recognition must never depend on colour alone** — silhouette, equipment arrangement, insignia shape and weapon silhouette carry it too, so the product remains legible to colour-blind players.

> Producer clearance under ADR-035 removes per-asset project-use holds and does not require a separate legal-review or substitution gate for acquired project assets. Keep the no-endorsement disclaimer, credits and content-ethics rules.

---

## 6. Compliance Checklist (per-asset, before commit)

- [ ] Publisher identified where available; unknown stays explicitly unverified
- [ ] Source URL / acquisition method recorded where available
- [ ] Seller terms/metadata recorded when available; unknown stays explicitly unverified
- [ ] Observed provenance class assigned only if useful; source terms do not override ADR-035 project-use clearance
- [x] Producer's Southern Spear F2P project-use clearance recorded (ADR-028/035); source terms remain provenance, not a project-use hold
- [ ] Attribution requirements captured and satisfied
- [ ] Modifications from the original recorded
- [ ] Share-alike / source-disclosure implications checked (class C)
- [ ] Row added to this register
- [ ] Row added to `ASSET_REGISTER.md`
- [ ] Prohibited-source check passed (L-0007, L-0008)

---

## 7. Release Gate

**Revised by ADR-035 (2026-09-28)** for a free-to-play release. Before any public release:

- [x] ~~Zero class D or E entries~~: every project asset is cleared (ADR-035)
- [x] ~~L-0003 insignia review~~: lifted (ADR-035); R-57 accepted
- [ ] The no-endorsement disclaimer ships (credits, store page, site)
- [ ] L-0001 Lyra sample-content shipping terms confirmed
- [ ] L-0002 UE EULA obligations satisfied (royalty reporting, credit)
- [ ] Attribution file generated from this register and shipped
- [ ] Every shipped asset traces to a register row or is class F

---

## 8. Change Log

| Date | Change | Entry |
|---|---|---|
| 2026-09-26 | Register created. Lyra and UE recorded. Insignia, ADF marks and prohibited sources placed on hold. No third-party assets acquired. | All |
| 2026-09-28 | **ADR-035**: free-to-play; every project asset cleared; real names allowed; L-0003 hold and L-0004 prohibition lifted; L-0007 narrowed to ripped/CAD sources; release gate revised; R-57 accepted. | §0, L-0003, L-0004, L-0006, L-0007, §5.2, §7, L-0021 |

### L-0016 — Fab/Vault assets acquired for Southern Spear; initial entries 2026-09-27, expanded in inventory 2026-10-01

> The old SESSION 090 risk claims R-94 (StoneWell unregistered) and R-95 (Singapore Canal against a prohibition) were superseded after this intake snapshot: StoneWell is registered/producer-cleared in `ASSET_REGISTER.md` §4.9h, and Singapore Canal's generic prop/material references are producer-cleared under ADR-028/035; the no-Asian-base-map art-direction distinction remains. The historical risk statements remain in the changelog as dated history, not current gates.
>
> **Disposition vocabulary:** this table began as dated intake/selection notes. “Held for” meant a candidate intended for possible map placement, not a permission hold; “downloaded, not imported” and similar labels describe observed technical state at that snapshot. Current cache/install/use findings are in `ASSET_REGISTER.md` §§4.9i–4.9n. Under ADR-035, none of those labels conditions project-use clearance.

| Pack | Local folder | Used for | Status |
|---|---|---|---|
| Rural Australia | `Content/RuralAustralia` | Base of `L_RedGum_01` (ADR-022); fence meshes changed to have no collision, and since Session 041 Dry River: ground material `MI_Ground_Dirt_01` (terrain and skirt), rocks, logs, trees (`Tools/Unreal/expand_dryriver.py`; `dryriver_ground.py` removed in Session 044) | In use |
| Namaqualand | `Content/Namaqualand` | Base of `L_Saltbush_01` (MAPS_SALTBUSH.md); Dry River scatter since Session 041: stones, rocks, boulders, bark debris, dead branches, *Didelta* shrubs. The South African wildflowers are not used (setting reads as Australian, ADR-016) | In use |
| QuantumCharacter (modular military character) | `Content/QuantumCharacter` plus tracked Game Feature prototype modules | Friendly visible body (ADR-042) | Producer-cleared for F2P use; four Quantum modules are on Quantum's skeleton, with component-level camo overrides and retained Manny-rigged vest/helmet. Final in-game appearance capture remains pending. |
| Modern_Insurgent_7 | `Content/Modern_Insurgent_7` | MAF soldier body (conventional parts only) | Producer-cleared for F2P use; retain provenance/credits. Historical friendly-head use ended under ADR-042. |
| Insurgent_2 | `Content/Insurgent_2` | — (not selected for current MAF art direction; historical art-selection note, not a permission hold) | Not used |
| FPS_Weapon_Bundle, AK-47, M1911 | `Content/FPS_Weapon_Bundle`, `Content/AK-47`, `Content/M1911` | Reference for A-series reshaping only | Not used |
| **Scene Quarry Slate** | `Content/Scene_QuarrySlate` | **Rock, ledges, gravel, the best stone in the project.** Dry River scatter and road surface, tinted under `MI_SS_Ironstone_*`; Ravenshoe Crossing gorge walls and boulders (`MAPS_RAVENSHOE.md`) | In use — **row added 2026-09-28, see L-0016b** |
| Modular Rural Cabin | `Content/Modular_Rural_Cabin` | Sparse conifer on shaded north-facing slopes (Ravenshoe). No map base | In use — **row added 2026-09-28, see L-0016b** |
| Singapore Canal | `Content/Singapore_Canal` | Generic corrugated/wood material and prop references used on Dry River and Red Gum structures; 11 committed assets reference the pack | **In use.** No canal layout or Asian masonry is used as an Australian base. Producer-cleared for F2P use under ADR-028/035; retain the art-direction distinction. Row added 2026-09-28, see L-0016b; corrected after map-reference scan. |
| Nanite Plants Sample Collection | `Content/Nanite_Plants_Sample_Collection` | — (6 sample meshes, temperate European garden species) | Installed, not used; producer-cleared if selected for F2P use. Row added 2026-09-28, see L-0016b |
| Military Radio | `Content/Military_Radio` | Radio/headset props | In use (props). Row added 2026-09-28, see L-0016b |
| Realistic Starter VFX Pack Vol 2 | `Content/Realistic_Starter_VFX_Pack_Vol2` | Particle effects | In use (FX). Row added 2026-09-28, see L-0016b |
| Sample Animation Pack | `Content/SampleAnimationPack` | — | Installed, not used. Row added 2026-09-28, see L-0016b |
| World Flags | `Content/World_Flags` | `MI_SS_Flag_Friendly`, `MI_SS_Flag_MAF` material instances | In use; corrected after reference scan. |
| FP_AKS74U Animation | `Content/FP_AKS74U_Animation` | `MI_AKS74U`, `MI_Magazine` on MAF weapon meshes | In use; material dependencies, not an asserted animation dependency. Corrected after reference scan. |
| Red car wreck | `Content/Downloaded/VaultCache/FabLibrary/Red_car_wreck-04d70886` (cache) → prepped to `SS_Raven_wreck_car` | **Ravenshoe Crossing M-008j** — the burning wreck on the bridge deck at OBJ A. A red Renault shell, doors open, engine bay gutted | In use (M-008j). **Row added 2026-09-28, see L-0016c.** Fab plugin wrote no `metadata` for this folder, so seller and `isAiForbidden` are **unverified** |
| Abandoned & junk Car (PLEXUS GAME ASSETS) | `.../FabLibrary/Abandoned___junk_Car-ee5cffe5` → prepped to `SS_Raven_wreck_junk` | Ravenshoe Crossing M-008j — second wreck, in the creek bed | In use (M-008j). Row added 2026-09-28, see L-0016c. `isAiForbidden: false` |
| American Old Windmill (Polyvine) | `.../American_Old_Windmill-d8d4a1d3` → prepped to `SS_Raven_windmill` | Ravenshoe Crossing M-008j — windmill on the north ridge | In use (M-008j). **`isAiForbidden: true` — see L-0016c** |
| Fuel barrel (SampleDotTxt) | `.../Fuel_barrel-873fee1d` → prepped to `SS_Raven_fuel_drum` | Ravenshoe Crossing M-008j — fuel drums on the deck and at the gatehouse | In use (M-008j). **`isAiForbidden: true` — see L-0016c** |
| Barn (seller unrecorded) | `.../FabLibrary/Barn-eb4457bc` → prepped to `SS_Raven_barn` | Ravenshoe Crossing M-008j — barn on the north ridge | In use (M-008j). No `metadata` written by the Fab plugin; seller and AI flag unverified. See L-0016c |
| Military Trenches — Pile Sandbag Canvas 01 (Quixel Megascans) | `.../Military_Trenches_Pile_Sandbag_Canvas_01-a08111c9` → prepped to `SS_Raven_sandbag_stack` | Ravenshoe Crossing M-008j — sandbag hard cover on both approaches | In use (M-008j). **`isAiForbidden: true` — see L-0016c** |
| Military Trenches — Wall Metal Corrugated 04 (Quixel Megascans) | `.../Military_Trenches_Wall_Metal_Corrugated_04-e15620d3` → prepped to `SS_Raven_trench_wall` | Ravenshoe Crossing M-008j — improvised cover panels at the abutments | In use (M-008j). `metadata` absent; `isAiForbidden` **unverified**, not inferred from neighboring Quixel listings — see L-0016c |
| Old Abandoned Rusty Cars (OlegVerenko) | `.../Old_Abandoned_Rusty_Cars___...-ed740921` | — (5 car meshes, `Content/RustyCarsFree/`) | **In use — Wandarra (M-009) since 2026-09-30**: 10 wrecks placed as cover. `isAiForbidden: false`. Row added 2026-09-28, see L-0016c; corrected 2026-09-29 to not-used, corrected again 2026-09-30 on first map use (`ASSET_REGISTER.md` §4.9j) |
| Rigged Cargo Container Red PBR (Vadim3dd) | `.../Rigged_Cargo_Container_Red_PBR-1db0b7e1` | — | Cache-only/not imported in the 2026-10-01 snapshot; `isAiForbidden: true` is observed metadata only, not a project-use hold under ADR-035. |
| Old Rustic Hand Water Pump (Sayan Paul) | `.../Old_Rustic_Hand_Water_Pump-0b2fc83d` | Candidate for Ravenshoe approaches in the 2026-09-28 intake snapshot | Not imported in the 2026-09-28 snapshot; later imported and used in Ravenshoe. `isAiForbidden: false`. Row added 2026-09-28 |
| Water Tower (Chamod1999) | `.../Water_Tower-86b17984` | Candidate for Ravenshoe approaches in the 2026-09-28 intake snapshot | Not imported in the 2026-09-28 snapshot; later imported and used in Ravenshoe. `isAiForbidden: false`. Row added 2026-09-28 |
| Red Tractor, Storage Unit nr5, Old Barn, Wooden Chicken Coop, Crushed Classic Raw Scan, Old Bath, Military Trenches Debris Pile Rock | `.../FabLibrary/*` | — | **Intake snapshot (2026-09-28):** downloaded/cache-only or not imported at that time; Old Barn was later imported and used in Ravenshoe. Other items remain unselected in the current inventory for import-pipeline or art-direction reasons, not a project-use permission hold. |
| **MOUT urban training kit** (Military Operation Urban Training; 2.1 GB, 507 files, 3 maps incl. a 4.26-era demo urban block) | `Content/Downloaded/VaultCache/ModularM6dfea54fd98cV5/` (staging) → `Content/MOUT_Civilian/` | **Wandarra (M-009) since 2026-09-30**: buildings, church kit, fences and street furniture; `Docs/MAPS_WANDARRA.md` | **In use; producer-cleared for F2P use.** The Vault download wrote no `metadata` sidecar anywhere in the pack, so seller and `isAiForbidden` are unverified. First 5.8 load of the 4.26 content measured silent (R-67 first-load evidence, 2026-09-30). Row added 2026-09-29 |
| **European Beech trees** (Fab; 7.0 GB, 258 files: SimpleWind and PivotPainter beech forests, saplings, impostors) | `Content/Downloaded/VaultCache/MS_Beech_UE51_V2/` (staging) → `Content/EuropeanBeech/` | **Wandarra (M-009) since 2026-09-30**: 38 SimpleWind statics as verge rows, park cluster and depot screen | **In use; producer-cleared for F2P use.** The Vault chunk carries a build manifest only — no `metadata` sidecar — so seller and `isAiForbidden` are unverified. Authored **UE 5.1 native**. Row added 2026-09-30 |
| Mega Moduler Apartment Building | `.../FabLibrary/Mega_Moduler_Apartment_Building-db1b80f5` | — | Cache-only/not imported in the 2026-10-01 snapshot; `isAiForbidden: true` is observed metadata only. No project-use hold under ADR-035. Seller karaman. Row added 2026-09-29 |
| Modular 3D hospital environment | `.../FabLibrary/Modular_3D_hospital_environment-7e1574fd` | — | Cache-only/not imported in the 2026-10-01 snapshot; `isAiForbidden: false` is observed metadata only. Seller Madd Game Art; listed under *Environments / Horror*, not selected for current use. Row added 2026-09-29 |
| American Road with Parking Lot | `.../FabLibrary/American_Road_with_Parking_Lot-a629eb34` | — | Cache-only/not imported in the 2026-10-01 snapshot; `isAiForbidden: false` is observed metadata only. Seller Jimbogies; GLB format is not currently onboarded in the prop-prep path. Row added 2026-09-29 |
| Individual First Aid Medical Kit (IFAK) | `.../FabLibrary/Individual_First_Aid_Medical_Kit_IFAK-a628e3ba` | — | Cache-only/not imported in the 2026-10-01 snapshot; planned medic asset (ADR-040). `isAiForbidden: true` is observed metadata only, not a project-use hold. Seller SpatialNeglect. Row added 2026-09-29 |

| Field | Value |
|---|---|
| **Author** | Respective Fab sellers (see each pack's Fab page in the producer's library) |
| **Source** | Fab (fab.com), added to the project from the producer's Epic account |
| **Licence/provenance** | Listing-specific terms and seller metadata vary; sidecar observations are listed in ASSET_REGISTER §4.9m. |
| **Project-use status** | Producer-cleared for Southern Spear F2P use under ADR-028/035. Preserve available credits/provenance; raw vendor source is not to be redistributed. |

### L-0016b — The installed-pack register gap, found and closed 2026-09-28

| Field | Value |
|---|---|
| **What was found (2026-09-28 snapshot)** | Nine packs were undocumented at that time: `Scene_QuarrySlate`, `Singapore_Canal`, `Modular_Rural_Cabin`, `Nanite_Plants_Sample_Collection`, `Military_Radio`, `Realistic_Starter_VFX_Pack_Vol2`, `SampleAnimationPack`, `World_Flags`, `FP_AKS74U_Animation`. Later dependency scanning corrected World Flags and FP_AKS74U Animation as in-use, and a 2026-10-01 review corrected Singapore Canal and added StoneWell. This historical nine-pack set was not a complete scan of FabLibrary or all VaultCache. |
| **How it was found** | A limited inventory of 19 non-Fab VaultCache directories (~36 GB) taken while scoping Ravenshoe Crossing. It did not include a recursive inventory of the separate `FabLibrary` cache and should not be read as the complete VaultCache state; the 2026-10-01 full local scan is documented in L-0025 and `ASSET_REGISTER.md` §4.9m–o. |
| **Why it went unnoticed** | L-0016's table was written when Red Gum was built (ADR-022) and listed only the packs that had a *decision* attached to them. Packs added later — Dry River's rock, the radio props, the VFX — were installed through per-feature work without a register pass, so the rule in §1 ("no third-party asset enters this repository without a row") was being met in letter for those six packs but not in substance |
| **Project-use status** | Producer-cleared for Southern Spear F2P use under ADR-028/035. This was an inventory/bookkeeping correction; listing terms and provenance are recorded separately and do not create a permission hold. |
| **Action taken** | L-0016's table completed with a row per pack, each marked as added 2026-09-28. **No asset was imported, modified, moved or deleted.** No licence class changed |
| **Standing action** | Any future pack import must add its L-0016 row **in the same change** that imports it, not afterwards. The CI check in §1 covers `.uasset`/`.umap` files appearing without a register entry; the failure mode found here is a pack that is *already* imported, which that check does not catch |

### L-0016c — Fab listing metadata observations (`isAiForbidden`), found 2026-09-28

| Field | Value |
|---|---|
| **What was found (2026-09-28 snapshot)** | The Ravenshoe prop sweep recorded marketplace `isAiForbidden` values, including true/false and absent metadata. The corrugated-wall sidecar was absent; its value is **unverified** and is not inferred from neighboring Quixel listings. The 2026-10-01 recursive inventory in ASSET_REGISTER §4.9m supersedes the old incomplete counts. |
| **How it was found** | Parsing the `metadata` sidecar that the Fab desktop plugin writes into `Content/Downloaded/VaultCache/FabLibrary/<pack>/<format>/metadata`. Note the sidecar sits at **varying depth** — `fbx/metadata`, `fbx/mid/metadata`, `obj/metadata` — so a fixed-depth scan silently misses most packs. A first pass at fixed depth reported only 3 of 12 |
| **Producer's decision** | Producer direction under ADR-028/035 clears project use for acquired Fab assets. The 2026-09-28 listing observations included windmill, fuel barrel, sandbag and corrugated-wall metadata, and the Rigged Cargo Container remained cache-only at that time. `isAiForbidden` is a marketplace metadata field, not the project's use decision; record it as provenance without imposing a hold. |
| **Project-use status** | Producer-cleared under ADR-028/035. Listing/sidecar values are recorded as provenance; this entry does not assert one Fab licence tier across these distinct listings. |
| **Metadata finding** | The flag is an observed marketplace field, not a licence class. The producer has cleared acquired assets for Southern Spear's free-to-play game under ADR-028/035, regardless of `true`, `false` or missing values. Preserve the flag and missing-sidecar state as provenance; neither is a project-use hold. |
| **Handling** | Record source metadata and credits where present. Mechanically prepped game derivatives are tracked as distinct project assets; keep raw vendor sources out of public redistribution. These steps do not modify or condition the producer's F2P use clearance. |
| **Standing action** | When available, record seller/source, credit and `isAiForbidden` metadata recursively, including an explicit `unverified` value when no sidecar exists. This is provenance/credit bookkeeping only and does not defer producer-cleared use. |

### L-0016d — Producer clearance applies regardless of `isAiForbidden` (2026-09-29; reaffirmed 2026-10-01)

| Field | Value |
|---|---|
| **Producer's decision** | Assets acquired/held for Southern Spear may be used in this free-to-play game regardless of whether `isAiForbidden` is `true`, `false` or unverified (ADR-028/035). No asset is held back or replaced on account of this metadata field. |
| **What stays** | Record available seller, source, attribution and AI-use metadata for provenance/credits. This is not a universal marketplace-license statement and does not authorize raw-source redistribution. The producer's prohibition on ripped commercial-game assets and the project's no-endorsement/content-ethics rules remain separate. |

### L-0017 — A88 textured model (producer-supplied download; project use cleared)

| Field | Value |
|---|---|
| **Component** | Bullpup rifle model with scope, foregrip, laser and suppressor; OBJ/3DS plus three 4K PNG atlases |
| **Source** | https://rigmodels.com/model.php?view=EF88_Rifle-3d-model__d1d54b9889924370a6d4576b004fa180 (aggregator; credits Upsurge Studios, upsurgestudios.com) |
| **Local copy** | `Art/Weapons/A88/New/` (not committed) |
| **Licence** | Aggregator page shows "Royalty Free"; the original author's terms are not shown and not yet confirmed |
| **Use** | Current A88 cosmetic mesh via `Tools/Blender/a88_sourced.py` and `setup_weapons.py` |
| **Status** | **Producer-cleared for Southern Spear F2P use (ADR-035).** Original-author terms remain unverified provenance; retain the source URL/credit record and continue fictional A-series visual-design work. R-21 is not a project-use hold. |
| **Producer decision — website promotion (2026-09-28)** | The producer directed publication of a render of the sourced EF88 model (current in-game A88 cosmetic mesh) on the website's Loadout section. The source terms remain unverified provenance; producer clearance under ADR-035 covers Southern Spear F2P use. Do not redistribute raw source files. |

### L-0021 — ADF Re-Cut (ADFRC) pack, extracted into `Content/Sourced/ADF_Extracted/`

| Field | Value |
|---|---|
| **Component** | 268 `.p3d` (ODOL-binarised) models, 2,484 decoded PNG textures, 165 `.rtm` animations, Arma configs (`.cpp`/`.hpp`/`.cfg`), `.rvmat` materials, sounds, 37 ready-made `.uasset`s; ~7,748 files, ~17 GB |
| **Source** | Two origins, per the tree's own `README.md`: (1) the source/config distribution of **ADF Re-Cut / ADFRC**, `github.com/IsoBones/ADFRC`, under APL-SA; (2) the **binarised Steam Workshop release**, `!Workshop\@ADF Re-Cut [Beta]\addons` (15 `.pbo` archives, 5.8 GB). The GitHub repository ships no `.p3d` by design — all geometry exists only inside the Workshop PBOs |
| **Local copy** | `Content/Sourced/ADF_Extracted/` (git-ignored, inside the Unreal content root — see R-25) |
| **Authorisation** | **WRITTEN GRANT ON FILE.** Email from **Tonnie** to the producer, 2026-09-27 15:05, granting permission to use "the ADF ReCut models and associated assets that I have extracted" within the Southern Spear project, for development, testing, prototyping and inclusion in the game, in the extracted (unextracted-format) state. Verbatim transcription and the original screenshot are preserved at `Docs/evidence/L0021_adfrc_authorisation_email.txt` / `.png`. This is the evidence that moves this entry off the R-24 block for the grantor's own components |
| **Observed upstream terms** | The source tree includes APL-SA and ADFRC license texts with restrictions on extraction, derivatives and redistribution. These remain recorded provenance. The producer's project-specific direction clears acquired assets for this game's free-to-play use; it does not authorize redistribution of raw source or erase the source record. |
| **Grant is narrower than it appears** | The email's third paragraph is a **disclaimer, not a warranty**: permission is granted "on the understanding that you remain responsible for ensuring compliance with any applicable intellectual property, licensing, copyright, or other legal requirements associated with the original source material." The grantor therefore expressly does **not** warrant that the material is free of third-party rights, nor that he holds every right he is granting. Recorded deliberately — this is the most consequential sentence in the message |
| **Scope limit — multi-author pack** | **RESOLVED 2026-09-27 (Session 032c).** The producer reports blanket permission from the ADFRC mod team as a whole, covering the credited contributors. This team permission is retained as provenance alongside the producer's broader project-specific F2P direction under ADR-035. Raw-source redistribution remains prohibited by project handling; no further per-component permission hold applies to acquired project assets. |
| **Source/branding note** | Source assets include recorded manufacturer/service identifiers and camouflage. These remain useful provenance/art-direction observations. ADR-035 accepts their use in Southern Spear's F2P game; preserve the no-endorsement statement and do not treat this row as a legal opinion about rights outside the project. |
| **Producer decision** | The producer confirms the ADFRC team permission and clears assets acquired/held for use in Southern Spear's free-to-play game, including converted and derived project work. This is the operative project-use direction under ADR-035; preserve source/credit records and do not redistribute raw vendor source. |
| **Producer decision — website promotion (2026-09-28)** | The producer directed publication of renders of internal ADFRC-derived weapon models on the website's Loadout section. The producer's F2P project-use clearance applies; this does not authorize public distribution of raw ADFRC source files. |
| **Use** | **Producer-cleared for Southern Spear F2P use**, including development, testing, prototyping and inclusion in the game. This does not authorize raw-source redistribution; see git handling. No brand-substitution permission gate remains under ADR-035. |
| **Location** | Relocated 2026-09-27 to `Art/ADFRC/` (source: 177 `.p3d`, 1,471 PNG, 292 animation files, 68 configs). **Converted 2026-09-27** to `Art/ADFRC_MLOD/` (177 MLOD) and `Art/ADFRC_BLEND/` (**179 `.blend` with verified geometry**), including 40 optics and the `adfrc_SR25` DMR. Player/worn gear consolidated in `Art/ADFRC_Player/` (57 models + 1,538 textures). Every model has a sibling `_textures/` folder. See `Art/ADFRC/MANIFEST.md`, `Art/ADFRC_Player/README.md`. The full extraction remains at `Content/Sourced/ADF_Extracted/` |
| **Conversion tooling** | `UKSFTA-P3D` (ODOL v73–v75 debinarizer, built on .NET 10) plus Arma 3 Object Builder v2.5.1 in Blender 5.2. Both live **outside** the repository at `E:/_tools/`. One local patch to `BlenderExport.cs` so the generated Blender script also tries the `bl_ext.user_default.*` module id. The converted output is **derived work** from the L-0021 material and is covered by the same terms |
| **Git handling** | `Art/ADFRC/*` is **git-ignored**; only `LICENSE.md` and `MANIFEST.md` are tracked. Rationale: these are third-party source files redistributed from someone else's distribution, and the pack is not the producer's to publish, so it must not travel via the repository. Without this rule 5.5 GB of third-party content would have become committable the moment it moved out of the already-ignored `Content/Sourced/`. **Amended 2026-09-28 (producer):** the earlier wording here said the authorisation was "personal and non-commercial" and treated the project's own release model as the constraint. The project is a free-to-play product and the producer has directed that this is not a limitation, so the git rule now rests solely on the redistribution point above and not on a non-commercial reading. |
| **Status** | **Producer-cleared for Southern Spear's free-to-play game (ADR-035)**. Raw source remains quarantined/git-ignored per project handling; it is not to be redistributed as a source pack. R-28 conversion is closed; R-29's FBX/material/texture engineering observations are workflow findings, not use-permission holds. |

### L-0022 — Original Southern Spear character materials (script-authored; historical application and current Quantum overrides)

| Field | Value |
|---|---|
| **Component** | 12 PNG texture sets (CMECU dry-country camo, MAF red-earth camo, tan and dark gear fabric; base colour, twill micro-normal, ORM) and 4 materials `M_SS_CMECU`, `M_SS_MAF`, `M_SS_GearTan`, `M_SS_GearDark`, plus the per-slot override arrays on `ASSCharacterPartActor` |
| **Source** | Original work, generated by `Tools/Textures/make_character_textures.py` (PIL/numpy). No third-party texture was sampled, traced or converted; the ADFRC material was specifically **not** used as a pattern reference |
| **Licence** | Class **F** — original, ours to license |
| **Use** | Original cosmetic materials remain part of the project; active friendly camo rides on Quantum module component overrides under ADR-042, with ADFRC vest/helmet and separate MAF materials. Vendor meshes are not duplicated or edited. |
| **Status** | The former friendly G3/MAF slot counts are historical and should not be read as current Quantum slot assignment. Active Quantum camo configuration is described under ADR-042 and ASSET_REGISTER CH-TEX-004; final visual capture remains pending. |
| **Retune (Session 042)** | CMECU retuned from four tones to seven and MAF lifted ~15%, both measured against the producer's reference photography by `Build/audit/tune_camo.py` rather than eyeballed: reference fabric lum p10/p50/p90 = 40/129/235, median saturation 0.46, oxide-red population 8.7%; the regenerated sets score lum 43/107/205, sat 0.47, red 10.2%. Still noise-generated from the script's own fbm field — **no real-world camouflage was sampled, traced or converted**. **Application superseded in part by ADR-042:** these original sets are not the current friendly third-person uniform; Quantum uses a component override for the generated DPCU-derived tileable camo, while MAF remains a separate opposing configuration. The `T_SS_CMECU_*` / `T_SS_MAF_*` sets and original materials remain project assets; do not infer the old G3 slot counts are current. |
| **Website use (Session 042)** | Studio renders using these textures on the L-0016 body and L-0021 kit were published and then **withdrawn** in the same session; see ASSET_REGISTER §4.9. The camo itself is Class F and carries no restriction; the body and kit in the same image do, and it is those two layers that made the renders unsuitable to publish. |

### L-0023 — Session 044 additions (producer-cleared project use; source metadata recorded per listing)

| Component | Source | Use | Status |
|---|---|---|---|
| M4 and G17 FPS Weapon Animations packs (BarcodeGames) | Fab `38da8f1e…`, `5b920af4…`; listing-specific source metadata | First-person arms and clips (`SSExp_ObjectiveAssault/FirstPerson`); the packs' real-weapon models are dropped in `fp_arms.py` | In use; producer-cleared for F2P use |
| African Slate Quarry (Scene_QuarrySlate) | Fab (Megascans) | Base of `L_Bluestone_01` (ADR-028 map-base note); Dry River stones | In use; git-ignored pack (R-41) |
| Military Trenches Wall Metal Corrugated 04 | Fab (Megascans) | `MI_SS_CorrugatedIron` texture set | In use |
| Gloves for fps game (Bobeer) | Fab listing, CC BY 4.0 recorded locally | — | Not used; producer-cleared if used; preserve credit "Bobeer" |
| VibeUE (Kevin Buckley) | github.com/kevinpbuckley/VibeUE, MIT | Editor-only dev tooling, git-ignored clone | Not shipped |

### L-0024 — Ghost gum tree and kangaroo models (registered 2026-09-30)

| Field | Value |
|---|---|
| **Component** | `Content/ghostgum/` (ghost gum tree FBX + TGA/PNG texture set, 20 MB) and `Content/kangaroo/` (kangaroo FBX/OBJ + JPG/TGA textures, 24 MB); original vendor archives kept alongside (`TH_Ghoast_Gum.zip.zip`, `kangaroo.rar`) |
| **Publisher** | Not individually recorded — the downloads arrived with no `metadata` sidecar and no seller page record ("TH_" prefix suggests a marketplace/archive source) |
| **Source** | Local files as received; no URL recorded |
| **Observed seller terms** | Not independently established; no licence file or seller page was recorded with the local copies. Producer confirmation is recorded as project-use clearance below, not as a vendor-published licence. |
| **Project-use status** | Producer-cleared for Southern Spear F2P use; seller/source metadata remains unverified. |
| **Status** | 🟢 **Cleared for use in Southern Spear's free-to-play game (producer decision, 2026-09-30; reaffirmed 2026-10-01)** |
| **Use** | Kangaroo: static easter-egg dressing (2 individuals per map on Dry River and Red Gum Station, collision off). Ghost gum: imported to `/Game/Art/Environment/Fab/TH_Complete_Full_Ghoast_Gum`, six texture maps and three material instances; 10 placed on Dry River as the windmill screen ring (ASSET_REGISTER ENV-003). |
| **Producer decision (2026-09-30; reaffirmed 2026-10-01)** | The producer confirms that assets downloaded for or used in the project are free to use in Southern Spear's F2P game. This closes R-90a; missing metadata remains a provenance/credits note, not a permission hold. |
| **Git handling** | Tracked via LFS (`.fbx`, `.obj`, `.tga`, `.png`, `.jpg`, `.jpeg` patterns); archives tracked as plain binaries (`-filter -diff -merge text`) |

### L-0025 — Full asset inventory and producer F2P reaffirmation (2026-10-01)

| Field | Value |
|---|---|
| **Scope** | Read-only inventory of FabLibrary, the broader VaultCache, project `Content/`, tracked Game Feature assets and the local UE 5.8.3 Installed Build. Counts and caveats are documented in `Docs/evidence/asset_inventory_20261001.md`; the map-only subset remains in `PACK_MANIFEST`. |
| **FabLibrary snapshot** | 50 physical directories, 675 files, 25,051,328,336 bytes; local `listings_v1.db` has 57 rows (51 `local_listing`). Recursive scan found 22 metadata sidecars: 10 `isAiForbidden=true`, 12 false; 28 folders have no sidecar. One catalogue listing reports `isAiGenerated=true`. These are observed source metadata, not project-use determinations. |
| **Broader local inventory** | VaultCache: 30 top-level directories, 7,366 files, 58,343,692,654 bytes. Project `Content/`: 29,437 files, 118,405,659,191 bytes, including untracked/shared-worktree data. UE 5.8.3 CL 58210709: Engine/Content 40,056 files; Engine/Plugins 113,127 files / 901 `.uplugin`; FeaturePacks 9; Templates 5,880. `SouthernSpear.uproject`: 95 plugin entries, 84 enabled, 11 disabled. These are local snapshots, not tracked-content totals or cook manifests. |
| **Tracked additions/findings** | Tracked A-series Game Feature roots contain 271 assets (151 `T_`, 82 `MI_`); tracked Quantum prototype meshes/material assets live under `Plugins/GameFeatures/SSExp_ObjectiveAssault/Content/Characters/QuantumProto/`. The tracked DPCU-derived tile image is a generated texture route, not evidence that the unmodified source is mounted unchanged. WaterPlane has 34 local files, one known tracked/reference normal and 33 untracked concurrent files; Splash assets were present untracked with origin/intent unknown. |
| **Producer direction (reaffirmed)** | Assets acquired/held for Southern Spear are free to use in this free-to-play game under ADR-028/035. This applies regardless of missing metadata or seller `isAiForbidden`/`isAiGenerated` observations. Preserve known attribution and provenance, no-endorsement and content-ethics rules. This is project-specific, is not a universal marketplace licence claim, does not authorize raw-source redistribution, and does not reverse specific excluded/prohibited sources (including Electric Dreams under ADR-013/L-0012 and ripped commercial-game content under L-0007/L-0008). |
| **Interpretation** | Cache presence, local installation, tracked Git presence, map references and selected runtime assets are separate states. This register records each only as supported by the inventory and existing reference evidence; it does not claim every cached file is imported, used, or selected in a shipping build. |
