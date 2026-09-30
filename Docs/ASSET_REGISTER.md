# ASSET REGISTER — Southern Spear

**Document ID:** `Docs/ASSET_REGISTER.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-29

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
| E-001 | Muzzle flash | `PLACEHOLDER` | — | Lyra's fire-cue sprite, moved onto the visible barrel (`ASSCharacter::AlignLyraMuzzle`), plus a code-driven muzzle light (`USSMuzzleLightSubsystem`, Session 060, no asset). A realistic flash sprite is still to choose. |
| E-002 | Tracers | `PLACEHOLDER` | — | |
| E-003 | Impact decals + debris | `PLACEHOLDER` | — | |
| E-004 | Dust / weather | `DEFERRED` | — | Layer-driven |
| E-005 | Spent cases | `PLACEHOLDER` | — | Engine cylinder in a brass tint, sized per calibre (`USSShellEjectSubsystem`, Session 059). A modelled case would replace the cylinder. |
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
| M-001 | **Dry River** — rural training area, dry creek bed, scrub, farm structures, long sightlines, concealed approaches | Objective Assault (sequential A→B), Day | `PLACEHOLDER` — **greybox, in the game** | **The vertical slice test bed** and the design standard. Playable area expanded to 340 × 240 m and dressed from cleared Class A packs (Session 044). `MAPS_PLAYABILITY_AUDIT.md` scores it 3 pass / 6 fail against its own rules. Original blockout authored in Blender; see `Docs/MAPS_DRYRIVER.md` |
| M-002 | **Red Gum Station** — 1 km outback station: open paddocks, gum-tree lines, fences, homestead | Objective Assault, Day | `PLACEHOLDER` — **in the game, measured not ready** | First playable map (ADR-022). Objectives re-laid and deployments pulled in for fairness; no capture yet. `MAPS_PLAYABILITY_AUDIT.md` measures it at 17% nav coverage, 12 hard and 0 soft cover, and calls it not playable as it stands. `Docs/MAPS_REDGUM.md` |
| M-003 | **Selat Canal** — urban canal district: walkable canal core, buildings and interiors | Objective Assault (three objectives), Day | `PLACEHOLDER` — **built, in production** | The only Special Forces map. Best close-quarters geometry measured in the project (2 m open crossings) and the worst objective placement: all three objectives 42–75% walk-imbalanced. `MAPS_PLAYABILITY_AUDIT.md` scores 5 pass / 5 fail. `Docs/MAPS_SELATCANAL.md` |
| M-004 | **Saltbush** — open semi-arid range, built to test engagement ranges past 200 m | Objective Assault, Secure and Hold, Day, Low-light | `PLACEHOLDER` — **built, in production** | Deployment and objective layout rebuilt for fairness; has produced a capture in a bot match. Measured at 7 pass / 3 fail by `MAPS_PLAYABILITY_AUDIT.md` — the strongest of the four audited maps. `Docs/MAPS_SALTBUSH.md` |
| M-005 | **Bluestone** — flooded slate pit converted from a studio diorama: loading bay, cutting face, spoil heaps | Objective Assault, Day | `PLACEHOLDER` — **built, on the operations menu** | Built 2026-09-28 from the slate-pit diorama by `Tools/Unreal/build_objective_map.py` (`quarry`); showroom and light bars stripped, open daylight, complex collision, boundary rim and three objectives, all legs connecting. Paused for fine-tuning; no design document yet, and not yet audited |
| M-006 | Training range | Training | `PLACEHOLDER` | Vertical slice. The MOUT kit (4.9j) is a *close-quarters village*, not an open firing range, and as of 2026-09-30 it is committed to **Wandarra (M-009)** as the urban half of training; what fills this entry — an open range on Saltbush's pattern or a redefinition — is still the producer's call. See `MAPS_TRAININGRANGE.md`, `MAPS_WANDARRA.md` |
| M-007 | Front end | — | `VENDORED` (Lyra) | L-0001 |
| M-008 | **Ravenshoe Crossing** — high-country gorge crossed by a wrought-iron lattice-girder road bridge; stone road-gate house on the far abutment; playable creek bed beneath giving a second lane | Objective Assault (sequential A→B), Day | `IN_PRODUCTION` — **in Unreal, 467 actors, 32/32 audit checks** | `/Game/Maps/L_Ravenshoe_01`; `Docs/MAPS_RAVENSHOE.md`, ADR-027. Original layout and original structures; dressed with already-installed Class A packs referenced in place |
| M-009 | **Wandarra** — invented urban training village: two crossing streets, lookalike bungalows and two-storey houses, a fenced depot compound, civic block, park and green, church terminating the cross street | Objective Assault (sequential A→B→C), Day | `PLACEHOLDER` — **built greybox, navmesh not yet baked (R-82)** | `/Game/Maps/L_Wandarra_01`; `Docs/MAPS_WANDARRA.md`. Built (not copied) by the Dry River pipeline pattern from the MOUT kit (4.9j), RustyCars wrecks (4.9j) and EuropeanBeech trees (4.9k); layout spec `Tools/Common/wandarra_spec.py`. Producer decision 2026-09-29: one big map from these packs |

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
| M-RG-01a | Homestead compound — farmhouse, shearing shed, stock pens, water tank, windmill, two stockman's huts | `Content/Art/Environment/RedGum/SS_RedGum_Homestead.blend` (source, LFS) + `SS_RedGum_*.fbx` → `/Game/Art/Environment/RedGum/*` with 5 authored materials; source `Tools/Blender/redgum_homestead.py`, importer `Tools/Unreal/import_redgum_homestead.py` | `IN_PRODUCTION` | **Class F — original, no third-party dependency.** Modelled from scratch because the Rural Australia pack has no building mesh and the other installed packs are the wrong continent or culture (ADR-013, ADR-021, L-0011). 7 structures, ~2,350 tris, LFS-tracked. Placement anchored to objective B by label, not coordinates |
| M-RG-01b | Rural dressing and play-space expansion | `Tools/Unreal/expand_redgum.py`; 1,140 actors in `L_RedGum_01` | `IN_PRODUCTION` | Class A pack meshes (L-0016) referenced in place, never modified; layout original. Seeded and idempotent, owned by the `SS_RedGum_Dress_v1_` prefix |
| M-008a | Ravenshoe Crossing blockout | `Tools/Common/ravenshoe_spec.py` + `Tools/Blender/ravenshoe_blockout.py` → `Content/Art/Blockout/SS_MAP_Ravenshoe_01_HI.blend` (LFS), `SS_MAP_Ravenshoe_01.fbx`, `SS_MAP_Ravenshoe_01_Layout.csv` | `DONE` — terrain 200 × 300 m, 15,000 faces, relief −18..+28 m; 72 layout rows | Class F — original (ADR-027, L-0011). Shared-spec-with-CI pattern per `dryriver_blockout.py` / `dryriver_spec.py`; every dimension read from the spec so generator and verifier cannot disagree |
| M-008b | Iron lattice-girder road bridge — trusses, uprights, deck, parapets, abutments, 10 lamp standards | `Content/Art/Blockout/SS_Raven_Bridge.fbx`; 68 m span, 20 bays of 3.4 m, 21 uprights/side, 7.5 m deck, 1266 faces | `DONE` — authored with **deck top at z=0**, placed by deck level; four material slots (Iron / Deck / **Road** / Stone) | **Class F — original, no third-party dependency.** Modelled because **no bridge mesh exists in the project or in any installed pack** (430-hit keyword sweep returned only rock, stone *materials* and audio). Same reasoning as M-RG-01a. The `Road` slot is the running surface, split off the deck slab by polygon so the slab's fascia and soffit can be painted steel while the top is road — one slot cannot be both, and the fault is invisible from the deck |
| M-008c | Stone road-gate house — granite rubble, 9.6 × 6.8 × 6.0 m, 4.6 m eaves, 1.2 m parapet, 3.4 × 3.6 m arched road passage, 17-stone segmental arch | `Content/Art/Blockout/SS_Raven_Gatehouse.fbx`; 450 faces | `DONE` — authored at its real position (0, 62) and rebased to its own footprint centre, base at 0 | **Class F — original.** The only installed building pack is Singapore_Canal, which is Asian canal architecture and ruled out on look and culture (ADR-016). Verified by ray cast: passage clear end to end, spandrel solid above the crown, piers solid |
| M-008d | Gorge heightfield, road corridor, both traverse ramps | in `SS_MAP_Ravenshoe_01.fbx` | `DONE` — ramps 133 m @ 17.6° east, 142 m @ 16.2° west, no pitch above the design grade | Class F terrain shell, to be dressed with `Scene_QuarrySlate` rock referenced in place (L-0016b) |
| M-008e | Ravenshoe layout and geometry verifier | `Tools/Blender/verify_ravenshoe.py` | `DONE` — **53/53 pass**; spec mode runs in CI with no Blender | Class F — original. Fails the build if S→OBJ A and N→OBJ A differ by more than 0.5 m, if any intent route has an uncovered run over 20 m, or if a ramp pitch exceeds the design grade. Also prints the bridge metric table every run and range-checks the **ratios** (span:truss depth inside 1:12–1:20, clear lane ≥ 6 m, headroom ≥ 4 m, bay 2.5–4.0 m), which can all be wrong while every dimension still reads as the value typed into the constant |
| M-008f | Blockout preview renders | `Build/ravenshoe/raven_*.png`; generator `Tools/Blender/ravenshoe_render.py` | `DONE` — 6 Workbench views | Class F — original. Shape check, not look-dev |
| M-008g | Imported mesh assets | `/Game/Art/Environment/Ravenshoe/Meshes/SS_MAP_Ravenshoe_01`, `SS_Raven_Bridge`, `SS_Raven_Gatehouse` | `IN_PRODUCTION` | Class F — original, imported by `Tools/Unreal/import_ravenshoe.py` with generated simple collision and `CTF_USE_DEFAULT` |
| M-008h | Authored flat safety-net materials | `/Game/Art/Environment/Ravenshoe/Materials/MI_SS_RavenFlat_{Iron,Stone,Deck,Road,Terrain}` | `DONE` — superseded by M-008m on the bridge, deck and masonry; still the terrain's material | Class F — original. **Was `M_SS_Raven_{Iron,Stone,Deck,Terrain}` and never worked**: it called `MaterialEditingLibrary.get_material_property`, which does not exist in 5.8, so the call raised, was swallowed as a warning, and the materials were created with engine defaults. They are now instances of `M_SS_ScanPBR` carrying a `Tint`, so a flat colour is a parameter rather than an expression-graph edit |
| M-008l | Prop material instances | `/Game/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_{Wreck,WreckJunk,FuelDrum,Metal,Timber,Canvas}` | `DONE` | Class F — authored, **not copies of the vendor material**. All six are instances of the project's own parameterised `M_SS_ScanPBR` (`Tint`, `Tiling`, and `BaseColor`/`Normal`/`Roughness`/`AO`/`Metalness` slots), so pack textures from several sources feed one shader instead of one shader per prop. Parameter values were read back off the working `MI_SS_CorrugatedIron` rather than guessed — the wreck pack ships an albedo and a grunge map and **no** normal, roughness, AO or metalness |
| M-008i | Gorge and approach dressing — 424 actors | `L_Ravenshoe_01`, labelled `SS_Raven_Cover_*` / `SS_Raven_Dress_*` | `IN_PRODUCTION` | **Class A pack meshes referenced in place, never modified** (L-0016, L-0016b): `Scene_QuarrySlate` ledge/rock clusters, `RuralAustralia` trees, logs, fence. Trees and wire are collision-off (ADR-022) — Lyra has no vault and a colliding wire fence splits the navmesh |
| M-008j | **Fab prop layer** — burning car wreck on the bridge deck at OBJ A, second wreck in the creek bed, fuel drums, sandbag and corrugated-panel cover on both approaches, water tower and hand pumps on the road edge, windmill and barn on the north ridge, old barn on the south ridge, plus fire / smoke / ember effects | `/Game/Art/Environment/Ravenshoe/Props/*` and `…/Materials/MI_SS_Raven_*`; built by `Tools/Blender/prep_fab_props.py` → `Tools/Unreal/dress_ravenshoe_props.py`; verified by `Tools/Unreal/audit_ravenshoe.py` | `DONE` — **35 actors placed, 35/35 audit checks** | **Class A — vendor meshes prepped then referenced in place, never modified** (ADR-004, ADR-021, L-0016c). Prep is mechanical: rescale to real-world size, strip the vendor's ground plane, re-pivot base-at-z=0, decimate to budget. **The wreck, windmill, fuel drum, sandbag stack and corrugated wall come from listings flagged `isAiForbidden: true`, or from a folder with no `metadata` at all — see L-0016c for the producer's decision and the residual risk** |
| M-008m | **Generated surface textures** — sealed gravel road, rusted ironwork, painted steel, coursed granite rubble | `Art/Environment/Ravenshoe/Surfaces/T_SS_Raven_{Gravel,RustIron,PaintedSteel,Granite}_{BC,N,R,AO,M}.png` (20 × 1024²); generator `Tools/Textures/make_ravenshoe_surfaces.py`; applied by `Tools/Unreal/setup_ravenshoe_surfaces.py` → `MI_SS_Raven_{Road,Iron,Deck,Stone}` | `DONE` | **Class F — original, generated from noise** (L-0011, ADR-029), on the same ground as the character camo sets (CH-TEX-001). Not sampled, traced or derived from any scanned or licensed texture. Two constraints are enforced in the generator rather than left to eye: every set is **periodic** (a tiling map with a baked-in low-frequency gradient repeats as stripes down a 68 m deck), and the granite has **bed joints as well as perpends** — perpends alone are not coursed masonry, they are vertical strips, and it rendered as flat grey slabs until the bed joints were added |
| M-008n | Bridge metric table and surface audit | `bridge_metrics()` / `check_bridge_metrics()` in `Tools/Common/ravenshoe_spec.py`; `audit_surfaces()` in `Tools/Unreal/audit_ravenshoe.py` | `DONE` | Class F — original. The metric table is the bridge's governing numbers as **ratios**, printed on every verify run. The surface audit asserts the overrides on the **saved** map, which is the only place a no-op write can be caught: the import re-spawns the bridge actor and strips them, so the surfaces pass must run last and the order is recorded in all three scripts |
| M-008k | Prop prep pipeline | `Tools/Blender/probe_fab_props.py` (measure), `Tools/Blender/prep_fab_props.py` (clean/scale/decimate/export), `Tools/Blender/render_fab_props.py` (judge), `Tools/Unreal/dress_ravenshoe_props.py` (import/material/place) | `DONE` | Class F — original tooling. Written because vendor FBX arrives in the author's own units, axis order and ground-plane state; the Renault wreck authors at 27.3 m and arrives with a ground plane. Re-running is idempotent — the pass purges and replaces only its own `Dress_Prop_` actors |
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

**Website promotion exception (producer decision, 2026-09-28):** the public website's Loadout section shows renders of the current internal weapon models — the ADFRC-derived A88, A4, A416, A25 and A9, the ADFRC F89 (`ADFRC_F89_Minimi_Mod_MLOD`) as the stand-in shown for the A89, and the sourced AKM as an external reference render explicitly labelled as not a game weapon. The A89 is shown as the ADFRC F89 rather than the exported in-build mesh because that mesh came from `ADFRC_F89_Minimi_MLOD`, which is assembled from Minimi parts plus Maximi (M249) and Mag58 parts and reads as an M249. This is a recorded producer risk acceptance (see LICENCE_REGISTER L-0017 and L-0021), not a licence clearance, and does not change the blocked status of any of these assets for release. The AKM and PKM remain reference-only (R-22/R-23): the AKM is published as a labelled reference render at the producer's direction; the PKM is not published.

**Soldier renders: built, published, then withdrawn (Session 042).** Studio renders of both
playable sides were made from `Docs/images/soldiers/*.png` (`Tools/Blender/render_soldiers.py`)
and briefly published, then withdrawn at the producer's direction. Unlike the weapon renders,
a soldier render is **two** restricted layers in one image — the L-0016 Fab mannequin the game's
rig is fitted to, plus L-0021 ADFRC-derived kit — and there is no single material whose
clearance carries the picture. On review the body's proportions read as a mannequin rather than
a soldier, which no amount of lighting or texture work fixes. Nothing from this session is
published; the renders are internal-only and the section's derivatives are listed in
`Tools/publish_site.py` under `RETIRED`. The camouflage worn in them is the project's own
L-0022 material and is retained for the game. **Do not re-publish player-model renders until
C-001/C-002 has an original body.**

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

### 4.9h Installed Fab packs registered 2026-09-28 (L-0016b)

Nine packs were found installed in `Content/` with no row in this register or in `LICENCE_REGISTER.md`.
Bookkeeping correction: **no asset was imported, modified, moved or deleted**, and no licence class changed.
All are Fab Standard License, **Class A** (L-0016).

| Pack | Path | Used by | Status |
|---|---|---|---|
| Scene Quarry Slate | `Content/Scene_QuarrySlate` | Dry River rock/gravel/road, tinted `MI_SS_Ironstone_*`; Ravenshoe Crossing (M-008d) gorge walls and boulders | `IN_USE` |
| Modular Rural Cabin | `Content/Modular_Rural_Cabin` | Ravenshoe shaded-slope conifers (M-008) | `IN_USE` |
| Singapore Canal | `Content/Singapore_Canal` | — | `NOT_USED` — Asian canal/urban (ADR-016); stone *materials* must not be repurposed for Australian masonry |
| Nanite Plants Sample Collection | `Content/Nanite_Plants_Sample_Collection` | — | `NOT_USED` — temperate European garden species |
| Military Radio | `Content/Military_Radio` | Radio and headset props | `IN_USE` |
| Realistic Starter VFX Pack Vol 2 | `Content/Realistic_Starter_VFX_Pack_Vol2` | Particle effects | `IN_USE` |
| Sample Animation Pack | `Content/SampleAnimationPack` | — | `NOT_USED` |
| World Flags | `Content/World_Flags` | — | `NOT_USED` |
| FP_AKS74U Animation | `Content/FP_AKS74U_Animation` | — | `NOT_USED` |

### 4.9i Fab prop downloads registered 2026-09-28 (L-0016c)

Thirteen further Fab listings were downloaded while scoping the Ravenshoe Crossing prop layer (M-008j).
**Seven were imported** after a Blender prep pass; **six were left in the download cache** and are recorded here so the sweep has a floor.
Bookkeeping rule applied (L-0016b): the register row is added **in the same change** that imports the asset.

| Listing | Folder in `Content/Downloaded/VaultCache/FabLibrary/` | Seller | `isAiForbidden` | Imported as | Status |
|---|---|---|---|---|---|
| Red car wreck | `Red_car_wreck-04d70886` | *(no metadata)* | **unverified** | `SS_Raven_wreck_car` | `IN_USE` — burning wreck on the bridge deck at OBJ A. 1.17 M tris in the source, prepped to 23 k |
| Abandoned & junk Car | `Abandoned___junk_Car-ee5cffe5` | PLEXUS GAME ASSETS | `false` | `SS_Raven_wreck_junk` | `IN_USE` — second wreck, creek bed |
| American Old Windmill | `American_Old_Windmill-d8d4a1d3` | Polyvine | **`true`** | `SS_Raven_windmill` | `IN_USE` — north ridge |
| Fuel barrel | `Fuel_barrel-873fee1d` | SampleDotTxt | **`true`** | `SS_Raven_fuel_drum` | `IN_USE` — deck spill and gatehouse cluster |
| Barn | `Barn-eb4457bc` | *(no metadata)* | **unverified** | `SS_Raven_barn` | `IN_USE` — north ridge |
| Military Trenches — Pile Sandbag Canvas 01 | `Military_Trenches_Pile_Sandbag_Canvas_01-a08111c9` | Quixel Megascans | **`true`** | `SS_Raven_sandbag_stack` | `IN_USE` — 8 stacks, both approaches |
| Military Trenches — Wall Metal Corrugated 04 | `Military_Trenches_Wall_Metal_Corrugated_04-e15620d3` | Quixel Megascans *(no metadata)* | **assumed `true`** | `SS_Raven_trench_wall` | `IN_USE` — 4 panels at the abutments |
| Old Abandoned Rusty Cars | `Old_Abandoned_Rusty_Cars___...-ed740921` | OlegVerenko | `false` | — | `NOT_USED` — 4 bodies, 75 MB; the single Renault covers the need at a third the size |
| Rigged Cargo Container Red PBR | `Rigged_Cargo_Container_Red_PBR-1db0b7e1` | Vadim3dd | **`true`** | — | `NOT_USED` |
| Old Rustic Hand Water Pump | `Old_Rustic_Hand_Water_Pump-0b2fc83d` | Sayan Paul | `false` | `SS_Raven_hand_pump` | `IN_USE` — 3 pumps at the road edge. Authors at 5.85 m tall, prepped to 1.6 m |
| Water Tower | `Water_Tower-86b17984` | Chamod1999 | `false` | `SS_Raven_water_tower` | `IN_USE` — 9 m tower set back at (14, 78) |
| Military Trenches — Debris Pile Rock | `Military_Trenches_Debris_Pile_Rock_S-11e2529f` | Quixel Megascans | **`true`** | — | `NOT_USED` — 19,751 tris for a 0.77 m flat piece |
| Red Tractor, Storage Unit nr5, Old Barn, Wooden Chicken Coop, Crushed Classic Raw Scan, Old Bath | as named | *(mixed)* | **mostly unverified** | `SS_Raven_old_barn` (Old Barn only) | Old Barn `IN_USE` — prepped and placed on the **south** ridge at (66, −104), so each deployment has a landmark. The rest `HELD` on two counts, both now recorded rather than vague: **the prep pipeline takes FBX and none of them ship it** (Storage Unit is OBJ only, Chicken Coop and Tractor are GLB only, Crushed Classic is an unextracted RAR), and they are European/Baltic in origin (the storage unit's own asset path is `Daugavpils_skuunis`) and need an ADR-016 look check for a high-country Australian gorge. Onboarding them means extending `prep_fab_props.py` to import OBJ and GLB as well |

> **AI-use flags.** Five imported or held listings carry `isAiForbidden: true`, and three more shipped no `metadata` at all so their flag is *unverified* rather than known-clear. The producer decided to proceed; the reasoning and the residual risk are in **LICENCE_REGISTER.md L-0016c**. An absent `metadata` file is recorded here as unverified, never as clear.
>
> **The VFX pack is reused, not re-registered.** The fire, smoke and ember systems placed on the wreck come from *Realistic Starter VFX Pack Vol 2*, already cleared in 4.9h. They are placed as instances of that pack's own `Spawn_Particle` Blueprint because 5.8's Python cannot persist a runtime-added `ParticleSystemComponent` — see M-008k.

**Standing rule.** A pack's register row is added **in the same change that imports it**, not afterwards.
The CI check covers `.uasset`/`.umap` appearing without a register entry; it does **not** catch a pack that
was already installed, which is how this gap survived.

### 4.9j Fab downloads registered 2026-09-29 — the MOUT urban training kit

Five listings were downloaded on 2026-09-29. One was **installed into `Content/`** and is the only new
environment map in the project; the other four are in the download cache only. Registered here in the same
change as the install, per the standing rule above. Bookkeeping: **no asset was imported into a map, modified,
moved or deleted**, and no licence class changed. All are Fab Standard License, **Class A** (L-0016).

| Listing | Folder | Seller | `isAiForbidden` | Installed as | Status |
|---|---|---|---|---|---|
| **MOUT urban training kit** (vendor abbreviation for Military Operation Urban Training) | `VaultCache/ModularM6dfea54fd98cV5/` | **unverified** — Vault pack wrote no `metadata` sidecar | **unverified** | `Content/MOUT_Civilian/` — 2.1 GB, 507 files, 3 maps | `IN_USE` — **Wandarra (M-009) since 2026-09-30**: 11 building Blueprints, ChurchKit assembly, FenceSetA, 13 prop sets placed by `build_wandarra_level.py`. First 5.8 load measured **silent** (no upconversion error lines) — R-67's texture/LOD/draw questions remain open. `Docs/MAPS_WANDARRA.md` |
| Old Abandoned Rusty Cars | `FabLibrary/Old_Abandoned_Rusty_Cars___...-ed740921` | OlegVerenko | `false` | `Content/RustyCarsFree/` — 69 MB | `IN_USE` — **Wandarra (M-009) since 2026-09-30**: 10 wrecks (`SM_asset_00–04`) as traffic-width cover, depot hulks and green-side parking. Row corrected 2026-09-29 to `NOT_USED`, corrected again 2026-09-30 on first map use |
| Mega Moduler Apartment Building | `FabLibrary/Mega_Moduler_Apartment_Building-db1b80f5` | karaman | **`true`** | — | `NOT_USED` — cache only |
| Modular 3D hospital environment | `FabLibrary/Modular_3D_hospital_environment-7e1574fd` | Madd Game Art | `false` | — | `NOT_USED` — cache only. Listed under *Environments / Horror*; needs an ADR-016 look check before any consideration |
| American Road with Parking Lot | `FabLibrary/American_Road_with_Parking_Lot-a629eb34` | Jimbogies | `false` | — | `NOT_USED` — cache only. GLB, not Unreal content; needs an FBX/GLB import path in the prep pipeline before it can be onboarded |
| Individual First Aid Medical Kit (IFAK) | `FabLibrary/Individual_First_Aid_Medical_Kit_IFAK-a628e3ba` | SpatialNeglect | **`true`** | — | `PLANNED` — the medic's kit (ADR-040). The flag is overruled for every asset (L-0016d) |

| European Beech trees | `VaultCache/MS_Beech_UE51_V2/` | **unverified** — Vault chunk carries a build manifest only, no `metadata` sidecar | **unverified** | `Content/EuropeanBeech/` — 7.0 GB, 258 files | `IN_USE` — **Wandarra (M-009) since 2026-09-30**: 38 `SimpleWind` static meshes as verge rows, park cluster and depot screen. Authored **UE 5.1 native** (no upconversion). Row added 2026-09-30 (`L-0016c` posture: unverified, never clear) |

> **AI-use flags.** Two of these packs carry `isAiForbidden: true` and neither is installed in a map. The MOUT
> kit's and the beech pack's flags are **unverified**, not clear: both arrived through the Vault route, which
> wrote no `metadata` sidecar anywhere in either pack. An absent sidecar is recorded as unverified, never as
> clear (L-0016c).
>
> **Why M-009 opened 2026-09-30.** The producer's "one big map" decision of 2026-09-29 supplied the three
> things the 2026-09-29 note lacked: an author (Session 082), an agreed name (Wandarra) and a layout
> (`Tools/Common/wandarra_spec.py`). The candidate became a map, so the id opened in the same change.

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

### 4.9k Animal and native flora models registered 2026-09-30 (L-0024) — easter-egg dressing

Two vendor model sets arrived in `Content/ghostgum/` and `Content/kangaroo/` on 2026-09-30 with no provenance
metadata. Registered here in the same change per the standing rule in §4.9i. Neither is a Fab listing — the
sources look like marketplace/archives downloads gathered manually — so provenance is **unverified** and both
carry the L-0016c posture: **unverified, never clear**, producer risk-accepted (ADR-035 posture). Neither has
been imported into the engine yet in this change except as noted in the Status column.

| ID | Asset | Path | Contents | Status | Licence dep. | Notes |
|---|---|---|---|---|---|---|
| ENV-003 | Ghost gum tree model + texture set | `Content/ghostgum/` | `source/TH_Complete_Full_Ghoast_Gum.fbx` (full tree), 8 TGA source textures (diffuse, normals, spec, branch alpha set), `textures/` PNG derivatives. 20 MB. `source/TH_Ghoast_Gum.zip.zip` is the original archive, kept for provenance | `VENDORED` — staged; UE import pending (queued: dressing pass for Dry River / Red Gum Station canopy variety alongside the RuralAustralia gums) | **L-0024** — provenance unverified (no licence text, no seller metadata); producer risk-accepted | "Ghoast" [sic] spelling is the vendor's. Australian ghost gum look fits ADR-016. Textures need power-of-two check and sRGB audit at import; the FBX axis/scale conventions must be measured before first placement (same intake discipline as M-008k) |
| ENV-004 | Kangaroo model + texture set | `Content/kangaroo/` | `source/source/kangaroo.FBX` (+ `.obj`/`.mtl` twins), 8 JPG + 1 TGA textures. 24 MB. `source/kangaroo.rar` is the original archive, kept for provenance | `VENDORED` — staged; **imported this change for the easter egg** (see below) | **L-0024** — provenance unverified; producer risk-accepted | Static prop — no rig, no animation in the source. Producer intent: 2–3 individuals as an easter egg under trees on Dry River (M-001) and Red Gum Station (M-RG-01) |

> **Provenance note (updated 2026-09-30, producer decision).** Both sources arrived without licence files or
> seller metadata. The producer has confirmed all models downloaded for or used in the project are **free and
> cleared for use in the game** — producer risk acceptance under the ADR-035 posture. R-90a is therefore
> **closed**; the register keeps the unverified-metadata observation for the credits record only.

**Easter-egg placement (this change):** kangaroos placed as static meshes under existing tree canopies —
2 on Red Gum Station, 2 on Dry River — by `Tools/Unreal/dress_kangaroo_easteregg.py`, labels
`SS_EasterEgg_Kangaroo_N`, terrain-anchored to the tree pivot, collision off (decoration only, never blocks
nav or shots).
