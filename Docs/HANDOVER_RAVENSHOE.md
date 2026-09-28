# Ravenshoe Crossing — handover

**For whoever launches and playtests this map.** Written 2026-09-28 by the agent that built it.
Everything below is measured and read back from the saved `.umap`, not assumed.

**How to use this document.** §1–§2 are the situation. §3 is what to run and in what order if
you rebuild anything. §4 is every asset involved, in use or not. §5 is the list of things that
fail *silently* on this build. §6–§7 are the current values and how to check them. §8 is the state
of the working tree. **§9 is a ready-to-paste prompt for the launching agent** — the fastest route
is to skip to the bottom and hand that over.

| | |
|---|---|
| Map | `/Game/Maps/L_Ravenshoe_01` |
| Design document | `Docs/MAPS_RAVENSHOE.md` (§3.1 metrics, §3.2 surfaces, §3.3 atmosphere, §3.4 pipeline order, §7.1 nav) |
| Rationale | ADR-027, **ADR-030** in `Docs/DECISION_LOG.md` |
| Asset rows | `M-008`, `M-008a`–`M-008n` in `Docs/ASSET_REGISTER.md` |
| Experience | `B_SS_ObjectiveAssault` (Objective Assault, sequential A→B) |
| Project root | `E:/SouthernSpear` · UE **5.8** · Blender 5.2.2 · Python 3.12 |

---

## 1. State in one paragraph

`/Game/Maps/L_Ravenshoe_01` is **complete and verified at 665 actors with 35/35 audit checks
passing**, 0 errors and 0 warnings across every build pass. It is built from an original blockout
(200 × 300 m gorge, 68 m wrought-iron lattice-girder road bridge, stone road-gate house), dressed
with 424 pack cover actors, 38 hand-placed props and 188 ground-cover actors, surfaced with 20
generated original PBR textures, lit and atmosphered, and wired to the shared Objective Assault
experience. **The one thing missing is the navigation bake**, and it is missing only because it
cannot be done without a display. Read §2 before launching.

Actor inventory, exactly as `audit_ravenshoe.py` counts it on the saved map:

| Labelled | Actors | What |
|---|---|---|
| `SS_Raven_Geo_*` | 3 | original structures — terrain, bridge, gate house |
| `SS_Raven_Cover_*` | 220 | pack cover dressing (from 68 layout cover markers) |
| `SS_Raven_Dress_*` | 204 | extra pack dressing |
| `SS_Raven_Ground_*` | 188 | Namaqualand ground cover |
| `SS_Raven_Light_*` | 5 | sun, sky atmosphere, skylight, fog, post process |
| `SS_Raven_NavBounds` | 1 | `NavMeshBoundsVolume`, scale `[115, 165, 45]` |
| **Subtotal, owned** | **621** | |
| `Dress_Prop_*` | 38 | the Fab prop layer (§4.3) |
| `SS_MAP_Ravenshoe_*` | 5 | 2 objectives + 2 deployments + `SS_ObjectiveAssault_Director` |
| `RecastNavMesh-Default` | 1 | the navmesh actor itself |
| **Subtotal, unprefixed** | **44** | |
| **Total** | **665** | |

The experience (`B_SS_ObjectiveAssault`) is bound as a **world setting**, not an actor, so it does
not appear in the count.

---

## 2. The one blocker: navigation is not baked

Verified headlessly by `Tools/Unreal/build_ravenshoe_nav.py` in verify mode, against the saved map:

```json
{ "ok": false, "mode": "verify", "nav_baked": false,
  "errors": ["not every objective is reachable from every deployment; see routes"],
  "checks":  { "navmesh_exists": false },
  "routes":  [ {"from": "SS_MAP_Ravenshoe_ObjA_Span",        "to": "…DeployAlpha", "reachable_both_ways": false},
               {"from": "SS_MAP_Ravenshoe_ObjA_Span",        "to": "…DeployBravo", "reachable_both_ways": false},
               {"from": "SS_MAP_Ravenshoe_ObjB_GravelGate",  "to": "…DeployAlpha", "reachable_both_ways": false},
               {"from": "SS_MAP_Ravenshoe_ObjB_GravelGate",  "to": "…DeployBravo", "reachable_both_ways": false} ],
  "nav_on_deck": null, "nav_in_creek_bed": null, "nav_projection_at_obj_a": null }
```

In words: **0 / 4 routes, deck not navigable, creek bed not navigable.** The objectives sit at
`[0, 0, 1415]` (mid-span) and `[0, -6200, 1614]` (gravel gate); deployments at `[0, ±13000, 2200]`.
Without a navmesh an AI cannot move at all, and a match will not play.

