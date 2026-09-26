# MAP DESIGN — Dry River (Vertical Slice Test Bed)

**Document ID:** `Docs/MAPS_DRYRIVER.md`
**Status:** Baseline — Phase 1 greybox
**Last updated:** 2026-09-26
**Authoring:** `Tools/Blender/dryriver_blockout.py` → FBX → Unreal

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army. Dry River is an invented location. Its layout is designed from gameplay requirements and does not reproduce any real training area, installation or operationally useful site.

---

## 1. Purpose

This is the **vertical slice test bed**: one playable map that proves two teams, contextual faction presentation, an objective sequence, the round lifecycle and a dedicated server. It is a **greybox**. It is not a final map, and it must never be mistaken for one.

Every dimension below is stated with the gameplay reason it exists. If a number has no justification, it is a guess, and guesses are what produce maps that feel arbitrary.

---

## 2. Design Brief

From `GAME_DESIGN_DOCUMENT.md` §4.7, Dry River is a **rural Australian training area** with:

- A dry creek bed
- Scrub
- Farm structures
- **Long sightlines and concealed approaches**

Those last two words are the whole design problem. Long sightlines and concealment pull in opposite directions: you cannot have both unless concealment is *placed deliberately* along the sightlines rather than scattered randomly. That is the central tactic this map teaches — **use cover to break a long lane, then cross it.**

---

## 3. Scale and Budgets

| Property | Value | Justification |
|---|---|---|
| Playable area | **260 m × 180 m** | Small enough to polish and to test at low player counts; large enough for real rotation decisions |
| Team size (vertical slice) | 4 v 4 | Keeps a round under 6 minutes so the full lifecycle can be tested repeatedly |
| Max players per server | 8 | Matches the 4-client acceptance test |
| Vertical relief | 14 m | Enough for elevation to matter; not enough to break sightlines entirely |
| Cover objects | ~120 | Target: no player crosses 20 m of open ground without passing cover |
| Navigation | Full NavMesh, no dynamic nav | A greybox must be navigable by construction, not by runtime carving |

**Deliberately small.** The brief says build smaller, polished maps first, and use World Partition only where scale justifies it. A 260 × 180 m blockout does not need it.

---

## 4. Layout

North is +Y. Teams deploy at opposite short edges.

```
        y = +90  ──────────────────────────────────────────────
                 │            [ B ] ridge + scrub            │
                 │         ~~~~~~~  ~~~~~~~~~~~~~              │
   OBJ B ────────┤   ▲B                ▓▲      ▲B             │
   (Farm)        │   (3)               (4)     (5)             │
                 │        ▄▄▄▄▄                             │
                 │   ▓▓▓▓ FARM  ▓▓▓▓        ┃ fence ┃         │
                 │        ▄▄▄▄▄                             │
                 │  ░░ scrub ░░         ═══ CREEK ═══        │
   OBJ A ────────┤   ▲A       ▲A              ▽                │
   (Water point) │  (1)       (2)          (dry bed)           │
                 │                                              │
   DEPLOY B ─────┤  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░          │
                 │                                              │
   DEPLOY A ─────┤  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒          │
        y = -90  ──────────────────────────────────────────────
              x = -130                                        x = +130
```

### 4.1 Objectives

| ID | Name | Location | Role |
|---|---|---|---|
| **OBJ A** | Water Point | (-15, 0) | First contact. A low ground-water pump station beside the creek. Sits on the map's Y centre line so **both teams reach it at an equal distance**. |
| **OBJ B** | Farmstead | (+40, +52) | Second objective. The farm sheds and stock pens. Held longer; the round's pivot. |

Two objectives, taken **sequentially**: both teams contest OBJ A, then both move to OBJ B (§6.1). That is enough to prove objective state replication, capture logic, and a round that can be **won, lost and restarted** — the Phase 1 acceptance criteria. Sequential order also makes the round symmetric by construction.

