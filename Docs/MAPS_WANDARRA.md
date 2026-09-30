# MAP: Wandarra (M-009) — the MOUT training village

**Document ID:** `Docs/MAPS_WANDARRA.md`
**Status:** Built greybox, in Unreal — **navmesh not yet baked (R-82)**, spawns not yet laid;
dressing pass (awnings + gate doors, Session 084) queued behind a rebuild that applies the Session
083 yaw correction below
**Last updated:** 2026-09-30 (Session 082)
**Map asset:** `/Game/Maps/L_Wandarra_01`
**Layout spec:** `Tools/Common/wandarra_spec.py` — every position below is read from it

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence
> Force, the Department of Defence or the Australian Army. Wandarra is an **invented** township,
> laid out from gameplay requirements. It must not reproduce any real base, installation or
> operationally useful site (ASSET_REGISTER §4.9 layout rule).

---

## 1. What Wandarra is

The producer's decision of 2026-09-29 resolves the open question in `MAPS_TRAININGRANGE.md` §4:
**one big map** built from the MOUT urban training kit, with every other installed-and-unused pack
brought in — RustyCarsFree's wrecks and the 7 GB EuropeanBeech forest (UE 5.1 native, so the only
one of the three with no upconversion question at all).

The name follows the register's convention of invented Australian locality names (Ravenshoe, Red
Gum): *wandarra* is constructed from "wan" (crow) + "dharra" (to have), glossed here as "place of
the crow" — like Ravenshoe, a bird-place name. No real locality named Wandarra is reproduced or
referenced; the layout below is designed, not surveyed.

**Role** (GDD §5 modules 1 and 4): close-quarters clearing, doorway work and identification among
lookalike buildings — the training environment `MAPS_TRAININGRANGE.md` judged this kit best for,
plus a full Objective Assault layout like every other map. M-006 stays an open range question;
this map stands beside it as the urban half of training.

## 2. The site

300 × 300 m flat site, ground at z = 0 (a cube slab under `M_SS_WorldGroundVT`, instanced as
`MI_SS_WorldGround_Wandarra` — Ravenshoe gravel textures, world-mapped, 3 m tile, tinted toward
dry township earth). Two streets cross at the centre:

- **Main street**, north–south at x = 150: 7 m bitumen + 1.5 m footpath each side (11 m corridor)
- **Cross street**, east–west at y = 150, running from the church (west) to the government block

Four named places sit in the quadrants:

| Place | Where | What |
|---|---|---|
| The depot | NW, 65 × 80 m fenced compound | compound-clearing practice; two gates left open |
| The civic block | N of the cross street | `BP_GovernmentBuilding_01` with benches, police sign, hydrant |
| The park | NE | the open heart: fountain, playground, benches, tree cluster |
| The green | SE | low-cover approach lane: picket fence, bus stop, clothes lines |

## 3. What was placed (2026-09-30, all from the spec)

| Layer | Count | Source | Notes |
|---|---|---|---|
| Buildings | 11 | MOUT `Blueprints/Buildings/` | 6 bungalows, 4 houses (2-storey), 1 government building; vendor Blueprints with interiors |
| Church | 17 parts | MOUT `ChurchKit/` | assembled in place (vendor BP set has no church): 8 m × 16 m nave, gabled roof, west bell tower + cross, east door terminating the cross street |
| Fences | 168 segments | MOUT `FenceSetA` | 5 runs (depot compound walls, green picket boundary), gates left open |
| Furniture | 35 props | MOUT `Meshes/Props/` | bollards, hydrants, bins, post boxes, bus stops, benches, power poles, police sign, clothes lines, fountain, playground |
| Cars | 10 wrecks | RustyCarsFree `SM_asset_00–04` | traffic-width cover on the streets (the stalled car in the Crossing is the signature cover), hulks in the depot, parked along the green |
| Trees | 38 | EuropeanBeech `SimpleWind` | verge rows, park cluster, depot screen; deterministic jitter (seed 20260930) |
| Ground | 1 | project (Ravenshoe gravel) | world-mapped VT material instance |

Excluded by rule: the pack's `Demo/` first-person character and weapon (ADR-020 — weapons are
script-built on Lyra sockets), the Flag skeletal mesh (needs an AnimBP and belongs to no gameplay
path), the AwningKit Blueprints (50 pieces, not yet needed), the beech PivotPainter/wind WIG
variants (the SimpleWind statics need no WPO setup), ivy meshes (European look — not used).

