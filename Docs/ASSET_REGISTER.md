# ASSET REGISTER — Southern Spear

**Document ID:** `Docs/ASSET_REGISTER.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-10-01

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army. All units, insignia, operations and places referenced are fictional.

---

## 1. Purpose

Every asset the game requires, its source, current state, project-use clearance and dependencies. **No third-party asset enters the project without a matching `LICENCE_REGISTER.md` provenance row.**

> **Producer confirmation (2026-10-01; ADR-028 / ADR-035):** assets held or acquired for Southern Spear are free to use in this free-to-play game. Do not place a per-asset permission hold on Fab, Vault-cache, producer-supplied or other project assets. Preserve known seller/source/attribution metadata and mark missing metadata as unknown; that bookkeeping does not override the producer's project-specific clearance. This is not a claim that every marketplace listing carries a universally applicable licence, nor a reason to distribute raw vendor source files.

### Status vocabulary

| Status | Meaning |
|---|---|
| `PLACEHOLDER` | A stand-in exists or is planned. **Not final. Does not ship.** |
| `VENDORED` | Third-party asset or source copy present in the project and registered; source/use readiness is stated separately (producer clearance is recorded under ADR-035) |
| `IN_PRODUCTION` | Asset in active creation, integration or validation; source type is stated in its entry |
| `DONE` | Final and reviewed for its intended production use; clearance/provenance are recorded separately |
| `DEFERRED` | Not started; sequenced later |

---

## 2. Sourcing Rules (Mandatory)

Applied in this order, for every asset:

1. Check whether an existing project asset can be legally reused.
2. Search Fab from within Unreal Engine for a suitable asset; the producer's ADR-028/035 direction clears acquired assets for this game's free-to-play use.
3. Record asset, publisher, source, licence and modifications in `LICENCE_REGISTER.md`.
4. If no suitable asset exists, create an original placeholder.
5. Replace placeholders incrementally with original production assets or deliberate integrations/adaptations of producer-cleared acquired assets; state the source and validation status in each entry.
6. **Never** download assets from unverified model-ripping or redistribution sites.
7. Record seller flags, licence labels, source URLs and attribution when present; distinguish observed source metadata from the producer's project-use clearance.
8. Preserve credits/attribution where the listing or source requests it; credits are not a permission hold under ADR-035.
9. Use the producer's clearance for Southern Spear's free-to-play release (ADR-028/ADR-035, reaffirmed 2026-10-01); do not infer that it licenses redistribution of raw source packs outside the game.

> **Tooling note (PROJECT_AUDIT R-03):** the Fab plugin's in-editor availability is still subject to Launcher registration. The local VaultCache and FabLibrary are inventoried separately below; a tooling/access limitation is not an asset-clearance hold.

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

This is the intended layout, **not the current on-disk layout**: the project currently has Lyra content, third-party pack roots, original art and source-review material in several top-level `Content/` folders. The inventory below records those roots instead of claiming they are already consolidated under `Content/SouthernSpear/Vendor/`.

---

## 4. Foundation Asset Register

### 4.1 Lyra Starter Game 5.8

| Item | Status | Notes |
|---|---|---|
| Lyra source + plugins | `VENDORED` | Licence **L-0001**. Basis of the project |
| Manny/Quinn skeleton + base meshes | `VENDORED` | Licence **L-0001**. Skeleton shared across all our soldiers |
| Lyra locomotion animations | `VENDORED` | Licence **L-0001**. Starting point, will be extended |
| Lyra example materials | `VENDORED` | Licence **L-0001** |

Lyra content is a **technical foundation, not Southern Spear art.** Its retained visual content is not automatically a placeholder: replace it only where the shipping art plan requires, and do not treat this sentence as a blanket claim that every Lyra asset must be replaced before release. Confirm applicable Epic sample/EULA shipping terms under L-0001/L-0002.

### 4.2 Weapons — Friendly force

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| W-001 | A88 Standard Service Rifle (A-series name; current cosmetic mesh is EF88-derived) | `IN_PRODUCTION` | L-0017 (producer-cleared for Southern Spear F2P use; original-author terms remain unverified provenance) | The original script-built A88 remains source work; the current textured cosmetic mesh and imported texture/material assets are tracked under `/SSExp_ObjectiveAssault/Weapons/A88/`. Producer clearance permits this project use. The model is a sourced EF88-family derivative, not an original bullpup silhouette; ongoing design/finish review is optional art direction, not a permission hold (R-21). |
| W-002 | A89 Light Support Weapon (A-series name; first-pass original mesh) | `IN_PRODUCTION` | Class F — original mesh; real-world/source data tracked separately | First-pass original script-built A89 is in the game; 1.19 m, 2,012 tris. Bipod and third-person carry poses remain to be validated. |
| W-003 | A9 Service Pistol (A-series name; G19-derived source configuration) | `IN_PRODUCTION` | Producer-cleared acquired source (ADR-035); record source/provenance under L-0021 | A9 assets are tracked under `/SSExp_ObjectiveAssault/Weapons/A9/` and the pistol appears in current loadout configuration. Its mesh/material finish and runtime presentation still require the weapon audit; it is not a placeholder. |
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
| C-001 | Friendly soldier visible body | `IN_PRODUCTION` (Quantum modular sample + ADFRC gear) | L-0016 / L-0025 / L-0021 | Quantum shirt, jeans, arms and head use Quantum's skeleton; Manny remains the gameplay/pose source and ADFRC vest/helmet are separate leader-posed gear (ADR-042). Producer rejects the latest in-game class-select appearance; body choice is set, but assembly, silhouette, materials, pose and fit are **not visually accepted**. |
| C-002 | Female soldier body | `DEFERRED` | L-0001 (Lyra baseline only) | No female playable body is currently identified in the active Quantum-friendly configuration; Quinn remains Lyra/sample content, not the shipped Southern Spear body. |
| C-003 | Modular heads / alternate head variants | `PLACEHOLDER` | — | A Quantum head is included in current body assembly C-001; additional selectable head variants are not established. |
| C-004 | Hair compatible with military headgear | `PLACEHOLDER` | — | Must not clip under helmets |
| C-005 | Helmets | `VENDORED` (ADFRC-derived gear) | L-0021 | ADFRC helmet gear is retained in the active friendly appearance assembly; fit and final in-game visual acceptance remain open. |
| C-006 | Eye protection | `PLACEHOLDER` | — | |
| C-007 | Hearing protection | `PLACEHOLDER` | — | |
| C-008 | Plate carriers | `VENDORED` (ADFRC-derived gear) | L-0021 | ADFRC vest gear is retained in the active friendly appearance assembly; fit and final in-game visual acceptance remain open. |
| C-009 | Webbing | `PLACEHOLDER` | — | |
| C-010 | Packs | `PLACEHOLDER` | — | |
| C-011 | Gloves | `PLACEHOLDER` | — | |
| C-012 | Boots | `PLACEHOLDER` | — | |
| C-013 | Role-appropriate pouches | `PLACEHOLDER` | — | |
| C-014 | **Commonwealth Multi-Environment Combat Uniform (CMECU) material** | `DONE` | Class F — original texture set, CH-TEX-001 | The original fictional CMECU texture set is generated and registered; current Quantum-friendly camo routing instead uses CH-TEX-004. This art-direction choice does not prohibit acquired real-world camouflage (ADR-035). |
| C-015 | Murasian Armed Forces clothing set | `IN_PRODUCTION` | Producer-cleared acquired assets / L-0016; original assembly | Current opposing appearance draws on conventional Modern Insurgent parts; the label is not a design/provenance status. Keep MAF fictional and non-stereotyped; no final visual sign-off claimed. |
| C-016 | Fictional unit insignia (CDS/CLS/ACR) | `PLACEHOLDER` | — | Original fictional marks remain the planned CDS/CLS/ACR design. ADR-035 also permits producer-directed acquired ADF/Army insignia in this F2P project; keep the no-endorsement disclaimer and content-ethics rules. |
| C-017 | Fictional Murasian Armed Forces insignia | `PLACEHOLDER` | — | Original, invented, not drawn from any real armed group |
| C-018 | Rank slides / progression insignia on uniforms | `PLACEHOLDER` | — | No current uniform-mounted rank-slide implementation is identified. Rank marks are drawn for UI by `SSInsigniaRaster.h` (U-011); producer direction permits authentic Army insignia in this F2P project, with no permission-review gate. |

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
| A-010 | Foot IK / Hand IK targets | `IN_PRODUCTION` | Class F (bridge implementation) | Session 067 A/B evidence records a rendered pose change with hand IK on; Session 070 measured the A88 wrist at its grip target. Broader hand-contact/visual validation across weapons remains open; see R-65. |
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
| S-014 | ADFRC AUG/A88 weapon recording source set | `IN_PRODUCTION` | L-0021 / ADR-035 | 28 SoundWaves and 2 attenuation assets are imported under `/Game/AUG/Sound/` (`AUD-AUG-001`). The A88 family uses recorded weapon sounds; reload/closure cues and dry-fire integration remain open (see `WEAPONS_ANIMATION_PLAN.md` W4). |

> **Voice privacy:** voice chat is **never recorded**. No voice asset is captured without explicit per-player consent and a documented privacy design. See GDD §4.4.

### 4.7 Effects

| ID | Asset | Status | Licence dep. | Notes |
|---|---|---|---|---|
| E-001 | Muzzle flash | `PLACEHOLDER` | L-0001 (Lyra candidate only) | Code-driven muzzle light (`USSMuzzleLightSubsystem`, Session 060) is tested, but a visible, player-facing muzzle-flash effect is not yet confirmed in-game. Lyra's `NS_WeaponFire_MuzzleFlash_Rifle` is a candidate; placement and visual capture remain open (see NEXT_PRIORITIES §4). |
| E-002 | Tracers | `PLACEHOLDER` | — | |
| E-003 | Impact decals + debris | `PLACEHOLDER` | — | |
| E-004 | Dust / weather | `DEFERRED` | — | Layer-driven |
| E-005 | Spent cases | `IN_PRODUCTION` | L-0002 (engine BasicShapes cylinder; visual placeholder) | Code-driven casing eject uses a tinted engine cylinder per calibre (`USSShellEjectSubsystem`, Session 059); replace the proxy with a project-authored case mesh when the effect is polished. |
| E-006 | Suppression visual | `PLACEHOLDER` | — | |
| E-007 | Smoke grenade | `PLACEHOLDER` | — | |

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
| U-011 | Insignia (rank, qualification badges) | `IN_PRODUCTION` | Class F (code-drawn); L-0003 for producer-accepted insignia references | `SSInsigniaRaster.h` draws the rank marks; L-0003's old permission hold is superseded by ADR-035. Qualification badge art remains to be completed. |
| U-012 | Post-round summary | `PLACEHOLDER` | — | |

### 4.9 Maps and Layers

The table records current map/layer implementation state, not release readiness or producer sign-off. Several maps are built and dressed; playability, navigation, visuals and audit findings remain map-specific. See each map document and `MAPS_PLAYABILITY_AUDIT.md`. The original M-001–M-007 planning set is retained as the foundation count; later M-008 Ravenshoe and M-009 Wandarra additions are tracked explicitly and are not included in that original seven-item plan.

| ID | Map | Layers required | Status | Notes |
|---|---|---|---|---|
| M-001 | **Dry River** — rural training area, dry creek bed, scrub, farm structures, long sightlines, concealed approaches | Objective Assault (sequential A→B), Day | `IN_PRODUCTION` — dressed prototype; playability audit 3 pass / 6 fail | **The vertical slice test bed** and the design standard. Playable area expanded to 340 × 240 m and dressed from producer-cleared acquired packs (Session 044). `MAPS_PLAYABILITY_AUDIT.md` scores it 3 pass / 6 fail against its own rules. Original blockout authored in Blender; see `Docs/MAPS_DRYRIVER.md` |
| M-002 | **Red Gum Station** — 1 km outback station: open paddocks, gum-tree lines, fences, homestead | Objective Assault, Day | `IN_PRODUCTION` — built; measured not ready | First playable map (ADR-022). Objectives re-laid and deployments pulled in for fairness; no capture yet. `MAPS_PLAYABILITY_AUDIT.md` measures it at 17% nav coverage, 12 hard and 0 soft cover, and calls it not playable as it stands. `Docs/MAPS_REDGUM.md` |
| M-003 | **Selat Canal** — urban canal district: walkable canal core, buildings and interiors | Objective Assault (three objectives), Day | `IN_PRODUCTION` — built; playability audit 5 pass / 5 fail | The only Special Forces map. Best close-quarters geometry measured in the project (2 m open crossings) and the worst objective placement: all three objectives 42–75% walk-imbalanced. `MAPS_PLAYABILITY_AUDIT.md` scores 5 pass / 5 fail. `Docs/MAPS_SELATCANAL.md` |
| M-004 | **Saltbush** — open semi-arid range, built to test engagement ranges past 200 m | Objective Assault, Secure and Hold, Day, Low-light | `IN_PRODUCTION` — built; playability audit 7 pass / 3 fail | Deployment and objective layout rebuilt for fairness; has produced a capture in a bot match. Measured at 7 pass / 3 fail by `MAPS_PLAYABILITY_AUDIT.md` — the strongest of the four audited maps. `Docs/MAPS_SALTBUSH.md` |
| M-005 | **Bluestone** — flooded slate pit converted from a studio diorama: loading bay, cutting face, spoil heaps | Objective Assault, Day | `IN_PRODUCTION` — built; on the operations menu; not audited | Built 2026-09-28 from the slate-pit diorama by `Tools/Unreal/build_objective_map.py` (`quarry`); showroom and light bars stripped, open daylight, complex collision, boundary rim and three objectives, all legs connecting. Paused for fine-tuning; no design document yet, and not yet audited |
| M-006 | Training range | Training | `PLACEHOLDER` | Vertical slice. The MOUT kit (4.9j) is a *close-quarters village*, not an open firing range, and as of 2026-09-30 it is committed to **Wandarra (M-009)** as the urban half of training; what fills this entry — an open range on Saltbush's pattern or a redefinition — is still the producer's call. See `MAPS_TRAININGRANGE.md`, `MAPS_WANDARRA.md` |
| M-007 | Front end | — | `VENDORED` (Lyra) | L-0001 |
| M-008 | **Ravenshoe Crossing** — high-country gorge crossed by a wrought-iron lattice-girder road bridge; stone road-gate house on the far abutment; playable creek bed beneath giving a second lane | Objective Assault (sequential A→B), Day | `IN_PRODUCTION` — **in Unreal; 665 actors and 35/35 asset-audit checks; nav not baked** | `/Game/Maps/L_Ravenshoe_01`; `Docs/MAPS_RAVENSHOE.md`, ADR-027. Original layout and structures, dressed with producer-cleared acquired pack assets referenced in place; playability is not established by the asset audit. |
| M-009 | **Wandarra** — invented urban training village: two crossing streets, lookalike bungalows and two-storey houses, a fenced depot compound, civic block, park and green, church terminating the cross street | Objective Assault (sequential A→B→C), Day | `IN_PRODUCTION` — **built and dressed; saved nav coverage is 0 pending attended R-82 bake** | `/Game/Maps/L_Wandarra_01`; `Docs/MAPS_WANDARRA.md`. Built by the Dry River pipeline pattern using producer-cleared MOUT assets (4.9j), RustyCars and EuropeanBeech; current outstanding work includes nav, attended look/fit review (R-89/R-90), and spawn layout. |

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
| M-RG-01 | Red Gum Station map | `/Game/Maps/L_RedGum_01`; source `Tools/Unreal/build_redgum_level.py`, `build_redgum_nav.py` | `IN_PRODUCTION` | Producer-cleared acquired pack base (L-0016, ADR-022) plus original wiring |
| M-RG-01a | Homestead compound — farmhouse, shearing shed, stock pens, water tank, windmill, two stockman's huts | `Content/Art/Environment/RedGum/SS_RedGum_Homestead.blend` (source, LFS) + `SS_RedGum_*.fbx` → `/Game/Art/Environment/RedGum/*` with 5 authored materials; source `Tools/Blender/redgum_homestead.py`, importer `Tools/Unreal/import_redgum_homestead.py` | `IN_PRODUCTION` | **Class F — original, no third-party dependency.** Modelled from scratch because the Rural Australia pack has no building mesh and the other installed packs are the wrong continent or culture (ADR-013, ADR-021, L-0011). 7 structures, ~2,350 tris, LFS-tracked. Placement anchored to objective B by label, not coordinates |
| M-RG-01b | Rural dressing and play-space expansion | `Tools/Unreal/expand_redgum.py`; 1,140 actors in `L_RedGum_01` | `IN_PRODUCTION` | Producer-cleared pack meshes (L-0016) referenced in place, never modified; layout original. Seeded and idempotent, owned by the `SS_RedGum_Dress_v1_` prefix |
| M-008a | Ravenshoe Crossing blockout | `Tools/Common/ravenshoe_spec.py` + `Tools/Blender/ravenshoe_blockout.py` → `Content/Art/Blockout/SS_MAP_Ravenshoe_01_HI.blend` (LFS), `SS_MAP_Ravenshoe_01.fbx`, `SS_MAP_Ravenshoe_01_Layout.csv` | `DONE` — terrain 200 × 300 m, 15,000 faces, relief −18..+28 m; 72 layout rows | Class F — original (ADR-027, L-0011). Shared-spec-with-CI pattern per `dryriver_blockout.py` / `dryriver_spec.py`; every dimension read from the spec so generator and verifier cannot disagree |
| M-008b | Iron lattice-girder road bridge — trusses, uprights, deck, parapets, abutments, 10 lamp standards | `Content/Art/Blockout/SS_Raven_Bridge.fbx`; 68 m span, 20 bays of 3.4 m, 21 uprights/side, 7.5 m deck, 1266 faces | `DONE` — authored with **deck top at z=0**, placed by deck level; four material slots (Iron / Deck / **Road** / Stone) | **Class F — original, no third-party dependency.** This authored bridge follows ADR-027's original-map decision. The 2026-10-01 inventory found `AutomotiveBridgeScene` locally installed, but no reference/dependency in Ravenshoe was established; the older keyword sweep is not proof that no bridge-like content exists anywhere. The `Road` slot is the running surface, split off the deck slab by polygon so the slab's fascia and soffit can be painted steel while the top is road. |
| M-008c | Stone road-gate house — granite rubble, 9.6 × 6.8 × 6.0 m, 4.6 m eaves, 1.2 m parapet, 3.4 × 3.6 m arched road passage, 17-stone segmental arch | `Content/Art/Blockout/SS_Raven_Gatehouse.fbx`; 450 faces | `DONE` — authored at its real position (0, 62) and rebased to its own footprint centre, base at 0 | **Class F — original.** The original gatehouse geometry is project-authored; the 2026-10-01 root inventory includes other installed building/environment content (including MOUT and AutomotiveBridgeScene). No such pack is asserted as the gatehouse source. Verified by ray cast: passage clear end to end, spandrel solid above the crown, piers solid. |
| M-008d | Gorge heightfield, road corridor, both traverse ramps | in `SS_MAP_Ravenshoe_01.fbx` | `DONE` — ramps 133 m @ 17.6° east, 142 m @ 16.2° west, no pitch above the design grade | Class F terrain shell, dressed with producer-cleared `Scene_QuarrySlate` rock referenced in place (L-0016b) |
| M-008e | Ravenshoe layout and geometry verifier | `Tools/Blender/verify_ravenshoe.py` | `DONE` — **53/53 pass**; spec mode runs in CI with no Blender | Class F — original. Fails the build if S→OBJ A and N→OBJ A differ by more than 0.5 m, if any intent route has an uncovered run over 20 m, or if a ramp pitch exceeds the design grade. Also prints the bridge metric table every run and range-checks the **ratios** (span:truss depth inside 1:12–1:20, clear lane ≥ 6 m, headroom ≥ 4 m, bay 2.5–4.0 m), which can all be wrong while every dimension still reads as the value typed into the constant |
| M-008f | Blockout preview renders | `Build/ravenshoe/raven_*.png`; generator `Tools/Blender/ravenshoe_render.py` | `DONE` — 6 Workbench views | Class F — original. Shape check, not look-dev |
| M-008g | Imported mesh assets | `/Game/Art/Environment/Ravenshoe/Meshes/SS_MAP_Ravenshoe_01`, `SS_Raven_Bridge`, `SS_Raven_Gatehouse` | `IN_PRODUCTION` | Class F — original, imported by `Tools/Unreal/import_ravenshoe.py` with generated simple collision and `CTF_USE_DEFAULT` |
| M-008h | Authored flat safety-net materials | `/Game/Art/Environment/Ravenshoe/Materials/MI_SS_RavenFlat_{Iron,Stone,Deck,Road,Terrain}` | `DONE` — superseded by M-008m on the bridge, deck and masonry; still the terrain's material | Class F — original. **Was `M_SS_Raven_{Iron,Stone,Deck,Terrain}` and never worked**: it called `MaterialEditingLibrary.get_material_property`, which does not exist in 5.8, so the call raised, was swallowed as a warning, and the materials were created with engine defaults. They are now instances of `M_SS_ScanPBR` carrying a `Tint`, so a flat colour is a parameter rather than an expression-graph edit |
| M-008l | Prop material instances | `/Game/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_{Wreck,WreckJunk,FuelDrum,Metal,Timber,Canvas}` | `DONE` | Class F — authored, **not copies of the vendor material**. All six are instances of the project's own parameterised `M_SS_ScanPBR` (`Tint`, `Tiling`, and `BaseColor`/`Normal`/`Roughness`/`AO`/`Metalness` slots), so pack textures from several sources feed one shader instead of one shader per prop. Parameter values were read back off the working `MI_SS_CorrugatedIron` rather than guessed — individual source textures vary by listing; review M-008j/L-0016c for source-level detail. |
| M-008i | Gorge and approach dressing — 424 actors | `L_Ravenshoe_01`, labelled `SS_Raven_Cover_*` / `SS_Raven_Dress_*` | `IN_PRODUCTION` | Producer-cleared pack meshes (ADR-028/035) referenced in place: `Scene_QuarrySlate` ledge/rock clusters and `RuralAustralia` trees, logs, fence. Trees and wire are collision-off (ADR-022) — Lyra has no vault and a colliding wire fence splits the navmesh. |
| M-008j | **Producer-cleared acquired prop layer** — burning car wreck on the bridge deck at OBJ A, second wreck in the creek bed, fuel drums, sandbag and corrugated-panel cover on both approaches, water tower and hand pumps on the road edge, windmill and barn on the north ridge, old barn on the south ridge, plus fire / smoke / ember effects | `/Game/Art/Environment/Ravenshoe/Props/*` and `…/Materials/MI_SS_Raven_*`; built by `Tools/Blender/prep_fab_props.py` → `Tools/Unreal/dress_ravenshoe_props.py`; verified by `Tools/Unreal/audit_ravenshoe.py` | `DONE` — **35 actors placed, 35/35 audit checks** | **Producer-cleared for Southern Spear F2P use** (ADR-028/035); original meshes were mechanically prepped and referenced in place. Listing `isAiForbidden` values and missing metadata are recorded in L-0016c/§4.9m as provenance only, not project-use holds. |
| M-008m | **Generated surface textures** — sealed gravel road, rusted ironwork, painted steel, coursed granite rubble | `Art/Environment/Ravenshoe/Surfaces/T_SS_Raven_{Gravel,RustIron,PaintedSteel,Granite}_{BC,N,R,AO,M}.png` (20 × 1024²); generator `Tools/Textures/make_ravenshoe_surfaces.py`; applied by `Tools/Unreal/setup_ravenshoe_surfaces.py` → `MI_SS_Raven_{Road,Iron,Deck,Stone}` | `DONE` | **Class F — original, generated from noise** (L-0011, ADR-029), on the same ground as the character camo sets (CH-TEX-001). Not sampled, traced or derived from any scanned or licensed texture. Two constraints are enforced in the generator rather than left to eye: every set is **periodic** (a tiling map with a baked-in low-frequency gradient repeats as stripes down a 68 m deck), and the granite has **bed joints as well as perpends** — perpends alone are not coursed masonry, they are vertical strips, and it rendered as flat grey slabs until the bed joints were added |
| M-008n | Bridge metric table and surface audit | `bridge_metrics()` / `check_bridge_metrics()` in `Tools/Common/ravenshoe_spec.py`; `audit_surfaces()` in `Tools/Unreal/audit_ravenshoe.py` | `DONE` | Class F — original. The metric table is the bridge's governing numbers as **ratios**, printed on every verify run. The surface audit asserts the overrides on the **saved** map, which is the only place a no-op write can be caught: the import re-spawns the bridge actor and strips them, so the surfaces pass must run last and the order is recorded in all three scripts |
| M-008k | Prop prep pipeline | `Tools/Blender/probe_fab_props.py` (measure), `Tools/Blender/prep_fab_props.py` (clean/scale/decimate/export), `Tools/Blender/render_fab_props.py` (judge), `Tools/Unreal/dress_ravenshoe_props.py` (import/material/place) | `DONE` | Class F — original tooling. Written because vendor FBX arrives in the author's own units, axis order and ground-plane state; the Renault wreck authors at 27.3 m and arrives with a ground plane. Re-running is idempotent — the pass purges and replaces only its own `Dress_Prop_` actors |
| C-SOL-01 | Soldier body parts (Quantum friendly / MAF opposing) | `/SSExp_ObjectiveAssault/Characters/B_SS_Soldier`, `B_SS_CharacterParts`; Quantum prototype parts under the Game Feature; sources `setup_soldiers.py`, `setup_quantum_proto.py` | `IN_PRODUCTION` | Producer-cleared vendor meshes (L-0016/L-0025) in original part actors; visible friendly-body choice ADR-042 |
| W-A89-01 | A89 light support weapon, first pass | `/SSExp_ObjectiveAssault/Weapons/A89/*`; source `Tools/Blender/a89_support.py` | `IN_PRODUCTION` | Class F — original (ADR-020); 2,012 tris, 119 cm |
| W-A88-01 | Original A88 first-pass source mesh | `Art/Weapons/A88/SM_A88.fbx`; source `Tools/Blender/a88_rifle.py` and `Art/Weapons/A88/A88.blend` | `IN_PRODUCTION` — original source retained | Class F — 2,632 tris, 89 cm. This original first pass is retained as source; the current imported game mesh is the separate provisional W-A88-02. |
| W-A88-02 | Textured producer-supplied A88 derivative and game import | Source `Art/Weapons/A88/New/` → `/SSExp_ObjectiveAssault/Weapons/A88/SM_A88` and `T_A88_*` | `IN_PRODUCTION` — appearance/re-design work open | L-0017; producer-cleared for Southern Spear F2P use (ADR-035, reaffirmed 2026-10-01). Pipeline report records 78.8 cm and 72,493 tris; imported texture/material assets are tracked. Source URL is recorded while original-author terms remain unverified provenance. A-series silhouette work is art direction, not a project-use blocker. |
| M-001g | Objective Assault experience | `/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault` | `IN_PRODUCTION` | Class F — original data; uses ShooterCore pawn data and action sets (Lyra, EULA) by reference |
| M-001e | Layout verifier | `Tools/Blender/verify_dryriver.py` | `DONE` | Class F — original |

**Generated 2026-09-26.** 162 objects, 8,944 faces. 4 gameplay markers. Verified against the design spec by `verify_dryriver.py`, which runs in CI.

Rows marked Class F were created specifically for this project and have no third-party asset dependency. Producer-cleared acquired/derived assets elsewhere in this expanded register are separately identified in their entries; F2P clearance does not change the classification of original work.

### 4.9b Licensed environment source meshes — staged for review/import

| ID | Asset | Path | Status | Licence dep. | Notes |
|---|---|---|---|---|---|
| ENV-001 | Split Point, Victoria photogrammetry source | `Content/SouthernSpear/Vendor/SAVollgger/SplitPointVictoria/` (OBJ, MTL, JPEG) | `VENDORED` — source staged; UE import not yet verified | L-0013 (CC BY 4.0) | 174,076 vertices / 346,200 triangles; dense scan, not optimized. Original source filenames retained; attribution in folder README. |
| ENV-002 | Bingie Bingie, NSW photogrammetry source | `Content/SouthernSpear/Vendor/SAVollgger/BingieBingieNSW/` (OBJ, MTL, JPEG) | `VENDORED` — source staged; UE import not yet verified | L-0014 (CC BY 4.0) | 273,042 vertices / 540,708 triangles; dense scan, not optimized. Original source filenames retained; attribution in folder README. |

These are raw source files, not imported/optimized shipping meshes; their presence does not establish game use. They may be used as source/reference or adapted under the producer's F2P project-use clearance. Keep map layouts original, record any imported/adapted derivative as a separate project asset, and preserve applicable attribution; raw-source redistribution remains disallowed.

### 4.9c Licensed third-party attribution

Ship the following attribution when the corresponding scans are included in a build:

- **Split Point, Victoria (Australia)** — Stefan A Vollgger, CC BY 4.0, https://sketchfab.com/3d-models/split-point-victoria-australia-d95f3ad4d0044c20a56ebb7bd507d515
- **Bingie Bingie, NSW (Australia)** — Stefan A Vollgger, CC BY 4.0, https://sketchfab.com/3d-models/bingie-bingie-nsw-australia-b3cdf8650ee44dd786f205c6c849ad59

Changes: source files staged unchanged; no modifications to mesh or texture data. License: https://creativecommons.org/licenses/by/4.0/.

### 4.9d Weapon source review — project use cleared; provenance and game-use scope tracked separately

| Source folder | Current file | Finding | Allowed next step |
|---|---|---|---|
| `Art/Weapons/A88/New/` | OBJ, MTL, 3DS, three PNGs, derived FBX | **Producer-cleared for Southern Spear F2P use (ADR-035).** Existing notes report the MTL references filenames absent from the folder; the 72k-triangle mesh has a real-rifle-like appearance. Exact original-author terms remain unverified provenance; the derivative does not establish those terms. | Keep raw source handling per project policy; record source/credit details and continue the fictional A-series silhouette/visual-quality work. R-21 is not a project-use permission hold. |
| `Art/Weapons/AKM/Weathered AKM rifle.blend` | Blender source | **Producer-cleared for Southern Spear F2P project use (ADR-035); not identified as an in-game asset.** Filename identifies a real AKM design; URL/author/terms remain unrecorded. | Keep its use/disposition distinct from the fictional A-series game weapons; record provenance and credits if incorporated. No source redistribution. |
| `Art/Weapons/PKM/PKM.blend` | Blender source | **Producer-cleared for Southern Spear F2P project use (ADR-035); not identified as an in-game asset.** Filename identifies a real PKM design; URL/author/terms remain unrecorded provenance. | Keep its use/disposition distinct from the fictional A-series; record provenance and credits if incorporated. Do not redistribute raw source. |
| `Art/Weapons/C4A1/kkanamalla_m4_carbine.blend` | Blender source; adjacent `textures(1)/` is empty in this checkout | **Producer-cleared for Southern Spear F2P project use (ADR-035); not identified as an in-game asset.** Session 021 records an embedded "Licensed CC-BY" label and author identifier `kkanamalla`; exact source page/version/terms remain unverified provenance. It depicts a real M4. | Preserve attribution if used; keep distinct from the fictional in-game A-series and do not redistribute raw source. |

**Intake rule:** files under `Art/Weapons/` are local source/review material, not automatically game-used assets. Record source, attribution and intended use in `LICENCE_REGISTER.md`; producer clearance covers use in Southern Spear's free-to-play game, not raw-source redistribution. The A88 import is already referenced by the experience and is cleared for project use; its source documentation and fictional-design quality tasks remain tracked under R-21, not as release permission holds.

**Website promotion note (producer decision, 2026-09-28; read with ADR-035):** the public website's Loadout section shows renders of internal weapon models — ADFRC-derived A88, A4, A416, A25 and A9, the ADFRC F89 (`ADFRC_F89_Minimi_Mod_MLOD`) as the stand-in shown for A89, and a sourced AKM reference render labelled as not a game weapon. The A89 is shown as the ADFRC F89 rather than the in-build mesh because that mesh came from `ADFRC_F89_Minimi_MLOD`, assembled from Minimi, Maximi (M249) and Mag58 parts, and reads as an M249. Producer F2P clearance applies to project use; the website note does not authorize redistribution of source files. The AKM and PKM remain reference-only (R-22/R-23): the AKM is published as a labelled reference render at the producer's direction; the PKM is not published.

**Soldier renders: built, published, then withdrawn (Session 042).** Studio renders of both playable sides were briefly published, then withdrawn at the producer's direction. This is a historical publication record: ADR-035 subsequently cleared project use of acquired assets for the F2P game, and ADR-042 selected Quantum as the friendly visual body. Do not infer current appearance or release status from those old renders. A fresh in-game capture of the active Quantum outfit remains pending; retain the no-endorsement, attribution and raw-source handling rules.

### 4.9e ADFRC raw extraction — segregated source tree; selected project assets tracked separately

`Content/Sourced/ADF_Extracted/` is a separate ADF Re-Cut (ADFRC) source/review collection, tracked under L-0021 / R-24 and quarantined per R-25. The producer has cleared acquired ADFRC assets for Southern Spear's free-to-play game under ADR-035; do not confuse that project-use clearance with permission to redistribute raw source or with approval of every file as an imported/referenced game asset. The `Models/ADF_Weapons/adfrc_ef88/` and `adfrc_m4a5/` `.p3d` files are real EF88 and M4A5-family content, distinct from the independent sources in `Art/Weapons/A88/New/` (L-0017 / R-21) and `Art/Weapons/C4A1/` (R-22). Any import/adaptation must be a deliberate art/use decision and registered; preserve source handling and credits. See `Docs/SOURCED_ASSET_REVIEW.md` for the collection inventory and source distinctions.

### 4.9f Character appearance textures — project originals and current Quantum camo

| ID | Asset | Path | Status | Licence dep. | Notes |
|---|---|---|---|---|---|
| CH-TEX-001 | CMECU camouflage set (3 ACR) | `Art/Characters/Textures/T_SS_CMECU_Camo_{BC,N,ORM}.png` (2048²) | `DONE` | Class F — original, script-built | Generated by `Tools/Textures/make_character_textures.py` from multi-octave value noise. Sun-bleached dry-country palette: khaki, pale dust, eucalypt grey-green, ironbark red-brown. **Original pattern** — not AMCU, not commercial MultiCam, not derived from ADFRC/Auscam material (ADR-016, L-0021). |
| CH-TEX-002 | MAF camouflage set (opposing force) | `Art/Characters/Textures/T_SS_MAF_Camo_{BC,N,ORM}.png` (2048²) | `DONE` | Class F — original | Red-earth disruptive per ADR-016/C-015: ochre, rust, dark brown, muted burgundy, charcoal. |
| CH-TEX-003 | Gear fabric sets (tan, dark) | `Art/Characters/Textures/T_SS_Gear{,_Dark}_{BC,N,ORM}.png` (1024²) | `DONE` | Class F — original | Near-solid dyed nylon with fine grain and a twill micro-normal. |
| CH-TEX-004 | ADFRC DPCU-derived tileable camo | Source `Art/ADFRC/Textures/adfrc_uniforms/data/Crye_G3_Shirt_DPC_co.png`; generated output `Art/Characters/ADF/T_ADFRC_DPC_camo.png` (`/Game/Art/Characters/ADF/T_ADFRC_DPC_camo`) by `Tools/Textures/make_adfrc_camo.py` | `IN_PRODUCTION` — routed to Quantum friendly shirt/jeans through `FriendlyMaterialOverrides`; visual capture pending | Producer-cleared source + project-generated derivative (ADR-035; producer reaffirmed 2026-10-01) | The script measures the source palette and generates a 2048² tileable texture; this output, not `T_SS_ADF_G3_Shirt_co.png` (a rejected historical G3 attempt), is loaded by `setup_quantum_proto.py`. Source and derivative remain distinct. |
| CH-TEX-005 | ADFRC G3 shirt sheet with its flat under-shirt panel repainted | Sources `Art/ADFRC/Textures/adfrc_uniforms/data/Crye_G3_Shirt_AMC_co.png` + `Crye_G3_Pants_AMC_co.png`; output `Art/Characters/ADF/T_ADFRC_G3_Shirt_AmcuCamo.png` (4096²) by `Tools/Textures/patch_adfrc_undershirt.py` → `/SSExp_ObjectiveAssault/Characters/ADF/Textures/T_ADF_G3_Shirt_AmcuCamo` | `IN_PRODUCTION` — visible in the 2026-10-01 class-select capture, producer acceptance pending (R-92) | Producer-cleared source + project-generated derivative (ADR-035) | Measured need: the fitted uniform's torso faces sample UV v 0.02–0.24, which is the sheet's plain khaki under-shirt (no camouflage), so the soldier rendered with a pale band at the waist. The script replaces the sheet's low-variance, non-background tiles with the trouser sheet's camouflage, mirrored across the sheet. Source and derivative remain distinct; re-running `setup_adf_soldier.py` without the patch reverts it. |
| CH-MAT-001 | Original fabric materials | `/SSExp_ObjectiveAssault/Characters/Materials/M_SS_{CMECU,MAF,GearTan,GearDark}` | `IN_PRODUCTION` | Class F — original | Authored by `Tools/Unreal/setup_character_textures.py`: TextureCoordinate → tiled UV0 into BC / normal / ORM, wired to BaseColor, Normal, and AO/Roughness/Metallic. |
| CH-MAT-002 | Quantum DPC camo master and garment instances | `/SSExp_ObjectiveAssault/Characters/QuantumProto/M_SS_ADFRC_Camo`, `MI_SS_ADFRC_Camo_{Shirt,Jeans}` | `IN_PRODUCTION` — material graph enhancement pending Unreal rebuild/render | Producer-cleared camo derivative + project-generated fabric N/ORM | `setup_quantum_proto.py` composes tileable camo color with generated cloth normal and ORM; component overrides route the shirt/jeans instances. Visual tiling, shader compile and surface response are not yet reviewed in a current capture. |
| CH-SOL-001 | Soldier appearance assemblies (ADFRC friendly + MAF opposing) | `/SSExp_ObjectiveAssault/Characters/B_SS_Soldier`; ADFRC gear under `Plugins/GameFeatures/SSExp_ObjectiveAssault/Content/Characters/ADF/`, Quantum head module under `.../QuantumProto/` | `IN_PRODUCTION` | Producer-cleared vendor meshes (L-0016/L-0025); original component material overrides | **Friendly (2026-10-01 evening):** ADFRC `SK_ADF_Uniform_G3` + `SK_ADF_Vest_TBAS` + `SK_ADF_Helmet_OpsCore`, Manny-rigged and leader-posed, with the Quantum head as the only retargeted module; the assembly and its textures were captured in the class-select preview this session. Producer direction was the ADFRC models and AMCU textures; ADR-042's body-source decision stands but its four-Quantum-module assembly is superseded. Fit, silhouette, camo finish and head choice remain open, as does producer acceptance. MAF is a separate opposing configuration. |

> **R-20 partial:** the `M_Patches` slot is now overridden with plain gear fabric, so any insignia carried by the vendor patch texture is no longer displayed. A rendered confirmation is still outstanding (see Session 026).

### 4.9g ADFRC-derived game assets (L-0021, ADR-025)

Cleared for use in the project; the source files stay git-ignored (`Art/ADFRC/`); the repository holds LFS pointers only (R-14).
Third-party marks/ADF camouflage remain provenance and art-direction details; ADR-035 accepts their use in the free-to-play project and no substitution permission gate remains. Retain the no-endorsement disclaimer and source/credit records.

| ID | Asset | Path | Status | Licence dep. | Notes |
|---|---|---|---|---|---|
| AUD-AUG-001 | AUG weapon audio (28 SoundWaves, 2 attenuations) | `/Game/AUG/Sound/` | `IN_PRODUCTION` | L-0021 | Imported by `Tools/Unreal/import_aug_audio.py` (Session 032b). |
| CH-ADF-001 | ADF and MAF gear skeletal meshes on Lyra's skeleton | `/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_*`, `SK_MAF_*`, `MI_ADF_*` | `IN_PRODUCTION` | L-0021; skeleton L-0016 (Epic) | `Tools/Blender/adfrc_gear_rig.py` + `Tools/Unreal/setup_adf_soldier.py` (Sessions 031, S1). |
| GP-DMG-001 | Hit-zone physical materials, per-weapon instances | `/SSExp_ObjectiveAssault/Characters/Physics/PM_SS_*`, `Weapons/*/B_SS_WeaponInstance_*` | `IN_PRODUCTION` | Class F (data); instances copied from Lyra (Epic) | `Tools/Unreal/setup_damage_model.py` (Session 034). |

### 4.9h Installed Fab packs registered 2026-09-28 (L-0016b)

This is the historical 2026-09-28 inventory of nine previously undocumented installed packs; later edits corrected use states and added the wider 2026-10-01 Content/VaultCache inventory below. **No source-level Fab licence audit is claimed here.** The producer clears assets acquired/held for this project for its F2P game under ADR-028/035; metadata, listing terms and any class labels remain provenance observations, not project-use holds.

> **This table is checked, not remembered.** `Tools/verify_packs.py` cross-references it against committed map dependencies. Singapore Canal, World Flags, FP_AKS74U Animation and StoneWell status corrections are recorded; run the verifier for the current result. The 14-pack map dependency scope and verifier are documented in `Docs/PACK_MANIFEST.md`; this is not a count of all Content roots, Vault entries or engine assets.

| Pack | Path | Used by | Status |
|---|---|---|---|
| Scene Quarry Slate | `Content/Scene_QuarrySlate` | Dry River rock/gravel/road, tinted `MI_SS_Ironstone_*`; Ravenshoe Crossing (M-008d) gorge walls and boulders | `IN_USE` |
| Modular Rural Cabin | `Content/Modular_Rural_Cabin` | Ravenshoe shaded-slope conifers (M-008) | `IN_USE` |
| Singapore Canal | `Content/Singapore_Canal` | **Dry River `SS_DR_LeanTo`, `SS_DR_Shed`, `SS_DR_Tank`; Red Gum farmhouse, huts, shearing shed and stock pens — 11 committed assets reference this pack, per `Tools/verify_packs.py`** | `IN_USE` — the observed dependency is generic corrugated/wood material and prop references; no canal layout or Asian masonry is used for Australian structures. Pack use is producer-cleared for F2P (ADR-028/035). Keep the art-direction distinction explicit. |
| Nanite Plants Sample Collection | `Content/Nanite_Plants_Sample_Collection` | — | `NOT_USED` — installed, not selected for current map use; producer-cleared if acquired assets are later selected |
| Military Radio | `Content/Military_Radio` | Radio and headset props | `IN_USE` |
| Realistic Starter VFX Pack Vol 2 | `Content/Realistic_Starter_VFX_Pack_Vol2` | Particle effects | `IN_USE` |
| Sample Animation Pack | `Content/SampleAnimationPack` | — | `NOT_USED` |
| World Flags | `Content/World_Flags` | `MI_SS_Flag_Friendly`, `MI_SS_Flag_MAF` (SSExp_ObjectiveAssault) | `IN_USE` — **corrected 2026-09-30**: the row said `NOT_USED` while two committed material instances parented off this pack. Found by `verify_packs.py`, not by reading |
| FP_AKS74U Animation | `Content/FP_AKS74U_Animation` | `MI_AKS74U`, `MI_Magazine` on `SM_MAF_R1` / `SM_MAF_S1` | `IN_USE` — **corrected 2026-09-30**, same as World Flags: the opposing weapon meshes take their materials from this pack |
| Stone Well | `Content/StoneWell` | Dry River farm dressing (`L_DryRiver_01.umap`; one referenced package) | `IN_USE` — 1.2 GB / 42 files. The installed Vault chunk is `Stonewel0323ec5dede0V1`; local listing title is `Stone well`, seller/listing URL are not recorded here. Producer confirms project use in the free-to-play game (ADR-035, reaffirmed 2026-10-01); identity metadata remains an inventory/restore detail, not a clearance hold. |
| WaterPlane (ocean/lake) | `Content/WaterPlane` | **Dry River creek water** (M-001): tracked `Lake/Textures/T_MediumWaves_N.uasset` feeds `M_SS_CreekWater` (ENV-005) | `PARTIAL_IN_USE` — 34 local files / 145,799,364 bytes (~139.1 MiB); one known texture dependency is tracked, while 33 other files were untracked in the shared working tree. Those files include lake/ocean/translucent examples and are not asserted as map dependencies. Source/listing metadata is not established locally; producer clearance covers project use, not raw-source redistribution. |

### 4.9i Fab prop downloads registered 2026-09-28 (L-0016c)

The original thirteen-listing intake below remains the Ravenshoe prop-layer record (M-008j): assets imported to the map are identified individually, and unused exports remain cache-only. The deeper 2026-10-01 recursive scan in §4.9m covers all 50 physical FabLibrary folders. The `NOT_USED` entry for Old Abandoned Rusty Cars in the table below is superseded by its Wandarra use in §4.9j; seller/AI fields are listing observations only, and producer clearance means no permission hold.

| Listing | Folder in `Content/Downloaded/VaultCache/FabLibrary/` | Seller | `isAiForbidden` | Imported as | Status |
|---|---|---|---|---|---|
| Red car wreck | `Red_car_wreck-04d70886` | *(no listing sidecar)* | **unverified** | `SS_Raven_wreck_car` | `IN_USE` — burning wreck on the bridge deck at OBJ A. 1.17 M tris in the source, prepped to 23 k; producer-cleared for F2P use (ADR-035) |
| Abandoned & junk Car | `Abandoned___junk_Car-ee5cffe5` | PLEXUS GAME ASSETS | `false` | `SS_Raven_wreck_junk` | `IN_USE` — second wreck, creek bed |
| American Old Windmill | `American_Old_Windmill-d8d4a1d3` | Polyvine | **`true`** | `SS_Raven_windmill` | `IN_USE` — north ridge |
| Fuel barrel | `Fuel_barrel-873fee1d` | SampleDotTxt | **`true`** | `SS_Raven_fuel_drum` | `IN_USE` — deck spill and gatehouse cluster |
| Barn | `Barn-eb4457bc` | *(no metadata)* | **unverified** | `SS_Raven_barn` | `IN_USE` — north ridge |
| Military Trenches — Pile Sandbag Canvas 01 | `Military_Trenches_Pile_Sandbag_Canvas_01-a08111c9` | Quixel Megascans | **`true`** | `SS_Raven_sandbag_stack` | `IN_USE` — 8 stacks, both approaches |
| Military Trenches — Wall Metal Corrugated 04 | `Military_Trenches_Wall_Metal_Corrugated_04-e15620d3` | Quixel Megascans *(seller from related Vault listing; no listing sidecar here)* | **unverified** | `SS_Raven_trench_wall` | `IN_USE` — 4 panels at the abutments; no flag is inferred from a neighboring asset. Producer-cleared for F2P use (ADR-035) |
| Old Abandoned Rusty Cars | `Old_Abandoned_Rusty_Cars___...-ed740921` | OlegVerenko | `false`; catalogue also reports `isAiGenerated: true` | `Content/RustyCarsFree/` | `IN_USE` — Wandarra M-009; see §4.9j. This supersedes the earlier Ravenshoe-only not-used decision. |
| Rigged Cargo Container Red PBR | `Rigged_Cargo_Container_Red_PBR-1db0b7e1` | Vadim3dd | **`true`** | — | `NOT_USED` |
| Old Rustic Hand Water Pump | `Old_Rustic_Hand_Water_Pump-0b2fc83d` | Sayan Paul | `false` | `SS_Raven_hand_pump` | `IN_USE` — 3 pumps at the road edge. Authors at 5.85 m tall, prepped to 1.6 m |
| Water Tower | `Water_Tower-86b17984` | Chamod1999 | `false` | `SS_Raven_water_tower` | `IN_USE` — 9 m tower set back at (14, 78) |
| Military Trenches — Debris Pile Rock | `Military_Trenches_Debris_Pile_Rock_S-11e2529f` | Quixel Megascans | **`true`** | — | `NOT_USED` — 19,751 tris for a 0.77 m flat piece |
| Red Tractor, Storage Unit nr5, Old Barn, Wooden Chicken Coop, Crushed Classic Raw Scan, Old Bath | as named | *(mixed)* | **mostly unverified** | `SS_Raven_old_barn` (Old Barn only) | Old Barn `IN_USE` — prepped and placed on the **south** ridge at (66, −104), so each deployment has a landmark. The remaining items are **not selected/imported** in this pass for production-pipeline and art-direction reasons, not licensing: the prep pipeline accepts FBX while Storage Unit is OBJ, Chicken Coop and Tractor are GLB, and Crushed Classic is an unextracted RAR; some have European/Baltic visual references (the storage unit path includes `Daugavpils_skuunis`) that would need a setting-fit decision for a high-country Australian gorge. Producer F2P clearance is recorded under ADR-035. Onboarding would require an OBJ/GLB import path in `prep_fab_props.py` and a deliberate art choice. |

> **Historical flag count.** The figures in the original M-008j intake refer only to that 13-listing sweep. The full recursive snapshot is in §4.9m: sidecar values, including absent metadata, are provenance notes. Under ADR-028/035 they do not create an asset-use or F2P permission hold.
>
> **The VFX pack is reused, not re-registered.** The fire, smoke and ember systems placed on the wreck come from *Realistic Starter VFX Pack Vol 2*, already cleared in 4.9h. They are placed as instances of that pack's own `Spawn_Particle` Blueprint because 5.8's Python cannot persist a runtime-added `ParticleSystemComponent` — see M-008k.

**Standing rule.** A pack's register row is added **in the same change that imports it**, not afterwards.
The CI check covers `.uasset`/`.umap` appearing without a register entry; it does **not** catch a pack that
was already installed, which is how this gap survived.

### 4.9j Fab/Vault downloads registered 2026-09-29 — the MOUT urban training kit

The 2026-09-29 MOUT listing and its then-cache-only candidates are recorded below, with later use states updated from the 2026-09-30 map work. The full cache scan and all 50 physical FabLibrary folders are indexed in §4.9m. Under ADR-028/035, the producer clears their use for this F2P project; metadata gaps remain provenance notes, not use holds.

| Listing | Folder | Seller | `isAiForbidden` | Installed as | Status |
|---|---|---|---|---|---|
| **MOUT urban training kit** (vendor abbreviation for Military Operation Urban Training) | `VaultCache/ModularM6dfea54fd98cV5/` | **unverified** — Vault pack wrote no `metadata` sidecar | **unverified** | `Content/MOUT_Civilian/` — 2.1 GB, 507 files, 3 maps | `IN_USE` — **Wandarra (M-009) since 2026-09-30**: 11 building Blueprints, ChurchKit assembly, FenceSetA, 13 prop sets placed by `build_wandarra_level.py`. First 5.8 load measured **silent** (no upconversion error lines) — R-67's texture/LOD/draw questions remain open. `Docs/MAPS_WANDARRA.md` |
| Old Abandoned Rusty Cars | `FabLibrary/Old_Abandoned_Rusty_Cars___...-ed740921` | OlegVerenko | `false`; metadata also says `isAiGenerated: true` | `Content/RustyCarsFree/` — 69 MB | `IN_USE` — **Wandarra (M-009) since 2026-09-30**: 10 wrecks (`SM_asset_00–04`) as traffic-width cover, depot hulks and green-side parking. The AI-generated field is catalog metadata; use is producer-cleared under ADR-035. |
| Mega Moduler Apartment Building | `FabLibrary/Mega_Moduler_Apartment_Building-db1b80f5` | karaman | **`true`** | — | `NOT_USED` — cache only |
| Modular 3D hospital environment | `FabLibrary/Modular_3D_hospital_environment-7e1574fd` | Madd Game Art | `false` | — | `NOT_USED` — cache only. Listed under *Environments / Horror*; needs an ADR-016 look check before any consideration |
| American Road with Parking Lot | `FabLibrary/American_Road_with_Parking_Lot-a629eb34` | Jimbogies | `false` | — | `NOT_USED` — cache only. GLB, not Unreal content; needs an FBX/GLB import path in the prep pipeline before it can be onboarded |
| Individual First Aid Medical Kit (IFAK) | `FabLibrary/Individual_First_Aid_Medical_Kit_IFAK-a628e3ba` | SpatialNeglect | **`true`** | — | `PLANNED` — the medic's kit (ADR-040). The flag is overruled for every asset (L-0016d) |

| European Beech trees | `VaultCache/MS_Beech_UE51_V2/` | seller and `isAiForbidden` unverified — Vault chunk has a build manifest, no Fab `metadata` sidecar | `unverified` provenance; no use hold | `Content/EuropeanBeech/` — 7.0 GB, 258 files | `IN_USE` — **Wandarra (M-009) since 2026-09-30**: 38 `SimpleWind` static meshes as verge rows, park cluster and depot screen. Authored **UE 5.1 native** (no upconversion); producer-cleared under ADR-035. Row added 2026-09-30. |

> **Metadata note.** MOUT and European Beech arrived by Vault route without a Fab `metadata` sidecar in the
> observed chunks, so their `isAiForbidden` value is unverified. European Beech is in use on Wandarra. This is
> provenance bookkeeping only; producer clearance under ADR-028/035 applies regardless of the sidecar value.
>
> **Why M-009 opened 2026-09-30.** The producer's "one big map" decision of 2026-09-29 supplied the three
> things the 2026-09-29 note lacked: an author (Session 082), an agreed name (Wandarra) and a layout
> (`Tools/Common/wandarra_spec.py`). The candidate became a map, so the id opened in the same change.

### 4.9m Full FabLibrary cache inventory — 2026-10-01 recursive audit (L-0025)

The machine-local `Content/Downloaded/VaultCache/FabLibrary` contains **50 physical listing folders**,
**675 files / 25,051,328,336 bytes (~23.3 GiB)** and a local catalogue database with 57 rows. The catalogue
also contains tool/Vault records and entries without a matching downloaded folder; it is not a one-row-per-folder
index. Recursive inspection found **22 `metadata` sidecars** (some UTF-16): 10 report `isAiForbidden=true`,
12 report `false`; 28 physical folders have no such sidecar, so their sidecar flag is unverified. One local
listing record (`Old Abandoned Rusty Cars`) reports `isAiGenerated=true`. These fields describe local Fab/Vault
metadata, not project-use decisions. **All acquired assets are cleared for this free-to-play game by producer
direction (ADR-035, reaffirmed 2026-10-01); absent metadata is not a hold.** Full methodology, totals and engine
snapshot are also recorded in `Docs/evidence/asset_inventory_20261001.md`.

The 50-folder table records every observed FabLibrary payload directory; rows marked catalogue-only or pointer-only are not counted as extra physical payload folders. `Cache-only` means no installed/project use was identified in this snapshot, not that the producer has withheld F2P clearance.

| Listing | FabLibrary folder | Cached payload (primary formats) | Seller / recorded flag | Project disposition |
|---|---|---|---|---|
| Abandoned & junk Car | `Abandoned___junk_Car-ee5cffe5` | FBX | PLEXUS GAME ASSETS; false | `IN_USE` — `SS_Raven_wreck_junk`, Ravenshoe |
| African Slate Quarry | `African_Slate_Quarry-578d0ceb` | pointer only; Unreal Vault payload is `AfricanS5f01daad2a87V1` | Quixel Megascans; true (Vault listing record) | `IN_USE` — `Content/Scene_QuarrySlate`; maps per §4.9h / PACK_MANIFEST |
| American Old Windmill | `American_Old_Windmill-d8d4a1d3` | FBX | Polyvine; true | `IN_USE` — `SS_Raven_windmill` |
| American Road with Parking Lot | `American_Road_with_Parking_Lot-a629eb34` | glTF + BIN | Jimbogies; false | Cache-only; no project install identified |
| Barn | `Barn-eb4457bc` | FBX | seller/flag unrecorded | `IN_USE` — `SS_Raven_barn` |
| Concrete Barrier | `Concrete_Barrier-a2721342` | FBX + ZIP/textures | seller/flag unrecorded | Cache-only; separate `ConcreteFPPack` is installed |
| Crushed Classic (Free Raw Scan) | `Crushed_Classic__Free_Raw_Scan_-fc2b1e83` | ZIP + RAR/raw scan | seller/flag unrecorded | Cache-only; no extracted game mesh identified |
| Dead Tree | `Dead_Tree-c0c4ec3a` | FBX | Quixel Megascans; true | Cache-only |
| Diesel Compressor IRMER+ELZE | `Diesel_Compressor_IRMER_ELZE-4b406aa6` | FBX | seller/flag unrecorded | Cache-only |
| Faymere River Village A Forgotten Medieval Gem | `Faymere_River_Village_A_Forgotten_Medieval_Gem-6e579cff` | OBJ + 228 BMP textures; ~21.9 GB | seller/flag unrecorded | Cache-only; exceptionally large source drop |
| FPS Animation Pack AKS74U | `FPS_Animation__Pack_AKS74U-75e66639` | Vault pointer; UE pack is `FPSAnimad04f3f6bcc62V1` | y0ung001; false (Vault record) | `IN_USE` — `Content/FP_AKS74U_Animation` references/materials; see §4.9h |
| FPS Guns 4K - Frag Grenade | `FPS_Guns_4K_-_Frag_Granade-0f6e325f` | FBX + Unity-format files/ZIP | seller/flag unrecorded | Cache-only |
| Free Animation Pack | `Free_Animation_Pack-8de31c5d` | FabLibrary catalogue/cache pointer; exact matching payload not independently identified | Gamma Studio; false (local catalogue record) | No separate project install/use established from this FabLibrary row. `SampleAnimationPack` is a separately observed Vault-installed root (§4.9n); do not equate it with `AnimStarterPack`. |
| Free Pack - Male Base Mesh | `Free_Pack_-_Male_Base_Mesh-6ea2f53a` | FBX | PolyOne Studio; false | Cache-only |
| FSB Operator | `FSB_Operator-d68905bd` | GLB | SpatialNeglect; false | Cache-only. Listing describes third-party clothing pieces; preserve its source/credit list if ever used |
| Fuel barrel | `Fuel_barrel-873fee1d` | FBX | SampleDotTxt; true | `IN_USE` — `SS_Raven_fuel_drum` |
| G17 - FPS Weapon Animations Pack | `G17_-_FPS_Weapon_Animations_Pack__v_1_-5b920af4` | FBX | BarcodeGames; false | `IN_USE` — animation assets, L-0023 |
| Gloves for fps game | `Gloves_for_fps_game-1b65b8fa` | FBX + textures | Bobeer; false | Cache-only; L-0023 says unused; retain CC-BY 4.0 credit if later used |
| Individual First Aid Medical Kit IFAK | `Individual_First_Aid_Medical_Kit_IFAK-a628e3ba` | GLB | SpatialNeglect; true | Cache-only / planned medic asset (ADR-040); seller flag is metadata, producer-cleared |
| Large Fallen Tree (listing 5796…) | `Large_Fallen_Tree-5796e9d5` | glTF + BIN/ZIP | seller/flag unrecorded | Cache-only |
| Large Fallen Tree (listing f36e…) | `Large_Fallen_Tree-f36e4566` | glTF + BIN/ZIP | seller/flag unrecorded | Cache-only; distinct listing from prior row |
| M4 - FPS Weapon Animations Pack | `M4_-_FPS_Weapon_Animations_Pack_FREE__v_1_-38da8f1e` | FBX + textures | BarcodeGames; false | `IN_USE` — animation assets, L-0023 |
| Mega Moduler Apartment Building | `Mega_Moduler_Apartment_Building-db1b80f5` | GLB | karaman; true | Cache-only |
| Metal Barricade | `Metal_Barricade-92c093cb` | FBX + ZIP/textures | seller/flag unrecorded | Cache-only |
| Military Trenches Barrier Sandbag Canvas 03 | `Military_Trenches_Barrier_Sandbag_Canvas_03-036e6adf` | FBX | seller/flag unrecorded | Cache-only |
| Military Trenches Debris Pile Rock S | `Military_Trenches_Debris_Pile_Rock_S-11e2529f` | FBX | Quixel Megascans; true | Cache-only |
| Military Trenches Pile Sandbag Canvas 01 | `Military_Trenches_Pile_Sandbag_Canvas_01-a08111c9` | FBX | Quixel Megascans; true | `IN_USE` — `SS_Raven_sandbag_stack` |
| Military Trenches Wall Extrusion Metal Corrugated 02 | `Military_Trenches_Wall_Extrusion_Metal_Corrugated_02-ae8080c4` | glTF + BIN/ZIP | seller/flag unrecorded | Cache-only; distinct from wall set 04 |
| Military Trenches Wall Metal Corrugated 04 | `Military_Trenches_Wall_Metal_Corrugated_04-e15620d3` | FBX | Quixel series; sidecar absent, flag unverified | `IN_USE` — `SS_Raven_trench_wall`; do not infer sibling's AI flag |
| Military Trenches Wall Metal Corrugated 16 | `Military_Trenches_Wall_Metal_Corrugated_16-823bd558` | catalog entry; no matching physical FabLibrary folder | seller/flag unrecorded | Catalogue-only; no cached payload identified |
| Military Trenches Wire Barbed Set | `Military_Trenches_Wire_Barbed_Set-caec3ac3` | glTF + BIN/ZIP | Quixel Megascans; true | Cache-only |
| Modern Gun Shooting Mocap Pack | `Modern_Gun_Shooting_Mocap_Pack-aec2f77f` | FBX clips | seller/flag unrecorded | Cache-only |
| Modular 3D hospital environment | `Modular_3D_hospital_environment-7e1574fd` | FBX + textures/ZIP | Madd Game Art; false | Cache-only; metadata describes 25 interior meshes, textures supplied separately |
| Mud Surface Scan | `Mud_Surface_Scan-f23ef271` | glTF + BIN/ZIP | seller/flag unrecorded | Cache-only |
| Old Abandoned Rusty Cars | `Old_Abandoned_Rusty_Cars___Overgrown_Post-Apocalyptic_Vehicle_Props_Free_3d_Pack-ed740921` | FBX | OlegVerenko; false; `isAiGenerated=true` | `IN_USE` — `Content/RustyCarsFree`, Wandarra (M-009) |
| Old Barn | `Old_Barn-4915f85e` | FBX | seller/flag unrecorded | `IN_USE` — `SS_Raven_old_barn` |
| Old Bath | `Old_Bath-b517e936` | ZIP only | seller/flag unrecorded | Cache-only; no unpacked model found |
| Old Freight Wagon [FREE] | `Old_Freight_Wagon__FREE_-fe7e6c8c` | Blender + ZIP/textures | seller/flag unrecorded | Cache-only |
| Old Rustic Hand Water Pump | `Old_Rustic_Hand_Water_Pump-0b2fc83d` | FBX | Sayan Paul; false | `IN_USE` — `SS_Raven_hand_pump` |
| Old Tree Branch | `Old_Tree_Branch-0c05052e` | glTF + BIN/ZIP | seller/flag unrecorded | Cache-only |
| Quantum Modular Character Free Sample | `Quantum_Modular_Character_Free_Sample-8e200050` | Vault pointer; UE pack is `QuantumMfb9fb897041bV1` | Quantum Assets; false (Vault record) | `IN_USE` — `Content/QuantumCharacter` plus tracked retarget prototype modules/material assets in `Plugins/GameFeatures/SSExp_ObjectiveAssault/Content/Characters/QuantumProto/`; friendly body (ADR-042) |
| Red Tractor | `Red_Tractor-dc5a5431` | GLB + ZIP/textures | seller/flag unrecorded | Cache-only |
| Red car wreck | `Red_car_wreck-04d70886` | FBX + ZIP/textures | seller/flag unrecorded | `IN_USE` — `SS_Raven_wreck_car` |
| Rigged Cargo Container Red PBR | `Rigged_Cargo_Container_Red_PBR-1db0b7e1` | FBX | Vadim3dd; true | Cache-only |
| S.W.A.T. Operator Special Remaster | `S_W_A_T__Operator-_4k_Followers_Special_Remaster-09e47572` | GLB | SpatialNeglect; false | Cache-only. Listing identifies seven CC-BY contributors: Bobeer (gloves), VassKacsoHunor (NVGs), Simon Coenen (helmet), Bzovius (uniform), Albin (boots), Shedmon (balaclava), h1ggs (VECTOR). Preserve listing source/credit details if ever used (L-0025). |
| Storage unit nr5 | `Storage_unit_nr5-bc8df922` | OBJ + ZIP/textures | seller/flag unrecorded | Cache-only |
| Traffic Cones | `Traffic_Cones-96d505b4` | glTF + BIN/ZIP | seller/flag unrecorded | Cache-only |
| Trailer Park | `Trailer_Park-e6f0267a` | ZIP + RAR and 96 images | seller/flag unrecorded | Cache-only; no unpacked model identified |
| Water Tower | `Water_Tower-86b17984` | FBX + ZIP/textures | Chamod1999; false | `IN_USE` — `SS_Raven_water_tower` |
| Wooden Chicken Coop | `Wooden_Chicken_Coop-57c94567` | GLB | seller/flag unrecorded | Cache-only |
| Worn bandages | `Worn_bandages-1647b37a` | glTF + BIN | Sousinho Games; true | Cache-only |

> The local catalogue has 57 rows (51 `local_listing` records), not one row per physical download. Records
> without a matching FabLibrary folder include the plain `American Road`, `Middle Eastern Armed Fighter`,
> `Old garage`, and the two additional Military Trenches listings (Sandbag Canvas 02 and Wall Metal Corrugated
> 16); tool/plugin and Vault-pointer records also occur in the catalogue. These are catalogue records, not
> extra physical payload folders. Seller flags and metadata above are transcribed from local records/sidecars;
> missing values remain `unverified`. None creates a project-use hold under ADR-028/035.


### 4.9n Other Vault chunks and installed Content roots (machine-local snapshot)

`Content/Downloaded/VaultCache` has **30 top-level directories / 7,366 files / 58,343,692,654 bytes (~54.3 GiB)**.
The FabLibrary root is inventoried in §4.9m. The remaining 29 Vault directories include installed UE projects,
map-independent tools and content not in the map-dependency manifest. The project's full `Content/` tree was
**29,437 files / 118,405,659,191 bytes (~110.27 GiB)** at this local snapshot (including vendor, source and
shared-worktree files; not a tracked-only measurement). The following installed vendor roots are present; their
per-root size/counts are local snapshot measures, not tracked Git asset totals:

| Installed Content root | Files | Approx. size | Notes / use recorded |
|---|---:|---:|---|
| `AK-47` | 58 | 56 MiB | weapon reference pack; not used in-game, retained for reference under L-0016 |
| `AnimStarterPack` | 85 | 24 MiB | locally installed animation sample; distinct from `SampleAnimationPack`; no use inferred from presence alone |
| `AutomotiveBridgeScene` | 323 | 2.0 GiB | present locally; not in the 14-pack `PACK_MANIFEST`; no current map dependency identified by this snapshot |
| `ConcreteFPPack` | 72 | 223 MiB | concrete FPS pack |
| `DeadBodies_Poses_nikoff` | 56 | 147 MiB | pose/mocap content |
| `EuropeanBeech` | 258 | 6.9 GiB | in use on Wandarra; see §4.9j / L-0016c |
| `FP_AKS74U_Animation` | 61 | 186 MiB | materials referenced by MAF weapon assets; §4.9h |
| `FPS_Weapon_Bundle` | 220 | 197 MiB | weapon reference bundle; not-used per L-0016 |
| `HighPoly_Tree_Model` | 9 | 37 MiB | installed 2026-10-01; showcase tree + demo floor map; **not referenced by any committed asset**; ADR-021/028 |
| `Insurgent_2` | 105 | 489 MiB | not used per L-0016; source content remains installed |
| `Light_Foliage` | 110 | 195 MiB | foliage pack |
| `M1911` | 31 | 37 MiB | weapon reference pack; not-used per L-0016 |
| `Military_Radio` | 55 | 243 MiB | radio/headset props; in use |
| `Modern_Insurgent_7` | 115 | 733 MiB | head/character source; current MAF dependency recorded in L-0016 |
| `Modular_Rural_Cabin` | 587 | 1.5 GiB | conifers; in use |
| `MOUT_Civilian` | 507 | 2.1 GiB | Wandarra buildings/fences; in use; UE 4.26 content loaded under 5.8 (R-67) |
| `MSPresets` | 102 | 22 MiB | material presets |
| `MWLandscapeAutoMaterial` | 100 | 701 MiB | landscape material pack |
| `Namaqualand` | 728 | 4.7 GiB | Dry River/Saltbush flora and ground dressing |
| `PN_GrassLibrary` | 626 | 1.1 GiB | installed 2026-10-01; grass foliage library + bending/global-updater blueprints; **not referenced by any committed asset**; ADR-021/028 |
| `Nanite_Plants_Sample_Collection` | 120 | 100 MiB | installed; not used per L-0016 |
| `QuantumCharacter` | 110 | 863 MiB | friendly body; use in ADR-042 |
| `Realistic_Starter_VFX_Pack_Vol2` | 188 | 110 MiB | fire/smoke/ember effects; in use |
| `RuralAustralia` | 436 | 2.3 GiB | Red Gum / Dry River ground, foliage and cover |
| `RustyCarsFree` | 57 | 68 MiB | Wandarra wreck cover; in use |
| `SampleAnimationPack` | 173 | 495 MiB | animation sample; installed, not used; distinct from the separate `AnimStarterPack` root |
| `Scene_QuarrySlate` | 396 | 2.6 GiB | rock/terrain dressing; maps use it |
| `Singapore_Canal` | 489 | 2.1 GiB | generic props/material references on Dry River and Red Gum; no Asian base-map reuse |
| `Splash` | 2 | 1.1 MiB | installed 2026-10-01; `Splash.bmp` + `Splash.uasset`; origin and intended use **not established**; **not referenced by any committed asset** |
| `StoneWell` | 42 | 1.2 GiB | Dry River well; one map reference; producer-cleared, listing identity not recorded |
| `WaterPlane` | 34 | 139 MiB | installed 2026-10-01; creek normal (`T_MediumWaves_N.uasset`, ENV-005 → `M_SS_CreekWater`) **is tracked and stays tracked**; remaining 33 files local/untracked per ADR-021; not map dependencies by inference |
| `World_Flags` | 344 | 549 MiB | Friendly/MAF flag material instances reference this pack |

**Git treatment of the four 2026-10-01 installs.** `Content/HighPoly_Tree_Model/`, `Content/PN_GrassLibrary/`,
`Content/Splash/` and `Content/WaterPlane/` were imported into `Content/` on 2026-10-01 and are ignored under
ADR-021 (`.gitignore`, block added in Session 093). Measured with `Tools/verify_packs.py scan_references()`:
**no committed asset references any of the four roots**, so they are *installed* but not *map dependencies* and
they are correctly absent from the 14-pack `PACK_MANIFEST` scope in §2 of that document. The one tracked file
inside an ignored root, `Content/WaterPlane/Lake/Textures/T_MediumWaves_N.uasset`, was already committed before
the rule was added (ENV-005, feeds `M_SS_CreekWater`); `.gitignore` does not untrack it, and a committed
project material requiring a vendor texture is a deliberate exception rather than an oversight.

Other Vault records observed: African Slate Quarry (`Scene_QuarrySlate`), Asian Canal (`Singapore_Canal`),
Automotive Bridge Scene, Concrete Block FPS Animation Pack, Dead Bodies Sitting & Lying Poses, Flag Props
Package, FPS Weapon Bundle, Free Animation Pack, Light Foliage, Modular Insurgent 2, Modular Rural Cabins,
Namaqualand, Quantum Modular Character, Realistic Starter VFX, Rural Australia, Stone Well, and other roots
listed above. `VisAI - Community - Modern AI Framework` is present only under the local Vault cache; no
installed root/plugin was found in `Content/` or `Plugins/`. Lyra's separate launcher-cache reference is not
counted as project content.

**Additional project-local source/art findings (not vendor packs):** `Content/Art/` holds original map, dressing,
character and surface assets plus Blender/FBX/CSV sources; `Content/ghostgum/` and `Content/kangaroo/` retain
source models/archives registered as ENV-003/ENV-004; `Content/Maps/` holds authored levels; `Content/Splash/`
currently contains `Splash.bmp` + `Splash.uasset` in the shared, untracked worktree (origin and intended use not independently established; do not overwrite). `Content/Sourced/` is a segregated mixed source/review collection (see `SOURCED_ASSET_REVIEW.md`, L-0021 and R-17/R-25), not a runtime-use manifest. The producer's project-use clearance covers acquired assets; ripped commercial-game content remains excluded and R-25 tracks the raw tree's Unreal-content-root handling. These notes inventory
what exists; they do not claim each file is referenced by a shipping map.

### 4.9o Unreal Engine foundation assets (UE 5.8.3 Installed Build; L-0002)

The local engine at `E:\\Unreal\\UE_5.8` is UE **5.8.3, CL 58210709**, `InstalledBuild.txt` = `UE_5.8`. The counts and dependency scan in §4.9o include **Engine/Content, Engine/Plugins, FeaturePacks and Templates**; this document records the principal scopes and selected project references, not every individual engine asset. Engine-supplied assets are not copied into project `Content/` and are not enumerated file-by-file here. This snapshot found:

| Engine scope | Files | Approx. size | Register treatment |
|---|---:|---:|---|
| `Engine/Content` | 40,056 | 1.47 GiB | Epic engine content under L-0002; includes EngineMaterials, BasicShapes, EngineMeshes, EngineSky, EngineSounds, EngineFonts, EngineResources, Maps/Templates and editor-only resources |
| `Engine/Plugins` | 113,127 | 20.10 GiB | 901 `.uplugin` descriptors; includes Engine plugins/content. Presence does not mean a plugin is enabled or shipped |
| `FeaturePacks` | 9 | 2.2 MiB | Epic starter/template `.upack` files |
| `Templates` | 5,880 | 0.99 GiB | Epic template project content; not assumed in game |

`SouthernSpear.uproject` declares 95 plugin entries: 84 enabled and 11 disabled. Notable enabled plugins include
GameplayAbilities, GameFeatures, EnhancedInput, Niagara, Water, CommonUI, AnimationWarping, ShooterCore and
Southern Spear modules; Fab plugin folders exist in the engine but are not evidence that Fab is active in this
project. A scan of tracked `.uasset`/`.umap` dependencies found 126 persistent `/Engine/` package paths (1,953
referrer edges; transient Interchange/editor import references excluded from the persistent figure). Fifteen
engine asset paths are referenced by project maps or Southern Spear Game Feature content, notably
`/Engine/BasicShapes/{Cube,Cylinder}`, `/Engine/EngineMaterials/{DefaultPhysicalMaterial,FlatNormal,WorldGridMaterial}`,
`/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst`, `/Engine/EngineResources/{Black,DefaultTexture,WhiteSquareTexture}`,
`/Engine/Maps/{Entry,Templates/OpenWorld}`, and the editor/audio icons under `/Engine/EditorResources`. Lyra and
other enabled project plugins also reference engine functions, meshes and animation defaults. The large remainder
of the engine catalog is installed foundation, not an asset individually selected for Southern Spear; engine
EULA obligations remain under L-0002.

### 4.9p Tracked A-series weapon feature assets (source-control inventory)

A 2026-10-01 scan of tracked Unreal content found weapon meshes, texture and material assets in the game feature (not only under root `Content/`). Counts are asset files, not unique runtime-selected resources; this does not establish that all variants or materials are currently mounted/visually verified.

| Game-feature weapon root | Tracked assets | Notable content |
|---|---:|---|
| `Weapons/A88` | 30 | Mesh and imported texture/material assets |
| `Weapons/A88G` | 30 | A88 cosmetic variant assets |
| `Weapons/A89` | 28 | A89 mesh/material/texture assets |
| `Weapons/A4` | 64 | A4 mesh/material/texture assets |
| `Weapons/A416` | 48 | A416 mesh/material/texture assets |
| `Weapons/A25` | 49 | A25 mesh/material/texture assets |
| `Weapons/A9` | 22 | A9 mesh/material/texture assets |
| **Total** | **271** | **151 texture (`T_`) and 82 material-instance (`MI_`) assets** |

These tracked imports correct the stale Session 090 claim that no weapon textures were in the repository. The A88 row W-A88-02 and the aggregate counts do not prove the active runtime graph or visual quality; NEXT_PRIORITIES §3 keeps that verification open. The external map dependency manifest remains a different, map-only inventory.

### 4.10 Data Assets (no third-party licence dependency — original data)

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

## 5. Summary — Current State (plan asset counts; separate from local inventory totals)

| Category | Placeholder | Vendored | In production | Deferred | Done |
|---|---|---|---|---|
| Weapons (15 planned foundation items) | 12 | 0 | 3 (W-001 A88, W-002 A89, W-003 A9; wider tracked A-series inventory in §4.9p) | 0 | 0 |
| Characters (18) | 12 (C-003–C-004, C-006–C-007, C-009–C-013, C-016–C-018) | 3 (C-001 Quantum body, C-005 helmet, C-008 plate carrier) | 1 (C-015 MAF assembly) | 1 (C-002 female body) | 1 (C-014 CMECU texture set) |
| Animation (13 planned items) | 9 (A-003–A-009, A-011–A-012) | 1 (A-001 Lyra locomotion) | 1 (A-010 hand-IK implementation; pose change is measured, broader fit/visual acceptance remains open) | 2 (A-002 prone set, A-013 animation LODs) | 0 |
| Audio (13 planned + S-014 source addition) | 13 planned rows remain placeholders | 0 | 1 (S-014 ADFRC AUG/A88 recording source set) | 0 | 0 |
| Effects (7) | 5 | 0 | 1 (E-005 spent-case proxy/eject in production) | 1 (E-004 dust / weather) | 0 |
| UI (12 planned items) | 10 (U-002–U-010, U-012) | 1 (U-001 Lyra config) | 1 (U-011 rank marks; qualification badges remain open) | 0 | 0 |
| Maps / layers (original M-001–M-007 foundation plan) | 1 (M-006) | 1 (M-007 Lyra front end) | 5 (M-001–M-005 built/in production; not sign-off) | 0 | 0 |
| Data (10) | 10 | 0 | 0 | 0 | 0 |
| Tooling (2-item initial plan only; later tools excluded) | 0 | 0 | 0 | 0 | 2 (initial blockout generator + verifier; later tooling tracked in §§4.9a–p) |

**The weapon intake in §4.9d is producer-cleared for Southern Spear's free-to-play use under ADR-035.** Its raw source files remain local review material; W-001's A88 appearance still has source-documentation and fictional-design work recorded under R-21, but those are not project-use permission holds. W-002 is original work in production. The photogrammetry sources in §4.9b remain unchanged review copies and are not imported Unreal assets; producer clearance does not turn a source/review copy into an approved or referenced game asset.

---

## 6. Placeholder Policy

1. A placeholder is **visibly** a placeholder — grey-boxed or primitive, never a low-effort imitation that could be mistaken for final art.
2. A placeholder carries no licence obligation and no attribution requirement.
3. Every placeholder is listed in this register until replaced.
4. Placeholders are acceptable in the vertical slice. **They are not acceptable in a release build**, and a release-build check that fails on any remaining placeholder is a packaging gate.

---

### 4.9k Animal and native flora models registered 2026-09-30 (L-0024) — easter-egg dressing

Two model sets arrived in `Content/ghostgum/` and `Content/kangaroo/` on 2026-09-30 with no provenance
metadata. Registered here under L-0024. Their seller/source details remain **unverified provenance**; the
producer has cleared their use in Southern Spear's free-to-play game. The status column distinguishes source
staging from Unreal import and map placement.

| ID | Asset | Path | Contents | Status | Licence dep. | Notes |
|---|---|---|---|---|---|---|
| ENV-003 | Ghost gum tree model + texture set | `Content/ghostgum/` | `source/TH_Complete_Full_Ghoast_Gum.fbx` (full tree), 8 TGA source textures (diffuse, normals, spec, branch alpha set), `textures/` PNG derivatives. 20 MB. `source/TH_Ghoast_Gum.zip.zip` is the original archive, kept for provenance | `VENDORED` — staged; **`IN_USE`: imported 2026-09-30** (Session 088) as `/Game/Art/Environment/Fab/TH_Complete_Full_Ghoast_Gum` + 6 maps under `Fab/GhostGum/` + `MI_SS_GhostGum_{Trunk,Branch,Leaf}`; 10 placed on Dry River as the windmill screen ring | **L-0024** — seller/licence metadata absent; producer-cleared for F2P use; retain provenance note | "Ghoast" [sic] spelling is the vendor's. Australian ghost gum look fits ADR-016. Measured at import: 656 × 615 × 651 cm bounds, 2 material slots (`blinn5` trunk, `TH_Gum_Branch_Blinn` foliage cards — the second slot carries the **leaves**, so it must take the alpha-masked Leaf instance or the tree renders grey and bare; that was the producer's "grey leafless gum") |
| ENV-004 | Kangaroo model + texture set | `Content/kangaroo/` | `source/source/kangaroo.FBX` (+ `.obj`/`.mtl` twins), 8 JPG + 1 TGA textures. 24 MB. `source/kangaroo.rar` is the original archive, kept for provenance | `VENDORED` — staged; **imported this change for the easter egg** (see below) | **L-0024** — seller/licence metadata absent; producer-cleared for F2P use | Static prop — no rig, no animation in the source. Producer intent: 2–3 individuals as an easter egg under trees on Dry River (M-001) and Red Gum Station (M-RG-01) |

> **Provenance note (updated 2026-09-30, producer decision).** Both sources arrived without licence files or
> seller metadata. The producer has confirmed all models downloaded for or used in the project are **free and
> cleared for use in the game** — producer risk acceptance under the ADR-035 posture. R-90a is therefore
> **closed**; the register keeps the unverified-metadata observation for the credits record only.

**Easter-egg placement (recorded 2026-09-30):** four kangaroo static meshes were reported placed under existing tree canopies — 2 on Red Gum Station and 2 on Dry River — by `Tools/Unreal/dress_kangaroo_easteregg.py`, labels `SS_EasterEgg_Kangaroo_N`, terrain-anchored to the tree pivot, collision off (decoration only). The 2026-10-01 review has not re-opened those maps to re-verify current placement; the last recorded Dry River view showed clay-grey appearance. Current presence and appearance need a new in-game check; this is not a clearance issue.

### 4.9l Dry River overhaul additions (Session 088) — original assets authored for D-DR-05

Both are script-authored originals with no third-party dependency, created because no installed pack asset
did the job. Registered in the same commit as the assets themselves, per §7.

| ID | Asset | Path | Source | Licence dep. | Notes |
|---|---|---|---|---|---|
| ENV-005 | Dry River creek water material | `Content/Art/Environment/DryRiver/M_SS_CreekWater.uasset` | `Tools/Unreal/author_creek_water.py` | **Class F — original** | `BLEND_TRANSLUCENT` / `MSM_DEFAULT_LIT`. Fresnel-lerped base colour (deep 0.012/0.022/0.020 → edge 0.045/0.075/0.085), roughness 0.06 → 0.30, opacity 0.60 → 0.94, panner-driven normal from `T_MediumWaves_N` (4.9h). Written because the only pack water in the project — `Scene_QuarrySlate` `M_Qua_Sla_Water_01` — read as a glossy orange strip on red dirt and was deleted from the creek in `expand_dryriver.py`. **Not yet visually confirmed in game** |
| ENV-006 | Gum trunk collider helpers | `L_DryRiver_01`, labels `SS_Gum_TrunkCol_00..09` | `Tools/Unreal/harvest_dryriver.py` (engine `BasicShapes/Cylinder`) | **Class F — original** | Invisible, non-shadowing `BlockAll` cylinders giving the 10 ENV-003 ghost gums trunk collision without making their canopies solid — Lyra has no vault, so a colliding canopy is worse than none. Untextured by design; the overhaul audit counts them in a separate `collision_only_default_material` list so they can never be mistaken for a D-DR-02 grey-asset defect |

> **Historical kangaroo visual finding (Session 088; last verified 2026-10-01).** The saved material instance read back with both maps bound, and the Dry River animals were re-seated on a ground trace; the last recorded game view still showed a clay-grey appearance. Treat this as unresolved visual verification, not proof that the current saved map/materials still have that state. A current in-game capture is required before closing D-DR-02.

## 7. Register Maintenance

This register is updated **in the same change** as any asset addition or status change. An asset that appears in the repository but not in this register is a build-review failure.

Each entry needs: a stable ID, the asset's name, its status, its licence dependency (or "original"), and where the source `.blend` lives if it is original production.
