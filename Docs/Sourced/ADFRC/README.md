# ADF_Extracted — extracted ADF Re-Cut assets for Unreal

Free-licensed Arma 3 *ADF Re-Cut (ADFRC)* assets, decoded out of their native
formats and prepared for Unreal Engine 5.

**Read `ADFRC_INTEGRATION_GUIDE.md` first** — it explains how models, textures,
materials and animations fit together and how to drive them from another agent.
**`ASSET_MANIFEST.json`** is the machine-readable registry of *files*;
**`_tools/config_registry.json`** is the registry of *what things are* — which
config class owns which mesh, muzzle attachment points, magazine and reload
timings, and weapon/vehicle animation bindings. Start with the manifest, then
§6.1 of the guide, then **`ADFRC_CONFIG_REGISTRY.md`** for the full schema.

## Totals

| | |
|---|---|
| Files / size | 9,545 · 19 GB |
| Models (FBX, textures bound) | 268 |
| Textures (PNG) | 2,494 |
| Materials (decoded to text) | 614 `.rvmat` + 69 `config.bin` |
| Animation rigs / clips | 13 / 165 |
| Sounds (WAV) | 266 (257 from `.wss`, 9 from `.ogg`) |
| Config parsed | 218 files, 9,927 classes, 2,648 items, 0 unparsed statements |

## Layout

| Path | What |
|---|---|
| `Models_UE/` | **FBX with PNG textures bound — use this** |
| `Models_FBX/` | FBX geometry only, no image bindings (intermediate) |
| `Models/` | raw Arma `.p3d` (ODOL), for reference |
| `Textures/` | decoded PNGs + `_ue_manifest.json` (per-texture sRGB + compression) |
| `Materials_Text/` | every `.rvmat`/`config.bin` as readable config script |
| `Animations/` | `.rtm`, decoded JSON, and `Rig/` (hierarchy + rest pose) |
| `Animations_UE/` | skeleton FBX per rig + one FBX per clip |
| `Source/`, `Workshop/` | untouched original PBO payloads (provenance) |
| `_tools/` | every script, all re-runnable and resumable (+ `ogg_sounds.json`, `texheaders_report.json`, `config_registry.json`) |
| `ASSET_MANIFEST.json` | the registry of files |
| `_tools/config_registry.json` | the registry of items: classes, muzzle points, timings, magazines, animation bindings |
| `ADFRC_CONFIG_REGISTRY.md` | **full reference for the item registry** — schema, worked examples, Arma config gotchas |

## The three things that bite

1. **Use `Models_UE/`, not `Models_FBX/`.** Only `Models_UE` has textures wired
   into materials (1,524 bindings over 444 textures).
2. **Import scale 0.01.** Arma is metres, Unreal is centimetres.
3. **The folder is under `Content\`.** Unreal will try to auto-import 12 GB on
   next editor open — move it to a staging path or exclude it.

## Licence

ADFRC is **APL-SA**. Per the upstream Workshop page and `ASSETS_LICENSE.md`,
code/configs/textures are open but **3D models may not be extracted or reused
commercially**. Log provenance in `Docs\LICENCE_REGISTER.md` and
`ASSET_REGISTER.md` before shipping. See §7 of the integration guide.
