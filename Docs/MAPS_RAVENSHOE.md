# MAP DESIGN — Ravenshoe Crossing

**Document ID:** `Docs/MAPS_RAVENSHOE.md`
**Status:** **In Unreal, dressed, surfaced, lit and wired. Navigation not baked.** `/Game/Maps/L_Ravenshoe_01` — **665 actors**, **35/35 audit checks pass**.
**2026-09-28 first play test:** spawns, collision and the nav bake fixed; ground still renders white, bots do not advance, horizon edge shows — see `Docs/HANDOVER_RAVENSHOE.md` §0.
**Last updated:** 2026-09-28
**Authoring:** `Tools/Common/ravenshoe_spec.py` (shared spec) → `Tools/Blender/ravenshoe_blockout.py` → FBX
**Import/dress:** `Tools/Unreal/import_ravenshoe.py` · **Audit:** `Tools/Unreal/audit_ravenshoe.py` (read-only)
**Verification:** `Tools/Blender/verify_ravenshoe.py` — **53/53 checks pass** (spec-only mode runs in CI without Blender)
**Map package:** `/Game/Maps/L_Ravenshoe_01`

**Companion documents:** `MAPS_DRYRIVER.md` (the design standard), `MAPS_REDGUM.md` (the large-map precedent), `MAPS_SALTBUSH.md`, `MAPS_SELATCANAL.md`.

> **Fictional entertainment project.** Not endorsed, developed or approved by the Australian Defence Force, the Department of Defence or the Australian Army. Ravenshoe Gorge is an **invented** location. Its layout is designed from gameplay requirements and reproduces no real training area, installation or operationally useful site.

---

## 0. Provenance — read this before anything else

The producer asked for a map "re-creating the famous bridge crossing map from America's Army 2, with an
Australian twist." That request is legitimate in its **design intent** and constrained in its **execution**.

| | Position |
|---|---|
| **L-0008** | ❌ No *America's Army 2* source content of any kind: no layouts, geometry, names, HUD, textures, audio. Binding. |
| **L-0007** | ❌ No commercial game models. Binding. |
| **ADR-013** | Maps are built **original**; a third-party environment is never a base map or a layout reference. |
| **ADR-021** | Licensed third-party art may **dress** an original layout. It may never define one. |

**What is taken from the reference, and what is not.**

*Taken — design principle only, and these are generic to the genre, not to any one game:*

- **A single crossing as the map's one chokepoint.** The whole round is about who controls the span.
- **A terminal objective that reads as a doorway.** A building with a road-passage through it, placed on the
  far bank, so the far end of the axis is a *threshold* rather than a point on a hill.
- **A hard axial sightline straight down the deck.** The lane is the map's signature and it is meant to be
  held or broken, not avoided.
- **Flanking approaches at both ends** that let a player bypass the chokepoint at a cost.
- **A lower space beneath the crossing** — a watercourse or working level — that creates a second lane and
  lets players take the crossing from underneath.

*Not taken, deliberately:*

- **No AA2 geometry is traced, approximated or eyeballed.** No dimensions are carried across.
- **No AA2 naming.** "Bridge Crossing", the mission name, the objective letters' placement, the HUD and the
  faction names do not appear. The map is *Ravenshoe Crossing*; its objectives are named for the place.
- **No AA2 assets**, and specifically not the stone-arch vocabulary. The reference's signature is a masonry
  arch bridge. This map's signature is a **wrought-iron lattice girder** (§2), which is a different
  engineering form, a different silhouette, and an authentically Australian one.
- **The reference is not used as a layout reference.** The layout below is derived from the Dry River rule
  set (§4), not from the screenshots.

**Every asset in this map is either already installed in the project or modelled by us.** No pack is
imported for it (§6). This is the second reason the design is safe: it does not merely avoid the AA2
problem, it needs no third-party base at all.

---

## 1. Purpose

Ravenshoe Crossing is the map that tests **a chokepoint with two levels**. Dry River tests long lanes and
concealment on one plane. Red Gum tests distance. Ravenshoe tests what happens when the fight has to happen
*in the throat of something*, where a handful of players decide a round and the rest of the map is approach.

It is deliberately **small** — the scale rule in `ASSET_REGISTER.md` §4.9 says small polished maps first —
and it is the natural successor to Dry River as a slice test bed, not a replacement for it.

**The lesson it teaches:** *a chokepoint you can walk around is not a chokepoint.* The bridge is the obvious
lane and it is the correct answer most of the time. The creek bed underneath is the alternative, and it is
always worse — and the player who takes it pays for that in time, not in a scripted punishment.

---

## 2. The Australian twist

**Setting.** A high-country gorge in the Australian Alps, in the dry season. Local granite, snow patches on
the shaded north-facing slopes, eucalypts holding the ridge above the treeline, a creek reduced to boulders
and a shallow channel.

**The bridge.** A **wrought-iron lattice-girder road bridge** — a local stone-and-timber era highway bridge,
the kind built across Australian creeks from the 1870s to the 1930s, many of which survive as heritage
structures. Wrought iron, not steel plate: riveted lattice diagonals, X-braced, with slender uprights and
cast-iron lamp standards along the parapet.

This is the twist doing real work, not decoration:

- It is **visually unlike** the reference's stone arches, so the two maps cannot be confused in a
  screenshot or a store thumbnail.
- It gives **better gameplay geometry than an arch would**: a lattice truss is a grid of diagonals and
  uprights, which is a repeating cover rhythm along the deck. A stone arch is mostly parapet, which is one
  continuous low wall and a dead lane.
- The uprights are **see-through**, so the deck is exposed to the gorge walls in a way that makes the
  flanking positions genuinely threatening rather than safely one-sided.

