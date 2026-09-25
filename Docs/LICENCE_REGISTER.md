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

### L-0012 — Electric Dreams environment (reference + selective harvest only)

| Field | Value |
|---|---|
| **Component** | "Electric Dreams" environment pack, staged at `E:\Unreal\Environment\` |
| **Status** | 🔴 **ACQUISED, TERMS NOT YET VERIFIED** |
| **Licence** | **UNREAD** |
| **Class** | **E — unresolved. Treated as class D (prohibited) until the licence text is read and recorded here.** |
| **Approved use** | **Generic modular pieces only** (e.g. concrete, steel, modular walls) — explicitly *not* as a base map |
| **Rejected use** | Base map, art direction, or any map derived from its layout or art style |

**Constraints on use:**
1. The environment's aesthetic is incompatible with the Australian bushland/industrial setting. It is **not** to be used as a base map, and no Southern Spear map may derive its layout or visual identity from it.
2. Only **generic, non-branded, non-stylised** modular pieces may be harvested. Anything carrying the pack's distinctive art direction, signature look, or branding is excluded.
3. Every harvested piece gets its **own** register row (L-0012.x) naming the specific piece, before it enters the repository.
4. Harvested pieces are to be **re-lit and re-surfaced** in our own original materials so they do not carry the source pack's visual signature into a shipping build.
5. The pack may additionally be used **outside the project** as a standalone GPU/Lumen/Nanite performance stress scene. That use carries no shipping obligation.

| Field | Value |
|---|---|
| **Action** | Read the Fab/EULA licence text in full, record the actual terms, then reclassify. If commercial packaging is not explicitly permitted, the harvest is abandoned. |

> Recorded before extraction, deliberately at class **E**. "Free" is not a licence category — an unread licence is treated as prohibited.

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

Separately from copyright, the following are **hard constraints** on the fiction:

1. **The hostile faction is fictional.** It must not represent any real ethnic, religious, political, or contemporary armed group.
2. **No culturally derogatory imagery, language or stereotypes.** The faction is designed to be tactically credible, not caricatured.
3. **Fictional insignia, names and backstory** throughout.
4. **No real base, installation or operationally useful site layout** in any map.
5. **No realistic manufacturing, modification or unlawful-use instructions.** All weapon work is game simulation.

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