**Everything the bake needs is already correct** — this is not a layout problem:

- one `RecastNavMesh` present ✔
- one `NavMeshBoundsVolume` present, scale `[115, 165, 45]` cm, covering the 200 × 300 m map ✔
- the map is saved, so the bounds volume registers correctly on load ✔

Only the build itself is missing.

### Why you have to do it by hand

`BUILDPATHS` is a **silent no-op without a real rendering device**. It does not crash and it does
not warn — it just leaves a navmesh covering nothing. Both headless workarounds were tried, and
both fail on this machine:

| Attempt | Result |
|---|---|
| `-nullrhi` | no RHI, build skipped |
| `-RenderOffscreen` | still logs `rhiname="Null"` — falls back to Null RHI — then crashes on exit |

`Tools/Unreal/redgum_nav_build.py` documents the same constraint for Red Gum. A real RHI needs a
display or a working offscreen D3D device, neither of which a commandlet gets here.

### How to do it

1. Open the editor with `/Game/Maps/L_Ravenshoe_01` loaded. **Do not re-run any of the build passes
   first** — `import_ravenshoe.py` re-spawns the geometry actors and strips the per-instance
   material overrides, which silently reverts the bridge to flat colour (see §5.1).
2. **Build ▸ Build Paths.** Once is enough; the script issues it twice only because commandlet
   registration needed it.
3. Save the map.
4. Re-run the verifier and confirm it is fixed:

```bash
cd /e/SouthernSpear
MSYS_NO_PATHCONV=1 "/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
  "E:/SouthernSpear/SouthernSpear.uproject" -run=pythonscript \
  -script="E:/SouthernSpear/Tools/Unreal/build_ravenshoe_nav.py" \
  -nullrhi -unattended -nosplash -nop4

python -c "import json;d=json.load(open('Build/ravenshoe_nav_report.json'));\
print(d['nav_baked'], sum(1 for r in d['routes'] if r['reachable_both_ways']),'/',len(d['routes']))"
```

It must print `True 4 / 4`. **If it still reads `False 0 / 4`, do not ship the map** — agents
cannot path and a match will not run.

---

## 3. Pipeline and run order

**Order is load-bearing, not cosmetic.** §5.1 explains why the last two Unreal passes must come in
this sequence.

```
Tools/Blender/ravenshoe_blockout.py        geometry + spec -> FBX, .blend, layout CSV
Tools/Blender/verify_ravenshoe.py          53 checks (Blender), or spec-only in CI
Tools/Textures/make_ravenshoe_surfaces.py   20 PBR sets + the tiling wrap check

  --- Unreal, in this order ---
Tools/Unreal/import_ravenshoe.py
Tools/Unreal/dress_ravenshoe_props.py
Tools/Unreal/setup_ravenshoe_surfaces.py      <-- must be after the import
Tools/Unreal/dress_ravenshoe_groundcover.py
Tools/Unreal/light_ravenshoe.py
Tools/Unreal/wire_ravenshoe_experience.py
Tools/Unreal/build_ravenshoe_nav.py           verify headless / build needs an editor
Tools/Unreal/audit_ravenshoe.py               35 checks, re-opens the saved map
Tools/Unreal/audit_ravenshoe_props.py         material orphans
```

All Unreal passes are idempotent and were left with **zero errors and zero warnings**.

| Pass | Result as of this handover |
|---|---|
| `make_ravenshoe_surfaces.py` | 4 sets × 5 maps (Gravel, RustIron, PaintedSteel, Granite), 1024², seam check **passes** (wrap step vs p99 of interior step, tol 1.0) |
| `ravenshoe_blockout.py` | bridge 1266 faces, 4 material slots (Iron / Deck / **Road** / Stone) |
| `verify_ravenshoe.py` | **53/53** (was 41) + ray-cast `verify_bridge_metrics()` probes, metric table printed every run |
| `import_ravenshoe.py` | 3 meshes imported, `CTF_USE_DEFAULT`; idempotent at 468 actors after the purge fix, 8 pack groups, 0 missing assets |
| `dress_ravenshoe_props.py` | **38** props placed (was 35): added `OldBarn` on the south ridge + 3-vehicle `Roadblock_0..2` at the south lip |
| `setup_ravenshoe_surfaces.py` | 20 textures imported, 4 `MI_SS_Raven_{Road,Iron,Deck,Stone}` built, assigned **bridge 4/4, gatehouse 1/1** |
| `dress_ravenshoe_groundcover.py` | **188** Namaqualand succulents in 11 clusters, collision off |
| `light_ravenshoe.py` | Sun / SkyAtmosphere / SkyLight / Fog / PostProcess, idempotent, 0 warnings |
| `wire_ravenshoe_experience.py` | 2 objectives ("The Span" seq 0, "Gravel Gate" seq 1), 1 director, experience bound; verified 2/1/2 |
| `build_ravenshoe_nav.py` | verify mode works headless; **build blocked on a display** (§2) |
| `audit_ravenshoe.py` | 35/35, including the new `audit_surfaces()` on the saved map |

