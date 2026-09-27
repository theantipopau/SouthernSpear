# Map Playability Audit — Objective Assault, all four maps

**Status: measured, not signed off.** Every number here came from
`Tools/Unreal/audit_map_playability.py` running against the four maps in
`Content/Maps/`. The tool is read-only: it loads a map, measures it and writes
a report, and never places, moves or saves anything. Where a number here
disagrees with what a map document claims, the measurement wins.

| Source | Run |
|---|---|
| `Build/map_playability.json` | four maps, `ok: true`, 0 errors |
| `Build/map_playability.md` | generated summary (per run; the Selat Canal figure set came from `SS_MAPS=L_SelatCanal_01 SS_OUT=mp_canal.json` and was merged into the JSON) |
| Rules from | `Docs/MAPS_DRYRIVER.md` §"design intent" |

The audit exists because the design rules in `MAPS_DRYRIVER.md` were written
for the hand-built blockout and nothing had ever measured them. The three
environment maps were documented as "fair" and "polished" on the strength of
spawn counts and walk legs. Spawn counts turned out to be the one thing that
was already true.

## Rule scoreboard

Rules come from Dry River and were written for a 260 × 180 m blockout. They are
scored on every map, except the absolute 220 m sightline, which only means
something on a map of that size and is reported unscored on Red Gum.

| Rule | Target | Dry River | Red Gum | Saltbush | Selat Canal |
|---|---|---|---|---|---|
| open crossing, p90 | ≤ 20 m | **30.0 FAIL** | **30.0 FAIL** | 16.0 pass | 6.0 pass |
| close quarters | clear sightline under 5 m | 1742 pass | 1749 pass | 1503 pass | 211 pass |
| max sightline | ≤ 220 m | **291.5 FAIL** | 1010.0 n/a | 148.5 pass | 92.7 pass |
| hard:soft cover | 1:3 | 0.47 pass | **none FAIL** | **9.97 FAIL** | **0.75 FAIL** |
| cover density | ≥ 0.3 props/cell | **0.09 FAIL** | **0.00 FAIL** | 1.54 pass | 57.7 pass |
| starts | 8 + 8 | 8+8 pass | 8+8 pass | 8+8 pass | 8+8 pass |
| spawn exposure | 0 of 64 pairs | **35/64 FAIL** | **7/64 FAIL** | 0/64 pass | **16/64 FAIL** |
| walk parity, objective A | ≤ 10% | **18 FAIL** | **12 FAIL** | 6 pass | **63 FAIL** |
| walk parity, objective B | ≤ 10% | **58 FAIL** | 4 pass | **35 FAIL** | **42 FAIL** |
| walk parity, objective C | ≤ 10% | n/a (two objectives) | **12 FAIL** | **22 FAIL** | **75 FAIL** |
| | | **3 pass / 6 fail** | **3 / 6 / 1** | **7 / 3** | **5 / 5** |

## Per map

### Dry River — the reference map fails its own rules

261 × 194 m, navmesh covers 100% of walkable ground (486 of 540 grid cells).

| Measure | Value |
|---|---|
| open crossing | p50 8.0 m, p90 30.0 m, max 30.0 m (search cap) |
| ground with no cover within 30 m | **13%** |
| ground over 20 m open | 15% |
| cover | 14 hard, 30 soft, 0.09 props per walkable cell |
| sightlines | p50 102.3 m, p90 184.6 m, max 291.5 m (90% of the diagonal) |
| deployments | 8+8, 164 m apart, **35 of 64 start pairs can see each other** |
| objectives | Water Point 76/93 m (18%), **Farmstead 134/56 m (58%)** |

`MAPS_DRYRIVER.md` states "no player crosses 20 m of open ground without
passing cover" and lists ~120 cover objects. Measured: 44 blocking props on the
whole map, and an eighth of the ground has no cover within 30 m. The document
is describing intent, not the built result.

The Farmstead is 2.4× farther from Team One than Team Two. Objective Assault
takes A → B → C, so this decides the middle of the round.

### Red Gum — not playable as it stands

1020 × 1020 m of paddock with a 720 × 240 × 200 m navigation volume.

| Measure | Value |
|---|---|
| nav coverage | **17%** of walkable ground |
| open crossing | p50 28.0 m; **50% of ground has no cover within 30 m** |
| cover | **12 hard, 0 soft, in the entire map** |
| sightlines | p50 310.2 m, p90 607.5 m, max 1010.0 m |
| cover within 20 m of each objective | 1, 1, **0** |
| deployments | 8+8, 379 m apart, 7 of 64 start pairs see each other |
| objectives | 211/239 m (12%), 187/194 m (4%), 202/230 m (12%) |

Three separate problems, any one of which is disqualifying:

1. **The navmesh covers a fifth of the map.** A kilometre of walkable ground
   with a navigation volume a fifth of that size means AI that pathfinds, and
   any gameplay logic that asks "can this team reach that point", is working on
   a small patch in one corner.
2. **There is no cover.** Twelve hard cover objects and zero soft on a
   kilometre map. The objectives stand in open paddocks with 310 m median
   sightlines. This is a vehicle and marksman map, not a first-person shooter
   map.