### 4.2 Deployment zones

| Team | Position | Justification |
|---|---|---|
| **Alpha** | y = -85, full width | Behind the southern scrub line |
| **Bravo** | y = +85, full width | Behind the northern ridge |

Symmetric on purpose. Objective mode is symmetric (GDD §3.1), so the spawns must be too — an asymmetric map would quietly reintroduce the imbalance the faction system exists to prevent.

### 4.3 The creek bed

Runs roughly east–west at y ≈ 0, meandering ±8 m. Cut depth 2.5 m, width 6–11 m.

It is the map's only hard-ish cover that cuts *across* the long north–south sightlines. A player in the bed is concealed from a ridge position but **cannot shoot out** — they must climb the bank to engage. That is a deliberate tactical trade, and it is the first thing to test once the map is playable.

### 4.4 Farmstead

Three structures at (+40, +52): a machinery shed, a small residence, and a set of stock pens.

- **Shed** — 18 × 10 × 6 m, open on two sides. Two hard corners, soft in between.
- **Residence** — 12 × 9 × 4 m, fully enclosed with two doorways. The only fully enclosed space on the map, so it is deliberately a strong position that is easy to over-run.
- **Stock pens** — post-and-rail, chest-high. Soft cover that blocks movement, not fire.

### 4.5 Fencing and scattered cover

Post-and-rail fence runs north–south at x = +10, giving partial concealment and dividing the eastern third. A scatter of ~40 boulders, 20 dead trees and 30 scrub clusters breaks up the remaining long lanes.

---

## 5. Cover Rules

The cover rules are a design contract, not a suggestion.

| Rule | Value | Why |
|---|---|---|
| Maximum open crossing | **20 m** | Beyond this, a moving player is a free kill. Cross the lane under 2 s of exposure. |
| Minimum engagement range | 5 m | Close quarters must be possible; the map is not a marksman park |
| Maximum sightline | 220 m | The full length of the map. Only achievable from the ridge, and only along a narrow arc. |
| Cover density | 1 object per 12 m of intended route | Enough to move cover-to-cover without feeling corralled |
| Hard : soft ratio | 1 : 3 | Hard cover is scarce so it is worth holding; soft cover is common so movement is possible |

---

## 6. Rotation Distances

**These are measured from the generated blockout, not estimated.** `Tools/Blender/verify_dryriver.py` recomputes them from the exported layout CSV and fails the check if the map drifts from this table.

| Route | Distance | Time (tactical jog ~3.5 m/s) | Notes |
|---|---|---|---|
| Alpha deploy → OBJ A | **86.3 m** | ~25 s | The contested opening |
| Bravo deploy → OBJ A | **86.3 m** | ~25 s | **Identical — the opening is fair** |
| OBJ A → OBJ B | **75.7 m** | ~22 s | The pivot of the round |
| Bravo deploy → OBJ B | **51.9 m** | ~15 s | Bravo's shorter route to the pivot |
| OBJ A → Bravo deploy (full rotation) | ~151 m | ~43 s | The out-of-play rotation |

### 6.1 Objective order — sequential, not parallel

The vertical slice uses **sequential objectives**: both teams contest OBJ A, then both move A → OBJ B.

This makes the round **symmetric by construction** — both teams begin the second leg from the same point, so no team gets a positional head start. The only fairness property that needs to hold is an equidistant opening, and §6 shows it does (86.3 m each).

**A note on Bravo's overlooking position.** Bravo's *direct* line from deployment to OBJ B is 51.9 m, against Alpha's 142.7 m. That is a genuine terrain asymmetry and it is recorded here rather than hidden. Under sequential order it is **not exploitable**, because neither team may skip OBJ A to take it. It is reported by the verifier as an informational figure, not asserted as a balance property.

**If a future layer switches this mode to parallel objectives, that asymmetry becomes decisive and must be rebalanced first** — by moving OBJ B south or pushing Bravo's deployment north, never by changing team capability (ADR-003, GDD §3.1).