**The gatehouse.** On the north abutment, a **stone road-gate house** in local granite rubble — the
telegraph/tollhouse type that guarded crossings and relay stations on the old overland routes, where a
road passage ran through the building under an arch. Objective B sits *in* that passage.

This is the Australian counterpart of the reference's portal-at-the-end-of-the-axis, arrived at from our own
history rather than from their map. The historical type is a good fit precisely because it was built to
**watch a crossing**.

**Why not the obvious alternatives.** A tropical timber trestle and an arid steel truss were both
considered and set aside: the trestle's timber piers fragment the deck into a pick-up-beat shooter space,
and the arid truss gives up the gorge depth that makes the second lane exist at all. Granite gorge depth is
the whole point.

---

## 3. Scale and budgets

| Property | Value | Justification |
|---|---|---|
| Playable area | **300 m (N–S) × 200 m (E–W)** | Small enough to polish and bake; long enough that a 68 m span is a real commitment. Dry River is 260 × 180, so this is a modest step, not a jump |
| World Partition | **No** | Scale rule: World Partition only where scale justifies it. 300 × 200 m does not |
| Vertical relief | **46 m** | Gorge bed at −18 m, ridge crest at +28 m. Dry River manages 14 m; a gorge cannot. Relief this size is the reason the map is interesting |
| Gorge width | **68 m** | The bridge span plus abutment seats. Fixed by the 20 m open-crossing rule: see §4.3 |
| Deck height above bed | **32 m** | Deep enough that the bed is a distinct place, not a ditch. Also forces the ramps to be real routes rather than shortcuts |
| Deck width | **7.5 m** | Wide enough to fight on and to fall back along; narrow enough to be covered. A 4 m deck is a shooting gallery |
| Team size | 8 v 8 | The vertical slice runs 4 v 4 (Dry River §3). 8 v 8 is the target the map is designed to hold |
| Cover objects | **68 markers** + 42 truss uprights + 10 lamps | Dry River's budget is ~120 for a smaller area. The 68 scattered markers cover the off-deck routes; the deck's cover is the structure itself, not dressing |
| Navigation | Full NavMesh, no dynamic nav | As Dry River: a greybox must be navigable by construction. **Infrastructure is in place, the bake is missing — see §7.1** |

**Built and measured** (`SS_MAP_Ravenshoe_01_HI.blend`): terrain 200 × 300 m, 15,000 faces, relief −18.0 to +28.0 m.
Bridge 1266 faces, four material slots (Iron / Deck / Road / Stone). Gatehouse 450 faces, 9.6 × 6.8 × 6.0 m. 72 layout rows.

### 3.1 Bridge metrics

The dimensions above are inputs. What the bridge is *judged* on are the **ratios** between them, and
those are printed on every `verify_ravenshoe.py` run and range-checked by
`check_bridge_metrics()` (M-008n). They can all be wrong while every dimension still reads as the value
typed into the constant, which is why the checks are on the ratios.

| Metric | Value | Why it is the number that matters |
|---|---|---|
| Span, lip to lip | **68.0 m** | The sanctioned exception to the 20 m open-crossing rule |
| Gorge depth at the bed | **32.0 m** | The drop the deck crosses |
| Deck width over the parapets | **7.5 m** | Wide enough to fight on, narrow enough to cover |
| Clear lane between parapets | **6.8 m** | The width a player actually has |
| Parapet height | **1.05 m** | Crouch cover, and it makes the deck a firing step rather than a lane |
| Truss depth above the deck | **5.2 m** | The structure's whole visual job |
| **Span : truss depth** | **1 : 13.1** | A lattice girder of this class sits in 1:12–1:20. Shallower and the chords are scenery; deeper and the portal headroom is being spent on structure |
| Bay length | **3.4 m** | The cover rhythm. A player crosses one bay per exposure, and it must not become a picket fence |
| Uprights per side | **21** | The 20 m rule's mitigation, made of geometry |
| Lamp standards | **10** (one each side every 17 m) | The two at each abutment are a pair, not a shared standard |
| Clear headroom over the lane | **5.03 m** | Set by the sway frames, not the lateral bracing. Below 4 m a 68 m deck starts to feel like a tunnel |
| Deck area fought over | **510 m²** | The map's primary firefight, all of it exposed from both approaches |
| Parapet cover, one side | **71.4 m²** | What the 1.05 m actually buys |
| Bed-to-deck over the span | **25.2°** | The visible slope of the gorge, lip to lip |

### 3.2 Surfaces

The bridge, its abutments and the gatehouse are surfaced with **generated original textures** (ADR-030,
M-008m), not an imported pack: sealed gravel on the running surface, rusted ironwork on the lattice and
parapets, painted steel on the deck structure, coursed granite on the abutments and gatehouse. All four
are `M_SS_ScanPBR` instances, so pack and generated textures feed one shader.

Two properties are enforced rather than eyeballed. Every set is **periodic** — a tiling map with a
baked-in low-frequency gradient repeats as stripes down a 68 m deck — and the deck's **running surface
is its own material slot**, split off the slab by polygon, so the fascia and soffit can be painted steel
while the top is road. The verifier checks that the Road slot's area equals deck width × span and that
no Road face is non-horizontal, because the fault it prevents is invisible from the deck.

### 3.3 Atmosphere, vegetation and dressing

