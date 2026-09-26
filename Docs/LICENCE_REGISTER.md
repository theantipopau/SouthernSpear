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
