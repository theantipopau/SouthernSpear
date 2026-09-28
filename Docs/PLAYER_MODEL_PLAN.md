# Player model and skeleton — where it stands and what to do next

**For the producer and whoever picks up the soldier.** Written 2026-09-28. Everything below is
measured from the assets, the source scripts and a render, not assumed. Where something is a
judgement rather than a measurement it says so.

**How to use this document.** §1–§2 are what the model is and what is wrong with it. §3 is the
skeleton, which is in better shape than the complaint suggests. §4 is the ordered plan — this is the
part to work from. §5 is the one decision only the producer can make. §6 is the list of things that
fail *silently* on this build, each of which has already cost time. §7 is the weapons hand-off.

| | |
|---|---|
| Producer complaint | "the shoulders look weird, the patch between the webbing and the waist is just a weird green" |
| Soldier assembly | `Tools/Unreal/setup_soldiers.py` → `B_SS_Soldier` (`USSCharacterPartActor`) |
| Gear import + materials | `Tools/Unreal/setup_adf_soldier.py` → `Build/adf_soldier_setup.json` |
| Fit rig | `Tools/Blender/adfrc_gear_rig.py` → `Art/Characters/ADF/SK_ADF_*.fbx` |
| Capture | `Build/soldier_check.html`, `Build/zoom_torso.png`, `Build/zoom_shoulders.png` |
| Licence position | ADR-033 (withdraws ADR-016's camouflage clause), ADR-035; L-0021 |
| Project root | `E:/SouthernSpear` · UE **5.8** · Blender 5.2.2 · Python 3.12 |

---

## 1. What the player model actually is

The friendly soldier is **four meshes and nothing else** — there is no body mesh underneath
(`setup_soldiers.py:21-23`):

| Part | Source | Verts | Bones | Z range |
|---|---|---|---|---|
| Head | `Modern_Insurgent_7/Separate_Parts/SK_Head` (Fab) | — | — | — |
| Uniform | `ADF/SK_ADF_Uniform_G3` (ADFRC G3) | 23,187 | 108 | −1.864 → −0.208 |
| Vest | `ADF/SK_ADF_Vest_TBAS` (ADFRC) | 42,311 | 41 | −0.275 → 0.634 |
| Helmet | `ADF/SK_ADF_Helmet_OpsCore` (ADFRC) | 24,498 | 1 | 0.579 → 0.831 |

Two consequences that matter for everything below:

- **The uniform carries the arms.** `SK_ADF_Uniform_G3` has 108 bones and its arm vertices split
  4,590 shirt / 914 gloves. The G3 base mesh is a full character, not a garment on a body. Anything
  that assumes a body mesh under the clothes is wrong here — including the earlier theory that
  `SKM_QuantumCharacter` (14 slots, all on vendor materials) was the body. **It is not in the soldier
  at all.** `friendly_material_overrides` is deliberately empty (`setup_soldiers.py:61`).
- **The head is from a different pack to the body.** Fab "Modern Insurgent 7" head on an ADFRC G3
  body, under an ADFRC vest and helmet. That is the reason the model reads as *assembled* rather than
  *worn*, independently of any texture fault. See §5.

## 2. The two complaints, diagnosed

### 2.1 The green patch between the webbing and the waist

**It is a flat, untextured olive surface, and it is baked into the vendor texture.** Measured:

| Evidence | Value |
|---|---|
| Render, webbing→waist band (`Build/zoom_torso.png`) | `rgb(60, 57, 35)`, local std **1.7** |
| `Crye_G3_Shirt_AMC_co.png` — share of sheet with no local detail | **53%** |
| …the luminance band that flat fill occupies | **73–86** (real camo on the same sheet spans 14–124) |

The G3 sheet paints the shirt as a *camo jacket over a plain olive under-shirt*, and the under-shirt
owns the whole torso, both forearms and the shoulder caps. So this is not a missing texture, not the
64×64 fallback, not the mannequin showing through, and not a lighting fault: the pixels are a
deliberate solid fill in ADFRC's own artwork. The band between the webbing and the waistband, and the
smooth forearms below the elbow, are **the same pixels** — one complaint, one cause.

No texture variant avoids it. `Crye_G3_Shirt_AMP_co`, `_DPC_co`, `_DPD_co` and the rest are the same
Arma base mesh with the same under-shirt. **Swapping the shirt texture cannot fix this.**

### 2.2 The shoulders

The strong candidate is the **seam**, not the geometry: a hard edge where a camo panel meets the flat
olive fill, running across the shoulder cap and down the arm. `Build/zoom_shoulders.png` shows it
clearly — camo upper arm, hard boundary at the elbow, smooth olive below, and the same olive across
the torso.

What the geometry does *not* show: the vest spans −0.275 → 0.634 and the uniform −1.864 → −0.208, so
the vest hem **overlaps** the uniform by 67 mm. There is no hole at the waist and no floating
shoulder piece. If the shoulders still read wrong after the texture work, the next thing to check is
the vest's shoulder strap placement in the FBX, not the skeleton (§3).

### 2.3 The attempt that did not work — and its state

`Tools/Textures/make_g3_shirt_camo.py` (new, untracked) generates
`Art/Characters/Textures/T_SS_ADF_G3_Shirt_co.png` (4096²) by finding the flat panels
(local detail over a 50 px window, grown from the large components only) and laying camo into them
over the fill's own fold shading. **The colours came out wrong** and the producer stopped it: the
first version mirrored real camo and came out visibly symmetric and 2× too soft; the rewrite used a
generated seamless tile whose palette, sampled from the sheet's own camo, was still too dark and
too large-blobby. Local detail in the repainted panels went 1.86 → 10.74 (real camo is ~20), and
luminance 78 → 69 against 57 for the real panels.

**Nothing in the game changed.** `setup_adf_soldier.py` is untouched, the generated sheet is not
bound to any material, and both files are untracked. The game still uses the stock ADFRC shirt. The
tool is a working *mask* — the panel detection is good — with the pattern generator as the part that
needs another pass.

## 3. The skeleton — better news than expected

**Nothing is wrong with the bones.** Measured against the animated mannequin's 164-bone skeleton:

| Check | Result |
|---|---|
| Uniform's 28 arm bones present in Manny | **28 / 28** — 0 missing |
| Vest's 18 arm bones present in Manny | **18 / 18** — 0 missing |
| Leader-pose mismatch | none; every part bone resolves to a mannequin bone |

So the odd shoulders are **not** a missing-bone or broken-leader-pose fault. I chased that first
because it is the usual cause and it is not this.

The real structural issue is **ownership**: `import_mesh()` parents every ADF part onto **Lyra's**
`/Game/Characters/Heroes/Mannequin/Meshes/SK_Mannequin` (`setup_adf_soldier.py:22`). The soldier
therefore cannot have its own clavicle, pec or corrective bones, and if Lyra's mannequin is ever
replaced every ADF part breaks. That is headroom, not a bug — but it is the thing that makes the
model hard to improve, because there is nowhere to add a bone.

## 4. What to do next, in order

### P1 — Fix the texture pipeline (cheap, certain, do first)

**P1.1 — DONE (Session 051).** `max_texture_size` raised 2048 → 4096 in `setup_adf_soldier.py`, and the
texture assets re-saved. The cap was halving every ADFRC colour sheet: `T_ADF_crye_g3_shirt_amc_co`
and `T_ADF_crye_g3_pants_amc_co` are 4096² and were reaching the screen at 1024². The report now
carries a `textures` block listing each texture's size beside the cap actually set on the asset, plus
`textures_halved`, which is **0** across all 89 textures, and `report["ok"]` now fails the run if
that is ever non-zero. Verified by re-running the script, not asserted.

The cap can only ever downscale, so 4096 leaves the 1024 gloves and 2048 normals untouched.

Still to do in P1:

2. **The 64×64 flat fallback makes a failed lookup look like a finished material.**
   `T_ADF_Olive` (rgb 78,84,58) and `T_ADF_Coyote` (rgb 128,104,74) are still wired in for the
   `MAF_FLAT` slots and for any `_mc` stem with no amcu/coyote variant. **4 of the soldier's 31
   material slots are flat colour slabs today** — `safariland` (multicam: flat coyote), and the MAF
   `belt`, `tacgear` and `pasgt` (flat olive). Delete the branch and make an unbound `BaseColorMap` an
   error. The `note` field in the report already names these slots, so the evidence is already there.
3. **`verify_character_materials.py` proves nothing.** It calls
   `get_material_property_input_expression`, which does not exist in UE 5.8, and it reads textures
   with `get_material_default_texture_parameter_value`, which cannot see a texture wired through
   graph nodes and returns UNSET on a correctly bound material. Rewrite it on
   `get_material_expressions()` / `get_texture_parameter_names()` and
   `get_material_instance_texture_parameter_value()`, then make it a gate.

### P2 — Own the skeleton

Create `/SSExp_ObjectiveAssault/Characters/ADF/SK_SS_Soldier` plus a physics asset, re-parent the
five parts onto it, and point the pawn's mesh at it. Nothing breaks (all bones already resolve); this
buys the ability to add clavicle/pec/corrective bones and decouples the soldier from Lyra's
mannequin. Sequence it after P1, since P1 changes the import anyway.

### P3 — Physics asset and LODs

- `create_physics_asset = False` on every import (`setup_adf_soldier.py:import_mesh`). 90k verts
  across three meshes with no physics asset: no cloth or gear collision, and no ragdoll.
- **No LODs.** 23,187 + 42,311 + 24,498 = **89,996 verts per soldier**, every soldier, always. With
  bots on both teams this is the single largest character cost in the game, and it is invisible in a
  single-front-end screenshot.

Both are import-time properties plus a physics-asset generation step, so both are scripted and
re-runnable in the same pass as P1/P2.

### P4 — The flat under-shirt: decide, then finish

Do not grind the generator yet. The choice is:

- **(a) Island-aware repaint** — the mask works (`make_g3_shirt_camo.py`), the pattern does not. Needs
  the ADFRC camo re-sampled at the right blob scale and the fill's fold shading preserved. Doable,
  another pass.
- **(b) Swap the base garment** for one whose sheet has no flat fill. Cheaper and better if ADFRC has
  one. **Check this first** — it may make (a) unnecessary.
- **(c) Accept it and re-frame it** — a soldier with the jacket unzipped over an olive base layer is
  not *wrong*, it just needs to be deliberate rather than accidental.

I recommend checking (b) before spending more on (a).

### P5 — Make "does the soldier look right" repeatable

Promote the ad-hoc `Build/soldier_check.html` into a turntable capture script and a checklist, so
this class of defect is caught by a run rather than by a producer noticing it in a screenshot. Every
finding in §2 came from a hand-cropped screenshot; none of it was caught by a check.

## 5. The body — decided (ADR-036)

**The ADFRC G3 is the body.** Head, arms, torso and gear all come from the ADF Re-Cut pack; the Fab
`Modern_Insurgent_7` head comes off the friendly soldier. `SKM_QuantumCharacter` is retired as a
candidate body. Rationale, and the MAF's unchanged position, are in `Docs/DECISION_LOG.md` ADR-036.

The "assembled rather than worn" read was never a texture fault — it is three sources of proportions,
skin and material response — and it is now fixed at the source rather than painted over. P2 below
unblocks as a direct result.

## 6. Things that fail silently on this build

Each of these has already cost time in this session.

| Trap | Consequence |
|---|---|
| `unreal.load_asset("/SSExp_ObjectiveAssault/…")` returns **None** in a `-run=pythonscript` commandlet | The game-feature plugin is not mounted, so every probe over the ADF parts reads nothing and reports success. A skeleton probe built this way reported 26 "bones" that were the characters of an error string. Enable the experience, or read the FBX with Blender. |
| **`EditorAssetLibrary.does_asset_exist()` answers False for those same plugin paths**, even though `unreal.load_asset()` and `find_asset_data()` both resolve them | The worst one, because it corrupts a script rather than failing loudly. Any `if does_asset_exist(p): load(p) else: create(p)` pattern takes the *create* branch for an asset that already exists; `create_asset` then returns `None` and the next line dies. `setup_adf_soldier.py` was **not idempotent** for exactly this reason and had never been re-run on a machine where it had already succeeded — the first re-run died on the MAF uniform slots and left `Build/adf_soldier_setup.json` with an empty `maf_uniform_slots`, which `setup_soldiers.py` reads. Fixed: branch on `load_asset()` returning `None`, not on `does_asset_exist`. |
| `Skeleton.get_reference_skeleton()` returns a **`str`** in UE 5.8 Python, not a bone-name array | Iterating it yields characters. The working route is `skeleton.get_reference_pose().get_bone_names()` — see `Tools/Unreal/dump_quantum_skeleton.py:41-43`. |
| `/Game/Characters/Heroes/Mannequin/Meshes/SK_Mannequin` loads as a **Skeleton**, not a SkeletalMesh | `get_editor_property("skeleton")` raises on it. |
| `get_material_default_texture_parameter_value` cannot see graph-wired textures | Returns UNSET on correctly bound materials — this is why `verify_character_materials.py` proves nothing. |
| The 64×64 flat fallback (§4 P1.2) | A failed texture lookup renders as a finished-looking flat garment. |
| The FrontEnd preview pawn is spawned at runtime, not placed in the level | `Tools/Unreal/probe_soldier_render.py` loads `L_SS_FrontEnd` and finds no pawn. Material audits of the *assembled* soldier have to spawn the pawn, not read the level. |

## 7. Weapons hand-off (from the other agent)

- **`f2c8870b` is pulled** (the `ss.Callsign` double-registration fix, which caused the
  `USSPlayerProfileSubsystem::Deinitialize()` access violation that stopped the run at 20/57 tests).
  Not yet built here.
- **The probe file already exists**: `Build/probe_weapon_fire.json` (15,439 bytes), from
  `Tools/Unreal/probe_weapon_fire.py`. What it says:
  - 4 weapons found: **A88, A89, A25** all on `GA_Weapon_Fire_Rifle_Auto_C`; **A9** on
    `GA_Weapon_Fire_Pistol_C`.
  - `GA_Weapon_Fire_C.FireDelayTimeSecs = 0.120` on **all three rifles** — one fire rate, ≈500 rpm, not
    differentiated. That is the rest of W1.
  - **A4 / A416 / A417 are absent from the probe** although the other agent's table has rows for them.
  - **A25 should be semi-auto** and is currently on the `_Auto` ability.
- To close W1, the delays to set (60 ÷ rpm): A88 682 → **0.088 s**, A89 750 → **0.080 s**,
  A4/A416 857 → **0.070 s**, A417 600 → **0.100 s**. A25 needs a different ability, not a delay.
- Still to run: build, then `Automation RunTests SouthernSpear` (expect all 57 now), then a match to
  check the HUD — A89 shows 200, A25 shows 20.

## 8. State of the working tree

Untracked, none of it wired into the game:

| Path | What it is |
|---|---|
| `Tools/Textures/make_g3_shirt_camo.py` | Panel mask works; pattern generator does not (§2.3) |
| `Tools/Unreal/probe_manny_bones.py` | Dumps the mannequin's 164 bones via the working 5.8 route |
| `Tools/Unreal/probe_soldier_render.py` | Material audit of a spawned pawn; blocked, see §6 |

`Art/Characters/Textures/T_SS_ADF_G3_Shirt_co.png` (13.8 MB) is the camo tool's output. It is **not
committed** and **not bound to any material** — the colours are wrong (§2.3) and the tool regenerates
it in about four seconds, so there is no reason to put a known-bad 13.8 MB artefact in the repository.
The project's other generated textures are committed because they are in use; this one is not.

No tracked file was modified. `origin/main` is at `f2c8870b`; the working tree was clean before this
document.