| Layer | What | Source |
|---|---|---|
| Light | Sun (pitch −54, yaw 38, intensity 9), `SkyAtmosphere`, real-time-capture `SkyLight`, unbound post-process with exposure clamped 0.5–2.0 | `Tools/Unreal/light_ravenshoe.py` |
| Fog | `ExponentialHeightFog`, `start_distance` **140 m**, density 0.055, max opacity 0.82 | as above |
| Ground cover | **188** low scrub/litter actors in 11 clusters, collision off | `Tools/Unreal/dress_ravenshoe_groundcover.py`; `Namaqualand` pack |
| Props | 38 actors incl. a 3-vehicle roadblock at the south lip | `Tools/Unreal/dress_ravenshoe_props.py` |
| Experience | 2 objectives, 1 director, `DefaultGameplayExperience` bound | `Tools/Unreal/wire_ravenshoe_experience.py` |

**Why the fog is distance, not height.** The obvious tool for a gorge is height fog, pooling in the bed
and thinning on the crest. Ravenshoe has **46 m of total relief** — bed −18 m, deck +14 m, crest +28 m
— and `ExponentialHeightFog` on 5.8 exposes `fog_height_falloff` but **not** `fog_height_offset` or
`fog_height_density` (both probed, both absent). With no offset the height layer pins to z = 0, so a
falloff of 0.02 makes a **50 cm-thick disc lying across the deck at road level**, not a pool in the
gorge. The height term is therefore off. `start_distance` is set to 140 m, which leaves the 68 m span
and both lips completely untouched and fogs only the 200 m ridge-to-ridge shot — which is the sniper
case the fog exists to break. A true bed-pool needs a property this build will not take.

**Why Namaqualand.** It is the only arid-country vegetation in the project, and Karoo succulent veld is
genuinely close to Australian arid shrubland in habit. Rejected on look: `Light_Foliage` is temperate
forest; `Nanite_Plants_Sample_Collection` is Acer and Ophiopogon — ornamental Japanese and Chinese
garden plants, wrong biome *and* wrong culture (ADR-016). Unlike the Fab props these arrive as ready
`StaticMesh` assets, so there is nothing to import or prep, and they **keep their own vendor
materials** (ADR-029) rather than being unified onto `MI_SS_Raven_*` — a dozen different plants reading
as a dozen different plants is the point of ground cover.

### 3.4 Pipeline and its run order

Order is load-bearing, not cosmetic. `import_ravenshoe` re-imports the bridge FBX and re-spawns the
geometry actors, which strips the surface overrides; running the surfaces pass first means the next
import silently returns the bridge to flat colours. Full order:

```
ravenshoe_blockout.py            (Blender: geometry + spec, generates the FBX)
verify_ravenshoe.py              (Blender: 53 checks, or spec-only in CI)
make_ravenshoe_surfaces.py       (Python: 20 PBR sets + the wrap check)
  --- Unreal, in this order ---
import_ravenshoe.py
dress_ravenshoe_props.py
setup_ravenshoe_surfaces.py
dress_ravenshoe_groundcover.py
light_ravenshoe.py
wire_ravenshoe_experience.py
expand_ravenshoe.py              (skirt, ground material, boundary, horizon, nav bounds, tile pool)
fix_ravenshoe_starts.py          (LyraPlayerStart deployments; import places plain starts Lyra ignores)
fix_ravenshoe_collision.py       (complex-as-simple on the three originals; terrain ground material)
build_ravenshoe_nav.py           (build mode: asserts bounds+pool, one BUILDPATHS, LES save)
audit_ravenshoe.py
```

## 7. Open items

### 7.1 Navigation — corrected 2026-09-29

Measured after the second round: the bounds volume is play-space correct (X ±130 m, Y ±180 m, Z −25..+40 m,
asserted by both the expand and nav passes) and the RecastNavMesh `TilePoolSize` is 4096 (the play space
needs ~1,285 tiles at TileSizeUU 1000; the actor carried the 1024 default, which capped the map's one
interactive bake). What remains true is that **the bake itself must happen in the attended editor**:
headless BUILDPATHS — commandlet, `-RenderOffscreen`, or the editor unattended — serialises ~8 KB of nav
against Dry River's megabytes, and a freshly spawned cube gains no poly on either map after ten spaced
builds (`Build/dr_cube.json`, `Build/raven_cube.json`). The async-loading ini flag earlier passes used
(`bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False`) makes the automatic load-time build
run **early, on partial geometry**; it is not part of the fix. Details and the full evidence trail:
`Docs/HANDOVER_RAVENSHOE.md` §0b and CHANGELOG Session 069 (R-69).

**To bake:** open the editor with `/Game/Maps/L_Ravenshoe_01` loaded, **Build ▸ Build Paths**, save.
Then re-run `build_ravenshoe_nav.py` in verify mode — it must report 32/32 routes — and a live `-game`
run must log `Steered N idle bot(s)` with N > 0.

**Map count.** This is a candidate **fifth** map. It is not a replacement for Dry River and does not
supersede Red Gum; it is an addition to the §4.9 table as `M-008`.

---

## 4. Layout

North is **+Y**. The road runs north–south; the gorge cuts **east–west** across it; the bridge spans it
north–south. This orientation is chosen so the axial lane is the map's long axis and the flanking routes
have to leave the road entirely and come back to it.

