# MAP DESIGN — Selat Canal

**Status:** Documented, **not** signed off — and it carries the most serious
fairness problem in the map set (§4). It is playable and completes rounds, but it
does not yet meet the Dry River standard.

Companion document: `MAPS_DRYRIVER.md` (the standard), `MAPS_SALTBUSH.md`.
`L_RedGum_01` is the third environment-derived map and is still undocumented.

---

## 1. Purpose

Selat Canal is the **urban** Objective Assault map, and the only map in the set
built on a built environment rather than terrain. It is where the project tests
close-quarters and interior fighting — the case Dry River explicitly rules out by
keeping a 5 m minimum engagement range on open ground and a 20 m maximum open
crossing.

It is also the only map registered as a **Special Forces** map (see §6), which makes
it the test bed for the SF weapon kits.

## 2. Provenance

| Property | Value |
|---|---|
| Built from | `/Game/Singapore_Canal/Map/Singapore_Canal` (Fab "Asian Canals" pack, L-0016) |
| Saved as | `/Game/Maps/L_SelatCanal_01` (20,418,944 bytes) |
| Builder | `Tools/Unreal/build_objective_map.py` (`SS_MAP=canal`, `SS_PASS=level` then `nav`) |
| Deployment tagging | `Tools/Unreal/tag_deployments.py` |
| ADR | ADR-022 pattern — the pack's own map is **never** saved |

**Naming.** The source is the real Singapore Canal. Under ADR-016 the project uses
fictional place names, so it ships as *Selat Canal* with objectives renamed
(Footbridge / Market Row / Pump House). The six `.umap` files of the source pack
(`Day01`, `Day02`, `Night01`, `AssetsShowcase`, …) remain in
`Content/Downloaded/VaultCache/` and are not part of the game.

## 3. Objectives and capture

| ID | Name | Role | Capture radius |
|---|---|---|---|
| **A** | Footbridge | First contact, chokepoint | 700 cm (7 m) |
| **B** | Market Row | Mid-map pivot, urban | 700 cm (7 m) |
| **C** | Pump House | Far objective, round decider | 700 cm (7 m) |

The 7 m radius is the builder's configured value (`radius: 700.0`), tighter than
Saltbush's 9 m. In dense urban geometry a 9 m volume would swallow a building, so
the tighter radius is the right instinct — but it has not been checked against how
the buildings actually enclose the objectives, only set.

## 4. Deployment — the fairness defect

| Property | Value |
|---|---|
| Player starts placed | **15** |
| Team One starts | **7** |
| Team Two starts | **8** |
| Deployment separation | **70 m** (tagging pass) / **75 m** (nav pass) |

**This is an even-odds problem in an odd-player game.** Team Two has one more
spawn than Team One. In a mode where a team that dies rotates back to a start, the
team with the extra start has a measurable advantage, and it compounds over a round.

Every other map in the set is 8/8:

| Map | Team One | Team Two | Separation |
|---|---:|---:|---:|
| Dry River | 8 | 8 | 170 m |
| Red Gum | 8 | 8 | 560 m |
| Saltbush | 8 | 8 | 162 m |
| **Selat Canal** | **7** | **8** | **70 m** |

Selat Canal is also the **shortest deployment separation in the set by a factor of
two**. Both teams start almost on top of each other. That may be deliberate — a
canal crossing is a natural chokepoint fight — but it is not documented as a
decision anywhere, and 70 m is inside the range at which a spawn is trivially
contested. Dry River's opening is 86 m to a centre objective and is explicitly
designed to be equal; this one starts the fight at the spawn.

**Two open questions, both needing a producer answer:**
1. Is 7/8 an accepted consequence of a 15-start source level, or should a start be
   added to Team One?
2. Is a 70 m separation the intended design, or an artefact of where the walkable
   ground ended up?

## 5. Navigation — the worst in the set

| Property | Selat Canal | Saltbush | Dry River |
|---|---:|---:|---|
| Grid points sampled | 154 | 793 | full rebuild |
| Reachable | **35 (23%)** | 292 (37%) | verified end to end |
| Round legs walkable | 4 / 4 | 4 / 4 | 4 / 4 |

**Only 35 of 154 sampled points are reachable — 23%.** This is the worst navigation
figure of any map in the project, and for an urban map it is a serious problem: the
level is full of walls, kerbs, stairs and canal edges, and most of it is not
connected for pathing purposes.

All four legs are walkable and the round completes, but only because the nav pass
moves whatever it cannot reach. The result is a map where the playable space is a
thin connected thread through a much larger decorative environment — which is
precisely the failure mode the ADR-022 whole-map reuse was supposed to avoid, and
the reason those maps are documented rather than signed off.

## 6. Special Forces registration

`Config/DefaultGame.ini` contains:

```
; Special Forces maps: SF kits (A416 / A4).
+SpecialForcesMaps=L_SelatCanal_01
```

Selat Canal is therefore the only map that hands players the Special Forces
loadouts — the A416 in the Rifleman and Grenadier roles, with the A4 as the
secondary. This is a real design intent recorded in configuration, and it is the
map where those weapons should be play-tested first.

## 7. Objective placement was corrected, not designed

As on Saltbush, the nav pass relocates any objective it cannot reach and reports
the distance moved:

| Objective | Distance moved |
|---|---|
| A Footbridge | 2.0 m |
| B Market Row | 5.5 m |
| C Pump House | 6.4 m |

These are much smaller than Saltbush's (up to 22.5 m), so the objectives still sit
on the features they are named for. That is the one respect in which this map is
in better shape than Saltbush.

## 8. Why this map is not signed off

1. **7/8 deployment split** — an even-odds defect in an odd-player game (§4)
2. **23% navigation coverage** — the worst in the set, on the map whose whole
   purpose is dense built geometry (§5)
3. **70 m separation, undocumented and unexplained** (§4)
4. **Urban cover rules unmeasured.** Dry River's rules (≤20 m open crossing, 5 m
   minimum engagement, 1:3 hard-to-soft) were written for open terrain. Whether
   they mean anything between buildings has not been considered, let alone checked.

## 9. What would sign it off

- [ ] Resolve the 7/8 split to 8/8, or record the acceptance explicitly
- [ ] Decide and document whether 70 m separation is intended
- [ ] Raise reachable grid coverage, or cut the level down to what is actually
      traversable so the map matches its own footprint
- [ ] Measure the map's real sightlines and engagement ranges in built geometry
- [ ] Play-test the SF kits on it, since it is their designated map
- [ ] Play a full round and record the result

## 10. Provenance of the numbers in this document

- `Build/objective_map_canal_level.json` — source map, 15 starts, objective names
- `Build/objective_map_canal_nav.json` — grid reachability, separation, relocation distances, leg verification
- `Build/deployment_tags.json` — per-team start counts, tagged separation
- `Config/DefaultGame.ini` — the Special Forces registration

`Build/` is gitignored; the values are recorded here so this document stands alone.