**Objectives** (sequential Objective Assault A→B→C, radii 900 cm, the project's urban standard):

| # | Name | Site position | Why |
|---|---|---|---|
| A | Bus Stop Corner | (150, 60) | the first fight off both deployments, on the main street |
| B | The Crossing | (150, 150) | the intersection: open ground broken by the stalled car |
| C | Church Square | (60, 150) | the church forecourt: vista terminus, hardest opening to defend |

**Deployments**: TeamOne behind the depot (30, 255), TeamTwo behind the green (270, 40) — both
screened by fences and trees, each opening on a ~200 m advance along its street. Legs Depot→A→B→C→Green
are ~90 m each. `layout_spawns.py` is the final authority on the 8 starts per team (ADR-018) and
runs after the navmesh exists.

The `SSObjectives` director is placed, `NavMeshBoundsVolume` scaled to the site (75, 75, 15 — the
×4-on-reload factor from R-10 is already accounted), a `RecastNavMesh` actor is saved into the map,
and WorldSettings.DefaultGameplayExperience is `B_SS_ObjectiveAssault`.

### 3.1 Dressings: awnings and gate doors (Session 084, ADR-041)

Six government awnings (four vendor Blueprint types, `BP_GovernmentAwning_01a/b`, `02a/b`) dress the civic face
and the row buildings' footpath sides as shopfront verandahs — a covered edge that breaks street
sightlines at torso height. The dressing pass (`Tools/Unreal/dress_wandarra_awnings.py`) pushes each
awning out along its facing until it clears the building's **measured** box by 40 cm, because the
spec row is the intent and the real vendor footprint is whatever R-90's dump says it is. That same
run performs the R-90 measurement: every building's actor bounds dumped to site coordinates,
road-corridor overlaps reported, corrections landed in the spec as a rebuild.

Two interactable door Blueprints stand **at the side gates, as scenery**: the depot's side gate and
the green's picket gate. Per ADR-041 they are not wired into gameplay this
phase — no input binding, no interaction target; the vendor door Blueprints ship with embedded
compile errors and client-local timelines, and the project's interact input is already assigned to
casualty care (ADR-040). Gate gaps were narrowed to 2.4 m personnel width so a door reads as a door,
and the depot's main gate stays an **open** 2.4 m gap on purpose: TeamOne spawns inside the compound
and the navmesh bakes a closed door as a blocker, so the compound's walkable exit never depends on an
unwired door. Doors open for nothing until a server-owned `USSDoorComponent` path is built; that is a
decision, not an omission — see ADR-041 for the phase-2 route.

## 4. Provenance and licence

| Pack | Installed as | Engine | Licence | Seller / AI flag |
|---|---|---|---|---|
| MOUT urban training kit | `Content/MOUT_Civilian/` (2.1 GB) | UE 4.26, upconverted on load (R-67) | Fab Standard A (L-0016) | **unverified** (no `metadata` sidecar, L-0016c) |
| Old Abandoned Rusty Cars | `Content/RustyCarsFree/` (69 MB) | — | Fab Standard A (L-0016) | OlegVerenko, `isAiForbidden: false` |
| European Beech trees | `Content/EuropeanBeech/` (7 GB) | **UE 5.1 native** | Fab Standard A (L-0016) | **unverified** (Vault chunk manifest only, no `metadata`, L-0016c) |

Pack assets are referenced in place, never modified (ADR-021). All three packs sit on the
git-ignored path; the repo carries the build scripts, the spec, the docs and the map.

## 5. Pipeline (the Dry River pattern, one map built not copied)

| Pass | Script | What it does |
|---|---|---|
| spec | `Tools/Common/wandarra_spec.py` | pure-Python single source: kit paths, layouts, PROTECTED zones, `seg_point_distance`, `run_clears_protected` (Liang–Barsky) |
| level | `Tools/Unreal/build_wandarra_level.py` | delete+`new_level`, ground, buildings, church, fences, furniture, cars, trees, objectives, director, nav volume, experience, lighting; saves |
| nav | `Tools/Unreal/build_wandarra_nav.py` | reload saved map, validate actor nav-export policy, sample saved nav coverage, verify the designed Depot→A→B→C→Green legs and repair only what cannot walk them; it does **not** bake paths |
| light | `Tools/Unreal/light_wandarra.py` | idempotent `SS_Light_*` rig (as `light_dryriver.py`) |
| spawns | `Tools/Unreal/layout_spawns.py` (SS_MAPS=L_Wandarra_01) | 8 starts per team on the navmesh — after the bake |

Run form (`PLAYTEST_COMMANDS.md` §5):

```
"/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "E:/SouthernSpear/SouthernSpear.uproject" \
  -nullrhi -unattended -nosplash -nosound \
  "-ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/<pass>.py" \
  -abslog=E:/SouthernSpear/Saved/Logs/SS_wandarra_<pass>.log
```

Reports: `Build/wandarra_level.json`, `Build/wandarra_nav.json`, `Build/wandarra_lighting_report.json`.

**Coordinate transform** (same silent-failure class as MAPS_DRYRIVER §11.2): the spec is metres on
a south-west-origin site frame; the builder writes `(x·100, −y·100, z·100)` — **Y mirrored**. Yaw
is site-frame degrees clockwise from north and converts as **`yaw − 90`** (site north = Unreal −Y =
Unreal yaw −90; site east = +X = 0; site south = +Y = 90). The first build shipped `-yaw`, which
put every rotated actor one cardinal direction off — found on 2026-09-30 while deriving the
awning push-out vector (Session 084), fixed in `build_wandarra_level.py`. The level was rebuilt and
dressed on 2026-09-30 (Session 086): the saved map now carries the corrected yaw and current gate
layout. The transform is code- and report-verified; the attended visual inspection and nav bake
remain outstanding.

## 6. Verification status (honest numbers, 2026-09-30)

| Check | Result |
|---|---|
| Python syntax checks | PASS (exit 0) for `wandarra_spec.py`, level, dressing, nav-verifier and spawn-layout scripts |
| Spec unit checks (`seg_point_distance`, protected-zone blocking) | PASS (Session 082) |
| Level pass headless | **ok: true** — 12/12 steps; 11 buildings, 17 church parts, 183 fence segments, 35 props, 10 cars, 38 trees; no missing assets/errors |
| Dressing + bounds pass headless | **ok: true** — 11 building bounds, 0 road-corridor overlaps, 6/6 awnings (5 pushed clear; max 2.7 m), 2/2 scenery doors; no missing assets/errors |
| Saved actor nav-export policy | 38 trees and 10 cars excluded from Recast mesh export; placed world collision remains enabled |
| `L_Wandarra_01.umap` on disk | 1,105,561 bytes |
| First 5.8 load of the 4.26 kit | **silent** — 0 upconversion/redirect error lines (R-67 first-load evidence; draw cost still unmeasured) |
| Nav verifier | **expected fail**: 0/3721 grid points on saved navmesh; headless BUILDPATHS is a no-op under -nullrhi (R-82) |
| `layout_spawns.py`, playability audit | NOT RUN — both need the attended nav bake |

The navmesh bake is **attended-editor work** (R-82): open `L_Wandarra_01`, Build ▸ Build Paths,
save, then re-run the nav pass (verify) and the spawn layout. Until then no pathfinding number on
this map is real, and none is claimed.

## 7. Risks

| ID | Risk | Note |
|---|---|---|
| R-67 (existing) | 4.26 upconversion — first load now measured **silent**; texture/LOD/draw cost still unmeasured | remains OPEN until the map is inspected in a rendered editor |
| R-82 (existing) | headless nav bake consumes no geometry on this machine | applies; attended bake is the documented next step |
| **R-89** (new) | the ADR-016 look check **deferred, not passed**: bungalows, awnings, bus stop, playground and clothes lines read ordinary-suburban rather than specifically European, and the beech forest is placed as scattered township trees — but the check is an editor-eyeball act and no one has eyeballed it | before the map is shown or played beyond a bot smoke test, the look verdict gets recorded here and in ADR-016 |
| **R-90** (new) | vendor building Blueprints arrive at their authored pivot/footprint; the 1 m grid in the spec assumed 5 m wall modules, so actual extents may intersect roads, footpaths or fence lines | Session 086 measured all 11 building bounds and found 0 road-corridor overlaps. Footpath/fence clearance and the rendered look still need attended inspection; if something conflicts, move spec rows and rebuild, never nudge actors |

## 8. How to re-verify every number above

```bash
python Tools/Common/wandarra_spec.py 2>/dev/null || python -c "import sys; sys.path.insert(0,'Tools/Common'); import wandarra_spec"
ls -la Content/Maps/L_Wandarra_01.umap                       # 1,105,561 bytes after Session 086 rebuild
python -c "import json; r=json.load(open('Build/wandarra_level.json')); print(r['ok'], len(r['steps']), r['counts'])"
python -c "import json; r=json.load(open('Build/wandarra_nav.json')); print(r['nav_coverage'])"   # 0 pct until the bake
du -sh Content/MOUT_Civilian Content/RustyCarsFree Content/EuropeanBeech   # 2.1G / 69M / 7.0G
strings -n 8 Content/EuropeanBeech/Geometry/SimpleWind/SM_EuropeanBeech_Field_01.uasset | grep -m1 Release   # ++UE5+Release-5.1
```