```
                    y = +150  ─────────────────────────────────────────
                        ▲N deploy                                      │
                             │   ▲▲▲▲  ridge crest +28 m  ▲▲▲▲          │
                             │      ▲▲▲  (snow, north slope)  ▲▲▲       │
                             │                                        │
   OBJ B (gate) ────┤            ▛▀▜▀▛▀▜▀▛▀▜▀▛▀▜▀▛▀▜▀▛▀▜▀▛▀▜▀        │
   (stone arch,     │   y=+62   │  stone road-gate house   │            │
    road passage)   │           │  deck z = +14            │            │
                             │            ░░░░░░░░░░░░░                  │
                             │            ░ iron truss  ░                 │
   OBJ A ───────────┤   y=0     ░░░░░░░░░  ▼ mid-span  ░░░░░░░░░░░         │
   (The Span)       │           ░░░░░░░░░  lamp posts  ░░░░░░░░░░░       │
                             │            ░ iron truss  ░                 │
                             │            ░░░░░░░░░░░░░                  │
                             │     ┌────────┴────────┐                    │
                             │     │  GORGE  −18 m   │   boulder cover     │
                             │   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒            │
                             │  ramp E        ramp W  (creek bed lane)   │
                             │        │         │                        │
   south abutment ──┤   y=−34   └─▬┬─────┬────┬─▬┘   iron abutment      │
   (toll bar +       │              │     │    │        + approach        │
    tollhouse)       │           y = −40        y = −52                    │
                             │                                        │
                             │   ▲▲  open snow approach  ▲▲              │
                    y = −150 ────────────────────────────────────────────
                        ▲S deploy
```

### 4.1 Objectives

Sequential **A → B**, as Dry River §6.1. Never parallel.

| ID | Name | Position | Role |
|---|---|---|---|
| **A** | **The Span** | Bridge deck at `y = 0`, `z = +14` | The contested opening. Mid-span, so it is equidistant |
| **B** | **Gravel Gate** | Road passage through the stone gatehouse, `y = +62` | The terminal objective and the round's pivot |

Sequential order is what makes the layout fair, and the argument is Dry River's (§6.1): both teams contest
mid-span first, so **both teams begin the second leg from the same place**. Neither may skip A to take B,
which is precisely what would otherwise hand the northern team the round for free.

**Objective A is on the bridge, not at a bridgehead.** This is the one non-obvious decision in the layout
and it is forced by fairness. A bridgehead objective at `y = −34` sits 96 m from the southern deployment
and 164 m from the northern one; that is a 68 m positional gift, and no amount of terrain dressing repairs
it. Mid-span splits it exactly.

### 4.2 Deployment zones

| Zone | Position | Depth |
|---|---|---|
| **South** | `y = −130`, full width | 30 m |
| **North** | `y = +130`, full width | 30 m |

Both open toward the crossing and both are behind the ridge crest, so neither team starts with the span in
view. **Rotation distances are now measured, not assumed** — the spec is the geometry, so
`ravenshoe_spec.py` can compute them and the verifier fails the build on drift:

| Route | Measured | Why |
|---|---|---|
| S deploy → OBJ A | **130.000 m** | Equals the map's half-length; under the 220 m sightline ceiling |
| N deploy → OBJ A | **130.000 m** | **Equal to the south figure to the millimetre.** `check_spec()` fails the build if they differ by more than 0.5 m |
| OBJ A → OBJ B | **62.0 m** | Short second leg; the round is decided at the span and then played out at the gate |
| OBJ A → S deploy (rotation) | ~130 m | The out-of-play rotation |
| East ramp, lip → bed | **133 m at 17.6°** | Walkable flank cost. No pitch exceeds the design grade |
| West ramp, lip → bed | **142 m at 16.2°** | ~9 m longer, and its foot is in the open |

**The northern overwatch is a known asymmetry.** From `y = +130` the northern deployment has a partial view
down the gorge to the southern approach; the southern deployment cannot reciprocate. This is recorded here
rather than hidden, exactly as Dry River §6.1 records Bravo's 51.9 m advantage. Under sequential order it
is **not exploitable**. If a later layer switches this map to parallel objectives, it becomes decisive and
must be rebalanced **by terrain** — moving OBJ B south or the northern deployment east — never by changing
team capability (ADR-003).

### 4.3 The gorge and the bridge

**The 20 m rule versus a 68 m span.** Dry River's §5 sets a 20 m maximum open crossing: beyond it a moving
player is a free kill. A 68 m bridge deck is 3.4× that, and the honest reading is that **the deck violates
the project's own cover contract.** The design does not pretend otherwise. It makes the deck the map's one
deliberate exception and mitigates it in four specific ways, all of which must be present in the blockout
or the exception is not justified:

| Mitigation | Value | Effect |
|---|---|---|
| Truss uprights, both sides | **20 bays of 3.4 m** | 21 per side. Intermittent hard cover, chest-to-head height |
| Lamp standards | every 5th upright, i.e. every **17 m** | 5 per side, **9 distinct** (the two at the abutments are shared pairs). Landmark rhythm and a rarer cover beat |
| Parapet / kerb | **1.05 m** | The Dry River rail height — crouch cover, and it makes the deck a *firing step* rather than a flat lane |
| Deck width | **7.5 m** | Room to fight, dodge laterally and fall back along the lane rather than queue on it |

A 68 m span is the *most* the mitigation can absorb. Widening the gorge to 90 m would make the deck a pure
shooting gallery; narrowing it to 45 m removes the second lane's value. **68 m is the design's load-bearing
number and the one most likely to need revisiting after playtesting.**

### 4.4 The creek bed — the second lane

The bed at `z = −18` is playable, not decoration. Two **traverse ramps** reach it, and the shape of those
ramps is the result of measuring rather than taste.

**Why the ramps run out sideways.** The first attempt sent each ramp east and west to `x = ±60` and dropped
32 m in 91 m of run. The verifier measured 1.54 m steps over a 2 m sample — a 38° pitch, impassable. The
cause is arithmetic: the gorge is 32 m deep with 76° walls, so a ramp heading straight for the deep centre
has almost no horizontal run available to it. The fix was to use the map's **width**, which the first attempt
ignored — and to run *out along* the wall, where the ground is high, so the track is a cutting rather than a
15 m embankment. Both ramps now run east and west to `x = ±92 / −98` and take 133 m and 142 m.