---

## 4. Assets

### 4.1 Generated and authored in-project (Class F — original, no third-party dependency)

| Asset | Path | Notes |
|---|---|---|
| Gorge heightfield + road corridor + both traverse ramps | `Content/Art/Blockout/SS_MAP_Ravenshoe_01.fbx`, `…_HI.blend` (LFS), `…_Layout.csv` | terrain 200 × 300 m, 15,000 faces, relief −18…+28 m; 74-row layout CSV of which 68 are cover markers; ramps 133 m @ 17.6° east, 142 m @ 16.2° west |
| Iron lattice-girder road bridge | `SS_Raven_Bridge.fbx` → `…/Meshes/SS_Raven_Bridge` | 68 m span, 20 bays of 3.4 m, 21 uprights/side, 7.5 m deck, 1266 faces, 10 lamp standards. **Modelled because no bridge mesh exists in the project or in any installed pack** (430-hit keyword sweep returned only rock, stone *materials* and audio) |
| Stone road-gate house | `SS_Raven_Gatehouse.fbx` → `…/Meshes/SS_Raven_Gatehouse` | granite rubble, 9.6 × 6.8 × 6.0 m, 4.6 m eaves, 1.2 m parapet, 3.4 × 3.6 m arched road passage, 17-stone segmental arch, 450 faces |
| 20 × 1024² PBR surfaces | `…/Surfaces/T_SS_Raven_{Gravel,RustIron,PaintedSteel,Granite}_{BC,N,R,AO,M}.png` | sealed gravel road, rusted ironwork, painted steel, coursed granite rubble. Generated from noise — not sampled, traced or derived from any scanned or licensed texture |
| 4 surface material instances | `…/Materials/MI_SS_Raven_{Road,Iron,Deck,Stone}` | tiling derived from the blockout UVs: `cube_project(2.0)` ⇒ 1 uv unit = 2 m |
| 5 flat safety-net materials | `MI_SS_RavenFlat_{Iron,Stone,Deck,Road,Terrain}` | instances of `M_SS_ScanPBR` carrying a `Tint`; still the terrain's material |
| 6 prop material instances | `MI_SS_Raven_{Wreck,WreckJunk,FuelDrum,Metal,Timber,Canvas}` | authored, **not copies of the vendor material** |

**Surface tiling, as applied:** Road 2.0 m/tile (tiling 1.0) · Iron 1.5 m (1.33) · Deck 0.9 m (2.22) ·
Stone 1.2 m (1.67).

### 4.2 Pack assets referenced in place (Class A — never modified, L-0016 / L-0016b)

The gorge and approach dressing is **424 actors** in 8 groups, placed by `import_ravenshoe.py`
(`placed 424 of 432 removed` — 8 were duplicates of an already-placed marker):

| Group | Count | Source | Collision |
|---|---|---|---|
| `wall_rock` | 86 | `Scene_QuarrySlate` | on |
| `bed_rock` | 54 | `Scene_QuarrySlate` | on |
| `cover_rock` | 35 | `Scene_QuarrySlate` | on |
| `cover_bush` | 33 | `RuralAustralia` | **off** (ADR-022) |
| `trees` | 76 | `RuralAustralia` | **off** (ADR-022) |
| `logs` | 12 | `RuralAustralia` | **off** (ADR-022) |
| `fence_post` | 64 | `RuralAustralia` | **off** (ADR-022) |
| `fence_wire` | 64 | `RuralAustralia` | **off** (ADR-022) |
| **Total** | **424** | 175 rock + 249 vegetation/wire | |

| Pack | Other contribution | Collision |
|---|---|---|
| `Namaqualand` | **188** ground cover, 11 clusters — 4 Cheiridopsis succulent variants + 3 crystalline iceplant | **off** (ADR-022) |
| Fab listings (13 downloaded) | the 38 props in §4.3 | on |
| `Realistic Starter VFX Pack Vol 2` | 4 systems on the wreck — `P_Fire_Big`, `P_Fire_Small`, `P_Smoke_A`, `P_Embers_A` | n/a |

