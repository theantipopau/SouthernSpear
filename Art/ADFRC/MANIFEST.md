# ADFRC Assets — Manifest

**Status: 209 of 211 models converted to usable Blender `.blend`.
2 are blocked — see §4.**

Converted 2026-09-27. Authorisation: `LICENSE.md`, `Docs/LICENCE_REGISTER.md` L-0021.

---

## 1. Honest totals

| Stage | Count | Note |
|---|---:|---|
| Source `.p3d` (ODOL) | 177 | plus 34 added later = **211** in `Art/ADFRC_MLOD` |
| → MLOD | **211** | 100% success, every file signature-verified |
| → Blender `.blend` | **209** | **2 blocked** (see §4) |
| Weapon sounds (WAV) | **212** | no conversion needed — usable as-is |

An earlier note in this file claimed 179/179. **That was wrong** — per-model
verification found silent failures, and the true blocker turned out to be
`class = man` (§4), not a general conversion problem.

## 2. Verified working

Rigid props (`class = ObjectProp`) convert reliably. Spot-checked geometry read
back out of the saved files:

| Model | Vertices | Polys |
|---|---|---|
| `adfrc_pasgt` helmet | 5,851 | 4,124 |
| `ADFRC_TA31_BLK` scope | 306 + 4 sub-meshes | 500 + 301 |
| `adfrc_SR25` sniper | 88 mesh objects, 13 MB | multiple LODs |

## 3. Folder layout

**`Art/ADFRC_BLEND/<addon>/`** — each model beside its own textures:

```
adfrc_ef88/
  ADFRC_EF88_MLOD.blend
  ADFRC_EF88_MLOD_textures/
    ADFRC_EF88_CO.png      base colour
    ADFRC_EF88_NOHQ.png    normal
    ADFRC_EF88_SMDI.png    specular/mask
    ADFRC_EF88_CA.png      combined atlas
```

**`Art/ADFRC_Player/`** — worn gear: `adfrc_helmets` (11), `adfrc_vests` (24),
`adfrc_backpacks` (11), `adfrc_uniforms` (2), `adfrc_facewear` (5),
`adfrc_grips` (4).

**`Art/ADFRC/Sounds/`** — **212 WAV files**, weapon fire and reload. Directly
usable in Unreal: no conversion needed. Covers close/mid/dist shots, dry-fire,
reload, bolt/mag handling, and environmental tails (forest, houses, interior,
meadows, trees) per weapon. This is the single most immediately usable category
in the whole extraction.

### Accessories — 26 models

`PEQ15` laser units (BLK/FDE, M4 top), `Atlas_Black`, `Foxtrot2_FDE`, `Grippod`,
`L3Squad` (+ EF88 top), `NT4`, `Ryder9_Ti2`, `SOCOM`, `WARCOMP`, `WMLx` (IR and
WL), `X400`, `Zev`, F88/F88SA1/F88SA2 silencers, lasers and lights, `MSS_SBRMP`.

### Converted weapons

`adfrc_optics` 40 · `adfrc_carlgustav` 20 · `adfrc_minimi` 9 · `adfrc_m4a5` 7 ·
`adfrc_magazines` 7 · `adfrc_maximi` 6 · `adfrc_f88` 5 · `adfrc_ef88` 4 ·
`adfrc_g19` 3 · `adfrc_SR25` 3 · `adfrc_f88sa1`/`sa2` 2 each · `adfrc_f9` 2 ·
`adfrc_hpiii` 2 · `adfrc_hk416` 2 · `adfrc_hk417` 1

### Optics — 40 models, all Brucey

| Family | N | Type |
|---|---:|---|
| `Spectr` | 12 | Variable-mag rifle scope (RAR/KF/DP variants) |
| `TA31` | 8 | ACOG-style prism, BLK/FDE, KF and RMR |
| `PRO` | 4 | Variable prism, S/T and FC |
| `552`, `EXPS3` | 3, 3 | Collapsible, holographic |
| `TA648` | 2 | 6×48 magnifier |
| `Swaro` | 2 | SWAV, SWAV_SA2 |
| `Romeo2`, `C79`, `T2`, `dpp` | 4 | Deltapoint Pro and compact sights |

### Sniper rifles

