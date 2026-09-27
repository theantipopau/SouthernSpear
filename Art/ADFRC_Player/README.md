# ADF Player Models (Gear)

All ADF Re-Cut soldier-worn gear, converted to Blender format with textures
linked. **57 models, 1,538 textures, 7.3 GB.**

Authorisation: `../ADFRC/LICENSE.md` and `Docs/LICENCE_REGISTER.md` L-0021.
Conversion notes: `../ADFRC/MANIFEST.md`.

---

## What is in here

These are **wearable equipment**, not character bodies. The ADF Re-Cut units pack
ships no player models — it only dresses vanilla Arma bodies via binarised config
headers. The project's character bodies remain the licensed Fab assets
(L-0016, `SKM_QuantumCharacter` and `SK_*` parts).

| Folder | Models | Contents |
|---|---:|---|
| `adfrc_helmets` | 11 | `adfrc_pasgt`, `adfrc_gentex_cvc`, `adfrc_teamwendy`, `boonie`, `exfil`, `opscore` (+ AF/MT/cover variants), `brh` |
| `adfrc_vests` | 24 | JPC base, Peacekeeper RAR/SOCOM, pouch bundles, aircrew vest, and the full **TBAS T2** (10 role variants) and **T5** (7 variants) role vest sets |
| `adfrc_backpacks` | 11 | `bullock`, `BP_1`–`BP_4`, `JPC_Backpannel`, `TBAS_T5_Backpannel`, `molle_117g`, `molle_asip`, slingshot |
| `adfrc_uniforms` | 2 | `crye_g3` combat shirt, `adfrc_field_dress` |
| `adfrc_facewear` | 5 | balaclavas, `npp_kondor` |
| `adfrc_grips` | 4 | `ADFRC_AFG_BLK`/`FDE`, `ADFRC_MVG_BLK`/`FDE` |

## Layout

Each model sits beside its own textures:

```
adfrc_helmets/
  adfrc_pasgt_MLOD.blend
  adfrc_pasgt_MLOD_textures/
    adfrc_pasgt_dpc_CO.png
    adfrc_pasgt_dpc_NOHQ.png
    ...
```

Texture suffixes: `_CO` base colour, `_NOHQ` normal, `_SMDI` specular/mask,
`_CA` combined atlas.

## Using these in Unreal

1. **FBX export** — open the `.blend`, File → Export → FBX. These are rigid props
   with no armature, so no rig options are needed. Unreal imports FBX natively.
2. **Textures** — PNG, import directly. Downscale to 1024² on import; they are
   large source maps.
3. **Materials are not authored** — the meshes carry per-material splits, but the
   Arma `.rvmat` shader graph has no Unreal equivalent. Build materials in the
   project following the existing `M_SS_CMECU` / `M_SS_GearTan` pattern, or as
   material instances off them.
4. **Textures are not packed** into the `.blend` (the addon resolves them at
   import time against an Arma path root). Use the sibling `_textures/` folder.

## Before anything goes in-game

**ADR-016 requires original camouflage and insignia.** These assets carry real
branding that must be replaced first:

- **Ops-Core**, **PASGT**, **"Team Wendy"** helmet and headwear marks
- **Crye Precision** G3 uniform (`crye_g3`)
- ADF camouflage patterns (AMCU / Auscam)

This is a project rule independent of the authorisation — see
`../ADFRC/LICENSE.md` §5 and `Docs/PROJECT_AUDIT.md` R-27. Plan the substitution
at import time rather than shipping branded textures and stripping later.

## Version control

Git-ignored. Only the documentation in `Art/ADFRC/` is tracked.