Ground-cover cluster centres (x, y metres, placed): `(-18,-8) 14` · `(16,6) 14` · `(0,20) 10` ·
`(-9,-60) 18` · `(10,-74) 16` · `(8,60) 16` · `(-11,76) 18` · `(44,104) 22` · `(-52,118) 22` ·
`(68,-108) 20` · `(-60,-96) 18`. Jitter 4–9 m.

**LICENCE NOTE — read before touching the tree.** `.gitignore` **deliberately** excludes the Fab
packs from git (`Content/RuralAustralia/` line 204, `Content/Scene_QuarrySlate/` line 220,
`Content/Namaqualand/` line 224, `Content/Realistic_Starter_VFX_Pack_Vol2/` line 218, and the rest of
the pack list at lines 195–224). The three packs this map leans on hold **1,552 uncommitted
`.uasset` files** — 431 `RuralAustralia`, 395 `Scene_QuarrySlate`, 726 `Namaqualand`. This is the
project convention, not a dangling dependency: anyone working on the project needs the Fab library
installed locally, and a clean clone of the repo is not expected to open the map.

### 4.3 The 38 hand-placed props

| Actor | Source mesh | Tris | Where |
|---|---|---|---|
| `Dress_Prop_WreckCar` | `SS_Raven_wreck_car` | 23,323 | burning wreck on the deck at OBJ A |
| `Dress_Prop_WreckJunk_Bed` | `SS_Raven_wreck_junk` | 11,999 | creek bed, second wreck |
| `Dress_Prop_Drum_Deck_0..6` (7) | `SS_Raven_fuel_drum` | 1,120 | along the deck parapet |
| `Dress_Prop_Drum_Gate_0..2` (3) | `SS_Raven_fuel_drum` | 1,120 | gravel gate |
| `Dress_Prop_Sandbag_N0..3`, `_S0..3` (8) | `SS_Raven_sandbag_stack` | 6,000 | cover, both approaches |
| `Dress_Prop_TrenchWall_0..3` (4) | `SS_Raven_trench_wall` | 6,000 | corrugated cover, both approaches |
| `Dress_Prop_Roadblock_0..2` (3) | `SS_Raven_wreck_junk` | 11,999 | 3-vehicle roadblock at the south lip, placed with deliberate gaps to leave a walkable line and a vehicle-width gap at the abutment |
| `Dress_Prop_Barn` | `SS_Raven_barn` | 1,338 | north ridge |
| `Dress_Prop_OldBarn` | `SS_Raven_old_barn` | 12,279 | south ridge |
| `Dress_Prop_Windmill` | `SS_Raven_windmill` | 3,676 | north ridge |
| `Dress_Prop_WaterTower` | `SS_Raven_water_tower` | 640 | road edge |
| `Dress_Prop_HandPump_0..2` (3) | `SS_Raven_hand_pump` | 4,278 | road edge |
| `Dress_Prop_{Fire_Engine,Fire_Cabin,Smoke_Column,Embers}` (4) | VFX pack | — | on the wreck, at the engine end and the cabin, spawned via the pack's own `Spawn_Particle` BP class |

All 10 imported meshes use `CTF_USE_DEFAULT` collision with generated simple collision.

### 4.4 ⚠ AI-flag disclosure (logged; producer has cleared it)

The wreck, windmill, fuel drum, sandbag stack and corrugated wall come from Fab listings flagged
**`isAiForbidden: true`**, or from folders with **no `metadata` at all** (unverified). This is
recorded in **L-0016c / ADR-029**. The producer has reviewed and accepted the residual risk. It is
disclosed here so the launching agent is not surprised if an Epic content-checker or marketplace
audit flags it. If it ever needs to go public, these are the five meshes to replace.

### 4.5 Available but deliberately unused

| Pack | Listings | Why not |
|---|---|---|
| `Light_Foliage` | 109 | Temperate forest (`Forest_A/B`). Wrong biome for Australian high country |
| `Nanite_Plants_Sample_Collection` | 119 | Acer, Ophiopogon, Abelia — ornamental Japanese/Chinese garden plants. Wrong biome **and** wrong culture (ADR-016) |
| `Modular_Rural_Cabin` | 582 | Listed `IN_USE` for shaded-slope conifers, but the cabin architecture is northern-hemisphere; an ADR-016 look problem for Australian maps. Check before placing a building from it |
| `AutomotiveBridgeScene` | 319 | Decals and materials only (asphalt, concrete, rust, corrugated) — **no bridge mesh**. Useful for surface reference |
| `Singapore_Canal` | — | Ruled out on look and culture (ADR-016). This is why the gate house is original geometry |