---

## 7. Art Direction — Placeholder Only

Everything below is a **greybox** primitive. It must look unpolished, because a greybox that looks finished stops being treated as one.

| Element | Placeholder treatment |
|---|---|
| Terrain | Flat-shaded subdivided grid with baked height variation |
| Structures | Untextured box primitives |
| Rocks | Low-poly icospheres, randomly scaled and rotated |
| Trees | Cylinder trunk + cone canopy, no bark or foliage |
| Scrub | Flat planes, single-sided |
| Fence | Thin box rails + post instances |

**No final materials. No original multicam-style texture. No detail.** Those are Phase 6, and the release gate (CP-10) fails on any placeholder that survives.

---

## 8. Naming

Per `ASSET_NAMING_STANDARDS.md`, Dry River content is prefixed `SS_MAP`:

```
SS_MAP_DryRiver_Terrain
SS_MAP_DryRiver_ObjA_WaterPoint
SS_MAP_DryRiver_ObjB_Farmstead
SS_MAP_DryRiver_DeployAlpha
SS_MAP_DryRiver_DeployBravo
SS_MAP_DryRiver_Cover_Rocks
SS_MAP_DryRiver_Cover_Trees
SS_MAP_DryRiver_Cover_Scrub
SS_MAP_DryRiver_Farm_Shed
SS_MAP_DryRiver_Farm_Residence
SS_MAP_DryRiver_Farm_Pens
SS_MAP_DryRiver_Fence
```

Blender source: `SS_MAP_DryRiver_01_HI.blend` (+ `_LO` for the game mesh).

---

## 9. Verification Checklist

Automated via `Tools/Blender/verify_dryriver.py`, which reads the exported layout CSV. The check is part of CI; the map cannot drift from this spec without failing.

- [x] Playable area is 260 × 180 m
- [x] Both objectives present and inside the playable area
- [x] Both deployment zones on the centre line, symmetric, 170 m apart
- [x] **First objective exactly equidistant from both deployments** (86.3 m)
- [x] Rotation distances match §6 within tolerance
- [x] Bravo's overlooking direct line to OBJ B is measured and recorded (terrain property)
- [x] Every element carries an `SS_MAP_DryRiver_*` name
- [x] Blockout exports to FBX with transforms applied
- [x] NavMesh generates covering all walkable space — **verified, gate G1.1**
- [x] A traversable path exists between both deployments (170 m) — **verified, gate G1.1**
- [ ] Source `.blend` committed to LFS

---

## 11. Bringing This Map Into Unreal (gate G1.1)

The level is built by two headless editor passes, not by hand. Both are version-controlled, deterministic and CI-runnable.

### 11.1 Running it

Both passes need one command-line override, explained in §11.4:

```
-ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False
```

**Pass 1 — construct** (`Tools/Unreal/build_dryriver_level.py`): creates `L_DryRiver_01`, imports the FBX, sets collision, places the gameplay actors from the layout CSV, creates the nav bounds volume, saves.

```
Engine\Binaries\Win64\UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout \
  -ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False \
  -ExecutePythonScript=Tools\Unreal\build_dryriver_level.py
```

**Pass 2 — navigate** (`Tools/Unreal/build_dryriver_nav.py`): loads the saved map, runs the editor's blocking *Build Paths*, and verifies a path between the deployments.

```
Engine\Binaries\Win64\UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout \
  -ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False \
  -ExecutePythonScript=Tools\Unreal\build_dryriver_nav.py
```

### 11.2 The coordinate transform — read this before placing anything

**The layout CSV is in Blender space. Unreal mirrors Y.**

Blender is right-handed Z-up; Unreal is left-handed Z-up. The FBX export (`axis_forward="-Z", axis_up="Y"`) performs the handedness conversion, so:

```
Unreal_X =  Blender_X
Unreal_Y = -Blender_Y      <-- negated
Unreal_Z =  Blender_Z
```

