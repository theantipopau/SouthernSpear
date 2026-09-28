# Docs/Sourced/ADFRC — ADF Re-Cut asset pipeline (tracked)

This directory holds the **documentation and tooling** for the extracted
Arma 3 *ADF Re-Cut (ADFRC)* asset set, so the pipeline survives even though the
19 GB of extracted assets themselves are deliberately not in git.

| File | What it is |
|---|---|
| `ADFRC_INTEGRATION_GUIDE.md` | **Start here.** How models, textures, materials and animations fit together, and how to drive them from another agent. |
| `EXTRACTION_README.md` | Layout and totals of the extraction output tree. |
| `ASSET_MANIFEST.json` | Registry: 268 models with material→texture bindings, 614 materials, 13 rigs, 165 clips, 257 sounds. |
| `TEXTURE_MANIFEST.json` | Per-texture sRGB + compression + channel role for all 2,494 PNGs. |
| `*.py`, `*.sh`, `*.c`, `*.h` | Every script used to build the extraction. All resumable, all take explicit paths. |

## The live output tree

The assets these scripts produce are **not** in git — `Content/Sourced/` is
excluded by `.gitignore`. They live at:

```
E:\SouthernSpear\Content\Sourced\ADF_Extracted\
├── Models_UE/        268 FBX with textures bound  ← import these
├── Models_FBX/       268 FBX geometry only         ← intermediate
├── Models/           268 raw .p3d (ODOL)           ← reference
├── Textures/         2,494 PNG + manifest
├── Materials_Text/   683 decoded .rvmat / config.bin
├── Animations/       .rtm, JSON, Rig/ (hierarchy + rest pose)
├── Animations_UE/    13 skeleton FBX + 165 clip FBX
└── _tools/           the scripts, mirrored from here
```

The two JSON manifests are **copies** of files inside that tree. If you re-run
`ue_manifest.py` or `texture_manifest.py`, refresh them here:

```bash
cp Content/Sourced/ADF_Extracted/ASSET_MANIFEST.json        Docs/Sourced/ADFRC/
cp Content/Sourced/ADF_Extracted/Textures/_ue_manifest.json Docs/Sourced/ADFRC/TEXTURE_MANIFEST.json
```

## Licence

ADFRC is **APL-SA**. Per the upstream Workshop page and the pack's
`ASSETS_LICENSE.md`, code/configs/textures are open, but **3D models may not be
extracted or reused commercially**. No extracted asset data is committed here —
only the tooling and documentation. Log provenance in
`Docs/LICENCE_REGISTER.md` and `Docs/ASSET_REGISTER.md` before shipping.