⚠️ **Nine installed pack folders are neither tracked nor gitignored** and so appear as `??` in
`git status` — a broad `git add` would commit several thousand vendor `.uasset` files:

```
Content/AnimStarterPack/        Content/AutomotiveBridgeScene/   Content/ConcreteFPPack/
Content/DeadBodies_Poses_nikoff/ Content/Light_Foliage/           Content/MSPresets/
Content/MWLandscapeAutoMaterial/ Content/Modular_Rural_Cabin/     Content/StoneWell/
```

Adding a `Content/<Pack>/` line for each (or a single `Content/*Pack*/` plus explicit exceptions
for the original art folders) would close the hole. Not done here because it is outside the Ravenshoe
scope and touches the other agent's working set.

**There is still no bridge mesh anywhere.** The truss is original geometry, modelled for exactly
this reason. Do not go looking for one to swap in.

### 4.6 Held Fab props, and the blocker to using them

From §4.9i of the asset register: red tractor, storage unit, chicken coop, crushed classic, old bath.
Two concrete reasons they are still held:

1. **Wrong format.** `prep_fab_props.py` takes FBX and none of them ship it — the storage unit is
   OBJ only, chicken coop and tractor are GLB only, crushed classic is an unextracted RAR.
2. **Look.** European/Baltian origin; the storage unit's own asset path is `Daugavpils_skuunis`.
   Needs an ADR-016 check for a high-country Australian gorge.

Onboarding them means extending `prep_fab_props.py` to import OBJ and GLB. The old barn from that
group **is** in use, on the south ridge.

---

## 5. Gotchas that will bite you

Every one of these cost real time and produced a **silent** wrong result — a pass reporting success
while writing nothing.

1. **`import_ravenshoe.py` must run before `setup_ravenshoe_surfaces.py`.** The import re-imports the
   bridge FBX with `replace_existing` and re-spawns the geometry actors, which strips the
   per-instance material overrides. Run them the other way and the bridge silently reverts to flat
   colours with the Road slot on `WorldGridMaterial`. `audit_ravenshoe.py`'s `audit_surfaces()` catches
   it on the **saved** map — that is how it was found.
2. **The import is idempotent only because it was fixed.** It used to purge just `SS_Raven_*` actors
   while objectives and deployments are labelled `SS_MAP_Ravenshoe_*`, so every re-run added another
   objective and another deployment. The audit read 2, then 4, then 6. If you add a prefix, purge it.
3. **Material writes are only real in one place.** On 5.8 every route to a `StaticMesh`'s own material
   slots is a no-op. Use `StaticMeshComponent.set_material(i, mat)` — the per-instance override —
   which persists and is what renders. The mesh asset's own slots read back `[None, None]` after a
   write, so checking there tells you nothing.
4. **Read every property back after setting it.** Four fog properties that look plausible do not exist
   on this build: `fog_height_offset`, `fog_height_density`, `fog_max_height`, `start_density`. The
   lighting pass now reads each value back and warns if it did not stick. The AO texture parameter is
   named `AO`, not `AmbientOcclusion`.
5. **`light_color` is not a `LinearColor` here.** It is a struct property and rejects `LinearColor`; a
   positional `unreal.Color` does not land in the right channels. The Ravenshoe sun is therefore left
   untinted and the atmosphere provides the warm cast. **Related bug, not fixed:**
   `Tools/Unreal/light_dryriver.py` sets `light_color` with a `LinearColor` inside a `try/except`, so
   the Dry River sun has been untinted white this whole time. It is that script's dependency, so it
   was left alone.
6. **The map has never been rendered.** Everything is measured and read back. The fog in particular is
   reasoned from the start-distance contract, not tuned by eye — expect to want it adjusted.
7. **`-nullrhi` cannot see StaticMeshActors.** Do not ray-cast for a surface height under a commandlet;
   use `ravenshoe_spec.ground_z(x, y)`.
8. **`get_editor_world()` returns a blank untitled level** unless `load_map()` ran first. Always load
   and verify actors exist before you touch them.
9. **The two layout CSVs do not share a column order.** Dry River is `name,x,y,z,kind`; Ravenshoe is
   `name,kind,x_m,y_m,…`. Sharing one parser would be a silent-corruption bug.
10. **`set_actor_location(loc, False, False)`** — 5.8 requires `sweep` positionally.
11. **`material_slot_name` is a `unreal.Name`, not a `str`.** Calling `.strip()` on it aborts the whole
    slot loop.
12. **`MaterialInstanceConstantFactoryNew` has no `initial_parent`.** Set
    `mi.set_editor_property("parent", ...)` after creating the instance.
