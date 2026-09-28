# MAP DESIGN — Saltbush

**Status:** Documented, **not** signed off. The deployment and objective layout
was rebuilt for fairness in Session 029 (§4–§6), and the map has produced a
capture in a bot match. Navigation coverage, sightlines and cover are still
unmeasured against the Dry River standard (§8).

Companion documents: `MAPS_DRYRIVER.md` (the standard), `MAPS_REDGUM.md`,
`MAPS_SELATCANAL.md`.

---

## 1. Purpose

Saltbush is one of three Objective Assault maps built from Fab environment packs.
It exists to test **long-range open engagement**:
- Dry River is a creek-and-farm map built for rotations;
- Red Gum is a 1 km station map;
- Saltbush asks whether the project's engagement ranges work past 200 m.

It is the main candidate for the long-sightline case that Dry River deliberately
avoids (§5 of that document caps practical sightlines).

## 2. Provenance

| Property | Value |
|---|---|
| Built from | `/Game/Namaqualand/Levels/Showcase` (Fab "Namaqualand" pack, L-0016) |
| Saved as | `/Game/Maps/L_Saltbush_01` |
| Pipeline | `build_objective_map.py` (`SS_MAP=saltbush`, `SS_PASS=level`, then `nav`) → `tag_deployments.py` → `layout_objectives.py` → `layout_spawns.py` |
| ADR | ADR-022 pattern: the pack's own map is **never** saved; a copy is taken and the source is left untouched |

**Naming.** The pack depicts the real Namaqualand in South Africa. ADR-016
requires fictional place names, so the map ships as *Saltbush*, with fictional
objective names (Windmill, Stock Yards, Dry Dam).

**The names are labels, not features.** Nobody has checked that a windmill,
stock yards or a dam stand at these points. The objectives are placed for
fairness (§5), not on named landmarks. Before release, either rename the
objectives after what is really there, or move them onto matching features.

## 3. Objectives and capture

| ID | Name | Capture radius |
|---|---|---|
| A | Windmill | 900 cm (9 m) |
| B | Stock Yards | 900 cm |
| C | Dry Dam | 900 cm |

Each round opens on A and takes A, B and C in order (ADR-018).

## 4. Deployment

| Property | Value | Source |
|---|---|---|
| Starts per team | **8 / 8** | `spawn_layout.json` |
| Minimum spacing between starts | 4.5 m / 7.2 m | `spawn_layout.json` |
| Spawn exposure (start pairs with a clear eye-level line of sight to an enemy start) | **0 / 64** | `spawn_layout.json` |
| Deployment separation | 121 m straight, 208 m on foot | `spawn_layout.json` |

`layout_spawns.py` owns the starts. For each team it samples walkable ground
around the deployment and rejects:
- points within 70 cm of a wall;
- points with under 2 m of headroom;
- points that cannot reach the centre objective.

It then keeps 8 starts spread by farthest-point sampling, preferring points
hidden from the enemy deployment. Every start faces the centre objective.

## 5. Fairness: the objective layout

**Before Session 029.** The builder spaced A, B and C along the line between the
deployments, which put A a third of the way from Team One. On foot, Team One had
46 m to walk to the opening objective and Team Two 134 m. The nav pass had also
moved objectives up to 22.5 m from where they were placed.

**Now.** `layout_objectives.py` places each objective at walkable points with the
most even walk from both deployments. Saltbush's walkable band is too narrow for
true left and right flanks, so the tool spreads the three objectives as far apart
as it can among the evenly reachable points.

Walk from each team's primary start, in metres (`spawn_layout.json`):

| Objective | Team One | Team Two |
|---|---:|---:|
| A Windmill (opening) | 105 | 104 |
| B Stock Yards | 95 | 132 |
| C Dry Dam | 132 | 139 |

The opening objective is even. B favours Team One by about 34%. That was the
price of keeping the three objectives at least 28 m apart (legs of 28 m and
52 m), and it is the first thing to revisit in a hand pass.

## 6. Navigation

| Property | Value |
|---|---|
| Grid points sampled (5 m) | 792 |
| Reachable from the largest walkable island | 293 (37%) |
| Round legs walkable | 4 / 4 |

## 7. Play evidence

A headless match on 2026-09-27 (8 bots, 180 s round) ran the whole round. Team
One captured the Windmill; no other capture happened in the time.

## 8. What still blocks sign-off

- [ ] Navigation coverage is 37%. Carve or open the approach routes, or cut the
      level down to its walkable footprint.
- [ ] Rename the objectives, or move them onto real features (§2).
- [ ] Reduce B's 34% walking imbalance.
- [ ] Measure the longest practical sightline (the map's reason to exist).
- [ ] Check cover density against the Dry River rule: no crossing of more than
      20 m of open ground without cover.
- [ ] A human-played round, recorded.

## 9. Provenance of the numbers

These `Build/` reports are git-ignored, so the values are recorded here:
- `objective_map_saltbush_nav.json`: grid reachability and walkable legs;
- `objective_layout.json`: objective placement and each objective's imbalance;
- `spawn_layout.json`: starts, spacing, exposure, and the walks in §5.

To regenerate them, run the pipeline in §2 in order.