This is a silent failure. Dry River is symmetric in Y, so using un-negated Y does not look obviously wrong — it simply **swaps the two deployments**, and every distance in §6 still holds because a mirror preserves distance. It was caught only by cross-checking the traced ground height against the CSV:

```
SS_MAP_DryRiver_DeployAlpha ground z=64.3cm  vs CSV  34.3cm  (delta 30.0cm)
SS_MAP_DryRiver_DeployBravo ground z=1332.0cm vs CSV 1302.0cm (delta 30.0cm)
```

The residual 30 cm on both is expected and correct: the Blender layout markers are 2 × 2 × 0.3 m boxes sitting on the terrain, so a downward trace lands on the box top, 0.30 m up. **Pass 2 asserts this delta stays under 150 cm and warns otherwise**, so a future transform regression fails loudly instead of quietly swapping teams.

### 11.3 Why it must be two passes, not one

Several engine behaviours make a single pass impossible, each found the hard way:

| Symptom | Cause |
|---|---|
| Nothing happens after the script returns | `-ExecutePythonScript` tears the world down as soon as the script returns, so a post-tick callback never gets a tick |
| `Navigation NOT building because navigation build is locked (flags: 0x20)` | `0x20` is `AsyncLoadLock` (`1 << 5`), held by `DoInitialSetup()` and released only on a later tick. Overridden on the command line rather than in project config, so the editor default is untouched for everyone else |
| `TotalNavBounds: IsValid=false` | `GatherNavigationBounds()` skips any volume failing `HasActorRegisteredAllComponents()`; a script-spawned brush never reaches that state. Loading the map in pass 2 does |
| Build succeeds in 0.00 s with zero tiles | The mesh asset was saved by the import task *before* collision was configured, so the `.uasset` on disk had no collision. Pass 1 now saves the asset explicitly after setting it |
| Nav data present but contributes nothing | Spawning a `RecastNavMesh` from script defers registration to a tick. Pass 2 lets the map load create it normally |

**No workaround here is a fake.** Every step uses the same code path a person uses in the editor: place the volume, then Build Paths.

### 11.4 Measured engine constants

Recorded because they are not documented and each was wrong on first assumption:

- Default `AVolume` brush half-extent is **100 cm**, so nav bounds half-width (cm) = world scale × 100.
- A script-spawned brush volume returns from save/load with its scale **multiplied by 4** (set 34 → reloaded 136), so the value written by pass 1 must be a quarter of the desired world scale.
- `BUILDPATHS` is the console form of the editor's blocking *Build Paths* (`UUnrealEdEngine::HandleBuildPathsCommand` → `FEditorBuildUtils::EditorBuild(..., BuildAIPaths)`). `REBUILDALL` is asynchronous and is the wrong tool for a one-shot script.

### 11.5 Verification

Pass 2 does not check that a navmesh actor exists — that is trivially true and was true while the navmesh covered nothing. It checks that **`find_path_to_location_synchronously` returns a non-empty point list between the two deployments**, 170 m apart across the whole map. An empty list means agents cannot cross it, whatever else the log says.

Confirmed result (gate G1.1):

| Check | Value |
|---|---|
| Nav bounds | Min (-13600, -9600, -1000) → Max (13600, 9600, 2600) cm |
| Tiles generated | 560 |
| Path points, DeployAlpha → DeployBravo | 2 |
| Map check | 0 errors, 0 warnings |
| Saved map size | 248 KB (8.5 KB empty) — navigation data is serialised |

Evidence: `Docs/evidence/G011_*`.

Note the 14 m of relief in §1 is *not* symmetric about the deployments, so OBJ B's approach distances in §6 were derived in Blender space and are unchanged by the mirror: Bravo remains 51.9 m from OBJ B against Alpha's 142.7 m. The map is mirrored, not altered, so the sequential OBJ A → OBJ B ordering that makes the round fair still holds.

