# Player model and skeleton — where it stands and what to do next

**For the producer and whoever picks up the soldier.** Updated 2026-10-01. The original G3 diagnosis below is retained as historical evidence, but it no longer describes the active friendly assembly. Current configuration is summarized first; measurements and judgements remain labeled.

**How to use this document.** §1 is the current assembly. §§2–4 preserve the superseded G3 diagnosis and plan as history, not active work. §5 records ADR-042's current Quantum body decision and evidence status. §6 documents UE tooling pitfalls; §7 is the historical weapons hand-off and requires revalidation before acting on it.

| | |
|---|---|
| Producer complaint (historical G3 assembly) | "the shoulders look weird, the patch between the webbing and the waist is just a weird green"; the active Quantum replacement is still **not visually accepted** |
| Soldier assembly | `Tools/Unreal/setup_soldiers.py` → `B_SS_Soldier` (`USSCharacterPartActor`) |
| Gear import + materials | `Tools/Unreal/setup_adf_soldier.py` → `Build/adf_soldier_setup.json` |
| Fit rig | `Tools/Blender/adfrc_gear_rig.py` → `Art/Characters/ADF/SK_ADF_*.fbx` |
| Historical captures | `Build/soldier_check.html`, `Build/zoom_torso.png`, `Build/zoom_shoulders.png` (G3 baseline); Session 091's `Saved/Screenshots/WindowsEditor/SSShot.png` is not available in this checkout |
| Project-use position | ADR-035/L-0021 clear acquired ADFRC assets for this F2P project; ADR-042 records the active Quantum body/camo route. ADR-033 is historical texture direction, not the current material assignment. |
| Project root | `E:/SouthernSpear` · UE **5.8** · Blender 5.2.2 · Python 3.12 |

---

## 1. Current player-model state (ADR-042)

The producer-selected friendly visual body is **Quantum**: shirt, jeans, arms and head modules use Quantum's own skeleton; camo is supplied through `FriendlyMaterialOverrides`. ADFRC vest and helmet remain separate Manny-rigged/leader-posed gear. The gameplay pawn retains Manny for gameplay/hand-IK, while the visible Quantum modules are retargeted at runtime. Thus the old G3 uniform/Modern Insurgent head findings in §§2–4 are superseded and must not be treated as the active outfit or defect. The opposing MAF configuration is separate.

**Active assembly measured (Session 091 audit, `Build/active_character_audit.json`):**
- Assembled LOD0 vertices: **107,016 verts across 6 parts** (Quantum Shirt: 3,948; Quantum Jeans: 9,653; Quantum Arms: 12,320; Quantum Head: 13,288; ADFRC TBAS Vest: 43,130; ADFRC OpsCore Helmet: 24,677). This measures geometry, not visual quality or render cost; all six parts have only LOD0, and the two large Manny-rigged gear pieces have no physics asset.
- **Construction/presentation fact:** active friendly appearance combines a Quantum sample head/body with ADFRC torso gear and the default Lyra rifle idle/weapon hold. The newer runtime retarget avoids detached preview parts, but does not prove the kit looks intentional, bespoke, flattering, or camera-ready. The class-select is a right-side 540×720 portrait; its preview-camera/light/pose must be judged as a designed presentation, not inferred from a capture command completing.
- **Known preview risks found in source review:** the preceding preview yaw had an extra −55° offset from its stated camera-facing pose; locality was applied immediately after child creation, before `BeginPlay` built the hidden component arrays; and the camera used 28° FOV at 330 cm. The working tree now defers locality, exposes the spawned skinned parts to the capture, centers the idle pose toward camera and uses a wider 32°/360 cm full-body frame. These are source fixes, not visual evidence; rebuild and inspect the composition before accepting it.
- **Art-quality concerns still open:** no role-specific silhouette, authored face/headgear variation, modern hard-surface material breakup on vest/helmet, boot/glove fit close-up, or bespoke combat-ready idle has been accepted. These are presentation/design issues beyond the skeleton/vertex audit.
- Skeletons: 4 Quantum modules on `SK_Military_Character_Skeleton` (351 bones), 2 ADFRC gear meshes on `SK_Mannequin` (164 bones).
- Physics assets: Quantum modules carry `PA_*` physics assets; ADFRC gear lacks physics assets.
- Material overrides: `M_SS_ADFRC_Camo` master material has `used_with_skeletal_mesh = True`; `MI_SS_ADFRC_Camo_Shirt` (tiling 3.0) and `MI_SS_ADFRC_Camo_Jeans` (tiling 4.0) provide Australian DPCU camouflage.
- Class Select Preview: `USSClassSelectWidget` spawns `B_SS_Soldier` directly as a child actor on `StageBody`, aiming to share runtime retargeting, locality, material overrides, and leader-posed gear.

