# MAP DESIGN — Red Gum Station

**Status:** Documented, **not** signed off. Red Gum is the first playable map (ADR-022). In Session 029 its
objectives were re-laid for fairness and its deployments pulled in. It has **not produced a capture** in a
three-minute bot round (§6).

Companion documents: `MAPS_DRYRIVER.md` (the standard), `MAPS_SALTBUSH.md`, `MAPS_SELATCANAL.md`.

---

## 1. Purpose

Red Gum is the **large outback station** map: a 1 km landscape with open paddocks, gum-tree lines, fences and
a homestead. It tests the long approach and the open ground between cover that the smaller maps cannot.

## 1a. The station, the dressing and the enlarged play space (2026-09-28)

Three passes, each idempotent and each owning its actors by label prefix, so a rerun of one cannot delete
another's work. The map grew from 383 actors to 1,530.

| Pass | Script | Owns | Result |
|---|---|---|---|
| Homestead | `Tools/Blender/redgum_homestead.py` → `Tools/Unreal/import_redgum_homestead.py` | `SS_RedGum_Homestead_*` | 7 structures at objective B |
| Rural dressing | `Tools/Unreal/expand_redgum.py` | `SS_RedGum_Dress_v1_*` | 1,140 actors |
| Nav volume | `expand_redgum.py` | `SS_MAP_RedGum_NavBounds` | 720 × 600 × 200 m |

**The homestead is original work, class F.** The Rural Australia pack has trees, logs, rocks, fences and
signs but no building mesh, and the only other installed packs are the wrong continent or the wrong culture.
So the station is modelled by us and carries no third-party dependency (L-0011, ADR-013, ADR-021).

| Structure | Footprint | Height | Role |
|---|---|---|---|
| Farmhouse | 12.7 × 13.5 m (incl. verandah) | 5.8 m | centre objective hard cover, 2.6 m verandah at 1.0 m |
| Shearing shed | 18.2 × 13.1 m | 6.3 m | tall cover, open front with two bays |
| Stock pens | 18.1 × 14.4 m | 1.35 m | soft cover, rails at 0.55 m and 1.05 m (the Dry River heights) |
| Water tank | 3.1 × 3.1 m | 5.2 m | landmark visible over the tree lines from both deployments |
| Windmill | 3.1 × 2.6 m | 11.5 m | silhouette only |
| Stockman's hut ×2 | 3.7 × 3.1 m | 3.9 m | one per paddock objective, so A and C are not fought around a tree |

Placed by **finding objective B by label**, not by hard-coded coordinates, so re-running
`layout_objectives.py` moves the station with it instead of leaving it stranded in open paddock.

**Verified, not assumed** (`Build/redgum_homestead_report.json`): all 7 placed, the 5 solid structures each
return 5 of 5 trace probes, and every base sits within 0.12 m of the ground measured outside its footprint.

**Collision is per structure, deliberately.** The farmhouse, shearing shed, water tank and both huts are
solid and are in the navmesh. The stock pens and the windmill carry **no collision**: a one-piece convex
hull around the joined pen mesh would be a solid 18 × 13 m block — an invisible wall in the middle of the
yard with the rails nowhere near its surface. Per-rail colliders are the correct fix and are a later pass.

**Dressing, 1,140 actors:** 352 trees, 124 bushes, 56 logs, 30 rocks, 28 ridge segments, 550 fence parts.
The added lines are the point: the original dressing stopped at y = ±270 m, which left the third of the map
that the widened nav volume made playable as bare open ground. The flank lines at y = 0 also break the
360 m deployment-to-homestead sightline down the middle. Every placement keeps 2.5 m clear of the station
structures, read from their real bounds rather than hard-coded; the nearest dressing to the farmhouse is
53.9 m away, which is the yard reading as a yard.

### What is NOT done, and one measurement that invalidates older numbers