---

## 12. Dressing

Dressing is the layer on top of the structural blockout: scrub, vehicle wrecks, crates, barrels, and fence runs. The blockout is the playable shape; dressing is what makes a lane a lane.

**The placement CSVs are the source of truth. Moving a fence or deleting a wreck is a one-line diff that needs no editor.**

| File | Holds |
|---|---|
| `Content/Art/Blockout/SS_MAP_DryRiver_02_Dressing.csv` | point dressing: `name,type,x,y,z,rot_y,scale` |
| `Content/Art/Blockout/SS_MAP_DryRiver_02_Fences.csv` | fence runs: `name,x1,y1,x2,y2,post_spacing` |

A fence is a *line*, not a set of objects, so a run is six numbers. Posts and both rails are generated from it, which means changing a boundary fence into a tight paddock is one CSV edit rather than a rebuild.

### 12.1 The pipeline

```
construct  ->  dress  ->  navigate
```

Dressing runs **before** navigation, not after. Placed afterwards, the fences and wrecks would be invisible to the NavMesh and agents would walk through them — a map that looks dressed and plays wrong, which is worse than one that is plainly undressed.

Inside the dressing pass, fences are placed **before** point dressing. Every placement snaps its height with a downward ray, and once crates and wrecks exist that ray hits *them* rather than the ground, leaving a fence post standing on a barrel. `Tools/verify_dressing.py` additionally keeps solid dressing 1.5 m clear of fence lines, so the data cannot create the situation in the first place.

Regenerating the meshes and the initial layout:

```
blender -b --factory-startup --python Tools/Blender/dryriver_dressing.py
blender -b --factory-startup --python Tools/Blender/dryriver_dressing.py -- --force
```

**Existing CSVs are never overwritten** without `--force`. A re-run regenerates the mesh library and leaves hand-placed dressing alone.

### 12.2 Validation without an editor

`python Tools/verify_dressing.py` — **19/19 checks, no Blender, no editor, seconds not minutes.** It is in CI, and it is the check that matters most, because it runs before anything is built:

- schema and headers, known types, name conventions, unique names, sane scales
- everything inside the playable area, and clear of every protected zone by a per-type clearance (a wreck is a sight-line breaker and needs far more room than scrub)
- no two solid dressing items intersecting; scrub may touch
- recorded `z` agreeing with the terrain
- fence runs within length limits, endpoints inside the map, clearing every protected zone
- **no fence bisecting the deployment line** — the one fence fault that makes a round unplayable
- solid dressing clear of fence lines

It has already earned its keep. It rejected two hand-placed wrecks sitting inside a deployment zone, because the generator's hand-placement path originally bypassed the clearance check that scattered dressing goes through. Hand placement overrides *where*, never *whether*.

### 12.3 Placement, and one unit trap

The level pass re-snaps every item to the terrain with a ray trace, so the CSV's `z` column is advisory: move a fence in a text editor and it re-sits itself on the ground rather than hovering or sinking.

**`spawn_actor_from_class` takes centimetres.** An early version divided by 100 on the way in, which placed all 290 dressing actors 100× too close to the world origin — a 1.3 m knot at (0,0). Every ray at the real coordinates hit open ground, and the map looked correct in the data file and bare in the engine. Every coordinate in the dressing pass is now centimetres end to end; metres appear only where a CSV is read.

Scrub is deliberately `NoCollision`. It conceals without obstructing; colliding scrub would carve holes in the NavMesh and make the map feel sticky to cross.

### 12.4 Resolved (Session 007): dressing collision after save and reload

