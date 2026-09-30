# NEXT PRIORITIES — what the game needs, in order

**Document ID:** `Docs/NEXT_PRIORITIES.md`
**Written:** 2026-09-30, from the producer's playtest verdict and the measured state of the repo
**Read with:** `CLAUDE.md` → `Docs/HANDOVER_CLAUDE_CLOUD.md` → the latest `Docs/CHANGELOG.md` entry

This document answers one question: **what should be built next, and why.** Everything in it is either
measured from this repo or sourced from a public specification, and anything unmeasured says so.

It does not replace `Docs/PLAYER_MODEL_PLAN.md` (the character work, which is measured and ordered) or
`Docs/PROJECT_AUDIT.md` (the risk register). Where those already have detail, this links to them instead
of repeating them.

---

## 1. The producer's verdict, and what it measures

Three complaints from play, in the producer's words: the **character models look horrible**, the
**weapons are not looking great** and need better textures, the **VFX need work**, and the weapons need
**zeroing and recoil** built on real-world data.

The order the producer gave is also the right dependency order, and it is not a preference:

```
models ──▶ animations ──▶ VFX ──▶ maps
   └──────────────────────▶ weapon textures ──▶ recoil / zeroing
```

**Why models gate animations:** an animation retargeted onto a body that is about to be replaced is
work thrown away. The friendly body decision (ADR-042, Quantum on its own skeleton) means the retarget
target is settled, so this is now unblocked.

**Why textures gate recoil:** recoil is read off the weapon. A muzzle-climb model tuned against a
placeholder mesh will not survive the real geometry and texture, because the perceived mass of a rifle
comes mostly from its surface — a flat grey gun and a camo'd one with a full-length rail do not kick
the same way to the player even with identical numbers.

**Why maps come last:** every map pass before the art is fixed is a pass that has to be redone against
better assets. Dry River was overhauled this session (D-DR-01..07) and reads well; the remaining map
work is gated on art, not on geometry.

---

## 2. Priority 1 — Character models

**State: Quantum body live (ADR-042, Session 087), appearance not accepted.** The producer's "horrible"
is a look verdict on a model that now renders correctly and is dressed with the ADFRC vest and helmet.

Ordered plan, from `Docs/PLAYER_MODEL_PLAN.md` §4 (P1–P5), with this session's additions:

| # | Task | Why first | State |
|---|---|---|---|
| P1 | **Fix the texture pipeline** | 53% of the uniform texture sheet is flat fill (PLAYER_MODEL_PLAN §2.1). This is the single largest contributor to "looks horrible" and it is not a modelling problem | `IN_PROGRESS` — camo was routed through `FriendlyMaterialOverrides` this session and is **not yet captured in game** |
| P2 | **Own the skeleton** | R-58: the soldier is welded to the Manny skeleton; the retarget to Quantum is a mitigation, not the fix | Open |
| P3 | **Physics asset and LODs** | R-59: ~90k verts with no LODs | Open |
| P4 | **The flat under-shirt** | Decide, then finish | Open |
| P5 | **Make "does the soldier look right" repeatable** | A fixed camera, fixed light, one pose. Session 067 already built this; it is not written up as a script | Open |

**Measurement, not adjectives.** P5 exists because the canopy-height defect in Session 084 was found by a
screenshot and missed by a passing placement report. A look verdict with a repeatable capture behind it is
the only kind that can be closed.

---

## 3. Priority 2 — Weapon textures

**State: ADFRC source textures are on the gun; the finish is unverified.** `Build/weapons_setup.json` shows
the A88 carrying `adfrc_ef88_co`, `mbus_front_co`, `mbus_rear_co`, `adfrc_spectr_co`, `adfrc_spectr_ca`
— five texture slots from the converted ADFRC pack. So the *source* is right; what is unproven is how it
reads in game.

Known texture problems, measured or reported:

| Problem | Evidence | State |
|---|---|---|
| Only `T_ADFRC_DPC_camo.uasset` is committed under `Content/Art/Characters/ADF/` | `git ls-files` | Weapon textures are **not in the repository** at all — they live in the git-ignored Sourced tree (L-0021, ADR-021) |
| Weapon meshes read as flat/untextured in game | producer screenshot | Unverified in this session's builds |
| No roughness/metalness separation on most ADFRC maps | the pack ships albedo + a grunge map and **no** normal/roughness/AO/metalness | Known; same finding as `ASSET_REGISTER` M-008l |
| `WID_SS_*` definitions are copies of Lyra's | `strings` on `WID_SS_A88.uasset` returns no authored stat keys | See §6 — this is also why recoil is generic |

**The fix is a project-owned material, not a better vendor texture.** `M_SS_ScanPBR` already exists as the
project's parameterised master (`Tiling`, `Tint`, `BaseColor`/`Normal`/`Roughness`/`AO`/`Metalness`) and is
what the Ravenshoe prop materials use. Point the weapons at `MI_SS_*` instances of it, add the missing
normal/roughness maps as project-authored textures, and the weapon look becomes a tunable parameter
rather than a baked vendor surface. That is also the mechanism that makes §6 reproducible.

---

## 4. Priority 3 — VFX

**State: the two systems that work are casing eject and muzzle light; muzzle flash is unplaced.**

| Effect | State | Next |
|---|---|---|
| Casing eject (`SSShellEjectSubsystem`) | In, tested (`SouthernSpear.Bridge.Casings.*`, 2 tests) | — |
| Muzzle light (`SSMuzzleLightSubsystem`) | In, tested (1 test) | — |
| **Muzzle flash** | **Lyra's `NS_WeaponFire_MuzzleFlash_Rifle` exists but was never placed.** Candidates listed in `Docs/evidence/vfx_muzzle_candidates.json` | Place it, capture it, then tune scale/intensity per weapon class |
| Impacts | `NS_ImpactConcrete`, `NS_ImpactGlass`, `NS_ImpactDataChannel`, `NS_ImpactDecals` present | Verify each surface type has a real impact; add dirt/sand/rock for the Dry River palette |
| Tracers, dust, weather | `PLACEHOLDER` per `ASSET_REGISTER` 4.7 | Deferred |

**Tracers are the notable gap for a shooter.** A tracer is what makes a 300 m shot legible to a player, and
`ASSET_REGISTER` E-002 still reads `PLACEHOLDER`. At Dry River's engagement ranges it matters more than at
close quarters.

---

## 5. Priority 4 — Weapon zeroing and recoil, from real data

This is the one item with **no measured baseline at all**, so it gets the most detail.

### 5.1 What "zeroing" means here, precisely

Two different things get called zeroing. Both are wanted; they are separate systems:

1. **Weapon zero (sight alignment)** — the sight is aligned to the bore at a stated distance, so the
   point of aim and the point of impact coincide there. Real weapons have a zero set by the shooter or
   the unit. In game this is one number per weapon: the range at which the crosshair is true. It is a
   property of the *weapon and its optic*, not of the player.
2. **Zeroing in (player-adjustable)** — letting the player dial the optic to a range. Nice to have; it is a
   UI and state problem on top of (1), and it is not first.

3. **Recoil** — the muzzle climb per shot and how fast the sight comes back down. This is what the player
   feels and what the numbers in §5.3 feed.

### 5.2 The measured baseline: there is none

`WID_SS_A88`, `WID_SS_A416`, `WID_SS_A4`, `WID_SS_A25`, `WID_SS_A89` and `WID_SS_A88G` are **copies of
Lyra's rifle definitions** (`Docs/HANDOVER_CLAUDE_CLOUD.md`, weapons pipeline). A `strings` scan of
`WID_SS_A88.uasset` returns no authored recoil, spread, dispersion, damage or range keys, and
`B_SS_A88_Weapon` references only Lyra's `/Game/Weapons/B_Weapon`.