**Why the plan is smoothed but the height is graded separately.** Two earlier passes smoothed the whole 3D
polyline with corner-cutting, and both produced a 40–47° apex at the turnaround — the plan direction reverses
there, so the horizontal run cancels while the drop does not. No amount of hand-tuning the control points
fixed it, because the curve was doing the damage, not the points. The generator now smooths the **plan only**
and lays a constant grade along the measured arc length, which makes the steepest pitch a stated design
property (22° cap; actual 17.6° and 16.2°) rather than a side effect of where the corners land.

From the bed floor it is ~34 m of open, boulder-covered ground to mid-span — and from that floor a player can
look **up** at the deck.

This is the map's best idea and it is what separates Ravenshoe from a corridor:

- The deck and the bed **mutually flank**. A player on the span is covered from below; a player in the bed
  is covered from above. Neither lane is safe, and the choice is a real one.
- The bed is reached from **both** ends, so it is a genuine rotation, not a one-way drop.
- It is **worse** than the deck by design: 34 m of open bed against 68 m of trussed deck, no lamp rhythm,
  and boulders rather than uprights, at roughly twice the distance. A player who takes it is trading a small
  risk for a large time cost — which is what makes it a decision rather than a dominant strategy.
- It is the natural place for **OBJ A's fallback**: losing the span should not end the round.

**Guard against one failure mode.** If the bed is a reliable free flank, the map degenerates into two
independent battles either side of a bridge nobody crosses. The counter is that both ramps are long, graded
and *visible from the span* — a player descending is inside the bridge's sightline for most of the descent
before reaching cover. The ramps are deliberately **not** symmetric: the west is 9 m longer and its foot
sits in the open.

### 4.5 The gatehouse

Granite rubble, **9.6 m wide × 6.8 m deep × 6.0 m high** including the parapet coping, with a
**3.4 m wide × 3.6 m high** arched road passage through the long axis. Walls stand to **4.6 m** eaves with a
**1.2 m** parapet, so there is 1.0 m of spandrel over a 3.6 m arch crown — the proportion a 3.4 m granite
span actually needs. The passage is the objective, so the building is a hard cover volume with one soft,
contested mouth.

The passage is the map's "door": from `y = 0` the far bank reads as a building with a lit opening at the
end of the axis, and the objective is *through* it rather than *on* it.

The arch is **original** and modelled as a **17-stone segmental arch**, not a semicircle. A semicircular arch
over a 3.4 m span would rise 1.7 m and demand a 5.3 m wall; 1.0 m of rise is what would be built in granite.
The spandrel above the arch is built as **vertical slices from the intrados curve up to the eaves** —
building it as a flat slab leaves holes at the haunches, which is the easiest way to make an arch look wrong.
The verifier ray-casts the passage end to end at standing and head height, and casts at head height *above*
the crown expecting solid, which is what proves the building has a roof and is not two walls.

### 4.6 Approach cover

Above Dry River's rules, and stated here so the verifier can check them:

| Rule | Value |
|---|---|
| Maximum open crossing **off the deck** | **20 m** — Dry River §5, unchanged |
| Maximum sightline | **220 m** — Dry River §5, unchanged. The map's axis runs its full 300 m end to end, which is the **one sanctioned exception** and is why the flanks are built up with rock and treeline |
| Minimum engagement range | **5 m** — enforced by the gatehouse passage and the ramp bottoms |
| Cover density | 1 object per **12 m** of intended route |
| Hard : soft ratio | **1 : 3** |

---

## 5. Asset plan

### 5.1 What must be built original

| Asset | Why original | Built as |
|---|---|---|
| **Iron truss bridge** | No bridge mesh exists in the project or in any installed pack. 430 keyword hits across `Content/` for bridge/gate/arch/tunnel/pier/stone/wall returned rock ledges, stone *materials* and Lyra audio — **nothing structural** | `SS_Raven_Bridge.fbx`, 852 faces, authored with the **deck top at z=0** so the placement anchor is the road surface |
| **Stone gatehouse** | As above. Singapore_Canal has Asian canal masonry and is ruled out on look and culture (ADR-016) | `SS_Raven_Gatehouse.fbx`, 450 faces, authored at its **real position** `(0, 62)` and rebased to its own footprint centre with base at 0 |
| **Gorge, ramps, road, terrain** | Assembled from dressed Quarry Slate ledges at dress time; the heightfield itself is ours | `SS_MAP_Ravenshoe_01.fbx`, 15,000 faces, 2 m grid |

**Class F — original, no third-party dependency** (L-0011, ADR-013, ADR-020). The same reasoning already
recorded for the Red Gum homestead in `ASSET_REGISTER.md` **M-RG-01a**, and for the same kind of reason:
*the packs that do have structures are the wrong continent or the wrong culture.*

**What this reuses, and from where.** Nothing third-party is modelled or copied. What the generators borrow
is our **own** class F work and our own house conventions: the primitive/join/export helpers follow
`redgum_homestead.py`; every dimension is read from `Tools/Common/ravenshoe_spec.py` so the verifier and the
generator cannot disagree; and the base-at-origin convention, flat shading, 2 m box-projected UVs and the
measured-footprint CSV columns are the Red Gum homestead's, because the import pass is the same and a second
convention would be a second class of bug. The gorge walls, boulders, scrub, gum trees and fences that dress
this are Class A pack meshes referenced in place, never reskinned.

**Two placement conventions, deliberately different, and both documented in the CSV.** The bridge is placed
by its **deck level** (`z_m = 14.0`) because its anchor is the road surface, not its underside — its abutments
reach 8.8 m below the deck by design. The gatehouse is placed by its **base** (`z_m` = the traced road
surface, `base_z_m = 0.000`) because it stands on the ground. `z_m` is authoritative for both; `base_z_m`
is diagnostic and exists so the importer can *assert* the convention rather than assume it.