**R-10 is closed.** Collision did survive reload. The failure was caused by (1) the nav script's
trace wrapper reading every hit as a miss (UE 5.8 Python returns a bare `HitResult` on a hit,
`None` on a miss), (2) a zero-length "vertical" ray, and (3) a genuine placement bug:
`unreal.Rotator` takes positional arguments as **(roll, pitch, yaw)**, so `Rotator(0, yaw, 0)`
pitched every rotated post, rail and wreck onto its side. Always construct rotators with keyword
arguments. After the fix: 3/3 sampled actors, 7/7 fence runs solid after reload
(`Docs/evidence/R10_dryriver_nav_report.json`). The analysis below is kept as the historical record.


**Stated plainly because it is not yet fixed. Tracked as R-10.**

| Moment | Result |
|---|---|
| Immediately after placement | **5/5 solid dressing types** (fence post, rail, wreck, crate, barrel), verified by ray |
| After the map is saved and reopened | **0/3** sampled actors collide; **0/7** fence runs block |

What is *not* the cause, each measured rather than assumed:

- not the placement — the actors are at exactly the CSV coordinates (a PaddockEast post reads 78.0, −34.0 m, which is what the CSV says)
- not the collision profile — `BlockAll` and `QUERY_AND_PHYSICS` both survive the round trip
- not the asset — FBX and `.uasset` sizes are healthy, geometry is present
- not the collision *type* — **now properly tested, not merely assumed.** The earlier “tried complex-as-simple, it failed too” note was not trustworthy: it went through the silent no-op described below, so the flag never actually changed and the experiment proved nothing. With the write fixed, `CTF_USE_COMPLEX_AS_SIMPLE` was applied and verified by read-back (`<CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE: 3>`), and R-10 reproduced identically: 0/3 actors, 0/7 fence runs. The flag is therefore eliminated as a cause by measurement
- not a stale import — reproduced after deleting all six dressing assets and re-importing them cleanly
- not the assets as saved — `Tools/Unreal/probe_collision_flag.py` reopens the project in a **fresh** editor with no import in play and reads every dressing `BodySetup` back off disk. All six are at `CTF_USE_DEFAULT` and each carries exactly one `convex_elems` entry, so the simple collision the map depends on really is present in the `.uasset` files. This exonerates the whole asset side, not merely the flag
- **and not the map** — the blockout mesh in the same map, in the same session, with the same profile, still collides correctly after reload

So the cause is narrower than any of those: collision on *script-spawned dressing components* is not being rebuilt when the map is reopened, while a component whose asset was imported in the same session as the map's original build is. The engine-level mechanism has not been isolated, and further blind iteration is not a good use of the time available.

#### The silent no-op found while investigating this

Probing the collision flag turned up a genuine defect in the dress pass, now fixed. The pass asked for `unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_SIMPLE`, and **no such enum member exists** — introspecting the live enum on 5.8.3 yields only `CTF_USE_DEFAULT`, `CTF_USE_COMPLEX_AS_SIMPLE`, `CTF_USE_SIMPLE_AND_COMPLEX` and `CTF_USE_SIMPLE_AS_COMPLEX`. The `AttributeError` was caught by a broad `except` and downgraded to a warning, so the intended write never happened on any of the six meshes while the run still reported `ok`. The dress report was carrying six such warnings and they were read as benign.

It was benign *in effect*, which is why R-10 outlived it: the importer had already left every mesh at `CTF_USE_DEFAULT`, and that is the value the code meant to set. But the code's stated purpose — making collision explicit — was not happening, and a pass whose job is to guarantee collision could not report a collision failure.

The same block also reported `body_agg_geom` via `str(KAggregateGeom)`, which is an opaque pointer whether or not the struct holds anything, so the one field meant to distinguish "this asset has no collision" from "this asset is fine" could never distinguish them. It now counts the element arrays, and it also no longer lists `capsule_elems` or `geom_elems`, which are not properties of `KAggregateGeom` on this engine and raised a property error on every run.

The dress report went from **6 warnings to 0**, and two conditions that were previously silent no-ops are now hard failures: a trace flag that does not read back as requested, and a mesh with zero simple-collision elements.

