# MAP DESIGN — Red Gum Station

**Status:** Documented, **not** signed off. Red Gum is the first playable map (ADR-022). In Session 029 its
objectives were re-laid for fairness and its deployments pulled in. It has **not produced a capture** in a
three-minute bot round (§6).

Companion documents: `MAPS_DRYRIVER.md` (the standard), `MAPS_SALTBUSH.md`, `MAPS_SELATCANAL.md`.

---

## 1. Purpose

Red Gum is the **large outback station** map: a 1 km landscape with open paddocks, gum-tree lines, fences and
a homestead. It tests the long approach and the open ground between cover that the smaller maps cannot.

## 2. Provenance

| Property | Value |
|---|---|
| Built from | `/Game/RuralAustralia/Maps/RuralAustralia_Example_01` (Fab "Rural Australia" pack, L-0016) |
| Saved as | `/Game/Maps/L_RedGum_01` |
| Pipeline | `build_redgum_level.py` → `build_redgum_nav.py` → `tag_deployments.py` → `layout_objectives.py` → `layout_spawns.py`; `fix_sky.py` for the sky |
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

- [ ] The capture stalemate (§6): producer decision on the rules or bot behaviour.
- [ ] Check the paddock names and positions against the terrain, in a rendered pass.
- [ ] Recover the evenness of objective A (11%).
- [ ] Measure cover density on the approaches (Dry River's 20 m rule) and the longest practical sightline.
- [ ] A human-played round, recorded.

## 8. Provenance of the numbers

These `Build/` reports are git-ignored; the values are recorded here:
- `redgum_level.json`, `redgum_nav.json`: original placement and walkable legs;
- `objective_layout.json`: flank placement and each objective's evenness;
- `spawn_layout.json`: starts, spacing, exposure, and the walks in §5.