### 5.2 What dresses it, from content already in the project

All Class A under **L-0016**, referenced in place and never modified.

| Source | Used for | Note |
|---|---|---|
| `Scene_QuarrySlate` | Gorge rock walls, boulders, scree, gravel, the road surface | Best rock in the project. Dry River already tints it (`MI_SS_Ironstone_MI_Qua_Sla_*`) — that tint set is the material reference |
| `RuralAustralia` | Eucalypts on the ridge, treeline above the gorge, fences on the approaches, ground texture, scatter | Same pack as Red Gum (ADR-022) |
| `Namaqualand` | Dry scrub, stones, dead branches on the bed and the scree | The South African wildflowers are **not** used — the setting must read Australian (ADR-016, as recorded in L-0016) |
| `Modular_Rural_Cabin` | Sparse pine on the shaded north-facing slope | The only other vegetation source |

**Deliberately not used:** `Singapore_Canal` (Asian canal/urban — wrong look, previously ruled out),
`Insurgent_2` (never used, ADR-016), and every weapon/character/VFX/animation pack in the cache, which are
irrelevant to a map.

### 5.3 The VaultCache finding

The producer pointed at `Content/Downloaded/VaultCache/` (19 folders, ~36 GB) expecting new assets. **It
contains no new assets.** All 18 content roots are **already installed** in `Content/` and reachable by
path:

> AK-47 · FPS_Weapon_Bundle · FP_AKS74U_Animation · Insurgent_2 · M1911 · Military_Radio · Modern_Insurgent_7 · Modular_Rural_Cabin · Namaqualand · Nanite_Plants_Sample_Collection · QuantumCharacter · Realistic_Starter_VFX_Pack_Vol2 · RuralAustralia · SampleAnimationPack · Scene_QuarrySlate · Singapore_Canal · World_Flags

The nineteenth folder, `VisAICom`, is a VFX/common pack and is not imported; it has no map geometry.
`FabLibrary` (22 GB) is the Fab desktop cache, not project content.

**Consequence for the licence register.** Nothing is imported for this map, so this map adds no new
third-party dependency. But the inventory surfaced a **pre-existing gap**: nine of the installed packs
above have no row in `LICENCE_REGISTER.md` or `ASSET_REGISTER.md`, including `Scene_QuarrySlate`, which
Dry River and this map both build on. L-0016's own rule is that no third-party asset enters the repository
without a row. That is fixed in this session as bookkeeping — see `LICENCE_REGISTER.md` **L-0016 (revised
2026-09-28)** and the **L-0016b** entry.

---

## 6. Verification — what was checked, and what could not be

`Tools/Blender/verify_ravenshoe.py` runs in two modes and currently reports **53/53 passing**. The split
matters: the spec mode runs in CI with no Blender, and the geometry mode ray-casts the built meshes.

**Spec mode (no Blender, runs in CI).** Deployment symmetry (S→A and N→A equal to within 0.5 m — measured
130.000 m each); the 220 m sightline ceiling on every approach; the deck mitigation existing at all
(bay ≤ 4 m, uprights present, deck ≥ 6 m); the 20 m open-crossing rule along all six intent routes; **worst
single pitch** on both ramps as well as their average grade; and that no cover marker lands inside the
gatehouse.

**Geometry mode (Blender, ray-casts the actual meshes).** This is the half that matters, because
re-asserting that the spec still says 3.4 m bays proves only that the spec still says 3.4 m bays:

| Probe | What it proves |
|---|---|
| Vertical rays at five points along the deck | The deck is continuous walkable surface at the authored level |
| Rays at `y = +42, +60` | No bridge structure over open ground beyond the abutments |
| Ray on the parapet line | Parapet top is at 1.50 m, i.e. real cover and not a railing |
| Ray **along the road axis** at standing and head height, through the gatehouse | The passage is a real hole — a player can walk and shoot through it |
| Ray above the arch crown | The spandrel is solid — the building has a roof and is not two walls |
| Rays either side of the opening | The piers are solid — the passage is not wider than `PASSAGE_W` |
| Gatehouse base and centre | It stands on the measured road surface, centred on objective B |
| Terrain at bed, lips, road samples | Gorge depth, road continuity, deck level |
| South wall sampled every 2 m | The wall descends **monotonically** lip to bed |
| Ramps sampled every 2 m | Continuous surface, grade under 32° on the mesh, tracking the spec line |

Four real defects were found this way and none of them were visible in the spec:

- **The arch ring ran below grade.** The voussoir sweep used `asin` where it needed `atan2`, because the arch
  centre sits below the springing line. The outermost stones ended up 0.44 m underground while every number
  in the spec stayed correct. Only a ray cast through the passage found it.
- **The gatehouse sat inside the bridge at mid-span.** It was authored at the origin on the assumption the
  layout CSV would place it — true of the FBX, false of the `.blend`, which is the authoritative artwork.
- **`rebase()` silently did nothing.** It computed its offset from `matrix_world`, which is not refreshed
  until the depsgraph updates, so straight after `join()` the offset came out as exactly zero and the
  gatehouse finished 2.3 m buried with no error anywhere. The generator now refuses to save if the measured
  base is not 0.
- **Footprints were measured from the world origin,** so a building standing at `y = 62` reported a 130 m
  footprint. Any keep-out test or seating assertion reading that would have cleared a 65 m radius around
  objective B.