The fix paid for itself immediately. Because the write now works, the collision trace flag became a variable that could actually be varied — and varying it, the one experiment the project had recorded as “already ruled out” without having really run it, produced `<CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE: 3>` on every mesh and **still** 0/3 after reload. A hypothesis that was quietly crossed off the list on the strength of a call that never executed is now genuinely closed. The flag is not R-10's cause.

`CTF_USE_DEFAULT` is what ships: 290 small meshes instanced across the map, each carrying one verified convex hull, is the case per-asset simple collision exists for. Both values now write, read back and are asserted, so the decision is one constant edit away if a future experiment needs the other.

**What R-10 now is, precisely.** Every observable is correct after reload: the actors exist at the right coordinates, `collision_profile` is `BlockAll`, `collision_enabled` is `QUERY_AND_PHYSICS`, `can_ever_affect_navigation` is `True`, the asset is at `CTF_USE_DEFAULT` with one `convex_elems` entry, and the trace flag is not the variable. Yet a ray cast at the same actor that was solid at placement returns `hit=False by=None`. The blockout in the same map, with the same profile and the same save path, does collide. The remaining live difference is **which session last touched the asset**: the blockout was imported in the construct session and carried forward unchanged, whereas every dressing mesh is deleted and re-imported by the dress pass and then saved in that same session. That is the next thing to vary, and it is a one-line change — stop deleting and re-importing the dressing assets, keep them, and re-run.

The nav pass therefore **reports this rather than hiding it**: the two `*_after_reload` steps appear in the report as failures, `report["dressing_collision_persists"]` is `false`, and a `WARN` explains it. They deliberately do **not** gate `report["ok"]`, because CI would then be permanently red for a reason we cannot yet fix, and because the data itself is already proven correct by §12.2. Gating them would be honest but useless; passing them silently would be a lie.

**Practical consequence: Dry River is currently traversable but its fences are not yet load-bearing cover, and navigation does not yet include them.** Treat the fencing as art direction until R-10 is closed. Everything else about the pass — data-driven placement, terrain snapping, collision at placement, map-check cleanliness, path verification — is verified and working.

---

## 9a. Objective Assault wiring (Session 008, ADR-018)

Run after the level and dressing passes, before navigation:

```
Engine\Binaries\Win64\UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash -nosound -stdout ^
  -ExecutePythonScript=Tools\Unreal\setup_objective_assault.py
```

It places one `SSObjectiveActor` per Objective row of the layout CSV (OBJ A Water Point = sequence 0,
OBJ B Farmstead = sequence 1, 10 m capture radius), one `SSObjectiveAssaultDirector`, and sets the map's
`DefaultGameplayExperience` to `B_SS_ObjectiveAssault`. Verified in a `-game` run: the experience loads
from WorldSettings and round 1 reaches InProgress with OBJ A active
(`Docs/evidence/G040_dryriver_objective_assault_game_keylines.txt`).

**Player starts fixed in the same session.** The level script had placed both deployments in metres
as if they were centimetres (both within 2 m of the centre) and pitched them 180°. They are now at
y = ±85 m, facing the map centre.

## 9b. Lighting (Session 013)

`Tools/Unreal/light_dryriver.py`, run after dressing and before Objective Assault setup, places a movable
daylight rig labelled `SS_Light_*`: sun (pitch -52°, yaw 35°, warm), sky atmosphere, real-time sky light,
height fog and an unbound post-process volume (exposure 0.5–2.0). Before it, the map had no lights and
rendered black. Evidence: `Docs/evidence/G051_hud_lit_dryriver.png`.

## 10. What This Map Does Not Do

Stated plainly so it is never over-claimed:

- It does **not** have final art, materials, lighting or audio.
- It does **not** have multiple layers. Day and low-light variants come in Phase 4; the vertical slice ships one.
- It does **not** have vehicles, destructibles, or dynamic cover.
- It does **not** represent a real place, and its layout is not derived from any real site.