**So all six weapons currently fire with one generic rifle's recoil, including the LMG.** That is the
defect. It is also why the producer can feel it before seeing it.

### 5.3 Real-world data

Every figure below is from a public specification. **Ranges are given as ranges** where the sources
disagree, rather than averaged into a false precision.

| Weapon (in game) | Cartridge | Muzzle velocity | Muzzle energy | Feed | Rate of fire | Effective range | Source |
|---|---|---|---|---|---|---|---|
| **EF88** (A88, A88G) | 5.56×45 NATO | ~940 m/s (typ.) | ~1,700 J (derived) | **30-round box** | **680–850 rpm** | **300 m** | Australian Army, F88 Austeyr equipment page; Navy capability page |
| **F89** (A89) | 5.56×45 NATO | — | — | **100 or 200-round box, belt capable** | 750–1,000 rpm (Minimi 5.56) | **400 m point / 600 m area** | ADF Navy, F89A1 Minimi page; FN Minimi 5.56 Mk3 |
| **M4-pattern** (A4) | 5.56×45 NATO | 880–910 m/s | ~1,550 J (derived) | 30-round box (STANAG) | 700–950 rpm | 500 m point | Standard published service data |
| **HK416** (A416) | 5.56×45 NATO | **790 m/s** (HK) / ~730 m/s (other sources) | **1,250 J** (HK) | 30-round box | 700–850 rpm | 400 m point | Heckler & Koch product page; Wikipedia |

**Derived figures are marked as such.** Muzzle energy above is `½·m·v²` from the quoted velocity and the
5.56 NATO SS109 projectile mass (~4.02 g). It is arithmetic on the cited velocity, not a sourced number,
and it is only used here to rank the weapons against each other.

### 5.4 What the data actually implies for game feel

**The ranking is not the interesting part. The shape differences are.** Four things follow from the table
that a generic rifle model cannot express:

1. **The A89 is a different weapon, not a bigger one.** Its 100/200-round box feed and belt capability are
   mechanical facts, and they are the whole reason an LMG feels different in a shooter: *sustained fire
   without a reload*. Its per-shot recoil should be **comparable to the A88**, not higher. What differs is
   time-on-target before the gun goes empty. This is the single most likely thing to get wrong.
2. **The A416 (HK416) should be the hardest-hitting 5.56 in the arsenal**, because HK quotes the lowest
   muzzle energy (1,250 J) and a piston/short-stroke system with a large vertical component. A player who
   switches to it should feel a distinctly different, more vertical climb — and it should be *controllable
   but demanding*, which is the character of the real weapon.
3. **The A88 and A88G are the same gun** and must share recoil numbers exactly (ADR-004: one gameplay
   definition, cosmetics only). They differ in sight and texture, never in ballistics.
4. **Effective ranges map to engagement design, not to falloff damage.** EF88 300 m vs F89 600 m area is
   the gap that makes the LMG role worth taking on Dry River, whose sightlines are long (§6 of
   `MAPS_DRYRIVER.md`). Do not model it as damage falloff over 300 m — the rifle is lethal well past its
   effective range; "effective" is about hit probability for a trained shooter.

### 5.5 One warning about recoil numbers

**Free recoil energy is not a game recoil value.** The physical figures above rank the weapons correctly,
but a shooter game's camera kick is tuned for readability at 60 fps, not for Newton's third law. The real
data should set the **ordering, the magnitude ratios and the zero distances**; the absolute per-shot
degrees should be tuned by playtest against those ratios.

The data-derived quantities that should be treated as fixed are the **zero distances** (300 / 400–600 /
500 / 400 m) and the **feed and rate-of-fire limits** (what empties the gun, and how fast). Those are
facts about the weapon. Per-shot climb and recovery are feel, and should be tuned with the producer in a
round rather than derived on paper.

### 5.6 Where the numbers have to live