**Verification status (corrected 2026-10-01):** The model/skeleton inventory and C++ build were reported as verified in Session 091. The screenshot is not available in this checkout, and the producer explicitly reports that the last in-game class-select popup did not show a good character model. Do **not** describe appearance as verified or call R-58/R-59 closure an art-quality acceptance. The follow-up changes in this review adjust preview locality timing, yaw, and framing, but still require a fresh attended build and in-game screenshot. Visual sign-off remains OPEN.

### Historical G3 assembly (superseded 2026-09-30)

The prior friendly soldier was four meshes — no body mesh underneath (`setup_soldiers.py:21-23`):

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

## 2. Historical G3 complaints, diagnosed (superseded)

### 2.1 The green patch between the webbing and the waist

**Historical G3-only diagnosis — not confirmed on the active Quantum appearance.** On the retired G3 assembly this was a flat olive surface baked into the vendor texture. Measured:

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

**Historical G3-only diagnosis — do not carry forward as the active cause without new evidence.** On the retired G3 uniform the strong candidate was the **seam**, not the geometry: a hard edge where a camo panel meets the flat olive fill, running across the shoulder cap and down the arm. `Build/zoom_shoulders.png` shows it
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

## 3. Historical G3 skeleton diagnosis (superseded for visible body)

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

## 4. Historical G3 work plan (do not apply without revalidation)

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

### P2 — Own the skeleton (historical G3 task; reassess)

The old task proposed a G3 soldier skeleton. ADR-042 replaced the visible friendly G3 body with Quantum while keeping Manny as gameplay skeleton and retaining Manny-rigged vest/helmet. Do not create/reparent the proposed G3 skeleton as written; first measure the active Quantum retarget and gear boundary, then decide whether separate gameplay/appearance skeleton ownership is still warranted.

### P3 — Physics asset and LODs

- `create_physics_asset = False` on every import (`setup_adf_soldier.py:import_mesh`). 90k verts
  across three meshes with no physics asset: no cloth or gear collision, and no ragdoll.
- **No LODs.** 23,187 + 42,311 + 24,498 = **89,996 verts per soldier**, every soldier, always. With
  bots on both teams this is the single largest character cost in the game, and it is invisible in a
  single-front-end screenshot.

Both are import-time properties plus a physics-asset generation step, so both are scripted and
re-runnable in the same pass as P1/P2.

### P4 — The flat under-shirt (historical G3-only issue; superseded)

Do not grind the generator yet. The choice is:

- **(a) Island-aware repaint** — the mask works (`make_g3_shirt_camo.py`), the pattern does not. Needs
  the ADFRC camo re-sampled at the right blob scale and the fill's fold shading preserved. Doable,
  another pass.
- **(b) Swap the base garment** for one whose sheet has no flat fill. Cheaper and better if ADFRC has
  one. **Check this first** — it may make (a) unnecessary.
- **(c) Accept it and re-frame it** — a soldier with the jacket unzipped over an olive base layer is
  not *wrong*, it just needs to be deliberate rather than accidental.

I recommend checking (b) before spending more on (a). This recommendation applied only to the retired G3 uniform; the current Quantum shirt/jeans camo needs its own visual inspection.

**Resolved 2026-10-01, and the cause was measured rather than inferred.** The ADFRC G3 shirt does have
a flat fill, and it is on the sheet the *current* uniform uses. `Tools/Blender/inspect_uniform_fit.py`
reports the fitted uniform's torso faces sample UV v 0.02–0.24 of `Crye_G3_Shirt_AMC_co.png`, and
`Tools/Common/ss_sheet_probe.py` shows that band is a plain khaki under-shirt panel — which is what
reads as "a weird gap at the waist". The mesh itself is continuous (trunk faces within 18 cm of the
axis in every 2.5 cm slab, 75–155 cm), so (b) was the wrong instinct: no other garment fixes it.
**Fix applied:** option (a), island-aware. `Tools/Textures/patch_adfrc_undershirt.py` writes
`Art/Characters/ADF/T_ADFRC_G3_Shirt_AmcuCamo.png` with the plain tiles replaced by the trouser
sheet's camouflage, mirrored across the sheet so the repeat has no visible seam, and
`setup_adf_soldier.py` points the shirt slot at it. Reversible: drop the patch and re-run the script.
The producer has not yet accepted the result (R-92).