3. **Deployment separation is 379 m**, more than twice Dry River's, on ground
   that is open the whole way.

### Saltbush — the best of the four

132 × 158 m, 95% nav coverage, 206 of 224 grid cells walkable.

| Measure | Value |
|---|---|
| open crossing | p50 4.0 m, p90 16.0 m, only 2% of ground over 20 m open |
| cover | 289 hard, 29 soft, 1.54 props per cell — dense |
| sightlines | p50 51.1 m, max 148.5 m, none over 220 m |
| deployments | 8+8, 121 m apart, **0 of 64 start pairs see each other** |
| objectives | Windmill 82/88 m (6%), **Stock Yards 75/116 m (35%)**, **Dry Dam 115/89 m (22%)** |

The only map with no open-ground problem, no spawn exposure and no over-long
sightlines. Its two failures are real but both are fixable without touching
geometry: the Stock Yards and Dry Dam walk imbalance, and a cover mix that is
almost entirely hard (every rock is a hard corner, so there is nothing to swing
a corner wide on — that is what the soft half of the 1:3 ratio is for).

### Selat Canal — excellent close quarters, unfair objectives

55 × 109 m, 97% nav coverage. This is the **only Special Forces map**
(`Config/DefaultGame.ini`, `+SpecialForcesMaps`).

| Measure | Value |
|---|---|
| open crossing | p50 2.0 m, p90 6.0 m, max 14.0 m — the tightest map in the project |
| close quarters | 211 clear probes under 5 m; 494 between 5 and 20 m |
| cover | 766 hard, 1024 soft, 57.7 props per cell — the city is all cover |
| sightlines | p50 26.9 m, max 92.7 m |
| deployments | 8+8, **51 m apart**, 16 of 64 start pairs see each other |
| objectives | **Footbridge 16/43 m (63%)**, **Market Row 41/24 m (42%)**, **Pump House 64/16 m (75%)** |

The geometry is the best in the project for a first-person mode: a player
crosses 2 m of open ground and is behind something. The objective placement is
the worst. On a 55 m wide map with deployments 51 m apart, the teams are
practically on top of each other and the objectives are stacked down one side,
so one team walks 16 m to the Footbridge while the other walks 64 m to the Pump
House. Every objective fails parity and the spread is enormous.

## What to change, in priority order

1. **Selat Canal objective placement.** Three objectives, all three between 42%
   and 75% walk imbalance, on the project's only Special Forces map. The fix is
   to place the three objectives across the map at points of roughly equal walk
   from both deployments, the way `layout_objectives.py` does for the other
   maps, and to refuse the placement rather than save a lopsided one.
2. **Dry River cover in the open ground.** 13% of the map has no cover within
   30 m against a documented promise of under 20 m. `dress_dryriver_cover.py`
   exists and this is the pass that should fill it.
3. **Red Gum: take it out of rotation or dress it.** A kilometre of open
   paddock with twelve cover objects and a navmesh on a fifth of it should not
   be in a match. It currently is.
4. **Objective walk parity on Saltbush and Dry River.** 35%, 22% and 58% on
   objectives that are worth points in the middle of the round.
5. **Spawn exposure on Dry River (35/64) and Selat Canal (16/64).** Both are
   "no start may see an enemy start" rules that are currently broken.

## Defect in another tool, found by this audit

`layout_spawns.py` reports `exposed_pairs` by tracing each candidate start to
the **enemy deployment centroid**, a single point, rather than to the enemy
starts. It reported 3/64 for Dry River. Tracing all 64 pairs, as this audit
does, gives **35/64**. Every map's exposure number in
`Build/spawn_layout.json` is therefore optimistic, and the spawn layout is not
as hidden as it looks. The fix is to trace against every enemy start rather
than the centroid.

## Method, and what these numbers do not say

- Sampling: a 10 m grid on the blockout-sized maps, scaled up to keep a large
  map under ~3600 cells. 220 walkable points per map, spread by farthest-point
  sampling so the samples cover the whole map rather than clustering.
- Cover: `get_actor_bounds` height against 60 cm (soft) and 140 cm (hard). Only
  meshes with a blocked chest-height trace count, so decoration is excluded.
  **Only `StaticMeshActor`s are counted** — cover inside a blueprint or in
  instanced foliage is not in the hard:soft figures. Selat Canal's 1790 props
  include most of a city block, so treat its density as "dense" and its ratio
  as approximate.
- Open crossing: 12 chest-height directions, 2 m steps, stopping at the search
  cap of 30 m. A ground with no cover within 30 m reads as 30 m, and
  `capped_pct` says how much of the map is that open.
- Walking distance is a chain of points projected onto the navmesh along the
  straight line, retried with a lateral offset if the chain leaves the
  navmesh. It ignores detours, so it reads slightly short — equally for both
  teams, which is what the parity comparison needs. A chain that never
  completes is reported as a lower bound with a note.
- The engine locks the navigation build while a map loads, so `BUILDPATHS` does
  nothing in a commandlet and all navigation data comes from the navmesh stored
  in the level.
- The cover figures and open-crossing measures say nothing about whether a
  cover is *fair*: a barn that belongs to one objective is cover for one team
  only. That needs a play test, not a trace.
