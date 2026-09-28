# ASSET REGISTER — Southern Spear

**Document ID:** `Docs/ASSET_REGISTER.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-27

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army. All units, insignia, operations and places referenced are fictional.

---

## 1. Purpose

Every asset the game requires, its intended source, its current status, and its licence dependency. **No asset enters the repository without a matching `LICENCE_REGISTER.md` entry.**

### Status vocabulary

| Status | Meaning |
|---|---|
| `PLACEHOLDER` | A stand-in exists or is planned. **Not final. Does not ship.** |
| `VENDORED` | Third-party asset or source copy present in the project; exact licence verified and registered (use/import readiness stated separately) |
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
| W-001 | A88 Standard Service Rifle (fictional; original bullpup design) | `IN_PRODUCTION` | L-0017 (Class E pending verification) | The original script-built A88 remains as project source; the current in-game cosmetic mesh is a producer-supplied textured A88 imported under `/SSExp_ObjectiveAssault/Weapons/A88/`. Its source URL/terms are missing and its real-rifle resemblance needs original A-series reshaping (R-21). The imported `.uasset` derivative is tracked; do not treat it as cleared or release-ready. |
| W-002 | A89 Light Support Weapon (fictional; original belt-fed design) | `IN_PRODUCTION` | Class F — original | First-pass original script-built A89 is in the game; 1.19 m, 2,012 tris. Bipod and third-person carry poses remain to be validated. |
| W-003 | A9 Service Pistol (fictional) | `PLACEHOLDER` | — | |
| W-004 | Smoke grenade | `PLACEHOLDER` | — | |
| W-005 | Fragmentation grenade | `PLACEHOLDER` | — | Simulation only; no real-world handling detail |
| W-006 | Field dressing | `PLACEHOLDER` | — | |
| W-007 | Binoculars | `PLACEHOLDER` | — | |
| W-008 | Role-dependent optics | `PLACEHOLDER` | — | Sockets exist from Phase 1; models later |

### 4.3 Weapons — Opposing force

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| W-101 | MAF service rifle display mesh (cosmetic counterpart to A88; same gameplay definition) | `PLACEHOLDER` | — | **Original model.** Distinct silhouette. Not a copy of any manufacturer CAD or commercial game model |
| W-102 | MAF support weapon display mesh (cosmetic counterpart to A89) | `PLACEHOLDER` | — | Original model |
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
| C-014 | **Commonwealth Multi-Environment Combat Uniform (CMECU) material** | `PLACEHOLDER` | — | **Original pattern. Must not reproduce AMCU, commercial MultiCam or any protected texture.** Licence **L-0003** applies to review |
| C-015 | Murasian Armed Forces clothing set | `PLACEHOLDER` | — | Red-earth disruptive camouflage (ochre, rust, dark brown, muted burgundy, charcoal), chest rigs, distinct silhouette. Conventional military, **not** an ethnic or religious militia |
| C-016 | Fictional unit insignia (CDS/CLS/ACR) | `PLACEHOLDER` | — | Original. **No ADF corps badge, Rising Sun, colour patch, motto or battle honour.** Licence **L-0003** |
| C-017 | Fictional Murasian Armed Forces insignia | `PLACEHOLDER` | — | Original, invented, not drawn from any real armed group |
| C-018 | Rank slides / progression insignia | `PLACEHOLDER` | — | **Original placeholders only** until legal clearance — Licence **L-0003** |

> **Fictional opposing force (ADR-016).** The **Murasian Armed Forces** are a fictional conventional military force. They must not be drawn from any real state, ethnicity, religion, political movement or contemporary armed group, and must carry no derogatory imagery, language or stereotypes. They are presented as a credible professional military, never as terrorists, extremists or a racial caricature. Faction recognition must never rely on colour alone.

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
| M-001 | **Dry River** — rural training area, dry creek bed, scrub, farm structures, long sightlines, concealed approaches | Objective Assault (sequential A→B), Day | `PLACEHOLDER` — **blockout generated** | **The vertical slice test bed.** Original blockout authored in Blender; see `Docs/MAPS_DRYRIVER.md` |
| M-002 | **Red Ridge** — semi-arid ridgeline, radio installation, rocky terrain, strong elevation change | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-003 | **Ironbark** — eucalypt woodland, training compound, mixed close/medium ranges, bushfire-safe fictional setting | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-004 | **Port Wakefield** — fictional industrial port, warehouses, container yards, administrative buildings, maritime edge | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-005 | **Wattle Creek** — small regional settlement, service station, houses, council facilities, drainage corridors | Objective Assault, Secure and Hold, Day, Low-light | `DEFERRED` | Phase 4 |
| M-006 | Training range | Training | `PLACEHOLDER` | Vertical slice |
| M-007 | Front end | — | `VENDORED` (Lyra) | L-0001 |

> **Layout rule:** no map may reproduce a real military base, sensitive installation, or any operationally useful site. Layouts are designed from gameplay requirements, not surveyed from any real location.
>
> **Scale rule:** World Partition only where scale justifies it. Small polished maps first.

### 4.9a Dry River blockout — generated assets

| ID | Asset | Path | Status | Licence dep. |
|---|---|---|---|---|
| M-001a | Source blockout | `Content/Art/Blockout/SS_MAP_DryRiver_01_HI.blend` | `IN_PRODUCTION` | Class F — original |
| M-001b | Game import mesh | `Content/Art/Blockout/SS_MAP_DryRiver_01.fbx` | `IN_PRODUCTION` | Class F — original |
| M-001c | Gameplay layout markers | `Content/Art/Blockout/SS_MAP_DryRiver_01_Layout.csv` | `IN_PRODUCTION` | Class F — original |
| M-001d | Blockout generator | `Tools/Blender/dryriver_blockout.py` | `DONE` | Class F — original |
| M-001f | Objective Assault Game Feature data | `/SSExp_ObjectiveAssault/SSExp_ObjectiveAssault` | `IN_PRODUCTION` | Class F — original data; generated by `Tools/Unreal/setup_objective_assault.py`. References ShooterCore/Lyra components by path only |
| M-RG-01 | Red Gum Station map | `/Game/Maps/L_RedGum_01`; source `Tools/Unreal/build_redgum_level.py`, `build_redgum_nav.py` | `IN_PRODUCTION` | Class A base (L-0016, ADR-022) plus original wiring |
| C-SOL-01 | Soldier body part (3 ACR / MAF) | `/SSExp_ObjectiveAssault/Characters/B_SS_Soldier`, `B_SS_CharacterParts`; source `Tools/Unreal/setup_soldiers.py` | `IN_PRODUCTION` | Class A meshes (L-0016) in an original part actor |
| W-A89-01 | A89 light support weapon, first pass | `/SSExp_ObjectiveAssault/Weapons/A89/*`; source `Tools/Blender/a89_support.py` | `IN_PRODUCTION` | Class F — original (ADR-020); 2,012 tris, 119 cm |
| W-A88-01 | Original A88 first-pass source mesh | `Art/Weapons/A88/SM_A88.fbx`; source `Tools/Blender/a88_rifle.py` and `Art/Weapons/A88/A88.blend` | `IN_PRODUCTION` — original source retained | Class F — 2,632 tris, 89 cm. This original first pass is retained as source; the current imported game mesh is the separate provisional W-A88-02. |
| W-A88-02 | Textured producer-supplied A88 derivative and game import | Source `Art/Weapons/A88/New/` → `/SSExp_ObjectiveAssault/Weapons/A88/SM_A88` and `T_A88_*` | `IN_PRODUCTION` — provisional / blocked | L-0017, Class E pending source/licence verification (R-21). Pipeline report records 78.8 cm and 72,493 tris; manually assigned texture atlases; not reshaped into a distinct original A-series silhouette. The derived Unreal assets are tracked even though raw source files are local/untracked. |
| M-001g | Objective Assault experience | `/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault` | `IN_PRODUCTION` | Class F — original data; uses ShooterCore pawn data and action sets (Lyra, EULA) by reference |
| M-001e | Layout verifier | `Tools/Blender/verify_dryriver.py` | `DONE` | Class F — original |

**Generated 2026-09-26.** 162 objects, 8,944 faces. 4 gameplay markers. Verified against the design spec by `verify_dryriver.py`, which runs in CI.

All class F — created specifically for this project, no third-party obligation. Registered in `LICENCE_REGISTER.md` §4.

### 4.9b Licensed environment source meshes — staged for review/import

| ID | Asset | Path | Status | Licence dep. | Notes |
|---|---|---|---|---|---|
| ENV-001 | Split Point, Victoria photogrammetry source | `Content/SouthernSpear/Vendor/SAVollgger/SplitPointVictoria/` (OBJ, MTL, JPEG) | `VENDORED` — source staged; UE import not yet verified | L-0013 (CC BY 4.0) | 174,076 vertices / 346,200 triangles; dense scan, not optimized. Original source filenames retained; attribution in folder README. |
| ENV-002 | Bingie Bingie, NSW photogrammetry source | `Content/SouthernSpear/Vendor/SAVollgger/BingieBingieNSW/` (OBJ, MTL, JPEG) | `VENDORED` — source staged; UE import not yet verified | L-0014 (CC BY 4.0) | 273,042 vertices / 540,708 triangles; dense scan, not optimized. Original source filenames retained; attribution in folder README. |

These are raw vendor files, not approved shipping meshes. They may be useful for environment/blockout reference and landscape dressing after import review; keep map layouts original. Any derivative that is retopologized, retextured, split, or otherwise adapted must get an explicitly tracked asset entry and preserve the required attribution.

### 4.9c Licensed third-party attribution

Ship the following attribution when the corresponding scans are included in a build:

- **Split Point, Victoria (Australia)** — Stefan A Vollgger, CC BY 4.0, https://sketchfab.com/3d-models/split-point-victoria-australia-d95f3ad4d0044c20a56ebb7bd507d515
- **Bingie Bingie, NSW (Australia)** — Stefan A Vollgger, CC BY 4.0, https://sketchfab.com/3d-models/bingie-bingie-nsw-australia-b3cdf8650ee44dd786f205c6c849ad59

Changes: source files staged unchanged; no modifications to mesh or texture data. License: https://creativecommons.org/licenses/by/4.0/.

### 4.9d Weapon source review — provenance pending

| Source folder | Current file | Finding | Allowed next step |
|---|---|---|---|
| `Art/Weapons/A88/New/` | OBJ, MTL, 3DS, three PNGs, derived FBX | **BLOCKED / R-21.** Existing notes report the MTL references filenames absent from the folder; 72k-triangle mesh is a real-rifle-like design. Producer says royalty-free, but no source URL or terms are recorded. The FBX is a derivative and does not establish rights. | Keep local/uncommitted. Obtain original source URL and licence terms; inspect/re-shape into an original A-series design before release. |
| `Art/Weapons/AKM/Weathered AKM rifle.blend` | Blender source | **REFERENCE ONLY / BLOCKED (R-23).** Filename identifies a real AKM design; source URL, author and licence evidence are absent. | Do not import, adapt or ship; confirm whether this is for visual reference only or provide rights/provenance. Create original A-series geometry independently. |
| `Art/Weapons/PKM/PKM.blend` | Blender source | **REFERENCE ONLY / BLOCKED (R-23).** Filename identifies a real PKM design; source URL, author and licence evidence are absent. | Same: keep out of game content; clarify provenance and use scope. |
| `Art/Weapons/C4A1/kkanamalla_m4_carbine.blend` | Blender source; adjacent `textures(1)/` is empty in this checkout | **BLOCKED / R-22.** Session 021 notes that the file contains a "Cycles-Ready M4 Carbine … Licensed CC-BY" label and the author identifier `kkanamalla`, but no exact source page/version/text or attribution record is present. A filename or embedded note is not the licence grant. It also depicts a real M4. | Keep unimported/uncommitted. Obtain the exact source URL and applicable CC BY version, preserve attribution, and reshape into an original A-series design before any game use. |

**Intake rule:** files under `Art/Weapons/` are local source/review material, not automatically approved game assets. For future intake, verify provenance, licence and intended use in `LICENCE_REGISTER.md` before importing or creating derivatives; any third-party weapon still needs an original fictional redesign per ADR-021. The A88 import predates this review and is already referenced by the experience: it remains blocked for release, and must not be treated as licence-cleared or expanded into other builds until R-21 is resolved.

**Website promotion exception (producer decision, 2026-09-28):** the public website's Loadout section shows renders of the current internal weapon models — the ADFRC-derived A4, A416, A25, A89 and A9, the sourced EF88 as the A88, and the sourced AKM as an external reference render explicitly labelled as not a game weapon. This is a recorded producer risk acceptance (see LICENCE_REGISTER L-0017 and L-0021), not a licence clearance, and does not change the blocked status of any of these assets for release. The AKM and PKM remain reference-only (R-22/R-23): the AKM is published as a labelled reference render at the producer's direction; the PKM is not published.

### 4.9e ADFRC extraction — quarantined, not a game asset

`Content/Sourced/ADF_Extracted/` is a separate ADF Re-Cut (ADFRC) Arma-content extraction, tracked for metadata/provenance review only under L-0021 / R-24. It is **not** a source asset for Southern Spear and has no game-asset ID. The `Models/ADF_Weapons/adfrc_ef88/` and `adfrc_m4a5/` `.p3d` files are real EF88 and M4A5-family content; they are not the independent sources in `Art/Weapons/A88/New/` (L-0017 / R-21) or `Art/Weapons/C4A1/` (L-0020 / R-22). Other ADFRC weapon/gear categories, Arma configs, textures and `.rtm` animations are likewise excluded. Do not promote any of these into W-001/A88, the C4A1 intake, or the A-series weapon pipeline; no copying, importing, conversion, derivative, or visual-reference use is approved. The ADFRC contributor agreement does not itself grant Southern Spear downstream rights. See `Docs/SOURCED_ASSET_REVIEW.md` for the source/rights basis.

### 4.9f Original character uniforms — applied to the licensed bodies

| ID | Asset | Path | Status | Licence dep. | Notes |
|---|---|---|---|---|---|
| CH-TEX-001 | CMECU camouflage set (3 ACR) | `Art/Characters/Textures/T_SS_CMECU_Camo_{BC,N,ORM}.png` (2048²) | `DONE` | Class F — original, script-built | Generated by `Tools/Textures/make_character_textures.py` from multi-octave value noise. Sun-bleached dry-country palette: khaki, pale dust, eucalypt grey-green, ironbark red-brown. **Original pattern** — not AMCU, not commercial MultiCam, not derived from ADFRC/Auscam material (ADR-016, L-0021). |
| CH-TEX-002 | MAF camouflage set (opposing force) | `Art/Characters/Textures/T_SS_MAF_Camo_{BC,N,ORM}.png` (2048²) | `DONE` | Class F — original | Red-earth disruptive per ADR-016/C-015: ochre, rust, dark brown, muted burgundy, charcoal. |
| CH-TEX-003 | Gear fabric sets (tan, dark) | `Art/Characters/Textures/T_SS_Gear{,_Dark}_{BC,N,ORM}.png` (1024²) | `DONE` | Class F — original | Near-solid dyed nylon with fine grain and a twill micro-normal. |
| CH-MAT-001 | Original fabric materials | `/SSExp_ObjectiveAssault/Characters/Materials/M_SS_{CMECU,MAF,GearTan,GearDark}` | `IN_PRODUCTION` | Class F — original | Authored by `Tools/Unreal/setup_character_textures.py`: TextureCoordinate → tiled UV0 into BC / normal / ORM, wired to BaseColor, Normal, and AO/Roughness/Metallic. |
| CH-SOL-001 | Original-uniformed soldier bodies (3 ACR + MAF) | `/SSExp_ObjectiveAssault/Characters/B_SS_Soldier` with `FSSPartMaterialOverride` | `IN_PRODUCTION` | Base meshes **L-0016 (Class A)**; appearance Class F | The Fab meshes are **not duplicated or edited**. `ASSCharacterPartActor` gained `FriendlyMaterialOverrides` / `OpposingMaterialOverrides`, applied per material slot on the character-part components. Friendly: cap, holster, carrier, patches and boonie → GearTan; shirt and jeans → CMECU. MAF: sweater and pants → MAF; shoes, armour and beret → GearDark. Skin, eyes, teeth, head and sidearm keep the vendor materials. |

> **R-20 partial:** the `M_Patches` slot is now overridden with plain gear fabric, so any insignia carried by the vendor patch texture is no longer displayed. A rendered confirmation is still outstanding (see Session 026).

### 4.9g ADFRC-derived game assets (L-0021, ADR-025)

Cleared for use in the project; the source files stay git-ignored (`Art/ADFRC/`); the repository holds LFS pointers only (R-14).
Third-party marks and ADF camouflage must be stripped or swapped before release (R-27).

| ID | Asset | Path | Status | Licence dep. | Notes |
|---|---|---|---|---|---|
| AUD-AUG-001 | AUG weapon audio (28 SoundWaves, 2 attenuations) | `/Game/AUG/Sound/` | `IN_PRODUCTION` | L-0021 | Imported by `Tools/Unreal/import_aug_audio.py` (Session 032b). |
| CH-ADF-001 | ADF and MAF gear skeletal meshes on Lyra's skeleton | `/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_*`, `SK_MAF_*`, `MI_ADF_*` | `IN_PRODUCTION` | L-0021; skeleton L-0016 (Epic) | `Tools/Blender/adfrc_gear_rig.py` + `Tools/Unreal/setup_adf_soldier.py` (Sessions 031, S1). |
| GP-DMG-001 | Hit-zone physical materials, per-weapon instances | `/SSExp_ObjectiveAssault/Characters/Physics/PM_SS_*`, `Weapons/*/B_SS_WeaponInstance_*` | `IN_PRODUCTION` | Class F (data); instances copied from Lyra (Epic) | `Tools/Unreal/setup_damage_model.py` (Session 034). |

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
| Weapons (15) | 13 | 0 | 2 (W-001 A88, W-002 A89; A88 source provisional under R-21) | 0 |
| Characters (18) | 16 | 2 (Lyra bodies, placeholder-quality) | 0 | 0 |
| Animation (13) | 9 | 4 (Lyra locomotion) | 0 | 0 |
| Audio (13) | 13 | 0 | 0 | 0 |
| Effects (6) | 6 | 0 | 0 | 0 |
| UI (12) | 11 | 1 | 0 | 0 |
| Maps / layers (7) | 1 | 1 | 1 (Dry River blockout generated) | 0 |
| Data (10) | 10 | 0 | 0 | 0 |
| Tooling (2) | 0 | 0 | 0 | 2 (blockout generator + verifier) |

**The weapon intake in §4.9d is not cleared game content.** Its raw source files remain local review material; W-001's imported A88 appearance is provisional under R-21, while W-002 is original work in production. The licensed photogrammetry sources in §4.9b are unchanged review copies and are not imported Unreal assets. Neither source group is approved as game-ready content.

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