### P5 — Make "does the soldier look right" repeatable

Promote the ad-hoc `Build/soldier_check.html` into a turntable capture script and a checklist, so
this class of defect is caught by a run rather than by a producer noticing it in a screenshot. Every
finding in §2 came from a hand-cropped screenshot; none of it was caught by a check.

## 5. Body and head — RESOLVED by producer decision: Quantum is the friendly body (ADR-042, 2026-09-30)

**The producer chose Quantum for the friendly body (ADR-042), ending the ADR-036–039 body-selection gate; this was not final visual acceptance.** The
G3/Modern-Insurgent assembly — the "assembled rather than worn" mismatch this plan diagnosed — has
left the friendly look. The active Quantum + ADFRC assembly still needs producer art-direction review. What is currently configured:

- **Friendly (current, 2026-10-01 evening — supersedes the four-Quantum-module assembly below):**
  the **ADFRC G3 uniform, TBAS vest and OpsCore helmet**, all Manny-rigged and leader-posed
  (`FriendlyLeaderPoseParts`), with the Quantum head as the only retargeted module
  (`FriendlyParts`). This is the producer's direction ("needs the AMCU from the ADFRC textures and
  models"): the gear that has to cover the head and torso is fitted to the skeleton the pawn
  animates, so it cannot drift from the pose. Measured in the class-select capture: helmet, webbing
  and AMCU camouflage all render, and the torso's white band turned out to be the shirt sheet's flat
  under-shirt panel (P4), now repainted in pattern from the same pack.
- **Superseded 2026-10-01 morning:** the four Quantum modules (shirt, jeans, arms, head), retargeted
  per tick from the pawn's evaluated pose, with the ADFRC vest and helmet leader-posed over them.
  The ADFRC gear is no longer layered over a Quantum body, so the Quantum shirt/jeans work in
  `setup_quantum_proto.py` is now unused for the friendly look.
- **Gameplay unchanged:** the pawn's body mesh is still Manny with the hand-IK component — hit
  zones, damage, movement, sockets and the wrist solve all keep working (ADR-004); the retarget
  carries the solved wrist rotation into the Quantum arms.
- **Camo:** the ADFRC camo on the shirt and jeans rides on component overrides
  (`FriendlyMaterialOverrides`), because mesh-asset material slots are read-only from Python in
  5.8 (R-91, measured 2026-09-30) — the prototype-era in-mesh assignment silently never wrote.
- **Opposing (MAF):** byte-for-byte the look it was before this change.

The fair-comparison evidence trail (ADR-036–039) remains below as historical context. The 2026-10-01 review found that Session 091's “verified in-engine” wording overstates what is established: it is a reported capture, unavailable in the checkout, and conflicts with the producer's direct visual feedback. R-58's skeleton/retarget boundary and R-59's mesh inventory can be measured independently; neither proves the outfit reads well. Treat final character appearance as OPEN.

**Historical (superseded):** the plan previously held the G3 baseline pending a fully-dressed, same-condition comparison, and recorded that `setup_soldiers.py` assembled the Modern Insurgent 7 head with the ADFRC G3 uniform. That assembly was live until 2026-09-30; its green under-shirt and fit analysis is historical, not a live Quantum-body defect.

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

## 8. Historical state of the working tree (2026-09-28 snapshot)

This table describes the older document snapshot, not the 2026-10-01 shared worktree or the active Quantum configuration. Untracked then, none of it wired into the game:

| Path | What it is |
|---|---|
| `Tools/Textures/make_g3_shirt_camo.py` | Panel mask works; pattern generator does not (§2.3) |
| `Tools/Unreal/probe_manny_bones.py` | Dumps the mannequin's 164 bones via the working 5.8 route |
| `Tools/Unreal/probe_soldier_render.py` | Material audit of a spawned pawn; blocked, see §6 |

`Art/Characters/Textures/T_SS_ADF_G3_Shirt_co.png` (13.8 MB) is the camo tool's output. It is **not
committed** and **not bound to any material** — the colours are wrong (§2.3) and the tool regenerates
it in about four seconds, so there is no reason to put a known-bad 13.8 MB artefact in the repository.
The project's other generated textures are committed because they are in use; this one is not.

This 2026-09-28 snapshot's note that no tracked file was modified and `origin/main` was at `f2c8870b` is historical; it is not a statement about the current working tree.