- **The navigation is not baked.** The nav volume was widened to 720 × 600 × 200 m, but `BUILDPATHS` in a
  `-nullrhi` commandlet is **not** the harmless no-op the old pipeline assumed: on this map it takes the
  commandlet down with an access violation inside UnrealEd, seconds in, before any report is written. It
  is now opt-in behind `SS_BUILDPATHS=1` (`Tools/Unreal/redgum_crash_probe.py` isolates it). Open
  `/Game/Maps/L_RedGum_01` in the editor, **Build ▸ Build Paths**, then run
  `Tools/Unreal/redgum_nav_build.py` to verify the routes. Until that is done the map is tactically
  720 × 600 m and mechanically not navigable at all — the audit found **0 of 3,721 sampled cells on the
  navmesh**. Do not run `build_redgum_nav.py` until the bake exists; it relocates objectives and
  deployments.
- **Ray traces in a commandlet cannot see static meshes, so every cover and sightline number this project
  has produced for this map is invalid.** `SystemLibrary.line_trace_single` hits the Landscape and
  essentially nothing else: 526 actors spawned by today's passes and 34 of 36 actors that were already in
  the `.umap` all miss, including meshes that store real collision data
  (`Build/redgum_collision_capability.json`). The playability audit's "2 hard / 0 soft cover", "69% of
  ground with nothing within 30 m", "p50 sightline 350 m" and the equivalent historical figures describe a
  map with its geometry deleted, not this one. They are not evidence that the map is a shooting gallery,
  and they are not evidence that it is not. Re-measure in the editor, or in game, before quoting any of
  them.
- **What the collision data does say**, and it is solid: the pack's `SM_Tree_L_01` and `SM_Tree_S_01`
  store **zero** simple-collision elements, while `SM_Log_M_01` stores 24, `SM_Rock_M_01` 4 and
  `SM_Ridge_Dirt_01_A` 4. Whether the trees therefore pass bullets and AI depends on their
  complex-as-simple setting, which could not be read from Python and must be checked in the editor. If the
  352 trees are visual-only, they dress the map and break no sightline, and that is the first thing to fix.
- **No rendered review.** Nobody has looked at this map.
- **The dressing is 1,140 individual static mesh actors**, not instanced foliage. That is the right shape
  for nav-relevant cover and the wrong shape for a shipping 1 km map. Instanced static meshes or PCG
  scatter, keeping the authored lines as the source of truth, is the follow-up.

## 2. Provenance

| Property | Value |
|---|---|
| Built from | `/Game/RuralAustralia/Maps/RuralAustralia_Example_01` (Fab "Rural Australia" pack, L-0016) |
| Saved as | `/Game/Maps/L_RedGum_01` |
| Pipeline | `build_redgum_level.py` → `build_redgum_nav.py` → `tag_deployments.py` → `layout_objectives.py` → `layout_spawns.py`; `fix_sky.py` for the sky; then `redgum_homestead.py` + `import_redgum_homestead.py` + `expand_redgum.py` (§1a) |
| ADR | ADR-022 |

Wire fences carry no collision, so pawns pass through them and they do not split the navigation mesh
(ADR-022). The demo map's sky sphere and painted horizon ring are hidden in game; a SkyAtmosphere with
volumetric clouds replaces them (`fix_sky.py`).

## 3. Objectives and capture

| ID | Name | Position | Capture radius |
|---|---|---|---|
| A | North Paddock | left flank | 1200 cm (12 m) |
| B | Homestead | centre | 1200 cm |
| C | South Paddock | right flank | 1200 cm |

**Why the objectives changed.** The original A, B and C sat along the line between the deployments at
−110 m, 0 m and +110 m, with the deployments at ±280 m. Every round opens on A, so Team One had about 170 m to
walk to the first fight and Team Two about 390 m.