**Not checked, and not checkable here.** Navigation is **not baked** — `BUILDPATHS` in a commandlet crashes
(Red Gum finding), so this must be done in the interactive editor. And no sightline or exposure figure is
quoted anywhere in this document, because `line_trace_single` in a `-nullrhi` commandlet cannot hit
`StaticMeshActor`; every cover/sightline number from `audit_map_playability.py` is invalid for every map.
Those two must be measured in-editor or in-game.

---

## 7. What this map does not do

- **Navigation is not baked.** The `NavMeshBoundsVolume` is placed and the engine auto-created a
  `RecastNavMesh-Default`, but it carries **no baked data** — 0 of the 433 actors are on a navmesh and
  neither ramp is confirmed traversable by an agent. Bake it with **Build ▸ Build Paths** in the
  interactive editor. **Not** by `BUILDPATHS` from a commandlet, which crashes (Red Gum finding).
- **No sightline or exposure figure is quoted**, because none can be measured from a commandlet. See §6.
- **It has not been playtested.** The 68 m span, the bed as a second lane, and the 8 v 8 team size are all
  design arguments awaiting a round.
- **The originals are still greybox.** The bridge, gatehouse and terrain carry four authored *constant*
  materials (`M_SS_Raven_Iron/Stone/Deck/Terrain`). The visual quality in the map right now is almost
  entirely the pack dressing, which brings its own PBR materials. A proper art pass on the originals is
  outstanding, and the terrain in particular has no ground texture.
- **It does not replace Dry River** as the vertical slice test bed, and does not displace Red Gum.
- **It has no vehicle content.** The reference screenshots show a vehicle on the deck; Southern Spear is
  infantry-only through Phase 1 and adding a vehicle would change the map's whole threat model.
- **It has no snow gameplay.** Snow is dressing on the north-facing slopes. A slippery-surface traversal
  mechanic is a locomotion project, not a map project (ADR-024).
- **It does not claim a third objective.** The reference has an A/B/C structure; this map is A/B only,
  because three sequential objectives across a 300 m map is a longer round than the slice budget allows.
- **It is not a competitive map.** The deck is deliberately a lane you can be caught in. That is the
  lesson, and it is a lesson about chokepoints, not about skill ceilings.

---

## 8. What still blocks sign-off

1. **Bake navigation in the editor** and confirm both ramps and the bed are traversable for agents, not
   just players. A 17.6° grade is fine for a pawn and may not be for a nav agent.
2. **Playtest the 68 m span.** The whole cover contract mitigation (§4.3) is unproven. If the deck is a meat
   grinder, the answer is *widen the deck and narrow the span*, not add more cover props.
3. **Confirm the creek bed is a lane, not a trap.** §4.4 is the map's best idea and its biggest unknown.
4. **Art pass the terrain.** ~~Constant materials only.~~ **Done for the bridge, deck and masonry**
   (ADR-030, M-008m): generated gravel, rust ironwork, painted steel and coursed granite, on the
   project's own `M_SS_ScanPBR`. **Still to do:** the terrain still carries a flat safety-net material
   and is the largest surface on the map. It needs its own dry high-country ground set at the terrain's
   4 m UV scale, and the road corridor wants a different, coarser treatment from the open ground.
5. **Wire the Objective Assault layer.** The two `SSObjectiveActor`s and two `PlayerStart`s are placed and
   labelled, but the map is not yet attached to `B_SS_ObjectiveAssault` the way Dry River is.
6. **Decide the 8 v 8 team size** honestly — the layout is designed for it, but the slice runs 4 v 4 and a
   4 v 4 round across this map may be over in ninety seconds.
7. **Lighting.** A gorge at midday is a hard-contrast problem; Dry River §9b has the precedent to follow.
8. **Look at it with a player in it.** Everything above is a measurement or an argument. None of it is a
   round.

---

## 9. In Unreal

`Tools/Unreal/import_ravenshoe.py` creates the map, imports the three original FBXs, authors four constant
materials, places the geometry, replaces all 68 greybox cover markers with real pack meshes, and adds the
dressing layer. `Tools/Unreal/audit_ravenshoe.py` then re-opens the saved `.umap` and measures it.

| | |
|---|---|
| Map | `/Game/Maps/L_Ravenshoe_01`, 748,423 bytes |
| Actors | **467** — 3 originals, 220 cover/dress, 204 dressing, 34 props, 1 nav volume, 4 gameplay, 1 engine navmesh |
| Placed by the import | 424 pack-dressed actors, 0 removed, 0 missing assets |
| Placed by the prop pass | 30 meshes + 4 VFX actors, 0 missing assets |
| Pack sources used | `Scene_QuarrySlate` (ledge/rock clusters), `RuralAustralia` (trees, logs, fences), plus the 2026-09-28 Fab prop downloads (L-0016c) |
| Audit | **35/35 pass** (`Build/ravenshoe_audit_report.json`) |

| Dressed | Count | Source |
|---|---|---|
| Layout cover markers | 68 (35 rock, 33 bush) | Quarry Slate + Rural Australia |
| Gorge wall ledges | 86 | Quarry Slate ledge clusters |
| Creek bed boulders + driftwood | 54 + 12 | Quarry Slate, Rural Australia |
| Ridge treeline | 76 | Rural Australia gums, collision off |
| Approach post-and-wire | 64 + 64 | Rural Australia, collision off (ADR-022) |
| Burning wreck + fire | 1 mesh + 4 VFX | Red car wreck, VFX pack |
| Second wreck (creek bed) | 1 | Abandoned & junk Car |
| Fuel drums | 7 deck + 3 gatehouse | Fuel barrel |
| Sandbag hard cover | 8 | Military Trenches sandbags |
| Corrugated cover panels | 4 | Military Trenches wall |
| Ridge silhouette | 1 windmill + 1 barn | Windmill, Barn |
| Water tower | 1 | Water Tower, set back at (14, 78) |
| Hand pumps | 3 | Hand Water Pump, at the road edge on both approaches |