`adfrc_SR25` — 3 models, 7.62×51 **semi-auto DMR**, not bolt-action.
`adfrc_hk417` — 7.62×51 battle rifle. **This pack contains no bolt-action
sniper**; that would need a new source.

## 4. The `class = man` problem

**20 models are declared `class = man`** (character/skinned geometry) rather than
`ObjectProp`. The Blender importer calls `bpy.ops.arma3tools.import_p3d`, which
**never returns** on these — it tries to build a skeleton the file does not
carry. Confirmed by instrumenting the call: the addon enables fine, then the
import call itself hangs indefinitely, on files as small as 3.6 MB. So this is
not a size or timeout problem, and `--model-cfg` does not help.

`python Tools/Common/adfrc_class_scan.py` lists them;
report at `Build/adfrc_model_classes.tsv`.

**Currently blocked** (all 20 are skinned garments):

| Addon | N | Models |
|---|---:|---|
| `adfrc_vests` | 12 | `TBAS_T5_*` (Base, CFA, CQB, ENG, MG, PC, TL), `tbas_T2_DMR`, `JPC_Base`, `Peacekeeper_RAR`, `Peacekeeper_SOCOM`, `vest_aircrew` |
| `adfrc_facewear` | 2 | `facewear`, `facewear2` |
| `adfrc_uniforms` | 2 | `crye_g3`, `adfrc_field_dress` |
| `adfrc_nvgs` | 2 | `psq36_up`, `psq36_down` |
| `adfrc_backpacks` | 1 | `JPC_Backpannel` |
| `adfrc_helmets` | 1 | `boonie` |

Some of these have a `.blend` present from an earlier partial run, but they are
**geometry without a skeleton** — `TBAS_T5_MG` reads back as 87 meshes and
**0 armatures**, so they are not usable as rigged gear. Treat all 20 as blocked
until a skinned-mesh import path exists.

That these are the TBAS role vests, the Crye G3 and the JPC is not incidental —
**the most character-relevant gear is the part that is skinned**.

## 5. Getting these into Unreal

1. **FBX** — File → Export → FBX from the `.blend`. Rigid props need no rig
   options. Unreal imports FBX natively.
2. **Sounds need no work at all** — 212 WAVs in `Art/ADFRC/Sounds/`. Import
   directly; trim to game-length and normalise.
3. **Textures** — standard PNG, but **not packed into the `.blend`**
   (`bpy.data.images` is 0 for every model, because the addon resolves paths
   against an Arma root). A `.blend` moved on its own renders untextured; it
   must travel with its sibling `_textures/` folder. Downscale to 2048² weapons /
   1024² gear.
4. **Materials are not authored** — the meshes carry per-material splits but the
   Arma `.rvmat` graph has no UE equivalent. Follow the existing `M_SS_*` pattern.

## 6. Animations

`Art/ADFRC/Animations/` — 165 `.rtm` **plus decoded `.json`** with bone list,
frame phases, and per-bone quaternion + position for every frame. **The JSON
needs no conversion** and is directly usable. `BIS.CLI rtm info` reads the
binarised `.rtm`.

## 7. Branding — mandatory before any in-game use

ADR-016 requires original camouflage and insignia. Replace before shipping:

- Crye Precision / G3 markings (`crye_g3`)
- Ops-Core, PASGT, "Team Wendy" helmet marks (`Opscore_*`, `adfrc_pasgt`, `adfrc_teamwendy`)
- ADF camouflage patterns (AMCU / Auscam)

See `LICENSE.md` §5 and `Docs/PROJECT_AUDIT.md` R-27.

## 8. Reproducing the conversion

```
# ODOL -> MLOD
debinarizer <model.p3d>

# MLOD -> .blend
BIS.CLI p3d export <model_MLOD.p3d> -o <outdir>
```

Tooling lives outside the repo at `E:/_tools/UKSFTA-P3D` and
`E:/_tools/Arma3ObjectBuilder`. Two local changes: `BlenderExport.cs` tries both
`bl_ext.blender_org.*` and `bl_ext.user_default.*` module ids; and drive Blender
**serially** — the tool's own batch mode spawns 2–4 concurrent Blenders that
deadlock on a shared scratch directory.

## 9. Source

Originals at `Content/Sourced/ADF_Extracted/` and `Art/ADFRC/`. All of it, plus
the converted output, is git-ignored — see `LICENSE.md` §7.