`layout_objectives.py` now places them **across** the map instead: the Homestead at the centre, and two
paddocks on the flanks at points with the most even walk from both deployments. Bore Pump and Shearing Shed
were renamed because the objectives no longer stand on those buildings. The paddock names are generic; check
them against what actually stands at those points.

## 4. Deployment

| Property | Value |
|---|---|
| Starts per team | 8 / 8, at least 10.3 m apart |
| Spawn exposure (start pairs with an eye-level line of sight) | 0 / 64 |
| Deployment separation | 379 m (was 560 m) |

Every objective was about 300 m from both deployments, so the first contact came about a minute into the
round. `layout_spawns.py` now slides any deployment more than 200 m on foot from the centre objective towards
it, 5% at a time, for both teams alike.

## 5. Fairness

Walk from each team's primary start, in metres (`spawn_layout.json`):

| Objective | Team One | Team Two |
|---|---:|---:|
| A North Paddock (opening) | 213 | 240 |
| B Homestead | 187 | 195 |
| C South Paddock | 206 | 231 |

The opening objective is within 11% for the two teams. Before the fairness pass the objectives were within
4%, at about 300 m. Pulling the deployments in cost some of that evenness; a hand pass can recover it.

## 6. Play evidence and the stalemate

A headless match on 2026-09-27 (8 bots, 180 s round) completed without errors, but **no objective was
captured**, both before and after the deployments were pulled in. The log shows constant fighting: dozens
of deaths, and bots steered back to the objective.

ADR-018 freezes capture while both teams are inside the objective ("capture is presence, not strength"), and
respawning bots keep both teams present. This is a rules question, not a layout one. It is recorded for a
producer decision in the Session 029 changelog.

## 7. What still blocks sign-off

- [ ] **Build the navigation** for the widened volume in the interactive editor and verify the routes (§1a).
- [ ] **Check the trees in the editor**: do 352 gum trees carry collision, or are they scenery? Zero
      simple-collision elements on `SM_Tree_L_01` / `SM_Tree_S_01` is a fact; what it means for gameplay
      is not yet known (§1a).
- [ ] Re-run the playability audit somewhere that can see static meshes, and throw out the old cover and
      sightline figures for all four maps, not just this one.
- [ ] The capture stalemate (§6): producer decision on the rules or bot behaviour.
- [ ] Check the paddock names and positions against the terrain, in a rendered pass. The centre objective is
      now a real homestead; A and C are named "paddocks" and must be checked against what now stands near them.
- [ ] Recover the evenness of objective A (11%).
- [ ] Re-measure cover density, open crossing and sightlines on the dressed map (§8) and confirm the
      farmhouse did not turn objective B into a hard-cover blob.
- [ ] A human-played round, recorded.
- [ ] Convert the 1,140 dressing actors to instancing or PCG before this map is performance-signed.

## 8. Provenance of the numbers

These `Build/` reports are git-ignored; the values are recorded here:
- `redgum_level.json`, `redgum_nav.json`: original placement and walkable legs;
- `objective_layout.json`: flank placement and each objective's evenness;
- `spawn_layout.json`: starts, spacing, exposure, and the walks in §5;
- `redgum_homestead_report.json`: the seven structures, their slots, trace flags, trace probes and
  ground-seating deltas (§1a);
- `redgum_expansion_report.json`: dressing counts, the station keep-out, and the nav volume;
- `redgum_playability.json` / `.md`: the post-dressing playability audit — **cover and sightline figures
  are void**, see §1a;
- `redgum_nav_probe.json`: whether the stored Recast data actually covers the widened volume;
- `redgum_crash_probe.json`, `redgum_collision_capability.json`, `redgum_selfcollide.json`,
  `redgum_cover_probe.json`, `redgum_trace_ab.json`: the measurements behind the two findings above.

Two `Build/` reports are **stale and must not be read as current**: `redgum_nav.json` is from a run made
before any navigation had been baked, so every route in it reads zero; and the playability figures quoted in
earlier revisions of this document predate all of §1a.