**Verified on the saved map, not asserted by the importer:** terrain at the origin; bridge deck at exactly
**1400.0 cm**; gatehouse at **(0, −6200, 1523.6)** matching the spec's road height; all three originals
blocking; and both deployments at **13000 cm from objective A** — the fairness property the whole layout is
built around, measured on the map rather than recomputed from the spec. The prop layer is measured the same
way: the wreck sits at **z = 14.00 m** on a 14.00 m deck, inside the 7.5 m bridge footprint, **blocking**,
and carrying an authored `ScanPBR` instance; all four VFX actors still hold a live Cascade template after a
save and reload.

### The burning wreck

The deck's only hard cover at mid-span is a burnt-out car sitting across it at **22°**, doors thrown open.
That is 3.5 m of width on a 7.5 m deck, so it is cover without sealing the bridge — there is still fighting
room down both flanks, which is the whole point of a wide deck. It is skewed rather than square-on so it
reads as a casualty that came to rest against the parapet, not a barricade someone placed. Seven fuel drums
are strewn between the wreck and the parapet, four of them upright and three on their sides: that is why it
is burning. A second, flatter wreck sits in the creek bed, so the lower lane gets the same read.

This is dressing a **derelict** vehicle on a road that was closed, and it carries no faction, no insignia
and no operation (ADR-016).

### The prop pipeline

Vendor FBX arrives in the author's own units, axis order and ground-plane state, so nothing is imported
raw. `Tools/Blender/probe_fab_props.py` measures each file; `prep_fab_props.py` resizes it to real-world
scale, strips the vendor's ground plane, re-pivots it base-at-z-0 and decimates to a stated budget;
`render_fab_props.py` renders it beside an exact 1 m cube so the result can be *looked at* before import.

The measurement pass is what justified the work rather than the guesswork. The red Renault authors at
**27.3 × 21.0 × 11.2 m** with **1,166,165 triangles** — because it is a scan carrying a ground plane at
roughly six times real scale. After prep it is a 4.60 m car at 23,323 triangles. A cross-section profile
confirms the 3.5 m width is the open doors, not a mis-scale: the body is 1.7–2.1 m across and only widens
to 3.5 m between the door hinges. The hand pump is the same story at smaller scale: it authors at
**5.85 m** tall and comes out at **1.6 m**, human height. The compressor was rejected at 73,622 triangles
for a 2.5 m prop, and the trench debris at 19,751 triangles for a flat 0.77 m piece.

### Materials: one shader, many sources

All six prop materials are instances of the project's own parameterised `M_SS_ScanPBR`, not copies of the
vendor materials. That parent exposes `Tint`, `Tiling` and `BaseColor`/`Normal`/`Roughness`/`AO`/
`Metalness` slots, so pack textures from several different packs feed **one** shader. The wreck pack ships
an albedo and a grunge map and **no** normal, roughness, AO or metalness, so the unset parameters are read
off the working `MI_SS_CorrugatedIron` rather than guessed — leaving them unset falls back to the parent,
whose defaults are tuned for a scan, not for a car panel.

### Unreal findings worth keeping

- **`EditorLevelUtils.new_level` does not exist in 5.8.** The level API is
  `LevelEditorSubsystem.new_level(asset_path, is_partitioned_world=False)`, and it returns a **bool**, not a
  world. The first import run stopped on "could not create" with no warning recorded at all.
- **Neither `print()` nor `unreal.log()` reaches the log file in this commandlet.** The report JSON is the
  only reliable channel, which is why every step in both scripts is recorded there rather than logged. A
  probe that reports on stdout reports nothing.
- **`unreal.BrushType` has no `BRUSH_NAV` member**, so a nav volume cannot be built from a `Brush` on this
  engine version. `unreal.NavMeshBoundsVolume` spawns directly and is what this pass uses.
- **`EditorLevelLibrary.get_editor_world()` returns a blank *untitled* level if you have not opened a map
  first.** Placing into it succeeds, reports clean, and is discarded — the `.umap` on disk never changes.
  The first prop pass reported 26 actors placed and 0 errors against a file that was byte-for-byte
  unchanged. The pass now loads the map explicitly and refuses to dress anything that does not have the
  three `SS_Raven_Geo_*` actors and a terrain.
- **A runtime-added `ParticleSystemComponent` cannot be persisted from a Python commandlet in 5.8.** There
  is no `Actor.add_instance_component`, no `ActorComponent.register_component` and no
  `EditorActorSubsystem.add_actor_component`; `call_method` into them raises *Failed to find function*.
  Components made that way are not owned by the actor, so the saved level has none of them. What does
  persist is a component property on a placed actor, so the fire is placed as instances of the VFX pack's
  own `Spawn_Particle` Blueprint with the template set per instance. Verified across a save and reload.
  `unreal.ParticleSystemActor` does not exist either.
- **Every route to a `StaticMesh`'s material *slots* is a silent no-op in 5.8.** Writing into the array
  returned by `get_editor_property("static_materials")` changes local copies; assigning it back with
  `set_editor_property` does not persist either; the slots read back `[None, None]`. The per-instance
  override `StaticMeshComponent.set_material(i, mat)` is a real component property, survives a reload, and
  is what actually renders — so that is where the prop materials go.
- **A Blender script must resolve paths from `__file__`, not `bpy.path.abspath("//")`.** With
  `--factory-startup` the blend path is empty and `//` resolves to the drive root, so renders were written
  to `C:\Build\` while the report claimed the project directory.