13. **A runtime-added `ParticleSystemComponent` cannot persist.** The VFX on the wreck are spawned as
    instances of the pack's own `Spawn_Particle` Blueprint's generated class.

---

## 6. Current map settings worth knowing

| Thing | Value | Why |
|---|---|---|
| Fog | `start_distance` 140 m, density 0.055, max opacity 0.82, cutoff 600 m | leaves the 68 m span and both lips clear; fogs only the 200 m ridge-to-ridge shot, which is the sniper case |
| Fog height term | **off** (`fog_height_falloff` 0) | 46 m of relief is too little to stratify, and with no `fog_height_offset` on this build a non-zero falloff puts a 50 cm disc across the deck |
| Sun | pitch −54, yaw 38, intensity 9 | mid-morning, northern sky (southern hemisphere) |
| SkyLight | real-time capture, intensity 1.0 | |
| PostProcess | unbound, exposure 0.5–2.0 | |
| Objectives | "The Span" (seq 0, mid-span), "Gravel Gate" (seq 1) | 10 m capture radius |
| Deployments | Alpha `[0, 13000, 2200]`, Bravo `[0, -13000, 2200]` | 130 m from centre, both ends of the road corridor |

### Bridge metrics — the governing numbers, as ratios

| Metric | Value |
|---|---|
| Span | 68.0 m (20 bays × 3.4 m, 21 uprights/side) |
| Deck width / clear lane | 7.5 m / 6.8 m (clear lane ≥ 6 m) |
| Parapet | 1.05 m |
| Truss depth | 5.2 m |
| **Span : truss depth** | **1 : 13.1** (band for this class: 1:12–1:20) |
| Headroom | 5.03 m (≥ 4 m) |
| Bay | 3.4 m (band 2.5–4.0 m) |
| Lamps | 10 |
| Deck area | 510 m² |
| 20 m open-crossing rule | broken exactly once — by the span — mitigated by 21 uprights a side at 3.4 m |

---

## 7. Verification commands

```bash
cd /e/SouthernSpear

# Geometry + spec (spec-only mode runs in CI with no Blender)
python Tools/Blender/verify_ravenshoe.py
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup \
  --python Tools/Blender/ravenshoe_blockout.py \
  --python Tools/Blender/verify_ravenshoe.py          # 53/53

# Textures and the tiling wrap check
python Tools/Textures/make_ravenshoe_surfaces.py      # "seam check: all sets periodic"

# Map audit — re-opens the saved .umap, so it is the real check
MSYS_NO_PATHCONV=1 "/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
  "E:/SouthernSpear/SouthernSpear.uproject" -run=pythonscript \
  -script="E:/SouthernSpear/Tools/Unreal/audit_ravenshoe.py" \
  -nullrhi -unattended -nosplash -nop4                 # 35/35

# Nav state
MSYS_NO_PATHCONV=1 "/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
  "E:/SouthernSpear/SouthernSpear.uproject" -run=pythonscript \
  -script="E:/SouthernSpear/Tools/Unreal/build_ravenshoe_nav.py" \
  -nullrhi -unattended -nosplash -nop4
```

Reports land in `Build/`: `ravenshoe_audit_report.json`, `ravenshoe_nav_report.json`,
`ravenshoe_import_report.json`, `ravenshoe_dress_report.json`, `ravenshoe_surfaces.json`,
`ravenshoe_surfaces_setup.json`, `ravenshoe_groundcover.json`, `ravenshoe_lighting_report.json`,
`ravenshoe_experience_wiring.json`.

Preview renders (shape check, not look-dev): `Build/ravenshoe/raven_*.png`, six Workbench views,
generated by `Tools/Blender/ravenshoe_render.py`.

---

## 8. State of the working tree — read before you commit anything

**All Ravenshoe work is uncommitted on `main`.** HEAD has also moved since the last Ravenshoe commit
(`7cda16a4`, Session 045) — another agent has since landed Session 046 and two weapons commits.

**Current tree state: 79 modified, 50 untracked. The overwhelming majority of that is not
Ravenshoe.** Never stage broadly here. Concretely:

- `git add -A` is **forbidden** — it would sweep in ~84 other-agent files, including the Red Gum
  map, the weapons work, the MAF camo textures, and the nine un-gitignored vendor pack folders
  listed in §4.5.
- Two of my own docs are **shared diffs**: `Docs/ASSET_REGISTER.md` carries both my `M-008*` rows
  and another agent's M-001–M-005 rows; `Docs/CHANGELOG.md` is large and likely shared too. Both
  need `git add -p`, not a whole-file stage.
