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
- [ ] NavMesh generates covering all walkable space — **requires the compiled project (G0.8)**
- [ ] Source `.blend` committed to LFS

---

## 10. What This Map Does Not Do

Stated plainly so it is never over-claimed:

- It does **not** have final art, materials, lighting or audio.
- It does **not** have multiple layers. Day and low-light variants come in Phase 4; the vertical slice ships one.
- It does **not** have vehicles, destructibles, or dynamic cover.
- It does **not** represent a real place, and its layout is not derived from any real site.
