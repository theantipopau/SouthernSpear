# MAP DESIGN — Saltbush

**Status:** Documented, **not** signed off. This map is playable in the sense that
it loads, spawns both teams and completes a round. It has **not** been held to the
Dry River standard, and §7 records why.

Companion document: `MAPS_DRYRIVER.md` (the standard), `MAPS_SELATCANAL.md`.
`L_RedGum_01` is the third environment-derived map and is still undocumented.

---

## 1. Purpose

Saltbush is the second of the three environment-derived Objective Assault maps. It
exists to test **long-range open engagement**: Dry River is a creek-and-farm map
built for rotations, Red Gum is a 1 km station map, and Saltbush is the map that
asks whether the project's engagement ranges work past 200 m.

It is the primary candidate for the "long sightline" case that Dry River
deliberately refuses (§5 of that document caps practical sightlines).

## 2. Provenance

| Property | Value |
|---|---|
| Built from | `/Game/Namaqualand/Levels/Showcase` (Fab "Namaqualand" pack, L-0016) |
| Saved as | `/Game/Maps/L_Saltbush_01` (28,035,985 bytes) |
| Builder | `Tools/Unreal/build_objective_map.py` (`SS_MAP=saltbush`, `SS_PASS=level` then `nav`) |
| Deployment tagging | `Tools/Unreal/tag_deployments.py` |
| ADR | ADR-022 pattern — the pack's own map is **never** saved; a copy is taken and the source left untouched |

**Naming.** The pack is the real Namaqualand in South Africa. Under ADR-016 the
project uses fictional place names, so the map ships as *Saltbush* and the
objectives are renamed away from the real ones (Windmill / Stock Yards / Dry Dam).
Any in-game text, briefing or store description must use the fictional names only.

## 3. Objectives and capture

| ID | Name | Role | Capture radius |
|---|---|---|---|
| **A** | Windmill | First contact, opening contest | 900 cm (9 m) |
| **B** | Stock Yards | Mid-map pivot | 900 cm (9 m) |
| **C** | Dry Dam | Far objective, round decider | 900 cm (9 m) |

The 9 m radius is the map's own configured value, carried from the builder's
`radius: 900.0`. It is roughly double a player's shoulder width, so an objective is
held by standing on it rather than by proximity — which is the intent for a
three-objection domination-style round.

Actor labels follow `SS_MAP_Saltbush_Obj{A,B,C}_<Name>` and
`SS_MAP_Saltbush_Deploy{A,B}`, set by the builder so the nav pass and any later
tooling can find them by convention.

## 4. Deployment

| Property | Value | Source |
|---|---|---|
| Player starts placed | 16 | `objective_map_saltbush_level.json` → `starts: 16` |
| Team One starts | 8 | `deployment_tags.json` |
| Team Two starts | 8 | `deployment_tags.json` |
| Deployment separation | **162 m** (tagging pass) / **167 m** (nav pass) | both reports |

The two separation figures are measured at different moments — 162 m at tagging
time, 167 m after the nav pass moved things to walkable positions. Both are in the
same range and the 5 m difference is not significant, but the two numbers are not
comparable and should not be quoted as one.

Team split is **even at 8/8**, which satisfies the Dry River fairness rule that
both teams must have the same number of starts.

## 5. Navigation

| Property | Saltbush | Dry River (reference) |
|---|---|---|
| Grid points sampled | 793 | full NavMesh rebuild |
| Reachable | **292 (37%)** | path verified end to end |
| Round legs walkable | 4 / 4 | 4 / 4 |

All four legs of the round (Deploy A → A → B → C → Deploy B) are confirmed
walkable, and the map has a nav-bounds volume, so a round completes. But **63% of
the sampled grid is not reachable**, which is the subject of §7.

## 6. Objective placement was corrected, not designed

The builder's nav pass does not fail when an objective sits somewhere the
navigation cannot reach. It **moves it** to the nearest reachable point and reports
how far it had to travel:

| Objective | Distance moved from its placed position |
|---|---|
| A Windmill | **15.6 m** |
| B Stock Yards | **22.5 m** |
| C Dry Dam | 2.0 m |

An objective relocated 22.5 m may no longer be the feature it was named for — "Stock
Yards" is a specific piece of level, and 22.5 m is far enough to put the capture
volume off the thing it is meant to describe. This map's objective positions are
therefore **not a design decision anyone has made**; they are wherever the
navigation happened to end up.

## 7. Why this map is not signed off

1. **Navigation coverage is 37%, not 100%.** Dry River is navigable *by
   construction* — it is a generated greybox whose whole purpose is to be walked.
   Saltbush is a showcase level from an environment pack, and most of it is not
   connected by walkable space. A player can be shot from somewhere they cannot
   return fire from, and AI will not path to most of the level.
2. **The objectives were auto-placed.** See §6. Fixing this properly means
   choosing the objective positions against the real navigation, which is design
   work, not a script pass.
3. **Sightlines are unmeasured.** The map's whole reason for existing is long-range
   engagement (see §1), and nobody has measured what it actually does. Until the
   longest practical sightline is known, the map cannot be said to fill the gap
   Dry River leaves.

## 8. What would sign it off

- [ ] Raise reachable grid coverage, or carve the objectives' approach routes
- [ ] Choose objective positions deliberately and re-run the nav pass to confirm
      zero relocation
- [ ] Measure longest practical sightline and record it here
- [ ] Verify cover density against the Dry River rule: no player crosses 20 m of
      open ground without passing cover
- [ ] Play a full round on it and record the result

## 9. Provenance of the numbers in this document

Every figure above is read from a checked-in tool report, not estimated:

- `Build/objective_map_saltbush_level.json` — source map, 16 starts, objective names
- `Build/objective_map_saltbush_nav.json` — grid reachability, deployment separation, per-objective relocation distance, leg verification
- `Build/deployment_tags.json` — per-team start counts, tagged separation

Re-run `build_objective_map.py` and `tag_deployments.py` to regenerate all three.
`Build/` is gitignored, so a fresh clone has none of them; the values are recorded
here so this document stands alone.