- `Content/Maps/L_RedGum_01.umap` is modified and is **not** mine.

The Ravenshoe paths, and only these:

**Content (24 modified + 11 new)**
```
Content/Art/Blockout/SS_MAP_Ravenshoe_01.fbx            Content/Art/Blockout/SS_MAP_Ravenshoe_01_HI.blend
Content/Art/Blockout/SS_Raven_Bridge.fbx                 Content/Art/Blockout/SS_Raven_Gatehouse.fbx
Content/Art/Environment/Ravenshoe/Meshes/                (3 .uasset)
Content/Art/Environment/Ravenshoe/Props/                 (10 .uasset)
Content/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_{Canvas,FuelDrum,Metal,Timber,Wreck,WreckJunk}.uasset
Content/Art/Environment/Ravenshoe/Materials/MI_SS_RavenFlat_{Deck,Iron,Road,Stone,Terrain}.uasset   (new)
Content/Art/Environment/Ravenshoe/Materials/MI_SS_Raven_{Deck,Iron,Road,Stone}.uasset               (new)
Content/Art/Environment/Ravenshoe/Materials/M_SS_Raven_Road.uasset                                  (new)
Content/Art/Environment/Ravenshoe/Surfaces/               (new directory, 20 textures)
Content/Maps/L_Ravenshoe_01.umap
```

**Tools (6 modified + 6 new)**
```
Tools/Common/ravenshoe_spec.py          Tools/Textures/make_ravenshoe_surfaces.py   (new)
Tools/Blender/ravenshoe_blockout.py     Tools/Unreal/setup_ravenshoe_surfaces.py   (new)
Tools/Blender/verify_ravenshoe.py       Tools/Unreal/dress_ravenshoe_groundcover.py (new)
Tools/Unreal/audit_ravenshoe.py          Tools/Unreal/light_ravenshoe.py            (new)
Tools/Unreal/dress_ravenshoe_props.py    Tools/Unreal/wire_ravenshoe_experience.py  (new)
Tools/Unreal/import_ravenshoe.py         Tools/Unreal/build_ravenshoe_nav.py        (new)
Tools/Unreal/probe_fog_props.py          (new — read-only probe that found the missing fog properties)
```

**Docs (4)**
```
Docs/MAPS_RAVENSHOE.md   Docs/DECISION_LOG.md (ADR-030)   Docs/CHANGELOG.md   Docs/HANDOVER_RAVENSHOE.md (new)
```

⚠️ **`Docs/ASSET_REGISTER.md` is mixed.** It carries my `M-008*` rows *and* another agent's
M-001–M-005 rows in the same working-tree diff. It needs a surgical partial stage (`git add -p`)
if it is committed — do not stage the whole file.

⚠️ Two register rows are **stale** against the current build and should be corrected on the next
touch: `M-008` still reads "467 actors, 32/32 audit checks" and `M-008j` still reads "35 actors
placed, 35/35". The map is now 665 actors at 35/35 with 38 props placed. `M-008a` says "72 layout
rows"; the CSV has 74 (68 of them cover markers). `M-008m` should note the `Namaqualand` ground
cover row as a new `M-008o`, since the 188 succulents are not yet registered.

---

## 9. Prompt for the launching agent

Copy from here down. It is self-contained — the other agent does not need to have read anything
above.

---

