# MAP DESIGN — Selat Canal

**Status:** Documented, **not** signed off. The 7/8 spawn split is fixed and the
starts are now laid out properly (§4). But the canal's connected walkable area is
too small for a fair three-objective sequence, and Team One reaches the opening
objective first (§5). **The map needs a redesign pass before it can be fair.**

Companion documents: `MAPS_DRYRIVER.md` (the standard), `MAPS_REDGUM.md`,
`MAPS_SALTBUSH.md`.

---

## 1. Purpose

Selat Canal is the **urban** Objective Assault map, and the only one set in a
built environment rather than open terrain. It tests close-quarters and interior
fighting. Dry River rules that case out: it keeps a 5 m minimum engagement range
on open ground and a 20 m maximum open crossing. Selat Canal is also the only
**Special Forces** map (§6).

## 2. Provenance

| Property | Value |
|---|---|
| Built from | `/Game/Singapore_Canal/Map/Singapore_Canal` (Fab "Asian Canals" pack, L-0016) |
| Saved as | `/Game/Maps/L_SelatCanal_01` |
| Pipeline | `build_objective_map.py` (`SS_MAP=canal`, `SS_PASS=level`, then `nav`) → `tag_deployments.py` → `layout_spawns.py` |
| ADR | ADR-022 pattern: the pack's own map is never saved |

**Naming.** The pack depicts the real Singapore Canal; the map ships as *Selat
Canal*, with fictional objective names: Footbridge, Market Row and Pump House
(ADR-016).

## 3. Objectives and capture

| ID | Name | Capture radius |
|---|---|---|
| A | Footbridge | 700 cm (7 m) |
| B | Market Row | 700 cm |
| C | Pump House | 700 cm |

The objectives sit along the longest route across the walkable island. The nav
pass moved them 2.3 m, 4.5 m and 5.0 m from where they were placed, so they are
still on or close to their intended spots.

## 4. Deployment: the 7/8 defect is fixed

| Property | Before | Now |
|---|---:|---:|
| Starts per team | **7 / 8** | **8 / 8** |
| Minimum spacing between starts | 3 m, in a line | 5.1 m / 8.7 m |
| Spawn exposure (start pairs with eye-level line of sight) | not measured | 11 / 64 |
| Deployment separation, straight / on foot | 70 m / not measured | 51 m / 99 m |

**What changed in the tools:**
- The old builder placed each team's starts in a single line 3 m apart, and
  dropped any start with no ground under it. That is how Team One ended up with 7.
- `layout_spawns.py` now places 8 starts per team on clear, walkable ground.
  Every start must also be able to reach the objectives.
- The deployment pair is chosen by `min(walk, 1.6 × straight line)`:
  - straight-line distance alone gave 70 m between two ends of a walled street;
  - walking distance alone put the teams on opposite banks, 20 m apart across
    the water.

**A bug this exposed (now fixed).** One run placed Team One's starts on a small
patch of navigation that did not connect to the rest of the map. The team's
centre point had drifted there, and starts were only checked against that point.
Starts must now also reach the centre objective.

**Exposure.** 11 of 64 start pairs still have a line of sight across the canal.
The ground near the deployments offers too little cover to hide all 16 starts.

## 5. Fairness: not yet achievable on this footprint

Walk from each team's primary start, in metres (`spawn_layout.json`):

| Objective | Team One | Team Two |
|---|---:|---:|
| A Footbridge (opening) | **25** | **74** |
| B Market Row | 51 | 69 |
| C Pump House | 65 | 35 |

Team One reaches the opening objective about three times faster.

`layout_objectives.py` (§5 of `MAPS_SALTBUSH.md`) was tried here. The evenly
reachable points all sit within about 28 m of each other, so the three 7 m
objectives almost merged into one zone. That layout was rejected and the
route-based one kept.

**Root cause: the map is barely connected.** Only 34 of the 158 sampled grid
points (22%) are reachable. An experiment raised the navigation step height from
35 cm to the character's 45 cm, to match what a player can step up. It connected
only 5 more points (36 → 41 of 164), so kerbs and steps are not the main break.
The unreachable samples are most likely rooftops, the canal bed and closed
courtyards. The experiment was reverted, since it would have required rebuilding
every map's navigation for a 3% gain.

## 6. Special Forces registration

`Config/DefaultGame.ini` includes `+SpecialForcesMaps=L_SelatCanal_01`. On this
map every class uses Special Forces kits (A416 / A4) in place of the standard A88.

## 7. What would make it fair

- [ ] Open more of the district to movement: connect the two banks with more
      crossings, or unblock courtyards and alleys, then re-run the nav pass and
      `layout_objectives.py`.
- [ ] Or cut the playable space down to a symmetric slice around one or two
      bridges.
- [ ] Or give the map two objectives (the Dry River shape) instead of three.
- [ ] Reduce the 11/64 spawn exposure with cover near the deployments.
- [ ] Measure urban sightlines, and decide which Dry River cover rules apply
      between buildings.
- [ ] A human-played round with the SF kits, recorded.

## 8. Provenance of the numbers

These `Build/` reports are git-ignored; the values are recorded here:
- `objective_map_canal_nav.json`: grid reachability, separation, relocations,
  legs;
- `spawn_layout.json`: starts, spacing, exposure, and the walks in §5;
- `Config/DefaultGame.ini`: the Special Forces registration.