Per §3, in a **project-owned data asset** — one `FSSWeaponBallistics` row per weapon id — and applied
through `SSExp_ObjectiveAssault` material/component overrides. It must not be edited into Lyra's assets
(ADR-004, "do not modify vendored Lyra"), and it must not be hardcoded in C++, because the cloud session
cannot compile or playtest it (§1 of the handover: put the rules in an engine-free header/data file that
`python` can check). `Tools/Common/` with a `test_*.py` is the proven pattern here.

---

## 6. Priority 5 — Maps

**State: Dry River overhauled and reading well (Session 088, D-DR-01..07 closed or explicitly deferred).**
The remaining map work is art-gated, not geometry-gated.

| Map | State | Gated on |
|---|---|---|
| Dry River (M-001) | Overhaul complete; 2 producer defects still open | **R-92** kangaroo grey, **R-93** water unverified in game |
| Red Gum (M-002) | `MAPS_PLAYABILITY_AUDIT.md`: 17% nav coverage, 12 hard cover — not playable as it stands | Art, then a nav pass |
| Wandarra (M-009) | Built, dressed, nav not baked | **R-82** attended bake |
| Ravenshoe (M-008) | Built, dressed, nav not baked | **R-82** attended bake |
| Bluestone (M-005) | Built, on the operations menu | Fine-tuning |
| Saltbush (M-004) | Best audited map (7 pass / 3 fail) | — |

**R-82 is the single blocker for three maps** and needs an attended editor session on this machine;
headless `BUILDPATHS` consumes no new geometry. It is cheap in effort and unblocks the most map play.

---

## 7. What is NOT on this list, and why

- **Casualty care (ADR-040).** Steps 1–2 are built and passing; step 3 is the Lyra bridge and it is
  blocked on reading the 5.8 Lyra source first (prompt C in the handover). Real work, but it is a
  *feature*, not a defect, and the producer's verdict was about how the game *looks and feels*.
- **Dedicated server (R-09).** Blocked on the engine distribution. Not actionable.
- **Licence questions.** None open. Every asset is cleared (ADR-035); record provenance, never hold back.

---

## 8. One-page order of work

1. **Weapon textures** via `M_SS_ScanPBR` instances — unblocks everything visual, and is the substrate the
   recoil tuning is read against. (`ASSET_REGISTER` M-008l already does this for props; the pattern exists.)
2. **Muzzle flash + impacts + tracers** — place what exists, author tracers.
3. **Ballistics data asset** — zero distances from §5.3 as fixed, climb tuned by playtest, A89 sustained
   fire as a reload-interval rule rather than extra kick.
4. **R-82 attended nav bake** — unblocks three maps in one session.
5. **Character P1–P5** — in parallel, owned by the character thread; do not duplicate that work.
6. **R-92 / R-93** — the two remaining Dry River defects, both with a measured root cause already recorded.

---

## 9. Sources

- Australian Army, *F88 Austeyr* — `army.gov.au/equipment/small-arms/f88-austeyr`
- Australian Navy, *EF88 Austeyr* — `navy.gov.au/capabilities/weapons/ef88-austeyr`
- Australian Navy, *F89A1 Minimi* — `navy.gov.au/capabilities/weapons/f89a1-minimi`
- FN Herstal, *FN MINIMI 5.56 MK3* — `fnherstal.com`
- Heckler & Koch, *HK416* — `heckler-koch.com` (790 m/s, 1,250 J)
- Wikipedia, *HK416* and *FN Minimi* — for the figures HK and FN do not quote
- In-repo: `Docs/PLAYER_MODEL_PLAN.md`, `Docs/ASSET_REGISTER.md` §4.7 and M-008l,
  `Docs/evidence/vfx_muzzle_candidates.json`, `Docs/MAPS_DRYRIVER.md`, `Docs/PROJECT_AUDIT.md`,
  `Build/weapons_setup.json`

**Real names are used deliberately** (ADR-035, ADR-034): EF88, F89, M4 and HK416 are all named in
`CLAUDE.md` as permitted, and the in-game A-series names map to them. The ADF is not endorsed by this
project and no Commonwealth emblem or insignia is reproduced.