> **Ravenshoe Crossing** (`/Game/Maps/L_Ravenshoe_01`, project `E:/SouthernSpear`, UE 5.8) is
> built and verified at **665 actors, 35/35 audit checks, 0 errors, 0 warnings**. It is an
> Objective Assault map: sequential A→B, 8 v 8, a 68 m wrought-iron lattice-girder bridge over a
> high-country gorge as the primary fight, creek bed as a second lane. Two objectives ("The Span"
> at mid-span, "Gravel Gate" at the south gate), two deployments 130 m out at each end.
>
> Full handover: **`Docs/HANDOVER_RAVENSHOE.md`**. Read §2 (the blocker) and §5 (silent-failure
> gotchas) before you change anything. Design brief: `Docs/MAPS_RAVENSHOE.md`.
>
> ## 1. Bake the navigation — this is the one blocker, and it needs an editor
>
> Open the editor with `/Game/Maps/L_Ravenshoe_01` loaded and press **Build ▸ Build Paths**, then
> save. The `RecastNavMesh` and the `NavMeshBoundsVolume` (scale `[115, 165, 45]`) are already in
> place, so this is a one-keystroke job. Right now `nav_baked: false`, **0 / 4** deployment↔objective
> routes, deck and creek bed not navigable — agents cannot path and a match will not run.
>
> **Do not re-run any of the build passes first.** `import_ravenshoe.py` re-spawns the geometry
> actors and strips their material overrides, which silently reverts the bridge to flat colour.
>
> It cannot be scripted: `BUILDPATHS` is a **silent no-op without a real rendering device** —
> `-nullrhi` has no RHI, and `-RenderOffscreen` still logs `rhiname="Null"` and crashes on exit.
> Details and the full JSON in `Docs/HANDOVER_RAVENSHOE.md` §2.
>
> Then confirm it:
> ```bash
> cd /e/SouthernSpear
> MSYS_NO_PATHCONV=1 "/e/Unreal/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
>   "E:/SouthernSpear/SouthernSpear.uproject" -run=pythonscript \
>   -script="E:/SouthernSpear/Tools/Unreal/build_ravenshoe_nav.py" \
>   -nullrhi -unattended -nosplash -nop4
> python -c "import json;d=json.load(open('Build/ravenshoe_nav_report.json'));\
> print(d['nav_baked'], sum(1 for r in d['routes'] if r['reachable_both_ways']),'/',len(d['routes']))"
> ```
> It must print **`True 4 / 4`**. If it prints `False 0 / 4` the bake did not take — do not ship it.
>
> ## 2. Launch a match and tell me what you actually see
>
> **The map has never been rendered by anyone.** Everything about it is measured and read back
> from the saved `.umap`; nobody has laid eyes on it. Treat this as a first look, not a regression
> test. The three things I most want a second opinion on:
>
> - **The fog.** Rationalised, never seen. `start_distance` 140 m, density 0.055, max opacity 0.82,
>   height term deliberately off. The intent is that the 68 m span and both lips stay clear and only
>   the 200 m ridge-to-ridge sightline fogs. If the whole map looks hazy or the deck looks lost in
>   it, that is the fix I want.
> - **Does the deck read?** 7.5 m wide, 6.8 m clear lane, 3.4 m bays with 21 uprights a side. It
>   should read as a legible lattice-girder firefight, not a blur of iron. Surfaces are generated
>   gravel / rust iron / painted steel / granite at 1024², tiling 0.9–2.0 m per tile.
> - **Does the ground cover sit right?** 188 Namaqualand succulents in 11 clusters, collision off.
>   Believable density, or scattered?
>
> ## 3. Ground rules
>
> - **Assets.** Three pack sources carry the dressing — `RuralAustralia`, `Scene_QuarrySlate`,
>   `Namaqualand` — plus 13 Fab listings and the VFX pack, all referenced in place and never
>   modified. Breakdown: 424 cover/dressing actors (86 wall rock, 54 bed rock, 35 cover rock, 33
>   bush, 76 trees, 12 logs, 64 fence posts, 64 fence wire), 38 props, 188 succulents, 20 generated
>   PBR textures. **The packs are deliberately gitignored** — 1,552 uncommitted `.uasset` files
>   across those three — so a clean clone will not open the map until the Fab library is installed.
>   That is this project's convention, not a broken reference. Full inventory in handover §4.
>   There is **no bridge mesh anywhere** — the truss is original geometry; do not go looking for
>   one to swap in.
> - **One disclosed risk:** the wreck, windmill, fuel drum, sandbag stack and corrugated wall come
>   from Fab listings flagged `isAiForbidden: true` or with no metadata. Logged in L-0016c /
>   ADR-029 and already accepted. Those five are the ones to replace if this ever goes public.
> - **Do not commit, push or open a PR** unless I ask. If you do get asked, the tree is shared:
>   79 modified and 50 untracked paths, most of them another agent's. `git add -A` is forbidden —
>   it would also commit nine installed vendor pack folders that are missing from `.gitignore`
>   (`AnimStarterPack`, `AutomotiveBridgeScene`, `ConcreteFPPack`, `DeadBodies_Poses_nikoff`,
>   `Light_Foliage`, `MSPresets`, `MWLandscapeAutoMaterial`, `Modular_Rural_Cabin`, `StoneWell`).
>   `Docs/ASSET_REGISTER.md` is a mixed diff needing `git add -p`. Handover §8 has the exact
>   Ravenshoe-only path list.
> - **Silent-failure list.** `Docs/HANDOVER_RAVENSHOE.md` §5 has thirteen. The three that matter
>   most: material writes only take via `StaticMeshComponent.set_material(i, mat)`; read every
>   property back after setting it (four plausible fog properties do not exist on this build); and
>   `setup_ravenshoe_surfaces.py` must run *after* `import_ravenshoe.py`.
