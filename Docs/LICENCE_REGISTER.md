# LICENCE REGISTER — Southern Spear

**Document ID:** `Docs/LICENCE_REGISTER.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army.

---

## 1. Purpose

A single authoritative record of **every** third-party dependency in the project, its licence, its attribution obligations, and whether it is legally clear for use in a **packaged commercial product**.

### The rule

> **No third-party asset, plugin, library or code enters this repository without a row in this register.**

This is enforced in CI: a build fails if a new `.uasset`/`.umap` appears with no corresponding register entry.

### "Free" is not a licence category

An asset that costs nothing to download may still be non-commercial, may require attribution, may forbid redistribution, or may forbid use in a product that competes with its author. **Each asset is judged on its actual licence terms, not its price.**

---

## 2. Licence Compatibility Classes

| Class | Meaning | Commercial packaging |
|---|---|---|
| **A** | Permits commercial use, no attribution required | ✅ Clear |
| **B** | Permits commercial use, attribution required | ✅ Clear with attribution shipped |
| **C** | Permits commercial use, share-alike or source-disclosure applies | ⚠️ Legal review required |
| **D** | Non-commercial / research / evaluation only | ❌ **Prohibited** |
| **E** | Unclear or undocumented | ❌ Treated as D until clarified |
| **F** | Original work created for this project | ✅ Clear, no obligation |

Anything class **D** or **E** is a release blocker. There is no exception.

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

> Lyra is used as an **architectural foundation**. Its *art* is a placeholder, not Southern Spear art. Visuals are replaced before release.

### L-0002 — Unreal Engine 5.8.3

| Field | Value |
|---|---|
| **Component** | Unreal Engine 5.8.3 (Installed Build, `E:\Unreal\UE_5.8`) |
| **Publisher** | Epic Games, Inc. |
| **Licence** | Unreal Engine EULA |
| **Class** | **B** — royalty/attribution obligations apply per EULA |
| **Modifications** | **None.** Installed Build used as-is |
| **Action** | Track EULA obligations (royalty reporting, credit notice) in release planning |

### L-0003 — Rank insignia and unit insignia — **LEGAL HOLD**

| Field | Value |
|---|---|
| **Component** | RAN-style rank slides/slides, progression insignia, friendly and hostile unit insignia |
| **Publisher** | — |
| **Source** | To be created |
| **Licence** | **PENDING REVIEW** |
| **Class** | **E** — unresolved |
| **Status** | 🔴 **ON HOLD** |
| **Hold** | Do **not** reproduce official Australian Defence Force or Australian Army insignia. All insignia in the project are **original placeholder designs** pending legal and branding review |
| **Required before release** | Written legal review of insignia design, and confirmation of any required attribution to the Australian Army / Department of Defence |

> This hold is binding. It is the reason the game carries original placeholder insignia rather than realistic slides. It also constrains naming: the project does not present itself as an official Australian Army product.

### L-0004 — Australian Defence Force / Australian Army name and marks

| Field | Value |
|---|---|
| **Component** | Use of "Australian Army", ADF insignia, service branding |
| **Licence** | **NOT LICENSED** |
| **Class** | **D** — not cleared |
| **Status** | 🔴 **PROHIBITED without written permission** |
| **Rule** | The game must **not** present itself as endorsed, developed, sponsored or approved by the ADF, the Department of Defence or the Australian Army. All ranks and units shown are fictional. Marketing, packaging and store listings carry the fictional-work disclaimer |

### L-0005 — Third-party audio

| Field | Value |
|---|---|
| **Component** | All weapon, impact, footstep, ambience and UI audio |
| **Status** | Not yet acquired |
| **Rule** | Original, properly licensed, or properly attributed audio only. **No recorded real voice content.** Voice chat is never recorded without explicit per-player consent and a documented privacy design |
| **Action** | Every future audio entry added here before import |

### L-0012 — Electric Dreams environment (DECLINED — historical evaluation record only)

| Field | Value |
|---|---|
| **Component** | "Electric Dreams" environment pack, briefly staged outside the repository at `E:\Unreal\Environment\` |
| **Status** | 🔴 **DECLINED** |
| **Import status** | **NOT IMPORTED** — no asset from this pack has ever entered the repository, the project, or a build |
| **Project use** | **NOT PERMITTED** |
| **Licence** | **UNREAD — and no longer relevant, because the pack is not used** |
| **Class** | **D — prohibited for project use** |
| **Authoritative decision** | **ADR-013** — maps are built original; third-party environments are not used |

**No selective harvesting is authorised.** An earlier revision of this register read
"reference + selective harvest only" and listed "approved use: generic modular pieces
only". That wording directly contradicted ADR-013, which declined the pack **entirely**,
and it left the register reading as though harvesting had been permitted. It was not.
ADR-013 is the authority; this row now agrees with it.

**Constraints:**
1. No asset, material, mesh, texture, layout or art-style reference from this pack may enter the repository or any build.
2. It may not be used as a base map, as art direction, or as the source of any Southern Spear map.
3. Southern Spear map layout and art direction are original work (ADR-015, Dry River).
4. Historical evaluation record is **retained** below so the decision and its reasoning survive. Retention is not authorisation.

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

| Field | Value |
|---|---|
| **Component** | Any asset acquired from Fab |
| **Status** | **NONE ACQUIRED** (see L-0012 for the one pack staged so far) |
| **Blocker** | PROJECT_AUDIT **R-03** — UE 5.8 is not registered in the Epic Games Launcher, so the in-editor Fab plugin cannot resolve this engine version |
| **Action** | Register the engine in the Launcher, or acquire assets manually. Either way, each asset gets a register row with publisher, source URL, licence class and modifications **before** it is imported |
| **Rule** | Never download from unverified model-ripping or redistribution sites. Never assume a free asset permits commercial packaging |

### L-0007 — Prohibited sources (standing prohibition)

| Field | Value |
|---|---|
| **Component** | Manufacturer CAD, commercial game models, ripped assets, real-world camouflage textures |
| **Status** | ❌ **PROHIBITED** |
| **Rule** | Do not trace, rip or redistribute manufacturer CAD files, commercial game models or protected assets. The multicam-style camouflage is an **original pattern**, not a reproduction of any protected commercial texture. Weapons are original models inspired by publicly documented equipment, not traced geometry |

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
| **Rule** | Licence must be class A or B (or C with legal sign-off) before inclusion. **No paid dependencies without producer approval.** Record version, source URL and licence here |

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

### 5.2 Prohibited real-world material

- **No ADF/Army emblems.** No Rising Sun, corps badge, colour patch, unit emblem, motto, battle honour, ceremonial tradition or official rank-slide artwork is used, reproduced or traced. L-0003 remains on legal hold.
- **No real battalion titles or mottos**, and nothing derived from the Royal Australian Regiment.
- **No manufacturer logos, roll marks or CAD.** All weapon geometry is original or appropriately licensed.
- **No copied commercial-game assets, and no ripped assets**, under any circumstances.
- **AMCU and commercial MultiCam are not reproduced exactly**, nor traced from photographed fabric.
- **Historical Musorian camouflage is not reproduced exactly.** The broad red-earth exercise-OPFOR idea is inspiration only; the pattern, shapes and colour arrangement are original.

### 5.3 Fictional-fiction constraints

1. **The opposing force is fictional** and must not represent any real ethnic, religious, political or contemporary armed group.
2. **No culturally derogatory imagery, language or stereotypes.** The Murasian Armed Forces are presented as a credible **conventional military force**, never as terrorists, extremists, an ethnic or religious militia, or a racial caricature.
3. **Fictional insignia, names and backstory** throughout.
4. **No real base, installation or operationally useful site layout** in any map.
5. **No realistic manufacturing, modification or unlawful-use instructions.** All weapon work is game simulation. Placeholder weapon silhouettes carry no dimensioned, functional or manufacturing-revealing detail.
6. **Faction recognition must never depend on colour alone** — silhouette, equipment arrangement, insignia shape and weapon silhouette carry it too, so the product remains legible to colour-blind players.

> Renaming alone does not confer legal clearance. Final branding, insignia, camouflage,
> uniforms, weapons and store presentation are flagged for **independent Australian legal
> review before release**.

---

## 6. Compliance Checklist (per-asset, before commit)

- [ ] Publisher identified
- [ ] Source URL / acquisition method recorded
- [ ] Licence terms read in full (not just the store blurb)
- [ ] Licence class assigned (A–F)
- [ ] Commercial packaging permitted — **explicitly confirmed, not assumed**
- [ ] Attribution requirements captured and satisfied
- [ ] Modifications from the original recorded
- [ ] Share-alike / source-disclosure implications checked (class C)
- [ ] Row added to this register
- [ ] Row added to `ASSET_REGISTER.md`
- [ ] Prohibited-source check passed (L-0007, L-0008)

---

## 7. Release Gate

Before any public release:

- [ ] Zero class D or E entries
- [ ] L-0003 insignia review complete and resolved
- [ ] L-0004 name/marks position confirmed with legal
- [ ] L-0001 Lyra sample-content shipping terms confirmed
- [ ] L-0002 UE EULA obligations satisfied (royalty reporting, credit)
- [ ] Attribution file generated from this register and shipped
- [ ] Every shipped asset traces to a register row or is class F

---

## 8. Change Log

| Date | Change | Entry |
|---|---|---|
| 2026-09-26 | Register created. Lyra and UE recorded. Insignia, ADF marks and prohibited sources placed on hold. No third-party assets acquired. | All |

### L-0016 — Fab packs (Standard License), added 2026-09-27; **table completed 2026-09-28**

| Pack | Local folder | Used for | Status |
|---|---|---|---|
| Rural Australia | `Content/RuralAustralia` | Base of `L_RedGum_01` (ADR-022); fence meshes changed to have no collision, and since Session 041 Dry River: ground material `MI_Ground_Dirt_01` (terrain and skirt), rocks, logs, trees (`Tools/Unreal/expand_dryriver.py`; `dryriver_ground.py` removed in Session 044) | In use |
| Namaqualand | `Content/Namaqualand` | Base of `L_Saltbush_01` (MAPS_SALTBUSH.md); Dry River scatter since Session 041: stones, rocks, boulders, bark debris, dead branches, *Didelta* shrubs. The South African wildflowers are not used (setting reads as Australian, ADR-016) | In use |
| QuantumCharacter (military character) | `Content/QuantumCharacter` | 3 ACR soldier body | In use; insignia check pending (R-20); carries original Southern Spear materials as per-slot cosmetic overrides (L-0022) |
| Modern_Insurgent_7 | `Content/Modern_Insurgent_7` | MAF soldier body (conventional parts only) | In use; names internal only |
| Insurgent_2 | `Content/Insurgent_2` | — (irregular/ethnic-coded gear; ADR-016) | Not used |
| FPS_Weapon_Bundle, AK-47, M1911 | `Content/FPS_Weapon_Bundle`, `Content/AK-47`, `Content/M1911` | Reference for A-series reshaping only | Not used |
| **Scene Quarry Slate** | `Content/Scene_QuarrySlate` | **Rock, ledges, gravel, the best stone in the project.** Dry River scatter and road surface, tinted under `MI_SS_Ironstone_*`; Ravenshoe Crossing gorge walls and boulders (`MAPS_RAVENSHOE.md`) | In use — **row added 2026-09-28, see L-0016b** |
| Modular Rural Cabin | `Content/Modular_Rural_Cabin` | Sparse conifer on shaded north-facing slopes (Ravenshoe). No map base | In use — **row added 2026-09-28, see L-0016b** |
| Singapore Canal | `Content/Singapore_Canal` | Dry River generic props only (Session 044): crates, barrels, tubs, carts, packed sacks, planks and plain wood materials | **Generic props in use; architecture not used.** Asian canal/urban architecture and ornamented metal (`MI_MetalParts_01`) stay out (ADR-016). Stone *materials* must not be repurposed for Australian masonry. Row added 2026-09-28, see L-0016b; corrected Session 044 |
| Nanite Plants Sample Collection | `Content/Nanite_Plants_Sample_Collection` | — (6 sample meshes, temperate European garden species) | Installed, not used. Row added 2026-09-28, see L-0016b |
| Military Radio | `Content/Military_Radio` | Radio/headset props | In use (props). Row added 2026-09-28, see L-0016b |
| Realistic Starter VFX Pack Vol 2 | `Content/Realistic_Starter_VFX_Pack_Vol2` | Particle effects | In use (FX). Row added 2026-09-28, see L-0016b |
| Sample Animation Pack | `Content/SampleAnimationPack` | — | Installed, not used. Row added 2026-09-28, see L-0016b |
| World Flags | `Content/World_Flags` | — | Installed, not used. Row added 2026-09-28, see L-0016b |
| FP_AKS74U Animation | `Content/FP_AKS74U_Animation` | AKS-74U animations | Installed, not used. Row added 2026-09-28, see L-0016b |

| Field | Value |
|---|---|
| **Author** | Respective Fab sellers (see each pack's Fab page in the producer's library) |
| **Source** | Fab (fab.com), added to the project from the producer's Epic account |
| **Licence** | Fab Standard License |
| **Class** | **A** — no attribution required; source files must not be redistributed publicly (R-14) |
| **Status** | Raw packs git-ignored; project assets reference them by path (R-19) |

### L-0016b — The installed-pack register gap, found and closed 2026-09-28

| Field | Value |
|---|---|
| **What was found** | Nine Fab packs were installed in `Content/` and in active use with **no row in this register and no row in `ASSET_REGISTER.md`**: `Scene_QuarrySlate`, `Singapore_Canal`, `Modular_Rural_Cabin`, `Nanite_Plants_Sample_Collection`, `Military_Radio`, `Realistic_Starter_VFX_Pack_Vol2`, `SampleAnimationPack`, `World_Flags`, `FP_AKS74U_Animation`. `Scene_QuarrySlate` is the significant one: Dry River is built on its rock and gravel meshes, and Ravenshoe Crossing is specified on it |
| **How it was found** | Inventory of `Content/Downloaded/VaultCache/` (19 folders, ~36 GB) taken while scoping the Ravenshoe Crossing map. The cache is the Fab desktop staging area; all 18 of its content roots turned out to be **already installed** in `Content/`, which made the register's coverage testable in one pass |
| **Why it went unnoticed** | L-0016's table was written when Red Gum was built (ADR-022) and listed only the packs that had a *decision* attached to them. Packs added later — Dry River's rock, the radio props, the VFX — were installed through per-feature work without a register pass, so the rule in §1 ("no third-party asset enters this repository without a row") was being met in letter for those six packs but not in substance |
| **Class** | **A** — Fab Standard License, as for the rest of L-0016. **This is a bookkeeping correction, not a new clearance:** the same licence, publisher and source apply as the rows above, because these are the same Fab packs from the same producer library |
| **Action taken** | L-0016's table completed with a row per pack, each marked as added 2026-09-28. **No asset was imported, modified, moved or deleted.** No licence class changed |
| **Residual risk** | None identified. The gap was documentary, not legal: every pack is a Fab Standard Licence pack already in the producer's library. Had any of them turned out to be a different licence class, the finding would have been materially more serious, which is why the sweep was done rather than assumed |
| **Standing action** | Any future pack import must add its L-0016 row **in the same change** that imports it, not afterwards. The CI check in §1 covers `.uasset`/`.umap` files appearing without a register entry; the failure mode found here is a pack that is *already* imported, which that check does not catch |

### L-0017 — A88 textured model (producer-supplied download)

| Field | Value |
|---|---|
| **Component** | Bullpup rifle model with scope, foregrip, laser and suppressor; OBJ/3DS plus three 4K PNG atlases |
| **Source** | https://rigmodels.com/model.php?view=EF88_Rifle-3d-model__d1d54b9889924370a6d4576b004fa180 (aggregator; credits Upsurge Studios, upsurgestudios.com) |
| **Local copy** | `Art/Weapons/A88/New/` (not committed) |
| **Licence** | Aggregator page shows "Royalty Free"; the original author's terms are not shown and not yet confirmed |
| **Use** | Current A88 cosmetic mesh via `Tools/Blender/a88_sourced.py` and `setup_weapons.py` |
| **Status** | **Provisional** (R-21): record the URL and terms; reshape into an original A-series design (ADR-021) |
| **Producer decision — website promotion (2026-09-28)** | The producer directs that a render of the sourced EF88 model (the current in-game A88 cosmetic mesh) be published on the public website's Loadout section, and accepts the residual risk that the aggregator "Royalty Free" claim is unverified against the original author's terms. The site labels the render as the current internal model. Producer risk acceptance only; **not a legal clearance**; revisit before any commercial release. |

### L-0021 — ADF Re-Cut (ADFRC) pack, extracted into `Content/Sourced/ADF_Extracted/`

| Field | Value |
|---|---|
| **Component** | 268 `.p3d` (ODOL-binarised) models, 2,484 decoded PNG textures, 165 `.rtm` animations, Arma configs (`.cpp`/`.hpp`/`.cfg`), `.rvmat` materials, sounds, 37 ready-made `.uasset`s; ~7,748 files, ~17 GB |
| **Source** | Two origins, per the tree's own `README.md`: (1) the source/config distribution of **ADF Re-Cut / ADFRC**, `github.com/IsoBones/ADFRC`, under APL-SA; (2) the **binarised Steam Workshop release**, `!Workshop\@ADF Re-Cut [Beta]\addons` (15 `.pbo` archives, 5.8 GB). The GitHub repository ships no `.p3d` by design — all geometry exists only inside the Workshop PBOs |
| **Local copy** | `Content/Sourced/ADF_Extracted/` (git-ignored, inside the Unreal content root — see R-25) |
| **Authorisation** | **WRITTEN GRANT ON FILE.** Email from **Tonnie** to the producer, 2026-09-27 15:05, granting permission to use "the ADF ReCut models and associated assets that I have extracted" within the Southern Spear project, for development, testing, prototyping and inclusion in the game, in the extracted (unextracted-format) state. Verbatim transcription and the original screenshot are preserved at `Docs/evidence/L0021_adfrc_authorisation_email.txt` / `.png`. This is the evidence that moves this entry off the R-24 block for the grantor's own components |
| **Licence** | **Partially cleared — see conditions.** APL-SA (Bohemia, Arma distribution side) remains non-commercial and Arma-only and is **not** within a community author's gift to waive. ADFRC's `ASSETS_LICENSE.md` and `DEV_LICENSE.md` §2.4 restrict the protected models against extraction, derivatives, redistribution and use in other media; the grantor states he performed the extraction himself, which is the act those terms restrict, so his permission cures the *use* question for his own components but does not retrospectively license the extraction method. Attribution still cannot cure APL-SA |
| **Grant is narrower than it appears** | The email's third paragraph is a **disclaimer, not a warranty**: permission is granted "on the understanding that you remain responsible for ensuring compliance with any applicable intellectual property, licensing, copyright, or other legal requirements associated with the original source material." The grantor therefore expressly does **not** warrant that the material is free of third-party rights, nor that he holds every right he is granting. Recorded deliberately — this is the most consequential sentence in the message |
| **Scope limit — multi-author pack** | **RESOLVED 2026-09-27 (Session 032c).** ADF Re-Cut is multi-author: author strings in the extracted configs name **Brucey, Exer, Growlor, Louetta, Quiggs**, "ADFU Team" and "ADF Re-Cut Team", and "Tonnie" is not among them — so his grant could only ever have covered his own components. The producer has since obtained a **blanket 100% permission from the mod team as a whole**, which covers the whole pack including every credited author. Per-component confirmation is no longer required for import, development or inclusion in game. The limits that the mod team cannot lift are unchanged: the third-party marks below, and redistribution |
| **Additional conflict — unaffected by this grant** | Real manufacturer and service identities are present regardless of the grant: Crye Precision (G3), Ops-Core, PASGT, "Team Wendy", and ADF camouflage patterns. These belong to companies and to the ADF/Department of Defence, **none of whom are party to the email**. ADR-016 and L-0004 / L-0007 continue to bar them, and ADR-016 requires CMECU to be an original pattern. No private grant can clear these; they need legal review or removal of the marks |
| **Producer decision** | The producer has reviewed the above, **confirms the authorisation is genuine**, and accepts responsibility for the terms: Brucey/Tonnie are old mates, the Re-Cut team are content for these to be used in his free project. As of 2026-09-27 the producer additionally holds a **blanket 100% permission from the mod team**, which closes the multi-author scope limit. ADFRC material is treated as **free to use in Southern Spear**, including converted and derived work. Recorded as a **producer risk acceptance**, not as a legal clearance — the third-party items in the row below are unchanged by it. |
| **Producer decision — website promotion (2026-09-28)** | The producer directs that renders of the ADFRC-derived weapon models (A4, A416, A25, A89, A9) be published on the public website's Loadout section as promotion, and accepts the residual redistribution risk that the underlying ADFRC/APL-SA terms restrict use in other media. The site labels these as renders of the current internal models. This is a **producer risk acceptance**, not a legal clearance, and **does not extend to selling, merchandising or any commercial use**; it is to be revisited before any commercial release or storefront page. |
| **Use** | **Authorised by the producer for use in Southern Spear** (development, testing, prototyping, inclusion in game) in the unextracted format. Not cleared for **redistribution** — see git handling below. Branding substitutions still required before release (ADR-016 / R-27) |
| **Location** | Relocated 2026-09-27 to `Art/ADFRC/` (source: 177 `.p3d`, 1,471 PNG, 292 animation files, 68 configs). **Converted 2026-09-27** to `Art/ADFRC_MLOD/` (177 MLOD) and `Art/ADFRC_BLEND/` (**179 `.blend` with verified geometry**), including 40 optics and the `adfrc_SR25` DMR. Player/worn gear consolidated in `Art/ADFRC_Player/` (57 models + 1,538 textures). Every model has a sibling `_textures/` folder. See `Art/ADFRC/MANIFEST.md`, `Art/ADFRC_Player/README.md`. The full extraction remains at `Content/Sourced/ADF_Extracted/` |
| **Conversion tooling** | `UKSFTA-P3D` (ODOL v73–v75 debinarizer, built on .NET 10) plus Arma 3 Object Builder v2.5.1 in Blender 5.2. Both live **outside** the repository at `E:/_tools/`. One local patch to `BlenderExport.cs` so the generated Blender script also tries the `bl_ext.user_default.*` module id. The converted output is **derived work** from the L-0021 material and is covered by the same terms |
| **Git handling** | `Art/ADFRC/*` is **git-ignored**; only `LICENSE.md` and `MANIFEST.md` are tracked. Rationale: the authorisation is personal and non-commercial, and these are third-party source files, so they must not be redistributed via the repository. Without this rule 5.5 GB of third-party content would have become committable the moment it moved out of the already-ignored `Content/Sourced/` |
| **Status** | **Authorised for use (producer-accepted), Class E.** Release still gated on branding substitution (R-27) and legal review. R-28 (conversion) is **closed**; R-29 tracks the remaining gap — FBX export, Unreal materials, and unpacked textures |

### L-0022 — Original Southern Spear character materials (script-authored, applied over L-0016 bodies)

| Field | Value |
|---|---|
| **Component** | 12 PNG texture sets (CMECU dry-country camo, MAF red-earth camo, tan and dark gear fabric; base colour, twill micro-normal, ORM) and 4 materials `M_SS_CMECU`, `M_SS_MAF`, `M_SS_GearTan`, `M_SS_GearDark`, plus the per-slot override arrays on `ASSCharacterPartActor` |
| **Source** | Original work, generated by `Tools/Textures/make_character_textures.py` (PIL/numpy). No third-party texture was sampled, traced or converted; the ADFRC material was specifically **not** used as a pattern reference |
| **Licence** | Class **F** — original, ours to license |
| **Use** | Cosmetic material overrides on the L-0016 bodies. The vendor meshes are neither duplicated nor edited (ADR-004: appearance only) |
| **Status** | In use on 7 of 14 friendly slots and 5 of 7 MAF parts; no rendered in-game view yet (see changelog Session 026) |
| **Retune (Session 042)** | CMECU retuned from four tones to seven and MAF lifted ~15%, both measured against the producer's reference photography by `Build/audit/tune_camo.py` rather than eyeballed: reference fabric lum p10/p50/p90 = 40/129/235, median saturation 0.46, oxide-red population 8.7%; the regenerated sets score lum 43/107/205, sat 0.47, red 10.2%. Still noise-generated from the script's own fbm field — **no real-world camouflage was sampled, traced or converted, and AMCU/Auscam remain out of bounds (ADR-016)**. The four `M_SS_*` materials and the per-slot override arrays are unchanged; only the texture images differ. |
| **Website use (Session 042)** | Studio renders using these textures on the L-0016 body and L-0021 kit were published and then **withdrawn** in the same session; see ASSET_REGISTER §4.9. The camo itself is Class F and carries no restriction; the body and kit in the same image do, and it is those two layers that made the renders unsuitable to publish. |

### L-0023 — Session 044 additions (Fab, cleared under ADR-028; tooling)

| Component | Source | Use | Status |
|---|---|---|---|
| M4 and G17 FPS Weapon Animations packs (BarcodeGames) | Fab `38da8f1e…`, `5b920af4…`, Standard License | First-person arms and clips (`SSExp_ObjectiveAssault/FirstPerson`); the packs' real-weapon models are dropped in `fp_arms.py` | In use |
| African Slate Quarry (Scene_QuarrySlate) | Fab (Megascans) | Base of `L_Bluestone_01` (ADR-028 map-base note); Dry River stones | In use; git-ignored pack (R-41) |
| Military Trenches Wall Metal Corrugated 04 | Fab (Megascans) | `MI_SS_CorrugatedIron` texture set | In use |
| Gloves for fps game (Bobeer) | Fab, CC BY 4.0 | — | Not used; credit "Bobeer" if used |
| VibeUE (Kevin Buckley) | github.com/kevinpbuckley/VibeUE, MIT | Editor-only dev tooling, git-ignored clone | Not shipped |
