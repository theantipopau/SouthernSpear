# ASSET REGISTER — Southern Spear

**Document ID:** `Docs/ASSET_REGISTER.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army. All units, insignia, operations and places referenced are fictional.

---

## 1. Purpose

Every asset the game requires, its intended source, its current status, and its licence dependency. **No asset enters the repository without a matching `LICENCE_REGISTER.md` entry.**

### Status vocabulary

| Status | Meaning |
|---|---|
| `PLACEHOLDER` | A stand-in exists or is planned. **Not final. Does not ship.** |
| `VENDORED` | Third-party asset in use, licence verified and registered |
| `IN_PRODUCTION` | Original asset being created in Blender |
| `DONE` | Final, reviewed, licence-clean |
| `DEFERRED` | Not started; sequenced later |

---

## 2. Sourcing Rules (Mandatory)

Applied in this order, for every asset:

1. Check whether an existing project asset can be legally reused.
2. Search Fab from within Unreal Engine for a properly licensed asset.
3. Record asset, publisher, source, licence and modifications in `LICENCE_REGISTER.md`.
4. If no suitable asset exists, create an original placeholder.
5. Replace placeholders incrementally with original production assets created in Blender.
6. **Never** download assets from unverified model-ripping or redistribution sites.
7. **Never** assume "free" means unrestricted.
8. Preserve attribution where required.
9. Ensure every third-party asset can legally be included in a **packaged commercial product** before depending on it.

> **Known blocker (PROJECT_AUDIT R-03):** the in-editor Fab plugin requires the engine to be registered in the Epic Games Launcher. UE 5.8 is not currently registered, so step 2 may require manual download. Until resolved, all third-party acquisition is manual and every download is licence-verified by hand before import.

---

## 3. Content Folder Structure

```
Content/SouthernSpear/
├── Core/        shared materials, common meshes, UI fonts
├── Characters/  bodies, heads, helmets, carriers, webbing, packs, gloves, boots
├── Weapons/     first-person and third-person weapons
├── Equipment/   grenades, dressings, binoculars, optics
├── Animations/  locomotion, aiming, weapon poses
├── Audio/       gunfire, impacts, footsteps, ambience, UI, voice indicators
├── UI/          HUD, menus, CommonUI assets, icons
├── Maps/        map-specific content
├── Training/    training range and module content
├── Effects/     muzzle flash, tracers, impacts, suppression
├── Data/        DataTables and Data Assets
├── Developer/   developer-only content, never cooked into a shipping build
└── Vendor/      THIRD-PARTY ONLY — segregated, never destructively reorganised
```

Vendor content is isolated so licence audits are a single-directory operation.

---

## 4. Foundation Asset Register

### 4.1 Lyra Starter Game 5.8

| Item | Status | Notes |
|---|---|---|
| Lyra source + plugins | `VENDORED` | Licence **L-0001**. Basis of the project |
| Manny/Quinn skeleton + base meshes | `VENDORED` | Licence **L-0001**. Skeleton shared across all our soldiers |
| Lyra locomotion animations | `VENDORED` | Licence **L-0001**. Starting point, will be extended |
| Lyra example materials | `VENDORED` | Licence **L-0001** |

Lyra content is a **technical foundation, not Southern Spear art.** It is a placeholder in visual terms and must be replaced before release.

### 4.2 Weapons — Friendly force

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| W-001 | EF88-style 5.56 mm bullpup service rifle | `PLACEHOLDER` | — | Use the **Quinn/Manny** placeholder rifle initially. Original bullpup model required. **Original design, not a trace of manufacturer CAD** |
| W-002 | F89 Minimi-style 5.56 mm belt-fed support weapon | `PLACEHOLDER` | — | Bipod, belt box, third-person carry poses |
| W-003 | Generic service pistol | `PLACEHOLDER` | — | |
| W-004 | Smoke grenade | `PLACEHOLDER` | — | |
| W-005 | Fragmentation grenade | `PLACEHOLDER` | — | Simulation only; no real-world handling detail |
| W-006 | Field dressing | `PLACEHOLDER` | — | |
| W-007 | Binoculars | `PLACEHOLDER` | — | |
| W-008 | Role-dependent optics | `PLACEHOLDER` | — | Sockets exist from Phase 1; models later |

### 4.3 Weapons — Opposing force

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| W-101 | AK-pattern service rifle | `PLACEHOLDER` | — | **Original model.** Distinct silhouette. Not a copy of any manufacturer CAD or commercial game model |
| W-102 | AK-pattern support rifle / belt-fed LMG | `PLACEHOLDER` | — | Original model |
| W-103 | Generic sidearm | `PLACEHOLDER` | — | |
| W-104 | Smoke grenade (opposing) | `PLACEHOLDER` | — | Cosmetic variant, same gameplay data |
| W-105 | Fragmentation grenade (opposing) | `PLACEHOLDER` | — | Cosmetic variant, same gameplay data |
| W-106 | Field dressing (opposing) | `PLACEHOLDER` | — | Cosmetic variant |
| W-107 | Binoculars (opposing) | `PLACEHOLDER` | — | Cosmetic variant |

> **Gameplay parity:** W-001 and W-101 share one `WeaponId`'s gameplay data. Only the *presentation* differs. See TDD §3.4.

### 4.4 Characters

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| C-001 | Male soldier base body | `VENDORED` (Manny) → `IN_PRODUCTION` | L-0001 | Manny is a placeholder; original body required |
| C-002 | Female soldier base body | `VENDORED` (Quinn) → `IN_PRODUCTION` | L-0001 | Quinn is a placeholder; original body required |
| C-003 | Modular heads | `PLACEHOLDER` | — | |
| C-004 | Hair compatible with military headgear | `PLACEHOLDER` | — | Must not clip under helmets |
| C-005 | Helmets | `PLACEHOLDER` | — | |
| C-006 | Eye protection | `PLACEHOLDER` | — | |
| C-007 | Hearing protection | `PLACEHOLDER` | — | |
| C-008 | Plate carriers | `PLACEHOLDER` | — | |
| C-009 | Webbing | `PLACEHOLDER` | — | |
| C-010 | Packs | `PLACEHOLDER` | — | |
| C-011 | Gloves | `PLACEHOLDER` | — | |
| C-012 | Boots | `PLACEHOLDER` | — | |
| C-013 | Role-appropriate pouches | `PLACEHOLDER` | — | |
| C-014 | **Original multicam-style camouflage material** | `PLACEHOLDER` | — | **Original pattern. Must not reproduce a protected commercial texture.** Licence **L-0003** applies to review |
| C-015 | Hostile militia clothing set | `PLACEHOLDER` | — | Mixed field clothing, chest rigs, distinct silhouette |
| C-016 | Fictional unit insignia (friendly) | `PLACEHOLDER` | — | Original. Licence **L-0003** |
| C-017 | Fictional non-national insignia (hostile) | `PLACEHOLDER` | — | Original, non-national, non-real |
| C-018 | Rank slides / progression insignia | `PLACEHOLDER` | — | **Original placeholders only** until legal clearance — Licence **L-0003** |

> **Fictional hostile faction.** The opposing force is a fictional armed group (working name *Kestrel Militia*). It must not be drawn from any real ethnic, religious, political or contemporary armed group, and must carry no derogatory imagery, language or stereotypes.

### 4.5 Animation

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| A-001 | Locomotion (walk/jog/sprint/crouch) | `VENDORED` (Lyra) → extend | L-0001 | |
| A-002 | Prone set | `DEFERRED` | — | **Ships only if animation quality meets the bar** |
| A-003 | Lean (L/R) | `PLACEHOLDER` | — | |
| A-004 | Vault / mantle | `PLACEHOLDER` | — | |
| A-005 | First-person arms (no-body) | `PLACEHOLDER` | — | |
| A-006 | Additive aiming layer | `PLACEHOLDER` | — | |
| A-007 | Weapon-specific poses (per weapon) | `PLACEHOLDER` | — | |
| A-008 | Reload (tactical / empty) | `PLACEHOLDER` | — | |
| A-009 | Bipod deploy / stow | `PLACEHOLDER` | — | |
| A-010 | Foot IK / Hand IK targets | `PLACEHOLDER` | — | |
| A-011 | Incapacitation / downed | `PLACEHOLDER` | — | |
| A-012 | Death states | `PLACEHOLDER` | — | |
| A-013 | Animation LODs | `DEFERRED` | — | Phase 6 |

### 4.6 Audio

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| S-001 | Gunfire — interior | `PLACEHOLDER` | — | |
| S-002 | Gunfire — exterior | `PLACEHOLDER` | — | |
| S-003 | Distant gunfire tail | `PLACEHOLDER` | — | |
| S-004 | Mechanical weapon sounds (bolt, mag, bipod) | `PLACEHOLDER` | — | |
| S-005 | Bullet cracks (supersonic) | `PLACEHOLDER` | — | |
| S-006 | Impacts by surface | `PLACEHOLDER` | — | |
| S-007 | Suppression | `PLACEHOLDER` | — | |
| S-008 | Footsteps by surface | `PLACEHOLDER` | — | |
| S-009 | Equipment movement | `PLACEHOLDER` | — | |
| S-010 | Environmental ambience | `PLACEHOLDER` | — | |
| S-011 | Radio-filtered speech bed / processing | `PLACEHOLDER` | — | Processing only — **no recorded real speech** |
| S-012 | UI feedback | `PLACEHOLDER` | — | |
| S-013 | Voice channel indicators | `PLACEHOLDER` | — | Tones only, not speech content |

> **Voice privacy:** voice chat is **never recorded**. No voice asset is captured without explicit per-player consent and a documented privacy design. See GDD §4.4.

### 4.7 Effects

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| E-001 | Muzzle flash | `PLACEHOLDER` | — | |
| E-002 | Tracers | `PLACEHOLDER` | — | |
| E-003 | Impact decals + debris | `PLACEHOLDER` | — | |
| E-004 | Dust / weather | `DEFERRED` | — | Layer-driven |
| E-005 | Suppression visual | `PLACEHOLDER` | — | |
| E-006 | Smoke grenade | `PLACEHOLDER` | — | |

### 4.8 UI

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| U-001 | CommonUI input config | `VENDORED` (Lyra) | L-0001 | |
| U-002 | Front-end / main menu | `PLACEHOLDER` | — | |
| U-003 | In-game HUD (sparse) | `PLACEHOLDER` | — | |
| U-004 | Scoreboard | `PLACEHOLDER` | — | |
| U-005 | Server browser | `PLACEHOLDER` | — | |
| U-006 | Training menu | `PLACEHOLDER` | — | |
| U-007 | Barracks | `PLACEHOLDER` | — | |
| U-008 | Service record / progression screens | `PLACEHOLDER` | — | |
| U-009 | Settings screens (incl. accessibility) | `PLACEHOLDER` | — | |
| U-010 | Icons (UI + objective markers) | `PLACEHOLDER` | — | **Non-colour identifiers required** |
| U-011 | Insignia (rank, qualification badges) | `PLACEHOLDER` | — | Licence **L-0003** |
| U-012 | Post-round summary | `PLACEHOLDER` | — | |

### 4.9 Maps and Layers

All maps `PLACEHOLDER` unless marked. **Greybox only in Phase 1.** No final maps before the vertical slice works.

| ID | Map | Layers required | Status | Notes |
|---|---|---|---|---|
| M-001 | **Dry River** — rural training area, dry creek bed, scrub, farm structures, long sightlines, concealed approaches | Objective Assault, Secure and Hold, Day, Low-light | `PLACEHOLDER` | **Greybox first — the vertical slice map** |
| M-002 | **Red Ridge** — semi-arid ridgeline, radio installation, rocky terrain, strong elevation change | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-003 | **Ironbark** — eucalypt woodland, training compound, mixed close/medium ranges, bushfire-safe fictional setting | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-004 | **Port Wakefield** — fictional industrial port, warehouses, container yards, administrative buildings, maritime edge | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-005 | **Wattle Creek** — small regional settlement, service station, houses, council facilities, drainage corridors | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-006 | Training range | Training | `PLACEHOLDER` | Vertical slice |
| M-007 | Front end | — | `VENDORED` (Lyra) | L-0001 |

> **Layout rule:** no map may reproduce a real military base, sensitive installation, or any operationally useful site. Layouts are designed from gameplay requirements, not surveyed from any real location.
>
> **Scale rule:** World Partition only where scale justifies it. Small polished maps first.

### 4.10 Data Assets (no licence dependency — original data)

| ID | Asset | Type | Status |
|---|---|---|---|
| D-001 | `DF_SS_WeaponDefinition` table | `UPrimaryDataAsset` / `UDataTable` | `PLACEHOLDER` |
| D-002 | `DF_SS_RoleDefinition` | `UPrimaryDataAsset` | `PLACEHOLDER` |
| D-003 | `DF_SS_RankDefinition` | `UPrimaryDataAsset` | `PLACEHOLDER` |
| D-004 | `DT_SS_ProgressionCurve` | `UDataTable` | `PLACEHOLDER` |
| D-005 | `DF_SS_CommendationDefinition` | `UPrimaryDataAsset` | `PLACEHOLDER` |
| D-006 | `DF_SS_MapLayerDefinition` | `UPrimaryDataAsset` | `PLACEHOLDER` |
| D-007 | `DF_SS_TrainingModuleDefinition` | `UPrimaryDataAsset` | `PLACEHOLDER` |
| D-008 | `DF_SS_FactionPresentationSet` | `UPrimaryDataAsset` | `PLACEHOLDER` |
| D-009 | `DT_SS_GameplayTags` | `UDataTable` | `PLACEHOLDER` |
| D-010 | `DF_SS_ServerBrowserFilter` | `UPrimaryDataAsset` | `PLACEHOLDER` |

---

## 5. Summary — Current State

| Category | Placeholder | Vendored | In production | Done |
|---|---|---|---|---|
| Weapons (15) | 15 | 0 | 0 | 0 |
| Characters (18) | 16 | 2 (Lyra bodies, placeholder-quality) | 0 | 0 |
| Animation (13) | 9 | 4 (Lyra locomotion) | 0 | 0 |
| Audio (13) | 13 | 0 | 0 | 0 |
| Effects (6) | 6 | 0 | 0 | 0 |
| UI (12) | 11 | 1 | 0 | 0 |
| Maps / layers (7) | 2 | 1 | 0 | 0 |
| Data (10) | 10 | 0 | 0 | 0 |

**Everything is a placeholder. Nothing here is final.** That is the correct state for the end of Phase 0.

---

## 6. Placeholder Policy

1. A placeholder is **visibly** a placeholder — grey-boxed or primitive, never a low-effort imitation that could be mistaken for final art.
2. A placeholder carries no licence obligation and no attribution requirement.
3. Every placeholder is listed in this register until replaced.
4. Placeholders are acceptable in the vertical slice. **They are not acceptable in a release build**, and a release-build check that fails on any remaining placeholder is a packaging gate.

---

## 7. Register Maintenance

This register is updated **in the same commit** as any asset addition or status change. An asset that appears in the repository but not in this register is a build-review failure.

Each entry needs: a stable ID, the asset's name, its status, its licence dependency (or "original"), and where the source `.blend` lives if it is original production.
